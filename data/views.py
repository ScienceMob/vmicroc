from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from data.models import ImportTask


class ImportTaskForm(forms.ModelForm):
    class Meta:
        model = ImportTask
        fields = ('data_file',)


@staff_member_required
def upload(request):
    if request.method == 'POST':
        import_task_form = ImportTaskForm(data=request.POST, files=request.FILES)
        if import_task_form.is_valid():
            import_task = import_task_form.save()
            import_task.enqueue()
            messages.info(request, 'Data file queued for processing')
            return HttpResponseRedirect(reverse('data_upload'))
    else:
        import_task_form = ImportTaskForm()

    return render(request, 'data/upload.html', {
            'import_task_form': import_task_form,
        })


@staff_member_required
def enqueue(request, import_task_id):
    import_task = ImportTask.objects.get(pk=import_task_id)
    import_task.enqueue()

    messages.info(request, 'Data file queued for processing')
    return HttpResponseRedirect(reverse('admin:data_importtask_changelist'))
