"""
preprocessor_mappings.py: Mappings between URL patterns and preprocessors

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import re

from . import __version__ as _version, __author__ as _author
from .preprocessors import pp_noop, pp_wikipedia, pp_dwelle, pp_fixheaders


__version__ = _version
__author__ = _author
__all__ = ('get_preps',)


DEFAULT_PREPROCESSORS = [pp_noop]

# The mappings are contain two-tuples of regexp patterns and iterables
# containing preprocessors. For every match against URL, preprocessors are
# applied in order. The last set is rigged to be always applied, so please do
# not add any preprocessors after the last set unless you know exactly what you
# are doing. Also, keep the last set minimal.
MAPPINGS = (
    (r'^https?://..\.wikipedia\.org', (pp_wikipedia,)),
    (r'^http://www\.dw\.de/', (pp_dwelle,)),
    (r'.*', (pp_fixheaders,)),
)


def get_preps(url):
    """ Returns a list of preprocessors for given URL

    Example::

        >>> get_preps('http://www.example.com')[0] == pp_fixheaders
        True
        >>> get_preps('http://en.wikipedia.org/')[0] == pp_wikipedia
        True

    :param url:     URL for which to retrieve preprocessors
    :returns:       Returns an interable of preprocessors
    """

    using_preps = ()
    for pattern, preps in MAPPINGS:
        if re.match(pattern, url, re.IGNORECASE):
            using_preps += preps
    return using_preps or DEFAULT_PREPROCESSORS


if __name__ == '__main__':
    import doctest
    doctest.testmod()
