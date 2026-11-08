"""(0.466) The Library panel — the components with their miniatures, as SketchUp's Components panel (the owner: «Nessa
aba quero uma biblioteca mesmo dos componentes com miniaturas dos componentes assim como no Sketchup. Deve ser feita com
as opções de visualização, biblioteca local e web. No futuro os criadores poderão vender componentes dentro desse
ecossistema»). Not the Project Browser's list again: a grid of pictures.

- On top, where they come from: «No projeto» (the project's components), «Local» (a folder on this computer, its
  subfolders its categories — model/component_library.py), «Web» (a catalogue from an address: the ArqSynth store, when
  it opens — creators publishing and selling their components); how they are shown (small, medium or large miniatures,
  or a list); a search.
- A click on a picture: the component placed with the mouse at once (the owner: «basta clicar no componente ele ativa o
  modelo para ser inserido») — one of the folder's or the web's brought into the project first; a folder opened. «Guardar na biblioteca local»: a project's component kept in the folder for the next projects.
The window does what is asked (on_place, on_bring, on_save, on_select); the miniatures are drawn a few at a time
(ui/component_thumbs.py), kept on disk."""

import os

from PySide6 import QtCore, QtGui, QtNetwork, QtWidgets

from ..i18n import decimal_sep, t
from ..model import component_library as lib
from . import component_thumbs

SOURCES = ("project", "local", "web")
VIEWS = {"small": 56, "medium": 88, "large": 128, "list": 36}
KIND = QtCore.Qt.ItemDataRole.UserRole          # ("project", guid) | ("folder", path) | ("file", path) | ("web", row)
SETTINGS = ("ArqSynth", "ArqSynth BIM")


def _settings():
    return QtCore.QSettings(*SETTINGS)


def price_text(row):
    """A web component's price as written: «Grátis», «12,00 €»."""
    if not row.get("price"):
        return t("libp.free")
    return "{:.2f} {}".format(row["price"], row.get("currency") or "€").replace(".", decimal_sep())


