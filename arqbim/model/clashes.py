"""Clash detection between the disciplines (0.149, Phase 6, step 6: «coordenação: deteção de conflitos entre
disciplinas, relatório»): the installations against the structure (a pipe through a beam, a duct in a column),
the installations against each other (a duct crossing a pipe — not the pieces of one run, which touch), and, if
asked, against the walls (where an opening is needed). Read from the shapes on screen (world coordinates), never
kept: a clash is a pair of elements and a point where they go into each other.

The report: an HTML page with the clashes, for the meeting."""

import html
from dataclasses import dataclass

import numpy as np

from ..core import clash as core_clash
from ..i18n import t

DISCIPLINES = {
    "structure": ("IfcColumn", "IfcBeam", "IfcSlab", "IfcFooting", "IfcPile"),
    "walls": ("IfcWall", "IfcWallStandardCase", "IfcCurtainWall"),
    "services": ("IfcPipeSegment", "IfcPipeFitting", "IfcDuctSegment", "IfcDuctFitting", "IfcCableCarrierSegment",
                 "IfcCableCarrierFitting", "IfcAirTerminal", "IfcUnitaryEquipment"),
}
PAIRS = (("services", "structure"), ("services", "services"), ("services", "walls"))
DEFAULT_PAIRS = (("services", "structure"), ("services", "services"))


@dataclass
class Clash:
    a: str                  # GlobalIds (a < b when both are of one discipline)
    b: str
    point: np.ndarray       # (3,) where they go into each other
    pair: tuple             # the disciplines' keys
    key: str = ""           # "a|b": the same clash from one search to the next

    def __post_init__(self):
        self.key = "|".join(sorted((self.a, self.b)))


def _members(doc, discipline, storey):
    out = []
    for o in doc.objects.values():
        if o.is_bim and o.ifc_class in DISCIPLINES[discipline] and (storey is None or o.storey == storey):
            box = o.mesh.bounds()
            if box is not None and len(o.mesh.tris):
                out.append((o.id, np.asarray(box[0], float), np.asarray(box[1], float), o))
    return out


def _neighbours(doc, guid):
    """The elements connected to this one by a port, and through a fitting next to it (the pieces of one run)."""
    try:
        near = set()
        for port in doc.ifc.ports(guid):
            other = doc.ifc.connected(port)
            owner = doc.ifc.owner_of(other) if other is not None else None
            if owner is not None:
                near.add(owner.GlobalId)
                if owner.is_a("IfcFlowFitting"):
                    for p2 in doc.ifc.ports(owner.GlobalId):
                        o2 = doc.ifc.connected(p2)
                        w2 = doc.ifc.owner_of(o2) if o2 is not None else None
                        if w2 is not None:
                            near.add(w2.GlobalId)
        return near
    except Exception:
        return set()


def find(doc, pairs=DEFAULT_PAIRS, storey=None):
    """The clashes of these pairs of disciplines (of a storey, or all): [Clash], in the order found (by pair)."""
    out, seen = [], set()
    cache = {}
    for x, y in pairs:
        xs, ys = _members(doc, x, storey), _members(doc, y, storey)
        if not xs or not ys:
            continue
        lo_y = np.array([m[1] for m in ys])
        hi_y = np.array([m[2] for m in ys])
        for ga, la, ha, oa in xs:
            near = np.flatnonzero(np.all(la < hi_y - core_clash.MARGIN, axis=1) & np.all(lo_y < ha - core_clash.MARGIN,
                                                                                         axis=1))
            for k in near:
                gb, _lb, _hb, ob = ys[k]
                if ga == gb or (x == y and ga > gb):
                    continue
                key = "|".join(sorted((ga, gb)))
                if key in seen:
                    continue
                if x == "services" and y == "services":
                    if ga not in cache:
                        cache[ga] = _neighbours(doc, ga)
                    if gb in cache[ga]:
                        continue
                point = core_clash.clash((oa.mesh.verts, oa.mesh.tris), (ob.mesh.verts, ob.mesh.tris))
                if point is not None:
                    seen.add(key)
                    out.append(Clash(ga, gb, np.asarray(point, float), (x, y)))
    return out


STATUSES = ("new", "active", "resolved", "approved")


def updated_status(old, clashes):
    """(0.150) The statuses after a search: a clash seen for the first time is new; one seen before, active (an
    approved one stays approved); one no longer there is resolved (an approved one too). {key: status}."""
    now = {c.key for c in clashes}
    out = {}
    for key in now:
        before = old.get(key)
        out[key] = "approved" if before == "approved" else ("new" if before in (None, "resolved") else "active")
    for key, before in old.items():
        if key not in now:
            out[key] = "resolved"
    return out


class SetClashStatus:
    """The clashes' statuses changed (a search, an approval): one undo step."""

    def __init__(self, after, label):
        self.after, self.label = dict(after), label
        self.before = None

    def do(self, doc):
        if self.before is None:
            self.before = dict(doc.clash_status)
        doc.clash_status = dict(self.after)

    def undo(self, doc):
        doc.clash_status = dict(self.before)


def pair_text(pair):
    return " × ".join(t("discipline." + d) for d in pair)


def report_html(doc, clashes, title, statuses=None):
    """The clashes as an HTML page: the project, the date, how many, and a row for each (the two elements, the
    disciplines, where, the status)."""
    from .notes import now
    rows = []
    for k, c in enumerate(clashes, 1):
        a, b = doc.get(c.a), doc.get(c.b)
        status = (statuses or {}).get(c.key, "")
        rows.append("<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
            k, html.escape(a.name if a else c.a), html.escape(b.name if b else c.b), html.escape(pair_text(c.pair)),
            "{:.2f}; {:.2f}; {:.2f}".format(*c.point).replace(".", ","),
            html.escape(t("clashstatus." + status) if status else "")))
    head = "".join("<th>{}</th>".format(html.escape(t(k))) for k in ("clash.col.n", "clash.col.a", "clash.col.b",
                                                                     "clash.col.pair", "clash.col.where",
                                                                     "clash.col.status"))
    return ("<!doctype html><html><head><meta charset='utf-8'><title>{t}</title><style>body{{font-family:sans-serif;"
            "margin:24px}}table{{border-collapse:collapse}}td,th{{border:1px solid #bbb;padding:4px 8px}}"
            "th{{background:#eee}}</style></head><body><h1>{t}</h1><p>{when} — {n}</p><table><tr>{head}</tr>{rows}"
            "</table></body></html>").format(t=html.escape(title), when=now().replace("T", " "),
                                             n=html.escape(t("clash.count", n=len(clashes))), head=head,
                                             rows="".join(rows))
