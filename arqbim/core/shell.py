"""A flat shell triangle (0.223, Phase 9, step 3: the slabs as shells): a plate in bending — the discrete Kirchhoff
triangle (DKT; Batoz, Bathe & Ho 1980), thin plates' standard — and a membrane (the constant strain triangle) side by
side, each node with the space frame's six degrees of freedom (ux, uy, uz, rx, ry, rz; the rotation about its normal
held by a small stiffness, the plate having none). Its local axes: x the global X laid on its plane (Y if the plane
is across X), z its normal (from its nodes' order: counter-clockwise seen from above is up), y = z × x. A slab's
moments: sagging positive (its bottom in tension), per metre, at the triangle's middle.

Units: kN, m, kPa."""

import numpy as np

DRILL = 1e-3                    # the rotation about the normal: held by this part of the plate's D (per node)
# the three points of the rule exact for a quadratic over a triangle (its sides' middles), as (ξ, η)
_POINTS = ((0.5, 0.0), (0.5, 0.5), (0.0, 0.5))


class ShellError(Exception):
    """A degenerate triangle (no area) or a property null."""


def axes(p1, p2, p3):
    """The triangle's local axes (3 × 3, rows x, y, z) and its nodes' local (x, y) (3 × 2)."""
    p = np.array((p1, p2, p3), dtype=float)
    n = np.cross(p[1] - p[0], p[2] - p[0])
    size = float(np.linalg.norm(n))
    if size <= 1e-12:
        raise ShellError("a triangle with no area")
    n = n / size
    ref = np.array((1.0, 0.0, 0.0)) if abs(n[0]) < 0.9 else np.array((0.0, 1.0, 0.0))
    x = ref - (ref @ n) * n
    x = x / np.linalg.norm(x)
    y = np.cross(n, x)
    rot = np.vstack((x, y, n))
    local = (p - p[0]) @ rot[:2].T
    return rot, local


def plate_matrix(e, nu, t):
    """The plate's bending rigidity matrix (3 × 3): D [[1, ν, 0], [ν, 1, 0], [0, 0, (1 − ν)/2]]."""
    d = e * t ** 3 / (12.0 * (1.0 - nu * nu))
    return d * np.array(((1.0, nu, 0.0), (nu, 1.0, 0.0), (0.0, 0.0, (1.0 - nu) / 2.0)))


def membrane_matrix(e, nu, t):
    return e * t / (1.0 - nu * nu) * np.array(((1.0, nu, 0.0), (nu, 1.0, 0.0), (0.0, 0.0, (1.0 - nu) / 2.0)))


def _sides(xy):
    """The DKT's side constants P, q, r, t of the sides 23, 31, 12 (k = 4, 5, 6)."""
    out = []
    for i, j in ((1, 2), (2, 0), (0, 1)):
        xij, yij = xy[i, 0] - xy[j, 0], xy[i, 1] - xy[j, 1]
        l2 = xij * xij + yij * yij
        out.append((-6.0 * xij / l2, 3.0 * xij * yij / l2, 3.0 * yij * yij / l2, -6.0 * yij / l2))
    return out


def plate_b(xy, xi, eta):
    """The DKT's curvature matrix (3 × 9) at (ξ, η): κ = (βx,x, βy,y, βx,y + βy,x) of the nodes' (w, θx, θy) — βx =
    −w,x, βy = −w,y."""
    (p4, q4, r4, t4), (p5, q5, r5, t5), (p6, q6, r6, t6) = _sides(xy)
    a, b = 1.0 - 2.0 * xi, 1.0 - 2.0 * eta
    hx_xi = np.array((p6 * a + (p5 - p6) * eta, q6 * a - (q5 + q6) * eta,
                      -4.0 + 6.0 * (xi + eta) + r6 * a - eta * (r5 + r6),
                      -p6 * a + eta * (p4 + p6), q6 * a - eta * (q6 - q4), -2.0 + 6.0 * xi + r6 * a + eta * (r4 - r6),
                      -eta * (p5 + p4), eta * (q4 - q5), -eta * (r5 - r4)))
    hy_xi = np.array((t6 * a + eta * (t5 - t6), 1.0 + r6 * a - eta * (r5 + r6), -q6 * a + eta * (q5 + q6),
                      -t6 * a + eta * (t4 + t6), -1.0 + r6 * a + eta * (r4 - r6), -q6 * a - eta * (q4 - q6),
                      -eta * (t4 + t5), eta * (r4 - r5), -eta * (q4 - q5)))
    hx_eta = np.array((-p5 * b - xi * (p6 - p5), q5 * b - xi * (q5 + q6),
                       -4.0 + 6.0 * (xi + eta) + r5 * b - xi * (r5 + r6),
                       xi * (p4 + p6), xi * (q4 - q6), -xi * (r6 - r4),
                       p5 * b - xi * (p4 + p5), q5 * b + xi * (q4 - q5), -2.0 + 6.0 * eta + r5 * b + xi * (r4 - r5)))
    hy_eta = np.array((-t5 * b - xi * (t6 - t5), 1.0 + r5 * b - xi * (r5 + r6), -q5 * b + xi * (q5 + q6),
                       xi * (t4 + t6), xi * (r4 - r6), -xi * (q4 - q6),
                       t5 * b - xi * (t4 + t5), -1.0 + r5 * b + xi * (r4 - r5), -q5 * b - xi * (q4 - q5)))
    x31, y31 = xy[2, 0] - xy[0, 0], xy[2, 1] - xy[0, 1]
    x12, y12 = xy[0, 0] - xy[1, 0], xy[0, 1] - xy[1, 1]
    two_a = x31 * y12 - x12 * y31
    return np.vstack((y31 * hx_xi + y12 * hx_eta,
                      -x31 * hy_xi - x12 * hy_eta,
                      -x31 * hx_xi - x12 * hx_eta + y31 * hy_xi + y12 * hy_eta)) / two_a


