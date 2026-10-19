import os
import sys

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath("."))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from data.synthetic.debris_gen import generate_cdm_progression
from data.synthetic.disaster_gen import generate_synthetic_chip_arrays
from data.synthetic.telemetry_gen import generate_telemetry_series


def main() -> None:
    output_dir = "notebooks"
    os.makedirs(output_dir, exist_ok=True)
    plot_file = os.path.join(output_dir, "phase1_diagnostic_plots.png")

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
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

    # 1. Telemetry Plot: Thermal Drift Injection
    df_telem = generate_telemetry_series(
        asset_id="SENTINEL-2A",
        duration_minutes=60,
        step_seconds=10,
        fault_type="drift",
        fault_start_minute=30,
        fault_channel="wheel_temp",
        seed=42,
    )
    temp_df = df_telem[df_telem["channel"] == "wheel_temp"].reset_index()
    time_min = np.linspace(0, 60, len(temp_df))

    ax1 = axes[0, 0]
    ax1.plot(time_min, temp_df["value"], color="#fe1e34", linewidth=1.5, label="wheel_temp (°C)")
    ax1.axvline(30, color="#d4d2d2", linestyle="--", alpha=0.7, label="Injected Drift (T+30m)")
    ax1.set_title("Spacecraft Health: Injected Reaction Wheel Thermal Drift", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Elapsed Time (minutes)")
    ax1.set_ylabel("Temperature (°C)")
    ax1.legend(facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper left")
    ax1.grid(True, color="#262525", linestyle=":")

    # 2. Telemetry Plot: Bus Current Spikes
    df_spikes = generate_telemetry_series(
        asset_id="SENTINEL-2A",
        duration_minutes=60,
        step_seconds=10,
        fault_type="spike",
        fault_start_minute=20,
        fault_channel="bus_current",
        seed=123,
    )
    curr_df = df_spikes[df_spikes["channel"] == "bus_current"].reset_index()
    time_curr = np.linspace(0, 60, len(curr_df))

    ax2 = axes[0, 1]
    ax2.plot(time_curr, curr_df["value"], color="#38bdf8", linewidth=1.2, label="bus_current (A)")
    ax2.axvline(20, color="#d4d2d2", linestyle="--", alpha=0.7, label="Fault Injected (T+20m)")
    ax2.set_title("Spacecraft Health: Transient Electrical Spikes", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Elapsed Time (minutes)")
    ax2.set_ylabel("Current (A)")
    ax2.legend(facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper left")
    ax2.grid(True, color="#262525", linestyle=":")

    # 3. Debris Encounter: Pc Evolution Over Time-to-TCA
    df_cdm = generate_cdm_progression(
        conjunction_id="CONJ-S2A-DEB",
        initial_pc=1.0e-6,
        final_pc=2.8e-4,
        seed=99,
    )
    ax3 = axes[1, 0]
    ax3.semilogy(df_cdm["time_to_tca_hours"], df_cdm["pc"], "o-", color="#f59e0b", linewidth=1.8, markersize=5, label="Pc (Collision Prob)")
    ax3.axhline(1e-4, color="#fe1e34", linestyle="--", label="CRITICAL Threshold (1e-4)")
    ax3.invert_xaxis()  # 72h down to 4h
    ax3.set_title("Debris Risk: Conjunction CDM Pc Trend to TCA", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Time to TCA (Hours remaining)")
    ax3.set_ylabel("Probability of Collision (Pc)")
    ax3.legend(facecolor="#262525", edgecolor="#393939", labelcolor="#fcfcfc", loc="upper right")
    ax3.grid(True, color="#262525", linestyle=":")

    # 4. Disaster AI: Synthetic SAR Chip & Flood Inundation Mask
    chip_backscatter, flood_mask = generate_synthetic_chip_arrays(size=128, water_ratio=0.32, seed=77)
    composite = np.zeros((128, 128, 3), dtype=np.uint8)
    composite[:, :, 0] = chip_backscatter
    composite[:, :, 1] = np.where(flood_mask == 1, 200, chip_backscatter)
    composite[:, :, 2] = np.where(flood_mask == 1, 255, chip_backscatter)

    ax4 = axes[1, 1]
    ax4.imshow(composite)
    ax4.set_title("Disaster Intelligence: Synthetic SAR Chip & Flood Mask", fontsize=11, fontweight="bold")
    ax4.set_xticks([])
    ax4.set_yticks([])

    plt.tight_layout()
    plt.savefig(plot_file, dpi=180, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    print(f"Successfully generated Phase 1 diagnostic plots: {plot_file}")


if __name__ == "__main__":
    main()
