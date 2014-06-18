#!/usr/bin/env bash

# setup.sh: Prepare vagrant box for testing artexin code
#
# author: 	Outernet Inc <branko@outernet.is>
# version: 	0.1
#
# Copyright 2014, Outernet Inc.
# Some rights reserved.
# 
# This software is free software licensed under the terms of GPLv3. See COPYING
# file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
#


set -e  # Halt on all errors

EI="easy_install3 -q"
PY="python3"
PIP="pip"
SRCDIR=/vagrant
BINDIR=/usr/local/bin
ARFILE=/var/artexin
MONGOSRC=/etc/apt/sources.list.d/mongodb.list

linkscript() {
    if [[ ! -f "$BINDIR/$1" ]]; then
        ln -s "$SRCDIR/scripts/${1}.sh" "$BINDIR/$1"
    fi
}

# Set up MongoDB repo from 10gen
if [[ ! -f "$MONGOSRC" ]]; then
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
    echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' > \
        "$MONGOSRC"
fi

# Update local package DB and upgrade installed packages
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y upgrade

# Install build requirements
DEBIAN_FRONTEND=noninteractive apt-get -y install build-essential python3 \
  python3-setuptools python3-dev python3-lxml python3-tk python3-imaging \
  phantomjs nginx mongodb-org=2.6.1

# Set up MongoDB from 10gen
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | \
    tee /etc/apt/sources.list.d/mongodb.list


# Setup Python libraries
echo "Installing dependencies"
$EI pip
$PIP install -r "$SRCDIR/requirements.txt"
$PIP install -r "$SRCDIR/dev_requirements.txt"

# Install NLTK data files
echo "Installing NLTK corpus data (please be patient)"
$PY -m nltk.downloader all

# Set up the runtest script
echo "Set up scripts"
linkscript runtests
linkscript startapp

# Add /usr/local/bin to vagrant user's PATH
if [[ ! -f "${ARFILE}_0.1" ]]; then
	echo 'export PATH=$PATH:/usr/local/bin' >> /home/vagrant/.bashrc
	touch "${ARFILE}_0.1"
fi

echo "Set up nginx default site"
mv /etc/nginx/sites-available/default /etc/nginx/sites-available/default.orig
ln -s "$SRCDIR/conf/default" /etc/nginx/sites-available/default
service nginx restart

# Create and start PhantomJS WebDriver service on port 8910
echo "Set up PhantomJS"
if [[ ! -f "/etc/init/phantom.conf" ]]; then
cat > /etc/init/phantom.conf <<EOF
start on started networking
stop on shutdown
exec /usr/bin/phantomjs --webdriver=127.0.0.1:8910
EOF
fi
service phantom start
