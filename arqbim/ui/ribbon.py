"""The header and the ribbon (0.182, the interface's panels 1 and 2): a dark header with the disciplines as tabs and,
on its right, the project's name and the global commands (save, undo, redo, synchronise, help); under it the
ribbon, the active discipline's tools. They take the place of the four environments (0.84), of their side bar and
of the menus; every tool keeps its key whatever the discipline, and the menus are still there underneath (hidden),
so that nothing is lost.

(0.298) The disciplines in the order a project is worked — Home, Modelling (drawing and modifying, at any stage),
Manage (setting the project up), Massing and studies, Terrain, Architecture, Structure, Services, Collaborate
(coordinating), Annotate, View, Render — and each one's tools in named panels, as Revit's, in the order they are
used: large buttons (an icon over a name) for the main ones, columns of up to three small ones (an icon beside the
name) for the others. When the window is too narrow the panels on the right fold, each into one button with its
name that drops its tools down — none is hidden. A contextual tab ("Modify | Walls") comes at the end of the tabs
when walls are selected, with their modifiers, and goes when the selection is emptied.

PANELS and CONTEXTS are pure data: each discipline's (context's) panels — (its name, its items); an item is a name
(a large button) or a tuple of names (a column of small ones); a name is a tool's, one of the window's actions by
the end of its attribute's name ("new": act_new), or a dropdown ("classify", "type_lists", "phase", "panels")."""

from PySide6 import QtCore, QtGui, QtWidgets

from . import command_icons, theme

DISCIPLINES =("home", "modeling", "manage", "massing", "terrain", "architecture", "structure", "services",
               "collaborate", "annotate", "view", "render")
DEFAULT = "architecture"
OLD = {"concept": "massing", "bim": "architecture", "structure": "structure", "docs": "annotate"}   # (the 0.84 ones)
SHORTCUTS = {d: "Ctrl+{}".format(k + 1) for k, d in enumerate(DISCIPLINES[1:10])}
MENUS = ("classify", "type_lists", "phase", "panels")       # (dropdown buttons)

