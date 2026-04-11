"""Celery application factory."""

from celery import Celery

from src.core.config import get_settings


def create_celery() -> Celery:
    settings = get_settings()
    app = Celery("rt_suggestion_engine", broker=settings.redis_url, backend=settings.redis_url)
    app.conf.task_default_queue = settings.compliance_queue
    app.conf.task_serializer = "json"
    app.conf.result_serializer = "json"
    app.conf.accept_content = ["json"]
    return app


celery_app = create_celery()
