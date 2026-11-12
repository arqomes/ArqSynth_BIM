"""(0.538) The Visual Graph — nodes that show results (PLANO.md, «Gráfico Visual», step 1: the core, no window)."""

from .graph import FORMAT, VERSION, Graph, GraphError
from .registry import FAMILIES, KINDS, REGISTRY, NodeSpec, Port, Registry
from . import nodes_panels  # noqa: E402,F401  (0.539) the first nodes register themselves
from . import nodes_3d  # noqa: E402,F401  (0.542) 3D and the model's walls
from . import nodes_logic  # noqa: E402,F401  (0.542) modulators from the surface, mixing, choosing, correcting
from . import nodes_organic  # noqa: E402,F401  (0.558) organic forms
from . import templates  # noqa: E402,F401  (0.541) ready graphs

__all__ = ["FORMAT", "VERSION", "Graph", "GraphError", "FAMILIES", "KINDS", "REGISTRY", "NodeSpec", "Port",
           "Registry"]
