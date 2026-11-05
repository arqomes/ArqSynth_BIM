"""A 3D space frame solved by its stiffness matrix (0.165, Phase 9, step 3) — the ArqSynth Modeler's
calc_space_frame (Phase 16A), its algorithm kept, without Blender: six degrees of freedom a node (ux, uy, uz, rx, ry,
rz); members with their section (A, Iy, Iz, J), turned by an orientation; loads spread along members (global, kN/m)
and on nodes; supports fixed or springs; the floors as rigid diaphragms (ux, uy, rz of their nodes tied to one);
several load cases solved with one factorisation, in symmetric band storage (500 members stay practical); results
combined and enveloped. A mechanism (a node free where it is loaded, a pivot ~0) is told, with the node.

(0.223) Shells too (core.shell: flat triangles, plate and membrane), loaded by area (kN/m²); for the many nodes a
slab's mesh brings, the nodes renumbered (reverse Cuthill–McKee) to keep the band narrow and the band solved by
dense blocks of its width (block-tridiagonal Cholesky, at LAPACK's speed).

Units: kN, m, kPa. A member's local x along it, local z from its orientation (a beam's: up), y = z × x."""

import math
from dataclasses import dataclass, field

import numpy as np

from . import shell as sh

DOF_NAMES = ("ux", "uy", "uz", "rx", "ry", "rz")
MIN_BLOCK = 32                  # (0.223) the solver's smallest block (its band's width when wider)


class SpaceFrameError(Exception):
    """An invalid or unstable model (a mechanism)."""


@dataclass
class SpaceMember:
    id: str
    n1: int
    n2: int
    e: float
    g: float
    area: float
    iy: float
    iz: float
    j: float
    orientation: tuple = (0.0, 0.0, 1.0)
    loads: dict = field(default_factory=dict)          # case -> (qx, qy, qz) global kN/m
    length: float = 0.0
    rotation: np.ndarray = None


@dataclass
class SpaceShell:
    """(0.223) A flat shell triangle: its three nodes, its concrete, its thickness; its loads by case (global, kN/m²)."""
    id: str
    nodes: tuple
    e: float
    nu: float
    t: float
    loads: dict = field(default_factory=dict)
    rotation: np.ndarray = None
    xy: np.ndarray = None
    area: float = 0.0


@dataclass(frozen=True)
class MemberResult:
    n: float                    # axial (compression < 0)
    vy: float
    vz: float
    t: float
    my: float                   # the largest moment about local y (a beam's bending in its vertical plane)
    mz: float
    ends: tuple                 # the 12 end forces, local


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = float(np.linalg.norm(v))
    if n <= 1e-12:
        raise SpaceFrameError("null orientation")
    return v / n


def local_axes(p1, p2, orientation=(0.0, 0.0, 1.0)):
    x = _unit(np.asarray(p2, dtype=float) - np.asarray(p1, dtype=float))
    ref = _unit(orientation)
    if abs(float(x @ ref)) > 0.95:
        ref = np.array((0.0, 1.0, 0.0))
        if abs(float(x @ ref)) > 0.95:
            ref = np.array((1.0, 0.0, 0.0))
    y = _unit(np.cross(ref, x))
    z = _unit(np.cross(x, y))
    return np.vstack((x, y, z))


def local_stiffness(e, g, area, iy, iz, j, length):
    if min(e, g, area, iy, iz, j, length) <= 0.0:
        raise SpaceFrameError("a member's property null or negative")
    k = np.zeros((12, 12))
    axial, torsion = e * area / length, g * j / length
    k[0, 0] = k[6, 6] = axial
    k[0, 6] = k[6, 0] = -axial
    k[3, 3] = k[9, 9] = torsion
    k[3, 9] = k[9, 3] = -torsion

    def bending(idx, ei, sign):
        l2, l3 = length * length, length ** 3
        vals = np.array([
            [12 * ei / l3, sign * 6 * ei / l2, -12 * ei / l3, sign * 6 * ei / l2],
            [sign * 6 * ei / l2, 4 * ei / length, -sign * 6 * ei / l2, 2 * ei / length],
            [-12 * ei / l3, -sign * 6 * ei / l2, 12 * ei / l3, -sign * 6 * ei / l2],
            [sign * 6 * ei / l2, 2 * ei / length, -sign * 6 * ei / l2, 4 * ei / length]])
        for r, gr in enumerate(idx):
            for c, gc in enumerate(idx):
                k[gr, gc] += vals[r, c]

    bending((1, 5, 7, 11), e * iz, 1.0)        # local y, moment about z
    bending((2, 4, 8, 10), e * iy, -1.0)       # local z, moment about y
    return k


