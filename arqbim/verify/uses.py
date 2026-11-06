"""(0.416) What a room is for — its use — as the rules ask for it: a bedroom, the living room, the kitchen, a bathroom,
a corridor…

Found from the room's name («Quarto 2», «Sala comum», «WC») and from what is inside it (a toilet: a bathroom; a sink and
a hob: a kitchen; a bed: a bedroom), or chosen by the architect (it is then kept in the IFC and never guessed again).
The use is written to the room's IfcSpace.ObjectType (its name in the project's language), which other programs read.
"""

import unicodedata

# key -> (Portuguese name, English name, habitable, a bedroom (counts in Tn), wet, common to the building, exterior)
USES = {
    "sala": ("Sala", "Living room", True, False, False, False, False),
    "quarto": ("Quarto", "Bedroom", True, True, False, False, False),
    "cozinha": ("Cozinha", "Kitchen", True, False, True, False, False),
    "sala_cozinha": ("Sala e cozinha", "Living room and kitchen", True, False, True, False, False),
    "refeicoes": ("Sala de refeições", "Dining room", True, False, False, False, False),
    "escritorio": ("Escritório", "Study", True, False, False, False, False),
    "instalacao_sanitaria": ("Instalação sanitária", "Bathroom", False, False, True, False, False),
    "tratamento_roupa": ("Tratamento de roupa", "Laundry", False, False, True, False, False),
    "corredor": ("Corredor", "Corridor", False, False, False, False, False),
    "vestibulo": ("Vestíbulo", "Entrance hall", False, False, False, False, False),
    "arrumos": ("Arrumos", "Storage", False, False, False, False, False),
    "varanda": ("Varanda", "Balcony", False, False, False, False, True),
    "garagem": ("Garagem", "Garage", False, False, False, False, False),
    "comum": ("Espaço comum", "Common area", False, False, False, True, False),
    "comercio": ("Comércio", "Shop", False, False, False, False, False),
    "servicos": ("Serviços", "Office", False, False, False, False, False),
    "outro": ("Outro", "Other", False, False, False, False, False),
}
ORDER = tuple(USES)

# words in a room's name -> its use (the first that matches; accents and case ignored). Longer phrases first, so that
# «sala de jantar» is a dining room and not a living room, «quarto de banho» a bathroom and not a bedroom.
NAME_WORDS = (
    ("instalacao_sanitaria", ("instalacao sanitaria", "inst. sanitaria", "inst sanitaria", "casa de banho",
                              "quarto de banho", "banheiro", "lavabo", "w.c", "wc", "i.s.", "i.s", "is ",
                              "bathroom", "toilet", "restroom", "ensuite", "en-suite")),
    ("sala_cozinha", ("sala/cozinha", "sala e cozinha", "sala-cozinha", "kitchenette", "cozinha americana",
                      "open space", "kitchen-living", "living/kitchen")),
    ("refeicoes", ("sala de jantar", "sala de refeicoes", "refeicoes", "jantar", "dining")),
    ("tratamento_roupa", ("tratamento de roupa", "lavandaria", "lavanderia", "area de servico", "laundry",
                          "utility")),
    ("comum", ("atrio comum", "hall do predio", "hall comum", "patamar", "caixa de escada", "escada comum",
               "zona comum", "espaco comum", "parte comum", "common", "lobby", "stairwell")),
    ("cozinha", ("cozinha", "copa", "kitchen")),
    ("quarto", ("quarto", "suite", "dormitorio", "bedroom", "bed room")),
    ("escritorio", ("escritorio", "estudio", "biblioteca", "office", "study")),
    ("sala", ("sala", "estar", "living", "lounge")),
    ("corredor", ("corredor", "circulacao", "passagem", "corridor", "hallway")),
    ("vestibulo", ("vestibulo", "hall", "entrada", "atrio", "foyer", "entrance")),
    ("arrumos", ("arrumos", "arrumo", "arrecadacao", "despensa", "closet", "rouparia", "storage", "pantry")),
    ("varanda", ("varanda", "terraco", "alpendre", "balcony", "terrace", "porch")),
    ("garagem", ("garagem", "estacionamento", "garage", "parking")),
    ("comercio", ("loja", "comercio", "shop", "store")),
)


