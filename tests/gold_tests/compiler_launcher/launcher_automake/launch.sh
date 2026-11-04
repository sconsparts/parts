#!/bin/sh
# stand-in for ccache/sccache: record the compile it was asked to run, then run
# it. A leading "--tag NAME" is recorded and dropped, so a test can check that
# a launcher given with arguments reaches the compile whole. CCACHE_DIR is
# recorded when set, so a test can check a quoted value with a space in it
# reached the launcher's environment as one value.
here=$(cd "$(dirname "$0")" && pwd)
tag=""
if [ "$1" = "--tag" ]; then
    tag="[$2] "
    shift 2
fi
echo "$tag${CCACHE_DIR:+[dir=$CCACHE_DIR] }$*" >> "$here/launch.log"
exec "$@"
