import io
from unittest.mock import patch

from sqlalchemy.future import select

from api.models import User


async def _register(client, email: str) -> str:
    response = await client.post("/api/v1/auth/register", json={"email": email})
    return response.json()["api_key"]


def _job_form(bbox: str = "[0, 0, 100, 100]") -> dict:
    """Multipart form with both the file and text fields packed into files=."""
    return {
        "video": ("test.mp4", io.BytesIO(b"fake-video-data"), "video/mp4"),
        "bbox": (None, bbox),
    }


async def test_create_job_missing_api_key_returns_401(client):
    response = await client.post("/api/v1/jobs")
    assert response.status_code == 401


async def test_create_job_invalid_api_key_returns_401(client):
    response = await client.post(
        "/api/v1/jobs",
        headers={"X-API-Key": "totally-wrong-key"},
        files=_job_form(),
    )
    assert response.status_code == 401


async def test_get_job_missing_api_key_returns_401(client):
    response = await client.get("/api/v1/jobs/some-id")
    assert response.status_code == 401


async def test_create_job_bad_bbox_json_returns_422(client):
    api_key = await _register(client, "user@example.com")
    response = await client.post(
        "/api/v1/jobs",
        headers={"X-API-Key": api_key},
        files=_job_form(bbox="not-json"),
    )
    assert response.status_code == 422


async def test_create_job_bbox_wrong_length_returns_422(client):
    api_key = await _register(client, "user@example.com")
    response = await client.post(
        "/api/v1/jobs",
        headers={"X-API-Key": api_key},
        files=_job_form(bbox="[0, 0, 100]"),
    )
    assert response.status_code == 422


async def test_create_job_bbox_non_integer_values_returns_422(client):
    api_key = await _register(client, "user@example.com")
    response = await client.post(
        "/api/v1/jobs",
        headers={"X-API-Key": api_key},
        files=_job_form(bbox="[0.5, 0, 100, 100]"),
    )
    assert response.status_code == 422


async def test_create_job_success_returns_201(client):
    api_key = await _register(client, "user@example.com")
    with patch("api.v1.routers.jobs.celery_app.send_task"):
        response = await client.post(
            "/api/v1/jobs",
            headers={"X-API-Key": api_key},
            files=_job_form(),
        )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert "id" in data


async def test_create_job_deducts_one_credit(client, db_session):
    api_key = await _register(client, "user@example.com")
    with patch("api.v1.routers.jobs.celery_app.send_task"):
        await client.post(
            "/api/v1/jobs",
            headers={"X-API-Key": api_key},
            files=_job_form(),
        )
    db_session.expire_all()
    result = await db_session.execute(
        select(User).where(User.email == "user@example.com")
    )
    user = result.scalar_one()
    assert user.credits == 9


async def test_create_job_dispatches_celery_task(client):
    api_key = await _register(client, "user@example.com")
    with patch("api.v1.routers.jobs.celery_app.send_task") as mock_send:
        response = await client.post(
            "/api/v1/jobs",
            headers={"X-API-Key": api_key},
            files=_job_form(),
        )
        job_id = response.json()["id"]
        mock_send.assert_called_once_with(
            "worker.tasks.process_job", args=[job_id], queue="jobs"
        )


async def test_create_job_no_credits_returns_402(client, db_session):
    api_key = await _register(client, "user@example.com")

    db_session.expire_all()
    result = await db_session.execute(
        select(User).where(User.email == "user@example.com")
    )
    user = result.scalar_one()
    user.credits = 0
    await db_session.commit()

    response = await client.post(
        "/api/v1/jobs",
        headers={"X-API-Key": api_key},
        files=_job_form(),
    )
    assert response.status_code == 402


async def test_get_job_not_found_returns_404(client):
    api_key = await _register(client, "user@example.com")
    response = await client.get(
        "/api/v1/jobs/nonexistent-id",
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 404


async def test_get_job_returns_correct_status(client):
    api_key = await _register(client, "user@example.com")
    with patch("api.v1.routers.jobs.celery_app.send_task"):
        create_resp = await client.post(
            "/api/v1/jobs",
            headers={"X-API-Key": api_key},
            files=_job_form(),
        )
    job_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"X-API-Key": api_key},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


async def test_get_job_isolated_by_user(client):
    key1 = await _register(client, "user1@example.com")
    key2 = await _register(client, "user2@example.com")

    with patch("api.v1.routers.jobs.celery_app.send_task"):
        create_resp = await client.post(
            "/api/v1/jobs",
            headers={"X-API-Key": key1},
            files=_job_form(),
        )
    job_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/jobs/{job_id}",
        headers={"X-API-Key": key2},
    )
    assert response.status_code == 404
