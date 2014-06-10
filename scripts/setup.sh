#!/usr/bin/env bash

# setup.sh: Prepare vagrant box for testing artexin code
#
# author: 	Outernet Inc <branko@outernet.is>
# version: 	0.1
#


set -e  # Halt on all errors

EI="easy_install -q"
SRCDIR=/vagrant
BINDIR=/usr/local/bin
ARFILE=/var/artexin

# Update local package DB and upgrade installed packages
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y upgrade

# Install build requirements
DEBIAN_FRONTEND=noninteractive apt-get -y install build-essential python \
  python-setuptools python-dev python-lxml libjpeg8 libjpeg8-dev zlib1g \
  zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev tcl8.5-dev tk8.5-dev \
  python-tk

# Setup Python libraries
echo "Installing dependencies"
$EI pip
pip install -r "$SRCDIR/requirements.txt"
pip install -r "$SRCDIR/dev_requirements.txt"

# Install NLTK data files
echo "Installing NLTK corpus data (please be patient)"
python -m nltk.downloader all

echo "Set up scripts"
if [[ ! -f "$BINDIR/runtests" ]]; then
	ln -s $SRCDIR/scripts/runtests.sh /usr/local/bin/runtests
fi

if [[ ! -f "$ARFILE" ]]; then
	echo 'export PATH=$PATH:/usr/local/bin' >> /home/vagrant/.bashrc
	touch "$ARFILE"
fi