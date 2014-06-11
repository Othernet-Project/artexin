"""
urlutils.py: tools for manipulating URLs

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

from __future__ import unicode_literals, print_function

import re
import urlparse
import itertools


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1
__all__ = ('mask', 'split', 'normalize', 'base_path', 'join', 'absolute_path',
           'is_http_url',)


MULTISLASH = re.compile(r'\/+')
FLIP = lambda x: 1 ^ x  # flips the bit in ``x`` (1 becomes 0, 0 becomes 1)
ROOT_MASK = (1, 1, 0, 0, 0, 0)  # used with urlparse() results
TAIL_MASK = map(FLIP, ROOT_MASK)  # reverse of ROOT_MASK


def mask(iterable, mask, empty=''):
    """ Masks elements in ``iter`` using a iterable of booleans

    For each value ``In`` of iterable ``iterable``, a member of the ``mask``
    iterable with same index ``Mn`` is tested. If ``Mn`` is ``True``, ``In`` is
    kept. Otherwise, it is replaced by ``empty``.

    Example::

        >>> i = [1, 2, 3, 4]
        >>> m = [0, 1, 1, 0]
        >>> e = None
        >>> list(mask(i, m, e))
        [None, 2, 3, None]

        # ``empty`` defaults to empty string
        >>> i = ['foo', 'bar', 'baz']
        >>> m = [0, 0, 1]
        >>> list(mask(i, m))
        [u'', u'', u'baz']

    :param iterable:    Iterable to be masked
    :param mask:        The mask iterable
    :param empty:       The value to be used when mask evaluates to ``False``
                        (default: empty string)
    :return:            Iterator containing masked values
    """
    return itertools.imap(lambda x, y: y if x else empty, mask, iterable)


def split(url):
    """ Splits the path between root (scheme + FQDN) and rest of the URL

    Example::

        >>> split('http://example.com/foo')
        (u'http://example.com', u'/foo')
        >>> split('/foo/bar')
        (u'', u'/foo/bar')
        >>> split('https://user:pwd@www.test.com/foo/bar')
        (u'https://user:pwd@www.test.com', u'/foo/bar')
        >>> split('http://localhost/?foo=bar')
        (u'http://localhost', u'/?foo=bar')
        >>> split('http://localhost/foo?bar=baz')
        (u'http://localhost', u'/foo?bar=baz')

        # FIXME: This example does not work as expected, no idea why
        >>> split('http://localhost?foo=bar')
        (u'http://localhost', u'/?foo=bar')

    :param url:     URL to strip the root from
    :returns:       path with root stripped
    """
    parsed = urlparse.urlparse(url)
    base = urlparse.urlunparse(mask(parsed, ROOT_MASK))
    stripped = urlparse.urlunparse(mask(parsed, TAIL_MASK))
    if stripped[0] != '/':
        return '/' + stripped
    return base, stripped


def normalize(path):
    """ Convert all .. and . to appropriate paths

    Leading double dots are left alone.

    Example::

        >>> normalize('a/../b')
        u'b'
        >>> normalize('/foo/bar/../baz/./fam')
        u'/foo/baz/fam'
        >>> normalize('../foo/bar')
        u'../foo/bar'
        >>> normalize('.././../foo/bar')
        u'../../foo/bar'
        >>> normalize('.././../foo/../bar')
        u'../../bar'

    :param path:    Full path to resource
    :returns:       Normalized path
    """
    comps = path.split('/')
    parts = []
    accumulate_dots = True
    for comp in comps:
        if comp == '..':
            if accumulate_dots:
                parts.append(comp)
            else:
                parts.pop()
        elif comp == '.':
            continue
        else:
            parts.append(comp)
            accumulate_dots = False
    return '/'.join(parts)


def base_path(path):
    """ Get base path of a web resource

    This function treats the path as folder structure and keeps URLs that
    end in ``/`` as they are, stripping anything that appears after the last
    ``/`` except the ``/`` itself.

    Example::

        >>> base_path('/foo/bar/baz/')
        u'/foo/bar/baz/'
        >>> base_path('/foo/bar/baz')
        u'/foo/bar/'
        >>> base_path('/')
        u'/'
        >>> base_path('')
        u'/'
        >>> base_path('foo')
        u'/'
        >>> base_path('foo/bar')
        u'foo/'
        >>> base_path('/foo/bar/../baz')
        u'/foo/'
        >>> base_path('../foo/fam/')
        u'../foo/fam/'

    :param path:    Full path of the resource
    :returns:       The base path
    """
    path = normalize(path)
    comps = path.split('/')
    if comps[-1] != '':
        comps[-1] = ''
    if len(comps) == 1:
        return '/'
    return '/'.join(comps)


def join(path1, path2):
    """ Join two paths and normalize them

    Note that the ``join()`` function is different from Python's standard
    ``posixpath.join()`` in that it always considers ``path2`` as being path
    fragment that needs to be concatenated with ``path1``. This is demonstrated
    by the following example::

        >>> import posixpath
        >>> posixpath.join('foo/bar', '/baz')
        u'/baz'
        >>> join('foo/bar', '/baz')
        u'foo/bar/baz'

    Another notable difference is that ``join()`` takes exactly two arguments,
    whereas ``posixpath.join()`` takes one or more arguments.

    Example::

        >>> join('foo', 'bar')
        u'foo/bar'
        >>> join('foo', '../bar')
        u'bar'
        >>> join('foo/bar', '/baz')
        u'foo/bar/baz'
        >>> join('/', '/foo/bar')
        u'/foo/bar'

    :param path1:   Fragment of a URL path
    :param path2:   Fragment of a URL path
    :returns:       Normalized and concatenated path
    """
    import posixpath
    full = path1 + '/' + path2
    full = MULTISLASH.sub('/', full)
    return normalize(full)


def absolute_path(path, base):
    """ Return absolute path of ``path`` relative to ``base``

    Example::

        >>> absolute_path('foo/bar/', '/')
        u'/foo/bar/'
        >>> absolute_path('../foo1/bar1/baz1', '/foo/bar/baz')
        u'/foo/foo1/bar1/baz1'

    :param path:    Path for which to calculate the absolute path
    :param base:    Path on which the base the calculation
    :returns:       Absolute path
    """
    base = base_path(base)
    return normalize(join(base, path))


def is_http_url(url):
    """ Test if ``url`` represents a full HTTP/HTTPS URL with FQDN

    Example::

        >>> is_http_url('http://www.example.com/')
        True
        >>> is_http_url('http//foobar')
        False
        >>> is_http_url('https://example')
        True
        >>> is_http_url('/foo')
        False
        >>> is_http_url('http://www.example.com/foo')
        True
        >>> is_http_url('//www.example.com')
        True

    :param url:     URL to test
    :returns:       True if URL is full url with scheme and FQDN
    """
    return any([url.startswith(i) for i in ('http://', 'https://', '//')])


def full_url(base, rest):
    """ Merges the base of the URL with rest of it (path, query params, etc)

    If the ``base`` URL contains more than just the scheme and host (e.g.,
    'http://www.example.com/foo/bar/baz') the path and other info will be
    stripped (e.g., '/foo/bar/baz' would be stripped).

    Any missing bits will be replaced by empty string.

    Example::

        >>> full_url('http://example.com', '/foo/bar')
        u'http://example.com/foo/bar'
        >>> full_url('http://example.com/foo', '/foo/bar')
        u'http://example.com/foo/bar'
        >>> full_url('http://example.com', 'foo/bar')
        u'http://example.com/foo/bar'
        >>> full_url('', 'foo/bar')
        u'foo/bar'

    :param base:    Base URL (scheme, domain)
    :param rest:    Rest of the url (path, query params, fragments, etc)
    """
    base = urlparse.urlparse(base)
    rest = urlparse.urlparse(rest)
    return urlparse.urlunparse(base[:2] + rest[2:])


if __name__ == '__main__':
    import doctest
    doctest.testmod()
