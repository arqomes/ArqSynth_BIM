"""The circuits' conduits (0.146, Phase 6, step 4: «canalizações e ligação ao quadro»): each circuit wired from its
board to its points, one after the other — from each to the nearest not yet reached — by conduits (IfcCableCarrierSegment
CONDUITSEGMENT): up the wall from where it is to the conduits' height (over the ceiling), across, and down to the
next point; the pieces joined by bends, connected to the points' cable ports, and put in the circuit (its group)."""

import numpy as np

from .circuits import LOADS

CONDUIT_Z = 2.75            # m over the storey: where the conduits run (over a 2,60 m ceiling)
MIN_RUN = 0.05              # m: a piece shorter than this is left out (the conduit goes straight on)


class ConduitMixin:
    def _wire_point(self, guid):
        """(the cable port of a point or None, where the conduit reaches it (3,))."""
        e = self.by_guid(guid)
        ports = [p for p in self.ports(guid) if (p.PredefinedType or "") == "CABLE"]
        if ports:
            return ports[0], self._placement_si(ports[0])[:3, 3].copy()
        m = self._placement_si(e)                      # (a light: on top of it, in the ceiling)
        return None, m[:3, 3] + np.array((0.0, 0.0, 0.06))

    def circuit_conduits(self, circuit):
        """The conduits in a circuit (its IfcCableCarrierSegments)."""
        return [g for g in self.circuit_points(circuit) if self.by_guid(g).is_a("IfcCableCarrierSegment")]

    def route_circuit(self, circuit, spec, z, lang="pt"):
        """The circuit's conduits, from its board (or its first point, if it has none) to its points in turn, each
        to the nearest not yet reached; each link up to the height z, across and down. Returns the GlobalIds made."""
        import ifcopenshell.api as api
        c = self.by_guid(circuit)
        loads = [g for g in self.circuit_points(circuit) if self.by_guid(g).is_a() in LOADS
                 and not self.by_guid(g).is_a("IfcUnitaryEquipment")]
        board = self._circuit_params(c).get("Quadro") or None
        if board is not None and self.by_guid(board) is None:
            board = None
        start = board if board is not None else (loads.pop(0) if loads else None)
        if start is None or not loads:
            return []
        word = "Tubo VD" if lang == "pt" else "Conduit"
        made, here = [], start
        while loads:
            _p, a = self._wire_point(here)
            nxt = min(loads, key=lambda g: float(np.linalg.norm(self._wire_point(g)[1][:2] - a[:2])))
            loads.remove(nxt)
            port_b, b = self._wire_point(nxt)
            port_a = self._wire_point(here)[0]
            stops = [a]
            if abs(float(a[2]) - z) >= MIN_RUN:
                stops.append(np.array((a[0], a[1], z)))
            if float(np.linalg.norm((b - a)[:2])) >= MIN_RUN:
                stops.append(np.array((b[0], b[1], z)))
            stops.append(b)
            pieces = []
            for p, q in zip(stops, stops[1:]):
                if float(np.linalg.norm(q - p)) < MIN_RUN:
                    continue
                name = "{} {}".format(word, self.count("IfcCableCarrierSegment") + 1)
                g = self.add_segment(spec, p[:2], q[:2], float(p[2]), name, lang, storey=self.storey_of(nxt),
                                     end_z=float(q[2]), x_dir=self._across(pieces[-1]) if pieces else None).GlobalId
                if pieces:
                    bend = self.join_segments(pieces[-1], g, lang)
                    if bend:
                        made.append(bend)
                pieces.append(g)
            if pieces:
                if port_a is not None and self.connected(port_a) is None:
                    self.connect_to_port(pieces[0], port_a, at_end=False)
                if port_b is not None and self.connected(port_b) is None:
                    self.connect_to_port(pieces[-1], port_b)
            made += pieces
            here = nxt
        if made:
            api.system.assign_system(self.file, products=[self.by_guid(g) for g in made], system=c)
        return made

    def conduit_length(self, circuit):
        """The length (m) of a circuit's conduits."""
        return sum(float(np.linalg.norm(np.subtract(*self.segment_params(g)[:2]))) for g in self.circuit_conduits(circuit))
