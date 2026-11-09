"""PT/EN string table. The app has its own language setting (PT by default)."""

_LANG = "pt"

_STRINGS = {
    "app.title": ("ArqSynth BIM", "ArqSynth BIM"),
    "app.untitled": ("sem título", "untitled"),
    "splash.version": ("Versão {v}", "Version {v}"),
    "splash.engine": ("A preparar o motor 3D e o IFC…", "Loading the 3D engine and IFC…"),
    "splash.window": ("A abrir a janela…", "Opening the window…"),
    # menus
    "menu.file": ("&Arquivo", "&File"),
    "menu.edit": ("&Editar", "&Edit"),
    "menu.view": ("&Vista", "&View"),
    "menu.tools": ("&Ferramentas", "&Tools"),
    "menu.help": ("A&juda", "&Help"),
    "menu.bim": ("&BIM", "&BIM"),
    "act.open": ("Abrir…", "Open…"),
    "act.save": ("Guardar", "Save"),
    "act.save_as": ("Guardar como…", "Save as…"),
    "act.classify": ("Classificar como", "Classify as"),
    "file.filter": ("Modelos IFC (*.ifc)", "IFC models (*.ifc)"),
    "ask.save": ("Guardar as alterações em \"{f}\"?", "Save changes to \"{f}\"?"),
    "info.saved": ("Gravado: {f} — IFC4 validado, sem erros.", "Saved: {f} — IFC4 validated, no errors."),
    "warn.invalid": ("Gravado: {f} — o validador encontrou {n} problema(s). Primeiro: {first}",
                     "Saved: {f} — the validator found {n} problem(s). First: {first}"),
    "info.opened": ("Aberto: {f} — {n} elementos, em {s} s.", "Opened: {f} — {n} elements, in {s} s."),
    "act.view_plan": ("Planta do pavimento ativo (corte a 1,20 m)", "Plan of the active storey (cut at 1.20 m)"),
    "info.plan": ("Planta de {name}, cortada a {z}. Page Up / Page Down: outro pavimento. F4 ou outra vista: 3D.",
                  "Plan of {name}, cut at {z}. Page Up / Page Down: another storey. F4 or another view: 3D."),
    "act.box": ("Caixa de corte (3D)", "Section box (3D)"),
    "act.box_selection": ("Caixa de corte à volta da seleção", "Section box round the selection"),
    "tab.3d": ("3D", "3D"),
    # (0.387) the start page
    "tab.start": ("Início", "Start"),
    "act.start_page": ("Página inicial", "Start page"),
    "tip.start_page": ("A página inicial: começar um projeto, os tutoriais, os documentos recentes, as discussões e os "
                       "apoiadores.",
                       "The start page: start a project, the tutorials, the recent documents, the discussions and the "
                       "supporters."),
    "act.new_from_base": ("Novo a partir de arquivo base…", "New from a base file…"),
    "tip.new_from_base": ("Começa um projeto a partir de um arquivo base (um modelo): abre-o como projeto novo, para "
                          "gravar com outro nome — o arquivo base fica como estava.",
                          "Starts a project from a base file (a template): opens it as a new project, to be saved under "
                          "another name — the base file stays as it was."),
    "info.new_from_base": ("Projeto novo a partir de «{f}». Ao gravar, dê-lhe um nome (o arquivo base fica como "
                           "estava).",
                           "A new project from “{f}”. When saving, give it a name (the base file stays as it was)."),
    "info.recent_missing": ("«{f}» já não está onde estava: saiu da lista dos recentes.",
                            "“{f}” is no longer where it was: taken off the recent list."),
    "start.tagline": ("Modelação BIM em IFC nativo · versão {v}", "BIM modelling in native IFC · version {v}"),
    "start.begin": ("Começar", "Start"),
    "start.new": ("Novo projeto", "New project"),
    "start.open": ("Abrir arquivo…", "Open file…"),
    "start.from_base": ("Novo de arquivo base…", "New from a base file…"),
    "start.base_files": ("Arquivos base", "Base files"),
    "start.base_none": ("Ponha arquivos IFC na pasta dos arquivos base para os ter aqui.",
                        "Put IFC files in the base files' folder to have them here."),
    "start.base_tip": ("Novo projeto a partir de {f}", "New project from {f}"),
    "start.base_folder": ("Abrir a pasta base", "Open the base folder"),
    "start.tutorials": ("Tutoriais", "Tutorials"),
    "start.videos": ("▶  Vídeos no YouTube", "▶  Videos on YouTube"),
    "start.videos_tip": ("Os tutoriais em vídeo, no canal do ArqSynth: {u}", "The video tutorials, on ArqSynth's "
                                                                            "channel: {u}"),
    "start.tutorial_missing": ("O tutorial «{t}» não está nesta cópia do programa.",
                               "The tutorial “{t}” is not in this copy of the program."),
    "start.tutorial_close": ("Fechar o tutorial (voltam as Discussões e os Apoiadores)",
                             "Close the tutorial (the Discussions and the Supporters come back)"),
    "start.tutorial_find": ("Procurar neste tutorial…", "Find in this tutorial…"),
    "start.tutorial_hits": ("{n} de {m}", "{n} of {m}"),
    "start.tutorial_none_found": ("Nada encontrado", "Not found"),
    "start.tutorial_next": ("Seguinte (Enter)", "Next (Enter)"),
    "start.tutorial_prev": ("Anterior (Shift+Enter)", "Previous (Shift+Enter)"),
    "start.recent": ("Documentos recentes", "Recent documents"),
    "start.recent_none": ("Os projetos que abrir e gravar aparecem aqui.", "The projects you open and save show here."),
    "start.recent_remove": ("Tirar da lista (o arquivo fica)", "Take off the list (the file stays)"),
    "start.missing": ("(já não está nesta pasta)", "(no longer in its folder)"),
    "start.keep": ("Manter arquivos recentes", "Keep recent files"),
    # (0.388) the recent documents' views
    "start.recent_find": ("Procurar…", "Find…"),
    "start.order.used": ("Mais recentes", "Most recent"),
    "start.order.name": ("Nome (A–Z)", "Name (A–Z)"),
    "start.order.modified": ("Data de alteração", "Date modified"),
    "start.order_tip": ("Por que ordem aparecem", "In what order they show"),
    "start.view.grid": ("Miniaturas grandes", "Large pictures"),
    "start.view.list": ("Lista", "List"),
    "start.view.details": ("Detalhes (pasta, data, tamanho)", "Details (folder, date, size)"),
    "start.col.name": ("Nome", "Name"),
    "start.col.folder": ("Pasta", "Folder"),
    "start.col.modified": ("Alterado", "Modified"),
    "start.col.size": ("Tamanho", "Size"),
    "start.menu.open": ("Abrir", "Open"),
    "start.menu.folder": ("Abrir a pasta", "Open the folder"),
    "start.menu.clear": ("Limpar a lista toda", "Clear the whole list"),
    "start.recent_count": ("{n} de {m}", "{n} of {m}"),
    "start.recent_not_found": ("Nenhum documento recente tem essas palavras.", "No recent document has those words."),
    "start.discussions": ("Discussões no GitHub", "Discussions on GitHub"),
    "start.discussions_none": ("As discussões aparecem aqui quando o repositório do GitHub estiver ligado.",
                               "The discussions show here once the GitHub repository is linked."),
    "start.discussions_open": ("Abrir as Discussões", "Open the Discussions"),
    "start.supporters": ("Apoiadores", "Supporters"),
    "start.supporters_none": ("Os nomes de quem apoia o ArqSynth BIM aparecem aqui.",
                              "The names of those who support ArqSynth BIM show here."),
    "start.support": ("♥  Apoiar o ArqSynth", "♥  Support ArqSynth"),
    "start.not_linked": ("«{what}» ainda não tem endereço: fica para ligar (assets/start_page.json).",
                         "“{what}” has no address yet: to be linked (assets/start_page.json)."),
    "tab.close": ("Fechar esta vista", "Close this view"),
    "tab.close_others": ("Fechar as outras vistas", "Close the other views"),
    "act.close_view": ("Fechar a vista (aba)", "Close the view (tab)"),
    "act.next_view": ("Vista seguinte (aba)", "Next view (tab)"),
    "act.prev_view": ("Vista anterior (aba)", "Previous view (tab)"),
    "info.box_on": ("Caixa de corte à volta do modelo. Arraste os pontos azuis (Selecionar) para mover as faces da "
                    "caixa. F6: o modelo inteiro outra vez.",
                    "Section box round the model. Drag the blue dots (Select) to move the box's faces. F6: the whole "
                    "model again."),
    "info.box_on_selection": ("Caixa de corte à volta da seleção. Arraste os pontos azuis (Selecionar) para mover "
                              "as faces da caixa. F6: o modelo inteiro outra vez.",
                              "Section box round the selection. Drag the blue dots (Select) to move the box's "
                              "faces. F6: the whole model again."),
    "info.box_off": ("Sem caixa de corte: o modelo inteiro.", "No section box: the whole model."),
    "info.box": ("Caixa de corte: {size}.", "Section box: {size}."),
    "info.box_nothing": ("Nada para pôr dentro da caixa de corte.", "Nothing to put inside the section box."),
    "storeys.status_plan": (" — planta", " — plan"),
    "storeys.status_section": (" — corte", " — section"),
    "act.export_pdf": ("Exportar vista em PDF…", "Export view as PDF…"),
    "pdf.title_plan": ("Planta — {name} (corte a {z})", "Plan — {name} (cut at {z})"),
    "pdf.title_section": ("Corte", "Section"),
    "pdf.file_plan": ("planta {name}", "plan {name}"),
    "pdf.file_section": ("corte", "section"),
    "pdf.filter": ("Desenho PDF (*.pdf)", "PDF drawing (*.pdf)"),
    "pdf.working": ("A preparar o desenho (linhas escondidas)…", "Preparing the drawing (hidden lines)…"),
    "info.pdf": ("PDF gravado: {f} (A3, escala 1:{s}).", "PDF written: {f} (A3, scale 1:{s})."),
    "info.pdf_empty": ("Nada a desenhar nesta vista.", "Nothing to draw in this view."),
    "act.export_sheets": ("Exportar folhas em PDF…", "Export sheets as PDF…"),
    "sheet.window": ("Folha", "Sheet"),
    "sheet.paper": ("Papel:", "Paper:"),
    "sheet.view_scale": ("Escala da vista:", "View scale:"),
    "sheet.scale_auto": ("Automática", "Automatic"),
    "sheet.tidy": ("Arrumar", "Tidy up"),
    "sheet.tidy_tip": ("Todas as vistas de volta aos lugares automáticos (as que arrastou também).",
                       "Every view back to its automatic place (also the ones you dragged)."),
    # (0.472) the sheet's commands on the parameters' bar; drawings imported; the company's title block
    "ctx.sheet": ("Folha", "Sheet"),
    "sheet.zoom_out_short": ("−", "−"),
    "sheet.zoom_in_short": ("+", "+"),
    "sheet.import": ("Importar desenho…", "Import drawing…"),
    "sheet.import_tip": ("Pôr na folha um desenho de fora: DWG ou DXF (numa escala), uma imagem (PNG, JPG…) ou um "
                         "SVG. Arraste-o para o pôr no sítio; Delete tira-o da folha.",
                         "Put a drawing from outside on the sheet: a DWG or DXF (at a scale), a picture (PNG, JPG…) or "
                         "an SVG. Drag it into place; Delete takes it off the sheet."),
    "sheet.import_filter": ("Desenhos (*.dwg *.dxf *.svg *.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;"
                            "DWG / DXF (*.dwg *.dxf);;Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;"
                            "SVG (*.svg)",
                            "Drawings (*.dwg *.dxf *.svg *.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;"
                            "DWG / DXF (*.dwg *.dxf);;Pictures (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp);;"
                            "SVG (*.svg)"),
    "sheet.import_bad": ("Não consegui ler «{f}» (para DWG é preciso o ODA File Converter).",
                         "Could not read “{f}” (a DWG needs the ODA File Converter)."),
    "sheet.import_kind": ("Esse tipo de ficheiro não se põe na folha: use DWG, DXF, SVG ou uma imagem.",
                          "That kind of file does not go on a sheet: use DWG, DXF, SVG or a picture."),
    "info.sheet_import": ("«{name}» posto na folha. Arraste-o para o mudar de sítio. Ctrl+Z desfaz.",
                          "“{name}” put on the sheet. Drag it to move it. Ctrl+Z undoes."),
    "sheet.import_scale": ("Escala do desenho", "Drawing scale"),
    "sheet.import_width": ("Largura", "Width"),
    "sheet.pick_hint": ("Clique numa vista ou num desenho para lhe mudar a escala", "Click a view or a drawing to "
                        "change its scale"),
    "sheet.edit_title_block": ("Editar carimbo…", "Edit title block…"),
    "sheet.edit_title_block_tip": ("Desenhar o carimbo da sua empresa na própria folha: linhas, retângulos, textos, "
                                   "imagens (o logótipo) e campos com os dados de cada folha. Fica no projeto e pode "
                                   "guardá-lo no escritório para todos os projetos.",
                                   "Draw your company's title block on the sheet itself: lines, rectangles, texts, "
                                   "pictures (the logo) and fields with each sheet's details. Kept with the project, "
                                   "and it can be kept in the office for every project."),
    "cmd.sheet_import": ("Desenho na folha", "Drawing on the sheet"),
    "cmd.company_title_block": ("Carimbo da empresa", "Company title block"),
    "info.company_title_block": ("Carimbo da empresa em {n} folha(s). Ctrl+Z desfaz.",
                                 "Company title block on {n} sheet(s). Ctrl+Z undoes."),
    # (0.473) the company's title block drawn on the sheet (ui/title_block_editor.py)
    "tbe.title": ("Carimbo", "Title block"),
    "tbe.tool_select": ("Selecionar", "Select"),
    "tbe.tool_line": ("Linha", "Line"),
    "tbe.tool_rect": ("Retângulo", "Rectangle"),
    "tbe.tool_text": ("Texto", "Text"),
    "tbe.tool_field": ("Campo", "Field"),
    "tbe.tool_image": ("Imagem", "Picture"),
    "tbe.pen": ("Espessura", "Thickness"),
    "tbe.fill": ("Preenchimento", "Fill"),
    "tbe.fill_none": ("Nenhum", "None"),
    "tbe.fill_e6e6e6": ("Cinza claro", "Light grey"),
    "tbe.fill_b3b3b3": ("Cinza", "Grey"),
    "tbe.fill_000000": ("Preto", "Black"),
    "tbe.text": ("Texto", "Text"),
    "tbe.text_new": ("texto", "text"),
    "tbe.size": ("Tamanho", "Size"),
    "tbe.bold": ("Negrito", "Bold"),
    "tbe.align": ("Alinhar", "Align"),
    "tbe.align_left": ("Esq.", "Left"),
    "tbe.align_center": ("Centro", "Centre"),
    "tbe.align_right": ("Dir.", "Right"),
    "tbe.colour": ("Cor", "Colour"),
    "tbe.colour_000000": ("Preto", "Black"),
    "tbe.colour_6b6b6b": ("Cinzento", "Grey"),
    "tbe.field": ("Campo", "Field"),
    "tbe.own_field": ("campo do projeto", "project field"),
    "tbe.image": ("Imagem", "Picture"),
    "tbe.picture": ("Trocar imagem…", "Change picture…"),
    "tbe.picture_filter": ("Imagens (*.png *.jpg *.jpeg *.bmp *.gif *.svg)", "Pictures (*.png *.jpg *.jpeg *.bmp *.gif "
                           "*.svg)"),
    "tbe.delete": ("Apagar", "Delete"),
    "tbe.start": ("Começar de", "Start from"),
    "tbe.start_full": ("Carimbo completo", "Full title block"),
    "tbe.start_compact": ("Carimbo compacto", "Compact title block"),
    "tbe.start_strip": ("Faixa lateral", "Side strip"),
    "tbe.start_company": ("Exemplo com logótipo", "Example with a logo"),
    "tbe.start_office": ("O do escritório", "The office's"),
    "tbe.start_blank": ("Em branco", "Blank"),
    "tbe.save_office": ("Guardar no escritório", "Keep in the office"),
    "tbe.save_office_tip": ("Guarda este carimbo para todos os projetos novos (e para os outros programas ArqSynth).",
                            "Keeps this title block for every new project (and the other ArqSynth programs)."),
    "tbe.everyone": ("Em todas as folhas", "On every sheet"),
    "tbe.done": ("✓ Concluir", "✓ Finish"),
    "tbe.done_tip": ("Guarda o carimbo no projeto (Ctrl+Z desfaz) e volta à folha.",
                     "Keeps the title block in the project (Ctrl+Z undoes) and goes back to the sheet."),
    "tbe.cancel": ("Cancelar", "Cancel"),
    "tbe.cancel_ask": ("Sair sem guardar o que mudou no carimbo?", "Leave without keeping the title block's changes?"),
    "tbe.cancel_leave": ("Sair sem guardar", "Leave without keeping"),
    "tbe.cancel_stay": ("Continuar a desenhar", "Go on drawing"),
    "tbe.hint": ("A desenhar o carimbo: escolha a ferramenta na barra de parâmetros (Linha, Retângulo, Texto, Campo, "
                 "Imagem). Dois cliques ou arrastar desenham; duplo clique num texto escreve-o. Delete apaga · setas "
                 "deslocam · Ctrl+Z desfaz · roda do rato: zoom. «Concluir» guarda.",
                 "Drawing the title block: choose the tool on the parameters' bar (Line, Rectangle, Text, Field, "
                 "Picture). Two clicks or a drag draw; double-click a text to write it. Delete deletes · arrows move · "
                 "Ctrl+Z undoes · mouse wheel: zoom. «Finish» keeps it."),
    "tbe.no_sheet": ("Para desenhar o carimbo, crie primeiro uma folha (navegador ▸ Folhas).",
                     "To draw the title block, make a sheet first (navigator ▸ Sheets)."),
    "tbe.office_none": ("Ainda não há carimbo guardado no escritório.", "No title block kept in the office yet."),
    "tbe.saved": ("Carimbo guardado no escritório: {f}", "Title block kept in the office: {f}"),
    "tbe.save_failed": ("Não consegui guardar o carimbo: {e}", "Could not keep the title block: {e}"),
    "tbe.size_label": ("{w} × {h}", "{w} × {h}"),
    "tbe.company_name": ("NOME DA EMPRESA", "COMPANY NAME"),
    "tbe.contacts": ("Morada · Cidade\nTel. · e-mail", "Address · Town\nPhone · e-mail"),
    "sheet.refresh": ("Atualizar desenhos", "Update drawings"),
    "sheet.refresh_needed": ("Atualizar desenhos (o modelo mudou)", "Update drawings (the model changed)"),
    "sheet.export": ("Exportar PDF…", "Export PDF…"),
    "sheet.hint": ("Arraste uma vista para a mudar de sítio. Clique numa vista para lhe escolher a escala; "
                   "Delete tira-a da folha. Para pôr mais vistas: painel Projeto, botão direito numa planta, "
                   "corte ou alçado ▸ Pôr na folha. Papel e legenda: painel Propriedades (Editar tipo…, ou duplo "
                   "clique na legenda). Roda do rato: zoom; botão do meio: mover. As etiquetas das armaduras e das "
                   "plantas de estrutura também se arrastam (duplo clique: voltam ao sítio).",
                   "Drag a view to move it. Click a view to choose its scale; Delete takes it off the sheet. "
                   "To put more views: Project panel, right-click a plan, section or elevation ▸ Put on sheet. "
                   "Paper and title block: Properties panel (Edit type…, or double-click the title block). Mouse "
                   "wheel: zoom; middle button: pan. The labels of reinforcement drawings and structure plans can "
                   "be dragged too (double-click: back to their place)."),
    "sheet.title_block": ("Legenda…", "Title block…"),
    "sheet.title_block_tip": ("Os dados da obra na legenda (iguais em todas as folhas), o nome e o número desta "
                              "folha. Também com duplo clique na legenda.",
                              "The project's details in the title block (the same on every sheet), this sheet's "
                              "name and number. Also by double-clicking the title block."),
    "tb.window": ("Legenda das folhas", "Sheets' title block"),
    "tb.intro": ("Os dados da obra aparecem na legenda de todas as folhas e nos PDF.",
                 "The project's details appear in the title block of every sheet and in the PDFs."),
    "tb.this_sheet": ("Esta folha", "This sheet"),
    "tb.project": ("Obra", "Project"),
    "tb.client": ("Dono de obra", "Client"),
    "tb.site": ("Local", "Site"),
    "tb.author": ("Autor do projeto", "Architect"),
    "tb.stage": ("Fase do projeto", "Design stage"),
    "tb.title": ("Desenho", "Drawing"),
    "tb.scale": ("Escala", "Scale"),
    "tb.date": ("Data", "Date"),
    "tb.number": ("Folha n.º", "Sheet no."),
    # (0.472) the company's own title block: its boxes (Editar carimbo…)
    "tb.company": ("Empresa", "Company"),
    "tb.contacts": ("Contactos", "Contacts"),
    "tb.logo": ("Logótipo", "Logo"),
    "tb.blank": ("(vazio)", "(empty)"),
    "tb.revision": ("Revisão", "Revision"),                                      # (0.473) fields of the drawn one
    "tb.count": ("Total de folhas", "Number of sheets"),
    "tb.number_auto": ("{n} (automático: a ordem das folhas)", "{n} (automatic: the order of the sheets)"),
    "tb.project_auto": ("{name} (o nome do ficheiro)", "{name} (the file's name)"),
    "tb.stages": ("Programa base|Estudo prévio|Anteprojeto|Licenciamento|Projeto de execução|Assistência técnica",
                  "Brief|Concept design|Preliminary design|Planning permission|Construction documents|"
                  "Construction support"),
    "sheet.plan": ("Planta — {name}", "Plan — {name}"),
    "sheet.file_all": ("folhas", "sheets"),
    "info.on_sheet": ("«{view}» está agora na folha «{sheet}».", "\"{view}\" is now on sheet \"{sheet}\"."),
    "info.sheet_empty": ("Nada a exportar: a folha não tem vistas (botão direito numa vista ▸ Pôr na folha).",
                         "Nothing to export: the sheet has no views (right-click a view ▸ Put on sheet)."),
    "info.sheets_pdf": ("PDF gravado: {f} ({n} folha(s)).", "PDF written: {f} ({n} sheet(s))."),
    "tree.sheets": ("Folhas", "Sheets"),
    "tree.put_on_sheet": ("Pôr na folha", "Put on sheet"),
    "tree.new_sheet": ("Nova folha", "New sheet"),
    "tree.export_sheets": ("Exportar todas em PDF…", "Export all as PDF…"),
    "tree.open_sheet": ("Abrir", "Open"),
    "tree.export_sheet": ("Exportar em PDF…", "Export as PDF…"),
    "tree.remove_sheet": ("Apagar esta folha", "Delete this sheet"),
    "tree.take_off": ("Tirar da folha", "Take off the sheet"),
    "sched.title": ("Tabelas", "Schedules"),
    "sched.cat.walls": ("Paredes", "Walls"),
    "sched.cat.slabs": ("Lajes", "Slabs"),
    "sched.cat.roofs": ("Coberturas", "Roofs"),                                     # (0.265)
    "sched.col.projected": ("Área em planta", "Area in plan"),
    "sched.col.eaves": ("Beirados", "Eaves"),
    "sched.col.ridges": ("Cumeeiras", "Ridges"),
    "sched.col.hips": ("Rincões", "Hips"),
    "sched.col.valleys": ("Larós", "Valleys"),
    "sched.col.gables": ("Empenas", "Gable edges"),
    "sched.col.tops": ("Remates no alto", "Top edges"),
    "sched.cat.columns": ("Pilares", "Columns"),
    # (0.500) the steel structure's lists
    "sched.cat.steel": ("Estrutura metálica: lista de material", "Steel structure: bill of materials"),
    "sched.cat.bolts": ("Estrutura metálica: parafusos", "Steel structure: bolts"),
    "sched.cat.cutting": ("Estrutura metálica: corte das barras", "Steel structure: bar cutting"),      # (0.501)
    "sched.col.bars": ("Barras de 12 m", "12 m bars"),
    "sched.col.bought": ("Comprados", "Bought"),
    "sched.col.used": ("Nas peças", "In pieces"),
    "sched.col.waste": ("Desperdício", "Waste"),
    "act.steel_nc": ("Exportar para fabrico", "Export for fabrication"),
    "tip.steel_nc": ("Grava numa pasta um ficheiro DSTV NC1 por marca (para as máquinas de corte e furação) e o plano "
                     "de corte das barras (CSV).",
                     "Writes in a folder a DSTV NC1 file per mark (for the sawing and drilling machines) and the bars' "
                     "cutting plan (CSV)."),
    "steel_nc.folder": ("Pasta para os ficheiros de fabrico", "Folder for the fabrication files"),
    "info.steel_nc": ("{n} ficheiros NC1 e o plano de corte gravados em {folder}.",
                      "{n} NC1 files and the cutting plan written in {folder}."),
    "info.steel_nc_none": ("Não há peças de aço para fabricar.", "No steel pieces to fabricate."),
    "sched.col.mark": ("Marca", "Mark"),
    "sched.col.grade": ("Aço", "Grade"),
    "sched.col.cut_length": ("Comprimento", "Length"),
    "sched.col.kg_m": ("kg/m", "kg/m"),
    "sched.col.paint": ("Pintura", "Paint"),
    "sched.col.bolt": ("Parafuso", "Bolt"),
    "sched.col.bolt_kind": ("Tipo", "Kind"),
    "steel_piece.column": ("Pilar", "Column"),
    "steel_piece.beam": ("Viga", "Beam"),
    "steel_piece.brace": ("Contraventamento", "Brace"),
    "steel_piece.purlin": ("Madre", "Purlin"),
    "steel_piece.member": ("Elemento", "Member"),
    "steel_piece.plate": ("Chapa", "Plate"),
    "steel_piece.bolt": ("Parafuso", "Bolt"),
    "steel_piece.anchor": ("Chumbadouro", "Anchor bolt"),
    "cmd.number_steel": ("Numerar peças de aço", "Number the steel pieces"),
    "act.number_steel": ("Numerar peças", "Number pieces"),
    "tip.number_steel": ("Escreve as marcas nas peças de aço (P, V, CV, M, E, Ch): a mesma para as peças iguais; uma "
                         "peça que não mudou guarda a sua.",
                         "Writes the marks on the steel pieces (P, V, CV, M, E, Ch): the same for the same pieces; a "
                         "piece that has not changed keeps its own."),
    "info.number_steel": ("{n} marca(s) escritas nas peças de aço. As Tabelas «Estrutura metálica» listam-nas.",
                          "{n} mark(s) written on the steel pieces. The «Steel structure» schedules list them."),
    "info.number_steel_none": ("As marcas das peças de aço já estão em dia.", "The steel pieces' marks are up to date."),
    "sched.cat.doors": ("Portas", "Doors"),
    "sched.cat.windows": ("Janelas", "Windows"),
    "sched.cat.other": ("Outros elementos", "Other elements"),
    "sched.cat.keynotes": ("Notas-chave", "Keynotes"),                    # (0.194) the legend
    "sched.col.code": ("Código", "Code"),
    "sched.col.keynote_text": ("Descrição", "Description"),
    "props.keynote": ("Nota-chave (do tipo)", "Keynote (the type's)"),
    "keynote.none": ("(sem nota-chave)", "(no keynote)"),
    "cmd.keynote": ("Nota-chave", "Keynote"),
    "cmd.keynote_table": ("Tabela de notas-chave do projeto", "The project's keynote table"),                # (0.248)
    "act.keynote_table": ("Notas-chave do projeto…", "Project keynotes…"),
    "kntable.title": ("Notas-chave do projeto", "The project's keynotes"),
    "kntable.note": ("Os códigos e textos próprios deste projeto. Aparecem ao lado da tabela do programa quando se "
                     "escolhe a nota-chave de um elemento; um código que já existe lá fica com o texto daqui, e os "
                     "elementos que o têm passam a escrevê-lo assim.",
                     "This project's own codes and texts. They are offered beside the program's table when an "
                     "element's keynote is chosen; a code it already has takes the text given here, and the elements "
                     "with it write it so."),
    "kntable.code": ("Código", "Code"),
    "kntable.text": ("Texto", "Text"),
    "kntable.add": ("Acrescentar", "Add"),
    "kntable.copy": ("Copiar uma da tabela do programa…", "Copy one from the program's table…"),
    "kntable.remove": ("Tirar", "Remove"),
    "info.keynote_table": ("Tabela de notas-chave do projeto: {n} códigos. Ctrl+Z desfaz.",
                           "The project's keynote table: {n} codes. Ctrl+Z undoes."),
    "sched.cat.rooms": ("Ambientes: quadro de áreas", "Rooms: areas"),              # (0.125; 0.357: Ambientes)
    "sched.cat.finishes": ("Ambientes: quadro de acabamentos", "Rooms: finishes"),
    "sched.col.number": ("N.º", "No."),
    "sched.col.perimeter": ("Perímetro", "Perimeter"),
    "sched.col.floor": ("Piso", "Floor"),
    "sched.col.walls": ("Paredes", "Walls"),
    "sched.col.ceiling": ("Teto", "Ceiling"),
    "sched.by_storey": ("Agrupar por pavimento", "Group by storey"),
    "sched.count_rooms": ("{n} ambientes", "{n} rooms"),
    "sched.by_type": ("Agrupar por tipo", "Group by type"),
    "sched.export": ("Exportar (Excel, CSV, JSON)…", "Export (Excel, CSV, JSON)…"),
    # (0.477) a table in its tab over the canvas, the side panel «Tabelas»
    "sched.export_short": ("Exportar…", "Export…"),
    "sched.export_tip": ("A tabela para o Excel (XLSX), CSV, ou JSON para outros programas (KazaFix Cost): números "
                         "como números, com as unidades.",
                         "The table to Excel (XLSX), CSV, or JSON for other programs (KazaFix Cost): numbers as "
                         "numbers, with their units."),
    "sched.properties": ("Propriedades…", "Properties…"),
    "sched.properties_tip": ("Os campos, os filtros, a ordem e os grupos da tabela, como as Propriedades da tabela do "
                             "Revit (a tabela de uma categoria fica uma tabela do projeto).",
                             "The table's fields, filters, order and groups, as Revit's Schedule Properties (a "
                             "category's table becomes one of the project's)."),
    "sched.highlight": ("Realçar no modelo", "Highlight in model"),
    "sched.highlight_tip": ("Escolhe no modelo os elementos das linhas escolhidas (todas, se nenhuma) e enquadra-os.",
                            "Picks in the model the elements of the rows chosen (all, if none) and frames them."),
    "sched.bar_title": ("Tabela: {name}", "Schedule: {name}"),
    "tab.table": ("Tabela — {name}", "Schedule — {name}"),
    "tables.title": ("Tabelas", "Schedules"),
    "tables.hint": ("Clique numa tabela para a abrir na tela. Botão direito: mais comandos.",
                    "Click a schedule to open it on the canvas. Right button: more commands."),
    "tables.search": ("Procurar tabela…", "Find a schedule…"),
    "tables.new": ("Nova tabela…", "New schedule…"),
    "tables.new_tip": ("Uma tabela do projeto, como no Revit: a categoria, os campos, os filtros, a ordem e os grupos.",
                       "A schedule of the project's, as in Revit: the category, fields, filters, order and groups."),
    "tables.duplicate": ("Duplicar", "Duplicate"),
    "tables.open": ("Abrir", "Open"),
    "tables.put": ("Pôr numa folha nova", "Put on a new sheet"),
    "tables.own_tip": ("Tabela do projeto ({cat})", "The project's schedule ({cat})"),
    "tables.copy_name": ("{name} (cópia)", "{name} (copy)"),
    "tables.group.own": ("Tabelas do projeto", "The project's schedules"),
    "tables.group.quantities": ("Quantidades do modelo", "Model quantities"),
    "tables.group.rooms": ("Ambientes e acabamentos", "Rooms and finishes"),
    "tables.group.openings": ("Portas e janelas", "Doors and windows"),
    "tables.group.services": ("Instalações", "Services"),
    "tables.group.notes": ("Anotações", "Annotations"),
    "info.table_deleted": ("Tabela apagada. Ctrl+Z desfaz.", "Schedule deleted. Ctrl+Z undoes."),
    # (0.478) a table of the project's as a spreadsheet: cells, merges, borders, formulas
    "grid.total_n": ("Total: {n}", "Total: {n}"),
    "grid.formula_hint": ("Um texto, um número ou uma fórmula: =SOMA(C:C), =C12*1,23, =ARRED(MÉDIA(C3:C9);2)…",
                          "A text, a number or a formula: =SUM(C:C), =C12*1.23, =ROUND(AVERAGE(C3:C9),2)…"),
    "grid.fx_tip": ("O que está na célula escolhida. Enter escreve-o; uma fórmula começa por «=». As linhas dos "
                    "elementos vêm do modelo.",
                    "What is in the cell chosen. Enter writes it; a formula starts with «=». The elements' rows come "
                    "from the model."),
    "grid.merge": ("Unir", "Merge"),
    "grid.merge_tip": ("Une as células escolhidas numa só (títulos, cabeçalhos, totais, notas) — ou separa-as, se já "
                       "estiverem unidas.",
                       "Merges the cells chosen into one (titles, headings, totals, notes) — or splits them, if "
                       "merged."),
    "grid.merge_menu": ("Unir células", "Merge cells"),
    "grid.unmerge": ("Separar células", "Unmerge cells"),
    "grid.bold": ("N", "B"),
    "grid.bold_tip": ("Negrito", "Bold"),
    "grid.italic": ("I", "I"),
    "grid.italic_tip": ("Itálico", "Italic"),
    "grid.align": ("Alinhar", "Align"),
    "grid.align.left": ("À esquerda", "Left"),
    "grid.align.center": ("Ao centro", "Centre"),
    "grid.align.right": ("À direita", "Right"),
    "grid.align.auto": ("Como vem (os números à direita)", "As it comes (numbers to the right)"),
    "grid.borders": ("Bordas", "Borders"),
    "grid.borders_tip": ("Linhas à volta das células escolhidas, como no Excel.",
                         "Lines round the cells chosen, as in Excel."),
    "grid.border.all": ("Todas as bordas", "All borders"),
    "grid.border.outer": ("Contorno", "Outline"),
    "grid.border.thick_outer": ("Contorno grosso", "Thick outline"),
    "grid.border.bottom": ("Só em baixo", "Bottom"),
    "grid.border.top_bottom": ("Em cima e em baixo", "Top and bottom"),
    "grid.border.none": ("Sem bordas", "No borders"),
    "grid.fill": ("Fundo", "Fill"),
    "grid.fill_tip": ("A cor de fundo das células escolhidas.", "The cells' fill colour."),
    "grid.fill.none": ("Sem cor", "No colour"),
    "grid.fill.#fff2cc": ("Amarelo claro", "Light yellow"),
    "grid.fill.#e2efda": ("Verde claro", "Light green"),
    "grid.fill.#ddebf7": ("Azul claro", "Light blue"),
    "grid.fill.#fce4d6": ("Laranja claro", "Light orange"),
    "grid.fill.#ededed": ("Cinzento claro", "Light grey"),
    "grid.fill.#d9d9d9": ("Cinzento", "Grey"),
    "grid.insert": ("Inserir", "Insert"),
    "grid.insert_tip": ("Linhas de título e de notas, colunas com os campos dos elementos.",
                        "Title and note rows, columns with the elements' fields."),
    "grid.row_above": ("Linha acima", "Row above"),
    "grid.row_below": ("Linha abaixo", "Row below"),
    "grid.title_row": ("Linha de título (por cima da tabela)", "Title row (over the table)"),
    "grid.note_row": ("Linha de notas (por baixo da tabela)", "Note row (under the table)"),
    "grid.delete_row": ("Apagar a linha", "Delete the row"),
    "grid.column": ("Coluna com o campo", "Column with the field"),
    "grid.column_fx": ("Coluna calculada (ƒx)…", "Calculated column (ƒx)…"),
    "grid.delete_column": ("Tirar a coluna «{name}»", "Remove the column «{name}»"),
    "grid.totals_row": ("Linha dos totais", "Totals row"),
    "grid.functions": ("ƒx", "ƒx"),
    "grid.functions_tip": ("Põe na célula escolhida uma soma, uma média… desta coluna, ou os dados do projeto.",
                           "Puts in the cell chosen a sum, an average… of this column, or the project's data."),
    "grid.functions_menu": ("ƒx Funções e dados do projeto", "ƒx Functions and project data"),
    "grid.fn.sum": ("Soma da coluna", "Sum of the column"),
    "grid.fn.avg": ("Média da coluna", "Average of the column"),
    "grid.fn.count": ("Contar os elementos", "Count the elements"),
    "grid.fn.max": ("Máximo da coluna", "Largest of the column"),
    "grid.fn.min": ("Mínimo da coluna", "Smallest of the column"),
    "grid.data": ("Dados do projeto", "Project data"),
    "grid.data.projeto": ("Nome do projeto", "Project name"),
    "grid.data.data": ("Data de hoje", "Today's date"),
    "grid.data.tabela": ("Nome da tabela", "Schedule name"),
    "grid.data.n": ("Número de elementos", "Number of elements"),
    "grid.clear": ("Limpar o conteúdo", "Clear contents"),
    "grid.make_own": ("Formatar como no Excel", "Format as in Excel"),
    "grid.make_own_tip": ("Faz desta lista uma tabela do projeto, com células como no Excel: títulos, notas, células "
                          "unidas, bordas, cores e fórmulas.",
                          "Makes this list a schedule of the project's, with cells as in Excel: titles, notes, merged "
                          "cells, borders, colours and formulas."),
    "grid.no_model_cell": ("As linhas dos elementos vêm do modelo: escreva numa linha de título, de notas ou na dos "
                           "totais (botão direito ▸ Inserir ▸ Linha de notas).",
                           "The elements' rows come from the model: write in a title or note row, or the totals' "
                           "(right button ▸ Insert ▸ Note row)."),
    "grid.no_merge": ("Unem-se células da mesma zona — títulos, cabeçalhos (numa linha), totais ou notas; as linhas "
                      "dos elementos vêm do modelo.",
                      "Cells of one zone are merged — titles, headings (in one row), totals or notes; the elements' "
                      "rows come from the model."),
    "grid.no_row": ("Só se põem e tiram linhas de título e de notas (as dos elementos vêm do modelo).",
                    "Only title and note rows are added and deleted (the elements' come from the model)."),
    "grid.one_column": ("A tabela fica com uma coluna pelo menos.", "The schedule keeps one column at least."),
    "grid.pick_cell": ("Escolha primeiro uma célula da tabela.", "Choose a cell of the schedule first."),
    "info.table_made_own": ("«{name}» passou a tabela do projeto: já pode unir células, pôr bordas, cores, títulos, "
                            "notas e fórmulas. Ctrl+Z desfaz.",
                            "«{name}» is now a schedule of the project's: merge cells, add borders, colours, titles, "
                            "notes and formulas. Ctrl+Z undoes."),
    "cmd.table_cells": ("Células da tabela", "Schedule cells"),
    "tables.insert": ("Inserir na tabela", "Insert in the schedule"),
    "tables.insert_hint": ("Escolha uma célula na tabela e faça duplo clique no que quer inserir.",
                           "Choose a cell in the schedule and double-click what to insert."),
    "tables.insert_button": ("Inserir", "Insert"),
    "tables.insert_none": ("Abra uma tabela do projeto para inserir campos, funções e linhas (numa lista: "
                           "«Formatar como no Excel»).",
                           "Open a schedule of the project's to insert fields, functions and rows (on a list: "
                           "«Format as in Excel»)."),
    "tables.insert_group.columns": ("Colunas (campos)", "Columns (fields)"),
    "tables.insert_group.functions": ("Funções (na célula)", "Functions (in the cell)"),
    "tables.insert_group.data": ("Dados do projeto (na célula)", "Project data (in the cell)"),
    "tables.insert_group.rows": ("Linhas", "Rows"),
    "sched.count": ("{n} elementos", "{n} elements"),
    "sched.col.name": ("Nome", "Name"),
    "sched.col.type": ("Tipo", "Type"),
    "sched.col.storey": ("Pavimento", "Storey"),
    "sched.col.length": ("Comprimento", "Length"),
    "sched.col.height": ("Altura", "Height"),
    "sched.col.thickness": ("Espessura", "Thickness"),
    "sched.col.width": ("Largura", "Width"),
    "sched.col.area": ("Área", "Area"),
    "sched.col.volume": ("Volume", "Volume"),
    "sched.col.host": ("Parede", "Wall"),
    "sched.col.class": ("Classe IFC", "IFC class"),
    "sched.col.count": ("Quantidade", "Count"),
    "info.schedule_exported": ("Tabela exportada: {f}", "Schedule exported: {f}"),
    # (0.370) the tables as Excel workbooks too
    "sched.table_filter": ("Livro do Excel (*.xlsx);;Tabela CSV para o Excel (*.csv);;"
                           "JSON para outros programas — KazaFix Cost (*.json)",
                           "Excel workbook (*.xlsx);;CSV table for Excel (*.csv);;"
                           "JSON for other programs — KazaFix Cost (*.json)"),
    "err.xlsx_missing": ("Para gravar em Excel (XLSX) é preciso a biblioteca openpyxl, que não está instalada. Grave "
                         "em CSV, que o Excel também abre.",
                         "Saving as Excel (XLSX) needs the openpyxl library, which is not installed. Save as CSV, "
                         "which Excel opens too."),
    "err.table_write": ("Não foi possível gravar «{f}»: {e}. Se estiver aberto no Excel, feche-o e tente outra vez.",
                        "Could not write \"{f}\": {e}. If it is open in Excel, close it and try again."),
    "tool.section": ("Corte", "Section"),
    "tool.dimension": ("Cota", "Dimension"),
    "tool.dim_exterior": ("Cotas exteriores", "Outside dimensions"),             # (0.399)
    "tool.dim_interior": ("Cotas interiores", "Inside dimensions"),              # (0.400)
    # navigation (0.78)
    "tool.orbit": ("Orbitar", "Orbit"),
    "tool.pan": ("Deslocar", "Pan"),
    "tool.zoom": ("Zoom", "Zoom"),
    "tool.zoom_window": ("Zoom janela", "Zoom window"),
    "hint.orbit": ("Orbitar: arraste com o botão esquerdo para rodar à volta do ponto onde carregou (Shift: "
                   "deslocar). Numa planta ou corte só desloca. Espaço volta a Selecionar.",
                   "Orbit: drag with the left button to turn round the point you pressed (Shift: pan). In a plan "
                   "or section it only pans. Space goes back to Select."),
    "hint.pan": ("Deslocar: arraste com o botão esquerdo. Espaço volta a Selecionar.",
                 "Pan: drag with the left button. Space goes back to Select."),
    "hint.zoom": ("Zoom: arraste para cima para aproximar, para baixo para afastar, a partir do ponto onde carregou. "
                  "Espaço volta a Selecionar.",
                  "Zoom: drag up to come closer, down to go back, from the point you pressed. Space goes back to "
                  "Select."),
    "hint.zoom_window": ("Zoom janela: arraste uma caixa (ou clique dois cantos) à volta do que quer ver. Esc "
                         "desiste.",
                         "Zoom window: drag a box (or click two corners) round what you want to see. Esc gives up."),
    "info.zoom_window": ("Vista ajustada à janela (Alt+← volta à anterior).",
                         "View fitted to the window (Alt+← goes back)."),
    "act.zoom_selection": ("Enquadrar a seleção", "Zoom to selection"),
    "act.view_back": ("Vista anterior", "Previous view"),
    "act.view_forward": ("Vista seguinte", "Next view"),
    "menu.navigate": ("Navegação", "Navigation"),
    # the disciplines (0.182: the header's tabs; they replace the work environments of 0.84)
    "menu.disciplines": ("Disciplinas", "Disciplines"),
    "disc.home": ("Início", "Home"),
    "disc.modeling": ("Modelagem", "Modelling"),
    "disc.architecture": ("Arquitetura", "Architecture"),
    "disc.structure": ("Estrutura", "Structure"),
    "disc.services": ("Instalações", "Services"),
    "disc.terrain": ("Terreno", "Terrain"),
    "disc.annotate": ("Anotar", "Annotate"),
    "disc.massing": ("Massa e Estudos", "Massing and studies"),
    "disc.view": ("Visualizar", "View"),
    "disc.manage": ("Gerenciar", "Manage"),
    "disc.render": ("Render", "Render"),
    "disc.collaborate": ("Colaborar", "Collaborate"),
    "disc.insert": ("Inserir", "Insert"),                     # (0.482, as Revit's)
    "disc.analyze": ("Analisar", "Analyze"),                  # (0.482, as Revit's)
    "tip.disc.home": ("Criar, abrir e gravar projetos; exportar; ajuda.",
                      "Make, open and save projects; export; help."),
    "tip.disc.insert": ("Vincular desenhos CAD e nuvens de pontos; importar imagens, modelos 3D, componentes e "
                        "pontos de levantamento.",
                        "Link CAD drawings and point clouds; import pictures, 3D models, components and survey "
                        "points."),
    "tip.disc.analyze": ("Cálculo da estrutura e os seus mapas; o Verificador (regulamentos), IFC e IDS.",
                         "The structure's analysis and its schedules; the Checker (regulations), IFC and IDS."),
    "tip.disc.modeling": ("Operações gerais de criação e edição geométrica.", "General making and editing."),
    "tip.disc.architecture": ("Elementos arquitetónicos: paredes, portas, janelas, coberturas, mobiliário.",
                              "Architectural elements: walls, doors, windows, roofs, furniture."),
    "tip.disc.structure": ("Vigas, paredes, pilares, lajes, fundações e a estrutura proposta de uma vez.",
                           "Beams, walls, columns, slabs, foundations and the structure proposed at once."),
    "tip.disc.services": ("Redes elétricas, de água, de esgoto e AVAC.", "Electrical, water, drainage and HVAC."),
    "tip.disc.terrain": ("Topografia, plataformas, curvas de nível e movimentação de terras.",
                         "Topography, platforms, contour lines and earthworks."),
    "tip.disc.annotate": ("Cotas, desenho, textos, etiquetas e símbolos.", "Dimensions, drafting, texts, tags and "
                                                                           "symbols."),
    "tip.disc.massing": ("Estudos volumétricos: linhas, retângulos, empurrar/puxar; depois classificar em BIM.",
                         "Massing studies: lines, rectangles, push/pull; then classify as BIM."),
    "tip.disc.view": ("Estilos gráficos, tema, render e apresentação, vistas (plantas, cortes, 3D), câmaras e painéis.",
                      "Graphic styles, theme, render and presentation, views (plans, sections, 3D), cameras and "
                      "panels."),
    "tip.disc.manage": ("Tipos, materiais, pavimentos, fases, componentes e grupos.",
                        "Types, materials, storeys, phases, components and groups."),
    "tip.disc.render": ("Imagens e apresentação (Gaussian splat).", "Pictures and presentation (Gaussian splat)."),
    "tip.disc.collaborate": ("Notas, trabalho em equipa e colisões.", "Notes, teamwork and clashes."),
    "notice.close": ("Fechar (Esc)", "Close (Esc)"),          # (0.321) the balloon over the view
    # (0.322) a command asking for the elements it needs
    # (0.326) Copy, Array and the clipboard, as Revit's
    "tool.copy": ("Copiar", "Copy"),
    "tool.array": ("Matriz", "Array"),
    "hint.array_mode": ("MATRIZ DE {n} CÓPIAS, {how} · ", "ARRAY OF {n} COPIES, {how} · "),
    "ctx.array_count": ("Cópias", "Copies"),
    "ctx.array_spread": ("Distância", "Distance"),
    "ctx.array_each": ("Cada uma à distância dada", "Each at the distance given"),
    "ctx.array_divide": ("Repartida até ao ponto dado", "Spread up to the point given"),
    "rpanel.clipboard": ("Copiar e colar", "Copy and paste"),
    "act.copy_clip": ("Copiar para colar", "Copy to paste"),
    "act.paste": ("Colar", "Paste"),
    "act.paste_storeys": ("Colar nos pavimentos…", "Paste on storeys…"),
    "tip.copy_clip": ("Guarda o que está selecionado para o colar a seguir.", "Keeps what is selected, to paste it."),
    "tip.paste": ("O que copiou fica no cursor: um clique põe a cópia.", "What you copied is on the cursor: a click "
                  "puts the copy."),
    "tip.paste_storeys": ("O que copiou, no mesmo sítio, nos pavimentos que escolher (como o «Colar alinhado» do "
                          "Revit).", "What you copied, in the same place, on the storeys you choose (as Revit's "
                          "Paste Aligned)."),
    "info.clip_copied": ("{n} elemento(s) copiado(s): Ctrl+V cola-os onde clicar; Ctrl+Shift+V noutros pavimentos.",
                         "{n} element(s) copied: Ctrl+V pastes them where you click; Ctrl+Shift+V on other storeys."),
    "info.clip_empty": ("Ainda não copiou nada: selecione e carregue em Ctrl+C (ou no botão).",
                        "Nothing copied yet: select and press Ctrl+C (or the button)."),
    "info.clip_gone": ("Os elementos copiados já não existem (foram apagados).",
                       "The elements copied are gone (deleted)."),
    "pick.copy_clip": ("Clique no que quer copiar.", "Click what to copy."),
    "err.component_none_open": ("Não está a editar nenhum componente: para mudar a forma de um, use primeiro Editar "
                                "componente.",
                                "No component is being edited: to change one's shape, use Edit component first."),
    "pick.component_close": ("Clique no componente a fechar (há vários em edição).",
                             "Click the component to close (several are being edited)."),
    # (0.325) small things the sweep of the ribbon found
    "info.storey_top": ("Este é o pavimento mais alto.", "This is the highest storey."),
    "info.storey_bottom": ("Este é o pavimento mais baixo.", "This is the lowest storey."),
    "info.no_columns": ("Não há pilares neste pavimento.", "There are no columns on this storey."),
    "info.no_beams": ("Não há vigas neste pavimento: faça-as entre os pilares.",
                      "There are no beams on this storey: make them between the columns."),
    "info.analytical_empty": ("O modelo analítico ficou vazio: entram pilares, vigas, lajes, sapatas e as paredes "
                              "marcadas «Estrutural (resistente)» nas Propriedades. Marque as paredes de alvenaria "
                              "que suportam a casa, ou proponha uma estrutura de betão a partir das paredes:",
                              "The analytical model is empty: columns, beams, slabs, footings and the walls marked "
                              "«Load bearing» in the Properties go into it. Mark the masonry walls that hold the house, "
                              "or propose a concrete structure from the walls:"),
    "info.analytical_walls": ("Modelo analítico feito: {n} barras, {w} paredes resistentes, {s} apoios.",
                              "Analytical model made: {n} members, {w} load-bearing walls, {s} supports."),
    "pick.delete": ("Clique no que quer apagar.", "Click what to delete."),
    "info.plan_for_tool": ("Isto faz-se numa planta, num corte ou num alçado: abri a planta «{plan}».",
                           "This is done in a plan, a section or an elevation: the plan “{plan}” is open."),
    "pick.keys": ("Escolhidos: {n} · um clique junta ou tira · Enter ou botão direito: continuar · Esc: cancelar",
                  "Chosen: {n} · a click adds or removes · Enter or right button: go on · Esc: cancel"),
    "pick.keys_one": ("Esc: cancelar", "Esc: cancel"),
    "pick.wrong": ("Esse elemento não serve para «{c}».", "That element does not do for “{c}”."),
    "pick.few": ("Falta escolher {n}: clique nele(s) e carregue em Enter.",
                 "{n} more to choose: click it / them and press Enter."),
    "pick.cancelled": ("«{c}» cancelado.", "“{c}” cancelled."),
    "pick.mirror": ("Clique no que quer espelhar.", "Click what to mirror."),
    "pick.scale": ("Clique nos esboços que quer escalar (os elementos BIM têm as medidas dos seus tipos).",
                   "Click the sketches to scale (BIM elements have their types' sizes)."),
    "pick.attach_top": ("Clique nas paredes e pilares cujo topo quer ligar.",
                        "Click the walls and columns whose top to attach."),
    "pick.attach_top_to": ("Agora clique na laje ou cobertura a que o topo se liga.",
                           "Now click the slab or roof the top attaches to."),
    "pick.attach_base": ("Clique nas paredes e pilares cuja base quer ligar.",
                         "Click the walls and columns whose base to attach."),
    "pick.attach_base_to": ("Agora clique na laje ou sapata em que a base assenta.",
                            "Now click the slab or footing the base stands on."),
    "pick.merge": ("Clique nas duas paredes a juntar (em linha, de ponta a ponta).",
                   "Click the two walls to merge (in line, end to end)."),
    "pick.profile_wall": ("Clique na parede reta cujo perfil quer editar.", "Click the straight wall whose profile to edit."),
    "pick.outline": ("Clique na laje, no piso ou no teto cujo contorno quer editar.",
                     "Click the slab, floor finish or ceiling whose outline to edit."),
    "pick.platform": ("Clique no terreno cuja plataforma quer editar.", "Click the terrain whose platform to edit."),
    "pick.combined_footing": ("Clique nos dois pilares da sapata combinada.", "Click the combined footing's two columns."),
    "pick.circuit": ("Clique nas tomadas, interruptores e luminárias do circuito.",
                     "Click the circuit's outlets, switches and lights."),
    "pick.repeat": ("Clique no que quer repetir noutros pavimentos (por exemplo, um grupo).",
                    "Click what to repeat on other storeys (for example, a group)."),
    "pick.component": ("Clique nos volumes de esboço do componente.", "Click the component's sketch volumes."),
    "pick.component_edit": ("Clique na cópia do componente que quer editar.", "Click the copy of the component to edit."),
    "pick.group": ("Clique nos elementos BIM do grupo.", "Click the group's BIM elements."),
    "pick.ungroup": ("Clique num elemento do grupo a desfazer.", "Click an element of the group to ungroup."),
    "pick.face_profile": ("Clique na face plana desenhada (um esboço sem volume) que dá a secção — na horizontal, para "
                          "fora da parede; na vertical, para cima.",
                          "Click the flat face drawn (a sketch with no volume) that gives the section — across, out "
                          "of the wall; up, upwards."),
    "pick.roof_profile_roof": ("Clique na cobertura a refazer pelo perfil.", "Click the roof to make by the profile."),
    "pick.roof_profile_face": ("Agora clique na face plana desenhada que dá o perfil da cobertura.",
                               "Now click the flat face drawn that gives the roof's profile."),
    "pick.box": ("Clique no que quer ver dentro da caixa de corte.", "Click what to see inside the section box."),
    "act.tool_type": ("Editar o tipo em uso…", "Edit the type in use…"),
    # the Properties panel's groups and tabs (0.185, the interface's panel 7)
    "props.g.identity": ("Identificação", "Identity"),
    "props.g.parameters": ("Restrições e dimensões", "Constraints and dimensions"),
    "props.group_tip": ("Clique no título para recolher ou abrir o grupo", "Click the title to fold or open the group"),
    # (0.414) types saved from an element and applied to others (model/element_types)
    "props.no_type": ("(sem tipo)", "(no type)"),
    "props.element_type_tip": ("O tipo deste elemento: escolha outro para lhe aplicar (com vários escolhidos, a todos)",
                               "This element's type: choose another to apply it (several chosen: to all of them)"),
    "props.type_save": ("Guardar como tipo…", "Save as type…"),
    "props.type_save_tip": ("Faz um tipo novo com o que este elemento tem (sem a sua posição nem as suas curvas)",
                            "Makes a new type of what this element has (not its place nor its curves)"),
    "props.type_update": ("Atualizar o tipo", "Update the type"),
    "props.type_update_tip": ("Leva as mudanças deste elemento ao tipo e a todos os elementos desse tipo",
                              "Takes this element's changes to its type and to every element of that type"),
    "ask.type_name": ("Nome do tipo:", "The type's name:"),
    "type.default_name": ("{k} — tipo {n}", "{k} — type {n}"),
    "info.element_type_saved": ("Tipo «{n}» guardado. Escolha-o no topo das Propriedades de outros elementos para "
                                "lhes aplicar. Ctrl+Z desfaz.",
                                "Type “{n}” saved. Choose it at the top of other elements' Properties to apply it. "
                                "Ctrl+Z undoes."),
    "info.type_applied": ("Tipo «{n}» aplicado a {k} elemento(s). Ctrl+Z desfaz.",
                          "Type “{n}” applied to {k} element(s). Ctrl+Z undoes."),
    "info.type_none": ("{n} elemento(s) sem tipo (os valores ficam como estão).",
                       "{n} element(s) with no type (their values stay as they are)."),
    "info.type_updated": ("Tipo «{n}» atualizado: {k} elemento(s) seguem-no. Ctrl+Z desfaz.",
                          "Type “{n}” updated: {k} element(s) follow it. Ctrl+Z undoes."),
    "cmd.type_save": ("Guardar como tipo", "Save as type"),
    "cmd.type_apply": ("Aplicar o tipo", "Apply the type"),
    "cmd.type_update": ("Atualizar o tipo", "Update the type"),
    "refuse.type_name": ("o tipo precisa de um nome", "the type needs a name"),
    "refuse.type_exists": ("já há um tipo com esse nome", "there is a type of that name already"),
    "props.g.materials": ("Materiais e acabamentos (do tipo)", "Materials and finishes (the type's)"),
    "props.g.phase": ("Fase", "Phase"),
    "props.g.ifc": ("Dados IFC e parâmetros", "IFC data and parameters"),
    "props.g.view": ("Vista", "View"),
    "props.search": ("Pesquisar propriedades…", "Search properties…"),
    "props.sketch_kind": ("Esboço", "Sketch"),
    "rib.header": ("Cabeçalho", "Header"),
    "rib.ribbon": ("Ferramentas", "Tools"),
    "rib.panels": ("Painéis", "Panels"),
    "rib.type_lists": ("Tipos para desenhar", "Types to draw with"),
    "rib.more": ("Mais grupos desta fita (a janela é estreita para os mostrar todos)",           # (0.482)
                 "More panels of this tab (the window is too narrow to show them all)"),
    # the ribbon's short names under the icons (the full one in the tooltip)
    "rib.short.save_as": ("Guardar\ncomo", "Save\nas"),
    "rib.short.import_image": ("Imagem\nde fundo", "Background\npicture"),
    "rib.short.terrain_points": ("Pontos de\nlevantamento", "Survey\npoints"),
    "rib.short.terrain_dxf": ("Terreno\nde um DXF", "Terrain\nfrom DXF"),
    "rib.short.cad_link": ("Ligar\nDXF", "Link\nDXF"),
    "rib.short.cloud_link": ("Nuvem\nde pontos", "Point\ncloud"),
    "rib.short.import_components": ("Componentes\nde outro", "Components\nfrom another"),
    "rib.short.pdf": ("Vista\nem PDF", "View\nas PDF"),
    "rib.short.dxf": ("Vista\nem DXF", "View\nas DXF"),
    "rib.short.sheets_pdf": ("Folhas\nem PDF", "Sheets\nas PDF"),
    "rib.short.sheets_by_storey": ("Folhas por\npavimento", "Sheets by\nstorey"),
    "rib.short.splat": ("Gaussian\nsplat", "Gaussian\nsplat"),
    "rib.short.export_image": ("Imagem\nda vista", "View\nimage"),
    "rib.short.element_hatches": ("Tramas por\nelemento", "Hatches by\nelement"),
    "rib.small.reset_patterns": ("Repor padrões", "Reset patterns"),
    "rib.short.help": ("Ajuda", "Help"),
    "rib.short.quit": ("Sair", "Quit"),
    "rib.short.cad_links": ("DXF\nligados", "Linked\nDXFs"),
    "rib.short.cloud_links": ("Nuvens\nligadas", "Linked\nclouds"),
    "rib.short.images": ("Imagens\nde fundo", "Background\npictures"),
    "rib.short.show_analytical": ("Modelo\nanalítico", "Analytical\nmodel"),
    "rib.short.view3d_new": ("Nova\nvista 3D", "New\n3D view"),
    "rib.short.mouse_sketchup": ("Meio\norbita", "Middle\norbits"),
    "rib.short.mouse_revit": ("Meio\ndesloca", "Middle\npans"),
    "rib.short.component_make": ("Fazer\ncomponente", "Make\ncomponent"),
    "rib.short.group_make": ("Fazer\ngrupo", "Make\ngroup"),
    "rib.short.storey_new": ("Novo\npavimento", "New\nstorey"),
    "rib.short.remove_water_proposal": ("Tirar\nproposta", "Remove\nproposal"),
    "rib.short.remove_electrical_proposal": ("Tirar\nproposta", "Remove\nproposal"),
    "rib.short.remove_proposal": ("Tirar\nproposta", "Remove\nproposal"),
    "rib.short.plan": ("Planta", "Plan"),
    "rib.short.dimension_walls": ("Cotar\nparedes", "Dimension\nwalls"),
    "rib.short.renumber": ("Numerar\nvãos", "Number\nopenings"),
    "rib.short.attach_top": ("Ligar\no topo", "Attach\ntop"),
    "rib.short.edit_outline": ("Editar\ncontorno", "Edit\noutline"),
    "rib.short.edit_profile": ("Editar\nperfil", "Edit\nprofile"),
    "rib.short.propose_structure": ("Propor\nestrutura", "Propose\nstructure"),
    "rib.short.footings_under": ("Sapatas sob\npilares", "Footings\nunder"),
    "rib.short.beams_between": ("Vigas entre\npilares", "Beams\nbetween"),
    "rib.short.walls_under_beams": ("Paredes sob\nvigas", "Walls under\nbeams"),
    "rib.short.slabs_in_bays": ("Lajes nos\nvãos", "Slabs in\nbays"),
    "rib.short.columns_on_grid": ("Pilares\nna grelha", "Columns\non grid"),
    "rib.short.connect_network": ("Ligar\nà rede", "Connect\nnetwork"),
    "rib.short.water_proposal": ("Propor\náguas", "Propose\nwater"),
    "rib.short.electrical_proposal": ("Propor\nelétrica", "Propose\nelectrical"),
    "rib.short.reset_profile": ("Repor\nperfil", "Reset\nprofile"),                                  # (0.298)
    "rib.short.detach_top": ("Desligar\no topo", "Detach\ntop"),
    "rib.short.corner_walls": ("Aparar ao\ncanto", "Trim to\ncorner"),
    "rib.short.share": ("Partilhar\nprojeto", "Share\nproject"),
    "rib.short.open_shared": ("Abrir\npartilhado", "Open\nshared"),
    "rib.short.sync": ("Sincronizar", "Synchronise"),
    "rib.short.new_note": ("Nota\nBCF", "BCF\nnote"),
    "rib.short.types": ("Tipos", "Types"),
    "rib.short.grid": ("Eixo", "Grid"),
    "rib.short.clashes": ("Conflitos", "Clashes"),
    "rib.short.site_location": ("Localização", "Location"),
    "rib.short.phase": ("Fases", "Phases"),
    "rib.short.type_lists": ("Tipos para\ndesenhar", "Types to\ndraw"),
    "rib.short.iso": ("Isométrica", "Isometric"),
    "rib.short.graphic_styles": ("Estilos\ngráficos", "Graphic\nstyles"),
    "rib.short.position_camera": ("Câmara", "Camera"),
    "rib.short.analyse": ("Analisar", "Analyse"),
    "rib.short.kitchen": ("Cozinha", "Kitchen"),
    "rib.small.only_active": ("3D: só o pavimento ativo", "3D: active storey only"),
    "rib.small.show_analytical": ("Mostrar analítico", "Show analytical"),
    "rib.small.remove_water_proposal": ("Tirar a proposta", "Remove proposal"),
    "rib.small.remove_electrical_proposal": ("Tirar a proposta", "Remove proposal"),
    "rib.small.repeat": ("Repetir nos pisos", "Repeat on storeys"),
    "rib.small.profile_from_face": ("Perfil de face", "Profile from face"),
    "rib.small.wall_finish": ("Revestimento", "Wall finish"),
    # (0.298) the ribbon's small buttons, an icon beside the name: a name in one line
    "rib.small.terrain_points": ("Levantamento", "Survey points"),
    "rib.small.terrain_dxf": ("Terreno de DXF", "Terrain from DXF"),
    "rib.small.typical": ("Pavimentos iguais", "Typical floors"),
    "rib.small.corner_walls": ("Aparar ao canto", "Trim to corner"),
    "rib.small.verify_ec2": ("Verificar EC2/EC6", "EC2/EC6 check"),
    "rib.small.new_circuit": ("Novo circuito", "New circuit"),
    "rib.small.route_circuits": ("Ligar ao quadro", "Wire to board"),
    "rib.small.electrical_check": ("Verificar instalação", "Check installation"),
    "rib.small.reserve_views": ("Reservar vistas", "Reserve views"),
    "rib.small.give_back": ("Devolver reservas", "Give back"),
    "rib.small.walls_from_cad": ("Modelo do desenho", "Model from drawing"),
    "rib.small.model_from_scan": ("Modelo da nuvem", "Model from cloud"),
    "rib.small.box_selection": ("Caixa à seleção", "Box round selection"),
    "rib.small.zoom_selection": ("Enquadrar seleção", "Zoom to selection"),
    "rib.small.close_view": ("Fechar a vista", "Close view"),
    "rib.small.next_view": ("Vista seguinte", "Next view"),
    "rib.small.prev_view": ("Vista anterior", "Previous view"),
    "rib.small.roof_opening": ("Abertura", "Opening"),
    "rib.small.analytical": ("Modelo analítico", "Analytical model"),
    "rib.small.actions": ("Ações e materiais", "Actions"),
    "rib.small.analyse": ("Analisar", "Analyse"),
    "rib.small.structure_quantities": ("Quantidades", "Quantities"),
    "rib.small.import_components": ("Componentes de outro", "Components from another"),
    "rib.small.check_ids": ("Requisitos IDS", "IDS requirements"),
    "rib.small.missing_data": ("Dados em falta", "Missing data"),
    "rib.small.check_ifc": ("Verificar IFC", "Check IFC"),
    # (0.298) the ribbon's panels, as Revit's: each discipline's tools in named groups, in the order they are used
    "rpanel.file": ("Projeto", "Project"),
    "rpanel.import": ("Importar", "Import"),
    "rpanel.export": ("Exportar", "Export"),
    "rpanel.help": ("Ajuda", "Help"),
    "rpanel.select": ("Selecionar", "Select"),
    "rpanel.draw": ("Desenhar", "Draw"),
    "rpanel.modify": ("Modificar", "Modify"),
    "rpanel.measure": ("Medir", "Measure"),
    "rpanel.paint": ("Materiais", "Materials"),                      # (0.391)
    "rpanel.freeform": ("Formas livres", "Free forms"),              # (0.395)
    "rpanel.create": ("Criar", "Create"),
    "rpanel.project": ("Projeto", "Project"),
    "rpanel.storeys": ("Pavimentos", "Storeys"),
    "rpanel.types": ("Tipos e materiais", "Types and materials"),
    "rpanel.components": ("Componentes", "Components"),
    "rpanel.groups": ("Grupos", "Groups"),
    "rpanel.ai": ("Assistente IA", "AI assistant"),
    "rpanel.image": ("Imagem de fundo", "Background picture"),
    "rpanel.to_bim": ("Passar a BIM", "Into BIM"),
    "rpanel.location": ("Localização", "Location"),
    "rpanel.survey": ("Levantamento", "Survey"),
    "rpanel.platforms": ("Plataformas", "Platforms"),
    "rpanel.earthworks": ("Movimento de terras", "Earthworks"),
    "rpanel.walls": ("Paredes", "Walls"),
    "rpanel.openings": ("Aberturas", "Openings"),
    "rpanel.floors_roofs": ("Pisos e coberturas", "Floors and roofs"),
    "rpanel.circulation": ("Circulação", "Circulation"),
    "rpanel.rooms": ("Ambiente e área", "Room & Area"),               # (0.482: Revit's names)
    "rpanel.furniture": ("Mobiliário", "Furniture"),
    "rpanel.build": ("Construir", "Build"),
    "rpanel.model": ("Modelo", "Model"),
    "rpanel.datum": ("Referência", "Datum"),
    "rpanel.work_plane": ("Plano de trabalho", "Work Plane"),
    "rpanel.structure": ("Estrutura", "Structure"),
    "rpanel.foundation": ("Fundação", "Foundation"),
    "rpanel.connection": ("Ligação", "Connection"),                  # (0.497)
    "rpanel.link": ("Vincular", "Link"),
    "rpanel.symbols": ("Símbolo", "Symbol"),
    # (0.374) the study's ribbon: the Wall's shapes as buttons, the rooms found at once, their areas
    "act.wall_rect": ("Retangular", "Rectangular"),
    "act.wall_circle": ("Circular", "Circular"),
    "act.wall_arc": ("Arco", "Arc"),
    "act.wall_face": ("Por face", "By face"),
    "act.wall_wand": ("Varinha mágica", "Magic wand"),
    "tip.wall_rect": ("Paredes à volta de um retângulo: dois cantos, ou as medidas digitadas (ex.: 5;4).",
                      "Walls round a rectangle: two corners, or its sizes typed (e.g. 5;4)."),
    "tip.wall_circle": ("Paredes num círculo: o centro e o raio.", "Walls on a circle: its centre and radius."),
    "tip.wall_arc": ("Uma parede curva: o início, o fim e a flecha.", "A curved wall: its start, its end, its bulge."),
    "tip.wall_face": ("Paredes ao longo do contorno de uma laje ou de uma face de esboço (um clique).",
                      "Walls along a slab's or a sketch face's outline (one click)."),
    "tip.wall_wand": ("Arraste uma janela sobre as duas linhas de uma parede num desenho (DWG/DXF ligado ou linhas): "
                      "a parede fica entre elas, com a espessura medida.",
                      "Drag a window over a wall's two lines in a drawing (a linked DWG/DXF or lines): the wall goes "
                      "between them, its thickness measured."),
    "act.rooms_identify": ("Identificar", "Identify"),
    "cmd.rooms_identify": ("Identificar ambientes", "Identify rooms"),
    "tip.rooms_identify": ("Um ambiente em cada espaço fechado do pavimento ativo que ainda não tem (paredes, pilares e "
                           "separadores), numerados.",
                           "A room in every closed space of the active storey that has none yet (walls, columns and "
                           "separators), numbered."),
    "act.areas": ("Áreas", "Areas"),
    "tip.areas": ("A área útil (dos ambientes) e a área bruta (por fora das paredes) de cada pavimento.",
                  "The net (the rooms') and gross (outside the walls) area of each storey."),
    "info.rooms_identified": ("{n} ambiente(s) novo(s), numerados. Dê-lhes o nome nas Propriedades.",
                              "{n} new room(s), numbered. Name them in the Properties."),
    "info.rooms_none_new": ("Não há espaços fechados sem ambiente neste pavimento (feche-os com paredes ou "
                            "Separadores).",
                            "There are no closed spaces without a room on this storey (close them with walls or "
                            "Separators)."),
    "areas.storey": ("Pavimento", "Storey"),
    "areas.rooms": ("Ambientes", "Rooms"),
    "areas.net": ("Área útil", "Net area"),
    "areas.gross": ("Área bruta", "Gross area"),
    "areas.total": ("Total", "Total"),
    "areas.note": ("Área útil: a soma dos ambientes. Área bruta: dentro das faces exteriores das paredes.",
                   "Net area: the rooms' sum. Gross area: inside the walls' outer faces."),
    # gutter, elevator, room separators (0.374)
    "tool.gutter": ("Calha", "Gutter"),
    "elem.gutter": ("Calha", "Gutter"),
    "cmd.gutter": ("Calha", "Gutter"),
    # (0.438) a gutter's section — a box or a half-round — and its downpipes
    "cmd.gutter_edit": ("Calha", "Gutter"),
    "ctx.gutter_shape": ("Secção", "Section"),
    "guttershape.caixa": ("Caixa (U)", "Box (U)"),
    "guttershape.meia_cana": ("Meia-cana", "Half-round"),
    "ctx.downpipes": ("Tubos de queda", "Downpipes"),
    "downpipes.nenhum": ("Nenhum", "None"),
    "downpipes.inicio": ("No início", "At its start"),
    "downpipes.fim": ("No fim", "At its end"),
    "downpipes.ambos": ("Nas duas pontas", "At both ends"),
    "hint.gutter": ("Calha: passe o rato por uma cobertura — mostra o beirado mais próximo — e clique: a calha fica ao "
                    "longo dele, por fora, sob a aresta de cima. Clique nos beirados vizinhos: as calhas ligam-se nos "
                    "cantos. Esc: Selecionar.",
                    "Gutter: move over a roof — its nearest eave is shown — and click: the gutter runs along it, "
                    "outside, under its upper edge. Click the eaves next to it: the gutters join at the corners. Esc: "
                    "Select."),
    "tip.gutter": ("Calha de {l}", "{l} gutter"),
    "tip.gutter_joined": ("Calha de {l} — liga-se a {n} calha(s) no canto", "{l} gutter — joins {n} gutter(s) at the "
                          "corner"),
    "info.gutter_joined": ("Ligada no canto a {n} calha(s).", "Joined at the corner to {n} gutter(s)."),
    "err.gutter_roof": ("Clique numa cobertura, perto do beirado.", "Click a roof, near its eave."),
    "info.gutter": ("Calha de {l} no beirado de {roof} (IFC).", "{l} gutter on {roof}'s eave (IFC)."),
    # (0.391) the Paint bucket, as SketchUp's
    "tool.paint": ("Pintura", "Paint"),
    "tip.paint": ("Pinta as faces com um material, como o balde do SketchUp — dos elementos e dos esboços: clique = a "
                  "face, Ctrl = o elemento todo (num esboço: as faces ligadas da mesma cor), Shift = substituir essa "
                  "cor em todo o modelo, Alt = conta-gotas. O material escolhe-se no Navegador de Materiais (um "
                  "clique).",
                  "Paints faces with a material, as SketchUp's bucket — the elements' and the sketches': click = the "
                  "face, Ctrl = the whole element (on a sketch: the joined faces of the same colour), Shift = replace "
                  "that colour in the whole model, Alt = eyedropper. The material is chosen in the Materials Browser "
                  "(one click)."),
    "keys.paint": ("Clique: a face  ·  Ctrl: o elemento / as faces ligadas  ·  Shift: substituir no modelo  ·  Alt: "
                   "conta-gotas  ·  Esc: Selecionar",
                   "Click: the face  ·  Ctrl: the element / the joined faces  ·  Shift: replace in the model  ·  Alt: "
                   "eyedropper  ·  Esc: Select"),
    "hint.paint": ("Pintura ({m}): escolha o material no Navegador de Materiais (à direita) e clique nas faces. Ctrl: o "
                   "elemento todo (num esboço, as faces ligadas da mesma cor); Shift: substituir essa cor em todo o "
                   "modelo; Alt: conta-gotas.",
                   "Paint ({m}): choose the material in the Materials Browser (on the right) and click the faces. Ctrl: "
                   "the whole element (on a sketch, the joined faces of the same colour); Shift: replace that colour "
                   "in the whole model; Alt: eyedropper."),
    "ctx.paint_material": ("Material", "Material"),
    "paint.none": ("Sem pintura", "No paint"),
    "cmd.paint": ("Pintura", "Paint"),
    "tip.paint_face": ("Pintar esta face: {m}", "Paint this face: {m}"),
    "tip.paint_element": ("Pintar o elemento todo: {m}", "Paint the whole element: {m}"),
    "tip.paint_replace": ("Substituir esta cor em todo o modelo por {m}", "Replace this colour in the whole model with "
                                                                          "{m}"),
    "tip.paint_pick": ("Conta-gotas: {m}", "Eyedropper: {m}"),
    "tip.paint_connected": ("Pintar as faces ligadas com a mesma cor: {m}", "Paint the joined faces of the same "
                                                                             "colour: {m}"),
    "info.paint_sketch": ("{n} face(s) de «{name}» pintada(s): {m}. Ctrl+Z desfaz.",
                          "{n} face(s) of “{name}” painted: {m}. Ctrl+Z undoes it."),
    "err.paint_replace": ("Shift substitui uma pintura: esta face não está pintada.",
                          "Shift replaces a paint: this face is not painted."),
    "info.paint_face": ("Face de «{name}» pintada: {m}. Ctrl+Z desfaz.", "A face of “{name}” painted: {m}. Ctrl+Z "
                                                                         "undoes it."),
    "info.paint_element": ("«{name}» pintado todo: {m}.", "“{name}” painted all over: {m}."),
    "info.paint_replace": ("{a} trocado por {m} em {n} elemento(s).", "{a} replaced with {m} in {n} element(s)."),
    "info.paint_picked": ("Conta-gotas: {m} no balde.", "Eyedropper: {m} in the bucket."),
    "props.paint": ("Pintura", "Paint"),
    # (0.390) the organic roof
    "tool.organic_roof": ("Cobertura orgânica", "Organic roof"),
    "tip.organic_roof": ("Uma cobertura curva sobre um contorno desenhado em planta — cúpula, abóbada ou onda, a "
                         "forma tirada do próprio contorno — em casca, gridshell, gridshell com vidro ou pérgola "
                         "curva, com aro e apoios.",
                         "A curved roof over an outline drawn in plan — dome, vault or wave, its form found from the "
                         "outline itself — as a shell, a gridshell, a glazed gridshell or a curved pergola, with a "
                         "ring beam and supports."),
    "keys.organic_roof": ("Clique: pontos  ·  Clique no 1.º ponto ou Enter: fechar  ·  Backspace: tirar o último  ·  "
                          "Botão direito: recomeçar  ·  Esc: Selecionar",
                          "Click: points  ·  Click the 1st point or Enter: close  ·  Backspace: take the last back  ·  "
                          "Right button: start again  ·  Esc: Select"),
    "hint.organic_roof.curvo": ("Cobertura orgânica ({f}, {s}): clique os pontos do contorno no chão — passa uma curva "
                                "suave por eles. Clique no primeiro ponto (ou Enter) para fechar.",
                                "Organic roof ({f}, {s}): click the outline's points on the floor — a smooth curve "
                                "goes through them. Click the first point (or Enter) to close."),
    "hint.organic_roof.poligono": ("Cobertura orgânica ({f}, {s}): clique os cantos do contorno no chão. Clique no "
                                   "primeiro (ou Enter) para fechar.",
                                   "Organic roof ({f}, {s}): click the outline's corners on the floor. Click the first "
                                   "one (or Enter) to close."),
    "hint.organic_roof.retangulo": ("Cobertura orgânica ({f}, {s}): clique dois cantos opostos no chão.",
                                    "Organic roof ({f}, {s}): click two opposite corners on the floor."),
    "hint.organic_roof.circulo": ("Cobertura orgânica ({f}, {s}): clique o centro e depois um ponto da borda.",
                                  "Organic roof ({f}, {s}): click its centre, then a point on its edge."),
    "ctx.organic_mode": ("Contorno", "Outline"),
    "ctx.organic_form": ("Forma", "Form"),
    "ctx.organic_system": ("Sistema", "System"),
    "ctx.organic_eave": ("Beirado", "Eave"),
    "ctx.organic_rise": ("Flecha", "Rise"),
    "ctx.organic_spacing": ("Malha", "Grid"),
    "organic.mode.curvo": ("Curvo", "Curved"),
    "organic.mode.poligono": ("Polígono", "Polygon"),
    "organic.mode.retangulo": ("Retângulo", "Rectangle"),
    "organic.mode.circulo": ("Círculo", "Circle"),
    "organic.form.cupula": ("Cúpula", "Dome"),
    "organic.form.abobada": ("Abóbada", "Vault"),
    "organic.form.onda": ("Onda", "Wave"),
    "organic.system.casca": ("Casca", "Shell"),
    "organic.system.gridshell": ("Gridshell", "Gridshell"),
    "organic.system.envidracada": ("Envidraçada", "Glazed"),
    "organic.system.pergola": ("Pérgola curva", "Curved pergola"),
    "organic.supports.nenhum": ("Nenhum", "None"),
    "organic.supports.cantos": ("Nos cantos", "At the corners"),
    "organic.supports.espacados": ("Espaçados", "Spaced"),
    "tip.organic_close": ("Clique: fechar o contorno", "Click: close the outline"),
    "vcb.organic_area": ("{a} m²", "{a} m²"),
    "info.organic_roof": ("«{name}»: {s} de {a} m², flecha {h}. As medidas estão nas Propriedades; Ctrl+Z desfaz.",
                          "“{name}”: {s} of {a} m², rise {h}. Its measures are in the Properties; Ctrl+Z undoes it."),
    "props.organic_base": ("Nível do beirado", "Eave level"),
    "props.organic_angle": ("Direção da malha", "Grid's direction"),
    "props.organic_thickness": ("Espessura da casca", "Shell thickness"),
    "props.organic_diameter": ("Diâmetro das barras", "Bars' diameter"),
    "props.organic_material": ("Material da estrutura", "Structure's material"),
    "props.organic_material_auto": ("O do sistema ({m})", "The system's ({m})"),
    "props.organic_ring": ("Aro perimetral", "Ring beam"),
    "props.organic_ring_width": ("Largura do aro", "Ring beam width"),
    "props.organic_ring_height": ("Altura do aro", "Ring beam height"),
    "props.organic_supports": ("Apoios", "Supports"),
    "props.organic_support_spacing": ("Espaçamento dos apoios", "Supports' spacing"),
    "props.organic_support_diameter": ("Diâmetro dos apoios", "Supports' diameter"),
    "props.organic_bars": ("Barras", "Bars"),
    "props.organic_bars_v": ("{n} ({l} m)", "{n} ({l} m)"),
    "props.organic_glass": ("Vidro", "Glass"),
    "props.organic_support_count": ("Número de apoios", "Number of supports"),
    "elem.organic_roof": ("Cobertura orgânica", "Organic roof"),
    "cmd.organic_roof": ("Cobertura orgânica", "Organic roof"),
    "cmd.organic_roof_edit": ("Editar cobertura orgânica", "Edit organic roof"),
    "refuse.organic_outline": ("o contorno da cobertura orgânica tem de ser fechado, sem se cruzar, com mais de 1 m²",
                               "the organic roof's outline must be closed, not crossing itself, over 1 m²"),
    "refuse.organic_small": ("essa medida da cobertura orgânica é pequena demais", "that organic roof measure is too "
                                                                                   "small"),
    "refuse.organic_many": ("a cobertura orgânica daria barras demais: aumente o espaçamento",
                            "the organic roof would have too many bars: make the spacing larger"),
    # (0.395) the parametric surface (the addon's «Superfícies Paramétricas»): form first, construction after
    "tool.param_surface": ("Superfície paramétrica", "Parametric surface"),
    "tip.param_surface": ("Uma superfície curva feita das curvas do modelo — loft entre secções, 4 bordos, revolução, "
                          "extrusão, varrimento, tampa sobre um contorno ou uma fórmula —, afinada por modificadores "
                          "(torcer, onda, atrator, dobrar…) e com construção por cima: casca, nervuras, ripas, "
                          "entrelaçado, gridshell, painéis, vidro spider, anel de bordo, pilares. Segue as curvas "
                          "quando as edita.",
                          "A curved surface made of the model's curves — a loft through sections, 4 edges, a "
                          "revolution, an extrusion, a sweep, a cap over an outline or a formula —, tuned by modifiers "
                          "(twist, wave, attractor, bend…) with construction on it: shell, ribs, slats, weave, "
                          "gridshell, panels, spider glass, edge ring, columns. It follows the curves when you edit "
                          "them."),
    "keys.param_surface": ("Clique: escolher curvas  ·  Enter: criar  ·  Backspace: tirar a última  ·  Botão direito: "
                           "recomeçar  ·  Esc: Selecionar",
                           "Click: pick curves  ·  Enter: make it  ·  Backspace: take the last back  ·  Right button: "
                           "start again  ·  Esc: Select"),
    "hint.param_surface.pick": ("Superfície paramétrica ({op}): clique nas curvas de que é feita ({n} escolhida(s)) — "
                                "Enter cria. {need}",
                                "Parametric surface ({op}): click the curves it is made of ({n} picked) — Enter makes "
                                "it. {need}"),
    "hint.param_surface.grid": ("Superfície paramétrica (fórmula): clique dois cantos opostos no chão.",
                                "Parametric surface (formula): click two opposite corners on the floor."),
    "need.param_surface.auto": ("1 curva fechada: tampa; 1 aberta: extrusão; 2 ou mais: loft; 4 que se tocam: 4 "
                                "bordos.", "1 closed curve: cap; 1 open: extrusion; 2 or more: loft; 4 that touch: 4 "
                                           "edges."),
    "need.param_surface.loft": ("Escolha 2 ou mais secções.", "Pick 2 or more sections."),
    "need.param_surface.coons": ("Escolha 4 curvas que se toquem nas pontas.", "Pick 4 curves that touch at their "
                                                                               "ends."),
    "need.param_surface.revolve": ("Escolha o perfil (roda à volta de um eixo vertical no seu início).",
                                   "Pick the profile (it turns round a vertical axis at its start)."),
    "need.param_surface.extrude": ("Escolha o perfil.", "Pick the profile."),
    "need.param_surface.sweep": ("Escolha o caminho e o perfil.", "Pick the path and the profile."),
    "need.param_surface.patch": ("Escolha um contorno fechado.", "Pick a closed outline."),
    "ctx.surface_op": ("Forma", "Form"),
    "ctx.surface_usage": ("Uso", "Use"),
    "ctx.surface_build": ("Construção", "Construction"),
    "ctx.surface_divisions": ("Divisões", "Divisions"),
    "ctx.surface_rise": ("Flecha", "Rise"),
    "ctx.surface_height": ("Altura", "Height"),
    "ctx.surface_angle": ("Volta", "Turn"),
    "surface.op.auto": ("Automática", "Automatic"),
    "surface.op.loft": ("Loft (secções)", "Loft (sections)"),
    "surface.op.coons": ("4 bordos", "4 edges"),
    "surface.op.revolve": ("Revolução", "Revolution"),
    "surface.op.extrude": ("Extrusão", "Extrusion"),
    "surface.op.sweep": ("Varrimento", "Sweep"),
    "surface.op.patch": ("Tampa sobre contorno", "Cap over an outline"),
    "surface.op.grid": ("Fórmula (grelha)", "Formula (grid)"),
    "surface.usage.estrutura": ("Estrutura", "Structure"),
    "surface.usage.cobertura": ("Cobertura", "Roof"),
    "surface.usage.fachada": ("Fachada", "Façade"),
    "surface.usage.pala": ("Pala / brise", "Canopy / brise"),
    "surface.build.none": ("Só a superfície", "The surface only"),
    "surface.build.shell": ("Casca", "Shell"),
    "surface.build.ribs": ("Nervuras", "Ribs"),
    "surface.build.slats": ("Ripas / brise", "Slats / brise"),
    "surface.build.weave": ("Entrelaçado", "Weave"),
    "surface.build.gridshell": ("Gridshell", "Gridshell"),
    "surface.build.edge": ("Anel de bordo", "Edge ring"),
    "surface.build.supports": ("Pilares", "Columns"),
    "surface.build.panels": ("Painéis", "Panels"),
    "surface.build.spider": ("Vidro spider", "Spider glass"),
    "surface.form.cosseno": ("Cosseno", "Cosine"),
    "surface.form.cupula": ("Cúpula (membrana)", "Dome (membrane)"),
    "surface.form.abobada": ("Abóbada", "Vault"),
    "surface.form.onda": ("Onda", "Wave"),
    "surface.form.plano": ("Plana", "Flat"),
    "surface.grid.quadras": ("Quatro lados", "Four sides"),
    "surface.grid.aneis": ("Anéis", "Rings"),
    "surface.mod.displace": ("Deslocar", "Displace"),
    "surface.mod.attractor": ("Atrator", "Attractor"),
    "surface.mod.taper": ("Afunilar", "Taper"),
    "surface.mod.twist": ("Torcer", "Twist"),
    "surface.mod.shear": ("Inclinar", "Shear"),
    "surface.mod.wave": ("Onda", "Wave"),
    "surface.mod.relax": ("Suavizar", "Relax"),
    "surface.mod.bend": ("Dobrar", "Bend"),
    "surface.mod.trim": ("Recortar", "Trim"),
    "act.control_ring": ("Anel de controlo", "Control ring"),
    "tip.control_ring": ("Copia a curva selecionada (a mais alta) 1 m acima, a 75 % do tamanho, e deixa a pilha "
                         "selecionada: repita e depois Superfície paramétrica faz o loft por todas (cúpula, torre).",
                         "Copies the selected curve (the highest) 1 m above, at 75 % of its size, and keeps the stack "
                         "selected: repeat, then Parametric surface lofts through them all (dome, tower)."),
    "cmd.control_ring": ("Anel de controlo", "Control ring"),
    "pick.control_ring": ("Anel de controlo: clique na curva do anel de baixo.",
                          "Control ring: click the curve of the ring below."),
    "info.control_ring": ("Anel de controlo: {n} curvas selecionadas — repita, ou Superfície paramétrica para o loft.",
                          "Control ring: {n} curves selected — repeat, or Parametric surface for the loft."),
    "tip.surface_pick": ("Clique: juntar esta curva", "Click: add this curve"),
    "tip.surface_unpick": ("Clique: tirar esta curva", "Click: take this curve out"),
    "info.param_surface": ("«{name}»: {op}, {a} m². Afine a forma e junte construção nas Propriedades; segue as "
                           "curvas quando as edita; Ctrl+Z desfaz.",
                           "“{name}”: {op}, {a} m². Tune its form and add construction in the Properties; it follows "
                           "the curves when you edit them; Ctrl+Z undoes it."),
    "elem.param_surface": ("Superfície paramétrica", "Parametric surface"),
    "cmd.param_surface": ("Superfície paramétrica", "Parametric surface"),
    "cmd.param_surface_edit": ("Editar superfície paramétrica", "Edit parametric surface"),
    "refuse.surface_no_curves": ("escolha primeiro as curvas (linhas, arcos, Bézier) de que a superfície é feita",
                                 "pick first the curves (lines, arcs, Béziers) the surface is made of"),
    "refuse.surface_empty": ("a superfície não deu nenhuma peça", "the surface made no piece"),
    "props.surface_form": ("Forma", "Form"),
    "props.surface_curves": ("Curvas", "Curves"),
    "props.surface_curves_v": ("{n} ({k} ligada(s) ao modelo)", "{n} ({k} linked to the model)"),
    "props.surface_inputs": ("Parâmetros", "Parameters"),
    "props.surface_modifiers": ("Modificadores", "Modifiers"),
    "props.surface_build": ("Construção", "Construction"),
    "props.surface_add_mod": ("+ Modificador…", "+ Modifier…"),
    "props.surface_add_build": ("+ Construção…", "+ Construction…"),
    "props.surface_none": ("(nenhum)", "(none)"),
    "props.surface_area": ("Área da superfície", "Surface area"),
    "props.surface_parts": ("Peças", "Parts"),
    "props.surface_warning": ("Aviso", "Warning"),
    "props.surface_csv": ("Lista de peças (CSV)…", "Parts list (CSV)…"),
    "props.surface_export": ("Exportar definição…", "Export definition…"),
    "props.surface_import": ("Importar definição…", "Import definition…"),
    "props.surface_text": ("Editar a definição…", "Edit the definition…"),
    "props.surface_file": ("Definição", "Definition"),
    "props.surface_up": ("Subir", "Move up"),
    "props.surface_down": ("Descer", "Move down"),
    "props.surface_remove": ("Tirar", "Remove"),
    "props.surface_on": ("Ligado", "On"),
    "props.surface_formula_tip": ("Um número ou uma fórmula (ex.: 0,3*sin(2*pi*u)). Nomes: os parâmetros e, por ponto, "
                                  "u v x y z i j nu nv.",
                                  "A number or a formula (e.g. 0.3*sin(2*pi*u)). Names: the parameters and, per point, "
                                  "u v x y z i j nu nv."),
    "props.surface_family": ("{n} · {d}", "{n} · {d}"),
    "dlg.surface_csv": ("Lista de peças", "Parts list"),
    "dlg.surface_export": ("Exportar a definição da superfície", "Export the surface's definition"),
    "dlg.surface_import": ("Importar uma definição de superfície", "Import a surface definition"),
    "dlg.surface_text": ("Definição da superfície (JSON)", "Surface definition (JSON)"),
    "info.surface_csv": ("Lista de peças gravada em {path}", "Parts list saved to {path}"),
    "info.surface_export": ("Definição gravada em {path}", "Definition saved to {path}"),
    "err.surface_import": ("Esta definição não serve: {e}", "This definition will not do: {e}"),
    # the fields of the surface's ops, modifiers and construction sections (sfield.<key>) and their choices
    "sfield.u": ("Divisões U", "Divisions U"), "sfield.v": ("Divisões V", "Divisions V"),
    "sfield.rise": ("Flecha", "Rise"), "sfield.form": ("Forma", "Form"), "sfield.grid": ("Grelha", "Grid"),
    "sfield.smooth": ("Suave entre secções", "Smooth across sections"), "sfield.angle": ("Ângulo (°)", "Angle (°)"),
    "sfield.width": ("Largura", "Width"), "sfield.depth": ("Altura da secção", "Section depth"),
    "sfield.grid_depth": ("Profundidade", "Depth"),
    "sfamily.casca": ("Casca", "Shell"), "sfamily.nervura": ("Nervuras", "Ribs"), "sfamily.ripa": ("Ripas", "Slats"),
    "sfamily.fita": ("Fitas", "Strips"), "sfamily.bordo": ("Anel de bordo", "Edge ring"),
    "sfamily.barra": ("Barras", "Bars"), "sfamily.no": ("Nós", "Nodes"), "sfamily.pilar": ("Pilares", "Columns"),
    "sfamily.painel": ("Painéis", "Panels"), "sfamily.painel_metalico": ("Painéis metálicos", "Metal panels"),
    "sfamily.painel_fibrocimento": ("Painéis de fibrocimento", "Fibre cement panels"),
    "sfamily.caixilho": ("Caixilhos", "Frames"), "sfamily.vidro": ("Vidros", "Glass panes"),
    "sfamily.aranha": ("Aranhas", "Spiders"), "sfamily.rotula": ("Rótulas", "Bolts"),
    "sfield.z": ("Altura z (fórmula)", "Height z (formula)"), "sfield.height": ("Altura", "Height"),
    "sfield.thickness": ("Espessura", "Thickness"), "sfield.offset": ("Afastamento", "Offset"),
    "sfield.count_u": ("Quantas em U", "How many in U"), "sfield.count_v": ("Quantas em V", "How many in V"),
    "sfield.count": ("Quantas", "How many"), "sfield.orient": ("Orientação", "Orientation"),
    "sfield.direction": ("Sentido", "Way"), "sfield.amplitude": ("Amplitude", "Amplitude"),
    "sfield.mode": ("Malha", "Lattice"), "sfield.size": ("Secção", "Section"), "sfield.nodes": ("Nós", "Nodes"),
    "sfield.node_size": ("Tamanho dos nós", "Node size"), "sfield.base_z": ("Nível da base", "Base level"),
    "sfield.pattern": ("Padrão", "Pattern"), "sfield.gap": ("Junta", "Joint"),
    "sfield.max_warp": ("Empeno admissível", "Allowed warp"), "sfield.kind": ("Tipo", "Kind"),
    "sfield.frame": ("Caixilho", "Frame"), "sfield.fill": ("Preencher (fórmula)", "Fill (formula)"),
    "sfield.open": ("Abertura (fórmula)", "Opening (formula)"), "sfield.mask": ("Imagem", "Picture"),
    "sfield.mask_invert": ("Inverter a imagem", "Invert the picture"), "sfield.perf": ("Perfuração fina", "Fine "
                                                                                                         "perforation"),
    "sfield.perf_spacing": ("Espaçamento dos furos", "Holes' spacing"), "sfield.perf_min": ("Furo mínimo", "Smallest "
                                                                                                           "hole"),
    "sfield.perf_max": ("Furo máximo", "Largest hole"), "sfield.perf_margin": ("Margem", "Margin"),
    "sfield.arm": ("Afastamento do vidro", "Glass stand-off"), "sfield.reach": ("Alcance dos braços", "Arms' reach"),
    "sfield.material": ("Material", "Material"), "sfield.along": ("Direção", "Direction"),
    "sfield.amount": ("Quanto", "Amount"), "sfield.point": ("Ponto (x, y, z)", "Point (x, y, z)"),
    "sfield.curve": ("Curva", "Curve"), "sfield.falloff": ("Decaimento", "Falloff"), "sfield.radius": ("Raio",
                                                                                                    "Radius"),
    "sfield.axis": ("Eixo", "Axis"), "sfield.factor": ("Fator", "Factor"), "sfield.by": ("Segundo", "By"),
    "sfield.phase": ("Fase (voltas)", "Phase (turns)"), "sfield.u_waves": ("Ondas em U", "Waves in U"),
    "sfield.v_waves": ("Ondas em V", "Waves in V"), "sfield.iterations": ("Passagens", "Passes"),
    "sfield.toward": ("Para", "Toward"), "sfield.keep": ("Manter", "Keep"),
    "schoice.center": ("Ao centro", "Centred"), "schoice.out": ("Por fora", "Outside"),
    "schoice.in": ("Por dentro", "Inside"), "schoice.normal": ("Normal à superfície", "Normal to the surface"),
    "schoice.vertical": ("Vertical", "Plumb"), "schoice.smooth": ("Sem torcer", "Without spin"),
    "schoice.u": ("U", "U"), "schoice.v": ("V", "V"), "schoice.x": ("X", "X"), "schoice.y": ("Y", "Y"),
    "schoice.z": ("Z", "Z"), "schoice.quad": ("Quadrada", "Square"), "schoice.tri": ("Triangular", "Triangular"),
    "schoice.diagrid": ("Diagrid", "Diagrid"), "schoice.hex": ("Hexagonal", "Hexagonal"),
    "schoice.solid": ("Painel", "Panel"), "schoice.glass": ("Vidro", "Glass"), "schoice.metal": ("Metálico", "Metal"),
    "schoice.fibro": ("Fibrocimento", "Fibre cement"), "schoice.gauss": ("Suave (Gauss)", "Smooth (Gauss)"),
    "schoice.linear": ("Linear", "Linear"), "schoice.inverse": ("Inverso", "Inverse"),
    "schoice.inside": ("Dentro", "Inside"), "schoice.outside": ("Fora", "Outside"),
    # (0.389) the perforated panel as a command of its own
    "tool.perforated_panel": ("Painel perfurado", "Perforated panel"),
    "tip.perforated_panel": ("Um painel perfurado numa parede: clique na face (toda ela) ou arraste de um canto ao "
                             "outro (um retângulo). Furos redondos ou quadrados, em malha reta ou a 45°, painéis com "
                             "junta; uma imagem pode fazer os furos maiores onde é escura. Pronto para o DXF da CNC.",
                             "A perforated panel on a wall: click its face (all of it) or drag from one corner to the "
                             "other (a rectangle). Round or square holes, on a straight or 45° grid, boards with a "
                             "joint; a picture can make the holes bigger where it is dark. Ready for the CNC's DXF."),
    "elem.perforated": ("Painel perfurado", "Perforated panel"),
    "cmd.perforated": ("Painel perfurado", "Perforated panel"),
    "keys.perforated_panel": ("Clique: a face inteira  ·  Arraste: um retângulo  ·  Clique num painel: escolhê-lo  ·  "
                              "Esc: Selecionar",
                              "Click: the whole face  ·  Drag: a rectangle  ·  Click a panel: choose it  ·  Esc: Select"),
    "hint.perforated_panel": ("Painel perfurado (furos {h} de {d}, passo {p}): passe o rato por uma parede e clique — "
                              "a face inteira — ou arraste de um canto ao outro — um retângulo. Clique num painel "
                              "perfurado para o escolher. Esc: Selecionar.",
                              "Perforated panel ({h} holes of {d}, pitch {p}): move over a wall and click — the whole "
                              "face — or drag from one corner to the other — a rectangle. Click a perforated panel to "
                              "choose it. Esc: Select."),
    "tip.perforated_whole": ("Clique: a face inteira · arraste: um retângulo", "Click: the whole face · drag: a "
                                                                              "rectangle"),
    "tip.perforated_pick": ("Clique: escolher este painel", "Click: choose this panel"),
    "info.perforated_picked": ("«{name}» escolhido: as medidas estão nas Propriedades.",
                               "“{name}” chosen: its measures are in the Properties."),
    "info.perforated": ("«{name}» na parede «{wall}»: {n} furos, {a} % de área aberta. Ctrl+Z desfaz.",
                        "“{name}” on the wall “{wall}”: {n} holes, {a} % open area. Ctrl+Z undoes it."),
    "err.perforated_small": ("O retângulo tem de ter pelo menos 5 cm de cada lado.",
                             "The rectangle must be at least 5 cm each way."),
    "warn.hole_pitch": ("Com furos de {d} o passo ({p}) tem de ser maior: assim não cabe nenhum furo.",
                        "With {d} holes the pitch ({p}) must be larger: no hole fits as it is."),
    # (0.441) a free-standing slatted screen
    "tool.ripado_screen": ("Ripado solto", "Slatted screen"),
    "tip.ripado_screen": ("Um ripado sem parede atrás — uma divisória ou um brise —, desenhado como uma parede: clique "
                          "no início e no fim (ou escreva o comprimento). Altura, ripas, moldura e fixações na barra.",
                          "A slatted screen with no wall behind it — a divider or a brise —, drawn as a wall: click its "
                          "start and its end (or type its length). Height, slats, frame and battens on the bar."),
    "hint.ripado_screen": ("Ripado solto ({h} de altura, ripas de {w}, passo {p}): clique no início da linha.",
                           "Slatted screen ({h} high, {w} slats, pitch {p}): click the start of its line."),
    "hint.ripado_screen_2": ("Clique no fim do ripado (ou escreva o comprimento e Enter).",
                             "Click the end of the screen (or type its length and Enter)."),
    "info.ripado_screen": ("«{name}» feito: {l} de comprimento, {n} ripas. Ctrl+Z desfaz.",
                           "“{name}” made: {l} long, {n} slats. Ctrl+Z undoes."),
    "props.screen_length": ("Comprimento", "Length"),
    # (0.440) loose furniture of the program's own
    "tool.loose_furniture": ("Mobiliário solto", "Loose furniture"),
    "tip.loose_furniture": ("Camas, mesas de cabeceira, sofás, poltrona, cadeira, mesas, secretária, estante, móvel de "
                            "TV e plantas em vaso: escolha a peça na barra, ajuste as medidas e clique na planta. R roda, "
                            "Espaço muda o ponto. As camas e os sofás contam no Verificador.",
                            "Beds, bedside tables, sofas, an armchair, a chair, tables, a desk, a bookcase, a TV unit and "
                            "potted plants: choose the piece on the bar, set its sizes and click on the plan. R turns it, "
                            "Space changes its point. The beds and sofas count in the Checker."),
    "keys.loose_furniture": ("Clique: pôr a peça  ·  R / Shift+R: rodar  ·  Espaço: o ponto  ·  Esc: Selecionar",
                             "Click: put the piece  ·  R / Shift+R: turn  ·  Space: its point  ·  Esc: Select"),
    "hint.loose_furniture": ("{name} ({w} × {d}, {h} de altura): clique onde fica. R roda · Espaço: o ponto · Esc: "
                             "Selecionar.",
                             "{name} ({w} × {d}, {h} high): click where it goes. R turns it · Space: its point · Esc: "
                             "Select."),
    "info.loose": ("«{name}» ({w} × {d}) posta. Ctrl+Z desfaz.", "“{name}” ({w} × {d}) put. Ctrl+Z undoes."),
    "ctx.loose_piece": ("Peça", "Piece"),
    "props.depth": ("Profundidade", "Depth"),
    "props.loose_piece": ("Peça de mobiliário", "Furniture piece"),
    "loosegroup.bedroom": ("Quarto", "Bedroom"),
    "loosegroup.living": ("Sala", "Living room"),
    "loosegroup.dining": ("Jantar", "Dining"),
    "loosegroup.office": ("Escritório", "Study"),
    "loosegroup.other": ("Outros", "Other"),
    "cmd.loose": ("Mobiliário solto", "Loose furniture"),
    "cmd.loose_edit": ("Mobiliário solto", "Loose furniture"),
    "refuse.loose_bad": ("essa peça não existe no catálogo", "there is no such piece in the catalogue"),
    "refuse.loose_size": ("cada medida da peça tem de estar entre 15 cm e 4 m",
                          "each of the piece's sizes must be between 15 cm and 4 m"),
    # (0.434) the addon's «Ripado» as a command of its own
    "tool.ripado_panel": ("Ripado", "Slatted panel"),
    "tip.ripado_panel": ("Um ripado numa parede: clique na face (toda ela) ou arraste de um canto ao outro (um "
                         "retângulo). Ripas na vertical ou na horizontal, com a largura, a espessura e o passo; uma "
                         "moldura à volta e ripas de fixação por trás, como no addon. Entra na lista de corte.",
                         "A slatted panel on a wall: click its face (all of it) or drag from one corner to the other (a "
                         "rectangle). Slats upright or level, of a width, a thickness and a pitch; a frame round it and "
                         "battens behind, as the addon's. It goes in the cut list."),
    "elem.ripado": ("Ripado", "Slatted panel"),
    "cmd.ripado": ("Ripado", "Slatted panel"),
    "keys.ripado_panel": ("Clique: a face inteira  ·  Arraste: um retângulo  ·  Clique num ripado: escolhê-lo  ·  "
                          "Esc: Selecionar",
                          "Click: the whole face  ·  Drag: a rectangle  ·  Click a slatted panel: choose it  ·  "
                          "Esc: Select"),
    "hint.ripado_panel": ("Ripado (ripas de {w} × {d}, passo {p}): passe o rato por uma parede e clique — a face "
                          "inteira — ou arraste de um canto ao outro — um retângulo. Clique num ripado para o escolher. "
                          "Esc: Selecionar.",
                          "Slatted panel ({w} × {d} slats, pitch {p}): move over a wall and click — the whole face — or "
                          "drag from one corner to the other — a rectangle. Click a slatted panel to choose it. "
                          "Esc: Select."),
    "tip.ripado_pick": ("Clique: escolher este ripado", "Click: choose this slatted panel"),
    "info.ripado_picked": ("«{name}» escolhido: as medidas estão nas Propriedades.",
                           "“{name}” chosen: its measures are in the Properties."),
    "info.ripado": ("«{name}» na parede «{wall}»: {n} ripas. Ctrl+Z desfaz.",
                    "“{name}” on the wall “{wall}”: {n} slats. Ctrl+Z undoes it."),
    "warn.slat_pitch": ("Com ripas de {w} o passo ({p}) tem de ser maior: as ripas ficariam umas sobre as outras.",
                        "With {w} slats the pitch ({p}) must be larger: the slats would overlap."),
    "props.slat_depth": ("Espessura da ripa", "Slat thickness"),
    "props.slat_pitch": ("Passo", "Pitch"),
    "props.ripado_frame": ("Moldura", "Frame"),
    "props.ripado_frame_tip": ("A largura da moldura à volta do ripado; 0: sem moldura",
                               "The width of the frame round the panel; 0: no frame"),
    "props.ripado_battens": ("Ripas de fixação", "Battens"),
    "props.batten_w": ("Largura da fixação", "Batten width"),
    "props.batten_d": ("Espessura da fixação", "Batten thickness"),
    "ripado.no_battens": ("Sem fixação", "None"),
    "refuse.ripado_frame": ("a moldura não deixa espaço para as ripas", "the frame leaves no room for the slats"),
    "ctx.hole_shape": ("Furos", "Holes"),
    "ctx.hole_grid": ("Malha", "Grid"),
    "ctx.hole_size": ("Ø", "Ø"),
    "ctx.hole_pitch": ("Passo", "Pitch"),
    "ctx.hole_margin": ("Margem", "Margin"),
    "ctx.sheet_w": ("Painel", "Board"),
    "ctx.sheet_h": ("×", "×"),
    "ctx.sheet_joint": ("Junta", "Joint"),
    "ctx.mask": ("Imagem", "Picture"),
    "mask.none": ("Nenhuma", "None"),
    "mask.choose": ("Escolher imagem…", "Choose a picture…"),
    "hole.redondo": ("Redondos", "Round"),
    "hole.quadrado": ("Quadrados", "Square"),
    "grid.reta": ("Reta", "Straight"),
    "grid.diagonal": ("A 45°", "At 45°"),
    "dlg.mask_image": ("Imagem dos furos (escuro: furos grandes)", "The holes' picture (dark: big holes)"),
    "dlg.images": ("Imagens", "Pictures"),
    "props.hole_shape": ("Forma dos furos", "Holes' shape"),
    "props.hole_grid": ("Malha dos furos", "Holes' grid"),
    "props.sheet_w": ("Largura dos painéis", "Boards' width"),
    "props.sheet_h": ("Altura dos painéis", "Boards' height"),
    "props.sheet_joint": ("Junta entre painéis", "Joint between boards"),
    "props.mask": ("Imagem dos furos", "Holes' picture"),
    "props.mask_missing": ("{f} (não encontrada: furos iguais)", "{f} (not found: equal holes)"),
    "props.mask_clear": ("Tirar a imagem", "Remove the picture"),
    "props.region_start": ("Início na parede", "Start on the wall"),
    "props.region_end": ("Fim na parede", "End on the wall"),
    "props.region_base": ("Base", "Base"),
    "props.region_top": ("Topo", "Top"),
    "props.region_whole": ("Cobre", "Covers"),
    "props.region_whole_v": ("A face inteira (segue a parede)", "The whole face (follows the wall)"),
    "tool.elevator": ("Elevador", "Elevator"),
    "elem.elevator": ("Elevador", "Elevator"),
    "cmd.elevator": ("Elevador", "Elevator"),
    "ctx.elevator_width": ("Largura da caixa", "Shaft width"),
    "ctx.elevator_depth": ("Profundidade", "Depth"),
    "hint.elevator": ("Elevador (caixa {w} × {d}): clique no canto da frente à esquerda; R roda 90°. Sobe até acima "
                      "do último pavimento. Esc: Selecionar.",
                      "Elevator ({w} × {d} shaft): click its front left corner; R turns it 90°. It goes up over the "
                      "top storey. Esc: Select."),
    "info.elevator": ("Elevador de {w} × {d} (caixa e cabina, IFC). Abra as lajes por cima dele com «Abertura na "
                      "cobertura».",
                      "{w} × {d} elevator (shaft and car, IFC). Open the slabs over it with «Roof opening»."),
    "tool.room_separator": ("Separador", "Separator"),
    "elem.separator": ("Separador", "Separator"),
    "cmd.separator": ("Separador de ambientes", "Room separator"),
    "hint.separator": ("Separador: clique onde começa a linha que divide dois ambientes sem parede.",
                       "Separator: click where the line dividing two rooms with no wall starts."),
    "hint.separator_next": ("Clique onde acaba (e continue); Esc termina. Os ambientes acompanham.",
                            "Click where it ends (and go on); Esc ends. The rooms follow."),
    "info.separator": ("Separador de {l}: os ambientes deste pavimento acompanham.",
                       "{l} separator: the rooms of this storey follow."),
    "rpanel.grid": ("Grelha", "Grid"),
    "rpanel.elements": ("Elementos", "Elements"),
    "rpanel.automatic": ("Automático", "Automatic"),
    "rpanel.analysis": ("Cálculo", "Analysis"),
    "rpanel.documents": ("Mapas", "Schedules"),
    "rpanel.water": ("Águas e esgotos", "Water and drainage"),
    "rpanel.hvac": ("AVAC", "HVAC"),
    "rpanel.electrical": ("Eletricidade", "Electrical"),
    "rpanel.coordination": ("Coordenação", "Coordination"),
    "rpanel.team": ("Equipa", "Team"),
    "rpanel.links": ("Vínculos", "Links"),
    "rpanel.check": ("Verificar", "Check"),
    "rpanel.notes": ("Notas", "Notes"),
    "rpanel.views": ("Vistas", "Views"),
    "rpanel.dimensions": ("Cotas", "Dimensions"),
    "rpanel.drafting": ("Desenho", "Drafting"),
    "rpanel.tags": ("Etiquetas e tabelas", "Tags and tables"),
    "rpanel.views3d": ("Vistas 3D", "3D views"),
    "rpanel.plans": ("Plantas e cortes", "Plans and sections"),
    "rpanel.look": ("Gráficos", "Graphics"),                                               # (0.482: Revit's)
    "rpanel.camera": ("Câmara", "Camera"),
    "rpanel.windows": ("Janelas", "Windows"),
    "rpanel.mouse": ("Rato", "Mouse"),
    "rpanel.theme": ("Tema", "Theme"),                                                       # (0.338)
    "rpanel.present": ("Apresentação", "Presentation"),
    "rpanel.geometry": ("Geometria", "Geometry"),                                          # (0.482: Revit's)
    "rpanel.trim": ("Dividir e aparar", "Split and trim"),
    "rpanel.wall_edit": ("Modificar parede", "Modify wall"),
    "rpanel.wall_dims": ("Cotas temporárias", "Temporary dimensions"),
    "rpanel.finishes": ("Acabamentos", "Finishes"),
    "rpanel.openings_finishes": ("Vãos e acabamentos", "Openings and finishes"),
    "rpanel.dims": ("Cotas", "Dimensions"),
    "rib.folded": ("{p} — as ferramentas do painel (a janela é estreita para as mostrar todas)",
                   "{p} — the panel's tools (the window is too narrow to show them all)"),
    # (0.298) the contextual tabs, as Revit's: they come with what is selected
    "ctxtab.walls": ("Modificar | Paredes", "Modify | Walls"),
    "tip.ctxtab.walls": ("Os modificadores das paredes selecionadas. Aparece quando se selecionam paredes e sai "
                         "quando a seleção se esvazia (Esc).",
                         "The modifiers of the walls selected. It comes when walls are selected and goes when the "
                         "selection is emptied (Esc)."),
    "act.mouse_sketchup": ("Botão do meio orbita (como no SketchUp)", "Middle button orbits (as in SketchUp)"),
    "act.mouse_revit": ("Botão do meio desloca (como no Revit)", "Middle button pans (as in Revit)"),
    "info.mouse_sketchup": ("Botão do meio: orbitar; Shift + botão do meio: deslocar.",
                            "Middle button: orbit; Shift + middle button: pan."),
    "info.mouse_revit": ("Botão do meio: deslocar; Shift + botão do meio: orbitar.",
                         "Middle button: pan; Shift + middle button: orbit."),
    # (0.338) the interface's theme, on this computer
    "act.theme_light": ("Tema claro", "Light theme"),
    "act.theme_dark": ("Tema escuro", "Dark theme"),
    # (0.374) the palettes of the owner's interface study, and «Explorar cores»
    "act.theme_revit": ("Azul · Revit", "Blue · Revit"),
    "tip.theme_revit": ("A paleta azul-acinzentada inspirada no Revit.", "The slate-blue palette inspired by Revit."),
    "info.theme_revit": ("Paleta Azul Revit. Fica assim neste computador.", "Revit Blue palette. Kept on this computer."),
    "act.theme_bege": ("Bege", "Beige"),
    "act.theme_areia": ("Areia", "Sand"),
    "act.theme_pedra": ("Pedra", "Stone"),
    "act.theme_escuro": ("Escuro", "Dark brown"),
    "act.theme_grafite": ("Grafite", "Graphite"),
    "act.theme_studio": ("Explorar cores…", "Explore colours…"),
    "menu.study_palettes": ("Paletas (Bege, Areia, Pedra, Escuro, Grafite)", "Palettes (Beige, Sand, Stone, Dark, "
                                                                            "Graphite)"),
    "tip.theme_menu": ("Tema e cores da interface: claro, escuro, as paletas Bege, Areia, Pedra, Escuro e Grafite, "
                       "Explorar cores…",
                       "The interface's theme and colours: light, dark, the Beige, Sand, Stone, Dark and Graphite "
                       "palettes, Explore colours…"),
    "tip.theme_bege": ("A paleta bege do estudo de interface (fica neste computador).",
                       "The interface study's beige palette (kept on this computer)."),
    "tip.theme_areia": ("A paleta areia do estudo de interface.", "The interface study's sand palette."),
    "tip.theme_pedra": ("A paleta pedra do estudo de interface.", "The interface study's stone palette."),
    "tip.theme_escuro": ("A paleta escura (castanho) do estudo de interface.",
                         "The interface study's dark (brown) palette."),
    "tip.theme_grafite": ("A paleta grafite do estudo de interface.", "The interface study's graphite palette."),
    "tip.theme_studio": ("Afinar as nove cores da interface (barra, fita, painéis, cabeçalhos, destaque, texto, área "
                         "de desenho, divisórias, campos) e guardá-las neste computador.",
                         "Tune the interface's nine colours (bar, ribbon, panels, headers, accent, text, drawing area, "
                         "dividers, fields) and keep them on this computer."),
    "info.theme_bege": ("Paleta bege. Fica assim neste computador.", "Beige palette. Kept on this computer."),
    "info.theme_areia": ("Paleta areia. Fica assim neste computador.", "Sand palette. Kept on this computer."),
    "info.theme_pedra": ("Paleta pedra. Fica assim neste computador.", "Stone palette. Kept on this computer."),
    "info.theme_escuro": ("Paleta escura. Fica assim neste computador.", "Dark palette. Kept on this computer."),
    "info.theme_grafite": ("Paleta grafite. Fica assim neste computador.", "Graphite palette. Kept on this computer."),
    "info.theme_personalizado": ("A sua paleta. Fica assim neste computador.", "Your palette. Kept on this computer."),
    "studio.intro": ("Ajuste as cores da interface; ficam guardadas neste computador. Comece por uma paleta do estudo.",
                     "Adjust the interface's colours; they are kept on this computer. Start from one of the study's "
                     "palettes."),
    "studio.base": ("Barra e fundo", "Bar and background"),
    "studio.ribbon": ("Fita", "Ribbon"),
    "studio.panel": ("Painéis", "Panels"),
    "studio.header": ("Cabeçalhos", "Headers"),
    "studio.accent": ("Destaque", "Accent"),
    "studio.text": ("Texto", "Text"),
    "studio.canvas": ("Área de desenho", "Drawing area"),
    "studio.line": ("Divisórias", "Dividers"),
    "studio.field": ("Campos", "Fields"),
    "studio.copy": ("Copiar paleta CSS", "Copy CSS palette"),
    "studio.reset": ("Repor bege", "Reset beige"),
    "studio.close": ("Fechar", "Close"),
    "studio.applied": ("Paleta aplicada.", "Palette applied."),
    "studio.kept": ("Cor mudada: a sua paleta fica guardada neste computador.",
                    "Colour changed: your palette is kept on this computer."),
    "studio.copied": ("Paleta CSS copiada.", "CSS palette copied."),
    "studio.bad_code": ("Use um código hexadecimal, por exemplo #D9C5AE.", "Use a hex code, e.g. #D9C5AE."),
    "info.theme_light": ("Tema claro. Fica assim neste computador.", "Light theme. Kept on this computer."),
    "info.theme_dark": ("Tema escuro. Fica assim neste computador; as vistas e as folhas continuam em papel branco "
                        "(para as vistas escuras: Visualizar ▸ Tema ▸ Vistas escuras).",
                        "Dark theme. Kept on this computer; the views and the sheets stay on white paper (for dark "
                        "views: View ▸ Theme ▸ Dark views)."),
    # (0.341) the views' background dark, apart from the interface's theme (as Revit's canvas theme)
    "act.canvas_dark": ("Vistas escuras", "Dark views"),
    "tip.canvas_dark": ("O fundo das vistas (3D, plantas, cortes e alçados) escuro, com as linhas e os textos claros. "
                        "À parte do tema da interface; as folhas e o que se exporta continuam em papel branco.",
                        "The views' background (3D, plans, sections and elevations) dark, the lines and texts light. "
                        "Apart from the interface's theme; the sheets and what is exported stay on white paper."),
    "info.canvas_dark": ("Vistas escuras: o fundo escuro, as linhas e os textos claros. Fica assim neste computador; "
                         "as folhas e o que se exporta continuam em papel branco.",
                         "Dark views: a dark background, light lines and texts. Kept on this computer; the sheets "
                         "and what is exported stay on white paper."),
    "info.canvas_light": ("Vistas claras, como em papel.", "Light views, as on paper."),
    "info.zoom_all_no_selection": ("Nada selecionado: enquadrado tudo.", "Nothing selected: zoomed to everything."),
    "info.no_view_back": ("Não há vista anterior.", "There is no previous view."),
    "info.no_view_forward": ("Não há vista seguinte.", "There is no next view."),
    # walking through (0.80)
    "tool.position_camera": ("Posicionar câmara", "Position camera"),
    "tool.look_around": ("Olhar em volta", "Look around"),
    "tool.walk": ("Caminhar", "Walk"),
    "tool.room": ("Ambiente", "Room"),          # (0.357: «Ambiente», interior or exterior — was «Sala»)
    "hint.room": ("Ambiente: clique dentro das paredes para fazer o ambiente (o contorno aparece debaixo do rato). "
                  "Ele acompanha as paredes. Esc: Selecionar.",
                  "Room: click inside the walls to make the room (its outline shows under the mouse). It follows "
                  "the walls. Esc: Select."),
    "keys.room": ("Clique dentro de paredes fechadas  ·  Esc: Selecionar", "Click inside closed walls  ·  Esc: Select"),
    "err.room_open": ("Aqui não há um ambiente fechado por paredes (ou o clique foi numa parede).",
                      "There is no room closed by walls here (or the click was on a wall)."),
    "info.room": ("Ambiente n.º {n} — {name}: {a} m². Mude o nome no painel Propriedades (clique no ambiente com "
                  "Selecionar). Ctrl+Z desfaz.",
                  "Room no. {n} — {name}: {a} m². Change its name in the Properties panel (click the room with "
                  "Select). Ctrl+Z undoes."),
    "props.room": ("Ambiente", "Room"),
    "props.rooms": ("{n} ambientes selecionados", "{n} rooms selected"),
    "props.room_name": ("Nome", "Name"),
    "props.room_where": ("Interior ou exterior", "Interior or exterior"),                           # (0.357)
    "props.room_interior": ("Interior", "Interior"),
    "props.room_exterior": ("Exterior (terraço, varanda, pátio…)", "Exterior (terrace, porch, yard…)"),
    "props.room_exterior_short": ("exterior", "exterior"),
    # (0.357) the programme (programa de necessidades)
    "act.room_program": ("Programa de necessidades", "Room programme"),
    "tip.room_program": ("O programa de necessidades no painel lateral (Ambientes): a lista dos ambientes de cada piso, "
                         "com o uso e a área pretendida. Clique num ambiente da lista e depois dentro das paredes para "
                         "o colocar (ou arraste-o para lá): verde quando a área é atingida, laranja para verificar, "
                         "vermelho nas zonas conflitantes.",
                         "The room programme in the side panel (Rooms): each storey's rooms, with their use and the "
                         "area wanted. Click a room of the list, then inside walls to place it (or drag it there): "
                         "green when the area is reached, orange to check, red for conflicting zones."),
    "program.title": ("Ambientes — programa de necessidades", "Rooms — programme"),
    "program.hint": ("Clique num ambiente e depois dentro das paredes para o colocar (ou arraste-o). Verde: meta "
                     "atingida · laranja: verificar · vermelho: zonas conflitantes.",
                     "Make each storey's list of rooms. Click a room, then inside the plan's walls to place it — or "
                     "drag it there. Green: area reached · Orange: to check · Red: conflicting zones."),
    "program.import": ("Importar…", "Import…"),
    "program.import_tip": ("Uma lista num ficheiro: CSV ou texto (nome; área; quantidade; interior/exterior), ou JSON "
                           "(por exemplo feito com uma IA — veja «Pedir à IA…»).",
                           "A list in a file: CSV or text (name; area; how many; interior/exterior), or JSON (for "
                           "instance made with an AI — see «Ask an AI…»)."),
    "program.clear": ("Limpar", "Clear"),
    "program.filter": ("Programa (*.json *.csv *.txt)", "Programme (*.json *.csv *.txt)"),
    "program.col.name": ("Ambiente", "Room"),
    "program.col.use": ("Uso", "Use"),
    "program.col.area_short": ("Pretendida", "Wanted"),
    "program.col.area": ("Área pretendida", "Area wanted"),
    "program.col.made": ("Feitos", "Made"),
    "program.col.made_area": ("Feito", "Made"),
    "program.drag_tip": ("Clique e depois clique dentro das paredes da planta — ou arraste «{name}» para lá.",
                         "Click, then click inside the plan's walls — or drag «{name}» there."),
    "program.totals": ("{n} ambientes, {done} com a meta atingida. Área pretendida {a}; feita {m}.",
                       "{n} rooms, {done} with their goal reached. Area wanted {a}; made {m}."),
    "program.empty": ("Sem ambientes neste piso: «+ Ambiente», ou importe uma lista (Importar…).",
                      "No rooms on this storey: «+ Room», or import a list (Import…)."),
    "program.building": ("Edifício", "Building"),
    "program.storey": ("Piso", "Storey"),
    "program.all_storeys": ("Todos os pisos", "Every storey"),
    "program.any_storey": ("Qualquer piso", "Any storey"),
    "program.line": ("Ambiente escolhido", "Room chosen"),
    "program.area_optional": ("opcional, em m²", "optional, in m²"),
    "program.count": ("Quantidade", "How many"),
    "program.external": ("Exterior", "Outside"),
    "program.external_tip": ("Um ambiente exterior: varanda, terraço, pátio, recreio.",
                             "An outside room: balcony, terrace, yard, playground."),
    "program.add": ("+ Ambiente", "+ Room"),
    "program.add_tip": ("Mais um ambiente na lista do piso mostrado.", "One more room on the storey shown."),
    "program.delete": ("Apagar", "Delete"),
    "program.new_name": ("Novo ambiente", "New room"),
    "program.ai": ("Pedir à IA…", "Ask an AI…"),
    "program.ai_tip": ("Copia um pedido para colar numa IA (ChatGPT, Claude, Gemini…): ela responde com o programa em "
                       "JSON; guarde-o num ficheiro .json e use «Importar…».",
                       "Copies a request to paste in an AI (ChatGPT, Claude, Gemini…): it answers with the programme "
                       "as JSON; save it in a .json file and use «Import…»."),
    "program.ai_what": ("um edifício de {type}", "a {type} building"),
    "program.conflicts": ("Zonas conflitantes ({n}) — verifique:", "Conflicting zones ({n}) — check:"),
    "program.conflict_line": ("«{a}» ↔ «{b}»: {why}", "«{a}» ↔ «{b}»: {why}"),
    "program.status.todo": ("«{name}» ainda não está no projeto.", "«{name}» is not in the project yet."),
    "program.status.ok": ("«{name}»: meta atingida (a área pedida, ou mais).", "«{name}»: goal reached."),
    "program.status.short": ("«{name}»: colocado, mas com menos área (ou menos vezes) do que o pedido — verifique.",
                             "«{name}»: placed, but smaller (or fewer) than asked — check it."),
    "program.status.conflict": ("«{name}» abre diretamente para um ambiente de uso incompatível — verifique as zonas "
                                "conflitantes.", "«{name}» opens straight into a room of an incompatible use — check "
                                                 "the conflicting zones."),
    "cmd.room_program": ("Programa de necessidades", "Room programme"),
    "info.program_none": ("O programa está vazio: «+ Ambiente» no painel, ou «Importar…» uma lista (CSV, texto ou "
                          "JSON).",
                          "The programme is empty: «+ Room» in the panel, or «Import…» a list (CSV, text or JSON)."),
    "err.program_empty": ("{f} não tem ambientes (uma linha por ambiente: nome; área; quantidade; interior/exterior — "
                          "ou um JSON com «ambientes»).",
                          "{f} has no rooms (a line a room: name; area; how many; interior/exterior — or a JSON with "
                          "«rooms»)."),
    "err.program_json": ("{f} não é um JSON que se leia: {e}", "{f} is not a JSON that can be read: {e}"),
    "info.program_imported": ("Programa importado de {f}: {n} ambientes. Clique num deles e depois dentro das paredes "
                              "(ou arraste-o).",
                              "Programme imported from {f}: {n} rooms. Click one, then inside walls (or drag it)."),
    "info.program_made": ("Ambiente «{name}» feito. Ctrl+Z desfaz.", "Room «{name}» made. Ctrl+Z undoes."),
    "info.program_named": ("O ambiente aqui passou a chamar-se «{name}». Ctrl+Z desfaz.",
                           "The room here is now called «{name}». Ctrl+Z undoes."),
    "info.program_area_ok": ("Área {a}: meta atingida.", "Area {a}: goal reached."),
    "info.program_area_short": ("Área {a}, menos do que os {w} pedidos — verifique.",
                                "Area {a}, less than the {w} asked — check it."),
    "info.program_conflict": ("Zonas conflitantes — verifique: «{name}» abre diretamente para um ambiente de uso "
                              "incompatível. {why}",
                              "Conflicting zones — check: «{name}» opens straight into a room of an incompatible "
                              "use. {why}"),
    "info.program_conflict_new": ("Zonas conflitantes — verifique: «{a}» abre diretamente para «{b}». {why}",
                                  "Conflicting zones — check: «{a}» opens straight into «{b}». {why}"),
    "info.program_storey_done": ("Todos os ambientes deste piso estão no projeto.",
                                 "Every room of this storey is in the project."),
    "info.program_ai": ("Pedido para a IA copiado: cole-o numa IA, guarde a resposta num ficheiro .json e use "
                        "«Importar…» no painel Ambientes.",
                        "Request for an AI copied: paste it in an AI, save the answer in a .json file and use "
                        "«Import…» in the Rooms panel."),
    "tool.room_need": ("Colocar ambiente do programa", "Place a room of the programme"),
    "hint.room_need": ("Clique dentro das paredes para colocar «{name}»{area}. Esc: terminar.",
                       "Click inside walls to place «{name}»{area}. Esc: done."),
    "hint.room_need_area": (" (pretendidos {a})", " ({a} wanted)"),
    "hint.room_need_none": ("Escolha um ambiente na lista do painel Ambientes.", "Choose a room in the Rooms panel."),
    "hint.room_need_enough": ("✓ meta atingida", "✓ goal reached"),
    "hint.room_need_short": ("faltam {a}", "{a} short"),
    "props.room_number": ("Número", "Number"),
    "props.room_area": ("Área", "Area"),
    "props.room_perimeter": ("Perímetro", "Perimeter"),
    "props.room_height": ("Pé-direito", "Height"),
    "props.room_floor": ("Acabamento do piso", "Floor finish"),
    "props.room_wall": ("Acabamento das paredes", "Wall finish"),
    "props.room_ceiling": ("Acabamento do teto", "Ceiling finish"),
    "props.room_hint": ("O ambiente acompanha as paredes: muda sozinho quando elas mudam. Delete apaga-o.",
                        "The room follows the walls: it changes by itself when they do. Delete removes it."),
    "hint.position_camera": ("Posicionar câmara: clique onde fica de pé — os olhos ficam a {h} por cima. Escreva "
                             "outra altura (ex.: 1,20) e Enter.",
                             "Position camera: click where you stand — the eyes go {h} over it. Type another "
                             "height (e.g. 1.20) and Enter."),
    "hint.look_around": ("Olhar em volta: arraste para rodar a cabeça; a câmara fica no sítio. Caminhar e "
                         "Orbitar na barra de navegação; Espaço volta a Selecionar.",
                         "Look around: drag to turn your head; the camera stays where it is. Walk and Orbit in the "
                         "navigation bar; Space goes back to Select."),
    "hint.walk": ("Caminhar: arraste para cima/baixo para andar, para os lados para virar (Shift: subir/descer; "
                  "Ctrl: mais depressa; Alt: atravessar paredes). Também as setas do teclado. Espaço volta a "
                  "Selecionar.",
                  "Walk: drag up/down to walk, sideways to turn (Shift: up/down; Ctrl: faster; Alt: through walls). "
                  "The arrow keys too. Space goes back to Select."),
    "info.walk_blocked": ("Há uma parede (ou outro elemento) à frente. As portas atravessam-se; com Alt "
                          "atravessa tudo.",
                          "A wall (or another element) is in the way. Doors are walked through; with Alt, "
                          "everything."),
    "err.walk_3d": ("Caminhar, olhar em volta e posicionar a câmara são para a vista 3D em perspetiva (abra o 3D: "
                    "F4 numa planta; Propriedades da vista ▸ Projeção: Perspetiva).",
                    "Walk, look around and position camera are for the 3D view in perspective (open 3D: F4 in a "
                    "plan; View properties ▸ Projection: Perspective)."),
    "info.position_camera": ("Câmara com os olhos a {h} do chão. Arraste para olhar em volta.",
                             "Camera with the eyes {h} over the floor. Drag to look around."),
    "vcb.eye_height": ("Altura dos olhos", "Eye height"),
    # the view cube's faces (0.79)
    "cube.top": ("TOPO", "TOP"),
    "cube.bottom": ("BASE", "BOTTOM"),
    "cube.front": ("FRENTE", "FRONT"),
    "cube.back": ("TRÁS", "BACK"),
    "cube.right": ("DIREITA", "RIGHT"),
    "cube.left": ("ESQUERDA", "LEFT"),
    "cube.letters": ("N E S O", "N E S W"),        # (0.81: the compass ring — north, east, south, west)
    "cube.menu.home": ("Ir para a vista inicial", "Go to the starting view"),
    "cube.menu.set_home": ("Definir a vista atual como inicial", "Set the current view as the starting one"),
    "cube.menu.reset_home": ("Repor a vista inicial de origem", "Back to the usual starting view"),
    "info.home_set": ("Vista inicial definida: a casinha do cubo volta aqui (Ctrl+Z desfaz).",
                      "Starting view set: the cube's house comes back here (Ctrl+Z undoes it)."),
    "info.home_reset": ("A vista inicial voltou a ser a de origem.", "The starting view is the usual one again."),
    "menu.team": ("Equipa (pasta partilhada)", "Team (shared folder)"),
    "act.share": ("Partilhar projeto numa pasta…", "Share the project in a folder…"),
    "act.open_shared": ("Abrir projeto partilhado…", "Open a shared project…"),
    "act.sync": ("Sincronizar com o central", "Synchronise with the central model"),
    "act.reserve_views": ("Reservar as vistas (cortes, folhas, cotas)", "Reserve the views (sections, sheets, dimensions)"),
    "act.give_back": ("Devolver as minhas reservas", "Give back my reservations"),
    "share.title_mark": (" (partilhado)", " (shared)"),
    "share.exists": ("Já existe um projeto com este nome nessa pasta: {f}", "There is already a project with this name there: {f}"),
    "info.shared": ("Projeto partilhado — o central é {f}. Trabalha numa cópia local; Sincronizar (Ctrl+Alt+S) troca as "
                    "alterações com a equipa.",
                    "Project shared — the central model is {f}. You work on a local copy; Synchronise (Ctrl+Alt+S) "
                    "exchanges the changes with the team."),
    "share.not_shared": ("Este projeto não está partilhado (Colaborar ▸ Equipa ▸ Partilhar projeto).",
                         "This project is not shared (Collaborate ▸ Team ▸ Share project)."),
    "share.working": ("A sincronizar com o central…", "Synchronising with the central model…"),
    "share.failed": ("Não foi possível sincronizar: {e}", "Could not synchronise: {e}"),
    "share.sent": ("as suas alterações foram para o central", "your changes went to the central model"),
    "share.nothing_sent": ("nada seu a enviar", "nothing of yours to send"),
    "share.received": ("chegaram alterações da equipa", "changes from the team came in"),
    "share.nothing_received": ("nada novo da equipa", "nothing new from the team"),
    "share.views_sent": ("as suas vistas foram para o central", "your views went to the central model"),
    "share.views_received": ("vistas do central recebidas", "views from the central model received"),
    "share.conflicts": ("{n} conflito(s): ficou a versão do central", "{n} conflict(s): the central's version stayed"),
    "info.synced": ("Sincronizado: {what}.", "Synchronised: {what}."),
    "share.views_taken": ("As vistas estão reservadas por {user}.", "The views are reserved by {user}."),
    "share.views_mine": ("As vistas estão reservadas para si: as suas vão para o central ao sincronizar.",
                         "The views are reserved for you: yours go to the central model when you synchronise."),
    "share.given_back": ("As suas reservas foram devolvidas.", "Your reservations were given back."),
    "share.reserved": ("Não pode mudar isto: está reservado por {users}. (A alteração foi desfeita.)",
                       "You cannot change this: it is reserved by {users}. (The change was undone.)"),
    "share.status": ("Partilhado · {n} reserva(s) minha(s)", "Shared · {n} reservation(s) of mine"),
    "phase.existing": ("Existente", "Existing"),
    "phase.new": ("Novo (a construir)", "New (to build)"),
    "phase.demolish": ("A demolir", "To demolish"),
    "phase.temporary": ("Temporário", "Temporary"),
    "props.phase": ("Fase", "Phase"),
    "props.more": ("Mais dados", "More data"),
    "props.add_property": ("+ Propriedade…", "+ Property…"),
    "props.add_title": ("Acrescentar propriedade", "Add a property"),
    "props.add_choose": ("Propriedade (normalizada, IFC4)", "Property (standard, IFC4)"),
    "props.add_value": ("Valor", "Value"),
    "props.add_none": ("Este elemento já tem todas as propriedades normalizadas da sua classe.",
                       "This element already has all the standard properties of its class."),
    "info.property_added": ("{prop} acrescentada em {pset}.", "{prop} added in {pset}."),
    "props.add_free": ("Outra (uma propriedade sua)…", "Another (a property of your own)…"),
    "props.free_pset": ("Projeto", "Project"),
    "props.free_pset_label": ("Conjunto", "Property set"),
    "props.free_prop_label": ("Propriedade", "Property"),
    "props.free_kind_label": ("Tipo de valor", "Kind of value"),
    "props.kind.text": ("Texto", "Text"),
    "props.kind.number": ("Número", "Number"),
    "props.kind.bool": ("Sim / não", "Yes / no"),
    "props.free_missing": ("Dê um nome ao conjunto e à propriedade.", "Give the set and the property a name."),
    "props.free_reserved": ("Os nomes começados por \"Pset_\" ou \"Qto_\" são da norma IFC: use outro.",
                            "Names starting with \"Pset_\" or \"Qto_\" belong to the IFC standard: use another."),
    "props.no_phase": ("(sem fase)", "(no phase)"),
    "act.phase": ("Fase da seleção", "Phase of the selection"),
    "cmd.status": ("Mudar a fase", "Change the phase"),
    "info.status": ("{n} elemento(s): {phase}.", "{n} element(s): {phase}."),
    "info.select_first": ("Selecione primeiro os elementos.", "Select the elements first."),
    "rules.status": ("Fase (alterações)", "Phase (renovation)"),
    "tpl.phases": ("Fases que se veem", "Phases shown"),
    "tpl.phases.all": ("Todas (alterações)", "All (changes)"),
    "tpl.phases.existing": ("Situação existente (sem o novo)", "As it is (without the new)"),
    "tpl.phases.proposal": ("Proposta (sem o que se demole)", "Proposal (without what is demolished)"),
    "tpl.phases.new": ("Só o novo", "Only the new"),
    "tpl.make_phases": ("Criar modelos de alterações", "Make renovation templates"),
    "tpl.name.existing": ("Existente", "Existing"),
    "tpl.name.proposal": ("Proposta", "Proposal"),
    "tpl.name.changes": ("Alterações (amarelos e vermelhos)", "Changes (yellows and reds)"),
    "notes.title": ("Notas (BCF)", "Notes (BCF)"),
    "notes.new": ("Nova nota", "New note"),
    "notes.go": ("Ir para a vista", "Go to the view"),
    "notes.toggle": ("Fechar / reabrir", "Close / reopen"),
    "notes.delete": ("Apagar", "Delete"),
    "notes.import": ("Importar BCF…", "Import BCF…"),
    "notes.export": ("Exportar BCF…", "Export BCF…"),
    "notes.col.title": ("Nota", "Note"),
    "notes.col.status": ("Estado", "State"),
    "notes.col.author": ("Autor", "Author"),
    "notes.col.date": ("Data", "Date"),
    "notes.col.comments": ("Coment.", "Comm."),
    "notes.open": ("Aberta", "Open"),
    "notes.closed": ("Fechada", "Closed"),
    "notes.no_picture": ("(sem imagem)", "(no picture)"),
    "notes.comment_hint": ("Escreva um comentário e prima Enter", "Write a comment and press Enter"),
    "notes.field_title": ("Título", "Title"),
    "notes.field_description": ("Descrição", "Description"),
    "notes.hint": ("Uma nota guarda onde estava a olhar, os elementos escolhidos e uma imagem. Gravam-se com o projeto "
                   "(<nome>.bcfzip) e trocam-se com o Revit, ArchiCAD, Solibri… (Exportar / Importar BCF).",
                   "A note keeps where you were looking, the elements selected and a picture. They are saved with "
                   "the project (<name>.bcfzip) and exchanged with Revit, ArchiCAD, Solibri… (Export / Import BCF)."),
    "notes.filter": ("Notas BCF (*.bcfzip *.bcf)", "BCF notes (*.bcfzip *.bcf)"),
    "notes.error": ("Não foi possível ler {f} como BCF: {e}", "Could not read {f} as BCF: {e}"),
    "act.new_note": ("Nova nota de coordenação (BCF)…", "New coordination note (BCF)…"),
    "cmd.note_new": ("Nova nota", "New note"),
    "cmd.note_comment": ("Comentar nota", "Comment on a note"),
    "cmd.note_status": ("Estado da nota", "Note state"),
    "cmd.note_delete": ("Apagar nota", "Delete note"),
    "cmd.notes_import": ("Importar notas", "Import notes"),
    "info.note_new": ("Nota «{t}» guardada com a vista e {n} elemento(s).",
                      "Note \"{t}\" kept with the view and {n} element(s)."),
    "info.note_go": ("Vista da nota «{t}» ({n} elemento(s)).", "View of the note \"{t}\" ({n} element(s))."),
    "info.note_no_view": ("Esta nota não tem vista guardada.", "This note has no view kept."),
    "info.notes_imported": ("{n} nota(s) importada(s) de {f}.", "{n} note(s) imported from {f}."),
    "info.notes_exported": ("{n} nota(s) exportada(s) para {f} (BCF 2.1).", "{n} note(s) exported to {f} (BCF 2.1)."),
    "tpl.title": ("Modelos de vista", "View templates"),
    "act.templates": ("Modelos de vista…", "View templates…"),
    "tpl.new": ("Novo", "New"),
    "tpl.delete": ("Apagar", "Delete"),
    "tpl.name": ("Nome", "Name"),
    "tpl.cut": ("Altura de corte (plantas)", "Cut height (plans)"),
    "tpl.scale": ("Escala nas folhas", "Scale on sheets"),
    "tpl.rule": ("Colorir por", "Colour by"),
    "tpl.visible": ("Categorias que se veem", "Categories shown"),
    "tpl.default_name": ("Modelo {n}", "Template {n}"),
    "tpl.hint": ("Um modelo dá as mesmas definições a várias vistas; mudar o modelo muda-as todas. Para dar um modelo "
                 "a uma vista: painel Projeto, botão direito na planta, corte ou alçado ▸ Modelo de vista.",
                 "A template gives the same settings to several views; changing it changes them all. To give a view "
                 "a template: Project panel, right-click the plan, section or elevation ▸ View template."),
    "tree.template": ("Modelo de vista", "View template"),
    "tree.no_template": ("(nenhum)", "(none)"),
    "cmd.templates": ("Modelos de vista", "View templates"),
    "cmd.assign_template": ("Dar modelo de vista", "Give a view template"),
    "info.templates": ("{n} modelo(s) de vista. Dê-os às vistas no painel Projeto (botão direito ▸ Modelo de vista).",
                       "{n} view template(s). Give them to views in the Project panel (right-click ▸ View template)."),
    "info.template_assigned": ("«{view}» segue o modelo «{tpl}».", "\"{view}\" follows the template \"{tpl}\"."),
    "info.template_none": ("«{view}» sem modelo de vista: tem as suas próprias propriedades (painel Propriedades, "
                           "com nada selecionado).",
                           "\"{view}\" has no view template: it has its own properties (Properties panel, with "
                           "nothing selected)."),
    "cmd.view_props": ("Propriedades da vista", "View properties"),
    "info.view_props": ("«{view}»: propriedades da vista mudadas (Ctrl+Z desfaz).",
                        "\"{view}\": view properties changed (Ctrl+Z undoes)."),
    "err.cut_height": ("A altura de corte tem de ficar entre 0,10 m e 5,00 m acima do pavimento.",
                       "The cut height must be between 0.10 m and 5.00 m above the storey."),
    "err.view_name": ("Já há uma vista com o nome «{name}».", "There is already a view named \"{name}\"."),
    "props.view": ("Vista", "View"),
    "props.view_kind": ("Tipo de vista", "View type"),
    "props.view_kind.plan": ("Planta do pavimento", "Floor plan"),
    "props.view_kind.section": ("Corte", "Section"),
    "props.view_kind.elevation": ("Alçado", "Elevation"),
    "props.view_kind.3d": ("Vista 3D", "3D view"),
    "props.view_template": ("Modelo de vista", "View template"),
    # (0.414) the view's type on top: its view template
    "props.view_template_tip": ("O tipo da vista (o seu modelo de vista): escolha outro para lhe aplicar. Os modelos "
                                "editam-se em Visualizar ▸ Modelos de vista.",
                                "The view's type (its view template): choose another to apply it. Templates are edited "
                                "in View ▸ View templates."),
    "props.view_template_save": ("Guardar como modelo…", "Save as template…"),
    "props.view_template_save_tip": ("Faz um modelo de vista com o que esta vista mostra agora e dá-lho; escolha-o no "
                                     "topo das Propriedades de outras vistas",
                                     "Makes a view template of what this view shows now and gives it to it; choose it "
                                     "at the top of other views' Properties"),
    "ask.template_name": ("Nome do modelo de vista:", "The view template's name:"),
    "cmd.view_template_save": ("Guardar como modelo de vista", "Save as view template"),
    "info.view_template_saved": ("Modelo de vista «{n}» feito com esta vista e dado a ela. Escolha-o no topo das "
                                 "Propriedades de outras vistas. Ctrl+Z desfaz.",
                                 "View template “{n}” made of this view and given to it. Choose it at the top of other "
                                 "views' Properties. Ctrl+Z undoes."),
    "props.view_style": ("Estilo visual", "Visual style"),
    "props.view_style.shaded": ("Sombreado", "Shaded"),
    "props.view_style.hidden": ("Linhas escondidas", "Hidden lines"),
    "props.view_style.wire": ("Arame", "Wireframe"),
    "props.view_style.xray": ("Raio-X", "X-ray"),
    "props.view_style.none": ("Nenhum (linhas, como sempre)", "None (lines, as always)"),     # (0.315)
    # (0.315) the view styles
    "act.view_styles": ("Estilos de vista…", "View styles…"),
    "tip.view_styles": ("Criar e editar estilos de vista: faces sombreadas ou em cores consistentes, cores dos "
                        "materiais, arestas, sombras, padrões de superfície, transparência e cortes",
                        "Make and edit view styles: shaded faces or consistent colours, the materials' colours, "
                        "edges, shadows, surface patterns, transparency and cuts"),
    "cmd.view_styles": ("Estilos de vista", "View styles"),
    "info.view_styles": ("Estilos de vista do projeto: {n}.", "The project's view styles: {n}."),
    "vstyle.title": ("Estilos de vista", "View styles"),
    "vstyle.new": ("Novo a partir deste", "New from this one"),
    "vstyle.new_tip": ("Um estilo novo do projeto, com as definições do escolhido", "A new style of the project's, "
                       "with the chosen one's settings"),
    "vstyle.delete": ("Apagar", "Delete"),
    "vstyle.name": ("Nome", "Name"),
    "vstyle.faces": ("Faces", "Faces"),
    "vstyle.faces.shaded": ("Sombreadas (com luz)", "Shaded (lit)"),
    "vstyle.faces.consistent": ("Cores consistentes (sem luz)", "Consistent colours (no light)"),
    "vstyle.faces.white": ("Brancas (linhas escondidas)", "White (hidden lines)"),
    "vstyle.faces.none": ("Só arestas (arames)", "Edges only (wireframe)"),
    "vstyle.faces.xray": ("Transparentes (raio-X)", "See-through (X-ray)"),
    "vstyle.colours": ("Cores", "Colours"),
    "vstyle.colours.category": ("Da categoria (paredes, lajes…)", "Each category's (walls, slabs…)"),
    "vstyle.colours.material": ("Dos materiais (camada a camada)", "The materials' (layer by layer)"),
    "vstyle.edges": ("Arestas", "Edges"),
    "vstyle.edges_on": ("Desenhar", "Drawn"),
    "vstyle.width_px": ("{w} px de espessura", "{w} px thick"),
    "vstyle.shadows": ("Sombras", "Shadows"),
    "vstyle.shadows_on": ("Sombras do sol", "The sun's shadows"),
    "vstyle.patterns": ("Padrões de superfície", "Surface patterns"),
    "vstyle.patterns_on": ("Azulejos, tijolos, pedra… nas faces", "Tiles, bricks, stone… on the faces"),
    "vstyle.transparency": ("Transparência", "Transparency"),
    "vstyle.transparency_on": ("Vidro e materiais transparentes", "Glass and see-through materials"),
    "vstyle.textures": ("Texturas", "Textures"),                                       # (0.469)
    "vstyle.textures_on": ("Texturas dos materiais", "The materials' textures"),
    "tip.vstyle.textures": ("As imagens do aspeto realista dos materiais (painel Materiais ▸ Editar ▸ Realista) nas "
                            "faces — com faces sombreadas nas cores dos materiais.", "The pictures of the materials' "
                            "realistic look (Materials panel ▸ Edit ▸ Realistic) on the faces — with shaded faces in "
                            "the materials' colours."),
    "vstyle.cut": ("Corte (desenhos)", "Cut (drawings)"),
    "vstyle.cut.material": ("Padrões de cada material", "Each material's patterns"),
    "vstyle.cut.category": ("Trama da categoria (estilo gráfico)", "The category's (graphic style)"),
    "vstyle.cut.solid": ("Cheio escuro", "Dark solid"),
    "vstyle.cut.empty": ("Vazio (só o contorno)", "Empty (the outline only)"),
    "vstyle.builtin_note": ("Este é um estilo do programa e não se muda. Clique em «Novo a partir deste» para fazer "
                            "um do projeto com estas definições.",
                            "This is one of the program's styles and does not change. Click “New from this one” to "
                            "make one of the project's with these settings."),
    "vstyle.hint": ("Dê um estilo a uma vista nas Propriedades (sem nada escolhido), no botão do estilo no rodapé ou "
                    "num modelo de vista. Os desenhos em folha e em PDF seguem o estilo da vista.",
                    "Give a view a style in the Properties (nothing selected), with the footer's style button or in a "
                    "view template. Its drawings on sheets and in PDF follow it."),
    "vstyle.copy_of": ("{name} — cópia", "{name} — copy"),
    # (0.318) its hatches by category
    "vstyle.categories": ("Tramas por categoria", "Hatches by category"),
    "vstyle.cat_add": ("Juntar…", "Add…"),
    "vstyle.cat_change": ("Mudar…", "Change…"),
    "vstyle.cat_drop": ("Tirar", "Remove"),
    "vstyle.cat_title": ("Tramas de uma categoria", "A category's hatches"),
    "vstyle.cat_category": ("Categoria", "Category"),
    "vstyle.cat_cut_box": ("Corte (o que o plano corta)", "Cut (what the plane cuts)"),
    "vstyle.cat_surface_box": ("Superfície projetada (o que se vê)", "Projected surface (what is seen)"),
    "vstyle.cat_cut": ("corte", "cut"),
    "vstyle.cat_surface": ("superfície", "surface"),
    "vstyle.cat_materials": ("dos materiais", "the materials'"),
    "vstyle.cat_note": ("Nesta vista, os elementos desta categoria passam a ter estas tramas em vez das dos seus "
                        "materiais. «Nenhum» deixa a dos materiais.",
                        "In this view, this category's elements get these hatches instead of their materials'. "
                        "“None” leaves the materials'."),
    # (0.316) its sun
    "vstyle.sun": ("Sol (sombras)", "Sun (shadows)"),
    "vstyle.azimuth": ("Azimute", "Azimuth"),
    "vstyle.altitude": ("Altura", "Altitude"),
    "vstyle.sun_hint": ("Azimute: 0 = norte, 90 = este, 180 = sul, 270 = oeste. Altura: acima do horizonte.",
                        "Azimuth: 0 = north, 90 = east, 180 = south, 270 = west. Altitude: above the horizon."),
    "vstyle.sun_from_site": ("Pelo local e pela hora…", "By the site and the hour…"),
    "vstyle.sun_title": ("O sol num dia e numa hora", "The sun on a day, at an hour"),
    "vstyle.sun_when": ("Dia e hora", "Day and hour"),
    "vstyle.sun_utc": ("Fuso horário (UTC +)", "Time zone (UTC +)"),
    "vstyle.sun_site": ("Terreno: latitude {lat}, longitude {lon}", "Site: latitude {lat}, longitude {lon}"),
    "vstyle.sun_no_site": ("O projeto ainda não tem localização. Indique-a primeiro em Gerenciar ▸ Projeto ▸ "
                           "Localização do terreno….",
                           "The project has no location yet. Give it first in Manage ▸ Project ▸ Site location…."),
    "vstyle.sun_night": ("A essa hora o sol está abaixo do horizonte ({alt}°): escolha outra hora.",
                         "At that hour the sun is below the horizon ({alt}°): choose another hour."),
    "vstyle.builtin.shaded": ("Sombreado", "Shaded"),
    "vstyle.builtin.hidden": ("Linhas escondidas", "Hidden lines"),
    "vstyle.builtin.wire": ("Arame", "Wireframe"),
    "vstyle.builtin.xray": ("Raio-X", "X-ray"),
    "vstyle.builtin.consistent": ("Cores consistentes", "Consistent colours"),
    "vstyle.builtin.realistic": ("Realista", "Realistic"),
    "tpl.style": ("Estilo de vista", "View style"),
    "tpl.style_own": ("O de cada vista", "Each view's own"),
    "props.view_projection": ("Projeção", "Projection"),
    "props.view_perspective": ("Perspetiva", "Perspective"),
    "props.view_axonometric": ("Axonometria (sem perspetiva)", "Axonometric (no perspective)"),
    "props.view_edges": ("Arestas", "Edges"),
    "props.view_grid": ("Grelha do chão", "Ground grid"),
    "props.view_slopes": ("Cores de inclinação do terreno", "Terrain slope colours"),          # (0.201)
    "slope.legend": ("Inclinação do terreno", "Terrain slope"),
    "slope.up_to": ("até {b} %", "up to {b} %"),
    "slope.between": ("{a} a {b} %", "{a} to {b} %"),
    "slope.over": ("mais de {a} %", "over {a} %"),
    "props.view_depth": ("Profundidade (abaixo do piso)", "Depth (below the floor)"),
    "props.view_underlay": ("Subjacente (a cinzento)", "Underlay (in grey)"),
    "props.view_underlay.none": ("(nenhum)", "(none)"),
    "props.view_underlay.below": ("Pavimento de baixo", "Storey below"),
    "props.view_underlay.above": ("Pavimento de cima", "Storey above"),
    "props.view_crop": ("Região de recorte", "Crop region"),
    "props.view_crop_axis": ("Recorte em {axis} (de; a)", "Crop in {axis} (from; to)"),
    "props.view_detail": ("Nível de detalhe", "Detail level"),
    "props.view_detail.coarse": ("Grosso (paredes cheias)", "Coarse (walls filled)"),
    "props.view_detail.medium": ("Médio (trama do material)", "Medium (the material's hatch)"),
    "props.view_detail.fine": ("Fino (camadas)", "Fine (layers)"),
    "props.view_box": ("Caixa de corte", "Section box"),
    "props.view_box_axis": ("Caixa em {axis} (de; a)", "Box in {axis} (from; to)"),
    "act.view3d_new": ("Nova vista 3D (guardar esta)", "New 3D view (keep this one)"),
    "cmd.view3d_new": ("Nova vista 3D", "New 3D view"),
    "cmd.view3d_remove": ("Apagar vista 3D", "Delete 3D view"),
    "info.view3d_new": ("Vista «{name}» criada com esta câmara, este aspeto e esta caixa de corte (painel Projeto ▸ "
                        "Vistas 3D).",
                        "View \"{name}\" made with this camera, look and section box (Project panel ▸ 3D views)."),
    "tree.views3d": ("Vistas 3D", "3D views"),
    "tree.remove_view3d": ("Apagar esta vista 3D", "Delete this 3D view"),
    "props.view_no_template": ("(sem modelo de vista)", "(no view template)"),
    "props.view_cut": ("Altura de corte", "Cut height"),
    "props.view_categories": ("Categorias", "Categories"),
    "props.view_all_shown": ("todas à vista", "all shown"),
    "props.view_n_hidden": ("{n} escondida(s): {names}", "{n} hidden: {names}"),
    "props.view_visibility": ("Visibilidade…", "Visibility…"),
    "props.view_visibility_tip": ("Escolher as categorias que se veem nesta vista (paredes, mobiliário…).",
                                  "Choose the categories this view shows (walls, furniture…)."),
    "props.view_by_template": ("Estes valores vêm do modelo «{name}». Para os mudar só nesta vista, escolha no topo "
                               "«(sem modelo de vista)»; para mudar todas as vistas desse modelo: Visualizar ▸ Gráficos ▸ "
                               "Modelos de vista…",
                               "These values come from the template \"{name}\". To change them for this view "
                               "alone, choose «(no view template)» on top; to change every view of that template: "
                               "View ▸ View templates…"),
    "props.view_hint": ("Com nada selecionado, este painel mostra a vista. Clique num elemento (ferramenta "
                        "Selecionar, Espaço) para ver as propriedades dele.",
                        "With nothing selected, this panel shows the view. Click an element (Select tool, "
                        "Space) to see its properties."),
    "vis.title": ("Visibilidade — {view}", "Visibility — {view}"),
    "vis.hint": ("Desmarque as categorias que não se devem ver nesta vista (nem no ecrã, nem nas folhas e PDF).",
                 "Untick the categories this view must not show (on screen, on sheets and in PDFs)."),
    "vis.all": ("Mostrar todas", "Show all"),
    "ids.title": ("Requisitos (IDS)", "Requirements (IDS)"),
    "act.check_ids": ("Verificar com requisitos IDS…", "Check against IDS requirements…"),
    "ids.open": ("Abrir IDS…", "Open IDS…"),
    "ids.again": ("Verificar de novo", "Check again"),
    "ids.filter": ("Requisitos IDS (*.ids *.xml)", "IDS requirements (*.ids *.xml)"),
    "ids.none": ("Abra um ficheiro IDS (requisitos do dono de obra, buildingSMART) para verificar o modelo.",
                 "Open an IDS file (the client's requirements, buildingSMART) to check the model."),
    "ids.working": ("A verificar o modelo com o IDS…", "Checking the model against the IDS…"),
    "ids.summary": ("{title}: {ok} de {n} requisito(s) cumprido(s).", "{title}: {ok} of {n} requirement(s) met."),
    "ids.col.requirement": ("Requisito / elemento", "Requirement / element"),
    "ids.col.result": ("Resultado", "Result"),
    "ids.met": ("cumprido ({n} elemento(s))", "met ({n} element(s))"),
    "ids.failed": ("falha em {f} de {n} elemento(s)", "fails for {f} of {n} element(s)"),
    "ids.missing": ("obrigatório, mas não há nenhum elemento destes", "required, but there is no such element"),
    "ids.prohibited": ("proibido, e há {n} elemento(s) assim", "prohibited, and there are {n} such element(s)"),
    "ids.not_applicable": ("não se aplica a nenhum elemento", "applies to no element"),
    "ids.other_version": ("não é para esta versão do IFC", "not for this IFC version"),
    "ids.hint": ("Clique num elemento que falha para o selecionar e enquadrar. Depois de corrigir: Verificar de novo.",
                 "Click a failing element to select and frame it. After fixing: Check again."),
    "ids.error": ("Não foi possível ler {f} como IDS: {e}", "Could not read {f} as an IDS: {e}"),
    "info.ids": ("IDS verificado: {ok} de {n} requisito(s) cumprido(s); {e} elemento(s) com falhas.",
                 "IDS checked: {ok} of {n} requirement(s) met; {e} element(s) failing."),
    # certification checks (0.70)
    "act.check_ifc": ("Verificar IFC para certificação", "Check the IFC for certification"),
    "act.site_location": ("Localização do terreno…", "Site location…"),
    "cmd.site_location": ("Localização do terreno", "Site location"),
    "site.title": ("Localização do terreno", "Site location"),
    "site.hint": ("Onde fica o terreno no mundo, como num mapa (ex.: Lisboa 38,7223 e −9,1393). Fica no IFC "
                  "(IfcSite): os outros programas e a certificação usam-no.",
                  "Where the site is on Earth, as on a map (e.g. Lisbon 38.7223 and −9.1393). It goes in the IFC "
                  "(IfcSite): other programs and certification use it."),
    "site.latitude": ("Latitude (°, + norte)", "Latitude (°, + north)"),
    "site.longitude": ("Longitude (°, + leste)", "Longitude (°, + east)"),
    "site.elevation": ("Altitude (m acima do mar)", "Elevation (m above sea level)"),
    "info.site_location": ("Terreno localizado em {lat}; {lon}.", "Site located at {lat}, {lon}."),
    "ids.save_report": ("Guardar relatório…", "Save report…"),
    "ids.report_filter": ("Página (*.html)", "Web page (*.html)"),
    "info.report_saved": ("Relatório guardado em {f}.", "Report saved as {f}."),
    "cert.working": ("A verificar o IFC (esquema, estrutura, unidades…)…",
                     "Checking the IFC (schema, structure, units…)…"),
    "cert.title": ("Verificação {schema} (preparação da certificação)", "{schema} check (getting ready for "
                   "certification)"),
    "info.cert": ("IFC verificado: {ok} de {n} verificações cumpridas (as recomendadas contam também).",
                  "IFC checked: {ok} of {n} checks met (the recommended ones count too)."),
    "cert.note": ("Preparação, não certificação: a certificação de software IFC é feita pela buildingSMART, com os "
                  "seus ficheiros de teste. Os pontos marcados como recomendados não impedem um IFC válido.",
                  "A preparation, not the certification: IFC software certification is buildingSMART's, with their "
                  "own test files. The points marked as recommended do not stop an IFC from being valid."),
    "cert.header": ("Cabeçalho do ficheiro", "File header"),
    "cert.header_tip": ("O programa que gravou o ficheiro e a vista do modelo (MVD) que declara.",
                        "The program that wrote the file and the model view (MVD) it declares."),
    "cert.header_ok": ("vista {view} · {system}", "view {view} · {system}"),
    "cert.no_view": ("Sem vista do modelo (ViewDefinition)", "No model view (ViewDefinition)"),
    "cert.no_system": ("Sem o programa de origem", "No originating program"),
    "cert.schema": ("Esquema e regras do IFC", "IFC schema and rules"),
    "cert.schema_tip": ("Cada entidade e atributo como o esquema pede, e as regras WHERE (IfcOpenShell).",
                        "Every entity and attribute as the schema asks, and the WHERE rules (IfcOpenShell)."),
    "cert.schema_ok": ("válido ({schema})", "valid ({schema})"),
    "cert.schema_error": ("Erro do esquema", "Schema error"),
    "cert.n_errors": ("{n} erro(s)", "{n} error(s)"),
    "cert.n_problems": ("{n} problema(s)", "{n} problem(s)"),
    "cert.n_missing": ("faltam {n}", "{n} missing"),
    "cert.n_of": ("falha em {f} de {n}", "fails for {f} of {n}"),
    "cert.all_n": ("todos ({n})", "all ({n})"),
    "cert.spatial": ("Estrutura espacial", "Spatial structure"),
    "cert.spatial_tip": ("Um projeto, terreno, edifício e pavimentos; cada elemento num pavimento (ou parte de um "
                         "elemento que esteja).",
                         "One project, a site, a building and storeys; every element in a storey (or part of an "
                         "element that is)."),
    "cert.spatial_ok": ("{s} pavimento(s), {n} elemento(s) arrumados", "{s} storey(s), {n} element(s) in place"),
    "cert.projects": ("Há {n} IfcProject (deve haver um)", "There are {n} IfcProject (there must be one)"),
    "cert.missing": ("Falta {what}", "No {what}"),
    "cert.not_contained": ("não está em nenhum pavimento", "is in no storey"),
    "cert.units": ("Unidades", "Units"),
    "cert.units_tip": ("Comprimento, área, volume e ângulo declarados no projeto.",
                       "Length, area, volume and angle declared in the project."),
    "cert.units_ok": ("comprimento, área, volume e ângulo", "length, area, volume and angle"),
    "cert.unit.lengthunit": ("Comprimento", "Length"),
    "cert.unit.areaunit": ("Área", "Area"),
    "cert.unit.volumeunit": ("Volume", "Volume"),
    "cert.unit.planeangleunit": ("Ângulo", "Angle"),
    "cert.unit_missing": ("unidade não declarada", "unit not declared"),
    "cert.georef": ("Georreferenciação (recomendado)", "Georeferencing (recommended)"),
    "cert.georef_tip": ("Onde fica o modelo no mundo: latitude e longitude do terreno, ou uma conversão de mapa.",
                        "Where the model is on Earth: the site's latitude and longitude, or a map conversion."),
    "cert.georef_map": ("conversão de mapa (IfcMapConversion)", "map conversion (IfcMapConversion)"),
    "cert.georef_site": ("latitude e longitude do terreno", "the site's latitude and longitude"),
    "cert.no_georef": ("Modelo sem posição no mundo", "The model has no position on Earth"),
    "cert.georef_how": ("dê a latitude e a longitude ao terreno: Gerenciar ▸ Projeto ▸ Localização…",
                        "give the site a latitude and longitude: Manage ▸ Project ▸ Location…"),
    "cert.georef_none": ("não definida", "not given"),
    "cert.guids": ("GlobalId únicos", "Unique GlobalIds"),
    "cert.guids_tip": ("Cada objeto com um GlobalId de 22 caracteres, só dele.",
                       "Every object with a 22-character GlobalId of its own."),
    "cert.guids_ok": ("{n} objeto(s), todos diferentes", "{n} object(s), all different"),
    "cert.bad_guid": ("GlobalId inválido: {g}", "Invalid GlobalId: {g}"),
    "cert.same_guid": ("o mesmo GlobalId que {other}", "the same GlobalId as {other}"),
    "cert.shapes": ("Forma 3D e nome", "3D shape and name"),
    "cert.shapes_tip": ("Cada elemento com forma 3D (Body) e nome.", "Every element with a 3D shape (Body) and a "
                        "name."),
    "cert.no_body": ("sem forma 3D (Body)", "no 3D shape (Body)"),
    "cert.no_name": ("sem nome", "no name"),
    "cert.quantities": ("Quantidades base (recomendado)", "Base quantities (recommended)"),
    "cert.quantities_tip": ("Paredes, lajes, pilares, vigas, sapatas, portas, janelas, tubos e condutas com as "
                            "quantidades base (Qto_…BaseQuantities).",
                            "Walls, slabs, columns, beams, footings, doors, windows, pipes and ducts with their "
                            "base quantities (Qto_…BaseQuantities)."),
    "cert.no_quantities": ("sem quantidades base", "no base quantities"),
    "cert.types": ("Tipo e material (recomendado)", "Type and material (recommended)"),
    "cert.types_tip": ("Os mesmos elementos com tipo (IfcRelDefinesByType) e material.",
                       "The same elements with a type (IfcRelDefinesByType) and a material."),
    "cert.type": ("tipo", "type"),
    "cert.material": ("material", "material"),
    "cert.without": ("sem {what}", "no {what}"),
    "rules.title": ("Regras gráficas", "Graphic rules"),
    "rules.colour_by": ("Colorir por:", "Colour by:"),
    "rules.none": ("Nada (cores normais)", "Nothing (usual colours)"),
    "rules.other": ("Outra propriedade…", "Another property…"),
    "rules.class": ("Classe IFC", "IFC class"),
    "rules.type": ("Tipo", "Type"),
    "rules.storey": ("Pavimento", "Storey"),
    "rules.material": ("Material", "Material"),
    "rules.external": ("Exterior / interior", "Outside / inside"),
    "rules.fire": ("Resistência ao fogo", "Fire rating"),
    "rules.value": ("Valor", "Value"),
    "rules.count": ("Elementos", "Elements"),
    "rules.yes": ("Sim", "Yes"),
    "rules.no": ("Não", "No"),
    "rules.no_value": ("(sem valor)", "(no value)"),
    "rules.hint": ("Clique numa linha para selecionar esses elementos. As cores só mudam o que se vê: o IFC não muda.",
                   "Click a line to select those elements. The colours only change what you see: the IFC does not."),
    "rules.working": ("A ler as propriedades…", "Reading the properties…"),
    "rules.loading": ("O ficheiro ainda está a ser lido: as regras gráficas ficam para daqui a pouco.",
                      "The file is still being read: graphic rules in a moment."),
    "info.rule": ("Cores por {rule}: {n} valor(es) — veja a legenda no painel Regras gráficas.",
                  "Colours by {rule}: {n} value(s) — see the legend in the Graphic rules panel."),
    "hint.dimension.view": ("Cota: abra primeiro uma planta (F4), um corte ou um alçado — a cota fica nessa vista.",
                            "Dimension: first open a plan (F4), a section or an elevation — it stays in that view."),
    "hint.dimension.start": ("Cota: clique na primeira referência — uma face, o núcleo ou o eixo de uma parede, uma "
                             "ombreira, um eixo estrutural, ou um canto (a laranja a que está sob o rato; Tab: a "
                             "seguinte no mesmo sítio).",
                             "Dimension: click the first reference — a wall's face, core or axis, a jamb, a grid "
                             "axis, or a corner (in orange the one under the mouse; Tab: the next one there)."),
    "hint.dimension.end": ("Clique na referência seguinte (Tab: a seguinte no mesmo sítio).",
                           "Click the next reference (Tab: the next one there)."),
    "hint.dimension.place": ("Clique em mais referências, ou num sítio vazio para pousar a cadeia de cotas.",
                             "Click more references, or an empty place to put the dimension string there."),
    "hint.dimension.walls": ("Cota de paredes inteiras: clique numa parede — as pontas, os vãos e as paredes que a "
                             "cruzam; depois num sítio vazio para pousar.",
                             "Entire walls: click a wall — its ends, openings and the walls crossing it; then an "
                             "empty place to put the string."),
    "cmd.dimension": ("Cota", "Dimension"),
    "cmd.section": ("Corte", "Section"),
    "cmd.rename_view": ("Mudar o nome", "Rename"),
    "cmd.remove_section": ("Apagar corte", "Delete section"),
    "cmd.sheet": ("Nova folha", "New sheet"),
    "cmd.remove_sheet": ("Apagar folha", "Delete sheet"),
    "cmd.put_on_sheet": ("Pôr na folha", "Put on sheet"),
    "cmd.change_sheet": ("Mudar a folha", "Change the sheet"),
    "cmd.title_block": ("Mudar a legenda", "Change the title block"),
    "cmd.sheet_type": ("Mudar o tipo da folha", "Change the sheet type"),                # (0.470)
    "info.sheet_type": ("Tipo «{type}» em {n} folha(s). Ctrl+Z desfaz.", "Type “{type}” on {n} sheet(s). Ctrl+Z "
                        "undoes it."),
    "props.sheet_kind": ("Folha", "Sheet"),
    "props.sheet_type_tip": ("O tipo da folha: papel, orientação e carimbo. Editar tipo… muda-o em todas as folhas "
                             "desse tipo.", "The sheet's type: paper, orientation and title block. Edit type… changes "
                             "it on every sheet of that type."),
    "props.sheet_edit_type_tip": ("Abre a janela do tipo, como no Revit: papel, orientação, carimbo e o que o carimbo "
                                  "mostra em todas as folhas.", "Opens the type's window, as in Revit: paper, "
                                  "orientation, title block and what it shows on every sheet."),
    "props.sheet_number": ("Número da folha", "Sheet number"),
    "props.sheet_number_auto": ("{n} (automático)", "{n} (automatic)"),
    "props.sheet_name": ("Nome da folha", "Sheet name"),
    "props.g.sheet": ("Folha", "Sheet"),
    "props.sheet_paper": ("Papel", "Paper"),
    "props.sheet_paper_value": ("{paper} {way}", "{paper} {way}"),
    "props.sheet_way.landscape": ("horizontal", "landscape"),
    "props.sheet_way.portrait": ("vertical", "portrait"),
    "props.sheet_template": ("Carimbo", "Title block"),
    "props.sheet_views": ("Vistas na folha", "Views on the sheet"),
    "props.sheet_sets": ("Conjuntos", "Sets"),
    "props.sheet_revisions": ("Revisões", "Revisions"),
    "props.sheet_revisions_button": ("Revisões ({n})…", "Revisions ({n})…"),
    "props.sheet_revisions_tip": ("As revisões da folha: código, data e o que mudou (impressas sobre o carimbo).",
                                  "The sheet's revisions: code, date and what changed (printed over the title "
                                  "block)."),
    "props.g.sheet_project": ("Carimbo (em todas as folhas)", "Title block (on every sheet)"),
    "props.sheet_hint": ("Conjuntos: nomes separados por vírgulas. O papel, o carimbo e os dados do projeto mudam-se "
                         "em Editar tipo…", "Sets: names split by commas. The paper, the title block and the "
                         "project's data change in Edit type…"),
    "sheettype.title": ("Propriedades do tipo — folha", "Type properties — sheet"),
    "sheettype.family": ("Família", "Family"),
    "sheettype.family_name": ("Carimbo ArqSynth", "ArqSynth title block"),
    "sheettype.type": ("Tipo", "Type"),
    "sheettype.name": ("{paper} {way} · {template}", "{paper} {way} · {template}"),
    "sheettype.params": ("Parâmetros do tipo", "Type parameters"),
    "sheettype.paper": ("Papel", "Paper"),
    "sheettype.way": ("Orientação", "Orientation"),
    "sheettype.template": ("Carimbo", "Title block"),
    "sheettype.apply_to": ("Aplicar a:", "Apply to:"),
    "sheettype.all": ("todas as folhas deste tipo ({n})", "every sheet of this type ({n})"),
    "sheettype.only": ("só «{name}»", "only “{name}”"),
    "sheettype.shown": ("O que o carimbo mostra (em todas as folhas)", "What the title block shows (on every sheet)"),
    "sheettype.number_now": ("Número desta folha agora: {n}", "This sheet's number now: {n}"),
    "sheettype.revisions_title": ("Revisões — {name}", "Revisions — {name}"),
    "sheet.zoom_in": ("Aproximar (também a roda do rato)", "Zoom in (the mouse wheel too)"),
    "sheet.zoom_out": ("Afastar (também a roda do rato)", "Zoom out (the mouse wheel too)"),
    "sheet.zoom_all": ("Ver tudo", "Fit"),
    "sheet.zoom_all_tip": ("A folha inteira (também duplo clique com o botão do meio). Arrastar com o botão do meio "
                           "move a folha.", "The whole sheet (a double click with the middle button too). Dragging "
                           "with the middle button moves the sheet."),
    "cmd.dimension_delete": ("Apagar cota", "Delete dimension"),
    "cmd.dimension_walls": ("Cotar paredes", "Dimension the walls"),
    "act.dimension_walls": ("Cotar paredes (cadeias e totais)", "Dimension the walls (chains and totals)"),
    "info.no_walls": ("Não há paredes neste pavimento para cotar.", "There are no walls on this storey to dimension."),
    "info.walls_dimensioned": ("{n} parede(s) cotada(s): {d} cotas na planta de {name}, do lado de fora. Repetir "
                               "substitui-as; clique numa cota + Delete apaga-a.",
                               "{n} wall(s) dimensioned: {d} dimensions on the plan of {name}, outside. Doing it again "
                               "replaces them; click one + Delete removes it."),
    "info.dimension": ("Cota de {v}. Clique para outra; Esc termina.", "Dimension of {v}. Click for another; Esc ends."),
    "hint.section.start": ("Corte: clique no início da linha de corte (ou numa extremidade, num eixo…).",
                           "Section: click where the section line starts (or on an endpoint, an axis…)."),
    "hint.section.end": ("Clique no fim da linha de corte.", "Click where the section line ends."),
    "hint.section.side": ("Clique do lado para onde o corte olha.", "Click on the side the section looks at."),
    "label.section_looks": ("o corte olha para aqui", "the section looks this way"),
    "act.last_section": ("Último corte", "Last section"),
    "info.section": ("{name}: o que está do lado de cá da linha foi retirado; o que é cortado a escuro. "
                     "F8 ou outra vista: 3D. F5 volta a este corte; os cortes estão no painel Projeto ▸ Vistas.",
                     "{name}: what is on the near side of the line is taken away; what is cut is dark. "
                     "F8 or another view: 3D. F5 comes back to this section; sections are in Project ▸ Views."),
    "info.elevation": ("{name}: o modelo visto de fora, desse lado. F8 ou outra vista: 3D.",
                       "{name}: the model seen from outside, from that side. F8 or another view: 3D."),
    "tree.views": ("Vistas", "Views"),
    "tree.library": ("Biblioteca", "Library"),
    "tree.components": ("Componentes", "Components"),
    "tree.groups": ("Grupos", "Groups"),
    "tree.copies": ("{name}   ({n} cópia(s))", "{name}   ({n} cop(ies))"),
    "tree.select_copies": ("Selecionar todas as cópias", "Select every copy"),
    "tree.place": ("Inserir outra cópia…", "Place another copy…"),
    "tree.import": ("Trazer de outro projeto…", "Bring from another project…"),
    "act.import_components": ("Trazer componentes de outro projeto…", "Bring components from another project…"),
    "lib.title": ("Trazer componentes", "Bring components"),
    # (0.466) the Library panel: the components with their miniatures (project, local, web)
    "libp.title": ("Biblioteca", "Library"),
    "libp.source.project": ("No projeto", "In the project"),
    "libp.source.local": ("Local", "Local"),
    "libp.source.web": ("Web", "Web"),
    "tip.libp.source.project": ("Os componentes deste projeto: um clique e coloca mais uma cópia",
                                "This project's components: one click and you place one more copy"),
    "tip.libp.source.local": ("A sua biblioteca neste computador (uma pasta; as subpastas são categorias): um clique "
                              "traz o componente para o projeto e coloca-o",
                              "Your library on this computer (a folder; its subfolders are categories): one click "
                              "brings the component into the project and places it"),
    "tip.libp.source.web": ("Componentes da web: a loja ArqSynth, onde criadores vão publicar e vender componentes",
                            "Components from the web: the ArqSynth store, where creators will publish and sell "
                            "components"),
    "libp.view": ("Como ver", "View"),
    "libp.view.small": ("Miniaturas pequenas", "Small miniatures"),
    "libp.view.medium": ("Miniaturas médias", "Medium miniatures"),
    "libp.view.large": ("Miniaturas grandes", "Large miniatures"),
    "libp.view.list": ("Lista com nomes", "List with names"),
    "libp.search": ("Pesquisar componentes…", "Search components…"),
    "libp.back": ("Voltar à pasta de cima", "Back to the folder above"),
    "libp.folder": ("Pasta…", "Folder…"),
    "tip.libp.folder": ("Escolher a pasta da biblioteca local (fica para as próximas vezes)",
                        "Choose the local library's folder (kept for the next times)"),
    "libp.folder_tip": ("Categoria «{name}»: clique para a abrir", "Category “{name}”: click to open it"),
    "libp.place": ("Colocar", "Place"),
    "libp.open": ("Abrir", "Open"),
    "libp.get": ("Obter", "Get"),
    "libp.save": ("Guardar na biblioteca local", "Keep in the local library"),
    "tip.libp.save": ("Guarda o componente escolhido como um ficheiro IFC na sua biblioteca local, para o usar noutros "
                      "projetos", "Keeps the chosen component as an IFC file in your local library, to use it in other "
                      "projects"),
    "libp.select_copies": ("Selecionar as cópias no modelo", "Select its copies in the model"),
    "libp.refresh": ("Atualizar", "Refresh"),
    "libp.project_none": ("Este projeto ainda não tem componentes. Crie um (Modelagem ▸ Fazer componente), importe um "
                          "modelo 3D, ou traga um da biblioteca Local.", "This project has no components yet. Make one "
                          "(Modelling ▸ Make component), import a 3D model, or bring one from the Local library."),
    "libp.project_tip": ("{name}\n{n} cópia(s) no modelo", "{name}\n{n} cop(ies) in the model"),
    "libp.project_hint": ("Clique num componente e coloque-o no modelo; clique direito para o guardar na biblioteca "
                          "local.", "Click a component and place it in the model; right click to keep it in the local "
                          "library."),
    "libp.local_none": ("A pasta está vazia: {folder}\nGuarde aqui componentes do projeto (aba «No projeto» ▸ Guardar na "
                        "biblioteca local) ou copie para ela ficheiros IFC, SketchUp, Rhino, glTF, OBJ ou STL.",
                        "The folder is empty: {folder}\nKeep project components here («In the project» ▸ Keep in the "
                        "local library) or copy IFC, SketchUp, Rhino, glTF, OBJ or STL files into it."),
    "libp.local_hint": ("Um clique traz o componente para o projeto e coloca-o. As pastas são categorias.",
                        "One click brings the component into the project and places it. Folders are categories."),
    "libp.file_info": ("{name}\n({f})", "{name}\n({f})"),
    "libp.free": ("Grátis", "Free"),
    "libp.web_soon": ("A loja de componentes ArqSynth vem aí: criadores vão poder publicar e vender os seus componentes, "
                      "que aparecem aqui com miniatura, autor, licença e preço. Já pode ligar um catálogo pelo seu "
                      "endereço.", "The ArqSynth component store is coming: creators will be able to publish and sell "
                      "their components, shown here with their miniature, author, licence and price. You can already "
                      "connect a catalogue by its address."),
    "libp.web_address": ("Endereço de um catálogo de componentes", "A component catalogue's address"),
    # (0.467) Poly Haven's free models
    "libp.web.polyhaven": ("Poly Haven — gratuitos (CC0)", "Poly Haven — free (CC0)"),
    "libp.web.arqsynth": ("Loja ArqSynth — em breve", "ArqSynth store — coming"),
    "libp.web.url": ("Outro catálogo (endereço)…", "Another catalogue (address)…"),
    "libp.web_category": ("Categoria", "Category"),
    "libp.web_all": ("Todas as categorias", "All categories"),
    "libp.web_address_hint": ("Escreva o endereço de um catálogo de componentes e carregue em «Ligar».",
                              "Type a component catalogue's address and press «Connect»."),
    "libp.polyhaven_credit": ("Modelos de <a href=\"https://polyhaven.com\">Poly Haven</a> — gratuitos, de domínio "
                              "público (CC0).", "Models from <a href=\"https://polyhaven.com\">Poly Haven</a> — free, "
                              "in the public domain (CC0)."),
    "libp.polyhaven_read": ("{n} modelos. Um clique descarrega o modelo para a sua biblioteca e coloca-o.",
                            "{n} models. One click fetches the model into your library and places it."),
    "libp.polyhaven_no_gltf": ("o modelo não tem ficheiro glTF", "the model has no glTF file"),
    "libp.web_getting_n": ("A obter «{name}»… {n} de {total} ficheiros", "Getting “{name}”… {n} of {total} files"),
    "libp.page": ("Ver a página do modelo na Poly Haven", "See the model's page on Poly Haven"),
    "libp.web_connect": ("Ligar", "Connect"),
    "libp.web_reading": ("A ler o catálogo…", "Reading the catalogue…"),
    "libp.web_read": ("Catálogo «{name}»: {n} componentes.", "Catalogue “{name}”: {n} components."),
    "libp.web_failed": ("Não foi possível ler: {e}", "Could not read: {e}"),
    "libp.web_info": ("{name}\nAutor: {author} · Licença: {licence} · {price}",
                      "{name}\nAuthor: {author} · Licence: {licence} · {price}"),
    "libp.web_buy_soon": ("«{name}» custa {price}: as compras na loja ArqSynth estão a ser preparadas.",
                          "“{name}” costs {price}: buying in the ArqSynth store is being prepared."),
    "libp.web_getting": ("A obter «{name}»…", "Getting “{name}”…"),
    "libp.bring_failed": ("Não foi possível trazer {f}: {e}", "Could not bring {f}: {e}"),
    "libp.brought": ("«{name}» trazido para o projeto: clique onde o quer colocar (R roda). Esc termina.",
                     "“{name}” brought into the project: click where you want it (R turns it). Esc ends."),
    "libp.save_failed": ("Não foi possível guardar o componente: {e}", "Could not keep the component: {e}"),
    "libp.saved": ("«{name}» guardado na biblioteca local: {f}", "“{name}” kept in the local library: {f}"),
    "lib.pick": ("Componentes de {f} (escolha um ou mais):", "Components in {f} (choose one or more):"),
    "lib.item": ("{name}   ({cls}; {n} cópia(s) lá)", "{name}   ({cls}; {n} cop(ies) there)"),
    "lib.reading": ("A ler {f}…", "Reading {f}…"),
    "lib.none": ("{f} não tem componentes que se possam inserir (mobiliário, louças, equipamento…).",
                 "{f} has no components that can be placed (furniture, fixtures, equipment…)."),
    "info.imported": ("{n} componente(s) na biblioteca: {names}. Para pôr cópias: painel Projeto ▸ Biblioteca, "
                      "botão direito ▸ Inserir outra cópia.",
                      "{n} component(s) in the library: {names}. To place copies: Project panel ▸ Library, "
                      "right-click ▸ Place another copy."),
    "hint.place": ("{name}: clique onde quer mais uma cópia (o canto mais baixo fica no ponto). "
                   "Tab: rodar 90°. Esc: terminar.",
                   "{name}: click where you want one more copy (its lowest corner goes on the point). "
                   "Tab: turn 90°. Esc: done."),
    "info.component_placed": ("Mais uma cópia de {name}.", "One more copy of {name}."),
    "info.copies_selected": ("{n} elementos selecionados.", "{n} elements selected."),
    "tree.plans": ("Plantas", "Plans"),
    "tree.sections": ("Cortes", "Sections"),
    "tree.elevations": ("Alçados", "Elevations"),
    "tree.elevation.N": ("Norte", "North"),
    "tree.elevation.S": ("Sul", "South"),
    "tree.elevation.E": ("Este", "East"),
    "tree.elevation.W": ("Oeste", "West"),
    "tree.elevation_title": ("Alçado {side}", "{side} elevation"),
    "tree.open_view": ("Abrir", "Open"),
    "tree.rename": ("Mudar o nome (F2)", "Rename (F2)"),
    "tree.remove_section": ("Apagar este corte", "Delete this section"),
    "info.no_section": ("Ainda não há corte: desenhe um com a ferramenta Corte (Visualizar ▸ Criar ▸ Corte).",
                        "No section yet: draw one with the Section tool (Annotate ▸ Views ▸ Section)."),
    "tree.title": ("Navegador do Projeto", "Project Browser"),
    "tree.search": ("Pesquisar…", "Search…"),
    # (0.461) the tabs at the Project Browser's foot: what its tree shows
    "tree.scope.all": ("Tudo", "All"),
    "tree.scope.views": ("Vistas", "Views"),
    "tree.scope.library": ("Biblioteca", "Library"),
    "tree.scope.project": ("Projeto", "Model"),
    "tree.scope.sheets": ("Folhas", "Sheets"),                                         # (0.470)
    "tip.tree.scope.sheets": ("Só as folhas e as vistas postas em cada uma — o último passo: imprimir e exportar "
                              "(clique direito)", "Only the sheets and the views on each — the last step: print and "
                              "export (right click)"),
    "tip.tree.scope.all": ("Tudo: as vistas, a biblioteca e o modelo, numa só árvore",
                           "All: the views, the library and the model, in one tree"),
    "tip.tree.scope.views": ("Só as vistas: plantas, cortes, alçados, vistas 3D, eixos e folhas",
                             "Views only: plans, sections, elevations, 3D views, grid axes and sheets"),
    "tip.tree.scope.library": ("Só a biblioteca: os componentes e os grupos do ficheiro, prontos a usar no projeto",
                               "Library only: the file's components and groups, ready to use in the project"),
    "tip.tree.scope.project": ("Só o que está no modelo: terreno, edifício, pavimentos e os elementos de cada um, "
                               "e os esboços", "Only what is in the model: site, building, storeys and the elements "
                               "of each, and the sketches"),
    # the compact bar's modules (0.184, the interface's panel 4)
    "mod.title": ("Módulos", "Modules"),
    "mod.project": ("Navegador do Projeto", "Project Browser"),
    "mod.storeys": ("Pavimentos", "Storeys"),
    "mod.library": ("Biblioteca", "Library"),
    "mod.sheets": ("Folhas", "Sheets"),
    "mod.rooms": ("Ambientes", "Rooms"),
    "mod.quantities": ("Tabelas e quantitativos", "Schedules and quantities"),
    "mod.materials": ("Materiais", "Materials"),
    "mod.rules": ("Regras gráficas", "Graphic rules"),
    "mod.presentation": ("ArqSynth Presentation", "ArqSynth Presentation"),
    "tip.mod.presentation": ("A interface do ArqSynth Presentation: as páginas e as cenas à esquerda, as camadas e os "
                             "ajustes da cena à direita, os comandos sobre o 3D. Outra vez (ou outro ícone): o BIM.",
                             "The ArqSynth Presentation's interface: the pages and scenes on the left, the layers and "
                             "the scene's settings on the right, the commands over the 3D view. Again (or another "
                             "icon): the BIM."),
    "mod.settings": ("Configurações", "Settings"),
    "tip.mod.project": ("As vistas, as folhas, a biblioteca e o modelo por pavimentos.",
                        "The views, the sheets, the library and the model by storeys."),
    "tip.mod.storeys": ("Os pavimentos: o ativo, novos, cotas, pisos tipo.", "The storeys: the active one, new ones, "
                                                                              "levels, typical floors."),
    "tip.mod.library": ("Os componentes com miniaturas: os do projeto, os da sua biblioteca local e os da web.",
                        "The components with miniatures: the project's, your local library's and the web's."),
    "tip.mod.sheets": ("As folhas e as vistas postas nelas.", "The sheets and the views on them."),
    "tip.mod.rooms": ("O programa de necessidades: a lista dos ambientes de cada piso, a área pretendida, colocá-los "
                      "na planta e as zonas conflitantes.",
                      "The room programme: each storey's rooms, the area wanted, placing them in the plan and the "
                      "conflicting zones."),
    "tip.mod.quantities": ("As tabelas: a árvore de todas no painel lateral; cada uma abre-se na tela (Ctrl+T).",
                           "The schedules: their tree in the side panel; each opens on the canvas (Ctrl+T)."),
    "tip.mod.materials": ("Os materiais com miniaturas: um clique pinta com ele; Editar: na vista, em corte e "
                          "realista, com texturas.", "The materials with miniatures: one click paints with it; Edit: in "
                          "view, cut and realistic, with textures."),
    # (0.468) the Materials panel (ui/material_editor.py)
    "matp.title": ("Materiais", "Materials"),
    "matp.tab.select": ("Selecionar", "Select"),
    "matp.tab.edit": ("Editar", "Edit"),
    "matp.shape.cube": ("Em cubos", "As cubes"),
    "matp.shape.sphere": ("Em esferas", "As spheres"),
    "matp.shape1.cube": ("Cubo", "Cube"),
    "matp.shape1.sphere": ("Esfera", "Sphere"),
    "matp.hint": ("Um clique num material pinta com ele (balde de tinta). Duplo clique: editar.",
                  "One click on a material paints with it (Paint bucket). Double click: edit."),
    "tip.matp.new": ("Um material novo, para editar na aba Editar.", "A new material, to edit on the Edit tab."),
    # (0.471) the Materials panel's web: Poly Haven's free textures
    "matp.source.project": ("No projeto", "In the project"),
    "matp.source.web": ("Web", "Web"),
    "tip.matp.source.project": ("Os materiais do projeto (os do programa e os seus).",
                                "The project's materials (the program's and your own)."),
    "tip.matp.source.web": ("Texturas gratuitas da Poly Haven (domínio público, CC0): um clique traz a textura como "
                            "material do projeto, com cor, relevo, rugosidade e oclusão, no tamanho real.",
                            "Poly Haven's free textures (public domain, CC0): one click brings the texture in as a "
                            "project material, with colour, relief, roughness and occlusion, at its real size."),
    "matp.web_credit": ("Texturas de <a href=\"https://polyhaven.com/textures\">Poly Haven</a> — gratuitas, de domínio "
                        "público (CC0).", "Textures from <a href=\"https://polyhaven.com/textures\">Poly Haven</a> — "
                        "free, in the public domain (CC0)."),
    "matp.web_read": ("{n} texturas.", "{n} textures."),
    "matp.web_hint": ("Um clique numa textura descarrega-a (só da primeira vez), cria o material no projeto e ativa o "
                      "balde de tinta. Clique direito: ver a página.", "One click on a texture fetches it (only the "
                      "first time), makes the project's material and turns the Paint bucket on. Right click: see its "
                      "page."),
    "matp.web_tip": ("{name}\nAutor: {authors}\nTamanho real: {size}", "{name}\nAuthor: {authors}\nReal size: {size}"),
    "matp.web_get": ("Trazer para o projeto", "Bring into the project"),
    "matp.web_getting": ("A obter «{name}»…", "Getting “{name}”…"),
    "matp.web_no_colour": ("a textura não tem imagem de cor", "the texture has no colour picture"),
    "matp.web_made": ("«{name}» é um material do projeto: clique numa face para a pintar (Editar: ver e mudar).",
                      "“{name}” is a project material: click a face to paint it (Edit: see and change it)."),
    "matp.paint": ("Pintar com este material", "Paint with this material"),
    "matp.ph.brick": ("Tijolo", "Brick"),
    "matp.ph.wood": ("Madeira", "Wood"),
    "matp.ph.concrete": ("Betão", "Concrete"),
    "matp.ph.plaster": ("Reboco", "Plaster"),
    "matp.ph.tiles": ("Azulejo e mosaico", "Tiles"),
    "matp.ph.rock": ("Pedra", "Rock"),
    "matp.ph.metal": ("Metal", "Metal"),
    "matp.ph.fabric": ("Tecido", "Fabric"),
    "matp.ph.floor": ("Pavimentos", "Floors"),
    "matp.ph.wall": ("Paredes", "Walls"),
    "matp.ph.roofing": ("Coberturas", "Roofing"),
    "matp.ph.terrain": ("Terreno", "Terrain"),
    "matp.ph.asphalt": ("Asfalto", "Asphalt"),
    "matp.ph.cobblestone": ("Calçada", "Cobblestone"),
    "matp.ph.sand": ("Areia", "Sand"),
    "matp.ph.gravel": ("Gravilha", "Gravel"),
    "matp.ph.leather": ("Couro", "Leather"),
    "tip.matp.duplicate": ("Uma cópia do material escolhido, com os seus gráficos e texturas.",
                           "A copy of the chosen material, with its graphics and textures."),
    "tip.matp.no_paint": ("Tira a pintura (fica o material do elemento).",
                          "Takes the paint off (the element's material shows)."),
    "matp.category": ("Categoria", "Category"),
    "matp.section.view": ("Na vista (3D, alçados)", "In view (3D, elevations)"),
    "matp.section.cut": ("Em corte (plantas, cortes)", "Cut (plans, sections)"),
    "matp.section.real": ("Realista (render)", "Realistic (render)"),
    "matp.section.data": ("Dados", "Data"),
    "matp.kind": ("Tipo", "Kind"),
    "matp.kind.standard": ("Padrão", "Standard"),
    "matp.kind.glass": ("Vidro", "Glass"),
    "matp.kind.water": ("Água", "Water"),
    "matp.kind.emissive": ("Luz (emissivo)", "Light (emissive)"),
    "matp.kind.cloth": ("Tecido", "Cloth"),
    "matp.preset": ("Acabamento", "Finish"),
    "tip.matp.preset": ("Um acabamento pronto (como os modelos do D5): preenche os valores; depois pode afiná-los.",
                        "A ready finish (as D5's templates): fills the values; then fine-tune them."),
    "matp.preset.custom": ("Personalizado", "Custom"),
    "matp.preset.matte": ("Baço", "Matte"),
    "matp.preset.satin": ("Acetinado", "Satin"),
    "matp.preset.glossy": ("Brilhante", "Glossy"),
    "matp.preset.lacquer": ("Lacado (verniz)", "Lacquered"),
    "matp.preset.metal": ("Metal polido", "Polished metal"),
    "matp.preset.brushed": ("Metal escovado", "Brushed metal"),
    "matp.preset.glass": ("Vidro", "Glass"),
    "matp.preset.frosted": ("Vidro fosco", "Frosted glass"),
    "matp.preset.water": ("Água", "Water"),
    "matp.preset.cloth": ("Tecido", "Cloth"),
    "matp.preset.emissive": ("Luz", "Light"),
    "matp.base": ("Cor base", "Base colour"),
    "matp.base_own": ("Própria", "Own"),
    "tip.matp.base_own": ("Ligado: esta cor (com textura, tinge-a). Desligado: a cor de sombreamento — com textura, a "
                          "textura tal como é.", "On: this colour (with a texture, it tints it). Off: the shading "
                          "colour — with a texture, the texture as it is."),
    "matp.roughness": ("Rugosidade", "Roughness"),
    "tip.matp.roughness": ("0 % espelho, 100 % giz. Com textura de rugosidade: 50 % é a textura tal como é.",
                           "0 % a mirror, 100 % chalk. With a roughness texture: 50 % is the texture as it is."),
    "matp.metallic": ("Metálico", "Metallic"),
    "tip.matp.metallic": ("0 % não metal, 100 % metal. Com textura: 50 % é a textura tal como é.",
                          "0 % not metal, 100 % metal. With a texture: 50 % is the texture as it is."),
    "matp.specular": ("Reflexão", "Specular"),
    "matp.clearcoat": ("Verniz", "Clear coat"),
    "matp.sheen": ("Brilho de tecido", "Sheen"),
    "matp.ior": ("Refração (IOR)", "Refraction (IOR)"),
    "matp.normal": ("Relevo (normal)", "Relief (normal)"),
    "matp.height": ("Altura do relevo", "Relief height"),
    "matp.ao": ("Oclusão (AO)", "Occlusion (AO)"),
    "matp.opacity": ("Opacidade", "Opacity"),
    "matp.opacity_note": ("textura: branco opaco, preto vazado", "texture: white solid, black see-through"),
    "matp.emission": ("Emissão", "Emission"),
    "matp.intensity": ("Intensidade", "Intensity"),
    "matp.shading": ("Sombreamento", "Shading"),
    "matp.mapping": ("Texturas no modelo", "Textures on the model"),
    "matp.size": ("Tamanho", "Size"),
    "tip.matp.keep_ratio": ("Manter a proporção da imagem (largura × altura).",
                            "Keep the picture's proportion (width × height)."),
    "matp.rotation": ("Rotação", "Rotation"),
    "matp.offset": ("Deslocar X, Y", "Offset X, Y"),
    "matp.pic.base": ("Textura da cor base", "Base colour texture"),
    "matp.pic.normal": ("Mapa normal (relevo à luz)", "Normal map (relief in the light)"),
    "matp.pic.roughness": ("Textura de rugosidade", "Roughness texture"),
    "matp.pic.metallic": ("Textura de metálico", "Metallic texture"),
    "matp.pic.height": ("Mapa de altura (relevo)", "Height map (relief)"),
    "matp.pic.ao": ("Mapa de oclusão (AO)", "Occlusion map (AO)"),
    "matp.pic.opacity": ("Textura de opacidade", "Opacity texture"),
    "matp.pic.emission": ("Textura de emissão", "Emission texture"),
    "matp.pic_tip": ("Clique para escolher uma imagem; clique direito: trocar, inverter, tirar.",
                     "Click to choose a picture; right click: change, invert, remove."),
    "matp.pic_choose": ("Escolher a textura", "Choose the texture"),
    "matp.pic_filter": ("Imagens (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)",
                        "Pictures (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)"),
    "matp.pic_change": ("Trocar a imagem…", "Change the picture…"),
    "matp.pic_invert": ("Inverter (branco ↔ preto)", "Invert (white ↔ black)"),
    "matp.pic_remove": ("Tirar a imagem", "Remove the picture"),
    "matp.pic_missing": ("Imagem não encontrada: {f}", "Picture not found: {f}"),
    "matp.pic_failed": ("Não foi possível guardar a imagem: {e}", "The picture could not be kept: {e}"),
    "matp.revert": ("Repor", "Revert"),
    "tip.matp.revert": ("Volta ao material como está no projeto.", "Back to the material as it is in the project."),
    "matp.ask_apply": ("O material «{name}» foi alterado. Aplicar as alterações?",
                       "The material “{name}” was changed. Apply the changes?"),
    "matp.discard": ("Descartar", "Discard"),
    "matp.stay": ("Continuar a editar", "Keep editing"),
    "tip.mod.rules": ("Colorir os elementos por uma propriedade.", "Colour the elements by a property."),
    "tip.mod.settings": ("O botão do meio do rato e os painéis.", "The mouse's middle button and the panels."),
    # the footer's view controls (0.186, the interface's panel 8)
    "foot.title": ("Rodapé — vista", "Footer — view"),
    "foot.view.top": ("Topo", "Top"),
    "foot.view.front": ("Frente (sul)", "Front (south)"),
    "foot.view.back": ("Trás (norte)", "Back (north)"),
    "foot.view.left": ("Esquerda (oeste)", "Left (west)"),
    "foot.view.right": ("Direita (este)", "Right (east)"),
    "foot.view.iso": ("Isométrica sudeste", "South-east isometric"),
    "foot.view.iso_sw": ("Isométrica sudoeste", "South-west isometric"),
    "foot.view.iso_ne": ("Isométrica nordeste", "North-east isometric"),
    "foot.view.iso_nw": ("Isométrica noroeste", "North-west isometric"),
    "foot.unit.m": ("Metros (m)", "Metres (m)"),
    "foot.unit.cm": ("Centímetros (cm)", "Centimetres (cm)"),
    "foot.unit.mm": ("Milímetros (mm)", "Millimetres (mm)"),
    "tip.foot.orientation": ("Orientação: a vista inicial, as vistas de cada lado e as isométricas (no 3D).",
                             "Orientation: the starting view, the views from each side and the isometrics (in 3D)."),
    "tip.foot.style": ("Estilo gráfico desta vista 3D: {style}. Clique para mudar.",
                       "This 3D view's graphic style: {style}. Click to change it."),
    "tip.foot.style_3d": ("Estilo gráfico: nas vistas 3D (as plantas e os cortes desenham-se a linhas).",
                          "Graphic style: in the 3D views (plans and sections are drawn in lines)."),
    "tip.foot.grid_3d": ("Grelha do chão: nas vistas 3D.", "Ground grid: in the 3D views."),
    "tip.foot.scale": ("Escala desta vista nas folhas. Clique para mudar.",
                       "This view's scale on the sheets. Click to change it."),
    "tip.foot.scale_template": ("Escala dada pelo modelo de vista desta vista (mude-a no modelo).",
                                "Scale set by this view's view template (change it in the template)."),
    "tip.foot.scale_3d": ("Escala: nas plantas, nos cortes e nos alçados.",
                          "Scale: in the plans, the sections and the elevations."),
    # (0.445) the footer's detail level, as Revit's view control bar
    "tip.foot.detail": ("Nível de detalhe desta vista: {level}. Clique para mudar (Grosso, Médio, Fino).",
                        "This view's detail level: {level}. Click to change it (Coarse, Medium, Fine)."),
    "tip.foot.detail_template": ("Nível de detalhe dado pelo modelo de vista desta vista (mude-o no modelo).",
                                 "Detail level set by this view's view template (change it in the template)."),
    "tip.foot.detail_3d": ("Nível de detalhe: nas plantas, nos cortes e nos alçados.",
                           "Detail level: in the plans, the sections and the elevations."),
    "info.dim_permanent": ("Cota permanente de {v} posta na vista (segue as paredes). Ctrl+Z desfaz.",
                           "A permanent {v} dimension put in the view (it follows the walls). Ctrl+Z undoes."),
    # (0.446) how drawing looks (the header's theme button)
    "act.draw_revit": ("Desenho como no Revit", "Drawing as in Revit"),
    "act.draw_addon": ("Desenho como no addon ArqSynth", "Drawing as in the ArqSynth addon"),
    "tip.draw_revit": ("Ao desenhar: o contorno do que se desenha e a linha de localização tracejada, cotas temporárias "
                       "com traços nas pontas e o valor a laranja, o ângulo num arco largo, os snaps com símbolos "
                       "magenta (□ ponta, △ meio, ⊥ perpendicular, ↔ horizontal…).",
                       "While drawing: the outline being drawn and its dashed location line, temporary dimensions "
                       "crossed at their ends with orange values, the angle on a wide arc, the snaps' magenta glyphs "
                       "(□ end, △ middle, ⊥ perpendicular, ↔ horizontal…)."),
    "tip.draw_addon": ("Ao desenhar: cotas temporárias com setas e o valor numa caixa escura, o volume do que se "
                       "desenha, os snaps com pontos coloridos (como na versão 0.372).",
                       "While drawing: temporary dimensions with arrows and values on dark boxes, the volume being "
                       "drawn, the snaps as coloured dots (as in version 0.372)."),
    "info.draw_revit": ("Desenho como no Revit.", "Drawing as in Revit."),
    "info.draw_addon": ("Desenho como no addon ArqSynth.", "Drawing as in the ArqSynth addon."),
    "foot.detail.coarse": ("Grosso", "Coarse"),
    "foot.detail.medium": ("Médio", "Medium"),
    "foot.detail.fine": ("Fino", "Fine"),
    "tip.foot.units": ("Unidades dos comprimentos mostrados e escritos sem unidade (m, cm ou mm).",
                       "Units of the lengths shown and of the ones typed without a unit (m, cm or mm)."),
    "tip.foot.storey": ("Pavimento ativo (onde se desenha). Clique para escolher outro.",
                        "Active storey (where you draw). Click to choose another."),
    "info.units": ("Comprimentos em {unit}: um número escrito sem unidade lê-se assim. As cotas dos desenhos "
                   "seguem o seu estilo; as tabelas e as cotas dos pavimentos ficam em metros.",
                   "Lengths in {unit}: a number typed without a unit is read so. The drawings' dimensions follow "
                   "their style; the schedules and the storeys' levels stay in metres."),
    "tree.hint": ("Clique: selecionar no 3D (uma categoria ou um pavimento: tudo o que tem). "
                  "Duplo clique: enquadrar. Ctrl+clique: juntar à seleção.",
                  "Click: select in 3D (a category or a storey: everything in it). "
                  "Double-click: frame it. Ctrl+click: add to the selection."),
    "tree.no_storey": ("Sem pavimento", "No storey"),
    "tree.sketches": ("Esboços (fora do IFC)", "Sketches (not in the IFC)"),
    "tree.cat.IfcWall": ("Paredes", "Walls"),
    "tree.cat.IfcCurtainWall": ("Fachadas-cortina", "Curtain walls"),
    "tree.cat.IfcColumn": ("Pilares", "Columns"),
    "tree.cat.IfcBeam": ("Vigas", "Beams"),
    "tree.cat.IfcFooting": ("Sapatas", "Footings"),
    "tree.cat.IfcReinforcingBar": ("Armaduras", "Reinforcement"),
    "tree.cat.IfcPipeSegment": ("Tubagens", "Pipes"),
    "tree.cat.IfcDuctSegment": ("Condutas", "Ducts"),
    "props.connections": ("Ligações", "Connections"),
    "props.end_n": ("{n}: {what}", "{n}: {what}"),
    "props.end_free": ("livre", "free"),
    "props.end_joined": ("ligado", "joined"),
    "props.end_none": ("sem portas", "no ports"),
    "tree.cat.IfcPipeFitting": ("Curvas de tubagem", "Pipe bends"),
    "tree.cat.IfcDuctFitting": ("Curvas de conduta", "Duct bends"),
    "tree.cat.IfcSlab": ("Lajes", "Slabs"),
    "tree.cat.IfcRamp": ("Rampas", "Ramps"),
    "tree.cat.IfcRoof": ("Coberturas", "Roofs"),
    "tree.cat.IfcMember": ("Peças lineares (contraventamentos, madres, madeiramento…)",  # (0.276; 0.437; 0.495)
                           "Members (braces, purlins, carpentry…)"),
    "tree.cat.IfcPlate": ("Chapas", "Plates"),                                         # (0.497)
    "tree.cat.IfcMechanicalFastener": ("Parafusos e chumbadouros", "Bolts and anchor bolts"),
    "tree.cat.IfcFastener": ("Soldaduras", "Welds"),
    "tree.cat.IfcElementAssembly": ("Conjuntos (madeiramento, estrutura leve…)",
                                    "Assemblies (carpentry, light frames…)"),
    "tree.cat.IfcStair": ("Escadas", "Stairs"),
    "tree.cat.IfcRailing": ("Guardas", "Railings"),
    "tree.cat.IfcTransportElement": ("Elevadores", "Elevators"),        # (0.374)
    "tree.cat.IfcVirtualElement": ("Separadores de ambientes", "Room separators"),
    "tree.cat.IfcDoor": ("Portas", "Doors"),
    "tree.cat.IfcWindow": ("Janelas", "Windows"),
    "tree.cat.IfcCovering": ("Revestimentos", "Coverings"),
    "tree.cat.IfcFurniture": ("Mobiliário", "Furniture"),
    "tree.cat.IfcSanitaryTerminal": ("Louça sanitária", "Sanitary fixtures"),
    "tree.cat.IfcGeographicElement": ("Terreno", "Terrain"),
    "tree.cat.IfcBuildingElementProxy": ("Elementos genéricos", "Generic elements"),
    "tree.cat.IfcSite": ("Terreno", "Site"),
    "tree.cat.IfcBuilding": ("Edifício", "Building"),
    "tree.cat.IfcProject": ("Projeto", "Project"),
    "info.recentred": (" Modelo longe da origem (E {x} m, N {y} m): trabalhado perto da origem; o IFC guarda "
                       "as coordenadas reais.",
                       " Model far from the origin (E {x} m, N {y} m): worked on near the origin; the IFC keeps "
                       "its real coordinates."),
    "open.loading": ("A ler o IFC de {f}… pode orbitar e ver; editar quando terminar",
                     "Reading the IFC of {f}… you can orbit and look; edit when it is done"),
    "info.opened_preview": ("Aberto: {f} — {n} elementos: no ecrã em {p} s (formas guardadas da última vez), "
                            "pronto a editar em {s} s.",
                            "Opened: {f} — {n} elements: on screen in {p} s (shapes kept from last time), "
                            "ready to edit in {s} s."),
    "info.open_cancelled_preview": ("Abertura cancelada.", "Opening cancelled."),
    "open.loading_shapes": ("A calcular as formas 3D de {f}… {p} % — pode orbitar e ver; editar quando terminar",
                            "Working out the 3D shapes of {f}… {p} % — you can orbit and look; edit when it is done"),
    "info.opened_streamed": ("Aberto: {f} — {n} elementos: os primeiros no ecrã em {p} s, todos e pronto a editar "
                             "em {s} s (da próxima vez será mais rápido).",
                             "Opened: {f} — {n} elements: the first on screen in {p} s, all and ready to edit in "
                             "{s} s (quicker next time)."),
    "open.reading": ("A ler {f}…", "Reading {f}…"),
    "open.shapes": ("A calcular as formas 3D de {f}…\n(só na primeira vez que este ficheiro é aberto)",
                    "Working out the 3D shapes of {f}…\n(only the first time this file is opened)"),
    "open.preparing": ("A preparar o desenho…", "Preparing the drawing…"),
    "open.cancel": ("Cancelar", "Cancel"),
    "open.cancelling": ("A cancelar…", "Cancelling…"),
    "info.open_cancelled": ("Abertura cancelada — o projeto anterior continua aberto.",
                            "Opening cancelled — the previous project is still open."),
    "info.opened_cached": ("Aberto: {f} — {n} elementos, em {s} s (formas guardadas da última vez).",
                           "Opened: {f} — {n} elements, in {s} s (shapes kept from last time)."),
    "err.open": ("Não foi possível abrir \"{f}\":\n{e}", "Could not open \"{f}\":\n{e}"),
    "cmd.edit": ("Editar elemento", "Edit element"),
    "cmd.flip_door": ("Virar a porta", "Flip the door"),
    "err.not_editable": ("Este elemento IFC veio de outro programa (ou de uma versão anterior): só leitura.",
                         "This IFC element comes from another program (or an older version): read-only."),
    "err.pp_filling": ("Portas e janelas movem-se no painel Propriedades (posição, peitoril, tipo).",
                       "Doors and windows are moved in the Properties panel (position, sill, type)."),
    "err.pp_thickness": ("A espessura vem do tipo: escolha outro tipo no painel Propriedades.",
                         "The thickness comes from the type: choose another type in the Properties panel."),
    "err.pp_base": ("A base fica no pavimento. Puxe o topo para mudar a altura.",
                    "The base stays on the storey. Pull the top to change the height."),
    "err.pp_section": ("A secção do pilar vem do tipo: escolha outro tipo no painel Propriedades.",
                       "The column section comes from the type: choose another type in the Properties panel."),
    "err.edit_refused": ("Não foi possível: {e}.", "Not possible: {e}."),
    "refuse.too_small": ("ficaria pequeno demais (mínimo 10 cm)", "it would be too small (10 cm minimum)"),
    "refuse.opening_outside": ("uma porta, janela ou vão ficaria fora do elemento",
                               "a door, window or opening would be left outside the element"),
    "refuse.outside_wall": ("a porta/janela sairia da parede", "the door/window would leave the wall"),
    "refuse.taller_than_wall": ("a porta/janela ficaria mais alta do que a parede",
                                "the door/window would be taller than the wall"),
    "refuse.not_editable": ("este elemento não é editável", "this element cannot be edited"),
    # (0.188) a curtain wall embedded in a wall
    "refuse.cw_outside_wall": ("a fachada embutida sairia da sua parede (desligue «Embutida na parede» primeiro)",
                               "the embedded curtain wall would leave its wall (turn off \"Embedded in the wall\" "
                               "first)"),
    "refuse.cw_no_wall": ("a fachada não está dentro de nenhuma parede (ao longo dela, entre as faces, sem passar "
                          "das pontas nem do topo)",
                          "the curtain wall lies in no wall (along it, between its faces, within its ends and top)"),
    "props.cw_embed": ("Embutida na parede", "Embedded in the wall"),
    "info.curtain_embedded": ("Embutida em «{wall}»: o vão abriu-se na parede.",
                              "Embedded in \"{wall}\": its opening was cut in the wall."),
    "cmd.curtain_embed": ("Embutir a fachada", "Embed the curtain wall"),
    "hint.curtain_wall_embed": ("Clique no fim da fachada (ou escreva o comprimento e Enter) — fica embutida em "
                                "«{wall}»: abre o seu vão na parede.",
                                "Click the curtain wall's end (or type its length and Enter) — it is embedded in "
                                "\"{wall}\": it cuts its opening in the wall."),
    # (0.252) a curtain wall round a curved wall
    "hint.curtain_wall_arc": ("A fachada segue o arco de «{wall}»: clique onde acaba (ou escreva o comprimento ao "
                              "longo do arco e Enter). Fica embutida na parede.",
                              "The curtain wall follows the arc of \"{wall}\": click where it ends (or type its "
                              "length along the arc and Enter). It is embedded in the wall."),
    "refuse.no_storey":("esse pavimento já não existe", "that storey no longer exists"),
    # base and top constraints of walls and columns (0.73)
    "cmd.constraints": ("Restrições de base e topo", "Base and top constraints"),
    "props.base_level": ("Restrição da base", "Base constraint"),
    "props.base_offset": ("Deslocamento da base", "Base offset"),
    "props.top": ("Restrição do topo", "Top constraint"),
    "props.top_free": ("Não ligado (altura própria)", "Unconnected (own height)"),
    "props.top_offset": ("Deslocamento do topo", "Top offset"),
    "props.height_free": ("Altura não ligada", "Unconnected height"),
    "info.edited": ("{name}: {what} = {v}.", "{name}: {what} = {v}."),
    "props.readonly": ("Só leitura (criado noutro programa ou versão anterior).",
                       "Read-only (made by another program or an older version)."),
    "props.length": ("Comprimento", "Length"),
    "props.height": ("Altura", "Height"),
    "props.thickness": ("Espessura", "Thickness"),
    "props.lx": ("Comprimento (X)", "Length (X)"),
    "props.ly": ("Largura (Y)", "Width (Y)"),
    "props.from_start": ("Distância ao início da parede", "Distance from the wall start"),
    "props.to_end": ("Distância ao fim da parede", "Distance to the wall end"),
    "props.swing": ("Virar a porta", "Flip the door"),
    "props.swing_window": ("Virar a janela", "Flip the window"),                           # (0.290)
    "props.flip_side_window_tip": ("Passa a abrir para o outro lado da parede; o peitoril vai para a outra face "
                                   "(as dobradiças ficam no mesmo lado). Virada à mão, o programa já não a vira "
                                   "sozinho para fora.",
                                   "It opens to the wall's other side; its sill goes to the other face (its hinges "
                                   "stay on the same side). Turned by hand, the program no longer turns it to the "
                                   "outside by itself."),
    "props.flip_hinge": ("Dobradiça", "Hinge"),
    "info.door_flipped_hinge": ("As dobradiças passaram para o outro aro. Ctrl+Z desfaz.",
                                "The hinges went to the other jamb. Ctrl+Z undoes."),                  # (0.359)
    "info.door_flipped_side": ("Agora abre para o outro lado da parede. Ctrl+Z desfaz.",
                               "It now opens to the other side of the wall. Ctrl+Z undoes."),
    "props.flip_hinge_tip": ("As dobradiças passam para o outro aro (abre para o mesmo lado).",
                             "The hinges go to the other jamb (it opens to the same side)."),
    "props.flip_side": ("Lado", "Side"),
    "props.flip_side_tip": ("Passa a abrir para o outro lado da parede (dobradiças no mesmo aro).",
                            "It opens to the other side of the wall (hinges on the same jamb)."),
    "props.sill": ("Peitoril", "Sill"),
    "props.by_type": ("{v} (do tipo)", "{v} (from the type)"),
    "props.type_tag": ("tipo", "type"),                                                           # (0.430)
    "props.type_tag_tip": ("Este valor é do tipo: vale para todos os elementos dele. Clique para editar o tipo.",
                           "This value is the type's: it holds for all its elements. Click to edit the type."),
    "props.use_type_value": ("Usar o valor do tipo ({v}): apaga o deste elemento.",
                             "Use the type's value ({v}): clears this element's own."),
    "cmd.void": ("Vão", "Opening"),
    "cmd.void_size": ("Medida do vão", "Opening size"),
    "info.void_size": ("{name}: {what} = {v}.", "{name}: {what} = {v}."),
    "void.width": ("largura do vão", "opening width"),
    "void.depth": ("profundidade do vão", "opening depth"),
    "void.height": ("altura do vão", "opening height"),
    "err.pp_door_opening": ("Este vão tem uma porta ou janela: mude-lhe a medida no painel Propriedades (tipo).",
                            "This opening has a door or window: change its size in the Properties panel (type)."),
    "err.pp_drawn_opening": ("Os lados de um vão desenhado com linhas inclinadas não se movem um a um: desfaça "
                             "(Ctrl+Z) e desenhe-o outra vez.",
                             "The sides of an opening drawn with slanted lines are not moved one by one: undo "
                             "(Ctrl+Z) and draw it again."),
    "props.base": ("Base", "Base"),
    "elem.void": ("Vão", "Opening"),
    "elem.niche": ("Nicho", "Niche"),
    "snap.through": ("Atravessa: abre vão", "Goes through: opening"),
    "snap.niche": ("Nicho", "Niche"),
    "info.hole": ("Furo aberto de lado a lado ({d}).", "Hole cut right through ({d})."),
    "info.void": ("Vão aberto em {wall} (IFC).", "Opening cut in {wall} (IFC)."),
    "info.niche": ("Nicho de {d} em {wall} (IFC).", "{d} niche in {wall} (IFC)."),
    "cmd.wall": ("Parede", "Wall"),
    "cmd.slab": ("Laje", "Slab"),
    "cmd.column": ("Pilar", "Column"),
    "act.typical": ("Pavimentos iguais (piso tipo)…", "Typical floors…"),
    "storeys.typical": ("Iguais…", "Typical…"),
    "storeys.typical_n": ("Igualar ({n})", "Make equal ({n})"),
    "storeys.untypical": ("Separar", "Separate"),
    "storeys.typical_tip": ("Pavimentos iguais (piso tipo): o que se modela, muda ou apaga num deles faz-se em todos, "
                            "e as cotas e os desenhos 2D da planta de um aparecem nas plantas de todos. Escolha vários "
                            "na lista (Ctrl ou Shift) e «Igualar»; «=A» marca os pavimentos iguais entre si.",
                            "Typical floors: what is modelled, changed or deleted on one of them is on all, and the "
                            "dimensions and 2D drawing of one's plan are in all their plans. Pick several in the list "
                            "(Ctrl or Shift) and «Make equal»; “=A” marks the storeys equal to each other."),
    "storeys.status_typical": (" · igual a {others}", " · equal to {others}"),
    # (0.465) «=»: the typical floors' replication on / off
    "storeys.live_tip": ("«=» ligado: o que se faz num pavimento igual (modelar, mudar, apagar, cotar, desenhar na "
                         "planta) faz-se em todos os iguais. Desligado: cada pavimento muda sozinho, e o que fizer "
                         "assim fica só nele.", "«=» on: what is done on a typical storey (modelling, changing, "
                         "deleting, dimensioning, drawing on its plan) is done on all its equals. Off: each storey "
                         "changes on its own, and what is done so stays its own."),
    "storeys.live_off_tip": ("Igual aos outros, mas com o «=» desligado: o que fizer aqui fica só neste pavimento",
                             "Equal to the others, but with «=» off: what you do here stays on this storey"),
    "storeys.status_live_off": (" (= desligado)", " (= off)"),
    "info.typical_live_on": ("«=» ligado: o que fizer num pavimento igual faz-se de novo em todos os iguais.",
                             "«=» on: what you do on a typical storey is done again on all its equals."),
    "info.typical_live_off": ("«=» desligado: cada pavimento muda sozinho — o que fizer agora fica só nele, mesmo "
                              "quando voltar a ligar o «=».", "«=» off: each storey changes on its own — what you do "
                              "now stays on it, even when «=» is on again."),
    "info.typical_taken": ("«{name}» já é igual a outros pavimentos: separe-o primeiro (Separar).",
                           "“{name}” is already equal to other storeys: separate it first (Separate)."),
    "info.typical_made": ("«{name}» e {others} são agora iguais: o que modelar, mudar ou apagar num deles faz-se em "
                          "todos, e as cotas e desenhos 2D da planta aparecem em todas. {kept}Ctrl+Z desfaz.",
                          "“{name}” and {others} are now equal: what you model, change or delete on one is done on "
                          "all, and the plan's dimensions and 2D drawing are in all. {kept}Ctrl+Z undoes."),
    "info.typical_kept": ("{names} já tinham elementos: ficam com eles e com os de «{name}». ",
                          "{names} already had elements: they keep them and get “{name}”'s. "),
    "typical.title": ("Pavimentos iguais", "Typical floors"),
    "typical.note": ("Escolha os pavimentos que ficam iguais a «{name}». Os elementos de «{name}» são copiados para "
                     "eles; daí em diante, o que se desenhar, mudar ou apagar num deles faz-se em todos.",
                     "Choose the storeys to be equal to “{name}”. The elements of “{name}” are copied to them; from "
                     "then on, what is drawn, changed or deleted on one is on all."),
    "typical.name": ("Nome do piso tipo", "Typical floor's name"),
    "typical.default_name": ("Piso tipo", "Typical floor"),
    "info.typical": ("«{name}» e {others} são agora iguais (piso tipo). Ctrl+Z desfaz.",
                     "“{name}” and {others} are now equal (typical floor). Ctrl+Z undoes."),
    "info.untypical": ("«{name}» deixou de ser igual a {others}; cada um fica com os seus elementos. Ctrl+Z desfaz.",
                       "“{name}” is no longer equal to {others}; each keeps its elements. Ctrl+Z undoes."),
    "info.typical_none": ("Marque pelo menos um pavimento.", "Tick at least one storey."),
    "cmd.room": ("Ambiente", "Room"),
    "cmd.room_edit": ("Mudar ambiente", "Change room"),
    "cmd.room_delete": ("Apagar ambiente", "Delete room"),
    "room.default": ("Ambiente", "Room"),
    "cmd.typical": ("Pavimentos iguais", "Typical floors"),
    "cmd.untypical": ("Pavimentos deixam de ser iguais", "Floors no longer typical"),
    "cmd.save_type": ("Gravar tipo", "Save type"),
    "cmd.delete_type": ("Apagar tipo", "Delete type"),
    # the type editor (0.87)
    "act.types": ("Tipos… (criar e editar)", "Types… (make and edit)"),
    # the materials window (0.89)
    "act.materials": ("Materiais…", "Materials…"),
    "mat.title": ("Materiais do projeto", "Project materials"),
    "mat.new": ("Novo", "New"),
    "mat.new_name": ("Material novo", "New material"),
    "mat.hatch": ("Trama em corte", "Cut pattern"),
    "mat.hatch.none": ("Nenhuma (cheio)", "None (solid)"),
    "mat.hatch.concrete": ("Betão", "Concrete"),
    "mat.hatch.masonry": ("Alvenaria", "Masonry"),
    "mat.hatch.wood": ("Madeira", "Wood"),
    "mat.hatch.insulation": ("Isolamento", "Insulation"),
    "mat.hatch.earth": ("Terra", "Earth"),
    "mat.hatch.gypsum": ("Gesso / reboco", "Gypsum / plaster"),
    "mat.colour": ("Cor", "Colour"),
    "mat.density": ("Massa volúmica (kg/m³)", "Density (kg/m³)"),
    "mat.conductivity": ("Condutibilidade térmica λ (W/(m·K))", "Thermal conductivity λ (W/(m·K))"),
    "mat.not_given": ("(não indicado)", "(not given)"),
    "mat.used": ("Usado em {n} tipo(s): {names}", "Used in {n} type(s): {names}"),
    "mat.unused": ("Nenhum tipo usa este material.", "No type uses this material."),
    "mat.err_same_name": ("Já há um material chamado «{name}».", "There is already a material called “{name}”."),
    "mat.err_number": ("Escreva um número (ex.: 1800 ou 0,7), ou deixe em branco.",
                       "Type a number (e.g. 1800 or 0.7), or leave it empty."),
    # (0.314) its graphics, as Revit's
    "mat.category": ("Categoria (trama por omissão)", "Category (default pattern)"),
    "mat.graphics": ("Gráficos", "Graphics"),
    "mat.data": ("Dados", "Data"),
    "mat.surface": ("Superfície (3D, alçados)", "Surface (3D, elevations)"),
    "mat.cut": ("Corte (plantas, cortes)", "Cut (plans, sections)"),
    "mat.fg": ("Primeiro plano", "Foreground"),
    "mat.bg": ("Fundo", "Background"),
    "mat.shading": ("Cor de sombreamento", "Shading colour"),
    "mat.transparency": ("Transparência", "Transparency"),
    "mat.finish": ("Acabamento (render)", "Finish (render)"),
    "mat.finish_tip": ("Como a superfície devolve a luz no render realista: baça, acetinada, brilhante, metálica, "
                       "vidro ou vidro fosco. «Pela categoria»: a do tipo de material (o betão baço, o aço metálico, "
                       "o azulejo brilhante…).",
                       "How the surface gives back the light in the realistic render: matte, satin, glossy, metallic, "
                       "glass or frosted glass. «By its category»: its kind of material's (concrete matte, steel "
                       "metallic, tiles glossy…)."),
    "mat.finish.auto": ("Pela categoria", "By its category"),
    "render.finish.matte": ("Baço", "Matte"),
    "render.finish.satin": ("Acetinado", "Satin"),
    "render.finish.glossy": ("Brilhante", "Glossy"),
    "render.finish.metal": ("Metálico", "Metallic"),
    "render.finish.glass": ("Vidro", "Glass"),
    "render.finish.frosted": ("Vidro fosco", "Frosted glass"),
    "render.finish.water": ("Água", "Water"),
    "mat.pattern_colour": ("Cor do padrão", "Pattern colour"),
    "mat.cut_by_category": ("Sem padrões de corte próprios: corta-se com a trama da categoria, do estilo gráfico do "
                            "projeto (Visualizar ▸ Estilos gráficos).",
                            "No cut patterns of its own: it is cut with its category's pattern, from the project's "
                            "graphic style (View ▸ Graphic styles)."),
    "pat.none": ("Nenhum", "None"),
    # (0.318) the project's own patterns
    "act.patterns": ("Padrões…", "Patterns…"),
    "tip.patterns": ("Padrões de preenchimento: criar, duplicar e mudar as tramas dos cortes e das superfícies",
                     "Fill patterns: make, duplicate and change the cuts' and the surfaces' hatches"),
    "mat.patterns": ("Padrões de preenchimento…", "Fill patterns…"),
    # (0.319) choosing a pattern, as in Revit
    "pick.title": ("Escolher padrão", "Choose a pattern"),
    "pick.drafting": ("De desenho (medidos no papel)", "Drafting (measured on paper)"),
    "pick.model": ("De modelo (medidos na obra)", "Model (measured on the building)"),
    "pick.none": ("Nenhum padrão", "No pattern"),
    "pick.new": ("Novo…", "New…"),
    "pick.edit": ("Editar…", "Edit…"),
    "pick.tip": ("Clique para escolher o padrão (ou criar um novo)", "Click to choose the pattern (or make a new one)"),
    "pick.sample_tip": ("Clique para escolher o padrão do primeiro plano", "Click to choose the foreground's pattern"),
    "mat.pattern": ("Padrão", "Pattern"),
    "mat.colour_of": ("Cor", "Colour"),
    "mat.pick_hint": ("Clique no padrão para o escolher, criar ou editar; ao lado, a sua cor.",
                      "Click the pattern to choose, make or edit it; beside it, its colour."),
    "mat.search": ("Pesquisar materiais…", "Search materials…"),
    "mat.family.all": ("Todas as famílias", "Every family"),
    "mat.family.masonry": ("Alvenarias", "Masonry"),
    "mat.family.concrete": ("Betões e argamassas", "Concretes and screeds"),
    "mat.family.insulation": ("Isolamentos", "Insulation"),
    "mat.family.wood": ("Madeiras e derivados", "Wood and boards"),
    "mat.family.stone": ("Pedras", "Stone"),
    "mat.family.metal": ("Metais", "Metals"),
    "mat.family.finish": ("Rebocos, gessos e cerâmicos", "Renders, gypsum and ceramics"),
    "mat.family.glass": ("Vidros", "Glass"),
    "mat.family.paint": ("Tintas", "Paints"),
    "mat.family.other": ("Outros", "Others"),
    "cmd.save_pattern": ("Gravar padrão", "Save pattern"),
    "cmd.delete_pattern": ("Apagar padrão", "Delete pattern"),
    "info.pattern_saved": ("Padrão «{name}» gravado no projeto.", "Pattern “{name}” saved in the project."),
    "err.pattern_failed": ("Não foi possível gravar o padrão: {e}", "The pattern could not be saved: {e}"),
    "patt.title": ("Padrões de preenchimento", "Fill patterns"),
    "patt.new": ("Novo", "New"),
    "patt.new_name": ("Padrão novo", "New pattern"),
    "patt.kind": ("Medido", "Measured"),
    "patt.kind.drafting": ("No papel (desenho: igual em qualquer escala)", "On paper (drafting: the same at any scale)"),
    "patt.kind.model": ("Na obra (modelo: azulejos, tijolos…)", "On the building (model: tiles, bricks…)"),
    "patt.shape": ("Forma", "Shape"),
    "patt.shape.lines": ("Linhas paralelas", "Parallel lines"),
    "patt.shape.cross": ("Linhas cruzadas", "Crossed lines"),
    "patt.shape.custom": ("Personalizado (várias famílias de linhas)", "Custom (several families of lines)"),
    "patt.angle": ("Ângulo", "Angle"),
    "patt.spacing": ("Afastamento", "Spacing"),
    "patt.col.angle": ("Ângulo (°)", "Angle (°)"),
    "patt.col.x": ("Origem X", "Origin X"),
    "patt.col.y": ("Origem Y", "Origin Y"),
    "patt.col.shift": ("Desvio", "Shift"),
    "patt.col.step": ("Afastamento", "Spacing"),
    "patt.col.dashes": ("Traços", "Dashes"),
    "patt.add_row": ("Juntar família", "Add a family"),
    "patt.del_row": ("Tirar família", "Remove the family"),
    "patt.table_hint": ("Cada linha é uma família de linhas paralelas: o ângulo, onde começa (origem), quanto a "
                        "seguinte se desvia ao longo dela e o afastamento entre elas; nos traços, «3 -1» é um traço "
                        "de 3 e um intervalo de 1, «0 -1» são pontos. Medidas em mm no papel, ou em m na obra.",
                        "Each row is a family of parallel lines: their angle, where they start (origin), how far the "
                        "next one shifts along and their spacing; in the dashes, “3 -1” is a dash of 3 and a gap of "
                        "1, “0 -1” dots. Sizes in mm on paper, or in m on the building."),
    "patt.builtin_note": ("Este padrão é do programa e não se muda. Clique em «Duplicar» para fazer um do projeto, "
                          "igual, e mudá-lo à vontade.",
                          "This pattern is the program's and does not change. Click “Duplicate” to make one of the "
                          "project's like it and change it as you wish."),
    "patt.err_number": ("Família {row}: escreva números (ex.: 45 ou 2,5).", "Family {row}: type numbers (e.g. 45 or 2.5)."),
    "patt.err_step": ("Família {row}: o afastamento não pode ser 0.", "Family {row}: the spacing cannot be 0."),
    "patt.err_empty": ("Junte pelo menos uma família de linhas.", "Add at least one family of lines."),
    "patt.err_same_name": ("Já há um padrão chamado «{name}».", "There is already a pattern called “{name}”."),
    "pat.solid": ("Cheio", "Solid fill"),
    "pat.diagonal": ("Diagonal", "Diagonal"),
    "pat.diagonal_wide": ("Diagonal larga", "Wide diagonal"),
    "pat.diagonal_back": ("Diagonal inversa", "Back diagonal"),
    "pat.cross": ("Diagonal cruzada", "Crosshatch"),
    "pat.horizontal": ("Horizontal", "Horizontal"),
    "pat.vertical": ("Vertical", "Vertical"),
    "pat.square": ("Quadrícula", "Square grid"),
    "pat.concrete": ("Betão", "Concrete"),
    "pat.sand": ("Areia (pontos)", "Sand (dots)"),
    "pat.insulation": ("Isolamento", "Insulation"),
    "pat.earth": ("Terra", "Earth"),
    "pat.wood": ("Madeira (veio)", "Wood (grain)"),
    "pat.steel": ("Aço", "Steel"),
    "pat.tile_10": ("Azulejo 10×10", "Tiles 10×10"),
    "pat.tile_15": ("Azulejo 15×15", "Tiles 15×15"),
    "pat.tile_20": ("Ladrilho 20×20", "Tiles 20×20"),
    "pat.tile_30": ("Ladrilho 30×30", "Tiles 30×30"),
    "pat.tile_30x60": ("Ladrilho 60×30", "Tiles 60×30"),
    "pat.brick": ("Tijolo à vista", "Face brick"),
    "pat.block": ("Bloco 50×20", "Block 50×20"),
    "pat.stone": ("Pedra aparelhada", "Ashlar stone"),
    "pat.boards_v": ("Réguas verticais", "Vertical boards"),
    "pat.boards_h": ("Réguas horizontais", "Horizontal boards"),
    "pat.roof_tiles": ("Telha", "Roof tiles"),
    "pat.panels": ("Painéis 120×240", "Panels 120×240"),
    "cmd.save_material": ("Gravar material", "Save material"),
    "cmd.delete_material": ("Apagar material", "Delete material"),
    "info.material_saved": ("Material «{name}» gravado no projeto.", "Material “{name}” saved in the project."),
    "err.material_failed": ("Não foi possível gravar o material: {e}", "The material could not be saved: {e}"),
    "err.material_in_use": ("Este material está a ser usado, ou é do catálogo: não se apaga.",
                            "This material is in use, or is the catalogue's: it is not deleted."),
    "props.edit_type": ("Editar tipo…", "Edit type…"),
    "props.edit_type_tip": ("Muda as camadas ou a secção deste tipo: mudam todos os elementos do mesmo tipo.",
                            "Changes this type's layers or section: every element of the type changes."),
    "types.title": ("Tipos do projeto", "Project types"),
    "types.walls": ("Paredes", "Walls"),
    "types.slabs": ("Lajes", "Slabs"),
    "types.roofs": ("Coberturas", "Roofs"),                          # (0.278)
    "types.columns": ("Pilares", "Columns"),
    "types.beams": ("Vigas", "Beams"),
    "types.members": ("Contraventamentos e madres", "Braces and purlins"),          # (0.495)
    "types.footings": ("Sapatas", "Footings"),
    "types.pipes": ("Tubos", "Pipes"),
    "types.piles": ("Estacas", "Piles"),
    "types.ducts": ("Condutas", "Ducts"),
    "types.doors": ("Portas", "Doors"),
    "types.windows": ("Janelas", "Windows"),
    "types.size": ("Medidas", "Size"),
    "types.shape": ("Forma", "Shape"),
    "types.shape.rect": ("Retangular", "Rectangular"),
    "types.shape.circle": ("Circular", "Round"),
    "types.shape.L": ("Em L", "L"),
    "types.shape.T": ("Em T", "T"),
    "types.web": ("Espessura das abas", "Legs' thickness"),
    # (0.494) steel sections of the catalogue
    "types.shape.steel": ("Perfil de aço", "Steel section"),
    "types.steel_family": ("Família", "Family"),
    "types.steel_size": ("Perfil", "Section"),
    "types.steel_grade": ("Classe do aço", "Steel grade"),
    "types.steel_dims": ("h {h} × b {b} mm · alma {tw} · banzo {tf} mm", "h {h} × b {b} mm · web {tw} · flange {tf} mm"),
    "types.steel_mass": ("{m} kg/m · A = {a} cm² · pintura {paint} m²/m", "{m} kg/m · A = {a} cm² · paint {paint} m²/m"),
    "types.steel_inertia": ("Iy = {iy} cm⁴ · Iz = {iz} cm⁴ · Wpl,y = {wy} cm³ · Wpl,z = {wz} cm³",
                            "Iy = {iy} cm⁴ · Iz = {iz} cm⁴ · Wpl,y = {wy} cm³ · Wpl,z = {wz} cm³"),
    "types.steel_grade_info": ("{grade}: fy = {fy} N/mm², fu = {fu} N/mm² (EC3-1-1, Quadro 3.1)",
                               "{grade}: fy = {fy} N/mm², fu = {fu} N/mm² (EC3-1-1, Table 3.1)"),
    "types.steel_standard": ("Medidas pela {std}.", "Dimensions to {std}."),
    "steel.family.IPE": ("IPE", "IPE"),
    "steel.family.HEA": ("HEA", "HEA"),
    "steel.family.HEB": ("HEB", "HEB"),
    "steel.family.HEM": ("HEM", "HEM"),
    "steel.family.UPN": ("UPN (abas inclinadas)", "UPN (tapered flanges)"),
    "steel.family.UPE": ("UPE (abas paralelas)", "UPE (parallel flanges)"),
    "steel.family.L": ("Cantoneira de abas iguais", "Equal angle"),
    "steel.family.LU": ("Cantoneira de abas desiguais", "Unequal angle"),
    "steel.family.SHS": ("Tubo quadrado", "Square hollow section"),
    "steel.family.RHS": ("Tubo retangular", "Rectangular hollow section"),
    "steel.family.CHS": ("Tubo redondo", "Circular hollow section"),
    "steel.family.C": ("Madre C (enformada a frio)", "C purlin (cold-formed)"),
    "steel.family.Z": ("Madre Z (enformada a frio)", "Z purlin (cold-formed)"),
    "steel.family.OMEGA": ("Ómega (enformado a frio)", "Omega (cold-formed)"),
    "types.err_web": ("A espessura das abas tem de ser maior do que zero e menor do que as medidas da secção.",
                      "The legs' thickness must be above zero and below the section's sizes."),
    "types.sill": ("Peitoril (ao colocar)", "Sill (when placed)"),
    "types.duplicate": ("Duplicar", "Duplicate"),
    "types.delete": ("Apagar", "Delete"),
    "types.name": ("Nome", "Name"),
    "types.layers": ("Camadas", "Layers"),
    "types.masonry": ("Alvenaria para o cálculo (EC6)", "Masonry for the calculation (EC6)"),           # (0.346)
    "types.masonry_own": ("Alvenaria própria deste tipo (desligada: a do projeto)",
                          "This type's own masonry (off: the project's)"),
    "types.masonry_tip": ("Os blocos, o seu grupo, a sua resistência fb e a argamassa das paredes deste tipo, para a "
                          "verificação pelo Eurocódigo 6. Desligada, usam a do projeto (Analisar ▸ Cálculo ▸ Ações e "
                          "materiais). "
                          "O γM é sempre o do projeto: vem da classe de execução da obra.",
                          "The units, their group, their strength fb and the mortar of this type's walls, for the "
                          "Eurocode 6 check. Off, they use the project's (Structure ▸ Analysis ▸ Actions and "
                          "materials). γM is "
                          "always the project's: it comes from the work's execution class."),
    "types.layers_wall": ("De fora para dentro (a primeira é a face exterior).",
                          "From outside to inside (the first is the outer face)."),
    "types.layers_slab": ("De baixo para cima.", "From bottom to top."),
    "types.material": ("Material", "Material"),
    "types.thickness": ("Espessura", "Thickness"),
    "types.function": ("Função", "Function"),                                                   # (0.334)
    "types.function_tip": ("Onde dois elementos se encontram, no corte, uma camada mais forte (1) atravessa as mais "
                           "fracas do outro, como no Revit. Automática: a mais grossa é a estrutura, as outras são "
                           "acabamento.",
                           "Where two elements meet, in the cut, a stronger layer (1) goes through the other's weaker "
                           "ones, as in Revit. Automatic: the thickest is the structure, the others finishes."),
    "types.function.auto": ("Automática", "Automatic"),
    "types.function.structure": ("Estrutura [1]", "Structure [1]"),
    "types.function.substrate": ("Substrato [2]", "Substrate [2]"),
    "types.function.thermal": ("Isolamento / caixa de ar [3]", "Thermal / air layer [3]"),
    "types.function.finish1": ("Acabamento 1 [4]", "Finish 1 [4]"),
    "types.function.finish2": ("Acabamento 2 [5]", "Finish 2 [5]"),
    "types.add_layer": ("+ Camada", "+ Layer"),
    "types.del_layer": ("− Camada", "− Layer"),
    "types.total": ("Total: {t}", "Total: {t}"),
    "types.section": ("Secção", "Section"),
    "types.width": ("Largura", "Width"),
    "types.height": ("Altura", "Height"),
    "types.length": ("Comprimento", "Length"),
    "types.diameter": ("Diâmetro", "Diameter"),
    "types.used": ("{n} no projeto", "{n} in the project"),
    "types.apply_note": ("{n} elemento(s) deste tipo no projeto: todos mudam ao aplicar (Ctrl+Z desfaz).",
                         "{n} element(s) of this type in the project: they all change when applied (Ctrl+Z undoes)."),
    "types.unused": ("Nenhum elemento deste tipo no projeto.", "No element of this type in the project."),
    "types.apply": ("Aplicar", "Apply"),
    "types.close": ("Fechar", "Close"),
    # (0.429) the live section, OK / Cancel, where it is used, a type in use replaced and deleted
    "types.core": ("núcleo", "core"),
    "types.side_out": ("Exterior", "Outside"),
    "types.side_in": ("Interior", "Inside"),
    "types.side_top": ("Topo", "Top"),
    "types.ok": ("OK", "OK"),
    "types.cancel": ("Cancelar", "Cancel"),
    "types.where_used": ("Onde se usa", "Where used"),
    "types.where_tip": ("Escolhe na vista todos os elementos deste tipo e enquadra-os.",
                        "Selects every element of this type in the view and frames them."),
    "types.replace_title": ("Apagar um tipo em uso", "Delete a type in use"),
    "types.replace_ask": ("{n} elemento(s) usam «{name}». Por que tipo os substituir, antes de o apagar?",
                          "{n} element(s) use «{name}». Which type should replace it before it is deleted?"),
    "types.replace_none": ("Não há outro tipo deste género para os substituir.",
                           "There is no other type of this kind to replace them with."),
    "cmd.replace_type": ("Substituir e apagar o tipo", "Replace and delete the type"),
    "info.type_replaced": ("{n} elemento(s) passaram a «{new}»; «{old}» foi apagado. Ctrl+Z desfaz.",
                           "{n} element(s) are now «{new}»; «{old}» was deleted. Ctrl+Z undoes."),
    "info.where_used": ("{n} elemento(s) do tipo «{name}» escolhidos.", "{n} element(s) of the type «{name}» selected."),
    "types.err_name": ("Dê um nome ao tipo.", "Give the type a name."),
    "types.err_same_name": ("Já há um tipo chamado «{name}».", "There is already a type called “{name}”."),
    "types.err_thickness": ("Cada camada precisa de uma espessura maior do que zero (ex.: 2 cm).",
                            "Each layer needs a thickness above zero (e.g. 2 cm)."),
    "types.err_size": ("As medidas da secção têm de ser maiores do que zero (ex.: 30 cm).",
                       "The section's sizes must be above zero (e.g. 30 cm)."),
    "info.type_saved": ("Tipo «{name}» gravado no projeto; {n} elemento(s) deste tipo.",
                        "Type “{name}” saved in the project; {n} element(s) of this type."),
    "err.type_failed": ("Não foi possível gravar o tipo: {e}", "The type could not be saved: {e}"),
    "err.type_in_use": ("Este tipo está a ser usado: mude primeiro os elementos para outro tipo.",
                        "This type is in use: change its elements to another type first."),
    "cmd.grid_axis": ("Eixo", "Grid axis"),
    "tool.grid": ("Eixo (grelha estrutural)", "Grid axis"),
    "hint.grid.start": ("Clique no início do eixo (snaps e alinhamentos). Ao longo de Y fica numerado (1, 2, 3…), ao "
                        "longo de X com letra (A, B, C…). Vários de uma vez: Estrutura ▸ Referência ▸ Gerar eixos…",
                        "Click the axis's start (snaps and alignments). Along Y it is numbered (1, 2, 3…), along X "
                        "lettered (A, B, C…). Several at once: Structure ▸ Grid ▸ Generate grid…"),
    # grid axes edited and generated (0.72)
    "cmd.grid_move": ("Mover eixo", "Move grid axis"),
    "cmd.grid_generate": ("Gerar eixos", "Generate grid"),
    "act.grid_generate": ("Gerar eixos…", "Generate grid…"),
    "props.grid_axis": ("Eixo da grelha", "Grid axis"),
    "props.grid_axes": ("{n} eixos selecionados", "{n} grid axes selected"),
    "props.grid_tag": ("Etiqueta", "Tag"),
    "props.grid_start": ("Início (x; y)", "Start (x; y)"),
    "props.grid_end": ("Fim (x; y)", "End (x; y)"),
    "props.grid_hint": ("Arraste a bolha (ponta) para encurtar ou alongar — as bolhas alinhadas vão juntas; com "
                        "Ctrl, só esta. O losango do meio desloca o eixo. Clique numa cota azul e escreva a "
                        "distância ao eixo vizinho. Delete apaga.",
                        "Drag a bubble (end) to shorten or lengthen — the bubbles lined up go too; with Ctrl, this "
                        "one only. The middle diamond moves the axis across. Click a blue dimension and type the "
                        "distance to the next axis. Delete removes it."),
    "hint.grid_grip": ("A ponta do eixo desliza ao longo dele (as pontas alinhadas vão juntas; Ctrl ao pegar: só "
                       "esta). Clique onde fica, ou escreva quanto anda e Enter. Esc desiste.",
                       "The axis's end slides along it (the ends lined up go too; Ctrl when taking it: this one "
                       "only). Click where it goes, or type how far and Enter. Esc gives up."),
    "hint.grid_move": ("O eixo desloca-se paralelo a si próprio. Clique onde fica, ou escreva quanto anda e Enter. "
                       "Esc desiste.",
                       "The axis moves parallel to itself. Click where it goes, or type how far and Enter. Esc "
                       "gives up."),
    "info.grid_moved": ("Eixo(s) mudado(s): {n}, {d} (Ctrl+Z desfaz).", "Grid axes changed: {n}, {d} (Ctrl+Z "
                        "undoes it)."),
    "info.grid_generated": ("{n} eixos gerados ({first} a {last}).", "{n} grid axes made ({first} to {last})."),
    "gen.title": ("Gerar eixos", "Generate grid"),
    "gen.hint": ("Os eixos verticais na planta vão da esquerda para a direita; os horizontais, de baixo para cima. "
                 "Os números e as letras seguem o esquema da grelha (Estrutura ▸ Referência ▸ Grelha estrutural…). "
                 "Distância: um "
                 "valor (todos iguais) ou vários separados por «;» (ex.: 5;5;6,50 — o último repete-se).",
                 "Vertical axes go from left to right on the plan; horizontal ones from the bottom up. Numbers and "
                 "letters follow the grid's scheme (Structure ▸ Grid ▸ Structural grid…). Spacing: one value (all "
                 "the same) or "
                 "several separated by \";\" (e.g. 5;5;6.50 — the last one repeats)."),
    "gen.numbered": ("Eixos verticais", "Vertical axes"),
    "gen.lettered": ("Eixos horizontais", "Horizontal axes"),
    # the grid's settings (0.91)
    "act.grid_settings": ("Grelha estrutural…", "Structural grid…"),
    "grid.title": ("Grelha estrutural", "Structural grid"),
    "grid.scheme": ("Etiquetas", "Tags"),
    "grid.scheme.numbers_y": ("Verticais com números (1, 2, 3…), horizontais com letras (A, B, C…)",
                              "Vertical numbered (1, 2, 3…), horizontal lettered (A, B, C…)"),
    "grid.scheme.letters_y": ("Verticais com letras (A, B, C…), horizontais com números (1, 2, 3…)",
                              "Vertical lettered (A, B, C…), horizontal numbered (1, 2, 3…)"),
    "grid.renumber": ("Renumerar os eixos pela ordem (da esquerda para a direita, de baixo para cima)",
                      "Renumber the axes in order (left to right, bottom to top)"),
    "grid.dims": ("Cotas entre eixos nas plantas", "Dimensions between axes in plans"),
    "grid.bubble": ("Raio da bolha", "Bubble radius"),
    "grid.note": ("As cotas entre eixos acompanham a grelha: mudam sozinhas quando os eixos mudam.",
                  "The dimensions between axes follow the grid: they change by themselves with the axes."),
    "cmd.grid_settings": ("Grelha estrutural", "Structural grid"),
    "cmd.columns_on_grid": ("Pilares na grelha", "Columns on the grid"),
    "cmd.footings_under": ("Sapatas sob os pilares", "Footings under the columns"),
    "cmd.beams_between": ("Vigas entre pilares", "Beams between columns"),
    "cmd.walls_under_beams": ("Paredes sob as vigas", "Walls under the beams"),
    "cmd.slabs_in_bays": ("Lajes nos vãos das vigas", "Slabs in the beams' bays"),
    "cmd.beam_system": ("Sistema de vigas", "Beam system"),
    "cmd.propose_structure": ("Propor estrutura", "Propose a structure"),
    "cmd.remove_proposal": ("Remover a proposta de estrutura", "Remove the proposed structure"),
    "act.propose_structure": ("Propor estrutura…", "Propose a structure…"),
    "act.remove_proposal": ("Remover proposta", "Remove proposal"),
    "tip.propose_structure": ("A partir das paredes do pavimento (ou das selecionadas): pilares nos cantos, encontros "
                              "e cruzamentos, e mais pelo vão máximo; vigas entre eles ao longo das paredes (as "
                              "paredes descem até à viga); sapatas. Fazer outra vez substitui a proposta.",
                              "From the storey's walls (or those selected): columns at corners, junctions and "
                              "crossings, more by the largest span; beams between them along the walls (the walls go "
                              "down to the beam); footings. Doing it again replaces the proposal."),
    "tip.remove_proposal": ("Apaga a estrutura proposta neste pavimento; as paredes voltam à altura que tinham.",
                            "Deletes the structure proposed on this storey; the walls go back to their height."),
    "prop.title": ("Propor estrutura", "Propose a structure"),
    "prop.note": ("A partir das paredes do pavimento ativo (ou das selecionadas). Tudo fica marcado como proposta: "
                  "fazer outra vez substitui-a; «Remover proposta» apaga-a.",
                  "From the active storey's walls (or those selected). All of it is marked as the proposal: doing it "
                  "again replaces it; “Remove proposal” deletes it."),
    "prop.span": ("Vão máximo entre pilares", "Largest span between columns"),
    "prop.column": ("Pilares", "Columns"),
    "prop.beam": ("Vigas", "Beams"),
    "prop.footings": ("Sapatas", "Footings"),
    "prop.no_footings": ("(sem sapatas)", "(no footings)"),
    "info.proposal": ("Estrutura proposta: {c} pilar(es), {b} viga(s), {f} sapata(s). Ctrl+Z desfaz; «Remover "
                      "proposta» apaga-a.",
                      "Proposed structure: {c} column(s), {b} beam(s), {f} footing(s). Ctrl+Z undoes; “Remove "
                      "proposal” deletes it."),
    "info.proposal_no_walls": ("Não há paredes neste pavimento para propor a estrutura.",
                               "There are no walls on this storey to propose a structure from."),
    "info.proposal_removed": ("Proposta de estrutura removida; as paredes voltaram à altura que tinham.",
                              "Proposed structure removed; the walls are back to their height."),
    "info.proposal_none": ("Não há proposta de estrutura neste pavimento.", "There is no proposed structure on this "
                           "storey."),
    "act.beam_system": ("Sistema de vigas…", "Beam system…"),
    "tip.beam_system": ("Vigas paralelas (ou em grelha) dentro de cada vão fechado pelas vigas selecionadas, por "
                        "número ou espaçamento. Ficam presas ao vão: refazem-se quando ele muda.",
                        "Parallel beams (or a grid of them) in each bay closed by the beams selected, by number or "
                        "spacing. They stay tied to the bay: laid again when it changes."),
    "bsys.title": ("Sistema de vigas", "Beam system"),
    "bsys.way": ("Direção", "Direction"),
    "bsys.way.x": ("Ao longo de X (vermelho)", "Along X (red)"),
    "bsys.way.y": ("Ao longo de Y (verde)", "Along Y (green)"),
    "bsys.way.grid": ("Grelha (nas duas direções)", "Grid (both ways)"),
    "bsys.mode": ("Como", "How"),
    "bsys.mode.count": ("Número de vigas", "Number of beams"),
    "bsys.mode.spacing": ("Espaçamento (m)", "Spacing (m)"),
    "bsys.value": ("Valor", "Value"),
    "bsys.type": ("Tipo de viga", "Beam type"),
    "info.beam_system": ("{n} viga(s) do sistema, presas aos vãos. Ctrl+Z desfaz.",
                         "{n} beam(s) of the system, tied to the bays. Ctrl+Z undoes."),
    "info.beam_system_none": ("Não há vãos fechados por vigas entre pilares nessa seleção.",
                              "There are no bays closed by beams between columns in that selection."),
    "act.slabs_in_bays": ("Lajes", "Slabs"),
    "tip.slabs_in_bays": ("Uma laje em cada vão fechado pelas vigas selecionadas (nenhuma: todas as do pavimento), "
                          "entre as faces de dentro das vigas, com o topo no topo delas e o tipo da ferramenta Laje. "
                          "Fica presa às vigas: refaz-se quando elas mudam. (Por agora, vãos retangulares.)",
                          "A slab in each bay closed by the beams selected (none: all on the storey), between the "
                          "beams' inner faces, its top at theirs, with the Slab tool's type. It stays tied to the "
                          "beams: made again when they change. (For now, rectangular bays.)"),
    "info.slabs_in_bays": ("{n} laje(s) nos vãos das vigas, presas a elas. Ctrl+Z desfaz.",
                           "{n} slab(s) in the beams' bays, tied to them. Ctrl+Z undoes."),
    "info.slabs_in_bays_skipped": (" {k} vão(s) não retangular(es) ficaram sem laje.",
                                   " {k} bay(s) that are not rectangles were left without a slab."),
    "info.slabs_in_bays_none": ("Não há vãos fechados por vigas sem laje (as vigas têm de ir de pilar a pilar).",
                                "There are no bays closed by beams without a slab (beams must go column to column)."),
    "act.walls_under_beams": ("Paredes", "Walls"),
    "tip.walls_under_beams": ("Paredes entre os pilares, sob as vigas selecionadas (nenhuma: todas as do "
                              "pavimento): de face a face dos pilares, da base deles até à face de baixo da viga, "
                              "com o tipo da ferramenta Parede. Ficam presas à viga: acompanham-na.",
                              "Walls between the columns, under the beams selected (none: all on the storey): face "
                              "to face of the columns, from their base up to the beam's underside, with the Wall "
                              "tool's type. They stay tied to the beam: they follow it."),
    "info.walls_under_beams": ("{n} parede(s) sob as vigas, presas a elas. Ctrl+Z desfaz.",
                               "{n} wall(s) under the beams, tied to them. Ctrl+Z undoes."),
    "info.walls_under_beams_none": ("Essas vigas já têm parede por baixo (ou não estão entre pilares).",
                                    "Those beams have their wall already (or are not between columns)."),
    "act.beams_between": ("Vigas entre pilares", "Beams between columns"),          # (0.324: was «Vigas»)
    "tip.beams_between": ("Vigas entre os pilares selecionados (nenhum: todos os do pavimento) alinhados em X ou Y, "
                          "só entre vizinhos, de face a face, com o topo no topo dos pilares e o tipo da "
                          "ferramenta Viga. Ficam presas aos pilares: acompanham-nos.",
                          "Beams between the columns selected (none: all on the storey) in line along X or Y, only "
                          "between neighbours, face to face, their top at the columns' top, with the Beam tool's "
                          "type. They stay tied to the columns: they follow them."),
    "info.beams_between": ("{n} viga(s) entre os pilares, presas a eles. Ctrl+Z desfaz.",
                           "{n} beam(s) between the columns, tied to them. Ctrl+Z undoes."),
    "info.beams_between_none": ("Não há pilares vizinhos alinhados sem viga entre eles.",
                                "There are no neighbouring columns in line without a beam between them."),
    "act.footings_under": ("Sapatas", "Footings"),
    "tip.footings_under": ("Uma sapata sob cada pilar selecionado (nenhum: todos os do pavimento), com o tipo de "
                           "sapata isolada da ferramenta Sapata. Fica presa ao pilar: vai com ele.",
                           "A footing under each column selected (none: all on the storey), with the Footing tool's "
                           "pad type. It stays tied to the column: it goes with it."),
    "info.footings_under": ("{n} sapata(s) sob os pilares, presas a eles. Ctrl+Z desfaz.",
                            "{n} footing(s) under the columns, tied to them. Ctrl+Z undoes."),
    "info.footings_under_none": ("Esses pilares já têm sapata.", "Those columns have their footing already."),
    "act.combined_footing": ("Sapata combinada", "Combined footing"),                                    # (0.249)
    "tip.combined_footing": ("Uma sapata sob os dois pilares selecionados, ao longo da linha entre eles, com o tipo de "
                             "sapata isolada da ferramenta Sapata (a sua largura; o seu comprimento para lá de cada "
                             "pilar). Fica presa aos dois: refaz-se quando se movem. As sapatas que já tinham ficam: "
                             "apague-as se esta as substitui.",
                             "A footing under the two columns selected, along the line between them, with the Footing "
                             "tool's pad type (its width; its length past each column). Tied to both: made again when "
                             "they move. Their own footings stay: delete them if this one replaces them."),
    "cmd.combined_footing": ("Sapata combinada", "Combined footing"),
    "info.combined_footing": ("Sapata combinada feita sob os dois pilares. Ctrl+Z desfaz.",
                              "Combined footing made under the two columns. Ctrl+Z undoes."),
    "info.combined_footing_none": ("Selecione dois pilares (e só dois) em sítios diferentes.",
                                   "Select two columns (and only two) in different places."),
    "act.columns_on_grid": ("Pilares na grelha", "Columns on grid"),                # (0.324: was «Inserir pilares»)
    "tip.columns_on_grid": ("Um pilar em cada cruzamento dos eixos selecionados (só eixos de um sentido: onde "
                            "cruzam os do outro; nenhum: em todos), com o tipo e a altura da ferramenta Pilar. "
                            "Ficam presos aos eixos: acompanham-nos.",
                            "A column at each crossing of the axes selected (axes one way only: where they cross the "
                            "others; none: at all), with the Column tool's type and height. They stay tied to the "
                            "axes: they go with them."),
    "info.columns_on_grid": ("{n} pilar(es) colocados nos cruzamentos dos eixos, presos a eles. Ctrl+Z desfaz.",
                             "{n} column(s) placed at the axes' crossings, tied to them. Ctrl+Z undoes."),
    "info.no_grid": ("Ainda não há eixos: desenhe-os (ferramenta Eixo) ou gere-os de uma vez.",
                     "There are no axes yet: draw them (Grid axis tool) or generate them all at once."),
    "info.columns_on_grid_none": ("Não há cruzamentos sem pilar nesses eixos.",
                                  "There are no crossings without a column on those axes."),
    "info.grid_settings": ("Grelha estrutural atualizada. Ctrl+Z desfaz.", "Structural grid updated. Ctrl+Z undoes."),
    "gen.spacing": ("   distância entre eles (m)", "   spacing (m)"),
    "gen.origin": ("Primeiro cruzamento em (x; y)", "First crossing at (x; y)"),
    "gen.extension": ("Os eixos passam dos últimos (m)", "Axes reach past the last ones by (m)"),
    "gen.replace": ("Substituir os eixos que já existem", "Replace the axes there are"),
    "hint.grid.next": ("Clique no fim do eixo ou digite o comprimento e Enter. Esc cancela.",
                       "Click the axis's end or type its length and Enter. Esc cancels."),
    "info.grid_axis": ("Eixo {tag} criado ({l}). Os cruzamentos dos eixos são pontos de snap (para os pilares).",
                       "Axis {tag} made ({l}). Where the axes cross are snap points (for the columns)."),
    "tree.grid": ("Eixos", "Grid"),
    "tree.grid_axis": ("Eixo {tag}", "Axis {tag}"),
    "tree.remove_grid_axis": ("Apagar este eixo", "Delete this axis"),
    "err.grid_tag": ("Já há um eixo «{tag}» (ou o nome está vazio).", "There is already an axis \"{tag}\" (or the "
                     "name is empty)."),
    "cmd.grid_rename": ("Mudar o nome do eixo", "Rename grid axis"),
    "cmd.grid_remove": ("Apagar eixo", "Delete grid axis"),
    "cmd.beam": ("Viga", "Beam"),
    "cmd.steel_member": ("Peça metálica", "Steel member"),          # (0.495)
    "cmd.steel_mitre": ("Meia-esquadria", "Mitre"),                 # (0.496)
    "cmd.steel_shed": ("Pórtico de nave", "Steel shed"),             # (0.499)
    # (0.497) steel connections
    "cmd.base_plate": ("Chapa de base", "Base plate"),
    "cmd.connection": ("Ligação metálica", "Steel connection"),
    "act.base_plate": ("Chapa de base", "Base plate"),
    "tip.base_plate": ("Põe uma chapa de base, com os chumbadouros e a soldadura, debaixo dos pilares de aço escolhidos "
                       "— sem nenhum escolhido, debaixo de todos os que ainda não têm.",
                       "Puts a base plate, with its anchor bolts and weld, under the steel columns selected — none "
                       "selected: under every one that has none yet."),
    "info.base_plates": ("{n} chapa(s) de base com os chumbadouros e a soldadura. Escolha uma para mudar as medidas "
                         "nas Propriedades.",
                         "{n} base plate(s) with their anchor bolts and weld. Select one to change its sizes in the "
                         "Properties."),
    "info.base_plates_none": ("Não há pilares de aço sem chapa de base (escolha pilares com um perfil de aço).",
                              "No steel columns without a base plate (select columns of a steel section)."),
    "props.connection": ("Ligação", "Connection"),
    "props.g.connection": ("Ligação — {what}", "Connection — {what}"),
    "props.connection_joins": ("Liga", "Joins"),
    "connection.base_plate": ("Chapa de base", "Base plate"),
    # (0.498) beam to column
    "connection.end_plate": ("Chapa de topo", "End plate"),
    "connection.fin_plate": ("Cutelo", "Fin plate"),
    "cmd.end_plate": ("Chapa de topo", "End plate"),
    "cmd.fin_plate": ("Cutelo", "Fin plate"),
    "act.end_plate": ("Chapa de topo", "End plate"),
    "act.fin_plate": ("Cutelo", "Fin plate"),
    "tip.end_plate": ("Nas vigas de aço escolhidas, em cada ponta que chega a um pilar de aço: uma chapa de topo soldada "
                      "à viga e aparafusada ao pilar (ligação rígida).",
                      "On the steel beams selected, at each end reaching a steel column: an end plate welded to the "
                      "beam and bolted to the column (a rigid joint)."),
    "tip.fin_plate": ("Nas vigas de aço escolhidas, em cada ponta que chega a um pilar de aço: um cutelo soldado ao pilar "
                      "e aparafusado à alma da viga (ligação articulada).",
                      "On the steel beams selected, at each end reaching a steel column: a fin plate welded to the "
                      "column and bolted to the beam's web (a pinned joint)."),
    "info.beam_connections": ("{n} ligação(ões) «{what}» nas pontas das vigas que chegam a pilares de aço.",
                              "{n} «{what}» connection(s) at the beams' ends reaching steel columns."),
    "info.beam_connections_none": ("Escolha vigas de aço cujas pontas cheguem a pilares de aço (e ainda sem ligação).",
                                   "Select steel beams whose ends reach steel columns (with no connection yet)."),
    "connection.field.W": ("Largura da chapa (mm; 0: a da viga)", "Plate width (mm; 0: the beam's)"),
    "connection.field.top": ("Chapa acima da viga (mm)", "Plate over the beam (mm)"),
    "connection.field.bottom": ("Chapa abaixo da viga (mm)", "Plate under the beam (mm)"),
    "connection.field.rows": ("Fiadas de parafusos", "Rows of bolts"),
    "connection.field.p": ("Passo entre fiadas (mm)", "Pitch (mm)"),
    "connection.field.g": ("Distância entre parafusos (mm; 0: automática)", "Gauge (mm; 0: automatic)"),
    "connection.field.w": ("Largura do cutelo ao longo da viga (mm)", "Fin plate width along the beam (mm)"),
    "connection.field.eh": ("Parafusos à face do pilar (mm)", "Bolts from the column's face (mm)"),
    "connection.warn.gauge": ("⚠ Parafusos mais perto do que 2,4·d0 = {v} mm na horizontal (EN 1993-1-8, Quadro 3.3).",
                              "⚠ Bolts closer than 2.4·d0 = {v} mm across (EN 1993-1-8, Table 3.3)."),
    "connection.warn.web": ("⚠ Os parafusos batem na alma do pilar: afaste-os (pelo menos {v} mm entre eles).",
                            "⚠ The bolts hit the column's web: spread them (at least {v} mm apart)."),
    "connection.warn.wide": ("⚠ A chapa é mais larga do que o pilar ({v} mm).", "⚠ The plate is wider than the column "
                                                                               "({v} mm)."),
    "connection.warn.tall": ("⚠ O cutelo não cabe entre os banzos da viga ({v} mm).",
                             "⚠ The fin plate does not fit between the beam's flanges ({v} mm)."),
    "connection.gusset": ("Gousset", "Gusset plate"),                                                 # (0.503)
    "cmd.gusset": ("Gousset", "Gusset plate"),
    "act.gusset": ("Gousset", "Gusset plate"),
    "tip.gusset": ("Nos contraventamentos em cantoneira escolhidos (nenhum escolhido: em todos), em cada ponta que chega "
                   "a um pilar de aço: um gousset soldado ao pilar, o contraventamento recuado e aparafusado a ele.",
                   "On the angle braces selected (none selected: on all of them), at each end reaching a steel column: "
                   "a gusset plate welded to the column, the brace held back and bolted to it."),
    "info.gussets": ("{n} gousset(s) nas pontas dos contraventamentos que chegam a pilares de aço.",
                     "{n} gusset plate(s) at the ends of the braces reaching steel columns."),
    "info.gussets_none": ("Nenhum contraventamento em cantoneira chega a um pilar de aço sem gousset.",
                          "No angle brace reaches a steel column without a gusset plate."),
    "connection.field.gap": ("Folga do contraventamento ao pilar (mm)", "Brace clear of the column (mm)"),
    "connection.field.edge": ("Chapa para além da aba (mm)", "Plate past the leg (mm)"),
    "connection.field.gusset.g": ("Parafusos ao canto da cantoneira (mm; 0: automático)",
                                  "Bolts from the angle's heel (mm; 0: automatic)"),
    "connection.field.gusset.rows": ("Parafusos ao longo do contraventamento", "Bolts along the brace"),
    "connection.field.gusset.p": ("Passo entre parafusos (mm)", "Pitch (mm)"),
    "connection.warn.root": ("⚠ O furo fica na raiz da cantoneira: os parafusos a pelo menos {v} mm do canto.",
                             "⚠ The hole falls in the angle's root: the bolts at least {v} mm from its heel."),
    "refuse.connection_brace_angle": ("o gousset liga contraventamentos em cantoneira (um tubo precisa de outra ligação)",
                                      "a gusset plate joins angle braces (a tube needs another connection)"),
    "connection.field.A": ("Largura da chapa (mm; 0: automática)", "Plate width (mm; 0: automatic)"),
    "connection.field.B": ("Comprimento da chapa (mm; 0: automático)", "Plate length (mm; 0: automatic)"),
    "connection.field.tp": ("Espessura da chapa (mm)", "Plate thickness (mm)"),
    "connection.field.n": ("Chumbadouros", "Anchor bolts"),
    "connection.field.d": ("Diâmetro", "Diameter"),
    "connection.field.e": ("Distância ao bordo (mm)", "Edge distance (mm)"),
    "connection.field.proj": ("Saliência acima da chapa (mm)", "Projection over the plate (mm)"),
    "connection.field.embed": ("Amarração no betão (mm)", "Embedment (mm)"),
    "connection.field.grout": ("Argamassa de selagem (mm)", "Grout (mm)"),
    "connection.field.a": ("Garganta da soldadura a (mm)", "Weld throat a (mm)"),
    "connection.warn.edge": ("⚠ Distância ao bordo menor que 1,2·d0 = {v} mm (EN 1993-1-8, Quadro 3.3).",
                             "⚠ Edge distance under 1.2·d0 = {v} mm (EN 1993-1-8, Table 3.3)."),
    "connection.warn.pitch": ("⚠ Chumbadouros mais perto do que 2,2·d0 = {v} mm (EN 1993-1-8, Quadro 3.3).",
                              "⚠ Anchor bolts closer than 2.2·d0 = {v} mm (EN 1993-1-8, Table 3.3)."),
    "connection.warn.small": ("⚠ A chapa não é maior do que o pilar.", "⚠ The plate is not bigger than the column."),
    "connection.warn.clash": ("⚠ Um chumbadouro bate no pilar: aumente a chapa ou a distância.",
                              "⚠ An anchor bolt clashes with the column: make the plate bigger or move it."),
    "act.steel_mitre": ("Meia-esquadria", "Mitre"),
    "tip.steel_mitre": ("Corta duas peças metálicas escolhidas em meia-esquadria onde as linhas se encontram (o "
                        "joelho de um pórtico).",
                        "Cuts the two steel pieces selected to a mitre where their lines meet (a portal's knee)."),
    "info.steel_mitre_pick": ("Escolha duas peças metálicas (Selecionar, Shift + clique) e depois Meia-esquadria.",
                              "Select two steel pieces (Select, Shift + click), then Mitre."),
    "info.steel_mitre_no": ("As linhas das duas peças não se encontram (paralelas, ou a mais de 50 cm).",
                            "The two pieces' lines do not meet (parallel, or more than 50 cm apart)."),
    "info.steel_mitre": ("{a} e {b} em meia-esquadria.", "{a} and {b} mitred."),
    "cmd.x_brace": ("Contraventamento entre pilares", "Bracing between columns"),
    "tool.wall": ("Parede", "Wall"),
    "tool.slab": ("Laje", "Slab"),
    "tool.column": ("Pilar", "Column"),
    "tool.beam": ("Viga", "Beam"),
    "tool.steel_member": ("Peça metálica", "Steel member"),          # (0.495)
    "tool.steel_shed": ("Pórtico de nave", "Steel shed"),            # (0.499)
    "ctx.shed_column": ("Pilares", "Columns"),
    "ctx.shed_rafter": ("Asnas", "Rafters"),
    "ctx.shed_purlin": ("Madres", "Purlins"),
    "ctx.shed_brace": ("Contraventamentos", "Bracing"),
    "ctx.shed_span": ("Vão", "Span"),
    "ctx.shed_eave": ("Altura do beirado", "Eaves' height"),
    "ctx.shed_slope": ("Inclinação", "Slope"),
    "ctx.shed_spacing": ("Afastamento dos pórticos", "Frames' spacing"),
    "ctx.shed_purlins": ("Afastamento das madres", "Purlins' spacing"),
    "ctx.shed_bracing": ("Contraventar", "Bracing"),
    "ctx.shed_plates": ("Chapas de base", "Base plates"),
    "hint.shed_start": ("Pórtico de nave: clique no início da primeira fila de pilares (o vão fica para a esquerda; as "
                        "medidas e os perfis na barra).",
                        "Steel shed: click the start of the first line of columns (the span goes to its left; sizes "
                        "and sections on the bar)."),
    "hint.shed_end": ("Clique no fim da fila (ou escreva o comprimento e Enter): a nave faz-se com {span} de vão.",
                      "Click the line's end (or type the length and Enter): the shed is made {span} wide."),
    "info.shed": ("Nave de {l} × {s}: {n} pórticos, madres, contraventamentos e chapas de base ({pieces} peças). Ctrl+Z "
                  "desfaz tudo.",
                  "Shed {l} × {s}: {n} frames, purlins, bracing and base plates ({pieces} pieces). Ctrl+Z undoes it "
                  "all."),
    "info.shed_types": ("Escolha perfis de aço para os pilares, asnas, madres e contraventamentos.",
                        "Choose steel sections for the columns, rafters, purlins and bracing."),
    "ctx.steel_mode": ("Desenhar", "Draw"),
    "steel_mode.line": ("Entre dois pontos", "Between two points"),
    "steel_mode.x": ("Contraventamento em X", "X bracing"),
    "steel_mode.slash": ("Diagonal ╱", "Diagonal ╱"),
    "steel_mode.backslash": ("Diagonal ╲", "Diagonal ╲"),
    "ctx.steel_function": ("Função", "Function"),
    "steel_function.beam": ("Viga", "Beam"),
    "steel_function.column": ("Pilar", "Column"),
    "steel_function.brace": ("Contraventamento", "Brace"),
    "steel_function.purlin": ("Madre", "Purlin"),
    "steel_function.member": ("Elemento", "Member"),
    "ctx.steel_cardinal": ("Inserção", "Insertion"),
    "steel_cardinal.auto": ("Automática", "Automatic"),
    "steel_cardinal.1": ("Em baixo, à esquerda", "Bottom left"),
    "steel_cardinal.2": ("Em baixo, ao meio", "Bottom middle"),
    "steel_cardinal.3": ("Em baixo, à direita", "Bottom right"),
    "steel_cardinal.4": ("A meio, à esquerda", "Middle left"),
    "steel_cardinal.5": ("Ao centro", "Centre"),
    "steel_cardinal.6": ("A meio, à direita", "Middle right"),
    "steel_cardinal.7": ("Em cima, à esquerda", "Top left"),
    "steel_cardinal.8": ("Em cima, ao meio", "Top middle"),
    "steel_cardinal.9": ("Em cima, à direita", "Top right"),
    "ctx.steel_rotation": ("Rotação", "Rotation"),
    "ctx.steel_heights": ("Alturas", "Heights"),
    "steel_heights.levels": ("Pelas cotas", "By the levels"),
    "steel_heights.points": ("Pelos pontos (3D)", "By the points (3D)"),
    "ctx.steel_z0": ("Cota no início", "Start level"),
    "ctx.steel_z1": ("Cota no fim", "End level"),
    "hint.steel_start": ("{what} {type}: clique no início da linha (as cotas na barra; em 3D, «pelos pontos» apanha "
                         "o topo de um pilar).",
                         "{what} {type}: click the line's start (the levels on the bar; in 3D, «by the points» takes "
                         "a column's top)."),
    "hint.steel_next": ("Clique no fim (ou escreva o comprimento e Enter). A próxima começa aí; Esc acaba.",
                        "Click the end (or type the length and Enter). The next starts there; Esc ends."),
    "hint.steel_brace": ("Contraventamento {type}: clique no primeiro pilar.",
                         "Bracing {type}: click the first column."),
    "hint.steel_brace_2": ("Clique no segundo pilar.", "Click the second column."),
    "info.steel_member": ("{what} {type} com {l}.", "{what} {type}, {l} long."),
    "info.steel_pick_column": ("Clique num pilar.", "Click a column."),
    "info.steel_braced": ("{n} contraventamento(s) entre {a} e {b}.", "{n} brace(s) between {a} and {b}."),
    "act.wall_types": ("Parede", "Wall"),
    "act.slab_types": ("Laje", "Slab"),
    "act.roof_types": ("Cobertura", "Roof"),                         # (0.278)
    "act.column_types": ("Pilar", "Column"),
    "act.beam_types": ("Viga", "Beam"),
    "hint.column": ("{type}, {h} de altura: clique onde fica o pilar (o meio do pé; snaps e alinhamentos). Digite "
                    "a altura (ex.: 3,00) e Enter para a mudar. Esc termina.",
                    "{type}, {h} tall: click where the column stands (the middle of its foot; snaps and "
                    "alignments). Type the height (e.g. 3.00) and Enter to change it. Esc ends."),
    "hint.beam.start": ("{type}, topo a {h}: clique no início da viga (o eixo; snaps e alinhamentos: o topo de um "
                        "pilar…). Digite a cota do topo (ex.: 2,80) e Enter para a mudar.",
                        "{type}, top at {h}: click the beam's start (its axis; snaps and alignments: a column's "
                        "top…). Type its top's height (e.g. 2.80) and Enter to change it."),
    "hint.beam.next": ("Clique no fim da viga ou digite o comprimento e Enter. Esc termina.",
                       "Click the beam's end or type its length and Enter. Esc ends."),
    "info.column": ("Pilar criado ({type}, {h} de altura).", "Column made ({type}, {h} tall)."),
    "info.beam": ("Viga de {l} criada ({type}, topo a {h}).", "{l} beam made ({type}, top at {h})."),
    "info.column_height": ("Os pilares passam a ter {h} de altura.", "Columns are now {h} tall."),
    "info.beam_top": ("O topo das vigas passa a ficar a {h}.", "Beam tops are now at {h}."),
    "props.beam_top": ("Cota do topo", "Top height"),
    "cmd.footing": ("Sapata", "Footing"),
    "tool.footing": ("Sapata", "Footing"),
    "act.footing_types": ("Sapata", "Footing"),
    "hint.footing": ("Clique num pilar: sapata isolada por baixo ({pad}). Clique numa parede: sapata corrida a todo o "
                     "comprimento ({strip}). Clique noutro sítio: sapata isolada aí, com o topo na cota do pavimento. "
                     "Esc termina.",
                     "Click a column: a pad footing under it ({pad}). Click a wall: a strip footing along it "
                     "({strip}). Click anywhere else: a pad there, its top at the storey level. Esc ends."),
    "tip.footing.column": ("Sapata isolada sob o pilar ({type})", "Pad footing under the column ({type})"),
    "tip.footing.wall": ("Sapata corrida sob a parede ({type})", "Strip footing under the wall ({type})"),
    "tip.footing.free": ("Sapata isolada aqui ({type})", "Pad footing here ({type})"),
    "info.footing": ("Sapata criada ({type}: {a} × {b}, {d} de altura).",
                     "Footing made ({type}: {a} × {b}, {d} deep)."),
    "props.footing_top": ("Cota do topo", "Top height"),
    "cmd.pipe": ("Tubo", "Pipe"),
    "cmd.duct": ("Conduta", "Duct"),
    "tool.pipe": ("Tubo", "Pipe"),
    "tool.duct": ("Conduta", "Duct"),
    "act.pipe_types": ("Tubo", "Pipe"),
    "act.duct_types": ("Conduta", "Duct"),
    "hint.segment.start": ("{type}, eixo a {h}: clique no início (snaps e alinhamentos). Digite a cota do eixo "
                           "(ex.: 0,30) e Enter para a mudar.",
                           "{type}, axis at {h}: click the start (snaps and alignments). Type the axis height "
                           "(e.g. 0.30) and Enter to change it."),
    "hint.segment.next": ("Clique no fim ou digite o comprimento e Enter; segue a partir daí. Esc termina.",
                          "Click the end or type the length and Enter; it goes on from there. Esc ends."),
    "info.pipe": ("Tubo de {l} criado ({type}, eixo a {h}).", "{l} pipe made ({type}, axis at {h})."),
    "info.duct": ("Conduta de {l} criada ({type}, eixo a {h}).", "{l} duct made ({type}, axis at {h})."),
    "info.segment_z": ("O eixo passa a ficar a {h} acima do pavimento.", "The axis is now {h} above the storey."),
    "warn.above_cut": ("{done} Fica acima do plano de corte desta planta ({h}), por isso não se vê aqui: veja no 3D "
                       "(F4).",
                       "{done} It is above this plan's cut plane ({h}), so it is not seen here: look in 3D (F4)."),
    "info.above_cut_dashed": ("{done} Fica acima do corte desta planta ({h}): mostra-se a tracejado.",
                              "{done} It is above this plan's cut ({h}): it is shown dashed."),
    "props.axis_z": ("Cota do eixo", "Axis height"),
    "ctx.slope": ("Inclinação", "Slope"),
    "ctx.segment_form": ("Forma", "Form"),
    "segform.run": ("Ramal (ponto a ponto)", "Run (point by point)"),
    "segform.stack": ("Tubo de queda (vertical)", "Stack (vertical)"),
    "ctx.stack_top": ("Topo a", "Top at"),
    "ctx.stack_bottom": ("Pé a", "Foot at"),
    "hint.segment.stack": ("{type}, tubo de queda de {a} a {b} do pavimento: clique onde fica. Digite a cota do "
                           "topo (ex.: 6,10) e Enter para a mudar.",
                           "{type}, stack from {a} to {b} over the storey: click where it goes. Type the top's "
                           "height (e.g. 6.10) and Enter to change it."),
    "tip.segment_go_on": ("Continuar a partir daqui (eixo a {h})", "Go on from here (axis at {h})"),
    "tip.segment_tee_from": ("Começar aqui, com um tê (eixo a {h})", "Start here, with a tee (axis at {h})"),
    "tip.segment_tee_to": ("Ligar aqui com um tê", "Join here with a tee"),
    "info.segment_tee": ("{done} Ligado ao outro com um tê.", "{done} Joined to the other one with a tee."),
    # (0.195) a run ended over (or under) a pipe at another height: straight down (up) to it, a tee there
    "tip.segment_tee_down": ("Desce {d} até este tubo e liga-se com um tê", "Goes down {d} to this pipe, a tee there"),
    "tip.segment_tee_up": ("Sobe {d} até este tubo e liga-se com um tê", "Goes up {d} to this pipe, a tee there"),
    "info.segment_tee_down": ("{done} Desce {name} na vertical e liga-se ao outro com um tê. Ctrl+Z desfaz tudo.",
                              "{done} Goes down {name} upright and joins the other one with a tee. Ctrl+Z undoes it "
                              "all."),
    "info.segment_tee_up": ("{done} Sobe {name} na vertical e liga-se ao outro com um tê. Ctrl+Z desfaz tudo.",
                            "{done} Goes up {name} upright and joins the other one with a tee. Ctrl+Z undoes it all."),
    "info.segment_sloped": ("{what} de {l} criado ({type}, inclinação {s}: o eixo desce de {h} a {h2}).",
                            "{what}, {l}, made ({type}, slope {s}: the axis falls from {h} to {h2})."),
    "info.riser_up": ("Subida de {d}, com uma curva em cada ponta; continua com o eixo a {h}.",
                      "A {d} riser up, a bend at each end; it goes on with the axis at {h}."),
    "info.riser_down": ("Descida de {d}, com uma curva em cada ponta; continua com o eixo a {h}.",
                        "A {d} drop, a bend at each end; it goes on with the axis at {h}."),
    "info.stack": ("Tubo de queda de {l} criado ({type}), de {a} a {b} do pavimento. Um tubo desenhado a partir "
                   "do pé continua-o, com uma curva.",
                   "{l} stack made ({type}), from {a} to {b} over the storey. A pipe drawn from its foot goes on "
                   "from it, with a bend."),
    "err.stack_short": ("O topo do tubo de queda tem de ficar acima do pé.", "The stack's top must be above its foot."),
    "props.end_z": ("Cota do eixo no fim", "Axis height at the end"),
    "props.vertical_from": ("Vertical, de", "Vertical, from"),
    "hint.wall.start": ("{type} · desenha-se {ref} (Tab muda): clique no início, depois em cada canto; digite o "
                        "comprimento (ex.: 4,50) e Enter para medidas exatas.",
                        "{type} · drawn {ref} (Tab changes it): click the start, then each corner; type the "
                        "length (e.g. 4.50) and Enter for exact sizes."),
    "hint.wall.next": ("Desenha-se {ref} (Tab muda). Clique no fim da parede ou digite o comprimento + Enter "
                       "(\"4,50;3,00\" muda também a altura). Esc termina.",
                       "Drawn {ref} (Tab changes it). Click the wall end or type the length + Enter (\"4.50;3.00\" "
                       "also sets the height). Esc ends."),
    "ref.axis": ("pelo eixo", "by the axis"),
    "ref.left": ("pela face esquerda", "by the left face"),
    "ref.right": ("pela face direita", "by the right face"),
    "info.wall_reference": ("A parede desenha-se agora {ref} (esquerda/direita no sentido em que desenha).",
                            "The wall is now drawn {ref} (left/right as seen in the drawing direction)."),
    "hint.slab.start": ("{type}: clique no primeiro canto. Na cota do pavimento = laje de piso; num canto do topo das "
                        "paredes = laje de cobertura. (Tab muda a forma: polígono, círculo, varinha mágica.)",
                        "{type}: click the first corner. At the storey level = floor slab; on a top corner of the "
                        "walls = roof slab. (Tab changes the shape: polygon, circle, magic wand.)"),
    # slabs by their outline (0.100)
    "ctx.slab_shape": ("Forma", "Shape"),
    "ctx.slab_function": ("Função", "Function"),
    "ctx.slab_reach": ("Contorno", "Outline"),
    "slabshape.rect": ("Retângulo", "Rectangle"),
    "slabshape.poly": ("Polígono", "Polygon"),
    "slabshape.circle": ("Círculo", "Circle"),
    # (0.456) Revit's «Draw» panel on a floor, a ceiling, a slab
    "slabshape.poly_in": ("Polígono inscrito", "Inscribed polygon"),
    "slabshape.poly_out": ("Polígono circunscrito", "Circumscribed polygon"),
    "slabshape.ellipse": ("Elipse", "Ellipse"),
    "slabshape.pick": ("Escolher linhas (o contorno das linhas clicadas)", "Pick lines (the outline of the lines "
                       "clicked)"),
    "ceilshape.circle": ("Círculo", "Circle"),
    "ceilshape.poly_in": ("Polígono inscrito", "Inscribed polygon"),
    "ceilshape.poly_out": ("Polígono circunscrito", "Circumscribed polygon"),
    "ceilshape.ellipse": ("Elipse", "Ellipse"),
    "ceilshape.pick": ("Escolher linhas (o contorno das linhas clicadas)", "Pick lines (the outline of the lines "
                       "clicked)"),
    "ctx.sides": ("Lados", "Sides"),
    "ctx.region_outline": ("Contorno", "Outline"),
    "ctx.outline_offset": ("Afastamento", "Offset"),
    "hint.outline.circle_0": ("Círculo: clique no centro. (Tab muda a forma.)", "Circle: click its centre. (Tab "
                              "changes the shape.)"),
    "hint.outline.poly_in_0": ("Polígono inscrito de {n} lados: clique no centro (os lados na barra).",
                               "Inscribed polygon of {n} sides: click its centre (the sides on the bar)."),
    "hint.outline.poly_in_1": ("Clique num canto do polígono — ou escreva o raio até um canto e Enter. Esc desiste.",
                               "Click a corner of the polygon — or type the radius to a corner and Enter. Esc gives "
                               "up."),
    "hint.outline.poly_out_0": ("Polígono circunscrito de {n} lados: clique no centro (os lados na barra).",
                                "Circumscribed polygon of {n} sides: click its centre (the sides on the bar)."),
    "hint.outline.poly_out_1": ("Clique no meio de um lado — ou escreva a distância do centro ao lado e Enter. Esc "
                                "desiste.", "Click the middle of a side — or type the distance from the centre to a "
                                "side and Enter. Esc gives up."),
    "hint.outline.ellipse_0": ("Elipse: clique no centro.", "Ellipse: click its centre."),
    "hint.outline.ellipse_1": ("Clique na ponta de um eixo — ou escreva esse semieixo e Enter.",
                               "Click the end of one axis — or type that half-axis and Enter."),
    "hint.outline.ellipse_2": ("Mova o rato para a largura e clique — ou escreva o outro semieixo e Enter.",
                               "Move the mouse for its width and click — or type the other half-axis and Enter."),
    "hint.outline.pick_0": ("Escolher linhas: clique numa linha, aresta, face de parede ou eixo — o contorno faz-se "
                            "das linhas clicadas, cada canto onde uma encontra a seguinte.",
                            "Pick lines: click a line, an edge, a wall's face or an axis — the outline is made of the "
                            "lines clicked, each corner where one meets the next."),
    "hint.outline.pick_1": ("Clique na linha seguinte ({n} escolhida). Delete tira a última; Esc desiste.",
                            "Click the next line ({n} picked). Delete takes the last back; Esc gives up."),
    "hint.outline.pick_2": ("Clique na linha seguinte ({n} escolhidas). Delete tira a última; Esc desiste.",
                            "Click the next line ({n} picked). Delete takes the last back; Esc gives up."),
    "hint.outline.pick_3": ("Mais linhas — ou clique de novo na primeira (ou Enter) para fechar ({n} escolhidas).",
                            "More lines — or click the first again (or Enter) to close ({n} picked)."),
    "err.outline_picked": ("As linhas escolhidas não fecham um contorno (duas seguidas paralelas, ou o contorno "
                           "cruza-se).", "The lines picked close no outline (two in a row parallel, or it crosses "
                           "itself)."),
    "slabshape.wand": ("Varinha mágica", "Magic wand"),
    "slabfn.estrutural": ("Estrutural", "Structural"),
    "slabfn.acabamento": ("Acabamento (sobre o nível)", "Finish (on the level)"),
    "slabfn.excluida": ("Excluída do cálculo", "Left out of the calculation"),
    "slabreach.interior": ("até às faces interiores das paredes", "to the walls' inner faces"),
    "slabreach.exterior": ("até às faces exteriores das paredes", "to the walls' outer faces"),
    "info.slab_shape": ("Forma da laje: {shape}. Tab muda.", "Slab shape: {shape}. Tab changes it."),
    "hint.slab.poly_start": ("{type}: clique no primeiro canto do contorno. (Tab muda a forma.)",
                             "{type}: click the outline's first corner. (Tab changes the shape.)"),
    "hint.slab.poly_next": ("Clique no canto seguinte ou digite o comprimento + Enter. Clique no primeiro canto (ou "
                            "Enter) fecha. Delete apaga o último canto. Esc desiste.",
                            "Click the next corner or type the length + Enter. A click on the first corner (or "
                            "Enter) closes it. Delete takes the last corner back. Esc gives up."),
    "hint.slab.circle_start": ("{type}: clique no centro do círculo. (Tab muda a forma.)",
                               "{type}: click the circle's centre. (Tab changes the shape.)"),
    "hint.slab.circle_end": ("Clique num ponto da borda ou digite o raio + Enter. Esc desiste.",
                             "Click a point of its edge or type the radius + Enter. Esc gives up."),
    "hint.slab.wand": ("{type}: clique dentro de paredes fechadas — a laje vai {reach}. (Tab muda a forma.)",
                       "{type}: click inside closed walls — the slab goes {reach}. (Tab changes the shape.)"),
    "keys.slab": ("Tab: retângulo → polígono → círculo → varinha mágica  ·  X / Y: bloquear o eixo  ·  N: soltar  ·  "
                  "Delete: apagar o último canto",
                  "Tab: rectangle → polygon → circle → magic wand  ·  X / Y: lock the axis  ·  N: let go  ·  "
                  "Delete: take the last corner back"),
    "info.slab_corner_back": ("Último canto apagado ({n} ficam).", "Last corner taken back ({n} left)."),
    "err.slab_outline_bad": ("Esse contorno não serve: os lados cruzam-se, tem menos de três cantos, ou é pequeno "
                             "demais.",
                             "That outline will not do: its sides cross, it has fewer than three corners, or it is "
                             "too small."),
    "info.slab_outline": ("Laje de {a} com {n} cantos criada ({type}). Ctrl+Z desfaz.",
                          "{a} slab with {n} corners created ({type}). Ctrl+Z undoes."),
    "info.slab_curved": ("Laje de {a} criada, o contorno com curvas como desenhado ({type}; Editar contorno muda-o). "
                         "Ctrl+Z desfaz.", "{a} slab created, its outline curved as drawn ({type}; Edit outline "
                         "changes it). Ctrl+Z undoes."),
    "info.slab_circle": ("Laje circular de raio {r} criada ({type}). Ctrl+Z desfaz.",
                         "Round slab of radius {r} created ({type}). Ctrl+Z undoes."),
    "err.slab_wand_open": ("Aqui não há paredes fechadas à volta", "There are no closed walls round here"),
    "info.slab_wand": ("Laje de {a} criada {reach} ({type}). Ctrl+Z desfaz.",
                       "{a} slab created {reach} ({type}). Ctrl+Z undoes."),
    "tool.slab_outline": ("Contorno", "Outline"),
    # (0.410) the wall profile's gestures and holes on a slab's, a floor's, a ceiling's outline
    "hint.slab_outline": ("Arraste o losango do meio de um lado: um canto novo — com Shift, um arco; com Alt, uma "
                          "curva. Arraste um quadrado: move o canto. Alt + clique num canto: concordância. «Furo» na "
                          "barra de cima: desenhar furos. Clique num ponto e Delete: tira-o. Esc: sair.",
                          "Drag a side's middle diamond: a new corner — with Shift, an arc; with Alt, a curve. Drag a "
                          "square: the corner moves. Alt + a click on a corner: a fillet. «Hole» on the bar above: "
                          "draw holes. Click a point and Delete: it goes. Esc: leave."),
    "hint.slab_outline_move": ("Com o botão carregado, leve o canto e largue onde fica (ou escreva a distância + "
                               "Enter). Botão direito: fica onde estava.",
                               "With the button held, take the corner and let go where it goes (or type the distance + "
                               "Enter). Right button: it stays where it was."),
    "hint.slab_outline_none": ("Este elemento não tem contorno que se edite aqui (uma laje circular muda pelo raio). "
                               "Esc: Selecionar.",
                               "This element has no outline to edit here (a round slab changes by its radius). "
                               "Esc: Select."),
    "keys.slab_outline": ("Arrastar losango: canto · +Shift: arco · +Alt: curva  ·  Alt + clique num canto: "
                          "concordância  ·  Furo: polígono, retângulo, círculo  ·  clique + Delete: tirar  ·  X / Y: "
                          "bloquear o eixo  ·  Esc: sair",
                          "Drag a diamond: corner · +Shift: arc · +Alt: curve  ·  Alt + click on a corner: fillet  ·  "
                          "Hole: polygon, rectangle, circle  ·  click + Delete: take away  ·  X / Y: lock the axis  ·  "
                          "Esc: leave"),
    "cmd.covering_outline": ("Contorno", "Outline"),
    "info.outline_changed": ("Contorno mudado.", "Outline changed."),
    "info.outline_area.slab": ("A laje tem agora {a}. Ctrl+Z desfaz.", "The slab is now {a}. Ctrl+Z undoes."),
    "info.outline_area.flooring": ("O piso tem agora {a}. Ctrl+Z desfaz.", "The floor finish is now {a}. Ctrl+Z "
                                   "undoes."),
    "info.outline_area.ceiling": ("O teto tem agora {a}. Ctrl+Z desfaz.", "The ceiling is now {a}. Ctrl+Z undoes."),
    "info.outline_pick_first": ("Clique primeiro num canto, na pega de uma curva ou dentro de um furo, depois Delete.",
                                "Click a corner, a curve's grip or inside a hole first, then Delete."),
    # (0.410) holes drawn in an outline (a slab's, a floor's, a ceiling's) or in a wall's profile
    "ctx.hole": ("Furo", "Hole"),
    "holeshape.poly": ("Polígono", "Polygon"),
    "holeshape.rect": ("Retângulo", "Rectangle"),
    "holeshape.circle": ("Círculo", "Circle"),
    "vcb.hole_size": ("Largura;Altura", "Width;Height"),
    "info.hole_mode.poly": ("Furo em polígono: clique nos cantos; clique no primeiro (ou Enter) fecha. Esc: largar o "
                            "furo.",
                            "Polygon hole: click its corners; a click on the first one (or Enter) closes it. Esc: "
                            "let the hole go."),
    "info.hole_mode.rect": ("Furo retangular: clique num canto e no oposto (ou arraste), ou escreva o tamanho "
                            "(ex.: 1,2;0,8) e Enter. Esc: largar o furo.",
                            "Rectangular hole: click a corner and the opposite one (or drag), or type its size (e.g. "
                            "1.2;0.8) and Enter. Esc: let the hole go."),
    "info.hole_mode.circle": ("Furo redondo: clique no centro e na borda (ou arraste), ou escreva o raio e Enter. "
                              "Esc: largar o furo.",
                              "Round hole: click its centre and its edge (or drag), or type the radius and Enter. "
                              "Esc: let the hole go."),
    "hint.hole.poly": ("Furo: clique no primeiro canto. Esc ou botão direito: largar o furo.",
                       "Hole: click its first corner. Esc or right button: let the hole go."),
    "hint.hole.poly_next": ("Clique no canto seguinte; no primeiro (ou Enter) fecha o furo. Delete: tira o último. "
                            "Esc: desiste deste.",
                            "Click the next corner; on the first one (or Enter) the hole closes. Delete: the last one "
                            "back. Esc: give this one up."),
    "hint.hole.rect": ("Furo: clique num canto do retângulo (ou arraste). Esc ou botão direito: largar o furo.",
                       "Hole: click a corner of the rectangle (or drag). Esc or right button: let the hole go."),
    "hint.hole.rect_next": ("Clique no canto oposto, ou escreva o tamanho (ex.: 1,2;0,8) e Enter. Esc: desiste deste.",
                            "Click the opposite corner, or type its size (e.g. 1.2;0.8) and Enter. Esc: give this "
                            "one up."),
    "hint.hole.circle": ("Furo: clique no centro (ou arraste até à borda). Esc ou botão direito: largar o furo.",
                         "Hole: click its centre (or drag to its edge). Esc or right button: let the hole go."),
    "hint.hole.circle_next": ("Clique na borda, ou escreva o raio e Enter. Esc: desiste deste.",
                              "Click its edge, or type the radius and Enter. Esc: give this one up."),
    "hint.hole_move": ("Com o botão carregado, leve o furo e largue onde fica. Botão direito: fica onde estava.",
                       "With the button held, take the hole and let go where it goes. Right button: it stays where it "
                       "was."),
    "tip.hole": ("Furo — arraste para o mover · clique + Delete: apagar",
                 "Hole — drag to move it · click + Delete: delete"),
    "tip.hole_drop": ("Furo a {d}  —  largue", "Hole {d} away  —  let go"),
    "tip.hole_close": ("Fechar o furo", "Close the hole"),
    "tip.hole_radius": ("Raio {r}", "Radius {r}"),
    "tip.hole_chosen": ("Furo escolhido: Delete apaga-o", "Hole chosen: Delete deletes it"),
    "err.hole_small": ("Esse furo é pequeno demais.", "That hole is too small."),
    "err.hole_outside": ("O furo tem de ficar dentro do contorno, sem tocar na borda nem noutro furo.",
                         "The hole must lie inside the outline, touching neither its edge nor another hole."),
    "info.hole_added": ("Furo de {a} feito.", "Hole of {a} made."),
    "info.hole_deleted": ("Furo apagado.", "Hole deleted."),
    "info.hole_moved": ("Furo mudado de sítio.", "Hole moved."),
    "tip.slab_corner": ("Arraste para mover · clique + Delete: tirar", "Drag to move · click + Delete: take away"),
    "tip.slab_add_corner": ("Arraste: um canto novo aqui", "Drag: a new corner here"),
    "tip.slab_corner_chosen": ("Escolhido: Delete tira este canto", "Chosen: Delete takes this corner away"),
    "info.slab_corner_moved": ("Canto mudado.", "Corner moved."),
    "info.slab_corner_deleted": ("Canto tirado.", "Corner taken away."),
    "info.slab_area": ("A laje tem agora {a}. Ctrl+Z desfaz.", "The slab is now {a}. Ctrl+Z undoes."),
    "info.slab_corner_pick_first": ("Clique primeiro num canto e depois Delete para o tirar.",
                                    "Click a corner first, then Delete to take it away."),
    "err.slab_three_corners": ("Uma laje precisa de pelo menos três cantos.", "A slab needs three corners at least."),
    "act.edit_outline": ("Editar contorno", "Edit outline"),
    "tip.edit_outline": ("Mudar o contorno da laje, do piso ou do teto: cantos, arcos (Shift), curvas (Alt), "
                         "concordâncias e furos (também com dois cliques no elemento)",
                         "Change the outline of the slab, floor finish or ceiling: corners, arcs (Shift), curves (Alt), "
                         "fillets and holes (also with two clicks on the element)"),
    "info.edit_outline_none": ("Selecione uma laje, um piso ou um teto (um só) para editar o contorno.",
                               "Select one slab, floor finish or ceiling to edit its outline."),
    "info.edit_outline_circle": ("Uma laje circular muda pelo raio, no painel Propriedades.",
                                 "A round slab changes by its radius, in the Properties panel."),
    "info.edit_outline": ("Contorno de «{name}»: arraste o losango do meio de um lado para fazer um canto — com Shift "
                          "um arco, com Alt uma curva. Alt + clique num canto: concordância. «Furo» na barra de cima: "
                          "desenhar furos. Esc: sair.",
                          "Outline of “{name}”: drag a side's middle diamond for a corner — with Shift an arc, with "
                          "Alt a curve. Alt + click on a corner: a fillet. «Hole» on the bar above: draw holes. "
                          "Esc: leave."),
    "props.radius": ("Raio", "Radius"),
    "props.slab_function": ("Função", "Function"),
    "props.slab_use": ("Uso (sobrecarga)", "Use (imposed load)"),                       # (0.218)
    "props.slab_use_project": ("O do projeto (Ações e materiais)", "The project's (Actions and materials)"),
    "cmd.slab_use": ("Uso da laje", "Slab use"),
    "props.outline": ("Contorno", "Outline"),
    # (0.433) a slab with a height of its own at each corner (the addon's «piso com declive por vértice»)
    "props.g.slope": ("Declive", "Slope"),
    "props.slope_side": ("Lado alto", "High side"),
    "props.slope_side_tip": ("O lado que fica no topo da laje; o declive cai a partir dele",
                             "The side that stays at the slab's top; the slope falls from it"),
    "props.slope_side_n": ("Lado {n} (cantos {a}–{b})", "Side {n} (corners {a}–{b})"),
    "props.slope_percent": ("Declive (%)", "Slope (%)"),
    "props.slope_percent_tip": ("Escreva o declive em % (1 % = 1 cm por metro) e carregue em Enter: a laje cai a partir "
                                "do lado alto. Cada canto fica com a sua altura, que pode mudar em baixo.",
                                "Type the slope in % (1 % = 1 cm a metre) and press Enter: the slab falls from the "
                                "high side. Each corner gets its height, which can be changed below."),
    "props.corner_height": ("Canto {n}", "Corner {n}"),
    "props.corner_height_tip": ("A altura deste canto acima (ou abaixo, com −) do topo da laje. ↑ ↓: 1 cm.",
                                "This corner's height over (or under, with −) the slab's top. ↑ ↓: 1 cm."),
    "props.corners_many": ("{n} cantos: use o Declive (%)", "{n} corners: use the Slope (%)"),
    "props.slab_flat": ("Pôr plana", "Make flat"),
    "info.slab_slope": ("Laje com {p} % de declive a partir do lado {s}. Ctrl+Z desfaz.",
                        "Slab sloping {p} % from side {s}. Ctrl+Z undoes."),
    "cmd.slab_outline": ("Contorno da laje", "Slab outline"),
    "cmd.slab_heights": ("Declive da laje", "Slab slope"),                                       # (0.433)
    # (0.437) a wall's light frame (the addon's «Steel Frame / Wood Frame»)
    "cmd.wall_framing": ("Estrutura leve", "Light frame"),
    "props.g.framing": ("Estrutura leve", "Light frame"),
    "props.framing": ("Estrutura", "Frame"),
    "framing.none": ("Nenhuma", "None"),
    "framing.steel": ("Steel frame (aço leve)", "Steel frame"),
    "framing.wood": ("Wood frame (madeira)", "Wood frame"),
    "props.framing_spacing": ("Espaçamento dos montantes", "Stud spacing"),
    "props.framing_blocking": ("Travamentos (filas)", "Blocking (rows)"),
    "framing.no_blocking": ("Sem travamentos", "No blocking"),
    "framing.role.plate": ("Guias", "Plates"),
    "framing.role.stud": ("Montantes", "Studs"),
    "framing.role.jamb": ("Ombreiras", "Jamb studs"),
    "framing.role.cripple": ("Montantes curtos", "Cripple studs"),
    "framing.role.header": ("Vergas", "Headers"),
    "framing.role.sill": ("Peitoris", "Sills"),
    "framing.role.blocking": ("Travamentos", "Blocking"),
    "framing.count": ("{n} — {m}", "{n} — {m}"),
    "info.wall_framing": ("Estrutura leve: {n} peças, {m} ao todo. Para a ver, esconda as paredes (Visibilidade). "
                          "Ctrl+Z desfaz.",
                          "Light frame: {n} pieces, {m} in all. To see it, hide the walls (Visibility). Ctrl+Z undoes."),
    "refuse.framing_bad": ("o espaçamento dos montantes tem de estar entre 10 cm e 1,50 m",
                           "the studs' spacing must be between 10 cm and 1.50 m"),
    "refuse.framing_small": ("a parede é pequena demais para uma estrutura", "the wall is too small for a frame"),
    "cmd.slab_function": ("Função da laje", "Slab function"),
    "refuse.slab_outline": ("o contorno não serve (lados cruzados ou pequeno demais)",
                            "the outline will not do (its sides cross, or it is too small)"),
    "refuse.slab_height": ("um canto ficaria a mais de 20 m do topo da laje",                    # (0.433)
                           "a corner would be more than 20 m off the slab's top"),
    "refuse.slab_outline_edit": ("esta laje muda pelo contorno (Editar contorno) ou pelo raio",
                                 "this slab changes by its outline (Edit outline) or its radius"),
    "refuse.slab_circle": ("uma laje circular muda pelo raio", "a round slab changes by its radius"),
    # walls by a rectangle, along a face (0.102)
    "ctx.wall_shape": ("Forma", "Shape"),
    "wallshape.line": ("Linha (ponto a ponto)", "Line (point by point)"),
    "wallshape.rect": ("Retângulo", "Rectangle"),
    "wallshape.face": ("A partir de uma face", "From a face"),
    "refloop.axis": ("pelo eixo", "by the axis"),
    "refloop.left": ("pela face interior", "by the inner face"),
    "refloop.right": ("pela face exterior", "by the outer face"),
    "cmd.walls": ("Paredes", "Walls"),
    "hint.wall.rect_start": ("{type}, desenhada {ref}: clique no primeiro canto do retângulo.",
                             "{type}, drawn {ref}: click the rectangle's first corner."),
    "hint.wall.rect_end": ("Clique no canto oposto ou digite as medidas (ex.: 6;4) e Enter: quatro paredes ligadas nos "
                           "cantos, desenhadas {ref} (Tab muda). Esc cancela.",
                           "Click the opposite corner or type the size (e.g. 6;4) and Enter: four walls joined at the "
                           "corners, drawn {ref} (Tab changes it). Esc cancels."),
    "hint.wall.face": ("{type}: clique numa laje ou numa face horizontal de um esboço — paredes ao longo do seu "
                       "contorno, desenhadas {ref} (Tab muda).",
                       "{type}: click a slab or a level face of a sketch — walls along its outline, drawn {ref} "
                       "(Tab changes it)."),
    "tip.wall_loop": ("{n} paredes", "{n} walls"),
    "tip.wall_face_none": ("Aqui não há uma laje nem uma face horizontal", "No slab nor level face here"),
    "err.wall_face_none": ("Clique numa laje (não circular) ou numa face horizontal de um esboço.",
                           "Click a slab (not a round one) or a level face of a sketch."),
    "wallshape.wand": ("Varinha mágica (num desenho)", "Magic wand (on a drawing)"),
    # (0.451) Revit's «Pick Lines» and «Offset»
    "wallshape.pick": ("Escolher linhas (sobre uma linha ou aresta)", "Pick lines (on a line or an edge)"),
    "hint.wall.pick": ("Escolher linhas — {type}, {ref}: clique numa linha, aresta, face de parede, eixo da grelha ou "
                       "linha de um desenho; a parede fica sobre ela, do lado do rato, com o Afastamento da barra.",
                       "Pick lines — {type}, {ref}: click a line, an edge, a wall's face, a grid axis or a drawing's "
                       "line; the wall lies on it, on the mouse's side, at the bar's Offset."),
    "tip.wall_pick": ("Parede de {l} aqui (clique)", "A {l} wall here (click)"),
    "tip.wall_pick_none": ("Aponte para uma linha ou aresta", "Point at a line or an edge"),
    "info.wall_picked": ("Parede de {l} sobre a linha escolhida ({type}). Clique noutra, ou Esc. Ctrl+Z desfaz.",
                         "A {l} wall on the line picked ({type}). Click another one, or Esc. Ctrl+Z undoes."),
    # (0.459) an arc drawn in pieces picked whole
    "tip.wall_pick_arc": ("Parede curva de raio {r} ({l}) aqui (clique)", "A curved wall of radius {r} ({l}) here "
                          "(click)"),
    "info.wall_picked_arc": ("Parede curva de raio {r} ({l}) sobre o arco escolhido, inteiro ({type}). Clique noutro, "
                             "ou Esc. Ctrl+Z desfaz.", "A curved wall of radius {r} ({l}) on the whole arc picked "
                             "({type}). Click another one, or Esc. Ctrl+Z undoes."),
    "info.arc_on_picked": ("Arco de raio {r} sobre o escolhido, inteiro. Clique noutro, ou Esc. Ctrl+Z desfaz.",
                           "An arc of radius {r} on the whole one picked. Click another one, or Esc. Ctrl+Z undoes."),
    "info.side_picked": ("Lado do polígono escolhido ({l}). Clique na cota e escreva outro comprimento, ou arraste as "
                         "pegas; Esc larga-o.", "The polygon's side picked ({l}). Click its dimension and type another "
                         "length, or drag its grips; Esc lets it go."),
    "info.side_arc_picked": ("Arco do polígono escolhido, inteiro (raio {r}). Clique na cota e escreva outro raio; "
                             "Esc larga-o.", "The polygon's arc picked whole (radius {r}). Click its dimension and type "
                             "another radius; Esc lets it go."),
    "hint.side_chosen": ("Lado do polígono escolhido: clique no valor da cota e escreva outro (um arco: o raio); "
                         "arraste as pegas para o mover. Esc larga-o.",
                         "A polygon's side picked: click the dimension's value and type another (an arc: its radius); "
                         "drag its grips to move it. Esc lets it go."),
    "ctx.offset": ("Afastamento", "Offset"),
    # (0.452) Revit's «Fillet Arc»
    "cmd.fillet": ("Arco de concordância", "Fillet arc"),
    "cmd.fillet_radius": ("Raio da concordância", "Fillet radius"),
    "wallshape.fillet": ("Arco de concordância (entre 2 paredes)", "Fillet arc (between 2 walls)"),
    "hint.wall.fillet_0": ("Arco de concordância — {type}: clique na 1.ª parede (do lado que fica).",
                           "Fillet arc — {type}: click the 1st wall (on the side that stays)."),
    "hint.wall.fillet_1": ("Arco de concordância: clique na 2.ª parede (do lado que fica).",
                           "Fillet arc: click the 2nd wall (on the side that stays)."),
    "hint.wall.fillet_2": ("Arco de concordância: mova o rato para o raio e clique, ou escreva o raio e Enter. Esc "
                           "recomeça.", "Fillet arc: move the mouse for the radius and click, or type the radius and "
                           "Enter. Esc starts again."),
    "tip.fillet_pick": ("Escolha a {n}.ª parede", "Pick wall {n}"),
    "tip.fillet_line": ("Escolha a {n}.ª linha (ou lado de um polígono)", "Pick line {n} (or a polygon's side)"),
    # (0.453) Revit's «Chain» and «Radius» on the options bar
    "ctx.chain": ("Cadeia", "Chain"),
    "ctx.corner_radius": ("Raio dos cantos", "Corner radius"),
    "info.corner_not_rounded": ("(o canto não foi arredondado: o raio de {r} é grande demais para estes troços)",
                                "(the corner was not rounded: the {r} radius is too big for these pieces)"),
    "draw.fillet": ("Arco de concordância (entre 2 linhas)", "Fillet arc (between 2 lines)"),
    "hint.line.fillet_0": ("Arco de concordância: clique na 1.ª linha (do lado que fica) — ou num lado de um polígono.",
                           "Fillet arc: click the 1st line (on the side that stays) — or a polygon's side."),
    "hint.line.fillet_1": ("Arco de concordância: clique na 2.ª linha (do lado que fica) — num polígono, o lado que "
                           "faz o canto com o primeiro.",
                           "Fillet arc: click the 2nd line (on the side that stays) — on a polygon, the side making "
                           "the corner with the first."),
    "hint.line.fillet_2": ("Arco de concordância: mova o rato para o raio e clique, ou escreva o raio e Enter. Esc "
                           "recomeça.", "Fillet arc: move the mouse for the radius and click, or type the radius and "
                           "Enter. Esc starts again."),
    "info.fillet_lines": ("Arco de concordância de raio {r}; as duas linhas foram aparadas até ele. Para mudar o raio: "
                          "Selecionar, clique no arco e no valor do raio. Ctrl+Z desfaz.",
                          "A fillet arc of radius {r}; the two lines were trimmed to it. To change its radius: Select, "
                          "click the arc, then the radius' value. Ctrl+Z undoes."),
    "info.fillet_polygon": ("Canto do polígono arredondado com raio {r}. Ctrl+Z desfaz.",
                            "The polygon's corner rounded with radius {r}. Ctrl+Z undoes."),
    "tip.fillet_radius": ("Raio {r}", "Radius {r}"),
    "err.fillet_none": ("Não há arco aqui: as paredes são paralelas, ou o raio é grande demais.",
                        "No arc here: the walls are parallel, or the radius is too big."),
    "info.fillet": ("Arco de concordância de raio {r} entre as duas paredes ({type}); elas foram aparadas até ele. "
                    "Ctrl+Z desfaz.", "A fillet arc of radius {r} between the two walls ({type}); they were trimmed "
                    "to it. Ctrl+Z undoes."),
    "refuse.too_big": ("o raio é grande demais para estes troços", "the radius is too big for these pieces"),
    "refuse.not_corner": ("escolha dois lados que fazem um canto do mesmo polígono (ou duas linhas)",
                          "pick two sides making a corner of the same polygon (or two lines)"),
    "refuse.not_level": ("o polígono não está deitado (a concordância desenha-se na planta)",
                         "the polygon does not lie level (the fillet is drawn in plan)"),
    "hint.wall.wand": ("Varinha mágica: arraste uma janela sobre as duas linhas de uma parede de um desenho (DWG/DXF "
                       "ligado ou linhas de esboço): a parede fica entre elas, com a espessura medida.",
                       "Magic wand: drag a window over a wall's two lines in a drawing (a linked DWG/DXF or sketch "
                       "lines): the wall goes between them, its thickness measured."),
    "err.wall_wand_none": ("Na janela não há duas linhas paralelas a 5–60 cm uma da outra (as faces de uma parede). "
                           "Ligue o desenho (Inserir ▸ Vincular ▸ Ligar um desenho DXF/DWG…) ou arraste por cima das "
                           "duas linhas.",
                           "In the window there are no two parallel lines 5–60 cm apart (a wall's faces). Link the "
                           "drawing (Home ▸ Link DWG/DXF) or drag over both lines."),
    "info.wall_wand": ("{n} parede(s) entre as linhas do desenho ({t}). Ctrl+Z desfaz.",
                       "{n} wall(s) between the drawing's lines ({t}). Ctrl+Z undoes."),
    "info.wall_rect": ("{n} paredes à volta de {a} × {b}, desenhadas {ref}, ligadas nos cantos ({type}). Ctrl+Z "
                       "desfaz.",
                       "{n} walls round {a} × {b}, drawn {ref}, joined at the corners ({type}). Ctrl+Z undoes."),
    "info.wall_face": ("{n} paredes ao longo do contorno, desenhadas {ref}, ligadas nos cantos ({type}). Ctrl+Z "
                       "desfaz.",
                       "{n} walls along the outline, drawn {ref}, joined at the corners ({type}). Ctrl+Z undoes."),
    # (0.307) the Caixilho Studio (the owner's prototype)
    "act.caixilho": ("Caixilho Studio", "Caixilho Studio"),
    "tip.caixilho": ("O editor de portas e janelas: desenhar o vão, montantes, travessas, aberturas e materiais, e "
                     "inserir no modelo",
                     "The door and window editor: draw the opening, its mullions, transoms, ways of opening and "
                     "fills, and insert it in the model"),
    "rib.short.caixilho": ("Caixilho\nStudio", "Caixilho\nStudio"),
    "caixilho.scale": ("escala de ecrã ≈ 1:{n} · grade 10 mm", "screen scale ≈ 1:{n} · 10 mm grid"),
    "caixilho.new": ("Novo vão", "New opening"),
    "caixilho.start_from": ("COMEÇAR DE", "START FROM"),
    "caixilho.duplicate": ("Duplicar", "Duplicate"),
    "caixilho.preset_two_leaves": ("Janela de 2 folhas", "Two-leaf window"),
    "caixilho.preset_fanlight": ("Janela com bandeira", "Window with a fanlight"),
    "caixilho.preset_door": ("Porta simples", "Single door"),
    "caixilho.preset_door_side": ("Porta com bandeira e lateral", "Door with fanlight and sidelight"),
    "caixilho.preset_sliding": ("Porta-janela de correr", "Sliding patio door"),
    "caixilho.preset_bare": ("Vão livre", "Plain opening"),
    "caixilho.view_exterior": ("Vista exterior", "Outside view"),
    "caixilho.view_interior": ("Vista interior", "Inside view"),
    "caixilho.linked": ("Travessas ligadas", "Linked transoms"),
    "caixilho.eq_cols": ("Larguras iguais", "Equal widths"),
    "caixilho.eq_rows": ("Alturas iguais", "Equal heights"),
    "caixilho.eq_all": ("Igualar tudo", "All equal"),
    "caixilho.eq_cols_tip": ("Parâmetro do tipo: todas as colunas com a mesma largura, sempre — ao pôr ou tirar "
                             "montantes e ao mudar a largura do vão (também na tabela do tipo). Mover um montante à "
                             "mão desliga-o.",
                             "A type parameter: every column as wide, always — when mullions are put in or taken out "
                             "and when the opening's width changes (in the type's table too). Moving a mullion by hand "
                             "turns it off."),
    "caixilho.eq_rows_tip": ("Parâmetro do tipo: em cada coluna, todos os painéis com a mesma altura, sempre — ao pôr "
                             "ou tirar travessas e ao mudar a altura do vão (também na tabela do tipo). Mover uma "
                             "travessa à mão desliga-o.",
                             "A type parameter: in each column, every panel as high, always — when transoms are put in "
                             "or taken out and when the opening's height changes (in the type's table too). Moving a "
                             "transom by hand turns it off."),
    "caixilho.eq_all_tip": ("Todas as divisões iguais: liga «Larguras iguais» e «Alturas iguais».",
                            "Every division equal: turns «Equal widths» and «Equal heights» on."),
    "caixilho.eq_cols_on": ("Larguras iguais: ligado", "Equal widths: on"),
    "caixilho.eq_cols_off": ("Larguras iguais: desligado", "Equal widths: off"),
    "caixilho.eq_rows_on": ("Alturas iguais: ligado", "Equal heights: on"),
    "caixilho.eq_rows_off": ("Alturas iguais: desligado", "Equal heights: off"),
    "caixilho.new_mullion": ("↓ arraste para criar montante", "↓ drag in a mullion"),
    "caixilho.new_transom": ("→ travessa", "→ transom"),
    "caixilho.ghost_col": ("+ montante · {a} | {b}", "+ mullion · {a} | {b}"),
    "caixilho.ghost_row": ("+ travessa · {h} da base", "+ transom · {h} from the foot"),
    "caixilho.ghost_one": (" (só esta coluna)", " (this column only)"),
    "caixilho.column": ("Coluna {n}", "Column {n}"),
    "caixilho.hint": ("Clique num painel para escolher abertura e material · as cotas são editáveis e aceitam contas "
                      "(2400/3) · setas movem montantes e travessas 10 mm (Shift 100)",
                      "Click a panel to choose how it opens and its fill · the sizes can be typed, sums too (2400/3) · "
                      "the arrows move mullions and transoms 10 mm (Shift 100)"),
    "caixilho.aria_col": ("Largura da coluna {n}", "Width of column {n}"),
    "caixilho.aria_W": ("Largura total do vão", "Whole width of the opening"),
    "caixilho.aria_H": ("Altura total do vão", "Whole height of the opening"),
    "caixilho.aria_row": ("Altura da linha {r} da coluna {c}", "Height of row {r} of column {c}"),
    "caixilho.remove_mullion": ("Remover montante", "Remove the mullion"),
    "caixilho.remove_transom": ("Remover travessa", "Remove the transom"),
    "caixilho.split_v": ("Dividir │", "Split │"),
    "caixilho.split_h": ("Dividir ─", "Split ─"),
    "caixilho.copy_row": ("Copiar p/ linha", "Copy along row"),
    "caixilho.kind": ("Tipo", "Kind"),
    "caixilho.kind_window": ("Janela", "Window"),
    "caixilho.kind_door": ("Porta", "Door"),
    "caixilho.reference": ("Referência", "Reference"),
    "caixilho.system": ("Sistema", "System"),
    "caixilho.system.aluminio": ("Alumínio", "Aluminium"),
    "caixilho.system.pvc": ("PVC", "PVC"),
    "caixilho.system.madeira": ("Madeira", "Wood"),
    "caixilho.system.aco": ("Aço", "Steel"),
    "caixilho.colour": ("Cor do perfil", "Profile colour"),
    "caixilho.colour.grafite": ("Grafite", "Graphite"),
    "caixilho.colour.branco": ("Branco", "White"),
    "caixilho.colour.bronze": ("Bronze", "Bronze"),
    "caixilho.colour.natural": ("Madeira natural", "Natural wood"),
    "caixilho.aro": ("Aro (mm)", "Frame (mm)"),
    "caixilho.sill": ("Peitoril (mm)", "Sill (mm)"),
    "caixilho.more": ("Mais opções…", "More options…"),
    "caixilho.plan": ("Planta…", "Plan…"),                                                          # (0.359)
    "caixilho.plan_tip": ("Como a porta se desenha em planta: aberta ou fechada, a linha de abertura, as guarnições e a "
                          "soleira, com a planta desenhada ao lado.",
                          "How the door is drawn in plan: open or closed, the swing's line, the casings and the "
                          "threshold, with its plan drawn beside."),
    "caixilho.plan_shown": ("Em planta", "In plan"),
    "caixilho.plan_open": ("Aberta, com a linha de abertura", "Open, with its swing"),
    "caixilho.plan_closed": ("Fechada, com a linha de abertura", "Closed, with its swing's line"),
    "caixilho.swing": ("Linha de abertura", "Swing's line"),
    "caixilho.swing_solid": ("Contínua", "Solid"),
    "caixilho.swing_dashed": ("Tracejada", "Dashed"),
    "caixilho.plan_frame": ("Aro (largura, no desenho)", "Frame (width, in the drawing)"),
    "caixilho.casing_depth": ("Espessura das guarnições", "Casings' thickness"),
    "caixilho.metric_size": ("Vão", "Opening"),
    "caixilho.metric_glass": ("Envidraçado", "Glazed"),
    "caixilho.metric_open": ("Área de abertura", "Opening area"),
    "caixilho.metric_ifc": ("IFC", "IFC"),
    "caixilho.cancel": ("Cancelar", "Cancel"),
    "caixilho.save": ("Guardar", "Save"),
    "caixilho.insert": ("Inserir no modelo", "Insert in the model"),
    "caixilho.fill.glass": ("Vidro", "Glass"),
    "caixilho.fill.frosted": ("Vidro fosco", "Frosted glass"),
    "caixilho.fill.panel": ("Painel opaco", "Solid panel"),
    "caixilho.fill.wood": ("Madeira", "Wood"),
    "caixilho.fill.louvre": ("Veneziana", "Louvres"),
    "caixilho.win.fixed": ("Fixo", "Fixed"), "caixilho.win.fixed.s": ("Fixo", "Fixed"),
    "caixilho.win.left": ("Batente esquerdo", "Side-hung left"), "caixilho.win.left.s": ("Bat. E", "Side L"),
    "caixilho.win.right": ("Batente direito", "Side-hung right"), "caixilho.win.right.s": ("Bat. D", "Side R"),
    "caixilho.win.bottom": ("Basculante", "Bottom-hung"), "caixilho.win.bottom.s": ("Bascul.", "Bottom"),
    "caixilho.win.top": ("Projetante", "Top-hung"), "caixilho.win.top.s": ("Projet.", "Top"),
    "caixilho.win.tilt_left": ("Oscilobatente", "Tilt and turn"), "caixilho.win.tilt_left.s": ("Oscilo", "Tilt"),
    "caixilho.win.slide_right": ("Correr", "Sliding"), "caixilho.win.slide_right.s": ("Correr", "Slide"),
    "caixilho.win.pivot_v": ("Pivotante", "Pivot"), "caixilho.win.pivot_v.s": ("Pivot.", "Pivot"),
    "caixilho.win.tilt_right": ("Oscilobatente direito", "Tilt and turn right"),
    "caixilho.win.tilt_right.s": ("Oscilo D", "Tilt R"),
    "caixilho.win.slide_left": ("Correr para a esquerda", "Sliding to the left"),
    "caixilho.win.slide_left.s": ("Correr ←", "Slide ←"),
    "caixilho.win.slide_up": ("Guilhotina", "Sash"), "caixilho.win.slide_up.s": ("Guilhot.", "Sash"),
    "caixilho.win.pivot_h": ("Pivotante horizontal", "Horizontal pivot"),
    "caixilho.win.pivot_h.s": ("Pivot. H", "Pivot H"),
    "caixilho.door.fixed": ("Fixo", "Fixed"), "caixilho.door.fixed.s": ("Fixo", "Fixed"),
    "caixilho.door.left": ("Folha esquerda", "Left leaf"), "caixilho.door.left.s": ("Folha E", "Leaf L"),
    "caixilho.door.right": ("Folha direita", "Right leaf"), "caixilho.door.right.s": ("Folha D", "Leaf R"),
    "caixilho.door.slide_right": ("Correr", "Sliding"), "caixilho.door.slide_right.s": ("Correr", "Slide"),
    "caixilho.door.slide_left": ("Correr para a esquerda", "Sliding to the left"),
    "caixilho.door.slide_left.s": ("Correr ←", "Slide ←"),
    "caixilho.door.swing_left": ("Vaivém esquerdo", "Double-acting left"),
    "caixilho.door.swing_left.s": ("Vaivém E", "Swing L"),
    "caixilho.door.swing_right": ("Vaivém direito", "Double-acting right"),
    "caixilho.door.swing_right.s": ("Vaivém D", "Swing R"),
    "caixilho.door.fold_left": ("Harmónio esquerdo", "Folding left"),
    "caixilho.door.fold_left.s": ("Harmón. E", "Fold L"),
    "caixilho.door.fold_right": ("Harmónio direito", "Folding right"),
    "caixilho.door.fold_right.s": ("Harmón. D", "Fold R"),
    "caixilho.door.bottom": ("Basculante", "Bottom-hung"), "caixilho.door.bottom.s": ("Bascul.", "Bottom"),
    "caixilho.door.top": ("Projetante", "Top-hung"), "caixilho.door.top.s": ("Projet.", "Top"),
    "caixilho.door.tilt_left": ("Oscilobatente", "Tilt and turn"), "caixilho.door.tilt_left.s": ("Oscilo", "Tilt"),
    "caixilho.door.tilt_right": ("Oscilobatente direito", "Tilt and turn right"),
    "caixilho.door.tilt_right.s": ("Oscilo D", "Tilt R"),
    "caixilho.door.pivot_v": ("Pivotante", "Pivot"), "caixilho.door.pivot_v.s": ("Pivot.", "Pivot"),
    "caixilho.door.pivot_h": ("Pivotante horizontal", "Horizontal pivot"),
    "caixilho.door.pivot_h.s": ("Pivot. H", "Pivot H"),
    "caixilho.door.slide_up": ("Guilhotina", "Sash"), "caixilho.door.slide_up.s": ("Guilhot.", "Sash"),
    "info.caixilho_inserted": ("{name} pronto · clique numa parede para o colocar.",
                               "{name} ready · click a wall to place it."),
    "info.caixilho_saved": ("{n} tipo(s) de porta / janela guardados.", "{n} door / window type(s) saved."),
    # (0.304) wall sweep, as Revit's
    "tool.wall_sweep": ("Rodapé / sanca na parede", "Wall sweep"),
    "cmd.wall_sweep": ("Perfil na parede", "Wall sweep"),
    "rib.small.wall_sweep": ("Rodapé na parede", "Wall sweep"),
    "hint.wall_sweep": ("{p}: clique na face de uma parede — corre ao longo dela e das paredes ligadas desse lado, "
                        "com os cantos em meia-esquadria, e pára nas portas. Esc: Selecionar.",
                        "{p}: click a wall's face — it runs along it and along the walls joined to it on that side, "
                        "its corners mitred, and stops at the doors. Esc: Select."),
    "keys.wall_sweep": ("Clique: na face da parede, do lado onde fica o perfil  ·  Esc: Selecionar",
                        "Click: on the wall's face, on the side the profile goes  ·  Esc: Select"),
    "err.wall_sweep": ("Clique na face de uma parede reta (não numa ponta).",
                       "Click the face of a straight wall (not an end)."),
    # (0.305) wall reveal, as Revit's
    "tool.wall_reveal": ("Ranhura", "Wall reveal"),
    "cmd.wall_reveal": ("Ranhura", "Wall reveal"),
    "cmd.remove_reveal": ("Tirar ranhura", "Remove reveal"),
    "elem.reveal": ("Ranhura", "Reveal"),
    "ctx.reveal_direction": ("Direção", "Direction"),
    "revealdir.h": ("Horizontal", "Level"),
    "revealdir.v": ("Vertical", "Vertical"),
    "ctx.reveal_width": ("Largura", "Width"),
    "ctx.reveal_depth": ("Profundidade", "Depth"),
    "ctx.reveal_remove": ("Tirar ranhuras", "Remove reveals"),
    "hint.wall_reveal.h": ("Clique na face de uma parede, à altura da ranhura: corre ao longo da parede toda (Tab: "
                           "vertical). Esc: Selecionar.",
                           "Click a wall's face at the reveal's height: it runs along the whole wall (Tab: "
                           "vertical). Esc: Select."),
    "hint.wall_reveal.v": ("Clique na face de uma parede, onde fica a ranhura: sobe a parede toda (Tab: horizontal). "
                           "Esc: Selecionar.",
                           "Click a wall's face where the reveal goes: it runs up the whole wall (Tab: level). Esc: "
                           "Select."),
    "hint.wall_reveal.remove": ("Clique numa ranhura para a tirar (desligue «Tirar ranhuras» para fazer outras). Esc: "
                                "Selecionar.",
                                "Click a reveal to take it away (switch «Remove reveals» off to make others). Esc: "
                                "Select."),
    "keys.wall_reveal": ("Clique: a ranhura ali  ·  Tab: horizontal / vertical  ·  Esc: Selecionar",
                         "Click: the reveal there  ·  Tab: level / vertical  ·  Esc: Select"),
    "info.wall_reveal.h": ("Ranhura de {w} × {d} ao longo de «{wall}», a {at} da base. Ctrl+Z desfaz.",
                           "{w} × {d} reveal along “{wall}”, {at} over its base. Ctrl+Z undoes."),
    "info.wall_reveal.v": ("Ranhura vertical de {w} × {d} em «{wall}», a {at} do início. Ctrl+Z desfaz.",
                           "{w} × {d} vertical reveal in “{wall}”, {at} from its start. Ctrl+Z undoes."),
    "info.wall_reveal_removed": ("Ranhura tirada de «{wall}». Ctrl+Z desfaz.",
                                 "Reveal taken away from “{wall}”. Ctrl+Z undoes."),
    "err.no_reveal": ("Aqui não há ranhura dessa direção.", "No reveal of that direction here."),
    "refuse.reveal_size": ("a ranhura tem de ter de 0,5 a 50 cm de largura e no máximo meia parede de profundidade",
                           "a reveal must be 0.5 to 50 cm wide and at most half the wall deep"),
    # (0.303) wall opening, as Revit's
    "tool.wall_opening": ("Abertura na parede", "Wall opening"),
    "cmd.wall_opening": ("Abertura na parede", "Wall opening"),
    "elem.wall_opening": ("Abertura", "Opening"),
    # the Niche (0.374)
    "tool.niche": ("Nicho", "Niche"),
    "cmd.niche": ("Nicho", "Niche"),
    "ctx.niche_depth": ("Profundidade", "Depth"),
    "hint.niche": ("Nicho de {d}: clique na face de uma parede reta, num canto do nicho (a profundidade na barra). "
                   "Esc: Selecionar.",
                   "{d} niche: click a straight wall's face, at a corner of the niche (its depth on the bar). Esc: "
                   "Select."),
    "hint.niche_2": ("Clique no canto oposto, ou digite a largura e a altura (ex.: 0,60;0,40) e Enter. Esc desiste.",
                     "Click the opposite corner, or type its width and height (e.g. 0.60;0.40) and Enter. Esc gives "
                     "up."),
    "info.niche_made": ("Nicho de {w} × {h}, {d} de fundo, em {wall} (IFC; acompanha a parede).",
                        "{w} × {h} niche, {d} deep, in {wall} (IFC; it goes with the wall)."),
    "refuse.niche_deep": ("o nicho seria tão fundo como a parede (para atravessar: Abertura na parede)",
                          "the niche would be as deep as the wall (to go through: Wall opening)"),
    "hint.wall_opening": ("Clique na face de uma parede reta, num canto da abertura. Esc: Selecionar.",
                          "Click a straight wall's face, at a corner of the opening. Esc: Select."),
    "hint.wall_opening_2": ("Clique no canto oposto, ou digite a largura e a altura (ex.: 1,20;2,10) e Enter. Esc: "
                            "cancelar.",
                            "Click the opposite corner, or type the width and height (e.g. 1,20;2,10) and Enter. Esc: "
                            "cancel."),
    "keys.wall_opening": ("Clique: um canto, depois o oposto  ·  largura;altura + Enter  ·  Esc: cancelar / Selecionar",
                          "Click: a corner, then the opposite one  ·  width;height + Enter  ·  Esc: cancel / Select"),
    "vcb.opening_size": ("Largura;altura", "Width;height"),
    "info.wall_opening": ("Abertura de {w} × {h}, a {z} da base, em «{wall}» (sem porta nem janela; vai com a "
                          "parede). Ctrl+Z desfaz.",
                          "{w} × {h} opening, {z} over the base, in “{wall}” (no door or window; it goes with the "
                          "wall). Ctrl+Z undoes."),
    # (0.301) wall joins, as Revit's
    "tool.wall_joins": ("Junções de paredes", "Wall joins"),
    "cmd.wall_joins": ("Junção de paredes", "Wall join"),
    "ctx.join_style": ("Junção", "Join"),
    "joinstyle.butt": ("Topo a topo (a parede clicada passa)", "Butt (the wall clicked runs through)"),
    "joinstyle.mitre": ("Meia-esquadria", "Mitre"),
    "hint.wall_joins.butt": ("Clique numa parede junto a um canto: passa a ser ela a passar e a outra pára na sua "
                             "face (Tab: meia-esquadria). Esc: Selecionar.",
                             "Click a wall near a corner: it runs through and the other stops at its face (Tab: "
                             "mitre). Esc: Select."),
    "hint.wall_joins.mitre": ("Clique numa parede junto a um canto: o canto fica em meia-esquadria (Tab: topo a topo). "
                              "Esc: Selecionar.",
                              "Click a wall near a corner: the corner is mitred (Tab: butt). Esc: Select."),
    "keys.wall_joins": ("Clique: junto ao canto, na parede  ·  Tab: topo a topo / meia-esquadria  ·  Esc: Selecionar",
                        "Click: near the corner, on the wall  ·  Tab: butt / mitre  ·  Esc: Select"),
    "info.wall_joins.butt": ("«{name}» passa no canto; «{other}» pára na sua face. Ctrl+Z desfaz.",
                             "“{name}” runs through the corner; “{other}” stops at its face. Ctrl+Z undoes."),
    "info.wall_joins.mitre": ("O canto de «{name}» e «{other}» ficou em meia-esquadria. Ctrl+Z desfaz.",
                              "The corner of “{name}” and “{other}” is mitred. Ctrl+Z undoes."),
    "err.no_corner": ("Aqui não há um canto: clique numa parede, perto da ponta que está ligada a outra.",
                      "No corner here: click a wall near its end that is joined to another."),
    "refuse.no_corner": ("essa ponta não faz canto com outra parede reta", "that end makes no corner with another "
                                                                          "straight wall"),
    "refuse.corner_angle": ("o canto não é reto: nos outros ângulos as paredes já se juntam em meia-esquadria",
                            "the corner is not square: at other angles walls are mitred anyway"),
    # (0.300) split with gap, trim / extend to a boundary
    "tool.split_gap": ("Dividir com folga", "Split with gap"),
    "cmd.split_gap": ("Dividir com folga", "Split with gap"),
    "ctx.split_gap": ("Folga", "Gap"),
    "hint.split_gap": ("Clique numa parede onde a quer dividir, com uma folga de {g} ao meio (a folga muda na barra "
                       "de cima; ou digite a distância à ponta mais perto + Enter). Esc: Selecionar.",
                       "Click a wall where to split it, with a {g} gap in the middle (the gap changes on the bar "
                       "above; or type the distance to the nearer end + Enter). Esc: Select."),
    "info.split_gap": ("«{name}» dividida em {a} e {b}, com {g} de folga entre as duas partes (não ligadas). Ctrl+Z "
                       "desfaz.",
                       "“{name}” split into {a} and {b}, with a {g} gap between the two parts (not joined). Ctrl+Z "
                       "undoes."),
    "tool.trim_extend": ("Aparar / estender a um limite", "Trim / extend to a boundary"),
    "cmd.trim_extend": ("Aparar / estender", "Trim / extend"),
    "hint.trim_extend": ("Clique na parede que serve de limite. Esc: Selecionar.",
                         "Click the wall that is the boundary. Esc: Select."),
    "hint.trim_extend_2": ("Clique em cada parede a aparar ou estender até ao limite, do lado que fica. Esc: outro "
                           "limite.",
                           "Click each wall to trim or extend to the boundary, on the side that stays. Esc: another "
                           "boundary."),
    "keys.trim_extend": ("Clique: o limite, depois as paredes (do lado que fica)  ·  Esc: outro limite / Selecionar",
                         "Click: the boundary, then the walls (on the side that stays)  ·  Esc: another boundary / "
                         "Select"),
    "info.trim_extend_first": ("Limite: «{name}». Clique agora nas paredes a aparar ou estender até ela.",
                               "Boundary: “{name}”. Now click the walls to trim or extend to it."),
    "info.trim_extend": ("«{name}» vai até «{b}» (ligada se a encontra). Ctrl+Z desfaz.",
                         "“{name}” goes to “{b}” (joined where it meets it). Ctrl+Z undoes."),
    "rib.small.trim_extend": ("Aparar a um limite", "Trim to boundary"),
    # split a wall, trim / extend to a corner (0.104)
    "cmd.split_wall": ("Dividir parede", "Split wall"),
    "cmd.corner_walls": ("Aparar ao canto", "Trim to corner"),
    "tool.split_wall": ("Dividir parede", "Split wall"),
    "tool.corner_walls": ("Aparar / estender ao canto", "Trim / extend to corner"),
    "refuse.split_opening": ("o ponto cai numa porta, janela ou vão", "the point falls in a door, window or opening"),
    "refuse.parallel": ("as paredes são paralelas: não fazem canto", "the walls are parallel: they make no corner"),
    "refuse.joint": ("as paredes não se ligam ali (ângulo demasiado agudo)",
                     "the walls do not join there (too sharp an angle)"),
    "hint.split_wall": ("Clique numa parede onde a quer dividir (ou digite a distância à ponta mais perto + Enter). "
                        "Esc: Selecionar.",
                        "Click a wall where you want it split (or type the distance from the nearer end + Enter). "
                        "Esc: Select."),
    "keys.split_wall": ("Clique: dividir ali  ·  o meio da parede atrai  ·  Esc: Selecionar",
                        "Click: split there  ·  the wall's middle snaps  ·  Esc: Select"),
    "tip.split_here": ("Dividir aqui: {a} + {b}", "Split here: {a} + {b}"),
    "tip.split_middle": ("Meio da parede: {a} + {b}", "Wall's middle: {a} + {b}"),
    "info.split_wall": ("«{name}» dividida em {a} e {b}; cada parte leva as suas portas e janelas. Ctrl+Z desfaz.",
                        "“{name}” split into {a} and {b}; each part keeps its doors and windows. Ctrl+Z undoes."),
    "err.split_no_wall": ("Clique numa parede reta (uma parede feita neste programa).",
                          "Click a straight wall (made by this program)."),
    "hint.corner_walls": ("Clique na primeira parede, do lado que fica. Esc: Selecionar.",
                          "Click the first wall, on the side to keep. Esc: Select."),
    "hint.corner_walls_2": ("Clique na segunda parede, do lado que fica: as duas vão até ao canto e ligam-se. Botão "
                            "direito: recomeçar.",
                            "Click the second wall, on the side to keep: both go to the corner and are joined. Right "
                            "button: start again."),
    "keys.corner_walls": ("Clique: a primeira parede, depois a segunda (do lado que fica)  ·  Esc: Selecionar",
                          "Click: the first wall, then the second (on the side to keep)  ·  Esc: Select"),
    "info.corner_walls": ("«{a}» e «{b}» vão até ao canto e ficam ligadas. Ctrl+Z desfaz.",
                          "“{a}” and “{b}” go to the corner and are joined. Ctrl+Z undoes."),
    "info.corner_first": ("Primeira parede: «{name}». Agora a segunda.", "First wall: “{name}”. Now the second."),
    # roofs (0.111)
    "tool.roof": ("Cobertura", "Roof"),
    "elem.roof": ("Cobertura", "Roof"),
    "cmd.roof": ("Cobertura", "Roof"),
    "cmd.roof_edit": ("Mudar cobertura", "Change roof"),
    "ctx.roof_form": ("Forma", "Form"),
    "ctx.roof_slope": ("Inclinação", "Slope"),
    "ctx.overhang": ("Beirado", "Overhang"),
    "ctx.roof_shape": ("Contorno", "Outline"),
    "roofform.flat": ("Plana", "Flat"),
    "roofform.shed": ("Uma água", "Shed (one slope)"),
    "roofform.gable": ("Duas águas", "Gable (two slopes)"),
    "roofform.hip": ("Quatro águas", "Hip (all sides)"),
    "roofform.butterfly": ("Borboleta (calha ao meio)", "Butterfly (a valley in the middle)"),
    "roofform.barrel": ("Abóbada", "Barrel"),
    "roofform.custom": ("Perfil desenhado", "Drawn profile"),                                           # (0.251)
    # roofs by blocks (0.262)
    "roofform.gable_across": ("Duas águas (cumeeira no lado menor)", "Gable (ridge along the shorter side)"),
    "roofform.blocks": ("Por blocos", "By blocks"),
    "roofshape.blocks": ("Por blocos", "By blocks"),
    "roof.by_blocks": ("Por blocos ({n})", "By blocks ({n})"),
    "hint.roof.blocks": ("Bloco {form}, {slope}, beirado {o}: clique em dois cantos — {where} (Tab muda; Esc: o "
                         "próximo começa outra cobertura.)",
                         "Block {form}, {slope}, overhang {o}: click two corners — {where} (Tab changes it; Esc: the "
                         "next starts another roof.)"),
    "hint.roof.blocks_into": ("junta-se a «{roof}».", "it goes into \"{roof}\"."),
    "hint.roof.blocks_new": ("começa uma cobertura nova.", "it starts a new roof."),
    "info.roof_block": ("Bloco {form} em «{roof}» ({n} blocos). Ctrl+Z desfaz.",
                        "{form} block in \"{roof}\" ({n} blocks). Ctrl+Z undoes."),
    "info.roof_blocks_new": ("O próximo bloco começa outra cobertura.", "The next block starts another roof."),
    "cmd.roof_block": ("Bloco de cobertura", "Roof block"),
    "refuse.roof_blocks": ("a cobertura ficava sem blocos", "the roof would have no block"),
    "refuse.roof_blocks_form": ("uma cobertura por blocos muda-se bloco a bloco", "a roof by blocks is changed block "
                                "by block"),
    # the roof block editor (0.263)
    "blocked.title": ("Blocos da cobertura «{roof}»", "Blocks of the roof \"{roof}\""),
    "blocked.block": ("Bloco {n} — {form}, {w} × {d}", "Block {n} — {form}, {w} × {d}"),   # (10,20 × 6,20 m)
    "blocked.custom": ("Personalizada (lado a lado)", "Custom (side by side)"),
    "blocked.custom_short": ("Personalizada", "Custom"),
    "blocked.form": ("Forma", "Form"),
    "blocked.cx": ("Centro X", "Centre X"),
    "blocked.cy": ("Centro Y", "Centre Y"),
    "blocked.angle": ("Rotação", "Rotation"),
    "blocked.width": ("Largura", "Width"),
    "blocked.depth": ("Profundidade", "Depth"),
    "blocked.overhang": ("Beirado (avanço)", "Overhang"),
    "blocked.height": ("Altura do bloco", "Block height"),                                          # (0.356)
    "blocked.height_tip": ("A altura do beirado mais baixo do bloco. Mude-a para subir ou descer o bloco todo (todos "
                           "os seus beirados juntos); cada beirado muda-se em Lados.",
                           "The height of the block's lowest eave. Change it to raise or lower the whole block (all "
                           "its eaves together); each eave is changed in Sides."),
    "blocked.sides": ("Lados do bloco", "The block's sides"),
    "blocked.water": ("Água", "Slope"),
    "blocked.slope": ("Inclinação", "Pitch"),
    "blocked.eave": ("Cota do beirado", "Eave at"),
    "blocked.hint": ("Clique num bloco para o escolher (outra vez: o que está por baixo). Clique na letra de um lado "
                     "para trocar entre água e empena. As cotas do beirado são as do topo sobre a linha das paredes.",
                     "Click a block to choose it (again: the one under it). Click a side's letter to switch it between "
                     "a slope and a gable. The eave heights are the top's over the walls' line."),
    "blocked.apply": ("Aplicar", "Apply"),
    "blocked.close": ("Fechar", "Close"),
    "blocked.bad_number": ("Há um valor que não se percebe.", "A value cannot be read."),
    "blocked.problem": ("Bloco {n}: {e}.", "Block {n}: {e}."),
    "blockside.N": ("N", "N"),
    "blockside.E": ("E", "E"),
    "blockside.S": ("S", "S"),
    "blockside.W": ("O", "W"),
    "refuse.block_too_small": ("um bloco tem de ter pelo menos 20 cm de cada lado",
                               "a block must be at least 20 cm each way"),
    "props.edit_blocks": ("Editar blocos…", "Edit blocks…"),
    "props.edit_blocks_tip": ("Os blocos desta cobertura: forma, medidas, e por lado água, inclinação e beirado.",
                              "This roof's blocks: form, sizes, and each side's slope, pitch and eave."),
    "info.roof_blocks_saved": ("«{roof}»: {n} blocos. Ctrl+Z desfaz.", "\"{roof}\": {n} blocks. Ctrl+Z undoes."),
    # the blocks' grips (0.264)
    "hint.roof_block_side": ("Com o botão carregado, leve o lado do bloco para fora ou para dentro e largue; o lado "
                             "oposto fica (ou escreva a distância e Enter). Numa parede, encosta à face de fora. Esc: "
                             "deixar como estava.",
                             "With the button held, take the block's side out or in and let go; the opposite side "
                             "stays (or type the distance and press Enter). On a wall it goes to its outer face. Esc: "
                             "leave it as it was."),
    "hint.roof_block_move": ("Com o botão carregado, leve o bloco para o sítio e largue (ou escreva a distância e "
                             "Enter). Esc: deixar como estava.",
                             "With the button held, take the block where it goes and let go (or type the distance and "
                             "press Enter). Esc: leave it as it was."),
    "info.roof_block_side": ("Bloco {n}: lado mudado {d}. Ctrl+Z desfaz.", "Block {n}: side moved {d}. Ctrl+Z "
                             "undoes."),
    "info.roof_block_moved": ("Bloco {n} movido {d}. Ctrl+Z desfaz.", "Block {n} moved {d}. Ctrl+Z undoes."),
    # (0.385) the blocks edited in the 3D view
    "tool.roof_blocks": ("Blocos da cobertura", "Roof blocks"),
    "info.roof_blocks_edit": ("A editar os blocos de «{name}»: clique num bloco (Shift: vários). Arraste os quadrados "
                              "para escalar; «−» tira uma água, «+» põe-na; clique numa cota para a escrever. Esc: "
                              "sair.",
                              "Editing the blocks of “{name}”: click a block (Shift: several). Drag the squares to "
                              "scale; «−» takes a water away, «+» puts it back; click a height to type it. Esc: "
                              "leave."),
    "hint.roof_blocks_pick": ("Clique num bloco para o escolher (Shift: junta ao grupo). Esc: sair.",
                              "Click a block to choose it (Shift: add it to the group). Esc: leave."),
    "hint.roof_blocks": ("Quadrados: arraste para escalar (no meio de um lado: esse lado; num canto: os dois) · "
                         "losango: arraste move · «−» tira a água desse lado, «+» põe-na · clique numa cota e escreva "
                         "· Delete: apaga o bloco · Esc: sair.",
                         "Squares: drag to scale (in a side's middle: that side; on a corner: both) · diamond: drag "
                         "moves · «−» takes that side's water away, «+» puts it back · click a height and type · "
                         "Delete: removes the block · Esc: leave."),
    "hint.roof_blocks_none": ("Esta cobertura não é por blocos. Esc: Selecionar.",
                              "This roof is not by blocks. Esc: Select."),
    "hint.roof_blocks_drag_side": ("Com o botão carregado, leve o lado para fora ou para dentro e largue (o lado "
                                   "oposto fica). Botão direito: desiste.",
                                   "With the button held, take the side out or in and let go (the opposite side "
                                   "stays). Right button: give up."),
    "hint.roof_blocks_drag_move": ("Com o botão carregado, leve os blocos escolhidos e largue. Botão direito: desiste.",
                                   "With the button held, take the chosen blocks and let go. Right button: give up."),
    "hint.roof_blocks_drag_corner": ("Com o botão carregado, leve o canto e largue: o bloco cresce ou encolhe pelos "
                                     "dois lados (o canto oposto fica). Botão direito: desiste.",
                                     "With the button held, take the corner and let go: the block grows or shrinks by "
                                     "both sides (the opposite corner stays). Right button: give up."),
    "hint.roof_blocks_type": ("Escreva a cota (a partir do piso) e Enter. Esc: deixa como está.",
                              "Type the height (from the floor) and Enter. Esc: leave it as it is."),
    "keys.roof_blocks": ("Clique: escolher (Shift: vários)  ·  quadrados: escalar  ·  losango: mover  ·  «−» / «+»: "
                         "tirar / pôr água  ·  cota: clicar e escrever  ·  Delete: apagar  ·  Esc: sair",
                         "Click: choose (Shift: several)  ·  squares: scale  ·  diamond: move  ·  «−» / «+»: take away "
                         "/ put a water  ·  height: click and type  ·  Delete: remove  ·  Esc: leave"),
    "vcb.roof_eave": ("Cota do beirado", "Eave height"),
    "vcb.roof_block_height": ("Altura do bloco", "Block height"),
    "tip.roof_block_side": ("Arraste: esticar o lado {s}", "Drag: stretch side {s}"),
    "tip.roof_block_corner": ("Arraste: escalar o bloco (os dois lados deste canto)",
                              "Drag: scale the block (this corner's two sides)"),
    "tip.roof_block_move": ("Arraste: mover os blocos escolhidos", "Drag: move the chosen blocks"),
    "tip.roof_block_water": ("Pôr a água do lado {s}", "Put a water on side {s}"),
    "tip.roof_block_gable": ("Tirar a água do lado {s} (fica empena)", "Take side {s}'s water away (a gable)"),
    "info.roof_block_scaled": ("Bloco {n}: {w} × {d}. Ctrl+Z desfaz.", "Block {n}: {w} × {d}. Ctrl+Z undoes."),
    "info.roof_blocks_chosen": ("{n} bloco(s) escolhido(s): {b}.", "{n} block(s) chosen: {b}."),
    "info.roof_blocks_moved": ("{n} bloco(s) movido(s) {d}. Ctrl+Z desfaz.", "{n} block(s) moved {d}. Ctrl+Z undoes."),
    "info.roof_block_water": ("Bloco {n}: o lado {s} é agora uma água. Ctrl+Z desfaz.",
                              "Block {n}: side {s} is a water now. Ctrl+Z undoes."),
    "info.roof_block_gable": ("Bloco {n}: o lado {s} é agora uma empena. Ctrl+Z desfaz.",
                              "Block {n}: side {s} is a gable now. Ctrl+Z undoes."),
    "info.roof_block_eave": ("Bloco {n}: beirado {s} a {h}. Ctrl+Z desfaz.", "Block {n}: eave {s} at {h}. Ctrl+Z "
                             "undoes."),
    "info.roof_block_height": ("Bloco(s) {n} à altura {h}. Ctrl+Z desfaz.", "Block(s) {n} at height {h}. Ctrl+Z "
                               "undoes."),
    "info.roof_blocks_pick_first": ("Escolha primeiro um bloco (clique nele).", "Choose a block first (click it)."),
    "err.roof_blocks_last": ("Uma cobertura por blocos fica com um bloco pelo menos.",
                             "A roof by blocks keeps one block at least."),
    "info.roof_blocks_deleted": ("{n} bloco(s) apagado(s). Ctrl+Z desfaz.", "{n} block(s) removed. Ctrl+Z undoes."),
    # the AI's link to the window (0.269)
    "act.ai_link": ("Ligação à IA", "AI link"),
    "tip.ai_link": ("Deixa um assistente de IA (Claude…) trabalhar neste modelo através do MCP do ArqSynth "
                    "(python -m arqbim.mcp): só neste computador, com uma chave feita ao acaso. Cada mudança da IA "
                    "desfaz-se com Ctrl+Z.",
                    "Lets an AI assistant (Claude…) work on this model through ArqSynth's MCP (python -m arqbim.mcp): "
                    "this computer only, with a key made at random. Each of the AI's changes is undone with Ctrl+Z."),
    "info.ai_link_on": ("Ligação à IA ligada: o MCP do ArqSynth trabalha neste modelo (só neste computador).",
                        "AI link on: ArqSynth's MCP works on this model (this computer only)."),
    "info.ai_link_off": ("Ligação à IA desligada.", "AI link off."),
    "err.ai_link": ("Não foi possível abrir a ligação à IA neste computador.", "The AI link could not be opened on "
                    "this computer."),
    "info.ai_did": ("IA: {what}. Ctrl+Z desfaz.", "AI: {what}. Ctrl+Z undoes."),
    # putting the MCP server in the AI's programs (0.270)
    "act.ai_install": ("Ligar um assistente de IA…", "Connect an AI assistant…"),
    "tip.ai_install": ("Põe o MCP do ArqSynth no Claude Desktop com um clique, ou dá a linha para o Claude Code e "
                       "a configuração para outros programas.",
                       "Puts ArqSynth's MCP in Claude Desktop with a click, or gives the line for Claude Code and the "
                       "configuration for other programs."),
    "aiinst.title": ("Ligar um assistente de IA", "Connect an AI assistant"),
    "aiinst.intro": ("O MCP do ArqSynth deixa um assistente de IA (Claude Desktop, Claude Code…) ler e mudar os seus "
                     "modelos IFC. Com a «Ligação à IA» ligada (Gerenciar), trabalha no modelo aberto nesta janela, "
                     "à vista e com Ctrl+Z; sem ela, num modelo seu, que pode gravar e abrir.",
                     "ArqSynth's MCP lets an AI assistant (Claude Desktop, Claude Code…) read and change your IFC "
                     "models. With «AI link» on (Manage) it works on the model open in this window, in sight and with "
                     "Ctrl+Z; without it, on a model of its own it can save and open."),
    "aiinst.desktop_path": ("Ficheiro de configuração: {path}", "Configuration file: {path}"),
    "aiinst.desktop_button": ("Pôr no Claude Desktop", "Put in Claude Desktop"),
    "aiinst.desktop_done": ("Feito ({path}; a cópia do que lá estava ficou ao lado, .bak). Feche e abra o Claude "
                            "Desktop.", "Done ({path}; a copy of what was there is beside it, .bak). Close and open "
                            "Claude Desktop again."),
    "aiinst.code_hint": ("Escreva esta linha num terminal (fica para todas as pastas):",
                         "Type this line in a terminal (it holds for every folder):"),
    "aiinst.other": ("Outro programa (configuração JSON)", "Another program (JSON configuration)"),
    "aiinst.copy": ("Copiar", "Copy"),
    "aiinst.copied": ("Copiado.", "Copied."),
    "aiinst.failed": ("Não foi possível: {e}", "It could not be done: {e}"),
    "aiinst.tokens": ("Para gastar poucos tokens: comece por pedir um resumo do modelo; peça tabelas só com os campos "
                      "de que precisa («lista as paredes com o comprimento»); fale dos elementos pelo número (#54).",
                      "To spend few tokens: start by asking for a summary of the model; ask for tables with just the "
                      "fields you need («list the walls with their length»); name elements by their number (#54)."),
    "ai.created": ("criou", "made"),
    "ai.changed": ("mudou:", "changed:"),
    "ai.deleted": ("apagou", "deleted"),
    "ai.undone": ("desfez:", "undid:"),
    "ai.saved": ("gravou", "saved"),
    # each element's standard IFC set (0.266): the Properties' rows, their names in Portuguese
    "props.ifc_data": ("Dados IFC", "IFC data"),                  # (0.396: its set, {pset}, beside it)
    "props.ifc_data_tip": ("As propriedades comuns do IFC4 para esta classe (buildingSMART). Um campo vazio («—») "
                           "não vai para o IFC; o que o programa sabe preenche-se sozinho (a azul).",
                           "IFC4's common properties for this class (buildingSMART). An empty field («—») is not "
                           "written; what the program knows fills itself in (in blue)."),
    "ifcdata.auto": ("Preenchido pelo programa: acompanha o elemento.", "Filled in by the program: it follows the "
                     "element."),
    "ifcdata.manual": ("Escrito à mão: o programa não o muda (apague-o para voltar ao automático).",
                       "Written by hand: the program leaves it (clear it to have the automatic value back)."),
    "ifcdata.type": ("Do tipo: vale para todos os elementos deste tipo.", "The type's: it holds for every element of "
                     "this type."),
    # what the IFC data still miss (0.273)
    "act.missing_data": ("Dados IFC em falta…", "IFC data missing…"),
    "tip.missing_data": ("Antes de entregar: por classe e propriedade, quantos elementos ainda não têm valor; um "
                         "duplo clique seleciona-os.",
                         "Before delivering: by class and property, how many elements have no value yet; a double "
                         "click selects them."),
    "missing.title": ("Dados IFC em falta", "IFC data missing"),
    "missing.note": ("O conjunto comum do IFC4 de cada classe e, em cada propriedade, quantos elementos ainda não lhe "
                     "dão valor (nem eles nem o seu tipo). Duplo clique numa propriedade: os elementos sem ela ficam "
                     "selecionados, para os preencher nas Propriedades ou no tipo.",
                     "Each class's IFC4 common set and, for each property, how many elements give it no value yet "
                     "(neither they nor their type). Double click a property: the elements without it are selected, "
                     "to fill it in the Properties or in their type."),
    "missing.property": ("Propriedade", "Property"),
    "missing.without": ("Sem valor", "Without"),
    "missing.with": ("Com valor", "With"),
    "missing.class": ("{cls} — {n} elemento(s), {pset}", "{cls} — {n} element(s), {pset}"),
    "missing.summary": ("{n} classe(s); {holes} valores por preencher.", "{n} class(es); {holes} values to fill in."),
    "missing.none": ("Não há elementos com conjunto comum no modelo.", "No element with a common set in the model."),
    "missing.fill": ("Preencher o que o programa sabe", "Fill in what the program knows"),
    "missing.fill_tip": ("Escreve em todos os elementos o que o programa sabe deles: a referência (o tipo), exterior "
                         "ou interior, o U. Útil num modelo feito antes ou noutro programa. Ctrl+Z desfaz.",
                         "Writes into every element what the program knows of it: its reference (the type), outside "
                         "or inside, its U. Useful in a model made before or in another program. Ctrl+Z undoes."),
    "missing.filled": ("{n} valores escritos.", "{n} values written."),
    "missing.select": ("Selecionar os que faltam", "Select the missing ones"),
    "cmd.fill_data": ("Preencher dados IFC", "Fill in IFC data"),
    # a type's IFC data (0.271)
    "types.ifc_data": ("Dados IFC do tipo", "The type's IFC data"),
    "types.ifc_data_tip": ("O que vale para todos os elementos deste tipo (a resistência ao fogo, o isolamento "
                           "acústico…), salvo o que um elemento tiver escrito à mão. Fica no tipo IFC (IfcWallType…).",
                           "What holds for every element of this type (fire rating, acoustic rating…), but for what an "
                           "element has written by hand. Kept in the IFC type (IfcWallType…)."),
    "types.err_data": ("«{prop}»: o valor não se percebe.", "«{prop}»: the value cannot be read."),
    "cmd.type_data": ("Dados IFC do tipo", "Type IFC data"),
    "info.type_data": ("{prop} do tipo: vale para {n} elemento(s) dele. Ctrl+Z desfaz.",
                       "The type's {prop}: it holds for {n} element(s) of it. Ctrl+Z undoes."),
    "ifcprop.Reference": ("Referência (tipo)", "Reference (type)"),
    "ifcprop.IsExternal": ("Exterior", "External"),
    "ifcprop.LoadBearing": ("Estrutural (resistente)", "Load bearing"),
    "ifcprop.FireRating": ("Resistência ao fogo", "Fire rating"),
    "ifcprop.AcousticRating": ("Isolamento acústico", "Acoustic rating"),
    "ifcprop.ThermalTransmittance": ("Transmissão térmica U (W/m²·K)", "Thermal transmittance U (W/m²·K)"),
    "ifcprop.Combustible": ("Combustível", "Combustible"),
    "ifcprop.SurfaceSpreadOfFlame": ("Propagação da chama à superfície", "Surface spread of flame"),
    "ifcprop.Compartmentation": ("Compartimentação corta-fogo", "Fire compartmentation"),
    "ifcprop.ExtendToStructure": ("Vai até à estrutura", "Extends to the structure"),
    "ifcprop.PitchAngle": ("Inclinação (°)", "Pitch angle (°)"),
    "ifcprop.Slope": ("Inclinação", "Slope"),
    "ifcprop.Roll": ("Rotação sobre o eixo", "Roll"),
    "ifcprop.Span": ("Vão", "Span"),
    "ifcprop.SecurityRating": ("Classe de segurança", "Security rating"),
    "ifcprop.DurabilityRating": ("Classe de durabilidade", "Durability rating"),
    "ifcprop.HygrothermalRating": ("Classe higrotérmica", "Hygrothermal rating"),
    "ifcprop.WaterTightnessRating": ("Estanquidade à água", "Water tightness rating"),
    "ifcprop.MechanicalLoadRating": ("Resistência mecânica", "Mechanical load rating"),
    "ifcprop.WindLoadRating": ("Resistência ao vento", "Wind load rating"),
    "ifcprop.Infiltration": ("Permeabilidade ao ar", "Infiltration"),
    "ifcprop.GlazingAreaFraction": ("Fração envidraçada", "Glazing area fraction"),
    "ifcprop.HandicapAccessible": ("Acessível (mobilidade condicionada)", "Handicap accessible"),
    "ifcprop.FireExit": ("Saída de emergência", "Fire exit"),
    "ifcprop.HasDrive": ("Motorizada", "Has a drive"),
    "ifcprop.SelfClosing": ("Fecho automático", "Self closing"),
    "ifcprop.SmokeStop": ("Corta-fumo", "Smoke stop"),
    "ifcprop.HasSillExternal": ("Peitoril exterior", "External sill"),
    "ifcprop.HasSillInternal": ("Peitoril interior", "Internal sill"),
    "ifcprop.NumberOfRiser": ("Número de espelhos", "Number of risers"),
    "ifcprop.NumberOfTreads": ("Número de cobertores", "Number of treads"),
    "ifcprop.RiserHeight": ("Altura do espelho", "Riser height"),
    "ifcprop.TreadLength": ("Cobertor", "Tread length"),
    "ifcprop.NosingLength": ("Focinho", "Nosing length"),
    "ifcprop.WalkingLineOffset": ("Afastamento da linha de passo", "Walking line offset"),
    "ifcprop.TreadLengthAtOffset": ("Cobertor na linha de passo", "Tread length at the walking line"),
    "ifcprop.TreadLengthAtInnerSide": ("Cobertor do lado de dentro", "Tread length at the inner side"),
    "ifcprop.WaistThickness": ("Espessura da laje do lanço", "Waist thickness"),
    "ifcprop.RequiredHeadroom": ("Pé-direito livre exigido", "Required headroom"),
    "ifcprop.HasNonSkidSurface": ("Superfície antiderrapante", "Non-skid surface"),
    "ifcprop.RequiredSlope": ("Inclinação exigida", "Required slope"),
    "ifcprop.Height": ("Altura", "Height"),
    "ifcprop.Diameter": ("Diâmetro", "Diameter"),
    "ifcprop.FlammabilityRating": ("Inflamabilidade", "Flammability rating"),
    "ifcprop.FragilityRating": ("Fragilidade", "Fragility rating"),
    "ifcprop.Finish": ("Acabamento", "Finish"),
    "ifcprop.GrossPlannedArea": ("Área bruta prevista", "Gross planned area"),
    "ifcprop.NetPlannedArea": ("Área útil prevista", "Net planned area"),
    "ifcprop.PubliclyAccessible": ("Acesso público", "Publicly accessible"),
    "ifcprop.Style": ("Estilo", "Style"),
    "ifcprop.NominalHeight": ("Altura nominal", "Nominal height"),
    "ifcprop.NominalLength": ("Comprimento nominal", "Nominal length"),
    "ifcprop.NominalDepth": ("Profundidade nominal", "Nominal depth"),
    "ifcprop.NominalWidth": ("Largura nominal", "Nominal width"),
    "ifcprop.MainColor": ("Cor principal", "Main colour"),
    "ifcprop.Color": ("Cor", "Colour"),
    "ifcprop.IsBuiltIn": ("Embutido", "Built in"),
    "ifcprop.NominalDiameter": ("Diâmetro nominal", "Nominal diameter"),
    "ifcprop.InnerDiameter": ("Diâmetro interior", "Inner diameter"),
    "ifcprop.OuterDiameter": ("Diâmetro exterior", "Outer diameter"),
    "ifcprop.WorkingPressure": ("Pressão de serviço", "Working pressure"),
    "ifcprop.NumberOfSources": ("Número de lâmpadas", "Number of sources"),
    "ifcprop.TotalWattage": ("Potência total (W)", "Total wattage (W)"),
    "ifcprop.NumberOfSockets": ("Número de tomadas", "Number of sockets"),
    "ifcprop.IsPluggableOutlet": ("Tomada de ficha", "Pluggable outlet"),
    "ifcprop.NumberOfGangs": ("Número de teclas", "Number of gangs"),
    # a roof's carpentry (0.276)
    "props.carpentry": ("Madeiramento", "Carpentry"),
    "props.carpentry_make": ("Fazer madeiramento", "Make its carpentry"),
    "props.carpentry_again": ("Refazer", "Make again"),
    "props.carpentry_remove": ("Tirar", "Take away"),
    "props.carpentry_tip": ("Frechais nas paredes, fileira, varas de rincão e laró, terças, caibros a 0,50 m e ripas à "
                            "galga, como no ArqSynth Modeler; a cobertura sobe para assentar nele. Ctrl+Z desfaz.",
                            "Wall plates on the walls, ridge board, hip and valley rafters, purlins, rafters 0.50 m "
                            "apart and battens at the gauge, as in ArqSynth Modeler; the roof goes up to rest on it. "
                            "Ctrl+Z undoes."),
    "props.carpentry_row": ("{n} — {m} — {v} m³", "{n} — {m} — {v} m³"),
    "props.carpentry_sizes": ("Medidas…", "Sizes…"),                                          # (0.277)
    "carpdlg.title": ("Medidas do madeiramento", "The carpentry's sizes"),
    "carpdlg.note": ("Os afastamentos e as secções (largura × altura) de cada peça. Aplicar refaz o madeiramento por "
                     "baixo da cobertura, que sobe ou desce para assentar nele.",
                     "The spacings and each piece's section (width × height). Apply makes the carpentry again under "
                     "the roof, which goes up or down to rest on it."),
    "carpdlg.spacing": ("Caibros: afastamento", "Rafters: spacing"),
    "carpdlg.gauge": ("Ripas: galga da telha", "Battens: the tile's gauge"),
    "carpdlg.span": ("Terças: vão máximo dos caibros", "Purlins: the rafters' longest span"),
    "carpdlg.apply": ("Aplicar", "Apply"),
    "carpdlg.bad": ("Há uma medida que não se percebe (ou não é maior do que zero).",
                    "A size cannot be read (or is not over zero)."),
    "sched.cat.carpentry": ("Madeiramento", "Carpentry"),
    "sched.col.roof": ("Cobertura", "Roof"),
    "sched.col.piece": ("Peça", "Piece"),
    "sched.col.pieces": ("Peças", "Pieces"),
    "carp.frechal": ("Frechais", "Wall plates"),
    "carp.fileira": ("Fileira", "Ridge board"),
    "carp.rincao": ("Varas de rincão", "Hip rafters"),
    "carp.laro": ("Varas de laró", "Valley rafters"),
    "carp.terca": ("Terças", "Purlins"),
    "carp.caibro": ("Caibros", "Rafters"),
    "carp.ripa": ("Ripas", "Battens"),
    "cmd.carpentry": ("Madeiramento", "Carpentry"),
    "cmd.carpentry_off": ("Tirar madeiramento", "Take the carpentry away"),
    "info.carpentry": ("Madeiramento: {n} peças, {v} m³ de madeira; a cobertura assenta nele. Ctrl+Z desfaz.",
                       "Carpentry: {n} pieces, {v} m³ of timber; the roof rests on it. Ctrl+Z undoes."),
    "info.carpentry_off": ("Madeiramento tirado: a cobertura voltou a assentar nas paredes. Ctrl+Z desfaz.",
                           "Carpentry taken away: the roof rests on the walls again. Ctrl+Z undoes."),
    "refuse.roof_carpentry_form": ("só as coberturas inclinadas (uma, duas ou quatro águas, ou por blocos) levam "
                                   "madeiramento", "only pitched roofs (shed, gable, hip or by blocks) take carpentry"),
    # a roof's tiles (0.279)
    "props.tiles": ("Telhas", "Tiles"),
    "props.tiles_make": ("Assentar telhas", "Lay tiles"),
    "props.tiles_again": ("Refazer", "Lay again"),
    "props.tiles_remove": ("Tirar", "Take away"),
    "props.tiles_tip": ("Telhas em fiadas à galga e em colunas à largura útil, cortadas nos rincões, larós e empenas, "
                        "com telhas de cumeeira nas cumeeiras e nos rincões (como no ArqSynth Modeler).",
                        "Tiles in rows at their gauge and columns at their cover width, cut at the hips, valleys and "
                        "gables, with ridge tiles on the ridges and hips (as in the ArqSynth Modeler)."),
    "props.tile_kind": ("Telha", "Tile"),
    "props.tiles_stagger": ("Fiadas desencontradas", "Staggered rows"),
    "props.tiles_count": ("{n} ({c} cortadas)", "{n} ({c} cut)"),
    "props.noun.tiles": ("Telhas", "Tiles"),                         # (0.280: what its pieces are called)
    "props.noun.sheets": ("Chapas", "Sheets"),
    "props.noun.panels": ("Painéis", "Panels"),
    "props.tiles_caps": ("Telhas de cumeeira", "Ridge tiles"),
    "props.tiles_weight": ("Peso", "Weight"),
    "props.tiles_roof": ("Cobertura", "Roof"),
    "props.tiles_select_roof": ("Selecionar a cobertura", "Select the roof"),
    "sched.cat.tiles": ("Telhas", "Tiles"),
    "sched.col.tile": ("Telha", "Tile"),
    "sched.col.tiles": ("Telhas", "Tiles"),
    "sched.col.cut": ("Cortadas", "Cut"),
    "sched.col.caps": ("Cumeeiras", "Ridge tiles"),
    "sched.col.weight": ("Peso", "Weight"),
    "cmd.tiles": ("Telhas", "Tiles"),
    "cmd.tiles_off": ("Tirar telhas", "Take the tiles away"),
    "info.tiles": ("Telhado: {n} {noun} ({tile}), {c} telhas de cumeeira, {w} kg. Ctrl+Z desfaz.",
                   "Roofing: {n} {noun} ({tile}), {c} ridge tiles, {w} kg. Ctrl+Z undoes."),
    "info.tiles_off": ("Telhas tiradas. Ctrl+Z desfaz.", "Tiles taken away. Ctrl+Z undoes."),
    "refuse.roof_tiles_form": ("só as coberturas inclinadas (uma, duas ou quatro águas, ou por blocos) levam telhas",
                               "only pitched roofs (shed, gable, hip or by blocks) take tiles"),
    # a tile of the user's own (0.281)
    "props.register_tile": ("Usar como telha…", "Use as a tile…"),
    "props.register_tile_tip": ("Regista este componente como telha (como o «Registar telha» do ArqSynth Modeler): "
                                "em metros, com a origem num canto, x a largura, y o sentido da água (para baixo), "
                                "z para cima.",
                                "Registers this component as a tile (as the ArqSynth Modeler's «Register tile»): in "
                                "metres, its origin at a corner, x its width, y the way the water runs (down), z up."),
    # (0.289) the door and window generator
    "joinery.title": ("Gerador de portas e janelas", "Door and window generator"),
    "joinery.button": ("Caixilho Studio…", "Caixilho Studio…"),                                   # (0.307)
    "joinery.button_tip": ("Desenha a caixilharia deste tipo: folhas, aberturas, vidro, perfis e materiais. Mudam "
                           "todas as portas ou janelas do mesmo tipo.",
                           "Designs this type's joinery: leaves, openings, glass, profiles and materials. Every door "
                           "or window of the type changes."),
    "joinery.own": ("(o seu desenho)", "(your own design)"),
    "joinery.model": ("Modelo", "Layout"),
    "joinery.cell": ("Célula {cell} da linha {row}", "Cell {cell} of row {row}"),
    "joinery.operation": ("Abertura", "Opening"),
    "joinery.fill": ("Enchimento", "Fill"),
    "joinery.auto": ("automática", "automatic"),
    "joinery.cell_width": ("Largura", "Width"),
    "joinery.row_height": ("Altura da linha", "Row height"),
    "joinery.split": ("Dividir", "Split"),
    "joinery.join": ("Juntar à direita", "Join with the right"),
    "joinery.add_row": ("Linha por cima", "Row above"),
    "joinery.remove_row": ("Tirar a linha", "Remove the row"),
    "joinery.profiles": ("Perfis", "Profiles"),
    "joinery.frame": ("Aro (largura)", "Frame (width)"),
    "joinery.depth": ("Aro (profundidade)", "Frame (depth)"),
    "joinery.wall_depth": ("a da parede", "the wall's"),
    "joinery.sash": ("Folha (largura do perfil)", "Leaf (profile width)"),
    "joinery.sash_depth": ("Folha (espessura)", "Leaf (thickness)"),
    "joinery.mullion": ("Montantes e travessas", "Mullions and transoms"),
    "joinery.glass": ("Vidro (espessura)", "Glass (thickness)"),
    "joinery.casing": ("Guarnições (para fora do vão)", "Casings (beyond the opening)"),
    "joinery.threshold": ("Soleira (espessura)", "Threshold (thickness)"),                  # (0.290)
    "joinery.sill": ("Peitoril (espessura)", "Sill (thickness)"),
    "joinery.stone_out": ("Saliência para fora da parede", "Projection out of the wall"),
    "joinery.none": ("nenhum", "none"),
    "joinery.casing_sides": ("Guarnições em", "Casings on"),
    "joinery.casing_both": ("as duas faces", "both faces"),
    "joinery.casing_open": ("a face para onde abre", "the face it opens to"),
    "joinery.casing_push": ("a face de onde se empurra", "the face it is pushed from"),
    "joinery.drip": ("Pingadeira por baixo do peitoril", "Drip groove under the sill"),
    "joinery.hardware": ("Puxadores e dobradiças", "Handles and hinges"),
    "joinery.stone_material": ("Soleira / peitoril", "Threshold / sill"),
    "joinery.hardware_material": ("Ferragens", "Hardware"),
    "joinery.shutter": ("Estore (altura da caixa)", "Roller shutter (box height)"),          # (0.291)
    "joinery.shutter_closed": ("Estore descido", "Shutter let down"),
    "joinery.screen": ("Mosquiteiro", "Insect screen"),
    "joinery.grille": ("Grade", "Security grille"),
    "joinery.shutter_material": ("Estore e perfis do mosquiteiro", "Shutter and screen profiles"),
    "joinery.screen_material": ("Rede do mosquiteiro", "Insect mesh"),
    "joinery.grille_material": ("Grade", "Grille"),
    "joinery.materials": ("Materiais", "Materials"),
    "joinery.frame_material": ("Aro e folhas", "Frame and leaves"),
    "joinery.panel_material": ("Painéis cegos", "Solid panels"),
    "joinery.glass_material": ("Vidro", "Glass"),
    "joinery.ifc": ("No IFC: {name}", "In the IFC: {name}"),
    "joinery.err_profiles": ("Os perfis têm de ter medida, e o aro tem de caber na largura e na altura.",
                             "The profiles must have a size, and the frame must fit in the width and the height."),
    "joinery.err_heights": ("As alturas das linhas não dão a altura do tipo (deixe uma em branco para ficar com o "
                            "resto).",
                            "The rows' heights do not add up to the type's height (leave one blank to take the rest)."),
    "joinery.err_widths": ("As larguras das células de uma linha não dão a largura do tipo (deixe uma em branco para "
                           "ficar com o resto).",
                           "A row's cell widths do not add up to the type's width (leave one blank to take the rest)."),
    "joinery.err_small": ("A célula {cell} da linha {row} fica pequena demais para a sua folha.",
                          "Cell {cell} of row {row} is too small for its leaf."),
    "joinery.err_arch": ("O arco não cabe: a flecha de um arco abatido vai até meia largura, e o arco tem de deixar "
                         "pelo menos 0,30 m por baixo.",
                         "The arch does not fit: a segmental arch rises up to half the width, and the arch must "
                         "leave at least 0.30 m under it."),
    "joinery.err_arch_leaf": ("A célula {cell} da linha {row} entra no arco: debaixo do arco a folha não pode ser "
                              "projetante, de correr, guilhotina nem harmónio (escolha outra abertura, ou acerte a "
                              "altura da linha com a flecha do arco).",
                              "Cell {cell} of row {row} reaches into the arch: under the arch a leaf cannot be "
                              "top-hung, sliding, sash nor folding (choose another way, or make the row's height the "
                              "arch's rise)."),
    "joinery.arch": ("Arco", "Arch"),                                                        # (0.294)
    "joinery.arch_none": ("reto (sem arco)", "square (no arch)"),
    "joinery.arch_round": ("de volta inteira", "round"),
    "joinery.arch_segmental": ("abatido", "segmental"),
    "joinery.arch_pointed": ("ogival", "pointed"),
    "joinery.arch_rise": ("Flecha do arco (abatido)", "Arch rise (segmental)"),
    "joinery.louvres": ("Portadas de lâminas", "Louvred shutters"),                         # (0.295)
    "joinery.louvres_none": ("sem portadas", "none"),
    "joinery.louvres_left": ("1 folha, dobradiças à esquerda", "1 leaf, hinged left"),
    "joinery.louvres_right": ("1 folha, dobradiças à direita", "1 leaf, hinged right"),
    "joinery.louvres_pair": ("2 folhas", "2 leaves"),
    "joinery.louvres_open": ("Portadas abertas (rebatidas sobre a parede)", "Shutters open (folded back on the wall)"),
    "joinery.louvres_material": ("Portadas", "Shutters"),
    "joinery.err_louvres_shutter": ("Portadas e estore não vão juntos: tire um deles.",
                                    "Shutters and a roller shutter do not go together: take one away."),
    "joinery.err_louvres_small": ("As portadas ficam pequenas demais para as lâminas.",
                                  "The shutters are too small for their louvres."),
    "tiledlg.title": ("Usar como telha", "Use as a tile"),
    "tiledlg.note": ("O componente assenta como telha: em fiadas à galga e em colunas à largura útil. Escreva os "
                     "dados do fabricante. A forma deve estar em metros, com a origem num canto, x a largura, y o "
                     "sentido da água (para baixo) e z para cima.",
                     "The component is laid as a tile: in rows at its gauge and columns at its cover width. Type in "
                     "its maker's data. Its shape should be in metres, its origin at a corner, x its width, y the "
                     "way the water runs (down), z up."),
    "tiledlg.measured": ("Medida (largura × comprimento × altura)", "Measured (width × length × height)"),
    "tiledlg.name": ("Nome", "Name"),
    "tiledlg.cover": ("Largura útil", "Cover width"),
    "tiledlg.gauge": ("Galga (comprimento útil)", "Gauge (cover length)"),
    "tiledlg.weight": ("Peso por telha (kg)", "Weight a tile (kg)"),
    "tiledlg.apply": ("Registar", "Register"),
    "tiledlg.bad": ("Escreva um nome, a largura útil e a galga entre 2 cm e 3 m e o peso.",
                    "Type in a name, the cover width and gauge between 2 cm and 3 m, and the weight."),
    "tiledlg.bigger": ("A largura útil e a galga não podem ser maiores do que a própria telha.",
                       "The cover width and gauge cannot be more than the tile itself."),
    "tiledlg.warn.size": ("Medidas estranhas: confirme que o componente está em metros.",
                          "Odd sizes: make sure the component is in metres."),
    "cmd.register_tile": ("Registar telha", "Register a tile"),
    "info.tile_registered": ("Telha registada: {name} (útil {c}, galga {g}). Escolha-a em Telha, nas Propriedades "
                             "de uma cobertura.", "Tile registered: {name} (cover {c}, gauge {g}). Choose it as the "
                             "Tile in a roof's Properties."),
    "refuse.tile_measures": ("a largura útil e a galga têm de estar entre 2 cm e 3 m",
                             "the cover width and gauge must be between 2 cm and 3 m"),
    # a roof by blocks' edges (0.265)
    "props.edge.eave": ("Beirados", "Eaves"),
    "props.edge.ridge": ("Cumeeiras", "Ridges"),
    "props.edge.hip": ("Rincões", "Hips"),
    "props.edge.valley": ("Larós", "Valleys"),
    "props.edge.gable": ("Empenas (bordos inclinados)", "Gable edges (rakes)"),
    "props.edge.top": ("Remates no alto", "Top edges"),
    "refuse.roof_rect": ("a borboleta, a abóbada e o perfil desenhado fazem-se sobre um contorno retangular",
                         "a butterfly, a barrel or a drawn profile roof goes over a rectangle"),
    "refuse.roof_section": ("a secção da cobertura tem de fechar uma área com pelo menos 50 cm de largura e 2 cm de "
                            "espessura — desenhe-a numa face e use Perfil da cobertura",
                            "the roof's section must close an area at least 50 cm wide and 2 cm thick — draw it as a "
                            "face and use Roof profile"),
    "act.roof_profile": ("Perfil da cobertura", "Roof profile"),
    "tip.roof_profile": ("Selecione uma cobertura sobre um retângulo e uma face plana desenhada (a secção, à medida "
                         "real, de pé atravessada ou no chão): a cobertura passa a essa secção, ao meio do vão e com o "
                         "ponto mais baixo à altura do beirado, corrida ao comprido.",
                         "Select a roof over a rectangle and a flat face drawn (the section, real size, upright "
                         "across it or on the ground): the roof becomes that section, over the span's middle, its "
                         "lowest point at the eave, run along it."),
    "cmd.roof_profile": ("Perfil da cobertura", "Roof profile"),
    "info.roof_profile": ("Cobertura feita com a secção desenhada. Ctrl+Z desfaz.",
                          "Roof made with the section drawn. Ctrl+Z undoes."),
    "err.roof_profile": ("Selecione uma cobertura e uma face plana desenhada (só as duas).",
                         "Select a roof and a flat face drawn (those two only)."),
    "roofshape.wand": ("Pelas paredes (clique dentro)", "By the walls (click inside)"),
    "roofshape.rect": ("Retângulo", "Rectangle"),
    "roofshape.poly": ("Polígono", "Polygon"),
    "roofshape.face": ("A partir de uma laje ou face", "From a slab or a face"),
    "hint.roof.face": ("{form}, {slope}, beirado {o}: clique numa laje ou numa face horizontal de um esboço — a "
                       "cobertura assenta nela. (Tab muda o contorno.)",
                       "{form}, {slope}, overhang {o}: click a slab or a level face of a sketch — the roof sits on "
                       "it. (Tab changes the outline.)"),
    "hint.roof.wand": ("{form}, {slope}, beirado {o}: clique dentro das paredes fechadas — a cobertura assenta no "
                       "topo delas. (Tab muda o contorno.)",
                       "{form}, {slope}, overhang {o}: click inside closed walls — the roof sits on their top. "
                       "(Tab changes the outline.)"),
    "hint.roof.rect": ("{form}, {slope}, beirado {o}: clique no primeiro canto (a linha de fora das paredes). (Tab "
                       "muda o contorno.)",
                       "{form}, {slope}, overhang {o}: click the first corner (the walls' outer line). (Tab "
                       "changes the outline.)"),
    "hint.roof.poly": ("{form}, {slope}, beirado {o}: clique nos cantos (a linha de fora das paredes); o primeiro "
                       "canto ou Enter fecha. (Tab muda o contorno.)",
                       "{form}, {slope}, overhang {o}: click the corners (the walls' outer line); the first corner "
                       "or Enter closes it. (Tab changes the outline.)"),
    "keys.roof": ("Tab: pelas paredes → retângulo → polígono → a partir de uma face  ·  X / Y: bloquear o eixo  ·  "
                  "Delete: apagar o último canto",
                  "Tab: by the walls → rectangle → polygon → from a face  ·  X / Y: lock the axis  ·  Delete: take "
                  "the last corner back"),
    "info.roof": ("Cobertura {form} de {a} (em planta), a {slope}, com o topo sobre as paredes a {z}. Ctrl+Z "
                  "desfaz.",
                  "{form} roof of {a} (in plan), at {slope}, its top over the walls at {z}. Ctrl+Z undoes."),
    "err.roof_wand": ("Aqui não há paredes fechadas à volta", "There are no closed walls round here"),
    "refuse.roof_not_convex": ("sobre um contorno com cantos para dentro só se faz uma cobertura de quatro águas "
                               "(ou plana); para uma de duas águas, divida-a em partes",
                               "over an outline with inward corners only a hip roof (or a flat one) is made; for a "
                               "gable roof, split it in parts"),
    "refuse.roof_slope": ("a inclinação tem de ficar entre 0° e 80°", "the slope must be between 0° and 80°"),
    "props.roof_form": ("Forma", "Form"),
    "props.roof_slope": ("Inclinação", "Slope"),
    "props.overhang": ("Beirado", "Overhang"),
    "props.eave": ("Cota do topo sobre as paredes", "Top over the walls at"),
    "props.roof_area": ("Área inclinada", "Sloped area"),
    "props.projected": ("Área em planta", "Area in plan"),
    "props.top_roof": ("Cobertura «{name}» (face de baixo)", "Roof “{name}” (underside)"),
    # ceilings (0.118)
    "tool.ceiling": ("Teto", "Ceiling"),
    "elem.ceiling": ("Teto", "Ceiling"),
    # the floor finish (0.374, the study's «Piso»)
    "tool.flooring": ("Piso", "Floor finish"),
    "elem.flooring": ("Piso", "Floor finish"),
    "cmd.flooring": ("Piso", "Floor finish"),
    "ctx.flooring": ("Acabamento", "Finish"),
    "flooring.ceramico": ("Cerâmico", "Ceramic tiles"),
    "flooring.madeira": ("Madeira", "Wood"),
    "flooring.pedra": ("Pedra", "Stone"),
    "flooring.vinilico": ("Vinílico", "Vinyl"),
    "flooring.betao": ("Betão afagado", "Polished concrete"),
    "hint.flooring.wand": ("Piso {f}: clique dentro das paredes de um ambiente. (Tab muda o contorno.)",
                           "{f} floor: click inside a room's walls. (Tab changes the outline.)"),
    "hint.flooring.rect": ("Piso {f}: clique num canto do retângulo. (Tab muda o contorno.)",
                           "{f} floor: click a corner of the rectangle. (Tab changes the outline.)"),
    "hint.flooring.poly": ("Piso {f}: clique os cantos; no 1.º ponto (ou Enter) fecha. (Tab muda o contorno.)",
                           "{f} floor: click its corners; on the first one (or Enter) it closes. (Tab changes the "
                           "outline.)"),
    "info.flooring": ("Piso {f} de {a} sobre a laje (IFC, nas quantidades).",
                      "{f} floor of {a} on the slab (IFC, in the quantities)."),
    "cmd.ceiling": ("Teto", "Ceiling"),
    "cmd.ceiling_edit": ("Mudar teto", "Change ceiling"),
    "cmd.flooring_edit": ("Mudar piso", "Change floor finish"),                       # (0.415)
    "props.catalog_type": ("Tipo do catálogo", "Catalogue type"),
    "props.type_fixed": ("O tipo do catálogo, escolhido ao colocar (para outro, coloque outro elemento)",
                         "The catalogue type, chosen when placed (for another, place another element)"),
    "ctx.ceiling_style": ("Acabamento", "Finish"),
    "ctx.ceiling_height": ("Altura do teto", "Ceiling height"),
    "ceilshape.wand": ("Por ambiente (clique dentro)", "By room (click inside)"),
    "ceilshape.rect": ("Retângulo", "Rectangle"),
    "ceilshape.poly": ("Polígono", "Polygon"),
    "ceilstyle.continuous": ("Contínuo (gesso cartonado)", "Continuous (plasterboard)"),
    "ceilstyle.tiles": ("Placas 60 × 60", "60 × 60 tiles"),
    "hint.ceiling.wand": ("Teto {style} a {h}: clique dentro das paredes de um ambiente. (Tab muda o contorno.)",
                          "{style} ceiling at {h}: click inside a room's walls. (Tab changes the outline.)"),
    "hint.ceiling.rect": ("Teto {style} a {h}: clique no primeiro canto. (Tab muda o contorno.)",
                          "{style} ceiling at {h}: click the first corner. (Tab changes the outline.)"),
    "hint.ceiling.poly": ("Teto {style} a {h}: clique nos cantos; o primeiro ou Enter fecha. (Tab muda o contorno.)",
                          "{style} ceiling at {h}: click its corners; the first one or Enter closes it. (Tab changes "
                          "the outline.)"),
    "keys.ceiling": ("Tab: por ambiente → retângulo → polígono  ·  X / Y: bloquear o eixo  ·  Delete: apagar o último "
                     "canto",
                     "Tab: by room → rectangle → polygon  ·  X / Y: lock the axis  ·  Delete: take the last corner "
                     "back"),
    "info.ceiling": ("Teto {style} de {a} a {h} do pavimento. Ctrl+Z desfaz.",
                     "{style} ceiling of {a} at {h} over the storey. Ctrl+Z undoes."),
    # ceilings' shadow gap and bulkhead, wall finishes, lights (0.119)
    "ctx.ceiling_gap": ("Rasgo", "Shadow gap"),                  # (0.456: shorter — the bar fits 1920 px)
    "ctx.bulkhead": ("Sanca", "Bulkhead"),
    "ctx.bulkhead_drop": ("Descida", "Drop"),
    "refuse.ceiling_gap": ("o rasgo vai de 0 a 20 cm", "the shadow gap goes from 0 to 20 cm"),
    "tool.wall_finish": ("Revestimento de parede", "Wall finish"),
    "elem.cladding": ("Revestimento", "Wall finish"),
    "cmd.cladding": ("Revestimento de parede", "Wall finish"),
    "cmd.cladding_edit": ("Mudar revestimento", "Change wall finish"),
    "ctx.finish": ("Acabamento", "Finish"),
    "ctx.finish_height": ("Até à altura", "Up to"),
    "finish.azulejo": ("Azulejo", "Ceramic tiles"),
    "finish.reboco": ("Reboco", "Plaster"),
    "finish.pedra": ("Pedra", "Stone"),
    "hint.wall_finish": ("Revestimento ({f} até {h}): clique na face de uma parede — fica recortado nas portas e "
                         "janelas e acompanha a parede.",
                         "Wall finish ({f} up to {h}): click a wall's face — it is cut round the doors and windows "
                         "and follows the wall."),
    "keys.wall_finish": ("Clique: o revestimento nessa face  ·  Esc: Selecionar",
                         "Click: the finish on that face  ·  Esc: Select"),
    "info.wall_finish": ("{f} até {h} na parede «{wall}». Ctrl+Z desfaz.", "{f} up to {h} on the wall “{wall}”. "
                                                                           "Ctrl+Z undoes."),
    "tool.light": ("Luminária", "Light"),
    "elem.light": ("Luminária", "Light"),
    "cmd.light": ("Luminária", "Light"),
    "ctx.light": ("Luminária", "Light"),
    "light.panel": ("Painel 60 × 60", "60 × 60 panel"),
    "light.downlight": ("Foco de encastrar", "Downlight"),
    "hint.light": ("Luminária ({k}): clique sob um teto — fica embutida nele.",
                   "Light ({k}): click under a ceiling — it is set in it."),
    "keys.light": ("Clique: uma luminária ali  ·  Esc: Selecionar", "Click: a light there  ·  Esc: Select"),
    "tip.light": ("Luminária no teto", "Light in the ceiling"),
    "tip.light_no_ceiling": ("Sem teto aqui: a 2,60 m do pavimento", "No ceiling here: 2.60 m over the storey"),
    "info.light": ("{k} posta. Ctrl+Z desfaz.", "{k} put in. Ctrl+Z undoes."),
    "tree.cat.IfcLightFixture": ("Luminárias", "Lights"),
    # air terminals (0.138)
    "tool.air_terminal": ("Grelha / difusor", "Grille / diffuser"),
    "elem.air_terminal": ("Difusor", "Diffuser"),
    "cmd.air_terminal": ("Grelha / difusor", "Grille / diffuser"),
    "ctx.air_terminal": ("Terminal de ar", "Air terminal"),
    "terminal.diffuser_60": ("Difusor quadrado 60 × 60", "60 × 60 square diffuser"),
    "terminal.diffuser_30": ("Difusor quadrado 30 × 30", "30 × 30 square diffuser"),
    "terminal.round_diffuser": ("Difusor circular Ø30", "Ø30 round diffuser"),
    "terminal.grille_60x30": ("Grelha de retorno 60 × 30", "60 × 30 return grille"),
    "air.supply": ("Insuflação", "Supply"),
    "air.return": ("Retorno", "Return"),
    "hint.air_terminal": ("Grelha / difusor ({k}): clique sob um teto — fica embutido nele; uma conduta desenhada até "
                          "ele desce e liga-se.",
                          "Grille / diffuser ({k}): click under a ceiling — it is set in it; a duct drawn to it comes "
                          "down to it and is connected."),
    "keys.air_terminal": ("Clique: um terminal ali  ·  Esc: Selecionar", "Click: a terminal there  ·  Esc: Select"),
    "tip.air_terminal": ("Terminal no teto", "Terminal in the ceiling"),
    "tip.air_terminal_no_ceiling": ("Sem teto aqui: a 2,60 m do pavimento", "No ceiling here: 2.60 m over the storey"),
    "info.air_terminal": ("{k} posto. Ctrl+Z desfaz.", "{k} put in. Ctrl+Z undoes."),
    "tree.cat.IfcAirTerminal": ("Grelhas e difusores", "Grilles and diffusers"),
    "props.air": ("Ar", "Air"),
    "tip.segment_to_terminal": ("Ligar a este terminal (desce até ele)", "Join this terminal (down to it)"),
    "tip.segment_from_terminal": ("Começar neste terminal (sobe a partir dele)", "Start on this terminal (up from it)"),
    "info.segment_terminal": ("{done} Desce até ao terminal e fica ligado a ele.",
                              "{done} It comes down to the terminal and is connected to it."),
    # HVAC equipment (0.139)
    "tool.equipment": ("Equipamento AVAC", "HVAC unit"),
    "elem.equipment": ("Equipamento", "Unit"),
    "cmd.equipment": ("Equipamento AVAC", "HVAC unit"),
    "ctx.equipment": ("Equipamento", "Unit"),
    "ctx.equipment_base": ("Base a", "Base at"),
    "equipment.ducted_unit": ("Unidade de conduta (no teto falso)", "Ducted unit (in the ceiling void)"),
    "equipment.split_wall": ("Unidade interior mural (split)", "Wall split unit"),
    "equipment.outdoor_unit": ("Unidade exterior", "Outdoor unit"),
    "equipment.ahu": ("Unidade de tratamento de ar (UTA)", "Air handling unit (AHU)"),
    "hint.equipment": ("{k}, base a {h}: clique onde fica (o meio da base). R / Shift+R roda 90°. As condutas "
                       "começam nas suas ligações ou acabam nelas.",
                       "{k}, base at {h}: click where it goes (its base's middle). R / Shift+R turns 90°. Ducts start "
                       "from its connections or end on them."),
    "keys.equipment": ("Clique: um equipamento ali  ·  R / Shift+R: rodar  ·  Esc: Selecionar",
                       "Click: a unit there  ·  R / Shift+R: turn  ·  Esc: Select"),
    "info.equipment": ("{k} posto. Ctrl+Z desfaz.", "{k} put in. Ctrl+Z undoes."),
    "tree.cat.IfcUnitaryEquipment": ("Equipamentos AVAC", "HVAC units"),
    "port.supply": ("Insuflação", "Supply"),
    "port.return": ("Retorno", "Return"),
    "port.condensate": ("Condensados", "Condensate"),
    "tip.segment_to_port": ("Ligar aqui ({port})", "Join here ({port})"),
    "tip.segment_from_port": ("Começar aqui ({port})", "Start here ({port})"),
    "info.segment_port": ("{done} Fica ligado a «{name}».", "{done} It is connected to “{name}”."),
    # sanitary fixtures (0.140)
    "tool.fixture": ("Louça sanitária", "Sanitary fixture"),
    "cmd.fixture": ("Louça sanitária", "Sanitary fixture"),
    "ctx.fixture": ("Louça", "Fixture"),
    "fixture.wc": ("Sanita", "WC"),
    "fixture.basin": ("Lavatório", "Washbasin"),
    "fixture.bidet": ("Bidé", "Bidet"),
    "fixture.shower": ("Base de duche", "Shower tray"),
    "fixture.bath": ("Banheira", "Bath"),
    "fixture.kitchen_sink": ("Lava-loiça", "Kitchen sink"),
    "elem.fixture.wc": ("Sanita", "WC"),
    "elem.fixture.basin": ("Lavatório", "Washbasin"),
    "elem.fixture.bidet": ("Bidé", "Bidet"),
    "elem.fixture.shower": ("Base de duche", "Shower tray"),
    "elem.fixture.bath": ("Banheira", "Bath"),
    "elem.fixture.kitchen_sink": ("Lava-loiça", "Kitchen sink"),
    "hint.fixture": ("{k}: passe sobre a face de uma parede — encosta-se a ela, virada para o ambiente — e clique. Longe "
                     "das paredes: no ponto, R / Shift+R roda. A verde, a zona livre à frente.",
                     "{k}: move over a wall's face — it goes against it, facing the room — and click. Away from "
                     "walls: at the point, R / Shift+R turns it. In green, the free zone in front."),
    "keys.fixture": ("Clique: a louça ali  ·  R / Shift+R: rodar  ·  Esc: Selecionar",
                     "Click: the fixture there  ·  R / Shift+R: turn  ·  Esc: Select"),
    "info.fixture": ("{k} posta. Ctrl+Z desfaz.", "{k} put in. Ctrl+Z undoes."),
    "info.fixture_wall": ("{k} posta, encostada à parede. Ctrl+Z desfaz.", "{k} put in, against the wall. Ctrl+Z "
                                                                           "undoes."),
    "props.connections_of": ("Ligações", "Connections"),
    "conn.drain": ("Esgoto", "Drain"),
    "conn.cold": ("Água fria", "Cold water"),
    "conn.hot": ("Água quente", "Hot water"),
    "props.free_zone": ("Zona livre", "Free zone"),
    # systems (0.141)
    "ctx.system": ("Sistema", "System"),
    "props.system": ("Sistema", "System"),
    "system.cold": ("Água fria", "Cold water"),
    "system.hot": ("Água quente", "Hot water"),
    "system.sewage": ("Águas negras", "Sewage"),
    "system.waste": ("Águas saponáceas", "Waste water"),
    "system.rain": ("Águas pluviais", "Rainwater"),
    "system.gas": ("Gás", "Gas"),
    "system.refrigerant_liquid": ("Refrigerante — líquido", "Refrigerant — liquid"),          # (0.196)
    "system.refrigerant_gas": ("Refrigerante — gás", "Refrigerant — gas"),
    "system.supply_air": ("Insuflação", "Supply air"),
    "system.return_air": ("Retorno", "Return air"),
    "system.exhaust": ("Extração", "Exhaust"),
    "system.fresh_air": ("Ar novo", "Fresh air"),
    "system.none": ("(nenhum)", "(none)"),
    "cmd.set_system": ("Mudar o sistema", "Change the system"),
    # electrical points (0.143)
    "tool.electrical": ("Ponto elétrico", "Electrical point"),
    "cmd.electrical": ("Ponto elétrico", "Electrical point"),
    "ctx.electrical": ("Ponto", "Point"),
    "ctx.point_height": ("A", "At"),
    "point.outlet": ("Tomada", "Outlet"),
    "point.outlet_double": ("Tomada dupla", "Double outlet"),
    "point.outlet_counter": ("Tomada de bancada", "Counter outlet"),
    "point.data_outlet": ("Tomada de dados (RJ45)", "Data outlet (RJ45)"),
    "point.switch": ("Interruptor", "Switch"),
    "point.switch_two_way": ("Comutador de escada", "Two-way switch"),
    "point.board": ("Quadro elétrico", "Distribution board"),
    "point.junction_box": ("Caixa de derivação", "Junction box"),
    "elem.point.outlet": ("Tomada", "Outlet"),
    "elem.point.outlet_double": ("Tomada dupla", "Double outlet"),
    "elem.point.outlet_counter": ("Tomada", "Outlet"),
    "elem.point.data_outlet": ("Tomada de dados", "Data outlet"),
    "elem.point.switch": ("Interruptor", "Switch"),
    "elem.point.switch_two_way": ("Comutador", "Two-way switch"),
    "elem.point.board": ("Quadro", "Board"),
    "elem.point.junction_box": ("Caixa", "Box"),
    "hint.electrical": ("{k} a {h} do chão: passe sobre a face de uma parede — encosta-se a ela — e clique. Na "
                        "planta, o seu símbolo.",
                        "{k} at {h} over the floor: move over a wall's face — it goes against it — and click. On the "
                        "plan, its symbol."),
    "keys.electrical": ("Clique: o ponto ali  ·  R / Shift+R: rodar  ·  Esc: Selecionar",
                        "Click: the point there  ·  R / Shift+R: turn  ·  Esc: Select"),
    "info.point": ("Ponto posto: {k}, a {h}. Ctrl+Z desfaz.", "Point put in: {k}, at {h}. Ctrl+Z undoes."),
    "info.point_wall": ("Ponto posto na parede: {k}, a {h}. Ctrl+Z desfaz.",
                        "Point put on the wall: {k}, at {h}. Ctrl+Z undoes."),
    "tree.cat.IfcOutlet": ("Tomadas", "Outlets"),
    "tree.cat.IfcSwitchingDevice": ("Interruptores", "Switches"),
    "tree.cat.IfcElectricDistributionBoard": ("Quadros elétricos", "Distribution boards"),
    "tree.cat.IfcJunctionBox": ("Caixas de derivação", "Junction boxes"),
    # circuits and the load schedule (0.144)
    "cmd.circuit": ("Novo circuito", "New circuit"),
    "cmd.circuit_edit": ("Mudar o circuito", "Change the circuit"),
    "cmd.circuit_remove": ("Apagar o circuito", "Delete the circuit"),
    "act.new_circuit": ("Novo circuito", "New circuit"),       # (0.324: it asks for its points when none are selected)
    "tip.new_circuit": ("Os pontos elétricos e as luminárias selecionados fazem um circuito novo (C1, C2…) do tipo "
                        "que eles dizem, no quadro do seu pavimento; o quadro de cargas (Tabelas ▸ Circuitos) mostra "
                        "a potência, a corrente e a verificação.",
                        "The selected electrical points and lights make a new circuit (C1, C2…) of the type they say, "
                        "on their storey's board; the load schedule (Tables ▸ Circuits) shows its power, current and "
                        "check."),
    "info.circuit_made": ("Circuito {name} ({k}): {n} pontos, {p}. Veja o quadro de cargas em Tabelas ▸ Circuitos.",
                          "Circuit {name} ({k}): {n} points, {p}. See the load schedule in Tables ▸ Circuits."),
    "info.circuit_none": ("Selecione pontos elétricos ou luminárias para fazer um circuito.",
                          "Select electrical points or lights to make a circuit."),
    "circuit.lighting": ("Iluminação", "Lighting"),
    "circuit.outlets": ("Tomadas", "Outlets"),
    "circuit.kitchen": ("Cozinha", "Kitchen"),
    "circuit.appliance": ("Máquina", "Appliance"),
    "circuit.hvac": ("AVAC", "HVAC"),
    "circuit.ok": ("OK", "OK"),
    "circuit.why.current": ("corrente acima do disjuntor", "current above the breaker"),
    "circuit.why.points": ("pontos a mais para o tipo", "too many points for the type"),
    "circuit.why.section": ("secção pequena para o disjuntor", "section too small for the breaker"),
    "sched.cat.circuits": ("Circuitos: quadro de cargas", "Circuits: load schedule"),
    "sched.count_circuits": ("{n} circuitos", "{n} circuits"),
    "sched.col.circuit_type": ("Tipo", "Type"),
    "sched.col.board": ("Quadro", "Board"),
    "sched.col.points": ("Pontos", "Points"),
    "sched.col.power": ("Potência", "Power"),
    "sched.col.current": ("Corrente", "Current"),
    "sched.col.breaker": ("Disjuntor", "Breaker"),
    "sched.col.section": ("Secção", "Section"),
    "sched.col.check": ("Verificação", "Check"),
    # clash detection (0.149)
    "discipline.structure": ("Estrutura", "Structure"),
    "discipline.walls": ("Paredes", "Walls"),
    "discipline.services": ("Instalações", "Services"),
    "clash.title": ("Conflitos entre disciplinas", "Clashes between disciplines"),
    "clash.count": ("{n} conflitos", "{n} clashes"),
    "clash.col.n": ("N.º", "No."),
    "clash.col.a": ("Elemento", "Element"),
    "clash.col.b": ("Com", "With"),
    "clash.col.pair": ("Disciplinas", "Disciplines"),
    "clash.col.where": ("Onde (x; y; z)", "Where (x; y; z)"),
    "clash.col.status": ("Estado", "Status"),
    "act.clashes": ("Detetar conflitos…", "Detect clashes…"),
    "tip.clashes": ("Onde as instalações atravessam a estrutura (vigas, pilares, lajes), onde se cruzam entre si e, se "
                    "quiser, onde atravessam paredes: a lista, o estado de cada conflito, notas BCF e um relatório.",
                    "Where the services go through the structure (beams, columns, slabs), where they cross each other "
                    "and, if wanted, where they go through walls: the list, each clash's status, BCF notes and a "
                    "report."),
    "clash.storey_only": ("Só o pavimento ativo", "The active storey only"),
    "clash.search": ("Procurar", "Search"),
    "clash.hint": ("Escolha as disciplinas e carregue em «Procurar».", "Choose the disciplines and press «Search»."),
    "clash.resolved_since": ("{n} resolvidos desde a última procura", "{n} resolved since the last search"),
    "clash.show": ("Ver", "Show"),
    "clash.approve": ("Aprovar", "Approve"),
    "clash.note": ("Criar nota BCF", "Make a BCF note"),
    "clash.report": ("Relatório…", "Report…"),
    "clash.cmd_search": ("Procurar conflitos", "Search for clashes"),
    "clash.cmd_approve": ("Aprovar o conflito", "Approve the clash"),
    "clash.note_title": ("Conflito: {a} × {b}", "Clash: {a} × {b}"),
    "clash.note_text": ("{pair}. Encontrado pelo ArqSynth BIM em {where}.", "{pair}. Found by ArqSynth BIM at {where}."),
    "info.clash_note": ("Nota de coordenação criada (Notas): «{title}».", "Coordination note made (Notes): “{title}”."),
    "info.clash_report": ("Relatório de conflitos gravado: {path}", "Clash report saved: {path}"),
    "clashstatus.new": ("Novo", "New"),
    "clashstatus.active": ("Ativo", "Active"),
    "clashstatus.resolved": ("Resolvido", "Resolved"),
    "clashstatus.approved": ("Aprovado", "Approved"),
    # the water and drainage proposal (0.148)
    "cmd.water_proposal": ("Propor águas e esgotos", "Propose water and drainage"),
    "act.water_proposal": ("Propor águas e esgotos", "Propose water and drainage"),
    "tip.water_proposal": ("Em cada ambiente com louças: um tubo de queda no canto junto à sanita (ou à primeira louça), "
                           "os tubos de água fria e quente ao longo da parede das louças, por cima do teto, e cada louça "
                           "ligada a eles. Tudo marcado como proposta (retira-se de uma vez).",
                           "In each room with fixtures: a stack in the corner by the WC (or the first fixture), the cold "
                           "and hot water pipes along the fixtures' wall, over the ceiling, and every fixture connected "
                           "to them. All tagged as a proposal (taken away at once)."),
    "act.remove_water_proposal": ("Retirar a proposta de águas e esgotos", "Remove the water and drainage proposal"),
    "info.water_proposal": ("Proposta de águas e esgotos: {r} ambientes, {n} tubos e acessórios. Ctrl+Z desfaz.",
                            "Water and drainage proposal: {r} rooms, {n} pipes and fittings. Ctrl+Z undoes."),
    "info.water_none": ("Não há ambientes com louças neste pavimento (ponha as louças dentro de ambientes).",
                        "No rooms with fixtures on this storey (put the fixtures inside rooms)."),
    "info.water_removed": ("Proposta de águas e esgotos retirada: {n} tubos e acessórios.",
                           "Water and drainage proposal removed: {n} pipes and fittings."),
    "info.water_removed_none": ("Não há proposta de águas e esgotos neste pavimento.",
                                "There is no water and drainage proposal on this storey."),
    # the electrical check and quantities (0.147)
    "act.electrical_check": ("Verificar a instalação elétrica…", "Check the electrical installation…"),
    "tip.electrical_check": ("O que falta ou está mal neste pavimento: pontos sem circuito, circuitos sem quadro, sem "
                             "canalização ou que não passam no cálculo, ambientes sem luminária.",
                             "What is missing or wrong on this storey: points in no circuit, circuits with no board, "
                             "no conduits or that do not pass their working out, rooms with no light."),
    "elcheck.title": ("Verificar a instalação elétrica", "Check the electrical installation"),
    "elcheck.again": ("Verificar outra vez", "Check again"),
    "elcheck.ok": ("Nada a apontar neste pavimento.", "Nothing to point out on this storey."),
    "elcheck.found": ("{n} problemas (duplo clique: selecionar o que está em causa):",
                      "{n} problems (double-click: select what it is about):"),
    "elcheck.no_board": ("O pavimento tem pontos elétricos mas nenhum quadro.",
                         "The storey has electrical points but no board."),
    "elcheck.circuit_no_board": ("O circuito {c} não está num quadro.", "Circuit {c} is on no board."),
    "elcheck.circuit_check": ("O circuito {c} não passa: {why}.", "Circuit {c} does not pass: {why}."),
    "elcheck.not_wired": ("O circuito {c} não tem canalização (Instalações ▸ Eletricidade ▸ Ligar ao quadro).",
                          "Circuit {c} has no conduits (Services ▸ Electrical ▸ Wire to board)."),
    "elcheck.loose": ("{n} pontos não estão em nenhum circuito.", "{n} points are in no circuit."),
    "elcheck.room_dark": ("O ambiente «{r}» não tem luminária.", "The room “{r}” has no light."),
    "elqty.circuits": ("Circuitos", "Circuits"),
    "sched.cat.electrical": ("Elétrica: quantidades", "Electrical: quantities"),
    "sched.col.item": ("Elemento", "Item"),
    "sched.col.metres": ("Metros", "Metres"),
    # conduits (0.146)
    "tool.conduit": ("Tubo VD", "Conduit"),
    "cmd.conduit": ("Tubo VD", "Conduit"),
    "elem.conduit": ("Tubo VD", "Conduit"),
    "act.conduit_types": ("Tubo VD", "Conduit"),
    "types.conduits": ("Tubos VD (canalizações elétricas)", "Conduits (electrical)"),
    "info.conduit": ("Tubo VD de {l} criado ({type}, eixo a {h}).", "{l} conduit made ({type}, axis at {h})."),
    "tree.cat.IfcCableCarrierSegment": ("Canalizações", "Conduits"),
    "tree.cat.IfcCableCarrierFitting": ("Curvas de canalização", "Conduit bends"),
    "cmd.route_circuits": ("Ligar ao quadro", "Wire to the board"),
    "act.route_circuits": ("Ligar ao quadro (canalizações)", "Wire to the board (conduits)"),
    "tip.route_circuits": ("Os circuitos do pavimento ainda sem canalização ganham os seus tubos VD: do quadro a cada "
                           "ponto, um a seguir ao outro (o mais próximo), a subir a parede até 2,75 m, por cima do teto, "
                           "e a descer até ao ponto seguinte.",
                           "The storey's circuits with no conduits yet get them: from the board to each point in turn "
                           "(the nearest), up the wall to 2.75 m, over the ceiling, and down to the next point."),
    "info.routed": ("Circuitos ligados ao quadro: {n}, com {l} de tubo VD. Veja o quadro de cargas.",
                    "Circuits wired to the board: {n}, with {l} of conduit. See the load schedule."),
    "info.route_none": ("Não há circuitos sem canalização neste pavimento (faça primeiro os circuitos).",
                        "No circuits without conduits on this storey (make the circuits first)."),
    "sched.col.conduit": ("Tubo VD", "Conduit"),
    # the electrical points proposed for the rooms (0.145)
    "cmd.electrical_proposal": ("Propor pontos elétricos", "Propose electrical points"),
    "act.electrical_proposal": ("Propor pontos elétricos…", "Propose electrical points…"),
    "tip.electrical_proposal": ("Para os ambientes do pavimento: pela função de cada um (pelo nome: Quarto, Sala, "
                                "Cozinha, WC, Corredor…), as luminárias no teto, um interruptor junto a cada porta e as "
                                "tomadas "
                                "pelas paredes — veja-as antes, mude as quantidades e aplique.",
                                "For the storey's rooms: by each one's use (its name: Bedroom, Living, Kitchen, WC, "
                                "Corridor…), the lights on the ceiling, a switch by each door, the outlets along the "
                                "walls — see them first, change the numbers and apply."),
    "act.remove_electrical_proposal": ("Retirar a proposta elétrica", "Remove the electrical proposal"),
    "tip.remove_electrical_proposal": ("Apaga os pontos e as luminárias que a proposta elétrica pôs neste pavimento.",
                                       "Deletes the points and lights the electrical proposal put on this storey."),
    "elprop.title": ("Propor pontos elétricos", "Propose electrical points"),
    "elprop.intro": ("Cada ambiente tem um perfil (pelo nome). Mude o perfil ou as quantidades, veja na planta com "
                     "«Pré-visualizar» e faça-os com «Aplicar». Os pontos ficam marcados como proposta e retiram-se "
                     "todos de uma vez (Instalações ▸ Eletricidade ▸ Tirar a proposta).",
                     "Each room has a profile (from its name). Change the profile or the numbers, see them on the plan "
                     "with «Preview» and make them with «Apply». They are tagged as a proposal and taken away all at "
                     "once (Services ▸ Electrical ▸ Remove proposal)."),
    "elprop.room": ("Ambiente", "Room"),
    "elprop.profile": ("Perfil", "Profile"),
    "elprop.preview": ("Pré-visualizar", "Preview"),
    "elprop.apply": ("Aplicar", "Apply"),
    "elprop.close": ("Fechar", "Close"),
    "elprop.none": ("Este pavimento não tem ambientes: faça-os primeiro (ferramenta Ambiente).",
                    "This storey has no rooms: make them first (Room tool)."),
    "profile.bedroom": ("Quarto", "Bedroom"),
    "profile.living": ("Sala", "Living room"),
    "profile.kitchen": ("Cozinha", "Kitchen"),
    "profile.bathroom": ("Instalação sanitária", "Bathroom"),
    "profile.corridor": ("Corredor / entrada", "Corridor / hall"),
    "profile.office": ("Escritório", "Office"),
    "profile.other": ("Outra", "Other"),
    "profile.none": ("Nenhum", "None"),
    "elcount.light": ("Luminárias", "Lights"),
    "elcount.switch": ("Interruptores", "Switches"),
    "elcount.outlet": ("Tomadas", "Outlets"),
    "elcount.data_outlet": ("Dados", "Data"),
    "elcount.outlet_counter": ("Bancada", "Counter"),
    "info.electrical_proposal": ("Proposta elétrica: {n} pontos e luminárias em {r} ambientes. Ctrl+Z desfaz.",
                                 "Electrical proposal: {n} points and lights in {r} rooms. Ctrl+Z undoes."),
    "info.electrical_removed": ("Proposta elétrica retirada: {n} pontos e luminárias.",
                                "Electrical proposal removed: {n} points and lights."),
    "info.electrical_removed_none": ("Não há proposta elétrica neste pavimento.",
                                     "There is no electrical proposal on this storey."),
    # connect to the network (0.142)
    "cmd.connect_network": ("Ligar à rede", "Connect to the network"),
    "act.connect_network": ("Ligar à rede", "Connect to the network"),
    "tip.connect_network": ("Cada ligação livre das louças selecionadas (nenhuma: todas as do pavimento) leva um "
                            "ramal até ao tubo mais próximo do seu sistema: o esgoto desce e vai a 2 % até ao coletor "
                            "ou ao tubo de queda; a água fria e a quente vêm dos seus tubos. Um tê em cada ligação.",
                            "Each free outlet of the selected fixtures (none: all of the storey) gets a branch to the "
                            "nearest pipe of its system: the drain goes down and at 2 % to the collector or the stack; "
                            "cold and hot water come from their pipes. A tee at each join."),
    "info.connected_network": ("Ligado à rede: {n} ramais.", "Connected to the network: {n} branches."),
    "info.connected_missing": ("Sem rede para: {what} (desenhe primeiro o tubo desse sistema).",
                               "No network for: {what} (draw that system's pipe first)."),
    "info.connect_none": ("Não há louças para ligar: selecione louças sanitárias (ou ponha-as no pavimento).",
                          "No fixtures to connect: select sanitary fixtures (or put them on the storey)."),
    "info.system_drain": ("{s}: os tubos descem {p} no sentido do desenho (mude a inclinação na barra).",
                          "{s}: the pipes fall {p} the way they are drawn (change the slope on the bar)."),
    "info.system_from_port": ("Começa em «{name}»: fica no sistema {s}.", "It starts on “{name}”: it is in the {s} "
                                                                           "system."),
    "warn.system_port": ("{done} Atenção: a ligação é de {port}, o tubo é de {s}.",
                         "{done} Note: the connection is for {port}, the pipe for {s}."),
    # drawing in the views (0.120)
    "tool.draft": ("Desenho 2D", "2D drawing"),
    "cmd.draft": ("Desenho 2D", "2D drawing"),
    "cmd.draft_delete": ("Apagar desenho 2D", "Delete 2D drawing"),
    # (0.191) a drawing changed: its points by their grips, its words, size, angle, hatch, line in the Properties
    "cmd.draft_edit": ("Mudar desenho 2D", "Change 2D drawing"),
    "hint.ann_grip": ("Leve o ponto para onde quer e clique (ou escreva a distância e Enter). Esc deixa-o.",
                      "Take the point where you want it and click (or type the distance and Enter). Esc leaves it."),
    "info.ann_grip": ("Ponto movido {d}. Ctrl+Z desfaz.", "Point moved {d}. Ctrl+Z undoes it."),
    "info.ann_edit": ("{k} mudado. Ctrl+Z desfaz.", "{k} changed. Ctrl+Z undoes it."),
    "props.anns": ("{n} desenhos 2D", "{n} 2D drawings"),
    "props.ann_sub": ("Desenho 2D (só nesta vista)", "2D drawing (in this view only)"),
    "props.g.drawing": ("Desenho", "Drawing"),
    "props.ann_text": ("Texto", "Text"),
    "props.ann_angle": ("Ângulo", "Angle"),
    "props.ann_hint": ("Arraste as pegas azuis para mudar os pontos. O Mover e o Rodar (numa planta) também "
                       "servem. Delete apaga.",
                       "Drag the blue grips to change its points. Move and Rotate (in a plan) work too. Delete "
                       "removes it."),
    "ctx.draft_shape": ("Desenhar", "Draw"),
    "ctx.draft_hatch": ("Trama", "Hatch"),
    "ctx.text_size": ("Altura do texto", "Text height"),
    "draft.line": ("Linha", "Line"),
    "draft.polyline": ("Polilinha", "Polyline"),
    "draft.rectangle": ("Retângulo", "Rectangle"),
    "draft.circle": ("Círculo", "Circle"),
    "draft.arc": ("Arco", "Arc"),
    "draft.region": ("Região com trama", "Hatched region"),
    "draft.text": ("Texto", "Text"),
    "drafthatch.diagonal": ("Diagonal (45°)", "Diagonal (45°)"),
    "drafthatch.cross": ("Cruzada", "Crossed"),
    "drafthatch.solid": ("Cheia (cinzento)", "Solid (grey)"),
    "drafthatch.none": ("Sem trama", "No hatch"),
    # (0.450) Revit's masking region; the drawing tools side by side on the contextual bar, as Revit's «Draw» panel
    "drafthatch.mask": ("Máscara (branca, esconde o que está por baixo)", "Mask (white, hides what is under it)"),
    "draft.mask": ("Máscara (esconde o que está por baixo)", "Masking region (hides what is under it)"),
    "draft.fillet": ("Arco de concordância (canto de região, máscara, polilinha, retângulo, ou 2 linhas)",
                     "Fillet arc (a region's, mask's, polyline's, rectangle's corner, or 2 lines)"),
    "hint.draft.fillet_0": ("Arco de concordância: clique num lado de uma região, máscara, polilinha ou retângulo — "
                            "ou numa linha (do lado que fica).",
                            "Fillet arc: click a side of a region, mask, polyline or rectangle — or a line (on the "
                            "side that stays)."),
    "hint.draft.fillet_1": ("Arco de concordância: clique no lado que faz o canto com o primeiro — ou na 2.ª linha.",
                            "Fillet arc: click the side making the corner with the first — or the 2nd line."),
    "hint.draft.fillet_2": ("Arco de concordância: mova o rato para o raio e clique, ou escreva o raio e Enter. Esc "
                            "recomeça.", "Fillet arc: move the mouse for the radius and click, or type the radius and "
                            "Enter. Esc starts again."),
    "tip.fillet_drawn": ("Escolha o {n}.º lado (ou linha) do desenho", "Pick the drawing's side (or line) {n}"),
    "info.fillet_drawn": ("Canto arredondado com raio {r} (um arco verdadeiro: acompanha quando se move ou roda). "
                          "Ctrl+Z desfaz.", "Corner rounded with radius {r} (a true arc: it follows when moved or "
                          "turned). Ctrl+Z undoes."),
    "ctx.draw": ("Desenhar", "Draw"),
    "draw.line": ("Linha", "Line"),
    "draw.line_arc": ("Linha com arcos (Tab)", "Line with arcs (Tab)"),
    "draw.rectangle": ("Retângulo", "Rectangle"),
    "draw.circle": ("Círculo", "Circle"),
    "draw.arc": ("Arco", "Arc"),
    "draw.bezier": ("Curva de Bézier", "Bézier curve"),
    # (0.458) Revit's polygons and ellipses, on the Line's row too
    "draw.poly_in": ("Polígono inscrito (os cantos no círculo)", "Inscribed polygon (its corners on the circle)"),
    "draw.poly_out": ("Polígono circunscrito (os lados tocam o círculo)",
                      "Circumscribed polygon (its sides touch the circle)"),
    "draw.ellipse": ("Elipse", "Ellipse"),
    "draw.ellipse_part": ("Elipse parcial (meia elipse)", "Partial ellipse (half an ellipse)"),
    "draw.freehand": ("Linha livre (à mão)", "Freehand line"),
    "draw.pick": ("Escolher linhas (sobre uma linha ou aresta)", "Pick lines (on a line or an edge)"),   # (0.451)
    "hint.line.pick": ("Escolher linhas: clique numa linha, aresta, face de parede, eixo da grelha ou linha de um "
                       "desenho — uma linha fica sobre ela, do lado do rato, com o Afastamento da barra.",
                       "Pick lines: click a line, an edge, a wall's face, a grid axis or a drawing's line — a line "
                       "lies on it, on the mouse's side, at the bar's Offset."),
    "info.line_on_picked": ("Linha de {l} sobre a escolhida. Clique noutra, ou Esc. Ctrl+Z desfaz.",
                            "A {l} line on the one picked. Click another one, or Esc. Ctrl+Z undoes."),
    "vcb.text": ("Texto", "Text"),
    "hint.draft_view": ("Desenho 2D: abra uma planta, um corte ou um alçado — o desenho fica nessa vista.",
                        "2D drawing: open a plan, a section or an elevation — the drawing stays in that view."),
    "hint.draft.line": ("Linha: clique no início. (Tab muda o que desenha.)",
                        "Line: click its start. (Tab changes what is drawn.)"),
    "hint.draft.end_line": ("Clique no fim da linha, ou escreva o comprimento e Enter.",
                            "Click the line's end, or type its length and Enter."),
    "hint.draft.polyline": ("Polilinha: clique no primeiro ponto. (Tab muda o que desenha.)",
                            "Polyline: click its first point. (Tab changes what is drawn.)"),
    "hint.draft.more": ("Clique no ponto seguinte; Enter acaba (um clique no primeiro ponto fecha). Delete tira o "
                        "último.",
                        "Click the next point; Enter ends it (a click on the first point closes it). Delete takes "
                        "the last one back."),
    "hint.draft.rectangle": ("Retângulo: clique num canto. (Tab muda o que desenha.)",
                             "Rectangle: click a corner. (Tab changes what is drawn.)"),
    "hint.draft.end_rectangle": ("Clique no canto oposto, ou escreva «largura;altura» e Enter.",
                                 "Click the opposite corner, or type “width;height” and Enter."),
    "hint.draft.circle": ("Círculo: clique no centro. (Tab muda o que desenha.)",
                          "Circle: click its centre. (Tab changes what is drawn.)"),
    "hint.draft.end_circle": ("Clique num ponto do círculo, ou escreva o raio e Enter.",
                              "Click a point on the circle, or type its radius and Enter."),
    "hint.draft.arc": ("Arco: clique no início. (Tab muda o que desenha.)",
                       "Arc: click its start. (Tab changes what is drawn.)"),
    "hint.draft.end_arc": ("Clique no fim do arco.", "Click the arc's end."),
    "hint.draft.arc_3": ("Clique num ponto por onde o arco passa.", "Click a point the arc passes through."),
    "hint.draft.region": ("Região com trama: clique no primeiro canto. (Tab muda o que desenha.)",
                          "Hatched region: click its first corner. (Tab changes what is drawn.)"),
    "hint.draft.text": ("Texto: clique onde começa. (Tab muda o que desenha.)",
                        "Text: click where it starts. (Tab changes what is drawn.)"),
    "hint.draft.text_2": ("Escreva o texto e Enter (Esc desiste).", "Type the text and Enter (Esc gives up)."),
    "draft.spot": ("Cota de nível", "Spot height"),
    "hint.draft.spot": ("Cota de nível: clique no ponto. Numa planta escreve a altura do que está por baixo (terreno, "
                        "laje, degrau), e acompanha o modelo. (Tab muda o que desenha.)",
                        "Spot height: click the point. In a plan it writes the height of what is under it (terrain, "
                        "slab, step), and follows the model. (Tab changes what is drawn.)"),
    "draft.level": ("Marca de nível", "Level mark"),
    # (0.194) keynotes
    "draft.keynote": ("Nota-chave", "Keynote"),
    "hint.draft.keynote": ("Nota-chave: clique no elemento (uma parede, uma laje…). (Tab muda o que desenha.)",
                           "Keynote: click the element (a wall, a slab…). (Tab changes what is drawn.)"),
    "hint.draft.end_keynote": ("Clique onde fica a etiqueta: escreve o código da nota-chave do elemento.",
                               "Click where the tag goes: it writes the element's keynote code."),
    "err.keynote_element": ("A nota-chave aponta para um elemento: clique numa parede, laje, porta…",
                            "A keynote points at an element: click a wall, slab, door…"),
    "hint.draft.level": ("Marca de nível: clique no ponto. O símbolo (círculo com dois quartos pretos) e a cota do "
                         "que está por baixo, sempre a do modelo. (Tab muda o que desenha.)",
                         "Level mark: click the point. The symbol (a circle with two black quarters) and the height "
                         "of what is under it, always the model's. (Tab changes what is drawn.)"),
    "keys.draft": ("Tab: linha → polilinha → retângulo → círculo → arco → região → texto → cota de nível → marca de "
                   "nível  ·  Enter: acabar  ·  Delete: tirar o último ponto  ·  Esc: recomeçar",
                   "Tab: line → polyline → rectangle → circle → arc → region → text → spot height → level mark  ·  "
                   "Enter: end  ·  Delete: take the last point back  ·  Esc: start again"),
    "info.draft": ("{k} na vista. Ctrl+Z desfaz.", "{k} in the view. Ctrl+Z undoes."),
    "info.draft_shape": ("A desenhar: {k}.", "Drawing: {k}."),
    "info.annotation_selected": ("Selecionado: {k}. Arraste as pegas para o mudar; Delete apaga.",
                                 "Selected: {k}. Drag its grips to change it; Delete removes it."),
    # dimensions in a chain, angular (0.122)
    "ctx.dim_kind": ("Cota", "Dimension"),
    "ctx.dim_chain": ("Continuar a cadeia", "Go on with the string"),
    # (0.399) the one-click dimensions and what is taken on the walls (Revit's «Preferência»)
    "ctx.dim_ref": ("Nas paredes", "On the walls"),
    "dimref.faces": ("Faces de acabamento", "Finish faces"),
    "dimref.core_faces": ("Faces do núcleo (em osso)", "Core faces"),
    "dimref.axis": ("Eixos das paredes", "Wall axes"),
    "dimref.core_axis": ("Eixo do núcleo", "Core axis"),
    "ctx.dim_openings": ("Vãos", "Openings"),
    "dimopen.jambs": ("Ombreiras", "Jambs"),
    "dimopen.centres": ("Eixos dos vãos", "Their middles"),
    "dimopen.none": ("Não cotar", "Not dimensioned"),
    "ctx.dim_row_walls": ("Paredes interiores", "Inner walls"),
    "ctx.dim_row_corners": ("Cantos", "Corners"),
    "ctx.dim_row_overall": ("Total", "Overall"),
    "ctx.dim_which": ("Fachadas", "Sides"),
    "dimwhich.all": ("Todas", "All"),
    "dimwhich.near": ("A mais perto do rato", "The one nearest the mouse"),
    "hint.auto_dims.view": ("Abra a planta do pavimento (F4): as cotas automáticas fazem-se na planta.",
                            "Open the storey's plan (F4): the automatic dimensions are made in a plan."),
    "hint.dim_exterior": ("Cotas exteriores: a azul, as que vão ficar à volta do edifício — um clique na planta "
                          "pousa-as (outra vez: refaz). Na barra: o que se cota nas paredes, os vãos, as filas.",
                          "Outside dimensions: in blue, those that will go round the building — a click in the plan "
                          "places them (again: made again). On the bar: what is taken on the walls, the openings, "
                          "the rows."),
    "hint.dim_exterior.near": ("Cotas exteriores: aproxime o rato de uma fachada (a azul, as dela) e clique para as "
                               "pousar.",
                               "Outside dimensions: bring the mouse near a side (in blue, its own) and click to "
                               "place them."),
    "cmd.dim_exterior": ("Cotas exteriores", "Outside dimensions"),
    "info.dim_exterior": ("{d} cotas exteriores em {n} fachada(s). Ctrl+Z desfaz; mude as opções na barra e clique "
                          "outra vez para as refazer.",
                          "{d} outside dimensions on {n} side(s). Ctrl+Z undoes; change the settings on the bar and "
                          "click again to make them again."),
    # (0.400) inside
    "ctx.dim_mode": ("Cotar", "Dimension"),
    "dimmode.size": ("Largura e profundidade", "Width and depth"),
    "dimmode.run": ("Corrida (através do edifício)", "A run (across the building)"),
    "dimmode.walls": ("Ao longo das paredes, com os vãos", "Along its walls, with the openings"),
    "ctx.dim_directions": ("Direção", "Direction"),
    "dimdir.both": ("As duas", "Both"),
    "dimdir.width": ("Só a largura", "Width only"),
    "dimdir.depth": ("Só a profundidade", "Depth only"),
    "ctx.dim_rooms": ("Compartimentos", "Rooms"),
    "dimrooms.one": ("O do clique", "The one clicked"),
    "dimrooms.all": ("Todos os do pavimento", "All on the storey"),
    "hint.dim_interior.size": ("Cotas interiores: clique dentro de um compartimento — a largura e a profundidade, de "
                               "parede a parede, passam pelo ponto do clique e alinham-se com a parede mais perto do "
                               "rato (a azul, antes de clicar). Ctrl+clique acrescenta outras sem tirar as que já pôs.",
                               "Inside dimensions: click inside a room — its width and depth, wall to wall, go through "
                               "the point clicked, square to the wall nearest the mouse (in blue, before clicking). "
                               "Ctrl+click adds more, keeping those already placed."),
    "hint.dim_interior.run": ("Cota corrida: clique dentro de um compartimento — a linha atravessa o edifício pelo "
                              "ponto do clique, com cada compartimento e cada espessura de parede.",
                              "A run: click inside a room — the line goes right across the building through the point "
                              "clicked, each room and each wall's thickness on the way."),
    "hint.dim_interior.walls": ("Cotas interiores ao longo das paredes: clique num compartimento — cada parede dele "
                                "cotada por dentro, com os vãos e as paredes que lhe chegam.",
                                "Inside dimensions along the walls: click in a room — each of its walls dimensioned "
                                "inside, with its openings and the walls that reach it."),
    "hint.dim_interior.all": ("Cotas interiores de todos os compartimentos: clique na planta.",
                              "Inside dimensions of every room: click in the plan."),
    "cmd.dim_interior": ("Cotas interiores", "Inside dimensions"),
    "info.dim_interior": ("{d} cotas interiores em {n} compartimento(s). Ctrl+Z desfaz.",
                          "{d} inside dimensions in {n} room(s). Ctrl+Z undoes."),
    "info.dim_interior_outside": ("Clique dentro de um compartimento fechado por paredes.",
                                  "Click inside a room closed by walls."),
    "info.dim_interior_none": ("Não encontrei paredes para cotar a partir deste ponto.",
                               "No walls found to dimension from this point."),
    "info.no_rooms_walls": ("Não há compartimentos fechados por paredes neste pavimento: desenhe as paredes primeiro.",
                            "There are no rooms closed by walls on this storey: draw the walls first."),
    "tip.dim_interior": ("Cotas interiores: um clique num compartimento — largura e profundidade, cota corrida "
                         "através do edifício, ou ao longo das paredes com os vãos — com ou sem Ambiente.",
                         "Inside dimensions: one click in a room — width and depth, a run across the building, or "
                         "along its walls with the openings — with a Room or without."),
    "tip.dim_exterior": ("Cotas exteriores: um clique na planta e o edifício fica cotado à volta — vãos, paredes "
                         "interiores, cantos e total — por faces de acabamento, faces do núcleo ou eixos.",
                         "Outside dimensions: one click in the plan and the building is dimensioned round — openings, "
                         "inner walls, corners and overall — by finish faces, core faces or axes."),
    "dimkind.linear": ("Linear (horizontal / vertical)", "Linear (level / upright)"),
    "dimkind.angular": ("Angular", "Angular"),
    "dimkind.aligned": ("Alinhada", "Aligned"),
    # (0.401) the manual dimension as Revit's
    "ctx.dim_pick": ("Escolher", "Pick"),
    "dimpick.single": ("Referências individuais", "Individual references"),
    "dimpick.walls": ("Paredes inteiras", "Entire walls"),
    "dimref.point": ("Ponto", "Point"),
    "dimref.kind.face_lo": ("Face de acabamento", "Finish face"),
    "dimref.kind.face_hi": ("Face de acabamento", "Finish face"),
    "dimref.kind.core_lo": ("Face do núcleo", "Core face"),
    "dimref.kind.core_hi": ("Face do núcleo", "Core face"),
    "dimref.kind.axis": ("Eixo da parede", "Wall axis"),
    "dimref.kind.core_axis": ("Eixo do núcleo", "Core axis"),
    "dimref.jamb": ("Ombreira", "Jamb"),
    "dimref.opening_axis": ("Eixo do vão", "Opening's middle"),
    "dimref.grid": ("Eixo estrutural {g}", "Grid axis {g}"),
    "info.dim_refs": ("{n} referências: clique em mais, ou num sítio vazio para pousar.",
                      "{n} references: click more, or an empty place to put them."),
    "info.dimension_string": ("Cadeia de {n} cotas ({v} no total). Esc termina; Ctrl+Z desfaz.",
                              "A string of {n} dimensions ({v} in all). Esc ends; Ctrl+Z undoes."),
    "info.dim_kind": ("Cota {k}.", "{k} dimension."),
    "hint.dimension.add_refs": ("Acrescentar referências: clique nas referências a juntar à cadeia e depois num sítio "
                                "vazio para a pousar outra vez.",
                                "Add references: click the references to add to the string, then an empty place to "
                                "put it back."),
    # (0.402) dimension strings edited as Revit's
    "act.dim_eq": ("IG — igualar", "EQ — make equal"),
    "act.dim_eq_off": ("Tirar o IG", "EQ off"),
    "act.dim_text": ("Texto da cota…", "Dimension text…"),
    "act.dim_add": ("Acrescentar referências", "Add references"),
    "act.dim_witness": ("Apagar linha de chamada", "Delete witness line"),
    "act.dim_text_back": ("Repor os valores no sítio", "Put the values back in place"),
    "tip.dim_eq": ("IG: as cotas da cadeia ficam iguais — as paredes, portas e janelas do meio movem-se — e escrevem "
                   "«IG». Outra vez: os valores voltam.",
                   "EQ: the string's pieces made equal — the walls, doors and windows in its middle move — writing "
                   "\"EQ\". Again: the values back."),
    "tip.dim_text": ("Texto da cota (ou duplo clique no valor): mudar o valor (move o elemento), substituir pelo texto, "
                     "prefixo, sufixo, texto por cima e por baixo.",
                     "Dimension text (or a double click on the value): change the value (moves the element), a text "
                     "over it, prefix, suffix, words over and under."),
    "tip.dim_add": ("Acrescentar referências à cadeia: clique nelas e depois num sítio vazio.",
                    "Add references to the string: click them, then an empty place."),
    "tip.dim_witness": ("Botão direito numa linha de chamada (o quadrado dela): tirá-la — as duas cotas vizinhas "
                        "passam a uma.",
                        "Right click on a witness line (its square): take it away — the two pieces beside it become "
                        "one."),
    "ctx.dims_selected": ("{n} cota(s) escolhida(s):", "{n} dimension(s) chosen:"),
    "hint.dim_chosen": ("Cadeia de cotas: arraste o losango da linha para a afastar, o losango de um valor para o mudar "
                        "de sítio, o quadrado de uma linha de chamada para outra referência; botão direito: IG, "
                        "apagar a linha de chamada; duplo clique num valor: o texto.",
                        "Dimension string: drag the line's diamond to move it off, a value's diamond to move the "
                        "value, a witness line's square to another reference; right button: EQ, delete the witness "
                        "line; double click a value: its text."),
    "hint.dim_grip_line": ("Leve a linha da cadeia para onde a quer e clique (ou largue).",
                           "Take the string's line where you want it and click (or let go)."),
    "hint.dim_grip_text": ("Leve o valor para onde o quer e clique (ou largue).",
                           "Take the value where you want it and click (or let go)."),
    "hint.dim_grip_witness": ("Leve a linha de chamada a outra referência (acende-se a laranja) e clique.",
                              "Take the witness line to another reference (lit in orange) and click."),
    "cmd.dim_move_line": ("Mover a linha das cotas", "Move the dimensions' line"),
    "cmd.dim_move_text": ("Mover o valor da cota", "Move the dimension's value"),
    "cmd.dim_move_witness": ("Mudar a linha de chamada", "Move the witness line"),
    "cmd.dim_witness": ("Apagar linha de chamada", "Delete witness line"),
    "cmd.dim_eq": ("Igualar (IG)", "Make equal (EQ)"),
    "cmd.dim_eq_off": ("Tirar o IG", "EQ off"),
    "cmd.dim_text": ("Texto da cota", "Dimension text"),
    "cmd.dim_value": ("Valor da cota", "Dimension value"),
    "info.dim_line_moved": ("Linha das cotas movida. Ctrl+Z desfaz.", "The dimensions' line moved. Ctrl+Z undoes."),
    "info.dim_text_moved": ("Valor mudado de sítio (botão direito ▸ Repor os valores no sítio). Ctrl+Z desfaz.",
                            "Value moved (right button ▸ Put the values back in place). Ctrl+Z undoes."),
    "info.dim_witness_moved": ("Linha de chamada levada para: {w}. Ctrl+Z desfaz.",
                               "Witness line taken to: {w}. Ctrl+Z undoes."),
    "info.dim_witness_removed": ("Linha de chamada apagada: as duas cotas vizinhas são agora uma. Ctrl+Z desfaz.",
                                 "Witness line deleted: the two pieces beside it are one now. Ctrl+Z undoes."),
    "info.dim_witness_last": ("Uma cota sozinha não perde linhas de chamada (apague-a com Delete).",
                              "A dimension alone keeps its witness lines (Delete removes it)."),
    "info.dim_witness_pick": ("Clique com o botão direito no quadrado da linha de chamada a apagar.",
                              "Right-click the square of the witness line to delete."),
    "info.dim_pick": ("Escolha primeiro uma cota (Selecionar, clique na linha ou no valor).",
                      "Choose a dimension first (Select, click its line or value)."),
    "info.dim_eq": ("{n} cotas iguais (IG); {m} elemento(s) movido(s). Ctrl+Z desfaz.",
                    "{n} dimensions made equal (EQ); {m} element(s) moved. Ctrl+Z undoes."),
    "info.dim_eq_off": ("Os valores voltam a ver-se.", "The values are written again."),
    "info.dim_value": ("Cota com {v}: {e} movido. Ctrl+Z desfaz.", "Dimension made {v}: {e} moved. Ctrl+Z undoes."),
    "info.dim_value_none": ("Não há elemento que se possa mover nas pontas desta cota.",
                            "There is no element at this dimension's ends that can move."),
    # (0.405) a dimension in the Properties panel, as Revit's; its values and lines dragged with alignments
    "props.g.dim_type": ("Tipo de cota", "Dimension type"),
    "props.g.dim_values": ("Cota", "Dimension"),
    "props.g.dim_text": ("Texto", "Text"),
    "props.dim_edit_type_tip": ("A aparência deste tipo de cota (marcas, linhas, texto, unidades) — muda todas as cotas "
                                "deste tipo.",
                                "How this dimension type looks (marks, lines, text, units) — every dimension of the "
                                "type changes."),
    "props.dim_string": ("Cadeia", "String"),
    "props.dim_string_n": ("{n} cotas, {v} no total", "{n} dimensions, {v} in all"),
    "props.dim_eq": ("IG (iguais)", "EQ (equal)"),
    "props.dim_override": ("Substituir pelo texto", "Replace with text"),
    "props.dim_prefix": ("Prefixo", "Prefix"),
    "props.dim_suffix": ("Sufixo", "Suffix"),
    "props.dim_above": ("Texto por cima", "Text above"),
    "props.dim_below": ("Texto por baixo", "Text below"),
    "props.dim_shifted": ("Valores mudados de sítio", "Values moved"),
    "props.dim_text_window": ("Texto da cota", "Dimension text"),
    "props.dim_open": ("Abrir…", "Open…"),
    "props.dim_refs": ("Referências", "References"),
    "props.dim_add": ("Acrescentar…", "Add…"),
    "snap.dim_value": ("Alinhado", "Aligned"),
    "snap.dim_line": ("Alinhada com outra cota", "In line with another dimension"),
    "dimtext.title": ("Texto da cota", "Dimension text"),
    "dimtext.value": ("Valor", "Value"),
    "dimtext.moving": ("Ao mudar o valor, move", "Changing the value moves"),
    "dimtext.real": ("Usar o valor real", "Use the actual value"),
    "dimtext.override": ("Substituir pelo texto:", "Replace with text:"),
    "dimtext.prefix": ("Prefixo", "Prefix"),
    "dimtext.suffix": ("Sufixo", "Suffix"),
    "dimtext.above": ("Por cima", "Above"),
    "dimtext.below": ("Por baixo", "Below"),
    "dimtext.whole": ("Aplicar às {n} cotas da cadeia", "Apply to the string's {n} dimensions"),
    "dimtext.value_title": ("Valor da cota", "Dimension value"),
    "dimtext.value_of": ("Novo valor (move «{e}»):", "New value (moves \"{e}\"):"),
    "hint.dimension.chain": ("Clique no ponto seguinte da cadeia: uma cota dele ao último, na mesma linha (Esc "
                             "acaba).",
                             "Click the chain's next point: a dimension from the last one to it, on the same line "
                             "(Esc ends it)."),
    "hint.dimension.angle_0": ("Cota angular: clique no vértice do ângulo. (Tab: alinhada.)",
                               "Angular dimension: click the angle's corner. (Tab: aligned.)"),
    "hint.dimension.angle_1": ("Clique num ponto do primeiro lado.", "Click a point on the first side."),
    "hint.dimension.angle_2": ("Clique num ponto do segundo lado.", "Click a point on the second side."),
    "hint.dimension.angle_3": ("Clique onde fica o arco — o ângulo é o desse lado.",
                               "Click where the arc goes — the angle is the one on that side."),
    "info.dimension_chain": ("Mais uma cota na cadeia: {v}. Esc acaba.", "One more in the chain: {v}. Esc ends it."),
    "info.dimension_angle": ("Cota angular de {v}. Clique para outra; Esc termina.",
                             "Angular dimension of {v}. Click for another; Esc ends."),
    "info.dimension_placed_chain": ("Cota de {v}. Clique no ponto seguinte da cadeia; Esc termina.",
                                    "Dimension of {v}. Click the chain's next point; Esc ends."),
    "err.dimension_angle": ("Os dois lados são paralelos, ou o arco está no vértice: não há ângulo.",
                            "The two sides are parallel, or the arc is on the corner: there is no angle."),
    # dimensions of the façades and the rooms (0.123)
    "act.dimension_facades": ("Cotar fachadas", "Dimension the façades"),
    "act.dimension_rooms": ("Cotar ambientes", "Dimension the rooms"),
    "tip.dimension_facades": ("Cotar fachadas: à volta do edifício, em cada lado, os cantos e os vãos, os cantos e "
                              "o comprimento total (outra vez: refaz)",
                              "Dimension the façades: round the building, on each side, its corners and openings, "
                              "its corners and its whole length (again: made again)"),
    "tip.dimension_rooms": ("Cotar ambientes: a largura e a profundidade de cada ambiente, de parede a parede (outra vez: "
                            "refaz)",
                            "Dimension the rooms: each room's width and depth, from wall to wall (again: made "
                            "again)"),
    "cmd.dimension_facade": ("Cotar fachadas", "Dimension the façades"),
    "cmd.dimension_room": ("Cotar ambientes", "Dimension the rooms"),
    "info.dimensioned_facade": ("{d} cotas nas fachadas da planta de {name}. Ctrl+Z desfaz.",
                                "{d} dimensions on the façades of the plan of {name}. Ctrl+Z undoes."),
    "info.dimensioned_room": ("{d} cotas nos ambientes da planta de {name}. Ctrl+Z desfaz.",
                              "{d} dimensions in the rooms of the plan of {name}. Ctrl+Z undoes."),
    "info.no_rooms_dims": ("Não há ambientes neste pavimento: faça-os primeiro (ferramenta Ambiente).",
                           "There are no rooms on this storey: make them first (Room tool)."),
    # the dimension style (0.124)
    "act.dimension_style": ("Tipos de cota…", "Dimension types…"),
    "cmd.dimension_style": ("Tipos de cota", "Dimension types"),
    "dimstyle.title": ("Tipos de cota", "Dimension types"),
    # (0.398) the dimension types' editor: every property, as Revit's Type Properties of a dimension
    "tip.dimension_style": ("Tipos de cota: a aparência das cotas — marcas, linhas, linhas de chamada, texto, unidades "
                            "(milímetros em expoente, arredondamento), altura dos vãos — com uma amostra em papel; "
                            "duplicar, mudar o nome, apagar.",
                            "Dimension types: how the dimensions look — marks, lines, extension lines, text, units "
                            "(raised millimetres, rounding), the openings' heights — with a sample on paper; "
                            "duplicate, rename, delete."),
    "dimtype.list": ("Tipos do projeto", "The project's types"),
    "dimtype.duplicate": ("Duplicar…", "Duplicate…"),
    "dimtype.rename": ("Mudar o nome…", "Rename…"),
    "dimtype.name": ("Nome do tipo:", "The type's name:"),
    "dimtype.exists": ("Já há um tipo «{n}».", "There is already a type \"{n}\"."),
    "dimtype.copy_of": ("{n} (cópia)", "{n} (copy)"),
    "dimtype.preset": ("Começar de:", "Start from:"),
    "dimtype.preset.choose": ("— um aspeto habitual —", "— a usual look —"),
    "dimtype.preset.architecture": ("Arquitetura — traço oblíquo", "Architecture — oblique tick"),
    "dimtype.preset.heavy": ("Traço grosso (como o Revit)", "Heavy tick (as Revit's)"),
    "dimtype.preset.engineering": ("Engenharia — setas cheias", "Engineering — filled arrows"),
    "dimtype.preset.raised": ("Metros com milímetros em expoente", "Metres with raised millimetres"),
    "dimtype.preset.centimetres": ("Centímetros com pontos", "Centimetres with dots"),
    "dimstyle.g.graphics": ("Gráficos", "Graphics"),
    "dimstyle.g.witness": ("Linhas de chamada", "Extension lines"),
    "dimstyle.g.text": ("Texto", "Text"),
    "dimstyle.g.units": ("Unidades e valores", "Units and values"),
    "dimstyle.g.openings": ("Vãos e cotas iguais", "Openings and equal dimensions"),
    "dimstyle.mark_size": ("Tamanho da marca", "Mark size"),
    "dimstyle.mark_pen": ("Espessura da marca", "Mark pen"),
    "dimstyle.pen": ("Espessura da linha de cota", "Dimension line pen"),
    "dimstyle.colour": ("Cor", "Colour"),
    "dimstyle.line_over": ("Prolongamento da linha de cota (além das linhas de chamada)",
                           "Dimension line extension (past the extension lines)"),
    "dimstyle.as_line": ("Como a linha", "As the line"),
    "dimstyle.as_project": ("A do projeto", "The project's"),
    "dimstyle.witness": ("Linhas de chamada", "Extension lines"),
    "dimstyle.witness.gap": ("Afastadas do elemento", "A gap off the element"),
    "dimstyle.witness.fixed": ("De comprimento fixo", "Of a fixed length"),
    "dimstyle.witness_gap": ("Afastamento ao elemento", "Gap to the element"),
    "dimstyle.witness_over": ("Prolongamento além da linha de cota", "Extension past the dimension line"),
    "dimstyle.witness_length": ("Comprimento fixo", "Fixed length"),
    "dimstyle.witness_pen": ("Espessura das linhas de chamada", "Extension lines' pen"),
    "dimstyle.font": ("Letra", "Font"),
    "dimstyle.font.program": ("A do programa", "The program's"),
    "dimstyle.width_factor": ("Fator de largura", "Width factor"),
    "dimstyle.bold": ("Negrito", "Bold"),
    "dimstyle.italic": ("Itálico", "Italic"),
    "dimstyle.underline": ("Sublinhado", "Underlined"),
    "dimstyle.text_offset": ("Afastamento do texto à linha", "Text offset from the line"),
    "dimstyle.text_place": ("Posição do texto", "Text position"),
    "dimstyle.text_place.above": ("Por cima da linha", "Over the line"),
    "dimstyle.text_place.centre": ("Na linha (interrompida)", "In the line (broken)"),
    "dimstyle.reading": ("Leitura", "Reading"),
    "dimstyle.reading.aligned": ("Ao longo da linha", "Along the line"),
    "dimstyle.reading.horizontal": ("Sempre na horizontal", "Always level"),
    "dimstyle.background": ("Fundo do texto", "Text background"),
    "dimstyle.background.transparent": ("Transparente", "Transparent"),
    "dimstyle.background.opaque": ("Opaco (tapa o que está por trás)", "Opaque (hides what is behind)"),
    "dimstyle.text_colour": ("Cor do texto", "Text colour"),
    "dimstyle.fit": ("Valores que não cabem", "Values that do not fit"),
    "dimstyle.fit.auto": ("Afastá-los (para fora ou para cima)", "Move them out of the way (out or up)"),
    "dimstyle.fit.keep": ("Deixá-los no meio", "Leave them in the middle"),
    "dimstyle.rounding": ("Arredondar a", "Round to"),
    "dimstyle.rounding.none": ("Não arredondar", "Not rounded"),
    "dimstyle.unit_symbol": ("Escrever a unidade (m, cm, mm)", "Write the unit (m, cm, mm)"),
    "dimstyle.sup_mm": ("Milímetros em expoente (2,47⁵)", "Raised millimetres (2.47⁵)"),
    "dimstyle.prefix": ("Prefixo", "Prefix"),
    "dimstyle.suffix": ("Sufixo", "Suffix"),
    "dimstyle.opening_height": ("Altura do vão por baixo da largura (portas e janelas)",
                                "The opening's height under its width (doors and windows)"),
    "dimstyle.eq_text": ("Texto das cotas iguais", "Equal dimensions' text"),
    "dimstyle.mark.tick_heavy": ("Traço oblíquo grosso", "Heavy oblique tick"),
    "dimstyle.mark.arrow_open": ("Seta aberta", "Open arrow"),
    "dimstyle.mark.arrow_closed": ("Seta fechada", "Closed arrow"),
    "dimstyle.mark.dot_open": ("Círculo", "Circle"),
    "dimstyle.mark.none": ("Nenhuma", "None"),
    # (0.193) dimension types: each dimension drawn by its own, else by the project's style
    "ctx.dim_type": ("Tipo de cota", "Dimension type"),
    "dimtype.project": ("Estilo do projeto", "The project's style"),
    "dimtype.which": ("Tipo", "Type"),
    "dimtype.delete": ("Apagar", "Delete"),
    "dimtype.new": ("Novo tipo", "New type"),
    "dimtype.new_name": ("Nome (por exemplo «Cotas de pormenor»)", "Name (e.g. \"Detail dimensions\")"),
    "dimtype.add": ("Juntar", "Add"),
    "cmd.dimension_type": ("Mudar o tipo das cotas", "Change the dimensions' type"),
    "info.dimension_type": ("{n} cota(s) passam a ser «{k}». Ctrl+Z desfaz.",
                            "{n} dimension(s) now \"{k}\". Ctrl+Z undoes it."),
    "props.dimension": ("Cota", "Dimension"),
    "props.dimensions": ("{n} cotas", "{n} dimensions"),
    "props.dim_value": ("Valor", "Value"),
    "props.dim_hint": ("Arraste um número ou a linha para os mudar de sítio (alinham-se com os outros); botão direito: "
                       "IG, apagar uma linha de chamada; duplo clique num número: o texto. Delete apaga.",
                       "Drag a value or the line to move them (they line up with the others); right button: EQ, "
                       "delete a witness line; double click a value: its text. Delete removes it."),
    "dimstyle.text": ("Altura do texto (no papel)", "Text height (on paper)"),
    "dimstyle.mark": ("Marca nas pontas", "Mark at the ends"),
    "dimstyle.mark.tick": ("Traço oblíquo", "Oblique tick"),
    "dimstyle.mark.arrow": ("Seta cheia", "Filled arrow"),
    "dimstyle.mark.dot": ("Ponto cheio", "Filled dot"),
    "dimstyle.unit": ("Unidade", "Unit"),
    "dimstyle.unit.m": ("Metros (4,50)", "Metres (4.50)"),
    "dimstyle.unit.cm": ("Centímetros (450)", "Centimetres (450)"),
    "dimstyle.unit.mm": ("Milímetros (4500)", "Millimetres (4500)"),
    "dimstyle.decimals": ("Casas decimais", "Decimals"),
    "dimstyle.example": ("Uma cota de 2,475 m escreve-se: {v}", "A 2.475 m dimension is written: {v}"),
    "info.dimension_style": ("Tipos de cota mudados: 2,475 m escreve-se {v}. Ctrl+Z desfaz.",
                             "Dimension types changed: 2.475 m is written {v}. Ctrl+Z undoes."),
    # sheets: own fields, numbering, revisions, sheets by storey (0.127)
    "tb.extra": ("Campos próprios do projeto (aparecem por cima da legenda)",
                 "The project's own fields (printed over the title block)"),
    "tb.extra_label": ("Campo", "Field"),
    "tb.extra_text": ("Texto", "Text"),
    "tb.add_row": ("Juntar", "Add"),
    "tb.remove_row": ("Tirar", "Remove"),
    "tb.numbering": ("Numeração das folhas", "Sheet numbering"),
    "tb.prefix": ("Prefixo", "Prefix"),
    "tb.prefix_hint": ("por exemplo A- (A-01, A-02…)", "for instance A- (A-01, A-02…)"),
    "tb.digits": ("Algarismos", "Digits"),
    "tb.revisions": ("Revisões desta folha (a mais recente em baixo):", "This sheet's revisions (the latest last):"),
    "tb.rev_code": ("Rev.", "Rev."),
    "tb.rev_date": ("Data", "Date"),
    "tb.rev_text": ("Descrição", "Description"),
    "act.sheets_by_storey": ("Folhas por pavimento…", "Sheets by storey…"),
    "tip.sheets_by_storey": ("Uma folha com a planta de cada pavimento escolhido (e, se quiser, uma com os alçados e "
                             "outra com os cortes)",
                             "A sheet with the plan of each storey chosen (and, if wanted, one with the elevations "
                             "and one with the sections)"),
    "wizard.title": ("Folhas por pavimento", "Sheets by storey"),
    "wizard.intro": ("Faz uma folha para cada pavimento escolhido, com a sua planta. As folhas já feitas ficam.",
                     "Makes a sheet for each storey chosen, with its plan. The sheets already made stay."),
    "wizard.paper": ("Papel", "Paper"),
    "wizard.elevations": ("Uma folha com os quatro alçados", "A sheet with the four elevations"),
    "wizard.sections": ("Uma folha com os cortes", "A sheet with the sections"),
    "wizard.plan_sheet": ("Planta — {name}", "Plan — {name}"),
    "wizard.elevations_sheet": ("Alçados", "Elevations"),
    "wizard.sections_sheet": ("Cortes", "Sections"),
    "cmd.sheets_by_storey": ("Folhas por pavimento", "Sheets by storey"),
    "info.sheets_by_storey": ("{n} folhas novas. Ctrl+Z desfaz.", "{n} new sheets. Ctrl+Z undoes."),
    # the project's own schedules (0.131)
    "sched.new": ("Nova tabela…", "New schedule…"),
    "sched.edit": ("Editar…", "Edit…"),
    "sched.delete": ("Apagar", "Delete"),
    "sched.own": ("Tabela: {name}", "Schedule: {name}"),
    "sched.untitled": ("Tabela nova", "New schedule"),
    "sched.editor": ("Propriedades da tabela", "Schedule properties"),
    "sched.def_name": ("Nome", "Name"),
    "sched.def_category": ("Selecionar campos disponíveis em", "Select available fields from"),
    "sched.def_fields": ("Campos tabelados (na ordem):", "Scheduled fields (in order):"),
    "sched.def_formulas": ("Valores calculados (ƒx):", "Calculated values (ƒx):"),
    # (0.477) the Properties as Revit's, in tabs
    "sched.tab.fields": ("Campos", "Fields"),
    "sched.tab.filter": ("Filtro", "Filter"),
    "sched.tab.sort": ("Classificar/Agrupar", "Sorting/Grouping"),
    "sched.search_label": ("Pesquisa de nomes de parâmetro", "Search parameter names"),
    "sched.search_fields": ("escreva parte do nome", "type part of the name"),
    "sched.available": ("Campos disponíveis:", "Available fields:"),
    "sched.available_n": ("Campos disponíveis: {n} itens", "Available fields: {n} items"),
    "sched.add_field": ("Acrescentar o campo à tabela", "Add the field to the schedule"),
    "sched.remove_field": ("Tirar o campo da tabela", "Remove the field from the schedule"),
    "sched.calculated": ("Valor calculado (uma fórmula com os campos de números)",
                         "Calculated value (a formula of the number fields)"),
    "sched.formula_new": ("Valor calculado", "Calculated value"),
    "sched.field_up": ("Subir o campo", "Move the field up"),
    "sched.field_down": ("Descer o campo", "Move the field down"),
    "sched.formula_name": ("Nome", "Name"),
    "sched.formula_expr": ("Fórmula", "Formula"),
    "sched.formula_hint": ("Na fórmula: números (1,10), + − * / ( ), round(x; casas), min, max, abs, e as colunas "
                           "de números: {names}. Por exemplo: length * height.",
                           "In a formula: numbers, + − * / ( ), round(x; places), min, max, abs, and the number "
                           "columns: {names}. For instance: length * height."),
    "sched.def_filters": ("Só as linhas em que:", "Only the rows where:"),
    "sched.filter_column": ("Coluna", "Column"),
    "sched.filter_op": ("É", "Is"),
    "sched.filter_value": ("Valor", "Value"),
    "sched.def_sort": ("Ordenar por", "Sort by"),
    "sched.descending": ("do maior para o menor", "largest first"),
    "sched.def_group": ("Agrupar por", "Group by"),
    "sched.none": ("(nada)", "(nothing)"),
    "cmd.schedules": ("Tabelas do projeto", "The project's schedules"),
    "sched.put": ("Pôr numa folha", "Put on a sheet"),                         # (0.132)
    # detail views (0.133)
    "tool.detail": ("Pormenor", "Detail view"),
    "detail.name": ("Pormenor {n}", "Detail {n}"),
    "cmd.detail": ("Pormenor", "Detail view"),
    "cmd.remove_detail": ("Apagar pormenor", "Delete detail view"),
    "ctx.detail_scale": ("Escala", "Scale"),
    "hint.detail_view": ("Pormenor: abra uma planta, um corte ou um alçado — o pormenor é um pedaço dele.",
                         "Detail view: open a plan, a section or an elevation — the detail is a piece of it."),
    "hint.detail": ("Pormenor a 1:{s}: clique num canto do pedaço a mostrar maior.",
                    "Detail at 1:{s}: click a corner of the piece to show bigger."),
    "hint.detail_2": ("Clique no canto oposto.", "Click the opposite corner."),
    "keys.detail": ("Dois cliques: os cantos  ·  Esc: recomeçar", "Two clicks: the corners  ·  Esc: start again"),
    "info.detail": ("{name} a 1:{s}: no painel Projeto, ponha-o numa folha. Ctrl+Z desfaz.",
                    "{name} at 1:{s}: in the Project panel, put it on a sheet. Ctrl+Z undoes."),
    "info.detail_head": ("{v} — duplo clique mostra-o maior aqui.", "{v} — double-click shows it bigger here."),
    "tree.details": ("Pormenores", "Detail views"),
    "tree.remove_detail": ("Apagar este pormenor", "Delete this detail view"),
    # title block templates (0.129)
    "sheet.template": ("Modelo da legenda", "Title block"),
    "sheet.template.full": ("Completo", "Full"),
    "sheet.template.compact": ("Compacto", "Compact"),
    "sheet.template.strip": ("Faixa lateral", "Side strip"),
    "sheet.template.custom": ("Da empresa (personalizado)", "The company's (custom)"),                # (0.472)
    # DXF (0.129)
    "act.export_dxf": ("Exportar vista (DXF, DWG, SVG)…", "Export view (DXF, DWG, SVG)…"),
    "dxf.filter": ("Desenho DXF para CAD (*.dxf);;Desenho DWG do AutoCAD (*.dwg);;Desenho SVG (*.svg)",
                   "DXF drawing for CAD (*.dxf);;AutoCAD DWG drawing (*.dwg);;SVG drawing (*.svg)"),
    "info.dxf": ("Vista exportada em DXF: {f} ({n} elementos, em metros, textos para 1:{s}).",
                 "View exported as DXF: {f} ({n} entities, in metres, texts for 1:{s})."),
    # (0.369) the view in DWG and in SVG
    "info.dwg": ("Vista exportada em DWG (AutoCAD 2018): {f} ({n} elementos, em metros, textos para 1:{s}).",
                 "View exported as DWG (AutoCAD 2018): {f} ({n} entities, in metres, texts for 1:{s})."),
    "info.svg_view": ("Vista exportada em SVG: {f}, à escala 1:{s} ({w} × {h} mm).",
                      "View exported as SVG: {f}, at 1:{s} ({w} × {h} mm)."),
    "dwg.working": ("A gravar o DWG…", "Writing the DWG…"),
    "err.dwg_converter_export": ("Para gravar em DWG é preciso o ODA File Converter (gratuito, da Open Design "
                                 "Alliance) instalado: o desenho passa por DXF e ele converte-o. Grave em DXF, que o "
                                 "AutoCAD também abre.",
                                 "Writing a DWG needs the ODA File Converter (free, from the Open Design Alliance) "
                                 "installed: the drawing goes through a DXF and it converts it. Save as DXF, which "
                                 "AutoCAD opens too."),
    "err.dwg_convert_export": ("O ODA File Converter não conseguiu gravar o DWG. Grave em DXF, que o AutoCAD também "
                               "abre.", "The ODA File Converter could not write the DWG. Save as DXF, which AutoCAD "
                               "opens too."),
    # sheet sets, publishing, PNG / SVG, printing (0.128)
    "tree.export_sheets_png": ("Exportar todas em PNG…", "Export all as PNG…"),
    "tree.export_sheets_svg": ("Exportar todas em SVG…", "Export all as SVG…"),
    "tree.export_sheet_png": ("Exportar em PNG…", "Export as PNG…"),
    "tree.export_sheet_svg": ("Exportar em SVG…", "Export as SVG…"),
    "tree.print_sheets": ("Imprimir todas…", "Print all…"),
    "tree.print_sheet": ("Imprimir…", "Print…"),
    "tree.sheet_sets": ("Conjuntos…", "Sets…"),
    "tree.publish_set": ("Publicar o conjunto", "Publish the set"),
    "sheet.export_png": ("Exportar folhas em PNG: escolha a pasta", "Export sheets as PNG: choose the folder"),
    "sheet.export_svg": ("Exportar folhas em SVG: escolha a pasta", "Export sheets as SVG: choose the folder"),
    "sheet.print": ("Imprimir folhas", "Print sheets"),
    "sets.title": ("Conjuntos de «{name}»", "Sets of “{name}”"),
    "sets.note": ("Um conjunto junta as folhas que se publicam juntas («Licenciamento», «Execução»…). Uma folha "
                  "pode estar em vários.",
                  "A set gathers the sheets published together (“Permit”, “Construction”…). A sheet can be in "
                  "several."),
    "sets.new": ("Novo conjunto (escreva o nome)", "New set (type its name)"),
    "cmd.sheet_sets": ("Conjuntos da folha", "Sheet's sets"),
    "info.sheets_images": ("{n} folhas em {fmt} na pasta {f}.", "{n} sheets as {fmt} in the folder {f}."),
    "info.sheets_printed": ("{n} folhas mandadas para a impressora.", "{n} sheets sent to the printer."),
    "info.set_empty": ("O conjunto «{name}» não tem folhas com vistas.", "The set “{name}” has no sheets with views."),
    # graphic styles, line types (0.126)
    "act.graphic_styles": ("Estilos gráficos…", "Graphic styles…"),
    # (0.360) the symbols' generator
    "act.symbol_styles": ("Símbolos…", "Symbols…"),
    "tip.symbol_styles": ("Como são os símbolos das vistas: a cabeça e a linha do corte, a marca do alçado, a chamada "
                          "do pormenor, a marca de nível — forma, seta, tamanhos, tipo de linha e caneta —, com o "
                          "desenho ao lado. Vale para todas as plantas, cortes, folhas, PDF e DXF.",
                          "How the views' symbols look: a section's head and line, an elevation's mark, a detail's "
                          "callout, a level's mark — shape, arrow, sizes, line type and pen —, drawn beside. Every plan, "
                          "section, sheet, PDF and DXF follows it."),
    "symbols.title": ("Símbolos", "Symbols"),
    "symbols.note": ("Os símbolos de todas as vistas do projeto, no papel (mm). Cada separador desenha o seu ao lado.",
                     "The symbols of all the project's views, on paper (mm). Each tab draws its own beside."),
    "symbols.defaults": ("Os de sempre", "The usual ones"),
    "symbols.storey": ("Piso 1", "Floor 1"),
    "symbols.kind.section": ("Corte", "Section"),
    "symbols.kind.elevation": ("Alçado (vista)", "Elevation (view)"),
    "symbols.kind.detail": ("Pormenor", "Detail"),
    "symbols.kind.level": ("Nível", "Level"),
    "symbols.field.head": ("Cabeça", "Head"),
    "symbols.field.arrow": ("Seta", "Arrow"),
    "symbols.field.size": ("Raio da cabeça", "Head's radius"),
    "symbols.field.text": ("Altura do texto", "Text height"),
    "symbols.field.line": ("Linha", "Line"),
    "symbols.field.pen": ("Caneta", "Pen"),
    "symbols.field.mark": ("Marca", "Mark"),
    "symbols.head.circle": ("Círculo", "Circle"),
    "symbols.head.square": ("Quadrado", "Square"),
    "symbols.head.none": ("Nenhuma (só o texto)", "None (the text only)"),
    "symbols.arrow.filled": ("Cheia", "Filled"),
    "symbols.arrow.open": ("Vazada", "Open"),
    "symbols.arrow.none": ("Nenhuma", "None"),
    "symbols.line.dashdot": ("Traço-ponto", "Dash-dot"),
    "symbols.line.dashed": ("Tracejada", "Dashed"),
    "symbols.line.dotted": ("Pontos", "Dotted"),
    "symbols.line.continuous": ("Contínua", "Continuous"),
    "symbols.line.ends": ("Só nas pontas", "Only at its ends"),
    "symbols.mark.triangle": ("Triângulo", "Triangle"),
    "symbols.mark.target": ("Círculo em quartos (como o Revit)", "Quartered circle (as Revit's)"),
    "symbols.mark.none": ("Nenhuma (só o texto)", "None (the text only)"),
    # (0.462) a level's: a square end, at which end(s), its words
    "symbols.mark.square": ("Quadrado", "Square"),
    "symbols.field.ends": ("Pontas", "Ends"),
    "symbols.field.label": ("Texto", "Text"),
    "symbols.ends.right": ("À direita", "On the right"),
    "symbols.ends.left": ("À esquerda", "On the left"),
    "symbols.ends.both": ("Nas duas", "On both"),
    "symbols.label.level_name": ("Cota e nome, por cima", "Level and name, over the line"),
    "symbols.label.name_level": ("NOME | cota, por cima", "NAME | level, over the line"),
    "symbols.label.name_over": ("Nome por cima, cota por baixo", "Name over, level under"),
    "symbols.label.level_over": ("Cota por cima, nome por baixo", "Level over, name under"),
    "cmd.symbol_styles": ("Símbolos", "Symbols"),
    "info.symbol_styles": ("Símbolos mudados: todas as vistas e folhas seguem-nos. Ctrl+Z desfaz.",
                           "Symbols changed: every view and sheet follows them. Ctrl+Z undoes."),
    "cmd.graphic_styles": ("Estilos gráficos", "Graphic styles"),
    "info.graphic_styles": ("Estilos gráficos mudados: as vistas e as folhas desenham-se de novo. Ctrl+Z desfaz.",
                            "Graphic styles changed: the views and sheets are drawn again. Ctrl+Z undoes."),
    "gstyle.title": ("Estilos gráficos do projeto", "The project's graphic styles"),
    "gstyle.note": ("Como os desenhos saem no papel (PDF e folhas): cada material cortado — o material de cada "
                    "camada diz o seu tipo, no editor de materiais — e a espessura de cada caneta.",
                    "How the drawings come out on paper (PDF and sheets): each material cut — each layer's "
                    "material says its kind, in the material editor — and the width of each pen."),
    "gstyle.material": ("Material cortado", "Material cut"),
    "gstyle.pattern": ("Padrão", "Pattern"),
    "gstyle.colour": ("Cor", "Colour"),
    "gstyle.angle": ("Ângulo", "Angle"),
    "gstyle.spacing": ("Espaçamento", "Spacing"),
    "gstyle.preview": ("No papel", "On paper"),
    "gstyle.pens": ("Canetas", "Pens"),
    "gstyle.defaults": ("Repor os de sempre", "Back to the usual ones"),
    "gstyle.mat.concrete": ("Betão", "Concrete"),
    "gstyle.mat.masonry": ("Alvenaria", "Masonry"),
    "gstyle.mat.wood": ("Madeira", "Wood"),
    "gstyle.mat.insulation": ("Isolamento", "Insulation"),
    "gstyle.mat.earth": ("Terra", "Earth"),
    "gstyle.mat.gypsum": ("Gesso e reboco", "Gypsum and plaster"),
    "gstyle.mat.other": ("Outros (sem tipo)", "Others (no kind)"),
    "gstyle.pattern.solid": ("Cheio", "Solid"),
    "gstyle.pattern.lines": ("Linhas", "Lines"),
    "gstyle.pattern.cross": ("Linhas cruzadas", "Crossed lines"),
    "gstyle.pattern.none": ("Nada (branco)", "Nothing (white)"),
    "gstyle.pen.cut": ("O que é cortado", "What is cut"),
    "gstyle.pen.seen": ("O que se vê para lá do corte", "What is seen beyond the cut"),
    "gstyle.pen.hatch": ("Tramas", "Hatches"),
    "gstyle.pen.dimension": ("Cotas", "Dimensions"),
    "gstyle.pen.drawn": ("Desenho 2D", "2D drawing"),
    "ctx.line_type": ("Linha", "Line"),
    "ctx.line_width": ("Espessura", "Width"),
    "linetype.continuous": ("Contínua", "Continuous"),
    "linetype.dashed": ("Tracejada", "Dashed"),
    "linetype.dashdot": ("Traço-ponto", "Dash-dot"),
    "linetype.hidden": ("Oculta", "Hidden"),
    "linewidth.project": ("A do projeto", "The project's"),
    # the views' symbols (0.121)
    "info.mark_head": ("{v} — duplo clique abre a vista.", "{v} — double-click opens the view."),
    "info.section_chosen": ("{v}: arraste os quadrados das pontas para esticar ou encurtar a linha; o losango vira o "
                            "corte para o outro lado. Duplo clique na cabeça abre a vista.",
                            "{v}: drag the squares at its ends to lengthen or shorten its line; the diamond turns it "
                            "to look the other way. Double-click its head to open the view."),           # (0.358)
    "info.section_flipped": ("{v} agora olha para o outro lado. Ctrl+Z desfaz.",
                             "{v} now looks the other way. Ctrl+Z undoes."),
    "info.section_ends": ("A linha do corte tem agora {l}. Ctrl+Z desfaz.", "The section's line is now {l}. Ctrl+Z "
                          "undoes."),
    "cmd.section_ends": ("Esticar a linha do corte", "Section line's length"),
    "cmd.section_flip": ("Virar o corte", "Turn the section round"),
    # curtain walls (0.117)
    "rib.short.curtain_wall": ("Parede cortina", "Curtain wall"),
    "tool.curtain_wall": ("Fachada de vidro", "Curtain wall"),
    "elem.curtain_wall": ("Fachada", "Curtain wall"),
    "cmd.curtain_wall": ("Fachada de vidro", "Curtain wall"),
    "cmd.curtain_wall_edit": ("Mudar fachada", "Change curtain wall"),
    "ctx.mullions": ("Montantes a cada", "Mullions every"),
    "ctx.transoms": ("Travessas a cada", "Transoms every"),
    # (0.436) the curtain wall along a free arc, or over an upright face (the addon's circular and «por face»)
    "ctx.cw_shape": ("Forma", "Shape"),
    "cwshape.line": ("Linha", "Line"),
    "cwshape.arc": ("Arco (3 cliques)", "Arc (3 clicks)"),
    "cwshape.face": ("Por face", "By face"),
    "hint.curtain_arc_start": ("Fachada de vidro em arco ({h} de altura): clique no início do arco.",
                               "Curtain wall along an arc ({h} high): click the start of the arc."),
    "hint.curtain_arc_end": ("Clique no fim do arco (ou escreva o comprimento da corda e Enter).",
                             "Click the end of the arc (or type the chord's length and Enter)."),
    "hint.curtain_arc_bulge": ("Mova o rato para curvar o arco e clique (ou escreva o raio e Enter).",
                               "Move the mouse to bend the arc and click (or type its radius and Enter)."),
    "hint.curtain_face": ("Fachada de vidro por face (montantes até {m}, travessas até {t}): passe o rato por uma face de "
                          "pé de um volume ou de uma parede e clique — a fachada fica por fora dela, do tamanho dela.",
                          "Curtain wall by face (mullions up to {m}, transoms up to {t}): move over an upright face of a "
                          "volume or a wall and click — the curtain wall goes just outside it, as big as it."),
    "tip.curtain_face_none": ("Aqui não: escolha uma face de pé", "Not here: choose an upright face"),
    "err.curtain_face_none": ("A fachada por face precisa de uma face de pé (a de um volume, de uma parede…).",
                              "A curtain wall by face needs an upright face (a volume's, a wall's…)."),
    "hint.curtain_wall": ("Fachada de vidro ({h} de altura, montantes até {m}, travessas até {t}): clique no início "
                          "da linha.",
                          "Curtain wall ({h} high, mullions up to {m}, transoms up to {t}): click the start of its "
                          "line."),
    "hint.curtain_wall_2": ("Clique no fim da linha ou digite o comprimento + Enter. Esc cancela.",
                            "Click the end of its line or type its length + Enter. Esc cancels."),
    "info.curtain_wall": ("Fachada de vidro de {l} × {h}, montantes e travessas a espaços iguais. Ctrl+Z desfaz.",
                          "{l} × {h} curtain wall, its mullions and transoms equally spaced. Ctrl+Z undoes."),
    # railings (0.115)
    "tool.railing": ("Guarda", "Railing"),
    "elem.railing": ("Guarda", "Railing"),
    "cmd.railing": ("Guarda", "Railing"),
    "cmd.railing_edit": ("Mudar guarda", "Change railing"),
    "ctx.railing_shape": ("Por", "Along"),
    "ctx.railing_style": ("Estilo", "Style"),
    "railshape.path": ("Caminho (clicado)", "A path (clicked)"),
    "railshape.void": ("À volta de um vazio", "Round a void"),
    "railshape.stair": ("Nos lados de uma escada", "On a stair's sides"),
    "railshape.opening": ("Num vão (porta ou janela)", "In an opening (door or window)"),
    "hint.railing.opening": ("Guarda {style} de {h} num vão: clique numa janela ou porta (fica de batente a batente, "
                             "a meio da parede). Tab muda a forma.",
                             "{h} {style} guard in an opening: click a window or door (it goes jamb to jamb, in the "
                             "middle of the wall). Tab changes the shape."),
    "err.railing_opening": ("Clique numa janela ou porta.", "Click a window or a door."),
    "railstyle.bars": ("Barras verticais", "Upright bars"),
    "railstyle.glass": ("Vidro", "Glass"),
    "railstyle.rails": ("Barras horizontais", "Horizontal rails"),
    "hint.railing.path": ("Guarda ({style}, {h}): clique nos pontos do caminho; Enter termina, Delete apaga o "
                          "último. (Tab muda.)",
                          "Railing ({style}, {h}): click the path's points; Enter ends it, Delete takes the last "
                          "back. (Tab changes it.)"),
    "hint.railing.void": ("Guarda ({style}, {h}): clique numa laje junto de um vazio (um furo ou uma abertura): a "
                          "guarda dá-lhe a volta. (Tab muda.)",
                          "Railing ({style}, {h}): click a slab by a void (a hole or an opening): the railing goes "
                          "round it. (Tab changes it.)"),
    "hint.railing.stair": ("Guardas ({style}, {h}): clique numa escada: uma de cada lado de cada lanço. (Tab "
                           "muda.)",
                           "Railings ({style}, {h}): click a stair: one on each side of each flight. (Tab changes "
                           "it.)"),
    "keys.railing": ("Tab: caminho → vazio → escada  ·  Enter: terminar o caminho  ·  Delete: último ponto  ·  "
                     "Esc: cancelar",
                     "Tab: path → void → stair  ·  Enter: end the path  ·  Delete: last point  ·  Esc: cancel"),
    "info.railing": ("Guarda de {l} ({style}, {h}). Ctrl+Z desfaz.", "{l} railing ({style}, {h}). Ctrl+Z undoes."),
    "info.stair_railings": ("{n} guardas nos lados da escada. Ctrl+Z desfaz.", "{n} railings on the stair's sides. "
                            "Ctrl+Z undoes."),
    "err.railing_void": ("Não há um vazio perto: clique numa laje junto de um furo ou de uma abertura.",
                         "No void near: click a slab by a hole or an opening."),
    "err.railing_stair": ("Clique numa escada.", "Click a stair."),
    "refuse.railing_short": ("o caminho é curto demais", "the path is too short"),
    "refuse.railing_height": ("a altura tem de ficar entre 0,30 e 3,00 m", "the height must be between 0.30 and "
                              "3.00 m"),
    "props.railing_style": ("Estilo", "Style"),
    # railing types (0.258)
    "ctx.railing_type": ("Tipo", "Type"),
    "props.railing_type": ("Tipo de guarda", "Railing type"),
    "props.rail_ext_base": ("Prolongamento na base", "Extension at its foot"),          # (0.282)
    "props.rail_ext_top": ("Prolongamento no topo", "Extension at its top"),
    "props.rail_ext_note": ("Numa escada, o DL 163/2006 (anexo, 2.4.9) pede um cobertor na base, com a inclinação, e "
                            "0,30 m no topo, de nível; numa rampa (2.5.8), 0,30 m nas duas pontas.",
                            "On a stair, Portugal's DL 163/2006 (annex, 2.4.9) asks for one going at the foot, "
                            "sloping, and 0.30 m at the top, level; on a ramp (2.5.8), 0.30 m at both ends."),
    "cmd.railing_type": ("Tipo de guarda", "Railing type"),
    # the railing type editor (0.260)
    "act.railing_types": ("Tipos de guarda…", "Railing types…"),
    "tip.railing_types": ("Os tipos de guarda do programa e do projeto: criar (duplicando), mudar as suas peças, "
                          "medidas e materiais, e apagar os que não estão em uso.",
                          "The program's and the project's railing types: make one (duplicating), change its parts, "
                          "sizes and materials, remove those not in use."),
    "props.edit_railing_type_tip": ("Abrir este tipo no editor de tipos de guarda", "Open this type in the railing "
                                    "type editor"),
    "cmd.railing_type_delete": ("Apagar tipo de guarda", "Delete railing type"),
    "refuse.type_in_use": ("há guardas deste tipo", "there are railings of this type"),
    "info.railing_type_saved": ("Tipo «{name}» guardado no projeto ({n} guardas refeitos).",
                                "Type \"{name}\" saved in the project ({n} railings made again)."),
    "railtype.title": ("Tipos de guarda", "Railing types"),
    "railtype.name": ("Nome", "Name"),
    "railtype.apply": ("Aplicar", "Apply"),
    "railtype.close": ("Fechar", "Close"),
    "railtype.copy_of": ("Cópia de {name}", "Copy of {name}"),
    "railtype.in_project": ("Guardado no projeto", "Kept in the project"),
    "railtype.by_gap": ("pela folga", "by the gap"),
    "railtype.bad_length": ("Há uma medida que não se percebe.", "A size cannot be read."),
    "railtype.group.general": ("Geral", "General"),
    "railtype.group.top": ("Corrimão de topo", "Top rail"),
    "railtype.group.posts": ("Prumos", "Posts"),
    "railtype.group.infill": ("Enchimento", "Infill"),
    "railtype.group.bottom": ("Travessa inferior", "Bottom rail"),
    "railtype.group.hand": ("Corrimão de apoio", "Handrail"),
    "railtype.group.shoe": ("Perfil de base (vidro encastrado)", "Base channel (glass set in it)"),
    "railtype.height": ("Altura habitual", "Usual height"),
    "railtype.top": ("Forma", "Shape"),
    "railtype.top_w": ("Largura (ou Ø)", "Width (or Ø)"),
    "railtype.top_h": ("Altura", "Height"),
    "railtype.top_mat": ("Material", "Material"),
    "railtype.post": ("Forma", "Shape"),
    "railtype.post_w": ("Largura (ou Ø)", "Width (or Ø)"),
    "railtype.post_d": ("Profundidade", "Depth"),
    "railtype.spacing": ("Afastamento máximo", "Most apart"),
    "railtype.plate": ("Chapa de base", "Base plate"),
    "railtype.plate_w": ("Largura da chapa", "Plate's width"),
    "railtype.plate_t": ("Espessura da chapa", "Plate's thickness"),
    "railtype.post_mat": ("Material", "Material"),
    "railtype.infill": ("Enchimento", "Infill"),
    "railtype.bar": ("Forma das barras", "Bars' shape"),
    "railtype.bar_w": ("Largura (ou Ø)", "Width (or Ø)"),
    "railtype.bar_d": ("Profundidade", "Depth"),
    "railtype.gap": ("Folga máxima (passo, malha)", "Most clear gap (pitch, mesh)"),
    "railtype.count": ("Número de travessas / cabos", "Rails / cables"),
    "railtype.sheet_t": ("Espessura do vidro / chapa", "Glass / sheet thickness"),
    "railtype.infill_mat": ("Material", "Material"),
    "railtype.bottom": ("Com travessa inferior", "With a bottom rail"),
    "railtype.bottom_z": ("Altura ao chão", "Over the floor"),
    "railtype.hand": ("Com corrimão de apoio", "With a handrail"),
    "railtype.hand_side": ("Lado", "Side"),
    "railtype.hand_shape": ("Forma", "Shape"),
    "railtype.hand_w": ("Ø (ou largura)", "Ø (or width)"),
    "railtype.hand_z": ("Altura do topo", "Its top's height"),
    "railtype.hand_off": ("Afastamento do guarda", "Off the railing"),
    "railtype.hand_mat": ("Material", "Material"),
    "railtype.shoe_w": ("Largura", "Width"),
    "railtype.shoe_h": ("Altura", "Height"),
    "railopt.top.rect": ("Retangular", "Rectangular"),
    "railopt.top.round": ("Redondo", "Round"),
    "railopt.top.none": ("Nenhum", "None"),
    "railopt.post.square": ("Quadrado", "Square"),
    "railopt.post.round": ("Redondo", "Round"),
    "railopt.post.flat": ("Chato", "Flat"),
    "railopt.post.none": ("Sem prumos", "No posts"),
    "railopt.plate.none": ("Nenhuma", "None"),
    "railopt.plate.square": ("Quadrada", "Square"),
    "railopt.plate.round": ("Redonda", "Round"),
    "railopt.infill.bars": ("Barras verticais", "Upright bars"),
    "railopt.infill.rails": ("Travessas horizontais", "Horizontal rails"),
    "railopt.infill.cables": ("Cabos de aço", "Steel cables"),
    "railopt.infill.glass": ("Vidro com grampos", "Glass with clamps"),
    "railopt.infill.glass_channel": ("Vidro encastrado (sem prumos)", "Glass in a base channel (no posts)"),
    "railopt.infill.panel": ("Chapa cheia", "Solid sheet"),
    "railopt.infill.mesh": ("Malha", "Mesh"),
    "railopt.infill.zigzag": ("Ziguezague", "Zigzag"),
    "railopt.infill.none": ("Nenhum", "None"),
    "railopt.bar.square": ("Quadradas", "Square"),
    "railopt.bar.round": ("Redondas", "Round"),
    "railopt.bar.flat": ("Chatas", "Flat"),
    "railopt.hand_side.left": ("Esquerdo", "Left"),
    "railopt.hand_side.right": ("Direito", "Right"),
    "railopt.hand_side.both": ("Os dois", "Both"),
    "railopt.hand_shape.round": ("Redondo", "Round"),
    "railopt.hand_shape.rect": ("Retangular", "Rectangular"),
    # stairs (0.114)
    "tool.stair": ("Escada", "Stair"),
    "elem.stair": ("Escada", "Stair"),
    "cmd.stair": ("Escada", "Stair"),
    "cmd.stair_edit": ("Mudar escada", "Change stair"),
    "ctx.stair_form": ("Forma", "Form"),
    "ctx.stair_turn": ("Viragem", "Turn"),
    "ctx.going": ("Cobertor", "Tread"),
    "stairform.straight": ("Reta", "Straight"),
    "stairform.l": ("Em L (patamar)", "L (landing)"),
    "stairform.u": ("Em U (patamar)", "U (landing)"),
    "stairform.v": ("Em V (lanços lado a lado)", "V (flights side by side)"),
    "stairform.spiral": ("Circular (caracol)", "Spiral"),
    "stairturn.left": ("À esquerda", "To the left"),
    "stairturn.right": ("À direita", "To the right"),
    "hint.stair": ("{form}, {w} de largura, a subir {h}: clique no meio do primeiro degrau (no chão).",
                   "{form}, {w} wide, rising {h}: click the middle of the first step (on the floor)."),
    "hint.stair_2": ("Clique para onde sobe (ou Esc). {n} espelhos de {r}, cobertor {g} (2E + C = {b}).",
                     "Click the way it goes up (or Esc). {n} risers of {r}, tread {g} (2R + T = {b})."),
    "keys.stair": ("Dois cliques: o pé e o sentido  ·  Pronta: um clique, R: rodar, Espaço: o ponto  ·  X / Y: "
                   "bloquear o eixo  ·  Esc: cancelar",
                   "Two clicks: its foot and its way  ·  Ready: one click, R: turn, Space: its point  ·  X / Y: lock "
                   "the axis  ·  Esc: cancel"),
    # (0.435) a stair ready to put down, in one click (the addon's «Gerar escada»)
    "ctx.stair_placing": ("Colocar", "Place"),
    "stairplacing.two": ("Pé e sentido (dois cliques)", "Foot and way (two clicks)"),
    "stairplacing.ready": ("Pronta (um clique)", "Ready (one click)"),
    "ctx.stair_anchor": ("Ponto", "Point"),
    "stairanchor.center": ("Meio do 1.º degrau", "Middle of the 1st step"),
    "stairanchor.outside": ("Canto de fora do 1.º degrau", "Outer corner of the 1st step"),
    "stairanchor.inside": ("Canto de dentro do 1.º degrau", "Inner corner of the 1st step"),
    "info.stair_anchor": ("A escada fica presa pelo {p}.", "The stair is held by its {p}."),
    "hint.stair_ready": ("{form} pronta, {w} de largura, a subir {h}: clique onde fica o {p}. R: rodar · Espaço: outro "
                         "ponto · Esc: Selecionar.",
                         "Ready {form}, {w} wide, rising {h}: click where its {p} goes. R: turn · Space: another point "
                         "· Esc: Select."),
    "tip.stair_ready": ("Clique: pôr a escada · R: rodar · Espaço: outro ponto",
                        "Click: put the stair · R: turn · Space: another point"),
    "info.stair": ("Escada ({form}) com {n} espelhos de {r} e cobertor {g}, a subir {h}. Ctrl+Z desfaz.",
                   "Stair ({form}) of {n} risers of {r}, tread {g}, rising {h}. Ctrl+Z undoes."),
    "refuse.stair_small": ("a escada ficaria pequena demais (largura 50 cm, cobertor 15 cm, desnível 30 cm no "
                           "mínimo)",
                           "the stair would be too small (50 cm wide, 15 cm treads, 30 cm rise at least)"),
    "props.stair_form": ("Forma", "Form"),
    "props.stair_turn": ("Viragem", "Turn"),
    "props.going": ("Cobertor", "Tread"),
    "props.risers": ("Espelhos", "Risers"),
    "props.blondel": ("2 espelhos + cobertor", "2 risers + tread"),
    # drains and openings through roofs (0.113)
    "tool.drain": ("Ralo", "Drain"),
    "elem.drain": ("Ralo", "Drain"),
    "cmd.drain": ("Ralo", "Drain"),
    "hint.drain": ("Clique numa cobertura onde fica o ralo. Esc: Selecionar.",
                   "Click a roof where the drain goes. Esc: Select."),
    "keys.drain": ("Clique: um ralo ali  ·  Esc: Selecionar", "Click: a drain there  ·  Esc: Select"),
    "tip.drain": ("Ralo aqui", "Drain here"),
    "err.drain_roof": ("Clique numa cobertura.", "Click a roof."),
    "info.drain": ("Ralo posto em «{roof}». Ctrl+Z desfaz.", "Drain put on “{roof}”. Ctrl+Z undoes."),
    "tool.roof_opening": ("Abertura (cobertura / laje)", "Opening (roof / slab)"),
    "cmd.vertical_opening": ("Abertura", "Opening"),
    "hint.roof_opening": ("Clique numa cobertura ou laje no primeiro canto da abertura. Esc: Selecionar.",
                          "Click a roof or slab at the opening's first corner. Esc: Select."),
    "hint.roof_opening_2": ("Clique no canto oposto (na mesma cobertura ou laje) ou digite as medidas (ex.: 1;0,8) "
                            "e Enter. Botão direito: recomeçar.",
                            "Click the opposite corner (on the same roof or slab) or type the size (e.g. 1;0.8) and "
                            "Enter. Right button: start again."),
    "keys.roof_opening": ("Dois cliques: os cantos  ·  Esc: Selecionar", "Two clicks: the corners  ·  Esc: Select"),
    "err.roof_opening_host": ("Clique numa cobertura ou numa laje.", "Click a roof or a slab."),
    "info.roof_opening": ("Abertura de {a} × {b} em «{host}», de alto a baixo. Ctrl+Z desfaz.",
                          "{a} × {b} opening in “{host}”, right through. Ctrl+Z undoes."),
    # openings: fanlights, marks, bare openings (0.110)
    "types.transom": ("Bandeira (altura)", "Fanlight (height)"),
    "types.err_transom": ("A bandeira tem de caber na altura e deixar pelo menos 1,80 m para a folha.",
                          "The fanlight must fit in the height and leave at least 1.80 m for the leaf."),
    "ctx.bare_opening": ("Só o vão (sem caixilho)", "Opening only (no frame)"),
    "hint.bare_opening": ("Vão sem caixilho do tamanho de «{type}»: passe o cursor sobre uma parede e clique (ou "
                          "digite a distância à ponta mais perto + Enter).",
                          "Opening with no frame, the size of “{type}”: hover a wall and click (or type the "
                          "distance from the nearer end + Enter)."),
    "info.placed_bare": ("Vão sem caixilho ({type}) aberto em «{wall}». Ctrl+Z desfaz.",
                         "Opening with no frame ({type}) cut in “{wall}”. Ctrl+Z undoes."),
    "elem.bare_opening": ("Vão", "Opening"),
    "cmd.bare_opening": ("Vão sem caixilho", "Opening with no frame"),
    "cmd.mark": ("Marca", "Mark"),
    "cmd.renumber": ("Numerar portas e janelas", "Number doors and windows"),
    "act.renumber": ("Numerar portas e janelas", "Number doors and windows"),
    "tip.renumber": ("Todas as portas (P1, P2…) e janelas (J1, J2…) numeradas de novo, pavimento a pavimento, pela "
                     "ordem de leitura da planta",
                     "All doors (P1, P2…) and windows (J1, J2…) numbered again, storey by storey, in the plan's "
                     "reading order"),
    "info.renumbered": ("{n} porta(s) e janela(s) numeradas de novo. Ctrl+Z desfaz.",
                        "{n} door(s) and window(s) numbered again. Ctrl+Z undoes."),
    "info.renumbered_none": ("Não há portas nem janelas para numerar.", "There are no doors or windows to number."),
    "props.mark": ("Marca", "Mark"),
    # a wall's elevation profile (0.109)
    "tool.wall_profile": ("Perfil da parede", "Wall profile"),
    "act.edit_profile": ("Editar perfil", "Edit profile"),
    "tip.edit_profile": ("Desenhar o alçado da parede: empena, topo em degraus, recortes, arcos e curvas (também com "
                         "duplo clique na parede)",
                         "Draw the wall's elevation: a gable, a stepped top, cut-outs, arcs and curves (a double click "
                         "on the wall too)"),
    "cmd.wall_profile": ("Perfil da parede", "Wall profile"),
    # (0.380) no modes: a side's diamond pulled — a corner, with Shift an arc, with Alt a curve; Alt + a corner: a fillet
    "hint.wall_profile": ("Arraste o losango do meio de um lado: um canto novo — com Shift, um arco; com Alt, uma "
                          "curva. Arraste um quadrado: move o canto. Alt + clique num canto: concordância (raio). "
                          "«Furo» na barra de cima: desenhar furos. Clique num ponto e Delete: tira-o. Esc: sair.",
                          "Drag a side's middle diamond: a new corner — with Shift, an arc; with Alt, a curve. Drag a "
                          "square: the corner moves. Alt + a click on a corner: a fillet (radius). «Hole» on the bar "
                          "above: draw holes. Click a point and Delete: it goes. Esc: leave."),
    "hint.wall_profile_move": ("Com o botão carregado, leve o canto e largue onde fica. Botão direito: fica onde "
                               "estava.",
                               "With the button held, take the corner and let go where it goes. Right button: it "
                               "stays where it was."),
    "hint.wall_profile_none": ("Esta parede não tem perfil que se edite aqui. Esc: Selecionar.",
                               "This wall has no profile to edit here. Esc: Select."),
    "hint.wall_profile_side": ("Com o botão carregado, leve o rato e largue. Sem nada: um canto novo · Shift: um arco "
                               "· Alt: uma curva (pode carregar e largar as teclas a meio). Botão direito: desiste.",
                               "With the button held, move the mouse and let go. Nothing held: a new corner · Shift: "
                               "an arc · Alt: a curve (the keys can be pressed or let go meanwhile). Right button: give "
                               "up."),
    "hint.wall_profile_fillet": ("Concordância: afaste o rato do canto para o raio, ou escreva o raio (ex.: 0,5) e "
                                 "Enter; clique para a fazer. Botão direito: desiste.",
                                 "Fillet: move the mouse away from the corner for its radius, or type the radius "
                                 "(e.g. 0.5) and Enter; click to make it. Right button: give up."),
    "hint.wall_profile_curve": ("Com o botão carregado, leve a pega e largue onde fica. Botão direito: fica onde "
                                "estava.",
                                "With the button held, take the grip and let go where it goes. Right button: it stays "
                                "where it was."),
    "tip.profile_corner": ("Arraste: mover · Alt + clique: concordância · clique + Delete: tirar",
                           "Drag: move · Alt + click: fillet · click + Delete: take away"),
    "tip.profile_side": ("Arraste: canto · com Shift: arco · com Alt: curva",
                         "Drag: corner · with Shift: arc · with Alt: curve"),
    "tip.profile_curve": ("Arraste para mudar a curva · clique + Delete: lado reto",
                          "Drag to change the curve · click + Delete: straight side"),
    "tip.profile_drop": ("{p}  —  largue", "{p}  —  let go"),
    "tip.profile_side_drop": ("{m}  {p}  —  largue", "{m}  {p}  —  let go"),
    "tip.profile_chosen_corner": ("Escolhido: Delete tira este canto", "Chosen: Delete takes this corner away"),
    "tip.profile_chosen_curve": ("Escolhido: Delete endireita este lado", "Chosen: Delete straightens this side"),
    "info.profile_pick_first": ("Clique primeiro num canto ou na pega de uma curva, depois Delete.",
                                "Click a corner or a curve's grip first, then Delete."),
    "profkind.corner": ("Canto", "Corner"),
    "profkind.arc": ("Arco", "Arc"),
    "profkind.bezier": ("Curva", "Curve"),
    "tip.profile_fillet": ("Raio {r}  —  clique, ou escreva o raio e Enter",
                           "Radius {r}  —  click, or type it and Enter"),
    "err.profile_fillet": ("A concordância faz-se num canto entre dois lados retos.",
                           "A fillet is made on a corner between two straight sides."),
    "info.wall_profile_curves": ("Perfil da parede mudado ({n} lado(s) curvo(s)). Ctrl+Z desfaz.",
                                 "Wall profile changed ({n} curved side(s)). Ctrl+Z undoes."),
    "keys.wall_profile": ("Arrastar losango: canto · +Shift: arco · +Alt: curva  ·  Alt + clique num canto: "
                          "concordância  ·  Furo: polígono, retângulo, círculo  ·  clique + Delete: tirar  ·  Esc: sair",
                          "Drag a diamond: corner · +Shift: arc · +Alt: curve  ·  Alt + click on a corner: fillet  ·  "
                          "Hole: polygon, rectangle, circle  ·  click + Delete: take away  ·  Esc: leave"),
    "ctx.wall_plain": ("Parede simples (retângulo)", "Plain wall (rectangle)"),
    "info.wall_plain": ("A parede voltou a ser um retângulo. Ctrl+Z desfaz.", "The wall is a rectangle again. "
                        "Ctrl+Z undoes."),
    "info.wall_profile": ("Perfil da parede mudado. Ctrl+Z desfaz.", "Wall profile changed. Ctrl+Z undoes."),
    "info.edit_profile": ("Perfil de «{name}»: arraste o losango do meio de um lado para fazer um canto — com Shift um "
                          "arco, com Alt uma curva. Alt + clique num canto: concordância. «Furo» na barra de cima: "
                          "desenhar furos. Esc: sair.",
                          "Profile of “{name}”: drag a side's middle diamond for a corner — with Shift an arc, with "
                          "Alt a curve. Alt + click on a corner: a fillet. «Hole» on the bar above: draw holes. "
                          "Esc: leave."),
    "info.edit_profile_none": ("Selecione uma parede reta (uma só) para editar o perfil.",
                               "Select one straight wall to edit its profile."),
    "err.profile_bad": ("Esse perfil não serve: os lados cruzam-se ou é pequeno demais.",
                        "That profile will not do: its sides cross or it is too small."),
    "refuse.profile_bad": ("o perfil não serve (lados cruzados ou pequeno demais)",
                           "the profile will not do (its sides cross, or it is too small)"),
    "props.profile_wall": ("Perfil (alçado)", "Profile (elevation)"),
    "props.profile_drawn": ("Perfil desenhado", "Profile drawn"),
    # mirror (0.108)
    "tool.mirror": ("Espelhar", "Mirror"),
    "cmd.mirror": ("Espelhar", "Mirror"),
    "hint.mirror": ("Clique no primeiro ponto do eixo de simetria (Ctrl: copiar ou não). Esc: Selecionar.",
                    "Click the first point of the mirror axis (Ctrl: copy or not). Esc: Select."),
    "hint.mirror_2": ("Clique no segundo ponto do eixo: a seleção passa para o outro lado{copy}. Botão direito: "
                      "recomeçar.",
                      "Click the axis's second point: the selection goes to the other side{copy}. Right button: "
                      "start again."),
    "hint.mirror_copy": (" (fica uma cópia)", " (as a copy)"),
    "hint.mirror_none": ("Selecione primeiro o que quer espelhar (ferramenta Selecionar) e volte a Espelhar.",
                         "Select first what you want to mirror (Select tool), then Mirror again."),
    "keys.mirror": ("Dois cliques: o eixo de simetria  ·  Ctrl: copiar  ·  X / Y: bloquear o eixo  ·  "
                    "Esc: Selecionar",
                    "Two clicks: the mirror axis  ·  Ctrl: copy  ·  X / Y: lock the axis  ·  Esc: Select"),
    "info.mirrored": ("{n} espelhado(s){copy}. Ctrl+Z desfaz.", "{n} mirrored{copy}. Ctrl+Z undoes."),
    "info.mirrored_copy": (" em cópia", " as copies"),
    "info.mirror_left_out": (" Ficaram de fora {k} elemento(s) que ainda não se espelham (componentes, tubagens…).",
                             " {k} element(s) that cannot be mirrored yet were left out (components, pipes…)."),
    "refuse.not_mirrorable": ("este elemento ainda não se espelha", "this element cannot be mirrored yet"),
    "refuse.mirror_openings": ("uma laje com vãos ainda não se espelha", "a slab with openings cannot be mirrored "
                               "yet"),
    # align (0.107)
    "tool.align": ("Alinhar", "Align"),
    "cmd.align": ("Alinhar", "Align"),
    "hint.align": ("Clique na referência: um eixo da grelha, uma linha, uma aresta ou a face de qualquer elemento. "
                   "Esc: Selecionar.",
                   "Click the reference: a grid axis, a line, an edge or a face of any element. Esc: Select."),
    "hint.align_2": ("Clique no que alinhar, paralelo à referência: uma linha, a aresta de um piso, de uma laje ou de "
                     "qualquer elemento, a face de uma parede (acende a laranja e passa para a referência), ou numa "
                     "linha de um padrão — junta de azulejo, fiada de tijolo. Botão direito: outra referência.",
                     "Click what to align, parallel to the reference: a line, the edge of a floor, a slab or any "
                     "element, a wall's face (lit in orange, it moves onto the reference), or a line of a pattern — a "
                     "tile's joint, a brick course. Right button: another reference."),
    "keys.align": ("Clique: a referência, depois as linhas, arestas e faces — ou as linhas dos padrões — a alinhar  ·  "
                   "botão direito: outra referência  ·  Esc: Selecionar",
                   "Click: the reference, then the lines, edges and faces — or the patterns' lines — to align  ·  "
                   "right button: another reference  ·  Esc: Select"),
    # join / unjoin geometry by hand (0.333)
    "tool.join_geometry": ("Unir geometria", "Join geometry"),
    "tool.unjoin_geometry": ("Desunir geometria", "Unjoin geometry"),
    "hint.unjoin_geometry": ("Clique no primeiro dos dois elementos (parede, laje, pilar…) cuja junção quer ver. Esc: "
                             "Selecionar.",
                             "Click the first of the two elements (wall, slab, column…) whose join you want to see. "
                             "Esc: Select."),
    "hint.unjoin_geometry_2": ("Clique no elemento a desunir de «{name}»: a linha entre eles passa a ver-se no corte e "
                               "nas vistas. Botão direito: outro primeiro.",
                               "Click the element to unjoin from “{name}”: the line between them shows in the cut "
                               "and the views. Right button: another first one."),
    "hint.join_geometry": ("Clique no primeiro dos dois elementos a unir de novo. Esc: Selecionar.",
                           "Click the first of the two elements to join again. Esc: Select."),
    "hint.join_geometry_2": ("Clique no elemento a unir de novo a «{name}». Botão direito: outro primeiro.",
                             "Click the element to join again to “{name}”. Right button: another first one."),
    "keys.unjoin_geometry": ("Clique: um elemento, depois o outro  ·  botão direito: outro primeiro  ·  Esc: "
                             "Selecionar",
                             "Click: one element, then the other  ·  right button: another first one  ·  Esc: Select"),
    "keys.join_geometry": ("Clique: um elemento, depois o outro  ·  botão direito: outro primeiro  ·  Esc: Selecionar",
                           "Click: one element, then the other  ·  right button: another first one  ·  Esc: Select"),
    "tip.unjoin_geometry": ("Desunir «{a}» e «{b}»", "Unjoin “{a}” and “{b}”"),
    "tip.join_geometry": ("Unir «{a}» e «{b}»", "Join “{a}” and “{b}”"),
    "err.join_geometry_pick": ("Clique num elemento do modelo (parede, laje, pilar, viga…).",
                               "Click an element of the model (wall, slab, column, beam…)."),
    "info.unjoin_geometry": ("«{a}» e «{b}» desunidos: a linha entre eles vê-se no corte e nas vistas. Ctrl+Z desfaz.",
                             "“{a}” and “{b}” unjoined: the line between them shows in the cut and the views. Ctrl+Z "
                             "undoes."),
    "info.unjoin_geometry_same": ("«{a}» e «{b}» já estavam desunidos.", "“{a}” and “{b}” were unjoined already."),
    "info.join_geometry": ("«{a}» e «{b}» unidos de novo: sem linha onde o material continua. Ctrl+Z desfaz.",
                           "“{a}” and “{b}” joined again: no line where the material goes on. Ctrl+Z undoes."),
    "info.join_geometry_same": ("«{a}» e «{b}» já estavam unidos (o programa une sozinho os elementos que se tocam; só "
                                "os desunidos à mão se unem aqui).",
                                "“{a}” and “{b}” were joined already (the program joins elements that touch by "
                                "itself; only those unjoined by hand are joined here)."),
    "cmd.unjoin_geometry": ("Desunir geometria", "Unjoin geometry"),
    "cmd.join_geometry": ("Unir geometria", "Join geometry"),
    # patterns aligned by hand (0.332)
    "align.pattern_move": ("Alinhar o padrão: mover {d}", "Align the pattern: move {d}"),
    "align.pattern_turn": ("Alinhar o padrão: rodar {a}", "Align the pattern: turn {a}"),
    "align.pattern_there": ("O padrão já está alinhado aqui", "The pattern is aligned here already"),
    "align.pattern_across": ("A referência atravessa esta face: escolha uma que fique sobre ela",
                             "The reference goes across this face: choose one lying on it"),
    "cmd.align_pattern": ("Alinhar padrão", "Align pattern"),
    "info.pattern_aligned": ("Padrão de «{name}» alinhado ({how}): acompanha o elemento. Clique noutra linha, ou "
                             "Esc. Ctrl+Z desfaz.",
                             "“{name}”'s pattern aligned ({how}): it follows the element. Click another line, or "
                             "Esc. Ctrl+Z undoes."),
    "info.pattern_there": ("O padrão de «{name}» já está alinhado com a referência.",
                           "“{name}”'s pattern is aligned with the reference already."),
    "act.reset_patterns": ("Repor os padrões alinhados", "Reset the aligned patterns"),
    "tip.reset_patterns": ("Os padrões dos elementos selecionados (azulejo, tijolo…) voltam a ficar como estavam "
                           "antes de alinhados à mão.",
                           "The selected elements' patterns (tiles, bricks…) go back to how they were before being "
                           "aligned by hand."),
    "pick.reset_patterns": ("Clique nos elementos cujos padrões voltam a ficar como estavam.",
                            "Click the elements whose patterns go back to how they were."),
    "info.patterns_reset": ("Padrões de {n} elemento(s) como estavam antes de alinhados. Ctrl+Z desfaz.",
                            "Patterns of {n} element(s) as they were before being aligned. Ctrl+Z undoes."),
    "info.patterns_not_aligned": ("Os padrões destes elementos não foram alinhados à mão (Modificar ▸ Alinhar).",
                                  "These elements' patterns were not aligned by hand (Modify ▸ Align)."),
    "align.grid": ("Eixo {tag}", "Axis {tag}"),
    "align.edge": ("Aresta", "Edge"),
    "align.line": ("Linha", "Line"),                                                       # (0.449)
    "align.face": ("Face da parede", "Wall face"),
    "align.not_parallel": ("Não é paralela à referência", "Not parallel to the reference"),
    "align.move": ("Alinhar: mover {d}", "Align: move {d}"),
    "err.align_reference": ("Clique num eixo da grelha, numa linha, numa aresta ou num elemento.",
                            "Click a grid axis, a line, an edge or an element."),
    "err.align_face": ("Clique numa linha, aresta ou face paralela à referência (de qualquer elemento).",
                       "Click a line, an edge or a face parallel to the reference (of any element)."),
    "info.align_reference": ("Referência: {what}. Agora o que alinhar (linha, aresta, face).",
                             "Reference: {what}. Now what to align (a line, an edge, a face)."),
    "info.aligned": ("«{name}» alinhado ({d}). Clique noutro, ou Esc. Ctrl+Z desfaz.",
                     "“{name}” aligned ({d}). Click another one, or Esc. Ctrl+Z undoes."),
    "info.align_there": ("«{name}» já está alinhado com a referência.", "“{name}” is aligned with the reference "
                         "already."),                                                      # (0.449)
    "refuse.align_across_wall": ("uma porta ou janela só se alinha ao longo da sua parede",
                                 "a door or window aligns only along its wall"),
    "refuse.align_not_moved": ("não se pode mover", "it cannot be moved"),
    # tops tied to a slab (0.106)
    "act.attach_top": ("Ligar o topo (laje / cobertura)", "Attach top (slab / roof)"),
    "tip.attach_top": ("As paredes e pilares selecionados sobem (ou descem) até à face de baixo da laje ou "
                       "cobertura selecionada com eles, e acompanham-na quando ela muda",
                       "The walls and columns selected reach up (or down) to the underside of the slab or roof "
                       "selected with them, and follow it when it changes"),
    "cmd.attach_top": ("Ligar o topo", "Attach top"),
    "info.attach_top_select": ("Selecione as paredes ou pilares e uma laje ou cobertura (Shift + clique) para ligar "
                               "o topo.",
                               "Select the walls or columns and one slab or roof (Shift + click) to attach their "
                               "tops."),
    "info.attach_top": ("{n} elemento(s) ligados pelo topo à face de baixo de «{slab}»: acompanham-na. Ctrl+Z "
                        "desfaz.",
                        "{n} element(s) attached by their top to the underside of “{slab}”: they follow it. Ctrl+Z "
                        "undoes."),
    "props.top_slab": ("Laje «{name}» (face de baixo)", "Slab “{name}” (underside)"),
    "refuse.no_slab": ("essa laje já não existe", "that slab no longer exists"),
    # merge walls, orthogonalize, let joints go (0.105)
    "act.merge_walls": ("Juntar paredes", "Merge walls"),
    "tip.merge_walls": ("As duas paredes selecionadas, em linha e de ponta a ponta, ficam uma só (com as portas e "
                        "janelas das duas)",
                        "The two walls selected, in line and end to end, become one (with the doors and windows "
                        "of both)"),
    "act.orthogonalize": ("Ortogonalizar", "Orthogonalize"),
    "tip.orthogonalize": ("As paredes selecionadas quase a direito (até 5°) ficam exatamente no eixo vermelho ou "
                          "verde; as ligadas acompanham",
                          "The walls selected that are nearly straight (up to 5°) go exactly along the red or "
                          "green axis; those joined to them follow"),
    "act.unjoin_walls": ("Soltar ligações", "Disallow joins"),
    "tip.unjoin_walls": ("As paredes selecionadas ficam onde estão, mas deixam de acompanhar as paredes onde "
                         "ligam",
                         "The walls selected stay where they are but no longer follow the walls they meet"),
    "cmd.merge_walls": ("Juntar paredes", "Merge walls"),
    "cmd.orthogonalize": ("Ortogonalizar", "Orthogonalize"),
    "cmd.unjoin_walls": ("Soltar ligações", "Disallow joins"),
    "info.merged": ("«{b}» juntou-se a «{a}»: uma só parede. Ctrl+Z desfaz.",
                    "“{b}” merged into “{a}”: one wall. Ctrl+Z undoes."),
    "info.orthogonalized": ("{n} parede(s) ficaram exatamente a direito. Ctrl+Z desfaz.",
                            "{n} wall(s) now exactly straight. Ctrl+Z undoes."),
    "info.orthogonalized_none": ("Nenhuma parede selecionada estava quase a direito (até 5°) sem já o estar.",
                                 "No wall selected was nearly straight (up to 5°) without being so already."),
    "info.unjoined": ("{n} ligação(ões) soltas: as paredes ficam onde estão. Ctrl+Z desfaz.",
                      "{n} join(s) let go: the walls stay where they are. Ctrl+Z undoes."),
    "info.unjoined_none": ("As paredes selecionadas não estavam ligadas a outras.",
                           "The walls selected were not joined to others."),
    # (0.302) Attach / detach base — Revit's, on the tab Modify | Walls
    "act.attach_base": ("Ligar a base", "Attach base"),
    "tip.attach_base": ("As paredes e pilares selecionados descem (ou sobem) até à face de cima da laje ou sapata "
                        "selecionada com eles (Shift + clique), e acompanham-na; o topo fica onde está",
                        "The walls and columns selected go down (or up) to the top face of the slab or footing "
                        "selected with them (Shift + click), and follow it; their top stays where it is"),
    "cmd.attach_base": ("Ligar a base", "Attach base"),
    "info.attach_base_select": ("Selecione as paredes ou pilares e uma laje ou sapata por baixo (Shift + clique) "
                                "para ligar a base.",
                                "Select the walls or columns and a slab or footing under them (Shift + click) to "
                                "attach their base."),
    "info.attach_base": ("{n} elemento(s) assentes na face de cima de «{slab}»: acompanham-na. Ctrl+Z desfaz.",
                         "{n} element(s) standing on the top face of “{slab}”: they follow it. Ctrl+Z undoes."),
    "act.detach_base": ("Desligar a base", "Detach base"),
    "tip.detach_base": ("As paredes e pilares selecionados deixam de acompanhar a laje ou sapata por baixo",
                        "The walls and columns selected no longer follow the slab or footing under them"),
    "cmd.detach_base": ("Desligar a base", "Detach base"),
    "info.detach_base": ("{n} elemento(s) desligados pela base: ficam onde estão. Ctrl+Z desfaz.",
                         "{n} element(s) detached by their base: they stay where they are. Ctrl+Z undoes."),
    "info.detach_base_none": ("Nenhum elemento selecionado está ligado pela base a uma laje ou sapata.",
                              "None of the elements selected is attached by its base to a slab or footing."),
    # (0.299) Flip wall, Allow joins — Revit's, on the tab Modify | Walls
    "act.flip_walls": ("Virar a parede", "Flip wall"),
    "tip.flip_walls": ("O interior e o exterior das paredes selecionadas trocam: as camadas passam para o outro lado "
                       "(o isolamento de fora vem para dentro). A parede, as ligações, as portas e as janelas ficam "
                       "onde estão",
                       "The inside and outside of the walls selected trade places: their layers go to the other side "
                       "(an insulation outside comes inside). The wall, its joins, doors and windows stay where they "
                       "are"),
    "cmd.flip_walls": ("Virar a parede", "Flip wall"),
    "info.flip_walls": ("{n} parede(s) viradas: as camadas trocaram de lado. Ctrl+Z desfaz.",
                        "{n} wall(s) flipped: their layers changed sides. Ctrl+Z undoes."),
    "info.flip_walls_none": ("Selecione paredes com camadas para as virar.", "Select walls with layers to flip them."),
    "refuse.no_layers": ("a parede não tem camadas", "the wall has no layers"),
    "act.join_wall_ends": ("Ligar as pontas", "Allow joins"),
    "tip.join_wall_ends": ("As pontas soltas das paredes selecionadas voltam a ligar-se à parede que tocam (em canto "
                           "ou em T), como ao desenhá-las: passam a acompanhá-la",
                           "The free ends of the walls selected join the wall they touch again (a corner or a T), as "
                           "when they were drawn: they follow it again"),
    "cmd.join_wall_ends": ("Ligar as pontas", "Allow joins"),
    "info.join_wall_ends": ("{n} parede(s) ligadas de novo nos cantos. Ctrl+Z desfaz.",
                            "{n} wall(s) joined again at their corners. Ctrl+Z undoes."),
    "info.join_wall_ends_none": ("Nenhuma ponta solta das paredes selecionadas toca outra parede (a menos de meia "
                                 "espessura).",
                                 "No free end of the walls selected touches another wall (within half a thickness)."),
    "rib.short.join_wall_ends": ("Ligar as\npontas", "Allow\njoins"),
    # (0.298) Reset profile, Detach top — Revit's, on the tab Modify | Walls
    "act.reset_profile": ("Repor perfil", "Reset profile"),
    "tip.reset_profile": ("As paredes selecionadas voltam a ser retângulos no alçado, com a altura mais alta do "
                          "perfil (e deixam de seguir uma cobertura)",
                          "The walls selected are rectangles in elevation again, as tall as their profile's top (and "
                          "no longer follow a roof)"),
    "cmd.reset_profile": ("Repor perfil", "Reset profile"),
    "info.reset_profile": ("{n} parede(s) voltaram a ser retângulos no alçado. Ctrl+Z desfaz.",
                           "{n} wall(s) are rectangles in elevation again. Ctrl+Z undoes."),
    "info.reset_profile_none": ("Nenhuma parede selecionada tem um perfil desenhado.",
                                "None of the walls selected has a drawn profile."),
    "act.detach_top": ("Desligar o topo", "Detach top"),
    "tip.detach_top": ("As paredes e pilares selecionados deixam de seguir a laje ou a cobertura por cima: ficam "
                       "com a altura que têm",
                       "The walls and columns selected no longer follow the slab or roof over them: they keep the "
                       "height they have"),
    "cmd.detach_top": ("Desligar o topo", "Detach top"),
    "info.detach_top": ("{n} elemento(s) desligados da laje ou cobertura: ficam com a altura que têm. Ctrl+Z desfaz.",
                        "{n} element(s) detached from the slab or roof: they keep their height. Ctrl+Z undoes."),
    "info.detach_top_none": ("Nenhum elemento selecionado está ligado pelo topo a uma laje ou cobertura.",
                             "None of the elements selected is attached by its top to a slab or roof."),
    "refuse.merge_different": ("as paredes têm tipos, bases ou alturas diferentes",
                               "the walls have different types, bases or heights"),
    "refuse.merge_not_in_line": ("as paredes não estão em linha", "the walls are not in line"),
    "refuse.merge_apart": ("as paredes não se tocam de ponta a ponta", "the walls do not touch end to end"),
    # curved walls (0.103)
    "wallshape.arc": ("Arco (início, fim, raio)", "Arc (start, end, radius)"),
    "wallshape.arc_center": ("Arco por centro e pontas", "Center-ends arc"),
    "wallshape.poly_in": ("Polígono inscrito", "Inscribed polygon"),
    "wallshape.poly_out": ("Polígono circunscrito", "Circumscribed polygon"),
    "hint.wall.loop_ref": ("({type}, desenhada {ref}; Tab muda.)", "({type}, drawn {ref}; Tab changes it.)"),
    "info.wall_polygon": ("{n} paredes em polígono regular ({type}, desenhadas {ref}), ligadas nos cantos. Ctrl+Z "
                          "desfaz.", "{n} walls in a regular polygon ({type}, drawn {ref}), joined at the corners. "
                          "Ctrl+Z undoes."),
    "wallshape.arc_tangent": ("Arco tangente na ponta", "Tangent end arc"),
    "hint.wall.centre_0": ("Arco por centro e pontas — {type}, desenhada {ref}: clique no centro do arco.",
                           "Center-ends arc — {type}, drawn {ref}: click the arc's centre."),
    "hint.wall.centre_1": ("Clique no início do arco: dá o raio (ou digite o raio + Enter). Esc cancela.",
                           "Click the arc's start: it gives the radius (or type the radius + Enter). Esc cancels."),
    "hint.wall.centre_2": ("Clique no fim do arco: vira para o lado para onde leva o rato (ou digite o ângulo em graus "
                           "+ Enter). Desenhada {ref} (Tab muda). Esc cancela.",
                           "Click the arc's end: it turns the way you take the mouse (or type the angle in degrees "
                           "+ Enter). Drawn {ref} (Tab changes it). Esc cancels."),
    "hint.wall.tangent_0": ("Arco tangente na ponta — {type}: clique na ponta de uma parede; o arco sai dela, "
                            "tangente.",
                            "Tangent end arc — {type}: click a wall's end; the arc leaves it, tangent."),
    "hint.wall.tangent_1": ("Clique no fim do arco (ou digite a distância + Enter); os arcos seguem tangentes, em "
                            "cadeia — escolha «Linha» na barra e a cadeia segue a direito. Desenhada {ref}. Esc "
                            "termina.",
                            "Click the arc's end (or type the distance + Enter); the arcs go on tangent, in a chain "
                            "— choose «Line» on the bar and the chain goes on straight. Drawn {ref}. Esc ends."),
    "tip.wall_tangent_none": ("Leve o rato à ponta de uma parede", "Take the mouse to a wall's end"),
    "wallshape.circle": ("Círculo", "Circle"),
    "hint.wall.arc_start": ("{type}, desenhada {ref}: clique no início do arco.",
                            "{type}, drawn {ref}: click the arc's start."),
    "hint.wall.arc_end": ("Clique no fim do arco (ou digite a distância + Enter). Esc cancela.",
                          "Click the arc's end (or type the distance + Enter). Esc cancels."),
    "hint.wall.arc_bulge": ("Mova o rato para curvar e clique (ou digite o raio + Enter): a parede curva, desenhada "
                            "{ref} (Tab muda). Esc cancela.",
                            "Move the mouse to bend it and click (or type the radius + Enter): the curved wall, "
                            "drawn {ref} (Tab changes it). Esc cancels."),
    "hint.wall.circle_start": ("{type}, desenhada {ref}: clique no centro do círculo.",
                               "{type}, drawn {ref}: click the circle's centre."),
    "hint.wall.circle_end": ("Clique num ponto do círculo ou digite o raio + Enter: uma parede circular, desenhada "
                             "{ref} (Tab muda). Esc cancela.",
                             "Click a point of the circle or type the radius + Enter: a round wall, drawn {ref} "
                             "(Tab changes it). Esc cancels."),
    "tip.wall_radius": ("raio {r}", "radius {r}"),
    "info.wall_arc": ("Parede curva de raio {r} ({a}°, {l} pelo eixo), desenhada {ref} ({type}). Ctrl+Z desfaz.",
                      "Curved wall of radius {r} ({a}°, {l} along its axis), drawn {ref} ({type}). Ctrl+Z undoes."),
    "info.wall_circle": ("Parede circular de raio {r} ({l} pelo eixo), desenhada {ref} ({type}). Ctrl+Z desfaz.",
                         "Round wall of radius {r} ({l} along its axis), drawn {ref} ({type}). Ctrl+Z undoes."),
    "err.wall_curve_small": ("Essa curva é apertada demais para a espessura da parede.",
                             "That curve is too tight for the wall's thickness."),
    "err.wall_arc_radius": ("O raio tem de ser pelo menos metade da distância entre as pontas ({c}).",
                            "The radius must be at least half the distance between the ends ({c})."),
    "props.radius_axis": ("Raio (eixo)", "Radius (axis)"),
    "props.sweep": ("Abertura", "Sweep"),
    "props.length_axis": ("Comprimento (eixo)", "Length (axis)"),
    "err.pp_sizes_in_panel": ("As medidas deste elemento mudam-se no painel Propriedades.",
                              "This element's sizes change in the Properties panel."),
    # ramps (0.101)
    "tool.ramp": ("Rampa", "Ramp"),
    "elem.ramp": ("Rampa", "Ramp"),
    "cmd.ramp": ("Rampa", "Ramp"),
    "ctx.width": ("Largura", "Width"),
    "ctx.rise": ("Desnível", "Rise"),
    "props.width": ("Largura", "Width"),
    "props.rise": ("Desnível", "Rise"),
    "props.slope": ("Inclinação", "Slope"),
    "hint.ramp.start": ("Rampa ({type}, {w} de largura, a subir {h}): clique no meio do pé da rampa.",
                        "Ramp ({type}, {w} wide, rising {h}): click the middle of the ramp's foot."),
    "hint.ramp.end": ("Clique no meio da cabeça da rampa ou digite o comprimento + Enter («6;0,5» muda também o "
                      "desnível). Esc cancela.",
                      "Click the middle of the ramp's head or type its length + Enter (\"6;0.5\" sets the rise "
                      "too). Esc cancels."),
    "tip.ramp_slope": ("Inclinação {s}", "Slope {s}"),
    "info.ramp": ("Rampa de {l} a subir {h} (inclinação {s}) criada ({type}). Ctrl+Z desfaz.",
                  "{l} ramp rising {h} (slope {s}) created ({type}). Ctrl+Z undoes."),
    "err.pp_slab_outline": ("Esta laje é um polígono ou um círculo: mude-a com «Editar contorno» (ou pelo raio, no "
                            "painel Propriedades).",
                            "This slab is a polygon or a circle: change it with “Edit outline” (or its radius, in "
                            "the Properties panel)."),
    # storeys (levels)
    "storeys.title": ("Pavimentos", "Storeys"),
    # (0.462) the levels' look, in the panel
    "storeys.look": ("Aparência dos níveis", "Levels' look"),
    "storeys.look_tip": ("Como os níveis aparecem nos cortes, alçados, folhas, PDF, DXF e no 3D: a linha, a cor, a "
                         "extremidade e o texto", "How the levels look in the sections, elevations, sheets, PDF, DXF and "
                         "in 3D: the line, the colour, the end and the text"),
    "storeys.look_line": ("Linha", "Line"),
    "storeys.look_colour": ("Cor", "Colour"),
    "storeys.look_mark": ("Extremidade", "End"),
    "storeys.look_ends": ("Pontas", "Ends"),
    "storeys.look_label": ("Texto", "Text"),
    "storeys.look_3d": ("Mostrar os níveis no 3D", "Show the levels in 3D"),
    "storeys.look_over": ("Linha por cima do desenho", "Line over the drawing"),
    "storeys.look_over_tip": ("Desligada, a linha do nível pára antes do edifício: fica só dos lados, com o símbolo e o "
                              "texto (nos cortes, alçados, folhas, PDF e DXF)", "Off, the level's line stops short of "
                              "the building: only its sides, with the symbol and the text (in sections, elevations, "
                              "sheets, PDF and DXF)"),
    "storeys.colour.auto": ("Automática (a do desenho)", "Automatic (the drawing's)"),
    "storeys.colour.black": ("Preto", "Black"),
    "storeys.colour.blue": ("Azul", "Blue"),
    "storeys.colour.red": ("Vermelho", "Red"),
    "storeys.colour.green": ("Verde", "Green"),
    "storeys.colour.grey": ("Cinzento", "Grey"),
    "storeys.colour.other": ("Outra…", "Other…"),
    "cmd.level_style": ("Aparência dos níveis", "Levels' look"),
    # (0.464) the levels' ends dragged in a view
    "info.level_chosen": ("Níveis escolhidos: arraste uma pega para encurtar ou alongar as linhas de nível desta vista "
                          "(todas juntas), afastando os símbolos do modelo. Esc larga-os.",
                          "Levels picked: drag a grip to shorten or lengthen this view's level lines (all together), "
                          "moving their symbols off the model. Esc lets them go."),
    "hint.level_chosen": ("Níveis escolhidos: arraste uma pega (no 3D, um canto do anel) para mudar onde as linhas "
                          "acabam nesta vista. Esc larga-os.", "Levels picked: drag a grip (in 3D, a corner of the "
                          "ring) to change where the lines end in this view. Esc lets them go."),
    "hint.level_grip": ("Leve a ponta do nível para onde quer e solte (ou clique). Esc cancela.",
                        "Take the level's end where you want and let go (or click). Esc cancels."),
    "info.level_ends": ("As linhas de nível desta vista acabam agora onde as deixou (os símbolos com elas). Ctrl+Z "
                        "desfaz.", "This view's level lines now end where you left them (their symbols with them). "
                        "Ctrl+Z undoes."),
    "info.level_style": ("Aparência dos níveis mudada: cortes, alçados, folhas e 3D já a seguem. Ctrl+Z desfaz.",
                         "The levels' look changed: sections, elevations, sheets and 3D follow it. Ctrl+Z undoes."),
    "storeys.name": ("Pavimento", "Storey"),
    "storeys.level": ("Cota", "Level"),
    "storeys.new": ("+ Novo", "+ New"),
    "storeys.delete": ("Apagar", "Delete"),
    "storeys.only_active": ("No 3D, ver só o pavimento ativo", "In 3D, show the active storey only"),   # (0.465)
    "storeys.default_name": ("Piso {n}", "Level {n}"),
    "storeys.status": ("Pavimento: {name} ({z})", "Storey: {name} ({z})"),
    "act.storey_new": ("Novo pavimento", "New storey"),
    "act.storey_up": ("Pavimento acima", "Storey above"),
    "act.storey_down": ("Pavimento abaixo", "Storey below"),
    "cmd.storey": ("Pavimento", "Storey"),
    "info.storey_new": ("Pavimento \"{name}\" criado à cota {z}. Agora desenha-se nele (duplo clique no nome ou na "
                        "cota para os mudar).",
                        "Storey \"{name}\" created at level {z}. You now draw on it (double-click the name or the "
                        "level to change them)."),
    "info.storey_active": ("A desenhar no pavimento \"{name}\" ({z}).", "Drawing on storey \"{name}\" ({z})."),
    "info.storey_moved": ("\"{name}\" passou para a cota {z}: {n} elemento(s) acompanharam.",
                          "\"{name}\" moved to level {z}: {n} element(s) moved along."),
    "refuse.last_storey": ("o edifício precisa de pelo menos um pavimento", "the building needs at least one storey"),
    "refuse.storey_not_empty": ("o pavimento tem elementos (apague-os ou mude-os primeiro)",
                                "the storey has elements (delete or move them first)"),
    "hint.slab.end": ("Clique no canto oposto ou digite as medidas (ex.: 6;4) e Enter. Esc cancela.",
                      "Click the opposite corner or type the size (e.g. 6;4) and Enter. Esc cancels."),
    "vcb.length": ("Comprimento", "Length"),
    "vcb.height": ("Altura", "Height"),
    "snap.axis_x": ("No eixo vermelho", "On red axis"),
    "snap.axis_y": ("No eixo verde", "On green axis"),
    "snap.axis_z": ("No eixo azul", "On blue axis"),
    "snap.close": ("Fechar contorno", "Close the outline"),
    "snap.wall_axis": ("Eixo da parede", "Wall axis"),
    "snap.intersection": ("Interseção", "Intersection"),
    "snap.on_guide": ("Na guia", "On guide"),
    "snap.align_x": ("Alinhado com o ponto (vermelho)", "Aligned with the point (red)"),
    "snap.align_y": ("Alinhado com o ponto (verde)", "Aligned with the point (green)"),
    "snap.align_z": ("Alinhado com o ponto (azul)", "Aligned with the point (blue)"),
    "snap.crossing": ("Cruzamento de alinhamentos", "Where the alignments cross"),
    "snap.parallel": ("Paralelo à aresta", "Parallel to the edge"),
    "snap.parallel_to": ("Paralela (à parede ou linha acesa)", "Parallel (to the wall or line lit)"),   # (0.448)
    "snap.angle": ("A {a}°", "At {a}°"),                                                              # (0.448)
    "snap.perpendicular": ("Perpendicular à aresta", "Perpendicular to the edge"),
    "snap.perpendicular_foot": ("Perpendicular à aresta (pé)", "Perpendicular to the edge (foot)"),
    "snap.extension": ("No prolongamento da aresta", "On the edge's extension"),
    "snap.locked": ("{what} — bloqueado (Shift)", "{what} — locked (Shift)"),
    "hint.start_typed": ("Para começar a uma distância de um ponto: leve o cursor desde esse ponto ao longo de um "
                         "alinhamento (tracejado) ou de uma aresta — a cota azul mostra a distância — escreva-a e "
                         "Enter.",
                         "To start at a distance from a point: take the cursor from that point along an alignment "
                         "(dashed) or an edge — the blue dimension shows the distance — type it and press Enter."),
    "info.start_typed": ("Começa a {l} do ponto seguido. Continue a desenhar.",
                         "Starts {l} from the point followed. Go on drawing."),
    "hint.temp_dim": ("Escreva a nova medida desta cota (a realçada, entre [ ]) e Enter. Esc: deixar.",
                      "Type this dimension's new value (the one picked out, in [ ]) and press Enter. Esc: leave it."),
    # (0.361) a wall's relations to the walls round it
    "hint.wall_dims_axes": ("Cotas de eixo a eixo até às paredes à volta (a verde). Clique num valor para o "
                            "escrever; clique na linha de uma cota verde para passar a face a face.",
                            "Axis-to-axis dimensions to the walls round it (in green). Click a value to type it; "
                            "click a green dimension's line for face to face."),
    "hint.wall_dims_faces": ("Cotas de face a face (vãos livres) até às paredes à volta (a verde). Clique num valor "
                             "para o escrever; clique na linha de uma cota verde para passar a eixo a eixo.",
                             "Face-to-face dimensions (the clear distances) to the walls round it (in green). Click a "
                             "value to type it; click a green dimension's line for axis to axis."),
    "act.dims_axes": ("Eixo a eixo", "Axis to axis"),
    "act.dims_faces": ("Face a face", "Face to face"),
    "tip.dims_axes": ("As cotas da parede escolhida até às paredes à volta medem de eixo a eixo",
                      "The chosen wall's dimensions to the walls round it measure from axis to axis"),
    "tip.dims_faces": ("As cotas da parede escolhida até às paredes à volta medem de face a face (os vãos livres)",
                       "The chosen wall's dimensions to the walls round it measure from face to face (the clear "
                       "distances)"),
    "info.dims_axes": ("Cotas das paredes de eixo a eixo.", "Walls' dimensions from axis to axis."),
    "info.dims_faces": ("Cotas das paredes de face a face (vãos livres).",
                        "Walls' dimensions from face to face (the clear distances)."),
    "info.temp_dim": ("Cota mudada para {v} (Ctrl+Z desfaz).", "Dimension changed to {v} (Ctrl+Z undoes)."),
    "cmd.line_length": ("Comprimento da linha", "Line length"),
    "cmd.line_angle": ("Ângulo da linha", "Line angle"),
    "cmd.line_edit": ("Mudar linha", "Change line"),
    "hint.grip": ("Leve a pega até ao sítio (snaps e alinhamentos) e clique — ou escreva a distância e Enter. "
                  "Esc: deixar como estava.",
                  "Take the grip where it goes (snaps and alignments) and click — or type the distance and press "
                  "Enter. Esc: leave it as it was."),
    "info.grip_moved": ("Linha mudada ({d}). Ctrl+Z desfaz.", "Line changed ({d}). Ctrl+Z undoes."),
    "info.grip_moved_joined": ("Linha mudada ({d}); as linhas ligadas a ela acompanharam. Ctrl+Z desfaz.",
                               "Line changed ({d}); the lines joined to it followed. Ctrl+Z undoes."),
    "refuse.too_short": ("um segmento ficaria com menos de 1 mm", "a segment would be shorter than 1 mm"),
    "refuse.vertical_line": ("uma linha a prumo não tem ângulo na planta", "a vertical line has no angle in plan"),
    "props.segment": ("Segmento {n}", "Segment {n}"),
    "props.line_angle": ("Ângulo (na planta)", "Angle (in plan)"),
    "props.line_start": ("Início (x; y; z)", "Start (x; y; z)"),
    "props.line_end": ("Fim (x; y; z)", "End (x; y; z)"),
    "props.lines_hint": ("Mudar à mão: arraste os quadrados das pontas ou os losangos do meio (ou clique na cota "
                         "azul e escreva). As linhas ligadas acompanham.",
                         "By hand: drag the squares on the ends or the diamonds in the middles (or click the blue "
                         "dimension and type). The lines joined follow."),
    "info.wall_joined": ("Canto unido à parede existente.", "Corner joined to the existing wall."),
    "info.wall_continue": ("A continuar «{name}»: clique onde acaba a parede nova (Esc para).",
                           "Going on from «{name}»: click where the new wall ends (Esc stops)."),     # (0.353)
    # Groups (Revit model groups) and typical floors
    "act.group_make": ("Criar grupo…", "Make group…"),
    "act.group_ungroup": ("Desagrupar", "Ungroup"),
    "act.repeat_storeys": ("Repetir nos pavimentos…", "Repeat on storeys…"),
    "cmd.group": ("Grupo", "Group"),
    "cmd.ungroup": ("Desagrupar", "Ungroup"),
    "cmd.repeat": ("Repetir nos pavimentos", "Repeat on storeys"),
    "group.default_name": ("Grupo {n}", "Group {n}"),
    "props.group": ("Grupo", "Group"),
    "props.group_value": ("Grupo — {n} cópia(s), {m} elementos", "Group — {n} cop(ies), {m} elements"),
    "props.group_member": ("{name} ({n} cópia(s)): as mudanças repetem-se em todas",
                           "{name} ({n} cop(ies)): changes are repeated in all"),
    "props.group_hint": ("Clique outra vez num elemento para o mudar sozinho: a mudança repete-se em todas as "
                         "cópias do grupo.",
                         "Click an element again to change it on its own: the change is repeated in every copy "
                         "of the group."),
    "repeat.ask": ("Repetir a seleção, no mesmo sítio, nestes pavimentos:",
                   "Repeat the selection, at the same place, on these storeys:"),
    "err.group_pick": ("Selecione um grupo (Espaço + clique num dos seus elementos).",
                       "Select a group (Space + click one of its elements)."),
    "err.repeat_storeys": ("Só há um pavimento: crie outro no painel Pavimentos.",
                           "There is only one storey: add one in the Storeys panel."),
    "refuse.already_grouped": ("um dos elementos já pertence a um grupo", "one of the elements is already in a group"),
    "info.group_made": ("Grupo \"{name}\" criado. Copie-o (Mover + Ctrl, ou Repetir nos pavimentos): mudar um "
                        "elemento numa cópia muda-o em todas.",
                        "Group \"{name}\" made. Copy it (Move + Ctrl, or Repeat on storeys): changing an element in "
                        "one copy changes it in all."),
    "info.ungrouped": ("Desagrupado: estes elementos ficam independentes das outras cópias.",
                       "Ungrouped: these elements no longer follow the other copies."),
    "info.repeated": ("Repetido em {n} pavimento(s).", "Repeated on {n} storey(s)."),
    # Components
    "act.component_make": ("Criar componente…", "Make component…"),
    "act.component_edit": ("Editar componente", "Edit component"),
    "act.component_close": ("Fechar componente", "Close component"),
    "cmd.component": ("Componente", "Component"),
    "cmd.component_place": ("Inserir componente", "Place component"),
    "cmd.import_components": ("Trazer componentes", "Bring components"),
    "cmd.component_edit": ("Editar componente", "Edit component"),
    "component.default_name": ("Componente {n}", "Component {n}"),
    "cat.furniture": ("Mobiliário", "Furniture"),
    "cat.sanitary": ("Louça sanitária", "Sanitary fixture"),
    "cat.generic": ("Elemento genérico", "Generic element"),
    "props.component": ("Componente", "Component"),
    "props.component_value": ("{name} ({n} cópia(s))", "{name} ({n} cop(ies))"),
    "props.component_hint": ("Para mudar a forma: Gerenciar ▸ Componentes ▸ Editar componente (todas as cópias "
                             "mudam).",
                             "To change its shape: Manage ▸ Components ▸ Edit component (all copies change)."),
    "props.component_editing": ("A editar o componente \"{name}\"", "Editing component \"{name}\""),
    "props.component_close_hint": ("Mude a forma (Push/Pull, Retângulo, Linha…) e depois Gerenciar ▸ Componentes ▸ "
                                   "Fechar componente.",
                                   "Change its shape (Push/Pull, Rectangle, Line…), then Manage ▸ Components ▸ Close "
                                   "component."),
    "err.pp_component": ("Componente: para mudar a forma, Gerenciar ▸ Componentes ▸ Editar componente (todas as "
                         "cópias mudam).",
                         "Component: to change its shape, Manage ▸ Components ▸ Edit component (all copies change)."),
    "info.component_made": ("Componente \"{name}\" criado. Copie-o com Mover + Ctrl: as cópias partilham a forma.",
                            "Component \"{name}\" made. Copy it with Move + Ctrl: the copies share its shape."),
    "info.component_editing": ("A editar \"{name}\": mude a forma e depois Gerenciar ▸ Componentes ▸ Fechar "
                               "componente.",
                               "Editing \"{name}\": change its shape, then Manage ▸ Components ▸ Close component."),
    "info.component_closed": ("Componente \"{name}\" atualizado: {n} cópia(s) mudaram.",
                              "Component \"{name}\" updated: {n} cop(ies) changed."),
    # Move and Rotate
    "tool.move": ("Mover", "Move"),
    "tool.rotate": ("Rodar", "Rotate"),
    "cmd.move": ("Mover", "Move"),
    "cmd.rotate": ("Rodar", "Rotate"),
    "vcb.angle": ("Ângulo", "Angle"),
    "hint.move.start": ("Clique no ponto de base (move o que está selecionado, ou o objeto sob o cursor).",
                        "Click the base point (moves the selection, or the object under the cursor)."),
    "hint.move.end": ("Clique no destino, ou digite a distância (ex.: 1,20) e Enter. Esc cancela.",
                      "Click the destination, or type the distance (e.g. 1.20) and Enter. Esc cancels."),
    "hint.rotate.start": ("Clique no centro da rotação (roda o que está selecionado, ou o objeto sob o cursor).",
                          "Click the centre of rotation (rotates the selection, or the object under the cursor)."),
    "hint.rotate.ref": ("Clique num ponto que dê a direção de partida, ou digite o ângulo (ex.: 90) e Enter.",
                        "Click a point giving the starting direction, or type the angle (e.g. 90) and Enter."),
    "hint.rotate.end": ("Rode o rato e clique (agarra de 15 em 15°), ou digite o ângulo (ex.: 45) e Enter. "
                        "Esc cancela.",
                        "Turn the mouse and click (snaps every 15°), or type the angle (e.g. 45) and Enter. "
                        "Esc cancels."),
    # (0.412) about X, Y or Z, as Blender's R then X / Y / Z
    "hint.rotate.axis": ("  ·  Eixo {a} — X, Y ou Z muda o eixo.", "  ·  Axis {a} — X, Y or Z changes it."),
    "ctx.rotate_axis": ("Eixo", "Axis"),
    "info.rotate_axis": ("Rodar à volta do eixo {a}, pelo centro (X vermelho, Y verde, Z azul). X, Y ou Z muda o "
                         "eixo.",
                         "Rotate about the {a} axis, through the centre (X red, Y green, Z blue). X, Y or Z changes "
                         "the axis."),
    "err.rotate_axis_bim": ("As paredes, lajes e outros elementos BIM só rodam à volta da vertical (Z). À volta de X "
                            "ou Y rodam os esboços: linhas, faces e curvas.",
                            "Walls, slabs and the other BIM elements turn about the vertical (Z) only. Sketches — "
                            "lines, faces, curves — turn about X or Y."),
    # (0.412) the work plane (model/work_plane, tools/work_plane)
    "tool.work_plane": ("Plano de trabalho", "Work plane"),
    "keys.work_plane": ("XY / XZ / YZ: clique onde o plano fica  ·  Face: clique numa face  ·  Esc: sair",
                        "XY / XZ / YZ: click where the plane goes  ·  Face: click a face  ·  Esc: leave"),
    "ctx.work_plane": ("Plano", "Plane"),
    "ctx.work_plane_level": ("Voltar ao nível do piso", "Back to the storey's level"),
    "workplane.short.xy": ("XY (horizontal)", "XY (horizontal)"),
    "workplane.short.xz": ("XZ (vertical)", "XZ (vertical)"),
    "workplane.short.yz": ("YZ (vertical)", "YZ (vertical)"),
    "workplane.short.face": ("Face", "Face"),
    "workplane.xy": ("Plano de trabalho horizontal XY", "Horizontal work plane XY"),
    "workplane.xz": ("Plano de trabalho vertical XZ", "Vertical work plane XZ"),
    "workplane.yz": ("Plano de trabalho vertical YZ", "Vertical work plane YZ"),
    "workplane.face": ("Plano de trabalho na face", "Work plane on the face"),
    "workplane.none": ("Nível do piso", "The storey's level"),
    "hint.work_plane.xy": ("Plano horizontal (XY): clique no ponto por onde passa (a altura). Na barra: XZ, YZ ou Face. "
                           "Esc: sair.",
                           "Horizontal plane (XY): click the point it goes through (its height). On the bar: XZ, YZ "
                           "or Face. Esc: leave."),
    "hint.work_plane.xz": ("Plano vertical ao longo do eixo vermelho (XZ): clique no ponto por onde passa. Na barra: XY, "
                           "YZ ou Face. Esc: sair.",
                           "Vertical plane along the red axis (XZ): click the point it goes through. On the bar: XY, "
                           "YZ or Face. Esc: leave."),
    "hint.work_plane.yz": ("Plano vertical ao longo do eixo verde (YZ): clique no ponto por onde passa. Na barra: XY, "
                           "XZ ou Face. Esc: sair.",
                           "Vertical plane along the green axis (YZ): click the point it goes through. On the bar: XY, "
                           "XZ or Face. Esc: leave."),
    "hint.work_plane.face": ("Clique numa face: o plano dela passa a ser o plano de trabalho. Esc: sair.",
                             "Click a face: its plane becomes the work plane. Esc: leave."),
    "tip.work_plane_no_face": ("Leve o rato a uma face", "Take the mouse to a face"),
    "err.work_plane_no_face": ("Aí não há uma face: clique numa face.", "There is no face there: click a face."),
    "info.work_plane": ("{p}{at}. Na vista 3D, a Linha, o Arco, o Retângulo, o Círculo, a Linha livre e a Bézier "
                        "desenham nele (onde não há uma face por baixo do rato). «Voltar ao nível do piso», na "
                        "ferramenta Plano de trabalho, tira-o.",
                        "{p}{at}. In the 3D view, Line, Arc, Rectangle, Circle, Freehand and Bézier draw on it (where "
                        "there is no face under the mouse). «Back to the storey's level», in the Work plane tool, lets "
                        "it go."),
    "info.work_plane_off": ("Sem plano de trabalho: desenha-se outra vez no nível do piso.",
                            "No work plane: drawing is on the storey's level again."),
    "snap.angle_step": ("Múltiplo de 15°", "Multiple of 15°"),
    "cmd.copy": ("Copiar", "Copy"),
    "hint.copy_mode": ("+ CÓPIA (Ctrl desliga) · ", "+ COPY (Ctrl turns it off) · "),
    "info.copy_on": ("Copiar: ligado — o original fica no sítio. Ctrl de novo para mover.",
                     "Copy: on — the original stays put. Ctrl again to move."),
    "info.copy_off": ("Copiar: desligado — move o original.", "Copy: off — moves the original."),
    "info.copied": ("{n} cópia(s) feita(s). Digite 3x + Enter para mais cópias iguais, /3 para dividir em 3, "
                    "ou outra medida para corrigir.",
                    "{n} cop(ies) made. Type 3x + Enter for more equal copies, /3 to split in 3, "
                    "or another value to correct it."),
    "info.moved": ("{n} objeto(s) movido(s) {d}. Digite outra distância + Enter para corrigir.",
                   "{n} object(s) moved {d}. Type another distance + Enter to correct it."),
    "info.rotated": ("{n} objeto(s) rodado(s) {a}. Digite outro ângulo + Enter para corrigir.",
                     "{n} object(s) rotated {a}. Type another angle + Enter to correct it."),
    "err.nothing_to_move": ("Clique em cima de um objeto (ou selecione primeiro com Espaço + clique).",
                            "Click on an object (or select first with Space + click)."),
    "err.rotate_filling": ("Portas e janelas rodam com a parede: selecione a parede.",
                           "Doors and windows rotate with their wall: select the wall."),
    "err.bad_angle": ("Ângulo inválido: \"{t}\". Exemplos: 90   -45   22,5", "Invalid angle: \"{t}\". Examples: 90   -45   22.5"),
    "refuse.not_movable": ("este elemento não tem uma colocação que se possa mover",
                           "this element has no placement that can be moved"),
    # Line and Tape Measure
    "tool.line": ("Linha", "Line"),
    "tool.tape": ("Fita métrica", "Tape measure"),
    "obj.lines": ("Linhas {n}", "Lines {n}"),
    "obj.arc": ("Arco {n}", "Arc {n}"),                         # (0.373: curves, named by what they are)
    "obj.freehand": ("Linha livre {n}", "Freehand {n}"),
    "obj.bezier": ("Bézier {n}", "Bézier {n}"),
    "cmd.line": ("Linha", "Line"),
    "cmd.face": ("Face", "Face"),
    "cmd.guide": ("Linha guia", "Guide line"),
    "hint.line.start": ("Clique no primeiro ponto (no chão, numa face ou num ponto).",
                        "Click the first point (on the ground, on a face or on a point)."),
    "hint.line.next": ("Clique no ponto seguinte ou digite o comprimento + Enter. Feche o contorno (no 1.º ponto, "
                       "ou noutro ponto ou linha do que desenhou) para fazer a face; uma linha de aresta a aresta "
                       "divide a face. Esc termina.",
                       "Click the next point or type the length + Enter. Close the outline (at the 1st point, or on "
                       "another point or line of what you drew) to make the face; a line from edge to edge divides "
                       "the face. Esc ends."),
    "hint.line.direction": ("Mova o rato na direção da linha e digite de novo o comprimento.",
                            "Move the mouse in the line's direction and type the length again."),
    "info.line": ("Linha de {l}.", "{l} line."),
    "cmd.split_face": ("Dividir a face", "Divide the face"),
    "info.line_on_wall": ("A linha ficou sobre «{wall}» sem a dividir: numa parede ou laje, a linha (ou várias "
                          "seguidas) divide a face quando vai de uma aresta da face até outra aresta (clique em "
                          "cima das arestas).",
                          "The line lies on \"{wall}\" without dividing it: on a wall or slab, a line (or several "
                          "in a row) divides the face when it goes from an edge of the face to another edge (click "
                          "on the edges)."),
    "info.split": ("Face dividida ({n} face(s) cortada(s)). Push/Pull (P) numa parte para a mover só a ela.",
                   "Face divided ({n} face(s) cut). Push/Pull (P) one part to move it alone."),
    "info.split_host": ("A face de «{wall}» ficou dividida em duas partes. Push/Pull (P): empurrar uma para dentro "
                        "faz um nicho ou um vão com essa forma; puxar para fora faz um volume de esboço.",
                        "The face of \"{wall}\" is now divided in two parts. Push/Pull (P): pushing one in makes "
                        "a niche or an opening of that shape; pulling it out makes a sketch volume."),
    "info.face": ("Contorno fechado: face com {n} cantos e {a} m². Para lhe dar altura: P e clique nela.",
                  "Outline closed: face with {n} corners, {a} m². To give it height: P and click it."),
    "info.faces_closed": ("Contorno fechado: {n} faces, {a} m² ao todo. As linhas fora delas ficaram como linhas.",
                          "Outline closed: {n} faces, {a} m² in all. The lines outside them stay lines."),   # (0.372)
    "info.face_closed": ("Contorno fechado: face com {n} cantos e {a} m²; as linhas fora dela ficaram como linhas. "
                         "Para lhe dar altura: P e clique nela.",
                         "Outline closed: face with {n} corners, {a} m²; the lines outside it stay lines. To give it "
                         "height: P and click it."),
    "warn.not_planar": ("O contorno não está num só plano: ficou como linhas (sem face).",
                        "The outline is not on one plane: it stays as lines (no face)."),
    "hint.tape.start": ("Clique numa aresta (para uma linha guia paralela) ou num ponto (para medir).",
                        "Click an edge (for a parallel guide line) or a point (to measure)."),
    "hint.tape.guide": ("Afaste o rato e clique, ou digite a distância (ex.: 1,20) e Enter. Esc cancela.",
                        "Move away and click, or type the distance (e.g. 1.20) and Enter. Esc cancels."),
    "hint.tape.measure": ("Clique no segundo ponto para medir. Esc cancela.",
                          "Click the second point to measure. Esc cancels."),
    "info.guide": ("Linha guia a {d}. Digite outra medida + Enter para a corrigir.",
                   "Guide line at {d}. Type another value + Enter to correct it."),
    "info.measure": ("Distância: {d}.", "Distance: {d}."),
    "act.delete_guides": ("Apagar linhas guia", "Delete guide lines"),
    "info.no_guides": ("Não há linhas guia.", "There are no guide lines."),
    "info.guides_deleted": ("{n} linha(s) guia apagada(s). Ctrl+Z repõe.", "{n} guide line(s) deleted. Ctrl+Z restores."),
    "info.wall": ("Parede de {l} criada ({type}).", "{l} wall created ({type})."),
    "info.closed": ("Contorno fechado: {n} paredes.", "Outline closed: {n} walls."),
    "info.slab": ("Laje {a} × {b} criada ({type}).", "{a} × {b} slab created ({type})."),
    "info.next_pp": ("Retângulo {a} × {b} criado. Para lhe dar altura: P e clique nele.",
                     "Rectangle {a} × {b} created. To give it height: P and click it."),
    "info.next_classify": ("Volume com {d}. Para o tornar BIM: Espaço, clique nele e Modelagem ▸ Criar ▸ Classificar.",
                           "Volume {d} high. To make it BIM: Space, click it and Modelling ▸ Create ▸ Classify."),
    "hint.classify_pick": ("Clique no volume de esboço que quer transformar em \"{type}\". Esc cancela.",
                           "Click the sketch volume to turn into \"{type}\". Esc cancels."),
    "dlg.not_box": ("Este volume não é uma caixa simples (tem nichos, varandas ou está inclinado), por isso não "
                    "pode virar \"{type}\".\n\nDica: use as ferramentas Parede (W) e Laje, ou faça o volume só com "
                    "Retângulo + Push/Pull.",
                    "This volume is not a plain box (it has recesses, balconies or is tilted), so it cannot become "
                    "\"{type}\".\n\nTip: use the Wall (W) and Slab tools, or make the volume with Rectangle + "
                    "Push/Pull only."),
    "err.classify_first": ("Isto ainda é um esboço. Transforme-o em parede (Espaço, clique, Modelagem ▸ Criar ▸ "
                           "Classificar) ou "
                           "desenhe com a ferramenta Parede (W).",
                           "This is still a sketch. Turn it into a wall (Space, click, Modelling ▸ Create ▸ Classify) "
                           "or draw with "
                           "the Wall tool (W)."),
    "elem.door": ("Porta", "Door"),
    "elem.window": ("Janela", "Window"),
    "tool.door": ("Porta", "Door"),
    "tool.window": ("Janela", "Window"),
    "cmd.door": ("Porta", "Door"),
    "cmd.window": ("Janela", "Window"),
    "act.door_types": ("Porta", "Door"),
    "act.window_types": ("Janela", "Window"),
    "hint.opening": ("{type}: passe o cursor sobre uma parede e clique — prende ao meio do compartimento e com a "
                     "ombreira a 0,10 ou 0,20 da gola —, ou digite a distância à extremidade mais próxima (ex.: 0,60) "
                     "e Enter.",
                     "{type}: hover a wall and click — it snaps to the middle of the room and with its jamb 0.10 or "
                     "0.20 from the corner —, or type the distance to the nearest end (e.g. 0.60) and Enter."),
    "vcb.to_end": ("Até à extremidade", "To the end"),
    "snap.wall_center": ("Centro da parede", "Wall centre"),
    "snap.room_middle": ("Meio do compartimento", "Middle of the room"),
    "snap.from_wall": ("Ombreira a {d} da gola", "Jamb {d} from the corner"),
    "err.no_wall": ("Passe o cursor sobre uma face de parede (elemento IFC).", "Hover a wall face (IFC element)."),
    "err.wall_small": ("Esta parede é pequena demais para {type}.", "This wall is too small for {type}."),
    "info.placed": ("{type} colocada em {wall}.", "{type} placed in {wall}."),
    "props.size": ("Dimensões", "Size"),
    "props.host": ("Parede", "Wall"),
    "elem.wall": ("Parede", "Wall"),
    "elem.slab": ("Laje", "Slab"),
    "elem.column": ("Pilar", "Column"),
    "elem.beam": ("Viga", "Beam"),
    "elem.brace": ("Contraventamento", "Brace"),                    # (0.495)
    "elem.purlin": ("Madre", "Purlin"),
    "elem.member": ("Elemento", "Member"),
    "elem.footing": ("Sapata", "Footing"),
    "elem.pipe": ("Tubo", "Pipe"),
    "elem.duct": ("Conduta", "Duct"),
    "cmd.classify": ("Classificar", "Classify"),
    "err.classify_none": ("Selecione primeiro um ou mais volumes de esboço (Espaço + clique).",
                          "First select one or more sketch volumes (Space + click)."),
    "err.classify_refused": ("{n} volume(s) não são caixas simples na vertical e não foram classificados.",
                             "{n} volume(s) are not plain upright boxes and were not classified."),
    "info.classified": ("{n} elemento(s) IFC criado(s): {type}.", "{n} IFC element(s) created: {type}."),
    "warn.adjusted": ("{n} elemento(s) criado(s) com a medida do tipo ({type}), diferente da do volume.",
                      "{n} element(s) created with the type's size ({type}), different from the volume."),
    "err.classify_failed": ("Não foi possível classificar (nada foi alterado):\n{e}",
                            "Could not classify (nothing was changed):\n{e}"),
    "err.pp_bim": ("Elemento IFC: Push/Pull em elementos BIM chega na próxima etapa.",
                   "IFC element: Push/Pull on BIM elements comes in the next step."),
    "props.title": ("Propriedades", "Properties"),
    "quick.title": ("Edição rápida (TAB)", "Quick edit (TAB)"),                                    # (0.354)
    "quick.close": ("Fechar (Esc ou TAB)", "Close (Esc or TAB)"),
    "props.nothing": ("Nada selecionado", "Nothing selected"),
    "props.hint": ("Selecione um volume (Espaço + clique).", "Select a volume (Space + click)."),
    "props.many": ("{n} objetos selecionados", "{n} objects selected"),
    # (0.187) several elements: their common properties, changed in all of them at once
    "props.many_filter": ("Elementos", "Elements"),
    "props.many_all": ("Todos ({n})", "All ({n})"),
    "props.sketches": ("Esboços", "Sketches"),
    "props.varies": ("<vários>", "<varies>"),
    "props.many_too_many": ("Mais de {n} elementos: escolha uma categoria na lista, ou selecione menos, para ver "
                            "e mudar as propriedades comuns.",
                            "More than {n} elements: choose a category in the list, or select fewer, to see and "
                            "change the common properties."),
    "props.many_sketches": ("Há esboços na seleção: escolha uma categoria de elementos na lista para ver e mudar "
                            "as propriedades comuns.",
                            "There are sketches in the selection: choose a category of elements in the list to see "
                            "and change the common properties."),
    "info.edit_many": ("Mudado em {n} elementos. Ctrl+Z desfaz tudo de uma vez.",
                       "Changed in {n} elements. Ctrl+Z undoes it all at once."),
    "props.kind": ("Natureza", "Kind"),
    "props.sketch": ("Esboço (não é IFC)", "Sketch (not IFC)"),
    "props.classify_hint": ("Use Modelagem ▸ Criar ▸ Classificar para o transformar em parede, laje ou pilar.",
                            "Use Modelling ▸ Create ▸ Classify to turn it into a wall, slab or column."),
    "props.class": ("Classe IFC", "IFC class"),
    "props.name": ("Nome", "Name"),
    "props.type": ("Tipo", "Type"),
    "props.storey": ("Pavimento", "Storey"),
    "props.layers": ("Camadas", "Layers"),
    "props.profile": ("Perfil", "Profile"),
    "props.steel_section": ("Perfil de aço", "Steel section"),       # (0.494)
    "props.steel_weight": ("Peso", "Weight"),
    "props.steel_mark": ("Marca", "Mark"),                           # (0.500)
    "props.steel_mark_none": ("— (Numerar peças)", "— (Number pieces)"),
    "props.dims": ("Dimensões", "Dimensions"),
    "props.volume": ("Volume", "Volume"),
    "props.free": ("forma livre", "free form"),
    "props.lines": ("Linhas", "Lines"),
    "props.lines_value": ("{n} segmento(s), {l} no total", "{n} segment(s), {l} in total"),
    "props.area": ("Área", "Area"),
    "props.total": ("Total", "Total"),
    "act.new": ("Novo", "New"),
    "act.quit": ("Sair", "Quit"),
    "act.undo": ("Desfazer", "Undo"),
    "act.redo": ("Refazer", "Redo"),
    "act.delete": ("Apagar", "Delete"),
    "act.zoom_all": ("Enquadrar tudo", "Zoom extents"),
    "act.view_iso": ("Vista isométrica", "Isometric view"),
    "act.view_top": ("Vista de topo", "Top view"),
    "act.view_front": ("Vista de frente", "Front view"),
    "act.shortcuts": ("Ajuda", "Help"),                        # (0.327: the Help window; was «Atalhos e navegação»)
    "help.title": ("Ajuda — ArqSynth BIM", "Help — ArqSynth BIM"),
    "help.tab.tool": ("Ferramenta", "Tool"),
    "help.tab.find": ("Procurar", "Find"),
    "help.tab.steps": ("Primeiros passos", "First steps"),
    "help.tab.keys": ("Teclas", "Keys"),
    "help.where": ("Na fita: {w}", "On the ribbon: {w}"),
    "help.now": ("O que fazer agora", "What to do now"),
    "help.keys": ("Teclas desta ferramenta", "This tool's keys"),
    "help.what": ("Para que serve", "What it is for"),
    "help.select": ("Um clique escolhe um elemento (na face de um esboço: dois cliques, com as arestas; três, o objeto "
                    "todo). Arrastar para a direita escolhe o que fica todo dentro da caixa; para a esquerda, o que "
                    "ela toca. Shift + clique junta ou tira. As Propriedades, à direita, mostram e mudam o que está "
                    "escolhido. Escolha uma ferramenta na fita (em cima) e esta ajuda diz como se usa.",
                    "A click picks an element (on a sketch's face: two clicks, with its edges; three, the whole "
                    "object). Dragging to the right picks what is wholly inside the box; to the left, what it "
                    "touches. Shift + click adds or removes. The Properties, on the right, show and change what is "
                    "picked. Choose a tool on the ribbon (at the top) and this help says how it is used."),
    "help.search": ("Escreva o nome de um comando: parede, cota, pilares, telhado, PDF…",
                    "Type a command's name: wall, dimension, columns, roof, PDF…"),
    "help.show": ("Mostrar onde está", "Show where"),
    "help.use": ("Usar", "Use"),
    "help.none_found": ("Nenhum comando com esse nome: experimente outra palavra.",
                        "No command by that name: try another word."),
    "help.needs_walls": ("Este comando está no separador verde «Modificar | Paredes», que aparece quando há paredes "
                         "selecionadas: clique numa parede.",
                         "This command is on the green tab “Modify | Walls”, which comes when walls are selected: "
                         "click a wall."),
    "help.steps_intro": ("Uma casa pequena, do princípio ao PDF. «Mostrar onde está» abre o separador certo e acende o "
                         "botão.",
                         "A small house, from the start to the PDF. «Show where» opens the right tab and lights the "
                         "button."),
    "help.step.walls": ("Paredes: clique em Parede, clique num ponto do chão, leve o rato para a direita, escreva 6 e "
                        "Enter; para cima, 4 e Enter; para a esquerda, 6 e Enter; clique no primeiro ponto para "
                        "fechar. Esc.",
                        "Walls: click Wall, click a point on the ground, move right, type 6 and Enter; up, 4 and "
                        "Enter; left, 6 and Enter; click the first point to close. Esc."),
    "help.step.slab": ("Laje de cobertura: clique em Laje e clique num canto do topo das paredes e no canto oposto. Esc.",
                       "Roof slab: click Slab, then a corner on top of the walls and the opposite one. Esc."),
    "help.step.door": ("Porta: clique em Porta, passe o rato sobre uma parede e clique. Esc.",
                       "Door: click Door, move over a wall and click. Esc."),
    "help.step.window": ("Janela: clique em Janela, passe o rato sobre uma parede e clique. Esc.",
                         "Window: click Window, move over a wall and click. Esc."),
    "help.step.roof": ("Telhado (em vez da laje de cobertura): clique em Cobertura e clique dentro das paredes.",
                       "Pitched roof (instead of the roof slab): click Roof, then inside the walls."),
    "help.step.room": ("Ambiente: clique em Ambiente e clique dentro das paredes: fica com o nome e a área.",
                       "Room: click Room, then inside the walls: it gets its name and area."),
    "help.step.plan": ("Planta: clique em Planta (ou carregue em F4).", "Plan: click Plan (or press F4)."),
    "help.step.dims": ("Cotas: na planta, clique em Cotar paredes.", "Dimensions: in the plan, click Dimension walls."),
    "help.step.sheets": ("Folhas: clique em Folhas por pavimento e OK: a planta vai para uma folha com legenda.",
                         "Sheets: click Sheets by storey and OK: the plan goes onto a sheet with a title block."),
    "help.step.pdf": ("PDF: clique em Folhas em PDF e escolha onde o gravar.",
                      "PDF: click Sheets as PDF and choose where to save it."),
    # (0.346) the tips of the commands that had none (over their buttons, in the Help, in GUIA.md)
    "tip.quit": ("Fecha o programa; se houver alterações por guardar, pergunta antes.",
                 "Closes the program; with changes not saved, it asks first."),
    "tip.storey_down": ("Passa para o pavimento de baixo: as ferramentas desenham nele e a planta (F4) mostra-o. PgUp "
                        "sobe.", "Goes to the storey below: the tools draw on it and the plan (F4) shows it. PgUp goes up."),
    "tip.only_active": ("No 3D (e nos cortes e alçados), mostra só o pavimento ativo — o que está a negrito na lista — "
                        "e esconde os outros: para trabalhar num andar sem os de cima à frente. A planta mostra sempre "
                        "só o seu pavimento.", "In 3D (and in sections and elevations), only the active storey shown — "
                        "the one in bold in the list — and the others hidden: to work on one floor without those above "
                        "in the way. A plan always shows its own storey only."),
    "tip.component_edit": ("Abre a cópia escolhida de um componente para a mudar de forma; ao fechar, a forma nova passa "
                           "a todas as cópias.", "Opens the chosen copy of a component to reshape it; when closed, the "
                                                 "new shape goes to every copy."),
    "tip.component_close": ("Termina a edição do componente: a forma nova passa a todas as suas cópias.",
                            "Ends editing the component: its new shape goes to all its copies."),
    "tip.group_ungroup": ("Desfaz o grupo escolhido: os elementos ficam soltos, onde estão.",
                          "Breaks up the chosen group: its elements stay where they are, on their own."),
    "tip.remove_water_proposal": ("Retira, do pavimento ativo, os tubos e as ligações que a proposta automática de "
                                  "águas e esgotos fez (os desenhados à mão ficam). Um passo de desfazer.",
                                  "Takes away, on the active storey, the pipes and connections the automatic water and "
                                  "drainage proposal made (those drawn by hand stay). One undo step."),
    "tip.sync": ("Num projeto partilhado: manda as suas alterações para o modelo central e traz as da equipa.",
                 "In a shared project: sends your changes to the central model and brings the team's."),
    "tip.reserve_views": ("Num projeto partilhado: reserva para si os cortes, as folhas, as cotas e os modelos de vista, "
                          "para ninguém os mudar ao mesmo tempo.",
                          "In a shared project: reserves the sections, sheets, dimensions and view templates for you, "
                          "so nobody changes them at the same time."),
    "tip.give_back": ("Num projeto partilhado: devolve tudo o que reservou, para a equipa o poder mudar.",
                      "In a shared project: gives back all you reserved, so the team can change it."),
    "tip.check_ifc": ("Verifica o IFC como o pede a certificação: o cabeçalho e as regras do esquema, a estrutura de "
                      "pavimentos, as unidades, os identificadores, as formas e os nomes, as quantidades, os tipos, os "
                      "materiais e a georreferência — cada falta no painel de requisitos.",
                      "Checks the IFC as certification asks: the header and the schema's rules, the storeys, units, "
                      "identifiers, shapes and names, quantities, types, materials and georeferencing — each gap in "
                      "the requirements panel."),
    "tip.last_section": ("Abre outra vez o último corte (F5).", "Opens the last section again (F5)."),
    "tip.dimension_walls": ("Na planta do pavimento ativo, cota as paredes escolhidas (nenhuma: todas) pelo lado de fora: "
                            "a cadeia pelas portas e janelas e o comprimento total. Outra vez: substitui-as.",
                            "On the active storey's plan, dimensions the chosen walls (none: all) on their outer side: "
                            "the chain through the doors and windows and the overall length. Again: replaces them."),
    "tip.iso": ("A vista 3D em isométrica, com o modelo todo (F8).", "The 3D view in isometric, the whole model (F8)."),
    "tip.top": ("A vista de cima (F2).", "The view from above (F2)."),
    "tip.front": ("A vista de frente (F3).", "The view from the front (F3)."),
    "tip.view3d_new": ("Guarda a vista 3D como está (a câmara, o estilo, a caixa de corte) numa vista nova do "
                       "navegador.", "Keeps the 3D view as it is (camera, style, section box) as a new view in the "
                                     "browser."),
    "tip.box": ("Liga ou desliga a caixa de corte do 3D: arraste as suas faces para cortar o modelo (F6).",
                "Turns the 3D section box on or off: drag its faces to cut the model (F6)."),
    "tip.box_selection": ("Põe a caixa de corte à volta do que está escolhido: vê-se só isso (Shift+F6).",
                          "Puts the section box round what is chosen: only that is seen (Shift+F6)."),
    "tip.templates": ("Modelos de vista: o que uma vista mostra (categorias, estilo, escala…) guardado com um nome, para "
                      "aplicar a outras vistas.", "View templates: what a view shows (categories, style, scale…) kept "
                                                  "under a name, to apply to other views."),
    "tip.next_view": ("Passa para a vista aberta seguinte (o separador à direita, Ctrl+Tab).",
                      "Goes to the next open view (the tab on the right, Ctrl+Tab)."),
    "tip.prev_view": ("Passa para a vista aberta anterior (Ctrl+Shift+Tab).",
                      "Goes to the previous open view (Ctrl+Shift+Tab)."),
    "tip.close_view": ("Fecha a vista que está à frente (Ctrl+W); fechadas todas, volta a vista 3D.",
                       "Closes the view in front (Ctrl+W); with all closed, the 3D view comes back."),
    "tip.mouse_sketchup": ("O botão do meio do rato orbita; com Shift, desloca — como no SketchUp.",
                           "The mouse's middle button orbits; with Shift, it pans — as in SketchUp."),
    "tip.mouse_revit": ("O botão do meio do rato desloca; com Shift, orbita — como no Revit.",
                        "The mouse's middle button pans; with Shift, it orbits — as in Revit."),
    # (0.348) the model in glTF binary (GLB)
    "act.export_model": ("Exportar modelo 3D…", "Export 3D model…"),
    "tip.export_model": ("O modelo em 3D: GLB (glTF) para o ArqSynth Presentation, a internet, o Blender, o Twinmotion — "
                         "as peças por pavimento e categoria, os materiais e os dados de cada elemento —; SKP para o "
                         "SketchUp e 3DM para o Rhino, com as mesmas etiquetas ou camadas, materiais e dados; OBJ para "
                         "quase todos os programas 3D; STL para imprimir uma maqueta à escala; USDZ para a realidade "
                         "aumentada no iPhone e no iPad (abre-se sozinho, e põe o modelo em cima da mesa).",
                         "The model in 3D: GLB (glTF) for the ArqSynth Presentation, the web, Blender, Twinmotion — the "
                         "parts by storey and category, the materials and each element's data —; SKP for SketchUp and "
                         "3DM for Rhino, with the same tags or layers, materials and data; OBJ for nearly every 3D "
                         "program; STL to print a scale model; USDZ for augmented reality on an iPhone or iPad (it opens "
                         "on its own, and puts the model on the table)."),
    "model3d.filter.glb": ("Modelo 3D glTF (*.glb)", "glTF 3D model (*.glb)"),                      # (0.349)
    "model3d.filter.skp": ("SketchUp (*.skp)", "SketchUp (*.skp)"),                                  # (0.350)
    "model3d.filter.3dm": ("Rhino (*.3dm)", "Rhino (*.3dm)"),
    "model3d.filter.obj": ("Modelo 3D OBJ, com os materiais (*.obj)", "OBJ 3D model, with its materials (*.obj)"),
    "model3d.filter.stl": ("Impressão 3D STL (*.stl)", "3D printing STL (*.stl)"),
    "model3d.filter.usdz": ("Realidade aumentada USDZ, iPhone e iPad (*.usdz)",                     # (0.371)
                            "Augmented reality USDZ, iPhone and iPad (*.usdz)"),
    "err.usd_missing": ("Para gravar em USDZ é preciso a biblioteca usd-core, que não está instalada.",
                        "Saving as USDZ needs the usd-core library, which is not installed."),
    "model3d.scale": ("A escala da maqueta (em milímetros):", "The scale model's scale (in millimetres):"),
    # (0.351) 3D models brought in
    "act.import_model": ("Importar modelo 3D…", "Import 3D model…"),
    "tip.import_model": ("Traz um modelo 3D do SketchUp (SKP), do Rhino (3DM), em glTF / GLB, OBJ ou STL: como "
                         "componente — mobiliário, equipamento, com as cores dos materiais, colocado com um clique e "
                         "depois na biblioteca — ou como esboço, com as faces inteiras, para editar.",
                         "Brings in a 3D model from SketchUp (SKP), Rhino (3DM), glTF / GLB, OBJ or STL: as a component "
                         "— furniture, equipment, in its materials' colours, placed with a click and then in the "
                         "library — or as a sketch, its faces whole, to edit."),
    "model3d.import_filter": ("Modelos 3D (*.skp *.3dm *.glb *.gltf *.obj *.stl)",
                              "3D models (*.skp *.3dm *.glb *.gltf *.obj *.stl)"),
    "model3d.summary": ("{f}: {tri} triângulos, {n} materiais.", "{f}: {tri} triangles, {n} materials."),
    "model3d.skipped": ("{n} superfícies vieram sem malha e ficaram de fora: no Rhino, veja-as em Sombreado e grave "
                        "outra vez.",
                        "{n} surfaces came without a mesh and were left out: in Rhino, view them Shaded and save "
                        "again."),
    "model3d.as": ("Entra como:", "Comes in as:"),
    "model3d.as.component": ("Componente (mobiliário, equipamento…)", "Component (furniture, equipment…)"),
    "model3d.as.sketch": ("Esboço, para editar", "Sketch, to edit"),
    "model3d.where": ("Onde:", "Where:"),
    "model3d.where.click": ("Onde eu clicar", "Where I click"),
    "model3d.where.file": ("Onde está no ficheiro", "Where it is in the file"),
    "model3d.unit": ("Unidade do ficheiro:", "The file's unit:"),
    "model3d.unit.m": ("metros", "metres"),
    "model3d.unit.cm": ("centímetros", "centimetres"),
    "model3d.unit.mm": ("milímetros", "millimetres"),
    "model3d.unit.in": ("polegadas", "inches"),
    "model3d.unit.ft": ("pés", "feet"),
    "model3d.up": ("Vertical:", "Vertical:"),
    "model3d.up.z": ("Z para cima", "Z up"),
    "model3d.up.y": ("Y para cima", "Y up"),
    "model3d.size": ("Tamanho:", "Size:"),
    "model3d.working": ("A trazer o modelo 3D…", "Bringing the 3D model in…"),
    "cmd.import_model": ("Importar modelo 3D", "Import 3D model"),
    "info.model3d_place": ("«{name}» está na biblioteca: clique onde o pôr (Tab roda 90°, Esc acaba).",
                           "«{name}» is in the library: click where to put it (Tab turns it 90°, Esc ends)."),
    "info.model3d_component": ("«{name}» trazido como componente, onde estava no ficheiro.",
                               "«{name}» brought in as a component, where it was in the file."),
    "info.model3d_sketch": ("«{name}» trazido como esboço: {n} faces.", "«{name}» brought in as a sketch: {n} faces."),
    "err.model3d": ("Não consegui ler {f}: {e}", "Could not read {f}: {e}"),
    "err.model3d_empty": ("{f} não tem nada em 3D para trazer.", "{f} has nothing in 3D to bring in."),
    "info.stl": ("Maqueta gravada em {f}: {tri} triângulos à escala 1:{s}, em milímetros ({mb} MB).",
                 "Scale model saved to {f}: {tri} triangles at 1:{s}, in millimetres ({mb} MB)."),
    "gltf.what": ("O que vai no ficheiro:", "What goes into the file:"),
    "gltf.what.shown": ("O que está à vista", "What is shown"),
    "gltf.what.all": ("O modelo todo", "The whole model"),
    "gltf.what.selection": ("Só a seleção", "Only the selection"),
    "gltf.working": ("A escrever o modelo 3D…", "Writing the 3D model…"),
    "gltf.model": ("Modelo", "Model"),
    "gltf.sketches": ("Esboços", "Sketches"),
    "gltf.sketch_material": ("Esboço", "Sketch"),
    "gltf.no_storey": ("Sem pavimento", "No storey"),
    "gltf.glass_part": ("vidro", "glass"),                # (0.483) a window's glass, in a node of its own
    "gltf.water_part": ("água", "water"),
    "info.gltf": ("Modelo 3D gravado em {f}: {n} elementos, {tri} triângulos, {mb} MB.",
                  "3D model saved to {f}: {n} elements, {tri} triangles, {mb} MB."),
    "info.gltf_empty_selection": ("Nada escolhido: escolha os elementos a exportar (ou escolha «O que está à vista»).",
                                  "Nothing chosen: choose the elements to export (or choose «What is shown»)."),
    # (0.362) the model for the ArqSynth Presentation
    "act.export_presentation": ("Para o ArqSynth Presentation…", "For the ArqSynth Presentation…"),
    "tip.export_presentation": ("O modelo todo num GLB para o ArqSynth Presentation, com a apresentação dentro: uma camada "
                                "por elemento (por pavimento e categoria) e as cenas — a vista geral, cada vista 3D "
                                "com nome (a câmara, o que esconde, a caixa de corte), a planta de cada pavimento (vista "
                                "de cima, cortada à altura de corte) e cada corte —, e o sol do terreno.",
                                "The whole model in a GLB for the ArqSynth Presentation, with the presentation in it: "
                                "a layer per element (by storey and category) and the scenes — the general view, each "
                                "named 3D view (its camera, what it hides, its section box), each storey's plan (seen "
                                "from above, cut at the cut height) and each section —, and the site's sun."),
    "present.working": ("A preparar o modelo para o Presentation…", "Preparing the model for the Presentation…"),
    "info.presentation_empty": ("Nada para o Presentation: o projeto não tem elementos do modelo (paredes, lajes…); "
                                "os esboços soltos não vão.",
                                "Nothing for the Presentation: the project has no elements of the model (walls, "
                                "slabs…); loose sketches do not go."),
    "present.overview": ("Vista geral", "General view"),
    "present.plan": ("Planta — {name}", "Plan — {name}"),
    "present.section": ("Corte — {name}", "Section — {name}"),
    "present.disclaimer": ("Modelo e cenas preparados no ArqSynth BIM; reveja-os no Presentation antes de partilhar.",
                           "Model and scenes prepared in ArqSynth BIM; review them in the Presentation before "
                           "sharing."),
    "info.presentation": ("Para o Presentation gravado em {f}: {n} elementos, {s} cenas, {mb} MB. No Presentation, "
                          "importe-o numa página Modelo 3D.",
                          "For the Presentation saved to {f}: {n} elements, {s} scenes, {mb} MB. In the "
                          "Presentation, import it into a 3D model page."),
    # (0.363) the Presentation panel: the scenes prepared here
    "act.presentation_panel": ("Cenas da apresentação", "Presentation scenes"),
    "tip.presentation_panel": ("Abre a interface do ArqSynth Presentation (o ícone da barra da esquerda): as cenas que vão "
                               "para o Presentation, pela ordem da apresentação, com a câmara, as camadas, a transição, "
                               "o efeito, o sol e a legenda de cada uma, e a exportação.",
                               "Opens the ArqSynth Presentation's interface (the icon of the left bar): the scenes that "
                               "go to the Presentation, in the presentation's order, with each one's camera, layers, "
                               "transition, effect, sun and caption, and the export."),
    "present.title": ("Apresentação", "Presentation"),
    "present.hint": ("As cenas que vão para o ArqSynth Presentation, pela ordem da apresentação. Arraste para mudar a "
                     "ordem; duplo clique abre a vista.",
                     "The scenes that go to the ArqSynth Presentation, in the presentation's order. Drag to change the "
                     "order; double-click opens the view."),
    "present.up": ("Subir", "Up"),
    "present.down": ("Descer", "Down"),
    "present.thumbs": ("Miniaturas", "Thumbnails"),
    "present.thumbs_tip": ("Tira uma imagem pequena de cada cena, como a Imagem da vista: o programa passa por elas uma "
                           "a uma e volta à vista em que estava. Vão também para o Presentation.",
                           "Takes a small image of each scene, as the Image of the view does: the program goes "
                           "through them one by one and comes back to the view it was in. They go to the "
                           "Presentation too."),
    "present.export": ("Exportar para o Presentation…", "Export for the Presentation…"),
    "present.scene": ("Cena escolhida", "Chosen scene"),
    "present.none": ("Escolha uma cena na lista.", "Choose a scene in the list."),
    "present.initial": ("Cena de entrada", "First scene"),
    "present.initial_tip": ("A apresentação abre nesta cena.", "The presentation opens on this scene."),
    "present.hidden": ("Fora da apresentação", "Left out of the presentation"),
    "present.hidden_tip": ("A cena vai na mesma para o Presentation, mas fica de lado: não entra na sequência que o "
                           "cliente vê.",
                           "The scene still goes to the Presentation, but is put aside: it is not in the sequence "
                           "the client sees."),
    "present.transition": ("Chegada", "Arrival"),
    "present.transition.smooth": ("Voo suave", "Smooth flight"),
    "present.transition.cut": ("Corte seco", "Cut"),
    "present.effect": ("Efeito", "Effect"),
    "present.effect.none": ("Nenhum", "None"),
    "present.effect.sun": ("Sol ao longo do dia", "Sun through the day"),
    "present.effect.construction": ("Construção, peça a peça", "Construction, piece by piece"),
    "present.effect.explode": ("Explosão (peças afastadas)", "Exploded (pieces apart)"),
    "present.seconds": ("Tempo na cena", "Time on the scene"),
    "present.seconds_auto": ("automático", "automatic"),
    "present.seconds_tip": ("Quanto tempo a cena fica no passeio automático (sem voz gravada). «automático»: o do "
                            "Presentation (4 s).",
                            "How long the scene stays in the automatic tour (with no recorded voice). «automatic»: "
                            "the Presentation's (4 s)."),
    "present.caption": ("Legenda", "Caption"),
    "present.caption_tip": ("O texto que aparece por baixo da cena no passeio narrado.",
                            "The text shown under the scene in the narrated tour."),
    "present.count": ("{n} cenas · {h} fora da apresentação", "{n} scenes · {h} left out"),
    "present.marks.initial": ("entrada", "first"),
    "present.marks.hidden": ("fora", "left out"),
    "present.thumbs_working": ("A tirar as miniaturas das cenas…", "Taking the scenes' thumbnails…"),
    "info.present_thumbs": ("{n} miniaturas tiradas.", "{n} thumbnails taken."),
    "cmd.presentation": ("Cenas da apresentação", "Presentation scenes"),
    # (0.364) the camera moves (the ArqSynth Presentation's library: the same names)
    "present.move": ("Movimento", "Camera move"),
    "present.move_tip": ("Um movimento de câmara do Presentation, feito com as medidas do edifício (ou do ambiente, nos "
                         "de interior). Toca ao entrar na cena.",
                         "One of the Presentation's camera moves, made from the building's measures (or the room's, "
                         "inside). It plays when the scene is entered."),
    "present.move.none": ("Nenhum", "None"),
    "present.move_own": ("{s} s (o do movimento)", "{s} s (the move's own)"),
    "present.room": ("Ambiente", "Room"),
    "present.room_tip": ("O ambiente onde se faz o movimento de interior. «O da cena»: o que a vista 3D tem à frente, "
                         "ou o maior do pavimento (numa planta) ou do projeto.",
                         "The room the interior move is made in. «The scene's»: the one the 3D view looks into, or "
                         "the largest of the storey (a plan) or of the project."),
    "present.room_auto": ("O da cena (automático)", "The scene's (automatic)"),
    "present.play": ("Ver movimento", "Play the move"),
    "present.stop": ("Parar", "Stop"),
    "present.play_tip": ("Mostra o movimento no 3D, como o Presentation o vai tocar; no fim (ou com Esc) a câmara volta "
                         "onde estava.",
                         "Shows the move in the 3D view as the Presentation will play it; at its end (or with Esc) "
                         "the camera goes back where it was."),
    "info.move_none": ("Esta cena não tem movimento: escolha um em «Movimento».",
                       "This scene has no camera move: choose one in «Camera move»."),
    "info.move_playing": ("{name}, {s} s. Esc para parar.", "{name}, {s} s. Esc to stop."),
    # (0.368) the 360° panoramas
    "act.panorama": ("Panorama 360°…", "360° panorama…"),
    "tip.panorama": ("Um panorama 360° em render realista, tirado de onde está a câmara do 3D (ponha-a dentro de uma "
                     "sala, à altura dos olhos): fica guardado com o projeto e vai para o ArqSynth Presentation como um "
                     "ponto 360° na planta do seu pavimento.",
                     "A realistic 360° panorama taken from where the 3D view's camera is (put it inside a room, at eye "
                     "height): kept with the project, it goes to the ArqSynth Presentation as a 360° point on its "
                     "storey's plan."),
    "cmd.panorama": ("Panoramas 360°", "360° panoramas"),
    "panorama.name": ("Panorama", "Panorama"),
    "panorama.name_label": ("Nome", "Name"),
    "panorama.size": ("Tamanho", "Size"),
    "panorama.hint": ("Tira-se de onde está a câmara do 3D, a olhar a direito para onde ela olha. São seis renders "
                      "(frente, direita, trás, esquerda, cima, baixo) juntos numa imagem 360°: demora umas seis vezes "
                      "um render da vista.",
                      "Taken from where the 3D view's camera is, looking level where it looks. Six renders (ahead, "
                      "right, behind, left, up, down) made one 360° picture: it takes about six times a view's render."),
    "info.panorama_3d": ("Para um panorama, abra o 3D em perspetiva e ponha a câmara onde o quer (dentro de uma sala, à "
                         "altura dos olhos: Visualizar ▸ Posicionar câmara).",
                         "For a panorama, open the 3D view in perspective and put the camera where you want it (inside "
                         "a room, at eye height: View ▸ Position camera)."),
    "info.panorama_save": ("Guarde o projeto primeiro: os panoramas ficam numa pasta ao lado dele.",
                           "Save the project first: the panoramas are kept in a folder beside it."),
    "info.panorama_started": ("A fazer o panorama «{name}» ({w} × {h}): seis vistas, uma a uma.",
                              "Making the panorama «{name}» ({w} × {h}): six views, one by one."),
    "info.panorama_kept": ("Panorama «{name}» guardado com o projeto: vai para o Presentation no pacote.",
                           "Panorama «{name}» kept with the project: it goes to the Presentation in the package."),
    "present.panoramas": ("Panoramas 360°", "360° panoramas"),
    "present.panorama_new": ("Novo…", "New…"),
    "present.panorama_remove": ("Remover", "Remove"),
    "present.panoramas_none": ("Nenhum. «Novo…» tira um de onde está a câmara do 3D.",
                               "None. «New…» takes one from where the 3D view's camera is."),
    # (0.367) the package: the model and the sheets as plan pages
    "present.filter": ("Pacote para o Presentation (*.zip);;Só o modelo 3D (*.glb)",
                       "Package for the Presentation (*.zip);;The 3D model alone (*.glb)"),
    "info.presentation_package": ("Pacote para o Presentation gravado em {f}: {n} elementos, {s} cenas, {p} para as "
                                  "plantas{v}, {mb} MB. No Presentation: «ArqSynth BIM» na lista de páginas.",
                                  "Package for the Presentation saved to {f}: {n} elements, {s} scenes, {p} for the "
                                  "plans{v}, {mb} MB. In the Presentation: «ArqSynth BIM» in the pages list."),
    "present.sheets_1": ("1 folha", "1 sheet"),
    "present.sheets_n": ("{n} folhas", "{n} sheets"),
    "present.panoramas_1": (", 1 panorama 360°", ", 1 360° panorama"),           # (0.368)
    "present.panoramas_n": (", {n} panoramas 360°", ", {n} 360° panoramas"),
    # (0.366) the rooms: as labels and as the Virtual Walk
    "present.labels": ("Etiquetas dos ambientes", "Room labels"),
    "present.labels_tip": ("Cada ambiente com a sua etiqueta no Presentation, deitada no chão: o nome, o número e a área.",
                           "Each room with its label in the Presentation, lying on its floor: its name, number and area."),
    "present.walk": ("Passeio Virtual pelos ambientes", "Virtual Walk through the rooms"),
    "present.walk_tip": ("Os ambientes como as zonas do Passeio Virtual do Presentation, um piso por pavimento, ligados "
                         "pelas portas entre eles e pelas escadas entre pisos; começa no ambiente por onde se entra.",
                         "The rooms as the Presentation's Virtual Walk zones, a floor per storey, linked by the doors "
                         "between them and the stairs between storeys; it starts in the room one comes in by."),
    # (0.365) the scene's sun, exposure and sky
    "present.sun": ("Sol (dia e hora)", "Sun (day and time)"),
    "present.sun_animate": ("Animação do sol", "Sun animation"),
    "present.sun_animate.none": ("Parado", "Still"),
    "present.sun_animate.day": ("Ao longo do dia", "Through the day"),
    "present.sun_animate.year": ("Ao longo do ano", "Through the year"),
    "present.sun_animate_tip": ("No Presentation, o sol pode andar: do nascer ao pôr do sol nesse dia, ou os doze meses "
                                "a essa hora (o sol mais alto e mais baixo do ano).",
                                "In the Presentation the sun may move: from sunrise to sunset on that day, or the twelve "
                                "months at that hour (the year's highest and lowest sun)."),
    "present.exposure": ("Exposição", "Exposure"),
    "present.exposure_tip": ("Mais clara ou mais escura (1 = a do Presentation; 0,3 a 1,6).",
                             "Lighter or darker (1 = the Presentation's; 0.3 to 1.6)."),
    "present.sky": ("Céu atrás do modelo", "Sky behind the model"),
    "present.sky_tip": ("O céu do sol desta hora; desligado, o fundo liso do Presentation.",
                        "The sky of this hour's sun; off, the Presentation's plain background."),
    "present.sun_play": ("Ver sol", "Show the sun"),
    "present.sun_play_tip": ("Mostra no 3D o sol deste dia e hora, com as sombras, como o Presentation o vai pôr (e a "
                             "animação, se a tiver). Outra vez (ou Esc): o sol do estilo de vista.",
                             "Shows in the 3D view this day's and hour's sun, with its shadows, as the Presentation "
                             "will place it (and its animation, if any). Again (or Esc): the view style's sun."),
    "present.no_site": ("O terreno não tem lugar (Terreno ▸ Localização): sem ele o Presentation põe o sol na direção "
                        "do estilo de vista, sem dia nem hora.",
                        "The site has no place (Terrain ▸ Location): without it the Presentation sets the sun in the "
                        "view style's direction, with no day or hour."),
    "info.sun_shown": ("Sol a {date} às {time}: azimute {az}°, altura {alt}°. Esc para voltar ao sol do estilo.",
                       "Sun on {date} at {time}: azimuth {az}°, altitude {alt}°. Esc for the view style's sun."),
    "info.sun_night": ("A {date} às {time} o sol está abaixo do horizonte: é noite (no Presentation, só as luzes).",
                       "On {date} at {time} the sun is below the horizon: night (in the Presentation, the lights alone)."),
    "info.sun_day": ("O sol de {date}, do nascer ao pôr, em {s} s. Esc para parar.",
                     "The sun of {date}, sunrise to sunset, in {s} s. Esc to stop."),
    "info.sun_year": ("O sol às {time}, de janeiro a dezembro, em {s} s. Esc para parar.",
                      "The sun at {time}, January to December, in {s} s. Esc to stop."),
    "info.no_site": ("O terreno não tem lugar: escolha-o em Terreno ▸ Localização para o sol ter dia e hora.",
                     "The site has no place: choose it in Terrain ▸ Location for the sun to have a day and hour."),
    # (0.479) the ArqSynth Presentation tab (ui/presentation_mode.py): the Presentation's own words
    "pmode.title": ("ArqSynth Presentation", "ArqSynth Presentation"),
    "pmode.split": ("Dividido", "Split"),
    "pmode.split_tip": ("Ver páginas e cenas", "See pages and scenes"),
    "pmode.tabs": ("Abas", "Tabs"),
    "pmode.tabs_tip": ("Ver por abas", "See by tabs"),
    "pmode.tab_pages": ("Páginas", "Pages"),
    "pmode.tab_pages_tip": ("As páginas que vão para o Presentation", "The pages that go to the Presentation"),
    "pmode.tab_scenes": ("Cenas", "Scenes"),
    "pmode.tab_scenes_tip": ("As cenas da página Modelo 3D", "The 3D model page's scenes"),
    "pmode.pages": ("Páginas", "Pages"),
    "pmode.add.cover": ("Capa", "Cover"),
    "pmode.add.text": ("Texto", "Text"),
    "pmode.add.plan": ("Planta", "Plan"),
    "pmode.add.model": ("Modelo 3D", "3D model"),
    "pmode.add.concept": ("Concept", "Concept"),
    "pmode.add_tip.cover": ("A capa faz-se no Presentation (o BIM envia o Modelo 3D e as plantas).",
                            "The cover is made in the Presentation (the BIM sends the 3D model and the plans)."),
    "pmode.add_tip.text": ("As páginas de texto fazem-se no Presentation (o BIM envia o Modelo 3D e as plantas).",
                           "Text pages are made in the Presentation (the BIM sends the 3D model and the plans)."),
    "pmode.add_tip.plan": ("Uma folha nova: com vistas, vai para o Presentation como página de planta.",
                           "A new sheet: with views on it, it goes to the Presentation as a plan page."),
    "pmode.add_tip.model": ("A página Modelo 3D: o modelo com as suas cenas.", "The 3D model page: the model and its "
                            "scenes."),
    "pmode.add_tip.concept": ("O Concept importa-se no Presentation (ficheiro do ArqSynth Concept).",
                              "The Concept is imported in the Presentation (an ArqSynth Concept file)."),
    "pmode.page_model": ("Modelo 3D", "3D model"),
    "pmode.page_kind.model": ("Modelo 3D", "3D model"),
    "pmode.page_kind.plan": ("Planta", "Plan"),
    "pmode.no_sheets": ("Sem folhas com vistas: as plantas vão quando houver folhas (botão «Planta»).",
                        "No sheets with views: the plans go once there are sheets («Plan» button)."),
    "pmode.export": ("Exportar / atualizar", "Export / update"),
    "pmode.export_tip": ("Grava o pacote para o Presentation (o modelo, as cenas com tudo o que se escolheu aqui, as "
                         "plantas). No Presentation, «Importar / atualizar» numa página Modelo 3D lê-o e mantém o que "
                         "lá se fez.",
                         "Saves the package for the Presentation (the model, the scenes with all chosen here, the "
                         "plans). In the Presentation, «Import / update» on a 3D model page reads it and keeps what "
                         "was done there."),
    "pmode.scenes": ("Cenas", "Scenes"),
    "pmode.transition": ("Transição", "Transition"),
    "pmode.transition_tip": ("O tempo da chegada a cada cena — vale para todas (cada uma mantém o seu voo suave ou "
                             "corte seco).",
                             "How long the arrival at each scene takes — for all of them (each keeps its smooth "
                             "flight or cut)."),
    "pmode.cmd_transition": ("Transição das cenas", "Scenes' transition"),
    "pmode.no_scenes": ("Sem cenas: «Criar cena» guarda a vista 3D como cena.",
                        "No scenes: «Create scene» keeps the 3D view as a scene."),
    "pmode.omitted": ("{n} cena(s) retirada(s) · Repor", "{n} scene(s) taken out · Restore"),
    "pmode.omitted_tip": ("Volta a enviar as cenas das vistas que foram eliminadas aqui (as vistas continuaram no "
                          "projeto).",
                          "Sends again the views' scenes deleted here (the views stayed in the project)."),
    "pmode.initial_mark": ("Cena inicial", "First scene"),
    "pmode.update_tip": ("Actualizar esta cena com a vista actual (câmara, visibilidade, modo de visualização)",
                         "Update this scene with the current view (camera, visibility, visual mode)"),
    "pmode.initial_tip": ("Definir como cena inicial", "Set as the first scene"),
    "pmode.hide_tip": ("Esconder da apresentação (continua editável aqui)", "Hide from the presentation (still "
                       "editable here)"),
    "pmode.show_tip": ("Mostrar na apresentação", "Show in the presentation"),
    "pmode.only_visible": ("É a única cena visível — a apresentação ficaria vazia",
                           "It is the only visible scene — the presentation would be empty"),
    "pmode.duplicate_tip": ("Duplicar cena", "Duplicate scene"),
    "pmode.rename_tip": ("Renomear cena", "Rename scene"),
    "pmode.rename_label": ("Nome da cena", "Scene name"),
    "pmode.delete_tip": ("Eliminar cena (e a sua vista 3D; Ctrl+Z repõe)", "Delete scene (and its 3D view; Ctrl+Z "
                         "brings it back)"),
    "pmode.delete_view_tip": ("Eliminar cena: deixa de ir para o Presentation (a vista continua no projeto)",
                              "Delete scene: it no longer goes to the Presentation (the view stays in the project)"),
    "pmode.sub_hidden": ("Fora da apresentação", "Out of the presentation"),
    "pmode.persp": ("Perspectiva", "Perspective"),
    "pmode.ortho": ("Ortogonal", "Orthographic"),
    "pmode.kind.plan": ("Planta", "Plan"),
    "pmode.kind.section": ("Corte", "Section"),
    "pmode.kind.overview": ("Vista geral", "General view"),
    "pmode.scene_word": ("Cena", "Scene"),
    "pmode.copy_word": ("cópia", "copy"),
    "pmode.cmd_create": ("Criar cena", "Create scene"),
    "pmode.cmd_duplicate": ("Duplicar cena", "Duplicate scene"),
    "pmode.cmd_look": ("Modo de visualização das cenas", "Scenes' visual mode"),
    "pmode.created": ("Cena «{name}» criada com a vista actual.", "Scene «{name}» created from the current view."),
    "pmode.updated": ("Cena «{name}» actualizada com a vista actual.", "Scene «{name}» updated from the current view."),
    "pmode.deleted": ("Cena «{name}» eliminada (Ctrl+Z repõe).", "Scene «{name}» deleted (Ctrl+Z brings it back)."),
    "pmode.sheet_new": ("Folha nova criada: ponha-lhe vistas e vai como página de planta.",
                        "New sheet made: put views on it and it goes as a plan page."),
    "pmode.rail.layers": ("Camadas", "Layers"),
    "pmode.rail.scenes": ("Cenas 3D", "3D scenes"),
    "pmode.rail.environment": ("Ambiente", "Environment"),
    "pmode.rail.labels": ("Etiquetas", "Labels"),
    "pmode.rail.images": ("Imagens", "Images"),
    "pmode.rail.effects": ("Efeitos", "Effects"),
    "pmode.rail.walk": ("Passeio", "Walk"),
    "pmode.search": ("Procurar peça…", "Search part…"),
    "pmode.select_matches": ("Seleccionar todas as correspondências", "Select all matches"),
    "pmode.layers_hint": ("Clique na lista ou duplo clique no modelo para seleccionar. Shift = série · Ctrl = múltipla.",
                          "Click in the list or double-click the model to select. Shift = range · Ctrl = several."),
    "pmode.layer_hide": ("Ocultar", "Hide"),
    "pmode.layer_show": ("Mostrar", "Show"),
    "pmode.folder_hide": ("Ocultar pasta", "Hide folder"),
    "pmode.folder_show": ("Mostrar pasta", "Show folder"),
    "pmode.no_category": ("Sem categoria", "No category"),
    "pmode.initial": ("Cena inicial", "First scene"),
    "pmode.shown": ("Mostrar na apresentação", "Show in the presentation"),
    "pmode.arrival": ("Movimento", "Movement"),
    "pmode.move.smooth": ("Suave", "Smooth"),
    "pmode.move.cut": ("Corte", "Cut"),
    "pmode.move_time": ("Duração", "Duration"),
    "pmode.effects_note": ("O movimento de câmara toca ao entrar na cena, como na biblioteca de efeitos do Presentation.",
                           "The camera move plays when the scene is entered, as in the Presentation's effects library."),
    "pmode.images_note": ("Cada panorama 360° vai como ponto 360° nas plantas do seu pavimento.",
                          "Each 360° panorama goes as a 360° point on its storey's plans."),
    "pmode.labels_note": ("Cada ambiente vai como etiqueta deitada no chão: nome, número e área.",
                          "Each room goes as a label on its floor: name, number and area."),
    "pmode.walk_note": ("Os ambientes como zonas do Passeio Virtual, ligadas pelas portas e escadas.",
                        "The rooms as the Virtual Walk's zones, linked by the doors and stairs."),
    "pmode.create": ("Criar cena", "Create scene"),
    "pmode.create_tip": ("Guardar a vista actual como nova cena", "Keep the current view as a new scene"),
    "pmode.persp_short": ("Persp", "Persp"),
    "pmode.persp_tip": ("Câmara em perspectiva", "Perspective camera"),
    "pmode.ortho_short": ("Orto", "Ortho"),
    "pmode.ortho_tip": ("Câmara ortogonal", "Orthographic camera"),
    "pmode.frame_model": ("Enquadrar modelo", "Frame the model"),
    "pmode.frame_selection": ("Enquadrar selecção", "Frame the selection"),
    "pmode.lock_tip": ("Bloquear câmara da cena", "Lock the scene's camera"),
    "pmode.unlock_tip": ("Desbloquear câmara", "Unlock the camera"),
    "pmode.locked": ("Câmara bloqueada: o rato já não a mexe (vai assim para a cena).",
                     "Camera locked: the mouse no longer moves it (it goes so to the scene)."),
    "pmode.unlocked": ("Câmara desbloqueada.", "Camera unlocked."),
    "pmode.fov": ("FOV", "FOV"),
    "pmode.fov_tip": ("Campo de visão (20–65°): o enquadramento fica, como no Presentation.",
                      "Field of view (20–65°): the framing stays, as in the Presentation."),
    "pmode.rail.cuts": ("Cortes", "Cuts"),                       # (0.484) the Presentation's «Cortes»
    "pmode.cuts_planes": ("Planos de corte", "Section planes"),
    "pmode.cut.horizontal": ("Horizontal", "Horizontal"),
    "pmode.cut.transversal": ("Vertical X", "Vertical X"),
    "pmode.cut.longitudinal": ("Vertical Z", "Vertical Z"),
    "pmode.cut_tip.horizontal": ("Um plano deitado: fica o que está por baixo da altura escolhida (como uma planta).",
                                 "A level plane: what is under the height chosen stays (as a plan)."),
    "pmode.cut_tip.transversal": ("Um plano de pé, de frente para o eixo X (vermelho).",
                                  "A standing plane, square to the X axis (red)."),
    "pmode.cut_tip.longitudinal": ("Um plano de pé, de frente para o eixo Z do Presentation (o verde do BIM).",
                                   "A standing plane, square to the Presentation's Z axis (the BIM's green)."),
    "pmode.cut_position": ("Posição exata do plano (m)", "The plane's exact position (m)"),
    "pmode.cut_flip": ("Inverter lado", "Flip side"),
    "pmode.cut_remove": ("Remover", "Remove"),
    "pmode.cuts_empty": ("Adicione um plano e mova-o com o deslizador. O corte é não-destrutivo.",
                         "Add a plane and move it with the slider. The cut is non-destructive."),
    "pmode.cuts_saved": ("Os cortes guardam-se na cena ao Criar/Actualizar.",
                         "The cuts are kept in the scene on Create/Update."),
    # (0.491) the cut's look (the Presentation's «Superfície cortada»)
    "pmode.cut_look": ("Aspeto do corte", "Cut look"),
    "pmode.cut_look.material": ("Material", "Material"),
    "pmode.cut_look.poche": ("Poché", "Poché"),
    "pmode.cut_look.solid": ("Sólido", "Solid"),
    "pmode.cut_look.open": ("Aberto", "Open"),
    "pmode.cut_look_tip.material": ("Cada parede, laje ou pilar cortado com a trama dos seus materiais (alvenaria, "
                                    "betão, isolamento, reboco…), como nas plantas e cortes do BIM. No Presentation: o "
                                    "material de cada categoria.",
                                    "Each wall, slab or column cut with its materials' hatches (masonry, concrete, "
                                    "insulation, plaster…), as in the BIM's plans and sections. In the Presentation: "
                                    "each category's material."),
    "pmode.cut_look_tip.poche": ("Tudo o que é cortado numa cor, tracejado.", "All that is cut in one colour, hatched."),
    "pmode.cut_look_tip.solid": ("Tudo o que é cortado numa cor lisa.", "All that is cut in one plain colour."),
    "pmode.cut_look_tip.open": ("Sem enchimento: vê-se o interior das peças cortadas.",
                                "No fill: the inside of the parts cut is seen."),
    "pmode.cut_colour": ("Cor do corte", "Cut colour"),
    # (0.488) the Presentation's «Passeio» (its Virtual Walk)
    "pmode.walk_room": ("Ambiente", "Room"),
    "pmode.walk_counts": ("Ambientes: {rooms} · portas entre eles: {doors} · escadas: {stairs}",
                          "Rooms: {rooms} · doors between them: {doors} · stairs: {stairs}"),
    "pmode.walk_start": ("Início", "Start"),
    "pmode.walk_start_auto": ("Automático ({name})", "Automatic ({name})"),
    "pmode.walk_start_tip": ("O ambiente onde o passeio começa (por omissão, o da porta de entrada no piso mais baixo).",
                             "The room the walk starts in (by default, the one behind the entrance door on the lowest "
                             "storey)."),
    "pmode.walk_dwell": ("Tempo em cada ambiente", "Time in each room"),
    "pmode.walk_tour": ("Visita guiada", "Guided tour"),
    "pmode.walk_off_tip": ("Desmarque um ambiente para o deixar fora do passeio (não navegável). Duplo clique: ir até "
                           "ele.", "Untick a room to leave it out of the walk (not navigable). Double click: walk to "
                           "it."),
    "pmode.walk_loose": ("sem ligação", "not linked"),
    "pmode.walk_start_mark": ("início", "start"),
    "pmode.walk_play": ("Percorrer a visita guiada", "Walk the guided tour"),
    "pmode.walk_play_tip": ("A câmara percorre a visita guiada à altura dos olhos, pelas portas e escadas, como no "
                            "Presentation. Esc para.",
                            "The camera walks the guided tour at eye height, through the doors and stairs, as in the "
                            "Presentation. Esc stops it."),
    "pmode.walk_go": ("Ir até ao escolhido", "Walk to the one chosen"),
    "pmode.walk_go_tip": ("A câmara vai do início até ao ambiente escolhido na lista, pelas portas e escadas.",
                          "The camera goes from the start to the room chosen in the list, through the doors and "
                          "stairs."),
    "pmode.walk_no_rooms": ("Sem ambientes: desenhe-os com «Ambiente e área» para haver passeio.",
                            "No rooms: draw them with «Room and area» for a walk."),
    "pmode.walk_shown_note": ("As zonas (a verde o início, a cinzento as de fora) e os caminhos pelas portas e escadas "
                              "veem-se no 3D enquanto este separador está aberto.",
                              "The zones (the start in green, those left out in grey) and the ways through the doors "
                              "and stairs are seen in the 3D view while this tab is open."),
    "info.walk_playing": ("A percorrer a visita guiada: {n} ambientes, a {v} m/s. Esc para parar.",
                          "Walking the guided tour: {n} rooms, at {v} m/s. Esc stops it."),
    "info.walk_to": ("A caminhar até «{name}». Esc para parar.", "Walking to «{name}». Esc stops it."),
    "info.walk_none": ("Não há caminho: os ambientes precisam de portas (ou escadas) entre eles.",
                       "There is no way: the rooms need doors (or stairs) between them."),
    # (0.487) the Presentation's «Diagramas» (its «Volumes para diagramas», its words)
    "pmode.rail.diagrams": ("Diagramas", "Diagrams"),
    "pmode.dia_scene": ("Cena: {name}", "Scene: {name}"),
    "pmode.dia_intro": ("Crie formas para explicar o projeto. Os volumes e as medidas são guardados nesta cena.",
                        "Make shapes to explain the project. The volumes and their measures are kept in this scene."),
    "pmode.dia_create": ("Criar volume", "Create volume"),
    "pmode.dia_shape.box": ("Caixa", "Box"),
    "pmode.dia_shape.cylinder": ("Cilindro", "Cylinder"),
    "pmode.dia_shape.sphere": ("Esfera", "Sphere"),
    "pmode.dia_shape.cone": ("Cone", "Cone"),
    "pmode.dia_shape.plane": ("Plano", "Plane"),
    "pmode.dia_new_hint": ("Novos volumes aparecem ao lado do modelo. Use Enquadrar volumes para os ver. Clique num "
                           "volume no 3D para o escolher: arraste-o, puxe as pegas das faces, ou use Mover, Rodar e "
                           "Escala da Modelagem.",
                           "New volumes appear beside the model. Use Frame volumes to see them. Click a volume in the "
                           "3D view to choose it: drag it, pull its faces' grips, or use the Modelagem's Move, Rotate "
                           "and Scale."),
    "pmode.dia_frame_all": ("Enquadrar volumes nesta cena", "Frame the volumes of this scene"),
    "pmode.dia_empty": ("Ainda não há volumes nesta cena.", "No volumes in this scene yet."),
    "pmode.dia_hide_named": ("Ocultar {name}", "Hide {name}"),
    "pmode.dia_show_named": ("Mostrar {name}", "Show {name}"),
    "pmode.dia_lock_named": ("Bloquear {name}", "Lock {name}"),
    "pmode.dia_name": ("Nome do volume", "Volume name"),
    "pmode.dia_info": ("{shape} · {v} m³", "{shape} · {v} m³"),
    "pmode.dia_duplicate": ("Duplicar", "Duplicate"),
    "pmode.dia_focus": ("Focar", "Focus"),
    "pmode.dia_lock": ("Bloquear", "Lock"),
    "pmode.dia_remove": ("Remover", "Remove"),
    "pmode.dia_show": ("Mostrar volume nesta cena", "Show the volume in this scene"),
    "pmode.dia_locked": ("Volume bloqueado: desbloqueie-o para o editar.", "Volume locked: unlock it to edit it."),
    "pmode.dia_measures": ("Medidas", "Measures"),
    "pmode.dia_width": ("Largura (m)", "Width (m)"),
    "pmode.dia_height": ("Altura (m)", "Height (m)"),
    "pmode.dia_depth": ("Profundidade (m)", "Depth (m)"),
    "pmode.dia_position": ("Posição", "Position"),
    "pmode.dia_x": ("Posição X (m)", "Position X (m)"),
    "pmode.dia_y": ("Posição Y (m)", "Position Y (m)"),
    "pmode.dia_elevation": ("Elevação (m)", "Elevation (m)"),
    "pmode.dia_base_hint": ("Posição do centro da base. A elevação é vertical.",
                            "Where the middle of the base is. The elevation is vertical."),
    "pmode.dia_rotation": ("Rotação", "Rotation"),
    "pmode.dia_rot_x": ("Rodar X (°)", "Rotate X (°)"),
    "pmode.dia_rot_v": ("Rodar vertical (°)", "Rotate vertical (°)"),
    "pmode.dia_rot_y": ("Rodar Y (°)", "Rotate Y (°)"),
    "pmode.dia_scale": ("Escala", "Scale"),
    "pmode.dia_scale_x": ("Escala X", "Scale X"),
    "pmode.dia_scale_v": ("Escala vertical", "Vertical scale"),
    "pmode.dia_scale_y": ("Escala Y", "Scale Y"),
    "pmode.dia_reset": ("Repor rotação e escala", "Reset rotation and scale"),
    "pmode.dia_appearance": ("Aparência", "Appearance"),
    "pmode.dia_colour": ("Cor do volume", "Volume colour"),
    "pmode.dia_opacity": ("Opacidade (%)", "Opacity (%)"),
    "pmode.dia_wireframe": ("Mostrar estrutura de linhas", "Show as lines"),
    "pmode.dia_description": ("Descrição", "Description"),
    "pmode.dia_dup_scene": ("Duplicar cena com estes volumes", "Duplicate the scene with these volumes"),
    "pmode.dia_put": ("Volume «{name}» criado ao lado do modelo: as medidas, a posição e a cor editam-se na coluna da "
                      "direita.", "Volume «{name}» made beside the model: its measures, position and colour are "
                      "edited in the right column."),
    "pmode.dia_removed": ("Volume «{name}» removido.", "Volume «{name}» removed."),
    "pmode.dia_full": ("Esta cena já tem {n} volumes: o máximo.", "This scene has {n} volumes already: the most."),
    "pmode.cmd_dia_add": ("Criar volume", "Create volume"),
    "pmode.cmd_dia": ("Editar volume", "Edit volume"),
    "pmode.cmd_dia_remove": ("Remover volume", "Remove volume"),
    "pmode.cmd_dia_dup": ("Duplicar volume", "Duplicate volume"),
    # (0.492) the volumes edited with the mouse and the Modelagem's tools
    "pmode.dia_chosen": ("Volume «{name}»: arraste-o para o mover; as pegas mudam uma face (a oposta fica). A grelha "
                         "anda de 10 em 10 cm; Shift: sem grelha. Mover, Rodar e Escala da Modelagem também o mudam.",
                         "Volume «{name}»: drag it to move it; the grips change one face (the opposite one stays). The "
                         "grid goes by 10 cm; Shift: no grid. The Modelagem's Move, Rotate and Scale change it too."),
    "hint.dia_face": ("Arraste a face: só ela se mexe, a oposta fica. Shift: sem a grelha de 10 cm.",
                      "Drag the face: only it moves, the opposite one stays. Shift: without the 10 cm grid."),
    "pmode.dia_moved": ("Volume movido {d}.", "Volume moved {d}."),
    "pmode.dia_rotated": ("Volume rodado {a}.", "Volume rotated {a}."),
    "pmode.dia_scaled": ("Volume em escala × {f}.", "Volume scaled × {f}."),
    # (0.493) «Combinar e recortar» (the Presentation's DiagramBooleanPanel, its words)
    "pmode.dia_bool_title": ("Combinar e recortar", "Combine and cut"),
    "pmode.dia_bool_intro": ("Crie uma forma a partir de dois sólidos. As origens ficam guardadas e o resultado volta a "
                             "ser calculado sozinho quando uma delas muda.",
                             "Make a shape from two solids. The origins are kept and the result is calculated again by "
                             "itself when one of them changes."),
    "pmode.dia_bool_a": ("Volume A", "Volume A"),
    "pmode.dia_bool_b": ("Volume B", "Volume B"),
    "pmode.dia_bool_swap": ("Trocar A e B", "Swap A and B"),
    "pmode.dia_bool_operation": ("Operação entre volumes", "Operation between volumes"),
    "pmode.dia_bool_short.union": ("União", "Union"),
    "pmode.dia_bool_short.subtract": ("A − B", "A − B"),
    "pmode.dia_bool_short.reverse_subtract": ("B − A", "B − A"),
    "pmode.dia_bool_short.intersect": ("Interseção", "Intersection"),
    "pmode.dia_bool_short.difference": ("Diferença", "Difference"),
    "pmode.dia_bool_name.union": ("União", "Union"),
    "pmode.dia_bool_name.subtract": ("Subtração A − B", "Subtraction A − B"),
    "pmode.dia_bool_name.reverse_subtract": ("Subtração B − A", "Subtraction B − A"),
    "pmode.dia_bool_name.intersect": ("Interseção", "Intersection"),
    "pmode.dia_bool_name.difference": ("Diferença (partes não comuns)", "Difference (parts not shared)"),
    "pmode.dia_bool_hint.union": ("Junta os dois volumes e remove as faces interiores.",
                                  "Joins the two volumes and removes the faces inside."),
    "pmode.dia_bool_hint.subtract": ("Retira do volume A a parte ocupada por B.",
                                     "Takes from volume A the part B fills."),
    "pmode.dia_bool_hint.reverse_subtract": ("Retira do volume B a parte ocupada por A.",
                                             "Takes from volume B the part A fills."),
    "pmode.dia_bool_hint.intersect": ("Mantém apenas a parte comum aos dois volumes.",
                                      "Keeps only the part the two volumes share."),
    "pmode.dia_bool_hint.difference": ("Mantém as partes que pertencem apenas a A ou apenas a B.",
                                       "Keeps the parts that belong to A only or to B only."),
    "pmode.dia_bool_hide": ("Ocultar origens ao aplicar", "Hide the origins when applying"),
    "pmode.dia_bool_locked_stay": ("Origens bloqueadas permanecem visíveis.", "Locked origins stay visible."),
    "pmode.dia_bool_apply": ("Aplicar à cena (novo resultado)", "Apply to the scene (new result)"),
    "pmode.dia_bool_update": ("Atualizar o resultado escolhido", "Update the chosen result"),
    "pmode.dia_bool_update_named": ("Atualizar «{name}» com estes", "Update «{name}» with these"),
    "pmode.dia_bool_hidden": (" · oculto", " · hidden"),
    "pmode.dia_bool_gone": ("Origem ausente", "Origin missing"),
    "pmode.dia_bool_from": ("{a} + {b} → {op} · {v} m³", "{a} + {b} → {op} · {v} m³"),
    "pmode.dia_bool_done": ("«{name}»: {v} m³. As origens ficaram guardadas; Ctrl+Z desfaz.",
                            "«{name}»: {v} m³. The origins are kept; Ctrl+Z undoes it."),
    "pmode.dia_bool_stale": ("«{name}» não pôde ser calculado outra vez e ficou como estava: {why}",
                             "«{name}» could not be calculated again and stays as it was: {why}"),
    "pmode.dia_bool_used": ("«{name}» é origem de «{result}»: apague primeiro o resultado.",
                            "«{name}» is an origin of «{result}»: delete the result first."),
    "pmode.cmd_dia_bool": ("Combinar volumes", "Combine volumes"),
    "pmode.dia_bool_err.pick_different": ("Escolha dois volumes diferentes.", "Choose two different volumes."),
    "pmode.dia_bool_err.cycle": ("Esta ligação criaria um ciclo entre resultados.",
                                 "This link would make a cycle between results."),
    "pmode.dia_bool_err.chain_limit": ("A cadeia admite até oito operações. Use uma composição mais simples.",
                                       "A chain takes up to eight operations. Use a simpler composition."),
    "pmode.dia_bool_err.source_gone": ("Um volume de origem já não está disponível.",
                                       "An origin volume is no longer there."),
    "pmode.dia_bool_err.plane_thin": ("O plano não tem espessura. Use uma caixa para fazer o corte.",
                                      "The plane has no thickness. Use a box to make the cut."),
    "pmode.dia_bool_err.plane_not_solid": ("O plano não é um sólido fechado. Use uma caixa com espessura.",
                                           "The plane is not a closed solid. Use a box with thickness."),
    "pmode.dia_bool_err.triangle_limit": ("A geometria excede o limite de 50 000 triângulos por volume.",
                                          "The geometry exceeds the limit of 50,000 triangles per volume."),
    "pmode.dia_bool_err.bad_coords": ("A malha contém coordenadas inválidas.", "The mesh has invalid coordinates."),
    "pmode.dia_bool_err.not_closed": ("A malha não forma um sólido fechado com faces orientadas. Nenhum volume foi "
                                      "alterado.",
                                      "The mesh is not a closed solid with oriented faces. No volume was changed."),
    "pmode.dia_bool_err.source_validation": ("Não foi possível validar os sólidos de origem.",
                                             "The origin solids could not be checked."),
    "pmode.dia_bool_err.no_engine": ("Falta a biblioteca manifold3d no Python do programa (scripts/wsl_setup.sh "
                                     "instala-a): sem ela os volumes não se combinam.",
                                     "The manifold3d library is missing from the program's Python "
                                     "(scripts/wsl_setup.sh installs it): without it volumes are not combined."),
    "pmode.dia_bool_err.unknown_op": ("Operação desconhecida.", "Unknown operation."),
    "pmode.dia_bool_err.bad_dimensions": ("Os volumes não têm dimensões válidas.", "The volumes have no valid size."),
    "pmode.dia_bool_err.invalid_result": ("A operação não produziu uma geometria válida.",
                                          "The operation did not give a valid geometry."),
    "pmode.dia_bool_err.empty_result": ("O resultado é vazio: não há volume restante nesta operação. As origens foram "
                                        "mantidas.",
                                        "The result is empty: no volume is left by this operation. The origins were "
                                        "kept."),
    "pmode.dia_bool_err.result_triangle_limit": ("O resultado excede 50 000 triângulos. Simplifique os volumes de "
                                                 "origem.",
                                                 "The result exceeds 50,000 triangles. Simplify the origin volumes."),
    "pmode.dia_bool_err.result_range": ("O resultado tem uma dimensão fora do intervalo de 0,01 a 10 000 metros.",
                                        "The result has a size outside 0.01 to 10,000 metres."),
    "pmode.dia_bool_err.save_validation": ("Não foi possível validar o resultado para gravação.",
                                           "The result could not be checked for saving."),
    "pmode.dia_bool_err.unlock_first": ("Desbloqueie o resultado antes de o atualizar.",
                                        "Unlock the result before updating it."),
    "pmode.dia_bool_err.full": ("A cena já tem 100 volumes.", "The scene already has 100 volumes."),
    # (0.486) the Presentation's «Efeitos» (its EffectsTab, its words)
    "pmode.effects_model": ("Modelo", "Model"),
    "pmode.effects_camera": ("Câmara", "Camera"),
    "pmode.effect_scene": ("Efeito da cena", "Scene effect"),
    "pmode.effect_kind.none": ("Nenhum", "None"),
    "pmode.effect_kind.sun": ("Estudo solar", "Sun study"),
    "pmode.effect_kind.construction": ("Construção", "Construction"),
    "pmode.effect_kind.explode": ("Explosão", "Explode"),
    "pmode.effect_hint.none": ("A cena apresenta-se sem animação de efeito.",
                               "The scene is shown with no effect animation."),
    "pmode.effect_hint.sun": ("Anima o percurso do sol ao longo do dia — sombras em movimento para estudo solar. Usa o "
                              "lugar do terreno e a data do separador Ambiente.",
                              "Animates the sun's path through the day — moving shadows for a sun study. It uses the "
                              "site's place and the date of the Environment tab."),
    "pmode.effect_hint.construction": ("O edifício constrói-se por ordem lógica de obra: terreno e fundações, "
                                       "estrutura, paredes, portas e janelas, escadas, cobertura, acabamentos e "
                                       "mobiliário.",
                                       "The building is built in the logical order of the works: terrain and "
                                       "foundations, structure, walls, doors and windows, stairs, roof, finishes and "
                                       "furniture."),
    "pmode.effect_hint.explode": ("Os elementos começam afastados e montam-se aleatoriamente até formar o modelo.",
                                  "The elements start apart and come together at random until they form the model."),
    "pmode.effect_time": ("Duração", "Duration"),
    "pmode.effect_auto": ("Reproduzir ao entrar na cena", "Play when the scene is entered"),
    "pmode.effect_auto_tip": ("Na apresentação o efeito toca sozinho ao chegar a esta cena (aqui, com o ▶ das cenas).",
                              "In the presentation the effect plays by itself when this scene is reached (here, with "
                              "the scenes' ▶)."),
    "pmode.effect_spread": ("Distância", "Distance"),
    "pmode.effect_spread_tip": ("Quão longe as peças começam: vezes o raio do modelo.",
                                "How far the pieces start: times the model's radius."),
    "pmode.effect_sun_hint": ("Dica: escolha o lugar do terreno (Terreno ▸ Localização) e acerte a data no separador "
                              "Ambiente para um estudo solar correto. A duração é o tempo do dia completo.",
                              "Tip: choose the site's place (Site ▸ Location) and set the date in the Environment tab "
                              "for a correct sun study. The duration is the whole day's time."),
    "pmode.effect_preview": ("Pré-visualizar", "Preview"),
    "pmode.effect_preview_tip": ("Tocar o efeito no 3D como o Presentation o toca. Esc para.",
                                 "Play the effect in the 3D view as the Presentation plays it. Esc stops it."),
    "pmode.effect_order": ("Sequência de construção · {n} elementos", "Construction sequence · {n} elements"),
    "pmode.effect_order_tip": ("Desmarque um elemento para o remover do efeito: fica visível e estático.",
                               "Untick an element to take it out of the effect: it stays visible and still."),
    "pmode.effect_order_note": ("Elementos removidos do efeito ficam visíveis e estáticos (ex.: terreno). A ordem é a "
                                "de obra e, dentro de cada fase, de baixo para cima.",
                                "Elements taken out of the effect stay visible and still (e.g. the terrain). The order "
                                "is the works' and, within each phase, from the bottom up."),
    "pmode.effect_saved": ("O efeito grava-se nesta cena e reproduz-se na apresentação ao entrar na cena (Tour, "
                           "Narração e Navegação Livre).",
                           "The effect is kept in this scene and plays in the presentation when the scene is entered "
                           "(Tour, Narration and Free Navigation)."),
    "pmode.effect_restore": ("Repor no efeito", "Put back in the effect"),
    "pmode.effect_exclude": ("Remover do efeito (fica estático)", "Take out of the effect (stays still)"),
    "pmode.phase.site": ("Terreno", "Terrain"),
    "pmode.phase.foundation": ("Fundações", "Foundations"),
    "pmode.phase.structure": ("Estrutura", "Structure"),
    "pmode.phase.walls": ("Paredes", "Walls"),
    "pmode.phase.openings": ("Portas e Janelas", "Doors and Windows"),
    "pmode.phase.stairs": ("Escadas", "Stairs"),
    "pmode.phase.roof": ("Cobertura", "Roof"),
    "pmode.phase.finishes": ("Acabamentos", "Finishes"),
    "pmode.phase.fixtures": ("Equipamento e Mobiliário", "Fittings and Furniture"),
    "pmode.phase.other": ("Outros", "Others"),
    "info.effect_playing": ("{name}: {n} elementos em {s} s, como no Presentation. Esc para parar.",
                            "{name}: {n} elements in {s} s, as in the Presentation. Esc stops it."),
    # (0.485) the Presentation's «Etiquetas» (its LabelsTab, its words)
    "tool.pres_label": ("Etiqueta", "Label"),
    "pmode.tag_add": ("Adicionar etiqueta", "Add label"),
    "pmode.tag_place.floor": ("Piso", "Floor"),
    "pmode.tag_place.wall": ("Parede", "Wall"),
    "pmode.tag_place.standing": ("Em pé", "Standing"),
    "pmode.tag_place.wall_leader": ("Chamada", "Leader"),
    "pmode.tag_place_tip.floor": ("Deitada no piso — complanar ao piso, como pintura no pavimento.",
                                  "Flat on the floor — coplanar with the floor, like paint on the paving."),
    "pmode.tag_place_tip.wall": ("Colada à parede — complanar à superfície vertical clicada.",
                                 "On the wall — coplanar with the clicked vertical surface."),
    "pmode.tag_place_tip.standing": ("Em pé no piso — vertical, com poste(s) apoiados no ponto clicado.",
                                     "Standing on the floor — upright, on post(s) at the clicked point."),
    "pmode.tag_place_tip.wall_leader": ("Parede com chamada — afastada da parede por uma linha de chamada horizontal.",
                                        "Wall with leader — held off the wall by a horizontal leader line."),
    "pmode.tag_place_hint": ("Clique numa superfície do modelo para colocar a etiqueta. Esc cancela.",
                             "Click a surface of the model to place the label. Esc cancels."),
    "pmode.tag_empty": ("Sem etiquetas. Escolha uma colocação acima e clique no modelo — nome do ambiente, área/nota e "
                        "estilo editam-se aqui.",
                        "No labels. Choose a placement above and click the model — the room's name, area/note and "
                        "style are edited here."),
    "pmode.tag_saved": ("O olho oculta a etiqueta no estado actual — guarda-se na cena ao Criar/Atualizar cena. As "
                        "etiquetas e o estilo são globais ao modelo.",
                        "The eye hides the label in the current state — it is kept in the scene on Create/Update "
                        "scene. The labels and their style are the model's."),
    "pmode.tag_unnamed": ("sem nome", "unnamed"),
    "pmode.tag_edit": ("Editar {name}", "Edit {name}"),
    "pmode.tag_close": ("Fechar {name}", "Close {name}"),
    "pmode.tag_show": ("Mostrar nesta cena: {name}", "Show in this scene: {name}"),
    "pmode.tag_hide": ("Ocultar nesta cena: {name}", "Hide in this scene: {name}"),
    "pmode.tag_name": ("Nome", "Name"),
    "pmode.tag_name_hint": ("Nome do ambiente", "Room name"),
    "pmode.tag_note": ("Nota", "Note"),
    "pmode.tag_note_hint": ("Nota ou área (ex.: 55 m²)", "Note or area (e.g. 55 m²)"),
    "pmode.tag_letter": ("Tamanho da letra", "Letter size"),
    "pmode.tag_delete": ("Apagar", "Delete"),
    "pmode.tag_shape": ("Forma", "Shape"),
    "pmode.tag_shape.rect": ("Retângulo", "Rectangle"),
    "pmode.tag_shape.circle": ("Círculo", "Circle"),
    "pmode.tag_number": ("Número da etiqueta", "Label number"),
    "pmode.tag_number_hint": ("Nº", "No."),
    "pmode.tag_background": ("Fundo", "Background"),
    "pmode.tag_text": ("Texto", "Text"),
    "pmode.tag_opacity": ("Opacidade", "Opacity"),
    "pmode.tag_size": ("Tamanho", "Size"),
    "pmode.tag_steps": ("Rotação em passos de 45°", "Rotation in steps of 45°"),
    "pmode.tag_rotation": ("Rotação", "Rotation"),
    "pmode.tag_post": ("Poste", "Pole"),
    "pmode.tag_callout": ("Chamada", "Leader"),
    "pmode.tag_face": ("Virar para a câmara", "Face the camera"),
    "pmode.tag_face_tip": ("A etiqueta acompanha a câmara. Desligado, mantém a orientação fixa em que foi colocada.",
                           "The label turns to follow the camera. Off, it keeps the fixed orientation it was placed "
                           "with."),
    "pmode.tag_occluded": ("Ocultar quando tapada", "Hide when covered"),
    "pmode.tag_occluded_tip": ("Desaparece quando há paredes ou lajes entre a câmara e a etiqueta.",
                               "It disappears when walls or slabs are between the camera and the label."),
    "pmode.tag_word": ("Ambiente", "Room"),
    "pmode.tag_nowhere": ("Aponte para o modelo ou para o chão para pôr a etiqueta.",
                          "Point at the model or at the ground to put the label."),
    "pmode.tag_put": ("Etiqueta «{name}» posta: o nome, a nota e o aspeto editam-se na coluna da direita.",
                      "Label «{name}» put: its name, note and look are edited in the right column."),
    "pmode.tag_removed": ("Etiqueta «{name}» apagada.", "Label «{name}» deleted."),
    "pmode.tag_full": ("O modelo já tem {n} etiquetas: o máximo.", "The model has {n} labels already: the most."),
    "pmode.cmd_tag_add": ("Pôr etiqueta", "Put label"),
    "pmode.cmd_tag": ("Editar etiqueta", "Edit label"),
    "pmode.cmd_tag_remove": ("Apagar etiqueta", "Delete label"),
    "pmode.prev_scene": ("Cena anterior", "Previous scene"),
    "pmode.next_scene": ("Cena seguinte", "Next scene"),
    "pmode.play_scenes": ("Reproduzir as cenas, uma a seguir à outra", "Play the scenes, one after the other"),
    "pmode.pause_scenes": ("Pausar", "Pause"),
    "pmode.scene_time": ("Tempo da cena · {s} s", "Scene time · {s} s"),
    "pmode.end_page": ("Página final", "End page"),
    "pmode.end_page_note": ("Feita no Presentation", "Made in the Presentation"),
    "pmode.end_page_tip": ("A página final (contactos, agradecimento) faz-se no Presentation; o BIM não a envia.",
                           "The end page (contacts, thanks) is made in the Presentation; the BIM does not send it."),
    "pmode.look_tip": ("Modo de visualização, qualidade e oclusão ambiente", "Visual mode, quality and ambient "
                       "occlusion"),
    "pmode.look_modes": ("Modo de visualização", "Visual mode"),
    "pmode.style.rendered": ("Renderizado", "Rendered"),
    "pmode.style.material": ("Com material", "With material"),
    "pmode.style.no_texture": ("Sem textura", "No texture"),
    "pmode.style.no_material": ("Sem material", "No material"),
    "pmode.style.clay": ("Clay / maqueta", "Clay / model"),
    "pmode.style.white_concept": ("Branco conceptual", "Conceptual white"),
    "pmode.style.technical_lines": ("Linhas técnicas", "Technical lines"),
    "pmode.style.xray": ("Raio-X", "X-ray"),
    "pmode.style.diagrammatic": ("Diagramático", "Diagrammatic"),
    "pmode.quality": ("Qualidade", "Quality"),
    "pmode.quality.high": ("Alta", "High"),
    "pmode.quality.medium": ("Média", "Medium"),
    "pmode.quality.low": ("Baixa", "Low"),
    "pmode.quality.auto": ("Auto", "Auto"),
    "pmode.ao": ("Oclusão ambiente", "Ambient occlusion"),
    "pmode.ao_intensity": ("Intensidade", "Strength"),
    "pmode.apply_all": ("Aplicar a todas as cenas", "Apply to all scenes"),
    "pmode.apply_all_tip": ("O modo, a qualidade e a oclusão escolhidos passam logo para todas as cenas.",
                            "The mode, quality and occlusion chosen go at once to every scene."),
    "pmode.sun_tip": ("O sol da cena (hora, azimute, altura): ajuste-o em Ambiente.",
                      "The scene's sun (hour, azimuth, altitude): set it in Environment."),
    "tab.presentation": ("ArqSynth Presentation", "ArqSynth Presentation"),
    "move.cat.exterior": ("Exterior", "Exterior"),
    "move.cat.aereo": ("Aéreo", "Aerial"),
    "move.cat.cinematografico": ("Cinematográfico", "Cinematic"),
    "move.cat.interior": ("Interior", "Interior"),
    "move.orbit_90": ("Órbita 90°", "Orbit 90°"),
    "move.orbit_180": ("Órbita 180°", "Orbit 180°"),
    "move.orbit_360": ("Órbita 360°", "Orbit 360°"),
    "move.orbit_rising": ("Órbita ascendente", "Rising orbit"),
    "move.orbit_descending": ("Órbita descendente", "Descending orbit"),
    "move.facade_wrap": ("Contorno de fachada", "Around the corner"),
    "move.aerial_orbit": ("Voo perimetral", "Perimeter flight"),
    "move.aerial_descent": ("Descida de aproximação", "Approach descent"),
    "move.dolly_in": ("Aproximação", "Dolly in"),
    "move.pull_back": ("Recuo com revelação", "Pull back reveal"),
    "move.lateral_travel": ("Deslocamento lateral", "Lateral travel"),
    "move.facade_rise": ("Subida de fachada", "Facade rise"),
    "move.hero_shot": ("Vista principal", "Hero shot"),
    "move.int_spiral_up": ("Espiral ascendente", "Rising spiral"),
    "move.int_spiral_down": ("Espiral descendente", "Descending spiral"),
    "move.int_orbit_full": ("Volta ao compartimento", "Round the room"),
    "move.int_wrap": ("Contorno do compartimento", "Along the walls"),
    "move.int_dolly_in": ("Aproximação interior", "Interior dolly in"),
    "move.int_pull_back": ("Recuo revelador", "Interior pull back"),
    "move.int_lateral": ("Deslocamento lateral interior", "Interior lateral travel"),
    "move.int_vertical": ("Deslocamento vertical", "Vertical travel"),
    "tip.new": ("Começa um projeto novo, vazio (pergunta antes se o atual tiver alterações por guardar).",
                "Starts a new, empty project (asks first if the current one has changes not saved)."),
    "tip.open": ("Abre um projeto (IFC). Da segunda vez abre muito mais depressa: as formas ficam guardadas.",
                 "Opens a project (IFC). The second time it opens much faster: the shapes are kept."),
    "tip.save": ("Guarda o projeto no seu ficheiro IFC (e as vistas, cotas e folhas no ficheiro ao lado).",
                 "Saves the project in its IFC file (and the views, dimensions and sheets in the file beside it)."),
    "tip.save_as": ("Guarda o projeto noutro ficheiro, com outro nome.", "Saves the project in another file, under "
                                                                         "another name."),
    "tip.cad_link": ("Liga uma planta em DXF ou DWG ao pavimento ativo, como linhas para desenhar por cima (nas "
                     "coordenadas do levantamento quando estão perto delas).",
                     "Links a DXF or DWG plan to the active storey, as lines to draw over (in the survey's coordinates "
                     "when near them)."),
    "tip.cloud_link": ("Liga uma nuvem de pontos de um levantamento (XYZ, PTS, PLY, LAS, LAZ, E57) ao pavimento ativo, "
                       "para modelar por cima dela.", "Links a survey's point cloud (XYZ, PTS, PLY, LAS, LAZ, E57) to "
                                                      "the active storey, to model over it."),
    "tip.import_image": ("Põe uma imagem (uma planta digitalizada…) deitada no pavimento ativo; a seguir, a ferramenta "
                         "Calibrar imagem acerta-lhe a escala com uma medida conhecida.",
                         "Lays a picture (a scanned plan…) flat on the active storey; then the Calibrate image tool sets "
                         "its scale by a known length."),
    "tip.terrain_points": ("Faz o terreno a partir de um ficheiro de pontos de levantamento (x y z por linha: CSV, "
                           "TXT, XYZ), com as curvas de nível.",
                           "Makes the terrain from a file of survey points (x y z a line: CSV, TXT, XYZ), with its "
                           "contour lines."),
    "tip.terrain_dxf": ("Faz o terreno a partir de um levantamento em DXF/DWG: os pontos, curvas de nível e cotas "
                        "escritas das camadas que escolher.", "Makes the terrain from a DXF/DWG survey: the points, "
                                                              "contour lines and written heights of the layers chosen."),
    "tip.import_components": ("Traz para a biblioteca do projeto os componentes (móveis, louças…) de outro ficheiro "
                              "IFC, para pôr cópias deles.", "Brings another IFC file's components (furniture, "
                                                             "fixtures…) into the project's library, to place copies."),
    "tip.pdf": ("O corte ou alçado que está à frente (senão, a planta do pavimento ativo) em PDF, num A3, à maior escala "
                "habitual que caiba (Ctrl+P).", "The section or elevation in front (else the active storey's plan) as "
                                                "a PDF, on A3, at the largest usual scale that fits (Ctrl+P)."),
    "tip.dxf": ("O corte ou alçado que está à frente (senão, a planta do pavimento ativo) em DXF ou DWG para o AutoCAD e "
                "outros programas (em metros, cada tipo de linha na sua camada), ou em SVG para o Illustrator, o "
                "Inkscape e a internet (desenhado como nas folhas, à escala da vista). Escolhe-se no tipo, ao gravar.",
                "The section or elevation in front (else the active storey's plan) as a DXF or DWG for AutoCAD and the "
                "others (in metres, each kind of line on its own layer), or as an SVG for Illustrator, Inkscape and "
                "the web (drawn as on the sheets, at the view's scale). Chosen in the type, when saving."),
    "tip.sheets_pdf": ("Todas as folhas do projeto num PDF, uma por página.", "All the project's sheets in one PDF, a "
                                                                              "page each."),
    "tip.splat": ("O modelo em Gaussian splat (PLY), para o apresentar nos visualizadores da internet; com as nuvens de "
                  "pontos ligadas, se quiser.", "The model as a Gaussian splat (PLY), to present in the web viewers; "
                                                "with the linked point clouds, if wanted."),
    "tip.help": ("Abre o painel Ajuda (F1): a ferramenta em uso, procurar um comando, uns primeiros passos e as teclas.",
                 "Opens the Help panel (F1): the tool in use, find a command, first steps and the keys."),
    "tip.delete": ("Apaga o que está escolhido (Del). Numa folha, tira de lá a vista escolhida (o modelo fica).",
                   "Deletes what is chosen (Del). On a sheet, takes the chosen view off it (the model stays)."),
    "tip.component_make": ("Faz um componente dos volumes de esboço escolhidos (G): as cópias dele mudam todas juntas.",
                           "Makes a component of the chosen sketch volumes (G): its copies all change together."),
    "tip.group_make": ("Junta os elementos escolhidos num grupo (Ctrl+G), para os copiar e mover juntos.",
                       "Puts the chosen elements in a group (Ctrl+G), to copy and move together."),
    "tip.materials": ("A janela dos materiais: nome, cor, tramas da superfície e do corte, transparência, acabamento "
                      "no render, densidade e condutibilidade térmica; novo, duplicar, apagar um sem uso.",
                      "The materials window: name, colour, surface and cut patterns, transparency, render finish, "
                      "density and thermal conductivity; new, duplicate, delete an unused one."),
    "tip.site_location": ("A latitude, a longitude e a cota do terreno: o sítio do modelo no mundo (para a "
                          "certificação, os outros programas e o sol do render).",
                          "The site's latitude, longitude and height: the model's place on Earth (for certification, "
                          "the other programs and the render's sun)."),
    "tip.storey_new": ("Acrescenta um pavimento 3 m acima do último e passa a ser o ativo.",
                       "Adds a storey 3 m over the last one; it becomes the active one."),
    "tip.storey_up": ("Passa para o pavimento de cima: as ferramentas desenham nele e a planta (F4) mostra-o. PgDn "
                      "desce.", "Goes to the storey above: the tools draw on it and the plan (F4) shows it. PgDn goes "
                                "down."),
    "tip.repeat": ("Copia o que está escolhido para outros pavimentos, no mesmo sítio.",
                   "Copies what is chosen to other storeys, in the same place."),
    "tip.typical": ("Pisos tipo: o pavimento ativo fica igual aos que escolher — o que se desenha, muda ou apaga num "
                    "passa a todos. Outra vez: deixam de ser iguais.",
                    "Typical floors: the active storey made equal to those chosen — what is drawn, changed or deleted "
                    "on one is on all. Again: no longer equal."),
    "tip.walls_from_cad": ("Lê as paredes de um desenho DXF ligado (pares de linhas paralelas nas camadas que "
                           "escolher), mostra-as e faz o modelo, cada uma do tipo da sua espessura.",
                           "Reads the walls of a linked DXF drawing (pairs of parallel lines on the layers chosen), "
                           "shows them and makes the model, each of the type of its thickness."),
    "tip.model_from_scan": ("Lê numa nuvem de pontos ligada o chão, a altura e as paredes (e as portas e janelas), "
                            "mostra-as e faz o modelo com a laje do piso.",
                            "Reads in a linked point cloud the floor, the height and the walls (and the doors and "
                            "windows), shows them and makes the model with the floor slab."),
    "tip.earthworks": ("As plataformas do terreno com a terra que cada uma tira e põe, e os totais.",
                       "The terrain's platforms with the earth each takes away and brings, and the totals."),
    "tip.slopes": ("Pinta o terreno pela inclinação, com a legenda (também nas folhas da planta).",
                   "Colours the terrain by its slope, with the legend (on the plan's sheets too)."),
    "tip.profile_from_face": ("Guarda a face plana de esboço escolhida como perfil do projeto, com um nome: a "
                              "ferramenta Perfil corre-o ao longo de paredes, lajes ou linhas.",
                              "Keeps the chosen flat sketch face as a profile of the project, under a name: the Profile "
                              "tool runs it along walls, slabs or lines."),
    "tip.worktop": ("Põe um tampo de bancada por cima dos módulos baixos escolhidos (nenhum: todos os do pavimento).",
                    "Puts a worktop over the base units chosen (none: all those of the storey)."),
    "tip.cut_list": ("A lista de corte dos móveis escolhidos (nenhum: todos): os painéis e as ferragens, os ripados e "
                     "perfurados; para CSV ou para o DXF da CNC.", "The cut list of the chosen cabinets (none: all): "
                                                                   "panels and hardware, slats and perforated panels; "
                                                                   "to CSV or to the CNC's DXF."),
    "tip.grid_generate": ("Gera os eixos da grelha estrutural: quantos, numerados e com letras, a que distância (uma "
                          "medida, ou várias separadas por «;»), a partir de que ponto.",
                          "Generates the structural grid's axes: how many, numbered and lettered, how far apart (one "
                          "length, or several separated by «;»), from which point."),
    "tip.grid_settings": ("A grelha estrutural: os nomes dos eixos (números ou letras), renumerar, as cotas entre eixos "
                          "nas plantas, o tamanho das bolhas.",
                          "The structural grid: the axes' names (numbers or letters), renumbering, the dimensions "
                          "between axes on the plans, the bubbles' size."),
    "tip.analyse": ("Analisa a estrutura com as suas ações: os esforços e as deformações de cada barra, o caminho das "
                    "cargas, os deslocamentos pelo vento e o sismo.",
                    "Analyses the structure with its actions: each member's forces and deflections, the load path, the "
                    "sway under wind and earthquake."),
    "tip.analytical": ("Faz de novo o modelo analítico a partir dos pilares, vigas, sapatas, lajes e paredes "
                       "resistentes, e lista os seus problemas (pilares sem apoio, vigas soltas…).",
                       "Makes the analytical model again from the columns, beams, footings, slabs and load-bearing "
                       "walls, and lists its problems (unsupported columns, loose beams…)."),
    "tip.actions": ("As ações e os materiais da estrutura: betão, aço, uso dos pisos, acabamentos, vento, sismo, neve, "
                    "solo, alvenaria — com as cargas de cada pavimento.",
                    "The structure's actions and materials: concrete, steel, the floors' use, finishes, wind, "
                    "earthquake, snow, soil, masonry — with each storey's loads."),
    "tip.show_analytical": ("Mostra o modelo analítico (barras, nós, apoios) por cima do modelo.",
                            "Shows the analytical model (members, nodes, supports) over the model."),
    "tip.verify_ec2": ("Verifica cada elemento pelo Eurocódigo 2 (betão) e as paredes de alvenaria pelo 6, com os "
                       "esforços da análise; escolhe as armaduras e pode pô-las no modelo.",
                       "Checks each member by Eurocode 2 (concrete) and the masonry walls by Eurocode 6, with the "
                       "analysis's forces; chooses the reinforcement and can put it in the model."),
    "tip.rebar_schedule": ("A lista das armaduras do modelo por posição, com os totais; para Excel ou CSV.",
                           "The model's reinforcement listed by position, with the totals; to Excel or CSV."),
    "tip.structure_quantities": ("O betão, a cofragem e o aço de cada elemento estrutural, e os totais; para Excel ou "
                                 "CSV.", "Each structural member's concrete, formwork and steel, and the totals; to "
                                 "Excel or CSV."),
    "tip.calc_report": ("A memória de cálculo da estrutura (ações, modelo, análise, verificação, quantidades, "
                        "armaduras) numa página HTML ou num PDF.",
                        "The structure's calculation report (actions, model, analysis, check, quantities, "
                        "reinforcement) as an HTML page or a PDF."),
    "tip.share": ("Partilha o projeto numa pasta (da rede, do OneDrive…): fica lá o modelo central e cada um trabalha "
                  "numa cópia sua, que sincroniza.", "Shares the project in a folder (on the network, OneDrive…): the "
                                                     "central model stays there and each works on a copy of their own, "
                                                     "which they synchronise."),
    "tip.open_shared": ("Abre um projeto partilhado numa pasta: trabalha-se numa cópia local, que se sincroniza com o "
                        "central.", "Opens a project shared in a folder: one works on a local copy, synchronised with "
                                    "the central one."),
    "tip.cad_links": ("Os desenhos CAD ligados: unidades, visível, bloqueado e as suas camadas.",
                      "The linked CAD drawings: units, shown, locked and their layers."),
    "tip.cloud_links": ("As nuvens de pontos ligadas: o pavimento, os pontos mostrados, as unidades, o tamanho dos pontos, "
                        "visível; ligar outra, apagar.", "The linked point clouds: their storey, the points shown, "
                                                         "units, point size, shown; link another, delete."),
    "tip.check_ids": ("Verifica o modelo contra um ficheiro IDS (os requisitos de informação do dono de obra): cada "
                      "requisito cumprido ou não, e os elementos em falta.",
                      "Checks the model against an IDS file (the client's information requirements): each requirement "
                      "met or not, and the elements that fail."),
    "tip.new_note": ("Uma nota de coordenação (BCF): um título e uma descrição, com a vista como está, os elementos "
                     "escolhidos e uma imagem.", "A coordination note (BCF): a title and a description, with the view "
                                                 "as it is, the chosen elements and a picture."),
    "tip.keynote_table": ("A tabela de notas-chave do projeto (código e texto), para as etiquetas e a legenda.",
                          "The project's keynote table (code and text), for the tags and the legend."),
    "tip.graphic_styles": ("Como os desenhos ficam no papel: a trama de cada material cortado e as canetas (cortado, "
                           "visto, tramado, cotas).", "How the drawings look on paper: each cut material's pattern and "
                                                      "the pens (cut, seen, hatched, dimensions)."),
    "tip.images": ("As imagens de fundo: largura, opacidade, visível, bloqueada; importar, calibrar, apagar.",
                   "The background images: width, opacity, shown, locked; import, calibrate, delete."),
    "tip.theme_light": ("A interface clara (fica neste computador, não no projeto).",
                        "The light interface (kept on this computer, not in the project)."),
    "tip.theme_dark": ("A interface escura (fica neste computador, não no projeto).",
                       "The dark interface (kept on this computer, not in the project)."),
    # tools
    "tool.select": ("Selecionar", "Select"),
    "tool.rectangle": ("Retângulo", "Rectangle"),
    "tool.push_pull": ("Push/Pull", "Push/Pull"),
    "hint.select": ("Clique num elemento, numa linha (dois cliques: a cadeia) ou na face de um esboço (dois cliques: "
                    "com as arestas; três: o objeto todo), ou arraste uma caixa: para a direita, só o que fica todo "
                    "dentro; para a esquerda, tudo o que toca. Shift troca, Ctrl junta, Ctrl+Shift tira. Delete apaga.",
                    "Click an element, a line (double click: its chain) or a sketch's face (double click: with its "
                    "edges; triple: the whole object), or drag a box: rightwards, only what is wholly inside; "
                    "leftwards, all it touches. Shift toggles, Ctrl adds, Ctrl+Shift removes. Delete removes it."),
    # a face picked alone (0.310)
    "info.part_selected": ("Face selecionada ({a} m²). Dois cliques: com as arestas; três: o objeto todo. Delete "
                           "apaga-a, Mover (M) e Rodar (Q) só a ela.",
                           "Face selected ({a} m²). Double click: with its edges; triple: the whole object. Delete "
                           "removes it, Move (M) and Rotate (Q) just it."),
    "info.part_edges": ("Face e arestas selecionadas ({a} m²). Três cliques: o objeto todo.",
                        "Face and edges selected ({a} m²). Triple click: the whole object."),
    "info.parts_selected": ("{n} faces selecionadas ({a} m²).", "{n} faces selected ({a} m²)."),
    "info.part_deleted": ("{n} face(s) apagada(s).", "{n} face(s) deleted."),
    "info.part_moved": ("Face movida {d}: as faces ao lado acompanham.", "Face moved {d}: the faces beside it follow."),
    "info.part_rotated": ("Face rodada {a}: as faces ao lado acompanham.",
                          "Face rotated {a}: the faces beside it follow."),
    "err.part_copy": ("Uma face sozinha não se copia: três cliques selecionam o objeto todo para o copiar.",
                      "A face alone is not copied: a triple click selects the whole object to copy it."),
    # loose lines picked alone (0.373)
    "info.line_picked": ("Linha selecionada ({l}). Dois cliques: a cadeia; três: tudo o que lhe está ligado. Delete "
                         "apaga-a; Mover (M), Copiar, Rodar (Q), Offset (F) e Ctrl+C só a ela.",
                         "Line selected ({l}). Double click: its chain; triple: all joined to it. Delete removes it; "
                         "Move (M), Copy, Rotate (Q), Offset (F) and Ctrl+C just it."),
    "info.lines_picked": ("{n} linhas selecionadas ({l} no total).", "{n} lines selected ({l} in all)."),
    "info.lines_joined": ("{n} esboço(s) de linhas ligados selecionados.", "{n} joined line sketch(es) selected."),
    "info.curve_picked": ("Curva selecionada inteira ({k}). Dois cliques: tudo o que lhe está ligado.",
                          "Curve selected whole ({k}). Double click: all joined to it."),
    "info.lines_deleted": ("{n} linha(s) apagada(s).", "{n} line(s) deleted."),
    "info.lines_moved": ("Linha(s) movida(s) {d}: as linhas ligadas às pontas acompanham.",
                         "Line(s) moved {d}: the lines joined to their ends follow."),
    "info.lines_rotated": ("Linha(s) rodada(s) {a}: as linhas ligadas às pontas acompanham.",
                           "Line(s) rotated {a}: the lines joined to their ends follow."),
    "hint.curve_grip": ("Com o botão carregado, leve a pega para onde quer (a curva muda de forma; as linhas ligadas "
                        "às pontas acompanham) e largue. Esc desiste.",
                        "With the button held, take the grip where you want it (the curve changes its shape; the "
                        "lines joined to its ends follow) and let go. Esc gives up."),
    "info.curve_reshaped": ("{k}: forma mudada.", "{k}: shape changed."),
    "props.arc_radius": ("Raio", "Radius"),
    "props.arc_angle": ("Ângulo", "Angle"),
    "props.arc_segments": ("Segmentos", "Segments"),
    "props.bezier_points": ("Pontos", "Points"),
    "props.curve_hint": ("Escolhe-se inteira. Arraste as pegas (pontas e meio de um arco, pontos e tangentes de uma "
                         "Bézier; o «+» no meio de um troço põe-lhe um nó novo) para lhe mudar a forma; as linhas "
                         "ligadas às pontas acompanham.",
                         "Picked whole. Drag its grips (an arc's ends and middle, a Bézier's points and tangents; the "
                         "«+» halfway along a span puts a new point there) to change its shape; the lines joined to "
                         "its ends follow."),
    "info.arc_changed": ("Arco mudado: raio {r}, {a}, {n} segmentos.", "Arc changed: radius {r}, {a}, {n} segments."),
    "cmd.curve_edit": ("Mudar curva", "Change curve"),
    "curve.arc": ("Arco", "Arc"),
    "curve.freehand": ("Linha livre", "Freehand line"),
    "curve.bezier": ("Curva de Bézier", "Bézier curve"),
    "curve.curve": ("Curva", "Curve"),
    # selection (0.75)
    "hint.select_lasso": ("Laço livre: arraste à volta do que quer — para a direita, só o que fica todo dentro; para "
                          "a esquerda, tudo o que toca. Um clique seleciona um elemento.",
                          "Free lasso: drag round what you want — rightwards, only what is wholly inside; leftwards, "
                          "all it touches. A click selects one element."),
    "hint.select_polygon": ("Polígono: clique os vértices (o 1.º lado para a direita: só o que fica dentro; para a "
                            "esquerda: tudo o que toca). Enter, botão direito ou clique no 1.º ponto fecha. Esc "
                            "desiste.",
                            "Polygon: click its corners (first side rightwards: only what is inside; leftwards: all it "
                            "touches). Enter, the right button or a click on the first point closes it. Esc gives up."),
    "hint.select_fence": ("Cerca: clique os pontos de uma linha; fica selecionado tudo o que ela corta. Enter ou "
                          "botão direito termina. Esc desiste.",
                          "Fence: click the points of a line; all it crosses gets selected. Enter or the right "
                          "button ends it. Esc gives up."),
    "err.region_points": ("Faltam pontos: um polígono precisa de 3, uma cerca de 2.",
                          "More points needed: 3 for a polygon, 2 for a fence."),
    "info.selected": ("{n} selecionado(s).", "{n} selected."),
    "info.selected_none": ("Nada selecionado.", "Nothing selected."),
    "menu.selection": ("Seleção", "Selection"),
    # the contextual bar (0.85)
    "menu.context": ("Barra contextual", "Contextual bar"),
    "ctx.type": ("Tipo", "Type"),
    "ctx.height": ("Altura", "Height"),
    "ctx.reference": ("Linha de referência", "Location line"),
    "ctx.beam_top": ("Topo a", "Top at"),
    "ctx.axis_z": ("Eixo a", "Axis at"),
    "ctx.pad": ("Isolada", "Pad"),
    "ctx.strip": ("Corrida", "Strip"),
    "ctx.copy": ("Copiar (Ctrl)", "Copy (Ctrl)"),
    "ctx.storey": ("Pavimento", "Storey"),
    "ctx.placing": ("Colocar componente", "Place component"),
    "ctx.selected": ("{n} selecionado(s): {what}", "{n} selected: {what}"),
    "act.same_type": ("Mesmo tipo", "Same type"),
    # the placement keys (0.86)
    "ctx.angle": ("Rotação", "Rotation"),
    "ctx.insertion": ("Ponto de inserção", "Insertion point"),
    "ctx.flip": ("Do outro lado (F)", "Other side (F)"),
    "ins.0": ("centro", "centre"),
    "ins.1": ("canto inferior esquerdo", "bottom left corner"),
    "ins.2": ("meio de baixo", "bottom middle"),
    "ins.3": ("canto inferior direito", "bottom right corner"),
    "ins.4": ("meio da direita", "right middle"),
    "ins.5": ("canto superior direito", "top right corner"),
    "ins.6": ("meio de cima", "top middle"),
    "ins.7": ("canto superior esquerdo", "top left corner"),
    "ins.8": ("meio da esquerda", "left middle"),
    "info.turned": ("Rodado: {a}°.", "Turned: {a}°."),
    "info.insertion": ("Ponto de inserção: {p}.", "Insertion point: {p}."),
    "info.flipped": ("Vai para a outra face da parede (F volta).", "Goes on the wall's other face (F: back)."),
    "info.unflipped": ("Vai para a face da parede debaixo do rato.", "Goes on the wall's face under the mouse."),
    "info.axis_locked_x": ("Bloqueado no eixo vermelho (X). N solta.", "Locked on the red axis (X). N lets go."),
    "info.axis_locked_y": ("Bloqueado no eixo verde (Y). N solta.", "Locked on the green axis (Y). N lets go."),
    "info.axis_free": ("Eixo solto.", "Axis free."),
    "keys.column": ("R / Shift+R: rodar 90°  ·  Espaço / Shift+Espaço: ponto de inserção  ·  Esc: Selecionar",
                    "R / Shift+R: turn 90°  ·  Space / Shift+Space: insertion point  ·  Esc: Select"),
    "keys.footing": ("R / Shift+R: rodar 90° (sapata solta)  ·  Esc: Selecionar",
                     "R / Shift+R: turn 90° (a pad on its own)  ·  Esc: Select"),
    "keys.opening": ("F: para a outra face da parede  ·  Esc: Selecionar",
                     "F: to the wall's other face  ·  Esc: Select"),
    "keys.door": ("Rato numa face: abre para esse lado  ·  F: para o outro  ·  Espaço: dobradiças no outro aro  ·  "
                  "Esc: Selecionar",
                  "Mouse on a face: opens to that side  ·  F: to the other  ·  Space: hinges at the other jamb  ·  "
                  "Esc: Select"),                                                                  # (0.359)
    "info.door_hinge_other": ("As dobradiças vão para o outro aro (Espaço outra vez: as do tipo).",
                              "The hinges go to the other jamb (Space again: the type's)."),
    "info.door_hinge_type": ("As dobradiças ficam no aro do tipo.", "The hinges stay at the type's jamb."),
    "keys.place": ("R / Shift+R (ou Tab): rodar 90°  ·  Esc: Selecionar",
                   "R / Shift+R (or Tab): turn 90°  ·  Esc: Select"),
    "keys.chain": ("X / Y: bloquear o eixo vermelho / verde  ·  N: soltar  ·  Shift: bloquear a linha seguida",
                   "X / Y: lock the red / green axis  ·  N: let go  ·  Shift: lock the line followed"),
    "act.select_all": ("Selecionar tudo", "Select all"),
    "act.select_invert": ("Inverter seleção", "Invert selection"),
    "act.select_none": ("Limpar seleção", "Clear selection"),
    "act.drag_box": ("Retângulo", "Box"),
    "act.drag_lasso": ("Laço livre", "Free lasso"),
    "act.pick_polygon": ("Polígono", "Polygon"),
    "act.pick_fence": ("Cerca", "Fence"),
    "tip.drag_box": ("Arrastar faz um retângulo de seleção", "Dragging draws a selection box"),
    "tip.drag_lasso": ("Arrastar faz um laço livre à mão", "Dragging draws a free-hand lasso"),
    "act.drag_elements": ("Arrastar elementos", "Drag elements"),                                  # (0.427)
    "act.thin_lines": ("Linhas finas", "Thin lines"),                                              # (0.428)
    # (0.432) «W + letra»: the walls' commands by a second letter, as the addon's
    "chord.walls": ("W · Paredes — a seguir: W desenhar · T aparar · E estender · A alinhar · O ortogonalizar · "
                    "R rodar · S dividir · M espelhar · J / C junções · U ligar ao topo · B ligar à base · G pegas · "
                    "L as ligadas · Q edição rápida",
                    "W · Walls — then: W draw · T trim · E extend · A align · O orthogonalize · R rotate · S split · "
                    "M mirror · J / C joins · U attach top · B attach base · G grips · L the joined ones · Q quick "
                    "edit"),
    "chord.done": ("W + letra: {c}.", "W + letter: {c}."),
    "chord.no_walls": ("W L: escolha primeiro uma parede.", "W L: choose a wall first."),
    "chord.cmd.wall": ("Parede", "Wall"),
    "chord.cmd.trim_extend": ("Aparar e estender", "Trim and extend"),
    "chord.cmd.align": ("Alinhar", "Align"),
    "chord.cmd.orthogonalize": ("Ortogonalizar", "Orthogonalize"),
    "chord.cmd.rotate": ("Rodar", "Rotate"),
    "chord.cmd.split_wall": ("Dividir parede", "Split wall"),
    "chord.cmd.mirror": ("Espelhar", "Mirror"),
    "chord.cmd.wall_joins": ("Junções de paredes", "Wall joins"),
    "chord.cmd.attach_top": ("Ligar o topo", "Attach top"),
    "chord.cmd.attach_base": ("Ligar a base", "Attach base"),
    "chord.cmd.select": ("Selecionar (pegas)", "Select (grips)"),
    "chord.cmd.select_linked": ("as paredes ligadas escolhidas", "the joined walls chosen"),
    "chord.cmd.quick_edit": ("Edição rápida", "Quick edit"),
    "tip.thin_lines": ("No ecrã, as linhas do corte com 1 píxel, seja qual for o zoom (para desenhar com rigor). "
                       "Desligado: com as canetas do papel — o corte grosso, as camadas e a trama finas, que mudam com "
                       "o zoom. O papel e o PDF não mudam.",
                       "On the screen, the cut's lines 1 pixel wide, whatever the zoom (to draw precisely). Off: with "
                       "the paper's pens — the cut thick, the layers and hatches thin, changing with the zoom. Paper "
                       "and PDF do not change."),
    "tip.drag_elements": ("Ligado: carregar num elemento e arrastar move-o (Ctrl ao largar: uma cópia; Esc: fica "
                          "onde estava); a partir do vazio continua a ser a caixa. Desligado: arrastar faz sempre a "
                          "caixa.",
                          "On: pressing on an element and dragging moves it (Ctrl as you let go: a copy; Esc: it stays "
                          "where it was); from empty space it is still the box. Off: dragging always draws the box."),
    "hint.select_drag": ("A arrastar: largue onde o quer (os snaps ajudam; Shift prende a direção; Ctrl ao largar "
                         "copia; escreva a distância e Enter). Esc: fica onde estava.",
                         "Dragging: let go where you want it (the snaps help; Shift holds the direction; Ctrl as you "
                         "let go copies; type the distance and Enter). Esc: it stays where it was."),
    "tip.pick_polygon": ("Selecionar com um polígono clicado ponto a ponto", "Select with a polygon clicked point by "
                         "point"),
    "tip.pick_fence": ("Selecionar o que uma linha corta", "Select what a line crosses"),
    # selection filters (0.76)
    "act.filter_selection": ("Filtrar…", "Filter…"),
    "act.select_by": ("Selecionar por…", "Select by…"),
    "act.selectable": ("Selecionáveis…", "Selectable…"),
    "act.selectable_some": ("Selecionáveis ({n} de fora)…", "Selectable ({n} left out)…"),
    "act.same_type_view": ("Todas do mesmo tipo, na vista", "All of the same type, in the view"),
    "act.same_type_project": ("Todas do mesmo tipo, no projeto", "All of the same type, in the project"),
    "act.same_category_view": ("Toda a mesma categoria, na vista", "All of the same category, in the view"),
    "tip.filter_selection": ("O que está selecionado, por categoria: desmarque o que não quer",
                             "What is selected, by category: untick what you do not want"),
    "tip.select_by": ("Selecionar por categoria, tipo, material, pavimento, fase ou propriedade",
                      "Select by category, type, material, storey, phase or property"),
    "tip.selectable": ("As categorias que se podem selecionar (as outras ficam de fora dos cliques e caixas)",
                       "The categories that can be selected (the others are left out of clicks and boxes)"),
    "sel.cat.sketch": ("Esboços", "Sketches"),
    "sel.cat.grid": ("Eixos", "Grid axes"),
    "sel.tick_all": ("Marcar todas", "Tick all"),
    "sel.tick_none": ("Desmarcar todas", "Untick all"),
    "sel.filter_title": ("Filtrar seleção", "Filter selection"),
    "sel.filter_note": ("Ficam selecionadas só as categorias marcadas.", "Only the categories ticked stay selected."),
    "sel.selectable_title": ("Categorias selecionáveis", "Selectable categories"),
    "sel.selectable_note": ("As categorias desmarcadas deixam de se poder selecionar (clique, caixa, laço, Selecionar "
                            "tudo) até as voltar a marcar.",
                            "The categories unticked can no longer be selected (click, box, lasso, Select all) until "
                            "ticked again."),
    "sel.by_title": ("Selecionar por…", "Select by…"),
    "sel.by_criterion": ("Critério", "Criterion"),
    "sel.by.class": ("Categoria", "Category"),
    "sel.scope": ("Onde", "Where"),
    "sel.scope_view": ("Na vista", "In the view"),
    "sel.scope_project": ("Em todo o projeto", "In the whole project"),
    "sel.add_to_selection": ("Juntar à seleção atual", "Add to the current selection"),
    "hint.rect.start": ("Clique no primeiro canto (no chão ou numa face).",
                        "Click the first corner (on the ground or on a face)."),
    "hint.rect.end": ("Clique no canto oposto, ou digite as medidas (ex.: 3,20;4,50) e Enter. Esc cancela.",
                      "Click the opposite corner, or type the size (e.g. 3.20;4.50) and Enter. Esc cancels."),
    "tool.terrain": ("Terreno por pontos", "Terrain from points"),
    "act.terrain_points": ("Importar pontos de levantamento…", "Import survey points…"),
    "file.points": ("Pontos de levantamento", "Survey points"),
    "elem.terrain": ("Terreno", "Terrain"),
    "cmd.terrain": ("Terreno", "Terrain"),
    "cmd.terrain_points": ("Pontos do terreno", "Terrain points"),
    "cmd.terrain_params": ("Curvas e base do terreno", "Terrain contours and base"),
    "vcb.height_point": ("Cota", "Height"),
    "hint.terrain.first": ("Escreva a cota do ponto (ex.: 12,50) e clique onde ele fica. Enter faz o terreno.",
                           "Type the point's height (e.g. 12.50) and click where it is. Enter makes the terrain."),
    "hint.terrain.more": ("{n} pontos. Clique no seguinte (cota {z}; escreva outra para mudar a do último e das "
                          "seguintes). Enter faz o terreno, Esc desiste.",
                          "{n} points. Click the next one (height {z}; type another to change the last one's and "
                          "the next ones'). Enter makes the terrain, Esc gives up."),
    "hint.terrain.add": ("A acrescentar pontos ao terreno «{name}»: escreva a cota e clique; Enter refaz-o.",
                         "Adding points to the terrain \"{name}\": type the height and click; Enter makes it again."),
    "err.terrain_few": ("São precisos pelo menos 3 pontos que não estejam em linha.",
                        "At least 3 points not in a line are needed."),
    "info.terrain_made": ("Terreno com {n} pontos, de {lo} a {hi}. As curvas de nível estão de {i} em {i}.",
                          "Terrain with {n} points, from {lo} to {hi}. Contour lines every {i}."),
    "info.terrain_far": ("Os pontos estão em coordenadas do levantamento (a {d} da origem): o projeto passou a "
                         "usá-las, e o IFC guarda-as tal como estão.",
                         "The points are in survey coordinates ({d} from the origin): the project now uses them, "
                         "and the IFC keeps them as they are."),
    "info.terrain_moved": ("Os pontos estavam longe (a {d}): foram trazidos para junto da origem do projeto.",
                           "The points were far away ({d}): they were brought near the project's origin."),
    "err.points_read": ("Não foram encontrados pontos (x, y, z) em «{f}».", "No points (x, y, z) were found in \"{f}\"."),
    "info.points_skipped": ("{n} linhas sem 3 números foram ignoradas.", "{n} lines without 3 numbers were skipped."),
    "cmd.walls_from_cad": ("Modelo do desenho", "Model from the drawing"),
    "act.walls_from_cad": ("Modelo a partir do desenho…", "Model from the drawing…"),
    "cadwalls.title": ("Modelo a partir do desenho", "Model from the drawing"),
    "cadwalls.intro": ("Paredes: desenhadas como duas linhas paralelas (as suas faces). Cada uma fica com o tipo da "
                       "sua espessura (o do projeto, ou um novo), ligada às outras nos cantos e nos T. Portas e "
                       "janelas: os blocos que caem na espessura de uma parede, com a largura desenhada. Mobiliário: "
                       "os blocos, um componente por bloco, em cada sítio onde foi inserido. O que se encontra "
                       "aparece a azul na planta; as camadas escolhidas ficam guardadas para o próximo desenho.",
                       "Walls: drawn as two parallel lines (their faces). Each one gets the type of its thickness "
                       "(the project's, or a new one), joined to the others at the corners and T junctions. Doors "
                       "and windows: the blocks that fall in a wall's thickness, as wide as drawn. Furniture: the "
                       "blocks, a component per block, wherever it was inserted. What is found is shown in blue on "
                       "the plan; the layers chosen are kept for the next drawing."),
    "cadwalls.drawing": ("Desenho", "Drawing"),
    "cadwalls.layers": ("Camadas das paredes:", "Layers of the walls:"),
    "cadwalls.layers_walls": ("Paredes (linhas):", "Walls (lines):"),
    "cadwalls.layers_columns": ("Pilares (retângulos e círculos):", "Columns (rectangles and circles):"),  # (0.211)
    "cadwalls.columns": ("E {n} pilares.", "And {n} columns."),
    "cadwalls.sized": ("{n} vãos com as medidas escritas ao lado (a altura e o peitoril vêm delas).",
                       "{n} openings with their size written beside them (their height and sill taken from it)."),
    "info.cadmodel_columns": ("E {n} pilares.", "And {n} columns."),
    "cadwalls.layers_openings": ("Portas e janelas (blocos):", "Doors and windows (blocks):"),
    "cadwalls.layers_furniture": ("Mobiliário (blocos):", "Furniture (blocks):"),
    "cadwalls.found_more": ("{d} portas, {w} janelas, {f} móveis.", "{d} doors, {w} windows, {f} pieces of furniture."),
    "info.cadmodel": ("Do desenho: {w} paredes, {d} portas, {j} janelas, {f} móveis. Ctrl+Z desfaz.",
                      "From the drawing: {w} walls, {d} doors, {j} windows, {f} pieces of furniture. Ctrl+Z undoes."),
    "info.cadmodel_left": ("{n} portas ou janelas não caíam numa parede e ficaram de fora.",
                           "{n} doors or windows did not fall in a wall and were left out."),
    "cadwalls.thickness": ("Espessuras de", "Thicknesses from"),
    "cadwalls.to": ("a", "to"),
    "cadwalls.height": ("Altura das paredes", "Walls' height"),
    "cadwalls.found": ("{n} paredes encontradas ({t}).", "{n} walls found ({t})."),
    "cadwalls.curved": ("Destas, {n} curvas (arcos duplos).", "Of these, {n} curved (double arcs)."),       # (0.210)
    "cadwalls.none": ("Nenhuma parede encontrada: marque as camadas das paredes, ou alargue as espessuras.",
                      "No walls found: tick the walls' layers, or widen the thicknesses."),
    "err.cadwalls_no_link": ("Ligue primeiro um desenho DXF (Inserir ▸ Vincular ▸ Ligar DXF).",
                             "Link a DXF drawing first (Home ▸ Import ▸ Link DXF)."),
    "info.cadwalls": ("{n} paredes feitas a partir do desenho. Ctrl+Z desfaz.",
                      "{n} walls made from the drawing. Ctrl+Z undoes."),
    "cmd.analytical": ("Modelo analítico", "Analytical model"),
    "elem.analytical": ("Modelo analítico", "Analytical model"),
    "act.analytical": ("Modelo analítico e verificação…", "Analytical model and check…"),
    "cmd.actions": ("Ações na estrutura", "Actions on the structure"),
    "act.actions": ("Ações e materiais…", "Actions and materials…"),
    "act.moments": ("Diagramas de momentos", "Moment diagrams"),                        # (0.220)
    "cmd.results": ("Resultados da análise no IFC", "Analysis results in the IFC"),     # (0.221)
    "analysis.save": ("Guardar resultados no IFC", "Save the results in the IFC"),
    "analysis.save_tip": ("Pôr no IFC a combinação 1,35G+1,50Q e os seus resultados: as reações dos apoios e os "
                          "momentos ao longo de cada barra (IfcStructuralResultGroup), para os programas de "
                          "estruturas os lerem",
                          "Put in the IFC the combination 1.35G+1.50Q and its results: the supports' reactions and each "
                          "member's moments along it (IfcStructuralResultGroup), for structural programs to read"),
    "analysis.saved": ("Resultados guardados no IFC.", "Results saved in the IFC."),
    "analysis.not_saved": ("Os resultados não se guardaram: a estrutura não se pôde analisar.",
                           "The results were not saved: the structure could not be analysed."),
    "info.results_saved": ("Resultados no IFC: os momentos de {n} barras e as reações de {r} apoios (1,35G+1,50Q). "
                           "Ctrl+Z desfaz.",
                           "Results in the IFC: the moments of {n} members and the reactions of {r} supports "
                           "(1.35G+1.50Q). Ctrl+Z undoes."),
    "rib.short.moments": ("Diagramas de\nmomentos", "Moment\ndiagrams"),
    "tip.moments": ("Analisar a estrutura e desenhar sobre o modelo o diagrama de momentos fletores de cada barra "
                    "(1,35G + 1,50Q), do lado das fibras traccionadas",
                    "Analyse the structure and draw each member's bending moment diagram over the model (1.35G + "
                    "1.50Q), on its tension side"),
    "moments.working": ("A analisar a estrutura…", "Analysing the structure…"),
    "moments.none": ("Não há diagramas: a estrutura não tem barras, ou não se pôde analisar (veja Analisar a "
                     "estrutura…).",
                     "No diagrams: the structure has no members, or it could not be analysed (see Analyse the "
                     "structure…)."),
    "info.moments": ("Diagramas de momentos ({c}) de {n} barras; o maior {m} kNm. Pré-dimensionamento.",
                     "Moment diagrams ({c}) of {n} members; the largest {m} kNm. Pre-design."),
    "act.analyse": ("Analisar a estrutura…", "Analyse the structure…"),
    # (0.336) the load-bearing walls in the analysis
    "analysis.wall_name": ("{name} (parede)", "{name} (wall)"),
    "analysis.wall_case": ("horizontal: {case}", "horizontal: {case}"),
    "analysis.wall_note": ("Parede resistente: N em kN por metro, na base (1,35G+1,50Q; e só G), pelo comprimento sem "
                           "os vãos; V em kN, a maior força horizontal que lhe cabe (vento × 1,5, sismo × 1), repartida "
                           "pelas paredes do piso nessa direção pela rigidez de cada uma.",
                           "Load-bearing wall: N in kN per metre at its base (1.35G+1.50Q; and G alone), over its "
                           "length less its openings; V in kN, the largest horizontal force it takes (wind × 1.5, "
                           "earthquake × 1), shared among the storey's walls that way by each one's stiffness."),
    "analysis.walls_only": ("{w} paredes resistentes: as cargas das lajes descem por elas até às fundações, e as "
                            "forças horizontais de cada piso repartem-se pelas paredes de cada direção pela rigidez. "
                            "(Sem pilares nem vigas, não há pórtico a analisar.)",
                            "{w} load-bearing walls: the slabs' loads go down them to the foundations, and each "
                            "storey's horizontal forces are shared among the walls of each way by their stiffness. (No "
                            "columns or beams: no frame to analyse.)"),
    "info.analysed_walls": ("Estrutura de paredes resistentes: as cargas de {w} paredes calculadas, piso a piso.",
                            "A structure of load-bearing walls: the loads of {w} walls worked out, storey by storey."),
    "analysis.walls_too": ("E {w} paredes resistentes, com as cargas das lajes e das vigas apoiadas nelas.",
                           "And {w} load-bearing walls, with the loads of the slabs and beams resting on them."),
    "analysis.title": ("Análise da estrutura", "Structural analysis"),
    "analysis.summary": ("{n} barras analisadas como um pórtico espacial. Cargas G + Q: entram {put} kN, descem aos "
                         "apoios {up} kN. Deriva máxima com o vento: {drift} da altura do piso.",
                         "{n} members analysed as a space frame. Loads G + Q: {put} kN go in, {up} kN come down to the "
                         "supports. Largest drift under the wind: {drift} of the storey's height."),
    "analysis.err.no_members": ("não tem pilares, vigas nem paredes resistentes",
                                "it has no columns, beams or load-bearing walls"),
    "analysis.error": ("A estrutura não se pode analisar: {e}. Veja Modelo analítico e verificação.",
                       "The structure cannot be analysed: {e}. See Analytical model and check."),
    "analysis.note": ("Pórtico espacial (6 graus de liberdade por nó, cada piso um diafragma rígido), as lajes como "
                      "cascas ou as suas cargas repartidas pelas vigas pelas áreas de influência (escolha em Ações e "
                      "materiais); combinações da NP EN 1990 (vento e sismo em X e em Y). Flecha na combinação quase "
                      "permanente, elástica, sem fluência (a vermelho acima de L/250). Pré-dimensionamento: o projeto "
                      "de estruturas é do engenheiro, que o assina.",
                      "Space frame (6 degrees of freedom a node, each floor a rigid diaphragm), the slabs as shells or "
                      "their loads carried to the beams by their areas (chosen in Actions and materials); NP EN 1990 "
                      "combinations (wind and earthquake in X and Y). Deflection in the quasi-permanent combination, "
                      "elastic, without creep (in red beyond L/250). Pre-design: the structural design is the "
                      "engineer's, who signs it."),
    "analysis.slab_moments": ("x {x} / y {y}", "x {x} / y {y}"),
    "analysis.slab_note": ("Lajes calculadas como cascas (elementos finitos triangulares DKT, malha de {size} m): os "
                           "momentos por metro (kNm/m) a armar segundo Wood–Armer, x na direção principal da laje e y "
                           "na outra; M vão é a face de baixo, M apoio a de cima.",
                           "Slabs analysed as shells (DKT triangular finite elements, {size} m mesh): the moments per "
                           "metre (kNm/m) to reinforce for by Wood–Armer, x along the slab's main direction and y "
                           "across; M span is the bottom face, M support the top."),
    "analysis.again": ("Analisar outra vez", "Analyse again"),
    "analysis.col.element": ("Elemento", "Element"),
    "analysis.col.length": ("L (m)", "L (m)"),
    "analysis.col.n_min": ("N mín (kN)", "N min (kN)"),
    "analysis.col.n_max": ("N máx (kN)", "N max (kN)"),
    "analysis.col.v": ("V (kN)", "V (kN)"),
    "analysis.col.m_pos": ("M vão / pilar (kNm)", "M span / column (kNm)"),
    "analysis.col.m_neg": ("M apoio (kNm)", "M support (kNm)"),
    "analysis.col.deflection": ("Flecha", "Deflection"),
    "analysis.col.combo": ("Combinação", "Combination"),
    "analysis.second_order": ("2.ª ordem: θ máximo {theta} ({case}, piso a {level} m) — {verdict}.",
                              "Second order: largest θ {theta} ({case}, storey at {level} m) — {verdict}."),
    "analysis.sway.ignored": ("desprezável (θ até 0,10)", "negligible (θ up to 0.10)"),
    "analysis.sway.amplified": ("as ações horizontais multiplicadas por 1/(1 − θ): {amps}",
                                "the horizontal actions multiplied by 1/(1 − θ): {amps}"),
    "analysis.sway.rigorous": ("θ acima de 0,20: o método simplificado não chega, peça uma análise de 2.ª ordem ao "
                               "engenheiro (aqui, como estimativa, multiplicadas por 1/(1 − θ): {amps})",
                               "θ above 0.20: the simplified method is not enough, ask the engineer for a second order "
                               "analysis (here, as an estimate, multiplied by 1/(1 − θ): {amps})"),
    "analysis.sway.flexible": ("θ acima de 0,30 não é permitido (EC8 4.4.2.2(4)): a estrutura é flexível demais — "
                               "aumente os pilares ou junte paredes resistentes ({amps})",
                               "θ above 0.30 is not allowed (EC8 4.4.2.2(4)): the structure is too flexible — enlarge "
                               "the columns or add shear walls ({amps})"),
    "analysis.sway.amp": ("{case} × {f}", "{case} × {f}"),
    "analysis.case.WX": ("vento X", "wind X"),
    "analysis.case.WY": ("vento Y", "wind Y"),
    "analysis.case.EX": ("sismo X", "earthquake X"),
    "analysis.case.EY": ("sismo Y", "earthquake Y"),
    "analysis.sway.col.case": ("Ação", "Action"),
    "analysis.sway.col.level": ("Piso (m)", "Storey (m)"),
    "analysis.sway.col.height": ("h (m)", "h (m)"),
    "analysis.sway.col.p": ("P (kN)", "P (kN)"),
    "analysis.sway.col.v": ("V (kN)", "V (kN)"),
    "analysis.sway.col.drift": ("dr (mm)", "dr (mm)"),
    "analysis.sway.col.theta": ("θ", "θ"),
    "analysis.sway.col.verdict": ("2.ª ordem", "Second order"),
    "analysis.sway.short.ignored": ("desprezável", "negligible"),
    "analysis.sway.short.amplified": ("× 1/(1 − θ)", "× 1/(1 − θ)"),
    "analysis.sway.short.rigorous": ("análise de 2.ª ordem", "second order analysis"),
    "analysis.sway.short.flexible": ("não permitido", "not allowed"),
    "analysis.sway_note": ("θ = P·dr/(V·h) de cada piso (NP EN 1998-1 4.4.2.2): P a carga vertical do piso e dos de "
                           "cima (sismo G + ψ2 Q; vento 1,35G + 1,50Q), V o esforço transverso do piso, dr a deriva "
                           "entre pisos com a estrutura fendilhada (sismo: metade da rigidez, EC8 4.3.1(7), e × q; "
                           "vento: 0,4 Ecd Ic, EC2 H.1.2), h a altura do piso. Até 0,10 a 2.ª ordem despreza-se; acima, "
                           "cada ação horizontal é multiplicada por 1/(1 − θ) do pior piso.",
                           "θ = P·dr/(V·h) of each storey (EN 1998-1 4.4.2.2): P the vertical load of the storey and "
                           "those above (earthquake G + ψ2 Q; wind 1.35G + 1.50Q), V the storey's shear, dr the "
                           "interstorey drift with the structure cracked (earthquake: half the stiffness, EC8 4.3.1(7), "
                           "and × q; wind: 0.4 Ecd Ic, EC2 H.1.2), h the storey's height. Up to 0.10 the second order is "
                           "neglected; above, each horizontal action is multiplied by 1/(1 − θ) of the worst storey."),
    "info.analysed": ("Estrutura analisada: {n} barras; o que entra desce aos apoios ({up} kN).",
                      "Structure analysed: {n} members; what goes in comes down to the supports ({up} kN)."),
    "act.verify_ec2": ("Verificação EC2 / EC6 e armaduras…", "EC2 / EC6 check and reinforcement…"),
    # (0.337) the load-bearing masonry walls by Eurocode 6
    "ec6.spot.top": ("no topo", "at the top"),
    "ec6.spot.mid": ("a meio", "at mid-height"),
    "ec6.spot.base": ("na base", "at the base"),
    "ec2.note.ec6_material": ("alvenaria de {unit} do grupo {group} ({src}): fb = {fb} N/mm², argamassa {mortar} → fk = "
                              "{fk} N/mm², fd = fk/γM = {fd} N/mm² (γM = {gm})",
                              "masonry of {unit}, group {group} ({src}): fb = {fb} N/mm², mortar {mortar} → fk = {fk} "
                              "N/mm², fd = fk/γM = {fd} N/mm² (γM = {gm})"),
    "ec6.unit.clay": ("blocos cerâmicos", "clay units"),                        # (0.346)
    "ec6.unit.concrete": ("blocos de betão", "concrete units"),
    "ec6.unit.calcium_silicate": ("blocos sílico-calcários", "calcium silicate units"),
    "ec6.unit.aac": ("blocos de betão celular", "aerated concrete units"),
    "ec6.src.type": ("a do tipo", "its type's"),
    "ec6.src.project": ("a do projeto", "the project's"),
    "ec2.note.ec6_slender": ("esbelteza hef/tef = {slender} (máximo {limit})",
                             "slenderness hef/tef = {slender} (at most {limit})"),
    "ec2.note.ec6_compression": ("compressão {spot}: NEd = {n} kN/m {sign} NRd = Φ t fd = {nrd} kN/m (Φ = {phi}, e = "
                                 "{ecc} mm)",
                                 "compression {spot}: NEd = {n} kN/m {sign} NRd = Φ t fd = {nrd} kN/m (Φ = {phi}, e = "
                                 "{ecc} mm)"),
    "ec2.note.ec6_shear": ("corte no plano: VEd = {v} kN {sign} VRd = fvd t lc = {vrd} kN (fvk = {fvk} N/mm² com σd = "
                           "{sig} N/mm², lc = {len} m)",
                           "in-plane shear: VEd = {v} kN {sign} VRd = fvd t lc = {vrd} kN (fvk = {fvk} N/mm² with σd = "
                           "{sig} N/mm², lc = {len} m)"),
    "ec2.note.ec6_no_shear": ("sem força horizontal no seu plano (corre na outra direção)",
                              "no horizontal force in its plane (it runs the other way)"),
    # (0.345) a façade wall's bending out of its plane, by the wind
    "ec2.note.ec6_flexural": ("alvenaria à flexão ({unit}, argamassa {mortar}: {src}): fxk1 = {f1}, fxk2 = {f2} N/mm² "
                              "(quadro 3.4; γM = {gm}); com σd = {sig} N/mm² → fxd1 = {fd1}, fxd2 = {fd2} N/mm², μ = "
                              "{ortho}",
                              "masonry in bending ({unit}, mortar {mortar}: {src}): fxk1 = {f1}, fxk2 = {f2} N/mm² "
                              "(table 3.4; γM = {gm}); with σd = {sig} N/mm² → fxd1 = {fd1}, fxd2 = {fd2} N/mm², μ = "
                              "{ortho}"),
    "ec2.note.ec6_wind": ("vento na fachada: WEd = 1,5 × qp × c × {open} = 1,5 × {qp} × {c} × {open} = {w} kN/m² (qp "
                          "a {z} m do chão; × {open}: o vento das janelas e portas vem para o pano)",
                          "wind on the façade: WEd = 1.5 × qp × c × {open} = 1.5 × {qp} × {c} × {open} = {w} kN/m² (qp "
                          "{z} m over the ground; × {open}: the windows' and doors' wind comes to the panel)"),
    "ec2.note.ec6_wind_solid": ("vento na fachada: WEd = 1,5 × qp × c = 1,5 × {qp} × {c} = {w} kN/m² (qp a {z} m do "
                                "chão)",
                                "wind on the façade: WEd = 1.5 × qp × c = 1.5 × {qp} × {c} = {w} kN/m² (qp {z} m over "
                                "the ground)"),
    "ec2.note.ec6_lateral": ("flexão para fora do plano, pano {len} × {h} m apoiado {edges}: MEd1 = {me1} {sign} MRd1 "
                             "= fxd1·Z = {mr1} kNm/m; MEd2 = {me2} {sign} MRd2 = fxd2·Z = {mr2} kNm/m (α2 = {alpha}, "
                             "linhas de rotura)",
                             "bending out of its plane, panel {len} × {h} m held {edges}: MEd1 = {me1} {sign} MRd1 = "
                             "fxd1·Z = {mr1} kNm/m; MEd2 = {me2} {sign} MRd2 = fxd2·Z = {mr2} kNm/m (α2 = {alpha}, "
                             "yield lines)"),
    "ec2.note.ec6_lateral_over": ("flexão para fora do plano, pano {len} × {h} m apoiado {edges}: MEd2 = {me2} {sign} "
                                  "MRd2 = {mr2} kNm/m (MEd1 = {me1}, MRd1 = {mr1}) — a flexão não chega sozinha",
                                  "bending out of its plane, panel {len} × {h} m held {edges}: MEd2 = {me2} {sign} "
                                  "MRd2 = {mr2} kNm/m (MEd1 = {me1}, MRd1 = {mr1}) — bending alone is not enough"),
    "ec2.note.ec6_arch": ("efeito de arco vertical (6.3.2: a parede justa, sem folga, à laje ou viga de cima): WEd = "
                          "{w} {sign} qlat = fd (t/h)² = {q} kN/m² (h/t = {ht} ≤ {limit})",
                          "vertical arching (6.3.2: the wall built tight, no gap, under the slab or beam above): WEd = "
                          "{w} {sign} qlat = fd (t/h)² = {q} kN/m² (h/t = {ht} ≤ {limit})"),
    "ec6.edges.all": ("nos quatro bordos", "on its four edges"),
    "ec6.edges.top_side": ("em baixo, em cima e num lado", "at its base, its top and one side"),
    "ec6.edges.top": ("em baixo e em cima", "at its base and its top"),
    "ec6.edges.sides": ("em baixo e nos dois lados (topo livre)", "at its base and both sides (its top free)"),
    "ec6.edges.side": ("em baixo e num lado", "at its base and one side"),
    "ec6.edges.base": ("só em baixo (em consola)", "only at its base (standing free)"),
    # (0.342) the load-bearing concrete walls by Eurocode 2, on each metre
    "ec2.note.wall_slender": ("esbelteza λ = l0·√12/t = {lam} (limite {limit}); 2.ª ordem M2 = {m2} kNm/m",
                              "slenderness λ = l0·√12/t = {lam} (limit {limit}); second order M2 = {m2} kNm/m"),
    "ec2.note.wall_compression": ("compressão {spot}: NEd = {n} kN/m, MEd = {m} kNm/m — {ratio} do diagrama N–M",
                                  "compression {spot}: NEd = {n} kN/m, MEd = {m} kNm/m — {ratio} of the N–M diagram"),
    "ec2.note.wall_vertical": ("armadura vertical Ø{d}//{s} em cada face: {area} cm²/m (mínimo 0,002 Ac = {as_min} "
                               "cm²/m)",
                               "vertical bars Ø{d}//{s} on each face: {area} cm²/m (least 0.002 Ac = {as_min} cm²/m)"),
    "ec2.note.wall_horizontal": ("armadura horizontal Ø{d}//{s} em cada face: {area} cm²/m (≥ 25 % da vertical e "
                                 "0,001 Ac)",
                                 "horizontal bars Ø{d}//{s} on each face: {area} cm²/m (≥ 25 % of the vertical and "
                                 "0.001 Ac)"),
    "ec2.note.wall_shear": ("corte no plano: VEd = {v} kN ≤ VRd,c = {vrd} kN (σcp = {sig} MPa, comprimento {len} m)",
                            "in-plane shear: VEd = {v} kN ≤ VRd,c = {vrd} kN (σcp = {sig} MPa, length {len} m)"),
    "ec2.note.wall_shear_bars": ("corte no plano: VEd = {v} kN > VRd,c = {vrd} kN — a armadura horizontal leva-o: "
                                 "{need} cm²/m (VRd,max = {vmax} kN; comprimento {len} m)",
                                 "in-plane shear: VEd = {v} kN > VRd,c = {vrd} kN — the horizontal bars take it: "
                                 "{need} cm²/m (VRd,max = {vmax} kN; length {len} m)"),
    "ec2.note.wall_shear_fail": ("corte no plano: VEd = {v} kN > VRd,max = {vmax} kN — a parede é curta ou fina de "
                                 "mais", "in-plane shear: VEd = {v} kN > VRd,max = {vmax} kN — the wall is too short "
                                         "or too thin"),
    "ec2.note.wall_no_shear": ("sem força horizontal no seu plano (corre na outra direção)",
                               "no horizontal force in its plane (it runs the other way)"),
    "ec2.note.wall_fail": ("NEd = {n} kN/m com MEd = {m} kNm/m: nem 4 % de armadura chega — engrosse a parede",
                           "NEd = {n} kN/m with MEd = {m} kNm/m: not even 4 % of steel will do — make the wall thicker"),
    "ec6.summary": ("{n} paredes de alvenaria verificadas pelo EC6 (fk = {fk} N/mm²).",
                    "{n} masonry walls checked by EC6 (fk = {fk} N/mm²)."),
    "ec6.fk_range": ("{a} a {b}", "{a} to {b}"),                                  # (0.346: by their types)
    "actions.masonry_unit": ("Alvenaria: blocos", "Masonry: units"),
    "actions.masonry_unit.clay": ("Cerâmicos (tijolo)", "Clay"),
    "actions.masonry_unit.concrete": ("De betão", "Aggregate concrete"),
    "actions.masonry_unit.calcium_silicate": ("Sílico-calcários", "Calcium silicate"),
    "actions.masonry_unit.aac": ("Betão celular", "Autoclaved aerated concrete"),
    "actions.masonry_group": ("Grupo dos blocos (EC6)", "Units' group (EC6)"),
    "actions.masonry_fb": ("Resistência dos blocos fb", "Units' strength fb"),
    "actions.masonry_mortar": ("Argamassa", "Mortar"),
    "actions.masonry_gamma": ("γM da alvenaria", "Masonry's γM"),
    "act.rebar_schedule": ("Lista de armaduras…", "Bar schedule…"),
    "cmd.rebars": ("Armaduras", "Reinforcement"),
    "cmd.remove_rebars": ("Tirar as armaduras", "Remove the reinforcement"),
    "ec2.title": ("Verificação EC2 / EC6 e armaduras", "EC2 / EC6 check and reinforcement"),
    "ec2.summary": ("{n} elementos verificados com os esforços da análise: {ok} OK, {w} com atenção, {f} falham. Betão "
                    "{c}, aço {s}.",
                    "{n} members checked with the analysis's forces: {ok} OK, {w} need attention, {f} fail. Concrete "
                    "{c}, steel {s}."),
    "ec2.none": ("Não há elementos estruturais para verificar: faça pilares, vigas, sapatas e lajes (separador "
                 "Estrutura) ou marque paredes como resistentes.",
                 "No structural members to check: make columns, beams, footings and slabs (the Structure tab) or "
                 "mark walls as load-bearing."),
    "ec2.note": ("NP EN 1992-1-1: vigas à flexão (no vão e nos apoios), ao esforço transverso (estribos) e à "
                 "deformação (L/d); pilares no diagrama de interação N–M, com a excentricidade mínima e os efeitos de "
                 "2.ª ordem (l0 = L); sapatas pela tensão no solo (área efetiva), flexão e punçoamento; lajes nas "
                 "duas direções (Marcus); paredes de betão por metro (N–M com a 2.ª ordem, armaduras mínimas de 9.6, "
                 "corte no plano). Varões A500/A400 NR, recobrimento 3 cm (sapatas 5 cm, lajes 2,5 cm). "
                 "NP EN 1996-1-1: paredes de alvenaria à compressão no topo, a meio e na base (Φ pela excentricidade "
                 "e pela esbelteza) e ao corte no seu plano; as de fachada, resistentes ou de enchimento, à flexão "
                 "para fora do plano pelo vento (linhas de rotura do Anexo E; o efeito de arco, 6.3.2). "
                 "Pré-dimensionamento: o projeto de estruturas é do engenheiro, que o assina.",
                 "NP EN 1992-1-1: beams in bending (span and supports), shear (stirrups) and deflection (L/d); columns "
                 "on their N–M interaction diagram, with the minimum eccentricity and second-order effects (l0 = L); "
                 "footings by the soil's pressure (effective area), bending and punching; slabs both ways (Marcus); "
                 "concrete walls on each metre (N–M with second order, 9.6's least bars, in-plane shear). "
                 "A500/A400 NR bars, 3 cm cover (footings 5 cm, slabs 2.5 cm). NP EN 1996-1-1: masonry walls in "
                 "compression at the top, mid-height and base (Φ by the eccentricity and slenderness) and in-plane "
                 "shear; the façade ones, load-bearing or infill, in bending out of their plane by the wind (annex E's "
                 "yield lines; arching, 6.3.2). Pre-design: the structural design is the engineer's, who signs it."),
    "ec2.again": ("Verificar outra vez", "Check again"),
    "ec2.make": ("Pôr as armaduras no modelo", "Put the reinforcement in the model"),
    "ec2.schedule": ("Lista de armaduras…", "Bar schedule…"),
    "ec2.col.element": ("Elemento", "Element"),
    "ec2.col.status": ("Estado", "Status"),
    "ec2.col.ratio": ("Utilização", "Utilisation"),
    "ec2.col.bars": ("Armadura", "Reinforcement"),
    "ec2.col.model": ("No modelo", "In the model"),
    "ec2.col.note": ("O que manda", "What governs"),
    "ec2.status.ok": ("OK", "OK"),
    "ec2.status.atencao": ("Atenção", "Attention"),
    "ec2.status.falha": ("Falha", "Fails"),
    "ec2.model.same": ("estas", "these"),
    "ec2.model.other": ("outras", "others"),
    "ec2.model.none": ("—", "—"),
    "ec2.bars.beam": ("inf. {b} · sup. {t} · estribos {l}", "bottom {b} · top {t} · stirrups {l}"),
    "ec2.bars.column": ("{b} · cintas {l}", "{b} · ties {l}"),
    "ec2.bars.footing": ("malha {x} × {y}", "mesh {x} × {y}"),
    "ec2.bars.wall": ("vert. {v} · horiz. {h} (2 faces)", "vert. {v} · horiz. {h} (2 faces)"),       # (0.342)
    "ec2.bars.slab": ("malha inf. {x} × {y}", "bottom mesh {x} × {y}"),
    "ec2.bars.slab_top": ("malha inf. {x} × {y} · sup. {tx} × {ty}", "bottom mesh {x} × {y} · top {tx} × {ty}"),
    "ec2.face.bottom": ("face inferior", "bottom face"),
    "ec2.face.top": ("face superior", "top face"),
    "ec2.face.x": ("em X", "along X"),
    "ec2.face.y": ("em Y", "along Y"),
    "ec2.face.short": ("no vão menor", "short span"),
    "ec2.face.long": ("no vão maior", "long span"),
    "ec2.note.no_depth": ("altura útil impossível (h = {h} m): aumente a altura", "no effective depth (h = {h} m): "
                                                                                  "make it deeper"),
    "ec2.note.forces": ("esforços de cálculo: M vão {m_pos} kNm, M apoio {m_neg} kNm, V {v} kN",
                        "design forces: M span {m_pos} kNm, M support {m_neg} kNm, V {v} kN"),
    "ec2.note.bending": ("flexão {face}: M {m} kNm, μ {mu}, As {need} cm² (com o mínimo: {area} cm²) → {n} Ø{d}",
                         "bending {face}: M {m} kNm, μ {mu}, As {need} cm² (with the minimum: {area} cm²) → {n} Ø{d}"),
    "ec2.note.bending_fail": ("flexão {face}: secção insuficiente (μ {mu} > 0,372) — aumente a secção",
                              "bending {face}: section too small (μ {mu} > 0.372) — make it larger"),
    "ec2.note.bending_ductility": ("flexão {face}: pouco dúctil (μ {mu} > 0,295, x/d > 0,45) — aumente a altura",
                                   "bending {face}: little ductile (μ {mu} > 0.295, x/d > 0.45) — make it deeper"),
    "ec2.note.bending_too_much": ("flexão {face}: As {area} cm² acima do máximo ({limit} cm²) — aumente a secção",
                                  "bending {face}: As {area} cm² over the maximum ({limit} cm²) — make it larger"),
    "ec2.note.bars_do_not_fit": ("{face}: {n} Ø{d} não cabem numa camada — alargue a viga",
                                 "{face}: {n} Ø{d} do not fit in one layer — make the beam wider"),
    "ec2.note.shear": ("esforço transverso: V {v} kN (VRd,c {vrdc} kN), cot θ {cot} → estribos Ø{d}//{s}",
                       "shear: V {v} kN (VRd,c {vrdc} kN), cot θ {cot} → stirrups Ø{d}//{s}"),
    "ec2.note.shear_crushing": ("esforço transverso: V {v} kN acima de VRd,max {limit} kN (bielas) — aumente a "
                                "secção", "shear: V {v} kN over VRd,max {limit} kN (struts) — make it larger"),
    "ec2.note.shear_links": ("esforço transverso: V {v} kN pede estribos a menos de 7,5 cm — aumente a secção",
                             "shear: V {v} kN needs stirrups closer than 7.5 cm — make it larger"),
    "ec2.note.slenderness": ("deformação: L/d {ratio} (limite {limit}, EC2 7.4.2)",
                             "deflection: L/d {ratio} (limit {limit}, EC2 7.4.2)"),
    "ec2.note.deflection": ("flecha elástica (quase permanente) {f} mm; L/250 = {allowed} mm",
                            "elastic deflection (quasi-permanent) {f} mm; L/250 = {allowed} mm"),
    "ec2.note.column_forces": ("esforços de cálculo: N {n} kN, M {m} kNm (e0 mín. {e0} m)",
                               "design forces: N {n} kN, M {m} kNm (e0 min. {e0} m)"),
    "ec2.note.column_slenderness": ("esbelteza λ {lam} (limite {limit}): sem efeitos de 2.ª ordem",
                                    "slenderness λ {lam} (limit {limit}): no second-order effects"),
    "ec2.note.second_order": ("esbelto: λ {lam} > {limit} — M2 = {m2} kNm de 2.ª ordem somado",
                              "slender: λ {lam} > {limit} — second-order M2 = {m2} kNm added"),
    "ec2.note.interaction": ("N–M: N {n} kN, M {m} kNm → {n_bars} Ø{d} (utilização {ratio})",
                             "N–M: N {n} kN, M {m} kNm → {n_bars} Ø{d} (utilisation {ratio})"),
    "ec2.note.column_fail": ("N {n} kN, M {m} kNm fora do diagrama mesmo com 4 % de armadura — aumente a secção",
                             "N {n} kN, M {m} kNm outside the diagram even with 4 % of steel — make it larger"),
    "ec2.note.ties": ("cintas Ø{d}//{s} (EC2 9.5.3)", "ties Ø{d}//{s} (EC2 9.5.3)"),
    "ec2.note.bearing": ("tensão no solo {sigma} kPa (admissível {soil} kPa; N {n} kN, e {ex} × {ey} m)",
                         "soil pressure {sigma} kPa (allowable {soil} kPa; N {n} kN, e {ex} × {ey} m)"),
    "ec2.note.bearing_fail": ("tensão no solo {sigma} kPa acima da admissível {soil} kPa — aumente para ~{side} × "
                              "{side} m", "soil pressure {sigma} kPa over the allowable {soil} kPa — make it ~{side} × "
                                          "{side} m"),
    "ec2.note.overturning": ("excentricidade {ex} × {ey} m fora da sapata — aumente-a",
                             "eccentricity {ex} × {ey} m outside the footing — make it larger"),
    "ec2.note.rigid": ("sapata rígida (h {h} m ≥ {limit} m)", "rigid footing (h {h} m ≥ {limit} m)"),
    "ec2.note.combined": ("sapata combinada sob dois pilares a {span} m (N {n1} e {n2} kN, ELU)",          # (0.250)
                          "combined footing under two columns {span} m apart (N {n1} and {n2} kN, ULS)"),
    "ec2.note.combined_bearing_fail": ("tensão no solo {sigma} kPa acima da admissível {soil} kPa — alargue-a "
                                       "para ~{width} m", "soil pressure {sigma} kPa over the allowable {soil} kPa — "
                                                         "make it ~{width} m wide"),
    "ec2.note.combined_moments": ("ao longo (viga sobre o solo): M+ {m_pos} kNm junto aos pilares (armadura "
                                  "inferior), M− {m_neg} kNm entre eles (armadura superior), V {v} kN a d das faces",
                                  "along it (a beam on the soil): M+ {m_pos} kNm by the columns (bottom bars), "
                                  "M− {m_neg} kNm between them (top bars), V {v} kN at d from the faces"),
    "ec2.note.combined_top": ("armadura superior ao longo: M {m} kNm/m, As {need} cm²/m (com o mínimo: {area}) → "
                              "Ø{d}//{s}", "top bars along it: M {m} kNm/m, As {need} cm²/m (with the minimum: "
                                          "{area}) → Ø{d}//{s}"),
    "ec2.note.combined_shear": ("esforço transverso sem estribos: vEd {v} MPa (vRd,c {limit} MPa)",
                                "shear with no links: vEd {v} MPa (vRd,c {limit} MPa)"),
    "ec2.note.flexible": ("sapata flexível (h {h} m < {limit} m): mais alta é rígida",
                          "flexible footing (h {h} m < {limit} m): deeper it would be rigid"),
    "ec2.note.mesh": ("malha {face}: M {m} kNm/m, As {need} cm²/m (com o mínimo: {area}) → Ø{d}//{s}",
                      "mesh {face}: M {m} kNm/m, As {need} cm²/m (with the minimum: {area}) → Ø{d}//{s}"),
    "ec2.note.punching": ("punçoamento a 2d: vEd {v} MPa (vRd,c {limit} MPa)",
                          "punching at 2d: vEd {v} MPa (vRd,c {limit} MPa)"),
    "ec2.note.punching_face": ("punçoamento junto ao pilar: vEd {v} MPa acima de vRd,max {limit} MPa — aumente a "
                               "altura", "punching at the column: vEd {v} MPa over vRd,max {limit} MPa — make it "
                                         "deeper"),
    "ec2.note.punching_out": ("punçoamento: o perímetro a 2d sai da sapata (não condiciona)",
                              "punching: the perimeter at 2d is outside the footing (not critical)"),
    "ec2.note.slab_load": ("carga de cálculo {p} kN/m²: M {m_short} kNm/m no vão menor, {m_long} no maior",
                           "design load {p} kN/m²: M {m_short} kNm/m short span, {m_long} long span"),
    "ec2.note.typical": ("piso tipo: a mesma armadura nos {n} elementos iguais — a do mais esforçado deles",
                         "typical floor: the same reinforcement in the {n} equal members — their most stressed one's"),
    "ec2.note.curtail": ("dispensa {face}: {kept} Ø{d} de ponta a ponta, mais {extra} só onde precisos — {zones} m "
                         "desde o início (a envolvente deslocada de al = {al} m, mais lb,rqd = {lbd} m; EC2 9.2.1.3)",
                         "curtailment {face}: {kept} Ø{d} end to end, {extra} more only where needed — {zones} m from "
                         "its start (the envelope moved al = {al} m, plus lb,rqd = {lbd} m; EC2 9.2.1.3)"),
    "ec2.note.pile_cap": ("maciço de {n} estaca(s), bielas e tirantes (EC2 6.5): {r} kN por estaca (ELU), {r_serv} kN "
                          "em serviço — a capacidade da estaca é do projeto de fundações",
                          "pile cap on {n} pile(s), struts and ties (EC2 6.5): {r} kN a pile (ULS), {r_serv} kN in "
                          "service — the pile's capacity is the foundation design's"),
    "ec2.note.pile_cap_one": ("uma só estaca: a carga desce direta; malha mínima nas duas direções",
                              "one pile: the load goes straight down; the minimum mesh both ways"),
    "ec2.note.pile_cap_other": ("maciço de {n} estacas: só os de 1, 2 e 4 são calculados — a definir pelo engenheiro "
                                "(malha mínima)",
                                "pile cap on {n} piles: only those on 1, 2 and 4 are worked out — for the engineer "
                                "(the minimum mesh)"),
    "ec2.note.struts": ("bielas a {theta}° (Blévot recomenda {low}° a {high}°)",
                        "struts at {theta}° (Blévot advises {low}° to {high}°)"),
    "ec2.note.node_column": ("nó sob o pilar: {stress} MPa (k1 ν' fcd = {limit} MPa, EC2 6.5.4)",
                             "node under the column: {stress} MPa (k1 ν' fcd = {limit} MPa, EC2 6.5.4)"),
    "ec2.note.node_pile": ("nó sobre a estaca: {stress} MPa (k2 ν' fcd = {limit} MPa, EC2 6.5.4)",
                           "node over the pile: {stress} MPa (k2 ν' fcd = {limit} MPa, EC2 6.5.4)"),
    "ec2.note.cap_tie": ("tirante {face}: {t} kN, As {need} cm²/m na faixa sobre as estacas (com o mínimo: {area}) → "
                         "Ø{d}//{s}",
                         "tie {face}: {t} kN, As {need} cm²/m in the band over the piles (with the minimum: {area}) "
                         "→ Ø{d}//{s}"),
    "ec2.note.cap_mesh": ("malha mínima {face}: {area} cm²/m → Ø{d}//{s}",
                          "minimum mesh {face}: {area} cm²/m → Ø{d}//{s}"),
    "ec2.note.strip_bearing": ("sapata corrida: {q} kN/m com o seu peso, {sigma} kPa no solo (admissível {soil} kPa)",
                               "strip footing: {q} kN/m with its own weight, {sigma} kPa on the soil (allowed {soil} "
                               "kPa)"),
    "ec2.note.strip_along": ("armadura longitudinal de distribuição: {area} cm²/m (20 % da transversal, EC2 9.3.1.1) "
                             "→ Ø{d}//{s}",
                             "distribution bars along it: {area} cm²/m (20 % of those across, EC2 9.3.1.1) → "
                             "Ø{d}//{s}"),
    "ec2.note.column_shape": ("secção {shape}: diagrama N–M por fibras, com os varões onde ficam, verificado com o "
                              "momento nos dois sentidos de cada direção",
                              "{shape} section: N–M diagram by fibres, with the bars where they are, checked with the "
                              "moment both ways in each direction"),
    "ec2.shape.circle": ("circular", "round"),
    "ec2.shape.L": ("em L", "L"),
    "ec2.shape.T": ("em T", "T"),
    "ec2.note.two_layers": ("{face}: os varões não cabem numa camada — {n1} Ø{d} na primeira e {n2} por cima deles na "
                            "segunda (EC2 8.2(3)); altura útil {depth} m",
                            "{face}: the bars do not fit in one layer — {n1} Ø{d} in the first and {n2} over them in "
                            "the second (EC2 8.2(3)); effective depth {depth} m"),
    "ec2.note.skin": ("viga com {h} m de altura (1,00 m ou mais): leva armadura de pele nas faces laterais, entre a "
                      "armadura de tração e o eixo neutro, dentro dos estribos (EC2 7.3.3(3)) — a definir pelo "
                      "engenheiro",
                      "beam {h} m deep (1.00 m or more): it wants skin bars on its sides, between the tension bars and "
                      "the neutral axis, inside the stirrups (EC2 7.3.3(3)) — for the engineer to define"),
    "ec2.note.slab_shell": ("momentos da laje calculada como casca (Wood–Armer): M {m_short} kNm/m no vão menor, "
                            "{m_long} no maior",
                            "moments of the slab analysed as a shell (Wood–Armer): M {m_short} kNm/m short span, "
                            "{m_long} long span"),
    "ec2.note.slab_top": ("armadura superior sobre as vigas, de cada lado até 0,2 do vão a partir da face (EC2 "
                          "9.3.1.2); nos bordos livres e sobre os pilares de lajes sem vigas: a definir pelo engenheiro",
                          "top bars over the beams, each side to 0.2 of the span from the face (EC2 9.3.1.2); at free "
                          "edges and over the columns of slabs without beams: for the engineer to define"),
    "ec2.note.slab_top_mesh": ("armadura superior sobre os apoios {face}: M {m} kNm/m (¼ do vão: {quarter}), As {need} "
                               "cm²/m (com o mínimo: {area}) → Ø{d}//{s}",
                               "top bars over the supports {face}: M {m} kNm/m (¼ of the span's: {quarter}), As {need} "
                               "cm²/m (with the minimum: {area}) → Ø{d}//{s}"),
    "ec2.done": ("Armaduras postas no modelo: {n} elementos, {b} varões. Ctrl+Z desfaz.",
                 "Reinforcement put in the model: {n} members, {b} bars. Ctrl+Z undoes."),
    "ec2.nothing": ("Não há armaduras para pôr: os elementos que falham ficam sem elas.",
                    "No reinforcement to put: the members that fail get none."),
    "tool.cabinet": ("Móvel", "Cabinet"),
    "cmd.cabinet": ("Móvel", "Cabinet"),
    "cmd.cabinet_edit": ("Mudar o móvel", "Change the cabinet"),
    "ctx.cabinet": ("Módulo", "Module"),
    "ctx.fronts": ("Frentes", "Fronts"),
    "ctx.handle": ("Puxador", "Handle"),
    "cabinet.kind.base": ("Inferior", "Base unit"),
    "cabinet.kind.wall": ("Superior", "Wall unit"),
    "cabinet.kind.tall": ("Coluna", "Tall unit"),
    "cabinet.kind.wardrobe": ("Roupeiro", "Wardrobe"),
    "elem.cabinet.wardrobe": ("Roupeiro", "Wardrobe"),
    "cabinet.fill.shelves": ("Prateleiras", "Shelves"),
    "cabinet.fill.rail": ("Varão de cabides", "Hanging rail"),
    "cabinet.fill.drawers": ("Gavetas interiores", "Inner drawers"),
    "cabinet.fill.empty": ("Vazio", "Empty"),
    "props.cab_compartments": ("Compartimentos", "Compartments"),
    "props.cab_compartment": ("Compartimento {k}", "Compartment {k}"),
    "cut.role.division": ("Divisória", "Division"),
    "cut.role.inner_drawer": ("Frente de gaveta interior", "Inner drawer front"),
    "cut.hw.hanger": ("varões de cabides", "hanging rails"),
    "cut.hw.carousel": ("carrosséis de canto", "corner carousels"),                                # (0.240)
    "cabinet.fill.carousel": ("Carrossel (canto em L)", "Carousel (L corner)"),
    "props.cab_arm": ("Canto em L (braço)", "L corner (arm)"),
    "refuse.cabinet_corner": ("um canto em L é um móvel inferior ou superior de portas, com uma porta de pelo menos "
                              "25 cm em cada braço e um só compartimento; o carrossel só cabe num canto em L",
                              "an L corner is a base or wall unit with doors, a door of 25 cm at least on each arm "
                              "and one compartment; a carousel only goes in an L corner"),
    "ctx.corner": ("Cantos", "Corners"),
    "kitchen.corner.blind": ("Cegos", "Blind"),
    "kitchen.corner.l": ("Em L", "L-shaped"),
    "kitchen.corner.carousel": ("Em L com carrossel", "L-shaped with carousel"),
    "cabinet.fronts.doors": ("Portas", "Doors"),
    "cabinet.fronts.drawers": ("Gavetas", "Drawers"),
    "cabinet.fronts.door_drawer": ("Gaveta e porta", "Drawer and door"),
    "cabinet.fronts.open": ("Aberto (prateleiras)", "Open (shelves)"),
    "cabinet.fronts.sliding": ("Portas de correr", "Sliding doors"),                                   # (0.241)
    "props.cab_finish": ("Acabamento das frentes", "Fronts' finish"),                                    # (0.243)
    "props.cab_cwidth": ("Largura do compartimento {k}", "Compartment {k}'s width"),                     # (0.244)
    "hint.cab_division": ("Arraste a divisória ao longo do móvel (ou clique e depois clique onde fica; ou escreva "
                          "quanto anda e Enter). Cada compartimento fica com pelo menos 15 cm.",
                          "Drag the division along the cabinet (or click, then click where it goes; or type how far "
                          "and Enter). Each compartment keeps 15 cm at least."),
    "info.cab_division": ("Divisória mudada: compartimentos de {a} e {b}. Ctrl+Z desfaz.",
                          "Division moved: compartments of {a} and {b}. Ctrl+Z undoes."),
    "cabinet.finish.melamine": ("Melamina (como o corpo)", "Melamine (as the carcass)"),
    "cabinet.finish.lacquer_white": ("Lacado branco", "White lacquer"),
    "cabinet.finish.lacquer_grey": ("Lacado cinzento", "Grey lacquer"),
    "cabinet.finish.lacquer_black": ("Lacado preto", "Black lacquer"),
    "cabinet.finish.oak": ("Carvalho", "Oak"),
    "cabinet.finish.walnut": ("Nogueira", "Walnut"),
    "cut.mat.front_lacquer_white": ("Frente MDF lacado branco 18 mm", "Front white lacquered MDF 18 mm"),
    "cut.mat.front_lacquer_grey": ("Frente MDF lacado cinzento 18 mm", "Front grey lacquered MDF 18 mm"),
    "cut.mat.front_lacquer_black": ("Frente MDF lacado preto 18 mm", "Front black lacquered MDF 18 mm"),
    "cut.mat.front_oak": ("Frente folheada a carvalho 18 mm", "Front oak veneer 18 mm"),
    "cut.mat.front_walnut": ("Frente folheada a nogueira 18 mm", "Front walnut veneer 18 mm"),
    "cut.role.sliding_door": ("Porta de correr", "Sliding door"),
    "cut.hw.slide": ("conjuntos de calhas de correr", "sliding track sets"),
    "refuse.cabinet_sliding": ("as portas de correr são 2 a 4, cada uma com pelo menos 30 cm, num móvel com pelo "
                               "menos 40 cm de altura", "sliding doors are 2 to 4, each 30 cm wide at least, on a "
                                                        "cabinet 40 cm tall at least"),
    "cabinet.handle.bar": ("Barra", "Bar"),
    "cabinet.handle.knob": ("Botão", "Knob"),
    "cabinet.handle.none": ("Sem puxador (gola)", "None (handleless)"),
    "elem.cabinet.base": ("Móvel inferior", "Base unit"),
    "elem.cabinet.wall": ("Móvel superior", "Wall unit"),
    "elem.cabinet.tall": ("Coluna", "Tall unit"),
    "hint.cabinet": ("Móvel {k} de {w} cm: passe sobre a face de uma parede — encosta-se a ela, virado para o ambiente, e "
                     "encosta-se ao lado de outro móvel — e clique. Escreva a largura e Enter para a mudar.",
                     "{k} of {w} cm: move over a wall's face — it goes against it, facing the room, and against "
                     "another cabinet's side — and click. Type the width and Enter to change it."),
    "keys.cabinet": ("Clique: o móvel ali  ·  largura escrita + Enter  ·  R / Shift+R: rodar  ·  Esc: Selecionar",
                     "Click: the cabinet there  ·  width typed + Enter  ·  R / Shift+R: turn  ·  Esc: Select"),
    "info.cabinet": ("{k} posto. Ctrl+Z desfaz.", "{k} put in. Ctrl+Z undoes."),
    "info.cabinet_wall": ("{k} posto contra a parede. Ctrl+Z desfaz.", "{k} put against the wall. Ctrl+Z undoes."),
    "info.cabinet_width": ("Largura do móvel: {w} cm.", "Cabinet's width: {w} cm."),
    "props.cab_height": ("Altura do corpo", "Carcass height"),
    "props.cab_depth": ("Profundidade do corpo", "Carcass depth"),
    "props.cab_plinth": ("Rodapé (altura)", "Plinth (height)"),
    "props.cab_elevation": ("Altura ao chão", "Height over the floor"),
    "props.cab_doors": ("Portas", "Doors"),
    "props.cab_blind": ("Canto cego (largura tapada)", "Blind corner (width closed)"),             # (0.239)
    "props.cab_corner_side": ("Lado do canto", "Corner side"),
    "cabinet.side.left": ("Esquerda", "Left"),
    "cabinet.side.right": ("Direita", "Right"),
    "cut.role.blind": ("Painel cego (canto)", "Blind panel (corner)"),
    "refuse.cabinet_blind": ("um canto cego é um móvel inferior ou superior de portas, com uma porta de pelo menos "
                             "25 cm ao lado da parte tapada", "a blind corner is a base or wall unit with doors, a "
                                                              "door of 25 cm at least beside the part closed"),
    "props.cab_drawers": ("Gavetas", "Drawers"),
    "props.cab_shelves": ("Prateleiras", "Shelves"),
    "props.cab_overall": ("Medidas totais (L × P × A)", "Overall (W × D × H)"),
    "refuse.cabinet_bad": ("o móvel tem um módulo, frentes ou puxador que não existe", "the cabinet has a module, "
                                                                                       "fronts or handle that does "
                                                                                       "not exist"),
    "refuse.cabinet_size": ("as medidas do móvel saem do que se faz (largura 15–150 cm — um roupeiro até 270 cm —, "
                            "altura 20–260 cm, profundidade 20–90 cm)",
                            "the cabinet's sizes are out of what is made (width 15–150 cm — a wardrobe up to 270 cm "
                            "—, height 20–260 cm, depth 20–90 cm)"),
    "refuse.cabinet_drawers": ("um móvel de gavetas tem de 1 a 6 gavetas", "a drawer unit has 1 to 6 drawers"),
    "finish.ripado": ("Ripado", "Slats"),
    "finish.canelado": ("Canelado", "Fluted"),
    "finish.perfurado": ("Painel perfurado", "Perforated panel"),
    "finish.ondulado": ("Ondulado (costelas)", "Wavy (ribs)"),
    "props.layer": ("Camada", "Layer"),
    "props.layer_v": ("{n}.ª, sobre: {under}", "{n}, over: {under}"),
    "props.rib_width": ("Espessura da costela", "Rib thickness"),
    "props.wave_amplitude": ("Amplitude da onda", "Wave amplitude"),
    "props.wave_length": ("Comprimento de onda", "Wavelength"),
    "props.wave_shift": ("Rotação da onda (por metro)", "Wave turn (per metre)"),
    "props.wave_depth": ("Saliência mínima", "Least projection"),
    "cut.role.rib": ("Costela", "Rib"),
    "cut.mat.rib": ("MDF", "MDF"),
    "props.slat_width": ("Largura da ripa", "Slat width"),
    "props.slat_gap": ("Intervalo", "Gap"),
    "props.slat_direction": ("Sentido", "Direction"),
    "slat.vertical": ("Na vertical", "Upright"),
    "slat.horizontal": ("Na horizontal", "Level"),
    "props.slats": ("Peças", "Pieces"),
    "props.hole_diameter": ("Diâmetro dos furos", "Holes' diameter"),
    "props.hole_pitch": ("Passo dos furos", "Holes' pitch"),
    "props.hole_margin": ("Margem sem furos", "Margin without holes"),
    "props.holes": ("Furos", "Holes"),
    "props.holes_v": ("{n} ({a} % de área aberta)", "{n} ({a} % open area)"),
    "refuse.pattern_bad": ("as medidas do padrão têm de ser maiores do que zero", "the pattern's measures must be "
                                                                                  "over zero"),
    "refuse.pattern_many": ("o padrão daria peças demais para o modelo (mais de 20 000 furos ou 3000 ripas): "
                            "aumente o passo ou a largura", "the pattern would make too many pieces for the model "
                                                            "(over 20,000 holes or 3,000 slats): make the pitch or "
                                                            "the width larger"),
    "cut.role.slat": ("Ripa", "Slat"),
    "cut.role.batten": ("Ripa de fixação", "Batten"),                                             # (0.434)
    "cut.role.ripado_frame": ("Moldura do ripado", "Slatted panel frame"),
    "cut.role.flute": ("Ripa canelada", "Fluted slat"),
    "cut.role.perforated": ("Painel perfurado", "Perforated panel"),
    "cut.mat.slat": ("Madeira", "Wood"),
    "cut.mat.perforated": ("MDF acústico", "Acoustic MDF"),
    "fab.panel": ("painel", "panel"),
    "fab.holes": ("furos", "holes"),
    "fab.export": ("DXF para fabrico…", "DXF for fabrication…"),
    "fab.file": ("Fabrico", "Fabrication"),
    "fab.none": ("Não há ripados, canelados, painéis perfurados, ondulados nem perfis corridos para fabricar.",
                 "No slats, fluted, perforated or wavy finishes nor profiles to make."),
    "info.fab_exported": ("DXF para fabrico gravado em {f}: {p} painéis perfurados, {s} peças de ripa, de costela e "
                          "de perfil (mm).",
                          "DXF for fabrication saved to {f}: {p} perforated panels, {s} slat, rib and profile "
                          "pieces (mm)."),
    # curtain wall panels (0.181)
    "tool.curtain_panel": ("Painel de fachada", "Curtain wall panel"),
    "cmd.curtain_panel": ("Painel de fachada", "Curtain wall panel"),
    "ctx.cw_panel": ("Painel", "Panel"),
    "cwpanel.glass": ("Vidro", "Glass"),
    "cwpanel.solid": ("Opaco", "Opaque"),
    "cwpanel.door": ("Porta de vidro", "Glass door"),
    "cwpanel.empty": ("Vazio", "Empty"),
    "hint.curtain_panel": ("Painel {k}: clique numa célula de uma fachada de vidro (as portas só na fila de baixo).",
                           "{k} panel: click a cell of a curtain wall (doors only in the bottom row)."),
    "keys.curtain_panel": ("Clique: o painel nessa célula  ·  Esc: Selecionar", "Click: the panel in that cell  ·  "
                                                                                 "Esc: Select"),
    "err.cw_panel_none": ("Clique numa célula de uma fachada de vidro.", "Click a cell of a curtain wall."),
    "info.curtain_panel": ("{k} na célula {c}.ª da {r}.ª fila de «{cw}». Ctrl+Z desfaz.",
                           "{k} in cell {c} of row {r} of “{cw}”. Ctrl+Z undoes."),
    "refuse.cw_door_row": ("uma porta só vai na fila de baixo", "a door only goes in the bottom row"),
    "refuse.cw_door_low": ("a célula é baixa demais para uma porta (afaste as travessas: pelo menos 1,90 m)",
                           "the cell is too low for a door (set the transoms further apart: at least 1.90 m)"),
    "props.cw_panels": ("Painéis", "Panels"),
    # Gaussian splats (0.176)
    "act.export_splat": ("Exportar Gaussian splat (apresentação)…", "Export Gaussian splat (presentation)…"),
    "splat.quality": ("Distância entre os pontos:", "Spacing of the points:"),
    "splat.ask_clouds": ("Juntar ao splat as {n} nuvens de pontos ligadas (tal como estão, cada ponto com a sua cor)?",
                         "Add the {n} linked point clouds to the splat (as they are, each point with its colour)?"),
    "splat.q_low": ("Baixa — 8 cm (ficheiro leve)", "Low — 8 cm (a light file)"),
    "splat.q_medium": ("Média — 5 cm", "Medium — 5 cm"),
    "splat.q_high": ("Alta — 3 cm (ficheiro pesado)", "High — 3 cm (a heavy file)"),
    "splat.working": ("A espalhar os pontos pelo modelo…", "Spreading the points over the model…"),
    "info.splat": ("Gaussian splat gravado em {f}: {n} pontos ({q}). Abra-o num visualizador de splats no "
                   "navegador (por exemplo, o SuperSplat).",
                   "Gaussian splat saved to {f}: {n} points ({q}). Open it in a splat viewer in the browser (the "
                   "SuperSplat, for one)."),
    "refuse.splat_many": ("o modelo daria pontos demais (mais de 4 milhões): escolha uma distância maior",
                          "the model would give too many points (over 4 million): choose a larger spacing"),
    # an image of the view (0.329)
    "act.export_image": ("Exportar imagem da vista…", "Export image of the view…"),
    "tip.export_image": ("A vista tal como está, numa imagem PNG ou JPEG do tamanho que escolher (Full HD, 4K, uma "
                         "folha A3…), sem a seleção nem as marcas das ferramentas.",
                         "The view as it is, as a PNG or JPEG image of the size you choose (Full HD, 4K, an A3 "
                         "sheet…), without the selection or the tools' marks."),
    "imgdlg.title": ("Exportar imagem da vista", "Export image of the view"),
    # (0.343) the realistic render (Mitsuba 3, path tracing)
    "act.render": ("Render realista…", "Realistic render…"),
    "tip.render": ("A vista como se vê, numa imagem fotográfica: a luz do céu e do sol a ressaltar nas superfícies, "
                   "sombras suaves, vidro. Corre à parte — pode continuar a trabalhar — e a imagem vai afinando.",
                   "The view as it is seen, as a photographic picture: the sky's and the sun's light bouncing off the "
                   "surfaces, soft shadows, glass. It runs apart — you may go on working — and the picture gets finer."),
    "render.title": ("Render realista", "Realistic render"),
    "render.note": ("A vista tal como se vê (o que está à vista, a câmara), com as cores e os acabamentos dos "
                    "materiais e as luminárias do modelo. O render corre à parte: pode continuar a trabalhar enquanto "
                    "a imagem afina.",
                    "The view as it is seen (what is shown, the camera), in the materials' colours and finishes, with "
                    "the model's lights. The render runs apart: you may go on working while the picture gets "
                    "finer."),
    "render.lighting": ("Iluminação", "Lighting"),
    "render.lighting.sun": ("Sol e céu", "Sun and sky"),
    "render.lighting.sun_lights": ("Sol, céu e luminárias acesas", "Sun, sky and the lights on"),
    "render.lighting.night": ("Noite: só as luminárias", "Night: the lights only"),
    "render.sun": ("Sol", "Sun"),
    "render.sun.style": ("O do estilo da vista ({az}°, {alt}° de altura)", "The view style's ({az}°, {alt}° high)"),
    "render.sun.site": ("O do terreno, num dia e hora", "The site's, on a day at an hour"),
    "render.sun.no_site": ("Para o sol de um dia e hora, dê a latitude e a longitude ao terreno: Gerenciar ▸ Projeto ▸ "
                           "Localização do terreno…",
                           "For the sun of a day and an hour, give the site a latitude and longitude: Manage ▸ "
                           "Project ▸ Site location…"),
    "render.when": ("Dia e hora", "Day and hour"),
    "render.sun_at": ("Sol a {az}° do norte, {alt}° acima do horizonte", "Sun {az}° from north, {alt}° above the "
                                                                        "horizon"),
    "render.sun_down": ("O sol está abaixo do horizonte: será de noite, só com as luminárias.",
                        "The sun is under the horizon: it will be night, with the lights only."),
    "render.exposure": ("Exposição", "Exposure"),
    "render.exposure_tip": ("Mais clara (+) ou mais escura (−) que a automática, em pontos de luz (EV): +1 é o dobro "
                            "da luz.", "Lighter (+) or darker (−) than the automatic one, in stops (EV): +1 is twice "
                                       "the light."),
    "render.clean": ("Limpar o grão (filtro)", "Clean the grain (filter)"),
    "render.clean_tip": ("Alisa o grão do render sem esbater as arestas, as cores nem as sombras: uma imagem limpa com "
                         "menos amostras, sobretudo nos interiores.",
                         "Smooths the render's grain without blurring the edges, the colours or the shadows: a clean "
                         "picture with fewer samples, above all indoors."),
    "render.size": ("Tamanho", "Size"),
    "render.size.hd": ("HD — {w} px", "HD — {w} px"),
    "render.size.full_hd": ("Full HD — {w} px", "Full HD — {w} px"),
    "render.size.qhd": ("2K — {w} px", "2K — {w} px"),
    "render.size.uhd": ("4K — {w} px", "4K — {w} px"),
    "render.pixels": ("{w} × {h} px ({mp} MP)", "{w} × {h} px ({mp} MP)"),
    "render.quality": ("Qualidade", "Quality"),
    "render.quality.draft": ("Rascunho (rápido)", "Draft (quick)"),
    "render.quality.normal": ("Normal", "Normal"),
    "render.quality.high": ("Alta (lenta, mais fina)", "High (slow, finer)"),
    "render.start": ("Renderizar", "Render"),
    "render.window": ("Render realista", "Realistic render"),
    "render.starting": ("A preparar o render…", "Getting the render ready…"),
    "render.progress": ("passagem {n} de {of} · {spp} amostras · {s}", "pass {n} of {of} · {spp} samples · {s}"),
    "render.done": ("Pronto: {spp} amostras por píxel em {s}.", "Done: {spp} samples per pixel in {s}."),
    "render.stopped": ("Parado na passagem {n} de {of}: a imagem fica como estava.",
                       "Stopped at pass {n} of {of}: the picture stays as it was."),
    "render.failed": ("O render não terminou: {e}", "The render did not finish: {e}"),
    "render.stop": ("Parar", "Stop"),
    "render.save": ("Guardar imagem…", "Save picture…"),
    "info.render_started": ("Render realista a correr ({w} × {h} px, {n} triângulos): a imagem vai afinando na sua "
                            "janela.", "Realistic render running ({w} × {h} px, {n} triangles): the picture gets "
                                       "finer in its window."),
    "info.render_missing": ("O motor do render realista (Mitsuba 3) não está instalado: corra outra vez a preparação "
                            "do Linux (scripts/wsl_setup.sh).",
                            "The realistic render's engine (Mitsuba 3) is not installed: run the Linux set-up again "
                            "(scripts/wsl_setup.sh)."),
    "info.render_empty": ("Não há nada à vista para renderizar.", "Nothing in view to render."),
    "imgdlg.note": ("A imagem é a vista como está no ecrã, mais nítida: as linhas e os textos ficam com a mesma "
                    "grossura e o mesmo tamanho em relação ao desenho. A altura segue a proporção da vista — para "
                    "outra proporção, mude antes o tamanho da janela.",
                    "The image is the view as it is on screen, sharper: lines and texts keep the same weight and the "
                    "same size compared with the drawing. Its height follows the view's proportion — for another, "
                    "resize the window first."),
    "imgdlg.size": ("Tamanho:", "Size:"),
    "imgdlg.size.full_hd": ("Full HD — {w} px de largura", "Full HD — {w} px wide"),
    "imgdlg.size.qhd": ("2K — {w} px", "2K — {w} px"),
    "imgdlg.size.uhd": ("4K — {w} px", "4K — {w} px"),
    "imgdlg.size.a4": ("Folha A4 deitada, a 300 ppp — {w} px", "A4 sheet across, at 300 dpi — {w} px"),
    "imgdlg.size.a3": ("Folha A3 deitada, a 300 ppp — {w} px", "A3 sheet across, at 300 dpi — {w} px"),
    "imgdlg.size.window": ("Como a janela — {w} px", "As the window — {w} px"),
    "imgdlg.size.other": ("Outra largura", "Another width"),
    "imgdlg.width": ("Largura:", "Width:"),
    "imgdlg.pixels": ("{w} × {h} px ({mp} milhões de píxeis)", "{w} × {h} px ({mp} megapixels)"),
    "imgdlg.background": ("Fundo:", "Background:"),
    "imgdlg.bg.view": ("Como a vista (céu claro)", "As the view (a light sky)"),
    "imgdlg.bg.white": ("Branco", "White"),
    "imgdlg.bg.transparent": ("Transparente (só em PNG)", "Transparent (PNG only)"),
    "imgdlg.export": ("Exportar…", "Export…"),
    "image.filter": ("Imagem PNG (*.png);;Imagem JPEG (*.jpg *.jpeg)", "PNG image (*.png);;JPEG image (*.jpg *.jpeg)"),
    "info.image": ("Imagem gravada em {f} ({w} × {h} px).", "Image saved to {f} ({w} × {h} px)."),
    "info.image_sheet": ("Uma folha exporta-se em PDF. A imagem é de uma vista do modelo: mude para a vista 3D, uma "
                         "planta, um corte ou um alçado.",
                         "A sheet is exported as PDF. The image is of a view of the model: go to the 3D view, a plan, "
                         "a section or an elevation."),
    "err.image": ("Não foi possível desenhar a imagem ({e}). Experimente uma largura menor.",
                  "The image could not be drawn ({e}). Try a smaller width."),
    # hatches by element in a view (0.331)
    "act.element_hatches": ("Tramas por elemento…", "Hatches by element…"),
    "tip.element_hatches": ("Dá aos elementos selecionados tramas próprias nesta vista — no corte e na superfície —, "
                            "por cima das da categoria e dos materiais (como «Substituir gráficos na vista ▸ Por "
                            "elemento» do Revit).",
                            "Gives the selected elements their own hatches in this view — cut and surface —, over "
                            "their category's and materials' (as Revit's «Override graphics in view ▸ By element»)."),
    "pick.element_hatches": ("Clique nos elementos que vão ter tramas próprias nesta vista.",
                             "Click the elements that get their own hatches in this view."),
    "ehatch.title": ("Tramas por elemento", "Hatches by element"),
    "ehatch.head": ("{what} — só na vista «{view}».", "{what} — in the view “{view}” only."),
    "ehatch.note": ("Estas tramas valem só nesta vista e passam por cima das da categoria (no estilo de vista) e das "
                    "dos materiais. Um padrão deixado em «Nenhum» fica como estava.",
                    "These hatches are for this view only and go over the category's (in the view style) and the "
                    "materials'. A pattern left at «None» stays as it was."),
    "ehatch.reset": ("Repor", "Reset"),
    "ehatch.reset_tip": ("Os elementos voltam às tramas da categoria e dos materiais nesta vista.",
                         "The elements go back to their category's and materials' hatches in this view."),
    "info.element_hatches": ("Tramas próprias para {n} elemento(s) na vista «{view}» (só nesta). Ctrl+Z desfaz.",
                             "Own hatches for {n} element(s) in the view “{view}” (this one only). Ctrl+Z undoes."),
    "info.element_hatches_back": ("{n} elemento(s) voltaram às tramas da categoria e dos materiais na vista «{view}».",
                                  "{n} element(s) back to their category's and materials' hatches in the view "
                                  "“{view}”."),
    "info.element_hatches_sheet": ("As tramas por elemento dão-se numa vista do modelo (planta, corte, alçado ou 3D), e "
                                   "a folha mostra-as.",
                                   "Hatches by element are given in a view of the model (plan, section, elevation or "
                                   "3D), and the sheet shows them."),
    "err.image_write": ("Não foi possível gravar {f}: a pasta não deixa escrever, ou o ficheiro está aberto noutro "
                        "programa?",
                        "{f} could not be written: is the folder read-only, or the file open in another program?"),
    # the Profile Pen (0.174)
    "tool.profile": ("Perfil corrido", "Profile Pen"),
    "cmd.profile": ("Perfil corrido", "Profile"),
    "cmd.profile_edit": ("Mudar perfil", "Change profile"),
    "ctx.profile_shape": ("Por", "Along"),
    "profshape.room": ("À volta de um ambiente", "Round a room"),
    "profshape.path": ("Caminho (clicado)", "A path (clicked)"),
    "ctx.profile": ("Perfil", "Profile"),
    "profile.rodape": ("Rodapé", "Skirting board"),
    "profile.sanca": ("Sanca", "Cornice"),
    "profile.friso": ("Friso", "Dado rail"),
    "profile.cimalha": ("Cimalha", "Outside cornice"),
    "ctx.profile_side": ("Lado", "Side"),
    "profside.left": ("À esquerda do caminho", "Left of the path"),
    "profside.right": ("À direita do caminho", "Right of the path"),
    "ctx.profile_foot": ("Altura ao chão", "Height over the floor"),
    "props.profile_width": ("Saliência", "Projection"),
    "props.profile_height": ("Altura do perfil", "Profile height"),
    "hint.profile.room": ("{p}: clique dentro de um ambiente — corre ao longo das paredes e à volta dos pilares, e "
                          "para nas portas. (Tab muda.)",
                          "{p}: click inside a room — it runs along the walls and round the columns, and stops at "
                          "the doors. (Tab changes it.)"),
    "hint.profile.path": ("{p}: clique nos pontos do caminho; Enter termina, um clique no primeiro ponto fecha-o, "
                          "Delete apaga o último. (Tab muda.)",
                          "{p}: click the path's points; Enter ends it, a click on its first point closes it, "
                          "Delete takes the last back. (Tab changes it.)"),
    "keys.profile": ("Tab: ambiente → caminho  ·  Enter: terminar o caminho  ·  Delete: último ponto  ·  Esc: cancelar",
                     "Tab: room → path  ·  Enter: end the path  ·  Delete: last point  ·  Esc: cancel"),
    "info.profile": ("{p} de {l}, a {h} do chão. Ctrl+Z desfaz.", "{p}, {l} long, {h} over the floor. Ctrl+Z "
                                                                  "undoes."),
    "err.profile_room": ("Não há um ambiente fechado aí: clique dentro de um ambiente rodeado de paredes.",
                         "No enclosed room there: click inside a room with walls all round."),
    "refuse.profile_short": ("o caminho é curto demais (ou fica todo nos vãos)", "the path is too short (or all in "
                                                                                "the openings)"),
    "refuse.profile_size": ("as medidas do perfil têm de ficar entre 0,5 e 60 cm", "the profile's sizes must be "
                                                                                  "between 0.5 and 60 cm"),
    "refuse.profile_foot": ("a altura ao chão não pode ser negativa", "the height over the floor cannot be "
                                                                      "negative"),
    "act.profile_from_face": ("Perfil de uma face", "Profile from a face"),                             # (0.245)
    "cmd.profile_from_face": ("Perfil de uma face", "Profile from a face"),
    "ask.profile_name": ("Nome do perfil (aparece na ferramenta Perfil):",
                         "The profile's name (shown in the Profile tool):"),
    "profile.own_default": ("Perfil próprio {n}", "Own profile {n}"),
    "info.profile_from_face": ("Perfil «{n}» guardado no projeto: escolha-o na ferramenta Perfil. Ctrl+Z desfaz.",
                               "Profile «{n}» kept in the project: choose it in the Profile tool. Ctrl+Z undoes."),
    "refuse.profile_face": ("a seleção não é uma face plana (é um volume ou um elemento)", "what is selected is not a "
                                                                                           "flat face (it is a volume "
                                                                                           "or an element)"),
    "refuse.profile_name": ("o perfil precisa de um nome que ainda não exista no projeto", "the profile needs a name "
                                                                                           "the project has not got "
                                                                                           "yet"),
    "refuse.profile_section": ("o contorno não fecha uma área", "the outline does not close an area"),
    "cut.role.rodape": ("Rodapé", "Skirting board"),
    "cut.role.sanca": ("Sanca", "Cornice"),
    "cut.role.friso": ("Friso", "Dado rail"),
    "cut.role.cimalha": ("Cimalha", "Outside cornice"),
    "cut.mat.madeira": ("Madeira", "Wood"),
    "cut.mat.gesso": ("Gesso", "Plaster"),
    "cut.mat.pedra": ("Pedra", "Stone"),
    "tool.appliance": ("Eletrodoméstico", "Appliance"),
    "cmd.appliance": ("Eletrodoméstico", "Appliance"),
    "ctx.appliance": ("Aparelho", "Appliance"),
    "appliance.hob": ("Placa", "Hob"),
    "appliance.gas_hob": ("Placa a gás", "Gas hob"),
    "appliance.oven": ("Forno", "Oven"),
    "appliance.oven_column": ("Forno em coluna", "Oven in a tall unit"),                          # (0.242)
    "cabinet.fronts.oven": ("Forno (gavetas, forno, porta)", "Oven (drawers, oven, door)"),
    "refuse.cabinet_oven": ("o forno vai numa coluna de pelo menos 60 cm de largura, com lugar para ele à altura dos "
                            "olhos", "an oven goes in a tall unit 60 cm wide at least, with room for it at eye level"),
    "appliance.dishwasher": ("Máquina de lavar loiça", "Dishwasher"),
    "appliance.washing_machine": ("Máquina de lavar roupa", "Washing machine"),
    "appliance.fridge": ("Frigorífico", "Fridge"),
    "appliance.microwave": ("Micro-ondas", "Microwave"),
    "appliance.hood": ("Exaustor", "Cooker hood"),
    "hint.appliance": ("{k}: passe sobre a face de uma parede — encosta-se a ela, à sua altura (uma placa na bancada, "
                       "que fica recortada) — e clique.",
                       "{k}: move over a wall's face — it goes against it, at its height (a hob in the worktop, which "
                       "is cut for it) — and click."),
    "keys.appliance": ("Clique: o aparelho ali  ·  R / Shift+R: rodar  ·  Esc: Selecionar",
                       "Click: the appliance there  ·  R / Shift+R: turn  ·  Esc: Select"),
    "info.appliance": ("{k} posto. Ctrl+Z desfaz.", "{k} put in. Ctrl+Z undoes."),
    "info.appliance_wall": ("{k} posto contra a parede. Ctrl+Z desfaz.", "{k} put against the wall. Ctrl+Z undoes."),
    "opt.yes": ("Sim", "Yes"),
    "opt.no": ("Não", "No"),
    "tool.kitchen": ("Cozinha", "Kitchen"),
    "cmd.kitchen": ("Cozinha", "Kitchen"),
    "cmd.worktop": ("Bancada", "Worktop"),
    "elem.worktop": ("Bancada", "Worktop"),
    "act.worktop": ("Bancada", "Worktop"),
    "ctx.wall_units": ("Superiores", "Wall units"),
    "ctx.worktop": ("Bancada", "Worktop"),
    "hint.kitchen_first": ("Cozinha: clique onde começa, na face de dentro de uma parede (o ambiente fica desse lado).",
                           "Kitchen: click where it starts, on a wall's inner face (the room is on that side)."),
    "hint.kitchen_next": ("Clique em cada canto e onde acaba; Enter (ou o botão direito) faz a cozinha. F vira-a para "
                          "o outro lado.", "Click at each corner and where it ends; Enter (or a right click) makes "
                                           "the kitchen. F turns it the other way."),
    "keys.kitchen": ("Clique: o começo, os cantos, o fim  ·  Enter: fazer  ·  F: o outro lado  ·  Esc: recomeçar",
                     "Click: the start, the corners, the end  ·  Enter: make  ·  F: the other side  ·  Esc: start "
                     "again"),
    "info.kitchen": ("Cozinha feita: {b} móveis inferiores, {w} superiores{m}. Ctrl+Z desfaz.",
                     "Kitchen made: {b} base units, {w} wall units{m}. Ctrl+Z undoes."),
    "info.kitchen_worktop": (" e a bancada", " and the worktop"),
    "info.kitchen_flipped": ("A cozinha passa para o outro lado da linha.", "The kitchen goes to the line's other "
                                                                            "side."),
    "info.worktop": ("Bancada feita sobre os móveis inferiores: segue-os quando mudam. Ctrl+Z desfaz.",
                     "Worktop made over the base units: it follows them when they change. Ctrl+Z undoes."),
    "err.worktop_none": ("Não há móveis inferiores para a bancada: selecione-os, ou faça-os primeiro.",
                         "No base units for the worktop: select them, or make them first."),
    "refuse.worktop_none": ("a bancada ficou sem móveis por baixo", "the worktop has no cabinets under it"),
    "cut.role.worktop": ("Bancada", "Worktop"),
    "cut.mat.worktop": ("Tampo de bancada 30 mm", "Worktop 30 mm"),
    "act.cut_list": ("Lista de corte…", "Cut list…"),
    "cut.title": ("Lista de corte do mobiliário", "Furniture cut list"),
    "cut.col.part": ("Peça", "Part"),
    "cut.col.material": ("Material", "Material"),
    "cut.col.length": ("Comprimento (mm)", "Length (mm)"),
    "cut.col.width": ("Largura (mm)", "Width (mm)"),
    "cut.col.thickness": ("Espessura (mm)", "Thickness (mm)"),
    "cut.col.count": ("Quant.", "No."),
    "cut.col.edges": ("Orlas", "Edges"),
    "cut.role.side": ("Lateral", "Side"),
    "cut.role.bottom": ("Base", "Bottom"),
    "cut.role.top": ("Tampo", "Top"),
    "cut.role.rail": ("Travessa", "Rail"),
    "cut.role.back": ("Costas", "Back"),
    "cut.role.shelf": ("Prateleira", "Shelf"),
    "cut.role.plinth": ("Rodapé", "Plinth"),
    "cut.role.door": ("Porta", "Door"),
    "cut.role.drawer": ("Frente de gaveta", "Drawer front"),
    "cut.mat.carcass": ("Aglomerado melamínico 18 mm", "Melamine-faced board 18 mm"),
    "cut.mat.back": ("HDF 3 mm", "HDF 3 mm"),
    "cut.mat.front": ("Frente 18 mm", "Front 18 mm"),
    "cut.hw.hinge": ("dobradiças", "hinges"),
    "cut.hw.runner": ("pares de corrediças", "pairs of runners"),
    "cut.hw.handle": ("puxadores", "handles"),
    "cut.hw.foot": ("pés", "feet"),
    "cut.summary": ("{n} móveis: {parts} peças. Placa: {areas}. Ferragens: {hw}.",
                    "{n} cabinets: {parts} parts. Board: {areas}. Hardware: {hw}."),
    "cut.none": ("Ainda não há móveis: faça-os com o botão Móvel (separador BIM).",
                 "No cabinets yet: make them with the Cabinet button (the BIM tab)."),
    "cut.note": ("Medidas de corte em milímetros, das peças como o modelo as tem (orlas: quantos lados orlados). "
                 "As costas pregadas atrás do corpo; as frentes com folgas de 3 mm. Confirme com o fabricante as "
                 "medidas das ferragens.",
                 "Cut sizes in millimetres, of the parts as the model has them (edges: how many sides banded). The "
                 "back nailed behind the carcass; the fronts with 3 mm gaps. Check the hardware's sizes with the "
                 "maker."),
    "cut.export": ("Exportar (Excel, CSV)…", "Export (Excel, CSV)…"),
    "info.cut_exported": ("Lista de corte exportada para {f}.", "Cut list exported to {f}."),
    "act.structure_quantities": ("Quantidades da estrutura…", "Structure quantities…"),
    "act.calc_report": ("Memória de cálculo…", "Calculation report…"),
    "qty.title": ("Quantidades da estrutura", "Structure quantities"),
    "qty.col.element": ("Elemento", "Element"),
    "qty.col.storey": ("Pavimento", "Storey"),
    "qty.col.concrete": ("Betão (m³)", "Concrete (m³)"),
    "qty.col.formwork": ("Cofragem (m²)", "Formwork (m²)"),
    "qty.col.steel": ("Aço (kg)", "Steel (kg)"),
    "qty.col.rate": ("Taxa (kg/m³)", "Rate (kg/m³)"),
    "qty.col.kind": ("Tipo", "Kind"),
    "qty.kind.column": ("Pilares", "Columns"),
    "qty.kind.beam": ("Vigas", "Beams"),
    "qty.kind.slab": ("Lajes", "Slabs"),
    "qty.kind.footing": ("Sapatas", "Footings"),
    "qty.kind.wall": ("Paredes de betão", "Concrete walls"),                          # (0.342)
    "qty.total": ("Total", "Total"),
    "qty.summary": ("{n} elementos: {c} m³ de betão, {f} m² de cofragem, {s} kg de aço ({r} kg/m³).",
                    "{n} members: {c} m³ of concrete, {f} m² of formwork, {s} kg of steel ({r} kg/m³)."),
    "qty.none": ("Não há elementos de betão: faça pilares, vigas, sapatas e lajes (separador Estrutura).",
                 "No concrete members: make columns, beams, footings and slabs (the Structure tab)."),
    "qty.note": ("O betão é o volume de cada elemento como está no modelo; a cofragem, os lados e o fundo das vigas, "
                 "as faces dos pilares, os lados das sapatas, o fundo e os bordos das lajes; o aço, o das armaduras "
                 "postas no modelo (Verificação EC2 / EC6 e armaduras). A vermelho, uma taxa de aço fora do habitual para o "
                 "tipo (vigas 40–220, pilares 60–300, sapatas 15–120 kg/m³).",
                 "The concrete is each member's volume as it is in the model; the formwork, a beam's sides and "
                 "soffit, a column's faces, a footing's sides, a slab's soffit and edges; the steel, that of the "
                 "reinforcement put in the model (EC2 check and reinforcement). In red, a steel rate out of the "
                 "usual for its kind (beams 40–220, columns 60–300, footings 15–120 kg/m³)."),
    "qty.export": ("Exportar (Excel, CSV)…", "Export (Excel, CSV)…"),
    "info.qty_exported": ("Quantidades da estrutura exportadas para {f}.", "Structure quantities exported to {f}."),
    "report.title": ("Memória de cálculo estrutural — pré-dimensionamento", "Structural calculation report — "
                                                                           "pre-design"),
    "report.save": ("Gravar a memória de cálculo", "Save the calculation report"),
    "info.calc_report_saved": ("Memória de cálculo gravada em {f}.", "Calculation report saved to {f}."),
    "report.date": ("Data", "Date"),
    "report.program": ("Calculado com", "Worked out with"),
    "report.s.project": ("Identificação do projeto", "The project"),
    "report.s.materials": ("Regulamentação e materiais", "Codes and materials"),
    "report.s.actions": ("Ações", "Actions"),
    "report.s.model": ("Modelo e verificação do modelo", "The model and its check"),
    "report.s.analysis": ("Análise", "Analysis"),
    "report.s.design": ("Verificação pelos Eurocódigos 2 e 6", "Eurocode 2 and 6 verification"),
    "report.s.quantities": ("Quantidades", "Quantities"),
    "report.s.rebars": ("Armaduras", "Reinforcement"),
    "report.drawings": ("Desenhos de armaduras (1:50; cortes 1:20)",                                 # (0.233)
                        "Reinforcement drawings (1:50; sections 1:20)"),
    "report.s.notes": ("Métodos, notas e limitações", "Methods, notes and limits"),
    "report.codes": ("NP EN 1990 (bases e combinações), NP EN 1991-1-1 (sobrecargas), NP EN 1991-1-4 (vento), "
                     "NP EN 1992-1-1 (betão armado), NP EN 1996-1-1 (alvenaria), NP EN 1998-1 (sismo), com os Anexos "
                     "Nacionais portugueses.",
                     "NP EN 1990 (basis and combinations), NP EN 1991-1-1 (imposed loads), NP EN 1991-1-4 (wind), "
                     "NP EN 1992-1-1 (reinforced concrete), NP EN 1996-1-1 (masonry), NP EN 1998-1 (earthquake), with "
                     "Portugal's National Annexes."),
    "report.masonry": ("Alvenaria do projeto (a das paredes cujo tipo não tem a sua): {unit}, grupo {group}, fb {fb} "
                       "N/mm², argamassa {mortar}: fk {fk} N/mm², fd {fd} N/mm² (γM {gm}, o de todas), fvk0 {fvk0} N/mm².",
                       "The project's masonry (the walls' whose type has none of its own): {unit}, group {group}, fb "
                       "{fb} N/mm², mortar {mortar}: fk {fk} N/mm², fd {fd} N/mm² (γM {gm}, for all), fvk0 {fvk0} "
                       "N/mm²."),
    "report.masonry_type": ("O tipo «{type}», com alvenaria própria: {unit} do grupo {group}, fb {fb} N/mm², argamassa "
                            "{mortar}: fk {fk} N/mm², fd {fd} N/mm².",
                            "The type «{type}», with masonry of its own: {unit}, group {group}, fb {fb} N/mm², mortar "
                            "{mortar}: fk {fk} N/mm², fd {fd} N/mm²."),
    "report.masonry_flex": ("Paredes de fachada à flexão pelo vento (EC6 6.3 e Anexo E): fxk1 {f1} N/mm², fxk2 {f2} "
                            "N/mm² (quadro 3.4, valores recomendados); o vento 1,5 qp(z) no topo de cada parede × "
                            "{mid} a meio da fachada e × {corner} perto das esquinas (EN 1991-1-4, zonas D e A, com a "
                            "pressão interior); os bordos apoiados simplesmente; presas em cima, quando a flexão não "
                            "chega, o efeito de arco vertical (6.3.2).",
                            "Façade walls in bending by the wind (EC6 6.3 and annex E): fxk1 {f1} N/mm², fxk2 {f2} "
                            "N/mm² (table 3.4, recommended values); the wind 1.5 qp(z) at each wall's top × {mid} in "
                            "the middle of a façade and × {corner} near the corners (EN 1991-1-4, zones D and A, with "
                            "the inside pressure); the edges simply supported; held at the top, when bending is not "
                            "enough, vertical arching (6.3.2)."),
    "report.model_walls": ("E {w} paredes resistentes.", "And {w} load-bearing walls."),
    "report.concrete": ("Betão {c}: fck {fck} MPa, fcd {fcd} MPa (γc 1,5, αcc 1,0), fctm {fctm} MPa, Ecm {ecm} GPa.",
                        "Concrete {c}: fck {fck} MPa, fcd {fcd} MPa (γc 1.5, αcc 1.0), fctm {fctm} MPa, Ecm {ecm} "
                        "GPa."),
    "report.steel": ("Aço {s} NR: fyk {fyk} MPa, fyd {fyd} MPa (γs 1,15).", "Steel {s} NR: fyk {fyk} MPa, fyd {fyd} "
                                                                            "MPa (γs 1.15)."),
    "report.covers": ("Recobrimentos nominais: 3 cm (vigas e pilares), 2,5 cm (lajes), 5 cm (sapatas).",
                      "Nominal covers: 3 cm (beams and columns), 2.5 cm (slabs), 5 cm (footings)."),
    "report.soil": ("Tensão admissível do solo: {kpa} kPa.", "Soil's allowable pressure: {kpa} kPa."),
    "report.uses": ("Uso dos pisos: {use}; da cobertura: {roof}; ψ0 {psi0}, ψ1 {psi1}, ψ2 {psi2}.",
                    "Use of the floors: {use}; of the roof: {roof}; ψ0 {psi0}, ψ1 {psi1}, ψ2 {psi2}."),
    "report.dead": ("Restantes cargas permanentes: revestimentos {f} kN/m², divisórias {p} kN/m²; pesos próprios do "
                    "betão a 25 kN/m³ e das paredes a 15 kN/m³.",
                    "Other permanent loads: finishes {f} kN/m², partitions {p} kN/m²; the concrete's own weight at "
                    "25 kN/m³, the walls' at 15 kN/m³."),
    "report.wind": ("Vento: zona {zone} (vb,0 {vb} m/s), categoria de terreno {terrain}, cf 1,3.",
                    "Wind: zone {zone} (vb,0 {vb} m/s), terrain category {terrain}, cf 1.3."),
    "report.quake": ("Sismo: tipo 1 zona {z1} (agR {a1} m/s²), tipo 2 zona {z2} (agR {a2} m/s²), terreno {ground}, "
                     "classe de importância {imp}, coeficiente de comportamento q = {q}; método das forças laterais.",
                     "Earthquake: type 1 zone {z1} (agR {a1} m/s²), type 2 zone {z2} (agR {a2} m/s²), ground "
                     "{ground}, importance class {imp}, behaviour factor q = {q}; lateral force method."),
    "report.model": ("Modelo analítico: {nodes} nós, {c} pilares, {b} vigas, {s} apoios, {p} lajes.",
                     "Analytical model: {nodes} nodes, {c} columns, {b} beams, {s} supports, {p} slabs."),
    "report.no_issues": ("Sem problemas na verificação do modelo.", "No problems in the model's check."),
    "report.col.severity": ("Gravidade", "Severity"),
    "report.col.element": ("Elemento", "Element"),
    "report.col.issue": ("Problema", "Problem"),
    "report.col.total_length": ("Comprimento (m)", "Length (m)"),
    "report.notes": ("Pórtico espacial com 6 graus de liberdade por nó; cada piso um diafragma rígido; as lajes "
                     "descarregam nas vigas pelas áreas de influência.|Combinações fundamentais da NP EN 1990 (6.10) "
                     "com o vento e o sismo em X e em Y, nos dois sentidos; a sísmica (6.12b); a quase permanente "
                     "para as flechas.|Vigas: flexão pelo bloco retangular, esforço transverso com estribos de dois "
                     "ramos (cot θ de 2,5 a 1,0), deformação pelas relações vão/altura útil (EC2 7.4.2).|Pilares: "
                     "diagrama de interação N–M na direção mais fraca, excentricidade mínima, 2.ª ordem pela "
                     "curvatura nominal com l0 = L.|Sapatas: tensão no solo pela área efetiva com as reações de "
                     "serviço, flexão em consola, punçoamento junto ao pilar e a 2d.|Lajes: método de Marcus, "
                     "simplesmente apoiadas; a armadura superior sobre os apoios fica por definir.|Paredes de "
                     "alvenaria (EN 1996-1-1): as cargas pelas áreas de influência das lajes, as forças horizontais "
                     "repartidas pela rigidez das paredes de cada direção; hef = 0,75 h (lajes de betão no topo e na "
                     "base), esbelteza ≤ 27; compressão no topo e na base com Φ = 1 − 2e/t e a meio pelo anexo G; "
                     "corte no plano com fvk = fvk0 + 0,4 σd.|Paredes de betão armado (EN 1992-1-1): por metro, como um "
                     "pilar de 1 m × t, no topo, a meio (2.ª ordem por curvatura nominal, l0 = h) e na base; armadura "
                     "vertical nas duas faces entre 0,002 Ac e 0,04 Ac (9.6.2), horizontal ≥ 25 % da vertical e 0,001 "
                     "Ac (9.6.3), também armadura de corte no plano (6.2.3, cot θ = 1).|Não se verificam "
                     "a fendilhação, a fluência, a resistência ao fogo nem a durabilidade além dos recobrimentos.",
                     "A space frame with 6 degrees of freedom a node; each floor a rigid diaphragm; the slabs carried "
                     "to the beams by their areas.|The fundamental combinations of NP EN 1990 (6.10) with the wind "
                     "and the earthquake in X and Y, both ways; the seismic one (6.12b); the quasi-permanent one for "
                     "deflections.|Beams: bending by the rectangular stress block, shear with two-legged stirrups "
                     "(cot θ from 2.5 to 1.0), deflection by the span / effective depth ratios (EC2 7.4.2).|Columns: "
                     "the N–M interaction diagram about the weaker axis, the minimum eccentricity, second order by "
                     "the nominal curvature with l0 = L.|Footings: the soil's pressure on the effective area with the "
                     "service reactions, bending as cantilevers, punching at the column and at 2d.|Slabs: Marcus' "
                     "method, simply supported; the top reinforcement over the supports is to be defined.|Masonry "
                     "walls (EN 1996-1-1): the loads by the slabs' tributary areas, the horizontal forces shared by "
                     "the stiffness of the walls of each direction; hef = 0.75 h (concrete floors at the top and the "
                     "base), slenderness ≤ 27; compression at the top and the base with Φ = 1 − 2e/t and at "
                     "mid-height by annex G; in-plane shear with fvk = fvk0 + 0.4 σd.|Reinforced concrete walls (EN "
                     "1992-1-1): on each metre, as a 1 m × t column, at the top, mid-height (second order by nominal "
                     "curvature, l0 = h) and the base; vertical bars on both faces between 0.002 Ac and 0.04 Ac "
                     "(9.6.2), horizontal ≥ 25 % of the vertical and 0.001 Ac (9.6.3), also in-plane shear "
                     "reinforcement (6.2.3, cot θ = 1).|Cracking, "
                     "creep, fire resistance and durability beyond the covers are not checked."),
    "report.sign": ("Este documento é um pré-dimensionamento, feito por um programa. O projeto de estruturas é de um "
                    "engenheiro civil responsável, que o verifica, completa e assina.",
                    "This document is a pre-design, made by a program. The structural design is a responsible "
                    "structural engineer's, who checks, completes and signs it."),
    "tree.rebars": ("Armaduras", "Reinforcement"),
    "tree.structure": ("Plantas de estrutura", "Structure plans"),
    "tree.structure_view": ("Planta de estrutura — {name}", "Structure plan — {name}"),
    "tree.structure_below": ("{name} — cofragem vista de baixo", "{name} — formwork seen from below"),   # (0.235)
    "tree.structure_below_view": ("Cofragem vista de baixo — {name}", "Formwork seen from below — {name}"),
    "rdraw.slab_tag": ("{tag} h = {h}", "{tag} h = {h}"),
    "tree.rebar_view": ("Armaduras — {name}", "Reinforcement — {name}"),
    "rdraw.bars": ("{n} Ø{d} — pos. {m} — L = {l} m", "{n} Ø{d} — mark {m} — L = {l} m"),
    "rdraw.links": ("{n} Ø{d}//{s} — pos. {m}", "{n} Ø{d}//{s} — mark {m}"),
    "rdraw.mesh": ("{n} Ø{d}//{s} — pos. {m} — L = {l} m", "{n} Ø{d}//{s} — mark {m} — L = {l} m"),
    "rdraw.top_mesh": ("{n} Ø{d}//{s} sup. — pos. {m} — L = {l} m", "{n} Ø{d}//{s} top — mark {m} — L = {l} m"),
    "tree.rebar_cut_view": ("Corte {k}–{k} — {name}", "Section {k}–{k} — {name}"),
    "tree.openings": ("Mapa de vãos", "Door and window schedule"),                                   # (0.293)
    "omap.size": ("L × A: {w} × {h} m", "W × H: {w} × {h} m"),
    "omap.sill": ("Peitoril: {s} m", "Sill: {s} m"),
    "omap.opening": ("Abertura: {ways}", "Opening: {ways}"),
    "omap.count": ("Quantidade: {n}", "Number: {n}"),
    "omap.louvres": ("Com portadas de lâminas", "With louvred shutters"),                    # (0.295)
    "omap.op.fixed": ("fixo", "fixed"),
    "omap.op.side": ("batente", "side-hung"),
    "omap.op.tilt": ("oscilobatente", "tilt and turn"),
    "omap.op.top": ("projetante", "top-hung"),
    "omap.op.bottom": ("basculante", "bottom-hung"),
    "omap.op.pivot": ("pivotante", "pivot"),
    "omap.op.slide": ("correr", "sliding"),
    "omap.op.sash": ("guilhotina", "sash"),
    "omap.op.swing": ("vaivém", "double-acting"),
    "omap.op.fold": ("harmónio", "folding"),
    "tree.rebar_details": ("Pormenores tipo", "Typical details"),                                    # (0.237)
    "tree.steel_parts": ("Peças de aço (fabrico)", "Steel pieces (fabrication)"),                     # (0.502)
    "sdraw.piece": ("{mark} — {section} {grade} — {n} peça(s) de {l} m — {kg} kg",
                    "{mark} — {section} {grade} — {n} piece(s) {l} m long — {kg} kg"),
    "sdraw.plate": ("{mark} — chapa {l} × {w} × {t} mm, {holes} furos Ø{d} — {n} peça(s) — {kg} kg (1:{s})",
                    "{mark} — plate {l} × {w} × {t} mm, {holes} holes Ø{d} — {n} piece(s) — {kg} kg (1:{s})"),
    "sdraw.gusset": ("{mark} — gousset {t} mm (cabe em {l} × {w}), {holes} furos Ø{d} — {n} peça(s) — {kg} kg (1:{s})",
                     "{mark} — gusset plate {t} mm (within {l} × {w}), {holes} holes Ø{d} — {n} piece(s) — {kg} kg "
                     "(1:{s})"),                                                                        # (0.503)
    "tree.rebar_details_view": ("Pormenores tipo de armaduras", "Typical reinforcement details"),
    "rdet.joint": ("Nó viga-pilar — {beam} / {column}", "Beam-column joint — {beam} / {column}"),
    "rdet.splices": ("Emendas por sobreposição", "Lap splices"),
    "rdet.splice": ("Ø{d} — l0 = 1,5 × lb,rqd = {l} m ({c}, {s})", "Ø{d} — l0 = 1.5 × lb,rqd = {l} m ({c}, {s})"),
    "props.rebar_host": ("Armadura de", "Reinforcement of"),
    "props.rebar_mark": ("Posição", "Mark"),
    "props.rebar_bars": ("Varões", "Bars"),
    "props.rebar_bars_v": ("{n} Ø{d}, {l} cada (forma {s})", "{n} Ø{d}, {l} each (shape {s})"),
    "props.rebar_weight": ("Peso", "Weight"),
    "rsched.title": ("Lista de armaduras", "Bar schedule"),
    "rsched.col.mark": ("Pos.", "Mark"),
    "rsched.col.element": ("Elemento", "Element"),
    "rsched.col.role": ("Função", "Role"),
    "rsched.col.diameter": ("Ø (mm)", "Ø (mm)"),
    "rsched.col.count": ("Quant.", "No."),
    "rsched.col.length": ("Comp. (m)", "Length (m)"),
    "rsched.col.shape": ("Forma", "Shape"),
    "rsched.col.total": ("Comp. total (m)", "Total length (m)"),
    "rsched.col.weight": ("Peso (kg)", "Weight (kg)"),
    "rsched.role.bottom": ("inferior", "bottom"),
    "rsched.role.top": ("superior", "top"),
    "rsched.role.stirrups": ("estribos", "stirrups"),
    "rsched.role.main": ("longitudinal", "main"),
    "rsched.role.ties": ("cintas", "ties"),
    "rsched.role.mesh_x": ("malha X", "mesh X"),
    "rsched.role.mesh_y": ("malha Y", "mesh Y"),
    "rsched.role.top_x": ("superior X", "top X"),                                                 # (0.224)
    "rsched.role.top_y": ("superior Y", "top Y"),
    "rsched.role.wall_v": ("vertical", "vertical"),                                            # (0.342)
    "rsched.role.wall_h": ("horizontal", "horizontal"),
    "rsched.role.wall_trim": ("reforço dos vãos", "round the openings"),
    "rsched.totals": ("Totais: {items} · total {kg} kg.", "Totals: {items} · total {kg} kg."),
    "rsched.total_item": ("Ø{d}: {m} m, {kg} kg", "Ø{d}: {m} m, {kg} kg"),
    "rsched.empty": ("Ainda não há armaduras no modelo: abra Verificação EC2 / EC6 e armaduras e clique em Pôr as armaduras "
                    "no modelo.", "No reinforcement in the model yet: open EC2 check and reinforcement and click Put "
                                  "the reinforcement in the model."),
    "rsched.note": ("Formas pela BS 8666: 00 direito, 11 uma dobra, 21 duas dobras, 51 estribo fechado com ganchos a "
                   "135°. Comprimentos de corte sem descontos das dobras. Um duplo clique seleciona o conjunto.",
                   "Shapes by BS 8666: 00 straight, 11 one bend, 21 two bends, 51 closed link with 135° hooks. Cut "
                   "lengths without bending deductions. A double-click selects the set."),
    "rsched.export": ("Exportar (Excel, CSV)…", "Export (Excel, CSV)…"),
    "rsched.export_title": ("Exportar a lista de armaduras", "Export the bar schedule"),
    "info.sched_exported": ("Lista de armaduras exportada para {f}.", "Bar schedule exported to {f}."),
    "actions.title": ("Ações e materiais da estrutura", "The structure's actions and materials"),
    "actions.concrete": ("Betão", "Concrete"),
    "actions.steel": ("Aço das armaduras", "Reinforcing steel"),
    "actions.use": ("Uso dos pisos", "Use of the floors"),
    "actions.roof_use": ("Uso da cobertura", "Use of the roof"),
    "actions.finishes": ("Revestimentos e tetos", "Finishes and ceilings"),
    "actions.partitions": ("Divisórias (distribuídas)", "Partitions (spread)"),
    "actions.soil_kpa": ("Tensão admissível do solo", "Soil's allowable pressure"),
    "actions.slabs": ("Lajes no cálculo", "Slabs in the analysis"),                                 # (0.223)
    "actions.slabs.shells": ("Cascas (elementos finitos)", "Shells (finite elements)"),
    "actions.slabs.areas": ("Áreas de influência (cargas às vigas)", "Tributary areas (loads to the beams)"),
    "actions.wind_zone": ("Vento: zona", "Wind: zone"),
    "actions.terrain": ("Vento: categoria do terreno", "Wind: terrain category"),
    "actions.seismic_zone_1": ("Sismo afastado (tipo 1): zona", "Far earthquake (type 1): zone"),
    "actions.seismic_zone_2": ("Sismo próximo (tipo 2): zona", "Near earthquake (type 2): zone"),
    "actions.ground": ("Tipo de terreno (sismo)", "Ground type (earthquake)"),
    "actions.importance": ("Classe de importância", "Importance class"),
    "actions.terrain.I": ("I — zona costeira exposta aos ventos de mar", "I — coast exposed to the sea's winds"),  # (0.219)
    "actions.terrain.II": ("II — vegetação rasteira, obstáculos isolados", "II — low vegetation, isolated obstacles"),
    "actions.terrain.III": ("III — subúrbios, florestas", "III — suburbs, forests"),
    "actions.terrain.IV": ("IV — cidade (15 % com edifícios de mais de 15 m)",
                           "IV — town (15 % with buildings over 15 m)"),    "actions.snow_zone": ("Neve: zona", "Snow: zone"),                                  # (0.217)
    "actions.snow_zone.Z1": ("Z1 (Cz 0,30)", "Z1 (Cz 0.30)"),
    "actions.snow_zone.Z2": ("Z2 (Cz 0,20)", "Z2 (Cz 0.20)"),
    "actions.snow_zone.Z3": ("Z3 — Açores e Madeira (Cz 0,10)", "Z3 — Azores and Madeira (Cz 0.10)"),
    "actions.altitude": ("Altitude do local", "Site's altitude"),
    "actions.snow_summary": ("Neve: sk = {sk} kN/m² no solo, {s} kN/m² na cobertura (μ1 0,8); a cobertura com "
                             "{q} kN/m² (a maior entre a sobrecarga do uso e a neve).",
                             "Snow: sk = {sk} kN/m² on the ground, {s} kN/m² on the roof (μ1 0.8); the roof with {q} "
                             "kN/m² (the greater of its use's imposed load and the snow)."),
    "report.snow": ("Neve (NP EN 1991-1-3): zona {zone}, altitude {h} m, sk = {sk} kN/m², na cobertura plana "
                    "{s} kN/m²; a cobertura carregada com {q} kN/m² (a maior entre a sobrecarga e a neve, que não se "
                    "combinam).",
                    "Snow (NP EN 1991-1-3): zone {zone}, altitude {h} m, sk = {sk} kN/m², on a flat roof {s} kN/m²; "
                    "the roof loaded with {q} kN/m² (the greater of the imposed load and the snow, not combined)."),
    "actions.use.A": ("A — habitação (2,0 kN/m²)", "A — housing (2.0 kN/m²)"),
    "actions.use.B": ("B — escritórios (3,0)", "B — offices (3.0)"),
    "actions.use.C1": ("C1 — com mesas: escolas, cafés (3,0)", "C1 — with tables: schools, cafés (3.0)"),
    "actions.use.C2": ("C2 — com lugares fixos (4,0)", "C2 — fixed seats (4.0)"),
    "actions.use.C3": ("C3 — sem obstáculos: museus, átrios (5,0)", "C3 — free to move: museums, halls (5.0)"),
    "actions.use.D1": ("D1 — comércio (4,0)", "D1 — shops (4.0)"),
    "actions.use.E1": ("E1 — armazenagem (7,5)", "E1 — storage (7.5)"),
    "actions.use.H": ("H — cobertura não acessível (0,4)", "H — roof not accessible (0.4)"),
    "actions.col.level": ("Altura (m)", "Height (m)"),
    "actions.col.area": ("Lajes (m²)", "Slabs (m²)"),
    "actions.col.g": ("G (kN)", "G (kN)"),
    "actions.col.q": ("Q (kN)", "Q (kN)"),
    "actions.col.weight": ("Peso sísmico (kN)", "Seismic weight (kN)"),
    "actions.col.wind_x": ("Vento X (kN)", "Wind X (kN)"),
    "actions.col.wind_y": ("Vento Y (kN)", "Wind Y (kN)"),
    "actions.col.quake_1": ("Sismo tipo 1 (kN)", "Earthquake type 1 (kN)"),
    "actions.col.quake_2": ("Sismo tipo 2 (kN)", "Earthquake type 2 (kN)"),
    "actions.summary": ("Período estimado T1 = {t1} s; Sd = {sd1} m/s² (tipo 1), {sd2} m/s² (tipo 2); corte basal "
                        "{b1} kN (tipo 1), {b2} kN (tipo 2).",
                        "Estimated period T1 = {t1} s; Sd = {sd1} m/s² (type 1), {sd2} m/s² (type 2); base shear {b1} "
                        "kN (type 1), {b2} kN (type 2)."),
    "actions.none": ("Ainda não há estrutura: faça pilares, vigas e lajes (separador Estrutura).",
                     "No structure yet: make columns, beams and slabs (the Structure tab)."),
    "actions.note": ("Eurocódigos com os Anexos Nacionais portugueses, para pré-dimensionamento: vento pela NP EN "
                     "1991-1-4 (pressão de pico por piso, cf 1,3), sismo pela NP EN 1998-1 (método das forças "
                     "laterais, q = 2,0, T1 estimado), sobrecargas pela NP EN 1991-1-1. O projeto de estruturas é do "
                     "engenheiro, que o assina.",
                     "Eurocodes with Portugal's National Annexes, for pre-design: wind by NP EN 1991-1-4 (peak pressure "
                     "per storey, cf 1.3), earthquake by NP EN 1998-1 (lateral force method, q = 2.0, estimated T1), "
                     "imposed loads by NP EN 1991-1-1. The structural design is the engineer's, who signs it."),
    "info.actions": ("Ações guardadas: cargas G e Q no modelo analítico ({n} pisos; corte basal sísmico {b} kN).",
                     "Actions kept: loads G and Q on the analytical model ({n} storeys; seismic base shear {b} kN)."),
    "act.show_analytical": ("Modelo analítico", "Analytical model"),
    "struct.title": ("Modelo estrutural: verificação", "Structural model: check"),
    "struct.summary": ("Modelo analítico: {nodes} nós, {c} pilares, {b} vigas, {s} apoios, {p} lajes. {e} erros, {w} "
                       "avisos.",
                       "Analytical model: {nodes} nodes, {c} columns, {b} beams, {s} supports, {p} slabs. {e} errors, "
                       "{w} warnings."),
    "struct.note": ("O modelo analítico é o eixo de cada pilar e de cada viga, ligados nos nós, com os apoios nas "
                    "sapatas; vai para o IFC (IfcStructuralAnalysisModel) para os programas de cálculo. Os erros "
                    "impedem o cálculo; um duplo clique seleciona o elemento.",
                    "The analytical model is each column's and beam's axis, joined at the nodes, the supports on the "
                    "footings; it goes into the IFC (IfcStructuralAnalysisModel) for analysis programs. Errors stop "
                    "a calculation; a double-click selects the element."),
    "struct.again": ("Verificar outra vez", "Check again"),
    "struct.sev.erro": ("Erro", "Error"),
    "struct.sev.aviso": ("Aviso", "Warning"),
    "struct.sev.info": ("Nota", "Note"),
    "struct.issue.column_no_height": ("pilar sem altura", "column with no height"),
    "struct.issue.column_no_section": ("pilar sem secção", "column with no section"),
    "struct.issue.beam_no_length": ("viga sem comprimento", "beam with no length"),
    "struct.issue.beam_no_section": ("viga sem secção", "beam with no section"),
    "struct.issue.not_concrete": ("material que não é betão: fora do dimensionamento do Eurocódigo 2",
                                  "a material other than concrete: outside the Eurocode 2 design"),
    "struct.issue.no_footing": ("pilar na cota da fundação sem sapata (fica encastrado, mas falta a sapata)",
                                "column at the foundations' level without a footing (fixed there, but it lacks one)"),
    "struct.issue.column_hanging": ("pilar suspenso: sem nada por baixo (sapata, pilar ou viga)",
                                    "hanging column: nothing under it (footing, column or beam)"),
    "struct.issue.off_level": ("base do pilar fora de qualquer nível", "column's base off every level"),
    "struct.issue.beam_loose": ("viga sem apoio em nenhum dos extremos", "beam held at neither end"),
    "struct.issue.beam_free_end": ("viga com um extremo sem apoio (é uma consola?)",
                                   "beam with one end free (a cantilever?)"),
    "struct.issue.footing_alone": ("sapata sem pilar por cima", "footing with no column on it"),
    "struct.issue.duplicate": ("pilares sobrepostos", "columns one on the other"),
    "struct.issue.panel_no_thickness": ("laje sem espessura", "slab with no thickness"),
    "struct.issue.panel_unsupported": ("laje sem vigas nem pilares que a apoiem", "slab with no beams nor columns "
                                                                               "holding it"),
    "struct.issue.no_supports": ("o modelo não tem apoios", "the model has no supports"),
    # (0.335) the load-bearing walls
    "struct.issue.wall_no_size": ("parede resistente sem comprimento, altura ou espessura",
                                  "load-bearing wall with no length, height or thickness"),
    "struct.issue.wall_concrete": ("parede resistente de betão: entra nas cargas, mas a verificação (EC2 de paredes) "
                                   "ainda não se faz",
                                   "concrete load-bearing wall: it takes its loads, but its check (EC2 for walls) is "
                                   "not made yet"),
    "struct.issue.wall_no_footing": ("parede resistente na cota da fundação sem sapata corrida (apoia-se, mas falta a "
                                     "sapata)",
                                     "load-bearing wall at the foundations' level without a strip footing (held, but "
                                     "it lacks one)"),
    "struct.issue.wall_on_slab": ("parede resistente sobre uma laje, sem parede por baixo: a laje leva a carga dela",
                                  "load-bearing wall on a slab, with no wall under it: the slab takes its load"),
    "struct.issue.wall_hanging": ("parede resistente suspensa: sem nada por baixo (sapata, parede ou laje)",
                                  "hanging load-bearing wall: nothing under it (footing, wall or slab)"),
    "info.analytical": ("Modelo analítico feito: {n} barras, {s} apoios.", "Analytical model made: {n} members, {s} "
                                                                          "supports."),
    "act.model_from_scan": ("Modelo a partir da nuvem…", "Model from the point cloud…"),
    "scan.title": ("Modelo a partir da nuvem de pontos", "Model from the point cloud"),
    "scan.intro": ("O chão e o teto são as alturas onde os pontos se juntam (corrija-os se for preciso). As paredes "
                   "leem-se numa fatia a meia altura: as linhas de pontos, endireitadas pela direção principal do "
                   "edifício; duas a uma espessura de parede são as faces de uma parede (por cima das portas e "
                   "janelas), e uma linha sozinha, uma fachada vista só por dentro, faz uma parede para fora. Veja a "
                   "azul o que se encontra.",
                   "The floor and the ceiling are the heights where the points gather (correct them if need be). "
                   "The walls are read in a slice at mid height: the lines of points, squared to the building's main "
                   "direction; two a wall's thickness apart are a wall's faces (over its doors and windows), and a "
                   "line alone, a façade seen from inside only, makes a wall outwards. What is found is shown in "
                   "blue."),
    "scan.cloud": ("Nuvem", "Cloud"),
    "scan.floor": ("Chão (cota)", "Floor (height)"),
    "scan.height": ("Altura das paredes", "Walls' height"),
    "scan.slice": ("Fatia acima do chão, de", "Slice over the floor, from"),
    "scan.outer": ("Espessura das paredes vistas de um só lado", "Thickness of the walls seen from one side"),
    "scan.slab": ("Fazer a laje do piso debaixo das paredes", "Make the floor's slab under the walls"),
    "scan.again": ("Procurar outra vez", "Look again"),
    "scan.none": ("Nenhuma parede encontrada: veja a cota do chão e a fatia.",
                  "No walls found: check the floor's height and the slice."),
    "err.scan_no_cloud": ("Ligue primeiro uma nuvem de pontos (Inserir ▸ Vincular ▸ Nuvem de pontos).",
                          "Link a point cloud first (Home ▸ Import ▸ Point cloud)."),
    "info.scanmodel": ("Da nuvem: {w} paredes e {s} laje. Ctrl+Z desfaz.",
                       "From the cloud: {w} walls and {s} slab. Ctrl+Z undoes."),
    "info.scanmodel_openings": ("E {d} portas e {j} janelas nos vãos que a nuvem tem.",               # (0.213)
                                "And {d} doors and {j} windows in the gaps the cloud has."),
    "scan.openings": ("Nos vãos: {d} portas e {w} janelas.", "In the gaps: {d} doors and {w} windows."),
    "scan.all_storeys": ("Todos os pisos de uma vez", "Every storey at once"),          # (0.214)
    "scan.all_storeys_n": ("Todos os pisos de uma vez ({n}: chão a {z} m)", "Every storey at once ({n}: floor at {z} m)"),
    "scan.in_storeys": ("Em {n} pisos.", "On {n} storeys."),
    "scan.storey_name": ("Piso {n}", "Storey {n}"),
    "info.scanmodel_storeys": ("Em {n} pisos.", "On {n} storeys."),
    "cmd.model_from_scan": ("Modelo a partir da nuvem", "Model from the point cloud"),
    "act.cloud_link": ("Ligar uma nuvem de pontos…", "Link a point cloud…"),
    "act.cloud_links": ("Nuvens de pontos ligadas…", "Linked point clouds…"),
    "file.clouds": ("Nuvens de pontos", "Point clouds"),
    "cmd.cloud_link": ("Ligar nuvem", "Link cloud"),
    "cmd.cloud_change": ("Mudar a nuvem ligada", "Change linked cloud"),
    "cmd.cloud_remove": ("Apagar a nuvem ligada", "Delete linked cloud"),
    "clouds.title": ("Nuvens de pontos ligadas", "Linked point clouds"),
    "clouds.intro": ("Levantamentos com laser ou fotogrametria postos no modelo, para ver o edifício como está e "
                     "desenhar por cima (numa planta vê-se a fatia abaixo do corte). Não vão para o IFC, e o ficheiro "
                     "fica onde está; mostram-se no máximo 1,5 milhões de pontos, tirados por igual.",
                     "Laser or photogrammetry surveys laid in the model, to see the building as it is and draw over "
                     "it (a plan shows the slice under its cut). They do not go into the IFC, and the file stays "
                     "where it is; at most 1.5 million points are shown, taken evenly."),
    "clouds.size": ("Tamanho dos pontos", "Points' size"),
    "clouds.link": ("Ligar nuvem…", "Link cloud…"),
    "clouds.count": ("{n} pontos mostrados", "{n} points shown"),
    "clouds.reading": ("A ler «{f}»…", "Reading \"{f}\"…"),
    "err.dwg_converter": ("Para ler «{f}» é preciso o ODA File Converter (gratuito, da Open Design Alliance) "
                          "instalado: o DWG é convertido em DXF por ele.",
                          "Reading \"{f}\" needs the ODA File Converter (free, from the Open Design Alliance) "
                          "installed: it turns the DWG into a DXF."),
    "err.cloud_read": ("Não foi possível ler «{f}» (os formatos lidos são XYZ, PTS, TXT, PLY, LAS, LAZ e E57; o "
                       "LAZ e o E57 precisam das bibliotecas laspy/lazrs e pye57 instaladas).",
                       "\"{f}\" could not be read (the formats read are XYZ, PTS, TXT, PLY, LAS, LAZ and E57; LAZ "
                       "and E57 need the laspy/lazrs and pye57 libraries installed)."),
    "info.cloud_linked": ("«{f}» ligado, {n} pontos à vista ({how}).", "\"{f}\" linked, {n} points shown ({how})."),
    "act.cad_link": ("Ligar um desenho DXF/DWG…", "Link a DXF/DWG drawing…"),
    "act.cad_links": ("Desenhos CAD ligados…", "Linked CAD drawings…"),
    "cmd.cad_link": ("Ligar desenho", "Link drawing"),
    "cmd.cad_change": ("Mudar o desenho ligado", "Change linked drawing"),
    "cmd.cad_remove": ("Apagar o desenho ligado", "Delete linked drawing"),
    "cadlinks.title": ("Desenhos CAD ligados", "Linked CAD drawings"),
    "cadlinks.intro": ("Plantas em DXF postas debaixo de um pavimento, para desenhar por cima (as ferramentas "
                       "agarram-se às suas linhas). Não vão para o IFC, e o DXF fica onde está: se mudar no programa "
                       "de CAD, vê-se como está da próxima vez que abrir o projeto.",
                       "DXF plans laid under a storey, to draw over (the tools snap to their lines). They do not go "
                       "into the IFC, and the DXF stays where it is: changed in the CAD program, it is seen as it is "
                       "the next time the project opens."),
    "cadlinks.units": ("Unidades do desenho", "Drawing units"),
    "cadlinks.layers": ("Camadas (as marcadas veem-se):", "Layers (those ticked are shown):"),
    "cadlinks.layer": ("{name} — {n} entidades, {s} linhas", "{name} — {n} entities, {s} lines"),
    "cadlinks.link": ("Ligar DXF…", "Link DXF…"),
    "err.cad_locked": ("O desenho «{f}» está bloqueado: desbloqueie-o primeiro.",
                       "The drawing \"{f}\" is locked: unlock it first."),
    "err.cad_read": ("Não foi possível ler «{f}» (não é um DXF em texto, ou está danificado).",
                     "\"{f}\" could not be read (not a text DXF, or damaged)."),
    "err.cad_empty": ("«{f}» não tem linhas para mostrar.", "\"{f}\" has no lines to show."),
    "info.cad_linked": ("«{f}» ligado ao pavimento {s} ({u}; {how}). As camadas veem-se e escondem-se em Inserir ▸ "
                        "Vincular ▸ DXF ligados.",
                        "\"{f}\" linked to the storey {s} ({u}; {how}). Its layers are shown or hidden in Collaborate ▸ "
                        "Links ▸ Linked DXFs."),
    "cadlinks.how.shared": ("nas coordenadas do levantamento do projeto", "in the project's survey coordinates"),
    "cadlinks.how.origin": ("origem com origem", "origin to origin"),
    "cadlinks.how.centre": ("ao centro da vista", "centred in the view"),
    "cadlinks.units_given": ("em {u}", "in {u}"),
    "cadlinks.units_guessed": ("em {u}, pelo tamanho", "in {u}, by its size"),
    "tool.platform": ("Plataforma", "Platform"),
    "tool.platform_outline": ("Editar plataforma", "Edit platform"),                    # (0.204)
    "tool.terrain_ramp": ("Rampa de acesso", "Access ramp"),                             # (0.205)
    "rib.short.terrain_ramp": ("Rampa de\nacesso", "Access\nramp"),
    "elem.terrain_ramp": ("Rampa", "Ramp"),
    "cmd.terrain_ramp": ("Rampa de acesso", "Access ramp"),
    "ctx.ramp_width": ("Largura", "Width"),
    "hint.terrain_ramp": ("Rampa de acesso: clique onde começa (o meio da ponta, por exemplo na borda de uma "
                          "plataforma). Fica à cota do terreno (ou da plataforma) nesse ponto.",
                          "Access ramp: click where it starts (the middle of its end, on a platform's edge for "
                          "instance). It is at the ground's (or the platform's) height there."),
    "hint.terrain_ramp_end": ("Clique onde acaba (na outra plataforma). {text}",
                              "Click where it ends (on the other platform). {text}"),
    "info.terrain_ramp_shape": ("De {a} a {b}, {l} de comprimento: {s} %.", "From {a} to {b}, {l} long: {s} %."),
    "info.terrain_ramp": ("Rampa feita. {text} Desaterro {c}, aterro {f}. Ctrl+Z desfaz.",
                          "Ramp made. {text} Cut {c}, fill {f}. Ctrl+Z undoes."),
    "err.terrain_ramp": ("A rampa não se fez: é curta demais, ou uma ponta fica fora do terreno.",
                         "No ramp made: it is too short, or one of its ends is off the terrain."),
    "act.edit_platform": ("Editar plataforma", "Edit platform"),
    "rib.short.edit_platform": ("Editar\nplataforma", "Edit\nplatform"),
    "tip.edit_platform": ("Mudar o contorno de uma plataforma já feita pelos cantos: mover, acrescentar e tirar "
                          "cantos (os taludes e o terreno à volta refazem-se)",
                          "Change a platform's outline by its corners: move, add and take away corners (its slopes "
                          "and the ground round it are made again)"),
    "info.edit_platform_none": ("Selecione um terreno com plataformas (ou tenha só um) para editar uma plataforma.",
                                "Select a terrain with platforms (or have only one) to edit a platform."),
    "info.edit_platform": ("A editar as plataformas de «{name}».", "Editing the platforms of «{name}»."),
    "hint.platform_pick": ("Clique dentro da plataforma a editar. Esc: Selecionar.",
                           "Click inside the platform to edit. Esc: Select."),
    "hint.platform_outline": ("Arraste um canto (quadrado) para o mover, ou o meio de um lado (losango) para "
                              "acrescentar um canto. Clique num canto e Delete: tira-o. Esc: Selecionar.",
                              "Drag a corner (square) to move it, or a side's middle (diamond) to add a corner. Click "
                              "a corner and Delete: it goes. Esc: Select."),
    "hint.platform_outline_none": ("Este terreno não tem plataformas. Esc: Selecionar.",
                                   "This terrain has no platforms. Esc: Select."),
    "err.platform_three_corners": ("Uma plataforma precisa de pelo menos três cantos.",
                                   "A platform needs three corners at least."),
    "err.platform_outline_bad": ("Esse contorno não serve: os lados cruzam-se, tem menos de três cantos, ou é pequeno "
                                 "demais.",
                                 "That outline will not do: its sides cross, it has fewer than three corners, or it "
                                 "is too small."),
    "info.platform_volumes": ("Desaterro {c}, aterro {f}. Ctrl+Z desfaz.", "Cut {c}, fill {f}. Ctrl+Z undoes."),
    "cmd.platform_edit": ("Editar plataforma", "Edit platform"),
    "elem.platform": ("Plataforma", "Platform"),
    "cmd.platform": ("Plataforma", "Platform"),
    "cmd.remove_platform": ("Apagar plataforma", "Delete platform"),
    "ctx.platform_shape": ("Forma", "Shape"),
    "ctx.platform_cut": ("Talude de escavação", "Cut slope"),
    "ctx.platform_fill": ("Talude de aterro", "Fill slope"),
    "slope.1:1": ("1:1 (45°)", "1:1 (45°)"),
    "slope.2:3": ("2:3 (1 por 1,5)", "2:3 (1 in 1.5)"),
    "slope.1:2": ("1:2", "1:2"),
    "slope.1:3": ("1:3", "1:3"),
    "slope.vertical": ("A prumo (muro)", "Upright (a wall)"),
    "hint.platform.none": ("Plataforma: faça primeiro o terreno (ou selecione aquele em que a quer pôr).",
                           "Platform: make the terrain first (or select the one to put it on)."),
    "hint.terrain_ramp.none": ("Rampa de acesso: faça primeiro o terreno (ou selecione aquele em que a quer pôr).",
                               "Access ramp: make the terrain first (or select the one to put it on)."),
    "hint.platform.rectangle": ("Plataforma: clique num canto. Fica à cota do terreno nesse ponto, ou escreva outra "
                                "(ex.: 1,20) e Enter.",
                                "Platform: click a corner. It is at the ground's height there, or type another "
                                "(e.g. 1.20) and Enter."),
    "hint.platform.polygon": ("Plataforma: clique no primeiro canto. Fica à cota do terreno nesse ponto, ou escreva "
                              "outra e Enter.",
                              "Platform: click its first corner. It is at the ground's height there, or type another "
                              "and Enter."),
    "hint.platform.end_rectangle": ("Clique no canto oposto (cota {z}; escreva outra para a mudar).",
                                    "Click the opposite corner (height {z}; type another to change it)."),
    "hint.platform.more": ("Clique no canto seguinte; Enter, ou um clique no primeiro, fecha (cota {z}).",
                           "Click the next corner; Enter, or a click on the first one, closes it (height {z})."),
    "err.platform_small": ("A plataforma é pequena demais.", "The platform is too small."),
    "info.platform": ("Plataforma a {z}. No terreno todo: escavação {c}, aterro {f}. Ctrl+Z desfaz.",
                      "Platform at {z}. On the whole terrain: cut {c}, fill {f}. Ctrl+Z undoes."),
    "act.earthworks": ("Aterro e escavação…", "Cut and fill…"),
    "earth.title": ("Aterro e escavação", "Cut and fill"),
    "earth.intro": ("As plataformas dos terrenos, com a terra que cada uma tira (escavação) e põe (aterro), entre o "
                    "terreno do levantamento e o proposto. Os totais contam uma só vez onde as plataformas se "
                    "sobrepõem.",
                    "The terrains' platforms, with the earth each takes away (cut) and brings (fill), between the "
                    "surveyed ground and the proposed one. The totals count once where platforms overlap."),
    "earth.name": ("Plataforma", "Platform"),
    "earth.height": ("Cota", "Height"),
    "earth.area": ("Área", "Area"),
    "earth.cut": ("Escavação", "Cut"),
    "earth.fill": ("Aterro", "Fill"),
    "earth.remove": ("Apagar a plataforma", "Delete the platform"),
    "earth.totals": ("Total: escavação {c}, aterro {f} (saldo {b}).", "Total: cut {c}, fill {f} (balance {b})."),
    "earth.none": ("Ainda não há plataformas (ferramenta Plataforma, no separador Conceito).",
                   "No platforms yet (the Platform tool, in the Concept tab)."),
    "props.platforms": ("Plataformas", "Platforms"),
    "props.earthworks": ("Escavação / aterro", "Cut / fill"),
    "act.terrain_dxf": ("Terreno a partir de um DXF/DWG…", "Terrain from a DXF/DWG…"),
    "act.terrain_slopes": ("Inclinações do terreno", "Terrain slopes"),
    "info.slopes": ("Inclinação do terreno: verde até 5 %, amarelo-esverdeado até 10 %, amarelo até 15 %, laranja "
                    "até 25 %, vermelho acima.",
                    "Terrain slope: green up to 5 %, yellow-green up to 10 %, yellow up to 15 %, orange up to 25 %, "
                    "red above."),
    "dxfpts.title": ("Terreno a partir de um DXF", "Terrain from a DXF"),
    "dxfpts.intro": ("Camadas de «{f}» com pontos com cota (pontos, curvas de nível, linhas e faces 3D, blocos, cotas "
                     "escritas). O terreno passa pelos pontos das camadas marcadas.",
                     "Layers of \"{f}\" with points that have a height (points, contour lines, 3D lines and faces, "
                     "blocks, written spot heights). The terrain goes through the points of the layers ticked."),
    "dxfpts.layer": ("{name} — {n} pontos, de {lo} a {hi} m", "{name} — {n} points, from {lo} to {hi} m"),
    "err.dxf_read": ("Não foi possível ler «{f}»: {e}", "\"{f}\" could not be read: {e}"),
    "err.dxf_none": ("«{f}» não tem pontos com cota (é um desenho em 2D?).",
                     "\"{f}\" has no points with a height (is it a 2D drawing?)."),
    "props.terrain_points": ("Pontos", "Points"),
    "props.terrain_heights": ("Cotas (mín. — máx.)", "Heights (min. — max.)"),
    "props.terrain_interval": ("Curvas de nível de", "Contour lines every"),
    "props.terrain_depth": ("Base abaixo do ponto mais baixo", "Base below the lowest point"),
    "tool.calibrate_image": ("Calibrar imagem", "Calibrate image"),
    "act.import_image": ("Importar imagem de fundo…", "Import background image…"),
    "act.images": ("Imagens de fundo…", "Background images…"),
    "file.images": ("Imagens", "Images"),
    "cmd.import_image": ("Importar imagem", "Import image"),
    "cmd.calibrate_image": ("Calibrar imagem", "Calibrate image"),
    "cmd.place_image": ("Pôr a imagem no sítio", "Place image"),
    "cmd.turn_image": ("Rodar a imagem", "Turn image"),
    "cmd.change_image": ("Mudar a imagem", "Change image"),
    "cmd.remove_image": ("Apagar a imagem", "Delete image"),
    "hint.image.none": ("Calibrar imagem: importe primeiro uma imagem (Inserir ▸ Importar ▸ Imagem de fundo).",
                        "Calibrate image: import an image first (Home ▸ Import ▸ Background picture)."),
    "hint.image.locked": ("A imagem está bloqueada. Desbloqueie-a em Visualizar ▸ Gráficos ▸ Imagens de fundo para a "
                          "calibrar outra vez.",
                          "The image is locked. Unlock it in View ▸ Look ▸ Background pictures to calibrate it again."),
    "hint.image.start": ("Clique na imagem no início de uma medida que conhece (uma cota, a largura de uma porta…).",
                         "Click on the image at the start of a measure you know (a dimension, a door's width…)."),
    "hint.image.end": ("Clique no fim dessa medida.", "Click at the end of that measure."),
    "hint.image.length": ("Escreva a medida verdadeira (ex.: 8,50) e Enter.",
                          "Type the real length (e.g. 8.50) and Enter."),
    "hint.image.length_later": ("Primeiro clique nos dois pontos da medida na imagem; depois escreva-a.",
                                "Click the two points of the measure on the image first; then type it."),
    "hint.image.place": ("Clique onde fica esse primeiro ponto no modelo (Esc deixa a imagem onde está).",
                         "Click where that first point is in the model (Esc leaves the image where it is)."),
    "hint.image.turn": ("Clique na direção do segundo ponto, ou escreva o ângulo (Esc deixa a imagem como está).",
                        "Click towards the second point, or type the angle (Esc leaves the image as it is)."),
    "info.image_imported": ("Imagem «{f}» importada, com {w} de largura. Calibre-a com uma medida que conhece.",
                            "Image \"{f}\" imported, {w} wide. Calibrate it with a measure you know."),
    "info.image_calibrated": ("Imagem calibrada (×{f}): tem agora {w} de largura, e ficou bloqueada.",
                              "Image calibrated (×{f}): it is now {w} wide, and locked."),
    "info.image_done": ("Imagem calibrada. Para a mudar, desbloqueie-a em Visualizar ▸ Gráficos ▸ Imagens de fundo.",
                        "Image calibrated. To change it, unlock it in View ▸ Look ▸ Background pictures."),
    "err.image_read": ("Não foi possível ler a imagem «{f}» (o formato não é conhecido, ou o ficheiro está "
                       "danificado).",
                       "The image \"{f}\" could not be read (an unknown format, or a damaged file)."),
    "err.image_locked": ("A imagem «{f}» está bloqueada: desbloqueie-a primeiro.",
                         "The image \"{f}\" is locked: unlock it first."),
    "images.title": ("Imagens de fundo", "Background images"),
    "images.intro": ("Imagens pousadas nos pavimentos, para desenhar por cima (uma planta digitalizada, uma "
                     "fotografia aérea). Não vão para o IFC: guardam-se com as vistas, e a imagem fica onde está.",
                     "Pictures laid on the storeys, to draw over (a scanned plan, an aerial photo). They do not go "
                     "into the IFC: they are kept with the views, and the picture stays where it is."),
    "images.name": ("Nome", "Name"),
    "images.storey": ("Pavimento", "Storey"),
    "images.width": ("Largura", "Width"),
    "images.opacity": ("Opacidade", "Opacity"),
    "images.visible": ("Visível", "Visible"),
    "images.crop": ("Recortar", "Crop"),                                                # (0.209)
    "images.crop_tip": ("Mostrar só uma parte da imagem escolhida: dois cliques, nos cantos da parte que fica",
                        "Show only a part of the chosen image: two clicks, at the corners of the part kept"),
    "images.whole": ("Inteira", "Whole"),
    "images.whole_tip": ("Mostrar outra vez a imagem escolhida inteira (sem recorte)",
                         "Show the chosen image whole again (no crop)"),
    "tool.crop_image": ("Recortar imagem", "Crop image"),
    "hint.crop_image.none": ("Escolha a imagem em Visualizar ▸ Imagens de fundo… e clique em «Recortar».",
                             "Choose the image in View ▸ Background images… and click «Crop»."),
    "hint.crop_image.first": ("Clique num canto da parte da imagem que fica. Esc: deixar como está.",
                              "Click a corner of the part of the image kept. Esc: leave it as it is."),
    "hint.crop_image.second": ("Clique no canto oposto.", "Click the opposite corner."),
    "err.crop_image_outside": ("Clique em cima da imagem.", "Click on the image."),
    "err.crop_image_thin": ("Essa parte é estreita demais: clique mais longe do primeiro canto.",
                            "That part is too thin: click farther from the first corner."),
    "cmd.crop_image": ("Recortar imagem", "Crop image"),
    "info.crop_image": ("«{f}» recortada (no ecrã e no papel). «Inteira», em Imagens de fundo…, mostra-a toda. "
                        "Ctrl+Z desfaz.",
                        "«{f}» cropped (on screen and on paper). «Whole», in Background images…, shows all of it. "
                        "Ctrl+Z undoes."),
    "images.facade": ("Pôr numa fachada", "Put on a facade"),                          # (0.208)
    "images.facade_tip": ("Pôr a imagem escolhida de pé numa face do modelo (a fotografia de uma fachada): dois "
                          "cliques, onde ficam os seus cantos de baixo",
                          "Stand the chosen image up on a face of the model (a facade's photo): two clicks, where "
                          "its lower corners go"),
    "tool.facade_image": ("Imagem numa fachada", "Image on a facade"),
    "hint.facade_image.none": ("Escolha a imagem em Visualizar ▸ Imagens de fundo… e clique em «Pôr numa fachada».",
                               "Choose the image in View ▸ Background images… and click «Put on a facade»."),
    "hint.facade_image.first": ("Clique numa face (uma parede, uma fachada) onde fica o canto de baixo à esquerda da "
                                "imagem. Esc: deixar como está.",
                                "Click a face (a wall, a facade) where the image's lower-left corner goes. Esc: "
                                "leave it as it is."),
    "hint.facade_image.second": ("Clique onde fica o canto de baixo à direita (ou digite a largura + Enter).",
                                 "Click where the lower-right corner goes (or type the width + Enter)."),
    "err.facade_image_face": ("Clique numa face de pé do modelo (uma parede, uma fachada).",
                              "Click an upright face of the model (a wall, a facade)."),
    "err.image_vertical": ("Esta imagem está numa fachada: para a mudar, ponha-a outra vez («Pôr numa fachada»).",
                           "This image is on a facade: to change it, put it there again («Put on a facade»)."),
    "cmd.facade_image": ("Imagem numa fachada", "Image on a facade"),
    "info.facade_image": ("«{f}» de pé na fachada: {w} × {h}. Ctrl+Z desfaz.",
                          "«{f}» standing on the facade: {w} × {h}. Ctrl+Z undoes."),
    "images.locked": ("Bloqueada", "Locked"),
    "images.import": ("Importar…", "Import…"),
    "images.calibrate": ("Calibrar", "Calibrate"),
    "images.remove": ("Apagar", "Delete"),
    "images.missing": ("Ficheiro da imagem em falta (mudou de pasta, ou foi apagado)",
                       "The image's file is missing (moved, or deleted)"),
    "images.ground": ("(nível 0)", "(level 0)"),
    "tool.scale": ("Escala", "Scale"),
    "cmd.scale": ("Escala", "Scale"),
    "vcb.factor": ("Fator", "Factor"),
    "hint.scale.select": ("Escala: selecione primeiro os esboços (os elementos BIM têm as medidas dos seus tipos).",
                          "Scale: select the sketches first (BIM elements have their types' sizes)."),
    "hint.scale.base": ("Clique no ponto base (fica onde está). Ctrl: a partir do centro.",
                        "Click the base point (it stays where it is). Ctrl: about the centre."),
    "hint.scale.centre": ("A partir do centro: digite o fator e Enter, ou clique num ponto da seleção e depois onde "
                          "ele vai. Ctrl: a partir de um ponto.",
                          "About the centre: type the factor and Enter, or click a point of the selection, then "
                          "where it goes. Ctrl: about a point."),
    "ctx.scale_centre": ("A partir do centro", "About the centre"),                    # (0.206)
    "info.scale_centre_on": ("Escala a partir do centro da seleção (Ctrl outra vez: a partir de um ponto).",
                             "Scaling about the selection's centre (Ctrl again: about a point)."),
    "info.scale_centre_off": ("Escala a partir de um ponto base.", "Scaling about a base point."),
    "hint.scale.factor": ("Digite o fator (ex.: 2, ou 1;1;2 por eixo) e Enter, ou clique num ponto da seleção e depois "
                          "onde ele vai.",
                          "Type the factor (e.g. 2, or 1;1;2 per axis) and Enter, or click a point of the selection and "
                          "then where it goes."),
    "hint.scale.target": ("Clique onde vai o ponto (o fator é a razão das distâncias ao ponto base).",
                          "Click where the point goes (the factor is the ratio of the distances from the base)."),
    "err.scale_zero": ("Um fator de zero apagava a forma: escolha outro.", "A factor of zero would wipe the shape out: "
                                                                           "choose another."),
    "info.scale": ("Escala {f} em {n} esboços. Ctrl+Z desfaz.", "Scaled {f}: {n} sketches. Ctrl+Z undoes."),
    "info.scale_bim": ("Os {n} elementos BIM selecionados ficaram como estavam (mude-lhes o tipo ou as medidas).",
                       "The {n} BIM elements selected stayed as they were (change their type or sizes)."),
    "tool.offset": ("Offset", "Offset"),
    "cmd.offset": ("Offset", "Offset"),
    "hint.offset.face": ("Offset: clique numa face de um esboço ou numa linha (a cadeia dela; as linhas escolhidas "
                         "antes, se as houver).",
                         "Offset: click a face of a sketch or a line (its chain; the lines picked before, if any)."),
    "hint.offset.distance": ("Mova o rato para o lado (dentro ou fora) e clique, ou digite a distância (ex.: 0,10) e "
                             "Enter. Esc cancela.",
                             "Move the mouse to the side (inside or outside) and click, or type the distance (e.g. "
                             "0.10) and Enter. Esc cancels."),
    "info.offset_lines": ("Linhas paralelas a {d}. Um valor escrito logo a seguir corrige-as.",
                          "Parallel lines at {d}. A value typed right after corrects them."),
    "err.offset_lines_plane": ("Essas linhas não estão num só plano: o Offset precisa de linhas num plano.",
                               "Those lines are not on one plane: Offset needs lines on a plane."),
    "info.offset": ("Contorno a {d} {w}. Um valor escrito logo a seguir corrige-o.",
                    "Outline {d} {w}. A value typed right after corrects it."),
    "offset.inside": ("para dentro: a face fica dividida", "inside: the face is divided"),
    "offset.outside": ("para fora: a face cresceu", "outside: the face grew"),
    "err.offset_face": ("Clique numa face de um esboço (não de um elemento BIM).",
                        "Click a face of a sketch (not of a BIM element)."),
    "err.offset_too_far": ("Tão longe para dentro, o contorno desaparece.", "That far inside, the outline vanishes."),
    "err.offset_convex": ("Essa distância muda a forma da face (fecha um canto ou parte-a em duas): escolha uma "
                          "menor.",
                          "That distance changes the face's shape (it closes a corner or splits it in two): choose a "
                          "smaller one."),
    "err.offset_outside": ("Para fora, só numa face sozinha (não na face de um volume).",
                           "Outside, only on a face on its own (not on a volume's face)."),
    "ctx.line_shape": ("Traço", "Stroke"),
    "lineshape.line": ("Reta", "Straight"),
    "lineshape.arc": ("Arco tangente", "Tangent arc"),
    "info.line_arc": ("Arcos: cada um sai tangente ao anterior (Tab volta às retas).",
                      "Arcs: each leaves tangent to the one before (Tab: back to straight lines)."),
    "info.line_straight": ("Retas (Tab: arcos).", "Straight lines (Tab: arcs)."),
    "hint.line.arc_start": ("Arco: clique no início (no chão ou numa face). Tab: retas.",
                            "Arc: click the start (on the ground or on a face). Tab: straight lines."),
    "hint.line.arc_next": ("Clique onde o arco acaba: sai tangente à linha anterior (o primeiro: meia "
                           "circunferência). Voltar ao primeiro ponto fecha uma face. Tab: retas; Esc termina.",
                           "Click where the arc ends: it leaves tangent to the line before (the first: a half "
                           "circle). Back at the first point closes a face. Tab: straight lines; Esc ends."),
    "info.arc": ("Arco de {n} troços.", "Arc of {n} pieces."),
    "hint.circle.centre": ("Círculo ({n} lados): clique no centro (no chão ou numa face).",
                           "Circle ({n} sides): click the centre (on the ground or on a face)."),
    "hint.circle.radius": ("Clique onde passa o círculo, ou digite o raio (ex.: 1,50) e Enter. Esc cancela.",
                           "Click where the circle goes through, or type the radius (e.g. 1.50) and Enter. Esc "
                           "cancels."),
    "vcb.radius": ("Raio", "Radius"),
    "ctx.circle_sides": ("Lados", "Sides"),
    "cmd.circle": ("Círculo", "Circle"),
    "tool.circle": ("Círculo", "Circle"),
    "info.circle": ("Círculo de raio {r} ({n} lados). Puxe-o com Push/Pull: os lados ficam uma superfície lisa.",
                    "Circle of radius {r} ({n} sides). Pull it with Push/Pull: its sides become one smooth surface."),
    # (0.458) Revit's polygons and ellipses, drawn by the Circle tool
    "hint.polygon.centre_in": ("Polígono inscrito ({n} lados): clique no centro (no chão ou numa face).",
                               "Inscribed polygon ({n} sides): click the centre (on the ground or on a face)."),
    "hint.polygon.centre_out": ("Polígono circunscrito ({n} lados): clique no centro (no chão ou numa face).",
                                "Circumscribed polygon ({n} sides): click the centre (on the ground or on a face)."),
    "hint.polygon.radius_in": ("Clique onde fica um canto, ou escreva o raio (ex.: 1,50) e Enter. Esc cancela.",
                               "Click where a corner goes, or type the radius (e.g. 1.50) and Enter. Esc cancels."),
    "hint.polygon.radius_out": ("Clique onde fica o meio de um lado, ou escreva a distância do centro aos lados (ex.: "
                                "1,50) e Enter. Esc cancela.",
                                "Click where the middle of a side goes, or type the distance from the centre to the "
                                "sides (e.g. 1.50) and Enter. Esc cancels."),
    "hint.ellipse.centre": ("Elipse: clique no centro (no chão ou numa face).",
                            "Ellipse: click the centre (on the ground or on a face)."),
    "hint.ellipse.axis": ("Clique na ponta de um dos eixos, ou escreva esse semieixo (ex.: 2,00) e Enter. Esc cancela.",
                          "Click the end of one axis, or type that half-axis (e.g. 2.00) and Enter. Esc cancels."),
    "hint.ellipse.minor": ("Mova o rato para o outro semieixo e clique, ou escreva-o e Enter. Esc cancela.",
                           "Move the mouse for the other half-axis and click, or type it and Enter. Esc cancels."),
    "hint.ellipse_part.start": ("Elipse parcial: clique onde começa o eixo (no chão ou numa face).",
                                "Partial ellipse: click where its axis starts (on the ground or on a face)."),
    "hint.ellipse_part.end": ("Clique onde acaba o eixo, ou escreva o comprimento e Enter. Esc cancela.",
                              "Click where the axis ends, or type its length and Enter. Esc cancels."),
    "hint.ellipse_part.height": ("Mova o rato para a altura da meia elipse e clique, ou escreva-a e Enter. Esc "
                                 "cancela.", "Move the mouse for the half ellipse's height and click, or type it and "
                                 "Enter. Esc cancels."),
    "vcb.half_axis": ("Semieixo", "Half-axis"),
    "cmd.polygon": ("Polígono", "Polygon"),
    "cmd.ellipse": ("Elipse", "Ellipse"),
    "obj.ellipse": ("Elipse {n}", "Ellipse {n}"),
    "info.polygon_in": ("Polígono de {n} lados inscrito no círculo de raio {r} (os cantos no círculo). Puxe-o com "
                        "Push/Pull.", "Polygon of {n} sides inscribed in the circle of radius {r} (its corners on the "
                        "circle). Pull it with Push/Pull."),
    "info.polygon_out": ("Polígono de {n} lados circunscrito ao círculo de raio {r} (os lados tocam o círculo). "
                         "Puxe-o com Push/Pull.", "Polygon of {n} sides circumscribed about the circle of radius {r} "
                         "(its sides touch the circle). Pull it with Push/Pull."),
    "info.ellipse": ("Elipse com semieixos de {a} e {b}. Puxe-a com Push/Pull: os lados ficam uma superfície lisa.",
                     "Ellipse with half-axes of {a} and {b}. Pull it with Push/Pull: its sides become one smooth "
                     "surface."),
    "info.ellipse_part": ("Meia elipse: eixo de {a}, altura de {b}. Selecionada, os dois semieixos mudam-se pelas "
                          "cotas temporárias.", "Half ellipse: axis of {a}, height of {b}. Selected, its two half-axes "
                          "change by its temporary dimensions."),
    "info.ellipse_face": ("A meia elipse fechou o contorno: face de {a} m².",
                          "The half ellipse closed the outline: a face of {a} m²."),
    "info.ellipse_changed": ("Elipse mudada: semieixos de {a} e {b}.", "Ellipse changed: half-axes of {a} and {b}."),
    "curve.ellipse": ("Elipse", "Ellipse"),
    "props.ellipse_axis": ("Semieixo", "Half-axis"),
    "props.ellipse_minor": ("Outro semieixo", "Other half-axis"),
    # the Arc tool (0.373)
    "tool.arc": ("Arco", "Arc"),
    "cmd.arc": ("Arco", "Arc"),
    "ctx.arc_mode": ("Arco", "Arc"),
    "arcmode.two": ("2 pontos e flecha", "2 points and bulge"),
    "arcmode.centre": ("Centro e ângulo", "Centre and angle"),
    "arcmode.three": ("3 pontos", "3 points"),
    "arcmode.pie": ("Setor (face)", "Sector (face)"),
    "ctx.arc_segments": ("Segmentos", "Segments"),
    "arcseg.auto": ("automático (15°)", "automatic (15°)"),
    "vcb.bulge": ("Flecha", "Bulge"),
    "hint.arc.two0": ("Arco: clique onde começa (no chão ou numa face).",
                      "Arc: click where it starts (on the ground or on a face)."),
    "hint.arc.two1": ("Clique onde acaba, ou digite o comprimento da corda e Enter.",
                      "Click where it ends, or type the chord's length and Enter."),
    "hint.arc.two2": ("Afaste o rato para curvar (prende em meia circunferência e na tangente à linha de onde sai) e "
                      "clique, ou digite a flecha (ex.: 0,50) ou o raio (ex.: 2r) e Enter. Esc cancela.",
                      "Move the mouse to bend it (it clicks into a half circle and the tangent to the line it starts "
                      "from) and click, or type the bulge (e.g. 0.50) or the radius (e.g. 2r) and Enter. Esc cancels."),
    "hint.arc.centre0": ("Arco: clique no centro (no chão ou numa face).",
                         "Arc: click the centre (on the ground or on a face)."),
    "hint.arc.centre1": ("Clique onde o arco começa (o raio), ou digite o raio e Enter.",
                         "Click where the arc starts (its radius), or type the radius and Enter."),
    "hint.arc.centre2": ("Rode o rato até onde acaba (de 15 em 15°) e clique, ou digite o ângulo (ex.: 90) e Enter.",
                         "Turn the mouse to where it ends (15° steps) and click, or type the angle (e.g. 90) and "
                         "Enter."),
    "hint.arc.three0": ("Arco por 3 pontos: clique onde começa.", "3-point arc: click where it starts."),
    "hint.arc.three1": ("Clique num ponto por onde passa.", "Click a point it passes through."),
    "hint.arc.three2": ("Clique onde acaba.", "Click where it ends."),
    "hint.arc.pie0": ("Setor: clique no centro (no chão ou numa face).",
                      "Sector: click the centre (on the ground or on a face)."),
    "hint.arc.pie1": ("Clique onde o arco começa (o raio), ou digite o raio e Enter.",
                      "Click where the arc starts (its radius), or type the radius and Enter."),
    "hint.arc.pie2": ("Rode o rato até onde acaba e clique, ou digite o ângulo e Enter: o setor fica uma face.",
                      "Turn the mouse to where it ends and click, or type the angle and Enter: the sector is a face."),
    "snap.arc_half": ("Meia circunferência", "Half circle"),
    "snap.arc_tangent": ("Tangente à linha", "Tangent to the line"),
    "info.arc_radius": ("Raio {r}", "Radius {r}"),
    "info.arc_made": ("Arco de raio {r}, {a} ({n} segmentos). Um valor escrito logo a seguir corrige a flecha (2r: o "
                      "raio; 24s: os segmentos).",
                      "Arc of radius {r}, {a} ({n} segments). A value typed right after corrects its bulge (2r: its "
                      "radius; 24s: its segments)."),
    "info.arc_face": ("O arco fechou o contorno: face de {a} m².", "The arc closed the outline: a face of {a} m²."),
    "info.arc_pie": ("Setor de raio {r}, {a}: uma face.", "Sector of radius {r}, {a}: a face."),
    "info.arc_segments": ("Arcos com {n} segmentos.", "Arcs of {n} segments."),
    "err.arc_radius": ("O raio tem de ser pelo menos metade da corda ({r}).",
                       "The radius must be at least half the chord ({r})."),
    # freehand and Bézier curves (0.373)
    "tool.freehand": ("Linha livre", "Freehand"),
    "cmd.freehand": ("Linha livre", "Freehand"),
    "hint.freehand.start": ("Linha livre: carregue onde começa (no chão ou numa face) e arraste; solte para acabar. "
                            "Acabar onde começou fecha uma face.",
                            "Freehand: press where it starts (on the ground or on a face) and drag; let go to end. "
                            "Ending where it began closes a face."),
    "hint.freehand.drag": ("Arraste o desenho; solte para acabar (no início: fecha uma face).",
                           "Drag the drawing; let go to end (at its start: it closes a face)."),
    "info.freehand": ("Linha livre de {n} troços (escolhe-se inteira).", "Freehand line of {n} pieces (picked whole)."),
    "info.freehand_face": ("A linha livre fechou o contorno: face de {a} m².",
                           "The freehand line closed the outline: a face of {a} m²."),
    "tool.bezier": ("Curva de Bézier", "Bézier curve"),
    "cmd.bezier": ("Curva de Bézier", "Bézier curve"),
    "ctx.bezier_steps": ("Segmentos por troço", "Segments per span"),
    # (0.411, as Blender's: a click a smooth point the curve passes through; a drag its tangent by hand; Alt a corner)
    "hint.bezier.start": ("Bézier: clique nos pontos por onde a curva passa (fica suave sozinha, como no Blender). "
                          "Arrastar: puxa a tangente à mão · Alt + clique: um canto.",
                          "Bézier: click the points the curve goes through (it is smooth by itself, as in Blender). "
                          "Drag: pull the tangent by hand · Alt + click: a corner."),
    "hint.bezier.next": ("Clique no ponto seguinte (a curva passa por ele, suave) · arrastar: tangente à mão · Alt + "
                         "clique: canto. No 1.º ponto fecha uma face; Enter, Esc, botão direito ou outro clique no "
                         "último ponto acabam.",
                         "Click the next point (the curve goes through it, smooth) · drag: tangent by hand · Alt + "
                         "click: corner. On the first point it closes a face; Enter, Esc, the right button or another "
                         "click on the last point end it."),
    "hint.bezier.drag": ("Arraste a tangente; solte para fixar o ponto.", "Drag the tangent; let go to fix the point."),
    "snap.bezier_tangent": ("Tangente", "Tangent"),
    "info.bezier": ("Curva de Bézier de {n} pontos. Escolhida (Selecionar): arraste os nós, as tangentes, ou o «+» "
                    "no meio de um troço para lhe pôr um nó novo e a curvar.",
                    "Bézier curve of {n} points. Picked (Select): drag its points, its tangents, or the «+» halfway "
                    "along a span to put a new point there and bend it."),
    "info.bezier_face": ("A curva fechou o contorno: face de {a} m².", "The curve closed the outline: a face of {a} m²."),
    "hint.pp.start": ("Clique numa face para a empurrar ou puxar (numa das faces escolhidas: todas juntas).",
                      "Click a face to push or pull it (on one of the faces picked: all of them together)."),
    "hint.pp.drag": ("Mova o rato e clique, ou digite a distância (ex.: 2,80) e Enter. Esc cancela.",
                     "Move the mouse and click, or type the distance (e.g. 2.80) and Enter. Esc cancels."),
    # Ctrl: a new starting face (0.310)
    "hint.pp_solid_mode": ("+ SÓLIDO (Ctrl desliga) · ", "+ SOLID (Ctrl turns it off) · "),
    "ctx.pp_solid": ("Criar sólido (Ctrl)", "Create solid (Ctrl)"),
    "snap.pp_solid": ("Sólido", "Solid"),
    "info.pp_solid_on": ("Criar sólido: ligado — a face de partida fica onde estava, e o que sai dela é um sólido "
                         "fechado, para cima ou para baixo. Ctrl de novo desliga.",
                         "Create solid: on — the starting face stays where it was, and what comes out of it is a "
                         "closed solid, up or down. Ctrl again turns it off."),
    "info.pp_solid_off": ("Criar sólido: desligado — a face sai do sítio (empurrada para dentro, abre um rebaixo).",
                          "Create solid: off — the face moves away (pushed in, it opens a recess)."),
    "info.pp_solid": ("Sólido de {d} criado: a face de partida ficou no sítio.",
                      "Solid of {d} made: the starting face stayed in place."),
    # several faces at once (0.311)
    "snap.pp_many": ("{n} faces", "{n} faces"),
    "info.pp_many": ("{n} faces puxadas {d}, todas juntas; continuam escolhidas — outro Push/Pull leva-as outra vez.",
                     "{n} faces pulled {d}, all together; still picked — another Push/Pull takes them again."),
    "info.pp_many_solid": ("{n} faces puxadas {d} com Criar sólido: as faces de partida ficaram no sítio; as novas "
                           "ficam escolhidas.",
                           "{n} faces pulled {d} with Create solid: the starting faces stayed in place; the new ones "
                           "are picked."),
    "snap.endpoint":("Extremidade", "Endpoint"),
    "snap.midpoint": ("Ponto médio", "Midpoint"),
    "snap.origin": ("Origem", "Origin"),
    "snap.on_edge": ("Na aresta", "On edge"),
    "snap.on_face": ("Na face", "On face"),
    "snap.square": ("Quadrado", "Square"),
    "vcb.label": ("Medidas", "Measurements"),
    "vcb.dims": ("Dimensões", "Dimensions"),
    "vcb.distance": ("Distância", "Distance"),
    # messages
    "obj.name": ("Esboço {n}", "Sketch {n}"),
    "cmd.rect": ("Retângulo", "Rectangle"),
    "cmd.pp": ("Push/Pull", "Push/Pull"),
    "cmd.delete": ("Apagar", "Delete"),
    "err.no_point": ("Não há ponto de desenho aqui. Rode a vista e tente de novo.",
                     "No drawing point here. Orbit the view and try again."),
    "err.bad_value": ("Medida inválida: \"{t}\". Exemplos: 3,20   3,20;4,50   320cm",
                      "Invalid value: \"{t}\". Examples: 3.20   3.20;4.50   320cm"),
    "err.nothing_to_adjust": ("Não há nada a ajustar com esta medida.", "Nothing to adjust with this value."),
    "info.rect": ("Retângulo {a} × {b} criado.", "Rectangle {a} × {b} created."),
    "info.pp": ("Push/Pull de {d}.", "Push/Pull of {d}."),
    "warn.clamped": ("Push/Pull limitado a {d} para não inverter o volume.",
                     "Push/Pull limited to {d} so the volume does not turn inside out."),
    "help.text": (                    # (0.327: the Help window's «Keys»; the menus' paths gone with the menus, 0.182)
        "Navegação\n"
        "  Botão do meio + arrastar: orbitar · Shift + botão do meio: deslocar (ao contrário: Visualizar ▸ Rato)\n"
        "  Roda do rato: zoom para onde aponta o cursor · Shift+Z: enquadrar tudo · Shift+F: enquadrar a seleção\n"
        "  F8: 3D · F2: topo · F3: frente · F4: planta do pavimento ativo · F5: último corte\n"
        "  F6: caixa de corte (Shift+F6: à volta da seleção) · PgUp / PgDn: pavimento acima / abaixo\n"
        "  Abas por cima da vista: uma por vista aberta · Ctrl+W fecha a vista · Ctrl+Tab: a seguinte\n"
        "  O cubo de vistas (canto de cima, à direita): clique numa face, aresta ou canto; arraste para orbitar\n\n"
        "Selecionar e editar\n"
        "  Espaço: Selecionar · arrastar para a direita: o que fica dentro · para a esquerda: o que toca\n"
        "  Shift + clique: juntar ou tirar · Ctrl+A: tudo · Esc: largar · Delete: apagar\n"
        "  Uma linha: um clique, só ela; dois, a cadeia; três, tudo o que lhe está ligado (um arco: inteiro)\n"
        "  Ctrl+Z / Ctrl+Y: desfazer / refazer\n"
        "  Ctrl+C: copiar · Ctrl+V: colar onde clicar · Ctrl+Shift+V: colar noutros pavimentos\n"
        "  Quando um comando pede elementos (balão verde): um clique junta ou tira; Enter ou botão direito\n"
        "  continuam; Esc desiste\n\n"
        "Ferramentas com tecla\n"
        "  L: Linha · A: Arco · R: Retângulo · P: Push/Pull · F: Offset · M: Mover · Q: Rodar · T: Fita métrica\n"
        "  C: Cota\n"
        "  W: Parede · D: Porta · J: Janela · G: criar componente · Ctrl+G: criar grupo\n"
        "  O: Orbitar · H: Deslocar · Z: Zoom · Ctrl+T: Tabelas · Ctrl+P: PDF da vista · F1: esta ajuda\n"
        "  Ctrl+1 … Ctrl+9: os separadores da fita (Modelagem, Arquitetura, Estrutura … Terreno); as teclas funcionam "
        "em todos\n\n"
        "Nas ferramentas de colocação (pilar, porta, louça, móvel…)\n"
        "  R / Shift+R: rodar 90° · Espaço: outro ponto de inserção · F: inverter · X / Y: só nesse eixo\n"
        "  Tab: muda a opção da ferramenta (a linha de referência da parede, a forma da laje…)\n\n"
        "Medidas: escreva a qualquer momento e carregue em Enter\n"
        "  3,20 · 3,20;4,50 · 320cm · 3200mm — depois de terminar, outra medida + Enter corrige a última\n"
        "  Copiar / Matriz: depois de uma cópia, 3x = mais 3 iguais, /3 = dividir em 3\n\n"
        "Inferências (o cursor agarra-se sozinho)\n"
        "  verde: extremidade · azul-claro: ponto médio · vermelho: na aresta · azul: na face\n"
        "  amarelo: origem · magenta: esquadria · cinzento: na guia · eixos vermelho / verde / azul\n\n"
        "Onde está cada coisa: separador «Procurar» deste painel (escreva o nome).",
        "Navigation\n"
        "  Middle button + drag: orbit · Shift + middle button: pan (the other way round: View ▸ Mouse)\n"
        "  Mouse wheel: zoom towards the cursor · Shift+Z: zoom extents · Shift+F: zoom to the selection\n"
        "  F8: 3D · F2: top · F3: front · F4: plan of the active storey · F5: last section\n"
        "  F6: section box (Shift+F6: round the selection) · PgUp / PgDn: storey above / below\n"
        "  Tabs over the view: one per open view · Ctrl+W closes the view · Ctrl+Tab: the next one\n"
        "  The view cube (top right corner): click a face, edge or corner; drag to orbit\n\n"
        "Selecting and editing\n"
        "  Space: Select · drag to the right: what is inside · to the left: what it touches\n"
        "  Shift + click: add or remove · Ctrl+A: all · Esc: let go · Delete: delete\n"
        "  A line: one click, just it; two, its chain; three, all joined to it (an arc: whole)\n"
        "  Ctrl+Z / Ctrl+Y: undo / redo\n"
        "  Ctrl+C: copy · Ctrl+V: paste where you click · Ctrl+Shift+V: paste on other storeys\n"
        "  When a command asks for elements (green balloon): a click adds or removes; Enter or the right button\n"
        "  go on; Esc gives up\n\n"
        "Tools with a key\n"
        "  L: Line · A: Arc · R: Rectangle · P: Push/Pull · F: Offset · M: Move · Q: Rotate · T: Tape measure\n"
        "  C: Dimension\n"
        "  W: Wall · D: Door · J: Window · G: make component · Ctrl+G: make group\n"
        "  O: Orbit · H: Pan · Z: Zoom · Ctrl+T: Schedules · Ctrl+P: the view's PDF · F1: this help\n"
        "  Ctrl+1 … Ctrl+9: the ribbon's tabs (Modelling, Architecture, Structure … Terrain); the keys work in all of "
        "them\n\n"
        "In the placing tools (column, door, fixture, cabinet…)\n"
        "  R / Shift+R: turn 90° · Space: another insertion point · F: flip · X / Y: only along that axis\n"
        "  Tab: changes the tool's option (the wall's reference line, the slab's shape…)\n\n"
        "Measurements: type at any time and press Enter\n"
        "  3.20 · 3.20;4.50 · 320cm · 3200mm — after finishing, another value + Enter corrects the last one\n"
        "  Copy / Array: after a copy, 3x = 3 more alike, /3 = split in 3\n\n"
        "Inferences (the cursor snaps by itself)\n"
        "  green: endpoint · cyan: midpoint · red: on edge · blue: on face\n"
        "  yellow: origin · magenta: square · grey: on guide · red / green / blue axes\n\n"
        "Where each thing is: this panel's «Find» tab (type its name)."),
}

from .verify.texts import STRINGS as _VERIFY_STRINGS  # noqa: E402  (0.416: the Verifier's own texts)
_STRINGS.update(_VERIFY_STRINGS)


def set_language(lang):
    global _LANG
    _LANG = "pt" if lang.lower().startswith("pt") else "en"


def lang():
    return _LANG


def t(key, **kwargs):
    pt, en = _STRINGS[key]
    s = pt if _LANG == "pt" else en
    return s.format(**kwargs) if kwargs else s


def has(key):
    """(0.182) Whether there is a text for this key (the ribbon's short names are only for some buttons)."""
    return key in _STRINGS


def refusal(exc):
    """Readable reason for an edit the model refused (exceptions carry a `code`)."""
    code = getattr(exc, "code", None) or ("not_editable" if type(exc).__name__ == "NotEditable" else None)
    return t("refuse." + code) if code and ("refuse." + code) in _STRINGS else str(exc)


def decimal_sep():
    return "," if _LANG == "pt" else "."


_IDS_REASONS = (       # ifctester's reasons (English) -> Portuguese; {0}, {1}: what it found
    (r'The entity class "(.*)" does not meet the required IFC class', 'A classe "{0}" não é a pedida'),
    (r'The predefined type "(.*)" does not meet the required type', 'O tipo predefinido "{0}" não é o pedido'),
    (r"The required attribute did not exist", "Falta o atributo pedido"),
    (r'The attribute value "(.*)" is empty', 'O atributo está vazio ("{0}")'),
    (r"An invalid attribute name was specified in the IDS", "O IDS pede um atributo que o IFC não tem"),
    (r'The attribute value "(.*)" does not match the requirement', 'O atributo vale "{0}", que não é o pedido'),
    (r"The attribute value should not have met the requirement", "O atributo não devia estar assim (é proibido)"),
    (r"The entity has no classification", "Não tem classificação"),
    (r'The references "(.*)" do not match the requirements', 'A classificação "{0}" não é a pedida'),
    (r'The systems "(.*)" do not match the requirements', 'O sistema de classificação "{0}" não é o pedido'),
    (r"The classification should not have met the requirement", "A classificação é proibida"),
    (r"The entity has no relationship", "Não faz parte do que é pedido (relação em falta)"),
    (r'The entity has a relationship with incorrect entities: "(.*)"', 'Faz parte de outro elemento: "{0}"'),
    (r'The entity has a relationship with incorrect predefined type: "(.*)"',
     'Faz parte de um elemento de outro tipo: "{0}"'),
    (r"The relationship should not have met the requirement", "Esta relação é proibida"),
    (r"The required property set does not exist", "Falta o conjunto de propriedades pedido"),
    (r"The property set does not contain the required property", "Falta a propriedade pedida no conjunto"),
    (r'The property\'s data type "(.*)" does not match the required data type of "(.*)"',
     'A propriedade é do tipo "{0}" e devia ser "{1}"'),
    (r'The property values? "(.*)" (?:does|do) not match the requirements', 'A propriedade vale "{0}", que não é o pedido'),
    (r"The property should not have met the requirement", "Esta propriedade é proibida"),
    (r"The entity has no material", "Não tem material"),
    (r'The material names and categories of "(.*)" does not match the requirement', 'O material "{0}" não é o pedido'),
    (r"The material should not have met the requirement", "Este material é proibido"),
)


def ids_reason(text):
    """Why an element fails an IDS requirement, in the program's language (ifctester says it in English)."""
    if _LANG != "pt":
        return text
    import re
    for pattern, pt in _IDS_REASONS:
        m = re.fullmatch(pattern, text.strip())
        if m:
            return pt.format(*m.groups())
    return text
