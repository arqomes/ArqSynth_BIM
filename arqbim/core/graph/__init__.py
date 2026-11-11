"""(0.538) The Visual Graph — nodes that show results (PLANO.md, «Gráfico Visual», step 1: the core, no window)."""

from .graph import FORMAT, VERSION, Graph, GraphError
from .registry import FAMILIES, KINDS, REGISTRY, NodeSpec, Port, Registry
from . import nodes_panels  # noqa: E402,F401  (0.539) the first nodes register themselves

__all__ = ["FORMAT", "VERSION", "Graph", "GraphError", "FAMILIES", "KINDS", "REGISTRY", "NodeSpec", "Port",
           "Registry"]
