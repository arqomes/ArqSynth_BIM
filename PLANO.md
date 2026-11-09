# Plano de desenvolvimento — ArqSynth BIM

Versão do plano: 2026-10-22, feito a partir do levantamento do **ArqSynth Modeler 1.1.0** (o addon para Blender) e do
estado do programa na **0.76**. Substitui a lista «Próximos passos» da ARQUITETURA.md como roteiro; a ARQUITETURA
continua a guardar as decisões técnicas.

## 1. Ponto de partida

**ArqSynth BIM** (até à 0.76 chamava-se ArqBIM) é um programa independente, com janela própria, que trabalha
diretamente em IFC. O ArqSynth Modeler é a mesma marca dentro do Blender: tem muitas mais ferramentas, mas com a
interface e os limites do Blender. O plano traz para o ArqSynth BIM o que o addon faz, com quatro regras que se
mantêm:

1. **IFC nativo e sempre válido** — cada ferramenta nova diz em que classe IFC grava (indicado entre parêntesis).
2. **Comportamento do Revit** — snaps, cotas temporárias e propriedades visíveis; as ligações nunca se partem; o
   que está ligado acompanha.
3. **Passos pequenos e testáveis** — cada passo é uma versão, com testes automáticos e passos de teste numerados
   para o dono do projeto.
4. **O addon é a referência de funções e de fluxos, não de interface** — não se copiam o «header», os painéis e o
   T-panel do Blender; copia-se o que eles fazem.

### O que o addon ensina, e se adota

- **Quatro ambientes de trabalho:** Conceito, BIM, Estrutura e Docs. Cada um tem as suas ferramentas.
- **Barra contextual:** muda com o ambiente, com a ferramenta e **com o que está selecionado**. Por exemplo: eixos
  selecionados → «Inserir pilares»; pilares selecionados → «Sapatas» e «Vigas»; vigas fechadas → «Inserir lajes».
- **Um contrato igual para todas as ferramentas:**
  - o primeiro clique começa;
  - a barra de estado diz o passo seguinte;
  - ESC ou o botão direito sai; ENTER confirma;
  - medidas escritas (VCB);
  - teclas comuns: R / Shift+R roda ±90°, Espaço / Shift+Espaço muda o ponto de inserção, F inverte, X / Y / N
    bloqueia o eixo, Shift dá ortogonal temporário.
- **Pisos tipo («equalizados», =):** o que se desenha num piso repete-se nos pisos iguais e acompanha as edições.
- **Automações:** pilares na grelha, sapatas sob pilares, vigas entre pilares, lajes nos vãos das vigas,
  propostas completas de estrutura, elétrica, abastecimento e drenagem.

### Onde o ArqSynth BIM deve ser melhor do que o addon

O próprio levantamento lista estes limites do addon (secção 5). No ArqSynth BIM devem ficar resolvidos:

| No addon | No ArqSynth BIM |
|---|---|
| Mover um pilar não leva a sapata nem as vigas | A sapata e as vigas acompanham o pilar (como as paredes ligadas, 0.71) |
| Mudar a grelha não mexe nos pilares | Os pilares presos a um cruzamento seguem os eixos |
| Mudar as vigas não refaz a laje | A laje feita a partir das vigas refaz-se |
| «Pilares na grelha» só com eixos selecionados | Também «em todos os cruzamentos», num clique |
| Dados nos objetos do Blender | Tudo no IFC, que o Revit e os outros programas abrem |

## 2. O que já existe e o que falta (0.76 × addon)

| Família | Já existe no ArqSynth BIM | Falta (vem do addon) |
|---|---|---|
| Conceito / modelação | Linha, Retângulo, Push/Pull, Mover, Rodar, cópias e séries, Fita métrica, componentes, grupos, Classificar volumes em BIM | Círculo, arco, offset, espelho, escala; imagem de fundo calibrada; volumetria por primitivas |
| Paredes | Desenho em cadeia, junções L/T e meia-esquadria, referência eixo/faces, camadas, ligações mantidas, restrições de base e topo, Push/Pull paramétrico | Retângulo, arco, círculo; parede a partir de face; varinha mágica; dividir, juntar/separar, aparar, estender, alinhar, espelhar, ortogonalizar; perfil; ligar o topo à cobertura; **editor de tipos**; fachada de vidro |
| Pisos e lajes | Laje retangular, vãos e nichos | Por polígono, círculo e varinha mágica; editar o contorno; função (estrutural / acabamento / excluída); rampas; editor de tipos |
| Coberturas | — | Plana a partir de piso; por paredes (águas); por esboço; extrusão; camadas e aberturas; mais tarde orgânicas, madeiramento e telhas |
| Escadas e guarda-corpos | — | Reta, L, U, V, circular; guarda-corpo por caminho, vão ou vazio |
| Vãos | Portas e janelas (5 tipos), vãos vazios, mover, virar, copiar | Editor de tipos, kits de vãos, numeração, orientação |
| Tetos e revestimentos | — | Teto por sala ou contorno, sancas, rasgos, luminárias; revestimentos em camadas |
| Salas | — | Espaços com área, nome e acabamentos; varinha mágica |
| Estrutura | Grelha (desenho, gerador, edição), pilares, vigas, sapatas isoladas e corridas | Automações; pilares circulares, L e T com 9 pontos de inserção; sistemas de vigas; radier, estaca, bloco; proposta de estrutura; modelo analítico; cálculo pelos Eurocódigos; armaduras; desenhos estruturais |
| Instalações | Tubos e condutas, curvas, portas IFC | Inclinação, tês, reduções, quedas verticais; terminais e equipamentos com conectores; elétrica toda; propostas automáticas; cálculo de redes |
| Mobiliário e equipamento | Componentes e biblioteca entre projetos | Mobiliário paramétrico (cozinhas, divisões, fachadas, lista de corte); equipamentos com conectores |
| Docs | Plantas, cortes e alçados ao vivo; propriedades e modelos de vista; cotas e cotas automáticas de paredes; folhas com legenda; PDF vetorial; tabelas (CSV); regras gráficas | Desenho 2D (linha, região, trama, texto), símbolos, chamadas, marcas de nível; cotas em cadeia e angulares; salas com etiqueta; estilos de linha e trama; revisões e modelos de folha; exportar PNG/SVG/DXF; tabelas com fórmulas |
| Coordenação | IDS, notas BCF, verificação para certificação, trabalho em equipa | Deteção de conflitos entre disciplinas, com relatório |
| Importação | IFC de outros programas | DXF → modelo; nuvem de pontos → BIM; topografia por pontos/DXF |
| Seleção / navegação | Seleção completa (0.75–0.76); órbita, pan, zoom ao cursor, vistas, caixa de corte | Cubo de vistas, zoom janela, vista anterior, caminhar, … (Fase 1) |

## 3. Decisões do dono do projeto (2026-10-22)

| # | Decisão | Escolha |
|---|---|---|
| 1 | Nome guardado nos ficheiros | **Mudar e continuar a ler os antigos** |
| 2 | Tecla Espaço | **As duas:** dentro das ferramentas de colocação muda o ponto de inserção; fora delas é Selecionar |
| 3 | Código do addon | **Aproveitar a lógica sem Blender** — a fonte é `D:\Nova pasta\arqsynth_modeler (2).zip` (é a 1.1.0, de 17-08-2026) |
| 4 | Ordem das fases | **Como abaixo** (Navegação primeiro) |
| 5 | Esquema do rato | a decidir na Fase 1 |

O texto de cada decisão, como foi posto:

1. **Nome guardado nos ficheiros.** Na 0.77 mudou só o que se vê. Nos dados continua «ArqBIM»:
   - o conjunto de propriedades `ArqBIM_Parametros` dentro do IFC, que o Revit mostra;
   - a extensão `.arqbim` do ficheiro que acompanha o IFC;
   - as pastas de trabalho.

   Proposta: gravar com o nome novo e continuar a ler os antigos, para os projetos existentes abrirem sem perder
   nada.
2. **A tecla Espaço.** No addon, Espaço muda o ponto de inserção; no ArqSynth BIM, Espaço ativa a ferramenta
   Selecionar (como no SketchUp). Proposta: dentro das ferramentas de colocação (pilar, sapata, porta, componente),
   Espaço muda o ponto de inserção; fora delas continua a ser Selecionar.
3. **Reaproveitar código do addon.** No ZIP antigo (`D:\Nova pasta\arqsynth_modeler (2).zip`), só cerca de 0,5 MB
   dos 6,6 MB de Python não dependem do Blender: dá para aproveitar algoritmos (cálculo, propostas, tolerâncias),
   não ferramentas inteiras. É preciso saber:
   - onde está a pasta da versão 1.1.0;
   - a licença: o código do addon é do dono do projeto e pode ser reutilizado; o código de terceiros que lá vem
     (ezdxf, fontTools, pyparsing) é MIT e também pode. O código escrito para o Blender (bpy) só serve de
     referência.
4. **A ordem das fases** — a recomendada está abaixo.
5. **O esquema do rato na navegação** (Fase 1). Hoje é como no SketchUp: o botão do meio orbita, Shift + botão do
   meio desloca. No Revit é o contrário. Proposta: as duas opções, à escolha nas preferências.

## 4. Fases (ordem recomendada)

Cada passo é uma versão: testes automáticos, registo no CHANGELOG e passos de teste numerados para o dono do
projeto. Os tamanhos são relativos: P (um ou dois dias de trabalho meu), M (alguns), G (várias versões).

### Fase 0 — Marca (P)
1. ~~Nome visível «ArqSynth BIM»~~ (feito, 0.77.0): janela, mensagens, PDF, cabeçalho do IFC, «ArqSynth BIM.bat».
2. ~~Nome nos ficheiros, com leitura dos antigos~~ (feito, 0.77.0): `ArqSynth_Parametros`, `.arqsynthbim`,
   pasta «ArqSynth BIM».
3. ~~Ícone e ecrã de arranque da marca~~ (feito, 0.82.0): o símbolo de www.arqsynth.com. O nome definitivo do
   programa BIM está por decidir (o dono vai mudá-lo; até lá, «ArqSynth BIM»).

### Fase 1 — Navegação (M)
1. ~~**Comandos de zoom**~~ (feito, 0.78.0): zoom janela, enquadrar a seleção, enquadrar tudo; vista anterior e
   seguinte; duplo clique do botão do meio enquadra tudo.
2. ~~**Cubo de vistas**~~ (feito, 0.79.0; como o do Revit, 0.81.0): faces, arestas e cantos clicáveis e realçados;
   anel com N, E, S, O; triângulos para a face ao lado; rodar 90°; arrastar orbita; casa e vista inicial; menu ▾.
3. ~~**Ferramentas de navegação**~~ (feito, 0.78.0): Orbitar (O), Deslocar (H), Zoom (Z); o botão do meio como no
   SketchUp ou no Revit, à escolha (Vista ▸ Navegação) — decisão 5 resolvida assim.
4. ~~**Órbita**~~ à volta do ponto sob o cursor (já existia); enquadrar o que está selecionado: Shift+F (0.78.0).
5. ~~**Caminhar e olhar em volta**~~ (feito, 0.80.0), com a altura dos olhos e a câmara posta num ponto; sem
   atravessar paredes, as portas atravessam-se, Alt atravessa tudo (0.83.0).
6. ~~**Plantas e cortes**~~ só com deslocar e zoom (já existia; a ferramenta Orbitar também só desloca, 0.78.0).
7. **Desempenho em modelos grandes:** ~~o motor de geometria noutro processo~~ (0.283.0: medido com o dono — não
   compensa: as mesmas pausas e o mesmo tempo, mais metade da memória). Fica por fazer, no próprio processo: a
   reabertura (2,7 s no grande, ≈ 30 s para 500 MB), ~~as pausas da janela ao abrir (até 1,4 s: a 1.ª imagem — 0,4 s a
   juntar os lotes, que pode ir para a tarefa de fundo, e 0,5 s a enviar para a placa)~~ (0.328.0: os lotes feitos
   aos poucos, uns por imagem, e a leitura à espera deles — a maior pausa ao abrir pela 1.ª vez 838 → 464 ms e ao
   reabrir 1448 → 317 ms; ficou na tarefa da janela, porque os objetos da placa não se fazem com segurança noutra
   tarefa). Continua por fazer: reabrir 500 MB (≈ 20 s, no limite da meta) — sobretudo ler o IFC e pôr os elementos
   no documento. e ~~mudar um grupo com 1000
   cópias (8 s)~~ (0.287.0: 2,75 s).

### Fase 2 — Base do ambiente de trabalho (M)
1. ~~**Ambientes** Conceito / BIM / Estrutura / Docs~~ (feito, 0.84.0): a barra lateral mostra as ferramentas do
   ambiente; separadores no topo; Ctrl+1…4.
2. ~~**Barra contextual**~~ (feito, 0.85.0): a barra de Seleção da 0.75 passa a mudar com a ferramenta e com a
   seleção — as opções da ferramenta (tipo, altura, linha de referência, pavimento) e os botões da seleção (os
   automáticos chegam com a Fase 3; o ponto de inserção, com as teclas comuns).
3. ~~**Teclas comuns**~~ (feito, 0.86.0) nas ferramentas de colocação: R / Shift+R, F, X / Y / N, Shift, ponto de
   inserção com Espaço (decisão 2); Esc volta a Selecionar.
4. **Editor de tipos** (fundamental): criar, duplicar e editar tipos de parede, piso, cobertura, pilar, viga,
   porta e janela — camadas, materiais, perfis. Os tipos vivem no IFC (`IfcWallType`… com
   `IfcMaterialLayerSet` / `ProfileSet`); o catálogo atual fica como ponto de partida.
   - ~~Paredes, lajes, pilares, vigas, sapatas, tubos e condutas~~ (feito, 0.87.0).
   - ~~Portas e janelas~~ (feito, 0.88.0); ~~coberturas quando houver coberturas (Fase 4)~~ (0.278.0: tipos de
     cobertura, `IfcRoofType`).
5. ~~**Materiais:**~~ (feito, 0.89.0) biblioteca com cor, trama e propriedades físicas (`IfcMaterial` +
   `Pset_Material…`).
6. ~~**Pisos tipo (equalizados):**~~ (feito, 0.90.0) marcar pisos iguais; o que se desenha num repete-se nos
   outros e acompanha as edições (por grupos, automático por piso). **Fase 2 completa.**

### Fase 3 — Estrutura automática (M) — o fluxo principal do levantamento
1. ~~**Grelha:**~~ (feito, 0.91.0) esquema de etiquetas (numérico ou alfabético por direção), renumerar, cotas
   entre eixos, tamanho da bolha. O gerador já existe.
2. ~~**Pilares na grelha:**~~ (feito, 0.92.0) nos cruzamentos dos eixos selecionados (X × Y), ou em todos. O
   pilar fica preso ao cruzamento e segue os eixos (melhor do que o addon).
3. ~~**Sapatas:**~~ (feito, 0.93.0) sob os pilares selecionados, sob todos, ou por ponto; tipos isolada, corrida,
   bloco sobre estacas (1, 2, 4), radier (dois cantos) e estaca (`IfcFooting`, `IfcPile`). A sapata segue o pilar.
   ~~Falta: a sapata combinada (sob dois pilares)~~ (0.249.0; a verificação EC2 e as armaduras: 0.250.0).
4. ~~**Vigas entre pilares:**~~ (feito, 0.94.0) pilares em linha em X ou Y, só vizinhos, recuadas às faces dos
   pilares, topo no topo do pilar, com tolerância. As vigas seguem os pilares. (A viga com o centro ou a base no
   topo do pilar: muda-se depois o «topo» da viga, no painel.)
5. ~~**Paredes entre pilares e sob as vigas**~~ (feito, 0.95.0), presas às vigas.
6. ~~**Lajes nos vãos das vigas:**~~ (feito, 0.96.0) contornos fechados encontrados nas vigas, laje entre as faces
   interiores; a laje refaz-se quando as vigas mudam. Só vãos retangulares até haver lajes de polígono (Fase 4).
7. ~~**Pilares e vigas mais completos:**~~ (feito, 0.86.0 e 0.97.0) secções retangular, circular, L e T; 9 pontos
   de inserção; rotação; sistemas de vigas (grelha ou paralelas, por número ou espaçamento).
8. ~~**Propor estrutura a partir das paredes:**~~ (feito, 0.98.0) pilares nos cantos e cruzamentos, intermédios
   pelo vão máximo, vigas, sapatas; refazer e remover a proposta. **Fase 3 completa** (~~falta a sapata combinada~~ (0.249.0)).

### Fase 4 — Arquitetura essencial (G)
1. ~~**Salas**~~ (feito, 0.99.0) (`IfcSpace`): por clique dentro de paredes (varinha mágica), nome, número, área,
   acabamentos; acompanham as paredes. São a base das etiquetas, dos quadros de áreas e das propostas automáticas.
2. ~~**Pisos e lajes:**~~ (feito, 0.100.0 e 0.101.0) por polígono, círculo e varinha mágica; editar o contorno;
   função estrutural / acabamento / excluída; rampas (`IfcSlab`, `IfcRamp`). (As rampas com patamares e
   lanços, `IfcRampFlight`, vêm com as escadas, passo 6.)
3. ~~**Paredes:**~~ (feito, 0.102.0 a 0.109.0)
   - criar por ~~retângulo, arco, círculo, a partir de uma face, ou pela varinha mágica~~ (feito, 0.102.0 e 0.103.0:
     a face de uma laje ou de um esboço; as curvas ~~sem cantos~~ — 0.189.0: cantos exatos com paredes retas e
     curvas, ponta com ponta —, ~~nem vãos~~ — 0.177.0: portas e janelas). Fica para depois: ~~uma parede a encontrar
     uma curva a meio (em T)~~ (0.246.0);
   - ~~editar: dividir, juntar e separar, aparar o canto, estender, alinhar, espelhar, ortogonalizar~~ (feito,
     0.104.0 a 0.108.0);
   - ~~ligar o topo a uma laje ou cobertura~~ (feito, 0.106.0 e 0.112.0);
   - ~~editar o perfil~~ (feito, 0.109.0).
4. **Vãos:** ~~tipos editáveis~~ (0.88.0), ~~kits (porta + bandeira…), numeração~~ (0.110.0), ~~orientação~~
   (0.86.0, F e o painel), ~~vão sem caixilho~~ (0.110.0) (`IfcDoorType`, `IfcWindowType`).
5. **Coberturas:** ~~plana a partir de um piso (com ralos)~~ (0.113.0); ~~por paredes (águas, beirados)~~
   (0.111.0, contornos convexos; 0.112.0: as paredes e pilares sob ela); ~~por esboço~~ (0.113.0: uma face); ~~por
   extrusão~~ (0.180.0: abóbada e borboleta); ~~camadas~~ (as do tipo); ~~aberturas~~ (0.113.0) (`IfcRoof`; no
   programa, com corpo próprio). ~~Os contornos com cantos para dentro~~ (0.179.0: quatro águas sobre contornos em
   esquadria — L, T, U; ~~os de lados oblíquos~~ — 0.190.0: o esqueleto reto, sobre qualquer contorno). Fica para
   depois: ~~um perfil de extrusão desenhado pelo utilizador~~ (0.251.0); ~~duas águas sobre um contorno com cantos para dentro~~ (0.247.0).
