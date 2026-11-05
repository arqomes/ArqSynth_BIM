#!/bin/bash
# Runs all tests in Linux (WSL), where ArqBIM runs since 2026-10-22. From Windows:
#   wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/BIM/tests/run_tests.sh          core tests (no window)
#   wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/BIM/tests/run_tests.sh --gui    + opens the app and drives it
#   ARQBIM_GUI_ONLY=components,groups  … --gui                                   only those flows of the GUI test
cd "$(dirname "$0")/.."
export LD_LIBRARY_PATH="/usr/lib/wsl/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export GALLIUM_DRIVER=d3d12 WGPU_BACKEND_TYPE=OpenGL QT_QPA_PLATFORM=xcb
py=/opt/arqbim/venv/bin/python
code=0
$py -m unittest discover -s tests || code=1
if [ "$1" = "--gui" ]; then
    $py tests/gui_smoke.py || code=1
fi
exit $code
