#!/usr/bin/env bash

BLENDER=$1
[ -z "$BLENDER" ] && BLENDER=blender && [ -z "$(which blender)" ] \
    && echo "error: blender not found: provide path to blender as an argument" && exit 1

PYTHONPATH=$(python3 -c 'import sys; print(*sys.path, sep=":")')

if [ "$(uname)" == "Darwin" ]; then
    # Verbose env for Mac OS X
    alias blender="env -v PYTHONPATH=\":$PYTHONPATH\" $BLENDER"
else
    # Unfortunately Linux doesn't have this flag
    alias blender="env PYTHONPATH=\":$PYTHONPATH\" $BLENDER"
fi
