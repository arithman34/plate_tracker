import csv
import json
from pathlib import Path

import cv2

from plate_tracker import (
    compute_metrics,
    compute_scale,
    draw_grid,
    draw_metrics,
    draw_trail,
    init_tracker,
    update_tracker,
)

MASS_KG = 170.0
VIDEO_PATH = "data/input/squat.mp4"


def bbox_path(video_path: str) -> Path:
    return Path("data") / f"bbox_{Path(video_path).stem}.json"


def save_bbox(bbox: tuple, video_path: str) -> None:
    bbox_path(video_path).write_text(json.dumps(list(bbox)))


def load_bbox(video_path: str) -> tuple | None:
    path = bbox_path(video_path)
    if path.exists():
        return tuple(json.loads(path.read_text()))
    return None


def open_video(video_path: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Error opening video file: {video_path}.")
    return cap


def centroids_path(video_path: str) -> Path:
    return Path("data/output") / f"centroids_{Path(video_path).stem}.csv"


def save_centroids(centroids: list[tuple[float, float]], video_path: str) -> None:
    path = centroids_path(video_path)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "cx", "cy"])
        for i, (cx, cy) in enumerate(centroids):
            writer.writerow([i, cx, cy])
    print(f"Centroids saved to {path}")


def load_centroids(video_path: str) -> list[tuple[float, float]] | None:
    path = centroids_path(video_path)
    if not path.exists():
        return None
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return [(float(row["cx"]), float(row["cy"])) for row in reader]


def main() -> None:
    cap = open_video(VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("Could not read first frame.")

    bbox = load_bbox(VIDEO_PATH)
    if bbox is None:
        bbox = cv2.selectROI(
            "Select plate region",
            draw_grid(first_frame),
            fromCenter=False,
            showCrosshair=True,
        )
        cv2.destroyWindow("Select plate region")
        if bbox[2] == 0 or bbox[3] == 0:
            raise RuntimeError("No region selected. Please draw a bounding box.")

        save_bbox(bbox, VIDEO_PATH)
        print(f"Bbox saved to {bbox_path(VIDEO_PATH)}")
    else:
        print(f"Using saved bbox: {bbox}  (delete {bbox_path(VIDEO_PATH)} to redraw)")

    scale = compute_scale(bbox)

    centroids = load_centroids(VIDEO_PATH)
    if centroids is not None:
        print(f"Using saved centroids: {centroids_path(VIDEO_PATH)}  (delete to retrack)")
        cap.release()
        return

    tracker = init_tracker(first_frame, bbox)
    centroids = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        centroid = update_tracker(tracker, frame)
        if centroid is not None:
            centroids.append(centroid)

        metrics = compute_metrics(centroids, fps, scale, MASS_KG)

        frame = draw_trail(frame, centroids)
        frame = draw_metrics(frame, metrics)
        cv2.imshow("Tracking", frame)

        if cv2.waitKey(25) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    save_centroids(centroids, VIDEO_PATH)


if __name__ == "__main__":
    main()
