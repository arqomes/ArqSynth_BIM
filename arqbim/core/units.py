"""Parsing and formatting of lengths typed by the user (SketchUp-style VCB).

Pure Python: no Blender imports, so it can be unit-tested anywhere.

Accepted input (case-insensitive, spaces ignored):
    3.20   3,20   -0,5   320cm   3200mm   3.2m
Two values (rectangle): separated by ';' or 'x'  ->  3,20;4,50   3.2x4.5
If there is no ';' or 'x' and the text has both '.' and a single ',',
the comma is taken as separator:  3.2,4.5
A missing value keeps the current mouse value:  ;4,50   3,20;
A number without a unit is in the display unit (0.186, the footer's Units: metres unless chosen otherwise).
"""

import re

_UNIT_FACTORS = {"mm": 0.001, "cm": 0.01, "m": 1.0}
_VALUE_RE = re.compile(r"^([+-]?)(\d+(?:[.,]\d*)?|[.,]\d+)(mm|cm|m)?$")

LENGTH_UNITS = ("m", "cm", "mm")
_display = {"unit": "m"}


def set_display_unit(unit):
    """(0.186) The unit lengths are shown in, and a bare typed number is read in: "m", "cm" or "mm" (anything
    else: "m")."""
    _display["unit"] = unit if unit in LENGTH_UNITS else "m"


def display_unit():
    return _display["unit"]


def parse_length(text, unit=None):
    """Return the length in meters, or None if `text` is not a valid length. A bare number is in `unit` (None:
    the display unit). (0.430) A sum is worked out — 3,50+0,15   2*1,20   (4-0,2)/2   3m+15cm   2×1,20 — each
    number in its unit or the display one, the result in the display one (as a person reckons on paper)."""
    t = text.strip().lower().replace(" ", "")
    base = unit or _display["unit"]
    m = _VALUE_RE.match(t)
    if not m:
        value = _reckon(t, base)
        return value * _UNIT_FACTORS[base] if value is not None else None
    sign, number, typed = m.groups()
    value = float(number.replace(",", "."))
    if sign == "-":
        value = -value
    return value * _UNIT_FACTORS[typed or base]


_TOKEN_RE = re.compile(r"(\d+(?:[.,]\d*)?|[.,]\d+)(mm|cm|m)?|([-+*/×÷()])")


def _reckon(text, base):
    """(0.430) A sum of lengths in the unit `base` (each number with a unit turned into it), or None: + − × ÷ and
    brackets, nothing else (not code: a small reckoner)."""
    if not text or not any(c in text for c in "+-*/×÷()"):
        return None
    tokens, pos = [], 0
    while pos < len(text):
        m = _TOKEN_RE.match(text, pos)
        if m is None:
            return None
        number, typed, op = m.groups()
        if number is not None:
            value = float(number.replace(",", "."))
            if typed:
                value = value * _UNIT_FACTORS[typed] / _UNIT_FACTORS[base]
            tokens.append(("n", value))
        else:
            tokens.append(("o", {"×": "*", "÷": "/"}.get(op, op)))
        pos = m.end()
    tokens.append(("end", None))
    at = [0]

    def peek():
        return tokens[at[0]]

    def take():
        at[0] += 1
        return tokens[at[0] - 1]

    def expr():
        value = term()
        while peek() in (("o", "+"), ("o", "-")):
            op = take()[1]
            right = term()
            value = value + right if op == "+" else value - right
        return value

    def term():
        value = unary()
        while peek() in (("o", "*"), ("o", "/")):
            op = take()[1]
            right = unary()
            if op == "/" and abs(right) < 1e-12:
                raise ValueError("division by zero")
            value = value * right if op == "*" else value / right
        return value

    def unary():
        sign = 1.0
        if peek() in (("o", "-"), ("o", "+")):              # (one sign — «--1» is a slip of the finger, not a sum)
            sign = -1.0 if take()[1] == "-" else 1.0
        kind, value = take()
        if kind == "n":
            return sign * value
        if (kind, value) == ("o", "("):
            inside = expr()
            if take() != ("o", ")"):
                raise ValueError("bracket")
            return sign * inside
        raise ValueError("token")

    try:
        value = expr()
        if peek()[0] != "end":
            return None
        return float(value)
    except (ValueError, IndexError):
        return None


def split_values(text):
    t = text.strip().lower().replace(" ", "")
    if ";" in t:
        return t.split(";")
    if "x" in t:
        return t.split("x")
    if t.count(",") == 1 and "." in t:
        return t.split(",")
    return [t]


def parse_lengths(text, count):
    """Parse up to `count` lengths.

    Returns a list of `count` items (meters or None for "keep current"),
    or None if the text is invalid.
    """
    parts = split_values(text)
    if not parts or len(parts) > count:
        return None
    values = []
    for p in parts:
        if p == "":
            values.append(None)
            continue
        v = parse_length(p)
        if v is None:
            return None
        values.append(v)
    if all(v is None for v in values):
        return None
    values += [None] * (count - len(values))
    return values


_ANGLE_RE = re.compile(r"^([+-]?)(\d+(?:[.,]\d*)?|[.,]\d+)(°|º|deg|graus)?$")


def parse_angle(text):
    """Degrees typed by the user: 45   -30   22,5   90°  -> float, or None if invalid."""
    m = _ANGLE_RE.match(text.strip().lower().replace(" ", ""))
    if not m:
        return None
    sign, number, _unit = m.groups()
    value = float(number.replace(",", "."))
    return -value if sign == "-" else value


_ARRAY_RE = re.compile(r"^(?:[x*](\d+)|(\d+)[x*]|/(\d+))$")


def parse_array(text):
    """A series of copies typed after copying (SketchUp): "3x", "x3" or "*3" -> ("times", 3):
    three copies at the same spacing; "/3" -> ("divide", 3): the distance split in three.
    None if `text` is not that."""
    m = _ARRAY_RE.match(text.strip().lower().replace(" ", ""))
    if not m:
        return None
    times = m.group(1) or m.group(2)
    n = int(times or m.group(3))
    if n < 1 or n > 500:
        return None
    return ("times" if times else "divide"), n


def format_angle(degrees, decimal_sep=","):
    return "{:.1f}°".format(degrees).replace(".", decimal_sep).replace("-0,0°", "0,0°").replace("-0.0°", "0.0°")


def format_slope(slope, decimal_sep=","):
    """0.015 -> '1,5 %': a pipe's fall (0.136), as written on a drawing."""
    return "{:g} %".format(round(100.0 * float(slope), 2)).replace(".", decimal_sep)


def format_length(meters, decimal_sep=",", decimals=2, unit=None):
    """3.2 -> '3,20 m'. Values not exact at this precision get SketchUp's '~':
    3.4871 -> '~ 3,49 m'. In `unit` (None: the display unit, 0.186): centimetres with a decimal fewer
    ('320,0 cm', to the millimetre), millimetres whole ('3200 mm')."""
    unit = unit or _display["unit"]
    value = meters / _UNIT_FACTORS[unit]
    places = {"m": decimals, "cm": max(decimals - 1, 0), "mm": max(decimals - 3, 0)}[unit]
    scaled = value * 10 ** places
    approx = abs(scaled - round(scaled)) > 1e-6
    s = "{:.{}f}".format(value, places)
    if s.startswith("-") and float(s) == 0.0:
        s = s[1:]
    return ("~ " if approx else "") + s.replace(".", decimal_sep) + " " + unit
