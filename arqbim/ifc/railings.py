"""Railings (0.115), mixed into IfcModel: an IfcRailing along a path — level, or sloping with a stair's flight —
with its own body. Pset_RailingCommon.Height, Qto_RailingBaseQuantities.Length.

(0.258) Of a type, as Revit's (core/railing_types): an IfcRailingType (GUARDRAIL; a handrail alone: HANDRAIL) with
its parts' sizes and materials in ArqSynth_Guarda, and a constituent set of its materials; the railing's body made
from the type's pieces along its path — each piece styled with its material's colour. The program's presets are made
in the project the first time they are used; a project's own types are its IfcRailingTypes.

ArqSynth_Parametros: Elemento "railing", Caminho (the path's points x, y, z in the railing's own frame — its
placement at the first point, so that moving it moves the path), Fechado (it goes round, back to its start),
Altura (its own height), Tipo (its type's key; before 0.258: Estilo, bars / glass / rails — read as their
presets), Prolongamentos (0.282: how far its handrail goes on past its start and its end, "base,top" in m — a
stair's: one going and 0,30 m, as DL 163/2006 asks)."""

import math

import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.element

from ..core import railing_types as core_rail
from .edit import EditRefused

api = ifcopenshell.api
STYLES = tuple(core_rail.PRESETS)       # (0.258: the types the program brings)
TYPE_PSET = "ArqSynth_Guarda"
GLASS = 0.012               # m


def _pts(text):
    return [tuple(float(v) for v in pair.split(",")) for pair in (text or "").split(";") if pair]


