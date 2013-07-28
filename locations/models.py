from django.db import models


class Location(models.Model):
    name = models.CharField(max_length=100)

    latitude = models.FloatField()
    longitude = models.FloatField()

    def __unicode__(self):
        return self.name


class Sensor(models.Model):
    POSITION_CHOICES = [
        (-20, '-0.2m'),
        (0, 'Ground'),
        (40, '0.4m'),
        (80, '0.8m'),
        (100, '1m'),
        (120, '1.2m'),
        (180, '1.8m'),
    ]
    location = models.ForeignKey(Location)
    position = models.IntegerField(choices=POSITION_CHOICES)

    sensor_id = models.CharField(max_length=20, db_index=True)

    slope = models.FloatField(default=1.0)
    intercept = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('location', 'position')

    def __unicode__(self):
        return '%s:%s' % (self.location, self.get_position_display())