class LibraryPanel(QtWidgets.QDockWidget):
    def __init__(self, parent):
        super().__init__(t("libp.title"), parent)
        self.setObjectName("library")
        body = QtWidgets.QWidget()
        col = QtWidgets.QVBoxLayout(body)
        col.setContentsMargins(4, 4, 4, 4)
        col.setSpacing(4)
        # where from (as SketchUp's «In Model», a local collection, 3D Warehouse) and how shown
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(2)
        self.source_buttons = {}
        group = QtWidgets.QButtonGroup(self)
        group.setExclusive(True)
        for s in SOURCES:
            b = QtWidgets.QToolButton()
            b.setText(t("libp.source." + s))
            b.setToolTip(t("tip.libp.source." + s))
            b.setCheckable(True)
            b.setObjectName("lib_source_" + s)
            b.clicked.connect(lambda _on=False, s=s: self.set_source(s))
            group.addButton(b)
            row.addWidget(b)
            self.source_buttons[s] = b
        row.addStretch(1)
        self.view_button = QtWidgets.QToolButton()
        self.view_button.setText("▦")
        self.view_button.setToolTip(t("libp.view"))
        self.view_button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QtWidgets.QMenu(self.view_button)
        self.view_actions = {}
        views = QtGui.QActionGroup(self)
        for v in VIEWS:
            act = menu.addAction(t("libp.view." + v), lambda v=v: self.set_view(v))
            act.setCheckable(True)
            views.addAction(act)
            self.view_actions[v] = act
        self.view_button.setMenu(menu)
        row.addWidget(self.view_button)
        col.addLayout(row)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(t("libp.search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _text: self._filter())
        col.addWidget(self.search)
        # (local) where in the folder: back up, its name, another folder
        self.where = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(self.where)
        h.setContentsMargins(0, 0, 0, 0)
        self.back = QtWidgets.QToolButton()
        self.back.setText("◀")
        self.back.setToolTip(t("libp.back"))
        self.back.clicked.connect(self.go_up)
        self.path_label = QtWidgets.QLabel()
        self.path_label.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred)
        self.folder_button = QtWidgets.QToolButton()
        self.folder_button.setText(t("libp.folder"))
        self.folder_button.setToolTip(t("tip.libp.folder"))
        self.folder_button.clicked.connect(self.choose_folder)
        h.addWidget(self.back)
        h.addWidget(self.path_label, 1)
        h.addWidget(self.folder_button)
        col.addWidget(self.where)
        # (web) what the store will be, the catalogue's address
        self.web_box = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(self.web_box)
        v.setContentsMargins(0, 0, 0, 0)
        self.web_note = QtWidgets.QLabel(t("libp.web_soon"))
        self.web_note.setWordWrap(True)
        v.addWidget(self.web_note)
        h = QtWidgets.QHBoxLayout()
        self.web_address = QtWidgets.QLineEdit()
        self.web_address.setPlaceholderText(t("libp.web_address"))
        self.web_address.returnPressed.connect(self.load_catalogue)
        self.web_connect = QtWidgets.QPushButton(t("libp.web_connect"))
        self.web_connect.clicked.connect(self.load_catalogue)
        h.addWidget(self.web_address, 1)
        h.addWidget(self.web_connect)
        v.addLayout(h)
        col.addWidget(self.web_box)
        # the miniatures
        self.list = QtWidgets.QListWidget()
        self.list.setObjectName("library_grid")
        self.list.setMovement(QtWidgets.QListView.Movement.Static)
        self.list.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.list.setUniformItemSizes(True)
        self.list.setWordWrap(True)
        self.list.setSpacing(4)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        # (the owner: «basta clicar no componente ele ativa o modelo para ser inserido, não precisa do botão colocar»)
        self.list.itemClicked.connect(self._use)
        self.list.currentItemChanged.connect(lambda item, _old: self._chosen(item))
        self.list.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._menu)
        col.addWidget(self.list, 1)
        # what is chosen
        self.info = QtWidgets.QLabel()
        self.info.setWordWrap(True)
        col.addWidget(self.info)
        h = QtWidgets.QHBoxLayout()
        self.btn_use = QtWidgets.QPushButton(t("libp.place"))       # (a click on the picture does it: kept hidden)
        self.btn_use.clicked.connect(lambda: self._use(self.list.currentItem()))
        self.btn_use.hide()
        self.btn_save = QtWidgets.QPushButton(t("libp.save"))
        self.btn_save.setToolTip(t("tip.libp.save"))
        self.btn_save.clicked.connect(self._save_current)
        h.addWidget(self.btn_use)
        h.addWidget(self.btn_save)
        col.addLayout(h)
        self.setWidget(body)

        # what the window gives and does
        self.project_items = None    # () -> [(type GlobalId, name, copies, placeable)]
        self.project_shape = None    # (type GlobalId) -> (corners (T, 3, 3), sRGB (T, 3))
        self.on_place = None         # (type GlobalId): placed with the mouse
        self.on_bring = None         # (path): a library file's component brought into the project, then placed
        self.on_save = None          # (type GlobalId): kept in the local library (returns the path, or None)
        self.on_select = None        # (type GlobalId): its copies selected

        s = _settings()
        self.source = s.value("biblioteca/fonte", "project")
        self.source = self.source if self.source in SOURCES else "project"
        self.view = s.value("biblioteca/vista", "medium")
        self.view = self.view if self.view in VIEWS else "medium"
        self.folder = s.value("biblioteca/pasta", "") or lib.default_folder()
        self.here = self.folder
        self.web_address.setText(s.value(lib.CATALOGUE_KEY, "") or "")
        self._queue = []
        self._generation = 0
        self._stale = True
        self._rows = None            # the project's components as listed
        self._pictures = {}          # (type GlobalId, size) -> its miniature (the project's: not drawn twice)
        self._net = None
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(0)
        self._timer.timeout.connect(self._next_miniature)
        self.visibilityChanged.connect(lambda shown: self.refresh() if shown and self._stale else None)
        self.source_buttons[self.source].setChecked(True)
        self.view_actions[self.view].setChecked(True)
        self._apply_view()

    # ------------------------------------------------------------ settings

    def set_source(self, source):
        if source not in SOURCES:
            return
        self.source = source
        self.source_buttons[source].setChecked(True)
        _settings().setValue("biblioteca/fonte", source)
        self.refresh()

    def set_view(self, view):
        if view not in VIEWS:
            return
        self.view = view
        self.view_actions[view].setChecked(True)
        _settings().setValue("biblioteca/vista", view)
        self._apply_view()
        self.refresh()

    def _apply_view(self):
        size = VIEWS[self.view]
        if self.view == "list":
            self.list.setViewMode(QtWidgets.QListView.ViewMode.ListMode)
            self.list.setIconSize(QtCore.QSize(size, size))
            self.list.setGridSize(QtCore.QSize())
        else:
            self.list.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
            self.list.setIconSize(QtCore.QSize(size, size))
            self.list.setGridSize(QtCore.QSize(size + 18, size + 36))

    def choose_folder(self):
        """Another folder for the local library (kept for the next sessions)."""
        path = QtWidgets.QFileDialog.getExistingDirectory(self, t("libp.folder"), self.folder)
        if path:
            self.set_folder(path)

    def set_folder(self, path):
        self.folder = self.here = path
        _settings().setValue("biblioteca/pasta", path)
        self.set_source("local")

    def go_up(self):
        if os.path.normcase(os.path.abspath(self.here)) != os.path.normcase(os.path.abspath(self.folder)):
            self.here = os.path.dirname(self.here)
            self.refresh()

    # ------------------------------------------------------------ what is shown

    def mark_stale(self):
        """The project changed: its components listed again — in view, only when they changed (a wall moved: not)."""
        if self.isVisible() and self.source == "project":
            rows = self.project_items() if self.project_items is not None else []
            if rows != self._rows:
                self.refresh()
        else:
            self._stale = True

    def refresh(self):
        self._stale = False
        self._generation += 1
        self._queue = []
        self.list.clear()
        self.info.setText("")
        self.where.setVisible(self.source == "local")
        self.web_box.setVisible(self.source == "web")
        self.btn_save.setVisible(self.source == "project")
        self.search.setVisible(self.source != "web" or bool(self.web_address.text().strip()))
        if self.source == "project":
            self._fill_project()
        elif self.source == "local":
            self._fill_local()
        else:
            self._fill_web()
        self._filter()
        self._chosen(None)
        if self._queue:
            self._timer.start()

    def _item(self, text, kind, tip=""):
        item = QtWidgets.QListWidgetItem(self._blank(), text)
        item.setData(KIND, kind)
        item.setToolTip(tip or text)
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
                              if self.view != "list" else QtCore.Qt.AlignmentFlag.AlignLeft
                              | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.list.addItem(item)
        return item

    def _blank(self):
        size = VIEWS[self.view]
        pm = QtGui.QPixmap(size, size)
        pm.fill(QtGui.QColor(0, 0, 0, 0))
        p = QtGui.QPainter(pm)
        p.setPen(QtGui.QPen(QtGui.QColor(150, 150, 150, 120), 1, QtCore.Qt.PenStyle.DashLine))
        p.drawRoundedRect(QtCore.QRectF(2, 2, size - 4, size - 4), 6, 6)
        p.end()
        return QtGui.QIcon(pm)

    def _fill_project(self):
        rows = self.project_items() if self.project_items is not None else []
        self._rows = rows
        if not rows:
            self.info.setText(t("libp.project_none"))
        for guid, name, copies, placeable in rows:
            item = self._item(name, ("project", guid), t("libp.project_tip", name=name, n=copies))
            if not placeable:
                item.setForeground(QtGui.QBrush(QtGui.QColor("#8a8a8a")))
            self._queue.append((self._generation, item, "project", guid))

    def _fill_local(self):
        try:
            os.makedirs(self.folder, exist_ok=True)
        except OSError:
            pass
        rel = os.path.relpath(self.here, os.path.dirname(self.folder))
        self.path_label.setText(rel.replace(os.sep, " ▸ "))
        self.path_label.setToolTip(self.here)
        self.back.setEnabled(os.path.normcase(os.path.abspath(self.here))
                             != os.path.normcase(os.path.abspath(self.folder)))
        folders, items = lib.listing(self.here)
        folder_icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_DirIcon)
        for name, path in folders:
            item = self._item(name, ("folder", path), t("libp.folder_tip", name=name))
            item.setIcon(folder_icon)
        for name, path, _ext in items:
            item = self._item(name, ("file", path), "{}\n{}".format(name, os.path.basename(path)))
            self._queue.append((self._generation, item, "file", path))
        if not folders and not items:
            self.info.setText(t("libp.local_none", folder=self.here))

    def _fill_web(self):
        if not self.web_address.text().strip():
            self.web_note.setText(t("libp.web_soon"))
            return
        self.load_catalogue()

    def _filter(self):
        text = self.search.text().strip().lower()
        for k in range(self.list.count()):
            item = self.list.item(k)
            item.setHidden(bool(text) and text not in item.text().lower())

    def items(self):
        """What is listed (tests): [(kind, reference, text)]."""
        return [(*self.list.item(k).data(KIND)[:2], self.list.item(k).text()) for k in range(self.list.count())]

    # ------------------------------------------------------------ miniatures, a few at a time

    def _next_miniature(self):
        if not self._queue:
            self._timer.stop()
            return
        generation, item, kind, ref = self._queue.pop(0)
        if generation != self._generation:
            return
        size = max(VIEWS[self.view], 96)
        try:
            if kind == "project":
                pm = self._pictures.get((ref, size))
                if pm is None:
                    shape = self.project_shape(ref) if self.project_shape is not None else None
                    if shape is None or not len(shape[0]):
                        return
                    key = component_thumbs.shape_key(shape[0])
                    pm = component_thumbs.cached(key, lambda: component_thumbs.render(*shape, size=size), size)
                    self._pictures[(ref, size)] = pm
            else:
                def make():
                    shape = lib.item_shape(ref)
                    return component_thumbs.render(*shape, size=size) if shape is not None else None
                pm = component_thumbs.cached(component_thumbs.file_key(ref), make, size)
        except Exception:                                  # (a file that cannot be read: its blank tile)
            return
        if pm is not None and not pm.isNull():
            item.setIcon(QtGui.QIcon(pm))

    def finish_miniatures(self):
        """Every miniature drawn now (tests, an image of the panel)."""
        while self._queue:
            self._next_miniature()
        self._timer.stop()

    # ------------------------------------------------------------ chosen, used

    def _chosen(self, item):
        kind = item.data(KIND) if item is not None else None
        self.btn_use.setEnabled(kind is not None)
        self.btn_save.setEnabled(kind is not None and kind[0] == "project")
        self.btn_use.setText(t("libp.get" if kind is not None and kind[0] == "web" else
                               "libp.open" if kind is not None and kind[0] == "folder" else "libp.place"))
        if kind is None:
            if self.source == "project" and self.list.count():
                self.info.setText(t("libp.project_hint"))
            elif self.source == "local" and self.list.count():
                self.info.setText(t("libp.local_hint"))
            elif self.source == "web":
                self.info.setText("")
            return
        if kind[0] == "project":
            self.info.setText(item.toolTip())
        elif kind[0] == "file":
            self.info.setText(t("libp.file_info", name=item.text(), f=os.path.basename(kind[1])))
        elif kind[0] == "folder":
            self.info.setText(t("libp.folder_tip", name=item.text()))
        else:
            row = kind[1]
            self.info.setText(t("libp.web_info", name=row["name"], author=row.get("author") or "—",
                                licence=row.get("licence") or "—", price=price_text(row)))

    def _use(self, item):
        if item is None:
            return
        kind = item.data(KIND)
        if kind[0] == "project" and self.on_place is not None:
            self.on_place(kind[1])
        elif kind[0] == "folder":
            self.here = kind[1]
            self.refresh()
        elif kind[0] == "file" and self.on_bring is not None:
            self.on_bring(kind[1])
        elif kind[0] == "web":
            self.get_web(kind[1])

    def _save_current(self):
        item = self.list.currentItem()
        kind = item.data(KIND) if item is not None else None
        if kind is not None and kind[0] == "project" and self.on_save is not None:
            self.on_save(kind[1])

    def _menu(self, pos):
        item = self.list.itemAt(pos)
        kind = item.data(KIND) if item is not None else None
        menu = QtWidgets.QMenu(self)
        if kind is not None and kind[0] == "project":
            menu.addAction(t("libp.place"), lambda: self._use(item))
            menu.addAction(t("libp.save"), lambda: self.on_save and self.on_save(kind[1]))
            menu.addAction(t("libp.select_copies"), lambda: self.on_select and self.on_select(kind[1]))
        elif kind is not None and kind[0] in ("file", "folder"):
            menu.addAction(t("libp.open" if kind[0] == "folder" else "libp.place"), lambda: self._use(item))
        elif kind is not None and kind[0] == "web":
            menu.addAction(t("libp.get"), lambda: self._use(item))
        if self.source == "local":
            menu.addSeparator()
            menu.addAction(t("libp.folder"), self.choose_folder)
            menu.addAction(t("libp.refresh"), self.refresh)
        if not menu.isEmpty():
            menu.exec(self.list.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------ the web: a catalogue (the ArqSynth store, when it opens)

    def _network(self):
        if self._net is None:
            self._net = QtNetwork.QNetworkAccessManager(self)
        return self._net

    def load_catalogue(self):
        """The catalogue at the address given read (its components listed with their miniatures, author, price)."""
        address = self.web_address.text().strip()
        _settings().setValue(lib.CATALOGUE_KEY, address)
        if not address:
            self.web_note.setText(t("libp.web_soon"))
            return
        self.web_note.setText(t("libp.web_reading"))
        url = QtCore.QUrl.fromUserInput(address)
        reply = self._network().get(QtNetwork.QNetworkRequest(url))
        generation = self._generation
        reply.finished.connect(lambda r=reply, u=url, g=generation: self._catalogue_read(r, u, g))

    def _catalogue_read(self, reply, base, generation):
        data = bytes(reply.readAll()).decode("utf-8", "replace")
        failed = reply.error() != QtNetwork.QNetworkReply.NetworkError.NoError
        reply.deleteLater()
        if generation != self._generation or self.source != "web":
            return
        try:
            if failed:
                raise ValueError(reply.errorString())
            name, rows = lib.read_catalogue(data)
        except (ValueError, TypeError) as exc:
            self.web_note.setText(t("libp.web_failed", e=exc))
            return
        self.web_note.setText(t("libp.web_read", name=name or base.host() or base.toString(), n=len(rows)))
        self._base = base
        for row in rows:
            item = self._item("{}\n{}".format(row["name"], price_text(row)), ("web", row),
                              t("libp.web_info", name=row["name"], author=row.get("author") or "—",
                                licence=row.get("licence") or "—", price=price_text(row)))
            if row.get("thumbnail"):
                self._get_picture(item, base.resolved(QtCore.QUrl(row["thumbnail"])))
        self._filter()

    def _get_picture(self, item, url):
        reply = self._network().get(QtNetwork.QNetworkRequest(url))
        generation = self._generation

        def done(r=reply):
            data = bytes(r.readAll())
            r.deleteLater()
            if generation != self._generation:
                return
            pm = QtGui.QPixmap()
            if pm.loadFromData(data):
                item.setIcon(QtGui.QIcon(pm))
        reply.finished.connect(done)

    def get_web(self, row):
        """A web component: free — fetched into the local library («Web» folder) and brought in; for sale — the store's
        purchase (not open yet)."""
        if row.get("price"):
            self.info.setText(t("libp.web_buy_soon", name=row["name"], price=price_text(row)))
            return
        url = getattr(self, "_base", QtCore.QUrl()).resolved(QtCore.QUrl(row["file"]))
        ext = os.path.splitext(url.path())[1].lower() or ".ifc"
        if ext not in lib.ITEM_EXTENSIONS:
            self.info.setText(t("libp.web_failed", e=ext))
            return
        folder = os.path.join(self.folder, "Web")
        os.makedirs(folder, exist_ok=True)
        path = lib.free_path(folder, row["name"], ext)
        self.info.setText(t("libp.web_getting", name=row["name"]))
        reply = self._network().get(QtNetwork.QNetworkRequest(url))

        def done(r=reply):
            data = bytes(r.readAll())
            failed = r.error() != QtNetwork.QNetworkReply.NetworkError.NoError
            r.deleteLater()
            if failed or not data:
                self.info.setText(t("libp.web_failed", e=r.errorString()))
                return
            with open(path, "wb") as fh:
                fh.write(data)
            if self.on_bring is not None:
                self.on_bring(path)
        reply.finished.connect(done)


def dock(parent):
    """The panel, hidden until the module bar's Library brings it up (the window puts it with the left panels)."""
    panel = LibraryPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, panel)
    panel.hide()
    return panel