6. ~~**Escadas** reta, L, U, V e circular, com patamares, e **guarda-corpos** por caminho, num vão ou num vazio~~
   (feito, 0.114.0 a 0.116.0; também nos lados das escadas; 0.256.0: a laje sob os degraus, medida ao canto interior; 0.257.0: patamar e lanços numa peça, sem linhas a mais) (`IfcStair`, `IfcRailing`).
7. **Fachada de vidro:** ~~grelha de montantes e travessas~~ (0.117.0), ~~tipos de painel~~ (`IfcCurtainWall`; no
   programa, com corpo próprio). ~~Os tipos de painel por célula~~ (0.181.0: vidro, opaco, porta, vazio). ~~Embutir
   numa parede~~ (0.188.0: abre o seu vão e vai com a parede, como uma porta). Fica para depois: ~~embutir numa
   parede curva~~ (0.252.0).
8. ~~**Tetos e revestimentos:** teto por sala ou contorno, grelha de placas~~ (0.118.0), ~~sanca, rasgo,
   luminárias; revestimentos de parede~~ (0.119.0: azulejo, reboco ou pedra numa face, até uma altura, recortados
   nos vãos e a acompanhar a parede) (`IfcCovering`, `IfcLightFixture`). ~~Falta: várias camadas na mesma face~~
   (0.178.0).
   **Fase 4 completa** (faltam os restos anotados nos passos 3, 5 e 7: ~~o T com uma curva~~ (0.246.0), ~~o perfil desenhado~~ (0.251.0) ~~e as
   duas águas com cantos para dentro~~ (0.247.0) nas coberturas, ~~a fachada numa parede curva~~ (0.252.0): todos
   feitos).

### Fase 5 — Documentação (G)
1. ~~**Desenho 2D nas vistas:** linha, polilinha, retângulo, círculo, arco, região com trama, texto~~ (0.120.0;
   guardado com as cotas, fora do IFC — `IfcAnnotation` pode vir como exportação). ~~Editar os pontos com pegas,
   mudar o texto e rodar~~ (0.191.0; o Rodar só nas plantas).
2. **Símbolos e anotações:** ~~chamadas de corte e alçado; marcas de nível nos cortes; norte~~ (0.121.0:
   calculados do modelo, duplo clique abre a vista); ~~chamadas de detalhe~~ (0.133.0, com as vistas de detalhe);
   ~~marcas de nível em planta~~ (0.192.0); ~~keynotes~~ (0.194.0: notas-chave no tipo, etiquetas e legenda).
   Fica para depois: ~~a tabela de notas-chave própria do projeto (hoje a do programa)~~ (0.248.0).
3. ~~**Cotas:** em cadeia e angulares~~ (0.122.0); ~~estilos~~ (0.124.0: um estilo do projeto); ~~cotas
   automáticas de fachada e de interiores~~ (0.123.0; as das paredes já existiam). ~~Tipos de cota por cota~~
   (0.193.0).
4. ~~**Salas no papel:** etiquetas, áreas, quadro de áreas e de acabamentos~~ (0.125.0; os quadros nas folhas
   vêm com as tabelas nas folhas, passo 7).
5. ~~**Estilos gráficos:** tipos de linha, tramas, como cada material se desenha~~ (0.126.0: por tipo de material,
   as canetas; os tipos de linha no desenho 2D).
6. ~~**Folhas:** modelos~~ (0.130.0: da legenda — completa, compacta, faixa lateral), ~~assistente de folhas
   por piso, revisões, campos próprios, numeração~~ (0.127.0), ~~conjuntos, publicação; exportar PNG, SVG~~
   (0.128.0) ~~e DXF~~ (0.129.0: de uma vista) (o PDF já existe); ~~imprimir~~ (0.128.0). ~~Os comandos da folha
   na barra de parâmetros, importar DWG/DXF/imagem/SVG para a folha e editar o carimbo da empresa~~ (0.472.0, pedido
   do dono com captura); ~~o carimbo desenhado na própria folha, com linhas, retângulos, textos, imagens e campos~~
   (0.473.0, o dono: «maior liberdade criativa»).
7. ~~**Tabelas:** editor com campos, fórmulas, filtros e modelos~~ (0.131.0: tabelas próprias do projeto,
   guardadas com nome); ~~tabelas nas folhas~~ (0.132.0).
   **Tabelas como no Revit e no Excel** (pedido do dono, 2026-11-08: «a tabela deve ser gerada na tela… algo
   abrangente para criar quantificação, exportar… para o KazaFix Cost… em células como no excel… guardável no arquivo
   base»), por fases:
   1. ~~O painel lateral «Tabelas» com a árvore de todas; cada tabela numa aba na tela; os comandos na barra de
      parâmetros; Propriedades como no Revit (Campos disponíveis ↔ tabelados, Filtro, Classificar/Agrupar); exportar
      JSON para o KazaFix Cost~~ (0.477.0).
   2. ~~Células como no Excel: unir células, alinhamento, bordas, fórmulas (=SOMA(C2:C9)…), linhas e células livres
      (títulos, notas); inserir campos e fórmulas numa célula com o botão direito ou pelo painel~~ (0.478.0: também
      a cor de fundo, negrito e itálico, os dados do projeto num texto, a grelha exportada para o Excel com as fórmulas
      e posta na folha). Restos: copiar e colar células (Ctrl+C / Ctrl+V); mais funções (SE.ERRO, CONTAR.SE, SOMA.SE…);
      tamanho e cor da letra por célula (na fase 3).
   3. Formatação e Aparência como no Revit: nome de cada coluna, unidades e casas decimais por campo, totais por campo,
      cabeçalhos e rodapés de grupo, totais gerais, «cada instância», grelha e letra.
   4. Mais tabelas: lista de vistas, lista de folhas, mapa de vãos (portas e janelas juntas), materiais (quantidades
      por camada e material), áreas (implantação, construção, útil), elementos de várias categorias.
   5. As tabelas no modelo base (arquivo base) e na biblioteca do escritório, para os outros projetos; importar as
      tabelas de outro projeto.
8. ~~**Vistas:** alçados cardinais automáticos~~ (já existiam desde a 0.29.0), ~~vistas de detalhe~~
   (0.133.0: pormenores com chamada), ~~vistas 3D nas folhas~~ (0.134.0: em linhas, axonometria).
   **Fase 5 completa** (faltam os restos anotados nos passos 1, 2 e 3).

### Fase 6 — Instalações (G)
~~(Primeiro: perceber porque a conduta do teste do dono do projeto não apareceu.)~~ (0.135.0: ficava acima do corte da planta; agora vê-se a tracejado.)
1. **Água e esgoto:** ~~inclinação, tubo de queda~~ (0.136.0), ~~ramais e coletor; tês, reduções~~ (0.137.0) e ~~subidas com curvas verticais~~ (0.136.0). Restos: ~~um ramal a outra altura do principal ainda não desce sozinho até ele~~ (0.195.0: desce na vertical, com o tê); ~~tês de 45° com forma de Y~~ (0.200.0: forquilhas nos ramais de esgoto).
2. ~~**AVAC:** condutas redondas e retangulares, terminais~~ (0.138.0) ~~e equipamentos (`IfcAirTerminal`, `IfcUnitaryEquipment`)~~ (0.139.0). Restos: ~~tubagem de refrigerante~~ (0.196.0); ~~curvas de conduta em S quando a descida não cabe~~ (0.197.0).
3. **Equipamentos com conectores** (~~água, esgoto~~ (0.140.0: louças), gás, elétrica, ~~AVAC~~ (0.139.0)):
   ~~ligar à rede, ramal automático~~ (0.142.0: água e esgoto), ~~zonas livres~~ (0.140.0). Sistemas com cores (0.141.0). Restos: ~~gás e elétrica (no passo 4)~~ (0.198.0: aparelhos ligados à rede de gás, alimentação e circuitos); ~~o ramal ainda não contorna obstáculos~~ (0.199.0: pilares e sapatas isoladas, curvas em esquadria).
4. **Elétrica:**
   - ~~pontos: tomadas, interruptores, luminárias, caixas, quadros~~ (0.143.0; as luminárias desde a 0.119.0);
   - ~~perfis por tipo de sala~~ (0.145.0);
   - ~~opções de iluminação, tomadas e interruptores, com pré-visualização~~ (0.145.0);
   - ~~circuitos e cálculo~~ (0.144.0; e o quadro de cargas);
   - ~~canalizações e ligação ao quadro~~ (0.146.0);
   - ~~validação, quadro de cargas e quantidades~~ (0.147.0; o quadro de cargas na 0.144.0). **Passo 4 completo.**

   Classes IFC: `IfcOutlet`, `IfcSwitchingDevice`, `IfcLightFixture`, `IfcElectricDistributionBoard`,
   `IfcJunctionBox`, `IfcCableCarrierSegment`, `IfcDistributionCircuit`.
5. ~~**Propostas automáticas** de abastecimento, drenagem e elétrica a partir das salas e dos aparelhos (removíveis)~~ (0.145.0 elétrica, 0.148.0 águas e esgotos).
6. ~~**Coordenação:** deteção de conflitos entre disciplinas, estados, relatório e notas BCF~~ (0.149.0). **Fase 6 completa.**

### Fase 7 — Conceito e terreno (M)
1. ~~**Primitivas:** círculo (0.150.0), arco (0.151.0), offset (0.152.0), espelho (0.108.0), escala (0.153.0) — com medidas escritas e snaps.~~
   Fica para depois: ~~o offset de faces côncavas (uma face em L), e escalar a partir do centro (com Ctrl, como no SketchUp)~~ (0.206.0).
2. ~~**Imagem de fundo:** importar, calibrar a escala com uma medida conhecida, bloquear~~ (0.154.0).
   Fica para depois: ~~a imagem nas folhas (PDF) e no DXF~~ (0.207.0; no DXF, o contorno e o nome); ~~uma imagem numa fachada (vertical)~~ (0.208.0: Pôr numa fachada); ~~recortar a imagem~~ (0.209.0). **Fase 7 sem restos.**
3. **Topografia:**
   - ~~pontos (0.155.0) ou DXF (0.156.0) → terreno, com curvas de nível (0.155.0)~~;
   - ~~plataformas~~ (0.157.0);
   - ~~corte e aterro~~ (0.157.0);
   - ~~cores de inclinação e cotas pontuais~~ (0.156.0). **Fase 7 completa** (0.157.0).

   Classes IFC: `IfcSite`, `IfcGeographicElement` TERRAIN.
   Fica para depois:
   - ~~as cores de inclinação nas folhas (PDF), com a legenda~~ (0.201.0);
   - ~~o valor escrito nas curvas mestras~~ (0.202.0: no papel, no DXF e no ecrã);
   - ~~o pé dos taludes desenhado na planta (a linha onde encontram o terreno, com os traços de talude)~~ (0.203.0);
   - ~~editar o contorno de uma plataforma já feita (hoje apaga-se e faz-se outra)~~ (0.204.0: Editar plataforma);
   - ~~rampas de acesso entre plataformas~~ (0.205.0: Rampa de acesso). **Topografia sem restos.**

### Fase 8 — Importação e levantamento (M)
1. ~~**DXF → modelo:** analisar layers e blocos, pré-visualizar (0.158.0: o DXF ligado, por camadas, com snaps),
   gerar paredes (0.159.0), vãos e mobiliário; guardar o perfil de mapeamento (0.160.0).~~
   Fica para depois: ~~paredes curvas (arcos duplos)~~ (0.210.0); ~~pilares (retângulos e círculos fechados)~~ (0.211.0); ~~a altura dos vãos lida
   de textos do desenho~~ (0.212.0); ~~o DWG~~ (0.286.0: pelo ODA File Converter, autorizado pelo dono — o
   DWG convertido em DXF).
2. ~~**Nuvem de pontos → BIM:** (0.161.0: a nuvem ligada, em XYZ / PLY / LAS, às fatias nas plantas) detetar planos,
   reconstruir, aparar, ortogonalizar, converter em paredes e lajes~~ (0.162.0).
   Fica para depois: ~~os vãos (portas e janelas) lidos na nuvem~~ (0.213.0); ~~vários pisos de uma vez~~ (0.214.0); ~~paredes curvas~~ (0.215.0); ~~o LAZ e o
   E57~~ (0.284.0: com o laspy/lazrs e o pye57, autorizados pelo dono).
3. ~~Gaussian splat (exportação para apresentação) — no fim.~~ (0.176.0: o modelo em splats, num PLY para os
   visualizadores no navegador.) **Fase 8 completa.**
   Fica para depois: splats a partir de fotografias (precisa de treino com placa gráfica); ~~ou da nuvem de pontos~~
   (0.216.0: ponto a ponto, sem treino).

### Fase 9 — Cálculo estrutural pelos Eurocódigos (G, várias versões)
1. ~~**Modelo analítico** derivado do físico (`IfcStructuralAnalysisModel`); validação com lista de problemas~~ (0.163.0).
2. ~~**Ações:** materiais, vento, sismo, cargas, solo~~ (0.164.0).
   Fica para depois: ~~a neve~~ (0.217.0); ~~o uso por laje (hoje é um para os pisos e outro para a cobertura)~~
   (0.218.0); ~~confirmar as
   categorias de terreno do vento no Anexo Nacional~~ (0.219.0).
3. ~~**Análise:** pórtico 2D, modelo global 3D; caminho das cargas~~ (0.165.0: o modelo global 3D, que contém o 2D).
   Fica para depois: ~~os diagramas de esforços desenhados no modelo~~ (0.220.0: os momentos); ~~as lajes como cascas~~ (0.223.0: triângulos DKT); ~~a 2.ª ordem~~ (0.222.0: o θ do EC8); ~~os
   resultados no IFC (`IfcStructuralResultGroup`)~~ (0.221.0).
4. ~~**Verificação EC2;** betão armado; armaduras (`IfcReinforcingBar`) e listas de fabrico~~ (0.166.0).
   Fica para depois: ~~a armadura superior das lajes sobre os apoios~~ (0.224.0: sobre as vigas); ~~a armadura de pele e a segunda camada~~ (0.226.0: a segunda camada; a pele avisada, a área por confirmar); ~~os
   pilares circulares e em L/T~~ (0.227.0); ~~as sapatas corridas e os maciços de estacas~~ (0.228.0); ~~os pormenores de emendas~~ (0.230.0) ~~e dispensas
   de varões (hoje inteiros de ponta a ponta)~~ (0.229.0: as dispensas); ~~as armaduras no piso tipo~~ (0.231.0: a do mais esforçado); ~~ligar a armadura ao elemento também por
   `IfcRelAggregates`~~ (0.285.0: o dono escolheu — como a «peça de betonagem» do Tekla).
5. ~~**Desenhos estruturais,**~~ (0.168.0) ~~quantidades, memória de cálculo~~ (0.167.0). **Fase 9 completa**
   (0.168.0).
   Fica para depois: ~~as cotas nos desenhos de armaduras~~ (0.232.0); ~~os cortes a uma escala própria (hoje ampliados no mesmo
   desenho)~~ (0.234.0); ~~os pormenores tipo (nós viga-pilar, emendas)~~ (0.237.0); ~~a planta de estrutura vista de baixo (a cofragem
   refletida)~~ (0.235.0); ~~as etiquetas à mão (mudar de sítio)~~ (0.238.0); ~~as marcas dos cortes nos alçados (por onde passa o A–A)~~ (0.236.0);
   ~~a memória de cálculo com os desenhos~~ (0.233.0).

Esta fase depende muito do código do addon (decisão 3).

### Fase 10 — Design e fabrico (M)
1. **Mobiliário paramétrico:** ~~blocos~~ (0.169.0: módulos inferior, superior e coluna), ~~cozinhas em L/U~~
   (0.170.0), ~~divisões~~ (0.172.0, e o roupeiro), ~~fachadas, puxadores~~, ~~bancada~~ (0.170.0), ~~rodapé~~,
   ~~equipamentos e gás~~ (0.171.0), ~~lista de corte~~ (0.169.0).
   Fica para depois: ~~módulos de canto (cegos, em L, carrossel)~~ (0.239.0: cegos; 0.240.0: em L e carrossel); ~~compartimentos de larguras diferentes, arrastados~~ (0.244.0);
   ~~portas de correr~~ (0.241.0); ~~o forno numa coluna~~ (0.242.0); ~~as frentes com outro material e cor~~ (0.243.0: no IFC e na lista de corte; no ecrã, a cor do móvel); as dobradiças e corrediças pela
   marca.
   Por rever: comparar com o `tools/furniture` do addon quando o disco D: voltar.
2. ~~**Superfícies**~~ (0.175.0: onduladas, em costelas), ~~painéis perfurados~~ (0.173.0), ~~Profile Pen~~
   (0.174.0: rodapé, sanca, friso, cimalha), ~~ripado~~ (0.173.0, e o canelado), ~~com exportação para fabrico~~
   (0.173.0: o DXF dos painéis, com os furos, e das ripas; 0.174.0: as peças dos perfis com as esquadrias; 0.175.0:
   o contorno de cada costela). **Fase 10 completa.**
   Fica para depois: ~~um perfil desenhado pelo utilizador (uma face do Conceito como secção)~~ (0.245.0).
   Por rever: comparar com o addon quando o disco D: voltar — em especial o que eram as «Superfícies».

### Interface — os 8 painéis (proposta do dono do projeto, 2026-10-25)
A «Ficha técnica dos 8 painéis da interface» (versão conceptual 1.0) passa à frente dos restos das fases. Faz-se
por etapas, sem mudar o motor de modelação nem as funções que já existem:
1. ~~**Cabeçalho (1) e faixa de ferramentas (2):** as disciplinas (Início, Modelagem, Arquitetura, Estrutura,
   Instalações, Terreno, Anotar, Massa e Estudos, Visualizar, Gerenciar, Render, Colaborar) em vez dos ambientes;
   as ferramentas com ícone e nome; os menus passam para as disciplinas~~ (0.182.0).
2. ~~**Parâmetros contextuais (3):** o novo aspeto da barra (que já muda com a ferramenta)~~ (0.183.0: o ícone e o
   nome da ferramenta, os campos com rebordo, a validação a vermelho, a roda dentada do tipo em uso).
3. ~~**Barra compacta (4) e Navegador do Projeto (5):** os módulos (Projeto, Biblioteca, Materiais, Ambientes,
   Folhas, Quantitativos, Configurações), o navegador com pesquisa; os Pavimentos e as Regras gráficas como
   módulos~~ (0.184.0).
4. ~~**Propriedades (7):** grupos recolhíveis, pesquisa, o tipo em cima, instância e tipo distinguidos, o Navegador
   de Materiais~~ (0.185.0). ~~As propriedades comuns de vários elementos selecionados, editáveis em conjunto~~
   (0.187.0).
5. ~~**Rodapé (8):** a navegação (já lá está desde a 0.182.0), a escala, as unidades, a grelha, o estilo visual e o
   piso ativo~~ (0.186.0: mais a orientação). As unidades são do utilizador; se o dono as quiser por projeto,
   guardam-se com o projeto.

### Guardas-corpos profissionais (pedido do dono do projeto, 2026-10-26)
«Quero uma ferramenta poderosa onde podemos criar tipos variados de guarda-corpo» (com imagens de referência:
barras, cabos, vidro com grampos e encastrado, malha, ziguezague, corrimão de madeira):
1. ~~Tipos de guarda (IfcRailingType): corrimão, prumos e chapas de base, enchimento (barras, travessas, cabos, vidro
   com grampos, vidro encastrado, chapa, malha, ziguezague), travessa inferior, corrimão de apoio, materiais; dez
   tipos feitos~~ (0.258.0).
