"""(0.563, PLANO.md «Gerador de revestimentos 3D em IFC», steps 2 and 9) The finishes a Revestimento is made of — each
a piece (its material, size, thickness), how it is laid (core/tiling's layout) and what is under it (the bed: glue
or mortar, its thickness) and between (the grout, set back from the face). Plain data; a finish chosen is copied
into the element, where everything of it can be changed."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Finish:
    key: str
    name_pt: str
    name_en: str
    material: str               # the piece's (ifc/catalog key)
    w: float                    # m: the piece along (its length)
    h: float                    # m: across (its height on a wall)
    thickness: float            # m
    pattern: str = "eito"
    joint: float = 0.003        # m
    bond: float = 0.5
    bed: float = 0.005          # m: glue or mortar under it (0: none — a floating floor, a dry fixing)
    bed_material: str = "cola_cimenticia"
    grout: str = "argamassa_junta"
    recess: float = 0.001       # m: how far the grout stays back from the face
    lengths: tuple = ()
    group: str = "ceramico"     # its family (cerâmico, pedra, madeira, tijolo…)
    extra: dict = field(default_factory=dict)

    def layout(self):
        """Its core/tiling layout (the start: automatic — no narrow strips)."""
        d = {"pattern": self.pattern, "w": self.w, "h": self.h, "joint": self.joint, "bond": self.bond,
             "origin": "auto", "thickness": self.thickness}
        if self.lengths:
            d["lengths"] = list(self.lengths)
        d.update(self.extra)
        return d


FINISHES = {f.key: f for f in (
    Finish("azulejo_20x20", "Azulejo 20 × 20", "Wall tile 20 × 20", "azulejo", 0.20, 0.20, 0.007, joint=0.002,
           bed=0.004),
    Finish("azulejo_30x60", "Azulejo 30 × 60", "Wall tile 30 × 60", "azulejo", 0.60, 0.30, 0.009, joint=0.002),
    Finish("metro_10x20", "Azulejo metro 10 × 20 (desencontrado)", "Subway tile 10 × 20", "azulejo", 0.20, 0.10,
           0.007, pattern="desencontrado", joint=0.002, bed=0.004),
    Finish("porcelanico_60x60", "Porcelânico 60 × 60", "Porcelain 60 × 60", "porcelanico", 0.60, 0.60, 0.010),
    Finish("porcelanico_120x60", "Porcelânico 120 × 60 (⅓)", "Porcelain 120 × 60 (⅓ bond)", "porcelanico", 1.20, 0.60,
           0.010, pattern="desencontrado", bond=1.0 / 3.0, joint=0.002, bed=0.006),
    Finish("hidraulico_20x20", "Ladrilho hidráulico 20 × 20", "Encaustic tile 20 × 20", "ladrilho_30", 0.20, 0.20,
           0.015, joint=0.001, bed=0.010),
    Finish("hexagono_20", "Hexágono 20 cm", "Hexagon 20 cm", "porcelanico", 0.20, 0.20, 0.009, pattern="hexagono",
           joint=0.002),
    Finish("pedra_60x40", "Pedra 60 × 40 (desencontrada)", "Stone 60 × 40 (running bond)", "pedra", 0.60, 0.40, 0.020,
           pattern="desencontrado", joint=0.004, bed=0.010, group="pedra"),
    Finish("pedra_opus", "Pedra em opus romano", "Stone in opus romanum", "calcario", 0.60, 0.20, 0.020,
           pattern="opus", joint=0.004, bed=0.010, group="pedra"),
    Finish("marmore_60x60", "Mármore 60 × 60 (diagonal)", "Marble 60 × 60 (diagonal)", "marmore", 0.60, 0.60, 0.020,
           pattern="diagonal", joint=0.001, bed=0.010, group="pedra"),
    Finish("soalho_carvalho", "Soalho de carvalho (réguas variáveis)", "Oak boards (random lengths)", "carvalho", 1.20,
           0.15, 0.015, pattern="reguas", joint=0.001, bed=0.0, grout="", recess=0.0, lengths=(0.6, 0.9, 1.2),
           group="madeira"),
    Finish("espinha_carvalho", "Carvalho em espinha", "Oak herringbone", "carvalho", 0.60, 0.10, 0.015,
           pattern="espinha", joint=0.001, bed=0.003, grout="", recess=0.0, group="madeira"),
    Finish("deck", "Deck (réguas)", "Decking", "deck", 2.40, 0.14, 0.025, pattern="reguas", joint=0.006, bed=0.0,
           grout="", recess=0.0, lengths=(1.2, 1.8, 2.4), group="madeira"),
    Finish("tijolo_face_vista", "Tijolo face à vista (meia vez)", "Facing brick (stretcher bond)", "tijolo_macico",
           0.24, 0.07, 0.020, pattern="desencontrado", joint=0.010, bed=0.010, bed_material="cola_cimenticia",
           recess=0.004, group="tijolo"),
    Finish("tijolo_flamengo", "Tijolo — aparelho flamengo", "Brick — Flemish bond", "tijolo_macico", 0.24, 0.07,
           0.020, pattern="flamengo", joint=0.010, bed=0.010, recess=0.004, group="tijolo"),
    # (0.567) skirtings, laid along the foot of a room's walls
    Finish("rodape_madeira", "Rodapé de madeira 8 cm", "Wooden skirting 8 cm", "madeira_branco", 2.40, 0.08, 0.012,
           joint=0.001, bed=0.0, grout="", recess=0.0, group="remate"),
    Finish("rodape_ceramico", "Rodapé cerâmico 8 cm", "Ceramic skirting 8 cm", "porcelanico", 0.60, 0.08, 0.009,
           joint=0.002, bed=0.004, group="remate"),
    Finish("rodape_pedra", "Rodapé de pedra 10 cm", "Stone skirting 10 cm", "pedra", 0.60, 0.10, 0.015,
           joint=0.002, bed=0.008, group="remate"),
    # (0.568) sills, thresholds, copings: long stone pieces, the whole depth of the face in one
    Finish("peitoril_pedra", "Peitoril / soleira de pedra 3 cm", "Stone sill / threshold 3 cm", "calcario", 1.20,
           0.40, 0.030, joint=0.002, bed=0.010, group="remate", extra={"origin": "canto"}),
    Finish("capeamento_pedra", "Capeamento de pedra 3 cm", "Stone coping 3 cm", "granito", 1.00, 0.40, 0.030,
           joint=0.003, bed=0.010, group="remate", extra={"origin": "canto"}),
    Finish("capeamento_zinco", "Capeamento de zinco", "Zinc coping", "zinco", 2.00, 0.60, 0.002, joint=0.0,
           bed=0.0, grout="", recess=0.0, group="remate", extra={"origin": "canto"}),
    # (0.569) façades and walls in panels, continuous coats, soft floors
    Finish("hpl_fachada", "Painel HPL de fachada 2,5 × 1,25", "HPL façade panel 2.5 × 1.25", "hpl", 2.50, 1.25,
           0.008, joint=0.008, bed=0.0, grout="", recess=0.0, group="painel", extra={"origin": "canto"}),
    Finish("acm_cassete", "Cassete de compósito 1,5 × 0,5", "Composite cassette 1.5 × 0.5", "acm", 1.50, 0.50,
           0.004, joint=0.015, bed=0.0, grout="", recess=0.0, group="painel"),
    Finish("chapa_ondulada", "Chapa metálica em faixas verticais", "Metal sheet in upright strips", "aco_grafite",
           3.00, 0.50, 0.002, pattern="vertical", bond=0.0, joint=0.003, bed=0.0, grout="", recess=0.0,
           group="painel"),
    Finish("zinco_junta_agrafada", "Zinco de junta agrafada", "Standing-seam zinc", "zinco", 6.00, 0.43, 0.002,
           pattern="vertical", bond=0.0, joint=0.012, bed=0.0, grout="", recess=0.0, group="painel"),
    Finish("gesso_cartonado", "Gesso cartonado 1,2 × 2,6", "Plasterboard 1.2 × 2.6", "gesso", 1.20, 2.60, 0.0125,
           pattern="eito", joint=0.001, bed=0.0, grout="", recess=0.0, group="painel", extra={"origin": "canto"}),
    Finish("microcimento", "Microcimento (contínuo)", "Microcement (seamless)", "microcimento", 1.0, 1.0, 0.003,
           pattern="continuo", joint=0.0, bed=0.0, grout="", recess=0.0, group="continuo"),
    Finish("pintura_branca", "Pintura branca", "White paint", "tinta_branca", 1.0, 1.0, 0.0005,
           pattern="continuo", joint=0.0, bed=0.0, grout="", recess=0.0, group="continuo"),
    Finish("reboco_pintado", "Reboco pintado 2 cm", "Painted render 2 cm", "reboco", 1.0, 1.0, 0.020,
           pattern="continuo", joint=0.0, bed=0.0, grout="", recess=0.0, group="continuo"),
    Finish("etics", "ETICS / capoto 6 cm", "ETICS 6 cm", "etics", 1.0, 1.0, 0.065, pattern="continuo", joint=0.0,
           bed=0.0, grout="", recess=0.0, group="continuo"),
    Finish("papel_parede", "Papel de parede (rolos de 53 cm)", "Wallpaper (53 cm rolls)", "papel_parede", 10.0,
           0.53, 0.0005, pattern="vertical", bond=0.0, joint=0.0, bed=0.0, grout="", recess=0.0,
           group="continuo"),
    Finish("vinilico_reguas", "Vinílico em réguas", "Vinyl planks", "vinilico", 1.22, 0.18, 0.005, pattern="reguas",
           joint=0.0005, bed=0.0, grout="", recess=0.0, lengths=(0.61, 0.92, 1.22), group="madeira"),
    Finish("cortica_placas", "Cortiça em placas 60 × 30", "Cork tiles 60 × 30", "cortica", 0.60, 0.30, 0.006,
           pattern="desencontrado", joint=0.0005, bed=0.0, grout="", recess=0.0, group="madeira"),
    Finish("alcatifa_placas", "Alcatifa em placas 50 × 50", "Carpet tiles 50 × 50", "tecido", 0.50, 0.50, 0.007,
           joint=0.0, bed=0.0, grout="", recess=0.0, group="continuo"),
)}
GROUPS = {"ceramico": ("Cerâmico", "Ceramic"), "pedra": ("Pedra", "Stone"), "madeira": ("Madeira", "Wood"),
          "tijolo": ("Tijolo", "Brick"), "painel": ("Painéis e chapas", "Panels and sheets"),
          "continuo": ("Contínuos (pintura, reboco, papel)", "Seamless (paint, render, paper)"),
          "remate": ("Rodapés e remates", "Skirtings and trims"),
          "proprio": ("Os meus revestimentos", "My finishes")}
BUILT_IN = frozenset(FINISHES)
CUSTOM_PREFIX = "proprio_"
FIELDS = ("name_pt", "name_en", "material", "w", "h", "thickness", "pattern", "joint", "bond", "bed",
          "bed_material", "grout", "recess", "lengths")


def finish(key):
    return FINISHES.get(key) or FINISHES["porcelanico_60x60"]


def to_dict(f):
    d = {k: getattr(f, k) for k in FIELDS}
    d["lengths"] = list(f.lengths)
    d["key"] = f.key
    return d


def register(entries):
    """(0.569) Finishes of one's own (from the project or the user's library: [{key, name_pt, …}]) put in the
    catalogue, in the group «Os meus revestimentos». Those of the same key replaced."""
    for d in entries or ():
        try:
            key = d["key"] if str(d["key"]).startswith(CUSTOM_PREFIX) else CUSTOM_PREFIX + str(d["key"])
            FINISHES[key] = Finish(key, str(d.get("name_pt") or key), str(d.get("name_en") or d.get("name_pt") or key),
                                   str(d["material"]), float(d["w"]), float(d["h"]), float(d["thickness"]),
                                   str(d.get("pattern") or "eito"), float(d.get("joint") or 0.0),
                                   float(d.get("bond") if d.get("bond") is not None else 0.5),
                                   float(d.get("bed") or 0.0), str(d.get("bed_material") or "cola_cimenticia"),
                                   str(d.get("grout") or ""), float(d.get("recess") or 0.0),
                                   tuple(float(v) for v in d.get("lengths") or ()), "proprio")
        except (KeyError, TypeError, ValueError):
            continue


def custom():
    return [to_dict(f) for k, f in FINISHES.items() if k not in BUILT_IN]


def library_path():
    """The user's own finishes, kept between projects."""
    import os
    from arqsynth_templates.paths import suite_dir      # (where the company's title block is kept too)
    return os.path.join(suite_dir(), "revestimentos.json")


def load_library():
    import json
    try:
        with open(library_path(), encoding="utf-8") as fh:
            register(json.load(fh))
    except (OSError, ValueError, ImportError):
        pass


def save_library(entries):
    import json
    import os
    try:
        path = library_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        old = {}
        try:
            with open(path, encoding="utf-8") as fh:
                old = {d["key"]: d for d in json.load(fh)}
        except (OSError, ValueError):
            pass
        old.update({d["key"]: d for d in entries})
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(list(old.values()), fh, ensure_ascii=False, indent=1)
    except (OSError, ImportError):
        pass
