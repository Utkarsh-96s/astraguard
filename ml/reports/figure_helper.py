"""Monochrome figure helper and manifest management for ASTRA-GUARD."""
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

STYLE_PATH = Path(__file__).parent / "astra_mono.mplstyle"
FIGURES_DIR = Path(__file__).resolve().parent.parent.parent / "apps" / "web" / "public" / "figures"
MANIFEST_PATH = FIGURES_DIR / "figures_manifest.json"


def apply_style() -> None:
    """Apply the SpaceX monochrome matplotlib style."""
    if STYLE_PATH.exists():
        plt.style.use(str(STYLE_PATH))


def get_git_commit() -> str:
    """Retrieve current git commit hash, or fallback to 'uncommitted'."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return "development"


def load_manifest() -> dict[str, Any]:
    """Load existing figures manifest or return empty structure."""
    if MANIFEST_PATH.exists():
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "manifest_version": "1.0.0",
        "last_updated": datetime.now(UTC).isoformat(),
        "figures": {},
    }


def save_figure(
    fig: plt.Figure,
    figure_id: str,
    title: str,
    description: str,
    model_version: str,
    dataset: str,
    data_hash: str,
    tags: list[str] | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Save high-resolution PNG (2x) and SVG to apps/web/public/figures/ and update figures_manifest.json.

    Args:
        fig: The matplotlib Figure instance to save.
        figure_id: Unique figure identifier (e.g. 'FIG-HEALTH-LSTM-LOSS').
        title: Descriptive human-readable title.
        description: Informative explanation of what the figure demonstrates.
        model_version: Model identifier/version that produced this output.
        dataset: Training or evaluation dataset identifier.
        data_hash: SHA-256 hash of the input dataset/window.
        tags: Optional category tags.
        extra_metadata: Additional key-value pairs for traceability.

    Returns:
        The manifest entry for the saved figure.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    png_filename = f"{figure_id}.png"
    svg_filename = f"{figure_id}.svg"
    png_path = FIGURES_DIR / png_filename
    svg_path = FIGURES_DIR / svg_filename

    # Save high-DPI raster and clean vector
    fig.savefig(png_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    fig.savefig(svg_path, facecolor=fig.get_facecolor(), edgecolor="none")

    commit = get_git_commit()
    timestamp = datetime.now(UTC).isoformat()

    manifest_data = load_manifest()
    entry: dict[str, Any] = {
        "figure_id": figure_id,
        "title": title,
        "description": description,
        "filename_png": png_filename,
        "filename_svg": svg_filename,
        "url_png": f"/figures/{png_filename}",
        "url_svg": f"/figures/{svg_filename}",
        "model_version": model_version,
        "dataset": dataset,
        "data_hash": data_hash,
        "commit": commit,
        "timestamp": timestamp,
        "tags": tags or [],
        "metadata": extra_metadata or {},
    }

    manifest_data["figures"][figure_id] = entry
    manifest_data["last_updated"] = timestamp

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    return entry
