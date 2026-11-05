"""Older templates brought up to this layout (SCHEMA_VERSION): each step from one schema_version to the next, in turn;
what each changed is said (Notice), never silently. A template from a *newer* layout is read as it is — what is not
known kept — and not overwritten by this program (it may be saved under another name).

Version 0 (the first drafts, no «schema_version»): «units» a plain text ("m"), a storey's level as «level», colours
as [r, g, b] (0–1)."""

from dataclasses import dataclass

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Notice:
    code: str          # migrated, newer
    detail: str = ""

    def text(self, lang="pt"):
        said = {"pt": {"migrated": "Modelo de uma versão anterior do formato ({}): convertido para a atual.",
                       "newer": "Modelo feito por uma versão mais nova do formato ({}): o que este programa não "
                                "conhece fica como está; não é regravado por cima."},
                "en": {"migrated": "A template of an earlier format version ({}): converted to the current one.",
                       "newer": "A template made by a newer format version ({}): what this program does not know is "
                                "kept; it is not saved over."}}
        return said.get(lang, said["en"])[self.code].format(self.detail)


def _hex(rgb):
    try:
        r, g, b = (min(max(float(c), 0.0), 1.0) for c in rgb[:3])
    except (TypeError, ValueError):
        return None
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def _from_0(data):
    if isinstance(data.get("units"), str):
        data["units"] = {"length": data["units"]}
    for storey in data.get("storeys") or ():
        if isinstance(storey, dict) and "elevation" not in storey and "level" in storey:
            storey["elevation"] = storey.pop("level")
    for material in data.get("materials") or ():
        if isinstance(material, dict) and isinstance(material.get("color"), (list, tuple)):
            material["color"] = _hex(material["color"]) or "#cccccc"
    data.setdefault("format", "arqsynth-template")
    data.setdefault("version", 1)
    return data


STEPS = {0: _from_0}            # schema_version -> the step to the next


def upgrade(data):
    """(data, [Notice]) — `data` (a dict, changed in place) in this layout as far as it can be."""
    notices = []
    try:
        version = int(data.get("schema_version", 0))
    except (TypeError, ValueError):
        version = 0
    if version > SCHEMA_VERSION:
        notices.append(Notice("newer", str(version)))
        return data, notices
    start = version
    while version < SCHEMA_VERSION:
        data = STEPS[version](data)
        version += 1
    data["schema_version"] = max(version, SCHEMA_VERSION)
    if start < SCHEMA_VERSION:
        notices.append(Notice("migrated", str(start)))
    return data, notices
