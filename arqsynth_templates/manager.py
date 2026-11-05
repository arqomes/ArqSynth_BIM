"""TemplateManager: the ArqSynth suite's templates (.astpl) in its shared folder (paths.py) — list, load, save,
update, delete, duplicate, rename, the default of each program (settings.json), validate. Plain Python, no program
of the suite in it: each program gives its own factory template («ArqSynth Padrão», built into it — never deleted,
used when the folder is empty, a file is broken or the default is gone).

Safe for several programs at once: a file is written to a temporary one beside it and put in place in one step
(os.replace) — one reading it sees the old one whole or the new one whole, and a program closed half-way leaves the
old one as it was; settings.json and the folder are changed under a lock file (another program waits, a lock left
by a program that stopped is taken over after LOCK_STALE s). What one program does not know in a template (another
program's «extensions», a newer field) is kept when it saves it."""

import copy
import datetime
import io
import json
import os
import re
import tempfile
import time
import uuid
import zipfile
from dataclasses import dataclass, field

from . import paths
from .migrate import SCHEMA_VERSION, Notice, upgrade
from .validate import problems as schema_problems

EXTENSION = ".astpl"
FORMAT = "arqsynth-template"
FACTORY_NAME = "ArqSynth Padrão"
FACTORY_ID = "a5a9b1f0-0000-4000-8000-000000000001"
TOP = ("format", "schema_version", "name", "version", "id")     # (a problem there: the template is not read)
LOCK_WAIT, LOCK_STALE = 4.0, 15.0                                  # s
_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {"COM%d" % k for k in range(1, 10)} | {"LPT%d" % k for k in range(1, 10)}

_ERRORS = {
    "pt": {"not_found": "O modelo «{}» não existe na pasta dos modelos.",
           "corrupted": "O ficheiro do modelo «{}» está estragado e não se lê: {}",
           "invalid": "O modelo «{}» não está certo: {}",
           "exists": "Já há um modelo chamado «{}».",
           "factory": "O modelo de fábrica «{}» não se apaga, não se muda de nome nem se regrava (grave uma cópia).",
           "newer": "O modelo «{}» foi feito por uma versão mais nova: grave-o com outro nome.",
           "name": "«{}» não serve de nome de modelo.",
           "busy": "Outro programa está a gravar na pasta dos modelos; tente outra vez."},
    "en": {"not_found": "There is no template “{}” in the templates folder.",
           "corrupted": "The file of the template “{}” is damaged and cannot be read: {}",
           "invalid": "The template “{}” is not right: {}",
           "exists": "There is a template called “{}” already.",
           "factory": "The factory template “{}” cannot be deleted, renamed or saved over (save a copy).",
           "newer": "The template “{}” was made by a newer version: save it under another name.",
           "name": "“{}” cannot be a template's name.",
           "busy": "Another program is saving in the templates folder; try again."},
}


class TemplateError(Exception):
    """code: not_found, corrupted, invalid, exists, factory, newer, name, busy."""

    def __init__(self, code, name="", detail="", problems=()):
        super().__init__(code, name, detail)
        self.code, self.name, self.detail, self.problems = code, name, detail, list(problems)

    def text(self, lang="pt"):
        said = _ERRORS.get(lang, _ERRORS["en"])[self.code]
        detail = self.detail or "; ".join(p.text(lang) for p in self.problems[:3])
        return said.format(self.name, detail) if said.count("{}") == 2 else said.format(self.name)

    def __str__(self):
        return self.text("en")


@dataclass(frozen=True)
class Filled:
    """A field that was missing or wrong, given the factory's value (or a list's item left out: removed)."""
    path: str
    removed: bool = False

    def text(self, lang="pt"):
        if lang == "pt":
            return ("«{}» estava errado: ficou de fora." if self.removed else
                    "«{}» faltava ou estava errado: usado o valor de fábrica.").format(self.path)
        return ("“{}” was wrong: left out." if self.removed else
                "“{}” was missing or wrong: the factory's value used.").format(self.path)


@dataclass(frozen=True)
class DefaultLost:
    """The default template could not be used (gone, broken): the factory's instead."""
    name: str
    why: str

    def text(self, lang="pt"):
        if lang == "pt":
            what = {"not_found": "já não está na pasta", "corrupted": "está estragado"}.get(self.why, "não se lê")
            return "O modelo padrão «{}» {}: usado o modelo de fábrica.".format(self.name, what)
        what = {"not_found": "is no longer in the folder", "corrupted": "is damaged"}.get(self.why, "cannot be read")
        return "The default template “{}” {}: the factory template used.".format(self.name, what)


