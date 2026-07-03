import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.core.database import get_db
from api.models import APIKey, Job, User
from api.models.job import JobStatus
from api.schemas.jobs import JobCreateRequest, JobResponse, JobResultResponse
from api.v1.deps import verify_api_key
from worker.celery_app import celery_app

router = APIRouter(prefix="/jobs", tags=["Jobs"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    video: UploadFile,
    bbox: str,
    mass_kg: float | None = None,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    result = await db.execute(select(User).where(User.id == api_key.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.credits < 1:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Insufficient credits",
        )

    try:
        bbox_list = json.loads(bbox)
        if len(bbox_list) != 4 or not all(isinstance(v, int) for v in bbox_list):
            raise ValueError
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="bbox must be a JSON array of 4 integers: [x, y, width, height]",
        )

    job_id = str(uuid.uuid4())
    video_path = UPLOAD_DIR / f"{job_id}_{video.filename}"
    with open(video_path, "wb") as f:
        f.write(await video.read())

    job = Job(
        id=job_id,
        user_id=api_key.user_id,
        video_path=str(video_path),
        bbox=bbox,
        mass_kg=mass_kg,
        status=JobStatus.PENDING,
    )
    user.credits -= 1
    db.add(job)
    await db.commit()

    celery_app.send_task("worker.tasks.process_job", args=[job.id], queue="jobs")

    return JobResponse(id=job.id, status=job.status.value, created_at=job.created_at)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == api_key.user_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return JobResponse(id=job.id, status=job.status.value, created_at=job.created_at)


@router.get("/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(
    job_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> JobResultResponse:
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == api_key.user_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status != JobStatus.COMPLETED:
        return JobResultResponse(
            id=job.id,
            status=job.status.value,
            error_message=job.error_message,
        )

    return JobResultResponse(
        id=job.id,
        status=job.status.value,
        video_url=f"/api/v1/jobs/{job_id}/video",
        centroids_url=f"/api/v1/jobs/{job_id}/centroids",
    )


@router.get("/{job_id}/video")
async def get_job_video(
    job_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == api_key.user_id)
    )
    job = result.scalar_one_or_none()
    if not job or job.status != JobStatus.COMPLETED or not job.result_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not available")

    video_path = Path("/app") / job.result_path
    if not video_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found")

    return FileResponse(str(video_path), media_type="video/mp4")


@router.get("/{job_id}/centroids")
async def get_job_centroids(
    job_id: str,
    api_key: APIKey = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == api_key.user_id)
    )
    job = result.scalar_one_or_none()
    if not job or job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centroids not available")

    centroids_path = Path("/app") / job.result_path.replace("output.mp4", "centroids.csv")
    if not centroids_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Centroids file not found")

    return FileResponse(str(centroids_path), media_type="text/csv")
