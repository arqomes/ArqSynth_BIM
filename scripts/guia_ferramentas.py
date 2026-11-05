"""(0.346) The guide of every tool, for the owner to test the program: GUIA.md, made from the program itself — the
ribbon's tabs, panels and commands (ui/ribbon.py), each command's name, key, tip, and a tool's step-by-step hint and
keys, as the Help panel (F1) shows them —, with the sections of TESTAR.md whose steps use it. Run it again after a
version so it follows:

    bash: QT_QPA_PLATFORM=xcb /opt/arqbim/venv/bin/python scripts/guia_ferramentas.py [GUIA.md]

It opens the window (nothing written to the user's settings: temporary folders) and closes it."""

import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "GUIA.md")
TMP = tempfile.mkdtemp(prefix="arqsynth_guia_")
for name, sub in (("XDG_CONFIG_HOME", "config"), ("ARQBIM_CACHE_DIR", "cache"), ("ARQBIM_SHARE_DIR", "share"),
                  ("LOCALAPPDATA", "local"), ("ARQBIM_DOCUMENTS", "docs")):
    os.environ[name] = os.path.join(TMP, sub)
    os.makedirs(os.environ[name], exist_ok=True)

from PySide6 import QtGui, QtWidgets  # noqa: E402

from arqbim import __version__  # noqa: E402
from arqbim.i18n import has, t  # noqa: E402
from arqbim.ui import help_window, ribbon  # noqa: E402

MOST_SECTIONS = 6               # the TESTAR sections named for a command, the newest first
KEY_NAMES = {"Space": "Espaço", "Del": "Delete", "PgDown": "PgDn"}     # (the keys as written on a Portuguese keyboard)
# names too common to find a command by in bold alone (a dialog's button of the same name)
GENERIC = {"Novo", "Abrir", "Guardar", "Guardar como", "Sair", "Copiar", "Colar", "Mover", "Rodar", "Apagar",
           "Selecionar", "Fechar", "Aplicar", "Duplicar", "Zoom", "Linha", "Cota"}


def clean(text):
    """A command's name as the guide writes it: no «&» of its key, one line."""
    return " ".join(str(text or "").replace("&&", "\0").replace("&", "").replace("\0", "&").split())


def testar_sections(path):
    """[(version, its title, its text)] of TESTAR.md."""
    out, head, body = [], None, []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^## (0\.\d+)(?:\s+—\s+(.*))?\s*$", line)
            if m:
                if head is not None:
                    out.append((head[0], head[1], "".join(body)))
                head, body = (m.group(1), (m.group(2) or "").strip()), []
            elif head is not None:
                body.append(line)
    if head is not None:
        out.append((head[0], head[1], "".join(body)))
    return out


def version_key(v):
    return tuple(int(p) for p in v.split("."))


def sections_of(label, sections, where):
    """The TESTAR sections whose steps use this command, newest first: those that name it on its tab's path («Render ▸
    Render realista…») or in their title, else — a name not too common (GENERIC) — those that name it in bold."""
    base = label.rstrip("…").strip()
    if len(base) < 3:
        return []
    paths = tuple(m.format(base) for m in ("▸ {}**", "▸ {}…**", "▸ {} ", "▸ {}…"))
    strong, weak = [], []
    for v, title, text in sections:
        if base.lower() in title.lower() or (any(p in text for p in paths) and where in text):
            strong.append((v, title))
        elif "**{}**".format(base) in text or "**{}…**".format(base) in text:
            weak.append((v, title))
    found = strong or ([] if base in GENERIC else weak)
    found.sort(key=lambda vt: version_key(vt[0]), reverse=True)
    return found[:MOST_SECTIONS]


def items(panel_items):
    """A panel's commands in order (its stacked small ones too)."""
    return [n for item in panel_items for n in (item if isinstance(item, tuple) else (item,))]


