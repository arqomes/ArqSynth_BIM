# Changelog

## 0.530.0 — 2026-11-10

**Cursor das ferramentas maior.**

- A cruz e o ícone da ferramenta ao lado ficam uma vez e meia maiores (traço um pouco mais grosso); o centro da cruz
  continua a ser o ponto exato do clique.

## 0.529.0 — 2026-11-10

**O cursor em cruz volta a apontar onde se clica.**

- A cruz das ferramentas (0.526) era desenhada ao dobro do tamanho no ecrã do programa, e o clique caía 10 px acima e
  à esquerda do centro da cruz: as pegas pequenas (contorno do piso, perfil da parede) não se apanhavam. Agora o centro
  da cruz é exatamente o ponto do clique.

## 0.528.0 — 2026-11-10

**Pontas da parede como no Revit: bolinha para esticar, Ctrl para o «+».**

- Uma parede selecionada sozinha mostra uma **bolinha** em cada ponta: arrastada, a parede **estica ou encurta pelo
  seu próprio eixo** (uma parede inclinada continua na mesma direção), com a cota do comprimento ao vivo.
- Com **Ctrl** carregado, as bolinhas passam a **«+»**: um clique continua a desenhar paredes a partir dessa ponta.

## 0.527.0 — 2026-11-10

**Mudar elementos de piso; trama nas categorias do Navegador; aba ativa destacada.**

- **Mudar de piso sem apagar:** um elemento (parede, laje, pilar, mobiliário…) passa para outro piso pelas
  **Propriedades ▸ Identificação ▸ Pavimento** (como o «Nível» do Revit) ou pelo botão direito no Navegador ▸ **Mudar
  para o piso ▸**. Sobe ou desce pela diferença de cotas entre os pisos; as portas e janelas vão com a parede; as
  paredes ligadas acompanham; um só Ctrl+Z. Os bloqueados ficam de fora.
- No **Navegador**, cada categoria (Paredes, Lajes, Janelas…) tem uma **trama** fina de fundo, para se destacar dos
  seus elementos.
- A **aba ativa no rodapé do Navegador** (Tudo, Vistas, Biblioteca, Projeto, Folhas) fica destacada como a da fita:
  a negrito, com o fundo do painel e a linha da cor de destaque.
- **Expandir tudo / Recolher tudo** no Navegador: dois botões ao lado da pesquisa e no fim do menu do botão direito.

## 0.526.0 — 2026-11-10

**Cursor por ferramenta, dicas do rodapé por cima e janelas ao centro.**

- O **cursor muda com a ferramenta**: seta para Selecionar, mão para a Mão (deslocar), e nas ferramentas de desenho e
  edição uma mira fina (o centro é o ponto exato do clique) com o ícone da ferramenta ao lado — como no SketchUp.
- No **rodapé**, a descrição de cada botão (navegação, pavimento, escala…) aparece **por cima** do botão, e já não por
  baixo, onde ficava escondida.
- As **janelas flutuantes** (diálogos e painéis soltos) abrem **ao centro** da janela do programa e sempre dentro do
  ecrã; se as mudar de sítio à mão, ficam onde as pôs.

## 0.525.0 — 2026-11-10

**Atalhos de ocultar e isolar, como no Blender.**

- **Shift+H** isola o que está selecionado (na vista ou no Navegador); **Alt+H** revela tudo; **Ctrl+H** oculta a
  seleção (fecha o olho no Navegador, gravado no IFC). O H sozinho continua a ser a Mão.
- O menu do botão direito do Navegador mostra os atalhos ao lado de «Isolar na vista» e «Revelar tudo».

## 0.524.0 — 2026-11-10

**O Navegador do Projeto com controlos como o Outliner do Blender.**

- Em cada elemento, categoria (ex.: «Paredes», «Malhas eletrossoldadas»), piso e edifício: **seta / cadeado**
  (selecionável ou bloqueado), **olho** (mostrar / ocultar), **câmara** (renderizar ou não), **impressora** (imprimir
  ou não), em traço fino, minimalistas. Ficam gravados no IFC (pset «ArqSynth_Controlo»).
- **Clicar e arrastar** pela coluna aplica o mesmo estado a todas as linhas por onde o rato passa — um só Ctrl+Z.
- **Shift** seleciona em série, **Ctrl** junta.
- **Botão direito**: Editar tipo…, Copiar, Duplicar, Replicar no piso ▸, Excluir, Isolar na vista, Revelar tudo,
  Ocultar/Revelar, Bloquear/Desbloquear, Renderizar ou não, Imprimir ou não.
- Bloqueado: não se escolhe na vista (logo não se move nem edita); Excluir e Duplicar recusam com aviso.
- «Não renderizar» sai do render (Mitsuba) e do estilo Realista; «não imprimir» sai das plantas, cortes e alçados das
  folhas, dos PDF e das vistas exportadas.

## 0.523.0 — 2026-11-10

**Passo 9: as malhas no mapa de armaduras.**

- A **Lista de armaduras** (e o seu Excel, e a memória de cálculo do betão) mostra, depois dos varões, as malhas
  eletrossoldadas: marca **M1, M2…** (uma por Ø e espaçamento), a laje, a face, o número de painéis de 6,00 m, a forma
  «Ø8//0,15» e o peso; o peso entra nos totais por diâmetro.
- As **Quantidades da estrutura** contam o aço das malhas na laje.

## 0.522.0 — 2026-11-10

**Estrutura metálica e pormenores, passo 9: malhas eletrossoldadas.**

- Comando novo **Malha eletrossoldada** (separador **Estrutura**, painel novo **Armadura**): põe nas lajes
  selecionadas uma malha genérica, pelo diâmetro dos fios (Ø5 a Ø12) e o espaçamento (0,10 a 0,30 m), na face
  inferior, na superior ou nas duas, com o recobrimento e a direção dos fios. As designações comerciais ficam por
  confirmar.
- Os fios são cortados pelo contorno da laje menos o recobrimento; a malha segue a laje quando esta muda.
- A janela mostra logo a verificação: recobrimento mínimo, espaçamento máximo (EC2 9.3.1.1), aço mínimo (EC2 9.2.1.1)
  e se as camadas cabem na espessura.
- No IFC: `IfcReinforcingMesh` (uma por face), com os diâmetros, as secções e os espaçamentos, os painéis de
  6,00 × 2,40 m (sobreposição 0,30 m) e o peso; agregada à laje.

## 0.521.0 — 2026-11-10

**Estrutura metálica, passo 8: a memória de cálculo.**

- Comando novo **Memória de cálculo (aço)…** (separador **Analisar**, painel **Documentos**; também no menu
  Estrutura): grava em **PDF** (ou HTML) a memória de cálculo da estrutura metálica, com o mesmo aspeto da do betão:
  1. o projeto (do carimbo); 2. as normas e os materiais (as classes de aço com fy e fu, os parafusos 8.8); 3. as
  ações (revestimento, sobrecarga ou neve da cobertura, vento com a sua pressão de pico, as combinações); 4. o modelo
  (peças, barras, ligações rígidas, nós, apoios); 5. a verificação de cada peça (NP EN 1993-1-1); 6. a de cada
  ligação (NP EN 1993-1-8); 7. a lista de material com o total; 8. os métodos, os limites e quem assina.
- Num projeto sem aço, o comando diz que não há estrutura metálica e não grava nada.

## 0.520.0 — 2026-11-10

**Estrutura metálica, passo 8: as ligações pela NP EN 1993-1-8.**

- Tabela nova **Estrutura metálica: ligações EC3** (painel Tabelas): cada ligação com os seus parafusos, a força de
  **corte** e de **tração** por parafuso, o uso das **soldaduras**, a **utilização** e a verificação que manda — OK ou
  Excede —, as mais carregadas primeiro, e as notas por baixo.
- As forças vêm do cálculo da 0.516–0.519 (com o vento), nas pontas das peças: o cutelo com o transverso da viga e o
  momento da excentricidade dos parafusos; o gousset com a tração do contraventamento; a orelha com a reação da madre
  na asna; a chapa de topo e o joelho aparafusado com o transverso em todos os parafusos e a tração do momento na
  fiada de fora; a chapa de base com o levantamento e os momentos do pé do pilar nos chumbadouros.
- Verificações: parafusos ao corte, esmagamento na peça mais fina (a alma de 2,5 mm de uma madre C manda nas
  orelhas), tração, corte com tração; soldaduras de ângulo pelo método simplificado (parafusos e chumbadouros classe
  8.8).
- Numa nave de 12 m com joelhos aparafusados: os joelhos a ~95 % (a fiada de fora à tração), os chumbadouros a ~70 %,
  as orelhas a ~33 %, os gousset a ~11 %.

## 0.519.0 — 2026-11-10

**Estrutura metálica, passo 8: a encurvadura lateral.**

- A **verificação EC3** passa a contar com a **encurvadura lateral** (bambeamento, NP EN 1993-1-1 6.3.2) das vigas,
  asnas e pilares em perfis I e U: o momento crítico Mcr pela fórmula clássica (C1 = 1, do lado da segurança), o
  comprimento entre os pontos onde outras peças os seguram (as madres nas asnas, os contraventamentos nos pilares) e
  as curvas dos perfis laminados. Entra sozinha («Encurvadura lateral (6.3.2)» na coluna da verificação que manda) e
  nas interações com a compressão.
- Por exemplo, uma HEB 200 com 6 m sem travamentos: Mcr ≈ 258 kN·m, χLT ≈ 0,80 — gasta 25 % mais do que pela flexão
  só; travada de 1,5 em 1,5 m, nada.
- A linha de Notas diz o que fica de fora: a das cantoneiras e dos enformados a frio.

## 0.518.0 — 2026-11-10

**Estrutura metálica, passo 8: o vento.**

- A **verificação EC3** (tabela e cores) passa a contar com o **vento** (NP EN 1991-1-4): a pressão de pico à altura
  da cumeeira, pela zona e pela rugosidade das **Ações e materiais** do projeto; em quatro direções; nas paredes
  (+0,8 a barlavento, −0,5 a sotavento) levado pelos pilares de cada parede, cada um com a sua largura de parede; na
  cobertura (sucção −0,6 / −0,5 / −0,7 conforme a água e a direção, com a pressão interior +0,2) levado pelas madres.
- Combinações da EN 1990 com o vento: a sobrecarga ou a neve a comandar com 0,9 do vento, o vento a comandar com o ψ0
  da outra, e o vento a levantar contra o peso só (1,0 G + 1,5 W); as flechas também com o vento.
- Numa nave de 12 m: os pilares de canto passam de 30 % a cerca de 50 % (o vento na empena dobra-os pelo eixo fraco) e
  os contraventamentos passam a trabalhar; as madres continuam comandadas pelo peso e pela sobrecarga.
- A linha de Notas diz a pressão do vento tomada; fica de fora o sismo.

## 0.517.0 — 2026-11-10

**Estrutura metálica, passo 8: a utilização do EC3 em cores no 3D.**

- No painel **Regras gráficas** (Colorir por), opção nova **Utilização EC3 (aço)**: cada peça de aço pintada pela
  parte da resistência que gasta — **verde** até 50 %, **amarelo** de 50 a 80 %, **laranja** de 80 a 100 %,
  **vermelho** acima de 100 % (excede) —, como nos resultados de um programa de cálculo; o resto do modelo a cinzento.
  A legenda diz quantas peças há em cada faixa e um clique numa linha escolhe-as.
- As cores voltam a ser calculadas sempre que se muda uma peça (uma peça muda os esforços de todas).

## 0.516.0 — 2026-11-09

**Estrutura metálica, passo 8 (primeira parte): a verificação pelo Eurocódigo 3.**

- Tabela nova **Estrutura metálica: verificação EC3** (painel Tabelas): cada peça de aço com os esforços de cálculo
  (N, com a compressão negativa; M; V), a **flecha** em relação a L/200, a **utilização** (quanto da resistência
  gasta) e a verificação que manda, **OK** ou **Excede** — as mais carregadas primeiro.
- Como se calcula (pré-dimensionamento, NP EN 1993-1-1): a estrutura metálica como um pórtico 3D — cada peça pela sua
  linha, cortada onde outra a encontra (madre na asna, contraventamento no pilar, viga na principal), com uma ligação
  rígida curta onde as linhas passam afastadas (a madre por cima da asna); os pés dos pilares encastrados; o peso
  próprio, o revestimento da cobertura (0,20 kN/m²) e a sobrecarga ou a neve da cobertura (as ações do projeto)
  levados pelas madres, cada uma com a faixa que lhe toca; 1,35 G + 1,5 Q; os contraventamentos em X só à tração.
  Em cada peça: a classe da secção, a resistência (axial, flexão nos dois eixos, transverso e a interação), a
  encurvadura por flexão (curvas a–d) e com flexão (Anexo B).
- Uma linha de **Notas** no fim diz o que fica de fora: o vento e o sismo, a encurvadura lateral (as madres e os
  contraventamentos tomados como travamento) e a EN 1993-1-3 dos enformados a frio.

## 0.515.0 — 2026-11-09

**Estrutura metálica, passo 6: o desenho de conjuntos com as soldaduras.**

- Vista nova **Conjuntos de aço (fabrico)** no navegador do projeto: cada **conjunto** uma vez — a peça com as chapas
  soldadas a ela (o pilar com a chapa de base, os gousset e a chapa do joelho; a asna com as orelhas e as chapas de
  topo…), os conjuntos iguais contados juntos —, desenhado de lado como no desenho de peças, com as chapas no sítio.
- Cada soldadura com o **símbolo ISO 2553** do cordão de ângulo: a seta até à chapa, a linha de referência, o
  triângulo (dos dois lados, quando a chapa é soldada dos dois lados — cutelo, gousset, orelha), a garganta «a6»
  antes dele e o **círculo de «toda a volta»** quando a peça é soldada à chapa a toda a volta (chapa de base, chapa
  de topo). Os símbolos afastam-se uns dos outros para não se sobreporem.
- Por baixo de cada conjunto: «Conjunto P1 — 4 un. — HEB 200 + Ch1, Ch3, Ch4 — 410 kg cada» e o comprimento cotado.
- Botão direito ▸ **Pôr numa folha nova**: a 1:50.

## 0.514.0 — 2026-11-09

**Estrutura metálica, passo 10 (primeira parte): a montagem.**

- Tabela nova **Estrutura metálica: montagem** (painel Tabelas): uma linha por **conjunto** — cada peça com as chapas
  soldadas a ela (um pilar com a chapa de base e os gousset, uma viga com as chapas de topo, uma asna com as orelhas
  das madres…) — pela **ordem de montagem**: primeiro os pilares, depois as vigas e asnas, os contraventamentos e as
  madres, e em cada fase a partir do primeiro canto. Para cada conjunto: a fase, a marca, o nome, as chapas soldadas,
  o **peso a içar** e o **centro de gravidade** (x; y; z) — o que a grua precisa de saber.
- Exporta-se em Excel/CSV como as outras tabelas; o total do peso é o da lista de material.

## 0.513.0 — 2026-11-09

**Estrutura metálica, passo 3: o joelho aparafusado.**

- Ligação nova **Joelho aparafusado** (na barra da seleção com duas peças de aço escolhidas, ao lado de
  Meia-esquadria; ou Estrutura ▸ Ligação ▸ seta de Chapa de topo): o joelho de um pórtico (pilar–asna) ou a
  cumeeira (asna–asna) em meia-esquadria com uma **chapa de topo em cada peça**, no plano da meia-esquadria, costas
  com costas, **aparafusadas** uma à outra (3 fiadas de 2 M20); cada peça recua a espessura da sua chapa; as chapas
  têm o tamanho exato do corte das duas secções (no joelho, a largura do HEB).
- O **Pórtico de nave** tem a opção **Joelhos: Soldados / Aparafusados** na barra de parâmetros: aparafusados, todos
  os joelhos e cumeeiras levam esta ligação.
- Nas Propriedades: espessura, fiadas, passo, distância entre parafusos, diâmetro, bordo e soldadura, com os avisos
  do EN 1993-1-8; apagar a ligação (ou Ctrl+Z) devolve a meia-esquadria soldada.

## 0.512.0 — 2026-11-09

**Estrutura metálica, passos 5 e 7: os furos nas próprias peças.**

- Os parafusos das ligações passam a **furar as peças** por onde passam, não só as chapas: a alma da viga no cutelo,
  a aba da cantoneira no gousset, a alma da madre na orelha, o banzo do pilar na chapa de topo. Cada furo com o
  diâmetro de furação (M16 → Ø18), a sua face (alma, banzo de cima ou de baixo) e a posição ao longo da peça.
- Os ficheiros **NC1** dos perfis levam esses furos (bloco BO), para a máquina furar.
- As **marcas** contam com os furos (como no DetailCraft): duas peças só têm a mesma marca se tiverem os mesmos
  furos (também viradas de ponta a ponta).
- O desenho **Peças de aço (fabrico)** mostra os furos da alma em cada perfil e diz «— 4 furos Ø18» na linha da
  marca.

## 0.511.0 — 2026-11-09

**Estrutura metálica, passo 7: a marcação e o DXF das chapas.**

- **Exportar para fabrico** (separador **Estrutura**, painel **Ligação**) grava agora também:
  - em cada ficheiro **NC1** o bloco **SI** — a **marca** que a máquina grava na peça (P1, V1…): nos perfis na alma,
    a 10 cm do início; nas chapas num ponto livre, longe dos furos;
  - o ficheiro **chapas.dxf** para o corte a laser ou plasma: cada marca de chapa uma vez, lado a lado, em
    milímetros — o contorno (o do gousset recortado, quando o tem), os furos e, por baixo, a marca, quantas e a
    espessura e o aço (por exemplo «4 x PL20 S275»), em camadas próprias (CONTORNO, FUROS, TEXTOS).

## 0.510.0 — 2026-11-09

**Estrutura metálica, passo 6: a planta de montagem.**

- Vista nova **Planta de montagem (aço)** no navegador do projeto (secção Vistas, só quando o modelo tem aço): toda a
  estrutura metálica vista de cima — pilares, asnas, vigas, contraventamentos, madres, treliças, vigas de escada —, os
  eixos (quando os há), o norte e a **marca** de cada peça ao lado dela (P1, V1, CV1, M1…, as mesmas da lista de
  material e do desenho de fabrico): o que a equipa de montagem põe em cada sítio.
- As marcas procuram sozinhas um lugar livre: fora das outras marcas e das linhas das outras peças (ao meio da peça,
  ou um pouco para um lado, ou do outro lado).
- Botão direito ▸ **Pôr numa folha nova**: a folha sai a **1:100**.

## 0.509.0 — 2026-11-09

**Estrutura metálica, passo 4: a escada metálica.**

- Ferramenta nova **Escada metálica** (separador **Estrutura**, na lista da seta ao lado do **Pórtico de nave**): como
  a Escada, um clique no pé (o meio do primeiro degrau, no chão) e outro para onde sobe — uma escada reta de
  **degraus abertos** entre duas **vigas de escada em UPN**:
  - os degraus em **grelha** (30 mm) ou em **chapa xadrez dobrada** (6 mm, com uma aba de 4 cm no focinho), cada um
    3 cm por cima do de baixo; espelhos de 18 cm no máximo, como na Escada;
  - as vigas de escada com a **alma virada para os degraus** e os banzos para fora, o topo 3 cm acima dos focinhos,
    **cortadas** rente ao chão no pé e a prumo e rente ao piso de cima no topo;
  - na barra: o desnível (até ao piso de cima, se não se escrever outro), a largura, o cobertor, os degraus e as
    vigas (UPN 160 a 240).
- As vigas de escada são peças metálicas (marcas — uma para a da esquerda, outra para a da direita —, lista de
  material, NC1, corte das barras); apagar a escada leva as vigas; um só Ctrl+Z desfaz tudo.

## 0.508.0 — 2026-11-09

**Estrutura metálica, passo 4: o piso metálico.**

- O **Sistema de vigas** (separador **Estrutura**, painel **Estrutura**) com um tipo de viga de aço faz agora um
  **piso metálico**: as vigas secundárias param a 1 cm da **alma** das vigas principais (não nas pontas dos banzos),
  ficam com os banzos **recortados** e levam um **cutelo** em cada ponta, soldado à alma da principal, com as fiadas
  de parafusos que cabem na viga (2 numa IPE 200, 3 numa IPE 300).
- Quando o vão muda (um eixo ou um pilar movido), o sistema volta a assentar como antes e as secundárias e os cutelos
  vão atrás; quando se volta a pôr o sistema, os cutelos das vigas antigas saem com elas.
- O **Cutelo** posto à mão também escolhe sozinho as fiadas que cabem na viga.

## 0.507.0 — 2026-11-09

**Estrutura metálica, passo 4: a treliça.**

- Ferramenta nova **Treliça** (separador **Estrutura**, na lista da seta ao lado do **Pórtico de nave**): com dois
  cliques — os dois apoios — faz uma treliça de banzos paralelos: o **banzo inferior** (por omissão a 3 m do nível),
  o **banzo superior** (1,2 m acima), os **montantes** e as **diagonais**, em painéis de cerca de 1,5 m (sempre um
  número par, para ficar igual dos dois lados do meio).
- Três tipos na barra de parâmetros: **Pratt** (as diagonais descem para o meio — à tração), **Howe** (sobem para o
  meio) e **Warren** (em ziguezague, só com os montantes das pontas).
- Também na barra: a altura, o comprimento dos painéis, a altura do banzo inferior e os perfis — **Banzos** (por
  omissão SHS 150×150×8) e **Montantes e diagonais** (CHS Ø76,1×4).
- Cada barra é uma peça metálica (IfcMember) com o seu nome (Banzo, Montante, Diagonal) e marca; um só Ctrl+Z desfaz
  a treliça toda.

## 0.506.0 — 2026-11-09

**Estrutura metálica, passo 3: viga apoiada noutra viga.**

- O **Cutelo** (separador **Estrutura**, painel **Ligação**, na lista da seta de **Chapa de topo**; ou na barra da
  seleção com uma viga de aço escolhida) já liga também uma viga à **alma de outra viga** (a principal): onde a viga
  secundária pára junto à alma da principal (como a ferramenta Viga já a faz parar, a 10 mm, e recorta os banzos —
  0.496), o cutelo fica soldado à face da alma da principal e a alma da secundária aparafusada a ele.
- Aviso novo: o cutelo não cabe entre os banzos da viga principal.
- O **Aplicar aos nós iguais** também serve aqui: põe o mesmo cutelo nas outras vigas iguais apoiadas em vigas iguais.

## 0.505.0 — 2026-11-09

**Estrutura metálica, passo 3: aplicar aos nós iguais.**

- Nas Propriedades de qualquer ligação de aço (chapa de base, chapa de topo, cutelo, gousset, apoio de madre), botão
  **Aplicar aos nós iguais**: as medidas desta ligação passam para todas as ligações do mesmo tipo nos **nós iguais**
  (os mesmos perfis e, numa ponta de viga, a mesma face do pilar — banzo ou alma), e a ligação é **posta** nos nós
  iguais que ainda não a têm (por exemplo: uma chapa de base com 25 mm debaixo de um pilar HEB 200, aplicada, põe a
  mesma debaixo de todos os HEB 200 sem chapa). Um só Ctrl+Z desfaz tudo.

## 0.504.0 — 2026-11-09

**Estrutura metálica, passo 3: o apoio das madres.**

- Ligação nova **Apoio de madre** (separador **Estrutura**, painel **Ligação**, na lista da seta ao lado de **Chapa de
  topo**; também na barra da seleção quando se escolhe uma madre): onde cada madre assenta numa viga ou asna de aço,
  uma **orelha** (chapa de 100 × 110 × 8 mm para uma madre C 160) de pé sobre o banzo da asna, **soldada** a ele dos
  dois lados, encostada à alma da madre (às costas, numa C ou num U; do lado livre, numa Z), e **dois parafusos M12**
  um sobre o outro pela orelha e pela alma. Sem nada escolhido, põe-se em todas as madres.
- Nas Propriedades: espessura, largura ao longo da madre, **altura** (0: 0,7 da altura da madre), parafusos, passo,
  diâmetro e soldadura; avisos do EN 1993-1-8 e do parafuso de cima contra o banzo da madre; aviso quando a madre já
  não assenta na viga.
- O **Pórtico de nave** já põe os apoios em todas as madres, e as madres passam **15 cm** além dos pórticos das
  pontas (a orelha das empenas fica toda debaixo da madre, e o remate da empena tem onde apoiar).
- O desenho **Peças de aço (fabrico)** passa a ter as chapas numa segunda coluna, à direita dos perfis (cabe a 1:50
  numa folha mesmo com muitas marcas), e as cotas em **milímetros**, como se usam na serralharia.
- Na fita, a Chapa de topo, o Cutelo, o Gousset e o Apoio de madre ficam num botão com seta (lista), como no Revit.

## 0.503.0 — 2026-11-09

**Estrutura metálica, passo 3: o gousset dos contraventamentos.**

- Ligação nova **Gousset** (separador **Estrutura**, painel **Ligação**, na lista da Chapa de topo e do Cutelo; também
  na barra da seleção quando se escolhe um contraventamento em cantoneira): em cada ponta do contraventamento que chega
  a um pilar de aço,
  - uma **chapa recortada** (o gousset) no plano do contraventamento, encostada às costas da aba da cantoneira,
    **soldada à alma do pilar** entre os banzos (ou à face, quando não cabe);
  - o contraventamento **recuado** para ficar a 20 mm dos banzos do pilar (a folga muda-se nas Propriedades);
  - **dois parafusos M16** ao longo do contraventamento, pela chapa e pela aba.
  Sem nada escolhido, põe-se em todos os contraventamentos em cantoneira. Os tubos não levam gousset (precisam de
  outra ligação — vem depois).
- O **Pórtico de nave** já põe os gousset nos contraventamentos das paredes (os do telhado não chegam a pilares).
- Nas Propriedades de um gousset: espessura, parafusos ao longo, passo, distância ao bordo, diâmetro, **folga ao
  pilar**, parafusos ao canto da cantoneira, chapa para além da aba e a soldadura; avisos do EN 1993-1-8 e do furo na
  raiz da cantoneira.
- Os gousset entram nas listas (marca **Ch**, parafusos M16), no **NC1** com o seu contorno recortado e no desenho de
  fabrico **Peças de aço**, a 1:10, com o contorno e as cotas acumuladas dos furos a partir da borda.
- Corrigido: uma peça metálica com as duas pontas recuadas (chapa de topo ou gousset nas duas) recuava o dobro na
  segunda ponta.

## 0.502.0 — 2026-11-09

**Estrutura metálica, passo 6 (primeira parte): o desenho de fabrico das peças.**

- Vista nova **Peças de aço (fabrico)** no navegador do projeto (secção Vistas, só quando o modelo tem aço): cada marca
  desenhada uma vez, como a serralharia a corta —
  - os **perfis** de lado, com os ângulos das meias-esquadrias e os recortes como estão no modelo, o comprimento e a
    altura cotados e uma linha de texto: marca, perfil, aço, quantas, comprimento, peso
    (por exemplo «P1 — HEB 200 S275 — 4 peça(s) de 6,08 m — 1569 kg»);
  - as **chapas** vistas de frente e ampliadas (a 1:10), com os **furos** e as cotas em cadeia da borda aos furos,
    entre furos e o total, e a linha «Ch1 — chapa 400 × 400 × 20 mm, 4 furos Ø22 — 4 peça(s) — 99,5 kg (1:10)».
- Botão direito ▸ **Pôr numa folha nova**: a folha sai a **1:50** com o carimbo, pronta a imprimir ou a exportar em PDF.

## 0.501.0 — 2026-11-09

**Estrutura metálica, passo 7: fabrico — DSTV NC1 e o corte das barras.**

- Comando **Exportar para fabrico** (separador **Estrutura**, painel **Ligação**): escolhe-se uma pasta e grava-se:
  - um ficheiro **DSTV NC1** por marca (P1.nc1, V1.nc1, Ch1.nc1…), o formato que as máquinas de corte e furação das
    serralharias leem: a marca, o aço, quantas, o perfil e o seu código, o comprimento total, as medidas da secção, kg/m,
    a área de pintura por metro e os **ângulos dos cortes** de cada ponta (os das meias-esquadrias); as **chapas** com o
    contorno e os **furos**;
  - o **plano de corte das barras** (corte_de_barras.csv, abre no Excel): para cada perfil, quantas barras de 12 m
    comprar, os metros comprados e os das peças, o desperdício, e que peças saem de cada barra (o maior primeiro, 3 mm
    por corte).
- Tabela nova **Estrutura metálica: corte das barras** (painel Tabelas): o mesmo plano, por perfil.
- As chapas das ligações guardam as suas medidas e furos (para o NC1).

## 0.500.0 — 2026-11-09

**Estrutura metálica, passo 5: marcas e listas.**

- Cada peça de aço tem uma **marca**, como nos desenhos de estrutura metálica: **P** pilar, **V** viga, **CV**
  contraventamento, **M** madre, **E** elemento, **Ch** chapa — a mesma para as peças iguais (perfil, aço, comprimento ao
  milímetro, os cortes e recortes das pontas; uma peça igual a outra rodada ou virada de ponta para ponta conta como
  igual, como no DetailCraft: o pilar da esquerda e o da direita de um pórtico têm a mesma marca).
- As marcas **guardam-se**: uma peça que não mudou guarda a sua; uma nova, ou que mudou, recebe o primeiro número livre.
  O comando **Numerar peças** (separador **Estrutura**, painel **Ligação**) escreve-as nas peças (no IFC, a `Tag` de cada
  peça, que o Tekla e o Revit leem como a marca).
- Tabelas novas (painel **Tabelas**):
  - **Estrutura metálica: lista de material** — uma linha por marca: a peça, o perfil, o aço, quantas, o comprimento
    (o real, já sem o que as meias-esquadrias e os recortes tiram), os metros, kg/m, o **peso** e a **área de pintura**,
    com os totais; exporta-se para Excel como as outras;
  - **Estrutura metálica: parafusos** — os parafusos e chumbadouros por diâmetro e comprimento (M20 × 530…), quantos.

## 0.499.0 — 2026-11-09

**Estrutura metálica, passo 4: estruturas prontas — o pórtico de nave.**

- Ferramenta nova **Pórtico de nave** (separador **Estrutura**, a seguir à Peça metálica): dois cliques marcam a primeira
  fila de pilares (o comprimento da nave; o vão fica para a esquerda dela) e a nave faz-se inteira, num só passo de
  Ctrl+Z:
  - **pórticos** igualmente afastados (cerca de 6 m), cada um com dois **pilares** — a alma no plano do pórtico — e
    duas **asnas** até à cumeeira, com os **joelhos e a cumeeira em meia-esquadria**;
  - **madres** em todo o comprimento, assentes no topo das asnas e inclinadas com o telhado, a cerca de 1,5 m;
  - **contraventamentos em X** nos vãos das pontas, nas duas paredes e nas duas águas do telhado;
  - **chapas de base** com chumbadouros debaixo de todos os pilares.
- Na barra: os perfis dos pilares, das asnas, das madres e dos contraventamentos (qualquer tipo de aço); o vão (12 m),
  a altura do beirado (6 m), a inclinação (3° a 30°; 10°), o afastamento dos pórticos e das madres, e se leva
  contraventamentos e chapas de base. O comprimento pode escrever-se depois do primeiro clique.
- Cada peça fica uma peça metálica normal: muda-se de perfil, move-se, apaga-se, e as ligações seguem-na.

## 0.498.0 — 2026-11-09

**Estrutura metálica, passo 3b: ligações viga–pilar — chapa de topo e cutelo.**

- Comandos **Chapa de topo** e **Cutelo** (separador **Estrutura**, painel **Ligação**; e na barra da seleção quando há
  vigas de aço escolhidas): em cada ponta das vigas de aço escolhidas que chega a um pilar de aço (e ainda sem
  ligação).
- **Chapa de topo** (ligação rígida): uma chapa soldada na ponta da viga, encostada à face do pilar (o banzo, ou a alma
  entre os banzos quando a chapa cabe; senão as pontas dos banzos), com fiadas de 2 parafusos através da chapa e do
  banzo (ou da alma), cabeça do lado da viga, anilha e porca do outro. A viga encurta o que for preciso para acabar na
  chapa. Por omissão: 20 mm, da largura da viga, rente, 4 fiadas M20 a 75 mm.
- **Cutelo** (ligação articulada): uma chapa de 10 mm soldada à face do pilar, ao lado da alma da viga, 115 mm ao longo
  dela, com parafusos através do cutelo e da alma da viga (3 fiadas M20 a 75 mm, a 65 mm da face).
- Nas **Propriedades** de qualquer peça da ligação: espessura, largura, quanto a chapa passa acima e abaixo da viga,
  fiadas, passo, distância entre parafusos, diâmetro, distâncias aos bordos, garganta da soldadura (e, no cutelo, a
  largura e a distância dos parafusos à face). **Avisos** pelo EN 1993-1-8: bordos (1,2·d0), passo (2,2·d0), distância
  entre parafusos (2,4·d0), parafusos a baterem na alma do pilar, chapa mais larga que o pilar, cutelo que não cabe
  entre os banzos da viga.
- Como a chapa de base: a ligação segue a viga e o pilar; apagar uma peça da ligação apaga-a inteira e a viga volta ao
  comprimento que tinha. No IFC: `IfcPlate` (ObjectType END_PLATE / FIN_PLATE), `IfcMechanicalFastener` BOLT com o
  `Pset_MechanicalFastenerBolt`, `IfcFastener` WELD.

## 0.497.0 — 2026-11-09

**Estrutura metálica, passo 3: ligações — a primeira, a chapa de base.**

- Comando **Chapa de base** (separador **Estrutura**, painel novo **Ligação**; e na barra da seleção quando há pilares
  de aço escolhidos): debaixo de cada pilar de aço escolhido — sem nenhum escolhido, de todos os que ainda não têm —
  uma chapa com os **chumbadouros** (varão, anilha e porca), e a **soldadura** do pilar à chapa à volta do perfil.
- Medidas automáticas: a chapa com 100 mm à volta do pilar (400 × 400 × 20 num HEB 200), 4 chumbadouros M20 a 50 mm dos
  bordos, 80 mm acima da chapa, 400 mm de amarração no betão, 30 mm de argamassa, soldadura a = 6 mm.
- Escolhida a chapa (ou um chumbadouro), as **Propriedades** mostram a ligação, e cada medida muda-se ali: largura e
  comprimento da chapa (0 = automáticos), espessura, número de chumbadouros (2, 4, 6, 8), diâmetro (M12 a M48),
  distância ao bordo, saliência, amarração, argamassa, garganta da soldadura. A ligação faz-se de novo a cada mudança.
- **Avisos** pelo EN 1993-1-8 (Quadro 3.3): distância ao bordo menor que 1,2·d0, chumbadouros mais perto do que
  2,2·d0; e se a chapa não é maior que o pilar ou um chumbadouro bate nele.
- A ligação **segue o pilar**: muda-se o perfil do pilar (ou move-se) e a chapa faz-se de novo à medida. Apagar uma peça
  da ligação apaga a ligação inteira; apagar o pilar apaga a sua ligação.
- No IFC, como o Tekla e o Revit as leem: um `IfcElementAssembly` «Ligação» com a `IfcPlate` (os furos no contorno),
  os `IfcMechanicalFastener` ANCHORBOLT (com o `Pset_MechanicalFastenerAnchorBolt`) e o `IfcFastener` WELD (com o
  `Pset_FastenerWeld`: garganta e comprimento), no aço do pilar. No Navegador: «Chapas», «Parafusos e chumbadouros».

## 0.496.0 — 2026-11-09

**Estrutura metálica, passo 2b: as pontas das peças cortadas.**

- **Meia-esquadria**: escolhidas duas peças metálicas cujas linhas se encontram (o pilar e a asna de um pórtico), a
  barra da seleção (e o separador **Estrutura**, por baixo do Sistema de vigas) oferece **Meia-esquadria**: as duas
  linhas acabam no ponto onde se encontram, cada peça prolonga-se para lá dele e é cortada pelo plano que divide o
  ângulo ao meio — o joelho fica fechado, sem buracos nem sobreposições. Um passo de Ctrl+Z. Se as linhas não se
  encontram (paralelas ou a mais de 50 cm), diz-o e não muda nada.
- **Recorte automático**: uma viga de aço desenhada com a ferramenta Viga até outra viga de aço (uma secundária numa
  principal) pára na alma da principal, a 10 mm, e o banzo de cima que bateria no banzo da principal é recortado (até
  por baixo do banzo e do raio de concordância, mais 5 mm); o de baixo também, quando for preciso.
- Os cortes e os recortes ficam guardados na peça, presos à ponta a que pertencem: mudar o perfil, o comprimento ou a
  altura da peça mantém-nos. No IFC, os cortes por planos são `IfcBooleanClippingResult` (corpo «Clipping») e os
  recortes `IfcBooleanResult` (corpo «CSG»), como o Revit e o Tekla os leem.

## 0.495.0 — 2026-11-09

**Estrutura metálica, passo 2: peças metálicas** (o PLANO, «Estrutura metálica e pormenores de fabrico»).

- Ferramenta nova **Peça metálica** (separador **Estrutura**, painel **Estrutura**, a seguir à Laje), como o «Beam» do Tekla: um perfil de
  aço entre dois pontos quaisquer — horizontal, inclinado ou de pé.
  - **Função**: Viga (`IfcBeam`), Pilar (`IfcColumn`), Contraventamento (`IfcMember` BRACE), Madre (`IfcMember`
    PURLIN) ou Elemento (`IfcMember`). Qualquer perfil serve para qualquer função: o tipo da função faz-se sozinho
    («Contraventamento L 80×8 — S275», «Madre C 160…»).
  - **Inserção**: um dos nove pontos da secção na linha desenhada (automática: o topo ao meio numa viga ou madre — o
    topo na cota, como a Viga —, o centro num contraventamento).
  - **Rotação** do perfil à volta da linha (0°, 90°, 180°, 270°).
  - **Alturas**: «pelas cotas» — a cota no início e a cota no fim (diferentes: uma asna inclinada) —, ou «pelos pontos
    (3D)» — onde os pontos se apanham no 3D (o topo de um pilar).
  - Ponto a ponto: cada peça começa onde a anterior acabou; Esc acaba. O comprimento pode escrever-se.
- **Contraventamento entre dois pilares**: no «Desenhar» da barra, «Contraventamento em X» (ou uma diagonal ╱ ou ╲) e
  um clique em cada pilar — as diagonais vão do pé de um ao topo do outro.
- As **vigas de aço** desenhadas com a ferramenta Viga **param na face dos pilares** onde chegam, a 10 mm: na alma de
  um pilar em I, entre os banzos, quando cabem; senão na face do banzo ou nas pontas dos banzos; num tubo, na sua face.
  As vigas de betão ficam como estavam.
- Tipos novos: Contraventamento L 80×8 e CHS Ø76,1×4, Madre C 160×60×20×2,5; no Editar tipo, a lista
  **Contraventamentos e madres**.
- Mudar o tipo de uma peça metálica (Propriedades ou Editar tipo) refaz a peça com o perfil novo, na mesma linha.

## 0.494.0 — 2026-11-09

**Estrutura metálica, passo 1: catálogo de perfis e classes de aço** (o dono: «faça plano para inserir a parte metálica e
detalhes estruturais… comece e não pare até eu mandar»; o plano está no PLANO, «Estrutura metálica e pormenores de
fabrico»).

- Catálogo de perfis europeus, com as medidas das normas: **IPE, HEA, HEB, HEM** (EN 10365), **UPN** (abas
  inclinadas a 8 %) e **UPE**, **cantoneiras** de abas iguais e desiguais (EN 10056-1), **tubos quadrados,
  retangulares e redondos** enformados a frio (EN 10219) e **madres C, Z e ómega** enformadas a frio — mais de 400
  perfis.
- Cada perfil desenhado como a norma o desenha (raios de concordância, a inclinação das abas da UPN, os cantos dos
  tubos) e com as suas propriedades: área, kg/m, inércias, módulos elástico e plástico, raios de giração, constantes
  de torção e de empenamento, área de pintura. Conferidas contra os catálogos (IPE 300, HEB 200, HEA 200, SHS, CHS,
  cantoneira, UPN).
- Classes de aço **S235, S275, S355 e S460**, com fy e fu pela espessura (EC3-1-1, Quadro 3.1); materiais novos
  «Aço estrutural S235 / S355 / S460».
- No **Editar tipo** de pilares e vigas, a forma **Perfil de aço**: escolhe-se a família, o perfil e a classe; mostra
  as medidas, o peso por metro e as propriedades; o nome segue a escolha («Viga IPE 300 — S275»). Os tipos novos:
  Pilar HEB 200, Pilar SHS 150×150×8, Viga IPE 200, IPE 300 e HEB 240.
- No IFC, a secção verdadeira (`IfcIShapeProfileDef`, `IfcUShapeProfileDef`, `IfcLShapeProfileDef`, os tubos,
  `IfcCShapeProfileDef`; Z e ómega pelo contorno) com o nome que o Revit e o Tekla usam («IPE300»); ao abrir um IFC de
  outro programa, os perfis de aço reconhecem-se pelo nome ou pelas medidas.
- Cada peça de aço com o **peso** (kg) e a área de pintura nas quantidades; nas plantas de estrutura a etiqueta diz o
  perfil («V1 HEA 200», «P1 HEB 200»). As miniaturas dos tipos desenham o perfil.

## 0.493.0 — 2026-11-09

**Combinar e recortar volumes de diagrama, nativo no BIM** (o dono: «ferramentas de adição, subtração, interseção
etc. nativo mesmo para este caso, quando exportamos para o ArqSynth, já vai pronto»).

- No separador **Diagramas** da interface do Presentation há uma secção nova, **COMBINAR E RECORTAR**, como a do
  Presentation: escolhe-se o **Volume A** e o **Volume B** (⇅ troca-os), a operação — **União**, **A − B**, **B − A**,
  **Interseção**, **Diferença** (as partes não comuns) — e carrega-se em **Aplicar à cena**.
- Aparece um volume novo, o **resultado** (chamado «União», «Subtração A − B»…), com a cor de A, já escolhido. As
  duas origens ficam guardadas e escondidas (desligue **Ocultar origens ao aplicar** para as deixar à vista; as
  bloqueadas ficam sempre à vista).
- O cálculo é feito no BIM com o **mesmo motor do Presentation** (manifold): o resultado vai para o Presentation **já
  pronto**, como o «volume resultante» de lá, com as origens.
- **Mais do que no Presentation:** quando uma origem muda (move-se, roda, muda de medidas), o resultado **volta a ser
  calculado sozinho**, mantendo o nome, a cor e o sítio para onde o tenha levado. Funciona em cadeia (um resultado
  pode ser origem de outro, até oito operações).
- Com um resultado escolhido, a secção mostra as suas origens e a operação; mudando-as, **Atualizar «…» com estes**
  recalcula-o no lugar.
- O resultado é um volume como os outros: arrasta-se, tem pegas, Mover, Rodar, Escala, Copiar, a cor e a opacidade.
- Apagar um resultado devolve as origens à vista. Uma origem de um resultado não se apaga (o aviso diz qual é o
  resultado). Tudo com Ctrl+Z.
- Recusas com as palavras do Presentation: um **plano** não tem espessura; uma interseção de volumes que não se tocam
  dá vazio; o mesmo volume duas vezes.
- Biblioteca nova no Python do programa: `manifold3d` 3.5.4 (licença Apache 2.0), com a autorização do dono.
- **No Presentation** (ramo `integracao-arqsynth-bim`): o importador calcula as chaves das origens como o editor de lá,
  para o resultado não aparecer como «desatualizado».

## 0.492.0 — 2026-11-09

**Volumes de diagrama editáveis com o rato e a Modelagem** (o dono: «elas podem ser editáveis usando as ferramentas
de Modelagem»).

Na interface do Presentation, os volumes dos diagramas (caixa, cilindro, esfera, cone, plano) deixam de se mexer só
pelos campos:

- **Clicar num volume** no 3D escolhe-o: abre-se o separador **Diagramas** com ele, e aparecem as **pegas** no meio das
  faces (seis; quatro num plano), como no Presentation. Clicar fora deixa de o escolher.
- **Arrastar o volume** move-o ao nível em que está, de 10 em 10 cm; com **Shift**, sem grelha.
- **Arrastar uma pega** muda só essa face — a oposta fica no sítio; a pega de cima e a de baixo mudam a altura.
- As ferramentas **Mover**, **Copiar**, **Rodar** e **Escala** do separador **Modelagem** da fita funcionam no volume
  escolhido, com os mesmos cliques e os valores escritos de sempre (Copiar faz um volume novo, «… cópia»).
- **Delete** apaga o volume escolhido; **Ctrl+Z** volta atrás em qualquer destas mudanças.
- O que se faz assim vai para o Presentation como antes: posição, rotação, escala e medidas do volume.

## 0.491.0 — 2026-11-09

**Corte preenchido** (o dono: «seria bom termos o preenchimento das paredes nos cortes aqui no BIM»).

- Nos cortes do 3D — os planos do separador **Cortes** da interface do Presentation e a **caixa de corte** da vista 3D
  — o que é cortado deixa de ser só escuro: cada parede, laje ou pilar aparece com a **trama dos seus materiais**
  (alvenaria, betão, isolamento, reboco…), como nas plantas e cortes do BIM.
- No separador **Cortes** há uma secção nova, **ASPETO DO CORTE**, como a «Superfície cortada» do Presentation:
  - **Material** — as tramas dos materiais (é o que vem por omissão);
  - **Poché** — tudo o que é cortado numa cor, tracejado;
  - **Sólido** — numa cor lisa;
  - **Aberto** — sem enchimento: vê-se o interior das peças.
  Em Poché e Sólido escolhe-se a **cor do corte**. Como os planos, o aspeto guarda-se na cena ao **Criar cena /
  Atualizar**.
- Enquanto se arrasta um plano, o preenchimento esconde-se e volta logo que o plano para (para o arrastar continuar
  fluido).
- Vai para o Presentation: Material como «Mat./cat.» — cada categoria (Paredes, Lajes…) com o material de que a maior
  parte das suas peças é feita: betão, bloco de cimento, bloco cerâmico, madeira, metal, pedra ou gravilha —; Poché,
  Sólido e Aberto como os do Presentation, com a cor.
- Os botões de escolha da coluna da direita (Material/Poché…, Piso/Parede…, Caixa/Cilindro…) mostram agora qual está
  escolhido.
- **No Presentation** (ramo `integracao-arqsynth-bim`): o importador lê o aspeto do corte; no «Atualizar», o que o BIM
  escolheu entra e o resto do aspeto afinado lá (a linha do corte, …) fica.

## 0.490.0 — 2026-11-09

**A mesma regra do «Atualizar» para as etiquetas dos ambientes e o Passeio Virtual** (o dono: «Sim, também»).

Ao exportar outra vez do BIM e escolher **Atualizar** no Presentation, **o que se prepara no BIM manda; o que só se faz
no Presentation fica** — agora também aqui:

- **Etiquetas dos ambientes**: o nome, a área e o número vêm do BIM. O aspeto escolhido no Presentation (forma, cores,
  tamanho, colocação) fica. O sítio também fica, enquanto estiver dentro do ambiente; se o ambiente mudou de sítio no
  BIM, a etiqueta vai com ele. A etiqueta de um ambiente apagado no BIM sai. As etiquetas feitas no Presentation ficam.
- **Passeio Virtual**:
  - vêm do BIM: os pisos, as zonas dos ambientes (contorno, nome, tipo, piso, se entram no passeio), os caminhos pelas
    portas e as ligações pelas escadas, o **início**, a **visita guiada** e o **tempo em cada ambiente**, e se o passeio
    está ligado;
  - ficam do Presentation: as zonas, caminhos e ligações desenhados lá, os apartamentos, quem vê cada zona, o movimento
    de câmara de cada caminho, a câmara de uma zona (enquanto o ambiente não mudar de sítio), o mini-mapa e as
    permissões;
  - um início ou uma visita guiada escolhidos no Presentation com zonas feitas lá ficam;
  - o que pertencia a um ambiente apagado no BIM sai, também os caminhos feitos lá que iam para ele.
- Com o passeio desligado no BIM, o Presentation desliga-o sem apagar o que lá se fez.
- A mudança é só no Presentation (o importador, ramo `integracao-arqsynth-bim`).

## 0.489.0 — 2026-11-09

**«Atualizar» no Presentation leva as mudanças do BIM às cenas que já lá estão** (o dono: «O "Atualizar" primeiro»).

Até aqui, ao exportar outra vez do BIM e escolher **Atualizar** no Presentation, só entravam as camadas e as cenas
novas; as cenas que já lá estavam ficavam como estavam, mesmo que tivessem mudado no BIM. Agora a regra é: **o que se
prepara no BIM manda; o que só se faz no Presentation fica.**

- **As cenas que vêm do BIM** recebem o que mudou lá: o nome, a câmara, o modo de visualização, o sol, a exposição e o
  céu, as camadas e as etiquetas escondidas, os cortes, a chegada, o efeito, a legenda e o tempo, o movimento de
  câmara, os volumes de diagrama feitos no BIM, se está dentro ou fora da apresentação e a miniatura nova.
- **O que só se faz no Presentation fica** nessas cenas: o áudio da narração, o aspeto do corte, os volumes e as
  etiquetas feitos lá, os comentários, as cotas, os materiais da cena.
- **As cenas criadas no Presentation** ficam exatamente como estão, no mesmo lugar.
- Uma cena **apagada no BIM** sai do Presentation; uma **nova** entra no fim. A **ordem** das cenas do BIM passa a ser a
  do BIM, nos lugares que elas ocupavam.
- A **cena de entrada** passa a ser a escolhida no BIM, a menos que no Presentation se tenha escolhido uma cena feita lá.
- O mesmo vale para o pacote ZIP (botão **ArqSynth BIM**) e para o GLB sozinho.
- Ficam como antes (o que se mudou no Presentation fica): as etiquetas dos ambientes e o Passeio Virtual de uma página
  que já existe; as fichas, as cores e a visibilidade das camadas; os ajustes de material da página.
- A mudança é só no Presentation (o importador, ramo `integracao-arqsynth-bim`); no BIM nada muda na exportação.

## 0.488.0 — 2026-11-09

**Passeio virtual na interface do Presentation** (o dono: «Sim, passeio»; passo 7, o último da lista do PLANO).

- O separador **Passeio** (o último ícone da direita) mostra agora o Passeio Virtual que vai para o Presentation:
  - continua a opção **Passeio Virtual pelos ambientes**;
  - quantos **ambientes**, **portas entre eles** e **escadas** o passeio tem;
  - o **Início**: o ambiente onde o passeio começa (por omissão, o da porta de entrada no piso mais baixo) ou outro à
    escolha;
  - o **Tempo em cada ambiente** da visita guiada (por omissão 3 s, como no Presentation);
  - a **Visita guiada**: os ambientes pela ordem em que se percorrem a partir do início, de porta em porta (e pelas
    escadas); os que não têm ligação aparecem marcados «sem ligação». Desmarcar um ambiente deixa-o fora do passeio.
- Com o separador aberto, veem-se no 3D as **zonas** dos ambientes (a verde o início, a cinzento as de fora) e os
  **caminhos** pelas portas e escadas.
- **Percorrer a visita guiada**: a câmara percorre o passeio à altura dos olhos (1,65 m), a 1,4 m/s, pelas portas e
  escadas, parando o tempo escolhido em cada ambiente — como o Presentation o faz. **Ir até ao escolhido** (ou duplo
  clique na lista) vai do início até esse ambiente. **Esc** ou **Parar** devolvem a câmara ao sítio.
- Vai para o Presentation: o início, os ambientes de fora (não navegáveis), a visita guiada pela ordem certa — só com
  os ambientes a que se chega, para o Presentation a aceitar — e o tempo em cada ambiente.
- **No Presentation** (ramo `integracao-arqsynth-bim`): o importador lê estas escolhas. Antes, a visita guiada levava
  todos os ambientes pela ordem do ficheiro e, se um não tivesse porta, o Presentation recusava a visita inteira.

## 0.487.0 — 2026-11-09

**Diagramas na interface do Presentation** (o dono: «Sim, diagramas»; passo 6 da lista do PLANO).

- Na barra de ícones da direita há um separador novo, **Diagramas** (o ícone com um triângulo, um quadrado e um
  círculo), entre Ambiente e Etiquetas, no mesmo sítio do Presentation. É o seu «Volumes para diagramas».
- **Criar volume**: **Caixa**, **Cilindro**, **Esfera**, **Cone** ou **Plano**. O volume aparece ao lado do modelo,
  com o nome «Caixa 1», «Cilindro 1»…, uma das cinco cores do Presentation e um pouco transparente.
- A **lista** dos volumes da cena, cada um com a sua cor, o **olho** (mostrar/ocultar) e o **cadeado** (bloquear).
- O volume escolhido, com o contorno destacado no 3D, edita-se por baixo:
  - o **nome**, o tipo e o volume em m³;
  - **Duplicar**, **Focar**, **Bloquear**, **Remover**;
  - **Mostrar volume nesta cena**;
  - **Medidas** (largura, altura, profundidade);
  - **Posição** do centro da base (X, Y e elevação);
  - **Rotação** e **Escala**, com **Repor rotação e escala**;
  - **Aparência**: as cinco cores do Presentation ou qualquer outra, a opacidade e «Mostrar estrutura de linhas»;
  - a **Descrição**.
  Um volume bloqueado não se muda até ser desbloqueado.
- **Enquadrar volumes** (canto de cima) põe à vista os volumes da cena.
- Os volumes são **de cada cena**, como no Presentation: ao escolher outra cena veem-se os dela.
  **Duplicar cena com estes volumes** faz uma cena nova com os mesmos. Cada mudança é um passo de desfazer.
- Vão para o Presentation como os volumes da cena, com todos os campos.
- **No Presentation** (ramo `integracao-arqsynth-bim`): o importador lê os volumes de cada cena e verifica-os como os
  do próprio editor.

## 0.486.0 — 2026-11-09

**Efeitos na interface do Presentation** (o dono: «Sim, efeitos»; passo 5 da lista do PLANO).

- O separador **Efeitos** da coluna da direita é agora o do Presentation, com os seus dois tipos no topo:
  **Modelo** e **Câmara** (o movimento de câmara que já havia passou para Câmara).
- Em **Modelo**, o **Efeito da cena**: **Nenhum**, **Estudo solar**, **Construção** ou **Explosão**, com a explicação
  de cada um; a **Duração** (2 a 60 s); **Reproduzir ao entrar na cena**; na Explosão a **Distância** (0,3 a 3,0 × o
  tamanho do modelo); no Estudo solar a dica do lugar e da data.
- **Pré-visualizar** toca o efeito no 3D do BIM **como o Presentation o toca**, com as mesmas contas:
  - **Construção**: as peças aparecem pela ordem de obra (terreno e fundações a subir do chão; estrutura, paredes,
    portas e janelas, escadas, cobertura, acabamentos e mobiliário a assentar vindos de cima), de baixo para cima;
  - **Explosão**: as peças começam afastadas do centro e montam-se numa ordem que parece ao acaso, mas é sempre a mesma;
  - **Estudo solar**: o sol ao longo do dia, com as sombras, no tempo da duração.
  O botão passa a **Parar**; Esc também para. O modelo não se refaz: no fim fica exatamente como estava.
- Na Construção, a **Sequência de construção** lista todas as peças pela ordem em que vão aparecer, com a fase de cada
  uma; desmarcar uma tira-a do efeito (fica parada e visível desde o início, como o terreno).
- O **▶** das cenas, por baixo do 3D, toca o efeito de cada cena ao chegar a ela (se «Reproduzir ao entrar na cena»
  estiver ligado) e espera que acabe antes de passar à seguinte.
- O efeito saiu da página **Cenas 3D** (no Presentation também só está em Efeitos).
- Tudo vai para o Presentation: o efeito, a duração, «reproduzir ao entrar», a distância e as peças tiradas do efeito.
- **No Presentation** (ramo `integracao-arqsynth-bim`): o importador lê estes campos; e a ordem de obra deixou de
  confundir o pavimento com a estrutura — as pastas do BIM são «Paredes · Piso 0» e a palavra «piso» fazia de cada
  parede, porta ou cobertura «Estrutura». Agora conta primeiro o nome e a categoria, e só depois o resto da pasta.

## 0.485.0 — 2026-11-09

**Etiquetas na interface do Presentation** (o dono: «Sim, etiquetas»; passo 4 da lista do PLANO).

- O separador **Etiquetas** da coluna da direita é agora o do Presentation:
  - **Adicionar etiqueta**: **Piso** (deitada no chão), **Parede** (colada à parede), **Em pé** (com poste) e
    **Chamada** (afastada da parede por uma linha). Escolhe-se uma e clica-se no modelo: enquanto se aponta, vê-se o
    contorno da etiqueta no sítio; o clique põe-na lá, com o nome «Ambiente 1», «Ambiente 2»… Fora do modelo vai para o
    chão. Esc cancela.
  - A **lista** das etiquetas, cada uma com a sua cor, onde está e o **olho** (oculta-a nesta cena).
  - A etiqueta escolhida edita-se por baixo: **Nome** e **Nota** (ex.: «24 m²»), cada um com o tamanho da letra;
    **Retângulo** ou **Círculo** (com o número); **Fundo** e **Texto** (cores); **Opacidade**; **Tamanho**; **Rotação**
    (oito botões de 45 em 45° e um deslizador que se prende a eles); o comprimento do **Poste** ou da **Chamada**;
    **Virar para a câmara** (as em pé); **Ocultar quando tapada**; **Apagar**.
  - Uma etiqueta nova herda o aspeto da escolhida (ou da última posta), como no Presentation.
  - Por baixo continua a opção dos ambientes como etiquetas.
- As etiquetas veem-se no 3D do BIM, desenhadas como no Presentation (caixa de cantos redondos com o nome em maiúsculas
  e a nota, ou círculo com o número); só dentro da interface do Presentation.
- As etiquetas são do modelo (gravam-se com o projeto); o **olho** de cada uma guarda-se na cena ao **Criar cena /
  Atualizar**, como as camadas e os cortes. Cada mudança é um passo de desfazer.
- Vão para o Presentation como etiquetas da página 3D, com todos os campos; cada cena leva as que esconde.
- **No Presentation** (o importador, ramo `integracao-arqsynth-bim`): lê as etiquetas do BIM e as escondidas de cada
  cena; ao **Atualizar** a página, as do BIM mudam no lugar, as apagadas no BIM saem e as feitas no Presentation ficam.

## 0.484.0 — 2026-11-09

**Cortes na interface do Presentation** (o dono: «é importante criar cortes…»; passo 3 da lista do PLANO).

- Na barra de ícones da direita da interface do Presentation há um separador novo, **Cortes** (o ícone do bloco
  cortado), logo a seguir a Cenas 3D, como no Presentation.
- **Planos de corte**: os botões **Horizontal**, **Vertical X** e **Vertical Z** acrescentam um plano:
  - o horizontal nasce à altura de uma planta (1,20 m acima do piso mais baixo);
  - os verticais nascem a meio do modelo.
  Cada plano tem um deslizador e a **posição exata em metros**, **Inverter lado** (fica a outra metade) e **Remover**.
  Até 6 planos.
- O corte vê-se logo no 3D, com o enchimento escuro onde corta paredes e lajes, como a caixa de corte. Não apaga nada.
- Como no Presentation, **os cortes guardam-se na cena ao Criar cena / Atualizar**. Ao escolher uma cena voltam os
  dela; fora da interface o 3D do BIM fica inteiro.
- Vão para o Presentation como planos de corte da cena (Horizontal, Vertical X, Vertical Z), junto com os que ela já
  levava (a caixa de corte de uma vista 3D, o corte de uma planta).

## 0.483.0 — 2026-11-09

**Uma camada por janela no Presentation e transições animadas entre as cenas** (o dono, depois de importar o pacote no
Presentation: «há 2 camadas de janela, um é window (vidro) e outro janela (estrutura) mas poderia ser apenas 1… o BIM
ainda não tem animação de transição entre as cenas como acontece no AP»).

- **Uma camada por janela.** O Presentation separava o vidro das janelas numa camada «WINDOW», à parte da camada da
  janela, porque classificava o vidro pelo material. Agora o vidro (e a água) de cada elemento vai para o Presentation
  com nome próprio («Janela 1 vidro») e dentro da camada da janela: no Presentation fica uma só camada por janela.
  Para corrigir um projeto já importado, exporte de novo e use «Importar / atualizar».
- **Transições animadas entre as cenas.** Na interface do Presentation, um clique num cartão de cena, ou as setas do
  leitor, levam a câmara até à cena **a voar**, no tempo da sua chegada (1,2 s, ou o da Transição), com a lente a
  mudar pelo caminho, como o «Voo suave» do Presentation. Uma cena com «Corte seco» chega de uma vez.
- No PLANO ficou a lista do que falta preparar no BIM: cortes, etiquetas, efeitos, diagramas e passeio virtual.

## 0.482.0 — 2026-11-09

**A fita organizada como a do Revit** (o dono: «gostaria que trabalhasse a organização das ferramentas como do revit…
começasse com modelagem, depois arquitetura, estrutura, e assim vai. organize também os ícones para serem como dos
revit nessa ordem»).

- **Os separadores, pela ordem do Revit**: a casa (o «Início»: projeto, exportar e ajuda — o «File» do Revit),
  **Modelagem**, **Arquitetura**, **Estrutura**, **Instalações**, **Inserir** (novo), **Anotar**, **Analisar** (novo),
  **Massa e Estudos**, **Terreno**, **Colaborar**, **Visualizar** e **Gerenciar**. O separador «Render» saiu: as suas
  ferramentas estão em **Visualizar ▸ Apresentação**, como no Revit.
- **Atalhos**: Ctrl+1 Modelagem, Ctrl+2 Arquitetura, Ctrl+3 Estrutura, Ctrl+4 Instalações, Ctrl+5 Inserir, Ctrl+6
  Anotar, Ctrl+7 Analisar, Ctrl+8 Massa e Estudos, Ctrl+9 Terreno.
- **Botões com seta ▾, como no Revit**: um clique no botão usa a ferramenta; a setinha em baixo à direita mostra as
  variantes — Janela ▾ (Caixilho Studio), Cobertura ▾ (perfil da cobertura, calha, ralo), Laje ▾ (piso, editar
  contorno), Parede cortina ▾ (painel de fachada), Guarda ▾ (tipos de guarda), Render realista ▾ (panorama 360°,
  Gaussian splat), Vista 3D ▾ (de cima, de frente, nova vista 3D).
- **Modelagem**, como o «Modificar» do Revit: Selecionar · Copiar e colar · Geometria (junções de paredes, unir e
  desunir) · Modificar (Mover, Copiar, Rodar, Espelhar; Alinhar, Offset, Escala; aparar, dividir, matriz, apagar) ·
  Desenhar · Medir · Criar.
- **Arquitetura**: Selecionar · **Construir** (Parede, Porta, Janela ▾, Mobiliário solto — o «Componente» do Revit —,
  Pilar, Cobertura ▾, Teto, Laje ▾, Parede cortina ▾) · **Circulação** (Guarda ▾, Rampa, Escada, Elevador) · **Modelo**
  (linha, fazer componente, fazer grupo) · **Ambiente e área** · **Aberturas** · **Referência** (novo pavimento, eixo)
  · **Plano de trabalho** · e no fim os nossos: Acabamentos e Mobiliário.
- **Estrutura**: Selecionar · **Estrutura** (Viga, Parede, Pilar, Laje; sistema de vigas, superfície paramétrica) ·
  **Fundação** (Sapata, sapata combinada, sapatas sob pilares) · Automático (propor a estrutura) · **Referência**
  (Eixo, gerar eixos, grelha estrutural, novo pavimento) · Plano de trabalho. O cálculo passou para **Analisar**.
- **Instalações**: AVAC · Águas e esgotos · Eletricidade · Plano de trabalho (as colisões estão em Colaborar).
- **Inserir** (novo): **Vincular** (desenho DXF/DWG, nuvem de pontos, e as listas de cada um) e **Importar** (imagem de
  fundo, modelo 3D, imagens, componentes de outro projeto, pontos de levantamento) — saíram do Início.
- **Anotar**: Cotas · Desenho · Etiquetas e tabelas · Símbolo. A planta e o corte estão em **Visualizar ▸ Criar**, como
  no Revit.
- **Analisar** (novo): Cálculo (da estrutura) · Mapas · Verificar (o Verificador, IFC, IDS, dados em falta).
- **Colaborar**: Notas · Equipa · Coordenação (colisões).
- **Visualizar**: Gráficos · Apresentação (Render realista ▾, cenas da apresentação, exportar) · Criar (Vista 3D ▾,
  Planta, Corte, pormenor, caixa de corte) · Câmara · Janelas · Tema · Rato.
- **Gerenciar**: Tipos e materiais · Projeto · Pavimentos · Componentes · Grupos · Assistente IA.
- Os nomes dos grupos passaram a ser os do Revit em português (Construir, Ambiente e área, Referência, Plano de
  trabalho, Geometria, Gráficos…). Os desenhos dos ícones são os mesmos; mudaram a ordem e os grupos.
- Numa janela estreita, os grupos da direita continuam a dobrar-se num botão com ▾ cada um (nada se perde).
- As mensagens que dizem onde está uma ferramenta seguem os sítios novos (por exemplo «Inserir ▸ Importar ▸ Imagem de
  fundo»), e a Ajuda (F1) também («Na fita: Arquitetura ▸ Construir»).

## 0.481.0 — 2026-11-09

**A interface do Presentation como a versão nova dele** (o dono: «faça a interface de acordo com a nova versão. O cubo
de navegação devia continuar o mesmo do programa… a imagem eu peguei na internet da versão antiga, e era apenas uma
referência. Ao abrir não precisa vir com a janela de ArqSynth aberta na aba de janelas, apenas quero o ícone da aba da
esquerda e quando ativado, abre a janela de interface»).

- **Não há aba do Presentation ao abrir o programa.** Só o ícone da barra da esquerda. Ao clicar nele abre-se a aba
  «ArqSynth Presentation» (a última, com o seu ×) e a interface. Para a guardar: o ícone outra vez, o × da aba ou outro
  ícone da barra. Volta a vista de onde se veio, com as colunas do BIM como estavam, e a aba desaparece.
- **O cubo de navegação é o do BIM**, e a navegação também. Saíram as teclas T, E, F, D, B e TRÁS.
- **Nada por cima do modelo**, como na versão nova do Presentation:
  - a **câmara** fica numa só linha, na ponta direita da barra de parâmetros (a faixa por cima do 3D): PERSP / ORTO,
    FOV, Enquadrar modelo, Enquadrar selecção e o cadeado;
  - **Renderizado · Auto ▾** fica no rodapé, à esquerda, e o menu abre para cima;
  - a **leitura do sol** fica no rodapé, à direita (um clique abre Ambiente);
  - **+ Criar cena** fica no rodapé fixo da coluna da esquerda, ao lado de «CENAS n», e não desaparece quando a lista
    rola.
- **Leitor das cenas** por baixo do 3D: ‹ ▶ «2/4 · Cena 1» › e o tempo da cena. As setas passam à cena anterior ou
  seguinte, em voo suave (ou corte seco, como a cena tiver). ▶ passa por todas, cada uma o seu tempo; ❚❚ pára.
- No fim da lista das páginas, o cartão **Página final** (tracejado): a página final faz-se no Presentation.

## 0.480.0 — 2026-11-09

**ArqSynth Presentation na barra da esquerda, sem o painel que dividia a coluna** (o dono, com uma captura marcada:
«não quero essa divisão na coluna como parece. Não vi ainda a aba de ArqSynth Presentation na esquerda»).

- Na barra de ícones da esquerda há um ícone novo, **ArqSynth Presentation** (um ecrã com um triângulo azul), logo a
  seguir ao das Regras gráficas. Ao clicar nele, a janela passa à interface do Presentation (a da 0.479: as páginas e
  as cenas à esquerda, as camadas e os ajustes à direita, os comandos sobre o 3D), e o ícone fica aceso. Outro clique
  nele, ou noutro ícone da barra, volta ao BIM como estava.
- O painel antigo **Apresentação** (da 0.363), que aparecia por baixo do Navegador e dividia a coluna, **saiu**. Tudo o
  que ele fazia está na interface do Presentation: a ordem, a cena inicial, as que ficam de fora, a chegada, o efeito,
  a legenda e o tempo (Cenas 3D), o movimento de câmara (Efeitos), o sol (Ambiente), as etiquetas e o passeio, e os
  panoramas 360° (Imagens).
- **Render ▸ Cenas da apresentação** passa a abrir também a interface do Presentation.
- Na coluna da direita, os campos de cada separador ficam juntos no topo (antes espalhavam-se pela altura).

## 0.479.0 — 2026-11-08

**Aba «ArqSynth Presentation»** (o dono: «crie uma aba de ArqSynth Presentation e use as 2 colunas para replicar a
experiência que se tem no ArqSynth Presentation… preparando o modelo 3D para exportação com todas as configurações do
ArqSynth Presentation. Ao clicar na aba a tela muda a interface para a interface do ArqSynth Presentation»).

- Nas abas das vistas, por cima do 3D, há uma aba nova, **sempre a última**: **ArqSynth Presentation** (ícone azul).
  Não tem ×, não se arrasta e não fecha. Ao clicar nela, as duas colunas do BIM dão lugar às do Presentation, com as
  mesmas larguras (o 3D fica do mesmo tamanho). Noutra aba, as colunas do BIM voltam como estavam.
- **Coluna da esquerda**, como a do Presentation:
  - **DIVIDIDO / ABAS**: as páginas com as cenas por baixo da página 3D, ou uma coisa de cada vez (Páginas / Cenas);
  - **PÁGINAS**: a página **Modelo 3D** (01) e uma página **Planta** por cada folha com vistas. O botão **Planta** faz
    uma folha nova. **Capa**, **Texto** e **Concept** fazem-se no Presentation (ficam à vista, sem efeito);
  - por baixo da página Modelo 3D, **Exportar / atualizar** (grava o pacote para o Presentation) e as **cenas** como
    cartões: miniatura com o número e a estrela da cena inicial, nome, «PERSPECTIVA» / «ORTOGONAL» / «FORA DA
    APRESENTAÇÃO», e os seis botões do Presentation — **Atualizar** (a cena fica com a vista atual), **Cena inicial**,
    **Mostrar / esconder**, **Duplicar** («Cena 1 cópia»), **Renomear** e **Eliminar** (Ctrl+Z repõe). Os cartões
    arrastam-se para mudar a ordem; um clique mostra a cena no 3D; duplo clique abre a vista dela;
  - em baixo, **CENAS** com o número, e **TRANSIÇÃO** (0,3 a 5 s): o tempo da chegada a todas as cenas.
- **Coluna da direita**, a barra de ícones do Presentation:
  - **Camadas**: cada elemento que vai para o Presentation, agrupado por categoria (PAREDES, LAJES, PORTAS…), cada um
    com o seu olho, e o grupo com o olho da pasta. Inclui «Procurar peça…», Shift / Ctrl para escolher vários (o olho
    de um escolhido vale para todos), e um clique que escolhe a peça no 3D (duplo clique: enquadra-a);
  - **Cenas 3D** (cena inicial, mostrar, movimento Suave / Corte e duração, efeito, tempo, legenda);
  - **Ambiente** (dia, hora e animação do sol, exposição, céu, «Ver sol»);
  - **Etiquetas** e **Passeio** (os ambientes como etiquetas e como Passeio Virtual);
  - **Imagens** (os panoramas 360°);
  - **Efeitos** (o movimento de câmara, «Ver movimento»).
- **Sobre o 3D**, os comandos do Presentation:
  - **+ Criar cena**: guarda a vista como «Cena N» (uma vista 3D com nome), com a miniatura;
  - **PERSP / ORTO**, **Enquadrar modelo**, **Enquadrar selecção** e o **cadeado** (o rato deixa de mexer a câmara);
  - **FOV** de 20 a 65° (o enquadramento fica);
  - as teclas **T, E, F, D, B, TRÁS** e girar 90°;
  - **Renderizado · Auto**: o modo de visualização (no BIM com o estilo mais parecido), a qualidade, a oclusão ambiente
    e «Aplicar a todas as cenas»;
  - a leitura do **sol** (hora, azimute, altura): um clique abre Ambiente.
  O cubo de vista do BIM sai enquanto a aba está à frente, e a barra de parâmetros mostra os comandos da aba.
- Como no Presentation, os **olhos das camadas** e o **modo** valem para o que se está a ver; **Criar cena** e
  **Atualizar** guardam-nos na cena. Ao escolher uma cena, voltam os dela.
- **Exportação**: cada cena leva a câmara (perspetiva ou ortogonal, FOV, bloqueada), o modo, a qualidade e a oclusão,
  as camadas escondidas, o nome, a transição e tudo o que já ia (efeito, movimento, sol, legenda, tempo). As cenas das
  vistas que se eliminam deixam de ir (as vistas ficam no projeto; «Repor» trá-las de volta).
- **No Presentation** (`C:\BIM\arqsynth`, `lib/presentation/bim-import.ts`), o importador passou a ler também a câmara
  bloqueada e a qualidade e oclusão ambiente de cada cena (teste novo em `scripts/test-bim-import.mts`).

## 0.478.0 — 2026-11-08

**Tabelas em células como no Excel — 2.ª fase** (o dono: «A tela, deve ser em células como no excel e ter as
ferramentas de união de células alinhamento, desenho de bordas, cálculo como no excel… Os elementos da célula devem ser
inseridas com o botão direito do rato e ou botões no painel lateral»).

- Uma **tabela do projeto** aparece agora como uma **folha do Excel**, branca como o papel:
  - as colunas têm letras (A, B, C…) e as linhas números;
  - a primeira linha da tabela leva os cabeçalhos, depois vêm os elementos e a linha dos totais;
  - por cima há uma **barra de fórmula**: mostra a célula escolhida («E7») e o que está nela. Escreve-se lá um texto, um
    número ou uma fórmula e carrega-se Enter.
- **Linhas de título** (por cima da tabela) e **linhas de notas** (por baixo). Escreve-se nelas o que se quiser; um
  texto pode levar os dados do projeto: {projeto}, {data}, {tabela}, {n} (número de elementos).
- **Fórmulas como no Excel**, com vírgula decimal e «;» entre argumentos: `=SOMA(D:D)`, `=D7*1,23`,
  `=ARRED(MÉDIA(E3:E9);2)`, `=SE(D7>20;"grande";"pequeno")`. Funções: SOMA, MÉDIA, MÍNIMO, MÁXIMO, CONTAR,
  CONTAR.VAL, ARRED, ABS, SE (os nomes em inglês também servem). **D:D** quer dizer «todos os elementos da coluna D»,
  sejam quantos forem.
- As fórmulas **continuam certas** quando o modelo muda: com uma parede a mais, a soma passa a contá-la. Também
  continuam certas quando se põem linhas por cima ou se muda a ordem das colunas (cada célula acompanha o seu
  campo). Os erros aparecem como no Excel: #REF!, #VALOR!, #DIV/0!, #NOME?, #CIRC!.
- Ferramentas na **barra de parâmetros**:
  - **Unir** (une e centra; noutro clique separa);
  - **N** (negrito) e **I** (itálico);
  - **Alinhar** (à esquerda, ao centro, à direita);
  - **Bordas** (todas, contorno, contorno grosso, só em baixo, em cima e em baixo, sem bordas);
  - **Fundo** (seis cores claras);
  - **Inserir** (linha acima ou abaixo, linha de título, linha de notas, coluna com um campo, coluna calculada,
    linha dos totais);
  - **ƒx** (soma, média, contagem, máximo ou mínimo da coluna, e os dados do projeto).
- O **botão direito** na tabela tem os mesmos comandos, e ainda Limpar o conteúdo, Apagar a linha e Tirar a coluna.
  A tecla **Delete** limpa as células de títulos e notas (numa linha de elementos continua a apagar os elementos, como
  no Revit).
- No painel **Tabelas**, a nova secção **Inserir na tabela** lista o que se pode pôr: as colunas (os campos que a
  tabela ainda não mostra), as funções, os dados do projeto e as linhas. Basta um duplo clique.
- Uma tabela de categoria (as listas «Paredes (3)», «Lajes»…) continua a ser uma lista. O botão **Formatar como no
  Excel**, na barra, no painel ou no botão direito, faz dela uma tabela do projeto com células.
- **Exportar para o Excel** leva a grelha como está no ecrã: títulos, notas, células unidas, negrito, cores, bordas e
  as fórmulas como fórmulas do Excel (`=SUM(D3:D6)`). Assim o Excel volta a fazer as contas. O JSON para o KazaFix Cost
  mantém o mesmo formato.
- **Na folha**, a tabela aparece como a grelha: título, cores, células unidas, notas e bordas.
- Cada mudança nas células é um passo de anular (Ctrl+Z). A largura das colunas, alargada à mão, fica guardada com a
  tabela.

## 0.477.0 — 2026-11-08

**Tabelas na tela, geridas no painel lateral — 1.ª fase** (o dono: «A aba de tabelas também deve ser gerenciada pelo
painel lateral, mas a tabela deve ser gerada na tela e não no rodapé… seria bom copiar o revit»).

- O botão **Quantidades** da barra lateral abre o painel **Tabelas** na coluna da esquerda. A árvore tem todas as
  tabelas, cada uma com o número de linhas:
  - as **Tabelas do projeto**;
  - as do programa: Quantidades do modelo, Ambientes e acabamentos, Portas e janelas, Instalações e Anotações.

  Tem também uma caixa para procurar uma tabela.
- Um clique numa tabela abre-a **numa aba na tela**, como uma folha. Por cima vai o título como no Revit
  («<Paredes>»), as linhas são numeradas e os totais vão por baixo. Ctrl+T abre a última tabela vista e, com uma
  tabela à vista, fecha-a. As tabelas deixaram de ficar no fundo da janela.
- Os comandos da tabela vão na **barra de parâmetros**: Propriedades…, Por tipo, Realçar no modelo, Pôr numa folha,
  Exportar… e Apagar (nas do projeto).
- No painel ficam os botões **Nova tabela…**, **Propriedades…**, **Duplicar**, **Apagar** e **Exportar…**. O botão
  direito tem ainda «Pôr numa folha nova».
- **Propriedades da tabela como no Revit**, em abas:
  - **Campos**: «Selecionar campos disponíveis em» (a categoria), uma pesquisa de nomes, e «Campos disponíveis» ao
    lado de «Campos tabelados (na ordem)». Entre as duas listas, → acrescenta e ← tira; ↑ ↓ mudam a ordem; ƒx cria um
    valor calculado (uma fórmula);
  - **Filtro**;
  - **Classificar/Agrupar**.

  A tabela de uma categoria fica uma tabela do projeto ao mudar as propriedades.
- **Exportar…** grava também **JSON para outros programas**, a pensar no **KazaFix Cost**. Leva o nome de cada coluna
  e a sua chave fixa, a unidade (m, m², m³, un…), as linhas com os números como números e os totais. Continua também
  a gravar Excel (XLSX) e CSV.
- As próximas fases estão no PLANO (Tabelas como no Revit e no Excel):
  - células como no Excel (unir, alinhar, bordas, fórmulas);
  - formatação e aparência;
  - mais tabelas (vistas, folhas, mapa de vãos, materiais, áreas);
  - as tabelas no modelo base.

## 0.476.0 — 2026-11-08

**A janela já não cresce sozinha.** As três falhas que sobravam da bateria de testes (as cotas de relação, a
fachada na parede curva e o leitor de tutoriais da página inicial) tinham a mesma origem: alguns painéis pediam mais
espaço do que a janela tinha. O programa alargava então a janela — para lá do ecrã, até 2 039 px — ou uma coluna de
painéis, e nunca as devolvia ao tamanho de antes. A vista 3D ficava mais estreita e os cliques caíam noutros sítios.

Corrigido no programa:

- **Página inicial**: as suas cinco colunas pedem 1 258 px. Agora está numa área com deslocamento, como uma página web:
  numa janela mais estreita aparece uma barra de deslocamento, em vez de a janela crescer. Ao abri-la, os painéis
  laterais saem primeiro.
- **Tabelas**: o painel antigo do rodapé (antes da 0.477) pedia 1 398 px — a lista das categorias tem agora uma largura
  fixa (os nomes longos na lista aberta). Na 0.477 as tabelas passaram para abas, e o painel novo das Tabelas, na coluna
  da esquerda, entra no teste «os painéis cabem nas colunas» (abaixo).
- **Painel Programa de necessidades** (o da 0.474): a linha dos totais alargava a coluna da esquerda de 270 para 459 px
  para sempre, e a vista 3D ficava com 425 px. O painel novo da 0.475 já cabe; o teste confirma-o.
- **Folhas**: o desenho da folha ajusta-se a qualquer tamanho; deixou de exigir 640 × 460 px.
- **Painéis da coluna da esquerda** (a coluna tem 270 px numa janela de 1280):
  - **Pavimentos** pedia 377 px. No grupo «Aparência», cada fila de desenhos passa à linha seguinte quando não cabe
    ao lado do nome (e o nome vai para cima dela); os botões «+ Novo», «Apagar» e «Iguais…» ficam do tamanho das
    palavras; numa janela baixa o painel desliza na vertical (pedia 674 px de altura).
  - **Materiais** pedia 286 px: os botões «Novo», «Duplicar», «Apagar» ficam do tamanho das palavras.
  - **Biblioteca ▸ Web** pedia 300 px: as duas listas (catálogo e categoria) ficam estreitas; os nomes inteiros veem-se
    na lista aberta.
- **Propriedades de uma folha** pediam 348 px: a lista do tipo de folha («A3 horizontal · Completo») fica estreita, o
  nome inteiro na lista aberta.

Nos testes: duas verificações novas. «A janela não cresce» diz depois de que passo a janela ficou maior do que o
teste a pôs. «Os painéis cabem nas colunas» abre um a um os painéis acima, numa janela de 1280 × 740, e confirma que
nenhum alarga a sua coluna, que a janela não cresce e que a vista 3D volta à mesma largura. O teste do Programa de
necessidades também confirma a largura da vista 3D. A cor do corte na caixa de corte lê-se nos píxeis mais escuros à
volta do ponto (um só píxel podia cair entre as linhas do tracejado).

A bateria completa da janela passa toda, já com as versões 0.475 a 0.480: nenhuma falha (antes: 6 falhas na 0.474).

## 0.475.0 — 2026-11-08

**Ambientes: o programa de necessidades no painel lateral** (o dono: «A aba ambiente quero que funcione no painel
lateral e não no rodapé… o painel vai ser um gestor de programa de necessidade»).

- O botão **Ambientes** da barra lateral abre agora o painel do programa de necessidades na coluna da esquerda. Antes
  abria as tabelas no fundo da janela.
- No topo do painel, o **tipo de edifício** e o **piso** mostrado (ou «Todos os pisos»). Os tipos: habitação,
  hospital, clínica / centro de saúde, escola, creche, lar de idosos, escritórios, comércio, armazém de venda,
  minimercado, supermercado, restaurante / café, hotel, farmácia, banco e esquadra de polícia.
- A lista de cada piso faz-se no painel: **+ Ambiente**, **Apagar** e **Limpar**. Cada ambiente tem nome, **uso /
  categoria** (os do tipo de edifício), **área pretendida** (opcional), quantidade, piso e exterior. Cada mudança é um
  passo de Ctrl+Z.
- Para **colocar** um ambiente:
  - clique nele na lista e depois dentro das paredes. Debaixo do rato aparece a área e se chega à meta. Depois de
    colocado, a ferramenta passa sozinha ao ambiente seguinte do piso que falta colocar;
  - ou arraste-o da lista e largue-o no espaço.
- Cores da lista:
  - **verde**: a meta foi atingida (a área pedida ou mais, tantos quantos pedidos);
  - **laranja**: está colocado mas com menos área (ou menos vezes) do que o pedido, para verificar;
  - **vermelho**: zonas conflitantes.
- **Zonas conflitantes**: regras por tipo de edifício para ambientes que não devem comunicar diretamente por uma
  porta. Alguns exemplos:
  - em todos: instalação sanitária ↔ cozinha;
  - habitação: garagem ↔ quarto;
  - hospital e clínica: sujos ↔ esterilização; no hospital, morgue ↔ zonas do público;
  - restaurante: instalação sanitária ↔ sala de refeições;
  - lojas de alimentos: instalação sanitária ↔ área de venda, talho, padaria e câmara frigorífica;
  - banco: cofre e tesouraria ↔ público;
  - polícia: celas e armeiro ↔ público.

  Quando acontece:
  - aparece logo um aviso;
  - as duas linhas ficam a vermelho, com a explicação por baixo da lista;
  - o Verificador conta o aviso «Zonas conflitantes — verifique» no rodapé, e mostra-o no painel (Ir para,
    Exceção…) e na ficha.
- **Importar…** lê também **JSON**, como uma IA o escreve: por pisos ou numa lista, com chaves em português ou inglês.
  Os pisos encontram-se pelo nome e os usos pelo nome ou por uma palavra. **Pedir à IA…** copia o pedido certo para
  colar numa IA (ChatGPT, Claude, Gemini…).
- Cada ambiente colocado guarda a ligação à sua linha do programa e o seu uso, que o Verificador também usa.

## 0.474.0 — 2026-11-08

**A bateria de testes da janela volta a passar** (o dono: «Faça esta tarefa aqui: corrigir as 24 falhas antigas»).
Havia 24 verificações a falhar desde as versões 0.442–0.471. Umas eram defeitos do programa, outras testes que
ficaram para trás depois de mudanças feitas de propósito.

Corrigido no programa:

- **Abrir um IFC em segundo plano**: enquanto o ficheiro ainda era lido, o painel Pavimentos dava um erro (o «=» dos
  pavimentos iguais perguntava ao IFC antes de ele existir). O rodapé com o pavimento e a árvore não se atualizavam.
- **Fachada de vidro numa parede curva**: o início e o fim agarravam aos cantos das facetas da parede (as faces da
  parede curva são desenhadas em bocadinhos retos). O arco saía uns graus ao lado e encostado à face interior. Agora
  segue exatamente o ponto clicado, sempre entre as pontas da parede.
- **Tema escuro no painel Materiais**: as notas cinzentas («Usado em … tipo(s)», as dicas) ficavam com a cor do tema
  claro e quase não se liam. Agora mudam com o tema.
- Duas funções repetidas no código, em que a segunda escondia a primeira: a imagem da vista (usada nas notas) e o painel
  de vidro das guardas.

Os testes acompanham agora o que mudou de propósito: a aba «Folhas» do navegador que fica escolhida (0.470), os lados
do polígono que se escolhem com um clique perto deles (0.459), o valor das cotas em cima da linha (0.446), Afastamento,
Cadeia e Raio na barra da Parede (0.450), as formas novas da Laje antes da varinha mágica (0.456), o aspeto realista
dos materiais no render (0.470), o duplo clique na legenda que abre «Editar tipo» (0.470) e as cotas temporárias da
porta escolhida (0.398).

Ficam 6 das 24. Três só falham na bateria completa: as cotas de relação, a fachada na parede curva e o leitor de
tutoriais da página inicial. Algum teste anterior deixa estado para trás; para as cotas, já se sabe que está entre os
fluxos da apresentação e o dos estilos de símbolos. As outras três falham umas vezes sim, outras não (dependem de
tempos).

## 0.473.0 — 2026-11-08

**O carimbo desenha-se na própria folha** (o dono: «se o carimbo pudesse abrir na tela e o utilizador usar as
ferramentas de desenhos e inserir os campos seria melhor… Maior liberdade criativa»).

- **Editar carimbo…** já não abre uma janela. A folha fica esbatida e aproxima-se do canto do carimbo, com uma
  quadrícula clara, e o carimbo desenha-se ali — como a família do carimbo no editor do Revit.
- Na barra de parâmetros: **✓ Concluir** e **Cancelar**, sempre à vista, e as ferramentas **Selecionar, Linha,
  Retângulo, Texto, Campo, Imagem**:
  - **Linha** e **Retângulo**: dois cliques ou arrastar; espessura de 0,13 a 1 mm; o retângulo pode ser cheio (cinza
    claro, cinza ou preto).
  - **Texto**: escreve-se no próprio sítio (Enter acaba, Shift+Enter muda de linha); tamanho, negrito, alinhamento e
    cor (preto ou cinzento).
  - **Campo**: uma caixa que em cada folha mostra um dado — obra, dono de obra, local, autor, fase, desenho, folha n.º,
    escala, data, **revisão**, **total de folhas** e os **campos próprios do projeto**. Enquanto se desenha, um campo
    vazio mostra o seu nome entre ‹ ›, a cinzento (no papel não sai nada).
  - **Imagem**: o logótipo (PNG, JPG, SVG…) numa caixa, nas suas proporções.
- **Snaps** como nas ferramentas de desenho, a magenta: pontas e cantos, meios, alinhado com eles ou com a margem,
  horizontal e vertical; fora disso, de 0,5 em 0,5 mm. Enquanto se desenha aparece o comprimento ou o tamanho em mm.
- **Selecionar**: clique (Shift: mais), janela (arrastada da direita: tudo o que toca), arrastar para mover, pegas para
  mudar pontas e cantos, setas (0,5 mm; Shift: 5 mm), Delete, Ctrl+C / Ctrl+V, Ctrl+A, Ctrl+Z / Ctrl+Y, duplo clique
  num texto para o reescrever (ou numa imagem para a trocar).
- **Começar de**: o carimbo completo, o compacto, a faixa lateral, o exemplo com logótipo, o do escritório ou em branco
  (Ctrl+Z volta atrás). Na primeira vez começa do carimbo que a folha mostra.
- O carimbo fica preso ao **canto de baixo à direita** da margem, em qualquer papel (A4 a A0, deitado ou em pé). As
  vistas arrumam-se por cima dele — ou ao lado, quando ele sobe pelo lado como uma faixa.
- **Guardar no escritório** guarda-o para os projetos novos (as imagens copiadas para a pasta da suite ArqSynth). **Em
  todas as folhas** (ligado) ou só na folha aberta.
- **✓ Concluir** guarda-o no projeto: um só Ctrl+Z desfaz. **Cancelar** pergunta antes de deitar fora o que mudou.
- O carimbo feito na 0.472 (linhas de caixas) abre como desenho, para continuar a editar.

## 0.472.0 — 2026-11-08

**Folhas: os comandos na barra de parâmetros, desenhos importados e o carimbo da empresa** (pedido do dono, com
captura).

- **Barra de parâmetros**: com uma folha aberta, a barra por baixo da fita mostra os comandos da folha, como os de uma
  ferramenta: − e + (zoom), Ver tudo, a escala do que está escolhido, Arrumar, **Importar desenho…**, **Editar
  carimbo…**, Atualizar desenhos e Exportar PDF…. A barra que havia por cima do papel saiu.
  - Clique numa vista da folha: a **escala da vista** aparece na barra.
- **Importar desenho…** põe na folha um desenho de fora:
  - **DWG ou DXF** numa escala (1:1 a 1:1000). Ao entrar, fica na maior escala em que cabe; muda-se na barra. As linhas
    e os textos saem a preto. Para DWG é preciso o ODA File Converter.
  - **Imagem** (PNG, JPG, BMP, GIF, TIF, WEBP) ou **SVG**, com a largura em mm escolhida na barra.
  - Arraste-o para o pôr no sítio. **Delete** tira-o da folha. Ctrl+Z desfaz.
  - Sai no PDF, no PNG e no SVG das folhas. O ficheiro fica onde está; o projeto guarda também o caminho relativo, e
    encontra-o se a pasta do projeto mudar de sítio.
- **Editar carimbo…**: o carimbo da sua empresa, desenhado ao vivo enquanto se faz:
  - o **nome**, os **contactos** (várias linhas) e o **logótipo** (uma imagem);
  - a largura do carimbo e as suas **linhas**, de cima para baixo. Cada linha tem a sua altura e as suas caixas; cada
    caixa mostra um campo (logótipo, empresa, contactos, obra, dono de obra, local, autor, fase, desenho, escala, data,
    folha n.º, ou vazia) e ocupa a sua parte da linha. Linhas e caixas juntam-se, tiram-se e mudam de ordem;
  - os **nomes dos campos** como a empresa os diz (por exemplo «Obra» → «Projeto»);
  - **Usar em** esta folha ou em todas as folhas: o carimbo delas passa a «Da empresa (personalizado)», que também se
    escolhe em Editar tipo….
  - **Guardar como carimbo da empresa** guarda-o para todos os projetos (na pasta da suite ArqSynth, com uma cópia do
    logótipo); **Usar o da empresa** traz esse carimbo para o projeto.
- O carimbo da empresa fica gravado no projeto e não se perde ao mudar os dados da obra.

## 0.471.0 — 2026-11-08

**Materiais ▸ Web: as texturas gratuitas da Poly Haven** (o dono: «Sim, liga»).

- O painel **Materiais**, em Selecionar, tem agora duas fontes no topo: **No projeto** e **Web**.
- **Web** lista as 869 texturas da Poly Haven (polyhaven.com), em domínio público (licença **CC0**: usar em qualquer
  projeto, também comercial). Mostra as miniaturas da própria Poly Haven, uma escolha de categoria (tijolo, madeira,
  betão, reboco, azulejo, pedra, metal, tecido, pavimentos, coberturas…) e a pesquisa por nome. A lista fica guardada
  um dia, e as miniaturas também.
- **Um clique** numa textura:
  - descarrega as imagens em 1k (cor, mapa normal, rugosidade e oclusão; nos metais também o metálico), só da
    primeira vez, para Documentos/ArqSynth/Texturas/Poly Haven;
  - cria um material do projeto com o nome da textura, a categoria certa (tijolo corta-se como alvenaria, madeira
    como madeira…) e a cor média da imagem;
  - põe a textura no tamanho real (a Poly Haven diz quantos metros a imagem cobre);
  - ativa o balde de tinta com esse material: basta clicar nas faces.
- Uma textura já trazida não se descarrega de novo. O material fica em «No projeto» e abre-se em Editar como os
  outros.
- Clique direito numa textura: trazer para o projeto, ou ver a página dela na Poly Haven.
- Créditos por baixo da escolha de categoria, como a Poly Haven pede.

## 0.470.0 — 2026-11-08

**Folhas: aba própria no navegador, propriedades na coluna, «Editar tipo…» como no Revit, A4 e zoom** (o dono:
«Colocar a opção de filtro da folha também no rodapé… deve ficar última aba, já que a ultima coisa a ser feita é folha
e impressão»; «A edição do tipo da folha e propriedades devem ficar na coluna de propriedade. E a edição numa janela
própria que abre como no revit»; «deve incluir tamanho A4»; «permitir zoom na folha»).

- **Navegador do Projeto**: aba **Folhas** no rodapé, a última (Tudo, Vistas, Biblioteca, Projeto, Folhas). Mostra só
  as folhas e as vistas de cada uma; o clique direito tem imprimir e exportar. As folhas continuam em «Tudo». O ícone
  Folhas da barra lateral abre esta aba.
- **Propriedades da folha** na coluna Propriedades, como no Revit: um clique numa folha do navegador, ou a folha
  aberta sem nada escolhido nela.
  - Em cima, o **tipo** da folha (papel, orientação e carimbo: «A3 horizontal · Completo»), a escolher na lista.
  - Por baixo, **Editar tipo…**.
  - Identificação: número (vazio = automático) e nome.
  - Folha: papel, carimbo, vistas na folha, conjuntos (separados por vírgulas) e **Revisões…**.
  - Carimbo (em todas as folhas): os dados do projeto que o carimbo mostra.
- **Editar tipo…** abre a janela do tipo, como as Propriedades do tipo do Revit:
  - família «Carimbo ArqSynth»; papel, orientação e modelo de carimbo, com a imagem da folha;
  - aplicar a todas as folhas deste tipo (como no Revit) ou só a esta;
  - o que o carimbo mostra em todas as folhas: obra, dono de obra, local, autor, fase, campos próprios e numeração;
  - também abre com duplo clique na legenda da folha, ou pelo clique direito numa folha no navegador.
  - O papel, o modelo e o botão «Legenda…» saíram da barra da folha.
- **Papel A4**, e qualquer papel **na vertical** (A4 a A0). O PDF sai na orientação da folha.
- **Zoom na folha**:
  - a roda do rato aproxima no sítio do cursor, e o botão do meio arrasta a folha;
  - duplo clique com o botão do meio, ou «Ver tudo», mostra a folha inteira;
  - botões − e + na barra da folha.

## 0.469.0 — 2026-11-08

**As texturas e o aspeto realista dos materiais no 3D (estilo Realista) e no render** (continuação do pedido do dono:
«colocar suporte a textura, e todos os controlos de um material realista… inspirar no D5 Render»).

- No estilo **Realista**, as faces de um material com texturas mostram a imagem, iluminada:
  - assentam como no SketchUp e no Revit: numa parede ao longo dela e para cima, num piso em planta;
  - com o tamanho em metros, a rotação e o deslocamento do painel Materiais;
  - com o mapa normal (relevo à luz), a rugosidade, o metálico, a oclusão e a emissão;
  - recebem as sombras do sol.
- Um clique continua a escolher o elemento por baixo da textura. O elemento selecionado (ou colorido por uma regra
  gráfica) perde a textura enquanto o está, para se ver o realce.
- Nos outros estilos (Sombreado, Linhas ocultas…) e nas plantas e cortes não há texturas.
- **Estilos de vista**: há a opção nova «Texturas dos materiais» (ligada no Realista), para os estilos do projeto.
- **Render realista** (Render ▸ Render realista, Mitsuba): um material com aspeto realista próprio usa os controlos
  todos do painel Materiais:
  - tipo: padrão, vidro (fino; fosco quando rugoso), água (com refração), luz e tecido;
  - rugosidade, metálico, reflexão, verniz e brilho de tecido;
  - as texturas: cor base (com a oclusão), mapa normal ou de altura (relevo), rugosidade, metálico, opacidade e
    emissão;
  - um material de luz ilumina a cena com a sua cor e intensidade (cd/m²).
- Os materiais sem aspeto próprio continuam a sair pelo acabamento, como antes.

## 0.468.0 — 2026-11-08

**Painel Materiais na coluna, como a Biblioteca, com Selecionar e Editar** (o dono: «A aba materiais eu quero que fique
antes da aba biblioteca, e deve ser semelhante à biblioteca. a janela flutuante de criação e configuração dos materiais
deve ser redesenhada. Vai ter a aba editar/criar para esse efeito. tudo deve ser feito na coluna e nada de janela
flutuante… opção de como vai aparecer na vista, em corte, e na vista realista, colocar suporte a textura, e todos os
controlos de um material realista… inspirar no D5 Render»; e «o navegador de material no lado direito deve ser
removido»).

- O ícone **Materiais** da barra lateral passa para antes da Biblioteca e abre um painel na coluna (já não abre janela).
- **Selecionar**: os materiais com miniaturas em **cubo**, como no SketchUp (ou em esfera), por família e com pesquisa;
  miniaturas pequenas, médias, grandes ou lista. **Um clique pinta com o material** (ativa o balde de tinta, como no
  SketchUp); duplo clique abre-o em Editar. Novo, Duplicar e Apagar estão no topo. Com o balde ligado, «Sem pintura»
  aparece em primeiro.
- **Editar**: a imagem do material iluminada (esfera ou cubo) segue cada alteração. Por baixo, partes que se dobram:
  - **Na vista (3D, alçados)**: padrões de superfície, sombreamento e transparência, como antes;
  - **Em corte (plantas, cortes)**: padrões de corte, como antes;
  - **Realista (render)**, inspirado no D5: tipo (padrão, vidro, água, luz, tecido) e acabamentos prontos (baço,
    acetinado, brilhante, lacado, metal polido ou escovado, vidro, vidro fosco, água, tecido, luz); cor base,
    rugosidade, metálico, reflexão, verniz, brilho de tecido, refração (IOR), emissão e intensidade;
  - **texturas**: cor base, mapa normal (relevo), rugosidade, metálico, altura, oclusão (AO), opacidade e emissão. Um
    clique escolhe a imagem; o clique direito troca, inverte (branco por preto) ou tira;
  - **Texturas no modelo**: tamanho em metros (mantém a proporção da imagem), rotação e deslocamento;
  - **Dados**: massa volúmica e condutibilidade térmica.
  - **Aplicar** grava (um passo de desfazer); **Repor** volta ao que está no projeto. Ao mudar de material com
    alterações por gravar, o programa pergunta.
- As imagens escolhidas são copiadas para Documentos/ArqSynth/Texturas, para não se perderem se o original mudar de
  sítio. Uma imagem que não esteja onde estava é procurada ao lado do projeto (e na sua pasta «texturas»).
- No IFC, o aspeto realista fica no material de três formas:
  - o texto «Realista» nos ArqSynth_Parametros;
  - um IfcSurfaceStyleRendering com rugosidade e metálico, como o Bonsai os guarda;
  - as texturas como IfcImageTexture (com tamanho e rotação), que outros programas leem.
- O «Navegador de Materiais» ao lado das Propriedades foi retirado: as Propriedades ficam só com as propriedades.
- Por fazer a seguir: mostrar as texturas e o aspeto realista no estilo de vista Realista e no render.

## 0.467.0 — 2026-11-08

**Biblioteca ▸ Web ligada a uma coleção gratuita: os modelos da Poly Haven** (o dono: «Sim, liga uma»).

- Na aba **Web** da Biblioteca há agora uma escolha de **coleção**: **Poly Haven** (a primeira, já ligada), a loja
  ArqSynth (para os criadores, mais tarde) ou um catálogo por endereço.
- A Poly Haven (polyhaven.com) dá mais de 500 modelos 3D em domínio público (licença **CC0**: usar em qualquer
  projeto, também comercial, sem pedir licença). Mobiliário, plantas, iluminação, decoração, objetos de cozinha…
- A lista mostra as **miniaturas** da própria Poly Haven e tem uma escolha de **categoria** e a pesquisa por nome. A
  lista fica guardada um dia e as miniaturas também, para não as descarregar de novo.
- **Um clique** num modelo descarrega-o (em 1k, leve) para a biblioteca local (pasta Web ▸ Poly Haven), traz-o para o
  projeto como componente e ativa logo a colocação. Um modelo já descarregado não se descarrega de novo.
- O componente fica com a **cor média da textura** de cada material, em vez de cinzento escuro.
- Clique direito num modelo: «Ver a página» abre a página dele no site.
- Créditos por baixo da lista, como a Poly Haven pede.

## 0.466.0 — 2026-11-08

**Biblioteca de componentes com miniaturas, como no SketchUp** (o dono: «A próxima aba que vamos trabalhar é a aba
Biblioteca, nessa não quero repetição do que já vemos na navegação do projeto… uma biblioteca mesmo dos componentes com
miniaturas dos componentes assim como no Sketchup. Deve ser feita com as opções de visualização, biblioteca local e web.
No futuro os criadores poderão vender componentes dentro desse ecossistema»).

- O ícone **Biblioteca** da barra lateral abre agora um painel próprio, em vez do Navegador.
- **Miniaturas** de cada componente em perspetiva, com as cores das peças, sombreado e as arestas onde a forma dobra,
  como as do SketchUp. Ficam guardadas e não se desenham duas vezes.
- **Três fontes**, no topo:
  - **No projeto**: os componentes deste projeto. **Um clique** na miniatura ativa logo a colocação com o rato, sem
    botão «Colocar» (o dono: «basta clicar no componente ele ativa o modelo para ser inserido»). Clique direito:
    guardar na biblioteca local ou selecionar as cópias no modelo.
  - **Local**: uma pasta neste computador (Documentos/ArqSynth/Biblioteca, ou outra em «Pasta…»), em que as subpastas
    são categorias. Um componente guardado pelo ArqSynth é um ficheiro IFC próprio, que o Revit e outros programas BIM
    também leem. Ficheiros SketchUp, Rhino, glTF/GLB, OBJ e STL na pasta também contam. Um clique traz o componente
    para o projeto e coloca-o; um clique numa pasta abre-a.
  - **Web**: o lugar da loja ArqSynth, onde criadores vão publicar e vender componentes. Já lê um catálogo pelo
    endereço (lista com miniatura, autor, licença, preço e ficheiro). Os gratuitos descarregam-se para a biblioteca
    local e colocam-se; as compras ainda não estão abertas.
- **Como ver**: miniaturas pequenas, médias ou grandes, ou lista com nomes. Há pesquisa por nome.

## 0.465.0 — 2026-11-08

**Linha de pontos, opções com desenhos e o «=» ligar/desligar** (o dono: «acrescentar o tipo de linha de pontos. O botão
= deve ligável e desligavel. Só faz o efeito quando o botão está ligado… colocar opções visuais em vez de texto»).

- **Linha de pontos** para os níveis (e para os outros símbolos: cortes, detalhes), no ecrã, nas folhas e no PDF
  (pontos redondos).
- **Aparência dos níveis com desenhos em vez de listas de texto**: cada opção é uma fila de botões com o desenho do que
  fica — a linha, a cor (quadradinhos; o último abre a paleta), a extremidade, as pontas e a disposição do texto. O
  nome aparece ao passar o rato. Os desenhos seguem o tema claro ou escuro.
- **Botão «=»** no painel Pavimentos, ligado ao abrir o projeto:
  - ligado: o que se faz num pavimento igual (modelar, mudar, apagar, cotar, desenhar na planta) faz-se em todos;
  - desligado: cada pavimento muda sozinho e o que se fizer assim fica só nele, mesmo depois de voltar a ligar.
  A marca «=A» fica a cinzento e o rodapé diz «(= desligado)».
- A opção do painel passa a chamar-se **«No 3D, ver só o pavimento ativo»** (na fita: «3D: só o pavimento ativo»). A
  dica explica que vale também para cortes e alçados, e que a planta mostra sempre só o seu pavimento (o dono: «a
  opção: ver só o pavimento ativo, deveria ser mais clara, para mostrar que é no 3D»).

## 0.464.0 — 2026-11-08

**Níveis ajustáveis em cada vista, e a linha só dos lados** (o dono: «os símbolos dos níveis precisam ser ajustável no
3D na vista e corte para não cobrirem o corte ou ficar sobre o modelo… também um utilizador pode não querer que as
linhas fiquem em cima do desenho, incluir essa opção»).

- **Cortes e alçados**: com Selecionar, um clique na linha de um nível (fora do edifício) ou no seu símbolo ou texto
  escolhe os níveis, com uma pega em cada ponta. Arraste uma ponta, ou clique nela e depois onde a quer: as linhas de
  todos os níveis dessa vista passam a acabar aí, alinhadas como no Revit, e os símbolos vão com elas, para fora do
  corte e do modelo.
- **3D**: o mesmo com o anel dos níveis. Escolhido, tem uma pega em cada canto; arrastar um canto alarga ou estreita o
  anel e leva a extremidade e o texto para onde não tapam o modelo.
- Cada vista guarda o seu ajuste (fica no projeto), e as folhas, o PDF e o DXF desenham os níveis assim. Ctrl+Z
  desfaz.
- **Linha por cima do desenho** (painel Pavimentos ▸ Aparência dos níveis): desligada, a linha do nível pára antes do
  edifício e fica só dos lados, com a extremidade e o texto. A pré-visualização mostra um edifício para se ver a
  diferença.

## 0.463.0 — 2026-11-08

**Pavimentos iguais no fluxo de trabalho** (o dono: «Se quiser selecionar um grupo de nível e igualar, tudo que se faz
num nível igualado é replicado nos outros níveis, seja modelação, modificação, documentação»).

- **Escolher e igualar**: na lista do painel Pavimentos escolha vários pavimentos (Ctrl ou Shift); o botão passa a
  **Igualar (n)** e iguala-os de uma vez. Os elementos do pavimento ativo (ou do mais baixo dos escolhidos) são
  copiados para os outros, e se esses já tinham elementos, ficam com eles e o aviso diz quais. Um pavimento que já é
  igual a outros tem de ser separado primeiro. Com um só escolhido, «Iguais…» abre a janela de antes.
- **Documentação replicada**: as **cotas** e os **desenhos 2D** (linhas, textos, regiões, máscaras…) feitos na planta
  de um pavimento igual aparecem nas plantas de todos os iguais. São os mesmos, por isso mudados ou apagados num, mudam
  ou desaparecem em todos. As cotas automáticas (exteriores, interiores) refeitas num deles substituem as de todos.
- A modelação e as modificações já se replicavam (desde a 0.90): paredes, lajes, pilares, portas e janelas…
- **Separar**: cada pavimento fica com uma cópia própria das cotas e desenhos 2D, e as cotas ficam presas às paredes do
  seu próprio pavimento.
- No rodapé, ao lado do pavimento ativo: «igual a Piso 2, Piso 3…».

## 0.462.0 — 2026-11-08

**Aparência dos níveis no painel Pavimentos, e os níveis no 3D** (o dono: «TAMBÉM DEVE SER CRIADO AUTOMATICAMENTE A
REPRESENTAÇÃO DOS NÍVEIS NO 3D, VISTAS E CORTES. A REPRESENTAÇÃO, OU APARÊNCIA ESSES ELEMENTOS DEVER SER CONFIGURADOS
NESSA ABA. A LINHA E A EXTREMIDADE»).

- O painel **Pavimentos** tem uma secção nova, **Aparência dos níveis**, com uma pré-visualização que muda logo:
  - **Linha**: traço-ponto, tracejada, contínua ou só nas pontas;
  - **Cor**: a do desenho, preto, azul, vermelho, verde, cinzento, ou outra à escolha;
  - **Extremidade**: círculo em quartos (como o Revit), quadrado, triângulo ou nenhuma (só o texto);
  - **Pontas**: à direita, à esquerda ou nas duas;
  - **Texto**: cota e nome; «NOME | cota»; nome por cima e cota por baixo (Revit); cota por cima e nome por baixo;
  - **Mostrar os níveis no 3D**.
  O texto fica junto da extremidade, virado para o desenho. Cada mudança desfaz-se com Ctrl+Z.
- Os níveis aparecem sozinhos, com esta aparência, nos **alçados e cortes** (ecrã, folhas, PDF, DXF) e agora também
  no **3D**: cada nível é um anel à volta do edifício à sua cota, com a extremidade e o texto na frente, escondido atrás
  do edifício como no Revit.
- O diálogo **Anotar ▸ Símbolos…** tem as mesmas opções novas do nível.

## 0.461.0 — 2026-11-08

**Navegador do Projeto com abas de filtro no rodapé** (o dono: «no rodapé, vamos colocar outras abas de filtro, Geral…
Vistas… Biblioteca… Projeto… remover essas abas atuais e substitua por esse»).

- No rodapé do Navegador, quatro abas escolhem o que a árvore mostra:
  - **Tudo**: tudo, como até agora;
  - **Vistas**: só as vistas (plantas, cortes, alçados, vistas 3D, eixos, folhas);
  - **Biblioteca**: só os componentes e grupos do ficheiro;
  - **Projeto**: só o que está no modelo (terreno, edifício, pavimentos e os seus elementos, esboços).
  A pesquisa procura dentro da aba escolhida, e a aba fica escolhida para a sessão seguinte.
- Saíram as abas antigas do rodapé (Navegador do Projeto · Pavimentos · Regras gráficas). Os **Pavimentos** e as
  **Regras gráficas** abrem-se pelos seus ícones na barra lateral, um painel de cada vez no mesmo lugar. Os ícones
  Biblioteca e Folhas abrem o Navegador já na aba Biblioteca ou Vistas.

## 0.460.0 — 2026-11-08

**A parede curva com as camadas do seu tipo na planta** (o dono: «a parede curva não tem camadas de reboco. devia ter
já que são mesmo tipo»).

- Na planta (detalhe «Fino»), a parede curva é cortada nas **camadas do seu tipo** como a reta: reboco, bloco e
  reboco, cada uma em anel à volta do centro, com as mesmas tramas. Isto vale para os arcos e para os círculos
  completos.
- Numa concordância entre paredes retas, o reboco de fora e o de dentro **seguem pela curva** sem linha onde as paredes
  se encontram; o bloco fica um só.
- O mesmo nas folhas em PDF e DXF (desenham a planta do mesmo modo). Em corte, a parede curva continua com a trama do
  seu material principal.

## 0.459.0 — 2026-11-08

**Lados e arcos do polígono, parede sobre um arco e raio da parede curva, como no Revit** (o dono: «não consigo
selecionar linhas e arcos no polígono para ajustar. Ao desenhar a parede por seleção de aresta, no arco ele só seleciona
segmentos em vez de arco inteiro. Selecionei um arco na parede, mas não tem cota temporária para ajustar»).

- **Polígono** (uma face desenhada com a Linha, o Retângulo, o Círculo…): com Selecionar, um clique **no contorno**
  escolhe só esse lado, realçado a azul; um clique no meio continua a escolher a face inteira.
  - Um lado reto mostra o **comprimento como cota temporária**: clique no valor e escreva outro. Tem pegas nas pontas
    e no meio para o arrastar.
  - Um **arco** (canto arredondado, círculo) escolhe-se **inteiro** e mostra o **raio**. Se o arco for uma
    concordância, mudar o raio mantém-no tangente aos dois lados, que encurtam ou alongam. Um círculo muda de tamanho.
- **Parede ▸ Escolher linhas** (e **Linha ▸ Escolher linhas**): numa aresta que faz parte de um arco — canto
  arredondado de um polígono, círculo, arco de linhas, face de uma parede curva —, o arco é escolhido **inteiro** e sai
  **uma parede curva** (ou um arco) sobre ele, com o Afastamento para o lado do rato.
- **Parede curva escolhida**: mostra o **raio como cota temporária**. Numa concordância entre duas paredes retas, o raio
  novo mantém-na tangente: as duas paredes encurtam ou alongam e voltam a ligar-se. Uma parede curva sozinha muda de
  raio à volta do centro.
- Teste na janela real: 44 de 44 passos certos (7 novos para estes casos).

## 0.458.0 — 2026-11-08

**Polígonos e elipses na Linha, como no Revit** (o dono: «Faço também os polígonos e a elipse na Linha? — Sim, faz»).

- A fila **Desenhar** da Linha (e do Retângulo, Círculo, Arco, Bézier, Linha livre) tem agora todas as formas do
  painel «Desenhar» do Revit, pela ordem dele, com quatro ícones novos:
  - **Polígono inscrito**: clique no centro e onde fica um canto — ou escreva o raio e Enter;
  - **Polígono circunscrito**: clique no centro e onde fica o meio de um lado — ou escreva a distância e Enter;
    os **Lados** (3 a 16) na barra;
  - **Elipse**: clique no centro, na ponta de um eixo (ou escreva o semieixo) e mova o rato para o outro semieixo
    (ou escreva-o) — fica uma face, como o círculo, que o Push/Pull levanta com os lados lisos;
  - **Elipse parcial**: clique nas duas pontas do eixo (ou escreva o comprimento) e mova o rato para a altura (ou
    escreva-a) — uma **meia elipse** que se escolhe inteira. Escolhida, mostra os **dois semieixos como cotas
    temporárias**: clique num valor e escreva outro (as linhas presas às pontas acompanham). Tem pegas nas pontas e no
    cimo, e os semieixos e segmentos nas Propriedades. Se fechar um contorno com linhas, faz a face.
- Os polígonos e a elipse são desenhados pela ferramenta Círculo; o botão **Círculo** da fita volta sempre ao círculo.
- Teste na janela real: 37 de 37 passos certos (8 novos para estas formas).

## 0.457.0 — 2026-11-07

**Parede em polígono regular, como no Revit.**

- **Parede ▸ Forma**: dois ícones novos, **Polígono inscrito** (clique no centro e num canto) e **Polígono
  circunscrito** (centro e meio de um lado), com o número de **Lados** na barra; ou o raio escrito e Enter. As
  paredes ficam ligadas nos cantos, desenhadas pelo eixo ou pela face interior / exterior (Tab).
- Teste na janela real: 29 de 29 passos certos.
- Testes: o ficheiro Rhino de exemplo com blocos passa a ser criado num processo à parte — a biblioteca rhino3dm, ao
  criar um bloco com o IfcOpenShell ou o Qt já carregados, às vezes rebentava (um defeito dela; o programa só lê
  blocos, não os cria).

## 0.456.0 — 2026-11-07

**Laje, Piso, Teto, Região e Máscara com as opções de desenho do Revit** (o dono: «Sim, põe»).

- **Forma / Contorno** na barra (ícones novos): **polígono inscrito** (clique no centro e num canto) e **polígono
  circunscrito** (centro e meio de um lado), com o número de **Lados** na barra; **elipse** (centro, ponta de um eixo,
  largura — ou os semieixos escritos); **Escolher linhas**: clique nas linhas, arestas ou faces de parede uma a uma —
  o contorno faz-se delas, cada canto onde uma encontra a seguinte; clique de novo na primeira (ou Enter) para fechar.
  O Teto e o Piso ganham também o **círculo**.
- **Afastamento**: o contorno sai essa distância para fora (negativo: para dentro). **Raio dos cantos**: todos os
  cantos arredondados (no retângulo, polígono, polígonos regulares e linhas escolhidas). A pré-visualização já mostra
  o contorno final.
- As curvas ficam como desenhadas (arcos e curvas no contorno: «Editar contorno» muda-as depois).
- **Desenho 2D ▸ Região / Máscara**: a fila **Contorno** com as mesmas formas, o Afastamento e o Raio (os arcos
  guardados como arcos).
- Barra do Teto mais curta (Rasgo, Sanca, Descida) para caber num ecrã de 1920 px.
- Teste na janela real alargado: 28 de 28 passos certos.

## 0.455.0 — 2026-11-07

**Arco de concordância como no Revit, em linhas, polígonos e no Desenho 2D** (o dono: «o arco não é um arco, mas um
monte de segmentos, não dá pra selecionar o raio inteiro para ajustar o raio como no revit. tentei fazer isso no
polígono, mas não funcionou, isso também deve ser colocado na região, máscara etc»).

- **Linha ▸ Arco de concordância**: o arco entre as duas linhas é agora um arco verdadeiro (como o da ferramenta
  Arco): um clique escolhe-o inteiro e mostra o **raio como cota temporária** — clique no valor, escreva outro raio e
  Enter. As duas linhas são aparadas ou esticadas e o arco **continua tangente** a elas. O mesmo pelo campo «Raio»
  das Propriedades.
- **Polígonos** (uma face desenhada com a Linha, um retângulo): clique em dois lados que fazem um canto — o canto
  fica arredondado, a face inteira.
- **Desenho 2D ▸ Arco de concordância** (ícone novo, ao lado do Arco): o canto de uma **região**, **máscara**,
  **polilinha** ou **retângulo** fica em arco verdadeiro (guardado como arco: acompanha quando se move ou roda, e sai
  em arco no papel, SVG e DXF); entre **duas linhas** nasce um arco 2D próprio.
- Testado na janela real, clique a clique, em todos os recursos novos (paredes: raio, cadeia, afastamento, os três
  arcos, concordância, escolher linhas, ângulos; linhas; polígono; alinhar; máscara): 21 de 21 passos certos
  (`tests/gui_desenho_revit.py`).
- Limite: no polígono e na região o raio ainda não se muda depois (Ctrl+Z e de novo).

## 0.454.0 — 2026-11-07

**Os arcos da parede como os do Revit.** Dois ícones novos em Parede ▸ Forma (o «Arco» que já havia é o
«início, fim, raio» do Revit).

- **Arco por centro e pontas**: clique no centro, depois no início do arco (dá o raio), depois no fim — o arco vira
  para o lado para onde leva o rato. Também por teclado: o raio + Enter, depois o ângulo em graus + Enter.
- **Arco tangente na ponta**: clique na ponta de uma parede (reta ou curva); o arco sai dela tangente e segue o rato
  até ao clique. Os arcos seguintes continuam tangentes, em cadeia (Esc termina; a opção «Cadeia» desligada faz um
  arco só). Escolher «Linha» na barra a meio da cadeia continua-a a direito, e voltar ao «Arco tangente» continua-a
  em arco, como no Revit. Com a parede desenhada pela face, o eixo do arco sai do eixo da parede.
- Limite: o arco e a parede reta que se tocam ficam tangentes mas não ligados — mover uma depois não arrasta a outra.

## 0.453.0 — 2026-11-07

**Cadeia e Raio na barra, como no Revit.**

- **Parede ▸ Forma ▸ Linha**: duas opções novas na barra de parâmetros.
  - **Raio dos cantos**: com um valor maior que zero, cada canto da cadeia sai arredondado com esse raio enquanto se
    desenha (uma parede curva tangente entre as duas, do mesmo tipo); ao fechar a cadeia no 1.º ponto, também esse
    canto. Se o raio não cabe nos troços, o canto fica vivo e a mensagem diz porquê.
  - **Cadeia** (ligada por omissão): desligada, cada parede começa num clique novo, em vez de continuar da ponta
    da anterior.
- **Linha ▸ Desenhar**: a mesma **Cadeia** — desligada, cada linha (ou arco) fica sozinha e a próxima começa num
  clique novo.
- Limite: o Raio ainda não existe na Linha (use o Arco de concordância depois de desenhar).

## 0.452.0 — 2026-11-07

**Arco de concordância entre dois elementos, como o «Fillet Arc» do Revit** (o dono: «o arco por seleção de 2
elementos»).

- **Parede ▸ Forma ▸ Arco de concordância** (ícone novo): clique numa parede, depois noutra (do lado que fica de cada
  uma); o arco tangente às duas segue o rato, com o raio escrito ao lado; um clique cria-o (ou escreva o raio e
  Enter). As duas paredes são aparadas ou estendidas até ao arco e a parede curva fica entre elas, do tipo escolhido
  na barra, sem junta em planta.
- **Linha ▸ Desenhar ▸ Arco de concordância**: o mesmo para duas linhas soltas (o canto que partilhavam é separado);
  um só passo de desfazer.
- Recusado, com a razão, quando as duas são paralelas ou o raio é maior do que os troços.
- Limite: a parede curva toca as duas paredes nas pontas, tangente, mas não fica «ligada» a elas — se mover uma das
  paredes depois, o arco não vai atrás.

## 0.451.0 — 2026-11-07

**Escolher linhas e Afastamento, como no Revit** (o dono: «criar por seleção… criar com offset a x distância»).

- **Parede ▸ Forma ▸ Escolher linhas** (ícone novo): um clique numa linha, numa aresta de qualquer elemento (a face
  de uma parede em planta, o lado de uma laje), num eixo da grelha ou numa linha de um desenho cria a parede sobre
  ela, a todo o comprimento; a linha escolhida acende a azul e a parede aparece antes do clique. Com a referência
  pela face, o corpo da parede fica do lado do rato.
- **Afastamento** na barra da Parede (formas Linha e Escolher linhas): a parede fica a essa distância da linha
  desenhada (à esquerda do sentido do desenho; um valor negativo, à direita) ou da linha escolhida (do lado do rato).
- **Linha ▸ Desenhar ▸ Escolher linhas**: uma linha sobre a linha ou aresta escolhida, com o seu Afastamento.
- O estudo do painel «Desenhar» do Revit e o que falta ficou no PLANO.md (secção própria, 5 passos).

## 0.450.0 — 2026-11-07

**As formas de desenho em ícones na barra de parâmetros, como o painel «Desenhar» do Revit** (o dono, com capturas:
«no Revit quando ativar comando de parede, piso, linha… aparece essas opções que permite desenhar em retângulo,
arco etc. … poderia ser em ícones para ocupar menos espaços»).

- A escolha da forma de cada comando de desenho passou de lista a **fila de ícones** na barra de parâmetros, com a
  forma em uso acesa e o nome na dica:
  - **Parede**: linha, retângulo, arco, círculo, por face, varinha mágica;
  - **Laje**: retângulo, polígono, círculo, varinha mágica; **Cobertura**: varinha, retângulo, polígono, por face,
    blocos; **Teto** e **Piso**: varinha, retângulo, polígono;
  - **Lote**: retângulo, polígono, terreno; **Plataforma**: retângulo, polígono;
  - **Desenho 2D**: linha, polilinha, retângulo, círculo, arco, região, **máscara**, texto, cota de nível, nível,
    nota-chave.
- **Linha, Retângulo, Círculo, Arco, Bézier e Linha livre** têm a mesma fila «Desenhar» (com «Linha com arcos»):
  um clique noutro ícone passa para essa ferramenta. O Arco mostra ainda os seus modos em ícones.
- **Máscara** (nova, como a «Masking Region» do Revit): uma região branca que esconde o que está por baixo. No papel
  (PDF e SVG) não tem contorno; no ecrã o contorno fica ténue, para a poder escolher; no DXF não sai. Também está na
  lista «Trama» das regiões.
- Na fita, Arquitetura ▸ Paredes deixou de ter os botões Retangular, Circular, Arco, Por face e Varinha mágica (estão
  na barra; os atalhos W + letra continuam).

## 0.449.0 — 2026-11-07

**Alinhar com linhas, pisos e qualquer elemento** (o dono, com captura: «o comando alinhar precisa melhorar e deve
funcionar com linhas, pisos, e qualquer elementos no projeto»).

- **Referência** (1.º clique): um eixo da grelha, uma linha, qualquer aresta, a face de uma parede — ou, clicando
  dentro de um elemento (uma laje, um piso, um móvel…), a aresta dele mais perto do rato.
- **O que se alinha** (2.º clique), paralelo à referência: uma linha, a aresta de um piso, de uma laje, de uma
  cobertura ou de qualquer elemento, a face de uma parede ou de um pilar; clicando dentro de um elemento, a aresta
  dele paralela à referência mais perto do rato. A aresta acende a laranja e a dica diz quanto se vai mover.
- Uma **linha solta** move-se sozinha e as linhas ligadas a ela esticam (como no Revit); uma **porta ou janela**
  desliza ao longo da parede; qualquer outro elemento move-se inteiro (as paredes ligadas acompanham, como antes).
- Corrigido: com o rato no meio ou na ponta de uma linha (o snap «ponto médio» / «extremidade»), a linha não era
  aceite — agora vale a linha onde o ponto está.
- As linhas dos padrões (azulejos, tijolo) continuam a alinhar-se como na 0.332.

## 0.448.0 — 2026-11-07

**Snap a 0°, 45°, 90° e paralelo às paredes e linhas** (o dono: «no desenho deve ter snap a 0, 45, 90 grau. Se
desenhar uma linha ou construir uma parede a 30º, quando desenhar outra parede inclinada na mesma direção, ele faz o
snap de paralelo assim a nova parede é desenhada com segurança na mesma direção»).

- A desenhar paredes e linhas em planta (num plano horizontal), a direção prende-se sozinha, até 2,5° de desvio:
  - a cada 45°: 0°, 45°, 90°, 135°… (na horizontal e na vertical com o símbolo ↔ / ↕; nas diagonais ∠, «A 45°»);
  - **paralela a qualquer parede ou linha** que esteja até 20 m dali: a nova fica exatamente na mesma direção, com o
    símbolo ∥, a dica «Paralela» e a parede ou linha de referência acesa a azul.
- Fica o que estiver mais perto da direção do rato. Um snap a um ponto (ponta, meio, aresta…) continua a ganhar.
- **Shift** solta a direção (para desenhar a 31° de propósito).
- Vale também para Mover e Rodar, que usam o mesmo cálculo do ponto.

## 0.447.0 — 2026-11-07

**Mais do Revit no desenho** (o dono: «Sim, segue», sobre o que faltava das capturas).

- **Ao desenhar uma parede**, a distância até à parede paralela mais próxima de cada lado (que a acompanhe no
  comprimento), como no Revit: de eixo a eixo, ou de face a face quando as cotas das paredes estão «Face a face».
  Só se olha para as paredes até 20 m dali (não se percorre o modelo inteiro a cada movimento do rato).
- **Parede escolhida**: as setas ⇆ para a virar, ao meio, do lado de fora (a face onde as camadas começam), como no
  Revit. Um clique no losango do meio vira a parede (as camadas trocam de face; Ctrl+Z desfaz). O «+» das pontas
  continua.
- **Tornar a cota permanente**: nas plantas e nos cortes, cada cota temporária da parede escolhida tem por baixo do
  valor o pequeno ícone vermelho ├┤ do Revit. Um clique põe na vista uma cota permanente igual, presa às paredes que
  mede — acompanha-as quando mudam.
- Do que as capturas mostram, fica por fazer arrastar as pontas da parede pelos pontos azuis (o Revit tem-nos; aqui
  as pontas têm o «+» para continuar a desenhar).

## 0.446.0 — 2026-11-07

**Desenhar como no Revit** (o dono, com 13 capturas do Revit: «quero ter essa experiência no desenho como a do
revit»).

- **A parede em planta**, enquanto se desenha: o contorno a cinzento (sem volume azul) e a linha de localização a
  tracejado azul-petróleo, a prolongar-se para lá das duas pontas.
- **Cotas temporárias** como as do Revit: linhas finas azul-acinzentadas com um pequeno × em cada ponta e as linhas
  de chamada, o valor a laranja ao lado da linha (do lado de fora), sem caixa e sem a unidade. A caixa azul só
  aparece na cota sob o rato ou quando se escreve por cima. Clicar no valor ou no meio da linha deixa escrever.
- **Ângulo**: um arco largo (do tamanho de quase toda a parede no ecrã) a partir de uma linha de referência
  cinzenta na horizontal, com × nas pontas e o valor com duas casas («135,00°») escrito ao longo do arco. Aparece
  também a 90°; na horizontal não.
- **Snaps com os símbolos do Revit**, a magenta, em vez dos pontos coloridos: □ ponta, △ meio, × interseção,
  ⧗ mais próximo (numa aresta), ⊥ perpendicular, ∥ paralelo, ↔ / ↕ horizontal / vertical, ○ centro. A aresta da
  parede onde o rato se prende acende a azul. As linhas de alinhamento ficam a tracejado azul-petróleo. A dica com
  o nome do snap continua.
- Vale para todas as ferramentas que desenham (parede, linha…), no ecrã claro e nas vistas escuras.
- O aspeto anterior (o do addon, 0.372) continua: botão **Tema** do cabeçalho ▸ «Desenho como no addon ArqSynth».
  A escolha fica guardada.

## 0.445.0 — 2026-11-07

**Botão do nível de detalhe no rodapé, como no Revit** (o dono: «um botão rápido para escolher o nível de
visualização como do Revit»).

- No rodapé, ao lado da escala, um botão com o nível de detalhe da vista: **Grosso** (paredes cheias), **Médio**
  (a trama do material) e **Fino** (as camadas). O ícone mostra o nível em que a vista está.
- Serve nas plantas, nos cortes e nos alçados (na vista 3D fica apagado). Quando a vista tem um modelo de vista, o
  nível é o do modelo e o botão fica apagado, como a escala.
- É o mesmo que «Nível de detalhe» nas Propriedades da vista (um passo de desfazer).

## 0.444.0 — 2026-11-07

**O reboco contorna as pontas livres e as ombreiras dos vãos** (o dono, com capturas: «quando há furo, ou uma
janela que não tem aro largo, ou uma porta de correr com caixilho de alumínio, o reboco precisa contornar; na
parede com extremidade livre, o reboco precisa contornar»).

- Em planta, com o nível de detalhe Fino, o acabamento de cada face da parede (a camada de fora, quando não é o
  núcleo) dá a volta, com a sua espessura, onde a parede acaba à vista: numa ponta livre, nas ombreiras de um furo,
  e nas ombreiras das janelas e portas cujo caixilho é mais estreito do que a parede — aí entra até ao caixilho.
  Como o «Wrapping» do Revit, nas pontas e nos vãos.
- Onde o aro de uma porta, outra parede ou um pilar tapa a ombreira, o reboco não entra (as portas com aro largo
  ficam como estavam).
- Num piso com 1100 elementos e 1200 ombreiras, o corte fica cerca de 20 % mais lento (1,9 → 2,3 s).
- De passagem: o fecho de fendas da 0.442 podia, num caso raro (visto numa parede em L rodada com o reboco a
  contornar), deixar um polígono cruzado e o desenho falhava com um erro de geometria; agora a geometria é
  consertada e, se a junção falhar, faz-se sem a grelha — o desenho segue sempre.

## 0.443.0 — 2026-11-07

**O reboco dá a volta à esquina onde a sala fecha** (o dono: «Sim, corrige», sobre o que a 0.442 encontrou).

- Numa sala desenhada de seguida e muito rodada (45°, 72°…), na esquina onde a cadeia de paredes fecha, o reboco
  exterior parava antes da esquina e o bloco chegava à face de fora.
- A causa era da mesma família da 0.442: as camadas da primeira parede, recortadas na outra ponta dela, ficavam a
  um fio umas das outras; a esquina só apanhava a camada encostada à outra parede (o reboco de dentro).
- Agora a esquina apanha também as camadas que tocam nessa, e assim por diante: a meia-esquadria é feita na parede
  inteira. Em 390 salas rodadas ao acaso, nenhum reboco ficou aberto; o tempo do corte não muda.

## 0.442.0 — 2026-11-07

**Sem linhas a mais nas esquinas das paredes** (o dono, com captura: «linhas invasoras na junção das paredes à
medida que desenho e insiro elementos»).

- Em planta (no ecrã, no PDF, no SVG e no DXF), numa esquina de duas paredes um pouco fora do esquadro aparecia às
  vezes o traço grosso do corte ao longo da meia-esquadria, da esquina de fora até ao fim do bloco, ou um traço
  curto a atravessar a parede. Os blocos das duas paredes são calculados cada um por si e arredondados a 0,001 mm;
  numa junta inclinada as duas pontas caíam em casas diferentes do arredondamento e ficava uma fenda de 0,001 mm
  entre eles, que o contorno seguia. Como dependia dos números exatos, aparecia e desaparecia ao desenhar ou pôr
  portas e janelas.
- Agora, ao juntar cada material, as fendas com menos de 0,04 mm fecham-se: um só bloco, uma só linha à volta.
- Numa varredura de esquinas em L e de salas fechadas (ângulos de 0° a 90°, sítios e medidas ao acaso, com e sem
  portas e janelas) a linha aparecia em 33 de 242 casos; agora em nenhum. O corte de um piso com 1100 elementos fica
  cerca de 5 % mais lento (2,9 → 3,05 s).

## 0.441.0 — 2026-11-06

**Ripado solto** (uma divisória ou um brise sem parede atrás), como o «Apoio: Livre» do ripado do addon.

- **Arquitetura ▸ Acabamentos ▸ Ripado solto**: desenha-se como uma parede, com um clique no início e outro no fim,
  ou escrevendo o comprimento.
- Na barra de cima ficam a altura e as ripas: sentido, largura, espessura, passo, moldura e ripas de fixação (por
  trás).
- Com as ripas na horizontal e sem moldura nem fixações, o ripado leva sozinho dois prumos por trás, para as segurar.
- Nas Propriedades mudam-se o comprimento (o início fica no sítio), a altura e as ripas. Movido, rodado ou
  espelhado, fica como foi posto.
- Entra na lista de corte (ripas, ripas de fixação e moldura). No IFC é um IfcBuildingElementProxy «Ripado», de
  madeira.

## 0.440.0 — 2026-11-06

**Mobiliário solto, com peças do próprio programa** (o dono: «Sim, peças próprias»).

- **Arquitetura ▸ Mobiliário ▸ Mobiliário solto**: escolha a peça na barra de cima, por divisão:
  - **Quarto**: cama de casal, cama de solteiro, mesa de cabeceira;
  - **Sala**: sofá de 2 e de 3 lugares, poltrona, mesa de centro, móvel de TV;
  - **Jantar**: mesa de jantar de 4 e de 6 lugares, cadeira;
  - **Escritório**: secretária, estante;
  - **Outros**: planta em vaso.
- A barra mostra a largura, a profundidade e a altura da peça (as dela, para começar), que se podem mudar.
  **R** roda um quarto de volta e **Espaço** muda o ponto que fica no clique (o meio, o meio da frente, um canto…),
  como nos pilares. Um clique põe a peça.
- Cada peça é feita de partes com o seu material e a sua cor: madeira, tecido do estofo, tecido claro dos colchões e
  almofadas, terracota do vaso, folhagem. Esticada, refaz-se nas medidas novas (as pernas não engrossam).
- Nas Propriedades, a peça está no topo, como um tipo: escolher outra troca a peça, com as medidas dela. Por baixo,
  a largura, a profundidade e a altura.
- No IFC é um IfcFurniture do seu tipo (BED, SOFA, CHAIR, TABLE, DESK, SHELF, ou USERDEFINED com o nome, como a mesa
  de cabeceira), com as medidas nominais e «não embutido».
- **No Verificador**, as camas e os sofás contam, e a cama de casal conta como cama de casal.

## 0.439.0 — 2026-11-06

**Elevador com portas de patamar e lajes abertas sozinhas.**

- Em cada piso, da base do elevador para cima, a caixa tem agora a parede da frente com a **porta de patamar**: duas
  folhas de correr fechadas, com até 0,90 m de largura e 2,10 m de altura, a cinzento (aço).
- As **lajes** que a caixa atravessa (acima do fundo dela) ficam **abertas à volta da caixa** quando se põe o elevador.
  A laje do piso de baixo, onde o elevador assenta, não se abre.
- Nas propriedades do elevador ficam o número de patamares e a largura da porta.

## 0.438.0 — 2026-11-06

**Calha em meia-cana e tubos de queda.**

- Na ferramenta **Calha** (Arquitetura ▸ Pisos e coberturas), a barra de cima tem agora:
  - **Secção**: **Caixa (U)**, como até aqui, ou **Meia-cana** (redonda, aberta em cima);
  - **Tubos de queda**: nenhum, no início, no fim ou nas duas pontas.
- Os tubos de queda são redondos, de 8 cm, de alumínio. Ficam por baixo da calha, a 15 cm da ponta, e descem até ao
  chão (o nível do pavimento mais baixo). No IFC são IfcPipeSegment.
- Nas Propriedades de uma calha também se mudam a secção e os tubos de queda.
- Apagar a calha apaga os seus tubos de queda.

## 0.437.0 — 2026-11-06

**Estrutura leve das paredes (Steel frame e Wood frame)**, como no addon.

- Nas Propriedades de uma parede há um grupo novo, **Estrutura leve**. Em **Estrutura**, escolha **Steel frame (aço
  leve)** ou **Wood frame (madeira)**.
- A estrutura fica dentro do núcleo da parede (a camada com a função Estrutura no tipo, ou a mais grossa):
  - **guias** em baixo e em cima (a de baixo cortada nas portas);
  - **montantes** ao espaçamento, contado do início da parede, e um em cada ponta;
  - **ombreiras** de cada lado de cada porta e janela, uma **verga** por cima e, nas janelas, um **peitoril** por baixo;
  - **montantes curtos** por cima das vergas e por baixo dos peitoris, onde estariam os montantes;
  - **travamentos** em filas, entre os montantes, sem atravessar as aberturas.
- Por omissão: aço com montantes de 4 cm a 60 cm e guias de 4 cm; madeira com 4,5 cm a 40 cm. O espaçamento e o número
  de filas de travamentos mudam-se nas Propriedades, que mostram também quantas peças há de cada e os metros.
- A estrutura refaz-se sozinha quando a parede muda: mais comprida, mais alta, com uma porta ou janela nova ou mudada
  de sítio. Uma cópia da parede leva a sua própria estrutura; apagar a parede apaga a estrutura.
- No IFC, é um IfcElementAssembly «Estrutura leve» com as peças em IfcMember (guias PLATE, montantes STUD, vergas,
  peitoris e travamentos), de aço galvanizado ou madeira, com o comprimento e o volume de cada uma.
- A parede continua igual (as placas e o isolamento são as camadas dela). Para ver a estrutura, esconda as paredes em
  **Visibilidade…** (Propriedades da vista).

## 0.436.0 — 2026-11-06

**Fachada de vidro em arco e por face**, como no addon. Na ferramenta **Parede cortina**, a barra de cima tem agora
**Forma**:

- **Linha**: como sempre, dois cliques.
- **Arco (3 cliques)**: clique no início, no fim e num ponto por onde o arco passa, como no arco da Parede. Não precisa
  de estar numa parede curva. Também se pode escrever a corda e depois o raio.
- **Por face**: passe o rato por uma face de pé de um volume (um esboço feito com o Empurrar/Puxar) ou de uma parede.
  Aparece o retângulo da fachada com os montantes e as travessas. Um clique põe a fachada por fora dessa face, com o
  comprimento e a altura dela (as faces ao lado no mesmo plano contam juntas).

**Corrigido:** desde a 0.433, mudar nas Propriedades o raio ou o ângulo de um arco, ou fazer o madeiramento de uma
cobertura, dava um erro interno e a mudança ficava a meio. A causa era uma linha da 0.433 (o declive das lajes).

## 0.435.0 — 2026-11-06

**Escadas prontas a colocar**, como o «Gerar escada» do addon: a escada inteira presa ao rato, posta com um clique.

- Na ferramenta **Escada**, escolha **Colocar ▸ Pronta (um clique)** na barra de cima.
- Ao passar o rato, a escada aparece toda (reta, em L, em U, em V ou circular, com a largura, o cobertor e a altura
  da barra), com uma seta no sentido em que sobe.
- **R** e **Shift+R** rodam a escada um quarto de volta, como num pilar.
- **Espaço** e **Shift+Espaço** escolhem o ponto do 1.º degrau que fica no ponto clicado: o meio, o canto de fora ou
  o canto de dentro (o lado para onde a escada vira).
- O ângulo e o ponto também estão na barra.
- **Pé e sentido (dois cliques)** continua a ser a forma de sempre.

**Corrigido:** desde a 0.432, depois de mudar um valor na edição rápida (TAB) e fechá-la, o TAB seguinte já não a
abria nem fechava. A causa era a limpeza do botão «Editar tipo…» no topo, que tocava num campo já apagado.

## 0.434.0 — 2026-11-06

**Ripado como ferramenta própria**, como no addon: **Arquitetura ▸ Acabamentos ▸ Ripado**, ao lado do Painel
perfurado.

- Passe o rato por uma parede: o ripado aparece na face, com as ripas desenhadas.
  - **Um clique** cobre a face inteira (toda a altura, e acompanha a parede).
  - **Arrastar** de um canto ao outro faz um ripado só nesse retângulo.
  - **Um clique num ripado** que já lá está escolhe-o, com as medidas nas Propriedades.
- Na barra de cima:
  - **Sentido**: ripas na vertical ou na horizontal;
  - **Largura da ripa**, **Espessura da ripa** e **Passo** (de eixo a eixo). Por omissão, ripas de 4 × 4 cm a 8 cm,
    como no addon;
  - **Moldura**: a largura da moldura à volta (0: sem moldura);
  - **Ripas de fixação**: quantas ripas por trás, atravessadas às ripas. As ripas ficam afastadas da parede pela
    espessura delas.
- As ripas ficam ao centro do espaço dentro da moldura, com as folgas das pontas iguais, e são cortadas nas portas e
  janelas.
- Nas Propriedades de um ripado há também a espessura da ripa, a moldura, as ripas de fixação e a largura e a espessura
  delas.
- A lista de corte e o DXF da CNC levam as ripas, as ripas de fixação e as peças da moldura.
- O ripado chama-se «Ripado 1», «Ripado 2»… (também o que se põe com Acabamento de parede ▸ Ripado).

## 0.433.0 — 2026-11-06

**Pisos com declive por canto**, como no addon: cada canto de uma laje pode ficar mais alto ou mais baixo do que o
topo dela. Serve para uma varanda ou um terraço que cai para o ralo, ou para uma rampa.

- Nas Propriedades de uma laje há um grupo novo, **Declive**, logo a seguir a «Restrições e dimensões»:
  - **Lado alto**: o lado que fica no topo da laje;
  - **Declive (%)**: escreva, por exemplo, 2 e carregue em Enter. A laje cai 2 cm por metro a partir do lado alto;
  - **Canto 1, Canto 2…**: a altura de cada canto acima do topo (ou abaixo, com −). As setas ↑ ↓ sobem ou descem 1 cm,
    como nos outros campos de medidas;
  - **Pôr plana**: volta a ser uma laje plana.
- A face de baixo acompanha o declive, sempre com a espessura do tipo. Os furos ficam no declive.
- Ao mexer no contorno, os cantos que já existiam guardam a sua altura; um canto novo fica à altura do declive nesse
  sítio. Mudar o tipo da laje, espelhá-la, gravar e abrir o ficheiro: o declive fica.
- Uma laje retangular com declive passa a polígono (os cantos passam a ser dela). Uma laje circular não tem cantos.
- No IFC, uma laje com declive leva um corpo de triângulos fechado (IfcTriangulatedFaceSet), com a área, o volume e a
  espessura certos nas quantidades.
- No MCP, «create» de uma laje aceita `heights` (a altura de cada canto, em metros).

## 0.432.0 — 2026-11-06

**«W + letra» — os comandos das paredes por uma segunda letra**, como no addon.

- Carregue em **W**: entra a ferramenta Parede, como sempre, e a faixa mostra as letras. Durante 1,25 s, uma segunda
  letra escolhe um comando das paredes:
  - **T** e **E**: Aparar e estender;
  - **A**: Alinhar;
  - **O**: Ortogonalizar;
  - **R**: Rodar;
  - **S**: Dividir parede;
  - **M**: Espelhar;
  - **J** e **C**: Junções de paredes;
  - **U** e **B**: Ligar o topo e Ligar a base;
  - **G**: Selecionar, para as pegas;
  - **L**: escolhe as paredes ligadas às escolhidas, e as ligadas a essas (novo);
  - **Q**: Edição rápida.
- Fora desse tempo, as letras são os atalhos de sempre: T continua a ser a Fita métrica.
- Outra tecla pelo meio (Esc, F1…) acaba com a espera: W, Esc, R é o Retângulo, não Rodar.

**«Editar tipo…» por baixo da lista de tipos**, no topo das Propriedades, como o «Edit Type» do Revit (pedido do
dono). Deixa de ser uma linha «Tipo» no grupo Identificação.

- Vale para paredes, lajes, coberturas, portas e janelas, guardas e cotas.
- Nos elementos com «Guardar como tipo…» e «Atualizar o tipo» (superfícies, móveis, luminárias…), estes dois botões
  também passam para baixo da lista.
- Com vários elementos escolhidos, os botões não aparecem: editam o tipo de um elemento só.

**Avisos do modelo** (Aprender com o Hestia, passo 5): o que está mal desenhado, não o que a lei pede. Estes são os
avisos mais comuns do Revit.

- **Os avisos:**
  - **Paredes sobrepostas**: duas paredes desenhadas uma por cima da outra, a partilhar mais do que um canto. Diz a
    área sobreposta.
  - **Elemento repetido no mesmo sítio**: uma cópia que ficou por cima de outra igual (paredes, lajes, pilares, vigas,
    portas, janelas, móveis, louças…).
  - **Ambiente não fechado pelas paredes**: uma parede de fora foi apagada e o ambiente ficou aberto.
  - **Vários ambientes no mesmo espaço fechado**: a parede entre dois ambientes foi apagada.
- **Entram no Verificador como mais um pacote, «Modelo», sempre ligado em qualquer país.**
  - Contam no rodapé como avisos (⚠) e aparecem na faixa laranja, com «Ir para» e «Porquê».
  - No painel Verificação ficam em «Modelo — Avisos do modelo».
  - Aceitam «Exceção…» com uma nota (o «Ignorar, com nota» do plano) e vão para a ficha de verificação.
- A frase destes avisos diz o que é e quanto: «Parede 1: Paredes sobrepostas (0,60 m²)».
- Desligam-se em Regulamentos do projeto ▸ **Avisos do modelo**.
- Uma varanda, um terraço ou um pátio (ambientes exteriores) não precisam de estar fechados.

**Propriedades mais rápidas** (Aprender com o Hestia, passo 4).

- **Contas nos campos de medidas**: «3,50+0,15», «2*1,20» (ou «2×1,20»), «(4-0,2)/2», «3m+15cm». Cada número está na sua
  unidade, ou na unidade do rodapé, e o resultado também. Vale nas Propriedades, nos dados IFC e na caixa das Medidas.
  Duas setas seguidas («--1») continuam a ser um engano, não uma conta.
- **Setas ↑ ↓ nos comprimentos das Propriedades**: sobem ou descem 1 cm (Shift: 10 cm; Ctrl: 1 mm). A **roda do rato**
  faz o mesmo enquanto o campo tem o cursor; fora dele, a roda continua a deslizar o painel. **Enter** aplica, num só
  Ctrl+Z.
- **O selo «tipo»** ao lado dos valores que vêm do tipo (a espessura de uma parede, de uma laje, de uma cobertura; o
  tamanho de uma sapata). Clicar nele abre esse tipo no editor de tipos.
- **«↺» nos dados IFC**: quando o elemento tem um valor seu (por exemplo a resistência ao fogo) e o tipo também tem um,
  aparece «↺» ao lado. Clicar nele apaga o valor do elemento e volta ao do tipo. A dica diz qual é o valor do tipo.

**Editar tipo com o corte ao vivo** (Aprender com o Hestia, passo 3).

- **O corte das camadas desenhado no editor de tipos** (paredes, lajes, coberturas). Muda enquanto se escreve, antes de
  aplicar:
  - cada camada na cor do seu material onde é cortado (clareada para o papel), com a trama se o material a tiver;
  - as linhas entre as camadas finas e o contorno grosso;
  - o **núcleo** marcado a vermelho: as camadas com a função Estrutura (ou Suporte), senão a mais grossa;
  - a espessura de cada camada onde cabe, e o total;
  - numa parede, «Exterior» à esquerda e «Interior» à direita; numa laje, o topo em cima.
- **OK / Cancelar / Aplicar**, como no Revit:
  - **OK** aplica o que mudou (um Ctrl+Z) e fecha;
  - **Cancelar** fecha e deixa o que não foi aplicado;
  - **Aplicar** aplica sem fechar.
- **Onde se usa**: escolhe na vista todos os elementos do tipo e enquadra-os.
- **Apagar um tipo em uso**: o programa pergunta por que tipo substituir os elementos. Eles passam a esse tipo e o
  tipo antigo é apagado, tudo num só Ctrl+Z. Antes, só se apagavam tipos sem elementos.

**As paredes em planta no ecrã com as canetas do papel** (Aprender com o Hestia, passo 2).

- **Num corte, no ecrã**, cada tipo de linha tem a sua caneta, como no PDF:
  - o **contorno do que é cortado** usa a caneta de corte (0,50 mm);
  - as **linhas entre as camadas** (reboco e bloco) e a **trama** usam a caneta da trama (0,10 mm).
- **As canetas seguem o zoom.** Os mm de papel passam a píxeis pela escala da vista e pelo zoom:
  - de longe, o corte tem 2 píxeis e as camadas 1 píxel;
  - aproximando, o corte engrossa até 6 píxeis e as camadas continuam finas.

  As canetas são as dos Estilos gráficos do projeto.
- **De longe, a trama sai.** Quando um milímetro de papel tem menos de 2 píxeis, deixa de se desenhar (era uma mancha
  cinzenta); com menos de 1 píxel saem também as linhas das camadas. A parede fica desenhada pelo contorno, como num
  desenho impresso pequeno. Aproximando, voltam.
- **Visualizar ▸ Linhas finas**: todas as linhas do corte com 1 píxel, seja qual for o zoom, para desenhar com rigor (como
  as «Thin Lines» do Revit). Só muda o ecrã: o papel e o PDF mantêm as canetas. O programa lembra-se da escolha.

**Arrastar para mover** (Aprender com o Hestia, passo 1 — «gostei de poder simplesmente selecionar e pegar qualquer
elemento e arrastar para reposicionar»).

- **Com o Selecionar, carregue num elemento — escolhido ou não — e arraste:** ele vai com o rato, na planta e no 3D.
  Por baixo é o trabalho do Mover:
  - o ponto agarrado e o destino prendem-se aos snaps, e aparece o fantasma com a distância;
  - Shift prende a direção, e pode escrever a distância e carregar em Enter;
  - as paredes ligadas esticam para continuar ligadas;
  - uma porta ou janela desliza na sua parede, sem sair dela;
  - **Ctrl ao largar faz uma cópia**, e **Esc** deixa tudo onde estava;
  - um só Ctrl+Z desfaz.
- Se o elemento estava numa seleção de vários, vão todos; se faz parte de um grupo, vai a cópia do grupo.
- **A partir do vazio**, arrastar continua a fazer a caixa (ou o laço). Na planta, lajes, pisos, coberturas e terreno
  só se agarram pela borda: dentro deles, arrastar faz a caixa, para os poder selecionar por cima.
- **Arrastar elementos** (o ícone da parede com a seta, na barra da seleção, a seguir ao Laço livre; e em Editar ▸
  Seleção) liga e desliga isto. O programa lembra-se da escolha.
- **Corrigido:** a 0.426 tinha mudado o nome do painel «Regras gráficas» para «Editor de regulamentos». Um teste novo
  impede que os textos do Verificador voltem a trocar os do programa.

**O Verificador, passo 9 (2.ª parte): o editor de regulamentos.** Com isto fica feito o plano do Verificador.

- **Colaborar ▸ Verificação ▸ Editar regulamentos…** (e o botão com o mesmo nome nos Regulamentos do projeto):
  - à esquerda, os regulamentos por país (os do programa e os seus, marcados «seu»);
  - à direita, as regras do escolhido numa tabela: artigo, regra, medida, limite, gravidade, conferido, ativa.
- **O que se muda:**
  - o **limite**: um número, ou uma fórmula das medidas, como `max(5; altura_fachada / 2)`;
  - a **gravidade**: incumprimento, aviso ou nota;
  - **Conferido**: o valor foi confirmado no texto publicado; deixa de aparecer «a confirmar» na ficha e nas
    mensagens;
  - **Ativa**: desligar uma regra que não se aplica.

  Os limites dados por tabela (as áreas por tipologia) mudam-se no ficheiro.
- **Os regulamentos do programa nunca se alteram.** Ao gravar, a mudança fica numa cópia sua, na pasta «ArqSynth
  BIM/regulamentos» dos dados do utilizador, e essa cópia passa a valer em vez do original. **Repor o original** tira a
  cópia. **Duplicar** faz um regulamento novo a partir do escolhido.
- **Novo país…**: um código (AO), um nome (Angola) e o país de partida (Cabo Verde). Copia os regulamentos desse país,
  com todos os valores «a confirmar» e sem supletivos. O país novo aparece logo na lista dos Regulamentos do projeto.
- Depois de editar, o Verificador volta a verificar com os regulamentos novos, mesmo sem nada mudar no modelo.

**O Verificador, passo 9 (1.ª parte): a ficha de verificação.**

- **Colaborar ▸ Verificação ▸ Ficha de verificação…** (e o botão «Ficha…» no painel Verificação) grava a ficha para o
  processo de licenciamento, em **PDF** ou numa **folha de cálculo Excel (XLSX)**. Escolhe-se pelo tipo de ficheiro.
- **O que a ficha tem:**
  - o projeto e a data, o país, o uso do edifício, o tipo de obra, a altura;
  - os regulamentos (os do país e os supletivos que contaram);
  - o resumo (incumprimentos, avisos, exceções, a cumprir, por medir);
  - o lote e o plano municipal, com o que o projeto tem;
  - o **quadro de áreas**: cada fogo com a tipologia, os compartimentos com o uso e a área, a área útil e a bruta;
  - a **verificação regra a regra**, por regulamento e artigo: o exigido, o que o projeto tem, ✓ ✗ ⚠ — ou ✓* para uma
    exceção aceite;
  - as **exceções**, com a justificação e a data;
  - uma nota com os valores ainda por conferir com o texto publicado.
- **No PDF**, uma regra verificada em mais de seis sítios (cada parede…) mostra só o que falha, um a um, e o resto numa
  linha («mais 7 que cumprem»). O que não tinha nada a medir (nenhuma fachada em frente) também fica numa linha.
- **No XLSX**, quatro folhas («Resumo», «Quadro de áreas», «Verificação», «Exceções»), com todas as linhas para
  filtrar.

**O Verificador, passo 8 (2.ª parte): as alturas das fachadas e os afastamentos da lei.**

- **CTE de Cabo Verde, mais 6 regras:**
  - **art. 21.º n.º 1:** a altura de cada fachada não passa o afastamento à fachada oposta (H ≤ L). Mede-se do meio
    da face exterior de cada parede exterior, a direito para fora, até à primeira parede ou fachada-cortina com
    2,20 m de altura ou mais. Um muro solto olha para os dois lados.
  - **art. 22.º n.º 1:** 11 m entre fachadas viradas à via pública. Só se mede com a fachada do outro lado da rua
    desenhada. Para um alinhamento preexistente a manter, usa-se Exceção….
  - **art. 22.º n.os 2 e 4:** as janelas de compartimentos habitáveis ficam a metade da altura da fachada, e a 5 m no
    mínimo, do lote vizinho (a estrema que está à frente delas, quando não é a via pública).
  - **art. 22.º n.º 3:** as janelas de compartimentos não habitáveis ficam a 1,50 m do lote vizinho.
  - **art. 23.º n.º 1 a):** um pátio interior deixa inscrever um círculo de metade da altura da fachada mais alta,
    com 4 m no mínimo.
  - **art. 24.º n.º 2:** o que sai sobre a via pública (uma varanda, uma pala para lá da frente do lote) fica com a face
    de baixo a 3 m do chão.
- **RGEU, mais 4 regras:**
  - art. 59.º: a linha a 45° desde a fachada fronteira;
  - art. 60.º: 10 m entre fachadas com janelas de habitação;
  - art. 62.º § 2.º: o logradouro da habitação multifamiliar, com metade da altura da fachada e 6 m no mínimo de
    fundo, e 40 m² livres.

  Em Cabo Verde não entram, porque o CTE trata os mesmos temas (arts. 21.º e 22.º).
- **Novo uso de ambiente: Pátio** (pelo nome «Pátio», «Saguão», «Logradouro»). É exterior: não conta na implantação.
- **A verificação já não prende a janela:** corre aos bocados de 40 ms entre os cliques. Num edifício de 2161
  elementos demora cerca de 1,1 s por edição, mas o programa continua a responder enquanto isso.
- **Corrigido:** o Verificador podia dar a um documento novo a leitura de um antigo, quando o Python lhe dava a mesma
  identidade e o mesmo número de revisão. Apareceu na bateria completa de testes. Agora a leitura guarda-se com o
  próprio documento e o seu IFC.

**O Verificador, passo 8 (1.ª parte): o lote e o plano municipal.**

- **Ferramenta Lote** (Terreno ▸ Lote): o lote em planta, como a «linha de propriedade» do Revit — um retângulo (dois
  cantos, ou as medidas escritas «20;30»), um polígono (canto a canto; Enter ou um clique no primeiro fecha) ou o
  contorno do terreno (um clique). Um lote por projeto: desenhado outra vez, substitui o que lá está. Fica no IFC como
  o contorno do terreno (`IfcSite`, representação «FootPrint»), que os outros programas leem.
- **Na planta**, o lote aparece a traço-ponto-ponto, com o número de cada estrema e «via pública» do lado da frente (mais
  grosso). «Enquadrar tudo» (Shift+Z) mostra-o inteiro.
- **A frente para a via pública** escolhe-se nos Regulamentos do projeto; sem escolha, é a estrema mais perto da
  entrada do edifício. As outras estremas são laterais, e a que fica de costas para a frente é o fundo (posterior).
- **Regulamentos do projeto ▸ Lote e plano municipal**: o nome do plano (PDM, plano de pormenor, alvará de loteamento)
  e os seus valores para o lote:
  - área mínima do lote;
  - índices de ocupação, de utilização e de impermeabilização;
  - áreas de implantação e de construção máximas;
  - pisos acima e abaixo do solo;
  - cércea e altura máximas;
  - afastamentos mínimos frontal, lateral e posterior.

  O Verificador mede cada um no projeto e diz no rodapé o que falha, por exemplo «CTE, PDM da Praia ✗ 4». Só se
  verifica o que tiver valor. Ao lado de cada campo, ao passar o rato, aparece o valor que o projeto tem agora.
- **Sempre, com um lote desenhado:** nada do edifício pode ficar fora do lote.
- **Como se mede:**
  - **Implantação:** as paredes e pilares do rés-do-chão e dos pisos de cima, com o que fecham, menos os ambientes
    exteriores (um pátio fechado conta até ter um ambiente exterior).
  - **Construção:** a soma desses pisos.
  - **Cércea:** do chão ao alto das paredes, guardas e fachadas-cortina da fachada. Não conta um telhado inclinado
    acima do beirado.
  - **Altura:** até ao ponto mais alto.
  - **Afastamentos:** contam também as varandas dos pisos de cima (CTE art. 22.º n.º 4).
  - **Chão:** o piso mais perto da cota 0; os que estão abaixo dele são caves.

**O Verificador, passo 7: os materiais e as boas práticas.**

- **O que é cada material**, pelo nome (`verify/materials.py`): «Placa de gesso cartonado hidrófugo 12,5 mm» é gesso
  cartonado e hidrófugo; reconhece alumínio, cobre, zinco, aço galvanizado, aço, poliestireno (EPS/XPS), betume,
  membranas, argamassa de cimento, cal, alvenaria antiga e corrente, madeira, alcatifa e isolantes. Em português e
  inglês, sem contar acentos nem maiúsculas.
- **CTE de Cabo Verde, mais 3 regras:**
  - art. 92.º n.º 3: o pano exterior das paredes exteriores duplas de alvenaria com 0,15 m em tosco;
  - art. 98.º: pavimentos estanques nas instalações sanitárias, cozinhas e lavandarias (aviso — madeira ou alcatifa);
  - art. 99.º n.º 1 a): a laje sobre o terreno com uma camada estanque contra a humidade (aviso).
- **Boas práticas** (`regulamentos/_geral/boas_praticas.json`, um pacote para qualquer país, só avisos e **nunca nos
  temas que a lei do projeto já trata**):
  - gesso cartonado normal num local húmido (pede o hidrófugo, do lado do local húmido);
  - metais em contacto que corroem (alumínio, zinco ou galvanizado com cobre; alumínio com aço), nas paredes, lajes e
    coberturas — duas camadas encostadas no mesmo tipo;
  - poliestireno encostado a betume;
  - argamassa de cimento contra alvenaria antiga ou de cal, nas obras de reabilitação;
  - o conforto da escada pela regra de Blondel (2 espelhos + 1 cobertor entre 0,60 e 0,65 m).
- **Ligar e desligar as boas práticas** nos Regulamentos do projeto (Colaborar ▸ Verificação ▸ Regulamentos).
- **Mais rápido:** num edifício de 2161 elementos e 72 ambientes, cada edição verifica-se em cerca de 0,6 s (era 2,5 s
  na primeira versão destas regras): as paredes à volta, os vãos e o que está em frente das janelas procuram-se só
  perto de cada coisa, e o que se mede uma vez fica guardado até ao fim da verificação.

**O Verificador, passo 6: Portugal — o RGEU e as acessibilidades (DL 163/2006).**

- **RGEU** (`regulamentos/PT/rgeu.json`, 19 regras, lido no texto da Ordem dos Arquitectos e no consolidado da PGD
  Lisboa — continua em vigor; a revogação foi adiada pelo DL 108/2026):
  - pé-direito (art. 65.º): 2,40 m livres na habitação em 80 % do teto, 2,20 m em vestíbulos, corredores,
    instalações sanitárias, despensas e arrecadações e na superfície restante, 3 m no comércio;
  - quadro do art. 66.º: sala (T0–T1 10 m², T2–T4 12, T5–T6 16), cozinha 6 m², quartos do maior para o menor (10,5
    e 9, e 6,5 nos simples), sala + cozinha + suplemento de área obrigatório;
  - área bruta (art. 67.º): T0 35, T1 52, T2 72, T3 91, T4 105, T5 122, T6 134 m²;
  - instalações sanitárias (art. 68.º): 3,5 m² até T2, 4,5 m² em dois espaços no T3–T4, 6 m² em dois espaços a
    partir do T5;
  - dimensões (art. 69.º): 2,10 m abaixo de 9,5 m², um círculo de 2,40 m entre 9,5 e 12 m², de 2,70 m a partir de 12
    m², 1,70 m na cozinha;
  - vãos (art. 71.º): pelo menos um para o exterior e 1/10 da área do compartimento, 1,08 m² no mínimo, **medidos no
    tosco** (a largura × a altura do vão — não o vidro, como no CTE);
  - ventilação transversal (art. 72.º, aviso) e afastamento a muros e fachadas (art. 73.º).
- **DL 163/2006, normas técnicas** (`regulamentos/PT/dl163_2006.json`, 16 regras): **portas com 0,77 m úteis**
  (a folha aberta a 90°) e 2,00 m de altura; escadas comuns com 1,20 m, das habitações com 1,00 m, espelho até 0,18 m,
  cobertor de 0,28 m, patim a cada 2,40 m; rampas até **6 % para 0,60 m de desnível e 8 % para 0,40 m (com os valores
  intermédios)**, lanços de 10 a 5 m, largura de 1,20 m (0,90 m se curtas ou dentro da habitação); entrada da
  habitação e cozinha com rotação de 360° (Ø 1,50 m livre de móveis); corredores com 1,10 m; uma instalação sanitária
  com lavatório, sanita, **bidé** e banheira (ou base de duche).
- **Cabo Verde chama Portugal** (CTE art. 4.º): os dois pacotes portugueses entram como supletivos, mas só as regras de
  temas que o CTE não trata (por agora, a largura das rampas dentro das habitações). Novo no CTE: a ventilação por
  fachadas de orientação diferente (art. 76.º n.º 4, nota).
- Medidas novas: a área dos vãos no tosco, a área e o número das instalações sanitárias (e as que têm bidé), as
  janelas em fachadas opostas ou de orientação diferente. O bidé deixou de contar como sanita.
- Por fazer em Portugal: a térmica (REH, os U máximos pela zona climática) e a segurança contra incêndio (SCIE).

## 0.420.0 — 2026-11-06

**O Verificador, passo 5: iluminação e ventilação naturais, e o que está em frente das janelas** (CTE arts. 76.º e
77.º).

- **Cada compartimento habitável com um vão para o exterior** (art. 76.º n.º 1).
- **Área de vidro** das janelas e portas envidraçadas para o exterior de, pelo menos, **1/8 da área útil a até 6 m
  delas** (art. 76.º n.os 1 e 2). O vidro mede-se pelo desenho da caixilharia: as folhas de vidro (ou fosco), menos o
  aro, os montantes e o caixilho das folhas que abrem — uma janela 150×120 de correr dá 1,08 m²; uma porta de sacada
  140×220, 1,85 m².
- **Fundo do compartimento** a mais de 6 m de qualquer janela (aviso).
- **Instalações sanitárias e arrumos sem vão para o exterior:** uma nota (não conta como falha) a lembrar a extração
  de ar viciado obrigatória (art. 76.º n.º 6 b).
- **O que está em frente das janelas** (art. 77.º): numa faixa de 4 m (2 m de cada lado do eixo da janela), o muro, a
  fachada, o edifício vizinho ou o terreno que se levanta à frente tem de estar a mais de metade da sua altura acima do
  pavimento do compartimento, e a 3 m no mínimo. Sem nada à frente, cumpre.
- Por fazer: as horas de sol do compartimento maior (art. 78.º — o texto não diz em que dia do ano; a decidir com o
  dono) e a profundidade do compartimento face à fachada (art. 41.º a).

## 0.419.0 — 2026-11-06

**O Verificador, passo 4: escadas, rampas, guardas, circulação, a forma dos compartimentos, as instalações sanitárias
e os arrumos** (CTE de Cabo Verde, mais 20 regras; 34 ao todo).

- **Escadas** (art. 35.º): espelho até 0,18 m, cobertor de 0,28 m ou mais; largura 1,10 m numa escada da habitação,
  1,20 m numa de uso comum (1,40 m num edifício com mais de 28 m); desnível de cada lanço comum até 2,40 m; altura
  livre de 2,20 m por cima de cada degrau (medida até à laje ou viga de cima).
- **Rampas** de uso comum (art. 36.º): inclinação até 6 %, lanços até 6,00 m, largura de 1,00 m.
- **Guardas** em espaços comuns (art. 131.º): 0,90 m de altura.
- **Forma dos compartimentos** (art. 41.º): a sala tem de inscrever um círculo de 2,70 m; os quartos um quadrado de
  2,40 m (2,60 m a partir de 10,5 m²); a cozinha 2,10 m na dimensão menor e um círculo de 1,50 m livre de móveis.
- **Instalações sanitárias** (art. 43.º): no T0–T2, uma completa (sanita, lavatório e base de chuveiro ou banheira)
  com 3,00 m²; a partir do T3, duas; um círculo de 1,50 m livre das louças (aviso).
- **Entrada e circulação** (art. 44.º): o vestíbulo inscreve um círculo de 1,50 m; os corredores têm 1,10 m na parte
  mais estreita (0,90 m se tiverem até 1,50 m de comprido).
- **Arrumos** (art. 45.º, aviso): despensas, arrecadações e roupeiros do fogo — 1,50 m² no T0/T1, 2,50 m² no T2, 3,00 m²
  do T3 para cima.
- Uma escada, rampa ou guarda é «de uso comum» quando está num espaço comum, ou fora dos fogos num edifício que os
  tem; numa moradia é da habitação.
- As medidas novas: a largura mais estreita de um compartimento (onde ele «se parte em dois» ao encolher das paredes —
  apanha o gargalo de um corredor), o maior círculo e o maior quadrado inscritos, o círculo livre do que está no chão
  (louças, móveis, armários).

## 0.418.0 — 2026-11-06

**O Verificador, passo 3: o painel Verificação, as exceções e as outras verificações num só lugar.**

- **Colaborar ▸ Verificar ▸ Verificação** (ou o indicador do rodapé ▸ Abrir o painel de verificação): tudo o que o
  Verificador encontrou, **por fogo** (e «Edifício e espaços comuns») ou **por regulamento**, com o resultado e o
  artigo; o resumo em cima («CTE: 2 incumprimento(s), 0 aviso(s), 0 exceção(ões), 10 a cumprir, 8 por medir»).
- **Filtros:** incumprimentos e avisos, só incumprimentos, exceções, por medir, tudo.
- Um clique numa linha **leva ao sítio** (abre a planta, escolhe e enquadra); **Porquê** diz a regra, o medido, o
  exigido e a fonte; o botão direito tem os mesmos.
- **Exceção…**: aceitar uma falha com a razão escrita (por exemplo «vontade expressa do dono de obra», CTE art. 27.º
  n.º 7). Fica no projeto (IFC), sai da contagem do rodapé e da faixa vermelha, aparece no filtro «Exceções» com a
  razão — e irá para a ficha de verificação. **Tirar a exceção** desfaz; Ctrl+Z também.
- **Outras verificações ▾**: os conflitos entre disciplinas, o IFC para certificação, os requisitos IDS, a instalação
  elétrica e a estrutura (EC2 / EC6) a um clique, no mesmo painel.

## 0.417.0 — 2026-11-06

**O Verificador, passo 2: as regras, o vigilante e o alerta vermelho no rodapé.** (O dono: «se for inferior à
legislação, então o sistema coloca uma mensagem no rodapé com fundo vermelho de alerta».)

- **Regulamentos do projeto** (Colaborar ▸ Verificar ▸ Regulamentos do projeto…, ou um clique no indicador do
  rodapé): o país onde se constrói (Cabo Verde, Portugal), o uso do edifício, o tipo de obra (nova ou intervenção de
  nível I a IV, como no CTE art. 6.º) e a altura. Fica no projeto (IFC) e o país escolhido passa a ser o dos projetos
  novos deste computador.
- **As regras são dados, não programa:** um ficheiro por regulamento (`arqbim/regulamentos/CV/cte_2012.json`), cada
  regra com o diploma, o artigo, o texto, onde se aplica, a medida e o limite. O primeiro é o **Código Técnico da
  Edificação de Cabo Verde** (Portaria conjunta n.º 4/2012), lido no Boletim Oficial: pé-direito (art. 27.º — 2,70 m
  na habitação em 80 % da área, 2,40 m em vestíbulos, corredores, instalações sanitárias e arrumos, 2,30 m no resto,
  3,20 m em serviços e comércio, 2,20 m no estacionamento), portas (art. 30.º — 0,90 m úteis na entrada do edifício,
  0,70 m nos compartimentos, 2,00 m de altura), áreas dos compartimentos pela tipologia (art. 40.º e Anexo I — sala,
  cozinha, quartos do maior para o menor, sala e cozinha juntas no T0/T1, suplementos) e área bruta do fogo (art. 40.º
  n.º 10). Cada valor diz «(valor a confirmar)» até ser conferido. Onde o CTE não diz nada, a lei portuguesa
  (art. 4.º) — o pacote de Portugal vem num passo seguinte.
- **O que se mede:** a área útil; o pé-direito em vários pontos do compartimento (até ao teto, à laje ou à cobertura
  de cima, a partir da laje ou do piso de baixo); a área bruta do fogo (até à face exterior das paredes exteriores e
  a meio das paredes com outro fogo); a largura útil das portas (o vão menos os aros e a folha aberta). Sem nada por
  cima, o pé-direito não se mede — e isso não conta como falha.
- **O vigilante:** 0,3 s depois de cada alteração verifica tudo outra vez (o que não mudou é reaproveitado).
- **No rodapé, à esquerda:** «CTE ✓» a verde, «CTE ✗ 2» a vermelho, «CTE ⚠ 1» a laranja («§ Regulamento?» antes de
  escolher o país); a dica conta-os e o clique abre o menu.
- **A faixa vermelha** no fundo da vista, quando uma alteração cria uma falha que não havia: a frase inteira — «✗ Sala
  (Fogo A): área útil 11,52 m² — CTE, art. 40.º, n.º 3 e Anexo I: mínimo 14,00 m²» — com **Ir para** (abre a planta
  do pavimento, escolhe e enquadra) e **Porquê** (o texto da regra, o medido, o exigido, a fonte e como resolver).
  Fica até à alteração seguinte.
- **Na planta:** os ambientes que falham ficam tingidos de vermelho (laranja num aviso); desliga-se no menu do
  indicador.
- **Nas Propriedades** de um ambiente ou de uma porta: o grupo **Verificação**, cada regra com ✓ / ✗, o valor e o
  limite (o texto do artigo na dica).
- Uma zona fechada por paredes sem «Ambiente» (um corredor) liga os compartimentos do fogo — a porta para ela não é
  tomada como entrada.

## 0.416.0 — 2026-11-06

**O Verificador, passo 1: o leitor — o uso de cada ambiente, os fogos e a tipologia.** (O dono: «quando colocar os
ambientes, o verificador entenderá a tipologia, por exemplo um T2».)

- **O uso de cada ambiente** — sala, quarto, cozinha, instalação sanitária, corredor, vestíbulo, arrumos, tratamento
  de roupa, varanda, garagem, espaço comum… — sai do **nome** («Quarto 2», «WC», «Sala de jantar», «Casa de banho»)
  e do que está **dentro** dele (uma sanita ou um duche: instalação sanitária; lava-loiça, placa ou móveis de
  cozinha: cozinha; uma cama: quarto). Nas **Propriedades** do ambiente: «Uso: Automático — Quarto (pelo nome)»; a
  lista deixa escolher outro, e esse fica (Ctrl+Z desfaz).
- **Os fogos:** os ambientes ligados por portas são um fogo; os espaços comuns (patamar, átrio comum, caixa de
  escada) não são de nenhum, e a porta deles (ou de fora) é a entrada do fogo. Um edifício sem espaços comuns é uma
  moradia: os pisos, uns por cima dos outros, são um só fogo. Num prédio, um piso sem entrada própria por cima de um
  fogo é o piso de cima dele (um duplex). Nas Propriedades: «Fogo: Fogo A» — escrever outro nome dá-o ao fogo inteiro
  («Fogo 1.º Esq.») ou junta ambientes que as portas não juntam.
- **A tipologia** (T0, T1, T2… pelo número de quartos de dormir, como no CTE de Cabo Verde, art. 40.º, e no RGEU):
  nas Propriedades («T2 — 2 quarto(s), 72,96 m² úteis») e na planta, na etiqueta do maior ambiente de cada fogo
  («Fogo A · T2»).
- **No IFC:** ao gravar, o uso vai para o IfcSpace (ObjectType) e cada fogo é uma IfcZone com a tipologia e os seus
  ambientes — o Revit e os outros programas leem-nos. Na memória são calculados a cada mudança (não se guardam duas
  vezes); o que se escolhe à mão (uso, nome do fogo) fica no ambiente.

## 0.415.0 — 2026-11-05

**Tipos para os outros elementos, sempre no cabeçalho.** (Seguimento de «quero todos os elementos IFC tenham tipo,
guardado e aplicado a outros elementos» e «os tipos devem ficar no cabeçalho como o da porta».)

- **Tipos guardados e aplicados** (Guardar como tipo…, a lista no topo, Atualizar o tipo — como na superfície
  paramétrica) também no **piso**, no **teto**, nos **revestimentos de parede** (azulejo, pedra, ripado, perfurado…),
  nas **escadas**, nas **rampas**, nas **paredes cortina** e nos **móveis**. O tipo guarda o que é «de tipo» e não o
  que é de cada um:
  - piso: o acabamento (não o contorno);
  - teto: o estilo, o rasgo e a sanca (não a altura);
  - revestimento: o acabamento e o padrão (não a altura nem o sítio na parede);
  - escada: a largura e o cobertor (não o desnível nem a forma);
  - rampa: a largura (não o comprimento nem o desnível);
  - parede cortina: o afastamento dos montantes e das travessas (não o comprimento nem a altura);
  - móvel: tudo o que o define (medidas, frentes, interior, acabamento), como as famílias do Revit.
- **Guardas:** a lista dos tipos de guarda passou para o cabeçalho; o «Editar tipo…» fica na linha «Tipo».
- **Luminárias, terminais, equipamentos, aparelhos sanitários e elétricos e perfis:** o tipo (do catálogo, escolhido
  ao colocar) aparece também no cabeçalho, a cinzento — para outro, coloca-se outro elemento.
- **Piso:** o painel mostra agora o acabamento (para mudar), a espessura, a área e o botão «Editar contorno».

## 0.414.0 — 2026-11-05

**Painel Propriedades mais arrumado, e tipos guardados e aplicados (começando pela superfície paramétrica).** (O
dono, com a captura das propriedades de uma superfície paramétrica: «pode ser mais bem organizado, destacando os
títulos colapsáveis e com trama para melhorar a distinção de parâmetros. Quero todos os elementos IFC tenham tipo,
guardado e aplicado a outros elementos».)

- **O painel Propriedades:**
  - os títulos dos grupos (Restrições e dimensões, Identificação, Fase…) numa faixa própria, em negrito e mais
    altos;
  - os subgrupos (Forma, Modificadores, Construção, Nervuras, Camadas…) numa faixa mais leve, em negrito;
  - as linhas em faixas alternadas, para separar bem cada parâmetro;
  - **um clique em qualquer sítio do título** recolhe ou abre o grupo (antes era só na seta);
  - na superfície paramétrica, os botões da «Definição» ficam numa linha inteira, sem cortar os nomes;
  - tudo com as cores do tema, no claro, no escuro e nas paletas.
- **Tipos guardados e aplicados** (por agora na superfície paramétrica; os outros elementos sem tipo vêm a seguir):
  - **Guardar como tipo…** faz um tipo com o que o elemento tem — na superfície: a forma, os modificadores, a
    construção e o uso (não as curvas, que são de cada uma);
  - no **topo das Propriedades**, como o seletor de tipos do Revit, a lista dos tipos guardados: escolher um aplica-o
    ao elemento — ou a todos os escolhidos;
  - **Atualizar o tipo** leva as mudanças de um elemento ao tipo e a todos os elementos desse tipo;
  - «(sem tipo)» solta o elemento do tipo (os valores ficam);
  - **as vistas também têm o tipo no cabeçalho** (o dono: «os tipos devem ficar no cabeçalho como o da porta»): com
    nada escolhido, o topo das Propriedades mostra o **modelo de vista** da vista, numa lista, como o tipo de uma
    parede ou porta — escolher outro aplica-o; **Guardar como modelo…** faz um modelo com o que a vista mostra agora
    e dá-lho;
  - no IFC, cada tipo é um tipo IFC da classe do elemento (IfcRoofType numa cobertura, …), e os elementos ficam
    ligados a ele.

## 0.413.0 — 2026-11-05

**O plano de trabalho fica guardado com o projeto.** (O dono: «Sim, guardar».)

- O plano de trabalho posto (XY, XZ, YZ ou de uma face) grava-se com o projeto, no ficheiro das vistas, ao lado do
  IFC. Ao abrir o projeto outra vez, volta ao mesmo sítio.
- Pôr ou tirar o plano marca o projeto como alterado (o «*» no título), para o «Guardar» o levar.
- Um projeto novo continua a começar sem plano (no nível do piso).

## 0.412.0 — 2026-11-05

**Rodar à volta de X, Y ou Z, e planos de trabalho.** (O dono, com a captura de uma curva deitada no chão: «senti
dificuldade de manipular no plano XZ… precisamos do plano de trabalho e um comando rotacionar mais poderoso para
rodar em qualquer eixo como o do Blender… clico para indicar o pivô e se clicar X, ele rotaciona à volta de X»; «o
plano de trabalho, podemos criar de acordo com eixos e inserir na tela onde vai ficar. Pode ser também por seleção de
faces».)

- **Rodar (Q) em qualquer eixo:** antes ou depois de clicar o centro (o pivô), carregue em **X**, **Y** ou **Z** —
  ou nos botões X / Y / Z da barra de cima — e a rotação é à volta desse eixo, pelo centro.
  - O eixo aparece desenhado na sua cor (X vermelho, Y verde, Z azul) e o transferidor fica atravessado a ele.
  - Por omissão continua a ser Z, a vertical, como antes.
  - Visto de lado (com o transferidor de perfil), o ângulo segue o rato à volta do centro no ecrã, como no Blender.
  - À volta de X ou Y rodam os esboços (linhas, faces, curvas). As paredes, lajes e outros elementos BIM ficam de
    pé: só rodam à volta de Z, e o programa diz porquê.
- **Plano de trabalho** (Modelagem e Massa ▸ Desenhar ▸ Plano de trabalho):
  - **XY** (horizontal), **XZ** (vertical, ao longo do eixo vermelho) ou **YZ** (vertical, ao longo do verde):
    clique no ponto por onde passa; antes do clique, vê-se onde fica.
  - **Face:** clique numa face, e o plano dela passa a ser o plano de trabalho.
  - Na vista 3D, fica uma grelha azul leve. A Linha, o Arco, o Retângulo, o Círculo, a Linha livre e a Bézier
    desenham nele quando não há uma face por baixo do rato, e o Mover desliza nele.
  - «Voltar ao nível do piso» tira-o. As plantas, os cortes e os alçados não o usam, e as paredes, lajes e outros
    elementos BIM continuam nos pisos.
  - Dura enquanto o projeto está aberto (ao abrir ou criar um projeto, volta o nível do piso; desde a 0.413 fica
    guardado com o projeto).
- O **Offset** passou para o painel Modificar (como no Revit), para o Plano de trabalho caber no painel Desenhar
  sem dobrar mais nenhum painel no ecrã de 1536 px.

## 0.411.0 — 2026-11-05

**Curva de Bézier como no Blender.** (O dono: «a curva Bézier não é uma curva, mas uma linha reta. Esperava nós na
linha que podem ser movidos criando a curva — faça como o Blender».)

- **Um clique põe um nó suave:** as tangentes calculam-se sozinhas (como as «Auto» do Blender) e a curva passa,
  suave, por todos os pontos clicados — já enquanto desenha, até ao rato. Antes, um clique punha um canto e a curva
  ficava em linhas retas.
  - Carregar e arrastar continua a puxar a tangente à mão.
  - **Alt + clique** põe um canto.
- **Nós na linha:** com a curva escolhida (Selecionar), aparece um **«+» no meio de cada troço**. Arrastá-lo cria
  ali um nó novo e a linha curva-se — uma curva de dois pontos (reta) fica curva assim.
- Mover um nó automático refaz as tangentes dele e das vizinhas: a curva continua suave. Arrastar uma tangente
  passa esse nó a «à mão».
- As pegas da curva só se movem a arrastar (um clique a mais já não as apanha), como no perfil da parede.

## 0.410.0 — 2026-11-05

**Contorno do piso como o perfil da parede, e furos desenhados nos dois.** (O dono: «assim como editamos o perfil da
parede com Shift, Alt quero que faça também o mesmo com o piso. E vamos adicionar tanto na parede como no piso a
possibilidade de desenhar (em edição) polígonos no meio para fazer buracos personalizados»; e «2 clique no piso para
abrir a edição do perfil».)

- **Dois cliques numa laje, num piso (acabamento) ou num teto abrem o contorno** — como dois cliques numa parede
  abrem o perfil. O botão «Editar contorno» também aparece com um piso ou um teto escolhido.
- **Os mesmos gestos do perfil da parede, no contorno:**
  - arrastar o losango do meio de um lado faz um canto novo;
  - com **Shift**, o lado fica um **arco**;
  - com **Alt**, fica uma **curva**;
  - **Alt + clique num canto** faz uma **concordância** (o raio pelo rato, ou escrito e Enter);
  - um clique num ponto e Delete tira-o (ou endireita a curva).
  - Os cantos continuam a prender aos pontos do modelo, com X / Y e a distância escrita.
- **Furos desenhados**, com «Furo» na barra de cima (Polígono, Retângulo, Círculo), no contorno da laje / piso / teto
  e no perfil da parede:
  - polígono: clique nos cantos; no primeiro (ou Enter) fecha;
  - retângulo: dois cantos (ou arrastar, ou o tamanho escrito «1,2;0,8»);
  - círculo: o centro e a borda (ou o raio escrito).
  - Cada furo tem as mesmas pegas do contorno (os lados podem ficar arcos e curvas).
  - **Arrastar dentro de um furo muda-o de sítio**; um clique dentro e Delete apaga-o.
  - O modo fica ligado para desenhar o seguinte; Esc (ou o botão aceso outra vez) desliga-o, e só depois o Esc sai.
- No IFC: o corpo continua a ser uma extrusão com vazios (IfcArbitraryProfileDefWithVoids), com as curvas em
  pedaços; o desenho (cantos, arcos, curvas) fica ao lado — «Desenho» na laje, no piso e no teto, «PerfilFuros» na
  parede. Uma porta ou janela não pode ficar por cima de um furo da parede. Ao mudar o perfil da parede, os furos
  ficam (os que deixam de caber saem).

## 0.409.0 — 2026-11-05

**Portas e janelas com snaps; cotas interiores com as esquinas e as duas paredes.** (O dono: «coloque snap na inserção
da porta e janela no meio de um compartimento e a 10, 20 cm da gola da parede»; «na cota automática não pega as
paredes em esquinas no interior»; e, com captura de um compartimento com uma parede inclinada, «devia pegar as 2
paredes».)

- **Porta e janela prendem** (na planta e no 3D), com o nome do snap ao lado:
  - ao **meio do compartimento** — entre as paredes que cruzam aquela face (numa parede sem nenhuma, o centro da
    parede, como antes);
  - com a **ombreira a 0,10 ou 0,20 da gola** (da face da parede ao lado, de um lado ou do outro).
  - Fora destes sítios continua livre, ao centímetro. Nenhum snap põe o vão por cima da parede ao lado.
- **Cotas interiores — as esquinas:** a largura e a profundidade apanham as esquinas do compartimento que ficam entre
  as duas paredes (a esquina de dentro de um L, um recanto): num L, por exemplo, 4,00 + 3,80 em vez de só 7,80.
- **Cotas interiores — as duas paredes:** as duas cotas seguem as **duas paredes mais perto do rato que não são
  paralelas**. Junto à esquina de uma parede direita com uma inclinada: uma atravessa o compartimento paralela à
  direita, até à inclinada, e a outra corre ao longo da inclinada. Num compartimento direito fica como antes (em
  esquadria).

## 0.408.0 — 2026-11-05

**Cotas interiores: alinham-se com a parede mais perto, e Ctrl+clique acrescenta.** (O dono, com captura de um
compartimento em L com uma parede inclinada: «gostaria de poder pegar as paredes em L clicando Ctrl para adicionar mais
cotas. Ele precisa alinhar com as paredes ao aproximar das paredes… a cota pega o alinhamento da parede inclinada e
fica só assim».)

- **A largura e a profundidade alinham-se com a parede mais perto do rato.** Perto de uma parede inclinada, as cotas
  seguem-na; perto das outras, ficam direitas com elas. Antes seguiam sempre o lado mais comprido do compartimento —
  num L com a parede de baixo inclinada, ficavam todas inclinadas.
- **Ctrl+clique acrescenta outro par de cotas** sem tirar as que já pôs nesse compartimento (por exemplo, uma em cada
  ala do L). Um clique sem Ctrl volta a pôr só um par.
- Com «Todos» os compartimentos, cada um continua a ser cotado pelo seu lado mais comprido.

## 0.407.0 — 2026-11-05

**Ortogonalizar: a porta e a janela endireitam-se com a parede.** (O dono, com captura: «esta parede estava inclinada,
então usei o ortogonalizar, mas a porta e a janela ficaram bugadas».)

- Ao ortogonalizar uma parede inclinada, as portas e janelas dela (e das paredes ligadas) são redesenhadas com ela.
  Antes a parede ficava direita mas a janela continuava desenhada torta e o aro da porta saía das faces da parede
  (no arquivo já estavam certas: só o desenho ficava para trás até se reabrir o projeto).

## 0.406.0 — 2026-11-05

**Tutoriais na própria página inicial.** (O dono, com capturas: «quando o utilizador pesquisar alguma coisa no
tutorial, que se abra logo no lado, ocultando as colunas de discussão e apoio… a sobreposição é apenas temporária.
Quando a janela de tutorial for fechada, teremos de novo os 2 painéis na direita. O canal de YouTube é
youtube.com/@arqsynth_a».)

- **Um tutorial abre-se na página inicial, no lugar das colunas Discussões e Apoiadores** (um pouco mais largo num
  ecrã grande). O resto da página não encolhe: antes os «Primeiros passos» abriam o painel Ajuda ao lado, que apertava
  todas as colunas, e os outros tutoriais uma janela à parte.
- O tutorial aberto fica marcado na lista; clicar noutro troca o texto no mesmo sítio.
- **Primeiros passos** com **▸ Mostrar onde está** em cada passo (muda a fita para o separador certo e acende o botão).
- **Procurar neste tutorial…**: sem acentos e sem maiúsculas, todos os sítios realçados, «1 de 2»; Enter vai para o
  seguinte, Shift+Enter para o anterior (ou ▲ ▼).
- **×** (ou Esc no campo de procurar) fecha o tutorial e **voltam as Discussões e os Apoiadores**.
- **▶ Vídeos no YouTube** abre o canal **youtube.com/@arqsynth_a**, com os tutoriais básicos.

## 0.405.0 — 2026-11-05

**Cotas: arrastar com alinhamentos, e o tipo e os ajustes no painel Propriedades.** (O dono: «quando largo as cotas
numa posição ele não fica como queria… seria bom ter snap de alinhamento das cotas dos números para não ficar uma
bagunça… o editor da cota, esperava que ficaria na barra de propriedade».)

- **O número fica onde o largar.** Antes, um número que o programa tinha afastado sozinho (por não caber) saltava
  para outro sítio ao ser largado.
- **Arrasta-se o próprio número ou a própria linha** de uma cadeia escolhida, sem ter de acertar nos losangos. As
  pegas das cotas só se movem a arrastar (um clique já não as «pega»).
- **Alinhamentos magnéticos** (com uma linha-guia cor-de-rosa):
  - um número alinha-se com os outros números (na horizontal ou na vertical) ou volta para cima do meio da sua linha;
  - a linha de uma cadeia alinha-se com outra cadeia paralela, ou fica à distância habitual entre filas (7 mm no
    papel).
- **No painel Propriedades**, como no Revit:
  - em cima, a lista dos **tipos de cota** (escolhe-se ali o tipo das cotas escolhidas);
  - **Editar tipo…** abre os Tipos de cota já nesse tipo;
  - **Cota:** o valor (numa cota sozinha, escreve-se e o elemento da ponta move-se) ou o total da cadeia, e **IG**;
  - **Texto:** substituir pelo texto, prefixo, sufixo, texto por cima e por baixo, **Repor os valores no sítio**;
  - **Texto da cota** (abrir) e **Referências** (acrescentar).

## 0.404.0 — 2026-11-05

**Portas e janelas: o lado certo, a prévia e as cotas na planta.** (O dono, com capturas: «quando insiro porta, a prévia
mostra a porta para dentro, mas quando clico para fixar, ela fica com abertura para fora… também no 3D»; «as alças de
controlo poderiam ficar dentro da porta e menores… só funciona clicando no pontinho das setas»; «para a janela, não
tive uma prévia… essa linha azul me confundiu… no 2D ficaria melhor uma cota».)

- **A porta abre para o lado onde está o rato**, como mostra a pré-visualização — também depois de fixada, na planta e
  no 3D (antes ficava a abrir para o lado contrário). F continua a trocar o lado; Espaço, as dobradiças.
- **Na planta, ao inserir uma porta ou uma janela:**
  - o vão aparece desenhado através da parede: a porta com a folha aberta e o arco, a **janela com o caixilho e o
    vidro** (antes a janela não tinha pré-visualização na planta);
  - em vez da linha azul ao longo da face, **duas cotas temporárias como no Revit**: das ombreiras até à parede mais
    próxima de cada lado (ou até à ponta da parede).
  - No 3D fica como estava.
- **As setas de uma porta escolhida ficam dentro da porta e mais pequenas:** a das dobradiças (↔) no vão, a do lado
  (↕) no arco de abertura. **Clicar em qualquer ponto da seta** vira a porta (antes só a bolinha do meio).

## 0.403.0 — 2026-11-05

**A página inicial é a casa, sempre na primeira aba.** (O dono, com captura: «quero que a página inicial tenha um ícone
de home e não seja uma aba normal que o utilizador possa fechar; ele estará sempre ali logo na primeira, a aba 3D depois
dele».)

- A aba da página inicial passa a ser **só o ícone da casa** (o nome «Início» aparece ao passar o rato), **sempre a
  primeira**, com a **3D logo a seguir**.
- **Não tem «×»** e não se fecha (nem com Ctrl+W, nem com «Fechar as outras», que também a deixa ficar).
- **Não se arrasta**; uma aba largada antes dela volta para depois dela.
- **Ctrl+Tab** anda só pelas vistas (não pela casa); a casa não se grava com o projeto (como antes).
- A casa tem a cor do texto do tema (clara no tema escuro, escura no claro) e muda com ele.

## 0.402.0 — 2026-11-05

**Editar as cotas como no Revit.**

- Um clique numa cota escolhe a **cadeia inteira**. Aparecem as pegas:
  - **quadrados** nas linhas de chamada: arraste um para **outra referência** (acende-se a laranja);
  - um **losango** na linha: arraste-a para a **afastar ou aproximar** (as cotas todas juntas);
  - um **losango** em cada valor: arraste-o para o **mudar de sítio**. Se ficar longe, aparece uma linha de chamada. O
    botão direito ▸ «Repor os valores no sítio» volta a pô-los no lugar.
- **Botão direito** numa cadeia escolhida (como no Revit):
  - **Apagar linha de chamada** (a do quadrado onde clicou): as duas cotas vizinhas passam a uma;
  - **Acrescentar referências**: clique nas novas e depois num sítio vazio;
  - **IG — igualar**: as cotas ficam iguais — as paredes, portas e janelas do meio movem-se — e escrevem «IG». Outra
    vez tira o IG;
  - **Texto da cota…**.
- **Duplo clique num valor** abre o «Texto da cota»:
  - **mudar o valor**, que move o elemento de uma das pontas, à escolha;
  - **substituir pelo texto**;
  - **prefixo**, **sufixo**, **texto por cima** e **por baixo**;
  - aplicar só a esta cota ou à cadeia toda.
- Com uma parede (ou porta, ou janela) escolhida, um clique no valor de uma cota presa a ela pede o novo valor e
  **move-a**, como no Revit.
- Cada edição desfaz-se com um Ctrl+Z.
- **Mais rápido:** numa planta com muitas cotas, cada alteração redesenha-as em cerca de um quinto do tempo (128 cotas:
  de 0,28 s para 0,06 s) — os números que não mudam não se refazem.

## 0.401.0 — 2026-11-05

**A Cota manual como no Revit.** (O dono: «vamos ter também cotação manual — mas a cotação manual precisa ser como no
Revit».)

- **Clique nas referências, uma a seguir à outra, e depois num sítio vazio** para pousar a cadeia: uma cota entre cada
  duas referências vizinhas, todas na mesma linha (uma «cadeia», escolhe-se e move-se inteira).
- As referências são **linhas** — a face de acabamento, a face do núcleo, o eixo da parede, o eixo do núcleo, a
  **ombreira** ou o **eixo** de uma porta ou janela, um **eixo estrutural** — ou **pontos** (cantos e pontas). A que está
  sob o rato **acende-se a laranja**, com o nome ao lado; o **Tab** passa à seguinte no mesmo sítio (face → núcleo →
  eixo…). Depois da primeira linha só se oferecem as paralelas: a cadeia mede de través.
- **Nas paredes** (barra contextual) diz qual vem primeiro: faces de acabamento, faces do núcleo, eixos, eixo do núcleo.
- **Escolher: Paredes inteiras** (como o Revit): um clique numa parede dá, ao longo dela, as pontas, as portas e janelas
  (ombreiras ou eixos) e as paredes que a cruzam ou lhe chegam.
- **Cota: Alinhada / Linear (horizontal ou vertical, conforme o rato) / Angular.**
- Como antes, dois cantos e um clique ao lado dão uma cota de ponto a ponto. «Continuar a cadeia» (desligado por
  omissão, como no Revit) continua a última cadeia com cada clique.
- As cotas presas a faces, núcleo ou eixos **seguem a parede** quando ela muda de espessura.

## 0.400.0 — 2026-11-05

**Cotas interiores num clique.** (O dono: «quero cotas automáticas, para cotar o interior com um clique».)

- **Anotar ▸ Cotas interiores** (ferramenta nova): ao passar o rato, o compartimento acende-se a azul com as cotas que
  vão ficar; **um clique** pousa-as. Funciona **com ou sem Ambiente**: o compartimento é o espaço fechado pelas
  paredes.
- Três maneiras de cotar (barra contextual, «Cotar»):
  - **Largura e profundidade**, de parede a parede, com as linhas a passar pelo ponto do clique (clicar noutro ponto
    do mesmo compartimento muda-as de sítio);
  - **Corrida (através do edifício)**: a linha atravessa o edifício pelo ponto do clique, com cada compartimento e cada
    espessura de parede, de fora a fora;
  - **Ao longo das paredes, com os vãos**: cada parede do compartimento cotada por dentro — os cantos, as portas e
    janelas (ombreiras ou eixos), as paredes que lhe chegam.
- A mesma escolha **Nas paredes** (faces de acabamento, faces do núcleo, eixos, eixo do núcleo), a **direção** (as
  duas, só a largura, só a profundidade) e **o compartimento do clique ou todos os do pavimento**.
- «Cotar ambientes» (o botão antigo) cota todos os compartimentos de uma vez, mesmo sem Ambientes.

## 0.399.0 — 2026-11-05

**Cotas exteriores num clique, e o que se cota nas paredes.** (O dono: «quero cotas automáticas… a mesma coisa para
a cotação externa» e «precisa ter opção de cotar acabamento externo, núcleo da parede, eixos da parede etc.»)

- **Anotar ▸ Cotas exteriores** (ferramenta nova): na planta, a azul, as cotas que vão ficar à volta do edifício; **um
  clique** pousa-as. As filas, de dentro para fora: os **vãos** (ombreiras ou eixos), as **paredes interiores** que
  chegam à fachada, os **cantos** (recuos e saliências) e o **total**. Uma fila que não diz nada de novo não aparece.
- **Em qualquer direção:** o edifício não precisa de estar alinhado com N/S/E/O — cada lado do contorno, para onde quer
  que olhe, recebe as suas filas (também os recuos de uma casa em L).
- **Nas paredes** (como a «Preferência» do Revit), escolhe-se o que se cota: **faces de acabamento**, **faces do núcleo**
  (as cotas «em osso», sem os rebocos), **eixos das paredes** ou **eixo do núcleo**.
- Na barra contextual: os vãos (ombreiras, eixos, não cotar), as filas (paredes interiores, cantos, total), **todas as
  fachadas ou só a mais perto do rato**, e o tipo de cota. Mudou uma opção? Clique outra vez: as cotas refazem-se no
  sítio (um Ctrl+Z por clique).
- As cotas **seguem as paredes**: uma ponta presa a uma face, ao núcleo ou ao eixo fica nessa linha quando a parede se
  move **e quando muda de tipo** (outra espessura, outras camadas).
- «Cotar fachadas» (o botão antigo) faz o mesmo de uma vez, com as opções da ferramenta.

## 0.398.0 — 2026-11-05

**Tipos de cota: o motor da aparência.** (O dono: «agora vamos turbinar a aba documentação… as cotas precisam de
opções mais robustas… e um motor de edição da aparência da cota». Primeiro passo da secção «Cotas como no Revit» do
PLANO.)

- **Anotar ▸ Tipos de cota…** (antes «Estilo das cotas…», com 4 opções) é agora como as propriedades de tipo de uma
  cota no Revit, com uma **amostra em papel** que muda a cada valor:
  - **Gráficos:** a marca nas pontas (traço oblíquo fino ou grosso, seta cheia, aberta ou fechada, ponto, círculo,
    nenhuma), o tamanho e a espessura da marca, a espessura e a cor da linha, o prolongamento da linha de cota para lá
    das linhas de chamada;
  - **Linhas de chamada:** afastadas do elemento ou de comprimento fixo, o afastamento, o prolongamento, a espessura;
  - **Texto:** a letra, a altura, o fator de largura, negrito, itálico, sublinhado, o afastamento à linha, por cima
    da linha ou na linha (interrompida), ao longo da linha ou sempre na horizontal, fundo opaco, a cor; e o que
    fazer aos valores que não cabem (afastá-los ou deixá-los no meio);
  - **Unidades e valores:** m, cm ou mm, as casas decimais, arredondar (0,5 mm a 5 cm), escrever a unidade,
    **milímetros em expoente** (2,47⁵), prefixo e sufixo;
  - **Vãos e cotas iguais:** a altura do vão por baixo da largura das portas e janelas; o texto das cotas iguais
    («IG»).
- Os tipos **duplicam-se, mudam de nome** (as cotas desse tipo seguem o nome novo) e **apagam-se**; «Começar de:»
  dá cinco aspetos habituais (arquitetura, traço grosso como o Revit, engenharia com setas, expoente, centímetros com
  pontos).
- **Um só desenhador** para o ecrã, o PDF, as folhas, o SVG e o DXF: as cotas saem iguais em todo o lado. No ecrã
  passam a estar **à escala da vista** (como no Revit): o texto ao longo da linha (as verticais leem-se da direita),
  com a altura que terá no papel.
- As **cadeias** (cotas lado a lado na mesma linha — as de «Cotar paredes / fachadas», a Cota em cadeia) desenham-se
  como uma só: as linhas de chamada e as marcas partilhadas, e os **valores que não cabem** saem para fora nas pontas
  ou sobem com uma pequena linha de chamada (alternando, para não se taparem).
- Os valores arredondam **a meio para cima**, como à mão (0,825 m em cm = 83; antes saía 82).
- Clicar no **número** de uma cota também a escolhe (antes só a linha).

## 0.397.0 — 2026-11-04

**As duas listas de materiais iguais.** (O dono perguntou a diferença entre a janela «Materiais do projeto» e o
«Navegador de Materiais»: são os mesmos materiais — a janela para os editar, o Navegador para os escolher e aplicar —,
mas cada uma os mostrava por outra ordem; «Sim, iguala».)

- As duas mostram os materiais pela **mesma ordem alfabética**, sem contar os acentos («Aço…» antes de «Água…», como
  num dicionário; antes «Aço» vinha depois de «Azulejo»).
- O **Navegador de Materiais** ganhou o mesmo **filtro por família** (Todas as famílias, Alvenarias, Betões e
  argamassas, Isolamentos, Madeiras e derivados, Pedras, Metais, Rebocos/gessos/cerâmicos, Vidros, Tintas, Outros) e
  a mesma **pesquisa** da janela.
- Com a **Pintura** ligada, «Sem pintura» continua no topo; as tintas já não vêm primeiro — escolha **Tintas** no
  filtro para ver só essas (o material do balde continua marcado).

## 0.396.0 — 2026-11-04

**Propriedades mais arrumadas e legíveis.** (O dono, com a captura das propriedades de uma escada: «melhorar a
organização da propriedade e visibilidade dos parâmetros».)

- Os grupos vêm pela **ordem do Revit**: primeiro o que se edita — **Restrições e dimensões**, depois **Materiais** —,
  e só depois **Identificação** (nome, classe, tipo, pavimento, GlobalId), **Fase** e **Dados IFC**.
- **Nenhum nome cortado com «…»:** um nome ou um valor comprido passa a **duas linhas** (ex.: «Deslocamento da
  base», «Número de espelhos», «2 espelhos + cobertor»); a coluna dos nomes fica do tamanho do nome mais comprido,
  no máximo metade do painel.
- O **divisor** entre nomes e valores arrasta-se e **fica onde o deixou** (também para os elementos seguintes e da
  próxima vez que abrir o programa).
- Um **grupo fechado à mão fica fechado** para os elementos seguintes (ex.: fechar «Dados IFC e parâmetros» se não
  precisa dele); aberto outra vez, volta a abrir-se.
- «Dados IFC — Pset_StairCommon» passou a **«Dados IFC»** com o nome do conjunto ao lado, na coluna dos valores.
- Um valor comprido num campo de texto mostra-se **do princípio** (antes via-se o fim: «erfície paramétrica 1»), com
  o texto inteiro na dica.

## 0.395.0 — 2026-11-04

**Superfície paramétrica: forma primeiro, construção depois.** (O dono: «a cobertura orgânica que pedi é uma coisa mais
complexa, e não essa forma simples de modelagem com colunas… estude o conceito da superfície paramétrica; com esse dá
pra fazer cobertura e estrutura orgânica»; e «não chamaria cobertura, porque não se restringe a cobrir».) Estudado o
addon (`EXEMPLOS DO BLENDER\tools\surfaces` e `roofs\organic_roof.py`) e trazido o seu conceito para o programa.

- **Massa e Estudos ▸ Formas livres ▸ Superfície paramétrica** (também em Estrutura ▸ Elementos): uma superfície curva feita
  das **curvas do modelo** (linhas, arcos, Bézier, linhas livres, o contorno de uma face). Clica-se nas curvas uma a uma
  (as que estiverem selecionadas entram logo), vê-se a superfície a cada clique, **Enter** cria. As formas:
  **loft** entre 2 ou mais secções (suave entre elas, cada secção virada e rodada para não torcer), **4 bordos**
  (Coons), **revolução**, **extrusão**, **varrimento** (perfil ao longo de um caminho, sem dar voltas), **tampa** sobre
  um contorno fechado (cúpula de membrana, abóbada, onda, cosseno ou plana, numa grelha de quatro lados) e
  **fórmula** (z = f(u, v) sobre dois cantos). «Automática» escolhe pela quantidade de curvas.
- **Segue as curvas:** editar, mover ou rodar uma curva de que a superfície é feita refaz a superfície **no mesmo
  passo** (Ctrl+Z desfaz as duas). A ligação fica gravada (os esboços ganham um nome próprio que sobrevive a gravar e
  abrir); apagar a curva não apaga a superfície (ela guarda a sua cópia).
- **Modificadores**, por ordem e cada um ligável: deslocar, atrator (a um ponto ou a uma curva), afunilar, torcer,
  inclinar, onda, suavizar, dobrar e recortar (por uma curva fechada). Os números podem ser **fórmulas** dos
  parâmetros e de u, v, x, y, z (ex.: `45*v`, `0,3*sin(2*pi*u)`), lidas em segurança (nunca se executa código).
- **Construção** sobre a superfície: casca (com espessura), nervuras U/V, ripas/brise, entrelaçado, **gridshell**
  (quadrado, triangular, diagrid ou hexagonal, com nós), anel de bordo, pilares, **painéis** (painel, vidro, metálico,
  fibrocimento; com junta exata; caixilho com vidro; células abertas por fórmula — «fachada pixel» —; abertura em cada
  painel por fórmula e imagem; ou **perfuração fina** com furos reais) e **vidro spider** (aranhas e rótulas). Cada
  peça no seu material e cor; a **lista de peças** (barras por comprimento ao mm, painéis com o empeno, raio mínimo
  de dobragem das nervuras) em CSV.
- **Uso** (não é só cobertura): Estrutura (IfcBuildingElementProxy, por omissão), Cobertura (IfcRoof), Fachada
  (IfcCurtainWall) ou Pala/brise (IfcShadingDevice) — muda a classe IFC sem perder o elemento.
- **Anel de controlo** (Formas livres): copia a curva selecionada 1 m acima a 75 % e deixa a pilha selecionada — duas
  vezes e a Superfície paramétrica faz o loft (cúpula, torre).
- Nas Propriedades: forma, divisões, parâmetros, modificadores e construção (cada campo editável; ▲▼ para a ordem,
  ✕ para tirar, «+» para juntar), o resumo das peças e os avisos (painéis empenados…); exportar, importar e editar
  a definição (`.arqsurf`, o mesmo formato do addon).
- A antiga «Cobertura orgânica» sai da fita (os elementos já feitos continuam a abrir e a editar-se).
- Nas Propriedades, a coluna dos nomes já não empurra os valores para fora quando um nome é muito longo (como «Dados
  IFC — Pset_BuildingElementProxyCommon») — melhorado de novo na 0.396.
- A «Casa do Farol» ganha uma pala de entrada feita como superfície paramétrica (gridshell, anel de bordo e vidro).

## 0.394.0 — 2026-11-04

**A casa de teste completa.** (O dono: «um teste de modelagem de uma casa não muito comum… com todos os componentes
do aplicativo; assim dá pra verificar tudo».)

- Nos testes de janela, a **«Casa do Farol»**: dois pisos, sala com fachada de vidro, cozinha, casa de banho, quartos
  sob um telhado de 4 águas com clarabóia e calhas, terraço sob uma abóbada orgânica envidraçada, torre redonda de
  betão com escada em caracol, janelas na parede curva e uma faixa de vidro curva, cobertura plana com ralo, atelier
  de paredes leves com cobertura por blocos, muro do jardim com o topo em arco e painel perfurado, varanda em pilares
  e viga sobre sapatas, elevador, rampa, terreno com plataforma; ambientes (com separador), pisos, teto, luzes,
  rodapé e sanca, azulejo, pintura (em elementos e num esboço), nicho, frisa, cozinha, roupeiro, louças, água, ar,
  eletricidade; grelha estrutural, um grupo, um componente feito de um esboço, corte, alçados, 4 folhas e o PDF.
  Cada parte é verificada à parte (35); o IFC sai válido, grava-se e reabre-se com os mesmos elementos.
- A casa fica em **`exemplos\Casa de teste completa.ifc`** (com as folhas em PDF ao lado), para abrir no programa.
- Corrigido (encontrado pela casa): ao **abrir um projeto com móveis** (cozinha, roupeiro), a pré-visualização
  rápida parava com um erro ao pedir a cor das frentes a um IFC ainda por ler — as peças a seguir podiam não aparecer
  até a leitura acabar.
- Os testes de janela **passam todos**: as 3 falhas antigas eram do teste, não do programa — um clique no meio de uma
  caixa de verificação larga (só a quadrícula e o texto respondem), um eixo de espelho a meio píxel do esperado, um
  separador desenhado a 40 cm das paredes que só por vezes «agarrava».

## 0.393.0 — 2026-11-04

**Modelos («Arquivo Modelo»), Fase 1: o gestor e o modelo de fábrica.** (O dono pediu um sistema de modelos para a
suite ArqSynth, em 4 fases, parando no fim de cada uma para testar.)

- Biblioteca **`arqsynth_templates/`** (Python só com a biblioteca padrão: os outros programas da suite podem usá-la
  tal como está): listar, ler, gravar, atualizar, apagar, duplicar, mudar o nome, definir e obter o padrão de cada
  programa, validar.
- Os modelos ficam na pasta da suite, fora da instalação: no Windows `%APPDATA%\ArqSynth\templates\` (o ArqSynth BIM,
  que corre no Linux do Windows, usa essa mesma pasta do Windows); `settings.json` ao lado diz o padrão de cada
  programa.
- Ficheiros **`.astpl`**: JSON legível (ou ZIP com o JSON e as texturas), com `schema_version`; formato descrito em
  `arqsynth_templates/FORMATO.md`, com o esquema `schema.json` e um exemplo `exemplo.astpl`.
- O modelo de fábrica **«ArqSynth Padrão»** vem dentro do programa, feito do que ele já usa (93 materiais, 59 tipos com
  camadas, portas e janelas com o desenho do caixilho, estilos de cotas, penas e tramas): não se apaga, e é o usado se
  a pasta estiver vazia, o ficheiro estragado ou o padrão tiver desaparecido.
- Ao ler: o que falta ou está errado fica com o valor de fábrica e é dito; um modelo de uma versão antiga do formato é
  convertido; um de uma versão mais nova é lido sem perder o que não se conhece e não é regravado por cima.
- Gravação segura (ficheiro temporário e depois a troca) e um bloqueio para dois programas não gravarem ao mesmo
  tempo.
- Para testar sem abrir o programa: **`Modelos - verificar.bat`** (na pasta do ArqSynth BIM) — um menu em português.
- Ainda não muda nada no ArqSynth BIM em si: isso é a Fase 2 (o padrão aplicado ao Novo Projeto).
- **Grelha do chão mais suave nos temas escuros** (o dono: «a linha grid no tema escuro está muito forte»): a cor das
  linhas sai agora do fundo em uso — num fundo escuro (Escuro, Grafite, Azul · Revit, vistas escuras) só um pouco
  mais clara do que ele; num fundo claro de paleta, um pouco mais escura. O fundo claro normal fica como estava.

## Interface minimalista — 2026-11-04

- Cabeçalho compacto e separador ativo com o fundo da fita e uma linha na cor de destaque.
- Ícones vetoriais das ferramentas principais com a cor da paleta, mantendo os modos de desenho nos grupos.
- Temas do estudo em **Visualizar ▸ Tema** e no botão de paleta do cabeçalho: **Bege, Pedra, Escuro, Grafite e Azul · Revit**, com as cores finais aprovadas. Areia retirado; uma preferência antiga por Areia passa para Bege.
- **Explorar cores** mantém a edição e a gravação de paletas personalizadas.

## 0.392.0 — 2026-11-04

**Pintura também nos esboços.** (O dono: «Sim, faz isso» — pintar as faces desenhadas com Linha, Retângulo,
Push/Pull, como no SketchUp.)

- O balde (**B**) pinta agora também as faces dos **esboços**. **Clique** = a face (com os pedaços dela unidos por
  arestas escondidas — um círculo desenhado numa face, a moldura de um Offset). **Ctrl + clique** = as faces ligadas
  a ela que têm a mesma cor (como o Ctrl do SketchUp). **Shift + clique** = substituir essa cor em todo o modelo —
  elementos e esboços, um só Ctrl+Z. **Alt + clique** = conta-gotas.
- A pintura fica em cada face e acompanha-a: no **Push/Pull** a face puxada continua pintada (os lados novos não);
  desenhar um retângulo numa face pintada ou dividi-la com uma linha deixa os pedaços pintados; copiar, espelhar,
  apagar outras faces — a pintura fica onde estava. Grava-se com o projeto.
- Corrigido: **dois cliques numa linha** voltam a escolher a cadeia toda — o segundo clique caía na caixa da cota
  da linha escolhida (desenhada do lado da linha) e ficava a «escrever na cota».

## 0.391.0 — 2026-11-04

**Pintura com o fluxo do SketchUp.** (O dono: «já tem o comando de pintura, quero que seja com fluxo como do
SketchUp» — no addon é a «Pintura (balde)».)

- Tecla **B** (como no SketchUp), ou **Modelagem ▸ Materiais ▸ Pintura**, ou **Arquitetura ▸ Acabamentos ▸
  Pintura**: o balde. O **Navegador de Materiais** abre-se à direita: **um clique** escolhe o material (as tintas
  primeiro; no topo, **Sem pintura**, que tira a pintura — como o material «Default» do SketchUp). O material também
  se escolhe na barra de cima.
- **Clique** numa face = pinta essa face do elemento (a face da parede, o topo da laje, uma água da cobertura).
- **Ctrl + clique** = o elemento todo. **Shift + clique** = substitui essa cor por a nova em todo o modelo.
  **Alt + clique** = conta-gotas: o material da face passa para o balde (a pintura, ou aquilo de que a face é feita).
- Junto ao rato diz o que vai acontecer («Pintar esta face: Tinta terracota»).
- A pintura não muda o tipo nem as camadas: fica no elemento, presa à face (mover ou rodar o elemento leva-a). Vê-se
  em qualquer estilo de vista, no papel e no render. Nas Propriedades: **Pintura** — cada tinta e a área pintada.
- Dez **tintas** novas no catálogo (branca, marfim, areia, cinzento claro, grafite, terracota, ocre, verde-salva,
  azul-acinzentado, vermelho-escuro), na família **Tintas**.
- Por agora pintam-se os elementos BIM; os esboços (faces desenhadas com Linha/Retângulo) ainda não (na 0.392 já).

## 0.390.0 — 2026-11-04

**Cobertura orgânica.** (O dono: «não vi o comando de … cobertura orgânica»; no addon do Blender: «coberturas
orgânicas paramétricas — gridshell, casca, envidraçada, pérgola curva — a partir de curvas de controlo».)

- Botão **Cobertura orgânica** em **Arquitetura ▸ Pisos e coberturas**, ao lado de Cobertura.
- Desenha-se o **contorno no chão** do pavimento ativo, de quatro maneiras (na barra, **Contorno**): **Curvo** (uma
  curva suave passa pelos pontos clicados — o contorno orgânico), **Polígono**, **Retângulo** (dois cantos) e
  **Círculo** (centro e borda). Enquanto se desenha, a cobertura aparece já em volume. Fecha-se clicando no primeiro
  ponto ou com **Enter**; **Backspace** tira o último ponto; o botão direito recomeça.
- A **forma** sai do próprio contorno — não se modela à mão: **Cúpula** (como uma membrana empurrada para cima,
  presa ao contorno: redonda num círculo, uma almofada num quadrado), **Abóbada** (um arco sobre cada corda do
  contorno, tão alto quanto ela é larga — as pontas ficam arcos abertos) e **Onda** (a abóbada com a cumeeira a subir
  e a descer).
- O **sistema**: **Casca** (betão, 12 cm), **Gridshell** (barras de aço preto numa malha de 1,20 m, retas de nó a nó),
  **Envidraçada** (o gridshell com vidro em cada célula) e **Pérgola curva** (costelas de madeira num só sentido,
  curvas). Com **aro perimetral** por baixo do beirado e **apoios** até ao chão (espaçados 4 m, ou nos cantos).
- Nas **Propriedades** muda-se tudo: forma, sistema, nível do beirado, flecha, malha e a sua direção, espessura ou
  diâmetro das barras, material, aro, apoios; e vê-se a área, as barras (quantas e quantos metros), o vidro e os
  apoios.
- Em IFC é uma **IfcRoof FREEFORM** só, com cada peça no seu material (betão, aço, madeira, vidro).

## 0.389.0 — 2026-11-04

**Painel perfurado como comando próprio.** (O dono: «não vi o comando de painel perfurado»; no addon do Blender é
uma ferramenta, aqui era só um dos acabamentos do Revestimento de parede.)

- Botão **Painel perfurado** em **Arquitetura ▸ Acabamentos** (o primeiro, grande).
- Passe o rato por uma parede: aparece o contorno do painel e as juntas das placas. **Clique** = a face inteira
  (toda a altura — se a parede crescer, o painel acompanha). **Arraste** de um canto ao outro = só esse retângulo
  (junto ao rato, «largura × altura»). **Clique num painel perfurado** que já lá está = escolhe-o (as medidas ficam
  nas Propriedades) — mesmo que o clique caia num furo.
- Na barra: **Furos** redondos ou quadrados; **Malha** reta ou **a 45°** (quincôncio; com furos quadrados ficam
  losangos); **Ø** (o diâmetro, ou o lado do quadrado), **Passo**, **Margem**; o tamanho das **placas** (1,22 ×
  2,44 m) e a **Junta** entre elas (1 cm); **Imagem**: uma fotografia ou desenho faz os furos maiores onde é escura
  e tira-os onde é branca (a imagem cobre o painel, como uma fotografia cortada a um quadro).
- Nas **Propriedades** do painel muda-se tudo isto e o retângulo (início e fim na parede, base, topo); o número de
  furos e a área aberta são contados com o tamanho de cada furo.
- O **DXF para a CNC** (Lista de corte) leva cada furo com o seu tamanho; os quadrados como quadrados (a 45°, rodados).
- Os acabamentos perfurados que já existiam ficam como estavam (furos redondos, malha reta, placas sem junta).

## 0.388.0 — 2026-11-04

**A página inicial arrumada de novo, e os documentos recentes com vistas.** (O dono: «a coluna de tutorial passa
também para a direita, e a do arquivo recente para a esquerda junto de abrir… a coluna de arquivos recentes preenche
todo o restante espaço, e deve ter opções de visualização dos arquivos recentes».)

- **Ordem das colunas:** à esquerda **Começar** e **Documentos recentes**; à direita **Tutoriais**, **Discussões no
  GitHub** e **Apoiadores**. Os recentes ficam com todo o espaço que sobra; as outras colunas, entre 200 e 260 px.
- **Três vistas** (os botões no canto da coluna): **miniaturas grandes**, **lista** (nome e pasta) e **detalhes**
  (nome, pasta, data de alteração, tamanho). Fica a última escolhida.
- **Ordem:** mais recentes, nome (A–Z) ou data de alteração. **Procurar…**: mostra só os que têm essas palavras no
  nome ou na pasta (acentos e maiúsculas à parte); em baixo, «1 de 5».
- **Um clique abre.** O **botão direito** num documento: Abrir, Abrir a pasta, Tirar da lista (o arquivo fica) e
  Limpar a lista toda — o **×** de cada linha saiu.
- Textos mais curtos nos botões, para caberem num ecrã de 1536 px: **Novo de arquivo base…**, **Abrir a pasta base**,
  **Abrir as Discussões**, **♥ Apoiar o ArqSynth**. As barras de rolagem da página passam às cores do tema (na
  grelha saíam pretas).

## 0.387.0 — 2026-11-04

**A página inicial.** (O dono, com a página de outro programa como referência: «à esquerda as opções de abrir novo,
carregar arquivo raiz ou arquivo de base, depois tutoriais, depois documentos recentes; no lado direito duas colunas
para Discussões no GitHub e apoiadores com o botão de apoiar. Depois vamos ligar esses botões».)

- Ao abrir o programa aparece o separador **Início**, com a página inicial; volta-se a ela por **Início ▸ Página
  inicial**. Enquanto está à frente, os painéis laterais afastam-se; voltam ao passar para o 3D.
- **Começar:** **Novo projeto**, **Abrir arquivo…**, **Novo a partir de arquivo base…** (um modelo: abre-se como
  projeto novo, e ao gravar pede outro nome — o arquivo base fica como estava). Os arquivos IFC da pasta
  **Documentos ▸ ArqSynth BIM ▸ Arquivos base** aparecem listados; o botão abre essa pasta.
- **Tutoriais:** os guias do próprio programa — Primeiros passos (Ajuda), as secções do TESTAR.md (paredes, perfil,
  cobertura por blocos, calhas, temas) e o GUIA.md — numa janela ao lado do trabalho; e o botão da lista de vídeos.
- **Documentos recentes:** os projetos abertos e gravados, os mais recentes primeiro, cada um com uma miniatura da
  vista; um clique abre, o **×** tira da lista (o arquivo fica); quantos se guardam (20, até 100).
- **Discussões no GitHub** e **Apoiadores** (com **♥ Apoiar o ArqSynth BIM**): por agora sem endereço — os botões
  dizem que estão por ligar. As ligações e listas estão em `arqbim/assets/start_page.json`.
- Também em Início ▸ Ficheiro: **Página inicial** e **Novo a partir de arquivo base…**.

## 0.386.0 — 2026-11-04

**Blocos da cobertura no 3D: cotas mais limpas, alças para escalar, «+» e «−» para as águas.** (O dono, com captura:
«tem como melhorar a aparência, principalmente da cota… somente um retângulo paralelo ao lado do beiral, e no meio
entende-se como a cota geral. Em vez de + para adicionar blocos, devia ficar alças para escalar o bloco. O + e − poderia
ficar para adicionar água e remover água».)

- **Cotas:** já não têm linhas de cota nem de chamada — só a **caixa com o valor, deitada ao longo do beirado** de cada
  água. A caixa **no meio do bloco** é a **altura geral**. Continuam a clicar-se para escrever.
- **Alças (quadrados) para escalar:** no meio de cada lado, arrastar estica esse lado; **nos quatro cantos**, arrastar
  escala o bloco pelos dois lados desse canto (o canto oposto fica).
- **«−» e «+» fora de cada lado:** **«−» tira a água** desse lado (fica empena); numa empena aparece **«+» que põe a
  água**. O «+» que acrescentava um bloco encostado saiu (os blocos acrescentam-se com a Cobertura «Por blocos»).
- Um clique dentro de uma caixa de cota escolhe a caixa, mesmo com uma pega por perto.

## 0.385.0 — 2026-11-04

**Os blocos da cobertura editam-se no 3D.** (O dono: «gostaria que a edição do bloco de telhado se desse no ambiente 3D
sem ser pela janela extra… abre a edição com 2 cliques, e podemos selecionar os blocos individualmente ou em grupo…
botões de edição acoplados nos blocos que permitam remover ou adicionar águas, aumentar a cota de um beiral, e do
bloco inteiro».)

- **Duplo clique** numa cobertura por blocos abre a edição na própria vista 3D (já não abre a janela), com o bloco
  clicado escolhido. Os contornos de todos os blocos aparecem; os escolhidos a azul forte.
- **Escolher:** clique num bloco; com **Shift** (ou Ctrl) junta-o ao grupo, ou tira-o.
- **Nos blocos escolhidos:**
  - um **quadrado no meio de cada lado**: um **clique troca água ⇄ empena**; **arrastado**, o lado sai ou entra (o
    oposto fica; sobre uma parede, encosta à face de fora);
  - um **losango no meio**: arrastado, **move os blocos escolhidos**;
  - um **«+» fora de cada lado** (com um só bloco escolhido): **acrescenta um bloco igual encostado a esse lado**, os
    lados que se tocam em empena — a cobertura continua;
  - **cotas**: a do **beirado de cada água** e a **altura do bloco**, medidas do piso. **Clique no valor, escreva e
    Enter.** Escrever um número sem clicar numa cota muda a altura dos blocos escolhidos (todos os beirados juntos).
- **Delete** apaga os blocos escolhidos (fica pelo menos um). Cada mudança é um passo de desfazer. **Esc** sai.
- A janela dos blocos continua em Propriedades ▸ «Editar blocos…», para os números (inclinações, avanço).

## 0.384.0 — 2026-11-04

**A calha à altura certa e ligada nos cantos.** (O dono, com captura de uma cobertura de quatro águas: «a calha está
muito baixa nesse tipo de telhado e não há ligação entre as calhas».)

- A calha ficava pendurada **por baixo** do beirado: o topo dela estava na aresta de baixo da testeira. Agora fica
  **encostada à testeira, com o topo 2 cm abaixo da aresta de cima da cobertura**, onde a água cai.
- **Calhas em beirados vizinhos ligam-se no canto:** ao pôr a segunda, as duas prolongam-se até ao canto de fora e
  cortam-se em meia-esquadria, como uma só calha a dobrar a esquina. Num canto para dentro, cortam-se onde se
  encontram. Um só passo de desfazer (**Ctrl+Z** separa-as outra vez).
- A prévia da ferramenta Calha mostra a calha em volume, à altura onde vai ficar, e diz «liga-se a 1 calha no canto»
  quando for o caso.
- As calhas já feitas antes desta versão ficam onde estavam: apague-as e volte a pô-las para ficarem à altura nova.

## 0.383.0 — 2026-11-04

**As prévias das paredes em volume.** (O dono, com capturas: «melhorar as prévias do desenho das paredes em
retângulo, círculo e arco, pois aparecem como 2 objetos separados, mas não se vê o volume».)

- Ao desenhar paredes por **retângulo**, **círculo**, **arco** ou pelo **contorno de uma face**, a prévia era só o
  contorno de baixo e o de cima — dois anéis soltos. Agora é **o volume das paredes**: as duas faces, o topo e as
  pontas, translúcidos e **sombreados** (o topo mais claro, os lados mais escuros conforme viram), com as **arestas
  verticais** nos cantos.
- A **parede reta** (ponto a ponto) usa a mesma prévia, para ser tudo igual.

## 0.382.0 — 2026-11-04

**Lajes e coberturas: as pegas também só a arrastar.** (O dono: «Sim, aplica» — o mesmo que no perfil da parede.)

- **Editar contorno** de uma laje e **Editar plataforma** do terreno: um canto move-se só com o botão carregado —
  carregue, leve, largue. Enquanto arrasta pode escrever a distância e **Enter**. Arrastar o losango do meio de um
  lado acrescenta um canto ali.
- Um **clique** num canto já não o pega: **escolhe-o** («Escolhido: Delete tira este canto»), e o **Delete** tira-o.
- **Coberturas por blocos** (pegas dos lados e do meio de cada bloco, com a cobertura selecionada): só a arrastar; um
  clique não move nada. A distância escrita durante o arrasto continua a funcionar.
- As outras pegas da ferramenta Selecionar (pontas de paredes, eixos, linhas, cortes, divisões de armários) ficam
  como estavam.

## 0.381.0 — 2026-11-04

**As curvas do perfil da parede já não se desfazem com um clique.** (O dono: «porque não está funcionando para as
curvas? tente descobrir».)

- **A causa** (vista num registo das teclas e do rato do lado do WSL, durante os gestos do dono): o Shift e o Alt
  chegavam bem. O arco ficava feito ao largar — e passa pelo rato, por isso a sua pega ficava mesmo debaixo do
  cursor. O clique seguinte no mesmo sítio **pegava no arco**, que passava a seguir o rato até ao clique seguinte,
  noutro lado da parede: o arco esticava todo torto. O mesmo com o canto da captura anterior.
- **Agora as pegas só se movem enquanto o botão está carregado** (arrastar e largar). Um clique simples numa pega
  não a pega: **escolhe-a** — **Delete** tira esse canto, ou endireita essa curva.
- A concordância (Alt + clique num canto) continua com o clique: o raio segue o rato até ao segundo clique ou ao
  **Enter** com o raio escrito.

## 0.380.0 — 2026-11-04

**O perfil da parede com gestos: arrastar, Shift, Alt.** (O dono: «o C ativa a cota… eu quero essa experiência:
clico 2x abre a edição e ao pegar os pontos ele cria vértices. Mas se pegar e clicar em Shift ele faz arco. Se clicar no
ponto e clicar na tecla Alt ele ativa a curva Bézier. Se clicar em Alt e clicar no ponto do canto, ele faz um fillet com
controlo do raio.»)

- **Sem modos nem letras.** As teclas C/A/B/R e os botões de modo da 0.378 saíram — o **C** volta a ser a **Cota**.
- **Arrastar o losango do meio de um lado:** um **canto novo** (um vértice) onde o largar.
- **Com Shift:** o lado faz-se **arco**, a passar pelo rato. **Com Alt:** uma **curva** (Bézier), a passar pelo rato;
  depois afina-se pelas duas tangentes. O Shift e o Alt podem carregar-se ou largar-se a meio do movimento — o desenho
  muda logo, sem mexer o rato.
- **Alt + clique num canto:** **concordância** (fillet) — o canto arredonda-se com um arco tangente aos dois lados. O
  raio é a distância do rato ao canto; ou escreva-o (ex.: `0,5`) e **Enter**. Clique (ou largue, se arrastou) para a
  fazer. Só num canto entre dois lados retos.
- Na barra por baixo da fita: «Arrastar losango: canto · +Shift: arco · +Alt: curva · Alt + clique num canto:
  concordância · Delete: tirar · Esc: sair».

## 0.379.0 — 2026-11-04

**O perfil da parede: o que se vê a meio do movimento.** (O dono, com captura: «fiz mas não funcionou».)

- Enquanto um canto ou uma curva se move, a vista mostra **só o contorno novo** (linhas azuis), como um esboço.
  Antes pintava todo o perfil novo de azul translúcido e deixava a parte que ia ser cortada no cinzento da parede —
  um recorte parecia um triângulo de parede, o contrário do que ia acontecer.
- Junto ao rato, as medidas dizem também **«largue ou clique para pousar»**: um canto pegado com um clique segue o
  rato até ao clique seguinte.

## 0.378.0 — 2026-11-04

**O perfil da parede, mais simples e direto.** (O dono: «precisa ser uma experiência mais simples e direta»,
«esperava ter que clicar numa tecla para alternar entre canto, curva, arco».)

- **Uma tecla para cada modo:** **C** canto, **A** arco, **B** curva, **R** reto (o Tab continua a passar de um
  para o outro). Enquanto edita o perfil, estas letras não abrem outras ferramentas.
- Na barra por baixo da fita, **Modo: Canto (C) · Arco (A) · Curva (B) · Reto (R)** — quatro botões lado a lado, o
  que está em uso aceso (antes era uma lista fechada).
- Ao entrar (duplo clique na parede), a vista 3D **vira-se de frente para a parede** e enquadra-a; ao sair (**Esc**)
  volta onde estava. Já não é preciso o F3.
- Os quadrados e os losangos **arrastam-se**: carregar, levar o rato, largar. (Clicar para pegar e clicar para
  pousar continua a funcionar.)
- **Curva:** arrasta-se pelo meio do lado, como o arco — a curva passa pelo rato; depois afina-se pelas duas
  tangentes.
- A mensagem de entrada e a linha de baixo dizem as teclas.

## 0.377.0 — 2026-11-04

**Os menus junto ao fundo do ecrã abrem para cima.** (O dono: «a lista fica escondida para baixo, devia subir acima» —
o menu da engrenagem descia para trás da barra de tarefas do Windows, que o Qt no WSL não sabe que existe.)

- A **engrenagem** (em baixo, à esquerda) abre a lista **para cima**, com o fundo da lista ao nível do botão.
- As listas dentro dela (**Paletas**, **Painéis**) sobem quando chegariam à barra de tarefas.
- O mesmo nos menus do **botão direito** na vista (seleção, cubo de vistas) e no **Navegador do Projeto**: perto do
  fundo do ecrã abrem para cima do rato.

## 0.376.0 — 2026-11-04

**Os temas à vista.** (O dono: «não consegui ver os temas, onde estão as opções?» — num ecrã de 1536 px o painel Tema
ficava dobrado na ponta direita da fita, e a engrenagem só tinha o claro e o escuro.)

- Um botão novo no **cabeçalho**, sempre à vista em qualquer separador: a **paleta** (entre a nuvem e o «?»). Abre
  Tema claro, Tema escuro, **Bege, Areia, Pedra, Escuro, Grafite**, **Explorar cores…** e Vistas escuras.
- Em **Visualizar**, o painel **Tema** passou para logo a seguir ao Aspeto.
- A **engrenagem** (em baixo, à esquerda) tem também as paletas, num submenu.

## 0.375.0 — 2026-11-04

**Arcos e curvas de Bézier no perfil da parede.**

- Na edição do perfil (duplo clique numa parede, ou Modificar | Paredes ▸ Editar perfil), a barra por baixo da fita
  tem **«Clique no meio de um lado»**: **Acrescenta um canto** (como até aqui), **Faz um arco**, **Faz uma curva
  Bézier** ou **Endireita o lado**. **Tab** passa de um para o outro.
- **Arco**: clique no losango do meio de um lado e leve o rato — o arco passa por esse ponto (um arco de volta
  perfeita, um arco abatido, um arco para dentro); clique para o pousar.
- **Bézier**: clique no losango do meio de um lado; aparecem as duas tangentes (losangos, com as linhas desde os
  cantos). Clique numa para a pegar e noutro sítio para a pousar.
- O ponto do arco e as tangentes movem-se como os cantos; ao mover um canto, as tangentes dele vão com ele.
  **Delete** com uma delas pegada endireita o lado.
- A parede faz-se com o arco e a curva lisos (sem riscos entre os troços), fica gravada no IFC com o desenho dos lados
  (reabre igual) e estica com a parede.

## 0.374.0 — 2026-11-03

**Ferramentas de arquitetura do addon do Blender (pelo inventário) e os temas do estudo de interface.**

- **A fita de Arquitetura do estudo** (`proposta-interface-arqsynth.html`):
  - **Paredes** — Parede e Fachada de vidro, e à vista **Retangular**, **Circular**, **Arco**, **Por face**,
    **Varinha mágica** (antes escondidas na barra de contexto);
  - **Aberturas** — Porta, Janela, Abertura na parede, Abertura na cobertura e **Nicho**;
  - **Pisos e coberturas** — Laje, Cobertura, **Piso**, Teto, **Calha**;
  - **Circulação** — Escada, Rampa, **Elevador**, Guarda-corpo;
  - **Ambientes** — Ambiente, **Separador**, **Identificar**, **Áreas**;
  - os revestimentos e perfis num painel à parte.
- **Parede pela varinha mágica** (o «wall_magic_wand» do addon): arraste uma janela sobre as duas linhas de uma parede
  num desenho (DWG/DXF ligado ou linhas de esboço): a parede fica entre elas, com a espessura medida.
- **Nicho**: na face de uma parede, um retângulo com a profundidade da barra (10 cm por omissão) — um rebaixo IFC
  que acompanha a parede.
- **Piso**: o revestimento de piso de um ambiente (clique dentro), de um retângulo ou de um polígono — cerâmico,
  madeira, pedra, vinílico ou betão afagado (IfcCovering FLOORING, com espessura e material nas quantidades).
- **Calha**: passe o rato por uma cobertura (mostra o beirado mais próximo) e clique: a calha corre ao longo dele,
  por fora (IfcPipeSegment GUTTER, alumínio).
- **Elevador**: a caixa e a cabina (IfcTransportElement), num clique, do pavimento ativo até acima do último;
  R roda 90°.
- **Separador**: linhas que dividem ambientes sem parede (contam para os ambientes, não para lajes ou coberturas);
  os ambientes do pavimento acompanham.
- **Identificar**: um ambiente em cada espaço fechado do pavimento que ainda não tem, numerados.
- **Áreas**: a área útil (dos ambientes) e a área bruta (por fora das paredes) de cada pavimento, numa tabela.
- **Guarda-corpo num vão**: forma nova do Guarda-corpo — um clique numa janela ou porta, de batente a batente.
- **Temas do estudo** (Visualizar ▸ Tema): **Bege**, **Areia**, **Pedra**, **Escuro** e **Grafite**, com as nove cores
  do estudo — barras, fita, painéis (títulos tingidos do azul do estudo), destaque, texto, área de desenho, divisórias e
  campos. **Explorar cores…** afina cada uma (pelo seletor ou pelo código) e guarda a sua paleta neste computador;
  «Copiar paleta CSS» e «Repor bege», como no estudo. As folhas e o PDF continuam em papel branco.

## 0.373.0 — 2026-11-03

**Desenho livre como no SketchUp: uma linha sozinha, Offset de linhas, Arco, Linha livre e Curvas de Bézier.**

- **Uma linha sozinha (Selecionar)**: até aqui, um clique numa linha escolhia a cadeia inteira (todas as linhas
  desenhadas de seguida). Agora é como no SketchUp:
  - **um clique** escolhe só a linha clicada (fica azul, com as pegas e a cota dela); um arco ou uma curva escolhe-se
    inteiro;
  - **dois cliques** escolhem a cadeia; **três**, tudo o que lhe está ligado (também de outras cadeias);
  - perto de uma linha, o clique vai para a linha, mesmo com uma face por trás;
  - numa cadeia já escolhida, um clique no meio de uma linha escolhe essa linha (arrastar o losango continua a mover
    o troço).
- Com uma linha escolhida: **Delete** apaga só ela; **Mover**, **Rodar**, **Copiar**, **Matriz** e **Ctrl+C / Ctrl+V**
  atuam só nela. Ao movê-la, as linhas ligadas às pontas esticam e continuam ligadas.
- As **faces escolhidas sozinhas** também se copiam (antes o programa recusava).
- **Offset (F)** em linhas: clique numa linha (ou escolha linhas antes e carregue em F) e afaste o rato para o lado,
  ou escreva a distância: aparece a paralela da cadeia, no seu plano, com os cantos vivos. Num arco, o arco paralelo
  com o mesmo centro. Um valor escrito logo a seguir corrige-a.
- **Arco (A)**, novo no painel **Desenhar** (separadores Modelagem e Massa):
  - **2 pontos e flecha** (como o do SketchUp): clique onde começa, onde acaba, e afaste o rato para curvar — prende
    em meia circunferência (magenta) e na tangente à linha de onde sai (azul-ciano); ou escreva a flecha (`0,5`) ou
    o raio (`2r`);
  - **Centro e ângulo**, **3 pontos** e **Setor** (fecha numa face), na barra de contexto;
  - os segmentos na barra (automático: um a cada 15°) ou escritos (`24s`);
  - um valor escrito logo a seguir corrige o arco.
- **Linha livre**: carregue e arraste; o desenho fica com os pontos onde dobra. Acabar onde começou faz uma face.
- **Curva de Bézier**: clique = ponto de canto; carregue e arraste = ponto suave, com a tangente para onde arrasta.
  Clicar no primeiro ponto fecha (uma face); Enter, Esc ou o botão direito acabam.
- Arcos, linhas livres e Béziers **fecham faces com as linhas já desenhadas**, como no SketchUp (um arco que acaba
  nas pontas de uma linha faz a face). A **Linha** também passa a fechar faces com linhas de outras cadeias.
- Uma curva escolhida mostra **pegas**: num arco, as pontas e o meio (continua um arco); numa Bézier, os pontos e as
  tangentes. As linhas ligadas às pontas acompanham.
- **Propriedades de um arco**: raio, ângulo e segmentos editáveis.
- As curvas ficam gravadas com o projeto e com o nome do que são («Arco 1», «Bézier 2»…).

## 0.372.0 — 2026-11-03

**A Linha fecha a face onde o contorno se fecha; as cotas temporárias com o aspeto novo do addon.**

- **Linha (L)**: até aqui, só fazia face quando se voltava ao **primeiro** ponto. Agora fecha-se como no SketchUp:
  - se a linha acabar num ponto do que já desenhou, ou a meio de uma das suas linhas, o laço que se formou vira
    **face**. O que ficou fora dele (por exemplo, um primeiro troço que não faz parte do contorno) fica como linha;
  - se a linha **atravessar** o que desenhou, o laço vira face e pode continuar a desenhar a partir do ponto onde
    clicou;
  - dois laços lado a lado são duas faces, com a aresta comum.
  - Desfaz-se tudo com um Ctrl+Z.
- Corrigida a face torta que aparecia quando, para fechar, se voltava ao primeiro ponto passando outra vez por um
  canto (ficava um triângulo a mais).
- Corrigida a mensagem da área da face («20,00 m m²» → «20,00 m²»).
- **Cotas temporárias** (a parede escolhida, e as do desenho) com o aspeto da versão nova do addon:
  - linhas finas azul-claro, contínuas, com setas;
  - cada valor em **branco numa caixa escura**, pousada sobre a sua linha e ao longo dela;
  - as distâncias às outras paredes com uma seta dupla **↔** antes do número;
  - a cota debaixo do rato fica mais forte, com a caixa azul;
  - o comprimento da parede fica mais afastado dela, como no addon.
  Clicar no valor continua a deixar escrever outra medida, e clicar na linha de uma distância continua a trocar entre
  eixo a eixo e face a face.

## 0.371.0 — 2026-11-03

**O modelo em USDZ, para a realidade aumentada no iPhone e no iPad.** Instalada, com o seu «sim», a biblioteca
usd-core 26.8 (o USD da Pixar, licença aberta; sem mais pacotes).

- **Início ▸ Exportar ▸ Exportar modelo 3D…** tem um tipo novo: **Realidade aumentada USDZ, iPhone e iPad (*.usdz)**.
- Mande o ficheiro para o iPhone ou o iPad (por e-mail, mensagem, AirDrop ou iCloud) e toque nele: abre-se sozinho,
  sem instalar nada.
  - Em **RA**, o modelo aparece pousado no chão ou na mesa, ao tamanho real. Com dois dedos, encolhe-se para uma
    maqueta.
  - Em **Objeto**, roda-se com o dedo.
- Leva o mesmo que o GLB:
  - as peças com os nomes do programa, por pavimento e categoria;
  - os materiais com a sua cor, transparência e acabamento: o vidro transparente, o metal a brilhar;
  - os dados de cada elemento (GlobalId, classe IFC, tipo).
- Abre-se também no Reality Composer da Apple, no Omniverse da NVIDIA, no Blender e no Houdini.

## 0.370.0 — 2026-11-03

**As tabelas em Excel (XLSX).** Instalada, com o seu «sim», a biblioteca openpyxl 3.1.5 (licença MIT).

- Os botões **Exportar (Excel, CSV)…** (eram «Exportar CSV…») gravam agora um **livro do Excel** por omissão, ou o
  CSV de sempre, escolhido no tipo, ao gravar. Estão nas **Tabelas**, na **Lista de armaduras**, nas **Quantidades da
  estrutura** e na **Lista de corte**.
- No livro do Excel:
  - os números são **números**: o Excel soma-os, ordena-os e faz gráficos com eles. Antes, no CSV, alguns chegavam
    como texto;
  - cada coluna tem as casas decimais que se viam na janela; as medidas têm pelo menos duas (5,00, não 5);
  - os códigos como «01» continuam texto, sem perder o zero;
  - os títulos das colunas vão a negrito, com filtro, e ficam fixos no topo quando se desce na folha;
  - as colunas têm a largura do que levam, e a folha tem o nome da tabela;
  - os totais vão no fim, como na janela.
- Se o ficheiro estiver aberto no Excel e não se puder gravar, o programa diz para o fechar.

## 0.369.0 — 2026-11-03

**A vista em DWG e em SVG** (os formatos, 4.º passo).

- **Início ▸ Exportar ▸ Exportar vista (DXF, DWG, SVG)…** (era «Exportar vista em DXF…»): o corte ou alçado que
  está à frente, senão a planta do pavimento ativo. Escolhe-se o formato no tipo, ao gravar:
  - **DXF**, como até aqui;
  - **DWG** (AutoCAD 2018): o mesmo desenho, convertido pelo ODA File Converter, o mesmo que o programa já usa para
    ler DWGs. Cada tipo de linha vai na sua camada, em metros. Sem o conversor instalado, o programa diz o que fazer;
  - **SVG**, para o Illustrator, o Inkscape e a internet: desenhado como nas folhas (tramas, espessuras, cotas,
    marcas dos alçados e o norte), à escala da vista e em milímetros, num papel do tamanho do desenho.
- **Corrigido o SVG das folhas** (desde a 0.128): a trama das paredes cortadas espalhava-se pela folha inteira, porque
  o gerador de SVG do Qt ignora os recortes. Agora as tramas, os padrões e as imagens de fundo são recortados pelo
  programa, só nos SVG. O PDF e o ecrã ficam como estavam.

## 0.368.0 — 2026-11-03

**Para o ArqSynth Presentation, 7.º passo (2.ª parte): panoramas 360°. Fecha a integração com o Presentation.**

- **Render ▸ Panorama 360°…** (novo, ao lado do Render realista): um panorama de 360° feito pelo render realista, a
  partir de onde está a câmara da vista 3D (de preferência dentro de uma sala, à altura dos olhos), a olhar a direito
  para onde ela olha.
  - Pede o nome, o tamanho (2048 × 1024 ou 4096 × 2048) e a qualidade.
  - São seis renders de 90° (à frente, à direita, atrás, à esquerda, para cima e para baixo) juntos numa só imagem
    equirretangular, a que os visualizadores 360° usam. Cada vista é feita um pouco mais larga e só se usa o meio,
    para as juntas não se verem.
  - Corre à parte, numa janela como a do render realista (a imagem vai ficando mais fina).
- O panorama **fica com o projeto**:
  - a imagem (JPEG) numa pasta ao lado dele, «<projeto> - panoramas»;
  - o sítio de onde foi tirado e o piso, no ficheiro do projeto. Criar e remover desfazem-se com Ctrl+Z.
  - Por isso pede-se para **guardar o projeto primeiro**, e só se faz no **3D em perspetiva**.
- O **painel Apresentação** tem uma lista **Panoramas 360°**, com **Novo…** e **Remover**.
- O **pacote para o Presentation** leva os panoramas: cada um como um **ponto 360° nas plantas do seu piso**, no
  sítio onde a câmara estava. A mensagem final diz quantos foram.
- **No Presentation** (ramo `integracao-arqsynth-bim`): o botão **ArqSynth BIM** põe cada panorama como um ponto 360°
  da página da planta (abre a imagem no visualizador 360° do Presentation).
  - Importar outra vez atualiza o ponto (o sítio, o nome, a imagem) e tira os que o BIM já não manda.
  - Os pontos feitos à mão no Presentation ficam. Isto também corrige a 0.367: ao importar outra vez, os pontos de
    uma planta perdiam-se, porque o PDF novo é outro ficheiro.
- **Corrigido no Presentation** (falha antiga, encontrada nesta versão): ao guardar os pontos de uma planta, o
  Presentation apagava, passados 10 minutos, as imagens dos pontos (360° e fotografias) de todas as **outras**
  plantas do mesmo projeto. Agora conta os pontos de todas as plantas, e se não os conseguir ler todos não apaga
  nada.

## 0.367.0 — 2026-11-03

**Para o ArqSynth Presentation, 7.º passo (1.ª parte): o pacote, com as folhas como plantas.**

- **Início ▸ Exportar ▸ Para o ArqSynth Presentation…** (e o botão do painel Apresentação) grava agora, por omissão,
  um **pacote**: um ficheiro ZIP com tudo o que vai para a apresentação:
  - o **modelo** (o GLB de sempre, com as cenas, os movimentos, o sol, os materiais e os ambientes);
  - cada **folha** do projeto que tenha vistas, como um **PDF de uma página**, desenhado como no PDF das folhas;
  - nas folhas com plantas, os **ambientes como zonas da página**: o contorno de cada um no sítio da planta, com o
    nome, o número e a área. Um ambiente cortado pela região de recorte da planta fica de fora.
- No diálogo de gravar continua a haver **Só o modelo 3D (*.glb)**, para o importar numa página 3D como até aqui.
- **No Presentation** (ramo `integracao-arqsynth-bim`): na lista de páginas há um botão novo, **ArqSynth BIM**.
  Escolhe-se o pacote e o Presentation:
  - faz a **página 3D** com o modelo; se já houver uma do BIM, atualiza-a («Atualizar»: o que se fez lá fica);
  - faz uma **página de planta por folha**, com o PDF e uma camada **Ambientes** (um polígono por ambiente, da cor do
    seu tipo, com o nome e a área).
- Importar o pacote outra vez atualiza essas páginas no lugar (o PDF e os ambientes). Fica o que se fez nelas no
  Presentation: o título, a rotação, as outras camadas. As páginas próprias do Presentation não são tocadas.
- Os panoramas 360° do render realista são a 2.ª parte deste passo (a seguir).

## 0.366.0 — 2026-11-03

**Para o ArqSynth Presentation, 6.º passo: os ambientes e o Passeio Virtual.**

- O pacote leva agora os **ambientes** do projeto (os IfcSpace): o contorno de cada um à cota do chão, o nome, o número,
  a área e o tipo. O tipo sai do nome: cozinha, quarto, casa de banho, corredor, hall, entrada, varanda, terraço,
  garagem, zona técnica; senão sala. Leva também os **pavimentos** que os têm, as **portas** que os ligam (o meio de
  cada porta e o lado de onde se vem; uma porta para a rua tem só um ambiente) e as **escadas** entre pisos (do pé à
  cabeça).
- No Presentation, o importador faz com isso:
  - **etiquetas** de cada ambiente, deitadas no chão, no meio dele: o nome, o número e a área («16,00 m²»);
  - o **Passeio Virtual**: um piso por pavimento, uma zona por ambiente com o seu tipo, um **fluxo por cada porta**
    entre dois ambientes (do meio de um ao meio do outro, a passar a direito pela porta) e uma **ligação por cada
    escada**. O passeio começa no ambiente por onde se entra da rua, e a visita guiada passa por todos. O editor do
    Presentation encontra sozinho o caminho de um ambiente a qualquer outro, também de um piso para outro.
- Num «Atualizar», as etiquetas e o passeio que já tiverem sido afinados no Presentation ficam como estão; só entram
  os ambientes, as portas e as escadas novos.
- No painel **Apresentação**, por baixo da lista, ficam **Etiquetas dos ambientes** e **Passeio Virtual pelos
  ambientes**, com o número de ambientes. Desligados, não vão (cada escolha desfaz-se com Ctrl+Z).

## 0.365.0 — 2026-11-03

**Para o ArqSynth Presentation, 5.º passo: o ambiente e os efeitos.**

- No painel **Apresentação**, cada cena tem agora:
  - o **Sol (dia e hora)**: o do lugar do terreno nesse dia, a essa hora;
  - a **Animação do sol**: parado, **ao longo do dia** (do nascer ao pôr) ou **ao longo do ano** (os doze meses a essa
    hora: o sol mais alto e o mais baixo);
  - a **Exposição** (de 0,3 a 1,6; 1 é a do Presentation);
  - o **Céu atrás do modelo** (desligado: o fundo liso do Presentation).
- **Ver sol** mostra no 3D o sol desse dia e dessa hora, com as sombras, e a barra azul diz o azimute e a altura. Com
  animação, passa o dia ou o ano em 8 s. Outra vez, ou **Esc**: o sol do estilo de vista. O sol é calculado como o
  Presentation o calcula (comparado com o código dele em 100 lugares, dias e horas: iguais). Sem o lugar do terreno,
  os campos do dia e da hora ficam desligados e o painel diz onde o dar (**Terreno ▸ Localização**).
- **Os acabamentos dos materiais seguem para o Presentation:**
  - o **vidro** e o **vidro fosco** passam a ser vidro lá (transparente com reflexos, ou fosco);
  - a **água** é um acabamento novo, e há um material novo, **Água (piscina, lago)**, para uma laje ou um esboço. No
    Presentation fica água animada; no render realista do BIM, uma superfície que refrata como a água;
  - as **luminárias** brilham lá, com luz quente, mais fortes e de mais alcance quanto mais lúmenes têm (um painel de
    3600 lm mais do que um foco de 800).
- No Presentation, o importador põe o sol, a exposição e o céu em cada cena, e os vidros, a água e as luzes como
  ajustes de material da página (o GLB não muda). Num «Atualizar», os materiais que já tinham sido afinados lá ficam
  como estão; só entram os que faltam.

## 0.364.0 — 2026-11-03

**Para o ArqSynth Presentation, 4.º passo: os movimentos de câmara**, escolhidos aqui e vistos no 3D antes de exportar.

- No painel **Apresentação**, cada cena tem agora um **Movimento**: os 21 da biblioteca do Presentation, com os mesmos
  nomes e nos mesmos grupos:
  - **Exterior**: órbitas de 90°, 180° e 360°, órbita ascendente e descendente, contorno de fachada;
  - **Aéreo**: voo perimetral, descida de aproximação;
  - **Cinematográfico**: aproximação, recuo com revelação, deslocamento lateral, subida de fachada, vista principal;
  - **Interior**: espirais, volta e contorno do compartimento, aproximação, recuo, deslocamentos lateral e vertical.
- Ao lado escolhe-se o **tempo** do movimento (por omissão, o que o Presentation lhe dá).
- Os movimentos fazem-se com as medidas do edifício (o meio, o tamanho). Os de **interior** fazem-se dentro de um
  **Ambiente**: o escolhido, ou, em «O da cena», o que a vista 3D tem à frente (senão o maior do pavimento ou do
  projeto).
- **Ver movimento** mostra-o no 3D como o Presentation o vai tocar, ao mesmo ritmo; no fim, ou com **Esc** ou
  **Parar**, a câmara volta onde estava.
- O pacote leva o nome do movimento, o tempo e as medidas de onde foi feito. O importador do Presentation faz o
  movimento com a sua própria biblioteca, a partir dessas medidas: nasce lá igual ao que se viu aqui e toca ao entrar
  na cena. Os 21 movimentos do BIM dão os mesmos pontos, alvos, tempos e curvas de velocidade que os do Presentation
  (comparados um a um com o código dele).
- O painel ficou com a ficha da cena num quadro que se desloca, para a lista das cenas não ficar com uma só linha num
  ecrã baixo.
- **Corrigido (da 0.363):** ao abrir, o painel alargava a coluna da esquerda e o 3D ficava mais estreito (614 → cerca
  de 500 px numa janela de 1280), e assim ficava mesmo depois de o fechar. Agora cabe na largura dos outros painéis: num
  painel estreito, os rótulos passam para cima dos campos, e os nomes compridos veem-se inteiros na lista que se abre.

## 0.363.0 — 2026-11-03

**Para o ArqSynth Presentation, 3.º passo: o painel Apresentação.** As cenas preparam-se aqui e seguem prontas.

- **Render ▸ Cenas da apresentação** abre o painel **Apresentação** (à esquerda, ao lado do Navegador). Lista as cenas
  que vão para o Presentation, pela ordem da apresentação, cada uma com a sua miniatura:
  - a vista geral, cada vista 3D com nome, a planta de cada pavimento e cada corte;
  - **a ordem**: arrastar na lista, ou **Subir** / **Descer**;
  - **duplo clique** abre a vista da cena (a vista geral: o 3D visto de onde o Presentation a mostra).
- Para a cena escolhida:
  - **Cena de entrada**: a apresentação abre nela;
  - **Fora da apresentação**: a cena vai na mesma, mas fica de lado no Presentation (não entra na sequência que o
    cliente vê);
  - **Chegada**: voo suave (com a duração) ou corte seco;
  - **Efeito**: sol ao longo do dia, construção peça a peça, ou explosão, com a duração;
  - **Tempo na cena**: quanto tempo fica no passeio automático («automático»: o do Presentation);
  - **Legenda**: o texto que aparece por baixo da cena no passeio narrado.
- Cada escolha é um passo de Ctrl+Z e fica guardada com o projeto, junto às vistas.
- **Miniaturas**: o programa passa pelas cenas uma a uma, tira uma imagem pequena de cada vista (como a Imagem da vista)
  e volta à vista em que estava, com as abas como estavam. Ao exportar para o Presentation tira-as de novo, para irem
  como as vistas estão nesse momento.
- **O pacote** (Início ▸ Exportar ▸ Para o ArqSynth Presentation…) leva tudo isto: a ordem, a entrada, as de fora, a
  chegada, o efeito, a legenda, o tempo e a miniatura de cada cena.
- **No Presentation** (ramo `integracao-arqsynth-bim` do código dele): o importador lê estas escolhas e faz as cenas com
  elas; as miniaturas sobem para o armazenamento como as que o editor tira ao criar uma cena. Num «Atualizar», as cenas
  que já lá estavam ficam como estão (e com a sua miniatura); só as novas trazem o que veio do BIM.
- **Corrigido (da 0.362):**
  - a **vista geral** estava por baixo do modelo, do lado nordeste. Agora vê de cima, de sudoeste, como devia;
  - a cena de um **corte** era conhecida pela posição do corte na lista: apagar um corte trocava as cenas dos outros. Cada
    corte tem agora um número próprio, que fica quando muda de nome (os cortes de ficheiros antigos ganham-no ao abrir).
- O importador do Presentation (0.362) foi verificado com o Node 24, instalado no WSL: os testes dele, a verificação de
  tipos do projeto inteiro e o lint passam.

## 0.362.0 — 2026-11-03

**Para o ArqSynth Presentation, 1.º passo: o pacote** (pedido do dono: «cenas 3D, cortes, animações, efeitos etc.
podia ser preparada aqui no BIM e depois migrada para a plataforma de apresentação»).

- **Início ▸ Exportar ▸ Para o ArqSynth Presentation…** (também em Render ▸ Apresentação) grava o modelo todo num GLB
  com a apresentação lá dentro:
  - **uma camada por elemento**, com o pavimento e a categoria para as pastas. Cada camada leva o número do elemento
    (GlobalId), igual de uma exportação para a outra: ao mandar o modelo outra vez, as cenas e as fichas feitas no
    Presentation continuam a apontar para os mesmos elementos;
  - **as cenas**:
    - a **vista geral**, de sudoeste e de cima;
    - cada **vista 3D com nome**: a câmara, as categorias escondidas e a caixa de corte;
    - a **planta de cada pavimento**: vista de cima, com o norte para cima, cortada à altura de corte, e os outros
      pavimentos escondidos;
    - cada **corte**: o plano e a câmara a olhar para ele;
  - **o sol**: pelo lugar do terreno, quando está dado; senão, a direção do estilo de vista.
- A descrição vai dentro do próprio GLB, no envelope de troca da marca, o mesmo do ArqSynth Concept. Diz o que se quis
  (uma câmara, um corte, uma categoria escondida), não o modo como o Presentation o guarda, para que uma versão nova
  do Presentation continue a ler ficheiros antigos.
- Os nomes dos nós do GLB são únicos e já no formato que o motor 3D do Presentation (three.js) lhes dá, para as
  camadas os encontrarem.
- **Falta o outro lado:** o Presentation de hoje abre este GLB como um modelo qualquer (faz as camadas dele). Para
  trazer as cenas é preciso o importador, que é o passo seguinte.
- **Corrigido (da 0.361):** no 3D, a linha verde de uma relação passa no chão e pode cair no ecrã por cima de outra
  parede. Um clique nessa parede trocava eixo/face em vez de a escolher. Agora a linha só troca onde está à vista, e
  enquanto um comando pede elementos o clique escolhe sempre.

## 0.361.0 — 2026-11-02

**A cota temporária da parede: a relação com as outras paredes** (pedido do dono: «ao selecionar a parede, aparece a
cota da extensão da parede, mas não aparece a relação da parede com outras paredes»).

- **Com uma parede escolhida,** além do comprimento, aparecem as cotas até às paredes à volta (a verde):
  - **de lado**: até à parede paralela mais próxima de cada lado, também as interiores (antes só contavam paredes à
    mesma cota de base e exatamente paralelas; agora até 1° de diferença e 1 m de base);
  - **para lá de uma ponta solta**: da ponta até à primeira parede à frente (a passagem que fica). Uma ponta ligada a
    outra parede não tem cota.
- **Eixo a eixo ou face a face:** em **Modificar | Paredes ▸ Cotas temporárias** (o separador verde), ou com um clique
  na linha de uma cota verde, que troca de uma para a outra. Face a face dá os vãos livres. A escolha fica gravada
  para a próxima vez.
- **Escrever por cima:** clicar no número de uma cota verde e escrever muda-a. A de lado mexe a parede; a da ponta
  solta estica ou encurta a parede até lá. Enquanto se escreve, o número aparece na própria cota, entre [ ].
- **O aspeto, como no addon do Blender:**
  - o comprimento a âmbar e as relações a verde-azulado, com a linha a tracejado e setas abertas;
  - o número ao longo da linha (nas verticais, lê-se de baixo para cima), e no 3D virado para a câmara;
  - a cota debaixo do rato realça-se;
  - no fundo escuro, amarelo e verde, como no Blender.
- As relações de lado medem-se a 20 % da parede, para o número não tapar o do comprimento, que fica a meio.

## 0.360.0 — 2026-11-02

**O gerador de símbolos** (6.º ponto do documento do dono, 2.ª parte: «definir como será a aparência dos símbolos
usados dentro do programa, seja do corte, da vista, dos detalhes»).

- **Anotar ▸ Símbolos…** (também em Visualizar, ao lado dos Estilos gráficos): uma janela com um separador por
  símbolo, cada um desenhado ao lado e a mudar com cada escolha:
  - **Corte**: a cabeça (círculo, quadrado ou nenhuma), a seta (cheia, vazada ou nenhuma), o raio da cabeça, a altura
    do texto, a linha (traço-ponto, tracejada, contínua ou só nas pontas) e a caneta;
  - **Alçado (vista)**: a cabeça, a seta, os tamanhos e a caneta;
  - **Pormenor**: a cabeça da chamada, a linha da caixa, os tamanhos e a caneta;
  - **Nível**: a marca (triângulo, círculo em quartos ou nenhuma), a linha, os tamanhos e a caneta.
- **Os de sempre** repõe os símbolos como eram até aqui.
- As medidas são as do papel (mm). A planta e os cortes no ecrã, as folhas, o PDF e o DXF desenham os símbolos assim.
- Ficam no estilo gráfico do projeto, gravados com ele. Ctrl+Z desfaz a mudança toda de uma vez.

## 0.359.0 — 2026-11-02

**A porta em planta** (8.º ponto do documento do dono).

- **As peças separadas:** na planta, a porta deixa de se desenhar pelo corte do corpo 3D, que juntava tudo numa massa.
  Passa a desenhar-se pelo seu desenho: os dois **aros**, as **guarnições** de cada face e a **soleira**, cada um com o
  seu contorno e a trama do seu material. Vale para a planta no ecrã e para as folhas.
- **Sem a folha a dobrar:** antes via-se a folha fechada (do corte 3D) e também a folha aberta (do símbolo). Agora:
  - **aberta** (como até aqui): a folha aberta e o arco, sem nenhuma folha no aro;
  - **fechada**: a folha no aro, e a abertura mostrada só pela linha simbólica (o arco e uma linha fina onde abre).
- **Caixilho Studio ▸ Planta…** (nas portas): a janela nova com a porta desenhada em planta ao lado, que muda com cada
  escolha:
  - **Em planta**: aberta ou fechada, com a linha de abertura;
  - **Linha de abertura**: contínua ou tracejada;
  - as **guarnições** (quanto entram na parede, a espessura, em que faces) e a **soleira**;
  - a largura do aro é a do Studio.
- **A colocar uma porta:** a pré-visualização desenha a folha aberta e o arco de abertura.
  - Abre para a face da parede onde está o rato; **F** troca o lado, como já fazia.
  - **Espaço** passa as dobradiças para o outro aro, como no Revit.
  - Um clique fixa-a assim, numa só anulação.
- **Com uma porta escolhida,** aparecem duas **setas** ao lado dela, cada uma com um losango para clicar:
  - a seta ao longo da parede, em frente da porta, passa as dobradiças para o outro aro;
  - a seta atravessada, ao lado, faz a porta abrir para o outro lado.

  Numa janela aparece só a do lado.
- **Ainda do 6.º ponto, para depois:** a aparência das linhas e dos símbolos do corte e o gerador de símbolos.

## 0.358.0 — 2026-11-02

**A linha de corte editável na planta** (documento do dono «O que precisa corrigir e melhorar», 6.º ponto, 1.ª parte).

- **Um clique na cabeça de um corte** (o círculo com a seta) escolhe-o. Aparece um quadrado em cada ponta da linha e um
  losango ao lado, a meio, para onde o corte olha.
- **Arrastar um quadrado** estica ou encurta a linha por essa ponta, ao longo dela (fica pelo menos com 20 cm). A
  linha passa a ter as suas pontas; até aqui atravessava sempre o edifício todo.
- **Clicar no losango** vira o corte para o outro lado (a mesma linha, as setas ao contrário).
- O duplo clique na cabeça continua a abrir a vista do corte. Um clique noutro sítio larga o corte. Cada mudança
  desfaz-se com Ctrl+Z e fica gravada com o projeto.
- **Fica para a versão seguinte:** a aparência das linhas e dos símbolos, e o gerador de símbolos (corte, vista,
  pormenor…).

## 0.357.0 — 2026-11-02

**«Ambiente» em vez de «Sala», e o programa de necessidades** (7.º ponto do documento).

- A ferramenta chama-se agora **Ambiente**, e o mesmo em todo o programa: «Ambientes e tetos», «Cotar ambientes»,
  «Ambientes: quadro de áreas», as mensagens… «Sala» só fica como uso de um ambiente (sala de estar).
- **Interior ou exterior:** nas Propriedades de um ambiente, a linha nova «Interior ou exterior» (terraço, varanda,
  pátio…). No IFC é o tipo EXTERNAL / INTERNAL e o `IsExternal` do Pset_SpaceCommon.
- **Programa de necessidades** (Arquitetura ▸ Ambientes e tetos ▸ Programa de necessidades): um painel ao lado do
  Navegador do Projeto.
  - **Importar…** lê um CSV (como uma folha de cálculo o grava) ou um texto com um ambiente por linha:
    `nome; área; quantidade; interior/exterior`. Tudo menos o nome é opcional; a primeira linha de títulos salta-se.
  - **Arrastar um nome** para dentro de um espaço da planta faz lá o ambiente com esse nome (e exterior, se o programa
    o disser). Largado num ambiente que já existe, muda-lhe o nome.
  - Ao lado de cada nome: a área prevista, quantos estão feitos («1 / 1» a verde) e a área feita. Em baixo, os
    totais.
  - O programa fica guardado no IFC do projeto.

## 0.356.0 — 2026-11-02

**O telhado por blocos mais à mão** (5.º ponto do documento).

- **Duplo clique num telhado por blocos** (escolhido) abre o editor de blocos já no bloco clicado.
- No editor, a linha nova **Altura do bloco**: a altura do seu beirado mais baixo. Mudá-la sobe ou desce o bloco
  inteiro (todos os beirados juntos).
- A altura de cada beirado e a inclinação de cada água continuam em «Lados», uma linha por lado (N, E, S, O), e podem
  ser diferentes umas das outras.
- O addon ArqSynth Modeler (no disco D:, que não estava ligado) não pôde ser consultado. Se o dono quiser o telhado
  igual ao do addon, é preciso voltar a ligar o disco.

## 0.355.0 — 2026-11-02

**Duplo clique numa parede: o perfil** (4.º ponto). Dois cliques seguidos numa parede (a primeira já escolhida
sozinha) abrem a ferramenta Perfil da parede com ela. Numa parede de um grupo, o segundo clique continua a escolher só
essa parede.

## 0.354.0 — 2026-11-02

**TAB, a edição rápida** (3.º ponto: «Vamos adotar a tecla TAB para edição rápida dos elementos»).

- Com um elemento escolhido (ferramenta Selecionar), **TAB** abre uma janelinha por cima da vista, ao lado dele: o
  tipo em cima e as **restrições e dimensões**. Numa parede: o comprimento, a base (pavimento e deslocamento), o topo,
  a altura e o botão do perfil. Numa porta ou janela, numa laje, num telhado: as suas.
- Cada mudança desfaz-se com Ctrl+Z, e a janelinha fica aberta a mostrar o elemento já mudado.
- Fecha com TAB outra vez, Esc, o ×, outra seleção, outra ferramenta ou um clique na vista. Dentro dela, TAB passa de
  um campo ao seguinte.
- Fica onde não tapa o elemento: à direita, à esquerda, por baixo ou por cima, dentro da vista.
- Nas ferramentas de desenho, o TAB continua a fazer o que fazia (a linha de referência da parede, rodar 90° um
  componente).

## 0.353.0 — 2026-11-02

**«+» nas pontas da parede** (2.º ponto). Uma parede reta escolhida sozinha mostra um **«+»** azul em cada ponta do
seu eixo. Clicar num deles passa à ferramenta Parede, do mesmo tipo e altura, a desenhar a partir dessa ponta: o
clique seguinte faz uma parede nova ligada à primeira nesse canto, e pode-se continuar como de costume (Esc acaba).

## 0.352.0 — 2026-11-02

**O reboco dá a volta às esquinas no 3D** (o 1.º ponto do documento do dono «O que precisa corrigir e melhorar»: «no
3D aparecem os materiais de núcleo, que não faz sentido, se em planta não é assim»).

- **Antes:** onde duas paredes se ligam em L, a que atravessa a esquina mostrava a ponta cortada pelas camadas
  (reboco, tijolo, reboco) no plano da fachada da outra. Aparecia uma faixa de tijolo de alto a baixo em cada esquina
  exterior: na vista 3D pintada por materiais, no render realista, nos alçados e no GLB, SKP e 3DM.
- **Agora:** a ponta de uma parede rente à face de uma parede ligada a ela leva o material dessa face, normalmente o
  reboco. Também não se desenha a linha de junta entre as duas a meio da fachada. A esquina fica como na planta e como
  o Revit limpa as ligações.
- **Não muda:**
  - a ponta de uma parede solta continua a mostrar as suas camadas;
  - as esquinas em meia-esquadria, as ligações em T e as paredes em fila já estavam certas.
- **Desempenho:** ao pintar muitos elementos de uma vez (o modelo inteiro num estilo por materiais, uma exportação,
  um desenho, um render), as camadas de cada parede leem-se uma só vez. No edifício de ensaio de 5001 paredes, pintar
  todas custa o mesmo que antes: 8,3 s.

## 0.351.0 — 2026-11-02

**Importar modelos 3D** (secção «Importação e exportação noutros formatos» do PLANO, passo 3).

- **Início ▸ Importar ▸ Importar modelo 3D…** (também em Gerenciar ▸ Componentes). Lê ficheiros do **SketchUp (SKP)**,
  do **Rhino (3DM)**, **glTF / GLB**, **OBJ** e **STL**.
- **Uma janela** mostra o ficheiro: os triângulos, os materiais e o tamanho em metros. Escolhe-se:
  - **como entra**: **componente** (mobiliário, louça sanitária ou genérico) ou **esboço**;
  - **o nome**;
  - **onde**, para um componente: **onde clicar** (fica na biblioteca e a ferramenta Colocar começa logo, com Tab para
    rodar 90°) ou **onde está no ficheiro** (nas coordenadas dele, útil para um terreno ou um edifício vizinho);
  - **a unidade e o eixo vertical**, só no OBJ e no STL, que não os dizem. O programa propõe uma unidade pelo tamanho
    e o tamanho mostrado acompanha a escolha.
- **Como componente**, o modelo fica um tipo IFC com a forma guardada uma só vez e **uma peça por material, cada uma
  com a sua cor** (e transparente, se for vidro). As cópias aparecem nessas cores na vista 3D. O mobiliário feito no
  programa continua com a cor da categoria.
- **Como esboço**, os triângulos do mesmo plano juntam-se em **faces inteiras**, para editar com Empurrar/Puxar ou
  fazer um componente. Uma face com furos fica nos seus triângulos, com as linhas entre eles escondidas.
- **O que se aproveita de cada formato:**
  - **SketchUp**: os grupos e componentes onde estão, com a cor dos materiais. Só a frente de cada face: o verso
    pintado de outra cor ficaria sobreposto;
  - **Rhino**: as malhas e as superfícies, pelas malhas que o Rhino guarda no ficheiro. Uma superfície gravada sem
    malha fica de fora e a janela diz quantas. Os blocos entram onde estão (também blocos dentro de blocos), com o
    material ou a cor do objeto ou da camada, na unidade do ficheiro;
  - **glTF / GLB**: em metros, com a cor base dos materiais;
  - **OBJ**: com os materiais do MTL;
  - **STL**: sem cores.
- **Tempos:** o edifício de ensaio inteiro (2161 elementos, 238 mil triângulos) lê-se em 6,7 s do SKP, 5,1 s do 3DM e
  3,2 s do GLB. Fica componente em 1,5 s, ou esboço de 100 mil faces em 2,7 s.
- O glTF, o OBJ e o STL leem-se com o **trimesh**, que já veio instalado com o OpenSKP na 0.350.

## 0.350.0 — 2026-11-02

**SketchUp e Rhino** (secção «Importação e exportação noutros formatos» do PLANO, passo 5, autorizado pelo dono a
2026-11-02 com as bibliotecas novas: rhino3dm 8.17 e OpenSKP 1.4, ambas MIT).

- O **Exportar modelo 3D…** grava também **SKP** (SketchUp) e **3DM** (Rhino). Escolhe-se o formato na janela de gravar,
  como os outros.
- **SketchUp:**
  - cada elemento é um **grupo** com o nome dele;
  - a **etiqueta** (tag) é «Pavimento - Categoria», por exemplo «Térreo - Paredes». Este formato não tem pastas de
    etiquetas;
  - os **materiais** levam o nome, a cor e a transparência, e vão nos dois lados de cada face;
  - os **dados de cada elemento** (GlobalId, classe IFC, tipo, pavimento, categoria) ficam no dicionário de atributos
    «ArqSynth» do grupo;
  - as **faces vão inteiras**, não em triângulos: os triângulos do mesmo plano que se tocam juntam-se numa face, com
    os furos que tiver. O SketchUp mostra as arestas que um arquiteto desenharia. No edifício de ensaio, 238 mil
    triângulos dão 70 mil faces.
- **O formato do SketchUp** é o de 2013 a 2020, que todas as versões abrem (a mais recente converte-o ao abrir).
  O SketchUp não tem biblioteca oficial para Linux; o OpenSKP lê e grava sem ela.
- **Rhino:**
  - **camadas** por pavimento, com uma subcamada por categoria («Térreo::Paredes»), na cor da categoria;
  - cada elemento é uma malha por material, com o nome dele, agrupada quando tem vários materiais;
  - os **dados** vão no Attribute User Text do objeto;
  - os **materiais** levam o nome, a cor, a transparência e o brilho do acabamento;
  - formato da versão 6, que o Rhino 6, 7 e 8 abrem.
- **As duas** gravam em metros (o SketchUp guarda polegadas por dentro, mas mostra as unidades do modelo), com Z para
  cima e nas coordenadas do próprio modelo, sem deslocar para a origem: assim batem com o IFC.
- **Tempos** no edifício médio de ensaio (2161 elementos, 237 mil triângulos), depois de 2,2 s a reunir as faces: SKP em
  6,0 s (19,8 MB) e 3DM em 5,8 s (7,4 MB). Os dois foram lidos de volta pelas mesmas bibliotecas, com a área do modelo
  inteira.

## 0.349.0 — 2026-11-02

**OBJ e STL** (secção «Importação e exportação noutros formatos» do PLANO, passo 2).

- O botão passa a chamar-se **Exportar modelo 3D…** (Início ▸ Exportar e Render ▸ Apresentação). O formato escolhe-se
  na janela de gravar:
  - **GLB**, como na 0.348;
  - **OBJ**, com os materiais num ficheiro MTL ao lado: abre em quase todos os programas 3D (SketchUp, 3ds Max,
    Rhino, Blender, Cinema 4D…). Cada elemento é um objeto, com o nome «Pavimento/Categoria/elemento»; os materiais
    levam a cor, a transparência e o brilho do acabamento. Y para cima e chegado à origem, como o GLB;
  - **STL**, para **imprimir uma maqueta em 3D**: o modelo todo num só sólido, à escala que escolher (1:50, 1:100,
    1:200, 1:500), em milímetros como os programas das impressoras pedem, Z para cima e pousado no prato (z = 0),
    centrado.
- **Tempos** no edifício médio de ensaio (2161 elementos, 237 mil triângulos): OBJ 2,4 s (37 MB), STL 0,1 s (12 MB),
  depois de 2,4 s a reunir as faces.

## 0.348.0 — 2026-11-02

**Exportar o modelo 3D em GLB** (secção «Importação e exportação noutros formatos» do PLANO, passo 1; pedido do dono
a 2026-11-02, junto com a integração com o ArqSynth Presentation, que usa este formato).

- **Início ▸ Exportar ▸ Exportar modelo 3D (GLB)…** (também em Render ▸ Apresentação). Pergunta o que vai no
  ficheiro — o que está à vista, o modelo todo ou só a seleção — e grava um GLB (glTF 2.0). É o formato do ArqSynth
  Presentation, dos visualizadores na internet, do Blender, do Twinmotion e do SketchUp.
- **Organizado como no programa:** Modelo ▸ Pavimento ▸ Categoria (Paredes, Lajes, Portas, Janelas…) ▸ elemento,
  com os nomes que o programa mostra. Os esboços ficam numa pasta «Esboços».
- **Os materiais** chamam-se como no programa e levam a cor, a transparência (o vidro) e o acabamento do render
  realista (baço, acetinado, brilhante, metálico). As paredes saem cortadas pelas camadas: o reboco de cada lado tem o
  seu material.
- **Os dados de cada elemento** vão com ele: GlobalId, classe IFC, tipo, pavimento e categoria.
- **Na prática:** o modelo vai em metros, com o Y para cima (como o glTF pede), e chegado à origem. Um modelo nas
  coordenadas do levantamento perderia os milímetros; o desvio fica guardado no ficheiro.
- **Tempos:** a casa de exemplo grava em 0,04 s (153 kB); um edifício de 2161 elementos e 237 mil triângulos em 2,9 s
  (18,7 MB). Verificado num visualizador three.js: a árvore, os materiais, o vidro e as medidas como no programa.

## 0.347.0 — 2026-11-02

**O guia de todas as ferramentas** (pedido do dono a 2026-11-02: «documentação geral de todas as ferramentas para
poder testar»).

- **[GUIA.md](GUIA.md)** descreve todos os 201 comandos da fita, separador a separador e painel a painel. Para cada
  um diz onde está, a tecla, o que faz, como se usa e as teclas da ferramenta. Diz também em que secções do TESTAR
  há passos para o experimentar clique a clique.
- Abre com uma introdução: onde estão as coisas na janela, as regras que valem para todas as ferramentas, o primeiro
  percurso (uma casa até ao PDF) e as teclas. Cada separador tem um **percurso curto de teste**.
- O guia é feito pelo próprio programa (`scripts/guia_ferramentas.py`): os nomes e os textos são os mesmos que se
  veem nos botões. Faz-se outra vez a cada versão.
- **Dicas em todos os botões:** 78 comandos não diziam nada ao passar o rato (Abrir, Guardar, Verificação EC2/EC6,
  Memória de cálculo, Caixa de corte…). Agora todos têm a sua dica, que aparece também no painel Ajuda (F1).
- **De passagem:** cada render realista deixava a cena e a imagem numa pasta temporária que nunca se apagava. Agora a
  pasta vai-se quando se fecha a janela do render; antes disso, guarde a imagem com «Guardar imagem…».

## 0.346.0 — 2026-11-02

**A alvenaria por tipo de parede** (secção «Alvenaria por tipo de parede» do PLANO; pedido do dono a 2026-11-02).
Até aqui a alvenaria do cálculo era uma só para o projeto. Agora cada tipo de parede pode ter a sua: tijolo furado nas
fachadas, blocos de betão na cave, tijolo maciço num muro.

- **Em Gerenciar ▸ Tipos**, num tipo de parede, há o grupo **«Alvenaria para o cálculo (EC6)»**:
  - com **«Alvenaria própria deste tipo»** ligada, escolhem-se os blocos (cerâmicos, de betão, sílico-calcários,
    betão celular), o grupo, a resistência fb e a argamassa;
  - desligada, as paredes usam a do projeto (Estrutura ▸ Cálculo ▸ Ações e materiais), como até aqui; os campos
    mostram-na em cinzento.

  O γM fica sempre no projeto, porque vem da classe de execução da obra.
- **Fica no IFC**, nos parâmetros do tipo, e vale para todas as paredes desse tipo.
- **A verificação pelo EC6** usa a alvenaria de cada parede: a compressão, o corte e a flexão pelo vento (0.345).
  As notas dizem os blocos e de onde vêm, por exemplo «alvenaria de blocos de betão do grupo 1 (a do tipo): fb = 15,0
  N/mm², argamassa M10 → fk = 7,31 N/mm²».
- **O resumo** mostra o fk, ou o intervalo «3,66 a 7,31» quando há alvenarias diferentes. **A memória de cálculo**
  diz a do projeto e cada tipo com alvenaria própria.

## 0.345.0 — 2026-11-02

**As paredes de fachada à flexão pelo vento** (secção «Flexão das paredes para fora do plano» do PLANO; pedido do
dono a 2026-11-02). Até aqui o EC6 só verificava as paredes resistentes à compressão e ao corte no seu plano. Agora
cada parede de alvenaria da fachada — resistente ou de enchimento — é verificada à pressão do vento que a empurra para
fora do seu plano (NP EN 1996-1-1, 6.3 e Anexo E).

- **Quais:** as paredes de alvenaria exteriores. O programa já as marca sozinho (Exterior, pelas salas); as de betão
  ficam de fora.
- **O vento em cada parede**, por metro quadrado: 1,5 × a pressão de pico no topo da parede (pela zona e pelo terreno
  do projeto) × 1,1 a meio da fachada, ou × 1,4 perto das esquinas, onde a sucção é maior. As janelas e portas passam
  o seu vento ao pano à volta: uma parede com muitos vãos leva mais.
- **Os apoios de cada pano**, vistos no modelo:
  - a base, sempre;
  - o topo, se tem uma laje, viga ou cobertura em cima;
  - cada lado, se tem um pilar ou outra parede.

  Uma parede solta (um muro de jardim) fica apoiada só na base: em consola.
- **A resistência:** a da alvenaria à flexão (fxk1 e fxk2, pelos blocos e pela argamassa do projeto), aumentada pela
  compressão que a parede tem. O momento conta-se pelas linhas de rotura, de onde vêm os coeficientes do Anexo E, com
  os bordos simplesmente apoiados (do lado seguro).
- **O efeito de arco:** uma parede de tijolo só à flexão raramente chega, porque a alvenaria resiste pouco à tração.
  Presa em cima por uma laje ou viga e construída justa a ela, trabalha em arco dentro da sua espessura (6.3.2). O
  programa usa o arco quando a flexão não chega, com a nota «a parede justa, sem folga, à laje de cima».
- **Onde se vê:** em **Estrutura ▸ Verificar EC2/EC6**, uma linha para cada parede de enchimento, e as notas novas
  nas resistentes, junto às suas. Ficam também na memória de cálculo, com a linha da alvenaria à flexão.

  Numa casa de 6 × 4 m com paredes de 20 cm e laje, as quatro passam pelo arco (31 a 43 %). Um muro de jardim de
  2,80 m solto falha.
- **De passagem:** quando o modelo só tem lajes e paredes não resistentes, a janela dizia «A estrutura não se pode
  analisar: no_members». Agora diz «não tem pilares, vigas nem paredes resistentes».

## 0.344.0 — 2026-11-02

**Reabrir um modelo grande mais depressa** (secção «Transversal» do PLANO: as metas de desempenho). Medido no
edifício grande de ensaio: 45 MB, 18 001 elementos, 968 mil triângulos.

- **Reabrir até à 1.ª imagem**, com as formas guardadas: **1,9 s → 1,0 s**. Estimado para um IFC de 500 MB, passa de
  21 s para 12 s, dentro da meta (< 20 s). **Até poder editar:** 3,9 s → 3,1 s.

  O tempo ia em preparar as peças de desenho (as faces e as arestas de cada elemento), uma a uma: 12 000 vezes as
  mesmas contas pequenas. Agora fazem-se todas de uma vez, em blocos de 2000. O resultado é o mesmo, peça a peça.
- **Navegação:** 57 imagens por segundo, sem os picos de 44 ms que o ensaio mostrava. Esses picos não eram do
  programa: a placa gráfica do portátil abranda quando fica parada, e as 2–3 primeiras imagens depois de uma pausa
  levam ~40 ms. O ensaio passa a desenhar 5 imagens antes de medir.
- **Abrir pela 1.ª vez** (sem formas guardadas) continua a 2,9 s até à 1.ª imagem. Mais de metade é o IfcOpenShell a
  ler o ficheiro (1,5 s): para 500 MB, só a leitura levaria ~17 s. Esta meta depende do leitor de IFC.

## 0.343.0 — 2026-11-02

**O render realista** (secção «Render realista» do PLANO, os três passos; pedido do dono a 2026-11-01, com o «sim» à
biblioteca nova, o Mitsuba 3). Uma imagem fotográfica da vista: a luz do céu, do sol e das luminárias a ressaltar
nas superfícies, sombras suaves, vidro, brilhos. A **Imagem da vista** (0.329) continua a ser a rápida.

- **Render ▸ Render realista…** (o primeiro botão do painel Apresentação). Pergunta:
  - o **tamanho** (HD, Full HD, 2K, 4K; a proporção é a da vista) e a **qualidade** (rascunho, normal, alta);
  - a **iluminação**: sol e céu; sol, céu e luminárias acesas; ou noite, só com as luminárias;
  - o **sol**: o do estilo da vista, ou o do terreno num dia e hora (pela latitude e longitude do terreno, com a
    hora de verão). A janela diz onde fica o sol; abaixo do horizonte, o render é de noite;
  - a **exposição** (mais clara ou mais escura que a automática, em EV);
  - **Limpar o grão**, ligado de origem.
- **A janela do render** corre à parte: pode continuar a trabalhar. A imagem vai afinando em oito passagens, com a
  passagem, as amostras e o tempo. **Parar** acaba-o na hora e deixa a imagem como estava. **Guardar imagem…** grava
  em PNG ou JPEG.
- **Os acabamentos:** cada material tem um acabamento no render: baço, acetinado, brilhante, metálico, vidro ou vidro
  fosco. Escolhe-se no **editor de materiais** («Acabamento (render)»); de origem é o da sua categoria:
  - baços: betão, reboco, tijolo, gesso;
  - acetinados: madeira, pedra, plástico, e os perfis lacados das caixilharias;
  - brilhantes: azulejo, lacados, mármore polido, tampos de bancada;
  - metálicos: aço, alumínio, zinco, cobre.

  Fica no IFC, nos parâmetros do material («Acabamento»).
- **As luminárias acesas:** os painéis 60 × 60 (3600 lm) e os downlights (800 lm) do modelo iluminam, com a face de
  baixo tão clara quanto o seu fluxo, em branco quente. À noite o céu fica azul-escuro e as janelas acesas.
- **Os interiores:**
  - o sol entra pelo vidro sem os pontos brancos soltos;
  - visto de dentro, há mais ressaltos de luz;
  - o **filtro do grão** alisa o ruído sem esbater as arestas, as cores nem as sombras, guiado pela cor própria,
    pela normal e pela profundidade de cada face. Uma imagem limpa com poucas amostras.
- **Tempos** (16 núcleos), num edifício médio de ensaio (2161 elementos, 237 mil triângulos), em HD e qualidade
  normal: a cena prepara-se em 2,5 s; o render por fora leva 37 s e por dentro 86 s. Uma casa pequena vista por
  dentro, em 480 × 270, leva 11 s.

## 0.342.0 — 2026-11-01

**As paredes de betão armado pelo Eurocódigo 2** (secção «Paredes de betão pelo Eurocódigo 2» do PLANO, os dois
passos; pedido do dono a 2026-11-01). As paredes resistentes de betão já entravam no cálculo e recebiam as cargas
(0.335–0.336), mas não eram verificadas; agora são verificadas e armadas como os pilares, vigas, lajes e sapatas.

- **Tipos novos:** paredes de betão armado de 15, 20 e 25 cm (Gerenciar ▸ Tipos ▸ Paredes). Uma parede destes tipos
  nasce já **resistente** (Estrutural), ao contrário das de alvenaria, que se marcam à mão.
- **A verificação**, em **Verificar EC2/EC6**, por metro de parede (NP EN 1992-1-1):
  - a compressão no topo, a meio e na base, com a excentricidade das lajes e a mínima;
  - a esbelteza, com os efeitos de 2.ª ordem numa parede esbelta;
  - a **armadura vertical** nas duas faces, pelo diagrama N–M, entre o mínimo de 0,2 % e o máximo de 4 %, com
    espaçamento até 3t e 40 cm;
  - a **horizontal**, pelo menos ¼ da vertical e 0,1 %, até 40 cm;
  - o **corte no plano**: o betão sozinho, ou a armadura horizontal a levá-lo quando ele não chega, sem passar o
    VRd,max.

  Cada parede tem a sua linha, com as armaduras («vert. Ø8//0,25 · horiz. Ø8//0,40 (2 faces)») e as notas.
- **Pôr as armaduras no modelo** arma também as paredes:
  - as malhas vertical e horizontal nas duas faces (a horizontal por fora), interrompidas nas portas e janelas;
  - um varão Ø12 de reforço por face de cada lado de cada vão, por cima e por baixo, prolongado o comprimento de
    amarração;
  - os arranques dobrados na sapata corrida, ou a emenda com a parede de cima;
  - os varões compridos emendados.

  Ficam na lista de armaduras (vertical, horizontal, reforço dos vãos) e acompanham a parede quando ela muda.
- **Desenho:** cada parede armada tem o seu alçado com a malha, os reforços, os arranques, as cotas e as posições —
  no navegador (Armaduras) e na memória de cálculo.
- **Quantidades:** as paredes de betão entram com o seu betão, a cofragem das duas faces e o aço (taxa habitual 20 a
  150 kg/m³).

## 0.341.0 — 2026-11-01

**O fundo escuro nas vistas** (secção «Fundo escuro nas vistas» do PLANO, os três passos; pedido do dono a
2026-11-01). Como o «tema do desenho» do Revit, é uma escolha à parte do tema da interface: dá para ter a interface
clara com as vistas escuras, ou o contrário.

- Liga-se e desliga-se em **Visualizar ▸ Tema ▸ Vistas escuras** (também no menu da roda dentada). Muda na hora e
  fica guardado neste computador.
- **Plantas, cortes e alçados** passam a ter o fundo escuro, e o que é cinzento inverte-se:
  - as linhas, o cortado e as suas tramas, as cotas, os textos, as marcas dos cortes e dos níveis passam a claros;
  - as faces brancas e cinzentas passam a escuras (as paredes num alçado, por exemplo);
  - as salas ficam num cinzento quente discreto;
  - os eixos, as linhas dos desenhos CAD e as curvas de nível ficam mais claros, mantendo a cor.
- **No 3D** só o fundo e a grelha do chão escurecem: o modelo fica com as suas cores e a sua luz, como no Revit. As
  arestas mantêm-se escuras sobre as faces, e só passam a claras no estilo «Arame», em que não há faces por trás.
- **As cores ficam como estão:** o vidro, a madeira, o tijolo, os sistemas, as fases, a seleção azul, os eixos
  vermelho, verde e azul. Nos estilos com as cores dos materiais (realista, cores consistentes), as faces mantêm a
  sua cor e as arestas ficam escuras sobre elas.
- **As folhas** continuam em papel branco. **O que se exporta** (PDF, DXF, a imagem da vista com fundo branco ou
  transparente) sai como em papel; a imagem com o «fundo da vista» sai como se vê.
- **A revisão:** a casa de ensaio foi desenhada em planta, alçado e 3D, com cada um dos seis estilos de vista, nas
  vistas claras e nas escuras. Mediu-se quantos contornos do desenho claro se continuam a ver no escuro; daí saíram
  três correções:
  - as arestas no estilo «Arame», que ficavam pretas no fundo escuro;
  - as tramas do cortado, que ficavam em papel branco no meio da planta escura;
  - as arestas sobre as cores dos materiais.
- Num edifício de 2161 elementos, passar para a planta demora quase o mesmo com as vistas escuras (+0,1 s) e voltar ao
  3D demora +0,2 s.

## 0.340.0 — 2026-11-01

**A revisão do tema escuro** (passo 3, o último, da secção «Tema escuro» do PLANO).

- Fiz uma varredura automática no tema escuro. Carrega em cada botão da fita, com uma casa de ensaio e depois com
  paredes escolhidas, e mede cada texto de cada janela e painel que abre: o contraste entre as letras e o fundo, lido
  na própria imagem, tem de ser pelo menos 3 para 1. Foram 37 janelas e painéis.
- Corrigido o que se lia mal depois de mudar para o escuro sem reabrir:
  - o rodapé: o pavimento («Pavimento: Térreo…»), as unidades e o modo das medidas ficavam com letra preta sobre o
    fundo escuro;
  - o título do painel de propriedades («3D», «4 objetos selecionados») também ficava preto.
- **Estilos gráficos:** o botão de cor escreve o código da cor a preto ou a branco, conforme a cor seja clara ou
  escura. Antes, numa cor clara, o texto claro do tema escuro não se lia.
- O ensaio automático das janelas escuras passa a medir também a janela principal, logo depois da mudança de tema.

## 0.339.0 — 2026-11-01

**As janelas por cima, no tema escuro** (passo 2 da secção «Tema escuro» do PLANO).

- **O Caixilho Studio** abre no escuro do protótipo do dono (o que ele trouxe a 2026-10-29): fundo quase preto, as
  cotas, os puxadores e o botão «Inserir no modelo» a âmbar. No tema claro continua como estava.
- **As outras janelas** (verificação da estrutura, análise, ações e materiais, quantidades, lista de armaduras,
  materiais, padrões, tipos, coberturas, guardas, estilos de vista e gráficos, mapas, cozinhas, imagens, CAD): as
  notas cinzentas, os avisos a vermelho e os estados OK / atenção / falha passam a ter as cores do tema, legíveis no
  escuro.
- Os desenhos dentro dessas janelas (amostras dos materiais, padrões, o desenho da caixilharia, da cobertura e da
  guarda) ficam em fundo branco, como o papel.
- Um ensaio automático abre o Caixilho Studio e as janelas dos materiais, dos tipos e das ações no tema escuro e mede
  o contraste de cada texto com o que tem por baixo (pelo menos 3 para 1).

## 0.338.0 — 2026-11-01

**O tema escuro** (passo 1 da secção «Tema escuro» do PLANO; pedido do dono a 2026-11-01). As cores são as do
protótipo escuro do Caixilho Studio: fundo quase preto, barras mais escuras, texto cinzento-claro, destaque âmbar e
seleção azul.

- Escolhe-se em **Visualizar ▸ Tema ▸ Tema escuro** (e volta-se em **Tema claro**). Também está no menu da roda
  dentada, em baixo na barra dos módulos. Muda na hora, sem reabrir o programa, e fica guardado neste computador (não
  no projeto: outra pessoa que abra o projeto vê o seu próprio tema).
- Ficam escuros:
  - **as janelas e os campos do Qt**: listas, tabelas, menus, dicas, barras de deslocamento;
  - **as peças da janela principal**: o cabeçalho das disciplinas (o separador ativo a âmbar), a fita, a barra
    contextual, a barra dos módulos, o navegador, o painel de propriedades e as suas notas, os balões por cima da
    vista, o painel da Ajuda e o rodapé.
- **Os ícones** mudam todos de uma vez: os traços escuros passam a claros e os fundos brancos a cinzento-escuro. O
  azul, o amarelo e as cores dos materiais ficam como estavam.
- **As vistas** (3D, plantas, cortes, alçados e folhas) ficam como estavam: o papel continua branco, como no Revit.
- Falta o passo 2: as janelas com cores próprias (Caixilho Studio, editores de materiais, de padrões, de tipos e
  de coberturas, janelas da estrutura) ainda têm partes claras no tema escuro.

## 0.337.0 — 2026-11-01

**A verificação das paredes de alvenaria pelo Eurocódigo 6** (passo 3, o último, da secção «Paredes resistentes no
cálculo» do PLANO). Uma casa de paredes resistentes já se verifica de ponta a ponta, como uma de betão armado.

- **A alvenaria do projeto** está em **Estrutura ▸ Cálculo ▸ Ações e materiais…**, com cinco campos novos: o material
  dos blocos (cerâmicos, de betão, sílico-calcários, betão celular), o grupo (1 a 4), a resistência dos blocos fb, a
  argamassa (M2,5 a M20) e o γM. Por omissão: tijolo cerâmico do grupo 2, fb 10 N/mm², argamassa M5, γM 2,5. Ficam
  guardados no IFC, com as outras definições da estrutura.
- Com isso o programa tira a **resistência da alvenaria**: fk = K fb^0,7 fm^0,3 e fd = fk/γM (para o tijolo do grupo 2
  com M5: fk = 3,66 N/mm²), e a resistência inicial ao corte fvk0.
- **Cada parede resistente verifica-se** em **Verificação EC2 / EC6 e armaduras…** (antes «Verificação EC2…»):
  - **a esbelteza** hef/tef ≤ 27, com hef = 0,75 h (lajes de betão no topo e na base) e t a espessura da camada
    resistente (o bloco, sem o reboco);
  - **a compressão no topo, a meio e na base**, por metro: NRd = Φ t fd. No topo e na base, Φ = 1 − 2e/t, com a
    excentricidade das lajes que lá se apoiam (tanto maior quanto mais desequilibradas dos dois lados) e a inicial
    hef/450; a meio, o Φm do anexo G, com a fluência quando a esbelteza passa de 15;
  - **o corte no seu plano**, com a força horizontal que lhe coube (vento × 1,5, sismo × 1): VRd = fvd t lc, fvk =
    fvk0 + 0,4 σd (σd só das cargas permanentes), lc o comprimento sem os vãos.
- Na janela, cada parede tem a sua linha (estado, utilização, a verificação mais apertada), «—» nas armaduras, e as
  notas todas por baixo, como as vigas e os pilares. O resumo diz quantas paredes se verificaram e o fk.
- **A memória de cálculo** traz a alvenaria nos materiais, as paredes no modelo, as cargas de cada parede na análise,
  a verificação EC6 de cada uma e o método nas notas.
- **Correção:** a área de laje que cabe a cada parede ou viga já não depende da ordem interna dos elementos. Os
  bocados de laje à mesma distância de duas (nas diagonais dos cantos) iam todos para a primeira, e a mesma casa podia
  dar cargas um pouco diferentes de projeto para projeto; agora repartem-se por igual.

## 0.336.0 — 2026-11-01

**As cargas nas paredes resistentes** (passo 2 da secção «Paredes resistentes no cálculo» do PLANO). Pelos métodos
simplificados do Eurocódigo 6 (NP EN 1996-3): as paredes não entram como cascas no pórtico.

- **Das lajes:** cada laje dá a cada parede resistente que a apoia, e a cada viga, a área mais perto dela, como já
  dava às vigas. As vigas deixam de levar a parte que agora vai para as paredes. Uma laje sem vigas, apoiada em
  paredes e pilares, reparte-se do mesmo modo pelas paredes e pelos topos dos pilares. Com as lajes em cascas, as
  paredes seguram a malha ao longo do seu eixo.
- **Das vigas e dos pilares** apoiados numa parede: as suas reações (G e Q) vão para a parede. No pórtico, o fim de
  uma viga numa parede fica apoiado sem poder tombar sobre o seu eixo.
- **De cima para baixo:** cada parede soma o seu peso (menos os vãos) e passa tudo à parede de baixo, pelo
  comprimento que têm em comum.
- **O horizontal:** a força de cada piso (vento e sismo, nas duas direções) reparte-se pelas paredes desse piso que
  correm nessa direção, pela rigidez de cada uma (consola: flexão e corte, pelo comprimento sem os vãos). As que
  correm na outra direção não levam nada.
- Uma casa só de paredes já se analisa: **Analisar a estrutura** lista cada parede, com a compressão por metro na base
  (1,35G+1,50Q, e só G) e a maior força horizontal que lhe cabe. Numa estrutura mista, as paredes aparecem com as
  barras.
- **A sapata corrida** de uma parede resistente é dimensionada com tudo o que a parede traz (G e Q), e já não só com o
  peso da parede.

Falta a verificação de cada parede pelo Eurocódigo 6 (passo 3).

## 0.335.0 — 2026-11-01

**Paredes resistentes no modelo analítico** (passo 1 da secção «Paredes resistentes no cálculo» do PLANO; pedido do
dono a 2026-11-01: «alvenaria no cálculo»). Até aqui só pilares, vigas, lajes e sapatas entravam no cálculo; uma
casa só com paredes dava «0 barras, 0 apoios».

- Entram as paredes marcadas **Estrutural (resistente)** nas Propriedades (o campo `LoadBearing` do
  `Pset_WallCommon`, já lá estava; por omissão, as paredes não são resistentes). Cada parede entra com o seu eixo, a
  base, o topo, a espessura e a da camada resistente (o bloco, não o reboco: a camada de função «Estrutura» no tipo,
  ou a mais grossa), e as portas e janelas que tem.
- Cada parede apoia-se na sua **sapata corrida**, na **parede de baixo** (na mesma linha) ou na fundação.
- Uma **viga** que acaba numa parede fica apoiada nela, e um **pilar** que nasce sobre uma parede também. As **lajes**
  pousadas em paredes deixam de aparecer como «laje sem apoio».
- **Verificar o modelo estrutural** diz os problemas novos:
  - parede suspensa (sem nada por baixo) — erro;
  - parede sobre uma laje, sem parede por baixo — aviso;
  - parede na fundação sem sapata corrida — aviso;
  - parede de betão — nota: entra nas cargas, mas ainda não se verifica.
- No IFC, cada parede resistente entra no modelo analítico como superfície estrutural (`IfcStructuralSurfaceMember`
  SHELL), ligada à parede. A vista do modelo analítico mostra-a.

Isto é a base: as cargas nas paredes (passo 2) e a verificação pelo Eurocódigo 6 (passo 3) vêm a seguir.

## 0.334.0 — 2026-11-01

**A prioridade das camadas escolhida no tipo** (decidido pelo dono a 2026-11-01; a outra metade da ideia da «Junção
automática pelo material» do PLANO), como as funções das camadas do Revit. Até aqui, onde duas paredes se encontram, o
programa tomava a camada mais grossa de cada uma por estrutura e as outras por acabamento. Numa parede com mais
isolamento do que betão, o isolamento passava por estrutura.

- No editor de tipos (**Gerenciar ▸ Tipos**), cada camada tem agora a coluna **Função**:
  - **Estrutura [1]**, **Substrato [2]**, **Isolamento / caixa de ar [3]**, **Acabamento 1 [4]**, **Acabamento 2 [5]**;
  - **Automática**, que é a de sempre (a mais grossa é a estrutura).
- No corte (plantas e cortes, ecrã, PDF e folhas), onde dois elementos se encontram, a camada mais forte (número mais
  baixo) atravessa as mais fracas do outro até chegar a uma tão forte como ela. Numa parede que encosta a outra (T),
  o bloco entra pelo reboco e pelo isolamento até ao betão; numa sobreposição, fica a mais forte.
- Num tipo com algumas funções dadas e outras em «Automática», as que ficam em «Automática» contam como acabamento.
- Fica no próprio IFC, nos atributos de cada camada (`IfcMaterialLayer.Priority` e `Category`, do IFC4). Lê-se de
  volta ao abrir, e outros programas também a podem ler. O IFC continua válido.

## 0.333.0 — 2026-11-01

**Desunir e Unir geometria à mão** (decidido pelo dono a 2026-11-01; a ideia anotada na «Junção automática pelo
material» do PLANO), como o «Unir / Desunir geometria» do Revit. Desde a 0.320 o programa junta sozinho os elementos
que se tocam: no corte, o mesmo material sem linha entre eles, as camadas a dobrar os cantos; nas vistas, sem a aresta
entre duas paredes iguais seguidas. Agora pode escolher quais **não** se juntam:

- **Modelagem ▸ Modificar ▸ Desunir geometria** (também no separador verde «Modificar | Paredes»): clique num
  elemento e depois noutro. Entre os dois:
  - no corte (plantas e cortes), a **linha volta a desenhar-se** onde se encontram (grossa, como o contorno do que é
    cortado), as camadas de um deixam de dobrar o canto do outro, e uma sobreposição fica como está;
  - nas vistas (alçados, 3D), **a aresta entre eles volta**.

  Vale no ecrã, no PDF, no DXF e nas folhas.
- **Unir geometria**: dois cliques, e voltam a juntar-se como os outros.
- Fica guardado nos dois elementos do IFC. Cada mudança é um passo de desfazer. A forma dos elementos não muda; só o
  desenho.

Fica por decidir a outra metade dessa ideia: a prioridade das camadas escolhida no tipo (estrutura, isolamento,
acabamento…), em vez de «a mais grossa é o núcleo».

Corrigido também um erro raro, que vinha da 0.328: um elemento que mudava de forma e era logo selecionado, antes de a
vista o desenhar de novo, podia dar o erro «could not broadcast…». Era mais provável com o computador ocupado, porque
desde a 0.328 a vista refaz os lotes de desenho aos poucos. Agora a cor fica guardada e entra quando o lote é refeito.

## 0.332.0 — 2026-11-01

**Alinhar à mão os padrões de modelo numa face** (decidido pelo dono a 2026-11-01; a ideia anotada no passo 6 dos
«Gráficos dos materiais» do PLANO), como o Alinhar do Revit numa linha de padrão. Até aqui um azulejo, um tijolo ou
um bloco começavam sempre na origem do projeto, sem os poder acertar com uma janela ou com o topo de uma parede.

- Use **Modificar ▸ Alinhar** (AL) como para as paredes:
  1. clique na **referência** — uma aresta (agora também uma vertical ou inclinada, como a ombreira de uma janela),
     um eixo da grelha ou a face de uma parede;
  2. passe o rato sobre uma **linha do padrão** (uma junta de azulejo, uma fiada de tijolo): ela **acende a laranja**
     e a dica diz quanto anda;
  3. clique: o padrão dessa face desloca-se até essa linha ficar sobre a referência.

  Se a linha não for paralela à referência, o padrão **roda** à volta do ponto onde as duas se cruzam (azulejos a 45°
  acertados com uma aresta inclinada).
- Fica guardado **no próprio elemento** do IFC, face a face: vale em todas as vistas, no ecrã e no papel, e **acompanha
  o elemento** quando ele se move ou roda. Num grupo, todas as cópias ficam iguais.
- Cada alinhamento é um passo de desfazer. **Repor padrões** (Visualizar ▸ Aspeto, ou o botão direito do Selecionar)
  devolve os padrões dos elementos selecionados a como estavam.
- Fora das linhas dos padrões, o Alinhar continua a mover paredes e pilares, como antes.

## 0.331.0 — 2026-11-01

**Tramas por elemento numa vista** (decidido pelo dono a 2026-11-01; a ideia anotada na secção «Tramas como sistema»
do PLANO), como o «Substituir gráficos na vista ▸ Por elemento» do Revit. Até aqui as tramas vinham dos materiais e,
por cima, da categoria no estilo de vista (0.318). Agora um elemento pode ter as suas próprias **numa vista só**:

- Selecione um ou mais elementos e use **Visualizar ▸ Tramas por elemento** (ou o **botão direito** do Selecionar ▸
  **Tramas por elemento…**). Sem nada selecionado, o balão verde pede os elementos.
- A janela tem o **Corte** (o que o plano corta) e a **Superfície projetada** (o que se vê), cada um com padrão de
  primeiro plano e de fundo e a sua cor — os mesmos botões de padrão das categorias e dos materiais. Um padrão deixado
  em «Nenhum» fica como estava.
- Vale **só na vista em que se dá** (a planta, um corte, um alçado ou a vista 3D) e passa por cima da categoria e dos
  materiais: no ecrã, no PDF e nas folhas. O corte de um elemento assim leva uma só trama (não por camadas); dois
  elementos com a mesma trama juntam-se como um material, sem linha entre eles.
- Na superfície vale mesmo numa vista sem estilo (nos desenhos em linhas).
- **Repor** devolve-lhes as tramas da categoria e dos materiais. Cada mudança é um passo de desfazer, e fica gravada
  com as vistas do projeto.

## 0.330.0 — 2026-11-01

**Os botões e as janelas do Qt em português de Portugal** (pedido do dono a 2026-11-01). As janelas que o programa
não desenha ele próprio — as perguntas, a de gravar e abrir ficheiros, a das cores — tinham os botões em inglês
(«Save», «Discard», «Cancel», «Yes», «File name»). Agora:

- **Perguntas:** «Guardar as alterações?» tem **Guardar / Não guardar / Cancelar**; as outras **Sim / Não**, **OK**,
  **Fechar**, **Aplicar**, **Repor**.
- **Gravar e abrir ficheiros:** **Procurar em**, **Nome do ficheiro**, **Ficheiros do tipo**, **Guardar** / **Abrir**,
  **Pasta acima**, **Nova pasta**, as colunas **Nome / Tamanho / Tipo / Data de modificação**, e as perguntas «… já
  existe. Quer substituí-lo?» e «Quer mesmo eliminar…?».
- **Cores** (Materiais, Estilos gráficos): **Cores básicas**, **Tirar cor do ecrã**, **Matiz**, **Vermelho / Verde /
  Azul**.
- **Menu do botão direito numa caixa de texto:** **Desfazer, Refazer, Cortar, Copiar, Colar, Eliminar, Selecionar
  tudo**; nas caixas de números também **Aumentar / Diminuir**.
- Os botões dos painéis (**Fechar**, **Destacar**) e o × dos separadores das vistas (**Fechar separador**).

O Qt só traz a tradução do português do Brasil («Salvar», «Arquivo», «Excluir», «tela»): fica por baixo, para algum
texto raro que não esteja na lista, e a lista do programa (`ui/qt_portuguese.py`) fica por cima. Os nomes das teclas
(Ctrl, Shift, Delete, Space) ficam como sempre se viram, porque os textos do programa os usam assim.

## 0.329.0 — 2026-11-01

**Exportar a vista em imagem** (o Render, 1.ª parte: decidido pelo dono a 2026-11-01). Novo botão **Imagem da vista**
em **Render ▸ Apresentação** e em **Início ▸ Exportar**, como o «Exportar ▸ Imagem» do Revit:

- Exporta a vista que está à frente — a vista 3D, uma planta, um corte ou um alçado — tal como se vê, num ficheiro
  **PNG ou JPEG**.
- **Tamanho:** Full HD (1920 px de largura), 2K (2560), 4K (3840), uma folha A4 ou A3 deitada a 300 ppp (3508 e
  4961 px; gravada com os 300 ppp, imprime-se nesse tamanho), a largura da janela, ou outra (até 7680 px). A altura
  segue a proporção da vista: o que se vê é o que sai.
- A imagem é **mais nítida, não diferente**: as linhas e os textos ficam com a mesma grossura e o mesmo tamanho em
  relação ao desenho que no ecrã; até ~4 milhões de píxeis é desenhada ao dobro e reduzida (arestas mais suaves).
- **Fundo:** como a vista (o céu claro), branco ou transparente (só em PNG; em JPEG fica branco). Numa planta ou corte
  propõe branco, como no papel; a escolha fica para a vez seguinte.
- Sai **sem o que só as ferramentas mostram**: a seleção (o elemento selecionado aparece na sua cor), a grelha do
  chão e os eixos, as guias, a caixa de corte, as cotas temporárias, as pré-visualizações e as dicas, o cubo de
  vistas. O que ainda estava a ser desenhado aos poucos (tramas depois de uma edição, juntas, lotes de um ficheiro
  acabado de abrir) é acabado antes.
- Rápido: 0,2 s em Full HD, 0,7 s em 4K (casa de exemplo). Numa folha, o aviso diz que as folhas se exportam em PDF,
  com o botão para isso.

O render realista (luz, materiais, reflexos) fica para depois, como estava no plano.

## 0.328.0 — 2026-10-31

**A janela já não para ao reabrir um modelo grande** (Fase 1, passo 7 do PLANO: «as pausas da janela ao abrir»).
Medido no edifício de ensaio grande (12 001 elementos com as formas guardadas, 40 lotes de desenho): a 1.ª imagem
parava a janela **1,1 s** de uma vez — 0,4 s a juntar os elementos em lotes e 0,7 s a enviá-los para a placa gráfica.

- Agora, quando muitos lotes mudam ao mesmo tempo (abrir um ficheiro), cada imagem faz só os que cabem em 30 ms e
  os outros nas imagens seguintes: a **1.ª imagem aparece em 0,14 s** e o modelo completa-se em mais 8 imagens (a
  maior de 0,12 s), em ~1 s ao todo — um pouco menos do que antes, e com a janela sempre a responder.
- Enquanto essas imagens se desenham, a leitura do ficheiro (noutra tarefa) espera por elas: as duas disputavam o
  Python e, na 1.ª abertura, cada imagem chegava a levar 0,9 s.
- Uma edição (poucos lotes) continua a refazer tudo na mesma imagem, como antes.
- O benchmark conta agora como «pronto» o modelo todo desenhado e mede cada uma dessas imagens como uma pausa.
- Benchmark oficial, edifício grande, 0.320 → 0.328: **janela parada ao abrir pela 1.ª vez 838 → 464 ms, ao
  reabrir 1448 → 317 ms**; reabrir até à 1.ª imagem 3,00 → 1,82 s (a estimativa para 500 MB fica nos 20 s, no limite
  da meta).

## 0.327.0 — 2026-10-31

**O painel de Ajuda (F1)** (passo 7, o último, da secção «O programa diz o que falta, onde se vê» do PLANO). O F1 era
uma caixa com uma lista de teclas, que ainda mandava para menus escondidos desde a 0.182. Agora o **F1** (ou o **?**
no canto de cima, à direita, ou **Início ▸ Ajuda**) abre o painel **Ajuda**, ao lado das Propriedades — fica à vista
enquanto se trabalha e não tira o teclado à vista 3D. Tem quatro separadores:

- **Ferramenta** — a ferramenta em uso: o ícone e o nome, **onde está na fita** («Na fita: Arquitetura ▸
  Paredes»), **o que fazer agora** (o passo inteiro), as **teclas** dela e para que serve. Acompanha a ferramenta que
  se escolher a seguir. Com o Selecionar, explica como se seleciona.
- **Procurar** — escreve-se uma palavra («pilares», «cota», «telhado», «PDF») e aparecem os comandos com esse nome,
  primeiro os que o têm no nome, e **onde estão** («Pilares na grelha — Estrutura ▸ Grelha»). **Mostrar onde está** abre o separador
  certo e acende o botão (amarelo, por um momento; num painel recolhido, acende o painel); **Usar** (ou duplo
  clique) fá-lo logo.
- **Primeiros passos** — uma casa pequena em dez passos, do primeiro clique ao PDF, cada um com **Mostrar onde
  está**.
- **Teclas** — as teclas e gestos, revistos: copiar e colar, o balão verde dos comandos que pedem elementos, as
  teclas das ferramentas de colocação, e os caminhos da fita em vez dos menus antigos.

E, da varredura da fita feita de novo no fim (394 cliques, nenhum erro; das 84 recusas de manhã, 33 passaram a pedir
os elementos e as outras dizem o que falta com o botão para o fazer, quando há o que oferecer):
- **Repetir nos pavimentos** com um só pavimento oferece **Novo pavimento**;
- **Fechar componente** sem nenhum componente em edição já não diz «Selecione o componente…»: diz que não há nenhum
  aberto e oferece **Editar componente**; com vários abertos, pede qual.

## 0.326.0 — 2026-10-31

**Copiar, Matriz e copiar-colar à vista, como no Revit** (passo 6 da secção «O programa diz o que falta, onde se vê»
do PLANO). Até aqui copiar era um gesto escondido — tocar no Ctrl dentro do Mover, ou escrever «3x» depois de uma
cópia — e não havia Ctrl+C / Ctrl+V.

- **Copiar** (Modelagem ▸ Modificar, ao lado do Mover; também em Massa e no separador verde das paredes): a
  ferramenta Mover que já começa a copiar — ponto de base, destino (ou a distância escrita) e fica uma cópia; o
  original não sai do sítio. O Ctrl continua a desligar a cópia.
- **Matriz** (no mesmo painel): várias cópias em fila. Na barra de cima escolhe-se o número de **cópias** e a
  **distância**: «cada uma à distância dada» (2 m: as cópias a 2, 4, 6… m) ou «repartida até ao ponto dado» (8 m em 4:
  a 2, 4, 6 e 8 m). É o mesmo que copiar e escrever «3x» ou «/3» depois, num só passo e à vista.
- **Copiar e colar** (painel novo em Modelagem):
  - **Ctrl+C** (Copiar para colar) guarda o que está selecionado (sem nada selecionado, pede-o);
  - **Ctrl+V** (Colar) põe a cópia no cursor, presa pelo canto de baixo do que foi copiado: um clique deixa-a lá;
  - **Ctrl+Shift+V** (Colar nos pavimentos…) põe-na, no mesmo sítio, nos pavimentos que escolher — o «Colar alinhado
    nos níveis» do Revit.

## 0.325.0 — 2026-10-31

**Os pequenos defeitos que a varredura da fita encontrou** (passo 5 da secção «O programa diz o que falta, onde se
vê» do PLANO).

- **Apagar sem nada selecionado** (a tecla Delete ou o botão) já não fica calado: pede, como o Revit, «Clique no que
  quer apagar»; clica-se no que se quer e Delete outra vez (ou Enter) apaga. Esc desiste.
- **Pavimento acima / abaixo** no último pavimento diz «Este é o pavimento mais alto» (com o botão **Novo
  pavimento**) ou «…mais baixo», em vez de não fazer nada.
- **O Ctrl+Z já não «falha»** depois de Numerar vãos sem vãos, Soltar ligações sem ligações ou Ortogonalizar sem
  paredes tortas: esses comandos já não deixam um passo de desfazer vazio.
- **Sapatas sob pilares**, **Vigas entre pilares**, **Paredes sob vigas** e **Lajes nos vãos** dizem qual é o caso:
  «Não há pilares neste pavimento» / «Não há vigas…» (com o botão para os fazer) ou «Esses pilares já têm sapata».
- O **Modelo analítico** de uma casa só com paredes já não diz apenas «0 barras»: explica que só pilares, vigas, lajes
  e sapatas entram no cálculo (as paredes de alvenaria ainda não) e oferece **Propor estrutura…**.
- A dica da **Rampa de acesso** sem terreno fala da rampa (dizia «Plataforma»).
- **Os avisos já não mandam para menus que não se veem:** cerca de 20 textos diziam «BIM ▸ …», «Ficheiro ▸ …»,
  «Vista ▸ …» ou «Arquivo ▸ …», menus escondidos desde a fita por disciplinas (0.182). Agora dizem o sítio na fita,
  por exemplo «Gerenciar ▸ Componentes ▸ Editar componente», «Início ▸ Importar ▸ Ligar DXF», «Modelagem ▸ Criar ▸
  Classificar». (A ajuda do F1 é refeita no passo 7.)

## 0.324.0 — 2026-10-31

**O que falta, com um botão para o fazer** (passo 4 da secção «O programa diz o que falta, onde se vê» do PLANO).
Quando um comando precisa de uma coisa que ainda não existe, o balão diz o quê e tem **um botão para a fazer logo**:

- **Pilares na grelha** sem eixos → **Gerar eixos…**;
- **Proposta elétrica** sem salas, **Cotar salas** sem salas → **Sala**; **Proposta de águas** → **Sala** ou
  **Louça sanitária**; **Ligar à rede** sem louças → **Louça sanitária**; **Ligar ao quadro** sem circuitos → **Novo
  circuito**;
- **Sapatas sob pilares** e **Vigas entre pilares** sem pilares → **Pilares na grelha** (com eixos) ou **Pilar**;
  **Paredes sob vigas** e **Lajes nos vãos** sem vigas → **Vigas entre pilares**;
- **Propor estrutura**, **Cotar paredes** e **Cotar fachadas** sem paredes → **Parede**;
- **Bancada** sem móveis → **Móvel**; **Paredes a partir do desenho** sem DXF → **Ligar um desenho DXF/DWG…**;
  **Modelo a partir da nuvem** sem nuvem → **Ligar uma nuvem de pontos…**; **Momentos** sem análise → **Analisar a
  estrutura…**; **Exportar folhas** sem vistas → **Folhas por pavimento…**; **Último corte** sem corte → **Corte**;
  **Sincronizar**, **Reservar** e **Devolver** num projeto não partilhado → **Partilhar projeto numa pasta…**;
  **Editar plataforma** sem plataformas → **Plataforma** (ou **Terreno por pontos**);
- as ferramentas **Calibrar imagem** (sem imagem → **Importar imagem de fundo…**), **Plataforma** e **Rampa de
  acesso** (sem terreno → **Terreno por pontos**) mostram o botão no balão do seu primeiro passo.
- Clicar no botão fecha o balão e faz o passo. Um aviso sem nada para oferecer fica sem botão.
- Os nomes de três comandos ficaram mais claros: «Vigas» passa a **Vigas entre pilares**, «Inserir pilares» a
  **Pilares na grelha** (como na fita) e «Novo circuito com a seleção» a **Novo circuito** (desde a 0.322 pede os
  pontos).

## 0.323.0 — 2026-10-31

**Cota, Desenho 2D e Pormenor abrem sozinhos a planta** (passo 3 da secção «O programa diz o que falta, onde se vê»
do PLANO). Escolhidos na vista 3D, diziam «abra primeiro uma planta (F4)…» e um clique no 3D não fazia nada — era uma
das ferramentas que «não funcionavam».

- Escolhidos numa vista 3D, abrem a **planta do pavimento ativo** (como o F4) e começam lá; o balão diz porquê e o
  primeiro passo: «Isto faz-se numa planta, num corte ou num alçado: abri a planta «Térreo». Clique no primeiro
  ponto…».
- Escolhidos numa planta, num corte ou num alçado, ficam nessa vista, como sempre.

## 0.322.0 — 2026-10-31

**Os comandos pedem o que lhes falta, como o Revit, em vez de recusar** (passo 2 da secção «O programa diz o que
falta, onde se vê» do PLANO). Até aqui, um comando que precisava de elementos selecionados e não os tinha dizia
«Selecione primeiro…» e parava: era preciso ir ao Selecionar, escolher e voltar ao botão.

- Agora o comando **fica à espera** e diz, num **balão verde** no cimo da vista, com o seu nome e ícone, o que se deve
  clicar e quantos já estão escolhidos («Clique nas paredes e pilares cujo topo quer ligar. Escolhidos: 2»):
  - **um clique** num elemento junta-o; outro clique no mesmo tira-o (sem precisar de Shift); **arrastar uma caixa**
    junta todos os que lá estão;
  - **Enter** ou o **botão direito** continuam; nos comandos de um só elemento (ou de dois), basta clicar e o comando
    segue sozinho;
  - **Esc** (ou o × do balão) desiste; o que estava selecionado fica;
  - um elemento que não serve (uma laje quando se pedem paredes) não entra, e o balão diz «Esse elemento não serve»;
  - o que já estava selecionado e serve conta como escolhido.
- Os comandos que pedem assim:
  - **Ligar o topo** e **Ligar a base**: primeiro as paredes e pilares, depois a laje ou cobertura (a laje ou sapata),
    num só clique;
  - **Juntar paredes** (as duas), **Editar perfil** (a parede), **Editar contorno** (a laje), **Editar plataforma**
    (o terreno, quando há vários);
  - **Sapata combinada** (os dois pilares), **Novo circuito** (as tomadas, interruptores e luminárias);
  - **Fazer componente**, **Fazer grupo**, **Desagrupar**, **Editar componente**, **Repetir nos pavimentos**;
  - **Perfil a partir de uma face** e **Perfil da cobertura** (a cobertura e depois a face, ou ao contrário);
  - **Caixa à volta da seleção**;
  - as ferramentas **Espelhar** e **Escala**: escolhidas sem nada selecionado, pedem primeiro o que espelhar (os
    esboços a escalar) e, com Enter, começam sobre isso.
- Enquanto um comando espera, o rodapé diz o mesmo que o balão; mudar para outra ferramenta desiste dele.

## 0.321.0 — 2026-10-31

**Os avisos e as dicas à vista, num balão por cima da vista** (o dono: «testei algumas [ferramentas] mas não
funcionaram; não sei se estou a usar errado»). Uma varredura de todos os botões da fita, na 0.320, mostrou que todos
respondiam, mas que 84 vezes a resposta era um aviso ⚠ que não se via: uma linha pequena no rodapé, cortada pelo resto
do rodapé e apagada ao fim de 10 s. Passo 1 da secção «O programa diz o que falta, onde se vê» do PLANO.

- **O que um comando diz aparece num balão no cimo da vista**, ao meio, por baixo dos separadores das vistas e longe
  do cubo de vistas, com o texto inteiro (em várias linhas, se for comprido):
  - quando o comando **não pode atuar** («Ainda não há eixos…», «Selecione primeiro…»), o balão é cor de âmbar e fica
    até ao clique seguinte na vista, ao Esc, a outra ferramenta ou a outra seleção (30 s no máximo);
  - quando **fez alguma coisa** («4 paredes viradas…», «Planta do Térreo…»), o balão é azul e sai sozinho, ao fim de
    4 a 12 s, conforme o comprimento do texto;
  - o × fecha-o; um clique no balão também.
- **Ao escolher uma ferramenta**, o balão mostra o seu nome e o primeiro passo, inteiro («Cota — abra primeiro uma
  planta (F4)…», «Parede — clique no início…»), até ao primeiro clique na vista. Não aparece no Selecionar nem nas
  ferramentas de navegação.
- **O rodapé fica só com o passo da ferramenta:** os avisos já não o tapam. Passando o rato por cima, vê-se o passo
  inteiro quando não cabe.
- **Mudar de separador já não escreve nada no rodapé** (a frase sobre a disciplina tapava durante 10 s a dica da
  ferramenta escolhida a seguir); o que cada disciplina tem diz-se ao passar o rato pelo separador.
- Um aviso dito por uma ferramenta que logo a seguir volta ao Selecionar fica à vista (antes, a troca de ferramenta
  apagava-o).

## 0.320.0 — 2026-10-30

**Junção automática pelo material, como no Revit** (pedido do dono: «quero que os elementos com mesmo material tenham
um auto join; em corte ou vista as partes com mesmo material mantêm-se unidas e não aparecem linhas de junções»).
Só muda o desenho: cada elemento continua com a sua forma no IFC.

- **No corte (plantas e cortes, no ecrã, no PDF, no DXF e nos detalhes):**
  - o mesmo material é uma peça só: já não aparece linha entre duas paredes que se encontram, nem entre os blocos ou
    os rebocos delas; a linha fina fica só onde o material muda e a grossa só à volta de tudo o que é cortado;
  - nos **cantos em L** de paredes com camadas, as camadas dobram a esquina em meia-esquadria: o reboco de fora
    continua por fora, o bloco com o bloco, o reboco de dentro por dentro (antes, o reboco de uma parede atravessava
    o bloco da outra);
  - numa parede que **encosta ao lado de outra (T)**, o bloco dela entra até ao bloco da outra, cortando o reboco; o
    reboco de cada sala dá a volta;
  - onde dois elementos se **sobrepõem**, fica a camada mais forte (o núcleo ganha ao acabamento; em empate, o pilar,
    depois a viga, a laje e a parede);
  - no PDF, o contorno grosso faltava nas faces de dentro das paredes de uma sala fechada: corrigido.
- **Nas vistas (3D, alçados, o que se vê nos cortes, as folhas e o PDF):** a aresta onde dois elementos do mesmo
  material ficam no mesmo plano (duas paredes do mesmo tipo seguidas, uma parede que continua a de baixo, uma laje
  que continua outra) não se desenha. Onde o material muda, a linha fica; se uma parede é mais alta, fica só a parte
  da aresta acima da outra. Vale para paredes, lajes, pilares, vigas, coberturas, revestimentos e escadas (portas e
  janelas guardam as suas linhas).
- **Sem pesar no trabalho:** no 3D, ao mudar um elemento só se olha para ele e para os que lhe tocam; ao abrir um
  projeto grande, as juntas vão-se tirando aos poucos depois de cada imagem, sem prender a janela. Numa planta com
  muitos elementos, ao editar aparece primeiro a imagem e as tramas refazem-se logo a seguir.

## 0.319.0 — 2026-10-30

**Escolher a trama da superfície e do corte como no Revit** (pedido do dono, com uma captura da janela dos materiais:
«ainda não consigo colocar uma trama na superfície e no corte; deveria ter opção nos 2 grupos para melhor intuição»).

- Na janela dos materiais, em **Superfície** e em **Corte**, o **primeiro plano** e o **fundo** são agora cada um um
  **botão com a amostra e o nome do padrão** (onde antes havia a lista «Nenhum»), com a cor ao lado.
- **Clicar no botão** (ou na amostra grande do grupo) abre a janela **Escolher padrão**:
  - todas as tramas em quadrados grandes;
  - as **de desenho** (medidas no papel) e as **de modelo** (medidas na obra) em separado — a superfície abre nas de
    modelo (azulejos, tijolos…), o corte nas de desenho;
  - **Nenhum padrão**;
  - **Novo…** e **Editar…**, que abrem a janela dos padrões de preenchimento e voltam com o padrão feito ou mudado
    já escolhido;
  - duplo clique numa trama escolhe-a.
- Em cada grupo, uma linha diz como se faz: «Clique no padrão para o escolher, criar ou editar; ao lado, a sua cor».
- O botão solto «Padrões de preenchimento…» do cimo da janela saiu: o caminho para criar e editar padrões é agora a
  própria escolha. (Continua também em Gerenciar ▸ Tipos e materiais ▸ Padrões….)
- As tramas por categoria dos estilos de vista escolhem-se da mesma maneira.
- Testes com a janela: as verificações da planta (F4), do corte e da visibilidade olhavam um só ponto da parede
  cortada, que agora tem a trama clara entre linhas (0.317); olham agora alguns pontos à volta e confirmam que a
  parede tem a trama no ecrã.

## 0.318.0 — 2026-10-30

**As tramas como sistema: padrões do projeto, tramas por categoria e uma biblioteca de materiais** (pedido do dono:
«as tramas ainda não são um sistema que permite criar muitos materiais»).

- **Padrões de preenchimento do projeto** (Gerenciar ▸ Tipos e materiais ▸ **Padrões…**, ou o botão **Padrões de
  preenchimento…** na janela dos materiais):
  - a lista tem os padrões do programa (a cinzento: não se mudam, duplicam-se) e os do projeto;
  - **Novo**, **Duplicar**, **Apagar**, com o nome à escolha;
  - cada padrão é **medido no papel** (igual em qualquer escala: tramas de corte) ou **na obra** (azulejos, tijolos);
  - a forma: **linhas paralelas** ou **cruzadas** (ângulo e afastamento), ou **personalizada**: várias famílias de
    linhas, cada uma com o ângulo, a origem, o desvio, o afastamento e os traços («3 -1» é traço e intervalo, «0 -1»
    são pontos);
  - uma amostra grande, que muda enquanto se escreve;
  - ficam gravados **no próprio ficheiro IFC** (como estilos de preenchimento), e vão com o projeto;
  - aparecem logo nas listas dos materiais e do estilo gráfico do projeto.
- **Tramas por categoria nos estilos de vista**, como as substituições de visibilidade e gráficos do Revit: na janela
  dos estilos (Visualizar ▸ Aspeto ▸ Estilos de vista…), **Tramas por categoria ▸ Juntar…**. Escolhe-se a categoria
  (paredes, lajes, pilares, coberturas…) e, para ela:
  - o **corte** (o que o plano corta): primeiro plano e fundo, cada um com a sua cor;
  - a **superfície projetada** (o que se vê): primeiro plano e fundo.

  Nas vistas com esse estilo, esses elementos passam a ter estas tramas em vez das dos seus materiais, no ecrã, nas
  folhas e no PDF. «Nenhum» deixa a dos materiais.
- **Uma biblioteca de materiais maior** — 37 materiais novos, cada um com a trama de corte (e de superfície quando faz
  sentido), a massa volúmica e a condutibilidade térmica:
  - alvenarias: tijolo furado 11, tijolo maciço (com o tijolo à vista), bloco de betão, bloco térmico;
  - betões: betão armado, betão leve, betonilha;
  - isolamentos: XPS, EPS, lã de rocha, cortiça (ICB), poliuretano;
  - madeiras: pinho, carvalho maciço, OSB, contraplacado, MDF, deck;
  - pedras: granito, calcário (lioz), mármore, xisto, calçada portuguesa;
  - metais: aço estrutural S275, zinco de junta agrafada, chapa de cobre;
  - revestimentos: gesso cartonado hidrófugo, estuque, reboco monomassa, reboco do ETICS, ladrilho 30×30,
    porcelânico 60×30, pavimento vinílico, tela impermeabilizante;
  - e brita, areia, vidro duplo.
- **A janela dos materiais** tem agora uma lista por **famílias** (alvenarias, betões, isolamentos, madeiras, pedras,
  metais, rebocos e cerâmicos, vidros) e uma **pesquisa** por nome.

## 0.317.0 — 2026-10-30

**As tramas de corte e de superfície no ecrã** (pedido do dono: «não consigo colocar uma trama para um elemento
cortado, e outra trama para a superfície projetada»).

- **O corte no ecrã como no papel.** Nas plantas e nos cortes, o que o plano corta já não fica todo escuro: cada
  camada mostra o fundo e as linhas do seu material (o bloco com a diagonal sobre rosa, a lã com o ziguezague), ou,
  sem trama própria, a da sua categoria no estilo gráfico do projeto (o reboco cinzento, o betão escuro). As tramas
  de desenho saem à escala da vista (1:50 se a vista não tiver escala). Um elemento escolhido fica na cor da seleção,
  e um clique no corte continua a escolhê-lo.
- **A superfície projetada no ecrã.** O azulejo no chão visto de cima, a pedra numa fachada: os estilos **Sombreado**,
  **Linhas escondidas** e **Cores consistentes** passam a mostrar as tramas de superfície dos materiais (só nos
  elementos cujos materiais as têm, para não pesar). Telhas, portas e guardas, desenhadas peça a peça, não levam
  trama por cima.
- **A superfície projetada no papel, também sem estilo.** Os desenhos de sempre (só linhas) desenham as tramas de
  superfície das faces que se veem — o azulejo do chão na planta, as fiadas da pedra no alçado —, escondidas pelo que
  está à frente.

## 0.316.0 — 2026-10-30

**Sombras no papel e o sol à escolha em cada estilo** (pedido do dono, a seguir à 0.315: «sim, faz»).

- **As sombras também saem nos desenhos** — alçados, cortes, plantas e vistas 3D nas folhas e no PDF —, quando o
  estilo da vista tem **Sombras do sol** e faces pintadas (Realista, Cores consistentes ou um estilo do projeto):
  - o que está à frente de uma face faz-lhe sombra: o beiral na fachada, um pilar na parede, o aro de uma janela e a
    padieira no vão, a parede no chão de uma planta (cortada, como se vê);
  - as faces viradas para o lado contrário ao sol ficam à sombra por inteiro;
  - a sombra é a cor do material, mais escura; os padrões da superfície (as fiadas da pedra) continuam por cima;
  - a luz que passa por uma porta ou entre dois elementos fica clara, com os cantos certos.
- **O sol de cada estilo escolhe-se** na janela dos estilos de vista (Visualizar ▸ Aspeto ▸ Estilos de vista…):
  - **Azimute** (0 = norte, 90 = este, 180 = sul, 270 = oeste) e **Altura** acima do horizonte;
  - ou o botão **Pelo local e pela hora…**: escolhe-se o dia, a hora e o fuso horário, e o programa calcula onde está
    o sol sobre o terreno do projeto (a latitude e a longitude de Gerenciar ▸ Projeto ▸ Localização do terreno…). A
    meio de uma noite, avisa que o sol está abaixo do horizonte.
  - Por omissão, o sol vem do sul-sudoeste, a 47° de altura (as sombras caem para nordeste).
- O mesmo sol serve o 3D e o papel: as sombras do 3D e as do PDF caem para o mesmo lado.

## 0.315.0 — 2026-10-30

**Estilos de vista com tramas e sombreamentos** (pedido do dono: «quero poder criar estilos de vistas com tramas e
sombreamentos»).

- **Estilos de vista com nome**, como os estilos visuais do Revit. Em **Visualizar ▸ Estilos de vista…** (também no
  separador **Render** e no botão do estilo, no rodapé) faz-se, dá-se nome, duplica-se, muda-se e apaga-se um estilo.
  Cada estilo diz:
  - **Faces:** sombreadas (com luz), em cores consistentes (sem luz), brancas (linhas escondidas), só arestas
    (arames) ou transparentes (raio-X);
  - **Cores:** as de cada categoria (paredes, lajes… como até aqui) ou as **dos materiais, camada a camada** — a pedra
    por fora, o reboco por dentro, e no topo de uma parede as suas camadas lado a lado;
  - **Arestas:** desenhadas ou não, e a espessura (1 a 3 px);
  - **Sombras do sol:** a casa faz sombra no chão e nas suas próprias paredes (o sol vem da frente, à esquerda, alto);
  - **Padrões de superfície:** as fiadas da pedra, os azulejos, o tijolo à vista, as telhas… desenhados nas faces;
  - **Transparência:** o vidro deixa ver o que está por trás;
  - **Corte (desenhos):** pelos padrões de cada material, pela trama da categoria, cheio escuro ou vazio (só o
    contorno).
- **Os estilos do programa** são os quatro de sempre (Sombreado, Linhas escondidas, Arame, Raio-X) e dois novos:
  **Cores consistentes** e **Realista** (cores dos materiais, padrões, vidro transparente e sombras). Não se mudam: o
  botão **Novo a partir deste** faz um do projeto com as mesmas definições, para o mudar à vontade.
- **Dar um estilo a uma vista:**
  - a vista 3D: nas Propriedades (sem nada escolhido), na linha **Estilo visual**, ou no botão do rodapé;
  - uma planta, um corte ou um alçado: a mesma linha das Propriedades. «Nenhum» deixa o desenho como sempre (linhas e
    o corte pelos materiais);
  - um **modelo de vista** pode dar o estilo a todas as suas vistas (nova linha **Estilo de vista** na janela dos
    modelos).
- **Os desenhos seguem o estilo**, no ecrã das folhas e no PDF:
  - alçados, cortes e plantas com as faces pintadas (sombreadas ou em cores consistentes), nas cores dos materiais;
  - os padrões de superfície das faces vistas (as fiadas da pedra no alçado), escondidos pelo que está à frente;
  - o corte como o estilo diz (padrões do material, trama da categoria, cheio ou vazio);
  - uma vista 3D numa folha com «Cores consistentes», «Realista» ou um estilo do projeto sai pintada; com os estilos
    de sempre sai em linhas, como até aqui.
- Os estilos do projeto ficam gravados com as vistas; apagar um estilo devolve as vistas que o usavam ao Sombreado.
  Tudo se desfaz com Ctrl+Z.

## 0.314.0 — 2026-10-30

**Os materiais com gráficos completos, como no Revit** (pedido do dono: «os materiais devem receber mais detalhes, de
apresentação de superfície e cortes»).

- **A janela dos materiais** (BIM ▸ Materiais…) tem agora duas partes novas, cada uma com a sua amostra:
  - **Superfície (3D, alçados):** padrão de primeiro plano e de fundo, cada um com a sua cor; a **cor de
    sombreamento** (a cor do material, como antes); a **transparência** (0 a 100 %);
  - **Corte (plantas, cortes):** padrão de primeiro plano e de fundo, cada um com a sua cor. Sem padrões próprios, o
    material corta-se como até aqui: com a trama da sua categoria, no estilo gráfico do projeto (a janela diz isso e
    mostra essa trama na amostra).
- **Uma biblioteca de padrões:**
  - de desenho, medidos no papel (iguais em qualquer escala): cheio, diagonal, diagonal larga, diagonal inversa,
    diagonal cruzada, horizontal, vertical, quadrícula, **betão**, **areia** (pontos), **isolamento** (ziguezague),
    **terra**, **madeira** (veio), **aço**;
  - de modelo, medidos na obra (crescem com a escala): azulejo 10×10 e 15×15, ladrilho 20×20, 30×30 e 60×30, **tijolo à
    vista**, bloco 50×20, **pedra aparelhada**, réguas verticais e horizontais, **telha**, painéis 120×240.
- **Os materiais do catálogo já vêm com alguns:** o azulejo com as juntas de 15×15, a pedra natural com as fiadas, a
  telha com as suas linhas; o vidro com 60 % de transparência, o vidro fosco com 30 %.
- **No papel** (plantas, cortes, folhas e PDF), cada camada cortada pinta-se com o fundo e o primeiro plano do seu
  material: o bloco com a diagonal sobre rosa, a lã mineral com o ziguezague sobre amarelo, o reboco com pontos…
- **O estilo gráfico do projeto** (Visualizar ▸ Estilos gráficos…) pode agora dar a cada categoria um destes padrões
  (betão, areia, isolamento, terra, madeira, aço, quadrícula).
- **As miniaturas dos tipos** (o corte das paredes, as camadas das lajes) usam os padrões de corte dos materiais.
- **Fica tudo no IFC**, para reabrir igual e para os outros programas lerem: a transparência no estilo de superfície
  do material; os padrões como estilos de preenchimento (IfcFillAreaStyle) ao lado dele — «Surface» e «Cut», o fundo
  cheio como cor e cada família de linhas como tracejado do IFC (IfcFillAreaStyleHatching); e o nome exato de cada
  padrão num parâmetro do material. Um material com tramas feitas noutro programa lê-se como diagonal ou cruzada, na
  sua cor.

## 0.313.0 — 2026-10-30

**O tipo no cabeçalho das Propriedades, com miniaturas** (pedido do dono: «colocar o botão do tipo no cabeçalho e com
lista com miniatura dos vãos» e «para todos os elementos, quero que fique ali o botão e tenha miniatura nas listas»).

- **O tipo escolhe-se em cima**, por baixo do nome do elemento, como no seletor de tipos do Revit:
  - vale para todos os elementos que têm tipo: paredes, lajes, coberturas, pilares, vigas, sapatas, estacas, tubos,
    condutas, portas e janelas;
  - ao lado fica a miniatura do tipo escolhido;
  - a linha «Tipo» das Propriedades passa a ter só o botão **Editar tipo…** (e, nas portas e janelas, o **Caixilho
    Studio…**).
- **A lista abre com uma imagem de cada tipo:**
  - portas e janelas: o desenho em alçado, com as cores dos materiais e os sinais de abertura;
  - paredes: o corte das camadas lado a lado, cada uma na cor e na trama do seu material;
  - lajes e coberturas: as camadas empilhadas;
  - pilares, sapatas, blocos de estacas (com as estacas a tracejado) e estacas: a secção vista de cima;
  - vigas: a secção;
  - tubos e condutas: a secção oca.

  Paredes, lajes e coberturas estão todas à mesma escala: uma parede de 20 cm vê-se mais grossa do que uma de 10 cm.
- **Com vários elementos escolhidos:**
  - se forem todos do mesmo tipo, a lista mostra esse tipo;
  - se forem de tipos diferentes, mostra «<vários>», e o tipo escolhido vai para todos;
  - se forem de categorias diferentes (paredes e pilares, por exemplo), não aparece a lista.
- **As mesmas miniaturas também aparecem:**
  - na lista **Tipo** da barra de cima, quando se desenha uma parede, laje, pilar, porta, janela…;
  - na lista do **editor de tipos**.
- Cada miniatura desenha-se uma vez por tipo (e pelas cores dos seus materiais) e fica guardada.

## 0.312.0 — 2026-10-30

**Portas e janelas sem linhas de junta** (pedido do dono: «quero que as linhas de junções das peças não apareçam, para
que portas e janelas fiquem mais limpas»).

- **O aro é uma peça só.** Onde o montante encontra a travessa de cima ou de baixo, já não aparece o traço (às vezes
  duplo) da junta. O mesmo vale para os montantes e travessas do meio, os carris das bandeiras e as guarnições da
  porta: a guarnição de cima e as dos lados fazem um ∩ sem juntas, e ficam presas ao aro sem linha no vão.
- **Cada folha é uma peça só.** Os cantos dos caixilhos das folhas (onde o montante encontra a travessa) ficam limpos.
- **As linhas que contam ficam.** Continua a ver-se a linha à volta de cada folha: entre a folha e o aro, e entre as
  duas folhas de um par que fecham uma contra a outra. As arestas verdadeiras (os cantos do vão, a profundidade do
  aro) também ficam.
- Também ficam sem juntas o peitoril com pingadeira, as portadas de lâminas e a moldura do mosquiteiro.
- **As novas já nascem limpas.** As que já estão num projeto ficam limpas quando forem refeitas:
  - ao movê-las ao longo da parede;
  - ao mudar-lhes o tipo ou a mão;
  - ao editar o tipo no editor de tipos (refaz todas as desse tipo de uma vez);
  - ao mudar a espessura da parede onde estão.
- O IFC gravado leva a geometria limpa: noutro programa (o Revit, por exemplo) também se vê sem juntas, e com menos
  triângulos.
- Juntar as peças custa cerca de 15 ms por janela. Fica guardado para as seguintes do mesmo tipo, medida e parede, que
  saem logo.

## 0.311.0 — 2026-10-29

**Push/Pull em várias faces escolhidas ao mesmo tempo** (pedido do dono: «gostaria de melhorar o push/pull, que ele
possa extrudir na mesma direção várias faces selecionadas»).

- **Escolha as faces e puxe uma delas.**
  - Escolhem-se com o Selecionar: um clique numa face, e Shift+clique nas outras.
  - Também contam os esboços escolhidos inteiros, por exemplo vários retângulos escolhidos com uma janela.
  - Com o Push/Pull, um clique numa das faces escolhidas leva todas, a mesma distância.
  - Um clique numa face que não está escolhida continua a levar só essa face, como antes.
- **Na mesma direção.**
  - Cada face anda pela sua própria normal: as que olham para o mesmo lado andam exatamente juntas.
  - Se a face clicada sai, saem todas; se entra, entram todas.
  - Dos esboços escolhidos inteiros, contam as faces que olham para o mesmo lado que a face clicada (o topo de várias
    caixas, não os lados).
- **As faces que se tocam andam como uma peça.**
  - Não fica parede entre elas, e as linhas entre elas ficam em cima. Por exemplo, duas divisões de uma planta dão um
    volume só, com a linha da divisória no teto.
  - Onde se juntam em ângulo (um chão e uma parede), os cantos vão de modo que cada face fique à mesma distância: uma
    casca mais grossa, sem fendas.
- **Cada peça segue as regras de uma face sozinha:**
  - sem nada ao lado, fica com a base: um sólido fechado;
  - numa caixa, os lados esticam;
  - noutros casos sai do sítio (um rebaixo aberto), salvo com o Ctrl, «Criar sólido», que deixa a face de partida e
    faz um sólido fechado.
- **A distância é a mesma para todas.** Se uma das faces não pode ir tão longe (para não virar uma caixa do avesso),
  todas param aí, e a barra de estado diz que o Push/Pull foi limitado.
  - Os retângulos desenhados numa parede ou laje IFC e empurrados para dentro abrem uma abertura ou um nicho cada um,
    como sozinhos.
- **Um só passo para desfazer.**
  - As faces escolhidas continuam escolhidas onde ficaram: outro Push/Pull leva-as outra vez. Com o Criar sólido, ficam
    escolhidas as faces novas, para ir empilhando pisos.
  - Uma medida escrita logo a seguir corrige todas.
- **A moldura de um Offset puxa-se inteira:** um clique numa das quatro tiras leva a moldura toda, a face que o
  SketchUp mostra. Antes levava só essa tira.
- Testes:
  - sem janela:
    - a moldura como uma face;
    - o esboço todo, uma caixa fechada;
    - a moldura com o Ctrl, um anel fechado;
    - duas divisões, um volume só;
    - duas faces afastadas e a alturas diferentes;
    - o topo e um lado de uma caixa juntos;
    - duas caixas limitadas pela mais baixa;
    - o chão e a parede, uma casca sem fendas;
  - com a janela real:
    - a moldura puxada inteira;
    - o meio de um esboço e outro retângulo puxados juntos, num só passo;
    - a correção por medida escrita.

## 0.310.0 — 2026-10-29

**Faces sozinhas e Push/Pull como no SketchUp** (queixa do dono: «construí um retângulo, fiz o offset, mas o
push/pull negativo criou um sólido, e as partes são selecionadas todas juntas; não consigo selecionar apenas uma face.
Isso não está a ser semelhante ao SketchUp» e «quando usar o push/pull com Control ligado, ele deve criar um sólido
independentemente da direção»). O Offset já dividia a face em duas, mas a seleção escolhia sempre o esboço inteiro, e
o Push/Pull deixava a face de partida no sítio, fechando o rebaixo.

- **Um clique escolhe só a face** de um esboço, como no SketchUp. A moldura de um Offset (quatro tiras unidas por
  arestas escondidas) conta como uma só face; o lado liso de um cilindro também.
  - Dois cliques seguidos: a face e as suas arestas (a azul forte).
  - Três cliques: o esboço inteiro, como antes.
  - Shift, Ctrl e Ctrl+Shift juntam e tiram faces, como na seleção de elementos.
  - A barra de estado diz a área da face escolhida.
  - Um elemento BIM, um componente em edição, um esboço de uma só face ou um tipo escolhido para classificar continuam
    a escolher-se inteiros.
- **O que se faz com a face escolhida:**
  - **Delete** tira-a; o contorno fica como linhas, como no SketchUp (com as arestas escolhidas, vai também);
  - **Mover** e **Rodar** levam só ela, e as faces ao lado esticam; uma face que deixe de ficar plana dobra-se em
    triângulos, por arestas escondidas. A face continua escolhida depois.
  - Uma face sozinha não se copia: a mensagem pede três cliques para escolher o esboço inteiro.
  - **Classificar como** e **Fazer componente (G)** usam o volume da face escolhida: um clique numa face e o tipo
    continuam a chegar para fazer uma parede, uma laje ou um componente.
- **Push/Pull como no SketchUp:** uma face com faces ao lado sai do sítio. O meio de um retângulo com Offset empurrado
  para baixo é um rebaixo aberto em cima; puxado para cima, uma caixa sem fundo. Um retângulo sozinho continua a dar
  uma caixa fechada.
- **Ctrl — «Criar sólido»** (a «nova face de partida» do SketchUp):
  - Ctrl carregado e largado sozinho liga e desliga; também há uma caixa na barra por baixo da fita, e o Ctrl seguro
    no clique conta.
  - Ligado, fica uma face onde a face partiu, e o que sai dela é um sólido fechado, para cima ou para baixo, também
    numa caixa (uma caixa nova por cima, em vez de a esticar).
  - Num retângulo desenhado numa parede ou laje IFC, com o Ctrl ligado faz-se um sólido em vez da abertura.
- **Corrigido:** o Ctrl de um atalho (Ctrl+Z, Ctrl+S…) já não conta como Ctrl sozinho. Antes, desfazer com Ctrl+Z
  ligava ou desligava a cópia do Mover e do Rodar.
- Testes:
  - sem janela: o rebaixo aberto e as suas paredes viradas para dentro; o sólido fechado com Ctrl, para cima e para
    baixo e numa caixa; a moldura do Offset e o lado do cilindro como uma face; apagar com e sem as arestas; mover
    uma face (as tiras ao lado continuam planas, ou dobram-se quando a face se inclina);
  - com a janela real: o percurso do TESTAR, do retângulo ao mover só o meio.
## 0.309.0 — 2026-10-29

**Igualar todas as divisões no Caixilho Studio, como parâmetros do tipo** (pergunta do dono: «tem parâmetros para
igualar todas as divisões? Caso não, faça»). Até aqui só havia «Igualar colunas», que igualava as larguras uma vez;
para as alturas não havia nada.

- Na barra por cima do desenho, «Igualar colunas» deu lugar a três botões:
  - **Larguras iguais**: todas as colunas com a mesma largura;
  - **Alturas iguais**: em cada coluna, todos os painéis com a mesma altura;
  - **Igualar tudo**: liga os dois de uma vez.
- São parâmetros, não um clique de uma só vez. Enquanto estão ligados (● e fundo azul claro), as divisões ficam iguais
  ao pôr ou tirar um montante ou uma travessa, ao escrever a largura ou a altura do vão e ao puxar os seus lados.
- Mover um montante ou uma travessa à mão, ou escrever a largura de uma coluna ou a altura de um painel, desliga o
  parâmetro respetivo. Um aviso no canto diz «Larguras iguais: desligado» (ou ligado).
- As cotas mostram «EQ» em cada medida igual a outra, também na cadeia das alturas. Com o parâmetro ligado, o «EQ» fica
  a negro, no azul forte.
- O parâmetro fica guardado no tipo, no IFC: as colunas e os painéis iguais vão com medida 0, que quer dizer «partilham
  por igual». Por isso, mudar a largura ou a altura do tipo fora do Studio (na tabela do tipo) também mantém as
  divisões iguais, e ao reabrir no Studio os botões aparecem ligados.
- Testes:
  - sem janela: os parâmetros mantidos ao pôr e tirar montantes e travessas e ao mudar o tamanho; desligados por um
    montante ou travessa movidos à mão; guardados no desenho com medidas 0 e lidos de volta (também num tipo com outra
    largura);
  - com a janela real: «Igualar tudo», um montante e uma travessa arrastados, a largura escrita, um montante movido à
    mão (desliga e avisa), «Larguras iguais» outra vez, inserido no modelo com as medidas 0 no tipo.

## 0.308.0 — 2026-10-29

**O Caixilho Studio no tema do programa** (pedido do dono: «o tema deve ser coerente; quando criarmos o tema escuro
vai ser assim, mas agora o tema é claro»).

- O Studio usa agora as cores claras do resto do programa, com a mesma organização e as mesmas medidas do protótipo:
  - o cabeçalho azul-escuro do programa, com o símbolo da marca (o mesmo do cabeçalho principal; antes era um quadrado
    desenhado pelo protótipo);
  - os separadores e o rodapé no cinzento claro da fita;
  - a tela clara com a grelha suave;
  - o cartão do painel branco;
  - o azul do programa nas cotas, nas pegas, nas escolhas e no botão «Inserir no modelo»;
  - os campos brancos com o rebordo dos da barra contextual, e os avisos no vermelho dos campos errados.
- As cores do protótipo ficam guardadas como o tema escuro do Studio. Vão servir quando o programa tiver um tema
  escuro: basta mudar o tema, sem mexer no resto.
- Os vidros, a madeira, a veneziana e as cores dos perfis continuam como eram: são do caixilho, não do tema.
- Testes:
  - sem janela: o tema claro está em uso, com o azul-escuro do cabeçalho, o azul e o cinzento da fita do programa; o
    escuro tem as mesmas cores definidas;
  - com a janela real: os percursos do Studio e os do antigo gerador, sem mudanças.

## 0.307.0 — 2026-10-29

**O Caixilho Studio** (passo 2, pedido do dono: «verifiquei o gerador de porta e janela, mas não gostei; fiz este
protótipo e quero que implemente»). Passa a ser o editor de portas e janelas do programa, no lugar do gerador.

- **Onde se abre:**
  - Arquitetura › Vãos › **Caixilho Studio**: com o tipo da ferramenta Porta ou Janela em uso, ou com uma janela nova;
  - nas Propriedades de uma porta ou janela, o botão do desenho;
  - no editor de tipos, o botão do desenho.
- **A janela é a do protótipo:** escura, com o vão à escala sobre uma grelha.
- **Montantes e travessas:**
  - arrastam-se para dentro do vão a partir das faixas tracejadas, por cima («↓ arraste para criar montante») e à
    esquerda («→ travessa»), com uma linha azul e a medida antes de largar;
  - movem-se pelas pegas âmbar, de 10 em 10 mm, ou com as setas (10 mm; Shift: 100 mm);
  - perto do meio dos dois painéis, a pega fica no meio;
  - tiram-se com o «×».
- **O tamanho do vão** muda-se pelo lado direito, pelo de baixo ou pelo canto.
- **Cotas editáveis:** cada coluna, a largura total, a altura total e os painéis de uma coluna.
  - Aceitam contas (por exemplo «2400/3»).
  - «EQ» marca as colunas com a mesma largura.
- **Barra de cima:** Vista exterior / Vista interior (espelhada), **Travessas ligadas** (as travessas à mesma altura
  andam juntas; desligadas, uma travessa nova fica só na sua coluna) e **Igualar colunas**.
- **O cartão do painel:** um clique num painel abre-o.
  - **12 aberturas:** as 8 do protótipo — fixo, batente esquerdo e direito, basculante, projetante, oscilobatente,
    correr, pivotante — e ainda oscilobatente direito, correr para a esquerda, guilhotina e pivotante horizontal.
  - Nas portas, as folhas de baixo abrem como portas: fixo, folhas, correr, vaivém, harmónio.
  - **5 enchimentos:** vidro, vidro fosco, painel opaco, madeira, veneziana.
  - **Dividir │**, **Dividir ─** e **Copiar p/ linha**.
- **Vários vãos em separadores** (J01, P01…), cada um com a sua medida.
  - «+» começa um a partir dos modelos do protótipo: janela de 2 folhas, janela com bandeira, porta simples, porta
    com bandeira e lateral, porta-janela de correr, vão livre.
  - **Duplicar** copia o vão aberto.
- **Rodapé:** tipo (Janela/Porta), referência, sistema, cor do perfil, aro (mm) e peitoril (mm).
  - Mostra o vão, a área envidraçada, a área de abertura e a classe IFC (por exemplo «IfcWindow ·
    DOUBLE_PANEL_VERTICAL»).
  - O que estiver mal aparece a vermelho, e então não se pode guardar.
- **Mais opções…:** o resto do antigo gerador, para nada se perder — profundidade do aro, folhas, vidro, peitoril ou
  soleira de pedra, estore, guarnições, arco, portadas, mosquiteiro, grade, ferragens, pingadeira e os materiais de
  cada parte.
- **Guardar e inserir:**
  - **Guardar** grava como tipos os vãos novos ou mudados (um passo de desfazer cada). As portas e janelas desses
    tipos já colocadas acompanham.
  - **Inserir no modelo** grava e liga a ferramenta Porta ou Janela com o vão mostrado: depois clica-se numa parede.
  - Um vão que mudou de janela para porta (ou ao contrário) fica um tipo novo.
- **Conversão dos tipos antigos:** abertos no Studio, ficam em grelha. Uma bandeira inteira sobre duas folhas passa
  a dois vidros fixos, um por coluna.
- O tipo de letra do protótipo (IBM Plex) usa-se se estiver instalado; senão, o mais parecido do sistema.
- Testes:
  - sem janela, o modelo do Studio:
    - montantes e travessas metidos, movidos (ligados e sozinhos, com o meio a atrair) e tirados;
    - colunas igualadas;
    - cotas com contas;
    - copiar para a linha;
    - largura pela esquerda;
    - janela feita porta;
    - ida e volta para o desenho, e uma porta por linhas feita grelha;
    - métricas;
    - os modelos sem avisos;
  - com a janela real, com o rato:
    - um montante largado da faixa e outro arrastado 100 mm;
    - uma cota escrita como conta;
    - o cartão com oscilobatente e vidro fosco;
    - uma travessa só numa coluna;
    - a vista interior;
    - a porta dos modelos num segundo separador;
    - Inserir no modelo: os dois tipos gravados, a ferramenta Porta ligada com a porta;
  - os percursos do antigo gerador (0.289–0.296) feitos agora pelo Studio: estore, mosquiteiro e grade; arco;
    portadas; folhas debaixo do arco e a de correr recusada.

## 0.306.0 — 2026-10-29

**O núcleo das portas e janelas por colunas** (Caixilho Studio, passo 1, pedido do dono). É a base do Caixilho
Studio (0.307).

- **Desenho por colunas:** os montantes vão a toda a altura e cada coluna tem as suas travessas, como no protótipo.
  - Até aqui só havia o desenho por linhas: as travessas a toda a largura e os montantes dentro de cada linha. Esse
    continua igual.
  - Duas colunas de uma só folha que fecham uma na outra (um par de batentes, duas folhas de correr) ficam sem
    montante entre elas. Duas guilhotinas na mesma coluna ficam sem travessa.
  - Funcionam por colunas, como por linhas:
    - os nomes IFC (OperationType das portas pelas células de baixo, PartitioningType das janelas);
    - os desvios das travessas e montantes no aro (Lining);
    - o espelho;
    - o arco (as células de cima de cada coluna debaixo dele);
    - os avisos de medidas.
- **Enchimentos por painel:** vidro, **vidro fosco**, painel opaco, **madeira** e **veneziana** (lâminas fixas,
  como as das portadas).
  - O vidro fosco conta como vidro na fração envidraçada (GlazingAreaFraction) e na constituinte «Glazing».
  - A madeira conta como «Framing».
- **Materiais novos:**
  - vidro fosco;
  - os perfis de cada sistema em cada cor: Alumínio, PVC, Madeira e Aço, em grafite, branco, bronze e cor madeira
    (por exemplo «Alumínio grafite»). São 16 materiais, com a cor certa no 3D e no IFC.
- O desenho guardado no tipo (o «Desenho» em texto) leva o modo por colunas e os enchimentos novos. Os tipos antigos
  leem-se como estavam.
- Testes (sem janela):
  - uma janela de 3 colunas com basculantes por cima: dois montantes a toda a altura, uma travessa por coluna, seis
    vidros;
  - um par de batentes sem montante;
  - uma porta por colunas, SWING_FIXED_LEFT;
  - as partições das janelas;
  - os enchimentos novos com os seus materiais e as lâminas da veneziana;
  - espelhada;
  - guardada e lida em texto.

## 0.305.0 — 2026-10-29

**Ranhura** (modificadores de paredes, passo 8, pedido do dono; como o «Wall Reveal» do Revit). Com esta versão
ficam feitos todos os modificadores de paredes. A ferramenta está no separador **Modificar | Paredes** (painel Vãos e
acabamentos) e na **Arquitetura** (painel Paredes).

- **Ranhura:** um friso rebaixado na face de uma parede, feito com um clique na face.
  - Horizontal, à altura do clique, ao longo da parede toda; ou vertical (Tab), onde se clica, a subir a parede toda.
  - A largura (2 cm à partida) e a profundidade (1 cm) mudam-se na barra de cima.
  - Com **Tirar ranhuras** ligado, um clique tira a ranhura que está por baixo.
  - Posições ao centímetro.
- No IFC é uma `IfcOpeningElement` RECESS (rebaixo) da parede, com os seus parâmetros (lado, direção, posição,
  largura, profundidade).
- Volta a fazer-se para caber na parede sempre que a parede muda:
  - mais comprida, mais alta ou com outra espessura;
  - dividida: a horizontal fica nas duas partes;
  - juntada: fica uma só;
  - num canto em meia-esquadria, chega até ao corte.
- Não conta como vão:
  - não impede encurtar nem dividir a parede;
  - não corta os rodapés;
  - só corta o revestimento da sua face.
- O separador **Modificar | Paredes** fica arrumado assim, com os modificadores das paredes primeiro:
  - Modificar parede (virar, perfil, topo e base);
  - Ligações (junções, juntar, ligar e soltar as pontas, ortogonalizar);
  - Dividir e aparar;
  - Vãos e acabamentos (porta, janela, abertura, revestimento, rodapé, ranhura);
  - no fim, o painel geral Modificar (mover, rodar, espelhar…, cotar paredes), que também está na Modelagem. É o
    primeiro a recolher-se quando falta largura.
  - A 1280 px cabem todos os outros.
- Os painéis antigos da fita saem logo quando se muda de separador, em vez de ficarem à espera de o Qt os apagar.
- Testes:
  - sem janela:
    - uma ranhura de 2 × 1 cm a 1,00 numa parede de 6 m tira-lhe 6 × 0,02 × 0,01;
    - com a parede 2 m mais comprida, a ranhura estica com ela;
    - uma vertical na outra face;
    - dividida aos 5 m, as duas partes ficam com a horizontal e a primeira com a vertical;
    - juntada outra vez, fica uma horizontal;
    - a vertical tirada;
    - uma ranhura mais funda do que meia parede é recusada;
    - IFC válido;
  - com a janela real: um clique a 1,00 e, com Tab, outro a 4,00 fazem as duas ranhuras.

## 0.304.0 — 2026-10-29

**Rodapé, sanca, friso ou cimalha na parede** (modificadores de paredes, passo 7, pedido do dono; como o «Wall
Sweep» do Revit). A ferramenta **Rodapé / sanca na parede** está no separador **Modificar | Paredes** (painel Vãos
e acabamentos) e na **Arquitetura** (painel Paredes).

- Um clique na face de uma parede faz correr o perfil ao longo dessa face.
  - Continua, do mesmo lado, pelas faces das paredes ligadas a ela (em canto ou em T), com os cantos em
    meia-esquadria, até uma ponta solta.
  - Se as faces fecham, dá a volta completa: por dentro de uma sala, ou por fora do edifício (uma cimalha à volta
    da casa).
  - Fica sempre do lado de fora da parede.
- Pára nas portas, como o Perfil corrido.
- Acompanha as paredes quando mudam (movidas, esticadas, divididas): o programa volta a seguir as faces a partir do
  ponto clicado, que anda com a parede.
- O perfil e a altura ao chão escolhem-se na barra de cima: rodapé, sanca, friso, cimalha ou um perfil próprio do
  projeto.
- Ao passar o rato, vê-se o caminho que o perfil vai fazer.
- Por dentro, as faces seguem o contorno da união das paredes ligadas. Quando duas paredes se tocam com uma folga
  mínima (arredondamentos), o programa fecha essa fenda; senão, o perfil entraria por ela e voltaria.
- Testes:
  - sem janela:
    - numa casa de 10 × 6 m com uma porta, o rodapé clicado por dentro dá a volta à sala, menos a porta;
    - a cimalha clicada por fora dá a volta à casa (32,80 m);
    - com a parede do lado nascente 1 m mais para fora, os dois ficam 2 m mais compridos;
    - num L de duas paredes, o perfil vai de uma ponta solta à outra (7,20 m);
    - IFC válido;
  - com a janela real: um clique por dentro de uma casa de 8 × 5 m faz um rodapé fechado de 25,20 m.

## 0.303.0 — 2026-10-29

**Abertura na parede** (modificadores de paredes, passo 6, pedido do dono; como o «Wall Opening» do Revit). A
ferramenta está no separador **Modificar | Paredes** (painel Vãos e acabamentos) e na **Arquitetura** (painel Vãos).

- Como se usa:
  - um clique na face de uma parede reta marca um canto da abertura;
  - um segundo clique marca o canto oposto; em vez disso, pode escrever-se a largura e a altura (por exemplo
    «1,20;2,10») e carregar em Enter;
  - antes do segundo clique, veem-se o retângulo na face, a largura, a altura e a altura a que começa;
  - os cantos andam ao centímetro.
- A abertura atravessa a parede e não leva porta nem janela. No IFC é uma `IfcOpeningElement` OPENING da parede.
  - Vai com a parede quando ela se move.
  - Numa cópia de um grupo, abre-se em todas as cópias.
- O programa recusa e explica porquê quando a abertura passa:
  - para lá das pontas da parede;
  - acima do topo;
  - fora do perfil desenhado da parede (numa empena, pode subir até debaixo da empena).
- Um passo de desfazer.
- Testes:
  - sem janela:
    - uma abertura de 1,20 × 1,00 a 2 m e a 0,90 tira à parede o volume certo e não tem porta nem janela;
    - vai com a parede;
    - para lá do topo e da ponta é recusada;
    - debaixo de uma empena é aceite;
    - Ctrl+Z desfaz;
    - IFC válido;
  - com a janela real: um clique e «1,2;1» escrito fazem a abertura.

## 0.302.0 — 2026-10-29

**Ligar e desligar a base** (modificadores de paredes, passo 5, pedido do dono; como o «Attach / Detach Base» do
Revit). Os botões estão no separador **Modificar | Paredes**, painel Modificar parede.

- **Ligar a base:** selecionam-se paredes ou pilares e uma laje ou sapata por baixo (Shift + clique). Clica-se em
  Ligar a base:
  - os elementos descem (ou sobem) até à face de cima da laje ou sapata;
  - o topo fica onde estava;
  - passam a acompanhá-la quando ela muda (sobe, desce, muda de espessura).
- **Desligar a base:** deixam de a acompanhar e ficam onde estão.
- A ligação fica no parâmetro «BaseLaje» do elemento, ao lado do «TopoLaje» de 0.106.
- Quando lajes ou sapatas mudam, o programa só procura os elementos ligados nos pisos delas, não no modelo todo.
- Numa cópia de um grupo, todas as cópias se ligam.
- Um passo de desfazer cada.
- Testes:
  - sem janela:
    - uma parede e um pilar sobre uma laje com o topo a −0,18 ficam com a base a −0,18 e o topo a 2,80;
    - com a laje 20 cm mais abaixo, acompanham;
    - a parede desligada fica e o pilar acompanha;
    - Ctrl+Z desfaz;
    - IFC válido;
  - com a janela real: Ligar a base e Desligar a base pelos botões da fita.

## 0.301.0 — 2026-10-29

**Junções de paredes** (modificadores de paredes, passo 4, pedido do dono; como o «Wall Joins» do Revit). A ferramenta
está no separador **Modificar | Paredes** (painel Ligações) e na **Modelagem** (painel Modificar).

- Num canto em ângulo reto, escolhe-se como as paredes se encontram:
  - **Topo a topo:** a parede clicada passa e a outra pára na face dela;
  - **Meia-esquadria:** as duas acabam no cruzamento dos eixos, cortadas a 45°.
- Como se usa:
  - escolhe-se a junção na barra de cima (ou com Tab);
  - clica-se numa parede, perto do canto;
  - antes do clique, um ponto verde mostra o canto que vai mudar.
- A escolha fica guardada na ligação do IFC: a meia-esquadria fica no nome da `IfcRelConnectsPathElements`, e quem
  passa é a parede «relating».
  - O canto mantém-se quando as paredes se movem, esticam ou mudam de espessura.
- Nos outros ângulos, as paredes já se juntam em meia-esquadria. Aí, e nas pontas que não fazem canto, o programa
  explica porquê.
- Um passo de desfazer por clique.
- Testes:
  - sem janela:
    - num L desenhado em cadeia, a primeira parede passa;
    - feita passar a segunda, a primeira pára na face dela (4,90);
    - em meia-esquadria, as duas acabam no cruzamento, cortadas a 45°;
    - a meia-esquadria continua quando uma parede se move;
    - um canto a 60° é recusado, e uma ponta sem canto também;
    - Ctrl+Z desfaz;
    - IFC válido;
  - com a janela real, vista de cima:
    - um clique perto do canto troca a parede que passa;
    - Tab e outro clique fazem a meia-esquadria.

## 0.300.0 — 2026-10-29

**Dividir com folga e aparar / estender até um limite** (modificadores de paredes, passo 3, pedido do dono). As duas
ferramentas estão no separador **Modificar | Paredes** (painel Dividir e aparar) e na **Modelagem** (painel
Modificar).

- **Dividir com folga** (como o «Split with Gap» do Revit): um clique numa parede divide-a e deixa uma folga entre as
  duas partes.
  - A folga é de 2 cm à partida e muda-se na barra de cima.
  - As duas partes acabam a direito nos lados da folga e não ficam ligadas uma à outra.
  - Também se pode digitar a distância à ponta mais perto, e o meio da parede atrai o cursor, como no Dividir parede.
  - Se uma porta, janela ou vão ficasse dentro da folga, o programa recusa e explica porquê.
- O **Dividir parede** tem agora também a opção **Folga** na barra de cima (0 à partida: divide ponta com ponta).
- **Aparar / estender a um limite** (como o «Trim/Extend Multiple Elements» do Revit):
  - um clique na parede que serve de limite;
  - depois, um clique em cada parede a levar até ele, do lado que fica: as mais curtas estendem-se, as que o
    atravessam são aparadas;
  - antes do clique vê-se onde fica a ponta;
  - Esc escolhe outro limite; outro Esc volta a Selecionar.
- Onde a parede toca o limite:
  - a meio do limite, fica em T, parada na face dele;
  - na ponta do limite, faz canto (o limite passa), a não ser que essa ponta já seja outro canto;
  - para lá das pontas do limite, fica no alinhamento dele, sem se ligar.
- Paredes paralelas ao limite: o programa recusa e explica porquê.
- Um passo de desfazer por clique.
- Testes:
  - sem janela:
    - uma parede de 10 m dividida aos 5 m com 4 cm de folga fica com 4,98 + 4,98, sem se ligarem;
    - a folga sobre a porta é recusada;
    - com um limite em x = 9: uma parede curta estendida e uma que o atravessa aparada, ambas paradas na face dele
      (8,90) e ligadas em T;
    - uma parede na ponta do limite faz canto;
    - uma parede para lá do limite fica no alinhamento dele, sem se ligar;
    - uma parede paralela é recusada;
    - Ctrl+Z desfaz;
    - IFC válido;
  - com a janela real, vista de cima:
    - Dividir com folga no meio de uma parede de 6 m: duas partes de 2,99 m;
    - Aparar a um limite: o limite e depois duas paredes, ambas a 8,90 e ligadas.

## 0.299.0 — 2026-10-29

**Virar a parede e ligar as pontas** (modificadores de paredes, passo 2, pedido do dono). As duas ferramentas estão
no separador **Modificar | Paredes**.

- **Virar a parede** (como as setas de virar do Revit): o interior e o exterior das paredes selecionadas trocam de
  lugar.
  - As camadas passam a ir pela ordem contrária: o que estava numa face passa para a outra. Por exemplo, um isolamento
    pelo lado de fora vem para dentro.
  - Ficam onde estavam: o corpo da parede, as ligações, os revestimentos, as portas e as janelas.
  - Vê-se nas plantas, nas tramas das camadas.
  - No IFC, troca-se o sentido e o ponto de partida das camadas da parede (`IfcMaterialLayerSetUsage`). Se essas
    camadas eram partilhadas com outra parede, esta parede passa primeiro a ter as suas próprias.
  - Uma parede virada continua virada quando se lhe muda o tipo.
  - Serve também para as paredes curvas.
  - Numa cópia de um grupo, todas as cópias viram.
- **Ligar as pontas** (como o «Permitir ligação» do Revit), o contrário de **Soltar ligações**: as pontas soltas das
  paredes selecionadas voltam a ligar-se à parede que tocam.
  - Na ponta de outra parede, fazem canto; a meio de outra parede, fazem um T.
  - Ficam ligadas como se tivessem sido desenhadas assim: o canto refaz-se e passam a acompanhar a outra parede.
  - O programa procura só nas paredes do mesmo piso, a menos de meia espessura da ponta.
  - Também liga às paredes curvas.
- Um passo de desfazer cada.
- O separador **Modificar | Paredes** aparece também quando se selecionam paredes curvas.
- Testes:
  - sem janela:
    - uma parede com o isolamento numa face virada: o isolamento passa para a outra face e a parede fica no mesmo
      sítio;
    - virada outra vez, volta ao que era;
    - virada e com outro tipo, continua virada, com as camadas dentro da espessura;
    - Ctrl+Z desfaz;
    - um canto solto e ligado outra vez fica igual ao que era;
    - uma parede que acaba no eixo de outra fica em T, parada na face dela;
    - uma parede longe não se liga a nada;
    - IFC válido;
  - com a janela real:
    - Virar a parede pelo botão da fita, na planta;
    - Soltar ligações e depois Ligar as pontas num canto: o canto volta a ser o que era.

## 0.298.0 — 2026-10-29

**A fita por disciplinas e o separador «Modificar | Paredes»** (modificadores de paredes, passo 1, pedido do dono).

- Antes desta versão, a 1280 px de largura, metade das ferramentas de cada disciplina ficava escondida na seta » (na
  Arquitetura: a cobertura, as salas, o mobiliário e as ferramentas das paredes), e os separadores já não cabiam no
  cabeçalho.
- **As disciplinas pela ordem do trabalho num projeto:** Início · Modelagem · Gerenciar · Massa e Estudos · Terreno ·
  Arquitetura · Estrutura · Instalações · Colaborar · Anotar · Visualizar · Render.
  - A Modelagem (desenhar e modificar) serve em qualquer fase e fica logo a seguir ao Início.
  - O Gerenciar (preparar o projeto) vem antes de se modelar.
  - O Colaborar (coordenar) vem antes de se documentar.
  - Os atalhos seguem a ordem: Ctrl+1 Modelagem, Ctrl+2 Gerenciar, Ctrl+3 Massa e Estudos, Ctrl+4 Terreno, Ctrl+5
    Arquitetura, Ctrl+6 Estrutura, Ctrl+7 Instalações, Ctrl+8 Colaborar, Ctrl+9 Anotar.
  - Um projeto aberto pela primeira vez começa na Arquitetura. Depois, o programa lembra a última disciplina usada.
- **Painéis com nome, como no Revit**, pela ordem em que se usam. Por exemplo:
  - Arquitetura: Selecionar · Paredes · Vãos · Pisos e coberturas · Circulação · Salas e tetos · Mobiliário;
  - Estrutura: Selecionar · Grelha · Elementos · Automático · Cálculo · Mapas.
- As ferramentas principais têm botões grandes (ícone por cima do nome). As outras ficam em colunas de três botões
  pequenos (ícone ao lado do nome).
- A Modelagem fica só com o que é comum a todas as disciplinas: desenhar, modificar, medir e criar. As paredes, portas
  e restantes elementos estão nas suas disciplinas.
- **Nada fica escondido.** Quando a janela é estreita, os painéis da direita recolhem-se, cada um num botão com o seu
  nome. Um clique nesse botão mostra as ferramentas do painel.
- A fita tem sempre a mesma altura, em qualquer disciplina, e as vistas por baixo não se mexem.
- **O separador «Modificar | Paredes»** (verde, como no Revit) aparece no fim dos separadores quando se selecionam
  paredes e fica à vista. Tem os painéis:
  - Selecionar;
  - Modificar: mover, rodar, espelhar, alinhar, offset, escala, apagar;
  - Ligações: juntar paredes, soltar ligações, ortogonalizar;
  - Dividir e aparar;
  - Modificar parede: editar e repor perfil, ligar e desligar o topo;
  - Acabamentos: revestimento, perfil corrido;
  - Cotas.

  Pode-se clicar noutro separador sem perder a seleção. Quando a seleção se esvazia (Esc), o separador desaparece e
  volta a disciplina onde se estava.
- Dois modificadores novos:
  - **Repor perfil:** a parede com o alçado desenhado volta a ser um retângulo, com a altura do ponto mais alto do
    perfil. Se o perfil vinha de uma cobertura, deixa de a seguir.
  - **Desligar o topo:** as paredes e pilares ligados a uma laje ou cobertura deixam de a seguir e ficam com a altura
    que têm.

  Os dois também aparecem na barra contextual quando servem.
- **Ícones novos para 57 comandos** que só tinham iniciais, como localização, fases, pavimentos, tipos, materiais,
  partilhar, sincronizar, conflitos, notas BCF, vistas, painéis e o botão do meio do rato. Seguem o desenho dos outros
  ícones.
- Os botões da fita guardam o seu nome curto e o seu ícone quando a ação muda de estado (marcada, ativa). Antes, o Qt
  repunha o nome comprido.
- O cabeçalho:
  - todos os separadores estão sempre à vista;
  - quando falta espaço, primeiro desaparece o nome do programa e depois o do projeto, que estão no título da janela;
  - só a uma largura muito pequena os nomes dos separadores se encurtam com «…».
- Testes:
  - sem janela:
    - todas as ferramentas estão nalgum painel, sem repetições numa disciplina;
    - as colunas têm no máximo três botões;
    - cada painel tem nome;
    - o separador das paredes tem todos os modificadores;
    - desligar o topo de uma parede e de um pilar presos a uma laje: ficam com 3,00 quando a laje sobe; Ctrl+Z
      volta a ligá-los;
    - repor o perfil das empenas de uma casa presas à cobertura: retângulos com a altura da empena, que já não
      mudam quando a cobertura muda;
    - IFC válido;
  - com a janela real:
    - Ctrl+6 abre a Estrutura;
    - uma parede selecionada faz aparecer o separador verde, com todos os nomes inteiros;
    - Desligar o topo e Repor perfil pelos botões da fita;
    - o separador da Arquitetura funciona com a seleção ativa;
    - Esc tira o separador verde;
    - a 1000 px, cinco painéis recolhidos, com as ferramentas nos menus.

## 0.297.0 — 2026-10-29

**O peitoril vai sozinho para o lado de fora** (motor de portas e janelas, passo 9, pedido do dono).

- Uma janela posta numa parede exterior (IsExternal) fica virada com o lado de fora para fora do edifício, mesmo que
  se clique na parede pelo lado de dentro. O lado de fora é onde ficam o peitoril, o estore, o mosquiteiro, a grade e
  as portadas. Para saber qual é o lado de fora, o programa usa o mesmo cálculo das paredes exteriores (0.267): ao
  meio da janela, uma face da parede dá para uma divisão e a outra não.
- Quando as paredes de um piso mudam (por exemplo, ao fechar a casa com a última parede), as janelas desse piso são
  vistas outra vez e viradas, se for preciso. Tudo isto faz parte do mesmo passo de desfazer.
- Uma janela que não é simétrica (por exemplo, oscilobatente) passa para o seu tipo espelhado, e as dobradiças ficam no
  mesmo montante.
- Uma janela virada à mão (Propriedades, **Virar a janela → Lado**) fica como o utilizador a deixou. O programa guarda
  isso no parâmetro «LadoManual» da janela e não volta a virá-la.
- Não mudam:
  - as janelas das paredes interiores;
  - as janelas de paredes sem divisões de nenhum dos lados (um muro sozinho);
  - as portas. O lado para onde a porta abre continua a ser o lado em que se clica.

## 0.296.0 — 2026-10-29

**Folhas de abrir dentro do arco** (motor de portas e janelas, passo 8, pedido do dono).

- Uma folha envidraçada pode agora subir para dentro do arco. A travessa de cima segue a curva do aro numa só peça,
  sem juntas, e o vidro é cortado pela curva, à largura de um perfil da folha.
- Debaixo do arco, uma folha pode ser:
  - de batente;
  - oscilobatente;
  - basculante (uma bandeira em meia-lua que abre);
  - pivotante;
  - de vaivém.
  O gerador só recusa as folhas que não podem abrir debaixo de uma curva: projetante (dobradiças em cima), de correr,
  guilhotina e harmónio.
- Para ter as folhas até ao arco, basta tirar a linha do arco no gerador (**Tirar a linha**): as folhas da linha de
  baixo sobem até à curva.
- Ao escolher um arco, a linha de cima fica com as suas aberturas. Só as que não podem abrir debaixo do arco passam a
  fixo (antes, ficavam todas fixas).
- As dobradiças, os puxadores e os sinais de abertura nos alçados acompanham a curva:
  - as dobradiças ficam abaixo do arranque, no montante onde está a dobradiça;
  - o puxador fica a meia altura do lado que abre;
  - as linhas do sinal vão aos cantos da folha, em cima da curva.
- No gerador, a célula escolhida é realçada com a forma da curva, e um clique dentro do arco escolhe-a.

## 0.295.0 — 2026-10-29

**Portadas de lâminas** (motor de portas e janelas, passo 7, pedido do dono).

- No gerador há um campo novo, **Portadas de lâminas**, com quatro escolhas:
  - sem portadas;
  - 1 folha, dobradiças à esquerda;
  - 1 folha, dobradiças à direita;
  - 2 folhas.
  A caixa **Portadas abertas (rebatidas sobre a parede)** escolhe a posição em que ficam desenhadas.
- Cada folha tem montantes de 6 cm, travessa de baixo de 10 cm e de cima de 6 cm. Tem 3,5 cm de espessura e lâminas
  inclinadas para fora (a água escorre para fora), uma a cada 4,5 cm mais ou menos. As folhas com mais de 1,40 m de
  lâminas levam uma travessa a meio. As dobradiças ficam na aresta do vão, na face da parede.
- **Fechadas**, as portadas ficam dentro do vão, à face exterior da parede, assentes no peitoril ou na soleira. Se o
  mosquiteiro ou a grade não deixarem espaço, ficam por fora da parede.
- **Abertas**, cada folha roda meia volta nas dobradiças e fica deitada na parede ao lado do vão.
- Num vão em arco, as portadas são cortadas pelo arco, e a travessa de cima segue a curva numa só peça.
- As portadas são de madeira; o material escolhe-se em **Materiais → Portadas**.
- Aparecem também:
  - na planta de uma porta (o contorno das folhas);
  - no mapa de vãos (desenhadas abertas, com a linha «Com portadas de lâminas»);
  - no alçado do gerador (por cima da janela, meio transparentes).
- O gerador avisa quando há portadas e estore ao mesmo tempo, e quando as folhas ficam pequenas demais para as lâminas.
- Corrigido no gerador: a altura escrita ao lado do desenho passou a ficar à esquerda de tudo, sem tapar o desenho.

## 0.294.0 — 2026-10-29

**Vãos em arco** (motor de portas e janelas, passo 6; o motor fica completo).

- No gerador há um campo novo, **Arco**, com quatro escolhas:
  - reto;
  - de volta inteira (meia circunferência);
  - abatido (com a **flecha** escrita; em branco, um sexto da largura);
  - ogival (equilátero).
  Ao escolher um arco, a linha de cima passa a ser o arco: um fixo com a altura da flecha. Se só havia uma linha, é
  criada uma.
- O arco do aro é uma faixa curva feita de 24 peças. Os aros sobem até ao arranque do arco, e as guarnições de uma
  porta contornam o arco. Os vidros, painéis e travessas que ficam por baixo do arco são cortados por ele.
- O vão na parede é cortado com a forma do arco: no IFC, o vão passa a ser o contorno do arco extrudido através da
  parede (IfcArbitraryClosedProfileDef). Mantém essa forma quando a janela se move, quando se vira de lado, quando a
  parede muda de espessura, quando é espelhada e nas paredes curvas.
- Avisos no gerador:
  - um arco abatido com flecha acima de meia largura, ou um arco que não deixa pelo menos 0,30 m por baixo;
  - uma folha que entra no arco (debaixo do arco só pode haver fixos).
- O peitoril, a fração envidraçada (sobre a área do contorno em arco), o alçado do gerador e o mapa de vãos seguem o
  arco.
- Nova no catálogo: **Janela em arco 100×150 (peitoril 0,90)**, com duas folhas de batente debaixo de um arco de volta
  inteira fixo.

## 0.293.0 — 2026-10-29

**Mapa de vãos** (motor de portas e janelas, passo 5, segunda parte).

- O Navegador do Projeto ganha a vista **Mapa de vãos**, quando o projeto tem portas ou janelas. Com o botão direito,
  **Pôr na folha** coloca-a numa folha existente ou numa nova, a 1:50.
- Cada tipo de porta e de janela usado no projeto aparece desenhado em alçado, visto de fora, tal como o gerador o
  faz: aro, folhas, vidro, peitoril ou soleira, estore ou grade, e os sinais de abertura. Leva as cotas de largura e
  altura e, por baixo:
  - o nome;
  - «L × A»;
  - o peitoril (janelas);
  - a abertura (por exemplo «batente + oscilobatente»);
  - a quantidade, com as marcas (P1, P2… / J1…).
- Uma porta de mão direita conta com o tipo de origem, e uma janela espelhada também. Primeiro vêm as portas, depois
  as janelas, cada grupo por nome, seis por linha.

## 0.292.0 — 2026-10-29

**Sinais de abertura nos alçados e cortes** (motor de portas e janelas, passo 5, primeira parte).

- Nos alçados e nos cortes, cada folha de porta ou janela mostra como abre, com as convenções europeias:
  - as linhas encontram-se do lado das dobradiças;
  - a oscilobatente tem também as linhas que se encontram em baixo;
  - a projetante tem-nas em cima e a basculante em baixo;
  - a pivotante mostra o eixo;
  - a de correr e a guilhotina mostram uma seta para o lado onde abrem;
  - o harmónio mostra uma seta e as dobras.
- Aparecem no ecrã, na vista do alçado ou do corte, e nas folhas impressas (PDF e DXF). Vistas do outro lado, ficam ao
  espelho, como devem. O que está à frente esconde-as, como esconde o resto do modelo.
- Uma porta ou janela que o corte atravessa mostra o corte, sem sinais.
- No IFC, cada porta e janela guarda os seus sinais numa representação de alçado (contexto Model / Annotation /
  ELEVATION_VIEW, curvas 3D nas duas faces do aro), para outros programas os poderem ler.
- O alçado do gerador usa os mesmos sinais.

## 0.291.0 — 2026-10-29

**Estores, mosquiteiros e grades** (motor de portas e janelas, passo 4), por fora do aro, do lado exterior.

- **Estore**: a caixa no topo do vão, de uma face à outra da parede, com a altura escrita no gerador (por exemplo
  20 cm). O aro fica por baixo dela. As calhas ficam nos aros, por fora, e as lâminas descem a percentagem escolhida
  («Estore descido», de 0 a 100 %).
- **Mosquiteiro**: uma rede fixa num perfil fino, encostada ao aro por fora, a cobrir o vão livre.
- **Grade**: barras verticais de 16 mm, no máximo a 12 cm de eixo a eixo, com duas travessas. Fica mais para fora
  que o estore.
- Cada coisa tem o seu material no gerador: perfis do estore e do mosquiteiro (alumínio), rede (material novo «Rede
  mosquiteira») e grade (aço lacado preto).
- **Dados IFC preenchidos pelo desenho**, no conjunto comum do tipo:
  - GlazingAreaFraction: a parte envidraçada, vista em alçado. Uma porta sem vidro não o leva, porque o IFC pede um
    valor acima de 0;
  - numa janela, HasSillExternal: tem peitoril exterior.
- No alçado do gerador, as peças passam a ser desenhadas da mais afastada para a mais próxima, vistas de fora. A rede
  do mosquiteiro aparece semitransparente por cima do vidro.

## 0.290.0 — 2026-10-29

**Acabamentos das portas e janelas** (motor de portas e janelas, passo 3).

- **Peitoril** nas janelas: uma pedra por baixo do aro, da face interior do aro até 3 cm para fora da face exterior
  da parede, com a **pingadeira** por baixo do nariz (um rasgo de 1 cm de largura e 8 mm de fundo, a 1,5 cm do
  nariz). O aro assenta no peitoril. As janelas do catálogo trazem peitoril de 3 cm.
- **Soleira** nas portas: uma pedra entre os aros, de uma face à outra da parede e para fora da face exterior. A
  folha começa por cima dela. No IFC fica a ThresholdThickness. Nova no catálogo: **Porta exterior 90×210
  (soleira)**.
- O lado exterior é aquele de onde se empurra a folha, isto é, a face onde se clicou ao pôr a porta ou a janela. As
  folhas abrem para o outro lado.
- **Puxadores e dobradiças** desenhados, em aço inoxidável (o material muda-se no gerador):
  - porta de batente: três dobradiças do lado das dobradiças e um puxador de alavanca em cada face, a 1 m do chão,
    virado para as dobradiças;
  - janela de batente ou oscilobatente: duas dobradiças e o puxador na face interior, a meia altura, virado para
    baixo;
  - basculante, projetante e pivotante: o puxador na travessa livre;
  - de correr e harmónio: um puxador embutido junto ao bordo por onde se puxa;
  - vaivém: chapas de empurrar nas duas faces;
  - guilhotina: um puxador na travessa de baixo.
- **Guarnições à escolha**: nas duas faces, só na face para onde a porta abre, ou só na outra.
- No gerador há campos novos:
  - soleira ou peitoril (espessura; em branco, nenhum) e saliência para fora da parede;
  - pingadeira (janelas) e guarnições em (portas);
  - «Puxadores e dobradiças»;
  - os materiais da pedra e das ferragens.
- **Virar a janela**: nas Propriedades de uma janela, o botão **Lado** põe-na a abrir para o outro lado da parede e
  leva o peitoril para a outra face. As dobradiças ficam do mesmo lado, porque a janela passa ao tipo espelhado se
  não for simétrica.

## 0.289.0 — 2026-10-29

**Gerador de portas e janelas** (motor de portas e janelas, passo 2): o desenho de cada tipo passa a ser editável.

- Nova janela **Gerador de portas e janelas**. Abre-se de dois sítios:
  - nas Propriedades de uma porta ou janela selecionada (botão por baixo de «Editar tipo»);
  - no editor de tipos, onde o tipo de porta ou janela aparece desenhado em pequeno.
- À esquerda, o alçado é desenhado à medida que se muda: aro, guarnições, montantes, folhas e vidro nas cores dos
  materiais. Cada folha mostra como abre, com as convenções de alçado:
  - as linhas encontram-se do lado das dobradiças;
  - a oscilobatente tem também as linhas que se encontram em baixo;
  - a projetante tem-nas em cima e a basculante em baixo;
  - a pivotante mostra o eixo;
  - a de correr e a guilhotina mostram uma seta;
  - o harmónio mostra uma seta e as dobras.
  Ao lado, as medidas totais.
- Clicar numa célula do alçado seleciona-a. Para essa célula pode-se mudar:
  - a **abertura**: uma folha de porta só oferece as maneiras de abrir de uma porta;
  - o **enchimento**: vidro ou painel cego;
  - a **largura** e a **altura da linha**. Deixar em branco reparte o que sobra.
- Botões **Dividir** (acrescenta um fixo ao lado), **Juntar à direita**, **Linha por cima** (uma bandeira de 40 cm) e
  **Tirar a linha**.
- **Modelos** prontos:
  - 12 de janela: fixo, batente de 1 e 2 folhas, oscilobatente, batente + oscilobatente, correr de 2 folhas,
    fixo + batente, basculante, projetante, pivotante, guilhotina, 2 folhas com bandeira basculante;
  - 11 de porta: folha cega ou envidraçada, 2 folhas, com bandeira, com fixo lateral, de correr de 1 e 2 folhas,
    vaivém de 1 e 2 folhas, harmónio.
  Escolher um modelo muda só as folhas: as medidas dos perfis e os materiais ficam.
- **Perfis**: aro (largura e profundidade; numa porta, em branco é a da parede), folha (largura do perfil e
  espessura), montantes e travessas, vidro, guarnições. **Materiais**: aro e folhas, painéis cegos, vidro.
- Por baixo aparece o nome que o IFC vai ter (por exemplo SINGLE_SWING_LEFT ou TRIPLE_PANEL_TOP) e o que está mal: um
  perfil sem medida, um aro que não cabe, alturas ou larguras que não somam, uma folha pequena demais. Com um
  problema destes, o OK fica desligado.
- Ao carregar em OK o tipo é gravado (um só passo de desfazer) e todas as portas ou janelas desse tipo são refeitas,
  incluindo as das cópias e as da mão direita. A janela fica também com o PartitioningType do novo desenho.
- **Espelhar janelas**: uma janela que não é simétrica (por exemplo, oscilobatente à esquerda), quando espelhada com a
  parede, passa ao tipo «… (espelhada)», que é a imagem ao espelho. Espelhar outra vez volta ao tipo de origem.
  Quando o tipo de origem muda, as janelas espelhadas acompanham, também espelhadas. O tipo espelhado não aparece na
  lista de tipos, tal como o «(à direita)» das portas.

## 0.288.0 — 2026-10-28

**Motor de portas e janelas** (pedido do dono: «motor gerador de portas e janelas avançado»), passo 1: o motor de base.

- Cada tipo de porta ou janela passa a ser um **desenho**: um aro à volta de linhas de células (de baixo para cima),
  e cada célula é uma folha que abre de uma maneira ou um fixo, com vidro ou painel cego. As medidas das linhas e das
  células contam de eixo a eixo dos montantes e travessas. Uma medida 0 reparte o que sobra, e por isso o desenho
  acompanha a largura e a altura do tipo.
- Aberturas: fixo; de batente (dobradiças à esquerda ou à direita); oscilobatente; projetante; basculante;
  pivotante horizontal e vertical; de correr; guilhotina; vaivém; harmónio.
- Duas folhas que fecham uma contra a outra não têm montante no meio (janela de duas folhas, porta dupla). Duas
  folhas de correr sobrepõem-se num montante e andam em calhas diferentes.
- O corpo 3D é feito de peças, cada uma na cor do seu material: aro, montantes e travessas, folhas, vidro, painéis.
  - Uma porta de madeira tem aro da espessura da parede e **guarnições de 5 cm nas duas faces**.
  - Um fixo ao nível do chão, ao lado de uma porta, fica sobre uma travessa.
  - Uma janela de alumínio tem aro de 7 cm de profundidade, a meio da parede.
- O **símbolo da porta em planta** é feito pelo motor: aro, guarnições, cada folha aberta a 90° com o arco. Uma
  porta de vaivém tem arco para os dois lados, uma de correr tem a seta do lado para onde abre, uma de harmónio
  aparece dobrada, um fixo aparece fechado.
- No IFC, o tipo leva:
  - o desenho («Desenho» no ArqSynth_Parametros);
  - o OperationType ou PartitioningType que o desenho dá. Os casos que o IFC4 não nomeia ficam USERDEFINED, com o
    texto das aberturas;
  - as propriedades de aro e de folhas do IFC4: IfcDoorLiningProperties com as guarnições e a bandeira, e sem
    profundidade quando o aro acompanha a parede, como o IFC lê; IfcDoorPanelProperties; IfcWindowLiningProperties
    com montantes e travessas; IfcWindowPanelProperties;
  - os materiais com os nomes que o IFC4 dá às portas e janelas: um conjunto com «Lining» (aro), «Framing» (folhas)
    e «Glazing» (vidro), só com as partes que existem.
- Catálogo novo com o motor: porta de 2 folhas 140×210, porta de correr 90×210, porta de sacada envidraçada
  140×220, janela oscilobatente 100×120. As que já existiam têm agora desenho:
  - janela 120×120: duas folhas de batente;
  - janela 150×120: duas folhas de correr;
  - basculante 60×60: basculante;
  - portas: uma folha cega, com bandeira de vidro na porta com bandeira.
- Ficheiros antigos: um tipo sem desenho é desenhado pelo que o IFC diz dele (OperationType, PartitioningType, as
  aberturas das folhas, a bandeira). Nada muda nos tipos que já estão no projeto.
- Corrigido:
  - inverter as dobradiças de uma porta com bandeira perdia a bandeira e o material. Agora o tipo da mão direita é a
    imagem ao espelho, com as medidas, a bandeira e os materiais;
  - uma janela que se mexia (deslocar, mudar a parede) ficava com um aro de 10 cm, fosse qual fosse o tipo. Agora
    fica com o do seu desenho.

## 0.287.0 — 2026-10-28

**Mudar um grupo com muitas cópias, três vezes mais depressa** (o que a medição da 0.283 encontrou).

- No edifício grande, mudar a altura de uma parede de um grupo com 1000 cópias passou de **8,1 s para 2,75 s**, com a
  imagem desenhada. Medido com uma sonda que olha onde a linha principal está de 5 em 5 ms. As causas eram trabalho
  repetido mil vezes:
  - os parâmetros do programa de cada parede eram lidos transformando em dicionários todos os conjuntos de
    propriedades e quantidades dela (5 ms numa parede com vãos). Agora lê-se só o conjunto do programa, juntando-lhe o
    do tipo como antes;
  - a escala das unidades do projeto era calculada de novo em cada leitura (milhares por edição). Agora fica guardada
    para o ficheiro;
  - os vãos de cada parede eram medidos pelo motor de geometria mesmo quando a parede só crescia. Só se medem quando
    a parede encolhe, que é quando um vão pode ficar de fora;
  - a parede inteira era desfeita e refeita só para mudar a altura. Agora o mesmo sólido fica mais alto;
  - prender o topo de uma parede lia os níveis de todos os pisos; agora lê só o seu;
  - encontrar as cópias lia todos os parâmetros de cada membro de cada cópia; agora lê só o papel.
- O resto do benchmark do edifício grande ficou como estava: regenerar uma parede 24 ms, selecionar 1,6 ms,
  inferências 9 ms. A navegação mediu 51 fps nesta corrida e 62 fps na da 0.283. O desenho não mudou; é a variação
  do portátil já conhecida (ver ARQUITETURA, 0.18).
- Medido, mas por fazer: na reabertura do edifício grande, a 1.ª imagem leva 1,2 s parada na janela. Cerca de 0,4 s
  são juntar as peças nos lotes de desenho, e isso pode passar para a tarefa de fundo; cerca de 0,5 s são o envio
  para a placa gráfica (no WSL, OpenGL sobre Direct3D 12).

## 0.286.0 — 2026-10-28

**DWG** (o dono autorizou o conversor da Open Design Alliance).

- **Ligar um desenho DXF/DWG…** e **Terreno a partir de um DXF/DWG…** passam a aceitar também **DWG**. Um DWG é
  convertido em DXF pelo **ODA File Converter** e depois lido como qualquer DXF: com as camadas, os blocos, as
  unidades e os snaps. O **Modelo a partir do desenho…** funciona igual sobre um DWG ligado.
- O DXF convertido fica guardado na pasta do utilizador (`~/.arqsynth/dwg`) e só se volta a converter quando o DWG
  muda. Reabrir um projeto com um DWG ligado não o converte outra vez.
- O ODA File Converter é um programa à parte, gratuito, da Open Design Alliance (licença própria). Foi instalado no
  WSL: a versão 27.9 (`ODAFileConverter_QT6_lnxX64_11dll_27.9.deb`, 72,7 MB) e a biblioteca `libopengl0` de que
  precisa. No Windows instala-se a partir de opendesign.com. Sem ele, o programa diz que o DWG precisa do conversor.
- Testes:
  - núcleo: uma planta em DXF passada a DWG pelo conversor e lida de volta como DWG (a linha de 5 m, o pilar
    redondo), convertida uma só vez;
  - interface: a planta em DWG ligada no piso térreo, em milímetros, desenhada.

## 0.285.0 — 2026-10-28

**Armaduras agregadas ao seu elemento** (o dono escolheu ligar por IfcRelAggregates).

- Cada armadura (IfcReinforcingBar) passa a ser parte do seu pilar, viga, laje ou sapata, por IfcRelAggregates. É a
  «peça de betonagem» do Tekla: para um programa de estruturas, o betão e as suas barras são uma coisa só.
- Por ser parte do elemento, a armadura deixa de estar contida diretamente no piso (o IFC não quer as duas coisas ao
  mesmo tempo). Continua no piso do seu elemento: no navegador, nas plantas, nas tabelas e no certificado.
- Tudo o resto fica igual: as armaduras refazem-se quando o elemento muda, vão com ele quando é apagado, e o
  parâmetro do programa (Armadura) continua a dizer de quem são.
- Atenção: há visualizadores IFC antigos que, quando um elemento tem partes, mostram só as partes. Se num deles um
  pilar com armadura aparecer sem betão, é isso.
- Testes: cada armadura de um pórtico (pilares, vigas, sapatas e laje) é parte do seu elemento, não está contida
  diretamente e fica no piso dele; IFC válido, com as regras; uma viga mudada refaz as barras com uma só agregação.

## 0.284.0 — 2026-10-28

**Nuvens de pontos LAZ e E57** (o dono autorizou as bibliotecas novas).

- **Ligar uma nuvem de pontos…** (separadores Início e Colaborar) passa a ler também:
  - **LAZ**, o LAS comprimido, com o laspy e o lazrs. Respeita a escala, a origem e as cores, como no LAS. É lido aos
    bocados, por isso uma nuvem grande não fica toda em memória quando se pede só parte dos pontos.
  - **E57**, o formato dos scanners. Lê todas as varreduras do ficheiro, cada uma colocada pela sua pose, com as
    cores quando as tem. Usa o pye57.
- Bibliotecas novas, todas de código aberto: laspy 2.7.0 (BSD-2), lazrs 0.8.2 (MIT), pye57 0.4.19 (MIT) e
  pyquaternion 0.9.9 (MIT, de que o pye57 precisa). Estão no `requirements.txt` e instaladas no ambiente do WSL. Sem
  elas, o programa diz que o LAZ e o E57 precisam delas, em vez de falhar.
- Testes:
  - núcleo: um LAZ comprimido (escala, origem, cores) e um E57 com duas varreduras, a segunda deslocada pela pose,
    escritos pelas bibliotecas e lidos de volta; com poucos pontos pedidos;
  - interface: uma sala digitalizada ligada em LAZ e em E57, com todos os pontos no ecrã.

## 0.283.0 — 2026-10-28

**Desempenho em modelos grandes: medido antes de decidir** (o dono escolheu «medir primeiro»).

- O benchmark (`scripts/benchmark.py`) passa a medir também a memória no Linux (WSL): o pico da abertura e o da
  reabertura.
- Novo `scripts/geometry_process.py`: mede o motor de geometria do IfcOpenShell de duas maneiras, no próprio processo
  (como hoje) e num processo à parte que lê o IFC e devolve as formas. Para cada uma dá o tempo, a maior pausa da
  janela e a memória dos dois processos.
- Edifício grande (45 MB, 18 001 elementos, 968 mil triângulos), no WSL com a RTX 3050:

  | | Resultado | Meta |
  |---|---|---|
  | Abrir pela 1.ª vez até à 1.ª imagem | 3,1 s (≈ 34 s para 500 MB) | 500 MB < 20 s ✘ |
  | … até tudo pronto a editar | 15,6 s | |
  | Reabrir até à 1.ª imagem | 2,7 s (≈ 30 s para 500 MB) | 500 MB < 20 s ✘ |
  | Maior pausa da janela: abrir / reabrir | 730 / 1442 ms | |
  | Navegação | 62 fps | 60 fps ✔ |
  | Regenerar uma parede | 26 ms | < 50 ms ✔ |
  | Mudar uma parede de um grupo com 1000 cópias | 8,1 s | |
  | Memória (pico) | 1,75 GB | |

- O motor de geometria noutro processo **não compensa**:

  | | todas as formas | maior pausa da janela | memória |
  |---|---|---|---|
  | no próprio processo | 10,3 s | 111 ms | 583 MB |
  | num processo à parte | 11,1 s | 107 ms | 326 + 548 = 874 MB |

  O tempo e as pausas ficam iguais, e a memória sobe metade. As pausas de 0,7–1,4 s e os 2,7 s da reabertura não vêm
  do motor de geometria, mas do trabalho da janela: pôr os elementos no documento, as peças dos lotes e a 1.ª
  imagem. A mudança num grupo com 1000 cópias (8 s) também se otimiza no próprio processo. Ficam como trabalho
  seguinte, sem gastar mais memória.
- O programa não muda nesta versão: só as medições.

## 0.282.0 — 2026-10-28

**Prolongamentos dos corrimãos** (segundo ponto que dependia do dono; as medidas do DL 163/2006).

- As medidas são as do Decreto-Lei n.º 163/2006, de 8 de agosto (o regime da acessibilidade). Foram lidas na versão
  consolidada do Diário da República (2024-01-08), anexo, secção 2.4 (Escadas), ponto 2.4.9:
  - no topo, os corrimãos prolongam-se pelo menos 0,3 m para além do último degrau, paralelos ao piso;
  - na base, prolongam-se para além do primeiro degrau um comprimento igual ao cobertor, com a inclinação da escada.
- As guardas feitas **Nos lados de uma escada** já saem assim: o corrimão continua um cobertor antes do primeiro
  focinho, inclinado, e 0,30 m depois do último, de nível. Se o tipo de guarda tem corrimão (o corrimão de parede, ou
  um tipo com corrimão nos suportes), é ele que se prolonga. Se não tem, prolonga-se o corrimão de cima da guarda, a
  0,90 m, que é o que se agarra.
- Cada prolongamento acaba virado para baixo até ao piso, como a opção «Floor» dos prolongamentos do Revit: fica
  apoiado e sem ponta solta (o anexo, em 4.11.4, não quer extremidades salientes perigosas).
- Nas **Propriedades** de qualquer guarda aberta há **Prolongamento na base** e **Prolongamento no topo**, para
  mudar ou tirar. Numa rampa, o ponto 2.5.8 pede pelo menos 0,30 m nas duas pontas: escreva 0,30 nos dois campos. A
  nota nas Propriedades lembra estas medidas.
- No IFC, os prolongamentos são peças do próprio IfcRailing, com o material do corrimão. Os comprimentos ficam nos
  ArqSynth_Parametros (Prolongamentos).
- Testes:
  - núcleo: um corrimão de parede numa escada de 10 degraus, um cobertor para trás inclinado e descido ao piso, 0,30 m
    para a frente de nível e descido ao piso de cima; uma guarda de barras, prolongada pelo corrimão de cima; uma
    guarda fechada, sem prolongamentos;
  - IFC: as guardas de uma escada reta com os prolongamentos guardados, um cobertor antes do primeiro focinho, 0,30 m
    depois do último, até ao piso; o da base tirado nas Propriedades; uma guarda desenhada, sem prolongamentos; IFC
    válido. As guardas de escada dos testes anteriores descem agora até ao piso.

## 0.281.0 — 2026-10-28

**A telha do utilizador** (o «Registar telha» do ArqSynth Modeler; fecha as telhas, a fase R3 do addon).

- Qualquer componente pode ser uma telha. Faça a telha como componente: desenhada no programa (**Criar
  componente…**) ou trazida de outro ficheiro (**Trazer componentes de outro projeto…**). Deve estar em metros, com a
  origem num canto, x a largura, y o sentido da água (para baixo) e z para cima, como no addon.
- Com uma cópia do componente selecionada, as **Propriedades** têm **Usar como telha…**. A janela:
  - mede o componente (largura × comprimento × altura) e avisa se as medidas parecem não estar em metros;
  - propõe, como o addon, 90 % da largura para a largura útil e 80 % do comprimento para a galga;
  - pede o peso por telha e se as fiadas são desencontradas.

  **Registar** guarda a telha no projeto.
- A telha registada aparece na lista **Telha** de qualquer cobertura inclinada, depois das do addon. Assenta como as
  outras: fiadas, colunas, cortes nos rincões, telhas de cumeeira, contagem e peso. Como no addon, assenta direita
  sobre a água, sem se inclinar sobre a de baixo, porque a sua forma é a do utilizador.
- No IFC: um IfcCoveringType ROOFING com o nome da telha, que guarda a forma (RepresentationMaps) e os dados de
  assentamento (largura útil, galga, peso, desfasamento). Fica no ficheiro e não aparece na Biblioteca como
  componente. As coberturas de telhas feitas com ela são do tipo dela.
- Testes:
  - núcleo: a telha dada como no addon passa ao referencial do programa, com a mesma medida, fechada e virada para
    fora; assenta sem se inclinar;
  - IFC: um componente de 30 × 45 × 2 cm medido; uma medida estranha avisada; registado como IfcCoveringType ROOFING
    com a forma, fora da Biblioteca; na lista das telhas; um telhado de quatro águas com ele, com tantas telhas e tanto
    peso quantos a área dá; uma largura útil de 1 cm recusada; IFC válido; lido de volta do ficheiro;
  - interface: «Usar como telha…» num componente, a janela com as medidas propostas, a telha na lista da cobertura e
    o telhado feito com ela.

## 0.280.0 — 2026-10-28

**Chapas e painéis** (o resto do «telhado realístico» do ArqSynth Modeler: a chapa ondulada e o painel sanduíche).

- Em **Telha**, nas Propriedades de uma cobertura inclinada, há mais duas escolhas, com as medidas do addon:
  - **Chapa ondulada:** de fibrocimento, 0,92 × 2,00 m, largura útil 0,85 m, galga 1,80 m, 6 mm de espessura, três
    ondas por chapa, 12 kg. Assenta como as telhas, em fiadas e colunas.
  - **Painel sanduíche:** de aço, 1,06 m de largura, 1,00 m útil, 4 cm de espessura com três nervuras de 3,8 cm por
    cima. Assenta como no «modo painel» do addon: um painel por coluna, do beirado ao cimo da água, em troços até 6 m
    (o comprimento de fabrico). O peso conta-se pelo comprimento, 11 kg por cada 3 m de painel, como no addon.
- Os painéis sobre um rincão ou laró são cortados por ele, como as telhas. O addon acabava-os a direito a meio da
  coluna e deixava um triângulo por cobrir.
- Telhas e chapas junto aos rincões: o addon só guardava as peças cujo meio da parte à vista ficava dentro da água.
  Com chapas de 1,80 m isso deixava um triângulo descoberto junto a cada rincão. Agora fica qualquer peça que toque a
  água, cortada pelo rincão, e o telhado fica todo coberto. Há mais telhas cortadas, como em obra: na casa de 10 × 6 m,
  1450 marselhas em vez de 1290.
- As Propriedades chamam às peças **Telhas**, **Chapas** ou **Painéis**, conforme a escolha. O rodapé também.
- Novo material: **Fibrocimento**.
- Testes:
  - núcleo: o painel fechado, liso por baixo e com nervuras por cima; num telhado de uma água com 11 m de pendente,
    um painel por coluna em dois troços, com o peso pelo comprimento; num de quatro águas, painéis cortados nos
    rincões; a chapa ondulada sem nenhum ponto das águas descoberto;
  - IFC: o painel sanduíche de aço, tantos painéis quantos o núcleo dá, no ecrã como o núcleo os põe, IFC válido;
  - interface: o painel sanduíche e a chapa ondulada escolhidos nas Propriedades, com o material certo.

## 0.279.0 — 2026-10-28

**Telhas** (o «telhado realístico» do ArqSynth Modeler, a fase R3; primeiro dos pontos que dependiam do dono).

- Numa cobertura inclinada (uma, duas ou quatro águas, ou por blocos), as **Propriedades** têm **Telha** e
  **Telhas ▸ Assentar telhas**. Há as telhas do addon, com as medidas dele:
  - **Telha marselha:** largura útil 21 cm, galga 34 cm, 2,8 kg;
  - **Telha colonial (capa):** 17 cm, 33 cm, 2,2 kg;
  - **Telha plana:** 20 cm, 32 cm, 2,5 kg, em fiadas desencontradas.
- As telhas assentam como no addon:
  - em fiadas à galga, do beirado para cima, e em colunas à largura útil;
  - fica cada telha cuja parte à vista tem o meio dentro da água;
  - as telhas sobre um rincão, laró, cumeeira ou empena são cortadas por ele (o addon cortava-as com um booleano);
  - as telhas de cumeeira vão ao longo das cumeeiras e dos rincões, de ponta a ponta.
- Duas coisas melhores do que no addon:
  - cada telha assenta como em obra, com o rabo na ripa e a cabeça em cima da telha de baixo, e as fiadas
    sobrepõem-se sem se atravessarem;
  - as ondas de uma telha repetem-se à largura útil, por isso duas telhas lado a lado sobrepõem-se onda com onda.
- As Propriedades da cobertura dizem quantas telhas há (e quantas cortadas), as telhas de cumeeira e o peso.
  **Fiadas desencontradas** liga ou desliga o meio-desfasamento. Escolher outra telha refaz o telhado com ela, e
  **Tirar** tira as telhas.
- Mudar a cobertura (inclinação, blocos, tipo, madeiramento…) volta a assentar as telhas nela. Apagar a cobertura
  leva as telhas com ela.
- Nas **Tabelas** (Ctrl+T) há a tabela **Telhas**: por cobertura, a telha, as telhas, as cortadas, as telhas de
  cumeeira, o peso e a área.
- No IFC: um IfcCovering do tipo IfcCoveringType ROOFING («Telha marselha»…), de telha cerâmica, ligado à cobertura
  por IfcRelCoversBldgElements. A forma de uma telha guarda-se uma vez (IfcRepresentationMap) e repete-se em cada
  telha (IfcMappedItem), como o addon fazia com as instâncias. Mil telhas são mil referências à mesma forma, e um
  telhado de 10 × 6 m fica com cerca de 1 MB. Quantidades: Qto_CoveringBaseQuantities.GrossArea, e o
  ArqSynth_Telhado do programa (telhas, cortadas, telhas de cumeeira, peso).
- No ecrã as telhas leem-se diretamente do IFC, sem o motor de geometria: 1300 telhas em 0,03 s. Assentar as telhas
  de uma casa de 10 × 6 m demora meio segundo, e mudar a inclinação com telhas 0,7 s.
- Testes:
  - núcleo: cada telha fechada; um cubo cortado por um plano fecha e fica com metade; um telhado de quatro águas
    com tantas telhas quantas a área dá; cortes junto aos rincões; telhas de cumeeira de ponta a ponta das arestas;
    a cabeça de cada telha em cima da de baixo; a telha plana desencontrada;
  - IFC: o IfcCovering ROOFING, o seu tipo e material, a ligação à cobertura, os três mapas; tantas telhas e tanto
    peso quantos o núcleo dá; no ecrã, onde o núcleo as põe; mais inclinada, refeito; a telha plana; com
    madeiramento, as telhas sobem; IFC válido; apagada a cobertura, vão com ela; desfazer; uma plana recusada;
  - interface: o botão, as linhas nas Propriedades, a vista de fora e de perto, a tabela, outra telha e «Tirar».

## 0.278.0 — 2026-10-28

**Tipos de cobertura** (Fase 2, passo 4: «coberturas quando houver coberturas»; como os Roof Types do Revit).

- As coberturas têm agora tipos próprios, como as paredes e as lajes. Até aqui usavam um tipo de laje, não se podia
  trocar o tipo depois de desenhada e mudar o tipo no editor não chegava às coberturas.
- Há três tipos para começar: **Cobertura de concreto 12 cm**, **Cobertura de concreto 15 cm** e **Telhado de telha
  cerâmica** (uma camada de telha cerâmica de 3 cm). A ferramenta **Cobertura** desenha com estes tipos e
  começa na de 15 cm, que tem a mesma espessura da laje que usava antes.
- Nas **Propriedades** de uma cobertura, o **Tipo** passou a ser uma lista: escolher outro tipo muda as camadas e a
  espessura. A face de baixo fica assente nas paredes, por isso uma cobertura mais grossa sobe por cima. Uma
  cobertura sem paredes por baixo também mantém a face de baixo onde estava. O madeiramento refaz-se por baixo.
- Uma cobertura fina (a telha, 3 cm) não chega para tapar o topo de uma parede de 20 cm quando a face de baixo
  assenta na aresta de dentro: a aresta de fora da parede atravessava a telha e via-se como uma faixa clara no
  telhado. Agora a cobertura nunca fica a menos de 1 cm por cima da aresta de fora da parede. Por dentro fica uma
  folga sobre a parede, que é onde vai o frechal. Com madeiramento, a cobertura sobe menos essa folga, e os caibros
  continuam pousados nos frechais. As coberturas grossas (as de concreto) não mudam.
- **Editar tipo** abre o editor de tipos em **Coberturas**, com as camadas de baixo para cima. Mudar as camadas de um
  tipo muda todas as coberturas desse tipo. Pode duplicar um tipo para fazer outro (por exemplo, telha sobre
  isolamento).
- Em **Gerenciar ▸ Tipos para desenhar** há **Cobertura**, para escolher o tipo e desenhar logo.
- No IFC: cada cobertura tem o seu IfcRoofType, com o IfcMaterialLayerSet das camadas. O PredefinedType do tipo é
  NOTDEFINED, porque a forma (quatro águas, duas águas…) é de cada cobertura. A Referência do Pset_RoofCommon é o nome
  do tipo, e os dados do tipo (fogo, U…) ficam no próprio IfcRoofType, como nos outros tipos.
- As coberturas feitas antes continuam como estavam, com as camadas da laje e sem tipo. Ao escolher-lhes um tipo de
  cobertura nas Propriedades, ficam com ele.
- Testes:
  - IFC: o IfcRoofType NOTDEFINED com a cobertura em HIP_ROOF; as camadas no tipo; a cobertura assente com a
    espessura da telha; trocada para 15 cm, com o madeiramento, sobe só a diferença; o tipo mudado no editor de
    tipos, com todas as coberturas dele a seguir; uma cobertura antiga (tipo de laje) a receber um tipo de cobertura;
    uma cobertura por blocos, cada beirado a subir a diferença; IFC válido; desfazer;
  - interface: a ferramenta Cobertura só com tipos de cobertura; o tipo trocado nas Propriedades e o editor de tipos
    aberto em Coberturas.

## 0.277.0 — 2026-10-28

**Medidas do madeiramento e tabela de madeira** (o resto da fase R2 do ArqSynth Modeler).

- Numa cobertura com madeiramento, as **Propriedades** têm **Madeiramento ▸ Medidas…**. Abre uma janela onde se
  escolhem:
  - o afastamento dos caibros;
  - a galga da telha (o afastamento das ripas);
  - o vão máximo dos caibros, que decide quantas terças há;
  - a largura e a altura de cada peça: frechais, fileira, varas de rincão e de laró, terças, caibros e ripas.

  **Aplicar** refaz o madeiramento com estas medidas. A cobertura sobe ou desce para continuar assente nele.
- As medidas ficam guardadas com a cobertura no IFC. Mudar a cobertura ou refazer o madeiramento mantém as medidas
  escolhidas.
- Nas **Tabelas** (Ctrl+T) há a tabela **Madeiramento**: uma linha por cobertura e por peça (frechais, fileira,
  varas, terças, caibros, ripas), com a secção, o número de peças, os metros lineares e o volume de madeira. Em baixo
  aparece o volume total. Exporta-se para CSV e põe-se numa folha como as outras tabelas.
- Testes:
  - IFC: as medidas guardadas e lidas de volta; com caibros a 0,60 m ficam menos caibros do que a 0,50 m; secções
    maiores fazem subir a cobertura; a tabela com as peças certas e o volume igual à soma das peças;
  - interface: a janela das medidas aplicada a partir das Propriedades e a tabela Madeiramento nas Tabelas.

## 0.276.0 — 2026-10-28

**Madeiramento da cobertura** (pedido do dono do projeto; a fase R2 do ArqSynth Modeler).

- Numa cobertura inclinada (uma, duas ou quatro águas, ou por blocos), as **Propriedades** têm **Madeiramento ▸ Fazer
  madeiramento**. Faz, a partir das águas e das arestas da cobertura, com as medidas do addon:
  - **frechais** de 8 × 16 cm deitados no topo das paredes por baixo das águas (no addon ficavam na ponta do beirado;
    aqui assentam nas paredes, como em obra);
  - a **fileira** nas cumeeiras e as **varas de rincão** e **de laró** nos rincões e larós, de 8 × 16 cm, a prumo;
  - **terças** de 8 × 16 cm, para nenhum caibro vencer mais de 1,50 m;
  - **caibros** de 5 × 6 cm a 0,50 m, pela pendente, até à ponta do beirado;
  - **ripas** de 5 × 1,5 cm à galga da telha (0,35 m).
- Cada peça é cortada pelo contorno da sua água: junto a um rincão ou a um laró, os caibros e as ripas acabam em
  bisel.
- A cobertura **sobe para assentar no madeiramento**, e o madeiramento assenta nas paredes: os caibros pousam na
  aresta de dentro dos frechais. **Tirar** devolve a cobertura às paredes.
- Mudar a cobertura (inclinação, beirado, blocos…) refaz o madeiramento por baixo dela. Apagar a cobertura leva o
  madeiramento com ela.
- As Propriedades da cobertura dizem quantas peças há de cada tipo, o comprimento e o volume de madeira.
- No IFC: um IfcElementAssembly «Madeiramento» que junta as peças IfcMember, todas de madeira:
  - os frechais são PLATE;
  - os caibros e as varas de rincão e de laró são RAFTER;
  - as terças são PURLIN;
  - a fileira e as ripas são USERDEFINED, porque o IFC4 não tem um tipo próprio para elas.

  Cada peça leva o seu comprimento e volume (Qto_MemberBaseQuantities).
- As peças lineares aparecem na cor do seu material (a madeira) e têm nome em português no navegador do projeto.
- Testes:
  - núcleo: as peças de uma cobertura de quatro águas (caibros a ≤ 0,50 m, ripas à galga, duas terças por água,
    quatro rincões, a fileira à altura dos caibros) e os larós de um T;
  - IFC: o conjunto e as peças com os seus tipos, de madeira e fechadas; um frechal em cada parede; a cobertura que
    sobe a medida certa; tornada mais inclinada, com o madeiramento refeito; tirado, com a cobertura de volta nas
    paredes; a cobertura apagada levando o madeiramento; desfazer; IFC válido;
  - interface: o botão nas Propriedades, as peças listadas, a vista de dentro da casa e «Tirar».

## 0.275.0 — 2026-10-28

**Coberturas assentes nas paredes** (decisão: a face de dentro, como o «Rafter» do Revit).

- Uma cobertura desenhada sobre paredes passa a assentar nelas: a face de baixo encosta à aresta de dentro do topo
  das paredes. Antes, o topo da cobertura passava pela aresta de fora, e por isso via-se uma linha na água por cima
  de cada parede. Agora a parede fica toda dentro da cobertura: não há linha nem folga, e não é preciso «Ligar o
  topo» para fechar.
- Fica mais alta sobre a linha das paredes: espessura / cos(inclinação) − largura da parede × tan(inclinação). Com
  uma laje de 15 cm a 30° sobre paredes de 20 cm, são mais 5,8 cm. Uma cobertura plana fica pousada em cima das
  paredes, com a face de baixo no topo delas. Usa-se a parede mais larga das que estão no contorno, para nunca
  ficar folga.
- Nas coberturas por blocos, cada água assenta pela sua própria inclinação.
- Mudar a inclinação ou a forma nas Propriedades mantém a cobertura assente, como no Revit, que guarda a base: o
  topo sobre a linha das paredes acompanha. A «Cota do topo sobre as paredes» escrita à mão continua a mandar.
- Sem paredes por baixo, fica como antes: a 2,80 m acima do piso.
- As coberturas já desenhadas não mudam ao abrir o ficheiro.
- Testes:
  - IFC: a cobertura de quatro águas com a face de baixo a 2,80 m na aresta de dentro das paredes, e as cumeeiras e
    os beirados à nova altura; tornada plana, pousada nas paredes (2,80–2,95 m); a abóbada e a borboleta; as
    paredes e o pilar ligados ao topo, e a cobertura mais inclinada que continua assente; os blocos com o assento
    em cada água;
  - interface: as coberturas pelas paredes, em L, oblíqua, por extrusão e por blocos, às novas alturas.

## 0.274.0 — 2026-10-28

**Os dados IFC pelo MCP, com poucos tokens.**

- **summary** com missing=true diz, numa linha por classe, que dados IFC ainda faltam e em quantos elementos. Por
  exemplo: «missing in IfcWall of 4 (Pset_WallCommon): FireRating 4, AcousticRating 4…».
- **query** com uma classe de tipo (IfcWallType, IfcDoorType…) lista os tipos do projeto, com quantos elementos tem
  cada um e os campos pedidos (por exemplo, FireRating).
- **edit** num tipo dá-lhe um dado IFC que passa a valer para todos os elementos desse tipo, como no editor de tipos
  da 0.271. Assim, «dá EI 60 ao tipo de parede de 20 cm» é uma só chamada, em vez de uma por parede.
- **get** num tipo mostra quantos elementos são dele e os seus dados.
- O guia MCP.md explica como pedir os dados em falta e preenchê-los pelos tipos.
- Testes: uma casa feita pelo MCP; o resumo com a resistência ao fogo em falta nas quatro paredes; o tipo em
  tabela; o tipo preenchido numa chamada, que vale para as quatro paredes e deixa de faltar no resumo; o tipo
  consultado.

## 0.273.0 — 2026-10-26

**Dados IFC em falta, antes de entregar** (passo 5 dos dados IFC).

- Botão novo no separador **Colaborar**: **Dados IFC em falta…**. Mostra, para cada classe de elemento do modelo (com
  o seu conjunto comum do IFC4), cada propriedade e quantos elementos ainda não lhe dão valor — nem eles nem o seu
  tipo. As propriedades com mais elementos em falta aparecem primeiro.
- Um duplo clique numa propriedade (ou **Selecionar os que faltam**) seleciona esses elementos na vista. Assim
  preenchem-se de uma vez nas Propriedades (com vários selecionados) ou no tipo.
- **Preencher o que o programa sabe** escreve em todos os elementos o que o programa sabe deles: a referência (o
  tipo), se é exterior ou interior e o U. Serve para modelos feitos antes desta versão ou noutro programa. É um só
  passo de desfazer.
- Testes:
  - IFC: a casa de exemplo, feita antes da 0.266 — paredes sem referência, preenchidas de uma vez (com exterior ou
    interior), e desfeito; duas paredes sem resistência ao fogo, que deixam de estar em falta quando o tipo a tem;
  - interface: a lista com as paredes, o preenchimento, e a linha da resistência ao fogo que seleciona as duas
    paredes.

## 0.272.0 — 2026-10-26

**Transmissão térmica U calculada** (passo 4 dos dados IFC).

- Paredes, coberturas e lajes feitas de camadas passam a ter a **Transmissão térmica U** (ThermalTransmittance do
  IFC) calculada sozinha. Usa a regra da EN ISO 6946 para camadas planas: U = 1 / (Rsi + Σ espessura / λ + Rse).
- As resistências superficiais são as convencionais da norma (quadro 7). Por dentro, Rsi = 0,13 m²·K/W nas paredes
  (fluxo horizontal), 0,10 nas coberturas (para cima) e 0,17 nas lajes (para baixo). Por fora, Rse = 0,04. Estes
  valores confirmaram-se em fontes secundárias; o texto da norma não foi consultado.
- O U só aparece quando todos os materiais das camadas têm a **condutividade térmica λ** preenchida (Gerenciar ▸
  Materiais). O catálogo não traz λ, porque depende de cada produto (o mesmo bloco cerâmico vai de valores muito
  diferentes conforme o fabricante), e o programa não inventa esses valores. Ao dar ou mudar a λ de um material, o U
  de todos os elementos feitos dele refaz-se. Mudar as camadas de um tipo também o refaz.
- Como os outros valores do programa, aparece a azul, e um U escrito à mão (por exemplo, o de um ensaio) fica.
- Câmaras de ar e pontes térmicas não entram: é o U das camadas, como a norma o dá para elementos homogéneos.
- Testes (IFC): uma parede de alvenaria sem λ (sem U), com λ só no reboco (ainda sem U) e com λ no bloco
  (U = 1/(0,13 + 2 × 0,02/0,80 + 0,16/0,35 + 0,04)); uma laje e uma cobertura de betão, uma para baixo e a outra para
  cima; um U escrito à mão que fica; IFC válido.

## 0.271.0 — 2026-10-26

**Dados IFC do tipo** (passo 3 dos dados IFC).

- O **editor de tipos** tem um grupo novo, **Dados IFC do tipo**, com o conjunto comum do IFC4 da classe: para
  paredes, Pset_WallCommon; para portas, Pset_DoorCommon; e assim por diante. Lá escreve-se o que vale para todos os
  elementos desse tipo (resistência ao fogo, isolamento acústico, combustível, estrutural…), e o botão **Aplicar**
  grava-o, com o resto do tipo, num passo de desfazer.
- Os valores ficam no próprio tipo IFC (IfcWallType, IfcDoorType…). Os elementos herdam-nos, como manda o IFC, e nas
  **Propriedades** aparecem a cinzento, com a dica «Do tipo». Um elemento pode ter o seu próprio valor, escrito à
  mão, e esse fica.
- Os valores com que os elementos foram feitos (por exemplo, «Estrutural: Não» das paredes) dão lugar ao do tipo,
  mas os escritos à mão não.
- Um tipo do catálogo que o projeto ainda não usa passa a estar no projeto quando se lhe dão dados. Só mudar os
  dados não cria uma cópia do tipo.
- **Correção da 0.266:** o valor herdado do tipo não aparecia nas Propriedades, porque se procurava no sítio errado
  do IFC. Os tipos guardam os seus conjuntos em HasPropertySets.
- O editor de tipos ficou mais alto, para caberem as camadas e os dados.
- Testes:
  - IFC: duas paredes que herdam a resistência ao fogo do tipo; uma escrita à mão que fica; «Estrutural» posto no
    tipo que substitui o valor de criação; um valor apagado do tipo; um tipo do catálogo fora do projeto;
    desfazer; IFC válido;
  - interface: o editor de tipos com os dados do tipo, EI 60 aplicado, e a parede com ele, como «do tipo».

## 0.270.0 — 2026-10-26

**Ligar um assistente de IA com um clique** (passo 3 da ligação à IA).

- No separador **Gerenciar** há um botão novo, **Ligar um assistente de IA…**. Abre uma janela com três maneiras:
  - **Pôr no Claude Desktop:** acrescenta o servidor ao ficheiro de configuração do Claude Desktop. Os outros
    servidores que lá estão ficam, e o ficheiro antigo é guardado ao lado, com o nome .bak;
  - a linha para o **Claude Code**, pronta a copiar (`claude mcp add …`, na forma que a documentação do Claude Code
    dá);
  - a configuração **JSON** para qualquer outro programa.
- A configuração usa o próprio Python do programa e a pasta do programa. Não há nada para instalar.
- Guia novo, **MCP.md**: como ligar, as ferramentas e como gastar poucos tokens. Medido numa sessão típica no
  edifício médio (resumo, consulta, uma casa, uma porta, os seus dados, uma mudança, gravar): cerca de 1 550 tokens
  ao todo, dos quais cerca de 700 são a lista das ferramentas.
- Testes:
  - a configuração com o Python e a pasta do programa; o servidor posto num ficheiro com outro servidor (que fica,
    e com a cópia .bak) e num ficheiro que ainda não existia; um ficheiro que não é JSON recusado; a linha do Claude
    Code;
  - interface: o botão na faixa, a janela com a linha e o JSON, e «Pôr no Claude Desktop» num ficheiro de teste.

## 0.269.0 — 2026-10-26

**Ligação da IA à janela aberta** (passo 2 da ligação à IA).

- Botão novo no separador **Gerenciar**: **Ligação à IA**. Ligado, um assistente de IA com o MCP do ArqSynth
  (`python -m arqbim.mcp`) trabalha no modelo aberto na janela, em vez de num ficheiro à parte:
  - vê-se a trabalhar;
  - cada mudança é um passo de desfazer, como as do utilizador (Ctrl+Z);
  - o rodapé diz o que a IA fez, por exemplo «IA: criou #12 "Parede 1"…».
- **Segurança:** a janela só escuta neste computador (127.0.0.1), numa porta que o sistema dá. Usa uma chave feita
  ao acaso, que só fica na pasta do utilizador (`~/.arqsynth/mcp.json`). Um pedido sem a chave é recusado.
  Desligar o botão, ou fechar o programa, fecha a porta e apaga a chave.
- O botão fica como se deixou da última vez.
- O MCP escolhe sozinho onde trabalha: na janela, se estiver aberta e ligada; num ficheiro, com `--file`; num modelo
  novo, se não houver nem uma nem outro. `--live` obriga a usar a janela e espera por ela se ainda não estiver
  aberta.
- Ferramenta nova, só com a janela: **show**. Seleciona elementos e aproxima a vista deles, para a IA mostrar ao
  utilizador do que está a falar. Na janela, a IA não abre nem começa modelos: isso fica para o utilizador.
- Testes:
  - a chave escrita, lida e apagada só pela janela que a escreveu; um MCP sem janela que o diz à IA; o show só com a
    janela;
  - na janela real: a ligação ligada, um MCP noutro processo que pede uma casa de quatro paredes e as mostra, as
    paredes no modelo e selecionadas, o rodapé, Ctrl+Z e a ligação desligada.

## 0.268.0 — 2026-10-26

**Servidor MCP para ligar a IA** (passo 1 da ligação à IA; pedido do dono do projeto: «bom MCP para poder ligar a
IA e ser mais barato no uso de token»).

- `python -m arqbim.mcp --file modelo.ifc` arranca um servidor MCP (Model Context Protocol, por stdin/stdout). Um
  assistente como o Claude pode ler e mudar o modelo IFC. Usa só a biblioteca padrão do Python: nenhuma biblioteca
  nova.
- Oito ferramentas, cada uma descrita numa linha:
  - **summary**: os pisos, os elementos por classe e os tipos usados; com types=true, as chaves dos tipos;
  - **query**: os elementos numa tabela, com filtros (classe, piso, tipo, texto do nome), os campos escolhidos
    (comprimento, altura, Exterior, resistência ao fogo, qualquer Pset_X.Propriedade…) e páginas (40 linhas de cada
    vez);
  - **get**: um elemento — classe, nome, tipo, piso, medidas, parede onde está (portas e janelas) e os seus dados
    IFC;
  - **create**: parede, paredes seguidas, laje, cobertura, porta, janela, pilar, viga, compartimento ou piso;
  - **edit**: nome, tipo, altura, qualquer dado IFC (null apaga); mover;
  - **delete**, **undo** e **file** (novo, abrir, gravar).
- **Para gastar poucos tokens:**
  - as respostas são tabelas de texto curtas, não JSON comprido;
  - cada elemento chama-se pelo seu número no ficheiro («#54»), em vez do GlobalId de 22 caracteres;
  - os números vão sem zeros a mais (2.8, 0.2);
  - as consultas vêm às páginas.

  Medido no edifício médio: a lista das ferramentas ocupa cerca de 650 tokens, o resumo do modelo 90, vinte paredes
  numa tabela 280 e um elemento 40.
- As mudanças passam pelos mesmos comandos da janela. Por isso cada uma é um passo de desfazer, as paredes ligam-se
  nos cantos, o IFC fica válido e os dados IFC preenchem-se sozinhos.
- Testes:
  - o protocolo: acordo de versão, lista de ferramentas, erros, notificações e tamanho da lista;
  - as ferramentas: uma casa feita de uma vez, consultada em tabela com o Exterior, uma porta, os seus dados IFC,
    uma resistência ao fogo, um pilar movido, desfazer, gravar e abrir, e um número errado;
  - uma sessão real por stdin/stdout, num processo à parte.

## 0.267.0 — 2026-10-26

**Exterior ou interior calculado** (passo 2 dos dados IFC).

- A propriedade **Exterior** (IsExternal do IFC) já não fica sempre «Não». O programa calcula-a sozinho:
  - **paredes** (retas, curvas e de vidro): exteriores quando, em algum troço, um dos lados não está dentro de um
    compartimento fechado pelas paredes e pilares do piso. As divisórias ficam interiores, e um muro de jardim
    sozinho fica exterior;
  - **portas e janelas**: as da sua parede.
- Acompanha o desenho: fechar a casa, juntar uma divisória ou tirar uma parede faz o cálculo de novo, no mesmo
  passo de desfazer. Como antes, o que se escreve à mão fica, e apagá-lo devolve o valor calculado.
- Para não pesar, só se refaz o cálculo do piso quando uma parede ou um pilar muda em planta. Mudar só a altura,
  o perfil em alçado ou ligar o topo não o refaz. Medido no edifício médio: regenerar uma parede 19 ms (meta
  50 ms); mudar a altura de uma parede de um grupo com 180 cópias 1,2 s (era 1,1 s).
- Testes:
  - IFC: uma casa aberta, depois fechada, com uma divisória, portas na fachada e na divisória, um muro de jardim,
    um valor escrito à mão que fica e que, apagado, volta ao calculado, e uma parede tirada que abre o
    compartimento; IFC válido;
  - interface: «Exterior» com Sim na fachada e na porta e Não na divisória.

## 0.266.0 — 2026-10-26

**Cada elemento com os seus dados IFC** (pedido do dono do projeto: «ao desenhar, cada elemento devia trazer uma
categoria de dados de IFC e parâmetros correspondentes»).

- Nas **Propriedades**, cada elemento mostra o conjunto comum do IFC4 da sua classe, com todas as propriedades,
  preenchidas ou não: Pset_WallCommon numa parede, Pset_DoorCommon numa porta, Pset_RoofCommon numa cobertura, e
  assim por diante. Os nomes vêm das tabelas da buildingSMART que acompanham o IfcOpenShell; não se inventa nenhum.
- Cada propriedade aparece em português (o nome IFC fica na dica) e preenche-se ali mesmo, sem abrir janelas:
  - sim / não / «—» nas que são de sim ou não;
  - uma lista com os valores do IFC nas que os têm;
  - texto, número ou medida nas outras.
- Um campo vazio («—») não vai para o IFC. Assim o ficheiro só leva o que tem valor, e o conjunto completo fica
  sempre à vista para preencher.
- O que o programa sabe preenche-se sozinho e aparece a azul. Para já é a **Referência**, que é o nome do tipo,
  como no Revit, e muda quando se muda o tipo. O que se escreve à mão fica do utilizador: o programa não volta a
  mudá-lo. Apagar esse valor devolve o automático.
- As tabelas do IFC4 trazem um erro no «LoadBearing» das coberturas, escadas e rampas: o nome e o tipo estão
  trocados de sítio. O programa lê-o como «Estrutural (resistente)», sim ou não, como nas outras classes. O mesmo
  vale para o «+ Propriedade…».
- Testes:
  - IFC: uma parede com a Referência do tipo e o conjunto completo; a resistência ao fogo escrita à mão; a
    Referência à mão que fica depois de mudar o tipo e que, apagada, volta ao novo tipo; uma porta com a Referência
    do seu tipo; o LoadBearing das coberturas, escadas e rampas; IFC válido; desfazer;
  - interface: o grupo «Dados IFC — Pset_WallCommon» numa parede, e «EI 60» escrito na resistência ao fogo.

## 0.265.0 — 2026-10-26

**Arestas e medições das coberturas por blocos** (passo 4 dos telhados por blocos), como o modelo de águas do
ArqSynth Modeler.

- Cada aresta de uma cobertura por blocos é classificada a partir dos seus planos:
  - **beirado**: uma aresta de nível, no pé de uma água;
  - **cumeeira**: duas águas que se encontram por cima, de nível;
  - **rincão**: duas águas que se encontram por cima, inclinado;
  - **laró**: duas águas que se encontram por baixo;
  - **empena**: o bordo inclinado de uma água sozinha;
  - **remate no alto**: uma aresta de nível no alto de uma água, por exemplo o lado alto de uma água só, ou um
    alpendre que encosta por baixo de um beirado.
- Os comprimentos são os verdadeiros, ao longo da inclinação. Aparecem:
  - nas **Propriedades** da cobertura: beirados, cumeeiras, rincões, larós, empenas e remates, só os que existem;
  - numa tabela nova, **Coberturas** (Ctrl+T), com a área inclinada, a área em planta, os comprimentos de cada tipo
    de aresta e o volume (a espessura vezes a área inclinada, exato mesmo quando as águas se cruzam), e com os
    totais em baixo;
  - no IFC, numa lista de quantidades do programa (ArqSynth_ArestasCobertura), para outros programas lerem.
- As coberturas simples também passam a aparecer na tabela **Coberturas** (antes ficavam em «Outros elementos»),
  com as suas áreas.
- Testes:
  - núcleo: quatro águas (32 m de beirados, cumeeira de 4 m, quatro rincões), duas águas, uma água (beirado, remate
    e duas empenas), um T com um laró de cada lado;
  - IFC: os comprimentos na lista de quantidades, nas Propriedades e na tabela, com as áreas; os larós de um
    segundo bloco;
  - interface: as arestas nas Propriedades e a tabela Coberturas com uma linha.

## 0.264.0 — 2026-10-26

**Pegas dos blocos da cobertura** (passo 3 dos telhados por blocos), como as alças do ArqSynth Modeler.

- Com a ferramenta **Selecionar**, uma cobertura por blocos selecionada mostra em cada bloco:
  - um quadrado no meio de cada lado, por cima do bloco;
  - um losango no meio do bloco.
- Arrastar o quadrado de um lado leva esse lado para fora ou para dentro, e o lado oposto fica onde estava. A
  inclinação não muda. Os snaps e os alinhamentos funcionam: largado em cima de uma parede, o lado encosta à face
  de fora dela, como quando se desenha o bloco.
- Arrastar o losango move o bloco inteiro.
- Como nas outras pegas, também se pode clicar na pega e depois clicar onde fica, ou escrever a distância e
  carregar em Enter. Esc deixa tudo como estava. Enquanto se mexe, vê-se o retângulo novo e a cota temporária.
- Cada mudança é um passo de desfazer. Um bloco não fica com menos de 20 cm.
- Testes:
  - núcleo: o lado de um bloco rodado; um lado esticado e encolhido, com o oposto parado;
  - IFC: encostar à parede só o lado que se mexeu;
  - interface: as pegas de dois blocos; o lado da parte larga arrastado até à parede de este (vai até 10,10 m e o
    lado oeste fica); a ala movida 1 m, escrito; desfazer.

## 0.263.0 — 2026-10-26

**Editor de blocos da cobertura** (passo 2 dos telhados por blocos).

- Numa cobertura por blocos, as **Propriedades** têm o botão **Editar blocos…**. Abre uma janela com:
  - a lista dos blocos;
  - a planta dos blocos, com as águas da cobertura sombreadas e o bloco escolhido a azul;
  - os campos do bloco escolhido.
- Para cada bloco, mudam-se:
  - a forma (quatro águas, duas águas, uma água, plana…);
  - o centro, a rotação, a largura, a profundidade e o avanço do beirado.
- Para cada lado do bloco (N, E, S, O), mudam-se três coisas:
  - se é água ou empena;
  - a inclinação dessa água;
  - a cota do beirado, ou seja, a cota do topo sobre a linha das paredes.
  Assim fazem-se, por exemplo, uma ala com três águas ou um lado mais inclinado. Quando as águas não dão uma das
  formas, a forma passa a «Personalizada (lado a lado)».
- Na planta da janela:
  - um clique escolhe um bloco; outro clique no mesmo sítio escolhe o que está por baixo;
  - as letras dos lados do bloco escolhido trocam entre água e empena com um clique;
  - as setas mostram para onde cai cada água.
- **Duplicar** faz uma cópia do bloco, um metro ao lado; **Apagar** tira-o (fica sempre pelo menos um).
- **Aplicar** refaz a cobertura num só passo, que Ctrl+Z desfaz. As coordenadas são as da planta, mesmo que a
  cobertura tenha sido rodada.
- Um bloco tem de ter pelo menos 20 cm de cada lado. Se não tiver, a janela diz qual é o bloco e não aplica.
- Testes:
  - IFC: os blocos lidos na planta como foram dados; a cobertura rodada 90° e os blocos rodados com ela; uma água
    nova no lado norte da ala, dada na planta, refeita e desfeita;
  - interface: o editor aberto pelas Propriedades, a ala escolhida com um clique na planta, a água norte com um
    clique na letra e a 45°, um bloco duplicado e apagado, aplicado e desfeito.

## 0.262.0 — 2026-10-26

**Coberturas por blocos** (pedido do dono do projeto: telhados de formas complexas, como no ArqSynth Modeler).

- A ferramenta **Cobertura** tem um contorno novo, **Por blocos**. Cada bloco é um retângulo, desenhado por dois
  cantos, com a sua forma, inclinação e beirado. As formas são:
  - quatro águas;
  - duas águas;
  - duas águas com a cumeeira no lado menor;
  - uma água;
  - plana.
- Os blocos desenhados uns a seguir aos outros juntam-se na mesma cobertura. Onde se cruzam fica sempre o mais
  alto, e os larós e os rincões aparecem sozinhos. Assim fazem-se telhados em L, em T, em U ou com alpendres mais
  baixos, que uma só forma não dava.
- Com uma cobertura por blocos selecionada, os blocos novos juntam-se a ela. **Esc** sem nenhum canto começado faz
  com que o bloco seguinte comece outra cobertura.
- Um bloco desenhado por cima da casa encosta à face exterior das paredes que estão debaixo dos seus lados, mesmo
  que o clique se prenda ao eixo ou à face de dentro. Assim nenhuma parede sai pelo beirado. Um alpendre encostado
  às paredes, por fora, fica como foi desenhado.
- O beirado de um bloco mais alto passa por cima de um bloco mais baixo, e o alpendre continua por baixo dele.
  Onde dois beirados se sobrepõem fora das paredes, fica só o mais alto.
- Nas **Propriedades**, a **Forma** diz «Por blocos» e quantos são. A inclinação e o beirado mudam todos os blocos
  de uma vez; a forma muda-se bloco a bloco (o editor de blocos vem a seguir).
- No IFC é um IfcRoof: com a forma do bloco, se for só um, ou FREEFORM, se forem vários. Os blocos ficam guardados
  nos parâmetros da cobertura. Funcionam também:
  - espelhar;
  - ligar o topo das paredes à cobertura;
  - gravar e voltar a abrir.
- O telhado simples (pelas paredes, retângulo, polígono, a partir de uma laje) fica como estava.
- Testes:
  - núcleo: um bloco de quatro águas com as suas quatro águas e as áreas certas; dois blocos em L com o mais alto em
    cada ponto, sem buracos nem sobreposições; o beirado de um bloco alto por cima de um baixo; dois beirados
    sobrepostos num L alinhado; texto, espelho e formas;
  - IFC: a cobertura sobre as paredes, o segundo bloco, a parede ligada, a inclinação de todos os blocos, espelhar,
    gravar e abrir, IFC válido, desfazer; um bloco desenhado no eixo das paredes alargado até às faces de fora;
  - interface: uma casa em L com dois blocos clicados (uma só cobertura, FREEFORM) e um alpendre, vista de frente e
    de trás.

## 0.261.0 — 2026-10-26

**Guardas de escada contínuos** (passo 4 dos guardas profissionais).

- **Guarda** com **Por: Nos lados de uma escada** dava dois guardas por lanço, soltos, e nada no patamar. Agora faz
  **um guarda de cada lado, de ponta a ponta**:
  - nos lanços, segue a linha dos focinhos (0,90 m acima, ou a altura escolhida);
  - no patamar, fica de nível;
  - **do lado de fora,** dá a volta às arestas do patamar;
  - **do lado de dentro,** numa escada em U ou em V, dá a volta ao vão um degrau depois do último espelho; numa em
    L, faz o canto.
- Os prumos ficam sempre a prumo, mesmo nos lanços, e o enchimento (barras, cabos, vidro…) acompanha a inclinação.
- Funciona com qualquer tipo de guarda (0.258), por exemplo barras verticais ou cabos com corrimão de madeira. A
  escada em caracol continua com o guarda pela aresta de fora.
- Testes:
  - núcleo: escadas em L, em U e em V, para a esquerda e para a direita, com dois caminhos que vão do primeiro
    focinho ao piso de cima, nunca a descer e de nível no patamar; o de dentro da U a dar a volta ao vão;
  - IFC: a escada em L com dois guardas, de 0,175 m a 3,70 m;
  - interface: uma escada em L com barras e uma em U com cabos, vistas em 3D.
## 0.260.0 — 2026-10-26

**O editor de tipos de guarda** (passo 3 dos guardas profissionais).

- Novo botão **Tipos de guarda…** no separador **Arquitetura**, ao lado de **Guarda**. Abre o editor de tipos,
  como as Propriedades de Tipo do Revit:
  - **à esquerda:** os tipos do programa e os do projeto (marcados com ★), com **Duplicar** e **Apagar**;
  - **à direita:** o nome e todas as partes do tipo, por grupos:
    - **Geral:** a altura habitual;
    - **Corrimão de topo:** forma, largura ou Ø, altura e material;
    - **Prumos:** forma, medidas, afastamento máximo, chapa de base com as suas medidas, e material;
    - **Enchimento:** o tipo, a forma e as medidas das barras, a folga máxima (ou o passo, ou a malha), o número
      de travessas ou cabos, a espessura do vidro ou da chapa, e o material;
    - **Travessa inferior:** com ou sem, e a altura ao chão;
    - **Corrimão de apoio:** com ou sem, o lado, a forma, o Ø, a altura, o afastamento e o material;
    - **Perfil de base** do vidro encastrado;
  - os campos que não servem ao enchimento escolhido ficam apagados;
  - **uma amostra de 2,40 m** do guarda, vista de frente nas cores dos materiais, desenhada à medida que se muda;
  - uma medida errada, ou fora do que se pode fazer, aparece a vermelho e não deixa aplicar.
- **Aplicar** guarda o tipo no projeto (um passo de desfazer) e refaz todos os guardas desse tipo. Um tipo do
  programa mudado passa a ser do projeto, com o mesmo nome na lista. Um duplicado é um tipo novo do projeto, que
  aparece logo na ferramenta **Guarda** e nas Propriedades.
- **Apagar** só apaga tipos do projeto que nenhum guarda usa.
- Também se chega ao editor:
  - pelas **Propriedades** de um guarda: **Editar tipo…** abre-o no tipo desse guarda;
  - pela roda dentada da barra de parâmetros, com a ferramenta **Guarda**: abre-o no tipo escolhido.
- Testes:
  - IFC:
    - um tipo próprio guardado sem guardas, listado e usado;
    - não se apaga enquanto está em uso, e os do programa nunca;
    - apagado (com a sua IfcRailingType) e desfeito;
  - interface:
    - o botão na faixa;
    - os cabos duplicados, com cabos a 12 cm, prumos redondos e outro nome, e a amostra refeita;
    - o tipo aplicado e um guarda desenhado com ele;
    - as barras verticais mudadas para redondas refazem o seu guarda;
    - **Editar tipo…** abre o editor no tipo do guarda.
## 0.259.0 — 2026-10-26

**Os guardas com as cores dos seus materiais no 3D** (passo 2 dos guardas profissionais).

- Cada peça de um guarda aparece com a cor do seu material:
  - o corrimão de madeira castanho;
  - os prumos e os cabos em aço inoxidável claros;
  - o aço lacado preto, preto;
  - o vidro azulado;
  - o alumínio do perfil de base.
- Ao selecionar, o guarda inteiro fica na cor da seleção; ao largar, voltam as cores de cada peça.
- As regras gráficas (cores por fase ou por propriedade) continuam a mandar sobre estas cores.
- As cores vêm dos estilos que cada peça já leva no IFC (0.258) e ficam guardadas na cache das formas: um projeto
  reaberto mostra-as logo.
- Só os guardas usam, por agora, as cores por peça; os outros elementos continuam com a cor da sua classe.
- O vidro aparece opaco; a transparência fica para depois.
- Testes:
  - IFC: o guarda de cabos tem a cor da madeira e a do inox, uma parede não tem cores próprias; gravado e reaberto
    (também a partir da cache), as cores ficam;
  - desenho: um elemento de duas cores, selecionado e largado, volta às suas cores sem mexer no vizinho, e uma peça
    acrescentada depois também;
  - interface: os tipos vistos de perto com as suas cores.
## 0.258.0 — 2026-10-26

**Tipos de guarda-corpo, como no Revit** (pedido do dono do projeto: «quero uma ferramenta poderosa onde podemos
criar tipos variados de guarda-corpo»; primeiro passo).

- O guarda deixa de ter três estilos fixos e passa a ser de um **tipo**. O tipo diz de que é feito o guarda:
  - **corrimão de topo:** retangular, redondo ou nenhum, com a largura, a altura e o material;
  - **prumos:** quadrados, redondos, chatos ou nenhum, a medida, o afastamento máximo e uma chapa de base (quadrada
    ou redonda). Há sempre prumos no princípio, no fim e nos cantos;
  - **enchimento entre prumos:**
    - barras verticais, com folgas iguais e nunca maiores do que a folga do tipo;
    - travessas horizontais;
    - cabos de aço, que passam pelos prumos;
    - vidro preso por grampos;
    - vidro encastrado num perfil de base, sem prumos, em painéis com junta;
    - chapa cheia;
    - malha com caixilho;
    - barras em ziguezague;
    - nenhum;
  - **travessa inferior,** à altura que se quiser do chão;
  - **corrimão de apoio** ao lado, em suportes, à esquerda, à direita ou dos dois lados;
  - o **material** de cada parte (dois novos no catálogo: aço inoxidável e aço lacado preto).
- **Dez tipos já feitos,** parecidos com as imagens enviadas:
  - barras verticais;
  - barras redondas com corrimão redondo;
  - travessas horizontais;
  - cabos de aço (com corrimão de madeira);
  - vidro com grampos;
  - vidro encastrado em perfil;
  - chapa cheia;
  - malha com corrimão de madeira;
  - barras em ziguezague;
  - corrimão de parede.
- A ferramenta **Guarda** (separador **Arquitetura**) escolhe o **Tipo** na barra de parâmetros; a altura passa a ser
  a do tipo, e cada guarda pode ter a sua. Nas **Propriedades**, **Tipo de guarda** muda o tipo de um guarda já feito.
- **No IFC:**
  - cada tipo é uma IfcRailingType (GUARDRAIL; o corrimão de parede, HANDRAIL), com as suas medidas em
    ArqSynth_Guarda e um conjunto dos seus materiais (Corrimão, Prumos, Enchimento, Corrimão de apoio);
  - cada peça do corpo leva o estilo do seu material;
  - os guardas feitos antes ficam com o tipo que corresponde ao seu estilo antigo.
- Um tipo mudado no projeto refaz todos os guardas desse tipo (o editor de tipos vem a seguir).
- Testes:
  - núcleo:
    - as peças de cada enchimento: os prumos, a folga entre barras, os cabos pelos prumos, os grampos, o vidro
      encastrado sem prumos, o ziguezague, o corrimão de apoio e os seus suportes, e um caminho fechado sem prumos
      repetidos;
    - os dez tipos lidos de volta do IFC tal como são;
  - IFC: um guarda de cada tipo, com o tipo, os materiais e os estilos; um tipo para dois guardas; a altura de cada
    um; um tipo mudado refaz os seus guardas; um guarda antigo lido pelo estilo; IFC válido;
  - interface: os tipos na ferramenta e nas Propriedades, e um guarda de cada tipo visto de perto.
## 0.257.0 — 2026-10-26

**Escadas com geometria limpa: patamar e lanços numa peça, sem linhas a mais** (pedido do dono do projeto: «quero
geometria mais limpa, sem essas linhas do degrau no patamar»).

- Até aqui, cada lanço e cada patamar eram sólidos à parte, e a vista desenhava as arestas de todos:
  - o fim do lanço ficava por cima do patamar, com uma linha atravessada no meio dele;
  - a frente do patamar tinha uma faixa, onde o último espelho e o patamar se sobrepunham;
  - havia juntas onde os lanços tocavam no patamar.
- Agora:
  - **o patamar é feito com os lanços.** O lanço que chega ao patamar leva-o consigo até ao bordo do outro lado, e
    a face de baixo dobra onde encontra a do patamar. Na escada em U e na em V, o segundo lanço leva a sua metade do
    patamar; na em U, a folga entre os dois lanços é uma placa à parte;
  - **a vista e os desenhos mostram a escada como uma superfície só.** As faces que ficam no mesmo plano juntam-se,
    as que se encostam desaparecem, e só se desenham as arestas verdadeiras: os degraus, o contorno do patamar, a
    dobra por baixo;
  - **o volume** passa a ser o da escada, sem partes contadas duas vezes.
- No IFC continua a ser uma IfcStair com o seu corpo (um sólido extrudido por lanço, já com o patamar, e a placa da
  folga do U), válido.
- Como na 0.256, as escadas já feitas ficam limpas quando são alteradas nas Propriedades.
- Testes:
  - núcleo: um lanço com o patamar à frente e outro com o patamar atrás. Duas caixas encostadas ficam uma caixa de
    12 arestas, fechada, com o volume das duas;
  - IFC: numa escada em L e numa em U, nenhuma aresta dentro do topo do patamar nem ao longo da sua frente, o volume
    da L a soma dos dois lanços, e o IFC válido;
  - interface: o patamar visto do primeiro lanço, como na imagem do pedido.
## 0.256.0 — 2026-10-26

**As escadas com a laje que suporta os degraus** (pedido do dono do projeto: «as escadas estão sem laje, há
somente degraus»).

- A espessura da laje da escada (a do tipo de laje escolhido, por exemplo 15 cm) era medida a partir da linha dos
  focinhos dos degraus. Com espelhos de 17,5 cm, a face de baixo passava exatamente pelos cantos interiores dos
  degraus: ficavam só os degraus, sem laje.
- Agora a laje é medida como manda o IFC (WaistThickness): na perpendicular à inclinação, a partir do **canto
  interior** de cada degrau (o encontro do espelho com o cobertor).
  - Uma laje de 15 cm tem 15 cm por baixo de todos os degraus.
  - O pé do 1.º lanço assenta no chão.
  - Um lanço que sai de um patamar começa na face de baixo do patamar.
  - Um lanço que chega a um patamar continua até a sua face de baixo encontrar a do patamar. Lanços e patamar
    ficam uma laje só, sem degraus por baixo.
  - O último lanço apoia-se no piso de cima como antes (10 cm para lá do último espelho, cortado na vertical).
- Vale para as escadas retas, em L, em U e em V; a caracol mantém os degraus soltos à volta da coluna. As escadas
  já feitas ficam corretas quando são alteradas (qualquer mudança nas Propriedades as refaz).
- Testes:
  - núcleo: 15 cm de laje sob cada canto interior; o pé no chão; o lanço que sai do patamar a partir da sua face
    de baixo; o que chega ao patamar a encontrar a face de baixo dele;
  - IFC: as escadas reta, em L e em U com as medidas de sempre, e o IFC válido;
  - interface: o volume da escada reta (degraus mais laje) e as vistas de lado e por baixo.
## 0.255.0 — 2026-10-26

**Desempenho medido no fim dos restos das fases, e o ficheiro lateral lido uma vez ao abrir** (Transversal do
plano: «desempenho medido a cada fase»).

- **Medição** (benchmark, no WSL com a placa por OpenGL, como desde a 0.225):
  - **edifício médio** (8,3 MB, 3241 elementos): nada piorou desde a 0.225.
    - Navegação: 85 imagens por segundo.
    - Regenerar uma parede: 18 ms.
    - Selecionar: 1,4 ms.
    - Inferências: 3,7 ms.
    - Abrir até à 1.ª imagem: 0,84 s. Reabrir: 0,73 s.
  - **edifício grande** (45 MB, 18 001 elementos, 968 mil triângulos):
    - Abrir até à 1.ª imagem: 2,6 s. Pronto a editar: 15 s.
    - Reabrir: 2,6 s. Pronto a editar: 3,5 s.
    - Navegação: 55 imagens por segundo (a meta é 60).
    - Regenerar: 28 ms. Selecionar: 1,5 ms. Inferências: 11 ms.
  - Nas versões até à 0.42, reabrir o grande demorava 1,6 s, mas no Windows com Vulkan. Desde a 0.61 o programa
    corre no WSL (OpenGL por D3D12, ficheiros em /mnt/c), e o «pronto a editar» é o mesmo (3,4 s). A diferença
    vem da plataforma, não do código.
  - A estimativa para 500 MB continua acima da meta: pela proporção do edifício grande, ~29 s, contra < 20 s.
- **Ao abrir um projeto**, o ficheiro lateral (`.arqsynthbim`: esboços, cortes, folhas, cotas, vistas, grelha…)
  era aberto e lido quase vinte vezes, uma por cada parte. Agora:
  - lê-se uma vez para os esboços (com o IFC) e outra para todas as outras partes;
  - no edifício grande, mostrar o projeto passou de 0,35 s para 0,26 s;
  - num projeto com muitos esboços, a diferença é maior.
- Por dentro: os lotes de desenho escrevem as peças diretamente nos seus buffers, sem montar antes uma cópia do
  lote inteiro. O tempo é o mesmo, porque o que pesa na 1.ª imagem é o envio para a placa (OpenGL no WSL), e há
  menos memória temporária.
- Testes: um projeto gravado e aberto de novo, contando as leituras do ficheiro lateral (duas), com a legenda e a
  grelha de volta.
## 0.254.0 — 2026-10-26

**No papel, o pilar recorta a parede onde está** (como as uniões do Revit; visto ao corrigir o contorno na 0.253).

- Um pilar dentro de uma parede (num canto, a meio, a atravessá-la) aparecia por baixo da trama da parede: a
  alvenaria pintava-se por cima do betão, conforme a ordem dos elementos.
- Agora, na planta e nos cortes, o pilar **recorta a parede**:
  - a trama da parede, ou as das suas camadas, para à face do pilar;
  - o pilar mostra a sua própria trama, inteira;
  - a linha grossa continua a ser o contorno de tudo o que é cortado, por fora.
- Entre materiais diferentes lado a lado (o betão do pilar e a alvenaria da parede, uma parede de betão encostada a
  uma de tijolo) desenha-se a **linha fina** onde o material muda, como entre as camadas de uma parede. Entre
  peças do mesmo material não há linha.
- O mesmo nas folhas, no PDF, no PNG, no SVG, na impressão e no DXF.
- **Correção de um fecho súbito do programa:** ao gravar os resultados da análise no IFC (Estrutura ▸ Analisar a
  estrutura… ▸ Guardar resultados no IFC), o trabalho corre noutra linha de execução para a janela não parar. Às vezes,
  essa linha refazia o painel de Propriedades e a vista 3D, coisa que só a janela pode fazer, e o programa fechava
  (apanhado pela suíte de testes da interface).
  - Agora as mudanças feitas noutra linha de execução esperam pelo fim do trabalho e são mostradas pela janela.
  - Isto vale para todos os trabalhos longos com a janela de progresso.
- Testes:
  - IFC, quatro paredes com um pilar em cada canto:
    - as tramas cobrem o que é cortado uma só vez (a soma das áreas é a da união);
    - a das paredes não toca a dos pilares;
    - a dos pilares é a sua secção inteira;
  - interface: o canto ampliado na planta pintada como numa folha;
  - documento: uma parede feita noutra linha de execução não avisa a janela de lá; o aviso vai para a janela e
    chega com as mudanças. Sem janela, avisa como antes;
  - interface: os resultados da análise gravados no IFC duas vezes seguidas, sem fechar.
## 0.253.0 — 2026-10-26

**O contorno grosso do corte no papel, certo nos cantos e nas paredes redondas** (o «Investigar» da secção
Transversal do plano).

- A causa da falha anotada no plano («o contorno grosso das paredes falhou uma vez num canto») era o sentido dos
  contornos cortados:
  - cada contorno saía do corte num sentido ou noutro, conforme os triângulos do elemento;
  - o papel junta-os com a regra do enrolamento, e dois elementos sobrepostos em sentidos contrários anulavam-se;
  - por isso, num canto com um pilar sobre as pontas de duas paredes, a linha grossa contornava o quadrado do
    pilar em vez de passar por fora;
  - e numa **parede redonda** inteira, o anel interior ia no mesmo sentido do exterior: a linha grossa de dentro
    desaparecia e a trama enchia a sala redonda.
- Agora os contornos de cada elemento seguem todos o mesmo sentido, e os seus buracos o sentido contrário:
  - **no papel** (folhas, PDF, PNG, SVG e impressão), a linha grossa é a união de tudo o que é cortado e os buracos
    ficam abertos;
  - as tramas das camadas seguem a mesma regra;
  - **no DXF**, cada trama enche de uma vez os seus contornos menos os buracos. Já não entra na sala redonda nem
    se desenha duas vezes onde dois elementos se sobrepõem.
- Testes:
  - núcleo: contornos em sentidos misturados ficam com os de fora num sentido, os buracos no outro e uma ilha
    dentro de um buraco de novo de fora;
  - IFC:
    - a planta de uma parede redonda tem o anel exterior e o interior em sentidos contrários, com a área do anel;
    - no DXF, nenhuma linha de trama dentro da sala;
    - quatro paredes com um pilar em cada canto têm todos os contornos no mesmo sentido;
  - interface: a planta pintada como numa folha (1:50), com os cantos dos pilares dentro do contorno, a sala
    redonda fora e o anel dentro.
## 0.252.0 — 2026-10-26

**A fachada de vidro numa parede curva** (resto do passo 7 da fase 4, o último resto da fase).

- A ferramenta **Fachada de vidro** (separador **Arquitetura**), começada dentro de uma parede curva (entre as suas
  faces, no eixo ou numa face), passa a seguir o arco da parede:
  - o primeiro clique fixa o início, no arco que passa por esse ponto;
  - o rato dá a volta pela parede, sem passar das pontas dela (numa parede circular, pelo lado mais curto);
  - um segundo clique, ou o comprimento escrito ao longo do arco e Enter, acaba a fachada.
  A dica diz que a fachada segue o arco da parede.
- A fachada fica **embutida** na parede, como as retas (0.188): abre nela o seu vão, de face a face, em forma de
  setor do anel, e vai com ela.
- **Como é feita:**
  - os montantes ficam no arco, à mesma distância uns dos outros e direitos à curva;
  - as travessas e os painéis são planos entre dois montantes (cordas), como se constroem;
  - os painéis opacos, as portas e os vazios por célula (0.181) funcionam na mesma.
- **Na parede:**
  - nas **Propriedades**, as distâncias às pontas da parede contam ao longo do arco; mudá-las faz a fachada deslizar
    pela parede;
  - a parede com outro raio ou outra espessura, com uma ponta mexida, espelhada, movida ou copiada: a fachada vai
    com ela, à mesma distância ao longo e ao mesmo afastamento do eixo, com o seu comprimento;
  - se a fachada deixasse de caber, a mudança é recusada;
  - desligar **Embutida na parede** deixa a parede inteira; voltar a ligá-la abre o vão de novo.
- **No IFC** é a mesma IfcCurtainWall, a preencher (IfcRelFillsElement) uma IfcOpeningElement da parede. O vão é um
  setor extrudido com arcos verdadeiros.
- Testes:
  - IFC, uma parede curva de 5 m de raio (um quarto de círculo) e uma fachada de 30°:
    - embutida, com a parede menos o setor;
    - 3 montantes e os painéis em cordas;
    - a célula sob um ponto;
    - deslizada; para lá da ponta, recusada;
    - a parede com 6 m de raio: a fachada acompanha;
    - espelhada; desembutida e embutida; copiada com a parede;
    - IFC válido; tudo desfeito;
  - interface: a ferramenta clicada na parede a 30° e a 60°, a dica, o vão, o deslizar nas Propriedades e a parede
    com outro raio.
## 0.251.0 — 2026-10-26

**A cobertura com um perfil desenhado** (resto do passo 5 da fase 4).

- Além da borboleta e da abóbada (0.180), uma cobertura sobre um retângulo pode agora ter a **secção que se
  desenhar**. Os passos são:
  1. Desenhe a secção como uma face plana, à medida real, com o Retângulo, a Linha ou o Polígono do separador
     **Conceito**. Pode desenhá-la de pé, atravessada à cobertura, ou no chão (aí o X é o atravessado e o Y para
     cima). A face inclui a espessura: a parte de baixo é o teto, a de cima o telhado.
  2. Selecione a cobertura e a face (com Shift).
  3. No separador **Arquitetura**, ao lado de **Cobertura**, clique em **Perfil da cobertura**.
- A cobertura passa a ser essa secção, centrada no vão e corrida ao comprido (com o beiral nas empenas). O ponto mais
  baixo da secção fica à altura do beirado.
- **No IFC** é uma IfcRoof **FREEFORM** («cobertura de forma livre»). O corpo é a secção extrudida ao longo, e a
  secção fica guardada com a cobertura.
- **Ligar o topo** das paredes funciona como nas outras coberturas: o topo da parede segue a parte de baixo da
  secção.
- Nas **Propriedades**, a forma aparece como **Perfil desenhado**. Pode trocar-se por outra e voltar a ela sem
  desenhar de novo. A ferramenta **Cobertura** não a oferece, porque a secção vem depois.
- O programa recusa:
  - uma cobertura que não esteja sobre um retângulo;
  - uma secção com menos de 50 cm de largura, menos de 2 cm de espessura ou sem área.
- Testes:
  - núcleo:
    - a secção posta a partir do ponto mais baixo;
    - a parte de baixo e o topo em cada ponto do vão;
    - as recusas;
  - IFC, uma cobertura de 10 × 6 m com uma secção de 7 m:
    - FREEFORM;
    - o topo 1,50 m acima do beirado ao meio, a parte de baixo no beirado e o bordo com 0,20 m;
    - o volume é a área da secção vezes o comprimento;
    - trocada para duas águas e de volta;
    - recusada sobre um L;
    - IFC válido;
  - interface: o botão na faixa e a cobertura feita com a face selecionada.
- Correção: a ferramenta **Perfil** guardava o último perfil próprio escolhido. Num projeto novo, onde esse perfil
  não existe, o primeiro clique não fazia nada. Agora volta ao Rodapé.

## 0.250.0 — 2026-10-26

**A verificação EC2 e as armaduras da sapata combinada** (resto do passo 3 da fase 3, com a fase 9).

- A **Verificação EC2 e armaduras…** passa a dimensionar a sapata combinada (0.249) com as reações dos seus dois
  pilares. Os resultados são de pré-dimensionamento, como os outros:
  - **o solo:** a tensão na área efetiva (EC7, Anexo D, com a excentricidade das cargas ao longo da sapata). Se a
    tensão passar a admissível, diz para que largura a alargar;
  - **ao longo:** a sapata é tratada como uma viga sobre o solo, com a pressão linear que a resultante dos pilares dá:
    - o momento positivo junto aos pilares dá a armadura inferior;
    - o momento negativo entre eles dá a **armadura superior**, que as sapatas isoladas não têm;
  - **o esforço transverso** a uma altura útil das faces dos pilares, sem estribos (EC2 6.2.2). Entre os pilares
    conta a armadura de cima e por fora a de baixo;
  - **na transversal:** sob cada pilar, uma banda com a largura dele e mais uma altura útil de cada lado, em consola
    a partir das faces. Dá a armadura inferior transversal;
  - **o punçoamento** em cada pilar, junto à face e a 2d, como nas sapatas isoladas (EC2 6.4).
- As notas dizem os dois pilares e as suas cargas, e os momentos e o esforço transverso ao longo.
- **Pôr as armaduras no modelo** põe a malha inferior nos dois sentidos e os varões superiores ao longo, dobrados
  para baixo nas pontas. Os varões dos pilares entram na sapata, como nas isoladas.
- Nos desenhos de armaduras, o corte C–C mostra os varões de cima e os de baixo ao longo.
- Testes:
  - núcleo, numa sapata de 4,20 × 1,50 × 0,70 sob dois pilares a 3 m com 700 kN cada:
    - o momento negativo N (L/4 − s/2) = 315 kNm e o positivo q · 0,6² / 2 = 60 kNm;
    - as três armaduras, o esforço transverso e o punçoamento;
    - com cargas grandes demais, a falha diz a largura;
    - os varões de cima dobrados para baixo, sob o recobrimento;
  - IFC, num pórtico de dois pilares sobre uma sapata combinada:
    - a verificação com as notas próprias e a armadura superior;
    - os pilares a entrar na sapata;
    - os varões postos (malha inferior nos dois sentidos e superiores);
    - IFC válido.

## 0.249.0 — 2026-10-26

**A sapata combinada** (resto do passo 3 da fase 3).

- No separador **Estrutura**, ao lado de **Sapatas**, há o botão **Sapata combinada**. Selecione dois pilares (e só
  dois) e clique nele: fica uma sapata debaixo dos dois.
- Como é a sapata:
  - vai ao longo da linha entre os pilares, centrada entre eles;
  - o comprimento é a distância entre os pilares mais o comprimento do tipo de sapata isolada da ferramenta
    **Sapata** (metade para lá de cada pilar);
  - a largura e a altura são as desse tipo;
  - o topo fica à cota da base do pilar mais baixo.
- **No IFC:** é uma IfcFooting PAD_FOOTING. A norma define-a como «um elemento que transfere a carga de um só pilar
  (ou dois) ao terreno».
- Fica presa aos dois pilares. Se um deles se mover, a sapata é feita outra vez debaixo deles: mais comprida ou mais
  curta, de novo ao meio, e com o mesmo tipo.
- As sapatas que os pilares já tinham ficam onde estão. Se a combinada as substitui, apague-as.
- O **modelo analítico** reconhece os dois pilares assentes nela: um pilar está sobre uma sapata quando o seu meio
  cai dentro da planta dela (e não só quando está perto do meio da sapata). Não há avisos de «pilar sem sapata» nem
  de «sapata sozinha».
- Fica para a versão seguinte: a verificação EC2 e as armaduras da sapata combinada.
- Testes:
  - IFC:
    - a sapata sob pilares a 3 m: PAD_FOOTING, ao meio, 4,20 × 1,20 e com o topo na base;
    - presa aos dois;
    - um pilar movido 1 m: refeita com 5,20, de novo ao meio;
    - o modelo analítico com os dois apoios e sem avisos;
    - IFC válido;
    - dois passos a desfazer;
    - recusada com o mesmo pilar duas vezes;
  - interface: o botão, a sapata feita com 4,20, presa e selecionada.

## 0.248.0 — 2026-10-26

**A tabela de notas-chave do projeto** (resto do passo 2 da fase 5).

- Além da tabela de notas-chave do programa (0.194), cada projeto pode ter a sua: no separador **Anotar**, botão
  **Notas-chave do projeto…**.
- Na janela, cada linha é um código e o seu texto:
  - **Acrescentar** junta uma linha nova;
  - **Copiar uma da tabela do programa** traz um código do programa para lhe mudar o texto;
  - **Tirar** apaga a linha.
  OK grava (um passo, Ctrl+Z desfaz).
- Quando se escolhe a nota-chave de um elemento (nas Propriedades), os códigos do projeto aparecem com os do
  programa. Um código que existe nos dois aparece com o texto do projeto.
- Mudar o texto de um código na tabela do projeto muda-o também nos elementos que o têm, e nas etiquetas e na legenda
  que os mostram.
- Tirar um código da tabela não o tira dos elementos: esses ficam com o código e o texto que tinham.
- **No IFC:** a tabela fica na própria classificação «Notas-chave», como referências que nenhum elemento usa (com uma
  marca na descrição). Por isso viaja com o ficheiro.
- Testes:
  - IFC:
    - a tabela gravada e lida, e um passo para desfazer;
    - os códigos oferecidos, os do projeto com o seu texto;
    - a parede com um código do projeto, e o texto mudado na tabela;
    - outra nota-chave na parede não apaga a entrada da tabela;
    - a tabela vazia deixa a parede como estava;
    - IFC válido;
  - interface: o botão na faixa, a janela preenchida (uma linha nova e uma copiada e mudada), e a nota-chave da parede
    escolhida entre elas nas Propriedades.

## 0.247.0 — 2026-10-26

**Duas águas sobre um contorno com cantos para dentro** (resto do passo 5 da fase 4).

- Uma **cobertura de duas águas** pode agora ir sobre uma casa em L, em T ou em U (contornos com cantos para dentro e
  os lados em esquadria). Até aqui, o programa recusava e só deixava fazer quatro águas.
- Como fica:
  - cada ala leva duas águas, com a cumeeira ao comprido;
  - onde as alas se encontram, as cumeeiras cruzam-se e há larós nos cantos de dentro;
  - no fim de cada ala fica uma empena, com a cobertura à altura toda sobre a linha da parede (nas quatro águas,
    está ali o beirado);
  - os beirados e as empenas avançam o beiral escolhido.
- A espessura, as quantidades (área inclinada, área em planta) e as paredes presas à cobertura (Ligar o topo)
  funcionam como nas outras coberturas.
- Uma cobertura de uma água sobre um L, ou de duas águas sobre um contorno com lados oblíquos, continua recusada.
- Testes:
  - núcleo, no L de 6 × 5 m:
    - as águas enchem-no (24 m²);
    - cada uma com a sua altura;
    - a empena com a altura toda no fim da ala, onde as quatro águas estão no beirado;
    - o L aceita duas águas e recusa uma;
  - IFC: a cobertura de duas águas sobre um L, com 50 cm de beiral:
    - GABLE_ROOF;
    - o volume é a área inclinada do L crescido vezes a espessura;
    - as cumeeiras à altura das quatro águas;
    - a empena com a altura toda.

## 0.246.0 — 2026-10-26

**A parede que encontra uma curva a meio, em T** (resto do passo 3 da fase 4).

- Uma parede reta desenhada até ao lado de uma parede curva (não às pontas) faz agora uma **ligação em T**, como já
  fazia com as paredes retas:
  - a parede curva continua, e a reta para na face dela, a de fora ou a de dentro, conforme o lado de onde vem;
  - os dois cantos da ponta da parede reta ficam sobre a face curva. A ponta é cortada pela corda entre eles, o que
    deixa no máximo um ou dois milímetros (a flecha do arco na espessura de uma parede), sem buracos nem paredes
    sobrepostas.
- A ligação fica registada no IFC como as outras (IfcRelConnectsPathElements, a curva «ATPATH») e mantém-se:
  - se a parede curva mudar de raio ou de espessura, ou se alguma das duas se mover, a reta acompanha;
  - se deixarem de se encontrar, a ligação desfaz-se e as paredes ficam como estão.
- Também se faz ao contrário: uma parede curva desenhada contra a ponta de uma reta que já existe.
- Não se faz T com uma parede ao longo da curva, nem para lá das pontas do arco.
- Testes:
  - núcleo:
    - a ponta de fora sobre a face de 3,10 m (o eixo em √(3,1² − 0,1²)), cortada virada para o centro;
    - a de dentro sobre a face de 2,90 m;
    - ao longo do arco ou para lá da ponta: nada;
  - IFC:
    - o T ligado e registado («ATPATH»), os cantos sobre a face, sem sobreposição;
    - a curva com mais raio leva a reta;
    - uma parede de dentro para na face de dentro;
    - uma para lá da ponta não se liga;
    - IFC válido.

## 0.245.0 — 2026-10-26

**Um perfil desenhado pelo utilizador** (resto do passo 2 da fase 10).

- O **Perfil** (0.174: rodapé, sanca, friso, cimalha) pode agora correr com uma **secção desenhada por si**:
  1. Desenhe a secção como uma face plana (Retângulo, Linha ou Polígono do separador **Conceito**). Pode desenhá-la
     no chão ou de pé, num plano vertical:
     - no chão, o X é para fora da parede e o Y para cima;
     - de pé, a horizontal é para fora da parede e a vertical para cima.
  2. Selecione a face e clique em **Perfil de uma face** (separador **Arquitetura**, ao lado de **Perfil**). Dê-lhe
     um nome.
  3. O perfil fica no projeto e aparece na ferramenta **Perfil**, a seguir aos do catálogo. Corre à volta de uma sala
     ou ao longo de um caminho, com os cantos em esquadria e cortado nas portas, como os outros.
- O tamanho é o do desenho e pode mudar-se nas **Propriedades** (largura, altura), como nos outros perfis. Também se
  pode trocar entre um perfil próprio e os do catálogo.
- **No IFC:**
  - a secção fica guardada como um `IfcArbitraryClosedProfileDef` com o nome que lhe deu, para se poder reutilizar;
  - cada perfil corrido leva consigo a sua secção.
- Na **lista de corte** e no DXF de fabrico, as peças aparecem com o nome do perfil.
- O programa recusa uma seleção que não seja uma só face plana, um nome repetido e uma secção com menos de 0,5 cm ou
  mais de 60 cm.
- Testes:
  - núcleo:
    - uma secção em L desenhada ao contrário dos ponteiros do relógio, posta no quadrado unitário e no sentido certo,
      com a medida guardada;
    - a secção varrida a outro tamanho;
    - as recusas;
  - IFC:
    - a face em L, de pé, guardada como «Friso L», e um passo a desfazer;
    - um volume e um nome repetido recusados;
    - o perfil corrido com a sua secção e a altura de 6 cm, IFC válido;
    - na lista de escolha e na de corte;
    - trocado por rodapé e de volta;
  - interface:
    - o botão na faixa;
    - o perfil feito a partir da face e oferecido pela ferramenta Perfil;
    - escolhido nas Propriedades do perfil corrido.

## 0.244.0 — 2026-10-26

**Os compartimentos de larguras diferentes, arrastados** (resto do passo 1 da fase 10).

- Até aqui, os compartimentos de um móvel (0.172) tinham todos a mesma largura. Agora cada divisória pode ir para
  onde se quiser:
  - **com o rato:** selecione o móvel (ferramenta **Selecionar**). Cada divisória mostra uma pega azul, a meia
    altura, na frente do corpo. Arraste a pega ao longo do móvel, ou clique nela e depois clique onde fica, ou escreva
    quanto anda e carregue em Enter. A barra de baixo diz as larguras dos dois compartimentos;
  - **nas Propriedades:** há uma **Largura do compartimento** para cada um. Escrever a largura move a divisória da
    direita dele (a do último, a da esquerda).
- As prateleiras, o varão e as gavetas interiores acompanham o compartimento. Cada compartimento fica com pelo menos
  15 cm; mais estreito, o programa recusa.
- Mudar o número de compartimentos põe-nos outra vez com a mesma largura.
- No IFC, os lugares das divisórias ficam no parâmetro «Divisoes» do móvel.
- Testes:
  - núcleo:
    - as divisórias à mesma distância, e depois a 45 cm, com as larguras certas;
    - a divisória e as prateleiras no sítio;
    - a recusa abaixo de 15 cm;
    - outro número de compartimentos volta às larguras iguais;
    - um móvel de gavetas não tem divisórias;
  - IFC:
    - a divisória posta e lida de volta, IFC válido;
    - a recusa sem mudar nada;
    - com três compartimentos, as larguras voltam a ser iguais;
  - interface: a pega arrastada 20 cm leva a divisória a 80 cm; a largura do compartimento aparece nas Propriedades;
    Ctrl+Z desfaz.

## 0.243.0 — 2026-10-26

**As frentes noutro material e cor** (resto do passo 1 da fase 10).

- As frentes dos móveis (portas, gavetas, o painel do canto cego, as portas de correr e as do canto em L) podem ter
  outro acabamento além do corpo de melamina:
  - **lacado** branco, cinzento ou preto (MDF lacado);
  - **carvalho** ou **nogueira** (folheado).
- Onde se escolhe:
  - nas **Propriedades** de um móvel (**Acabamento das frentes**);
  - na barra das ferramentas **Móvel** e **Cozinha** (**Acabamento**). Uma cozinha sai toda com o mesmo.
- O que muda:
  - **no ecrã**, o móvel aparece na cor das frentes, que é o que se vê dele na sala. Com melamina, fica na cor de
    sempre;
  - **no IFC**, o material do móvel passa a um conjunto de constituintes: «Corpo» (aglomerado melamínico) e
    «Frentes» (o acabamento). O conjunto é partilhado pelos móveis com o mesmo acabamento, e cada frente leva a cor
    do seu material;
  - na **lista de corte**, as frentes aparecem à parte, com o material: por exemplo «Frente folheada a carvalho 18
    mm».
- Correção: a ferramenta **Móvel** guardava as frentes «Forno» ao mudar para um módulo que não é coluna, e o
  programa recusava o móvel. Agora volta a «Portas».
- Testes:
  - núcleo:
    - as frentes de carvalho com o material próprio e o corpo de placa;
    - o painel cego, as portas de correr e as portas do canto em L também;
    - a melamina continua «front»;
    - um acabamento que não existe é recusado;
  - IFC:
    - o conjunto «Corpo» + «Frentes», partilhado por dois móveis;
    - as frentes com estilo e a cor no ecrã;
    - IFC válido;
    - de volta à melamina, só a placa;
  - interface: o acabamento escolhido nas Propriedades, a cor no 3D e as frentes na lista de corte.

## 0.242.0 — 2026-10-26

**O forno numa coluna** (resto do passo 1 da fase 10).

- Uma **coluna** (móvel alto) tem umas frentes novas: **Forno (gavetas, forno, porta)**. Escolhem-se na barra da
  ferramenta **Móvel** ou nas **Propriedades** (Frentes). A coluna fica assim:
  - uma prateleira fixa debaixo do forno, com o tampo a 86 cm do chão (à altura dos olhos), e outra por cima da
    abertura de 60 cm;
  - por baixo, duas gavetas;
  - por cima, uma porta, com o puxador em baixo (fica acima da cabeça), e as prateleiras atrás dela.
- O **forno** põe-se sozinho no nicho, no mesmo passo:
  - é um eletrodoméstico («Forno em coluna», IfcElectricAppliance ELECTRICCOOKER), com a mesma potência do outro forno
    (3500 W) para os circuitos;
  - a caixa fica entre os lados da coluna e a porta à face das frentes;
  - acompanha a coluna quando ela se move;
  - sai quando a coluna deixa de ter forno ou é apagada, e Ctrl+Z traz os dois.
- O forno em coluna não aparece na lista da ferramenta **Eletrodoméstico**: é a coluna que o põe. O forno de
  antes, debaixo da bancada, continua lá.
- Testes:
  - núcleo, na coluna de 60 cm com forno:
    - as prateleiras fixas à altura certa;
    - as duas gavetas e a porta, com o puxador em baixo;
    - as prateleiras só atrás da porta;
    - as ferragens;
    - a caixa do forno entre os lados;
    - as recusas (um móvel inferior, uma coluna de 50 cm);
  - IFC:
    - o forno feito com a coluna, ligado a ela, à altura e à face certas, IFC válido;
    - desfazer leva os dois;
    - a coluna movida leva o forno;
    - com portas, o forno sai; desfeito, volta; apagada a coluna, sai também;
  - interface: a coluna com forno posta com a ferramenta Móvel, e o forno dentro.

## 0.241.0 — 2026-10-26

**As portas de correr** (resto do passo 1 da fase 10).

- Os móveis e os roupeiros têm umas frentes novas: **Portas de correr**. Escolhem-se nas **Propriedades** (Frentes)
  ou na barra da ferramenta **Móvel**:
  - correm em duas calhas: uma porta atrás, a seguinte à frente, e assim por diante;
  - onde se encontram, sobrepõem-se 3 cm;
  - são 2 a 4 portas (Portas, nas Propriedades), com pelo menos 30 cm cada;
  - há uma calha em cima e outra em baixo, num perfil de 6 cm à frente do corpo. A profundidade total e o rodapé
    contam com ele;
  - cada porta tem o puxador no lado livre: as das pontas junto à ponta, as do meio ao centro.
- Na **lista de corte**, as portas aparecem como «Porta de correr». As calhas ficam nas ferragens, como «conjuntos
  de calhas de correr», e não têm dobradiças.
- Um **roupeiro** pode agora ter até 2,70 m de largura (o comprimento de uma placa); os outros móveis continuam até
  1,50 m.
- Testes:
  - núcleo, num roupeiro de 1,80 m com duas portas:
    - a largura de cada porta;
    - uma porta em cada calha, sobrepostas 3 cm;
    - as calhas fora da lista de corte, e nenhuma dobradiça;
    - os puxadores nas pontas;
    - a profundidade e o rodapé;
  - núcleo: três portas em 2,40 m; uma porta passa a duas; portas de menos de 30 cm são recusadas;
  - IFC: um roupeiro de 2,40 m com três portas, IFC válido, as portas na lista e as calhas nas ferragens. Com portas
    de abrir, a profundidade volta à de antes. 2,80 m é recusado;
  - interface: nas Propriedades, as frentes mudam para portas de correr; a escolha de portas passa a 2 a 4, e com 3
    o roupeiro fica com três portas.

## 0.240.0 — 2026-10-26

**O canto em L e o carrossel** (resto do passo 1 da fase 10).

- A ferramenta **Cozinha** tem uma escolha nova na barra de cima: **Cantos**. Há três opções:
  - **Cegos:** o módulo de canto cego da 0.239. É o que vem escolhido;
  - **Em L:** em cada canto de dentro, um **móvel de canto em L**:
    - em baixo, de 90 × 90 cm; em cima, de 65 × 65 cm;
    - cada braço encosta a uma parede, e o troço seguinte começa depois do segundo braço;
  - **Em L com carrossel:** o mesmo, com um carrossel no móvel de baixo.
- O móvel de canto em L:
  - o corpo é feito em L, com um lado no fim de cada braço. O fundo, o tampo (ou as travessas) e as costas vão em
    duas peças cada um;
  - as prateleiras são em L;
  - tem uma porta em cada braço, que se juntam no canto de dentro. São portas articuladas: dobram uma sobre a outra,
    com duas dobradiças entre elas e duas no fim do segundo braço. O puxador fica no lado livre da primeira;
  - o rodapé corre ao longo das duas frentes.
- O **carrossel** tem dois tabuleiros de três quartos de círculo, à volta do canto de dentro. O quarto que falta fica
  do lado das portas. No IFC, cada tabuleiro é um perfil com essa forma. O carrossel conta nas ferragens («carrosséis
  de canto») e não na lista de corte, porque vem feito.
- A **bancada** cobre também o segundo braço: a peça do segundo troço começa onde acaba a do primeiro.
- Nas **Propriedades**, um móvel inferior ou superior de portas tem também **Canto em L (braço)** e o **lado do
  canto**. O carrossel escolhe-se no compartimento («Carrossel (canto em L)»). O programa recusa:
  - um carrossel fora de um canto em L;
  - braços sem lugar para uma porta de 25 cm.
- Testes:
  - núcleo, no móvel de canto em L de 90 × 90:
    - as duas portas (33,4 e 31,6 cm);
    - os tabuleiros (três quartos de círculo, nenhum ponto do lado das portas);
    - quatro dobradiças e um puxador no lado livre;
    - o carrossel fora da lista de corte;
    - virado para um canto à esquerda;
    - as recusas;
  - núcleo, na cozinha em L com cantos em L: os troços e a bancada em L, com a segunda peça a começar onde acaba a
    primeira;
  - IFC: a cozinha com carrossel, os tabuleiros como perfis próprios, IFC válido. Tirar o braço com o carrossel é
    recusado;
  - interface: a cozinha feita com a opção «Em L com carrossel», vista em 3D.

## 0.239.0 — 2026-10-26

**O módulo de canto cego** (resto do passo 1 da fase 10).

- Numa cozinha em L ou em U, o último módulo antes de um canto de dentro ficava com a porta tapada pelo primeiro
  módulo da outra parede. Agora a **Cozinha** põe lá um **canto cego**:
  - em baixo, um módulo de 1,00 m. Os 63 cm do lado do canto são um painel fixo (a profundidade do móvel da outra
    parede, mais 5 cm para os puxadores dele), e a porta de 37 cm fica ao lado;
  - em cima, um de 0,80 m, com 40 cm tapados e uma porta de 40 cm;
  - a porta abre para fora do canto: as dobradiças do lado de fora e o puxador junto ao painel;
  - por dentro, as prateleiras ocupam a largura toda, também atrás do painel.
- Um troço demasiado curto para o canto cego fica como antes.
- Qualquer móvel inferior ou superior de portas pode ser um canto cego. Nas **Propriedades** há a **largura tapada**
  e o **lado do canto** (esquerda ou direita); 0 tira o painel. A porta tem de ficar com pelo menos 25 cm, senão o
  programa recusa.
- No IFC, os dois valores ficam nos parâmetros do móvel («Cego», «LadoCanto»); um móvel de antes lê-se sem canto. Na
  **lista de corte**, o painel aparece como «Painel cego (canto)», com as frentes.
- Testes:
  - núcleo:
    - o canto cego de 1,00 m com o painel de 63 cm e uma porta de 37 cm, do lado certo e com o puxador junto ao
      painel;
    - do outro lado, ao contrário;
    - as prateleiras de lado a lado;
    - a recusa com uma porta de menos de 25 cm;
    - numa cozinha em L, o primeiro troço com três módulos de 60 e o canto de 1,00 a acabar no canto, e o segundo
      troço a começar como antes;
    - a bancada ainda em L;
  - IFC: a cozinha em L com os cantos cegos em baixo e em cima, lidos de volta do ficheiro. Mudado o lado e tirado o
    painel, o móvel é feito outra vez.

## 0.238.0 — 2026-10-26

**As etiquetas mudadas à mão** (último resto do passo 5 da fase 9).

- Numa folha, as etiquetas dos desenhos de armaduras (por exemplo «2 Ø12 — pos. 3 — L = 6,54 m») e as das plantas
  de estrutura e da cofragem vista de baixo («P1 30×30», «V1 20×40», «L1 h = 0,15») **arrastam-se com o rato**:
  - carregue numa etiqueta e arraste-a. Ao largar, fica lá; o resto da vista não se mexe;
  - arrastar fora das etiquetas continua a mudar a vista inteira de sítio;
  - Ctrl+Z desfaz e Ctrl+Y refaz;
  - um duplo clique numa etiqueta mudada põe-na outra vez no seu sítio.
- A etiqueta acompanha o que diz e não o sítio onde estava escrita: a posição da lista de armaduras (a função do
  varão e o seu número) ou o elemento. Se as armaduras forem refeitas, a etiqueta continua desviada o mesmo.
- O desvio fica nas propriedades da vista: é gravado com o projeto e serve também a **memória de cálculo**, que
  desenha a etiqueta onde a pôs.
- Testes:
  - IFC: cada etiqueta com a sua chave, sem repetidas. Uma etiqueta mudada:
    - fica desviada o que se pediu e a vista não se mexe;
    - desfaz-se e refaz-se num passo;
    - volta ao sítio com «nenhum desvio»;
    - fica gravada no ficheiro e volta ao abrir;
    - aparece assim na memória de cálculo;
  - IFC: uma etiqueta de viga na planta de estrutura também se muda;
  - interface: uma etiqueta arrastada 30 × 20 píxeis fica com esse desvio, em metros, à escala da vista, e a vista
    não sai do sítio. Ctrl+Z tira-a e o duplo clique põe-na no sítio.

## 0.237.0 — 2026-10-26

**Os pormenores tipo das armaduras** (resto do passo 5 da fase 9).

- No painel do Projeto, em **Vistas ▸ Armaduras**, o primeiro item é agora **Pormenores tipo**. Põe-se numa folha
  com o botão direito ▸ **Pôr na folha**, e fica a 1:20.
- Os pormenores saem das armaduras que estão no modelo, não de um desenho feito à parte:
  - **nó viga-pilar:** a ponta da primeira viga armada (por nome) sobre o seu pilar. O desenho recorta do modelo,
    numa janela à volta do nó:
    - os varões de cima e de baixo da viga, dobrados para dentro do pilar;
    - os varões do pilar a subir;
    - os estribos e as cintas.
    Tem as etiquetas com as posições da lista de armaduras, a cota da largura do pilar e a cota da dobra dos varões
    de cima dentro do pilar;
  - **emendas por sobreposição:** uma por cada diâmetro dos varões principais do projeto. Cada uma tem dois varões
    sobrepostos, a cota do comprimento e o texto «Ø12 — l0 = 1,5 × lb,rqd = 0,75 m (C25/30, A500)». É o mesmo
    comprimento que o programa usa nas emendas do modelo (0.230).
- A **memória de cálculo** mostra os pormenores tipo no fim dos desenhos de armaduras.
- Testes:
  - IFC, no pórtico armado: sem armaduras, não há pormenores. Com armaduras:
    - o nó «V1 / P»;
    - nenhum varão fora da janela;
    - a cota de 0,30 do pilar e a da dobra;
    - uma emenda por diâmetro, com o l0 do modelo no texto e na cota;
    - 1:20 na folha;
  - interface: no painel do Projeto e numa folha nova, com o nome, a escala e a imagem gravada. A memória tem 26
    desenhos.

## 0.236.0 — 2026-10-26

**As marcas dos cortes nos desenhos de armaduras** (resto do passo 5 da fase 9).

- O alçado ou a planta de cada elemento mostra agora **por onde passa o seu corte**. Em cada ponta da linha de corte
  há um traço grosso, fora do betão, com a letra do corte ao lado:
  - **viga:** «A» por cima e por baixo, a meio vão;
  - **pilar:** «B» à esquerda e à direita, a meia altura;
  - **sapata e maciço:** «C» nas duas pontas, a meio da planta, ao longo do comprimento.
- O corte de cada um continua na sua vista, a 1:20, com o nome «Corte A–A — Viga 1» (0.234).
- Numa viga curta, as etiquetas dos varões afastam-se uma linha, para não ficarem por cima das marcas.
- Testes: IFC, no pórtico armado. A viga tem as duas marcas «A» a meio vão, o pilar as duas «B» e a sapata as duas
  «C». A laje não tem nenhuma.

## 0.235.0 — 2026-10-26

**A cofragem vista de baixo** (resto do passo 5 da fase 9).

- Cada pavimento com estrutura tem agora, além da **planta de estrutura**, a **cofragem vista de baixo** (a planta
  refletida, como se a víssemos num espelho no chão: fica virada como a planta). Está no painel do Projeto, em
  **Vistas ▸ Plantas de estrutura**, como «Térreo — cofragem vista de baixo».
- O que mostra:
  - o corte passa 5 cm abaixo da viga ou laje mais baixa do teto do pavimento;
  - os pilares cortados, a cheio;
  - as faces de baixo das vigas e das lajes, vistas. As arestas de uma laje que ficam atrás de uma viga não se
    veem, como em obra;
  - as aberturas das lajes;
  - a grelha, o norte e as etiquetas de cada pilar, viga e laje («P1 30×30», «V1 20×40», «L1 h = 0,15»).
- As sapatas e as estacas, que ficam por baixo do corte, não entram.
- Põe-se numa folha como a planta de estrutura (botão direito ▸ **Pôr na folha**), e fica gravada com o projeto.
- Testes:
  - IFC: no pórtico armado, os quatro pilares cortados e as arestas das vigas a 10 cm do eixo. As etiquetas dos
    pilares, das vigas e da laje estão lá, e as das sapatas não;
  - interface: a vista no painel do Projeto e numa folha nova, com o seu nome e a imagem gravada.

## 0.234.0 — 2026-10-26

**Os cortes das armaduras a uma escala própria** (resto do passo 5 da fase 9).

- Até aqui, o corte de uma viga ou de um pilar ia no mesmo desenho que o alçado, **ampliado 2,5×**, e à mesma escala
  na folha. Agora cada corte é **uma vista à parte**, desenhada à medida real:
  - viga: corte A–A;
  - pilar: corte B–B;
  - sapata e maciço: corte C–C (antes ia por baixo da planta, à mesma escala);
  - laje: não tem corte.
- **Pôr na folha** um desenho de armaduras põe as duas vistas na folha, num só passo (Ctrl+Z tira as duas):
  - o alçado (ou a planta) a **1:50**, com o nome «Armaduras — Viga 1»;
  - o corte a **1:20**, ao lado, com o nome «Corte A–A — Viga 1».
- Essas são as escalas habituais. Uma vista que não caiba na folha a 1:50 (uma laje grande) fica com a escala
  automática, e cada vista pode ter outra escala, à escolha, na barra da folha.
- Na folha, o corte tem as mesmas cotas, os mesmos estribos e os mesmos varões cortados que antes. As cotas e os
  textos ficam do mesmo tamanho no papel.
- A **memória de cálculo** mostra, em cada elemento, o alçado a 1:50 e, ao lado, o corte a 1:20.
- Correções:
  - os desenhos de armaduras e as plantas de estrutura postos numa folha **perdiam-se ao gravar e abrir** o projeto.
    Agora ficam;
  - o nome por baixo de um desenho de armaduras já não fica por cima das cotas: o desenho conta com elas.
- Testes:
  - IFC: o alçado da viga sem o corte, e as cotas com espaço para os textos;
  - IFC: o corte A–A a 0,20 × 0,40 reais, com o estribo, os varões cortados e as duas cotas. O pilar circular e a
    sapata também têm o seu corte; a laje não tem;
  - IFC: na folha, as escalas 1:50 e 1:20, as duas vistas a voltar do ficheiro e um só passo a desfazer;
  - interface: a folha com a viga e o pilar, cada um com o seu corte, nas escalas e com os nomes certos; a memória
    com os 25 desenhos.

## 0.233.0 — 2026-10-26

**A memória de cálculo com os desenhos** (resto do passo 5 da fase 9).

- A **Memória de cálculo…** (separador **Estrutura**) passa a ter os desenhos de armaduras de cada elemento armado:
  - ficam na secção 8 (armaduras), depois da lista de varões, com o título «Desenhos de armaduras (1:50)»;
  - vão pela ordem pilares, vigas, lajes e sapatas, e cada desenho tem o nome do elemento por baixo;
  - são os mesmos desenhos de **Vistas ▸ Armaduras**: os varões, as etiquetas, os cortes e as cotas da 0.232.
- No **HTML**, os desenhos são vetoriais (SVG), à escala 1:50 no papel.
- No **PDF**, cada desenho é uma imagem fina (200 pontos por polegada) à mesma escala. Um desenho que não cabe na
  largura da folha A4 é reduzido para caber.
- Testes:
  - IFC: o desenho de uma viga em SVG, com o tamanho certo no papel, os varões e as cotas; a memória do pórtico
    armado com os 13 desenhos;
  - interface: a memória em HTML com os 13 desenhos e o PDF com as 13 imagens.

## 0.232.0 — 2026-10-26

**As cotas nos desenhos de armaduras** (resto do passo 5 da fase 9).

- Os desenhos de armaduras passam a ter cotas, no estilo de cotas do projeto. Saem na folha, no PDF e no DXF, como
  as dos outros desenhos:
  - **viga:**
    - o comprimento por baixo das etiquetas e a altura do lado esquerdo;
    - o alcance de cada varão que para antes das pontas: os reforços de cima sobre a viga e os de baixo por baixo;
    - no corte A–A, a largura e a altura reais (o corte está ampliado, mas as cotas leem a medida verdadeira);
  - **pilar:** a altura ao lado do alçado, e no corte B–B os lados (num circular, o diâmetro);
  - **sapata e maciço:** os dois lados da planta e a altura no corte C–C;
  - **laje:** os dois lados maiores do contorno.
- Testes: IFC, no pórtico armado:
  - a viga com o seu comprimento e o corte com 0,20 e 0,40;
  - o pilar com 3,00 e 0,30;
  - a sapata com 1,20 e 0,50;
  - a laje com 6,00 e 4,00.

## 0.231.0 — 2026-10-26

**As armaduras nos pisos tipo** (resto do passo 4 da fase 9).

- Nos **pisos tipo** (Gerenciar ▸ Pavimentos iguais), cada pilar, viga, laje e sapata tem um igual em cada um dos outros
  pisos. Até aqui cada um era armado com os seus próprios esforços, e os pisos iguais podiam ter varões diferentes.
- Agora a **Verificação EC2** dá a todos os iguais **a mesma armadura**: a do mais esforçado deles (o estado pior, a
  maior utilização). É como se faz em obra, com um só desenho para os pisos iguais.
  - Cada um recebe a nota «piso tipo: a mesma armadura nos N elementos iguais — a do mais esforçado deles»;
  - a disposição de cada um (quanto entra nos apoios, a direção principal) continua a ser a sua, que é igual;
  - os elementos dos pisos que não são tipo, e as cópias de grupos comuns (por exemplo, apartamentos copiados),
    ficam com a sua própria armadura.
- **Pôr as armaduras no modelo** faz varões iguais nos pisos iguais.
- Testes:
  - IFC: um pórtico de três pisos com os dois de cima tipo. Cada pilar, viga e laje desses pisos tem os mesmos
    varões que o seu igual e a nota; os pilares do rés-do-chão ficam com os seus;
  - janela real: o pilar de um piso tipo diz «piso tipo» e tem os mesmos varões e o mesmo número de varões no
    modelo que o seu igual.

## 0.230.0 — 2026-10-26

**As emendas dos varões compridos** (resto do passo 4 da fase 9).

- Um varão com mais de **12 m** (o comprimento comercial) já não fica inteiro no modelo:
  - é cortado em troços iguais ao longo do seu troço reto mais comprido, nenhum com mais de 12 m;
  - cada emenda é uma sobreposição de **l0 = α6 · lb,rqd** com α6 = 1,5 (EC2 8.7.3): o caso de todas as emendas na
    mesma secção, o mais pesado, para ficar do lado seguro. O comprimento é arredondado aos 5 cm;
  - o primeiro troço guarda o início do varão (com a sua dobra) e o último guarda o fim. Os troços alternados ficam
    um diâmetro ao lado, como dois varões emendados ficam encostados.
- Vale para as vigas, as lajes, as sapatas e os maciços. Os pilares já emendam os varões em cada piso.
- Os troços aparecem na lista de armaduras como posições próprias, e o aço total conta as sobreposições.
- **Correção:** uma sapata corrida sem pórtico (só a parede) não era calculada, porque o dimensionamento parava
  sem análise. Agora é calculada sempre, porque só precisa do peso da parede.
- Testes:
  - um varão Ø16 de 20 m dobrado nas pontas, cortado em troços de no máximo 12 m:
    - com sobreposições de 1,5 lb,rqd;
    - o primeiro troço com o início e o último com o fim;
    - os alternados um diâmetro ao lado;
    - o aço total igual ao do varão mais as sobreposições;
  - um de 10 m fica inteiro; os estribos ficam como estavam;
  - IFC: uma parede de 15 m numa sapata corrida, com os varões longitudinais emendados (nenhum com mais de 12 m) e
    os transversais inteiros;
  - janela real: a sapata corrida calculada sozinha e os seus varões longitudinais emendados.

## 0.229.0 — 2026-10-26

**A dispensa de varões nas vigas** (resto do passo 4 da fase 9).

- Até aqui, todos os varões de uma viga corriam de ponta a ponta. Agora:
  - a **análise** guarda a envolvente dos momentos ao longo de cada viga: o maior e o menor de todas as
    combinações ELU, em 21 pontos por peça;
  - na **Verificação EC2**, ficam de ponta a ponta só os varões dos cantos (2) e, em baixo, pelo menos um quarto dos
    do vão (EC2 9.2.1.4(1) e 9.2.1.5(1)). Os outros vão só onde fazem falta:
    - onde a envolvente, deslocada de a_l = z·cot θ/2 para cada lado (EC2 9.2.1.3(2), com o θ dos estribos), pede
      mais do que os contínuos resistem;
    - mais o comprimento de amarração lb,rqd para lá desse ponto (9.2.1.3(3)), contado em má aderência para os de
      cima;
  - em baixo, o reforço fica a meio do vão; em cima, o reforço fica sobre cada apoio, a partir da ponta da viga, e
    entra no pilar dobrado como os outros;
  - se um varão é preciso em quase toda a viga, corre inteiro. Em vigas com duas camadas nenhum varão para;
  - a nota da viga diz quantos ficam de ponta a ponta, quantos param e onde (em metros desde o início da viga),
    com a_l e lb,rqd.
- **Pôr as armaduras no modelo** faz os varões com estes comprimentos. Na lista de armaduras aparecem como posições
  diferentes, por terem outro comprimento. Os varões são guardados com o projeto da viga e refeitos iguais se a
  viga mudar.
- Numa viga simplesmente apoiada com carga uniforme, a translação e a amarração costumam cobrir a viga toda, e aí
  nenhum varão para. A dispensa aparece sobretudo com momentos negativos nos apoios.
- Testes:
  - o momento de n varões igual ao que a sua área precisa;
  - uma viga de 8 m, 30 × 60, com 180 kNm no vão e −120 nas pontas:
    - 2 varões de ponta a ponta e os outros numa zona simétrica;
    - a borda dessa zona fica lb,rqd para lá de onde a envolvente deslocada encontra o momento dos dois varões;
    - o reforço de cima a partir de cada ponta;
  - uma envolvente plana: nada para; em duas camadas: nada para;
  - os varões: 2 de ponta a ponta dobrados e 2 retos entre 1,5 e 4,5 m; o reforço de cima de cada ponta até 1,2 m
    e desde 4,8 m;
  - IFC: no pórtico 8 × 5 m com a laje de sala:
    - a envolvente com 21 pontos;
    - a nota e os varões de dois comprimentos;
    - guardados e refeitos iguais;
  - janela real: a nota da dispensa e os varões de dois comprimentos em baixo e em cima.

## 0.228.0 — 2026-10-26

**Os maciços de estacas e as sapatas corridas** (resto do passo 4 da fase 9).

- Até aqui, um maciço de estacas era calculado como uma sapata isolada assente no solo, e uma sapata corrida não
  era calculada. Agora o programa distingue as três:
  - **sapata isolada** (sob um pilar): como até aqui;
  - **maciço de estacas** (sob um pilar): com as suas estacas, a posição de cada uma e o diâmetro;
  - **sapata corrida** (sob uma parede): com a parede que suporta e o peso dela por metro.
- **Maciços de estacas**, calculados por **bielas e tirantes** (EC2 6.5):
  - a força do pilar e o peso do maciço repartem-se pelas estacas, e a nota diz a carga de cada uma (ELU e
    serviço). A capacidade da estaca fica para o projeto de fundações;
  - **2 estacas:** um tirante ao longo delas, T = N (2l − a) / (8d). As bielas vão de um quarto do pilar até ao eixo
    de cada estaca;
  - **4 estacas** nos cantos: um tirante em cada lado, T = N (2l − a) / (16d);
  - o ângulo das bielas é comparado com o intervalo de 45° a 55° recomendado por Blévot; fora dele, fica a
    laranja;
  - os nós (EC2 6.5.4, nós hidrostáticos): sob o pilar, N / A ≤ k1 ν′ fcd; sobre cada estaca, R / A ≤ k2 ν′ fcd
    (com k1 = 1,0, k2 = 0,85 e ν′ = 1 − fck/250). Se não cumprem, o maciço falha;
  - a armadura do tirante fica na faixa sobre as estacas, com a malha mínima em toda a base. Na direção sem
    tirante (o maciço de 2 estacas, na transversal) fica a malha mínima;
  - maciços de 1 estaca: a carga desce direta, com malha mínima. Outras disposições ficam a laranja, para o
    engenheiro.
- **Sapatas corridas:**
  - a carga é o peso da parede por metro (o seu volume × 15 kN/m³ a dividir pelo comprimento), mais o peso da
    própria sapata;
  - verifica a pressão no solo e diz a largura precisa quando não chega;
  - verifica se a sapata é rígida;
  - calcula a flexão de cada aba a partir da face da parede, com os varões transversais;
  - os varões longitudinais de distribuição têm 20 % dos transversais (EC2 9.3.1.1(2)).
- Uma sapata corrida já não é tomada pela sapata de um pilar, nem dá o aviso «sapata sem pilar».
- **Pôr as armaduras no modelo** faz as malhas dos maciços e das sapatas corridas.
- Testes:
  - maciço de 2 estacas a 0,90 m sob um pilar 30 × 30 com 1000 kN:
    - o peso somado;
    - o tirante pela fórmula, com d = 0,534 m;
    - o ângulo das bielas;
    - as tensões dos nós e os seus limites;
    - o tirante contido na faixa sobre as estacas;
    - a malha mínima na transversal;
  - maciço de 4 estacas com um tirante igual em cada lado;
  - um pilar pesado demais para o nó dá falha;
  - maciço de 1 estaca com malha mínima;
  - sapata corrida 50 × 30 sob uma parede de 8,4 kN/m: 24,3 kPa, a flexão e os 20 %. Com carga a mais, a largura
    precisa;
  - IFC: um pórtico em maciços de 2 e de 4 estacas e uma parede numa sapata corrida, todos lidos como são,
    verificados e armados;
  - janela real: as notas das bielas e tirantes e da sapata corrida, e as armaduras feitas.

## 0.227.0 — 2026-10-26

**Os pilares circulares, em L e em T, como são** (resto do passo 4 da fase 9).

- Até aqui, todos os pilares entravam no cálculo como retângulos do tamanho da sua caixa: um circular de Ø30 contava
  como 30 × 30, com 27 % mais área e 70 % mais inércia do que tem, e pesava a mais. Agora:
  - o **modelo analítico** guarda a forma de cada pilar (lida do seu perfil IFC), a espessura dos braços e a sua
    direção em planta. Um pilar retangular rodado também entra rodado no cálculo (antes ficava sempre alinhado
    com X);
  - na **análise**, a secção tem a área, as inércias e a torção verdadeiras:
    - círculo: π r², π r⁴/4;
    - L e T: em braços, com as inércias em relação ao centro de gravidade;
  - o **peso próprio** do pilar é o da secção verdadeira;
  - na **verificação EC2**, o diagrama de interação N–M destes pilares é calculado **por fibras**, com os varões
    onde ficam de facto (mesmo bloco retangular de tensões e εcu = 3,5 ‰ dos retangulares). O momento é verificado
    nos dois sentidos de cada direção, porque o L e o T não são simétricos. A esbelteza usa o menor raio de giração
    da secção;
  - os **varões**:
    - num circular, à volta de um círculo, pelo menos 6 (prática corrente; o EC2 9.5.2(4) pede 4);
    - num L, nos seis cantos; num T, nos oito (um em cada canto, EC2 9.5.2(4));
    - os restantes aos pares nas faces mais compridas, para a secção ficar simétrica;
  - as **cintas**: num circular, cintas redondas com sobreposição de 10 φ; num L ou T, uma cinta fechada à volta
    de cada braço, com o espaçamento limitado também pela espessura do braço;
  - no **desenho de armaduras** do pilar, o corte mostra a forma verdadeira (círculo, L, T) e todas as cintas do
    nível.
- A nota do pilar diz «secção circular» (ou em L, em T): diagrama por fibras, verificado nos dois sentidos.
- Os pilares retangulares são verificados exatamente como antes.
- Testes:
  - as secções conferidas à mão:
    - Ø30: π r² e π r⁴/4;
    - L 40 × 40 com braços de 15 cm: 0,0975 m², centro a 4,8 cm do meio;
    - T 50 × 40: 0,1125 m², centro 5,8 cm acima;
    - retângulo igual ao de antes;
  - o diagrama por fibras igual ao do retângulo: as pontas exatas, e a menos de 3 % pelo meio;
  - os varões:
    - à volta do círculo, nos 6 cantos do L e nos 8 do T;
    - os extras simétricos;
    - nada quando não cabem;
  - um Ø30 com 800 kN e 30 kNm verificado com 6 varões ou mais, dentro do seu diagrama, armado com varões à mesma
    distância do eixo e cintas redondas;
  - um L com uma cinta por braço;
  - a análise com a secção e o peso verdadeiros;
  - IFC: um pórtico com um pilar de cada forma, verificado e armado, com o desenho em círculo;
  - janela real: os quatro pilares verificados, a forma dita na nota, os varões do circular à volta do eixo e as
    cintas do L uma por braço.

## 0.226.0 — 2026-10-26

**A segunda camada de varões nas vigas, e o aviso da armadura de pele** (resto do passo 4 da fase 9).

- Na **Verificação EC2 e armaduras…**, quando os varões de uma viga não cabem numa camada com as folgas do EC2
  (8.2(2)), em vez de ficar só o aviso «não cabem», o programa põe-nos **em duas camadas** (EC2 8.2(3)):
  - escolhe o menor diâmetro em que isso resulte;
  - põe na primeira camada os que cabem e na segunda o resto, nunca mais do que na primeira;
  - os da segunda ficam por cima dos da primeira, a começar pelos dos cantos, com a folga entre camadas;
  - a altura útil passa a ser a do centro dos varões, e a área precisa é calculada outra vez com ela, até
    acertar.
- A linha da viga diz, por exemplo, «inf. 6 Ø16 (3 + 3)». A nota explica as duas camadas e dá a altura útil.
- **Pôr as armaduras no modelo** faz a segunda camada: os varões por cima dos da primeira, com as dobras das pontas
  mais curtas pela folga. Estes varões são guardados com o projeto da viga e refeitos se ela mudar.
- **Armadura de pele:** uma viga com 1,00 m ou mais de altura recebe a nota «leva armadura de pele nas faces
  laterais, entre a armadura de tração e o eixo neutro, dentro dos estribos (EC2 7.3.3(3))», a laranja, para o
  engenheiro definir. A área não é calculada: não foi possível confirmar no texto da norma a fórmula e os
  coeficientes, e o programa não inventa valores.
- Testes:
  - EC2: uma viga 20 × 60 com 280 kNm leva 5 Ø20, com 3 na primeira camada e 2 na segunda. A altura útil é
    0,534 m e a área é calculada com ela. As folgas: 3 varões cabem numa camada e 4 não. Uma viga de 1,00 m leva
    a nota da pele; uma de 0,95 m não;
  - os varões: 3 em baixo e 2 por cima dos dos cantos, à distância φ + folga, com as dobras mais curtas; guardados
    e lidos outra vez;
  - janela real: um pórtico de 8 × 5 m com vigas 20 × 50 e a laje como armazém dá «6 Ø16 (3 + 3)» nas vigas
    longas. A nota fala das duas camadas, e os varões de baixo ficam a duas alturas.

## 0.225.0 — 2026-10-26

**O programa mais leve e a barra de parâmetros fixa** (pedido do dono).

- A **barra de parâmetros** (por baixo da fita) tem agora sempre a mesma altura, seja qual for a ferramenta e
  esteja ou não algo selecionado. Antes ia de 31 a 41 px conforme os campos de cada ferramenta, e a vista saltava
  para cima e para baixo a cada troca.
- **Medido antes de mexer.** No prédio de ensaio (2161 elementos), comparado com a medição da versão 0.53, mudar
  uma parede passara de 18 ms para 175 ms. As causas eram procuras no modelo inteiro feitas em cada edição, mesmo
  quando não havia nada para procurar:
  - as paredes e pilares presos a uma laje ou a uma cobertura eram procurados em todos os elementos mesmo quando a
    edição não tinha mexido em nenhuma laje nem cobertura;
  - o mesmo com as paredes por baixo de vigas, as lajes nos vãos das vigas e as vigas presas a pilares, ao mover;
  - para saber o tipo de cada elemento liam-se todos os seus conjuntos de propriedades; agora lê-se só o valor
    preciso;
  - a lista de pisos era calculada cinco ou seis vezes em cada edição; agora calcula-se uma vez enquanto o
    ficheiro não muda;
  - as cotas temporárias de uma parede selecionada calculavam os eixos de todas as paredes a cada seleção; agora
    ficam guardados, e só os das paredes alteradas são refeitos;
  - a ferramenta de parede projetava no ecrã, uma a uma, as pontas de todas as paredes a cada movimento do rato;
    agora faz a conta de uma vez;
  - a colocação dos elementos é calculada sem refazer a cadeia piso → edifício → terreno para cada um.
- Resultados no mesmo prédio:

  | Ação | Antes | Agora |
  |---|---|---|
  | Mudar uma parede | 152 ms | 8 ms |
  | Juntar uma parede | 233 ms | 41 ms |
  | Mover uma parede | 181 ms | 5 ms |
  | Selecionar uma parede | 430–700 ms | ~80 ms (a 1.ª vez depois de abrir, ~430 ms) |
  | Trocar de ferramenta | 45–75 ms | 21–42 ms |
  | Movimento do rato com a ferramenta de parede (sem a imagem) | 14 ms | 4,4 ms |

- A imagem da vista leva ~16 ms (cerca de 60 por segundo) e não muda com a resolução. O modo direto de desenho
  no ecrã («screen») não funciona no WSL (erro da superfície), por isso fica o atual.
- Testes:
  - a leitura direta do tipo e da colocação dá o mesmo que a do IfcOpenShell (uma parede rodada num piso de cima e
    a sua porta);
  - a lista de pisos guardada vê na hora um piso feito na mesma edição, e esquece-o quando é desfeito;
  - os eixos das paredes acompanham uma parede alongada, apagada e desfeita;
  - as procuras não leem nada quando não há nada para procurar;
  - janela real: em oito ferramentas e com uma parede selecionada, a barra fica sempre com a mesma altura e a vista
    no mesmo sítio.

## 0.224.0 — 2026-10-25

**A armadura superior das lajes sobre os apoios** (resto do passo 4 da fase 9).

- A **Verificação EC2 e armaduras…** calcula agora, para cada laje, a **armadura superior sobre as vigas** em
  que ela apoia, nas duas direções:
  - Com as lajes como cascas (0.223), usa o momento negativo da análise (Wood–Armer, face de cima).
  - Fica sempre com pelo menos um quarto do momento do vão (EC2 9.3.1.2(2): o encastramento parcial que as
    vigas dão) e nunca abaixo da armadura mínima.
  - Pelas áreas de influência, fica só com o quarto do vão.
  - Cada direção tem a sua nota: o momento, o quarto do vão, a área precisa e a malha escolhida.
- O programa encontra sozinho as **vigas onde a laje apoia**: à cota dela, ao longo das bordas (com o eixo até 0,40 m
  fora) ou a atravessá-la. Para cada uma mede o vão de cada lado, até à viga seguinte ou ao bordo oposto.
- **Pôr as armaduras no modelo** faz os varões superiores (`IfcReinforcingBar`, MAIN):
  - atravessam cada viga, com o espaçamento da malha superior;
  - de cada lado vão até 0,2 do vão a partir da face da viga (EC2 9.3.1.2(2));
  - numa viga de bordo, vão do bordo da laje (menos o recobrimento) e dobram 10 cm para dentro da viga;
  - os que seguem a direção principal da laje ficam por cima; os da outra direção, uma camada abaixo.
- As novas posições aparecem na lista de armaduras como «superior X» e «superior Y»:
  - no IFC, «armadura superior X/Y sobre os apoios»;
  - na linha da laje, «malha inf. … · sup. … × …».
- No desenho de armaduras da laje, os varões superiores aparecem com traço mais grosso e com a etiqueta «sup.».
- A nota da laje diz até onde vão os varões. Nos bordos livres e sobre os pilares de lajes sem vigas, a armadura
  fica a definir pelo engenheiro.
- Testes:
  - EC2:
    - a malha superior com o momento da análise quando é maior que o quarto do vão, e com o quarto quando é menor;
    - a área nunca abaixo da precisa;
    - por Marcus, o quarto de cada vão;
  - os apoios de uma laje 6 × 4 com uma viga a meio: 7 troços, as vigas de bordo com o vão para dentro, a do
    meio com 3 m de cada lado;
  - os varões:
    - 19 sobre a viga do meio com 1,40 m (0,2 × 3 + meia viga de cada lado);
    - nas bordas, dobrados 10 cm para baixo, com 0,2 × 3 + meia viga − recobrimento;
    - a segunda direção uma camada abaixo, todos dentro da laje menos o recobrimento;
  - IFC: a laje do pórtico com as quatro funções (malha X/Y, superior X/Y), os superiores com uma dobra (forma 11),
    o IFC válido;
  - o desenho da laje com «sup.» e dois traços;
  - janela real: a linha da laje diz «sup.», a nota fala da armadura superior sobre os apoios, as armaduras ficam
    no modelo com as quatro funções e os superiores dobrados, e o desenho mostra-os.

## 0.223.0 — 2026-10-25

**As lajes como cascas** (último resto do passo 3 da fase 9).

- Na análise da estrutura, cada laje entra agora no pórtico espacial como uma **casca**: uma malha de triângulos
  que dobra como placa e trabalha no seu plano.
  - Cada triângulo é um **DKT** (triângulo de Kirchhoff discreto, Batoz, Bathe e Ho, 1980), o elemento corrente das
    lajes finas, com uma membrana de deformação constante.
  - Foi conferido com as placas de Timoshenko (laje quadrada de 4 m, malha 8 × 8):
    - simplesmente apoiada: flecha a 1 % de 0,00406 qa⁴/D e momento a 5 % de 0,0479 qa²;
    - encastrada: flecha a 3 % de 0,00126 qa⁴/D.
- A malha de cada laje é feita sozinha, com passo de 0,50 m. Num edifício grande o passo aumenta, para os nós
  ficarem à volta de 2500.
  - Tem nós ao longo das vigas e nos pilares; as vigas são cortadas nesses nós, e a laje e as vigas dobram juntas.
  - Uma laje desenhada até à face da viga é levada até ao eixo dela, como no modelo analítico.
  - As cargas da laje (G e Q) ficam sobre os seus triângulos. O total é sempre o da laje real.
- Assim, a laje leva a carga para onde está a rigidez, e não por áreas de influência: no pórtico de ensaio, a viga
  do meio, mais flexível, recebe menos do que antes.
- **No diálogo Analisar a estrutura…**, cada laje tem a sua linha:
  - os **momentos a armar** por metro (Wood–Armer: o momento torsor somado a cada direção), x na direção principal
    da laje e y na outra;
  - em M vão, a face de baixo; em M apoio, a face de cima;
  - a **flecha** (combinação quase permanente, elástica, sem fluência), a vermelho acima de L/250;
  - a dica da linha explica o método e o passo da malha.
- **Verificação EC2 e armaduras…:** a malha inferior de cada laje é calculada com os momentos da casca, e já não
  pelas tabelas de Marcus. A nota da laje diz isso.
- A memória de cálculo tem as lajes na tabela da análise, com a nota do método.
- Em **Ações e materiais…** há a escolha nova **Lajes no cálculo**:
  - **Cascas (elementos finitos)**, a escolha por omissão;
  - **Áreas de influência (cargas às vigas)**, como até aqui.

  A escolha fica gravada no IFC com as outras definições.
- O pórtico espacial ficou mais rápido para muitos nós:
  - os nós são renumerados (Cuthill–McKee inverso), para a matriz ficar estreita;
  - a matriz é resolvida por blocos densos com o LAPACK.

  Um mecanismo continua a ser indicado com o nó onde está.
- Testes:
  - as placas de Timoshenko pelo pórtico espacial;
  - o triângulo:
    - movido ou rodado por inteiro, sem esforços;
    - num esticão uniforme, a força certa;
    - os momentos de Wood–Armer;
  - o resolvedor por blocos igual ao do numpy, e um pivô nulo indicado no sítio certo;
  - a malha de uma laje 6 × 4 com uma viga a meio:
    - os nós ao longo da viga, a área inteira e todos os triângulos no mesmo sentido;
    - a laje desenhada à face das vigas levada aos eixos;
    - uma laje em L com a área certa;
  - a análise com cascas:
    - o que entra desce;
    - 192 triângulos, momentos em baixo e em cima, flecha pequena;
    - a viga do meio com menos momento do que por áreas, contada inteira (4 m, 11 pontos no diagrama);
    - o EC2 da laje com os momentos da casca;
  - a memória de cálculo com a nota;
  - janela real:
    - em Ações e materiais, a escolha com as duas opções e «cascas» por omissão;
    - a laje listada com «x … / y …» e a flecha;
    - com «áreas», nenhuma laje, e a escolha gravada.

## 0.222.0 — 2026-10-25

**A 2.ª ordem** (resto do passo 3 da fase 9).

- A análise da estrutura vê agora, piso a piso, quanto o peso do edifício agrava o vento e o sismo quando a
  estrutura se desloca para o lado (o efeito P-Δ):
  - em cada piso, e para cada ação (vento X, vento Y, sismo X, sismo Y), calcula o coeficiente
    **θ = P·dr / (V·h)** da NP EN 1998-1 (4.4.2.2):
    - P é a carga vertical desse piso e dos de cima (no sismo G + ψ2 Q; no vento 1,35G + 1,50Q);
    - V é o esforço transverso do piso;
    - dr é a deriva entre pisos com a estrutura fendilhada. No sismo conta metade da rigidez (EC8 4.3.1(7)) e
      multiplica por q (EC8 4.3.4). No vento conta 0,4 Ecd Ic (EC2 H.1.2, com γcE 1,2);
    - h é a altura do piso.
  - **θ até 0,10:** a 2.ª ordem despreza-se (EC8 4.4.2.2(2); EC2 5.8.2(6)).
  - **Acima de 0,10:** essa ação horizontal é multiplicada por 1/(1 − θ) do pior piso em todas as combinações (EC8
    4.4.2.2(3); EC2 H.2). Os esforços dos pilares e das vigas, a verificação EC2 e as armaduras já saem com isso.
  - **Acima de 0,20:** o programa diz que o método simplificado não chega e que é preciso uma análise de 2.ª ordem
    do engenheiro. Mesmo assim multiplica a ação, como estimativa.
  - **Acima de 0,30:** não é permitido (EC8 4.4.2.2(4)). O programa diz que a estrutura é flexível demais e
    sugere aumentar os pilares ou juntar paredes resistentes.
- No diálogo **Analisar a estrutura…**:
  - há uma tabela nova com cada piso e cada ação: P, V, deriva, θ e o que pede;
  - θ aparece a laranja quando a ação é multiplicada e a vermelho quando passa de 0,20;
  - o resumo diz o θ máximo, onde está e por quanto se multiplicou cada ação.
- A memória de cálculo tem a mesma tabela e a mesma frase, com a explicação do método.
- **Correção:** num edifício de vários pisos, a sapata de um pilar prendia também os pilares dos pisos de cima,
  como se cada piso estivesse apoiado no chão. A estrutura parecia muito mais rígida do que é, e as cargas
  «desciam» a meio do edifício. Agora a sapata só segura o pilar que nasce no seu topo (até 0,50 m acima dele).
- Testes:
  - um piso: θ é exatamente P·dr/(V·h); P é o peso do piso no sismo e 1,35G + 1,50Q no vento; V é a força do
    piso. A razão entre θ do sismo e θ do vento é a que as fendilhações e o q dão. θ é pequeno e nada é
    multiplicado;
  - três pisos com pilares de 20 cm:
    - só 4 apoios, os das sapatas;
    - V e P somados de cima para baixo, e θ maior no piso de baixo;
    - o sismo multiplicado por 1/(1 − θ máx.);
    - os momentos dos pilares de baixo maiores do que na mesma análise sem a 2.ª ordem;
  - os quatro escalões de θ (0,10 / 0,20 / 0,30);
  - a memória de cálculo com a frase e a nota;
  - janela real: uma torre de 3 pisos dá a tabela com 12 linhas, o piso de baixo é o pior, o resumo diz a 2.ª
    ordem e os fatores, e há só 4 apoios.

## 0.221.0 — 2026-10-25

**Os resultados da análise no IFC** (resto do passo 3 da fase 9).

- No diálogo **Analisar a estrutura…** há o botão novo **Guardar resultados no IFC**. Grava no IFC, num só passo de
  desfazer:
  - a **combinação** 1,35G + 1,50Q, como grupo de cargas do tipo combinação, com os casos G e Q e os seus fatores;
  - um **grupo de resultados** (`IfcStructuralResultGroup`, teoria de 1.ª ordem, linear) dessa combinação, ligado
    ao modelo analítico como o seu resultado;
  - as **reações** de cada apoio: forças e momentos nos nós (`IfcStructuralPointReaction`);
  - os **momentos fletores** ao longo de cada viga e pilar: 11 valores, cada um com a sua distância ao início
    (`IfcStructuralCurveReaction` discreta).
- Os valores vão em unidades do SI (N, N·m), como as cargas.
- Refaz também o modelo analítico e os casos G e Q, para os resultados ficarem certos com eles.
- Guardar outra vez substitui os resultados anteriores. Refazer o modelo analítico tira-os, para não ficarem de um
  modelo que já não existe.
- Assim, os programas de estruturas que leem IFC recebem as cargas e também os resultados.
- Testes:
  - IFC: no pórtico, a combinação com os fatores 1,35 e 1,50; o grupo de resultados de 1.ª ordem e linear, como
    resultado do modelo; 4 reações, cuja soma vertical é a da análise; os momentos das 8 barras com 11 valores; o
    IFC válido com as regras do esquema; guardar duas vezes deixa um só grupo; desfazer tira-o;
  - janela real: o botão no diálogo grava o grupo e as 4 reações, a janela diz «Resultados guardados no IFC», e
    Ctrl+Z tira-os.

## 0.220.0 — 2026-10-25

**Os diagramas de esforços desenhados no modelo** (resto do passo 3 da fase 9).

- Botão novo **Diagramas de momentos** no separador **Estrutura**.
  - Analisa a estrutura (com as ações e materiais do projeto) e desenha sobre o modelo o diagrama de momentos
    fletores de cada viga e pilar, para a combinação 1,35G + 1,50Q.
  - Cada momento é desenhado perpendicular à barra, do lado das fibras traccionadas: numa viga, o momento positivo
    a meio vão fica por baixo e o negativo nos apoios fica por cima.
  - O maior momento de todos fica a 1 m da barra, e os outros à mesma escala.
  - Linhas a ligar o diagrama à barra fazem a trama; em cada barra fica escrito o seu maior valor, em kNm.
  - A barra de baixo diz a combinação, quantas barras e o maior momento. Desligando o botão, os diagramas saem.
- Continua a ser pré-dimensionamento.
- Testes:
  - núcleo: o pórtico de 6 × 4 m com laje tem diagrama em todas as barras. Na viga do meio, os momentos são negativos
    nas pontas e positivos a meio, dentro da envolvente, e o lado de cima da viga é o seu z. Os valores nas pontas são
    os do cálculo do vão;
  - janela real: o botão está na Estrutura, os diagramas das 8 barras aparecem com os valores e saem ao desligar.

## 0.219.0 — 2026-10-25

**As categorias de terreno do vento do Anexo Nacional** (resto do passo 2 da fase 9).

- As categorias de terreno passam a ser as do **Anexo Nacional da NP EN 1991-1-4**, confirmadas (estavam os valores
  recomendados da EN, com uma nota a dizer que faltava confirmar). São quatro, sem a categoria 0:

  | Categoria | Terreno | z0 | zmin |
  |---|---|---|---|
  | I | zona costeira exposta aos ventos de mar | 0,005 m | 1 m |
  | II | vegetação rasteira, obstáculos isolados | 0,05 m | 3 m |
  | III | subúrbios, florestas | 0,3 m | 8 m |
  | IV | cidade (15 % com edifícios de mais de 15 m) | 1,0 m | 15 m |

- A janela **Ações e materiais…** mostra cada categoria com a sua descrição.
- Um projeto antigo que tivesse a categoria 0 lê-se como I (a costa).
- O que muda nos números:
  - na categoria I, a pressão do vento fica um pouco maior;
  - abaixo do zmin, a pressão é a do zmin, que agora é mais alto (3, 8 e 15 m em vez de 2, 5 e 10 m);
  - a categoria III, a habitual, não muda acima de 8 m.
- Fonte: o quadro das categorias de terreno do material de Dimensionamento de Estruturas do IST, que segue a norma e
  o seu Anexo Nacional. As intensidades de turbulência desse material só batem com estes valores.
- Testes:
  - núcleo: as quatro categorias e os seus valores; as intensidades de turbulência a 10 m (0,13 / 0,19 / 0,29 /
    0,37) como as do Anexo; abaixo do zmin, a pressão do zmin; a categoria 0 antiga lida como I;
  - janela real: a lista das categorias tem as quatro.

## 0.218.0 — 2026-10-25

**O uso por laje** (resto do passo 2 da fase 9).

- No painel **Propriedades** de uma laje há a linha nova **Uso (sobrecarga)**.
  - Por omissão é «O do projeto (Ações e materiais)»: o uso dos pisos, ou o da cobertura na laje mais alta, como
    até agora.
  - Pode escolher-se o uso próprio dessa laje: A habitação, B escritórios, C1 a C3, D1 comércio, E1 armazéns,
    H cobertura não acessível.
  - A sobrecarga e o ψ dessa laje passam a ser os do seu uso, também na massa sísmica do piso (um armazém pesa mais
    no sismo). Numa laje de cobertura com uso próprio continua a contar a neve, quando é maior.
  - Fica guardado na laje, no IFC, e desfaz-se num passo.
- **Correção (paredes curvas da nuvem, 0.215)**: o ajuste dos arcos ficou robusto.
  - Afina os melhores candidatos, tira os pontos soltos e escolhe pelo arco contínuo mais comprido.
  - Antes, conforme o sorteio, podia sair um círculo errado e as duas faces de uma parede curva não
    emparelhavam.
- Testes:
  - IFC: a laje de cobertura marcada como armazém (E1) fica com 7,5 kN/m², e a massa sísmica do piso cresce
    0,8 × 7,5 × 24 kN; de volta ao do projeto, 0,4; fica no IFC e desfaz-se;
  - janela real: o painel mostra o uso, escolhe-se «E1», as cargas usam 7,5 kN/m² e volta-se ao do projeto. A
    parede curva da nuvem sai com 1,60 m de raio.

## 0.217.0 — 2026-10-25

**A neve** (resto do passo 2 da fase 9).

- **Ações e materiais…** tem dois campos novos: **Neve: zona** e **Altitude do local**.
  - As zonas são as do Anexo Nacional da NP EN 1991-1-3: Z1 (Cz 0,30), Z2 (Cz 0,20) e Z3, os Açores e a Madeira
    (Cz 0,10).
  - A neve no solo é sk = Cz [1 + (H/500)²], com H a altitude. Numa cobertura é s = μ1 · sk, com μ1 = 0,8 para
    coberturas até 30° (desce até 0 aos 60°), Ce = Ct = 1.
  - A cobertura é carregada com a **maior** entre a sobrecarga do seu uso e a neve: a NP EN 1991-1-1 diz que a
    sobrecarga de uma cobertura não se toma junto com a neve. O ψ é o da que manda, e o da neve é 0,5 / 0,2 / 0,0
    (0,7 / 0,5 / 0,2 acima de 1000 m).
  - Ao nível do mar a neve (0,24 kN/m² em Z1) fica abaixo da sobrecarga de uma cobertura não acessível (0,4), por
    isso os projetos já feitos dão o mesmo.
- A janela diz a neve no solo e na cobertura e a carga com que a cobertura fica. A **memória de cálculo** tem uma
  linha da neve.
- Continua a ser pré-dimensionamento; o projeto é do engenheiro.
- Testes:
  - núcleo: sk de 0,30 ao nível do mar e de 1,50 a 1000 m em Z1; 0,10 em Z3; μ1 de 0,8, 0,4 aos 45° e 0 aos 70°;
    ao nível do mar a cobertura fica com a sua sobrecarga; a 1000 m fica com 1,2 kN/m² e o ψ da neve; acima de
    1000 m, os ψ mais altos; os pisos não mudam;
  - janela real: com a altitude de 1000 m, a laje de cobertura de 24 m² fica com 28,8 kN de sobrecarga, a janela
    fala da neve e a altitude fica guardada no IFC.

## 0.216.0 — 2026-10-25

**Splats a partir da nuvem de pontos** (resto do passo 3 da fase 8, a parte que não precisa de treino).

- **Gaussian splat** (separador Render) passa a poder levar as **nuvens de pontos ligadas**. Com nuvens à vista, o programa
  pergunta se as junta.
  - Cada ponto da nuvem vira um splat redondo (uma nuvem não tem faces) com a cor do ponto, ou cinzento quando a
    nuvem não tem cores.
  - A nuvem é desbastada para um ponto por cada célula da distância escolhida (8, 5 ou 3 cm).
  - Vai no mesmo ficheiro PLY do modelo, com Y para cima, para os visualizadores de splats (SuperSplat,
    PlayCanvas…).
  - Uma nuvem ligada sem modelo também se exporta sozinha.
- Os splats a partir de **fotografias** continuam por fazer: precisam de treino com placa gráfica.
- Testes:
  - IFC: uma grelha de 1 cm de 1 × 1 m dá 400 splats a 5 cm, redondos, da cor dos pontos e com Y para cima;
    cinzentos sem cores; num ficheiro com o modelo, e sozinhos;
  - janela real: a sala digitalizada ligada e exportada com as nuvens; sem elas (e sem modelo) a exportação é
    recusada.

## 0.215.0 — 2026-10-25

**Paredes curvas a partir da nuvem** (resto do passo 2 da fase 8).

- O **Modelo a partir da nuvem…** passa a encontrar **paredes curvas** na fatia da nuvem.
  - Primeiro procuram-se os arcos de círculo onde os pontos estão (raio de 0,8 a 40 m, pelo menos 1 m de comprimento
    e 12° de volta). Cada círculo é afinado aos seus pontos, e os arcos separam-se onde os pontos deixam um vazio.
  - Os pontos dos arcos saem antes de se procurarem as retas. Antes, uma parede curva virava uma série de retas
    curtas (as suas cordas).
  - Dois arcos à volta do mesmo centro, a uma espessura de parede, são as duas faces de uma parede curva.
  - Um arco sozinho (uma fachada curva vista só de dentro) é uma parede com a espessura «vista de um lado», para
    fora: para o lado onde não há pontos.
  - A janela diz quantas paredes são curvas e desenha-as a azul. O **OK** faz paredes curvas de verdade, também
    quando são vários pisos de uma vez.
- Testes:
  - núcleo: numa fatia com uma parede curva (faces a 3,0 e 3,2 m, um quarto de volta) e uma reta, saem os dois arcos
    e tiram-se antes das retas; a reta dá uma parede de 20 cm e a curva uma de 3,1 m de raio com 20 cm. Uma fachada
    curva vista de dentro dá uma parede de 30 cm para fora. As paredes retas de uma sala simples não dão arcos;
  - janela real: uma sala digitalizada com uma parede curva lá dentro dá uma parede curva de 1,6 m de raio.

## 0.214.0 — 2026-10-25

**Vários pisos de uma vez a partir da nuvem** (resto do passo 2 da fase 8).

- O **Modelo a partir da nuvem…** passa a ver os **pisos** da nuvem.
  - Um piso é um chão e, pelo menos 2 m acima, o seu teto. O chão do piso de cima é a altura seguinte à espessura de
    uma laje (8 cm a 1 m) acima do teto de baixo. Os tampos de mesas pelo meio não contam.
  - Com dois ou mais pisos, aparece marcada a caixa nova **Todos os pisos de uma vez**, com quantos são e as cotas
    dos chãos. A cota do chão e a altura vêm já as do piso de baixo.
  - Cada piso lê as suas paredes e vãos (0.213) na sua própria fatia, e a janela diz em quantos pisos estão.
  - Ao **OK**, cada piso fica com o pavimento do projeto a essa cota, ou com um pavimento novo («Piso 1»), e com as
    suas paredes, portas, janelas e laje. Fica tudo num só passo de desfazer.
  - Desmarcando a caixa, faz-se só o piso da cota e da altura escritas, como antes.
- Testes:
  - núcleo: das alturas de uma sala só sai um piso; de duas salas sobrepostas, com um tampo de mesa pelo meio, saem
    dois pisos de 2,80 m (o de cima a 3,05); sem o teto do último piso, só os de baixo; de uma nuvem de duas salas,
    as alturas e os dois pisos;
  - janela real: duas salas digitalizadas uma sobre a outra; a caixa vem marcada, com quatro paredes em cada piso;
    o OK faz o pavimento a 3,05, oito paredes e duas lajes, e Ctrl+Z tira tudo.

## 0.213.0 — 2026-10-25

**Os vãos lidos na nuvem de pontos** (resto do passo 2 da fase 8).

- O **Modelo a partir da nuvem…** passa a encontrar as **portas e janelas** nas paredes que encontra.
  - Em cada parede, olha-se para os pontos na sua espessura. Onde, entre 1,15 e 1,45 m sobre o chão, não há pontos
    ao longo de 50 cm ou mais, há um vão.
  - É **porta** quando os pontos faltam até ao chão. É **janela** quando há parede por baixo: o peitoril fica onde
    esses pontos acabam.
  - O alto do vão fica onde os pontos voltam por cima, a padieira. Se não voltam até ao teto, fica a altura de
    sempre (porta 2,10 m, janela 1,20 m).
  - As pontas medem-se nos últimos pontos de cada lado, não na grelha.
  - Um vazio na ponta de uma parede é uma esquina, não um vão, e fica de fora.
  - A janela diz quantas portas e janelas encontrou. O **OK** põe-nas nas paredes, do tipo das suas medidas, no
    mesmo passo de desfazer, e a mensagem final conta-as.
- Testes:
  - núcleo: uma parede de 6 m digitalizada dos dois lados, com o vão de uma porta (2,0 a 2,9 m, até 2,10 m) e o de
    uma janela (4,0 a 5,2 m, de 1,00 a 2,20 m), dá uma porta de 90 × 210 e uma janela de 120 × 120 com peitoril de
    1,00; um vazio na ponta e um buraco estreito não contam;
  - IFC: a mesma parede dá a parede, a porta e a janela no sítio e à altura certa, com o IFC válido;
  - janela real: a sala digitalizada com uma porta na parede do meio; a janela diz a porta e o OK fá-la.

## 0.212.0 — 2026-10-25

**A altura dos vãos lida dos textos do desenho** (resto do passo 1 da fase 8).

- No **Modelo a partir do desenho…**, as portas e janelas dos blocos passam a ler as medidas escritas ao lado delas
  no desenho.
  - Lê-se o texto mais perto do vão, até 1,5 m do seu meio, e cada texto serve um só vão.
  - Formas reconhecidas: «0,90×2,10», «90x210», «P1 0.80 x 2.00», «1,20x1,10 / 1,00», «J2 1,20x1,10 pt 1,00»,
    «1200x1100 peitoril 900», «h=2,20».
  - O primeiro número é a largura e o segundo a altura. O peitoril vem depois de «/», «pt», «ptr», «peitoril» ou
    «parapeito».
  - Os valores podem estar em metros, centímetros ou milímetros (pelo tamanho dos números).
  - A largura continua a ser a do bloco na parede. A altura (e o peitoril das janelas) passam a ser os escritos: o
    vão fica com um tipo dessas medidas («Porta 90×220», «Janela 120×110 (peitoril 0,95)»), do projeto ou novo.
  - A janela diz quantos vãos tinham as medidas escritas.
  - Sem texto ao lado, fica como antes: porta com 2,10 m, janela com 1,20 m sobre um peitoril de 1,00 m.
- Testes:
  - núcleo: as medidas lidas em m, cm e mm, com e sem peitoril; «Sala» e «PT1» não são medidas; cada vão fica com
    o texto mais perto, uma vez, até ao alcance;
  - IFC: a porta com «0,90x2,20» ao lado fica com 2,20 m; a janela com «1,20x1,10 pt 0,95» fica com 1,10 m sobre
    0,95 m; o IFC é válido;
  - janela real: o mesmo desenho, a janela a dizer as duas medidas lidas e os vãos com as alturas escritas.

## 0.211.0 — 2026-10-25

**Pilares a partir do desenho** (resto do passo 1 da fase 8).

- **Modelo a partir do desenho…** tem uma lista nova de camadas: **Pilares (retângulos e círculos)**.
  - Vêm marcadas as camadas cujo nome fala de pilares (PILAR, COLUNA, COLUMN, ESTRUTURA…), ou as da última vez.
  - Nessas camadas, cada retângulo fechado (quatro cantos em esquadria) e cada círculo com tamanho de pilar
    (lados ou diâmetro entre 12 cm e 1,20 m) é um pilar. Servem as polilinhas fechadas e os círculos, também dentro
    de blocos.
  - O pilar fica no meio do desenho, rodado como o retângulo, e com a altura das paredes da janela.
  - O tipo é o da secção desenhada: o do catálogo ou do projeto com essas medidas (um 50 × 20 é o 20 × 50 rodado um
    quarto), senão um novo de betão («Pilar de concreto 35×35», «Pilar circular Ø40»).
  - A janela diz quantos pilares encontrou e desenha-os a azul. O **OK** faz tudo no mesmo passo de desfazer.
  - Um pilar desenhado duas vezes (o contorno e o da trama) conta uma vez. Retângulos compridos (o contorno de uma
    parede), pequenos demais, tortos, ou círculos grandes ficam de fora.
- Testes:
  - núcleo: um retângulo de 30 × 50 rodado 30°, um círculo de 30 cm e um retângulo desenhado duas vezes dão três
    pilares, com o meio, o rumo e as medidas certas; os compridos, os pequenos, os tortos e os círculos grandes não
    contam;
  - IFC: um retângulo de 50 × 20 e um círculo de 30 cm num DXF dão um pilar do tipo 20 × 50 rodado e um do tipo
    circular Ø30, à altura pedida, num só passo de desfazer, com o IFC válido;
  - janela real: três pilares de um DXF, a camada marcada pelo nome e a janela a dizê-lo.

## 0.210.0 — 2026-10-25

**Paredes curvas a partir do desenho (arcos duplos)** (resto do passo 1 da fase 8).

- **Modelo a partir do desenho…** passa a encontrar também as **paredes curvas**: dois arcos à volta do mesmo
  centro, afastados entre as espessuras mínima e máxima da janela.
  - Servem os ARC, os CIRCLE (uma parede redonda inteira) e os lados curvos das polilinhas (os «bulges»), também
    dentro de blocos.
  - O eixo fica a meio dos dois arcos e a espessura é a distância entre eles. Quando os arcos só estão lado a lado
    num pedaço, a parede é esse pedaço.
  - A janela diz quantas paredes curvas há («Destas, 1 curvas (arcos duplos).») e desenha-as a azul como as outras.
  - Ao **OK**, fazem-se paredes curvas de verdade (como as da ferramenta Parede em arco), do tipo da sua espessura e
    ligadas pelas pontas às retas, no mesmo passo de desfazer.
- Antes, os arcos eram partidos em bocadinhos de reta e saíam paredes facetadas (ou nada). Agora as paredes retas
  procuram-se só nas linhas retas.
- As portas e janelas dos blocos continuam a ir só para as paredes retas.
- Testes:
  - núcleo: os arcos lidos como arcos (o meio círculo de uma polilinha, o círculo) e as retas à parte; dois arcos
    de 3 e 3,2 m dão uma parede de 3,1 m com 20 cm; dois círculos dão uma parede redonda; arcos só em parte lado a
    lado dão o pedaço comum, também a passar pelos 0°; centros diferentes ou afastados demais, nada;
  - IFC: um DXF com uma parede reta que continua numa curva dá as duas paredes, a curva com 3,1 m de raio, 90° e
    20 cm, num só passo de desfazer, com o IFC válido;
  - janela real: o mesmo DXF ligado; a janela diz a parede curva e o OK faz as duas paredes.

## 0.209.0 — 2026-10-25

**Recortar a imagem de fundo** (último resto do passo 2 da fase 7).

- Em **Visualizar ▸ Imagens de fundo…**, dois botões novos:
  - **Recortar**: o diálogo fecha e aparece o contorno inteiro da imagem. Dois cliques em cima dela, nos cantos da
    parte que fica: o resto deixa de se desenhar.
  - **Inteira**: mostra outra vez a imagem toda.
- O recorte vale para as imagens deitadas e para as de pé numa fachada (0.208). Vale no ecrã, no papel (folhas,
  PDF: a imagem é cortada ao pedaço que fica) e no DXF (o contorno é o do pedaço).
- O recorte guarda-se com o projeto. Cada recorte é um passo de desfazer, e a parte cortada continua no ficheiro
  da imagem (nada se perde).
- Os cliques na imagem (Calibrar, Recortar) só contam na parte que se vê.
- Testes:
  - núcleo: uma imagem de 10 × 5 recortada pelo meio (cantos a 20 %/20 % e 70 %/80 %, por qualquer ordem) mostra a
    parte certa, com as coordenadas da fotografia certas; um ponto fora deixa de estar nela; guardar e ler; estreita
    demais, nada; numa fachada, também recortada;
  - IFC: a planta leva o contorno inteiro (para a fotografia) e a parte que fica (para a cortar); o DXF leva só a
    parte;
  - janela real: dois cliques numa imagem vista de cima deixam a parte entre eles, no ecrã e no papel.

## 0.208.0 — 2026-10-25

**Uma imagem numa fachada** (resto do passo 2 da fase 7).

- Em **Visualizar ▸ Imagens de fundo…**, o botão novo **Pôr numa fachada** põe a imagem escolhida de pé numa face do
  modelo, por exemplo a fotografia de uma fachada existente sobre a parede.
  - O primeiro clique é na face, onde fica o canto de baixo à esquerda.
  - O segundo é onde fica o canto de baixo à direita, ou escreve-se a largura + Enter.
  - A largura é a distância entre os dois cliques; a altura segue as proporções da fotografia; o pé fica à altura
    do primeiro clique.
  - A imagem lê-se do lado para onde a face olha: os cliques podem ser da esquerda para a direita ou ao contrário.
  - Faz-se num só passo de desfazer, e a imagem fica guardada com o projeto («de pé» e a altura do pé).
- A imagem de pé aparece no 3D e nos alçados, encostada à face. Também vai para o papel (folhas, PDF) dos alçados e
  cortes que a veem de frente (0.207), e para o DXF deles, como contorno com o nome.
- Uma imagem de pé não se calibra com **Calibrar**: para a mudar, põe-se outra vez na fachada.
- Testes:
  - núcleo: de pé entre (2; 0; 3,5) e (8; 0; 3,5) num pavimento a 3 m, fica com 6 m de largura, 3 m de altura e o pé
    a 0,5 m, lida de sul; ao contrário, igual; guardar e ler; um só ponto, nada;
  - IFC: a fotografia na face sul de uma parede está no alçado sul com 6 × 3 m, lida da esquerda para a direita, e
    não está no alçado norte nem na planta;
  - janela real: «Pôr numa fachada» com dois cliques na parede vista de sul.

## 0.207.0 — 2026-10-25

**A imagem de fundo nas folhas e no DXF** (resto do passo 2 da fase 7).

- **No papel** (folhas, PDF, impressão): as imagens de fundo visíveis do pavimento passam a ir com a planta.
  - Ficam por baixo de tudo, com a sua opacidade, rodadas e à escala como no ecrã.
  - São recortadas ao desenho: nunca saem para cima das outras vistas da folha, nem o fazem maior.
  - Para a imagem ficar só no ecrã, esconde-se em **Imagens de fundo…** (a caixa «Visível»).
  - Uma imagem que já não está onde estava (ficheiro mudado ou apagado) não aparece; o resto desenha-se.
- **No DXF**: o DXF R12 não tem imagens. Vai o contorno da imagem, na camada nova IMAGENS, com o nome do ficheiro no
  canto, para se pôr lá a imagem no programa de CAD.
- Testes:
  - IFC: a planta leva a imagem visível do pavimento, com os seus cantos e opacidade, e não leva a escondida nem a
    de outro pavimento; o DXF tem a camada IMAGENS e o nome do ficheiro;
  - janela real: uma imagem vermelha debaixo de duas paredes aparece no papel e o PDF sai; escondida, desaparece.

## 0.206.0 — 2026-10-25

**Offset de faces côncavas e Escala a partir do centro** (restos do passo 1 da fase 7).

- **Offset** numa face côncava (em L, em U…):
  - para dentro, a face divide-se: fica o L interior e, à volta, uma moldura com uma face de quatro lados por cada
    lado da face (as arestas que ligam os cantos ficam escondidas);
  - para fora, numa face sozinha, o L cresce e o antigo fica lá dentro;
  - antes só funcionava em faces convexas (retângulos, círculos, polígonos regulares);
  - uma distância que muda a forma da face (fecha um braço do L, ou parte-a em duas) é recusada, com uma mensagem
    que o diz.
- **Escala a partir do centro**, como o Ctrl do SketchUp:
  - na ferramenta **Escala**, tocar em Ctrl (ou marcar **A partir do centro** na barra de cima) faz a escala a
    partir do meio da seleção;
  - digita-se o fator (por exemplo 2) e Enter, ou clica-se num ponto da seleção e depois onde ele vai;
  - com Ctrl carregado no primeiro clique, faz o mesmo só dessa vez;
  - tocar outra vez em Ctrl volta ao ponto base.
- Testes:
  - núcleo: um L com offset de 0,25 fica o L interior (5,75 m²) e seis faces de moldura, com as áreas a somar e
    todas viradas para o mesmo lado; para fora, o L crescido; um offset que fecha o braço é recusado e a malha fica
    como estava; uma caixa escalada a partir do meio fica com o meio no mesmo sítio;
  - janela real: o Offset num L e a Escala com Ctrl.

## 0.205.0 — 2026-10-25

**Rampas de acesso entre plataformas** (último resto da topografia, fase 7, passo 3).

- Ferramenta nova **Rampa de acesso**, no separador **Terreno**.
  - Faz-se com dois cliques: onde a rampa começa e onde acaba (o meio de cada ponta), por exemplo na borda de uma
    plataforma e na borda de outra.
  - Na barra de cima escolhe-se a **largura** (2,50 a 6,00 m) e os taludes de escavação e de aterro, como nas
    plataformas.
  - A cota de cada ponta é a do terreno nesse ponto, isto é, a da plataforma, quando a ponta está numa.
  - Ao longo da rampa, a cota vai de uma ponta à outra por igual. A rampa é um plano inclinado, com os seus taludes
    à volta, até ao terreno.
  - Enquanto se desenha, a barra de baixo diz as cotas das pontas, o comprimento e a inclinação («De 1,00 a 3,00,
    12,00 de comprimento: 16,7 %»). No fim diz também o desaterro e o aterro.
- Na planta, a rampa tem o contorno inclinado e o texto «+1,00 / +3,00 · 16,7 %». Os taludes e os traços (0.203)
  seguem a cota de cada ponto da rampa.
- A rampa fica guardada no terreno, com as plataformas, e o **Editar plataforma** (0.204) também lhe muda os cantos.
- **A topografia (fase 7, passo 3) fica sem restos.**
- Testes:
  - núcleo: o contorno da rampa; a cota ao longo dela; o terreno proposto em cima e nos taludes de aterro ao lado;
    o pé do aterro, que se afasta à medida que a rampa sobe; guardar e ler;
  - IFC: duas plataformas (11 e 13 m) e a rampa entre elas, com as pontas às cotas delas, 12 m a meio, o texto na
    planta e o IFC válido; desfazer tira-a; rampa curta demais ou fora do terreno é recusada;
  - janela real: os dois cliques, a inclinação dita enquanto se desenha, a rampa feita de 1,00 a 3,00 e o terreno a
    2,00 a meio.

## 0.204.0 — 2026-10-25

**Editar o contorno de uma plataforma já feita** (resto da fase 7).

- Ferramenta nova **Editar plataforma**, no separador **Terreno** e na barra de cima quando um terreno está
  selecionado. Antes, para mudar uma plataforma, era preciso apagá-la e fazer outra.
  - Os cantos da plataforma aparecem como pegas, à altura dela, como no «Editar contorno» das lajes:
    - clicar num canto pega-o e outro clique pousa-o (ou escreve-se a distância + Enter);
    - o losango no meio de um lado acrescenta um canto;
    - Delete tira o canto pegado (ficam pelo menos três);
    - o botão direito põe o canto onde estava;
    - Esc volta ao Selecionar.
  - Cada mudança refaz os taludes e o terreno à volta, num só passo de desfazer. A barra de baixo diz o desaterro e
    o aterro de todas as plataformas do terreno.
  - Num terreno com várias plataformas, clica-se dentro da que se quer editar (os contornos de todas aparecem
    na cor da pré-visualização).
- Por baixo (`bim.set_platform`) também se pode mudar a cota da plataforma.
- Testes:
  - IFC: um canto movido 3 m põe o terreno plano à cota da plataforma na parte nova; a cota muda; cada mudança
    desfaz-se de uma vez; o IFC é válido;
  - janela real: o terreno selecionado mostra **Editar plataforma**, aparecem as quatro pegas, um canto é levado
    3 m para nascente e o terreno fica plano ali; Esc volta ao Selecionar.

## 0.203.0 — 2026-10-25

**O pé dos taludes na planta** (resto da fase 7).

- Os taludes à volta das **plataformas** passam a desenhar-se na planta, como numa planta de implantação:
  - **a linha onde o talude encontra o terreno**:
    - a crista do desaterro, do lado onde o terreno está mais alto;
    - o pé do aterro, do lado onde está mais baixo;
  - **os traços de talude**: perpendiculares aos lados da plataforma, um comprido e um curto, a cada metro. Saem
    sempre do alto do talude:
    - no desaterro, da crista para a plataforma;
    - no aterro, da borda da plataforma para o pé.
- Onde a plataforma assenta no terreno não há talude e não se desenha nada.
- Aparecem:
  - no ecrã, na planta e na vista 3D (sobre o terreno, à altura certa);
  - no papel (folhas, PDF, impressão), em traço fino;
  - no DXF, na camada nova TALUDES.
- As linhas calculam-se a partir do terreno levantado, sem as plataformas: é onde o terreno encontra a inclinação do
  talude de cada plataforma (1:1 no desaterro e 2:3 no aterro, ou as que se escolheram).
- Testes:
  - núcleo: uma plataforma num terreno que sobe para nascente, com a crista onde o talude 1:1 encontra o terreno
    (2,22 m) e o pé onde o 2:3 o encontra (2,35 m); os traços saem do alto do talude, compridos e curtos; num terreno
    plano à altura da plataforma, nada;
  - IFC: a planta com as linhas dos dois lados e o DXF com a camada TALUDES; sem plataformas, nada;
  - janela real: as linhas no ecrã e no papel.

## 0.202.0 — 2026-10-25

**O valor escrito nas curvas mestras** (resto da fase 7).

- As **curvas mestras** passam a ter a sua cota escrita: «15», «12,5», sem «m» nem sinal, como nas cartas. São as
  mais grossas, uma em cada cinco.
- **No papel** (folhas, PDF, impressão):
  - o número segue a curva, rodado para se ler de baixo ou da direita;
  - vai sobre a curva, com um contorno branco que a interrompe;
  - aparece uma vez em cada 12 cm de curva no papel, pelo menos uma em cada troço com 2,5 cm ou mais;
  - os números ficam com 1,8 mm de altura, à escala da vista.
- **No DXF**: os números vão na camada CURVAS_MESTRAS, rodados como no papel.
- **No ecrã**: o número aparece sobre a curva (na vista 3D e na planta), um em cada 20 m de curva.
- Testes:
  - núcleo: o texto da cota; os segmentos de uma curva, baralhados, juntos numa só linha (fechada à volta de um
    morro); os números espalhados ao longo dela, rodados para se lerem, nenhum num troço curto;
  - IFC: no DXF, a curva mestra dos 15 m tem «15» na sua camada e as outras não;
  - janela real: os números no ecrã e o papel pintado.

## 0.201.0 — 2026-10-25

**Cores de inclinação nas folhas, com a legenda** (resto da fase 7).

- **Inclinações do terreno** (separador Terreno) passa a ser uma propriedade da vista onde se liga.
  - Cada vista lembra-se dela, e ela fica gravada com o projeto.
  - Com nada selecionado, o painel **Propriedades** da vista tem a caixa **Cores de inclinação do terreno**.
  - A vista 3D tem a sua, e cada planta a sua.
- **No papel**: uma planta com as cores ligadas leva-as para as folhas, para o PDF (**Exportar vista em PDF…**, Ctrl+P) e
  para a impressão.
  - As cores são as mesmas do ecrã, por faixas de inclinação: até 5 %, 5 a 10 %, 10 a 15 %, 15 a 25 % e mais de
    25 %.
  - Ficam um pouco transparentes, por baixo das curvas de nível, das plataformas e do resto do desenho.
  - Mostram só o terreno abaixo do plano de corte da planta e respeitam a região de recorte.
  - No canto inferior esquerdo do desenho fica uma **legenda**: «Inclinação do terreno», com uma linha por cada
    faixa que aparece.
- O DXF não leva as cores (fica para quando houver tramas sólidas no DXF).
- Testes:
  - IFC: as faixas cobrem os 600 m² do terreno, uma entrada por faixa (o morro acima de 25 %); o corte e o recorte
    tiram-lhe parte; desligadas, nada; desfazer volta atrás;
  - janela real: ligar na planta, o painel com a caixa marcada, o papel pintado com a legenda, o PDF, a vista 3D com
    a sua (desligada).

## 0.200.0 — 2026-10-25

**Forquilhas a 45° nos esgotos** (resto do passo 1 da fase 6).

- **Ligar à rede**: o ramal de esgoto entra no coletor a 45°, virado para onde o coletor desce, com uma
  **forquilha** (o tê em Y), em vez de entrar em esquadria.
  - O ramal vem direito ao coletor e, a 2 diâmetros + 5 cm dele, vira 45°. Encontra-o esse tanto mais abaixo.
  - Um ramal curto, de um só troço, vai a 45° desde a louça.
  - A pendente de 2 % mantém-se ao longo do caminho todo.
- Fica em esquadria, como antes:
  - num tubo de queda;
  - quando o coletor não tem comprimento para a forquilha;
  - quando um pilar está no caminho do troço a 45°;
  - quando o ramal contornou um obstáculo e o último troço é curto.
- Os ramais de água continuam com tês em esquadria.
- **Nome e tipo próprios**: um tê com o ramal a menos de 60° do coletor chama-se **Forquilha** («Forquilha 1»,
  tipo «Forquilha — Tubo PVC Ø100»). No IFC continua a ser um `IfcPipeFitting` JUNCTION. Também o tubo desenhado à
  mão que acaba oblíquo num coletor leva uma forquilha.
- Testes:
  - IFC: o esgoto de um WC entra no coletor a 45°, 25 cm abaixo do ponto em esquadria; a forquilha está ligada às
    três pontas; a água tem um tê; a pendente é de 2 %; o IFC é válido;
  - janela real: «Ligar à rede» faz a forquilha, e o painel Propriedades mostra-a.

## 0.199.0 — 2026-10-25

**O ramal contorna obstáculos** (resto do passo 3 da fase 6).

- **Ligar à rede**: quando um pilar está entre a louça (ou o aparelho) e o tubo da rede, o ramal contorna-o.
  - Contorna com curvas em ângulo reto: sai para o lado, passa o pilar e volta à linha.
  - Fica a 5 cm da face do pilar (mais o raio do tubo).
  - Escolhe o lado com menos curvas e o caminho mais curto.
  - Cada troço entre duas curvas fica com comprimento para elas.
  - O último troço chega ao tubo da rede (ou à ligação da louça) de frente, por isso o tê fica em esquadria.
- O esgoto debaixo do piso contorna também as **sapatas isoladas** que encontra à sua altura, sempre a descer a 2 %
  ao longo do caminho todo.
- **O que não contorna**:
  - as sapatas corridas e as vigas (atravessa-as, como antes; aí faz-se uma passagem);
  - um obstáculo que obrigue a uma volta mais de 3 m maior do que o caminho direito (aí o ramal vai direito, como
    antes, e a **Deteção de conflitos** mostra o cruzamento).
- Testes:
  - o caminho em planta: direito quando livre; à volta de um pilar com curvas em ângulo reto e o último troço a
    direito; recusado sem lugar para as curvas ou com uma volta grande demais;
  - IFC: um WC com um pilar no caminho da água e uma sapata no do esgoto; nenhum tubo atravessa nenhum dos dois; os
    tês e as curvas estão lá; o IFC é válido;
  - janela real: «Ligar à rede» com um pilar entre o WC e o tubo da água.

## 0.198.0 — 2026-10-25

**Gás e eletricidade nos aparelhos** (resto do passo 3 da fase 6).

- **Gás**:
  - **Ligar à rede** passa a servir também os aparelhos (a placa a gás, a máquina de lavar, a de lavar loiça), e
    não só as louças. Selecione-os (ou nada: todos os do pavimento ativo) e cada ligação livre ganha o seu ramal
    até à rede do seu sistema.
  - Uma placa a gás liga-se ao tubo de gás mais perto com um ramal de cobre Ø15.
  - Tipos novos de tubo: cobre Ø15 e Ø22 para o gás.
  - A ferramenta **Tubo** começa e acaba também nas ligações dos aparelhos (água, esgoto, gás).
- **Eletricidade**:
  - Os aparelhos elétricos (placa, forno, máquina de lavar loiça e de lavar roupa, frigorífico, micro-ondas,
    exaustor) têm agora a ligação de alimentação, junto à base, atrás.
  - A ferramenta **Tubo VD** (condutas elétricas) acaba nessa ligação.
  - **Novo circuito com a seleção** aceita aparelhos. Um aparelho faz um circuito próprio («Máquina», 20 A,
    4 mm²) e conta com a sua potência (placa 7000 W, forno 3500 W, máquinas 2200 W, micro-ondas 1200 W,
    frigorífico 300 W, exaustor 250 W). Estes são valores habituais do programa; o projeto elétrico é do
    engenheiro.
- Testes:
  - IFC: a placa a gás ligada à rede de gás; a ligação de alimentação do forno; o circuito do forno com 3500 W; o
    IFC válido;
  - janela real: «Ligar à rede» com a placa a gás selecionada e «Novo circuito com a seleção» com o forno.

## 0.197.0 — 2026-10-25

**Condutas em S** (o último resto do passo 2 da fase 6).

- Uma conduta (ou um tubo) desenhada até à porta lateral de uma unidade, a uma altura um pouco diferente da da
  porta, já não tenta descer na vertical. Com pouco desnível, as duas curvas de 90° não cabiam e ficavam peças
  sobrepostas. Agora faz um **S**:
  - segue à sua altura até à frente da porta;
  - desce (ou sobe) a 45°, com duas curvas de 45°;
  - entra na porta, nivelada, e fica ligada.
- Faz o S quando o desnível é menor do que duas larguras da conduta mais 10 cm (para a conduta 30×20, menos de
  70 cm). Com mais desnível, desce na vertical como antes.
- Testes:
  - IFC: uma conduta 30×20 que chega com 26,5 cm de desnível faz o S (um troço a 45°, duas curvas, ligada); com
    1,20 m de desnível desce na vertical; o IFC válido;
  - janela real: a ferramenta Conduta desenhada até à porta de retorno de uma unidade de conduta.

## 0.196.0 — 2026-10-25

**Tubagem de refrigerante** (resto do passo 2 da fase 6).

- As unidades de ar condicionado têm agora as portas das duas linhas de refrigerante, **líquido** e **gás**:
  - a interior de parede (split), junto da do condensado, nas costas;
  - a de conduta, junto da do condensado;
  - a exterior, num dos lados.
- Há dois sistemas novos: **Refrigerante — líquido** e **Refrigerante — gás**, cada um com a sua cor.
- Há quatro tipos novos de tubo, em **cobre isolado**: 1/4", 3/8", 1/2" e 5/8" (desenhados com a espessura do
  isolamento).
- Com a ferramenta **Tubo**, uma linha começada numa unidade sai da porta do sistema escolhido (líquido ou gás) e
  fica nesse sistema. Desenhada até à outra unidade, acaba na porta igual e fica ligada.
- Um tubo de outro sistema (o condensado, a água) nunca vai para uma porta de refrigerante, e um de refrigerante
  nunca vai para a do condensado.
- No IFC: as portas são IfcDistributionPort com SystemType REFRIGERATION e o fluxo nos dois sentidos
  (SOURCEANDSINK).
- Testes:
  - IFC: as portas das duas unidades; a linha de líquido em cobre 1/4" de uma à outra, ligada nas duas pontas e
    no seu sistema, com as portas de gás livres; o IFC válido;
  - janela real: as duas unidades postas com a ferramenta e a linha de líquido desenhada com a ferramenta Tubo.

## 0.195.0 — 2026-10-25

**Ramais a outra altura descem sozinhos até ao tubo** (resto do passo 1 da fase 6).

- Na ferramenta **Tubo** (e nas condutas e tubos de esgoto), um troço desenhado até ao eixo de outro tubo que está
  bastante mais acima ou abaixo (mais de 10 cm, ou mais do que o diâmetro) já não desce em rampa até ele:
  - o troço continua à sua altura até ficar por cima (ou por baixo) do outro;
  - daí desce (ou sobe) na vertical até ele, com uma curva no topo;
  - liga-se com um tê virado para cima (ou para baixo), como faz o Revit.
- Tudo isto é **um só passo** de anular.
- Enquanto se desenha, a dica diz quanto vai descer («Desce 2,00 m até este tubo e liga-se com um tê»).
- A uma altura parecida (como os ramais de esgoto com a sua inclinação), liga-se como até aqui.
- Testes: na janela real, um tubo Ø100 a 0,50 m e um ramal Ø50 a 2,50 m desenhado até ele: o troço vertical de
  2,50 m a 0,50 m, o tê ligado, o fim do ramal, um só passo de anular.

## 0.194.0 — 2026-10-25

**Notas-chave** (keynotes, o que faltava no passo 2 da fase 5).

- Cada elemento pode ter uma **nota-chave**: um código e um texto curto para aquilo de que é feito (por exemplo
  «02.03 — Alvenaria de tijolo cerâmico 20 cm»).
  - Escolhe-se nas **Propriedades**, na linha **Nota-chave (do tipo)**.
  - Fica no tipo do elemento, como no Revit: todas as paredes desse tipo passam a tê-la. Um elemento sem tipo
    fica com a sua.
  - A tabela de notas vem com o programa: 34 notas, por capítulos, como num mapa de quantidades (estrutura,
    alvenarias, revestimentos, pavimentos, tetos, coberturas, vãos, serralharias, equipamentos).
- A ferramenta **Desenho 2D** tem a forma **Nota-chave**: um clique no elemento e outro onde fica a etiqueta. A
  etiqueta é uma linha de chamada com uma caixa, que escreve o código do elemento.
  - O código é sempre o do modelo: se a nota do tipo mudar, a etiqueta muda sozinha.
  - Um elemento ainda sem nota mostra «?».
- Nas **Tabelas**, a categoria nova **Notas-chave** é a legenda: cada código usado, a sua descrição e quantos
  elementos o têm. Põe-se numa folha como as outras tabelas.
- No papel (PDF, imagem) e no DXF, a etiqueta sai com a caixa e o código.
- No IFC, a nota é uma IfcClassificationReference da classificação «Notas-chave», no tipo, e os outros programas
  leem-na.
- Testes:
  - IFC: a nota no tipo (a outra parede do mesmo tipo tem-na, uma de outro tipo não); a etiqueta com «?», depois
    com o código, depois com o novo; desfazer; a legenda; o desenho; o IFC válido; gravar e abrir; tirar a nota;
  - janela real: a nota escolhida nas Propriedades; a etiqueta desenhada na planta; a legenda nas Tabelas; a planta
    impressa em PDF.

## 0.193.0 — 2026-10-25

**Tipos de cota** (o que faltava no passo 3 da fase 5: tipos por cota, como os do Revit).

- **Anotar ▸ Estilo das cotas…** passa a ter, em cima, a lista **Tipo**. Nela estão o estilo do projeto e os tipos
  de cota que o projeto tiver. Os campos (tamanho do texto, marca, unidade, casas decimais) são os do tipo escolhido.
  - **Novo tipo**: escreve-se o nome (por exemplo «Cotas de pormenor») e clica-se em **Juntar**. Começa igual ao
    tipo escolhido.
  - **Apagar** tira o tipo escolhido. As cotas desse tipo passam a desenhar-se pelo estilo do projeto.
- Cada cota desenha-se pelo seu tipo (no ecrã, no papel e no DXF); as que não têm tipo, pelo estilo do projeto,
  como até aqui.
- A ferramenta **Cota** tem a opção **Tipo de cota** na barra contextual (quando o projeto tem tipos): as cotas
  novas, e as da cadeia, ficam desse tipo.
- Selecionar cotas mostra-as nas **Propriedades**: o valor (de uma) e o **Tipo de cota**, que se muda ali para
  todas as selecionadas de uma vez (um passo de anular). Se diferem, a lista fica «<vários>».
- Os tipos guardam-se com o estilo das cotas, no ficheiro ao lado do IFC.
- Testes:
  - IFC: um tipo «Pormenor» (centímetros, setas, 3,5 mm); uma cota desse tipo («450») e outra do projeto
    («4,50») no desenho, cada uma com a sua marca e texto; mudar o tipo e desfazer; um tipo que já não existe;
    gravar e abrir;
  - janela real: o tipo novo juntado na janela do estilo; uma cota desenhada com esse tipo («400»); nas
    Propriedades, mudada para o estilo do projeto, e o Ctrl+Z.

## 0.192.0 — 2026-10-25

**Marcas de nível nas plantas** (passo 2 da fase 5).

- A ferramenta **Desenho 2D** tem uma forma nova, **Marca de nível**: um clique na planta põe o símbolo usado nos
  desenhos portugueses (um círculo dividido em quatro, com dois quartos pretos) e escreve ao lado a cota do que
  está por baixo («+0,30», «±0,00»).
- Como a cota de nível (0.156), a cota é sempre a do modelo: se a laje ou o terreno mudar de altura, a marca
  muda sozinha. Fora de qualquer laje, escreve a cota do pavimento.
- Sai no papel (PDF, imagem, com os quartos preenchidos) e no DXF (o círculo, os quartos e a cota).
- Selecionada, mostra a pega no seu ponto (0.191): arrastá-la leva a marca e a cota é lida no sítio novo.
- Correção: uma folha passa a refazer a vista quando muda o tamanho, o ângulo ou o tipo de linha de um desenho
  2D. Antes, só refazia quando mudavam os pontos, o texto ou a trama.
- Testes:
  - IFC: uma marca sobre uma laje e outra fora; a laje subida 30 cm e a marca a acompanhar; o desenho (o círculo,
    os diâmetros e os dois quartos) e o DXF;
  - janela real: a marca desenhada sobre uma laje, com a cota da laje, os quartos preenchidos no ecrã e a planta
    impressa em PDF.

## 0.191.0 — 2026-10-25

**Editar os desenhos 2D** das vistas (o que faltava no passo 1 da fase 5).

- Uma linha, polilinha, retângulo, círculo, arco, região ou texto desenhado numa vista, quando selecionado,
  mostra uma **pega azul em cada ponto** (as pontas de uma linha, os cantos, o centro e um ponto de um círculo, o
  início de um texto).
  - Arrastar uma pega (ou clicar nela e depois onde a quer) leva esse ponto, no papel da vista, com os snaps.
  - Pode escrever a distância e carregar em Enter.
  - Esc deixa-o como estava; Ctrl+Z desfaz.
- As **Propriedades** mostram o desenho selecionado:
  - um texto: as palavras, o tamanho e o ângulo, todos editáveis;
  - uma região: a trama e a área;
  - uma linha: o comprimento (escrever um novo estica-a a partir do início);
  - um círculo: o raio;
  - tudo exceto os textos: o tipo de linha e a espessura.
- O **Rodar** passa a rodar desenhos 2D numa planta. Um texto rodado fica com o novo ângulo.
- O ângulo dos textos sai no papel (PDF, imagem) e no DXF.
- Testes:
  - modelo: mudar uma ponta e desfazer; mudar as palavras, o tamanho, o ângulo e a trama; rodar 90° (o ângulo do
    texto acompanha) e desfazer; o ângulo guardado e lido; no desenho e no DXF;
  - janela real: uma linha e um texto numa planta; as duas pegas da linha, uma arrastada; o comprimento escrito;
    as palavras e o ângulo do texto; a linha rodada 90° e o Ctrl+Z.

## 0.190.0 — 2026-10-25

**Coberturas de quatro águas sobre qualquer contorno** (o que faltava no passo 5 da fase 4: os contornos de lados
oblíquos).

- Uma cobertura de quatro águas faz-se agora sobre qualquer contorno: com cantos para dentro e lados em qualquer
  ângulo (um L torto, um T, uma casa com uma ala em viés, uma estrela…). Antes, só sobre contornos convexos ou com
  os lados em esquadria.
- As águas saem do **esqueleto reto** do contorno. É o que fazem os beirados a subir todos juntos à mesma
  inclinação: onde se encontram nascem os rincões, os larós e as cumeeiras. Há uma água por lado do contorno, sem
  folga nem sobreposição.
- As paredes ligadas por baixo a uma cobertura destas sobem até ela, como nas outras.
- Contornos convexos e contornos em esquadria fazem-se como antes, com as mesmas águas.
- A cobertura de duas águas sobre um contorno com cantos para dentro continua a não se fazer; a mensagem diz agora
  que se faz de quatro águas ou plana.
- Testes:
  - núcleo: o esqueleto de retângulos, L, T, cruz, estrela e contornos oblíquos (uma água por lado, a altura igual
    vista de cada água); sobre um contorno convexo, as mesmas águas de antes; a altura numa água;
  - IFC: uma cobertura de quatro águas sobre um L de lados oblíquos, com o volume certo, e uma de duas águas
    recusada;
  - janela real: a ferramenta Cobertura com quatro águas clicada dentro de uma casa em L de lados oblíquos.

## 0.189.0 — 2026-10-25

**Cantos com paredes curvas** (o que faltava no passo 3 da fase 4: as curvas ainda não faziam cantos).

- Uma parede curva cuja ponta fica na ponta de outra parede (reta ou curva) **junta-se a ela sozinha**, como as
  retas entre si. Acontece ao desenhar a curva a partir da ponta de uma parede, e também ao desenhar uma parede
  reta até à ponta de uma curva.
- O canto é **exato**: as duas paredes são cortadas pela mesma linha, que passa pelo ponto onde as faces de dentro
  se encontram e pelo ponto onde as faces de fora se encontram. A face curva entra pelo que é, e não pela sua
  tangente. Não fica folga nem sobreposição; os volumes e as áreas das salas ficam certos.
- Para isso, cada parede vai até onde o seu eixo cruza essa linha (a reta estica ou encurta um pouco; a curva
  abre ou fecha um pouco). As portas e janelas da curva ficam onde estavam.
- Uma curva que continua a direção da reta (tangente) já encontra a reta em esquadria: não se junta.
- O canto **refaz-se** quando muda a espessura de uma das paredes, quando se movem e quando se espelham. Mudar o raio
  ou a abertura da curva solta-a do canto, como esticar uma parede reta.
- No IFC, o canto fica registado como os das retas (IfcRelConnectsPathElements); a curva guarda o corte de cada
  ponta (CorteInicio e CorteFim, como as retas).
- Ferramenta **Parede**, formas Arco, Círculo e Retângulo: o primeiro ponto fica no nível do pavimento, como já
  acontecia na forma Linha. Antes, um arco começado na ponta de outra parede ficava no topo dela.
- Testes:
  - núcleo: o canto exato entre uma reta e uma curva (os cantos de uma são os da outra, também na planta das
    salas); uma curva tangente não se junta; duas curvas;
  - IFC: reta e curva juntas sozinhas, sem folga; a reta mais fina; as duas espelhadas; duas curvas; uma reta
    desenhada até à ponta de uma curva; desfazer;
  - janela real: o arco desenhado com a ferramenta Parede e uma reta desenhada até à sua ponta, juntas, com o
    canto exato.

## 0.188.0 — 2026-10-25

**Fachada de vidro embutida numa parede** (o que faltava no passo 7 da fase 4, como o «Embutir automaticamente» do
Revit).

- Uma fachada desenhada dentro de uma parede reta (ao longo dela, entre as faces, sem passar das pontas nem do
  topo) **abre o seu vão na parede**. No IFC, é um vão que corta a parede e que a fachada preenche, como uma porta.
- Enquanto se desenha, a dica diz em que parede vai ficar embutida; no fim, a barra de baixo confirma.
- Embutida, a fachada **comporta-se como uma porta**:
  - vai com a parede quando esta se move, se copia, se espelha ou se divide (cada parte fica com a sua);
  - sozinha, com o Mover, desliza ao longo da parede; com Ctrl, copia-se ao longo dela;
  - selecionada, mostra as cotas temporárias até às pontas da parede;
  - apagar a parede apaga também o que está nela.
- Mudar o comprimento ou a altura da fachada ajusta o vão. Se a fachada passasse a sair da parede, a mudança é
  recusada.
- Mudar a espessura da parede refaz o vão através da nova espessura; a fachada fica como estava.
- **Propriedades** da fachada:
  - **Embutida na parede** (uma caixa): desmarcada, a parede fica inteira e a fachada fica onde está; marcada de
    novo, volta a cortá-la;
  - com a fachada embutida, **Parede** e as distâncias ao início e ao fim da parede (escrever uma desliza-a).
- Uma fachada desenhada fora de uma parede e depois movida para dentro de uma embute-se sozinha.
- As fachadas dos projetos antigos não mudam: só as novas se embutem.
- Testes:
  - IFC: o vão e o volume da parede; deslizar; mais comprida, e comprida demais (recusada); a parede movida,
    espelhada e mais fina; desligar e ligar; uma fachada movida para dentro da parede; uma cópia ao longo dela; a
    parede dividida; a parede apagada; o IFC válido em cada passo;
  - janela real: a ferramenta Fachada sobre o eixo de uma parede, com a dica e o comprimento escrito; o vão; as
    Propriedades; deslizar para 1 m do início; desembutir e Ctrl+Z.

## 0.187.0 — 2026-10-25

As **Propriedades** com vários elementos selecionados (o que ficou para depois na etapa 4 da interface).

- Em cima, quantos são e de que categorias (por exemplo, «4 objetos selecionados / Paredes, Pilares»).
- Quando são de mais de uma categoria, a lista **Elementos** deixa escolher: **Todos (4)**, **Paredes (3)**,
  **Pilares (1)**…
  - Com todos, aparecem as propriedades que todos têm, como a fase.
  - Com uma categoria, as dessa categoria.
  - Uma categoria com um só elemento mostra-o como se estivesse selecionado sozinho.
- As propriedades em comum:
  - um valor igual em todos mostra-se;
  - um valor que difere fica em branco, com «<vários>» (uma caixa de marcar fica meio marcada).
- Mudar uma propriedade muda-a em **todos** de uma vez, mesmo que um deles já tivesse esse valor. É **um só
  passo** de anular: o Ctrl+Z desfaz em todos.
- Ficam de fora o nome e a marca (um para cada elemento), o GlobalId e os botões que trabalham sobre um só
  elemento (editar o perfil, o contorno, o tipo).
- Com mais de 150 elementos, ou com esboços na seleção, o painel pede que se escolha uma categoria na lista.
- Testes:
  - IFC: a altura de três paredes num passo; desfazer e refazer em todas;
  - janela real: três paredes e um pilar; a lista; as propriedades comuns de todos; as das paredes, com a altura
    igual e o comprimento «<vários>»; a altura 3,20 m nas três num passo, e o Ctrl+Z; o comprimento escrito sobre
    «<vários>» nas três; a fase nas três; o pilar sozinho.

## 0.186.0 — 2026-10-25

Interface nova, quinta etapa: o **rodapé** (painel 8). Da esquerda para a direita:

- **Estado**: a dica da ferramenta e as mensagens, como antes.
- **Pavimento ativo**: passou a ser um botão. Um clique lista os pavimentos, o mais alto em cima e o ativo
  marcado; escolher outro passa a desenhar nele. No fim da lista, «Pavimentos…» abre o painel dos pavimentos.
- **Medidas** e **navegação**, como antes.
- **Orientação** (o cubo): a vista inicial, as vistas de cada lado (topo, frente, trás, esquerda, direita) e as
  quatro isométricas (sudeste, sudoeste, nordeste, noroeste).
- **Estilo gráfico** da vista 3D (sombreado, linhas escondidas, arame, raio-X). O ícone mostra o estilo atual.
  Nas plantas e nos cortes fica apagado, porque estes desenham-se a linhas.
- **Escala** da planta, do corte ou do alçado nas folhas (1:50, 1:100…). Fica apagada quando o modelo de vista
  da vista a fixa, e no 3D.
- **Grelha do chão** da vista 3D: ligar e desligar.
- **Unidades**: metros, centímetros ou milímetros.
  - Mudam o que se mostra: a caixa de medidas, as cotas temporárias, as Propriedades e a barra contextual.
  - Mudam também como se lê um número escrito sem unidade: em centímetros, «320» é 3,20 m. Um número com a
    unidade escrita («3,2m») lê-se sempre assim.
  - Ficam guardadas para a próxima vez.
  - As cotas dos desenhos seguem o seu estilo de cotas. As tabelas e as cotas dos pavimentos ficam em metros.
- Cada mudança de estilo, escala ou grelha é um passo que o Ctrl+Z desfaz, como nas Propriedades.
- Testes:
  - unidades: centímetros (ao milímetro), milímetros, a leitura dos números sem unidade, as tabelas sempre
    em metros;
  - janela real: o rodapé visível; linhas escondidas e Ctrl+Z; a grelha desligada e ligada; a isométrica
    nordeste, a vista de trás e a vista inicial; na planta, o estilo e a grelha apagados e a escala 1:50; em
    centímetros, a parede mede «400,0 cm» e «320» lê-se 3,20 m, com as cotas dos pavimentos ainda em metros;
    voltar a metros; o pavimento térreo escolhido na lista do rodapé.

## 0.185.0 — 2026-10-25

Interface nova, quarta etapa: as **Propriedades** (painel 7).

- **Em cima**, o que está selecionado: o ícone, o nome e, por baixo, o tipo (por exemplo, «Parede 1 / Parede
  alvenaria 20 cm»). Com nada selecionado, a vista à mostra («3D», «Planta — Térreo»…); com vários, quantos são.
- **Pesquisar propriedades…**: escrever deixa só as linhas cujo nome ou valor tem esse texto, dentro dos seus
  grupos.
- As linhas estão em **grupos que se recolhem**:
  - **Identificação** (nome, classe IFC, tipo, pavimento, GlobalId);
  - **Restrições e dimensões** (as medidas, as alturas, as ligações);
  - **Materiais e acabamentos (do tipo)**: as camadas e o perfil, que vêm do tipo e mudam em todos os elementos
    desse tipo;
  - **Fase**;
  - **Dados IFC e parâmetros** (os conjuntos de propriedades e o botão para juntar uma);
  - com nada selecionado, o grupo **Vista**.
- Separador **Navegador de Materiais**: os materiais do projeto com a sua cor; um duplo clique abre o material na
  janela dos materiais.
- Testes com a janela real: o nome, o tipo e o ícone de uma parede em cima; os grupos; a pesquisa deixa o
  comprimento e esconde a classe; o navegador de materiais lista-os e abre um; sem seleção, a vista em cima e o
  grupo Vista.
- Num teste com a janela real (o Push/Pull que abre um vão numa parede), passou a aceitar-se também a dica «Na
  aresta» quando o rato acaba numa aresta da face de trás. O vão sai igual.

## 0.184.0 — 2026-10-25

Interface nova, terceira etapa: a **barra compacta** (painel 4) e o **Navegador do Projeto** (painel 5).

- **Barra compacta** no extremo esquerdo, estreita e só com ícones (o nome aparece ao passar o rato). Cada ícone
  muda o que se vê ao lado:
  - **Navegador do Projeto**;
  - **Pavimentos**;
  - **Biblioteca** (o navegador aberto nos componentes e grupos);
  - **Folhas** (o navegador aberto nas folhas);
  - **Ambientes** (o quadro das salas);
  - **Tabelas e quantitativos**;
  - **Materiais** (a janela dos materiais);
  - **Regras gráficas**;
  - **Configurações**, em baixo (o botão do meio do rato e os painéis).
  O módulo ativo fica realçado. Clicar outra vez no módulo que está à vista recolhe os painéis da esquerda, para
  dar espaço ao modelo, e outro clique volta a mostrá-los.
- **Navegador do Projeto** (era o painel «Projeto»): passa para a esquerda, junto com os Pavimentos e as Regras
  gráficas, e tem em cima a caixa **Pesquisar…**. Escrever deixa só o que tem esse texto (vistas, folhas,
  componentes, pavimentos, categorias), com os grupos onde está; apagar o texto mostra tudo outra vez.
- As **Propriedades** ficam sozinhas à direita, com a altura toda.
- No rodapé, uma mensagem longa passa a ser cortada em vez de empurrar os botões de navegação para fora.
- Testes com a janela real: a barra compacta à esquerda e estreita, os painéis à esquerda e as Propriedades à
  direita; os módulos Pavimentos, Folhas, Ambientes; a pesquisa («Norte» deixa só o alçado Norte); recolher e
  voltar a mostrar.

## 0.183.0 — 2026-10-25

Interface nova, segunda etapa: a **barra de parâmetros** (painel 3).

- A barra por baixo das ferramentas passa a ter o ícone e o nome da ferramenta ativa à esquerda (por exemplo,
  «Parede»). Seguem-se os parâmetros, cada um com o seu nome (Tipo, Forma, Altura, Linha de referência,
  Pavimento…), em campos com rebordo e fundo claro. O campo em que se está a escrever fica com o rebordo azul.
- **Validação**: um valor escrito que não é uma medida (letras, por exemplo) põe o campo a vermelho durante um
  instante, o rodapé diz porquê e o valor anterior fica.
- **Roda dentada** ao fim dos parâmetros das ferramentas que desenham com um tipo (paredes, lajes, pilares, vigas,
  sapatas, tubos, condutas, portas, janelas): abre o editor de tipos com o tipo em uso já escolhido.
- Com a ferramenta Selecionar, a barra mostra o ícone da seleção e continua com os modos de seleção e os botões do
  que está selecionado.
- Testes com a janela real: o ícone e o nome da ferramenta; a altura escrita mal fica a vermelho e não muda; a roda
  dentada abre o editor no tipo da parede.

## 0.182.0 — 2026-10-25

Interface nova, primeira etapa (a proposta dos 8 painéis): o **cabeçalho com as disciplinas** e a **faixa de
ferramentas**.

- **Cabeçalho (painel 1)**: uma faixa escura com o símbolo e o nome ArqSynth BIM, e as disciplinas como
  separadores: Início (a casa), Modelagem, Arquitetura, Estrutura, Instalações, Terreno, Anotar, Massa e Estudos,
  Visualizar, Gerenciar, Render e Colaborar. À direita ficam o nome do projeto (com * quando há alterações por
  guardar) e os comandos Guardar, Desfazer, Refazer, Sincronizar (equipa) e Ajuda.
- **Faixa de ferramentas (painel 2)**: as ferramentas da disciplina ativa como botões grandes, com o ícone e o nome
  por baixo, em grupos separados por traços; a ferramenta ativa fica realçada. O que não couber vai para a seta da
  direita (o «Mais»). Um duplo clique numa disciplina esconde a faixa e outro volta a mostrá-la.
- As disciplinas substituem os quatro ambientes (Conceito, BIM, Estrutura, Docs) e a barra vertical de ferramentas.
  Ctrl+1 a Ctrl+9 mudam de disciplina (Modelagem a Gerenciar). As teclas das ferramentas funcionam em todas, e a
  disciplina escolhida fica para a próxima vez. Quem estava num ambiente começa na disciplina que lhe corresponde.
- **Os menus clássicos** (Arquivo, Editar, Vista, Ferramentas, BIM, Ajuda) deixam de se ver. Tudo o que tinham
  está numa disciplina:
  - o Início tem Novo, Abrir, Guardar, as importações e as exportações;
  - Colaborar tem a equipa, os vínculos e as verificações IFC;
  - Gerenciar tem os tipos, os materiais, os pavimentos, as fases, os componentes e os grupos;
  - Visualizar tem as vistas, os estilos e os painéis;
  - Render tem o Gaussian splat.
  Os atalhos de teclado continuam todos.
- **A navegação** (enquadrar, vista anterior e seguinte, orbitar, deslocar, zoom, câmara, caminhar) passa para o
  rodapé (painel 8).
- Correção (encontrada pelo dono do projeto): depois de passar por uma disciplina com o botão **Classificar** e
  mudar para outra, gravar um tipo dava «Não foi possível gravar o tipo: … QMenu already deleted». Ao refazer a
  faixa, o botão apagado levava consigo o menu da janela. Agora os botões de menu da faixa só mostram o menu ao
  clicar.
- Os comandos que não tinham ícone ganharam um (Novo, Abrir, Guardar, as exportações, o splat, a ajuda); os
  restantes mostram as iniciais. Os nomes longos aparecem abreviados por baixo do ícone, e o nome completo continua
  na dica.
- Testes:
  - sem janela: todas as ferramentas estão nalguma disciplina, todos os nomes da faixa são comandos que existem e
    todos os comandos dos menus estão nalguma disciplina; os atalhos; a correspondência dos ambientes antigos; os
    nomes partidos em duas linhas;
  - com a janela real: Massa e Estudos, Estrutura (Ctrl+3) e Anotar (clique no separador) mostram as suas
    ferramentas; a tecla W funciona em Anotar; a disciplina fica guardada; o Início tem os comandos do ficheiro; os
    menus estão escondidos; a navegação está no rodapé; o cabeçalho mostra o nome do projeto.

## 0.181.0 — 2026-10-25

Restos da Fase 4, passo 7: **os painéis da fachada de vidro, célula a célula**.

- Ferramenta nova **Painel de fachada** (separador BIM, ao lado da Fachada de vidro): escolha na barra de cima o
  painel e clique numa célula de uma fachada; a célula sob o rato fica realçada. Os painéis são:
  - **Vidro** (o habitual);
  - **Opaco**: um painel de 6 cm, como os de remate de laje;
  - **Porta de vidro**: só na fila de baixo e numa célula com pelo menos 1,90 m; desce até ao chão (a travessa de
    baixo deixa de passar por ali) e tem um puxador de cada lado;
  - **Vazio**: a célula fica aberta.
- Nas **Propriedades** da fachada, a linha **Painéis** conta os que não são de vidro.
- Os painéis ficam no IFC com a fachada (`Paineis`). O painel opaco leva um estilo cinzento próprio, que o Revit e os
  outros programas mostram. No ecrã do programa ainda aparece com a cor da fachada, porque cada elemento é pintado
  de uma só cor.
- Mudar o espaçamento dos montantes ou das travessas mantém os painéis das células que continuam a existir.
- Testes:
  - sem janela: a célula sob um ponto; a porta (sem travessa por baixo, a folha até ao chão, os puxadores); o opaco
    com o seu estilo; o vazio; a porta recusada na fila de cima e numa célula baixa; as Propriedades; o IFC
    válido;
  - com a janela real: uma porta e um painel opaco clicados com a ferramenta; as Propriedades.

## 0.180.0 — 2026-10-24

Restos da Fase 4, passo 5: **coberturas por extrusão**, com duas formas novas na ferramenta **Cobertura** e nas
Propriedades.

- **Abóbada**: um arco que nasce das paredes à **Inclinação** escolhida e corre ao longo da casa. A 30° o raio é
  igual ao vão e a flecha é cerca de 13 % do vão. Com beirado, o arco continua para lá das paredes.
- **Borboleta (calha ao meio)**: duas águas que descem das paredes compridas, à inclinação escolhida, até uma calha
  a meio da casa.
- O perfil vai sempre de um lado ao outro do vão mais curto e corre ao longo do comprimento. Só se fazem sobre
  contornos retangulares; noutros a mensagem diz porquê.
- As paredes ligadas à cobertura (**Ligar o topo**) seguem o arco ou a calha: as empenas ficam com o topo em arco,
  ou com o bico para baixo na borboleta.
- No IFC: **IfcRoof BARREL_ROOF** e **BUTTERFLY_ROOF** (confirmados no esquema IFC4), com um só sólido extrudido do
  perfil; na abóbada, arcos verdadeiros (IfcArcIndex). As áreas (inclinada e em planta) entram nas quantidades.
- Testes:
  - sem janela:
    - o referencial do retângulo;
    - o arco da abóbada a 30° (raio igual ao vão, a nascer nas paredes e com o beirado mais baixo);
    - a calha da borboleta e a sua altura num ponto;
    - um L recusado para as duas;
    - no IFC: a abóbada com arcos verdadeiros, o volume, a cumeeira, a empena ligada com o topo em arco, passada
      a borboleta (a calha, a empena a segui-la), o L recusado e o IFC válido;
  - com a janela real: a abóbada pela ferramenta e passada a borboleta nas Propriedades.

## 0.179.0 — 2026-10-24

Restos da Fase 4, passo 5: **coberturas de quatro águas sobre casas em L, T ou U**.

- A **Cobertura** de quatro águas passa a fazer-se sobre contornos com cantos para dentro, desde que os lados
  estejam em esquadria uns com os outros, mesmo que a casa esteja rodada (em L, T, U, em cruz…).
- Saem as cumeeiras de cada corpo, os rincões nos cantos de fora e as **lárós** nos cantos de dentro, todas as
  águas com a mesma inclinação, como as faria um carpinteiro.
- As de uma e de duas águas continuam a ser só sobre contornos convexos; nos outros casos a mensagem explica o que
  se pode fazer.
- Correção na **varinha mágica** «pelas faces exteriores» (lajes e coberturas): quando duas paredes se encontram
  num canto sem estarem ligadas, ficava um degrau no contorno (um quadrado de quase 1 m no canto de dentro de um
  L). Agora o canto fica limpo; um ressalto verdadeiro da parede continua a contar.
- Testes:
  - sem janela:
    - as águas de um L preenchem-no (24 m²) e cada uma está à altura certa (a do corpo mais alto);
    - as cumeeiras e os rincões no sítio, e o L rodado também;
    - os dois retângulos máximos;
    - a de duas águas sobre um L recusada;
    - a varinha num L de paredes não ligadas dá um L limpo e um ressalto verdadeiro fica;
    - no IFC: o volume da cobertura em L com beirado, a altura das cumeeiras, passada a plana e de volta;
  - com a janela real: a ferramenta Cobertura com um clique dentro de uma casa em L, a cumeeira à altura certa.

## 0.178.0 — 2026-10-24

Restos da Fase 4, passo 8: **revestimentos em camadas** na mesma face.

- Com a ferramenta **Revestimento de parede**, clicar num revestimento que já lá está põe uma **camada nova por
  cima** dele, na mesma face: por exemplo, reboco até ao teto e azulejo até 2,10 m por cima do reboco.
- Cada camada afasta-se da parede a espessura das camadas de baixo onde se sobrepõem. O azulejo fica a 2 cm da
  parede (o reboco) e com 1 cm de espessura.
- As camadas acompanham-se umas às outras:
  - mudar o acabamento ou a altura de uma camada de baixo leva as de cima (reboco passado a pedra de 3 cm: o
    azulejo sai mais 1 cm);
  - apagar uma camada de baixo faz descer as de cima, e Ctrl+Z repõe tudo.
- Nas **Propriedades**, uma camada que esteja sobre outras diz **Camada: 2.ª, sobre: Reboco 1**.
- Os revestimentos feitos antes desta versão contam como a primeira camada.
- Testes:
  - sem janela: reboco e azulejo na mesma face (o azulejo a 2 cm), o reboco passado a pedra, a outra face sem
    mudar, o reboco apagado e desfeito, o IFC válido;
  - com a janela real: reboco e depois azulejo clicado sobre o reboco, na planta; as Propriedades com a camada.

## 0.177.0 — 2026-10-24

Restos da Fase 4, passo 3: **portas e janelas nas paredes curvas**.

- As ferramentas **Porta** e **Janela** passam a funcionar nas paredes curvas:
  - passe sobre a parede e clique: o vão fica centrado no ponto do arco onde está o rato, arredondado ao centímetro
    e a pelo menos 5 cm das pontas;
  - fica virado para a face do lado do rato (por fora ou por dentro do arco), e F troca de face;
  - escrever um número põe o vão a essa distância da ponta mais perto, medida ao longo do arco;
  - **Só o vão** (sem caixilho) também funciona.
- A porta ou janela é direita, tangente ao arco no seu meio, e o vão é cortado com a profundidade necessária para
  atravessar a parede onde ela já curvou nas ombreiras.
- **Acompanham a parede**:
  - mudar o raio ou a espessura (o tipo) mantém cada vão à mesma distância ao longo do arco;
  - um arco encurtado ao ponto de deixar um vão de fora é recusado;
  - mover a parede leva os vãos, e apagá-la apaga-os.
- Nas **Propriedades** de uma porta ou janela de uma parede curva, as distâncias ao início e ao fim são medidas
  ao longo do arco e podem ser escritas. Também se pode virar a porta, trocar-lhe o tipo (a ombreira da esquerda
  fica onde estava) ou arrastá-la ao longo da parede.
- Testes:
  - sem janela:
    - o referencial tangente;
    - a profundidade do vão numa parede de 5 m de raio, e nenhuma numa demasiado apertada;
    - a distância ao longo do arco, também nos arcos ao contrário e para lá das pontas;
    - no IFC: a porta e o volume que a parede perde, a janela só com o vão, o raio mudado, o arco curto recusado,
      as distâncias nas Propriedades, mover, virar, trocar de tipo, arrastar, mover a parede, o IFC válido e
      apagar;
  - com a janela real: a porta e a janela postas pelas ferramentas, na planta, numa meia-circunferência; o raio
    mudado nas Propriedades, com as duas a acompanharem.

## 0.176.0 — 2026-10-24

Fase 8, passo 3: o modelo em **Gaussian splat**, para apresentação.

- **Ficheiro ▸ Exportar Gaussian splat (apresentação)…**: o modelo passa a uma nuvem de pequenos discos coloridos,
  espalhados por todas as superfícies. É o formato dos visualizadores de splats no navegador (por exemplo, o
  SuperSplat).
  - Escolhe-se a distância entre os pontos: **baixa** (8 cm, ficheiro leve), **média** (5 cm) ou **alta** (3 cm,
    ficheiro pesado).
  - Cada elemento tem a cor do seu material (a da primeira camada); os que não têm material ficam com a cor do
    ecrã.
  - A luz de um sol a sudoeste fica gravada nas cores, porque um splat mostra a mesma cor de qualquer lado.
  - As janelas e as fachadas de vidro ficam transparentes.
- O ficheiro é um **PLY binário** com as propriedades habituais do 3D Gaussian Splatting (posição, normal, cor,
  opacidade, escala e rotação), com o eixo Y para cima, como nesses visualizadores.
- Modelos que dariam mais de 4 milhões de pontos são recusados (é preciso escolher uma distância maior).
- Testes:
  - sem janela: uma sala com uma janela a 8 cm; o número de pontos certo para a área das superfícies; o Y para cima;
    cada disco deitado na sua face; as cores dentro dos limites; a janela transparente; o PLY lido de volta igual;
  - com a janela real: a opção no menu Ficheiro e a exportação de uma sala.

## 0.175.0 — 2026-10-24

Fase 10, passo 2 completo: as **superfícies onduladas**, feitas de costelas para cortar na CNC.

- No **Revestimento de parede** há um acabamento novo, **Ondulado (costelas)**: placas de 18 mm a cada 36 mm,
  deitadas umas sobre as outras ou de pé lado a lado. A frente de cada costela é uma onda, e de uma costela para a
  seguinte a onda roda um pouco, por isso as ondas desenham diagonais na parede. Juntas formam uma superfície
  ondulada.
- Por omissão a onda tem 6 cm de amplitude e 1,20 m de comprimento, roda 90° por metro e fica a 2 cm da parede no
  ponto mais fundo (a 8 cm no mais saliente).
- Nas **Propriedades**: **Espessura da costela**, **Intervalo**, **Sentido**, **Amplitude da onda**,
  **Comprimento de onda**, **Rotação da onda (por metro)** (0° faz ondas direitas, negativa roda para o outro
  lado), **Saliência mínima** e quantas **Peças** tem.
- As costelas são cortadas nas portas e nas janelas e seguem a parede, como o ripado.
- A **Lista de corte…** inclui as costelas (MDF), e o **DXF para fabrico…** desenha o contorno de cada uma (a costa
  direita e a frente em onda), todas, porque são todas diferentes.
- No IFC continua a ser um **IfcCovering** CLADDING: cada costela é um sólido extrudido do seu contorno
  (IfcIndexedPolyCurve).
- Correção: nas Propriedades já se pode escrever **0** onde o zero faz sentido: a **Altura ao chão** de um perfil
  (para voltar a pôr um friso no chão), o **Intervalo** de um ripado e a **Margem sem furos** de um painel.
- Testes:
  - sem janela:
    - as costelas deitadas numa face com uma porta: as do lado da porta em dois bocados, as de cima inteiras;
    - a frente sempre entre 2 e 8 cm e a onda rodada como deve;
    - as costelas de pé por cima da porta, só acima dela;
    - no IFC: uma peça por costela, a crista a 8 cm da face e a 12 cm com mais amplitude e as costelas de pé;
      o IFC válido, a lista de corte e o DXF com o contorno de cada costela;
  - com a janela real: o ondulado na parede norte de uma sala, pela ferramenta; a amplitude mudada nas
    Propriedades; a lista de corte e o DXF.

## 0.174.0 — 2026-10-24

Fase 10, passo 2 (segunda parte): a **Profile Pen**, ou **Perfil corrido**: rodapés, sancas, frisos e cimalhas ao
longo de um caminho ou à volta de uma sala.

- Ferramenta nova **Perfil corrido** (separador BIM, ao lado do Revestimento de parede), com quatro perfis:
  - **Rodapé**: 8 cm de altura e 1,5 cm de saliência, de madeira, no chão;
  - **Sanca**: meia-cana de gesso de 10 × 10 cm, encostada ao topo das paredes;
  - **Friso**: 6 × 2 cm, de madeira, a 0,90 m do chão;
  - **Cimalha**: perfil em degraus de pedra, 15 × 12 cm, encostado ao topo das paredes (para as fachadas).
- Duas maneiras de o pôr (Tab muda):
  - **À volta de uma sala**: um clique dentro da sala, e o perfil corre ao longo das faces das paredes, para dentro
    da sala, e à volta dos pilares que lá estejam;
  - **Caminho (clicado)**: clique nos pontos; Enter termina, um clique no primeiro ponto fecha o caminho, Delete
    apaga o último ponto. Na barra de cima escolhe-se o **Lado** (à esquerda ou à direita do caminho).
- Os cantos ficam **em esquadria** (cortados pela bissetriz, como os corta o carpinteiro).
- O perfil **para nas portas e nas janelas** que o atravessam: um rodapé para na porta, uma sanca passa por cima
  dela, um friso a 0,90 m para numa janela com o peitoril mais baixo.
- **O perfil segue a sala**: alongar uma parede ou pôr uma porta nova refaz o rodapé à volta da sala.
- Nas **Propriedades**: **Perfil** (trocar de um para outro), **Saliência**, **Altura do perfil**, **Altura ao
  chão**, **Lado** (nos caminhos) e o **Comprimento**.
- A **Lista de corte…** inclui as peças direitas de cada perfil, pelo comprimento maior (a ponta comprida da
  esquadria).
- O **DXF para fabrico…** desenha cada peça em planta, com as esquadrias das pontas e os ângulos (45° num canto
  de sala).
- No IFC é um **IfcCovering**: **SKIRTINGBOARD** no rodapé e **MOLDING** nos outros (os dois confirmados no esquema
  IFC4), com o material e uma malha de triângulos (IfcTriangulatedFaceSet) lida diretamente do ficheiro.
- Testes:
  - sem janela:
    - um rodapé à volta de uma sala de 4 × 3 m e ao longo de um L: sólidos fechados, com as faces para fora e o
      volume certo;
    - as peças com 45° nos cantos de dentro e nos de fora (à volta de um pilar, a frente mais comprida);
    - pontos em linha retirados e um caminho que volta para trás partido aí;
    - no IFC, numa sala de 5 × 4 m com uma porta:
      - o rodapé partido na porta, que acompanha a parede alongada e se corta numa porta nova;
      - a sanca inteira, rente ao topo das paredes;
      - um friso à direita de um caminho, mais alto pelas Propriedades, movido e espelhado;
      - o IFC válido, a lista de corte e o DXF;
  - com a janela real: rodapé e sanca por um clique na sala, friso por três pontos, a altura mudada nas
    Propriedades, a lista de corte com os três perfis e o DXF.

## 0.173.0 — 2026-10-24

Fase 10, passo 2 (primeira parte): **revestimentos com padrão**, ou seja, ripado, canelado e painel perfurado,
com **exportação para fabrico**.

- A ferramenta **Revestimento de parede** (separador BIM) tem três acabamentos novos:
  - **Ripado**: ripas de madeira de 4 cm com 2 cm de intervalo, na vertical ou na horizontal, centradas na face.
    Cada ripa é cortada onde há uma porta ou uma janela; por cima e por baixo do vão fica o bocado que lá cabe, e
    os bocados com menos de 5 cm ficam de fora.
  - **Canelado**: meias-canas de 4 cm encostadas umas às outras.
  - **Painel perfurado**: painéis de 16 mm, que são placas de 1,22 × 2,44 m recortadas nos vãos. Cada painel tem
    furos de 3 cm a cada 6 cm e 5 cm sem furos à volta, e por isso as juntas entre painéis ficam sem furos, como nos
    painéis acústicos.
- Nas **Propriedades** de um revestimento com padrão:
  - no ripado e no canelado: **Largura da ripa**, **Intervalo** (só no ripado) e **Sentido** (na vertical ou na
    horizontal);
  - no painel perfurado: **Diâmetro dos furos**, **Passo dos furos** e **Margem sem furos**;
  - quantas **Peças** ou **Furos** tem, os furos com a área aberta em %.
- O revestimento segue a parede: alongá-la ou pôr-lhe uma porta refaz as ripas e os furos.
- A **Lista de corte…** inclui as ripas (por comprimento, as iguais juntas) e os painéis perfurados.
- O botão novo **DXF para fabrico…** grava o ficheiro para a CNC, em milímetros:
  - cada painel deitado, com o contorno (e o recorte dos vãos), os furos e o nome, nas camadas CONTORNO, FUROS e
    TEXTOS;
  - cada comprimento de ripa uma vez, com quantas são.
- No IFC continua a ser um **IfcCovering** CLADDING ligado à parede:
  - as ripas são um sólido extrudido por peça;
  - as meias-canas são um perfil com arco (IfcIndexedPolyCurve com IfcArcIndex);
  - o painel perfurado é uma malha de triângulos (IfcTriangulatedFaceSet), que o programa lê diretamente do ficheiro
    e por isso um painel com milhares de furos aparece num instante.
- São recusados os padrões com mais de 20 000 furos ou 3000 ripas (o modelo ficaria pesado demais) e as medidas a
  zero ou negativas.
- Testes:
  - sem janela:
    - as ripas centradas, cortadas na porta, e também na horizontal;
    - os furos só em células inteiras, longe das margens, das juntas e da porta, e a malha com as faces para fora;
    - 8 painéis numa face de 4 × 2,6 m, o primeiro recortado pela porta;
    - no IFC: uma peça por ripa, menos ripas com mais intervalo, a meia-cana com arco, o painel como malha lida
      diretamente, mais furos ao alongar a parede, e o IFC válido;
    - a lista de corte e o DXF: um círculo por furo e o contorno recortado na porta;
  - com a janela real: ripado na parede sul e painel perfurado na nascente de uma sala, pela ferramenta; o intervalo
    alargado nas Propriedades; a lista de corte e o DXF.

## 0.172.0 — 2026-10-23

Fase 10, passo 1 completo: **as divisões dos móveis** e **o roupeiro**.

- Um móvel passa a ter **compartimentos** lado a lado, separados por divisórias, cada um com o que guarda:
  **prateleiras** (o número das Prateleiras), **varão de cabides** (com a prateleira de chapéus por cima), **gavetas
  interiores** (três, em baixo) ou **vazio**.
- Nas **Propriedades** de um móvel: **Compartimentos** (1 a 5) e, para cada um, **Compartimento 1, 2…** com o que
  tem; as portas passam a poder ser de 1 a 4 (pelo menos 25 cm cada).
- **Roupeiro**, um módulo novo (na barra de cima do Móvel): 1 m de largura, corpo de 2,30 m num rodapé de 10 cm
  (2,40 m), 58 cm de fundo, duas portas, e por omissão um compartimento de cabides e outro de quatro prateleiras.
- A lista de corte inclui as divisórias e as frentes das gavetas interiores; as ferragens, os varões de cabides e
  as corrediças das gavetas interiores.
- Compartimentos com menos de 15 cm, ou com um conteúdo que não existe, são recusados.
- Testes:
  - sem janela: o roupeiro de 1 m (2,40 m, duas portas), a divisória a meio, o varão no compartimento da esquerda
    debaixo da prateleira de chapéus, as quatro prateleiras do da direita; três compartimentos de gavetas
    interiores (seis corrediças); os recusados; a lista de corte com a divisória e sem o varão; no IFC, um
    «Roupeiro», os compartimentos guardados, mudar de módulo traz as medidas dele;
  - com a janela real: um roupeiro com três compartimentos pelas Propriedades, o do meio de gavetas interiores.

## 0.171.0 — 2026-10-23

Fase 10, passo 1 (terceira parte): **os eletrodomésticos e o gás**.

- **Eletrodoméstico** (botão no separador BIM, ao lado da Cozinha): passe sobre a face de uma parede e clique — o
  aparelho encosta-se a ela, à sua altura habitual:
  - **placa** e **placa a gás**, na bancada (rente ao tampo, a 90 cm); a **bancada fica recortada** para ela;
  - **forno** (no móvel inferior), **máquina de lavar loiça** e **máquina de lavar roupa** (debaixo da bancada),
    **frigorífico**, **micro-ondas** (na bancada) e **exaustor** (pendurado a 1,55 m, com a chaminé);
  - cada um com a sua forma (a caixa, a porta ou as portas; os queimadores da placa a gás) e as suas ligações: a
    máquina de lavar loiça e a de roupa com água fria e esgoto, a placa a gás com o **gás**.
- No IFC: **IfcElectricAppliance** (ELECTRICCOOKER a placa e o forno, DISHWASHER, WASHINGMACHINE, FRIDGE_FREEZER,
  MICROWAVE, e USERDEFINED «COOKERHOOD» o exaustor) e **IfcBurner** USERDEFINED «GASHOB» a placa a gás; as ligações
  são IfcDistributionPort (água fria, águas saponáceas, gás), como as das louças, e uma tubagem começada nelas fica
  no sistema certo.
- **A bancada recorta-se** pelas placas e pelos lava-loiças de cozinha (a louça «Lava-loiça», 0.140)
  que lhe ficam dentro: o perfil da bancada passa a ter os furos; mover ou apagar a placa refaz a bancada.
- As tubagens têm um sistema novo, **Gás** (amarelo; IfcDistributionSystem GAS).
- As Propriedades de um eletrodoméstico dizem qual é e a que está ligado.
- Testes:
  - sem janela: as medidas e os sítios habituais (a placa rente à bancada a 90 cm, o seu recorte de 56 × 49 cm
    dentro dela, o do lava-loiça), as ligações da máquina de lavar loiça e da placa a gás, as duas portas do
    frigorífico, o exaustor pendurado; no IFC, a placa recorta a bancada (um perfil com um furo), o lava-loiça outro,
    apagar a placa tira-lhe o furo; a máquina de lavar loiça com água fria e esgoto; a placa a gás um IfcBurner com
    o gás; o sistema Gás nas tubagens; IFC válido.

## 0.170.0 — 2026-10-23

Fase 10, passo 1 (segunda parte): **as cozinhas em fila, em L e em U**, e **a bancada**.

- **Cozinha** (botão no separador BIM, ao lado do Móvel): clique onde começa, na face de dentro de uma parede, depois
  em cada canto e onde acaba; Enter (ou o botão direito) faz a cozinha num só passo:
  - cada troço cheio de módulos inferiores de 60 cm, e o que sobra num módulo mais estreito das medidas habituais
    (30, 40, 45, 50 cm); num canto de dentro, o troço seguinte começa depois da profundidade dos módulos do anterior;
  - os superiores por cima (na barra de cima: **Superiores** sim/não), com os cantos pela sua própria profundidade;
  - a bancada por cima dos inferiores (**Bancada** sim/não);
  - as frentes escolhidas (portas, gavetas, gaveta e porta); os módulos de 60 cm com duas portas;
  - os cliques endireitam-se ao troço anterior (em X ou em Y), como se desenham as cozinhas; a sala fica do lado da
    face clicada primeiro, e F vira-a para o outro lado. Enquanto o rato anda, os módulos aparecem como vão ficar.
- **Bancada** (botão e menu BIM): sobre os móveis inferiores selecionados (ou todos os do pavimento): um
  **IfcSystemFurnitureElement** WORKSURFACE de 3 cm sobre os móveis (a 90 cm), 2 cm para lá das frentes, uma peça
  por troço, de um módulo ao outro (também por cima de um vão para uma máquina), juntas nos cantos; o material
  «Tampo de bancada».
- **A bancada segue os móveis**: se um muda de largura ou se move, refaz-se; se se apagam alguns, encolhe; se se
  apagam todos, sai com eles. Ctrl+Z traz tudo de volta.
- A lista de corte inclui as peças da bancada.
- Testes:
  - sem janela: uma cozinha em L (3 m e 2,4 m): cinco módulos de 60 até ao canto, o troço seguinte a começar depois
    da profundidade deles com três; virados para a sala, e ao contrário com a sala do outro lado; a bancada com as
    duas peças (3,00 e 1,80 m) e o contorno em L; no IFC, a cozinha num passo (8 inferiores, 8 superiores, a
    bancada WORKSURFACE a 90 cm), IFC válido; um módulo mais estreito e a bancada segue-o; apagados dois, encolhe;
    apagados todos, sai; desfeito, volta; a lista de corte com as duas peças;
  - com a janela real: a cozinha em L numa sala de 5 × 4 m, por três cliques e Enter (11 inferiores, 11 superiores,
    a bancada a 90 cm), e um Ctrl+Z que a tira toda.

## 0.169.0 — 2026-10-23

Fase 10, passo 1 (primeira parte): **os móveis paramétricos** — os módulos de uma cozinha ou de um roupeiro — e a
**lista de corte**.

- **Móvel** (botão no separador BIM, ao lado das louças): passe sobre a face de uma parede e clique — o móvel
  encosta as costas à parede, virado para a sala; clicado a menos de 10 cm do lado de outro, encosta-se a ele, e
  assim se faz uma fila de módulos. Longe das paredes fica no ponto, e R roda-o. Na barra de cima:
  - o **módulo**: inferior (num rodapé, debaixo da bancada), superior (pendurado a 1,45 m) ou coluna;
  - a **largura** (as habituais, de 30 a 120 cm, ou escrita e Enter);
  - as **frentes**: portas (1 ou 2), gavetas, gaveta e porta, ou aberto (prateleiras);
  - o **puxador**: barra, botão, ou sem puxador (gola).
- Cada móvel é feito das suas peças, como o marceneiro as corta: duas laterais, a base, o tampo (num móvel inferior,
  duas travessas, onde assenta a bancada), as costas, as prateleiras, o rodapé recuado, as frentes com folgas de
  3 mm e os puxadores. As medidas habituais: corpo de 72 cm num rodapé de 15 cm (a bancada fica a 90 cm),
  profundidade 56 cm; o superior com 33 cm de fundo; a coluna até aos 2,17 m dos superiores.
- No IFC: um **IfcFurniture** USERDEFINED («Móvel inferior», «Móvel superior», «Coluna»), embutido
  (`Pset_FurnitureTypeCommon`: as medidas nominais e IsBuiltIn), com uma forma por peça; o material «Aglomerado
  melamínico».
- **Propriedades** de um móvel: o módulo, a largura, a altura e a profundidade do corpo, o rodapé (ou a altura ao
  chão, num superior), as frentes, quantas portas, gavetas e prateleiras, o puxador, e as medidas totais. Ao mudar,
  o móvel refaz-se, com o canto esquerdo no mesmo sítio (mais largo, cresce para a direita); medidas fora do que se
  faz são recusadas.
- **BIM ▸ Lista de corte…** (botão ao lado do Móvel): as peças dos móveis selecionados (ou de todos) — peça,
  material, comprimento × largura × espessura em mm, quantidade e orlas —, as peças iguais juntas; a área de placa
  por material e as ferragens (dobradiças, pares de corrediças, puxadores, pés). **Exportar CSV…**.
- Testes:
  - sem janela: um módulo inferior de 60 cm com duas portas (as laterais de 72 cm sobre o rodapé de 15, as duas
    travessas, a prateleira, as portas com as folgas, 4 dobradiças e 4 pés); um de gavetas (3 frentes, 3 corrediças,
    sem prateleiras); um superior (com tampo, sem rodapé, a 1,45 m); a lista de corte junta as peças iguais; medidas
    fora do que se faz recusadas; uma parede de 2,85 m enche-se com 4 módulos de 60 e um de 45; no IFC, o móvel, as
    medidas nominais, uma forma por peça, IFC válido, mudado (mais largo, com gavetas) com o canto no sítio, uma
    medida impossível recusada sem estragar nada, a lista de corte, e lido de novo do ficheiro;
  - com a janela real: dois módulos inferiores contra a parede de uma sala (o segundo encostado ao primeiro), um
    superior por cima, gavetas pelas Propriedades, a lista de corte e o CSV, e a cozinha em 3D.

## 0.168.0 — 2026-10-23

Fase 9, passo 5 completo: **os desenhos estruturais**. Com eles, a **Fase 9 fica completa**.

- **Plantas de estrutura** (no painel Projeto, em Vistas ▸ Plantas de estrutura, um por pavimento com estrutura):
  - a planta cortada logo abaixo das lajes do pavimento: os pilares e as vigas cortados (a cheio), as sapatas
    vistas por baixo, as lajes a tracejado por cima, os eixos e o norte;
  - cada elemento com a sua etiqueta, feita quando se desenha (segue o modelo): «P1 30×30», «V2 20×40» (por cima de
    uma viga em X, à direita de uma em Y), «L1 h = 0,15», «S1 1,20×1,20».
- **Desenhos de armaduras** (em Vistas ▸ Armaduras, um por elemento armado), lidos das armaduras do IFC:
  - uma viga: o alçado com o betão, cada varão a traço grosso (com as dobras nos apoios) e um traço fino por estribo,
    e o corte A–A a meio vão, ampliado 2,5×, com o estribo e os seus ganchos e os varões a cheio;
  - um pilar: o alçado com os varões desde a sapata e as cintas, e o corte B–B a meia altura, ampliado;
  - uma sapata: a planta com a malha nas duas direções e o corte C–C;
  - uma laje: a planta com a malha;
  - cada conjunto com a sua legenda: «2 Ø12 — pos. 3 — L = 6,54 m», «24 Ø8//0,25 — pos. 4» (as posições são as da
    lista de armaduras);
  - o desenho conta o lugar das suas legendas, para que a vista seguinte na folha não as tape.
- Botão direito ▸ **Pôr na folha** (numa folha que já existe ou numa nova), como as outras vistas: vão para o PDF,
  o PNG, o SVG e a impressão das folhas.
- Testes:
  - sem janela: o desenho de armaduras de uma viga (os contornos do alçado e do corte, um traço por varão e por
    estribo, os varões cortados a meio vão, as legendas com as posições e o corte A–A); os de um pilar, de uma
    sapata (os 7 varões cortados) e de uma laje; nenhum para um elemento sem armaduras; a planta de estrutura com os
    pilares e as vigas cortados, a laje a tracejado e as etiquetas «P1 30×30», «V1 20×40», «L1 h = 0,15»,
    «S1 1,20×1,20»;
  - com a janela real: o painel Projeto lista a planta de estrutura e os 13 elementos armados; a planta numa folha,
    a viga e o pilar noutra, as duas desenhadas e gravadas em imagem.

## 0.167.0 — 2026-10-23

Fase 9, passo 5 (primeira parte): **as quantidades da estrutura e a memória de cálculo**. Partem do calc_quantities e
do calc_report do ArqSynth Modeler (decisão 3).

- **Estrutura ▸ Quantidades da estrutura…** (botão no separador Estrutura e menu BIM):
  - cada pilar, viga, laje e sapata com o seu **betão** (o volume da forma como está no modelo), a **cofragem** (os
    lados e o fundo das vigas, as faces dos pilares, os lados das sapatas, o fundo e os bordos das lajes) e o **aço**
    (o das armaduras postas no modelo, 0.166); a **taxa de aço** em kg/m³, a vermelho quando sai do habitual para o
    tipo (vigas 40–220, pilares 60–300, sapatas 15–120 kg/m³, os intervalos do addon);
  - uma linha por tipo e o total; **Exportar CSV…**; um duplo clique seleciona o elemento.
- **Estrutura ▸ Memória de cálculo…**: grava um **PDF** (pelo próprio Qt, sem bibliotecas novas) ou uma página
  **HTML** com:
  1. a identificação do projeto (da Legenda: projeto, dono de obra, local, autor, fase), a data e a versão;
  2. a regulamentação e os materiais (as normas, o betão com fck, fcd, fctm e Ecm, o aço, os recobrimentos, o solo);
  3. as ações (os usos e os ψ, as restantes cargas permanentes, o vento, o sismo) e a tabela por piso, com o período e
     o corte basal;
  4. o modelo analítico e os problemas da sua verificação;
  5. a análise: o caminho das cargas, a deriva e os esforços de cada barra;
  6. a verificação EC2 de cada elemento, com todas as suas notas;
  7. as quantidades;
  8. as armaduras, posição a posição, e os totais por diâmetro;
  9. os métodos, as notas e as limitações, e, num quadro a vermelho, que é um pré-dimensionamento e que o projeto é
     do engenheiro, que o verifica, completa e assina.
- As notas da verificação escrevem-se num módulo só (sem Qt), que serve à janela e à memória de cálculo.
- Testes:
  - sem janela: as fórmulas da cofragem (viga, pilar, sapata, laje), os totais por tipo e a taxa fora do habitual
    (só quando há armaduras); as notas escritas com a vírgula decimal e os varões em poucas palavras; no IFC, o
    betão de cada elemento é o da sua forma (um pilar 30 × 30 com 3 m: 0,27 m³), o aço das quantidades é o da lista
    de armaduras, e a memória de cálculo tem as nove secções, todos os elementos, o nome do projeto da Legenda e
    quem assina;
  - com a janela real: as quantidades do pórtico (13 elementos, uma linha por tipo e o total), o CSV, e a memória
    de cálculo em PDF e em HTML.

## 0.166.0 — 2026-10-23

Fase 9, passo 4: **verificação pelo Eurocódigo 2, armaduras no IFC e lista de armaduras**. As fórmulas são as do
ArqSynth Modeler (decisão 3), refeitas sem o Blender, agora com os esforços da análise (0.165).

- **Estrutura ▸ Verificação EC2 e armaduras…** (botão no separador Estrutura e menu BIM):
  - cada elemento de betão verificado pela NP EN 1992-1-1, com os esforços da análise:
    - **vigas**: flexão no vão (M+) e nos apoios (M−) pelo bloco retangular, com As,mín e As,máx; aviso de pouca
      ductilidade acima de μ 0,295; esforço transverso (VRd,c, bielas com cot θ de 2,5 a 1,0, estribos de dois
      ramos com o espaçamento máximo e a taxa mínima); deformação pelas relações vão/altura útil da 7.4.2 e a flecha
      elástica da análise contra L/250;
    - **pilares**: excentricidade mínima, esbelteza com os efeitos de 2.ª ordem (curvatura nominal, l0 = L) e os
      varões pelo **diagrama de interação N–M**, a flexão na direção mais fraca (do lado da segurança); cintas pela
      9.5.3;
    - **sapatas**: tensão no solo pela área efetiva (com as reações de serviço G + Q e os momentos), sapata rígida
      ou flexível, flexão nas duas direções e punçoamento (junto ao pilar e a 2d);
    - **lajes**: as duas direções pelo método de Marcus (simplesmente apoiadas) e a relação vão/altura útil;
  - os varões escolhidos para caberem: o diâmetro mais pequeno que dá a área numa só camada, com a distância livre
    da 8.2; espaçamentos arredondados a 2,5 cm;
  - a tabela: o estado (OK, Atenção, Falha, a cores), a utilização, a armadura («inf. 3 Ø16 · sup. 2 Ø12 ·
    estribos Ø8//0,175»), se as armaduras do modelo são estas, e o que manda; por baixo, todas as notas da linha
    escolhida; um duplo clique seleciona o elemento.
- **Pôr as armaduras no modelo** (um só passo de desfazer):
  - cada conjunto de varões é um **IfcReinforcingBar** (MAIN; SHEAR os estribos; LIGATURE as cintas), cada varão um
    IfcSweptDiskSolid ao longo do seu eixo; com o diâmetro, a secção, o comprimento de corte e a superfície
    nervurada; o Pset_ReinforcingBarCommon (posição, diâmetro, comprimento, espaçamento, forma) e o
    Qto_ReinforcingElementBaseQuantities (quantidade e peso); o material «Aço A500 NR» (ou A400); o projeto ganha a
    unidade de massa (kg);
  - as vigas com os varões inferiores e superiores a entrar nos pilares e dobrados nas pontas, e os estribos
    fechados com ganchos a 135°; os pilares com os varões desde a sapata (dobrados sobre a malha) até ao piso, com
    a emenda quando há pilar por cima, e as cintas; as sapatas e as lajes com a malha inferior nas duas direções (a
    da laje cortada pelo contorno menos o recobrimento);
  - **as armaduras ficam presas ao elemento**, como no Revit: apagar a viga apaga as suas armaduras, e mudar-lhe a
    forma (outra secção, outro comprimento) refá-las nela, com o mesmo cálculo;
  - o elemento recebe o Pset_ConcreteElementGeneral (classes do betão e do aço, recobrimento) e o passo dos
    estribos ou das cintas (ou o número de varões da sapata);
  - as posições numeram-se no projeto: varões iguais (diâmetro, forma, comprimento e dobragem) têm a mesma.
- **Estrutura ▸ Lista de armaduras…**: posição a posição, o elemento, a função, o diâmetro, a quantidade, o
  comprimento de cada, a forma (BS 8666), o comprimento total e o peso; os totais por diâmetro e o peso total;
  **Exportar CSV…** (abre como está no Excel).
- O painel de Propriedades de um conjunto de varões diz de que elemento é, a posição, os varões e o peso.
- Na árvore do projeto e na Visibilidade das vistas, as armaduras são uma categoria («Armaduras»), que se pode
  esconder numa vista.
- Testes:
  - sem janela:
    - EC2 contra contas à mão: uma viga 30 × 50 com 100 kNm (μ 0,097, As 5,34 cm², 5 Ø12 numa camada), 80 nos
      apoios (4 Ø12), 250 kN (estribos Ø8//0,175); uma secção pequena demais dita; as relações vão/altura útil do
      Quadro 7.4N; o comprimento de amarração de um Ø16 (40 φ); um pilar 30 × 30 esbelto com 1000 kN dentro do seu
      diagrama; uma sapata 2 × 2 com 192,5 kPa, rígida, com a malha mínima, e o tamanho que precisa quando a tensão
      passa; o momento de Marcus de uma laje 6 × 4;
    - a geometria dos varões: os de uma viga nas cotas e larguras certas, a entrar 12 cm nos pilares e dobrados
      (forma 21), os 34 estribos; os de um pilar desde 42 cm dentro da sapata; os 7 + 7 de uma sapata de 1,2 m;
      os de uma laje em L todos dentro dela; uma cinta e um estribo do mesmo comprimento mas dobrados de outra
      maneira são posições diferentes;
    - no IFC: o pórtico de 0.164 todo OK e as armaduras postas: as três classes de varão, um sólido por varão, as
      posições, o aço A500 NR, a unidade de massa, os psets das vigas, IFC válido; a viga mais alta refaz os seus
      estribos (20 cm mais compridos); apagada, leva as armaduras; desfeito, voltam;
  - com a janela real: o pórtico verificado (13 elementos OK), as armaduras postas (30 conjuntos, 270 varões, a
    janela diz que são as do modelo), a lista e o CSV, as Propriedades de um conjunto, o raio X, e Ctrl+Z.

## 0.165.0 — 2026-10-23

Fase 9, passo 3: **a análise da estrutura como um pórtico espacial**. O solver é o do ArqSynth Modeler (decisão 3),
refeito sem o Blender.

- **Estrutura ▸ Analisar a estrutura…** (botão no separador Estrutura e menu BIM):
  - o modelo analítico (0.163) passa a um **pórtico espacial**:
    - 6 graus de liberdade por nó, resolvido pela matriz de rigidez em banda;
    - o betão com o seu módulo (do Ecm da classe escolhida) e cada barra com a sua secção;
    - os apoios como foram feitos;
    - **cada piso um diafragma rígido**;
  - **as cargas** (0.164):
    - o peso próprio de cada barra;
    - o G e o Q de cada laje levados às vigas pelas **áreas de influência**: cada bocado da laje vai para a viga
      mais próxima, que num retângulo é a regra dos 45°. Uma laje sem vigas descarrega nos topos dos pilares;
    - o vento e o sismo de cada piso, em X e em Y;
  - **as combinações** da NP EN 1990: fundamental, com o vento e o sismo em cada direção e nos dois sentidos, e a
    quase permanente para as flechas;
  - **a tabela**, barra a barra (os pilares primeiro): o comprimento, o N mínimo e máximo, o V, o momento de vão e
    o de apoio (ou o maior de um pilar), a flecha a meio vão (em mm e L/…, a vermelho acima de L/250) e a
    combinação que manda;
  - **o caminho das cargas confere-se**: o que entra (os pesos e as sobrecargas) é o que desce aos apoios. Também
    se mostra a deriva máxima com o vento;
  - um duplo clique numa linha seleciona o elemento, e «Analisar outra vez» volta a calcular depois de mudar o
    modelo.
- Uma laje pousada nas vigas (3,15 m sobre 3,00 m) conta como o mesmo piso.
- Testes:
  - sem janela:
    - o pórtico espacial confere com as tabelas de vigas: simplesmente apoiada com 10 kN/m em 6 m (45 kNm a meio,
      30 kN em cada apoio, flecha 5qL⁴/384EI); encastrada nos dois extremos (−30 kNm nos apoios, 15 a meio);
      consola com 10 kN na ponta (30 kNm, PL³/3EI); um mecanismo é dito;
    - o pórtico com laje: o que entra desce aos apoios, os pilares ficam comprimidos, as vigas positivas no vão e
      negativas nos pilares, com flechas pequenas; a deriva com o vento fica abaixo de 1/500; a laje reparte-se
      toda pelas vigas, e a do meio leva mais;
  - com a janela real: o pórtico com laje analisado. Fecha o caminho das cargas (187,6 kN entram e descem), mostra
    oito linhas, e o duplo clique seleciona a viga.

## 0.164.0 — 2026-10-23

Fase 9, passo 2: **as ações e os materiais da estrutura**, pelos Eurocódigos com os Anexos Nacionais portugueses.
É um pré-dimensionamento: o projeto de estruturas é do engenheiro, que o assina (a janela di-lo).

- **Estrutura ▸ Ações e materiais…** (botão no separador Estrutura e menu BIM):
  - **materiais**: o betão (C20/25 a C50/60) e o aço das armaduras (A400, A500);
  - **cargas**:
    - o uso dos pisos e o da cobertura, pelas categorias da NP EN 1991-1-1 (A habitação 2,0 kN/m², B escritórios
      3,0, C1 a C3, D1 comércio, E1 armazenagem, H cobertura não acessível 0,4), com os coeficientes ψ;
    - os revestimentos (1,5 kN/m² por omissão) e as divisórias distribuídas (1,0);
  - **vento**: a zona (A 27 m/s, B 30 m/s) e a categoria do terreno. A pressão de pico qp(z) faz-se piso a piso
    (NP EN 1991-1-4), e as categorias usam os valores recomendados da norma, a confirmar no Anexo Nacional;
  - **sismo**: as zonas do Anexo Nacional para o sismo afastado (tipo 1, zonas 1.1 a 1.6) e o próximo (tipo 2,
    zonas 2.1 a 2.5), o tipo de terreno (A a E) e a classe de importância. O espectro de cálculo segue a NP
    EN 1998-1 (S a cair com ag, os períodos do terreno, q = 2,0), com T1 estimado pela altura (Ct = 0,075) e o
    método das forças laterais, a repartir em altura;
  - **solo**: a tensão admissível (para as sapatas, no passo 4).
- **A tabela, piso a piso, muda enquanto se escolhe**: a altura, a área das lajes, G e Q, o peso sísmico (G + ψ2 Q:
  as lajes, as vigas, metade dos pilares e das paredes acima e abaixo), o vento em X e em Y e o sismo tipo 1 e
  tipo 2. Por baixo vêm o período, o Sd e o corte basal.
- **OK guarda tudo no IFC**: as definições no edifício (`ArqSynth_Estrutura`) e o modelo analítico refeito com os
  **casos de carga G e Q** (`IfcStructuralLoadGroup`). Cada laje tem a sua força por m² e cada barra o seu peso
  próprio, como as leem os programas de cálculo.
- Testes:
  - sem janela:
    - o vento a 10 m (zona A, categoria II) dá cerca de 1,07 kPa, e sobe com a altura e com a zona B;
    - o sismo de um pórtico de três pisos na zona 1.4, terreno B, dá T1 = 0,39 s, Sd = 1,69 m/s² e o corte basal
      certo, repartido 1:2:3; o S desce com ag; há oito combinações;
    - os materiais (fcd, fyd e o módulo do C25/30);
  - com o IFC: o pórtico com uma laje e as definições mudadas, guardadas e lidas. Os casos G e Q carregam o modelo,
    com a laje a 5,25 kN/m² de G (o peso e os revestimentos; numa cobertura não entram as divisórias) e cada barra
    com o seu peso. O IFC fica válido, e o peso sísmico bate com as contas à mão;
  - com a janela real: a janela com C30/37 e a zona 1.3, um piso na tabela, e depois de OK as definições no IFC e
    os casos G e Q.

## 0.163.0 — 2026-10-23

Fase 9, passo 1: **o modelo analítico da estrutura e a sua verificação**. É o começo do cálculo estrutural. A lógica
da validação vem do ArqSynth Modeler (decisão 3), refeita sem o Blender.

- **Estrutura ▸ Modelo analítico e verificação…** (botão no separador Estrutura e menu BIM):
  - **o modelo analítico** faz-se a partir do modelo físico, como no Revit:
    - cada pilar é o seu eixo, da base ao topo;
    - cada viga é o seu eixo, ao nível do topo (onde encontra os pilares e a laje);
    - os extremos juntam-se em **nós**: a ponta de uma viga junto a um pilar passa para o eixo dele;
    - uma viga apoiada noutra parte essa outra nesse ponto;
    - um pilar parte-se em cada nível onde uma viga lhe chega;
    - a base de um pilar sobre uma sapata é um **apoio encastrado**;
    - as lajes estruturais são **painéis** ao seu nível;
  - vai para o IFC como um `IfcStructuralAnalysisModel` (LOADING_3D), lido pelos programas de cálculo:
    - os nós são `IfcStructuralPointConnection`, com as condições de apoio (`IfcBoundaryNodeCondition`);
    - os pilares e as vigas são `IfcStructuralCurveMember`, ligados aos seus nós e ao elemento físico que
      representam;
    - as lajes são `IfcStructuralSurfaceMember`;
    - fica numa vista de análise (`GRAPH_VIEW`), e cada vez que se faz substitui o anterior;
  - **os problemas** aparecem numa lista, os erros primeiro (impedem o cálculo), depois os avisos:
    - erros: pilar suspenso (nada por baixo); viga sem apoio em nenhum extremo; sem secção ou sem altura; o modelo
      sem apoios;
    - avisos: pilar na cota da fundação sem sapata; um extremo de viga solto (é uma consola?); base fora dos
      níveis; sapata sem pilar; pilares sobrepostos; laje sem nada que a apoie; um material que não é betão;
    - um duplo clique seleciona o elemento, e «Verificar outra vez» refaz tudo depois de corrigir.
- **Vista ▸ Modelo analítico** desenha o modelo analítico por cima do modelo, sem ser tapado: os pilares a laranja,
  as vigas a azul, as lajes a verde e os apoios em quadrados vermelhos.
- Testes:
  - sem janela: um pórtico de 6 × 4 m com quatro pilares em sapatas, quatro vigas, uma viga a meio apoiada em duas
    delas e uma laje. Dá dez nós, onze barras (as duas vigas onde a do meio apoia partidas ao meio) e quatro
    encastramentos, sem problemas. Sem sapatas há quatro avisos; um pilar sem nada por baixo e uma viga solta são
    dois erros;
  - com o IFC: o pórtico desenhado com as ferramentas passa a um modelo de análise com oito nós, quatro apoios e
    oito barras, cada uma ligada aos seus dois nós e ao seu pilar ou viga. O IFC fica válido; refeito, continua a
    ser um só; lido de volta como foi desenhado;
  - com a janela real: o pórtico e um pilar suspenso. O modelo fica feito e desenhado por cima, o único erro é o
    pilar suspenso, e o duplo clique seleciona-o.

## 0.162.0 — 2026-10-23

Fase 8, passo 2, completo: **as paredes e o piso a partir de uma nuvem de pontos** (scan to BIM).

- **BIM ▸ Modelo a partir da nuvem…** (e o botão nos separadores Conceito e BIM):
  - **o chão e o teto** são as alturas onde os pontos se juntam (os picos das alturas). Encontram-se ao abrir a
    janela e podem corrigir-se, e a altura das paredes é a distância entre os dois;
  - **as paredes** leem-se numa fatia da nuvem a meia altura, de 1,0 a 1,4 m acima do chão (acima dos móveis e
    através das janelas):
    - procuram-se as linhas de pontos, uma a uma (a linha onde há mais pontos, os seus troços, e esses pontos
      saem);
    - as linhas a menos de 5° da direção principal do edifício, ou do esquadro dela, **endireitam-se** (um edifício
      rodado no levantamento também serve);
    - duas linhas à distância de uma espessura são as faces de uma parede, com a espessura medida ao centímetro e
      por cima dos vãos das portas e das janelas (intervalos até 3 m);
    - uma linha sozinha, uma fachada vista só por dentro, faz uma parede de 30 cm (pode mudar-se) **para fora**,
      do lado onde não há pontos;
  - a **laje do piso** fica debaixo das paredes, até às faces de fora (pode desligar-se);
  - o que se encontra aparece a azul na planta, e o botão «Procurar outra vez» volta a procurar depois de mudar a
    fatia ou as espessuras;
  - OK faz tudo num só passo, com as paredes ligadas como as desenhadas à mão (cantos e T). Ctrl+Z desfaz.
- Testes:
  - sem janela: uma sala de 6 × 4 × 2,8 m digitalizada por dentro, com uma parede de 10 cm a atravessá-la e o vão
    de uma porta. Encontra o chão e o teto (0 e 2,8 m), a parede interior de 10 cm inteira por cima do vão e as
    quatro exteriores de 30 cm, todas para fora. A mesma sala rodada 30° tem a direção principal a 30° e as linhas
    no esquadro dela;
  - com o IFC: as cinco paredes, com 2,80 m de altura, e a laje debaixo de tudo (de −0,3 a 6,3 m), num só passo, com
    o IFC válido;
  - com a janela real: a sala digitalizada ligada, a janela com o chão a 0, a altura de 2,80 m e as cinco paredes,
    e depois as cinco paredes e a laje feitas.

## 0.161.0 — 2026-10-23

Fase 8, passo 2, primeira parte: **ligar uma nuvem de pontos** ao projeto.

- **Ficheiro ▸ Ligar uma nuvem de pontos…** (e o botão nos separadores Conceito e BIM):
  - lê um levantamento com laser ou fotogrametria em **XYZ / PTS / TXT** (x y z, com ou sem intensidade e cor),
    **PLY** (em texto ou binário) e **LAS** (1.0 a 1.4, formatos de ponto 0 a 10, com a escala e o deslocamento do
    ficheiro). O LAZ (LAS comprimido) e o E57 não se leem;
  - um LAS grande lê-se sem passar o ficheiro todo para a memória;
  - mostram-se no máximo **1,5 milhões de pontos**, tirados por igual, para a vista rodar com suavidade;
  - os pontos aparecem com as suas cores. Quando o levantamento não as tem, pintam-se pela altura (azul em baixo,
    verde, amarelo, vermelho em cima);
  - o sítio é escolhido como para os desenhos DXF: nas coordenadas do levantamento do projeto, tal como está (perto
    de 0, 0), ou ao centro da vista com o ponto mais baixo a 0;
  - **numa planta vê-se a fatia da nuvem abaixo do corte**: as paredes aparecem como linhas de pontos, para desenhar
    por cima.
- **Vista ▸ Nuvens de pontos ligadas…** mostra as nuvens, com o pavimento e quantos pontos se veem. Para a
  escolhida, permite mudar as unidades, o tamanho dos pontos e se se vê, e tem os botões Ligar nuvem… e Apagar.
  Cada mudança desfaz-se com Ctrl+Z.
- Como os desenhos ligados, **não vai para o IFC**: guarda-se com as vistas, o ficheiro fica onde está, e lê-se outra
  vez quando o projeto abre.
- Testes:
  - sem janela: um LAS 1.2 de formato 2 montado no teste (a escala, o deslocamento e as cores), também lido do
    ficheiro sem o carregar todo e reduzido a metade; um PLY binário com cores; um CSV com cabeçalho; uma nuvem
    reduzida a 100 pontos;
  - com a janela real: uma sala de 6 × 4 × 2,8 m digitalizada por dentro (PLY, 28 mil pontos), ligada tal como está,
    com todos os pontos à vista. Vê-se na planta, os pontos ficam maiores pela lista, e depois de guardar e abrir
    outra vez lá está.

## 0.160.0 — 2026-10-23

Fase 8, passo 1, completo: **as portas, as janelas e o mobiliário a partir do DXF, e o perfil de correspondência**.
O DXF → modelo fica feito.

- **BIM ▸ Modelo a partir do desenho…** (antes «Paredes a partir do desenho»). A janela tem agora três listas de
  camadas:
  - **Paredes** (linhas), como na 0.159;
  - **Portas e janelas** (blocos): cada bloco que cai na espessura de uma parede é um vão, com a largura desenhada,
    no sítio onde foi desenhado. É uma porta ou uma janela pelo nome do bloco ou da camada (PORTA / DOOR,
    JANELA / WINDOW). Sem nome que o diga, um bloco com arco (a abertura) é uma porta, e um sem arco é uma janela.
    A porta abre para o lado onde o arco foi desenhado;
  - **Mobiliário** (blocos): cada bloco passa a um componente, com o contorno das suas linhas levantado à altura
    do móvel (mesa 75 cm, cadeira 85, cama 50, sofá 80, armário 2,00 m, louça 80; pelo nome do bloco). Fica uma
    cópia em cada sítio onde o bloco foi inserido, rodada como estava.
  - O que se encontra aparece a azul na planta (as paredes e os blocos dos vãos), e conta-se.
- **As paredes atravessam os vãos das portas.** No desenho, as linhas da parede param no vão da porta, mas a parede
  faz-se inteira por cima do vão, e a porta abre-se nela depois.
- **Os tipos das portas e das janelas** são os do projeto com essa largura (até 5 cm de diferença), senão tipos
  novos: uma porta de 2,10 m de altura, ou uma janela de 1,20 m num peitoril de 1,00 m.
- **Tudo num só passo**: as paredes, os vãos e o mobiliário. Ctrl+Z desfaz tudo. A mensagem diz quantos de cada se
  fizeram, e quantos vãos ficaram de fora por não caírem numa parede.
- **O perfil de correspondência** (as camadas escolhidas para cada coisa e as espessuras) fica guardado. O próximo
  desenho com as mesmas camadas já vem com elas marcadas. Sem perfil, as camadas marcam-se pelos nomes.
- Testes:
  - sem janela: uma sala com o vão de uma porta nas linhas duplas, os batentes desenhados e o bloco da porta. A
    parede de baixo fica uma só parede por cima do vão, a porta fica com 0,90 m no sítio desenhado e a abrir para
    dentro, e a mesa fica mobiliário com o contorno de 1,60 × 0,90. Sem a porta, o vão faz duas paredes;
  - com o IFC: paredes, a porta de 90 cm (do catálogo) entre 4,0 e 4,9 m, a janela de 1,20 m na parede de cima e as
    duas mesas, um só componente posto duas vezes, tudo num só passo. O IFC fica válido, e desfeito não fica
    nada;
  - com a janela real: o desenho completo ligado, as camadas marcadas pelos nomes, e 4 paredes, 1 porta, 1 janela e
    2 mesas feitas. O perfil fica guardado.

## 0.159.0 — 2026-10-23

Fase 8, passo 1, segunda parte: **as paredes a partir de um desenho DXF ligado**.

- **BIM ▸ Paredes a partir do desenho…** (e o botão nos separadores Conceito e BIM):
  - escolhe-se o desenho ligado, as **camadas das paredes** (já vêm marcadas as que têm nomes de paredes: PAREDE,
    WALL, MURO, ALVENARIA…), as espessuras a procurar (de 5 a 60 cm, por omissão) e a altura das paredes;
  - enquanto se escolhe, as paredes encontradas aparecem **a azul na planta**, e diz-se quantas há de cada
    espessura;
  - OK faz as paredes num só passo (Ctrl+Z desfaz-as todas).
- **Como se encontram as paredes**: uma parede no desenho são duas linhas paralelas (as suas faces) a uma distância
  entre as espessuras escolhidas, lado a lado num troço de ambas:
  - o eixo fica ao meio, e a espessura é a distância entre as linhas;
  - os pares mais juntos contam primeiro, e cada troço de uma linha só serve uma vez (a face de uma parede não é
    também a da parede do outro lado da sala);
  - os bocados seguidos juntam-se, mesmo quando uma parede interior parte a face de dentro da exterior (num T, a
    face de fora continua);
  - as pontas vão até onde os eixos se encontram, nos cantos e nos T;
  - as linhas curtas (tramas, traços) não contam.
- **Cada parede fica com o tipo da sua espessura**: o do catálogo ou do projeto que tiver essa espessura (até 5 mm
  de diferença), senão um tipo novo do projeto («Parede 25 cm»). O tipo novo é de alvenaria rebocada a partir de
  10 cm, e de placa abaixo disso.
- **As paredes ficam ligadas** como as desenhadas à mão: cantos em topo, T, e também às paredes que já houver.
  Fazem-se das mais compridas para as mais curtas, para que uma parede interior encoste à face das exteriores.
- Por agora, as portas e as janelas do desenho ficam como aberturas entre paredes. Os vãos e o mobiliário vêm na
  próxima versão.
- Testes:
  - sem janela: uma sala de 10 × 8 m em linhas duplas a 20 cm, com uma parede de 10 cm a atravessá-la. Dá cinco
    paredes, com os eixos 10 cm para dentro e os cantos e os T no sítio, e a parede de baixo fica inteira. As
    tramas, as linhas curtas e as linhas afastadas não contam;
  - com o IFC: essas cinco paredes num só passo. Ficam com os tipos de 20 cm e de 10 cm e um novo de 25 cm, e as
    exteriores cobrem o anel uma só vez. A interior vai de face a face, o IFC fica válido, e desfeito não fica
    nenhuma;
  - com a janela real: a planta em DXF ligada, a janela das paredes (com a camada PAREDES marcada e quatro paredes
    de 20 cm encontradas) e as paredes feitas, ligadas nos cantos.

## 0.158.0 — 2026-10-23

Fase 8, passo 1, primeira parte: **ligar um desenho DXF** a um pavimento, para desenhar por cima. É o começo do
DXF → modelo.

- **Ficheiro ▸ Ligar um desenho DXF…** (e o botão nos separadores Conceito e BIM):
  - a planta em DXF fica deitada no pavimento ativo, em linhas finas azuladas: linhas, polilinhas (também os seus
    arcos), arcos, círculos e blocos, cada um no sítio, rodado e à escala com que foi inserido;
  - as **unidades** vêm do ficheiro (mm, cm, m). Quando o ficheiro não as diz, adivinham-se pelo tamanho do desenho;
  - o sítio é escolhido como no Revit:
    - nas **coordenadas do levantamento** do projeto, quando o desenho está perto delas (por exemplo, com um
      terreno já importado);
    - **origem com origem**, quando o desenho está perto de (0, 0);
    - ao **centro da vista**, nos outros casos;
    - a mensagem diz qual foi.
  - **As ferramentas agarram-se às linhas do desenho**, como às arestas dos elementos: os cantos, os pontos médios
    e as próprias linhas. Uma parede começa no canto desenhado no DXF.
- **Vista ▸ Desenhos CAD ligados…**:
  - mostra os desenhos ligados, com o pavimento, as unidades (podem corrigir-se) e as caixas Visível e Bloqueado;
  - mostra as **camadas** do desenho escolhido, com quantas entidades e linhas tem cada uma. As camadas marcadas
    veem-se e as outras escondem-se;
  - tem os botões Ligar DXF… e Apagar.
  - Cada mudança desfaz-se com Ctrl+Z.
- **Não vai para o IFC.** Guarda-se com as vistas, ao lado do IFC, e o DXF fica onde estava: o caminho completo e
  o caminho a partir do projeto. Volta a ler-se cada vez que o projeto abre, por isso uma mudança feita no programa
  de CAD vê-se da próxima vez. Num projeto partilhado, faz parte das vistas.
- O DXF lê-se com um leitor próprio, sem bibliotecas novas. Aceita DXF em texto de qualquer versão, mas não o
  binário.
- Testes:
  - sem janela: uma planta em mm, com uma linha de 5 m, um meio círculo de uma polilinha, um círculo, um bloco de
    porta inserido rodado 90° e um texto, e as unidades adivinhadas quando faltam; o sítio de um desenho
    (coordenadas do levantamento, origem com origem, centro da vista) e as linhas no sítio (mm, rodadas, movidas);
    guardar e ler com a pasta do projeto mudada de sítio;
  - com o IFC: o desenho ligado, com uma camada escondida, guardado fora do IFC e lido de volta, e desfeito;
  - com a janela real: uma planta em DXF ligada à planta do rés-do-chão. Fica origem com origem, em mm, e
    desenhada; um clique um pouco ao lado do canto de uma parede cai nele; na lista, a camada das cotas
    desmarcada esconde-se; guardado e aberto outra vez, lá está.

## 0.157.0 — 2026-10-23

Fase 7, passo 3, completo: **as plataformas, com taludes, e o aterro e a escavação**. Com isto, a Fase 7 fica
completa.

- **Ferramenta Plataforma** (separador Conceito), como a plataforma do Revit, mas com taludes:
  - sobre o terreno selecionado, ou sobre o único que houver, desenhe um **retângulo** (dois cantos) ou um
    **polígono** (os cantos; Enter, ou um clique no primeiro, fecha);
  - a plataforma fica **à cota do terreno no primeiro canto**, ou à que escrever (ex.: «1,20» e Enter);
  - à volta dela fazem-se os **taludes**, até encontrarem o terreno:
    - em escavação, onde o terreno é mais alto, a 1:1 por omissão;
    - em aterro, onde é mais baixo, a 2:3 por omissão (1 de altura para 1,5 de largura);
    - na barra de contexto escolhe-se 1:1, 2:3, 1:2, 1:3 ou a prumo (um muro);
  - a mensagem diz quanta terra o terreno todo passa a tirar e a pôr. Ctrl+Z desfaz.
- **O terreno fica com o levantamento guardado.** A primeira plataforma guarda os pontos do levantamento no próprio
  terreno (um parâmetro do programa, em `IfcText`). A partir daí, o corpo do terreno no IFC é o **terreno proposto**,
  com as plataformas e os taludes. Os pontos acrescentados com a ferramenta Terreno por pontos vão para o
  levantamento, e as plataformas ficam.
- **Vista ▸ Aterro e escavação…** (e o botão no separador Conceito):
  - mostra as plataformas, com a cota, a área e a terra que cada uma tira e põe;
  - mostra os totais (onde as plataformas se sobrepõem, contados uma só vez) e o saldo;
  - permite apagar uma plataforma, e o terreno volta a ser o do levantamento nesse sítio.
- **Nas Propriedades** do terreno aparecem quantas plataformas tem e os volumes de escavação e aterro.
- **Nas plantas** (no ecrã, no PDF e no DXF), cada plataforma tem o seu contorno e a cota escrita ao meio
  («+1,00»). No DXF vão para a camada PLATAFORMAS.
- Testes:
  - sem janela: uma plataforma de 10 × 10 m num terreno plano. Subida 1 m, fica a 1 m, com o talude de aterro a
    meio da altura a 0,75 m da borda, e cerca de 133 m³ de aterro (100 debaixo dela e 33 nos taludes), sem
    escavação. Descida 1 m, cerca de 121 m³ de escavação, sem aterro. Também os taludes escritos («1:1,5»);
  - com o IFC: uma plataforma de 6 × 4 m no terreno inclinado. O terreno fica plano nela, o IFC continua válido, o
    levantamento mantém os 12 pontos e há escavação e aterro. A plataforma fica na planta («+12,00») e ao gravar e
    abrir outra vez; um ponto a mais no levantamento mantém-na; apagada, volta o terreno do levantamento; desfeito,
    volta ela;
  - com a janela real: na planta, a ferramenta Plataforma com dois cantos. A plataforma fica a +1,00, plana, com o
    contorno e a cota, e com terra tirada e posta. A lista de Aterro e escavação mostra-a, com os totais.

## 0.156.0 — 2026-10-23

Fase 7, passo 3, segunda parte: **o terreno a partir de um DXF, as cores de inclinação e as cotas de nível**.

- **Ficheiro ▸ Terreno a partir de um DXF…** lê um levantamento desenhado em DXF:
  - aproveita os pontos, as curvas de nível (polilinhas à sua cota), as linhas 3D, as polilinhas 3D, as faces 3D e
    os blocos (um ponto de levantamento como bloco);
  - lê também as **cotas escritas** («12,35»: o número é a altura, o sítio do texto é o ponto). Um número inteiro
    é tomado como o número de um ponto e não se lê;
  - uma janela mostra as camadas com cota, com quantos pontos cada uma tem e entre que cotas, já marcadas. As
    camadas em 2D (paredes, textos) não aparecem;
  - o terreno passa pelos pontos das camadas marcadas. As coordenadas de levantamento tratam-se como nos ficheiros
    de pontos (0.155);
  - aceita DXF em texto de qualquer versão, sem precisar de nenhuma biblioteca nova. O DXF binário não se lê.
- **Vista ▸ Inclinações do terreno**: a superfície do terreno pintada pela inclinação de cada triângulo, como nas
  análises de um terreno para um plano: verde até 5 %, amarelo-esverdeado até 10 %, amarelo até 15 %, laranja até
  25 %, vermelho acima. A barra de baixo dá a legenda.
- **Cota de nível** (nova forma da ferramenta Desenho 2D, a seguir ao Texto, com Tab):
  - um clique numa planta põe uma cruz e a altura do que está por baixo, abaixo do corte (terreno, laje, degrau),
    escrita como os arquitetos a escrevem: «+12,35», «-1,20», «±0,00»;
  - a cota **acompanha o modelo**: se o terreno ou a laje mudar, o número muda;
  - num corte ou num alçado, a cota é a altura do ponto clicado;
  - aparece no ecrã, no PDF e no DXF.
- Na planta no ecrã, o terreno cortado (um monte acima do corte) aparece numa **cor de terra**, e não no preto do
  que se corta de betão ou de alvenaria.
- Testes:
  - sem janela: um DXF com um ponto, uma curva de nível, uma polilinha 3D, uma face 3D, um bloco, uma cota escrita
    e um número de ponto (que não se lê), e as camadas com cota distinguidas das de 2D; a altura debaixo de um
    ponto (o topo de uma caixa, ou o que fica abaixo de um corte); a escrita «+12,35 / -1,20 / ±0,00»; as bandas
    de inclinação;
  - com o IFC: a cota de nível numa planta, sobre o terreno («+12,00»), e o terreno subido nesse ponto (passa a
    «+12,10» sozinha);
  - com a janela real: um DXF com pontos, cotas escritas e paredes em 2D. Aparecem as camadas certas, o terreno
    fica com 27 pontos e as cores de inclinação ficam à vista. Na planta, a cota de nível clicada mostra a altura
    do terreno.

## 0.155.0 — 2026-10-23

Fase 7, passo 3, primeira parte: **o terreno a partir de pontos, com curvas de nível**.

- **Ficheiro ▸ Importar pontos de levantamento…** (e o botão no separador Conceito) lê o ficheiro de texto de um
  levantamento (CSV, TXT, XYZ, PTS), com um ponto por linha:
  - aceita «x y z», «x;y;z», «x,y,z» ou com tabulações, e decimais com ponto ou com vírgula;
  - aceita o número do ponto antes e um código depois, e ignora a linha de cabeçalho;
  - as colunas lidas são x, y e z, por esta ordem.
  - **Coordenadas do levantamento** (longe da origem, como as PT-TM06):
    - num projeto ainda vazio, o projeto passa a usá-las. O IFC guarda-as tal como estão, e o programa trabalha
      perto da sua origem, sem tremer;
    - num projeto que já tem elementos, os pontos são trazidos para junto da origem.
    - A mensagem diz qual dos dois aconteceu.
- **Ferramenta Terreno por pontos** (separador Conceito), como os pontos da topografia do Revit:
  - escreva a cota (ex.: «12,50») e clique onde fica o ponto (com snaps: o canto de uma parede, uma linha-guia);
  - outra cota escrita muda a do último ponto e a dos seguintes;
  - Enter faz o terreno. São precisos pelo menos 3 pontos que não estejam em linha.
  - Com um terreno selecionado, os pontos **acrescentam-se a ele** e Enter refá-lo.
- **O terreno** é um `IfcGeographicElement` TERRAIN no `IfcSite` (não pertence a nenhum pavimento):
  - o corpo é um sólido fechado, como o Toposolid do Revit: a superfície triangulada dos pontos por cima, os lados a
    prumo e uma base 1 m abaixo do ponto mais baixo;
  - o material é «Solo natural», da categoria IFC *earth*. Por isso, nos cortes e nas plantas que o atravessam, a
    terra aparece com a trama própria (nova trama «Terra» nos estilos gráficos);
  - no ecrã não se veem os triângulos, só o contorno e as **curvas de nível**: de metro em metro, e de cinco em
    cinco mais grossas (as curvas mestras);
  - nas Propriedades vêem-se os pontos, a área, a cota mínima e a máxima, a **distância entre curvas** e a **base
    abaixo do ponto mais baixo**. As duas últimas podem mudar-se.
- **Nas plantas** (no ecrã, no PDF e no DXF):
  - o terreno aparece com as suas curvas de nível abaixo do plano de corte, numa cor de terra;
  - as curvas que ficam debaixo de uma laje ficam escondidas;
  - o que está acima do corte (um monte) aparece cortado;
  - um terreno que fica todo abaixo da vista não aparece;
  - no DXF, as curvas vão para as camadas CURVAS_NIVEL e CURVAS_MESTRAS.
- **Nos cortes**, o perfil do terreno aparece cortado, com a trama de terra.
- Testes:
  - sem janela: a superfície por uma grelha de pontos num plano a 10 %; o sólido (fechado, com o volume certo); a
    cota num ponto; as curvas de metro em metro, no sítio certo; a inclinação; ficheiros de pontos com todos os
    separadores e decimais;
  - com o IFC: o terreno (TERRAIN no `IfcSite`, IFC válido, trama de terra); os pontos lidos de volta; um ponto a
    mais e desfazer; as curvas na planta (só abaixo do corte, escondidas por uma laje por cima); o corte com terra;
    a distância entre curvas e a base mudadas;
  - com a janela real: um CSV de 30 pontos em coordenadas a 150 km de distância, importado num projeto vazio (o
    projeto passa a essas coordenadas, o terreno fica selecionado, com curvas em 3D e na planta). Depois, com a
    ferramenta, mais um ponto com cota 3 (31 pontos, topo a 3 m).

## 0.154.0 — 2026-10-23

Fase 7, passo 2: **a imagem de fundo**. Serve para desenhar por cima de uma planta digitalizada, de uma fotografia
aérea ou de um esquisso.

- **Ficheiro ▸ Importar imagem de fundo…** (e o botão com a imagem nos separadores Conceito e BIM):
  - aceita PNG, JPG, BMP, GIF, TIFF e WebP;
  - a imagem fica deitada no pavimento ativo, no meio do que se está a ver, meio transparente. Vê-se na planta
    desse pavimento e no 3D;
  - antes de calibrar, cada pixel vale 1 cm;
  - a vista enquadra a imagem, e a ferramenta Calibrar imagem começa logo nela.
- **Ferramenta Calibrar imagem**, em cinco passos (a barra de baixo diz sempre o que falta):
  1. clique na imagem no início de uma medida que conhece (uma cota escrita na planta, a largura de uma porta);
  2. clique no fim dessa medida. Enquanto move o rato, a linha mostra quanto ela mede agora na imagem;
  3. escreva a medida verdadeira (ex.: «8,50») e Enter. A imagem cresce ou encolhe à volta do primeiro ponto, e
     **fica bloqueada**;
  4. clique onde esse primeiro ponto fica no modelo (com snaps: o canto de uma parede, um cruzamento da grelha),
     ou Esc para a deixar onde está;
  5. clique na direção do segundo ponto, ou escreva o ângulo, ou Esc para a deixar como está.
  - Cada passo desfaz-se com Ctrl+Z.
- **Vista ▸ Imagens de fundo…**: a lista das imagens do projeto, com:
  - o nome, o pavimento, a largura, a opacidade, e as caixas Visível e Bloqueada;
  - os botões Importar…, Calibrar (a escolhida) e Apagar.
  - Uma imagem bloqueada não se calibra, não muda de largura e não se apaga até ser desbloqueada.
  - Se o ficheiro da imagem mudou de sítio, a lista avisa.
- **Não vai para o IFC.** As imagens guardam-se com as vistas, no ficheiro ao lado do IFC. A imagem em si fica onde
  estava: guarda-se o caminho completo e também o caminho a partir do projeto, por isso uma pasta de projeto
  copiada inteira (com as imagens dentro) continua a encontrá-las. Num projeto partilhado, as imagens fazem parte
  das vistas.
- **Zoom total** (duplo clique no botão do meio) também enquadra as imagens.
- Testes:
  - sem janela: os cantos de uma imagem rodada; a calibração (8 m medidos como 4 m: duas vezes maior, com o
    primeiro ponto no mesmo sítio); pôr no sítio e rodar para o segundo ponto; guardar e ler, com a origem do
    modelo deslocada e a pasta do projeto mudada de sítio;
  - com o IFC: importar e calibrar (um passo de desfazer cada um); guardar, a imagem não está no IFC, e abrir outra
    vez (a mesma imagem, no seu pavimento, bloqueada);
  - com a janela real: uma «planta digitalizada» de 600 × 300 px importada na planta do rés-do-chão (com 6 m de
    largura, desenhada, com a ferramenta nela). A cota é calibrada com «8» (12 m, bloqueada), o seu início vai à
    origem, depois guarda-se e abre-se outra vez (lá está, desenhada), e a lista mostra-a.

## 0.153.0 — 2026-10-23

Fase 7, passo 1, completo: **a Escala**. Com ela, as primitivas do conceito ficam todas: círculo, arco, offset,
espelho (desde a 0.108) e escala.

- **Ferramenta Escala** (separador Conceito, ao lado de Mover, Rodar e Espelho), como a do Revit:
  1. selecione um ou mais esboços;
  2. clique no **ponto base**, que fica onde está (os snaps funcionam: um canto, um ponto médio);
  3. escreva o **fator** e Enter:
     - «2» duplica, «0,5» reduz a metade;
     - «1;1;2» é um fator por eixo (X;Y;Z), aqui só fica mais alto.
  - Em alternativa, dois cliques: um ponto da seleção e o sítio para onde ele vai. O fator é a razão entre as
    distâncias ao ponto base, e vai-se vendo enquanto se move o rato.
  - O contorno escalado aparece a azul antes de confirmar. Ctrl+Z desfaz.
  - Os furos dos esboços também são escalados.
- **Os elementos BIM ficam de fora**: uma parede, uma laje ou um tubo têm as medidas do seu tipo e dos seus
  parâmetros. A mensagem diz quantos ficaram como estavam; para os mudar, use o tipo ou as medidas nas
  Propriedades.
- Testes:
  - sem janela: uma caixa de 2 × 1 × 1 escalada 2 vezes a partir de um canto (o volume 8 vezes maior, o canto no
    mesmo sítio, a matriz igual); só mais alta com «1;1;3»;
  - com a janela real: um retângulo de 3 × 2 escalado 2 vezes a partir do canto (6 × 4 no mesmo canto) e Ctrl+Z
    (3 × 2 outra vez).

## 0.152.0 — 2026-10-23

Fase 7, passo 1, terceira parte: **o Offset**.

- **Ferramenta Offset** (separador Conceito), como a do SketchUp: um clique numa face de um esboço e depois o
  rato para dentro (ou para fora) mostra o contorno desviado dessa distância. Um segundo clique, ou a **distância
  escrita** («0,10» e Enter), fá-lo:
  - **para dentro**, a face fica **dividida** pelo novo contorno, para fazer uma moldura à volta de uma janela ou
    uma borda que se empurra ou puxa;
  - **para fora**, numa face sozinha, a face **cresce**, e o contorno antigo fica dentro dela.
  - Os cantos ficam vivos (sem arredondar), e um círculo continua com os seus lados.
  - Um valor escrito logo a seguir corrige o último offset.
  - Por agora, só faces convexas (retângulos, círculos, polígonos regulares). Uma face em L diz porquê.
- **Desenhar dentro de uma face de um volume** (Retângulo, Círculo, Offset) já divide a face com qualquer
  polígono convexo, e não só um retângulo. Um círculo desenhado no topo de uma caixa e empurrado faz um furo
  redondo, e a caixa continua fechada.
- Testes:
  - sem janela: o contorno desviado (um quadrado mais pequeno com cantos vivos, um círculo com os seus 24 lados,
    para fora a crescer, longe demais para dentro sem nada); um círculo marcado no topo de uma caixa e empurrado
    (o furo redondo, a caixa fechada, o volume certo);
  - com a janela real: um retângulo de 3 × 2 e o Offset de 0,20 para dentro (a face dividida, a parte de dentro
    com 2,60 × 1,60).

## 0.151.0 — 2026-10-23

Fase 7, passo 1, segunda parte: **o arco**, na ferramenta Linha.

- Com a ferramenta **Linha**, **Tab** (ou «Traço: Arco tangente» na barra de contexto) faz dos traços seguintes
  **arcos**, como o arco tangente do SketchUp:
  - cada arco sai **tangente** ao traço anterior e acaba onde se clica; o primeiro, sem traço antes, é uma meia
    circunferência;
  - antes do clique vê-se o arco como vai ficar;
  - divide-se em troços de no máximo 15° (uma meia circunferência tem 12).
  - **Tab** volta às retas, e retas e arcos misturam-se no mesmo contorno.
- **Voltar ao primeiro ponto fecha uma face**, como com as retas: um contorno em D, uma janela em arco, uma ponta
  arredondada. Puxada com Push/Pull, a parte curva fica uma superfície lisa (0.150).
- Testes:
  - sem janela: o arco tangente (a meia circunferência com os seus 12 troços, todos na mesma circunferência e a
    sair na direção certa, um quarto a virar à direita, e em frente sem arco);
  - com a janela real: Tab, um arco em meia circunferência, Tab, uma reta de volta ao início (a face em D) e
    Push/Pull (um sólido com o lado curvo liso).

## 0.150.0 — 2026-10-23

Fase 7 (conceito e terreno), passo 1, primeira parte: **o Círculo**.

- **Ferramenta Círculo** (separador Conceito, ao lado do Retângulo), como a do SketchUp:
  - um clique no centro (no chão, numa face, com os snaps e alinhamentos de sempre);
  - um segundo clique onde o círculo passa, ou o **raio escrito** («1,5» e Enter).
  - É uma face de **24 lados** por omissão; a barra de contexto escolhe 12, 16, 24, 32, 48 ou 64.
  - Um valor escrito logo a seguir **corrige** o raio do último círculo, como no Retângulo.
  - Desenhado dentro de uma face de um volume, **divide essa face**, para a empurrar (um furo, um nicho) ou
    puxar.
- **Superfícies curvas lisas**: puxado com Push/Pull, o círculo dá um cilindro fechado cujos lados são uma só
  superfície. As arestas entre os lados escondem-se, como o SketchUp as suaviza, e não se veem 24 tábuas.
  - Vale para qualquer face cujos lados façam ângulos pequenos entre si (menos de 20°).
  - As arestas de uma caixa ficam.
- Testes:
  - sem janela: um círculo (24 lados, o raio, virado para cima), puxado (fechado, o volume, 24 arestas escondidas
    e só as duas circunferências à vista); uma caixa com as suas 12 arestas; um polígono virado para cima;
  - com a janela real: a ferramenta Círculo com o raio escrito, corrigido logo a seguir, e puxado com Push/Pull
    (um cilindro de lados lisos).

## 0.149.0 — 2026-10-23

Fase 6, passo 6: **coordenação**, com deteção de conflitos entre disciplinas, estados, relatório e notas BCF.
**A Fase 6 fica completa.**

- **BIM ▸ Detetar conflitos…** abre uma janela para escolher que disciplinas comparar:
  - as instalações (tubos, condutas, tubos VD, curvas, tês, terminais, equipamentos) contra a **estrutura**
    (pilares, vigas, lajes, sapatas, estacas);
  - as instalações **entre si** (uma conduta que cruza um tubo), sem contar as peças do mesmo ramal, que se
    tocam;
  - e, se se quiser, as instalações contra as **paredes** (onde é preciso uma abertura ou uma manga).
  - A procura pode ser só no pavimento ativo ou no projeto todo.
- **Procurar** lista os conflitos: os dois elementos, as disciplinas e o **estado**:
  - **Novo** na primeira vez que aparece;
  - **Ativo** se já lá estava na procura anterior;
  - **Aprovado** se foi aceite (por exemplo, uma passagem prevista numa parede), e fica aprovado nas procuras
    seguintes;
  - os que desapareceram ficam **Resolvidos**, e a janela diz quantos se resolveram desde a última procura.
  - Os estados guardam-se com o projeto e desfazem-se como o resto.
- **Ver** (ou um duplo clique) seleciona os dois elementos e aproxima a vista deles. **Aprovar** aceita o
  conflito.
- **Criar nota BCF** faz uma nota de coordenação («Conflito: Tubo 1 × Viga 1», tipo Clash) com os dois elementos
  e uma vista sobre o sítio. Vai para o painel Notas e exporta-se em .bcfzip para o Revit, o ArchiCAD ou o
  Solibri, como as outras notas.
- **Relatório…** grava a lista como uma página HTML: o projeto, a data, quantos são, e uma linha por conflito com
  os elementos, as disciplinas, o sítio e o estado. Serve para levar à reunião.
- **Como se deteta**: as formas de dois elementos entram uma na outra quando uma aresta de uma atravessa uma
  face da outra, ou quando uma está toda dentro da outra. Tocar (uma face encostada a outra, um tubo que acaba
  numa parede) não é conflito.
- Testes:
  - sem janela: duas caixas que se atravessam, que se tocam por baixo e de lado, e uma dentro da outra; um tubo
    que atravessa uma viga (o conflito e o seu sítio), um tubo por baixo dela e o seu ramal com uma curva (sem
    conflito), uma conduta que cruza um tubo, as paredes só quando pedidas, o relatório; os estados de procura
    em procura (novo, ativo, aprovado, resolvido), guardados com o projeto e desfeitos;
  - com a janela real: Procurar (um conflito, «Novo»), Ver (os dois selecionados), Aprovar («Aprovado»), Criar
    nota BCF (a nota com os dois elementos) e Relatório (a página).

## 0.148.0 — 2026-10-23

Fase 6, passo 5: **propostas automáticas** de abastecimento e drenagem a partir das salas e das louças. A de
elétrica já existia (0.145.0), e o passo 5 fica completo.

- **BIM ▸ Propor águas e esgotos**: em cada sala do pavimento ativo que tenha louças:
  - um **tubo de queda** Ø100 no canto mais perto da sanita (ou da primeira louça), a 15 cm das duas paredes,
    do teto do último pavimento até debaixo do piso. É de águas negras se a sala tiver sanita; senão, de
    saponáceas.
  - os tubos de **água fria** e de **água quente** Ø25 ao longo da parede das louças, por cima do teto (a
    2,40 m e a 2,50 m);
  - cada louça **ligada** a eles, como em «Ligar à rede»: os esgotos ao tubo de queda, a 2 %, e a água a descer
    do seu tubo até à entrada. Cada ramal leva um tê.
  - A proposta só se liga aos tubos que ela própria faz; os tubos que o projeto já tinha ficam como estão.
  - Tudo é uma operação de desfazer e fica marcado como proposta.
- **BIM ▸ Retirar a proposta de águas e esgotos** apaga de uma vez os tubos, curvas e tês que a proposta fez no
  pavimento. As louças ficam.
- Os ramais de água (também em «Ligar à rede») descem do seu tubo até à altura da entrada e entram a direito, sem
  passar por dentro da parede.
- Testes:
  - sem janela: uma instalação sanitária com sanita e lavatório (o tubo de queda no canto da sanita, de águas
    negras; a água fria ao longo da parede; todas as ligações feitas; um tubo de água fria do projeto deixado
    em paz; retirar e desfazer);
  - com a janela real: «Propor águas e esgotos» e «Retirar a proposta» numa instalação sanitária.

## 0.147.0 — 2026-10-23

Fase 6, passo 4 (Elétrica), última parte: **verificação e quantidades**. O passo 4 fica completo.

- **BIM ▸ Verificar a instalação elétrica…** lista o que falta ou está mal no pavimento ativo:
  - o pavimento tem pontos mas nenhum quadro;
  - um circuito não está num quadro;
  - um circuito não passa no cálculo (diz porquê: corrente, pontos a mais ou secção);
  - um circuito não tem canalização (com a indicação de BIM ▸ Ligar ao quadro);
  - pontos que não estão em nenhum circuito;
  - uma sala sem luminária.
  - Um duplo clique numa linha seleciona os elementos de que fala. «Verificar outra vez» refaz a lista depois de
    uma correção. Sem problemas, diz «Nada a apontar neste pavimento».
- **Tabelas ▸ Elétrica: quantidades**: quantas tomadas, tomadas duplas, interruptores, comutadores, quadros e
  luminárias há; os metros de tubo VD de cada diâmetro; e quantos circuitos. Como as outras tabelas, põe-se numa
  folha e exporta-se em CSV.
- Testes:
  - sem janela: um pavimento com duas tomadas e uma sala (sem quadro, pontos soltos, sala sem luminária), depois
    corrigido passo a passo (quadro e circuito, canalização, luminária com o seu circuito) até não haver nada a
    apontar; as quantidades (tomadas, quadro, luminária, metros de tubo, circuitos);
  - com a janela real: a lista com os dois problemas, o duplo clique a selecionar as tomadas soltas e a tabela
    das quantidades.

## 0.146.0 — 2026-10-23

Fase 6, passo 4 (Elétrica), quarta parte: **canalizações e ligação ao quadro**.

- **Ferramenta Tubo VD** (separador BIM): as canalizações elétricas (`IfcCableCarrierSegment` CONDUITSEGMENT) em
  Ø20, Ø25 e Ø32 desenham-se como os tubos.
  - Por omissão a 2,75 m, por cima de um teto a 2,60 m.
  - As curvas (`IfcCableCarrierFitting` BEND), as subidas e o resto fazem-se como nos tubos, com ligações
    CABLECARRIER.
  - Começada num ponto elétrico («Começar neste terminal»), sobe a parede a partir dele até à sua altura.
    Acabada num ponto, desce até ele. Fica ligada nos dois casos.
  - Os tipos de tubo VD aparecem no editor de tipos e editam-se como os outros.
- **BIM ▸ Ligar ao quadro (canalizações)**: cada circuito do pavimento ainda sem canalização ganha os seus tubos
  VD.
  - O percurso parte do quadro para o ponto mais próximo, depois para o mais próximo desse, e assim por diante,
    como se cablam os circuitos.
  - Cada ligação sobe a parede até 2,75 m, segue por cima do teto e desce até ao ponto seguinte, com curvas.
  - Cada ponto e o quadro ficam ligados, e os tubos ficam no circuito.
  - É uma operação de desfazer, e a mensagem diz quantos metros de tubo se fizeram.
- **O quadro de cargas** ganha a coluna **Tubo VD**: os metros de canalização de cada circuito e o total.
- Testes:
  - sem janela: um tubo VD com uma curva (a classe, o tipo, as quantidades do IFC, as ligações); um circuito de
    três tomadas ligado ao quadro (as nove peças, tudo ligado, o comprimento no quadro de cargas, não se repete,
    desfazer);
  - com a janela real: o Tubo VD a começar numa tomada (sobe, fica ligada) e «Ligar ao quadro» num circuito de
    duas tomadas.

## 0.145.0 — 2026-10-23

Fase 6, passo 4 (Elétrica), terceira parte: **perfis por tipo de sala e opções com pré-visualização**.

- **BIM ▸ Propor pontos elétricos…** abre uma lista das salas do pavimento ativo. Cada sala tem o seu **perfil**,
  tirado do nome: Quarto, Sala, Cozinha, Instalação sanitária (WC, casa de banho, I.S.), Corredor / entrada,
  Escritório, ou Outra. O perfil pode mudar-se numa lista, e Nenhum deixa a sala de fora.
- Cada perfil traz as quantidades habituais (luminárias, interruptores, tomadas, tomadas de dados e de bancada),
  que se mudam nas caixas. Por exemplo:
  - quarto: 1 luminária, 1 interruptor, 3 tomadas, 1 tomada de dados;
  - cozinha: 2 tomadas e 4 de bancada;
  - corredor: 2 comutadores de escada.
- **Onde ficam**, como um projetista começaria:
  - as luminárias no teto (uma no meio; duas ao longo de uma sala comprida);
  - um interruptor junto a cada porta, por dentro, a 15 cm do aro (sem porta, na parede mais comprida);
  - as tomadas espalhadas pelas paredes, longe das portas (30 cm do aro) e dos cantos, cada uma virada para a
    sala.
- **Pré-visualizar** desenha os pontos na planta (com os seus símbolos) antes de os fazer. **Aplicar** fá-los
  todos de uma vez (uma operação de desfazer). Ficam marcados como proposta.
- **BIM ▸ Retirar a proposta elétrica** apaga de uma vez o que a proposta pôs no pavimento. O que se desenhou à
  mão fica.
- Testes:
  - sem janela: os perfis pelos nomes; um quarto com uma porta (a luminária no meio, o interruptor junto à porta
    e virado para a sala, as tomadas longe da porta, a tomada de dados); aplicar, retirar e desfazer; uma
    cozinha sem porta (as 4 tomadas de bancada, o interruptor numa parede);
  - com a janela real: a janela de opções com o quarto, as tomadas mudadas para 2, a pré-visualização na
    planta, Aplicar e Retirar.

## 0.144.0 — 2026-10-23

Fase 6, passo 4 (Elétrica), segunda parte: **circuitos e cálculo, e o quadro de cargas**.

- **Novo circuito com a seleção** (menu BIM e barra da seleção, com pontos elétricos ou luminárias selecionados):
  os selecionados fazem um circuito novo, C1, C2…, que sai dos circuitos onde estava cada um.
  - O tipo vem deles: luminárias e interruptores dão iluminação; tomadas de bancada dão cozinha; um equipamento
    AVAC dá AVAC; o resto, tomadas.
  - Fica no quadro elétrico do pavimento, se houver um.
- **O cálculo de cada circuito**: a potência (a soma dos pontos), a corrente a 230 V (monofásico) e uma
  **verificação** simples:
  - a corrente não pode passar o disjuntor;
  - o tipo admite um número de pontos (8 em iluminação e tomadas, 4 em cozinha);
  - a secção do cabo tem de chegar para o disjuntor (10 A 1,5 mm², 16 A 2,5 mm², 20 A 4 mm², até 32 A 6 mm²).
  - **Atenção:** a potência por ponto, os disjuntores e as secções são os valores habituais do programa (uma
    luminária 100 W, uma tomada 300 W, uma tomada dupla 400 W, uma de bancada 1000 W), para mudar no projeto. A
    verificação não substitui o regulamento: o projeto elétrico é verificado pelo seu técnico.
- **Tabelas ▸ Circuitos: quadro de cargas**: uma linha por circuito, com o nome, o tipo, o quadro, os pontos, a
  potência, a corrente, o disjuntor, a secção e a verificação («OK», ou o que falha). Por baixo, o total de
  circuitos e a potência instalada com a sua corrente.
  - O nome, o disjuntor e a secção escrevem-se nas células («10», «16 A», «2,5 mm²»), uma operação de desfazer
    cada.
  - Um clique na linha seleciona os pontos do circuito.
  - Como as outras tabelas, agrupa-se por tipo, põe-se numa folha e exporta-se em CSV.
- **No IFC**: cada circuito é um `IfcDistributionCircuit` (LIGHTING ou ELECTRICAL) com os seus pontos atribuídos.
  O tipo, o disjuntor, a secção e o quadro ficam num conjunto de propriedades do programa no circuito. Os sistemas
  das tubagens (0.141) não mexem nos circuitos.
- Testes:
  - sem janela: três tomadas (C1: tomadas, 900 W, 3,91 A, 16 A, 2,5 mm², OK, o quadro), um interruptor e uma
    luminária (C2: iluminação); nove tomadas num circuito (pontos a mais), com 10 A (corrente a mais) e com 32 A
    (secção pequena); a tabela (os textos das unidades, as células editáveis); apagar um circuito e desfazer;
  - com a janela real: três tomadas selecionadas, «Novo circuito com a seleção» na barra, o quadro de cargas com
    a linha certa, e o disjuntor mudado na célula (Ctrl+Z repõe).

## 0.143.0 — 2026-10-23

Fase 6, passo 4 (Elétrica), primeira parte: **os pontos elétricos**.

- **Ferramenta Ponto elétrico** (separador BIM): tomada, tomada dupla, tomada de bancada, tomada de dados
  (RJ45), interruptor, comutador de escada, quadro elétrico e caixa de derivação (`IfcOutlet` POWEROUTLET /
  DATAOUTLET, `IfcSwitchingDevice` TOGGLESWITCH, `IfcElectricDistributionBoard`, `IfcJunctionBox`).
  - Como as louças, encosta-se à face da parede onde está o rato, voltado para a sala. Longe das paredes, fica
    no ponto, e R roda-o.
  - Cada um fica à **altura habitual** (do chão ao meio dele), que se pode mudar na barra antes do clique: tomadas
    a 0,30 m, tomada de bancada a 1,10 m, interruptores a 1,10 m, quadro a 1,50 m, caixa de derivação a 2,30 m.
- Cada ponto tem a sua **ligação** (`IfcDistributionPort` CABLE, sistema ELECTRICAL, LIGHTING ou DATA), nas costas,
  para dentro da parede, onde chega o cabo. O quadro é a origem (SOURCE). O painel Propriedades mostra o tipo e a
  altura.
- **Na planta, o símbolo de cada ponto**, desenhado como à mão e com o tamanho no papel (as peças reais têm
  poucos centímetros):
  - a tomada é um meio círculo contra a parede com um traço (dois na dupla, uma barra na de bancada);
  - a tomada de dados é um triângulo;
  - o interruptor é um pequeno círculo com um traço inclinado (o comutador tem dois);
  - o quadro é um retângulo cheio; a caixa de derivação, um quadrado com uma cruz.
  - Os símbolos veem-se no ecrã, no papel (PDF, folhas, PNG, SVG, impressora) e no DXF (camada ELETRICIDADE).
- Testes:
  - sem janela: uma tomada, um interruptor e o quadro encostados a uma parede (o tamanho, a altura, a ligação e
    o sentido, as Propriedades), os símbolos na planta e no DXF; o símbolo da tomada à frente da parede, com o
    tamanho certo no papel;
  - com a janela real: na planta, a ferramenta Ponto elétrico sobre a face interior de uma parede: uma tomada, um
    interruptor e o quadro, encostados, às suas alturas, com os símbolos.

## 0.142.0 — 2026-10-23

Fase 6, passo 3: **ligar à rede (ramal automático)**. O passo 3 fica completo para a água e o esgoto.

- **BIM ▸ Ligar à rede** (também na barra da seleção, com louças selecionadas): cada ligação livre das louças
  selecionadas (sem seleção: as de todo o pavimento) leva sozinha um ramal até ao tubo mais próximo do seu
  sistema.
  - **Esgoto**: sai da louça para dentro da parede (ou para baixo, no ralo), desce na vertical e vai a 2 % até ao
    coletor ou ao tubo de queda. O esgoto de uma sanita procura primeiro as águas negras, o das outras louças
    as saponáceas; serve a outra se for a única. Um coletor mais alto do que a louça não serve, porque o ramal
    não pode subir.
  - **Água fria e água quente**: vêm do tubo do seu sistema. Sobem ou descem dele até à altura da ligação e
    seguem até à louça.
  - Cada ramal acaba no tubo principal com um **tê** (o principal parte-se ali) e na louça fica ligado à sua
    ligação, com as curvas pelo caminho. Os ramais ficam no sistema da ligação, com o diâmetro habitual: Ø100
    para a sanita, Ø50 para o resto do esgoto, Ø25 para a água.
  - Tudo é uma só operação de desfazer. A mensagem diz quantos ramais se fizeram e para que sistemas não havia
    rede («Sem rede para: Água quente (desenhe primeiro o tubo desse sistema)»).
- Testes:
  - sem janela: uma sanita com o coletor de águas negras e o tubo de água fria atrás da parede (os dois ramais,
    os dois tês, a descida e os 2 %, o sistema; desfazer); um lavatório a um tubo de queda de saponáceas, com o
    tê à altura certa, e a água sem rede;
  - com a janela real: uma sanita e um lavatório selecionados, «Ligar à rede» na barra da seleção: quatro ramais
    e o aviso da água quente.

## 0.141.0 — 2026-10-23

Fase 6: **os sistemas das instalações**. Cada tubo e conduta pertence a uma rede, como no Revit.

- **Sistema**, na barra de contexto das ferramentas Tubo e Conduta:
  - tubos: água fria, água quente, águas negras, águas saponáceas, águas pluviais;
  - condutas: insuflação, retorno, extração, ar novo.
  - O que se desenha (os troços, as curvas, as reduções, as descidas até um terminal) fica nesse sistema.
- **Um sistema de esgoto inclina sozinho**: escolher águas negras, saponáceas ou pluviais com o tubo nivelado
  põe a inclinação a 2 %, e a mensagem diz-o. A água fria e a quente voltam a nível. A inclinação pode mudar-se
  a seguir na barra.
- **O sistema herda-se**, como no Revit:
  - começar na ponta livre de um tubo, ou no meio dele (um tê), continua no sistema dele;
  - começar numa ligação de uma louça ou de um equipamento toma o sistema dessa ligação. O esgoto de uma sanita
    é «Águas negras», e a mensagem diz «Começa em «Sanita 1»: fica no sistema Águas negras».
  - Um tê fica no sistema do tubo principal (a parte nova dele também); o ramal fica no seu.
- **Que ligação se apanha**: sobre uma louça ou um equipamento com várias ligações, o clique (em qualquer sítio
  sobre a peça) toma a do sistema que se está a desenhar. Em água fria, a entrada de água fria da sanita; num
  sistema de esgoto, o esgoto. Só sem nenhuma dessas toma a mais próxima.
- **Cores dos sistemas** no ecrã: água fria azul, água quente vermelha, águas negras castanhas, saponáceas
  castanho-claras, pluviais ciano, insuflação azul-claro, retorno verde, extração amarela, ar novo azul-pálido.
  As regras gráficas («Colorir por») continuam a sobrepor-se.
- **No painel Propriedades**, um tubo, uma conduta, uma curva ou um tê mostra o seu sistema numa lista. Mudá-lo
  passa o **ramal todo** (o que está ligado a ele por tubos e acessórios) para o outro sistema, numa só
  operação de desfazer.
- **No IFC**: um `IfcDistributionSystem` por sistema usado (o nome e o tipo: DOMESTICCOLDWATER, SEWAGE,
  VENTILATION…), com os elementos atribuídos a ele (`IfcRelAssignsToGroup`). As ligações levam o `SystemType`
  dele. Um sistema que fica vazio sai do ficheiro.
- Testes:
  - sem janela: um ramal em águas negras (os troços e a curva no sistema, o seu tipo e nome, as ligações), outro
    em água fria (outro sistema), o ramal todo passado para saponáceas (o sistema vazio sai; desfazer); um tê
    no sistema do principal; o esgoto de uma sanita é águas negras;
  - com a janela real: a ferramenta Tubo em águas negras (2 %), o tubo na cor do sistema, o ramal passado para
    saponáceas no painel Propriedades, e uma sanita (em água fria apanha a entrada de água; em saponáceas apanha
    o esgoto e passa para águas negras).

## 0.140.0 — 2026-10-23

Fase 6, passo 3 (equipamentos com ligações), primeira parte: **louças sanitárias com ligações e zonas livres**.

- **Ferramenta Louça sanitária** (separador BIM, ao lado de Tubo e Conduta): sanita, lavatório, bidé, base de
  duche, banheira e lava-loiça (`IfcSanitaryTerminal` TOILETPAN, WASHHANDBASIN, BIDET, SHOWER, BATH, SINK), cada
  uma com o tamanho habitual.
  - Ao passar sobre a face de uma parede, a louça **encosta-se a ela**, virada para a sala, no ponto onde está o
    rato ao longo da parede, sem sair da parede. Longe das paredes, fica no ponto, e R / Shift+R roda-a 90°.
  - O contorno e a zona livre veem-se antes do clique.
- Cada louça tem as suas **ligações** (`IfcDistributionPort` PIPE, com o tipo de sistema do IFC):
  - o **esgoto**: SEWAGE (águas negras) na sanita, WASTEWATER (águas saponáceas) nas outras; a água sai por
    aqui;
  - a **água fria** e a **água quente** (DOMESTICCOLDWATER / DOMESTICHOTWATER), onde a água entra.
  - Cada ligação aponta para onde vai o tubo: para dentro da parede, ou para baixo, no ralo da base de duche e
    da banheira.
  - O painel Propriedades mostra que louça é e cada ligação, ligada ou livre.
- **Zona livre**: à frente de cada louça, a zona que o seu uso pede (80 × 70 cm à frente da sanita, do lavatório
  e do bidé; ao longo da banheira; 90 cm à frente do lava-loiça).
  - Fica guardada com a louça e desenha-se a tracejado verde na planta, no ecrã.
  - No papel sai a tracejado fino, e no DXF vai na camada ZONAS_LIVRES.
- **A ferramenta Tubo liga-se às louças** como a Conduta aos equipamentos: começa numa ligação («Começar aqui
  (Esgoto)»), à altura dela, ou acaba nela, chegando de fora a direito.
- Testes:
  - sem janela: uma sanita encostada a uma parede (o tamanho, o esgoto SEWAGE para dentro da parede, a água
    fria, a zona livre, a planta); um lavatório rodado 90° e um tubo até ao seu esgoto (entra a direito, ligado);
  - com a janela real: na planta, uma sanita e um lavatório encostados à face interior de uma parede (as zonas
    livres) e um tubo a sair do esgoto da sanita.

## 0.139.0 — 2026-10-23

Fase 6, passo 2 (AVAC), segunda parte: **equipamentos com ligações**. O passo 2 fica completo.

- **Ferramenta Equipamento AVAC** (separador BIM): um clique põe um equipamento (`IfcUnitaryEquipment`) com o
  meio da base no ponto, o contorno à vista antes do clique e os snaps de sempre. A barra de contexto escolhe:
  - **unidade de conduta**, no teto falso: base a 2,60 m, ligações de insuflação e retorno nas pontas e a
    saída de condensados;
  - **unidade interior mural (split)**, a 2,10 m, com a saída de condensados;
  - **unidade exterior**, no chão;
  - **UTA**, no chão, com as ligações de insuflação e retorno por cima.
  - A cota da base e a rotação (R / Shift+R: 90°) também se escolhem.
- Cada ligação é uma `IfcDistributionPort` (DUCT ou PIPE) virada para fora do equipamento, com o sentido do ar:
  a insuflação sai, o retorno entra. As ligações acompanham o equipamento quando ele se move ou roda, e uma
  cópia tem as suas.
- **Ligar condutas aos equipamentos**:
  - **começar numa ligação de lado** (passar o rato mostra «Começar aqui (Insuflação)»): a conduta sai dela à
    altura dela;
  - **acabar numa ligação de lado**: a conduta acaba um pouco antes (40 cm, ou três vezes a largura), desce
    ou sobe até à altura da ligação e entra nela a direito;
  - **numa ligação por cima** (a UTA): desce até ela, como num difusor.
  - A ferramenta Tubo liga-se do mesmo modo às saídas de condensados.
- Na planta, um equipamento acima do corte (a unidade no teto falso) vê-se a tracejado, como as condutas.
- Testes:
  - sem janela: uma unidade de conduta (o tamanho, as três ligações, para onde estão viradas), uma conduta a
    partir da insuflação e outra até ao retorno (três troços: ao longo, a descer, a entrar), a unidade rodada
    90°; uma UTA com uma conduta Ø250 a descer até à insuflação;
  - com a janela real: na planta, uma unidade de conduta e uma UTA rodada com R; uma conduta a partir da
    insuflação da unidade (à altura dela) e outra até à UTA (desce).

## 0.138.0 — 2026-10-23

Fase 6, passo 2 (AVAC), primeira parte: **condutas redondas, grelhas e difusores**.

- **Condutas circulares** Ø160, Ø200 e Ø250 (aço galvanizado) na ferramenta Conduta. No IFC levam
  `Pset_DuctSegmentTypeCommon.Shape = ROUND`. As curvas, tês e reduções fazem-se como nas outras.
- **Ferramenta Grelha / difusor** (separador BIM, ao lado de Tubo e Conduta): um clique põe um terminal de ar
  embutido no teto que está por cima (sem teto, a 2,60 m do pavimento), como a Luminária. A barra de contexto
  escolhe qual:
  - difusor quadrado 60 × 60 ou 30 × 30;
  - difusor circular Ø30;
  - grelha de retorno 60 × 30.
- Cada terminal (`IfcAirTerminal` DIFFUSER / GRILLE) tem a face no teto, o colarinho por cima e, no topo deste,
  a sua **ligação** (`IfcDistributionPort` DUCT).
  - Um difusor recebe o ar da conduta; uma grelha de retorno entrega-o à conduta.
  - O painel Propriedades mostra qual é e se é de insuflação ou de retorno.
- **Ligar condutas aos terminais**, como no Revit:
  - ao desenhar uma conduta, passar o rato sobre um terminal livre mostra «Ligar a este terminal (desce até
    ele)». O clique acaba a conduta por cima dele, com uma descida e uma curva até à ligação, e o desenho
    termina aí.
  - O primeiro clique sobre um terminal («Começar neste terminal») sobe a partir dele até à cota do eixo, e o
    desenho continua daí.
  - Mover o terminal leva a ligação com ele.
- **Correção**: uma subida ou descida muito curta (por exemplo, 12 cm num tubo Ø50) era recusada, e o desenho
  desfazia-se, porque as curvas deixavam um troço mais curto do que uma edição permite. Agora faz-se: com as
  curvas que couberem, e ligado na mesma.
- Testes:
  - sem janela: um difusor (a face, o colarinho, a ligação, as Propriedades), uma conduta Ø200 até ele (a
    descida, a curva, ligado; desfazer); uma grelha de retorno a começar uma conduta e movida com a ligação;
    uma subida de 12 cm;
  - com a janela real: na planta, um difusor e uma grelha (um clique cada), uma conduta Ø200 a 3,00 m até ao
    difusor e outra a começar na grelha.

## 0.137.0 — 2026-10-23

Fase 6, passo 1 (água e esgoto), segunda parte: **ramais e coletor, tês e reduções**. O passo 1 fica completo.

- **Tê**: um ramal desenhado até ao meio de outro tubo (o coletor, ou um tubo de queda) acaba aí, ligado por um
  **tê** (`IfcPipeFitting` / `IfcDuctFitting` JUNCTION).
  - Ao passar o rato sobre o eixo do outro tubo aparece «Ligar aqui com um tê».
  - O tubo principal parte-se em dois nesse ponto. O tê fica com um troço dele e um ramo ao longo do ramal, com
    três ligações, todas feitas.
  - O ramal escoa para o tê (esgoto). O ramal acaba na altura do tubo principal nesse ponto, e a mensagem diz
    a inclinação que ficou.
  - Num tubo de queda, o tê fica à altura do ramal.
  - O desenho do ramal termina aí, como no Revit.
- **Começar no meio de um tubo**: o primeiro clique sobre o eixo de um tubo («Começar aqui, com um tê») começa
  um ramal a partir dele, com um tê, à altura dele (abastecimento: a água sai do tubo principal para o ramal).
- A parte nova do tubo partido fica com o mesmo tipo, o mesmo pavimento e as mesmas propriedades (a fase, por
  exemplo), e continua ligada ao que estava ligado à ponta dele.
- **Redução**: mudar o tipo (o diâmetro) a meio do desenho põe uma **redução** entre os dois troços (TRANSITION):
  - nos tubos, um cone (`IfcExtrudedAreaSolidTapered`);
  - nas condutas retangulares, um sólido de faces planas (`IfcFacetedBrep`), porque o motor de geometria repete
    uma face na extrusão cónica de um retângulo.
  - O comprimento depende da diferença de tamanhos, e os dois troços ficam mais curtos para a receber.
- Testes:
  - sem janela: um ramal Ø50 num coletor Ø100 a 1 % (o tê, o coletor em dois, com a fase e a ligação do fim,
    as três ligações, o tamanho do tê, desfazer); um ramal num tubo de queda já ligado ao coletor; um ramal a
    partir de um tubo (a água sai); as reduções Ø100 → Ø50 (o volume do cone) e 50×30 → 30×20 (o volume certo);
  - com a janela real: na planta, um coletor, um ramal até ao meio dele (um tê, o desenho acaba), outro a partir
    do meio dele (outro tê) e um tubo que muda de Ø100 para Ø50 a meio (uma redução).

## 0.136.0 — 2026-10-23

Fase 6, passo 1 (água e esgoto), primeira parte: **inclinação, tubo de queda e subidas com curvas verticais**.

- **Inclinação**: a ferramenta Tubo tem, na barra de contexto, a **Inclinação** (0 a 5 %). Com 1 %, cada tubo desce
  1 cm por metro no sentido em que é desenhado (o do escoamento). O seguinte continua a partir da ponta mais baixa.
  - A mensagem diz de que cota a que cota desce o eixo.
  - O painel Propriedades mostra a inclinação e a cota do eixo no fim.
- **Na planta**, ao lado de cada tubo inclinado, uma **seta** no sentido em que desce e a inclinação escrita
  («1 %»).
  - No ecrã, no papel (PDF, folhas, PNG, SVG, impressora) e no DXF (camada COTAS).
  - O tamanho é o do papel, à escala da vista. A marca não aumenta o desenho, por isso a escala das folhas
    não muda.
- **Tubo de queda**: na barra de contexto, **Forma: Tubo de queda (vertical)**.
  - Um clique põe um tubo vertical, do **Topo** (por omissão, o teto do último pavimento) ao **Pé** (−0,30 m,
    debaixo do piso, onde o coletor o recebe).
  - Na planta vê-se cortado, como um círculo cheio.
- **Continuar a partir de uma ponta livre**: com a ferramenta Tubo (ou Conduta), passar o rato sobre a ponta
  livre de um tubo mostra «Continuar a partir daqui (eixo a …)», qualquer que seja a altura dessa ponta. Um
  clique começa aí, à altura dela.
  - É assim que se desenha o **coletor** a partir do pé do tubo de queda: fica ligado a ele por uma curva.
  - É como no Revit.
- **Subidas e descidas**: mudar a cota do eixo («Eixo a») enquanto se desenha faz ali um troço vertical, com uma
  curva em cada ponta, e o desenho continua à nova altura (como no Revit, ao mudar o deslocamento a meio).
  - O mesmo com a ferramenta Conduta: a curva de uma conduta retangular fica com a secção na posição certa
    (os 30 cm continuam de lado).
- **Curvas em qualquer direção**: as curvas (`IfcPipeFitting` / `IfcDuctFitting` BEND) já não são só
  horizontais. Fazem-se no plano em que o tubo vira: para cima, para baixo ou ao longo da inclinação.
  - Comprimentos e quantidades medem-se ao longo do tubo.
  - Mudar o comprimento estica o tubo na sua direção, e o que vem a seguir acompanha. Mudar a cota leva o
    ramal todo.
- **Os tubos redondos desenham-se no papel**. Até aqui, numa planta ou num corte, um tubo abaixo do corte quase
  não aparecia: os seus lados são superfície lisa, sem arestas, e só se viam as pontas.
  - Agora os desenhos traçam o contorno das superfícies curvas tal como se veem: os dois lados de um tubo
    visto de cima e a curva pelo seu arco.
  - O mesmo vale para os pilares redondos e as paredes curvas nos alçados e cortes.
  - As curvas dos tubos já não mostram as arestas da malha.
- Testes:
  - sem janela: um tubo a 1 % (cotas, comprimento, inclinação, esticar ao longo dele; a seta e «1 %» na planta e
    no DXF); um tubo de queda e o coletor a partir do pé, ligados por uma curva com o volume certo; uma subida
    entre dois troços (duas curvas, tudo ligado, sobe junto); a subida de uma conduta retangular com a secção na
    posição certa; os lados de um tubo num desenho;
  - com a janela real: na planta, a ferramenta Tubo Ø100 a 1 % (dois cliques), a cota mudada a meio (uma subida),
    um tubo de queda (um clique) e o coletor a 2 % a partir do pé.

## 0.135.0 — 2026-10-23

Fase 6, início. Corrige o problema do teste do dono do projeto (22/10): «testei o duto, mas ele não apareceu».

- **A causa**: a ferramenta Conduta põe o eixo a 2,50 m do pavimento, por baixo da laje, como deve ser. A planta,
  porém, corta a 1,20 m e mostra só o que está abaixo do corte. Uma conduta desenhada na planta ficava acima do
  corte e não se via; só uma mensagem dizia para a ir ver no 3D.
- **Agora**, na planta, as tubagens e condutas do pavimento que ficam acima do corte (condutas, tubos, as suas
  curvas, as bocas de ar e as calhas de cabos) aparecem pelo contorno visto de cima, **a tracejado**, como se
  desenham numa planta.
  - Um clique nesse contorno seleciona-as; selecionadas, ficam na cor da seleção.
  - A mensagem ao desenhar diz que fica acima do corte e que se mostra a tracejado.
  - No papel (PDF, folhas, PNG, SVG) saem a tracejado. No DXF vão na camada **ACIMA**.
- Os tubos baixos (a 0,30 m, por omissão) continuam a ver-se como antes, e as vigas acima do corte também não
  mudam.
- Testes:
  - sem janela: uma conduta a 2,50 m entra na planta como contorno (o seu tamanho certo), um tubo a 0,30 m não,
    nem uma conduta de outro pavimento; no DXF, a camada ACIMA;
  - com a janela real, o teste do dono: na planta, a ferramenta Conduta com dois cliques; a conduta aparece a
    tracejado e um clique no contorno seleciona-a.

## 0.134.0 — 2026-10-23

Fase 5, passo 8 (fim): **vistas 3D nas folhas**. No painel Projeto, sobre a vista 3D ou uma vista 3D com nome,
há **Pôr na folha ▸**.

- Na folha, a vista 3D sai **desenhada em linhas**: uma axonometria (sem perspetiva), com as arestas escondidas
  pelo que está à frente tiradas, como num alçado.
  - Uma vista 3D com nome é vista do lado da sua câmara.
  - A vista 3D, que não guarda câmara, é vista de sudoeste, de cima.
- As categorias que a vista esconde ficam de fora. Escolhe-se a escala, arruma-se e exporta-se como as outras
  vistas, e fica sempre como o modelo está.
- A **Fase 5 fica feita**. Os alçados cardinais automáticos já existiam desde a 0.29.
- Testes:
  - sem janela:
    - a casa em linhas de sudoeste (nada cortado, a extensão), com menos linhas do que sem tirar as escondidas;
    - de uma câmara de nordeste, outro desenho;
    - uma vista que já não existe não dá nada;
    - guardada com a folha;
  - com a janela real: a vista 3D de uma casa com porta e janela posta numa folha nova, pintada como no papel.

## 0.133.0 — 2026-10-23

Fase 5, passo 8 (primeira parte): **vistas de pormenor**. Há uma ferramenta nova, **Pormenor**, no ambiente
Docs.

- Numa planta, num corte ou num alçado, dois cliques nos cantos do pedaço que se quer mostrar maior. Faz um
  pormenor («Pormenor 1», «Pormenor 2»…), à escala escolhida na barra: 1:5, 1:10, 1:20 (a de omissão) ou 1:50.
  As inferências funcionam, como nas cotas.
- Na vista de origem fica a **chamada**: um retângulo tracejado de cantos redondos e, no canto de cima à direita,
  uma bolha com o número. Aparece no ecrã e no papel.
  - Um clique na bolha diz qual é; um duplo clique mostra esse pedaço a encher a vista.
- No painel Projeto, em **Pormenores**, cada um tem **Pôr na folha ▸** e **Apagar**.
- Na folha, o pormenor é o desenho da vista de origem só dentro do retângulo, à sua escala, sempre como o modelo
  está:
  - leva o que é cortado e o que se vê, as cotas e o desenho 2D que lá estão, e os níveis de um corte;
  - não leva o norte nem as marcas das outras vistas;
  - ocupa na folha o tamanho do retângulo.
- Mudar o nome a um corte leva os seus pormenores. Apagá-lo apaga-os, também das folhas. Tudo se guarda com as
  vistas e desfaz-se com Ctrl+Z.
- Testes:
  - sem janela:
    - o pormenor do canto de uma casa: o nome, o retângulo arrumado, a escala;
    - a chamada na planta;
    - só o que está dentro (a cota de dentro sim, a de fora não), a extensão, sem norte nem marcas;
    - o tamanho na folha (2 m a 1:20 = 100 mm);
    - um de um corte, com o corte renomeado e apagado;
    - gravados e lidos de novo; desfeito;
  - com a janela real: a ferramenta com dois cliques, a bolha na planta, o duplo clique que aproxima, e o
    pormenor numa folha nova, pintada como no papel.

## 0.132.0 — 2026-10-23

Fase 5, passo 7 (fim): **tabelas nas folhas**.

- No painel Tabelas, **Pôr numa folha ▸** põe a tabela que se está a ver numa folha que já existe ou numa nova.
  Pode ser uma categoria (as paredes, o quadro de áreas…) ou uma tabela própria.
- Na folha, a tabela aparece com os títulos das colunas a negro sobre cinzento, as linhas (os números alinhados à
  direita) e os totais por baixo. O nome fica por baixo, como o de uma vista.
- Tem o tamanho que precisa no papel (2 mm de letra), qualquer que seja a escala dos desenhos. Arruma-se, move-se
  e tira-se da folha como as vistas.
- Fica sempre como o modelo está: muda quando as paredes mudam, ou quando se muda a tabela própria. Sai também nos
  PDF, PNG, SVG e na impressora.
- Testes:
  - sem janela: a tabela própria agrupada por pavimento como tabela da folha (títulos, linhas escritas como no
    painel, totais), o seu tamanho no papel, a das paredes, uma que já não existe, guardada com a folha;
  - com a janela real: uma tabela própria posta numa folha nova pelo painel, e a das paredes posta na mesma; a
    folha pintada como no papel.

## 0.131.0 — 2026-10-23

Fase 5, passo 7 (primeira parte): **tabelas próprias do projeto**. No painel Tabelas (Ctrl+T) há **Nova
tabela…**, **Editar…** e **Apagar**. Uma tabela própria tem:

- um **nome** e os **elementos** de que trata: paredes, lajes, pilares, portas, janelas, salas (áreas ou
  acabamentos) ou outros;
- as **colunas** que se querem, marcadas, pela ordem em que se arrastam;
- **colunas com fórmulas**: um nome e uma fórmula com as colunas de números, por exemplo «length * height»
  (comprimento × altura) ou «area * 1,10». Valem números com vírgula, + − * / e parênteses, round(x; casas), min,
  max e abs; mais nada é executado;
- **filtros**: só as linhas em que uma coluna é =, ≠, >, <, ≥, ≤ ou contém um valor;
- a coluna por que se **ordena** (e se do maior para o menor) e a coluna por que se **agrupa**. Agrupada, dá uma
  linha por valor com quantos são e as somas.

As tabelas próprias aparecem na lista do painel, depois das categorias («Tabela: Paredes compridas»), e mostram os
totais das suas colunas. Como nas outras, os nomes, comprimentos e alturas escrevem-se nas células e «Exportar
CSV…» dá a tabela tal como se vê. Guardam-se com as vistas no ficheiro ao lado do IFC, vão com elas no trabalho de
equipa, e criar, mudar ou apagar uma é um passo de Ctrl+Z.

- Testes:
  - sem janela:
    - as fórmulas (vírgula decimal, «;» entre argumentos, coisas perigosas recusadas);
    - uma tabela de paredes com colunas, uma fórmula, um filtro, ordenada e agrupada por pavimento;
    - gravada e lida de novo; desfeita;
  - com a janela real: «Nova tabela…» com uma fórmula, um filtro e a ordem do maior para o menor (2 linhas, a de
    8 m primeiro, 22,40 na fórmula); Ctrl+Z tira-a.

## 0.130.0 — 2026-10-23

Fase 5, passo 6 (fim): **modelos de legenda**. Cada folha escolhe o seu na barra da folha («Modelo da legenda»), e o
assistente «Folhas por pavimento…» também:

- **Completo**: o de sempre, em baixo à direita;
- **Compacto**: mais pequeno, só com a obra, o desenho, a escala, a data e o número;
- **Faixa lateral**: uma coluna a toda a altura do lado direito, com as casas em baixo. Dá mais lugar aos
  desenhos compridos; as revisões e os campos próprios ficam dentro da coluna.

A área onde as vistas se dispõem ajusta-se ao modelo de cada folha. O duplo clique na legenda, para a preencher,
funciona em todos. Guarda-se com a folha e desfaz-se com Ctrl+Z.

- Testes:
  - sem janela:
    - onde fica cada modelo e o lugar que deixa às vistas (o completo como antes);
    - o modelo guardado com a folha (um modelo desconhecido volta a completo);
    - feito pelo assistente;
    - um desenho alto cabe numa escala igual ou maior ao lado da faixa;
  - com a janela real:
    - o assistente com a faixa lateral, pintada como no papel com uma revisão e um campo próprio;
    - a folha aberta e mudada para compacto na barra.

## 0.129.0 — 2026-10-23

Fase 5, passo 6 (continuação): **exportar a vista em DXF**, para o AutoCAD e os outros programas de CAD.

- **Ficheiro ▸ Exportar vista em DXF…**: o corte ou o alçado que se está a ver; senão, a planta do pavimento
  ativo, como no PDF.
- O ficheiro é DXF R12, a versão que todos os programas de CAD leem, e as medidas vão em metros.
- Cada tipo de linha vai na sua camada:
  - **CORTE**: o que é cortado, em polilinhas fechadas;
  - **VISTO**: o que se vê para lá do corte;
  - **TRAMAS**: as tramas de linhas, com o estilo gráfico do projeto;
  - **SIMBOLOS**: as portas;
  - **SUBJACENTE**: o pavimento que se vê por baixo;
  - **COTAS**: as linhas, os traços e os valores; também as angulares;
  - **DESENHO** e **TEXTOS**: o desenho 2D;
  - **SALAS**: as etiquetas;
  - **GRELHA**: a grelha estrutural;
  - **MARCAS**: os cortes, os alçados e os níveis.
- Os textos e as marcas têm o tamanho de papel à escala da vista nas folhas (sem escala, 1:100).
- As tramas cheias (o betão…) vão só com o contorno, porque o DXF R12 não tem tramas.
- Testes:
  - sem janela: a planta de uma casa com porta, sala, cota, texto, região tracejada e corte, lida de volta do
    ficheiro (códigos e valores do princípio ao fim, a versão, as camadas, cada coisa na sua camada, os textos,
    as medidas em metros);
  - com a janela real: a planta com as fachadas cotadas exportada pelo menu, e as linhas lidas de volta do
    ficheiro pintadas, para ver.

## 0.128.0 — 2026-10-23

Fase 5, passo 6 (continuação): **conjuntos de folhas, publicar, PNG, SVG e imprimir**.

- **Conjuntos**: no painel Projeto, sobre uma folha, **Conjuntos…**. Marcam-se os conjuntos em que ela entra
  («Licenciamento», «Execução»…) e escreve-se o nome de um novo. Uma folha pode estar em vários. É um passo de
  Ctrl+Z.
- **Publicar o conjunto** ▸ (sobre «Folhas»): as folhas desse conjunto, pela sua ordem, num só PDF com o nome
  do conjunto.
- **Exportar em PNG…** e **em SVG…**, de uma folha ou de todas:
  - cada folha num ficheiro, na pasta escolhida, com o número e o nome («01 Planta.png»);
  - o PNG é uma imagem a 150 ppp;
  - o SVG é um desenho em vetores (linhas e enchimentos), que se abre noutros programas.
- **Imprimir…**, de uma folha ou de todas: a janela da impressora e depois cada folha numa página, no seu papel
  (A3 a A0), deitado como as folhas.
- Testes:
  - sem janela: os conjuntos (nomes limpos e sem repetir, as folhas de um conjunto), gravados e desfeitos;
  - com a janela real: a folha da planta posta no conjunto «Licenciamento» pelo diálogo; publicado (um PDF de
    uma página); as duas folhas em PNG e em SVG; impressas para uma impressora PDF (duas páginas).

## 0.127.0 — 2026-10-23

Fase 5, passo 6 (primeira parte): **folhas por pavimento, numeração, campos próprios e revisões**.

- **Folhas por pavimento…** (menu Ficheiro, e no painel Projeto, sobre «Folhas»): faz de uma vez uma folha para
  cada pavimento escolhido, com a sua planta.
  - Vêm todos escolhidos à partida, e escolhe-se o papel.
  - Se se quiser, junta uma folha com os quatro alçados e outra com os cortes.
  - As folhas que já existem ficam. É um passo de Ctrl+Z, e abre a primeira das folhas novas.
- Na **Legenda…**:
  - **campos próprios do projeto**: tantos quantos se quiser, cada um com um nome e um texto («Processo:
    123/2026»). Aparecem em todas as folhas, por cima da legenda;
  - **numeração das folhas**: um prefixo e quantos algarismos («A-01», «A-001»). Uma folha com número próprio
    fica com o seu;
  - para cada folha, as suas **revisões**: código, data e descrição. «Juntar» dá a letra seguinte (A, B, C…) e a
    data de hoje. Aparecem numa tabela por cima da legenda, a mais recente em cima, e a última vai junto ao número
    («A-01 · B»).
- As vistas de uma folha deixam livre o espaço dessas linhas por cima da legenda.
- Tudo se guarda com as folhas no ficheiro ao lado do IFC e desfaz-se com Ctrl+Z.
- Testes:
  - sem janela:
    - as folhas por pavimento (três, num passo de desfazer);
    - a numeração com prefixo e três algarismos;
    - os campos próprios e as revisões limpos (sem nome, ou vazios, saem);
    - nos textos da legenda;
    - o espaço guardado por cima dela;
    - gravado e lido de novo; desfeito;
  - com a janela real: o assistente com os alçados (três folhas) e a legenda da primeira com prefixo, um campo
    próprio e uma revisão, pintado como no papel.

## 0.126.0 — 2026-10-23

Fase 5, passo 5: **estilos gráficos**. No menu Vista há **Estilos gráficos…**, para todo o projeto: como os
desenhos saem no papel (PDF e folhas).

- **Cada material cortado** tem uma linha: betão, alvenaria, madeira, isolamento, gesso e reboco, e outros. O
  material de cada camada diz o seu tipo, no editor de materiais. Em cada linha muda-se:
  - o **padrão**: cheio, linhas, linhas cruzadas ou nada;
  - a **cor**;
  - o **ângulo**;
  - o **espaçamento** em mm de papel.
  - Ao lado, uma amostra de como imprime.
- **As canetas**: a espessura do que é cortado, do que se vê para lá do corte, das tramas, das cotas e do
  desenho 2D.
- «Repor os de sempre» volta aos de antes (que continuam a ser os de omissão).
- Mudar os estilos é um passo de Ctrl+Z. As vistas e as folhas desenham-se de novo. Guardam-se com as vistas no
  ficheiro ao lado do IFC e vão com elas no trabalho de equipa.
- **Tipos de linha no Desenho 2D**: a barra da ferramenta tem **Linha** (contínua, tracejada, traço-ponto,
  oculta) e **Espessura** (a do projeto, ou de 0,13 a 0,70 mm). Vêem-se no ecrã e no papel.
- Testes:
  - sem janela:
    - as tramas de sempre;
    - uma mudada (alvenaria cruzada a vermelho), e valores sem sentido limpos;
    - uma caneta;
    - o estilo no desenho da planta, e uma linha tracejada de 0,35 mm no papel;
    - gravado e lido de novo; desfeito;
  - com a janela real: o diálogo (alvenaria cruzada e rosa, corte a 0,70), uma linha tracejada de 0,35 desenhada
    na planta, a planta no papel com eles, e Ctrl+Z duas vezes volta ao de sempre.

## 0.125.0 — 2026-10-23

Fase 5, passo 4: **salas no papel e quadros de áreas e de acabamentos**.

- **Etiquetas das salas no papel** (PDF e folhas): em cada sala da planta, o nome em maiúsculas com o número, e
  a área por baixo. Ficam no mesmo sítio que no ecrã e têm sempre o mesmo tamanho no papel, qualquer que seja a
  escala. Com região de recorte, só as salas de dentro.
- **Tabelas** (Ctrl+T), duas categorias novas:
  - **Salas: quadro de áreas**: número, nome, pavimento, área, perímetro e pé-direito, por pavimento e número; no
    fim, quantas salas e a área total;
  - **Salas: quadro de acabamentos**: número, nome, pavimento, piso, paredes, teto e área;
  - nas duas, o número, o nome e os acabamentos escrevem-se na célula: é o mesmo que no painel Propriedades, um
    passo de Ctrl+Z cada;
  - «Agrupar por pavimento» dá uma linha por pavimento, com quantas salas tem e a área;
  - «Exportar CSV…» funciona como nas outras.
- Testes:
  - sem janela:
    - uma casa dividida em duas salas: o quadro de áreas (a ordem, as áreas, o total);
    - o de acabamentos (os acabamentos postos);
    - as células que se podem mudar;
    - uma linha por pavimento;
    - as etiquetas no papel, dentro das salas;
  - com a janela real:
    - os dois quadros;
    - «Mosaico» escrito no piso de uma sala muda-lhe o acabamento, e Ctrl+Z tira-o;
    - a planta no papel com as duas etiquetas.

## 0.124.0 — 2026-10-23

Fase 5, passo 3 (fim): **estilo das cotas**. No menu Vista há **Estilo das cotas…**, para todo o projeto:

- **altura do texto** no papel: 1,8 / 2,2 / 2,5 / 3,5 mm;
- **nas pontas da linha**: traço a 45° (o de sempre), seta ou ponto;
- **unidade**: metros («4,50»), centímetros («450») ou milímetros («4500»);
- **casas decimais**: ao mudar a unidade passa a 2 em metros e a 0 nas outras, e pode-se mudar à mão;
- o diálogo mostra como fica uma cota de 4,5 m.

Todas as cotas seguem o estilo, no ecrã, no papel e nos PDF: as lineares, as em cadeia, as automáticas e o
texto das angulares. As mensagens da ferramenta Cota dizem o valor com a unidade do estilo. Mudar o estilo é um
passo de Ctrl+Z. Guarda-se com as cotas no ficheiro ao lado do IFC e vai com as vistas no trabalho de equipa.

- Testes:
  - sem janela:
    - os valores em centímetros e milímetros, e as casas decimais;
    - um estilo com valores estranhos fica limpo;
    - mudado e desfeito;
    - no papel (texto e marca);
    - gravado e lido de novo;
  - com a janela real: o diálogo em centímetros, com setas e texto de 3,5 mm; as cotas da casa passam a
    «1020»; Ctrl+Z volta aos metros.

## 0.123.0 — 2026-10-23

Fase 5, passo 3 (continuação): **cotas automáticas de fachadas e de salas**. Duas ações novas no menu Vista e no
ambiente Docs, ao lado de «Cotar paredes».

- **Cotar fachadas**: à volta do edifício da planta do pavimento ativo, em cada um dos quatro lados, por fora da
  sua face mais saliente, até três filas:
  - a 0,80 m, todos os cantos desse lado e as ombreiras das suas portas e janelas;
  - a 1,40 m, só os cantos (quando há vãos e mais de dois cantos);
  - a 2,00 m, o comprimento total.
  - As cotas medem na horizontal (ou na vertical), mesmo com cantos a profundidades diferentes: cada linha de
    chamada vai do seu ponto à linha da cota, em esquadria.
  - Cada ponta agarra-se ao canto ou à ombreira e acompanha-os.
  - Outra vez: refaz-as (não as duplica).
- **Cotar salas**: em cada sala do pavimento, a largura e a profundidade de parede a parede. As linhas ficam a um
  quarto da sala do meio, longe do nome e da área.
- As **cotas com direção** (horizontais ou verticais) servem também para estas automáticas. Guardam-se como as
  outras e aparecem no ecrã, no papel e nos PDF.
- As marcas de alçado ficam agora para lá das cotas da planta, não por cima delas.
- Testes:
  - sem janela:
    - uma casa de 10 × 6 m com porta e janela na parede sul: 6 cotas a sul (a soma da cadeia é o total), 1 em
      cada outro lado, as distâncias das filas, a direção, as pontas agarradas;
    - a sala com 9,80 e 5,80;
    - no papel;
    - uma cota com direção entre pontos a profundidades diferentes;
  - com a janela real:
    - as duas ações (9 cotas nas fachadas; outra vez, as mesmas 9; 2 na sala);
    - o teste das cotas angulares deixa a ferramenta em linear (ela guarda o último tipo usado).

## 0.122.0 — 2026-10-23

Fase 5, passo 3 (primeira parte): **cotas em cadeia e angulares**. Na ferramenta Cota (C), a barra de opções
tem agora **Cota: Linear / Angular** (Tab muda) e, na linear, **Em cadeia**.

- **Em cadeia** (ligada por omissão):
  - depois de pôr uma cota, cada clique é o ponto seguinte da cadeia: uma cota do último ponto até ele, na mesma
    linha, como no Revit;
  - Esc (ou o botão direito) acaba a cadeia;
  - cada cota da cadeia agarra-se aos elementos como as outras e acompanha-os.
- **Angular**:
  - um clique no vértice, um num ponto de cada lado, e um onde fica o arco;
  - de quatro ângulos que as duas linhas fazem, o ângulo medido é o do lado onde se pôs o arco;
  - no ecrã e no papel: o arco com um traço a 45° em cada ponta, os lados prolongados até ele, o ângulo ao
    meio («90°», «22,5°»);
  - o vértice e os lados agarrados a uma parede acompanham-na quando ela se move.
- As cotas angulares guardam-se com as outras, no ficheiro ao lado do IFC.
- Testes:
  - sem janela:
    - o ângulo do lado do arco (60°, 120° do outro lado, 60° do lado oposto do vértice);
    - linhas paralelas sem ângulo;
    - a escrita dos ângulos;
    - a cota no papel;
    - o vértice a seguir a parede movida;
    - gravada e lida de novo;
  - com a janela real, na planta: os primeiros 3 m da fachada sul e, com mais um clique, a segunda cota da
    cadeia na mesma linha; Tab e a cota angular no canto: 90°.

## 0.121.0 — 2026-10-23

Fase 5, passo 2: **símbolos das vistas**. Calculam-se sempre do modelo e das vistas (não se guardam), por isso
estão sempre certos.

- **Nas plantas**:
  - **cada corte** tem a sua linha (traço-ponto) através do edifício, 4 mm de papel para lá dele de cada lado;
  - em cada ponta, uma **cabeça**: um círculo com a referência do corte («1» para «Corte 1», «A» para
    «Corte A»; outro nome dá as primeiras letras) e uma seta para onde o corte olha;
  - **os quatro alçados** têm a sua marca a 16 mm de papel do edifício, do lado de onde são vistos: a letra
    (N, S, E, O) e a seta virada para o edifício;
  - **duplo clique** numa cabeça abre esse corte ou alçado, como no Revit; um clique só diz qual é;
  - **no papel**, a seta do **norte** ao lado do canto de cima à direita (o norte do projeto: para cima, +Y).
- **Nos cortes e alçados**, cada pavimento tem a sua **marca de nível**:
  - uma linha traço-ponto através do desenho;
  - na ponta direita, um triângulo e a cota com o nome («+3,00  Piso 1», «±0,00  Térreo»).
- As medidas dos símbolos são as do papel, como no desenho à mão: as cabeças têm 4 mm de raio, a linha de nível
  passa 8 mm para lá do desenho. No ecrã multiplicam-se pela escala da vista.
- Os símbolos **não aumentam o desenho**: a escala que uma folha escolhe para a vista fica a mesma de antes. A
  legenda da vista desce para ficar abaixo das marcas.
- Com região de recorte, a linha do corte é cortada por ela e as marcas de alçado de fora não aparecem.
- Testes:
  - sem janela:
    - a extensão do edifício;
    - a linha do corte (onde começa e acaba, a referência, para onde olha);
    - as marcas de alçado (onde ficam, as setas, a letra O);
    - as referências curtas e a escrita das cotas;
    - a planta no papel (as cinco marcas, o norte, a extensão);
    - o corte com os dois níveis;
  - com a janela real:
    - as seis cabeças na planta;
    - o duplo clique na marca Norte abre o alçado Norte, com os dois níveis;
    - a planta pintada como no PDF.

## 0.120.0 — 2026-10-23

Fase 5, passo 1: **desenho 2D nas vistas**. Há uma ferramenta nova, **Desenho 2D**, no ambiente Docs, ao lado das
cotas.

- Numa planta, num corte ou num alçado desenha-se (Tab muda o que se desenha):
  - **linha**: dois cliques, ou o comprimento escrito depois do primeiro;
  - **polilinha**: cliques; Enter acaba, um clique no primeiro ponto fecha;
  - **retângulo**: dois cantos opostos, ou «largura;altura» escrito;
  - **círculo**: o centro e um ponto do círculo, ou o raio escrito;
  - **arco**: o início, o fim e um ponto por onde passa;
  - **região com trama**: os cantos, Enter ou o primeiro canto fecha; trama diagonal, cruzada, cheia (cinzento)
    ou sem trama;
  - **texto**: um clique onde começa, depois escreve-se no campo Medidas e Enter; a altura no papel escolhe-se
    (1,8 / 2,5 / 3,5 / 5 mm).
- As inferências funcionam como nas cotas: o canto de uma parede, o fim de uma linha já desenhada…
- Delete tira o último ponto clicado.
- O desenho fica **só nessa vista**, como as cotas: vê-se no ecrã e no papel (PDF e folhas), com a trama ao
  espaçamento certo para a escala.
- Com Selecionar, um clique numa linha, num bordo de região ou num texto seleciona-o (Shift junta). Depois:
  - Delete apaga;
  - Mover move-o; com cópia, copia-o, e as séries também funcionam.
- Mudar o nome a um corte leva os seus desenhos; apagar o corte apaga-os.
- Tudo desfaz com Ctrl+Z.
- Guarda-se no ficheiro ao lado do IFC, com as cotas (o IFC não muda), e vai com as vistas no trabalho de equipa.
- O campo Medidas aceita agora letras, maiúsculas e espaços enquanto se escreve um texto.
- Testes:
  - sem janela:
    - as formas no referencial da vista (o retângulo, o raio do círculo, o arco pelos três pontos, a área da
      região, a trama dentro dela);
    - no papel, só na sua vista (planta e corte) e a contar para o tamanho do desenho;
    - desfazer e refazer, apagar e mover;
    - gravado e lido de novo; com o corte renomeado e apagado;
  - com a janela real, na planta: uma linha, Tab cinco vezes e uma região, Tab e o texto «Sala 1» escrito;
    a linha selecionada e apagada; a planta no papel e em PDF.

## 0.119.0 — 2026-10-23

Fase 4, passo 8 (resto): **revestimentos de parede, luminárias, rasgo e sanca no teto**. Há duas ferramentas
novas no ambiente BIM, ao lado do Ralo e da Abertura na cobertura.

- **Revestimento de parede**:
  - passa-se o rato sobre uma parede e vê-se, a azul, a face onde o revestimento vai ficar; um clique põe-no lá;
  - na planta, a face é a do lado onde está o cursor;
  - **acabamento**: azulejo (1 cm), reboco (2 cm) ou pedra (3 cm);
  - **até à altura**: 2,10 m por omissão (a altura das portas), desde a base da parede;
  - fica recortado nas portas, janelas e vãos da parede;
  - **acompanha a parede**, como no Revit:
    - a parede mais comprida, movida, rodada ou espelhada: o revestimento vai com ela;
    - uma porta posta: o revestimento é recortado;
    - a parede dividida: as duas partes ficam revestidas; duas paredes unidas: fica um só revestimento;
    - a parede copiada: a cópia leva o seu próprio revestimento;
    - a parede apagada: o revestimento vai com ela;
  - no painel Propriedades mudam-se o acabamento e a altura; vêem-se a parede e a área (sem os vãos).
- **Luminária**:
  - um clique na sala põe uma luminária embutida no teto que estiver por cima (sob uma sanca, na sanca);
  - sem teto, fica a 2,60 m do pavimento;
  - **painel 60 × 60** ou **foco de encastrar**.
- **Teto**, duas opções novas (na barra da ferramenta e no painel Propriedades):
  - **rasgo junto às paredes**: uma folga de sombra à volta (0 a 20 cm);
  - **sanca**: uma faixa mais baixa à volta, com a largura e a descida que se quiserem (30 cm por omissão).
- No IFC:
  - revestimento: `IfcCovering` CLADDING, com o material do acabamento, ligado à parede por
    `IfcRelCoversBldgElements`; `Qto_CoveringBaseQuantities` (área bruta e área sem os vãos);
  - luminária: `IfcLightFixture` POINTSOURCE;
  - teto com sanca: uma peça a mais, a faixa descida; a área conta as duas.
- Testes:
  - sem janela:
    - o azulejo numa face de uma parede de 5 m (classe, ligação à parede, material, posição, área);
    - recortado numa porta;
    - a parede mais comprida, movida, copiada, dividida e unida, apagada;
    - mudado para pedra a 1,20;
    - o teto com rasgo e sanca (a cota da sanca, a área, as peças), uma luminária no meio e outra sob a sanca;
    - a luminária espelhada; o IFC válido;
  - com a janela real: o azulejo com um clique na face de dentro de uma parede, na planta; a luminária com um
    clique na sala.

## 0.118.0 — 2026-10-23

Fase 4, passo 8 (primeira parte): **tetos**. Há uma ferramenta nova, **Teto**, no ambiente BIM ao lado da
Cobertura.

- O contorno faz-se de três maneiras (Tab muda):
  - **por sala**: um clique dentro das paredes de uma sala usa as faces de dentro delas; um pilar fica como furo;
  - **retângulo**;
  - **polígono**.
- **Altura do teto**: 2,60 m acima do pavimento por omissão.
- **Acabamento**:
  - **contínuo**: gesso cartonado de 12,5 mm;
  - **placas 60 × 60**: a grelha começa no canto de baixo à esquerda, as placas dos bordos são cortadas como na
    obra, e as juntas de 6 mm vêem-se.
- No painel Propriedades mudam-se o acabamento e a altura, e vê-se a área.
- Move-se, copia-se e espelha-se.
- No IFC:
  - `IfcCovering` CEILING de gesso, com corpo próprio;
  - `Qto_CoveringBaseQuantities` (área, espessura) e `Pset_CoveringCommon`.
- Testes:
  - sem janela:
    - o teto de uma sala com um pilar (o furo, a área, o volume);
    - em placas (as juntas tiram volume, mais de 150 placas);
    - a 2,50;
    - espelhado;
    - IFC válido;
  - com a janela real: o teto com um clique dentro da sala, mudado para placas no painel.

## 0.117.0 — 2026-10-23

Fase 4, passo 7: **fachada de vidro**. Há uma ferramenta nova, **Fachada de vidro**, no ambiente BIM ao lado da
Parede.

- **Desenhar**: como uma parede, pela sua linha — um clique no início e outro no fim, ou o comprimento
  digitado.
- **Na barra contextual**:
  - a altura (2,80 m por omissão);
  - **montantes a cada** (no máximo 1,50 m);
  - **travessas a cada** (no máximo 1,00 m).

  Montantes e travessas saem a espaços iguais, com um painel de vidro em cada célula.
- No painel Propriedades mudam-se o comprimento (o início fica), a altura e os dois espaçamentos.
- Move-se, roda, copia-se e espelha-se.
- No IFC:
  - `IfcCurtainWall` com corpo próprio (montantes 5 × 15 cm, travessas 12 × 5 cm, vidro de 24 mm);
  - um conjunto de materiais (`IfcMaterialConstituentSet`) de alumínio (o caixilho) e **vidro** (material novo do
    catálogo);
  - `Qto_CurtainWallQuantities` e `Pset_CurtainWallCommon` (IsExternal).
- Ainda não: os tipos de painel por célula (opaco, porta) e a fachada embutida numa parede.
- Testes:
  - sem janela: 6 × 3 m (5 montantes, 4 travessas, 12 painéis, os materiais, as quantidades); 7,5 m de
    comprimento (5 vãos); movida e espelhada; IFC válido;
  - com a janela real: a fachada com o comprimento digitado e os montantes reespaçados no painel.

## 0.116.0 — 2026-10-23

Fase 4, passo 6 (fim): **escadas em V e circulares**. Com a 0.114 e a 0.115, o passo 6 fica feito.

- A ferramenta Escada tem mais duas formas:
  - **em V**: dois lanços opostos lado a lado, sem folga entre eles, e o patamar a todo o comprimento;
  - **circular (caracol)**:
    - os degraus são cunhas à volta de uma coluna, com espelhos abertos;
    - o cobertor mede-se na linha de passagem (o meio dos degraus);
    - a largura vai da coluna à borda de fora;
    - a viragem escolhe o sentido.
- As **guardas «nos lados de uma escada»** acompanham a borda de fora de uma escada circular, a subir com os
  degraus.
- Espelhada, uma escada circular passa a rodar para o outro lado.
- No IFC:
  - a escada circular é `SPIRAL_STAIR`, com a coluna (`IfcCircleProfileDef`) e cada degrau com arcos
    verdadeiros (`IfcIndexedPolyCurve` com `IfcArcIndex`);
  - a em V é `HALF_TURN_STAIR`.
- Testes:
  - sem janela: a em V (2 m de largura em tudo); a circular (a coluna à altura do desnível, os 15 degraus, dentro
    do raio, o Pset); a sua guarda; IFC válido;
  - com a janela real: a escada circular com dois cliques e a guarda à volta dela.

## 0.115.0 — 2026-10-23

Fase 4, passo 6 (continuação): **guarda-corpos**. Há uma ferramenta nova, **Guarda**, no ambiente BIM ao lado da
Escada. Tab muda a maneira de a fazer:

- **por um caminho**: clicam-se os pontos e Enter termina; Delete apaga o último;
- **à volta de um vazio**: um clique numa laje junto de um furo ou de uma abertura feita nela, e a guarda dá-lhe
  a volta, fechada, no topo da laje;
- **nos lados de uma escada**: um clique na escada põe uma guarda de cada lado de cada lanço, a 90 cm dos
  focinhos, inclinada com eles.

Estilos e medidas:
- três **estilos**: barras verticais (com 11 cm no máximo entre elas), vidro, barras horizontais;
- a **altura** muda-se na barra contextual (1,00 m por omissão);
- os prumos ficam nos cantos e a 1,20 m no máximo uns dos outros;
- no painel Propriedades mudam-se o estilo e a altura, e vê-se o comprimento.

Move-se, copia-se e espelha-se.

No IFC:
- `IfcRailing` GUARDRAIL com corpo próprio (prumos, corrimão, barras ou vidro);
- o material é aço galvanizado;
- `Pset_RailingCommon.Height` e `Qto_RailingBaseQuantities.Length`.

Corrigido: mudar a forma de uma escada no painel (por exemplo de L para U) mudava o desenho, mas não a classe
`PredefinedType` no IFC. O IfcOpenShell esvazia o dicionário de propriedades que lhe é passado; o programa passa-lhe
agora sempre uma cópia, o que protege também as outras edições de parâmetros.

Testes:
- sem janela:
  - uma guarda por um caminho (o comprimento, a altura) que passa a vidro;
  - as duas guardas de uma escada (inclinadas, 90 cm acima);
  - uma à volta de uma abertura numa laje (fechada, no topo);
  - espelhada;
  - IFC válido;
- com a janela real: o caminho com três cliques e Enter, as guardas da escada, o vidro no painel.

## 0.114.0 — 2026-10-23

Fase 4, passo 6 (primeira parte): **escadas** reta, em L e em U, com patamar. Há uma ferramenta nova,
**Escada**, no ambiente BIM.

- **Desenhar**: um clique no meio do primeiro degrau, no chão, e outro para o lado onde sobe. Antes do segundo
  clique vê-se a planta da escada.
- **Na barra contextual**:
  - a forma (reta, em L, em U);
  - a viragem (à esquerda ou à direita);
  - a largura (1,00 m por omissão);
  - o cobertor (28 cm por omissão);
  - o desnível (por omissão, até ao pavimento de cima);
  - o tipo (o material e a espessura da laje da escada).
- **Os espelhos calculam-se** pelo desnível, iguais e com 18 cm no máximo. Mostram-se com o «2 espelhos +
  cobertor» (a regra de Blondel, à volta de 63 cm).
- Em L e em U:
  - o patamar fica a meio, com a largura da escada;
  - em U, os dois lanços têm 10 cm entre eles.
- No painel Propriedades mudam-se a forma, a viragem, a largura, o cobertor e o desnível. Vêem-se os espelhos e
  o Blondel.
- Move-se, roda e copia-se. **Espelhada**, a viragem passa para o outro lado.
- No IFC:
  - `IfcStair` (STRAIGHT_RUN_STAIR, QUARTER_TURN_STAIR, HALF_TURN_STAIR) com corpo próprio;
  - cada lanço é o seu lado (os degraus e a laje por baixo) extrudido pela largura, e o patamar é uma placa;
  - o lanço apoia 10 cm no patamar ou no pavimento a que chega;
  - `Pset_StairCommon` com os espelhos, os cobertores, a altura do espelho, o cobertor e a espessura.
- Testes:
  - sem janela:
    - a escada reta de 2,80 (16 espelhos de 17,5 cm, o comprimento, o volume, o Pset);
    - a em L e a em U (as medidas);
    - a viragem mudada e espelhada;
    - IFC válido;
  - com a janela real: a escada em L até ao pavimento de cima (17 espelhos), o painel e a mudança para U.

## 0.113.0 — 2026-10-23

Fase 4, passo 5 (continuação): **cobertura a partir de uma laje ou de um esboço, ralos e aberturas**.

- A ferramenta Cobertura tem a forma **A partir de uma laje ou face**:
  - um clique numa laje, ou numa face horizontal de um esboço, faz a cobertura com o contorno dela;
  - a cobertura assenta por cima, sem se misturar com a laje;
  - é a cobertura plana sobre um piso, e a cobertura por esboço.
- **Ralo** (ferramenta nova): um clique numa cobertura põe um ralo no topo dela (`IfcWasteTerminal`
  ROOFDRAIN). Move-se, copia-se e espelha-se como os outros elementos.
- **Abertura (cobertura / laje)** (ferramenta nova):
  - dois cliques numa cobertura ou numa laje dão um retângulo, ou digitam-se as medidas («1;0,8»);
  - abre-se um buraco de alto a baixo, para uma claraboia ou um atravessamento (`IfcOpeningElement`);
  - a abertura vai com a cobertura quando esta se move.
- O botão «Ligar o topo» diz agora «laje / cobertura».
- Testes:
  - sem janela:
    - a cobertura plana feita do contorno de uma laje;
    - o ralo no topo;
    - a abertura numa cobertura de duas águas (o volume tirado), que continua cortada depois de a cobertura
      ser movida;
    - IFC válido;
  - com a janela real: a cobertura sobre a laje, o ralo e a abertura com os cliques.

## 0.112.0 — 2026-10-23

Fase 4, passo 5 (continuação): **o topo das paredes e pilares ligado à cobertura**.

- **Ligar o topo à laje** passa a funcionar também com uma cobertura. Selecionam-se as paredes ou pilares e a
  cobertura:
  - cada parede fica com o **topo pela face de baixo da cobertura**, ao longo dela: numa cobertura de duas
    águas, as paredes das pontas ficam em **empena** (um perfil de cinco cantos), as compridas ficam direitas
    sob o beirado; sob um rincão, o perfil segue-o;
  - um pilar sobe até à água por cima dele.
- **Acompanham a cobertura**: com outra inclinação, outra forma ou outra cota, as paredes e os pilares
  ajustam-se no mesmo passo de desfazer. Uma parede movida para debaixo de outra parte da cobertura também.
- No painel Propriedades, o Topo mostra «Cobertura … (face de baixo)». Escolher um pavimento ou «não ligado»
  solta-os.
- Por dentro: o perfil (0.109) é calculado onde a linha da parede cruza os contornos das águas (rincões,
  cumeeira, beirado). O gancho no fim de cada comando é o mesmo das lajes (0.106).
- Testes:
  - sem janela: as quatro paredes e um pilar sob uma cobertura de duas águas (duas empenas, as alturas certas);
    a cobertura mais inclinada (acompanham); IFC válido;
  - com a janela real: o botão com a cobertura selecionada, as empenas e o painel.

## 0.111.0 — 2026-10-23

Fase 4, passo 5 (primeira parte): **coberturas**. Há uma ferramenta nova, **Cobertura**, no ambiente BIM ao lado
da Laje.

- O contorno faz-se de três maneiras (Tab muda):
  - **pelas paredes**: um clique dentro de paredes fechadas usa a linha de fora delas;
  - **retângulo**;
  - **polígono**.
- A **forma** escolhe-se na barra contextual:
  - **plana**;
  - **uma água**: sobe a partir do primeiro lado;
  - **duas águas**: a cumeeira corre ao longo do lado mais comprido;
  - **quatro águas**: com os rincões e a cumeeira.
- Na barra contextual estão também a **inclinação** (de 5° a 45°), o **beirado** (quanto sai das paredes) e o
  tipo (as camadas e a espessura de um tipo de laje).
- A cobertura **assenta no topo das paredes** debaixo dela, ou a 2,80 m do pavimento se não houver paredes.
  O beirado fica mais baixo, na mesma inclinação.
- No painel Propriedades mudam-se a forma, a inclinação, o beirado e a cota sobre as paredes, e vêem-se a área
  inclinada e a área em planta.
- Move-se, roda, copia-se e **espelha-se** como os outros elementos. Aparece no painel Projeto em «Coberturas».
- No IFC:
  - `IfcRoof` (FLAT_ROOF, SHED_ROOF, GABLE_ROOF, HIP_ROOF) com corpo próprio;
  - cada água é uma placa inclinada extrudida a direito para baixo, por isso as águas encontram-se certinhas
    nos rincões e na cumeeira;
  - as camadas do tipo, `Qto_RoofBaseQuantities` (área inclinada, área em planta) e `Pset_RoofCommon`
    (IsExternal).
- Ainda não:
  - coberturas inclinadas sobre contornos com cantos para dentro (em L): o programa recusa e explica; plana
    já se faz;
  - ralos, aberturas e coberturas por extrusão: ficam para os passos seguintes.
- Testes:
  - sem janela:
    - as águas de um retângulo (quatro águas: dois trapézios e dois triângulos; duas águas; uma água;
      a cumeeira);
    - a cobertura de quatro águas sobre uma casa (a cumeeira, a face de baixo do beirado, o volume, as
      quantidades);
    - mudada para duas águas e plana, movida;
    - o L recusado inclinado e aceite plano;
    - IFC válido;
  - com a janela real: a cobertura feita com um clique dentro das paredes, mudada no painel e desfeita.

## 0.110.0 — 2026-10-23

Fase 4, passo 4 (primeira parte): **vãos — bandeira, marcas e vão sem caixilho**.

- **Porta com bandeira** (o kit porta + bandeira):
  - o catálogo traz «Porta 80×210 + bandeira 50»;
  - no editor de tipos, as portas têm o campo **Bandeira (altura)**;
  - a porta desenha-se com a travessa e o vidro fixo por cima da folha;
  - o tipo guarda a bandeira, por isso a porta continua igual quando muda de parede ou de tamanho.
- **Marcas**:
  - cada porta recebe a sua marca ao ser posta (P1, P2…), e cada janela também (J1, J2…);
  - uma cópia recebe a marca seguinte;
  - a marca vê-se e muda-se no painel Propriedades («Marca»);
  - **Numerar portas e janelas** (menu BIM, ou a barra contextual com portas ou janelas selecionadas) numera
    tudo de novo, pavimento a pavimento, pela ordem de leitura da planta (de cima para baixo, da esquerda para a
    direita);
  - no IFC, a marca vai no `Tag` do elemento.
- **Vão sem caixilho**: nas ferramentas Porta e Janela, «Só o vão (sem caixilho)» abre na parede o buraco do
  tamanho do tipo, sem porta nem janela (`IfcOpeningElement` OPENING). Depois muda-se como os outros vãos, com
  Empurrar/Puxar nos lados.
- Testes:
  - sem janela:
    - a porta com bandeira (50 cm mais alta que a normal, o tipo com a bandeira);
    - as marcas P1, P2, J1 e a da cópia;
    - numerar pela ordem de leitura;
    - uma marca escrita à mão;
    - o vão sem caixilho (o volume tirado à parede);
    - IFC válido;
  - com a janela real: a porta com bandeira e a marca P1 no painel, o vão sem caixilho, o botão Numerar.

## 0.109.0 — 2026-10-23

Fase 4, passo 3 (fim): **editar o perfil da parede**, como o «Editar perfil» do Revit. Com a 0.102 a 0.108, o
passo 3 (paredes) fica feito.

- Com uma parede reta selecionada, a barra contextual (e o painel Propriedades) mostra **Editar perfil**:
  - o alçado da parede aparece com pegas nos cantos, na face que se vê;
  - um clique pega num canto e o seguinte pousa-o no plano da parede; os cantos alinham-se com os outros;
  - a pega no meio de um lado acrescenta um canto;
  - com um canto pegado, Delete tira-o;
  - assim fazem-se empenas, topos em degraus e recortes.
- A altura da parede passa a ser o ponto mais alto do perfil. Se a parede ficar mais comprida ou mais alta, o
  perfil estica na mesma proporção.
- As portas e janelas têm de caber no perfil: o programa recusa um perfil que corte uma.
- «Parede simples» na barra contextual volta ao retângulo.
- Cada mudança é um passo de desfazer.
- No IFC, o corpo é o perfil no plano x-z da parede, extrudido pela espessura e centrado no eixo
  (`IfcArbitraryClosedProfileDef`). Qto_WallBaseQuantities leva a área do alçado e o volume.
- Ainda não: uma parede com perfil fica com as pontas a direito (os cortes em meia-esquadria dos cantos não se
  aplicam).
- Testes:
  - sem janela:
    - uma empena (o volume, a altura);
    - o perfil que corta a porta recusado;
    - a parede 2 m mais comprida (o perfil estica);
    - volta ao retângulo;
    - IFC válido;
  - com a janela real: o botão, as pegas e uma empena feita com dois cliques.

## 0.108.0 — 2026-10-23

Fase 4, passo 3 (continuação): **Espelhar**, como o «Espelhar – desenhar eixo» do Revit. Está em todos os
ambientes, ao lado de Mover e Rodar.

- Com coisas selecionadas, dois cliques dão o eixo de simetria, com os snaps e os alinhamentos (X / Y
  bloqueiam o eixo).
- Antes do segundo clique vê-se o eixo e o contorno da seleção já refletido.
- A seleção passa para o outro lado; com **Ctrl** (ou «Copiar» na barra contextual) ficam cópias espelhadas.
- O que se espelha:
  - **paredes retas**: as camadas ficam do lado certo, os cortes dos cantos trocam de ponta, as portas e
    janelas vão para o sítio refletido e as **portas trocam a mão** (à esquerda ↔ à direita). Nas cópias, os
    cantos entre as paredes copiadas refazem-se;
  - **paredes curvas** (o arco vira para o outro lado);
  - **pilares, estacas, rampas, sapatas** (as sapatas e estacas debaixo dos pilares vão com eles);
  - **vigas** (as duas pontas);
  - **lajes** (o contorno; uma laje com vãos ainda não);
  - **esboços**.
- O que ainda não se espelha (componentes, tubagens…) fica de fora, e o programa diz quantos.
- É um passo de desfazer.
- No IFC não há colocações espelhadas (não são válidas): cada elemento refaz-se pelo que o define.
- Testes:
  - sem janela: um canto de duas paredes com uma porta, um pilar, uma laje em L e uma viga copiados ao espelho
    (o sítio de cada um, o canto das cópias, a porta à direita, a área da laje, os originais intactos); um pilar
    espelhado no lugar; desfazer; IFC válido;
  - com a janela real: a cópia espelhada de uma parede com porta.

## 0.107.0 — 2026-10-23

Fase 4, passo 3 (continuação): **Alinhar**, como o AL do Revit. Está em todos os ambientes, ao lado de Mover
e Rodar.

- Primeiro clica-se na **referência**: um eixo da grelha, uma aresta, ou a face de uma parede. Ao passar com o
  rato, a referência aparece com o nome («Eixo A», «Aresta», «Face da parede»).
- Depois clica-se na **face** de uma parede ou de um pilar, paralela à referência. O elemento passa para lá: a
  face fica sobre a referência, e as paredes ligadas acompanham.
- Antes do clique vê-se quanto vai mover. Se a face não é paralela, o programa diz.
- A referência fica para as faces seguintes; o botão direito escolhe outra; Esc volta a Selecionar.
- Cada alinhamento é um passo de desfazer.
- Testes com a janela real: uma parede e um pilar alinhados pela face a um eixo da grelha.

## 0.106.0 — 2026-10-23

Fase 4, passo 3 (continuação): **ligar o topo das paredes e pilares a uma laje** (o «Attach Top» do Revit).

- Com paredes ou pilares selecionados, e uma laje com eles (Shift + clique), a barra contextual mostra
  **Ligar o topo à laje**:
  - o topo sobe ou desce até à face de baixo da laje;
  - a partir daí acompanha a laje: se ela for movida, ou mudar de tipo e ficar mais grossa (o topo da laje fica,
    a face de baixo desce), as paredes e os pilares ajustam a altura no mesmo passo de desfazer.
- No painel Propriedades, o **Topo** mostra «Laje … (face de baixo)», com o desvio:
  - escolher um pavimento ou «não ligado» solta-os da laje;
  - levantar a parede à mão muda o desvio, como com os pavimentos (0.73).
- Testes:
  - sem janela:
    - uma parede e um pilar ligados pelo topo a uma laje (chegam a ela);
    - a laje movida 50 cm e depois mais grossa (acompanham);
    - soltos (ficam);
    - desfazer;
    - IFC válido;
  - com a janela real: o botão na barra contextual, o painel e a laje movida.

## 0.105.0 — 2026-10-23

Fase 4, passo 3 (continuação): **juntar, ortogonalizar e soltar paredes**. São botões da barra contextual
quando há paredes selecionadas.

- **Juntar paredes**:
  - aparece com duas paredes selecionadas, em linha e de ponta a ponta (é o contrário de Dividir);
  - ficam uma só parede, que leva as portas, janelas e vãos da outra, no sítio onde estavam;
  - leva também a ligação da ponta de lá e as paredes que lhe batem de lado;
  - funciona mesmo que a segunda tenha sido desenhada ao contrário;
  - se os tipos, as bases ou as alturas forem diferentes, ou se as paredes não se tocarem, o programa explica
    porquê.
- **Ortogonalizar**: as paredes selecionadas que estão quase a direito (até 5°) rodam pelo meio até ficarem
  exatamente no eixo vermelho ou verde. As paredes ligadas a elas acompanham.
- **Soltar ligações** (o «Não permitir ligação» do Revit): as paredes selecionadas ficam onde estão, mas deixam
  de acompanhar as paredes onde ligam.
- Cada operação é um passo de desfazer.
- Testes:
  - sem janela:
    - juntar duas paredes (a porta e o canto passam para a primeira, a porta no mesmo sítio);
    - a segunda desenhada ao contrário;
    - afastadas e de outro tipo recusadas;
    - uma parede a 2° fica a direito e a ligada acompanha;
    - soltar uma ligação;
    - IFC válido;
  - com a janela real: os três botões na barra contextual.

## 0.104.0 — 2026-10-23

Fase 4, passo 3 (continuação): **dividir paredes e aparar / estender ao canto**, como no Revit. Ficam no
ambiente BIM, ao lado de Mover e Rodar.

- **Dividir parede**:
  - sobre uma parede reta vê-se onde fica a divisão e os dois comprimentos;
  - o meio da parede atrai o cursor;
  - um clique divide ali, ou digita-se a distância à ponta mais perto.
- Depois de dividir:
  - as duas partes ficam com o tipo, as propriedades, a base e o topo da parede;
  - cada porta, janela ou vão fica com a parte em que está;
  - não se divide a meio de uma porta: o programa explica porquê;
  - a ligação na ponta da parede, e as paredes que lhe batem de lado depois do ponto, passam para a parte nova;
  - num grupo, todas as cópias se dividem.
- **Aparar / estender ao canto**:
  - um clique numa parede, do lado que fica, e outro numa segunda parede;
  - antes do segundo clique vê-se onde fica o canto;
  - as duas vão até onde os eixos se cruzam e ligam-se como no desenho ponto a ponto: uma passa, a outra pára
    na face dela; noutros ângulos, em meia-esquadria;
  - paredes paralelas não fazem canto: o programa explica porquê.
- Cada operação é um passo de desfazer.
- A falha intermitente do teste da janela por distância (o mapa de seleção do ecrã ainda não estava refeito
  depois da porta) ficou resolvida no teste: o rato mexe-se até encontrar a parede.
- Testes:
  - sem janela:
    - dividir uma parede de 10 m com porta, janela e um canto (cada vão com a sua parte, o canto com a parte
      nova);
    - a divisão a meio da porta recusada;
    - desfazer;
    - duas paredes afastadas levadas ao canto e ligadas;
    - paralelas recusadas;
    - IFC válido;
  - com a janela real: o meio que atrai e a divisão em 5 + 5; o canto com dois cliques.

## 0.103.0 — 2026-10-23

Fase 4, passo 3 (continuação): **paredes curvas** — em arco e em círculo.

- A ferramenta **Parede** tem mais duas formas, na barra contextual:
  - **Arco**:
    - clica-se no início e no fim;
    - depois move-se o rato para curvar (vê-se a parede e o raio) e clica-se;
    - ou digita-se o raio: o arco vai para o lado do rato;
    - depois do início, uma distância digitada dá o fim;
  - **Círculo**: o centro e depois um ponto do círculo, ou o raio digitado.
- A linha de referência conta como nas outras formas:
  - no arco, pela face esquerda ou direita, no sentido em que se desenha;
  - no círculo, pela face interior ou exterior.
- No painel Propriedades da parede curva:
  - mudam-se o **raio** (do eixo), a **abertura** (em graus; o início fica onde está) e a **altura**;
  - o tipo muda a espessura e o eixo fica;
  - mostra também o comprimento ao longo do eixo.
- Move-se, roda e copia-se como as outras paredes.
- As **salas** e a **varinha mágica** das lajes contam com as paredes curvas: uma sala dentro de uma parede
  circular é um círculo.
- No IFC:
  - `IfcWall` com as camadas do tipo, centradas no eixo;
  - o corpo é a planta entre os dois arcos, com arcos verdadeiros (`IfcIndexedPolyCurve` com `IfcArcIndex`);
    numa parede circular é um `IfcCircleHollowProfileDef`;
  - o eixo é um `IfcTrimmedCurve` sobre um `IfcCircle`;
  - `Qto_WallBaseQuantities`, com o comprimento ao longo do eixo.
- Ainda não: as paredes curvas não se ligam às outras paredes nos cantos e não levam portas nem janelas. Ficam
  para um passo seguinte.
- Testes:
  - sem janela:
    - os arcos (por três pontos, nos dois sentidos, pelo raio para um lado), a faixa e o raio do eixo;
    - a parede de um quarto de círculo (o volume certo), a circular (anel) com uma sala dentro;
    - raio e abertura mudados, outro tipo (o eixo fica), movida, desfazer;
    - IFC válido;
  - com a janela real: o arco por três cliques (raio 3,25 m), o círculo pelo raio digitado, o painel e o raio
    mudado.

## 0.102.0 — 2026-10-23

Fase 4, passo 3 (primeira parte): **paredes por retângulo e a partir de uma face**.

- A ferramenta **Parede** tem «Forma» na barra contextual:
  - **Linha**: ponto a ponto, como até aqui;
  - **Retângulo**: dois cantos, ou o primeiro canto e as medidas digitadas («6;4»). Fazem-se quatro paredes
    ligadas nos cantos;
  - **A partir de uma face**: um clique numa laje, ou numa face horizontal de um esboço, faz as paredes ao longo
    do seu contorno, ligadas nos cantos. Antes do clique vê-se quantas paredes vão ser.
- Nestas formas, a linha de referência (Tab ou a barra contextual) diz de que lado as paredes ficam:
  - **pela face exterior**: o contorno é a face de fora e as paredes ficam por dentro;
  - **pela face interior**: as paredes ficam por fora;
  - **pelo eixo**.
- Enquanto se desenha, aparece a faixa das paredes à volta do contorno.
- Cada retângulo ou contorno é **um só passo de desfazer**, com todas as suas paredes.
- Por dentro do programa: as paredes de uma cadeia fazem-se todas dentro da mesma transação IFC, com os mesmos
  cantos limpos das paredes desenhadas ponto a ponto.
- Testes:
  - sem janela: o retângulo pela face exterior, pela interior e pelo eixo (as medidas, os cantos ligados, um
    passo de desfazer); as seis paredes de uma laje em L; a face de um esboço; uma laje circular e uma face
    vertical não dão paredes; IFC válido;
  - com a janela real: o retângulo com as medidas digitadas, a laje em L com o número de paredes à vista,
    desfazer.

## 0.101.0 — 2026-10-23

Fase 4, passo 2 (fim): **rampas**. Com a 0.100, o passo 2 (pisos e lajes) fica feito.

- **Ferramenta Rampa** (ambiente BIM, ao lado da Laje):
  - um clique no meio do pé da rampa e outro no meio da cabeça;
  - ou digita-se o comprimento: «6», ou «6;0,5» para mudar também o desnível;
  - a largura e o desnível estão na barra contextual (por omissão 1,20 m e 50 cm);
  - a espessura e o material são os do tipo de laje escolhido;
  - enquanto se desenha, vê-se a rampa e a **inclinação** em %;
  - X / Y bloqueiam o eixo.
- No painel Propriedades:
  - o comprimento (o pé fica onde está), a largura e o desnível mudam-se ali;
  - a inclinação aparece ao lado.
- A rampa move-se, roda e copia-se como os outros elementos, e aparece no painel Projeto em «Rampas».
- No IFC:
  - `IfcRamp` STRAIGHT_RUN_RAMP com o seu próprio corpo: o lado da rampa (a superfície de andar a subir o
    desnível, com a espessura por baixo) extrudido pela largura;
  - o material do tipo;
  - `Pset_RampCommon` com RequiredSlope (a inclinação) e IsExternal.
- Testes:
  - sem janela: a rampa de 6 m a subir 50 cm (medidas, inclinação, material); comprimento, largura e desnível
    mudados; movida; desfazer; IFC válido;
  - com a janela real: o desnível na barra, a inclinação à vista, o comprimento digitado, o painel e a largura.

## 0.100.0 — 2026-10-23

Fase 4, passo 2 (primeira parte): **lajes por contorno**.

- A ferramenta **Laje** tem agora quatro formas. Mudam-se com **Tab** ou na barra contextual («Forma»):
  - **retângulo** (como até aqui);
  - **polígono**:
    - clica-se canto a canto, ou digita-se o comprimento na direção do rato;
    - um clique no primeiro canto, ou Enter, fecha;
    - Delete apaga o último canto;
    - X / Y bloqueiam o eixo;
  - **círculo**: o centro e depois um ponto da borda, ou o raio digitado. No IFC fica um círculo verdadeiro;
  - **varinha mágica**: um clique dentro de paredes fechadas faz a laje. Antes do clique vê-se o contorno e a
    área. O «Contorno» vai:
    - até às **faces interiores** das paredes (um pilar lá dentro fica como furo);
    - ou até às **faces exteriores**: cada lado vai até à face de fora da parede que lá está, com a espessura
      dessa parede.
- **Função** da laje, na barra contextual e no painel Propriedades:
  - **estrutural**: na cota do pavimento é a laje de piso, com o topo na cota;
  - **acabamento**: assenta sobre a cota e não é resistente;
  - **excluída do cálculo**.

  No IFC, `Pset_SlabCommon.LoadBearing` acompanha a função.
- **Editar contorno**:
  - com uma laje selecionada, há o botão na barra contextual e no painel Propriedades;
  - os cantos aparecem como pegas: um clique pega num canto e o seguinte pousa-o (com os snaps e os
    alinhamentos, ou com a distância digitada);
  - no meio de cada lado há uma pega que acrescenta um canto;
  - com um canto pegado, Delete tira-o;
  - cada mudança é um passo de desfazer;
  - um retângulo editado assim passa a polígono. Se estava presa às vigas, deixa de as seguir.
- A laje circular muda pelo **raio**, no painel Propriedades. O painel mostra também a área de todas as lajes.
- Mudar o tipo de uma laje de contorno mantém o contorno e o topo.
- Empurrar/Puxar num lado de uma laje de contorno explica que ela se muda com «Editar contorno».
- No IFC:
  - IfcSlab com `IfcArbitraryClosedProfileDef` (ou `…WithVoids`, com furos) ou `IfcCircleProfileDef`,
    extrudido pela espessura do tipo;
  - Qto_SlabBaseQuantities;
  - o contorno lê-se do próprio corpo da laje: não há uma segunda cópia para manter em dia.
- Corrigido (0.99): abrir um IFC em segundo plano com uma planta aberta já não falha. As salas esperam que o
  ficheiro esteja lido.
- Testes:
  - sem janela:
    - um L, lados que se cruzam e cantos a menos;
    - a varinha por dentro (com um pilar) e por fora (com uma parede a meio);
    - o círculo e o raio;
    - o acabamento sobre a cota;
    - um canto mudado e desfeito;
    - um retângulo que passa a polígono;
    - outro tipo mantém o contorno;
    - IFC válido;
  - com a janela real: polígono, círculo e varinha numa planta; Editar contorno (mover, acrescentar e tirar um
    canto); a função mudada no painel.

## 0.99.0 — 2026-10-23

Fase 4 (arquitetura essencial), passo 1: **salas**.

- **Ferramenta Sala** (ambientes BIM e Docs):
  - um clique dentro das paredes faz a sala que lá está, entre as paredes e os pilares do pavimento ativo
    («varinha mágica»);
  - antes do clique, o contorno e a área aparecem debaixo do rato;
  - fora das paredes, ou sobre uma parede, avisa que não há sala;
  - uma folga de até 2 cm entre paredes ainda fecha a sala.
- Cada sala recebe o **número** seguinte do pavimento e o nome «Sala».
- **A sala acompanha as paredes:** quando uma parede muda, se move ou é apagada, a sala refaz-se sozinha no mesmo
  passo de desfazer, como no Revit.
- **Nas plantas** as salas aparecem com uma cor clara e uma etiqueta com o nome, o número e a área.
- Com **Selecionar**, um clique dentro de uma sala seleciona-a. O painel Propriedades mostra:
  - nome e número, que se mudam ali;
  - área, perímetro e pé-direito;
  - acabamentos do piso, das paredes e do teto.
- **Delete** apaga a sala selecionada.
- No IFC:
  - IfcSpace no seu pavimento: número no Name, nome no LongName;
  - corpo extrudido até ao pavimento de cima (ou 2,80 m);
  - Qto_SpaceBaseQuantities;
  - acabamentos em Pset_SpaceCoveringRequirements.
- Testes:
  - sem janela: duas salas numa casa com uma parede ao meio, com um pilar (um buraco), uma folga de 1 cm, fora
    das paredes; a parede movida e apagada (a sala segue); o nome e os acabamentos; desfazer; IFC válido;
  - com a janela real: a ferramenta Sala, as etiquetas, o clique numa sala, o nome no painel, a parede movida e
    Delete.

## 0.98.0 — 2026-10-23

Fase 3, passo 8: **propor estrutura a partir das paredes**. **A Fase 3 fica completa** (falta só a sapata
combinada).

- **BIM ▸ Propor estrutura…** (também no ambiente Estrutura). Funciona com as paredes do pavimento ativo, ou com
  as selecionadas. Escolhem-se o vão máximo, o tipo de pilar, o tipo de viga e o tipo de sapata (ou sem sapatas).
  - **Pilares:** em cada canto, encontro em T, cruzamento e ponta solta das paredes. Onde dois pilares ficam mais
    afastados do que o vão máximo, entram mais pilares pelo meio, a distâncias iguais.
  - **Vigas:** entre os pilares seguidos ao longo de cada parede, com o topo no topo das paredes. As paredes
    descem até à face de baixo da viga (não descem se tiverem uma janela lá em cima).
  - **Sapatas:** sob todos os pilares.
- Tudo fica marcado como **proposta**:
  - fazer outra vez **substitui** a proposta (não acrescenta);
  - **Remover proposta** apaga-a e as paredes voltam à altura que tinham.
- As vigas da proposta ficam presas aos pilares, como as outras.
- Testes:
  - sem janela: os nós de uma sala de 12 × 8 m com uma parede ao meio (com 6 m e com 5 m de vão máximo); 9
    pilares, 10 vigas, 9 sapatas, paredes a 2,50 m; outra vez: substituída; removida: paredes a 2,80 m;
    desfazer;
  - com a janela real: a janela Propor estrutura e Remover proposta.

## 0.97.0 — 2026-10-23

Fase 3, passo 7: **pilares e vigas mais completos**.

- **Secções novas:**
  - pilares **circulares** (Ø30), **em L** (40×40, abas de 15 cm) e **em T** (50×40), e um 20×50;
  - viga **em T** (60×50, abas de 12 cm).
  - Na janela Tipos, os pilares e as vigas têm agora **Forma** (retangular, circular, em L, em T) e a **espessura
    das abas**.
  - No IFC: IfcCircleProfileDef, IfcLShapeProfileDef, IfcTShapeProfileDef, com a área certa nas quantidades.
- **Sistema de vigas** (com 3 ou mais vigas selecionadas aparece na barra contextual; também em BIM ▸ Sistema de
  vigas… e no ambiente Estrutura):
  - em cada vão fechado pelas vigas, vigas paralelas ao longo de X ou de Y, ou nas duas direções (grelha);
  - por número de vigas ou por espaçamento; com o tipo de viga escolhido;
  - ficam presas ao vão: quando o vão muda, refazem-se. Fazer outra vez no mesmo vão substitui o sistema.
- (Os pontos de inserção e a rotação dos pilares vieram na 0.86.)
- Corrigido: um eixo movido para além do fim dos outros eixos já não larga os seus pilares.
- Testes:
  - sem janela: as áreas das secções e o IFC; uma viga entre pilares redondos; um tipo em L editado; o sistema
    (3 vigas por vão, depois uma grelha 2 + 2, depois o eixo movido);
  - com a janela real: a forma e as abas na janela Tipos; o Sistema de vigas pela barra contextual.

## 0.96.0 — 2026-10-23

Fase 3, passo 6: **lajes nos vãos das vigas**.

- **Lajes** (com 3 ou mais vigas selecionadas aparece na barra contextual; também em BIM ▸ Lajes e no ambiente
  Estrutura):
  - em cada vão fechado pelas vigas (o contorno mais pequeno de vigas entre pilares), uma laje entre as faces de
    dentro das vigas, com o topo no topo delas;
  - usa o tipo da ferramenta Laje; não repete lajes;
  - por agora só vãos retangulares (vigas ao longo de X e Y). Os outros ficam sem laje e a mensagem diz quantos.
- **A laje fica presa às vigas:** quando um pilar ou um eixo se move, a laje refaz-se entre as vigas novas.
- Corrigido: um elemento podia ficar com a cor de selecionado depois de um comando que acrescenta peças ao ecrã
  (por exemplo, as vigas depois de pôr as lajes).
- Testes:
  - sem janela: os vãos de um pórtico; duas lajes de 4,80 × 5,80 m entre as faces das vigas; o eixo movido;
    desfazer; IFC válido; a cor depois de acrescentar peças;
  - com a janela real: o botão Lajes com as vigas selecionadas.

## 0.95.0 — 2026-10-23

Fase 3, passo 5: **paredes entre pilares e sob as vigas**.

- **Paredes** (com vigas selecionadas aparece na barra contextual; também em BIM ▸ Paredes e no ambiente
  Estrutura):
  - uma parede sob cada viga selecionada, ou sob todas as do pavimento que estão entre pilares;
  - de face a face dos pilares, da base deles até à face de baixo da viga;
  - usa o tipo da ferramenta Parede; não repete paredes.
- **A parede fica presa à viga:** quando um pilar se move, a viga acompanha e a parede também.
- Testes:
  - sem janela: 4,70 × 2,40 m sob uma viga de 40 cm, sem repetir; o pilar movido (a parede passa a 5,70 m);
    desfazer; IFC válido;
  - com a janela real: as 7 paredes de um pórtico 3 × 2 pelo botão Paredes; um pilar movido.

## 0.94.0 — 2026-10-23

Fase 3, passo 4: **vigas entre pilares**, presas aos pilares.

- **Vigas** (com 2 ou mais pilares selecionados aparece na barra contextual; também em BIM ▸ Vigas e no ambiente
  Estrutura):
  - entre os pilares alinhados em X ou em Y (com 5 cm de tolerância), só entre vizinhos;
  - de face a face dos pilares, com o topo no topo dos pilares;
  - usa o tipo da ferramenta Viga; sem pilares selecionados, liga todos os do pavimento; não repete vigas.
- **As vigas ficam presas aos dois pilares:**
  - quando um pilar se move (Mover, Rodar, ou o eixo dele), a viga estica, encolhe ou roda para continuar de face a
    face;
  - quando o pilar muda de tipo, a viga chega às novas faces.
- Ao **copiar** pilares com as suas vigas, as cópias das vigas ficam presas às cópias dos pilares (o mesmo nos pisos
  tipo e para as sapatas).
- Testes:
  - sem janela: os pares de pilares vizinhos; 7 vigas num 3 × 2; o eixo movido; um pilar mais pequeno; cópia;
    desfazer;
  - com a janela real: o botão Vigas na barra contextual e um pilar movido.

## 0.93.0 — 2026-10-23

Fase 3, passo 3: **sapatas automáticas, blocos sobre estacas e radier**.

- **Sapatas** (com pilares selecionados aparece na barra contextual; também em BIM ▸ Sapatas e no ambiente
  Estrutura): uma sapata sob cada pilar selecionado, ou sob todos os do pavimento. Usa o tipo «Isolada» da
  ferramenta Sapata e não repete pilares que já têm sapata.
- **A sapata fica presa ao pilar:** move-se com ele (Mover, Rodar, e quando o eixo do pilar se move). O mesmo para
  as sapatas postas com a ferramenta Sapata sobre um pilar ou uma parede.
- **Blocos sobre estacas** (novos tipos: bloco de 1, 2 ou 4 estacas): escolha-os em «Isolada» na barra contextual
  da ferramenta Sapata.
  - O bloco leva as estacas por baixo, presas a ele; apagar o bloco apaga as estacas;
  - no IFC: IfcFooting PILE_CAP e IfcPile (BORED), com Qto_PileBaseQuantities e Pset_PileCommon;
  - as estacas (Ø30 e Ø40) também aparecem na janela Tipos («Estacas»).
- **Radier** (novo tipo de laje «Radier 30 cm»): desenha-se com a ferramenta Laje; no IFC é uma laje de fundação
  (IfcSlab BASESLAB).
- Testes:
  - sem janela: sapatas sob todos os pilares sem repetir; seguem o pilar movido e o eixo movido; bloco de 2 estacas
    (cabeças sob o bloco, 8 m, a 15 cm + meio diâmetro das pontas); movem-se com o pilar; apagadas com o bloco;
    radier BASESLAB; IFC válido;
  - com a janela real: o botão Sapatas na barra contextual; um bloco de 2 estacas escolhido na barra da ferramenta
    Sapata.

## 0.92.0 — 2026-10-23

Fase 3, passo 2: **pilares na grelha**, presos aos eixos (melhor do que no addon).

- **Inserir pilares:**
  - com eixos selecionados, aparece na barra contextual: um pilar em cada cruzamento dos eixos selecionados;
  - só eixos de um sentido: onde cruzam os do outro sentido;
  - sem eixos selecionados (BIM ▸ Inserir pilares, ou o botão no ambiente Estrutura): em todos os cruzamentos.
- Usa o tipo e a altura da ferramenta Pilar e o pavimento ativo. Não põe dois pilares no mesmo cruzamento.
- **Os pilares ficam presos aos seus dois eixos:** quando um eixo se move, os pilares dele vão junto. Continua
  assim depois de renomear ou renumerar os eixos.
- Um pilar desenhado à mão exatamente num cruzamento também fica preso.
- Os pilares novos ficam selecionados. Tudo num passo de desfazer.
- Testes:
  - sem janela: os três modos, nada repetido, mover um eixo, renumerar, desfazer;
  - com a janela real: o botão na barra contextual, todos os cruzamentos, o eixo movido, Ctrl+Z.

## 0.91.0 — 2026-10-23

Fase 3 (estrutura automática), passo 1: **grelha estrutural** mais completa.

- **BIM ▸ Grelha estrutural…**:
  - **Etiquetas:** os eixos verticais com números e os horizontais com letras, ou ao contrário;
  - **Renumerar** os eixos pela ordem: da esquerda para a direita e de baixo para cima. Fica marcado sozinho
    quando se muda o esquema;
  - **Cotas entre eixos nas plantas:** entre a grelha e as bolhas, uma cadeia entre eixos vizinhos e a cota
    total. Acompanham a grelha sozinhas, aparecem nas folhas e no PDF, e não se apagam por engano;
  - **Raio da bolha.**
- Os eixos novos (desenhados ou gerados) seguem o esquema escolhido. O gerador fala agora de eixos «verticais» e
  «horizontais».
- Tudo fica guardado com o projeto (no ficheiro .arqsynthbim) e é um passo de desfazer.
- Testes:
  - sem janela: as cotas (5 + 5, 10 e 6), letras nos verticais renumerados, um eixo novo com letra, gravar e
    voltar a abrir, desfazer;
  - com a janela real: a janela Grelha estrutural, a planta com as cotas, que não se selecionam; Ctrl+Z.

## 0.90.0 — 2026-10-23

Fase 2, passo 6: **pisos tipo** (pavimentos iguais, o «=» do ArqSynth Modeler). **A Fase 2 fica completa.**

- No painel **Pavimentos**, botão **Iguais…** (ou BIM ▸ Pavimentos iguais (piso tipo)…): escolha os pavimentos
  que ficam iguais ao ativo e dê um nome ao piso tipo. Os elementos do pavimento ativo são copiados para os outros.
- A partir daí, nesses pavimentos:
  - o que se **desenha** num deles aparece em todos, no mesmo passo de desfazer: paredes (ligadas às paredes
    certas em cada pavimento), pilares, vigas, lajes, tubos… e o que se classifica ou copia para lá;
  - o que se **muda** num deles muda em todos: comprimento, tipo, portas e janelas;
  - o que se **apaga** num deles sai de todos.
- A coluna «=» do painel mostra «=A», «=B»… nos pavimentos iguais entre si.
- **Separar** (o mesmo botão, num pavimento igual): cada pavimento fica com os seus elementos, independente.
- No IFC: cada pavimento leva a marca do piso tipo e os elementos ficam num grupo por pavimento (IfcGroup), como
  os grupos de modelo.
- Testes:
  - sem janela: três pavimentos iguais; uma parede nova num deles (ligada em todos); mais comprida em todos;
    uma porta em todos; apagada de todos; desfazer; separar;
  - com a janela real: Iguais…, uma parede desenhada com a ferramenta Parede, Ctrl+Z, Separar, Ctrl+Z.

## 0.89.0 — 2026-10-23

Fase 2, passo 5: **biblioteca de materiais**.

- **BIM ▸ Materiais…**, ou o botão **Materiais…** na janela Tipos. Para cada material:
  - **nome**;
  - **trama em corte** (betão, alvenaria, madeira, isolamento, gesso/reboco ou cheio): é a trama das plantas e
    dos cortes;
  - **cor**: é a que o Revit e os outros programas mostram;
  - **massa volúmica** (kg/m³) e **condutibilidade térmica** λ (W/(m·K)).
- **Novo**, **Duplicar** e **Apagar** (só materiais do projeto que nenhum tipo usa).
- Os materiais novos aparecem logo nas camadas e nas secções da janela Tipos.
- Tudo fica no IFC: a categoria do IfcMaterial, o estilo de superfície, Pset_MaterialCommon e
  Pset_MaterialThermal.
- Cada alteração é um passo de desfazer.
- Testes:
  - sem janela: mudar o bloco cerâmico (a parede passa a ter a trama de betão nessa camada), criar e apagar um
    material, o do catálogo não se apaga, desfazer;
  - com a janela real: o mesmo pela janela Materiais.

## 0.88.0 — 2026-10-23

Fase 2, passo 4 (segunda parte): **portas e janelas no editor de tipos**.

- Na janela **Tipos**, «Portas» e «Janelas»: largura, altura e, nas janelas, o peitoril ao colocar.
- **Aplicar** muda todas as portas ou janelas desse tipo, cada uma no seu sítio. As portas com as dobradiças à
  direita também acompanham.
- **Duplicar** e **Apagar** funcionam como nos outros tipos.
- O botão **Editar tipo…** do painel Propriedades também aparece nas portas e janelas.
- As medidas dos tipos ficam no IFC (nos parâmetros ArqSynth do IfcDoorType / IfcWindowType).
- Testes:
  - sem janela: uma porta à esquerda e outra à direita acompanham o tipo; desfazer;
  - com a janela real: Editar tipo… a partir de uma porta selecionada, 95 cm, Ctrl+Z.

## 0.87.0 — 2026-10-23

Fase 2, passo 4 (primeira parte): **editor de tipos**, como as propriedades de tipo do Revit.

- **BIM ▸ Tipos… (criar e editar)**, ou o botão **Editar tipo…** no painel Propriedades de um elemento.
- Para paredes, lajes, pilares, vigas, sapatas, tubos e condutas:
  - **camadas** (paredes, lajes, sapatas): material e espessura de cada uma, acrescentar, tirar, subir e descer;
    mostra o total;
  - **secção** (pilares, vigas, tubos, condutas): largura e altura (ou diâmetro) e material; nas sapatas, o
    tamanho em planta;
  - **nome**.
- **Aplicar** muda **todos os elementos desse tipo**: espessura, secção, cantos ligados, portas e janelas
  acompanham. É um só passo de desfazer (Ctrl+Z).
- **Duplicar** cria um tipo novo a partir do mostrado. **Apagar** só aparece para tipos do projeto que nenhum
  elemento usa.
- Os tipos ficam **no IFC** (IfcWallType com IfcMaterialLayerSet, IfcColumnType com IfcMaterialProfileSet…), que
  o Revit e os outros programas leem. Um tipo do catálogo mudado no projeto passa a ser o do projeto.
- Os tipos novos aparecem logo no menu BIM, em Classificar como, na barra contextual e no painel Propriedades.
- Testes:
  - sem janela: mudar o tipo (as paredes, a porta e o IFC acompanham; o mesmo GlobalId), criar, apagar, desfazer;
  - com a janela real: a mesma coisa pela janela Tipos, o menu, a barra contextual e Ctrl+Z.

## 0.86.0 — 2026-10-23

Fase 2, passo 3: **teclas comuns de colocação**, como no ArqSynth Modeler. Dentro das ferramentas que as usam,
estas teclas deixam de ser atalhos: R não é Retângulo e Espaço não é Selecionar.

- **Pilar:**
  - **R / Shift+R** roda 90° para um lado ou para o outro;
  - **Espaço / Shift+Espaço** muda o **ponto de inserção**: centro, os quatro cantos ou o meio de cada lado. O
    pilar fica com esse ponto no sítio do clique.
  - A barra contextual mostra a rotação e o ponto de inserção, e também se mudam ali.
- **Sapata** (isolada, solta): R / Shift+R roda 90°.
- **Porta e Janela:** **F** põe-na na outra face da parede. Também há a caixa «Do outro lado» na barra.
- **Componente** a colocar: R / Shift+R roda 90° (o Tab continua a funcionar).
- **Parede, Viga, Tubo, Conduta e Eixos:** depois do primeiro clique, **X** prende ao eixo vermelho, **Y** ao
  verde e **N** solta. O Shift continua a prender a linha que se está a seguir.
- Nas ferramentas de colocação (pilar, sapata, porta, janela, componente), o **Esc volta a Selecionar**.
- A barra contextual lembra as teclas de cada ferramenta, em cinzento.
- Testes:
  - sem janela: os nove pontos de inserção e as rotações;
  - com a janela real: R e Espaço no pilar (e o pilar colocado assim), Shift+Espaço, Esc, X e N na parede, F na
    porta, R continua a ser Retângulo fora delas.

## 0.85.0 — 2026-10-23

Fase 2, passo 2: **barra contextual** (como a barra de opções do Revit), por cima da vista. Muda com a ferramenta
e com o que está selecionado.

- **Com uma ferramenta de desenho**, mostra as opções dela, que se mudam ali mesmo:
  - Parede: tipo, altura, linha de referência e pavimento;
  - Pilar: tipo e altura;
  - Viga: tipo e «topo a»; Tubo e Conduta: tipo e «eixo a»;
  - Laje: tipo; Sapata: o tipo isolada e o tipo corrida;
  - Porta e Janela: tipo;
  - Mover e Rodar: «Copiar».
- A barra **acompanha** quando a opção muda de outra maneira: o Tab na parede, a altura escrita, o tipo escolhido
  no menu BIM, o Ctrl em Mover.
- **Com Selecionar**, mostra as formas de seleção e os filtros (o que já estava na barra Seleção). Com alguma coisa
  selecionada, mostra também:
  - o que está selecionado, por exemplo «3 selecionado(s): 2 Paredes, 1 Pilar»;
  - os botões Mesmo tipo, Enquadrar a seleção e Caixa de corte à volta;
  - com paredes, Cotar paredes.
- Os botões de navegação passaram para a linha dos separadores dos ambientes; a barra contextual tem a largura
  toda.
- Testes com a janela real: tipo e altura mudados na barra, Tab, menu BIM, Copiar com o Ctrl, parede selecionada.

## 0.84.0 — 2026-10-23

Fase 2 (base do ambiente de trabalho), passo 1: **ambientes de trabalho**, como no ArqSynth Modeler.

- **Separadores** em cima: **Conceito**, **BIM**, **Estrutura**, **Docs** (também Ctrl+1 a Ctrl+4, ou Vista ▸
  Ambiente). A barra da esquerda mostra as ferramentas desse ambiente:
  - **Conceito:** Linha, Retângulo, Empurrar/Puxar, Corte e o botão Classificar como;
  - **BIM:** Parede, Laje, Pilar, Porta, Janela, Tubo, Conduta, as ferramentas de esboço e Classificar como;
  - **Estrutura:** Eixos, Pilar, Viga, Sapata, Laje e Parede;
  - **Docs:** Planta do pavimento ativo, Corte, Cota, Cotar paredes e Modelos de vista.
- Em todos: Selecionar, Mover, Rodar e Fita métrica.
- As **teclas das ferramentas funcionam em qualquer ambiente** (W é sempre Parede), e o menu Ferramentas continua a
  ter todas.
- O ambiente escolhido fica guardado para a próxima vez.
- Ícones novos: planta, cotar paredes, modelos de vista.
- Testes:
  - sem janela: nenhuma ferramenta fica de fora de todos os ambientes;
  - com a janela real: Conceito, Ctrl+3, clique em Docs, tecla W em Docs, guardado.

## 0.83.0 — 2026-10-23

Fase 1 (navegação), passo 5: **caminhar sem atravessar paredes** (como no SketchUp).

- Com a ferramenta Caminhar (arrastar ou setas do teclado), o passo para **25 cm antes** de uma parede, pilar,
  janela, móvel ou esboço que esteja à frente. Conta à altura dos olhos e à da cintura: uma mesa também trava.
- As **portas atravessam-se** (abrem-se); as salas e os vãos também.
- **Alt** + arrastar atravessa tudo.
- A barra de estado avisa quando há uma parede à frente.
- Testes:
  - sem janela: parar antes da parede, passar a porta, a mesa trava, só os elementos perto do passo contam;
  - com a janela real: andar contra a parede, parar a 25 cm, atravessar com Alt.

## 0.82.0 — 2026-10-23

Fase 0 (marca), passo 3: **símbolo da ArqSynth** no programa.

- O **ícone da janela** e da barra de tarefas é o símbolo azul de www.arqsynth.com.
- **Ecrã de arranque** enquanto o programa carrega o motor 3D e o IFC: o símbolo, o nome, a versão e o que está a
  carregar.
- O nome é escrito pelo programa, num só sítio (o nome definitivo do programa BIM ainda está por decidir).
- Testes: o ícone tem todos os tamanhos e é o símbolo; o ecrã de arranque aparece e fecha quando a janela abre.

## 0.81.0 — 2026-10-23

Fase 1 (navegação): **o cubo de vistas como o ViewCube do Revit**.

- **Realce azul** na parte do cubo debaixo do rato: uma face, uma aresta (as duas tiras) ou um canto (os três
  quadradinhos). Com o rato longe, o cubo fica meio transparente.
- **Bússola** à volta do cubo, com N, E, S e O: clique numa letra para ver desse lado, à mesma altura. Vendo de cima,
  essa letra passa para cima.
- **Arrastar o anel** roda o modelo à volta (como um prato giratório). **Arrastar o cubo** orbita.
- **Olhando de frente para uma face**, aparecem:
  - quatro **triângulos** à volta do cubo, que vão para a face ao lado;
  - duas **setas curvas**, que rodam a vista 90° (para a esquerda ou para a direita).
- **Casinha:** vai para a vista inicial.
- **Menu ▾** (canto de baixo):
  - Ir para a vista inicial;
  - Definir a vista atual como inicial (fica guardada com o projeto);
  - Repor a vista inicial de origem;
  - Enquadrar tudo;
  - Perspetiva / Axonometria.
- Desenho: o cubo está maior, as faces têm sombra suave e não se veem as arestas de trás.
- Corrigido: ao abrir o programa em vista isométrica, os triângulos e as setas de rodar podiam aparecer sem estar a
  olhar de frente para uma face.
- Testes:
  - com a janela real: realce, TOPO, triângulo, rodar no sentido certo, letra E, arrastar o anel e o cubo, menu,
    vista inicial e casinha, nada na planta, transparente com o rato fora;
  - novos testes do clique no cubo, nos cantos, nas arestas, nas letras, no anel e nos botões.
- Testes (no Linux, uma corrida completa): 240 do núcleo/IFC/desenho + 235 verificações com a janela real, todas a
  passar.

## 0.80.0 — 2026-10-22

Fase 1 (navegação), passo 3: **caminhar pelo projeto** (como no SketchUp), na vista 3D em perspetiva.

- **Posicionar câmara** (barra de navegação, em cima): clique onde fica de pé; os olhos ficam a 1,60 m por cima, a
  olhar em frente. Para outra altura, escreva-a antes (ex.: 1,20 e Enter). Depois passa a Olhar em volta.
- **Olhar em volta:** arrastar roda a cabeça; a câmara fica no sítio.
- **Caminhar:**
  - arrastar para cima ou para baixo anda para a frente ou para trás; para os lados vira;
  - fica sempre à mesma altura; Shift sobe ou desce; Ctrl anda mais depressa;
  - as setas do teclado também andam (50 cm) e viram (cerca de 10°).
- Numa planta ou corte estas ferramentas dizem que são para o 3D. Ainda atravessam as paredes.
- Testes: com a janela real — posicionar, olhar em volta, caminhar com o rato e com a seta, e o aviso na planta.
- Testes (no Linux, uma corrida completa, com as 0.78 e 0.79): 238 do núcleo/IFC/desenho + 234 verificações com a
  janela real, todas a passar.

## 0.79.0 — 2026-10-22

Fase 1 (navegação), passo 2: **cubo de vistas** (como o ViewCube do Revit), no canto superior direito da vista 3D.

- **Gira com a câmara** e mostra de que lado se está a ver (TOPO, FRENTE, DIREITA…).
- **Clique numa face** para ver desse lado; numa aresta ou num canto, para ver de entre as faces. O modelo fica
  enquadrado e a câmara vira suavemente.
- A **casinha** por cima volta à vista inicial.
- Não aparece nas plantas e cortes.
- Testes: clique na face TOPO (vista de cima), num canto, na casinha; na planta não há cubo.

## 0.78.0 — 2026-10-22

Fase 1 (navegação), passo 1: **zooms, vista anterior e ferramentas de navegação**.

- **Barra Navegação** (em cima, à direita da barra Seleção) e menu **Vista**:
  - **Enquadrar tudo** (Shift+Z);
  - **Zoom janela** (Ctrl+Shift+W): arraste uma caixa (ou clique dois cantos) e o que está dentro enche a vista;
    depois volta à ferramenta de antes;
  - **Enquadrar a seleção** (Shift+F);
  - **Vista anterior / seguinte** (Alt+← / Alt+→), como num navegador: até 50 posições de câmara.
- **Duplo clique no botão do meio:** enquadrar tudo (como no AutoCAD).
- **Ferramentas Orbitar (O), Deslocar (H) e Zoom (Z)**, para quem não tem botão do meio ou usa o touchpad:
  - arrastar com o botão esquerdo;
  - numa planta, Orbitar só desloca;
  - Espaço volta a Selecionar.
- **Botão do meio à escolha** (Vista ▸ Navegação):
  - como no SketchUp: orbita (Shift desloca);
  - como no Revit: desloca (Shift orbita).
  - Fica guardado para a próxima vez.
- Testes: zoom janela e vista anterior/seguinte, enquadrar a seleção, Orbitar/Deslocar/Zoom, Orbitar numa planta
  (não roda), duplo clique do meio, botão do meio como no Revit.

## 0.77.0 — 2026-10-22

O programa passa a chamar-se **ArqSynth BIM** (a marca do dono do projeto; até aqui, ArqBIM).

- **Nome novo no que se vê:**
  - título da janela e mensagens;
  - PDF (programa que o criou);
  - cabeçalho do IFC gravado: programa de origem «ArqSynth BIM 0.77.0».
- **Abrir:** duplo clique em **«ArqSynth BIM.bat»**. O antigo «ArqBIM.bat» continua a funcionar e chama o novo.
- **Nos dados também** (escolha do dono do projeto: mudar e continuar a ler os antigos):
  - o conjunto de propriedades do programa no IFC passa a `ArqSynth_Parametros` (o Revit mostra-o); um IFC com
    `ArqBIM_Parametros` abre e edita-se como antes, e ao gravar fica com o nome novo;
  - o ficheiro das vistas, esboços e folhas ao lado do IFC passa a `.arqsynthbim`; um `.arqbim` antigo é lido
    quando não há o novo (fica no disco, já não é usado depois de gravar);
  - a pasta de trabalho (registo de erros, formas guardadas, cópias dos projetos partilhados) passa a
    «ArqSynth BIM», mudada de nome da «ArqBIM» na primeira vez, com tudo dentro.
  - Por dentro, o código continua a chamar-se `arqbim` (não se vê).
- Testes: um projeto gravado como pelo ArqBIM 0.76 abre, edita-se e grava-se com os nomes novos; a pasta antiga
  muda de nome uma vez, com o que tem dentro.
- Testes (no Linux, uma corrida completa): 238 do núcleo/IFC/desenho; 229 verificações com a janela real, 228 a
  passar.
  - A que falhou foi a dica de um alinhamento («Alinhado com o ponto» em vez de «Interseção»): a linha ficou certa e
    o percurso passa sozinho.
  - O teste passa a largar os pontos apanhados pelo caminho antes de verificar.
- **Plano de desenvolvimento novo, `PLANO.md`**, feito a partir do levantamento do ArqSynth Modeler 1.1.0 (o
  addon para Blender):
  - o que já existe e o que falta, família a família;
  - as decisões a confirmar;
  - dez fases, da Navegação ao cálculo estrutural e ao fabrico, com as classes IFC de cada ferramenta e onde o
    ArqSynth BIM deve fazer melhor do que o addon (o que está ligado acompanha).

## 0.76.0 — 2026-10-22

Seleção, passo 2: **filtros de seleção** (como no Revit e no AutoCAD).

- **Filtrar…** (barra Seleção, menu Editar ▸ Seleção ou botão direito): mostra as categorias do que está
  selecionado, com quantos há de cada; desmarque as que não quer e só as outras ficam selecionadas (o funil do
  Revit).
- **Selecionáveis…:** as categorias desmarcadas deixam de se poder selecionar — clique, caixa, laço e Selecionar tudo
  passam-lhes ao lado (por exemplo, as lajes ao escolher as paredes por cima delas). O botão mostra quantas estão de
  fora.
- **Selecionar por…:**
  - critérios: categoria, tipo, material, pavimento, fase, exterior, resistência ao fogo ou qualquer propriedade
    do modelo;
  - mostra os valores encontrados, com quantos há de cada; marque os que quer;
  - na vista ou em todo o projeto;
  - a substituir a seleção ou a juntar-se a ela.
- **Botão direito** com a ferramenta Selecionar:
  - todas do mesmo tipo (na vista ou no projeto);
  - toda a mesma categoria na vista;
  - Filtrar, Selecionar por, Selecionáveis;
  - Selecionar tudo, Inverter, Limpar.
- A grelha do chão deixou de tapar o que está pousado no chão: uma face desenhada à cota 0 fica sempre por cima dela,
  no ecrã e ao apontar com o rato.
- Testes: com a janela real — Selecionar tudo e Filtrar, o mesmo tipo, Selecionar por tipo, uma categoria
  posta de fora e uma caixa por cima de tudo, o menu do botão direito. Três testes antigos ficaram mais robustos:
  - o diálogo de componente é esperado até abrir;
  - o Push/Pull aponta ao meio da face desenhada;
  - depois do menu, um clique devolve o foco à janela.
- Testes (no Linux, uma corrida completa, com a 0.75): 236 do núcleo/IFC/desenho + 229 verificações com a janela
  real, todas a passar.

## 0.75.0 — 2026-10-22

Seleção, passo 1: **selecionar com caixa, laço, polígono e cerca** (como no AutoCAD, Revit e SketchUp).

- **Arrastar** com a ferramenta Selecionar (a partir de qualquer sítio, mesmo de cima de uma laje) faz uma caixa:
  - **para a direita** — azul: só o que fica **todo dentro** (janela);
  - **para a esquerda** — verde, tracejado: **tudo o que toca** (cruzamento).
  - Um clique continua a selecionar um elemento.
- **Laço livre** (barra Seleção ▸ Laço livre): arrastar desenha à mão à volta do que se quer; o sentido do
  primeiro movimento decide janela ou cruzamento, como na caixa.
- **Polígono:** clique os vértices; Enter, o botão direito ou um clique no primeiro ponto fecha.
- **Cerca:** clique os pontos de uma linha; fica selecionado tudo o que ela corta.
- **Teclas:** Shift troca (põe/tira), Ctrl junta, Ctrl+Shift tira — no clique e nas regiões.
- **Selecionar tudo** (Ctrl+A) e **Inverter seleção** (Ctrl+I): o que está à vista.
- Barra **Seleção** por cima da vista e menu **Editar ▸ Seleção**. Os eixos também entram nas regiões.
- Em planta, o que fica acima do corte não é apanhado.
- Testes: janela, cruzamento, laço, polígono e cerca no ecrã (núcleo); com a janela real, cada forma, o Ctrl,
  Selecionar tudo e Inverter.

## 0.74.0 — 2026-10-22

Melhorias pedidas depois da Fase 5, passo 4: **conectores nas tubagens e condutas**.

- **Cada tubo e conduta tem agora duas ligações (portas IFC), uma em cada ponta.**
- **Curvas automáticas:** ao desenhar seguido com a ferramenta Tubo ou Conduta, cada esquina leva uma curva:
  - o raio é um diâmetro (tubo) ou a largura (conduta);
  - os dois troços terminam onde a curva começa e acaba;
  - curva e troços ficam ligados entre si.
  - Seguir a direito liga os troços sem curva.
  - Começar um troço na ponta livre de outro igual também os liga.
- **A tubagem ligada move-se junta:**
  - mudar a cota do eixo de um troço sobe ou desce toda a tubagem ligada;
  - mudar o comprimento de um troço empurra a curva e os troços que vêm depois.
- **Painel Propriedades:** linha «Ligações» — o que está ligado a cada ponta (ex.: «1: livre · 2: Curva 1»).
- As curvas aparecem no painel Projeto (Curvas de tubagem / de conduta), nos modelos de vista e na verificação para
  certificação.
- Apagar um troço apaga também as suas ligações.
- Ainda não há tês, reduções nem subidas com curvas verticais. Mover um troço sozinho com a ferramenta Mover desliga-o
  dos outros.
- Testes: tubagem com curva (medidas, volume, ligações, em linha, encontrada pela ponta, apagar, desfazer), conduta a
  virar à direita, tubagem que sobe e encurta junta; com a janela real, a curva e as ligações no painel.
- Testes (no Linux, uma corrida completa, com as 0.71–0.73): 235 do núcleo/IFC/desenho + 224 verificações com a
  janela real, todas a passar.

## 0.73.0 — 2026-10-22

Melhorias pedidas depois da Fase 5, passo 3: **restrições de base e topo** das paredes e pilares, como no Revit.

- **No painel Propriedades** de uma parede ou pilar:
  - **Restrição da base:** o pavimento onde assenta;
  - **Deslocamento da base:** acima (ou abaixo, com «-») desse pavimento — por exemplo, um pilar que começa
    50 cm abaixo do chão;
  - **Restrição do topo:** «Não ligado (altura própria)», com a **Altura não ligada** escrita, ou um pavimento;
  - **Deslocamento do topo:** acima ou abaixo desse pavimento — a altura passa a ser calculada.
- **Quando um pavimento sobe ou desce,** as paredes e pilares presos a ele pelo topo mudam de altura e continuam a
  chegar lá.
- **Apagar um pavimento** que era o topo de alguma parede deixa-a «não ligada», com a mesma altura.
- **Mudar a altura à mão** (painel, Push/Pull) ou subir o elemento com Mover acerta o deslocamento do topo, como no
  Revit.
- Escolher outro pavimento de base leva o elemento para esse pavimento.
- Testes: parede e pilar presos a pavimentos (subir o pavimento, base acima do chão, pilar desde a sapata, altura à
  mão, pavimento apagado, mudar de pavimento, desfazer); com a janela real, o topo escolhido na lista e o deslocamento
  da base escrito.

## 0.72.0 — 2026-10-22

Melhorias pedidas depois da Fase 5, passo 2: **eixos editáveis e gerador de eixos**.

- **Selecionar um eixo** (ferramenta Selecionar, Espaço): clique na bolha, ou na linha onde não houver outro
  elemento; Shift junta mais eixos. O eixo fica azul. No painel Propriedades:
  - a etiqueta e as duas pontas (x; y), editáveis;
  - o comprimento.
- **Pegas** (como nas linhas):
  - o quadrado de cada ponta encurta ou alonga o eixo, ao longo dele;
  - as bolhas dos eixos paralelos alinhadas com ela vão juntas, como no Revit; segurando Ctrl ao pegar, só essa;
  - o losango do meio desloca o eixo paralelo a si próprio;
  - arrastar, ou clicar e clicar, ou escrever a distância.
- **Cotas temporárias** até ao eixo vizinho de cada lado: clique no número e escreva a nova distância.
- **Delete** apaga os eixos selecionados.
- **BIM ▸ Gerar eixos…:**
  - quantos eixos numerados (verticais) e com letra (horizontais);
  - a distância entre eles — um valor, ou vários separados por «;» (ex.: 5;5;6,50);
  - o ponto do primeiro cruzamento e quanto os eixos passam dos últimos;
  - acrescenta aos existentes ou substitui-os.
  - O desenho livre com a ferramenta Eixo continua.
- Testes: gerador (posições, etiquetas, acrescentar, substituir, desfazer), pontas alinhadas, vizinhos, mover,
  apagar; com a janela real: gerar pela janela, escolher pela bolha, cota temporária, arrastar a bolha, Delete.

## 0.71.0 — 2026-10-22

Melhorias pedidas depois da Fase 5, passo 1: **as paredes continuam ligadas**.

- Mudar o comprimento de uma parede — na cota temporária, no painel Propriedades ou com Push/Pull na ponta — já não
  solta a esquina:
  - a parede ligada nessa ponta vai junto (desloca-se, sem rodar);
  - as paredes ligadas a essa esticam ou encolhem para continuarem ligadas;
  - uma meia-esquadria continua meia-esquadria.
  - Antes, a ponta soltava-se e a esquina ficava aberta.
- A caixa «Medidas» deixa de mostrar o valor antigo depois de mudar uma cota temporária.
- Testes: o caso das três paredes do dono do projeto (no modelo e com a janela real, escrevendo na cota temporária),
  uma sala que cresce com os cantos limpos, a meia-esquadria que se mantém.

## 0.70.0 — 2026-10-22

Fase 5, passo 5: **preparar a certificação IFC**. **Fase 5 completa.**

- **BIM ▸ Verificar IFC para certificação:** o modelo é verificado como seria gravado; o resultado aparece no painel
  de baixo (o mesmo dos requisitos IDS), com ✓/✗ e, debaixo de cada falha, os elementos (um clique seleciona e
  enquadra). Verifica:
  - cabeçalho do ficheiro (programa de origem e vista do modelo declarada);
  - esquema IFC4 e as suas regras;
  - estrutura espacial (projeto, terreno, edifício, pavimentos; cada elemento num pavimento);
  - unidades (comprimento, área, volume, ângulo);
  - GlobalId únicos e válidos;
  - forma 3D e nome de cada elemento;
  - recomendados: quantidades base, tipo e material, georreferenciação.
- **Guardar relatório…** (botão no painel): guarda a verificação — ou a de um IDS — como página HTML, para enviar.
- **BIM ▸ Localização do terreno…:** latitude, longitude e altitude do terreno (como num mapa); ficam no IFC
  (`IfcSite`) e desfazem-se com Ctrl+Z.
- **O IFC gravado** passa a dizer no cabeçalho que foi feito pelo «ArqBIM 0.70.0» (antes dizia só IfcOpenShell) e o
  nome do ficheiro; os projetos novos declaram também a unidade de ângulo.
- **Portas e janelas** passam a ter quantidades base (largura, altura, área) e material no tipo (madeira / alumínio).
- Nota: isto prepara, não certifica — a certificação de software é feita pela buildingSMART com os seus ficheiros de
  teste.
- Testes: verificação de um modelo com todos os tipos de elemento (só falta a localização; depois de a dar, tudo
  cumprido), cabeçalho gravado, relatório, um elemento solto apanhado; no teste de interface, verificar, localizar o
  terreno pelo diálogo, verificar de novo e guardar o relatório. O teste da meia-esquadria passa a escolher a parede
  pela posição em X (antes, um empate em Y escolhia às vezes a outra).
- Testes (no Linux, uma corrida completa): 228 do núcleo/IFC/desenho + 218 verificações com a janela real, todas a
  passar.

## 0.69.0 — 2026-10-22

Fase 5, passo 4: **instalações** (tubos e condutas).

- **Ferramentas Tubo e Conduta** (barra de ferramentas, a seguir à Janela; tipos em BIM ▸ Tubo / BIM ▸ Conduta):
  - desenham-se ponto a ponto, como a viga — o eixo do tubo/conduta, nivelado;
  - cada clique continua a partir do fim do anterior; um valor escrito depois do 1.º clique é o comprimento;
  - antes do 1.º clique, um valor escrito muda a **cota do eixo** acima do pavimento (por omissão: tubo 0,30 m,
    conduta 2,50 m).
- **Tipos:** Tubo PVC Ø25, Ø50 e Ø100; Conduta 30×20 e 50×30 (aço galvanizado).
- **No IFC** são `IfcPipeSegment` / `IfcDuctSegment` com tipo (`IfcPipeSegmentType` / `IfcDuctSegmentType`),
  perfil redondo ou retangular, material, quantidades (comprimento, secção, área exterior) e, no tipo, o diâmetro
  nominal ou as medidas da conduta.
- **Painel Propriedades:** comprimento e cota do eixo editáveis; o perfil de um tubo mostra «Ø 5,0 cm». Mudar o tipo
  mantém o eixo no sítio.
- **Numa planta**, se o elemento desenhado ficar acima do plano de corte, a mensagem diz que não se vê ali e que se
  veja no 3D (também nas vigas).
- **Superfícies curvas sem riscas:** tubos, pilares redondos e paredes curvas já não mostram uma aresta preta em
  cada faceta (também em IFC de outros programas); a cumeeira de um telhado pouco inclinado continua a aparecer.
- Testes: tubo e conduta no IFC (medidas, volume, tipo, edição, desfazer), arestas macias; no teste de interface, dois
  tubos ponto a ponto, a cota do eixo no painel e uma conduta numa planta com o aviso do corte.
- Testes (no Linux, uma corrida completa, com as sapatas da 0.68): 226 do núcleo/IFC/desenho + 217 verificações com
  a janela real, todas a passar.

## 0.68.0 — 2026-10-22

Fase 5, passo 3: **sapatas**.

- **Ferramenta Sapata** (barra de ferramentas, a seguir à Viga; tipos em BIM ▸ Sapata):
  - **clique num pilar** → sapata isolada por baixo dele, centrada no pé e rodada com ele, com o topo na base do
    pilar;
  - **clique numa parede** → sapata corrida a todo o comprimento da parede, centrada no eixo;
  - **clique noutro sítio** → sapata isolada nesse ponto (com snaps e alinhamentos), com o topo na cota do pavimento.
  - Antes de clicar, a sapata aparece em pré-visualização e uma dica diz o que vai ser criado.
  - Usa o último tipo isolado e o último tipo corrido escolhidos, cada um onde pertence.
- **Tipos novos:** Sapata 80×80×40, Sapata 120×120×50 (isoladas) e Sapata corrida 50×30.
- **No IFC** são `IfcFooting` paramétricos com tipo `IfcFootingType` (isolada `PAD_FOOTING`, corrida `STRIP_FOOTING`),
  camada de betão, quantidades (`Qto_FootingBaseQuantities`: comprimento, largura, altura, volume) e
  `Pset_FootingCommon` (portante).
- **Painel Propriedades de uma sapata:** cota do topo editável; numa corrida, também o comprimento (o início fica).
  Mudar o tipo mantém o centro e o topo.
- **Classificar ▸ Sapata:** um bloco de esboço passa a sapata com a sua planta e a altura do tipo.
- As sapatas têm categoria própria no painel Projeto e nos modelos de vista.
- Testes: 3 testes novos (isolada sob pilar, corrida sob parede, classificar); no teste de interface, um clique num
  pilar com a ferramenta Sapata.

## 0.67.0 — 2026-10-22

Fase 5, passo 2: **eixos (grelha estrutural)**.

- **Ferramenta Eixo** (barra de ferramentas, junto ao Corte): dois cliques — ou um clique e o comprimento escrito —
  fazem um eixo.
  - Ao longo de Y fica **numerado** (1, 2, 3…); ao longo de X fica **com letra** (A, B, C…, depois AA…).
  - Usa os snaps e os alinhamentos.
- **Os eixos aparecem** a traço-ponto, com uma bolha e a etiqueta em cada ponta:
  - no 3D, ao nível do pavimento ativo;
  - nas plantas, por cima de tudo, como num desenho;
  - nas folhas e no PDF das plantas, e respeitam a região de recorte.
- **Snaps nos eixos:** ao longo deles e nos cruzamentos (dica «Interseção») — um pilar fica exatamente no cruzamento
  de dois eixos.
- **Painel Projeto ▸ Eixos:** lista os eixos; F2 muda a etiqueta, o botão direito apaga.
- **No IFC**, a grelha é um `IfcGrid` (eixos numerados em `UAxes`, com letra em `VAxes`), que mantém o seu GlobalId.
  - Enquanto só houver eixos numa direção, fica de fora do IFC: o IFC4 exige as duas e o ficheiro tem de continuar
    válido. Os eixos ficam guardados com o projeto.
  - Um IFC com grelha feito noutro programa mostra-a e passa a editá-la.
- Cada mudança é um passo de Ctrl+Z (os eixos e o IFC juntos).
- Testes (no Linux, uma corrida completa): 220 do núcleo/IFC/desenho + 213 verificações com a janela real, todas a
  passar.

## 0.66.0 — 2026-10-22

Fase 5, passo 1: **pilares e vigas** desenhados diretamente (estrutura).

- **Ferramenta Pilar** (barra de ferramentas, ícone do pilar; tipos em BIM ▸ Pilar):
  - um clique onde fica o pilar (o meio do pé, no pavimento ativo), com os snaps e os alinhamentos;
  - a altura escreve-se (ex.: 3,00 e Enter) — por omissão 2,80 m.
- **Ferramenta Viga** (tipos 15×30, 20×40, 20×50 em BIM ▸ Viga):
  - ponto a ponto, como a parede — o eixo da viga, com o topo a 2,80 m acima do pavimento;
  - antes do primeiro clique, um valor escrito muda a cota do topo;
  - depois do primeiro clique, um valor escrito é o comprimento;
  - os snaps apanham, por exemplo, os cantos do topo dos pilares; a cota azul mostra o comprimento.
- No IFC são **`IfcColumn` e `IfcBeam` paramétricos**, com tipo (`IfcColumnType`, `IfcBeamType`), perfil retangular
  de betão (`IfcMaterialProfileSet`), quantidades (`Qto_…BaseQuantities`) e `Pset_…Common` (portante).
- **Painel Propriedades de uma viga:** comprimento e cota do topo editáveis. Mudar o tipo mantém o topo no mesmo
  sítio (uma viga mais alta desce por baixo).
- **Classificar ▸ Viga:** um volume de esboço comprido passa a viga ao longo do seu lado maior.
- Correção: na planta, as cotas, os símbolos das portas e o subjacente também respeitam a região de recorte.

## 0.65.0 — 2026-10-22

Propriedades das vistas, passo 4: **alcance e aspeto das plantas**. Com isto, as propriedades das vistas ficam
completas.

- **Profundidade da vista** (abaixo do piso): a planta mostra também os pavimentos até essa profundidade, por
  exemplo o de baixo, visto através de um vazio ou de uma escada. Aparecem no ecrã e no papel.
- **Subjacente:** o pavimento de baixo ou o de cima desenhado a cinzento por baixo da planta, como no Revit. No
  ecrã fica sobre o chão e por baixo das paredes; no PDF e nas folhas sai a cinzento. Acompanha as mudanças no
  modelo.
- **Região de recorte:** só um retângulo da planta é desenhado, no ecrã, nas folhas e no PDF.
  - Liga-se no painel (fica à volta do que se vê).
  - Os limites escrevem-se: «Recorte em X (de; a)», «Recorte em Y».
- **Nível de detalhe** (plantas, cortes e alçados, no papel) — o que é cortado fica:
  - **Grosso**: as paredes cheias, escuras;
  - **Médio**: com a trama do material;
  - **Fino**: por camadas (o de antes).
- Estas propriedades são sempre da planta, mesmo que ela tenha um modelo de vista. Guardam-se com o projeto e
  desfazem-se com Ctrl+Z.
- Correções:
  - depois de desfazer uma vista 3D com nome, o F8 tentava voltar a ela; agora volta à vista 3D;
  - a caixa de corte acompanha o desfazer mesmo com uma planta à vista.

## 0.64.0 — 2026-10-22

Propriedades das vistas, passo 3: **caixa de corte nas propriedades e vistas 3D com nome**.

- **A caixa de corte é da vista 3D** e guarda-se com o projeto: ao reabrir, a vista volta cortada como estava.
  - Liga-se no painel (Caixa de corte), com F6 ou com Shift+F6 (à volta da seleção).
  - Ligar, desligar ou arrastar uma face é um passo de Ctrl+Z.
- **As medidas da caixa escrevem-se no painel:** «Caixa em X (de; a)», «Caixa em Y», «Caixa em Z». Por exemplo,
  `0; 1,5` em Z corta tudo acima de 1,50 m.
- **Vistas 3D com nome**, como no Revit:
  - **Vista ▸ Nova vista 3D** (Ctrl+Shift+3) guarda a vista como está (câmara, aspeto e caixa de corte) com o nome
    «3D 1», «3D 2»… e abre-a numa aba.
  - No painel Projeto, **Vistas 3D** lista a vista 3D e as com nome. Duplo clique abre; F2 ou o painel Propriedades
    mudam o nome; o botão direito apaga.
  - Cada uma tem o seu aspeto e a sua caixa. A câmara fica onde foi deixada e guarda-se com o projeto.
- Testes: caixa escrita no painel, vista com nome com o seu estilo, a vista 3D com o seu, desfazer tudo; no modelo,
  vistas guardadas e lidas de volta.

## 0.63.0 — 2026-10-22

Propriedades das vistas, passo 2: **o aspeto do 3D**. Estas propriedades aparecem no painel Propriedades com nada
selecionado, na vista 3D.

- **Estilo visual:**
  - **Sombreado** (o habitual);
  - **Linhas escondidas**: faces brancas, só as arestas da frente;
  - **Arame**: só as arestas — as faces continuam a poder ser clicadas;
  - **Raio-X**: as cores ficam transparentes e vê-se o que está por dentro e por trás.
- **Projeção:** perspetiva ou **axonometria** (sem perspetiva). Na axonometria continua a rodar-se com o botão do
  meio; a mudança mantém o que está à vista.
- **Arestas:** ligadas ou desligadas. **Grelha do chão:** ligada ou desligada.
- Ficam com a vista 3D, mesmo que ela tenha um modelo de vista. As plantas e os cortes mantêm o seu aspeto (cortados,
  sombreados, sem grelha); ao voltar ao 3D, ele volta como estava.
- Cada mudança é um passo de Ctrl+Z e guarda-se no `.arqbim`.
- Testes (no Linux, uma corrida completa): 214 do núcleo/IFC/desenho + 205 verificações com a janela real (incluindo
  as linhas escondidas vistas na cor do ecrã, o raio-X, a axonometria, a planta com o seu aspeto e desfazer).

## 0.62.0 — 2026-10-22

Desenho de precisão, passo 3: **linhas paramétricas**. As linhas desenhadas continuam editáveis.

- **Pegas:** uma linha selecionada (ferramenta Selecionar) mostra um quadrado azul em cada ponta e um losango a meio
  de cada segmento.
  - **Arrastar uma ponta** muda-a de sítio, com os snaps, os alinhamentos e a cota azul do comprimento.
  - **Arrastar um losango** desloca esse segmento inteiro; os segmentos vizinhos esticam.
  - Também se pode **clicar** na pega, levar o rato e clicar no destino, ou **escrever a distância** e premir Enter.
    Esc deixa como estava.
- **As linhas ligadas acompanham:** todas as linhas soltas com uma ponta no ponto movido vão com ele, mesmo que
  tenham sido desenhadas noutra corrente. Um só passo de Ctrl+Z.
- **Painel Propriedades de uma linha:**
  - o comprimento de cada segmento, editável;
  - numa linha de um segmento, também o ângulo (na planta) e as pontas (x; y; z).
- **Cota temporária de uma linha** (0.61): ao mudar o comprimento, as linhas ligadas à ponta também acompanham.
- Recusa explicada: um segmento não pode ficar com menos de 1 mm.
- Testes (no Linux, uma corrida completa): 214 do núcleo/IFC/desenho + 203 verificações com a janela real (incluindo
  as pegas, as linhas ligadas, a pega do meio e o comprimento no painel).

## 0.61.0 — 2026-10-22

Desenho de precisão, passo 2, depois do teste do dono do projeto: não via os alinhamentos, as cotas, nem como
começar a partir de um ponto.

- **Correção importante: os textos do ecrã voltam a aparecer no Linux (WSL).** Desde a mudança para o WSL (0.54),
  nenhum texto colado ao ecrã era desenhado: as dicas dos snaps («Extremidade», «Alinhado…»), as medidas ao desenhar
  e os valores das cotas.
  - A causa estava na placa gráfica: através do OpenGL do WSL, uma pequena matriz que roda e escala cada letra
    chegava com valores errados, e as letras ficavam sem tamanho.
  - O ArqBIM não roda nem escala esses textos, por isso passam a ser desenhados sem essa matriz.
- **Alinhamentos automáticos, como no Revit:** os cantos dos objetos perto do cursor alinham-no sozinhos (tracejado
  da cor do eixo), sem ser preciso parar em cima deles.
  - Ficam no plano em que se desenha: no chão, alinhar com o canto de cima de uma parede dá um ponto no chão; na face
    de uma parede, alinha-se na face.
  - Ao seguir um eixo a partir do último ponto, um alinhamento paralelo não desvia o ponto; os que cruzam o eixo dão
    o ponto exato nele.
- **Cotas temporárias ao desenhar**, a azul: o comprimento do segmento (Linha, Parede) com tiques e o número, e o
  ângulo com o eixo vermelho quando não é a direito. No Retângulo e na Laje, os dois lados.
- **Começar a uma distância de um ponto**, antes do primeiro clique.
  - Leve o cursor desde um canto ao longo de um alinhamento (ou ao longo de uma aresta). Uma cota azul mostra a
    distância.
  - Escreva a distância e prima Enter: o ponto inicial fica exatamente lá.
  - Funciona em Linha, Parede, Retângulo e Laje.
- **Cotas temporárias ao selecionar**, como no Revit (ferramenta Selecionar, um elemento):
  - uma **parede** mostra o comprimento e as distâncias às paredes paralelas de cada lado (eixo a eixo);
  - uma **porta ou janela** mostra as distâncias às pontas da parede;
  - uma **linha** mostra o comprimento de cada segmento.
  - **Clicar no número** põe-no a laranja; escrever a nova medida e premir Enter muda ou move o elemento (um passo de
    Ctrl+Z). Esc larga a cota.
- **Interseção de duas arestas:** escolhe o cruzamento mais perto, dando preferência ao que fica no eixo.
- Testes (no Linux, uma corrida completa): 212 do núcleo/IFC/desenho + 200 verificações com a janela real
  (incluindo o alinhamento sem pausa, o início a uma distância escrita e as cotas de uma parede e de uma linha
  reescritas).

## 0.60.0 — 2026-10-22

Desenho de precisão, passo 1: snaps mais completos e alinhamentos (pedido do dono do projeto, que passa à frente do
resto das propriedades das vistas).

- **Pontos apanhados e alinhamentos**, como no SketchUp, no Revit e no AutoCAD. O cursor parado um instante (0,2 s)
  numa extremidade, ponto médio ou interseção apanha esse ponto, que fica marcado com uma cruz cinzenta.
  - Depois, ao desenhar, o cursor **alinha-se com ele** na direção vermelha, verde ou azul, com um tracejado da cor
    do eixo e o ponto exatamente nesse alinhamento.
  - Onde dois alinhamentos se cruzam (por exemplo o eixo verde do ponto de partida e o vermelho de um canto), o
    ponto fica no **cruzamento**.
  - Ficam guardados os 3 últimos pontos apanhados. Esc ou mudar de ferramenta larga-os.
- **Aresta apanhada** (cursor parado nela): o segmento seguinte pode ser **paralelo** ou **perpendicular** a ela
  (magenta), ou seguir o seu **prolongamento** (tracejado cinzento).
- **Pé da perpendicular**: o ponto de uma aresta onde a linha a partir do último ponto lhe fica perpendicular.
- **Interseção de duas arestas** que se cruzam, como snap de ponto (antes só com guias).
- **Shift bloqueia a direção** em uso (um eixo, um alinhamento, paralelo…). Com Shift, o rato pode afastar-se e o
  ponto continua nessa linha; um ponto apontado é trazido para cima dela. A dica diz «— bloqueado (Shift)».
- Funciona em **Linha, Retângulo, Parede, Laje, Mover e Rodar**. Na Parede e na Laje só os alinhamentos de nível
  (sem azul).
- Testes (no Linux, uma corrida completa): 209 do núcleo/IFC/desenho (incluindo 6 novos do motor de alinhamentos)
  + 197 verificações com a janela real (incluindo uma linha que acaba alinhada com um ponto apanhado, o Shift e uma
  parede que começa alinhada).

## 0.59.0 — 2026-10-22

Propriedades das vistas, passo 1 (pedido do dono do projeto; novo bloco no plano, antes da Fase 5).

- **Com nada selecionado, o painel Propriedades mostra a vista ativa**, como no Revit: nome (o de um corte muda-se
  aí), tipo de vista e modelo de vista.
  - Na **planta**: escala nas folhas, altura de corte, fases que se veem, colorir por, e as categorias que se veem
    (**Visibilidade…**: uma lista para marcar, como o Visibilidade/Gráficos do Revit).
  - No **corte** e no **alçado**: o mesmo, sem a altura de corte.
  - No **3D**: fases, colorir por e categorias.
- **Cada vista tem as suas propriedades.** Esconder o mobiliário na planta não o esconde no 3D nem nas outras
  plantas. O ecrã, as folhas e os PDF seguem-nas.
- Com um **modelo de vista**, os valores vêm do modelo e ficam só para ler; o painel explica como os mudar.
  - Escolher Modelo de vista: (nenhum) volta às propriedades dessa vista, que ficam guardadas.
- Cada mudança é um passo de Ctrl+Z. Guarda-se no `.arqbim` (não toca no IFC) e vai com as vistas no trabalho de
  equipa.
- Testes (no Linux, uma corrida completa): 203 do núcleo/IFC/desenho + 194 verificações com a janela real
  (incluindo o painel do 3D e da planta, a altura de corte, a visibilidade vista na cor do ecrã, o modelo de vista e o
  desfazer).

## 0.58.1 — 2026-10-22

Correção pedida pelo dono do projeto: depois de dividir a face de uma parede com a linha, os vãos da porta e da janela
pareciam perdidos.

- Os vãos **nunca se perdiam** no IFC: a parte da face que ficava por cima deles era pintada como uma superfície
  própria e tapava-os. Agora, como no SketchUp, as partes de uma face de parede ou laje (divididas pela linha, ou um
  retângulo desenhado nela) mostram **só o contorno**: a parede, as portas, as janelas e os furos veem-se através
  delas. A parte continua lá para o Push/Pull a apanhar; selecionada, fica com um leve tom azul.
- Se a parede mudar ou for apagada, as partes pousadas nela voltam a ser verificadas (sem a parede, voltam a ver-se
  como superfície de esboço).
- Testes (no Linux, uma corrida completa): 202 do núcleo/IFC/desenho + 187 verificações com a janela real, incluindo
  uma nova — uma parede com um furo, dividida pela linha: a cor vista através do furo é a mesma antes e depois.

## 0.58.0 — 2026-10-22

A linha divide a face de uma parede com qualquer inclinação (o caso que o dono do projeto testou).

- Numa parede ou laje, uma linha **inclinada** — por exemplo do canto de baixo até à aresta de cima — divide a face em
  duas partes (um triângulo e um quadrilátero, dois trapézios…). Também um caminho de várias linhas, de aresta a
  aresta. Antes só uma linha nivelada ou a prumo dividia; a inclinada ficava uma linha.
- **Empurrar uma dessas partes** para dentro faz um **nicho ou vão IFC com essa forma** (um `IfcOpeningElement` com o
  contorno do polígono, extrudido na espessura; a parede continua paramétrica). Puxar para fora faz um volume de
  esboço, como antes.
- Os lados de um vão desenhado assim não se mexem um a um (só os de vãos retangulares): a barra explica em vez de
  esticar a ponta da parede.
- Uma linha quase nivelada ou quase a prumo (até 5°) continua a ser endireitada a partir do primeiro clique, e as
  pontas até 2 cm das arestas continuam a contar como estando nelas.
- Testes (no Linux, uma corrida completa): 202 do núcleo/IFC/desenho + 186 verificações com a janela real.

## 0.57.0 — 2026-10-22

Correções pedidas pelo dono do projeto depois de testar: os lados dos vãos, a base da parede, a linha na parede.

- **Push/Pull num lado de um vão** (esquerdo, direito, peitoril, padieira) **ou no fundo de um nicho**: só esse lado se
  move — o vão fica mais largo, mais estreito, mais alto ou mais fundo. O vão continua a ser um vão IFC
  (`IfcOpeningElement`) e a parede continua paramétrica. Antes, clicar num lado do vão mexia na ponta da parede. Ao
  passar o rato, só esse lado fica realçado; a medida pode escrever-se (e corrigir-se logo a seguir, como sempre).
  Num vão com porta ou janela, a mensagem diz que se muda pela medida da porta / janela.
- **Push/Pull na base da parede** (vista de baixo): puxar desce a base, empurrar sobe-a; o topo fica onde está e as
  portas, janelas e vãos não mexem. Antes era recusado.
- **Linha numa parede**: aceita uma linha desenhada à mão até 5° fora do nível / da vertical (fica à altura do
  primeiro clique) e pontas até 2 cm das arestas. Se a linha ficar numa face de parede sem a poder dividir, a barra
  de baixo diz porquê (antes ficava só uma linha, sem aviso).
- Testes (no Linux, uma corrida completa): 201 do núcleo/IFC/desenho + 184 verificações com a janela real.

## 0.56.0 — 2026-10-22

Folhas em abas; as abas ficam com o projeto (pedido do dono do projeto).

- As **folhas abrem-se numa aba** ao lado das vistas (Folha 1, Folha 2…), em vez de uma janela à parte. Painel
  Projeto ▸ duplo clique numa folha, ou "Pôr na folha": abre a aba dela. Tudo o que a janela da folha tinha está
  lá: papel, Legenda…, escala da vista, Arrumar, Atualizar desenhos, Exportar PDF…
- Numa folha, **Delete** tira da folha a vista escolhida (nunca apaga nada do modelo). As medidas escritas no
  teclado não vão para as ferramentas do 3D enquanto se vê uma folha.
- **As abas gravam-se com o projeto**: ao abrir de novo voltam as mesmas abas, pela mesma ordem, cada vista com o
  seu enquadramento, e a que estava à frente. Ficam no `.arqbim`; na pasta partilhada da equipa cada pessoa tem as
  suas.
- Teste com a janela no Linux mais fiável: os movimentos do rato vão diretos ao visor (o `QTest.mouseMove` mexia o
  cursor do sistema, e no WSLg esses movimentos às vezes iam parar a outra janela); as capturas já não pedem ao 3D
  para se pintar; a janela é ativada antes dos atalhos; no fim o teste sai sem a limpeza do Python, que fazia cair
  o processo depois de uma sessão longa (o programa em si fecha bem — verificado 3 vezes com abas de planta e de
  folha abertas).
- Corrigido: um projeto aberto sem janela (o colega no teste da equipa) e gravado de novo dava erro a escrever as
  câmaras das abas.
- Testes (no Linux, uma corrida completa): 200 do núcleo/IFC/desenho + 182 verificações com a janela real.

## 0.55.0 — 2026-10-22

Abas das vistas (pedido do dono do projeto), como no Revit.

- Por cima da vista há uma **aba por vista aberta**: **3D**, **Planta — Térreo**, **Corte 1**, **Alçado Sul**… Abrir
  uma vista (F4, F5, F8, ferramenta Corte, duplo clique no painel Projeto) abre a aba dela, ou mostra-a se já existir.
- **Clicar numa aba** volta a essa vista **como foi deixada**: o mesmo enquadramento e a mesma aproximação.
- **Fechar** uma aba (o × ou **Ctrl+W**) fecha só essa vista; o projeto continua aberto. Fechando a última, fica o
  3D. Botão direito numa aba: **Fechar esta vista** / **Fechar as outras vistas**. As abas podem arrastar-se para
  mudar a ordem.
- **Ctrl+Tab** / **Ctrl+Shift+Tab**: a vista seguinte / anterior (também em Vista ▸ …).
- Numa planta, PgUp / PgDn vai para a aba do outro pavimento, se estiver aberta; senão, a planta passa para lá.
- Apagar um pavimento ou um corte fecha a aba dele; mudar o nome de um corte muda a aba.
- Novo projeto ou abrir outro: só a aba do 3D. As abas ainda não se guardam com o projeto.
- Testes (no Linux, uma corrida completa): 199 do núcleo/IFC/desenho + 180 verificações com a janela real.

## 0.54.0 — 2026-10-22

O ArqBIM corre no Linux do Windows (WSL), por escolha do dono do projeto.

- O Smart App Control do Windows passou a bloquear 54 bibliotecas não assinadas do IfcOpenShell (o motor de
  geometria incluído): no Windows o programa deixou de calcular as formas. Em vez de desligar essa proteção, o
  programa corre agora no **Ubuntu 24.04 do WSL**, onde nada disso é verificado. A **janela aparece no Windows**
  como as outras; os projetos continuam nas mesmas pastas; as caixas Abrir/Gravar começam nos **Documentos** do
  Windows.
- **`ArqBIM.bat`** abre esta versão. `ArqBIM-Windows.bat` abre a do Windows, para quando o Windows a deixar correr.
- Preparar o Linux: `scripts/wsl_setup.sh` (pacotes do Ubuntu; o Python e as mesmas versões das bibliotecas,
  `requirements-lock.txt`, em `/opt/arqbim`; as letras do Windows para as folhas e os PDF).
- **Placa gráfica**: a RTX 3050 é usada por OpenGL sobre Direct3D 12, porque o WSL não tem Vulkan para ela. No
  prédio médio: navegação 101 imagens/s (meta 60), regenerar 18 ms, selecionar 1,5 ms, reabrir 0,8 s.
- Testes: correm no Linux (`tests\run_tests.ps1`, `-Gui` com a janela). Para o teste com a janela no Linux, as
  capturas juntam a pintura do Qt com a última imagem do 3D; a cor de um ponto do 3D lê-se da imagem do motor
  gráfico; depois de um diálogo a janela é ativada (como faria um clique); "abrir aos poucos" aceita a barra de
  estado como prova quando a abertura é mais rápida do que a amostragem.
- No Linux: 199 testes do núcleo/IFC/desenho passam. Com a janela real, 176 de 177 numa corrida completa; a que
  faltava ("abrir aos poucos") foi corrigida e passa à parte. Com outra janela do ArqBIM aberta ao mesmo tempo o
  teste da janela falha (essa janela fica com o teclado): corre-se com o programa fechado.

## 0.53.1 — 2026-10-22

Correção: o ArqBIM não abria.

- O Windows (Smart App Control) passou a bloquear um ficheiro não assinado da biblioteca que escreve os textos do 3D
  (`uharfbuzz\_harfbuzz.pyd`). Sem ele, a biblioteca do 3D (pygfx) não carregava e o programa fechava ao abrir.
  Agora, se esse ficheiro estiver bloqueado, os textos (medidas, nomes) são escritos com a outra biblioteca do pygfx
  (FreeType), que o Windows deixa passar. As definições do Windows não foram mexidas.
- Se o programa não conseguir abrir, a mensagem já não diz "o programa continua aberto". Quando é o Windows a
  bloquear um ficheiro, explica-o.

## 0.53.0 — 2026-10-21

Melhorias (6): caixa de corte no 3D (como o "Corte 3D" do ArchiCAD).

- O **3D mostra sempre o modelo inteiro**; só se corta com a **caixa de corte**.
- **Vista ▸ Caixa de corte (3D)** — **F6**: uma caixa azul à volta da **seleção** (se houver) ou do **modelo
  inteiro**. Só se vê o que está dentro; o que a caixa corta fica a escuro, como numa planta. Em planta ou corte
  passa-se para o 3D.
- **Mover as faces da caixa**: com Selecionar (a ferramenta fica ativa), arraste os **pontos azuis** no meio de
  cada face (por exemplo o de cima para baixo, para "tirar o telhado"). A barra de baixo diz o tamanho da caixa.
- **Shift+F6**: a caixa à volta da seleção (outra vez, depois de escolher outra coisa). **F6** de novo: sem caixa.
- As inferências não apanham pontos fora da caixa. Em planta/corte manda o corte deles; ao voltar ao 3D a caixa
  continua lá. Novo projeto ou abrir: sem caixa.
- Testes: 199 do núcleo/IFC/desenho + 177 verificações com a janela real.

## 0.52.0 — 2026-10-21

Melhorias (5): plantas e cortes sempre em ortogonal; desenhar na planta.

- **Plantas (F4), cortes e alçados sem perspetiva** (câmara ortogonal, como uma peça desenhada): as paredes já não
  "abrem" para os lados. Antes eram vistas de muito longe, quase sem perspetiva.
- **Não rodam**: na planta e no corte o botão do meio **desloca** (como Shift + botão do meio). A roda aproxima e
  afasta para o ponto do cursor. Para ver em 3D: F4 outra vez, ou F8 (3D), que mostra o modelo **inteiro**. Antes,
  rodar uma planta dava um 3D cortado.
- **Desenhar e editar na planta**: Parede, Retângulo, Linha, Cota e Selecionar trabalham no nível do pavimento
  (verificado nos testes). **Portas e janelas** passam a colocar-se clicando na parede **na planta** (o lado é o do
  cursor). Antes não se conseguia.
- As notas BCF feitas numa planta guardam a vista como uma câmara 3D que mostra o mesmo.
- Testes: 197 do núcleo/IFC/desenho + 175 verificações com a janela real.

## 0.51.0 — 2026-10-21

Melhorias (4): a Linha divide faces; Push/Pull de uma parte da face.

- **Uma linha de aresta a aresta divide a face** (como no SketchUp): por exemplo no topo de um volume. Um caminho de
  várias linhas por dentro da face (um L) também a divide. Uma linha que atravessa várias faces divide todas. A linha
  passa a ser uma aresta do volume, e a corrente continua a partir dali.
- **Push/Pull de uma parte**: puxar ou empurrar só uma das partes. Os lados que estão no plano do movimento esticam
  com ela (a frente fica em L, sem costura); do lado da linha nasce uma face nova. Não passa do fundo do volume.
- **Numa parede ou laje** (feitas no ArqBIM): uma linha nivelada ou a prumo, de lado a lado da face, cobre-a com
  **dois retângulos**. Empurrar um para dentro faz um **nicho** ou um **vão** IFC (a parede continua paramétrica);
  puxar para fora faz um volume de esboço (que pode classificar). Uma segunda linha divide um desses retângulos.
- Um esboço plano (um retângulo) dividido fica em dois esboços, cada um com o seu Push/Pull.
- Corrigido: um esboço com 4 cantos que não seja um retângulo alinhado com a parede já não é cortado na parede como
  se fosse uma caixa.
- Testes: 197 do núcleo/IFC/desenho + 172 verificações com a janela real.

## 0.50.0 — 2026-10-21

Melhorias (3): legenda das folhas personalizável.

- **Legenda (carimbo) com quadrículas**, como nas peças desenhadas: **Obra**, **Dono de obra**, **Local**, **Autor do
  projeto**, **Fase do projeto**, **Desenho** (o nome da folha), **Escala** e **Data** (sozinhas) e **Folha n.º**. Cada
  quadrícula tem o nome pequeno em cima; um texto comprido é cortado com "…". Igual no ecrã e no PDF.
- **Preencher**: na janela da folha, botão **Legenda…** ou **duplo clique na legenda**; também no painel Projeto, botão
  direito numa folha (ou em "Folhas") ▸ **Legenda…**. Os dados da obra são iguais em todas as folhas; o nome e o
  número são de cada folha. A fase escolhe-se da lista (Programa base, Estudo prévio, Anteprojeto, Licenciamento,
  Projeto de execução, Assistência técnica) ou escreve-se outra.
- Sem nada preenchido: a obra é o nome do ficheiro e o número é a ordem da folha (01, 02…).
- Fica no `.arqbim` com as folhas (vai para a equipa com as vistas). Um passo de Ctrl+Z.
- Corrigido: mudar só a arrumação de uma folha (mover uma vista, a legenda, o papel) já não diz "o modelo mudou" no
  botão **Atualizar desenhos**; uma cota nova numa vista atualiza essa vista na folha sozinha.
- A legenda passou de 24 para 40 mm de altura: as vistas arrumadas sozinhas ficam um pouco mais acima.
- Testes: 188 do núcleo/IFC/desenho + 168 verificações com a janela real.

## 0.49.0 — 2026-10-21

Melhorias (2): cotas que seguem as paredes.

- **Esticar uma parede leva a cota**: uma ponta de cota tirada de uma parede lembra-se de que ponta da parede estava
  perto (o início ou o fim, e a que distância). Esticar ou encurtar a parede (Push/Pull, comprimento no painel) leva-a
  com essa ponta; a outra fica onde estava.
- **Cotas automáticas que seguem portas e janelas**: nas cadeias de **Cotar paredes**, os aros ficam presos à própria
  porta ou janela — deslizá-la na parede leva as duas pontas, e a cota ao lado ajusta-se.
- **A linha de cota vai com o elemento**: mover ou rodar a parede leva também a linha da cota (antes ficava onde fora
  desenhada, longe da parede).
- As cotas gravadas antes continuam a ler-se (sem a ponta da parede, seguem só a colocação, como antes).
- Testes: 187 do núcleo/IFC/desenho + 167 verificações com a janela real.

## 0.48.0 — 2026-10-21

Melhorias (1): camadas, sincronizar, propriedades livres.

- **Camadas iguais de paredes diferentes juntam-se** no desenho: onde duas paredes se encontram, o reboco de uma
  continua no da outra (e o bloco no bloco) sem traço; o traço fino fica só onde o material muda.
- **Sincronizar sem perder o Ctrl+Z**: quando não chegou nada da equipa (só as suas alterações foram), o projeto já
  não é reaberto — o histórico de desfazer continua. (Quando chegam alterações de outros, ainda é reaberto.) As vistas
  só contam como "recebidas" quando são de facto diferentes.
- **Propriedades livres**: em **+ Propriedade…**, a última opção **Outra (uma propriedade sua)…** — conjunto (ex.:
  "Projeto"), nome (ex.: "Fornecedor") e tipo de valor (texto, número, sim/não). Os nomes começados por "Pset_" ou
  "Qto_" ficam para a norma IFC.
- Testes: 186 do núcleo/IFC/desenho + 167 verificações com a janela real.

## 0.47.0 — 2026-10-21

Fase 4, passo 6: trabalho em equipa numa pasta partilhada (decisão do dono do projeto).

- **Arquivo ▸ Equipa ▸ Partilhar projeto numa pasta…**: o projeto (IFC, vistas, notas) vai para uma pasta partilhada
  (servidor do escritório, OneDrive…) e passa a ser o **modelo central**. Cada pessoa trabalha numa **cópia local**
  (fica no computador entre sessões, com o que ainda não foi sincronizado). **Abrir projeto partilhado…** para os
  colegas.
- **Sincronizar com o central (Ctrl+Alt+S)**: o que mudou aqui vai para o central, o que os outros mudaram vem para
  aqui. O IFC é juntado entidade a entidade (comparando com a versão da última sincronização): duas pessoas que
  acrescentam paredes ao mesmo pavimento ficam ambas; uma muda o nome a uma parede e outra a altura — fica com as
  duas mudanças. Se duas pessoas mudarem a mesma coisa de maneiras diferentes, fica a do central e a mensagem diz
  quantos conflitos houve. O central é escrito com um bloqueio (duas sincronizações ao mesmo tempo esperam).
- **Reservas**: mudar um elemento reserva-o para quem o mudou (fica num ficheiro ao lado do central). Se outra pessoa
  o tiver reservado, a alteração é **desfeita** e a mensagem diz quem o tem. **Devolver as minhas reservas** liberta
  tudo. Barra de baixo: "Partilhado · N reserva(s) minha(s)"; título com "(partilhado)".
- **Vistas** (cortes, folhas, cotas, modelos de vista): vão para o central com a reserva das vistas (**Reservar as
  vistas**); os outros recebem-nas ao sincronizar (os seus esboços ficam seus). **Notas BCF**: juntam-se (os
  comentários de todos).
- Testes: 185 do núcleo/IFC/desenho (duas pessoas ao mesmo tempo, conflitos, reservas) + 166 verificações com a
  janela real.

## 0.46.0 — 2026-10-21

Fase 4: acrescentar propriedades normalizadas.

- Painel **Propriedades**, linha **Mais dados ▸ + Propriedade…**: lista as propriedades **normalizadas IFC4** da
  classe do elemento que ele ainda não tem (ex.: numa porta, `Pset_DoorCommon ▸ FireRating`, `AcousticRating`…),
  com o campo certo para o valor (sim/não, lista de escolhas, texto, número inteiro, número, medida em metros). Um
  passo de Ctrl+Z.
- Assim já se corrige no ArqBIM o que um IDS pede e falta (ex.: a resistência ao fogo das portas) e depois
  **Verificar de novo**.
- Gravar propriedades: se o conjunto não existe é criado; se vem do **tipo**, o elemento ganha a sua cópia (o tipo,
  partilhado por outros, não muda); os valores enumerados ficam como a norma diz.
- Testes: 183 do núcleo/IFC/desenho + 163 verificações com a janela real.

## 0.45.0 — 2026-10-21

Fase 4, passo 5: fases de obra (alterações) — amarelos e vermelhos.

- Cada elemento pode ter uma **fase**: **Existente**, **Novo (a construir)**, **A demolir**, **Temporário**. Dá-se em
  **BIM ▸ Fase da seleção ▸** (vários elementos de uma vez) ou na nova linha **Fase** do painel Propriedades.
  Fica no IFC como a norma diz: a propriedade `Status` (valor enumerado `PEnum_ElementStatus`) do `Pset_…Common` de
  cada elemento — o que o ArchiCAD e o Revit também leem e escrevem. Um passo de Ctrl+Z; a forma não é recalculada.
- Regras gráficas: **Colorir por ▸ Fase (alterações)** — a construir a **vermelho**, a demolir a **amarelo**,
  existente e sem fase a cinzento, temporário a azul. No ecrã, numa planta ou corte, também o que é cortado fica
  com essas cores.
- Modelos de vista: **Fases que se veem** — Todas (alterações), **Situação existente** (sem o novo), **Proposta** (sem
  o que se demole), Só o novo. Botão **Criar modelos de alterações**: cria logo os três — "Existente", "Proposta" e
  "Alterações (amarelos e vermelhos)".
- No papel (PDF e folhas), com a regra das fases: o cortado a construir **vermelho cheio**, a demolir **amarelo
  cheio**, o que fica com a sua trama — a convenção portuguesa das peças desenhadas de alterações. (Com outras regras,
  o cortado sai nas cores da regra.)
- Testes: 183 do núcleo/IFC/desenho + 162 verificações com a janela real.

## 0.44.0 — 2026-10-21

Fase 4, passo 4: notas de coordenação (BCF).

- **BIM ▸ Nova nota de coordenação (BCF)…** (ou painel **Notas (BCF)** ▸ Nova nota): título e descrição; a nota
  guarda **onde se estava a olhar**, os **elementos selecionados** e uma **imagem** da vista.
- Painel **Notas (BCF)** (em baixo, ao lado das Tabelas e dos Requisitos): a lista das notas (estado, autor, data,
  número de comentários), a imagem, a descrição e os comentários da escolhida. **Ir para a vista** (ou duplo
  clique) volta à câmara da nota e seleciona os seus elementos; escrever um **comentário** + Enter; **Fechar /
  reabrir**; **Apagar**. Tudo entra no Ctrl+Z.
- As notas **gravam-se com o projeto** em `<nome>.bcfzip` ao lado do IFC e voltam ao abrir.
- **Exportar BCF…** / **Importar BCF…**: trocar notas com o Revit, ArchiCAD, Solibri, BIMcollab… (escreve BCF 2.1;
  lê 2.1 e 3.0). Importar uma nota que já cá está substitui-a pela do ficheiro (a mais recente de quem a mudou).
- As posições vão no BCF nas coordenadas reais do IFC (também nos modelos longe da origem).
- Correção: ao fechar o programa podia aparecer um erro do filtro de teclado (objetos já destruídos).
- Biblioteca nova: **bcf-client** 0.9.0 (projeto IfcOpenShell, LGPL-3.0, autorizada), com xsdata (MIT). Sem o
  `requests` que traria (servidores BCF — não usados).
- Testes: 182 do núcleo/IFC/desenho + 159 verificações com a janela real.

## 0.43.0 — 2026-10-21

Fase 4, passo 3: modelos de vista.

- **Vista ▸ Modelos de vista…**: criar, mudar e apagar modelos. Cada um tem **nome**, **altura de corte** (plantas),
  **escala nas folhas** (Automática ou 1:20 … 1:1000), **colorir por** (as regras gráficas) e as **categorias que se
  veem** (desmarcar Mobiliário, Paredes…).
- No painel Projeto, botão direito numa planta, corte ou alçado ▸ **Modelo de vista ▸** um modelo ou (nenhum). O
  nome do modelo aparece ao lado da vista. Mudar o modelo muda todas as vistas que o seguem.
- Ao abrir essa vista (duplo clique, F4, PgUp/PgDn para outro pavimento) aplica-se o modelo: as categorias
  escondidas desaparecem, a planta corta à altura do modelo, as cores seguem a regra. No 3D (F8) volta tudo ao normal.
- No papel (Ctrl+P, folhas) também: sem as categorias escondidas, com a altura de corte do modelo, e nas folhas a
  escala do modelo (se a vista não tiver uma sua).
- Gravado no `.arqbim`; criar/mudar modelos e dá-los a vistas entra no Ctrl+Z.
- Desempenho: só as classes que algum modelo esconde ficam em lotes de desenho à parte (navegação no prédio grande
  63 fps, igual a antes).
- Testes: 181 do núcleo/IFC/desenho + 156 verificações com a janela real.

## 0.42.0 — 2026-10-21

Fase 4, passo 2: verificação com requisitos IDS.

- **BIM ▸ Verificar com requisitos IDS…**: escolhe-se um ficheiro **IDS** (Information Delivery Specification da
  buildingSMART — o que o dono de obra exige que o modelo diga: propriedades, classificações, materiais…) e o modelo,
  tal como está, é verificado.
- Painel **Requisitos (IDS)** (em baixo, ao lado das Tabelas): cada requisito com ✓ ou ✗ e o resultado ("cumprido (4
  elementos)", "falha em 2 de 2 elementos"…); debaixo de cada um que falha, os **elementos que falham e porquê**, em
  português ("Falta a propriedade pedida no conjunto"). **Clicar num elemento seleciona-o e enquadra-o.** Depois de
  corrigir (ex.: no painel Propriedades), **Verificar de novo**.
- Exemplo novo: `exemplos/requisitos_exemplo.ids` (4 requisitos; a casa de exemplo falha um — as portas sem
  resistência ao fogo), feito por `scripts/ids_exemplo.py`.
- Biblioteca nova: **ifctester** 0.9.0 (do projeto IfcOpenShell, LGPL-3.0, autorizada pelo dono do projeto), com
  xmlschema e elementpath (MIT). Instalada sem o servidor web e o bcf-client que traria (não são precisos aqui).
- Testes: 180 do núcleo/IFC/desenho + 152 verificações com a janela real.

## 0.41.0 — 2026-10-21

Fase 4, passo 1: regras gráficas por propriedade.

- Painel **Regras gráficas** (separador ao lado de Pavimentos e Projeto; também em Vista ▸ Regras gráficas):
  **Colorir por** Classe IFC, Tipo, Pavimento, Material, **Exterior / interior**, **Resistência ao fogo**, ou
  **Outra propriedade…** (qualquer propriedade que o ficheiro tenha, também as do Revit/ArchiCAD).
- Cada valor ganha uma cor (sim/não: quente/frio; sem valor: cinzento claro) no 3D, nas plantas e nos cortes ao
  vivo; a **legenda** mostra cada valor, a cor e quantos elementos o têm. **Clicar numa linha seleciona esses
  elementos.** A seleção continua azul. "Nada" volta às cores normais.
- Mudar um elemento (ex.: marcar uma parede como exterior no painel Propriedades) muda logo a sua cor. Abrir outro
  ficheiro volta às cores normais.
- As cores só mudam o que se vê: o IFC não muda.
- Testes: 179 do núcleo/IFC/desenho + 150 verificações com a janela real.

## 0.40.0 — 2026-10-21

Fase 3, passo 16: cotas automáticas das paredes.

- **Vista ▸ Cotar paredes (cadeias e totais)**: as paredes escolhidas (ou, sem escolha, todas as do pavimento ativo)
  ganham, do lado de fora, uma **cadeia de cotas** de ponta a ponta pelos aros das portas e janelas (0,80 | 1,20 |
  0,55 | 0,90 …) e, mais afastada, a **cota total**. Ficam na planta desse pavimento (abre-se a planta), no ecrã e no
  papel, presas às paredes.
- A cadeia de uma parede vai até ao canto exterior das paredes encostadas às suas pontas: uma parede lateral entre
  duas outras mede a casa toda.
- Repetir o comando **substitui** as cotas automáticas dessas paredes (não as duplica); as cotas feitas à mão ficam.
  Um passo de Ctrl+Z.
- Testes: 178 do núcleo/IFC/desenho + 147 verificações com a janela real.

## 0.39.0 — 2026-10-21

Fase 3, passo 15: desfazer também nas vistas.

- **Ctrl+Z / Ctrl+Y** desfazem e refazem agora também: criar um corte, mudar-lhe o nome, apagá-lo (volta com as suas
  cotas e o seu lugar nas folhas); criar, mudar o nome e apagar folhas; pôr e tirar vistas de uma folha, arrastá-las,
  mudar a escala, o papel e "Arrumar". Tudo no mesmo desfazer do modelo, pela ordem em que foi feito.
- **Pôr na folha ▸ Nova folha** é um só passo (a folha nova e a vista).
- Ctrl+Z e Ctrl+Y funcionam também com a janela da folha à frente; a janela continua aberta na mesma folha.
- Testes: 177 do núcleo/IFC/desenho + 146 verificações com a janela real.

## 0.38.0 — 2026-10-21

Fase 3, passo 14: cotas.

- Ferramenta **Cota** (tecla **C**; também na barra da esquerda e no menu Vista): numa **planta** (F4), num **corte**
  ou num **alçado**, clique no 1.º ponto e no 2.º (as inferências funcionam: canto de parede, aresta de um vão…) e
  depois onde fica a linha de cota. O valor é a distância vista nessa vista, em metros com duas casas ("4,50").
- A cota **fica na vista onde foi feita** (como no Revit): aparece nessa planta / corte / alçado, no ecrã e no PDF e
  nas folhas, e não nas outras.
- Uma ponta tirada de um elemento (um canto de parede) **fica presa a ele**: se a parede for movida ou rodada, a cota
  acompanha. (Se a parede for esticada, a ponta fica onde estava — a seguir.)
- Escolher uma cota: clique em cima da linha (fica azul); **Delete** apaga; **Ctrl+Z** desfaz (fazer e apagar cotas
  entra no desfazer).
- No papel: linhas de chamada com folga do objeto, traços a 45° nas pontas, o valor por cima da linha, lido de baixo
  ou da direita.
- Guardadas no `.arqbim`, ao lado do IFC (decisão do dono do projeto); mudar o nome a um corte leva as suas cotas;
  apagar um corte apaga-as.
- Os ícones Corte e Cota estão também na barra da esquerda (com contorno claro, para se verem no tema escuro).
- Testes: 176 do núcleo/IFC/desenho + 145 verificações com a janela real.

## 0.37.0 — 2026-10-21

Fase 3, passo 13: biblioteca entre projetos.

- **BIM ▸ Trazer componentes de outro projeto…** (ou painel Projeto, botão direito em Biblioteca / Componentes ▸
  Trazer de outro projeto…): escolhe-se um IFC (feito no ArqBIM, no Revit, no ArchiCAD…), aparece a lista dos seus
  componentes (mobiliário, louças, equipamento — tipos com forma), marcam-se os que se querem, e ficam na
  Biblioteca deste projeto com a forma, os materiais e as propriedades (`append_asset` do IfcOpenShell). Se o outro
  ficheiro estiver noutra unidade (metros, pés), é convertido. Um componente já trazido não se repete. Ctrl+Z desfaz.
- **Inserir outra cópia** funciona agora com qualquer componente da biblioteca, também os que vieram de outros
  programas: a cópia fica com o canto mais baixo da sua caixa no ponto clicado (como os do ArqBIM). Portas e janelas
  não entram (vão nas paredes, com as suas ferramentas).
- Exemplo novo: `exemplos/biblioteca_mobiliario.ifc` (mesa, cadeira, cama, lavatório; feito por
  `scripts/biblioteca_exemplo.py`).
- Testes: 174 do núcleo/IFC/desenho (incluindo um ficheiro em metros) + 142 verificações com a janela real.

## 0.36.0 — 2026-10-21

Fase 3, passo 12: desenho 2D mais limpo — camadas e paredes unidas.

- **Tramas por camada**: uma parede de várias camadas é desenhada camada a camada onde é cortada — na alvenaria de
  20 cm, reboco (cinzento) | bloco (tracejado) | reboco; na parede de gesso cartonado, placa | lã (tracejado fino) |
  placa — com um traço fino entre camadas. O mesmo nas lajes cortadas em corte. As camadas vêm do IFC (a
  `IfcMaterialLayerSetUsage`: direção, sentido, desvio); se não baterem certo com a forma do elemento, ele é
  desenhado com a trama do material principal, como antes.
- **Paredes unidas**: o contorno grosso do que é cortado é um só — onde duas paredes se encontram já não há traço.
- Medido no prédio grande (5 700 contornos numa planta): unir 0,36 s, uma vez por desenho.
- Testes: 173 do núcleo/IFC/desenho + 141 verificações com a janela real.

## 0.35.0 — 2026-10-21

Fase 3, passo 11: as portas com arco também na planta ao vivo.

- Na **planta (F4)**, as portas com símbolo aparecem como no desenho — aros, folha aberta, arco — por cima do que está
  abaixo do corte, em vez do corte 3D da porta fechada. Clicar perto da folha ou do arco seleciona a porta (fica a
  azul); "Virar a porta" no painel Propriedades vê-se logo.
- Nos cortes, nos alçados e no 3D as portas continuam iguais.
- Os símbolos das portas calculam-se uma vez e ficam guardados até a porta mudar.
- Testes: 172 do núcleo/IFC/desenho + 141 verificações com a janela real.

## 0.34.0 — 2026-10-21

Fase 3, passo 10: virar portas.

- Painel **Propriedades** de uma porta: linha **Virar a porta** com dois botões — **Dobradiça** (as dobradiças passam
  para o outro aro; abre para o mesmo lado) e **Lado** (passa a abrir para o outro lado da parede; dobradiças no
  mesmo aro). A planta em PDF e as folhas mostram logo o arco novo; Ctrl+Z desfaz.
- No IFC, o lado das dobradiças é o do tipo (`IfcDoorType.OperationType` …LEFT / …RIGHT, como manda a norma): a
  porta com dobradiças à direita passa para o tipo "Porta 80×210 (à direita)" (criado na primeira vez). Mudar o
  tamanho da porta (Tipo) mantém o lado das dobradiças. O IFC continua válido.
- Testes: 172 do núcleo/IFC/desenho + 140 verificações com a janela real.

## 0.33.0 — 2026-10-21

Fase 3, passo 9: portas com arco e tramas nos desenhos.

- Nas plantas em PDF e nas folhas, as **portas** aparecem como um arquiteto as desenha: aros, **folha aberta a 90°
  e o arco** de abertura (em vez do corte da porta fechada).
- O símbolo fica **no próprio IFC** de cada porta nova (uma representação 2D no contexto "Plan", como o Bonsai a
  faz, gerada pelo IfcOpenShell). Portas de outros programas que tragam símbolo 2D também o mostram; as que não
  trazem (e as feitas com versões anteriores do ArqBIM) continuam a aparecer cortadas.
- **Tramas pelo material** do que é cortado (plantas e cortes): alvenaria (tijolo, bloco, pedra) com tracejado a 45°,
  betão a negro, madeira em quadrícula, isolamento com tracejado fino, gesso/reboco a cinzento; sem material: escuro,
  como antes. O material conta pela sua categoria IFC ou, sem ela, pelo nome; numa parede de várias camadas, a
  mais grossa.
- Novo exemplo `exemplos/casa_desenhos.ifc` (portas com símbolo).
- Testes: 171 do núcleo/IFC/desenho (o IFC com o símbolo valida sem erros) + 139 verificações com a janela real.

## 0.32.0 — 2026-10-21

Fase 3, passo 8: folhas com várias vistas.

- **Folhas** no painel Projeto ▸ Vistas. Botão direito numa planta, corte ou alçado ▸ **Pôr na folha ▸** uma folha
  existente ou **Nova folha**. A folha abre numa janela, como vai ser impressa: as vistas arrumadas sozinhas,
  todas na mesma escala (a maior que cabe), cada uma com o nome e a escala por baixo, e a legenda.
- Na janela da folha: **arrastar** uma vista muda-a de sítio (fica lá); clicar numa vista e escolher a **escala**
  (Automática, 1:20 … 1:1000); **Delete** tira-a da folha; **Papel** A3, A2, A1 ou A0 (deitado); **Arrumar** volta
  a pôr todas nos lugares automáticos; **Exportar PDF…**.
- Quando o modelo muda, a janela avisa "Atualizar desenhos (o modelo mudou)"; o PDF sai sempre com o modelo atual.
- **Arquivo ▸ Exportar folhas em PDF…** (ou botão direito em Folhas ▸ Exportar todas): um PDF, uma página por folha,
  cada página no seu tamanho de papel.
- As folhas gravam-se no `.arqbim` ao lado do IFC (o IFC não muda). Mudar o nome a um corte muda-o nas folhas;
  apagar um corte tira-o das folhas; dois cortes não podem ter o mesmo nome.
- Testes: 170 do núcleo/IFC/desenho + 139 verificações com a janela real.

## 0.31.0 — 2026-10-21

Fase 3, passo 7: biblioteca do projeto.

- O painel **Projeto** tem uma **Biblioteca**: os **Componentes** (mesas, louças… — cada um com o número de
  cópias; também os de ficheiros do Revit) e os **Grupos** (apartamentos, casas de banho… — com o número de cópias).
- **Duplo clique** seleciona todas as cópias. **Botão direito ▸ Inserir outra cópia…** num componente: a sua caixa
  segue o rato (com inferências) e cada clique põe mais uma cópia; **Tab** roda 90°; **Esc** termina.
- Correção: uma frase repetida no ficheiro de textos fazia a mensagem "porta/janela colocada" falhar ao inserir;
  um teste novo impede chaves repetidas.
- Testes: 166 do núcleo/IFC/desenho + 130 verificações com a janela real.

## 0.30.0 — 2026-10-21

Fase 3, passo 6: linhas escondidas nos desenhos.

- Os PDF de plantas, cortes e **alçados** deixam de mostrar o que está tapado: só se desenha o que se vê
  (as paredes de trás não atravessam as da frente). Um alçado sai como um alçado desenhado.
- Como: uma "imagem de profundidade" da vista (~0,25 mm no papel) diz, ao longo de cada aresta, onde ela está
  à vista; o PDF continua vetorial (as linhas são cortadas onde deixam de se ver).
- O desenho prepara-se numa tarefa à parte (a janela não congela; num modelo grande aparece "A preparar o
  desenho…"). Prédio de 45 MB: alçado inteiro em 4,7 s, planta de um piso em 1 s; uma casa em menos de 0,4 s.
- Exemplo novo: `exemplos/casa_alcado_sul.pdf`.
- Testes: 163 do núcleo/IFC/desenho + 127 verificações com a janela real.

## 0.29.0 — 2026-10-21

Fase 3, passo 5: vistas do projeto.

- O painel **Projeto** começa por **Vistas**: **Plantas** (uma por pavimento), **Cortes** (cada corte desenhado
  fica com nome — "Corte 1", "Corte 2"… — e guardado com o projeto) e **Alçados** (Norte, Sul, Este, Oeste: o
  modelo visto de fora, desse lado). **Duplo clique abre a vista.**
- Cortes: F2 (ou botão direito ▸ Mudar o nome) muda o nome; botão direito ▸ Apagar este corte.
- A barra de estado e o PDF levam o nome da vista ("Corte A", "Alçado Norte").
- Os projetos gravados pela 0.28 (com um só corte) abrem com ele como "Corte 1".
- Testes: 162 do núcleo/IFC/desenho + 126 verificações com a janela real.

## 0.28.0 — 2026-10-21

Fase 3, passo 4: plantas e cortes em PDF vetorial.

- **Arquivo ▸ Exportar vista em PDF… (Ctrl+P)**: o corte que está à vista, ou a planta do pavimento ativo (corte a
  1,20 m), como **desenho vetorial** em A3 deitado, na maior escala habitual que cabe (1:20, 1:50, 1:100, 1:200…),
  com legenda (projeto, vista, escala, data). O que é cortado vai preenchido a escuro com traço grosso (0,50 mm);
  o que se vê para lá do corte a traço fino (0,18 mm). Linhas vetoriais: nítidas em qualquer zoom, medíveis.
- O desenho é calculado do modelo (interseção exata das formas com o plano de corte), por isso está sempre igual
  ao modelo. Exemplos em `exemplos/casa_planta.pdf` e `exemplos/casa_corte.pdf`.
- O último corte desenhado fica guardado com o projeto (ficheiro `.arqbim`): F5 volta a ele depois de reabrir.
- Benchmark (prédio de 1,2 / 7,9 / 45 MB): reabrir 0,05 / 0,28 / 1,6 s (≈ 18 s para 500 MB ✔); regenerar uma
  parede 14 / 16 / 38 ms; navegação 244 / 153 / 59 fps (o grande varia entre 57 e 78 fps neste portátil).
- Testes: 162 do núcleo/IFC/desenho + 122 verificações com a janela real.

## 0.27.0 — 2026-10-21

Fase 3, passo 3: tabelas.

- Novo painel **Tabelas** (Vista ▸ Tabelas, **Ctrl+T**), em baixo: os elementos de uma categoria (paredes, lajes,
  pilares, portas, janelas, outros) com pavimento, tipo e quantidades — comprimento, altura, espessura, **área**
  e **volume** (as aberturas descontadas: lidos da geometria real) — e os totais. "Agrupar por tipo" dá uma linha
  por tipo, com a quantidade e as somas.
- **Como numa folha de cálculo**: o nome, o comprimento e a altura de uma parede, a altura de um pilar escrevem-se
  na célula (um passo de desfazer, como no painel Propriedades).
- Clicar numa linha seleciona o elemento no 3D (e a seleção do 3D aparece na tabela); duplo clique enquadra-o.
- **Exportar CSV…**: a tabela para o Excel (";" e vírgula decimal).
- Funciona com ficheiros de outros programas: as medidas vêm das quantidades base do IFC (o Revit escreve-as).
- Testes: 158 do núcleo/IFC/desenho + 121 verificações com a janela real.

## 0.26.0 — 2026-10-21

Fase 3, passo 2: cortes ao vivo.

- Nova ferramenta **Corte** (barra de ferramentas e menu Vista): dois cliques desenham a linha de corte no pavimento
  (com inferências), um terceiro clique escolhe o lado para onde o corte olha (setas na pré-visualização). A
  vista passa a ser esse corte: o que está do lado de cá da linha é retirado, o que o plano atravessa fica **a
  escuro**, todos os pavimentos aparecem, quase sem perspetiva.
- **Vista ▸ Último corte (F5)** volta ao último corte desenhado; F8 (ou outra vista) volta ao 3D; orbitar dá o
  edifício aberto pelo corte.
- Em corte pode-se selecionar o que está cortado; as inferências ignoram o que foi retirado.
- Testes: 155 do núcleo/IFC/desenho + 117 verificações com a janela real (o corte desenhado com o rato, a cor
  da parede cortada na imagem).

## 0.25.0 — 2026-10-21

Fase 3, passo 1: planta ao vivo.

- **Vista ▸ Planta do pavimento ativo (F4)**: o pavimento ativo visto de cima, quase sem perspetiva, **cortado a
  1,20 m** acima da sua cota; o que o corte atravessa (paredes, caixilhos, portas) fica **a escuro (poché)**, como
  numa planta desenhada. Só esse pavimento aparece; sem grelha. É o próprio modelo: qualquer mudança aparece logo.
- Page Up / Page Down mudam a planta para o pavimento de cima / de baixo; orbitar dá um corte 3D à mesma altura;
  F4 outra vez, F8, F2 ou F3 voltam ao 3D.
- Em planta pode-se selecionar (clicar no que está cortado seleciona-o) e desenhar: as inferências ignoram o que
  está acima do corte e os pontos encontrados ficam na cota do pavimento.
- Testes: 155 do núcleo/IFC/desenho + 115 verificações com a janela real (a cor da parede cortada na imagem).

## 0.24.0 — 2026-10-21

Fase 2, passo 8: a 1.ª abertura aos poucos.

- Um ficheiro grande aberto **pela primeira vez** (por exemplo vindo do Revit) já não fica em branco enquanto o
  motor de geometria trabalha: lido o IFC, os elementos **aparecem à medida que são calculados** (o primeiro lote
  ao fim de 0,3 s, depois com intervalos maiores). Pode-se orbitar e ver; editar quando terminar. A barra de
  estado mostra a percentagem.
- Enquanto a janela põe um lote no ecrã, a leitura espera a sua vez (as duas partilham o "cadeado" do Python).
- Juntar elementos novos a um lote escreve só os novos no fim (sem refazer o lote inteiro); a árvore do projeto
  só é refeita no fim da abertura.
- Benchmark (prédio de 7,9 / 45 MB): **1.ª abertura até aos primeiros elementos 0,95 / 2,7 s** (antes 6,7 / 34 s
  sem nada no ecrã); tudo pronto em 6,0 / 31 s. Reabrir: 0,27 / 1,5 s.
- Testes: 154 do núcleo/IFC/desenho + 112 verificações com a janela real.

## 0.23.0 — 2026-10-21

Fase 2, passo 7: abrir a partir das formas guardadas.

- Um ficheiro já aberto antes aparece **logo**, desenhado a partir das formas guardadas (que agora guardam também
  a classe, o nome e o pavimento de cada elemento, os pavimentos e a estrutura do projeto), enquanto o IFC é lido
  por trás. Entretanto pode-se orbitar, deslocar, aproximar e mudar de vista; desenhar, editar, selecionar e
  gravar esperam — a barra de estado diz "A ler o IFC de… pode orbitar e ver; editar quando terminar", com
  Cancelar. Quando a leitura acaba, os elementos no ecrã ficam (não são refeitos) e passam a ser editáveis.
- Benchmark (prédio de 1,2 / 7,9 / 45 MB): **reabrir até à 1.ª imagem 0,06 / 0,30 / 1,6 s**, pronto a editar
  0,15 / 0,68 / 3,3 s. Estimativa para 500 MB: **17–19 s — a meta "< 20 s" cumpre-se ao reabrir**.
- Testes: 153 do núcleo/IFC/desenho + 111 verificações com a janela real (ver enquanto lê, cancelar a meio).

## 0.22.0 — 2026-10-21

Fase 2, passo 6: coordenadas recentradas.

- Um IFC **georreferenciado** (por exemplo exportado do Revit com coordenadas partilhadas, o edifício a centenas
  de km da origem) é agora trabalhado **perto da origem**: a placa gráfica usa números de 32 bits, que a 500 km
  só distinguem ~3 cm — as arestas tremiam e as inferências falhavam. O IFC guarda sempre as coordenadas reais:
  tudo o que se desenha ou move é gravado no sítio verdadeiro.
- A barra de estado avisa quando um modelo foi recentrado (com a posição E / N do edifício).
- Os esboços e linhas guia (ficheiro `.arqbim`) guardam a origem usada.
- Exemplo para testar: `exemplos/casa_georreferenciada.ifc` (`scripts/casa_exemplo.py --georreferenciada`).
- Regenerar mais leve: depois de uma edição, o lote do elemento reaproveita a memória da placa gráfica (só os
  dados são reenviados), em vez de criar buffers novos — a imagem seguinte passa de ~40–60 ms para ~18 ms no
  prédio grande. Benchmark: **regenerar uma parede 13 / 19 / 41 ms** (pequeno / médio / grande).
- O benchmark desenha uma imagem antes de cada edição medida (como quando o rato se aproxima da parede): a placa
  gráfica do portátil abranda o relógio quando fica parada e as primeiras imagens levam ~40 ms em vez de ~14 ms.
- Testes: 151 do núcleo/IFC/desenho + 108 verificações com a janela real.

## 0.21.0 — 2026-10-21

Fase 2, passo 5: árvore do projeto.

- Novo painel **Projeto** (separador ao lado de Pavimentos): Projeto → Terreno → Edifício → pavimentos (o mais
  alto em cima, com a cota e quantos elementos tem) → categorias (Paredes, Lajes, Portas, Janelas…) → elementos;
  no fim, os esboços (fora do IFC). Lê a estrutura do próprio IFC, por isso funciona com ficheiros do Revit.
- **Clique** seleciona no 3D (uma categoria ou um pavimento: tudo o que tem; Ctrl+clique junta); **duplo
  clique** enquadra a vista. O que se seleciona no 3D aparece marcado na árvore.
- Com "Ver só o pavimento ativo", clicar em elementos de outro pavimento passa a esse pavimento.
- Num modelo grande a árvore não pesa: as categorias só listam os elementos quando se abrem, e uma edição que só
  muda a forma de um elemento não a refaz.
- Testes: 148 do núcleo/IFC/desenho + 107 verificações com a janela real.

## 0.20.0 — 2026-10-21

Fase 2, passo 4: abrir em segundo plano.

- Abrir um ficheiro já **não congela a janela**: ler o IFC, calcular (ou ler da cache) as formas e preparar o
  desenho correm numa tarefa à parte. Se demorar mais de 0,4 s aparece uma janela de progresso ("A ler…",
  "A calcular as formas 3D… n %", "A preparar o desenho…") com **Cancelar** — o projeto anterior continua aberto.
- Ao arrancar, o programa prepara logo os programas da placa gráfica (antes pagos na 1.ª abertura).
- A cache de geometria guarda também os elementos sem forma 3D (não são tentados outra vez).
- Benchmark (prédio de 1,2 / 7,9 / 45 MB): **reabrir 0,10 / 0,63 / 3,8 s** (antes 1,1 / 1,3 / 4,5 s); 1.ª vez
  0,9 / 6,1 / 34 s; **maior pausa da janela ao abrir 22 / 118 / ~500 ms** (antes: a janela parada o tempo todo).
- Testes: 147 do núcleo/IFC/desenho + 101 verificações com a janela real (abrir, cancelar, reabrir).

## 0.19.0 — 2026-10-21

Fase 2, passo 3: cache de geometria em disco.

- As formas 3D já calculadas de todos os elementos (com os vãos recortados e as arestas visíveis) ficam
  guardadas em `%LOCALAPPDATA%\ArqBIM\geometria` ao gravar e ao abrir. Ao reabrir um ficheiro que não mudou,
  o programa lê-as em vez de as calcular de novo. Se o IFC tiver mudado (por exemplo gravado por outro programa)
  ou a cache estiver estragada, tudo é calculado como antes. Nada é escrito na pasta do projeto nem no IFC.
- A barra de estado diz quanto tempo demorou a abrir e se as formas vieram da cache.
- Benchmark (prédio de 1,2 / 7,9 / 45 MB): **reabrir 1,1 / 1,3 / 4,5 s** (1.ª vez 1,6 / 6,7 / 34,5 s). O benchmark
  mede a 1.ª abertura (cache apagada) e a reabertura num processo novo, como quem abre o programa outra vez.
- Abrir também ficou mais leve por elemento: normais calculadas de uma vez para o modelo todo, caixas das
  inferências e cores sem contas repetidas.
- Testes: 147 do núcleo/IFC/desenho (4 novos para a cache) + 98 verificações com a janela real.

## 0.18.0 — 2026-10-21

Fase 2, passo 2: inferências só perto do cursor.

- As inferências (extremidade, ponto médio, aresta, guia…) já não examinam o modelo todo a cada movimento do
  rato: cada elemento guarda os seus pontos e a sua caixa, e só os elementos por onde passa o raio do cursor
  são examinados. Uma alteração só refaz os pontos do elemento alterado.
- Benchmark (prédio de 1,2 / 7,9 / 45 MB): **um movimento do rato 1,2 / 2,4 / 8,6 ms** (antes 5 / 36 / 144 ms);
  **depois de uma alteração 1,6 / 3,5 / 10 ms** (antes 22 / 100 / 530 ms). Nova meta no benchmark: < 16 ms.
- O benchmark passa a medir as inferências em vários pontos da imagem e o 1.º movimento depois de uma alteração.
- Testes: 143 do núcleo/IFC/desenho + 97 verificações com a janela real.

## 0.17.0 — 2026-10-21

Fase 2, passo 1: desenho em lotes.

- Os elementos IFC passam a ser desenhados **em lotes** (muitos elementos num só objeto gráfico, por pavimento)
  em vez de um objeto por elemento. Selecionar muda só as cores desse elemento dentro do lote; editar um elemento
  refaz só o seu lote.
- Depois de cada ação o programa só olha para os elementos que essa ação tocou (lido da transação IFC), em vez
  de percorrer o modelo todo; uma edição triangula só o que mudou, sem arrancar as tarefas paralelas.
- Inferências: os candidatos dos elementos IFC são preparados em blocos (7× mais rápido).
- Benchmark (prédio de 1,2 / 7,9 / 45 MB): **navegação 232 / 99 / 64 fps** (antes 41 / 10 fps), **regenerar uma
  parede 15 / 21 / 33 ms** (antes 64 / 209 ms), abrir 1,6 / 6,8 / 35 s (antes 3,4 / 18,5 s), memória −40 %.
  Navegar, regenerar e selecionar cumprem as metas mesmo no prédio grande; abrir ainda não (é sobretudo o
  motor de geometria — passo seguinte: cache em disco). Detalhes em `ARQUITETURA.md` ("Desempenho").
- Testes: 140 do núcleo/IFC/desenho + 97 verificações com a janela real.

## 0.16.0 — 2026-10-21

Benchmark (instruções, secção 6).

- **`Benchmark.bat`** / `scripts/benchmark.py`: gera um edifício de teste com os comandos do próprio programa
  (apartamentos em grupo, numa grelha, repetidos em todos os pisos — pequeno, médio ou grande) ou mede qualquer
  IFC (por exemplo exportado do Revit). Mede abrir até à 1.ª imagem, triangular, navegar (fps), selecionar,
  regenerar uma parede, inferências, gravar e memória, contra as metas.
- Resultados acumulados em `benchmark/resultados.md` (legível) e `benchmark/resultados.jsonl` (para comparar fases).
- Primeira medição e diagnóstico em `ARQUITETURA.md` ("Desempenho"): selecionar já cumpre a meta; abrir, navegar
  e regenerar ainda não — o plano da Fase 2 começa pelo desenho em lotes.

## 0.15.0 — 2026-10-20

Grupos BIM e piso tipo.

- **Criar grupo (Ctrl+G)**, no menu BIM: os elementos selecionados (paredes, lajes, componentes…; as portas e
  janelas das paredes entram sozinhas) passam a ser um grupo com nome — um apartamento, uma casa de banho. No IFC é
  um `IfcGroup`, como nos grupos de modelo do Revit.
- **Clicar** num elemento do grupo seleciona o grupo inteiro; **clicar outra vez** escolhe só esse elemento.
- **Copiar o grupo** (Mover + Ctrl, séries 3x, ou Repetir nos pavimentos) faz cópias ligadas: **mudar um elemento
  numa cópia muda-o em todas** — medidas (Push/Pull, painel), tipo, Psets, portas e janelas novas, movidas ou
  apagadas, mover/rodar uma parede (mesmo em cópias rodadas).
- **Repetir nos pavimentos…** (menu BIM): copia a seleção para os pavimentos escolhidos, no mesmo sítio em planta —
  o **piso tipo**. Com um grupo, os pisos ficam ligados.
- **Desagrupar**: aquela cópia deixa de seguir as outras.
- Testes: 133 do núcleo/IFC + 97 verificações com a janela real.

## 0.14.0 — 2026-10-20

Componentes.

- **Criar componente (G)**, no menu BIM: os volumes de esboço selecionados passam a ser um componente com nome e
  natureza (**Mobiliário**, **Louça sanitária** ou **Elemento genérico**). No IFC é um **tipo** (`IfcFurnitureType`,
  `IfcSanitaryTerminalType`, `IfcBuildingElementProxyType`) que guarda a forma **uma só vez**; cada cópia é uma
  instância que a reutiliza (como as famílias do Revit e os componentes do SketchUp; ficheiro mais leve).
- **Copiar** um componente (Mover + Ctrl, séries 3x…) faz mais cópias do mesmo componente.
- **Editar componente** (menu BIM): a cópia escolhida vira um esboço para mudar a forma com Push/Pull, Retângulo,
  Linha…; **Fechar componente** grava a forma nova e **todas as cópias mudam**. Cada passo desfaz-se com Ctrl+Z;
  um componente a meio da edição fica gravado e pode ser fechado depois de reabrir o projeto.
- Painel Propriedades: "Componente: Mesa (3 cópias)". Push/Pull numa cópia explica como a editar.
- Testes: 127 do núcleo/IFC + 93 verificações com a janela real.

## 0.13.0 — 2026-10-20

Paredes que ficam ligadas.

- Os cantos e encontros em T feitos pela ferramenta Parede ficam **registados no IFC** (`IfcRelConnectsPathElements`,
  como no Revit e no ArchiCAD).
- **Mover ou Rodar uma parede**: as paredes ligadas a ela **esticam ou encolhem** até voltarem a encontrá-la —
  os cantos continuam fechados (em topo ou em meia-esquadria). Se já não se podem encontrar (ficariam paralelas,
  em ângulo agudo demais, ou o canto ficaria para trás), a ligação é largada e ficam como estão.
- **Mudar o tipo (espessura)** de uma parede refaz os seus cantos: as vizinhas encostam-se à face nova.
- **Push/Pull na ponta** de uma parede solta essa ponta (o canto é desfeito de propósito); a altura não mexe nas
  ligações. Apagar uma parede apaga as suas ligações.
- Copiar uma sala inteira: as cópias ficam ligadas entre si.
- Testes: 123 do núcleo/IFC + 90 verificações com a janela real.

## 0.12.0 — 2026-10-20

Copiar.

- **Copiar com Mover e Rodar** (como no SketchUp): tocar em **Ctrl** liga/desliga a cópia (ou segurar Ctrl no
  último clique). A dica em baixo começa por "+ CÓPIA"; o original fica no sítio e as cópias ficam selecionadas.
- **Séries de cópias**: logo a seguir a copiar, digitar **3x** + Enter faz 3 cópias com o mesmo espaçamento (ou
  ângulo — cópias à volta de um centro); **/3** divide a distância (ou o ângulo) em 3. Outra medida corrige.
  Um só Ctrl+Z desfaz a série.
- **Elementos IFC copiados com tudo**: tipo, materiais, Psets e quantidades; uma parede leva cópias das suas
  portas, janelas, vãos e nichos. As cópias continuam editáveis e recebem o número seguinte ("Parede 2").
- **Copiar uma porta ou janela** sozinha: a cópia fica na mesma parede, com o seu vão (nunca sai da parede).
- Testes: 116 do núcleo/IFC + 88 verificações com a janela real.

## 0.11.0 — 2026-10-20

Cantos em qualquer ângulo, Mover e Rodar.

- **Cantos de paredes em ângulo** (de 15° a 165°): cortados em **meia-esquadria**, sem sobreposição nem falha,
  dentro de um contorno ou com paredes desenhadas antes. Encontros em T inclinados: a nova parede é cortada ao
  longo da face da outra. A 90° continua o canto "em topo". No IFC a parede é um perfil em trapézio extrudido
  (sem operações booleanas); os ângulos de corte ficam no Pset `ArqBIM_Parametros`, o comprimento e as
  quantidades são os do eixo (volume exato). Mexer numa ponta com Push/Pull ou no painel volta a pô-la a esquadro.
- **Mover (M)**: clicar no ponto de base e no destino (inferências, eixos vermelho/verde/azul) ou digitar a
  distância. Move a seleção, ou o objeto sob o cursor. Uma parede leva as suas portas e janelas; **uma porta ou
  janela sozinha desliza ao longo da parede** (e para cima/baixo, o peitoril) sem nunca sair dela.
- **Rodar (Q)**: clicar no centro, num ponto que dá a direção de partida e na direção final (o transferidor agarra
  de 15 em 15°), ou digitar o ângulo. Roda à volta de um eixo vertical.
- Em ambos, digitar logo a seguir corrige a última ação; Ctrl+Z desfaz. Funcionam com esboços e elementos IFC
  (de qualquer programa: só a colocação muda, a geometria não).
- Trocar de ferramenta já não desfaz a seleção (selecionar e depois M/Q).
- Testes: 110 do núcleo/IFC + 84 verificações com a janela real.

## 0.10.0 — 2026-10-20

Pavimentos e paredes desenhadas pela face.

- **Painel Pavimentos** (à direita, por cima de Propriedades): lista com nome e cota, o mais alto em cima; o
  pavimento ativo em negrito. Clique = passar a desenhar nesse pavimento (a grelha e o plano de desenho sobem
  para a sua cota). Duplo clique no nome ou na cota para os mudar — **mudar a cota leva tudo o que lá está**
  (paredes, lajes, portas, janelas, vãos). **+ Novo** cria um pavimento 3,00 m acima do mais alto. **Apagar** só
  um pavimento vazio. **Ver só o pavimento ativo** esconde os outros. **PgUp / PgDn**: pavimento acima / abaixo.
  Também no menu BIM. A barra de estado mostra o pavimento ativo.
- Paredes, lajes e portas ficam no pavimento ativo (`IfcBuildingStorey` com cota, colocação relativa ao
  pavimento); Classificar põe cada volume no pavimento onde assenta. O Revit lê os pavimentos como níveis.
- Laje desenhada na cota de um pavimento = laje de piso desse pavimento (topo na cota).
- **Paredes pela face**: na ferramenta Parede, **Tab** muda a linha desenhada entre eixo, face esquerda e face
  direita (no sentido em que se desenha). Um contorno exterior digitado com 10 × 8 fica com 10,00 × 8,00 por fora.
  Os cantos fecham-se limpos também assim, e com paredes desenhadas antes em separado.
- Testes: 97 do núcleo/IFC + 77 verificações com a janela real.

## 0.9.0 — 2026-10-20

Linha, Fita métrica e cantos entre paredes separadas.

- **Ferramenta Linha (L)**: clicar ponto a ponto; cada segmento fica guardado. Trava nos eixos **vermelho, verde e
  azul** a partir do último ponto (dica "No eixo …"); agarra a extremidades, pontos médios, arestas, guias e
  interseções. Comprimento digitado + Enter na direção do rato. Voltar ao 1.º ponto ("Fechar contorno") transforma
  o contorno numa **face de qualquer forma** (L, U, triângulo…) pronta para Push/Pull. Esc termina: as linhas abertas
  ficam (selecionam-se, apagam-se, gravam-se com os esboços).
- **Fita métrica (T)**: clicar numa aresta, afastar e clicar ou digitar a distância → **linha guia** paralela
  (tracejada). Clicar num ponto e noutro → mede a distância. Digitar logo a seguir corrige a última guia.
- Inferências novas em todas as ferramentas: **"Na guia"** e **"Interseção"** (guia × guia, guia × aresta).
- **Editar ▸ Apagar linhas guia** (um passo de desfazer). As guias gravam-se no `.arqbim`, nunca no IFC.
- **Paredes desenhadas em separado unem os cantos**: começar ou terminar na ponta do eixo de uma parede existente
  (dica "Eixo da parede") faz um canto limpo como dentro de uma corrente; começar no meio do eixo faz uma junta em T.
- Selecionar também apanha linhas (clicar perto delas). Painel Propriedades mostra o comprimento total das linhas e
  a área de uma face ainda não puxada.
- Push/Pull em faces não retangulares (pré-visualização correta de formas em L).
- Correção: "▸" não aparecia nos textos dentro da vista 3D.
- Testes: 88 do núcleo/IFC + 71 verificações com a janela real.

## 0.8.0 — 2026-10-20

Editar elementos que já são IFC (o "Voltar" do fluxo híbrido) e painel de propriedades editável (entrega 4 da Fase 1).

- **Push/Pull em elementos IFC**: topo da parede = altura, pontas = comprimento; bordas da laje = contorno;
  topo do pilar = altura. Pré-visualização da nova caixa; inferências e medida digitada; digitar logo a seguir corrige.
  Face lateral da parede / topo da laje / lados do pilar explicam que a medida vem do tipo.
- **Painel Propriedades editável**: nome, **tipo** (lista; mudar o tipo de uma parede muda a espessura e refaz
  portas, janelas e nichos), comprimento/altura, contorno da laje, altura do pilar; portas/janelas: distância ao
  início/fim da parede e peitoril; valores dos Psets (caixas de verificação, texto, números). Quantidades (Qto)
  recalculadas sozinhas.
- Proteções: nada fica com menos de 10 cm; nenhuma porta, janela ou vão fica fora do elemento (mensagem em português).
- Elementos criados pelo ArqBIM levam o Pset `ArqBIM_Parametros` (editáveis); os de outros programas ficam só leitura.
- Correção: um valor digitado no Push/Pull logo após passar o cursor por uma aresta da própria face ia para o lado errado.
- `exemplos/casa_exemplo.ifc` regenerado (editável).
- Testes: 70 do núcleo/IFC + 57 verificações com a janela real.

## 0.7.0 — 2026-10-20

Pedido do dono do projeto: Push/Pull que fura, para abrir vãos.

- **Esboço**: um retângulo desenhado numa face e empurrado para dentro faz um **nicho**; ao tocar ou passar a face
  de trás, faz um **furo de lado a lado** (operação booleana). Dica no ecrã "Atravessa: abre vão". Se não houver
  como furar (face de trás já dividida), para 1 mm antes.
- **Parede ou laje IFC**: retângulo desenhado na face e empurrado para dentro → **vão IFC** (`IfcOpeningElement`,
  OPENING) se atravessar, ou **nicho** (`IfcOpeningElement`, RECESS) com a profundidade digitada. O retângulo é
  consumido. Digitar outra medida logo a seguir corrige o vão/nicho.
- **Classificar** um volume com furos: os furos passam a vãos IFC na parede/laje (pilares com furos são recusados).
- Os furos do esboço gravam-se no ficheiro `.arqbim` e sobrevivem a fechar/abrir.
- Testes: 63 do núcleo/IFC + 50 verificações com a janela real.

## 0.6.0 — 2026-10-20

Depois do primeiro teste do dono do projeto ("não consegui fazer a parede e a laje"):

- **Ferramenta Parede (W)**: clicar no início e em cada canto (ou digitar os comprimentos), voltar ao início fecha o
  contorno. Trava nos eixos vermelho/verde, agarra a pontos. Cantos a 90° limpos (sem sobreposição nem falha).
  `4,50;3,00` muda também a altura (2,80 m por omissão). Tipo em BIM ▸ Parede.
- **Ferramenta Laje**: dois cantos ou medidas digitadas. No chão = laje de piso (topo no nível 0); num canto do topo
  das paredes = laje de cobertura. Tipo em BIM ▸ Laje.
- Medidas digitadas **sem clicar antes**: Retângulo começa no ponto sob o cursor; Push/Pull atua na face sob o cursor;
  Parede e Laje idem.
- O teclado funciona **qualquer que seja o foco** na janela (painel, barra de ferramentas…).
- **Classificar sem seleção**: escolher o tipo e depois clicar no volume.
- Volume que não pode ser classificado: janela a explicar porquê e o que fazer.
- Porta/Janela sobre um esboço: explica que é preciso torná-lo parede.
- Mensagens de "próximo passo" depois de cada ação; mensagens ficam 10 s.
- Vista ▸ Propriedades reabre o painel se for fechado.
- Correção nas inferências: cantos da própria face sob o cursor eram por vezes tratados como escondidos.
- Testes: 54 do núcleo/IFC + 45 verificações com a janela real (incluindo o percurso de um iniciante).

## 0.5.0 — 2026-10-20

- **Portas (D) e janelas (J)** em paredes IFC: passar o cursor sobre a parede mostra o contorno e a cota até à
  extremidade mais próxima; agarra ao **centro da parede**; clique para colocar ou digite a distância (ex.: `0,60`);
  digitar logo a seguir move a última colocada.
- Cada porta/janela abre um **vão real** (`IfcOpeningElement` + `IfcRelVoidsElement`) e preenche-o
  (`IfcRelFillsElement`), com tipo (`IfcDoorType`/`IfcWindowType`), caixilho/aro/folha paramétricos do IfcOpenShell,
  pavimento e Pset. A parede é recortada no ecrã.
- Apagar uma porta/janela fecha o vão; apagar uma parede leva as suas portas e janelas. Tudo com desfazer/refazer.
- Catálogo: portas 80×210 e 90×210; janelas 120×120 e 150×120 (peitoril 1,00) e basculante 60×60 (peitoril 1,60).
- `exemplos/casa_exemplo.ifc`: casa de aceitação da Fase 1 (4 paredes, laje, 2 portas, 4 janelas), validada.
- Testes: 50 do núcleo/IFC + 37 verificações com a janela real.

## 0.4.0 — 2026-10-20

- **IFC nativo**: o projeto vive em memória como IFC4 (IfcOpenShell). Arquivo ▸ Guardar (Ctrl+S) grava `.ifc`
  e valida-o; Arquivo ▸ Abrir (Ctrl+O) abre `.ifc` (também de outros programas). Pergunta antes de perder alterações.
- **Classificar** (BIM ▸ Classificar como…, ou botão IFC na barra): um volume de esboço vira `IfcWall`, `IfcSlab`
  ou `IfcColumn` paramétrico, com tipo (`IfcWallType`…), camadas/perfil de material, pavimento, Pset e quantidades.
- Catálogo inicial: paredes alvenaria 15/20 cm e drywall 10 cm; lajes de concreto 12/15 cm; pilares 20×20 e 30×30.
- Desfazer/refazer cobre as alterações IFC (transações do IfcOpenShell, mesmo GlobalId).
- Painel **Propriedades**: classe IFC, tipo, camadas com espessuras, Psets e quantidades.
- Esboços ficam fora do IFC, num ficheiro ao lado (`nome.arqbim`).
- Testes: 43 do núcleo/IFC (incluindo validação completa IFC4 com regras WHERE) + 32 verificações com a janela real.

## 0.3.0 — 2026-10-20

- **Inferências** (snaps) estilo SketchUp, com cores e dica de texto: extremidade (verde), ponto médio
  (azul-claro), origem (amarelo), na aresta (vermelho), na face (azul). Pontos escondidos atrás de faces são ignorados.
- Retângulo: os dois cantos agarram-se a pontos e arestas; inferência "Quadrado" (diagonal magenta).
- Push/Pull **até ao ponto**: passar o cursor por um ponto de outro volume iguala a distância.
- Navegação nova: orbitar à volta do ponto sob o cursor, zoom para onde aponta o cursor.
- Faces soltas pousadas sobre outras deixam de "piscar" e são escolhidas primeiro ao clicar.
- Testes: 31 do núcleo + 25 verificações com a janela real.

## 0.2.0 — 2026-10-20

- **Programa independente** (janela própria), substitui o protótipo em Blender. Python 3.13 + Qt + wgpu.
- Vista 3D com céu, grelha, eixos vermelho/verde/azul, sombreado e arestas pretas; orbitar (botão do meio),
  deslocar (Shift + botão do meio), zoom (roda), enquadrar tudo (Shift+Z), vistas isométrica/topo/frente (F8/F2/F3).
- Ferramentas **Selecionar** (Espaço), **Retângulo** (R) e **Push/Pull** (P), com caixa "Medidas".
- Retângulo dentro de uma face divide-a: puxar faz varanda, empurrar faz nicho.
- Desfazer/refazer (Ctrl+Z / Ctrl+Y), apagar (Delete), corrigir a última medida digitando outra.
- Testes: 23 do núcleo + 18 verificações com a janela real.

## 0.1.0 — 2026-10-20

- Protótipo como add-on do Blender (arquivado em `arquivo/prototipo_blender`).
