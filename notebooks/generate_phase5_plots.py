"""Generate diagnostic visualization plots for Phase 5 Mission Risk Engine + XAI."""
import json
import os
import sys

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, os.path.abspath("."))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    output_dir = "notebooks"
    os.makedirs(output_dir, exist_ok=True)
    plot_file = os.path.join(output_dir, "phase5_risk_diagnostics.png")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
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

    # Load evaluated benchmark results
    with open("evaluation/results/risk.json", encoding="utf-8") as f:
        risk_data = json.load(f)

    # 1. PANEL 1: Noisy-OR Safety Hazard Fusion Surface
    ax1 = axes[0, 0]
    rh_grid, rd_grid = np.meshgrid(np.linspace(0, 1, 100), np.linspace(0, 1, 100))
    rsafety_grid = 1.0 - (1.0 - rh_grid) * (1.0 - rd_grid)

    cs1 = ax1.contourf(rh_grid, rd_grid, rsafety_grid, levels=20, cmap="viridis")
    cbar1 = fig.colorbar(cs1, ax=ax1)
    cbar1.ax.tick_params(colors="#d4d2d2")
    cbar1.set_label("R_safety = 1 - (1 - r_h)(1 - r_d)", color="#fcfcfc", fontsize=9)

    # Mark health deferral boundary r_h = 0.50
    ax1.axvline(0.50, color="#f59e0b", linestyle="--", linewidth=1.5, label="EO Deferral Cutoff (r_h ≥ 0.50)")
    ax1.scatter([0.04, 0.68, 0.06, 0.16], [0.02, 0.05, 0.94, 0.08], color="#00e5ff", s=70, edgecolors="#ffffff", zorder=5, label="Scenarios 1-4")
    ax1.set_title("1. Noisy-OR Safety Hazard Fusion Surface", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Spacecraft Health Risk (r_h)", fontsize=10)
    ax1.set_ylabel("Debris Collision Risk (r_d)", fontsize=10)
    ax1.legend(facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper left", fontsize=8)

    # 2. PANEL 2: Integrated Mission Risk Score Heatmap & Overrides
    ax2 = axes[0, 1]
    rs_grid, re_grid = np.meshgrid(np.linspace(0, 1, 100), np.linspace(0, 1, 100))
    rmiss_grid = 100.0 * (0.85 * rs_grid + 0.15 * re_grid)

    # Custom colormap reflecting NOMINAL (green), WATCH (cyan), WARNING (amber), CRITICAL (red)
    from matplotlib.colors import LinearSegmentedColormap
    risk_colors = ["#10b981", "#00e5ff", "#f59e0b", "#fe1e34"]
    risk_cmap = LinearSegmentedColormap.from_list("risk_bands", risk_colors, N=100)

    cs2 = ax2.contourf(rs_grid, re_grid, rmiss_grid, levels=[0, 25, 50, 75, 100], cmap=risk_cmap, alpha=0.85)
    cbar2 = fig.colorbar(cs2, ax=ax2)
    cbar2.ax.tick_params(colors="#d4d2d2")
    cbar2.set_label("R_mission = 100·(0.85·R_safety + 0.15·r_e)", color="#fcfcfc", fontsize=9)

    # Hard override indicator
    ax2.text(0.10, 0.85, "Override: Pc ≥ 10⁻⁴\n→ CRITICAL (Score ≥ 75)", bbox={"boxstyle": "round,pad=0.4", "fc": "#330006", "ec": "#fe1e34", "lw": 1.5}, color="#fcfcfc", fontsize=8)
    ax2.text(0.10, 0.65, "Override: r_h ≥ 0.90\n→ WARNING (Score ≥ 50)", bbox={"boxstyle": "round,pad=0.4", "fc": "#332200", "ec": "#f59e0b", "lw": 1.5}, color="#fcfcfc", fontsize=8)
    ax2.set_title("2. Mission Risk Score & Hard Safety Overrides", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Fused Safety Hazard (R_safety)", fontsize=10)
    ax2.set_ylabel("EO Observation Priority (r_e)", fontsize=10)

    # 3. PANEL 3: Scenario Feature Attribution Breakdown
    ax3 = axes[1, 0]
    scenarios = risk_data["canonical_scenarios"]
    sc_names = [s["scenario_id"].replace("SCENARIO-", "") for s in scenarios]
    top_driver_shares = [s["top_driver_share"] for s in scenarios]
    top_drivers = [s["top_driver"] for s in scenarios]

    y_pos = np.arange(len(sc_names))
    bars = ax3.barh(y_pos, top_driver_shares, height=0.55, color="#00e5ff", edgecolor="#393939")
    ax3.set_yticks(y_pos)
    ax3.set_yticklabels(sc_names, fontsize=8)
    ax3.set_xlabel("Primary Risk Driver Share (%)", fontsize=10)
    ax3.set_xlim(0, 100)
    ax3.set_title("3. Primary Factor-Level Risk Driver Share", fontsize=11, fontweight="bold")
    ax3.grid(axis="x", color="#393939", linestyle="--", alpha=0.5)

    for i, (bar, d_name) in enumerate(zip(bars, top_drivers)):
        width = bar.get_width()
        ax3.text(width + 2, bar.get_y() + bar.get_height() / 2, f"{d_name} ({width:.1f}%)", va="center", color="#fcfcfc", fontsize=8)

    # 4. PANEL 4: Scenario Risk Level & Advisory Actions
    ax4 = axes[1, 1]
    scores = [s["score"] for s in scenarios]
    levels = [s["level"] for s in scenarios]
    actions = [s["primary_action"] for s in scenarios]

    level_colors = {
        "NOMINAL": "#10b981",
        "WATCH": "#00e5ff",
        "WARNING": "#f59e0b",
        "CRITICAL": "#fe1e34",
    }
    bar_colors = [level_colors.get(lvl, "#9e9c9c") for lvl in levels]

    bars4 = ax4.bar(sc_names, scores, width=0.55, color=bar_colors, edgecolor="#393939")
    ax4.set_ylim(0, 100)
    ax4.set_ylabel("Mission Risk Score (0 - 100)", fontsize=10)
    ax4.set_title("4. Operational Scenario Level & Advisory Recommendations", fontsize=11, fontweight="bold")
    ax4.tick_params(axis="x", labelsize=8)
    ax4.grid(axis="y", color="#393939", linestyle="--", alpha=0.5)

    # Threshold horizontal reference lines
    ax4.axhline(25, color="#00e5ff", linestyle=":", alpha=0.6, label="Watch (25)")
    ax4.axhline(50, color="#f59e0b", linestyle=":", alpha=0.6, label="Warning (50)")
    ax4.axhline(75, color="#fe1e34", linestyle=":", alpha=0.6, label="Critical (75)")
    ax4.legend(facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper left", fontsize=8)

    for bar, score_val, act in zip(bars4, scores, actions):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width() / 2, height + 2.5, f"{score_val:.1f}\n[{act}]", ha="center", va="bottom", color="#fcfcfc", fontsize=7.5, fontweight="bold")

    plt.tight_layout()
    plt.savefig(plot_file, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Successfully generated Phase 5 diagnostic plot: {plot_file}", flush=True)


if __name__ == "__main__":
    main()
