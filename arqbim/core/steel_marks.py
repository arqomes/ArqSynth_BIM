"""(0.500) Part marks of the steel pieces — DetailCraft's rule (one mark for pieces that are the same: section, grade,
cut length to the millimetre, how their ends are cut and coped) with a prefix by what the piece is, as the drawings
in Portugal write them (P pilar, V viga, CV contraventamento, M madre, E elemento, Ch chapa) — and, better than
DetailCraft's, kept: a piece keeps the mark it has while it stays the same as the others of that mark; a new piece, or
one that changed, gets the first number free of its prefix. Pure Python."""

import re

PREFIXES = ("P", "V", "CV", "M", "E", "Ch")


def _natural(text):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", str(text or ""))]


def assign(pieces):
    """pieces: [(id, prefix, signature, its mark now or "")] — the marks to give: {id: mark}. The pieces of one
    signature share a mark: the one most of them have (that no piece of another signature has), else the first number
    free of their prefix (the groups taken by prefix, then by signature: the bigger sections and longer pieces
    first, as the signature sorts)."""
    groups = {}
    for pid, prefix, sig, mark in pieces:
        groups.setdefault((prefix, sig), []).append((pid, mark or ""))
    owners = {}                                          # (a mark: the groups that use it)
    for key, members in groups.items():
        for _pid, mark in members:
            if mark:
                owners.setdefault(mark, set()).add(key)
    out, taken = {}, set()
    pending = []
    for key in sorted(groups, key=lambda k: (PREFIXES.index(k[0]) if k[0] in PREFIXES else 99, k[1])):
        prefix = key[0]
        members = groups[key]
        votes = {}
        for _pid, mark in members:
            if mark and mark.startswith(prefix) and _number(mark, prefix) is not None and owners[mark] == {key} \
                    and mark not in taken:
                votes[mark] = votes.get(mark, 0) + 1
        if votes:
            mark = max(votes, key=lambda m: (votes[m], [-v if isinstance(v, int) else 0 for v in _natural(m)]))
            taken.add(mark)
            for pid, _m in members:
                out[pid] = mark
        else:
            pending.append(key)
    for key in pending:
        prefix = key[0]
        n = 1
        while "{}{}".format(prefix, n) in taken:
            n += 1
        mark = "{}{}".format(prefix, n)
        taken.add(mark)
        for pid, _m in groups[key]:
            out[pid] = mark
    return out


def _turned(cuts, copes, ext, variant):
    """A piece's cuts, copes and drawing out as they would be with it turned: 0 as it is, 1 turned half round its
    own axis (x, y → −x, −y), 2 end for end (x, z → −x, −z; its ends swapped), 3 both."""
    flip_x = -1.0 if variant in (1, 2) else 1.0
    flip_y = -1.0 if variant in (1, 3) else 1.0
    swap = variant in (2, 3)
    flip_z = -1.0 if swap else 1.0

    def p(v):
        return (round(v[0] * flip_x, 3) + 0.0, round(v[1] * flip_y, 3) + 0.0, round(v[2] * flip_z, 3) + 0.0)

    out_cuts = tuple(sorted(((1 - c.get("end", 0)) if swap else c.get("end", 0), p(c["p"]), p(c["n"])) for c in cuts))
    out_copes = []
    for c in copes:
        a, b = p(c["lo"]), p(c["hi"])
        lo = tuple(min(a[k], b[k]) for k in range(3))
        hi = tuple(max(a[k], b[k]) for k in range(3))
        out_copes.append(((1 - c.get("end", 0)) if swap else c.get("end", 0), lo, hi))
    e0, e1 = ext
    return out_cuts, tuple(sorted(out_copes)), (round(e1, 4), round(e0, 4)) if swap else (round(e0, 4), round(e1, 4))


def shape_signature(cuts, copes, ext, symmetric):
    """How a piece's ends are cut, the same for two pieces that are one turned (DetailCraft's turnover: a symmetric
    section — an I, a tube — any of the four ways; another only as it is)."""
    variants = (0, 1, 2, 3) if symmetric else (0,)
    return min(_turned(cuts, copes, ext, v) for v in variants)


def holes_signature(holes, length, width):
    """(0.512) A piece's holes as its mark sees them — [(face, x, y, d0, …)] mm — to the millimetre, the same for the
    piece turned end for end (x → its length − x; a flange's y → its width − y): the smaller of the two."""
    def ways(flip):
        out = []
        for face, x, y, d, *_rest in holes:
            if flip:
                x = length - x
                y = width - y if face in ("o", "u") else y
            out.append((face, int(round(x)), int(round(y)), int(round(d))))
        return tuple(sorted(out))
    return min(ways(False), ways(True)) if holes else ()


def _number(mark, prefix):
    rest = mark[len(prefix):]
    return int(rest) if rest.isdigit() else None


def sort_key(mark):
    """Marks in order: by their prefix's place, then by number."""
    prefix = next((p for p in sorted(PREFIXES, key=len, reverse=True) if str(mark).startswith(p)), "")
    return (PREFIXES.index(prefix) if prefix in PREFIXES else 99, _natural(mark))