@dataclass
class Template:
    data: dict
    path: str = None                  # its file; None: the factory's, built into the program
    notices: list = field(default_factory=list)   # what was said reading it: Notice, Filled, DefaultLost
    assets: dict = field(default_factory=dict)    # a ZIP .astpl's files: {name under assets/: bytes}

    @property
    def name(self):
        return self.data.get("name", "")

    @property
    def id(self):
        return self.data.get("id", "")

    @property
    def version(self):
        return int(self.data.get("version") or 1)

    @property
    def is_factory(self):
        return self.path is None

    def messages(self, lang="pt"):
        return [n.text(lang) for n in self.notices]


@dataclass
class Entry:
    """A template as listed (read whole: they are small)."""
    name: str
    path: str = None
    id: str = ""
    version: int = 1
    modified: str = ""
    programs: tuple = ()
    description: str = ""
    is_factory: bool = False
    is_default: bool = False
    ok: bool = True
    problem: str = ""                 # why it is not ok (a broken file)


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def file_name(name):
    """A template's file name from its name: what Windows refuses replaced, «.astpl»."""
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip().strip(".")[:80].strip() or "modelo"
    if s.split(".")[0].upper() in _RESERVED:
        s = "_" + s
    return s + EXTENSION


def _get(data, path):
    """The value at a dotted path of plain keys (no list index), or KeyError."""
    node = data
    for part in path.split(".") if path else ():
        if not isinstance(node, dict) or part not in node:
            raise KeyError(path)
        node = node[part]
    return node


def _set(data, path, value):
    node = data
    parts = path.split(".")
    for part in parts[:-1]:
        if not isinstance(node.get(part), dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value


class _Lock:
    """A lock file (another program of the suite waits for it; one left by a program that stopped is taken over)."""

    def __init__(self, path):
        self.path = path

    def __enter__(self):
        end = time.monotonic() + LOCK_WAIT
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        while True:
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > LOCK_STALE:
                        os.remove(self.path)
                        continue
                except OSError:
                    pass
                if time.monotonic() > end:
                    raise TemplateError("busy") from None
                time.sleep(0.05)

    def __exit__(self, *_exc):
        try:
            os.remove(self.path)
        except OSError:
            pass


def write_atomic(path, payload):
    """`payload` (bytes) written to `path` safely: to a temporary file beside it, flushed to the disk, then put in its
    place in one step — never a half-written file (Windows: retried while another program holds it open)."""
    folder = os.path.dirname(os.path.abspath(path))
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        for attempt in range(20):
            try:
                os.replace(tmp, path)
                break
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.05)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def read_file(path):
    """(data, assets) of a .astpl — JSON, or a ZIP with template.json and assets/… —; TemplateError «corrupted»."""
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError as exc:
        raise TemplateError("corrupted", name, str(exc)) from None
    assets = {}
    try:
        if raw[:2] == b"PK":
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                text = z.read("template.json").decode("utf-8-sig")
                assets = {n[len("assets/"):]: z.read(n) for n in z.namelist()
                          if n.startswith("assets/") and not n.endswith("/")}
        else:
            text = raw.decode("utf-8-sig")
        data = json.loads(text)
    except (ValueError, KeyError, zipfile.BadZipFile, UnicodeDecodeError) as exc:
        raise TemplateError("corrupted", name, str(exc)[:160]) from None
    if not isinstance(data, dict) or data.get("format", FORMAT) != FORMAT:
        raise TemplateError("corrupted", name, "not an ArqSynth template")
    return data, assets


def payload(data, assets=None):
    """The bytes of a .astpl: the JSON (indented, UTF-8) — or, with files, a ZIP of template.json and assets/…"""
    text = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    if not assets:
        return text
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("template.json", text)
        for name, blob in sorted(assets.items()):
            z.writestr("assets/" + name, blob)
    return out.getvalue()


