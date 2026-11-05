"""Writes exemplos/biblioteca_mobiliario.ifc: a few components (simple blocks of the right size)
to try BIM ▸ Bring components from another project.

    .venv\\Scripts\\python scripts\\biblioteca_exemplo.py [out.ifc]
"""

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from arqbim.core.sketch_geometry import push_pull, rectangle_matrix, rectangle_mesh  # noqa: E402
from arqbim.model import bim  # noqa: E402
from arqbim.model.document import AddObject, Document, SketchObject  # noqa: E402

PIECES = (                      # name, category, width, depth, height (m)
    ("Mesa 120×80", "furniture", 1.20, 0.80, 0.75),
    ("Cadeira 45×45", "furniture", 0.45, 0.45, 0.90),
    ("Cama 160×200", "furniture", 1.60, 2.00, 0.50),
    ("Lavatório 60×45", "sanitary", 0.60, 0.45, 0.85),
)

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "exemplos", "biblioteca_mobiliario.ifc")
    doc = Document()
    x = 0.0
    for name, category, w, d, h in PIECES:
        m = rectangle_matrix(np.array((x, 0.0, 0.0)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)))
        mesh = rectangle_mesh(w, d)
        push_pull(mesh, 0, m, h)
        sketch = SketchObject(name, m, mesh)
        doc.execute(AddObject(sketch))
        bim.make_component(doc, [sketch.id], name, category)
        x += w + 0.5
    doc.save(out)
    print(out, "componentes:", len(PIECES), "erros de validação:", len(doc.ifc.validate(express_rules=True)))