2. ~~As cores dos materiais de cada peça no 3D (madeira, vidro, inox, aço preto)~~ (0.259.0; o vidro ainda opaco).
3. ~~O editor de tipos de guarda, com pré-visualização: criar, duplicar, mudar e apagar tipos~~ (0.260.0).
4. ~~Guardas de escada contínuas: nos patamares, prumos a prumo nos lanços~~ (0.261.0); ~~prolongamentos e remates nas
   pontas~~ (0.282.0: as medidas do DL 163/2006, anexo 2.4.9 — um cobertor na base, inclinado, 0,30 m no topo, de nível
   —, as pontas viradas para o piso).

### Telhados por blocos (pedido do dono do projeto, 2026-10-26)
«Vamos deixar o telhado simples por face, e vamos adicionar essa outra possibilidade de telhado por bloco», como no
ArqSynth Modeler (formas complexas que de outra forma não se conseguem):
1. ~~Coberturas por blocos: retângulos com águas por lado, juntos pela envolvente de cima; a ferramenta Cobertura →
   Por blocos~~ (0.262.0).
2. ~~Editor de blocos: por lado, água ou empena, inclinação e beirado; mover, rodar, apagar e duplicar blocos~~ (0.263.0).
3. ~~Pegas para esticar os blocos na planta e no 3D (como o `roof_block_stretch` do addon)~~ (0.264.0).
4. ~~Arestas classificadas e medições: comprimentos de beirado, cumeeira, rincão e laró (como o `roof_frame_model` do
   addon), nas Propriedades e nas tabelas~~ (0.265.0).
5. ~~Coberturas assentes nas paredes (todas, não só as por blocos)~~ (0.275.0): hoje o topo da cobertura passa pela aresta de fora
   do topo da parede, e essa aresta vê-se como uma linha na água. Assentar a face de baixo na parede, como o Revit.
   A ajuda do Revit diz que a altura «onde a parede e a cobertura se encontram» (Plate Offset from Base) se mede
   pela face de dentro da parede com «Rafter» e pela de fora com «Truss». (2026-10-28: o dono deixou a escolha ao
   programa — face de dentro, «Rafter»: sem folga nem linha, sem precisar de ligar o topo.)
6. ~~Madeiramento (pedido do dono, 2026-10-28), a partir das águas e das arestas classificadas, como a fase R2 do
   addon (roof_carpentry): frechal nos beirados, fileira nas cumeeiras, varas de rincão e de laró, terças (vão do
   caibro até 1,50 m), caibros a 0,50 m e ripas à galga da telha, com as medidas do addon por omissão (8×16, 5×6,
   5×1,5 cm); no IFC, peças IfcMember da cobertura~~ (0.276.0).
7. ~~Madeiramento: as medidas e os afastamentos escolhidos numa janela (secções, caibros, galga, vão das terças) e a
   tabela de madeira (peças, comprimentos, volume por tipo) nas Tabelas~~ (0.277.0).

### Telhas (o «telhado realista» do addon, fase R3; o dono: «vai por ordem», 2026-10-28)
1. ~~As telhas do addon (marselha, colonial, plana) assentes nas águas: fiadas à galga, colunas à largura
   útil, cortadas nos rincões, larós, cumeeiras e empenas, telhas de cumeeira; no IFC, um IfcCovering ROOFING com a telha
   guardada uma vez e repetida (IfcMappedItem)~~ (0.279.0).
2. ~~Chapas e painéis (a chapa ondulada e o painel sanduíche do addon): por colunas à largura útil, ao comprimento da
   água, divididos pelo comprimento de fabrico~~ (0.280.0; e nenhum triângulo descoberto junto aos rincões).
3. ~~A telha do utilizador: uma forma própria (um componente) com a largura útil, a galga e o peso do fabricante, como
   o «Registar telha» do addon~~ (0.281.0). **Telhas completas.**

### Motor de portas e janelas (pedido do dono, 2026-10-28: «motor gerador de portas e janelas avançado»)
O addon não tinha gerador de caixilharia; este é novo. Cada tipo de porta ou janela é um desenho: um aro à volta de
linhas de células, e cada célula é uma folha que abre de uma maneira (ou um fixo), com vidro ou painel cego.
1. ~~Motor de base: o desenho (linhas e células com abertura e enchimento; aro, folhas, montantes e travessas, vidro)
   dá o corpo 3D em peças com o seu material, o símbolo em planta e os nomes do IFC (OperationType / PartitioningType,
   IfcDoorLiningProperties / IfcWindowLiningProperties, propriedades das folhas). O desenho fica guardado no tipo e as
   portas e janelas do catálogo são feitas por ele. Corrigir a bandeira que se perdia ao inverter as dobradiças e o
   aro de 10 cm que as janelas ganhavam ao mexer~~ (0.288.0; e as guarnições das portas, que já existiam).
2. ~~O gerador nas mãos do utilizador: uma janela com o alçado desenhado ao vivo, a grelha editável (dividir e juntar
   células, medidas, abertura e enchimento de cada uma) e uma biblioteca de modelos prontos. Espelhar também as
   janelas que não são simétricas (oscilobatente à esquerda passa a à direita)~~ (0.289.0).
3. ~~Guarnições à escolha, soleira e peitoril com pingadeira, puxadores e dobradiças desenhados~~ (0.290.0; e virar a
   janela de lado nas Propriedades, para o peitoril ficar para fora).
4. ~~Estores e persianas (caixa e lâminas), mosquiteiros, grades~~ (0.291.0: o estore de enrolar; as portadas de
   lâminas ficam para quando o dono as pedir).
5. ~~Os símbolos de abertura nos alçados (o triângulo da folha)~~ (0.292.0) ~~e o mapa de vãos nas folhas~~ (0.293.0).
6. ~~Vãos em arco (de volta inteira, abatido, ogival)~~ (0.294.0). **Motor de portas e janelas completo.** Ficam para
   quando o dono pedir: portadas de lâminas, folhas em arco (com a travessa curva), pôr sozinho o peitoril para o lado
   de fora (pelo IsExternal da parede).

Pedido do dono, 2026-10-29 («avance com esses»):

7. ~~Portadas de lâminas: uma ou duas folhas por fora da caixilharia, fechadas no vão à face da parede ou abertas
   (rebatidas sobre a parede), com aro e lâminas inclinadas; cortadas pelo arco num vão em arco~~ (0.295.0).
8. ~~Folhas de abrir dentro do arco, com a travessa de cima curva numa só peça~~ (0.296.0).
9. ~~O peitoril para o lado de fora sozinho: a janela posta numa parede exterior (IsExternal) fica virada com o peitoril
   para o lado de fora do edifício, e volta a virar-se quando as paredes mudam; virada à mão, fica como o utilizador a
   deixou~~ (0.297.0).

### Modificadores de paredes e a fita por disciplinas (pedido do dono do projeto, 2026-10-29)
«Vamos criar os modificadores de paredes e colocá-los na barra de ferramentas. Aliás, a barra de ferramentas
precisa de uma atenção especial: organizar de acordo com as disciplinas e de forma lógica do fluxo de trabalho em
BIM.» Medido antes: a 1280 px, metade das ferramentas de cada disciplina ficava escondida na seta » (na Arquitetura,
a cobertura, as salas, o mobiliário e as ferramentas das paredes) e os separadores já não cabiam no cabeçalho.
1. ~~**A fita nova:**~~ (0.298.0)
   - as disciplinas pela ordem do trabalho: Início · Modelagem (desenhar e modificar, em qualquer fase) · Gerenciar
     (preparar o projeto) · Massa e Estudos · Terreno · Arquitetura · Estrutura · Instalações · Colaborar
     (coordenar) · Anotar · Visualizar · Render;
   - em cada disciplina, painéis com nome (como no Revit), pela ordem em que se usam;
   - botões grandes para as ferramentas principais e colunas de três botões pequenos para as outras;
   - quando a janela é estreita, os painéis da direita recolhem-se num botão com o nome do painel e as suas
     ferramentas, em vez de as esconder;
   - o separador **«Modificar | Paredes»** (como no Revit) aparece sozinho quando se selecionam paredes, com todos
     os modificadores, e desaparece quando a seleção se esvazia. Também: repor o perfil e desligar o topo.
2. ~~Virar a parede~~ (0.299.0) (o interior e o exterior trocam: as camadas passam para o outro lado) e voltar a ligar as pontas
   soltas.
3. ~~Dividir com folga, e aparar / estender até um limite (uma parede ou várias de uma vez)~~ (0.300.0).
4. ~~Junções de paredes: num canto, meia-esquadria ou topo a topo, e qual das paredes passa~~ (0.301.0).
5. ~~Ligar a base (a uma laje ou sapata por baixo) e desligar o topo e a base~~ (0.302.0; o topo, 0.298.0).
6. ~~Abertura na parede: um retângulo desenhado na face da parede, sem porta nem janela~~ (0.303.0).
7. ~~Rodapé, sanca, friso ou cimalha na parede~~ (0.304.0): o perfil corrido preso à face de uma parede, que a acompanha quando
   ela muda, cortado nas portas.
8. ~~Ranhura: um friso rebaixado na face de uma parede, horizontal ou vertical, que a acompanha~~ (0.305.0).

### Caixilho Studio (pedido do dono do projeto, 2026-10-29)
«Verifiquei o gerador de porta e janela, mas não gostei. Fiz este protótipo e quero que implemente» (o protótipo
«Caixilho Studio — editor visual», HTML):
1. ~~O núcleo por colunas: os montantes a toda a altura e as travessas por coluna (ligadas ou não); um enchimento
   por painel — vidro, vidro fosco, painel opaco, madeira, veneziana; os sistemas (alumínio, PVC, madeira, aço) e as
   cores do perfil (grafite, branco, bronze, madeira natural) como materiais~~ (0.306.0).
2. ~~O Caixilho Studio no lugar do gerador: o vão à escala, montantes e travessas arrastados, cotas editáveis com
   contas, o cartão do painel, vistas exterior e interior, vários vãos em separadores, modelos de arranque,
   «Inserir no modelo»; o resto do gerador em «Mais opções…»~~ (0.307.0).
3. ~~«O tema deve ser coerente: quando criarmos o tema escuro vai ser assim, mas agora o tema é claro» — o Studio nas
   cores claras do programa; as do protótipo guardadas como tema escuro~~ (0.308.0).
4. ~~«Tem parâmetros para igualar todas as divisões? Caso não, faça» — «Larguras iguais» e «Alturas iguais» como
   parâmetros do tipo (mantidos ao pôr e tirar montantes e travessas e ao mudar o tamanho; guardados no IFC),
   «Igualar tudo»~~ (0.309.0).

### Modelação como no SketchUp (pedido do dono do projeto, 2026-10-29)
«Construí um retângulo, fiz o offset, mas o push/pull negativo criou um sólido, e as partes são selecionadas todas
juntas; não consigo selecionar apenas uma face. Isso não está a ser semelhante ao SketchUp» e «quando usar o push/pull
com Control ligado, ele deve criar um sólido independentemente da direção»:
1. ~~Um clique escolhe só a face de um esboço (dois: com as arestas; três: o esboço inteiro); Delete, Mover e Rodar
   na face sozinha; o Push/Pull tira a face do sítio (um rebaixo aberto); Ctrl, «Criar sólido», deixa a face de
   partida e faz um sólido fechado para cima ou para baixo~~ (0.310.0).
2. ~~Push/Pull em várias faces escolhidas ao mesmo tempo, na mesma direção («que ele possa extrudir na mesma direção
   várias faces selecionadas»): a mesma distância para todas, as que se tocam como uma peça, um só passo~~ (0.311.0).

### Desenho livre como no SketchUp (pedido do dono do projeto, 2026-11-03)
«A parte de modelagem livre precisa melhorar, para assemelhar ao SketchUp. Não consigo selecionar uma linha, copiar,
ou usar o offset. Preciso de ferramenta de arco nesse grupo, linha livre, curvas de Bézier.» O que havia: um clique
numa linha escolhia a cadeia inteira (as linhas desenhadas de seguida), o Copiar levava-a toda, o Offset só aceitava
faces e uma face escolhida sozinha não se copiava; os arcos só com o Tab da Linha.
1. ~~**Uma linha sozinha, como no SketchUp:** um clique escolhe só a linha clicada (um arco, uma curva: inteiros); dois
   cliques, a cadeia; três, tudo o que está ligado. Apagar, Mover, Rodar, Copiar, Matriz e Ctrl+C / Ctrl+V nela; as
   linhas ligadas às pontas acompanham quando ela se move. As faces escolhidas sozinhas também se copiam~~ (0.373.0).
2. ~~**Offset de linhas:** um clique numa linha (ou as linhas escolhidas) e o rato — ou a distância digitada — fazem a
   paralela da cadeia no seu plano, cantos vivos; num arco, o arco concêntrico~~ (0.373.0).
3. ~~**Arco (A) no painel Desenhar:** dois pontos e a flecha (o arco do SketchUp), centro e ângulo, três pontos, e
   setor (fecha a face); o raio, a flecha ou o ângulo digitados; os segmentos à escolha. Um arco que fecha um contorno
   com outras linhas faz a face, como no SketchUp — também linhas de cadeias diferentes~~ (0.373.0; a Linha também
   fecha com outras cadeias; pegas e Propriedades do arco).
4. ~~**Linha livre (à mão):** arrastar desenha a curva, simplificada; fechada, faz a face~~ (0.373.0).
5. ~~**Curvas de Bézier:** clique = ponto de canto, arrastar = ponto com tangentes (como no Illustrator); Enter acaba,
   no primeiro ponto fecha; escolhida, as pegas dos pontos e das tangentes mudam-lhe a forma~~ (0.373.0).

### Modelos da suite — «Arquivo Modelo» (pedido do dono do projeto, 2026-11-04)
«Criar um sistema de Arquivo Modelo (template) que define as configurações iniciais de cada projeto novo, guarda os
modelos numa biblioteca partilhada legível pelos outros programas da suite, e permite guardar um modelo como PADRÃO.»
Por fases, parando no fim de cada uma para o dono testar:
1. ~~TemplateManager (ler, gravar, validar) e modelo de fábrica~~ (0.393.0: `arqsynth_templates/`, «ArqSynth Padrão»,
   `Modelos - verificar.bat`).
2. Carregar o padrão no arranque e em «Novo Projeto»: aplicá-lo ao projeto novo (unidades, IfcProject/Site/Building,
   pisos, tipos, materiais, estilos, interface), nunca a um projeto que se abre; guardar no projeto o modelo usado
   (nome + versão); avisar do que veio do de fábrica.
3. Gestor de Modelos (janela): lista com ★, aplicar ao projeto atual, guardar a configuração atual como modelo,
   atualizar, definir padrão, repor fábrica, abrir a pasta, duplicar, mudar o nome, apagar; Ficheiro ▸ «Guardar como
   Modelo…» e «Definir configuração atual como padrão»; escolher o modelo na página inicial / Novo Projeto.
4. Importar / exportar (partilhar com colegas) e a partilha com os outros programas da suite.

### Arcos e curvas no perfil da parede (pedido do dono do projeto, 2026-11-04)
«Na edição do perfil da parede preciso de mais controlo para poder criar arcos ou curva Bézier.»
1. ~~Cada lado do perfil reto, em arco (por um ponto de passagem) ou em curva de Bézier (pelas tangentes), escolhido
   na barra da edição do perfil (Tab), com pegas para o ponto do arco e as tangentes; gravado no IFC, liso, a esticar
   com a parede~~ (0.375.0).

### Ferramentas de arquitetura do addon e os temas do estudo (pedido do dono do projeto, 2026-11-03)
«Gostaria que criasse mais ferramentas de arquitetura para corresponder ao que existe no Blender de acordo com o
inventário de ferramentas na pasta raiz. Depois crie os temas de acordo com o estudo em html na pasta raiz.» O
inventário é `D:\BIM\# Inventário de ferramentas — ArqSy.txt` (ArqSynth Modeler 1.1); o estudo,
`C:\BIM\proposta-interface-arqsynth.html` (a fita de Arquitetura e cinco paletas). Já havia: paredes por linha,
retângulo, arco, círculo e face (escondidas na barra de contexto), lajes também pela varinha mágica, coberturas por
blocos, pelas paredes e por face, telhas e madeiramento, escadas reta/L/U/V/caracol, rampas, guarda-corpos por
caminho, vazio e escada, forros, revestimentos (também ripado e perfurado), nichos pelo Push/Pull, ambientes por
clique dentro das paredes. Falta, pela ordem do estudo:
1. ~~**A fita de Arquitetura do estudo:** Paredes — Parede, Parede cortina e, à vista, Retangular, Circular, Arco, Por
   face e Varinha mágica; Aberturas — Porta, Janela, Abertura na parede, Abertura na cobertura, Nicho; Pisos e
   coberturas — Laje, Cobertura, Piso, Forro, Calha; Circulação — Escada, Rampa, Elevador, Guarda-corpo; Ambientes —
   Ambiente, Separador, Identificar, Áreas. O que já lá estava (caixilho, revestimentos, perfis, móveis) continua~~
   (0.374.0).
2. ~~**Parede pela varinha mágica** (o `wall_magic_wand` do addon): arrastar uma janela sobre duas linhas paralelas de
   um desenho (DWG/DXF ligado, linhas de esboço) faz a parede entre elas, a espessura medida~~ (0.374.0).
3. ~~**Nicho:** um clique na face de uma parede faz um nicho (largura, altura, profundidade, peitoril) — o rebaixo
   IFC que o Push/Pull já fazia, agora direto~~ (0.374.0).
4. ~~**Piso:** o revestimento de piso de um ambiente (clique dentro) ou de um polígono — IfcCovering FLOORING, com
   espessura e material, nas quantidades~~ (0.374.0).
5. ~~**Calha:** num beirado da cobertura, a calha ao longo dele~~ (0.374.0, uma caixa em U de alumínio);
   ~~a meia-cana e o tubo de queda~~ (0.438.0: Secção e Tubos de queda na barra e nas Propriedades; fica por fazer o
   cotovelo do tubo até à parede).
6. ~~**Elevador:** a caixa e a cabina (IfcTransportElement ELEVATOR) em planta, por pavimentos~~ (0.374.0, a frente
   aberta); ~~as portas de patamar e abrir as lajes por cima sozinho~~ (0.439.0).
7. ~~**Ambientes — Separador, Identificar, Áreas:** linhas que separam ambientes sem paredes (contam como limite);
   identificar todos os espaços fechados do pavimento de uma vez; as áreas (útil e bruta) do pavimento~~ (0.374.0).
8. ~~**Guarda de vão:** o guarda-corpo dentro de uma porta ou janela escolhida (de batente a batente)~~ (0.374.0).
9. ~~**Temas do estudo:** as paletas Bege, Areia, Pedra, Escuro e Grafite (nove cores: barra e fundo, fita, painéis,
   cabeçalhos, destaque, texto, área de desenho, divisórias, campos) em Visualizar ▸ Tema, e «Explorar cores» para
   as afinar e guardar, como no estudo~~ (0.374.0).
