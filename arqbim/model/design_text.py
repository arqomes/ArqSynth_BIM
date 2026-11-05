"""The words of the structural design (0.166–0.167): a member's notes (core.ec2.Note: a code and its numbers) and its
reinforcement written in the program's language, numbers with its decimal separator — for the verification window
and the calculation report alike (no Qt here)."""

import re

from ..core import ec2
from ..i18n import decimal_sep, t

KIND_ORDER = {"column": 0, "beam": 1, "slab": 2, "footing": 3, "wall": 4}
MAIN_NOTES = ("interaction", "bearing", "bending", "mesh")


# (code, value) -> how it is shown: decimals, or "cm2" (m² as cm²), "mm" (m as mm), "pct", "face", "int", "spacing"
_FORMATS = {"mu": 3, "need": "cm2", "area": "cm2", "as_min": "cm2", "s": "spacing", "d": "int", "n_bars": "int",
            "lam": 0, "sigma": 0, "soil": 0, "e0": 2, "ex": 2, "ey": 2, "h": 2, "f": "mm", "allowed": "mm", "p": 2,
            "cot": 1, "side": 2, "ratio": 1, "face": "face", "n1": "int", "n2": "int", "depth": 3, "shape": "shape",
            "stress": 1, "theta": 0, "low": 0, "high": 0, "kept": "int", "extra": "int", "zones": "text", "al": 2,
            "lbd": 2, "span": 2, "width": 2,
            # (0.337) the walls' (core/ec6.py)
            "fb": 1, "fk": 2, "fd": 2, "gm": 1, "mortar": "text", "slender": 1, "spot": "spot", "nrd": 1, "phi": 2,
            "ecc": "mm", "vrd": 1, "fvk": 2, "sig": 2, "len": 2, "sign": "text",
            # (0.342) the concrete walls' (core/ec2.wall)
            "m2": 1, "vmax": 1,
            # (0.345) the façade walls' bending out of their plane (core/ec6.lateral)
            "f1": 2, "f2": 2, "fd1": 3, "fd2": 3, "ortho": 2, "qp": 2, "c": 1, "z": 1, "open": 2, "w": 2,
            "edges": "edges", "me1": 2, "me2": 2, "mr1": 2, "mr2": 2, "alpha": 3, "q": 2, "ht": 1,
            # (0.346) a wall's masonry: its type's or the project's
            "unit": "unit", "group": "text", "src": "src"}
_LIMITS = {"bending_too_much": "cm2", "rigid": 2, "flexible": 2, "punching": 2, "punching_face": 2,
           "node_column": 1, "node_pile": 1, "combined_shear": 2}
_SPECIAL = {("interaction", "ratio"): "pct", ("bars_do_not_fit", "n"): "int", ("bending", "n"): "int",
            ("pile_cap", "n"): "int", ("pile_cap_other", "n"): "int",                  # (0.228: its piles)
            ("typical", "n"): "int", ("combined_shear", "v"): 2, ("combined", "n1"): 0,
            ("combined", "n2"): 0,                                                     # (0.250)
            ("wall_compression", "ratio"): "pct", ("wall_slender", "lam"): 0, ("wall_slender", "limit"): 0,
            ("wall_shear_bars", "need"): "cm2"}                                        # (0.342)


def num(v, d=1):
    return ("{:." + str(d) + "f}").format(float(v)).replace(".", decimal_sep())


def natural(text):
    """«Pilar 2» before «Pilar 10»."""
    return [(0, int(p), "") if p.isdigit() else (1, 0, p.lower()) for p in re.split(r"(\d+)", text)]


def spacing_text(s):
    """0,175 · 0,25 · 0,20: centimetres, the millimetres only when there are some."""
    text = num(s, 3)
    return text[:-1] if text.endswith("0") else text


