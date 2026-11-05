"""Modelo a partir do desenho (0.159 walls; 0.160 openings, furniture and the mapping profile): of a linked DXF, the
layers its walls are drawn on, those of its doors and windows (blocks), those of its furniture (blocks) — ticked
first from the profile kept from the last drawing (the same layer names), else by their names (PAREDE / WALL…,
PORTA / JANELA…, MOBILIÁRIO…) —; the thicknesses to look for, the walls' height. What is found shown in blue on the
plan as the choices change, and counted. OK makes it all (one undo step) and keeps the profile."""

import json
import re

import numpy as np
from PySide6 import QtCore, QtWidgets

from ..core import cad_columns, cad_openings, cad_walls
from ..i18n import decimal_sep, t
from ..model import cad_links as cad_model

LAYER = QtCore.Qt.ItemDataRole.UserRole
WALL_WORDS = re.compile(r"(?i)par(ede)?|wall|muro|alv|tabique|divis")
OPENING_WORDS = re.compile(r"(?i)port|door|jan|win|v[aã]o|caixilh")
FURNITURE_WORDS = re.compile(r"(?i)mob|furn|equip|sanit|loi[cç]|cozinh|kitchen")
COLUMN_WORDS = re.compile(r"(?i)pil|colun|column|estrut")                    # (0.211)
PROFILE_KEY = "dxf/perfil"
ROLES = ("walls", "columns", "openings", "furniture")


def wall_layers(names):
    """The layers whose names say walls."""
    return [n for n in names if WALL_WORDS.search(n)]


def load_profile():
    try:
        data = json.loads(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value(PROFILE_KEY, "") or "{}")
    except (ValueError, TypeError):
        data = {}
    return data if isinstance(data, dict) else {}


def save_profile(profile):
    QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue(PROFILE_KEY, json.dumps(profile, ensure_ascii=False))


