"""(0.538) The Visual Graph itself: nodes with their measures, links from an output to an input, worked out in order
with a cache (a node is worked again only when its measures or something upstream changed), kept as JSON
(`arqsynth-grafo`, version 1) — the same text for the window, the files and the AI."""

import hashlib
import json

from .registry import REGISTRY

FORMAT = "arqsynth-grafo"
VERSION = 1


class GraphError(ValueError):
    pass


class Graph:
    def __init__(self, registry=None):
        self.registry = registry or REGISTRY
        self.nodes = {}       # id -> {"type", "params", "pos"}
        self.links = []       # (from_id, output, to_id, input)
        self._next = 1
        self._cache = {}      # id -> (key, outputs)
        self.errors = {}      # id -> message of the last evaluation

    # ---- building ----
    def add_node(self, type_, params=None, pos=(0.0, 0.0), node_id=None):
        spec = self.registry.get(type_)
        nid = node_id or f"n{self._next}"
        if nid in self.nodes:
            raise GraphError(f"já há um nó «{nid}»")
        self._next = max(self._next, _num(nid) + 1)
        self.nodes[nid] = {"type": type_, "params": spec.defaults(), "pos": [float(pos[0]), float(pos[1])]}
        for k, v in (params or {}).items():
            self.set_param(nid, k, v)
        return nid

    def remove_node(self, nid):
        self._node(nid)
        del self.nodes[nid]
        self.links = [l for l in self.links if l[0] != nid and l[2] != nid]
        self._cache.pop(nid, None)

    def set_param(self, nid, name, value):
        node = self._node(nid)
        port = self.registry.get(node["type"]).port("params", name)
        node["params"][name] = port.clamp(value)
        return node["params"][name]

    def connect(self, from_id, output, to_id, input_):
        src = self.registry.get(self._node(from_id)["type"]).port("outputs", output)
        dst = self.registry.get(self._node(to_id)["type"]).port("inputs", input_)
        if "any" not in (src.kind, dst.kind) and src.kind != dst.kind:
            raise GraphError(f"«{src.label or src.name}» ({src.kind}) não liga a «{dst.label or dst.name}» "
                             f"({dst.kind})")
        if from_id == to_id or from_id in self._downstream(to_id):
            raise GraphError("essa ligação fecharia um ciclo")
        # an input takes one link: a new one replaces the old
        self.links = [l for l in self.links if not (l[2] == to_id and l[3] == input_)]
        self.links.append((from_id, output, to_id, input_))

    def disconnect(self, to_id, input_):
        self.links = [l for l in self.links if not (l[2] == to_id and l[3] == input_)]

    # ---- working out ----
    def order(self):
        """Every node after the ones it takes from (Kahn's order; ids in a stable order where free)."""
        need = {n: set() for n in self.nodes}
        for f, _, t, _ in self.links:
            need[t].add(f)
        done, out = set(), []
        while len(out) < len(self.nodes):
            ready = sorted((n for n in self.nodes if n not in done and need[n] <= done), key=_num)
            if not ready:
                raise GraphError("o gráfico tem um ciclo")
            for n in ready:
                done.add(n)
                out.append(n)
        return out

    def evaluate(self, targets=None):
        """Each node's outputs, {id: {output: value}}. A node that fails keeps its message in `errors` and the
        nodes after it are left out (they say which one stopped them)."""
        self.errors = {}
        results, keys = {}, {}
        wanted = None if targets is None else self._upstream_all(targets)
        for nid in self.order():
            if wanted is not None and nid not in wanted:
                continue
            node = self.nodes[nid]
            spec = self.registry.get(node["type"])
            args, upkeys, blocked = dict(node["params"]), [], None
            for p in spec.inputs:
                link = next((l for l in self.links if l[2] == nid and l[3] == p.name), None)
                if link is None:
                    if not p.optional:
                        blocked = f"falta ligar «{p.label or p.name}»"
                        break
                    args[p.name] = p.default
                    continue
                if link[0] not in results:
                    blocked = f"parado por «{link[0]}»"
                    break
                args[p.name] = results[link[0]][link[1]]
                upkeys.append((p.name, keys[link[0]], link[1]))
            if blocked:
                self.errors[nid] = blocked
                continue
            key = _key(node["type"], node["params"], upkeys)
            cached = self._cache.get(nid)
            if cached and cached[0] == key:
                out = cached[1]
            else:
                try:
                    out = spec.func(**args) or {}
                except Exception as e:  # a node's failure is shown on its card, not a crash
                    self.errors[nid] = str(e) or type(e).__name__
                    self._cache.pop(nid, None)
                    continue
                missing = [p.name for p in spec.outputs if p.name not in out]
                if missing:
                    self.errors[nid] = f"o nó não devolveu {missing}"
                    continue
                self._cache[nid] = (key, out)
            results[nid], keys[nid] = out, key
        return results

    # ---- JSON ----
    def to_dict(self):
        return {"format": FORMAT, "version": VERSION,
                "nodes": [{"id": n, **{k: v for k, v in d.items()}} for n, d in self.nodes.items()],
                "links": [{"from": f, "output": o, "to": t, "input": i} for f, o, t, i in self.links]}

    def to_json(self):
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=1)

    @classmethod
    def from_dict(cls, data, registry=None):
        if data.get("format") != FORMAT:
            raise GraphError("não é um gráfico do ArqSynth")
        if data.get("version", 0) > VERSION:
            raise GraphError("gráfico feito por uma versão mais nova do ArqSynth")
        g = cls(registry)
        for n in data.get("nodes", []):
            g.add_node(n["type"], n.get("params"), n.get("pos", (0, 0)), node_id=n["id"])
        for l in data.get("links", []):
            g.connect(l["from"], l["output"], l["to"], l["input"])
        return g

    @classmethod
    def from_json(cls, text, registry=None):
        return cls.from_dict(json.loads(text), registry)

    # ---- helpers ----
    def _node(self, nid):
        try:
            return self.nodes[nid]
        except KeyError:
            raise GraphError(f"não há nó «{nid}»") from None

    def _downstream(self, nid):
        seen, stack = set(), [nid]
        while stack:
            for f, _, t, _ in self.links:
                if f == stack[-1] and t not in seen:
                    seen.add(t)
                    stack.append(t)
                    break
            else:
                stack.pop()
        return seen

    def _upstream_all(self, targets):
        seen, stack = set(targets), list(targets)
        while stack:
            n = stack.pop()
            for f, _, t, _ in self.links:
                if t == n and f not in seen:
                    seen.add(f)
                    stack.append(f)
        return seen


def _num(nid):
    digits = "".join(c for c in str(nid) if c.isdigit())
    return int(digits) if digits else 0


def _key(type_, params, upkeys):
    text = json.dumps([type_, params, upkeys], sort_keys=True, default=repr)
    return hashlib.sha1(text.encode()).hexdigest()
