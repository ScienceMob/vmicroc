from django.db import models

from locations.models import Location, Sensor


class Datum(models.Model):
    location = models.ForeignKey(Location)
    sensor = models.ForeignKey(Sensor)

    timestamp = models.DateTimeField(db_index=True)
    temperature = models.FloatField()

    class Meta:
        verbose_name_plural = 'data'

    def __unicode__(self):
        return '%s @ %s' % (self.sensor, self.timestamp)
