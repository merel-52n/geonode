from .opensensemap import get_city_bounding_box, get_box_data
from .constants import bbox_budapest

from geonode.celery_app import app
from django_celery_beat.models import (
            IntervalSchedule,
            PeriodicTask,
        )

import logging

logger = logging.getLogger(__name__)

# Creating celery schedules for running every hour, every day or every minute
schedule1h, created1h = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.HOURS
)

schedule1d, created1d = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.DAYS
)

schedule1m, created1m = IntervalSchedule.objects.get_or_create(
    every=1,
    period=IntervalSchedule.MINUTES
)

# Below a task is defined using '@app.task' which calls the celery.app and added to a queue
# The tasks are then scheduled with class 'PeriodicTask' from the django-celery-beat models library

@app.task(
    bind=True,
    queue='geonode',
    name='get_city_bounding_box',
    acks_late=False,
    ignore_result=False,
)
def get_city_bounding_box_task(self):
    logger.info("Runing get_city_bounding_box_task task")
    get_city_bounding_box("Budapest")

PeriodicTask.objects.get_or_create(
    interval=schedule1h,
    name='get_city_bounding_box',
    task='geonode.livinglabdata.tasks.get_city_bounding_box_task',
    enabled=False
)

@app.task(
    bind=True,
    queue='geonode',
    name='get_box_data',
    acks_late=False,
    ignore_result=False,
)
def get_box_data_temperature_task(self):
    logger.info("Runing get_box_data_task task")
    # First get the result of task get_sensorbox_ids_task 
    get_box_data(bbox_budapest, "Temperatur")

PeriodicTask.objects.get_or_create(
    interval=schedule1h,
    name='get_city_bounding_box',
    task='geonode.livinglabdata.tasks.get_city_bounding_box_task',
    enabled=False
)

PeriodicTask.objects.get_or_create(
    interval=schedule1h,
    name='get_box_data_temperature',
    task='geonode.livinglabdata.tasks.get_box_data_temperature_task',
    enabled=False
)

