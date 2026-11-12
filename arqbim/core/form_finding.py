"""(0.554, PLANO.md «Gerador de formas orgânicas», step 1) Form finding on a grid of points — the shape found, not
modelled: the points held (the outline, masts, supports) stay; the others settle where the forces leave them.

The grid is a Superfície paramétrica's (rows (nr, nc, 3), closed round in u or not). Every point is pulled by its
neighbours along the grid's lines with the same force (a force density, as Linkwitz and Schek's method): alone, the
points settle on a *membrane* — the surface of least tension between the points held, as a soap film; with a load
added the membrane sags or bulges:

- «membrana»  a tensioned membrane (no load): tents, sails, Frei Otto's canopies;
- «almofada»  a pressure square to the surface: a cushion (ETFE, pneumatic roofs) — it bulges and its plan swells;
- «catenaria» its own weight, hung and turned upside down: a shell that only works in compression (Gaudí, Isler);
- «suavizar»  smoothing (Taubin: no shrinking): rounds a shape off, keeps its size.

All in numpy: the points relaxed together, step after step (Jacobi with over-relaxation), until they no longer move.
A load's size does not change the shape of a linear form (membrane and catenary), only its height: the form is found
for a unit load and scaled to the height asked."""

import numpy as np

BEHAVIOURS = ("membrana", "almofada", "catenaria", "suavizar")
MAX_STEPS = 4000
TOL = 1e-7                    # m: a step that moves no point more than this ends the search


class FormError(ValueError):
    pass


def _neighbours(rows, close_u, edge_k=1.0):
    """(sum of each point's neighbours along the grid's lines (nr, nc, 3), how many it has (nr, nc, 1)) — each
    weighed by its line's force density. (0.556) `edge_k`: the grid's edge lines that many times stronger — a free
    edge's cable, pulling its points along it more than the membrane pulls them in."""
    p = np.asarray(rows, dtype=float)
    nr, nc = p.shape[:2]
    s = np.zeros_like(p)
    n = np.zeros((nr, nc, 1))
    wv = np.ones((nr, nc, 1))                            # (the weight of a point's lines along v, along u)
    wu = np.ones((nr, nc, 1))
    if edge_k != 1.0:
        wu[0] = wu[-1] = edge_k                          # (its first and last rows run along u)
        if not close_u:
            wv[:, 0] = wv[:, -1] = edge_k                # (its first and last columns along v)
    s[1:] += p[:-1] * wv[1:]
    n[1:] += wv[1:]
    s[:-1] += p[1:] * wv[:-1]
    n[:-1] += wv[:-1]
    if close_u:
        s += (np.roll(p, 1, axis=1) + np.roll(p, -1, axis=1)) * wu
        n += 2 * wu
    else:
        s[:, 1:] += p[:, :-1] * wu[:, 1:]
        n[:, 1:] += wu[:, 1:]
        s[:, :-1] += p[:, 1:] * wu[:, :-1]
        n[:, :-1] += wu[:, :-1]
    return s, n


def boundary_mask(shape, close_u):
    """The grid's edge points (its first and last rows; its first and last columns where it is open)."""
    nr, nc = shape[:2]
    m = np.zeros((nr, nc), dtype=bool)
    m[0], m[-1] = True, True
    if not close_u:
        m[:, 0], m[:, -1] = True, True
    return m


def _poles(rows):
    """The rows whose points are all one point (a revolved grid's tip): held together."""
    p = np.asarray(rows, dtype=float)
    return [j for j in range(p.shape[0]) if np.all(np.linalg.norm(p[j] - p[j, 0], axis=1) < 1e-9)]


