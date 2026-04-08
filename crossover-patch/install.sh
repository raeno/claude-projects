#!/bin/bash
set -e
CX=/Applications/CrossOver.app/Contents/SharedSupport/CrossOver
SRC=/Users/raeno/dev/claude-projects/crossover-patch/build64/dlls/win32u

sudo cp "$SRC/win32u.so" "$CX/lib/wine/x86_64-unix/win32u.so"
sudo cp "$SRC/x86_64-windows/win32u.dll" "$CX/lib/wine/x86_64-windows/win32u.dll"

echo "Done! Patched win32u installed."