PANELS = {
    "home": (("file", ("new", "open", "save", "save_as", ("start_page", "new_from_base"))),     # (0.387)
             ("import", ("cad_link", "cloud_link", "import_image", "import_model", ("terrain_points", "terrain_dxf",
                                                                                    "import_components"))),
             ("export", ("pdf", "dxf", "export_image", "export_model", "export_presentation", "sheets_pdf",
                         ("sheets_by_storey", "splat"))),
             ("help", ("help", "quit"))),
    "modeling": (("select", ("select",)),
                 # (0.412) the work plane beside the curves; Offset with Modify, as Revit's (no column more: the
                 # owner's 1536 px keep the panels they had open)
                 ("draw", ("line", "arc", "rectangle", "circle", ("freehand", "bezier", "work_plane"), "push_pull")),
                 ("modify", ("move", "copy", "rotate", "mirror", ("array", "align", "scale"),
                             ("split_wall", "split_gap", "offset"), ("delete", "corner_walls", "trim_extend"),
                             ("wall_joins", "join_geometry", "unjoin_geometry"))),
                 ("clipboard", (("copy_clip", "paste", "paste_storeys"),)),            # (0.326, Revit's Clipboard)
                 ("measure", ("tape", "dimension")),
                 ("create", ("component_make", "group_make", ("classify", "materials")))),
    "manage": (("project", ("site_location", "phase")),
               ("storeys", ("storey_new", ("storey_up", "storey_down", "only_active"), ("repeat", "typical"))),
               ("types", ("types", "materials", "patterns", "type_lists")),
               ("components", ("component_make", "import_model", ("component_edit", "component_close",
                                                                  "import_components"))),
               ("groups", ("group_make", "group_ungroup")),
               ("ai", ("ai_link", "ai_install"))),
    "massing": (("select", ("select",)),
                ("image", ("import_image", "calibrate_image")),
                ("draw", ("line", "arc", "rectangle", "circle", ("freehand", "bezier", "work_plane"), "push_pull")),
                ("freeform", ("param_surface", "control_ring")),     # (0.395) the addon's «Superfícies Paramétricas»
                ("modify", ("move", "copy", "rotate", ("mirror", "align", "scale"), ("array", "offset"))),
                ("measure", ("tape",)),
                ("paint", ("paint",)),                                   # (0.391) SketchUp's Paint Bucket
                ("to_bim", ("classify", ("walls_from_cad", "model_from_scan")))),
    "terrain": (("select", ("select",)),
                ("location", ("site_location",)),
                ("survey", ("terrain_points", "terrain_dxf", "terrain")),
                ("platforms", ("platform", "terrain_ramp", "edit_platform")),
                ("earthworks", ("earthworks", "slopes"))),
    # (0.374) as the owner's study (proposta-interface-arqsynth.html): the walls' shapes in sight, the niche, the floor
    # finish, the gutter, the elevator, the room separators, identifying the rooms and their areas
    "architecture": (("select", ("select",)),
                     ("walls", ("wall", "curtain_wall", ("wall_rect", "wall_circle", "wall_arc"),
                                ("wall_face", "wall_wand", "curtain_panel"))),
                     ("openings", ("door", "window", ("wall_opening", "roof_opening", "niche"), ("caixilho", "renumber"))),
                     ("floors_roofs", ("slab", "roof", ("flooring", "ceiling", "gutter"),
                                      ("edit_outline", "roof_profile", "drain"))),
                     ("circulation", ("stair", "ramp", ("elevator", "railing", "railing_types"))),
                     ("rooms", ("room", ("room_separator", "rooms_identify", "areas"), ("room_program", "light"))),
                     ("finishes", ("paint", "perforated_panel", ("wall_finish", "wall_reveal", "profile"),
                                   ("wall_sweep", "profile_from_face"))),          # (0.389) the perforated panel
                     ("furniture", ("kitchen", "cabinet", ("worktop", "appliance", "cut_list")))),
    "structure": (("select", ("select",)),
                  ("grid", ("grid", ("grid_generate", "grid_settings", "columns_on_grid"))),
                  ("elements", ("footing", "column", "beam", "slab", ("wall", "param_surface"))),
                  ("automatic", ("propose_structure", ("footings_under", "combined_footing", "beams_between"),
                                 ("walls_under_beams", "slabs_in_bays", "beam_system"), ("remove_proposal",))),
                  ("analysis", ("analyse", ("analytical", "actions", "show_analytical"), ("moments", "verify_ec2"))),
                  ("documents", (("rebar_schedule", "structure_quantities", "calc_report"),))),
    "services": (("select", ("select",)),
                 ("water", ("fixture", "pipe", ("connect_network", "water_proposal", "remove_water_proposal"))),
                 ("hvac", ("duct", ("air_terminal", "equipment"))),
                 ("electrical", ("electrical", "conduit", ("light", "new_circuit", "route_circuits"),
                                 ("electrical_proposal", "remove_electrical_proposal", "electrical_check"))),
                 ("coordination", ("clashes",))),
    "collaborate": (("team", ("share", "open_shared", "sync", ("reserve_views", "give_back"))),
                    ("links", ("cad_link", "cloud_link", ("cad_links", "cloud_links", "walls_from_cad"))),
                    ("check", ("verify_panel", "clashes", ("check_ifc", "check_ids", "missing_data"),
                               ("verify_settings",))),
                    ("notes", ("new_note",))),
    "annotate": (("select", ("select",)),
                 ("views", ("plan", "section", ("last_section", "detail", "symbol_styles"))),
                 # (0.399) the one-click ones beside the manual one (C), as the owner asked
                 ("dimensions", ("dimension", "dim_exterior", "dim_interior", ("dimension_walls", "dimension_facades",
                                                                               "dimension_rooms"), ("dimension_style",))),
                 ("drafting", ("draft", ("tape",))),
                 ("tags", ("room", "renumber", "keynote_table"))),
    "view": (("views3d", ("iso", ("top", "front", "view3d_new"))),
             ("plans", ("plan", "section", ("last_section", "box", "box_selection"))),
             ("look", ("view_styles", "graphic_styles", "symbol_styles", "templates", "element_hatches",
                       ("images", "cad_links", "cloud_links"), ("show_analytical", "reset_patterns"))),
             # (0.376: the theme beside the looks — at the end it folded first, out of sight on a 1536 px screen)
             ("theme", (("theme_light", "theme_dark", "canvas_dark"),             # (0.338; 0.341)
                        ("theme_bege", "theme_pedra", "theme_revit"),             # (0.374: the owner's study's palettes)
                        ("theme_escuro", "theme_grafite", "theme_studio"))),
             ("camera", ("position_camera", ("look_around", "walk"))),
             ("windows", ("panels", ("next_view", "prev_view", "close_view"))),
             ("mouse", (("mouse_sketchup", "mouse_revit"),))),
    "render": (("present", ("render", "panorama", "export_image", "export_model", "presentation_panel",
                            "export_presentation", "splat", "view3d_new", "view_styles", "graphic_styles")),),
}

