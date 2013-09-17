import os

from redis import Redis
from rq import Queue

from django.db import models

from locations.models import Location, Sensor
from data.workers import import_data_file


class Datum(models.Model):
    location = models.ForeignKey(Location)
    sensor = models.ForeignKey(Sensor)

    timestamp = models.DateTimeField(db_index=True)
    raw_temperature = models.FloatField()
    temperature = models.FloatField('Calibrated temperature')

    class Meta:
        verbose_name_plural = 'data'

    def __unicode__(self):
        return '%s @ %s' % (self.sensor, self.timestamp)


class DaySummary(models.Model):
    location = models.ForeignKey(Location)
    sensor = models.ForeignKey(Sensor)

    day = models.DateField(db_index=True)

    minimum = models.FloatField()
    average = models.FloatField()
    maximum = models.FloatField()

    class Meta:
        verbose_name_plural = 'day summaries'

    def __unicode__(self):
        return '%s @ %s' % (self.sensor, self.day)


class ImportTask(models.Model):
    PENDING = 10
    IMPORTING = 11
    SUMMARIZING = 12
    DONE = 20
    ATTENTION_REQUIRED = 30
    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (IMPORTING, 'Importing'),
        (SUMMARIZING, 'Summarizing'),
        (DONE, 'Done'),
        (ATTENTION_REQUIRED, 'Attention Required'),
    )
    uploaded = models.DateTimeField(auto_now_add=True)
    data_file = models.FileField(upload_to='imports')

    status = models.IntegerField(choices=STATUS_CHOICES, default=PENDING)

    def __unicode__(self):
        return 'Import task %s (%s)' % (self.id, self.get_status_display())

    def enqueue(self):
        # Set the status of the task to PENDING
        self.status = self.PENDING
        self.save()
        # Purge any existing import messages
        self.messages.all().delete()

        # Enqueue the task.
        q = Queue(connection=Redis())
        q.enqueue_call(
            func=import_data_file,
            args=(self.id,),
            timeout=600
        )


class ImportMessage(models.Model):
    INFO = 20
    SUMMARY = 25
    WARNING = 30
    ERROR = 40
    LEVEL_CHOICES = (
        (INFO, 'Info'),
        (SUMMARY, 'Summary'),
        (WARNING, 'Warning'),
        (ERROR, 'Error'),
    )
    task = models.ForeignKey(ImportTask, related_name='messages')
    level = models.IntegerField(choices=LEVEL_CHOICES)
    message = models.CharField(max_length=512)

    def __unicode__(self):
        return '[%s] %s: %s' % (self.task.id, self.get_level_display(), self.message)
