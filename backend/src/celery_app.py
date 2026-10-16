"""
Celery configuration and app
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
from celery import Celery
from src.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "control_red",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.tasks.network"]  # Task modules
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks
    task_acks_late=True,  # Acknowledge after task completion
    task_reject_on_worker_lost=True,
)

# Task routes (optional)
celery_app.conf.task_routes = {
    'src.tasks.network.*': {'queue': 'network'},
    'src.tasks.blocking.*': {'queue': 'blocking'},
}

# Beat schedule (periodic tasks)
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'scan-network-every-5-minutes': {
        'task': 'src.tasks.network.periodic_network_scan',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
}
