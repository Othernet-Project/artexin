# -*- coding: utf-8 -*-
import os
import uuid

from bottle import request, get, post, jinja2_view, jinja2_template, redirect

from artexinweb import settings
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


class JobForm(object):

    @classmethod
    def fetchable(cls):
        option_names = ('javascript', 'extract')
        options = dict((key, bool(request.forms.get(key)))
                       for key in option_names)

        raw_urls = request.forms.get('urls')
        urls = list(set(url.strip() for url in raw_urls.strip().split('\n')))

        Job.create(targets=urls, job_type=Job.FETCHABLE, **options)

        return redirect('/jobs/')

    @classmethod
    def standalone(cls):
        folder_name = str(uuid.uuid4())
        media_root = settings.BOTTLE_CONFIG['web.media_root']
        upload_path = os.path.join(media_root, folder_name)

        os.makedirs(upload_path)

        for uploaded_file in request.files.getlist('file[]'):
            uploaded_file.save(upload_path)

        options = {'origin': request.forms.get('origin')}

        Job.create(targets=[upload_path],
                   job_type=Job.STANDALONE,
                   **options)

        return redirect('/jobs/')


@post('/jobs/')
def jobs_create():
    job_type = request.forms.get('type')

    if Job.is_valid_type(job_type):
        return getattr(JobForm, job_type.lower())()

    return jinja2_template('jobs_wizard.html')


@get('/jobs/new/')
def jobs_new():
    job_type = request.query.get('type')
    if Job.is_valid_type(job_type):
        return jinja2_template('jobs_{0}.html'.format(job_type.lower()))

    return jinja2_template('jobs_wizard.html')


@get('/jobs/<job_id:re:[a-zA-Z0-9]+>/tasks/')
@jinja2_view('tasks.html')
def task_list(job_id):
    job = Job.objects.get(job_id=job_id)
    return {'task_list': job.tasks, 'job_id': job_id}
