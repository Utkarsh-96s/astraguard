"""Exhaustive tests for deep learning model registry, figures catalog, and real-time ONNX inference."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_models_classic_backwards_compatible(client: AsyncClient) -> None:
    """Verify GET /api/v1/models without query params strictly returns the 4 classic models."""
    res = await client.get("/api/v1/models")
    assert res.status_code == 200
    models = res.json()
    assert len(models) == 4

    ids = {m["id"] for m in models}
    assert "MOD-HEALTH-001" in ids
    assert "MOD-DEBRIS-001" in ids
    assert "MOD-DISASTER-001" in ids
    assert "MOD-FUSION-001" in ids


@pytest.mark.asyncio
async def test_get_models_deep_and_all(client: AsyncClient) -> None:
    """Verify deep models catalog query, single lookup, and view=all mode."""
    # 1. view=deep query
    res = await client.get("/api/v1/models?view=deep")
    assert res.status_code == 200
    deep_models = res.json()
    assert len(deep_models) == 8  # 3 health + 3 debris + 2 disaster

    # 2. Dedicated /deep endpoint
    res_deep = await client.get("/api/v1/models/deep")
    assert res_deep.status_code == 200
    deep_catalog = res_deep.json()
    assert len(deep_catalog) == 8

    deep_ids = {m["model_id"] for m in deep_catalog}
    assert "MOD-HEALTH-TCN-001" in deep_ids
    assert "MOD-HEALTH-LSTM-001" in deep_ids
    assert "MOD-HEALTH-TRANSFORMER-001" in deep_ids
    assert "MOD-DEBRIS-CNN-001" in deep_ids
    assert "MOD-DEBRIS-GRU-001" in deep_ids
    assert "MOD-DEBRIS-LSTM-001" in deep_ids
    assert "MOD-DISASTER-UNET-001" in deep_ids
    assert "MOD-DISASTER-SIAMESE-001" in deep_ids

    # 3. Filter by subsystem
    res_health = await client.get("/api/v1/models/deep?subsystem=health")
    assert res_health.status_code == 200
    assert len(res_health.json()) == 3

    # 4. Single model lookup
    res_single = await client.get("/api/v1/models/deep/MOD-HEALTH-TCN-001")
    assert res_single.status_code == 200
    single_data = res_single.json()
    assert single_data["architecture"] == "TCNAutoencoderNet"
    assert single_data["total_params"] > 0
    assert "p50" in single_data["latency_ms"]

    # 404 for unknown model
    res_404 = await client.get("/api/v1/models/deep/UNKNOWN-MODEL-999")
    assert res_404.status_code == 404

    # 5. view=all query
    res_all = await client.get("/api/v1/models?view=all")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 12  # 4 classic + 8 deep


@pytest.mark.asyncio
async def test_figures_catalog(client: AsyncClient) -> None:
    """Verify SpaceX monochrome figures catalog and filtering."""
    res = await client.get("/api/v1/figures")
    assert res.status_code == 200
    figures = res.json()
    assert len(figures) == 26

    fig_map = {f["figure_id"]: f for f in figures}
    assert "FIG-HEALTH-DEEP-TRAIN-LOSS" in fig_map
    assert "FIG-DEBRIS-CALIBRATION-CURVE" in fig_map
    assert "FIG-DISASTER-UNET-SEGMENTATION" in fig_map
    assert "FIG-DISASTER-FAILURE-CASES" in fig_map

    # Filter by subsystem
    res_sub = await client.get("/api/v1/figures?subsystem=disaster")
    assert res_sub.status_code == 200
    assert len(res_sub.json()) >= 6

    # Single figure lookup
    res_single = await client.get("/api/v1/figures/FIG-DISASTER-GRAD-CAM")
    assert res_single.status_code == 200
    fig_data = res_single.json()
    assert fig_data["filename_svg"] == "FIG-DISASTER-GRAD-CAM.svg"
    assert "/figures/" in fig_data["url_svg"]

    # 404 for unknown figure
    res_404 = await client.get("/api/v1/figures/FIG-UNKNOWN-000")
    assert res_404.status_code == 404


@pytest.mark.asyncio
async def test_health_inference(client: AsyncClient) -> None:
    """Verify real-time ONNX health anomaly detection and residual attribution."""
    # 1. Battery thermal runaway anomaly preset
    res_anomaly = await client.post(
        "/api/v1/infer/health",
        json={"model_id": "MOD-HEALTH-TCN-001", "sample_id": "battery_thermal_runaway"},
    )
    assert res_anomaly.status_code == 200
    data_anomaly = res_anomaly.json()
    assert data_anomaly["is_anomaly"] is True
    assert data_anomaly["anomaly_score"] > data_anomaly["threshold"]
    assert "wheel_temp" in data_anomaly["channel_attributions"]
    assert data_anomaly["latency_ms"] < 25.0

    # 2. Nominal orbit pass preset
    res_nominal = await client.post(
        "/api/v1/infer/health",
        json={"model_id": "MOD-HEALTH-TCN-001", "sample_id": "nominal"},
    )
    assert res_nominal.status_code == 200
    data_nominal = res_nominal.json()
    assert data_nominal["is_anomaly"] is False
    assert data_nominal["anomaly_score"] <= data_nominal["threshold"]

    # 3. Model switching to LSTM and Transformer
    for mid in ["MOD-HEALTH-LSTM-001", "MOD-HEALTH-TRANSFORMER-001"]:
        res_m = await client.post(
            "/api/v1/infer/health",
            json={"model_id": mid, "sample_id": "solar_panel_degradation"},
        )
        assert res_m.status_code == 200
        assert res_m.json()["model_id"] == mid


@pytest.mark.asyncio
async def test_debris_inference(client: AsyncClient) -> None:
    """Verify real-time ONNX debris classification and Platt calibration."""
    # 1. Critical collision decay preset
    res_crit = await client.post(
        "/api/v1/infer/debris",
        json={"model_id": "MOD-DEBRIS-CNN-001", "sample_id": "critical_collision_decay"},
    )
    assert res_crit.status_code == 200
    data_crit = res_crit.json()
    assert data_crit["risk_level"] == "CRITICAL"
    assert data_crit["calibrated_risk_probability"] >= 1e-4
    assert len(data_crit["temporal_attributions"]) == 10
    assert "MANEUVER" in data_crit["operational_recommendation"]
    assert data_crit["latency_ms"] < 15.0

    # 2. Nominal flyby preset
    res_nom = await client.post(
        "/api/v1/infer/debris",
        json={"model_id": "MOD-DEBRIS-CNN-001", "sample_id": "nominal_flyby"},
    )
    assert res_nom.status_code == 200
    data_nom = res_nom.json()
    assert data_nom["risk_level"] == "NOMINAL"
    assert data_nom["calibrated_risk_probability"] < 1e-5

    # 3. Model switching to GRU
    res_gru = await client.post(
        "/api/v1/infer/debris",
        json={"model_id": "MOD-DEBRIS-GRU-001", "sample_id": "critical_collision_decay"},
    )
    assert res_gru.status_code == 200
    assert res_gru.json()["model_id"] == "MOD-DEBRIS-GRU-001"


@pytest.mark.asyncio
async def test_disaster_inference(client: AsyncClient) -> None:
    """Verify real-time ONNX SAR flood segmentation and runway false positive suppression."""
    # 1. Dual-temporal Siamese Change U-Net on monsoon flood with airport runway
    res_siamese = await client.post(
        "/api/v1/infer/disaster",
        json={"model_id": "MOD-DISASTER-SIAMESE-001", "sample_id": "monsoon_flood_runway_present"},
    )
    assert res_siamese.status_code == 200
    data_siamese = res_siamese.json()
    assert data_siamese["flood_fraction"] > 0.05
    assert data_siamese["inundated_pixels"] > 0
    assert data_siamese["inundated_area_km2"] > 0.0
    assert data_siamese["specular_runway_rejected"] is True
    assert len(data_siamese["spatial_attention_grid"]) == 16
    assert len(data_siamese["spatial_attention_grid"][0]) == 16
    assert data_siamese["latency_ms"] < 35.0

    # 2. Dry terrain preset
    res_dry = await client.post(
        "/api/v1/infer/disaster",
        json={"model_id": "MOD-DISASTER-SIAMESE-001", "sample_id": "nominal_dry_season"},
    )
    assert res_dry.status_code == 200
    assert res_dry.json()["flood_fraction"] == 0.0

    # 3. Single-chip U-Net
    res_unet = await client.post(
        "/api/v1/infer/disaster",
        json={"model_id": "MOD-DISASTER-UNET-001", "sample_id": "monsoon_flood_runway_present"},
    )
    assert res_unet.status_code == 200
    assert res_unet.json()["model_id"] == "MOD-DISASTER-UNET-001"


@pytest.mark.asyncio
async def test_sample_presets_endpoint(client: AsyncClient) -> None:
    """Verify mission preset catalog across all 3 subsystems."""
    for sub in ["health", "debris", "disaster"]:
        res = await client.get(f"/api/v1/infer/samples/{sub}")
        assert res.status_code == 200
        presets = res.json()
        assert len(presets) >= 3
        for p in presets:
            assert p["subsystem"] == sub
            assert len(p["id"]) > 0
            assert len(p["description"]) > 0

    # Invalid subsystem
    res_err = await client.get("/api/v1/infer/samples/invalid_subsystem")
    assert res_err.status_code == 400
