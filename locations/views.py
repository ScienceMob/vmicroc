import csv
from datetime import datetime
from StringIO import StringIO
import pytz

from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.utils import timezone

from locations.models import Location
from data.models import Datum, DaySummary


ACST = pytz.timezone('Australia/Adelaide')


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

    # Extract the timestamp from the raw data request, and convert it
    # into a time in the local timezone.
    try:
        timestamp = timezone.localtime(datetime.fromtimestamp(int(request.GET['timestamp']) / 1000).replace(tzinfo=ACST))
    except KeyError:
        raise Http404

    # Get all data that falls on the same day at the same location.
    raw_data = Datum.objects.filter(
        location=location,
        timestamp__range=(
                timestamp.replace(hour=0, minute=0, second=0),
                timestamp.replace(hour=23, minute=59, second=59)
            )
        ).select_related(
            "sensor__position"
        ).order_by(
            'timestamp', 'sensor'
        )

    output = StringIO()
    writer = csv.writer(output)

    # Write header block
    sensors = location.sensors.order_by('position')
    writer.writerow(['Timestamp'] + [sensor.get_position_display() for sensor in sensors])

    current_timestamp = None
    row = None
    for datum in raw_data:
        # If this is the first row, or the first row of a new timestamp,
        # fill out a dummy row of data.
        if row is None or current_timestamp != datum.timestamp:
            # A new timestamp has been found, so output
            # the compiled row of data
            if row is not None:
                writer.writerow(
                    [timezone.localtime(current_timestamp).strftime('%Y/%m/%d %H:%M:%S')] +
                    [val for (key, val) in sorted(row.items())]
                )

            # Set up a new empty row
            row = dict(
                (sensor.position, None)
                for sensor in sensors
            )

            # Record the new current timestamp
            current_timestamp = datum.timestamp

        # Add this sensor's reading to the row.
        row[datum.sensor.position] = datum.temperature

    # We've got no more data to process; if there's anything stored
    # in the row, record it as the last timestamp.
    if current_timestamp and any(row.values()):
        writer.writerow(
            [current_timestamp.strftime('%Y/%m/%d %H:%M:%S')] +
            [val for (key, val) in sorted(row.items())]
        )

    return HttpResponse(output.getvalue(), content_type='text/csv')


def summary_data(request, location_id):
    try:
        location = Location.objects.get(pk=location_id)
    except Location.DoesNotExist:
        raise Http404

    output = StringIO()
    writer = csv.writer(output)

    summary_data = DaySummary.objects.filter(
            location=location,
        ).select_related(
            "sensor__position"
        ).order_by(
            'day', 'sensor'
        )

    output = StringIO()
    writer = csv.writer(output)

    # Write header block
    sensors = location.sensors.order_by('position')
    writer.writerow(['Day'] + [sensor.get_position_display() for sensor in sensors])

    current_day = None
    row = None
    for summary in summary_data:
        # If this is the first row, or the first row of a new timestamp,
        # fill out a dummy row of data.
        if row is None or current_day != summary.day:
            # A new timestamp has been found, so output
            # the compiled row of data
            if row is not None:
                writer.writerow(
                    [current_day.strftime('%Y/%m/%d')] +
                    ['%s;%s;%s' % val for (key, val) in sorted(row.items())]
                )

            # Set up a new empty row
            row = dict(
                (sensor.position, None)
                for sensor in sensors
            )

            # Record the new current timestamp
            current_day = summary.day

        # Add this sensor's reading to the row.
        row[summary.sensor.position] = (summary.minimum, summary.average, summary.maximum)

    # We've got no more data to process; if there's anything stored
    # in the row, record it as the last timestamp.
    if current_day and any(row.values()):
        writer.writerow(
            [current_day.strftime('%Y/%m/%d')] +
            ['%s;%s;%s' % val for (key, val) in sorted(row.items())]
        )

    return HttpResponse(output.getvalue(), content_type='text/csv')


def export_data(request, location_id):
    try:
        location = Location.objects.get(pk=location_id)
    except Location.DoesNotExist:
        raise Http404

    # Get all data that falls on the same day at the same location.
    raw_data = Datum.objects.filter(
        location=location,
        ).select_related(
            "sensor__position"
        ).order_by(
            'timestamp', 'sensor'
        )

    output = StringIO()
    writer = csv.writer(output)

    # Write header block
    sensors = location.sensors.order_by('position')
    writer.writerow(['Timestamp'] + [sensor.get_position_display() for sensor in sensors])

    current_timestamp = None
    row = None
    for datum in raw_data:
        # If this is the first row, or the first row of a new timestamp,
        # fill out a dummy row of data.
        if row is None or current_timestamp != datum.timestamp:
            # A new timestamp has been found, so output
            # the compiled row of data
            if row is not None:
                writer.writerow(
                    [timezone.localtime(current_timestamp).strftime('%Y/%m/%d %H:%M:%S')] +
                    [val for (key, val) in sorted(row.items())]
                )

            # Set up a new empty row
            row = dict(
                (sensor.position, None)
                for sensor in sensors
            )

            # Record the new current timestamp
            current_timestamp = datum.timestamp

        # Add this sensor's reading to the row.
        row[datum.sensor.position] = datum.temperature

    # We've got no more data to process; if there's anything stored
    # in the row, record it as the last timestamp.
    if current_timestamp and any(row.values()):
        writer.writerow(
            [current_timestamp.strftime('%Y/%m/%d %H:%M:%S')] +
            [val for (key, val) in sorted(row.items())]
        )

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=vmicroc.%s.%s.csv' % (
        location.name,
        timezone.localtime(timezone.now()).strftime('%Y_%m_%d-%H_%M')
    )
    return response
