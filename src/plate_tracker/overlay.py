import cv2
import numpy as np


def draw_grid(frame: np.ndarray, divisions: int = 20) -> np.ndarray:
    """Draw a grid on the frame for visual reference."""
    frame = frame.copy()
    h, w = frame.shape[:2]
    for i in range(1, divisions):
        x = int(w * i / divisions)
        y = int(h * i / divisions)
        cv2.line(frame, (x, 0), (x, h), (200, 200, 200), 1)
        cv2.line(frame, (0, y), (w, y), (200, 200, 200), 1)
    return frame


def draw_trail(frame: np.ndarray, centroids: list[tuple[float, float]]) -> np.ndarray:
    """Draw the trail of the tracked object on the frame."""
    if len(centroids) < 2:
        return frame

    points = [(int(cx), int(cy)) for cx, cy in centroids]
    for i in range(1, len(points)):
        cv2.line(frame, points[i - 1], points[i], (0, 255, 0), 2)

    cx, cy = points[-1]
    cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

    return frame


def draw_metrics(frame: np.ndarray, metrics: dict) -> np.ndarray:
    """Draw computed metrics on the frame."""
    if not metrics:
        return frame

    labels = {
        "velocity_m_s": "Vel",
        "acceleration_m_s2": "Acc",
        "peak_velocity_m_s": "Peak Vel",
        "mean_velocity_m_s": "Mean Vel",
        "force_n": "Force",
        "power_w": "Power",
    }
    units = {
        "velocity_m_s": "m/s",
        "acceleration_m_s2": "m/s^2",
        "peak_velocity_m_s": "m/s",
        "mean_velocity_m_s": "m/s",
        "force_n": "N",
        "power_w": "W",
    }

    x, y_start = 10, 30
    for key, value in metrics.items():
        label = labels.get(key, key)
        unit = units.get(key, "")
        text = f"{label}: {value} {unit}"
        cv2.putText(
            frame, text, (x, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
        )
        y_start += 28

    return frame
