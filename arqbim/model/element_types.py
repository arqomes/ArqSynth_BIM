"""(0.414) Types saved and applied — as Revit's types (Type Selector, Duplicate, Edit Type), for the kinds of element that
had none (ifc/element_types keeps them in the IFC). The owner: «quero todos os elementos IFC tenham tipo, guardado e
aplicado a outros elementos».

For each kind: what its type keeps (`values`: an element's settings that are not its own place or shape — a
parametric surface's form, modifiers, construction and use, not its curves) and how they are put on an element
(`apply`). Then, each one undo step:

- save_type: a type made from an element (and the element tied to it);
- apply_type: a type's values put on elements of its kind (and them tied to it) — None: tied to none;
- update_type: an element's values taken to its type and to every element of that type (Revit's «Edit Type»)."""

from dataclasses import dataclass
from typing import Callable

from ..i18n import lang, t
from .document import IfcCommand


@dataclass
class KindTypes:
    values: Callable          # (ifc, guid) -> dict: what a type of it keeps
    apply: Callable           # (ifc, guid, values, lang) -> None: those values put on it


# ---------------------------------------------------------------- a parametric surface (0.414)

def _surface_values(ifc, guid):
    """Its form, modifiers, construction and use — not its curves (each surface's own)."""
    data = dict(ifc.surface_definition(guid))
    data.pop("curves", None)
    return {"definition": data, "usage": ifc.surface_usage(guid)}


def _surface_apply(ifc, guid, values, language):
    data = dict(values.get("definition") or {})
    data["curves"] = ifc.surface_definition(guid).get("curves") or []
    ifc.set_param_surface(guid, data, lang=language, usage=values.get("usage"))


KINDS = {"param_surface": KindTypes(_surface_values, _surface_apply)}


# ---------------------------------------------------------------- (0.415) the others — what is the type's, not each one's

def _params(ifc, guid):
    return ifc._params(ifc.by_guid(guid))


def _ceiling_values(ifc, guid):
    """Its style, its shadow gap and bulkhead — not its height over the floor."""
    p = _params(ifc, guid)
    return {"style": ifc.ceiling_params(guid)["style"], "gap": float(p.get("Rasgo") or 0.0),
            "bulkhead": float(p.get("SancaLargura") or 0.0), "drop": float(p.get("SancaAltura") or 0.0)}


def _ceiling_apply(ifc, guid, v, language):
    ifc.set_ceiling(guid, style=v.get("style"), gap=v.get("gap"),
                    bulkhead=(float(v.get("bulkhead") or 0.0), float(v.get("drop") or 0.0)))


def _flooring_values(ifc, guid):
    """Its finish (material, thickness with its bed) — not its outline."""
    return {"finish": _params(ifc, guid).get("Acabamento") or "ceramico"}


def _flooring_apply(ifc, guid, v, language):
    ifc.set_flooring(guid, v.get("finish") or "ceramico", language)


CLADDING_KEYS = ("finish", "width", "gap", "direction", "diameter", "pitch", "margin", "amplitude", "wavelength",
                 "shift", "depth", "hole", "grid", "sheet_w", "sheet_h", "joint", "mask")


def _cladding_values(ifc, guid):
    """Its finish and its pattern (slats, flutes, holes, waves…) — not where on its wall, nor how high."""
    p = ifc.pattern_params(guid)
    return {k: p[k] for k in CLADDING_KEYS if p.get(k) is not None}


def _cladding_apply(ifc, guid, v, language):
    values = {k: v[k] for k in CLADDING_KEYS if k in v}
    finish = values.pop("finish", None)
    ifc.set_cladding(guid, finish=finish, **values)


def _stair_values(ifc, guid):
    """Its flights' width and its tread — not its rise (the storey's) nor its form."""
    p = ifc.stair_params(guid)
    return {"width": p["width"], "going": p["going"]}


def _stair_apply(ifc, guid, v, language):
    ifc.set_stair(guid, width=float(v["width"]), going=float(v["going"]))


def _ramp_values(ifc, guid):
    """Its width — not its length nor its rise."""
    return {"width": float(ifc.ramp_params(guid)[2])}


def _ramp_apply(ifc, guid, v, language):
    ifc.set_ramp(guid, width=float(v["width"]))


def _curtain_values(ifc, guid):
    """Its mullions' and transoms' spacing — not its length nor its height."""
    p = ifc.curtain_params(guid)
    return {"mullions": float(p["mullions"]), "transoms": float(p["transoms"])}