def transformation(rotation):
    t = np.zeros((12, 12))
    for s in (0, 3, 6, 9):
        t[s:s + 3, s:s + 3] = rotation
    return t


def distributed_load_local(qx, qy, qz, length):
    """A uniform load's fixed-end forces, local (12,)."""
    f = np.zeros(12)
    f[0] = f[6] = qx * length / 2.0
    f[1] = f[7] = qy * length / 2.0
    f[5] = qy * length ** 2 / 12.0
    f[11] = -f[5]
    f[2] = f[8] = qz * length / 2.0
    f[4] = -qz * length ** 2 / 12.0
    f[10] = -f[4]
    return f


def result_from(forces):
    f = np.asarray(forces, dtype=float)
    return MemberResult(float(-f[0]), float(max(abs(f[1]), abs(f[7]))), float(max(abs(f[2]), abs(f[8]))),
                        float(max(abs(f[3]), abs(f[9]))), float(max(abs(f[4]), abs(f[10]))),
                        float(max(abs(f[5]), abs(f[11]))), tuple(float(v) for v in f))


def span_moment(ends, qz_local, length):
    """The bending moment about local y along a member, sagging positive (its bottom — local −z — in tension):
    M(x) = My1 + Fz1 x + qz x²/2 from its end 1's forces and the uniform load across local z — (M at end 1, M at the
    span's stationary point (0 if none inside), M at end 2)."""
    fz1, my1 = ends[2], ends[4]

    def m(x):
        return my1 + fz1 * x + qz_local * x * x / 2.0

    mspan = 0.0
    if abs(qz_local) > 1e-12:
        x = -fz1 / qz_local
        if 0.0 < x < length:
            mspan = m(x)
    return m(0.0), mspan, m(length)


def moments_along(ends, qz_local, length, stations=11):
    """(0.220) The bending moment about local y at `stations` points evenly along a member (its ends included),
    sagging positive (span_moment's M(x)) — what its diagram is drawn with."""
    fz1, my1 = ends[2], ends[4]
    xs = np.linspace(0.0, float(length), max(int(stations), 2))
    return [float(my1 + fz1 * x + qz_local * x * x / 2.0) for x in xs]


class _Pivot(Exception):
    """A pivot of the elimination null or negative: at this (renumbered) degree of freedom."""

    def __init__(self, index):
        super().__init__(index)
        self.index = index


def _first_bad_pivot(c, tol):
    """The first pivot of a dense symmetric block's elimination at or under tol (its index)."""
    a = np.array(c, dtype=float)
    for p in range(len(a)):
        pivot = a[p, p]
        if not np.isfinite(pivot) or pivot <= tol:
            return p
        a[p + 1:, p + 1:] -= np.outer(a[p + 1:, p], a[p, p + 1:]) / pivot
    return len(a) - 1


