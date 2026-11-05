"""The electrical installation checked and counted (0.147, Phase 6, step 4: «validação, quadro de cargas e
quantidades»): what is missing or wrong — points in no circuit, a circuit with no board, not wired, or that its
working out does not pass, a storey with points and no board, a room with no light — each problem with the
elements it is about (to select them); and the quantities: the points of each kind, the conduits' metres of each
diameter, the circuits and the boards.

Read from the model each time (never kept)."""

import numpy as np

import ifcopenshell.util.element

from ..i18n import t

POINT_CLASSES = ("IfcOutlet", "IfcSwitchingDevice", "IfcLightFixture", "IfcJunctionBox")


def problems(doc, storey=None):
    """[(what — an i18n key's end —, its text, the GlobalIds it is about)] of the electrical installation (of a
    storey, or all), the most serious first."""
    out = []
    objs = [o for o in doc.objects.values() if o.is_bim and (storey is None or o.storey == storey)]
    points = [o.id for o in objs if o.ifc_class in POINT_CLASSES]
    boards = [o.id for o in objs if o.ifc_class == "IfcElectricDistributionBoard"]
    try:
        circuits = doc.ifc.circuits()
    except RuntimeError:
        return out
    loose = [g for g in points if doc.ifc.circuit_of(g) is None]
    if points and not boards:
        out.append(("no_board", t("elcheck.no_board"), points))
    for g, name in circuits:
        members = [m for m in doc.ifc.circuit_points(g)
                   if doc.get(m) is not None and (storey is None or doc.get(m).storey == storey)]
        if not members:
            continue
        r = doc.ifc.circuit_report(g)
        if not r["board"] or doc.get(r["board"]) is None:
            out.append(("circuit_no_board", t("elcheck.circuit_no_board", c=name), members))
        if not r["ok"]:
            why = ", ".join(t("circuit.why." + w) for w in r["why"])
            out.append(("circuit_check", t("elcheck.circuit_check", c=name, why=why), members))
        if not doc.ifc.circuit_conduits(g):
            out.append(("not_wired", t("elcheck.not_wired", c=name), members))
    if loose:
        out.append(("loose", t("elcheck.loose", n=len(loose)), loose))
    try:
        rooms = doc.ifc.spaces(storey) if storey is not None else doc.ifc.spaces()
    except Exception:
        rooms = []
    from shapely.geometry import Point, Polygon
    lights = [doc.get(g) for g in points if doc.get(g).ifc_class == "IfcLightFixture" and doc.get(g).mesh.bounds()]
    middles = [(o.storey, Point(*((np.asarray(o.mesh.bounds()[0]) + np.asarray(o.mesh.bounds()[1])) / 2)[:2]))
               for o in lights]
    for info in rooms:
        poly = Polygon(info["outline"], info["holes"])
        if not poly.is_valid:
            continue
        if not any(s == info["storey"] and poly.buffer(1e-6).contains(m) for s, m in middles):
            out.append(("room_dark", t("elcheck.room_dark", r=info["name"] or info["number"]), [info["guid"]]))
    return out


def quantities(doc):
    """The electrical quantities: [(what, how many, metres or None)] — the points of each kind, the conduits of each
    type (their metres), the circuits and the boards."""
    from ..ifc.electrical import POINTS
    counts = {}
    for o in doc.objects.values():
        if not o.is_bim:
            continue
        if o.ifc_class in ("IfcOutlet", "IfcSwitchingDevice", "IfcJunctionBox", "IfcElectricDistributionBoard"):
            try:
                kind = doc.ifc.point_params(o.id)["kind"]
            except Exception:
                continue
            label = t("point." + kind) if kind in POINTS else o.ifc_class
            counts[label] = counts.get(label, 0) + 1
        elif o.ifc_class == "IfcLightFixture":
            label = t("elcount.light")
            counts[label] = counts.get(label, 0) + 1
    rows = [(label, n, None) for label, n in sorted(counts.items())]
    lengths = {}
    for e in doc.ifc.file.by_type("IfcCableCarrierSegment"):
        try:
            s, end, _z = doc.ifc.segment_params(e.GlobalId)
        except Exception:
            continue
        type_ = ifcopenshell.util.element.get_type(e)
        name = (type_.Name if type_ is not None else None) or t("elem.conduit")
        n, length = lengths.get(name, (0, 0.0))
        lengths[name] = (n + 1, length + float(np.linalg.norm(end - s)))
    rows += [(name, n, length) for name, (n, length) in sorted(lengths.items())]
    rows.append((t("elqty.circuits"), len(doc.ifc.circuits()), None))
    return rows
