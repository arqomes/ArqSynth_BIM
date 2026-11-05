"""Propor pontos elétricos (0.145): the storey's rooms, each with its profile (from its name; chosen in a list) and
how many lights, switches, outlets, data and counter outlets it gets (changed in the boxes); «Pré-visualizar» shows
them on the plan, «Aplicar» makes them (one undo step)."""

from PySide6 import QtWidgets

from ..i18n import t
from ..model import electrical_proposal as ep

COUNTS = ("light", "switch", "outlet", "data_outlet", "outlet_counter")


class ElectricalProposalDialog(QtWidgets.QDialog):
    def __init__(self, parent, rooms):
        """rooms: [(GlobalId, name, profile)] — the storey's, their profile as their name says."""
        super().__init__(parent)
        self.setWindowTitle(t("elprop.title"))
        self.on_preview = None          # (profiles, counts) -> None: shows them on the plan
        self.on_apply = None            # (profiles, counts) -> None: makes them
        self.rooms = list(rooms)
        layout = QtWidgets.QVBoxLayout(self)
        intro = QtWidgets.QLabel(t("elprop.intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)
        self.table = QtWidgets.QTableWidget(len(self.rooms), 2 + len(COUNTS))
        self.table.setHorizontalHeaderLabels([t("elprop.room"), t("elprop.profile")]
                                             + [t("elcount." + c) for c in COUNTS])
        self.profiles, self.spins = {}, {}
        for r, (guid, name, profile) in enumerate(self.rooms):
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(name or "—"))
            combo = QtWidgets.QComboBox()
            for key in ep.PROFILES:
                combo.addItem(t("profile." + key), key)
            combo.setCurrentIndex(combo.findData(profile))
            combo.currentIndexChanged.connect(lambda _i, g=guid: self._profile_chosen(g))
            self.table.setCellWidget(r, 1, combo)
            self.profiles[guid] = combo
            for c, key in enumerate(COUNTS):
                spin = QtWidgets.QSpinBox()
                spin.setRange(0, 20)
                spin.setValue(ep.PROFILES[profile][key])
                self.table.setCellWidget(r, 2 + c, spin)
                self.spins[(guid, key)] = spin
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        buttons = QtWidgets.QHBoxLayout()
        self.preview_button = QtWidgets.QPushButton(t("elprop.preview"))
        self.apply_button = QtWidgets.QPushButton(t("elprop.apply"))
        close = QtWidgets.QPushButton(t("elprop.close"))
        self.preview_button.clicked.connect(lambda: self.on_preview and self.on_preview(*self.choices()))
        self.apply_button.clicked.connect(self._apply)
        close.clicked.connect(self.reject)
        buttons.addWidget(self.preview_button)
        buttons.addStretch(1)
        buttons.addWidget(self.apply_button)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.resize(760, 140 + 32 * max(len(self.rooms), 3))

    def _profile_chosen(self, guid):
        """Another profile: its numbers in the boxes."""
        profile = self.profiles[guid].currentData()
        for key in COUNTS:
            self.spins[(guid, key)].setValue(ep.PROFILES[profile][key])

    def choices(self):
        """({room: profile}, {room: {kind: how many}}) as chosen."""
        profiles = {g: combo.currentData() for g, combo in self.profiles.items()}
        counts = {g: {key: self.spins[(g, key)].value() for key in COUNTS} for g, _n, _p in self.rooms}
        return profiles, counts

    def _apply(self):
        if self.on_apply is not None:
            self.on_apply(*self.choices())
        self.accept()