def relax(rows, fixed, close_u=False, load=None, axes=(0, 1, 2), steps=MAX_STEPS, omega=1.8, tol=TOL, edge_k=1.0,
          groups=()):
    """The points not `fixed` (mask (nr, nc)) moved, coordinate by coordinate in `axes`, to where each is the mean
    of its neighbours plus `load` (nr, nc, 3: a push per point, already divided by the force density) — the discrete
    Laplace/Poisson problem, solved by over-relaxed Gauss–Seidel in red-black order (half the points, then the
    other half: each sees its neighbours' new places)."""
    p = np.array(rows, dtype=float)
    free = ~np.asarray(fixed, dtype=bool)
    poles = [j for j in _poles(p) if free[j].any()]       # (a tip: one point — moved as one)
    ax = list(axes)
    jj, ii = np.indices(free.shape)
    colours = [free & ((jj + ii) % 2 == k) for k in (0, 1)]
    groups = [np.asarray(g, bool) & free for g in (groups or ()) if np.asarray(g, bool).any()]
    links = []                                             # (each rigid group's pull from outside it: its links out)
    for g in groups:
        inner, weight = _neighbours(g[..., None].astype(float), close_u, edge_k)
        links.append(max(float((weight - inner)[g].sum()), 1e-9))
        colours = [c & ~g for c in colours]                # (moved as one, below — not point by point)
    for _ in range(int(steps)):
        biggest = 0.0
        for colour in colours:
            s, n = _neighbours(p, close_u, edge_k)
            target = s / n
            if load is not None:
                target = target + load / n
            move = (target - p)[..., ax] * omega
            move[~colour] = 0.0
            p[..., ax] += move
            biggest = max(biggest, float(np.abs(move).max()))
        for j in poles:
            p[j] = p[j].mean(axis=0)
        for g, out in zip(groups, links):                  # (0.557) a rigid ring: moved as one, by the pull of the
            s, n = _neighbours(p, close_u, edge_k)         #  lines from outside it (those inside it cancel out)
            force = s - n * p
            if load is not None:
                force = force + load
            shift = force[g][:, ax].sum(axis=0) / out * omega
            sel = p[g]
            sel[:, ax] += shift
            p[g] = sel
            biggest = max(biggest, float(np.abs(shift).max()))
        if biggest < tol:
            break
    return p


def plan_grid(rows, fixed, close_u=False, edge_k=1.0):
    """The grid's plan relaxed (its points spread evenly between the edge, no lines folded over in a concave
    outline) — z left as it is."""
    return relax(rows, fixed, close_u, axes=(0, 1), edge_k=edge_k)


def _scaled(rows, base, fixed, height, sign=1.0):
    """`rows` whose z off `base` is scaled so that its highest (sign +1) — or lowest (−1) — point is `height` off."""
    dz = (rows[..., 2] - base[..., 2]) * sign
    top = float(dz.max()) if dz.size else 0.0
    if top <= 1e-12:
        return rows
    out = rows.copy()
    out[..., 2] = base[..., 2] + (rows[..., 2] - base[..., 2]) * (abs(height) / top)
    return out


def _areas(rows, close_u):
    """Each point's share of the surface's area (a quarter of the cells round it)."""
    p = np.asarray(rows, dtype=float)
    if close_u:
        p = np.concatenate((p, p[:, :1]), axis=1)
    a, b, c, d = p[:-1, :-1], p[:-1, 1:], p[1:, 1:], p[1:, :-1]
    cell = 0.5 * (np.linalg.norm(np.cross(b - a, d - a), axis=-1) + np.linalg.norm(np.cross(b - c, d - c), axis=-1))
    out = np.zeros(p.shape[:2])
    for dj, di in ((0, 0), (0, 1), (1, 1), (1, 0)):
        out[dj:dj + cell.shape[0], di:di + cell.shape[1]] += cell / 4.0
    if close_u:
        out[:, 0] += out[:, -1]
        out = out[:, :-1]
    return out


def _normals(rows, close_u):
    from .param_surface import grid_normals
    return grid_normals(rows, close_u)


