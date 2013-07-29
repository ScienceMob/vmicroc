from django.contrib import admin
from django.contrib import messages

from data.models import Datum, DaySummary, ImportTask, ImportMessage


class DatumAdmin(admin.ModelAdmin):
    list_display = ('location', 'sensor', 'timestamp', 'raw_temperature', 'temperature')
    list_filter = ('location',)


class DaySummaryAdmin(admin.ModelAdmin):
    list_display = ('location', 'sensor', 'day', 'minimum', 'average', 'maximum')
    list_filter = ('location',)
    date_heirarchy = ('day',)


def enqueue(modeladmin, request, queryset):
    for task in queryset:
        messages.info(request, '%s enqueued for processing' % task)
        task.enqueue()
enqueue.short_description = "Enqueue for processing"


class ImportMessageInline(admin.TabularInline):
    model = ImportMessage
    list_display = ('level', 'message')
    readonly_fields = ('level', 'message')
    ordering = ('level',)
    extra = 0


class ImportTaskAdmin(admin.ModelAdmin):
    list_display = ('location', 'status')
    list_filter = ('status',)
    inlines = [ImportMessageInline]
    actions = [enqueue]


admin.site.register(Datum, DatumAdmin)
admin.site.register(DaySummary, DaySummaryAdmin)
admin.site.register(ImportTask, ImportTaskAdmin)