class TemplateManager:
    def __init__(self, program, factory, root=None, lang="pt", program_version=""):
        """program: who uses it ("arqsynth-bim"…: its default in settings.json, its «extensions»); factory: its
        factory template (a dict in this layout); root: the suite's folder (else paths.suite_dir())."""
        self.program, self.root, self.lang, self.program_version = program, root, lang, program_version
        made = copy.deepcopy(factory)
        made.update(format=FORMAT, schema_version=SCHEMA_VERSION)
        made.setdefault("name", FACTORY_NAME)
        made.setdefault("id", FACTORY_ID)
        made.setdefault("version", 1)
        made.setdefault("programs", [program])
        self._factory = made
        self.factory_name = made["name"]

    # ------------------------------------------------------------ where

    @property
    def folder(self):
        return paths.templates_dir(self.root)

    @property
    def settings_path(self):
        return paths.settings_file(self.root)

    def ensure(self):
        """The templates' folder made if it is not there (the first start); temporary files a program left when
        it stopped half-way, older than a day, cleared. Returns the folder."""
        os.makedirs(self.folder, exist_ok=True)
        for name in os.listdir(self.folder):
            if name.endswith(".tmp"):
                path = os.path.join(self.folder, name)
                try:
                    if time.time() - os.path.getmtime(path) > 86400:
                        os.remove(path)
                except OSError:
                    pass
        return self.folder

    def _files(self):
        if not os.path.isdir(self.folder):
            return []
        return [os.path.join(self.folder, n) for n in sorted(os.listdir(self.folder))
                if n.lower().endswith(EXTENSION) and not n.startswith(".")]

    def _is_factory(self, name):
        return isinstance(name, str) and name.strip().casefold() == self.factory_name.casefold()

    def _find(self, name=None, tid=None):
        """The file of the template of that name (or id), or None — a broken file found by its file name."""
        wanted = (name or "").strip().casefold()
        for path in self._files():
            try:
                data, _assets = read_file(path)
            except TemplateError:
                if wanted and os.path.basename(path).casefold() == file_name(name).casefold():
                    return path
                continue
            if tid and data.get("id") == tid:
                return path
            if wanted and str(data.get("name", "")).strip().casefold() == wanted:
                return path
        return None

    # ------------------------------------------------------------ reading

    def factory(self):
        return Template(copy.deepcopy(self._factory))

    def load(self, name):
        """The template of that name (or a .astpl's path): upgraded to this layout, checked, what is missing or wrong
        given the factory's value — each said in its notices. TemplateError: not there, or not readable at all."""
        if not name or self._is_factory(name):
            return self.factory()
        path = name if os.path.isfile(name) else self._find(name)
        if path is None:
            raise TemplateError("not_found", name)
        data, assets = read_file(path)
        return self.prepare(data, path, assets)

    def prepare(self, data, path=None, assets=None):
        """A template read: upgraded, mended from the factory, completed (see load)."""
        data, notices = upgrade(copy.deepcopy(data))
        newer = any(isinstance(n, Notice) and n.code == "newer" for n in notices)
        if not str(data.get("name", "")).strip():
            data["name"] = os.path.splitext(os.path.basename(path))[0] if path else "Modelo"
            notices.append(Filled("name"))
        notices += self._mend(data, keep_unknown=newer)
        notices += self._complete(data)
        return Template(data, path, notices, dict(assets or {}))

    def _mend(self, data, keep_unknown=False):
        """The fields the schema refuses: given the factory's value, or — inside a list — that item left out."""
        notices = []
        for _round in range(6):
            found = [p for p in schema_problems(data) if not (keep_unknown and p.code == "unknown")]
            if not found:
                break
            for p in found:
                path = p.path + "." + p.detail if p.code == "required" and p.path else \
                    (p.detail if p.code == "required" else p.path)
                if "[" in path:                           # (inside a list: the item left out)
                    head = path[:path.index("]") + 1]
                    if self._drop(data, head):
                        notices.append(Filled(head, removed=True))
                    continue
                try:
                    _set(data, path, copy.deepcopy(_get(self._factory, path)))
                    notices.append(Filled(path))
                except KeyError:
                    parent, _dot, key = path.rpartition(".")
                    try:
                        node = _get(data, parent) if parent else data
                        node.pop(key, None)
                        notices.append(Filled(path, removed=True))
                    except KeyError:
                        pass
        return notices

    @staticmethod
    def _drop(data, head):
        """Takes out the list item at `head` ("types.wall[2]"); True if it did."""
        m = re.match(r"^(.*)\[(\d+)\]$", head)
        if not m:
            return False
        try:
            items = _get(data, m.group(1))
        except KeyError:
            return False
        k = int(m.group(2))
        if isinstance(items, list) and k < len(items):
            items[k] = None
            items[:] = [i for i in items if i is not None]
            return True
        return False

    def _complete(self, data):
        """The sections (and their own fields) the template has not: the factory's — each said."""
        notices = []
        for key, value in self._factory.items():
            if key in ("id", "name", "version", "created", "modified", "description", "author", "generator",
                       "programs", "extensions"):
                continue
            if key not in data:
                data[key] = copy.deepcopy(value)
                notices.append(Filled(key))
            elif isinstance(value, dict) and isinstance(data[key], dict) and key not in ("types", "ifc_classes"):
                for sub, default in value.items():
                    if sub not in data[key]:
                        data[key][sub] = copy.deepcopy(default)
                        notices.append(Filled("{}.{}".format(key, sub)))
        return notices

    def validate(self, data):
        """[Problem] of a template (as it would be read: upgraded first)."""
        upgraded, _notices = upgrade(copy.deepcopy(data))
        return schema_problems(upgraded)

    def list(self):
        """[Entry]: the factory's first, then the folder's by name — the broken ones too (ok False, why)."""
        default = self.default_ref()
        out = [Entry(self.factory_name, None, self._factory["id"], int(self._factory.get("version", 1)),
                     self._factory.get("modified", ""), tuple(self._factory.get("programs", ())),
                     self._factory.get("description", ""), is_factory=True)]
        effective = None
        for path in self._files():
            try:
                data, _assets = read_file(path)
            except TemplateError as exc:
                out.append(Entry(os.path.splitext(os.path.basename(path))[0], path, ok=False, problem=exc.text(self.lang)))
                continue
            entry = Entry(str(data.get("name") or os.path.splitext(os.path.basename(path))[0]), path,
                          str(data.get("id", "")), int(data.get("version") or 1), str(data.get("modified", "")),
                          tuple(data.get("programs") or ()), str(data.get("description", "")))
            out.append(entry)
            if default and (default.get("id") and entry.id == default.get("id") or
                            entry.name.casefold() == str(default.get("name", "")).casefold()):
                effective = entry if effective is None else effective
        (effective or out[0]).is_default = True
        out[1:] = sorted(out[1:], key=lambda e: e.name.casefold())
        return out

    # ------------------------------------------------------------ the default (settings.json)

    def read_settings(self):
        """settings.json as a dict ({} when it is not there or broken — the factory then)."""
        try:
            with open(self.settings_path, encoding="utf-8-sig") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _change_settings(self, change):
        with _Lock(self.settings_path + ".lock"):
            data = self.read_settings()
            data.setdefault("schema_version", 1)
            change(data)
            write_atomic(self.settings_path, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def default_ref(self):
        """{name, id} of this program's default template in settings.json, or None (the factory's)."""
        ref = self.read_settings().get("defaults", {}).get(self.program)
        if isinstance(ref, str):
            ref = {"name": ref}
        return ref if isinstance(ref, dict) and ref.get("name") else None

    def default_name(self):
        ref = self.default_ref()
        return ref["name"] if ref else self.factory_name

    def get_default(self):
        """The template a new project starts with: this program's default — or, when there is none, it is gone or it
        is broken, the factory's (said in its notices)."""
        ref = self.default_ref()
        if ref is None or self._is_factory(ref.get("name")):
            return self.factory()
        path = self._find(tid=ref.get("id")) if ref.get("id") else None
        try:
            return self.load(path or ref["name"])
        except TemplateError as exc:
            made = self.factory()
            made.notices.insert(0, DefaultLost(ref["name"], exc.code))
            return made

    def set_default(self, name):
        """That template this program's default (it must read); the factory's: none kept."""
        if self._is_factory(name):
            self.reset_factory()
            return self.factory()
        made = self.load(name)
        self._change_settings(lambda s: s.setdefault("defaults", {}).update(
            {self.program: {"name": made.name, "id": made.id}}))
        return made

    def reset_factory(self):
        """The factory template this program's default again."""
        self._change_settings(lambda s: s.setdefault("defaults", {}).pop(self.program, None))

    # ------------------------------------------------------------ writing

    def _check_name(self, name):
        name = (name or "").strip()
        if not name or len(name) > 120 or re.search(r"[\x00-\x1f]", name):
            raise TemplateError("name", name)
        if self._is_factory(name):
            raise TemplateError("factory", self.factory_name)
        return name

    def save(self, data, name=None, replace=False, assets=None):
        """`data` saved as the template `name` (or its own name): a new one (TemplateError «exists» when there is one,
        unless `replace`), or over it — its id kept, its version one more, what this program does not know in it
        (another program's extensions) kept. Checked against the schema first (TemplateError «invalid»)."""
        name = self._check_name(name or data.get("name"))
        data = copy.deepcopy(data)
        with _Lock(os.path.join(self.folder, ".lock")):
            existing = self._find(name)
            if existing is not None and not replace:
                raise TemplateError("exists", name)
            old = {}
            if existing is not None:
                try:
                    old, _old_assets = read_file(existing)
                except TemplateError:
                    old = {}                      # (broken: written anew over it)
                if int(old.get("schema_version", 0) or 0) > SCHEMA_VERSION:
                    raise TemplateError("newer", name)
            stamp = now_iso()
            for key, value in old.items():        # (what this program does not know: kept)
                if key not in data and key not in ("generator",):
                    data[key] = copy.deepcopy(value)
            mine = data.setdefault("extensions", {})
            for program, value in (old.get("extensions") or {}).items():
                if program != self.program and program not in mine:
                    mine[program] = copy.deepcopy(value)
            data.update(format=FORMAT, schema_version=SCHEMA_VERSION, name=name, modified=stamp,
                        generator={"program": self.program, "version": str(self.program_version)})
            if old:
                data["id"] = old.get("id") or str(uuid.uuid4())
                data["version"] = int(old.get("version") or 0) + 1
                data["created"] = old.get("created") or stamp
            else:
                if not data.get("id") or data.get("id") == FACTORY_ID or self._find(tid=data.get("id")):
                    data["id"] = str(uuid.uuid4())
                data["version"] = 1
                data["created"] = stamp
            programs = list(data.get("programs") or [])
            if self.program not in programs:
                programs.append(self.program)
            data["programs"] = programs
            found = schema_problems(data)
            if found:
                raise TemplateError("invalid", name, problems=found)
            path = existing or self._free_path(name)
            write_atomic(path, payload(data, assets))
        return Template(data, path, [], dict(assets or {}))

    def _free_path(self, name):
        path = os.path.join(self.ensure(), file_name(name))
        base, ext = os.path.splitext(path)
        k = 2
        while os.path.exists(path):                       # (another template's file of the same file name)
            path = "{} ({}){}".format(base, k, ext)
            k += 1
        return path

    def update(self, name, data, assets=None):
        """The template `name` saved over with `data` (TemplateError «factory», «not_found», «newer»)."""
        if self._is_factory(name):
            raise TemplateError("factory", self.factory_name)
        if self._find(name) is None:
            raise TemplateError("not_found", name)
        return self.save(data, name, replace=True, assets=assets)

    def delete(self, name):
        """The template's file deleted (not the factory's); a program whose default it was: the factory's again."""
        if self._is_factory(name):
            raise TemplateError("factory", self.factory_name)
        with _Lock(os.path.join(self.folder, ".lock")):
            path = self._find(name)
            if path is None:
                raise TemplateError("not_found", name)
            try:
                tid = read_file(path)[0].get("id")
            except TemplateError:
                tid = None
            os.remove(path)
        self._change_settings(lambda s: self._forget(s, name, tid))

    @staticmethod
    def _forget(settings, name, tid, new_name=None):
        for program, ref in list((settings.get("defaults") or {}).items()):
            ref = {"name": ref} if isinstance(ref, str) else ref
            if isinstance(ref, dict) and (tid and ref.get("id") == tid or
                                          str(ref.get("name", "")).casefold() == name.casefold()):
                if new_name is None:
                    settings["defaults"].pop(program)
                else:
                    settings["defaults"][program] = dict(ref, name=new_name)

    def duplicate(self, name, new_name):
        """A copy of a template (the factory's too) under another name: a new template (its own id, version 1)."""
        made = self.load(name)
        data = copy.deepcopy(made.data)
        data.pop("id", None)
        return self.save(data, new_name, assets=made.assets)

    def rename(self, name, new_name):
        """A template's name changed (its file too; its id and version kept); the programs whose default it was
        follow it."""
        if self._is_factory(name):
            raise TemplateError("factory", self.factory_name)
        new_name = self._check_name(new_name)
        with _Lock(os.path.join(self.folder, ".lock")):
            path = self._find(name)
            if path is None:
                raise TemplateError("not_found", name)
            other = self._find(new_name)
            if other is not None and other != path:
                raise TemplateError("exists", new_name)
            data, assets = read_file(path)
            data["name"] = new_name
            data["modified"] = now_iso()
            target = path if file_name(new_name).casefold() == os.path.basename(path).casefold() else \
                self._free_path(new_name)
            write_atomic(target, payload(data, assets))
            if target != path:
                os.remove(path)
        self._change_settings(lambda s: self._forget(s, name, data.get("id"), new_name))
        return Template(data, target, [], assets)
