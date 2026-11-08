"""BIM groups (Revit's "model groups"), mixed into IfcModel.

A set of elements placed several times (an apartment, a bathroom). Each
placement is an IfcGroup (IfcRelAssignsToGroup); the copies of one group share
a "model" id, and every element has a role, the same in each copy. An edit
made to one element is then repeated on the element with the same role in
every other copy (model.bim does that). Both live in the Pset
ArqBIM_Parametros: Elemento = "group" and Modelo on the IfcGroup, Papel on
each element.
"""

import importlib

import numpy as np

import ifcopenshell
import ifcopenshell.util.element

importlib.import_module("ifcopenshell.api.group")
importlib.import_module("ifcopenshell.api.spatial")
api = ifcopenshell.api


class GroupMixin:
    def group_of(self, guid):
        """The ArqBIM group (IfcGroup) an element belongs to, or None."""
        e = self.by_guid(guid)
        for rel in getattr(e, "HasAssignments", None) or ():
            if rel.is_a("IfcRelAssignsToGroup") and self._params(rel.RelatingGroup).get("Elemento") == "group":
                return rel.RelatingGroup
        return None

    def group_members(self, group):
        if isinstance(group, str):
            group = self.by_guid(group)
        return [o.GlobalId for rel in (group.IsGroupedBy or ()) for o in rel.RelatedObjects]

    def group_model(self, group):
        return self._params(group).get("Modelo")

    def group_copies(self, model):
        """Every placement (IfcGroup) of a group model."""
        return [g for g in self.file.by_type("IfcGroup")
                if self._params(g).get("Elemento") == "group" and self._params(g).get("Modelo") == model]

    def role_of(self, guid):
        from .edit import _MISSING, _own_param        # (0.287: one value read, not all of them — a group's
        e = self.by_guid(guid)                         #  thousand copies ask it of each member)
        role = _own_param(e, "Papel")
        if role is _MISSING:
            role = self._params(e).get("Papel")
        return None if role is None else int(role)

    def counterparts(self, guid):
        """The same element (same role) in the other copies of its group — (0.465) a typical floor's none while its
        replication is switched off (the Storeys panel's «=»: what is changed on one storey changes on it alone)."""
        group = self.group_of(guid)
        if group is None:
            return []
        if not getattr(self, "typical_live", True) and self._params(group).get("Pavimento"):
            return []
        role = self.role_of(guid)
        out = []
        for other in self.group_copies(self.group_model(group)):
            if other != group:
                out += [m for m in self.group_members(other) if self.role_of(m) == role]
        return out

    def _with_fillings(self, guids):
        out = list(guids)
        for guid in guids:
            e = self.by_guid(guid)
            for rel in getattr(e, "HasOpenings", None) or ():
                for fill in rel.RelatedOpeningElement.HasFillings or ():
                    if fill.RelatedBuildingElement.GlobalId not in out:
                        out.append(fill.RelatedBuildingElement.GlobalId)
        return out

    def make_group(self, guids, name):
        """A new group from these elements (a wall's doors and windows come with it). Returns the IfcGroup."""
        from .edit import EditRefused
        members = self._with_fillings(guids)
        if any(self.group_of(g) is not None for g in members):
            raise EditRefused("already_grouped")
        group = api.group.add_group(self.file, name=name)
        api.group.assign_group(self.file, products=[self.by_guid(g) for g in members], group=group)
        self._set_params(group, {"Elemento": "group", "Modelo": group.GlobalId})
        for role, guid in enumerate(members):
            self._set_params(self.by_guid(guid), {"Papel": role})
        return group

    def copy_group(self, group, members):
        """One more placement of a group: an IfcGroup of the same model holding `members` (already copied)."""
        new = api.group.add_group(self.file, name=group.Name)
        api.group.assign_group(self.file, products=[self.by_guid(g) for g in members], group=new)
        self._set_params(new, {"Elemento": "group", "Modelo": self.group_model(group)})
        return new

    def join_group(self, guid, group, role):
        api.group.assign_group(self.file, products=[self.by_guid(guid)], group=group)
        self._set_params(self.by_guid(guid), {"Papel": role})

    def next_role(self, model):
        roles = [self.role_of(m) for g in self.group_copies(model) for m in self.group_members(g)]
        return max([r for r in roles if r is not None], default=-1) + 1

    def ungroup(self, group_guid):
        """The elements stay, independent from the other copies."""
        group = self.by_guid(group_guid)
        for guid in self.group_members(group):
            self._set_params(self.by_guid(guid), {"Papel": None})
        api.group.remove_group(self.file, group=group)

    def _leave_copied_groups(self, new):
        """copy_class also puts a copy into the original's groups: take it out of ours."""
        for rel in list(getattr(new, "HasAssignments", None) or ()):
            if rel.is_a("IfcRelAssignsToGroup") and self._params(rel.RelatingGroup).get("Elemento") == "group":
                api.group.unassign_group(self.file, products=[new], group=rel.RelatingGroup)

    def remove_empty_groups(self):
        for g in self.file.by_type("IfcGroup"):
            if self._params(g).get("Elemento") == "group" and not self.group_members(g):
                api.group.remove_group(self.file, group=g)

    def placement_between(self, guid, other):
        """The rigid move taking element `guid` onto its counterpart `other` (4x4, meters)."""
        return self._placement_si(self.by_guid(other)) @ np.linalg.inv(self._placement_si(self.by_guid(guid)))

    def move_to_storey(self, guid, storey_guid):
        """Put an element (and its doors / windows) in another storey; it stays where it is."""
        storey = self.storey(storey_guid)
        for g in self._with_fillings([guid]):
            api.spatial.assign_container(self.file, products=[self.by_guid(g)], relating_structure=storey)
