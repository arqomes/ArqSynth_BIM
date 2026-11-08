"""(0.475, the owner: «Criar regras para alertar sobre zonas conflitantes. Por exemplo, se uma casa de banho ficar
diretamente dentro da cozinha, acende a alerta no rodapé… Na criação de lista deve ter o uso ou categoria… criar regra
para habitação, hospital, clínica, escola, comercial, armazém de venda, minimercados, supermercados, restaurante,
bancos, polícia, etc») The programme's building types, the uses (categories) of its rooms, and the zones that must not
open straight into each other in each type of building: two rooms joined by a door whose uses are such a pair are a
conflict — the Verifier's «Zonas conflitantes» warning (in the footer; verify/model_checks.py) and both rooms red in the
Programme panel.

A room's use: the one its programme line gave it (the room keeps it: «UsoPrograma»), else the Verifier's (from its name
and what is in it — verify/uses.py), turned into one of these. The pairs are good practice (hygiene, safety, privacy),
not a law — the Verifier says them as warnings, and one accepted (Exceção…) keeps its note."""

import unicodedata

# building type -> (Portuguese, English)
BUILDING_TYPES = {
    "habitacao": ("Habitação", "Housing"),
    "hospital": ("Hospital", "Hospital"),
    "clinica": ("Clínica / centro de saúde", "Clinic / health centre"),
    "escola": ("Escola", "School"),
    "creche": ("Creche / jardim de infância", "Nursery / kindergarten"),
    "lar": ("Lar de idosos", "Care home"),
    "escritorios": ("Escritórios", "Offices"),
    "comercio": ("Comércio (loja)", "Shop"),
    "armazem_venda": ("Armazém de venda", "Warehouse store"),
    "minimercado": ("Minimercado", "Convenience store"),
    "supermercado": ("Supermercado", "Supermarket"),
    "restaurante": ("Restaurante / café", "Restaurant / café"),
    "hotel": ("Hotel", "Hotel"),
    "farmacia": ("Farmácia", "Pharmacy"),
    "banco": ("Banco / agência", "Bank branch"),
    "policia": ("Esquadra de polícia", "Police station"),
}

