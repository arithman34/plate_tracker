import csv
import json
import tempfile
from pathlib import Path

import boto3
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

_sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
engine = create_engine(_sync_url)
SessionLocal = sessionmaker(bind=engine)

OUTPUT_DIR = Path("data/output")


def _s3():
    return boto3.client("s3", region_name=settings.aws_region)


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

        if settings.s3_bucket:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                _s3().download_fileobj(settings.s3_bucket, job.video_path, tmp)
                input_path = tmp.name
        else:
            input_path = job.video_path

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {input_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        ret, first_frame = cap.read()
        if not ret:
            raise RuntimeError("Could not read first frame")

        tracker = init_tracker(first_frame, bbox)

        if settings.s3_bucket:
            tmp_out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
            output_path = tmp_out.name
            tmp_out.close()
        else:
            job_output_dir = OUTPUT_DIR / job_id
            job_output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(job_output_dir / "output.mp4")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

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

        if settings.s3_bucket:
            tmp_csv = tempfile.NamedTemporaryFile(
                suffix=".csv", delete=False, mode="w", newline=""
            )
            csv_path = tmp_csv.name
        else:
            csv_path = output_path.replace("output.mp4", "centroids.csv")

        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["frame", "cx", "cy"])
            for i, (cx, cy) in enumerate(centroids):
                w.writerow([i, cx, cy])

        if settings.s3_bucket:
            result_video_key = f"results/{job_id}/output.mp4"
            result_csv_key = f"results/{job_id}/centroids.csv"
            s3 = _s3()
            s3.upload_file(output_path, settings.s3_bucket, result_video_key)
            s3.upload_file(csv_path, settings.s3_bucket, result_csv_key)
            result_path = result_video_key
        else:
            result_path = output_path

        job.status = JobStatus.COMPLETED
        job.result_path = result_path
        db.commit()

    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error_message = str(exc)
        db.commit()
        raise self.retry(exc=exc, max_retries=0)
    finally:
        db.close()
