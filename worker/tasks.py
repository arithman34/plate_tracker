import csv
import json
from pathlib import Path

import cv2
from celery import Task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.core.settings import settings
from api.models.job import Job, JobStatus
from plate_tracker import (
    compute_metrics,
    compute_scale,
    draw_metrics,
    draw_trail,
    init_tracker,
    update_tracker,
)
from worker.celery_app import celery_app

# Sync engine — Celery tasks are synchronous
_sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
engine = create_engine(_sync_url)
SessionLocal = sessionmaker(bind=engine)

OUTPUT_DIR = Path("data/output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@celery_app.task(bind=True, name="worker.tasks.process_job")
def process_job(self: Task, job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = JobStatus.PROCESSING
        db.commit()

        bbox = tuple(json.loads(job.bbox))
        scale = compute_scale(bbox)

        cap = cv2.VideoCapture(job.video_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {job.video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        ret, first_frame = cap.read()
        if not ret:
            raise RuntimeError("Could not read first frame")

        tracker = init_tracker(first_frame, bbox)

        job_output_dir = OUTPUT_DIR / job_id
        job_output_dir.mkdir(parents=True, exist_ok=True)

        output_video_path = job_output_dir / "output.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

        centroids: list[tuple[float, float]] = []
        writer.write(first_frame)

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            centroid = update_tracker(tracker, frame)
            if centroid is not None:
                centroids.append(centroid)

            metrics = compute_metrics(centroids, fps, scale, job.mass_kg)
            frame = draw_trail(frame, centroids)
            frame = draw_metrics(frame, metrics)
            writer.write(frame)

        cap.release()
        writer.release()

        centroids_path = job_output_dir / "centroids.csv"
        with open(centroids_path, "w", newline="") as f:
            csv_writer = csv.writer(f)
            csv_writer.writerow(["frame", "cx", "cy"])
            for i, (cx, cy) in enumerate(centroids):
                csv_writer.writerow([i, cx, cy])

        job.status = JobStatus.COMPLETED
        job.result_path = str(output_video_path)
        db.commit()

    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        raise self.retry(exc=exc, max_retries=0)
    finally:
        db.close()