def _value(code, key, v):
    how = _SPECIAL.get((code, key)) or (_LIMITS.get(code, 1) if key == "limit" else _FORMATS.get(key, 1))
    if how == "face":
        return t("ec2.face." + str(v))
    if how == "shape":                                  # (0.227: a column's section)
        return t("ec2.shape." + str(v))
    if how == "spot":                                   # (0.337: where in a wall: top, mid-height, base)
        return t("ec6.spot." + str(v))
    if how == "edges":                                  # (0.345: the edges a façade panel is held on)
        return t("ec6.edges." + str(v))
    if how in ("unit", "src"):                          # (0.346: a wall's masonry, and whose it is)
        return t("ec6.{}.{}".format(how, v))
    if how == "text":                                   # (0.229: written already — its decimals the program's)
        return str(v).replace(".", decimal_sep())
    if how == "int":
        return str(int(v))
    if how == "cm2":
        return num(float(v) * 1e4, 2)
    if how == "mm":
        return num(float(v) * 1000.0, 1)
    if how == "pct":
        return "{:.0f} %".format(100.0 * float(v))
    if how == "spacing":
        return spacing_text(v)
    if isinstance(v, bool):
        return str(v)
    return num(v, how)


def note_text(note):
    return t("ec2.note." + note.code, **{k: _value(note.code, k, v) for k, v in note.values.items()})


def _bar(n_d):
    return "{} Ø{}".format(int(n_d[0]), int(n_d[1]))


def _spaced(d_s):
    return "Ø{}//{}".format(int(d_s[0]), spacing_text(d_s[1]))


def bars_text(kind, d):
    """The reinforcement adopted, in a few words."""
    if kind == "beam" and d.bottom and d.top and d.links:
        def layered(bars, second):                      # (0.225: in two layers, «6 Ø16 (4 + 2)»)
            return _bar(bars) + (" ({} + {})".format(int(bars[0]) - second, second) if second else "")
        return t("ec2.bars.beam", b=layered(d.bottom, getattr(d, "bottom2", 0)),
                 t=layered(d.top, getattr(d, "top2", 0)), l=_spaced(d.links))
    if kind == "column" and d.bars and d.links:
        return t("ec2.bars.column", b=_bar(d.bars), l=_spaced(d.links))
    if kind == "slab" and d.mesh_x and d.mesh_y and getattr(d, "top_x", None) and getattr(d, "top_y", None):
        return t("ec2.bars.slab_top", x=_spaced(d.mesh_x), y=_spaced(d.mesh_y), tx=_spaced(d.top_x),
                 ty=_spaced(d.top_y))                                   # (0.224: its top bars over the supports)
    if kind in ("footing", "slab") and d.mesh_x and d.mesh_y:
        return t("ec2.bars." + kind, x=_spaced(d.mesh_x), y=_spaced(d.mesh_y))
    if kind == "wall" and getattr(d, "vertical", None) and getattr(d, "horizontal", None):     # (0.342: concrete)
        return t("ec2.bars.wall", v=_spaced(d.vertical), h=_spaced(d.horizontal))
    return "—"


def _wall_use(note):
    """(0.337) A wall's check's utilisation: NEd / NRd, VEd / VRd (-1 for its other notes)."""
    v = note.values
    if note.code == "ec6_compression":
        return v["n"] / v["nrd"] if v["nrd"] > 1e-9 else float("inf")
    if note.code in ("ec6_shear", "wall_shear"):
        return v["v"] / v["vrd"] if v["vrd"] > 1e-9 else float("inf")
    if note.code == "wall_compression":                 # (0.342: a concrete wall's)
        return v["ratio"]
    if note.code == "wall_shear_bars":
        return v["v"] / v["vmax"] if v["vmax"] > 1e-9 else float("inf")
    if note.code == "ec6_lateral":                      # (0.345: out of its plane, by the wind…
        return v["me2"] / v["mr2"] if v["mr2"] > 1e-12 else float("inf")
    if note.code == "ec6_arch":                         # …or its arch, held at its top)
        return v["w"] / v["q"] if v["q"] > 1e-12 else float("inf")
    return -1.0


def error_text(error):
    """(0.345) An analysis's error in words: its code's text (analysis.err.<code>), else as it came (a solver's)."""
    from ..i18n import has
    key = "analysis.err." + str(error)
    return t(key) if has(key) else str(error)


