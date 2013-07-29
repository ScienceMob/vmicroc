from django.db import models

from locations.models import Location, Sensor


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
