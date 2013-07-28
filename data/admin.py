from django.contrib import admin

from data.models import Datum


class DatumAdmin(admin.ModelAdmin):
    list_display = ('location', 'sensor', 'timestamp', 'temperature')
    list_filter = ('location',)


admin.site.register(Datum, DatumAdmin)