10. **Do inventário, ainda por fazer** (fora da fita do estudo): ~~escadas a colocar já feitas (arrastar a escada
    pronta)~~ (0.435.0: Escada ▸ Colocar ▸ Pronta — a escada presa ao rato, R roda, Espaço o ponto do 1.º degrau),
    ~~pisos com declive por vértice~~ (0.433.0: o grupo Declive nas Propriedades — lado alto e %, a altura de cada
    canto, Pôr plana; corpo de triângulos no IFC), ~~fachada de vidro em arco e por face~~ (0.436.0: Parede cortina ▸
    Forma ▸ Arco — três cliques — e Por face — o retângulo de pé da face, por fora dela), ~~Steel/Wood frame~~ (0.437.0:
    Propriedades da parede ▸ Estrutura leve — guias, montantes, ombreiras, vergas, peitoris, travamentos no núcleo,
    refeita quando a parede muda; ficam por fazer as placas por face como peças e a estrutura nas listas), ~~mobiliário
    solto de catálogo~~ (0.440.0, «Sim, peças próprias»: Mobiliário ▸ Mobiliário solto — 14 peças paramétricas do
    próprio programa, por divisão, R/Espaço, cores por parte, peça no topo das Propriedades; o catálogo do addon usa
    ficheiros .blend de terceiros, que não vêm),
    ~~o «W + letra» das paredes~~ (0.432.0: W e, em 1,25 s, a letra do comando; L novo — as paredes ligadas), ~~ripado
    como ferramenta própria~~ (0.434.0: Acabamentos ▸ Ripado — clique na face ou retângulo, moldura, ripas de fixação,
    lista de corte; ~~o ripado solto, sem parede — divisória ou brise~~ — 0.441.0: Acabamentos ▸ Ripado solto, dois
    cliques).
    ~~Painel perfurado como ferramenta própria~~ (0.389.0:
    furos redondos/quadrados, malha reta/45°, placas com junta, imagem, retângulo na face). ~~Cobertura orgânica~~
    (0.390.0: cúpula/abóbada/onda tiradas do contorno; casca, gridshell, envidraçada, pérgola curva; aro e apoios).
    ~~Da cobertura orgânica fica por fazer: o loft entre 2+ curvas e a superfície por 4 bordos (o addon tem), nós
    desenhados nos cruzamentos das barras~~ — substituída (o dono: «não é isso que eu quero… estude a superfície
    paramétrica»; «não chamaria cobertura») pela **Superfície paramétrica** (0.395.0): ver a secção abaixo.

### Superfície paramétrica (pedido do dono do projeto, 2026-11-04)
O conceito do addon (`EXEMPLOS DO BLENDER\tools\surfaces`): forma primeiro (curvas do modelo → loft, 4 bordos,
revolução, extrusão, varrimento, tampa, fórmula; modificadores), construção depois (casca, nervuras, ripas,
entrelaçado, gridshell, anel de bordo, pilares, painéis com caixilho/abertura/perfuração, vidro spider), a seguir as
curvas quando mudam; o Uso escolhe a classe IFC (estrutura, cobertura, fachada, pala).
1. ~~Motor, construção, elemento, ferramenta, Propriedades, ligação às curvas, Anel de controlo, lista de peças,
   definição .arqsurf~~ (0.395.0).
2. **Por fazer, do addon:** «Superfície esculpível» (4 secções Bézier já em loft, para editar à mão), biblioteca de
   definições (guardar/usar com outras curvas), curvas de expressão desenhadas na ferramenta, «Mapa de peças» numa
   folha, painel a CNC (a chapa plana de uma célula, como o painel perfurado), números de peça (P001, N001) na vista.
3. **Por fazer, além do addon** (o estudo aponta): apoios interiores e form-finding (pontos fixos no solver da
   membrana; densidade de forças para gridshells), aberturas/óculos na superfície, pilares em árvore, mapas de
   planaridade/inclinação/curvatura, camadas da cobertura (isolamento, impermeabilização) e caleiras nos pontos baixos.

### Portas e janelas limpas (pedido do dono do projeto, 2026-10-30)
«Quero que as linhas de junções das peças não apareçam, para que portas e janelas fiquem mais limpas» (com capturas
dos cantos do aro, das folhas e das guarnições marcados):
1. ~~O aro, cada folha, as guarnições, o peitoril, as portadas e o mosquiteiro, cada um uma superfície só, sem linhas
   onde as peças se encontram; fica a linha à volta de cada folha~~ (0.312.0).
2. ~~O tipo no cabeçalho das Propriedades, em todos os elementos com tipo («colocar o botão do tipo no cabeçalho e
   com lista com miniatura dos vãos», «para todos os elementos»): uma lista com a miniatura de cada tipo; as mesmas
   miniaturas na barra de cima e no editor de tipos~~ (0.313.0).

### Gráficos dos materiais e estilos de vista (pedido do dono do projeto, 2026-10-30)
«Programe mais camadas de desenvolvimento no gráfico final do projeto. Quero poder criar estilos de vistas com tramas
e sombreamentos. E para isso os materiais devem receber mais detalhes, de apresentação de superfície e cortes.» O que
já havia: a cor de cada material (o estilo de superfície no IFC), a trama de corte tirada da categoria do material e
o estilo gráfico do projeto (0.126: trama, cor, ângulo e afastamento por categoria; as penas); os quatro aspetos da
vista 3D (sombreado, linhas escondidas, arames, raio-X) e as arestas. Fica assim, passo a passo:
1. ~~**Os padrões e os gráficos de cada material, como no Revit:** uma biblioteca de padrões feitos de famílias de
   linhas (traços e pontos), de desenho (medidos no papel: diagonal, cruzada, betão, areia, isolamento, terra,
   madeira…) e de modelo (medidos na obra: azulejo, tijolo à vista, pedra aparelhada, réguas, telha…). Cada material
   ganha a superfície (padrão de primeiro plano e de fundo, cada um com a sua cor; a cor de sombreamento; a
   transparência) e o corte (padrão de primeiro plano e de fundo, com cores; vazio = o do estilo gráfico do projeto
   pela categoria, como até aqui). Editados na janela dos materiais, com a amostra de cada um; gravados no IFC, para
   reabrir igual e ler noutro programa. As miniaturas dos tipos usam os padrões dos materiais~~ (0.314.0).
2. ~~**Os cortes no papel pelos materiais:** plantas, cortes, folhas e PDF pintam o corte de cada camada com o fundo e
   o primeiro plano do seu material; o estilo gráfico do projeto passa a ter os padrões novos por categoria~~
   (0.314.0).
3. ~~**Estilos de vista com nome:** criar, nomear, duplicar, editar e apagar (Visualizar ▸ Estilos de vista…): faces,
   cores, arestas e espessura, sombras, padrões de superfície, cortes e transparência. Os quatro aspetos de sempre
   ficam como estilos do programa, e juntam-se «Cores consistentes» e «Realista». Dão-se às vistas nas Propriedades,
   no botão do rodapé e nos modelos de vista; ficam com as vistas no ficheiro do projeto~~ (0.315.0).
4. ~~**O 3D pelo estilo:** as cores dos materiais, camada a camada (a pedra por fora, as camadas lado a lado no topo
   da parede); as cores sem luz; o vidro transparente; os padrões de superfície nas faces; as sombras do sol; arestas
   mais grossas~~ (0.315.0).
5. ~~**Os desenhos pelo estilo:** alçados, cortes, plantas e vistas 3D nas folhas e no PDF com as faces pintadas
   (sombreadas ou em cores consistentes), os padrões de superfície nas faces vistas e o corte como o estilo diz~~
   (0.315.0).


6. ~~**As sombras no papel e o sol à escolha** (o dono: «sim, faz»): as sombras projetadas pelo sol do estilo nos
   alçados, cortes, plantas e vistas 3D das folhas e do PDF; o sol de cada estilo por azimute e altura, ou calculado
   pelo local do terreno, pelo dia e pela hora~~ (0.316.0).

7. ~~**Os padrões de modelo alinhados à mão numa face** (como o «alinhar» do Revit)~~ (0.332.0, decidido pelo dono a
   2026-11-01: Modificar ▸ Alinhar numa linha do padrão — desloca ou roda; guardado no elemento, acompanha-o).

### Tramas como sistema: no ecrã, criadas pelo projeto, por categoria (pedido do dono do projeto, 2026-10-30)
«As tramas ainda não são um sistema que permite criar muitos materiais, e não consigo colocar uma trama para um
elemento cortado e outra trama para a superfície projetada.» O que faltava: no ecrã, o corte das plantas e dos cortes
saía sempre escuro e as superfícies projetadas sem trama (as tramas só apareciam no PDF, e a da superfície só com um
estilo); os padrões eram uma lista fixa, sem como criar outros. Fica assim:
1. ~~**As tramas no ecrã:** nas plantas e nos cortes, o que é cortado mostra-se com o fundo e o primeiro plano de cada
   camada (do material, ou da categoria no estilo gráfico do projeto), como no papel e à escala da vista; as
   superfícies projetadas mostram a trama de superfície do seu material, também no estilo Sombreado~~ (0.317.0).
2. ~~**As superfícies projetadas no papel sem estilo:** os desenhos de sempre (linhas) também desenham a trama de
   superfície das faces vistas, escondida pelo que está à frente~~ (0.317.0).
3. ~~**Padrões do projeto:** uma janela para criar, duplicar, mudar e apagar padrões (de desenho ou de modelo; simples
   ou com várias famílias de linhas e traços), com a amostra; gravados no próprio IFC; nas listas dos materiais e do
   estilo gráfico~~ (0.318.0).
4. ~~**Tramas por categoria nos estilos de vista:** o corte e a superfície projetada de cada categoria (primeiro plano
   e fundo), por cima das dos materiais, no ecrã e no papel~~ (0.318.0).
5. ~~**Uma biblioteca de materiais maior**, por famílias, cada um com as suas tramas de corte e de superfície; a
   janela dos materiais por família e com pesquisa~~ (0.318.0).

6. ~~**Escolher a trama como no Revit** (o dono: «ainda não consigo colocar uma trama na superfície e no corte; deveria
   ter opção nos 2 grupos para melhor intuição»): cada padrão um botão com a amostra; clicado, a janela com todas as
   tramas, «Nenhum», «Novo…» e «Editar…»; a amostra do grupo também a abre~~ (0.319.0).

7. ~~**As tramas também por elemento numa vista** (como «Substituir gráficos na vista ▸ Por elemento» do Revit), além
   de por categoria~~ (0.331.0, decidido pelo dono a 2026-11-01: Visualizar ▸ Tramas por elemento e o botão direito
   do Selecionar; corte e superfície, só nessa vista, no ecrã e no papel).

### Junção automática pelo material (pedido do dono do projeto, 2026-10-30)
«Quero que os elementos com o mesmo material tenham uma junção automática: em corte ou em vista, as partes com o mesmo
material mantêm-se unidas e não aparecem linhas de junção.» O que se via (casa de ensaio: paredes em L, em T e em
fila, lajes): no ecrã, cada parede cortada com o seu contorno, uma linha em cada encontro; no papel, o contorno
grosso faltava nas faces de dentro das paredes e o reboco de uma parede atravessava o bloco da outra nos cantos; no
alçado e no 3D, uma linha (ou duas) onde duas paredes iguais se seguem. Como no Revit (limpeza das junções pela
prioridade das camadas), sem mudar a forma de cada elemento no IFC — só o desenho:
1. ~~**O corte unido pelo material (papel e ecrã):** onde dois elementos se sobrepõem, fica a camada mais forte (o
   núcleo — a camada mais grossa — ganha aos acabamentos; empate: pilar, viga, laje, parede); nos cantos em L de
   paredes com camadas, as camadas dobram a esquina em meia-esquadria (o reboco de fora continua por fora, o bloco
   com o bloco, o reboco de dentro por dentro); numa parede que encosta a outra (T), o núcleo dela entra até ao
   núcleo da outra, cortando o reboco. Depois, o mesmo material junta-se num só: linha fina só onde o material
   muda, contorno grosso só à volta de tudo o que é cortado. No PDF, no DXF, nos detalhes e no ecrã (planta e
   corte), cada elemento continua escolhível pelo seu corte~~ (0.320.0).
2. ~~**As vistas sem linhas de junção (papel e ecrã):** num alçado, num corte (o que se vê para lá do plano), na
   vista 3D e nas folhas, a aresta de um elemento que fica no meio de uma face de outro, no mesmo plano e do mesmo
   material (duas paredes iguais seguidas, uma parede que continua outra no piso de cima), não se desenha; onde o
   material muda, a linha fica. No ecrã refaz-se só à volta do que muda (os vizinhos), sem percorrer o modelo~~
   (0.320.0; ao abrir um projeto, aos poucos depois de cada imagem).
3. ~~**Testes e capturas:** unitários (corte em L, T, sobreposição, pilar na parede, vistas), da janela e capturas
   de perto da casa de ensaio no ecrã e no papel~~ (0.320.0).

4. ~~**«Desunir» à mão dois elementos** (como «Unjoin Geometry» do Revit)~~ (0.333.0, decidido pelo dono a
   2026-11-01: Modelagem ▸ Desunir / Unir geometria; a linha entre eles volta no corte e nas vistas).

5. ~~**A prioridade das camadas escolhida no tipo** (estrutura, substrato, isolamento, acabamento), em vez de só «a
   mais grossa é o núcleo»~~ (0.334.0, decidido pelo dono a 2026-11-01: a coluna Função no editor de tipos; no IFC4,
   Priority e Category de cada camada).

### Dados IFC em cada elemento (pedido do dono do projeto, 2026-10-26)
«Ao desenhar, cada elemento devia trazer uma categoria de dados de IFC e parâmetros correspondentes — seja telha,
porta, parede ou qualquer elemento. A filosofia deste aplicativo é ser o mais prático possível e diminuir o tempo de
modelagem.» As propriedades são as das tabelas do IFC4 da buildingSMART, que vêm com o IfcOpenShell; não se inventam
nomes.
1. ~~O conjunto comum completo de cada elemento (Pset_…Common da sua classe) nas Propriedades: as propriedades com
   valor e as vazias, prontas a preencher no sítio, sem diálogo, com os nomes em português. O que o programa sabe
   preenche-se sozinho ao desenhar e acompanha as mudanças: a Referência (o tipo) e os valores já conhecidos. O que
   o utilizador escreve à mão não volta a ser mudado pelo programa~~ (0.266.0).
2. ~~Exterior ou interior calculado: paredes no contorno do edifício, portas e janelas pela parede, coberturas,
   fachadas~~ (0.267.0).
3. ~~Dados do tipo: o que vale para todos os elementos de um tipo (fogo, acústica, U…) no próprio tipo (IfcWallType…),
   editável no editor de tipos; os elementos herdam e podem mudar o seu~~ (0.271.0).
4. ~~Transmissão térmica U das paredes, lajes e coberturas, pelas camadas (EN ISO 6946), para a
   ThermalTransmittance~~ (0.272.0).
5. ~~Verificação antes de entregar: a lista dos elementos com dados em falta, por classe~~ (0.273.0).

### Ligação à IA por MCP (pedido do dono do projeto, 2026-10-26)
«Também quero que o programa tenha bom MCP para poder ligar a IA e ser mais barato no uso de tokens.»
1. ~~Servidor MCP (stdio, JSON-RPC 2.0, só com a biblioteca padrão do Python, sem bibliotecas novas), sobre um
   ficheiro IFC e sem janela, com poucas ferramentas genéricas e descrições curtas: resumo do modelo; consulta com
   filtros, campos escolhidos e páginas, em texto de tabela e não em JSON comprido; descrição de um elemento; criar,
   mudar, apagar e desfazer; abrir e gravar~~ (0.268.0).
2. ~~Ligação à janela aberta: o programa escuta só no próprio computador (localhost, com uma chave). A IA trabalha no
   modelo aberto, à vista e com desfazer~~ (0.269.0).
3. ~~Instalação no Claude (Desktop e Code) e medida dos tokens de uma sessão típica~~ (0.270.0).
4. ~~Os dados IFC pelo MCP: o que falta, num resumo; os tipos em tabela e preenchidos numa só chamada~~ (0.274.0).

### O programa diz o que falta, onde se vê (análise pedida pelo dono do projeto, 2026-10-31)
«Testei algumas [ferramentas] mas não funcionaram; não sei se estou a usar errado ou se a ferramenta ainda não
funciona.» Medido antes, na 0.320: um teste automático carregou em cada botão da fita (187 comandos) no projeto
vazio, numa casa de ensaio e com as paredes escolhidas — 382 cliques. **Nenhum erro: todos respondem.** Mas 84 vezes
(50 comandos diferentes) a resposta foi um aviso ⚠ porque faltava alguma coisa antes — uma seleção, uma planta
aberta, eixos, salas, pilares —, e mais 8 ferramentas ligam-se só para dizer o que fazer primeiro. Esse aviso:
- aparece numa linha pequena no rodapé, à esquerda, e desaparece ao fim de 10 s;
- fica cortado pelo resto do rodapé (Pavimento, Medidas, navegação): a 1440 px lê-se «⚠ Ainda não há eixos:
  desenhe-os (ferramenta Eixos) ou gere-os» e o resto não aparece;
- ao mudar de separador, a mensagem do separador tapa durante 10 s a dica da ferramenta escolhida a seguir (Anotar ▸
  Cota na vista 3D: a dica «abra primeiro uma planta (F4)» não se vê).

Quem não olha para o rodapé vê um botão que «não faz nada». Fica assim, por ordem:
1. ~~**Avisos e dicas à vista:** um balão por cima da vista (em cima, ao centro), com o texto inteiro, que fica até ao
   clique seguinte ou ao Esc; a dica da ferramenta ativa sempre inteira; a mensagem do separador deixa de tapar a
   dica~~ (0.321.0).
2. ~~**Escolher dentro do comando, como no Revit:** os comandos que hoje recusam sem seleção passam a pedir os
   elementos («clique nas paredes… Enter») e continuam — Espelhar, Escala, Ligar topo / base (as paredes, depois a
   laje ou a cobertura), Juntar paredes, Editar perfil, Editar contorno, Sapata combinada, Novo circuito, Repetir nos
   pavimentos, Fazer componente / grupo, Perfil a partir de uma face, Perfil da cobertura, Caixa à volta da seleção~~
   (0.322.0; e Desagrupar, Editar componente, Editar plataforma).
3. ~~**Anotar a partir do 3D:** Cota, Desenho 2D e Pormenor escolhidos na vista 3D abrem sozinhos a planta do
   pavimento ativo~~ (0.323.0).
4. ~~**O que falta, com um botão para o fazer:** quando um comando precisa de algo que ainda não existe, o balão diz o
   quê e oferece o passo — Pilares na grelha sem eixos → «Gerar eixos…»; Calibrar sem imagem → «Importar imagem…»;
   Plataforma sem terreno → «Terreno por pontos…»; propostas elétrica e de águas sem salas → a ferramenta Sala;
   Vigas entre pilares, Lajes nos vãos, Bancada, do mesmo modo~~ (0.324.0; 23 comandos e ferramentas).
5. ~~**Pequenos defeitos achados na varredura**~~ (0.325.0; e os avisos que mandavam para menus escondidos desde a
   0.182, e Apagar sem seleção que pede o que apagar, como o Revit):
   - passos de desfazer vazios: Numerar vãos sem vãos, Soltar ligações e Ortogonalizar sem efeito (o Ctrl+Z seguinte
     parece não fazer nada);
   - Apagar sem nada escolhido, e Pavimento acima / abaixo no último pavimento, não dizem nada;
   - a dica da Rampa de acesso fala em «Plataforma»;
   - «Esses pilares já têm sapata (ou não há pilares)» passa a dizer qual dos dois;
   - o Modelo analítico de uma casa só com paredes diz «0 barras, 0 apoios» sem explicar que as paredes de alvenaria
     não entram no cálculo.
