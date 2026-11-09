"""(0.327) The Help window (F1, or the «?» of the header): until 0.326 F1 was a list of keys in a message box, and the
owner did not know whether a tool «did not work» or was being used the wrong way (2026-10-31). Four tabs:

- **This tool** — the tool in use: its icon and name, where it is on the ribbon, its step now (whole), its keys and
  what it is for;
- **Find** — every command of the ribbon by its name (or a word of its tip): where it is (Discipline ▸ Panel), and two
  buttons: «Show where» (its tab chosen, its button lit a moment) and «Use»;
- **First steps** — a small house, step by step, clicks written out, each with «Show where»;
- **Keys** — the keys and gestures.

It is a panel of the main window (`MainWindow.show_help`), beside the Properties: it stays beside the work and never
takes the keyboard from it (a window of its own did, in Linux: the next W or R typed went to it)."""

import unicodedata

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import t
from ..i18n import has as i18n_has
from . import ribbon, theme

# (step's text key, the command it shows) — a small house, in the order it is made
FIRST_STEPS = (("help.step.walls", "wall"), ("help.step.slab", "slab"), ("help.step.door", "door"),
               ("help.step.window", "window"), ("help.step.roof", "roof"), ("help.step.room", "room"),
               ("help.step.plan", "plan"), ("help.step.dims", "dimension_walls"),
               ("help.step.sheets", "sheets_by_storey"), ("help.step.pdf", "sheets_pdf"))


def folded(text):
    """Lower case without accents: «Coberturas» found by «cobertura» and by «coberturas»."""
    text = unicodedata.normalize("NFKD", text or "").lower()
    return "".join(c for c in text if not unicodedata.combining(c))


def _names(items):
    return [n for item in items for n in ribbon.names_of(item)]


def where(name):
    """(discipline key or "ctx:walls", panel key) of a command on the ribbon — the first discipline that has it — or
    None."""
    for d in ribbon.DISCIPLINES:
        for panel, items in ribbon.PANELS[d]:
            if name in _names(items):
                return d, panel
    for key, panels in ribbon.CONTEXTS.items():
        for panel, items in panels:
            if name in _names(items):
                return "ctx:" + key, panel
    return None


def where_text(name):
    """«Arquitetura ▸ Paredes» (or «Modificar | Paredes ▸ …» for the contextual tab's)."""
    found = where(name)
    if found is None:
        return ""
    tab, panel = found
    head = t("ctxtab." + tab[4:]) if tab.startswith("ctx:") else t("disc." + tab)
    return "{} ▸ {}".format(head, t("rpanel." + panel))


def dock(win):
    """The Help panel of `win` (the main window), beside its Properties; hidden until F1."""
    panel = QtWidgets.QDockWidget(t("help.title"), win)
    panel.setObjectName("help_dock")
    panel.setWidget(HelpWindow(win, panel))
    win.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, panel)
    win.tabifyDockWidget(win.props, panel)
    panel.hide()
    return panel