def find(rows, behaviour="membrana", height=2.0, fixed=None, close_u=False, steps=MAX_STEPS, iterations=12,
         plan=True, edge_k=1.0, edge=None, groups=()):
    """The grid's form found (rows (nr, nc, 3) as given: the points held at their place — by default its edge).
    `height`: how high the form rises over the plane of its edge (a negative one: how deep it hangs, for a
    membrane between points held at different heights it is not used). (0.557) `edge`: the points of the edge alone
    (`fixed` then also holds masts, supports, rings inside): the load is the one that lifts the form held by its edge
    alone to `height` — those inside then shape it, as a ring or a support would. Returns the new rows."""
    if behaviour in ("catenaria", "almofada") and edge is not None and \
            ((np.asarray(fixed, bool) & ~np.asarray(edge, bool)).any() or len(groups)):
        return _with_held(rows, behaviour, height, np.asarray(fixed, bool), np.asarray(edge, bool), close_u, steps,
                          iterations, plan, edge_k, groups)
    if behaviour not in BEHAVIOURS:
        raise FormError("comportamento desconhecido: {}".format(behaviour))
    p = np.array(rows, dtype=float)
    if p.ndim != 3 or p.shape[0] < 3 or p.shape[1] < 3:
        raise FormError("a grelha é pequena demais para encontrar a forma")
    fixed = boundary_mask(p.shape, close_u) if fixed is None else np.asarray(fixed, dtype=bool)
    if not fixed.any():
        raise FormError("prenda pelo menos um ponto (o contorno, um apoio)")
    if behaviour == "suavizar":
        return smooth(p, fixed, close_u)
    rings = np.zeros_like(fixed)
    for g in groups:
        rings |= np.asarray(g, bool)
    flat = plan_grid(p, fixed | rings, close_u, edge_k) if plan else p      # (the plan first: evenly spread)
    if behaviour == "membrana":
        # the points held where they are (masts, supports at their heights): the least-tension surface between them
        return relax(flat, fixed, close_u, steps=steps, edge_k=edge_k, groups=groups)
    sign = 1.0 if height >= 0 else -1.0
    # the height: the form's own rise over the plane of its edge (the points held — a ring, a mast, a support — stay
    # where they are)
    base = flat
    if behaviour == "catenaria":
        # its weight — each point's share of the area — hung (and turned: upwards), its plan kept; the weight
        # follows the area as the form deepens (a few rounds)
        form = flat.copy()
        for _ in range(int(iterations)):
            load = np.zeros_like(form)
            load[..., 2] = _areas(form, close_u) * sign
            load[..., 2] *= 1.0 / max(np.mean(np.abs(load[..., 2])), 1e-12) * 1e-3
            new = relax(form, fixed, close_u, load=load, axes=(2,), steps=steps, edge_k=edge_k)
            new = _scaled(new, base, fixed, height, sign)
            if np.abs(new - form).max() < 1e-5:
                form = new
                break
            form = new
        return form
    # almofada: a pressure square to the surface, its plan swelling with it (all three coordinates). Not linear: the
    # pressure itself is sought (a few rounds, each one the last's times the height asked over the height reached)
    up = 1.0 if np.mean(_normals(flat, close_u)[..., 2]) >= 0 else -1.0     # (the grid's normals: up or down)
    pressure = None
    form = flat.copy()
    for k in range(int(iterations)):
        load = _normals(form, close_u) * (_areas(form, close_u) * sign * up)[..., None]
        if pressure is None:                               # (a first guess: as a catenary of that height)
            trial = relax(base, fixed, close_u, load=load * 1e-3, axes=(2,), steps=steps, edge_k=edge_k)
            reach = float(np.abs(trial[..., 2] - base[..., 2]).max())
            pressure = 1e-3 * abs(height) / max(reach, 1e-12)
        new = relax(form, fixed, close_u, load=load * pressure, steps=steps, edge_k=edge_k)
        reach = float(((new[..., 2] - base[..., 2]) * sign).max())
        if reach <= 1e-9:
            raise FormError("a almofada não sobe — veja os pontos presos")
        done = k >= 3 and abs(reach - abs(height)) < 1e-3 * max(abs(height), 1.0)   # (the plan's swell: rounds)
        pressure *= (abs(height) / reach) ** 0.8
        form = new
        if done:
            break
    return _scaled(form, base, fixed, height, sign)


