# Guia das ferramentas — ArqSynth BIM 0.482.0

Este guia descreve **todas as ferramentas e comandos da fita**, separador a separador, para as poder experimentar.
Para cada uma diz:

- **onde está** (Separador ▸ Painel) e a tecla, se tiver;
- **o que faz** — a mesma dica que aparece ao passar o rato pelo botão;
- **como se usa** — o que o programa pede, passo a passo, quando a ferramenta está ativa;
- **onde estão os passos de teste** — as secções do [TESTAR.md](TESTAR.md) que a experimentam clique a clique.

O guia é feito pelo próprio programa (`scripts/guia_ferramentas.py`): os nomes e os textos são exatamente os do
ArqSynth BIM 0.482.0.

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

   O registo de erros fica em `%LOCALAPPDATA%\ArqSynth BIM\arqbim.log`.

## Primeiro percurso: uma casa do princípio ao PDF

Uma casa pequena, do princípio ao PDF. «Mostrar onde está» abre o separador certo e acende o botão.

1. Paredes: clique em Parede, clique num ponto do chão, leve o rato para a direita, escreva 6 e Enter; para cima, 4 e Enter; para a esquerda, 6 e Enter; clique no primeiro ponto para fechar. Esc.
2. Laje de cobertura: clique em Laje e clique num canto do topo das paredes e no canto oposto. Esc.
3. Porta: clique em Porta, passe o rato sobre uma parede e clique. Esc.
4. Janela: clique em Janela, passe o rato sobre uma parede e clique. Esc.
5. Telhado (em vez da laje de cobertura): clique em Cobertura e clique dentro das paredes.
6. Ambiente: clique em Ambiente e clique dentro das paredes: fica com o nome e a área.
7. Planta: clique em Planta (ou carregue em F4).
8. Cotas: na planta, clique em Cotar paredes.
9. Folhas: clique em Folhas por pavimento e OK: a planta vai para uma folha com legenda.
10. PDF: clique em Folhas em PDF e escolha onde o gravar.

## As teclas

```
Navegação
  Botão do meio + arrastar: orbitar · Shift + botão do meio: deslocar (ao contrário: Visualizar ▸ Rato)
  Roda do rato: zoom para onde aponta o cursor · Shift+Z: enquadrar tudo · Shift+F: enquadrar a seleção
  F8: 3D · F2: topo · F3: frente · F4: planta do pavimento ativo · F5: último corte
  F6: caixa de corte (Shift+F6: à volta da seleção) · PgUp / PgDn: pavimento acima / abaixo
  Abas por cima da vista: uma por vista aberta · Ctrl+W fecha a vista · Ctrl+Tab: a seguinte
  O cubo de vistas (canto de cima, à direita): clique numa face, aresta ou canto; arraste para orbitar

Selecionar e editar
  Espaço: Selecionar · arrastar para a direita: o que fica dentro · para a esquerda: o que toca
  Shift + clique: juntar ou tirar · Ctrl+A: tudo · Esc: largar · Delete: apagar
  Uma linha: um clique, só ela; dois, a cadeia; três, tudo o que lhe está ligado (um arco: inteiro)
  Ctrl+Z / Ctrl+Y: desfazer / refazer
  Ctrl+C: copiar · Ctrl+V: colar onde clicar · Ctrl+Shift+V: colar noutros pavimentos
  Quando um comando pede elementos (balão verde): um clique junta ou tira; Enter ou botão direito
  continuam; Esc desiste

Ferramentas com tecla
  L: Linha · A: Arco · R: Retângulo · P: Push/Pull · F: Offset · M: Mover · Q: Rodar · T: Fita métrica
  C: Cota
  W: Parede · D: Porta · J: Janela · G: criar componente · Ctrl+G: criar grupo
  O: Orbitar · H: Deslocar · Z: Zoom · Ctrl+T: Tabelas · Ctrl+P: PDF da vista · F1: esta ajuda
  Ctrl+1 … Ctrl+9: os separadores da fita (Modelagem, Arquitetura, Estrutura … Terreno); as teclas funcionam em todos

Nas ferramentas de colocação (pilar, porta, louça, móvel…)
  R / Shift+R: rodar 90° · Espaço: outro ponto de inserção · F: inverter · X / Y: só nesse eixo
  Tab: muda a opção da ferramenta (a linha de referência da parede, a forma da laje…)

Medidas: escreva a qualquer momento e carregue em Enter
  3,20 · 3,20;4,50 · 320cm · 3200mm — depois de terminar, outra medida + Enter corrige a última
  Copiar / Matriz: depois de uma cópia, 3x = mais 3 iguais, /3 = dividir em 3

Inferências (o cursor agarra-se sozinho)
  verde: extremidade · azul-claro: ponto médio · vermelho: na aresta · azul: na face
  amarelo: origem · magenta: esquadria · cinzento: na guia · eixos vermelho / verde / azul

Onde está cada coisa: separador «Procurar» deste painel (escreva o nome).
```

## Índice

