# Celery Tasks

- `app.tasks.poll_prices.poll_watch_prices` refreshes active watch items.
- Scheduled by Celery beat at 8:00 AM local timezone.

Start worker:

```powershell
celery -A app.tasks.celery_app:celery_app worker --loglevel=info --pool=solo
```

Start beat scheduler:

```powershell
celery -A app.tasks.celery_app:celery_app beat --loglevel=info
```
