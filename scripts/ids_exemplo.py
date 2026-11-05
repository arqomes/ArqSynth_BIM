"""Writes exemplos/requisitos_exemplo.ids: a small IDS (buildingSMART Information Delivery
Specification) to try BIM ▸ Check with IDS on the example house — some requirements the
house meets, one it does not (doors without a fire rating).

    .venv\\Scripts\\python scripts\\ids_exemplo.py [out.ids]
"""

import os
import sys

from ifctester import ids

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "exemplos", "requisitos_exemplo.ids")
    spec = ids.Ids(title="Requisitos de exemplo (ArqBIM)", author="arqbim@example.com", version="1",
                   description="Para experimentar BIM ▸ Verificar com IDS na casa de exemplo.")
    rules = (
        ("Paredes: exterior ou interior", "Cada parede diz se é exterior (Pset_WallCommon.IsExternal).",
         ids.Entity(name="IFCWALL"),
         ids.Property(propertySet="Pset_WallCommon", baseName="IsExternal", dataType="IFCBOOLEAN")),
        ("Paredes com nome", "Cada parede tem nome.", ids.Entity(name="IFCWALL"), ids.Attribute(name="Name")),
        ("Portas: resistência ao fogo", "Cada porta tem a resistência ao fogo (Pset_DoorCommon.FireRating).",
         ids.Entity(name="IFCDOOR"),
         ids.Property(propertySet="Pset_DoorCommon", baseName="FireRating", dataType="IFCLABEL")),
        ("Lajes com material", "Cada laje tem material.", ids.Entity(name="IFCSLAB"), ids.Material()),
    )
    for name, description, applies, requires in rules:
        s = ids.Specification(name=name, description=description, ifcVersion=["IFC4"])
        s.applicability.append(applies)
        s.requirements.append(requires)
        spec.specifications.append(s)
    valid = spec.to_xml(out)
    print(out, "especificações:", len(rules), "válido:", valid)
