"""Tabs over the 3D view, one per open view, as in Revit: the 3D view, a storey's plan, a section,
an elevation, a sheet. Clicking a tab shows that view again as it was left (its camera kept);
closing a tab closes that view only — the project stays open. Opening a view that has a tab
shows that tab. One view is drawn at a time: the model's views all use the window's 3D canvas,
the sheets one sheet page. The tabs are saved with the project (state / restore).

A view is named by its key: ("3d",), ("3d", uid) (a named 3D view, 0.64), ("plan", storey
GlobalId), ("section", name), ("elevation", "N" | "S" | "E" | "W"), ("sheet", its uid).

(0.403) The start page is the first tab, always there (the owner: «a página inicial tenha um ícone de home e não seja
uma aba normal que o utilizador possa fechar; ele estará sempre ali logo na primeira, a aba 3D depois dele»): a house,
no name, no ×, not dragged, the other tabs kept after it; not saved with the project, not in Ctrl+Tab's round.
"""

from PySide6 import QtCore, QtWidgets

from ..i18n import t

THREE_D = ("3d",)
START = ("start",)                  # (0.387) the start page: a tab, but not the project's (no camera, not saved)
NO_CAMERA = ("sheet", "start")


class ViewTabs(QtCore.QObject):
    def __init__(self, bar, show, label, camera, set_camera, home_icon=None):
        """bar: the QTabBar. show(key): the window shows that view; label(key): its tab's name;
        camera() / set_camera(state): the view's camera as it is / as it was; home_icon(): the start page's house
        (0.403)."""
        super().__init__(bar)
        self.bar = bar
        self._show, self._label, self._camera, self._set_camera = show, label, camera, set_camera
        self._home_icon = home_icon
        self.keys = []              # per tab, its view
        self.cameras = {}           # view -> its camera when it was left
        self._shown = None          # the view on screen (its camera is kept when another is shown)
        self.on_leave = None        # (view, camera): a view left or closed, as it was (a named 3D view keeps it)
        bar.setTabsClosable(True)
        bar.setMovable(True)
        bar.setDocumentMode(True)
        bar.setExpanding(False)
        bar.setUsesScrollButtons(True)
        bar.setElideMode(QtCore.Qt.TextElideMode.ElideRight)
        bar.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        bar.currentChanged.connect(self._changed)
        bar.tabCloseRequested.connect(self.close)
        bar.tabMoved.connect(lambda a, b: self.keys.insert(b, self.keys.pop(a)))
        bar.customContextMenuRequested.connect(self._menu)
        bar.installEventFilter(self)

    # ------------------------------------------------------------ (0.403) the house, first and fixed

    def _ensure_home(self):
        """The start page's tab, first — added (quietly, not shown) if it is not there."""
        if START in self.keys:
            return
        blocked = self.bar.blockSignals(True)
        self.keys.insert(0, START)
        if self._home_icon is not None:
            self.bar.insertTab(0, self._home_icon(), "")
        else:
            self.bar.insertTab(0, self._label(START))
        self.bar.setTabToolTip(0, self._label(START))
        for side in (QtWidgets.QTabBar.ButtonPosition.LeftSide, QtWidgets.QTabBar.ButtonPosition.RightSide):
            self.bar.setTabButton(0, side, None)             # (no ×)
        self.bar.blockSignals(blocked)

    def _text(self, key):
        """A tab's name as written on it: none for the house (its icon), the view's name for the others."""
        return "" if key == START and self._home_icon is not None else self._label(key)

    def eventFilter(self, obj, event):
        """The house is not dragged (a press on it only shows it); a tab dropped before it goes back after it."""
        if obj is self.bar:
            kind = event.type()
            if kind == QtCore.QEvent.Type.MouseButtonPress and event.button() == QtCore.Qt.MouseButton.LeftButton:
                k = self.bar.tabAt(event.position().toPoint())
                if 0 <= k < len(self.keys) and self.keys[k] == START:
                    self.bar.setCurrentIndex(k)
                    return True
            elif kind == QtCore.QEvent.Type.MouseButtonRelease:
                QtCore.QTimer.singleShot(0, self._pin)
        return False

    def _pin(self):
        """The house back in the first place (a tab was dragged before it)."""
        if START in self.keys and self.keys.index(START) != 0:
            self.bar.moveTab(self.keys.index(START), 0)          # (keys follow: tabMoved)

    def retheme(self):
        """The house in the theme's colours (the theme changed)."""
        if START in self.keys and self._home_icon is not None:
            self.bar.setTabIcon(self.keys.index(START), self._home_icon())

    def models(self):
        """The tabs' views but the start page."""
        return [k for k in self.keys if k != START]

    def current(self):
        k = self.bar.currentIndex()
        return self.keys[k] if 0 <= k < len(self.keys) else None

    def open(self, key):
        """Show a view: its tab if it has one, else a new tab (after the current one — never before the house)."""
        key = tuple(key)
        self._ensure_home()
        if key in self.keys:
            k = self.keys.index(key)
            if k != self.bar.currentIndex():
                self.bar.setCurrentIndex(k)                 # (shown by _changed)
            elif key != self._shown:
                self._enter(key)
            return
        k = max(self.bar.currentIndex() + 1, 1)
        self.keys.insert(k, key)
        self.bar.insertTab(k, self._text(key))              # (the first tab: shown by _changed)
        self.bar.setTabToolTip(k, self._label(key))
        if self.bar.currentIndex() != k:
            self.bar.setCurrentIndex(k)

    def _changed(self, k):
        if 0 <= k < len(self.keys) and self.keys[k] != self._shown:   # (a tab before it closed: the same view)
            self._enter(self.keys[k])

    def _enter(self, key):
        if self._shown is not None and self._shown in self.keys and self._shown[0] not in NO_CAMERA:
            self.cameras[self._shown] = self._camera()      # (as it is left; a sheet, the start page: no camera)
            if self.on_leave is not None:
                self.on_leave(self._shown, self.cameras[self._shown])
        self._shown = key
        self._show(key)
        if key in self.cameras:
            self._set_camera(self.cameras[key])

    def close(self, k):
        """Close a view's tab (not the project). With none left, the 3D view. (0.403) The house is not closed."""
        if not 0 <= k < len(self.keys) or self.keys[k] == START:
            return
        key = self.keys.pop(k)
        camera = self._camera() if key == self._shown and key[0] not in NO_CAMERA else self.cameras.get(key)
        if self.on_leave is not None and camera is not None:
            self.on_leave(key, camera)
        self.cameras.pop(key, None)
        if key == self._shown:
            self._shown = None                              # (its camera is not kept by the tabs)
        self.bar.removeTab(k)                               # (the tab that becomes current is shown)
        if not self.models():
            self.open(THREE_D)

    def close_current(self):
        self.close(self.bar.currentIndex())

    def step(self, n):
        """The next (n = 1) or previous (n = -1) view's tab (0.403: not the house; from it, the first view)."""
        views = [k for k, key in enumerate(self.keys) if key != START]
        if not views:
            return
        k = self.bar.currentIndex()
        if k not in views:
            self.bar.setCurrentIndex(views[0 if n > 0 else -1])
            return
        self.bar.setCurrentIndex(views[(views.index(k) + n) % len(views)])

    def retarget(self, key):
        """The current plan follows another storey (Page Up / Down): its own tab if it has one
        (True: that tab shown); else this tab becomes that storey's plan (False)."""
        key = tuple(key)
        if key in self.keys:
            if self.keys.index(key) != self.bar.currentIndex():
                self.bar.setCurrentIndex(self.keys.index(key))
            return True
        k = self.bar.currentIndex()
        if 0 <= k < len(self.keys) and self.keys[k] != START:
            self.cameras.pop(self.keys[k], None)
            self.keys[k] = self._shown = key
            self.bar.setTabText(k, self._text(key))
            self.bar.setTabToolTip(k, self._label(key))
        return False

    def rename(self, old, new):
        """A view got another name (a section renamed)."""
        old, new = tuple(old), tuple(new)
        if old in self.keys:
            k = self.keys.index(old)
            self.keys[k] = new
            if old in self.cameras:
                self.cameras[new] = self.cameras.pop(old)
            if self._shown == old:
                self._shown = new
            self.bar.setTabText(k, self._text(new))
            self.bar.setTabToolTip(k, self._label(new))

    def refresh(self, exists):
        """Tabs of views that are gone (a storey or section deleted) closed; the names again
        (a storey renamed). exists(key) says if a view is still there."""
        for k in reversed(range(len(self.keys))):
            if self.keys[k] != START and not exists(self.keys[k]):
                self.close(k)
        for k, key in enumerate(self.keys):
            if self.bar.tabText(k) != self._text(key):
                self.bar.setTabText(k, self._text(key))
                self.bar.setTabToolTip(k, self._label(key))

    def reset(self):
        """Another project: the house and the 3D view (shown)."""
        self.bar.blockSignals(True)
        while self.bar.count():
            self.bar.removeTab(0)
        self.bar.blockSignals(False)
        self.keys, self.cameras, self._shown = [], {}, None
        self.open(THREE_D)

    def state(self):
        """The tabs to save with the project: {"tabs": [{"key", "camera"}], "current": key} (JSON)."""
        if self._shown is not None and self._shown[0] not in NO_CAMERA:
            self.cameras[self._shown] = self._camera()
        tabs = []
        for key in self.keys:
            if key == START:                                # (0.387: the program's page, not the project's)
                continue
            cam = self.cameras.get(key)
            tabs.append({"key": list(key), "camera": None if cam is None else {
                "position": [float(c) for c in cam["position"]], "rotation": [float(c) for c in cam["rotation"]],
                "focus": [float(c) for c in cam["focus"]],
                **{name: float(cam[name]) for name in ("fov", "width", "height", "zoom")}}})
        current = self.current() if self.current() != START else None
        return {"tabs": tabs, "current": list(current) if current else None}

    def restore(self, state, exists):
        """The tabs saved with the project (state as read back), those whose views are still there
        (exists(key)); the one that was current shown, as it was."""
        tabs = [tab for tab in (state or {}).get("tabs", ()) if exists(tuple(tab["key"]))]
        if not tabs:
            return False
        self.bar.blockSignals(True)
        while self.bar.count():
            self.bar.removeTab(0)
        self.keys, self.cameras, self._shown = [], {}, None
        self._ensure_home()                                 # (0.403: the house first)
        for tab in tabs:
            key = tuple(tab["key"])
            if key in self.keys:
                continue
            self.keys.append(key)
            self.bar.addTab(self._text(key))
            self.bar.setTabToolTip(len(self.keys) - 1, self._label(key))
            if tab.get("camera"):
                self.cameras[key] = tab["camera"]
        current = tuple(state.get("current") or ())
        k = self.keys.index(current) if current in self.keys else 1
        self.bar.setCurrentIndex(k)
        self.bar.blockSignals(False)
        self._enter(self.keys[k])
        return True

    def _menu(self, pos):
        k = self.bar.tabAt(pos)
        if k < 0 or self.keys[k] == START:                  # (0.403: the house has none — it is not closed)
            return
        menu = QtWidgets.QMenu(self.bar)
        menu.addAction(t("tab.close"), lambda: self.close(k))
        others = menu.addAction(t("tab.close_others"), lambda: self._close_others(self.keys[k]))
        others.setEnabled(len(self.models()) > 1)
        menu.exec(self.bar.mapToGlobal(pos))

    def _close_others(self, key):
        for k in reversed(range(len(self.keys))):
            if self.keys[k] not in (key, START):
                self.close(k)

    def text(self):
        """The views' tabs as shown, the current one marked (used by tests) — (0.403) the house left out."""
        cur = self.bar.currentIndex()
        return " | ".join(("[{}]" if k == cur else "{}").format(self.bar.tabText(k)) for k in range(self.bar.count())
                          if k < len(self.keys) and self.keys[k] != START)
