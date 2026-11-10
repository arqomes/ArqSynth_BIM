"""(0.524) The Project navigator's controls, as Blender's Outliner: on each element (or a whole group / category)
whether it can be selected and edited (locked: not), shown, rendered, printed. Kept in the IFC (the pset
«ArqSynth_Controlo», ifc/model.IfcModel.set_control), read once when a file is opened and then kept up to date with
the elements each change touched — never by sweeping the model on every edit.

    locked     not picked in the views (so neither moved nor edited), refused by Delete / Duplicate
    hidden     not drawn in the views
    no_render  left out of the renders (Mitsuba) and of the Realistic view style
    no_print   left out of the drawings: sheets, PDF, the views exported
"""

from ..i18n import t
from .document import IfcCommand

FLAGS = ("locked", "hidden", "no_render", "no_print")
# the navigator's columns, left to right, and the flag each switches (its icon "on" = the flag off)
COLUMNS = ("locked", "hidden", "no_render", "no_print")


def _cache(doc):
    found = getattr(doc, "_controls", None)
    if found is None:
        try:
            found = {g: set(f) for g, f in doc.ifc.all_controls().items()}
        except (AttributeError, RuntimeError):
            found = {}
        doc._controls = found
    return found


def reload(doc):
    """Everything read again (a file opened, an undo of many things)."""
    doc._controls = None
    return _cache(doc)


def refresh(doc, changed):
    """The flags of the elements a change touched read again (None: all of them)."""
    if changed is None or getattr(doc, "_controls", None) is None:
        return reload(doc)
    cache = _cache(doc)
    for guid in changed:
        if not isinstance(guid, str):
            continue
        try:
            flags = doc.ifc.controls_of(guid)
        except (AttributeError, RuntimeError):
            flags = set()
        if flags:
            cache[guid] = flags
        else:
            cache.pop(guid, None)
    return cache


def flags_of(doc, guid):
    return frozenset(_cache(doc).get(guid, ()))


def has(doc, guid, flag):
    return flag in _cache(doc).get(guid, ())


def ids_with(doc, flag):
    return {g for g, f in _cache(doc).items() if flag in f}


def state_of(doc, guids, flag):
    """True: all of them have it; False: none; None: some (a group shown half so)."""
    guids = list(guids)
    if not guids:
        return False
    n = sum(1 for g in guids if has(doc, g, flag))
    return True if n == len(guids) else False if n == 0 else None


def set_flag(doc, guids, flag, on):
    """The flag switched on (or off) on these elements: one undo step; their shapes are not made again. Returns how
    many changed."""
    if flag not in FLAGS:
        raise ValueError(flag)
    guids = [g for g in guids if isinstance(g, str) and has(doc, g, flag) != bool(on)]
    if not guids:
        return 0
    done = doc.execute(IfcCommand(t("cmd.control_" + flag), lambda ifc: ifc.set_control(guids, flag, on),
                                  touched=guids, plan=False)).result
    refresh(doc, guids)
    return done
