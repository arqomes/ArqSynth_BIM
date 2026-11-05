"""Team work on a shared folder (Phase 4, step 6; the owner's choice of 2026-10-21: a central
model in a shared folder — the office server, OneDrive… — with reservations, no server).

Each person works on a local copy of the central IFC. "Synchronise" puts together, entity by
entity, what changed in the local copy and in the central one since the last synchronisation
(a three-way merge of the IFC text, as IfcOpenShell's ifcmerge does): IfcOpenShell keeps the
numbers (#123) of what it reads and writes, so an entity nobody touched has the same line in
the three files. New entities of the local copy are renumbered after the central's; lists both
changed (the elements of a storey…) are joined. Reservations — who is changing which elements
— are kept beside the central model, so that two people do not change the same thing.
"""

import json
import os
import re
import time

LINE = re.compile(r"^#(\d+)\s*=\s*(.*);\s*$")
REF = re.compile(r"#(\d+)")


# ---------------------------------------------------------------- the IFC text

def parse(text):
    """(header, {id: entity text "IFCWALL(…)"}) of an IFC file written one entity per line."""
    head, _, rest = text.partition("DATA;")
    body = rest.rpartition("ENDSEC;")[0]
    entities = {}
    for line in body.splitlines():
        m = LINE.match(line.strip())
        if m:
            entities[int(m.group(1))] = m.group(2)
    return head + "DATA;", entities


def write(header, entities):
    lines = ["#{}={};".format(i, entities[i]) for i in sorted(entities)]
    return header + "\n" + "\n".join(lines) + "\nENDSEC;\nEND-ISO-10303-21;\n"


def _renumber(text, mapping):
    return REF.sub(lambda m: "#{}".format(mapping.get(int(m.group(1)), int(m.group(1)))), text)


def split_args(entity):
    """("IFCWALL", [top-level arguments as text]) of an entity's text."""
    name, _, rest = entity.partition("(")
    rest = rest[:rest.rfind(")")]
    args, depth, quote, start = [], 0, False, 0
    k = 0
    while k < len(rest):
        c = rest[k]
        if quote:
            if c == "'":
                if k + 1 < len(rest) and rest[k + 1] == "'":
                    k += 1                                   # '' inside a string
                else:
                    quote = False
        elif c == "'":
            quote = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
        elif c == "," and depth == 0:
            args.append(rest[start:k])
            start = k + 1
        k += 1
    args.append(rest[start:])
    return name, args


def _ref_list(arg):
    """[ids] if the argument is a list of references "(#1,#2)", else None."""
    arg = arg.strip()
    if not (arg.startswith("(") and arg.endswith(")")):
        return None
    items = [x.strip() for x in arg[1:-1].split(",") if x.strip()]
    if not items or not all(re.fullmatch(r"#\d+", x) for x in items):
        return None
    return [int(x[1:]) for x in items]


def _merge_entity(base, mine, theirs):
    """The three versions of one entity -> (merged text, conflict?): argument by argument, each
    side's change kept; lists of references changed on both sides joined."""
    name_b, b = split_args(base)
    name_m, m = split_args(mine)
    name_t, t = split_args(theirs)
    if not (name_b == name_m == name_t and len(b) == len(m) == len(t)):
        return theirs, True
    out, conflict = [], False
    for xb, xm, xt in zip(b, m, t):
        if xm == xb or xm == xt:
            out.append(xt)
        elif xt == xb:
            out.append(xm)
        else:
            lb, lm, lt = _ref_list(xb) or [], _ref_list(xm), _ref_list(xt)
            if lm is not None and lt is not None:
                removed = set(lb) - set(lm)
                joined = [i for i in lt if i not in removed] + [i for i in lm if i not in lb and i not in lt]
                out.append("(" + ",".join("#{}".format(i) for i in joined) + ")")
            else:
                out.append(xt)                               # both changed it differently: theirs stays
                conflict = True
    return "{}({})".format(name_t, ",".join(out)), conflict


def merge(base_text, mine_text, theirs_text):
    """Three-way merge of IFC files: base = the central model at the last synchronisation, mine =
    the local copy, theirs = the central model now. Returns (merged text, [conflicting entity
    texts]); on a conflict the central's version stays."""
    _, base = parse(base_text)
    _, mine = parse(mine_text)
    header, theirs = parse(theirs_text)
    result = dict(theirs)
    # what is new here gets numbers after everything that exists on both sides
    start = max([0] + list(theirs) + list(mine) + list(base)) + 1
    added = sorted(set(mine) - set(base))
    mapping = {old: start + k for k, old in enumerate(added)}
    for old in added:
        result[mapping[old]] = _renumber(mine[old], mapping)
    conflicts = []
    for i, text in mine.items():
        if i in base and text != base[i]:
            text = _renumber(text, mapping)
            if i not in theirs:
                conflicts.append(base[i])                     # changed here, removed there: removed stays
            elif theirs[i] == base[i]:
                result[i] = text
            elif theirs[i] != text:
                result[i], conflict = _merge_entity(base[i], text, theirs[i])
                if conflict:
                    conflicts.append(theirs[i])
    for i in set(base) - set(mine):                           # removed here
        if i in theirs:
            if theirs[i] == base[i]:
                del result[i]
            else:
                conflicts.append(theirs[i])                    # changed there: it stays
    # nothing may point at what is gone: what is still needed comes back
    missing = {int(r) for text in result.values() for r in REF.findall(text)} - set(result)
    while missing:
        for i in missing:
            source = theirs.get(i) or base.get(i)
            if source is None:
                raise ValueError("merged IFC refers to #{} that exists nowhere".format(i))
            result[i] = source
        missing = {int(r) for text in result.values() for r in REF.findall(text)} - set(result)
    return write(header, result), conflicts


