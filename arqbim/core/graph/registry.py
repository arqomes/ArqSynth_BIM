"""(0.538) The Visual Graph's node registry — each node type is described once (its inputs, outputs, measures with
their limits, a description and an example), and from that one description come the palette in the window, the
documentation and the AI's tools (MCP). The nodes' work is a plain function; nothing here knows about Qt."""

from dataclasses import dataclass, field

# Kinds of data a link carries. A link joins an output to an input of the same kind ("any" takes everything).
KINDS = ("number", "int", "bool", "text", "choice", "point", "image", "panel", "points", "field", "holes", "report",
         "file", "any")


@dataclass(frozen=True)
class Port:
    """An input, output or measure of a node. `default`, `min`, `max`, `step` and `unit` only for measures (the
    sliders); `choices` for a "choice"."""
    name: str
    kind: str
    label: str = ""
    default: object = None
    min: float = None
    max: float = None
    step: float = None
    unit: str = ""
    choices: tuple = ()
    optional: bool = False

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"tipo de ligação desconhecido: {self.kind}")

    def clamp(self, value):
        """The value kept inside this measure's limits (a slider can't go past its ends; the AI neither)."""
        if self.kind in ("number", "int"):
            value = float(value)
            if self.min is not None:
                value = max(self.min, value)
            if self.max is not None:
                value = min(self.max, value)
            return int(round(value)) if self.kind == "int" else value
        if self.kind == "bool":
            return bool(value)
        if self.kind == "choice":
            if value not in self.choices:
                raise ValueError(f"«{self.label or self.name}»: {value!r} não é uma das opções {self.choices}")
            return value
        if self.kind == "text":
            return str(value)
        return value

    def as_dict(self):
        d = {"name": self.name, "kind": self.kind, "label": self.label or self.name}
        for k in ("default", "min", "max", "step"):
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        if self.unit:
            d["unit"] = self.unit
        if self.choices:
            d["choices"] = list(self.choices)
        if self.optional:
            d["optional"] = True
        return d


@dataclass(frozen=True)
class NodeSpec:
    """A node type. `func(**inputs, **params)` returns a dict with one value per output."""
    key: str
    family: str
    label: str
    description: str
    func: object
    inputs: tuple = ()
    outputs: tuple = ()
    params: tuple = ()
    example: str = ""

    def port(self, group, name):
        for p in getattr(self, group):
            if p.name == name:
                return p
        raise KeyError(f"o nó «{self.label}» não tem «{name}» em {group}")

    def defaults(self):
        return {p.name: p.default for p in self.params}

    def as_dict(self):
        return {"key": self.key, "family": self.family, "label": self.label, "description": self.description,
                "inputs": [p.as_dict() for p in self.inputs], "outputs": [p.as_dict() for p in self.outputs],
                "params": [p.as_dict() for p in self.params], "example": self.example}


# Families in the order the palette shows them (decided with the owner, 2026-11-11).
FAMILIES = ("Base", "Padrões", "Moduladores", "Operações", "Orgânico", "Fabrico", "BIM")


class Registry:
    def __init__(self):
        self._specs = {}

    def add(self, spec):
        if spec.key in self._specs:
            raise ValueError(f"nó repetido: {spec.key}")
        if spec.family not in FAMILIES:
            raise ValueError(f"família desconhecida: {spec.family}")
        names = [p.name for p in spec.inputs + spec.params]
        if len(names) != len(set(names)):
            raise ValueError(f"«{spec.key}»: entradas e medidas com o mesmo nome")
        self._specs[spec.key] = spec
        return spec

    def node(self, key, family, label, description, inputs=(), outputs=(), params=(), example=""):
        """Decorator: the function under it is the node's work."""
        def wrap(func):
            self.add(NodeSpec(key, family, label, description, func, tuple(inputs), tuple(outputs), tuple(params),
                              example))
            return func
        return wrap

    def get(self, key):
        try:
            return self._specs[key]
        except KeyError:
            raise KeyError(f"não há nó «{key}»") from None

    def __contains__(self, key):
        return key in self._specs

    def keys(self):
        return list(self._specs)

    def catalog(self):
        """Every node, family by family — for the palette, the documentation and `list_nodes` of the MCP."""
        order = {f: i for i, f in enumerate(FAMILIES)}
        specs = sorted(self._specs.values(), key=lambda s: (order[s.family], s.label))
        return [s.as_dict() for s in specs]


# The program's own nodes register here (step 2 of the plan).
REGISTRY = Registry()
