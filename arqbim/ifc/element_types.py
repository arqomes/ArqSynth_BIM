"""(0.414) Types saved from an element and applied to others — the owner: «quero todos os elementos IFC tenham tipo,
guardado e aplicado a outros elementos» —, for the elements whose kinds have no catalogue types (model/element_types
says which, and what their type keeps). Mixed into IfcModel.

A type is an IfcTypeObject of the element's class's type (IfcRoofType for an IfcRoof, IfcBuildingElementProxyType…),
named, with the pset «ArqSynth_Tipo»: Elemento (the kind) and Valores (what the type keeps, JSON). Its elements are
tied to it by IfcRelDefinesByType, as any IFC type's. Not the program's own pset (ArqSynth_Parametros): an element's
parameters read through its type would take those."""

import json

import ifcopenshell.api
import ifcopenshell.api.root
import ifcopenshell.api.type
import ifcopenshell.util.element

from .edit import EditRefused

api = ifcopenshell.api
TYPE_PSET = "ArqSynth_Tipo"
# an element's class -> its type's class (IFC4); what is not here: a proxy type
TYPE_CLASS = {"IfcRoof": "IfcRoofType", "IfcBuildingElementProxy": "IfcBuildingElementProxyType",
              "IfcCurtainWall": "IfcCurtainWallType", "IfcShadingDevice": "IfcShadingDeviceType",
              "IfcCovering": "IfcCoveringType", "IfcStair": "IfcStairType", "IfcRamp": "IfcRampType",
              "IfcRailing": "IfcRailingType", "IfcFurniture": "IfcFurnitureType",
              "IfcTransportElement": "IfcTransportElementType", "IfcLightFixture": "IfcLightFixtureType"}


class ElementTypeMixin:
    def _type_pset(self, type_):
        for rel in getattr(type_, "HasPropertySets", None) or ():
            if rel.is_a("IfcPropertySet") and rel.Name == TYPE_PSET:
                return {p.Name: getattr(p.NominalValue, "wrappedValue", None) for p in rel.HasProperties
                        if p.is_a("IfcPropertySingleValue")}
        return None

    def element_types(self, kind):
        """[(GlobalId, name)] of the types saved for this kind of element, by name."""
        out = []
        for type_ in self.file.by_type("IfcTypeObject"):
            p = self._type_pset(type_)
            if p is not None and p.get("Elemento") == kind:
                out.append((type_.GlobalId, type_.Name or ""))
        return sorted(out, key=lambda item: item[1].lower())

    def element_type_of(self, guid):
        """GlobalId of the saved type this element is of, or None."""
        e = self.by_guid(guid)
        for rel in getattr(e, "IsTypedBy", None) or ():
            if self._type_pset(rel.RelatingType) is not None:
                return rel.RelatingType.GlobalId
        return None

    def element_type_values(self, type_guid):
        """What the type keeps (dict) — {} when not understood."""
        type_ = self.by_guid(type_guid)
        p = self._type_pset(type_) if type_ is not None else None
        try:
            values = json.loads((p or {}).get("Valores") or "{}")
        except (TypeError, ValueError):
            return {}
        return values if isinstance(values, dict) else {}

    def elements_of_type(self, type_guid):
        type_ = self.by_guid(type_guid)
        return [e.GlobalId for e in ifcopenshell.util.element.get_types(type_)] if type_ is not None else []

    def add_element_type(self, kind, name, values, ifc_class):
        """A new type of this kind, named, keeping `values`, of the type class of `ifc_class` (the element's). Its
        GlobalId."""
        name = str(name or "").strip()
        if not name:
            raise EditRefused("type_name")
        if any(n.lower() == name.lower() for _g, n in self.element_types(kind)):
            raise EditRefused("type_exists")
        type_ = api.root.create_entity(self.file, ifc_class=TYPE_CLASS.get(ifc_class, "IfcBuildingElementProxyType"),
                                       name=name)
        pset = api.pset.add_pset(self.file, product=type_, name=TYPE_PSET)
        api.pset.edit_pset(self.file, pset=pset, properties={"Elemento": kind,
                                                             "Valores": json.dumps(values, ensure_ascii=False)})
        return type_.GlobalId

    def set_element_type_values(self, type_guid, values):
        type_ = self.by_guid(type_guid)
        for rel in getattr(type_, "HasPropertySets", None) or ():
            if rel.is_a("IfcPropertySet") and rel.Name == TYPE_PSET:
                api.pset.edit_pset(self.file, pset=rel,
                                   properties={"Valores": json.dumps(values, ensure_ascii=False)})
                return
        raise EditRefused("not_editable")

    def tie_element_type(self, guid, type_guid):
        """The element tied to this type (None: to none) — the type it had let go. A type of another class than the
        element's now (its use changed it): a type of the right class, the same name and values, takes its place
        for it."""
        e = self.by_guid(guid)
        for rel in list(getattr(e, "IsTypedBy", None) or ()):
            if self._type_pset(rel.RelatingType) is not None:
                api.type.unassign_type(self.file, related_objects=[e])
        if type_guid is None:
            return
        type_ = self.by_guid(type_guid)
        want = TYPE_CLASS.get(e.is_a(), "IfcBuildingElementProxyType")
        if not type_.is_a(want):
            type_ = api.root.reassign_class(self.file, product=type_, ifc_class=want)
        api.type.assign_type(self.file, related_objects=[e], relating_type=type_)

    def rename_element_type(self, type_guid, name):
        type_ = self.by_guid(type_guid)
        if type_ is None or not str(name).strip():
            raise EditRefused("type_name")
        type_.Name = str(name).strip()
