"""Getting a model ready for IFC certification (0.70, Phase 5, step 5): the checks buildingSMART's
validation and a certifier look at first — the file's header (which program, which model view), the
schema and its rules, the spatial structure, the units, georeferencing, GlobalIds, quantities, types,
materials, names and 3D shapes. Each check is a Requirement (as the IDS ones: the same panel shows
them); the ones a certifier only recommends are "optional".

This is a preparation, not the certification: that is buildingSMART's, with their own test files."""

import html
import re

import ifcopenshell
import ifcopenshell.util.element

from .. import __version__
from ..i18n import t
from .ids import Requirement

# the element classes whose base quantities, type and material a certifier expects (the program makes them)
WITH_QUANTITIES = ("IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcFooting", "IfcPipeSegment", "IfcDuctSegment",
                   "IfcPipeFitting", "IfcDuctFitting", "IfcDoor", "IfcWindow")
_GUID = re.compile(r"[0-3][0-9A-Za-z_$]{21}")
MAX_LISTED = 200            # elements listed under one check (the count says how many in all)


def stamp_header(ifc_model, path=None):
    """The header the program writes (0.70): its own name and version as the originating system,
    IfcOpenShell as the preprocessor, the file's name. The model view declared (IfcOpenShell's) stays."""
    name = ifc_model.file.header.file_name
    name.originating_system = "ArqSynth BIM {}".format(__version__)
    name.preprocessor_version = "IfcOpenShell {}".format(ifcopenshell.version)
    if path:
        import os
        name.name = os.path.basename(path)


def _label(e):
    return "{} — {}".format(getattr(e, "Name", None) or "", e.is_a())


def _req(name, description, failures, applicable, optional=False, result=None):
    met = not failures
    return Requirement(name, description, met, "optional" if optional else "required", applicable,
                       failures[:MAX_LISTED], result or "")


def _header(f):
    h = f.header
    description = " ".join(h.file_description.description or ())
    view = re.search(r"ViewDefinition\s*\[([^\]]*)\]", description)
    system = h.file_name.originating_system or ""
    failures = []
    if view is None:
        failures.append((None, t("cert.no_view"), description or "—"))
    if not system or system.startswith("IfcOpenShell"):
        failures.append((None, t("cert.no_system"), system or "—"))
    result = t("cert.header_ok", view=view.group(1) if view else "—", system=system or "—")
    return _req(t("cert.header"), t("cert.header_tip"), failures, 1, result=result if not failures else None)


def _schema(ifc_model):
    errors = ifc_model.validate(express_rules=True)
    failures = [(None, t("cert.schema_error"), e[:300]) for e in errors]
    result = t("cert.schema_ok", schema=ifc_model.file.schema) if not errors else t("cert.n_errors", n=len(errors))
    return _req(t("cert.schema"), t("cert.schema_tip"), failures, 1, result=result)


def _spatial(f):
    failures = []
    projects = f.by_type("IfcProject")
    if len(projects) != 1:
        failures.append((None, t("cert.projects", n=len(projects)), ""))
    for cls in ("IfcSite", "IfcBuilding", "IfcBuildingStorey"):
        if not f.by_type(cls):
            failures.append((None, t("cert.missing", what=cls), ""))
    elements = [e for e in f.by_type("IfcElement") if not e.is_a("IfcFeatureElement")]
    for e in elements:
        host = e
        while host is not None and ifcopenshell.util.element.get_container(host) is None:
            host = ifcopenshell.util.element.get_aggregate(host) or ifcopenshell.util.element.get_nest(host)
        if host is None:
            failures.append((e.GlobalId, _label(e), t("cert.not_contained")))
    result = (t("cert.spatial_ok", s=len(f.by_type("IfcBuildingStorey")), n=len(elements)) if not failures
              else t("cert.n_problems", n=len(failures)))
    return _req(t("cert.spatial"), t("cert.spatial_tip"), failures, len(elements), result=result)


def _units(f):
    found = set()
    for assignment in f.by_type("IfcUnitAssignment"):
        for unit in assignment.Units or ():
            kind = getattr(unit, "UnitType", None)
            if kind:
                found.add(kind)
    needed = ("LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT", "PLANEANGLEUNIT")
    failures = [(None, t("cert.unit." + k.lower()), t("cert.unit_missing")) for k in needed if k not in found]
    return _req(t("cert.units"), t("cert.units_tip"), failures, len(needed),
                result=t("cert.units_ok") if not failures else t("cert.n_missing", n=len(failures)))


