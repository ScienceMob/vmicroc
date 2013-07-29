from django import forms

from locations.models import Location


class UploadForm(forms.Form):
    location = forms.ModelChoiceField(queryset=Location.objects.all())
    data_file = forms.FileField()