# ---------------------------------------------------------------- the local copy

VIEWS = "__views__"            # the reservation of the views (sections, sheets, dimensions, view templates)
VIEW_KEYS = ("sections", "last_section", "sheets", "dimensions", "templates", "view_templates", "title_block",
             "view_props", "views3d", "grids", "annotations", "dim_style",   # (drawn in the views 0.120; 0.124)
             "graphic_style", "schedules", "details",                        # (0.126; 0.131; 0.133)
             "clashes", "images", "cad", "clouds",                                            # (the clashes' statuses, 0.150; images 0.154)
             "presentation", "panoramas")                                                     # (the Presentation's, 0.363; 0.368)


def share_root():
    """Where the local copies of shared projects are kept."""
    from ..paths import local_base, user_dir
    root = os.environ.get("ARQBIM_SHARE_DIR") or user_dir(local_base(), "partilha")
    os.makedirs(root, exist_ok=True)
    return root


def local_copy(central):
    """The local copy of a central model (same file name, in its own folder)."""
    import hashlib
    key = hashlib.sha1(os.path.normcase(os.path.abspath(central)).encode("utf-8")).hexdigest()[:16]
    folder = os.path.join(share_root(), key)
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, os.path.basename(central))


def base_copy(local):
    """The central model as it was at the last synchronisation (what both sides changed from)."""
    return os.path.splitext(local)[0] + ".base.ifc"


def _link(local):
    return os.path.join(os.path.dirname(local), "link.json")


def central_of(local):
    """The central model a local copy belongs to, or None (not a shared project)."""
    if not local:
        return None
    try:
        with open(_link(local), encoding="utf-8") as f:
            return json.load(f).get("central")
    except (OSError, ValueError):
        return None


def _sidecars(ifc_path, write=False):
    """A project's files: its IFC, its views (".arqsynthbim" — read, an old ".arqbim" too), its notes."""
    from .document import sidecar_path
    stem = os.path.splitext(ifc_path)[0]
    return {"ifc": ifc_path, "arqbim": sidecar_path(ifc_path, write=write), "bcfzip": stem + ".bcfzip"}


def _copy(src, dst):
    import shutil
    if os.path.exists(src):
        tmp = dst + ".tmp"
        shutil.copyfile(src, tmp)
        os.replace(tmp, dst)


def open_shared(central):
    """The local copy to work on (made from the central model the first time; kept otherwise —
    with whatever was not synchronised yet)."""
    local = local_copy(central)
    if not os.path.exists(local):
        with lock(_lock_of(central)):
            for kind, src in _sidecars(central).items():
                _copy(src, _sidecars(local, write=True)[kind])
            _copy(central, base_copy(local))
    with open(_link(local), "w", encoding="utf-8") as f:
        json.dump({"central": os.path.abspath(central)}, f)
    return local


def _lock_of(central):
    return os.path.splitext(central)[0] + ".lock"


# ---------------------------------------------------------------- synchronising

