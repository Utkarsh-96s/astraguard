"""Generate diagnostic visualization plots for Phase 4 Disaster Intelligence AI."""
import json
import os
import sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from data.synthetic.disaster_gen import generate_synthetic_chip_arrays
from ml.disaster.change_detector import SARChangeDetector
from ml.disaster.module import DisasterRiskModule


def main() -> None:
    output_dir = "notebooks"
    os.makedirs(output_dir, exist_ok=True)
    plot_file = os.path.join(output_dir, "phase4_disaster_diagnostics.png")

    fig, axes = plt.subplots(2, 2, figsize=(15, 11))
    fig.patch.set_facecolor("#080808")

    # Dark theme styling matching design.md
    for ax in axes.flat:
        ax.set_facecolor("#171617")
        ax.tick_params(colors="#d4d2d2")
        ax.xaxis.label.set_color("#fcfcfc")
        ax.yaxis.label.set_color("#fcfcfc")
        ax.title.set_color("#fcfcfc")
        for spine in ax.spines.values():
            spine.set_color("#393939")

    # Load evaluated disaster metrics
    with open("evaluation/results/disaster.json", "r", encoding="utf-8") as f:
        disaster_data = json.load(f)

    # Generate synthetic SAR chip and ground-truth mask
    pre_chip, _ = generate_synthetic_chip_arrays(size=128, water_ratio=0.15, seed=10)
    post_chip, true_mask = generate_synthetic_chip_arrays(size=128, water_ratio=0.35, seed=42)

    module = DisasterRiskModule()
    module.fit()
    pred_mask, _water_ratio, _conf = module.unet.predict_mask(post_chip)

    detector = SARChangeDetector()
    change_res = detector.detect_flood_expansion(pre_chip, post_chip, pred_mask)

    # 1. PANEL 1: Raw Sentinel-1 SAR Backscatter Chip
    ax1 = axes[0, 0]
    im1 = ax1.imshow(post_chip, cmap="bone")
    ax1.set_title("1. Sentinel-1 SAR Backscatter (Raw 128x128 Chip)", fontsize=11, fontweight="bold")
    ax1.set_xticks([])
    ax1.set_yticks([])
    cbar1 = fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.ax.tick_params(colors="#d4d2d2")
    cbar1.set_label("Backscatter Intensity (DN)", color="#fcfcfc", fontsize=9)

    # 2. PANEL 2: Ground-Truth vs U-Net Segmentation Mask
    ax2 = axes[0, 1]
    # Overlay comparison: True Positive (Cyan), False Positive (Yellow), False Negative (Red)
    tp = np.logical_and(pred_mask == 1, true_mask == 1)
    fp = np.logical_and(pred_mask == 1, true_mask == 0)
    fn = np.logical_and(pred_mask == 0, true_mask == 1)

    comp_rgb = np.zeros((128, 128, 3), dtype=np.uint8)
    comp_rgb[tp] = [0, 220, 255]    # Cyan (Accurate flood detection)
    comp_rgb[fp] = [245, 158, 11]   # Amber (False Positive)
    comp_rgb[fn] = [254, 30, 52]    # Red (False Negative)

    ax2.imshow(comp_rgb)
    iou = disaster_data["segmentation_metrics"]["iou"]
    f1 = disaster_data["segmentation_metrics"]["dice_f1"]
    ax2.set_title(f"2. U-Net Segmentation vs Truth (IoU: {iou:.3f} | F1: {f1:.3f})", fontsize=11, fontweight="bold")
    ax2.set_xticks([])
    ax2.set_yticks([])
    # Custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="#00dcff", lw=4, label="True Positive (Flood)"),
        Line2D([0], [0], color="#f59e0b", lw=4, label="False Positive"),
        Line2D([0], [0], color="#fe1e34", lw=4, label="False Negative"),
    ]
    ax2.legend(handles=legend_elements, facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper right", fontsize=8)

    # 3. PANEL 3: Temporal Change Detection (New Flood Inundation)
    ax3 = axes[1, 0]
    # Base is post SAR image with bright red/amber highlight on newly inundated pixels
    change_overlay = np.dstack([post_chip, post_chip, post_chip])
    new_mask = change_res["new_water_mask"] == 1
    change_overlay[new_mask] = [254, 30, 52]  # Highlight new flood expansion in red

    ax3.imshow(change_overlay)
    new_area = change_res["new_flooded_area_km2"]
    ax3.set_title(f"3. Change Detection: Newly Inundated Terrain (+{new_area} km²)", fontsize=11, fontweight="bold")
    ax3.set_xticks([])
    ax3.set_yticks([])

    # 4. PANEL 4: Observation Priority Scoring Breakdown & Health Cross-Effect
    ax4 = axes[1, 1]
    priority_nom = disaster_data["observation_priority_cross_effects"]["nominal_priority"]
    priority_deg = disaster_data["observation_priority_cross_effects"]["degraded_health_priority"]

    categories = [
        "Area (40%)", "Recency (25%)", "Pop. Exposure (20%)", "Cloud Factor (15%)",
        "Nominal Score (r_e)", "Degraded Score (r_h ≥ 0.5)",
    ]
    vals = [
        0.40 * min(1.0, 180.0 / 500.0),
        0.25 * max(0.0, 1.0 - (1.5 / 72.0)),
        0.20 * 0.80,
        0.15 * max(0.0, 1.0 - (5.0 / 100.0)),
        priority_nom,
        priority_deg,
    ]
    colors = ["#38bdf8", "#38bdf8", "#38bdf8", "#38bdf8", "#10b981", "#fe1e34"]

    bars = ax4.barh(categories, vals, color=colors, height=0.55)
    ax4.set_title("4. Observation Priority Scoring & Health Safety Cross-Effect", fontsize=11, fontweight="bold")
    ax4.set_xlabel("Score Contribution")
    for bar in bars:
        w = bar.get_width()
        ax4.text(w + 0.015, bar.get_y() + bar.get_height() / 2, f"{w:.3f}", va="center", color="#fcfcfc", fontsize=9)
    ax4.set_xlim(0, 1.0)
    ax4.grid(True, color="#262525", linestyle=":", axis="x")

    plt.tight_layout()
    plt.savefig(plot_file, dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Successfully generated Phase 4 diagnostic plot: {plot_file}", flush=True)


if __name__ == "__main__":
    main()
