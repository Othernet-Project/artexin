"""
batch.py: batch-collecting using multiprocessing

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from __future__ import unicode_literals

import multiprocessing

from . import __version__ as _version, __author__ as _author
from .pack import collect, BASE_DIR
from .preprocessor_mappings import get_preps


__version__ = _version
__author__ = _author
__all__ = ('batch',)


def wrapper(data):
    """ Wrapper for ``pack.collect()`` with alternative argument format

    :param data:    Tuple containing ``pack.collect()`` arguments
    :return:        Results of calling ``pack.collect()``
    """
    url, preps, base_dir, keep_dir = data
    return collect(url, prep=preps, base_dir=base_dir, keep_dir=keep_dir)


def batch(urls, base_dir=BASE_DIR, keep_dir=False, max_procs=None):
    """ Batch-collect URLs using ``pack.collect()``

    :param urls:        Iterable containing URLs to process
    :param base_dir:    Base directory in which to operate
    :param keep_dir:    Keep the directory in which content was collected
    :param max_procs:   Maximum number of processes in the process pool that
                        handles the batch job. Defaults to ``None``, which uses
                        a single process. This corresponds to
                        ``multiprocessing.Pool()`` constructor's ``processes``
                        argument.
    """
    urls = ((u, get_preps(u), base_dir, keep_dir) for u in urls)
    pool = multiprocessing.Pool(max_procs)
    results = pool.map(wrapper, urls)
    pool.close()
    pool.join()
    return results