def _with_held(rows, behaviour, height, fixed, edge, close_u, steps, iterations, plan, edge_k, groups=()):
    """(0.557) A catenary or a cushion with points held inside it (masts, supports, an oculus's ring): its load found
    on the form held by its edge alone (the one that rises `height`), then the same load on the form held also by
    them — so a ring set at the form's top leaves the same dome, open there; a support pulls it down to the ground."""
    p = np.array(rows, dtype=float)
    rings = np.zeros_like(fixed)
    for g in groups:
        rings |= np.asarray(g, bool)
    flat = plan_grid(p, fixed | rings, close_u, edge_k) if plan else p     # (a ring keeps its round plan)
    sign = 1.0 if height >= 0 else -1.0
    plain = flat.copy()
    plain[~edge, 2] = 0.0 if not len(flat[edge]) else float(np.mean(flat[edge, 2]))
    if behaviour == "catenaria":                       # (the load that lifts the edge-held form `height`, its weight
        form, alone = flat.copy(), plain.copy()        #  following its area as it deepens — on the form held inside)
        for _ in range(int(iterations)):
            load = np.zeros_like(flat)
            load[..., 2] = _areas(alone, close_u) * sign
            load[..., 2] *= 1e-3 / max(float(np.mean(np.abs(load[..., 2]))), 1e-12)
            trial = relax(plain, edge, close_u, load=load, axes=(2,), steps=steps, edge_k=edge_k)
            reach = float(((trial[..., 2] - plain[..., 2]) * sign).max())
            scale = abs(height) / max(reach, 1e-12)
            alone = plain + (trial - plain) * scale
            new = relax(form, fixed, close_u, load=load * scale, axes=(2,), steps=steps, edge_k=edge_k,
                        groups=groups)
            if np.abs(new - form).max() < 1e-5:
                return new
            form = new
        return form
    alone = find(plain, behaviour, height, edge, close_u, steps, iterations, plan=False, edge_k=edge_k)
    # (the cushion's pressure is the one that lifts it alone: found again here, a few rounds, from its form)
    up = 1.0 if np.mean(_normals(flat, close_u)[..., 2]) >= 0 else -1.0
    unit = _normals(alone, close_u) * (_areas(alone, close_u) * sign * up)[..., None]
    trial = relax(plain, edge, close_u, load=unit * 1e-3, steps=steps, edge_k=edge_k)
    reach = float(((trial[..., 2] - plain[..., 2]) * sign).max())
    target = float(((alone[..., 2] - plain[..., 2]) * sign).max())
    pressure = 1e-3 * target / max(reach, 1e-12)
    form = flat.copy()
    for _ in range(int(iterations)):
        load = _normals(form, close_u) * (_areas(form, close_u) * sign * up)[..., None]
        new = relax(form, fixed, close_u, load=load * pressure, steps=steps, edge_k=edge_k, groups=groups)
        if np.abs(new - form).max() < 1e-5:
            return new
        form = new
    return form


def smooth(rows, fixed=None, close_u=False, rounds=20, lam=0.5, mu=-0.53):
    """Taubin's smoothing — a shrinking step (λ) then a swelling one (μ), in turn — the points held kept: rounds a
    form off without making it smaller."""
    p = np.array(rows, dtype=float)
    fixed = boundary_mask(p.shape, close_u) if fixed is None else np.asarray(fixed, dtype=bool)
    free = ~fixed
    for _ in range(int(rounds)):
        for f in (lam, mu):
            s, n = _neighbours(p, close_u)
            move = (s / n - p) * f
            move[~free] = 0.0
            p += move
    return p


def surface_area(rows, close_u=False):
    return float(_areas(rows, close_u).sum())
