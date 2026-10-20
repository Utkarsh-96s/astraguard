"""Tests for Phase 4 Disaster Intelligence AI modules."""
import json
import os
import tempfile

import numpy as np
import pytest
import torch
from data.synthetic.disaster_gen import generate_synthetic_chip_arrays
from ml.common.protocols import RiskModule
from ml.common.schemas import Attribution, ModuleResult
from ml.disaster.change_detector import ChangeResult, SARChangeDetector
from ml.disaster.geo_export import export_geojson_footprint, export_overlay_png
from ml.disaster.module import DisasterRiskModule
from ml.disaster.priority_scorer import DisasterPriorityScorer, PriorityResult
from ml.disaster.unet import UNetSegmenter, compute_dice_f1, compute_iou


def test_unet_segmentation_forward_and_metrics() -> None:
    """Test U-Net forward pass, mask predictions, and metric computations."""
    model = UNetSegmenter(in_channels=1, base_filters=16)

    # Test tensor forward
    x = torch.randn(2, 1, 64, 64)
    out = model(x)
    assert out.shape == (2, 1, 64, 64)
    assert torch.all(out >= 0.0) and torch.all(out <= 1.0)

    # Test numpy predict_mask
    raw_img = np.random.uniform(0, 255, size=(64, 64)).astype(np.float32)
    binary_mask, water_ratio, conf = model.predict_mask(raw_img, threshold=0.5)
    assert binary_mask.shape == (64, 64)
    assert 0.0 <= water_ratio <= 1.0
    assert 0.0 <= conf <= 1.0
    assert binary_mask.dtype == np.uint8
    assert set(np.unique(binary_mask)).issubset({0, 1})

    # Test area computation: 100 pixels at 10m res = 100 * 100m^2 = 10,000m^2 = 0.01 km^2
    dummy_mask = np.zeros((100, 100), dtype=np.uint8)
    dummy_mask[:10, :10] = 1  # 100 pixels
    area = model.compute_surface_area_km2(dummy_mask, resolution_m=10.0)
    assert pytest.approx(area, rel=1e-3) == 0.01

    # Test IoU and Dice metric functions
    mask_a = np.array([[1, 1], [0, 0]], dtype=np.uint8)
    mask_b = np.array([[1, 0], [1, 0]], dtype=np.uint8)
    # Intersection = 1, Union = 3 -> IoU = 1/3
    # 2 * |A and B| / (|A| + |B|) = 2 * 1 / (2 + 2) = 0.5 -> Dice = 0.5
    assert pytest.approx(compute_iou(mask_a, mask_b), rel=1e-3) == 1.0 / 3.0
    assert pytest.approx(compute_dice_f1(mask_a, mask_b), rel=1e-3) == 0.5

    # Perfect overlap
    assert compute_iou(mask_a, mask_a) == 1.0
    assert compute_dice_f1(mask_a, mask_a) == 1.0

    # Zero overlap
    mask_c = np.array([[0, 0], [1, 1]], dtype=np.uint8)
    assert compute_iou(mask_a, mask_c) == 0.0
    assert compute_dice_f1(mask_a, mask_c) == 0.0


def test_sar_change_detector() -> None:
    """Test SAR change detector identifies newly inundated water surfaces."""
    pre_chip, _ = generate_synthetic_chip_arrays(size=64, water_ratio=0.10, seed=101)
    post_chip, _ = generate_synthetic_chip_arrays(size=64, water_ratio=0.35, seed=102)

    detector = SARChangeDetector(threshold_db_drop=0.20, resolution_m=10.0)
    result = detector.detect_flood_extent(pre_chip, post_chip)

    assert isinstance(result, ChangeResult)
    assert result.change_mask.shape == (64, 64)
    assert result.total_water_km2 >= result.newly_flooded_km2
    assert result.expansion_ratio >= 1.0
    assert result.newly_flooded_km2 >= 0.0


def test_priority_scorer_formula_and_bounds() -> None:
    """Test priority formula weights, normalization bounds, and sensitivities."""
    scorer = DisasterPriorityScorer()

    # Moderate conditions
    res = scorer.score_priority(
        inundated_area_km2=50.0,
        hours_since_event=4.0,
        cloud_cover_pct=20.0,
        population_proxy=0.6,
        spacecraft_health_risk=0.10,
    )
    assert isinstance(res, PriorityResult)
    assert 0.0 <= res.priority_score <= 1.0
    assert not res.deferral_flag
    assert res.recommendation == "schedule_observation"

    # Verify component contribution sum matches priority_score before health modifier
    expected_sum = (
        res.feature_contributions["area_contribution"]
        + res.feature_contributions["recency_contribution"]
        + res.feature_contributions["population_contribution"]
        + res.feature_contributions["cloud_clearance_contribution"]
    )
    assert pytest.approx(res.priority_score, abs=1e-3) == expected_sum

    # Higher area -> higher score
    res_larger = scorer.score_priority(
        inundated_area_km2=200.0,
        hours_since_event=4.0,
        cloud_cover_pct=20.0,
        population_proxy=0.6,
        spacecraft_health_risk=0.10,
    )
    assert res_larger.priority_score > res.priority_score


