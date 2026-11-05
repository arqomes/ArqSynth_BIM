"""Keynotes ("notas-chave", 0.194, Phase 5 step 2 — as Revit's): a code and a short text for what an element is made
of ("02.02 Alvenaria de tijolo cerâmico 15 cm"), given to its type (all the elements of that type share it) or to
the element when it has none — in the IFC an IfcClassificationReference of the classification "Notas-chave".

In a view, a keynote tag (an annotation of kind "keynote") points at an element with a leader; its box writes the
element's code, read whenever it is drawn (so it is always the model's). The schedule "Notas-chave" lists the codes
used, their texts and how many elements carry each — the legend for the sheets.

The table below is the program's own, by chapters as a Portuguese bill of quantities goes; a code not in it (from
another program) is kept and shown as it is."""

CLASSIFICATION = "Notas-chave"

# (code, Portuguese, English)
TABLE = (
    ("01.01", "Betão armado C25/30", "Reinforced concrete C25/30"),
    ("01.02", "Betão de limpeza", "Blinding concrete"),
    ("01.03", "Aço estrutural S275", "Structural steel S275"),
    ("01.04", "Laje aligeirada de vigotas", "Beam-and-block floor"),
    ("02.01", "Alvenaria de tijolo cerâmico 11 cm", "Clay brick masonry 11 cm"),
    ("02.02", "Alvenaria de tijolo cerâmico 15 cm", "Clay brick masonry 15 cm"),
    ("02.03", "Alvenaria de tijolo cerâmico 20 cm", "Clay brick masonry 20 cm"),
    ("02.04", "Alvenaria de blocos de betão 20 cm", "Concrete block masonry 20 cm"),
    ("02.05", "Divisória de gesso cartonado", "Plasterboard partition"),
    ("03.01", "Reboco e pintura", "Render and paint"),
    ("03.02", "Estuque e pintura", "Plaster and paint"),
    ("03.03", "Azulejo cerâmico", "Ceramic wall tiles"),
    ("03.04", "Revestimento em pedra natural", "Natural stone cladding"),
    ("03.05", "Isolamento térmico pelo exterior (ETICS)", "External thermal insulation (ETICS)"),
    ("04.01", "Betonilha de regularização", "Levelling screed"),
    ("04.02", "Mosaico cerâmico", "Ceramic floor tiles"),
    ("04.03", "Soalho de madeira maciça", "Solid wood flooring"),
    ("04.04", "Pavimento flutuante laminado", "Laminate floating floor"),
    ("04.05", "Pavimento em pedra natural", "Natural stone floor"),
    ("05.01", "Teto falso em gesso cartonado", "Plasterboard suspended ceiling"),
    ("05.02", "Estuque projetado e pintura", "Sprayed plaster and paint"),
    ("06.01", "Telha cerâmica", "Clay roof tiles"),
    ("06.02", "Cobertura plana invertida", "Inverted flat roof"),
    ("06.03", "Impermeabilização betuminosa", "Bituminous waterproofing"),
    ("06.04", "Isolamento térmico XPS", "XPS thermal insulation"),
    ("07.01", "Caixilharia de alumínio com corte térmico", "Thermally broken aluminium frame"),
    ("07.02", "Vidro duplo", "Double glazing"),
    ("07.03", "Porta interior de madeira", "Interior wooden door"),
    ("07.04", "Porta exterior", "Exterior door"),
    ("07.05", "Fachada-cortina", "Curtain wall"),
    ("08.01", "Guarda metálica", "Metal railing"),
    ("08.02", "Escada de betão armado", "Reinforced concrete stair"),
    ("09.01", "Louças sanitárias", "Sanitary ware"),
    ("09.02", "Móveis de cozinha", "Kitchen cabinets"),
)
BY_CODE = {code: (pt, en) for code, pt, en in TABLE}
NO_TAG = "?"                    # a tag on an element with no keynote


def text_of(code, lang="pt", own=None):
    """The table's text for a code ("" if it is not in it) — (0.248) the project's own table's first (`own`
    {code: text}: IfcModel.keynote_table)."""
    if own and code in own:
        return own[code]
    found = BY_CODE.get(code)
    return "" if found is None else (found[0] if lang == "pt" else found[1])


def choices(lang="pt", own=None):
    """[(label "02.02 — Alvenaria…", code)] in code order — (0.248) the program's table and the project's own, its
    texts first."""
    rows = {code: (pt if lang == "pt" else en) for code, pt, en in TABLE}
    rows.update(own or {})
    return [("{} — {}".format(code, text), code) for code, text in sorted(rows.items())]


def tag_text(doc, ann):
    """What a keynote tag writes now: its element's code ("?" when it has none, or is gone)."""
    guid = (ann.extra or {}).get("element")
    if not guid or doc.get(guid) is None:
        return NO_TAG
    try:
        found = doc.ifc.keynote_of(guid)
    except Exception:
        return NO_TAG
    return found[0] if found else NO_TAG


def legend_rows(doc, lang="pt"):
    """The schedule "Notas-chave": dicts with "guid" None, "kind" "keynote", "code", "keynote_text", "count" — one per
    code used in the model, in code order."""
    counts, texts = {}, {}
    for obj in doc.objects.values():
        if not obj.is_bim:
            continue
        try:
            found = doc.ifc.keynote_of(obj.id)
        except Exception:
            continue
        if found:
            code, text = found
            counts[code] = counts.get(code, 0) + 1
            texts.setdefault(code, text or text_of(code, lang))
    return [{"guid": None, "kind": "keynote", "code": code, "keynote_text": texts[code], "count": counts[code],
             "name": code, "type": texts[code], "storey": ""} for code in sorted(counts)]
