"""(0.338) The program's two themes — the light one it always had, and the dark one of the owner's Caixilho Studio
prototype (2026-10-29: «quando criarmos o tema escuro, vai ser assim»): every colour of the interface comes from here,
none written in the middle of the code (ui/ribbon, context_bar, notice, properties, the main window's pieces; the
Caixilho Studio's keys are its prototype's names).

The theme is the computer's, not the project's (QSettings «aparencia/tema»), and changes at once: apply() sets the
Fusion style's palette — the Qt windows follow (dialogs, tables, fields, lists, menus, scroll bars, tips) — and C (the
theme in use, changed in place); the main window then restyles its own pieces and puts its icons in the theme's ink
(icon(), themed()). The views (3D, plans, sheets) are not the interface's: the paper stays white, as Revit's."""

import hashlib

from PySide6 import QtCore, QtGui, QtWidgets

KEY = "aparencia/tema"
NAMES = ("light", "dark")

THEMES = {
    "light": dict(
        # (0.308: the Caixilho Studio's names) the ribbon's whites and greys, its dark blue header, its blue
        window="#ffffff", header="#1f2a37", header_text="#e8edf4", header_muted="#aab4c3", bar="#f6f7f9",
        line="#d9dde3", canvas="#f3f5f8", grid="#e4e8ee", text="#1f2a37", muted="#6b7685", hint="#7a828e",
        accent="#2f6fe4", accent_strong="#1f4fb0", accent_text="#ffffff", accent_off="#a9c1ee",
        accent_off_text="#ffffff", select="#2f6fe4", select_text="#ffffff", select_soft="#dce8ff",
        select_border="#9ab8f0", select_ink="#1f2a37", card="#ffffff", edge="#d9dde3", edge_2="#cfd5dd",
        button="#f6f7f9", button_hover="#e6edf9", chip_on="#dce8ff", chip_on_text="#1f2a37",
        strip="#b9c1cc", strip_fill=(47, 111, 228, 12), footer="#f6f7f9", input="#ffffff",
        warning="#d64545", ext=(47, 111, 228, 95), shadow=(31, 42, 55), tab_on="#ffffff",
        system_on_bg="#dce8ff", system_on_text="#1f4fb0", off_text="#4a5361", mark_ink="#ffffff",
        toast_text="#ffffff", outline=(31, 42, 55, 150), panel_edge=(31, 42, 55, 70),
        grip_outline=(255, 255, 255, 235),
        # (0.338) the program's own
        context="#2e9e4f", context_text="#8fe0a4", panel="#eef1f5", panel_hover="#dfe6f1", link="#1f5fd6",
        note="#6b7380", ctx_text="#2f4f7f", invalid_bg="#fff2f2", ok="#2e7d32", attention="#b26a00",
        fail="#b0302a", good="#2e8b57", bad="#d0453f", neutral="#8a8a8a", target="#ffe58a",
        target_border="#e3b341", notice_text="#1f2a37", notice_close="#5b6b80", notice_button="#ffffff",
        notice_warning=("#fff6dc", "#e3b341", "#b7791f"), notice_info=("#eef4ff", "#a9c3f2", "#2f6fe4"),
        notice_hint=("#ffffff", "#c8d1dd", "#2f6fe4"), notice_ask=("#edf8f0", "#86c99b", "#2e9e4f")),
    "dark": dict(
        window="#17191c", header="#111316", header_text="#dde1e6", header_muted="#9aa3ad", bar="#1b1e22",
        line="#2a2e34", canvas="#15171a", grid="#1c1f23", text="#dde1e6", muted="#9aa3ad", hint="#8b949e",
        accent="#f0b44c", accent_strong="#ffd27a", accent_text="#17191c", accent_off="#6b5a35",
        accent_off_text="#2a2a2a", select="#5b9cff", select_text="#0d1420", select_soft="rgba(91,156,255,46)",
        select_border="#5b9cff", select_ink="#cfe0ff", card="rgba(28,31,35,245)", edge="#30353b",
        edge_2="#3a3f46", button="#24282d", button_hover="#2b3036", chip_on="#3a3f46", chip_on_text="#eef1f4",
        strip="#4a5059", strip_fill=(91, 156, 255, 10), footer="#1b1e22", input="#15171a",
        warning="#ff8a80", ext=(240, 180, 76, 82), shadow=(0, 0, 0), tab_on="#15171a",
        system_on_bg="rgba(240,180,76,36)", system_on_text="#ffd27a", off_text="#c3c9d0",
        mark_ink="#17191c", toast_text="#0d1420", outline=(0, 0, 0, 153), panel_edge=(0, 0, 0, 89),
        grip_outline=(0, 0, 0, 115),
        context="#2e9e4f", context_text="#8fe0a4", panel="#1c1f23", panel_hover="#2b3036", link="#7fb0ff",
        note="#9aa3ad", ctx_text="#9cc2ff", invalid_bg="#3a2224", ok="#6cc070", attention="#f0b44c",
        fail="#ff8a80", good="#5cc28a", bad="#ff8a80", neutral="#9aa3ad", target="#5a4a1a",
        target_border="#f0b44c", notice_text="#dde1e6", notice_close="#9aa3ad", notice_button="#24282d",
        notice_warning=("#2e2717", "#8a6d2c", "#f0b44c"), notice_info=("#1a2433", "#35507a", "#5b9cff"),
        notice_hint=("#1f2226", "#3a3f46", "#5b9cff"), notice_ask=("#18291e", "#2f6b43", "#6cc070")),
}