def describe(win, name):
    """{label, key, tip, hint, keys, menu} of a command of the ribbon, as the program has it now."""
    item = win.ribbon_item(name)
    out = {"label": name, "key": "", "tip": "", "hint": "", "keys": "", "menu": []}
    if isinstance(item, QtWidgets.QMenu):
        out["label"] = clean(item.title())
        out["menu"] = [clean(a.text()) for a in item.actions() if a.text() and not a.isSeparator()]
        return out
    if item is None:
        return out
    out["label"] = named = clean(item.text())
    keys = item.shortcuts() if hasattr(item, "shortcuts") else []
    out["key"] = ", ".join(KEY_NAMES.get(text, text) for text in
                           (k.toString(QtGui.QKeySequence.SequenceFormat.NativeText) for k in keys if not k.isEmpty()))
    if out["key"]:                                       # («Parede (W)»: its key said apart)
        out["label"] = re.sub(r"\s*\([^()]{1,8}\)$", "", out["label"])
    tip = clean(item.toolTip())
    if tip and tip.rstrip("…").strip() not in (out["label"].rstrip("…").strip(), named.rstrip("…").strip()):
        out["tip"] = tip                                 # (not its name again)
    tool = getattr(win, "tools", {}).get(name)
    if tool is not None:
        try:
            out["hint"] = clean(tool.hint())
        except Exception:                                # (a hint that needs the tool started: its text alone)
            out["hint"] = clean(t("hint." + name)) if has("hint." + name) else ""
        keys_help = getattr(tool, "keys_help", None)
        if keys_help and has(keys_help):
            out["keys"] = clean(t(keys_help))
    return out


INTRO = """# Guia das ferramentas — ArqSynth BIM {version}

Este guia descreve **todas as ferramentas e comandos da fita**, separador a separador, para as poder experimentar.
Para cada uma diz:

- **onde está** (Separador ▸ Painel) e a tecla, se tiver;
- **o que faz** — a mesma dica que aparece ao passar o rato pelo botão;
- **como se usa** — o que o programa pede, passo a passo, quando a ferramenta está ativa;
- **onde estão os passos de teste** — as secções do [TESTAR.md](TESTAR.md) que a experimentam clique a clique.

O guia é feito pelo próprio programa (`scripts/guia_ferramentas.py`): os nomes e os textos são exatamente os do
ArqSynth BIM {version}.

**Uma nota sobre o TESTAR:** as secções antigas (antes da 0.182) falam dos menus de então — «Ficheiro ▸», «Vista ▸»,
«BIM ▸», o separador «Conceito». Hoje esses comandos estão nos separadores da fita, com o mesmo nome ou parecido: use
este guia, ou o **F1 ▸ Procurar**, para os encontrar.

---

## Antes de começar

1. Abra o programa com **ArqSynth BIM.bat**. Para cada teste, comece com um projeto novo: **Ctrl+N**.
2. **Onde estão as coisas:**
   - em cima, **os separadores** (Início, Modelagem, Gerenciar…) e, por baixo, **a fita** com os botões do separador
     escolhido;
   - quando um painel não cabe, fica recolhido num botão com uma seta: clique nele para ver os comandos;
   - por baixo da fita, **a barra contextual**: as opções da ferramenta ativa (tipo, altura, pavimento…);
   - ao centro, **a vista** (3D, planta, corte, alçado, folha), com os separadores das vistas abertas;
   - à esquerda, **o navegador** do projeto; à direita, **as Propriedades** do que está escolhido;
   - as mensagens aparecem num **balão** por cima da vista; se faltar alguma coisa, o balão diz o quê e, muitas vezes,
     tem um botão que faz o passo que falta.
3. **Regras que valem para todas as ferramentas:**
   - **Esc** (ou **Espaço**, fora das ferramentas de colocação) volta a **Selecionar**;
   - as medidas escrevem-se no teclado e confirmam-se com **Enter** (por exemplo `6` Enter, ou `3;2` para um
     retângulo de 3 × 2);
   - **Ctrl+Z** desfaz e **Ctrl+Y** refaz, um passo de cada vez;
   - **F1** abre o painel **Ajuda**: a ferramenta em uso, a procura de um comando pelo nome («Mostrar onde está»
     acende o botão na fita), uns primeiros passos e as teclas.
4. **Se alguma coisa não funcionar**, escreva-me:
   - o que fez, clique a clique;
   - o que esperava e o que aconteceu;
   - se puder, uma captura.

   O registo de erros fica em `%LOCALAPPDATA%\\ArqSynth BIM\\arqbim.log`.
"""


