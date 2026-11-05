"""(0.387) The start page — the owner: «vamos criar a página inicial onde à esquerda ficam as opções de abrir novo,
carregar arquivo raiz ou arquivo de base, depois tutoriais, depois documentos recentes. No lado direito duas colunas:
Discussões no GitHub, e outra com nomes de apoiadores e o botão de apoiar».

A tab of the views («Início»), shown when the program starts and from Início ▸ Página inicial; the side panels step
aside while it is in front. Five cards in a row:

- Começar: a new project, a file opened, a new one from a base file (a template: opened, then saved under another
  name) — the base files of the folder «ArqSynth BIM/Arquivos base» in the Documents listed, the folder opened;
- Tutoriais: the program's own guides — Help ▸ First steps, a section of TESTAR.md, GUIA.md — read on the page (0.406;
  a window of their own until 0.405), or a web address; the videos (the YouTube channel);
- Documentos recentes: the files opened and saved last (ui/recent), each with a picture of its view, taken off the
  list with ×; how many are kept;
- Discussões no GitHub, Apoiadores: from assets/start_page.json — their buttons open its addresses (none yet: they say
  so, to be linked).

(0.388, the owner: «a coluna de tutorial passa também para a direita, e a do arquivo recente para a esquerda junto de
abrir… a coluna de arquivos recentes preenche todo o restante espaço, e deve ter opções de visualização») The order is
Começar, Documentos recentes — which takes all the room left — then Tutoriais, Discussões, Apoiadores on the right.
The recent documents are shown as big pictures in a grid, as a list or as details (folder, date, size), in the order
they were used, by name or by date, found by a word; a click opens one, the right button opens its folder or takes it
off the list.

(0.406, the owner: «quando o utilizador pesquisar alguma coisa no tutorial, que se abra logo no lado ocultando as colunas
de discussão e apoio … a sobreposição é apenas temporária. Quando a janela de tutorial for fechada, teremos de novo os 2
painéis na direita») A tutorial is read on the page itself, in the place of the Discussions and the Supporters (until
0.405 the first steps opened the Help panel beside the page, which squeezed all its columns, and the others a window of
their own): its title and ×, a word to find in it, its text — the first steps with «Mostrar onde está» on each. × (or
Esc in its find field) closes it and the two columns come back. The videos: the YouTube channel.

Colours from ui/theme.py only (restyle())."""

import json
import os
import time
import unicodedata

from PySide6 import QtCore, QtGui, QtWidgets

from .. import __version__
from ..i18n import t
from . import brand, links, recent, theme

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))     # (the program's folder)
CONFIG = os.path.join(brand.ASSETS, "start_page.json")
BASE_FOLDER = ("ArqSynth BIM", "Arquivos base")
CARD_MIN_W = 200                    # px: a side card's narrowest and widest (the recent one takes the rest)
CARD_MAX_W = 260
RECENT_MIN_W = 320
SIDE_WEIGHT, RECENT_WEIGHT = 10, 26  # (0.388) how the page's width is shared (the recent ≈ 2,6 side cards, or more)
GRID_PICTURE = QtCore.QSize(176, 110)       # (0.388) a recent document's picture in the grid, in the list
LIST_PICTURE = QtCore.QSize(64, 40)
PATH_ROLE = QtCore.Qt.ItemDataRole.UserRole
# (0.406) the tutorial read on the page: the room of the two columns it covers (and a little more on a wide screen)
READER_MIN_W = 2 * CARD_MIN_W + 14
READER_MAX_W = 760
READER_WEIGHT = 2 * SIDE_WEIGHT