class CadWallsDialog(QtWidgets.QDialog):
    def __init__(self, parent, links, show_axes, height):
        """links: the CAD links to choose from; show_axes([(a, b, t)], link, blocks) shows what is found."""
        super().__init__(parent)
        self.setWindowTitle(t("cadwalls.title"))
        self.links, self.show_axes = list(links), show_axes
        self.profile = load_profile()
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("cadwalls.intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        form = QtWidgets.QFormLayout()
        self.drawing = QtWidgets.QComboBox()
        for link in self.links:
            self.drawing.addItem(link.name)
        self.drawing.currentIndexChanged.connect(lambda _i: self._fill_layers())
        form.addRow(t("cadwalls.drawing"), self.drawing)
        row = QtWidgets.QHBoxLayout()
        self.min_t, self.max_t = QtWidgets.QDoubleSpinBox(), QtWidgets.QDoubleSpinBox()
        for box, value in ((self.min_t, self.profile.get("min_t", cad_walls.MIN_T)),
                           (self.max_t, self.profile.get("max_t", cad_walls.MAX_T))):
            box.setRange(0.02, 2.0)
            box.setDecimals(2)
            box.setSingleStep(0.01)
            box.setSuffix(" m")
            box.setValue(float(value))
            box.valueChanged.connect(lambda _v: self.refresh())
        row.addWidget(self.min_t)
        row.addWidget(QtWidgets.QLabel(t("cadwalls.to")))
        row.addWidget(self.max_t)
        form.addRow(t("cadwalls.thickness"), row)
        self.height = QtWidgets.QDoubleSpinBox()
        self.height.setRange(0.5, 50.0)
        self.height.setDecimals(2)
        self.height.setSuffix(" m")
        self.height.setValue(height)
        form.addRow(t("cadwalls.height"), self.height)
        layout.addLayout(form)
        columns = QtWidgets.QHBoxLayout()
        self.lists = {}
        for role in ROLES:
            box = QtWidgets.QVBoxLayout()
            box.addWidget(QtWidgets.QLabel(t("cadwalls.layers_" + role)))
            lst = QtWidgets.QListWidget()
            lst.itemChanged.connect(lambda _i: self.refresh())
            box.addWidget(lst, 1)
            columns.addLayout(box)
            self.lists[role] = lst
        self.layers = self.lists["walls"]                   # (0.159's name for the walls' list)
        layout.addLayout(columns, 1)
        self.found_label = QtWidgets.QLabel()
        self.found_label.setWordWrap(True)
        layout.addWidget(self.found_label)
        self.buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                                  | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self._accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.resize(760, 560)
        self.axes, self.openings, self.furniture = [], [], []
        self._fill_layers()

    def link(self):
        k = self.drawing.currentIndex()
        return self.links[k] if 0 <= k < len(self.links) else None

    def _ticked_first(self, role, names, inserts):
        """The layers ticked to start with for a role: the profile's (those of its names this drawing has), else by
        the layers' names — of the openings and the furniture only layers with blocks."""
        kept = [n for n in self.profile.get(role, ()) if n in names]
        if kept:
            return set(kept)
        if role == "walls":
            return set(wall_layers(names))
        if role == "columns":                               # (0.211: any layer, by its name)
            return {n for n in names if COLUMN_WORDS.search(n)}
        words = OPENING_WORDS if role == "openings" else FURNITURE_WORDS
        return {n for n in names if n in inserts and words.search(n)}

    def _fill_layers(self):
        link = self.link()
        found = cad_model.drawing_of(link.path) if link is not None else None
        names, inserts = [], set()
        if found is not None:
            from ..core import cad
            names = sorted(cad.layers(found[0]))
            inserts = {e.layer for e in found[0].entities if e.kind == "insert"}
        for role, lst in self.lists.items():
            blocker = QtCore.QSignalBlocker(lst)
            lst.clear()
            ticked = self._ticked_first(role, names, inserts)
            for name in names:
                if role not in ("walls", "columns") and name not in inserts:
                    continue                                 # (openings and furniture are blocks)
                item = QtWidgets.QListWidgetItem(name)
                item.setData(LAYER, name)
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.CheckState.Checked if name in ticked else QtCore.Qt.CheckState.Unchecked)
                lst.addItem(item)
            del blocker
        self.refresh()

    def chosen(self, role):
        lst = self.lists[role]
        return [lst.item(k).data(LAYER) for k in range(lst.count())
                if lst.item(k).checkState() == QtCore.Qt.CheckState.Checked]

    def chosen_layers(self):
        return self.chosen("walls")

    def refresh(self):
        """What the layers ticked have: the walls (across the doors' gaps), the doors and windows, the furniture."""
        link = self.link()
        found = cad_model.drawing_of(link.path) if link is not None else None
        self.axes, self.openings, self.furniture = [], [], []
        self.arcs = []                                       # (0.210) the curved walls: (centre, radius, start, sweep, t)
        self.columns = []                                    # (0.211) cad_columns.columns
        self.sized = 0                                       # (0.212) openings with their size written
        if found is not None:
            drawing, raw = found
            walls = set(self.chosen("walls"))
            blocks = cad_openings.instances(drawing, link.place, set(self.chosen("openings")), link.angle)
            self.openings = [(b, cad_openings.kind_of(b) if cad_openings.kind_of(b) in ("door", "window")
                              else ("door" if b.arc else "window")) for b in blocks]
            self.sized = cad_openings.read_sizes(blocks, cad_openings.texts(drawing, link.place))    # (0.212)
            lines = cad_model.wall_lines_of(link.path)      # (0.210: the straight lines and the arcs apart)
            straight, curves = lines if lines is not None else (raw, {})
            segs = [v for k, v in straight.items() if k in walls]
            if segs:
                placed = link.place(np.concatenate(segs))
                self.axes = cad_walls.wall_axes(placed, self.min_t.value(), self.max_t.value(),
                                                blocks=[b for b, _k in self.openings])
            self.arcs = cad_walls.arc_walls([cad_model.place_arc(link, a) for k, v in curves.items() if k in walls
                                             for a in v], self.min_t.value(), self.max_t.value())
            self.furniture = cad_openings.furniture_items(drawing, link.place, link.units,
                                                          set(self.chosen("furniture")), link.angle)
            self.columns = cad_columns.columns(*cad_model.placed_shapes(link, self.chosen("columns")))
        counts = {}
        for th in [w[2] for w in self.axes] + [w[4] for w in self.arcs]:
            counts[round(th * 100, 1)] = counts.get(round(th * 100, 1), 0) + 1
        text = ", ".join("{} × {} cm".format(n, ("{:g}".format(cm)).replace(".", decimal_sep()))
                         for cm, n in sorted(counts.items()))
        doors = sum(1 for _b, k in self.openings if k == "door")
        walls = len(self.axes) + len(self.arcs)
        parts = [t("cadwalls.found", n=walls, t=text) if walls else t("cadwalls.none")]
        if self.arcs:
            parts.append(t("cadwalls.curved", n=len(self.arcs)))
        if self.columns:
            parts.append(t("cadwalls.columns", n=len(self.columns)))
        if self.openings or self.furniture:
            parts.append(t("cadwalls.found_more", d=doors, w=len(self.openings) - doors, f=len(self.furniture)))
            if self.sized:
                parts.append(t("cadwalls.sized", n=self.sized))
        self.found_label.setText(" ".join(parts))
        self.buttons.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(
            bool(self.axes or self.arcs or self.columns or self.furniture))
        if self.show_axes is not None:
            self.show_axes(self.axes, link, [b for b, _k in self.openings], self.arcs, self.columns)

    def _accept(self):
        """The layers chosen kept as the profile for the next drawing."""
        profile = {role: self.chosen(role) for role in ROLES}
        profile.update(min_t=self.min_t.value(), max_t=self.max_t.value())
        save_profile(profile)
        self.accept()
