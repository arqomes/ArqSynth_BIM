# Modelos ArqSynth (`.astpl`) — o formato

Um **modelo** («Arquivo Modelo») guarda as configurações com que um projeto novo começa: unidades, dados do
projeto IFC, pisos, tipos de parede/laje/cobertura/vãos, materiais, classes IFC, estilos de anotação, cotas, linhas e
folhas, e preferências da interface. É de **toda a suite ArqSynth**: qualquer programa o lê, e outros programas
também (é JSON).

## Onde ficam

Numa pasta da suite, fora da pasta de instalação de qualquer programa (uma atualização nunca lhe mexe):

| Sistema | Pasta |
|---|---|
| Windows | `%APPDATA%\ArqSynth\` (ex.: `C:\Users\<nome>\AppData\Roaming\ArqSynth\`) |
| macOS | `~/Library/Application Support/ArqSynth/` |
| Linux | `~/.config/ArqSynth/` (ou `$XDG_CONFIG_HOME/ArqSynth/`) |
| Linux do Windows (WSL) — onde corre o ArqSynth BIM | a pasta do **Windows** (`/mnt/c/Users/<nome>/AppData/Roaming/ArqSynth/`), para os programas Windows da suite verem os mesmos modelos |

Se a variável `ARQSYNTH_HOME` existir, é essa a pasta (testes, uma pasta partilhada na rede).

```
ArqSynth/
  templates/
    Escritório.astpl          um modelo
    Moradias T3.astpl
  settings.json               o modelo padrão de cada programa
```

## O ficheiro `.astpl`

- **JSON** em UTF-8 (abre-se no Bloco de Notas) — ou, quando o modelo tem ficheiros (texturas), um **ZIP** com o JSON
  em `template.json` e os ficheiros em `assets/` (um material com `"texture": "tijolo.png"` → `assets/tijolo.png`).
  Distingue-se pelos dois primeiros bytes (`PK` = ZIP).
- Comprimentos em **metros**, cores em `"#rrggbb"`, datas em ISO 8601 (UTC).
- O esquema completo está em [`schema.json`](schema.json) (JSON Schema 2020-12); um exemplo com todas as secções em
  [`exemplo.astpl`](exemplo.astpl).

| Campo | O que é |
|---|---|
| `format` | sempre `"arqsynth-template"` |
| `schema_version` | a versão deste formato (**1**). Um programa que lê uma mais nova guarda o que não conhece e não a regrava por cima |
| `id` | UUID; o mesmo ao mudar de nome e ao atualizar |
| `name`, `version` | o nome; `version` sobe 1 a cada atualização (cada projeto guarda o nome e a versão do modelo usado) |
| `description`, `author`, `created`, `modified`, `programs`, `generator` | informação |
| `units` | `length` (`m`/`cm`/`mm`), `decimals`, `area_decimals`, `angle_decimals`, `decimal_separator` |
| `project` | nomes do IfcProject, IfcSite, IfcBuilding; autor, organização, morada; esquema IFC; unidade de comprimento do IFC |
| `storeys` | `[{name, elevation, height}]` (m) |
| `materials` | `[{key, name, name_en, category, color, transparency, finish, texture, thermal{conductivity, density, specific_heat}, acoustic{absorption, sound_reduction}, graphics}]` |
| `types` | por espécie (`wall`, `slab`, `roof`, `column`, `beam`, `footing`, `pile`, `pipe`, `duct`, `conduit`, `door`, `window`): camadas `[{material, thickness, function}]` de fora para dentro / de baixo para cima, ou secção (`profile`, `material`); portas e janelas: `width`, `height`, `sill`, `operation`, `design` (o desenho do Caixilho Studio) |
| `ifc_classes` | a classe IFC de cada espécie de elemento (`"wall": "IfcWall"`) |
| `annotation`, `dimensions`, `lines`, `sheets` | textos, estilo das cotas, penas/tramas/símbolos, papel e carimbo das folhas |
| `interface` | tema, paleta, página inicial, vista inicial, atalhos |
| `extensions` | o que só um programa usa: `{"arqsynth-bim": {...}, "arqsynth-cad": {...}}` |

## Regras para quem escreve um programa da suite

1. **Ler**: aceitar JSON ou ZIP; se `schema_version` for menor, converter (ver `migrate.py`); se for maior, ler o que
   conhece e guardar o resto. Campos em falta ou errados → os do modelo de fábrica do programa, e **avisar**.
2. **Gravar**: escrever num ficheiro temporário na mesma pasta e só depois substituir (`os.replace`) — nunca um
   ficheiro meio escrito. Guardar o que não se conhece (os `extensions` dos outros programas, campos novos).
3. **`settings.json`**: `{"schema_version": 1, "defaults": {"<programa>": {"name": "...", "id": "..."}}}` — cada
   programa só muda a sua entrada, com o ficheiro de bloqueio `settings.json.lock` (criado em exclusivo; se tiver
   mais de 15 s, é de um programa que parou e pode ser retirado).
4. O modelo de fábrica (**ArqSynth Padrão**) vem dentro de cada programa: não está na pasta, não se apaga, e é o que
   se usa se a pasta estiver vazia, o ficheiro estragado ou o padrão tiver desaparecido.

Em Python, a pasta `arqsynth_templates/` faz tudo isto (só biblioteca padrão — copia-se para o outro programa):

```python
from arqsynth_templates import TemplateManager
modelos = TemplateManager("arqsynth-cad", factory=MEU_MODELO_DE_FABRICA)
modelo = modelos.get_default()      # o padrão (ou o de fábrica, com o aviso em modelo.messages())
modelos.save(dados, "Escritório")   # list(), load(), update(), delete(), duplicate(), rename(), set_default()…
```