def band_solve(band, rhs, bw, tol):
    """(0.223) A symmetric positive definite banded system (band[r, k] = A[r, r + k], k ≤ bw) solved for each row
    of rhs (cases × n): cut in dense blocks at least the band wide, it is block-tridiagonal — each block's Schur
    complement checked by Cholesky (a pivot at or under tol raises _Pivot with its index) and solved by LAPACK."""
    n = band.shape[0]
    nb = max(int(bw), MIN_BLOCK)
    width = band.shape[1]

    def diagonal(s, e):
        size = e - s
        d = np.zeros((size, size))
        for k in range(min(width - 1, size - 1) + 1):
            idx = np.arange(size - k)
            d[idx, idx + k] = band[s + idx, k]
        return d + np.triu(d, 1).T

    def coupling(s, e, f):
        """A[s:e, e:f]."""
        b = np.zeros((e - s, f - e))
        for r in range(max(s, e - width + 1), e):
            hi = min(f, r + width)
            b[r - s, :hi - e] = band[r, e - r:hi - r]
        return b

    y = np.array(rhs, dtype=float).T.copy()
    blocks = []
    prev = None
    for s in range(0, n, nb):
        e = min(s + nb, n)
        c = diagonal(s, e)
        if prev is not None:
            c_prev, b_prev, s_prev = prev
            z = np.linalg.solve(c_prev, np.hstack((b_prev, y[s_prev:s])))
            c -= b_prev.T @ z[:, :b_prev.shape[1]]
            y[s:e] -= b_prev.T @ z[:, b_prev.shape[1]:]
        try:
            low = np.linalg.cholesky(c)
            bad = float(np.min(np.diag(low))) ** 2 <= tol
        except np.linalg.LinAlgError:
            bad = True
        if bad:
            raise _Pivot(s + _first_bad_pivot(c, tol))
        b = coupling(s, e, min(e + nb, n)) if e < n else np.zeros((e - s, 0))
        blocks.append((c, b, s, e))
        prev = (c, b, s)
    x = np.zeros_like(y)
    for c, b, s, e in reversed(blocks):
        r = y[s:e] - (b @ x[e:e + b.shape[1]] if b.shape[1] else 0.0)
        x[s:e] = np.linalg.solve(c, r)
    return x.T


