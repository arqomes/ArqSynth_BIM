"""Typical floors (0.90), as the ArqSynth Modeler's equalised storeys ("="), mixed into IfcModel: storeys marked
as equal hold the same elements — what is drawn on one of them appears on the others, an edit made on one is
made on all, deleting one deletes all.

Each set of equal storeys is a group model (ifc/groups.py): on each storey one copy of the group (an IfcGroup,
"Pavimento" = that storey), every element with its role, the same on every storey; edits and deletions are then
repeated by the group machinery (model/bim). The storeys carry the set's id (ArqSynth_Parametros "PisoTipo").

The elements made during a command (tracked in `created` by _mark and copy_element) that stand on a typical
storey are put in its group copy and copied to the other storeys at the end of that same command
(replicate_typical: one undo step); walls joined to elements of the floor are joined, on each storey, to the
copies there."""

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.guid
import ifcopenshell.util.element

api = ifcopenshell.api
SKIP = ("door", "window", "group", "space", None)   # (doors / windows follow their wall; groups and rooms: no)


def _translation(dz):
    import numpy as np
    m = np.eye(4)
    m[2, 3] = dz
    return m


class TypicalMixin:
    created = None                 # GlobalIds of the elements made since the transaction began (None: not kept)
    # (0.465, the owner: «O botão = deve ligável e desligavel. Só faz o efeito quando o botão está ligado») the typical
    # floors' replication on (made, changed, deleted on one: on all) or off (each storey on its own meanwhile — what is
    # made then stays its own)
    typical_live = True

    # ------------------------------------------------------------ the sets

    def typical_sets(self):
        """{set id: [storey GlobalIds, lowest first]} of the storeys marked as equal."""
        out = {}
        for s in sorted(self.file.by_type("IfcBuildingStorey"), key=self._elevation):
            model = self._params(s).get("PisoTipo")
            if model:
                out.setdefault(model, []).append(s.GlobalId)
        return out

    def typical_of(self, storey_guid):
        """The id of the set of equal storeys a storey is in, or None."""
        s = self.by_guid(storey_guid) if storey_guid else None
        return self._params(s).get("PisoTipo") if s is not None else None

    def _storey_elements(self, storey_guid):
        """The program's elements contained in a storey (no doors / windows: they come with their walls), not
        in a group."""
        storey = self.storey(storey_guid)
        out = []
        for rel in storey.ContainsElements or ():
            for e in rel.RelatedElements:
                if self.kind_of(e.GlobalId) not in SKIP and self.group_of(e.GlobalId) is None:
                    out.append(e.GlobalId)
        return out

    def _typical_group(self, model, storey_guid, name):
        """The group copy of a set on a storey (made if it has none yet)."""
        for g in self.group_copies(model):
            if self._params(g).get("Pavimento") == storey_guid:
                return g
        group = api.group.add_group(self.file, name=name)
        self._set_params(group, {"Elemento": "group", "Modelo": model, "Pavimento": storey_guid})
        return group

    def _typical_name(self, model):
        copies = self.group_copies(model)
        return copies[0].Name if copies and copies[0].Name else "Piso tipo"

    # ------------------------------------------------------------ making and unmaking

    def make_typical(self, storeys, source, name):
        """These storeys (2+, GlobalIds) made equal: the elements of `source` (one of them) are the floor's —
        copied to the others. Returns the set's id."""
        model = ifcopenshell.guid.new()
        members = self._with_fillings(self._storey_elements(source))
        group = self._typical_group(model, source, name)
        for role, g in enumerate(members):
            self.join_group(g, group, role)
        for s in storeys:
            self._set_params(self.storey(s), {"PisoTipo": model})
        for s in storeys:
            if s != source:
                self._copy_into(members, source, s, model, name)
        return model

    def unmake_typical(self, model):
        """The storeys of a set no longer equal: their elements stay, each storey's on its own."""
        for g in list(self.group_copies(model)):
            self.ungroup(g.GlobalId)
        for s in self.file.by_type("IfcBuildingStorey"):
            if self._params(s).get("PisoTipo") == model:
                self._set_params(s, {"PisoTipo": None})

    # ------------------------------------------------------------ copies

    def _copy_into(self, guids, source, target, model, name):
        """Copies of these elements of the storey `source` on `target`, in its group copy with the same roles;
        walls copied together stay joined, and those joined to walls already on the floor are joined to the
        ones there. Returns the walls already there whose shape the joints changed."""
        levels = {g: z for g, _n, z in self.storeys()}
        dz = levels[target] - levels[source]
        group = self._typical_group(model, target, name)
        self.copy_map = {}
        copies = {}
        for g in guids:
            if self.kind_of(g) in ("door", "window"):
                continue                                  # (copied with their wall)
            new = self.copy_element(g)
            self.transform(new.GlobalId, _translation(dz))
            self.move_to_storey(new.GlobalId, target)
            copies[g] = new.GlobalId
        for original, copy in self.copy_map.items():
            role = self.role_of(original)
            if role is not None:
                self.join_group(copy, group, role)
        there = {self.role_of(m): m for m in self.group_members(group)}
        # (tied to a column / a cap of the floor: to the same one on this storey, 0.94)
        self.remap_ties(self.copy_map, lambda ref: there.get(self.role_of(ref)) if self.group_of(ref) else None)
        touched = set()
        joints = {j[0].id(): j for g in copies for j in self.wall_joints(g)}
        for _rel, through, through_end, butt, butt_end in joints.values():
            a = copies.get(through) or (there.get(self.role_of(through)) if self.group_of(through) else None)
            b = copies.get(butt) or (there.get(self.role_of(butt)) if self.group_of(butt) else None)
            if a is None or b is None or (through not in copies and butt not in copies):
                continue
            self.connect_walls(a, through_end, b, butt_end)
            touched |= {x for x in (a, b) if x not in copies.values()}
        if touched:
            self.rejoin(sorted(touched | set(copies.values())))
        return sorted(touched)

    def replicate_typical(self):
        """At the end of a command: the elements it made on a typical storey join that storey's group copy and
        are copied to the set's other storeys. Returns the existing elements whose shape changed (walls joined)."""
        made, self.created = list(self.created or ()), None          # (the copies made here are not tracked)
        if not made or not self.typical_live:                       # (0.465: «=» off — it stays on its storey)
            return []
        sets = self.typical_sets()
        if not sets:
            return []
        by_storey = {}
        for g in made:
            if self.by_guid(g) is None or self.kind_of(g) in SKIP or self.group_of(g) is not None:
                continue
            storey = self.storey_of(g)
            model = self.typical_of(storey)
            if model is None or len(sets.get(model, ())) < 2:
                continue
            by_storey.setdefault((model, storey), []).append(g)
        changed = []
        for (model, storey), guids in by_storey.items():
            name = self._typical_name(model)
            group = self._typical_group(model, storey, name)
            guids = self._with_fillings(guids)
            role = self.next_role(model)
            for g in guids:
                self.join_group(g, group, role)
                role += 1
            for other in sets[model]:
                if other != storey:
                    changed += self._copy_into(guids, storey, other, model, name)
        return sorted(set(changed))
