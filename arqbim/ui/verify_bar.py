"""(0.417) The Verifier in the window: it watches the project and says what fails where it is seen.

- the footer's indicator, always there: green «✓ Cumpre o CTE», amber «⚠ 2 aviso(s)», red «✗ 3 incumprimento(s)» (grey
  «escolher o regulamento» before the project has a country); a click: the menu (the project's regulations, the
  marks on the plan);
- the strip at the foot of the view (red; amber for a warning): when a change makes something fail that did not, the
  whole sentence — «✗ Sala (Fogo A): área útil 12,40 m² — CTE, art. 40.º e Anexo I: mínimo 14,00 m²» — with «Ir para»
  and «Porquê», until the next change (or ×);
- the watcher: 0,3 s after the last change (never while a gesture goes on), the check made again (verify/check.py:
  the reader and the measures are kept until the model changes) — the program never waits for it.

The owner (2026-11-06): «se for inferior à legislação, então o sistema coloca uma mensagem no rodapé com fundo vermelho
de alerta»."""

from PySide6 import QtCore, QtGui, QtWidgets

from ..i18n import lang, t
from ..verify import check as check_mod
from ..verify import project
from . import theme

DELAY_MS = 300
SLICE_S = 0.04              # (0.424) s: the check goes on this long at a time, then lets the window answer
COUNTRY_KEY = "verificacao/pais"            # (QSettings: the country last chosen, for new projects)
MARKS_KEY = "verificacao/marcas"


def default_country():
    value = QtCore.QSettings("ArqSynth", "ArqSynth BIM").value(COUNTRY_KEY, "")
    return value if value in project.countries() else None


def marks_on():
    return str(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value(MARKS_KEY, "true")).lower() == "true"


