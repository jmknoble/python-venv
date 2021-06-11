#!/bin/sh

SCALE=1
THEME=asciinema

for i in *.cast; do
    o="`basename \"${i}\" .cast`.gif"
    (set -x; asciicast2gif -S ${SCALE} -t ${THEME} "${i}" "${o}")
done
