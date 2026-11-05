#!/bin/bash
# Prepares Ubuntu 24.04 in WSL to run ArqBIM (2026-10-22: Windows' Smart App Control blocks the
# unsigned libraries of IfcOpenShell, so the program runs in Linux, where it does not look).
# Run as root, from Windows:
#     wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/BIM/scripts/wsl_setup.sh
# Only Ubuntu's own packages (apt) and the same Python packages as on Windows (requirements-lock.txt).
set -e
export DEBIAN_FRONTEND=noninteractive
HERE="$(cd "$(dirname "$0")/.." && pwd)"

apt-get update
# Python; Vulkan through the WSL graphics card (Mesa); what Qt's window needs on Linux (X11 / XWayland)
apt-get install -y --no-install-recommends \
    python3-venv python3-pip \
    mesa-vulkan-drivers vulkan-tools libgl1 libegl1 \
    libxkbcommon-x11-0 libxkbcommon0 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1 libxcb-render-util0 \
    libxcb-shape0 libxcb-xinerama0 libxcb-randr0 libxcb-image0 libxcb-xfixes0 libxcb-sync1 libxcb-shm0 \
    libxcb-util1 libxcb-xkb1 libx11-xcb1 libxrender1 libxi6 libsm6 libice6 \
    libfontconfig1 libfreetype6 libdbus-1-3 libglib2.0-0t64 fonts-dejavu-core \
    libatomic1
# (libatomic1, 0.343: Dr.Jit's — the realistic render's Mitsuba 3)

python3 -m venv /opt/arqbim/venv
/opt/arqbim/venv/bin/pip install --upgrade pip
/opt/arqbim/venv/bin/pip install --no-deps -r "$HERE/requirements-lock.txt"

# the Windows fonts (Segoe UI…) for Qt and the PDFs, as on Windows
mkdir -p /etc/fonts/conf.d
cat > /etc/fonts/conf.d/99-windows-fonts.conf <<'EOF'
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig><dir>/mnt/c/Windows/Fonts</dir></fontconfig>
EOF
fc-cache -f >/dev/null 2>&1 || true
echo "ArqBIM: Linux pronto."
