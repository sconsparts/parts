@rem This script build basic install packages
@rem Clean everything to be safe
python setup.py clean --all
@rem make zip and tar.bz2 formats as these are generally cross platform
python setup.py sdist --format=zip,bztar
@rem make a nice windows installer
python setup.py bdist_wininst --user-access-control=auto
@rem clean everything up.. don't need the tmp files laying around
python setup.py clean --all

