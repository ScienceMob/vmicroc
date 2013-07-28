from django.db import models

from locations.models import Location, Sensor


class Datum(models.Model):
    location = models.ForeignKey(Location)
    sensor = models.ForeignKey(Sensor)

    timestamp = models.DateTimeField(db_index=True)
    temperature = models.FloatField(null=True)

    class Meta:
        verbose_name_plural = 'data'

    def __unicode__(self):
        return '%s @ %s' % (self.sensor, self.timestamp)


class DaySummary(models.Model):
    location = models.ForeignKey(Location)
    sensor = models.ForeignKey(Sensor)

    day = models.DateField(db_index=True)

    minimum = models.FloatField(null=True)
    average = models.FloatField(null=True)
    maximum = models.FloatField(null=True)

    def __unicode__(self):
        return '%s @ %s' % (self.sensor, self.day)
