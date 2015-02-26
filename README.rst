=======
ArtExIn
=======
.. image:: https://travis-ci.org/integricho/artexin.svg
  :target: https://travis-ci.org/integricho/artexin

.. image:: https://coveralls.io/repos/integricho/artexin/badge.svg
  :target: https://coveralls.io/r/integricho/artexin

ArtExIn is short for Article Extraction and Indexing. It's a set of modules for
fetching HTML pages, extracting relevant articles from it, and indexing the
extracted text.

ArtExIn is developed by `Outernet Inc`_ and it powers the preparation of web
pages for broadcast over the Outernet network.

Installation
============

Install artexin using pip::

    pip install git+git://github.com/Outernet-Project/artexin.git

Tests
=====

Execute unittests with::

    python setup.py test

or if you've got tox installed::

    tox

Reporting bugs
==============

Please report all bugs to our `issue tracker`_.

.. _Outernet Inc: https://www.outernet.is/
.. _issue tracker: https://github.com/Outernet-Project/artexin/issues
