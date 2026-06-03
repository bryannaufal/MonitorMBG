"""Celery application instance and configuration."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "monitor_mbg",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    # ── Serialization ──
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # ── Timezone ──
    timezone="Asia/Jakarta",
    enable_utc=True,

    # ── Task Behavior ──
    task_track_started=True,
    task_time_limit=600,           # 10 min hard limit
    task_soft_time_limit=540,      # 9 min soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,

    # ── Result Expiry ──
    result_expires=3600,           # Results expire after 1 hour

    # ── Task Routes ──
    task_routes={
        "app.workers.scraping_tasks.*": {"queue": "scraping"},
        "app.workers.nlp_tasks.*": {"queue": "nlp"},
        "app.workers.cv_tasks.*": {"queue": "cv"},
        "app.workers.nutrition_tasks.*": {"queue": "cv"},
        "app.workers.scoring_tasks.*": {"queue": "scoring"},
    },
)

# ── Auto-discover tasks ──
celery_app.autodiscover_tasks([
    "app.workers.scraping_tasks",
    "app.workers.nlp_tasks",
    "app.workers.cv_tasks",
    "app.workers.nutrition_tasks",
    "app.workers.scoring_tasks",
])
