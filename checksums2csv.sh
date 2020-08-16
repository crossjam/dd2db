#!/bin/bash
echo "sha256,filename"
awk 'BEGIN { FS="[ \t\n]+\\*?" } {printf "%s,%s\n", $1, $2}' $* | sed 's|/tmp/||'
