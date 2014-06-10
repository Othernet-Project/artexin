=======
ArtExIn
=======

ArtExIn is short for Article Extraction and Indexing. It's a set of modules for
fetching HTML pages, extracting relevant articles from it, and indexing the
extracted text.

ArtExIn is developed by `Outernet Inc`_ and it powers the preparation of web
pages for broadcast over the Outernet network.

Developing ArtExIn
==================

To develop ArtExIn, we recommend using Vagrant_. The source code comes with
``Vagrantfile``, which contains definition for a vagrant box we used to develop
the package. We prefer using Vagrant over virtualenv_ because ArtExIn
interfaces with Java and C++ code through its dependencies, so using a full
virtual machine takes care of many cross-platform issues.

Setting up the vagrant box
==========================

After set-up, the root filesystem takes up around 3.5GB on disk, so make sure
you have enough free space.

Make sure Vagrant and VirtualBox are installed. Issue the following commands to
to start the development box::

	vagrant box add ubuntu/trusty64
	vagrant up

Commands should be run from the source directory.

Setting up the box may take a while, depending on your network connections
because the complete corpora of the NLTK_ library is downloaded to the
virtualbox.

Running unit tests
==================

First SSH into the development vagrant box (run ``vagrant up`` if it's not
started yet)::

	vagrant ssh

Run the following command to run the unit tests::

	runtests

The above command simply runs the script in ``scripts/runtests.sh`` (it's just
a symlink).

Alternatively, you can run each ``.py`` file separately. The source code is
located in ``/vagrant`` directory within the virtual machine.


.. _Outernet Inc: https://www.outernet.is/
.. _Vagrant: http://www.vagrantup.com/
.. _virtualenv: http://virtualenv.readthedocs.org/en/latest/
.. _NLTK: http://www.nltk.org/