"""(0.393) Modelos ArqSynth — Fase 1: verificar a pasta partilhada dos modelos sem abrir o ArqSynth BIM (o
«Modelos - verificar.bat» abre isto). Um menu em português: ver a lista, criar um modelo de exemplo, abrir a pasta,
ler um modelo (o que faltava ou estava errado), definir o padrão, ver o padrão, repor o de fábrica, apagar, gravar
o modelo de fábrica e o esquema numa pasta para ver o formato."""

import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from arqsynth_templates import TemplateError, paths, write_atomic  # noqa: E402
from arqsynth_templates.manager import payload  # noqa: E402

EXAMPLE = "Exemplo de escritório"
KINDS = {"wall": "paredes", "slab": "lajes", "roof": "coberturas", "column": "pilares", "beam": "vigas",
         "footing": "sapatas", "pile": "estacas", "pipe": "tubagens", "duct": "condutas", "conduit": "tubos elétricos",
         "door": "portas", "window": "janelas"}


def windows(path):
    """A path as the Windows Explorer shows it (C:\\Users\\…) when it is one of WSL's /mnt/c/…."""
    if path.startswith("/mnt/") and len(path) > 6 and path[6] == "/":
        return "{}:\\{}".format(path[5].upper(), path[7:].replace("/", "\\"))
    return path


def show_list(manager):
    print()
    for e in manager.list():
        star = "★" if e.is_default else " "
        what = " (de fábrica: vem dentro do programa)" if e.is_factory else ""
        if not e.ok:
            print(" {} {}  — ESTRAGADO: {}".format(star, e.name, e.problem))
        else:
            print(" {} {}{}  — versão {}{}".format(star, e.name, what, e.version,
                                                    ", de " + e.modified[:10] if e.modified and not e.is_factory
                                                    else ""))
    print("\n ★ = o padrão (o que um projeto novo usa)")


def make_example(manager):
    data = manager.factory().data
    data.pop("id", None)
    data["description"] = "Um exemplo para experimentar: cotas em cm, três pisos, um autor."
    data["units"].update(length="cm", decimals=1)
    data["project"].update(name="Moradia", site="Lote", building="Moradia", author="Ana Silva, arq.",
                           organization="Gabinete Exemplo, Lda.")
    data["storeys"] = [{"name": "Cave", "elevation": -3.0, "height": 3.0},
                       {"name": "Rés-do-chão", "elevation": 0.0, "height": 3.0},
                       {"name": "Piso 1", "elevation": 3.0, "height": 3.0}]
    try:
        made = manager.save(data, EXAMPLE)
        print("\n Gravado: {}".format(windows(made.path)))
    except TemplateError as exc:
        if exc.code != "exists":
            raise
        made = manager.update(EXAMPLE, data)
        print("\n Já existia: atualizado para a versão {}: {}".format(made.version, windows(made.path)))
    print(" Abra-o no Bloco de Notas para ver o formato (é texto JSON).")


def open_folder(manager):
    folder = manager.ensure()
    print("\n A abrir: {}".format(windows(folder)))
    try:
        if paths.in_wsl():
            subprocess.run(["explorer.exe", windows(folder)], cwd="/mnt/c", timeout=10)
        elif sys.platform == "win32":
            os.startfile(folder)  # noqa: S606
        else:
            subprocess.run(["xdg-open", folder], timeout=10)
    except (OSError, subprocess.SubprocessError) as exc:
        print(" Não consegui abrir a pasta: {}".format(exc))


def ask_name(manager, what):
    entries = manager.list()
    for k, e in enumerate(entries, 1):
        print("  {}  {}{}".format(k, e.name, "" if e.ok else "  (estragado)"))
    answer = input(" Número do modelo a {} (Enter: nenhum): ".format(what)).strip()
    if not answer.isdigit() or not 1 <= int(answer) <= len(entries):
        return None
    return entries[int(answer) - 1].name


