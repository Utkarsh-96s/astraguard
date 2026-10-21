"""Unit and integration test suite for Stage B Spacecraft Health Deep Models."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from ml.common.onnx_engine import export_to_onnx
from ml.health.baselines import IsolationForestBaseline, RollingZScoreDetector
from ml.health.explanations import (
    compute_integrated_gradients_attributions,
    compute_residual_matrix,
)
from ml.health.lstm_ae import LSTMAutoencoderNet
from ml.health.tcn_ae import TCNAutoencoderNet
from ml.health.transformer_ae import TransformerAutoencoderNet


def test_baseline_detectors() -> None:
    """Verify statistical and tabular baselines run and return valid score arrays."""
    channel_names = ["wheel_temp", "bus_current", "battery_v", "gyro_rate_x", "gyro_rate_y", "gyro_rate_z", "sun_sensor"]

    # Rolling Z-score test
    records = []
    for ch in channel_names:
        for t in range(50):
            records.append({"timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(seconds=t), "channel": ch, "value": 1.0})
    df_nominal = pd.DataFrame(records)

    z_detector = RollingZScoreDetector(window_size=32, threshold_sigma=3.0, channels=channel_names)
    z_detector.fit(df_nominal)
    assert z_detector.is_fitted

    test_records = []
    for ch in channel_names:
        for t in range(32):
            val = 10.0 if ch == "wheel_temp" and t == 31 else 1.0
            test_records.append({"timestamp": pd.Timestamp("2026-01-01 01:00") + pd.Timedelta(seconds=t), "channel": ch, "value": val})
    res = z_detector.score_window(pd.DataFrame(test_records))
    assert res.score > 0.0
    assert res.raw_metric > 3.0
    assert res.is_anomaly

    # Isolation Forest test
    windows_nominal = np.random.normal(0, 1, size=(20, 32, 7)).astype(np.float32)
    if_detector = IsolationForestBaseline(n_estimators=30, contamination=0.05, random_state=42)
    if_detector.fit(windows_nominal, channel_names)
    assert if_detector.is_fitted

    test_window = np.random.normal(0, 1, size=(1, 32, 7)).astype(np.float32)
    test_window[0, :, 0] += 10.0
    cal_score, _raw_res, ev = if_detector.predict_window(test_window)
    assert 0.0 <= cal_score <= 1.0
    assert "model_type" in ev


def test_deep_architectures_forward_and_onnx(tmp_path: Path) -> None:
    """Verify forward pass and ONNX export for LSTM, TCN, and Transformer autoencoders."""
    batch_size = 2
    seq_len = 64
    in_channels = 7
    dummy_input = torch.randn(batch_size, seq_len, in_channels)

    models = [
        ("lstm", LSTMAutoencoderNet(input_dim=in_channels, hidden_dim=32, latent_dim=16)),
        ("tcn", TCNAutoencoderNet(input_dim=in_channels, hidden_dim=32, latent_dim=16, kernel_size=3)),
        ("transformer", TransformerAutoencoderNet(input_dim=in_channels, d_model=32, nhead=4, num_layers=2)),
    ]

    for name, model in models:
        model.eval()
        with torch.no_grad():
            out = model(dummy_input)
            assert out.shape == dummy_input.shape, f"{name} output shape {out.shape} != input {dummy_input.shape}"

        onnx_path = tmp_path / f"{name}_test.onnx"
        export_to_onnx(
            model=model,
            dummy_input=dummy_input,
            output_path=onnx_path,
            input_names=["telemetry_seq"],
            output_names=["reconstructed_seq"],
        )
        assert onnx_path.exists()
        assert onnx_path.stat().st_size > 0


def test_explainability_methods() -> None:
    """Verify residual heatmap calculation and Captum Integrated Gradients attribution ranking."""
    seq_len = 32
    channels = 7
    raw = torch.randn(seq_len, channels)
    recon = raw + 0.1 * torch.randn(seq_len, channels)

    # Residual matrix: shape (channels, seq_len)
    residuals = compute_residual_matrix(raw, recon)
    assert residuals.shape == (channels, seq_len)
    assert (residuals >= 0).all()

    # Captum Integrated Gradients
    channel_names = ["wheel_temp", "bus_current", "battery_v", "gyro_x", "gyro_y", "gyro_z", "sun_sensor"]
    model = TCNAutoencoderNet(input_dim=channels, hidden_dim=16, latent_dim=8, kernel_size=3)
    model.eval()

    sample = torch.randn(1, seq_len, channels)
    attributions = compute_integrated_gradients_attributions(
        model=model,
        input_tensor=sample,
        channel_names=channel_names,
        n_steps=5,
    )
    assert len(attributions) == channels
    assert all(hasattr(item, "driver") and hasattr(item, "contribution") for item in attributions)
    # Ensure contributions are sorted descending
    contributions = [item.contribution for item in attributions]
    assert contributions == sorted(contributions, reverse=True)


def test_stage_b_evaluation_and_figures_manifest() -> None:
    """Verify Stage B evaluation json and that all 6 figures are registered in manifest and exist on disk."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    results_path = repo_root / "ml" / "evaluation" / "results" / "health_deep.json"
    manifest_path = repo_root / "apps" / "web" / "public" / "figures" / "figures_manifest.json"

    assert results_path.exists(), "health_deep.json evaluation results missing"
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "baselines" in data
    assert "rolling_zscore" in data["baselines"]
    assert "isolation_forest" in data["baselines"]
    assert "deep_models" in data
    assert "lstm_autoencoder" in data["deep_models"]
    assert "tcn_autoencoder" in data["deep_models"]
    assert "transformer_autoencoder" in data["deep_models"]
    assert "honest_comparison" in data

    # Verify figures manifest
    assert manifest_path.exists(), "figures_manifest.json missing"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    expected_figures = [
        "FIG-HEALTH-DEEP-TRAIN-LOSS",
        "FIG-HEALTH-TELEMETRY-RECON",
        "FIG-HEALTH-RESIDUAL-HEATMAP",
        "FIG-HEALTH-CAPTUM-IG",
        "FIG-HEALTH-MODEL-COMPARISON",
        "FIG-HEALTH-ROC-PR",
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