class SpaceFrame:
    def __init__(self, tolerance=1e-5):
        self.tolerance = float(tolerance)
        self.nodes = []
        self.labels = []
        self.members = []
        self.shells = []                # (0.223) [SpaceShell]
        self.supports = {}              # node -> (fixes (6 bools), springs (6))
        self.nodal_loads = {}           # case -> {node: (6,)}
        self.diaphragms = []            # (name, nodes, master)
        self._index = {}                # (0.223) a node's place by its rounded position (a mesh's many nodes)

    def add_node(self, x, y, z, label=""):
        p = np.array((x, y, z), dtype=float)
        key = tuple(np.round(p / max(self.tolerance, 1e-9)).astype(np.int64))
        for dx in (-1, 0, 1):                               # (the cells around: a point near a cell's edge)
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for k in self._index.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        if np.linalg.norm(p - np.asarray(self.nodes[k])) <= self.tolerance:
                            return k
        self.nodes.append(tuple(float(v) for v in p))
        self.labels.append(label or "N{}".format(len(self.nodes)))
        self._index.setdefault(key, []).append(len(self.nodes) - 1)
        return len(self.nodes) - 1

    def add_member(self, mid, n1, n2, e, g, area, iy, iz, j, orientation=(0.0, 0.0, 1.0)):
        p1, p2 = self.nodes[n1], self.nodes[n2]
        length = float(np.linalg.norm(np.subtract(p2, p1)))
        if length <= self.tolerance:
            raise SpaceFrameError("member {} of null length".format(mid))
        m = SpaceMember(str(mid), int(n1), int(n2), float(e), float(g), float(area), float(iy), float(iz), float(j),
                        tuple(orientation))
        m.length = length
        m.rotation = local_axes(p1, p2, orientation)
        self.members.append(m)
        return m

    def add_shell(self, sid, n1, n2, n3, e, nu, t):
        """(0.223) A flat shell triangle on three nodes (counter-clockwise seen from its top)."""
        s = SpaceShell(str(sid), (int(n1), int(n2), int(n3)), float(e), float(nu), float(t))
        try:
            s.rotation, s.xy = sh.axes(*(self.nodes[k] for k in s.nodes))
        except sh.ShellError as exc:
            raise SpaceFrameError("shell {}: {}".format(sid, exc)) from exc
        s.area = float(sh._area(s.xy))
        self.shells.append(s)
        return s

    def add_shell_load(self, case, shell, qx=0.0, qy=0.0, qz=0.0):
        """(0.223) A load over a shell's area (global, kN/m²)."""
        old = shell.loads.get(case, (0.0, 0.0, 0.0))
        shell.loads[case] = (old[0] + qx, old[1] + qy, old[2] + qz)

    def set_support(self, node, fixes=(True,) * 6, springs=(0.0,) * 6):
        self.supports[int(node)] = (tuple(bool(v) for v in fixes), tuple(max(float(v), 0.0) for v in springs))

    def add_diaphragm(self, name, nodes, master=None):
        unique = tuple(dict.fromkeys(int(n) for n in nodes))
        if len(unique) < 2:
            return None
        master = unique[0] if master is None else int(master)
        self.diaphragms.append((str(name), unique, master))
        return master

    def add_member_load(self, case, member, qx=0.0, qy=0.0, qz=0.0):
        old = member.loads.get(case, (0.0, 0.0, 0.0))
        member.loads[case] = (old[0] + qx, old[1] + qy, old[2] + qz)

    def add_nodal_load(self, case, node, fx=0.0, fy=0.0, fz=0.0, mx=0.0, my=0.0, mz=0.0):
        loads = self.nodal_loads.setdefault(case, {})
        loads[int(node)] = loads.get(int(node), np.zeros(6)) + np.array((fx, fy, fz, mx, my, mz), dtype=float)

    def _links(self):
        """Each pair of nodes a member, a shell or a diaphragm ties."""
        for m in self.members:
            yield m.n1, m.n2
        for s in self.shells:
            a, b, c = s.nodes
            yield a, b
            yield b, c
            yield a, c
        for _n, nodes, master in self.diaphragms:
            for n in nodes:
                yield master, n

    def _ordering(self):
        """(0.223) Each node's place in the band: the nodes renumbered by reverse Cuthill–McKee (from the least tied
        node, each node's neighbours the least tied first; reversed) — a mesh's band stays as narrow as it is wide."""
        n = len(self.nodes)
        adj = [set() for _ in range(n)]
        for a, b in self._links():
            if a != b:
                adj[a].add(b)
                adj[b].add(a)
        degree = [len(x) for x in adj]
        seen = [False] * n
        order = []
        for start in sorted(range(n), key=lambda k: degree[k]):
            if seen[start]:
                continue
            seen[start] = True
            queue, head = [start], 0
            while head < len(queue):
                v = queue[head]
                head += 1
                for w in sorted((w for w in adj[v] if not seen[w]), key=lambda k: degree[k]):
                    seen[w] = True
                    queue.append(w)
            order.extend(queue)
        order.reverse()
        pos = np.empty(n, dtype=int)
        pos[order] = np.arange(n)
        return pos

    def _bandwidth(self, pos):
        bw = 5
        for a, b in self._links():
            bw = max(bw, 6 * abs(int(pos[a]) - int(pos[b])) + 5)
        return min(bw, max(6 * len(self.nodes) - 1, 0))

    @staticmethod
    def _dofs(pos, nodes):
        return np.array([6 * int(pos[v]) + d for v in nodes for d in range(6)])

    @staticmethod
    def _add_block(band, dofs, k):
        """An element's stiffness (its dofs in the band's numbering) into the band: its upper half."""
        r, c = np.meshgrid(dofs, dofs, indexing="ij")
        upper = r <= c
        np.add.at(band, (r[upper], (c - r)[upper]), k[upper])

    @staticmethod
    def _add(band, r, c, v):
        if c < r:
            r, c = c, r
        if c - r < band.shape[1]:
            band[r, c - r] += v

    def _matrices(self, m, case):
        k = local_stiffness(m.e, m.g, m.area, m.iy, m.iz, m.j, m.length)
        t = transformation(m.rotation)
        q_local = m.rotation @ np.asarray(m.loads.get(case, (0.0, 0.0, 0.0)), dtype=float)
        f = distributed_load_local(*q_local, m.length)
        return k, f, t, t.T @ k @ t, t.T @ f

    def _shell_matrices(self, s):
        """(0.223) A shell's local stiffness, its transformation and its global stiffness."""
        try:
            k = sh.local_stiffness(s.xy, s.e, s.nu, s.t)
        except sh.ShellError as exc:
            raise SpaceFrameError("shell {}: {}".format(s.id, exc)) from exc
        t = sh.transformation(s.rotation)
        return k, t, t.T @ k @ t

    @staticmethod
    def _shell_load(s, case):
        """A shell's area load as its nodes' forces (a third each, global; 18,)."""
        f = np.zeros(18)
        q = np.asarray(s.loads.get(case, (0.0, 0.0, 0.0)), dtype=float) * s.area / 3.0
        for k in range(3):
            f[6 * k:6 * k + 3] = q
        return f

    def _assemble(self, cases):
        if not self.members and not self.shells:
            raise SpaceFrameError("no members")
        if not self.supports:
            raise SpaceFrameError("no supports")
        pos = self._ordering()
        n, bw = 6 * len(self.nodes), self._bandwidth(pos)
        band = np.zeros((n, bw + 1))
        rhs = np.zeros((len(cases), n))
        cache = {}
        for m in self.members:
            dofs = self._dofs(pos, (m.n1, m.n2))
            for ci, case in enumerate(cases):
                k, f, t, kg, fg = self._matrices(m, case)
                cache[(m.id, case)] = (k, f, t)
                if ci == 0:
                    self._add_block(band, dofs, kg)
                rhs[ci, dofs] += fg
        for s in self.shells:
            dofs = self._dofs(pos, s.nodes)
            k, t, kg = self._shell_matrices(s)
            cache[("shell", s.id)] = (k, t, kg)
            self._add_block(band, dofs, kg)
            for ci, case in enumerate(cases):
                rhs[ci, dofs] += self._shell_load(s, case)
        for ci, case in enumerate(cases):
            for node, load in self.nodal_loads.get(case, {}).items():
                i = 6 * int(pos[node])
                rhs[ci, i:i + 6] += load
        top = max(float(np.max(np.abs(band[:, 0]))), 1.0)
        support_penalty, diaphragm_penalty = top * 1e10, top * 1e8
        for node, (fixes, springs) in self.supports.items():
            for dof, (fixed, spring) in enumerate(zip(fixes, springs)):
                i = 6 * int(pos[node]) + dof
                if fixed:
                    band[i, 0] += support_penalty
                elif spring > 0.0:
                    band[i, 0] += spring
        for _name, nodes, master in self.diaphragms:
            for node in nodes:
                if node == master:
                    continue
                for dof in (0, 1, 5):
                    a, b = 6 * int(pos[master]) + dof, 6 * int(pos[node]) + dof
                    band[a, 0] += diaphragm_penalty
                    band[b, 0] += diaphragm_penalty
                    self._add(band, a, b, -diaphragm_penalty)
        idle = top * 1e-12
        order = np.argsort(pos)
        for i in np.flatnonzero(np.abs(band[:, 0]) <= idle):
            if np.max(np.abs(rhs[:, i])) > idle:
                place, dof = divmod(int(i), 6)
                raise SpaceFrameError("load on a free degree: node {} ({})".format(self.labels[order[place]],
                                                                                   DOF_NAMES[dof]))
            band[i, 0] += support_penalty
        return band, rhs, bw, top, cache, pos

    def solve(self, cases=("G",)):
        """{case: {"disp", "forces", "members", "reactions", (0.223) "shells"}}."""
        cases = tuple(cases)
        band, rhs, bw, top, cache, pos = self._assemble(cases)
        try:
            x = band_solve(band, rhs, bw, top * 1e-10)
        except _Pivot as bad:
            place, dof = divmod(bad.index, 6)
            node = int(np.argsort(pos)[place])
            raise SpaceFrameError("mechanism: node {} ({}) with no stiffness".format(self.labels[node],
                                                                                     DOF_NAMES[dof])) from None
        index = self._dofs(pos, range(len(self.nodes)))    # (each node's dofs, in the band's numbering)
        return {case: self._post(case, x[ci][index], cache) for ci, case in enumerate(cases)}

    def _post(self, case, d, cache):
        forces, members, shells = {}, {}, {}
        balance = np.zeros((len(self.nodes), 6))
        for m in self.members:
            dofs = list(range(6 * m.n1, 6 * m.n1 + 6)) + list(range(6 * m.n2, 6 * m.n2 + 6))
            k, f, t = cache[(m.id, case)]
            local = k @ (t @ d[dofs]) - f
            forces[m.id] = local
            members[m.id] = result_from(local)
            g = t.T @ local
            balance[m.n1] += g[:6]
            balance[m.n2] += g[6:]
        for s in self.shells:                               # (0.223) its moments and forces at its middle
            dofs = [6 * v + k for v in s.nodes for k in range(6)]
            k, t, kg = cache[("shell", s.id)]
            shells[s.id] = sh.resultants(s.xy, s.e, s.nu, s.t, t @ d[dofs])
            g = kg @ d[dofs] - self._shell_load(s, case)
            for j, v in enumerate(s.nodes):
                balance[v] += g[6 * j:6 * j + 6]
        for node, load in self.nodal_loads.get(case, {}).items():
            balance[node] -= load
        return {"disp": d, "forces": forces, "members": members, "shells": shells,
                "reactions": {node: tuple(float(v) for v in balance[node]) for node in self.supports}}

    def combined_shell(self, results, factors, shell):
        """(0.223) A shell's (mx, my, mxy, nx, ny, nxy) under a combination."""
        out = np.zeros(6)
        for case, factor in factors.items():
            if case in results:
                out += float(factor) * results[case]["shells"][shell.id]
        return out

    def combined_forces(self, results, factors, member):
        f = np.zeros(12)
        for case, factor in factors.items():
            if case in results:
                f += float(factor) * results[case]["forces"][member.id]
        return f

    def local_qz(self, member, factors):
        q = np.zeros(3)
        for case, factor in factors.items():
            q += float(factor) * np.asarray(member.loads.get(case, (0.0, 0.0, 0.0)), dtype=float)
        return float((member.rotation @ q)[2])

    def envelope(self, results, combinations):
        """{member id: {"n_min", "n_max", "vz", "vy", "t", "m_pos" (sagging), "m_neg" (hogging), "mz", "combo"}}
        over the combinations [(name, {case: factor})]."""
        out = {}
        for m in self.members:
            rec = {"n_min": 0.0, "n_max": 0.0, "vy": 0.0, "vz": 0.0, "t": 0.0, "m_pos": 0.0, "m_neg": 0.0,
                   "mz": 0.0, "combo": ""}
            worst = -1.0
            for name, factors in combinations:
                f = self.combined_forces(results, factors, m)
                r = result_from(f)
                m1, ms, m2 = span_moment(f, self.local_qz(m, factors), m.length)
                rec["n_min"], rec["n_max"] = min(rec["n_min"], r.n), max(rec["n_max"], r.n)
                rec["vy"], rec["vz"] = max(rec["vy"], r.vy), max(rec["vz"], r.vz)
                rec["t"], rec["mz"] = max(rec["t"], r.t), max(rec["mz"], r.mz)
                rec["m_pos"] = max(rec["m_pos"], m1, ms, m2)
                rec["m_neg"] = min(rec["m_neg"], m1, ms, m2)
                size = max(abs(r.n), r.vz, r.my, abs(ms))
                if size > worst:
                    worst, rec["combo"] = size, name
            out[m.id] = rec
        return out

    def deflection_mid(self, results, factors, member):
        """A member's deflection at mid-span, from its chord (m, down positive), under a combination — across its
        local z (a beam's vertical)."""
        f = self.combined_forces(results, factors, member)
        dofs = list(range(6 * member.n1, 6 * member.n1 + 6)) + list(range(6 * member.n2, 6 * member.n2 + 6))
        dg = np.zeros(12)
        for case, factor in factors.items():
            if case in results:
                dg += float(factor) * results[case]["disp"][dofs]
        dl = transformation(member.rotation) @ dg
        ei = member.e * member.iy
        x = member.length / 2.0
        w1, th1, w2 = dl[2], -dl[4], dl[8]
        q = self.local_qz(member, factors)
        vz1, my1 = f[2], f[4]
        w_mid = w1 + th1 * x + (my1 * x ** 2 / 2.0 + vz1 * x ** 3 / 6.0 + q * x ** 4 / 24.0) / ei
        return -(w_mid - (w1 + w2) / 2.0)