# (0.374) the palettes of the owner's interface study (proposta-interface-arqsynth.html, «Explorar cores»): nine
# colours each — the bar and background, the ribbon, the panels, the headers, the accent, the text, the drawing area,
# the dividers, the fields — the program's other colours made from them (study_theme)
STUDY = {
    "bege": dict(base="#d9c5ae", ribbon="#e7d6c3", panel="#e6d4c1", header="#17366c", accent="#5d74a2",
                 text="#272923", canvas="#bfb2a4", line="#aa9987", field="#f2e5d7"),
    "pedra": dict(base="#bfc4c0", ribbon="#d9dcd8", panel="#d5d9d5", header="#17366c", accent="#4966a2",
                  text="#242d2c", canvas="#b4beb9", line="#939f99", field="#eef0ed"),
    "escuro": dict(base="#45413e", ribbon="#56504a", panel="#514d48", header="#1b2c4a", accent="#a2b2d2",
                   text="#f3eee7", canvas="#77736d", line="#82796f", field="#66605a"),
    "grafite": dict(base="#1b1b1b", ribbon="#242424", panel="#202020", header="#171717", accent="#2f75fd",
                    text="#e9e6e1", canvas="#30302f", line="#42413f", field="#303030"),
}
STUDY["revit"] = dict(base="#202833", ribbon="#354153", panel="#374456", header="#1b242f",
                      accent="#6279d5", text="#f1f3f5", canvas="#202630", line="#526074", field="#293646")

TOKENS = ("base", "ribbon", "panel", "header", "accent", "text", "canvas", "line", "field")
CUSTOM = "personalizado"        # the palette as the owner tuned it in «Explorar cores» (kept on this computer)
PALETTE_KEY = "aparencia/paleta"
NAMES = NAMES + tuple(STUDY) + (CUSTOM,)


def _mix(a, b, f):
    """The colour f of the way from a to b ("#rrggbb")."""
    ca, cb = QtGui.QColor(a), QtGui.QColor(b)
    return QtGui.QColor(round(ca.red() + (cb.red() - ca.red()) * f), round(ca.green() + (cb.green() - ca.green()) * f),
                        round(ca.blue() + (cb.blue() - ca.blue()) * f)).name()


def _dark(colour):
    return QtGui.QColor(colour).lightnessF() < 0.45


def study_theme(p):
    """A study palette's nine colours (p) made into a whole theme of the program: the dark one's or the light one's
    as the base, the colours of the bars, panels, fields, lines, text and accent taken from the palette."""
    dark = _dark(p["base"])
    out = dict(THEMES["dark" if dark else "light"])
    text, accent = p["text"], p["accent"]
    muted = _mix(text, p["base"], 0.45)
    out.update(
        window=p["panel"], header=p["base"], header_text=text, header_muted=muted, bar=p["ribbon"], line=p["line"],
        canvas=p["canvas"], grid=_mix(p["canvas"], text, 0.09), text=text, muted=muted, hint=muted,
        accent=accent, accent_strong=_mix(accent, "#000000" if not dark else "#ffffff", 0.25), accent_text="#ffffff",
        select=accent, select_text="#ffffff", select_soft=_mix(p["ribbon"], accent, 0.20),
        select_border=_mix(p["ribbon"], accent, 0.45), select_ink=text, card=p["panel"], edge=p["line"],
        edge_2=_mix(p["line"], text, 0.15), button=p["field"], button_hover=_mix(p["ribbon"], accent, 0.12),
        chip_on=_mix(p["ribbon"], accent, 0.20), chip_on_text=text, footer=p["base"], input=p["field"],
        tab_on=p["ribbon"], panel=p["panel"], panel_hover=_mix(p["panel"], accent, 0.12), link=accent,
        ctx_text=p["header"] if not dark else _mix(accent, "#ffffff", 0.35), notice_text=text,
        off_text=_mix(text, p["base"], 0.25),
        # (the panels' titles: on a dark palette the study's header itself; on a light one a tint of it, under the
        # theme's dark text)
        panel_head=p["header"], panel_head_text="#ffffff", palette=dict(p))
    return out