# (0.298) the contextual tabs, as Revit's "Modify | …": what they are for, and their panels
CONTEXTS = {
    # (the walls' own modifiers first, always in sight; the general ones — also on Modelling — last: the first to fold)
    "walls": (("wall_edit", ("flip_walls", "edit_profile", ("reset_profile", "attach_top", "detach_top"),
                             ("attach_base", "detach_base"))),
              ("wall_dims", (("dims_axes", "dims_faces"),)),     # (0.361) its relations' dimensions: axes or faces
              ("geometry", ("wall_joins", "merge_walls", ("join_wall_ends", "unjoin_walls", "orthogonalize"),
                            ("join_geometry", "unjoin_geometry"))),
              ("trim", (("split_wall", "split_gap"), ("corner_walls", "trim_extend"))),
              ("openings_finishes", (("door", "window", "wall_opening"), ("wall_finish", "wall_sweep", "wall_reveal"))),
              ("modify", ("move", "copy", "rotate", ("mirror", "align", "offset"), ("array", "scale", "delete"),
                          ("dimension_walls",)))),
}

# (0.338) the header's, the ribbon's colours: the theme's (ui/theme: "header", "accent" — the active discipline's —,
# "header_text", "bar", "context" — a contextual tab's, green as Revit's)
RIBBON_HEIGHT = 79          # (0.298) the same for every discipline (as tall as before): the views under it do not move


def panels_of(tab):
    """A discipline's (or a contextual tab's: "ctx:walls") panels."""
    return CONTEXTS[tab[4:]] if tab.startswith("ctx:") else PANELS[tab]


def items_of(tab):
    """The buttons of a discipline (or of a contextual tab), in order."""
    return [name for _key, items in panels_of(tab) for item in items
            for name in (item if isinstance(item, tuple) else (item,))]


def short_label(text):
    """A button's name under its icon: without its key and its dots, in two lines when long."""
    text = text.split("   (")[0].replace("…", "").strip()
    if len(text) <= 12 or " " not in text:
        return text
    words = text.split(" ")
    best = min(range(1, len(words)), key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
    return " ".join(words[:best]) + "\n" + " ".join(words[best:])


def small_label(text):
    """(0.298) A small button's name beside its icon: one line, without its key, its dots or what is in brackets."""
    text = text.split("   (")[0].replace("…", "").replace("\n", " ").strip()
    if "(" in text and not text.startswith("("):
        text = text[:text.index("(")].strip()
    return text


# ------------------------------------------------------------ icons drawn in white, for the header

def _canvas(size=20, colour=None):
    pm = QtGui.QPixmap(size, size)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    pen = QtGui.QPen(colour if colour is not None else theme.colour("header_text"), 1.6)
    pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    return pm, p


def header_icon(kind, colour=None):
    """A small white glyph: "home", "save", "undo", "redo", "sync", "help" — (0.403) or in `colour` (the views' tabs'
    house, in the text's colour of the theme)."""
    pm, p = _canvas(colour=colour)
    if kind == "home":
        p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(3, 10), QtCore.QPointF(10, 3.5), QtCore.QPointF(17, 10)]))
        p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(5, 9), QtCore.QPointF(5, 16.5), QtCore.QPointF(15, 16.5),
                                        QtCore.QPointF(15, 9)]))
        p.drawRect(QtCore.QRectF(8.5, 11.5, 3, 5))
    elif kind == "save":
        p.drawRoundedRect(QtCore.QRectF(3.5, 3.5, 13, 13), 1.5, 1.5)
        p.drawRect(QtCore.QRectF(6.5, 3.5, 7, 4.5))
        p.drawRect(QtCore.QRectF(6, 11, 8, 5.5))
    elif kind in ("undo", "redo"):
        path = QtGui.QPainterPath(QtCore.QPointF(5, 8))
        path.cubicTo(9, 4, 16, 6, 16, 12)
        path.cubicTo(16, 15, 13, 16.5, 10, 16.5)
        if kind == "redo":
            path = QtGui.QTransform(-1, 0, 0, 1, 20, 0).map(path)
        p.drawPath(path)
        tip = (5, 8) if kind == "undo" else (15, 8)
        s = 1 if kind == "undo" else -1
        p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(tip[0] + s * 4, tip[1] - 3.5), QtCore.QPointF(*tip),
                                        QtCore.QPointF(tip[0] + s * 4.5, tip[1] + 2.5)]))
    elif kind == "sync":
        path = QtGui.QPainterPath(QtCore.QPointF(5, 15))
        path.cubicTo(1.5, 15, 1.5, 9.5, 5.5, 9.5)
        path.cubicTo(6, 5, 13, 4.5, 14, 8.5)
        path.cubicTo(18.5, 8.5, 18.5, 15, 15, 15)
        path.closeSubpath()
        p.drawPath(path)
    elif kind == "help":
        p.drawEllipse(QtCore.QPointF(10, 10), 7, 7)
        path = QtGui.QPainterPath(QtCore.QPointF(7.5, 8))
        path.cubicTo(7.5, 4.8, 12.5, 4.8, 12.5, 8)
        path.cubicTo(12.5, 10, 10, 10, 10, 12)
        p.drawPath(path)
        p.drawPoint(QtCore.QPointF(10, 14.5))
    elif kind == "theme":                            # (0.376) a painter's palette: the interface's colours
        path = QtGui.QPainterPath(QtCore.QPointF(10, 3))
        path.cubicTo(15, 3, 17.5, 6.5, 17, 9.5)
        path.cubicTo(16.5, 12, 13, 11, 12.5, 13)
        path.cubicTo(12, 15.5, 13.5, 17, 10, 17)
        path.cubicTo(5, 17, 2.5, 13.5, 2.5, 10)
        path.cubicTo(2.5, 6, 5.5, 3, 10, 3)
        p.drawPath(path)
        for x, y in ((6.5, 8), (10, 6.2), (13.5, 7.5), (6.5, 12.5)):
            p.drawEllipse(QtCore.QPointF(x, y), 1.1, 1.1)
    p.end()
    return QtGui.QIcon(pm)