def _curtain_apply(ifc, guid, v, language):
    ifc.set_curtain_wall(guid, mullions=float(v["mullions"]), transoms=float(v["transoms"]))


CABINET_KEYS = ("kind", "width", "height", "depth", "plinth", "elevation", "fronts", "doors", "drawers", "shelves",
                "handle", "interior", "blind", "corner_side", "arm", "finish", "splits")


def _cabinet_values(ifc, guid):
    """All it is — a piece of furniture's type is its sizes, its fronts and what is inside (as Revit's families)."""
    c = ifc.cabinet_params(guid)
    return {k: getattr(c, k) for k in CABINET_KEYS if getattr(c, k, None) is not None}


def _cabinet_apply(ifc, guid, v, language):
    ifc.set_cabinet(guid, **{k: v[k] for k in CABINET_KEYS if k in v})


KINDS.update({"ceiling": KindTypes(_ceiling_values, _ceiling_apply),
              "flooring": KindTypes(_flooring_values, _flooring_apply),
              "cladding": KindTypes(_cladding_values, _cladding_apply),
              "stair": KindTypes(_stair_values, _stair_apply),
              "ramp": KindTypes(_ramp_values, _ramp_apply),
              "curtain_wall": KindTypes(_curtain_values, _curtain_apply),
              "cabinet": KindTypes(_cabinet_values, _cabinet_apply)})


def has_types(doc, guid):
    """This element's kind is one with saved types."""
    return doc.ifc.kind_of(guid) in KINDS


def types_of(doc, kind):
    """[(type GlobalId, name)] saved for this kind."""
    return doc.ifc.element_types(kind)


def save_type(doc, guid, name):
    """A type named `name` made from this element — what its kind's types keep — and the element tied to it. One undo
    step. Its GlobalId."""
    kind = doc.ifc.kind_of(guid)
    spec = KINDS[kind]

    def action(ifc):
        made = ifc.add_element_type(kind, name, spec.values(ifc, guid), ifc.by_guid(guid).is_a())
        ifc.tie_element_type(guid, made)
        return made

    return doc.execute(IfcCommand(t("cmd.type_save"), action, changed=[guid], plan=False)).result


def apply_type(doc, guids, type_guid):
    """The type's values put on these elements (those of its kind) and them tied to it — (type_guid None) or tied to
    none (their settings stay). One undo step. Returns those changed."""
    if type_guid is not None:
        kind = next((k for k in KINDS if any(g == type_guid for g, _n in doc.ifc.element_types(k))), None)
        if kind is None:
            return []
        guids = [g for g in guids if doc.ifc.kind_of(g) == kind]
    else:
        guids = [g for g in guids if has_types(doc, g)]
    if not guids:
        return []
    language = lang()

    def action(ifc):
        values = ifc.element_type_values(type_guid) if type_guid is not None else None
        for g in guids:
            if values is not None:
                KINDS[ifc.kind_of(g)].apply(ifc, g, values, language)
            ifc.tie_element_type(g, type_guid)
        return guids

    return doc.execute(IfcCommand(t("cmd.type_apply"), action, changed=list(guids), plan=False)).result


def update_type(doc, guid):
    """This element's values taken to its type and put on every other element of that type. One undo step. Returns the
    elements changed (it and the others), or [] (it has no type)."""
    type_guid = doc.ifc.element_type_of(guid)
    if type_guid is None:
        return []
    kind = doc.ifc.kind_of(guid)
    others = [g for g in doc.ifc.elements_of_type(type_guid) if g != guid and doc.ifc.kind_of(g) == kind]
    language = lang()

    def action(ifc):
        values = KINDS[kind].values(ifc, guid)
        ifc.set_element_type_values(type_guid, values)
        for g in others:
            KINDS[kind].apply(ifc, g, values, language)
            ifc.tie_element_type(g, type_guid)
        return [guid] + others

    return doc.execute(IfcCommand(t("cmd.type_update"), action, changed=[guid] + others, plan=False)).result


def differs(doc, guid):
    """The element's values are not its type's any more (changed by hand since): «Atualizar o tipo» has something to
    take."""
    type_guid = doc.ifc.element_type_of(guid)
    if type_guid is None:
        return False
    kind = doc.ifc.kind_of(guid)
    import json
    mine = json.dumps(KINDS[kind].values(doc.ifc, guid), sort_keys=True, ensure_ascii=False)
    theirs = json.dumps(doc.ifc.element_type_values(type_guid), sort_keys=True, ensure_ascii=False)
    return mine != theirs