def masonry(e):
    """(0.342) An ElementDesign of a masonry wall (EC6: no bars) — not a concrete one (EC2: its bars)?"""
    return e.kind == "wall" and getattr(e.design, "vertical", None) is None and \
        any(n.code.startswith("ec6") for n in e.design.notes)


def masonry_fk(designs, settings):
    """(0.346) The masonry's fk of these designs' walls as text: one value, or «least a most» when their types have
    masonry of their own (the project's when none says)."""
    from ..core import ec6
    found = sorted({round(n.values["fk"], 2) for e in designs if masonry(e) for n in e.design.notes
                    if n.code in ("ec6_material", "ec6_flexural") and "fk" in n.values})
    if not found:
        return num(ec6.strength(settings)[0], 2)
    return num(found[0], 2) if len(found) == 1 else t("ec6.fk_range", a=num(found[0], 2), b=num(found[-1], 2))


def main_note(design):
    """What governs a member: its worst note when it is not OK, else its main result (the bars of its bending, its
    N–M diagram, its soil pressure; (0.337) a wall's most used check)."""
    if design.status != ec2.OK:
        return design.worst()
    if design.kind == "wall":
        return max(design.notes, key=_wall_use, default=None)
    return next((n for n in design.notes if n.code in MAIN_NOTES), None)


def ordered(designs, names):
    """The designs columns first, then beams, slabs, footings, each by name."""
    return sorted(designs, key=lambda e: (KIND_ORDER.get(e.kind, 9), natural(names.get(e.guid, e.guid))))


def second_order_text(analysis):
    """(0.222) The sentence of an Analysis's second order: its largest θ, where, and what it asks ("" when it has no
    horizontal action)."""
    from .structure_analysis import sway_verdict
    theta, worst = analysis.theta()
    if worst is None:
        return ""
    amps = ", ".join(t("analysis.sway.amp", case=t("analysis.case." + c), f=num(f, 2))
                     for c, f in analysis.amplification.items())
    return t("analysis.second_order", theta=num(theta, 3), case=t("analysis.case." + worst.case),
             level=num(worst.level, 2), verdict=t("analysis.sway." + sway_verdict(theta), amps=amps or "—"))


def panel_values(panel, name):
    """(0.223) A slab analysed as a shell as a line of the analysis's table: (element, its shorter span, —, —, —,
    M span x / y, M support x / y, its deflection (mm, L/…), the combination)."""
    defl = ""
    if panel.deflection > 1e-9:
        defl = "{} mm (L/{:.0f})".format(num(panel.deflection * 1000, 1), panel.span / panel.deflection)
    return (name, num(panel.span, 2), "", "", "", t("analysis.slab_moments", x=num(panel.m_x), y=num(panel.m_y)),
            t("analysis.slab_moments", x=num(panel.m_x_top), y=num(panel.m_y_top)), defl, panel.combo)


def wall_values(wall, name):
    """(0.336) A load-bearing wall (model.wall_loads.WallLoad) as a line of the analysis's table: (element, its
    length, the compression on each metre at its base — ULS 1,35G+1,50Q and G alone —, the largest horizontal force
    it takes — the wind × 1,5, the earthquake × 1 —, —, —, —, from which action)."""
    net = max(wall.net, 1e-9)
    uls = (1.35 * wall.base_g + 1.5 * wall.base_q) / net
    shears = {case: v * (1.5 if case.startswith("W") else 1.0) for case, v in wall.shear.items()}
    case = max(shears, key=shears.get, default="")
    return (t("analysis.wall_name", name=name), num(wall.length, 2), num(-uls), num(-wall.base_g / net),
            num(shears.get(case, 0.0)), "", "", "", t("analysis.wall_case", case=case) if case else "")


def sway_rows(analysis):
    """(0.222) Each storey's sway as text, by action: (action, storey, h, P, V, dr mm, θ, what it asks) and the
    verdict's key."""
    from .structure_analysis import sway_verdict
    return [((t("analysis.case." + s.case), num(s.level, 2), num(s.height, 2), num(s.p), num(s.v),
              num(s.drift * 1000, 1), num(s.theta, 3), t("analysis.sway.short." + sway_verdict(s.theta))),
             sway_verdict(s.theta)) for s in analysis.sways]