def config():
    """The page's addresses and lists (assets/start_page.json)."""
    try:
        with open(CONFIG, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    for key in ("tutorials", "discussions", "supporters"):
        data.setdefault(key, [])
    for key in ("videos_url", "discussions_url", "support_url"):
        data.setdefault(key, "")
    return data


def base_folder(documents):
    return os.path.join(documents or os.path.expanduser("~"), *BASE_FOLDER)


def base_files(documents):
    """The base files (.ifc) in the base folder, by name."""
    folder = base_folder(documents)
    try:
        names = sorted(n for n in os.listdir(folder) if n.lower().endswith(".ifc"))
    except OSError:
        return []
    return [os.path.join(folder, n) for n in names]


def testar_section(version):
    """The steps of a version in TESTAR.md (its «## 0.380 — …» section), or ""."""
    try:
        with open(os.path.join(ROOT, "TESTAR.md"), encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return ""
    head = "\n## {} ".format(version)
    at = text.find(head)
    if at < 0:
        return ""
    end = text.find("\n## ", at + len(head))
    return text[at + 1:end if end > 0 else len(text)].strip()


def doc_text(name):
    try:
        with open(os.path.join(ROOT, os.path.basename(name)), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _size_text(size):
    """A file's size for people: «850 kB», «12,4 MB»."""
    if size < 1024 * 1024:
        return "{} kB".format(max(1, round(size / 1024)))
    return "{:.1f} MB".format(size / (1024 * 1024)).replace(".", ",")


class _Row(QtWidgets.QFrame):
    """A line of a list that is clicked (a tutorial, a recent file, a discussion)."""

    def __init__(self, on_click=None, tip=""):
        super().__init__()
        self.setObjectName("start_row")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_Hover, on_click is not None)
        self.on_click = on_click
        if on_click is not None:
            self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        if tip:
            self.setToolTip(tip)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if self.on_click is not None and event.button() == QtCore.Qt.MouseButton.LeftButton and \
                self.rect().contains(event.position().toPoint()):
            self.on_click()
        super().mouseReleaseEvent(event)


def _fold(text):
    """(0.406) Lower case without accents, letter for letter — the same length, so a place found in it is that place
    in the text: «cobertura» finds «Cobertura» and «cobertúra»."""
    out = []
    for c in text:
        base = unicodedata.normalize("NFKD", c)[:1] or c
        out.append(base.lower()[:1] or base)
    return "".join(out)


def _html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")


class TutorialPane(QtWidgets.QFrame):
    """(0.406) A tutorial read on the start page, in the place of the Discussions and the Supporters: its title and ×,
    a word to find in it (every place lit, the one in front stronger; Enter the next, Shift+Enter the one before, Esc
    clears the word or closes), its text. Its links: «Mostrar onde está» (show:<command>), a place in it (#…), a web
    address (the browser)."""

    MOST_LIT = 400                          # (places lit at once; a letter typed alone finds thousands)

    def __init__(self, on_close, on_show):
        super().__init__()
        self.setObjectName("start_card")
        self.setMinimumWidth(READER_MIN_W)
        self.setMaximumWidth(READER_MAX_W)
        self.on_close, self.on_show = on_close, on_show
        self.key = None                     # (the tutorial shown: its «open», "help:steps", "testar:0.380"…)
        self._shown = None                  # (how it was made: ("steps", title) or ("text", title, markdown))
        self._hits, self._at, self._length = [], -1, 0
        box = QtWidgets.QVBoxLayout(self)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(8)
        top = QtWidgets.QHBoxLayout()
        top.setSpacing(6)
        self.head = QtWidgets.QLabel()
        self.head.setObjectName("start_title")
        self.head.setWordWrap(True)
        top.addWidget(self.head, 1)
        self.close_button = QtWidgets.QToolButton()
        self.close_button.setObjectName("start_close")
        self.close_button.setText("×")
        self.close_button.setToolTip(t("start.tutorial_close"))
        self.close_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.close_button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.close_button.clicked.connect(lambda _=False: self.on_close())
        top.addWidget(self.close_button, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        box.addLayout(top)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(4)
        self.find = QtWidgets.QLineEdit()
        self.find.setObjectName("start_find")
        self.find.setPlaceholderText(t("start.tutorial_find"))
        self.find.setClearButtonEnabled(True)
        self.find.textChanged.connect(lambda _text: self.look())
        self.find.installEventFilter(self)
        row.addWidget(self.find, 1)
        self.hits_label = QtWidgets.QLabel()
        self.hits_label.setObjectName("start_muted")
        row.addWidget(self.hits_label)
        self.prev_button = self._arrow("▲", t("start.tutorial_prev"), -1)
        self.next_button = self._arrow("▼", t("start.tutorial_next"), 1)
        row.addWidget(self.prev_button)
        row.addWidget(self.next_button)
        box.addLayout(row)
        self.view = QtWidgets.QTextBrowser()
        self.view.setObjectName("start_reader")
        self.view.setOpenLinks(False)
        self.view.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.view.anchorClicked.connect(self._link)
        box.addWidget(self.view, 1)
        self._say_hits()
        self.hide()

    def _arrow(self, glyph, tip, step):
        b = QtWidgets.QToolButton()
        b.setObjectName("start_step")
        b.setText(glyph)
        b.setToolTip(tip)
        b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        b.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        b.clicked.connect(lambda _=False: self.step(step))
        return b

    # ------------------------------------------------------------ what it shows

    def show_steps(self, key, title):
        """The first steps of a small house (those of Help ▸ First steps), each with «Mostrar onde está»."""
        self._shown = ("steps", title)
        self.key = key
        self.head.setText(title)
        self.view.setHtml(self._steps_html())
        self._from_top()

    def show_text(self, key, title, text):
        """A guide's text (Markdown): a section of TESTAR.md, GUIA.md."""
        self._shown = ("text", title, text)
        self.key = key
        self.head.setText(title)
        self.view.setMarkdown(text)
        self._from_top()

    @staticmethod
    def _steps_html():
        from .help_window import FIRST_STEPS
        link = theme.C["select"]
        parts = ["<p>{}</p>".format(_html(t("help.steps_intro")))]
        for k, (text_key, name) in enumerate(FIRST_STEPS, 1):
            parts.append('<p style="margin-top:10px;"><b>{}.</b>&nbsp; {}<br><a href="show:{}" style="color:{};'
                         ' text-decoration:none; font-weight:600;">▸ {}</a></p>'.format(
                             k, _html(t(text_key)), name, link, _html(t("help.show"))))
        return "".join(parts)

    def _from_top(self):
        self.view.verticalScrollBar().setValue(0)
        self.look()

    def restyle(self):
        """The first steps' links in the theme's colour; the places found lit again in it."""
        if self._shown is not None and self._shown[0] == "steps":
            at = self.view.verticalScrollBar().value()
            self.view.setHtml(self._steps_html())
            self.view.verticalScrollBar().setValue(at)
        self._paint(scroll=False)

    def _link(self, url):
        if url.scheme() == "show":
            if self.on_show is not None:
                self.on_show(url.path())
            return
        text = url.toString()
        if text.startswith("#"):
            self.view.scrollToAnchor(text[1:])
            return
        links.open_url(text)

    # ------------------------------------------------------------ a word found in it

    def look(self):
        """Every place of the word typed (without accents, any case); the first in front."""
        wanted = _fold(self.find.text().strip())
        self._hits, self._length = [], len(wanted)
        if wanted:
            hay = _fold(self.view.document().toPlainText())
            at = hay.find(wanted)
            while at >= 0:
                self._hits.append(at)
                at = hay.find(wanted, at + len(wanted))
        self._at = 0 if self._hits else -1
        self._paint()

    def step(self, by):
        """The next place found (by=1) or the one before (-1), round."""
        if self._hits:
            self._at = (self._at + by) % len(self._hits)
            self._paint()

    def _paint(self, scroll=True):
        doc = self.view.document()
        soft, strong = QtGui.QColor(theme.C["target"]), QtGui.QColor(theme.C["select"])
        ink = QtGui.QColor(theme.C["select_text"])
        lit = []
        shown = set(range(min(len(self._hits), self.MOST_LIT)))
        if self._at >= 0:
            shown.add(self._at)
        for k in sorted(shown):
            sel = QtWidgets.QTextEdit.ExtraSelection()
            cursor = QtGui.QTextCursor(doc)
            cursor.setPosition(self._hits[k])
            cursor.setPosition(self._hits[k] + self._length, QtGui.QTextCursor.MoveMode.KeepAnchor)
            sel.cursor = cursor
            fmt = QtGui.QTextCharFormat()
            fmt.setBackground(strong if k == self._at else soft)
            if k == self._at:
                fmt.setForeground(ink)
            sel.format = fmt
            lit.append(sel)
        self.view.setExtraSelections(lit)
        if scroll and self._at >= 0:
            cursor = QtGui.QTextCursor(doc)
            cursor.setPosition(self._hits[self._at] + self._length)
            self.view.setTextCursor(cursor)
            self.view.ensureCursorVisible()
        self._say_hits()

    def _say_hits(self):
        n = len(self._hits)
        if n:
            self.hits_label.setText(t("start.tutorial_hits", n=self._at + 1, m=n))
        else:
            self.hits_label.setText(t("start.tutorial_none_found") if self.find.text().strip() else "")
        for b in (self.prev_button, self.next_button):
            b.setEnabled(n > 1)

    def hits(self):
        """How many places the word was found in (the tests' way in)."""
        return len(self._hits)

    def eventFilter(self, obj, event):  # noqa: N802
        """In the find field: Enter the next place, Shift+Enter the one before; Esc clears the word, or (none) closes."""
        if obj is self.find:
            kind = event.type()
            if kind == QtCore.QEvent.Type.ShortcutOverride and event.key() == QtCore.Qt.Key.Key_Escape:
                event.accept()                  # (Esc is the find field's here, not the window's «Selecionar»)
                return True
            if kind == QtCore.QEvent.Type.KeyPress:
                if event.key() == QtCore.Qt.Key.Key_Escape:
                    if self.find.text():
                        self.find.clear()
                    else:
                        self.on_close()
                    return True
                if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
                    self.step(-1 if event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier else 1)
                    return True
        return super().eventFilter(obj, event)


class StartPage(QtWidgets.QWidget):
    def __init__(self, parent, documents):
        super().__init__(parent)
        self.setObjectName("start_page")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.documents = documents
        self.on_new = self.on_open = self.on_open_path = self.on_base = None
        self.on_help = self.on_message = self.on_show = None
        self._tutorial_rows = []            # (0.406) (its tutorial, its line) — the one being read marked
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(24, 18, 24, 18)
        outer.setSpacing(16)
        outer.addLayout(self._brand())
        cards = QtWidgets.QHBoxLayout()
        cards.setSpacing(14)
        self.start_card = self._card(t("start.begin"))
        self.recent_card = self._recent_card()
        self.tutorials_card = self._card(t("start.tutorials"))
        self.discussions_card = self._card(t("start.discussions"))
        self.supporters_card = self._card(t("start.supporters"))
        # (0.388) Começar and the recent documents (all the room left) on the left; the tutorials, the discussions and
        # the supporters on the right. Shared by weight: a side card 10 (between CARD_MIN_W and CARD_MAX_W), the
        # recent documents 26 — and all that the side cards cannot take
        cards.addWidget(self.start_card, SIDE_WEIGHT)
        cards.addWidget(self.recent_card, RECENT_WEIGHT)
        for card in (self.tutorials_card, self.discussions_card, self.supporters_card):
            cards.addWidget(card, SIDE_WEIGHT)
        # (0.406) the tutorial read here, in the place of the Discussions and the Supporters while it is open
        self.reader = TutorialPane(self.close_tutorial, lambda name: self._call("on_show", name))
        cards.addWidget(self.reader, READER_WEIGHT)
        outer.addLayout(cards, 1)
        self.refresh()
        self.restyle()

    # ------------------------------------------------------------ the pieces

    def _brand(self):
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(12)
        mark = brand.symbol(46)
        if mark is not None:
            icon = QtWidgets.QLabel()
            icon.setPixmap(mark)
            row.addWidget(icon)
        names = QtWidgets.QVBoxLayout()
        names.setSpacing(0)
        self.title = QtWidgets.QLabel()
        self.title.setObjectName("start_brand")
        self.title.setTextFormat(QtCore.Qt.TextFormat.RichText)
        names.addWidget(self.title)
        self.subtitle = QtWidgets.QLabel(t("start.tagline", v=__version__))
        self.subtitle.setObjectName("start_muted")
        names.addWidget(self.subtitle)
        row.addLayout(names)
        row.addStretch(1)
        return row

    def _card(self, title):
        card = QtWidgets.QFrame()
        card.setObjectName("start_card")
        card.setMinimumWidth(CARD_MIN_W)
        card.setMaximumWidth(CARD_MAX_W)
        box = QtWidgets.QVBoxLayout(card)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(8)
        head = QtWidgets.QLabel(title)
        head.setObjectName("start_title")
        head.setWordWrap(True)                      # (0.388) a long title in two lines on a narrow screen
        box.addWidget(head)
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QtWidgets.QWidget()
        inner.setObjectName("start_inner")
        body = QtWidgets.QVBoxLayout(inner)
        body.setContentsMargins(0, 0, 4, 0)
        body.setSpacing(6)
        scroll.setWidget(inner)
        box.addWidget(scroll, 1)
        foot = QtWidgets.QVBoxLayout()
        foot.setSpacing(6)
        box.addLayout(foot)
        card.body, card.foot = body, foot
        return card

    @staticmethod
    def _clear(layout):
        """A list's pieces taken away — hidden at once: until Qt deletes them they stayed on the page, some (never laid
        out) at Qt's first size over the cards."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()
                item.widget().deleteLater()
            elif item.layout() is not None:
                StartPage._clear(item.layout())
                item.layout().deleteLater()

    def _button(self, text, slot, name="start_button", tip=""):
        b = QtWidgets.QPushButton(text)
        b.setObjectName(name)
        b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        b.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        if tip:
            b.setToolTip(tip)
        b.clicked.connect(lambda _=False: slot())
        return b

    def _note(self, text):
        label = QtWidgets.QLabel(text)
        label.setObjectName("start_muted")
        label.setWordWrap(True)
        return label

    def _text_row(self, title, text, on_click, tip=""):
        row = _Row(on_click, tip)
        box = QtWidgets.QVBoxLayout(row)
        box.setContentsMargins(8, 6, 8, 6)
        box.setSpacing(2)
        head = QtWidgets.QLabel(title)
        head.setObjectName("start_row_title")
        head.setWordWrap(True)
        box.addWidget(head)
        if text:
            line = QtWidgets.QLabel(text)
            line.setObjectName("start_row_text")
            line.setWordWrap(True)
            box.addWidget(line)
        return row

    def _say(self, text):
        if self.on_message is not None:
            self.on_message(text)

    def _open_link(self, url, what):
        if not links.open_url(url):
            self._say(t("start.not_linked", what=what))

    # ------------------------------------------------------------ the lists, made again

    def refresh(self):
        """The cards' lists as they are now (the recent files, the base files, the page's file)."""
        data = config()
        self._fill_start()
        self._fill_tutorials(data)
        self._fill_recent()
        self._fill_discussions(data)
        self._fill_supporters(data)
        self._fit_cards()

    def _fit_cards(self):
        """(0.388) A side card never narrower than what it holds (a button's words): its scroll area would cut it
        on the right. Between CARD_MIN_W and CARD_MAX_W."""
        for card in (self.start_card, self.tutorials_card, self.discussions_card, self.supporters_card):
            inner = card.body.parentWidget()
            need = max(inner.minimumSizeHint().width() + 12,      # (room for its scroll bar)
                       card.foot.minimumSize().width()) + 28        # (the card's margins)
            card.setMinimumWidth(int(min(CARD_MAX_W, max(CARD_MIN_W, need))))

    def _call(self, name, *args):
        slot = getattr(self, name)
        if slot is not None:
            slot(*args)

    def _fill_start(self):
        body, foot = self.start_card.body, self.start_card.foot
        self._clear(body)
        self._clear(foot)
        body.addWidget(self._button(t("start.new"), lambda: self._call("on_new"), "start_primary",
                                    t("tip.new")))
        body.addWidget(self._button(t("start.open"), lambda: self._call("on_open"), tip=t("tip.open")))
        body.addWidget(self._button(t("start.from_base"), lambda: self._call("on_base", None),
                                    tip=t("tip.new_from_base")))
        body.addSpacing(8)
        head = QtWidgets.QLabel(t("start.base_files"))
        head.setObjectName("start_row_title")
        body.addWidget(head)
        files = base_files(self.documents)
        for path in files:
            body.addWidget(self._text_row(os.path.splitext(os.path.basename(path))[0], "",
                                          lambda p=path: self._call("on_base", p), t("start.base_tip", f=path)))
        if not files:
            body.addWidget(self._note(t("start.base_none")))
        body.addStretch(1)
        foot.addWidget(self._button(t("start.base_folder"), lambda: links.open_folder(base_folder(self.documents)),
                                    tip=base_folder(self.documents)))

    def _fill_tutorials(self, data):
        body, foot = self.tutorials_card.body, self.tutorials_card.foot
        self._clear(body)
        self._clear(foot)
        self._tutorial_rows = []
        for item in data["tutorials"]:
            row = self._text_row(str(item.get("title", "")), str(item.get("text", "")),
                                 lambda it=item: self.open_tutorial(it))
            body.addWidget(row)
            self._tutorial_rows.append((item, row))
        self._mark_tutorial()
        body.addStretch(1)
        foot.addWidget(self._button(t("start.videos"), lambda: self._open_link(config()["videos_url"],
                                                                                t("start.videos")), "start_red",
                                    t("start.videos_tip", u=data["videos_url"]) if data["videos_url"] else ""))

    # ------------------------------------------------------------ the recent documents (0.388)

    def _recent_card(self):
        """The recent documents' card: how they are shown (big pictures, list, details), in what order, a word to find
        them; the documents (the room left on the page); how many are kept."""
        card = QtWidgets.QFrame()
        card.setObjectName("start_card")
        card.setMinimumWidth(RECENT_MIN_W)
        box = QtWidgets.QVBoxLayout(card)
        box.setContentsMargins(14, 12, 14, 12)
        box.setSpacing(8)
        top = QtWidgets.QHBoxLayout()               # (its title and the three views; under them, find and order)
        top.setSpacing(6)
        head = QtWidgets.QLabel(t("start.recent"))
        head.setObjectName("start_title")
        top.addWidget(head)
        top.addStretch(1)
        tools = QtWidgets.QHBoxLayout()
        tools.setSpacing(6)
        self.recent_find = QtWidgets.QLineEdit()
        self.recent_find.setObjectName("start_find")
        self.recent_find.setPlaceholderText(t("start.recent_find"))
        self.recent_find.setClearButtonEnabled(True)
        self.recent_find.textChanged.connect(lambda _text: self._fill_recent())
        tools.addWidget(self.recent_find, 1)
        self.recent_order = QtWidgets.QComboBox()
        for key in recent.ORDERS:
            self.recent_order.addItem(t("start.order." + key), key)
        self.recent_order.setToolTip(t("start.order_tip"))
        self.recent_order.setSizeAdjustPolicy(QtWidgets.QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.recent_order.activated.connect(lambda _i: self.set_recent_order(self.recent_order.currentData()))
        tools.addWidget(self.recent_order)
        self.recent_views = {}
        group = QtWidgets.QButtonGroup(card)
        for key in recent.VIEWS:
            b = QtWidgets.QToolButton()
            b.setObjectName("start_view")
            b.setCheckable(True)
            b.setToolTip(t("start.view." + key))
            b.setIconSize(QtCore.QSize(16, 16))
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            b.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            b.clicked.connect(lambda _=False, k=key: self.set_recent_view(k))
            group.addButton(b)
            top.addWidget(b)
            self.recent_views[key] = b
        box.addLayout(top)
        box.addLayout(tools)
        self.recent_stack = QtWidgets.QStackedWidget()
        self.recent_grid = self._recent_list(QtWidgets.QListView.ViewMode.IconMode, GRID_PICTURE)
        self.recent_list = self._recent_list(QtWidgets.QListView.ViewMode.ListMode, LIST_PICTURE)
        self.recent_details = QtWidgets.QTreeWidget()
        self.recent_details.setObjectName("start_recent")
        self.recent_details.setColumnCount(4)
        self.recent_details.setHeaderLabels([t("start.col.name"), t("start.col.folder"), t("start.col.modified"),
                                              t("start.col.size")])
        self.recent_details.setRootIsDecorated(False)
        self.recent_details.setUniformRowHeights(True)
        self.recent_details.setIconSize(QtCore.QSize(32, 20))
        self.recent_details.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.recent_details.setTextElideMode(QtCore.Qt.TextElideMode.ElideMiddle)
        self.recent_details.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        header = self.recent_details.header()
        header.setStretchLastSection(False)
        for col in (0, 1):                          # (the name and the folder share what is left, cut in the middle)
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeMode.Stretch)
        for col in (2, 3):
            header.setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.recent_details.itemClicked.connect(lambda item, _col: self._open_item(item))
        self._menu_on(self.recent_details)
        self.recent_none = self._note(t("start.recent_none"))
        self.recent_none.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignLeft)
        for w in (self.recent_grid, self.recent_list, self.recent_details, self.recent_none):
            self.recent_stack.addWidget(w)
        box.addWidget(self.recent_stack, 1)
        row = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(t("start.keep"))
        label.setObjectName("start_muted")
        row.addWidget(label)
        spin = QtWidgets.QSpinBox()
        spin.setRange(1, recent.MOST)
        spin.setSuffix(" / {}".format(recent.MOST))
        spin.valueChanged.connect(lambda n: (recent.set_keep(n), QtCore.QTimer.singleShot(0, self._fill_recent)))
        self.keep_spin = spin
        row.addWidget(spin)
        row.addStretch(1)
        self.recent_count = QtWidgets.QLabel()
        self.recent_count.setObjectName("start_muted")
        row.addWidget(self.recent_count)
        box.addLayout(row)
        return card

    def _recent_list(self, mode, size):
        view = QtWidgets.QListWidget()
        view.setObjectName("start_recent")
        view.setViewMode(mode)
        view.setIconSize(size)
        view.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        view.setMovement(QtWidgets.QListView.Movement.Static)
        view.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        view.setWordWrap(True)
        view.setTextElideMode(QtCore.Qt.TextElideMode.ElideMiddle)
        view.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setMouseTracking(True)
        if mode == QtWidgets.QListView.ViewMode.IconMode:
            view.setGridSize(QtCore.QSize(size.width() + 24, size.height() + 46))
            view.setSpacing(6)
            view.setUniformItemSizes(True)
        else:
            view.setSpacing(2)
        view.itemClicked.connect(self._open_item)
        self._menu_on(view)
        return view

    def _menu_on(self, view):
        view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        view.customContextMenuRequested.connect(lambda pos, v=view: self._recent_menu(v, pos))

    def _recent_menu(self, view, pos):
        """The right button on a recent document: open it, open its folder, take it off the list; or the whole list."""
        item = view.itemAt(pos)
        if isinstance(item, QtWidgets.QTreeWidgetItem):
            path = item.data(0, PATH_ROLE)
        else:
            path = item.data(PATH_ROLE) if item is not None else None
        menu = QtWidgets.QMenu(view)
        if path:
            menu.addAction(t("start.menu.open"), lambda: self._call("on_open_path", path))
            folder = menu.addAction(t("start.menu.folder"), lambda: links.open_folder(os.path.dirname(path)))
            folder.setEnabled(os.path.isdir(os.path.dirname(path)))
            menu.addAction(t("start.recent_remove"), lambda: self.remove_recent(path))
            menu.addSeparator()
        clear = menu.addAction(t("start.menu.clear"), self.clear_recent)
        clear.setEnabled(bool(recent.files()))
        self._recent_menu_shown = menu                      # (tests)
        from . import menus
        menu.exec(menus.menu_point(menu, view.viewport().mapToGlobal(pos)))

    def remove_recent(self, path):
        recent.remove(path)
        self._fill_recent()

    def clear_recent(self):
        for path in recent.files():
            recent.remove(path)
        self._fill_recent()

    def _open_item(self, item):
        path = item.data(0, PATH_ROLE) if isinstance(item, QtWidgets.QTreeWidgetItem) else item.data(PATH_ROLE)
        if path:
            self._call("on_open_path", path)

    def set_recent_view(self, key):
        """Big pictures in a grid ("grid"), a list ("list") or details ("details") — kept for next time."""
        recent.set_view(key)
        self._fill_recent()

    def set_recent_order(self, key):
        recent.set_order(key)
        self._fill_recent()

    def _picture(self, path, size):
        """A document's picture at `size` (cut to its shape round its middle), or the symbol on the panel's colour."""
        pm = QtGui.QPixmap(recent.thumb_file(path))
        if not pm.isNull():
            pm = pm.scaled(size, QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                           QtCore.Qt.TransformationMode.SmoothTransformation)
            return pm.copy((pm.width() - size.width()) // 2, (pm.height() - size.height()) // 2, size.width(),
                           size.height())
        out = QtGui.QPixmap(size)
        out.fill(QtGui.QColor(theme.C["panel"]))
        mark = brand.symbol(int(min(size.width(), size.height()) * 0.6))
        if mark is not None:
            p = QtGui.QPainter(out)
            p.drawPixmap((size.width() - mark.width()) // 2, (size.height() - mark.height()) // 2, mark)
            p.end()
        return out

    def _view_icons(self):
        """The view buttons' glyphs (in the theme's ink): a grid of pictures, a list, details."""
        ink = QtGui.QColor(theme.C["text"])
        for key, button in self.recent_views.items():
            pm = QtGui.QPixmap(16, 16)
            pm.fill(QtCore.Qt.GlobalColor.transparent)
            p = QtGui.QPainter(pm)
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.setBrush(ink)
            if key == "grid":
                for x, y in ((1, 1), (9, 1), (1, 9), (9, 9)):
                    p.drawRect(x, y, 6, 6)
            elif key == "list":
                for y in (2, 7, 12):
                    p.drawRect(1, y, 3, 3)
                    p.drawRect(6, y + 1, 9, 1)
            else:
                for y in (2, 6, 10, 14):
                    p.drawRect(1, y, 14, 1)
            p.end()
            button.setIcon(QtGui.QIcon(pm))

    def _fill_recent(self):
        """The recent documents as asked: their view, their order, the word typed."""
        key, how = recent.view(), recent.order()
        for k, b in self.recent_views.items():
            b.setChecked(k == key)
        self.recent_order.setCurrentIndex(max(0, self.recent_order.findData(how)))
        everything = recent.files()
        paths = recent.arranged(everything, how, self.recent_find.text())
        self.keep_spin.blockSignals(True)
        self.keep_spin.setValue(recent.keep())
        self.keep_spin.blockSignals(False)
        self.recent_count.setText(t("start.recent_count", n=len(paths), m=len(everything)))
        if not paths:
            self.recent_none.setText(t("start.recent_none") if not everything else t("start.recent_not_found"))
            self.recent_stack.setCurrentWidget(self.recent_none)
            return
        if key == "details":
            view = self.recent_details
            view.clear()
            for path in paths:
                there = os.path.exists(path)
                when = recent.modified(path)
                size = os.path.getsize(path) if there else None
                item = QtWidgets.QTreeWidgetItem([
                    os.path.splitext(os.path.basename(path))[0],
                    os.path.dirname(path) if there else t("start.missing"),
                    time.strftime("%d/%m/%Y %H:%M", time.localtime(when)) if when else "",
                    _size_text(size) if size is not None else ""])
                item.setIcon(0, QtGui.QIcon(self._picture(path, QtCore.QSize(32, 20))))
                item.setData(0, PATH_ROLE, path)
                item.setToolTip(0, path)
                item.setToolTip(1, path)
                if not there:
                    for col in range(4):
                        item.setForeground(col, QtGui.QColor(theme.C["muted"]))
                view.addTopLevelItem(item)
        else:
            view = self.recent_grid if key == "grid" else self.recent_list
            size = GRID_PICTURE if key == "grid" else LIST_PICTURE
            view.clear()
            for path in paths:
                there = os.path.exists(path)
                name = os.path.splitext(os.path.basename(path))[0]
                text = name if key == "grid" else "{}\n{}".format(
                    name, os.path.dirname(path) if there else t("start.missing"))
                item = QtWidgets.QListWidgetItem(QtGui.QIcon(self._picture(path, size)), text)
                item.setData(PATH_ROLE, path)
                item.setToolTip(path if there else "{}\n{}".format(path, t("start.missing")))
                if not there:
                    item.setForeground(QtGui.QColor(theme.C["muted"]))
                view.addItem(item)
        self.recent_stack.setCurrentWidget(view)

    def _fill_discussions(self, data):
        body, foot = self.discussions_card.body, self.discussions_card.foot
        self._clear(body)
        self._clear(foot)
        for item in data["discussions"]:
            number, author = item.get("number"), item.get("author")
            line = " · ".join(x for x in ("#{}".format(number) if number else "", "@{}".format(author) if author
                                          else "") if x)
            body.addWidget(self._text_row(str(item.get("title", "")), line,
                                          lambda u=item.get("url", ""): self._open_link(u, t("start.discussions"))))
        if not data["discussions"]:
            body.addWidget(self._note(t("start.discussions_none")))
        body.addStretch(1)
        foot.addWidget(self._button(t("start.discussions_open"),
                                    lambda: self._open_link(config()["discussions_url"], t("start.discussions")),
                                    "start_blue"))

    def _fill_supporters(self, data):
        body, foot = self.supporters_card.body, self.supporters_card.foot
        self._clear(body)
        self._clear(foot)
        for item in data["supporters"]:
            row = QtWidgets.QHBoxLayout()
            name = QtWidgets.QLabel(str(item.get("name", "")))
            name.setObjectName("start_row_text")
            row.addWidget(name, 1)
            amount = QtWidgets.QLabel(str(item.get("amount", "")))
            amount.setObjectName("start_row_text")
            row.addWidget(amount)
            body.addLayout(row)
        if not data["supporters"]:
            body.addWidget(self._note(t("start.supporters_none")))
        body.addStretch(1)
        foot.addWidget(self._button(t("start.support"),
                                    lambda: self._open_link(config()["support_url"], t("start.supporters")),
                                    "start_red"))

    # ------------------------------------------------------------ the tutorials

    def open_tutorial(self, item):
        """A tutorial: the first steps, a section of TESTAR.md or GUIA.md — read on the page, over the Discussions and
        the Supporters (0.406) — another tab of the Help, or a web address (the browser)."""
        what, title = str(item.get("open", "")), str(item.get("title", ""))
        if what == "help:steps":
            self.reader.show_steps(what, title)
            self._show_reader(True)
            return
        if what.startswith("help:"):
            if self.on_help is not None:
                self.on_help(what[5:])
            return
        if what.startswith("testar:"):
            text = testar_section(what[7:])
        elif what.startswith("doc:"):
            text = doc_text(what[4:])
        else:
            self._open_link(what, title)
            return
        if not text:
            self._say(t("start.tutorial_missing", t=title))
            return
        self.reader.show_text(what, title, text)
        self._show_reader(True)

    def close_tutorial(self):
        """The tutorial closed: the Discussions and the Supporters back in their place."""
        self._show_reader(False)

    def tutorial_open(self):
        return not self.reader.isHidden()

    def _show_reader(self, on):
        self.discussions_card.setVisible(not on)
        self.supporters_card.setVisible(not on)
        self.reader.setVisible(on)
        if not on:
            self.reader.key = None
        self._mark_tutorial()

    def _mark_tutorial(self):
        """The tutorial being read marked in the list."""
        for item, row in self._tutorial_rows:
            now = self.tutorial_open() and str(item.get("open", "")) == self.reader.key
            if bool(row.property("current")) != now:
                row.setProperty("current", now)
                row.style().unpolish(row)
                row.style().polish(row)

    # ------------------------------------------------------------ colours

    def restyle(self):
        c = theme.C
        blue = brand.BLUE.name()
        self.title.setText('Arq<span style="color:{}">Synth</span> BIM'.format(blue))
        self.setStyleSheet(
            "QWidget#start_page { background: %(page)s; }"
            "QFrame#start_card { background: %(card)s; border: 1px solid %(edge)s; border-radius: 10px; }"
            "QWidget#start_inner, QScrollArea { background: transparent; border: none; }"
            "QLabel#start_brand { font-size: 26px; font-weight: 700; color: %(text)s; }"
            "QLabel#start_title { font-size: 15px; font-weight: 700; color: %(text)s; }"
            "QLabel#start_muted { color: %(muted)s; }"
            "QLabel#start_row_title { font-weight: 600; color: %(text)s; }"
            "QLabel#start_row_text { color: %(muted)s; }"
            "QLabel#start_thumb { background: %(canvas)s; border: 1px solid %(edge)s; border-radius: 4px; }"
            "QFrame#start_row { background: transparent; border-radius: 6px; }"
            "QFrame#start_row:hover { background: %(hover)s; }"
            # (0.406) the tutorial being read: its line marked; the reader, its ×, its arrows
            "QFrame#start_row[current=\"true\"] { background: %(select_soft)s; }"
            "QTextBrowser#start_reader { background: transparent; border: none; color: %(text)s;"
            " selection-background-color: %(select)s; selection-color: %(select_text)s; }"
            "QToolButton#start_close { border: none; border-radius: 5px; color: %(muted)s; font-size: 20px;"
            " padding: 0 7px; }"
            "QToolButton#start_close:hover { background: %(hover)s; color: %(text)s; }"
            "QToolButton#start_step { border: 1px solid %(edge)s; border-radius: 5px; background: %(button)s;"
            " color: %(text)s; padding: 2px 6px; }"
            "QToolButton#start_step:hover { background: %(hover)s; }"
            "QToolButton#start_step:disabled { color: %(muted)s; }"
            "QPushButton#start_primary, QPushButton#start_button, QPushButton#start_blue, QPushButton#start_red {"
            " border-radius: 6px; padding: 8px 14px; font-weight: 600; text-align: left; }"
            "QPushButton#start_primary { background: %(accent)s; color: %(accent_text)s; border: none; }"
            "QPushButton#start_primary:hover { background: %(accent_strong)s; }"
            "QPushButton#start_button { background: %(button)s; color: %(text)s; border: 1px solid %(edge)s; }"
            "QPushButton#start_button:hover { background: %(hover)s; }"
            "QPushButton#start_blue { background: %(select)s; color: %(select_text)s; border: none;"
            " text-align: center; }"
            "QPushButton#start_red { background: %(fail)s; color: %(on_red)s; border: none; text-align: center; }"
            "QToolButton#start_remove { border: none; color: %(muted)s; font-size: 15px; padding: 0 4px; }"
            "QToolButton#start_remove:hover { color: %(fail)s; }"
            # (0.388) the recent documents' views and their tools
            "QListWidget#start_recent, QTreeWidget#start_recent { background: transparent; border: none;"
            " color: %(text)s; outline: none; }"
            "QListWidget#start_recent::item { border-radius: 6px; padding: 4px; color: %(text)s; }"
            "QListWidget#start_recent::item:hover, QTreeWidget#start_recent::item:hover { background: %(hover)s; }"
            "QListWidget#start_recent::item:selected, QTreeWidget#start_recent::item:selected {"
            " background: %(select_soft)s; color: %(text)s; }"
            "QToolButton#start_view { border: 1px solid transparent; border-radius: 5px; padding: 3px; }"
            "QToolButton#start_view:hover { background: %(hover)s; }"
            "QToolButton#start_view:checked { background: %(select_soft)s; border-color: %(select)s; }"
            "QLineEdit#start_find { border: 1px solid %(edge)s; border-radius: 5px; padding: 3px 6px;"
            " background: %(input)s; color: %(text)s; }"
            # (0.388) the scroll bars thin, in the theme's colours (the lists' came out black)
            "QScrollBar:vertical { background: transparent; width: 10px; margin: 0; border: none; }"
            "QScrollBar::handle:vertical { background: %(edge)s; border-radius: 4px; min-height: 30px;"
            " margin: 0 2px; }"
            "QScrollBar::handle:vertical:hover { background: %(muted)s; }"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; border: none; }"
            "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }"
            % dict(page=c["canvas"], card=c["window"], edge=c["edge"], text=c["text"], muted=c["muted"],
                   canvas=c["panel"], hover=c["button_hover"], accent=c["accent"], accent_text=c["accent_text"],
                   accent_strong=c["accent_strong"], button=c["button"], select=c["select"],
                   select_text=c["select_text"], fail=c["fail"], on_red=c["window"], select_soft=c["select_soft"],
                   input=c["input"]))
        if getattr(self, "recent_views", None):
            self._view_icons()
            self._fill_recent()                             # (the pictures' background in the theme's colour)
            self._fit_cards()
        if getattr(self, "reader", None) is not None:
            self.reader.restyle()