def _plain(text):
    """Lower case, without accents: «Instalação Sanitária» -> «instalacao sanitaria»."""
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    return " {} ".format(text.lower().strip())


def label(key, language="pt"):
    """A use's name in the language («Quarto»), "" for none."""
    entry = USES.get(key)
    return "" if entry is None else (entry[0] if language == "pt" else entry[1])


def from_label(text):
    """The use whose name (in either language) is `text` — as written to IfcSpace.ObjectType —, or None."""
    plain = _plain(text).strip()
    for key, entry in USES.items():
        if plain in (_plain(entry[0]).strip(), _plain(entry[1]).strip()):
            return key
    return None


def from_name(name):
    """The use a room's name says, or None. Short words («wc», «is») only as whole words; longer ones anywhere
    («Quartos», «Salinha»)."""
    text = _plain(name)
    for key, words in NAME_WORDS:
        for word in words:
            w = word.strip()
            if (" " + w + " ") in text or (len(w) > 3 and w in text):
                return key
    return None


# what is inside -> the use it says. contents: {kind: count}, kind = "toilet" | "shower" | "bath" | "basin" | "sink"
# | "cooker" | "washer" | "bed" | "double_bed" | "kitchen_cabinet" | "sofa" | "car" …
def from_contents(contents):
    """The use the fittings and furniture inside a room say, or None: a toilet, a shower or a bath -> a bathroom; a
    kitchen sink, a hob or kitchen cabinets -> a kitchen (with a sofa: the living room and kitchen); a washing
    machine alone -> the laundry; a bed -> a bedroom."""
    c = contents or {}
    if c.get("toilet") or c.get("shower") or c.get("bath"):
        return "instalacao_sanitaria"
    if c.get("sink") or c.get("cooker") or c.get("kitchen_cabinet"):
        return "sala_cozinha" if c.get("sofa") or c.get("bed") else "cozinha"
    if c.get("bed") or c.get("double_bed"):
        return "quarto"
    if c.get("washer"):
        return "tratamento_roupa"
    if c.get("basin"):
        return "instalacao_sanitaria"
    if c.get("sofa"):
        return "sala"
    return None


def deduce(name, contents=None, external=False, chosen=None):
    """(use key, why) of a room: chosen by the architect ("chosen"), else what is inside it says ("contents"), else
    its name ("name"), else an exterior room is a balcony and any other "outro" ("none"). The contents win over the
    name when they disagree on a wet room (a «Quarto» with a toilet is a bathroom) — never the other way: a «Sala»
    with a sofa is still a living room."""
    if chosen in USES:
        return chosen, "chosen"
    by_name = from_name(name)
    by_contents = from_contents(contents)
    if by_contents is None:
        return (by_name, "name") if by_name is not None else (("varanda" if external else "outro"), "none")
    if by_name is None or by_name == by_contents:
        return by_contents, ("contents" if by_name is None else "name")
    if by_name in ("sala", "refeicoes") and by_contents == "cozinha":
        return "sala_cozinha", "contents"                # (a «Sala» with the kitchen in it)
    if is_wet(by_contents) and not is_wet(by_name):
        return by_contents, "contents"                   # (a «Quarto» with a toilet is a bathroom)
    return by_name, "name"


def is_bedroom(key):
    return bool(USES.get(key, USES["outro"])[3])


def is_habitable(key):
    return bool(USES.get(key, USES["outro"])[2])


def is_wet(key):
    return bool(USES.get(key, USES["outro"])[4])


def is_common(key):
    return bool(USES.get(key, USES["outro"])[5])
