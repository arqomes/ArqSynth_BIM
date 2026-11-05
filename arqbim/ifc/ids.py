"""Checking the model against an IDS — buildingSMART's Information Delivery Specification, the
client's list of "what the model must say" — with IfcOpenShell's ifctester (LGPL-3.0, the owner's
go-ahead of 2026-10-21): which requirements are met, and by which elements not.

Reading the IDS and checking run on the IFC file as it is in memory (edits included)."""

import os
from dataclasses import dataclass, field


@dataclass
class Requirement:
    name: str
    description: str
    status: object               # True: met; False: not; None: not for this IFC version
    usage: str                   # "required" | "optional" | "prohibited"
    applicable: int              # elements it applies to
    failures: list = field(default_factory=list)    # [(GlobalId or None, element label, reason as ifctester says it)]
    result: str = ""             # what the panel says of it, when the check words it itself (0.70: certification)


class IdsError(ValueError):
    """The file is not an IDS that can be read (its text goes with it)."""


def check(ifc_model, path):
    """(title of the IDS, [Requirement]) for the model's IFC."""
    from ifctester import ids as ifctester_ids
    try:
        spec_file = ifctester_ids.open(path, validate=True)
    except Exception as exc:            # not XML, not an IDS, not valid against the IDS schema
        raise IdsError(str(exc)[:300]) from exc
    spec_file.validate(ifc_model.file)
    out = []
    for spec in spec_file.specifications:
        failures = []
        for facet in spec.requirements:
            for failure in facet.failures:
                e = failure["element"]
                label = "{} — {}".format(getattr(e, "Name", None) or "", e.is_a())
                failures.append((getattr(e, "GlobalId", None), label, str(failure["reason"])))
        out.append(Requirement(spec.name, spec.description or "", spec.status, spec.get_usage(),
                               len(spec.applicable_entities), failures))
    title = (getattr(spec_file, "info", None) or {}).get("title") or os.path.basename(path)
    return title, out
