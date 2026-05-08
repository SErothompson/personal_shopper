from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "personal_shopper",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.poll_prices"],
)

celery_app.conf.timezone = settings.celery_timezone
celery_app.conf.beat_schedule = {
    "daily-watch-price-refresh": {
        "task": "app.tasks.poll_prices.poll_watch_prices",
        "schedule": crontab(hour=8, minute=0),
    }
}
