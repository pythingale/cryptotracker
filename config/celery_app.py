import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
from celery.schedules import crontab

app = Celery("cryptotrackr")


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "fetch_historical_prices": {
        "task": "cryptocurrencies.tasks.fetch_historical_prices_tasks.fetch_historical_prices",
        "schedule": crontab(hour=0, minute=0),
    },
}
