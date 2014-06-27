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

YES=1
NO=0

EI="easy_install3 -q"
PY="python3"
PIP="pip"
SRCDIR=/vagrant
CONFPATH="$SRCDIR/conf/artexin.ini"
SCRIPTDIR="$( cd "$( dirname "$0" )" && pwd )"
STATICDIR=/srv/static
ZIPDIR=/srv/zipballs
APPUSER=artexin
NGINXUSER=www-data
NLTKDIR=/usr/share/nltk_data
BINDIR=/usr/local/bin
BINPROF=/etc/profile.d/local_exec.sh
MONGOSRC=/etc/apt/sources.list.d/mongodb.list
PRODUCTION=$NO
QUIET=$NO
RUNTESTS=$YES

usage() {
cat <<EOF
USAGE:
    $0 [-p] [-c PATH] [-h] 

SUMMARY:
    Set up the environment for running ArtExIn.

OPTIONS:
    -p          production box (i.e. not vagrant)
    -c PATH     configuration path
    -h          show usage and quit

NOTES:
    This script expects to be run with root privileges.

    You may need to restart the machine after running this script.

    In production mode (see '-p' swtich) this script will derive the source
    directory location by looking at its own location, assuming that it is
    located in a 'scripts' directory within the source directory. Otherwise, it 
    will assume it's in a vagrant box, and that a shared directory at 
    '/vagrant' points to the source regardless of where the script is located.

    This script has been tested with Ubuntu 14.04LTS 64-bit. Do not expect it 
    to run on anything else.
EOF
}

linkscript() {
    rm "$BINDIR/$1" || true
    ln -s "$SRCDIR/scripts/${1}.sh" "$BINDIR/$1"
}

# Parse command line options
while getopts ":hpc:" option; do
    case "$option" in
    h)
        # Show usage and quit
        usage
        exit 0
        ;;
    p)
        # Override the SRCDIR because this is not a vagrant box
        SRCDIR="$( cd "$SCRIPTDIR" && cd .. && pwd )"
        PRODUCTION=$YES
        RUNTESTS=$NO
        ;;
    c)
        # Override configuration path
        CONFPATH="$OPTARG"
        if [[ ! -f "$CONFPATH" ]]; then
            echo "Configuration file '$CONFPATH' does not exit"
            exit 1
        fi
        ;;
    ?)
        echo "ERROR: invalid option: -$OPTARG"
        echo
        usage
        exit 1
        ;;
    esac
done


###############################################################################
# USERS
###############################################################################

id "$APPUSER" > /dev/null || useradd "$APPUSER"

###############################################################################
# FILESYSTEM
###############################################################################

# Prepare directories
rm -f "$STATICDIR" || true
ln -s "$SRCDIR/artexin_webui/static" "$STATICDIR"

mkdir -p "$ZIPDIR"
chown -R "$NGINXUSER":"$NGINXUSER" "$ZIPDIR"
chmod 775 "$ZIPDIR"

# Set up the runtest script
echo "Set up scripts"
if [[ $RUNTESTS == $YES ]]; then
    linkscript runtests
fi
linkscript startapp


###############################################################################
# PACKAGES
###############################################################################

# Set up MongoDB repo from 10gen
if [[ ! -f "$MONGOSRC" ]]; then
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
    echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' > \
        "$MONGOSRC"
fi

# Update local package DB and upgrade installed packages
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y --force-yes upgrade

# Install build requirements
DEBIAN_FRONTEND=noninteractive apt-get -y --force-yes install build-essential \
    python3 python3-setuptools python3-dev python3-lxml python3-tk \
    python3-imaging phantomjs nginx mongodb-org=2.6.1

# Set up MongoDB from 10gen
apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' > \
    /etc/apt/sources.list.d/mongodb.list


###############################################################################
# LIBRARIES AND DATA FILES
###############################################################################

# Setup Python libraries
echo "Installing dependencies"
$EI pip
$PIP install -r "$SRCDIR/conf/requirements.txt"
$PIP install -r "$SRCDIR/conf/dev_requirements.txt"

# Install NLTK data files
echo "Installing NLTK corpus data (please be patient)"
$PY -m nltk.downloader -d "$NLTKDIR" all


###############################################################################
# SYSTEM SERVICES
###############################################################################

echo "Set up nginx default site"
mv /etc/nginx/sites-available/default /etc/nginx/sites-available/default.orig
ln -s "$SRCDIR/conf/default" /etc/nginx/sites-available/default
service nginx restart || echo "Problem restarting nginx"

# Create and start PhantomJS WebDriver service on port 8910
echo "Set up PhantomJS"
cat > /etc/init/phantom.conf <<EOF
start on started networking
stop on shutdown
exec /usr/bin/phantomjs --webdriver=127.0.0.1:8910
EOF
service phantom restart

if [[ $PRODUCTION == $YES ]]; then
# Create and start application service
echo "Set up ArtExIn application"
cat > /etc/init/artexin.conf <<EOF
start on started phantom
stop on stopping phantom
env PYTHONPATH=$SRCDIR
exec python3 "$SRCDIR/artexin_webui/app.py" -c "$CONFPATH"
EOF
service artexin restart
fi


###############################################################################
# ENVIRONMENT
###############################################################################

# Add /usr/local/bin to vagrant user's PATH
echo 'export PATH=$PATH:/usr/local/bin' > "$BINPROF"

