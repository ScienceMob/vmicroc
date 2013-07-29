import csv
from datetime import datetime, timedelta
import pytz
import time

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Max, Min
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils import timezone

from locations.models import Sensor
from data.models import Datum, DaySummary
from data.forms import UploadForm


ACST = pytz.timezone('Australia/Adelaide')
EPOCH = time.mktime((2000, 1, 1, 0, 0, 0, 0, 0, 0))


class RTCFailure(Exception):
    pass


@staff_member_required
def upload(request):
    if request.method == 'POST':
        upload_form = UploadForm(data=request.POST, files=request.FILES)
        if upload_form.is_valid():
            # Errors and warnings observed during import
            errors = []
            warnings = []

            # Track the observed data for analysis purposes
            unknown_sensor_ids = set()
            observed_timestamps = set()
            saved_count = 0

            # Now, parse the file.
            location = upload_form.cleaned_data['location']
            sensors = dict((s.sensor_id, s) for s in location.sensors.all())
            try:
                reader = csv.reader(request.FILES.get('data_file'))
                for n, parts in enumerate(reader):
                    if len(parts) != 3:
                        errors.append('Line %s: Invalid data format' % (n + 1))
                    else:
                        timestamp, sensor_id, raw_reading = parts

                        try:
                            sensor = sensors[sensor_id]
                            timestamp = datetime.fromtimestamp(int(timestamp) + EPOCH).replace(tzinfo=ACST)
                            if timestamp < (timezone.now() - timedelta(days=730)):
                                raise RTCFailure('File contains timestamps that are > 2 years old; possible RTC failure')
                            observed_timestamps.add(timestamp)
                            raw_temperature = float(raw_reading)
                            temperature = raw_temperature * sensor.slope + sensor.intercept

                            try:
                                Datum.objects.get(
                                    location=location,
                                    sensor=sensor,
                                    timestamp=timestamp
                                )
                                warnings.append('Line %s: Data for sensor %s at %s has already been recorded' % (n, sensor_id, timestamp))
                            except Datum.MultipleObjectsReturned:
                                errors.append('Line %s: Multiple existing matches for sensor %s at %s exist in the database' % (n, sensor_id, timestamp))
                            except Datum.DoesNotExist:
                                Datum.objects.create(
                                    location=location,
                                    sensor=sensor,
                                    timestamp=timestamp,
                                    raw_temperature=raw_temperature,
                                    temperature=temperature
                                )
                            saved_count = saved_count + 1
                        except KeyError:
                            unknown_sensor_ids.add(sensor_id)
                        except TypeError, e:
                            errors.append("Line %s: Invalid timestamp '%s'" % (n + 1, timestamp))
                        except ValueError:
                            errors.append("Line %s: Invalid temperature reading '%s'" % (n + 1, raw_reading))
            except RTCFailure, e:
                errors.append(e.message)

            for sensor_id in unknown_sensor_ids:
                try:
                    errors.append('File contains data for unknown sensor %s' % sensor_id)
                except Sensor.DoesNotExist:
                    warnings.append('File contains data for sensor %s, which is not at %s' % (sensor_id, location))

            # Report success, but if there are errors/warnings, qualify that success.
            if errors or warnings:
                messages.info(request, 'Data file uploaded with some problems; %s records uploaded' % saved_count)
            else:
                messages.success(request, 'Data file uploaded successfully; %s records uploaded' % saved_count)

            # Print the first 20 warnings, and the first 20 errors.
            # If there are more, print a count to indicate how bad the problem is.
            for error in errors[:20]:
                messages.error(request, error)
            if len(errors) > 20:
                messages.error(request, '... and %s other errors' % len(errors) - 20)
            for warning in warnings[:20]:
                messages.warning(request, warning)
            if len(warnings) > 20:
                messages.warnings(request, '... and %s other warnings' % len(warnings) - 20)

            # Generate summary statistics for all observed timestamps
            for timestamp in observed_timestamps:
                for sensor in sensors.values():
                    data = Datum.objects.filter(
                        location=location,
                        sensor=sensor,
                        timestamp__range=(
                            timestamp.replace(hour=0, minute=0, second=0),
                            timestamp.replace(hour=23, minute=59, second=59)
                        )
                    ).aggregate(
                        min=Min('temperature'),
                        avg=Avg('temperature'),
                        max=Max('temperature'),
                    )

                    if data['min']:
                        try:
                            summary = DaySummary.objects.get(
                                location=location,
                                sensor=sensor,
                                day=timestamp.date(),
                            )
                            summary.minimum = data['min']
                            summary.average = data['avg']
                            summary.maximum = data['max']
                            summary.save()

                        except DaySummary.DoesNotExist:
                            summary = DaySummary.objects.create(
                                location=location,
                                sensor=sensor,
                                day=timestamp.date(),
                                minimum=data['min'],
                                average=data['avg'],
                                maximum=data['max'],
                            )

            return HttpResponseRedirect(reverse('data_upload'))
    else:
        upload_form = UploadForm()

    return render(request, 'data/upload.html', {
            'upload_form': upload_form,
        })