def _sheet(p, label=None, fold=True):
    """A sheet of paper (its corner folded), a short label on it."""
    path = QtGui.QPainterPath(QtCore.QPointF(8, 4))
    path.lineTo(19, 4)
    path.lineTo(24, 9)
    path.lineTo(24, 28)
    path.lineTo(8, 28)
    path.closeSubpath()
    p.setBrush(QtGui.QColor("#ffffff"))
    p.drawPath(path)
    if fold:
        p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(19, 4), QtCore.QPointF(19, 9), QtCore.QPointF(24, 9)]))
    if label:
        font = p.font()
        font.setBold(True)
        font.setPixelSize(7)
        p.setFont(font)
        p.setPen(QtGui.QColor("#c0392b" if label == "PDF" else "#2f6fe4"))
        p.drawText(QtCore.QRectF(5, 15, 22, 9), QtCore.Qt.AlignmentFlag.AlignCenter, label)


def command_icon(name):
    """(0.182) The icons of the commands that had none, drawn as the tools' (a dark outline, a blue mark): the
    file's (new, open, save, save as), the exports (PDF, DXF, sheets, splat), help and quit — None for the rest."""
    drawn = ("new", "open", "save", "save_as", "pdf", "dxf", "sheets_pdf", "sheets_by_storey", "splat", "help",
             "quit", "terrain_dxf", "import_components", "start_page", "new_from_base")
    if name not in drawn:
        return command_icons.icon(name)                   # (0.298: the others that had only their initials)
    pm = QtGui.QPixmap(32, 32)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    ink = QtGui.QPen(QtGui.QColor(command_icons.INK), 1.4)
    ink.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
    blue = QtGui.QPen(QtGui.QColor(command_icons.BLUE), 2.0)
    blue.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
    p.setPen(ink)
    if name == "new":
        _sheet(p)
        p.setPen(blue)
        p.drawLine(QtCore.QPointF(16, 13), QtCore.QPointF(16, 23))
        p.drawLine(QtCore.QPointF(11, 18), QtCore.QPointF(21, 18))
    elif name == "start_page":                     # (0.387) a house: the program's own page
        p.setBrush(QtGui.QColor("#ffffff"))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(7, 15), QtCore.QPointF(16, 6), QtCore.QPointF(25, 15),
                                       QtCore.QPointF(25, 27), QtCore.QPointF(7, 27)]))
        p.setPen(blue)
        p.drawLine(QtCore.QPointF(4, 17), QtCore.QPointF(16, 5))
        p.drawLine(QtCore.QPointF(16, 5), QtCore.QPointF(28, 17))
        p.setPen(ink)
        p.drawRect(QtCore.QRectF(13.5, 19, 5, 8))
    elif name == "new_from_base":                  # (0.387) a sheet taken from another under it
        p.setBrush(QtGui.QColor("#dfe8f6"))
        p.drawRect(QtCore.QRectF(4, 8, 16, 20))
        _sheet(p)
        p.setPen(blue)
        p.drawLine(QtCore.QPointF(12, 15), QtCore.QPointF(20, 15))
        p.drawLine(QtCore.QPointF(12, 19), QtCore.QPointF(20, 19))
        p.drawLine(QtCore.QPointF(12, 23), QtCore.QPointF(17, 23))
    elif name == "open":
        p.setBrush(QtGui.QColor("#f3d27a"))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(4, 9), QtCore.QPointF(12, 9), QtCore.QPointF(14, 11),
                                       QtCore.QPointF(26, 11), QtCore.QPointF(26, 25), QtCore.QPointF(4, 25)]))
        p.setBrush(QtGui.QColor("#f7e2a6"))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(7, 15), QtCore.QPointF(29, 15), QtCore.QPointF(26, 25),
                                       QtCore.QPointF(4, 25)]))
    elif name in ("save", "save_as"):
        p.setBrush(QtGui.QColor("#dfe8f6"))
        p.drawRoundedRect(QtCore.QRectF(5, 5, 22, 22), 2, 2)
        p.setBrush(QtGui.QColor("#ffffff"))
        p.drawRect(QtCore.QRectF(10, 5, 12, 7))
        p.drawRect(QtCore.QRectF(9, 17, 14, 10))
        if name == "save_as":
            p.setPen(blue)
            p.drawLine(QtCore.QPointF(19, 27), QtCore.QPointF(28, 18))
    elif name in ("pdf", "dxf", "terrain_dxf"):
        _sheet(p, "PDF" if name == "pdf" else "DXF")
        if name == "terrain_dxf":
            p.setPen(blue)
            p.drawArc(QtCore.QRectF(10, 20, 12, 8), 0, 180 * 16)
    elif name in ("sheets_pdf", "sheets_by_storey"):
        p.save()
        p.translate(-3, 2)
        _sheet(p, fold=False)
        p.restore()
        _sheet(p, "PDF" if name == "sheets_pdf" else None)
        if name == "sheets_by_storey":
            p.setPen(blue)
            for y in (14, 19, 24):
                p.drawLine(QtCore.QPointF(11, y), QtCore.QPointF(21, y))
    elif name == "splat":
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        for (x, y, r, c) in ((10, 12, 4.5, "#e07b5a"), (19, 9, 4.0, "#7ab0e0"), (22, 19, 5.0, "#9ccc7a"),
                             (13, 22, 4.5, "#e8c45a"), (16, 15, 3.5, "#b48ad6")):
            colour = QtGui.QColor(c)
            colour.setAlpha(200)
            p.setBrush(colour)
            p.drawEllipse(QtCore.QPointF(x, y), r, r * 0.7)
    elif name == "help":
        p.setBrush(QtGui.QColor("#eef2f8"))
        p.drawEllipse(QtCore.QPointF(16, 16), 11, 11)
        p.setPen(blue)
        path = QtGui.QPainterPath(QtCore.QPointF(12, 13))
        path.cubicTo(12, 7.5, 20, 7.5, 20, 13)
        path.cubicTo(20, 16, 16, 16, 16, 19)
        p.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.drawPoint(QtCore.QPointF(16, 23))
    elif name == "quit":
        p.drawRect(QtCore.QRectF(6, 5, 12, 22))
        p.setPen(blue)
        p.drawLine(QtCore.QPointF(14, 16), QtCore.QPointF(28, 16))
        p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(24, 12), QtCore.QPointF(28, 16), QtCore.QPointF(24, 20)]))
    elif name == "import_components":
        p.setBrush(QtGui.QColor("#e9dcc9"))
        p.drawPolygon(QtGui.QPolygonF([QtCore.QPointF(11, 13), QtCore.QPointF(19, 9), QtCore.QPointF(27, 13),
                                       QtCore.QPointF(27, 23), QtCore.QPointF(19, 27), QtCore.QPointF(11, 23)]))
        p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(11, 13), QtCore.QPointF(19, 17), QtCore.QPointF(27, 13)]))
        p.drawLine(QtCore.QPointF(19, 17), QtCore.QPointF(19, 27))
        p.setPen(blue)
        p.drawLine(QtCore.QPointF(3, 18), QtCore.QPointF(10, 18))
        p.drawPolyline(QtGui.QPolygonF([QtCore.QPointF(7, 15), QtCore.QPointF(10, 18), QtCore.QPointF(7, 21)]))
    p.end()
    return theme.icon(pm)


