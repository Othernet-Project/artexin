"""
htmlutils.py: manupulate BeautifulSoup HTML document

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from . import __version__ as _version, __author__ as _author


__version__ = _version
__author__ = _author
__all__ = ('get_cls',)


def get_cls(tag):
    """ Get class attribute and default to empty array

    Example::

        >>> from bs4 import BeautifulSoup
        >>> html = '<span class="foo bar">baz</span>'
        >>> soup = BeautifulSoup(html)
        >>> get_cls(soup.span)
        ['foo', 'bar']

        >>> from bs4 import BeautifulSoup
        >>> html = '<span>baz</span>'
        >>> soup = BeautifulSoup(html)
        >>> get_cls(soup.span)
        []

    """
    return tag.attrs and tag.get('class', []) or []


if __name__ == '__main__':
    import doctest
    doctest.testmod()
