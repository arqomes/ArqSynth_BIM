"""(0.416) The Verifier («o Verificador»): the project checked against the law of the place it is built in and against
good practice, while it is drawn.

- uses.py: what each room is for (its use), from its name and what is inside it — or chosen;
- dwellings.py: the dwellings (fogos) the rooms make, found through their doors, and their type (T0, T1, T2…);
- measures.py: what is measured in the model (areas, heights, widths…), each with the name the rules use;
- rules.py: the rules — data, not code: one pack per country and law (regulamentos/), read and evaluated;
- watch.py: the watcher — after each change, the rules of what changed evaluated again, in the background.

Pure Python (no Qt): the IFC side is ifc/dwellings.py, the window's ui/verify_*.py."""
