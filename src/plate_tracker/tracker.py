import cv2


def init_tracker(frame, bbox):
    """Initialize the tracker with the first frame and bounding box."""
    tracker = cv2.legacy.TrackerCSRT_create()
    tracker.init(frame, bbox)
    return tracker


def update_tracker(tracker, frame) -> tuple[float, float] | None:
    """Update the tracker with the new frame and return the centroid of the tracked object."""
    success, bbox = tracker.update(frame)
    if not success:
        return None

    x, y, w, h = bbox
    center_x = x + w / 2
    center_y = y + h / 2
    return (center_x, center_y)
