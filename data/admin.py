from django.contrib import admin

from data.models import Datum, DaySummary


class DatumAdmin(admin.ModelAdmin):
    list_display = ('location', 'sensor', 'timestamp', 'raw_temperature', 'temperature')
    list_filter = ('location',)


class DaySummaryAdmin(admin.ModelAdmin):
    list_display = ('location', 'sensor', 'day', 'minimum', 'average', 'maximum')
    list_filter = ('location',)
    date_heirarchy = ('day',)


admin.site.register(Datum, DatumAdmin)
admin.site.register(DaySummary, DaySummaryAdmin)
