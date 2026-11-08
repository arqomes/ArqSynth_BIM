"""Curves changed after they were drawn (0.373): an arc by its grips (its ends, its middle) or its Properties (radius,
angle, segments); a Bézier curve by the grips of its points and tangents. The curve's lines are made again from its
data; the loose lines whose ends were at its ends follow them (model/line_edit). One undo step."""

import numpy as np

from ..core import curves
from ..core.mesh import PolyMesh
from ..core.sketch_geometry import transform_point
from ..i18n import t
from . import line_edit
from .document import JoinedCommand, ReplaceMeshes, ReplaceObjects, SketchObject


def _ends(obj):
    """The curve's two ends (world), where lines joined to it are."""
    pts = curves.curve_points(obj.curve)
    if not pts or curves.is_closed(obj.curve):
        return []
    if obj.curve.get("pie"):
        pts = pts[1:]
    return [transform_point(obj.matrix, pts[0]), transform_point(obj.matrix, pts[-1])]


def remade(obj, curve):
    """The sketch with its lines made from `curve` (its data, in the sketch's frame)."""
    pts = curves.curve_points(curve)
    closed = curves.is_closed(curve)
    pairs = [(k, k + 1) for k in range(len(pts) - 1)] + ([(len(pts) - 1, 0)] if closed and len(pts) > 2 else [])
    return SketchObject(obj.name, obj.matrix, PolyMesh(pts, lines=pairs), obj_id=obj.id, component=obj.component,
                        curve=curve)


def reshape(doc, obj_id, curve, label=None):
    """The curve `obj_id` made as `curve` says; the loose lines at its ends follow them. Raises
    line_edit.LineRefused("too_short") when one of them would vanish."""
    obj = doc.get(obj_id)
    new = remade(obj, curve)
    before, after = _ends(obj), _ends(new)
    label = label or t("cmd.curve_edit")
    moves = [(b, a) for b, a in zip(before, after) if np.linalg.norm(a - b) > line_edit.TOL]
    found, touched = line_edit.moved_lines(doc, moves) if moves else ({}, [])
    found.pop(obj_id, None)
    if any(np.linalg.norm(q - p) < line_edit.MIN_LENGTH for p, q in touched):
        raise line_edit.LineRefused("too_short")
    step = ReplaceObjects([obj], [new], label)
    if found:
        step = JoinedCommand([step, ReplaceMeshes([(o.id, o.mesh, m) for o, m in found.values()], label)], label)
    doc.execute(step)
    return new


# ---------------------------------------------------------------- grips

def grips(obj):
    """The grips of a curve picked alone: (ends, middles, arrows, what each is, adds) — ends squares, middles
    diamonds, arrows the tangents' lines (pairs of points), (0.411) adds «+» halfway along each span of a Bézier curve
    (dragged: a new point there) — all world; what: [("start" | "end" | "mid" | ("anchor" | "in" | "out" | "add",
    k))] for the ends, then the middles, then the adds. None when the curve has no grips of its own."""
    c = obj.curve or {}
    w = lambda p: transform_point(obj.matrix, np.asarray(p, float))        # noqa: E731
    if c.get("kind") == "arc" and not c.get("pie") and not curves.is_closed(c):
        pts = curves.arc_points(c["centre"], c["normal"], c["start"], c["angle"], 64)
        return [w(pts[0]), w(pts[-1])], [w(pts[32])], [], ["start", "end", "mid"], []
    if curves.is_half_ellipse(c):                    # (0.458) a half ellipse: its ends, its top
        pts = curves.ellipse_points(c, 64)
        return [w(pts[0]), w(pts[-1])], [w(pts[32])], [], ["start", "end", "mid"], []
    if c.get("kind") == "bezier":
        ends, middles, arrows, what_e, what_m = [], [], [], [], []
        for k, (p, hi, ho) in enumerate(c["anchors"]):
            ends.append(w(p))
            what_e.append(("anchor", k))
            for name, h in (("in", hi), ("out", ho)):
                if np.linalg.norm(np.asarray(h, float) - np.asarray(p, float)) > 1e-9:
                    middles.append(w(h))
                    what_m.append((name, k))
                    arrows += [w(p), w(h)]
        adds = [w(m) for m in curves.span_middles(c["anchors"], c.get("closed"))]
        return ends, middles, arrows, what_e + what_m + [("add", k) for k in range(len(adds))], adds
    return None