class SyncResult:
    def __init__(self, conflicts, theirs_changed, mine_changed, views):
        self.conflicts = conflicts            # entity texts where the central's version stayed
        self.theirs_changed = theirs_changed  # others had changed the central model
        self.mine_changed = mine_changed      # this copy had changes that went to the central model
        self.views = views                    # "sent" | "received" | None


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write_text(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def _merge_views(local_arqbim, central_arqbim, holder):
    """The views go with the views reservation: its holder sends them; the others receive them
    (their own sketches and guides stay theirs)."""
    def load(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None
    mine, theirs = load(local_arqbim), load(central_arqbim)
    if mine is not None and theirs is not None and all(mine.get(k) == theirs.get(k) for k in VIEW_KEYS):
        return None                                     # the same views on both sides
    if holder:
        if mine is not None:
            merged = dict(theirs or {"format": "arqbim-sketches", "version": 1, "origin": mine.get("origin")})
            for key in VIEW_KEYS:
                merged.pop(key, None)
                if key in mine:
                    merged[key] = mine[key]
            _write_json(central_arqbim, merged)
        return "sent"
    if theirs is None:
        return None
    merged = dict(mine or {"format": "arqbim-sketches", "version": 1, "origin": theirs.get("origin")})
    for key in VIEW_KEYS:
        merged.pop(key, None)
        if key in theirs:
            merged[key] = theirs[key]
    _write_json(local_arqbim, merged)
    return "received"


def _write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def _merge_notes(local_bcf, central_bcf):
    """Notes joined by their GUID (the comments of both kept); both sides get the result."""
    from . import notes as notes_model

    def load(path):
        try:
            return notes_model.load(path) if os.path.exists(path) else []
        except ValueError:
            return []
    mine, theirs = load(local_bcf), load(central_bcf)
    if not mine and not theirs:
        return
    by_guid = {n.guid: n for n in theirs}
    for n in mine:
        other = by_guid.get(n.guid)
        if other is not None:
            seen = {tuple(c) for c in n.comments}
            n.comments = list(n.comments) + [c for c in other.comments if tuple(c) not in seen]
            n.comments.sort(key=lambda c: c[1])
        by_guid[n.guid] = n
    joined = list(by_guid.values())
    notes_model.save(joined, central_bcf)
    notes_model.save(joined, local_bcf)


def sync(local, user):
    """Synchronise a saved local copy with its central model: the IFC merged (three-way), the
    views sent or received (VIEWS reservation), the notes joined. Afterwards the local copy, the
    central model and the base are the same IFC. Returns a SyncResult."""
    central = central_of(local)
    if central is None:
        raise ValueError("not a shared project")
    with lock(_lock_of(central)):
        base_text, mine_text, theirs_text = _read(base_copy(local)), _read(local), _read(central)
        theirs_changed = parse(theirs_text)[1] != parse(base_text)[1]
        mine_changed = parse(mine_text)[1] != parse(base_text)[1]
        conflicts = []
        if mine_changed:
            merged, conflicts = merge(base_text, mine_text, theirs_text) if theirs_changed else (mine_text, [])
            _write_text(central, merged)
        else:
            merged = theirs_text
        _write_text(local, merged)
        _write_text(base_copy(local), merged)
        holder = Reservations(central).read().get(VIEWS, (None,))[0] == user
        views = _merge_views(_sidecars(local)["arqbim"], _sidecars(central)["arqbim"], holder)
        _merge_notes(_sidecars(local)["bcfzip"], _sidecars(central)["bcfzip"])
    return SyncResult(conflicts, theirs_changed, mine_changed, views)


def share(ifc_path, folder):
    """Put a saved project (its IFC, views and notes) in a shared folder as the central model;
    returns the central model's path. An existing one of the same name is not overwritten."""
    central = os.path.join(folder, os.path.basename(ifc_path))
    if os.path.exists(central):
        raise FileExistsError(central)
    for kind, src in _sidecars(ifc_path).items():
        _copy(src, _sidecars(central, write=True)[kind])
    return central


# ---------------------------------------------------------------- reservations

class Reservations:
    """Who is changing which elements: a JSON file beside the central model, changed under a
    lock file (two people at the same moment wait for each other)."""

    def __init__(self, central):
        self.path = os.path.splitext(central)[0] + ".reservas.json"
        self.lock_path = os.path.splitext(central)[0] + ".reservas.lock"

    def read(self):
        """{GlobalId or "__views__": (user, since)}"""
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return {}
        return {k: (v.get("user", "?"), v.get("since", "")) for k, v in data.items() if isinstance(v, dict)}

    def _write(self, entries):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({k: {"user": u, "since": s} for k, (u, s) in entries.items()}, f, ensure_ascii=False)
        os.replace(tmp, self.path)

    def take(self, user, keys):
        """Reserve `keys` for `user`; returns those someone else already has ({key: user})."""
        with lock(self.lock_path):
            entries = self.read()
            taken = {k: entries[k][0] for k in keys if k in entries and entries[k][0] != user}
            now = time.strftime("%Y-%m-%dT%H:%M:%S")
            for k in keys:
                if k not in taken and k not in entries:
                    entries[k] = (user, now)
            self._write(entries)
        return taken

    def give_back(self, user, keys=None):
        """Give back `keys` (all of the user's: None)."""
        with lock(self.lock_path):
            entries = self.read()
            for k in [k for k, (u, _s) in entries.items() if u == user and (keys is None or k in keys)]:
                del entries[k]
            self._write(entries)


class lock:
    """A lock file made exclusively (works on a shared folder); a lock older than `stale` seconds
    (someone's program stopped) is broken."""

    def __init__(self, path, wait=10.0, stale=120.0):
        self.path, self.wait, self.stale = path, wait, stale

    def __enter__(self):
        end = time.time() + self.wait
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > self.stale:
                        os.remove(self.path)
                        continue
                except OSError:
                    pass
                if time.time() > end:
                    raise TimeoutError("the shared project is busy ({})".format(self.path))
                time.sleep(0.1)

    def __exit__(self, *exc):
        try:
            os.remove(self.path)
        except OSError:
            pass
        return False