def stand_in_icon(text):
    """An icon for a command that has none: its initials in a rounded square (blue), as the others' size."""
    pm = QtGui.QPixmap(32, 32)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.setPen(QtGui.QPen(QtGui.QColor("#5b6b80"), 1.4))
    p.setBrush(QtGui.QColor("#eef2f8"))
    p.drawRoundedRect(QtCore.QRectF(4, 4, 24, 24), 5, 5)
    words = [w for w in text.split("   (")[0].replace("…", "").replace("(", " ").split() if len(w) > 2 or w.isupper()]
    letters = "".join(w[0] for w in words[:2]).upper() or text[:1].upper()
    font = p.font()
    font.setBold(True)
    font.setPixelSize(11 if len(letters) > 1 else 14)
    p.setFont(font)
    p.setPen(QtGui.QColor(command_icons.BLUE))
    p.drawText(QtCore.QRectF(4, 4, 24, 24), QtCore.Qt.AlignmentFlag.AlignCenter, letters)
    p.end()
    return theme.icon(pm)


# ------------------------------------------------------------ the header

class Header(QtWidgets.QWidget):
    """Panel 1: the logo, the disciplines' tabs, the project's name and the global commands."""

    def __init__(self, parent, logo, labels, tips, on_discipline, commands):
        """labels / tips: {discipline: text}; commands: [(kind, tooltip, callback)] on the right."""
        super().__init__(parent)
        self.setObjectName("header")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(header_style())
        self.setProperty("context", False)
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(8, 0, 8, 0)
        row.setSpacing(2)
        mark = QtWidgets.QLabel()
        mark.setPixmap(logo.pixmap(26, 26))
        row.addWidget(mark)
        self.brand = QtWidgets.QLabel("ArqSynth BIM")
        self.brand.setObjectName("brand")
        row.addWidget(self.brand)
        self.tabs = QtWidgets.QTabBar()
        self.tabs.setDrawBase(False)
        self.tabs.setExpanding(False)
        self.tabs.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        # (0.298) all the tabs always in sight: short of room, their names shortened, not scrolled away
        self.tabs.setUsesScrollButtons(False)
        self.tabs.setElideMode(QtCore.Qt.TextElideMode.ElideRight)
        for d in DISCIPLINES:
            if d == "home":                                   # (the house, as on the drawing)
                i = self.tabs.addTab(header_icon("home"), "")
            else:
                i = self.tabs.addTab(labels[d])
            self.tabs.setTabToolTip(i, "{}\n{}".format(labels[d], tips[d]))
        self.context = None                                   # (0.298) the contextual tab's key, or None
        self.tabs.currentChanged.connect(
            lambda i: on_discipline(DISCIPLINES[i] if i < len(DISCIPLINES) else "ctx:" + self.context))
        row.addWidget(self.tabs, 1)
        self.project = QtWidgets.QLabel()
        self.project.setObjectName("project")
        self.project.setMinimumWidth(1)                      # (0.298: it gives way to the tabs)
        row.addWidget(self.project)
        self.buttons = {}
        for kind, tip, callback in commands:
            button = QtWidgets.QToolButton()
            button.setIcon(header_icon(kind))
            button.setIconSize(QtCore.QSize(20, 20))
            button.setToolTip(tip)
            button.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
            button.clicked.connect(callback)
            row.addWidget(button)
            self.buttons[kind] = button
        self.setFixedHeight(35)

    def restyle(self):
        """(0.338) In the theme in use: its colours, its glyphs drawn again in its text's colour."""
        self.setStyleSheet(header_style())
        self.tabs.setTabIcon(DISCIPLINES.index("home"), header_icon("home"))
        for kind, button in self.buttons.items():
            button.setIcon(header_icon(kind))

    def show_discipline(self, discipline):
        """The tab of a discipline (or the contextual one: "ctx:walls") lit, without saying so."""
        i = len(DISCIPLINES) if discipline.startswith("ctx:") else DISCIPLINES.index(discipline)
        if self.tabs.currentIndex() != i and i < self.tabs.count():
            blocker = QtCore.QSignalBlocker(self.tabs)
            self.tabs.setCurrentIndex(i)
            del blocker

    def set_context(self, key, label=None, tip=None):
        """(0.298) The contextual tab at the end of the tabs (key "walls", its label "Modify | Walls"), or none (key
        None). The tab lit stays the one it was, unless it was the contextual one going away."""
        blocker = QtCore.QSignalBlocker(self.tabs)
        n = len(DISCIPLINES)
        current = self.tabs.currentIndex()
        if key is None:
            if self.tabs.count() > n:
                self.tabs.removeTab(n)
        elif self.tabs.count() > n:
            self.tabs.setTabText(n, label)
        else:
            self.tabs.addTab(label)
        if key is not None:
            self.tabs.setTabToolTip(n, tip or label)
        self.context = key
        if current < self.tabs.count() and self.tabs.currentIndex() != current:
            self.tabs.setCurrentIndex(current)
        del blocker
        self.fit()
        if bool(self.property("context")) != (key is not None):
            self.setProperty("context", key is not None)
            self.style().unpolish(self)
            self.style().polish(self)
            for w in self.findChildren(QtWidgets.QWidget):
                self.style().unpolish(w)
                self.style().polish(w)
            self.update()

    def set_project(self, text):
        self.project.setText(text)
        self.fit()

    def fit(self):
        """(0.298) Short of room, the program's name beside the symbol goes first, then the project's (the window's
        title has both), so that the tabs keep theirs whole."""
        row = self.layout()
        margins = row.contentsMargins()
        fixed = (margins.left() + margins.right() + 26 + row.spacing() * (len(self.buttons) + 4)
                 + sum(b.sizeHint().width() for b in self.buttons.values()))
        spare = self.width() - fixed - self.tabs.sizeHint().width()
        brand, project = self.brand.sizeHint().width(), self.project.sizeHint().width()
        self.project.setVisible(spare >= project)
        self.brand.setVisible(spare >= project + brand)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()


