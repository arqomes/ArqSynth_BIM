"""Connect to the network (0.142, Phase 6, step 3: «ligar à rede, ramal automático»): each free outlet of a sanitary
fixture (its drain, its cold and hot water) gets its branch to the nearest pipe of its system — a drain to the
collector or the stack (sewage or waste water), falling 2 %, ending on it with a tee; the water from the cold /
hot water pipe, up or down from it and across to the fixture. A short piece leaves the outlet the way it points
(into the wall, under the floor) before the branch turns. Its level run goes round the columns and pad footings on
its way, with square bends (0.199, core/routing)."""

import ifcopenshell.util.element
import numpy as np

from ..core import routing
from . import catalog
from .services import COLLAR, MIN_PIECE
from .systems import SYSTEMS

DRAIN_SLOPE = 0.02          # a drain branch falls this much towards the network
OUT = 0.10                  # m: out of the outlet the way it points, before turning
CLEAR = 0.05                # m (0.199): between a branch and a column it goes round
SPECS = {"sewage": "tubo_100", "waste": "tubo_50", "rain": "tubo_100", "cold": "tubo_25", "hot": "tubo_25",
         "gas": "gas_cobre_15"}                                            # (gas: 0.198, a gas hob's)
NETWORKS = {"sewage": ("sewage", "waste"), "waste": ("waste", "sewage"), "rain": ("rain",), "cold": ("cold",),
            "hot": ("hot",), "gas": ("gas",)}  # (the systems a branch of each may join, the first best)