class HelpWindow(QtWidgets.QWidget):
    """The Help of `win` (the main window: its commands, tool, ribbon), in its `panel`."""

    def __init__(self, win, panel):
        super().__init__(panel)
        self.win = win
        self.panel = panel
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)
        self.tabs.addTab(self._tool_page(), t("help.tab.tool"))
        self.tabs.addTab(self._find_page(), t("help.tab.find"))
        self.tabs.addTab(self._steps_page(), t("help.tab.steps"))
        self.tabs.addTab(self._keys_page(), t("help.tab.keys"))
        self.restyle()

    def restyle(self):
        """(0.338) Its grey lines in the theme's colours; its icons in the theme's ink."""
        self.tool_where.setStyleSheet("QLabel { color: %s; }" % theme.C["muted"])
        self.found_tip.setStyleSheet("QLabel { color: %s; }" % theme.C["off_text"])
        if self._commands:
            self._commands = []                 # (their icons taken again from the actions)
            self._filter(self.search.text())
        self.refresh_tool()

    # ------------------------------------------------------------ this tool

    def _tool_page(self):
        page = QtWidgets.QWidget()
        box = QtWidgets.QVBoxLayout(page)
        top = QtWidgets.QHBoxLayout()
        self.tool_icon = QtWidgets.QLabel()
        self.tool_icon.setFixedSize(40, 40)
        top.addWidget(self.tool_icon)
        names = QtWidgets.QVBoxLayout()
        self.tool_name = QtWidgets.QLabel()
        self.tool_name.setStyleSheet("QLabel { font-size: 16px; font-weight: 700; }")
        self.tool_where = QtWidgets.QLabel()
        names.addWidget(self.tool_name)
        names.addWidget(self.tool_where)
        top.addLayout(names, 1)
        box.addLayout(top)
        self.tool_text = QtWidgets.QLabel()
        self.tool_text.setWordWrap(True)
        self.tool_text.setTextFormat(QtCore.Qt.TextFormat.RichText)
        self.tool_text.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        box.addWidget(self.tool_text, 1)
        return page

    def refresh_tool(self):
        """The tool in use as it is now — its step, its keys. Select (or a navigation tool): how to select."""
        win = self.win
        tool = win.tool
        name = tool.name if tool is not None else "select"
        act = win.tool_actions.get(name)
        icon = act.icon() if act is not None else QtGui.QIcon()
        self.tool_icon.setPixmap(icon.pixmap(36, 36) if not icon.isNull() else QtGui.QPixmap())
        self.tool_name.setText(t("tool." + name) if i18n_has("tool." + name) else name)
        place = where_text(name)
        self.tool_where.setText(t("help.where", w=place) if place else "")
        parts = [("help.now", win.hint_label.text())]
        if tool is not None and tool.keys_help:
            parts.append(("help.keys", t(tool.keys_help)))
        if act is not None and act.toolTip() and act.toolTip() != act.text():
            parts.append(("help.what", act.toolTip()))
        if name == "select":
            parts.append(("help.what", t("help.select")))
        self.tool_text.setText("".join("<p><b>{}</b><br>{}</p>".format(t(k), _html(v)) for k, v in parts if v))

    # ------------------------------------------------------------ find a command

    def _find_page(self):
        page = QtWidgets.QWidget()
        box = QtWidgets.QVBoxLayout(page)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText(t("help.search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._filter)
        box.addWidget(self.search)
        self.found = QtWidgets.QListWidget()
        self.found.setIconSize(QtCore.QSize(20, 20))
        self.found.itemDoubleClicked.connect(lambda item: self.win.use_command(item.data(QtCore.Qt.ItemDataRole.UserRole)))
        self.found.currentItemChanged.connect(lambda *_a: self._say_found())
        box.addWidget(self.found, 1)
        self.found_tip = QtWidgets.QLabel()
        self.found_tip.setWordWrap(True)
        box.addWidget(self.found_tip)
        row = QtWidgets.QHBoxLayout()
        row.addStretch(1)
        show = QtWidgets.QPushButton(t("help.show"))
        show.clicked.connect(lambda: self._chosen(self.win.show_command))
        use = QtWidgets.QPushButton(t("help.use"))
        use.clicked.connect(lambda: self._chosen(self.win.use_command))
        row.addWidget(show)
        row.addWidget(use)
        box.addLayout(row)
        self._commands = []
        return page

    def _fill_commands(self):
        """Every command on the ribbon, once: (name, label, where, tip, icon, words to find it by)."""
        if self._commands:
            return
        seen = set()
        for tab in list(ribbon.DISCIPLINES) + ["ctx:" + k for k in ribbon.CONTEXTS]:
            for name in ribbon.items_of(tab):
                if name in seen or name in ribbon.MENUS:
                    continue
                item = self.win.ribbon_item(name)
                if item is None:
                    continue
                seen.add(name)
                label = t("tool." + name) if name in self.win.tool_actions else \
                    item.text().split("   (")[0].replace("…", "").strip()
                short = t("rib.short." + name).replace("\n", " ") if i18n_has("rib.short." + name) else ""
                tip = item.toolTip() if item.toolTip() != item.text() else ""
                words = (folded(label + " " + short), folded(where_text(name)), folded(tip))
                self._commands.append((name, label, where_text(name), tip, item.icon(), words))
        self._commands.sort(key=lambda c: folded(c[1]))

    @staticmethod
    def _rank(wanted, words):
        """How well a command answers the words typed: 0 all in its name (1 if its name starts with the first), 2 in
        its name and place, 3 anywhere (its tip too); None: not all of them."""
        name, place, tip = words
        if all(w in name for w in wanted):
            return 0 if not wanted or name.startswith(wanted[0]) else 1
        if all(w in name or w in place for w in wanted):
            return 2
        if all(w in name or w in place or w in tip for w in wanted):
            return 3
        return None

    def _filter(self, text=None):
        self._fill_commands()
        wanted = folded(self.search.text() if text is None else text).split()
        self.found.clear()
        ranked = [(r, c) for c in self._commands for r in [self._rank(wanted, c[5])] if r is not None]
        for _rank, (name, label, place, tip, icon, _words) in sorted(ranked, key=lambda rc: rc[0]):
            item = QtWidgets.QListWidgetItem(icon, "{}   —   {}".format(label, place) if place else label)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, name)
            item.setToolTip(tip)
            self.found.addItem(item)
        if self.found.count():
            self.found.setCurrentRow(0)
        self._say_found()

    def _say_found(self):
        item = self.found.currentItem()
        self.found_tip.setText(item.toolTip() if item is not None else t("help.none_found"))

    def _chosen(self, run):
        item = self.found.currentItem()
        if item is not None:
            run(item.data(QtCore.Qt.ItemDataRole.UserRole))

    def found_names(self):
        """The names of the commands listed now (the tests' way in)."""
        return [self.found.item(i).data(QtCore.Qt.ItemDataRole.UserRole) for i in range(self.found.count())]

    # ------------------------------------------------------------ first steps

    def _steps_page(self):
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(inner)
        grid.setColumnStretch(1, 1)
        intro = QtWidgets.QLabel(t("help.steps_intro"))
        intro.setWordWrap(True)
        grid.addWidget(intro, 0, 0, 1, 3)
        self.step_buttons = []
        for k, (text_key, name) in enumerate(FIRST_STEPS, 1):
            number = QtWidgets.QLabel("{}.".format(k))
            number.setStyleSheet("QLabel { font-weight: 700; }")
            number.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
            text = QtWidgets.QLabel(t(text_key))
            text.setWordWrap(True)
            button = QtWidgets.QPushButton(t("help.show"))
            button.clicked.connect(lambda _=False, n=name: self.win.show_command(n))
            grid.addWidget(number, k, 0)
            grid.addWidget(text, k, 1)
            grid.addWidget(button, k, 2, QtCore.Qt.AlignmentFlag.AlignTop)
            self.step_buttons.append(button)
        grid.setRowStretch(len(FIRST_STEPS) + 1, 1)
        scroll.setWidget(inner)
        return scroll

    # ------------------------------------------------------------ keys

    def _keys_page(self):
        text = QtWidgets.QPlainTextEdit(t("help.text"))
        text.setReadOnly(True)
        self.keys_text = text
        return text

    # ------------------------------------------------------------ shown

    def open_on(self, tab):
        """Shown (or brought up) on a tab: "tool", "find", "steps", "keys"."""
        self.refresh_tool()
        self._filter()
        self.tabs.setCurrentIndex(("tool", "find", "steps", "keys").index(tab))
        self.panel.show()
        self.panel.raise_()                     # (its tab, beside the Properties', in front)
        if tab == "find":
            self.search.setFocus()              # (to type the name at once; on a tool the keyboard stays in the view)


def _html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