def custom_palette():
    """The palette kept from «Explorar cores» on this computer, or None."""
    import json
    try:
        p = json.loads(str(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value(PALETTE_KEY, "") or "null"))
    except ValueError:
        return None
    if isinstance(p, dict) and all(isinstance(p.get(k), str) and QtGui.QColor(p[k]).isValid() for k in TOKENS):
        return {k: QtGui.QColor(p[k]).name() for k in TOKENS}
    return None


def keep_palette(p):
    import json
    QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue(PALETTE_KEY, json.dumps({k: p[k] for k in TOKENS}))


def theme_of(name):
    """A theme's colours by its name (the program's two, the study's five, the owner's own)."""
    if name in STUDY:
        return study_theme(STUDY[name])
    if name == CUSTOM:
        return study_theme(custom_palette() or STUDY["bege"])
    return THEMES[name]


NAME = "light"
C = dict(THEMES[NAME])          # the theme in use — changed in place: who took it keeps seeing it

# the dark palette of the Qt windows (Fusion): (role, colour, the disabled one's)
_DARK_ROLES = (("Window", "#17191c", None), ("WindowText", "#dde1e6", "#6b7380"), ("Base", "#15171a", "#1a1c1f"),
               ("AlternateBase", "#1c1f23", None), ("ToolTipBase", "#24282d", None),
               ("ToolTipText", "#dde1e6", None), ("PlaceholderText", "#7a828e", None),
               ("Text", "#dde1e6", "#6b7380"), ("Button", "#24282d", "#1e2125"),
               ("ButtonText", "#dde1e6", "#6b7380"), ("BrightText", "#ffffff", None),
               ("Light", "#3a3f46", None), ("Midlight", "#30353b", None), ("Mid", "#2a2e34", None),
               ("Dark", "#0e1012", None), ("Shadow", "#000000", None), ("Highlight", "#5b9cff", "#3a3f46"),
               ("HighlightedText", "#0d1420", "#9aa3ad"), ("Link", "#7fb0ff", None),
               ("LinkVisited", "#b39ddb", None))


def is_dark():
    """The interface dark (its icons in a light ink): the dark theme, or (0.374) a dark palette of the study's."""
    return NAME == "dark" or (NAME in STUDY or NAME == CUSTOM) and _dark(C.get("header", "#ffffff"))


def qcolor(value):
    """A colour of the theme as a QColor: "#rrggbb", "rgba(r,g,b,a)" (a 0–255) or an (r, g, b[, a]) tuple."""
    if isinstance(value, (tuple, list)):
        return QtGui.QColor(*value)
    text = str(value).strip()
    if text.startswith("rgba(") and text.endswith(")"):
        r, g, b, a = (int(float(v)) for v in text[5:-1].split(","))
        return QtGui.QColor(r, g, b, a)
    return QtGui.QColor(text)


def colour(key):
    """The theme's colour of this key, as a QColor."""
    return qcolor(C[key])


def _hex(key, fallback):
    """The theme's colour as «#rrggbb» (an «rgba(…)» one: its colour, opaque)."""
    return qcolor(C.get(key, fallback)).name()


def props_colours():
    """(0.414, the owner: «destacando os títulos colapsáveis e com trama para melhorar a distinção de parâmetros») The
    Properties panel's: its groups' titles on a band of the selection's colour over the panel's, the subgroups' on a
    lighter one, the rows striped a shade off the fields' — all from the theme in use."""
    field, panel = _hex("input", "#ffffff"), _hex("panel", "#eef1f5")
    select, text = _hex("select", "#2f6fe4"), _hex("text", "#1f2a37")
    dark = _dark(field)
    return {"group": _mix(panel, select, 0.30 if dark else 0.20), "group_text": text,
            "sub": _mix(field, select, 0.14 if dark else 0.09), "stripe": _mix(field, text, 0.08 if dark else 0.07),
            "group_rule": _mix(panel, select, 0.55 if dark else 0.45)}


