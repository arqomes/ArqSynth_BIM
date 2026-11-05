#!/bin/bash
# Starts ArqSynth BIM (until 0.76: ArqBIM) in Linux (WSL), its window shown on the Windows desktop by WSLg. Used by ArqBIM.bat.
# The open/save dialogs start in the Windows "Documents" folder; the program's own files (log,
# shapes kept, local copies) are in Linux: ~/ArqSynth BIM, ~/.cache/ArqSynth BIM (until 0.76: ArqBIM).
HERE="$(cd "$(dirname "$0")/.." && pwd)"
docs="$(powershell.exe -NoProfile -Command '[Environment]::GetFolderPath("MyDocuments")' 2>/dev/null | tr -d '\r')"
if [ -n "$docs" ]; then
    export ARQBIM_DOCUMENTS="$(wslpath -u "$docs")"
fi
# the graphics card through WSL: OpenGL on Direct3D 12 (Mesa's d3d12 driver; no Vulkan driver in WSL)
export LD_LIBRARY_PATH="/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export GALLIUM_DRIVER=d3d12
export WGPU_BACKEND_TYPE=OpenGL
export QT_QPA_PLATFORM=xcb          # (Qt through XWayland: the 3D canvas needs an X11 window)
cd "$HERE"
exec /opt/arqbim/venv/bin/python -m arqbim "$@"
