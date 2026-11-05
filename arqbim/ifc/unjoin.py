"""(0.333) Two elements «unjoined» by hand, as Revit's Unjoin Geometry: their cut and their faces no longer cleaned up
together (model/cut_joins.py, model/seen_joins.py) — the line between them drawn where they meet, a wall's layers no
longer turning the other's corner, an overlap left as it is. Kept in both elements: ArqSynth_Parametros, Desunidos —
the other ones' GlobalIds, ";" between (an IfcText). Only the drawing changes: their shapes in the IFC are their own,
as always."""

from .edit import PARAM_PSET

PROPERTY = "Desunidos"


def apart_from(ifc, guid):
    """The elements an element is unjoined from (frozenset of GlobalIds)."""
    element = ifc.by_guid(guid) if ifc is not None else None
    if element is None:
        return frozenset()
    text = ifc._params(element).get(PROPERTY)
    return frozenset(g for g in str(text).split(";") if g) if text else frozenset()


def pairs(ifc, guids):
    """{frozenset((a, b))} of the elements among `guids` unjoined from each other."""
    among = set(guids)
    found = set()
    for guid in among:
        for other in apart_from(ifc, guid):
            if other in among and other != guid:
                found.add(frozenset((guid, other)))
    return found


def set_apart(ifc, a, b, apart=True):
    """Two elements unjoined (apart) or joined again, kept in both. Runs inside the caller's IFC transaction."""
    for mine, other in ((a, b), (b, a)):
        kept = set(apart_from(ifc, mine))
        if apart:
            kept.add(other)
        else:
            kept.discard(other)
        value = ifc.file.create_entity("IfcText", ";".join(sorted(kept))) if kept else None
        ifc.set_property(mine, PARAM_PSET, PROPERTY, value)    # (its own set, never its type's: shared)
