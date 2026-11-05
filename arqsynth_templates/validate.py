"""A template checked against its JSON Schema (schema.json) — the part of JSON Schema it uses ($ref to its $defs, type,
required, properties, additionalProperties, items, enum, const, minimum, maximum, exclusiveMinimum, minLength,
pattern), in plain Python: no library to install, the same in every program of the suite. Problems come back as
Problem(path, code, detail) — never as an exception —, said in Portuguese or English by text()."""

import json
import os
import re
from dataclasses import dataclass

_SCHEMA = []


def schema():
    """The template's JSON Schema (schema.json beside this file)."""
    if not _SCHEMA:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.json"), encoding="utf-8") as f:
            _SCHEMA.append(json.load(f))
    return _SCHEMA[0]


@dataclass(frozen=True)
class Problem:
    path: str          # where: "units.decimals", "types.wall[2].layers[0].thickness"
    code: str          # what: type, const, enum, minimum, maximum, exclusive_minimum, empty, pattern, required, unknown
    detail: str = ""   # with what: the types / values wanted, the bound, the key missing

    def text(self, lang="pt"):
        return text(self, lang)


_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}
_WORDS = {"pt": {"object": "um grupo de campos", "array": "uma lista", "string": "um texto", "integer": "um inteiro",
                 "number": "um número", "boolean": "true ou false", "null": "null"},
          "en": {"object": "an object", "array": "a list", "string": "a text", "integer": "an integer",
                 "number": "a number", "boolean": "true or false", "null": "null"}}
_SAY = {
    "pt": {"type": "tem de ser {}", "const": "tem de ser {}", "enum": "tem de ser um de: {}", "minimum": "no mínimo {}",
           "maximum": "no máximo {}", "exclusive_minimum": "tem de ser maior do que {}", "empty": "não pode estar vazio",
           "pattern": "não está escrito como deve ({})", "required": "falta «{}»", "unknown": "não é conhecido",
           "json": "não é JSON válido: {}", "format": "não é um modelo ArqSynth"},
    "en": {"type": "must be {}", "const": "must be {}", "enum": "must be one of: {}", "minimum": "at least {}",
           "maximum": "at most {}", "exclusive_minimum": "must be more than {}", "empty": "must not be empty",
           "pattern": "is not written as it should ({})", "required": "lacks “{}”", "unknown": "is not known",
           "json": "is not valid JSON: {}", "format": "is not an ArqSynth template"},
}


def text(problem, lang="pt"):
    """«units.decimals: tem de ser um inteiro»."""
    lang = lang if lang in _SAY else "en"
    detail = problem.detail
    if problem.code == "type":
        detail = (" ou " if lang == "pt" else " or ").join(_WORDS[lang].get(k, k) for k in detail.split("|"))
    where = problem.path or ("o modelo" if lang == "pt" else "the template")
    return "{}: {}".format(where, _SAY[lang].get(problem.code, problem.code + " {}").format(detail))


def problems(data, root=None):
    """[Problem] of `data` against the template's schema (or `root`)."""
    root = root or schema()
    out = []
    _check(data, root, root, "", out)
    return out


def _resolve(node, root):
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if not ref.startswith("#/"):
            return {}
        target = root
        for part in ref[2:].split("/"):
            target = target.get(part, {}) if isinstance(target, dict) else {}
        node = target
    return node


def _check(value, node, root, path, out):
    node = _resolve(node, root)
    if not isinstance(node, dict):
        return
    kinds = node.get("type")
    if kinds is not None:
        kinds = [kinds] if isinstance(kinds, str) else list(kinds)
        if not any(_TYPES.get(k, lambda v: True)(value) for k in kinds):
            out.append(Problem(path, "type", "|".join(kinds)))
            return
    if "const" in node and value != node["const"]:
        out.append(Problem(path, "const", json.dumps(node["const"], ensure_ascii=False)))
    if "enum" in node and value not in node["enum"]:
        out.append(Problem(path, "enum", ", ".join(json.dumps(v, ensure_ascii=False) for v in node["enum"])))
    if _TYPES["number"](value):
        for word, test in (("minimum", lambda b: value < b), ("maximum", lambda b: value > b),
                           ("exclusiveMinimum", lambda b: value <= b)):
            if word in node and test(node[word]):
                out.append(Problem(path, "exclusive_minimum" if word == "exclusiveMinimum" else word, str(node[word])))
    if isinstance(value, str):
        if node.get("minLength", 0) >= 1 and not value:
            out.append(Problem(path, "empty"))
        if "pattern" in node and not re.search(node["pattern"], value):
            out.append(Problem(path, "pattern", node["pattern"]))
    if isinstance(value, dict):
        for key in node.get("required", ()):
            if key not in value:
                out.append(Problem(path, "required", key))
        props = node.get("properties", {})
        extra = node.get("additionalProperties", True)
        for key, item in value.items():
            sub = "{}.{}".format(path, key) if path else key
            if key in props:
                _check(item, props[key], root, sub, out)
            elif extra is False:
                out.append(Problem(sub, "unknown"))
            elif isinstance(extra, dict):
                _check(item, extra, root, sub, out)
    if isinstance(value, list) and "items" in node:
        for k, item in enumerate(value):
            _check(item, node["items"], root, "{}[{}]".format(path, k), out)
