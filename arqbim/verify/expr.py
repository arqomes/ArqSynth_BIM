"""(0.417) A small, safe calculator for the rules' formulas («área útil / 8», «1,2 × Ahab») — and for numbers typed
in a field as sums («3,50+0,15»). Numbers with a comma or a point, + − × ÷ (also * / x), brackets, names given by the
caller, min( ) and max( ). Never Python's eval: only this grammar is read, so a rule file cannot run code."""

import re

_LETTER = "A-Za-z_À-ÖØ-öø-ÿ"          # (accented letters, not × nor ÷)
_TOKEN = re.compile(r"\s*(?:(\d+(?:[.,]\d+)?|[.,]\d+)|([" + _LETTER + r"][0-9" + _LETTER + r"]*)"
                    r"|(\*\*|[-+*/×÷()^;]))")
FUNCTIONS = {"min": min, "max": max, "abs": abs}


class ExprError(ValueError):
    pass


def _tokens(text):
    text = str(text).strip()
    pos, out = 0, []
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if m is None or m.end() == pos:
            if text[pos:].strip() == "":
                break
            raise ExprError("unexpected «{}»".format(text[pos:pos + 8]))
        number, name, op = m.groups()
        if number is not None:
            out.append(("num", float(number.replace(",", "."))))
        elif name is not None:
            after_value = out and (out[-1][0] == "num" or out[-1] == ("op", ")"))
            if after_value and name[0] in "xX":             # («2x1,20»: x is «times» after a number)
                out.append(("op", "*"))
                pos = m.start(2) + 1
                continue
            out.append(("name", name))
        else:
            out.append(("op", {"×": "*", "÷": "/", "^": "**"}.get(op, op)))
        pos = m.end()
    return out


class _Parser:
    def __init__(self, tokens, names):
        self.t, self.k, self.names = tokens, 0, names

    def peek(self):
        return self.t[self.k] if self.k < len(self.t) else (None, None)

    def take(self):
        tok = self.peek()
        self.k += 1
        return tok

    def expr(self):
        value = self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.take()[1]
            right = self.term()
            value = value + right if op == "+" else value - right
        return value

    def term(self):
        value = self.power()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.take()[1]
            right = self.power()
            if op == "/" and right == 0:
                raise ExprError("division by zero")
            value = value * right if op == "*" else value / right
        return value

    def power(self):
        value = self.unary()
        if self.peek() == ("op", "**"):
            self.take()
            value = value ** self.power()
        return value

    def unary(self):
        if self.peek() == ("op", "-"):
            self.take()
            return -self.unary()
        if self.peek() == ("op", "+"):
            self.take()
            return self.unary()
        return self.atom()

    def atom(self):
        kind, value = self.take()
        if kind == "num":
            return value
        if kind == "name":
            if self.peek() == ("op", "("):
                fn = FUNCTIONS.get(value.lower())
                if fn is None:
                    raise ExprError("unknown function «{}»".format(value))
                self.take()
                args = [self.expr()]
                while self.peek() == ("op", ";"):
                    self.take()
                    args.append(self.expr())
                if self.take() != ("op", ")"):
                    raise ExprError("missing «)»")
                return float(fn(args) if len(args) > 1 else fn(args[0]) if fn is abs else fn(args))
            if value not in self.names or self.names[value] is None:
                raise ExprError("unknown «{}»".format(value))
            return float(self.names[value])
        if (kind, value) == ("op", "("):
            inner = self.expr()
            if self.take() != ("op", ")"):
                raise ExprError("missing «)»")
            return inner
        raise ExprError("unexpected end")


def evaluate(text, names=None):
    """The value of `text` («3,50+0,15», «area_util / 8») with the names given; ExprError if it is not one."""
    if isinstance(text, (int, float)):
        return float(text)
    tokens = _tokens(text)
    if not tokens:
        raise ExprError("empty")
    parser = _Parser(tokens, names or {})
    value = parser.expr()
    if parser.k != len(tokens):
        raise ExprError("unexpected «{}»".format(tokens[parser.k][1]))
    return float(value)


def try_evaluate(text, names=None):
    """evaluate(), or None when it is not a formula."""
    try:
        return evaluate(text, names)
    except (ExprError, TypeError, ValueError, OverflowError):
        return None