def test_priority_scorer_health_deferral() -> None:
    """Test autonomous EO deferral when spacecraft health risk >= 0.50."""
    scorer = DisasterPriorityScorer()

    # Nominal health
    nom = scorer.score_priority(
        inundated_area_km2=100.0,
        hours_since_event=1.0,
        cloud_cover_pct=5.0,
        population_proxy=0.9,
        spacecraft_health_risk=0.20,
    )
    assert not nom.deferral_flag
    assert nom.recommendation == "schedule_observation"

    # Degraded health >= 0.50
    deg = scorer.score_priority(
        inundated_area_km2=100.0,
        hours_since_event=1.0,
        cloud_cover_pct=5.0,
        population_proxy=0.9,
        spacecraft_health_risk=0.55,
    )
    assert deg.deferral_flag
    assert deg.recommendation == "defer/low-power"
    assert deg.priority_score < nom.priority_score
    assert deg.health_penalty_applied is True


def test_geospatial_export() -> None:
    """Test RGBA PNG mask generation and RFC 7946 GeoJSON export."""
    mask = np.zeros((32, 32), dtype=np.uint8)
    mask[10:20, 10:20] = 1

    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Test PNG export
        png_path = os.path.join(tmpdir, "test_mask.png")
        export_overlay_png(mask, png_path, color_rgba=(0, 229, 255, 180))
        assert os.path.exists(png_path)
        assert os.path.getsize(png_path) > 0

        # Verify PNG header
        with open(png_path, "rb") as f:
            header = f.read(8)
            assert header == b"\x89PNG\r\n\x1a\n"

        # 2. Test GeoJSON export
        geojson_path = os.path.join(tmpdir, "test_footprint.geojson")
        bounds = (20.0, 85.0, 20.5, 85.5)
        gj = export_geojson_footprint(
            mask,
            bounds=bounds,
            output_path=geojson_path,
            properties={"mission": "ASTRA-GUARD", "event": "Flood Test"},
        )

        assert os.path.exists(geojson_path)
        assert gj["type"] == "FeatureCollection"
        assert len(gj["features"]) >= 1

        feature = gj["features"][0]
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Polygon"
        assert feature["properties"]["mission"] == "ASTRA-GUARD"

        # Verify valid JSON on disk
        with open(geojson_path, encoding="utf-8") as f:
            disk_gj = json.load(f)
            assert disk_gj["type"] == "FeatureCollection"


def test_disaster_risk_module_contract() -> None:
    """Test DisasterRiskModule satisfies unified RiskModule protocol and contract."""
    module = DisasterRiskModule()
    assert isinstance(module, RiskModule)

    # Test fit
    module.fit()
    assert module.is_fitted

    # Test score
    inputs = {
        "area_km2": 75.0,
        "hours_ago": 2.0,
        "cloud_pct": 10.0,
        "population_proxy": 0.75,
    }
    result = module.score(inputs, spacecraft_health_score=0.15)
    assert isinstance(result, ModuleResult)
    assert 0.0 <= result.score <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert result.asset_id == "SENTINEL-2A"
    assert result.synthetic is True
    assert result.evidence["disaster_type"] == "flood"
    assert result.evidence["recommendation"] == "schedule_observation"

    # Test score with degraded health
    result_deg = module.score(inputs, spacecraft_health_score=0.60)
    assert result_deg.evidence["deferred_due_to_health"] is True
    assert result_deg.evidence["recommendation"] == "defer/low-power"
    assert result_deg.score < result.score

    # Test explain
    attributions = module.explain(inputs, result)
    assert len(attributions) == 4
    for attr in attributions:
        assert isinstance(attr, Attribution)
        assert attr.module == "disaster"
        assert attr.contribution >= 0.0
    drivers = {attr.driver for attr in attributions}
    assert drivers == {"flooded_area_km2", "event_recency", "population_exposure", "clear_sky_visibility"}
