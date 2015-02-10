# -*- coding: utf-8 -*-
from artexin_admin.decorators import registered


@registered('job')
def job_handler(job_data):
    job_id = job_data['id']
    print(job_id)
