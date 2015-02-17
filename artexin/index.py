"""
index.py: Create word and word-pair indices for given text

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import re

import nltk

from . import __version__ as _version, __author__ as _author


__version__ = _version
__author__ = _author
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
        >>> text = '''
        ... It cannot be said that the Everhard Manuscript is an important
        ... historical document. To the historian it bristles with errors--not
        ... errors of fact, but errors of interpretation. Looking back across
        ... the seven centuries that have lapsed since Avis Everhard completed
        ... her manuscript, events, and the bearings of events, that were
        ... confused and veiled to her, are clear to us. She lacked
        ... perspective. She was too close to the events she writes about. Nay,
        ... she was merged in the events she has described.
        ...
        ... Nevertheless, as a personal document, the Everhard Manuscript is of
        ... inestimable value. But here again enter error of perspective, and
        ... vitiation due to the bias of love. Yet we smile, indeed, and
        ... forgive Avis Everhard for the heroic lines upon which she modelled
        ... her husband. We know today that he was not so colossal, and that he
        ... loomed among the events of his times less largely than the
        ... Manuscript would lead us to believe.
        ...
        ... We know that Ernest Everhard was an exceptionally strong man, but
        ... not so exceptional as his wife thought him to be. He was, after
        ... all, but one of a large number of heroes who, throughout the world,
        ... devoted their lives to the Revolution; though it must be conceded
        ... that he did unusual work, especially in his elaboration and
        ... interpretation of working-class philosophy. "Proletarian science"
        ... and "proletarian philosophy" were his phrases for it, and therein
        ... he shows the provincialism of his mind--a defect, however, that was
        ... due to the times and that none in that day could escape.
        ... '''

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
