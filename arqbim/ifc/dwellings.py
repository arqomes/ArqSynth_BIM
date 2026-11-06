"""(0.416) The Verifier's data in the IFC, mixed into IfcModel:

- what the architect chose: a room's use («Uso» in ArqSynth_Parametros: verify/uses.USES's key) and the dwelling it
  is in («Fogo»: its name) — kept, never guessed again;
- the project's verification settings (on IfcProject: the country, the laws checked, the building's use, the kind of
  work, its height);
- what the Verifier found, written to the file when it is saved and only then: each room's use in IfcSpace.ObjectType
  and each dwelling an IfcZone (its name; LongName its type «T2»; its rooms by IfcRelAssignsToGroup) — read by Revit and
  the other programs. In memory they are found again at every change (verify/reader.py), so they are put in just
  before writing and taken out after (stamped()), and those of a file opened are taken out (strip_dwellings)."""

import contextlib
import json

import ifcopenshell.api

api = ifcopenshell.api
ZONE_KIND = "fogo"          # the Elemento of the program's dwellings (IfcZone)
SETTINGS_KEY = "Verificacao"


class DwellingMixin:
    # ------------------------------------------------------------ what the architect chose

    def space_choices(self, guid):
        """(use key or None, dwelling name or None) a room was given by hand."""
        space = self.by_guid(guid)
        if space is None:
            return None, None
        params = self._params(space)
        return params.get("Uso") or None, params.get("Fogo") or None

    def set_space_use(self, guid, key):
        """A room's use chosen (a verify/uses key), or None: found again from its name and contents."""
        space = self.by_guid(guid)
        if space is not None:
            self._set_params(space, {"Uso": key or None})

    def set_space_dwelling(self, guid, name):
        """The dwelling a room is in, by its name (a duplex, two houses side by side…), or None: found from its doors."""
        space = self.by_guid(guid)
        if space is not None:
            self._set_params(space, {"Fogo": (name or "").strip() or None})

    # ------------------------------------------------------------ the project's settings

    def verify_settings(self):
        """The project's verification settings ({} when none were set): see verify/project.py."""
        projects = self.file.by_type("IfcProject")
        if not projects:
            return {}
        text = self._params(projects[0]).get(SETTINGS_KEY)
        try:
            return json.loads(text) if text else {}
        except (TypeError, ValueError):
            return {}

    def set_verify_settings(self, values):
        projects = self.file.by_type("IfcProject")
        if projects:
            self._set_params(projects[0], {SETTINGS_KEY: json.dumps(values, ensure_ascii=False, sort_keys=True)})

    # ------------------------------------------------------------ written with the file

    def _zones(self):
        return [z for z in self.file.by_type("IfcZone") if self._params(z).get("Elemento") == ZONE_KIND]

    def _drop_zone(self, zone):
        for rel in list(getattr(zone, "IsDefinedBy", None) or ()):
            if rel.is_a("IfcRelDefinesByProperties"):
                api.pset.remove_pset(self.file, product=zone, pset=rel.RelatingPropertyDefinition)
        api.group.remove_group(self.file, group=zone)

    def strip_dwellings(self):
        """The dwellings a file had (written when it was saved) taken out of memory: they are found again from the
        rooms. Outside any transaction (nothing to undo). How many."""
        zones = self._zones()
        for zone in zones:
            self._drop_zone(zone)
        return len(zones)

    @contextlib.contextmanager
    def stamped(self, rooms, dwellings, labels, kind_name="Fogo"):
        """Inside: each room's use in its ObjectType (labels: {room: name}), each dwelling an IfcZone with its rooms —
        for the file being written; after: the model as it was. rooms: {GlobalId: use key} (unused), dwellings:
        [verify.dwellings.Dwelling]."""
        before = {}
        made = []
        try:
            for guid, text in labels.items():
                space = self.by_guid(guid)
                if space is not None and text:
                    before[guid] = space.ObjectType
                    space.ObjectType = text
            for d in dwellings:
                members = [self.by_guid(g) for g in d.rooms]
                members = [m for m in members if m is not None]
                if not members:
                    continue
                zone = api.root.create_entity(self.file, ifc_class="IfcZone", name=d.name)
                zone.LongName = d.typology
                zone.ObjectType = kind_name
                made.append(zone)
                self._set_params(zone, {"Elemento": ZONE_KIND, "Tipologia": d.typology,
                                        "AreaUtil": round(float(d.useful_area), 2)})
                api.group.assign_group(self.file, products=members, group=zone)
            yield
        finally:
            for zone in made:
                self._drop_zone(zone)
            for guid, value in before.items():
                space = self.by_guid(guid)
                if space is not None:
                    space.ObjectType = value
