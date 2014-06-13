"""
preprocessor_mappings.py: Mappings between URL patterns and preprocessors

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from __future__ import unicode_literals

import re

from preprocessors import *


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1
__all__ = ('get_preps',)


DEFAULT_PREPROCESSORS = [pp_noop]

MAPPINGS = {
    r'^https?://..\.wikipedia\.org': (pp_wikipedia,),
}


def get_preps(url):
    """ Returns a list of preprocessors for given URL

    Example::

        >>> get_preps('http://www.example.com')[0] == pp_noop
        True
        >>> get_preps('http://en.wikipedia.org/')[0] == pp_wikipedia
        True

    :param url:     URL for which to retrieve preprocessors
    :returns:       Returns an interable of preprocessors
    """

    for pattern, preps in MAPPINGS.items():
        if re.match(pattern, url, re.IGNORECASE):
            return preps
    return DEFAULT_PREPROCESSORS


if __name__ == '__main__':
    import doctest
    doctest.testmod()
