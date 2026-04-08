#!/bin/bash
set -e
CX=/Applications/CrossOver.app/Contents/SharedSupport/CrossOver
BK=/Users/raeno/dev/claude-projects/crossover-patch/backup

sudo cp "$BK/win32u.so.orig" "$CX/lib/wine/x86_64-unix/win32u.so"
sudo cp "$BK/win32u.x64.dll.orig" "$CX/lib/wine/x86_64-windows/win32u.dll"

echo "Done! Original win32u restored."
