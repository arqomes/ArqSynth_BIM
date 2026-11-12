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
)}
GROUPS = {"ceramico": ("Cerâmico", "Ceramic"), "pedra": ("Pedra", "Stone"), "madeira": ("Madeira", "Wood"),
          "tijolo": ("Tijolo", "Brick"), "remate": ("Rodapés e remates", "Skirtings and trims")}


def finish(key):
    return FINISHES.get(key) or FINISHES["porcelanico_60x60"]
