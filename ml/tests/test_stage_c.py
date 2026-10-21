"""Unit and integration test suite for Stage C Debris Risk Deep Models."""
import json
from pathlib import Path

import torch

from ml.common.onnx_engine import export_to_onnx
from ml.debris.baselines import (
    CDM_FEATURE_NAMES,
    DebrisProbabilityCalibrator,
    LatestCDMThresholdBaseline,
    XGBoostSequenceBaseline,
)
from ml.debris.cnn_classifier import Debris1DCNNClassifierNet
from ml.debris.dataset import generate_kelvins_cdm_dataset
from ml.debris.explanations import compute_debris_integrated_gradients
from ml.debris.gru_classifier import DebrisGRUClassifierNet, DebrisLSTMClassifierNet


def test_debris_dataset_generator() -> None:
    """Verify synthetic Kelvins CDM sequence generator produces valid 3D tensors and hashes."""
    num_events = 20
    seq_len = 8
    X_seq, y, metadata, data_hash = generate_kelvins_cdm_dataset(
        num_events=num_events,
        seq_len=seq_len,
        seed=42,
    )

    assert X_seq.shape == (num_events, seq_len, len(CDM_FEATURE_NAMES))
    assert len(y) == num_events
    assert len(metadata) == num_events
    assert len(data_hash) == 64
    assert set(y).issubset({0.0, 1.0})


def test_debris_baselines_and_calibrator() -> None:
    """Verify LatestCDMThresholdBaseline, XGBoostSequenceBaseline, and DebrisProbabilityCalibrator."""
    X_seq, y, _, _ = generate_kelvins_cdm_dataset(num_events=30, seq_len=6, seed=42)

    # Physical Threshold
    thresh_model = LatestCDMThresholdBaseline()
    thresh_model.fit(X_seq, y)
    probs_thresh = thresh_model.predict_proba(X_seq)
    assert probs_thresh.shape == (30, 2)
    assert (probs_thresh >= 0.0).all() and (probs_thresh <= 1.0).all()

    # XGBoost Sequence
    xgb_model = XGBoostSequenceBaseline(n_estimators=20, max_depth=2, random_state=42)
    xgb_model.fit(X_seq, y)
    assert xgb_model.is_fitted
    probs_xgb = xgb_model.predict_proba(X_seq)
    assert probs_xgb.shape == (30, 2)

    # Probability Calibrator
    raw_p = probs_thresh[:, 1]
    calibrator = DebrisProbabilityCalibrator(n_bins=5)
    calibrator.fit(raw_p, y)
    assert calibrator.is_calibrated
    cal_p = calibrator.calibrate(raw_p)
    assert len(cal_p) == len(raw_p)
    assert (cal_p >= 0.0).all() and (cal_p <= 1.0).all()

    ece = DebrisProbabilityCalibrator.compute_ece(cal_p, y, n_bins=5)
    brier = DebrisProbabilityCalibrator.compute_brier_score(cal_p, y)
    assert 0.0 <= ece <= 1.0
    assert 0.0 <= brier <= 1.0


def test_debris_deep_models_forward_and_onnx(tmp_path: Path) -> None:
    """Verify forward pass and ONNX export for GRU, LSTM, and 1D-CNN sequence classifiers."""
    batch_size = 2
    seq_len = 10
    input_dim = 7
    dummy_input = torch.randn(batch_size, seq_len, input_dim)

    models = [
        ("gru", DebrisGRUClassifierNet(input_dim=input_dim, hidden_dim=16, num_layers=2)),
        ("lstm", DebrisLSTMClassifierNet(input_dim=input_dim, hidden_dim=16, num_layers=2)),
        ("cnn", Debris1DCNNClassifierNet(input_dim=input_dim, branch_channels=8, hidden_dim=16)),
    ]

    for name, model in models:
        model.eval()
        with torch.no_grad():
            out = model(dummy_input)
            assert out.shape == (batch_size, 1), f"{name} output shape {out.shape} != {(batch_size, 1)}"
            probs = model.predict_proba(dummy_input)
            assert (probs >= 0.0).all() and (probs <= 1.0).all()

        onnx_file = tmp_path / f"{name}_classifier.onnx"
        export_to_onnx(
            model=model,
            dummy_input=dummy_input,
            output_path=onnx_file,
            input_names=["cdm_sequence"],
            output_names=["critical_risk_logits"],
        )
        assert onnx_file.exists()
        assert onnx_file.stat().st_size > 0


def test_debris_integrated_gradients_explainability() -> None:
    """Verify Captum Integrated Gradients returns temporal and feature attributions."""
    seq_len = 8
    input_dim = 7
    model = DebrisGRUClassifierNet(input_dim=input_dim, hidden_dim=16, num_layers=1)
    model.eval()

    sample = torch.randn(1, seq_len, input_dim)
    hours = [72.0, 48.0, 36.0, 24.0, 18.0, 12.0, 8.0, 4.0]

    attr_res = compute_debris_integrated_gradients(
        model=model,
        input_seq=sample,
        feature_names=CDM_FEATURE_NAMES,
        time_to_tca_hours=hours,
        n_steps=5,
    )

    assert "feature_attributions" in attr_res
    assert len(attr_res["feature_attributions"]) == input_dim
    assert hasattr(attr_res["feature_attributions"][0], "driver")

    assert "temporal_attributions" in attr_res
    assert len(attr_res["temporal_attributions"]) == seq_len

    assert "attribution_matrix" in attr_res
    assert attr_res["attribution_matrix"].shape == (input_dim, seq_len)


def test_stage_c_evaluation_and_figures_manifest() -> None:
    """Verify debris_deep.json evaluation output and 6 registered Stage C figures."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    results_path = repo_root / "ml" / "evaluation" / "results" / "debris_deep.json"
    manifest_path = repo_root / "apps" / "web" / "public" / "figures" / "figures_manifest.json"

    assert results_path.exists(), "debris_deep.json evaluation results missing"
    with open(results_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "baselines" in data
    assert "latest_cdm_threshold" in data["baselines"]
    assert "xgboost_sequence_summary" in data["baselines"]
    assert "deep_models" in data
    assert "MOD-DEBRIS-GRU-001" in data["deep_models"]
    assert "MOD-DEBRIS-CNN-001" in data["deep_models"]
    assert "MOD-DEBRIS-LSTM-001" in data["deep_models"]
    assert "honest_comparison" in data

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    expected_figures = [
        "FIG-DEBRIS-TRAIN-LOSS",
        "FIG-DEBRIS-CDM-SEQUENCE-EVOLUTION",
        "FIG-DEBRIS-CALIBRATION-CURVE",
        "FIG-DEBRIS-MODEL-COMPARISON",
        "FIG-DEBRIS-ROC-PR",
        "FIG-DEBRIS-TEMPORAL-ATTRIBUTION",
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
