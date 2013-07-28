from django.shortcuts import render

from locations.models import Location


def inspector(request, base_template='normal.html'):
    return render(request, 'locations/inspector.html', {
            'base_template': base_template,
            'locations': Location.objects.all()
        })
