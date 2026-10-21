"""Unit and integration test suite for Stage D Disaster Imagery Deep Models."""
import json
from pathlib import Path

import numpy as np
import torch

from ml.common.onnx_engine import export_to_onnx
from ml.disaster.baselines import (
    BackscatterDifferencingBaseline,
    OtsuThresholdBaseline,
    compute_segmentation_metrics,
)
from ml.disaster.dataset import generate_sar_flood_dataset
from ml.disaster.explanations import SARGradCAM
from ml.disaster.siamese_unet import SiameseChangeUNet
from ml.disaster.unet import UNet


def test_disaster_dataset_generator() -> None:
    """Verify SAR dual-temporal chip dataset generator outputs valid shapes and data hash."""
    num_chips = 10
    size = 64
    chips, masks, meta, data_hash = generate_sar_flood_dataset(
        num_chips=num_chips,
        size=size,
        seed=42,
    )

    assert chips.shape == (num_chips, 2, size, size)
    assert masks.shape == (num_chips, 1, size, size)
    assert len(data_hash) == 64
    assert len(meta["chips"]) == num_chips
    assert (chips >= 0.0).all() and (chips <= 1.0).all()
    assert set(np.unique(masks)).issubset({0.0, 1.0})


def test_disaster_baselines_and_metrics() -> None:
    """Verify OtsuThresholdBaseline, BackscatterDifferencingBaseline, and metric calculation."""
    chips, masks, _, _ = generate_sar_flood_dataset(num_chips=10, size=64, seed=42)
    pre = chips[:, 0]
    post = chips[:, 1]

    # Otsu baseline
    otsu = OtsuThresholdBaseline()
    otsu.fit(post)
    assert otsu.is_fitted
    pred_otsu = otsu.predict(post[0])
    assert pred_otsu.shape == (64, 64)

    # Differencing baseline
    diff_base = BackscatterDifferencingBaseline(diff_threshold=0.20)
    pred_diff = diff_base.predict(pre[0], post[0])
    assert pred_diff.shape == (64, 64)

    # Metrics
    metrics = compute_segmentation_metrics(pred_diff, masks[0, 0])
    assert "iou" in metrics
    assert "dice_f1" in metrics
    assert 0.0 <= metrics["iou"] <= 1.0
    assert 0.0 <= metrics["dice_f1"] <= 1.0


def test_unet_and_siamese_forward_and_onnx(tmp_path: Path) -> None:
    """Verify forward pass and ONNX export for UNet and SiameseChangeUNet."""
    batch_size = 2
    size = 64

    # Single-date U-Net
    unet = UNet(in_channels=1, out_channels=1, base_filters=16)
    unet.eval()
    dummy_unet_in = torch.randn(batch_size, 1, size, size)
    with torch.no_grad():
        out_unet = unet(dummy_unet_in)
        assert out_unet.shape == (batch_size, 1, size, size)

    onnx_unet = tmp_path / "unet_test.onnx"
    export_to_onnx(
        model=unet,
        dummy_input=dummy_unet_in,
        output_path=onnx_unet,
        input_names=["sar_post_chip"],
        output_names=["flood_map"],
    )
    assert onnx_unet.exists()
    assert onnx_unet.stat().st_size > 0

    # Dual-temporal Siamese Change U-Net
    siamese = SiameseChangeUNet(in_channels=2, out_channels=1, base_filters=16)
    siamese.eval()
    dummy_siamese_in = torch.randn(batch_size, 2, size, size)
    with torch.no_grad():
        out_siamese = siamese(dummy_siamese_in)
        assert out_siamese.shape == (batch_size, 1, size, size)

    onnx_siamese = tmp_path / "siamese_test.onnx"
    export_to_onnx(
        model=siamese,
        dummy_input=dummy_siamese_in,
        output_path=onnx_siamese,
        input_names=["sar_pair_chips"],
        output_names=["change_map"],
    )
    assert onnx_siamese.exists()
    assert onnx_siamese.stat().st_size > 0


def test_sar_gradcam_heatmap() -> None:
    """Verify Grad-CAM produces a normalized 2D attention heatmap."""
    size = 64
    model = UNet(in_channels=1, out_channels=1, base_filters=16)
    model.eval()

    gradcam = SARGradCAM(model)
    dummy_input = torch.randn(1, 1, size, size)
    heatmap = gradcam.generate_heatmap(dummy_input)

    assert heatmap.shape == (size, size)
    assert (heatmap >= 0.0).all() and (heatmap <= 1.0).all()


def test_stage_d_evaluation_and_figures_manifest() -> None:
    """Verify disaster_deep.json and all 6 Stage D figures registered in figures_manifest.json."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    results_path = repo_root / "ml" / "evaluation" / "results" / "disaster_deep.json"
    manifest_path = repo_root / "apps" / "web" / "public" / "figures" / "figures_manifest.json"

    assert results_path.exists(), "disaster_deep.json results file missing"
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "baselines" in data
    assert "otsu_thresholding" in data["baselines"]
    assert "backscatter_differencing" in data["baselines"]
    assert "deep_models" in data
    assert "MOD-DISASTER-UNET-001" in data["deep_models"]
    assert "MOD-DISASTER-SIAMESE-001" in data["deep_models"]
    assert "failure_case_analysis" in data
    assert "honest_comparison" in data

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    expected_figures = [
        "FIG-DISASTER-TRAIN-LOSS",
        "FIG-DISASTER-UNET-SEGMENTATION",
        "FIG-DISASTER-GRAD-CAM",
        "FIG-DISASTER-CHANGE-DETECTION",
        "FIG-DISASTER-MODEL-COMPARISON",
        "FIG-DISASTER-FAILURE-CASES",
    ]

    for fig_id in expected_figures:
        assert fig_id in manifest["figures"], f"{fig_id} not in manifest"
        entry = manifest["figures"][fig_id]
        png_file = repo_root / "apps" / "web" / "public" / "figures" / entry["filename_png"]
        svg_file = repo_root / "apps" / "web" / "public" / "figures" / entry["filename_svg"]
        assert png_file.exists(), f"PNG missing for {fig_id}"
        assert svg_file.exists(), f"SVG missing for {fig_id}"
        assert png_file.stat().st_size > 0
        assert svg_file.stat().st_size > 0