def saved():
    """The theme chosen on this computer ("light" when none was)."""
    name = str(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value(KEY, "light") or "light")
    return "bege" if name == "areia" else name if name in NAMES else "light"


VIEWS_KEY = "aparencia/vistas_escuras"    # (0.341) the views' background dark — apart from the interface's theme


def dark_views():
    """(0.341) The views' background dark on this computer (render/canvas)?"""
    return str(QtCore.QSettings("ArqSynth", "ArqSynth BIM").value(VIEWS_KEY, "false")).lower() == "true"


def set_dark_views(on):
    QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue(VIEWS_KEY, "true" if on else "false")


def palette(name=None):
    """The Qt windows' palette of a theme: the Fusion style's own for the light one (as always), the prototype's
    greys for the dark one."""
    name = name or NAME
    style = QtWidgets.QApplication.style() if QtWidgets.QApplication.instance() is not None else None
    if name == "light":
        return style.standardPalette() if style is not None else QtGui.QPalette()
    pal = QtGui.QPalette()
    disabled = QtGui.QPalette.ColorGroup.Disabled
    if name in STUDY or name == CUSTOM:                  # (0.374) the study's palettes: the Qt windows in its colours
        p = theme_of(name)["palette"]
        dim = _mix(p["text"], p["panel"], 0.55)
        roles = (("Window", p["panel"], None), ("WindowText", p["text"], dim), ("Base", p["field"], p["panel"]),
                 ("AlternateBase", _mix(p["field"], p["panel"], 0.5), None), ("ToolTipBase", p["field"], None),
                 ("ToolTipText", p["text"], None), ("PlaceholderText", dim, None), ("Text", p["text"], dim),
                 ("Button", p["ribbon"], p["panel"]), ("ButtonText", p["text"], dim), ("BrightText", "#ffffff", None),
                 ("Light", _mix(p["ribbon"], "#ffffff", 0.3), None), ("Midlight", p["ribbon"], None),
                 ("Mid", p["line"], None), ("Dark", _mix(p["line"], "#000000", 0.3), None), ("Shadow", "#000000", None),
                 ("Highlight", p["accent"], p["line"]), ("HighlightedText", "#ffffff", dim),
                 ("Link", p["accent"], None), ("LinkVisited", _mix(p["accent"], "#800080", 0.4), None))
        for role, on, off in roles:
            r = getattr(QtGui.QPalette.ColorRole, role)
            pal.setColor(r, QtGui.QColor(on))
            pal.setColor(disabled, r, QtGui.QColor(off or on))
        return pal
    for role, on, off in _DARK_ROLES:
        r = getattr(QtGui.QPalette.ColorRole, role)
        pal.setColor(r, QtGui.QColor(on))
        pal.setColor(disabled, r, QtGui.QColor(off or on))
    return pal


def apply(name, remember=False):
    """The theme in use from now on: C, the Qt windows' palette (the Fusion style, which follows it whole). Kept for
    next time when remember. Returns its name."""
    global NAME
    name = name if name in NAMES else "light"
    NAME = name
    C.clear()
    C.update(theme_of(name))
    app = QtWidgets.QApplication.instance()
    if app is not None:
        if name != "light":
            app.setStyle("Fusion")       # (the style that follows a palette whole; set again, every window polished anew)
        app.setPalette(palette(name))
    if remember:
        QtCore.QSettings("ArqSynth", "ArqSynth BIM").setValue(KEY, name)
    return name


# ------------------------------------------------------------ the icons in the theme's ink

_PAIRS = {}                     # an icon's cacheKey -> [its drawing, its light QIcon, its dark one (made when needed)]
_BY_LOOK = {}                   # the light drawing's bytes' digest -> that pair (an icon drawn again: the same pair)


