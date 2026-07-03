from celery import Celery

from api.core.settings import settings

celery_app = Celery(
    "plate_tracker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["worker.tasks"],
)

celery_app.conf.task_routes = {
    "worker.tasks.process_job": {"queue": "jobs"},
}