def read_one(manager):
    name = ask_name(manager, "ler")
    if name is None:
        return
    try:
        made = manager.load(name)
    except TemplateError as exc:
        print("\n " + exc.text("pt"))
        return
    d = made.data
    print("\n «{}», versão {}: unidades {} com {} casa(s) decimal(is); {} piso(s); {} materiais; tipos: {}".format(
        made.name, made.version, d["units"].get("length"), d["units"].get("decimals"), len(d.get("storeys", [])),
        len(d.get("materials", [])),
        ", ".join("{} {}".format(len(v), KINDS.get(k, k)) for k, v in d.get("types", {}).items())))
    if made.notices:
        print(" Ao ler, o programa avisou:")
        for text in made.messages("pt"):
            print("  - " + text)
    else:
        print(" Lido sem nenhum aviso.")


def set_default(manager):
    name = ask_name(manager, "pôr como padrão")
    if name is None:
        return
    try:
        manager.set_default(name)
        print("\n «{}» é agora o padrão do ArqSynth BIM.".format(name))
    except TemplateError as exc:
        print("\n " + exc.text("pt"))


def show_default(manager):
    made = manager.get_default()
    print("\n O padrão do ArqSynth BIM é «{}» (versão {}).".format(made.name, made.version))
    for text in made.messages("pt"):
        print("  - " + text)
    print(" (settings.json: {})".format(windows(manager.settings_path)))


def delete(manager):
    name = ask_name(manager, "apagar")
    if name is None:
        return
    if input(" Apagar «{}»? (s/n): ".format(name)).strip().lower() != "s":
        return
    try:
        manager.delete(name)
        print("\n Apagado.")
    except TemplateError as exc:
        print("\n " + exc.text("pt"))


def write_format(manager):
    """The factory template, the schema and the format's description in <suite>/formato (not a template: only to
    see)."""
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "arqsynth_templates")
    out = os.path.join(paths.suite_dir() if manager.root is None else manager.root, "formato")
    write_atomic(os.path.join(out, "ArqSynth Padrão (fábrica).astpl"), payload(manager.factory().data))
    for name in ("schema.json", "FORMATO.md", "exemplo.astpl"):
        with open(os.path.join(here, name), "rb") as f:
            write_atomic(os.path.join(out, name), f.read())
    print("\n Gravados em {}:".format(windows(out)))
    print("  ArqSynth Padrão (fábrica).astpl — o modelo de fábrica completo (só para ver)")
    print("  schema.json — o esquema JSON; FORMATO.md — a descrição; exemplo.astpl — um exemplo curto")


def main():
    from arqbim.model import project_templates
    manager = project_templates.manager()
    actions = {"1": show_list, "2": make_example, "3": open_folder, "4": read_one, "5": set_default,
               "6": show_default, "7": None, "8": delete, "9": write_format}
    print("ArqSynth — Modelos (Fase 1: verificação)")
    print("Pasta dos modelos: {}".format(windows(manager.folder)))
    if not os.path.isdir(manager.folder):
        manager.ensure()
        print("(Não existia: acabou de ser criada — o primeiro arranque.)")
    while True:
        print("\n 1  Ver a lista dos modelos\n 2  Criar o modelo de exemplo («{}»)\n 3  Abrir a pasta dos modelos"
              "\n 4  Ler um modelo (diz o que faltava ou estava errado)\n 5  Definir um modelo como padrão"
              "\n 6  Ver o modelo padrão\n 7  Repor o modelo de fábrica como padrão\n 8  Apagar um modelo"
              "\n 9  Gravar o modelo de fábrica e o formato numa pasta, para ver\n 0  Sair".format(EXAMPLE))
        choice = input("\nEscolha: ").strip()
        if choice in ("0", ""):
            return
        if choice == "7":
            manager.reset_factory()
            print("\n O padrão voltou a ser «{}».".format(manager.factory_name))
        elif choice in actions:
            try:
                actions[choice](manager)
            except TemplateError as exc:
                print("\n " + exc.text("pt"))


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        pass