class RailingMixin:
    def railing_params(self, guid):
        e = self.by_guid(guid)
        p = self._params(e)
        m = self._placement_si(e)
        local = _pts(p.get("Caminho"))
        world = [tuple((m @ np.array((x, y, z, 1.0)))[:3]) for x, y, z in local]
        key = p.get("Tipo") or core_rail.OLD_STYLES.get(p.get("Estilo") or "", core_rail.DEFAULT)
        rt = self.railing_type(key)
        try:                                            # (0.282) its handrail's extensions at its start and end
            extend = tuple(float(v) for v in str(p.get("Prolongamentos") or "0,0").split(","))[:2]
        except ValueError:
            extend = (0.0, 0.0)
        return {"path": world, "local": local, "closed": bool(p.get("Fechado")),
                "height": float(p.get("Altura") or rt.height), "type": key, "rtype": rt, "style": key,
                "extend": extend if len(extend) == 2 else (0.0, 0.0)}

    # ------------------------------------------------------------ types (0.258)

    def railing_types(self):
        """{key: RailingType} of the project's railing types (its IfcRailingTypes that carry ArqSynth_Guarda)."""
        out = {}
        for tp in self.file.by_type("IfcRailingType"):
            props = ifcopenshell.util.element.get_psets(tp).get(TYPE_PSET)
            if props:
                rt = core_rail.from_props(tp.Name or "", props, core_rail.PRESETS.get(props.get("Chave")))
                out[rt.key] = rt
        return out

    def railing_type(self, key):
        """A railing type by its key: the project's, else the program's preset, else the default."""
        return self.railing_types().get(key) or core_rail.PRESETS.get(key) or core_rail.PRESETS[core_rail.DEFAULT]

    def railing_type_choices(self):
        """[(key, name)] the program's presets and the project's own types, for the tools and the Properties."""
        own = self.railing_types()
        out = [(k, own[k].name if k in own else rt.name) for k, rt in core_rail.PRESETS.items()]
        return out + [(k, rt.name) for k, rt in own.items() if k not in core_rail.PRESETS]

    def _railing_ifc_type(self, key):
        for tp in self.file.by_type("IfcRailingType"):
            props = ifcopenshell.util.element.get_psets(tp).get(TYPE_PSET) or {}
            if props.get("Chave") == key:
                return tp
        return None

    def ensure_railing_type(self, rt, lang="pt"):
        """The IfcRailingType of a railing type, made the first time it is used (its properties, its materials)."""
        tp = self._railing_ifc_type(rt.key)
        if tp is not None:
            return tp
        f = self.file
        handrail = rt.hand and rt.infill == "none" and rt.top == "none"
        tp = api.root.create_entity(f, ifc_class="IfcRailingType", name=rt.label(lang),
                                    predefined_type="HANDRAIL" if handrail else "GUARDRAIL")
        self._write_railing_type(tp, rt, lang)
        return tp

    def _write_railing_type(self, tp, rt, lang="pt"):
        f, u = self.file, 1.0 / self.unit_scale
        pset = next((f.by_id(v["id"]) for k, v in ifcopenshell.util.element.get_psets(tp).items() if k == TYPE_PSET),
                    None) or api.pset.add_pset(f, product=tp, name=TYPE_PSET)
        api.pset.edit_pset(f, pset=pset, properties=core_rail.to_props(rt))
        common = ifcopenshell.util.element.get_psets(tp).get("Pset_RailingCommon")
        common = f.by_id(common["id"]) if common else api.pset.add_pset(f, product=tp, name="Pset_RailingCommon")
        api.pset.edit_pset(f, pset=common, properties={"Height": rt.height * u})
        roles = (("Corrimão", "Top rail", rt.top_mat, rt.top != "none"),
                 ("Prumos", "Posts", rt.post_mat, rt.has_posts or rt.infill == "glass_channel"),
                 ("Enchimento", "Infill", rt.infill_mat, rt.infill != "none"),
                 ("Corrimão de apoio", "Handrail", rt.hand_mat, rt.hand))
        old = ifcopenshell.util.element.get_material(tp)
        if old is not None:
            api.material.unassign_material(f, products=[tp])
            if old.is_a("IfcMaterialConstituentSet") and not f.get_inverse(old):
                api.material.remove_material_set(f, material=old)
        mats = api.material.add_material_set(f, name=tp.Name, set_type="IfcMaterialConstituentSet")
        for pt, en, key, used in roles:
            if used:
                api.material.add_constituent(f, constituent_set=mats, material=self._material(key, lang)).Name = \
                    pt if lang == "pt" else en
        api.material.assign_material(f, products=[tp], type="IfcMaterialConstituentSet", material=mats)

    def _use_railing_type(self, railing, key, lang="pt"):
        """The railing made of a type: assigned to it (its IfcRailingType made if new), its own material let go."""
        rt = self.railing_type(key)
        tp = self.ensure_railing_type(rt, lang)
        if ifcopenshell.util.element.get_material(railing, should_skip_usage=True) is not None and \
                not railing.IsTypedBy:
            api.material.unassign_material(self.file, products=[railing])
        now = ifcopenshell.util.element.get_type(railing)
        if now is None or now.id() != tp.id():
            api.type.assign_type(self.file, related_objects=[railing], relating_type=tp)
        railing.PredefinedType = tp.PredefinedType
        self._set_params(railing, {"Tipo": rt.key})
        return rt

    def _box_along(self, a, b, w, d, ref=None):
        """A square bar w × d from a to b (any direction): an IfcExtrudedAreaSolid — (0.252) its w along `ref`
        (square to a -> b) when given."""
        f, u = self.file, 1.0 / self.unit_scale
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        axis = b - a
        length = float(np.linalg.norm(axis))
        axis /= length
        if ref is not None:
            ref = np.asarray(ref, dtype=float)
        else:
            ref = np.array((1.0, 0.0, 0.0)) if abs(axis[0]) < 0.9 else np.array((0.0, 1.0, 0.0))
        ref = ref - axis * float(ref @ axis)
        ref /= np.linalg.norm(ref)
        profile = f.createIfcRectangleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
            f.createIfcCartesianPoint((0.0, 0.0)), None), float(w * u), float(d * u))
        return f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint(tuple(float(c * u) for c in a)),
                                                 f.createIfcDirection(tuple(float(c) for c in axis)),
                                                 f.createIfcDirection(tuple(float(c) for c in ref))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(length * u))

    def _round_along(self, a, b, diameter):
        """(0.258) A round bar of `diameter` from a to b (any direction): an IfcExtrudedAreaSolid of a circle."""
        f, u = self.file, 1.0 / self.unit_scale
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        axis = b - a
        length = float(np.linalg.norm(axis))
        axis /= length
        ref = np.array((1.0, 0.0, 0.0)) if abs(axis[0]) < 0.9 else np.array((0.0, 1.0, 0.0))
        ref = ref - axis * float(ref @ axis)
        profile = f.createIfcCircleProfileDef("AREA", None, f.createIfcAxis2Placement2D(
            f.createIfcCartesianPoint((0.0, 0.0)), None), float(diameter / 2 * u))
        return f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint(tuple(float(c * u) for c in a)),
                                                 f.createIfcDirection(tuple(float(c) for c in axis)),
                                                 f.createIfcDirection(tuple(float(c) for c in ref / np.linalg.norm(ref)))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(length * u))

    def _pane(self, a, b, z_lo, z_hi, thickness):
        """(0.258) A flat piece upright on the line a -> b (its sides upright, its top and foot along the line,
        z_lo to z_hi over it), `thickness` thick, centred on the line."""
        f, u = self.file, 1.0 / self.unit_scale
        a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
        run = float(np.linalg.norm((b - a)[:2]))
        d = (b - a)[:2] / run
        rise = float(b[2] - a[2])
        side = [(0.0, z_lo), (run, rise + z_lo), (run, rise + z_hi), (0.0, z_hi)]
        coords = [(float(x * u), float(z * u)) for x, z in side + side[:1]]
        left = np.array((-d[1], d[0], 0.0))
        origin = a + left * thickness / 2
        return f.createIfcExtrudedAreaSolid(
            f.createIfcArbitraryClosedProfileDef("AREA", None, f.createIfcIndexedPolyCurve(
                f.createIfcCartesianPointList2D(coords), None, False)),
            f.createIfcAxis2Placement3D(f.createIfcCartesianPoint(tuple(float(c * u) for c in origin)),
                                        f.createIfcDirection(tuple(float(c) for c in -left)),
                                        f.createIfcDirection((float(d[0]), float(d[1]), 0.0))),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(thickness * u))

    def _glass_panel(self, a, b, z_lo, z_hi):
        """A glass panel between two points of the path (its sides upright, its top and foot along the path)."""
        return self._pane(a, b, z_lo, z_hi, GLASS)

    def _plate(self, centre, shape, width, thickness):
        """(0.258) A base plate on the floor under a post: a square or a disc, `width` across, `thickness` thick."""
        f, u = self.file, 1.0 / self.unit_scale
        origin2 = f.createIfcAxis2Placement2D(f.createIfcCartesianPoint((0.0, 0.0)), None)
        profile = f.createIfcCircleProfileDef("AREA", None, origin2, float(width / 2 * u)) if shape == "round" else \
            f.createIfcRectangleProfileDef("AREA", None, origin2, float(width * u), float(width * u))
        return f.createIfcExtrudedAreaSolid(
            profile, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint(tuple(float(c * u) for c in centre)),
                                                 None, None),
            f.createIfcDirection((0.0, 0.0, 1.0)), float(thickness * u))

    def _railing_item(self, part):
        kind = part[0]
        if kind == "bar":
            _k, a, b, shape, w, d, ref, _mat = part
            if np.linalg.norm(np.asarray(b) - np.asarray(a)) < 1e-6:
                return None
            if shape == "round":
                return self._round_along(a, b, w)
            return self._box_along(a, b, w, d, ref=ref)
        if kind == "pane":
            _k, a, b, z0, z1, thickness, _mat = part
            return self._pane(a, b, z0, z1, thickness) if z1 > z0 + 1e-6 else None
        _k, centre, shape, width, thickness, _mat = part
        return self._plate(centre, shape, width, thickness)

    def _set_railing_body(self, railing, lang="pt"):
        f, u = self.file, 1.0 / self.unit_scale
        p = self.railing_params(railing.GlobalId)
        pts = [np.asarray(q, dtype=float) for q in p["local"]]
        if len(pts) < 2:
            raise EditRefused("railing_short")
        rt = self._use_railing_type(railing, p["type"], lang)
        h, items = p["height"], []
        ring = pts + pts[:1] if p["closed"] else pts
        length = sum(float(np.linalg.norm(b - a)) for a, b in zip(ring, ring[1:]))
        styles = {}
        for part in core_rail.parts(pts, rt, h, p["closed"], p["extend"]):
            item = self._railing_item(part)
            if item is None:
                continue
            items.append(item)
            key = part[-1]
            if key not in styles:
                styles[key] = self._material_style(self._material(key, lang))
            f.createIfcStyledItem(item, [styles[key]], None)
        if not items:
            raise EditRefused("railing_short")
        self._clear_representations(railing)
        api.geometry.assign_representation(f, product=railing, representation=f.createIfcShapeRepresentation(
            self.body, self.body.ContextIdentifier, "SweptSolid", items))
        common = ifcopenshell.util.element.get_psets(railing).get("Pset_RailingCommon")
        pset = f.by_id(common["id"]) if common else api.pset.add_pset(f, product=railing, name="Pset_RailingCommon")
        api.pset.edit_pset(f, pset=pset, properties={"Height": h * u, "IsExternal": False})
        self._set_qto(railing, "Qto_RailingBaseQuantities", {"Length": length * u})

    def void_outlines(self, slab):
        """The plan outlines [(x, y)…] (world) of a slab's holes and of the openings cut through it (0.115): where a
        railing can go round a void. With the level of its top."""
        info = self.slab_outline(slab)
        rings = [list(h) for h in info["holes"]] if info else []
        m = self.placement(slab)
        for _gid, lo, hi, filled, box in self.voids(slab):
            if filled:
                continue
            corners = [(lo[0], lo[1]), (hi[0], lo[1]), (hi[0], hi[1]), (lo[0], hi[1])]
            rings.append([tuple((m @ np.array((x, y, 0.0, 1.0)))[:2]) for x, y in corners])
        top = info["top"] if info else float(self.element_frame(slab).z1)
        return rings, top

    def add_railing(self, path, height, style, name, closed=False, storey=None, lang="pt", extend=(0.0, 0.0)):
        """A railing along `path` ([(x, y, z)…] — level or sloping), `height` over it (None: its type's), of a type
        (its key — 0.258; a 0.115 style is read as its preset); closed: round and back to its start; (0.282)
        extend: its handrail on past its start and its end (m). Returns the IfcRailing."""
        pts = [np.asarray(q, dtype=float) for q in path]
        if len(pts) < 2 or sum(float(np.linalg.norm((b - a)[:2])) for a, b in zip(pts, pts[1:])) < 0.10:
            raise EditRefused("railing_short")
        key = core_rail.OLD_STYLES.get(style, style) or core_rail.DEFAULT
        rt = self.railing_type(key)
        height = rt.height if height is None else float(height)
        if not 0.3 <= height <= 3.0:
            raise EditRefused("railing_height")
        f = self.file
        railing = api.root.create_entity(f, ifc_class="IfcRailing", name=name, predefined_type="GUARDRAIL")
        m = np.eye(4)
        m[:3, 3] = pts[0]
        self._place(railing, m)
        container = self.storey(storey) if storey is not None else self.storey_at(float(pts[0][2]))
        api.spatial.assign_container(f, products=[railing], relating_structure=container)
        self._mark(railing, "railing")
        local = [q - pts[0] for q in pts]
        self._set_params(railing, {"Caminho": ";".join("{:.6f},{:.6f},{:.6f}".format(*q) for q in local),
                                   "Fechado": bool(closed), "Altura": height, "Tipo": rt.key})
        if max(extend) > 0.0 and not closed:
            self._set_params(railing, {"Prolongamentos": "{:.6f},{:.6f}".format(*extend)})
        self._set_railing_body(railing, lang)
        return railing

    def set_railing(self, guid, height=None, style=None, lang="pt", extend=None):
        """A railing's own height and/or its type (its key; a 0.115 style is read as its preset); (0.282) its
        handrail's extensions (at its start, at its end; m)."""
        railing, _ = self._require(guid, "railing")
        changes = {}
        if extend is not None:
            if min(extend) < 0.0 or max(extend) > 3.0:
                raise EditRefused("too_small")
            changes["Prolongamentos"] = "{:.6f},{:.6f}".format(*extend)
        if height is not None:
            if not 0.3 <= float(height) <= 3.0:
                raise EditRefused("railing_height")
            changes["Altura"] = float(height)
        if style is not None:
            key = core_rail.OLD_STYLES.get(style, style)
            if key not in core_rail.PRESETS and key not in self.railing_types():
                raise EditRefused("not_editable")
            changes["Tipo"] = key
        self._set_params(railing, changes)
        self._set_railing_body(railing, lang)

    def remove_railing_type(self, key):
        """(0.260) A project's own railing type taken away — refused for the program's and for one in use."""
        if key in core_rail.PRESETS:
            raise EditRefused("not_editable")
        if self.railings_of_type(key):
            raise EditRefused("type_in_use")
        tp = self._railing_ifc_type(key)
        if tp is not None:
            mats = ifcopenshell.util.element.get_material(tp)
            api.root.remove_product(self.file, product=tp)
            if mats is not None and mats.is_a("IfcMaterialConstituentSet") and not self.file.get_inverse(mats):
                api.material.remove_material_set(self.file, material=mats)

    def railings_of_type(self, key):
        """(0.258) The railings made of a type."""
        return [e.GlobalId for e in self.file.by_type("IfcRailing")
                if self.kind_of(e.GlobalId) == "railing" and self.railing_params(e.GlobalId)["type"] == key]

    def set_railing_type(self, rt, old_key=None, lang="pt"):
        """(0.258) A railing type saved in the project — new, or changed (its key `old_key`; a preset changed
        becomes the project's own, under the same key) — and every railing of it made again. Returns their
        GlobalIds."""
        trouble = core_rail.problem(rt)
        if trouble:
            raise EditRefused(trouble)
        old_key = old_key or rt.key
        tp = self._railing_ifc_type(old_key)
        if tp is None:
            tp = api.root.create_entity(self.file, ifc_class="IfcRailingType", name=rt.label(lang),
                                        predefined_type="GUARDRAIL")
        tp.Name = rt.label(lang)
        handrail = rt.hand and rt.infill == "none" and rt.top == "none"
        tp.PredefinedType = "HANDRAIL" if handrail else "GUARDRAIL"
        self._write_railing_type(tp, rt, lang)
        changed = self.railings_of_type(old_key) if old_key != rt.key else self.railings_of_type(rt.key)
        for g in changed:
            railing = self.by_guid(g)
            self._set_params(railing, {"Tipo": rt.key})
            self._set_railing_body(railing, lang)
        return changed

    def stair_railing_paths(self, stair):
        """The paths of a stair's railings (world): [[(x, y, z)…]…] (0.115) — (0.261) one each side, all the way up
        (core/stairs.railing_sides); a spiral stair's along its outer edge."""
        from ..core import stairs as core_stairs
        p = self.stair_params(stair)
        m = self._placement_si(self.by_guid(stair))
        pieces = core_stairs.layout(p["form"], p["rise"], p["width"], p["going"], p["turn"])
        out = []
        wedges = [piece for piece in pieces if piece[0] == "wedge"]
        if wedges:                                       # (0.116) a spiral stair: along its outer edge
            path = []
            for _kind, (cx, cy), _r0, r1, a0, _a1, top in wedges:
                path.append((cx + (r1 - 0.05) * math.cos(a0), cy + (r1 - 0.05) * math.sin(a0), top))
            _kind, (cx, cy), _r0, r1, _a0, a1, top = wedges[-1]
            path.append((cx + (r1 - 0.05) * math.cos(a1), cy + (r1 - 0.05) * math.sin(a1), p["rise"]))
            out.append([tuple((m @ np.array((*q, 1.0)))[:3]) for q in path])
            return out
        # (0.261) one railing each side, all the way up: along the flights' nosings, level along the landing
        for path in core_stairs.railing_sides(p["form"], p["rise"], p["width"], p["going"], p["turn"]):
            out.append([tuple((m @ np.array((*q, 1.0)))[:3]) for q in path])
        return out
