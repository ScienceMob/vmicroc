from django.contrib import admin

from locations.models import Location, Sensor


class SensorAdmin(admin.TabularInline):
    model = Sensor
    list_display = ('position', 'sensor_id')
    extra = 0


class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    inlines = [SensorAdmin]

admin.site.register(Location, LocationAdmin)
