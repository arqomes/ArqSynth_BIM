"""(0.570, PLANO.md «Gerador de revestimentos 3D em IFC», step 10) The Revestimento's tools for an AI over MCP — few,
short in and out (tokens are dear): lay one on a face or many by category or by room, change its layout, read its
quantities, export its drawing."""

from ..core import covering_finishes as cf
from ..core import tiling as tl
from .protocol import ToolError


def _guid(session, ref):
    e = session.element(ref)
    if e is None:
        raise ToolError("no element {}".format(ref))
    return e.GlobalId


def finishes(session, args):
    """The finishes (key: name), one group or all."""
    g = args.get("group")
    return "\n".join("{} {}".format(k, f.name_pt) for k, f in cf.FINISHES.items() if g is None or f.group == g)


def cover(session, args):
    """A Revestimento: on element `id`'s face facing `normal` [x,y,z] (its outer face that way), or on a room
    (`room`: floor/walls/height/skirting/ceiling), or on every element of a `category`."""
    from ..model import bim
    from ..model import covering_targets as ct
    doc = session.doc
    finish = args.get("finish") or "porcelanico_60x60"
    if args.get("room"):
        made = bim.cover_room(doc, _guid(session, args["room"]), args.get("floor"), args.get("walls"),
                              float(args.get("height") or 2.1), args.get("skirting"), args.get("ceiling"))
    elif args.get("category"):
        cat = args["category"]
        ids = [_guid(session, i) for i in args.get("ids") or ()] or \
            [e.GlobalId for e in session.ifc.file.by_type(ct.IFC_CLASSES[cat][0])]
        made = bim.cover_category(doc, ids, cat, finish, args.get("sides") or "ambas",
                                  tuple(args.get("slab_faces") or ("topo",)))
    else:
        host = _guid(session, args["id"])
        found = ct.face_along(session.ifc, host, args.get("normal") or (0.0, -1.0, 0.0), {})
        if found is None:
            raise ToolError("no flat face that way")
        made = [bim.cover_face(doc, host, found[0], args.get("normal") or (0.0, -1.0, 0.0), finish,
                               args.get("layout"))]
    return " ".join("#{}".format(session.ifc.by_guid(g).id()) for g in made if g)


def edit(session, args):
    """A Revestimento (#n) changed: finish, layout {pattern,w,h,joint,angle,origin…}, material, thickness, bed, grout."""
    from ..model import bim
    g = _guid(session, args["id"])
    keep = {k: args[k] for k in ("finish", "material", "thickness", "bed", "grout", "recess") if k in args}
    if args.get("layout"):
        keep["layout"] = args["layout"]
    bim.set_covering(session.doc, g, **keep)
    p = session.ifc.describe(g)["params"]
    return "pieces={} cut={} narrowest={:.3f}".format(p["pieces"], p["cut"], p["narrowest"])


def quantities(session, args):
    """Quantities of Revestimentos (ids, or all): area, to buy, waste, joints, glue, grout; dxf/xlsx paths to write."""
    from ..model import bim
    ids = [_guid(session, i) for i in args.get("ids") or ()] or \
        [e.GlobalId for e in session.ifc.file.by_type("IfcCovering")
         if session.ifc._params(e).get("Elemento") == "tiled_covering"]
    _each, q = bim.covering_quantities(session.doc, ids)
    if args.get("dxf") or args.get("xlsx"):
        bim.covering_export(session.doc, ids[0], args.get("dxf"), args.get("xlsx"))
    return "area={:.2f} buy={:.2f} waste={:.0%} joints={:.0f}m glue={:.0f}kg grout={:.0f}kg pieces={}/{}cut".format(
        q["area"], q["buy_area"], q["waste"], q["joints_m"], q["glue_kg"], q["grout_kg"], q["pieces"], q["cut"])


def covering(session, args):
    """One tool for it all (tokens are dear): do = keys | lay | edit | qty."""
    do = args.get("do") or "lay"
    opt = dict(args.get("opt") or {})
    merged = dict(opt, **{k: v for k, v in args.items() if k not in ("do", "opt")})
    if do == "keys":
        return finishes(session, merged)
    if do == "edit":
        return edit(session, merged)
    if do == "qty":
        return quantities(session, merged)
    return cover(session, merged)


def definitions(schema):
    s, str_, obj = schema, {"type": "string"}, {"type": "object"}
    return [
        ("covering", "Finish in pieces. do keys{group?}|lay{id,normal}|{room,opt:floor,walls,height,skirting,"
                     "ceiling}|{category:parede|laje|pilar|viga,opt:sides,ids}|edit{id,layout{pattern,w,h,joint,"
                     "angle,origin}|finish..}|qty{ids?,dxf?,xlsx?}.",
         s({"do": str_, "id": {"type": ["string", "integer"]}, "normal": {"type": "array"}, "finish": str_,
            "layout": obj, "room": {"type": ["string", "integer"]}, "category": str_, "opt": obj}), covering, False),
    ]
