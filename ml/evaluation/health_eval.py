"""Evaluation harness for Spacecraft Health AI: Event-wise metrics & False Alarm Rate."""
import json
import os
from typing import Any

import numpy as np
import pandas as pd

from data.synthetic.telemetry_gen import generate_telemetry_series
from ml.health.module import HealthRiskModule


def compute_event_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    total_time_hours: float,
) -> dict[str, float]:
    """Compute point-wise and event-wise anomaly detection metrics + false alarms/day.

    Args:
        y_true: Binary ground-truth array (1 = anomalous, 0 = nominal)
        y_pred: Binary predicted alarm array (1 = alarm, 0 = nominal)
        total_time_hours: Total duration evaluated in hours
    """
    # 1. Point-wise metrics
    tp_point = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp_point = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn_point = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn_point = int(np.sum((y_true == 0) & (y_pred == 0)))

    point_precision = tp_point / (tp_point + fp_point + 1e-8)
    point_recall = tp_point / (tp_point + fn_point + 1e-8)
    point_f1 = (2 * point_precision * point_recall) / (point_precision + point_recall + 1e-8)

    # 2. Event-wise metrics
    # Extract contiguous ground-truth anomaly events
    true_events: list[tuple[int, int]] = []
    in_event = False
    start_idx = 0
    for i, val in enumerate(y_true):
        if val == 1 and not in_event:
            in_event = True
            start_idx = i
        elif val == 0 and in_event:
            in_event = False
            true_events.append((start_idx, i))
    if in_event:
        true_events.append((start_idx, len(y_true)))

    # Extract contiguous predicted alarm events
    pred_events: list[tuple[int, int]] = []
    in_pred = False
    p_start = 0
    for i, val in enumerate(y_pred):
        if val == 1 and not in_pred:
            in_pred = True
            p_start = i
        elif val == 0 and in_pred:
            in_pred = False
            pred_events.append((p_start, i))
    if in_pred:
        pred_events.append((p_start, len(y_pred)))

    # Check which true events were detected by at least one alarm point
    detected_true_events = 0
    for start, end in true_events:
        if np.any(y_pred[start:end] == 1):
            detected_true_events += 1

    # Check which predicted events are false alarms (zero overlap with any true event)
    false_alarm_events = 0
    for p_s, p_e in pred_events:
        if not np.any(y_true[p_s:p_e] == 1):
            false_alarm_events += 1

    event_recall = detected_true_events / (len(true_events) + 1e-8) if true_events else 1.0
    event_precision = detected_true_events / (detected_true_events + false_alarm_events + 1e-8) if (detected_true_events + false_alarm_events) > 0 else 1.0
    event_f1 = (2 * event_precision * event_recall) / (event_precision + event_recall + 1e-8)
    event_f05 = (1.25 * event_precision * event_recall) / (0.25 * event_precision + event_recall + 1e-8)

    # False alarm rate scaled to 24 hours (1 day)
    nominal_time_days = (total_time_hours / 24.0) * (tn_point + fp_point) / (len(y_true) + 1e-8)
    false_alarms_per_day = false_alarm_events / (nominal_time_days + 1e-8)

    return {
        "event_precision": round(float(event_precision), 4),
        "event_recall": round(float(event_recall), 4),
        "event_f1": round(float(event_f1), 4),
        "event_f05": round(float(event_f05), 4),
        "false_alarms_per_day": round(float(false_alarms_per_day), 3),
        "point_precision": round(float(point_precision), 4),
        "point_recall": round(float(point_recall), 4),
        "point_f1": round(float(point_f1), 4),
        "total_true_events": len(true_events),
        "detected_true_events": detected_true_events,
        "false_alarm_events": false_alarm_events,
    }


