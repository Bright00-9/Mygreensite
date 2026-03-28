import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'greensite.settings')

app = Celery('greensite')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# komado_project/celery.py
app.conf.beat_schedule = {
    'hunt-zombies-every-morning': {
        'task': 'dashboard.tasks.hunt_for_zombies',
        'schedule': 86400.0, # Runs once every 24 hours
    },
}
