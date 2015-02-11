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

Make sure Vagrant, VirtualBox and Ansible are installed::

    wget https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2_x86_64.deb
    sudo dpkg -i vagrant_1.7.2_x86_64.deb

    sudo apt-get install virtualbox

    sudo apt-get install software-properties-common
    sudo apt-add-repository ppa:ansible/ansible
    sudo apt-get update
    sudo apt-get install ansible

Issue the following commands to to start the development box::

    vagrant box add ubuntu/trusty64
    vagrant up

Commands should be run from the source directory.

Setting up the box may take a while, depending on your network connections
because the complete corpora of the NLTK_ library is downloaded to the
virtualbox.
By the end of deployment, the web application will be accessible on::

    http://localhost:8080/

To stop the server, SSH into the vagrant VM::

    vagrant ssh
    sudo service circusd stop

Running unit tests
==================

First SSH into the development vagrant box (run ``vagrant up`` if it's not
started yet)::

    vagrant ssh

Run the following command to run the unit tests::

    runtests

The above command simply runs the script in ``scripts/runtests.sh`` (it's just
a symlink).

You cannot run tests for individual modules because they may use relative
imports from different modules in the same package.

Starting the ArtExIn Web UI application
=======================================

The application can be started using the ``startapp`` script from your Vagrant
box. To do this, simply ssh into Vagrant box and type::

    startapp

The configuration settings for the application are located in
``conf/artexin.ini``. These settings are not quite useful generally, so you
will need to modify it. Instead of modifying the configuration in-place, you
should consider creating your own copy. If you create a ``tmp`` directory
within the source tree, it will be ignored by git, so it's a good place to
store your own configuration without complicating source code management.

Copy ``conf/artexin.ini`` to ``tmp/dev.ini`` (or some other file name you want)
and edit anything you wish. Then run the application like so::

    starapp -c /vagrant/tmp/dev.ini

If you want to know what configuration settings are being used, you can do so
by using the ``--debug-conf`` switch::

    starapp -c /vagrant/tmp/dev.ini --debug-conf

This prints out a listing that looks like this::

    {   'artex.directory': '/vagrant',
        'artex.processes': '4',
        'artexin.bind': '127.0.0.1',
        'artexin.database': 'artexinweb',
        'artexin.debug': 'yes',
        'artexin.port': '8080',
        'artexin.server': 'cherrypy',
        'artexin.views': '/vagrant/artexin_webui/views',
        'autojson': True,
        'catchall': True,
        'email.host': 'localhost',
        'email.pass': 'root',
        'email.port': '25',
        'email.sender': 'joe@example.com',
        'email.ssl': 'yes',
        'email.user': 'root'}

Once the application is started, it can be accessed as `on port 8080`_ or
`port 9090`_ on the host machine. The port 8080 is a forwarded nginx listening
at port 80 on the Vagrant box. It only serves the prepared content so you can
inspect the results. The port 9090 serves the actual web UI.

Known issues
============

There are some known issues with the development environment.

Accessing localhost:8080 on host system says host does not exist
----------------------------------------------------------------

Nginx may actually not start correctly when Vagrant box is started. Simply
restart nginx using the following command::

    $ sudo service nginx restart


Reporting bugs
==============

Please report all bugs to our `issue tracker`_.

.. _Outernet Inc: https://www.outernet.is/
.. _Vagrant: http://www.vagrantup.com/
.. _virtualenv: http://virtualenv.readthedocs.org/en/latest/
.. _NLTK: http://www.nltk.org/
.. _issue tracker: https://github.com/Outernet-Project/artexin/issues
.. _on port 8080: http://localhost:8080/
.. _port 9090: http://localhost:9090/