# use -> (Portuguese, English, the Verifier's use it is — verify/uses.USES — or None, the building types it is
# offered for: () = every one)
_ALL = ()
_HEALTH = ("hospital", "clinica", "lar")
_FOOD_SHOPS = ("minimercado", "supermercado", "armazem_venda", "comercio")
USES = {
    "estar": ("Sala de estar", "Living room", "sala", ("habitacao", "lar", "hotel")),
    "quarto": ("Quarto", "Bedroom", "quarto", ("habitacao", "lar", "hotel", "creche")),
    "cozinha": ("Cozinha", "Kitchen", "cozinha", _ALL),
    "copa": ("Copa (do pessoal)", "Staff pantry", "cozinha", _ALL),
    "refeicoes": ("Sala de refeições / refeitório", "Dining room", "refeicoes", _ALL),
    "sanitario": ("Instalação sanitária", "Toilet / bathroom", "instalacao_sanitaria", _ALL),
    "lavandaria": ("Lavandaria / tratamento de roupa", "Laundry", "tratamento_roupa", _ALL),
    "entrada": ("Entrada / átrio / receção", "Entrance / lobby", "vestibulo", _ALL),
    "circulacao": ("Circulação / corredor", "Corridor", "corredor", _ALL),
    "escada": ("Escada / elevador", "Stair / lift", "comum", _ALL),
    "arrumos": ("Arrumos / despensa", "Storage", "arrumos", _ALL),
    "garagem": ("Garagem / estacionamento", "Garage / parking", "garagem", _ALL),
    "exterior": ("Exterior (varanda, terraço, pátio)", "Outside (balcony, terrace, yard)", "varanda", _ALL),
    "escritorio": ("Escritório / gabinete", "Office", "escritorio", _ALL),
    "reunioes": ("Sala de reuniões", "Meeting room", "servicos", _ALL),
    "atendimento": ("Atendimento / sala de espera", "Public counter / waiting room", "servicos", _ALL),
    "vestiario": ("Vestiário do pessoal", "Staff changing room", None, _ALL),
    "tecnica": ("Área técnica (quadros, AVAC)", "Plant room", None, _ALL),
    "lixo": ("Lixos / resíduos", "Refuse store", None, _ALL),
    # health
    "consulta": ("Gabinete de consulta", "Consulting room", "servicos", _HEALTH),
    "tratamento": ("Sala de tratamentos / enfermagem", "Treatment room", "servicos", _HEALTH),
    "internamento": ("Quarto de internamento", "Ward", "quarto", ("hospital",)),
    "isolamento": ("Quarto de isolamento", "Isolation room", "quarto", ("hospital",)),
    "bloco_operatorio": ("Bloco operatório", "Operating theatre", "servicos", ("hospital",)),
    "esterilizacao": ("Esterilização (zona limpa)", "Sterilisation (clean)", "servicos", _HEALTH),
    "sujos": ("Sujos / despejos", "Dirty utility / sluice", None, _HEALTH),
    "urgencia": ("Urgência", "Emergency", "servicos", ("hospital",)),
    "laboratorio": ("Laboratório", "Laboratory", "servicos", ("hospital", "clinica", "escola")),
    "imagiologia": ("Imagiologia (raio-X)", "Imaging (X-ray)", "servicos", ("hospital", "clinica")),
    "morgue": ("Morgue", "Mortuary", None, ("hospital",)),
    "farmacia": ("Farmácia / medicamentos", "Pharmacy / medicines", "comercio", ("hospital", "clinica", "farmacia",
                                                                              "lar")),
    # schools
    "sala_aula": ("Sala de aula / atividades", "Classroom", "servicos", ("escola", "creche")),
    "ginasio": ("Ginásio / polidesportivo", "Gym / sports hall", "servicos", ("escola",)),
    "biblioteca": ("Biblioteca", "Library", "escritorio", ("escola",)),
    "recreio": ("Recreio", "Playground", "patio", ("escola", "creche")),
    # shops, restaurants
    "loja": ("Área de venda / loja", "Sales floor", "comercio", _FOOD_SHOPS + ("farmacia",)),
    "caixas": ("Caixas", "Checkouts", "comercio", _FOOD_SHOPS),
    "talho": ("Talho / peixaria (preparação)", "Butcher / fishmonger", "comercio", _FOOD_SHOPS),
    "padaria": ("Padaria / pastelaria", "Bakery", "comercio", _FOOD_SHOPS + ("restaurante",)),
    "camara_frigorifica": ("Câmara frigorífica", "Cold room", "arrumos", _FOOD_SHOPS + ("restaurante", "hospital")),
    "armazem": ("Armazém (mercadoria)", "Stockroom", "arrumos", _FOOD_SHOPS + ("restaurante", "farmacia")),
    "cargas": ("Cargas e descargas", "Loading bay", None, _FOOD_SHOPS + ("restaurante", "hospital")),
    "copa_suja": ("Copa suja (lavagem de loiça)", "Dishwashing", "cozinha", ("restaurante", "hotel", "escola",
                                                                            "hospital", "lar")),
    # banks, police
    "cofre": ("Cofre / casa-forte", "Vault", None, ("banco",)),
    "tesouraria": ("Tesouraria", "Treasury", "servicos", ("banco",)),
    "atm": ("Multibanco (ATM)", "Cash machines", "servicos", ("banco",)),
    "celas": ("Celas / detenção", "Cells", None, ("policia",)),
    "armeiro": ("Armeiro / sala de armas", "Armoury", None, ("policia",)),
    "interrogatorio": ("Sala de interrogatório", "Interview room", "servicos", ("policia",)),
    "camarata": ("Camarata", "Dormitory", "quarto", ("policia",)),
    "outro": ("Outro", "Other", "outro", _ALL),
}

# the Verifier's use -> this programme's (a room not placed from the programme)
FROM_VERIFIER = {"sala": "estar", "quarto": "quarto", "cozinha": "cozinha", "sala_cozinha": "cozinha",
                 "refeicoes": "refeicoes", "escritorio": "escritorio", "instalacao_sanitaria": "sanitario",
                 "tratamento_roupa": "lavandaria", "corredor": "circulacao", "vestibulo": "entrada",
                 "arrumos": "arrumos", "varanda": "exterior", "patio": "exterior", "garagem": "garagem",
                 "comum": "escada", "comercio": "loja", "servicos": "escritorio", "outro": "outro"}