6. ~~**Copiar e Matriz na fita** (painel Modificar, como no Revit), Ctrl+C / Ctrl+V e Colar nos pavimentos (o «Colar
   alinhado» do Revit). Hoje copiar é um gesto escondido: Ctrl dentro do Mover, «3x» na caixa de medidas~~ (0.326.0;
   a matriz polar — cópias à volta de um centro — continua no Rodar com «3x»).
7. ~~**A ajuda de cada ferramenta:** F1 (ou um «?» na barra de cima) com uma ferramenta ativa mostra os seus passos —
   o que escolher antes, onde clicar, as teclas —; e «Primeiros passos»: uma casa feita passo a passo, com o programa
   a mostrar onde clicar. (Hoje o F1 é uma lista de teclas.)~~ (0.327.0: o painel Ajuda — a ferramenta em uso, procurar
   um comando e mostrar onde está, primeiros passos, teclas). **Os sete passos estão feitos.**

Medido de novo na 0.327 (a mesma varredura, 394 cliques): nenhum erro; nenhum botão calado (o F1 abre um painel); das
84 recusas ⚠ da 0.320, 33 passaram a pedir os elementos (balão verde) e as que ficam dizem o que falta, com o botão
para o fazer sempre que há o que oferecer (83 balões com botão); as restantes são casos sem nada a fazer (não há
proposta a tirar, a vista está vazia, as paredes já estão a direito).

Ferramentas que ainda faltam, a decidir com o dono (não entram sem ele dizer):
- **Render:** ~~exportar a vista 3D como imagem em alta resolução~~ (0.329.0, decidido pelo dono a 2026-11-01:
  **Render ▸ Imagem da vista** — a vista 3D, planta, corte ou alçado, até 7680 px, fundo do céu, branco ou
  transparente, sem a seleção nem as marcas das ferramentas). ~~Falta, mais tarde, um render realista~~ (0.343.0,
  secção própria abaixo).
- ~~Os botões e as janelas do próprio Qt (Cancel, Save, File name…) em português de Portugal~~ (0.330.0, pedido do
  dono a 2026-11-01).
- As ideias já anotadas acima: ~~tramas por elemento numa vista~~ (0.331.0); ~~alinhar à mão os padrões de modelo
  numa face~~ (0.332.0); ~~«Desunir» à mão~~ (0.333.0); ~~a prioridade das camadas escolhida no tipo~~ (0.334.0).
- ~~Paredes de alvenaria estrutural no modelo analítico (hoje só pilares, vigas, lajes e sapatas)~~ (0.335.0 a
  0.337.0): secção própria abaixo («Paredes resistentes no cálculo»).
- ~~O tema escuro (as cores do protótipo do Caixilho Studio estão guardadas)~~ (0.338.0 a 0.340.0): secção própria
  abaixo («Tema escuro»).

### Paredes resistentes no cálculo (decidido pelo dono do projeto, 2026-11-01)
«Alvenaria no cálculo.» Hoje, uma casa só com paredes resistentes dá «0 barras, 0 apoios»: as paredes só entram no
peso dos pisos e na sapata corrida. Fica assim, pelos métodos simplificados do Eurocódigo 6 (NP EN 1996-3 e
1996-1-1). Como o resto, é pré-dimensionamento; o projeto de estruturas é do engenheiro. As paredes não entram como
cascas no pórtico: as cargas descem por áreas de influência e a força horizontal reparte-se pela rigidez de cada
parede, o caminho habitual destes métodos.
1. ~~**As paredes resistentes no modelo analítico**~~ (0.335.0):
   - entram as paredes marcadas «Estrutural (resistente)» nas Propriedades (o `Pset_WallCommon.LoadBearing` do IFC),
     piso a piso, cada uma com o seu plano (eixo, base, topo, espessura total e da camada resistente) e os vãos;
   - cada parede apoia-se numa sapata corrida, na parede de baixo ou na fundação; as vigas que acabam numa parede, e
     os pilares sobre ela, ficam apoiados nela; as lajes também;
   - os problemas são ditos: parede suspensa, parede sobre uma laje, parede na fundação sem sapata;
   - no IFC entram como IfcStructuralSurfaceMember (SHELL); a vista 3D do modelo analítico mostra-as.
2. ~~**As cargas nas paredes**~~ (0.336.0):
   - cada laje dá a cada viga e a cada parede a área mais perto, como já faz com as vigas;
   - juntam-se as reações das vigas e dos pilares apoiados nas paredes e o peso próprio de cada parede;
   - de cima para baixo, a carga passa à parede de baixo (pelo comprimento comum) e à sapata corrida;
   - as forças horizontais de cada piso (vento e sismo) repartem-se pelas paredes de cada direção pela sua rigidez;
   - a sapata corrida passa a usar a carga real da parede.
3. ~~**A verificação pelo Eurocódigo 6**~~ (0.337.0):
   - a alvenaria do projeto vai nas definições da estrutura: grupo e resistência do bloco, argamassa, classe de
     execução e γM (a classe de execução entra pelo γM que lhe corresponde no Anexo Nacional);
   - cada parede verifica-se à compressão no topo, a meio e na base (Φ pela excentricidade e pela esbelteza;
     esbelteza ≤ 27) e ao corte no seu plano;
   - o resultado é OK / atenção / falha, com as notas, na janela da verificação e na memória de cálculo.
   - Fica para depois, se o dono pedir: ~~as paredes de betão armado (pelo EC2)~~ (0.342.0, secção própria abaixo), ~~a
     flexão para fora do plano (vento na fachada, sobretudo em paredes de enchimento)~~ (0.345.0, secção própria
     abaixo), e ~~a alvenaria por tipo de parede em vez de uma só para o projeto~~ (0.346.0, secção própria abaixo).

### Importação e exportação noutros formatos (pedido do dono do projeto, 2026-11-02)
«Importação e exportação a outros formatos.»

Hoje o programa:
- **abre e grava IFC**, e traz componentes de outro IFC;
- **liga** desenhos DXF/DWG e nuvens de pontos (XYZ, PTS, PLY, LAS, LAZ, E57); importa imagens e pontos de
  levantamento;
- **lê** IDS e BCF;
- **grava** PDF (vista, folhas, memória de cálculo), DXF (vista e CNC), PNG/SVG das folhas, imagem e render
  PNG/JPEG, Gaussian splat PLY, CSV das tabelas, BCF e HTML.

Falta o 3D para os outros programas, e trazer 3D de fora.
1. ~~**Exportar o 3D em GLB / glTF.**~~ (0.348.0) É o formato do ArqSynth Presentation, dos visualizadores na
   internet, do Blender, do Twinmotion e do SketchUp. Leva o modelo todo, ou só o que está à vista:
   - as peças agrupadas por pavimento ▸ categoria ▸ elemento, com nomes legíveis;
   - os materiais com a sua cor, transparência e acabamento (baço, brilhante, metal, vidro);
   - os dados de cada elemento (GlobalId, classe IFC, tipo, pavimento).

   Escreve-se em NumPy, sem biblioteca nova.
2. ~~**OBJ e STL:**~~ (0.349.0) o OBJ, com os materiais (MTL), para quase todos os programas 3D; o STL para imprimir
   maquetas em 3D, à escala escolhida.
3. ~~**Importar 3D:**~~ (0.351.0) SKP, 3DM, GLB/glTF, OBJ e STL como componente (mobiliário, equipamento), com uma
   peça por material na sua cor, colocado com um clique ou onde está no ficheiro; ou como esboço, com as faces inteiras.
4. ~~**DWG e SVG:** a vista em DWG, pelo conversor ODA que o programa já usa para importar, e em SVG~~ (0.369.0: no
   mesmo comando do DXF, «Exportar vista (DXF, DWG, SVG)…»; corrigido de caminho o SVG das folhas, cujas tramas o
   gerador do Qt deixava sair das paredes).
5. **A decidir com o dono:** formatos que pedem bibliotecas ou kits de outros fabricantes:
   - ~~SketchUp SKP~~ — **sim** (o dono, 2026-11-02); a exportação na 0.350.0. O kit oficial não existe para Linux;
     vai pelo OpenSKP (MIT), que lê do SketchUp 2013 aos atuais e grava no formato 2013–2020, que qualquer SketchUp
     abre. Cada elemento é um grupo com etiqueta e dados, e as faces vão inteiras;
   - ~~Rhino 3DM~~ — **sim** (o dono, 2026-11-02): rhino3dm (MIT, da McNeel); a exportação na 0.350.0, com camadas
     por pavimento e categoria;
   - FBX (o kit da Autodesk);
   - ~~USDZ, para a realidade aumentada no telemóvel (usd-core)~~ — **sim** (o dono, 2026-11-03); na 0.371.0, no
     «Exportar modelo 3D…»: as mesmas peças, materiais e dados do GLB, Y para cima, pousado no chão;
   - ~~Excel XLSX nas tabelas (openpyxl)~~ — **sim** (o dono, 2026-11-03); na 0.370.0, nas Tabelas, na Lista de
     armaduras, nas Quantidades da estrutura e na Lista de corte, os números como números.

### O que precisa corrigir e melhorar (documento do dono, 2026-11-02)
O documento «O QUE PRECISA CORRIGIR E MELHORAR» (OneDrive ▸ Documentos), com capturas; «depois faça essas
correções». Por ordem:
1. ~~**Paredes no 3D sem o núcleo à vista:**~~ (0.352.0) «no 3D aparecem os materiais de núcleo, que não faz sentido,
   se em planta não é assim». As esquinas exteriores mostravam a ponta da parede cortada pelas camadas; agora o reboco
   dá a volta, como na planta.
2. ~~**«+» nas pontas da parede escolhida:**~~ (0.353.0) um «+» em cada ponta; clicar num deles continua a desenhar
   a parede a partir dessa ponta, ligada a ela.
3. ~~**TAB, a edição rápida dos elementos:**~~ (0.354.0) com um elemento escolhido, o TAB abre junto dele uma janelinha
   com o tipo e as restrições e dimensões (na parede: comprimento, base e topo com os desvios, altura, perfil; na
   porta, na janela, na laje, no telhado: as suas). Nas ferramentas de desenho o TAB continua a fazer o que fazia.
4. ~~**Duplo clique numa parede: editar o perfil**~~ (0.355.0).
5. ~~**Telhado por blocos**~~ (0.356.0; o addon ArqSynth Modeler, no disco D:, não estava ligado, por isso parti do que
   o dono descreve e do que o editor já tinha): a altura de cada beirado e a inclinação de cada água já se mudavam lado
   a lado no editor de blocos, mas só lá se chegava pelas Propriedades. Agora o duplo clique no telhado abre o editor no
   bloco clicado, e há a «Altura do bloco» (o bloco todo para cima ou para baixo).
6. ~~**Linha de corte e símbolos:**~~
   - ~~escolhida, a linha de corte tem pegas para a esticar ou encurtar nas pontas~~ (0.358.0);
   - ~~uma seta para mudar o lado para onde olha~~ (0.358.0: o losango);
   - ~~a aparência das linhas e dos símbolos do corte editável~~ (0.360.0);
   - ~~um gerador de símbolos, onde o utilizador define como são os símbolos do programa: corte, vista, pormenor,
     etc.~~ (0.360.0: Anotar ▸ Símbolos…, com o corte, o alçado, o pormenor e o nível, cada um desenhado ao lado).
7. ~~**«Ambiente» em vez de «Sala»:**~~ (0.357.0) interior ou exterior; o programa de necessidades importado de um CSV
   ou texto; arrastar um nome da lista para dentro de um espaço da planta cria aí o ambiente com esse nome.
   ~~O gestor do programa no painel lateral (Ambientes): lista por piso com uso e área pretendida, colocar com um
   clique ou arrastando, verde / laranja / vermelho, zonas conflitantes por tipo de edifício, importar JSON de uma
   IA~~ (0.475.0, pedido do dono).
8. ~~**A porta em planta:**~~ (0.359.0)
   - o aro, a folha e os remates (guarnições) desenhados como peças separadas, não como uma massa só (em todas as
     escalas: a planta desenha a porta pelo seu desenho, não pelo corte do corpo 3D);
   - a porta desenhada fechada mostra a folha no aro e só a linha simbólica da abertura (o arco e uma linha fina); a
     aberta, a folha aberta e o arco, sem a folha fechada a dobrar;
   - no Caixilho Studio, «Planta…»: aberta ou fechada, a linha de abertura contínua ou tracejada, as guarnições e a
     soleira, com a planta desenhada ao lado;
   - a colocar: a pré-visualização mostra o lado (a face onde está o rato; F troca) e as dobradiças (Espaço troca),
     e um clique fixa-a — a 2.ª forma que o dono deu («ou na pré-visualização já escolher o lado e direção»);
   - com uma porta escolhida, duas setas ao lado dela: as dobradiças para o outro aro, a abertura para o outro lado.
9. ~~**As cotas temporárias**~~ (0.361.0; pedido a seguir, 2026-11-02): «em projetos mais complexos, com divisão
   interna, ao selecionar a parede aparece a cota da extensão da parede, mas não aparece a relação da parede com outras
   paredes».
   - ~~com uma parede escolhida, as cotas até às paredes vizinhas dos dois lados (as paralelas mais próximas, também
     as interiores)~~, e da ponta solta até à parede à frente;
   - ~~a escolha entre eixo a eixo e face a face (e trocar de uma para a outra com um clique)~~ (no separador verde ou
     na linha da cota);
   - ~~o aspeto das cotas mais próximo do addon do Blender~~ (o disco D: voltou: `tools/walls/wall_dimensions.py` e
     `ui/ui_utils._arch_dim_2d` do addon — tracejado, setas abertas, o número ao longo da linha, âmbar e verde).

10. ~~**A Linha fecha a face onde o contorno se fecha**~~ (0.372.0; o dono, 2026-11-03: «só cria o polígono se a
    geometria fechar no mesmo lugar que iniciou. Gostaria que ele criasse faces ao intersetar e fechar o polígono mesmo
    que não termine no ponto inicial»): acabar num ponto ou a meio de uma linha do que se desenhou, ou atravessá-lo,
    fecha a face do laço, como no SketchUp; o resto fica linha.
11. ~~**As cotas temporárias com o aspeto novo do addon**~~ (0.372.0; o dono: «a aparência da cota temporária eu queria
    como na imagem»; a versão mais recente do addon não está nesta máquina — partiu-se da imagem e da cópia de setembro
    em `E:\ArqSynth_CAD\arqsynth\referencia`): linhas azul-claro contínuas, o valor branco numa caixa escura pousada
    na linha, «↔» nas distâncias.

### Integração com o ArqSynth Presentation (pedido do dono do projeto, 2026-11-02)
«Preparar as cenas aqui e exportar para o ArqSynth Presentation de forma mais organizada e eficiente.»

O Presentation (arqsynth.com, a plataforma de apresentações da marca) recebe:
- plantas em PDF ou imagem, com pontos de interesse e panoramas 360° presos a eles;
- um modelo GLB com as peças em camadas;
- cenas: a câmara, os cortes e as peças visíveis;
- salas como zonas (nome, tipo, piso, unidade), ligadas por fluxos para os percursos.

Hoje faz-se tudo à mão, lá dentro. O dono vai fornecer o formato de entrada do Presentation. Até lá, os passos
abaixo são a proposta.

2026-11-02 (mais tarde), o dono: «examinar a última versão do Aplicativo de visualização e apresentação, e fazer uma
integração entre os dois … O utilizador pudesse fazer vários processos no ArqSynth BIM antes de enviar para o
Presentation: cenas 3D, cortes, animações, efeitos etc. podia ser preparada aqui no BIM e depois migrada para a
plataforma de apresentação». O código do Presentation está em `C:\BIM\arqsynth` (Next.js + Supabase; «a pasta do
projeto foi colocada dentro da raiz do programa»).

**O que o Presentation lê** (examinado 2026-11-03): cada projeto é um `_slides.json` no armazenamento; uma página 3D
(`Model3DData`, `lib/store/editor-store.ts`) tem o GLB (metros, Y para cima), as camadas (`Model3DLayer`, os nós pelo
nome que o three.js lhes dá), as cenas (`Scene3D`: câmara, estilo, ambiente com o sol, visibilidade, planos de corte,
transição, narração, efeito sol / construção / explosão, movimentos de câmara pelos `CAMERA_PRESETS`), as etiquetas
dos ambientes e o Passeio Virtual (pisos, zonas, fluxos). Não tem nenhuma entrada para outro programa (nem API, nem
importação de cenas): a integração precisa dos dois lados. O envelope de troca da marca já existe
(`arqsynth-ecosystem-handoff` 1.0, `lib/concept/integration.ts`, usado pelo Concept).

**A ponte:** um só ficheiro — o GLB do modelo com a descrição da apresentação dentro (`asset.extras.arqsynth`, o
envelope 1.0 com destino «presentation» e origem «ArqSynth BIM»). O Presentation já aceita GLB; ao importá-lo,
reconhece a descrição e traz as cenas, as camadas e o resto. A descrição diz o que o arquiteto quis (a câmara, o
corte, «uma órbita aérea»), e o importador faz os objetos dele com as suas próprias funções (`createScene3D`,
`createClipFromPreset`…): uma versão nova do Presentation não parte os ficheiros antigos.
1. ~~**O pacote (BIM):** Início ▸ Exportar ▸ Para o ArqSynth Presentation… — o GLB com nós de nomes únicos (os do
   three.js, previstos), as camadas por pavimento e categoria, e uma cena por vista 3D com nome (câmara, categorias à
   vista, caixa de corte → planos, estilo), por planta (vista de cima, corte horizontal à altura de corte, o pavimento)
   e por corte (o plano vertical); o sol pelo terreno (latitude, longitude, norte)~~ (0.362.0; uma camada por
   elemento, como o Presentation faz as suas, nas pastas «Categoria · Pavimento»).
2. ~~**O importador (Presentation):** `lib/presentation/bim-import.ts` (puro: a descrição → as camadas e as cenas, com
   as funções dele), o teste `scripts/test-bim-import.mts` como os outros, e a ligação ao carregar um GLB numa página
   3D. Num ramo próprio do git dele~~ (2026-11-03: `bim-import.ts`, a ligação no `model-3d-import-manager.ts`
   («Atualizar» junta ao trabalho da página), o teste com um GLB real do BIM (`scripts/fixtures/arqsynth-bim-casa.glb`,
   feito por `scripts/fixture_presentation.py`), a secção no GUIA_UTILIZADOR dele. Node 24 no WSL (`/opt/node24`):
   `npm run test:bim-import` 6/6, `tsc -p tsconfig.check.json` sem erros, eslint sem erros. Commit `f62c951` no ramo
   `integracao-arqsynth-bim`, feito de lado: o Presentation continua no `checkpoint/pre-harmonizacao-ui`, com os
   ficheiros por fazer commit na pasta como estavam.)