class BranchMixin:
    def _branch_target(self, key, start, storey, leave=(), only=None):
        """The nearest point, with room for a tee, on a pipe of a network a branch of system `key` may join, from
        `start` (3,): (its GlobalId, the point (3,)) — a drain only to a point lower than it can fall to — or None.
        only (0.148): the pipes it may join (None: any)."""
        drain = SYSTEMS[key][4]
        best = None
        for rank, system in enumerate(NETWORKS.get(key, ())):
            for e in self.file.by_type("IfcPipeSegment"):
                g = e.GlobalId
                if g in leave or (only is not None and g not in only) or self.kind_of(g) != "pipe" \
                        or self.system_of(g) != system:
                    continue
                s, end, _z = self.segment_params(g)
                d = end - s
                length, run = float(np.linalg.norm(d)), float(np.linalg.norm(d[:2]))
                margin = max(self._size(e)) + 2 * COLLAR + MIN_PIECE
                if run < 1e-6:                                     # a stack: where the branch reaches it
                    gap = float(np.linalg.norm(s[:2] - start[:2]))
                    z = float(start[2]) - (DRAIN_SLOPE * gap if drain else 0.0)
                    lo, hi = sorted((float(s[2]), float(end[2])))
                    if not lo + margin <= z <= hi - margin:
                        continue
                    point = np.array((s[0], s[1], z))
                else:
                    if self.storey_of(g) != storey:
                        continue
                    k = float(np.dot(start[:2] - s[:2], d[:2])) / run ** 2
                    k = min(max(k, margin / length), 1.0 - margin / length)
                    if margin / length > 1.0 - margin / length:
                        continue                                   # (too short for a tee)
                    point = s + d * k
                    gap = float(np.linalg.norm(point[:2] - start[:2]))
                    if drain and float(point[2]) > float(start[2]) - 0.005:
                        continue                                   # (higher than the outlet: it cannot fall to it)
                key_ = (rank, gap)
                if best is None or key_ < best[0]:
                    best = (key_, g, point)
        return None if best is None else (best[1], best[2])

    def connect_fixture(self, guid, lang="pt", changed=None, only=None):
        """Each free outlet of the fixture `guid` with a system (drain, cold, hot) gets its branch to the network
        (see the module). changed: a list the pipes split by a tee are added to; only (0.148): a set of the pipes it
        may join (the pieces a tee splits off them join it). Returns [(outlet's name, its system's key, the
        GlobalId of the pipe joined, or None: no network for it)]."""
        report = []
        storey = self.storey_of(guid)
        for port in list(self.ports(guid)):
            if self.connected(port) is not None or (port.PredefinedType or "") != "PIPE":
                continue
            key = self.port_system(port)
            if key not in SPECS:
                continue
            at = self._placement_si(port)[:3, 3].copy()
            way = self.port_way(port)
            out = at + way * OUT
            target = self._branch_target(key, out, storey, only=only)
            if target is None:
                report.append((port.Name, key, None))
                continue
            main, point = target
            if changed is not None and main not in changed:
                changed.append(main)
            spec = catalog.BY_KEY[SPECS[key]]
            self._last_rest = None
            made = self._make_branch(spec, port, at, out, main, point, SYSTEMS[key][4], storey, lang)
            self.set_system(made, key, lang)
            if only is not None and getattr(self, "_last_rest", None):
                only.add(self._last_rest)              # (the piece its tee split off the main: still a main)
            report.append((port.Name, key, main))
        return report

    def _piece(self, spec, a, b, lang, storey, like=None):
        """One pipe a → b (3D)."""
        word = "Tubo" if lang == "pt" else "Pipe"
        name = "{} {}".format(word, self.count("IfcPipeSegment") + 1)
        return self.add_segment(spec, a[:2], b[:2], float(a[2]), name, lang, storey=storey, end_z=float(b[2]),
                                x_dir=self._across(like) if like else None).GlobalId

    def _make_branch(self, spec, port, at, out, main, point, drain, storey, lang):
        """The pieces of one branch, joined, its outlet's end connected, its network's end on `main` by a tee.
        A drain runs from the outlet to the network; water from the network to the outlet. Returns their ids
        (and their fittings')."""
        made = []
        join = lambda a, b: made.append(self.join_segments(a, b, lang))          # noqa: E731
        if drain:
            first = self._piece(spec, at, out, lang, storey)
            made.append(first)
            self.connect_to_port(first, port, at_end=False)
            last, start = first, out
            reach = float(np.linalg.norm((point - out)[:2])) + routing.MAX_DETOUR     # (its run: no higher than this)
            lo, hi = float(point[2]), min(float(out[2]), float(point[2]) + DRAIN_SLOPE * reach)
            way = self._branch_way(spec, out, point, lo, hi, last_along=True)
            way, point = self._wye_end(spec, way, main, point, lo, hi)
            gap = _length(way)
            low = float(point[2]) + DRAIN_SLOPE * gap               # (down there first, then at 2 % to it)
            if float(out[2]) - low >= MIN_PIECE:
                start = np.array((out[0], out[1], low))
                down = self._piece(spec, out, start, lang, storey, like=first)
                made.append(down)
                join(first, down)
                last = down
            run = None
            for a, b in _level_run(way, start, point):
                run = self._piece(spec, a, b, lang, storey, like=last)
                made.append(run)
                join(last, run)
                last = run
            tee = self.add_tee(main, run, lang)
        else:                                      # (water: from the network down / up to the inlet's height, then
            pieces = []                            # straight in to it — 0.148: not through the wall)
            corner = np.array((point[0], point[1], at[2]))
            if abs(float(point[2]) - float(at[2])) >= MIN_PIECE:
                pieces.append((point, corner))
                start = corner
            else:
                start = np.array((point[0], point[1], point[2]))
            if float(np.linalg.norm((at - start)[:2])) >= MIN_PIECE or not pieces:
                way = self._branch_way(spec, start, at, float(start[2]), float(at[2]), first_along=not pieces,
                                       last_along=True)              # (into the inlet head on)
                pieces.extend(_level_run(way, start, at))
            last = None
            for a, b in pieces:
                g = self._piece(spec, a, b, lang, storey, like=last)
                made.append(g)
                if last is not None:
                    join(last, g)
                last = g
            tee = self.add_tee(main, made[0], lang)
            self.connect_to_port(last, port)
        made.append(tee)
        return [g for g in made if g]

    def _branch_way(self, spec, a, b, lo, hi, first_along=False, last_along=False):
        """The way in plan (0.199) of a branch's level run a → b, between the heights lo and hi: round the columns
        and pad footings on the straight line (core/routing), with room for its bends — or straight."""
        size = max(spec.profile[:2])
        boxes = self._branch_obstacles(min(lo, hi) - size / 2, max(lo, hi) + size / 2, size / 2 + CLEAR)
        way = routing.route(a[:2], b[:2], boxes, min_run=2 * size + MIN_PIECE, first_along=first_along,
                            last_along=last_along) if boxes else None
        return way or [np.asarray(a, float)[:2], np.asarray(b, float)[:2]]

    def _wye_end(self, spec, way, main, point, lo, hi):
        """(0.200) A drain's way (plan) ending square on its main, made to end at 45° pointing down the main (a
        wye): the last run turns a leg (2 diameters + 5 cm) before the main and meets it that far downstream — or, a
        branch with one short run, goes at 45° all the way. Unchanged on a stack, with no room on the main, or an obstacle in the
        way. Returns (the way, the point on the main)."""
        sm, endm, _z = self.segment_params(main)
        d = endm - sm
        length, run = float(np.linalg.norm(d)), float(np.linalg.norm(d[:2]))
        if run < 1e-6:
            return way, point                                       # (a stack: square)
        dm = d / length
        flow = dm if float(endm[2]) <= float(sm[2]) + 1e-9 else -dm  # (down the main: its lower end, or as drawn)
        size = max(spec.profile[:2])
        leg, need = 2 * size + MIN_PIECE, 2 * size + MIN_PIECE
        p, q = np.asarray(way[-1], float), np.asarray(way[-2], float)
        last = float(np.linalg.norm(p - q))
        if last - leg >= need:
            head = way[:-1] + [p + (q - p) / last * leg]
        elif len(way) == 2 and last >= need:
            leg, head = last, way[:-1]
        else:
            return way, point
        end = np.asarray(point, float) + flow * leg / float(np.linalg.norm(flow[:2]))
        k = float(np.dot(end - sm, dm))
        margin = max(self._size(self.by_guid(main))) + size / 2 / np.sin(np.radians(45.0)) + COLLAR + MIN_PIECE
        if not margin <= k <= length - margin:
            return way, point
        end = sm + dm * k
        boxes = self._branch_obstacles(lo - size / 2, hi + size / 2, size / 2 + CLEAR)
        if routing.blocked(head[-1], end[:2], boxes):
            return way, point
        return head + [end[:2]], end

    def _branch_obstacles(self, lo, hi, grow):
        """The boxes in plan (4 corners each, grown by `grow`) of the columns and pad footings between the heights
        lo and hi: what a branch goes round (0.199)."""
        out = []
        for e in self.file.by_type("IfcColumn"):
            try:
                centre, x, (ha, hb), base, top = self.column_box(e.GlobalId)
            except Exception:                              # (one not made by this program: no section of ours)
                continue
            if base < hi and top > lo:
                out.append(_box(centre, x, ha + grow, hb + grow))
        for e in self.file.by_type("IfcFooting"):
            if ifcopenshell.util.element.get_predefined_type(e) != "PAD_FOOTING":     # (its type says)
                continue
            try:
                centre, x, length, width, top = self.footing_params(e.GlobalId)
            except Exception:
                continue
            if float(self.placement(e.GlobalId)[2, 3]) < hi and top > lo:
                out.append(_box(centre, x[:2], length / 2 + grow, width / 2 + grow))
        return out