def dragged(obj, what, target):
    """The curve's data with the grip `what` taken to `target` (world; kept on the curve's plane), or None."""
    c = dict(obj.curve)
    inv = np.linalg.inv(obj.matrix)
    p = transform_point(inv, np.asarray(target, float))
    normal = np.asarray(c["normal"], float)
    if c["kind"] == "arc":
        centre = np.asarray(c["centre"], float)
        p = p - float((p - centre) @ normal) * normal
        pts = curves.arc_points(c["centre"], normal, c["start"], c["angle"], 64)
        s, m, e = pts[0], pts[32], pts[-1]
        if what == "start":
            s = p
        elif what == "end":
            e = p
        else:
            m = p
        through = curves.arc_through(s, m, e)
        if through is None:
            return None
        centre, n3, angle = through
        if float(n3 @ normal) < 0:
            angle = -angle
        return curves.arc_curve(centre, normal, s, angle, c.get("segments"), c.get("pie"))
    if curves.is_half_ellipse(c):                    # (0.458) an end moved: the half ellipse on the new axis, as tall;
        centre = np.asarray(c["centre"], float)      # its top: that tall (the axis stays)
        p = p - float((p - centre) @ normal) * normal
        s, m, e = curves.ellipse_points(c, 2)
        left = lambda a, b: curves._unit(np.cross(normal, b - a))          # noqa: E731
        height = float((m - centre) @ left(s, e))
        if what == "start":
            s = p
        elif what == "end":
            e = p
        else:
            height = float((p - centre) @ left(s, e))
        if np.linalg.norm(e - s) < 1e-6 or abs(height) < 1e-6:
            return None
        return curves.half_ellipse(s, e, height, normal, c.get("segments"))
    if c["kind"] == "bezier":
        anchors = [[np.asarray(x, float) for x in a] for a in c["anchors"]]
        auto = list(c.get("auto") or [])
        auto += [False] * (len(anchors) - len(auto))
        base = anchors[0][0]
        p = p - float((p - base) @ normal) * normal
        name, k = what
        if name == "add":                            # (0.411) a new point on that span (its shape kept), moved
            anchors, k = curves.split_span(anchors, k)
            auto.insert(k, True)
            name = "anchor"
        a, hi, ho = anchors[k]
        if name == "anchor":
            d = p - a
            anchors[k] = [a + d, hi + d, ho + d]
        else:
            auto[k] = False                          # (0.411: its tangent set by hand — Blender's «Aligned»)
            mine, other = (ho, hi) if name == "out" else (hi, ho)
            smooth = np.linalg.norm(other - a) > 1e-9 and \
                np.linalg.norm(np.cross(mine - a, other - a)) < 1e-6 * max(np.linalg.norm(mine - a), 1.0)
            new_other = other
            if smooth and np.linalg.norm(p - a) > 1e-9:      # (a smooth point stays smooth: the other turns with it)
                new_other = a - (p - a) / np.linalg.norm(p - a) * np.linalg.norm(other - a)
            anchors[k] = [a, new_other, p] if name == "out" else [a, p, new_other]
        # (0.411) the automatic tangents worked out again — the point moved and its neighbours: still smooth
        anchors = curves.auto_handles(anchors, auto, c.get("closed"))
        return curves.bezier_curve(anchors, normal, c.get("closed"), c.get("steps", curves.BEZIER_STEPS), auto)
    return None