class RibbonButton(QtWidgets.QToolButton):
    """(0.298) A ribbon button that keeps its own short name and icon when its action changes (checked, enabled, its
    tooltip): Qt would put the action's long name and empty icon back."""

    def keep(self):
        self._kept = (self.text(), self.icon())

    def actionEvent(self, event):
        super().actionEvent(event)
        kept = getattr(self, "_kept", None)
        if kept is not None and event.type() == QtCore.QEvent.Type.ActionChanged:
            self.setText(kept[0])
            self.setIcon(kept[1])


class Panel(QtWidgets.QWidget):
    """(0.298) A named panel of the ribbon, as Revit's: its buttons — large ones, and columns of up to three small
    ones — over its name; or, when the ribbon is short of room, folded into one button with its name that drops its
    tools down."""

    def __init__(self, title, columns, icon, entries, parent=None):
        """columns: in order, a QToolButton (a large one) or a list of them (a column of small ones); icon: the folded
        button's; entries: the folded button's menu — QActions, or QMenus (shown as submenus)."""
        super().__init__(parent)
        self.setObjectName("ribbon_panel")
        self.full = QtWidgets.QWidget(self)
        box = QtWidgets.QVBoxLayout(self.full)
        box.setContentsMargins(1, 0, 1, 0)
        box.setSpacing(0)
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(1)
        for column in columns:
            if isinstance(column, list):
                stack = QtWidgets.QVBoxLayout()
                stack.setSpacing(0)
                for button in column:
                    stack.addWidget(button, 0, QtCore.Qt.AlignmentFlag.AlignLeft)
                stack.addStretch(1)
                row.addLayout(stack)
            else:
                row.addWidget(column, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        box.addLayout(row, 1)
        self.title = QtWidgets.QLabel(title)
        self.title.setObjectName("panel_title")
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        box.addWidget(self.title)
        self.folded = QtWidgets.QToolButton(self)
        self.folded.setObjectName("panel_folded")
        self.folded.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.folded.setIconSize(QtCore.QSize(30, 30))
        self.folded.setIcon(icon)
        self.folded.setText(short_label(title) + " ▾")
        self.folded.setPopupMode(QtWidgets.QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QtWidgets.QMenu(self.folded)
        for entry in entries:
            menu.addAction(entry.menuAction() if isinstance(entry, QtWidgets.QMenu) else entry)
        self.folded.setMenu(menu)
        self.folded.hide()
        outer = QtWidgets.QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self.full)
        outer.addWidget(self.folded, 0, QtCore.Qt.AlignmentFlag.AlignTop)

    def is_folded(self):
        return not self.folded.isHidden()

    def fold(self, folded):
        self.full.setVisible(not folded)
        self.folded.setVisible(folded)

    def width_for(self, folded):
        return (self.folded if folded else self.full).sizeHint().width()


class Ribbon(QtWidgets.QWidget):
    """(0.298) The ribbon's panels in a row, as wide as the window lets them be: when they do not fit, those on the
    right fold one by one into a button each (the first ones, the most used, stay open)."""

    GAP = 7                         # (a thin line between two panels, and its margins)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ribbon_panels")
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        self.setFixedHeight(RIBBON_HEIGHT - 4)
        self.row = QtWidgets.QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(0)
        self.panels = []

    def sizeHint(self):                 # (the toolbar gives it the room there is: it never asks for more)
        return QtCore.QSize(200, self.height())

    def minimumSizeHint(self):
        return QtCore.QSize(100, self.height())

    def show_panels(self, panels):
        """These panels instead of those shown (taken down)."""
        while self.row.count():
            widget = self.row.takeAt(0).widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)                  # (out of the ribbon now, not when Qt gets round to it)
                widget.deleteLater()
        for i, panel in enumerate(panels):
            if i:
                line = QtWidgets.QFrame(self)
                line.setObjectName("panel_line")
                line.setFrameShape(QtWidgets.QFrame.Shape.VLine)
                line.setFixedWidth(self.GAP)
                self.row.addWidget(line)
            self.row.addWidget(panel)
        self.row.addStretch(1)
        self.panels = panels
        self.fit()

    def fit(self):
        """Open as many panels as fit, from the left; fold the others."""
        if not self.panels:
            return
        room = self.width() - self.GAP * (len(self.panels) - 1) - 4
        full = [p.width_for(False) for p in self.panels]
        small = [p.width_for(True) for p in self.panels]
        total, folded = sum(full), [False] * len(self.panels)
        for i in range(len(self.panels) - 1, -1, -1):
            if total <= room:
                break
            total -= full[i] - small[i]
            folded[i] = True
        for panel, f in zip(self.panels, folded):
            panel.fold(f)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()


