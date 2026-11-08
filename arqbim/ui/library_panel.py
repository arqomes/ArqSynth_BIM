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
import shutil

from PySide6 import QtCore, QtGui, QtNetwork, QtWidgets

from ..i18n import decimal_sep, t
from ..model import component_library as lib
from . import component_thumbs

SOURCES = ("project", "local", "web")
WEB_SOURCES = ("polyhaven", "arqsynth", "url")      # (0.467) Poly Haven's free models, the ArqSynth store, an address
LIST_HOURS = 24                                     # (0.467) Poly Haven's list read again after this long
PICTURES_AT_ONCE = 6                                # (0.467) miniatures fetched at the same time
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
        # (web) which catalogue — Poly Haven's free models (0.467), the ArqSynth store (to come), another address —, its
        # categories, where the models come from (as Poly Haven asks), the address
        self.web_box = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(self.web_box)
        v.setContentsMargins(0, 0, 0, 0)
        h = QtWidgets.QHBoxLayout()
        self.web_source = QtWidgets.QComboBox()
        for key in WEB_SOURCES:
            self.web_source.addItem(t("libp.web." + key), key)
        self.web_source.currentIndexChanged.connect(lambda _i: self._web_source_changed())
        self.web_category = QtWidgets.QComboBox()
        self.web_category.setToolTip(t("libp.web_category"))
        self.web_category.currentIndexChanged.connect(lambda _i: self._filter())
        h.addWidget(self.web_source, 1)
        h.addWidget(self.web_category, 1)
        v.addLayout(h)
        self.web_note = QtWidgets.QLabel(t("libp.web_soon"))
        self.web_note.setWordWrap(True)
        self.web_note.setOpenExternalLinks(True)
        self.web_note.setTextFormat(QtCore.Qt.TextFormat.RichText)
        v.addWidget(self.web_note)
        self.web_address_row = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(self.web_address_row)
        h.setContentsMargins(0, 0, 0, 0)
        self.web_address = QtWidgets.QLineEdit()
        self.web_address.setPlaceholderText(t("libp.web_address"))
        self.web_address.returnPressed.connect(self.load_catalogue)
        self.web_connect = QtWidgets.QPushButton(t("libp.web_connect"))
        self.web_connect.clicked.connect(self.load_catalogue)
        h.addWidget(self.web_address, 1)
        h.addWidget(self.web_connect)
        v.addWidget(self.web_address_row)
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
        web = s.value("biblioteca/web_fonte", "polyhaven")
        self.web_source.blockSignals(True)
        self.web_source.setCurrentIndex(max(0, self.web_source.findData(web)))
        self.web_source.blockSignals(False)
        self._pictures_waiting, self._pictures_running = [], 0
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
        self._pictures_waiting = []
        self.where.setVisible(self.source == "local")
        self.web_box.setVisible(self.source == "web")
        self.btn_save.setVisible(self.source == "project")
        web = self.web_source.currentData()
        self.web_address_row.setVisible(web == "url")
        self.web_category.setVisible(web == "polyhaven")
        self.search.setVisible(self.source != "web" or web != "arqsynth")
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

    def _web_source_changed(self):
        _settings().setValue("biblioteca/web_fonte", self.web_source.currentData())
        self.refresh()

    def _fill_web(self):
        web = self.web_source.currentData()
        if web == "arqsynth":
            self.web_note.setText(t("libp.web_soon"))
        elif web == "polyhaven":
            self.load_polyhaven()
        elif not self.web_address.text().strip():
            self.web_note.setText(t("libp.web_address_hint"))
        else:
            self.load_catalogue()

    def _filter(self):
        text = self.search.text().strip().lower()
        category = self.web_category.currentData() if self.source == "web" and self.web_category.isVisibleTo(self) \
            else None
        for k in range(self.list.count()):
            item = self.list.item(k)
            kind = item.data(KIND)
            row = kind[1] if kind and kind[0] == "web" else {}
            hidden = (bool(text) and text not in item.text().lower()
                      and text not in str(row.get("category", "")).lower()) or \
                (bool(category) and row.get("category") != category)
            item.setHidden(hidden)

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
            if kind[1].get("page"):                       # (0.467: its page, where it comes from)
                menu.addAction(t("libp.page"), lambda: QtGui.QDesktopServices.openUrl(QtCore.QUrl(kind[1]["page"])))
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

    @staticmethod
    def _request(url):
        """A request saying which program asks (Poly Haven's API wants it), following redirects."""
        request = QtNetwork.QNetworkRequest(url)
        request.setRawHeader(b"User-Agent", lib.user_agent().encode("ascii"))
        request.setAttribute(QtNetwork.QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QtNetwork.QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy)
        return request

    def _get(self, url, done):
        """`done(bytes or None, error text)` once the address is read (None: it failed)."""
        reply = self._network().get(self._request(url))

        def finished(r=reply):
            ok = r.error() == QtNetwork.QNetworkReply.NetworkError.NoError
            data, error = (bytes(r.readAll()) if ok else None), r.errorString()
            r.deleteLater()
            done(data, error)
        reply.finished.connect(finished)

    def load_catalogue(self):
        """The catalogue at the address given read (its components listed with their miniatures, author, price)."""
        address = self.web_address.text().strip()
        _settings().setValue(lib.CATALOGUE_KEY, address)
        if not address:
            self.web_note.setText(t("libp.web_address_hint"))
            return
        self.web_note.setText(t("libp.web_reading"))
        url = QtCore.QUrl.fromUserInput(address)
        generation = self._generation

        def done(data, error):
            if generation != self._generation or self.source != "web":
                return
            try:
                if data is None:
                    raise ValueError(error)
                name, rows = lib.read_catalogue(data.decode("utf-8", "replace"))
            except (ValueError, TypeError) as exc:
                self.web_note.setText(t("libp.web_failed", e=exc))
                return
            self.web_note.setText(t("libp.web_read", name=name or url.host() or url.toString(), n=len(rows)))
            self._show_rows(rows, url)
        self._get(url, done)

    def load_polyhaven(self):
        """(0.467) Poly Haven's free models listed (its list kept a day on this computer), with its credit."""
        self.web_note.setText(t("libp.polyhaven_credit") + " " + t("libp.web_reading"))
        kept = os.path.join(component_thumbs.cache_dir(), "polyhaven_models.json")
        generation = self._generation

        def show(text):
            try:
                rows = lib.polyhaven_rows(text)
            except (ValueError, TypeError) as exc:
                self.web_note.setText(t("libp.polyhaven_credit") + " " + t("libp.web_failed", e=exc))
                return False
            self.web_note.setText(t("libp.polyhaven_credit") + " " + t("libp.polyhaven_read", n=len(rows)))
            self._show_rows(rows, QtCore.QUrl(lib.POLYHAVEN_SITE))
            return True
        try:
            fresh = os.path.exists(kept) and (QtCore.QDateTime.currentSecsSinceEpoch() - os.path.getmtime(kept)) \
                < LIST_HOURS * 3600
            if fresh:
                with open(kept, encoding="utf-8") as fh:
                    if show(fh.read()):
                        return
        except OSError:
            pass

        def done(data, error):
            if generation != self._generation or self.source != "web":
                return
            if data is None:
                self.web_note.setText(t("libp.polyhaven_credit") + " " + t("libp.web_failed", e=error))
                return
            text = data.decode("utf-8", "replace")
            if show(text):
                try:
                    with open(kept, "w", encoding="utf-8") as fh:
                        fh.write(text)
                except OSError:
                    pass
        self._get(QtCore.QUrl(lib.POLYHAVEN_API + "/assets?type=models"), done)

    def _show_rows(self, rows, base):
        """A catalogue's components listed, their miniatures fetched a few at a time (kept on this computer)."""
        self._base = base
        categories = sorted({r.get("category") for r in rows if r.get("category")}, key=str.lower)
        self.web_category.blockSignals(True)
        self.web_category.clear()
        self.web_category.addItem(t("libp.web_all"), "")
        for c in categories:
            self.web_category.addItem(c.capitalize(), c)
        self.web_category.blockSignals(False)
        for row in rows:                                   # (a price under its name only when it has one)
            text = "{}\n{}".format(row["name"], price_text(row)) if row.get("price") else row["name"]
            item = self._item(text, ("web", row),
                              t("libp.web_info", name=row["name"], author=row.get("author") or "—",
                                licence=row.get("licence") or "—", price=price_text(row)))
            if row.get("thumbnail"):
                self._pictures_waiting.append((self._generation, item, base.resolved(QtCore.QUrl(row["thumbnail"]))))
        self._filter()
        self._next_pictures()

    def _next_pictures(self):
        """The next miniatures fetched — PICTURES_AT_ONCE at a time; one kept on this computer: from there."""
        while self._pictures_waiting and self._pictures_running < PICTURES_AT_ONCE:
            generation, item, url = self._pictures_waiting.pop(0)
            if generation != self._generation:
                continue
            import hashlib
            kept = os.path.join(component_thumbs.cache_dir(),
                                "web_" + hashlib.sha1(url.toString().encode("utf-8")).hexdigest() + ".png")
            pm = QtGui.QPixmap(kept) if os.path.exists(kept) else QtGui.QPixmap()
            if not pm.isNull():
                item.setIcon(QtGui.QIcon(pm))
                continue
            self._pictures_running += 1

            def done(data, _error, item=item, kept=kept, generation=generation):
                self._pictures_running -= 1
                if data is not None and generation == self._generation:
                    picture = QtGui.QPixmap()
                    if picture.loadFromData(data):
                        picture.save(kept, "PNG")
                        item.setIcon(QtGui.QIcon(picture))
                self._next_pictures()
            self._get(url, done)

    def get_web(self, row):
        """A web component: free — fetched into the local library («Web» folder) and brought in; for sale — the store's
        purchase (not open yet). (0.467) A Poly Haven model: its glTF with its binary and textures, in its own folder."""
        if row.get("price"):
            self.info.setText(t("libp.web_buy_soon", name=row["name"], price=price_text(row)))
            return
        if row.get("provider") == "polyhaven":
            self._get_polyhaven(row)
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

    def _get_polyhaven(self, row):
        """(0.467) A Poly Haven model fetched — its glTF at its lightest resolution, with what it needs — into the local
        library (Web ▸ Poly Haven ▸ its name), then brought into the project and placed. Fetched before: from there."""
        folder = os.path.join(self.folder, "Web", "Poly Haven", lib.file_name(row["name"]))
        found = [n for n in os.listdir(folder) if n.lower().endswith(".gltf")] if os.path.isdir(folder) else []
        if found:
            if self.on_bring is not None:
                self.on_bring(os.path.join(folder, found[0]))
            return
        self.info.setText(t("libp.web_getting", name=row["name"]))

        def listed(data, error):
            try:
                if data is None:
                    raise ValueError(error)
                files = lib.polyhaven_files(data.decode("utf-8", "replace"))
                if files is None:
                    raise ValueError(t("libp.polyhaven_no_gltf"))
            except (ValueError, TypeError) as exc:
                self.info.setText(t("libp.web_failed", e=exc))
                return
            main, parts = files
            work = folder + ".parcial"                     # (whole, or not at all: a half-fetched one is not kept)
            shutil.rmtree(work, ignore_errors=True)
            os.makedirs(work, exist_ok=True)
            state = {"left": len(parts), "failed": None}

            named = lib.file_name(row["name"]) + ".gltf"   # (the component named as the catalogue names it)

            def one(rel):
                path = os.path.join(work, named if rel == main else lib.safe_relative(rel))

                def saved(content, err):
                    state["left"] -= 1
                    if content is None:
                        state["failed"] = err
                    else:
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        with open(path, "wb") as fh:
                            fh.write(content)
                    self.info.setText(t("libp.web_getting_n", name=row["name"], n=len(parts) - state["left"],
                                        total=len(parts)))
                    if state["left"]:
                        return
                    if state["failed"] is not None:
                        shutil.rmtree(work, ignore_errors=True)
                        self.info.setText(t("libp.web_failed", e=state["failed"]))
                        return
                    shutil.rmtree(folder, ignore_errors=True)
                    os.replace(work, folder)
                    if self.on_bring is not None:
                        self.on_bring(os.path.join(folder, named))
                return saved
            for rel, address in parts:
                self._get(QtCore.QUrl(address), one(rel))
        self._get(QtCore.QUrl("{}/files/{}".format(lib.POLYHAVEN_API, row["id"])), listed)


def dock(parent):
    """The panel, hidden until the module bar's Library brings it up (the window puts it with the left panels)."""
    panel = LibraryPanel(parent)
    parent.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, panel)
    panel.hide()
    return panel