3. ~~**O painel Apresentação (BIM):** as cenas por ordem, a de entrada, a transição, o efeito (sol, construção,
   explosão), a narração (texto), as ocultas; miniaturas pela Imagem da vista~~ (0.363.0: Render ▸ Cenas da
   apresentação; também o tempo na cena; no Presentation, o importador lê as escolhas e sobe as miniaturas, no mesmo
   ramo `integracao-arqsynth-bim`. Num «Atualizar» as cenas que já lá estavam não mudam — trazer as mudanças do BIM
   para cenas já revistas no Presentation fica por decidir com o dono).
4. ~~**Movimentos de câmara (BIM):** por cena, um dos movimentos do Presentation (órbita, aproximação, recuo, voo,
   subida de fachada, os de interior), com o centro e o tamanho do edifício ou do ambiente, vistos no BIM antes~~
   (0.364.0: os 21, o tempo, o ambiente dos de interior, «Ver movimento»; no Presentation o importador fá-los com a
   biblioteca dele, no ramo `integracao-arqsynth-bim`).
5. ~~**Ambiente e efeitos:** o sol do dia e da hora (e a animação do dia ou do ano), a exposição; vidro, água e luzes
   pelos acabamentos dos materiais~~ (0.365.0: e o céu; «Ver sol» no 3D; a água como acabamento e material novos do
   BIM; no Presentation, ajustes de material da página).
6. ~~**Ambientes e passeio:** os ambientes como etiquetas (nome, área, número) e como zonas do Passeio Virtual (pisos,
   polígonos, centro, câmara); os fluxos entre eles pelas portas~~ (0.366.0: e as escadas entre pisos como ligações; o
   início por onde se entra; as duas escolhas no painel).
7. ~~**Plantas e panoramas:** as folhas como páginas de planta (PDF) com os ambientes como zonas~~ (0.367.0: o pacote
   ZIP e o botão «ArqSynth BIM» no Presentation); ~~panoramas 360° do render realista~~ (0.368.0: seis faces do Mitsuba
   juntas numa imagem equirretangular, guardadas com o projeto e listadas no painel; no Presentation, pontos 360° na
   planta do seu pavimento, atualizados ao importar outra vez sem tirar os feitos à mão). **Integração completa.**
   Fica por decidir pelo dono: se o «Atualizar» deve levar as mudanças do BIM também às cenas que já existem no
   Presentation (hoje leva as camadas e junta as cenas novas, sem mexer nas que lá se afinaram).
8. ~~**A aba «ArqSynth Presentation»** (o dono, 2026-11-08: «use as 2 colunas para replicar a experiência que se tem no
   ArqSynth Presentation… ao clicar na aba a tela muda a interface para a interface do ArqSynth Presentation»)~~
   (0.479.0): a última aba das vistas; as colunas do Presentation (páginas e cartões das cenas com os seis botões,
   Transição; a barra de ícones com Camadas e os olhos, Cenas 3D, Ambiente, Etiquetas, Imagens, Efeitos, Passeio) e os
   seus comandos sobre o 3D (Criar cena, Persp / Orto, FOV, cadeado, T/E/F/D/B/Trás, Renderizado · Auto, sol); cada
   cena leva a câmara, o modo, a qualidade, a oclusão e as camadas escondidas; no Presentation o importador lê o
   cadeado, a qualidade e a oclusão. ~~O ícone na barra da esquerda e sem o painel que dividia a coluna~~ (0.480.0,
   o dono: «não quero essa divisão na coluna… não vi ainda a aba de ArqSynth Presentation na esquerda»: o painel
   Apresentação da 0.363 saiu; Render ▸ Cenas da apresentação abre a interface). ~~Como a versão nova do Presentation~~
   (0.481.0, o dono: «faça de acordo com o novo… o cubo de navegação devia continuar o mesmo do programa… apenas quero o
   ícone»: a aba só existe enquanto a interface está aberta; a câmara na barra de parâmetros, «Renderizado · Auto» e o
   sol no rodapé, «+ Criar cena» no rodapé fixo da coluna, o leitor das cenas por baixo do 3D, «Página final»; o cubo e
   a navegação do BIM). Ficam para depois, se o dono quiser:
   - **Capa, Texto e Concept** feitos no BIM (o pacote só leva o Modelo 3D e as plantas; o Presentation teria de ler
     páginas novas);
   - os separadores do Presentation que o BIM ainda não prepara: Biblioteca, Material, Textos, Cortes (planos de corte
     por cena), Diagramas, Fluxos e zonas, Áudio, Notas;
   - a «Página final» do Presentation.
9. **Preparar no BIM o que o Presentation faz** (o dono, 2026-11-09, depois de importar o pacote no Presentation local:
   «o que é importante fazer no BIM é criar cenas… o BIM ainda não tem animação de transição entre as cenas como
   acontece no AP, não tem ainda ferramentas de cortes, passeio virtual… é importante criar cortes, ter diagramas,
   etiqueta, efeitos»; e «há 2 camadas de janela, uma é window (vidro) e outra janela (estrutura), mas poderia ser
   apenas 1»). Por passos, um por versão:
   1. ~~**Uma camada por janela**~~ (0.483.0: o vidro e a água de cada elemento num nó próprio do GLB, com nome,
      dentro da camada do elemento — o Presentation dava ao vidro dono próprio pelo material e fazia dele «Window»).
   2. ~~**Transições animadas entre as cenas**~~ (0.483.0: um clique num cartão ou o leitor voam até à cena no tempo
      da sua chegada, com a lente, como o «Voo suave» do Presentation; «Corte seco» chega de uma vez).
   3. ~~**Cortes** (o separador «Cortes» do Presentation): por cena, planos de corte horizontais (à altura escolhida) e
      verticais (por um eixo e uma posição), vistos no 3D do BIM enquanto se escolhem; vão nas cenas como
      `section.planes` (o importador do Presentation já os lê)~~ (0.484.0: Horizontal, Vertical X, Vertical Z, até 6,
      com a posição exata, inverter e remover; guardados ao Criar/Atualizar). Ficam por fazer o plano inclinado e a
      caixa de corte própria da cena (hoje vai a da vista 3D com nome), e o aspeto do corte do Presentation (cor,
      padrão, «Sólido / Poché / Categoria»).
   4. **Etiquetas** (o separador «Etiquetas»): texto num ponto do modelo — além das dos ambientes, que já vão —, vistas
      no 3D; vão como etiquetas da página 3D (o importador do Presentation passa a lê-las).
   5. **Efeitos**: ver no BIM, antes de exportar, a construção peça a peça e a explosão como o Presentation as toca (o
      sol do dia e o movimento de câmara já se veem).
   6. **Diagramas** (o separador «Diagramas»): volumes, setas e zonas coloridas sobre o modelo; vão para a página 3D
      (o importador do Presentation passa a lê-los).
   7. **Passeio virtual**: ver no BIM as zonas dos ambientes e os caminhos pelas portas e escadas que vão para o
      Passeio do Presentation, e percorrê-lo no 3D (a ferramenta Caminhar).

### Alvenaria por tipo de parede (decidido pelo dono do projeto, 2026-11-02)
«Alvenaria por tipo.» Até aqui a alvenaria do cálculo (os blocos, o seu grupo, a sua resistência fb, a argamassa)
era uma só para o projeto, na janela das Ações e materiais. Num edifício convivem tijolo furado nas fachadas, blocos de
betão na cave, tijolo maciço num muro: cada tipo de parede passa a poder ter a sua. (0.346.0: o passo.)
1. ~~**A alvenaria no tipo**~~ (uma versão):
   - em Gerenciar ▸ Tipos, num tipo de parede: «Alvenaria própria deste tipo» — os blocos, o grupo, o fb e a
     argamassa; desligada, a do projeto (como até aqui). O γM fica no projeto: vem da classe de execução da obra;
   - guarda-se no IFC, nos parâmetros do tipo (o IfcWallType), e acompanha as suas paredes;
   - a verificação pelo EC6 (compressão, corte e flexão pelo vento) usa a de cada parede; as notas dizem os blocos e
     de onde vêm (do tipo ou do projeto); o resumo e a memória de cálculo mostram as de cada tipo.

### Flexão das paredes para fora do plano (decidido pelo dono do projeto, 2026-11-02)
«Flexão das paredes.» O vento empurra as fachadas: cada pano de alvenaria tem de levar essa pressão até aos seus
apoios (a laje de baixo e a de cima, os pilares e as paredes que o travam nos lados). Pelo Eurocódigo 6 (NP EN
1996-1-1, 6.3 e Anexo E), para pré-dimensionamento, nas paredes de alvenaria exteriores — as resistentes e, sobretudo,
as de enchimento, que até aqui não eram verificadas. (0.345.0: o passo.)
1. ~~**A verificação**~~ (uma versão):
   - as paredes de fachada são as exteriores do modelo (o IsExternal, que o programa já calcula pelas salas), de
     alvenaria;
   - o vento de cálculo em cada parede: 1,5 × qp(z) no seu topo × o coeficiente das paredes — 1,1 a meio da fachada
     (pressão +0,8 e sucção interior −0,3) e 1,4 perto das esquinas (sucção −1,2 da zona A e pressão interior +0,2);
     as janelas e portas passam a sua parte ao pano à volta delas;
   - os apoios de cada pano, vistos no modelo: a base sempre; o topo se tem uma laje, viga ou cobertura em cima; cada
     lado se lá está um pilar ou outra parede (contínua ou de través);
   - a resistência à flexão da alvenaria (fxk1 e fxk2, valores recomendados do quadro 3.4, pelos blocos e pela
     argamassa do projeto), a de fxk1 aumentada pela compressão vertical permanente (6.3.1(3));
   - o momento pelo método das linhas de rotura de que vêm os coeficientes do Anexo E, com os bordos apoiados
     simplesmente (do lado seguro) e a relação ortogonal μ; quando a flexão não chega e a parede está presa em cima,
     o efeito de arco vertical (6.3.2: qlat = fd (t/h)², até h/t = 25);
   - o resultado OK / atenção / falha, com as notas, na janela da verificação e na memória de cálculo, para as
     resistentes junto ao resto da sua verificação e para as de enchimento numa linha própria.

### Render realista (decidido pelo dono do projeto, 2026-11-01)
«Render realista.» O motor é o Mitsuba 3 (path tracing no processador, licença BSD; o «sim» do dono à biblioteca nova
a 2026-11-01): a luz ressalta nas superfícies (iluminação global), sombras suaves, vidro, céu físico com o sol. O
render corre num processo à parte — o programa continua a responder, a imagem vai aparecendo e afinando, pode-se
parar a meio. A imagem da vista (0.329) continua a ser a rápida, do motor da vista 3D. (0.343.0: os três passos.)
1. ~~**O motor e a cena:**~~ o modelo como se vê na vista 3D (o que está à vista, a câmara dela), cada face com a cor
   do seu material (ou da sua categoria), o vidro transparente; o céu físico e o sol do estilo de vista; **Render ▸
   Render realista…**: o tamanho e a qualidade (rascunho, normal, alta); a janela do render com a imagem a afinar,
   Parar e Guardar (PNG / JPEG).
2. ~~**Os acabamentos e as luzes:**~~ cada material com o seu acabamento (baço, acetinado, brilhante, metálico,
   vidro, vidro fosco), pela sua categoria e escolhido no editor de materiais; as luminárias do modelo acesas
   (interiores e noite).
3. ~~**O sol do sítio e a revisão:**~~ o sol pela localização do terreno, o dia e a hora; a exposição; os interiores
   (mais ressaltos, menos pontos de ruído — o vidro deixa passar o sol, e um filtro do grão guiado pelas normais,
   profundidades e cores); renders de ensaio de fora e de dentro, com capturas e tempos.

### Paredes de betão pelo Eurocódigo 2 (decidido pelo dono do projeto, 2026-11-01)
«Paredes de betão EC2.» As paredes resistentes já entram no modelo analítico e já recebem as cargas (0.335–0.336),
mas só as de alvenaria são verificadas (EC6, 0.337); as de betão ficam de fora. Pré-dimensionamento, como o resto.
(0.342.0: os dois passos.)
1. ~~**A verificação**~~ (NP EN 1992-1-1, por metro de parede, como um pilar de 1 m × t):
   - tipos novos no catálogo: paredes de betão armado de 15, 20 e 25 cm (a camada «Estrutura» toda a espessura);
   - a compressão no topo, a meio e na base com a excentricidade das lajes e a mínima (6.1(4)), a esbelteza com
     l0 = h (presa no topo e na base) e, numa parede esbelta, os efeitos de 2.ª ordem (curvatura nominal, 5.8.8);
   - a armadura vertical nas duas faces pelo diagrama N–M, entre 0,002 Ac e 0,04 Ac, espaçada no máximo 3t e 40 cm
     (9.6.2); a horizontal, pelo menos 25 % da vertical e 0,001 Ac, espaçada no máximo 40 cm (9.6.3);
   - o corte no plano: VRd,c com a compressão (6.2.2), e a armadura horizontal como armadura de corte quando não
     chega (6.2.3), com VRd,max;
   - o resultado na janela da verificação e na memória de cálculo, como as outras.
2. ~~**As armaduras no modelo**~~ (e o alçado armado): as malhas vertical e horizontal nas duas faces, interrompidas nos vãos e com dois
   varões de reforço de cada lado deles; os arranques da sapata (ou da parede de baixo) com o comprimento de
   emenda; a lista de armaduras e as quantidades (betão, cofragem das duas faces, aço).