def header_style():
    """The header's look (0.338: the theme's): its tabs, the active discipline's lit, the contextual one green."""
    c = theme.C
    return ("#header { background: %s; }"
            "QLabel { color: %s; }"
            "QLabel#brand { font-size: 15px; font-weight: 700; padding: 0 8px 0 4px; }"
            "QLabel#project { padding: 0 12px; }"
            "QToolButton { border: none; padding: 5px; border-radius: 4px; color: %s; }"
            "QToolButton:hover { background: rgba(255, 255, 255, 0.12); }"
            "QTabBar::tab { color: %s; background: transparent; padding: 7px 8px; border: none; border-top: 2px solid transparent; }"
            "QTabBar::tab:hover:!selected { background: rgba(255, 255, 255, 0.10); }"
            "QTabBar::tab:selected { background: %s; color: %s; font-weight: 600; border-top: 2px solid %s; }"
            # (0.298) the contextual tab, the last one while there is one: green
            "#header[context=\"true\"] QTabBar::tab:last { color: %s; font-weight: 600; }"
            "#header[context=\"true\"] QTabBar::tab:last:selected { background: %s; color: white; }"
            % (c["header"], c["header_text"], c["header_text"], c["header_text"], c["bar"], c["text"], c["accent"],
               c["context_text"], c["context"]))


