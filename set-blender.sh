#!/usr/bin/env bash

PYTHONPATH=`python3 -c 'import sys; print(*sys.path, sep=":")'`

alias blender="env -v PYTHONPATH=\":$PYTHONPATH\" $1"