### Tema escuro (decidido pelo dono do projeto, 2026-11-01)
«Tema escuro.» As cores são as do protótipo do Caixilho Studio que o dono trouxe a 2026-10-29 (fundo #17191c, barras
#111316, linhas #2a2e34, texto #dde1e6, destaque âmbar #f0b44c, seleção azul #5b9cff) — «quando criarmos o tema
escuro, vai ser assim». Escolhe-se em **Visualizar ▸ Tema**, fica guardado no computador (não no projeto) e muda na
hora, sem reabrir o programa. Nenhuma cor de tema fica escrita no meio do código: todas saem de `ui/theme.py`.
1. ~~**A base, as peças da janela e os ícones**~~ (0.338.0):
   - `ui/theme.py` com as duas paletas; as janelas normais do Qt (diálogos, tabelas, campos, listas, menus, barras de
     deslocamento, dicas) seguem o tema pela paleta do estilo Fusion;
   - o cabeçalho das disciplinas, a fita e o separador contextual, a barra contextual, a barra dos módulos, o painel
     de propriedades, os balões, o painel da ajuda e o rodapé, com as cores do tema;
   - os ícones: no escuro, os traços escuros passam a claros e os fundos brancos a cinzento-escuro; as cores (o azul,
     o amarelo, os materiais) ficam. Todos de uma vez, e trocam na hora com o tema.
2. ~~**As janelas com cores próprias**~~ (0.339.0; os desenhos dentro delas ficam em papel branco): o Caixilho Studio no escuro do protótipo; os editores de materiais, padrões,
   tipos, coberturas e grades; as janelas da estrutura (OK / atenção / falha legíveis no escuro); as notas cinzentas
   e as dicas azuis das outras janelas.
3. ~~**A revisão**~~ (0.340.0: 37 janelas e painéis medidos, o rodapé, o título das propriedades e os botões de cor
   corrigidos): uma varredura que abre cada janela e painel no tema escuro, mede o contraste do texto com o fundo e
   corrige o que se lê mal; capturas de cada uma.
- As vistas (3D, plantas, cortes, alçados, folhas) ficam como estão: o papel é branco, como no Revit, onde o tema da
  interface e o do desenho são coisas separadas. Um fundo escuro nas vistas fica para depois, se o dono pedir.

### Fundo escuro nas vistas (decidido pelo dono do projeto, 2026-11-01)
«Fundo escuro nas vistas.» Como o «tema do desenho» do Revit, é uma escolha à parte do tema da interface: **Visualizar
▸ Tema ▸ Vistas escuras** (liga e desliga), guardada no computador, na hora. As vistas 3D, as plantas, os cortes e os
alçados ficam com o fundo escuro, e o que é neutro inverte-se: as linhas pretas, o cortado, as cotas e os textos passam
a claros; as faces brancas e cinzentas (as cores das categorias) passam a escuras, para as linhas se continuarem a ver
sobre elas. As cores ficam como estão: os materiais num estilo de vista realista, o vidro, o tijolo, os sistemas, as
fases, a seleção azul, os eixos vermelho, verde e azul. As folhas continuam em papel branco, e o que se exporta (PDF,
DXF, a imagem da vista com fundo branco ou transparente) sai sempre como em papel.
(0.341.0: os três passos; no 3D o modelo fica com as suas cores, como no Revit — só as plantas, cortes e alçados se
invertem.)
1. ~~**A base**~~: a escolha; o fundo; as arestas e as faces dos elementos e dos esboços; o cortado (poché); a grelha do
   chão; as cotas, os textos, as marcas dos cortes e dos níveis, os eixos estruturais, as guias.
2. ~~**O resto do que se desenha nas vistas**~~: as tramas do cortado, os símbolos das plantas, as salas, o terreno, as
   imagens e os desenhos CAD, os pré-visionamentos, as dicas e as cotas temporárias das ferramentas; a imagem da vista
   com fundo branco ou transparente feita em papel.
3. ~~**A revisão**~~: uma varredura que mostra cada tipo de vista com cada estilo de vista nas vistas escuras e mede se as
   linhas e os textos se distinguem do fundo; capturas.
- Continuam à espera do dono: o documento da Reference View, o catálogo das dobradiças por marca, o disco D: (comparar
  o mobiliário com o addon), a confirmação no Revit elemento a elemento e o nome definitivo do programa.

### Cotas como no Revit (pedido do dono do projeto, 2026-11-05)
«Agora vamos turbinar a aba documentação. As cotas precisam de opções mais robustas para satisfazer às necessidades do
arquiteto e engenheiro. Quero cotas automáticas, para cotar o interior com um clique; a mesma coisa para a cotação
externa; e vamos ter também cotação manual — mas como no Revit. E um motor de edição da aparência da cota.» E, logo a
seguir: «precisa ter opção de cotar acabamento externo, núcleo da parede, eixos da parede etc.»
Até aqui (0.114–0.193): a ferramenta Cota (dois pontos e a posição, em cadeia), «Cotar paredes / fachadas / ambientes»
de uma vez para o pavimento ativo (as fachadas só nos quatro lados N/S/E/O), e um estilo pequeno (altura do texto, marca,
unidade, decimais, tipos com nome). Cada cota desenhava-se em quatro sítios com medidas próprias (ecrã, PDF, SVG, DXF).
1. ~~**O motor da aparência**~~ (0.398.0) (tipos de cota como as propriedades de tipo do Revit): um só desenhador de cotas
   (`core/dim_layout.py`) para o ecrã, o PDF, o SVG e o DXF — o ecrã à escala da vista, como fica no papel; marcas
   (traço oblíquo fino e grosso, setas aberta, fechada e cheia, ponto cheio e vazio, nenhuma) e o seu tamanho e
   espessura; a linha de cota (espessura, cor, prolongamento para lá das linhas de chamada); as linhas de chamada
   (afastadas do elemento ou de comprimento fixo, o afastamento, o prolongamento); o texto (letra, altura, largura,
   negrito, itálico, sublinhado, afastamento da linha, por cima ou a meio da linha, alinhado com a linha ou sempre
   horizontal, fundo opaco, cor); as unidades (m / cm / mm, decimais, arredondamento, símbolo, milímetros em expoente
   como «2,47⁵», prefixo e sufixo); a altura dos vãos por baixo da largura; o texto das cotas iguais («IG»); os valores
   que não cabem saem para cima com uma linha de chamada. **Anotar ▸ Tipos de cota…**: a lista dos tipos (duplicar,
   mudar o nome, apagar, o tipo por omissão), as propriedades por grupos e uma amostra em papel que muda a cada valor.
2. ~~**As referências das paredes e as cadeias:**~~ (0.398.0–0.399.0) a «preferência» do Revit em todas as cotas — eixo da parede, faces de
   acabamento, face de acabamento exterior / interior, faces do núcleo, eixo do núcleo (o núcleo = as camadas
   «Estrutura» do tipo, senão a mais grossa) —; uma cadeia de cotas é uma só cota com várias linhas de chamada (escolhe-se
   inteira, move-se inteira), cada ponta presa à face ou eixo da sua parede: a parede mexe-se, a cota segue.
3. ~~**Cotas exteriores num clique**~~ (0.399.0) (Anotar ▸ Cotas exteriores): passar o rato sobre o edifício mostra-as, um clique
   pousa-as à volta de todo o pavimento, em qualquer direção (não só N/S/E/O); as filas por ordem de fora para dentro —
   o total, os cantos (saliências e reentrâncias), as paredes interiores que chegam à fachada, os vãos (as ombreiras ou os
   eixos); quais filas, a distância ao edifício e entre filas, e a referência das paredes na barra contextual.
4. ~~**Cotas interiores num clique**~~ (0.400.0) (Anotar ▸ Cotas interiores): um clique dentro de um compartimento — com Ambiente ou
   só fechado por paredes — cota-o: a largura e a profundidade de face a face; «corrida» (a linha atravessa o edifício
   pelo ponto do clique: cada compartimento e cada espessura de parede, de fora a fora); «com os vãos» (ao longo de cada
   parede do compartimento, os vãos e as paredes que chegam). Um botão para todos os compartimentos do pavimento.
5. ~~**Cota manual como no Revit**~~ (0.401.0) (C): clicar as referências umas a seguir às outras (faces, eixos e núcleo das paredes,
   ombreiras e eixos dos vãos, eixos estruturais, cantos e pontos) — a referência sob o rato acende-se, o Tab passa à
   seguinte no mesmo sítio —, e um clique no vazio pousa a cadeia; «paredes inteiras» (um clique numa parede dá as duas
   faces, os vãos e as paredes que a cruzam); alinhada, linear (horizontal / vertical) e angular.
6. ~~**Editar as cotas como no Revit**~~ (0.402.0) (Selecionar): pegas para mover a linha da cadeia, mover o texto, levar uma linha de
   chamada para outra referência; botão direito: apagar uma linha de chamada, acrescentar uma; «IG» iguala os
   segmentos (move as paredes / vãos do meio) e escreve IG; com um elemento escolhido, o valor das cotas presas a ele
   clica-se e escreve-se para o mover; duplo clique no valor: substituir pelo texto, prefixo, sufixo, texto por cima e
   por baixo.
7. ~~**A revisão:**~~ (0.402.0) capturas no WSL de cada passo (no ecrã e no PDF), a bateria GUI completa, o GUIA.
   (Unitários 779/779; janela 549 verificações, 3 refeitas sozinhas e passadas — 2 eram um teste que deixava a
   ferramenta em «eixos»; o desenho das cotas medido e acelerado: 128 cotas 0,28 → 0,06 s.)

### Propriedades e tipos para todos os elementos (pedido do dono do projeto, 2026-11-05)
O dono, com a captura das propriedades de uma superfície paramétrica: «vamos arrumar o painel de propriedades para
tornar visualmente mais interessante… pode ser mais bem organizado, destacando os títulos colapsáveis e com trama para
melhorar a distinção de parâmetros. Quero todos os elementos IFC tenham tipo, guardado e aplicado a outros elementos.»
Até aqui têm tipos (TypeSpec do catálogo, escolhidos no topo do painel e editados no editor de tipos) as paredes, lajes,
pilares, vigas, sapatas, portas, janelas, tubos, condutas e coberturas; as escadas, rampas, guardas, tetos e outros só
mostram o tipo; a superfície paramétrica, o piso (acabamento), os móveis e outros não têm.
1. ~~**O painel Propriedades:**~~ (0.414.0) os títulos dos grupos numa faixa própria, em negrito e mais altos, recolhíveis com um
   clique em todo o título; os subgrupos (Forma, Nervuras…) numa faixa mais leve; as linhas em faixas alternadas
   («trama»); os botões que não cabem na coluna dos valores em linha inteira. Cores só do tema, nos dois temas.
2. ~~**Tipos guardados e aplicados — o mecanismo e a superfície paramétrica:**~~ (0.414.0) «Guardar como tipo…» (nome) faz um tipo
   do elemento (IfcTypeObject da classe dele, os valores do tipo num pset); no topo do painel, a lista dos tipos dessa
   natureza: escolher um aplica-o ao elemento — ou a todos os escolhidos —; «Atualizar o tipo» leva as mudanças de um
   elemento ao tipo e a todos os elementos desse tipo (como «Editar tipo» no Revit). Na superfície, o tipo é a forma
   (operação, divisões), os modificadores, a construção e o uso — não as curvas, que são de cada uma.
3. ~~**Os outros elementos sem tipo**~~ (0.415.0): piso, teto, revestimentos, escadas, rampas, paredes cortina e móveis
   com tipos guardados; as guardas com os seus tipos no cabeçalho; luminárias, terminais, equipamentos e perfis com o
   tipo do catálogo no cabeçalho (só mostrado). Ficam sem tipo, se o dono os quiser: elevador, calha, nicho, terreno,
   ambientes e os aparelhos de catálogo (trocá-los no lugar pede refazer o corpo).

### Aprender com o Hestia (pedido do dono do projeto, 2026-11-06)
«Encontrei um clone do Revit que está com boa performance e gráfico muito interessante… gostei de poder simplesmente
selecionar e pegar qualquer elemento e arrastar para reposicionar. Gostei da verificação de acordo com a legislação, mas
vamos fazer isso melhor. Gostei do gráfico da parede em planta, do tipo e editar tipo, do painel de propriedades, da
navegação… podemos personalizar alguma coisa do nosso jeito.» O Hestia (github.com/engdennylsonsantos-cloud/Hestia,
brasileiro, licença MIT) é um BIM no navegador (TypeScript, WebGL2/WebGPU). Estudado o código de 2026-11-05 (commit
9f0192e). A MIT deixa aproveitar ideias e algoritmos; o que se traduzir de perto leva o aviso de autoria MIT num
ficheiro de terceiros.

O que se viu, ponto a ponto (Hestia → ArqSynth 0.415):
- **Arrastar:** no Hestia escolhe-se e depois arrasta-se, só na planta; as paredes ligadas esticam, portas e janelas
  deslizam na parede, um só Ctrl+Z. Não há cotas nem medida escrita durante o arraste, nem móveis, nem 3D. No ArqSynth,
  arrastar com o Selecionar desenha a caixa (`tools/select.py`); mover é a ferramenta Mover (ponto base → destino).
- **Parede em planta:** as espessuras das linhas estão em mm de papel por escala (1:50 / 1:100 / 1:200) e passam para o
  ecrã a cada zoom — o corte sai grosso, as camadas finas; o fundo é a cor do material clareada para o papel (a
  alvenaria salmão), com a trama por cima; trama e linhas das camadas somem quando a parede fica fina demais no ecrã; o
  pormenor dos vãos segue o zoom; «linhas finas» só no ecrã. No ArqSynth o recorte e as junções já são do mesmo nível
  (junção pelo material, 0.320; níveis de detalhe), mas no ecrã todas as linhas têm 1–1,5 px e o corte é um cinzento
  escuro fixo (`render/batches.py`, `POCHE_COLOR`): as canetas só existem no papel.
- **Tipos:** o diálogo edita um rascunho (Aplicar / OK / Cancelar, cada um um Ctrl+Z), com o corte da parede ao vivo
  (núcleo marcado, espessuras, total), «usado em N paredes», Duplicar a partir do rascunho e Apagar bloqueado com
  «Substituir por…». O ArqSynth tem o editor com camadas e contagem (`ui/type_editor.py`), sem corte ao vivo.
- **Propriedades:** os valores que vêm do tipo levam um selo «tipo»; as exceções por elemento têm «usar o valor do
  tipo»; os campos aceitam contas (3,50+0,15) e mudam com as setas e a roda. O ArqSynth já tem procura no painel (o
  Hestia não), multi-seleção e a vista sem seleção; não aceita contas (`core/units.py`, `parse_length`).
- **Navegação:** equivalente; do Hestia vale só o zoom no 3D que pára antes da primeira superfície.
- **Legislação:** no Hestia só escadas (Blondel, espelho, cobertor, patamares, altura livre), rampas (tabela da NBR 9050
  editável no tipo, com «norma conferida») e portas / janelas dentro do diálogo do tipo. Os limites estão quase todos
  escritos no código, quase nenhuma mensagem cita o artigo, não há relatório nem «ignorar», e o lote / zoneamento ficou
  no papel. Os avisos vivem num botão do rodapé («2 avisos») com «Ir para». O ArqSynth não verifica legislação (o 2h+p
  da escada só se mostra) nem tem uma lista de avisos permanente.
- **Desempenho:** o ArqSynth já está medido e bem (57 imagens/s, escolher 1,6 ms, refazer uma parede 24 ms). Do Hestia
  valem uma camada própria na placa para a pré-visualização (o arraste não mexe no resto) e um contorno provisório logo
  ao largar, com o exato a seguir.

Passos propostos (a ordem decide-a o dono):
1. ~~**Arrastar para mover, à nossa maneira:**~~ (0.427.0: com o Mover por baixo — snaps, distância escrita, Shift,
   Ctrl ao largar copia, Esc, paredes ligadas esticam, portas e janelas deslizam na parede; lajes, pisos, coberturas e
   terreno pela borda na planta; «Arrastar elementos» na barra da seleção. Por fazer: as cotas temporárias aos
   vizinhos durante o arraste, Alt para soltar as paredes ligadas, o fantasma das paredes que esticam.) Com o
   Selecionar, carregar num elemento — escolhido ou não — e arrastar
   move-o, na planta e no 3D (no plano de trabalho); a partir do vazio continua a ser a caixa; mais de 6 px conta como
   arraste. O ponto agarrado prende-se aos snaps e o destino também; cotas temporárias aos vizinhos durante o arraste e
   a distância pode escrever-se; as paredes ligadas acompanham (Alt solta-as); portas e janelas deslizam na parede, com
   fantasma, sem sair dela; Ctrl copia; Shift prende a ortogonal; Esc cancela; um só Ctrl+Z. Lajes, pisos e terreno
   agarram-se pela borda na planta (para a caixa não os levar sem querer); interruptor «Arrastar elementos» na barra da
   seleção, como no Revit.
2. ~~**Paredes em planta no ecrã como no papel:**~~ (0.428.0: as canetas do estilo gráfico em mm de papel, pela escala
   da vista e pelo zoom — o contorno do corte com a de corte, mínimo 2 px, as costuras entre camadas e a trama com a da
   trama, mínimo 1 px, máximo 6 px; a trama sai quando 1 mm de papel tem menos de 2 px, as costuras com menos de 1;
   «Linhas finas» no Visualizar. Por fazer: o fundo do corte na cor do material clareada — hoje é o do estilo gráfico
   (branco na alvenaria), que o dono pode mudar em Estilos gráficos; as arestas vistas para lá do corte com a caneta
   «vista».) As canetas em mm por escala, convertidas a cada zoom (corte grosso,
   camadas finas, mínimo 1 px); o fundo do corte na cor do material clareada, como na folha, em vez do cinzento fixo,
   com a trama por cima; trama e linhas das camadas somem quando a parede fica fina demais; o pormenor dos vãos pelo
   zoom; botão «Linhas finas» (só no ecrã). Cores do tema, papel branco.
3. ~~**Editar tipo com corte ao vivo:**~~ (0.429.0: o corte desenhado — cor e trama do material, núcleo, espessuras,
   total, exterior / interior —, OK / Cancelar / Aplicar, Onde se usa, apagar em uso substituindo por outro num só
   Ctrl+Z; Duplicar já partia do rascunho.) Na parede, laje, piso e cobertura, o corte das camadas desenhado no editor (face
   exterior / interior, núcleo, espessuras, total), que muda a cada valor; rascunho com Aplicar / OK / Cancelar;
   Duplicar a partir do rascunho; tipo em uso: «Substituir por… e apagar»; «Onde se usa» (escolhe e enquadra).
4. ~~**Propriedades mais rápidas:**~~ (0.430.0: contas em `parse_length` — nas Propriedades, nos dados IFC e nas
   Medidas; ↑ ↓ e a roda nos comprimentos; o selo «tipo» que abre o tipo; «↺» para voltar ao valor do tipo nos dados
   IFC. As áreas e volumes já não atrasavam o clique.) Selo «tipo» nos valores do tipo (clique → Editar tipo); exceções por elemento com
   «usar o valor do tipo»; contas nos campos (3,50+0,15; 2*1,20; com unidades); setas ↑↓ e roda a ajustar; áreas e
   volumes calculados sem atrasar o clique.
5. ~~**Avisos do modelo sempre à vista:**~~ (0.431.0: o pacote «Modelo» no Verificador — paredes sobrepostas,
   elementos repetidos, ambientes não fechados, vários ambientes no mesmo espaço; no rodapé, na faixa, no painel com Ir
   para e Exceção com nota, na ficha; desligável. **A secção «Aprender com o Hestia» fica completa (0.427–0.431).**)
   No rodapé «⚠ 3 avisos» / «✓ sem avisos»; a lista por gravidade e categoria;
   «Ir para» abre a planta, enquadra e escolhe todos os elementos envolvidos; «Ignorar, com nota»; exportar. Calculados
   em fundo depois de cada edição.
6. ~~**Verificação regulamentar**~~ (0.416–0.426: o Verificador, os seus 9 passos) — desenhada a seguir, na secção «O Verificador» (o dono, a 2026-11-06: Portugal e
   Cabo Verde primeiro, com lugar para outros países).

### O Verificador — legislação e boas práticas a vigiar o projeto (pedido do dono do projeto, 2026-11-06)
«Vamos seguir a legislação portuguesa e o código técnico de Cabo Verde, mas quero que tenha espaço para outras
legislações, pois o programa pode ser utilizado noutros lugares. Quero um sistema de verificação melhor e mais
abrangente. Enquanto o arquiteto estiver a fazer o seu projeto, esse sistema deve vigiar e verificar. Por exemplo, o
arquiteto faz uma sala; quando colocar os ambientes, o verificador entenderá a tipologia — por exemplo um T2 — e pode
verificar a área da sala; se for inferior à legislação, coloca uma mensagem no rodapé com fundo vermelho de alerta.
É bom verificar a largura da escada, a inclinação da rampa, a largura da porta, o pé-direito, as áreas dos
compartimentos, a ventilação e a iluminação… incompatibilidade de material e outras coisas.»

**O que a legislação obriga o sistema a saber fazer** (lido nos textos, 2026-11-06):
- **Portugal:** o RGEU continua em vigor. O DL 10/2024 (Simplex urbanístico) revogava-o a 1 de junho de 2026; o DL
  108/2026 adiou a revogação até entrar o diploma das regras técnicas dos edifícios; o Despacho 12528/2026 (15 de
  outubro) só criou a equipa que prepara o Código da Construção. Quando este chegar, troca-se o pacote, não o programa.
  O DL 10/2024 também mexeu no art. 66.º (áreas). Acessibilidades: DL 163/2006 e alterações; incêndio: SCIE; térmica:
  REH. Os textos consolidados do Diário da República não se leem fora do navegador: os valores de Portugal tiram-se do
  texto oficial com o dono.
- **Cabo Verde:** Código Técnico da Edificação (CTE), Portaria conjunta n.º 4/2012 (impressa «4/2011»), B.O. I Série n.º
  2, de 12 de janeiro de 2012, ao abrigo do DL 18/2011; não achei revisões depois (confirmar com o dono). Lido o texto
  todo. Mostra os tipos de regra que o motor tem de saber — e não basta comparar números:
  - limites por uso do compartimento: pé-direito de habitação, mais baixo em vestíbulos, corredores, instalações
    sanitárias e arrumos; em tetos inclinados, o mínimo em 80 % da área (art. 27.º);
  - tabelas pela tipologia: áreas mínimas da sala, cozinha, quartos e suplementos (art. 40.º, Anexo I — no T2 a sala
    pede 14 m²) e a área bruta do fogo, com regra própria para medir o fogo (art. 40.º n.º 4 e n.º 10, Tn = 1,2 × Ahab);
  - figuras que têm de caber: um círculo na sala, um quadrado nos quartos, um cilindro livre na cozinha, a profundidade
    face à fachada com vãos (art. 41.º); um círculo de 1,50 m no patamar que as portas não varram (art. 35.º);
  - proporções: envidraçado contra a área útil a até 6 m do vão (art. 76.º); obstáculo fronteiro a mais de metade da
    sua altura (art. 77.º); horas de sol direto no compartimento maior (art. 78.º);
  - presença de equipamento: lava-loiça, bancada e exaustão na cozinha (art. 42.º);
  - dependências do edifício: a largura da escada comum muda com a altura do edifício (art. 35.º); elevador a partir de
    certo número de pisos (art. 37.º); o nível da intervenção em edifício existente, I a IV (art. 6.º);
  - materiais e espessuras: espessuras mínimas das paredes pelo material e pela função (art. 92.º, Anexo II);
    pavimentos de locais húmidos e em contacto com o solo (arts. 98.º–100.º);
  - lei supletiva: no que o CTE não cobre aplica-se a regulamentação portuguesa (art. 4.º); os municípios
    pormenorizam (art. 5.º); exceções por vontade expressa do dono de obra (art. 27.º n.º 7).

**Como funciona — cinco peças:**
1. **O leitor (perceber o projeto).** O uso de cada ambiente — sala, quarto, cozinha, instalação sanitária, corredor,
   vestíbulo, arrumos, tratamento de roupa, varanda, garagem… — pelo nome e pelo que lá está dentro (sanita ou duche →
   instalação sanitária; lava-loiça e bancada → cozinha; cama → quarto, cama de casal → quarto de casal), mostrado nas
   Propriedades com o porquê («Quarto — pelo nome e pela cama») e corrigível. O **fogo**: os ambientes ligados por portas
   a partir de uma porta de entrada (para o exterior ou para um espaço comum); numa moradia, um fogo. A **tipologia** Tn
   pelo número de quartos de dormir (CTE art. 40.º n.º 1), viva, na etiqueta da planta e nas Propriedades. O
   **edifício**: uso, altura, número de pisos, obra nova ou intervenção (nível I–IV). Nos elementos: largura útil da
   porta (o vão livre com a folha a 90°), área envidraçada e de ventilação de cada janela e se dá para o exterior,
   espelho, cobertor, largura e altura livre da escada, inclinação e lanços da rampa, altura das guardas, camadas e U
   das paredes.
2. **Os medidores.** Uma biblioteca de medidas feitas no programa e testadas, cada uma com um nome que as regras usam:
   área útil, área bruta do fogo, pé-direito (o mínimo e a percentagem da área acima de um valor), maior círculo e
   maior quadrado inscritos, menor dimensão, profundidade face à fachada, envidraçado ÷ área útil, distância a
   obstáculos, horas de sol (o sol do terreno, 0.365), largura útil, zonas livres das portas e das louças (0.140), 2e+c,
   desnível por lanço, U. Uma regra nova não pede programação; uma medida nova, sim.
3. **Os regulamentos (as regras são dados).** Um pacote por país — Portugal e Cabo Verde primeiro; Brasil, Angola,
   Moçambique… quando vierem —; cada diploma com a data, as alterações, o estado (em vigor, revogado, proposta) e a
   fonte; cada regra com o artigo (n.º e alínea), o texto curto, onde se aplica (ambiente de um uso, fogo, porta de
   entrada, escada comum, rampa, parede exterior, par de camadas, edifício, lote), a condição sobre os medidores (≥, ≤,
   entre, tabela pela tipologia, conta simples), a gravidade e a correção sugerida. Por projeto: o país, os diplomas à
   data do pedido de licença, o regulamento municipal / PDM (os valores escritos pelo arquiteto) e as regras do
   gabinete; Cabo Verde chama Portugal como supletivo. Cada valor fica «a confirmar» até o arquiteto o conferir no texto
   publicado. O projeto guarda a cópia das regras com que foi verificado (a ficha de 2026 não muda com o pacote de
   2027; atualizar é um botão). Um editor de regulamentos no programa — tabela, sem programar — e «duplicar um país»
   para adaptar a outro.
4. **O vigilante.** Depois de cada edição (cada passo de Ctrl+Z) refazem-se só as regras do que mudou e do que depende
   disso (o ambiente ← as paredes, portas e janelas à volta; o fogo ← os seus ambientes; a escada ← a laje de cima, pela
   altura livre), em fundo, depois de ~0,3 s parado, nunca durante uma órbita ou um arraste; o resultado guarda-se por
   elemento até ele mudar. Meta: menos de 50 ms por edição; ao abrir, o projeto todo em fundo. Ao desenhar: a porta, a
   escada e a rampa mostram ✓ / ⚠ na barra da ferramenta antes do clique; ao pousar um ambiente, o uso, o fogo e a
   tipologia refazem-se e a área é comparada logo.
5. **Mostrar e agir.**
   - **Rodapé:** um indicador permanente — verde «✓ Cumpre o CTE», âmbar «⚠ 2 recomendações», vermelho «✗ 3
     incumprimentos». Quando a última ação cria um incumprimento, a faixa do rodapé fica vermelha com a frase inteira:
     «✗ Sala do fogo A (T2): 12,40 m² — CTE, art. 40.º e Anexo I: mínimo 14,00 m²   [Ir para] [Porquê] [Exceção]», até à
     ação seguinte.
   - **Na vista:** o ambiente ou o elemento que falha com uma trama vermelha transparente e um ⚠; desliga-se.
   - **Propriedades:** um grupo «Verificação» em cada elemento e ambiente — cada regra com ✓ / ✗, o medido, o exigido e
     o artigo.
   - **Painel Verificação:** por fogo → ambiente → regra, ou por diploma; filtros (incumprimentos, recomendações,
     exceções, a confirmar); «Ir para» abre a planta, enquadra e escolhe todos os envolvidos; «Corrigir» quando a
     resposta é única (o número de degraus, o tipo de porta seguinte que cumpre, o corrimão que falta); «Exceção» com a
     justificação (vontade do dono de obra, edifício existente…), quem e quando.
   - **Ficha de verificação** em PDF e XLSX para o licenciamento: diploma, artigo, exigido, projeto, estado, exceções
     justificadas; o quadro de áreas por fogo com a tipologia.
   - Nunca bloqueia: avisa.
   - **Tudo num só lugar:** o mesmo rodapé e o mesmo painel juntam o que já se verifica noutros sítios, cada um como
     uma fonte com o seu filtro — a coerência do modelo (vãos fora da parede, paredes sobrepostas, ambientes abertos),
     as boas práticas dos materiais, os conflitos entre disciplinas, a elétrica, a estrutura (EC2 / EC6) e o IFC para
     certificação (IDS).

**Materiais incompatíveis (pacote «Boas práticas», à parte da lei, desligável):** cada material ganha uma família (gesso
cartonado normal ou hidrófugo, madeira, aço, alumínio, cobre, zinco, betão, argamassa de cimento ou de cal, pedra, EPS,
XPS, lã mineral, betume, PVC, vidro…); as regras olham para as camadas que se tocam e para o material no seu sítio — gesso
normal em instalação sanitária ou cozinha; madeira em contacto com o terreno; metais em contacto que corroem (alumínio
com cobre, zinco com cobre); poliestireno com produtos betuminosos com solventes; argamassa de cimento sobre alvenaria
antiga de cal; local húmido sem revestimento impermeável; parede mais fina do que o mínimo do seu material e função
(CTE Anexo II); U da parede exterior acima do máximo (REH, em Portugal). Cada regra diz o porquê.

**O que verificar, por tema** (Cabo Verde lido no CTE; Portugal a fixar no texto oficial):

| Tema | Cabo Verde (CTE) | Portugal |
|---|---|---|
| Pé-direito | art. 27.º | RGEU, art. 65.º |
| Áreas dos compartimentos e dos fogos pela tipologia | art. 40.º e Anexo I | RGEU, arts. 66.º–67.º (DL 10/2024) |
| Forma dos compartimentos | art. 41.º | RGEU |
| Iluminação, ventilação, obstáculos, sol | arts. 76.º–78.º | RGEU |
| Portas e zonas livres | arts. 30.º e 115.º | DL 163/2006 |
| Escadas, rampas, corredores, passagens | arts. 35.º–39.º | RGEU; DL 163/2006 |
| Cozinha e instalações sanitárias | arts. 42.º–43.º | RGEU; DL 163/2006 |
| Elevador | art. 37.º | DL 163/2006 |
| Paredes e pavimentos (material, espessura, humidade) | arts. 92.º, 98.º–100.º, Anexo II | — |
| Urbanismo: parâmetros, alturas de fachada, afastamentos, pátios | arts. 19.º–23.º e regulamento municipal | PDM; RGEU |
| Incêndio | arts. 59.º–62.º (remete para legislação própria) | SCIE (mais tarde) |
| Térmica | art. 79.º | REH |

**Passos (uma versão cada, parar em cada um para o dono testar):**
1. ~~**O leitor:** uso dos ambientes (nome e equipamento), fogos e tipologia automáticos, na planta e nas Propriedades,
   corrigíveis~~ (0.416.0; o uso e os fogos no IFC ao gravar — IfcSpace.ObjectType, IfcZone —, calculados em memória
   a cada mudança). As Propriedades do projeto (país, regulamentos, tipo de obra, uso e altura do edifício) passam
   para o passo 2, com os regulamentos.
2. ~~**O motor, o vigilante e o rodapé:** o formato dos pacotes, os primeiros medidores (área útil, área bruta do fogo,
   pé-direito, largura útil das portas), a vigilância por edição, a faixa do rodapé, o grupo Verificação nas
   Propriedades; o pacote de Cabo Verde com os arts. 27.º, 30.º, 40.º e o Anexo I. Teste: um T2 com a sala pequena → o
   rodapé vermelho~~ (0.417.0; e as Propriedades do projeto que eram do passo 1: país, uso, obra, altura; o
   indicador ficou à esquerda do rodapé — à direita empurrava os botões do rodapé a 1280 px).
3. ~~**O painel Verificação:** a lista, Ir para, Exceção com justificação, filtros, as marcas na vista; as verificações que
   já existem entram como fontes~~ (0.418.0; as exceções no IFC com as definições do projeto; as outras verificações a
   um clique no mesmo painel — os resultados delas continuam nas janelas próprias).
4. ~~**Escadas, rampas, corredores e guardas:** os medidores e as regras dos arts. 35.º–39.º~~ (0.419.0; e a forma
   dos compartimentos do art. 41.º, as instalações sanitárias do 43.º, a circulação do 44.º, os arrumos do 45.º e as
   guardas do 131.º). Por fazer: os corrimãos (número e prolongamentos, arts. 35.º e 36.º), os patamares, a altura
   livre das rampas; ✓ / ⚠ na barra das ferramentas ao desenhar e «Corrigir» (o vigilante já avisa 0,3 s depois de
   cada clique).
5. ~~**Iluminação, ventilação e forma:** envidraçado ÷ área até 6 m, círculos e quadrados inscritos, profundidade,
   obstáculos fronteiros~~ (0.420.0; os círculos e quadrados vieram na 0.419). Por fazer: as **horas de sol** (art.
   78.º: cinco horas entre as 7 e as 17 horas solares — o texto não diz em que dia do ano; perguntar ao dono) e a
   **profundidade face à fachada** (art. 41.º a).
6. ~~**Portugal:** RGEU, DL 163/2006; Cabo Verde → Portugal supletivo~~ (0.421.0; o RGEU do texto da Ordem dos
   Arquitectos — redação do DL 650/75 — e do consolidado da PGD Lisboa até ao DL 108/2026; o DL 163/2006 do texto de
   2006: confirmar com o dono as alterações do DL 10/2024 ao art. 66.º e as de 2014–2019 às normas técnicas). Por
   fazer: o **U do REH** (os máximos pela zona climática, Portaria 138-I/2021 — preciso do quadro) e a **SCIE**.
7. ~~**Materiais e boas práticas:** as famílias, as camadas em contacto, o material no seu sítio~~ (0.422.0; o CTE
   arts. 92.º n.º 3, 98.º e 99.º n.º 1 a); um pacote «Boas práticas» para qualquer país, só avisos e só onde a lei do
   projeto não diz nada, que se desliga nos Regulamentos do projeto; a verificação de um edifício de 2161 elementos
   em ~0,6 s por edição). Por fazer: **as espessuras do Anexo II** do CTE (preciso do quadro — o B.O. que li não o
   traz legível) e os materiais pela sua posição em altura (o corte de humidade na base das paredes).
