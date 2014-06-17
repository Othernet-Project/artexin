"""
index.py: Create word and word-pair indices for given text

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import re

import nltk


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1
__all__ = ('split_sentences', 'split_words', 'get_counts')


WSRE = re.compile(r'\s+')
NONWORD_RE = re.compile(r'^\W+$')


def fix_ws(s):
    """ Strip one or more consecutive whitespace with single blank

    The trailing and leading whitespace will also be removed.

    Example::

        >>> fix_ws('This text contains a tab\\t and two newlines\\n\\n')
        'This text contains a tab and two newlines'

    :param s:   sentence
    :returns:   string with normalized whitespace
    """
    return WSRE.sub(' ', s.strip())


def strip_period(t):
    """ Strip trailing period from a token ``t``

    Example::

        >>> strip_period('sentences.')
        'sentences'
        >>> strip_period('two')
        'two'

    :param t:   string token probably extracted using tokenizers
    :returns:   token with stripped trailing period
    """
    if t[-1] == '.':
        return t[:-1]
    return t


def is_word(t):
    """ Returns ``True`` if token ``t`` is a word (not punctuation)

    This is rather naive test that tests if ``t`` consists of only
    non-alphanumeric characters.

    Example::

        >>> is_word('abracadabra')
        True
        >>> is_word("abr'acadabra")
        True
        >>> is_word('foo:bar')
        True
        >>> is_word(',')
        False
        >>> is_word('...')
        False

    :param t:   string token probably extracted using tokenizers
    :returns:   True if token is a word (not punctuation)
    """
    return NONWORD_RE.match(t) is None


def split_sentences(t, tdata='nltkdata/tokenizers/punkt/english.pickle'):
    """ Split text ``t`` into sentences

    Optional tokenizer data file can be specified. Default is
    'nltkdata/tokenizers/punkt/english.pickle', which is for English texts.

    Example::

        >>> t = "This is a paragraph. It has two sentences."
        >>> list(split_sentences(t))
        ['This is a paragraph.', 'It has two sentences.']

    :param t:       source text

    :param tdata:   tokenizer data file path
    :returns:       iterator of all sentences
    """
    tokenizer = nltk.tokenize.punkt.PunktSentenceTokenizer(tdata)
    return (fix_ws(s) for s in tokenizer.tokenize(t))


def split_words(t, tdata='nltkdata/tokenizers/punkt/english.pickle'):
    """ Splits text ``t`` into words

    Example::

        >>> list(split_words('This is a sample sentence, so to speak.'))
        ['This', 'is', 'a', 'sample', 'sentence', 'so', 'to', 'speak']

    :param t:       source text
    :param tdata:   tokenizer data file path
    :returns:       iterator of all words
    """
    tokenizer = nltk.tokenize.punkt.PunktWordTokenizer()
    tokens = tokenizer.tokenize(t)
    return (strip_period(w) for w in tokens if is_word(w))


def get_counts(sentences):
    """ Obtain term and term-pair counts from sentences iterable

    Example::

        # Load the fixture file
        >>> f = open('../fixtures/sample1.txt')
        >>> text = f.read()
        >>> f.close()

        # First split into sentences
        >>> sentences = split_sentences(text)

        # Feed the sentences to this function
        >>> tc, pc, wc = get_counts(sentences)

        >>> tc['and']
        9
        >>> tc['vitiation']
        1
        >>> pc['the events']
        3
        >>> pc['of working-class']
        1
        >>> wc
        255

        # Get words that appear more than 5 times
        >>> tc = sorted(tc.items(), key=lambda x: (x[1], x[0]), reverse=True)
        >>> [i[0] for i in tc if i[1] > 5]
        ['the', 'of', 'that', 'to', 'and', 'was', 'she']

        # See if some combination of words appear in a text
        >>> pc.get('the events', 0)
        3

    :parm sentences:    iterable containing sentences
    :returns:           tuple of term, term-pair, and word counts
    """
    term_counts = {}  # term_count[term] = count
    pair_counts = {}  # pair_count[term1 + ' ' + term2] = count
    word_count = 0

    for sentence in sentences:
        pterm = None  # previously seen terms
        for term in split_words(sentence):
            term = term.lower()
            word_count += 1
            term_counts.setdefault(term, 0)
            term_counts[term] += 1
            if pterm:
                pkey = '%s %s' % (pterm, term)
                pair_counts.setdefault(pkey, 0)
                pair_counts[pkey] += 1
            pterm = term
    return term_counts, pair_counts, word_count


if __name__ == '__main__':
    import doctest
    doctest.testmod()