def inked(pixmap):
    """An icon drawn for the light theme, for the dark one: its dark lines (neutral greys and black) light, its white
    and near-white fills dark grey; its colours (the blue, the yellow, the materials') and its mid greys as they were."""
    import numpy as np
    image = pixmap.toImage().convertToFormat(QtGui.QImage.Format.Format_ARGB32)
    w, h = image.width(), image.height()
    if not w or not h:
        return QtGui.QPixmap(pixmap)
    data = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(h, image.bytesPerLine())[:, :w * 4]
    px = data.reshape(h, w, 4).astype(np.float32)                   # B, G, R, A
    rgb = px[:, :, :3] / 255.0
    high, low = rgb.max(axis=2), rgb.min(axis=2)
    light = (high + low) / 2.0
    chroma = high - low
    neutral = (chroma < 0.18) & (px[:, :, 3] > 0)
    target = light.copy()
    dark_ink = neutral & (light < 0.5)
    target[dark_ink] = 0.88 - light[dark_ink] * 0.5                 # #222 → #d1d1d1
    paper = neutral & (light >= 0.8)
    target[paper] = 0.25 + (1.0 - light[paper]) * 0.5               # #ffffff → #404040
    shift = (target - light)[:, :, None]
    out = px.copy()
    out[:, :, :3] = np.clip((rgb + shift) * 255.0 + 0.5, 0, 255)
    result = QtGui.QImage(out.astype(np.uint8).tobytes(), w, h, w * 4, QtGui.QImage.Format.Format_ARGB32).copy()
    pm = QtGui.QPixmap.fromImage(result)
    pm.setDevicePixelRatio(pixmap.devicePixelRatio())
    return pm


def icon(pixmap):
    """A program's icon (drawn for the light theme) as a QIcon in the theme in use; its other theme's kept beside
    it, for themed()."""
    image = pixmap.toImage()
    digest = hashlib.blake2b(bytes(image.constBits()), digest_size=16).hexdigest() + "{}x{}@{}".format(
        image.width(), image.height(), pixmap.devicePixelRatio())
    pair = _BY_LOOK.get(digest)
    if pair is None:
        pair = [QtGui.QPixmap(pixmap), QtGui.QIcon(pixmap), None]
        _BY_LOOK[digest] = pair
        _PAIRS[pair[1].cacheKey()] = pair
    return _in_theme(pair)


def _in_theme(pair):
    if not is_dark():
        return pair[1]
    if pair[2] is None:                                 # (its dark one drawn the first time it is wanted)
        pair[2] = QtGui.QIcon(inked(pair[0]))
        _PAIRS[pair[2].cacheKey()] = pair
    return pair[2]


def themed(qicon):
    """The same icon in the theme in use (an icon not made by icon() as it is)."""
    if qicon is None or qicon.isNull():
        return qicon
    pair = _PAIRS.get(qicon.cacheKey())
    return qicon if pair is None else _in_theme(pair)


def retheme_icons(root):
    """Every icon under this window (its actions', its buttons', its tabs', its lists' and trees' items) in the theme
    in use."""
    for action in root.findChildren(QtGui.QAction):
        new = themed(action.icon())
        if new is not None and new.cacheKey() != action.icon().cacheKey():
            action.setIcon(new)
    widgets = [root] + root.findChildren(QtWidgets.QWidget)
    for w in widgets:
        if isinstance(w, QtWidgets.QAbstractButton):
            new = themed(w.icon())
            if new is not None and new.cacheKey() != w.icon().cacheKey():
                w.setIcon(new)
                if hasattr(w, "keep"):                      # (a ribbon button keeps its own icon)
                    w.keep()
        elif isinstance(w, QtWidgets.QTabBar):
            for i in range(w.count()):
                new = themed(w.tabIcon(i))
                if new is not None and not new.isNull():
                    w.setTabIcon(i, new)
        elif isinstance(w, QtWidgets.QTreeWidget):
            items = [w.topLevelItem(i) for i in range(w.topLevelItemCount())]
            while items:
                item = items.pop()
                for col in range(w.columnCount()):
                    new = themed(item.icon(col))
                    if new is not None and not new.isNull() and new.cacheKey() != item.icon(col).cacheKey():
                        item.setIcon(col, new)
                items += [item.child(i) for i in range(item.childCount())]
        elif isinstance(w, QtWidgets.QListWidget):
            for i in range(w.count()):
                item = w.item(i)
                new = themed(item.icon())
                if new is not None and not new.isNull() and new.cacheKey() != item.icon().cacheKey():
                    item.setIcon(new)
        elif isinstance(w, QtWidgets.QComboBox):
            for i in range(w.count()):
                new = themed(w.itemIcon(i))
                if new is not None and not new.isNull() and new.cacheKey() != w.itemIcon(i).cacheKey():
                    w.setItemIcon(i, new)
