"""(0.501) Cutting the pieces out of stock bars — DetailCraft's nest: first fit, longest piece first, into bars of the
stock length (12 m, or 6 m), each cut losing the saw's width; what is left of a bar 500 mm or more counted as an
offcut to use again, the rest as waste. Pure Python."""

STOCK = 12000.0                 # mm
KERF = 3.0                      # mm, the saw's cut
USEFUL = 500.0                  # mm: an offcut this long is kept


def plan(pieces, stock=STOCK, kerf=KERF):
    """pieces: [(mark, length mm)] of one section — the bars to buy: [{"pieces": [(mark, length)], "used": mm,
    "left": mm}] (a piece longer than a bar: a bar of its own, longer, said by its "left" < 0)."""
    bars = []
    for mark, length in sorted(pieces, key=lambda p: -p[1]):
        for bar in bars:
            need = length + (kerf if bar["pieces"] else 0.0)
            if bar["left"] >= need:
                bar["pieces"].append((mark, length))
                bar["used"] += need
                bar["left"] -= need
                break
        else:
            bars.append({"pieces": [(mark, length)], "used": length, "left": stock - length})
    return bars


def summary(bars, stock=STOCK):
    """(bars, metres bought, metres of pieces, waste %, offcuts kept (≥ USEFUL) [mm])."""
    bought = len(bars) * stock / 1000.0
    used = sum(length for bar in bars for _m, length in bar["pieces"]) / 1000.0
    offcuts = [bar["left"] for bar in bars if bar["left"] >= USEFUL]
    waste = sum(bar["left"] for bar in bars if 0 <= bar["left"] < USEFUL) + \
        sum(kerf_lost for kerf_lost in (bar["used"] - sum(l for _m, l in bar["pieces"]) for bar in bars))
    return len(bars), bought, used, (100.0 * waste / 1000.0 / bought) if bought else 0.0, offcuts
