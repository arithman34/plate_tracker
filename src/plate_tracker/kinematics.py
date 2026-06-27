import numpy as np
from scipy.signal import savgol_filter

PLATE_DIAMETER_M = 0.450  # 450mm
ACCELERATION_DUE_TO_GRAVITY = 9.81

_SG_WINDOW = 9
_SG_POLY = 3


def compute_scale(bbox: tuple) -> float:
    """Pixels to meters using the plate diameter as the reference."""
    _, _, w, h = bbox
    plate_diameter_px = (w + h) / 2
    return PLATE_DIAMETER_M / plate_diameter_px


def apply_savgol_filter(
    data: np.ndarray, dt: float = 1.0, derivative: int = 0
) -> np.ndarray:
    """Apply Savitzky-Golay filter to smooth data and compute derivatives."""
    return savgol_filter(
        data, window_length=_SG_WINDOW, polyorder=_SG_POLY, deriv=derivative, delta=dt
    )


def compute_timeseries(
    centroids: list[tuple[float, float]],
    fps: float,
    scale: float,
) -> dict:
    """Returns smoothed position, velocity, and acceleration arrays for plotting."""
    if len(centroids) < _SG_WINDOW:
        return {}

    ys = np.array([cy for _, cy in centroids]) * scale
    t = np.arange(len(ys)) / fps
    dt = 1.0 / fps

    position = apply_savgol_filter(ys)
    velocity = apply_savgol_filter(ys, dt, derivative=1)
    acceleration = apply_savgol_filter(ys, dt, derivative=2)

    return {
        "t": t,
        "position": position,
        "velocity": velocity,
        "acceleration": acceleration,
    }


def compute_metrics(
    centroids: list[tuple[float, float]],
    fps: float,
    scale: float,
    mass_kg: float | None = None,
) -> dict:
    """Compute metrics from the centroids of the tracked object."""
    if len(centroids) < _SG_WINDOW:
        return {}

    ys = np.array([cy for _, cy in centroids]) * scale  # pixels to metres, y axis

    dt = 1.0 / fps
    position = apply_savgol_filter(ys)
    velocity = apply_savgol_filter(position, dt, derivative=1)
    acceleration = apply_savgol_filter(position, dt, derivative=2)

    current_v = velocity[-1]
    current_a = acceleration[-1]
    peak_v = float(np.max(np.abs(velocity)))
    mean_v = float(np.mean(np.abs(velocity)))

    metrics = {
        "velocity_m_s": round(float(current_v), 3),
        "acceleration_m_s2": round(float(current_a), 3),
        "peak_velocity_m_s": round(peak_v, 3),
        "mean_velocity_m_s": round(mean_v, 3),
    }

    if mass_kg is not None:
        force = mass_kg * (current_a + ACCELERATION_DUE_TO_GRAVITY)
        power = force * abs(current_v)
        metrics["force_n"] = round(float(force), 2)
        metrics["power_w"] = round(float(power), 2)

    return metrics