def rectangle(b, h):
    """(A, Iy, Iz, J) of a b × h section (h along local z: the strong axis of a beam standing up)."""
    a, iy, iz = b * h, b * h ** 3 / 12.0, h * b ** 3 / 12.0
    s, l = min(b, h), max(b, h)
    j = s ** 3 * l * (1.0 / 3.0 - 0.21 * s / l * (1.0 - (s / l) ** 4 / 12.0))
    return a, iy, iz, j


def shape_rects(shape, sx, sy, web=0.0):
    """(0.227) A column's section as rectangles [(x0, y0, x1, y1)] in its own axes, centred on its bounding box as
    IFC's profiles are: "rect" sx × sy; "L" (IfcLShapeProfileDef) its legs along its left (−x) and bottom (−y)
    sides, `web` thick; "T" (IfcTShapeProfileDef) its flange sx wide at the top (+y), its web in the middle. (A
    circle is not rectangles: see section.)"""
    hx, hy = sx / 2.0, sy / 2.0
    if shape == "L":
        t = min(web, sx, sy)
        return [(-hx, -hy, -hx + t, hy), (-hx + t, -hy, hx, -hy + t)]
    if shape == "T":
        t = min(web, sy)
        return [(-hx, hy - t, hx, hy), (-t / 2.0, -hy, t / 2.0, hy - t)]
    return [(-hx, -hy, hx, hy)]


