import numpy as np
import pytest

from plate_tracker.kinematics import (
    _SG_WINDOW,
    PLATE_DIAMETER_M,
    apply_savgol_filter,
    compute_metrics,
    compute_scale,
    compute_timeseries,
)


def test_compute_scale_square_bbox():
    bbox = (0, 0, 100, 100)
    scale = compute_scale(bbox)
    assert scale == pytest.approx(PLATE_DIAMETER_M / 100)


def test_compute_scale_rectangular_bbox():
    bbox = (0, 0, 80, 100)
    scale = compute_scale(bbox)
    expected = PLATE_DIAMETER_M / 90
    assert scale == pytest.approx(expected)


def test_apply_savgol_filter_smooths_constant():
    data = np.ones(20) * 5.0
    smoothed = apply_savgol_filter(data)
    np.testing.assert_allclose(smoothed, 5.0, atol=1e-10)


def test_apply_savgol_filter_derivative_of_constant_is_zero():
    data = np.ones(20) * 5.0
    deriv = apply_savgol_filter(data, dt=1.0, derivative=1)
    np.testing.assert_allclose(deriv, 0.0, atol=1e-10)


def test_apply_savgol_filter_recovers_velocity_from_linear_position():
    fps = 30.0
    dt = 1.0 / fps
    t = np.arange(30) * dt
    expected_velocity = 2.0
    position = expected_velocity * t
    computed = apply_savgol_filter(position, dt=dt, derivative=1)
    np.testing.assert_allclose(computed[4:-4], expected_velocity, atol=1e-6)


def test_compute_metrics_returns_empty_when_too_few_centroids():
    centroids = [(0.0, float(i)) for i in range(_SG_WINDOW - 1)]
    result = compute_metrics(centroids, fps=30.0, scale=0.005)
    assert result == {}


def test_compute_metrics_returns_expected_keys_without_mass():
    centroids = [(0.0, float(i)) for i in range(20)]
    result = compute_metrics(centroids, fps=30.0, scale=0.005)
    assert set(result.keys()) == {
        "velocity_m_s",
        "acceleration_m_s2",
        "peak_velocity_m_s",
        "mean_velocity_m_s",
    }


def test_compute_metrics_includes_force_and_power_with_mass():
    centroids = [(0.0, float(i)) for i in range(20)]
    result = compute_metrics(centroids, fps=30.0, scale=0.005, mass_kg=100.0)
    assert "force_n" in result
    assert "power_w" in result


def test_compute_metrics_peak_velocity_gte_mean():
    centroids = [(0.0, float(i)) for i in range(30)]
    result = compute_metrics(centroids, fps=30.0, scale=0.005)
    assert result["peak_velocity_m_s"] >= result["mean_velocity_m_s"]


def test_compute_timeseries_returns_empty_when_too_few_centroids():
    centroids = [(0.0, float(i)) for i in range(_SG_WINDOW - 1)]
    result = compute_timeseries(centroids, fps=30.0, scale=0.005)
    assert result == {}


def test_compute_timeseries_returns_arrays_of_correct_length():
    n = 30
    centroids = [(0.0, float(i)) for i in range(n)]
    result = compute_timeseries(centroids, fps=30.0, scale=0.005)
    assert set(result.keys()) == {"t", "position", "velocity", "acceleration"}
    for key in result:
        assert len(result[key]) == n