# the pairs that must not open straight into each other (a door between them): (use, use, why) — those of every
# building, and each type's own
_EVERY = (
    ("sanitario", "cozinha", "Uma instalação sanitária não abre diretamente para uma cozinha (higiene dos alimentos)."),
    ("sanitario", "copa", "Uma instalação sanitária não abre diretamente para a copa (higiene dos alimentos)."),
    ("lixo", "cozinha", "O depósito de lixos não comunica diretamente com a cozinha."),
    ("lixo", "camara_frigorifica", "O depósito de lixos não comunica diretamente com a câmara frigorífica."),
)
_FOOD = (
    ("sanitario", "loja", "Numa loja de alimentos, a instalação sanitária não abre para a área de venda: precisa de "
                          "antecâmara."),
    ("sanitario", "talho", "A instalação sanitária não abre para a preparação de frescos (talho, peixaria)."),
    ("sanitario", "padaria", "A instalação sanitária não abre para a padaria / pastelaria."),
    ("sanitario", "camara_frigorifica", "A instalação sanitária não abre para a câmara frigorífica."),
    ("sanitario", "armazem", "A instalação sanitária não abre para o armazém de mercadoria."),
    ("lixo", "talho", "O depósito de lixos não comunica com a preparação de frescos."),
    ("lixo", "padaria", "O depósito de lixos não comunica com a padaria."),
    ("lixo", "loja", "O depósito de lixos não abre para a área de venda."),
    ("lixo", "armazem", "O depósito de lixos não comunica diretamente com o armazém de alimentos."),
)
RULES = {
    "habitacao": (
        ("garagem", "quarto", "A garagem não abre diretamente para um quarto (fumos e incêndio)."),
        ("garagem", "cozinha", "A garagem não abre diretamente para a cozinha (fumos e incêndio)."),
        ("tecnica", "quarto", "A área técnica não abre diretamente para um quarto (ruído)."),
    ),
    "hospital": (
        ("sujos", "esterilizacao", "Os sujos / despejos não comunicam com a esterilização (zona limpa)."),
        ("sujos", "bloco_operatorio", "Os sujos não abrem diretamente para o bloco operatório."),
        ("sujos", "cozinha", "Os sujos não comunicam com a cozinha."),
        ("sanitario", "esterilizacao", "A instalação sanitária não abre para a esterilização."),
        ("sanitario", "bloco_operatorio", "A instalação sanitária não abre para o bloco operatório."),
        ("lixo", "esterilizacao", "O depósito de lixos não comunica com a esterilização."),
        ("morgue", "entrada", "A morgue não abre para a entrada nem para as zonas do público."),
        ("morgue", "atendimento", "A morgue não abre para as zonas do público."),
        ("morgue", "refeicoes", "A morgue não comunica com o refeitório."),
        ("morgue", "cozinha", "A morgue não comunica com a cozinha."),
        ("isolamento", "circulacao", "O quarto de isolamento entra por uma antecâmara, não diretamente do corredor."),
        ("bloco_operatorio", "entrada", "O bloco operatório não abre para a entrada (circuito limpo)."),
        ("bloco_operatorio", "atendimento", "O bloco operatório não abre para a sala de espera."),
        ("imagiologia", "atendimento", "A sala de raio-X não abre diretamente para a sala de espera (proteção "
                                       "radiológica: antecâmara ou zona de comando)."),
    ),
    "clinica": (
        ("sujos", "esterilizacao", "Os sujos / despejos não comunicam com a esterilização (zona limpa)."),
        ("sanitario", "esterilizacao", "A instalação sanitária não abre para a esterilização."),
        ("lixo", "esterilizacao", "O depósito de lixos não comunica com a esterilização."),
        ("sujos", "tratamento", "Os sujos não abrem diretamente para a sala de tratamentos."),
        ("imagiologia", "atendimento", "A sala de raio-X não abre diretamente para a sala de espera."),
    ),
    "lar": (
        ("garagem", "quarto", "A garagem não abre diretamente para um quarto."),
        ("sujos", "cozinha", "Os sujos não comunicam com a cozinha."),
        ("lixo", "refeicoes", "O depósito de lixos não comunica com a sala de refeições."),
    ),
    "escola": (
        ("sanitario", "refeicoes", "A instalação sanitária não abre diretamente para o refeitório."),
        ("cozinha", "sala_aula", "A cozinha não abre diretamente para uma sala de aula (segurança)."),
        ("tecnica", "sala_aula", "A área técnica não abre para uma sala de aula."),
        ("lixo", "refeicoes", "O depósito de lixos não comunica com o refeitório."),
        ("laboratorio", "refeicoes", "O laboratório não abre para o refeitório."),
    ),
    "creche": (
        ("cozinha", "sala_aula", "A cozinha não abre para uma sala de atividades das crianças (segurança)."),
        ("cozinha", "quarto", "A cozinha não abre para a sala de repouso das crianças."),
        ("cozinha", "recreio", "A cozinha não abre para o recreio."),
        ("sanitario", "refeicoes", "A instalação sanitária não abre diretamente para o refeitório."),
        ("tecnica", "sala_aula", "A área técnica não abre para uma sala de atividades."),
        ("lixo", "recreio", "O depósito de lixos não abre para o recreio."),
    ),
    "escritorios": (
        ("tecnica", "reunioes", "A área técnica não abre para uma sala de reuniões (ruído)."),
    ),
    "comercio": _FOOD,
    "armazem_venda": _FOOD,
    "minimercado": _FOOD,
    "supermercado": _FOOD + (
        ("cargas", "loja", "As cargas e descargas não abrem diretamente para a área de venda."),
    ),
    "restaurante": (
        ("sanitario", "refeicoes", "A instalação sanitária não abre diretamente para a sala de refeições: precisa de "
                                   "antecâmara."),
        ("sanitario", "despensa", "A instalação sanitária não abre para a despensa."),
        ("sanitario", "armazem", "A instalação sanitária não abre para o armazém de alimentos."),
        ("sanitario", "padaria", "A instalação sanitária não abre para a pastelaria."),
        ("lixo", "refeicoes", "O depósito de lixos não comunica com a sala de refeições."),
        ("lixo", "armazem", "O depósito de lixos não comunica com o armazém de alimentos."),
        ("copa_suja", "armazem", "A copa suja não comunica diretamente com o armazém de alimentos."),
        ("vestiario", "cozinha", "O vestiário do pessoal não abre diretamente para a cozinha."),
    ),
    "hotel": (
        ("lixo", "refeicoes", "O depósito de lixos não comunica com a sala de refeições."),
        ("cozinha", "quarto", "A cozinha não abre para um quarto."),
        ("tecnica", "quarto", "A área técnica não abre para um quarto (ruído)."),
    ),
    "farmacia": (
        ("sanitario", "farmacia", "A instalação sanitária não abre para a zona dos medicamentos."),
        ("sanitario", "armazem", "A instalação sanitária não abre para o armazém de medicamentos."),
        ("lixo", "farmacia", "O depósito de lixos não comunica com a zona dos medicamentos."),
    ),
    "banco": (
        ("cofre", "atendimento", "O cofre não abre para a zona do público (segurança)."),
        ("cofre", "entrada", "O cofre não abre para a entrada (segurança)."),
        ("cofre", "atm", "O cofre não abre para a zona do multibanco."),
        ("tesouraria", "atendimento", "A tesouraria não abre diretamente para a zona do público: entra por uma "
                                      "zona controlada."),
        ("tesouraria", "entrada", "A tesouraria não abre para a entrada."),
    ),
    "policia": (
        ("celas", "atendimento", "As celas não abrem para a zona do público (segurança)."),
        ("celas", "entrada", "As celas não abrem para a entrada."),
        ("armeiro", "atendimento", "O armeiro não abre para a zona do público."),
        ("armeiro", "entrada", "O armeiro não abre para a entrada."),
        ("armeiro", "celas", "O armeiro não comunica com as celas."),
        ("interrogatorio", "atendimento", "A sala de interrogatório não abre para a zona do público."),
        ("interrogatorio", "entrada", "A sala de interrogatório não abre para a entrada."),
    ),
}
DEFAULT_TYPE = "habitacao"
EXTRA_USE = {"despensa": "arrumos"}          # (words of the rules' that are another use's)


