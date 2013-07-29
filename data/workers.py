import csv
from datetime import datetime, timedelta
import os
import pytz
import time

from django.conf import settings
from django.db.models import Min, Avg, Max
from django.utils import timezone

from locations.models import Sensor


ACST = pytz.timezone('Australia/Adelaide')
EPOCH = time.mktime((2000, 1, 1, 0, 0, 0, 0, 0, 0))


class RTCFailure(Exception):
    pass


def import_data_file(import_task_id):
    from data.models import Datum, DaySummary, ImportTask, ImportMessage
    import_task = ImportTask.objects.get(pk=import_task_id)
    import_task.status = ImportTask.IMPORTING
    import_task.save()

    try:
        # Errors and warnings observed during import
        errors = []
        warnings = []

        # Track the observed data for analysis purposes
        unknown_sensor_ids = set()
        observed_dates = set()
        saved_count = 0

        # Now, parse the import task.
        location = import_task.location
        sensors = dict((s.sensor_id, s) for s in location.sensors.all())
        with open(os.path.join(settings.MEDIA_ROOT, import_task.data_file.name)) as data_file:
            try:
                reader = csv.reader(data_file)
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
                            observed_dates.add(timestamp.date())
                            raw_temperature = float(raw_reading)
                            temperature = raw_temperature * sensor.slope + sensor.intercept

                            if n % 1000 == 1:
                                print "Processing datum for %s" % timestamp
                            try:
                                Datum.objects.get(
                                    location=location,
                                    sensor=sensor,
                                    timestamp=timestamp
                                )
                                warnings.append('Line %s: Data for sensor %s at %s has already been recorded' % (n + 1, sensor_id, timestamp))
                            except Datum.MultipleObjectsReturned:
                                errors.append('Line %s: Multiple existing matches for sensor %s at %s exist in the database' % (n + 1, sensor_id, timestamp))
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

        import_task.status = ImportTask.SUMMARIZING
        import_task.save()

        # Generate summary statistics for all observed timestamps
        print sorted(observed_dates)
        for day in sorted(observed_dates):
            print "Summarizing ", day
            for sensor in sensors.values():
                data = Datum.objects.filter(
                    location=location,
                    sensor=sensor,
                    timestamp__range=(
                        datetime(year=day.year, month=day.month, day=day.day, hour=0, minute=0, second=0, tzinfo=ACST),
                        datetime(year=day.year, month=day.month, day=day.day, hour=23, minute=59, second=59, tzinfo=ACST),
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
                            day=day,
                        )
                        summary.minimum = data['min']
                        summary.average = data['avg']
                        summary.maximum = data['max']
                        summary.save()

                    except DaySummary.DoesNotExist:
                        summary = DaySummary.objects.create(
                            location=location,
                            sensor=sensor,
                            day=day,
                            minimum=data['min'],
                            average=data['avg'],
                            maximum=data['max'],
                        )

        for sensor_id in unknown_sensor_ids:
            try:
                errors.append('File contains data for unknown sensor %s' % sensor_id)
            except Sensor.DoesNotExist:
                warnings.append('File contains data for sensor %s, which is not at %s' % (sensor_id, location))

        # Report success, but if there are errors/warnings, qualify that success.
        if errors or warnings:
            import_task.status = ImportTask.ATTENTION_REQUIRED
            import_task.messages.create(level=ImportMessage.SUMMARY, message='Data file uploaded with some problems; %s records uploaded' % saved_count)
        else:
            import_task.status = ImportTask.DONE
            import_task.messages.create(level=ImportMessage.SUMMARY, message='Data file uploaded successfully; %s records uploaded' % saved_count)

        # Print the first 20 warnings, and the first 20 errors.
        # If there are more, print a count to indicate how bad the problem is.
        for error in errors[:20]:
            import_task.messages.create(level=ImportMessage.ERROR, message=error)
        if len(errors) > 20:
            import_task.messages.create(level=ImportMessage.ERROR, message='... and %s other errors' % (len(errors) - 20))
        for warning in warnings[:20]:
            import_task.messages.create(level=ImportMessage.WARNING, message=warning)
        if len(warnings) > 20:
            import_task.messages.create(level=ImportMessage.WARNING, message='... and %s other warnings' % (len(warnings) - 20))

    except Exception, e:
        # Catch all... in case something goes wrong.
        import_task.status = ImportTask.ATTENTION_REQUIRED
        import_task.messages.create(level=ImportMessage.ERROR, message=str(e))

    # Save the import task state
    import_task.save()
