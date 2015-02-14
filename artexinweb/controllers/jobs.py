# -*- coding: utf-8 -*-
import os
import uuid

from bottle import request, get, post, jinja2_view, jinja2_template, redirect

from artexinweb import settings
from artexinweb.forms import FetchableJobForm, StandaloneJobForm
from artexinweb.models import Job


@get('/jobs/')
@jinja2_view('jobs.html')
def jobs_list():
    status = request.query.get('status')
    if status:
        job_list = Job.objects.filter(status=status)
    else:
        job_list = Job.objects.all()

    return {'job_list': job_list,
            'current_status': status,
            'statuses': Job.STATUSES}


class JobController(object):

    forms = {
        Job.FETCHABLE: FetchableJobForm,
        Job.STANDALONE: StandaloneJobForm
    }

    @classmethod
    def fetchable(cls, job_type, form):
        Job.create(job_type=job_type,
                   targets=form.urls.data,
                   extract=form.extract.data,
                   javascript=form.javascript.data)
        return redirect('/jobs/')

    @classmethod
    def standalone(cls, job_type, form):
        folder_name = str(uuid.uuid4())
        media_root = settings.BOTTLE_CONFIG['web.media_root']
        upload_path = os.path.join(media_root, folder_name)

        os.makedirs(upload_path)

        for uploaded_file in request.files.getlist('files'):
            uploaded_file.save(upload_path)

        Job.create(targets=[upload_path],
                   job_type=job_type,
                   origin=form.origin.data)
        return redirect('/jobs/')


@post('/jobs/')
def jobs_create():
    job_type = request.forms.get('type')

    if Job.is_valid_type(job_type):
        form_cls = JobController.forms[job_type]
        form_data = request.forms.decode()
        form_data.update(request.files)
        form = form_cls(form_data)

        if form.validate():
            return getattr(JobController, job_type.lower())(job_type, form)

        template_name = 'jobs_{0}.html'.format(job_type.lower())
        return jinja2_template(template_name, form=form, job_type=job_type)

    return jinja2_template('jobs_wizard.html')


@get('/jobs/new/')
def jobs_new():
    job_type = request.query.get('type')
    if Job.is_valid_type(job_type):
        form_cls = JobController.forms[job_type]
        form = form_cls()

        return jinja2_template('jobs_{0}.html'.format(job_type.lower()),
                               form=form,
                               job_type=job_type)

    return jinja2_template('jobs_wizard.html')


@get('/jobs/<job_id:re:[a-zA-Z0-9]+>/tasks/')
@jinja2_view('tasks.html')
def task_list(job_id):
    job = Job.objects.get(job_id=job_id)
    return {'task_list': job.tasks, 'job_id': job_id}