8. ~~**Urbanismo:** lote e estremas (do terreno), índices, alturas de fachada, afastamentos, os valores do regulamento
   municipal / PDM por projeto~~ (0.423.0: a ferramenta Lote — retângulo, polígono, contorno do terreno — no `IfcSite`
   «FootPrint»; a frente escolhida ou a estrema mais perto da entrada; o pacote «Plano municipal» feito dos valores
   escritos para o projeto; a construção dentro do lote. 0.424.0: CTE arts. 21.º, 22.º, 23.º a) e 24.º n.º 2; RGEU
   arts. 59.º, 60.º e 62.º § 2.º; o uso «Pátio»; a verificação aos bocados, sem prender a janela). Por fazer: o lote
   escolhido com o rato e as suas pegas (hoje redesenha-se); o lote nas tabelas; o art. 21.º n.os 2–4 (elementos
   recuados, fachadas contíguas, terreno em declive), o 23.º b)–g) (acesso ao pátio, cotas) e o 24.º n.os 3–4.
9. ~~**A ficha de verificação** (PDF e XLSX) e o **editor de regulamentos** (duplicar um país para outro)~~ (0.425.0:
   o projeto, os regulamentos, o lote e o plano municipal, o quadro de áreas, regra a regra por artigo, as exceções;
   no PDF as regras de muitos sítios resumidas. 0.426.0: o editor — limites, gravidade, conferido, ativa; os do programa
   nunca alterados, as mudanças numa cópia do arquiteto que vale em vez deles; Novo país a partir de outro).

**O Verificador está completo nos 9 passos (0.416–0.426).** Ficam anotados, para quando o dono decidir: as horas de sol
(art. 78.º: em que dia do ano), o art. 41.º a), o U do REH (o quadro da Portaria 138-I/2021), a SCIE, os corrimãos e os
patamares, ✓/⚠ ao desenhar e «Corrigir», as espessuras do Anexo II do CTE, o lote escolhido com o rato e as suas pegas.

**Decisões do dono antes do passo 1** (formato dos dados, difíceis de desfazer):
- O uso dos ambientes e os fogos no IFC: o uso em `IfcSpace.ObjectType` e cada fogo uma `IfcZone` com a tipologia
  (o Revit e os outros programas leem-nos) — proposta.
- Os pacotes de regras: ficheiros JSON numa pasta «regulamentos» do programa (um por diploma) e a cópia usada no
  `.arqsynthbim` do projeto — proposta.
- As fontes: Cabo Verde do texto do B.O. de 2012 que li (o dono confirma se houve alterações); Portugal do texto
  consolidado oficial (o dono traz ou confirma).

### O painel «Desenhar» do Revit, completo (pedido do dono do projeto, 2026-11-07)

O dono: «no revit temos algumas outras ferramentas interessantes que não devemos deixar de fora; estude esses comandos
e crie para o ArqSynth. por exemplo criar por seleção, o arco por seleção de 2 elementos, criar com offset a x
distância etc». As formas já estão em ícones na barra de parâmetros (0.450). O estudo, ferramenta a ferramenta:

| Revit (Modificar ▸ Colocar ▸ Desenhar) | ArqSynth hoje | Passo |
| --- | --- | --- |
| Linha, Retângulo, Círculo | Parede e Linha | — |
| Polígono inscrito / circunscrito | Círculo com lados (só linhas) — 0.456–0.458: em tudo | 5 |
| Arco início-fim-raio, arco centro-pontas | Arco de 2 pontos e de centro (linhas); parede só de 3 pontos | 4 |
| Arco tangente na ponta | «Linha com arcos» (linhas, Tab); parede não | 4 |
| **Arco de concordância** (escolher 2 elementos) | não há | 2 |
| Spline | Bézier | — |
| Elipse, elipse parcial | não há — 0.456–0.458: lajes, regiões, linhas | 5 |
| **Escolher linhas** (criar sobre uma linha ou aresta existente) | só a varinha (2 linhas paralelas de um desenho) | 1 |
| Escolher faces / escolher paredes | «Por face» / a varinha (laje dentro das paredes) | — |
| Barra: **Afastamento** (a X da linha desenhada ou escolhida) | não há | 1 |
| Barra: **Raio** (cantos arredondados ao desenhar em cadeia) | só no perfil (Alt + clique num canto) | 3 |
| Barra: **Cadeia** (desligada: troços soltos) | sempre em cadeia | 3 |

1. ~~**Afastamento e Escolher linhas** (Parede e Linha)~~ (0.451.0: `tools/pick_lines.py`; a parede desenhada fica à
   esquerda do sentido do desenho, a escolhida do lado do rato; nas lajes / pisos ainda não).
2. ~~**Arco de concordância**~~ (0.452.0: `core/fillet.py`, `IfcModel.fillet_walls`, `line_edit.fillet_lines`. Por
   fazer: a parede curva fica tangente às duas mas sem junta registada — mover uma parede depois não arrasta o
   arco).
3. ~~**Raio e Cadeia** na barra da Parede e da Linha: com «Raio» ligado, cada canto da cadeia sai arredondado com esse
   raio; com «Cadeia» desligada, cada troço começa num clique novo.~~ (0.453.0: o Raio só na Parede — nas linhas o
   arco de concordância acrescenta vértices e a cadeia continua do último; fica por fazer o Raio da Linha.)
4. ~~**Arcos da parede como os do Revit**: início-fim-raio, centro-pontas e tangente na ponta (continuar a cadeia em
   arco).~~ (0.454.0: o «Arco» que havia é o início-fim-raio; novos `arcs.arc_tangent` / `arc_from_centre`; a cadeia
   passa de «Linha» a «Arco tangente» e volta sem se partir. Por fazer: o arco e a parede reta que se tocam não
   ficam ligados — mover uma não arrasta a outra.)
5. ~~**Polígonos e elipses**: polígono inscrito e circunscrito (paredes, linhas, lajes, regiões) e elipse / elipse
   parcial (linhas, regiões, desenho 2D).~~ (0.456.0: lajes, pisos, tetos, regiões e máscaras; 0.457.0: paredes;
   0.458.0: na fila «Desenhar» da Linha — o Círculo desenha-os —, a elipse uma face, a elipse parcial uma meia elipse
   escolhida inteira, os semieixos nas cotas temporárias. Fica por fazer: as linhas do Desenho 2D sem elipse.)
6. ~~**Concordância como no Revit em tudo o que se desenha**~~ (0.455.0, o dono: «o arco não é um arco, mas um monte
   de segmentos… tentei no polígono… também na região, máscara»): nas linhas um arco verdadeiro, escolhido inteiro, o
   raio na cota temporária e nas Propriedades (as linhas seguem, tangentes); no canto de um polígono; no Desenho 2D
   (região, máscara, polilinha, retângulo: o lado guardado como arco — «bulge»; duas linhas: um arco 2D). Teste na
   janela real: `tests/gui_desenho_revit.py`. Por fazer: mudar depois o raio no polígono e na região. (0.459.0: no
   polígono feito — um clique no contorno escolhe o lado ou o arco inteiro, `core/arc_runs.py`; na região ainda não.
   Também a parede por «Escolher linhas» sobre um arco inteiro e a cota do raio da parede curva, uma concordância
   continuando tangente.)
7. ~~**Laje, Piso, Teto e Região com as mesmas opções**~~ (0.456.0, o dono, 2026-11-07: «Sim, põe»): polígono inscrito /
   circunscrito, elipse, Escolher linhas (o contorno das linhas clicadas), Afastamento e Raio dos cantos —
   `core/outline_shapes.py`, os contornos como `core/outline_loops` (arcos e Bézier). Falta: a Cobertura (as suas
   formas são outras), a elipse parcial e os polígonos na Parede e na Linha (passo 5).

### Transversal (ao longo das fases)
- Confirmar no Revit, elemento a elemento, os IFC gravados.
- ~~Investigar: no papel, o contorno grosso das paredes falhou uma vez num canto (a união dos contornos pelo Qt, `pdf._paths`); não se repetiu ao desenhar de novo.~~ (0.253.0: os contornos saíam do corte num sentido ou noutro; agora orientados por elemento; 0.254.0: o pilar recorta a parede no papel.)
- Exportação «Reference View» para certificação. (2026-10-26: por fazer — preciso do texto da MVD IFC4 Reference
  View 1.2, sobretudo a geometria permitida e os vãos já recortados; o sítio da buildingSMART só abre depois de
  uma verificação de pessoa. O dono pode trazer o documento.)
- Desempenho medido a cada fase (as metas da secção 6 das instruções). (0.255.0: medido no fim dos restos — sem regressões do código; falta a meta de abrir 500 MB, ~29 s pela proporção do edifício grande, e a pausa de ~1,3 s ao reabrir um modelo grande.) (0.344.0: ~~reabrir~~ — 1,0 s até à 1.ª imagem no edifício grande, ~12 s estimados para 500 MB; ~~a pausa ao reabrir~~ — 0,3 s desde a 0.328; a navegação a 57 imagens/s, medida fora do ecrã com a leitura da imagem. Fica a 1.ª abertura de 500 MB, ~32 s: mais de metade é o IfcOpenShell a ler o ficheiro, ~17 s só isso.)

## 5. Como se trabalha cada passo

1. Uma versão por passo, com testes automáticos (núcleo e janela real) e uma captura do que o dono do projeto deve
   ver.
2. CHANGELOG e ARQUITETURA (decisões) atualizados; este plano risca o passo feito.
3. No fim de cada passo, passos de teste numerados, clique a clique.
4. Decisões difíceis de desfazer — formato dos dados, motor, licença — perguntam-se antes.
