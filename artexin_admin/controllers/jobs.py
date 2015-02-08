# -*- coding: utf-8 -*-
from bottle import request, get, post, jinja2_view, redirect

from artexin_admin.models import Job


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


@post('/jobs/')
@jinja2_view('jobs_edit.html')
def jobs_create():
    option_names = ('javascript', 'extract')
    options = dict((key, bool(request.forms.get(key))) for key in option_names)

    raw_urls = request.forms.get('urls')
    urls = list(set(url.strip() for url in raw_urls.strip().split('\n')))

    Job.create(urls=urls, **options)

    return redirect('/jobs/')


@get('/jobs/new/')
@jinja2_view('jobs_edit.html')
def jobs_new():
    return {}


@get('/jobs/<job_id:re:[a-zA-Z0-9]+>/tasks/')
@jinja2_view('tasks.html')
def task_list(job_id):
    job = Job.objects.get(job_id=job_id)
    return {'task_list': job.tasks, 'job_id': job_id}
