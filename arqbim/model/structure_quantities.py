"""The structure's quantities (0.167, Phase 9, step 5): for each concrete member (column, beam, footing, structural
slab) its concrete (m³, of its shape), its formwork (m²: a beam's sides and soffit, a column's faces, a footing's
sides, a slab's soffit and edges) and its steel (kg, of the bars in the model — none told when it has none), the
steel's rate (kg/m³) checked against plausible ranges (taken over from the ArqSynth Modeler's calc_quantities); the
totals by kind and of all. What the quantities window lists, the calculation report sums up, and goes to CSV."""

from dataclasses import dataclass

KINDS = ("column", "beam", "slab", "footing", "wall")          # (0.342: load-bearing concrete walls)
STEEL_RATE_RANGE = {"beam": (40.0, 220.0), "column": (60.0, 300.0), "footing": (15.0, 120.0),   # kg/m³ (the addon's)
                    "wall": (20.0, 150.0)}                                          # (0.342: the usual for walls)


@dataclass
class QuantityRow:
    guid: str
    kind: str
    storey: str = ""
    concrete: float = 0.0       # m³
    formwork: float = 0.0       # m²
    steel: float = 0.0          # kg (of the bars in the model)
    has_bars: bool = False

    @property
    def rate(self):
        return self.steel / self.concrete if self.concrete > 1e-9 else 0.0

    @property
    def implausible(self):
        """The steel's rate out of the plausible range of its kind (only when it has bars)."""
        low, high = STEEL_RATE_RANGE.get(self.kind, (0.0, float("inf")))
        return self.has_bars and not low <= self.rate <= high


def formwork(kind, size=None, length=0.0, area=0.0, perimeter=0.0, thickness=0.0):
    """m² of formwork: a beam (size b × h, length) its two sides and soffit; a column (size, height = length) its
    faces; a footing (perimeter, depth = thickness) its sides; a slab (area, perimeter, thickness) its soffit and
    edges."""
    if kind == "beam":
        b, h = size
        return (2.0 * h + b) * length
    if kind == "column":
        b, h = size
        return 2.0 * (b + h) * length
    if kind == "footing":
        return perimeter * thickness
    if kind == "slab":
        return area + perimeter * thickness
    if kind == "wall":                                  # (0.342) its two faces (area: one, its openings left out), ends
        return 2.0 * area + perimeter * thickness
    return 0.0


def totals(rows):
    """{kind: (m³, m², kg)} and the whole (m³, m², kg)."""
    by_kind = {}
    whole = [0.0, 0.0, 0.0]
    for r in rows:
        entry = by_kind.setdefault(r.kind, [0.0, 0.0, 0.0])
        for k, v in enumerate((r.concrete, r.formwork, r.steel)):
            entry[k] += v
            whole[k] += v
    return {k: tuple(v) for k, v in by_kind.items()}, tuple(whole)
