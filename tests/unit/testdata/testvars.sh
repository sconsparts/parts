#!/bin/bash
export ARGTEST=$1
export PATH=`dirname $0`/vc/bin:/opt/foo/a/b/c:/usr/bin/joe/VC/BIN:/usr/bin/jack/Tools:
export INCLUDE="/usr/bin/joe/myinclude/INCLUDE:/opt/foo/INCLUDE:oddvar:::like this"
export LIB=/opt/someplace:/usr/bin/joe/myinclude/LIB:/opt/foo/lib:
export LIBPATH=/opt/someplace:
