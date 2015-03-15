#!/bin/bash
pushd $(dirname $0)
pushd ../..
export PYTHONPATH=$(pwd):$PYTHONPATH
popd
python ../gtest/gtest.py $*
ret=$?
popd
exit $ret