class Strip(QtWidgets.QWidget):
    """The strip at the foot of the view: a failure said whole, with its buttons."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("verify_strip")
        self.kind = "fail"
        self.text = QtWidgets.QLabel(self)
        self.text.setWordWrap(True)
        self.text.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        font = self.text.font()
        font.setPixelSize(13)
        font.setBold(True)
        self.text.setFont(font)
        self.goto = QtWidgets.QPushButton(t("verify.strip.goto"), self)
        self.why = QtWidgets.QPushButton(t("verify.strip.why"), self)
        self.close_button = QtWidgets.QToolButton(self)
        self.close_button.setText("×")
        self.close_button.setAutoRaise(True)
        self.close_button.clicked.connect(self.hide)
        for b in (self.goto, self.why, self.close_button):
            b.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.on_goto = self.on_why = None
        self.goto.clicked.connect(lambda: self.on_goto and self.on_goto())
        self.why.clicked.connect(lambda: self.on_why and self.on_why())
        self.restyle()
        self.hide()
        parent.installEventFilter(self)

    def restyle(self):
        back = theme.C["fail"] if self.kind == "fail" else theme.C["attention"]
        ink = "#ffffff"
        self.setStyleSheet(
            "QWidget#verify_strip { background: %s; }"
            "QLabel { color: %s; background: transparent; }"
            "QPushButton { background: transparent; color: %s; border: 1px solid %s; border-radius: 4px;"
            " padding: 3px 10px; font-weight: 600; }"
            "QPushButton:hover { background: rgba(255,255,255,40); }"
            "QToolButton { color: %s; border: none; font-size: 16px; }" % (back, ink, ink, ink, ink))
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)

    def say(self, text, kind="fail"):
        self.kind = kind
        self.restyle()
        self.text.setText(text)
        self.place()
        self.show()
        self.raise_()

    def shown_text(self):
        return self.text.text() if self.isVisible() else ""

    def place(self):
        parent = self.parentWidget()
        w = parent.width()
        buttons = [self.goto, self.why]
        bw = sum(b.sizeHint().width() for b in buttons) + 8 * len(buttons) + 28
        text_w = max(200, w - bw - 24)
        h = max(34, self.text.heightForWidth(text_w) + 14)
        self.setGeometry(0, parent.height() - h, w, h)
        self.text.setGeometry(12, (h - self.text.heightForWidth(text_w)) // 2, text_w, self.text.heightForWidth(text_w))
        x = 12 + text_w + 8
        for b in buttons:
            size = b.sizeHint()
            b.setGeometry(x, (h - size.height()) // 2, size.width(), size.height())
            x += size.width() + 8
        self.close_button.setGeometry(w - 26, (h - 22) // 2, 22, 22)

    def eventFilter(self, obj, event):
        if obj is self.parentWidget() and event.type() == QtCore.QEvent.Type.Resize and self.isVisible():
            self.place()
        return False


class Verifier(QtCore.QObject):
    """The watcher and what it shows. The window gives it its document, its status bar and the views' area; it tells
    the window what to select (on_goto) and the view what fails (on_marks)."""

    def __init__(self, window, doc, status_bar, views_area):
        super().__init__(window)
        self.window, self.doc = window, doc
        self.result = None
        self.known = set()                  # the failures' keys of the last check (new ones are said)
        self.shown = None                   # the finding the strip says
        self.on_goto = None                 # fn(finding)
        self.on_marks = None                # fn({GlobalId: "fail" | "warn"})
        self.on_settings = None             # fn(): the project's regulations dialog
        self.on_panel = None                # fn(): (0.418) the Verification panel shown
        self.on_result = None               # fn(result): (0.418) each new result (the panel follows)
        self._model = getattr(doc, "ifc", None)
        self._job = None                    # (0.424) (the check's steps under way, the revision they are of)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.run)
        self.button = QtWidgets.QToolButton(status_bar)
        self.button.setObjectName("verify_indicator")
        self.button.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        self.button.setAutoRaise(True)
        menu = QtWidgets.QMenu(self.button)
        menu.addAction(t("verify.menu.panel"), lambda: self.on_panel and self.on_panel())          # (0.418)
        menu.addAction(t("verify.menu.settings"), lambda: self.on_settings and self.on_settings())
        self.marks_action = menu.addAction(t("verify.menu.marks"))
        self.marks_action.setCheckable(True)
        self.marks_action.setChecked(marks_on())
        self.marks_action.toggled.connect(self._marks_toggled)
        self.button.setMenu(menu)
        # (first on the left of the footer: it takes room from the tool's hint — cut short anyway, said whole in the
        # balloon — never from the footer's own buttons)
        status_bar.insertWidget(0, self.button)
        self.strip = Strip(views_area)
        self.strip.on_goto = lambda: self.shown is not None and self.on_goto and self.on_goto(self.shown)
        self.strip.on_why = lambda: self.shown is not None and self.why(self.shown)
        self._paint_button()

    # ------------------------------------------------------------ watching
    def changed(self):
        """The document changed: the check again in a moment (a run of changes: once, after the last)."""
        self.timer.start(DELAY_MS)

    def settings(self):
        return project.settings(self.doc, default_country())

    def run(self):
        """The check started — (0.424) in slices of 40 ms between the window's events (check_mod.steps): a big model
        is checked without the window standing still; a result kept is shown at once."""
        if getattr(self.doc, "loading", False):
            self.timer.start(DELAY_MS)
            return
        try:
            self._job = (check_mod.steps(self.doc, self.settings()), getattr(self.doc, "revision", 0))
        except Exception:                                   # noqa: BLE001 (never in the way of the drawing)
            import logging
            logging.getLogger("arqbim").exception("verifier")
            return
        self._slice()

    def _slice(self):
        import time
        job = getattr(self, "_job", None)
        if job is None:
            return
        steps, revision = job
        if getattr(self.doc, "revision", 0) != revision:   # (changed meanwhile: started again, after the change)
            self._job = None
            self.timer.start(DELAY_MS)
            return
        end = time.perf_counter() + SLICE_S
        try:
            while time.perf_counter() < end:
                next(steps)
        except StopIteration as done:
            self._job = None
            self._show(done.value)
            return
        except Exception:                                   # noqa: BLE001 (never in the way of the drawing)
            import logging
            logging.getLogger("arqbim").exception("verifier")
            self._job = None
            return
        QtCore.QTimer.singleShot(0, self._slice)

    def busy(self):
        """Whether a check is under way (its slices still to come)."""
        return getattr(self, "_job", None) is not None

    def _show(self, result):
        if self._model is not getattr(self.doc, "ifc", None):     # (another project: what it has is not «new»)
            self._model = getattr(self.doc, "ifc", None)
            self.result, self.known = None, set()
            self.strip.hide()
        first = self.result is None
        self.result = result
        failures = [f for f in result.failures if f.rule.severity != "info"]   # (0.420: a note is not an alert)
        keys = {f.key for f in failures}
        new = [f for f in failures if f.key not in self.known]
        self.known = keys
        self._paint_button()
        if new and not first:
            errors = [f for f in new if f.rule.severity == "error"]
            finding = (errors or new)[0]
            text = "✗ " + check_mod.message(finding) if finding.rule.severity == "error" else \
                "⚠ " + check_mod.message(finding)
            if len(new) > 1:
                text += "  " + t("verify.strip.more", n=len(new) - 1)
            self.shown = finding
            self.strip.say(text, "fail" if finding.rule.severity == "error" else "warn")
        elif self.strip.isVisible():
            self.strip.hide()
            self.shown = None
        if self.on_marks is not None:
            self.on_marks(self.marks())
        if self.on_result is not None:
            self.on_result(result)

    def marks(self):
        """{room / door GlobalId: "fail" | "warn"} of what fails, for the plan (none when the marks are off)."""
        if self.result is None or not self.marks_action.isChecked():
            return {}
        out = {}
        for f in self.result.failures:
            if f.rule.severity == "info":
                continue
            for g in f.subject.elements if f.subject.kind in ("room", "door") else ():
                if out.get(g) != "fail":
                    out[g] = "fail" if f.rule.severity == "error" else "warn"
        return out

    def _marks_toggled(self, on):
        QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue(MARKS_KEY, "true" if on else "false")
        if self.on_marks is not None:
            self.on_marks(self.marks())

    # ------------------------------------------------------------ the footer's indicator
    def _paint_button(self):
        s = self.settings()
        country = s.get("country")
        language = lang()
        if not country or not project.active(s):
            text, colour, tip = t("verify.foot.off"), theme.C["neutral"], t("verify.foot.tip_off")
        else:
            packs = self.result.packs if self.result is not None else project.active(s)
            laws = ", ".join(p.short for p, own in packs if own and project.is_law(p) and (   # (0.423: the town
                p.id != project.PLAN_PACK or project.plan_values(s))) or "—"              # plan once it has values)
            tip = t("verify.foot.tip", country=project.country_name(country, language), laws=laws)
            r = self.result
            n_err = r.count("error") if r is not None else 0
            n_warn = r.count("warning") if r is not None else 0
            tip = t("verify.foot.count", n=n_err, w=n_warn) + "\n" + tip
            if r is None or not r.findings:
                text, colour = t("verify.foot.none", law=laws), theme.C["neutral"]
            elif n_err and n_warn:
                text, colour = t("verify.foot.both", law=laws, n=n_err, w=n_warn), theme.C["fail"]
            elif n_err:
                text, colour = t("verify.foot.fail", law=laws, n=n_err), theme.C["fail"]
            elif n_warn:
                text, colour = t("verify.foot.warn", law=laws, n=n_warn), theme.C["attention"]
            else:
                text, colour = t("verify.foot.ok", law=laws), theme.C["ok"]
        self.button.setText(text)
        self.button.setToolTip(tip)
        self.button.setStyleSheet("QToolButton#verify_indicator { color: %s; font-weight: 600; padding: 0 6px; }"
                                  % colour)

    def restyle(self):
        self._paint_button()
        if self.strip.isVisible():
            self.strip.restyle()

    # ------------------------------------------------------------ why
    def why(self, finding):
        from ..verify import rules as rules_mod
        rule = finding.rule
        pack = rules_mod.find(rule.pack)
        side = "min" if any(k.startswith("min") for k in rule.limit) else "max"
        text = t("verify.why.text", title=rule.title, text=rule.text, value=check_mod.number(finding.value, rule.unit),
                 side=t("verify.side." + side), limit=check_mod.number(finding.limit, rule.unit),
                 source="{} — {}".format(pack.instrument, pack.source) if pack else rule.pack,
                 state=t("verify.why.confirmed") if rule.confirmed else t("verify.why.unconfirmed"))
        if rule.fix:
            text += t("verify.why.fix", fix=rule.fix)
        box = QtWidgets.QMessageBox(self.window)
        box.setWindowTitle(t("verify.why.title", law=pack.short if pack else rule.pack, article=rule.article))
        box.setText(text)
        box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        box.exec()
