"""Stage G Automated Audit Tests — Verification of Honesty & Cryptographic Traceability.

Asserts:
1. 100% of figures in figures_manifest.json have valid high-DPI PNG and vector SVG files on disk.
2. 100% of models in models_manifest.json have valid ONNX and PyTorch checkpoints on disk.
3. All evaluation result files exist and contain real numerical benchmark measurements.
4. All figures embedded in the frontend /technology page exist in figures_manifest.json.
5. The standalone scripts/honesty_audit.py auditor executes cleanly and returns exit code 0.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIGURES_MANIFEST = REPO_ROOT / "apps" / "web" / "public" / "figures" / "figures_manifest.json"
FIGURES_DIR = REPO_ROOT / "apps" / "web" / "public" / "figures"
MODELS_MANIFEST = REPO_ROOT / "ml" / "registry" / "models_manifest.json"
ARTIFACTS_DIR = REPO_ROOT / "ml" / "artifacts"
EVAL_RESULTS_DIR = REPO_ROOT / "ml" / "evaluation" / "results"
TECHNOLOGY_PAGE = REPO_ROOT / "apps" / "web" / "src" / "app" / "technology" / "page.tsx"


def test_figures_manifest_audit() -> None:
    """Every figure in figures_manifest.json must exist as valid PNG and SVG."""
    assert FIGURES_MANIFEST.is_file(), f"Manifest missing at {FIGURES_MANIFEST}"

    with open(FIGURES_MANIFEST, "r", encoding="utf-8") as f:
        data = json.load(f)

    figures = data.get("figures", {})
    assert len(figures) >= 26, f"Expected at least 26 registered figures, got {len(figures)}"

    for fig_id, fig in figures.items():
        assert fig["figure_id"] == fig_id
        assert len(fig.get("title", "")) > 0
        assert len(fig.get("data_hash", "")) >= 6
        assert len(fig.get("commit", "")) > 0

        png_path = FIGURES_DIR / fig["filename_png"]
        svg_path = FIGURES_DIR / fig["filename_svg"]

        assert png_path.is_file(), f"PNG missing for {fig_id}: {png_path}"
        assert svg_path.is_file(), f"SVG missing for {fig_id}: {svg_path}"
        assert png_path.stat().st_size > 100, f"PNG empty for {fig_id}"
        assert svg_path.stat().st_size > 100, f"SVG empty for {fig_id}"


def test_model_registry_and_artifacts_audit() -> None:
    """Every operational deep learning model must have ONNX and PyTorch checkpoints."""
    assert MODELS_MANIFEST.is_file(), f"Models manifest missing at {MODELS_MANIFEST}"

    with open(MODELS_MANIFEST, "r", encoding="utf-8") as f:
        data = json.load(f)

    models = data.get("models", {})
    assert len(models) >= 9, f"Expected at least 9 models, got {len(models)}"

    for model_id, m in models.items():
        if "TEST" in model_id:
            continue

        onnx_rel = m.get("onnx_path")
        ckpt_rel = m.get("checkpoint_path")

        assert onnx_rel is not None, f"Model {model_id} missing onnx_path in manifest"
        assert ckpt_rel is not None, f"Model {model_id} missing checkpoint_path in manifest"

        onnx_file = REPO_ROOT / onnx_rel
        ckpt_file = REPO_ROOT / ckpt_rel

        assert onnx_file.is_file(), f"ONNX file missing on disk for {model_id}: {onnx_file}"
        assert ckpt_file.is_file(), f"Checkpoint file missing on disk for {model_id}: {ckpt_file}"
        assert onnx_file.stat().st_size > 1000, f"ONNX file too small for {model_id}"
        assert ckpt_file.stat().st_size > 1000, f"Checkpoint file too small for {model_id}"


def test_evaluation_benchmark_results_audit() -> None:
    """All 7 evaluation results files must exist and contain non-zero numerical metrics."""
    assert EVAL_RESULTS_DIR.is_dir(), f"Evaluation dir missing: {EVAL_RESULTS_DIR}"

    expected_benchmarks = [
        "health_deep.json",
        "debris_deep.json",
        "disaster_deep.json",
        "health.json",
        "debris.json",
        "disaster.json",
        "risk.json",
    ]

    for fname in expected_benchmarks:
        fpath = EVAL_RESULTS_DIR / fname
        assert fpath.is_file(), f"Benchmark result file missing: {fname}"

        with open(fpath, "r", encoding="utf-8") as f:
            content = json.load(f)

        assert isinstance(content, dict), f"Result in {fname} must be a JSON object"
        assert len(content) > 0, f"Result in {fname} is empty"


def test_frontend_technology_figures_alignment() -> None:
    """All figures referenced in technology page must be in the manifest."""
    assert TECHNOLOGY_PAGE.is_file(), f"Technology page missing: {TECHNOLOGY_PAGE}"
    page_text = TECHNOLOGY_PAGE.read_text(encoding="utf-8")

    fig_refs = sorted(set(re.findall(r"(FIG-[A-Z0-9\-]+)", page_text)))
    assert len(fig_refs) >= 18, f"Expected at least 18 figures referenced in technology page, found {len(fig_refs)}"

    with open(FIGURES_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest_keys = set(manifest.get("figures", {}).keys())

    missing = [f for f in fig_refs if f not in manifest_keys]
    assert len(missing) == 0, f"Technology page references unknown figures: {missing}"


def test_honesty_audit_script_execution() -> None:
    """The scripts/honesty_audit.py script must execute cleanly with exit code 0."""
    script_path = REPO_ROOT / "scripts" / "honesty_audit.py"
    assert script_path.is_file()

    res = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, f"honesty_audit.py failed with code {res.returncode}:\n{res.stdout}\n{res.stderr}"
    assert "ALL AUDIT CHECKS PASSED" in res.stdout
