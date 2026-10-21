"""Unit and integration test suite for Stage A Deep Learning Foundation."""
from pathlib import Path

import torch

from ml.common.dummy_model import DummySequenceModel
from ml.common.onnx_engine import InferenceEngine, export_to_onnx
from ml.common.registry import (
    ModelRegistryEntry,
    compute_data_hash,
    extract_param_counts,
    load_model_registry,
    register_model,
)
from ml.common.train import train_model
from ml.reports.figure_helper import apply_style, load_manifest, save_figure


def test_astra_mono_style_and_figure_helper(tmp_path: Path) -> None:
    """Test that astra_mono.mplstyle applies cleanly and save_figure exports dual PNG/SVG."""
    import matplotlib.pyplot as plt

    apply_style()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([1, 2, 3], [0.5, 0.2, 0.1], linestyle="-", marker="o", label="Test Line")
    ax.set_title("TEST FIGURE")
    ax.legend()

    test_fig_id = "FIG-TEST-STAGE-A-001"
    entry = save_figure(
        fig=fig,
        figure_id=test_fig_id,
        title="Test Figure Title",
        description="Test figure description for Stage A validation.",
        model_version="1.0.0",
        dataset="test_synth",
        data_hash="abc123hash",
        tags=["unit_test"],
    )
    plt.close(fig)

    assert entry["figure_id"] == test_fig_id
    assert entry["commit"] != ""
    assert entry["data_hash"] == "abc123hash"

    manifest = load_manifest()
    assert test_fig_id in manifest["figures"]

    png_path = Path(__file__).resolve().parent.parent.parent / "apps" / "web" / "public" / "figures" / f"{test_fig_id}.png"
    svg_path = Path(__file__).resolve().parent.parent.parent / "apps" / "web" / "public" / "figures" / f"{test_fig_id}.svg"
    assert png_path.exists()
    assert svg_path.exists()
    assert png_path.stat().st_size > 0
    assert svg_path.stat().st_size > 0


def test_registry_metadata_and_torchinfo() -> None:
    """Verify parameter count calculation using torchinfo and data hashing."""
    model = DummySequenceModel(in_channels=4, seq_len=32, hidden_dim=16)
    dummy_input = torch.zeros((1, 32, 4))

    counts = extract_param_counts(model, input_data=dummy_input)
    assert counts["total_params"] > 0
    assert counts["trainable_params"] == counts["total_params"]
    assert counts["model_size_bytes"] > 0

    data = b"astraguard_synthetic_telemetry_stream"
    d_hash = compute_data_hash(data)
    assert len(d_hash) == 64  # SHA-256 length

    test_entry = ModelRegistryEntry(
        model_id="MOD-TEST-REGISTRY-001",
        name="Unit Test Model",
        version="0.0.1",
        architecture="DummySequenceModel",
        subsystem="foundation",
        data_hash=d_hash,
        params_count=counts,
        metrics={"f1": 0.95},
        latency_ms={"p50": 0.05, "p95": 0.08},
    )
    record = register_model(test_entry)
    assert record["model_id"] == "MOD-TEST-REGISTRY-001"

    loaded = load_model_registry()
    assert "MOD-TEST-REGISTRY-001" in loaded["models"]


def test_onnx_export_and_runtime_parity(tmp_path: Path) -> None:
    """Verify ONNX export and parity between PyTorch and ONNX Runtime outputs."""
    model = DummySequenceModel(in_channels=4, seq_len=32, hidden_dim=16)
    model.eval()
    dummy_input = torch.randn(2, 32, 4)

    onnx_file = tmp_path / "test_model.onnx"
    export_to_onnx(
        model=model,
        dummy_input=dummy_input,
        output_path=onnx_file,
        input_names=["input_seq"],
        output_names=["output_seq"],
        dynamic_axes={"input_seq": {0: "batch"}, "output_seq": {0: "batch"}},
    )
    assert onnx_file.exists()

    engine = InferenceEngine(onnx_path=onnx_file, fallback_model=model)
    assert not engine.using_fallback
    assert engine.session is not None

    is_close, max_diff = engine.verify_parity(model, dummy_input, tolerance=1e-4)
    assert is_close
    assert max_diff < 1e-4

    latencies = engine.measure_latency(dummy_input, warmups=5, iterations=20)
    assert latencies["p50"] > 0.0
    assert latencies["p95"] >= latencies["p50"]


def test_config_driven_training_fast_mode() -> None:
    """Verify end-to-end training in fast mode creates weights, logs, and registry entries."""
    config_path = Path(__file__).resolve().parent.parent / "configs" / "dummy_stage_a.yaml"
    assert config_path.exists()

    result = train_model(config_path=config_path, fast=True)
    assert result["model_id"] == "MOD-FOUNDATION-DUMMY-001"
    assert "best_val_loss" in result
    assert result["latency_ms"]["p50"] > 0.0

    out_dir = Path(__file__).resolve().parent.parent / "artifacts" / "dummy_stage_a"
    assert (out_dir / "best_model.pt").exists()
    assert (out_dir / "training_log.csv").exists()
    assert (out_dir / "training_log.json").exists()
    assert (out_dir / "MOD-FOUNDATION-DUMMY-001.onnx").exists()
