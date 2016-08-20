#!/bin/bash

# This script build basic install packages
# Clean everything to be safe
python setup.py clean --all
# make zip and tar.bz2 formats as these are generally cross platform
python setup.py sdist --format=zip,bztar
# make a nice windows installer
python setup.py bdist_wininst --user-access-control=auto
# clean everything up.. don't need the tmp files laying around
python setup.py clean --all