def run_evaluation() -> dict[str, Any]:
    """Run full Phase 2 comparative evaluation of LSTM Autoencoder vs. IsoForest."""
    print("================================================================================")
    print("ASTRA-GUARD: Running Phase 2 Spacecraft Health AI Evaluation Harness")
    print("================================================================================")

    # 1. Generate strictly nominal training data (180 minutes = 1080 time steps per channel)
    print("1. Generating nominal training telemetry (180 min, step=10s)...")
    df_train_nom = generate_telemetry_series(
        asset_id="SENTINEL-2A",
        duration_minutes=180,
        step_seconds=10,
        fault_type=None,
        seed=1001,
    )

    # Fit module (trains both LSTM AE and IsoForest)
    module = HealthRiskModule(window_size=64, window_step=1)
    print("2. Fitting HealthRiskModule (RobustScaler, LSTM Autoencoder, IsoForest baseline)...")
    module.fit(df_train_nom)

    # 2. Build test scenarios:
    # A) Pure nominal test sequence (120 minutes)
    df_test_nom = generate_telemetry_series(
        asset_id="SENTINEL-2A", duration_minutes=120, step_seconds=10, fault_type=None, seed=2001
    )
    df_test_nom["is_anomaly"] = 0

    # B) Thermal Drift fault: 120 minutes total, drift starts at T+60m
    df_test_drift = generate_telemetry_series(
        asset_id="SENTINEL-2A",
        duration_minutes=120,
        step_seconds=10,
        fault_type="drift",
        fault_start_minute=60,
        fault_channel="wheel_temp",
        seed=3001,
    )
    # Mark points past T+65m (once drift exceeds nominal noise threshold) as anomalous
    drift_times = df_test_drift[df_test_drift["channel"] == "wheel_temp"]["ts"].reset_index(drop=True)
    t_start_drift = drift_times.iloc[65 * 6]  # 65 min in 10s steps
    df_test_drift["is_anomaly"] = (df_test_drift["ts"] >= t_start_drift).astype(int)

    # C) Electrical Spike fault: 120 minutes total, transient spikes around T+60m
    df_test_spike = generate_telemetry_series(
        asset_id="SENTINEL-2A",
        duration_minutes=120,
        step_seconds=10,
        fault_type="spike",
        fault_start_minute=60,
        fault_channel="bus_current",
        seed=4001,
    )
    spike_times = df_test_spike[df_test_spike["channel"] == "bus_current"]["ts"].reset_index(drop=True)
    t_start_spike = spike_times.iloc[60 * 6]
    t_end_spike = spike_times.iloc[80 * 6]
    df_test_spike["is_anomaly"] = (
        (df_test_spike["ts"] >= t_start_spike) & (df_test_spike["ts"] <= t_end_spike)
    ).astype(int)

    # D) Stuck sensor freeze: 120 minutes total, stuck starts at T+60m
    df_test_stuck = generate_telemetry_series(
        asset_id="SENTINEL-2A",
        duration_minutes=120,
        step_seconds=10,
        fault_type="stuck",
        fault_start_minute=60,
        fault_channel="gyro_rate_x",
        seed=5001,
    )
    stuck_times = df_test_stuck[df_test_stuck["channel"] == "gyro_rate_x"]["ts"].reset_index(drop=True)
    t_start_stuck = stuck_times.iloc[65 * 6]
    df_test_stuck["is_anomaly"] = (df_test_stuck["ts"] >= t_start_stuck).astype(int)

    test_datasets = [
        ("Nominal Baseline", df_test_nom, 2.0),
        ("Reaction Wheel Drift", df_test_drift, 2.0),
        ("EPS Bus Current Spikes", df_test_spike, 2.0),
        ("ADCS Gyro Sensor Stuck", df_test_stuck, 2.0),
    ]

    total_test_hours = sum(hours for _, _, hours in test_datasets)

    results_by_engine: dict[str, Any] = {}

    for engine in ["lstm", "isoforest"]:
        print(f"\nEvaluating Engine: {engine.upper()}...", flush=True)
        module.active_engine = engine  # type: ignore[assignment]
        module.persistence_filter.reset()

        all_y_true: list[int] = []
        all_y_pred: list[int] = []

        for name, test_df, _ in test_datasets:
            print(f"  Testing scenario: {name}...", flush=True)
            sub_labels = test_df.groupby("ts")["is_anomaly"].max().values
            pivoted = test_df.pivot_table(index="ts", columns="channel", values="value", aggfunc="mean")[module.channel_names]
            scaled = module.scaler.transform(pivoted.values, module.channel_names)
            win_len = module.window_size

            # Evaluate with step=2 (every 20s) for prompt evaluation
            for t_idx in range(win_len, len(scaled), 2):
                win = scaled[t_idx - win_len : t_idx]
                res = module.score(win, asset_id="SENTINEL-2A")
                pred_alarm = 1 if res.score >= 0.50 else 0
                true_label = int(sub_labels[t_idx])
                all_y_true.append(true_label)
                all_y_pred.append(pred_alarm)

        y_true_arr = np.array(all_y_true)
        y_pred_arr = np.array(all_y_pred)

        metrics = compute_event_metrics(
            y_true=y_true_arr,
            y_pred=y_pred_arr,
            total_time_hours=total_test_hours,
        )
        results_by_engine[engine] = metrics
        print(
            f"  -> {engine.upper()} Event F1: {metrics['event_f1']:.4f} | "
            f"Recall: {metrics['event_recall']:.4f} | "
            f"Precision: {metrics['event_precision']:.4f} | "
            f"False Alarms/Day: {metrics['false_alarms_per_day']:.3f}",
            flush=True,
        )

    output_payload = {
        "benchmark_dataset": "ASTRA-GUARD Synthetic Physics Benchmark (ESA-ADB structure)",
        "window_size": module.window_size,
        "channels": module.channel_names,
        "evaluation_duration_hours": total_test_hours,
        "primary_model": {
            "name": "PyTorch LSTM Autoencoder",
            "type": "deep_reconstruction",
            "metrics": results_by_engine["lstm"],
        },
        "baseline_model": {
            "name": "Isolation Forest Baseline",
            "type": "tabular_spectral_stats",
            "metrics": results_by_engine["isoforest"],
        },
        "comparison_delta": {
            "f1_improvement": round(results_by_engine["lstm"]["event_f1"] - results_by_engine["isoforest"]["event_f1"], 4),
            "false_alarms_reduction_per_day": round(
                results_by_engine["isoforest"]["false_alarms_per_day"] - results_by_engine["lstm"]["false_alarms_per_day"], 3
            ),
        },
        "timestamp": pd.Timestamp.now().isoformat(),
    }

    # Save to evaluation/results/health.json and ml/evaluation/results/health.json
    for path in [
        "evaluation/results/health.json",
        "ml/evaluation/results/health.json",
    ]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)
        print(f"Saved evaluation results to: {path}", flush=True)

    return output_payload


if __name__ == "__main__":
    run_evaluation()