def membrane_b(xy):
    """The constant strain triangle's strain matrix (3 × 6) of the nodes' (u, v)."""
    (x1, y1), (x2, y2), (x3, y3) = xy
    two_a = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
    return np.array(((y2 - y3, 0.0, y3 - y1, 0.0, y1 - y2, 0.0),
                     (0.0, x3 - x2, 0.0, x1 - x3, 0.0, x2 - x1),
                     (x3 - x2, y2 - y3, x1 - x3, y3 - y1, x2 - x1, y1 - y2))) / two_a


def _area(xy):
    (x1, y1), (x2, y2), (x3, y3) = xy
    return 0.5 * ((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))


# the local degrees of freedom of the plate (w, θx, θy) and of the membrane (u, v) in the 18 of the three nodes
PLATE_DOFS = [6 * k + d for k in range(3) for d in (2, 3, 4)]
MEMBRANE_DOFS = [6 * k + d for k in range(3) for d in (0, 1)]
DRILL_DOFS = [6 * k + 5 for k in range(3)]


def local_stiffness(xy, e, nu, t):
    """The triangle's stiffness (18 × 18) in its local axes."""
    if min(e, t) <= 0.0:
        raise ShellError("a shell's property null or negative")
    area = _area(xy)
    if area <= 1e-12:
        raise ShellError("a triangle with no area")
    k = np.zeros((18, 18))
    bm = membrane_b(xy)
    k[np.ix_(MEMBRANE_DOFS, MEMBRANE_DOFS)] = area * bm.T @ membrane_matrix(e, nu, t) @ bm
    db = plate_matrix(e, nu, t)
    kb = np.zeros((9, 9))
    for xi, eta in _POINTS:
        b = plate_b(xy, xi, eta)
        kb += b.T @ db @ b * (area / 3.0)
    k[np.ix_(PLATE_DOFS, PLATE_DOFS)] = kb
    k[DRILL_DOFS, DRILL_DOFS] += DRILL * db[0, 0]
    return k


def transformation(rot):
    t = np.zeros((18, 18))
    for s in range(0, 18, 3):
        t[s:s + 3, s:s + 3] = rot
    return t


def resultants(xy, e, nu, t, u_local):
    """At the triangle's middle, from its nodes' local displacements (18,): (mx, my, mxy) kNm/m sagging positive
    and (nx, ny, nxy) kN/m, tension positive."""
    u = np.asarray(u_local, dtype=float)
    m = -plate_matrix(e, nu, t) @ plate_b(xy, 1.0 / 3.0, 1.0 / 3.0) @ u[PLATE_DOFS]
    n = membrane_matrix(e, nu, t) @ membrane_b(xy) @ u[MEMBRANE_DOFS]
    return np.concatenate((m, n))


def design_moments(mx, my, mxy):
    """Wood–Armer's moments to reinforce for (EC2's slabs: the twisting moment added to each way): ((bottom x,
    bottom y), (top x, top y)) — the bottom's sagging (≥ 0), the top's hogging (≤ 0)."""
    a = abs(mxy)
    return (max(mx + a, 0.0), max(my + a, 0.0)), (min(mx - a, 0.0), min(my - a, 0.0))
