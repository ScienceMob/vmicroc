import csv
from datetime import datetime, timedelta
from StringIO import StringIO

from django.http import HttpResponse, Http404
from django.shortcuts import render


from locations.models import Location


def inspector(request, base_template='normal.html'):
    return render(request, 'locations/inspector.html', {
            'base_template': base_template,
            'locations': Location.objects.all()
        })


def detail_data(request, location_id):
    try:
        location = Location.objects.get(pk=location_id)
    except Location.DoesNotExist:
        raise Http404

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['Data'] + [sensor.get_position_display() for sensor in location.sensors.order_by('position')])

    for i in range(1000):
        writer.writerow(
            [(datetime(2009, 1, 1) + timedelta(i)).strftime('%Y%m%d')] +
            [
                '%s;%s;%s' % (sensor.position - 10, sensor.position, sensor.position + 10)
                for sensor in location.sensors.order_by('position')
            ]
        )

    return HttpResponse(output.getvalue(), content_type='text/csv')


def summary_data(request, location_id):
    try:
        location = Location.objects.get(pk=location_id)
    except Location.DoesNotExist:
        raise Http404

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(['Data'] + [sensor.get_position_display() for sensor in location.sensors.order_by('position')])

    for i in range(1000):
        writer.writerow(
            [(datetime(2009, 1, 1) + timedelta(i)).strftime('%Y%m%d')] +
            [
                '%s;%s;%s' % (sensor.position - 10, sensor.position, sensor.position + 10)
                for sensor in location.sensors.order_by('position')
            ]
        )

    return HttpResponse(output.getvalue(), content_type='text/csv')