1. [Início](#1-início) — 16 comandos
2. [Modelagem](#2-modelagem) — 34 comandos
3. [Arquitetura](#3-arquitetura) — 50 comandos
4. [Estrutura](#4-estrutura) — 21 comandos
5. [Instalações](#5-instalações) — 18 comandos
6. [Inserir](#6-inserir) — 10 comandos
7. [Anotar](#7-anotar) — 14 comandos
8. [Analisar](#8-analisar) — 16 comandos
9. [Massa e Estudos](#9-massa-e-estudos) — 26 comandos
10. [Terreno](#10-terreno) — 11 comandos
11. [Colaborar](#11-colaborar) — 7 comandos
12. [Visualizar](#12-visualizar) — 46 comandos
13. [Gerenciar](#13-gerenciar) — 21 comandos
14. [Modificar | Paredes](#14-modificar-paredes) — 36 comandos

---

## 1. Início

Criar, abrir e gravar projetos; exportar; ajuda.

**Para testar este separador** (projeto novo, Ctrl+N):

1. Faça um retângulo e puxe-o (separador Modelagem), e carregue em **Guardar** (Ctrl+S): escolha uma pasta e um nome.
2. **Novo** (Ctrl+N) e depois **Abrir…** (Ctrl+O) o ficheiro que guardou: volta como estava.
3. **Ligar um desenho DXF/DWG…** com `planta_cad.dxf`: as linhas ficam no chão, para desenhar por cima.
4. Na planta (F4), **Exportar vista em PDF…** (Ctrl+P) e **Exportar imagem da vista…**: abra os ficheiros.
5. **Exportar modelo 3D…** com «O modelo todo»: em GLB, abra-o no Blender ou num visualizador de glTF na internet (as peças por pavimento e categoria, com os materiais); em OBJ, no SketchUp; em STL a 1:100, no programa da impressora 3D.
6. **Ajuda** (F1): no separador «Procurar», escreva «parede» e clique em «Mostrar onde está».

### Início ▸ Projeto

#### Novo  ·  tecla Ctrl+N

- **O que faz:** Começa um projeto novo, vazio (pergunta antes se o atual tiver alterações por guardar).
- **Passos de teste (TESTAR.md):** 0.398 «Tipos de cota (o motor da aparência)»

#### Abrir…  ·  tecla Ctrl+O

- **O que faz:** Abre um projeto (IFC). Da segunda vez abre muito mais depressa: as formas ficam guardadas.
- **Passos de teste (TESTAR.md):** 0.347 «O guia de todas as ferramentas»; 0.344 «Reabrir um modelo grande mais depressa»; 0.328 «Reabrir um modelo grande sem a janela parar»; 0.296 «Folhas de abrir dentro do arco»; 0.255 «Abrir um projeto com o ficheiro lateral lido uma vez»

#### Guardar  ·  tecla Ctrl+S

- **O que faz:** Guarda o projeto no seu ficheiro IFC (e as vistas, cotas e folhas no ficheiro ao lado).

#### Guardar como…  ·  tecla Ctrl+Shift+S

- **O que faz:** Guarda o projeto noutro ficheiro, com outro nome.

#### Página inicial

- **O que faz:** A página inicial: começar um projeto, os tutoriais, os documentos recentes, as discussões e os apoiadores.
- **Passos de teste (TESTAR.md):** 0.476 «A janela já não cresce sozinha»; 0.406 «Tutoriais na própria página inicial»; 0.403 «A página inicial na primeira aba, com a casa»; 0.388 «Página inicial: recentes à esquerda, com vistas»; 0.387 «A página inicial»

#### Novo a partir de arquivo base…

- **O que faz:** Começa um projeto a partir de um arquivo base (um modelo): abre-o como projeto novo, para gravar com outro nome — o arquivo base fica como estava.

### Início ▸ Exportar

#### Exportar vista em PDF…  ·  tecla Ctrl+P

- **O que faz:** O corte ou alçado que está à frente (senão, a planta do pavimento ativo) em PDF, num A3, à maior escala habitual que caiba (Ctrl+P).
- **Passos de teste (TESTAR.md):** 0.207 «A imagem de fundo nas folhas»; 0.203 «O pé dos taludes na planta»; 0.202 «O valor escrito nas curvas mestras»; 0.201 «Cores de inclinação nas folhas»

#### Exportar vista (DXF, DWG, SVG)…

- **O que faz:** O corte ou alçado que está à frente (senão, a planta do pavimento ativo) em DXF ou DWG para o AutoCAD e outros programas (em metros, cada tipo de linha na sua camada), ou em SVG para o Illustrator, o Inkscape e a internet (desenhado como nas folhas, à escala da vista). Escolhe-se no tipo, ao gravar.
- **Passos de teste (TESTAR.md):** 0.369 «A vista em DWG e em SVG»

#### Exportar imagem da vista…

- **O que faz:** A vista tal como está, numa imagem PNG ou JPEG do tamanho que escolher (Full HD, 4K, uma folha A3…), sem a seleção nem as marcas das ferramentas.
- **Passos de teste (TESTAR.md):** 0.329 «Exportar a vista em imagem»

#### Exportar modelo 3D…

- **O que faz:** O modelo em 3D: GLB (glTF) para o ArqSynth Presentation, a internet, o Blender, o Twinmotion — as peças por pavimento e categoria, os materiais e os dados de cada elemento —; SKP para o SketchUp e 3DM para o Rhino, com as mesmas etiquetas ou camadas, materiais e dados; OBJ para quase todos os programas 3D; STL para imprimir uma maqueta à escala; USDZ para a realidade aumentada no iPhone e no iPad (abre-se sozinho, e põe o modelo em cima da mesa).
- **Passos de teste (TESTAR.md):** 0.371 «O modelo em USDZ (realidade aumentada)»; 0.350 «Exportar para o SketchUp e o Rhino»

#### Para o ArqSynth Presentation…

- **O que faz:** O modelo todo num GLB para o ArqSynth Presentation, com a apresentação dentro: uma camada por elemento (por pavimento e categoria) e as cenas — a vista geral, cada vista 3D com nome (a câmara, o que esconde, a caixa de corte), a planta de cada pavimento (vista de cima, cortada à altura de corte) e cada corte —, e o sol do terreno.
- **Passos de teste (TESTAR.md):** 0.368 «Panoramas 360° para o Presentation»; 0.367 «O pacote para o Presentation: o modelo e as folhas como plantas»; 0.362 «Para o ArqSynth Presentation: o pacote»

#### Exportar folhas em PDF…

- **O que faz:** Todas as folhas do projeto num PDF, uma por página.

#### Folhas por pavimento…

- **O que faz:** Uma folha com a planta de cada pavimento escolhido (e, se quiser, uma com os alçados e outra com os cortes)
- **Passos de teste (TESTAR.md):** 0.367 «O pacote para o Presentation: o modelo e as folhas como plantas»

#### Exportar Gaussian splat (apresentação)…

- **O que faz:** O modelo em Gaussian splat (PLY), para o apresentar nos visualizadores da internet; com as nuvens de pontos ligadas, se quiser.

### Início ▸ Ajuda

#### Ajuda  ·  tecla F1

- **O que faz:** Abre o painel Ajuda (F1): a ferramenta em uso, procurar um comando, uns primeiros passos e as teclas.
- **Passos de teste (TESTAR.md):** 0.327 «A janela de Ajuda (F1)»

#### Sair  ·  tecla Ctrl+Q

- **O que faz:** Fecha o programa; se houver alterações por guardar, pergunta antes.

---

## 2. Modelagem

Operações gerais de criação e edição geométrica.

**Para testar este separador** (projeto novo, Ctrl+N):

1. **Retângulo** (R): clique no chão, escreva `3;2` e Enter.
2. **Push/Pull** (P): clique no retângulo, escreva `3` e Enter: um volume de 3 m.
3. **Mover** (M), **Copiar** (depois de uma cópia, `3x` Enter faz mais três), **Rodar** (Q, `90` Enter), **Espelhar**, **Escala** (`2` Enter): cada um com o volume escolhido.
4. **Fita métrica** (T) e **Cota** (C) entre dois cantos.
5. Escolha um volume e **Classificar como ▸ Parede alvenaria 20 cm**: passa a parede BIM.
6. Ctrl+Z várias vezes: tudo volta atrás, um passo de cada vez.

### Modelagem ▸ Selecionar

#### Selecionar  ·  tecla Espaço

- **Como se usa:** Clique num elemento, numa linha (dois cliques: a cadeia) ou na face de um esboço (dois cliques: com as arestas; três: o objeto todo), ou arraste uma caixa: para a direita, só o que fica todo dentro; para a esquerda, tudo o que toca. Shift troca, Ctrl junta, Ctrl+Shift tira. Delete apaga.

### Modelagem ▸ Copiar e colar

#### Copiar para colar  ·  tecla Ctrl+C

- **O que faz:** Guarda o que está selecionado para o colar a seguir.

#### Colar  ·  tecla Ctrl+V

- **O que faz:** O que copiou fica no cursor: um clique põe a cópia.
- **Passos de teste (TESTAR.md):** 0.326 «Copiar, Matriz e copiar-colar»

#### Colar nos pavimentos…  ·  tecla Ctrl+Shift+V

- **O que faz:** O que copiou, no mesmo sítio, nos pavimentos que escolher (como o «Colar alinhado» do Revit).

### Modelagem ▸ Geometria

#### Junções de paredes

- **Como se usa:** Clique numa parede junto a um canto: passa a ser ela a passar e a outra pára na sua face (Tab: meia-esquadria). Esc: Selecionar.
- **Teclas:** Clique: junto ao canto, na parede · Tab: topo a topo / meia-esquadria · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.301 «Junções de paredes»

#### Unir geometria

- **Como se usa:** Clique no primeiro dos dois elementos a unir de novo. Esc: Selecionar.
- **Teclas:** Clique: um elemento, depois o outro · botão direito: outro primeiro · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.333 «Desunir e Unir geometria»

#### Desunir geometria

- **Como se usa:** Clique no primeiro dos dois elementos (parede, laje, pilar…) cuja junção quer ver. Esc: Selecionar.
- **Teclas:** Clique: um elemento, depois o outro · botão direito: outro primeiro · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.333 «Desunir e Unir geometria»

### Modelagem ▸ Modificar

#### Mover  ·  tecla M

- **Como se usa:** Clique no ponto de base (move o que está selecionado, ou o objeto sob o cursor).
- **Passos de teste (TESTAR.md):** 0.427 «Arrastar para mover»

#### Copiar

- **Como se usa:** Clique no ponto de base (move o que está selecionado, ou o objeto sob o cursor).
- **Passos de teste (TESTAR.md):** 0.326 «Copiar, Matriz e copiar-colar»

#### Rodar  ·  tecla Q

- **Como se usa:** Clique no centro da rotação (roda o que está selecionado, ou o objeto sob o cursor). · Eixo Z — X, Y ou Z muda o eixo.
- **Passos de teste (TESTAR.md):** 0.412 «Rodar à volta de X, Y ou Z; planos de trabalho»

#### Espelhar

- **Como se usa:** Selecione primeiro o que quer espelhar (ferramenta Selecionar) e volte a Espelhar.
- **Teclas:** Dois cliques: o eixo de simetria · Ctrl: copiar · X / Y: bloquear o eixo · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.322 «Os comandos pedem o que lhes falta»; 0.289 «Gerador de portas e janelas»

#### Alinhar

- **Como se usa:** Clique na referência: um eixo da grelha, uma linha, uma aresta ou a face de qualquer elemento. Esc: Selecionar.
- **Teclas:** Clique: a referência, depois as linhas, arestas e faces — ou as linhas dos padrões — a alinhar · botão direito: outra referência · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.332 «Alinhar os padrões numa face»

#### Offset  ·  tecla F

- **Como se usa:** Offset: clique numa face de um esboço ou numa linha (a cadeia dela; as linhas escolhidas antes, se as houver).
- **Passos de teste (TESTAR.md):** 0.373 «Desenho livre como no SketchUp: uma linha sozinha, Offset, Arco, Linha livre, Bézier»; 0.206 «Offset de faces em L e Escala a partir do centro»

#### Escala

- **Como se usa:** Escala: selecione primeiro os esboços (os elementos BIM têm as medidas dos seus tipos).
- **Passos de teste (TESTAR.md):** 0.234 «Os cortes das armaduras a uma escala própria»; 0.206 «Offset de faces em L e Escala a partir do centro»; 0.153 «Escala»

#### Aparar / estender a um limite

- **Como se usa:** Clique na parede que serve de limite. Esc: Selecionar.
- **Teclas:** Clique: o limite, depois as paredes (do lado que fica) · Esc: outro limite / Selecionar

#### Aparar / estender ao canto

- **Como se usa:** Clique na primeira parede, do lado que fica. Esc: Selecionar.
- **Teclas:** Clique: a primeira parede, depois a segunda (do lado que fica) · Esc: Selecionar

#### Dividir parede

- **Como se usa:** Clique numa parede onde a quer dividir (ou digite a distância à ponta mais perto + Enter). Esc: Selecionar.
- **Teclas:** Clique: dividir ali · o meio da parede atrai · Esc: Selecionar

#### Dividir com folga

- **Como se usa:** Clique numa parede onde a quer dividir, com uma folga de 0,02 m ao meio (a folga muda na barra de cima; ou digite a distância à ponta mais perto + Enter). Esc: Selecionar.
- **Teclas:** Clique: dividir ali · o meio da parede atrai · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.300 «Dividir com folga e aparar / estender até um limite»

#### Matriz

- **Como se usa:** MATRIZ DE 3 CÓPIAS, cada uma à distância dada · Clique no ponto de base (move o que está selecionado, ou o objeto sob o cursor).
- **Passos de teste (TESTAR.md):** 0.326 «Copiar, Matriz e copiar-colar»

#### Apagar  ·  tecla Delete

- **O que faz:** Apaga o que está escolhido (Del). Numa folha, tira de lá a vista escolhida (o modelo fica).

### Modelagem ▸ Desenhar

#### Linha  ·  tecla L

- **Como se usa:** Clique no primeiro ponto (no chão, numa face ou num ponto).
- **Passos de teste (TESTAR.md):** 0.408 «Cotas interiores: alinham-se com a parede mais perto; Ctrl+clique acrescenta»; 0.405 «Cotas: arrastar com alinhamentos; tipo e ajustes nas Propriedades»; 0.373 «Desenho livre como no SketchUp: uma linha sozinha, Offset, Arco, Linha livre, Bézier»; 0.372 «A Linha fecha a face onde se fecha; as cotas temporárias novas»; 0.358 «A linha de corte editável»; 0.332 «Alinhar os padrões numa face»

#### Arco  ·  tecla A

- **Como se usa:** Arco: clique onde começa (no chão ou numa face).
- **Passos de teste (TESTAR.md):** 0.436 «Fachada de vidro em arco e por face»; 0.375 «Arcos e curvas de Bézier no perfil da parede»; 0.373 «Desenho livre como no SketchUp: uma linha sozinha, Offset, Arco, Linha livre, Bézier»; 0.296 «Folhas de abrir dentro do arco»; 0.294 «Vãos em arco»

#### Retângulo  ·  tecla R

- **Como se usa:** Clique no primeiro canto (no chão ou numa face).
- **Passos de teste (TESTAR.md):** 0.392 «Pintura nos esboços»

#### Círculo

- **Como se usa:** Círculo (24 lados): clique no centro (no chão ou numa face).
- **Passos de teste (TESTAR.md):** 0.410 «Contorno do piso como o perfil da parede; furos desenhados»; 0.383 «As prévias das paredes em volume»; 0.373 «Desenho livre como no SketchUp: uma linha sozinha, Offset, Arco, Linha livre, Bézier»

#### Linha livre

- **Como se usa:** Linha livre: carregue onde começa (no chão ou numa face) e arraste; solte para acabar. Acabar onde começou fecha uma face.
- **Passos de teste (TESTAR.md):** 0.373 «Desenho livre como no SketchUp: uma linha sozinha, Offset, Arco, Linha livre, Bézier»

#### Curva de Bézier

- **Como se usa:** Bézier: clique nos pontos por onde a curva passa (fica suave sozinha, como no Blender). Arrastar: puxa a tangente à mão · Alt + clique: um canto.
- **Passos de teste (TESTAR.md):** 0.411 «Curva de Bézier como no Blender»

#### Plano de trabalho

- **Como se usa:** Plano vertical ao longo do eixo vermelho (XZ): clique no ponto por onde passa. Na barra: XY, YZ ou Face. Esc: sair.
- **Teclas:** XY / XZ / YZ: clique onde o plano fica · Face: clique numa face · Esc: sair
- **Passos de teste (TESTAR.md):** 0.413 «O plano de trabalho fica guardado com o projeto»; 0.412 «Rodar à volta de X, Y ou Z; planos de trabalho»

#### Push/Pull  ·  tecla P

- **Como se usa:** Clique numa face para a empurrar ou puxar (numa das faces escolhidas: todas juntas).
- **Passos de teste (TESTAR.md):** 0.311 «Push/Pull em várias faces ao mesmo tempo»; 0.310 «Faces sozinhas e Push/Pull como no SketchUp»

### Modelagem ▸ Medir

#### Fita métrica  ·  tecla T

- **Como se usa:** Clique numa aresta (para uma linha guia paralela) ou num ponto (para medir).

#### Cota  ·  tecla C

- **Como se usa:** Cota: abra primeiro uma planta (F4), um corte ou um alçado — a cota fica nessa vista.
- **Passos de teste (TESTAR.md):** 0.409 «Snaps da porta e da janela; cotas interiores com esquinas e com as duas paredes»; 0.408 «Cotas interiores: alinham-se com a parede mais perto; Ctrl+clique acrescenta»; 0.405 «Cotas: arrastar com alinhamentos; tipo e ajustes nas Propriedades»; 0.404 «Portas e janelas: o lado certo, a prévia e as cotas na planta»; 0.402 «Editar as cotas como no Revit»; 0.401 «A Cota manual como no Revit»

### Modelagem ▸ Criar

#### Criar componente…  ·  tecla G

- **O que faz:** Faz um componente dos volumes de esboço escolhidos (G): as cópias dele mudam todas juntas.
- **Passos de teste (TESTAR.md):** 0.281 «A telha do utilizador»

#### Criar grupo…  ·  tecla Ctrl+G

- **O que faz:** Junta os elementos escolhidos num grupo (Ctrl+G), para os copiar e mover juntos.

#### Classificar como

- **Escolhas:** Parede alvenaria 15 cm · Parede alvenaria 20 cm · Parede drywall 10 cm · Parede de betão armado 15 cm · Parede de betão armado 20 cm · Parede de betão armado 25 cm · Laje de concreto 12 cm · Laje de concreto 15 cm · Radier 30 cm · Pilar de concreto 20×20 · Pilar de concreto 30×30 · Pilar de concreto 20×50 · Pilar circular Ø30 · Pilar em L 40×40 (15) · Pilar em T 50×40 (15) · Viga de concreto 15×30 · Viga de concreto 20×40 · Viga de concreto 20×50 · Viga em T 60×50 (12) · Sapata 80×80×40 · Sapata 120×120×50 · Sapata corrida 50×30 · Bloco de 1 estaca 60×60×50 · Bloco de 2 estacas 150×60×60 · Bloco de 4 estacas 150×150×70
- **Passos de teste (TESTAR.md):** 0.310 «Faces sozinhas e Push/Pull como no SketchUp»

#### Materiais…

- **O que faz:** A janela dos materiais: nome, cor, tramas da superfície e do corte, transparência, acabamento no render, densidade e condutibilidade térmica; novo, duplicar, apagar um sem uso.
- **Passos de teste (TESTAR.md):** 0.422 «Materiais e boas práticas»; 0.397 «As duas listas de materiais iguais»; 0.318 «Padrões do projeto, tramas por categoria e a biblioteca de materiais»; 0.314 «Os materiais com gráficos completos (superfície e corte)»; 0.164 «Ações e materiais»

---

## 3. Arquitetura

Elementos arquitetónicos: paredes, portas, janelas, coberturas, mobiliário.

**Para testar este separador** (projeto novo, Ctrl+N):

1. **Parede** (W): clique, `6` Enter, `4` Enter, `6` Enter, clique no primeiro ponto. Esc.
2. **Porta** (D) e **Janela** (J): passe por cima de uma parede e clique. **Caixilho Studio** abre o editor de caixilharia de uma janela escolhida.
3. **Laje** no topo das paredes, ou **Cobertura** clicando dentro delas.
4. **Sala**: clique dentro das paredes — nome e área. **Teto** e **Luminária** na sala.
5. **Escada** e **Guarda**. **Cozinha**: clique na face de dentro de uma parede onde começa, nos cantos e no fim, e Enter.
6. Escolha uma parede: aparece o separador verde **Modificar | Paredes** (último deste guia).

### Arquitetura ▸ Selecionar

- **Selecionar** — o mesmo de Modelagem ▸ Selecionar.

### Arquitetura ▸ Construir

#### Parede  ·  tecla W

- **Como se usa:** Parede alvenaria 20 cm · desenha-se pelo eixo (Tab muda): clique no início, depois em cada canto; digite o comprimento (ex.: 4,50) e Enter para medidas exatas.
- **Teclas:** X / Y: bloquear o eixo vermelho / verde · N: soltar · Shift: bloquear a linha seguida
- **Passos de teste (TESTAR.md):** 0.474 «Correções encontradas pela bateria de testes»; 0.437 «Estrutura leve (Steel frame e Wood frame)»; 0.436 «Fachada de vidro em arco e por face»; 0.434 «Ripado como ferramenta própria»; 0.431 «Avisos do modelo»; 0.428 «Paredes em planta com as canetas do papel»

#### Porta  ·  tecla D

- **Como se usa:** Porta 80×210: passe o cursor sobre uma parede e clique — prende ao meio do compartimento e com a ombreira a 0,10 ou 0,20 da gola —, ou digite a distância à extremidade mais próxima (ex.: 0,60) e Enter.
- **Teclas:** Rato numa face: abre para esse lado · F: para o outro · Espaço: dobradiças no outro aro · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.475 «Ambientes: o programa de necessidades no painel lateral»; 0.472 «Folhas: comandos na barra, desenhos importados, carimbo da empresa»; 0.439 «Elevador com portas de patamar»; 0.437 «Estrutura leve (Steel frame e Wood frame)»; 0.409 «Snaps da porta e da janela; cotas interiores com esquinas e com as duas paredes»; 0.407 «Ortogonalizar: a porta e a janela endireitam-se com a parede»

#### Janela  ·  tecla J

- **Como se usa:** Janela 120×120 (peitoril 1,00): passe o cursor sobre uma parede e clique — prende ao meio do compartimento e com a ombreira a 0,10 ou 0,20 da gola —, ou digite a distância à extremidade mais próxima (ex.: 0,60) e Enter.
- **Teclas:** F: para a outra face da parede · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.476 «A janela já não cresce sozinha»; 0.420 «Iluminação, ventilação e o que está em frente das janelas»; 0.409 «Snaps da porta e da janela; cotas interiores com esquinas e com as duas paredes»; 0.407 «Ortogonalizar: a porta e a janela endireitam-se com a parede»; 0.404 «Portas e janelas: o lado certo, a prévia e as cotas na planta»; 0.339 «As janelas por cima, no tema escuro»

#### Caixilho Studio

- **O que faz:** O editor de portas e janelas: desenhar o vão, montantes, travessas, aberturas e materiais, e inserir no modelo
- **Passos de teste (TESTAR.md):** 0.339 «As janelas por cima, no tema escuro»; 0.309 «Igualar todas as divisões no Caixilho Studio»; 0.308 «O Caixilho Studio no tema do programa»; 0.307 «O Caixilho Studio»

#### Mobiliário solto

- **Como se usa:** Sofá de 3 lugares (2,20 m × 0,90 m, 0,85 m de altura): clique onde fica. R roda · Espaço: o ponto · Esc: Selecionar.
- **Teclas:** Clique: pôr a peça · R / Shift+R: rodar · Espaço: o ponto · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.440 «Mobiliário solto»

#### Pilar

- **Como se usa:** Pilar de concreto 30×30, 2,80 m de altura: clique onde fica o pilar (o meio do pé; snaps e alinhamentos). Digite a altura (ex.: 3,00) e Enter para a mudar. Esc termina.
- **Teclas:** R / Shift+R: rodar 90° · Espaço / Shift+Espaço: ponto de inserção · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.345 «As paredes de fachada à flexão pelo vento»; 0.254 «O pilar recorta a parede no papel»; 0.227 «Os pilares circulares, em L e em T»; 0.211 «Pilares a partir do desenho»

#### Cobertura

- **Como se usa:** Quatro águas, 30°, beirado 0,50 m: clique dentro das paredes fechadas — a cobertura assenta no topo delas. (Tab muda o contorno.)
- **Teclas:** Tab: pelas paredes → retângulo → polígono → a partir de uma face · X / Y: bloquear o eixo · Delete: apagar o último canto
- **Passos de teste (TESTAR.md):** 0.390 «Cobertura orgânica»; 0.385 «Os blocos da cobertura no 3D»; 0.382 «Lajes e coberturas: as pegas só a arrastar»; 0.356 «O telhado por blocos mais à mão»; 0.278 «Tipos de cobertura»; 0.276 «Madeiramento da cobertura»

#### Perfil da cobertura

- **O que faz:** Selecione uma cobertura sobre um retângulo e uma face plana desenhada (a secção, à medida real, de pé atravessada ou no chão): a cobertura passa a essa secção, ao meio do vão e com o ponto mais baixo à altura do beirado, corrida ao comprido.
- **Passos de teste (TESTAR.md):** 0.251 «A cobertura com um perfil desenhado»

#### Calha

- **Como se usa:** Calha: passe o rato por uma cobertura — mostra o beirado mais próximo — e clique: a calha fica ao longo dele, por fora, sob a aresta de cima. Clique nos beirados vizinhos: as calhas ligam-se nos cantos. Esc: Selecionar.
- **Passos de teste (TESTAR.md):** 0.438 «Calha em meia-cana e tubos de queda»; 0.384 «A calha à altura certa e ligada nos cantos»

#### Ralo

- **Como se usa:** Clique numa cobertura onde fica o ralo. Esc: Selecionar.
- **Teclas:** Clique: um ralo ali · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.482 «A fita organizada como a do Revit»

#### Teto

- **Como se usa:** Teto contínuo (gesso cartonado) a 2,60 m: clique dentro das paredes de um ambiente. (Tab muda o contorno.)
- **Teclas:** Tab: por ambiente → retângulo → polígono · X / Y: bloquear o eixo · Delete: apagar o último canto

#### Laje

- **Como se usa:** Laje de concreto 12 cm: clique no primeiro canto. Na cota do pavimento = laje de piso; num canto do topo das paredes = laje de cobertura. (Tab muda a forma: polígono, círculo, varinha mágica.)
- **Teclas:** Tab: retângulo → polígono → círculo → varinha mágica · X / Y: bloquear o eixo · N: soltar · Delete: apagar o último canto
- **Passos de teste (TESTAR.md):** 0.439 «Elevador com portas de patamar»; 0.433 «Pisos com declive por canto»; 0.422 «Materiais e boas práticas»; 0.410 «Contorno do piso como o perfil da parede; furos desenhados»; 0.382 «Lajes e coberturas: as pegas só a arrastar»; 0.345 «As paredes de fachada à flexão pelo vento»

#### Piso

- **Como se usa:** Piso cerâmico: clique dentro das paredes de um ambiente. (Tab muda o contorno.)
- **Teclas:** Tab: por ambiente → retângulo → polígono · X / Y: bloquear o eixo · Delete: apagar o último canto
- **Passos de teste (TESTAR.md):** 0.433 «Pisos com declive por canto»; 0.410 «Contorno do piso como o perfil da parede; furos desenhados»; 0.231 «As armaduras nos pisos tipo»; 0.214 «Vários pisos de uma vez a partir da nuvem»

#### Editar contorno

- **O que faz:** Mudar o contorno da laje, do piso ou do teto: cantos, arcos (Shift), curvas (Alt), concordâncias e furos (também com dois cliques no elemento)
- **Passos de teste (TESTAR.md):** 0.433 «Pisos com declive por canto»; 0.382 «Lajes e coberturas: as pegas só a arrastar»

#### Fachada de vidro

- **Como se usa:** Fachada de vidro (2,80 m de altura, montantes até 1,50 m, travessas até 1,00 m): clique no início da linha.
- **Teclas:** X / Y: bloquear o eixo vermelho / verde · N: soltar · Shift: bloquear a linha seguida
- **Passos de teste (TESTAR.md):** 0.436 «Fachada de vidro em arco e por face»; 0.252 «A fachada de vidro numa parede curva»; 0.188 «Fachada de vidro embutida numa parede»; 0.181 «Painéis da fachada de vidro»

#### Painel de fachada

- **Como se usa:** Painel opaco: clique numa célula de uma fachada de vidro (as portas só na fila de baixo).
- **Teclas:** Clique: o painel nessa célula · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.181 «Painéis da fachada de vidro»

### Arquitetura ▸ Circulação

#### Guarda

- **Como se usa:** Guarda (barras verticais, 1,00 m): clique nos pontos do caminho; Enter termina, Delete apaga o último. (Tab muda.)
- **Teclas:** Tab: caminho → vazio → escada · Enter: terminar o caminho · Delete: último ponto · Esc: cancelar
- **Passos de teste (TESTAR.md):** 0.419 «Escadas, rampas, guardas, forma dos compartimentos, casas de banho e arrumos»; 0.414 «Painel Propriedades arrumado; tipos guardados e aplicados»; 0.413 «O plano de trabalho fica guardado com o projeto»; 0.261 «Guardas de escada contínuos»; 0.260 «O editor de tipos de guarda»; 0.259 «As cores dos guardas no 3D»

#### Tipos de guarda…

- **O que faz:** Os tipos de guarda do programa e do projeto: criar (duplicando), mudar as suas peças, medidas e materiais, e apagar os que não estão em uso.
- **Passos de teste (TESTAR.md):** 0.260 «O editor de tipos de guarda»; 0.258 «Tipos de guarda-corpo»

#### Rampa

- **Como se usa:** Rampa (Laje de concreto 15 cm, 1,20 m de largura, a subir 0,50 m): clique no meio do pé da rampa.
- **Teclas:** X / Y: bloquear o eixo vermelho / verde · N: soltar · Shift: bloquear a linha seguida
- **Passos de teste (TESTAR.md):** 0.419 «Escadas, rampas, guardas, forma dos compartimentos, casas de banho e arrumos»; 0.205 «Rampas de acesso entre plataformas»

#### Escada

- **Como se usa:** Reta, 1,00 m de largura, a subir 2,80 m: clique no meio do primeiro degrau (no chão).
- **Teclas:** Dois cliques: o pé e o sentido · Pronta: um clique, R: rodar, Espaço: o ponto · X / Y: bloquear o eixo · Esc: cancelar
- **Passos de teste (TESTAR.md):** 0.435 «Escadas prontas a colocar»; 0.419 «Escadas, rampas, guardas, forma dos compartimentos, casas de banho e arrumos»; 0.261 «Guardas de escada contínuos»; 0.257 «Escadas sem linhas a mais no patamar»; 0.256 «As escadas com laje por baixo dos degraus»

#### Elevador

- **Como se usa:** Elevador (caixa 1,60 m × 1,75 m): clique no canto da frente à esquerda; R roda 90°. Sobe até acima do último pavimento. Esc: Selecionar.
- **Passos de teste (TESTAR.md):** 0.439 «Elevador com portas de patamar»

### Arquitetura ▸ Modelo

- **Linha** — o mesmo de Modelagem ▸ Desenhar.

- **Criar componente…** — o mesmo de Modelagem ▸ Criar.

- **Criar grupo…** — o mesmo de Modelagem ▸ Criar.

### Arquitetura ▸ Ambiente e área

#### Ambiente

- **Como se usa:** Ambiente: clique dentro das paredes para fazer o ambiente (o contorno aparece debaixo do rato). Ele acompanha as paredes. Esc: Selecionar.
- **Teclas:** Clique dentro de paredes fechadas · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.475 «Ambientes: o programa de necessidades no painel lateral»; 0.416 «O Verificador: o uso dos ambientes, os fogos e a tipologia»; 0.366 «Os ambientes e o Passeio Virtual»; 0.365 «O ambiente e os efeitos: o sol, a exposição, o vidro, a água e as luzes»; 0.364 «Os movimentos de câmara»; 0.357 «Ambientes e o programa de necessidades»

#### Separador

- **Como se usa:** Separador: clique onde começa a linha que divide dois ambientes sem parede.
- **Passos de teste (TESTAR.md):** 0.298 «A fita por disciplinas e o separador «Modificar | Paredes»»

#### Identificar

- **O que faz:** Um ambiente em cada espaço fechado do pavimento ativo que ainda não tem (paredes, pilares e separadores), numerados.
- **Passos de teste (TESTAR.md):** 0.374 «Ferramentas de arquitetura do addon; os temas do estudo»

#### Áreas

- **O que faz:** A área útil (dos ambientes) e a área bruta (por fora das paredes) de cada pavimento.
- **Passos de teste (TESTAR.md):** 0.374 «Ferramentas de arquitetura do addon; os temas do estudo»

#### Programa de necessidades

- **O que faz:** O programa de necessidades no painel lateral (Ambientes): a lista dos ambientes de cada piso, com o uso e a área pretendida. Clique num ambiente da lista e depois dentro das paredes para o colocar (ou arraste-o para lá): verde quando a área é atingida, laranja para verificar, vermelho nas zonas conflitantes.
- **Passos de teste (TESTAR.md):** 0.475 «Ambientes: o programa de necessidades no painel lateral»; 0.357 «Ambientes e o programa de necessidades»

### Arquitetura ▸ Aberturas

#### Abertura na parede

- **Como se usa:** Clique na face de uma parede reta, num canto da abertura. Esc: Selecionar.
- **Teclas:** Clique: um canto, depois o oposto · largura;altura + Enter · Esc: cancelar / Selecionar
- **Passos de teste (TESTAR.md):** 0.303 «Abertura na parede»

#### Abertura (cobertura / laje)

- **Como se usa:** Clique numa cobertura ou laje no primeiro canto da abertura. Esc: Selecionar.
- **Teclas:** Dois cliques: os cantos · Esc: Selecionar

#### Nicho

- **Como se usa:** Nicho de 0,10 m: clique na face de uma parede reta, num canto do nicho (a profundidade na barra). Esc: Selecionar.
- **Teclas:** Clique: um canto, depois o oposto · largura;altura + Enter · Esc: cancelar / Selecionar
- **Passos de teste (TESTAR.md):** 0.374 «Ferramentas de arquitetura do addon; os temas do estudo»

### Arquitetura ▸ Referência

#### Novo pavimento

- **O que faz:** Acrescenta um pavimento 3 m acima do último e passa a ser o ativo.
- **Passos de teste (TESTAR.md):** 0.439 «Elevador com portas de patamar»; 0.326 «Copiar, Matriz e copiar-colar»; 0.325 «Pequenos defeitos»; 0.231 «As armaduras nos pisos tipo»; 0.222 «A 2.ª ordem»

#### Eixo (grelha estrutural)

- **Como se usa:** Clique no início do eixo (snaps e alinhamentos). Ao longo de Y fica numerado (1, 2, 3…), ao longo de X com letra (A, B, C…). Vários de uma vez: Estrutura ▸ Referência ▸ Gerar eixos…
- **Teclas:** X / Y: bloquear o eixo vermelho / verde · N: soltar · Shift: bloquear a linha seguida

### Arquitetura ▸ Plano de trabalho

- **Plano de trabalho** — o mesmo de Modelagem ▸ Desenhar.

### Arquitetura ▸ Acabamentos

#### Pintura  ·  tecla B

- **Como se usa:** Pintura (Tinta branca): escolha o material no Navegador de Materiais (à direita) e clique nas faces. Ctrl: o elemento todo (num esboço, as faces ligadas da mesma cor); Shift: substituir essa cor em todo o modelo; Alt: conta-gotas.
- **Teclas:** Clique: a face · Ctrl: o elemento / as faces ligadas · Shift: substituir no modelo · Alt: conta-gotas · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.392 «Pintura nos esboços»; 0.391 «Pintura (como o balde do SketchUp)»

#### Painel perfurado

- **Como se usa:** Painel perfurado (furos redondos de 0,03 m, passo 0,06 m): passe o rato por uma parede e clique — a face inteira — ou arraste de um canto ao outro — um retângulo. Clique num painel perfurado para o escolher. Esc: Selecionar.
- **Teclas:** Clique: a face inteira · Arraste: um retângulo · Clique num painel: escolhê-lo · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.389 «Painel perfurado»; 0.173 «Ripado, canelado e painel perfurado»

#### Ripado

- **Como se usa:** Ripado (ripas de 0,04 m × 0,04 m, passo 0,08 m): passe o rato por uma parede e clique — a face inteira — ou arraste de um canto ao outro — um retângulo. Clique num ripado para o escolher. Esc: Selecionar.
- **Teclas:** Clique: a face inteira · Arraste: um retângulo · Clique num ripado: escolhê-lo · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.441 «Ripado solto»; 0.434 «Ripado como ferramenta própria»; 0.173 «Ripado, canelado e painel perfurado»

#### Revestimento de parede

- **Como se usa:** Revestimento (azulejo até 2,10 m): clique na face de uma parede — fica recortado nas portas e janelas e acompanha a parede.
- **Teclas:** Clique: o revestimento nessa face · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.178 «Revestimentos em camadas»; 0.175 «Superfície ondulada (costelas)»; 0.174 «Perfil corrido (rodapés, sancas, frisos)»; 0.173 «Ripado, canelado e painel perfurado»

#### Ranhura

- **Como se usa:** Clique na face de uma parede, à altura da ranhura: corre ao longo da parede toda (Tab: vertical). Esc: Selecionar.
- **Teclas:** Clique: a ranhura ali · Tab: horizontal / vertical · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.305 «Ranhura»

#### Perfil corrido

- **Como se usa:** rodapé: clique dentro de um ambiente — corre ao longo das paredes e à volta dos pilares, e para nas portas. (Tab muda.)
- **Teclas:** Tab: ambiente → caminho · Enter: terminar o caminho · Delete: último ponto · Esc: cancelar
- **Passos de teste (TESTAR.md):** 0.174 «Perfil corrido (rodapés, sancas, frisos)»

#### Rodapé / sanca na parede

- **Como se usa:** rodapé: clique na face de uma parede — corre ao longo dela e das paredes ligadas desse lado, com os cantos em meia-esquadria, e pára nas portas. Esc: Selecionar.
- **Teclas:** Clique: na face da parede, do lado onde fica o perfil · Esc: Selecionar

#### Perfil de uma face

- **O que faz:** Guarda a face plana de esboço escolhida como perfil do projeto, com um nome: a ferramenta Perfil corre-o ao longo de paredes, lajes ou linhas.
- **Passos de teste (TESTAR.md):** 0.245 «Um perfil desenhado por si»

#### Ripado solto

- **Como se usa:** Ripado solto (2,40 m de altura, ripas de 0,04 m, passo 0,08 m): clique no início da linha.
- **Teclas:** X / Y: bloquear o eixo vermelho / verde · N: soltar · Shift: bloquear a linha seguida
- **Passos de teste (TESTAR.md):** 0.441 «Ripado solto»

### Arquitetura ▸ Mobiliário

#### Cozinha

- **Como se usa:** Cozinha: clique onde começa, na face de dentro de uma parede (o ambiente fica desse lado).
- **Teclas:** Clique: o começo, os cantos, o fim · Enter: fazer · F: o outro lado · Esc: recomeçar
- **Passos de teste (TESTAR.md):** 0.170 «Cozinhas e bancada»

#### Móvel

- **Como se usa:** Móvel inferior de 60 cm: passe sobre a face de uma parede — encosta-se a ela, virado para o ambiente, e encosta-se ao lado de outro móvel — e clique. Escreva a largura e Enter para a mudar.
- **Teclas:** Clique: o móvel ali · largura escrita + Enter · R / Shift+R: rodar · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.244 «Os compartimentos de larguras diferentes»; 0.243 «As frentes noutro material e cor»; 0.242 «O forno numa coluna»; 0.241 «As portas de correr»; 0.172 «Divisões e roupeiro»; 0.170 «Cozinhas e bancada»

#### Bancada

- **O que faz:** Põe um tampo de bancada por cima dos módulos baixos escolhidos (nenhum: todos os do pavimento).
- **Passos de teste (TESTAR.md):** 0.170 «Cozinhas e bancada»

#### Eletrodoméstico

- **Como se usa:** placa: passe sobre a face de uma parede — encosta-se a ela, à sua altura (uma placa na bancada, que fica recortada) — e clique.
- **Teclas:** Clique: o aparelho ali · R / Shift+R: rodar · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.171 «Eletrodomésticos e gás»

#### Lista de corte…

- **O que faz:** A lista de corte dos móveis escolhidos (nenhum: todos): os painéis e as ferragens, os ripados e perfurados; para CSV ou para o DXF da CNC.
- **Passos de teste (TESTAR.md):** 0.441 «Ripado solto»; 0.434 «Ripado como ferramenta própria»; 0.389 «Painel perfurado»; 0.169 «Móveis e lista de corte»

---

## 4. Estrutura

Vigas, paredes, pilares, lajes, fundações e a estrutura proposta de uma vez.

**Para testar este separador** (projeto novo, Ctrl+N):

1. **Gerar eixos…** (por exemplo 3 × 3 a 5 m) e **Pilares na grelha**.
2. **Sapatas** debaixo dos pilares, **Vigas entre pilares** e **Lajes** nos vãos (ou, numa casa de paredes, **Propor estrutura…**).
3. **Ações e materiais…**: veja as cargas de cada pavimento; OK.
4. **Analisar a estrutura…**: os esforços de cada barra.
5. **Verificação EC2 / EC6 e armaduras…**: cada elemento OK / atenção / falha; «Pôr as armaduras no modelo» e veja-as em Raio-X.
6. **Lista de armaduras…**, **Quantidades da estrutura…** e **Memória de cálculo…**.

### Estrutura ▸ Selecionar

- **Selecionar** — o mesmo de Modelagem ▸ Selecionar.

### Estrutura ▸ Estrutura

#### Viga

- **Como se usa:** Viga de concreto 20×40, topo a 2,80 m: clique no início da viga (o eixo; snaps e alinhamentos: o topo de um pilar…). Digite a cota do topo (ex.: 2,80) e Enter para a mudar.
- **Teclas:** X / Y: bloquear o eixo vermelho / verde · N: soltar · Shift: bloquear a linha seguida
- **Passos de teste (TESTAR.md):** 0.336 «As cargas nas paredes resistentes»; 0.229 «A dispensa de varões nas vigas»; 0.226 «A segunda camada de varões nas vigas»

- **Parede** — o mesmo de Arquitetura ▸ Construir.

- **Pilar** — o mesmo de Arquitetura ▸ Construir.

- **Laje** — o mesmo de Arquitetura ▸ Construir.

#### Sistema de vigas…

- **O que faz:** Vigas paralelas (ou em grelha) dentro de cada vão fechado pelas vigas selecionadas, por número ou espaçamento. Ficam presas ao vão: refazem-se quando ele muda.

#### Superfície paramétrica

- **Como se usa:** Superfície paramétrica (automática): clique nas curvas de que é feita (0 escolhida(s)) — Enter cria. 1 curva fechada: tampa; 1 aberta: extrusão; 2 ou mais: loft; 4 que se tocam: 4 bordos.
- **Teclas:** Clique: escolher curvas · Enter: criar · Backspace: tirar a última · Botão direito: recomeçar · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.395 «Superfície paramétrica (forma primeiro, construção depois)»

### Estrutura ▸ Fundação

#### Sapata

- **Como se usa:** Clique num pilar: sapata isolada por baixo (Sapata 80×80×40). Clique numa parede: sapata corrida a todo o comprimento (Sapata corrida 50×30). Clique noutro sítio: sapata isolada aí, com o topo na cota do pavimento. Esc termina.
- **Teclas:** R / Shift+R: rodar 90° (sapata solta) · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.342 «As paredes de betão armado pelo Eurocódigo 2»; 0.335 «Paredes resistentes no modelo analítico»; 0.250 «A verificação da sapata combinada»; 0.249 «A sapata combinada»; 0.228 «Os maciços de estacas e as sapatas corridas»

#### Sapata combinada

- **O que faz:** Uma sapata sob os dois pilares selecionados, ao longo da linha entre eles, com o tipo de sapata isolada da ferramenta Sapata (a sua largura; o seu comprimento para lá de cada pilar). Fica presa aos dois: refaz-se quando se movem. As sapatas que já tinham ficam: apague-as se esta as substitui.
- **Passos de teste (TESTAR.md):** 0.250 «A verificação da sapata combinada»; 0.249 «A sapata combinada»

#### Sapatas

- **O que faz:** Uma sapata sob cada pilar selecionado (nenhum: todos os do pavimento), com o tipo de sapata isolada da ferramenta Sapata. Fica presa ao pilar: vai com ele.
- **Passos de teste (TESTAR.md):** 0.228 «Os maciços de estacas e as sapatas corridas»

### Estrutura ▸ Automático

#### Propor estrutura…

- **O que faz:** A partir das paredes do pavimento (ou das selecionadas): pilares nos cantos, encontros e cruzamentos, e mais pelo vão máximo; vigas entre eles ao longo das paredes (as paredes descem até à viga); sapatas. Fazer outra vez substitui a proposta.

#### Vigas entre pilares

- **O que faz:** Vigas entre os pilares selecionados (nenhum: todos os do pavimento) alinhados em X ou Y, só entre vizinhos, de face a face, com o topo no topo dos pilares e o tipo da ferramenta Viga. Ficam presas aos pilares: acompanham-nos.
- **Passos de teste (TESTAR.md):** 0.250 «A verificação da sapata combinada»; 0.231 «As armaduras nos pisos tipo»; 0.229 «A dispensa de varões nas vigas»; 0.228 «Os maciços de estacas e as sapatas corridas»; 0.227 «Os pilares circulares, em L e em T»; 0.226 «A segunda camada de varões nas vigas»

#### Paredes

- **O que faz:** Paredes entre os pilares, sob as vigas selecionadas (nenhuma: todas as do pavimento): de face a face dos pilares, da base deles até à face de baixo da viga, com o tipo da ferramenta Parede. Ficam presas à viga: acompanham-na.
- **Passos de teste (TESTAR.md):** 0.428 «Paredes em planta com as canetas do papel»; 0.409 «Snaps da porta e da janela; cotas interiores com esquinas e com as duas paredes»; 0.383 «As prévias das paredes em volume»; 0.361 «A cota temporária: a relação com as outras paredes»; 0.345 «As paredes de fachada à flexão pelo vento»; 0.342 «As paredes de betão armado pelo Eurocódigo 2»

#### Lajes

- **O que faz:** Uma laje em cada vão fechado pelas vigas selecionadas (nenhuma: todas as do pavimento), entre as faces de dentro das vigas, com o topo no topo delas e o tipo da ferramenta Laje. Fica presa às vigas: refaz-se quando elas mudam. (Por agora, vãos retangulares.)
- **Passos de teste (TESTAR.md):** 0.382 «Lajes e coberturas: as pegas só a arrastar»; 0.224 «A armadura superior das lajes sobre os apoios»; 0.223 «As lajes como cascas»

#### Pilares na grelha

- **O que faz:** Um pilar em cada cruzamento dos eixos selecionados (só eixos de um sentido: onde cruzam os do outro; nenhum: em todos), com o tipo e a altura da ferramenta Pilar. Ficam presos aos eixos: acompanham-nos.
- **Passos de teste (TESTAR.md):** 0.327 «A janela de Ajuda (F1)»; 0.324 «O que falta, com um botão»; 0.321 «Os avisos num balão por cima da vista»

#### Remover proposta

- **O que faz:** Apaga a estrutura proposta neste pavimento; as paredes voltam à altura que tinham.

### Estrutura ▸ Referência

- **Eixo (grelha estrutural)** — o mesmo de Arquitetura ▸ Referência.

#### Gerar eixos…

- **O que faz:** Gera os eixos da grelha estrutural: quantos, numerados e com letras, a que distância (uma medida, ou várias separadas por «;»), a partir de que ponto.
- **Passos de teste (TESTAR.md):** 0.321 «Os avisos num balão por cima da vista»

#### Grelha estrutural…

- **O que faz:** A grelha estrutural: os nomes dos eixos (números ou letras), renumerar, as cotas entre eixos nas plantas, o tamanho das bolhas.

- **Novo pavimento** — o mesmo de Arquitetura ▸ Referência.

### Estrutura ▸ Plano de trabalho

- **Plano de trabalho** — o mesmo de Modelagem ▸ Desenhar.

---

## 5. Instalações

Redes elétricas, de água, de esgoto e AVAC.

**Para testar este separador** (projeto novo, Ctrl+N):

1. Numa casa com uma sala (Arquitetura ▸ Sala), **Louça sanitária**: passe sobre a face de uma parede e clique — a sanita encosta-se a ela.
2. **Propor águas e esgotos** e depois **Ligar à rede**; **Retirar a proposta de águas e esgotos** desfaz.
3. **Propor pontos elétricos…** pelas salas, **Novo circuito** e **Verificar a instalação elétrica…**.
4. **Conduta** e **Grelha / difusor** no teto.
5. **Detetar conflitos…**: uma conduta a atravessar uma viga aparece na lista.

### Instalações ▸ Selecionar

- **Selecionar** — o mesmo de Modelagem ▸ Selecionar.

### Instalações ▸ AVAC

#### Conduta

- **Como se usa:** Conduta 30×20, eixo a 2,50 m: clique no início (snaps e alinhamentos). Digite a cota do eixo (ex.: 0,30) e Enter para a mudar.
- **Teclas:** X / Y: bloquear o eixo vermelho / verde · N: soltar · Shift: bloquear a linha seguida
- **Passos de teste (TESTAR.md):** 0.197 «Condutas em S»

#### Grelha / difusor

- **Como se usa:** Grelha / difusor (difusor quadrado 60 × 60): clique sob um teto — fica embutido nele; uma conduta desenhada até ele desce e liga-se.
- **Teclas:** Clique: um terminal ali · Esc: Selecionar

#### Equipamento AVAC

- **Como se usa:** Unidade de conduta (no teto falso), base a 2,60 m: clique onde fica (o meio da base). R / Shift+R roda 90°. As condutas começam nas suas ligações ou acabam nelas.
- **Teclas:** Clique: um equipamento ali · R / Shift+R: rodar · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.197 «Condutas em S»; 0.196 «Tubagem de refrigerante»

### Instalações ▸ Águas e esgotos

#### Tubo

- **Como se usa:** Tubo PVC Ø50, eixo a 0,30 m: clique no início (snaps e alinhamentos). Digite a cota do eixo (ex.: 0,30) e Enter para a mudar.
- **Teclas:** X / Y: bloquear o eixo vermelho / verde · N: soltar · Shift: bloquear a linha seguida
- **Passos de teste (TESTAR.md):** 0.438 «Calha em meia-cana e tubos de queda»; 0.195 «Ramais a outra altura descem até ao tubo»

#### Louça sanitária

- **Como se usa:** sanita: passe sobre a face de uma parede — encosta-se a ela, virada para o ambiente — e clique. Longe das paredes: no ponto, R / Shift+R roda. A verde, a zona livre à frente.
- **Teclas:** Clique: a louça ali · R / Shift+R: rodar · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.419 «Escadas, rampas, guardas, forma dos compartimentos, casas de banho e arrumos»; 0.416 «O Verificador: o uso dos ambientes, os fogos e a tipologia»

#### Ligar à rede

- **O que faz:** Cada ligação livre das louças selecionadas (nenhuma: todas as do pavimento) leva um ramal até ao tubo mais próximo do seu sistema: o esgoto desce e vai a 2 % até ao coletor ou ao tubo de queda; a água fria e a quente vêm dos seus tubos. Um tê em cada ligação.
- **Passos de teste (TESTAR.md):** 0.200 «Forquilhas a 45° nos esgotos»; 0.199 «O ramal contorna obstáculos»; 0.198 «Gás e eletricidade nos aparelhos»

#### Propor águas e esgotos

- **O que faz:** Em cada ambiente com louças: um tubo de queda no canto junto à sanita (ou à primeira louça), os tubos de água fria e quente ao longo da parede das louças, por cima do teto, e cada louça ligada a eles. Tudo marcado como proposta (retira-se de uma vez).

#### Retirar a proposta de águas e esgotos

- **O que faz:** Retira, do pavimento ativo, os tubos e as ligações que a proposta automática de águas e esgotos fez (os desenhados à mão ficam). Um passo de desfazer.

### Instalações ▸ Eletricidade

#### Ponto elétrico

- **Como se usa:** tomada a 0,30 m do chão: passe sobre a face de uma parede — encosta-se a ela — e clique. Na planta, o seu símbolo.
- **Teclas:** Clique: o ponto ali · R / Shift+R: rodar · Esc: Selecionar

#### Tubo VD

- **Como se usa:** Tubo VD Ø20, eixo a 2,75 m: clique no início (snaps e alinhamentos). Digite a cota do eixo (ex.: 0,30) e Enter para a mudar.
- **Teclas:** X / Y: bloquear o eixo vermelho / verde · N: soltar · Shift: bloquear a linha seguida

#### Luminária

- **Como se usa:** Luminária (painel 60 × 60): clique sob um teto — fica embutida nele.
- **Teclas:** Clique: uma luminária ali · Esc: Selecionar
- **Passos de teste (TESTAR.md):** 0.365 «O ambiente e os efeitos: o sol, a exposição, o vidro, a água e as luzes»

#### Novo circuito

- **O que faz:** Os pontos elétricos e as luminárias selecionados fazem um circuito novo (C1, C2…) do tipo que eles dizem, no quadro do seu pavimento; o quadro de cargas (Tabelas ▸ Circuitos) mostra a potência, a corrente e a verificação.

#### Ligar ao quadro (canalizações)

- **O que faz:** Os circuitos do pavimento ainda sem canalização ganham os seus tubos VD: do quadro a cada ponto, um a seguir ao outro (o mais próximo), a subir a parede até 2,75 m, por cima do teto, e a descer até ao ponto seguinte.

#### Propor pontos elétricos…

- **O que faz:** Para os ambientes do pavimento: pela função de cada um (pelo nome: Quarto, Sala, Cozinha, WC, Corredor…), as luminárias no teto, um interruptor junto a cada porta e as tomadas pelas paredes — veja-as antes, mude as quantidades e aplique.

#### Retirar a proposta elétrica

- **O que faz:** Apaga os pontos e as luminárias que a proposta elétrica pôs neste pavimento.

#### Verificar a instalação elétrica…

- **O que faz:** O que falta ou está mal neste pavimento: pontos sem circuito, circuitos sem quadro, sem canalização ou que não passam no cálculo, ambientes sem luminária.

### Instalações ▸ Plano de trabalho

- **Plano de trabalho** — o mesmo de Modelagem ▸ Desenhar.

---

## 6. Inserir

Vincular desenhos CAD e nuvens de pontos; importar imagens, modelos 3D, componentes e pontos de levantamento.

### Inserir ▸ Vincular

#### Ligar um desenho DXF/DWG…

- **O que faz:** Liga uma planta em DXF ou DWG ao pavimento ativo, como linhas para desenhar por cima (nas coordenadas do levantamento quando estão perto delas).
- **Passos de teste (TESTAR.md):** 0.286 «DWG»

#### Ligar uma nuvem de pontos…

- **O que faz:** Liga uma nuvem de pontos de um levantamento (XYZ, PTS, PLY, LAS, LAZ, E57) ao pavimento ativo, para modelar por cima dela.
- **Passos de teste (TESTAR.md):** 0.161 «Ligar uma nuvem de pontos»

#### Desenhos CAD ligados…

- **O que faz:** Os desenhos CAD ligados: unidades, visível, bloqueado e as suas camadas.

#### Nuvens de pontos ligadas…

- **O que faz:** As nuvens de pontos ligadas: o pavimento, os pontos mostrados, as unidades, o tamanho dos pontos, visível; ligar outra, apagar.

### Inserir ▸ Importar

#### Importar imagem de fundo…

- **O que faz:** Põe uma imagem (uma planta digitalizada…) deitada no pavimento ativo; a seguir, a ferramenta Calibrar imagem acerta-lhe a escala com uma medida conhecida.

#### Importar modelo 3D…

- **O que faz:** Traz um modelo 3D do SketchUp (SKP), do Rhino (3DM), em glTF / GLB, OBJ ou STL: como componente — mobiliário, equipamento, com as cores dos materiais, colocado com um clique e depois na biblioteca — ou como esboço, com as faces inteiras, para editar.
- **Passos de teste (TESTAR.md):** 0.351 «Importar modelos 3D»

#### Imagens de fundo…

- **O que faz:** As imagens de fundo: largura, opacidade, visível, bloqueada; importar, calibrar, apagar.
- **Passos de teste (TESTAR.md):** 0.209 «Recortar a imagem de fundo»

#### Trazer componentes de outro projeto…

- **O que faz:** Traz para a biblioteca do projeto os componentes (móveis, louças…) de outro ficheiro IFC, para pôr cópias deles.

#### Importar pontos de levantamento…

- **O que faz:** Faz o terreno a partir de um ficheiro de pontos de levantamento (x y z por linha: CSV, TXT, XYZ), com as curvas de nível.

#### Terreno a partir de um DXF/DWG…

- **O que faz:** Faz o terreno a partir de um levantamento em DXF/DWG: os pontos, curvas de nível e cotas escritas das camadas que escolher.

---

## 7. Anotar

Cotas, desenho, textos, etiquetas e símbolos.

**Para testar este separador** (projeto novo, Ctrl+N):

1. **Planta do pavimento ativo** (F4).
2. **Cotar paredes**, **Cotar fachadas** e **Cotar salas**; **Estilo das cotas…** muda todas.
3. **Corte**: dois cliques na planta e o lado para onde se olha; F5 volta ao último.
4. **Pormenor**: um retângulo à volta de um canto da planta.
5. **Desenho 2D**: linhas, textos e regiões tramadas na planta.

### Anotar ▸ Selecionar

- **Selecionar** — o mesmo de Modelagem ▸ Selecionar.

### Anotar ▸ Cotas

- **Cota** — o mesmo de Modelagem ▸ Medir.

#### Cotas exteriores

- **Como se usa:** Abra a planta do pavimento (F4): as cotas automáticas fazem-se na planta.
- **Passos de teste (TESTAR.md):** 0.399 «Cotas exteriores num clique»

#### Cotas interiores

- **Como se usa:** Abra a planta do pavimento (F4): as cotas automáticas fazem-se na planta.
- **Passos de teste (TESTAR.md):** 0.409 «Snaps da porta e da janela; cotas interiores com esquinas e com as duas paredes»; 0.408 «Cotas interiores: alinham-se com a parede mais perto; Ctrl+clique acrescenta»; 0.400 «Cotas interiores num clique»

#### Cotar paredes (cadeias e totais)

- **O que faz:** Na planta do pavimento ativo, cota as paredes escolhidas (nenhuma: todas) pelo lado de fora: a cadeia pelas portas e janelas e o comprimento total. Outra vez: substitui-as.

#### Cotar fachadas

- **O que faz:** Cotar fachadas: à volta do edifício, em cada lado, os cantos e os vãos, os cantos e o comprimento total (outra vez: refaz)
- **Passos de teste (TESTAR.md):** 0.398 «Tipos de cota (o motor da aparência)»

#### Cotar ambientes

- **O que faz:** Cotar ambientes: a largura e a profundidade de cada ambiente, de parede a parede (outra vez: refaz)

#### Tipos de cota…

- **O que faz:** Tipos de cota: a aparência das cotas — marcas, linhas, linhas de chamada, texto, unidades (milímetros em expoente, arredondamento), altura dos vãos — com uma amostra em papel; duplicar, mudar o nome, apagar.
- **Passos de teste (TESTAR.md):** 0.398 «Tipos de cota (o motor da aparência)»; 0.193 «Tipos de cota»

### Anotar ▸ Desenho

#### Desenho 2D

- **Como se usa:** Desenho 2D: abra uma planta, um corte ou um alçado — o desenho fica nessa vista.
- **Teclas:** Tab: linha → polilinha → retângulo → círculo → arco → região → texto → cota de nível → marca de nível · Enter: acabar · Delete: tirar o último ponto · Esc: recomeçar
- **Passos de teste (TESTAR.md):** 0.323 «Cota, Desenho 2D e Pormenor abrem a planta»

- **Fita métrica** — o mesmo de Modelagem ▸ Medir.

### Anotar ▸ Etiquetas e tabelas

- **Ambiente** — o mesmo de Arquitetura ▸ Ambiente e área.

#### Numerar portas e janelas

- **O que faz:** Todas as portas (P1, P2…) e janelas (J1, J2…) numeradas de novo, pavimento a pavimento, pela ordem de leitura da planta

#### Notas-chave do projeto…

- **O que faz:** A tabela de notas-chave do projeto (código e texto), para as etiquetas e a legenda.
- **Passos de teste (TESTAR.md):** 0.248 «A tabela de notas-chave do projeto»

### Anotar ▸ Símbolo

#### Símbolos…

- **O que faz:** Como são os símbolos das vistas: a cabeça e a linha do corte, a marca do alçado, a chamada do pormenor, a marca de nível — forma, seta, tamanhos, tipo de linha e caneta —, com o desenho ao lado. Vale para todas as plantas, cortes, folhas, PDF e DXF.
- **Passos de teste (TESTAR.md):** 0.360 «O gerador de símbolos»

---

## 8. Analisar

Cálculo da estrutura e os seus mapas; o Verificador (regulamentos), IFC e IDS.

### Analisar ▸ Cálculo

#### Analisar a estrutura…

- **O que faz:** Analisa a estrutura com as suas ações: os esforços e as deformações de cada barra, o caminho das cargas, os deslocamentos pelo vento e o sismo.
- **Passos de teste (TESTAR.md):** 0.336 «As cargas nas paredes resistentes»; 0.165 «Analisar a estrutura»

#### Modelo analítico e verificação…

- **O que faz:** Faz de novo o modelo analítico a partir dos pilares, vigas, sapatas, lajes e paredes resistentes, e lista os seus problemas (pilares sem apoio, vigas soltas…).
- **Passos de teste (TESTAR.md):** 0.163 «Modelo analítico e verificação»

#### Ações e materiais…

- **O que faz:** As ações e os materiais da estrutura: betão, aço, uso dos pisos, acabamentos, vento, sismo, neve, solo, alvenaria — com as cargas de cada pavimento.
- **Passos de teste (TESTAR.md):** 0.164 «Ações e materiais»

#### Modelo analítico

- **O que faz:** Mostra o modelo analítico (barras, nós, apoios) por cima do modelo.
- **Passos de teste (TESTAR.md):** 0.335 «Paredes resistentes no modelo analítico»; 0.163 «Modelo analítico e verificação»

#### Diagramas de momentos

- **O que faz:** Analisar a estrutura e desenhar sobre o modelo o diagrama de momentos fletores de cada barra (1,35G + 1,50Q), do lado das fibras traccionadas
- **Passos de teste (TESTAR.md):** 0.220 «Os diagramas de momentos»

#### Verificação EC2 / EC6 e armaduras…

- **O que faz:** Verifica cada elemento pelo Eurocódigo 2 (betão) e as paredes de alvenaria pelo 6, com os esforços da análise; escolhe as armaduras e pode pô-las no modelo.

### Analisar ▸ Mapas

#### Lista de armaduras…

- **O que faz:** A lista das armaduras do modelo por posição, com os totais; para Excel ou CSV.
- **Passos de teste (TESTAR.md):** 0.230 «As emendas dos varões compridos»; 0.229 «A dispensa de varões nas vigas»; 0.224 «A armadura superior das lajes sobre os apoios»; 0.166 «Verificação EC2 e armaduras»

#### Quantidades da estrutura…

- **O que faz:** O betão, a cofragem e o aço de cada elemento estrutural, e os totais; para Excel ou CSV.
- **Passos de teste (TESTAR.md):** 0.167 «Quantidades da estrutura e memória de cálculo»

#### Memória de cálculo…

- **O que faz:** A memória de cálculo da estrutura (ações, modelo, análise, verificação, quantidades, armaduras) numa página HTML ou num PDF.
- **Passos de teste (TESTAR.md):** 0.233 «A memória de cálculo com os desenhos»; 0.167 «Quantidades da estrutura e memória de cálculo»

### Analisar ▸ Verificar

#### Verificação

- **O que faz:** O painel da Verificação: tudo o que o Verificador encontrou, por fogo ou por regulamento — um clique leva ao sítio; «Porquê» diz a regra; «Exceção…» aceita uma falha com a razão escrita. E as outras verificações do programa num só lugar.
- **Passos de teste (TESTAR.md):** 0.425 «A ficha de verificação»; 0.418 «O painel Verificação e as exceções»; 0.337 «A verificação das paredes de alvenaria (Eurocódigo 6)»; 0.250 «A verificação da sapata combinada»; 0.166 «Verificação EC2 e armaduras»; 0.163 «Modelo analítico e verificação»

#### Regulamentos do projeto…

- **O que faz:** O país onde o projeto se constrói (os seus regulamentos: Cabo Verde — CTE; Portugal — RGEU…), o uso do edifício, o tipo de obra e a altura. O Verificador vigia o projeto por eles e diz no rodapé o que falha.
- **Passos de teste (TESTAR.md):** 0.431 «Avisos do modelo»; 0.426 «O editor de regulamentos»; 0.423 «O lote e o plano municipal»; 0.422 «Materiais e boas práticas»; 0.421 «Portugal: RGEU e DL 163/2006»; 0.417 «O Verificador: as regras e o alerta vermelho no rodapé»

#### Ficha de verificação…

- **O que faz:** A ficha de verificação para o processo de licenciamento: o projeto, os regulamentos, o lote e o plano municipal, o quadro de áreas de cada fogo e cada regra verificada com o seu resultado e as exceções — em PDF ou numa folha de cálculo (XLSX).
- **Passos de teste (TESTAR.md):** 0.425 «A ficha de verificação»

#### Editar regulamentos…

- **O que faz:** Os regulamentos que o Verificador usa, regra a regra: os limites, a gravidade, se o valor já foi conferido, ligar e desligar. Os do programa ficam como estão — o que se muda guarda-se numa cópia sua. E outro país, a partir de um que já existe.
- **Passos de teste (TESTAR.md):** 0.426 «O editor de regulamentos»

#### Verificar IFC para certificação

- **O que faz:** Verifica o IFC como o pede a certificação: o cabeçalho e as regras do esquema, a estrutura de pavimentos, as unidades, os identificadores, as formas e os nomes, as quantidades, os tipos, os materiais e a georreferência — cada falta no painel de requisitos.

#### Verificar com requisitos IDS…

- **O que faz:** Verifica o modelo contra um ficheiro IDS (os requisitos de informação do dono de obra): cada requisito cumprido ou não, e os elementos em falta.

#### Dados IFC em falta…

- **O que faz:** Antes de entregar: por classe e propriedade, quantos elementos ainda não têm valor; um duplo clique seleciona-os.
- **Passos de teste (TESTAR.md):** 0.273 «Dados IFC em falta, antes de entregar»

---

## 9. Massa e Estudos

Estudos volumétricos: linhas, retângulos, empurrar/puxar; depois classificar em BIM.

**Para testar este separador** (projeto novo, Ctrl+N):

1. **Importar imagem de fundo…** com `planta_digitalizada.png`; a seguir **Calibrar imagem**: clique nas duas pontas da cota vermelha e escreva `8` Enter.
2. Desenhe por cima com **Linha**, **Retângulo** e **Push/Pull**.
3. Ligue `planta_cad.dxf` (Início ▸ Importar) e use **Modelo a partir do desenho…**: escolha as camadas das paredes e OK.
4. Ligue `sala_digitalizada.ply` (Ligar uma nuvem de pontos…) e use **Modelo a partir da nuvem…**.

### Massa e Estudos ▸ Selecionar

- **Selecionar** — o mesmo de Modelagem ▸ Selecionar.

### Massa e Estudos ▸ Imagem de fundo

- **Importar imagem de fundo…** — o mesmo de Inserir ▸ Importar.

#### Calibrar imagem

- **Como se usa:** Calibrar imagem: importe primeiro uma imagem (Inserir ▸ Importar ▸ Imagem de fundo).
- **Passos de teste (TESTAR.md):** 0.154 «Imagem de fundo»

### Massa e Estudos ▸ Desenhar

- **Linha** — o mesmo de Modelagem ▸ Desenhar.

- **Arco** — o mesmo de Modelagem ▸ Desenhar.

- **Retângulo** — o mesmo de Modelagem ▸ Desenhar.

- **Círculo** — o mesmo de Modelagem ▸ Desenhar.

- **Linha livre** — o mesmo de Modelagem ▸ Desenhar.

- **Curva de Bézier** — o mesmo de Modelagem ▸ Desenhar.

- **Plano de trabalho** — o mesmo de Modelagem ▸ Desenhar.

- **Push/Pull** — o mesmo de Modelagem ▸ Desenhar.

### Massa e Estudos ▸ Formas livres

- **Superfície paramétrica** — o mesmo de Estrutura ▸ Estrutura.

#### Anel de controlo

- **O que faz:** Copia a curva selecionada (a mais alta) 1 m acima, a 75 % do tamanho, e deixa a pilha selecionada: repita e depois Superfície paramétrica faz o loft por todas (cúpula, torre).
- **Passos de teste (TESTAR.md):** 0.395 «Superfície paramétrica (forma primeiro, construção depois)»

### Massa e Estudos ▸ Modificar

- **Mover** — o mesmo de Modelagem ▸ Modificar.

- **Copiar** — o mesmo de Modelagem ▸ Modificar.

- **Rodar** — o mesmo de Modelagem ▸ Modificar.

- **Espelhar** — o mesmo de Modelagem ▸ Modificar.

- **Alinhar** — o mesmo de Modelagem ▸ Modificar.

- **Escala** — o mesmo de Modelagem ▸ Modificar.

- **Matriz** — o mesmo de Modelagem ▸ Modificar.

- **Offset** — o mesmo de Modelagem ▸ Modificar.

### Massa e Estudos ▸ Medir

- **Fita métrica** — o mesmo de Modelagem ▸ Medir.

### Massa e Estudos ▸ Materiais

- **Pintura** — o mesmo de Arquitetura ▸ Acabamentos.

### Massa e Estudos ▸ Passar a BIM

- **Classificar como** — o mesmo de Modelagem ▸ Criar.

#### Modelo a partir do desenho…

- **O que faz:** Lê as paredes de um desenho DXF ligado (pares de linhas paralelas nas camadas que escolher), mostra-as e faz o modelo, cada uma do tipo da sua espessura.
- **Passos de teste (TESTAR.md):** 0.286 «DWG»; 0.211 «Pilares a partir do desenho»; 0.210 «Paredes curvas a partir do desenho»

#### Modelo a partir da nuvem…

- **O que faz:** Lê numa nuvem de pontos ligada o chão, a altura e as paredes (e as portas e janelas), mostra-as e faz o modelo com a laje do piso.
- **Passos de teste (TESTAR.md):** 0.162 «Modelo a partir da nuvem»

---

## 10. Terreno

Topografia, plataformas, curvas de nível e movimentação de terras.

**Para testar este separador** (projeto novo, Ctrl+N):

1. **Importar pontos de levantamento…** com `levantamento.csv`: o terreno aparece com as curvas de nível.
2. Na planta (F4), **Plataforma**: escreva a cota (`1,5` Enter) e clique em dois cantos opostos — a plataforma fica cortada no terreno, com os taludes.
3. **Aterro e escavação…**: a terra tirada e posta.
4. **Inclinações do terreno**: o terreno pintado pela inclinação.
5. **Rampa de acesso** entre duas plataformas.

### Terreno ▸ Selecionar

- **Selecionar** — o mesmo de Modelagem ▸ Selecionar.

### Terreno ▸ Localização

#### Localização do terreno…

- **O que faz:** A latitude, a longitude e a cota do terreno: o sítio do modelo no mundo (para a certificação, os outros programas e o sol do render).
- **Passos de teste (TESTAR.md):** 0.316 «Sombras no papel e o sol à escolha»

### Terreno ▸ Levantamento

- **Importar pontos de levantamento…** — o mesmo de Inserir ▸ Importar.

- **Terreno a partir de um DXF/DWG…** — o mesmo de Inserir ▸ Importar.

#### Terreno por pontos

- **Como se usa:** Escreva a cota do ponto (ex.: 12,50) e clique onde ele fica. Enter faz o terreno.
- **Passos de teste (TESTAR.md):** 0.155 «Terreno por pontos»

### Terreno ▸ Lote

#### Lote

- **Como se usa:** Lote: clique num canto (Tab: polígono, contorno do terreno).
- **Teclas:** Tab: retângulo → polígono → círculo → varinha mágica · X / Y: bloquear o eixo · N: soltar · Delete: apagar o último canto
- **Passos de teste (TESTAR.md):** 0.424 «Alturas das fachadas e afastamentos da lei»; 0.423 «O lote e o plano municipal»

### Terreno ▸ Plataformas

#### Plataforma

- **Como se usa:** Plataforma: faça primeiro o terreno (ou selecione aquele em que a quer pôr).
- **Passos de teste (TESTAR.md):** 0.205 «Rampas de acesso entre plataformas»; 0.204 «Editar uma plataforma»; 0.157 «Plataformas, aterro e escavação»

#### Rampa de acesso

- **Como se usa:** Rampa de acesso: faça primeiro o terreno (ou selecione aquele em que a quer pôr).
- **Passos de teste (TESTAR.md):** 0.205 «Rampas de acesso entre plataformas»

#### Editar plataforma

- **O que faz:** Mudar o contorno de uma plataforma já feita pelos cantos: mover, acrescentar e tirar cantos (os taludes e o terreno à volta refazem-se)
- **Passos de teste (TESTAR.md):** 0.204 «Editar uma plataforma»

### Terreno ▸ Movimento de terras

#### Aterro e escavação…

- **O que faz:** As plataformas do terreno com a terra que cada uma tira e põe, e os totais.
- **Passos de teste (TESTAR.md):** 0.157 «Plataformas, aterro e escavação»

#### Inclinações do terreno

- **O que faz:** Pinta o terreno pela inclinação, com a legenda (também nas folhas da planta).
- **Passos de teste (TESTAR.md):** 0.156 «Terreno de um DXF, inclinações e cotas de nível»

---

## 11. Colaborar

Notas, trabalho em equipa e colisões.

**Para testar este separador** (projeto novo, Ctrl+N):

1. Guarde o projeto e **Partilhar projeto numa pasta…** (uma pasta de teste).
2. Noutra cópia do programa (ou depois de fechar), **Abrir projeto partilhado…** e **Sincronizar com o central** (Ctrl+Alt+S).
3. **Verificar IFC para certificação** e **Dados IFC em falta…**: o que falta ao modelo.
4. **Nova nota de coordenação (BCF)…**: título, descrição e a vista como está.

### Colaborar ▸ Notas

#### Nova nota de coordenação (BCF)…

- **O que faz:** Uma nota de coordenação (BCF): um título e uma descrição, com a vista como está, os elementos escolhidos e uma imagem.

### Colaborar ▸ Equipa

#### Partilhar projeto numa pasta…

- **O que faz:** Partilha o projeto numa pasta (da rede, do OneDrive…): fica lá o modelo central e cada um trabalha numa cópia sua, que sincroniza.

#### Abrir projeto partilhado…

- **O que faz:** Abre um projeto partilhado numa pasta: trabalha-se numa cópia local, que se sincroniza com o central.

#### Sincronizar com o central  ·  tecla Ctrl+Alt+S

- **O que faz:** Num projeto partilhado: manda as suas alterações para o modelo central e traz as da equipa.

#### Reservar as vistas (cortes, folhas, cotas)

- **O que faz:** Num projeto partilhado: reserva para si os cortes, as folhas, as cotas e os modelos de vista, para ninguém os mudar ao mesmo tempo.

#### Devolver as minhas reservas

- **O que faz:** Num projeto partilhado: devolve tudo o que reservou, para a equipa o poder mudar.

### Colaborar ▸ Coordenação

#### Detetar conflitos…

- **O que faz:** Onde as instalações atravessam a estrutura (vigas, pilares, lajes), onde se cruzam entre si e, se quiser, onde atravessam paredes: a lista, o estado de cada conflito, notas BCF e um relatório.

---

## 12. Visualizar

Estilos gráficos, tema, render e apresentação, vistas (plantas, cortes, 3D), câmaras e painéis.

**Para testar este separador** (projeto novo, Ctrl+N):

1. F8, F2 e F3: isométrica, topo e frente. **Nova vista 3D (guardar esta)** guarda a câmara.
2. **Caixa de corte (3D)** (F6): arraste as faces da caixa.
3. **Estilos de vista…**: os estilos (sombreado, realista…) e as suas opções — sombras, arestas, transparência, tramas.
4. **Posicionar câmara** num ponto do chão e **Caminhar** com as setas.
5. **Tema escuro** e **Vistas escuras**; **Tema claro** volta.

### Visualizar ▸ Gráficos

#### Estilos de vista…

- **O que faz:** Criar e editar estilos de vista: faces sombreadas ou em cores consistentes, cores dos materiais, arestas, sombras, padrões de superfície, transparência e cortes
- **Passos de teste (TESTAR.md):** 0.318 «Padrões do projeto, tramas por categoria e a biblioteca de materiais»; 0.315 «Estilos de vista com tramas e sombreamentos»

#### Estilos gráficos…

- **O que faz:** Como os desenhos ficam no papel: a trama de cada material cortado e as canetas (cortado, visto, tramado, cotas).
- **Passos de teste (TESTAR.md):** 0.340 «A revisão do tema escuro»

- **Símbolos…** — o mesmo de Anotar ▸ Símbolo.

#### Modelos de vista…

- **O que faz:** Modelos de vista: o que uma vista mostra (categorias, estilo, escala…) guardado com um nome, para aplicar a outras vistas.

#### Tramas por elemento…

- **O que faz:** Dá aos elementos selecionados tramas próprias nesta vista — no corte e na superfície —, por cima das da categoria e dos materiais (como «Substituir gráficos na vista ▸ Por elemento» do Revit).
- **Passos de teste (TESTAR.md):** 0.332 «Alinhar os padrões numa face»; 0.331 «Tramas por elemento numa vista»

- **Imagens de fundo…** — o mesmo de Inserir ▸ Importar.

- **Desenhos CAD ligados…** — o mesmo de Inserir ▸ Vincular.

- **Nuvens de pontos ligadas…** — o mesmo de Inserir ▸ Vincular.

- **Modelo analítico** — o mesmo de Analisar ▸ Cálculo.

#### Repor os padrões alinhados

- **O que faz:** Os padrões dos elementos selecionados (azulejo, tijolo…) voltam a ficar como estavam antes de alinhados à mão.
- **Passos de teste (TESTAR.md):** 0.332 «Alinhar os padrões numa face»

#### Linhas finas

- **O que faz:** No ecrã, as linhas do corte com 1 píxel, seja qual for o zoom (para desenhar com rigor). Desligado: com as canetas do papel — o corte grosso, as camadas e a trama finas, que mudam com o zoom. O papel e o PDF não mudam.
- **Passos de teste (TESTAR.md):** 0.428 «Paredes em planta com as canetas do papel»

### Visualizar ▸ Apresentação

#### Render realista…

- **O que faz:** A vista como se vê, numa imagem fotográfica: a luz do céu e do sol a ressaltar nas superfícies, sombras suaves, vidro. Corre à parte — pode continuar a trabalhar — e a imagem vai afinando.
- **Passos de teste (TESTAR.md):** 0.343 «O render realista»

#### Panorama 360°…

- **O que faz:** Um panorama 360° em render realista, tirado de onde está a câmara do 3D (ponha-a dentro de uma sala, à altura dos olhos): fica guardado com o projeto e vai para o ArqSynth Presentation como um ponto 360° na planta do seu pavimento.

- **Exportar Gaussian splat (apresentação)…** — o mesmo de Início ▸ Exportar.

#### Cenas da apresentação

- **O que faz:** Abre a interface do ArqSynth Presentation (o ícone da barra da esquerda): as cenas que vão para o Presentation, pela ordem da apresentação, com a câmara, as camadas, a transição, o efeito, o sol e a legenda de cada uma, e a exportação.
- **Passos de teste (TESTAR.md):** 0.480 «ArqSynth Presentation na barra da esquerda»

- **Exportar imagem da vista…** — o mesmo de Início ▸ Exportar.

- **Exportar modelo 3D…** — o mesmo de Início ▸ Exportar.

- **Para o ArqSynth Presentation…** — o mesmo de Início ▸ Exportar.

### Visualizar ▸ Criar

#### Vista isométrica  ·  tecla F8

- **O que faz:** A vista 3D em isométrica, com o modelo todo (F8).

#### Vista de topo  ·  tecla F2

- **O que faz:** A vista de cima (F2).

#### Vista de frente  ·  tecla F3

- **O que faz:** A vista de frente (F3).

#### Nova vista 3D (guardar esta)  ·  tecla Ctrl+Shift+3

- **O que faz:** Guarda a vista 3D como está (a câmara, o estilo, a caixa de corte) numa vista nova do navegador.

#### Planta do pavimento ativo (corte a 1,20 m)  ·  tecla F4

- **O que faz:** Planta do pavimento ativo (corte a 1,20 m) (F4)

#### Corte

- **Como se usa:** Corte: clique no início da linha de corte (ou numa extremidade, num eixo…).
- **Passos de teste (TESTAR.md):** 0.429 «Editar tipo com o corte ao vivo»; 0.362 «Para o ArqSynth Presentation: o pacote»; 0.358 «A linha de corte editável»; 0.319 «Escolher a trama da superfície e do corte»; 0.317 «As tramas de corte e de superfície no ecrã»; 0.314 «Os materiais com gráficos completos (superfície e corte)»

#### Pormenor

- **Como se usa:** Pormenor: abra uma planta, um corte ou um alçado — o pormenor é um pedaço dele.
- **Teclas:** Dois cliques: os cantos · Esc: recomeçar
- **Passos de teste (TESTAR.md):** 0.323 «Cota, Desenho 2D e Pormenor abrem a planta»; 0.237 «Os pormenores tipo»

#### Último corte  ·  tecla F5

- **O que faz:** Abre outra vez o último corte (F5).

#### Caixa de corte  ·  tecla F6

- **O que faz:** Liga ou desliga a caixa de corte do 3D: arraste as suas faces para cortar o modelo (F6).
- **Passos de teste (TESTAR.md):** 0.347 «O guia de todas as ferramentas»

#### Caixa de corte à volta da seleção  ·  tecla Shift+F6

- **O que faz:** Põe a caixa de corte à volta do que está escolhido: vê-se só isso (Shift+F6).

### Visualizar ▸ Câmara

#### Posicionar câmara

- **Como se usa:** Posicionar câmara: clique onde fica de pé — os olhos ficam a 1,60 m por cima. Escreva outra altura (ex.: 1,20) e Enter.
- **Passos de teste (TESTAR.md):** 0.343 «O render realista»

#### Olhar em volta

- **Como se usa:** Olhar em volta: arraste para rodar a cabeça; a câmara fica no sítio. Caminhar e Orbitar na barra de navegação; Espaço volta a Selecionar.
- **Passos de teste (TESTAR.md):** 0.343 «O render realista»

#### Caminhar

- **Como se usa:** Caminhar: arraste para cima/baixo para andar, para os lados para virar (Shift: subir/descer; Ctrl: mais depressa; Alt: atravessar paredes). Também as setas do teclado. Espaço volta a Selecionar.

### Visualizar ▸ Janelas

#### Painéis

- **Escolhas:** Propriedades · Pavimentos · Navegador do Projeto · Regras gráficas · Requisitos (IDS) · Notas (BCF) · Tabelas · Verificação
- **Passos de teste (TESTAR.md):** 0.280 «Chapas e painéis»; 0.181 «Painéis da fachada de vidro»

#### Vista seguinte  ·  tecla Ctrl+Tab

- **O que faz:** Passa para a vista aberta seguinte (o separador à direita, Ctrl+Tab).

#### Vista anterior  ·  tecla Ctrl+Shift+Tab

- **O que faz:** Passa para a vista aberta anterior (Ctrl+Shift+Tab).

#### Fechar a vista  ·  tecla Ctrl+W

- **O que faz:** Fecha a vista que está à frente (Ctrl+W); fechadas todas, volta a vista 3D.

### Visualizar ▸ Tema

#### Tema claro

- **O que faz:** A interface clara (fica neste computador, não no projeto).
- **Passos de teste (TESTAR.md):** 0.339 «As janelas por cima, no tema escuro»

#### Tema escuro

- **O que faz:** A interface escura (fica neste computador, não no projeto).
- **Passos de teste (TESTAR.md):** 0.340 «A revisão do tema escuro»; 0.339 «As janelas por cima, no tema escuro»; 0.338 «O tema escuro»

#### Vistas escuras

- **O que faz:** O fundo das vistas (3D, plantas, cortes e alçados) escuro, com as linhas e os textos claros. À parte do tema da interface; as folhas e o que se exporta continuam em papel branco.
- **Passos de teste (TESTAR.md):** 0.361 «A cota temporária: a relação com as outras paredes»

#### Bege

- **O que faz:** A paleta bege do estudo de interface (fica neste computador).
- **Passos de teste (TESTAR.md):** 0.376 «Os temas à vista»; 0.374 «Ferramentas de arquitetura do addon; os temas do estudo»

#### Pedra

- **O que faz:** A paleta pedra do estudo de interface.
- **Passos de teste (TESTAR.md):** 0.376 «Os temas à vista»; 0.374 «Ferramentas de arquitetura do addon; os temas do estudo»

#### Azul · Revit

- **O que faz:** A paleta azul-acinzentada inspirada no Revit.
- **Passos de teste (TESTAR.md):** 0.393 «Modelos, Fase 1 (o gestor e o modelo de fábrica)»

#### Escuro

- **O que faz:** A paleta escura (castanho) do estudo de interface.
- **Passos de teste (TESTAR.md):** 0.341 «O fundo escuro nas vistas»; 0.340 «A revisão do tema escuro»; 0.339 «As janelas por cima, no tema escuro»; 0.338 «O tema escuro»

#### Grafite

- **O que faz:** A paleta grafite do estudo de interface.
- **Passos de teste (TESTAR.md):** 0.393 «Modelos, Fase 1 (o gestor e o modelo de fábrica)»; 0.376 «Os temas à vista»; 0.374 «Ferramentas de arquitetura do addon; os temas do estudo»

#### Explorar cores…

- **O que faz:** Afinar as nove cores da interface (barra, fita, painéis, cabeçalhos, destaque, texto, área de desenho, divisórias, campos) e guardá-las neste computador.
- **Passos de teste (TESTAR.md):** 0.376 «Os temas à vista»; 0.374 «Ferramentas de arquitetura do addon; os temas do estudo»

### Visualizar ▸ Rato

#### Botão do meio orbita (como no SketchUp)

- **O que faz:** O botão do meio do rato orbita; com Shift, desloca — como no SketchUp.

#### Botão do meio desloca (como no Revit)

- **O que faz:** O botão do meio do rato desloca; com Shift, orbita — como no Revit.

---

## 13. Gerenciar

Tipos, materiais, pavimentos, fases, componentes e grupos.

**Para testar este separador** (projeto novo, Ctrl+N):

1. **Novo pavimento**; PgUp e PgDn mudam o pavimento ativo (veja-o na planta, F4).
2. Desenhe paredes no pavimento 0, escolha-as e **Repetir nos pavimentos…**: aparecem nos de cima.
3. **Tipos… (criar e editar)**: duplique a «Parede alvenaria 20 cm», mude a espessura do bloco e **Aplicar**; desenhe uma parede com o tipo novo.
4. **Materiais…** e **Padrões…**: mude a cor e a trama de um material e veja-o nas paredes.
5. **Localização do terreno…**: escreva a latitude e a longitude da obra.

### Gerenciar ▸ Tipos e materiais

#### Tipos… (criar e editar)

- **O que faz:** Tipos (criar e editar)

- **Materiais…** — o mesmo de Modelagem ▸ Criar.

#### Padrões…

- **O que faz:** Padrões de preenchimento: criar, duplicar e mudar as tramas dos cortes e das superfícies
- **Passos de teste (TESTAR.md):** 0.332 «Alinhar os padrões numa face»; 0.318 «Padrões do projeto, tramas por categoria e a biblioteca de materiais»

#### Tipos para desenhar

- **Escolhas:** Parede · Laje · Cobertura · Pilar · Viga · Sapata · Tubo · Conduta · Tubo VD · Porta · Janela

### Gerenciar ▸ Projeto

- **Localização do terreno…** — o mesmo de Terreno ▸ Localização.

#### Fase da seleção

- **Escolhas:** Existente · Novo (a construir) · A demolir · Temporário · (sem fase)

### Gerenciar ▸ Pavimentos

- **Novo pavimento** — o mesmo de Arquitetura ▸ Referência.

#### Pavimento acima  ·  tecla PgUp

- **O que faz:** Passa para o pavimento de cima: as ferramentas desenham nele e a planta (F4) mostra-o. PgDn desce.
- **Passos de teste (TESTAR.md):** 0.325 «Pequenos defeitos»

#### Pavimento abaixo  ·  tecla PgDn

- **O que faz:** Passa para o pavimento de baixo: as ferramentas desenham nele e a planta (F4) mostra-o. PgUp sobe.

#### No 3D, ver só o pavimento ativo

- **O que faz:** No 3D (e nos cortes e alçados), mostra só o pavimento ativo — o que está a negrito na lista — e esconde os outros: para trabalhar num andar sem os de cima à frente. A planta mostra sempre só o seu pavimento.

#### Repetir nos pavimentos…

- **O que faz:** Copia o que está escolhido para outros pavimentos, no mesmo sítio.
- **Passos de teste (TESTAR.md):** 0.222 «A 2.ª ordem»

#### Pavimentos iguais (piso tipo)…

- **O que faz:** Pisos tipo: o pavimento ativo fica igual aos que escolher — o que se desenha, muda ou apaga num passa a todos. Outra vez: deixam de ser iguais.
- **Passos de teste (TESTAR.md):** 0.231 «As armaduras nos pisos tipo»

### Gerenciar ▸ Componentes

- **Criar componente…** — o mesmo de Modelagem ▸ Criar.

- **Importar modelo 3D…** — o mesmo de Inserir ▸ Importar.

#### Editar componente

- **O que faz:** Abre a cópia escolhida de um componente para a mudar de forma; ao fechar, a forma nova passa a todas as cópias.

#### Fechar componente

- **O que faz:** Termina a edição do componente: a forma nova passa a todas as suas cópias.

- **Trazer componentes de outro projeto…** — o mesmo de Inserir ▸ Importar.

### Gerenciar ▸ Grupos

- **Criar grupo…** — o mesmo de Modelagem ▸ Criar.

#### Desagrupar

- **O que faz:** Desfaz o grupo escolhido: os elementos ficam soltos, onde estão.

### Gerenciar ▸ Assistente IA

#### Ligação à IA

- **O que faz:** Deixa um assistente de IA (Claude…) trabalhar neste modelo através do MCP do ArqSynth (python -m arqbim.mcp): só neste computador, com uma chave feita ao acaso. Cada mudança da IA desfaz-se com Ctrl+Z.
- **Passos de teste (TESTAR.md):** 0.274 «Os dados IFC pelo MCP»; 0.270 «Ligar um assistente de IA com um clique»; 0.269 «Ligação da IA à janela aberta»

#### Ligar um assistente de IA…

- **O que faz:** Põe o MCP do ArqSynth no Claude Desktop com um clique, ou dá a linha para o Claude Code e a configuração para outros programas.
- **Passos de teste (TESTAR.md):** 0.270 «Ligar um assistente de IA com um clique»

---

## 14. Modificar | Paredes

Os modificadores das paredes selecionadas. Aparece quando se selecionam paredes e sai quando a seleção se esvazia (Esc).

**Para testar este separador** (projeto novo, Ctrl+N):

1. Escolha uma ou mais paredes: o separador verde **Modificar | Paredes** aparece sozinho.
2. **Virar a parede**, **Ligar o topo (laje / cobertura)** com uma laje por cima, **Desligar o topo**.
3. **Juntar paredes** (duas em linha), **Ligar as pontas** e **Ortogonalizar**.
4. **Editar perfil**: arraste o contorno da parede no seu alçado; **Repor perfil** volta.

### Modificar | Paredes ▸ Modificar parede

#### Virar a parede

- **O que faz:** O interior e o exterior das paredes selecionadas trocam: as camadas passam para o outro lado (o isolamento de fora vem para dentro). A parede, as ligações, as portas e as janelas ficam onde estão
- **Passos de teste (TESTAR.md):** 0.299 «Virar a parede e ligar as pontas»

#### Editar perfil

- **O que faz:** Desenhar o alçado da parede: empena, topo em degraus, recortes, arcos e curvas (também com duplo clique na parede)
- **Passos de teste (TESTAR.md):** 0.298 «A fita por disciplinas e o separador «Modificar | Paredes»»

#### Repor perfil

- **O que faz:** As paredes selecionadas voltam a ser retângulos no alçado, com a altura mais alta do perfil (e deixam de seguir uma cobertura)
- **Passos de teste (TESTAR.md):** 0.298 «A fita por disciplinas e o separador «Modificar | Paredes»»

#### Ligar o topo (laje / cobertura)

- **O que faz:** As paredes e pilares selecionados sobem (ou descem) até à face de baixo da laje ou cobertura selecionada com eles, e acompanham-na quando ela muda
- **Passos de teste (TESTAR.md):** 0.251 «A cobertura com um perfil desenhado»; 0.247 «Duas águas sobre uma casa em L»; 0.180 «Abóbada e borboleta»

#### Desligar o topo

- **O que faz:** As paredes e pilares selecionados deixam de seguir a laje ou a cobertura por cima: ficam com a altura que têm
- **Passos de teste (TESTAR.md):** 0.298 «A fita por disciplinas e o separador «Modificar | Paredes»»

#### Ligar a base

- **O que faz:** As paredes e pilares selecionados descem (ou sobem) até à face de cima da laje ou sapata selecionada com eles (Shift + clique), e acompanham-na; o topo fica onde está
- **Passos de teste (TESTAR.md):** 0.302 «Ligar e desligar a base»

#### Desligar a base

- **O que faz:** As paredes e pilares selecionados deixam de acompanhar a laje ou sapata por baixo
- **Passos de teste (TESTAR.md):** 0.302 «Ligar e desligar a base»

### Modificar | Paredes ▸ Cotas temporárias

#### Eixo a eixo

- **O que faz:** As cotas da parede escolhida até às paredes à volta medem de eixo a eixo
- **Passos de teste (TESTAR.md):** 0.361 «A cota temporária: a relação com as outras paredes»

#### Face a face

- **O que faz:** As cotas da parede escolhida até às paredes à volta medem de face a face (os vãos livres)
- **Passos de teste (TESTAR.md):** 0.361 «A cota temporária: a relação com as outras paredes»

### Modificar | Paredes ▸ Geometria

- **Junções de paredes** — o mesmo de Modelagem ▸ Geometria.

#### Juntar paredes

- **O que faz:** As duas paredes selecionadas, em linha e de ponta a ponta, ficam uma só (com as portas e janelas das duas)
- **Passos de teste (TESTAR.md):** 0.322 «Os comandos pedem o que lhes falta»

#### Ligar as pontas

- **O que faz:** As pontas soltas das paredes selecionadas voltam a ligar-se à parede que tocam (em canto ou em T), como ao desenhá-las: passam a acompanhá-la
- **Passos de teste (TESTAR.md):** 0.299 «Virar a parede e ligar as pontas»

#### Soltar ligações

- **O que faz:** As paredes selecionadas ficam onde estão, mas deixam de acompanhar as paredes onde ligam
- **Passos de teste (TESTAR.md):** 0.299 «Virar a parede e ligar as pontas»

#### Ortogonalizar

- **O que faz:** As paredes selecionadas quase a direito (até 5°) ficam exatamente no eixo vermelho ou verde; as ligadas acompanham
- **Passos de teste (TESTAR.md):** 0.407 «Ortogonalizar: a porta e a janela endireitam-se com a parede»

- **Unir geometria** — o mesmo de Modelagem ▸ Geometria.

- **Desunir geometria** — o mesmo de Modelagem ▸ Geometria.

### Modificar | Paredes ▸ Dividir e aparar

- **Dividir parede** — o mesmo de Modelagem ▸ Modificar.

- **Dividir com folga** — o mesmo de Modelagem ▸ Modificar.

- **Aparar / estender ao canto** — o mesmo de Modelagem ▸ Modificar.

- **Aparar / estender a um limite** — o mesmo de Modelagem ▸ Modificar.

### Modificar | Paredes ▸ Vãos e acabamentos

- **Porta** — o mesmo de Arquitetura ▸ Construir.

- **Janela** — o mesmo de Arquitetura ▸ Construir.

- **Abertura na parede** — o mesmo de Arquitetura ▸ Aberturas.

- **Revestimento de parede** — o mesmo de Arquitetura ▸ Acabamentos.

- **Rodapé / sanca na parede** — o mesmo de Arquitetura ▸ Acabamentos.

- **Ranhura** — o mesmo de Arquitetura ▸ Acabamentos.

### Modificar | Paredes ▸ Modificar

- **Mover** — o mesmo de Modelagem ▸ Modificar.

- **Copiar** — o mesmo de Modelagem ▸ Modificar.

- **Rodar** — o mesmo de Modelagem ▸ Modificar.

- **Espelhar** — o mesmo de Modelagem ▸ Modificar.

- **Alinhar** — o mesmo de Modelagem ▸ Modificar.

- **Offset** — o mesmo de Modelagem ▸ Modificar.

- **Matriz** — o mesmo de Modelagem ▸ Modificar.

- **Escala** — o mesmo de Modelagem ▸ Modificar.

- **Apagar** — o mesmo de Modelagem ▸ Modificar.

- **Cotar paredes (cadeias e totais)** — o mesmo de Anotar ▸ Cotas.

---

*244 comandos descritos, gerados do ArqSynth BIM 0.482.0.*