def _plain(text):
    text = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    return " ".join(text.lower().replace("_", " ").replace("/", " ").split())


def type_label(key, language="pt"):
    names = BUILDING_TYPES.get(key)
    return (names[0] if language == "pt" else names[1]) if names else str(key or "")


def use_label(key, language="pt"):
    names = USES.get(key)
    return (names[0] if language == "pt" else names[1]) if names else str(key or "")


def uses_for(building):
    """The uses offered for a type of building (its own and those of every building), as [key]."""
    return [k for k, v in USES.items() if not v[3] or building in v[3]]


def verifier_use(key):
    """The Verifier's use a programme's use is (verify/uses.USES), or None."""
    found = USES.get(key)
    return found[2] if found else None


def from_verifier(key):
    return FROM_VERIFIER.get(key or "", "outro")


def type_from_text(text):
    """A type of building from what is written (its key, its name, a word of it), or None."""
    plain = _plain(text)
    if not plain:
        return None
    for key, (pt, en) in BUILDING_TYPES.items():
        if plain in (_plain(key), _plain(pt), _plain(en)):
            return key
    for key, (pt, en) in BUILDING_TYPES.items():
        words = (_plain(key), _plain(pt), _plain(en))
        if any(plain in w or w.split()[0] == plain.split()[0] for w in words):
            return key
    return None


