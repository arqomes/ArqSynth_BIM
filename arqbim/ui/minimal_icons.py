"""Primary ribbon icons from the approved interface study, coloured with the active palette."""
from PySide6 import QtCore, QtGui, QtSvg
from . import theme

SHAPES = {'select': '<path d="M7 4v22l5-5 4 7 3-2-4-7h7z"/>', 'wall': '<path class="fill" d="M5 26V5h21v7H12v14z"/><path d="M5 26V5h21v7H12v14z"/><path d="M8.5 7.5v15M9 8.5h14" class="detail"/>', 'curtain_wall': '<rect class="fill" x="4" y="5" width="24" height="22" rx="1"/><path d="M4 5h24v22H4zM12 5v22M20 5v22M4 12h24M4 20h24"/>', 'door': '<path class="fill" d="M8 27V5l14-2v24z"/><path d="M6 27h20M8 27V5l14-2v24M18 16h.1"/>', 'window': '<rect class="fill" x="4" y="5" width="24" height="22" rx="1"/><path d="M4 5h24v22H4zM16 5v22M4 16h24"/>', 'slab': '<path class="fill" d="M3 17 16 9l13 6v6l-13 8-13-6z"/><path d="m3 17 13 6 13-8M16 23v6M3 17v6l13 6 13-8v-6L16 9z"/>', 'roof': '<path class="fill" d="M3 21 16 7l13 14z"/><path d="M2 22 16 7l14 15M6 19v7h20v-7M12 26v-7h8v7"/>', 'stair': '<path class="fill" d="M3 27v-5h6v-5h6v-5h6V7h8v20z"/><path d="M3 27v-5h6v-5h6v-5h6V7h8M3 27h26M26 4l3 3-3 3"/>', 'room': '<rect class="fill" x="5" y="5" width="22" height="22" rx="2"/><path d="M5 13V5h8M19 5h8v8M27 19v8h-8M13 27H5v-8M11 13h10M11 18h7"/>'}

def icon(name):
    shape = SHAPES.get(name)
    if shape is None:
        return None
    accent = theme.C["accent"]
    fill = theme._mix(theme.C["bar"], accent, 0.24)
    shape = shape.replace('class="fill"', 'fill="'+fill+'" stroke="none"')
    shape = shape.replace('class="detail"', 'stroke-width="1" opacity="0.65"')
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none" '
           'stroke="'+accent+'" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'+shape+'</svg>')
    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(svg.encode()))
    pm = QtGui.QPixmap(64, 64)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    painter = QtGui.QPainter(pm)
    renderer.render(painter)
    painter.end()
    pm.setDevicePixelRatio(2)
    return QtGui.QIcon(pm)
