"""
htmlutils.py: manupulate BeautifulSoup HTML document

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from __future__ import unicode_literals, print_function

from bs4 import BeautifulSoup, NavigableString


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1
__all__ = ('get_cls',)


def get_cls(tag):
    """ Get class attribute and default to empty array

    Example::

        >>> html = '<span class="foo bar">baz</span>'
        >>> soup = BeautifulSoup(html)
        >>> get_cls(soup.span)
        ['foo', 'bar']

        >>> html = '<span>baz</span>'
        >>> soup = BeautifulSoup(html)
        >>> get_cls(soup.span)
        []

    """
    return tag.attrs and tag.get('class', []) or []



if __name__ == '__main__':
    import doctest
    doctest.testmod()