def use_from_text(text, name=""):
    """A use from what is written (its key, its name, a word of it — accents and case aside) or, with nothing found,
    from the room's name as the Verifier reads it; None when neither says."""
    plain = _plain(text)
    if plain:
        for key, (pt, en, _v, _types) in USES.items():
            if plain in (_plain(key), _plain(pt), _plain(en)):
                return key
        for key, (pt, en, _v, _types) in USES.items():       # (its first word: «cozinha», «cofre», «kitchen»)
            if any(plain == name.split(" ")[0] for name in (_plain(pt), _plain(en))):
                return key
    from ..verify import uses as verifier_uses
    for source in (text, name):
        found = verifier_uses.from_name(source) if source else None
        if found and found != "outro":
            return from_verifier(found)
    return None


def rules(building):
    """The pairs of uses that must not open into each other in this type of building: [(use, use, why)]."""
    return list(_EVERY) + list(RULES.get(building, ()))


def conflict_of(building, use_a, use_b, extra=()):
    """The rule two rooms of these uses joined by a door break — (use, use, why) — or None. `extra`: the project's own
    pairs [(use, use)]."""
    a, b = EXTRA_USE.get(use_a, use_a), EXTRA_USE.get(use_b, use_b)
    for rule in rules(building) + [tuple(p) + ("",) for p in extra]:
        x, y = EXTRA_USE.get(rule[0], rule[0]), EXTRA_USE.get(rule[1], rule[1])
        if {a, b} == {x, y} and (a != b or x == y):
            return rule
    return None


def room_uses(doc, facts):
    """{room GlobalId: its programme use}: the one its programme line gave it, else the Verifier's turned into one."""
    out = {}
    for guid, room in facts.rooms.items():
        space = doc.ifc.by_guid(guid)
        params = doc.ifc._params(space) if space is not None else {}
        own = params.get("UsoPrograma")
        out[guid] = own if own in USES else from_verifier(room.use)
    return out


def conflicts(doc, facts=None, building=None):
    """The rooms joined by a door that should not be: [(room, room, door, (use, use, why))] — facts: the Verifier's
    reading (verify/reader.read), building: the project's type (the programme's, else the Verifier's, else housing)."""
    from ..verify import reader
    facts = facts if facts is not None else reader.read(doc)
    building = building or project_type(doc)
    extra = []
    try:
        extra = doc.ifc.room_program_rules()
    except Exception:                                   # noqa: BLE001 (the IFC still being read)
        extra = []
    found = room_uses(doc, facts)
    out = []
    for door, (a, b) in facts.sides.items():
        if a not in found or b not in found or a == b:
            continue
        rule = conflict_of(building, found[a], found[b], extra)
        if rule is not None:
            out.append((a, b, door, rule))
    return out


def project_type(doc):
    """The project's type of building: its programme's, else the Verifier's building use when it is one, else
    housing."""
    try:
        own = doc.ifc.room_program_type()
    except Exception:                                   # noqa: BLE001
        own = None
    if own in BUILDING_TYPES:
        return own
    try:
        from ..verify import project as verify_project
        use = verify_project.settings(doc).get("building_use")
    except Exception:                                   # noqa: BLE001
        use = None
    return use if use in BUILDING_TYPES else DEFAULT_TYPE
