"""Tests for Phase 2 Spacecraft Health AI modules and pipelines."""
import numpy as np
from data.synthetic.telemetry_gen import generate_telemetry_series
from ml.common.protocols import RiskModule
from ml.common.schemas import Attribution, ModuleResult
from ml.evaluation.health_eval import compute_event_metrics
from ml.health.calibrator import HealthScoreCalibrator, PersistenceFilter
from ml.health.isoforest import IsolationForestBaseline
from ml.health.lstm_ae import LSTMAutoencoder
from ml.health.module import HealthRiskModule
from ml.health.preprocessor import (
    CORE_CHANNELS,
    TelemetryRobustScaler,
    create_sliding_windows,
    extract_window_features,
)


def test_robust_scaler_fit_transform() -> None:
    """Test robust scaler preserves channel dimensions and inverts correctly."""
    np.random.seed(42)
    nominal_data = np.random.normal(loc=20.0, scale=2.0, size=(100, 7)).astype(np.float32)
    scaler = TelemetryRobustScaler()
    scaler.fit(nominal_data, CORE_CHANNELS)

    assert scaler.is_fitted
    assert len(scaler.medians) == 7

    scaled = scaler.transform(nominal_data, CORE_CHANNELS)
    assert scaled.shape == (100, 7)
    assert np.allclose(np.median(scaled, axis=0), 0.0, atol=0.15)

    reconstructed = scaler.inverse_transform(scaled, CORE_CHANNELS)
    assert np.allclose(reconstructed, nominal_data, atol=1e-4)


def test_sliding_window_creation() -> None:
    """Test sliding window generator shapes and padding."""
    data = np.arange(100 * 7).reshape(100, 7).astype(np.float32)
    windows = create_sliding_windows(data, window_size=32, step=2)
    # (100 - 32) // 2 + 1 = 35 windows
    assert windows.shape == (35, 32, 7)

    # Test short series padding
    short_data = np.ones((10, 7), dtype=np.float32)
    padded_windows = create_sliding_windows(short_data, window_size=32, step=1)
    assert padded_windows.shape == (1, 32, 7)


def test_window_feature_extraction() -> None:
    """Test statistical and spectral feature extraction."""
    windows = np.random.uniform(10.0, 30.0, size=(5, 32, 7)).astype(np.float32)
    feat_matrix, feat_names = extract_window_features(windows, CORE_CHANNELS)

    assert feat_matrix.shape == (5, 7 * 7)
    assert len(feat_names) == 49
    assert "wheel_temp_mean" in feat_names
    assert "wheel_temp_fft_high" in feat_names


def test_health_score_calibrator_monotonicity() -> None:
    """Test calibrator outputs stay bounded in [0, 1] and strictly monotonic."""
    calibrator = HealthScoreCalibrator()
    nominal_residuals = np.linspace(0.01, 0.5, 200)
    calibrator.fit(nominal_residuals)

    test_residuals = np.array([0.0, 0.05, 0.2, 0.4, 0.6, 1.2, 5.0])
    scores = calibrator.calibrate(test_residuals)

    assert len(scores) == len(test_residuals)
    assert (scores >= 0.0).all()
    assert (scores <= 1.0).all()
    # Check monotonicity
    assert (np.diff(scores) >= 0.0).all()


def test_persistence_filter_suppression() -> None:
    """Test persistence filter suppresses transient spikes until sustained."""
    filter_ = PersistenceFilter(n=5, k=3, threshold=0.50)
    asset = "SAT-TEST"

    # Single transient spike -> should be suppressed
    score_1, sustained_1, count_1 = filter_.update(asset, raw_score=0.90)
    assert not sustained_1
    assert count_1 == 1
    assert score_1 < 0.50

    # Second high reading
    _, sustained_2, count_2 = filter_.update(asset, raw_score=0.88)
    assert not sustained_2
    assert count_2 == 2

    # Third high reading -> threshold k=3 reached!
    score_3, sustained_3, count_3 = filter_.update(asset, raw_score=0.92)
    assert sustained_3
    assert count_3 == 3
    assert score_3 >= 0.50


def test_isoforest_baseline_fit_and_predict() -> None:
    """Test Isolation Forest baseline fitting, scoring, and explainability."""
    np.random.seed(42)
    windows = np.random.normal(0.0, 1.0, size=(40, 32, 7)).astype(np.float32)
    model = IsolationForestBaseline(n_estimators=20)
    model.fit(windows, CORE_CHANNELS)

    assert model.is_fitted
    cal_score, raw_res, evidence = model.predict_window(windows[0])
    assert 0.0 <= cal_score <= 1.0
    assert "p95_threshold" in evidence

    attributions = model.explain_window(windows[0], top_k=3)
    assert len(attributions) <= 3
    assert sum(a.contribution for a in attributions) > 0.0


def test_lstm_autoencoder_anomaly_detection() -> None:
    """Test LSTM Autoencoder detects injected anomaly and attributes culprit channel."""
    np.random.seed(42)
    nom_windows = np.random.normal(0.0, 0.2, size=(50, 32, 7)).astype(np.float32)

    lstm = LSTMAutoencoder(hidden_dim=16, latent_dim=8, epochs=10, seed=42)
    lstm.fit(nom_windows, CORE_CHANNELS)
    assert lstm.is_fitted

    # Score nominal window
    nom_score, _, _ = lstm.predict_window(nom_windows[0])

    # Create anomalous window with huge thermal spike on wheel_temp (channel 0)
    anom_window = nom_windows[0].copy()
    anom_window[:, 0] += 5.0
    anom_score, _, evidence = lstm.predict_window(anom_window)

    assert anom_score > nom_score
    assert evidence["channel_residuals"]["wheel_temp"] > evidence["channel_residuals"]["bus_current"]

    # Explain anomalous window
    attributions = lstm.explain_window(anom_window, top_k=3)
    assert attributions[0].driver == "wheel_temp"
    assert attributions[0].contribution > 0.50


def test_health_risk_module_contract() -> None:
    """Test HealthRiskModule adheres to RiskModule protocol and returns valid ModuleResult."""
    df_nom = generate_telemetry_series(
        asset_id="SAT-S2A", duration_minutes=30, step_seconds=10, fault_type=None, seed=42
    )

    module = HealthRiskModule(window_size=32)
    assert isinstance(module, RiskModule)

    module.fit(df_nom)
    assert module.is_fitted

    # Test scoring with DataFrame input
    result = module.score(df_nom.iloc[-32 * 7 :], asset_id="SAT-S2A")
    assert isinstance(result, ModuleResult)
    assert 0.0 <= result.score <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert result.asset_id == "SAT-S2A"
    assert result.synthetic is True

    # Test explanation
    attributions = module.explain(df_nom.iloc[-32 * 7 :], result)
    assert isinstance(attributions, list)
    assert all(isinstance(a, Attribution) for a in attributions)

    # Test engine switching
    module.active_engine = "isoforest"
    iso_result = module.score(df_nom.iloc[-32 * 7 :], asset_id="SAT-S2A")
    assert iso_result.evidence["active_engine"] == "isoforest"


def test_event_metrics_computation() -> None:
    """Test event-wise metrics and false alarm rate calculations."""
    y_true = np.array([0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0])
    y_pred = np.array([0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0])

    metrics = compute_event_metrics(y_true, y_pred, total_time_hours=2.0)
    assert metrics["total_true_events"] == 2
    assert metrics["detected_true_events"] == 2
    assert metrics["event_recall"] == 1.0
    assert metrics["false_alarm_events"] == 1
    assert metrics["false_alarms_per_day"] > 0.0
