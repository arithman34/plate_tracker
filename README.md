# Plate Tracker

A barbell velocity tracker that analyses lift videos and computes real-time kinematics — velocity, acceleration, force, and power — by tracking the plate across frames using computer vision.

**API docs:** [plate-tracker.arithman.dev/docs](https://plate-tracker.arithman.dev/docs)


## How it works

1. Upload a lift video and provide a bounding box around the plate in the first frame
2. The worker tracks the plate across every frame using OpenCV's CSRT tracker
3. Savitzky-Golay filtering smooths the position signal and computes velocity and acceleration
4. Scale is derived from the plate diameter (450 mm), so no calibration is needed
5. The annotated video and centroid CSV are returned via the API

## Stack

| Layer | Tech |
|---|---|
| CV pipeline | OpenCV CSRT, Savitzky-Golay (scipy) |
| API | FastAPI + async SQLAlchemy (asyncpg) |
| Job queue | Celery + Redis |
| Database | PostgreSQL |
| Storage | Local filesystem (shared Docker volume) |
| Deploy | Hetzner VPS, Docker Compose, nginx, Let's Encrypt |
| CI/CD | GitHub Actions (auto-deploy on push to `main`) |
| Auth | SHA-256 hashed API keys, credit system |

AWS infrastructure (ECS Fargate, RDS, ElastiCache, ALB, ECR, S3) is defined in `terraform/` and kept for portfolio reference — the live deployment runs on Hetzner for cost effectiveness.

## API

### Register

```bash
curl -X POST https://plate-tracker.arithman.dev/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
```

Returns an API key — store it, it won't be shown again.

### Submit a job

`bbox` is `[x, y, width, height]` of the plate in the first frame.

```bash
curl -X POST https://plate-tracker.arithman.dev/api/v1/jobs \
  -H "X-API-Key: <your-key>" \
  -F "video=@squat.mp4" \
  -F 'bbox=[361, 14, 270, 287]' \
  -F "mass_kg=100"
```

### Poll for status

```bash
curl https://plate-tracker.arithman.dev/api/v1/jobs/<job-id> \
  -H "X-API-Key: <your-key>"
```

Status: `pending` -> `processing` -> `completed` / `failed`

### Download results

```bash
# Annotated video
curl https://plate-tracker.arithman.dev/api/v1/jobs/<job-id>/video \
  -H "X-API-Key: <your-key>" -o output.mp4

# Centroid CSV (frame, cx, cy)
curl https://plate-tracker.arithman.dev/api/v1/jobs/<job-id>/centroids \
  -H "X-API-Key: <your-key>" -o centroids.csv
```

## Local development

```bash
# Install dependencies
uv sync

# Start services
docker compose up -d

# Run migrations
uv run alembic upgrade head

# Start API
uv run uvicorn api.main:app --reload

# Start worker
uv run celery -A worker.celery_app worker --queues jobs --loglevel=info
```

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

## Project structure

```
src/plate_tracker/   # CV library (tracker, kinematics, overlay)
api/                 # FastAPI app (auth, jobs, models, schemas)
worker/              # Celery worker and task
migrations/          # Alembic migrations
terraform/           # AWS infrastructure (portfolio reference)
notebooks/           # Kinematics explorer
```

## Metrics

| Metric | Description |
|---|---|
| `velocity_m_s` | Current bar velocity (m/s) |
| `peak_velocity_m_s` | Peak velocity across the lift |
| `mean_velocity_m_s` | Mean velocity across the lift |
| `acceleration_m_s2` | Current acceleration (m/s²) |
| `force_n` | Force in Newtons (requires `mass_kg`) |
| `power_w` | Power in Watts (requires `mass_kg`) |

## Future Work

- Add frontend for easier job submission and result visualization
- Add email notifications when jobs complete