def _box(centre, x, half_x, half_y):
    """The 4 corners in plan of a box centred on `centre`, its x direction `x`."""
    x = np.asarray(x, float)[:2]
    x = x / np.linalg.norm(x)
    y = np.array((-x[1], x[0]))
    c = np.asarray(centre, float)[:2]
    return np.array([c + x * i * half_x + y * j * half_y for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


def _length(way):
    return sum(float(np.linalg.norm(np.asarray(q) - np.asarray(p))) for p, q in zip(way, way[1:]))


def _level_run(way, start, end):
    """The pieces (a, b) 3D of a run along `way` (plan) from `start` to `end`: its height going from one's to the
    other's evenly along it (a drain's slope)."""
    total = _length(way)
    if total < 1e-9:
        return [(np.asarray(start, float), np.asarray(end, float))]
    z0, z1 = float(start[2]), float(end[2])
    pieces, done = [], 0.0
    for p, q in zip(way, way[1:]):
        step = float(np.linalg.norm(np.asarray(q) - np.asarray(p)))
        a = np.array((p[0], p[1], z0 + (z1 - z0) * done / total))
        done += step
        b = np.array((q[0], q[1], z0 + (z1 - z0) * done / total))
        pieces.append((a, b))
    pieces[0] = (np.asarray(start, float), pieces[0][1])
    pieces[-1] = (pieces[-1][0], np.asarray(end, float))
    return pieces
