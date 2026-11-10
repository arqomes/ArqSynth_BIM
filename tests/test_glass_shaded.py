"""(0.533) Glass seen through in the usual 3D style («Sombreado»), from the very start (not only after picking another
style and coming back)."""

import re

from arqbim.model import view_styles


def test_shaded_shows_glass_through():
    assert view_styles.BUILTIN["shaded"].transparency
    assert view_styles.BUILTIN[view_styles.DEFAULT].transparency


def test_viewport_starts_with_its_style_dressing():
    import pathlib
    src = pathlib.Path(__file__).parents[1].joinpath("arqbim", "render", "viewport.py").read_text(encoding="utf-8")
    start = re.search(r"self\._dressing = (.+)", src).group(1)
    assert "self.vstyle.transparency" in start       # not a fixed («category», False, False)
