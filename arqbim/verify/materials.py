"""(0.422) What a material is, for the rules on materials: its families, found from its name («Placa de gesso
cartonado hidrófugo 12,5 mm» → gypsum board, water-resistant). Words in Portuguese and English; accents and case
ignored. A material can be in several families (a «betão leve com EPS»)."""

import functools
import unicodedata

FAMILY_WORDS = {
    "gesso_cartonado": ("gesso cartonado", "placa de gesso", "pladur", "drywall", "plasterboard", "gypsum board",
                        "gyproc", "knauf"),
    "hidrofugo": ("hidrofug", "hidro-fug", "h1", "verde", "anti-humidade", "antihumidade", "moisture", "water resist",
                  "wr "),
    "aluminio": ("alumin",),
    "cobre": ("cobre", "copper"),
    "zinco": ("zinco", "zinc", "titanzinc"),
    "aco_galvanizado": ("galvaniz",),
    "aco": ("aco ", "aço", "steel", "inox"),
    "poliestireno": ("eps", "xps", "poliestireno", "polystyrene", "roofmate", "styrofoam", "wallmate"),
    "betume": ("betum", "bitum", "asfalt", "asphalt", "tela asf", "membrana betum"),
    "membrana": ("membrana", "barreira", "pvc", "polietileno", "polyethylene", "tela", "impermeabiliz", "geomembrana",
                 "dpc", "dpm", "betum", "bitum", "epdm"),
    "argamassa_cimento": ("cimento", "cement", "reboco", "render", "betonilha", "screed"),
    "cal": ("argamassa de cal", "reboco de cal", "cal hidraulica", "cal aerea", "lime"),
    "alvenaria_antiga": ("pedra", "granito", "calcario", "xisto", "taipa", "adobe", "stone", "rubble"),
    "alvenaria": ("tijolo", "bloco", "brick", "block", "alvenaria", "masonry", "pedra", "stone", "taipa", "adobe"),
    "madeira": ("madeira", "wood", "soalho", "parquet", "pinho", "carvalho", "osb", "contraplacado", "timber",
                "flutuante", "laminado"),
    "alcatifa": ("alcatifa", "carpet", "moquete"),
    "isolante": ("isolamento", "insulation", "la de rocha", "la mineral", "la de vidro", "cortica", "eps", "xps",
                 "poliuretano", "pur", "pir", "wool"),
}


def plain(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    return " {} ".format(text.lower())


_WORDS = None


def _words():
    """The family words made plain once: [(family, [(word, whole only)])]."""
    global _WORDS
    if _WORDS is None:
        _WORDS = [(family, [(plain(w).strip(), len(plain(w).strip()) <= 3) for w in words])
                  for family, words in FAMILY_WORDS.items()]
    return _WORDS


@functools.lru_cache(maxsize=4096)
def families(name):
    """The families a material's name says: {"gesso_cartonado", "hidrofugo", …} (a frozenset; one name read once)."""
    return frozenset(_families(name))


def _families(name):
    text = plain(name)
    out = set()
    for family, words in _words():
        for w, whole in words:                          # (short words — «eps», «aço», «h1» — only whole)
            if (whole and (" " + w + " ") in text) or (not whole and w in text):
                out.add(family)
                break
    if "cal" in out and "argamassa_cimento" in out and "cimento" not in text:
        out.discard("argamassa_cimento")                # («reboco de cal» is lime, not cement)
    return out


# pairs of families that harm each other in contact: (a, b, the topic, why)
GALVANIC = (("aluminio", "cobre"), ("zinco", "cobre"), ("aco_galvanizado", "cobre"), ("aluminio", "aco"))


def galvanic(a, b):
    """Whether two materials' families corrode each other in contact (galvanic pairs)."""
    for x, y in GALVANIC:
        if (x in a and y in b) or (y in a and x in b):
            return True
    return False


def eps_bitumen(a, b):
    return ("poliestireno" in a and "betume" in b) or ("poliestireno" in b and "betume" in a)


def cement_on_lime(a, b):
    """Cement mortar against old masonry or lime: it holds the damp in and cracks off (rehabilitation)."""
    cement = lambda f: "argamassa_cimento" in f and "cal" not in f            # noqa: E731
    old = lambda f: "alvenaria_antiga" in f or "cal" in f                      # noqa: E731
    return (cement(a) and old(b)) or (cement(b) and old(a))
