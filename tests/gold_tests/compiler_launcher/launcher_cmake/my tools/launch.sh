#!/bin/sh
# a launcher whose path has a space in it: tags the compile and hands it to
# the launch.sh next to the sconstruct, which records it
exec "$(dirname "$0")/../launch.sh" --tag spaced "$@"
