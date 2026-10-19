"""Generate diagnostic visualization plots for Phase 2 Spacecraft Health AI."""
import os
import sys

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath("."))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from data.synthetic.telemetry_gen import generate_telemetry_series
from ml.health.module import HealthRiskModule


def main() -> None:
    output_dir = "notebooks"
    os.makedirs(output_dir, exist_ok=True)
    plot_file = os.path.join(output_dir, "phase2_health_diagnostics.png")

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

    # 1. Train Health Module on nominal series
    df_train = generate_telemetry_series(
        asset_id="SENTINEL-2A", duration_minutes=120, step_seconds=10, fault_type=None, seed=42
    )
    module = HealthRiskModule(window_size=64, window_step=1)
    module.fit(df_train)

    # 2. Test on thermal drift series
    df_drift = generate_telemetry_series(
        asset_id="SENTINEL-2A",
        duration_minutes=90,
        step_seconds=10,
        fault_type="drift",
        fault_start_minute=45,
        fault_channel="wheel_temp",
        seed=99,
    )

    pivoted = df_drift.pivot_table(index="ts", columns="channel", values="value", aggfunc="mean")[module.channel_names]
    scaled = module.scaler.transform(pivoted.values, module.channel_names)
    win_len = module.window_size

    scores: list[float] = []
    inst_scores: list[float] = []
    recons_wheel: list[float] = []
    actual_wheel: list[float] = []
    timestamps_min = np.linspace(0, 90, len(scaled))

    for i in range(win_len, len(scaled), 2):
        win = scaled[i - win_len : i]
        res = module.score(win, asset_id="SENTINEL-2A")
        scores.append(res.score)
        inst_scores.append(res.evidence.get("instantaneous_score", res.score))
        actual_wheel.append(win[-1, module.channel_names.index("wheel_temp")])

        # Get reconstructed wheel_temp for last step
        recon_arr = module.lstm_model.net(
            module.lstm_model.net.__class__.__mro__[0] if False else
            __import__("torch").from_numpy(win[None, :, :]).float().to(module.lstm_model.device)
        ).cpu().detach().numpy()[0, -1, module.channel_names.index("wheel_temp")]
        recons_wheel.append(float(recon_arr))

    eval_time = timestamps_min[win_len::2]

    # Revert scaled actual and recon to °C
    med = module.scaler.medians["wheel_temp"]
    iqr = module.scaler.iqrs["wheel_temp"]
    actual_c = np.array(actual_wheel) * (iqr + 1e-6) + med
    recon_c = np.array(recons_wheel) * (iqr + 1e-6) + med

    # PANEL 1: Telemetry vs Autoencoder Reconstruction
    ax1 = axes[0, 0]
    ax1.plot(eval_time, actual_c, color="#fe1e34", linewidth=1.8, label="Actual Sensor (°C)")
    ax1.plot(eval_time, recon_c, color="#38bdf8", linestyle="--", linewidth=1.5, label="LSTM AE Reconstruction")
    ax1.axvline(45, color="#f59e0b", linestyle=":", linewidth=1.2, label="Drift Injected (T+45m)")
    ax1.set_title("1. Autoencoder Telemetry Reconstruction Residual", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Mission Elapsed Time (min)")
    ax1.set_ylabel("Wheel Temperature (°C)")
    ax1.legend(facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper left")
    ax1.grid(True, color="#262525", linestyle=":")

    # PANEL 2: Calibrated Health Risk Score & Persistence Filter
    ax2 = axes[0, 1]
    ax2.plot(eval_time, inst_scores, color="#71717a", linestyle=":", alpha=0.8, label="Instantaneous Score")
    ax2.plot(eval_time, scores, color="#fe1e34", linewidth=2.0, label="Filtered Health Risk r_h (k=3 of n=5)")
    ax2.axhline(0.25, color="#10b981", linestyle="--", alpha=0.5, label="WATCH (0.25)")
    ax2.axhline(0.50, color="#f59e0b", linestyle="--", alpha=0.6, label="WARNING (0.50)")
    ax2.axhline(0.75, color="#fe1e34", linestyle="--", alpha=0.7, label="CRITICAL (0.75)")
    ax2.set_title("2. Calibrated Health Risk Score & Alert Escalation", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Mission Elapsed Time (min)")
    ax2.set_ylabel("Risk Score r_h (0..1)")
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend(facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper left")
    ax2.grid(True, color="#262525", linestyle=":")

    # PANEL 3: Channel-Level Explainability Attribution
    ax3 = axes[1, 0]
    anomaly_win = scaled[-win_len:]
    attributions = module.explain(anomaly_win)
    drivers = [attr.driver for attr in reversed(attributions)]
    contributions = [attr.contribution * 100 for attr in reversed(attributions)]
    colors = ["#fe1e34" if d == "wheel_temp" else "#38bdf8" for d in drivers]

    bars = ax3.barh(drivers, contributions, color=colors, height=0.55)
    ax3.set_title("3. Root Cause Attribution (Channel Residual Breakdown)", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Attribution Contribution (%)")
    for bar in bars:
        w = bar.get_width()
        ax3.text(w + 1.0, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%", va="center", color="#fcfcfc", fontsize=9)
    ax3.set_xlim(0, max(contributions) + 15)
    ax3.grid(True, color="#262525", linestyle=":", axis="x")

    # PANEL 4: Comparative Evaluation: LSTM AE vs IsoForest
    ax4 = axes[1, 1]
    import json
    with open("evaluation/results/health.json", "r", encoding="utf-8") as f:
        metrics_data = json.load(f)

    models = ["LSTM Autoencoder", "IsoForest Baseline"]
    f1_scores = [
        metrics_data["primary_model"]["metrics"]["event_f1"],
        metrics_data["baseline_model"]["metrics"]["event_f1"],
    ]
    false_alarms = [
        metrics_data["primary_model"]["metrics"]["false_alarms_per_day"],
        metrics_data["baseline_model"]["metrics"]["false_alarms_per_day"],
    ]

    x = np.arange(len(models))
    width = 0.35

    ax4_twin = ax4.twinx()
    ax4.bar(x - width/2, f1_scores, width, label="Event F1 Score", color="#10b981")
    ax4_twin.bar(x + width/2, false_alarms, width, label="False Alarms / Day", color="#f59e0b")

    ax4.set_xticks(x)
    ax4.set_xticklabels(models, color="#fcfcfc", fontweight="bold")
    ax4.set_ylabel("Event-wise F1", color="#10b981")
    ax4.set_ylim(0, 1.0)
    ax4_twin.set_ylabel("False Alarms / Day", color="#f59e0b")
    ax4_twin.tick_params(colors="#f59e0b")
    ax4_twin.set_ylim(0, max(false_alarms) * 1.25)
    ax4.set_title("4. Benchmark: Event F1 vs False Alarms/Day", fontsize=11, fontweight="bold")

    # Combine legends
    lines1, labels1 = ax4.get_legend_handles_labels()
    lines2, labels2 = ax4_twin.get_legend_handles_labels()
    ax4.legend(lines1 + lines2, labels1 + labels2, facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper center")

    plt.tight_layout()
    plt.savefig(plot_file, dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Successfully generated Phase 2 diagnostic plot: {plot_file}")


if __name__ == "__main__":
    main()