def section(shape, sx, sy, web=0.0):
    """(0.227) (A, I about its own y, I about its own x, J, centroid (x, y)) of a column's section in its own axes
    (sx along x, sy along y): a rectangle, a circle (diameter sx), an L or a T (shape_rects) — the inertias about
    its centroid, parallel to its sides (an L's product of inertia left out); J of thin legs Σ b t³ / 3."""
    if shape == "circle":
        r = sx / 2.0
        i = math.pi * r ** 4 / 4.0
        return math.pi * r * r, i, i, 2.0 * i, (0.0, 0.0)
    if shape not in ("L", "T"):
        a, iy, iz, j = rectangle(sy, sx)                # (sx along local z: I about its own y first)
        return a, iy, iz, j, (0.0, 0.0)
    rects = shape_rects(shape, sx, sy, web)
    parts = [((x1 - x0) * (y1 - y0), (x0 + x1) / 2.0, (y0 + y1) / 2.0, x1 - x0, y1 - y0) for x0, y0, x1, y1 in rects]
    area = sum(p[0] for p in parts)
    cx, cy = sum(p[0] * p[1] for p in parts) / area, sum(p[0] * p[2] for p in parts) / area
    i_y = sum(h * w ** 3 / 12.0 + a * (x - cx) ** 2 for a, x, _y, w, h in parts)
    i_x = sum(w * h ** 3 / 12.0 + a * (y - cy) ** 2 for a, _x, y, w, h in parts)
    j = sum(max(w, h) * min(w, h) ** 3 / 3.0 for _a, _x, _y, w, h in parts)
    return area, i_y, i_x, j, (cx, cy)
