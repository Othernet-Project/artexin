""" helpers.py: helper function for use with templates """

from . import __version__ as _version, __author__ as _author

__version__ = _version
__author__ = _author
__all__ = ('plur', 'humsize',)

SIZES = 'KMGTP'


def plur(word, n, plural=lambda n: n != 1,
         convert=lambda w, p: w + 's' if p else w):
    """ Pluralize word based on number of items

    This function takes two optional arguments, ``plural`` and ``convert``,
    which can be customized to change the way plural form is derived from the
    original string. The default implementation is a naive version of English
    language plural, which uses plural form if number is not 1, and derives the
    plural form by simply adding 's' to the word. While this works in most
    cases, it doesn't always work even for English.

    The ``plural`` function takes the value of the ``n`` argument and its
    return value is fed into the ``convert`` function. The latter takes the
    source word as first argument, and return value of ``plural()`` call as
    second argument, and returns a string representing the pluralized word.
    Return value of the ``convert()`` call is returned from this function.

    Example::

        >>> plur('book', 1)
        'book'
        >>> plur('book', 2)
        'books'

        # But it's a bit naive
        >>> plur('box', 2)
        'boxs'

    :param word:    string to pluralize
    :param n:       number of items from which to calculate plurals
    :param plural:  function that returns true if the plural form should be
                    used
    :param convert: function that converts the string to plural
    :returns:       word in appropriate form
    """
    return convert(word, plural(n))


def hsize(size, unit='B', step=1024):
    """ Given size in unit produce size with human-friendly units

    Example::

        >>> hsize(12)
        '12 B'
        >>> hsize(1030)
        '1 KB'
        >>> hsize(1536)
        '1.5 KB'
        >>> hsize(2097152)
        '2 MB'

    :param size:    size in base units
    :param unit:    base unit without prefix
    :param step:    steps for next unit (e.g., 1000 for Kilo, or 1024 for Kilo)
    :returns:       appropriate units
    """
    order = -1
    while size > step:
        size /= step
        order += 1
    if order < 0:
        return '%.2f %s' % (size, unit)
    return '%.2f %s%s' % (size, SIZES[order], unit)