# a short test of each tab, by the commands' own names (the example files: tests\saida_gui, made by the tests)
SCENARIOS = {
    "home": ["Faça um retângulo e puxe-o (separador Modelagem), e carregue em **Guardar** (Ctrl+S): escolha uma pasta "
             "e um nome.",
             "**Novo** (Ctrl+N) e depois **Abrir…** (Ctrl+O) o ficheiro que guardou: volta como estava.",
             "**Ligar um desenho DXF/DWG…** com `planta_cad.dxf`: as linhas ficam no chão, para desenhar por cima.",
             "Na planta (F4), **Exportar vista em PDF…** (Ctrl+P) e **Exportar imagem da vista…**: abra os ficheiros.",
             "**Exportar modelo 3D…** com «O modelo todo»: em GLB, abra-o no Blender ou num visualizador de glTF na "
             "internet (as peças por pavimento e categoria, com os materiais); em OBJ, no SketchUp; em STL a 1:100, "
             "no programa da impressora 3D.",
             "**Ajuda** (F1): no separador «Procurar», escreva «parede» e clique em «Mostrar onde está»."],
    "modeling": ["**Retângulo** (R): clique no chão, escreva `3;2` e Enter.",
                 "**Push/Pull** (P): clique no retângulo, escreva `3` e Enter: um volume de 3 m.",
                 "**Mover** (M), **Copiar** (depois de uma cópia, `3x` Enter faz mais três), **Rodar** (Q, `90` "
                 "Enter), **Espelhar**, **Escala** (`2` Enter): cada um com o volume escolhido.",
                 "**Fita métrica** (T) e **Cota** (C) entre dois cantos.",
                 "Escolha um volume e **Classificar como ▸ Parede alvenaria 20 cm**: passa a parede BIM.",
                 "Ctrl+Z várias vezes: tudo volta atrás, um passo de cada vez."],
    "manage": ["**Novo pavimento**; PgUp e PgDn mudam o pavimento ativo (veja-o na planta, F4).",
               "Desenhe paredes no pavimento 0, escolha-as e **Repetir nos pavimentos…**: aparecem nos de cima.",
               "**Tipos… (criar e editar)**: duplique a «Parede alvenaria 20 cm», mude a espessura do bloco e "
               "**Aplicar**; desenhe uma parede com o tipo novo.",
               "**Materiais…** e **Padrões…**: mude a cor e a trama de um material e veja-o nas paredes.",
               "**Localização do terreno…**: escreva a latitude e a longitude da obra."],
    "massing": ["**Importar imagem de fundo…** com `planta_digitalizada.png`; a seguir **Calibrar imagem**: clique nas "
                "duas pontas da cota vermelha e escreva `8` Enter.",
                "Desenhe por cima com **Linha**, **Retângulo** e **Push/Pull**.",
                "Ligue `planta_cad.dxf` (Início ▸ Importar) e use **Modelo a partir do desenho…**: escolha as camadas "
                "das paredes e OK.",
                "Ligue `sala_digitalizada.ply` (Ligar uma nuvem de pontos…) e use **Modelo a partir da nuvem…**."],
    "terrain": ["**Importar pontos de levantamento…** com `levantamento.csv`: o terreno aparece com as curvas de nível.",
                "Na planta (F4), **Plataforma**: escreva a cota (`1,5` Enter) e clique em dois cantos opostos — a "
                "plataforma fica cortada no terreno, com os taludes.",
                "**Aterro e escavação…**: a terra tirada e posta.",
                "**Inclinações do terreno**: o terreno pintado pela inclinação.",
                "**Rampa de acesso** entre duas plataformas."],
    "architecture": ["**Parede** (W): clique, `6` Enter, `4` Enter, `6` Enter, clique no primeiro ponto. Esc.",
                     "**Porta** (D) e **Janela** (J): passe por cima de uma parede e clique. **Caixilho Studio** abre "
                     "o editor de caixilharia de uma janela escolhida.",
                     "**Laje** no topo das paredes, ou **Cobertura** clicando dentro delas.",
                     "**Sala**: clique dentro das paredes — nome e área. **Teto** e **Luminária** na sala.",
                     "**Escada** e **Guarda**. **Cozinha**: clique na face de dentro de uma parede onde começa, nos "
                     "cantos e no fim, e Enter.",
                     "Escolha uma parede: aparece o separador verde **Modificar | Paredes** (último deste guia)."],
    "structure": ["**Gerar eixos…** (por exemplo 3 × 3 a 5 m) e **Pilares na grelha**.",
                  "**Sapatas** debaixo dos pilares, **Vigas entre pilares** e **Lajes** nos vãos (ou, numa casa de "
                  "paredes, **Propor estrutura…**).",
                  "**Ações e materiais…**: veja as cargas de cada pavimento; OK.",
                  "**Analisar a estrutura…**: os esforços de cada barra.",
                  "**Verificação EC2 / EC6 e armaduras…**: cada elemento OK / atenção / falha; «Pôr as armaduras no "
                  "modelo» e veja-as em Raio-X.",
                  "**Lista de armaduras…**, **Quantidades da estrutura…** e **Memória de cálculo…**."],
    "services": ["Numa casa com uma sala (Arquitetura ▸ Sala), **Louça sanitária**: passe sobre a face de uma parede "
                 "e clique — a sanita encosta-se a ela.",
                 "**Propor águas e esgotos** e depois **Ligar à rede**; **Retirar a proposta de águas e esgotos** "
                 "desfaz.",
                 "**Propor pontos elétricos…** pelas salas, **Novo circuito** e **Verificar a instalação elétrica…**.",
                 "**Conduta** e **Grelha / difusor** no teto.",
                 "**Detetar conflitos…**: uma conduta a atravessar uma viga aparece na lista."],
    "collaborate": ["Guarde o projeto e **Partilhar projeto numa pasta…** (uma pasta de teste).",
                    "Noutra cópia do programa (ou depois de fechar), **Abrir projeto partilhado…** e **Sincronizar "
                    "com o central** (Ctrl+Alt+S).",
                    "**Verificar IFC para certificação** e **Dados IFC em falta…**: o que falta ao modelo.",
                    "**Nova nota de coordenação (BCF)…**: título, descrição e a vista como está."],
    "annotate": ["**Planta do pavimento ativo** (F4).",
                 "**Cotar paredes**, **Cotar fachadas** e **Cotar salas**; **Estilo das cotas…** muda todas.",
                 "**Corte**: dois cliques na planta e o lado para onde se olha; F5 volta ao último.",
                 "**Pormenor**: um retângulo à volta de um canto da planta.",
                 "**Desenho 2D**: linhas, textos e regiões tramadas na planta."],
    "view": ["F8, F2 e F3: isométrica, topo e frente. **Nova vista 3D (guardar esta)** guarda a câmara.",
             "**Caixa de corte (3D)** (F6): arraste as faces da caixa.",
             "**Estilos de vista…**: os estilos (sombreado, realista…) e as suas opções — sombras, arestas, "
             "transparência, tramas.",
             "**Posicionar câmara** num ponto do chão e **Caminhar** com as setas.",
             "**Tema escuro** e **Vistas escuras**; **Tema claro** volta."],
    "render": ["**Render realista…**: tamanho HD, qualidade Rascunho, Renderizar — a imagem vai afinando; Guardar "
               "imagem.",
               "Os passos completos (acabamentos, luminárias, noite, sol do terreno) estão no TESTAR, 0.343."],
    "ctx:walls": ["Escolha uma ou mais paredes: o separador verde **Modificar | Paredes** aparece sozinho.",
                  "**Virar a parede**, **Ligar o topo (laje / cobertura)** com uma laje por cima, **Desligar o topo**.",
                  "**Juntar paredes** (duas em linha), **Ligar as pontas** e **Ortogonalizar**.",
                  "**Editar perfil**: arraste o contorno da parede no seu alçado; **Repor perfil** volta."],
}