def _georeference(f):
    sites = f.by_type("IfcSite")
    by_map = bool(f.by_type("IfcMapConversion"))
    by_site = any(s.RefLatitude and s.RefLongitude for s in sites)
    failures = [] if by_map or by_site else [(None, t("cert.no_georef"), t("cert.georef_how"))]
    result = t("cert.georef_map") if by_map else t("cert.georef_site") if by_site else t("cert.georef_none")
    return _req(t("cert.georef"), t("cert.georef_tip"), failures, 1, optional=True, result=result)


def _guids(f):
    seen, failures = {}, []
    roots = f.by_type("IfcRoot")
    for e in roots:
        g = e.GlobalId
        if not g or not _GUID.fullmatch(g):
            failures.append((None, _label(e), t("cert.bad_guid", g=g or "—")))
        elif g in seen:
            failures.append((g, _label(e), t("cert.same_guid", other=_label(seen[g]))))
        else:
            seen[g] = e
    return _req(t("cert.guids"), t("cert.guids_tip"), failures, len(roots),
                result=t("cert.guids_ok", n=len(roots)) if not failures else t("cert.n_problems", n=len(failures)))


def _elements(f):
    return [e for cls in WITH_QUANTITIES for e in f.by_type(cls)]


def _quantities(f):
    elements = _elements(f)
    failures = []
    for e in elements:
        psets = ifcopenshell.util.element.get_psets(e, qtos_only=True)
        if not any(name.endswith("BaseQuantities") for name in psets):
            failures.append((e.GlobalId, _label(e), t("cert.no_quantities")))
    return _req(t("cert.quantities"), t("cert.quantities_tip"), failures, len(elements), optional=True,
                result=t("cert.all_n", n=len(elements)) if not failures else t("cert.n_of", f=len(failures),
                                                                                n=len(elements)))


def _types_materials(f):
    elements = _elements(f)
    failures = []
    for e in elements:
        missing = []
        if ifcopenshell.util.element.get_type(e) is None:
            missing.append(t("cert.type"))
        if ifcopenshell.util.element.get_material(e) is None:
            missing.append(t("cert.material"))
        if missing:
            failures.append((e.GlobalId, _label(e), t("cert.without", what=", ".join(missing))))
    return _req(t("cert.types"), t("cert.types_tip"), failures, len(elements), optional=True,
                result=t("cert.all_n", n=len(elements)) if not failures else t("cert.n_of", f=len(failures),
                                                                                n=len(elements)))


def _names_and_shapes(f):
    elements = [e for e in f.by_type("IfcElement") if not e.is_a("IfcFeatureElement")]
    failures = []
    for e in elements:
        reps = e.Representation.Representations if e.Representation else ()
        if not any(r.RepresentationIdentifier == "Body" for r in reps):
            failures.append((e.GlobalId, _label(e), t("cert.no_body")))
        elif not (e.Name or "").strip():
            failures.append((e.GlobalId, _label(e), t("cert.no_name")))
    return _req(t("cert.shapes"), t("cert.shapes_tip"), failures, len(elements),
                result=t("cert.all_n", n=len(elements)) if not failures else t("cert.n_of", f=len(failures),
                                                                                n=len(elements)))


def check(ifc_model):
    """(title, [Requirement]) — the model as it would be saved now (its header stamped as on saving)."""
    stamp_header(ifc_model)
    f = ifc_model.file
    out = [_header(f), _schema(ifc_model), _spatial(f), _units(f), _guids(f), _names_and_shapes(f),
           _quantities(f), _types_materials(f), _georeference(f)]
    return t("cert.title", schema=f.schema), out


def report_html(title, requirements, model_name=""):
    """The checks as a page to keep or send (a certifier, a client): each check, its result, what fails."""
    rows = []
    for r in requirements:
        mark = "✓" if r.status else ("—" if r.status is None else "✗")
        colour = "#2e8b57" if r.status else ("#8a8a8a" if r.status is None else "#d0453f")
        rows.append('<tr><td style="color:{}"><b>{} {}</b><br><small>{}</small></td><td>{}</td></tr>'.format(
            colour, mark, html.escape(r.name), html.escape(r.description), html.escape(r.result or "")))
        for _guid, label, reason in r.failures:
            rows.append('<tr><td style="padding-left:2em">{}</td><td>{}</td></tr>'.format(
                html.escape(label), html.escape(reason)))
    return ("<!doctype html><html><head><meta charset='utf-8'><title>{t}</title>"
            "<style>body{{font-family:sans-serif;margin:2em}}td{{border-bottom:1px solid #ddd;padding:4px 8px;"
            "vertical-align:top}}table{{border-collapse:collapse;width:100%}}</style></head><body>"
            "<h1>{t}</h1><p>{m}</p><table>{rows}</table><p><small>{note}</small></p></body></html>").format(
        t=html.escape(title), m=html.escape(model_name), rows="".join(rows), note=html.escape(t("cert.note")))
