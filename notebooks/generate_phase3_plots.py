"""Generate diagnostic visualization plots for Phase 3 Debris Collision Risk AI."""
import json
import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse

from data.synthetic.debris_gen import generate_cdm_progression
from ml.debris.module import DebrisRiskModule


def main() -> None:
    output_dir = "notebooks"
    os.makedirs(output_dir, exist_ok=True)
    plot_file = os.path.join(output_dir, "phase3_debris_diagnostics.png")

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

    # Load evaluated debris metrics
    with open("evaluation/results/debris.json", "r", encoding="utf-8") as f:
        debris_data = json.load(f)

    # 1. PANEL 1: SGP4 Analytical Propagation Error vs Horizon
    ax1 = axes[0, 0]
    horizons = debris_data["sgp4_propagation_error"]["horizons_hours"]
    errors = debris_data["sgp4_propagation_error"]["error_km"]

    ax1.plot(horizons, errors, "o-", color="#38bdf8", linewidth=2.0, markersize=6, label="SGP4 Ephemeris Drift (km)")
    ax1.axvline(24, color="#10b981", linestyle="--", alpha=0.7, label=f"24h Error: {debris_data['sgp4_propagation_error']['error_24h_km']} km")
    ax1.axvline(72, color="#fe1e34", linestyle="--", alpha=0.7, label=f"72h Error: {debris_data['sgp4_propagation_error']['error_72h_km']} km")
    ax1.set_title("1. SGP4 Propagation Position Error vs. Horizon", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Propagation Horizon (Hours)")
    ax1.set_ylabel("Position Uncertainty (km)")
    ax1.legend(facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper left")
    ax1.grid(True, color="#262525", linestyle=":")

    # 2. PANEL 2: Foster 2-D Encounter Plane (B-Plane) Geometry
    ax2 = axes[0, 1]
    # Covariance ellipse parameters (sigma_x = 50m, sigma_y = 250m)
    sig_x, sig_y = 50.0, 250.0
    miss_x, miss_y = 35.0, 80.0

    # 1-sigma and 3-sigma ellipses
    ellipse_1sig = Ellipse((0, 0), width=2*sig_x, height=2*sig_y, angle=15, edgecolor="#f59e0b", facecolor="none", linestyle="--", linewidth=1.5, label="1-σ Combined Covariance")
    ellipse_3sig = Ellipse((0, 0), width=6*sig_x, height=6*sig_y, angle=15, edgecolor="#71717a", facecolor="#f59e0b", alpha=0.08, linewidth=1.0, label="3-σ Boundary")
    ax2.add_patch(ellipse_3sig)
    ax2.add_patch(ellipse_1sig)

    # Primary asset at origin, Secondary at miss coordinates
    ax2.plot(0, 0, "o", color="#10b981", markersize=8, label="Primary Asset (SENTINEL-2A)")
    ax2.plot(miss_x, miss_y, "x", color="#fe1e34", markersize=10, markeredgewidth=2.5, label=f"Secondary Debris ({miss_x}m, {miss_y}m)")
    ax2.plot([0, miss_x], [0, miss_y], color="#fe1e34", linestyle=":", linewidth=1.5, label=f"Miss Distance: {np.hypot(miss_x, miss_y):.1f}m")

    ax2.set_xlim(-400, 400)
    ax2.set_ylim(-400, 400)
    ax2.set_title("2. B-Plane Encounter Geometry & Covariance Ellipse", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Cross-Track Offset (meters)")
    ax2.set_ylabel("In-Track Offset (meters)")
    ax2.legend(facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper left", fontsize=8)
    ax2.grid(True, color="#262525", linestyle=":")

    # 3. PANEL 3: Conjunction CDM Pc & Risk Score Evolution to TCA
    ax3 = axes[1, 0]
    prog = generate_cdm_progression(
        conjunction_id="CONJ-S2A-FY1C",
        initial_pc=1.2e-6,
        final_pc=2.4e-4,
        num_updates=8,
        seed=42,
    )

    hours = prog["time_to_tca_hours"].values
    pcs = prog["pc"].values

    module = DebrisRiskModule()
    scores = [module.score(row).score for _, row in prog.iterrows()]

    ax3_twin = ax3.twinx()
    l1 = ax3.semilogy(hours, pcs, "o-", color="#f59e0b", linewidth=2.0, markersize=6, label="Pc (Collision Prob)")
    ax3.axhline(1e-4, color="#fe1e34", linestyle="--", linewidth=1.5, label="CRITICAL Threshold (1e-4)")
    l2 = ax3_twin.plot(hours, scores, "s-", color="#fe1e34", linewidth=2.0, markersize=5, label="Risk Score r_d (0..1)")

    ax3.invert_xaxis()  # TCA approaches to 0h
    ax3.set_title("3. CDM Collision Probability & Risk Escalation to TCA", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Time to TCA (Hours remaining)")
    ax3.set_ylabel("Collision Probability Pc", color="#f59e0b")
    ax3_twin.set_ylabel("Debris Risk Score r_d", color="#fe1e34")
    ax3_twin.tick_params(colors="#fe1e34")
    ax3_twin.set_ylim(-0.05, 1.05)

    lines = l1 + l2
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper right")
    ax3.grid(True, color="#262525", linestyle=":")

    # 4. PANEL 4: XGBoost CDM Model Feature Importance
    ax4 = axes[1, 1]
    module.fit()
    fnames = module.classifier.feature_names
    importances = module.classifier.model.feature_importances_ * 100

    sorted_idx = np.argsort(importances)
    sorted_fnames = [fnames[i] for i in sorted_idx]
    sorted_imp = importances[sorted_idx]

    bars = ax4.barh(sorted_fnames, sorted_imp, color="#38bdf8", height=0.55)
    ax4.set_title(f"4. XGBoost Feature Importance (ROC-AUC: {debris_data['xgboost_cdm_model']['metrics']['roc_auc']:.2f})", fontsize=11, fontweight="bold")
    ax4.set_xlabel("Relative Importance (%)")
    for bar in bars:
        w = bar.get_width()
        ax4.text(w + 0.8, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%", va="center", color="#fcfcfc", fontsize=9)
    ax4.set_xlim(0, max(sorted_imp) + 12)
    ax4.grid(True, color="#262525", linestyle=":", axis="x")

    plt.tight_layout()
    plt.savefig(plot_file, dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Successfully generated Phase 3 diagnostic plot: {plot_file}", flush=True)


if __name__ == "__main__":
    main()