def header_bar_style():
    """(0.338) The toolbar the header sits in: the header's colour, edge to edge."""
    return ("QToolBar#header_bar { background: %s; border: none; padding: 0; spacing: 0; }"
            % theme.C["header"])


def ribbon_style():
    """The ribbon's look: large buttons, the active tool lit, the panels' names under them (0.338: the theme's)."""
    c = theme.C
    return ("QToolBar#ribbon { background: %s; border: none; border-bottom: 1px solid %s; spacing: 0px;"
            " padding: 2px 4px 1px 4px; }"
            "QToolBar#ribbon QToolButton { padding: 2px 3px; border-radius: 4px; color: %s; font-size: 11px; }"
            "QToolBar#ribbon QToolButton[small=\"true\"] { padding: 1px 4px 1px 2px; }"
            "QToolBar#ribbon QToolButton:hover { background: %s; }"
            "QToolBar#ribbon QToolButton:checked { background: %s; border: 1px solid %s; }"
            "QToolBar#ribbon QToolButton#panel_folded::menu-indicator { image: none; width: 0px; }"
            "QToolBar#ribbon QLabel#panel_title { color: %s; font-size: 10px; padding: 0px; }"
            "QToolBar#ribbon QFrame#panel_line { color: %s; margin: 4px 3px 4px 3px; }"
            % (c["bar"], c["line"], c["text"], c["button_hover"], c["select_soft"], c["select_border"], c["muted"],
               c["line"]))