def main():
    from arqbim.app import create_window
    app, win = create_window()
    win.resize(1440, 860)
    win.show()
    for _ in range(50):
        app.processEvents()
    sections = testar_sections(os.path.join(ROOT, "TESTAR.md"))
    parts = [INTRO.format(version=__version__)]
    # the first steps and the keys: the Help panel's own
    parts.append("\n## Primeiro percurso: uma casa do princípio ao PDF\n\n"
                 + clean(t("help.steps_intro")) + "\n\n"
                 + "\n".join("{}. {}".format(k, clean(t(key))) for k, (key, _cmd) in
                             enumerate(help_window.FIRST_STEPS, 1)) + "\n")
    parts.append("\n## As teclas\n\n```\n" + t("help.text").strip() + "\n```\n")
    tabs = [(d, t("disc." + d), ribbon.PANELS[d]) for d in ribbon.DISCIPLINES] + \
        [("ctx:" + k, t("ctxtab." + k), panels) for k, panels in ribbon.CONTEXTS.items()]
    counted = {d: len({n for _p, its in panels for n in items(its)}) for d, _l, panels in tabs}
    parts.append("\n## Índice\n\n" + "\n".join(
        "{}. [{}](#{}) — {} comandos".format(k, label, anchor(k, label), counted[d])
        for k, (d, label, _p) in enumerate(tabs, 1)) + "\n")
    first = {}                                           # command -> where it was described first
    total = 0
    for k, (d, label, panels) in enumerate(tabs, 1):
        parts.append("\n---\n\n## {}. {}\n".format(k, label))
        about = "tip.disc." + d if not d.startswith("ctx:") else "tip.ctxtab." + d[4:]
        if has(about):
            parts.append("\n" + clean(t(about)) + "\n")
        if d in SCENARIOS:                               # (a short test of the tab, before its commands)
            parts.append("\n**Para testar este separador** (projeto novo, Ctrl+N):\n\n" + "\n".join(
                "{}. {}".format(n, step) for n, step in enumerate(SCENARIOS[d], 1)) + "\n")
        for panel, panel_items in panels:
            plabel = t("rpanel." + panel) if has("rpanel." + panel) else panel
            parts.append("\n### {} ▸ {}\n".format(label, plabel))
            for name in items(panel_items):
                info = describe(win, name)
                here = "{} ▸ {}".format(label, plabel)
                if name in first:
                    parts.append("\n- **{}** — o mesmo de {}.\n".format(info["label"], first[name]))
                    continue
                first[name] = here
                total += 1
                head = "\n#### {}".format(info["label"]) + ("  ·  tecla {}".format(info["key"]) if info["key"] else "")
                lines = [head, ""]
                if info["tip"]:
                    lines.append("- **O que faz:** " + info["tip"])
                if info["hint"]:
                    lines.append("- **Como se usa:** " + info["hint"])
                if info["keys"]:
                    lines.append("- **Teclas:** " + info["keys"])
                if info["menu"]:
                    lines.append("- **Escolhas:** " + " · ".join(info["menu"]))
                found = sections_of(info["label"], sections, label)
                if found:
                    lines.append("- **Passos de teste (TESTAR.md):** " + "; ".join(
                        "{}{}".format(v, " «{}»".format(title) if title else "") for v, title in found))
                if len(lines) == 2:
                    lines.append("- (sem descrição no programa)")
                parts.append("\n".join(lines) + "\n")
    parts.append("\n---\n\n*{} comandos descritos, gerados do ArqSynth BIM {}.*\n".format(total, __version__))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("".join(parts))
    print("{}: {} comandos, {} separadores".format(OUT, total, len(tabs)), flush=True)
    win.doc.modified = False
    win.close()
    app.processEvents()
    shutil.rmtree(TMP, ignore_errors=True)
    os._exit(0)


def anchor(k, label):
    """The Markdown anchor of a tab's heading «N. Label»."""
    text = "{} {}".format(k, label).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"\s+", "-", text.strip())


if __name__ == "__main__":
    main()
