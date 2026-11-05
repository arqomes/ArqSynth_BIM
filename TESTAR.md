# Como testar — versões 0.153 a 0.197

Passos numerados, clique a clique, para experimentar o que cada versão trouxe. Os ficheiros de exemplo estão em
`C:\BIM\tests\saida_gui` (os testes automáticos fazem-nos de cada vez que correm):
`planta_digitalizada.png`, `levantamento.csv`, `levantamento.dxf`, `planta_cad.dxf`, `planta_cad_completa.dxf`,
`sala_digitalizada.ply`, `sala_com_parede.ply`.

Para começar cada teste: abra o programa com **ArqSynth BIM.bat** e, se já estiver aberto, faça **Ficheiro ▸ Novo**
(Ctrl+N).

---

## 0.153 — Escala

1. Clique no separador **Conceito** (em cima, à esquerda).
2. Clique no botão **Retângulo** (barra da esquerda).
3. Clique num ponto do chão, escreva `3;2` e carregue em Enter: aparece um retângulo de 3 × 2 m.
4. Clique no botão **Selecionar** (a seta) e depois clique no retângulo (fica azul).
5. Clique no botão **Escala** (o quadrado pequeno com o grande e a seta azul).
6. Clique no canto de baixo à esquerda do retângulo (o ponto base, que não se mexe).
7. Escreva `2` e carregue em Enter: o retângulo passa a 6 × 4 m, a partir do mesmo canto. A barra de baixo diz
   «Escala 2 em 1 esboços».
8. Carregue em Ctrl+Z: volta a 3 × 2.
9. Repita os passos 5 e 6 e escreva `1;1;2` e Enter num volume puxado (Push/Pull): só fica mais alto.

## 0.154 — Imagem de fundo

1. Clique em **Ficheiro ▸ Importar imagem de fundo…**.
2. Escolha `planta_digitalizada.png` e clique em Abrir: a imagem fica deitada no chão, meio transparente, e a
   ferramenta **Calibrar imagem** começa sozinha.
3. Clique na imagem no início da cota vermelha (o traço da esquerda).
4. Clique no fim dessa cota (o traço da direita). Enquanto mexe o rato, a caixa Medidas diz quanto mede.
5. Escreva `8` e carregue em Enter: a imagem cresce para a cota medir 8 m, e fica bloqueada.
6. Clique num ponto do modelo onde quer esse primeiro ponto (por exemplo, a origem, onde se cruzam o eixo vermelho
   e o verde).
7. Carregue em Esc para a deixar com o ângulo que tem.
8. Clique em **Vista ▸ Imagens de fundo…**: a imagem está na lista. Experimente a **Opacidade** e a caixa
   **Visível**; para a calibrar outra vez, tire a marca de **Bloqueada** e clique em **Calibrar**.
9. Grave (Ctrl+S), feche e abra o projeto: a imagem continua lá.

## 0.155 — Terreno por pontos

1. Clique em **Ficheiro ▸ Importar pontos de levantamento…**.
2. Escolha `levantamento.csv` e clique em Abrir: aparece o terreno, selecionado, com as curvas de nível. A barra de
   baixo diz que os pontos estavam em coordenadas do levantamento e que o projeto passou a usá-las.
3. Veja nas **Propriedades** (à direita): os pontos, a área, as cotas, **Curvas de nível de** e **Base abaixo do
   ponto mais baixo**. Mude «Curvas de nível de» para `0,5` e carregue em Enter: as curvas ficam mais juntas.
4. Carregue em F4 (planta): o terreno aparece com as curvas, e o monte acima do corte aparece cortado.
5. Para acrescentar um ponto: com o terreno selecionado, clique no separador **Conceito** e no botão **Terreno por
   pontos** (o monte com as cruzes azuis), escreva `3` e Enter, clique num sítio dentro do terreno e carregue em
   Enter: o terreno sobe até 3 m nesse ponto.
6. Para fazer um terreno à mão num projeto novo: no mesmo botão, escreva a cota de cada ponto e clique onde ele
   fica (pelo menos 3), e carregue em Enter no fim.

## 0.156 — Terreno de um DXF, inclinações e cotas de nível

1. Clique em **Ficheiro ▸ Terreno a partir de um DXF…** e escolha `levantamento.dxf`.
2. Na janela aparecem as camadas com cota (PONTOS, COTAS), já marcadas. A camada das paredes, em 2D, não aparece.
   Clique em OK.
3. Clique em **Vista ▸ Inclinações do terreno**: o terreno fica amarelo (10 a 15 %). A legenda está na barra de
   baixo. Clique outra vez para desligar.
4. Carregue em F4 (planta). Clique no separador **Docs** e no botão **Desenho 2D**; na barra de cima escolha
   **Desenhar: Cota de nível**.
5. Clique num ponto do terreno: aparece uma cruz e a cota («+1,20»).
6. Volte ao terreno, acrescente-lhe um ponto mais alto nesse sítio (como no passo 5 da 0.155): a cota de nível
   muda sozinha.

## 0.157 — Plataformas, aterro e escavação

1. Faça o terreno do teste 0.155 ou 0.156.
2. Carregue em F4 (planta). Clique no separador **Conceito** e no botão **Plataforma**.
3. Escreva `1,5` e Enter (a cota da plataforma). Sem isto, a cota é a do terreno no primeiro canto.
4. Clique num canto e depois no canto oposto: a plataforma fica feita, com os taludes à volta. A barra de baixo diz
   a escavação e o aterro.
5. Na barra de cima pode escolher a **Forma** (retângulo ou polígono) e os taludes (1:1, 2:3, a prumo…), antes de
   fazer outra.
6. Clique em **Vista ▸ Aterro e escavação…**: a lista mostra a plataforma, com a cota, a área e a terra que tira e
   põe, e os totais. **Apagar a plataforma** devolve o terreno do levantamento.
7. Carregue em F4 outra vez para o 3D: a plataforma está cortada no terreno.

## 0.158 — Ligar um DXF

1. Carregue em F4 (planta do Térreo).
2. Clique em **Ficheiro ▸ Ligar um desenho DXF…** e escolha `planta_cad.dxf`: a planta aparece em linhas azuladas.
   A barra de baixo diz «em mm; origem com origem».
3. Clique no separador **BIM** e no botão **Parede**. Leve o rato a um canto da planta do DXF: o snap agarra-se ao
   canto. Desenhe uma parede pelo DXF e carregue em Esc.
4. Clique em **Vista ▸ Desenhos CAD ligados…**: tire a marca da camada **COTAS** e clique em Fechar: a linha da
   cota desaparece.
5. Grave, feche e abra: o desenho continua ligado, com a camada escondida.

## 0.159 e 0.160 — Modelo a partir do desenho

1. Num projeto novo, carregue em F4 e ligue `planta_cad_completa.dxf` (como no passo 2 da 0.158).
2. Clique em **BIM ▸ Modelo a partir do desenho…**.
3. Veja as três listas: **Paredes** (PAREDES marcada), **Portas e janelas** (JANELAS e PORTAS marcadas),
   **Mobiliário** (MOBILIARIO marcada). Por baixo: «4 paredes encontradas (4 × 20 cm). 1 portas, 1 janelas, 2
   móveis.», e a azul na planta.
4. Clique em OK: aparecem as paredes, a porta no vão, a janela e as duas mesas.
5. Carregue em F4 para ver em 3D. Ctrl+Z desfaz tudo de uma vez.
6. Ligue outra vez o DXF num projeto novo e abra a mesma janela: as camadas já vêm marcadas pelo perfil guardado.

## 0.161 — Ligar uma nuvem de pontos

1. Clique em **Ficheiro ▸ Ligar uma nuvem de pontos…** e escolha `sala_digitalizada.ply`: aparece a sala em pontos.
2. Rode a vista (botão do meio do rato) para a ver por fora.
3. Carregue em F4 (planta): vê-se a fatia da nuvem abaixo do corte, com as paredes em linhas de pontos.
4. Clique em **Vista ▸ Nuvens de pontos ligadas…**: mude o **Tamanho dos pontos** para 3 e clique em Fechar.

## 0.162 — Modelo a partir da nuvem

1. Num projeto novo, ligue `sala_com_parede.ply` (como na 0.161).
2. Clique em **BIM ▸ Modelo a partir da nuvem…**: o chão (0,00) e a altura (2,80) já vêm encontrados, e por baixo
   «5 paredes encontradas (1 × 10 cm, 4 × 30 cm)», a azul na planta.
3. Clique em OK: aparecem as cinco paredes e a laje do piso. Ctrl+Z desfaz.

## 0.163 — Modelo analítico e verificação

1. Num projeto novo, clique no separador **Estrutura**.
2. Desenhe quatro pilares nos cantos de um retângulo de 6 × 4 m (botão **Pilar**).
3. Clique no botão **Sapatas** (faz uma sapata debaixo de cada pilar).
4. Desenhe as quatro vigas por cima, de pilar a pilar (botão **Viga**).
5. Desenhe mais um pilar afastado e suba-o para começar a 3 m (nas Propriedades, **Deslocamento da base** `3`).
6. Clique no botão **Modelo analítico e verificação…** (o pórtico laranja e azul com o visto verde).
7. A janela diz quantos nós, pilares, vigas e apoios tem o modelo, e lista um **Erro — pilar suspenso**. Faça duplo
   clique nele: o pilar fica selecionado.
8. Feche a janela: o modelo analítico fica desenhado por cima (pilares a laranja, vigas a azul, apoios a vermelho).
   **Vista ▸ Modelo analítico** liga-o e desliga-o.
9. Apague o pilar suspenso e clique outra vez no botão: já não há erros.

## 0.164 — Ações e materiais

1. Com o pórtico do teste 0.163 (sem o pilar suspenso), clique no separador **BIM**, no botão **Laje**, e desenhe
   uma laje de 6 × 4 m por cima das vigas.
2. Clique no separador **Estrutura** e no botão **Ações e materiais…** (a laje com as setas vermelhas).
3. Na janela, escolha **Betão: C30/37** e **Sismo afastado (tipo 1): zona 1.3**. A tabela muda logo: a altura do
   piso, a área da laje, G, Q, o peso sísmico, o vento em X e em Y e o sismo tipo 1 e tipo 2. Por baixo vêm o
   período e o corte basal.
4. Experimente **Uso dos pisos: B — escritórios**: o Q sobe.
5. Clique em OK: a barra de baixo diz que as ações ficaram guardadas, e o modelo analítico aparece por cima.
6. Abra outra vez a janela: as escolhas continuam lá (estão guardadas no IFC).

## 0.165 — Analisar a estrutura

1. Com o pórtico e a laje do teste 0.164, clique no botão **Analisar a estrutura…** (a viga com a curva azul).
2. A janela diz quantas barras foram analisadas e que as cargas que entram são as que descem aos apoios (os dois
   números são iguais).
3. Veja a tabela: os pilares primeiro (N negativo: comprimidos), depois as vigas, com o momento de vão, o de apoio,
   a flecha (em mm e L/…) e a combinação que manda.
4. Faça duplo clique numa viga: fica selecionada no modelo.
5. Feche, mude a secção de uma viga (nas Propriedades, o **Tipo**) e clique em **Analisar outra vez** (ou no botão
   outra vez): os números mudam.

## 0.166 — Verificação EC2 e armaduras

1. Faça o pórtico do teste 0.164: os quatro pilares (o botão **Pilar** faz pilares 30×30; confirme na barra de cima,
   em **Tipo**, que está «Pilar de concreto 30×30»), as sapatas, as quatro vigas e a laje.
2. No separador **Estrutura**, clique no botão **Verificação EC2 e armaduras…** (a secção de viga com os varões e o
   visto verde).
3. A janela lista os pilares, as vigas, a laje e as sapatas, cada um com o **Estado** (OK a verde, Atenção a laranja,
   Falha a vermelho), a **Utilização**, a **Armadura** («4 Ø12 · cintas Ø8//0,225», «inf. 2 Ø12 · sup. 2 Ø12 ·
   estribos Ø8//0,25»…) e **O que manda**. Na coluna **No modelo** aparece «—» (ainda não há armaduras).
4. Clique numa viga: em baixo aparecem todas as contas dela (flexão, esforço transverso, deformação, flecha).
5. Clique em **Pôr as armaduras no modelo**: a barra de baixo diz quantos elementos e varões; na coluna **No
   modelo** aparece «estas».
6. Clique em **Lista de armaduras…**: cada posição com o elemento, o Ø, a quantidade, o comprimento, a forma e o
   peso; em baixo os totais por diâmetro. Clique em **Exportar CSV…**, grave, e abra o ficheiro no Excel.
7. Feche as duas janelas. Com nada selecionado, nas **Propriedades** mude o **Estilo visual** para **Raio-X**: vê os
   varões dentro dos pilares, das vigas, da laje e das sapatas.
8. Clique num estribo de uma viga (no raio X): as Propriedades dizem «Armadura de Viga …», a posição, os varões e o
   peso.
9. Selecione uma viga e mude-lhe o **Tipo** para «Viga de concreto 20×50»: os estribos dela refazem-se mais altos. Apague a viga:
   as armaduras dela vão com ela. Ctrl+Z traz tudo de volta.
10. Experimente uma viga fraca: mude o tipo de uma viga para «Viga de concreto 15×30» e abra a verificação outra vez — se
    falhar, a linha fica a vermelho com o que fazer («aumente a secção»), e ao pôr as armaduras essa fica sem elas.

## 0.167 — Quantidades da estrutura e memória de cálculo

1. Com o pórtico e as armaduras do teste 0.166, clique no separador **Estrutura** e no botão **Quantidades da
   estrutura…** (o bloco de betão com as linhas azuis).
2. A tabela mostra cada pilar, viga, laje e sapata com o betão (m³), a cofragem (m²), o aço (kg) e a taxa (kg/m³);
   em baixo, uma linha por tipo (a negrito) e o **Total**. Uma taxa fora do habitual aparece a vermelho.
3. Clique em **Exportar CSV…**, grave e abra no Excel.
4. Feche. Clique no botão **Memória de cálculo…** (a folha com o carimbo vermelho), escolha onde gravar e deixe o tipo
   **PDF**; clique em Gravar.
5. Abra o PDF: as nove secções (projeto, materiais, ações, modelo, análise, verificação EC2 de cada elemento,
   quantidades, armaduras, notas) e, no fim, o quadro a vermelho a dizer que o engenheiro verifica e assina.
6. Para pôr o nome do projeto e do dono de obra na memória: à direita, no separador **Projeto**, clique com o botão
   direito em **Folhas** e escolha **Legenda…**; preencha **Projeto** e **Dono de obra**, OK, e grave a memória outra
   vez.
7. Repita o passo 4 escolhendo o tipo **HTML**: abre no navegador e imprime-se para PDF a partir dele.

## 0.168 — Plantas de estrutura e desenhos de armaduras

1. Com o pórtico e as armaduras do teste 0.166, clique à direita no separador **Projeto**.
2. Em **Vistas** aparecem dois grupos novos: **Plantas de estrutura (1)** e **Armaduras (13)**.
3. Abra **Plantas de estrutura**, clique com o botão direito em **Térreo** e escolha **Pôr na folha ▸ Nova folha**:
   abre a folha com a planta cortada abaixo da laje — os pilares e as vigas a cheio, as sapatas por baixo, a laje a
   tracejado — e as etiquetas «P1 30×30», «V1 20×40», «L1 h = 0,15», «S1 1,20×1,20».
4. Volte ao painel **Projeto**, abra **Armaduras**, clique com o botão direito numa viga e escolha **Pôr na folha ▸
   Nova folha**: abre a folha com o alçado da viga (os varões a traço grosso, um traço por estribo) e o corte A–A
   ampliado, com as legendas «2 Ø12 — pos. … — L = … m».
5. Clique com o botão direito num pilar (em **Armaduras**) e escolha **Pôr na folha ▸** a folha do passo 4: o
   desenho do pilar fica ao lado do da viga, sem tapar as legendas.
6. Mude a secção da viga (nas Propriedades, o **Tipo** para «Viga de concreto 20×50») e volte à folha: o desenho já
   mostra a viga mais alta, com os estribos refeitos.
7. Exporte a folha em PDF (no painel Projeto, botão direito na folha ▸ **Exportar em PDF…**).

## 0.169 — Móveis e lista de corte

1. Num projeto novo, desenhe as quatro paredes de uma sala de 5 × 4 m (separador **BIM**, botão **Parede**) e
   carregue em F4 (planta).
2. Clique no botão **Móvel** (o móvel com a bancada e as duas portas). Na barra de cima: **Módulo: Inferior**,
   **Largura: 60 cm**, **Frentes: Portas**, **Puxador: Barra**.
3. Passe o rato sobre a face de dentro da parede de baixo: aparece o contorno do móvel encostado. Clique.
4. Clique outra vez um pouco ao lado (a menos de 10 cm do lado do primeiro): o segundo fica encostado ao primeiro.
5. Escreva `0,45` (ou `45cm`) e Enter (a largura passa a 45 cm) e ponha um terceiro ao lado.
6. Na barra de cima mude para **Módulo: Superior** e ponha um por cima do primeiro (fica pendurado a 1,45 m).
7. Carregue em Esc, depois em F4 (3D): vê os móveis, os rodapés recuados, as portas e os puxadores.
8. Clique no primeiro móvel: nas **Propriedades**, mude **Frentes** para **Gavetas** e **Gavetas** para 4; mude a
   **Largura** para `0,80`: o móvel cresce para a direita.
9. Clique no botão **Lista de corte…** (a placa com as peças marcadas): a tabela das peças (laterais, bases,
   travessas, costas, prateleiras, rodapés, portas, frentes de gaveta) em mm, as orlas, a área de placa e as
   ferragens. **Exportar CSV…** e abra no Excel.
10. Para a lista só de alguns móveis: selecione-os antes de clicar em **Lista de corte…**.

## 0.170 — Cozinhas e bancada

1. Num projeto novo, desenhe as quatro paredes de uma sala de 5 × 4 m e carregue em F4 (planta).
2. Clique no botão **Cozinha** (as paredes em L com os módulos e a linha azul da bancada).
3. Clique na face de dentro da parede de baixo, perto da esquerda (onde a cozinha começa).
4. Clique no canto de dentro com a parede da direita, e depois mais acima nessa parede (onde acaba). Enquanto o rato
   anda, vê os módulos como vão ficar.
5. Carregue em Enter: a cozinha em L fica feita — inferiores, superiores e a bancada. Carregue em F4 para a ver em 3D.
6. Clique num módulo inferior do fim do primeiro troço e, nas **Propriedades**, mude a **Largura** para `0,40`: a
   bancada encurta com ele.
7. Apague dois módulos inferiores (Delete): a bancada encolhe. Ctrl+Z traz tudo.
8. Para uma bancada sobre módulos postos à mão (com o botão **Móvel**): selecione-os e clique no botão **Bancada**.
9. Na barra de cima da Cozinha experimente **Superiores: Não** e **Frentes: Gavetas** antes do primeiro clique; F
   vira a cozinha para o outro lado da linha.
10. **Lista de corte…**: aparecem também as peças da bancada.

## 0.171 — Eletrodomésticos e gás

1. Faça uma cozinha como no teste 0.170 (ou só um troço reto) e carregue em F4 (planta).
2. Clique no botão **Eletrodoméstico** (a placa com os quatro círculos laranja). Na barra de cima, **Aparelho:
   Placa**.
3. Passe sobre a face da parede atrás da bancada e clique: a placa fica rente ao tampo. Em 3D (F4) a bancada tem o
   recorte por baixo da placa.
4. No botão **Louça sanitária**, escolha **Lava-loiça** e ponha-o mais ao lado, contra a mesma parede: a
   bancada fica com o segundo recorte.
5. Apague a placa (selecione-a e Delete): o recorte desaparece. Ctrl+Z traz a placa e o recorte.
6. Ponha uma **Máquina de lavar loiça**: nas Propriedades vê as ligações (água fria e esgoto). Com o botão **Tubo**,
   comece num ponto de ligação dela: o tubo fica no sistema certo.
7. Ponha uma **Placa a gás**: o tubo começado na sua ligação fica no sistema **Gás** (amarelo).
8. Experimente também o **Frigorífico**, o **Forno**, o **Micro-ondas** e o **Exaustor** (fica pendurado a 1,55 m).

## 0.172 — Divisões e roupeiro

1. Num projeto novo, desenhe uma sala e carregue em F4. Clique no botão **Móvel** e, na barra de cima, escolha
   **Módulo: Roupeiro** (a largura passa a 100 cm).
2. Passe sobre a face de uma parede e clique: o roupeiro fica de 2,40 m de altura, com duas portas.
3. Clique no roupeiro (botão **Selecionar**): nas **Propriedades**, **Compartimentos** está em 2 —
   **Compartimento 1: Varão de cabides**, **Compartimento 2: Prateleiras**.
4. Mude **Compartimentos** para 3 e **Compartimento 2** para **Gavetas interiores**; mude a **Largura** para `1,20`.
5. Veja em 3D com **Estilo visual: Raio-X** (Propriedades da vista, com nada selecionado): as divisórias, o varão, a
   prateleira de chapéus, as gavetas interiores e as prateleiras.
6. **Lista de corte…**: aparecem as divisórias e as frentes das gavetas interiores; nas ferragens, os varões e as
   corrediças.
7. Num móvel inferior de cozinha também pode dividir: 2 compartimentos de prateleiras numa porta dupla.

## 0.173 — Ripado, canelado e painel perfurado

Nas medidas, um número sem unidade é em metros: escreva `0,06` ou `6cm`, e não só `6`.

1. Num projeto novo, no separador **BIM**, desenhe com o botão **Parede** uma sala de 5 × 4 m e, com o botão
   **Porta**, ponha uma porta numa das paredes.
2. Clique no botão **Revestimento de parede**. Na barra de cima, em **Acabamento**, escolha **Ripado**; em **Até à
   altura** escreva `2,60` e carregue em Enter.
3. Passe sobre a face de dentro da parede com a porta e clique: a parede fica com ripas na vertical, cortadas por
   cima da porta.
4. Em **Acabamento**, escolha **Painel perfurado**, clique na face de fora da mesma parede (a da porta) e carregue em
   Esc.
5. Carregue em F4 (3D), rode a vista para ver a sala por fora e aproxime-se: o painel tem furos, recortados à volta
   da porta, e a cada 1,22 m uma faixa sem furos (a junta entre dois painéis).
6. Com o botão **Selecionar**, clique nas ripas. Nas **Propriedades** aparecem **Largura da ripa**, **Intervalo**,
   **Sentido** e **Peças** (quantas ripas).
7. Em **Intervalo** escreva `0,06` e carregue em Enter: ficam menos ripas, mais afastadas.
8. Mude **Sentido** para **Na horizontal**: as ripas deitam-se.
9. Mude **Acabamento** para **Canelado**: ficam meias-canas encostadas. Volte a pôr **Ripado**.
10. Clique no painel perfurado: **Furos** diz quantos são e a área aberta.
11. Em **Passo dos furos** escreva `0,10` e carregue em Enter: ficam menos furos.
12. Clique num sítio vazio da vista, para não ficar nada selecionado, e clique no botão **Lista de corte…**: aparecem
    as ripas (por comprimento) e os painéis perfurados.
13. Clique em **DXF para fabrico…** e grave o ficheiro.
14. Abra o DXF num programa de CAD. Cada painel aparece deitado, com o contorno (o que fica junto à porta,
    recortado), os furos e o nome; por baixo, cada comprimento de ripa com quantas são.
15. Na planta, selecione a parede do painel e puxe-lhe a ponta para a alongar: o painel acompanha, com mais furos.

## 0.174 — Perfil corrido (rodapés, sancas, frisos)

1. Num projeto novo, no separador **BIM**, desenhe com o botão **Parede** uma sala de 5 × 4 m (os quatro lados
   seguidos, a fechar no primeiro ponto) e, com o botão **Porta**, ponha uma porta numa das paredes.
2. Clique no botão **Perfil corrido** (ao lado de **Revestimento de parede**). Na barra de cima: **Por: À volta de
   uma sala** e **Perfil: Rodapé**.
3. Clique dentro da sala: o rodapé corre ao longo das quatro paredes e para nos dois lados da porta.
4. Na barra de cima, mude **Perfil** para **Sanca** e clique outra vez dentro da sala: a sanca fica encostada ao
   topo das paredes, inteira (passa por cima da porta).
5. Carregue em Tab (passa a **Caminho (clicado)**), escolha **Perfil: Friso** e, em **Lado**, **À esquerda do
   caminho**.
6. Clique em três pontos junto à face de dentro de uma parede sem porta, seguindo-a e virando no canto para a
   parede seguinte, e carregue em Enter: fica um friso a 0,90 m do chão, com a esquadria no canto.
7. Carregue em Esc e, com o botão **Selecionar**, clique no friso. Nas **Propriedades**, em **Altura ao chão**,
   escreva `1,00` e carregue em Enter: o friso sobe.
8. Mude **Saliência** para `0,03` e carregue em Enter: o friso fica mais grosso.
9. Carregue em F4 (3D) e entre na sala com a roda do rato, a olhar para um canto: o rodapé, o friso e a sanca com
   os cantos em esquadria.
10. Volte à planta. Selecione a parede de baixo e arraste o quadradinho da ponta direita dela 1 m para a direita:
    a parede da direita vai atrás, a sala cresce, e o rodapé e a sanca acompanham-na.
11. Ponha outra porta na sala: o rodapé passa a parar também nessa porta.
12. Clique num sítio vazio da vista, para não ficar nada selecionado, e clique em **Lista de corte…**: aparecem o
    rodapé, a sanca e o friso, peça a peça, pelo comprimento maior.
13. Clique em **DXF para fabrico…**, grave e abra o ficheiro num programa de CAD: cada peça em planta, com as pontas
    em esquadria e os ângulos (45° nos cantos da sala).

## 0.175 — Superfície ondulada (costelas)

1. Num projeto novo, no separador **BIM**, desenhe com o botão **Parede** uma sala de 5 × 4 m.
2. Clique no botão **Revestimento de parede**. Na barra de cima, em **Acabamento**, escolha **Ondulado
   (costelas)**; em **Até à altura** escreva `2,60` e carregue em Enter.
3. Passe sobre a face de dentro da parede de cima e clique; carregue em Esc.
4. Carregue em F4 (3D) e entre na sala com a roda do rato, a olhar para essa parede: as costelas deitadas, a frente
   de cada uma em onda, e as ondas a fazerem diagonais na parede.
5. Com o botão **Selecionar**, clique no ondulado. Nas **Propriedades**, em **Amplitude da onda**, escreva `0,10` e
   carregue em Enter: as ondas ficam mais fundas.
6. Em **Rotação da onda (por metro)** escreva `0` e carregue em Enter: as ondas ficam direitas, na vertical.
7. Mude **Sentido** para **Na vertical**: as costelas ficam de pé, lado a lado, e a onda corre de baixo para cima.
8. Em **Intervalo** escreva `0` e carregue em Enter: as costelas encostam-se e a superfície fica cheia.
9. Clique num sítio vazio da vista e clique em **Lista de corte…**: aparecem as costelas (MDF).
10. Clique em **DXF para fabrico…**, grave e abra o ficheiro num programa de CAD: o contorno de cada costela, a
    costa direita e a frente em onda, uma por baixo da outra, com o nome.
11. Num perfil corrido (0.174), em **Altura ao chão**, escreva `0` e carregue em Enter: o perfil desce ao chão (antes
    o zero não era aceite).

## 0.176 — Gaussian splat

1. Abra um projeto com uma casa (ou desenhe uma sala com paredes, uma laje, uma porta e uma janela).
2. **Ficheiro ▸ Exportar Gaussian splat (apresentação)…**.
3. Escolha **Média — 5 cm** e clique em **OK**.
4. Grave o ficheiro (por exemplo, `casa - splat.ply`). Na barra de baixo aparece quantos pontos tem.
5. No navegador, abra um visualizador de splats (por exemplo, o SuperSplat) e arraste para lá o ficheiro `.ply`.
6. Rode à volta da casa: as paredes com a cor do material, mais claras do lado do sol (sudoeste), e as janelas
   transparentes.
7. Repita com **Baixa — 8 cm**: o ficheiro fica bem mais leve e os pontos mais espaçados.

## 0.177 — Portas e janelas em paredes curvas

1. Num projeto novo, no separador **BIM**, clique no botão **Parede** e, na barra de cima, em **Forma**, escolha
   **Arco**. Clique no início do arco, depois no fim, 8 m ao lado; mova o rato para curvar, escreva `4` (o raio) e
   carregue em Enter: fica uma meia-circunferência.
2. Clique no botão **Porta**, passe sobre a parede curva pelo lado de fora e clique: a porta fica nesse ponto do
   arco, a atravessar a parede.
3. Clique no botão **Janela** e clique noutro ponto da parede: a janela fica lá. Carregue em Esc.
4. Carregue em F4 (3D): a porta e a janela, direitas, encaixadas na parede curva.
5. Com o botão **Selecionar**, clique na porta. Nas **Propriedades**, **Distância ao início da parede** é medida ao
   longo do arco: escreva `1,50` e carregue em Enter. A porta desliza ao longo da parede.
6. Clique em **Lado** (virar a porta): passa a abrir para o outro lado.
7. Clique na parede curva e, nas **Propriedades**, mude o **Raio** para `5`: a porta e a janela vão com a parede,
   à mesma distância ao longo do arco.
8. Mude a **Abertura** do arco para `20` (graus): é recusado, porque a janela ficaria de fora.

## 0.178 — Revestimentos em camadas

1. Num projeto novo, no separador **BIM**, desenhe com o botão **Parede** uma sala de 5 × 4 m.
2. Clique no botão **Revestimento de parede**. Na barra de cima, em **Acabamento**, escolha **Reboco**; em **Até à
   altura** escreva `2,80` e carregue em Enter. Clique na face de dentro de uma parede.
3. Na barra de cima, mude **Acabamento** para **Azulejo** e **Até à altura** para `2,10`. Clique sobre o reboco que
   acabou de pôr: o azulejo fica por cima do reboco, até 2,10 m.
4. Carregue em Esc e, com o botão **Selecionar**, clique no azulejo. Nas **Propriedades** aparece **Camada: 2.ª,
   sobre: Reboco 1**.
5. Clique no reboco e mude o **Acabamento** para **Pedra natural**: o azulejo sai um pouco, por cima da pedra.
6. Apague a pedra (tecla Delete): o azulejo encosta-se à parede. Ctrl+Z: volta tudo.

## 0.179 — Cobertura de quatro águas numa casa em L

1. Num projeto novo, no separador **BIM**, desenhe com o botão **Parede** uma casa em L: uma cadeia de seis
   paredes que feche no primeiro ponto — por exemplo 8 m para a direita, 4 m para cima, 4 m para a esquerda, 4 m
   para cima, 4 m para a esquerda e de volta ao início.
2. Clique no botão **Cobertura**. Na barra de cima, escolha **Forma: Quatro águas** e **Contorno: Pelas paredes
   (clique dentro)**.
3. Clique dentro da casa: a cobertura cobre o L todo.
4. Carregue em F4 (3D): as duas cumeeiras encontram-se, com um rincão no canto de fora e uma laró no canto de
   dentro.
5. Clique na cobertura e, nas **Propriedades**, mude a **Forma** para **Duas águas**: é recusado, com uma mensagem
   a explicar porquê. A de quatro águas fica.
6. Num projeto novo, desenhe as seis paredes do L soltas: cada uma com o seu clique de início e de fim, com Esc
   entre elas, para não ficarem ligadas. Clique no botão **Laje** e, na barra de cima, escolha **Varinha mágica** e
   **Contorno: até às faces exteriores das paredes**. Clique dentro do L: o contorno da laje é um L limpo, sem um
   degrau no canto de dentro.

## 0.180 — Abóbada e borboleta

1. Num projeto novo, no separador **BIM**, desenhe com o botão **Parede** uma casa de 10 × 6 m.
2. Clique no botão **Cobertura**. Na barra de cima: **Forma: Abóbada**, **Inclinação: 30°**, **Contorno: Pelas
   paredes (clique dentro)**.
3. Clique dentro da casa: fica uma abóbada a nascer das paredes compridas e a correr ao longo da casa.
4. Carregue em F4 (3D) e veja-a de lado: o arco, com o beirado a continuá-lo.
5. Clique na cobertura e, nas **Propriedades**, mude a **Forma** para **Borboleta (calha ao meio)**: as duas águas
   descem até uma calha a meio da casa.
6. Clique numa das paredes curtas (uma empena) e, com Shift, clique também na cobertura, para ficarem as duas
   selecionadas. Na barra de cima, clique em **Ligar o topo (laje / cobertura)**: o topo da parede fica com o bico
   para baixo, por baixo da calha.
7. Volte a pôr **Abóbada**: a empena passa a ter o topo em arco.

## 0.181 — Painéis da fachada de vidro

1. Num projeto novo, no separador **BIM**, clique no botão **Fachada de vidro**. Na barra de cima: **Altura**
   `4,40`, **Montantes a cada** `1,50`, **Travessas a cada** `2,20` (Enter em cada um). Clique em dois pontos a 6 m um
   do outro.
2. Carregue em F4 (3D) e vire a vista para ver a fachada de frente.
3. Clique no botão **Painel de fachada** (ao lado da Fachada de vidro). Na barra de cima, escolha **Painel: Porta
   de vidro**. Passe sobre as células (a célula sob o rato fica realçada) e clique na segunda de baixo: fica uma
   porta até ao chão, com puxadores.
4. Escolha **Painel: Opaco** e clique numa célula de cima: fica um painel opaco (no programa ainda com a cor da
   fachada; num visualizador de IFC, cinzento).
5. Escolha **Painel: Vazio** e clique noutra célula: a célula fica aberta.
6. Escolha **Porta de vidro** e clique numa célula de cima: é recusado (as portas só vão na fila de baixo).
7. Carregue em Esc, clique na fachada e veja nas **Propriedades** a linha **Painéis** (1 × opaco, 1 × porta de
   vidro, 1 × vazio).

## 0.182 — Cabeçalho com as disciplinas e faixa de ferramentas

1. Abra o programa. No topo está a faixa escura: o símbolo, **ArqSynth BIM**, a casa (Início) e as disciplinas
   **Modelagem**, **Arquitetura**, **Estrutura**, **Instalações**, **Terreno**, **Anotar**, **Massa e Estudos**,
   **Visualizar**, **Gerenciar**, **Render** e **Colaborar**. À direita: o nome do projeto e os botões Guardar,
   Desfazer, Refazer, Sincronizar e Ajuda.
2. Clique na casa (Início): por baixo aparecem **Novo**, **Abrir**, **Guardar**, **Guardar como**, as importações e
   as exportações. Clique em **Novo** para ver que funciona.
3. Clique em **Arquitetura**: aparecem Parede, Fachada de vidro, Painel de fachada, Revestimento, Porta, Janela,
   Laje, Escada, Cobertura, o mobiliário… Clique em **Parede** e desenhe uma parede.
4. Carregue em Ctrl+3: passa a **Estrutura** (eixos, pilares, vigas, sapatas, cálculo).
5. Clique em **Anotar** e carregue na tecla W: a ferramenta Parede funciona na mesma.
6. Faça um duplo clique numa disciplina: a faixa de ferramentas esconde-se. Outro duplo clique: volta.
7. Em baixo, no rodapé, estão os botões de navegação (enquadrar tudo, vista anterior, orbitar, deslocar, zoom,
   câmara, caminhar).
8. Feche e volte a abrir o programa: abre na disciplina em que estava.
9. Os menus antigos (Arquivo, Editar…) já não aparecem. Os atalhos continuam: Ctrl+S guarda, Ctrl+Z desfaz, F4 abre
   a planta.

## 0.183 — Barra de parâmetros

1. Em **Arquitetura**, clique em **Parede**. A barra por baixo das ferramentas começa com o ícone e o nome
   **Parede** e mostra Tipo, Forma, Altura, Linha de referência e Pavimento, em campos com rebordo.
2. Clique no campo **Altura**, escreva `abc` e carregue em Enter: o campo fica vermelho um instante, o rodapé diz
   «Medida inválida» e a altura fica a que estava.
3. Escreva `3,20` e carregue em Enter: a altura muda.
4. Clique na roda dentada, à direita dos parâmetros: abre-se a janela dos tipos com o tipo da parede escolhido.
   Feche-a.
5. Clique em **Selecionar** (ou carregue em Espaço): a barra mostra o ícone da seleção e os modos de seleção.

## 0.184 — Barra compacta e Navegador do Projeto

1. Abra o programa. No extremo esquerdo está uma barra estreita só com ícones; passe o rato por cima de cada um
   para ver o nome. Ao lado dela está o **Navegador do Projeto**; à direita, as **Propriedades** com a altura toda.
2. Clique no segundo ícone (**Pavimentos**): aparece o painel dos pavimentos.
3. Clique no ícone **Folhas**: volta o navegador, aberto nas folhas.
4. Clique no primeiro ícone (**Navegador do Projeto**). Na caixa **Pesquisar…** escreva `Norte`: ficam só as Vistas,
   os Alçados e o Norte. Apague o texto: volta tudo.
5. Clique outra vez no ícone do Navegador do Projeto: os painéis da esquerda recolhem-se e o modelo ganha espaço.
   Clique de novo: voltam.
6. Clique no ícone **Ambientes**: em baixo abre-se o quadro das salas.
7. Clique na roda dentada, em baixo na barra (**Configurações**): aparece o menu com o botão do meio do rato e os
   painéis.

## 0.185 — Propriedades

1. Desenhe uma parede e clique nela com o botão **Selecionar**. Nas **Propriedades**, à direita, aparece em cima o
   ícone da parede, o nome («Parede 1») e por baixo o tipo.
2. Por baixo estão os grupos **Identificação**, **Restrições e dimensões**, **Materiais e acabamentos (do tipo)**,
   **Fase** e **Dados IFC e parâmetros**. Clique na seta de um grupo para o recolher, e outra vez para o abrir.
3. Na caixa **Pesquisar propriedades…** escreva `compr`: fica só o **Comprimento**. Apague o texto: volta tudo.
4. Clique no separador **Navegador de Materiais**: aparecem os materiais com a sua cor. Faça um duplo clique num:
   abre-se a janela dos materiais nele. Feche-a e volte ao separador **Propriedades**.
5. Clique num sítio vazio da vista: em cima aparece o nome da vista («3D») e as linhas ficam no grupo **Vista**.

## 0.186 — Rodapé

O rodapé é a barra de baixo da janela. Comece com uma parede desenhada, na vista 3D.

1. Olhe para a direita do rodapé: depois dos botões de navegação aparecem o **cubo** (orientação), um **cubo
   colorido** (estilo gráfico), **1:—** (escala), a **grelha** e **m** (unidades).
2. Clique no cubo colorido e escolha **Linhas escondidas**: o 3D fica a branco com as arestas, e o ícone muda.
   Carregue em Ctrl+Z: volta a **Sombreado**.
3. Clique no botão da grelha: a grelha do chão desaparece. Clique outra vez: volta.
4. Clique no cubo da orientação e escolha **Isométrica nordeste**: a vista passa para o canto de trás, à direita.
   Volte ao cubo e escolha **Trás (norte)**: vê o modelo de frente, pelo lado norte. Por fim escolha **Ir para a
   vista inicial**.
5. Carregue em F4 (planta): o estilo e a grelha ficam apagados. Clique em **Automática** (a escala) e escolha
   **1:50**: o botão passa a dizer «1:50». Se a planta tiver um modelo de vista, a escala fica apagada, porque é o
   modelo que a fixa.
6. Clique em **m** e escolha **Centímetros (cm)**. Selecione a parede: nas Propriedades, o comprimento aparece em
   centímetros (por exemplo «400,0 cm»). As cotas dos pavimentos continuam em metros.
7. Escolha a ferramenta **Parede**, clique no chão, escreva `300` e carregue em Enter: a parede mede 3 m (o número
   sem unidade lê-se em centímetros). Carregue em Esc.
8. Clique em **cm** e escolha **Metros (m)**: tudo volta a metros.
9. Faça um pavimento novo no painel **Pavimentos**. Depois clique no nome do pavimento, no rodapé
   («Pavimento: …»): aparece a lista, com o mais alto em cima e o ativo marcado. Escolha **Térreo**: passa a
   desenhar nele.

## 0.187 — Propriedades de vários elementos

1. Desenhe três paredes soltas (sem se tocarem): duas com 4 m e uma com 5 m. Ponha um pilar ao lado.
2. Clique no botão **Selecionar** e arraste uma caixa à volta de tudo. Nas **Propriedades** aparece em cima
   «4 objetos selecionados», e a lista **Elementos** com **Todos (4)**, **Paredes (3)** e **Pilares (1)**.
3. Com **Todos (4)**, só aparecem as propriedades que todos têm, como a **Fase**.
4. Na lista **Elementos**, escolha **Paredes (3)**. A **Altura** mostra 2,80 m (é igual nas três); o
   **Comprimento** está em branco, com «<vários>», porque difere.
5. Clique na Altura, escreva `3,20` e carregue em Enter: as três paredes sobem juntas.
6. Carregue em Ctrl+Z: as três voltam a 2,80 m de uma vez. O Ctrl+Z tira a seleção: selecione tudo outra vez
   com a caixa e escolha **Paredes (3)** na lista.
7. Clique no Comprimento («<vários>»), escreva `6` e carregue em Enter: as três ficam com 6 m.
8. Na **Fase**, escolha **Existente**: as três passam a existentes; o pilar não.
9. Na lista **Elementos**, escolha **Pilares (1)**: aparecem as propriedades do pilar, como se estivesse sozinho.

## 0.188 — Fachada de vidro embutida numa parede

1. Desenhe uma parede reta de 8 m com a ferramenta **Parede**. Carregue em Esc.
2. Carregue em F2 (vista de topo) e aproxime-se da parede, para a ver larga no ecrã.
3. Escolha a ferramenta **Fachada de vidro** (separador Arquitetura).
4. Clique no meio da espessura da parede, a 2 m do início (longe das arestas, para o clique não ir para o topo).
5. Mova o rato ao longo da parede: a dica em baixo diz «fica embutida em "Parede 1"».
6. Escreva `3` e carregue em Enter: a fachada fica feita e a parede ganha o vão dela. Carregue em Esc.
7. Rode a vista (F8): a parede está aberta onde está a fachada.
8. Clique na fachada com o **Selecionar**. Nas Propriedades:
   - **Embutida na parede** está marcada;
   - aparece **Parede: Parede 1** e as distâncias ao início e ao fim da parede.
9. Na distância ao início escreva `1` e carregue em Enter: a fachada desliza para 1 m do início, com o seu vão.
10. Com a fachada selecionada, use o **Mover** ao longo da parede: ela desliza, sem sair da parede.
11. Desmarque **Embutida na parede**: a parede fica inteira e a fachada fica onde estava. Carregue em Ctrl+Z: volta
    a estar embutida.
12. Selecione a parede e mova-a: a fachada vai com ela.

## 0.189 — Cantos com paredes curvas

1. Carregue em F2 (vista de topo).
2. Escolha a ferramenta **Parede** e, na barra contextual, a forma **Arco**.
3. Clique num ponto do chão (o início do arco), depois noutro ponto 6 m ao lado (o fim) e por fim um ponto 2 m
   para cima, a meio: fica uma parede curva.
4. Na barra contextual, volte à forma **Linha**.
5. Clique num ponto 4 m abaixo do fim do arco e depois exatamente na ponta do arco (o rato agarra-se ao meio da
   ponta da parede). Carregue em Esc.
6. A barra de baixo diz que a parede ficou ligada. Aproxime-se do canto (F4, planta): as duas paredes encontram-se
   sem folga nem sobreposição, cortadas pela mesma linha.
7. Selecione a parede reta e mude o tipo para **Parede alvenaria 15 cm**: o canto refaz-se, ainda fechado.
8. Experimente também ao contrário: desenhe uma parede reta; depois, com o **Arco**, clique primeiro na ponta da
   parede reta (o rato agarra-se ao meio da ponta), depois no fim do arco, e dê a curvatura: o arco fica no chão e
   junta-se sozinho à parede.

## 0.190 — Coberturas de quatro águas sobre qualquer contorno

1. Carregue em F2 (vista de topo). Escolha a ferramenta **Parede** (forma Linha).
2. Desenhe uma casa em L com lados em viés, clicando à vista seis cantos e voltando ao primeiro para fechar — por
   exemplo, em metros: (0, 0), (10, 0), (10, 4), (5, 5), (3, 10), (0, 9). Não precisa de precisão: o que importa é
   haver lados oblíquos e um canto para dentro. Carregue em Esc.
3. Escolha a ferramenta **Cobertura** e, na barra contextual, **Quatro águas**.
4. Clique dentro da casa: aparece a cobertura, com uma água por cada lado da casa.
5. Rode a vista (F8): os rincões saem dos cantos, o laró sai do canto para dentro, e as cumeeiras correm ao longo
   das alas. Não há buracos nem degraus entre as águas.
6. Com a cobertura selecionada, mude nas Propriedades a forma para **Duas águas**: aparece o aviso de que sobre um
   contorno com cantos para dentro só se faz de quatro águas ou plana.

## 0.191 — Editar os desenhos 2D

1. Abra a planta do pavimento (F4). Escolha a ferramenta **Desenho 2D** (separador Anotar), forma **Linha**, e
   desenhe uma linha com dois cliques. Na forma **Texto**, clique noutro sítio, escreva `Nota` e carregue em Enter.
2. Escolha **Selecionar** e clique na linha: aparecem duas pegas azuis, uma em cada ponta.
3. Arraste uma das pegas para outro sítio: a ponta vai com ela. Carregue em Ctrl+Z: volta ao que era.
4. Com a linha selecionada, veja as **Propriedades**: escreva `3` no **Comprimento** e carregue em Enter. A linha
   passa a ter 3 m, a partir do seu início. Mude também o **Tipo de linha** para tracejado.
5. Clique no texto. Nas Propriedades, mude o **Texto** para `Sala comum` e o **Ângulo** para `45`: o texto fica
   rodado, no ecrã e no papel.
6. Selecione a linha, escolha **Rodar**, clique num ponto (o centro), depois noutro (a direção de partida),
   escreva `90` e carregue em Enter: a linha roda 90°.
7. Para ver no papel: imprima a planta em PDF (ou ponha-a numa folha). O texto sai rodado.

## 0.192 — Marcas de nível nas plantas

1. Desenhe uma laje (ferramenta **Laje**) e, nas Propriedades, ponha-a um pouco acima do pavimento (ou desenhe-a
   já a +0,30).
2. Abra a planta (F4). Escolha **Desenho 2D** e, na barra contextual, a forma **Marca de nível**.
3. Clique em cima da laje: aparece o círculo com dois quartos pretos e, ao lado, a cota da laje (por exemplo
   «+0,30»).
4. Clique fora da laje: a marca escreve a cota do pavimento («±0,00»).
5. Na vista 3D, suba a laje com o **Mover**: clique nela, leve o rato para cima, ao longo do eixo azul, escreva
   `0,3` e carregue em Enter. Volte à planta: a primeira marca mudou sozinha.
6. Imprima a planta em PDF: as marcas saem com os quartos pretos.

## 0.193 — Tipos de cota

1. Abra uma planta com paredes (F4).
2. Clique em **Anotar ▸ Estilo das cotas…**. Em **Novo tipo** escreva `Pormenor` e clique em **Juntar**: a lista
   **Tipo** passa a mostrar «Pormenor».
3. Com «Pormenor» escolhido, mude a **Unidade** para centímetros e a **Marca** para setas. Clique em OK.
4. Escolha a ferramenta **Cota**. Na barra contextual, em **Tipo de cota**, escolha «Pormenor».
5. Desenhe uma cota ao longo de uma parede (dois pontos e o sítio da linha): o valor sai em centímetros
   (por exemplo «400»), com setas.
6. Com **Selecionar**, clique na cota: as Propriedades mostram o valor e o **Tipo de cota** «Pormenor». Mude-o para
   **Estilo do projeto**: a cota passa a «4,00». Carregue em Ctrl+Z: volta a «Pormenor».
7. Selecione várias cotas (Shift + clique) e mude-lhes o tipo de uma vez.

## 0.194 — Notas-chave

1. Desenhe duas paredes do mesmo tipo (por exemplo «Parede alvenaria 20 cm»).
2. Selecione uma delas. Nas Propriedades, no grupo **Dados IFC e parâmetros**, em **Nota-chave (do tipo)**,
   escolha «02.03 — Alvenaria de tijolo cerâmico 20 cm».
3. Selecione a outra parede: tem a mesma nota-chave, porque a nota é do tipo.
4. Abra a planta (F4). Escolha **Desenho 2D**, forma **Nota-chave**. Clique numa parede e depois ao lado: aparece
   a etiqueta, uma linha com uma caixa que diz «02.03».
5. Selecione a parede e mude a nota para «02.04»: a etiqueta muda sozinha.
6. Carregue em Ctrl+T (Tabelas) e escolha **Notas-chave**: aparece «02.04», a descrição e «2» (as duas paredes).
   Esta tabela pode ir para uma folha (botão **Pôr numa folha**).
7. Imprima a planta em PDF: a etiqueta sai com a caixa e o código.

## 0.195 — Ramais a outra altura descem até ao tubo

1. Abra a planta (F4). Escolha a ferramenta **Tubo**, forma **Ramal (ponto a ponto)**, tipo Ø100, inclinação 0,
   e em **Eixo a** escreva `0,5`.
2. Desenhe um tubo de um lado ao outro da planta (dois cliques) e carregue em Esc.
3. Mude o tipo para Ø50 e o **Eixo a** para `2,5`.
4. Clique num ponto afastado do primeiro tubo e leve o rato até cima dele: a dica diz «Desce 2,00 m até este tubo
   e liga-se com um tê». Clique.
5. Rode a vista (F8): o ramal fica a 2,50 m até por cima do tubo, desce na vertical com uma curva no topo e liga-se
   com um tê virado para cima.
6. Carregue em Ctrl+Z: desaparece tudo de uma vez (o troço, a descida, a curva e o tê).

## 0.196 — Tubagem de refrigerante

1. Abra a planta (F4). Escolha a ferramenta **Equipamento AVAC**, tipo **Unidade interior mural (split)**, e
   clique junto de uma parede. Depois o tipo **Unidade exterior** e clique noutro sítio.
2. Escolha a ferramenta **Tubo**, forma **Ramal (ponto a ponto)**, tipo «Tubo de cobre 1/4" isolado», inclinação 0
   e sistema **Refrigerante — líquido**.
3. Clique no split: o tubo sai da porta de líquido.
4. Clique junto da unidade exterior: o tubo acaba na porta de líquido dela e fica ligado.
5. Faça o mesmo com o tipo 3/8" e o sistema **Refrigerante — gás**: liga as duas portas de gás.
6. Selecione um dos tubos: nas Propriedades, o sistema é o do refrigerante e o material o cobre.

## 0.412 — Rodar à volta de X, Y ou Z; planos de trabalho

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.412.0**. Num projeto novo, abra a vista **3D**.
2. Separador **Modelagem**, **Curva de Bézier**: desenhe uma curva no chão, ao longo do eixo verde, e carregue em
   **Enter**.
3. Carregue em **Espaço** (Selecionar) e clique na curva. Carregue em **Q** (Rodar) e clique na ponta da curva (o
   pivô).
4. Carregue em **X**: aparece uma linha vermelha (o eixo X) pelo pivô, e o balão diz «Rodar à volta do eixo X».
5. Clique num ponto da curva (a direção de partida), escreva **90** e carregue em **Enter**: a curva fica de pé.
6. Experimente os botões **X / Y / Z** na barra de cima do Rodar: fazem o mesmo que as teclas.
7. Clique em **Desenhar ▸ Plano de trabalho**. Na barra de cima está **XZ (vertical)** aceso. Leve o rato pelo chão:
   vê-se um quadrado onde o plano ficaria. Clique: aparece uma grelha azul de pé.
8. Carregue em **L** (Linha) e clique em dois pontos «no ar», em frente à grelha: a linha fica no plano. Faça o mesmo
   com a **Curva de Bézier**.
9. Abra a planta (F4): lá a grelha não aparece e desenha-se no piso, como sempre. Volte à vista 3D.
10. Faça uma parede. **Plano de trabalho ▸ Face** e clique numa face da parede: o plano passa a ser o dessa face.
11. **Plano de trabalho ▸ Voltar ao nível do piso**: a grelha desaparece e desenha-se outra vez no chão.
12. Escolha a parede, **Q**, clique num canto, carregue em **X**, clique noutro ponto e escreva 90: o programa recusa
    («só rodam à volta da vertical») e a parede fica de pé.
13. O **Offset** está agora no painel **Modificar**, por baixo de «Dividir com folga» (a tecla F continua a mesma).

## 0.411 — Curva de Bézier como no Blender

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.411.0**. Abra a planta (F4) de um projeto novo.
2. Clique no separador **Modelagem** e, no painel de desenho, em **Curva de Bézier** (o botão pequeno junto de
   «Linha livre»).
3. Clique em quatro pontos em zigue-zague e carregue em **Enter**: a curva passa, **suave**, por todos os pontos (já
   enquanto desenha, a curva segue o rato).
4. Clique em **Curva de Bézier** outra vez, clique em dois pontos e carregue em **Enter**: uma curva reta.
5. Carregue em **Espaço** (Selecionar) e clique nessa curva reta: aparecem os nós (quadrados) e um **«+» no meio**.
6. Carregue sem largar no **«+»**, leve o rato para o lado e largue: nasce um nó ali e a linha **curva-se**, suave.
7. Arraste esse nó novo para outro sítio: a curva segue-o e continua suave.
8. Arraste uma das tangentes (os losangos nas pontas das linhas cinzentas): esse nó passa a «à mão».
9. Na ferramenta Curva de Bézier, **Alt + clique** num ponto: aí fica um canto (bico).

## 0.410 — Contorno do piso como o perfil da parede; furos desenhados

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.410.0**. Abra a planta (F4) de um projeto
   novo.
2. Desenhe uma laje: **Arquitetura ▸ Pisos e coberturas ▸ Laje**, dois cliques em cantos opostos (por exemplo um
   retângulo de 6 × 4 m). Carregue em **Esc**.
3. Carregue em **Espaço** (Selecionar) e dê **dois cliques** na laje: aparecem quadrados nos cantos e losangos no
   meio dos lados; o balão diz Shift, Alt e «Furo». Na barra de cima aparece «Contorno — Furo: Polígono, Retângulo,
   Círculo».
4. Carregue sem largar no **losango do lado direito**, carregue também em **Shift** e leve o rato 1 m para fora;
   largue: o lado fica um **arco**.
5. Faça o mesmo no **losango de cima**, mas com **Alt**: o lado fica uma **curva**, com duas linhas de tangente.
6. Com **Alt** carregado, clique no **canto de baixo à esquerda**, escreva **0,5** e carregue em **Enter**: o canto
   fica arredondado (concordância de 0,50 m).
7. Na barra de cima, clique em **Retângulo** (fica aceso). Clique em dois pontos dentro da laje: aparece um **furo**
   retangular, com as suas pegas.
8. Clique em **Polígono** e clique em três pontos dentro da laje; clique outra vez no primeiro: fecha-se um furo
   triangular.
9. Clique em **Círculo**, clique num ponto dentro da laje, escreva **0,4** e **Enter**: um furo redondo de 0,40 m de
   raio.
10. Carregue em **Esc**: o botão apaga-se (continua a editar a laje).
11. Carregue dentro do furo retangular, arraste-o e largue noutro sítio: o furo muda de sítio.
12. Clique dentro do furo triangular (fica laranja) e carregue em **Delete**: o furo desaparece. **Ctrl+Z** volta a
    pô-lo.
13. Arraste o losango do meio de um lado de um furo com **Shift**: esse lado do furo fica em arco.
14. Carregue em **Esc**: volta ao Selecionar. Rode a vista (3D): a laje tem os furos e o lado em arco.
15. Faça um **Piso** (Arquitetura ▸ Acabamentos ▸ Piso) e dê dois cliques nele: edita-se da mesma maneira.
16. Dê dois cliques numa **parede** (perfil da parede). Na barra de cima clique em **Retângulo** e em dois pontos na
    parede: um furo que a atravessa. Experimente pôr uma janela por cima do furo: é recusada.

## 0.409 — Snaps da porta e da janela; cotas interiores com esquinas e com as duas paredes

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.409.0**. Abra a planta (F4) da casa com o
   compartimento em L e o da parede inclinada.
2. Carregue em **D** (Porta). Passe o rato **por dentro** de um compartimento, sobre uma parede, perto de uma esquina:
   ao chegar perto, a porta **prende** com a ombreira a **0,10** da parede ao lado (a cota temporária diz «0,10 m» e
   ao lado aparece «Ombreira a 0,10 m da gola»). Afaste um pouco: prende a **0,20**.
3. Leve o rato para o meio desse compartimento, na mesma parede: prende ao **Meio do compartimento** (as duas cotas
   temporárias ficam iguais). Clique.
4. Carregue em **J** (Janela) e faça o mesmo: prende igual.
5. Clique em **Anotar ▸ Cotas interiores** e clique na ala de baixo do **L**: a cota horizontal tem um ponto na
   esquina de dentro do L (por exemplo 4,00 + 3,80), e a vertical da outra ala também.
6. No compartimento com a **parede inclinada**, passe o rato perto da esquina da parede de cima com a inclinada: uma
   linha azul atravessa o compartimento paralela à parede de cima, até à inclinada, e a outra corre **ao longo da
   inclinada**. Clique: ficam as duas cotas.
7. Num compartimento direito, as cotas continuam em esquadria, como antes.

## 0.408 — Cotas interiores: alinham-se com a parede mais perto; Ctrl+clique acrescenta

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.408.0**. Abra a planta onde tem o compartimento em
   L com a parede de baixo inclinada (F4).
2. Clique em **Anotar ▸ Cotas interiores**. Na barra de cima, **Cotar: Largura e profundidade**, **Compartimentos: O
   do clique**.
3. Passe o rato dentro do L **perto da parede de cima** (direita): as duas linhas azuis ficam direitas — a horizontal
   paralela à parede de cima e a vertical em esquadria com ela.
4. Leve o rato **perto da parede inclinada de baixo**: as linhas azuis rodam e passam a seguir a parede inclinada.
   Perto da parede da esquerda voltam a ficar direitas.
5. Perto da parede de cima, clique: ficam duas cotas direitas.
6. Mantenha **Ctrl** carregado e clique na outra ala do L, perto da parede de baixo: ficam mais duas cotas (inclinadas,
   como essa parede) e as primeiras continuam lá.
7. Clique outra vez **sem Ctrl**: as quatro dão lugar só às duas do novo clique. **Ctrl+Z** volta atrás.

## 0.407 — Ortogonalizar: a porta e a janela endireitam-se com a parede

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.407.0**. Crie um projeto novo e abra a planta (F4).
2. Carregue em **W** (Parede). Clique num ponto do chão, leve o rato uns 8 m para a direita e **um pouco para cima**
   (uns 30 cm, de modo que a linha não fique vermelha) e clique. Carregue em **Esc**: a parede fica ligeiramente
   inclinada.
3. Carregue em **D** (Porta) e clique sobre a parede, perto do princípio. Carregue em **J** (Janela) e clique sobre a
   parede, perto do fim. Carregue em **Esc**.
4. Carregue em **Espaço** e clique na parede. Na barra por cima da vista clique em **Ortogonalizar**.
5. A parede fica direita **e a porta e a janela também**: a janela fica alinhada com as faces da parede e o aro da
   porta não sai da parede (antes a janela ficava torta e o aro saía para fora).
6. Carregue em **F8** (3D) e veja o mesmo. Carregue em **Ctrl+Z**: volta tudo inclinado, porta e janela incluídas.

## 0.406 — Tutoriais na própria página inicial

1. Feche o ArqSynth BIM e abra-o outra vez (o título diz **0.407.0**, que já inclui a 0.406). Clique na **casa**, a
   primeira aba: a página inicial.
2. Na coluna **Tutoriais**, clique em **Primeiros passos: uma casa**. As colunas **Discussões no GitHub** e
   **Apoiadores** dão lugar ao tutorial, ali mesmo; as outras colunas não encolhem. O tutorial escolhido fica marcado
   na lista.
3. Clique em **▸ Mostrar onde está** debaixo de um passo (por exemplo o 3, Porta): a fita passa para o separador certo
   e o botão acende uns segundos.
4. Clique em **Perfil da parede: canto, arco e curva**: o texto muda para esse tutorial, no mesmo sítio.
5. Em **Procurar neste tutorial…** escreva `concordancia` (sem acento): as palavras ficam realçadas e à direita
   aparece **1 de 2**. Carregue em **Enter**: vai para a segunda. **Shift+Enter** volta à primeira (ou use ▲ ▼).
6. Carregue em **Esc** (limpa a palavra) e outra vez **Esc** (ou clique no **×**): o tutorial fecha e **voltam as
   Discussões e os Apoiadores**.
7. Clique em **▶ Vídeos no YouTube**: abre no navegador o canal **youtube.com/@arqsynth_a**.

## 0.405 — Cotas: arrastar com alinhamentos; tipo e ajustes nas Propriedades

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.405.0**. Use uma planta com cotas (por exemplo, a
   casa do teste 0.399 com as **Cotas exteriores**).
2. Carregue em **Espaço** e clique numa cota: a cadeia fica azul. No painel **Propriedades**, em cima, está a lista
   **Estilo do projeto** (o tipo); por baixo **Tipo ▸ Editar tipo…**, **Cota** (o total da cadeia, IG) e **Texto**
   (prefixo, sufixo, texto por cima e por baixo).
3. Arraste **um número** (carregue nele e arraste) e largue-o: fica exatamente onde o largou.
4. Arraste outro número da mesma cadeia até perto da altura do primeiro: aparece uma linha-guia cor-de-rosa e ele
   alinha-se com o primeiro. Largue.
5. Arraste **a linha** da cadeia para perto de outra cadeia paralela: encaixa na mesma linha (ou à distância habitual
   entre filas).
6. Nas Propriedades, escreva `≈` em **Prefixo** e Enter: todas as cotas da cadeia ficam com «≈».
7. Clique em **Editar tipo…**: abre os Tipos de cota já no tipo dessa cota.
8. Clique em **Repor os valores no sítio**: os números voltam ao lugar.

## 0.404 — Portas e janelas: o lado certo, a prévia e as cotas na planta

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.404.0**. Faça uma sala com **Arquitetura ▸
   Retangular** (clique no chão, `5;4`, Enter) e abra a planta (F4).
2. Carregue em **D** (Porta). Passe o rato **por dentro** da sala sobre a parede de baixo: a porta abre para dentro
   (arco a azul) e aparecem **duas cotas**, das ombreiras até às paredes de cada lado.
3. Clique: a porta fica **a abrir para dentro**, como mostrava. Passe agora o rato **por fora** de outra parede e
   clique: essa abre para fora.
4. Carregue em **J** (Janela) e passe o rato sobre outra parede: vê a janela desenhada através da parede (caixilho e
   vidro) e as duas cotas. Clique para a pôr.
5. Carregue em **Espaço** (Selecionar) e clique numa porta: as setas estão **dentro da porta** — a «↔» no vão e a
   «↕» no arco. Clique **numa ponta** da «↕» (não precisa de acertar na bolinha): a porta passa a abrir para o outro
   lado. Clique na «↔»: as dobradiças passam para o outro aro.
6. No 3D (F8) faça o mesmo com uma porta: abre para o lado de onde está o rato.

## 0.403 — A página inicial na primeira aba, com a casa

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.403.0**. A primeira aba por cima da vista é uma
   **casa**, sem nome nem «×»; a seguir vem **3D**. Passe o rato na casa: aparece «Início».
2. Clique em **3D**: vê o modelo. Clique na **casa**: volta a página inicial.
3. Abra a planta (F4): a aba da planta fica depois da 3D.
4. Tente arrastar a casa para a direita: não se mexe. Arraste a aba da planta para a esquerda de tudo e largue: ela
   volta para depois da casa.
5. Com a casa escolhida, carregue em **Ctrl+W**: nada fecha. Botão direito na aba 3D ▸ **Fechar as outras**: fecha a
   planta, a casa fica.
6. **Ctrl+Tab** passa de vista em vista (3D, planta…) sem parar na casa.
7. Mude o tema (Visualizar ▸ Tema ▸ Claro / Escuro): a casa muda de cor com ele.

## 0.402 — Editar as cotas como no Revit

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.402.0**. Use a planta do teste da 0.401 (as duas
   paredes) e acrescente uma terceira parede paralela a 3 m da segunda (W, clique em 0;7 e em 6;7, Esc).
2. Carregue em **C**; em **Nas paredes** escolha **Eixos das paredes**; clique no eixo das três paredes e depois num
   sítio vazio à esquerda: uma cadeia 4,00 | 3,00. Carregue em **Espaço** (Selecionar).
3. Clique numa das duas cotas: ficam azuis **as duas** (a cadeia), com quadrados nas linhas de chamada e losangos na
   linha e nos valores.
4. Arraste o losango da linha para a esquerda: a cadeia afasta-se das paredes.
5. Arraste o losango de um valor: o número muda de sítio (longe, com uma linha a ligá-lo). Botão direito ▸ **Repor os
   valores no sítio**.
6. Botão direito ▸ **IG — igualar**: a parede do meio move-se para ficar a 3,50 e 3,50; as cotas escrevem «IG».
   **Ctrl+Z**: volta tudo.
7. Botão direito **em cima do quadrado do meio** ▸ **Apagar linha de chamada**: fica uma cota só, 7,00. Ctrl+Z.
8. Faça **duplo clique** no valor 3,00: abre o «Texto da cota». Mude o **Valor** para `3,5` (em «Ao mudar o valor,
   move», a terceira parede) e OK: a parede move-se e a cota fica 3,50.
9. Outra vez duplo clique: marque **Substituir pelo texto:** e escreva `VAR`, em **Por baixo** escreva `osso` e OK.
10. Escolha a parede do meio (clique nela) e depois clique no número de uma cota presa a ela: aparece a caixa «Novo
    valor»; escreva `4,2` e Enter: a parede move-se.

## 0.401 — A Cota manual como no Revit

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.401.0**. Faça **Ficheiro ▸ Novo** (Ctrl+N).
2. Faça duas paredes paralelas, a 4 m uma da outra: ferramenta **Parede** (W), clique em 0;0 e em 6;0, Esc; outra
   vez W, clique em 0;4 e em 6;4, Esc. Ponha uma porta na primeira.
3. Abra a planta (F4) e carregue em **C** (Cota).
4. Passe o rato devagar sobre a face de dentro da primeira parede: a face acende-se a **laranja** e ao lado aparece
   «Face de acabamento   (Tab)». Carregue em **Tab**: passa a «Face do núcleo»; outra vez: «Eixo da parede». Volte a
   «Face de acabamento» com mais Tabs.
5. Clique: a face fica a azul. Passe à face de dentro da outra parede e clique.
6. Leve o rato para o lado, para um sítio vazio: a cota acompanha o rato. Clique: fica **3,80** de face a face.
7. Na barra, em **Nas paredes**, escolha **Eixos das paredes**. Clique perto do eixo da primeira parede, perto do eixo
   da segunda e num sítio vazio: **4,00** de eixo a eixo.
8. Em **Escolher**, escolha **Paredes inteiras** e clique na primeira parede (do lado de fora); depois num sítio vazio
   abaixo dela: a cadeia vai de ponta a ponta com as ombreiras da porta (por exemplo 3,50 | 0,80 | 1,70).
9. Volte a **Referências individuais**. Clique em três ou quatro faces paralelas seguidas e só depois no vazio: uma
   cadeia com várias cotas na mesma linha.
10. Clique num canto, noutro canto e ao lado: como antes, a cota de ponto a ponto.
11. Saia (Esc, Espaço). Escolha a segunda parede e, nas Propriedades, mude o tipo para **Parede de betão armado 25
    cm**: a cota de 3,80 passa a **3,78** (continua na face).

## 0.400 — Cotas interiores num clique

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.400.0**. Use a casa em L do teste da 0.399 (com
   a parede interior), sem fazer Ambientes.
2. Separador **Anotar**, botão **Cotas interiores**: abre-se a planta.
3. Passe o rato dentro de um compartimento: ele acende-se a azul com a largura e a profundidade.
4. Clique: ficam as duas cotas, de face a face, a passar pelo ponto do clique. Clique noutro ponto do mesmo
   compartimento: as cotas mudam para lá (não ficam a dobrar).
5. Na barra contextual, em **Cotar**, escolha **Corrida (através do edifício)** e clique num compartimento: a linha
   atravessa a casa inteira — 0,20 | compartimento | parede | compartimento | 0,20 — nas duas direções (em
   **Direção** pode escolher só uma).
6. Em **Cotar**, escolha **Ao longo das paredes, com os vãos** e clique no outro compartimento: cada parede dele fica
   cotada por dentro, com a porta ou a janela e a parede que lhe chega.
7. Em **Nas paredes**, escolha **Eixos das paredes** e repita o passo 5: a corrida passa a ir de eixo a eixo.
8. Volte a **Largura e profundidade**, em **Compartimentos** escolha **Todos os do pavimento** e clique na planta:
   todos os compartimentos ficam com as suas duas cotas.
9. **Ctrl+Z** desfaz cada clique.

## 0.399 — Cotas exteriores num clique

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.399.0**. Faça **Ficheiro ▸ Novo** (Ctrl+N).
2. Faça uma casa em L com a ferramenta **Parede** (W): clique nos pontos 0;0 → 10;0 → 10;5 → 6;5 → 6;8 → 0;8 e
   feche no primeiro (ou escreva as medidas). Ponha uma parede interior de lado a lado e uma porta e uma janela
   numa parede exterior.
3. Separador **Anotar**, botão **Cotas exteriores**: abre-se a planta; ao mexer o rato aparecem, a azul, as cotas
   que vão ficar à volta da casa.
4. Clique em qualquer sítio da planta: ficam as filas em todas as fachadas — de dentro para fora, os vãos, as
   paredes interiores que chegam à fachada, os cantos (o recuo do L) e o total. O balão diz quantas.
5. Na barra contextual, em **Nas paredes**, escolha **Eixos das paredes** e clique outra vez na planta: as cotas
   refazem-se de eixo a eixo (o total da fachada sul passa de 10,20 para 10,00). Experimente **Faces do núcleo (em
   osso)**: as medidas sem os rebocos.
6. **Ctrl+Z**: volta às anteriores.
7. Em **Fachadas** escolha **A mais perto do rato**: só a fachada perto do rato fica a azul; mude **Vãos** para
   **Eixos dos vãos** e clique perto da fachada da porta: só essa fachada é refeita, com os vãos pelos eixos.
8. Tire a marca de **Paredes interiores** ou de **Cantos** e clique: essas filas desaparecem.
9. Saia com **Esc**. Escolha a parede interior e, nas Propriedades, mude-lhe o tipo para uma parede mais grossa: as
   cotas que estavam nas faces dela continuam nas faces (agora mais afastadas).
10. Rode a casa (Selecionar tudo, **Rodar**, 30°) e volte a **Cotas exteriores** e clique: as cotas seguem as
    fachadas inclinadas.

## 0.398 — Tipos de cota (o motor da aparência)

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.398.0**. Faça **Ficheiro ▸ Novo** (Ctrl+N).
2. Separador **Arquitetura**, botão **Retangular** (painel Paredes). Clique num ponto do chão, escreva `8;6` e
   carregue em Enter: ficam quatro paredes.
3. Separador **Anotar**, botão **Cotar fachadas**: abre-se a planta com as cotas à volta. Repare: o texto das cotas
   verticais está deitado ao longo da linha (lê-se da direita), como no papel; as cotas pequenas que não cabem entre
   as linhas de chamada saem para fora.
4. No painel da direita (com nada escolhido, as propriedades da vista), mude **Escala nas folhas** para **1:50**: as
   cotas no ecrã ficam com o tamanho que terão numa folha a 1:50 (como no Revit). Volte a **Automática** se quiser.
5. **Anotar ▸ Tipos de cota…**: abre a janela nova — à esquerda os tipos do projeto («Estilo do projeto»), ao meio
   as propriedades por grupos (Gráficos, Linhas de chamada, Texto, Unidades e valores, Vãos e cotas iguais), à
   direita uma amostra em papel.
6. Em **Começar de:** (em baixo, à esquerda) escolha **Metros com milímetros em expoente**: na amostra, a porta passa a
   «0,82» com um «5» pequeno e subido. Escolha agora **Engenharia — setas cheias**: as marcas passam a setas.
7. No grupo **Texto**, ponha **Posição do texto** em **Na linha (interrompida)** e **Leitura** em **Sempre na
   horizontal**: a amostra mostra o valor no meio da linha, que se interrompe à volta dele. Marque **Negrito**.
8. No grupo **Vãos e cotas iguais**, marque **Altura do vão por baixo da largura**: por baixo de «0,83» aparece
   «2,10».
9. Clique em **OK**: as cotas da planta mudam todas. **Ctrl+Z** volta ao aspeto anterior; **Ctrl+Y** refaz.
10. Abra outra vez **Tipos de cota…**, clique **Duplicar…**, escreva `Pormenor` e OK; mude a **Unidade** para
    **Centímetros** e clique **OK**. Escolha uma cota na planta (clique na linha ou no número): nas Propriedades, em
    **Tipo de cota**, escolha **Pormenor** — essa cota passa a «820».
11. **Início ▸ Exportar ▸ PDF** (ou DXF): as cotas saem no papel exatamente como no ecrã.

## 0.397 — As duas listas de materiais iguais

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.397.0**.
2. No painel da direita, separador **Navegador de Materiais**: em cima há agora a lista das famílias («Todas as
   famílias») e a pesquisa. Os materiais estão por ordem alfabética: «Aço A400 NR», «Aço A500 NR», «Aço branco»… e
   só depois «Água (piscina, lago)», «Alumínio…», «Azulejo cerâmico».
3. **Gerenciar ▸ Materiais…**: a janela mostra a mesma lista, pela mesma ordem.
4. Nas duas, escolha a família **Metais**: as mesmas 18 linhas, iguais. Escreva `cobre` na pesquisa: as mesmas duas.
5. Ferramenta **Pintura** (B): no Navegador, «Sem pintura» é a primeira linha; escolha **Tintas** na lista das
   famílias para ver só as tintas e clique numa: fica marcada e é a do balde.

## 0.396 — Propriedades arrumadas

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.396.0**. Abra um projeto com uma escada e
   paredes (por exemplo `C:\BIM\exemplos\Casa de teste completa.ifc`).
2. Clique numa **escada**. Nas Propriedades, o primeiro grupo é **Restrições e dimensões** (Forma, Viragem, Largura,
   Cobertor, Desnível…); a **Identificação** vem a seguir, depois a **Fase** e no fim os **Dados IFC e parâmetros**.
3. Nenhum nome acaba em «…»: os compridos («2 espelhos + cobertor», «Número de espelhos», «Afastamento da linha de
   piso…») ocupam duas linhas. Ao lado de **Dados IFC** aparece, a cinzento, o conjunto IFC (Pset_StairCommon).
4. Ponha o rato na **linha vertical invisível entre os nomes e os valores** (o cursor muda para ↔) e arraste-a para
   a esquerda: os nomes ficam mais estreitos (em mais linhas) e os valores mais largos. Clique numa **parede**: o
   divisor fica onde o deixou. Feche e abra o programa: continua lá.
5. Clique no triângulo de **Dados IFC e parâmetros** para o fechar. Clique noutra parede: esse grupo já vem fechado.
   Abra-o outra vez: nos elementos seguintes volta a vir aberto.
6. Clique numa porta, numa laje, na superfície paramétrica: a mesma ordem e nada cortado.

## 0.395 — Superfície paramétrica (forma primeiro, construção depois)

A ferramenta está em **Massa e Estudos ▸ Formas livres** (e também em Estrutura ▸ Elementos). A antiga «Cobertura
orgânica» saiu da fita.

**A — Uma cúpula a partir de três anéis (o «Anel de controlo»)**

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.395.0**. Faça **Ficheiro ▸ Novo** (Ctrl+N).
2. Separador **Massa e Estudos ▸ Círculo**: clique no chão para o centro, afaste o rato uns 6 m e clique outra vez.
3. Tecla **Espaço** (Selecionar) e clique na **linha** do círculo: fica azul.
4. **Massa e Estudos ▸ Formas livres ▸ Anel de controlo**: aparece um círculo mais pequeno 1 m acima; os dois ficam
   selecionados. Clique **Anel de controlo** outra vez: um terceiro, 2 m acima.
5. Clique **Superfície paramétrica**: os três círculos ficam a laranja e a superfície aparece logo em pré-visualização
   (azul transparente) a passar por eles. Na barra de cima deixe **Forma: Automática** e escolha **Construção:
   Gridshell**. Carregue **Enter**.
6. Aparece a estrutura de barras pretas com nós, e fica selecionada. Nas **Propriedades**: **Forma: Loft (secções)**,
   **Curvas: 3 (3 ligada(s) ao modelo)**, depois **Modificadores** e **Construção ▸ Gridshell**.
7. Em **Construção ▸ Gridshell ▸ Malha** escolha **Hexagonal**: as barras passam a hexágonos.
8. Em **Modificadores**, na linha **+ Modificador…** escolha **Torcer**: a superfície torce 45° de baixo para cima.
   Clique no valor do **Ângulo (°)**, escreva `90*v` e Enter: torce o dobro.
9. Na linha **+ Construção…** escolha **Painéis**; em **Painéis ▸ Tipo** escolha **Vidro**: vidros entre as barras.
   No fim das Propriedades aparecem as **Peças** (barras, nós, vidros, com metros e m²) e, a laranja, os avisos
   (painéis empenados).
10. Clique no **círculo do meio** (na linha) para o selecionar, ferramenta **Mover** (M), clique num ponto da linha e
    suba o rato a direito até a linha ficar **azul** («No eixo azul»); escreva `1` e Enter: o anel sobe 1 m **e a
    cúpula acompanha**.
11. **Ctrl+Z** uma vez: o anel e a cúpula voltam os dois.
12. Clique na cúpula; em **Uso** escolha **Cobertura**: a **Classe IFC** passa a IfcRoof (era IfcBuildingElementProxy).
13. Clique **Lista de peças (CSV)…**, grave, e abra o ficheiro no Excel: uma linha por peça (barras por comprimento
    ao milímetro) e o resumo por família no fim.

**B — Uma tampa sobre um contorno**

1. **Massa e Estudos ▸ Retângulo**: um retângulo de uns 10 × 8 m no chão, ao lado.
2. **Superfície paramétrica**, **Flecha 2,5** na barra, e clique na **face** do retângulo: em pré-visualização, uma
   cúpula sobre ele (Automática: uma curva fechada faz uma tampa). **Enter**.
3. Nas Propriedades, **Forma ▸ Forma**: experimente **Abóbada**, **Onda**, **Cosseno**; **Flecha** `4` e Enter.
4. **+ Construção…** ▸ **Casca**: fica uma casca de betão de 12 cm. **+ Construção…** ▸ **Pilares**: 4 pilares sob os
   pontos mais baixos do bordo (só aparecem se a superfície estiver acima do chão).

**C — Uma superfície de fórmula, como pala**

1. **Superfície paramétrica**; na barra: **Forma: Fórmula (grelha)**, **Uso: Pala / brise**, **Construção: Ripas /
   brise**.
2. Clique dois cantos opostos no chão (a pré-visualização segue o rato): uma pala ondulada de ripas de madeira.
3. Nas Propriedades, em **Parâmetros**, mude **H** para `2` (fica mais alta) e, em **Forma ▸ Altura z (fórmula)**,
   escreva `H*sin(2*pi*u)*v` e Enter: a onda muda. Uma fórmula errada (ex. `H*foo`) é recusada com a explicação e a
   superfície fica como estava.

**D — Curvas escolhidas uma a uma**

1. Desenhe duas ou três **Curvas de Bézier** ou **Arcos** (Massa e Estudos ▸ Desenhar) e levante-as com **Mover** a
   alturas diferentes.
2. **Superfície paramétrica** sem nada selecionado; passe o rato por cima de uma curva (fica verde: «Clique: juntar
   esta curva») e clique; depois as outras. **Backspace** tira a última; o botão direito recomeça. **Enter** cria.
3. Na barra, **Forma** pode forçar outra: **Revolução** (uma curva de perfil roda à volta de um eixo vertical no seu
   início), **Extrusão** (com a **Altura**), **Varrimento** (a curva mais comprida é o caminho, a outra o perfil),
   **4 bordos** (quatro curvas que se tocam nas pontas).

## 0.394 — A casa de teste completa

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.394.0**.
2. **Abrir arquivo…** e escolha `C:\BIM\exemplos\Casa de teste completa.ifc`. Abre sem mensagem de erro; os móveis
   da cozinha aparecem logo com as cores das frentes.
3. Rode à volta (botão do meio do rato): na frente a fachada de vidro, a rampa, a torre branca com a faixa de vidro
   curva e a porta, o elevador; atrás a fachada pintada de terracota, a varanda nos pilares, a abóbada de vidro do
   terraço; à esquerda o atelier grafite com a cobertura por blocos e o muro em arco com o painel perfurado.
4. **F4** (planta): 4 ambientes no Térreo (sala, cozinha, casa de banho, atelier), a escada em caracol na torre.
   **Page Up**: o Piso 1 com o quarto, o roupeiro e o vazio da escada.
5. No **Navegador do Projeto ▸ Vistas ▸ Cortes ▸ Corte 1** e nos alçados: os dois pisos, as coberturas, o terreno.
6. Abra `C:\BIM\exemplos\Casa de teste completa - folhas.pdf`: 4 folhas A3 (as duas plantas, os alçados, o corte).
7. Clique em qualquer elemento e veja as Propriedades: a parede norte diz a pintura; o painel perfurado, a abóbada,
   a cozinha… cada um com as suas medidas.

## 0.393 — Modelos, Fase 1 (o gestor e o modelo de fábrica)

Ainda sem nada novo dentro do ArqSynth BIM: testa-se com o **`Modelos - verificar.bat`** (pasta `C:\BIM`).

1. Duplo clique em **`Modelos - verificar.bat`**. Abre-se uma janela preta com um menu; em cima diz a pasta dos
   modelos (`C:\Users\…\AppData\Roaming\ArqSynth\templates`) e, da primeira vez, «acabou de ser criada».
2. Escreva `1` e Enter: a lista tem só **★ ArqSynth Padrão (de fábrica)** — o padrão.
3. `2` e Enter: cria o **Exemplo de escritório**. `3` e Enter: abre a pasta no Explorador; abra o ficheiro
   **Exemplo de escritório.astpl** no Bloco de Notas — é texto (JSON): veja `"units"`, `"storeys"`, `"materials"`.
4. De volta à janela preta: `4`, Enter, escolha o número do exemplo: diz «cm com 1 casa decimal; 3 pisos; 93
   materiais; tipos: 6 paredes, 3 lajes…» e «Lido sem nenhum aviso».
5. **Campo errado**: no Bloco de Notas, troque `"decimals": 1` por `"decimals": "dois"`, grave. Na janela: `4` no
   exemplo — avisa «units.decimals faltava ou estava errado: usado o valor de fábrica».
6. **Ficheiro estragado**: apague a última chaveta `}` do ficheiro e grave. `1`: o exemplo aparece **ESTRAGADO** com o
   motivo; o programa não se queixa de mais nada.
7. Ponha a chaveta de volta. `5` e escolha o exemplo: fica ★ padrão. `6`: diz que o padrão é o exemplo.
8. **Padrão apagado à mão**: apague o ficheiro do exemplo no Explorador. `6`: diz «O modelo padrão «Exemplo de
   escritório» já não está na pasta: usado o modelo de fábrica».
9. `7`: o padrão volta a ser o de fábrica. `9`: grava, na pasta `ArqSynth\formato`, o modelo de fábrica completo, o
   esquema (`schema.json`), a descrição (`FORMATO.md`) e um exemplo curto — para ver o formato. `0` sai.
10. **Grelha do chão** (no ArqSynth BIM): botão da paleta no cabeçalho ▸ **Grafite** (ou **Azul · Revit**): as linhas
    da grelha ficam só um pouco mais claras do que o fundo, discretas. Com **Vistas escuras** ligadas, o mesmo. No
    tema claro normal a grelha fica como sempre esteve.

## 0.392 — Pintura nos esboços

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.392.0**. Crie um projeto novo (**Ctrl+N**).
2. **Modelagem ▸ Retângulo** (tecla **R**): desenhe um retângulo no chão; **Push/Pull** (tecla **P**): puxe-o para
   cima — uma caixa.
3. Tecla **B**; no Navegador de Materiais, um clique em **Tinta ocre**. Clique no **topo** da caixa: fica ocre.
4. **Push/Pull** no topo outra vez, mais 50 cm: o topo continua ocre (os lados continuam sem cor).
5. **B** de novo, escolha **Tinta azul-acinzentado** e, com **Ctrl** carregado, clique num **lado**: ficam azuis
   todos os lados e a base (as faces ligadas que não tinham cor); o topo fica ocre.
6. Com **Alt** carregado, clique no topo: o balde passa a ocre. Escolha **Tinta verde-salva** e, com **Shift**,
   clique no topo: todas as faces ocre do modelo (esboços e elementos) passam a verde — um só **Ctrl+Z** desfaz.
7. Grave (**Ctrl+S**), feche e abra o projeto: as cores da caixa continuam.

## 0.391 — Pintura (como o balde do SketchUp)

> Mudado na 0.392: os esboços também se pintam — ver a secção 0.392.

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.391.0**. Crie um projeto novo (**Ctrl+N**) e faça
   quatro paredes à volta de uma sala (**Arquitetura ▸ Retangular**, dois cliques).
2. Clique na área do desenho e carregue na tecla **B**: na barra de cima aparece **Pintura** e, à direita, abre-se o
   **Navegador de Materiais** com **Sem pintura** no topo e as **tintas** a seguir.
3. **Um clique** em **Tinta terracota** na lista. Passe o rato pela face de fora de uma parede: junto ao rato diz
   «Pintar esta face: Tinta terracota». **Clique**: essa face fica terracota (a de dentro não).
4. Na lista, um clique em **Tinta verde-salva**. Com **Ctrl** carregado, clique noutra parede: fica toda verde.
5. Com **Alt** carregado, clique na face terracota: o balde passa a ter **Tinta terracota** (a barra de cima e a
   lista mostram-no).
6. Escolha **Tinta azul-acinzentado** e, com **Shift** carregado, clique na parede verde: todas as faces verdes do
   modelo passam a azul.
7. Escolha **Sem pintura** e clique na face terracota: volta a ser como era. **Ctrl+Z** desfaz cada passo.
8. **Esc**: volta ao Selecionar e o painel volta às Propriedades. Clique numa parede pintada: nas Propriedades,
   **Pintura** diz a tinta e a área.

## 0.390 — Cobertura orgânica

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.390.0**. Crie um projeto novo (**Ctrl+N**).
2. Separador **Arquitetura** ▸ **Pisos e coberturas ▾** ▸ **Cobertura orgânica** (ao lado de Cobertura, com um arco
   em malha).
3. Na barra de cima: **Contorno** = **Retângulo**, **Forma** = **Cúpula**, **Sistema** = **Envidraçada**. Clique num
   canto no chão e depois no canto oposto (uns 10 × 6 m): aparece a cobertura de vidro com as barras, o aro e os
   pilares; o balão diz a área.
4. Na barra, **Contorno** = **Curvo**, **Forma** = **Abóbada**, **Sistema** = **Casca**. Clique 5 ou 6 pontos à volta
   de uma zona livre — a cobertura aparece em volume enquanto desenha — e carregue em **Enter** (ou clique no primeiro
   ponto): fica uma casca de betão curva.
5. **Esc**, depois clique na primeira cobertura: nas **Propriedades** mude **Forma** para **Onda**, **Malha** para
   `1,5` e **Apoios** para **Nos cantos**. Cada mudança refaz a cobertura; **Ctrl+Z** desfaz.
6. Mude **Nível do beirado** para `4`: a cobertura sobe e os pilares crescem.
7. Experimente **Sistema** = **Pérgola curva**: ficam só as costelas de madeira num sentido; mude **Direção da malha**
   para `90` e as costelas rodam.

## 0.389 — Painel perfurado

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.389.0**. Crie um projeto novo (**Ctrl+N**) e faça
   uma parede reta de uns 4 m (**W**, dois cliques, **Esc**). Rode a vista para ver uma das faces da parede.
2. Separador **Arquitetura** ▸ **Acabamentos ▾** ▸ **Painel perfurado** (o botão grande, com duas placas furadas).
3. Passe o rato pela parede: aparece o contorno azul da face inteira, com as juntas das placas.
4. **Arraste** de um ponto da face (mais ou menos a 1 m do canto e a 0,5 m do chão) até outro (a 3 m e a 2 m de
   altura) e largue: fica um painel perfurado só nesse retângulo; o balão diz quantos furos tem e a área aberta.
5. Na barra de cima, em **Furos** escolha **Quadrados** e em **Malha** escolha **A 45°**. Passe para a outra face da
   parede (rode a vista) e **clique** uma vez: o painel cobre a face toda, com losangos.
6. Clique no primeiro painel: fica escolhido (azul) e as **Propriedades** mostram as medidas dele — forma e malha dos
   furos, diâmetro, passo, margem, placas, junta, imagem, início, fim, base.
7. Nas Propriedades, em **Imagem dos furos**, escolha **Escolher imagem…** e abra uma fotografia ou um logótipo: os
   furos ficam maiores onde a imagem é escura e desaparecem onde é branca.
8. Mude o **Passo dos furos** para `0,08`: os furos espaçam-se. **Ctrl+Z** desfaz.
9. **Arquitetura ▸ Mobiliário ▾ ▸ Lista de corte**, botão do DXF: o ficheiro tem cada placa com o contorno e os furos.

## 0.388 — Página inicial: recentes à esquerda, com vistas

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.388.0**. Aparece a página **Início**.
2. As colunas, da esquerda para a direita: **Começar**, **Documentos recentes** (a mais larga), **Tutoriais**,
   **Discussões no GitHub**, **Apoiadores**. Nenhum botão fica cortado.
3. Se a lista de recentes estiver vazia: clique em **Novo projeto**, faça uma parede, grave com **Ctrl+S** com um nome;
   grave outra vez com **Ctrl+Shift+S** com outro nome. Volte com **Início ▸ Página inicial**.
4. No canto de cima dos recentes há três botões. Clique no do meio (**Lista**): cada documento numa linha, com a pasta
   por baixo do nome. Clique no da direita (**Detalhes**): colunas Nome, Pasta, Alterado e Tamanho. Clique no da
   esquerda: as miniaturas grandes voltam.
5. Na caixa de ordem (diz **Mais recentes**), escolha **Nome (A–Z)**: ficam por ordem alfabética.
6. Clique em **Procurar…** e escreva uma parte do nome de um dos projetos: só esse fica; em baixo, à direita, diz
   «1 de 2». Apague o que escreveu.
7. Clique com o **botão direito** num documento: aparece o menu **Abrir**, **Abrir a pasta**, **Tirar da lista (o
   arquivo fica)** e **Limpar a lista toda**. Escolha **Tirar da lista**: sai da página (o arquivo continua no disco).
8. Feche e abra o programa: a vista e a ordem que escolheu continuam.
9. Clique **uma vez** num documento recente: abre.

## 0.387 — A página inicial

> Mudado na 0.388: os recentes passaram para a esquerda, junto de Começar; o **×** de cada linha saiu (agora é o
> botão direito ▸ **Tirar da lista**); os botões chamam-se **Abrir a pasta base** e **♥ Apoiar o ArqSynth** — ver a
> secção 0.388.

1. Feche o ArqSynth BIM e abra-o outra vez: aparece o separador **Início** com a página inicial (o título da janela
   diz **0.387.0**). Os painéis laterais não aparecem enquanto ela estiver à frente.
2. Na coluna **Tutoriais**, clique em **Perfil da parede: canto, arco e curva**: abre-se uma janela com os passos.
   Feche-a.
3. Clique em **Abrir a lista de vídeos** e em **♥ Apoiar o ArqSynth BIM**: o balão diz que ainda não têm endereço.
4. Clique em **Novo projeto**: a página sai, aparece o 3D com os painéis. Faça uma parede e grave-a (**Ctrl+S**) com
   um nome.
5. **Início ▸ Página inicial** (na fita, no painel Ficheiro): o projeto gravado está em **Documentos recentes**, com
   a miniatura da vista. Clique nele: abre.
6. Grave uma cópia desse projeto na pasta **Documentos ▸ ArqSynth BIM ▸ Arquivos base** (o botão **Abrir a pasta dos
   arquivos base** abre-a). Volte à página inicial: o arquivo aparece em **Arquivos base**; clique nele — abre como
   projeto **sem título**; ao gravar pede um nome novo.
7. Num documento recente, clique no **×**: sai da lista (o arquivo continua no disco).

## 0.386 — Blocos no 3D: caixas de cota, alças, «+» e «−»

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.386.0**. Faça os passos 1 a 3 da secção 0.385
   (uma cobertura por blocos e duplo clique nela).
2. As cotas são só caixas com o valor: uma ao longo de cada beirado com água, e uma no meio do bloco (a altura geral).
3. **Arraste** o quadrado de um **canto** para fora e largue: o bloco cresce pelos dois lados desse canto (junto ao
   rato aparece «largura × profundidade»).
4. **Arraste** o quadrado do **meio de um lado**: só esse lado sai ou entra.
5. **Clique** no **«−»** fora de um lado: essa água sai e o lado fica empena; no mesmo sítio aparece um **«+»** —
   clique nele: a água volta.
6. **Clique** na caixa de um beirado, escreva `3,2` e **Enter**: só esse beirado sobe. Clique na caixa do meio,
   escreva `3,5` e **Enter**: o bloco inteiro sobe.
7. **Ctrl+Z** desfaz cada passo; **Esc** sai.

## 0.385 — Os blocos da cobertura no 3D

> Mudado na 0.386: o clique no quadrado já não troca água ⇄ empena (agora são o «−» e o «+» fora dos lados) e o
> «+» que acrescentava um bloco encostado saiu — ver a secção 0.386.

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.385.0**. Crie um projeto novo com **Ctrl+N**.
2. Separador **Arquitetura** ▸ **Cobertura**; na barra, em **Contorno**, escolha **Por blocos**; clique em dois cantos
   no chão (um bloco de uns 10 × 6 m). Carregue em **Esc** e depois em **Espaço**.
3. Faça **duplo clique** na cobertura: abre-se a edição no 3D (sem janela) — o bloco a azul, quadrados no meio dos
   lados, um losango no meio, «+» fora dos lados e as cotas dos beirados.
4. **Clique** no quadrado de um lado: essa água passa a empena (e outra vez: volta a água).
5. **Arraste** o quadrado de um lado para fora e largue: o bloco estica desse lado.
6. **Clique** no «+» de um lado: aparece outro bloco encostado, com os lados que se tocam em empena.
7. **Clique** no primeiro bloco e, com **Shift** carregado, no segundo: os dois ficam escolhidos. Arraste o losango
   de um deles: os dois mudam de sítio.
8. Escolha só um bloco. **Clique no valor** da cota de um beirado (a caixa escura com «2,80 m»), escreva `3,2` e
   **Enter**: esse beirado sobe para 3,20 m.
9. Sem clicar em cota nenhuma, escreva `3,5` e **Enter**: o bloco inteiro sobe (todos os beirados).
10. Com um bloco escolhido, carregue em **Delete**: o bloco sai. **Ctrl+Z** desfaz cada passo. **Esc** sai.

## 0.384 — A calha à altura certa e ligada nos cantos

1. Feche o ArqSynth BIM e abra-o outra vez; o título deve dizer **0.384.0**. Crie um projeto novo com **Ctrl+N**.
2. Separador **Arquitetura** ▸ **Parede**; na barra por baixo da fita, em **Forma**, escolha **Retângulo**. Clique num
   canto no chão, escreva `6;4` e **Enter**. Carregue em **Esc**.
3. **Arquitetura** ▸ **Cobertura**; em **Contorno** escolha **Pelas paredes (clique dentro)** e em **Forma** **Quatro
   águas**; clique dentro das paredes. Carregue em **Esc**.
4. **Arquitetura** ▸ **Calha**. Passe o rato perto de um beirado: aparece a calha em volume, encostada à testeira,
   logo abaixo da aresta de cima. Clique.
5. Passe o rato pelo beirado **ao lado** (o que faz canto com o primeiro): junto ao rato diz «liga-se a 1 calha no
   canto». Clique: as duas calhas prolongam-se até ao canto e cortam-se em meia-esquadria.
6. Rode a vista até ao canto (botão do meio do rato): a calha dobra a esquina sem buraco. **Ctrl+Z** separa-as.

## 0.383 — As prévias das paredes em volume

1. Num projeto novo, separador **Arquitetura** ▸ **Parede**. Na barra por baixo da fita, em **Forma**, escolha
   **Retângulo**.
2. Clique num canto no chão e leve o rato (sem clicar): a prévia mostra as quatro paredes em volume — faces
   translúcidas sombreadas, o topo mais claro, arestas verticais nos cantos. Carregue em **Esc**.
3. Em **Forma**, escolha **Círculo**: clique no centro e afaste o rato — um anel de parede em volume. **Esc**.
4. Em **Forma**, escolha **Arco**: clique no início, clique no fim e leve o rato — o arco de parede em volume, com as
   pontas fechadas. **Esc**.
5. Em **Forma**, escolha **Linha**: clique e leve o rato — a parede reta com a mesma prévia.

## 0.382 — Lajes e coberturas: as pegas só a arrastar

1. Feche o ArqSynth BIM e abra-o outra vez. Crie um projeto novo com **Ctrl+N**.
2. **Laje:** separador **Arquitetura** ▸ **Laje**; clique num canto no chão, leve o rato e clique no canto oposto
   (uma laje retangular). Carregue em **Esc**, depois em **Espaço**, e clique na laje para a selecionar.
3. Na barra por baixo da fita, clique em **Editar contorno**: aparecem quadrados nos cantos e losangos no meio dos
   lados.
4. Carregue num quadrado e, sem largar, leve-o para fora; largue: o canto muda.
5. **Clique** outra vez no mesmo quadrado e leve o rato para longe sem carregar no botão: o canto **fica** (antes ia
   atrás do rato). Junto ao canto aparece «Escolhido: Delete tira este canto».
6. Carregue em **Delete**: o canto sai (a laje fica com três). **Ctrl+Z** volta a pô-lo.
7. Arraste o losango do meio de um lado para fora: um canto novo.
8. **Cobertura por blocos:** separador **Arquitetura** ▸ **Cobertura**; na barra por baixo da fita, em **Contorno**,
   escolha **Por blocos**; clique em dois cantos no chão. Carregue em **Esc**, depois em **Espaço**, e clique na
   cobertura para a selecionar. Arraste o quadrado de um lado de um bloco: o bloco estica. **Clique** no losango do meio de
   um bloco e leve o rato: o bloco **não** se mexe. Para o mover, arraste esse losango.

## 0.381 — As curvas do perfil já não se desfazem com um clique

1. Feche o ArqSynth BIM e abra-o outra vez. Faça os passos 1 a 3 da secção 0.380 (parede de 6 m, **Espaço**,
   **duplo clique** nela).
2. Carregue no **Shift** e mantenha-o. Arraste o losango do meio do lado de **cima** para cima e largue o rato:
   o topo fica em arco. Largue o Shift.
3. **Clique** outra vez no mesmo sítio (em cima da pega do arco) e leve o rato para o outro lado da parede, sem
   carregar no botão: o arco **fica** como está (antes ia atrás do rato).
4. Carregue no **Alt da esquerda** e mantenha-o. Arraste o losango do meio do lado **esquerdo** para dentro da parede
   e largue: o lado fica curvo. Largue o Alt.
5. Clique **uma vez** no quadrado do canto de baixo à esquerda: junto a ele aparece «Escolhido: Delete tira este
   canto». Carregue em **Delete**: o canto sai. **Ctrl+Z** volta a pô-lo.
6. **Concordância:** com o **Alt da esquerda** carregado, clique num canto entre dois lados retos e largue o Alt.
   Afaste o rato (o raio segue-o) e clique — ou escreva `0,5` e **Enter**.

## 0.380 — O perfil da parede com gestos (arrastar, Shift, Alt)

1. Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Crie um projeto novo com **Ctrl+N**.
2. Carregue em **W**, clique no chão, leve o rato para a direita, escreva `6` e carregue em **Enter**. Depois
   **Esc**.
3. Carregue em **Espaço** e faça **duplo clique** na parede. A vista vira-se de frente para a parede; aparecem
   quadrados nos cantos e losangos no meio dos lados.
4. **Canto novo:** carregue no losango do meio do lado de **baixo** e, sem largar o botão, leve o rato cerca de 1 m
   para cima. Largue: aparece um canto novo — um recorte em bico na base.
5. **Arco:** carregue no losango do meio do lado de **cima** e, sem largar, leve o rato para cima. Enquanto o move,
   carregue em **Shift** e mantenha-o: o topo passa logo a arco (junto ao rato diz «Arco»). Largue o rato: o topo fica
   em arco.
6. **Curva:** carregue em **Alt** e mantenha-o; carregue no losango do meio do lado **esquerdo** e arraste-o para
   dentro da parede. Largue: o lado fica curvo, com duas tangentes (losangos com linhas). Arraste uma tangente (sem
   Alt) para afinar a curva.
7. **Concordância:** com **Alt** carregado, clique no **quadrado do canto de baixo à direita** e largue o Alt. Afaste
   o rato do canto: o canto arredonda-se e junto ao rato aparece «Raio …». Escreva `0,5` e carregue em **Enter**: o
   canto fica arredondado com 0,50 m de raio. (Também pode só clicar, com o raio que o rato mostra.) Como o canto
   está ao lado do recorte do passo 4, que é reto, a concordância pode fazer-se.
8. **Ctrl+Z** desfaz cada passo. **Esc** sai do perfil e a vista volta onde estava.
9. Fora do perfil, **C** continua a ser a **Cota**.

## 0.379 — O perfil da parede: o contorno a meio do movimento

> Mudado na 0.381: um clique já não pega numa pega para a levar até ao clique seguinte — arraste com o botão
> carregado (passos 2–4 abaixo: carregue no losango, leve-o sem largar e largue).

1. Feche o ArqSynth BIM e abra-o outra vez. Faça os passos 1 a 3 da secção 0.378 (parede de 6 m, **Espaço**,
   **duplo clique** nela).
2. Clique **uma vez** no losango do meio do lado de **baixo** e largue o botão logo.
3. Leve o rato para cima, sem clicar: a parede fica cinzenta inteira e o contorno novo aparece em linhas azuis — um
   bico a subir a partir da base. Junto ao rato aparecem as medidas e «largue ou clique para pousar».
4. Clique: o recorte fica feito — por baixo do bico passa a ver-se o chão.
5. Agora a arrastar: carregue no quadrado da ponta do bico e, sem largar, leve-o mais para cima. Largue: o recorte
   fica mais alto.

## 0.378 — O perfil da parede, simples e direto

> Substituído na 0.380: as teclas C/A/B/R e os botões de modo saíram; ver a secção 0.380 (arrastar, Shift, Alt).

1. Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Crie um projeto novo com **Ctrl+N**.
2. Carregue em **W**, clique no chão, leve o rato para a direita, escreva `6` e carregue em **Enter**. Depois
   **Esc**.
3. Carregue em **Espaço** e faça **duplo clique** na parede. A vista vira-se de frente para a parede, aparecem
   quadrados nos cantos e losangos no meio dos lados, e na barra por baixo da fita está **Modo: Canto (C) · Arco (A)
   · Curva (B) · Reto (R)**.
4. Carregue na tecla **A**: acende-se **Arco (A)**.
5. Carregue no losango do meio do lado de **cima**, sem largar o botão leve o rato para cima cerca de 1 m e largue:
   o topo fica em arco.
6. Carregue na tecla **B**: acende-se **Curva (B)**. Arraste o losango do meio do lado **esquerdo** para dentro da
   parede e largue: o lado fica curvo, com duas tangentes (losangos com linhas). Arraste uma tangente para afinar.
7. Carregue em **C** e arraste o losango do meio do lado de baixo para cima: aparece um canto novo (um recorte).
8. Carregue em **R** e clique no losango do arco: o topo volta a ser reto.
9. **Ctrl+Z** desfaz cada passo. Carregue em **Esc**: sai do perfil e a vista volta à posição de antes.

## 0.377 — Os menus no fundo do ecrã abrem para cima

1. Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), com a janela maximizada.
2. Clique na **engrenagem**, em baixo à esquerda: a lista abre **para cima**, toda à vista, com o fundo ao nível do
   botão.
3. Passe o rato por **Painéis** (a última linha): a lista dos painéis abre à direita e sobe, sem ficar atrás da barra
   de tarefas. O mesmo em **Paletas (Bege, Areia, …)**.
4. Feche com **Esc**. Selecione uma parede e clique com o **botão direito** sobre ela perto do fundo da vista: o menu
   abre para cima do rato.
5. No **Navegador do Projeto**, clique com o botão direito numa linha perto do fundo do painel: o menu também sobe.

## 0.376 — Os temas à vista

1. Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**).
2. No cabeçalho azul escuro, em cima à direita, há um botão novo com uma **paleta de pintor** (entre a nuvem e o
   «?»). Clique nele: abre a lista dos temas.
3. Clique em **Bege**: a interface muda logo. Volte a abrir o botão e experimente **Areia**, **Pedra**, **Escuro** e
   **Grafite**.
4. No mesmo botão, **Explorar cores…** abre a janela para afinar as cores (ver 0.374, passo 12).
5. Para voltar ao de antes: o mesmo botão ▸ **Tema claro**.

## 0.375 — Arcos e curvas de Bézier no perfil da parede

1. Num projeto novo, faça uma parede reta de 6 m (**W**, clique, rato para a direita, `6` e Enter, **Esc**).
2. Carregue em **Espaço** e faça **duplo clique** na parede: abre-se a edição do perfil, com quadrados nos cantos e
   losangos no meio dos lados. (Carregue em **F3** para a ver de frente.)
3. Carregue em **Tab**: a barra por baixo da fita passa a dizer **«Clique no meio de um lado: Faz um arco»**.
4. Clique no losango do meio do lado de cima e suba o rato cerca de 1 m: o topo curva em arco, a passar pelo rato.
   Clique: a parede fica com o topo em arco.
5. Na barra, escolha **Faz uma curva Bézier**. Clique no losango do meio do lado esquerdo: aparecem dois losangos
   (as tangentes), com linhas desde os cantos, e o primeiro já pegado. Leve-o para dentro da parede e clique: o lado
   fica curvo.
6. Clique na outra tangente, mova-a e clique outra vez: a curva muda.
7. Clique num canto de cima e mova-o: a tangente desse canto vai com ele.
8. Na barra, escolha **Endireita o lado** e clique na pega do arco: o topo volta a ser reto.
9. **Ctrl+Z** desfaz cada passo. Carregue em **Esc** e rode a vista: o arco e a curva estão lisos. Grave e volte a
   abrir: a parede está igual.

## 0.374 — Ferramentas de arquitetura do addon; os temas do estudo

1. Num projeto novo (**Ctrl+N**), clique no separador **Arquitetura**. No painel **Paredes** estão à vista
   **Retangular**, **Circular**, **Arco**, **Por face** e **Varinha mágica**.
2. Carregue em **F4** (planta). Clique em **Retangular**, clique num ponto, escreva `6;4` e Enter: quatro paredes.
3. Em **Ambientes**, clique em **Separador**: clique a meio da parede de baixo, por dentro, e depois a meio da de cima;
   **Esc**.
4. Clique em **Identificar**: aparecem dois ambientes numerados (1 e 2). Clique em **Áreas**: a tabela mostra a área
   útil e a área bruta do pavimento. Feche-a.
5. Em **Pisos e coberturas**, clique em **Piso**; na barra por baixo da fita escolha **Madeira**; clique dentro do
   ambiente da esquerda: o piso fica só nesse ambiente.
6. Carregue em **F8** (3D). Em **Aberturas**, clique em **Nicho**. Clique na face de fora de uma parede, a meia
   altura, escreva `0,6;0,5` e Enter: um nicho de 10 cm de fundo (a profundidade muda-se na barra).
7. Em **Circulação**, clique em **Elevador** e clique ao lado da casa: a caixa e a cabina. Antes de clicar, **R** roda-o.
8. Em **Pisos e coberturas**, clique em **Cobertura**, escolha na barra a forma **Pelas paredes** e clique dentro da
   casa. Depois clique em **Calha**, passe o rato pela cobertura (o beirado mais próximo fica azul) e clique: a calha
   fica ao longo dele.
9. **Guarda num vão**: ponha uma **Janela** numa parede; clique em **Guarda-corpo**, escolha na barra a forma **Num
   vão** e clique na janela.
10. **Varinha mágica**: ligue um DWG/DXF de uma planta (**Início ▸ Ligar um desenho DXF/DWG…**). Clique em **Varinha mágica** e,
    na planta, arraste uma janela por cima das duas linhas de uma parede do desenho: a parede fica entre elas, com a
    espessura medida.
11. **Temas**: separador **Visualizar**, painel **Tema**: clique em **Bege**, **Areia**, **Pedra**, **Escuro** e
    **Grafite** — muda logo tudo; os títulos dos painéis ficam tingidos do azul do estudo.
12. Clique em **Explorar cores…**: mude, por exemplo, o **Destaque** (clique no quadrado da cor, ou escreva o código
    `#C0392B` e Enter): a interface muda logo e fica guardada. **Repor bege** volta ao bege; **Copiar paleta CSS**
    copia as cores. Feche e abra o programa: fica como deixou.

## 0.373 — Desenho livre como no SketchUp: uma linha sozinha, Offset, Arco, Linha livre, Bézier

1. Num projeto novo (**Ctrl+N**), clique no separador **Modelagem** (em cima). No painel **Desenhar** estão agora
   **Linha**, **Arco**, **Retângulo** e **Círculo**, e, pequenos, **Linha livre**, **Curva de Bézier** e **Offset**.
2. Carregue em **L**, clique na origem, leve o rato ao longo do eixo vermelho e escreva `4` + Enter; leve o rato para
   cima (eixo verde) e escreva `3` + Enter; para a esquerda, `2` + Enter. Carregue em **Esc**.
3. Carregue em **Espaço** (Selecionar) e clique **a meio da linha de 3 m**: só ela fica azul, com a cota «3,00 m». A
   barra azul diz «Linha selecionada (3,00 m)».
4. Carregue em **Ctrl+C** e depois em **Ctrl+V**: a cópia segue o rato. Clique noutro sítio do chão: fica lá uma
   linha de 3 m sozinha. Carregue em **Esc**.
5. Clique outra vez a meio da linha de 3 m e, logo a seguir, outra vez no mesmo sítio (dois cliques): fica escolhida
   a cadeia toda (as três linhas).
6. Clique num sítio vazio. Clique uma vez a meio da linha de 3 m. Carregue em **M** (Mover), clique na linha, leve o
   rato para a direita e escreva `1` + Enter: a linha anda 1 m e as duas linhas ligadas às pontas esticam.
7. Carregue em **Delete**: só essa linha desaparece. **Ctrl+Z** volta a pô-la.
8. **Offset de linhas**: carregue em **F** e clique na linha de 4 m. Leve o rato para dentro (para cima) e escreva
   `0,5` + Enter: aparece a paralela das três linhas, a 0,5 m, com os cantos vivos.
9. **Arco**: **Ctrl+N**. Carregue em **L**, clique na origem, escreva `4` + Enter ao longo do eixo vermelho e
   carregue em **Esc**. Carregue em **A** (Arco). Clique na ponta da direita da linha (a dica diz «Extremidade») e
   depois na origem. Afaste o rato para cima: o arco segue o rato; perto da meia circunferência fica magenta e a dica
   diz «Meia circunferência». Escreva `1,5` + Enter: o arco fecha com a linha — a barra azul diz «O arco fechou o
   contorno: face de … m²» — e fica uma face.
10. Logo a seguir, escreva `2r` + Enter: o arco passa a meia circunferência de raio 2 m.
11. Na barra por baixo da fita, em **Arco**, escolha **Centro e ângulo**. Clique num ponto do chão (o centro), noutro
    a 1 m (o raio) e rode o rato: prende de 15 em 15°. Clique (ou escreva `90` + Enter).
12. Carregue em **Espaço** e clique no arco do passo 11: escolhe-se inteiro, com três pegas — as pontas (quadrados) e
    o meio (losango). Arraste o losango: muda a flecha. Nas **Propriedades** (à direita), mude o **Raio** para `3` e
    carregue em Enter.
13. **Linha livre**: clique em **Linha livre** (painel Desenhar). Carregue no chão e, sem largar, desenhe uma volta e
    solte perto de onde começou: fica uma face.
14. **Bézier**: clique em **Curva de Bézier**. Clique num ponto do chão (um canto). Noutro ponto, carregue e arraste:
    a tangente sai para onde arrasta (um ponto suave); solte. Clique num terceiro ponto e carregue em **Enter**: fica
    a curva.
15. Carregue em **Espaço** e clique na curva: mostra os pontos (quadrados) e as tangentes (losangos, com as linhas).
    Arraste um losango: a curva muda; arraste um quadrado: o ponto muda com as suas tangentes.
16. Carregue em **P** (Push/Pull) e puxe a face do arco (passo 9): sobe com o lado curvo liso.

## 0.372 — A Linha fecha a face onde se fecha; as cotas temporárias novas

1. Num projeto novo, abra o 3D (**F8**) e carregue em **L** (Linha).
2. Faça o desenho da sua imagem:
   - clique na origem e, ao longo do eixo vermelho, escreva `1` + Enter (um troço de 1 m);
   - dali, desenhe um retângulo: `4` + Enter para cima (eixo verde), `5` + Enter para a direita, `4` + Enter para
     baixo;
   - para fechar, leve o rato ao fim do primeiro troço (o ponto a 1 m da origem), que mostra «Extremidade», e
     clique. (Ou escreva `5` + Enter para a esquerda.)
3. O retângulo fica logo uma **face** de 20 m². A barra azul diz «Contorno fechado: face com 4 cantos e 20,00 m²; as
   linhas fora dela ficaram como linhas». O primeiro troço de 1 m fica como linha solta, e a Linha termina.
4. Carregue em **Ctrl+Z**: volta às linhas sem face. **Ctrl+Y** refaz a face.
5. Agora cruzando: **L**, clique noutro sítio, desenhe 4 m para a direita, 3 m para cima, 2 m para a esquerda e depois
   4 m para baixo, atravessando a primeira linha. O retângulo de 2 × 3 m fica face, e pode continuar a desenhar
   a partir do último ponto. **Esc** termina.
6. Carregue em **P** (Push/Pull) e puxe uma das faces: sobe como qualquer face.
7. **Cotas temporárias**: abra uma planta com paredes (**F4**) e clique numa parede interior.
   - O comprimento aparece afastado da parede, numa caixa escura com o número a branco, sobre uma linha azul com
     setas.
   - As distâncias às paredes vizinhas aparecem do mesmo modo, com **↔** antes do número.
8. Passe o rato por cima de um valor: a caixa fica azul. Clique, escreva `2` e Enter: a parede muda.
9. Clique na linha azul de uma distância, fora da caixa: troca entre **eixo a eixo** e **face a face** (como na 0.361).

## 0.371 — O modelo em USDZ (realidade aumentada)

1. Abra um projeto com paredes, uma porta, uma janela e uma laje.
2. Clique em **Início ▸ Exportar ▸ Exportar modelo 3D…**. Escolha **O modelo todo** e clique em OK.
3. No diálogo de gravar, em baixo, no **tipo**, escolha **Realidade aumentada USDZ, iPhone e iPad (*.usdz)** e clique
   em **Guardar**. A barra azul diz «Modelo 3D gravado em … .usdz: … elementos, … triângulos».
4. Mande o ficheiro para um iPhone ou iPad: por exemplo, por e-mail para si próprio, ou pelo iCloud Drive.
5. No iPhone, toque no ficheiro. Abre-se uma janela com o modelo:
   - no separador **Objeto**, rode-o com um dedo: as paredes têm as cores dos materiais e o vidro da janela é
     transparente;
   - no separador **RA**, aponte para o chão ou para uma mesa: o modelo pousa nela ao tamanho real. Aproxime dois
     dedos para o encolher numa maqueta e ande à volta dele.
6. (Opcional) Num Mac, abra o USDZ no Pré-visualizar ou no Reality Composer: o modelo está em pé, com os pavimentos,
   as categorias e os elementos pelos nomes do programa.

## 0.370 — As tabelas em Excel

1. Abra um projeto com algumas paredes e carregue em **Ctrl+T** (Tabelas). Escolha **Paredes**.
2. Clique em **Exportar (Excel, CSV)…**. O nome proposto acaba em **.xlsx**. Em baixo, no tipo, está **Livro do
   Excel (*.xlsx)**; também há **Tabela CSV para o Excel (*.csv)**. Clique em **Guardar**. A barra azul diz «Tabela
   exportada».
3. Abra o ficheiro no Excel:
   - a folha tem o nome da tabela; os títulos estão a negrito, com as setas do filtro, e ficam no topo quando desce;
   - clique numa célula do comprimento: é um **número** (alinhado à direita, com «5,00»). Selecione a coluna: em
     baixo, o Excel mostra a **Soma**.
4. Com o ficheiro ainda aberto no Excel, exporte outra vez para o mesmo nome: o programa diz que não conseguiu gravar
   e para fechar o ficheiro no Excel. Feche-o e exporte outra vez: grava.
5. Num projeto com estrutura armada, abra **Estrutura ▸ Lista de armaduras…** e clique em **Exportar (Excel, CSV)…**.
   No Excel, as quantidades, os comprimentos e os pesos são números, com as casas que tinham na janela, e os totais
   ficam no fim.
6. O mesmo nas **Quantidades da estrutura** e na **Lista de corte** dos móveis.

## 0.369 — A vista em DWG e em SVG

1. Abra a planta de um projeto com paredes e uma porta (**F4**). Para ver as cotas no ficheiro, clique em **Anotar ▸
   Cotar fachadas** (no painel das cotas).
2. Clique em **Início ▸ Exportar ▸ Exportar vista (DXF, DWG, SVG)…**. No diálogo de gravar, em baixo, no **tipo**,
   escolha **Desenho DWG do AutoCAD (*.dwg)** e clique em **Guardar**.
3. A barra azul diz «Vista exportada em DWG (AutoCAD 2018): … elementos, em metros, textos para 1:100».
4. Abra o DWG no AutoCAD (ou num visualizador de DWG): as paredes cortadas estão na camada **CORTE**, as cotas com os
   valores, tudo em metros.
5. Volte a **Exportar vista…** e escolha agora **Desenho SVG (*.svg)**. Clique em **Guardar**. A barra azul diz a
   escala e o tamanho em milímetros.
6. Abra o SVG no navegador (arraste-o para o Edge ou o Chrome) ou no Inkscape. Deve ver:
   - a planta como no PDF, com a trama **só dentro das paredes**;
   - as cotas e as marcas dos alçados inteiras, nada cortado na borda.
   No Inkscape, o desenho tem o tamanho certo para a escala (uma parede de 10 m mede 100 mm a 1:100).
7. Folhas em SVG (a correção): no painel **Projeto**, em **Folhas**, clique com o botão direito numa folha com uma
   planta, escolha **Exportar em SVG…** e uma pasta. Abra o SVG no navegador: a trama das paredes já não se espalha
   pela folha.

## 0.368 — Panoramas 360° para o Presentation

1. Abra um projeto com uma sala com ambiente (o da 0.367 serve) e uma folha com a planta do térreo. Se o projeto nunca
   foi gravado, grave-o (**Ctrl+S**): os panoramas ficam numa pasta ao lado dele.
2. Ponha a câmara do 3D dentro da sala, à altura dos olhos: abra a vista 3D (**F8**), clique em **Vista ▸ Posicionar
   câmara** e clique no chão da sala, onde ficaria de pé. Com **Vista ▸ Olhar em volta**, arraste para virar a cabeça
   para onde quer que o panorama comece (o meio da imagem).
3. Clique em **Render ▸ Panorama 360°…**. No diálogo:
   - **Nome**: deixe «Panorama 1» ou escreva «Sala»;
   - **Tamanho**: **2048 × 1024**;
   - **Qualidade**: **Rascunho** para experimentar.
   Clique em **OK**.
4. Abre-se a janela do render, como a do render realista, e a barra azul diz «A fazer o panorama… seis vistas, uma a
   uma». A imagem é larga (2 : 1) e vai ficando mais fina. Pode continuar a trabalhar entretanto.
5. Quando acabar, a barra azul diz «Panorama «Sala» guardado com o projeto». Feche a janela do render.
6. No Explorador do Windows, ao lado do projeto, há a pasta **«<nome do projeto> - panoramas»** com um JPEG.
7. Clique em **Render ▸ Cenas da apresentação**: em baixo, na lista **Panoramas 360°**, aparece «Sala».
   - Escolha-o e clique em **Remover**: sai da lista. Carregue em **Ctrl+Z**: volta.
8. Experimente os avisos:
   - numa planta (**F4**), **Render ▸ Panorama 360°…** diz que é preciso o 3D em perspetiva;
   - num projeto novo nunca gravado, diz para gravar primeiro.
9. Clique em **Início ▸ Exportar ▸ Para o ArqSynth Presentation…** e grave o pacote (.zip). A barra azul diz «… 1
   folha para as plantas, 1 panorama 360°, …».
10. No Presentation com o ramo `integracao-arqsynth-bim`, na lista de páginas, clique em **ArqSynth BIM** e escolha o
    ZIP. Na página da planta aparece um **ponto 360°** dentro da sala, no sítio onde estava a câmara. Clique nele (em
    modo de apresentação): abre o panorama, e pode olhar à volta.
11. No Presentation, ponha um ponto à mão nessa planta (por exemplo um ponto de informação). No BIM, faça outro
    panorama, exporte e importe outra vez o pacote: o ponto feito à mão continua lá, e o do BIM atualiza-se.
12. A correção no Presentation: num projeto com duas plantas, ponha em cada uma um ponto com uma fotografia (ou use os
    panoramas do BIM em dois pisos). Espere mais de 10 minutos. Mude o nome do ponto da primeira planta (grava
    sozinho). Abra a segunda planta e clique no ponto dela: a fotografia continua lá (antes desaparecia).

## 0.367 — O pacote para o Presentation: o modelo e as folhas como plantas

1. Abra um projeto com ambientes (os da 0.366) e faça as folhas: **Início ▸ Exportar ▸ Folhas por pavimento…** (ou uma
   folha à mão com a planta do térreo).
2. Clique em **Início ▸ Exportar ▸ Para o ArqSynth Presentation…**. O nome proposto acaba em **.zip**; em baixo, no
   tipo, há também **Só o modelo 3D (*.glb)**. Deixe o pacote e clique em **Guardar**.
3. A barra azul diz quantos elementos, cenas e folhas foram.
4. (Opcional) Abra o ZIP no Explorador do Windows: lá dentro estão `manifest.json`, `modelo.glb` e a pasta `folhas`
   com um PDF por folha.
5. No Presentation com o ramo `integracao-arqsynth-bim`, na lista de páginas, clique em **ArqSynth BIM** e escolha o
   ZIP:
   - aparece a página 3D com o modelo e as cenas;
   - aparece uma página de planta por folha. Na camada **Ambientes**, cada sala tem o seu polígono por cima da planta,
     com o nome e a área.
6. Mude o título de uma página de planta e desenhe um fluxo nela. No BIM, mexa numa parede, exporte de novo e volte a
   importar o pacote: a planta atualiza-se, e o título e o fluxo continuam lá.

## 0.366 — Os ambientes e o Passeio Virtual

1. Abra um projeto com duas salas lado a lado, uma porta entre elas e uma porta para a rua (ou desenhe-as: paredes, uma
   divisória, **Arquitetura ▸ Porta** em cada uma).
2. Ponha os ambientes: **Arquitetura ▸ Ambiente** e um clique dentro de cada sala. Dê-lhes nome, por exemplo «Sala» e
   «Cozinha».
3. **Render ▸ Cenas da apresentação**: por baixo da lista aparecem **Etiquetas dos ambientes (2)** e **Passeio Virtual
   pelos ambientes (2)**, ligados.
4. Desligue **Passeio Virtual pelos ambientes** e carregue em **Ctrl+Z**: volta a ficar ligado.
5. **Exportar para o Presentation…** e importe no Presentation com o ramo `integracao-arqsynth-bim`:
   - cada sala tem a sua etiqueta deitada no chão, com o nome, o número e a área;
   - na aba **Passeio**, há um piso, uma zona por sala (a cozinha com o tipo «cozinha») e um fluxo pela porta entre
     elas; o passeio começa na sala onde está a porta da rua.
6. Com dois pisos e uma escada entre eles (e um ambiente no pé e outro na cabeça da escada), o passeio vai de um piso
   ao outro pela escada.

## 0.365 — O ambiente e os efeitos: o sol, a exposição, o vidro, a água e as luzes

1. Abra um projeto com paredes e uma janela. Se o terreno ainda não tiver lugar, abra **Render ▸ Cenas da
   apresentação** e escolha uma cena: os campos do sol estão cinzentos e há uma nota a dizer que falta o lugar.
2. Clique em **Terreno ▸ Localização** e dê o lugar (por exemplo Lisboa). No painel, os campos do sol ficam ativos.
3. Escolha a **Vista geral**. Em **Sol (dia e hora)** escreva **21/12** e **10:00**. Em **Exposição** ponha **1,20** e
   ligue **Céu atrás do modelo**.
4. Clique em **Ver sol**: no 3D aparecem as sombras desse sol de inverno, baixo, a vir de sueste; a barra azul diz o
   azimute e a altura. Carregue em **Esc**: volta o sol do estilo de vista.
5. Em **Animação do sol** escolha **Ao longo do dia** e clique em **Ver sol**: em 8 s o sol vai do nascer ao pôr, e as
   sombras rodam. Experimente **Ao longo do ano**: os doze meses a essa hora.
6. Ponha 22:00 e clique em **Ver sol**: a barra diz que é noite.
7. Água: desenhe uma laje no exterior (ferramenta Laje) e, em **Gerenciar ▸ Materiais**, dê-lhe o material **Água
   (piscina, lago)** (ou escolha o acabamento **Água** num material seu). No **Render realista** a água refrata.
8. Luzes: ponha uma luminária no teto de uma sala (**Instalações ▸ Luminária**).
9. **Exportar para o Presentation…** e importe no Presentation com o ramo `integracao-arqsynth-bim`: cada cena com o
   seu sol, exposição e céu; o vidro da janela como vidro, a água animada, a luminária a brilhar (aba Material).

## 0.364 — Os movimentos de câmara

1. Abra um projeto com paredes e pelo menos um ambiente (**Arquitetura ▸ Ambientes e tetos ▸ Ambiente**, um clique
   dentro de uma sala). Faça uma vista 3D com nome a olhar para essa sala (**Render ▸ Nova vista 3D**).
2. Clique em **Render ▸ Cenas da apresentação** e escolha a **Vista geral** na lista.
3. Em **Movimento**, escolha **Órbita ascendente** (grupo Exterior). Ao lado aparece «14 s (o do movimento)».
4. Clique em **Ver movimento**. No 3D, a câmara dá a volta ao edifício e sobe, ao ritmo do Presentation; a barra azul
   diz o nome e o tempo. No fim, a câmara volta onde estava.
5. Escolha a vista 3D na lista e, em **Movimento**, **Volta ao compartimento** (grupo Interior). Aparece a linha
   **Ambiente**, em «O da cena (automático)»; abra-a: lá está a sua sala.
6. Mude o tempo para **10 s** e clique em **Ver movimento**: a câmara dá a volta dentro da sala, à altura do olhar.
   Carregue em **Esc** a meio: pára e volta onde estava.
7. Experimente outros (Aproximação, Subida de fachada, Espiral ascendente…) com **Ver movimento**.
8. Ctrl+Z desfaz cada escolha; guarde, feche e abra o projeto: os movimentos estão lá.
9. **Exportar para o Presentation…** e, no Presentation com o ramo `integracao-arqsynth-bim`, importe o GLB numa página
   Modelo 3D: na aba dos efeitos de câmara, cada cena tem o movimento escolhido, com o mesmo nome e o mesmo tempo, e
   ele toca ao entrar na cena da apresentação.

## 0.363 — O painel Apresentação: as cenas preparadas aqui

1. Abra um projeto com paredes. Faça uma vista 3D com nome (rode o 3D e clique em **Render ▸ Nova vista 3D**) e um corte
   (**Anotar ▸ Corte**: dois cliques atravessando o edifício).
2. Clique em **Render ▸ Cenas da apresentação**. À esquerda abre-se o painel **Apresentação** com as cenas: 01 Vista
   geral (com «entrada» por baixo), a vista 3D, a planta de cada pavimento e o corte.
3. Clique em **Miniaturas**. O programa passa pelas vistas uma a uma e volta à vista em que estava. Cada cena fica com a
   sua imagem pequena, e a barra azul diz quantas tirou.
4. Escolha o corte na lista e clique em **Subir** até ficar logo a seguir à vista geral. (Também pode arrastá-lo na
   lista.)
5. Com o corte escolhido, em **Cena escolhida**:
   - **Chegada**: **Corte seco** (o tempo ao lado fica cinzento: um corte seco não tem duração);
   - **Efeito**: **Construção, peça a peça**, e 10 s ao lado;
   - **Tempo na cena**: 8 s;
   - **Legenda**: escreva uma frase e clique noutro sítio do painel.
6. Escolha a **vista geral** e ligue **Fora da apresentação**: na lista fica «fora» por baixo dela, e a vista 3D passa a
   ser a «entrada». Carregue em **Ctrl+Z**: volta a estar dentro. Ligue-a outra vez, se quiser.
7. Escolha a vista 3D e ligue **Cena de entrada**.
8. Faça duplo clique numa cena da lista: abre-se a vista dela (a vista geral abre o 3D visto de sudoeste, de cima).
9. Guarde o projeto, feche-o e abra-o de novo: no painel, a ordem e as escolhas estão como as deixou.
10. Clique em **Exportar para o Presentation…** (no fundo do painel), escolha o nome e clique em **Guardar**. O programa
    passa outra vez pelas cenas (as miniaturas) e grava o GLB.
11. No ArqSynth Presentation **com o ramo `integracao-arqsynth-bim`**, numa página **Modelo 3D**, importe esse GLB: as
    cenas chegam pela ordem do painel, com as miniaturas, a entrada, a de fora (com o olho cortado), o corte seco, o
    efeito e a legenda. (O Presentation publicado em arqsynth.com ainda não tem este importador: abre o GLB como um
    modelo qualquer.)

## 0.362 — Para o ArqSynth Presentation: o pacote

1. Abra um projeto com paredes, portas e janelas. Se ainda não tiver, faça uma vista 3D com nome: rode o 3D até
   gostar da vista e clique em **Render ▸ Nova vista 3D**.
2. (Opcional) Faça um corte (**Anotar ▸ Corte**). Na vista 3D com nome, ligue a **caixa de corte** (Visualizar ▸
   Caixa de corte) ou, sem nada escolhido, clique em **Visibilidade…** nas Propriedades e esconda uma categoria.
3. Clique em **Início ▸ Exportar ▸ Para o ArqSynth Presentation…** (está também em **Render ▸ Apresentação**).
4. Escolha a pasta e o nome (por omissão «<projeto> - Presentation.glb») e clique em **Guardar**. A mensagem azul diz
   quantos elementos e quantas cenas foram: a vista geral, cada vista 3D com nome, uma planta por pavimento e cada
   corte.
5. No ArqSynth Presentation (a versão atual), numa página **Modelo 3D**, importe esse GLB: o modelo entra como
   qualquer outro, com uma camada por elemento. As cenas preparadas no BIM só entram quando o importador estiver
   feito, no passo seguinte.

## 0.361 — A cota temporária: a relação com as outras paredes

1. Abra a planta (F4). Com a ferramenta **Parede**, desenhe uma sala de uns 10 × 7 m e uma divisão interior de lado a
   lado. Faça mais uma parede curta que parta da divisão e **não chegue** à parede da frente (deixe uma passagem de
   1 a 2 m).
2. Esc e clique na parede curta (ferramenta **Selecionar**). Aparecem:
   - o **comprimento** dela, a âmbar, ao lado;
   - a **verde**, a distância até à parede de cada lado e a distância da ponta solta até à parede da frente;
   - no separador verde **Modificar | Paredes**, o painel **Cotas temporárias** com **Eixo a eixo** carregado.
3. Passe o rato por cima de um número verde: a cota fica realçada (preta; branca no fundo escuro).
4. Clique na **linha** de uma cota verde (na linha, não no número): todas passam a **face a face** (os vãos livres).
   O botão **Face a face** fica carregado, e a barra de baixo diz «Cotas de face a face».
5. Clique no **número** da cota da passagem e escreva `0,90`: o número aparece na cota como «[ 0,90 ]». Carregue em
   Enter: a parede estica até a passagem ficar com 90 cm livres. Ctrl+Z desfaz.
6. Clique numa cota verde de lado, escreva outra medida e Enter: a parede vem para essa distância da outra.
7. Clique em **Eixo a eixo** no separador verde: as cotas voltam a medir pelos eixos.
8. **Visualizar ▸ Tema ▸ Vistas escuras**: o comprimento fica amarelo e as relações verdes, como no Blender. Volte ao
   fundo claro.
9. Feche e abra o programa e escolha outra parede: as cotas medem como as deixou (eixos ou faces).

## 0.360 — O gerador de símbolos

1. Numa casa com paredes, faça um corte (**Anotar ▸ Corte**: dois cliques atravessando a casa) e abra a planta (F4):
   vê o corte com a cabeça redonda e a seta cheia, e os alçados (Norte, Sul…) à volta.
2. Clique em **Anotar ▸ Símbolos…**. Abre-se a janela **Símbolos** com quatro separadores: Corte, Alçado (vista),
   Pormenor e Nível.
3. No separador **Corte**:
   - mude a **Cabeça** para **Quadrado**: o desenho à direita passa a ter quadrados com o «1»;
   - mude a **Seta** para **Nenhuma** e a **Linha** para **Só nas pontas**: a linha fica só junto das cabeças;
   - mude o **Raio da cabeça** para 5 mm: as cabeças crescem no desenho.
4. Clique em **OK**. A barra azul diz «Símbolos mudados». Na planta, o corte tem agora as cabeças quadradas, sem seta
   e a linha só nas pontas.
5. Faça uma folha com essa planta e exporte o PDF (ou o DXF): o corte está desenhado da mesma maneira.
6. Carregue em **Ctrl+Z**: volta tudo ao que era.
7. Abra outra vez **Símbolos…** e experimente o separador **Nível** (a marca em **Círculo em quartos**) e o
   **Alçado (vista)**. **Os de sempre** repõe tudo como estava; **Cancelar** não muda nada.
8. Grave o projeto, feche e abra-o: os símbolos continuam como os deixou.

## 0.359 — A porta em planta

1. Numa casa com paredes, escolha a ferramenta **Porta** (porta de 90 cm) e abra a planta (F4).
2. Passe o rato sobre uma parede: aparece a abertura com a **folha aberta e o arco**. Passe para a outra face da parede:
   o arco vira-se para lá. Carregue em **Espaço**: as dobradiças passam para o outro aro (o arco também). Clique: a
   porta fica como se via.
3. Esc e, com **Selecionar**, clique na porta: aparecem **duas setas** azuis com um losango cada.
   - Clique no losango da seta **atravessada** (ao lado da porta): a porta passa a abrir para o outro lado da parede.
   - Clique no da seta **ao longo da parede** (em frente da porta): as dobradiças passam para o outro aro.
   - Ctrl+Z desfaz cada passo.
4. Aproxime-se da porta na planta (roda do rato): o **aro** (as duas peças nas pontas da abertura), as **guarnições**
   (as peças finas nas faces da parede) e a soleira estão desenhadas cada uma com o seu contorno, não como uma massa
   só. Não há uma folha fechada dentro do aro ao mesmo tempo que a folha aberta.
5. Com a porta escolhida, abra o **Caixilho Studio** (Propriedades ▸ o botão do tipo / do desenho da porta) e clique em
   **Planta…**:
   - escolha **Em planta: Fechada, com a linha de abertura** e **Linha de abertura: Tracejada** — o desenho ao lado
     mostra a folha no aro e o arco e a linha a tracejado;
   - mude as **guarnições** para 70 mm e veja o desenho mudar; OK e aplique o tipo.
6. Na planta, as portas desse tipo aparecem fechadas com a linha de abertura tracejada. Faça uma folha com a planta e
   exporte o PDF: o mesmo.

## 0.358 — A linha de corte editável

1. Numa casa com paredes, faça um corte (Anotar ▸ Corte: dois cliques para a linha e um para o lado). Abra a planta
   (F4).
2. Com a ferramenta **Selecionar**, clique uma vez na **cabeça** do corte (o círculo com a seta). O balão diz «Corte 1:
   arraste os quadrados…»; aparecem dois quadrados azuis nas pontas da linha e um losango ao lado.
3. Arraste o quadrado de uma ponta para dentro do edifício: a linha fica mais curta desse lado. Arraste-o para fora:
   fica mais comprida.
4. Clique no **losango**: as setas viram-se, e o corte olha para o outro lado. Abra o corte (duplo clique na cabeça):
   vê-se o lado oposto.
5. Ctrl+Z desfaz cada passo. Clique num sítio vazio: o corte deixa de estar escolhido.

## 0.357 — Ambientes e o programa de necessidades

1. Clique em **Arquitetura**: no painel «Ambientes e tetos» o botão chama-se **Ambiente** (antes «Sala») e há um botão
   novo, **Programa de necessidades**.
2. Faça uma folha de cálculo com uma coluna de nomes, outra de áreas e outra de quantidades, por exemplo:

   | Ambiente | Área | Quantidade | Tipo |
   |---|---|---|---|
   | Quarto | 12,5 | 2 | interior |
   | Sala comum | 20 | 1 | |
   | Terraço | 8 | 1 | exterior |

   Grave-a como **CSV (separado por ponto e vírgula)**. Também serve um ficheiro de texto com um nome por linha.
3. Clique em **Programa de necessidades**: abre-se o painel à esquerda. Clique em **Importar…** e escolha o CSV. A lista
   mostra os ambientes, a área prevista e «0 / 2», «0 / 1»…
4. Abra a planta (F4). **Arraste «Quarto»** da lista para dentro de um espaço fechado por paredes e largue: o ambiente
   fica lá, chamado «Quarto», e a lista passa a «1 / 2» com a área feita.
5. Arraste «Terraço» para dentro de um ambiente que já existe: esse ambiente passa a chamar-se «Terraço» e a ser
   exterior.
6. Clique no ambiente com Selecionar: nas Propriedades, a linha **Interior ou exterior** mostra «Exterior». Mude-a.
7. Ctrl+Z desfaz cada passo.

## 0.356 — O telhado por blocos mais à mão

1. Faça uma casa em L com um telhado por blocos (Arquitetura ▸ Cobertura ▸ Por blocos), com dois blocos.
2. Com Selecionar, clique no telhado e, logo a seguir, **outra vez em cima do bloco menor** (duplo clique): abre o
   editor de blocos com esse bloco escolhido na lista.
3. Na linha nova **Altura do bloco**, escreva mais 0,50 m do que lá está e carregue em Enter: na planta do editor e em
   «Lados», as quatro alturas de beirado sobem 50 cm.
4. Em «Lados», mude a **inclinação** só do lado N (por exemplo 45°) e a altura do beirado só do lado E.
5. **Aplicar** e feche. No 3D, o bloco está mais alto, com uma água mais inclinada. Ctrl+Z desfaz.

## 0.355 — Duplo clique numa parede: o perfil

1. Com Selecionar, clique numa parede e logo a seguir outra vez nela: abre-se a ferramenta **Perfil da parede**, com os
   cantos do alçado da parede como pegas.
2. Arraste um canto de cima: a parede muda de forma. Esc volta a Selecionar.

## 0.354 — TAB, a edição rápida

1. Com **Selecionar**, clique numa parede e carregue em **TAB**: ao lado da parede abre-se a janelinha «Edição rápida
   (TAB)», com o tipo em cima e as restrições e dimensões (comprimento, base, topo, altura, perfil).
2. Mude o **Deslocamento da base** para 0,10 e Enter: a parede sobe 10 cm e a janelinha continua aberta, já com o valor
   novo. Ctrl+Z desfaz.
3. Escolha outro tipo na lista de cima: a parede muda de tipo.
4. Carregue em TAB outra vez (com o rato na vista): fecha-se. Também fecha com Esc, com o × ou com um clique na vista.
5. Faça o mesmo com uma porta, uma janela, uma laje e um telhado: cada uma mostra as suas medidas.
6. Com a ferramenta **Parede**, o TAB continua a mudar a linha de referência (eixo, face esquerda, face direita).

## 0.353 — «+» nas pontas da parede

1. Desenhe uma parede. Com **Selecionar**, clique nela: aparece um **«+»** azul em cada ponta.
2. Clique no «+» da ponta: passa à ferramenta Parede, do mesmo tipo, já a partir dessa ponta. Clique noutro sítio: fica
   uma parede nova, ligada à primeira em canto. Continue a clicar para mais paredes; Esc acaba.
3. Escolha duas paredes (Shift): não há «+» (só com uma parede escolhida).

## 0.352 — O reboco dá a volta às esquinas

1. Abra a casa do documento (ou desenhe quatro paredes em retângulo com **Parede de alvenaria 20 cm**).
2. Abra a vista 3D. Clique num sítio vazio da vista: o painel **Propriedades** mostra a vista. Em **Estilo visual**,
   escolha **Cores consistentes** (ou **Realista**).
3. Olhe para as esquinas de fora: o reboco dá a volta, sem a faixa de tijolo de alto a baixo e sem uma linha a meio
   da fachada. O mesmo nas esquinas do alpendre.
4. Faça um **Render realista** da esquina: também sem faixa.
5. Desenhe uma parede solta e veja a ponta dela no 3D: mostra o reboco, o tijolo e o reboco (é o corte da parede).
6. Exporte em SKP ou GLB e abra noutro programa: as esquinas estão rebocadas.

## 0.351 — Importar modelos 3D

Precisa de um modelo 3D de fora: um móvel descarregado do 3D Warehouse do SketchUp (`.skp`), um ficheiro do Rhino
(`.3dm`), ou um `.glb` / `.obj` / `.stl`. Também serve um ficheiro gravado pelo próprio ArqSynth BIM (0.348–0.350).

1. Abra um projeto com uma sala. Clique em **Início ▸ Importar modelo 3D…** (um cubo com uma seta a entrar) e escolha
   o ficheiro `.skp` de um móvel.
2. Abre-se a janela **Importar modelo 3D**:
   - em cima, o nome do ficheiro, os triângulos e os materiais;
   - **Entra como: Componente**; **Natureza: Mobiliário**; **Onde: Onde eu clicar**;
   - em **Tamanho**, as medidas do móvel em metros (por exemplo «2,10 m × 0,90 m × 0,80 m» para um sofá).

   Carregue em OK.
3. O balão diz «… está na biblioteca: clique onde o pôr». Leve o rato à planta ou ao 3D: vê-se a caixa do móvel.
   Carregue em Tab para o rodar 90° e clique: o móvel fica lá, **com as cores do SketchUp**. Clique noutro sítio para
   mais uma cópia; Esc acaba.
4. No **Navegador do Projeto ▸ Biblioteca ▸ Componentes** está o móvel, com as cópias. Clique com o botão direito ▸
   **Inserir outra cópia…** para pôr outra.
5. Importe outra vez, agora um `.obj` ou `.stl`. A janela mostra mais duas linhas:
   - **Unidade do ficheiro**, proposta pelo tamanho;
   - **Vertical**: Y para cima no OBJ, Z no STL.

   Mude a unidade (metros, centímetros, milímetros…) e veja o **Tamanho** mudar. Deixe a que dá o tamanho certo.
6. Importe um edifício (por exemplo um `.skp` ou `.3dm` do terreno ou dos vizinhos) com **Onde: Onde está no
   ficheiro**: fica nas coordenadas do ficheiro.
7. Importe o mesmo ficheiro com **Entra como: Esboço**: fica um esboço cinzento com as faces inteiras, sem triângulos.
   Use o Empurrar/Puxar numa face.
8. Do Rhino: um ficheiro com superfícies (não malhas) gravado sem as malhas de visualização diz, em cima na janela,
   quantas ficaram de fora. No Rhino, mostre o modelo em **Sombreado**, grave, e importe outra vez.
9. Escolha um ficheiro que não seja 3D (por exemplo um `.obj` vazio): o balão diz que não tem nada para trazer.
10. Ctrl+Z desfaz a importação de uma só vez.

## 0.350 — Exportar para o SketchUp e o Rhino

1. Abra uma casa com paredes, portas, janelas e laje. Clique em **Início ▸ Exportar modelo 3D…**, escolha **O modelo
   todo** e OK.
2. Na janela de gravar, em **Tipo**, escolha **SketchUp (\*.skp)** e grave. O balão diz «Modelo 3D gravado em …:
   N elementos».
3. Abra o `.skp` no SketchUp (duplo clique, ou Ficheiro ▸ Abrir). Se for o SketchUp 2021 ou mais recente, ele avisa que
   o ficheiro é de uma versão anterior e converte-o: aceite.
4. Veja:
   - no painel **Etiquetas** (Tags): uma etiqueta por pavimento e categoria, por exemplo «Térreo - Paredes». Desligue
     uma: essas peças desaparecem;
   - no **Estruturador** (Outliner): cada elemento é um grupo com o seu nome, por exemplo «Parede 1»;
   - as paredes têm as arestas de um desenho, sem os triângulos: uma fachada com uma janela é uma face com um furo;
   - o vidro é transparente; o reboco tem a cor do programa;
   - clique com o botão direito numa parede ▸ **Informação da entidade**: a etiqueta e o nome. Com a extensão
     «Attribute Inspector» (ou na consola Ruby: `Sketchup.active_model.selection[0].attribute_dictionary("ArqSynth").to_a`)
     aparecem o GlobalId, a classe IFC, o tipo, o pavimento e a categoria.
5. Meça a fachada com a fita métrica: as medidas são as do ArqSynth BIM.
6. Exporte outra vez e escolha **Rhino (\*.3dm)**. Abra-o no Rhino:
   - no painel **Camadas**: uma camada por pavimento e, dentro, uma por categoria («Paredes», «Lajes»…), cada uma na
     sua cor;
   - clique numa parede e abra **Propriedades ▸ Attribute User Text**: GlobalId, ifcClass, type, storey, category;
   - no modo **Renderizado** as peças têm as cores e o vidro transparente;
   - as unidades do documento são metros.

## 0.349 — OBJ e STL

O botão da 0.348 chama-se agora **Exportar modelo 3D…** (Início ▸ Exportar).

1. Abra uma casa com paredes, portas, janelas e laje. Clique em **Exportar modelo 3D…**, escolha **O modelo todo** e
   OK.
2. Na janela de gravar, em **Tipo**, escolha **Modelo 3D OBJ, com os materiais** e grave. Na mesma pasta ficam dois
   ficheiros: o `.obj` e o `.mtl` (os materiais).
3. Abra o `.obj` no SketchUp (Ficheiro ▸ Importar), no Blender (Ficheiro ▸ Importar ▸ Wavefront) ou noutro programa
   3D: cada elemento é um objeto com o nome «Térreo/Paredes/Parede_1»; as paredes têm a cor do reboco e o vidro é
   transparente.
4. Exporte outra vez e escolha **Impressão 3D STL**. O programa pergunta a escala: deixe **1:100** e OK. O balão diz
   «Maqueta gravada em … à escala 1:100, em milímetros».
5. Abra o `.stl` no programa da sua impressora (Cura, PrusaSlicer, Bambu Studio…): a casa aparece pousada no prato, à
   escala — 6 m de fachada são 60 mm.

## 0.348 — Exportar o modelo 3D em GLB

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Abra uma casa com paredes, portas, janelas e laje
(ou faça uma: Ctrl+N, o «Primeiro percurso» do GUIA).

1. Clique em **Início**. No painel **Exportar** há um botão novo, **Exportar modelo 3D (GLB)…** (um cubo com uma
   seta). Clique nele.
2. Escolha **O modelo todo** e OK. Escolha onde gravar e o nome. O balão diz «Modelo 3D gravado em …: N elementos,
   N triângulos, N MB».
3. Abra o ficheiro:
   - no **Blender** (Ficheiro ▸ Importar ▸ glTF 2.0); ou
   - na internet, num visualizador de glTF: por exemplo, abra `https://gltf-viewer.donmccurdy.com/` e arraste o
     ficheiro para lá.
4. No Blender, na lista de objetos, veja a árvore: o nome do modelo ▸ o pavimento ▸ Paredes, Lajes, Portas, Janelas
   ▸ cada elemento com o seu nome. As janelas têm vidro transparente e as paredes o reboco por fora.
5. Clique numa parede no Blender e veja as propriedades personalizadas: GlobalId, ifcClass, type, storey.
6. No ArqSynth BIM, escolha uma só parede e exporte outra vez com **Só a seleção**: o ficheiro leva só essa parede.
   Sem nada escolhido, o balão diz «Nada escolhido».
7. O mesmo botão está em **Render ▸ Apresentação**.

## 0.347 — O guia de todas as ferramentas

1. Abra o ficheiro **GUIA.md** (na pasta `C:\BIM`, ao lado deste). Comece pela secção «Antes de começar» e pelo
   «Primeiro percurso».
2. Escolha um separador no «Índice» e siga o seu «Para testar este separador». Para os pormenores de uma ferramenta,
   veja as secções do TESTAR que o guia indica.
3. No programa, passe o rato por cima de botões como **Início ▸ Abrir…**, **Estrutura ▸ Memória de cálculo…** ou
   **Visualizar ▸ Caixa de corte (3D)**: cada um mostra agora uma frase a dizer o que faz.
4. Carregue em F1 e, no separador **Procurar**, escreva «memória»: o comando aparece com a sua dica por baixo.

## 0.346 — A alvenaria por tipo de parede

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Pode continuar no projeto do teste 0.345 (a casa
com laje e o muro) ou fazer outro igual.

1. Clique em **Estrutura ▸ Cálculo ▸ Verificar EC2/EC6** e clique numa parede da casa. Na primeira nota lê-se
   «alvenaria à flexão (blocos cerâmicos, argamassa M5: a do projeto)». Feche.
2. Clique em **Gerenciar ▸ Tipos**. À esquerda escolha **Paredes** e clique em **Parede alvenaria 20 cm**.
3. Por baixo das camadas aparece o grupo **Alvenaria para o cálculo (EC6)**. A caixa **Alvenaria própria deste
   tipo** está desligada e os campos em cinzento mostram a alvenaria do projeto.
4. Ligue a caixa. Escolha **Alvenaria: blocos** = **De betão**, **Grupo** = **1**, **fb** = `15` e **Argamassa** =
   **M10**. Clique em **Aplicar** e depois em **Fechar**.
5. Volte a **Verificar EC2/EC6** e clique numa parede da casa. A nota diz agora «alvenaria à flexão (blocos de
   betão, argamassa M10: a do tipo)». Em cima, o resumo diz «fk = 7,31 N/mm²», o da alvenaria do tipo. Se tiver
   paredes de outro tipo (por exemplo um muro de 15 cm), o resumo mostra as duas: «fk = 3,66 a 7,31 N/mm²».
   Numa parede resistente, a primeira nota diz «alvenaria de blocos de betão do grupo 1 (a do tipo): fb = 15,0
   N/mm², argamassa M10 → fk = 7,31 N/mm²».
6. Em **Estrutura ▸ Mapas ▸ Memória de cálculo…**, no capítulo 2 aparece a alvenaria do projeto e a linha «O tipo
   «Parede alvenaria 20 cm», com alvenaria própria: …».
7. Grave (Ctrl+S), feche e abra o projeto: o tipo continua com a sua alvenaria.
8. Para voltar ao de antes: em **Gerenciar ▸ Tipos**, desligue a caixa e clique em **Aplicar**.

## 0.345 — As paredes de fachada à flexão pelo vento

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Crie um projeto novo (Ctrl+N).

1. Em **Arquitetura ▸ Parede**, com o tipo **Parede alvenaria 20 cm**, desenhe um retângulo de 6 × 4 m (clique, `6`
   Enter, `4` Enter, `6` Enter, clique no primeiro canto). Carregue em Esc.
2. Ponha uma porta e duas janelas numa das paredes compridas e uma laje por cima das paredes (**Estrutura ▸ Laje**,
   à cota do topo das paredes).
3. Desenhe, longe da casa, uma parede solta de 4 m (um muro de jardim), com o mesmo tipo.
4. Clique numa das paredes da casa: nas Propriedades, **Exterior** está ligado (o programa marca-o sozinho).
5. Clique em **Estrutura ▸ Cálculo ▸ Verificar EC2/EC6**. Aparecem as cinco paredes:
   - as quatro da casa estão **OK**; o que manda é o «efeito de arco vertical»;
   - o muro de jardim está em **Falha**: «apoiado só em baixo (em consola)».
6. Clique na parede com a porta e as janelas. Em baixo aparecem as notas:
   - a alvenaria à flexão (fxk1, fxk2, μ);
   - o vento na fachada, com o «× 1,38» do vento das janelas e portas;
   - a flexão do pano «apoiado nos quatro bordos» — «a flexão não chega sozinha»;
   - o efeito de arco, que passa.
7. Dê ao muro pilares nas pontas (**Estrutura ▸ Elementos ▸ Pilar**, um em cada ponta do muro) e clique em
   **Verificar outra vez**: o muro passa a «apoiado em baixo e nos dois lados (topo livre)», com um momento menor.
   Pode continuar a falhar, porque não tem laje em cima para fazer o arco.
8. Em **Estrutura ▸ Mapas ▸ Memória de cálculo…**, no capítulo 2 aparece a linha «Paredes de fachada à flexão pelo
   vento», e no capítulo 6 as paredes com as suas notas.

## 0.344 — Reabrir um modelo grande mais depressa

Não há nada de novo para clicar: os modelos grandes reabrem mais depressa.

1. Abra o ArqSynth BIM (**ArqSynth BIM.bat**) e abra um modelo grande seu, de preferência com milhares de elementos
   (ou o de ensaio: `C:\BIM\benchmark\modelos\edificio_grande.ifc`). A 1.ª vez demora o mesmo de sempre: o
   programa calcula as formas e guarda-as.
2. Feche o programa e abra-o outra vez. Abra o mesmo modelo (**Abrir…**, Ctrl+O). O edifício aparece cerca de
   duas vezes mais depressa do que na versão anterior; no de ensaio, em cerca de 1 s.
3. Rode a vista 3D com o rato: anda tão solto como antes.

## 0.343 — O render realista

Antes de testar, corra uma vez a preparação do Linux para instalar o motor novo (Mitsuba 3, cerca de 200 MB): no
menu Iniciar, abra **Ubuntu** e escreva `bash /mnt/c/BIM/scripts/wsl_setup.sh`, Enter (pede a palavra-passe do
Linux). Depois feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Crie um projeto novo (Ctrl+N).

**De dia, por fora**

1. Desenhe uma casa: **Arquitetura ▸ Parede**, um retângulo de 6 × 4 m (clique, `6` Enter, `4` Enter, `6` Enter,
   clique no primeiro canto), Esc. Ponha uma porta e duas janelas numa parede comprida e uma laje por cima
   (**Estrutura ▸ Laje**, à cota do topo das paredes).
2. Abra a vista **3D** e rode-a para ver a casa de frente, um pouco de cima.
3. Clique em **Render ▸ Render realista…** (o primeiro botão do painel Apresentação). Abre a janela de preparação.
4. Deixe **Tamanho** em **HD — 1280 px**, **Qualidade** em **Rascunho** e **Iluminação** em **Sol, céu e luminárias
   acesas**. Clique em **Renderizar**.
5. Abre a janela do render. Em baixo, a barra diz «passagem 1 de 8 · … amostras · 0:03». A imagem aparece e fica
   mais fina a cada passagem. Enquanto corre, pode mexer na vista 3D: o programa continua a responder.
6. No fim, a barra diz «Pronto: … amostras por píxel em …». Veem-se a casa com a sombra do sol no chão e o céu azul.
7. Clique em **Guardar imagem…**, escolha uma pasta e grave. Abra a imagem gravada.

**O acabamento de um material**

8. Clique em **Gerenciar ▸ Materiais…** e escolha **Reboco** na lista. Em **Superfície**, na linha **Acabamento
   (render)**, está **Pela categoria**. Escolha **Brilhante** e clique em **Aplicar**. Feche.
9. Repita os passos 3 e 4: as paredes têm agora brilhos do céu.
10. Volte a pôr o Reboco **Pela categoria** (passo 8).

**À noite, com as luminárias**

11. Na planta (F4), clique em **Arquitetura**, no painel **Salas e tetos**, no botão pequeno **Luminária**, e clique
    em dois sítios dentro da casa: ficam dois painéis 60 × 60 no teto. Carregue em Esc.
12. Volte à vista 3D. **Render ▸ Render realista…**, **Iluminação**: **Noite: só as luminárias**. Renderizar.
13. O céu fica azul-escuro, a casa às escuras e as janelas acesas em branco quente, com a luz a cair no chão.

**O sol do terreno, num dia e hora**

14. Clique em **Gerenciar ▸ Projeto ▸ Localização do terreno…** e escreva a latitude `38,72` e a longitude `-9,14` (Lisboa). OK.
15. **Render ▸ Render realista…**. Em **Sol**, escolha **O do terreno, num dia e hora**. Ficam ativos **Dia e hora**
    e o fuso (UTC 1,0 no verão). Escreva `21/06/2026 19:30`. Por baixo aparece onde fica o sol: «Sol a 288° do
    norte, 16° acima do horizonte».
16. Mude a hora para `23:00`: aparece «O sol está abaixo do horizonte: será de noite, só com as luminárias».
17. Volte às `19:30`, ponha **Iluminação** em **Sol e céu** e renderize: o sol baixo, as sombras compridas.

**Por dentro**

18. Na vista 3D, rode a vista (Orbitar) até olhar para a porta quase ao nível do chão e aproxime-se até ver o chão
    dentro da casa, pela porta. Clique em **Visualizar ▸ Câmara ▸ Posicionar câmara** e clique nesse chão, lá
    dentro: a câmara fica de pé dentro da casa e a ferramenta passa a **Olhar em volta**. Arraste para virar a
    cabeça até ver uma janela.
19. **Render ▸ Render realista…**, **Qualidade** **Normal**, **Sol, céu e luminárias acesas**. Renderizar. O sol
    entra pelas janelas e desenha manchas no chão. As paredes ficam lisas, sem grão.
20. Para ver o efeito do filtro, repita com **Limpar o grão (filtro)** desligado: a mesma imagem com grão.
21. **Exposição**: com `+1,0 EV` a imagem sai mais clara (o dobro da luz), com `-1,0 EV` mais escura.
22. Num render comprido (qualidade **Alta**, 4K), clique em **Parar** a meio: o render acaba logo e a imagem fica
    como estava. Pode guardá-la na mesma.

## 0.342 — As paredes de betão armado pelo Eurocódigo 2

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Crie um projeto novo (Ctrl+N).

1. Em **Arquitetura ▸ Parede**, na barra contextual, escolha o tipo **Parede de betão armado 20 cm** e desenhe um
   retângulo de 6 × 4 m (clique, `6` Enter, `4` Enter, `6` Enter, clique no primeiro canto). Carregue em Esc.
2. Carregue em Espaço e clique numa parede: nas Propriedades, **Estrutural (resistente)** já está ligada (numa
   parede de betão não é preciso ligá-la à mão).
3. Em **Estrutura ▸ Sapata**, clique em cada parede: fica uma sapata corrida debaixo de cada uma.
4. Ponha uma porta numa das paredes compridas e uma laje por cima das paredes (**Estrutura ▸ Laje**, à cota do topo
   das paredes).
5. Clique em **Estrutura ▸ Cálculo ▸ Verificar EC2/EC6**. As quatro paredes estão **OK**, cada uma com as suas
   armaduras na coluna «Armadura» (por exemplo «vert. Ø8//0,25 · horiz. Ø8//0,40 (2 faces)»: os mínimos, numa casa
   leve). Clique numa parede: por baixo aparecem as notas (esbelteza, compressão no topo, a meio e na base, armadura
   vertical, corte no plano, armadura horizontal).
6. Clique em **Pôr as armaduras no modelo**. O balão diz quantos elementos e varões. Na coluna «No modelo», as
   paredes passam a dizer «estas».
7. Feche a janela e, na vista 3D, ponha o **Estilo visual** em **Raio-X**: veem-se os varões dentro das paredes,
   interrompidos na porta, com os varões de reforço à volta dela e os arranques a descer para as sapatas.
8. No navegador, em **Armaduras**, faça duplo clique em **Parede 1**: o alçado armado da parede, com a malha, os
   reforços da porta, as cotas e a lista das posições ao lado.
9. Em **Estrutura ▸ Mapas ▸ Lista de armaduras…**: aparecem as posições das paredes (vertical, horizontal, reforço
   dos vãos). Em **Quantidades da estrutura…**: as paredes de betão com o betão, a cofragem e o aço.

## 0.341 — O fundo escuro nas vistas

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Abra uma casa com paredes, portas, janelas, uma sala,
eixos e cotas (por exemplo a dos testes da alvenaria), e abra a planta do piso (F4).

1. Clique em **Visualizar**. No painel **Tema** há agora um terceiro botão pequeno, **Vistas escuras** (um quadro azul
   com uma planta amarela). Se a janela for estreita, está dentro do botão **Tema ▾**.
2. Clique em **Vistas escuras**. Na hora:
   - o fundo da planta fica escuro;
   - as paredes cortadas, com a sua trama, as portas, as cotas, os números e o nome da sala ficam claros;
   - os eixos ficam azul-claro e a sala num cinzento quente.

   A interface continua como estava: as vistas escuras não dependem do tema da interface.
3. Clique num elemento: fica azul, como sempre.
4. Abra o alçado **Sul** (no navegador, **Alçados ▸ Sul**). As paredes ficam escuras com os contornos claros. O vidro
   das janelas continua azul e a porta de madeira continua castanha.
5. Abra a vista **3D**. O fundo e a grelha do chão estão escuros, mas a casa tem as cores de sempre, com as arestas
   escuras.
6. Ainda no 3D, nas Propriedades (com nada escolhido), mude o **Estilo visual**:
   - em **Linhas escondidas**: a casa branca com traços escuros;
   - em **Arame**: só os traços, claros sobre o fundo escuro;
   - volte a **Sombreado**.
7. Volte à planta. Em **Início ▸ Exportar ▸ Imagem da vista**, escolha o fundo **Branco** e grave. Abra a imagem: está
   como em papel (fundo branco, traços pretos), e a planta no ecrã continua escura.
8. Abra uma folha, se tiver: continua em papel branco.
9. Feche o programa e abra-o outra vez: as vistas continuam escuras. Clique outra vez em **Vistas escuras** para
   voltar às claras.

## 0.340 — A revisão do tema escuro

Feche o ArqSynth BIM e abra-o outra vez, **no tema claro** (se estiver no escuro, mude para o claro, feche e abra).

1. Abra um projeto com paredes e clique numa parede.
2. Mude para o escuro sem fechar: **Visualizar ▸ Tema ▸ Tema escuro**.
3. Olhe para o rodapé, em baixo: **Pavimento: Térreo (0,00 m)**, as unidades (**m**) e o modo das medidas
   (**Automática**) leem-se em letra clara. Antes ficavam pretos sobre o escuro.
4. No painel de propriedades, o título por cima («Parede alvenaria…» ou o nome do que estiver escolhido) lê-se em
   branco.
5. Clique em **Visualizar ▸ Estilos gráficos**: nos botões de cor, o código da cor (#ffffff, #b9b9b9…) aparece a preto
   nas cores claras e a branco nas escuras, sempre legível. Feche.

## 0.339 — As janelas por cima, no tema escuro

Feche o ArqSynth BIM e abra-o outra vez. Ponha o tema escuro (**Visualizar ▸ Tema ▸ Tema escuro**).

1. Clique em **Arquitetura ▸ Caixilho Studio**. Abre escuro, como o protótipo: a janela com as cotas a âmbar, os
   puxadores a âmbar e o botão **Inserir no modelo** a âmbar em baixo, à direita. Clique em **Cancelar**.
2. Clique em **Gerenciar ▸ Materiais**: a lista e os campos estão escuros; as amostras de cada material e os quadrados
   das cores continuam com as suas cores. A frase azul em baixo («Usado em …») lê-se bem. Feche.
3. Clique em **Gerenciar ▸ Tipos**: escuro, com a tabela das camadas e os dados IFC legíveis. Feche.
4. Clique em **Estrutura ▸ Cálculo ▸ Ações e materiais…**: escuro; a nota cinzenta em baixo lê-se bem. Cancele.
5. Ponha o tema claro (**Visualizar ▸ Tema ▸ Tema claro**) e abra outra vez o Caixilho Studio: está claro, como
   antes.

## 0.338 — O tema escuro

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Abra um projeto qualquer com algumas paredes.

1. Clique no separador **Visualizar** do cabeçalho. Na fita, à direita, há um painel novo, **Tema**, com dois botões
   pequenos: **Tema claro** (um sol) e **Tema escuro** (uma lua). Se a janela for estreita, o painel aparece
   fechado num botão **Tema ▾**: clique nele e escolha.
2. Clique em **Tema escuro**. Na hora, sem reabrir, a janela fica escura: o cabeçalho, a fita, a barra contextual (por
   baixo da fita), o navegador à esquerda, as propriedades à direita e o rodapé. O separador da disciplina ativa fica
   a âmbar. Por cima da vista aparece o balão «Tema escuro. Fica assim neste computador…».
3. Olhe para os ícones da fita: os traços passaram a claros e os fundos a cinzento-escuro; o azul e as cores (portas,
   telhas, tijolo) ficam iguais. A vista 3D continua com o fundo claro, e as plantas e folhas em papel branco.
4. Clique numa parede: o painel de propriedades mostra-a com as cores do escuro, e os grupos (Identificação, …) têm
   uma faixa cinzento-escura.
5. Escolha a ferramenta **Arquitetura ▸ Parede**: a barra contextual mostra os campos (tipo, altura…) escuros, com o
   texto claro. Carregue em Esc.
6. Carregue em **F1**: o painel da Ajuda também está escuro, com os ícones claros.
7. Feche o programa e abra-o outra vez: arranca já no tema escuro.
8. Em baixo, à esquerda, na barra dos módulos, clique na roda dentada: o menu tem **Tema claro** e **Tema escuro**.
   Escolha **Tema claro**: tudo volta a ser como era.

Nota: algumas janelas que se abrem por cima (Caixilho Studio, editor de materiais, de padrões, de tipos, verificação
da estrutura) ainda têm partes claras no tema escuro — são o passo seguinte.

## 0.337 — A verificação das paredes de alvenaria (Eurocódigo 6)

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**). Abra a casa dos testes 0.335 e 0.336 (quatro paredes
resistentes de 20 cm, 6 × 4 m, com sapatas corridas e uma laje por cima). Se tiver acrescentado a viga do passo 4 do
teste 0.336, apague-a.

1. Clique em **Estrutura ▸ Cálculo ▸ Ações e materiais…**. No fim da coluna da esquerda há cinco campos novos:
   **Alvenaria: blocos** («Cerâmicos (tijolo)»), **Grupo dos blocos (EC6)** («2»), **Resistência dos blocos fb**
   («10,00 N/mm²»), **Argamassa** («M5») e **γM da alvenaria** («2,50»).
2. Abra a lista **Alvenaria: blocos** e veja as quatro escolhas (cerâmicos, de betão, sílico-calcários, betão
   celular). Deixe «Cerâmicos (tijolo)». Carregue em **OK**.
3. Clique em **Estrutura ▸ Cálculo ▸ Verificar EC2/EC6**. A janela chama-se agora «Verificação EC2 / EC6 e
   armaduras». Há uma linha para cada parede («Parede 1» a «Parede 4»), todas **OK**, com a utilização (entre 15 e
   35 %), «—» na coluna das armaduras, e na última coluna a verificação mais apertada (nesta casa, «corte no plano:
   VEd = … ≤ VRd = …»).
4. O texto de cima termina com «4 paredes de alvenaria verificadas pelo EC6 (fk = 3,66 N/mm²).»
5. Clique na linha de uma parede. Por baixo aparecem as notas todas: a alvenaria (fb, argamassa, fk, fd), a esbelteza
   («13,1 (máximo 27,0)»: a parede tem 20 cm, mas só o bloco de 16 cm conta), a compressão **no topo**, **a meio** e
   **na base** (cada uma com NEd ≤ NRd, o Φ e a excentricidade) e o **corte no plano**.
6. Feche a janela. Volte a **Ações e materiais…**, mude **Resistência dos blocos fb** para 15 e **Argamassa** para
   «M10» e carregue em **OK**. Repita o passo 3: o resumo diz agora «fk = 5,98 N/mm²», as utilizações descem um pouco
   e as notas dizem «fb = 15,0 N/mm², argamassa M10».
7. Para ver uma parede a falhar: volte a **Ações e materiais…** e ponha **Resistência dos blocos fb** em 1,00 e a
   **Argamassa** em «M2.5». Repita o passo 3: as duas paredes curtas (4 m) ficam **Falha**, e a última coluna diz
   porquê: «corte no plano: VEd = 20,6 kN > VRd = … 16,6 kN …» (o sinal «>» diz que não chega). As compridas passam,
   perto do limite (cerca de 78 %). Volte depois a pôr 10 e M5.
8. Clique em **Estrutura ▸ Mapas ▸ Memória de cálculo…** e guarde a página. Abra-a: nos materiais
   aparece «Alvenaria resistente: …» com o fk e o fd; na análise, uma linha por parede; na secção 6, «Verificação pelos
   Eurocódigos 2 e 6», cada parede com as suas notas; e, nas notas do fim, o método das paredes de alvenaria.

## 0.336 — As cargas nas paredes resistentes

Continue com a casa do teste 0.335 (quatro paredes resistentes com sapatas corridas).

1. Ponha uma laje por cima das paredes: **Estrutura ▸ Laje**, desenhe um retângulo à volta das quatro paredes, no
   piso de cima (ou com o tipo de laje de 15 cm, à cota do topo das paredes).
2. Clique em **Estrutura ▸ Cálculo ▸ Analisar a estrutura…**. O balão diz «Estrutura de paredes resistentes: as
   cargas de 4 paredes calculadas». A lista tem uma linha por parede («Parede 1 (parede)»), com a compressão por metro
   na base (N, com 1,35G+1,50Q e só com G) e a maior força horizontal que lhe cabe (V), e de onde vem (por exemplo
   «horizontal: WX»).
3. Passe o rato sobre uma linha: a dica explica cada número. As duas paredes compridas dividem entre si o vento ao
   longo delas; as curtas, o da outra direção.
4. Acrescente uma viga de uma parede comprida à outra, a meio (**Estrutura ▸ Viga**, à cota do topo das paredes), e
   analise outra vez: aparece a viga na lista, e as paredes onde ela se apoia recebem a sua reação (N maior nessas
   duas).

## 0.335 — Paredes resistentes no modelo analítico

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N). Em **Arquitetura ▸ Parede**, desenhe um retângulo de quatro paredes (por exemplo
   6 × 4 m: clique, `6` Enter, `4` Enter, `6` Enter e clique no primeiro canto). Carregue em Esc.
2. Carregue na barra de **Espaço** (Selecionar), clique numa parede e, com **Shift**, nas outras três. Nas
   **Propriedades**, procure **Estrutural (resistente)** e ligue a caixa: as quatro ficam resistentes.
3. Clique em **Estrutura ▸ Cálculo ▸ Modelo analítico e verificação…**. O balão diz «Modelo analítico feito: 0
   barras, 4 paredes resistentes…» e a lista tem quatro avisos «parede resistente na cota da fundação sem sapata
   corrida». Na vista, o modelo analítico mostra as quatro paredes (retângulos). Feche a lista.
4. Em **Estrutura ▸ Sapata**, clique em cada parede: fica uma sapata corrida debaixo de cada uma. Repita o passo 3:
   os avisos desaparecem.
5. Desenhe uma parede sozinha no piso de cima, num sítio sem nada por baixo, marque-a resistente e repita o passo 3:
   aparece o erro «parede resistente suspensa».

## 0.334 — A função de cada camada no tipo

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N). Desenhe uma parede de 6 m (**Arquitetura ▸ Parede**, clique, rato para a direita,
   `6`, Enter, Esc) e outra que encoste a meio dela, de lado (um **T**): comece no meio da primeira e suba 3 m.
2. Abra a planta (**F4**) e aproxime-se do encontro: o bloco da parede que encosta entra pelo reboco da outra até ao
   bloco (como até aqui).
3. Abra **Gerenciar ▸ Tipos**, escolha **Parede alvenaria 20 cm**. A tabela das camadas tem agora a coluna
   **Função**, com «Automática» em todas.
4. Experimente: ponha as três camadas em **Estrutura [1]** e clique em **Aplicar**. Na planta, o bloco da parede que
   encosta deixa de entrar pelo reboco da outra e pára na face dela: agora todas as camadas são igualmente fortes, e
   nenhuma atravessa as do outro.
5. Volte ao editor, ponha as funções «a sério» — **Reboco: Acabamento 1 [4]**, **Bloco: Estrutura [1]**, **Reboco:
   Acabamento 2 [5]** — e Aplicar: o encontro fica como no passo 2.
6. **Ctrl+Z** volta atrás em cada passo. Grave o projeto, feche-o e abra-o: as funções continuam lá.

## 0.333 — Desunir e Unir geometria

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N). Em **Arquitetura**, clique em **Parede** e desenhe duas paredes seguidas na mesma
   linha: clique no chão, rato para a direita, `4` e Enter; outra vez o rato para a direita, `4` e Enter. Carregue em
   Esc.
2. Abra a planta (**F4**) e aproxime-se do encontro das duas paredes (a meio): não há linha entre elas, o corte é
   contínuo.
3. Clique em **Modelagem ▸ Desunir geometria** (painel Modificar). Clique na primeira parede e depois na segunda. O
   balão diz «… desunidos: a linha entre eles vê-se no corte e nas vistas».
4. No encontro aparece agora uma **linha** a separar as duas paredes. Abra a vista **3D**: a aresta vertical entre
   elas também voltou.
5. Volte à planta e use **Início ▸ Vista em PDF**: no PDF, a linha entre as duas paredes está desenhada.
6. Clique em **Modelagem ▸ Unir geometria**, depois numa parede e na outra: a linha desaparece outra vez. **Ctrl+Z**
   volta a desuni-las.
7. Num canto (duas paredes em L, com reboco): desuna-as e veja na planta que o reboco de uma deixa de dobrar a
   esquina da outra, com a linha entre as duas.

## 0.332 — Alinhar os padrões numa face

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N). Em **Arquitetura**, desenhe uma parede de 4 m (**Parede**, clique no chão, rato
   para a direita, `4`, Enter, Esc).
2. Dê-lhe azulejo para ver o padrão: **Espaço** (Selecionar), clique na parede, **Visualizar ▸ Tramas por elemento**;
   em **Superfície projetada ▸ Primeiro plano** escolha **Ladrilho 30×30** e clique em **OK**. Clique fora da
   parede. (Uma parede com um material de azulejo ou tijolo já mostra o seu, sem este passo.)
3. Ponha a parede de frente: no cubo de vistas, clique em **FRENTE**, e aproxime com a roda do rato.
4. Clique em **Modelagem ▸ Alinhar**. Clique na **aresta de cima da parede**, num sítio que não seja o meio: fica uma
   linha comprida sobre ela (a referência).
5. Passe o rato devagar sobre as juntas horizontais do ladrilho: a junta debaixo do rato acende a **laranja** e a dica
   diz «Alinhar o padrão: mover …». Clique numa delas.
6. O ladrilho sobe ou desce até uma fiada ficar justa com o topo da parede; o balão diz «Padrão de «Parede 1»
   alinhado». Agora as juntas verticais: clique com o **botão direito** (outra referência), clique na **aresta
   vertical da ponta da parede** e depois numa junta vertical: as juntas verticais acertam com a ponta.
7. Carregue em Esc duas vezes, escolha **Mover** e mova a parede: o ladrilho vai com ela (não «escorrega»).
8. **Ctrl+Z** desfaz cada passo. Para tirar tudo de uma vez: com a parede selecionada, **Visualizar ▸ Repor
   padrões** (ou **botão direito ▸ Repor os padrões alinhados**).

## 0.331 — Tramas por elemento numa vista

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N). Em **Arquitetura**, clique em **Parede** e desenhe duas paredes seguidas: clique no
   chão, rato para a direita, escreva `5` e Enter; rato para cima, `4` e Enter. Carregue em Esc.
2. Abra a planta (**F4**). Carregue na barra de **Espaço** (Selecionar) e clique numa das paredes.
3. Clique no separador **Visualizar** e, no painel **Aspeto**, no botão **Tramas por elemento**. Abre-se a janela
   «Tramas por elemento», que diz «Paredes × 1 — só na vista «Planta — Térreo»».
4. Em **Corte**, clique no botão do **Primeiro plano** (diz «Nenhum»), escolha **Cheio** e confirme; depois, no
   botão de cor ao lado, escolha um cinzento escuro. Clique em **OK**.
5. Clique fora das paredes: na planta, essa parede está cortada a cinzento escuro cheio; a outra continua com a
   trama dos seus materiais. O balão diz «Tramas próprias para 1 elemento(s) na vista «Planta — Térreo»».
6. Abra a vista **3D** (separador **3D** por cima da vista) e volte à planta: a trama só está na planta.
7. Na planta, clique com o **botão direito** num sítio vazio (com o Selecionar): o menu tem **Tramas por elemento…**.
8. Selecione outra vez a parede, abra **Tramas por elemento** e clique em **Repor**: volta à trama dos materiais.
   Carregue em **Ctrl+Z**: volta o cinzento; **Ctrl+Y** tira-o outra vez.
9. Para a superfície: num alçado (no Navegador do Projeto, **Alçados ▸ Sul**), selecione uma parede e dê-lhe em
   **Superfície projetada** um padrão de tijolo: vê-se o tijolo nessa parede, só nesse alçado. **Início ▸ Vista em
   PDF** mostra-o também no papel.

## 0.330 — Botões e janelas em português de Portugal

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Desenhe uma parede qualquer e carregue em **Ctrl+N** (projeto novo): a pergunta tem os botões **Guardar**, **Não
   guardar** e **Cancelar**. Clique em **Cancelar**.
2. Clique em **Render ▸ Imagem da vista** e em **Exportar…**: a janela de gravar diz **Procurar em**, **Nome do
   ficheiro**, **Ficheiros do tipo** e tem os botões **Guardar** e **Cancelar**; as colunas são **Nome, Tamanho,
   Tipo, Data de modificação**. Clique em **Cancelar**.
3. Clique com o botão direito dentro de uma caixa de texto (por exemplo a altura de uma parede nas Propriedades): o
   menu diz **Desfazer, Refazer, Cortar, Copiar, Colar, Eliminar, Selecionar tudo**.
4. Abra **Gerenciar ▸ Materiais**, escolha um material e, em **Superfície**, clique no botão de **Cor de
   sombreamento** (o que mostra o código da cor, como #c8c8c8): a janela das cores diz **Cores básicas**, **Tirar cor
   do ecrã**, **Vermelho, Verde, Azul** e tem **OK** e **Cancelar**. Clique em **Cancelar**.

## 0.329 — Exportar a vista em imagem

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Abra um projeto com um edifício (por exemplo `C:\BIM\exemplos\casa_exemplo.ifc`, Ctrl+O). Na vista 3D, rode e
   aproxime até gostar do enquadramento. Clique numa parede, para a deixar selecionada (fica azul).
2. Clique no separador **Render** (o último, em cima) e no botão **Imagem da vista** (o primeiro do painel
   Apresentação).
3. Abre-se a janela **Exportar imagem da vista**. Em **Tamanho**, escolha **4K — 3840 px**: a linha de baixo diz o
   tamanho da imagem (3840 × a altura que corresponde à forma da sua vista). Em **Fundo**, deixe **Como a vista (céu
   claro)**. Clique em **Exportar…**.
4. Na janela de gravar, o nome proposto é o do projeto e da vista («casa_exemplo - 3D.png»). Escolha a pasta (por
   exemplo o Ambiente de trabalho) e clique em **Guardar** (ou **Save**). Por cima da vista aparece «Imagem gravada
   em … (3840 × … px)».
5. Abra a imagem no Windows (duplo clique no ficheiro): é a vista que tinha no ecrã, mais nítida, **sem** a parede
   azul da seleção, sem a grelha do chão nem o cubo de vistas. No programa, a parede continua selecionada.
6. Abra a planta (F4) e clique outra vez em **Render ▸ Imagem da vista**: agora o **Fundo** proposto é **Branco**.
   Escolha **Folha A3 deitada, a 300 ppp**, clique em **Exportar…** e grave. A imagem é a planta com as tramas das
   paredes e as marcas dos alçados, sobre branco.
7. Volte à vista 3D (o separador **3D** por cima da vista), exporte outra vez com **Fundo: Transparente (só em
   PNG)** e grave como PNG: ao pôr a imagem num documento (Word, PowerPoint) ou num programa de imagem, só se vê o
   edifício, sem fundo.
8. O mesmo botão está também em **Início ▸ Exportar** (ao lado de «Vista em PDF» e «Vista em DXF»).

## 0.328 — Reabrir um modelo grande sem a janela parar

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Abra um projeto grande que já tenha aberto antes (Ctrl+O). Para ensaio há `C:\BIM\benchmark\modelos\edificio_grande.ifc`
   (a 1.ª vez demora uns 16 s a calcular as formas; feche e volte a abri-lo para o passo seguinte).
2. Ao abri-lo outra vez, o edifício aparece quase de imediato e vai-se completando em menos de um segundo, aos
   bocados; durante isso pode mexer o rato e a janela responde (antes ficava parada mais de um segundo).

## 0.327 — A janela de Ajuda (F1)

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N). Carregue em **W** (ferramenta Parede) e depois em **F1**.
2. À direita, ao lado das Propriedades, abre-se o painel **Ajuda** no separador **Ferramenta**: «Parede», «Na fita:
   Arquitetura ▸ Paredes», o que fazer agora e as teclas da parede. Deixe-o aberto e carregue em **R** (Retângulo):
   o painel passa a falar do Retângulo.
3. Clique no separador **Procurar** e escreva `pilares`: aparece primeiro «Pilares na grelha — Estrutura ▸ Grelha»
   (e outros a seguir). Escolha-o e clique em **Mostrar onde está**: a fita passa ao separador **Estrutura** e o botão
   **Pilares na grelha** fica amarelo por um momento.
4. Clique em **Usar**: o comando corre (aqui diz que ainda não há eixos e oferece **Gerar eixos…**).
5. Clique no separador **Primeiros passos**: dez passos para uma casa. Clique em **Mostrar onde está** no primeiro:
   a fita passa à **Arquitetura** e o botão **Parede** acende.
6. Clique no separador **Teclas** para ver a lista. Para voltar às Propriedades, clique no separador
   **Propriedades** por baixo do painel (ou feche a Ajuda no × do painel).

## 0.326 — Copiar, Matriz e copiar-colar

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N). Em **Arquitetura**, clique em **Parede** e desenhe uma parede de 4 m (clique no
   chão, rato para a direita, `4`, Enter). Carregue em Esc e depois na barra de **Espaço** (Selecionar).
2. Clique na parede para a selecionar. No separador **Modelagem**, painel **Modificar**, clique em **Copiar**.
3. Clique num ponto do chão perto da parede (o ponto de base), leve o rato para a frente (afastando-se da parede),
   escreva `3` e Enter: aparece uma cópia a 3 m e a parede original fica onde estava. Carregue em Ctrl+Z.
4. Selecione outra vez a parede e clique em **Matriz** (no mesmo painel). Na barra de cima, em **Cópias**, escolha
   `4`. Clique num ponto do chão, leve o rato para a frente, escreva `2` e Enter: quatro cópias, a 2, 4, 6 e 8 m.
   Carregue em Esc e em Ctrl+Z.
5. Carregue na barra de **Espaço**, clique na parede e carregue em **Ctrl+C** (o balão diz «1 elemento(s)
   copiado(s)…»).
6. Carregue em **Ctrl+V**: uma cópia da parede segue o rato. Clique num ponto do chão: fica lá. Carregue em Esc.
7. Em **Gerenciar ▸ Pavimentos**, clique em **Novo pavimento**. Volte a selecionar a parede do Térreo (no painel
   **Navegador do Projeto** ou clicando nela) e carregue em **Ctrl+C** e depois **Ctrl+Shift+V**: na janela que abre,
   marque o pavimento novo e OK — a parede aparece por cima, no mesmo sítio.

## 0.325 — Pequenos defeitos

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N). Em **Arquitetura**, clique em **Parede** e desenhe uma parede de 5 m (clique no
   chão, rato para a direita, `5`, Enter). Carregue em Esc e depois na barra de **Espaço** (Selecionar). Clique num
   sítio vazio do chão.
2. Carregue na tecla **Delete**: o balão verde pede «Clique no que quer apagar». Clique na parede e carregue em
   **Delete** outra vez: a parede é apagada. Carregue em Ctrl+Z para a ter de volta.
3. Em **Gerenciar ▸ Pavimentos**, clique em **Pavimento acima** (ou carregue em Page Up): o balão diz «Este é o
   pavimento mais alto» e tem o botão **Novo pavimento**.
4. Em **Estrutura ▸ Automático**, clique em **Sapatas sob pilares**: «Não há pilares neste pavimento», com o botão
   **Pilar**.
5. Em **Arquitetura ▸ Vãos**, clique em **Numerar vãos** (ainda não há portas nem janelas): o balão diz que não há
   vãos. Carregue em **Ctrl+Z**: a parede desaparece — o Ctrl+Z desfez a parede, e não um passo vazio do Numerar
   vãos (antes era preciso carregar duas vezes).

## 0.324 — O que falta, com um botão

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N).
2. Em **Estrutura ▸ Grelha**, clique em **Pilares na grelha**: o balão âmbar diz «Ainda não há eixos…» e tem o botão
   **Gerar eixos…**. Clique nele: abre a janela para gerar os eixos. Gere-os (OK) e clique outra vez em **Pilares na
   grelha**: os pilares aparecem nos cruzamentos.
3. Em **Instalações ▸ Eletricidade**, clique em **Propor elétrica** (no projeto sem salas): o balão tem o botão
   **Sala**. Clique nele: a ferramenta Sala fica ativa. Carregue em Esc.
4. Em **Terreno ▸ Plataformas**, clique em **Plataforma**: o balão diz para fazer primeiro o terreno e tem o botão
   **Terreno por pontos**. Clique nele: a ferramenta Terreno fica ativa. Carregue em Esc.

## 0.323 — Cota, Desenho 2D e Pormenor abrem a planta

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N). Em **Arquitetura**, clique em **Parede** e desenhe uma parede de 5 m: clique num
   ponto do chão, leve o rato para a direita, escreva `5` e Enter. Carregue em Esc.
2. Confirme que está na vista **3D** (carregue em F8 se não estiver).
3. No separador **Anotar**, clique em **Cota**: a vista passa sozinha à planta do **Térreo**, e o balão diz «Isto
   faz-se numa planta, num corte ou num alçado: abri a planta «Térreo»», seguido do primeiro passo da cota.
4. Clique num canto da parede, no outro canto e, por fim, um pouco abaixo da parede: a cota fica feita na planta.
   Carregue em Esc.
5. Carregue em **F8** (3D) e, em **Anotar**, clique em **Desenho 2D**: o mesmo — abre a planta e pode desenhar.
   Carregue em Esc.
6. Já na planta, clique outra vez em **Cota**: a vista não muda e o balão mostra só o passo da cota.

## 0.322 — Os comandos pedem o que lhes falta

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

Preparar:
1. Crie um projeto novo (Ctrl+N).
2. No separador **Arquitetura**, clique em **Parede**. Desenhe uma sala de 6 × 4 m: clique num ponto do chão, leve o
   rato para a direita, escreva `6` e Enter; para cima, `4` e Enter; para a esquerda, `6` e Enter; e clique no
   primeiro ponto para fechar. Carregue em Esc.
3. Ainda na **Arquitetura**, clique em **Laje** e faça uma laje por cima: clique num canto do topo das paredes e no
   canto oposto (a laje fica à cota do topo). Carregue em Esc e depois na barra de **Espaço** (Selecionar).
4. Clique num sítio vazio do chão, para não ficar nada selecionado.

Ligar o topo (como no Revit: a parede, o botão, a laje):
5. Clique numa parede: aparece o separador verde **Modificar | Paredes**.
6. Clique em **Ligar o topo**: aparece um balão verde no cimo da vista, «Agora clique na laje ou cobertura a que o
   topo se liga».
7. Clique na laje: a parede fica ligada a ela (balão azul: «1 elemento(s) ligados pelo topo…»).

Escolher vários sem selecionar antes:
8. Carregue em **Esc** (a seleção limpa-se). No separador **Modelagem**, painel **Criar**, clique em **Fazer grupo**.
9. O balão verde diz «Clique nos elementos BIM do grupo» e, por baixo, «Escolhidos: 0».
10. Clique numa parede: fica azul e o balão diz «Escolhidos: 1». Clique noutra parede: «Escolhidos: 2». Clique outra
    vez na primeira: sai («Escolhidos: 1»). Clique nela de novo: volta.
11. Carregue em **Enter** (ou no **botão direito** do rato): pede o nome do grupo. Clique em OK: o grupo fica feito.

Um elemento que não serve:
12. Carregue em **Esc**. Em **Modelagem ▸ Criar**, clique em **Fazer componente**: o balão pede «Clique nos volumes de
    esboço do componente».
13. Clique numa parede: não entra, e o balão diz por um momento «Esse elemento não serve para «Criar componente»».
    Carregue em **Esc**: «Criar componente cancelado».

Espelhar sem selecionar antes:
14. Em **Modelagem ▸ Modificar**, clique em **Espelhar**: o balão verde pede «Clique no que quer espelhar».
15. Clique numa parede e carregue em **Enter**: a ferramenta Espelhar começa sobre essa parede. Carregue em Esc.

Desistir:
16. Clique numa parede e, no separador verde, em **Juntar paredes**: o balão pede as duas paredes e já conta
    «Escolhidos: 1». Carregue em **Esc**: «Juntar paredes cancelado», e a parede continua selecionada.

## 0.321 — Os avisos num balão por cima da vista

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

Um aviso:
1. Crie um projeto novo (Ctrl+N).
2. Clique no separador **Estrutura** (em cima, na barra azul-escura).
3. No painel **Grelha**, clique em **Pilares na grelha**.
4. No cimo da vista 3D, ao meio, aparece um balão cor de âmbar com o triângulo ⚠: «Ainda não há eixos: desenhe-os
   (ferramenta Eixos) ou gere-os (BIM ▸ Gerar eixos…)». O texto está todo lá.
5. Clique em qualquer sítio da vista 3D: o balão desaparece.

A dica de uma ferramenta:
6. Clique no separador **Anotar**.
7. No painel **Cotas**, clique em **Cota**.
8. Aparece um balão branco com o ícone e o nome **Cota** e o primeiro passo: «Abra primeiro uma planta (F4), um corte
   ou um alçado — a cota fica nessa vista». Em baixo, no rodapé, à esquerda, continua o mesmo passo. Se estiver
   cortado, pare o rato em cima dele para o ler inteiro.
9. Carregue em **Esc**: o balão desaparece.
10. Clique no separador **Arquitetura** e em **Parede**: o balão diz «Parede» e o primeiro passo. Clique num ponto do
    chão: o balão desaparece e a parede começa como sempre. Carregue em Esc.

O que um comando fez:
11. Ainda no 3D, com a ferramenta Parede, desenhe uma parede: clique num ponto do chão, leve o rato para a direita,
    escreva `4` e Enter. Carregue em Esc e depois na barra de **Espaço** (ferramenta Selecionar).
12. Clique na parede para a selecionar. Aparece o separador verde **Modificar | Paredes**: clique em **Virar a
    parede**.
13. Aparece um balão azul com o ⓘ: «1 parede(s) viradas: as camadas trocaram de lado. Ctrl+Z desfaz.». Não toque em
    nada: ao fim de uns segundos sai sozinho.

## 0.320 — Junção automática pelo material

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

No corte (planta):
1. Crie um projeto novo (Ctrl+N).
2. No separador **Arquitetura**, clique em **Parede**. Na barra de cima escolha o tipo **Parede alvenaria 20 cm**.
3. Desenhe uma sala de 6 × 4 m: clique num ponto do chão, leve o rato para a direita, escreva `6` e Enter; para
   cima, `4` e Enter; para a esquerda, `6` e Enter; e clique no primeiro ponto para fechar. Carregue em Esc.
4. Desenhe uma parede a meio da sala, de cima a baixo: clique no meio da parede de baixo e no meio da parede de
   cima. Carregue em Esc.
5. Carregue em **F4** (planta) e aproxime-se de um canto com a roda do rato: o bloco das duas paredes é uma peça só,
   o reboco de fora dobra a esquina por fora e o de dentro por dentro, sem linha entre as paredes.
6. Aproxime-se do sítio onde a parede do meio encosta à de baixo: o bloco dela entra no bloco da outra e o reboco de
   cada sala dá a volta. Não há linha a atravessar a parede de baixo.
7. Clique em **Ficheiro ▸ Exportar PDF…** (ou ponha a planta numa folha) e abra o PDF: o mesmo, com a linha grossa à
   volta das paredes, por fora e por dentro de cada sala.

Nas vistas:
8. Carregue em **F8** (3D). Desenhe mais uma parede igual que continue a de baixo para a direita: clique no canto de
   baixo à direita da sala e 4 m mais à direita. Carregue em Esc.
9. Rode a vista para ver a fachada de baixo: não há linha onde a parede da sala acaba e a nova começa.
10. Selecione a parede nova e, nas **Propriedades**, mude o tipo para **Parede drywall 10 cm**: a linha aparece (o
    material mudou). Carregue em Ctrl+Z: volta a desaparecer.
11. Para ver no papel: na **Vista ▸ Alçados**, abra o alçado **Sul** (ou ponha-o numa folha e exporte o PDF): também
    sem a linha entre as duas paredes iguais.

## 0.319 — Escolher a trama da superfície e do corte

Feche o ArqSynth BIM e abra-o outra vez (**ArqSynth BIM.bat**), para entrar a versão nova.

1. Crie um projeto novo (Ctrl+N).
2. No separador **Gerenciar**, painel **Tipos e materiais**, clique em **Materiais…**. Clique em **Reboco**.
3. No grupo **Corte (plantas, cortes)**, ao lado de **Primeiro plano**, clique no botão que diz **Nenhum ▾**. Abre a
   janela **Escolher padrão**, com as tramas de desenho em quadrados grandes.
4. Clique em **Areia (pontos)** e em **OK**: o botão passa a mostrar a areia, e a amostra grande do corte também.
5. Ao lado de **Fundo**, clique no botão, escolha **Cheio** e OK. Clique no botão da cor ao lado e escolha um bege
   muito claro.
6. No grupo **Superfície (3D, alçados)**, clique na **amostra grande** (o quadrado à direita): abre a mesma janela,
   agora nas tramas **de modelo**. Escolha **Ladrilho 20×20** e OK.
7. Para criar uma trama nova a partir daqui: clique outra vez num botão de padrão e, na janela, em **Novo…**: abre a
   janela dos padrões com um padrão novo; dê-lhe um nome, escolha a forma, clique em **Aplicar** e **Fechar** — volta
   à escolha com ele já escolhido. Clique em OK.
8. Clique em **Aplicar** e em **Fechar**. Desenhe uma parede de **Parede alvenaria 20 cm** e veja a planta (F4): o
   reboco cortado tem os pontos sobre o bege.

## 0.318 — Padrões do projeto, tramas por categoria e a biblioteca de materiais

Um padrão novo:

1. Crie um projeto novo (Ctrl+N).
2. No separador **Gerenciar**, painel **Tipos e materiais**, clique em **Padrões…**. À esquerda estão os padrões do
   programa (a cinzento).
3. Clique em **Novo**. No **Nome**, escreva `Juntas 45`. Em **Medido**, deixe **No papel**. Em **Forma**, escolha
   **Linhas cruzadas**; **Ângulo** `45`, **Afastamento** `3`. A amostra mostra a quadrícula inclinada.
4. Em **Forma**, escolha **Personalizado**. Clique em **Juntar família** e, na linha nova, escreva: Ângulo `0`,
   Afastamento `1,5`, e em **Traços** `0 -0,8` (pontos). A amostra junta uma linha de pontos.
5. Clique em **Aplicar** e em **Fechar**.
6. No mesmo painel, clique em **Materiais…**. Escolha **Bloco cerâmico** e, em **Corte**, abra a lista **Primeiro
   plano**: **Juntas 45** está no fim dos padrões de desenho. Escolha-o, clique em **Aplicar** e em **Fechar**.
7. Grave o projeto (Ctrl+S), feche-o e abra-o outra vez: o padrão e o bloco continuam iguais.

A biblioteca de materiais:

8. Volte a **Materiais…**. Por cima da lista, escolha a família **Isolamentos**: só ficam os isolamentos (Lã mineral,
   XPS, EPS, Lã de rocha, Cortiça, Poliuretano). Na **Pesquisa**, escreva `granito` (com **Todas as famílias**): fica
   só o Granito, com a sua trama de corte e as fiadas na superfície.

Tramas por categoria num estilo:

9. Desenhe quatro paredes (Arquitetura ▸ Paredes ▸ Parede, **Forma** Retângulo, clique no chão, `6;4`, Enter, Esc).
10. Clique em **Visualizar ▸ Aspeto ▸ Estilos de vista…**, escolha **Linhas escondidas** e clique em **Novo a partir
    deste**. Dê-lhe o nome `Licenciamento`.
11. Em **Tramas por categoria**, clique em **Juntar…**. Escolha a categoria **Paredes**. Em **Corte**: **Primeiro
    plano** **Betão** e **Fundo** **Cheio** com um cinzento médio. Em **Superfície projetada**: **Primeiro plano**
    **Tijolo à vista**. Clique em OK e outra vez em OK.
12. Abra a planta (F4) e, nas **Propriedades** (sem nada escolhido), em **Estilo visual**, escolha **Licenciamento**:
    as paredes cortadas ficam com a trama de betão sobre cinzento, no ecrã. Carregue em Ctrl+P: no PDF também.
13. Abra o alçado **Sul** (Navegador do Projeto ▸ Alçados ▸ Sul), escolha o mesmo estilo e carregue em Ctrl+P: a
    fachada sai com o tijolo à vista.

## 0.317 — As tramas de corte e de superfície no ecrã

1. Crie um projeto novo (Ctrl+N). Em **Gerenciar ▸ Tipos e materiais ▸ Materiais…**, escolha **Bloco cerâmico** e, em
   **Corte**, **Primeiro plano** **Diagonal** e **Fundo** **Cheio** com um rosa claro. Clique em **Aplicar** e
   **Fechar**.
2. Desenhe quatro paredes de **Parede alvenaria 20 cm** (Arquitetura ▸ Paredes ▸ Parede, **Forma** Retângulo, clique
   no chão, `6;4`, Enter, Esc).
3. Carregue em F4 (planta): as paredes cortadas mostram, no ecrã, o reboco a cinzento dos dois lados e o bloco a rosa
   com a diagonal, como no papel — já não ficam todas escuras.
4. Clique numa parede: o seu corte passa à cor da seleção (azul claro). Carregue em Esc.
5. Para ver a superfície projetada: em **Gerenciar ▸ Tipos e materiais ▸ Tipos…**, faça uma laje com duas camadas
   (**Concreto** em baixo e **Azulejo cerâmico** em cima) e desenhe-a dentro das paredes (Arquitetura ▸ Laje). Na
   planta, o chão mostra as juntas do azulejo.
6. Carregue em Ctrl+P: no PDF da planta (sem estilo nenhum) o chão também sai com o azulejo.

## 0.316 — Sombras no papel e o sol à escolha

Comece com a casa de pedra do teste da 0.315 (passos 1 a 4).

O sol pelo local e pela hora:

1. No separador **Gerenciar**, painel **Projeto**, clique em **Localização do terreno…**. Escreva a latitude `38,72` e a
   longitude `-9,14` (Lisboa) e clique em OK.
2. No separador **Visualizar**, painel **Aspeto**, clique em **Estilos de vista…**.
3. Clique em **Realista** e em **Novo a partir deste**. No **Nome**, escreva `Tarde de verão`.
4. Na linha **Sol (sombras)**, clique em **Pelo local e pela hora…**. Escolha o dia 21/06 deste ano às `16:00` e o fuso
   **1,0** (hora de verão em Portugal). Clique em OK: o **Azimute** passa a uns 254° (oeste-sudoeste) e a **Altura** a
   uns 56°.
5. Clique em **OK**. No rodapé, clique no botão do estilo e escolha **Tarde de verão**: a sombra da casa cai agora para
   nascente (à direita, um pouco para trás).
6. Experimente escrever outro **Azimute** à mão (por exemplo `135`, sol de sudeste, de manhã) na janela dos estilos: a
   sombra passa para o outro lado.

As sombras no papel:

7. No **Navegador do Projeto**, em **Alçados**, faça duplo clique em **Sul**.
8. Com nada escolhido, nas **Propriedades**, na linha **Estilo visual**, escolha **Realista**.
9. Carregue em Ctrl+P, grave o PDF e abra-o: o caixilho da janela e a padieira fazem sombra dentro do vão, por cima e
   ao lado; as fiadas da pedra continuam por cima das sombras.
10. Para ver uma sombra maior: volte ao 3D (F8), no separador **Estrutura**, painel **Elementos**, clique em **Pilar** e
    clique no chão uns 1,5 m à frente da fachada sul; carregue em Esc. Volte ao alçado **Sul** e carregue outra vez em
    Ctrl+P: a sombra do pilar aparece na parede, desviada para a direita. (Uma laje de cobertura maior do que a casa,
    com beiral, faz uma faixa de sombra por baixo dele.)
11. Abra a planta (F4), escolha também **Realista** nas Propriedades e carregue em Ctrl+P: as paredes cortadas fazem
    sombra no chão, e pela porta entra uma faixa de luz.

## 0.315 — Estilos de vista com tramas e sombreamentos

Antes, dê à pedra uma parede (como no teste da 0.314, passos 1 a 3, mas com outro tipo):

1. Crie um projeto novo (Ctrl+N).
2. No separador **Gerenciar**, painel **Tipos e materiais**, clique em **Tipos…**. Na lista, clique em **Parede
   alvenaria 20 cm** e em **Duplicar**. No **Nome**, escreva `Parede de pedra`. Na tabela **Camadas**, na primeira linha
   (a de fora), abra a lista do material e escolha **Pedra natural**. Clique em **Aplicar** e em **Fechar**.
3. No separador **Arquitetura**, painel **Paredes**, clique em **Parede**. Na barra de cima, em **Forma**, escolha
   **Retângulo** e, em **Tipo**, **Parede de pedra**. Clique no chão, escreva `8;5` e carregue em Enter: ficam quatro
   paredes ligadas. Carregue em Esc.
4. No painel **Vãos**, clique em **Janela** e clique na parede da frente. Carregue em Esc.

O estilo «Realista» no 3D:

5. No rodapé (em baixo, à direita), clique no botão do **estilo visual** (o cubo pequeno). A lista tem os estilos do
   programa: Sombreado, Linhas escondidas, Arame, Raio-X, **Cores consistentes** e **Realista**. Clique em **Realista**.
6. A casa aparece com:
   - a pedra por fora, com as fiadas desenhadas;
   - no topo das paredes, as camadas lado a lado (pedra, bloco, reboco);
   - o vidro da janela transparente;
   - a sombra da casa no chão, à direita, e a das paredes por dentro.
7. Rode a vista (botão do meio do rato): a sombra fica no mesmo sítio (o sol está parado, à frente e à esquerda).

Um estilo do projeto:

8. No separador **Visualizar**, painel **Aspeto**, clique em **Estilos de vista…**.
9. Na lista da esquerda, clique em **Cores consistentes** (está a cinzento: é do programa e não se muda). Clique em
   **Novo a partir deste**: aparece «Cores consistentes — cópia», já escolhido.
10. No **Nome**, escreva `Apresentação`. Marque **Sombras do sol**. Em **Arestas**, escolha **2 px de espessura**.
    Clique em **OK**.
11. No rodapé, clique outra vez no botão do estilo: **Apresentação** está no fim da lista. Clique nele: a casa fica em
    cores sem luz, com as arestas mais grossas e a sombra no chão.
12. Carregue em Ctrl+Z duas vezes: volta ao Realista e depois o estilo «Apresentação» desaparece.

Os desenhos com estilo:

13. No **Navegador do Projeto** (à esquerda), em **Alçados**, faça duplo clique em **Sul**.
14. Com nada escolhido, nas **Propriedades**, na linha **Estilo visual**, escolha **Realista** (a primeira opção,
    «Nenhum», deixa o desenho em linhas, como sempre).
15. Carregue em Ctrl+P, escolha onde gravar e clique em **Gravar**. Abra o PDF: o alçado sai com a pedra pintada e as
    suas fiadas, a janela com o caixilho e o vidro, a laje a cinzento.
16. Abra a planta (F4) e, nas Propriedades, escolha o **Estilo visual** **Cores consistentes**: no ecrã, o chão e o
    corte das paredes passam às cores dos materiais. Carregue em Ctrl+P: no PDF o chão sai pintado.
17. Para dar o mesmo estilo a várias vistas de uma vez: separador **Visualizar**, painel **Aspeto**, **Modelos de
    vista…** — a linha nova **Estilo de vista**.

## 0.314 — Os materiais com gráficos completos (superfície e corte)

1. Crie um projeto novo (Ctrl+N).
2. No separador **Gerenciar**, painel **Tipos e materiais**, clique em **Materiais…**.
3. Na lista da esquerda, clique em **Azulejo cerâmico**. À direita há duas partes novas, cada uma com uma amostra:
   - **Superfície (3D, alçados):** o primeiro plano já tem **Azulejo 15×15** (as juntas), a cor de sombreamento e a
     transparência;
   - **Corte (plantas, cortes):** sem padrões próprios — a nota diz que corta com a trama da categoria.
4. Clique em **Bloco cerâmico**. Em **Corte**:
   - no **Primeiro plano**, escolha **Diagonal**;
   - no **Fundo**, escolha **Cheio** e clique no botão da cor ao lado; escolha um rosa claro e clique em OK.

   A amostra do corte mostra a diagonal sobre o rosa, e a nota desaparece.
5. Clique em **Lã mineral**. Em **Corte**, no **Primeiro plano**, escolha **Isolamento** (o ziguezague); no **Fundo**,
   **Cheio** e um amarelo claro.
6. Clique em **Aplicar** e depois em **Fechar**.
7. No separador **Arquitetura**, painel **Paredes**, clique em **Parede**. Na barra de cima, abra a lista **Tipo**: a
   miniatura da **Parede alvenaria 20 cm** já mostra o bloco com a diagonal sobre o rosa. Escolha-a.
8. Clique no chão, escreva `6` e carregue em Enter. Escolha agora o tipo **Parede drywall 10 cm**, clique ao lado,
   escreva `4` e carregue em Enter. Carregue em Esc.
9. Abra a planta (F4) e carregue em Ctrl+P; grave o PDF e abra-o: no corte, o bloco está com a diagonal sobre rosa, a
   lã mineral com o ziguezague sobre amarelo, e o reboco e o gesso como antes.
10. Grave o projeto (Ctrl+S), feche-o e abra-o de novo; volte a **Materiais…**: o bloco e a lã têm os mesmos padrões.
11. No separador **Visualizar**, painel **Aspeto**, clique em **Estilos gráficos…**: na coluna **Padrão** há agora,
    além de Cheio, Linhas, Linhas cruzadas e Nada, os padrões novos (Betão, Areia, Isolamento, Terra, Madeira, Aço,
    Quadrícula) para dar a uma categoria inteira.

## 0.313 — O tipo no cabeçalho das Propriedades, com miniaturas

1. Crie um projeto novo (Ctrl+N).
2. No separador **Arquitetura**, painel **Paredes**, clique em **Parede**. Olhe para a barra de cima: a lista **Tipo**
   tem uma pequena imagem da parede ao lado do nome. Clique nela: cada tipo de parede aparece com o corte das suas
   camadas. Escolha **Parede alvenaria 20 cm**.
3. Clique no chão, escreva `6` e carregue em Enter. Carregue em Esc.
4. No painel **Vãos**, clique em **Janela** e clique na parede. Carregue em Esc.
5. Clique no botão **Selecionar** e clique na janela. No painel **Propriedades**, em cima:
   - à esquerda, a miniatura da janela;
   - ao lado, o nome «Janela 1» e, por baixo, a lista com o tipo.
6. Clique nessa lista: abre com o desenho de cada janela (alçado, cores e sinais de abertura). Escolha a **Janela
   150×120 (peitoril 1,00)**: a janela muda no modelo, e a miniatura de cima muda também.
7. Clique na parede: em cima aparece o corte da parede e a lista dos tipos de parede, cada um com o seu corte.
8. Com o Shift carregado, clique noutra parede de outro tipo (desenhe uma de **Parede drywall 10 cm**, se precisar). A
   lista de cima diz «<vários>»; escolha um tipo e as duas paredes passam a esse tipo.
9. Nas Propriedades, na linha **Tipo**, clique em **Editar tipo…**: na lista da esquerda, cada tipo tem também a sua
   miniatura.

## 0.312 — Portas e janelas sem linhas de junta

1. Crie um projeto novo (Ctrl+N).
2. No separador **Arquitetura**, painel **Paredes**, clique em **Parede**. Clique no chão, escreva `6` e carregue em
   Enter. Carregue em Esc.
3. No painel **Vãos**, clique em **Janela**. Na barra de cima, em **Tipo**, escolha **Janela 120×120 (peitoril
   1,00)**. Clique na parede, a cerca de 1,5 m da ponta esquerda.
4. No painel **Vãos**, clique em **Porta**. Na barra de cima, em **Tipo**, escolha a **Porta 80×210**. Clique na
   parede, a cerca de 4 m da ponta esquerda. Carregue em Esc.
5. Vá para a vista **3D** e aproxime-se de um canto de cima da janela, pela rodinha do rato. Veja que:
   - onde o montante do aro encontra a travessa de cima, já não há traço (antes havia um traço duplo);
   - nos cantos das folhas também não;
   - continua a ver-se a linha à volta de cada folha, e a linha entre as duas folhas, ao meio.
6. Dê a volta à parede (botão do meio do rato) e veja a janela por dentro: as dobradiças e os puxadores lá estão, e os
   cantos do aro e das folhas também estão limpos.
7. Aproxime-se da porta, em cima. As guarnições fazem um ∩ sem traço entre a de cima e as dos lados. No vão, a
   guarnição e o aro ficam sem traço entre eles.
8. Para limpar uma porta ou janela que já estava num projeto antigo: com o botão **Selecionar**, clique nela e, nas
   **Propriedades**, mude a **Distância ao início da parede** 1 cm e volte a pô-la. Fica refeita, sem juntas.

## 0.311 — Push/Pull em várias faces ao mesmo tempo

1. No separador **Modelagem**, painel **Desenhar**, clique em **Retângulo**. Clique no chão, escreva `3;2` e carregue
   em Enter.
2. Clique outra vez em **Retângulo**. Clique no chão uns 2 m à direita do primeiro, escreva `2;2` e carregue em Enter.
3. No painel **Modificar**, clique em **Offset**. Clique dentro do primeiro retângulo, escreva `0,20` e carregue em
   Enter.
4. No painel **Desenhar**, clique em **Push/Pull**. Clique numa das tiras da moldura (a faixa de 20 cm), escreva `0,30`
   e carregue em Enter:
   - a moldura inteira sobe 30 cm, à volta toda;
   - não há paredes entre as tiras;
   - o meio fica em baixo.
5. Carregue em Ctrl+Z: a moldura volta ao chão.
6. No painel **Selecionar**, clique em **Selecionar**. Clique no meio do primeiro retângulo: só o meio fica azul.
   Carregue no Shift e, sem o largar, clique no segundo retângulo: fica também escolhido.
7. No painel **Desenhar**, clique em **Push/Pull** e clique no segundo retângulo. Mova o rato para cima:
   - os dois sobem ao mesmo tempo;
   - ao lado da face aparece «2 faces».

   Escreva `1` e carregue em Enter:
   - os dois ficam com 1 m de altura;
   - por baixo, na barra de estado, aparece «2 faces puxadas 1,00 m, todas juntas…»;
   - o meio continua azul.
8. Logo a seguir, escreva `0,5` e carregue em Enter: os dois baixam para 50 cm.
9. Carregue uma vez em Ctrl+Z: os dois voltam ao chão ao mesmo tempo (um só passo).
10. Desenhe um retângulo de `4;3`, longe dos outros. No painel **Desenhar**, clique em **Linha**. Clique no meio de um
    lado comprido do retângulo (aparece «Ponto médio»), depois no meio do lado oposto, e carregue em Esc: o retângulo
    fica com duas divisões.
11. No painel **Selecionar**, clique em **Selecionar**. Clique numa divisão e, com o Shift carregado, clique na outra.
    Clique em **Push/Pull**, clique numa delas, escreva `2,80` e carregue em Enter:
    - fica um volume só, sem parede no meio;
    - a linha da divisória continua no teto e no chão;
    - o teto das duas divisões fica escolhido.
12. Carregue no **Ctrl** e largue-o, sem outra tecla: **Criar sólido (Ctrl)** fica com visto. Clique no teto, escreva
    `2,80` e carregue em Enter: fica um segundo piso por cima, e o teto novo é o que fica escolhido. Repita (clique no
    teto, `2,80`, Enter): terceiro piso.
13. Clique numa face que não está escolhida, por exemplo um lado do volume. O Push/Pull leva só essa face, como antes.

## 0.310 — Faces sozinhas e Push/Pull como no SketchUp

1. No separador **Modelagem**, painel **Desenhar**, clique em **Retângulo**. Clique no chão, escreva `3;2` e carregue
   em Enter.
2. No painel **Modificar**, clique em **Offset**. Clique dentro do retângulo, escreva `0,20` e carregue em Enter. Fica
   uma linha 20 cm para dentro.
3. No painel **Selecionar**, clique em **Selecionar**. Clique no meio do retângulo:
   - só o meio fica azul; a moldura à volta não;
   - por baixo, na barra de estado, aparece «Face selecionada (4,16 m²)».
4. Espere um segundo e clique uma vez na moldura (a tira de 20 cm). Só a moldura fica azul, à volta toda.
5. Logo a seguir, clique outra vez na moldura: as arestas dela ficam também a azul forte. Clique uma terceira vez:
   fica escolhido o esboço inteiro.
6. Carregue em Esc. Clique no meio e carregue em **Delete**. O meio desaparece e fica um buraco na moldura. Carregue em
   Ctrl+Z: o meio volta.
7. No painel **Desenhar**, clique em **Push/Pull**. Clique no meio, escreva `-0,30` e carregue em Enter. Fica um
   rebaixo aberto em cima, como no SketchUp: vê-se o fundo e as paredes de dentro.
8. Carregue em Ctrl+Z. Carregue no **Ctrl** e largue-o, sem outra tecla:
   - na barra por baixo da fita, **Criar sólido (Ctrl)** fica com visto;
   - a ajuda em baixo começa por «+ SÓLIDO».
9. Clique no meio, escreva `-0,30` e carregue em Enter. Fica um sólido fechado por baixo da moldura: o meio continua
   em cima, e por baixo há uma caixa de 30 cm.
10. Carregue em Ctrl+Z. Clique no meio e puxe o rato para cima, depois clique. Também fica uma caixa fechada, por cima.
    Carregue em Ctrl+Z, e no **Ctrl** sozinho outra vez: **Criar sólido** fica sem visto.
11. No painel **Selecionar**, clique em **Selecionar** e clique no meio. No painel **Modificar**, clique em **Mover**.
    Clique no meio, leve o rato um pouco para a direita, escreva `0,10` e carregue em Enter:
    - só o meio anda 10 cm;
    - a moldura estica à volta dele;
    - o meio continua escolhido.
12. Ainda com o **Mover**, carregue em Ctrl+Z: o meio volta ao sítio. A ajuda em baixo não começa por «+ CÓPIA»: o Ctrl
    do Ctrl+Z já não liga a cópia.
13. Desenhe outro retângulo de `4;0,2` e puxe-o 2,80 m com o **Push/Pull**. No painel **Selecionar**, clique em
    **Selecionar** e clique uma vez numa face da caixa: só essa face fica azul. No separador **Modelagem**, painel
    **Criar**, clique em **Classificar como** e escolha **Parede alvenaria 20 cm**: a caixa inteira passa a parede.
## 0.309 — Igualar todas as divisões no Caixilho Studio

1. No separador **Arquitetura**, painel **Vãos**, clique em **Caixilho Studio**. Abre uma janela nova, J01, com três
   colunas.
2. Por baixo do desenho, clique na cota da primeira coluna (800), escreva `700` e carregue em Enter. As colunas deixam
   de ser iguais.
3. Na barra por cima do desenho, clique em **Igualar tudo**:
   - os botões **Larguras iguais** e **Alturas iguais** ficam com ● e fundo azul claro;
   - as três colunas voltam a 800 e, em cada coluna, os dois painéis ficam com 750;
   - as cotas mostram **EQ** a negro;
   - no canto superior direito aparece «Larguras iguais: ligado · Alturas iguais: ligado».
4. Arraste da faixa tracejada de cima («↓ arraste para criar montante») para dentro da primeira coluna e largue. Ficam
   quatro colunas, todas com 600.
5. Arraste da faixa tracejada da esquerda («→ travessa») para perto do fundo do vão e largue. Em cada coluna ficam
   três painéis, todos com 500.
6. Clique na cota total por baixo (2400), escreva `3000` e carregue em Enter. As quatro colunas ficam com 750.
7. Arraste a pega azul do primeiro montante um pouco para a direita. As colunas deixam de ser iguais:
   - **Larguras iguais** fica com ○;
   - o aviso diz «Larguras iguais: desligado»;
   - **Alturas iguais** continua ligado.
8. Clique em **Larguras iguais**: fica outra vez com ●, e as colunas voltam a ser iguais.
9. Clique em **Inserir no modelo** e ponha a janela numa parede. Carregue em Esc.
10. No separador **Gerenciar**, clique em **Tipos**. Na lista de cima escolha **Janelas** e, por baixo, **J01**. Mude
    a **Largura** para 3,60 e clique em **Aplicar**. No pequeno desenho do tipo, e na janela da parede, as quatro
    colunas continuam iguais.
11. Clique em **Caixilho Studio…**, por baixo do desenho: o Studio abre com **Larguras iguais** e **Alturas iguais**
    ligados.

## 0.308 — O Caixilho Studio no tema do programa

1. No separador **Arquitetura**, painel **Vãos**, clique em **Caixilho Studio**.
2. O cabeçalho do Studio é azul-escuro como o do programa, com o mesmo símbolo da marca, «ArqSynth BIM» e «Caixilho
   Studio».
3. Os separadores dos vãos e o rodapé estão no cinzento claro da fita. A tela, onde está o vão, é clara, com uma
   grelha suave.
4. As cotas, as pegas dos montantes e travessas e o botão **Inserir no modelo** estão no azul do programa.
5. Clique num painel: o cartão é branco, e a abertura escolhida fica em azul claro, como os botões escolhidos da fita.
6. O resto funciona como na 0.307 (arrastar montantes e travessas, cotas, cartão, separadores, inserir).

## 0.307 — O Caixilho Studio

1. Crie um projeto novo (Ctrl+N) e desenhe uma **Parede** de 6 m.
2. No separador **Arquitetura**, painel **Vãos**, clique em **Caixilho Studio**. Abre-se a janela do Studio com
   uma janela nova (J01, 2400 × 1500, três colunas com basculantes por cima).
3. Arraste a partir da faixa tracejada de cima («↓ arraste para criar montante») para o meio da primeira coluna: uma
   linha azul tracejada mostra onde fica e as duas medidas. Largue: fica um montante novo.
4. Pegue na pega âmbar de um montante e arraste-a para a direita: as cotas de baixo mudam de 10 em 10 mm. Clique na
   pega e use as setas do teclado (com Shift andam 100 mm).
5. Clique na cota de uma coluna, escreva «2400/3» e carregue em Enter: a coluna fica com 800.
6. Clique num painel: abre-se o cartão. Escolha **Oscilo** e o círculo do **Vidro fosco**. Feche o cartão com o «×».
7. Clique em **Travessas ligadas** para as desligar. Arraste a partir da faixa da esquerda («→ travessa») para dentro
   de uma coluna: a travessa nova fica só nessa coluna.
8. Clique em **Vista interior**: a janela vê-se espelhada, como de dentro de casa. Volte à **Vista exterior**.
9. No rodapé, escolha o sistema **PVC** e a cor **Branco**: o aro passa a branco. Veja ao fundo a área envidraçada, a
   área de abertura e a classe IFC.
10. Clique em **+** e escolha **Porta com bandeira e lateral**: aparece o separador P01, com a porta de madeira, a
    bandeira de vidro e a lateral fosca.
11. Clique em **Mais opções…** e ponha uma **Soleira** de 30 mm; OK.
12. Clique em **Inserir no modelo**. A janela fecha, os dois vãos ficam gravados como tipos e a ferramenta Porta fica
    ligada com a P01. Clique na parede: a porta fica colocada.
13. Selecione a porta e, nas Propriedades, clique em **Caixilho Studio…**: abre-se o Studio só com essa porta.
    Mude-lhe uma coisa e clique em **Guardar**: a porta muda no modelo.

## 0.306 — O núcleo das portas e janelas por colunas

Esta versão prepara o Caixilho Studio (0.307); vê-se e testa-se por ele. Antes disso, só uma verificação:

1. Abra um projeto que já tenha portas e janelas feitas no gerador antigo. Ficam exatamente como estavam: os mesmos
   vidros, folhas, peitoris e portadas.
2. No separador **Gerenciar**, clique em **Materiais**. Na lista há agora o **Vidro fosco** e os perfis por sistema e
   cor, por exemplo «Alumínio grafite», «PVC branco» e «Madeira bronze».

## 0.305 — Ranhura

1. Crie um projeto novo (Ctrl+N). Desenhe uma **Parede** de 6 m e veja-a de frente (F3).
2. No separador **Arquitetura**, painel **Paredes**, clique em **Ranhura**. Na barra de cima: **Direção** Horizontal,
   **Largura** 0,02 m, **Profundidade** 0,01 m.
3. Passe o rato pela face da parede: vê-se a linha da ranhura à altura do rato. Clique a cerca de 1 m do chão: fica
   uma ranhura ao longo da parede toda.
4. Carregue em Tab (Vertical) e clique a cerca de 4 m da ponta esquerda: fica uma ranhura vertical, a subir a parede
   toda.
5. Estique a parede 2 m pela ponta direita: a ranhura horizontal estica com ela.
6. Ligue **Tirar ranhuras** na barra e clique na ranhura vertical: desaparece.
7. Clique na parede para abrir o separador verde **Modificar | Paredes** e confira a arrumação:
   - Modificar parede;
   - Ligações;
   - Dividir e aparar;
   - Vãos e acabamentos;
   - Modificar.

   Numa janela estreita, o **Modificar** (mover, rodar…) é o primeiro a recolher-se.

## 0.304 — Rodapé, sanca, friso ou cimalha na parede

1. Crie um projeto novo (Ctrl+N). Desenhe quatro **Paredes** que fechem uma casa de 8 × 5 m e ponha uma **Porta**
   numa delas.
2. No separador **Arquitetura**, painel **Paredes**, clique em **Rodapé na parede**. Na barra de cima, o **Perfil**
   é **Rodapé** e a **Altura ao chão** é 0,00 m.
3. Olhe para dentro da casa e passe o rato sobre a face interior de uma parede: vê-se o caminho do rodapé a dar a
   volta à sala. Clique: o rodapé fica feito, com os cantos em meia-esquadria, e pára na porta.
4. Mude o **Perfil** para **Cimalha**, olhe a casa de fora e clique na face exterior de uma parede: a cimalha dá a
   volta à casa toda, junto ao topo.
5. Mova uma das paredes 1 m para fora: o rodapé e a cimalha acompanham-na.
6. Desenhe duas paredes soltas em L e clique na face de fora de uma delas: o perfil vai de uma ponta à outra do L,
   com o canto em meia-esquadria.

## 0.303 — Abertura na parede

1. Crie um projeto novo (Ctrl+N). Desenhe uma **Parede** de 6 m e veja-a de frente (F3).
2. No separador **Arquitetura**, painel **Vãos**, clique em **Abertura na parede**.
3. Clique na face da parede, a 2 m da ponta esquerda e a cerca de 0,90 m do chão. Mexa o rato: vê-se o retângulo da
   abertura, a largura, a altura e a altura a que começa.
4. Escreva «1,2;1» e carregue em Enter. Fica uma abertura de 1,20 × 1,00 que atravessa a parede, sem porta nem janela.
5. Mova a parede: a abertura vai com ela.
6. Tente uma abertura que passe acima do topo da parede: o programa recusa e explica porquê.

## 0.302 — Ligar e desligar a base

1. Crie um projeto novo (Ctrl+N). Desenhe uma **Parede** de 5 m e um **Pilar** perto dela, ambos no piso Térreo.
2. Desenhe uma **Laje** de 12 cm por baixo dos dois. Selecione-a, carregue em M, clique num canto dela, desça o rato
   e escreva 0,3 + Enter: a face de cima da laje fica a −0,18 m.
3. Clique na parede e, com Shift, no pilar e na laje. No separador verde **Modificar | Paredes**, painel **Modificar
   parede**, clique em **Ligar a base**. A parede e o pilar descem até à face de cima da laje e o topo fica onde estava
   (2,80 m).
4. Selecione só a laje e mova-a 20 cm para baixo: a parede e o pilar descem com ela.
5. Selecione a parede e clique em **Desligar a base**. Mova outra vez a laje para baixo: a parede fica onde está e o
   pilar continua a acompanhar a laje.

## 0.301 — Junções de paredes

1. Crie um projeto novo (Ctrl+N). Desenhe duas **Paredes** em L, clicando em seguida: 5 m para a direita e 4 m para
   cima. Veja de cima (F2): a primeira parede passa no canto e a segunda pára na face dela.
2. Carregue em Esc e clique numa das paredes: abre-se o separador verde **Modificar | Paredes**. No painel
   **Ligações**, clique em **Junções de paredes**. Na barra de cima, a **Junção** está em **Topo a topo (a parede
   clicada passa)**.
3. Passe o rato sobre a segunda parede, perto do canto: aparece um ponto verde no canto. Clique: agora é a segunda
   parede que passa e a primeira pára na face dela.
4. Carregue em Tab: a junção passa a **Meia-esquadria**. Clique outra vez perto do canto: as duas paredes acabam
   cortadas a 45°, sem linha a meio.
5. Carregue em Esc, selecione a parede vertical e mova-a 1 m para a direita: o canto continua em meia-esquadria.
6. Desenhe duas paredes que façam um canto a 60°. Com **Junções de paredes**, clique perto desse canto: o programa
   diz que nos outros ângulos as paredes já se juntam em meia-esquadria.

## 0.300 — Dividir com folga e aparar / estender até um limite

1. Crie um projeto novo (Ctrl+N). Desenhe uma **Parede** de 6 m.
2. Carregue em Esc e clique na parede: abre-se o separador verde **Modificar | Paredes**. No painel **Dividir e
   aparar**, clique em **Dividir com folga**. Na barra de cima, a **Folga** é 0,02 m.
3. Passe o rato sobre a parede: veem-se duas linhas (os lados da folga) e as duas medidas. Ao meio, o cursor é
   atraído. Clique ao meio: ficam duas paredes de 2,99 m, com 2 cm entre elas.
4. Mude a **Folga** na barra para 0,10 e divida outra parede: a folga fica com 10 cm.
5. Desenhe uma parede vertical de 6 m, mais à direita, que vai servir de limite. Desenhe à esquerda dela duas paredes
   horizontais: uma curta, que não chega ao limite, e uma comprida, que o atravessa.
6. No separador **Modelagem**, painel **Modificar**, clique em **Aparar a um limite**. Clique na parede vertical: fica
   selecionada como limite.
7. Clique na parede curta, do lado esquerdo: estende-se até à face do limite e fica ligada em T. Clique na parede
   comprida, também do lado esquerdo: o bocado que passava para lá do limite é cortado e ela fica ligada em T.
8. Carregue em Esc (outro limite) e outra vez Esc (volta a Selecionar). Mova a parede do limite para a direita: as
   duas paredes acompanham-na.

## 0.299 — Virar a parede e ligar as pontas

1. Crie um projeto novo (Ctrl+N). No separador **Gerenciar**, clique em **Tipos**. Crie um tipo de parede com
   isolamento numa só face, por exemplo: reboco 2 cm, bloco 20 cm, lã mineral 6 cm e reboco 1 cm. Feche o editor.
2. No separador **Arquitetura**, clique em **Parede**, escolha esse tipo e desenhe uma parede de 5 m.
3. Abra a planta (F4) e aproxime a parede: a trama do isolamento está junto a uma das faces.
4. Carregue em Esc e clique na parede. Abre-se o separador verde **Modificar | Paredes**. No painel **Modificar
   parede**, clique em **Virar a parede**. O isolamento passa para a outra face, e a parede não sai do sítio.
5. Clique outra vez em **Virar a parede**: o isolamento volta para a face onde estava.
6. Desenhe duas paredes em canto (um L), clicando sempre em seguida. Selecione as duas (Shift + clique) e, no painel
   **Ligações**, clique em **Soltar ligações**. Mova uma delas um pouco: a outra já não a acompanha. Carregue em
   Ctrl+Z para desfazer o movimento.
7. Com as duas selecionadas, clique em **Ligar as pontas**. O canto volta a fazer-se. Mova uma das paredes: a outra
   volta a acompanhá-la.
8. Desenhe uma parede que acabe a meio de outra, sem ligar (por exemplo, desenhe-a primeiro e mova-a depois até
   tocar). Selecione-a e clique em **Ligar as pontas**: fica em T, parada na face da outra parede.

## 0.298 — A fita por disciplinas e o separador «Modificar | Paredes»

1. Abra o programa com a janela maximizada. No cabeçalho, os separadores estão por esta ordem: a casinha (Início),
   **Modelagem**, **Gerenciar**, **Massa e Estudos**, **Terreno**, **Arquitetura**, **Estrutura**, **Instalações**,
   **Colaborar**, **Anotar**, **Visualizar**, **Render**.
2. Clique em **Arquitetura**. A fita mostra painéis com o nome por baixo: Selecionar, Paredes, Vãos, Pisos e
   coberturas, Circulação, Salas e tetos, Mobiliário. As ferramentas principais têm botões grandes; as outras têm
   botões pequenos, em colunas.
3. Carregue em Ctrl+6: abre a **Estrutura**. Carregue em Ctrl+5: volta à **Arquitetura**.
4. Desenhe uma **Parede** de 6 m. Carregue em Esc e clique na parede. Aparece no fim dos separadores um separador
   verde, **Modificar | Paredes**, já aberto, com os painéis Modificar parede, Ligações, Dividir e aparar, Vãos e
   acabamentos e Modificar (arrumação final da 0.305).
5. Com a parede selecionada, clique em **Editar perfil** (painel Modificar parede). Clique no quadrado do canto de
   cima à direita, suba o rato um metro e clique outra vez; carregue em Esc. Clique outra vez na parede e depois em
   **Repor perfil**. A parede volta a ser um retângulo, com a altura do ponto mais alto do perfil.
6. Desenhe uma **Laje** por cima da parede, a 3,00 m. Selecione a parede e a laje (Shift + clique) e clique em
   **Ligar o topo**. A parede sobe até à face de baixo da laje.
7. Selecione só a parede e clique em **Desligar o topo**. Mova a laje para cima: a parede já não a segue e fica com a
   altura que tinha.
8. Com a parede selecionada, clique no separador **Arquitetura**: a fita mostra a Arquitetura e o separador verde
   continua lá. Clique no separador verde: voltam os modificadores.
9. Carregue em Esc. O separador verde desaparece e a fita fica na Arquitetura.
10. Tire a janela do modo maximizado e estreite-a. Os painéis da direita recolhem-se, cada um num botão com o nome e
    uma seta (por exemplo **Mobiliário ▾**). Clique num deles: aparecem as ferramentas desse painel. Alargue a janela:
    os painéis voltam a abrir-se.
11. Passe pelos separadores **Gerenciar**, **Colaborar** e **Visualizar**: os botões têm ícones desenhados (não
    iniciais), por exemplo Localização, Fases, Tipos, Partilhar projeto, Sincronizar, Conflitos e Isométrica.

## 0.297 — O peitoril vai sozinho para o lado de fora

1. Crie um projeto novo (Ctrl+N). Desenhe quatro **Paredes** que fechem uma casa de 8 × 5 m.
2. Clique em **Janela**, escolha a **Janela 120×120 (peitoril 1,00)** e clique na parede de baixo **pelo lado de
   dentro** da casa. A janela fica virada com o peitoril para fora da casa.
3. Na vista **3D**, olhe a casa de fora: o peitoril de pedra sai da parede para fora.
4. Ponha uma **Janela oscilobatente** noutra parede, também clicando por dentro. Fica com o peitoril para fora e o
   tipo «… (espelhada)», com as dobradiças no mesmo montante.
5. Clique em **Selecionar**, clique na primeira janela e, nas Propriedades, clique em **Virar a janela → Lado**. O
   peitoril passa para dentro.
6. Desenhe uma parede pequena dentro da casa. A janela virada à mão continua com o peitoril para dentro: o programa
   não volta a mexer nela.
7. Num projeto novo, desenhe só três paredes da casa (aberta) e ponha uma janela clicando por dentro. Como não há
   divisão, fica como foi clicada. Desenhe a quarta parede: a janela vira-se sozinha para fora. Carregue em Ctrl+Z: a
   parede desaparece e a janela volta a ficar como estava.

## 0.296 — Folhas de abrir dentro do arco

1. Crie um projeto novo (Ctrl+N) e desenhe uma **Parede** de 5 m.
2. Clique em **Janela**, escolha em **Tipo** a **Janela em arco 100×150 (peitoril 0,90)** e clique na parede, do lado
   de fora.
3. Clique em **Selecionar**, clique na janela e, nas Propriedades, clique em **Gerador de portas e janelas…**.
4. No desenho à esquerda, clique dentro do arco (a meia-lua de cima). A caixa passa a dizer **Célula 1 da linha 2**.
   Clique em **Tirar a linha**. As duas folhas de batente sobem até à curva, com a travessa de cima curva. Não deve
   aparecer nenhum aviso a vermelho.
5. Clique em **OK**. Na vista **3D**, aproxime-se da janela: a travessa de cima de cada folha acompanha o arco numa
   só peça, sem juntas, e as dobradiças ficam abaixo do arranque do arco.
6. Abra o gerador outra vez, clique na folha da esquerda e, em **Abertura**, escolha **De correr (abre para a
   esquerda)**. Aparece o aviso de que debaixo do arco a folha não pode ser de correr, e o OK fica desligado. Escolha
   **Basculante (dobradiças em baixo)**: o aviso desaparece. Clique em **Cancelar**.
7. Nota: o passo 7 do teste da 0.294 mudou. Uma folha de batente debaixo do arco já não dá aviso.

## 0.295 — Portadas de lâminas

1. Crie um projeto novo (Ctrl+N) e desenhe uma **Parede** de 5 m.
2. Clique em **Janela**, escolha em **Tipo** a **Janela 120×120 (peitoril 1,00)** e clique na parede, do lado de fora.
3. Clique em **Selecionar** e clique na janela. Nas Propriedades, clique em **Gerador de portas e janelas…**.
4. Desça até **Portadas de lâminas** e escolha **2 folhas**. No desenho à esquerda aparecem as duas portadas por cima
   da janela, meio transparentes, com as lâminas. Não deve aparecer nenhum aviso a vermelho. Clique em **OK**.
5. Na vista **3D**, olhe a janela de fora. As portadas estão fechadas dentro do vão, à face da parede, de madeira.
   Aproxime-se: as lâminas estão inclinadas, com a aresta de fora mais baixa.
6. Abra o gerador outra vez e ligue **Portadas abertas (rebatidas sobre a parede)**. As folhas passam para os lados da
   janela. Clique em **OK**. No 3D, as portadas estão deitadas na parede, uma de cada lado.
7. Abra o gerador e escreva 0,20 em **Estore (altura da caixa)** e carregue em Enter. Aparece o aviso de que portadas
   e estore não vão juntos, e o OK fica desligado. Clique em **Cancelar**.
8. No **Navegador do Projeto**, em **Vistas**, clique com o botão direito em **Mapa de vãos**, escolha **Pôr na folha**
   e depois **Nova folha**. A janela aparece com as portadas abertas ao lado e a linha «Com portadas de lâminas» por
   baixo.

## 0.294 — Vãos em arco

1. Crie um projeto novo (Ctrl+N) e desenhe uma **Parede** de 5 m.
2. Clique em **Janela**. Em **Tipo**, escolha **Janela em arco 100×150 (peitoril 0,90)** e clique na parede, do lado de
   fora. A parede fica cortada em arco e a janela tem duas folhas de batente debaixo de um arco fixo.
3. Ponha uma **Porta 90×210** na mesma parede. Selecione-a e, nas Propriedades, clique em **Gerador de portas e
   janelas…**.
4. Em **Arco**, escolha **abatido**. Aparece por cima da folha uma linha fixa, com a curva no topo.
5. Em **Flecha do arco (abatido)** escreva 0,25 e carregue em Enter. O arco sobe. Não deve aparecer nenhum aviso a
   vermelho. Clique em **OK**.
6. Na vista **3D**: o vão da porta está cortado em arco, com o aro curvo e as guarnições a contornar o arco.
7. Abra o gerador outra vez e escolha **de volta inteira**. Mude a abertura da célula do arco para **De batente**:
   aparece o aviso de que debaixo do arco só pode haver fixos, e o OK fica desligado. Clique em **Cancelar**.
8. Mova a janela em arco ao longo da parede (Propriedades, **Distância ao início da parede**): o vão continua em arco.

## 0.293 — Mapa de vãos

1. Use o projeto do teste anterior (duas portas e duas janelas), ou ponha algumas portas e janelas numa parede.
2. No Navegador do Projeto, em **Vistas**, aparece **Mapa de vãos**. Clique nele com o botão direito, escolha **Pôr na
   folha** e depois **Nova folha**.
3. Abre-se a folha com o mapa a 1:50. Cada tipo aparece em alçado, com as cotas de largura e altura e, por baixo:
   - o nome e «L × A»;
   - o peitoril (janelas);
   - a abertura;
   - a quantidade, com as marcas.
4. Inverta as dobradiças de uma das portas 80×210 (Propriedades, **Virar a porta**, **Dobradiça**). No mapa, a porta
   continua a contar com o seu tipo: «Quantidade: 2».
5. Imprima a folha em PDF.

## 0.292 — Sinais de abertura nos alçados

1. Crie um projeto novo (Ctrl+N). Desenhe uma **Parede** de 9 m.
2. Ponha, clicando do lado de fora (o lado de baixo, a sul), uma **Porta 80×210**, uma **Porta de 2 folhas 140×210**,
   uma **Janela 120×120 (peitoril 1,00)** e uma **Janela 150×120 (peitoril 1,00)**.
3. No Navegador do Projeto, em **Alçados**, faça duplo clique em **Sul**. Veja:
   - em cada folha de batente, duas linhas que se encontram do lado das dobradiças;
   - na janela de correr, uma seta para o lado onde abre.
4. Faça duplo clique em **Norte**: os mesmos sinais, vistos de dentro, ficam ao espelho.
5. Ponha o alçado **Sul** numa folha e imprima-a em PDF: os sinais saem também no papel.

## 0.291 — Estore, mosquiteiro e grade

1. Crie um projeto novo (Ctrl+N). Desenhe uma **Parede** de 6 m e ponha uma **Janela 120×120 (peitoril 1,00)**,
   clicando do lado de fora da parede.
2. Clique em **Selecionar**, clique na janela e, nas Propriedades, clique em **Gerador de portas e janelas…**.
3. Em **Estore (altura da caixa)** escreva 0,20 e carregue em Enter. Aparece a caixa no topo e o aro desce.
4. Em **Estore descido** ponha 50 % e carregue em Enter. As lâminas descem até meio.
5. Ligue **Mosquiteiro**: a rede aparece por cima do vidro, semitransparente.
6. Ligue **Grade**: aparecem as barras verticais e as duas travessas.
7. Por baixo dos materiais deve continuar «No IFC: DOUBLE_PANEL_VERTICAL», sem avisos. Clique em **OK**.
8. Na vista **3D**, de fora, veja a caixa do estore, as calhas nos aros, as lâminas a meio, a grade à frente de
   tudo e, entre a grade e o vidro, a rede.
9. Guarde o ficheiro e abra-o noutro programa IFC. No tipo da janela, em Pset_WindowCommon, há a
   GlazingAreaFraction e HasSillExternal = verdadeiro.

## 0.290 — Peitoril, soleira, puxadores e dobradiças

1. Crie um projeto novo (Ctrl+N). Na aba **Modelagem**, desenhe uma **Parede** de 6 m.
2. Clique em **Janela**. Em **Tipo**, escolha **Janela 120×120 (peitoril 1,00)**. Passe o rato pelo lado de **fora**
   da parede e clique.
3. Clique em **Porta**. Em **Tipo**, escolha **Porta exterior 90×210 (soleira)** e clique no lado de fora da parede.
4. Abra a vista **3D** e aproxime-se pelo lado de fora. Veja:
   - por baixo da janela, o peitoril de pedra a sair 3 cm da parede. Por baixo do peitoril, vista de baixo, a
     pingadeira (o rasgo junto ao nariz);
   - na porta, a soleira de pedra; a folha começa por cima dela;
   - o puxador de alavanca a 1 m do chão e, do lado das dobradiças, as três dobradiças.
5. Vá para o lado de dentro: as duas folhas da janela têm o puxador virado para baixo e as dobradiças nos aros.
6. Clique em **Selecionar** e clique na janela. Nas Propriedades, na linha **Virar a janela**, clique em **Lado**. O
   peitoril passa para a face de dentro e as folhas passam a abrir para fora. Ctrl+Z desfaz.
7. Com a porta selecionada, clique em **Gerador de portas e janelas…** e veja os campos novos:
   - **Soleira (espessura)** e **Saliência para fora da parede**;
   - **Guarnições em**: escolha «a face para onde abre»;
   - **Puxadores e dobradiças**: desligue-o.
   Clique em **OK**. A porta fica com guarnições só de um lado e sem puxadores.
8. Na **Planta**, a soleira da porta aparece como um retângulo atravessado no vão.

## 0.289 — Gerador de portas e janelas

1. Crie um projeto novo (Ctrl+N). Na aba **Modelagem**, desenhe uma **Parede** de 6 m.
2. Clique em **Janela**. Em **Tipo**, escolha **Janela 120×120 (peitoril 1,00)** e clique na parede.
3. Clique em **Selecionar** e clique na janela. Nas Propriedades, por baixo de **Editar tipo**, clique em **Gerador de
   portas e janelas…**.
4. Abre-se a janela do gerador, com o alçado à esquerda: duas folhas de batente, cada uma com duas linhas que se
   encontram do lado das dobradiças.
5. Em **Modelo**, escolha **Batente + oscilobatente**. A folha da direita passa a ter também as linhas que se
   encontram em baixo (oscilobatente).
6. Clique na folha da direita, no alçado: fica marcada a azul e o quadro passa a dizer «Célula 2 da linha 1».
7. Clique em **Dividir**. Aparece um fixo à direita dela.
8. Clique no fixo novo. Em **Largura**, escreva 0,30 e carregue em Enter.
9. Clique em **Linha por cima**. Aparece uma bandeira de vidro fixo por cima das três células.
10. Por baixo dos materiais deve aparecer «No IFC: USERDEFINED (3×1)», sem nenhum aviso a vermelho. Clique em **OK**.
11. A janela na parede é refeita: três vãos (batente, oscilobatente e fixo) com a bandeira por cima. Veja na vista 3D.
12. Na aba **Gerenciar**, clique em **Tipos (criar e editar)**. Na lista de cima escolha **Janelas** e, por baixo,
    **Janela 120×120 (peitoril 1,00)**. O desenho aparece em pequeno, com o botão **Gerador de portas e janelas…** por
    baixo.
13. Abra o gerador outra vez, clique na bandeira e escreva 2,00 em **Altura da linha**. Aparece o aviso a vermelho de
    que as alturas não somam e o OK fica desligado. Apague o valor (fica em branco) e o aviso desaparece.
14. Espelhar: ponha uma **Janela oscilobatente 100×120** numa parede. Selecione a parede e espelhe-a (**Espelhar**,
    na aba **Modelagem**). A janela passa ao tipo «Janela oscilobatente 100×120 (peitoril 1,00) (espelhada)», com as
    dobradiças do outro lado. Espelhe outra vez: volta ao tipo de origem.

## 0.288 — Motor de portas e janelas (passo 1)

1. Abra o programa e crie um projeto novo (Ctrl+N).
2. Na aba **Modelagem**, clique em **Parede** e desenhe uma parede comprida (por exemplo, 16 m).
3. Clique em **Porta**. Na barra por baixo do friso, em **Tipo**, escolha **Porta de 2 folhas 140×210** e clique na
   parede.
4. Ainda com **Porta**, em **Tipo**, escolha **Porta de correr 90×210** e clique noutro ponto da parede.
5. Em **Tipo**, escolha **Porta de sacada 140×220 (vidro)** e clique noutro ponto.
6. Clique em **Janela**. Em **Tipo**, escolha **Janela 120×120 (peitoril 1,00)** e clique na parede. Repita com
   **Janela 150×120 (peitoril 1,00)** e com **Janela oscilobatente 100×120 (peitoril 1,00)**.
7. Abra a vista **3D** e aproxime-se das janelas. Veja:
   - o aro e as folhas em cinzento (alumínio) e o vidro azulado;
   - a janela de 120 tem duas folhas que se encontram ao meio, sem montante;
   - a de 150 tem duas folhas de correr sobrepostas.
8. Aproxime-se das portas de madeira. Têm guarnições nas duas faces da parede, 5 cm para fora do vão.
9. Abra a **Planta** do piso e aproxime-se das portas. Veja:
   - a porta de 2 folhas com as duas folhas abertas e dois arcos;
   - a de correr com uma seta do lado para onde abre;
   - a de sacada com as duas folhas de vidro abertas.
10. Coloque uma **Porta 80×210 + bandeira 50**. Clique em **Selecionar** e clique na porta. Nas Propriedades, na
    linha **Virar a porta**, clique em **Dobradiça**. O tipo passa a «Porta 80×210 + bandeira 50 (à direita)» e a
    bandeira de vidro mantém-se.
11. Selecione uma janela e, nas Propriedades, mude a **Distância ao início da parede** (por exemplo, mais 0,10 m). O
    aro continua com 7 cm de profundidade.
12. Guarde o ficheiro e abra-o noutro programa IFC (por exemplo, o visualizador da buildingSMART). Selecione um tipo
    de porta ou janela e veja:
    - o «Desenho» no ArqSynth_Parametros;
    - as propriedades de aro e folhas (DoorLiningProperties, DoorPanelProperties LEFT…);
    - os materiais Lining / Framing / Glazing.

## 0.287 — Grupos com muitas cópias

1. Abra um projeto com um grupo copiado muitas vezes (por exemplo, `benchmark/modelos/edificio_grande.ifc`: um
   apartamento repetido 1000 vezes).
2. Selecione uma parede de um apartamento e mude a **Altura** nas Propriedades para 3,00 m.
3. Todas as cópias mudam em cerca de 3 s (antes, mais de 8 s).
4. Ctrl+Z desfaz em todas.

## 0.286 — DWG

1. Num projeto novo, abra a planta do piso térreo (navegador: **Plantas ▸ Térreo**).
2. No separador **Início** (ou **Colaborar**), clique em **Ligar um desenho DXF/DWG…**. Na lista de ficheiros aparece
   `*.dxf *.dwg`. Escolha um DWG seu (ou `tests/saida_gui/planta.dwg`, feito pelos testes).
3. O desenho aparece na planta, como um DXF: as paredes, as portas e as cotas, nas camadas do DWG.
4. Clique em **Modelo a partir do desenho…**: as paredes fazem-se como a partir de um DXF.
5. Grave, feche e volte a abrir o projeto: o DWG continua ligado e abre logo, porque a conversão ficou guardada.
6. Num computador sem o ODA File Converter, ligar um DWG mostra uma mensagem a dizer que é preciso o conversor.

## 0.285 — Armaduras agregadas

1. Abra um projeto com estrutura e ponha-lhe as armaduras (separador **Estrutura**, **Verificação EC2 e
   armaduras…**, como no teste da 0.166).
2. Clique numa armadura: as Propriedades e o navegador continuam a mostrá-la no piso do seu elemento.
3. Grave o IFC e abra-o noutro programa (Revit, BIMcollab Zoom, Solibri…). Na árvore, as armaduras aparecem dentro do
   seu pilar ou viga, e não soltas no piso.
4. Mude a secção de uma viga: as armaduras refazem-se e continuam dentro dela.

## 0.284 — Nuvens LAZ e E57

1. Num projeto novo, no separador **Início** (ou **Colaborar**), clique em **Ligar uma nuvem de pontos…**. Na lista
   de tipos de ficheiro aparecem agora `*.laz` e `*.e57`.
2. Escolha um ficheiro LAZ (por exemplo, `tests/saida_gui/sala_digitalizada.laz`, feito pelos testes): a nuvem
   aparece com todos os pontos.
3. Faça o mesmo com um E57 (`tests/saida_gui/sala_digitalizada.e57`, ou um do seu scanner): aparecem todas as
   varreduras, cada uma no seu sítio.
4. As nuvens LAZ e E57 cortam-se nas plantas e gravam-se com o projeto como as outras.

## 0.283 — Medição do desempenho

Nada muda na janela. Para repetir as medições no WSL (demora uns minutos):

```bash
wsl -d Ubuntu-24.04 -u root -- bash -lc "cd /mnt/c/BIM && LD_LIBRARY_PATH=/usr/lib/wsl/lib GALLIUM_DRIVER=d3d12 WGPU_BACKEND_TYPE=OpenGL /opt/arqbim/venv/bin/python -W ignore scripts/benchmark.py --tamanho grande"
```

```bash
wsl -e bash -lc "cd /mnt/c/BIM && /opt/arqbim/venv/bin/python -W ignore scripts/geometry_process.py benchmark/modelos/edificio_grande.ifc"
```

1. O primeiro comando acrescenta uma secção a `benchmark/resultados.md`, com a memória no fim.
2. O segundo escreve uma tabela que compara o motor de geometria no programa e num processo à parte.

## 0.282 — Prolongamentos dos corrimãos

1. Num projeto novo, faça uma escada reta (separador **Arquitetura**, **Escada**) de 2,80 m.
2. Clique em **Guarda** e, na barra de parâmetros, escolha **Nos lados de uma escada** e o tipo **Corrimão de
   parede**. Clique na escada: aparecem dois corrimãos.
3. Olhe para o pé da escada: cada corrimão continua um cobertor para a frente do primeiro degrau, com a mesma
   inclinação, e desce até ao chão. No topo continua 0,30 m de nível para lá do último degrau e desce até ao piso.
4. Clique num corrimão. Nas **Propriedades** há **Prolongamento na base** (o cobertor) e **Prolongamento no topo**
   (0,300 m), e por baixo uma nota com as medidas do DL 163/2006.
5. Escreva 0 no **Prolongamento na base**: o corrimão passa a acabar no primeiro degrau. Ctrl+Z volta atrás.
6. Faça as guardas de outra escada com o tipo **Barras verticais**: é o corrimão de cima da guarda que se prolonga e
   desce ao chão. Os prumos e as barras ficam só ao longo da escada.

## 0.281 — A telha do utilizador

1. Num projeto novo, desenhe uma casa com uma cobertura de quatro águas, como na 0.279.
2. Ao lado da casa, desenhe um retângulo de 0,30 × 0,45 m (separador **Modelagem**, **Retângulo**, escreva 0,30;0,45
   e Enter) e puxe-o 0,02 m para cima (**Push/Pull**, clique no retângulo, escreva 0,02 e Enter).
3. Com o volume selecionado, clique em **Criar componente…** (separador **Modelagem**) e dê-lhe o nome «Telha da
   fábrica».
4. Clique no componente. Nas **Propriedades**, clique em **Usar como telha…**. A janela mostra a medida
   (0,300 × 0,450 × 0,020 m) e propõe a largura útil 0,270 m e a galga 0,360 m.
5. Escreva 3,1 no peso e clique em **Registar**. O rodapé diz que a telha foi registada.
6. Selecione a cobertura. Em **Telha**, no fim da lista, está **Telha da fábrica**. Escolha-a: o telhado faz-se com
   ela, e as linhas dizem quantas telhas há e o peso.
7. Grave o projeto, feche-o e volte a abri-lo: a telha continua na lista.

## 0.280 — Chapas e painéis

1. Faça a casa de 10 × 6 m com a cobertura de quatro águas, como na 0.279. Na Inclinação da cobertura escreva 15°.
2. Selecione a cobertura. Nas **Propriedades**, em **Telha**, escolha **Painel sanduíche**. A cobertura fica com
   painéis de um metro de largura, do beirado ao cimo, cortados nos rincões. As linhas dizem **Painéis** e o peso.
3. Rode a vista: cada painel tem três nervuras por cima, e nos rincões e na cumeeira há as peças de cumeeira.
4. Em **Telha**, escolha **Chapa ondulada**. O telhado refaz-se com chapas onduladas, em fiadas e colunas. As linhas
   dizem **Chapas**.
5. Clique no separador **Navegador de Materiais**, ao lado das Propriedades: aparece **Fibrocimento**, o material das
   chapas.
6. Ctrl+T, **Telhas**: a tabela mostra a chapa ondulada, quantas chapas há e o peso.

## 0.279 — Telhas

1. Num projeto novo, desenhe uma casa de 10 × 6 m com paredes de 20 cm e ponha-lhe uma **Cobertura** de quatro águas
   (separador **Arquitetura**, **Cobertura**, clique dentro da casa).
2. Clique em **Selecionar** e clique na cobertura. Nas **Propriedades**, em **Telha**, deixe **Telha marselha** e
   clique em **Assentar telhas**. O rodapé diz quantas telhas se puseram (cerca de 1450), as telhas de cumeeira e o
   peso.
3. Nas **Propriedades** aparecem as linhas **Telhas** (com as cortadas), **Telhas de cumeeira** e **Peso**, e a
   caixa **Fiadas desencontradas**.
4. Rode a vista à volta da casa: as telhas fazem fiadas do beirado à cumeeira. Junto aos rincões estão cortadas, e
   os rincões e a cumeeira têm telhas de cumeeira de ponta a ponta. Aproxime-se: cada fiada assenta na de baixo.
5. Carregue em Ctrl+T e escolha **Telhas**: aparece a cobertura, a telha, as telhas, as cortadas, as telhas de
   cumeeira, o peso e a área.
6. Em **Telha**, escolha **Telha plana**: o telhado refaz-se com telhas planas, em fiadas desencontradas. Tire o
   visto de **Fiadas desencontradas**: as fiadas ficam alinhadas.
7. Mude a **Inclinação** da cobertura para 40°: as telhas voltam a assentar nela.
8. Clique em **Fazer madeiramento**: a cobertura sobe e as telhas sobem com ela.
9. Clique numa telha: fica selecionado o telhado (em **Revestimentos** no navegador). As Propriedades dizem de que
   cobertura é; **Selecionar a cobertura** volta a ela.
10. Volte à cobertura e clique em **Tirar**, na linha **Telhas**: as telhas desaparecem. Ctrl+Z trá-las de volta.
11. Apague a cobertura: as telhas vão com ela.

## 0.278 — Tipos de cobertura

1. Num projeto novo, desenhe uma casa de 10 × 6 m com paredes de 20 cm.
2. No separador **Arquitetura**, clique em **Cobertura**. Na barra de parâmetros, abra a lista **Tipo**. Aparecem
   **Cobertura de concreto 12 cm**, **Cobertura de concreto 15 cm** e **Telhado de telha cerâmica**, e já não
   aparecem lajes. Deixe a de 15 cm e clique dentro da casa: faz-se a cobertura de quatro águas.
3. Clique em **Selecionar** e clique na cobertura. Nas **Propriedades**, o **Tipo** é uma lista. Escolha **Telhado de
   telha cerâmica**. A cobertura fica fina (3 cm) e continua assente nas paredes: a face de cima desce um
   pouco e a de baixo não mexe.
4. Clique em **Editar tipo…**. Abre o editor de tipos em **Coberturas**, com a camada «Telha cerâmica» de 0,030 m.
   Clique em **Fechar**.
5. Volte a escolher **Cobertura de concreto 15 cm** no Tipo: a cobertura volta a ficar grossa (15 cm).
6. No separador **Gerenciar**, clique em **Tipos**. Na lista de cima escolha **Coberturas** e depois **Cobertura de
   concreto 15 cm**. Mude a espessura da camada para 0,200 m e clique em **Aplicar**: a cobertura da casa fica com
   20 cm.
7. Com a cobertura selecionada, clique em **Fazer madeiramento** (Propriedades ▸ Madeiramento). Depois troque o tipo
   para **Telhado de telha cerâmica**: o madeiramento continua por baixo da telha.
8. Ctrl+Z desfaz cada troca de tipo.
9. Abra um projeto com coberturas feitas antes da 0.278. O Tipo mostra a laje que tinham. Escolha um tipo de
   cobertura na lista e a cobertura passa a tê-lo.

## 0.277 — Medidas do madeiramento e tabela de madeira

1. Faça a casa e o madeiramento como no teste da 0.276 (passos 1 e 2).
2. Com a cobertura selecionada, nas **Propriedades**, em **Madeiramento**, clique em **Medidas…**. Abre uma janela com
   o afastamento dos caibros (0,50 m), a galga da telha (0,350 m), o vão máximo dos caibros (1,500 m) e a largura ×
   altura de cada peça.
3. Mude **Caibros: afastamento** para 0,60 e a altura dos **Caibros** para 0,080 m. Clique em **Aplicar**.
4. Nas **Propriedades**, a linha **Caibros** tem menos peças do que antes. A cobertura subiu um pouco, porque os
   caibros são mais altos.
5. Mude a **Inclinação** da cobertura para 35°: o madeiramento refaz-se e mantém os caibros a 0,60 m.
6. Carregue em Ctrl+T (Tabelas) e escolha **Madeiramento**. Aparece uma linha por peça, com a secção, o número de
   peças, os metros e o volume. Em cima, ao lado do número de elementos, aparece o volume total de madeira.
7. Clique em **Exportar CSV…** e guarde: a tabela abre-se numa folha de cálculo.
8. Ctrl+Z desfaz as medidas: os caibros voltam a 0,50 m.

## 0.276 — Madeiramento da cobertura

1. Num projeto novo, desenhe uma casa de 10 × 6 m com paredes de 20 cm e ponha-lhe uma **Cobertura** de quatro águas
   (Contorno: Pelas paredes). Para uma cobertura de telha, escolha um tipo fino (a laje de 12 cm serve para ver).
2. Clique em **Selecionar** e clique na cobertura. Nas **Propriedades**, em **Madeiramento**, clique em **Fazer
   madeiramento**. O rodapé diz quantas peças se fizeram e o volume de madeira, e a cobertura sobe um pouco.
3. Nas **Propriedades** aparecem as linhas Frechais, Fileira, Varas de rincão, Terças, Caibros e Ripas, cada uma com
   o número de peças, o comprimento e o volume.
4. Carregue em F4 e entre na casa com a vista (ou faça um corte): por baixo da cobertura vê-se a fileira, as varas
   de rincão, as terças, os caibros e as ripas, na cor da madeira, e os frechais em cima das paredes.
5. Mude a **Inclinação** da cobertura para 40°: o madeiramento refaz-se por baixo dela.
6. Clique em **Tirar**: o madeiramento desaparece e a cobertura volta a assentar nas paredes. Ctrl+Z traz tudo de
   volta.
7. Faça o mesmo numa cobertura **Por blocos** em L: aparecem também as varas de laró.

## 0.275 — Coberturas assentes nas paredes

1. Num projeto novo, desenhe uma casa de 10 × 6 m com paredes de 20 cm (separador **Modelagem**, **Parede**).
2. Clique em **Cobertura** (Contorno: Pelas paredes, Quatro águas, 30°) e clique dentro da casa.
3. Carregue em F4 e rode a vista à volta da cobertura: as águas estão limpas, sem a linha que antes aparecia por cima
   de cada parede.
4. Faça um **Corte** pela casa: a face de baixo da cobertura toca na aresta de dentro do topo das paredes, e a parede
   fica toda dentro da cobertura, sem folga.
5. Selecione a cobertura. Nas **Propriedades**, mude a **Inclinação** para 40°: a cobertura continua assente nas
   paredes (a cota do topo sobre as paredes muda sozinha). Mude a **Forma** para **Plana**: fica pousada em cima das
   paredes.
6. Repita com uma cobertura **Por blocos**: cada água também assenta nas paredes.

## 0.274 — Os dados IFC pelo MCP

1. Abra o ArqSynth BIM com a casa de exemplo e ligue **Ligação à IA** (Gerenciar).
2. No Claude, peça: «faz um resumo do modelo com os dados IFC em falta». A resposta diz, por classe, que propriedades
   faltam e em quantos elementos.
3. Peça: «lista os tipos de parede». Aparece uma tabela com cada tipo e quantas paredes tem.
4. Peça: «dá resistência ao fogo EI 60 ao tipo Parede alvenaria 20 cm». Na janela, selecione uma dessas paredes: a
   resistência ao fogo diz EI 60, a cinzento («Do tipo»).
5. Peça outra vez o resumo dos dados em falta: a resistência ao fogo dessas paredes já não falta.
6. Carregue em Ctrl+Z na janela: o tipo volta ao que era.

## 0.273 — Dados IFC em falta, antes de entregar

1. Abra a casa de exemplo (exemplos\casa_exemplo.ifc).
2. No separador **Colaborar**, clique em **Dados IFC em falta…**. Abra **IfcWall**: vê cada propriedade e quantas
   paredes não a têm (por exemplo, a referência em todas, porque este modelo foi feito antes).
3. Clique em **Preencher o que o programa sabe**: a referência e o exterior/interior deixam de estar em falta.
4. Faça duplo clique em **Resistência ao fogo**: as paredes sem ela ficam selecionadas na vista.
5. Nas **Propriedades** (com elas selecionadas), escreva EI 60 na resistência ao fogo. Volte a **Dados IFC em
   falta…**: a resistência ao fogo já não falta.
6. Carregue em Ctrl+Z duas vezes para desfazer.

## 0.272 — Transmissão térmica U calculada

1. Num projeto novo, desenhe uma parede «Parede alvenaria 20 cm» e selecione-a. Em **Dados IFC — Pset_WallCommon**,
   a **Transmissão térmica U** está vazia («—»), porque os materiais ainda não têm λ.
2. No separador **Gerenciar**, clique em **Materiais**. Escolha **Reboco** e escreva 0,80 na condutividade térmica
   (W/m·K); aplique. Escolha **Bloco cerâmico**, escreva 0,35 e aplique. Feche.
3. Selecione a parede: a **Transmissão térmica U** diz 1,477, a azul (calculada).
4. Desenhe uma **Laje** de betão de 15 cm e dê ao **Concreto** a λ 2,0. A laje fica com U = 3,509 (fluxo para baixo).
   Uma **Cobertura** plana com o mesmo tipo fica com 4,651 (fluxo para cima).
5. Escreva 0,5 no U da parede (por exemplo, de um ensaio). Mude a λ do bloco: o U da parede continua 0,5, porque foi
   escrito à mão.

## 0.271 — Dados IFC do tipo

1. Num projeto novo, desenhe três paredes com o tipo «Parede alvenaria 20 cm».
2. Selecione uma parede e, nas **Propriedades**, clique em **Editar tipo…** (ou, no separador **Gerenciar**, clique
   em **Tipos** e escolha a parede de 20 cm).
3. Em baixo está **Dados IFC do tipo — Pset_WallCommon**. Escreva EI 60 em **Resistência ao fogo**, escolha **Sim** em
   **Estrutural (resistente)** e clique em **Aplicar**.
4. Feche o editor e selecione cada parede: a **Resistência ao fogo** diz EI 60, a cinzento («Do tipo»), e o
   **Estrutural** diz Sim.
5. Numa das paredes, escreva EI 30 na resistência ao fogo (fica dela). Volte ao editor de tipos, mude a do tipo para
   EI 90 e aplique: essa parede continua EI 30 e as outras passam a EI 90.
6. Carregue em Ctrl+Z: o tipo volta a EI 60.

## 0.270 — Ligar um assistente de IA com um clique

1. Abra o ArqSynth BIM. No separador **Gerenciar**, clique em **Ligar um assistente de IA…**.
2. Se tem o Claude Desktop, clique em **Pôr no Claude Desktop**. A janela diz «Feito…» e mostra onde ficou a cópia
   do ficheiro antigo. Feche e abra o Claude Desktop.
3. No separador **Gerenciar**, ligue **Ligação à IA**.
4. No Claude Desktop, peça: «usa o ArqSynth para fazer um resumo do modelo aberto». Depois: «desenha uma parede de
   5 m a partir da origem». A parede aparece na janela do ArqSynth BIM.
5. Se usa o Claude Code, clique em **Copiar** na linha do Claude Code e cole-a num terminal. A partir daí, o servidor
   arqsynth-bim está disponível em qualquer pasta.
6. Leia o guia **MCP.md** (na pasta do programa): as ferramentas e os conselhos para gastar poucos tokens.

## 0.269 — Ligação da IA à janela aberta

1. Abra o ArqSynth BIM. No separador **Gerenciar**, clique em **Ligação à IA**: o botão fica carregado e o rodapé diz
   «Ligação à IA ligada…».
2. No Claude Code, com o servidor MCP da 0.268 configurado **sem** `--file` (só `python -m arqbim.mcp`), peça: «desenha
   uma casa de 8 × 5 m». As paredes aparecem na janela aberta, e o rodapé diz «IA: criou…».
3. Peça: «mostra-me as paredes exteriores». As paredes ficam selecionadas e a vista aproxima-se delas.
4. Carregue em Ctrl+Z na janela: a casa da IA desaparece, como uma mudança sua.
5. Clique outra vez em **Ligação à IA** para a desligar. Peça outra coisa à IA: ela responde que o ArqSynth BIM não
   está aberto com a ligação ligada.
6. Feche e abra o programa com a ligação ligada: volta ligada.

## 0.268 — Servidor MCP para ligar a IA

Este passo é para quem já usa o Claude Code ou o Claude Desktop. A instalação simples, com um clique, vem no passo 3
da ligação à IA.

1. No Claude Code, na pasta C:\BIM, escreva: «junta um servidor MCP chamado arqsynth que corre `python -m
   arqbim.mcp --file C:\BIM\exemplos\casa.ifc` na pasta C:\BIM» (pode usar o seu próprio modelo IFC).
2. Peça ao Claude: «faz um resumo do modelo». Deve responder com os pisos, os elementos por classe e os tipos.
3. Peça: «lista as paredes com o comprimento e se são exteriores». Deve mostrar uma tabela.
4. Peça: «desenha uma casa de 8 × 5 m com paredes de 20 cm e uma porta na fachada sul, a 1 m do canto». Depois:
   «grava o modelo».
5. Abra o ficheiro no ArqSynth BIM: as paredes estão ligadas nos cantos, a porta está na parede, e nas
   Propriedades as paredes dizem «Exterior: Sim».

## 0.267 — Exterior ou interior calculado

1. Num projeto novo, no separador **Modelagem**, com a **Parede**, desenhe três lados de uma casa de 10 × 6 m (sem a
   fechar).
2. Clique em **Selecionar** e clique numa das paredes. Em **Dados IFC — Pset_WallCommon**, o **Exterior** diz «Sim»,
   a azul.
3. Feche a casa com a quarta parede e desenhe uma divisória de um lado ao outro, a meio. Selecione a divisória: o
   **Exterior** diz «Não». Selecione a parede da frente: continua «Sim».
4. Ponha uma **Porta** na parede da frente e outra na divisória. Selecione cada uma: a da frente diz «Sim», a da
   divisória diz «Não».
5. Selecione a divisória e escolha «Sim» no **Exterior** (escrito à mão). Desenhe outra parede noutro sítio: a
   divisória continua «Sim». Escolha «—» para voltar ao calculado: volta a «Não».
6. Apague uma das paredes da casa: a divisória passa a «Sim», porque o compartimento abriu. Carregue em Ctrl+Z:
   volta a «Não».

## 0.266 — Cada elemento com os seus dados IFC

1. Num projeto novo, no separador **Modelagem**, clique em **Parede** e desenhe uma parede de 5 m.
2. Clique em **Selecionar** (ou carregue em Espaço) e clique na parede. Nas **Propriedades**, desça até **Dados IFC
   e parâmetros**: está lá o grupo **Dados IFC — Pset_WallCommon**, com todas as propriedades da parede.
3. A **Referência (tipo)** está a azul e diz «Parede alvenaria 20 cm»: foi o programa que a preencheu. Pouse o rato
   em cima de uma propriedade para ver o nome IFC (por exemplo, Pset_WallCommon.FireRating).
4. Na **Resistência ao fogo**, escreva EI 60 e carregue em Enter. Em **Combustível**, escolha **Não**.
5. Nas **Propriedades**, mude o **Tipo** para «Parede alvenaria 15 cm»: a Referência muda sozinha para o novo
   tipo, e a resistência ao fogo continua EI 60.
6. Escreva PE1 na **Referência** e mude outra vez o tipo: a Referência fica PE1, porque foi escrita à mão. Apague o
   PE1 e carregue em Enter: volta o nome do tipo, a azul.
7. Desenhe uma **Porta** na parede e selecione-a: aparece **Dados IFC — Pset_DoorCommon**, com a Referência
   «Porta 80×210» e as propriedades das portas (saída de emergência, fecho automático, corta-fumo…).
8. Grave o projeto e abra-o noutro programa de IFC: a parede leva FireRating = EI 60, Combustible = FALSE e
   Reference.

## 0.265 — Arestas e medições das coberturas por blocos

1. Faça a casa em L e a cobertura por blocos da 0.262 (passos 1 a 4).
2. Clique em **Selecionar** e clique na cobertura. Nas **Propriedades**, por baixo da **Área em planta**, aparecem
   os **Beirados**, as **Cumeeiras**, os **Rincões**, os **Larós** e as **Empenas**, em metros.
3. Carregue em Ctrl+T para abrir as tabelas e escolha **Coberturas**. Há uma linha com a área inclinada, a área em
   planta e os comprimentos de cada tipo de aresta; em baixo, os totais.
4. Clique em **Editar blocos…** nas Propriedades, ponha uma água no lado N da ala e clique em **Aplicar**: a tabela
   e as Propriedades mudam (a ala passa a ter rincões em vez de empenas).
5. Faça também uma cobertura simples (Contorno: Pelas paredes) noutra casa: aparece na tabela **Coberturas** com as
   suas áreas, sem os comprimentos das arestas.

## 0.264 — Pegas dos blocos da cobertura

1. Faça a casa em L e a cobertura por blocos da 0.262 (passos 1 a 4). No passo 3, clique o segundo canto um metro
   antes da parede da direita, em 9,1, 6,1.
2. Clique em **Selecionar** (ou carregue em Espaço) e clique na cobertura. Em cada bloco aparece um quadrado no
   meio de cada lado e um losango no meio do bloco.
3. Arraste o quadrado do lado direito da parte larga até cima da parede da direita e largue. O lado vai até à face
   de fora da parede, e o lado esquerdo não se mexe. O rodapé diz «Bloco 1: lado mudado …».
4. Clique no losango da ala, sem arrastar. Mova o rato um pouco para a direita, escreva 1 e carregue em Enter: a
   ala anda 1 m para a direita.
5. Carregue em Ctrl+Z: a ala volta ao sítio. Carregue outra vez em Ctrl+Z: o lado da parte larga volta a 9,1 m.
6. Clique num quadrado e carregue em Esc: fica tudo como estava.

## 0.263 — Editor de blocos da cobertura

1. Faça a casa em L e a cobertura por blocos dos passos 1 a 4 da 0.262 (parte larga de quatro águas, ala de duas
   águas).
2. Clique em **Selecionar** (ou carregue em Espaço) e clique na cobertura. Nas **Propriedades**, por baixo de
   **Forma: Por blocos (2)**, clique em **Editar blocos…**.
3. Abre a janela **Blocos da cobertura**. À esquerda estão os dois blocos; ao meio, a planta com as águas
   sombreadas; o bloco escolhido está a azul.
4. Na planta, clique na ala (a parte de cima, à direita). Fica escolhida, e à volta aparecem as letras N, E, S e O.
   As letras cheias são águas.
5. Clique na letra **N** da ala. Passa a ser uma água e a **Forma** muda para «Personalizada (lado a lado)». Na
   tabela **Lados do bloco**, escreva 45 na **Inclinação** da linha **N** e carregue em Enter.
6. Escolha o primeiro bloco na lista e clique em **Duplicar**: aparece uma cópia um metro ao lado. Clique em
   **Apagar** para a tirar.
7. Clique em **Aplicar** e depois em **Fechar**. Carregue em F4: a ala tem agora uma água no topo norte (de quatro
   águas, só falta a do lado da parte larga).
8. Carregue em Ctrl+Z: a ala volta a ter só duas águas.

## 0.262 — Coberturas por blocos

1. Num projeto novo, no separador **Modelagem**, clique em **Parede** e desenhe uma casa em L, escrevendo os pontos
   ou clicando na grelha: 0,0 → 10,0 → 10,10 → 6,10 → 6,6 → 0,6 → de volta a 0,0.
2. Clique em **Cobertura**. Na barra de parâmetros, escolha **Contorno: Por blocos** e **Forma: Quatro águas**. O
   rodapé diz «… começa uma cobertura nova».
3. Clique no canto de fora em baixo à esquerda da casa (−0,1, −0,1) e depois no canto de cima à direita da parte
   larga (10,1, 6,1). Aparece uma cobertura de quatro águas sobre a parte larga, com beirado de 0,50 m.
4. Mude a **Forma** para **Duas águas**. O rodapé diz agora «… junta-se a «Cobertura 1»». Clique em 5,9, 4 (dentro
   da parte larga) e depois no canto de fora em cima à direita da ala (10,1, 10,1).
5. Carregue em F4 e rode a vista. A ala tem a cumeeira ao comprido, e entre a ala e a parte larga há um laró.
   É tudo uma só cobertura, e nenhuma parede sai pelo beirado (mesmo que o clique se tenha prendido ao eixo das
   paredes).
6. Clique em **Selecionar** (ou carregue em Espaço) e clique na cobertura. Nas **Propriedades**, a **Forma** diz «Por blocos
   (2)». Mude a **Inclinação** para 40°: os dois blocos ficam mais inclinados.
7. Carregue em Ctrl+Z duas vezes: a inclinação volta a 30° e o segundo bloco desaparece.
8. Com a cobertura ainda selecionada, clique outra vez em **Cobertura** (Por blocos). O rodapé diz «… junta-se a
   «Cobertura 1»». Carregue em Esc sem clicar em nenhum canto: o rodapé diz «O próximo bloco começa outra
   cobertura».

## 0.261 — Guardas de escada contínuos

1. Num projeto novo, no separador **Arquitetura**, desenhe uma **Escada** com **Forma: Em L (patamar)**.
2. Clique em **Guarda**. Na barra de parâmetros, escolha **Por: Nos lados de uma escada** e o **Tipo** **Barras
   verticais**. Clique na escada.
3. Carregue em F4 e veja: há dois guardas, um de cada lado. Cada um sobe pelo primeiro lanço, fica de nível no
   patamar e sobe pelo segundo. O de fora dá a volta às arestas do patamar.
4. Desenhe uma **Escada** **Em U (patamar)** e ponha-lhe guardas do tipo **Cabos de aço**: o guarda de dentro dá a
   volta ao vão entre os dois lanços, e o corrimão de madeira é contínuo.
5. Selecione um dos guardas e veja nas **Propriedades** que é um só guarda; mude o **Tipo de guarda** para **Vidro com
   grampos**: o vidro segue a inclinação dos lanços.
## 0.260 — O editor de tipos de guarda

1. Num projeto novo, no separador **Arquitetura**, clique em **Tipos de guarda…**. Abre-se o editor: os tipos à
   esquerda, e à direita o nome, a amostra e os campos por grupos.
2. Escolha **Cabos de aço** na lista e clique em **Duplicar**: aparece «Cópia de Cabos de aço ★».
3. Mude o **Nome** para «Cabos largos». Em **Enchimento**, mude a **Folga máxima** para 12 cm (escreva «0,12» ou
   «12 cm»). Em **Prumos**, mude a **Forma** para **Redondo**. A amostra muda a cada alteração.
4. Escreva uma medida impossível (por exemplo, «0» na espessura da chapa): aparece um aviso a vermelho e o botão
   **Aplicar** fica apagado. Corrija-a.
5. Clique em **Aplicar** e depois em **Fechar**.
6. Clique em **Guarda**: na barra de parâmetros, **Tipo** já tem «Cabos largos». Desenhe um guarda com ele.
7. Selecione o guarda. Nas **Propriedades**, clique em **Editar tipo…**: o editor abre-se em «Cabos largos». Mude o
   **Material** do corrimão para **Aço inoxidável** e clique em **Aplicar**: o guarda muda.
8. No editor, escolha **Cabos largos** e clique em **Apagar**: é recusado, porque há um guarda desse tipo. Apague o
   guarda e repita: o tipo sai da lista. Ctrl+Z traz o tipo de volta.
## 0.259 — As cores dos guardas no 3D

1. Num projeto novo, no separador **Arquitetura**, clique em **Guarda**, escolha o **Tipo** **Cabos de aço** e desenhe
   um caminho (Enter no fim).
2. Carregue em F4 e aproxime: o corrimão é castanho (madeira), os prumos e os cabos claros (inox).
3. Desenhe outro guarda do tipo **Malha com corrimão de madeira**: a malha e os prumos são pretos e o corrimão é de
   madeira. Outro do tipo **Vidro com grampos**: o vidro aparece azulado.
4. Clique num dos guardas: fica todo na cor da seleção. Clique fora: voltam as cores de cada peça.
5. Grave o projeto, feche-o e volte a abri-lo: as cores aparecem logo.
## 0.258 — Tipos de guarda-corpo

1. Num projeto novo, no separador **Arquitetura**, clique em **Guarda**.
2. Na barra de parâmetros, abra **Tipo** e veja os dez tipos: barras verticais, barras redondas, travessas
   horizontais, cabos de aço, vidro com grampos, vidro encastrado em perfil, chapa cheia, malha, ziguezague e
   corrimão de parede. Escolha **Cabos de aço**: a altura muda para a do tipo.
3. Com **Por: Caminho (clicado)**, clique três pontos no chão (por exemplo, 3 m para um lado e 2 m para o outro) e
   carregue em Enter. Carregue em F4 e aproxime: há prumos com chapa de base, cabos que passam pelos prumos e o
   corrimão por cima.
4. Repita com **Vidro com grampos**: painéis de vidro entre prumos redondos, com dois grampos de cada lado.
5. Repita com **Vidro encastrado em perfil**: vidro contínuo, sem prumos, assente num perfil de base, em painéis com
   junta.
6. Selecione um dos guardas. Nas **Propriedades**, mude **Tipo de guarda** para **Barras em ziguezague**: o guarda é
   refeito com o novo tipo. Mude a **Altura** para 1,10 m: só esse guarda muda.
7. Grave o projeto, feche-o e volte a abri-lo: os guardas mantêm os tipos.
8. As cores de cada material (madeira, vidro, inox) ainda aparecem no 3D na cor dos guardas; vêm na versão seguinte.
## 0.257 — Escadas sem linhas a mais no patamar

1. Num projeto novo, no separador **Arquitetura**, clique em **Escada** e escolha **Forma: Em L (patamar)**. Clique
   no chão onde começa e depois na direção em que sobe.
2. Carregue em F4 e rode a vista para olhar para o patamar a partir do primeiro lanço, como na sua imagem. O topo do
   patamar é uma superfície só, sem a linha do último degrau atravessada, e a frente do patamar não tem faixa.
3. Rode a vista para ver a escada por baixo: a laje do primeiro lanço dobra onde encontra o patamar, sem juntas, e
   o segundo lanço sai do bordo do patamar.
4. Desenhe outra **Escada** com **Forma: Em U (patamar)** e veja o mesmo: o patamar inteiro, com os dois lanços.
5. Numa escada desenhada antes desta versão, mude a largura nas **Propriedades** e volte a pô-la: a escada é
   refeita, já limpa.
## 0.256 — As escadas com laje por baixo dos degraus

1. Num projeto novo, no separador **Arquitetura**, clique em **Escada**. Na barra de parâmetros, deixe **Forma:
   Reta**. Clique no chão onde começa e depois na direção em que sobe.
2. Carregue em F4 e rode a vista para ver a escada de lado, rente ao chão: por baixo dos degraus há agora uma laje
   inclinada, com a espessura do tipo (15 cm na laje de 15), e o pé assenta no chão.
3. Desenhe outra **Escada** com **Forma: Em L (patamar)**. Rode a vista para a ver por baixo: a laje do primeiro lanço sobe
   até encontrar a face de baixo do patamar, e o segundo lanço sai dela. É tudo uma laje só, sem degraus por baixo.
4. Repita com **Forma: Em U (patamar)**: o mesmo, com os dois lanços lado a lado.
5. Numa escada feita antes desta versão, mude qualquer valor nas **Propriedades** (por exemplo a largura) e volte a
   pô-lo: a escada é refeita, já com a laje.
## 0.255 — Abrir um projeto com o ficheiro lateral lido uma vez

1. Abra um projeto seu que tenha folhas, cotas, cortes e esboços (separador **Início**, **Abrir**).
2. Confirme que voltou tudo: as folhas no Navegador do Projeto, as cotas e os textos nas plantas, os cortes, as
   vistas 3D guardadas e a grelha, se a tiver.
3. Feche o programa e abra o mesmo projeto outra vez: deve aparecer igual ou mais depressa do que antes, sobretudo se
   tiver muitos esboços.
4. Os números da medição estão em `benchmark\resultados.md`, no fim (as duas secções de 2026-10-26 13:30 e 13:31).
## 0.254 — O pilar recorta a parede no papel

1. Use o projeto do teste da 0.253 (quatro paredes com um pilar em cada canto) ou faça-o de novo.
2. Ponha também um **Pilar** (separador **Estrutura**) a meio de uma parede comprida.
3. No separador **Início**, clique em **Folhas por pavimento…**, escolha o Térreo e abra a folha.
4. Aproxime um canto: o pilar tem a sua trama inteira, e a trama da parede para à face dele. Há uma linha fina entre
   o pilar e a parede, e a linha grossa passa por fora dos dois.
5. Veja o pilar a meio da parede: o mesmo, com a parede interrompida pela trama do pilar.
6. Abra a planta do Térreo, clique em **Exportar vista em DXF…** (separador **Início**) e veja noutro programa: as
   linhas de trama da parede (camada TRAMAS) não entram nos pilares.
7. Com pilares e vigas no modelo, no separador **Estrutura** clique em **Analisar a estrutura…** e, na janela, em
   **Guardar resultados no IFC**. Repita duas ou três vezes: o programa não fecha, e o painel de Propriedades
   continua a responder.
## 0.253 — O contorno grosso do corte no papel

1. Num projeto novo, no separador **Arquitetura**, desenhe quatro **Paredes** em retângulo (6 × 4 m).
2. No separador **Estrutura**, ponha um **Pilar** em cada canto do retângulo.
3. Ainda em **Arquitetura**, desenhe ao lado uma **Parede** em círculo, com 3 m de raio.
4. No separador **Início**, clique em **Folhas por pavimento…**, escolha o Térreo e abra a folha criada.
5. Veja os cantos com pilares: a linha grossa passa por fora do conjunto parede e pilar, sem desenhar o quadrado do
   pilar por dentro.
6. Veja a parede redonda: tem a linha grossa por fora e por dentro, e a trama só na espessura da parede. A sala
   redonda fica branca.
7. Abra a planta do Térreo e, no separador **Início**, clique em **Exportar vista em DXF…**. Abra o ficheiro noutro
   programa: as linhas de trama (camada TRAMAS) estão só dentro das paredes, e não na sala redonda.
## 0.252 — A fachada de vidro numa parede curva

1. Num projeto novo, no separador **Arquitetura**, desenhe uma **Parede** em arco: um quarto de círculo com 5 m de
   raio.
2. Ainda em **Arquitetura**, clique em **Fachada de vidro**. Clique sobre a parede, mais ou menos a um terço do arco.
   A dica diz «A fachada segue o arco de "Parede 1"».
3. Leve o rato ao longo da parede: a fachada desenha-se a seguir a curva. Clique a dois terços do arco.
4. Carregue em Esc e veja em 3D. A fachada está dentro da parede, com os montantes no arco e os painéis planos entre
   eles. A parede tem o vão aberto.
5. Selecione a fachada. Nas **Propriedades**, mude **Distância ao início da parede** para 1 m: a fachada desliza pela
   curva.
6. Selecione a parede e, nas **Propriedades**, mude **Raio (eixo)** para 6 m. A fachada vai com ela.
7. Volte a selecionar a fachada e desligue **Embutida na parede**: a parede fica inteira. Volte a ligar: o vão abre-se
   de novo.
8. Ainda na fachada, ponha **Distância ao início da parede** maior do que a parede permite: o programa recusa e diz
   que não cabe.
## 0.251 — A cobertura com um perfil desenhado

1. Num projeto novo, desenhe quatro paredes de 10 × 6 m e faça-lhes uma **Cobertura** de duas águas, com 50 cm de
   beiral (separador **Arquitetura**, **Cobertura**, **Contorno: Pelas paredes**, clique dentro).
2. Carregue em F4 (planta). No separador **Conceito**, com a **Linha**, desenhe no chão, fora da casa, uma secção de
   7 m de largura:
   - 7 m para a direita;
   - 0,2 m para cima;
   - em diagonal até 3,5 m da ponta e 1,5 m de altura;
   - em diagonal até 0,2 m de altura na outra ponta;
   - de volta ao início.
   Fica uma face.
3. Selecione a cobertura e, com Shift, a face.
4. No separador **Arquitetura**, clique em **Perfil da cobertura**. Carregue em F4 para ver em 3D: a cobertura tem
   agora a secção desenhada, corrida ao comprido, com 1,50 m no meio e 0,20 m nos bordos.
5. Selecione uma parede comprida e, com Shift, a cobertura. Clique em **Ligar o topo (laje / cobertura)**: o topo da
   parede encosta à parte de baixo da cobertura.
6. Nas **Propriedades** da cobertura, a forma diz «Perfil desenhado». Mude para **Duas águas** e depois outra vez
   para **Perfil desenhado**: volta a secção, sem ter de a desenhar.
7. Selecione só a cobertura e clique em **Perfil da cobertura**: o programa pede a cobertura e uma face.

## 0.250 — A verificação da sapata combinada

1. Faça os dois pilares a 3 m com a sapata combinada da 0.249.
2. Selecione os dois pilares e clique em **Vigas entre pilares** (separador **Estrutura**): fica uma viga no topo.
3. Clique em **Verificação EC2 e armaduras…**. Na lista, clique na sapata combinada. As notas dizem:
   - «sapata combinada sob dois pilares a 3,00 m», com as cargas;
   - a tensão no solo;
   - os momentos ao longo: o positivo junto aos pilares e o negativo entre eles;
   - a malha inferior nos dois sentidos e a **armadura superior ao longo**;
   - o esforço transverso e o punçoamento em cada pilar.
4. Clique em **Pôr as armaduras no modelo**. Selecione a sapata com o Raio-X ligado (nas Propriedades da vista):
   - em baixo, a malha nos dois sentidos;
   - em cima, os varões ao longo, dobrados para baixo nas pontas;
   - os varões dos pilares entram na sapata.
5. À direita, no separador **Projeto**, em **Vistas ▸ Armaduras**, ponha a sapata numa folha nova: no corte C–C
   aparecem os varões de baixo e os de cima.
6. Para ver a falha do solo: em **Ações e materiais…**, ponha o solo com uma tensão admissível baixa (por exemplo
   50 kPa) e volte à verificação. A nota diz para que largura alargar a sapata.

## 0.249 — A sapata combinada

1. Num projeto novo, no separador **Estrutura**, com a ferramenta **Pilar**, ponha dois pilares a 3 m um do outro.
2. Clique em **Sapata**. Na barra de cima, escolha o tipo de sapata isolada de 1,20 × 1,20 e carregue em Esc.
3. Selecione os dois pilares (o primeiro com um clique, o segundo com Shift e clique).
4. Clique em **Sapata combinada** (ao lado de **Sapatas**). Fica uma sapata de 4,20 × 1,20 debaixo dos dois, ao meio
   deles, e selecionada. Carregue em F4 para a ver em 3D.
5. Mova um dos pilares 1 m para longe do outro (ferramenta **Mover**): a sapata acompanha e fica com 5,20, outra vez
   ao meio.
6. Clique em **Modelo analítico** (separador **Estrutura**): os dois pilares aparecem apoiados (encastrados) e não há
   avisos de pilar sem sapata.
7. Selecione só um pilar e clique em **Sapata combinada**: o programa pede dois pilares.

## 0.248 — A tabela de notas-chave do projeto

1. Num projeto novo, desenhe uma parede.
2. No separador **Anotar**, clique em **Notas-chave do projeto…**.
3. Clique em **Acrescentar** e escreva, na linha nova, o código `10.01` e o texto `Painel acústico`.
4. Em **Copiar uma da tabela do programa…**, escolha «02.02 — Alvenaria de tijolo cerâmico 15 cm». Na linha que
   aparece, mude o texto para `Tijolo de 15 (projeto)`.
5. Clique em OK.
6. Selecione a parede. Nas **Propriedades**, em **Nota-chave**, a lista tem «10.01 — Painel acústico» e «02.02 —
   Tijolo de 15 (projeto)», além das do programa. Escolha a 10.01.
7. Abra outra vez **Notas-chave do projeto…**, mude o texto do 10.01 para `Painel acústico perfurado` e clique em
   OK. A nota-chave da parede passa a dizer o texto novo, também na legenda das notas-chave (as tabelas).
8. Carregue em Ctrl+Z: volta o texto antigo.
9. Grave em IFC, feche e abra: a tabela do projeto continua lá.

## 0.247 — Duas águas sobre uma casa em L

1. Num projeto novo, desenhe as paredes de uma casa em L, carregue em F4 (planta) e use a ferramenta **Parede**:
   - 10 m para a direita;
   - 4 m para cima;
   - 6 m para a esquerda;
   - 6 m para cima;
   - 4 m para a esquerda;
   - de volta ao início.
2. No separador **Arquitetura**, clique em **Cobertura**. Na barra de cima, escolha **Forma: Duas águas** e
   **Contorno: Pelas paredes (clique dentro)**.
3. Clique dentro da casa: a cobertura fica feita sobre as paredes. Antes, o programa recusava o L para duas águas.
4. Carregue em F4 para ver em 3D:
   - cada ala tem duas águas, com a cumeeira ao comprido;
   - no canto de dentro há uma laró;
   - no fim de cada ala há uma empena (o triângulo da parede fica por baixo da cobertura).
5. Clique na parede do fim de uma ala (uma empena) e, com Shift, clique também na cobertura. Na barra de cima,
   clique em **Ligar o topo (laje / cobertura)**: o topo da parede sobe em bico até à cobertura.
6. Selecione a cobertura e, nas **Propriedades**, mude a **Forma** para **Quatro águas** e outra vez para **Duas
   águas**: muda sem ser recusada.

## 0.246 — A parede em T com uma curva

1. Num projeto novo, carregue em F4 (planta).
2. No separador **Arquitetura**, clique em **Parede** e, na barra de cima, em **Forma**, escolha **Arco**. Clique no
   início do arco, depois no fim, 6 m ao lado; mova o rato para curvar, escreva `4` (o raio) e carregue em Enter.
3. Volte à **Forma** de linha reta e desenhe uma parede reta de fora para dentro, a acabar no meio da curva
   (clique em cima da parede curva).
4. Carregue em F4 para ver em 3D e aproxime-se da ligação:
   - a parede reta para na face de fora da curva;
   - os dois cantos da ponta tocam a face;
   - não há buraco nem parede a entrar na outra.
5. Selecione a parede curva e, nas **Propriedades**, mude o **Raio** para `4,5`: a parede reta acompanha e
   continua encostada.
6. Desenhe outra parede reta de dentro da curva até ela: para na face de dentro.
7. Desenhe uma parede reta que acabe para lá da ponta do arco: não se liga (fica como a desenhou).
8. Ctrl+Z desfaz cada uma.

## 0.245 — Um perfil desenhado por si

1. Num projeto novo, desenhe as quatro paredes de uma sala de 4 × 3 m e carregue em F4 (planta).
2. No separador **Conceito**, com a **Linha**, desenhe no chão, num canto livre, a secção de um friso em L, fechando
   o contorno no primeiro ponto (fica uma face):
   - 4 cm para a direita;
   - 1 cm para cima;
   - 3 cm para a esquerda;
   - 5 cm para cima;
   - 1 cm para a esquerda;
   - de volta ao início.
   (Escreva as medidas na caixa Medidas: `0,04` Enter, e assim por diante.)
3. Selecione a face (ferramenta **Selecionar**, um clique nela).
4. No separador **Arquitetura**, clique em **Perfil de uma face**. Escreva `Friso L` e clique em OK. A barra de baixo
   diz que o perfil ficou guardado.
5. Clique em **Perfil**. Na barra de cima, em **Perfil**, a seguir a Rodapé, Sanca, Friso e Cimalha, aparece
   **Friso L**: escolha-o.
6. Clique dentro da sala: o friso em L corre à volta dela, encostado às paredes (e cortado nas portas, se as houver).
7. Carregue em F4 para ver em 3D.
8. Selecione o perfil. Nas **Propriedades**, o perfil é «Friso L», com 0,04 de largura e 0,06 de altura. Mude a
   altura para 0,12: fica duas vezes mais alto. Mude o perfil para Rodapé e depois outra vez para Friso L.
9. Clique em **Lista de corte…**: as peças aparecem como «Friso L».
10. Selecione uma parede e clique em **Perfil de uma face**: o programa diz que é preciso uma face plana.

## 0.244 — Os compartimentos de larguras diferentes

1. Num projeto novo, desenhe uma parede de 4 m. Com a ferramenta **Móvel** (separador **Arquitetura**), ponha um
   **Roupeiro** contra ela.
2. Selecione o roupeiro (ferramenta **Selecionar**). Já vem com dois compartimentos (o varão e as prateleiras) e uma
   divisória ao meio; nas **Propriedades**, **Compartimentos** diz 2.
3. Carregue em F4 para o 3D, se ainda não estiver. Com o roupeiro selecionado, a divisória tem uma pega azul na
   frente do corpo, a meia altura.
4. Arraste a pega para a direita: a divisória vai com ela e, ao largar, fica lá. A barra de baixo diz as larguras dos
   dois compartimentos. As prateleiras e o varão acompanham.
5. Carregue em Ctrl+Z: a divisória volta ao meio.
6. Clique na pega (sem arrastar) e mexa o rato um pouco para a direita. Escreva `0,20` e carregue em Enter: a
   divisória anda 20 cm para a direita.
7. Nas **Propriedades**, em **Largura do compartimento 1**, escreva `0,40`: a divisória vai para lá.
8. Tente encostar a divisória a um lado: não passa dos 15 cm de compartimento.
9. Mude **Compartimentos** para 3: as larguras voltam a ser iguais.

## 0.243 — As frentes noutro material e cor

1. Num projeto novo, desenhe uma parede de 4 m e carregue em F4 (planta).
2. No separador **Arquitetura**, clique em **Móvel**. Na barra de cima, em **Acabamento**, escolha **Carvalho**.
3. Passe sobre a face da parede e clique. Carregue em F4: o móvel aparece cor de carvalho.
4. Selecione-o. Nas **Propriedades**, em **Acabamento das frentes**, escolha **Lacado preto**: o móvel fica preto.
   Escolha **Melamina (como o corpo)**: volta à cor de sempre.
5. Faça uma cozinha com a ferramenta **Cozinha** e, na barra, **Acabamento: Lacado cinzento**. Os módulos de baixo e
   de cima saem todos cinzentos, também os dos cantos.
6. No separador **Arquitetura**, clique em **Lista de corte…**: as frentes aparecem como «Frente MDF lacado
   cinzento 18 mm», à parte do «Aglomerado melamínico 18 mm» do corpo.
7. Grave o projeto em IFC e abra-o noutro programa (por exemplo, o Revit): cada móvel tem o material «Aglomerado
   melamínico + MDF lacado cinzento», com os constituintes «Corpo» e «Frentes».

## 0.242 — O forno numa coluna

1. Num projeto novo, desenhe uma parede de 4 m e carregue em F4 (planta).
2. No separador **Arquitetura**, clique em **Móvel**.
3. Na barra de cima:
   - em **Módulo**, escolha **Coluna**;
   - em **Frentes**, escolha **Forno (gavetas, forno, porta)**.
4. Passe sobre a face da parede e clique. Fica uma coluna de 60 cm com:
   - duas gavetas em baixo;
   - o nicho com o forno, com a prateleira a 86 cm do chão;
   - uma porta por cima, com o puxador em baixo.
5. Carregue em F4 para ver em 3D. Selecione o forno: nas Propriedades é o «Forno em coluna».
6. Selecione a coluna e mova-a (ferramenta **Mover**): o forno vai com ela.
7. Nas **Propriedades** da coluna, mude **Frentes** para **Portas**: o forno sai e a coluna fica só com portas.
   Ctrl+Z: o forno volta.
8. Apague a coluna (Delete): o forno sai também. Ctrl+Z traz os dois.
9. Clique em **Eletrodoméstico** (separador **Arquitetura**): na lista há o «Forno» de baixo da bancada, mas não o
   «Forno em coluna».

## 0.241 — As portas de correr

1. Num projeto novo, desenhe uma parede de 4 m e carregue em F4 (planta).
2. No separador **Arquitetura**, clique em **Móvel**.
3. Na barra de cima:
   - em **Módulo**, escolha **Roupeiro**;
   - em **Frentes**, escolha **Portas de correr**.
4. Passe sobre a face da parede e clique: fica um roupeiro de 1,00 m com duas portas de correr.
5. Carregue em F4 para o ver em 3D: uma porta atrás e outra à frente, sobrepostas no meio, com as calhas em cima e
   em baixo. Os puxadores estão nas pontas.
6. Selecione o roupeiro. Nas **Propriedades**:
   1. Mude a **Largura** para 2,40.
   2. Em **Portas**, a escolha vai de 2 a 4: escolha 3. Ficam três portas, a do meio à frente das outras duas.
7. Mude a **Largura** para 2,80: o programa recusa e diz que um roupeiro vai até 270 cm.
8. No separador **Arquitetura**, clique em **Lista de corte…**. As três «Porta de correr» estão nas peças, e o
   conjunto de calhas está nas ferragens, sem dobradiças.
9. Mude **Frentes** para **Portas**: o roupeiro fica com portas de abrir e menos fundo (as calhas saem).

## 0.240 — O canto em L e o carrossel

1. Num projeto novo, desenhe as quatro paredes de uma sala de 5 × 4 m e carregue em F4 (planta).
2. No separador **Arquitetura**, clique em **Cozinha**.
3. Na barra de cima, em **Cantos**, escolha **Em L com carrossel**.
4. Clique na face de dentro da parede de baixo, perto da esquerda. Depois clique no canto de dentro com a parede da
   direita e mais acima nessa parede. Enquanto o rato anda, vê o L do canto desenhado nos dois braços.
5. Carregue em Enter e depois em F4 para ver em 3D. No canto:
   - em baixo, um móvel em L de 90 × 90 cm, com uma porta em cada braço; as duas portas juntam-se no canto de dentro;
   - em cima, um móvel em L de 65 × 65 cm;
   - a bancada cobre os dois braços sem tapar o canto da sala;
   - o troço da parede da direita começa depois do braço do L.
6. Clique num sítio vazio e, nas **Propriedades** da vista, mude o **Estilo visual** para **Raio-X**. Dentro do móvel
   de baixo veem-se os dois tabuleiros do carrossel, em três quartos de círculo, com o quarto que falta virado para
   as portas. Volte ao estilo Sombreado.
7. No separador **Arquitetura**, clique em **Lista de corte…**. Nas ferragens aparece «1 carrosséis de canto», e os
   tabuleiros não vêm na lista das peças.
8. Selecione o móvel de canto de baixo. Nas **Propriedades** aparecem:
   - **Canto em L (braço)**: 0,90;
   - **Lado do canto**: Direita;
   - **Compartimento 1**: Carrossel (canto em L).
   Mude o compartimento para Prateleiras: o carrossel dá lugar a prateleiras em L.
9. Escreva 0 em **Canto em L**: o móvel volta a ser um módulo reto, com prateleiras. Ctrl+Z volta ao L.
10. Faça outra cozinha com **Cantos: Em L**: os cantos em L ficam com prateleiras, sem carrossel.

## 0.239 — O módulo de canto cego

1. Faça uma cozinha em L:
   1. Num projeto novo, desenhe as quatro paredes de uma sala de 5 × 4 m e carregue em F4 (planta).
   2. No separador **Arquitetura**, clique em **Cozinha**.
   3. Clique na face de dentro da parede de baixo, perto da esquerda.
   4. Clique no canto de dentro com a parede da direita e depois mais acima nessa parede.
   5. Carregue em Enter e depois em F4, para ver a cozinha em 3D.
2. Olhe para o canto, de dentro da sala:
   - o último módulo inferior da parede de baixo é agora um **canto cego** de 1,00 m;
   - a parte encostada ao canto (63 cm) é um painel fixo, sem puxador, e por trás dele fica o primeiro módulo da
     outra parede;
   - ao lado do painel há uma porta de 37 cm, com o puxador do lado do painel. Abre para fora do canto e não bate no
     móvel da outra parede.
3. Por cima, o móvel superior do canto também é cego: 80 cm, com 40 cm tapados e uma porta de 40 cm.
4. Selecione o canto cego inferior. Nas **Propriedades** aparecem:
   - **Canto cego (largura tapada)**: 0,63;
   - **Lado do canto**: Direita.
   Mude o lado para Esquerda: o painel e a porta trocam de lado. Ctrl+Z volta.
5. Escreva 0 em **Canto cego**: o móvel volta a ser um módulo de portas normal. Ctrl+Z volta.
6. Num módulo de 60 cm, escreva 0,45 em **Canto cego**: o programa recusa e diz porquê (a porta ficava com menos
   de 25 cm).
7. No separador **Arquitetura**, clique em **Lista de corte…**: o «Painel cego (canto)» aparece com as frentes.

## 0.238 — As etiquetas mudadas à mão

1. Com o pórtico armado da 0.229 (ou o da 0.166), ponha uma viga numa folha nova: à direita, no separador
   **Projeto**, em **Vistas ▸ Armaduras**, clique com o botão direito na viga e escolha **Pôr na folha ▸ Nova
   folha**.
2. Na folha, carregue com o botão esquerdo em cima de uma etiqueta da viga (por exemplo «2 Ø12 — pos. 3 — L = …»)
   e arraste-a para outro sítio. Ao largar, a etiqueta fica lá e o resto da vista não se mexe.
3. Carregue em Ctrl+Z: a etiqueta volta ao sítio onde estava. Ctrl+Y põe-na outra vez onde a largou.
4. Faça duplo clique na etiqueta mudada: volta ao seu sítio de origem.
5. Arraste uma etiqueta e depois carregue em **Atualizar desenhos**: a etiqueta continua onde a pôs (mesmo que as
   armaduras mudem, a etiqueta acompanha a sua posição da lista).
6. Faça o mesmo numa planta de estrutura (**Vistas ▸ Plantas de estrutura**, botão direito no pavimento ▸ **Pôr na
   folha**): as etiquetas «P1 30×30», «V1 20×40» e «L1 h = 0,15» também se arrastam.
7. Arrastar fora das etiquetas continua a mudar a vista inteira de sítio, como antes.
8. Grave (Ctrl+S), feche e abra o projeto: as etiquetas continuam onde as pôs.
9. No separador **Estrutura**, clique em **Memória de cálculo…**: nos desenhos de armaduras, as etiquetas estão onde
   as pôs na folha.

## 0.237 — Os pormenores tipo

1. Comece com o pórtico armado da 0.229 (ou o da 0.166), com as armaduras no modelo.
2. À direita, no separador **Projeto**, abra **Vistas ▸ Armaduras**: o primeiro item é **Pormenores tipo**.
3. Clique nele com o botão direito e escolha **Pôr na folha ▸ Nova folha**. A folha mostra «Pormenores tipo de
   armaduras 1:20» com:
   - à esquerda, o «Nó viga-pilar — V1 / P1»:
     - o pilar e a ponta da viga;
     - os varões de cima e de baixo da viga dobrados para dentro do pilar;
     - os varões do pilar, os estribos e as cintas;
     - as etiquetas com as posições;
     - a cota 0,30 do pilar e a cota da dobra (0,15);
   - à direita, as «Emendas por sobreposição»: uma por diâmetro, por exemplo «Ø12 — l0 = 1,5 × lb,rqd = 0,75 m
     (C25/30, A500)», com a cota 0,75 sobre a parte sobreposta.
4. Mude o betão para C30/37:
   1. No separador **Estrutura**, clique em **Ações e materiais…**, escolha **Betão: C30/37** e clique em OK.
   2. Clique em **Verificação EC2 e armaduras…** e depois em **Pôr as armaduras no modelo**.
   3. Volte à folha e clique em **Atualizar desenhos**. As emendas ficam mais curtas e o texto diz C30/37.
5. No separador **Estrutura**, clique em **Memória de cálculo…**: os pormenores tipo vêm no fim dos desenhos da
   secção 8.

## 0.236 — As marcas dos cortes

1. Com o pórtico armado da 0.229 (ou o da 0.166), ponha uma viga numa folha nova: à direita, no separador
   **Projeto**, em **Vistas ▸ Armaduras**, clique com o botão direito na viga e escolha **Pôr na folha ▸ Nova
   folha**.
2. No alçado da viga, a meio vão, há um traço grosso por cima e outro por baixo, cada um com um «A» ao lado: é por
   ali que passa o «Corte A–A», que está ao lado a 1:20.
3. Faça o mesmo com um pilar: a meia altura, um traço de cada lado, com «B».
4. Com uma sapata: nas duas pontas da planta, a meio, um traço com «C».
5. Com uma laje: não há marcas (a laje não tem corte).
6. Clique em **Exportar PDF…** (na barra da folha), grave e abra o PDF: as marcas saem também.

## 0.235 — A cofragem vista de baixo

1. Comece com o pórtico da 0.229 (ou o da 0.166): pilares, sapatas, vigas e laje.
2. À direita, no separador **Projeto**, abra **Vistas ▸ Plantas de estrutura**. Por baixo do nome do pavimento
   (por exemplo «Térreo») há agora «Térreo — cofragem vista de baixo».
3. Clique com o botão direito em «Térreo — cofragem vista de baixo» e escolha **Pôr na folha ▸ Nova folha**. A folha
   mostra:
   - os pilares cortados, a cheio;
   - as vigas vistas de baixo, cada uma com as suas duas arestas;
   - a laje sem as arestas que ficam atrás das vigas;
   - as etiquetas «P1 30×30», «V1 20×40» e «L1 h = 0,15»;
   - sem sapatas;
   - o nome «Cofragem vista de baixo — Térreo» e a escala por baixo.
4. Ponha a **planta de estrutura** do mesmo pavimento na mesma folha (botão direito em «Térreo» ▸ **Pôr na folha**
   e, no submenu, essa folha) e compare: a planta mostra as sapatas e a laje a tracejado por cima. A cofragem vista
   de baixo fica virada da mesma maneira.
5. Grave, feche e abra o projeto: a folha continua com as duas vistas.

## 0.234 — Os cortes das armaduras a uma escala própria

1. Comece com o pórtico armado da 0.229 (ou o da 0.166), com as armaduras no modelo.
2. À direita, no separador **Projeto**, abra **Vistas ▸ Armaduras**.
3. Clique com o botão direito numa viga e escolha **Pôr na folha ▸ Nova folha**. A folha abre com duas vistas:
   - «Armaduras — Viga 1 1:50»: o alçado com os varões, os estribos e as cotas, sem o corte ao lado;
   - «Corte A–A — Viga 1 1:20»: o corte à parte, com o estribo, os varões cortados e as cotas 0,20 e 0,40.
4. O nome por baixo de cada vista não fica por cima das cotas. Na legenda, a escala diz «1:20 · 1:50».
5. Clique com o botão direito num pilar e escolha **Pôr na folha** e, no submenu, a folha do passo 3: entram o alçado a
   1:50 e o «Corte B–B» a 1:20.
6. Carregue em Ctrl+Z: saem as duas vistas do pilar, juntas.
7. Clique no corte A–A da viga e mude a **Escala da vista** (na barra da folha) para 1:50: só o corte fica mais
   pequeno; o alçado fica como estava.
8. Com uma sapata: a planta a 1:50 e o «Corte C–C» a 1:20. Com uma laje: só a planta (não tem corte).
9. Grave (Ctrl+S), feche e abra o projeto. A folha continua com as vistas das armaduras (antes perdiam-se).
10. No separador **Estrutura**, clique em **Memória de cálculo…** e grave em **HTML**. Na secção 8, cada viga, pilar e
    sapata tem o alçado e, ao lado, o corte.

## 0.233 — A memória de cálculo com os desenhos

1. Comece com o pórtico armado da 0.229 (ou o da 0.166). As armaduras têm de estar no modelo: se não estiverem,
   clique em **Verificação EC2 e armaduras…** (separador **Estrutura**) e depois em **Pôr as armaduras no modelo**.
2. No separador **Estrutura**, clique em **Memória de cálculo…**.
3. Escolha onde gravar, deixe o tipo **HTML** e clique em Gravar.
4. Abra o ficheiro no navegador e desça até à secção 8 (armaduras). Depois da lista de varões vem o título
   «Desenhos de armaduras (1:50)», com um desenho por elemento:
   - primeiro os pilares, depois as vigas, as lajes e as sapatas;
   - cada desenho tem por baixo o nome do elemento;
   - são os mesmos desenhos de **Vistas ▸ Armaduras**, com as cotas.
5. Aproxime (Ctrl e a roda do rato): os traços continuam nítidos.
6. Repita os passos 2 e 3 com o tipo **PDF**.
7. Abra o PDF: os mesmos desenhos estão na secção 8, à mesma escala. Um desenho largo demais fica reduzido à largura
   da folha.

## 0.232 — As cotas nos desenhos de armaduras

1. Com o pórtico armado da 0.229 (ou o da 0.166), à direita, no separador **Projeto**, abra **Vistas ▸ Armaduras**.
2. Clique com o botão direito numa viga e escolha **Pôr na folha ▸ Nova folha**:
   - por baixo da viga, a cota do comprimento;
   - à esquerda, a cota da altura;
   - por cima, o alcance de cada reforço sobre os apoios; por baixo das etiquetas, o do reforço do vão;
   - no corte A–A, a largura e a altura reais da viga.
3. Faça o mesmo com um pilar: a altura ao lado do alçado e os lados no corte B–B (num pilar circular, o diâmetro).
4. Com uma sapata: os dois lados da planta e a altura no corte C–C.
5. Com uma laje: os dois lados maiores.
6. Exporte a folha em PDF e em DXF: as cotas aparecem nos dois.

## 0.231 — As armaduras nos pisos tipo

1. Faça um pórtico de 6 × 4 m em dois pavimentos:
   1. No separador **Gerenciar**, clique duas vezes em **Novo pavimento**: ficam «Piso 1» (3,00 m) e «Piso 2»
      (6,00 m).
   2. No pavimento de baixo, ponha quatro pilares 30×30, **Sapatas sob pilares**, **Vigas entre pilares** e **Lajes
      nos vãos**.
   3. Passe ao «Piso 1» (PgUp) e ponha lá os quatro pilares, as vigas e a laje.
2. Com o «Piso 1» ativo, clique em **Pavimentos iguais (piso tipo)…** (separador
   **Gerenciar**), marque o «Piso 2» e clique em **OK**:
   o «Piso 2» fica igual ao «Piso 1».
3. Clique em **Verificação EC2 e armaduras…**.
4. Clique num pilar do «Piso 1» e depois no mesmo pilar do «Piso 2»:
   - os dois têm a mesma armadura;
   - a nota diz «piso tipo: a mesma armadura nos 2 elementos iguais — a do mais esforçado deles».
5. Os pilares do pavimento de baixo não têm essa nota: ficam com a sua armadura.
6. Clique em **Pôr as armaduras no modelo**: os pilares, as vigas e as lajes dos dois pisos tipo ficam com varões
   iguais.

## 0.230 — As emendas dos varões compridos

1. Num projeto novo, desenhe uma parede de 15 m (**Parede**).
2. No separador **Estrutura**, clique no botão **Sapata**, deixe em **Corrida** a «Sapata corrida 50×30» e clique na
   parede: fica uma sapata corrida de 15 m debaixo dela.
3. Clique em **Verificação EC2 e armaduras…**: a sapata corrida aparece calculada, mesmo sem pilares nem vigas.
4. Clique em **Pôr as armaduras no modelo** e feche.
5. Abra a **Lista de armaduras…** (separador **Estrutura**): os varões longitudinais da sapata aparecem em troços de
   menos de 12 m, e o comprimento total conta as sobreposições.
6. Com nada selecionado, nas **Propriedades** mude o **Estilo visual** para **Raio-X** e aproxime-se de uma emenda:
   os dois troços sobrepõem-se, encostados um ao outro.

## 0.229 — A dispensa de varões nas vigas

1. Faça o pórtico de 8 × 5 m da 0.226 (pilares 30×30, **Sapatas sob pilares**, vigas «Viga de concreto 20×50» com
   **Vigas entre pilares**, **Lajes nos vãos**).
2. Selecione a laje e, nas **Propriedades**, em **Uso (sobrecarga)**, escolha «C3 — sem obstáculos: museus, átrios
   (5,0)».
3. Clique em **Verificação EC2 e armaduras…** e clique numa viga de 8 m. As notas dizem, por exemplo:
   - «dispensa face inferior: 2 Ø20 de ponta a ponta, mais 1 só onde precisos — 1,59–6,41 m desde o início…»;
   - «dispensa face superior: … 0,00–1,32; 6,68–8,00 m…».
4. Clique em **Pôr as armaduras no modelo** e feche.
5. Abra a **Lista de armaduras…**: a viga tem varões inferiores de dois comprimentos (8,72 m e 4,82 m) e superiores
   de dois (8,63 m e 1,64 m).
6. À direita, no separador **Projeto**, abra **Vistas ▸ Armaduras**, clique com o botão direito na viga e escolha
   **Pôr na folha ▸ Nova folha**: no alçado, o varão de baixo mais curto fica a meio do vão, e os de cima mais
   curtos sobre os apoios.

## 0.228 — Os maciços de estacas e as sapatas corridas

1. Ponha quatro pilares «Pilar de concreto 30×30» nos cantos de um retângulo de 6 × 4 m (separador
   **Estrutura**, botão **Pilar**).
2. Clique no botão **Sapata** (separador **Estrutura**). Na barra de cima, em **Isolada**, escolha «Bloco de 2
   estacas 150×60×60» e clique em dois pilares: cada um fica num maciço com as suas duas estacas.
3. Em **Isolada**, escolha «Bloco de 4 estacas 150×150×70» e clique nos outros dois pilares.
4. Clique em **Vigas entre pilares** e em **Lajes nos vãos**.
5. Desenhe uma parede de 5 m ao lado do pórtico (**Parede**). Volte a **Sapata**, deixe em **Corrida** a «Sapata
   corrida 50×30» e clique na parede: fica uma sapata corrida ao longo dela.
6. Clique em **Verificação EC2 e armaduras…**.
7. Clique num maciço de 2 estacas:
   - as notas dizem a carga por estaca e o ângulo das bielas;
   - também mostram as tensões no nó sob o pilar e sobre a estaca, cada uma com o seu limite;
   - por fim, o tirante com a sua armadura.
8. Clique num maciço de 4 estacas: há um tirante em X e outro em Y.
9. Clique na sapata corrida: a nota diz a carga por metro (a parede e a sapata), a pressão no solo e as armaduras
   transversal e longitudinal.
10. Clique em **Pôr as armaduras no modelo**: os maciços e a sapata corrida ficam com as suas malhas (veja-as em
    **Raio-X**).

## 0.227 — Os pilares circulares, em L e em T

1. Faça um pórtico de 6 × 4 m com um pilar de cada forma:
   1. No separador **Estrutura**, clique no botão **Pilar**. Na barra de cima, em **Tipo**, escolha «Pilar circular
      Ø30» e clique no canto (0; 0).
   2. Mude o tipo para «Pilar em L 40×40 (15)» e clique no canto (6; 0); depois «Pilar em T 50×40 (15)» no canto
      (6; 4); e «Pilar de concreto 30×30» no canto (0; 4). Carregue em Esc.
   3. Clique em **Sapatas sob pilares**, **Vigas entre pilares** e **Lajes nos vãos**.
2. Clique em **Verificação EC2 e armaduras…**. Os quatro pilares aparecem verificados.
3. Clique no pilar circular: as notas dizem «secção circular: diagrama N–M por fibras…», e a armadura tem pelo menos
   6 varões. Faça o mesmo com o L e o T.
4. Clique em **Pôr as armaduras no modelo** e feche.
5. Com nada selecionado, nas **Propriedades** mude o **Estilo visual** para **Raio-X**:
   - no pilar circular, os varões estão à volta do eixo e as cintas são redondas;
   - no pilar em L, cada braço tem a sua cinta.
6. À direita, no separador **Projeto**, abra **Vistas ▸ Armaduras**, clique com o botão direito no pilar circular e
   escolha **Pôr na folha ▸ Nova folha**: o corte B–B é um círculo, com os varões à volta.

## 0.226 — A segunda camada de varões nas vigas

1. Faça um pórtico de 8 × 5 m:
   1. No separador **Estrutura**, clique no botão **Pilar** (tipo «Pilar de concreto 30×30») e ponha quatro
      pilares nos cantos de um retângulo de 8 × 5 m.
   2. Clique em **Sapatas sob pilares**.
   3. Clique no botão **Viga** e, na barra de cima, em **Tipo**, escolha «Viga de concreto 20×50». Carregue em Esc
      e clique em **Vigas entre pilares**.
   4. Clique em **Lajes nos vãos**.
2. Selecione a laje e, nas **Propriedades**, em **Uso (sobrecarga)**, escolha «E1 — armazenagem (7,5)».
3. Clique em **Verificação EC2 e armaduras…** (separador **Estrutura**). As duas vigas de 8 m dizem, na coluna da
   armadura, «inf. 6 Ø16 (3 + 3)».
4. Clique numa delas: a nota diz que os varões não cabem numa camada, quantos ficam em cada uma e a altura útil.
5. Clique em **Pôr as armaduras no modelo** e feche.
6. Com nada selecionado, nas **Propriedades** mude o **Estilo visual** para **Raio-X** e aproxime-se de uma viga de
   8 m: em baixo há três varões, e por cima deles mais três.
## 0.225 — O programa mais leve e a barra de parâmetros fixa

1. Abra um projeto grande (por exemplo `C:\BIM\benchmark\modelos\edificio_medio.ifc`).
2. Clique em várias ferramentas seguidas, na fita: **Parede**, **Porta**, **Pilar**, **Laje**, **Cota** e
   **Selecionar**. A barra de parâmetros por baixo da fita fica sempre com a mesma altura, e a vista 3D não salta.
3. Com **Selecionar**, clique numa parede. As **Propriedades** e as cotas temporárias aparecem quase de imediato.
   A primeira seleção depois de abrir o ficheiro demora um pouco mais; as seguintes são rápidas.
4. Escolha **Parede** e desenhe algumas paredes junto do prédio. O fantasma acompanha o rato sem solavancos, e
   cada clique faz a parede logo.
5. Selecione uma parede e mude-lhe a altura nas **Propriedades**. A vista muda de imediato.
6. Mova uma parede (**Mover**, separador **Modelagem**). O movimento é rápido.
7. Faça Ctrl+Z e Ctrl+Shift+Z algumas vezes. Desfazer e refazer são imediatos.

## 0.224 — A armadura superior das lajes sobre os apoios

1. Faça o pórtico com laje do teste 0.223 (quatro pilares 30×30 num retângulo de 6 × 4 m, **Sapatas sob pilares**,
   **Vigas entre pilares**, **Lajes nos vãos**).
2. No separador **Estrutura**, clique em **Verificação EC2 e armaduras…**.
3. Na linha da **Laje 1**, a coluna dos varões diz «malha inf. Ø…//… × Ø…//… · sup. Ø…//… × Ø…//…».
4. Clique na linha da laje: em baixo aparecem duas notas «armadura superior sobre os apoios», uma para cada
   direção, com o momento, o quarto do vão, a área e a malha. A última nota diz até onde vão os varões.
5. Clique em **Pôr as armaduras no modelo**.
6. Feche o diálogo. Com nada selecionado, nas **Propriedades** mude o **Estilo visual** para **Raio-X** e rode a
   vista (F8): por cima das vigas há varões curtos atravessados. Nas bordas, dobram para baixo, para dentro da viga.
7. Clique num desses varões: as **Propriedades** dizem «armadura superior X sobre os apoios» (ou Y).
8. Clique em **Lista de armaduras…** (separador **Estrutura**): há posições «superior X» e «superior Y».
9. À direita, no separador **Projeto**, abra **Vistas ▸ Armaduras**, clique com o botão direito na laje e escolha
   **Pôr na folha ▸ Nova folha**: os varões superiores aparecem com traço mais grosso e a etiqueta diz «sup.».

## 0.223 — As lajes como cascas

1. Faça o pórtico com laje:
   1. No separador **Estrutura**, clique no botão **Pilar** (tipo «Pilar de concreto 30×30») e ponha quatro pilares
      nos cantos de um retângulo de 6 × 4 m.
   2. Clique em **Sapatas sob pilares**, depois em **Vigas entre pilares** e depois em **Lajes nos vãos**.
2. Clique em **Ações e materiais…** (separador **Estrutura**). À esquerda, em **Lajes no cálculo**, está
   «Cascas (elementos finitos)». Abra a lista: a outra escolha é «Áreas de influência (cargas às vigas)». Deixe
   «Cascas» e clique em **OK**.
3. Clique em **Analisar a estrutura…**: no fim da tabela das barras aparece a linha da **Laje 1**.
   - Em **M vão** estão os momentos da face de baixo («x … / y …», em kNm por metro).
   - Em **M apoio** estão os da face de cima.
   - Em **Flecha** está a flecha em mm e em L/….
4. Passe o rato por cima da linha da laje: a dica explica que a laje foi calculada como casca, com triângulos DKT,
   e diz o passo da malha (0,50 m).
5. Feche o diálogo. Clique em **Verificação EC2 e armaduras…** e escolha a laje: a nota diz «momentos da laje
   calculada como casca (Wood–Armer)», com os momentos que entraram no cálculo da malha.
6. Volte a **Ações e materiais…**, escolha «Áreas de influência (cargas às vigas)» e clique em **OK**. Analise outra
   vez: a laje já não aparece, e os momentos das vigas mudam (as cargas vão às vigas por áreas).
7. Grave o projeto, feche-o e volte a abri-lo: em **Ações e materiais…** continua a escolha que deixou.
8. Clique em **Memória de cálculo…**: no capítulo 5 a laje aparece na tabela da análise (com «Cascas»), com a nota
   do método por baixo.

## 0.222 — A 2.ª ordem

1. Faça uma torre de três pisos com pilares finos:
   1. No separador **Estrutura**, clique no botão **Pilar** e, na barra de cima, em **Tipo**, escolha «Pilar de
      concreto 20×20», altura 3,00. Ponha quatro pilares nos cantos de um retângulo de 6 × 4 m.
   2. Clique em **Sapatas sob pilares** (separador **Estrutura**).
   3. Clique em **Vigas entre pilares**: ficam as quatro vigas a 3,00 m.
   4. Clique em **Lajes nos vãos** para pôr a laje de 6 × 4 m por cima.
   5. No separador **Gerenciar**, clique duas vezes em **Novo pavimento**: ficam pavimentos a 3,00 m e a 6,00 m.
   6. Carregue duas vezes em PgDown para voltar ao pavimento de baixo. Selecione os quatro pilares, as quatro vigas e
      a laje (as sapatas não) e clique em **Repetir nos pavimentos…** (separador **Gerenciar**). Marque os dois
      pavimentos novos e clique em **OK**: fica uma torre de três pisos, até 9,00 m.
2. Clique em **Analisar a estrutura…** (separador **Estrutura**).
3. No diálogo, por baixo da tabela das barras, há uma tabela nova com uma linha por piso e por ação (vento X,
   vento Y, sismo X, sismo Y): P, V, a deriva dr, o θ e, na última coluna, o que esse θ pede.
4. Veja que o θ é maior no piso de baixo e diminui para cima. Quando passa de 0,10, aparece a laranja e diz
   «× 1/(1 − θ)».
5. Leia o texto de cima: no fim diz «2.ª ordem: θ máximo …», onde está o pior piso, e por quanto ficou multiplicada
   cada ação (por exemplo «sismo X × 1,14»).
6. Passe o rato por cima da tabela dos pisos: a dica explica como se calcula o θ e os artigos dos Eurocódigos.
7. Feche o diálogo. Selecione os pilares todos e, nas **Propriedades**, mude o tipo para «Pilar de concreto 30×30».
   Analise outra vez: o θ desce e as ações deixam de ser multiplicadas (ou são menos).
8. Clique em **Memória de cálculo…** (separador **Estrutura**): no capítulo 5 está a mesma frase e a tabela dos
   pisos, com a explicação por baixo.
9. Num edifício de vários pisos, clique em **Modelo analítico e verificação…**: os apoios (os nós encastrados) estão
   só nas sapatas, já não a meio dos pisos de cima.

## 0.221 — Os resultados da análise no IFC

1. Num projeto com estrutura, clique em **Analisar a estrutura…** (separador **Estrutura**).
2. No diálogo, clique em **Guardar resultados no IFC**: o texto de cima acrescenta «Resultados guardados no IFC.» e
   a barra de baixo diz quantas barras e apoios.
3. Grave o projeto e abra o IFC num programa de estruturas ou num visualizador de IFC (por exemplo, o BIMcollab ZOOM
   ou o FreeCAD): no modelo analítico há o grupo de resultados «1,35G+1,50Q», com as reações dos apoios e os momentos
   das barras.
4. Ctrl+Z tira os resultados.

## 0.220 — Os diagramas de momentos

1. Num projeto com estrutura (pilares, vigas, laje), abra o separador **Estrutura** e clique em **Diagramas de
   momentos**.
2. Sobre o modelo aparecem, a vermelho, os diagramas de momentos de cada viga e pilar. Nas vigas, o positivo (a meio
   vão) fica por baixo e o negativo (nos apoios) por cima. Em cada barra está escrito o seu maior valor.
3. A barra de baixo diz «Diagramas de momentos (1,35G+1,50Q) de N barras; o maior … kNm».
4. Rode a vista (F8) para ver os diagramas dos pilares.
5. Clique outra vez no botão: os diagramas saem.
## 0.219 — As categorias de terreno do vento do Anexo Nacional

1. Num projeto com estrutura, clique em **Ações e materiais…** (separador **Estrutura**).
2. Abra a lista **Vento: categoria do terreno**: tem quatro, I a IV, cada uma com a sua descrição («I — zona costeira
   exposta aos ventos de mar»…). Já não há a categoria 0.
3. Mude de III para I: as forças do vento na tabela sobem (na costa o vento é mais forte).
4. Um projeto antigo que tivesse a categoria 0 abre com a I.
## 0.218 — O uso por laje

1. Num projeto com estrutura e lajes, clique numa laje: no painel **Propriedades** há a linha **Uso (sobrecarga)**,
   com «O do projeto (Ações e materiais)».
2. Escolha «E1 — armazenagem (7,5)».
3. Clique em **Ações e materiais…** (separador **Estrutura**): na tabela, a sobrecarga (Q) e o peso sísmico do piso
   dessa laje sobem.
4. Volte à laje e escolha «O do projeto»: os valores voltam ao que eram.
5. Ctrl+Z desfaz a mudança do uso.
## 0.217 — A neve

1. Num projeto com estrutura (pilares, vigas e laje de cobertura), clique em **Ações e materiais…** (separador
   **Estrutura**).
2. Na janela, escolha **Neve: zona** «Z1 (Cz 0,30)» e escreva `1000` na **Altitude do local**.
3. Por baixo da tabela aparece a neve: «sk = 1,50 kN/m² no solo, 1,20 kN/m² na cobertura», e a cobertura com
   1,20 kN/m². Na tabela, a sobrecarga (Q) do piso da cobertura sobe.
4. Ponha a altitude a `0`: a cobertura volta a ter a sobrecarga do seu uso (0,40 kN/m²), porque a neve (0,24) é
   menor.
5. Clique em **OK** e abra a **Memória de cálculo…** (separador **Estrutura**): na secção das ações há a linha da
   neve.
## 0.216 — Splats a partir da nuvem de pontos

1. Ligue uma nuvem de pontos (separador **Início ▸ Ligar uma nuvem de pontos…**).
2. No separador **Render**, clique em **Gaussian splat**, escolha a distância (por exemplo «Média — 5 cm») e o
   ficheiro.
3. O programa pergunta se junta as nuvens de pontos ligadas: responda **Sim**.
4. Abra o PLY num visualizador de splats (por exemplo, SuperSplat no navegador): aparece a nuvem com as suas cores,
   junto com o modelo, se houver.
5. Repita respondendo **Não**: só vai o modelo.
## 0.215 — Paredes curvas a partir da nuvem

1. Ligue a nuvem de pontos de um espaço com uma parede curva (separador **Início ▸ Ligar uma nuvem de pontos…**).
2. Clique em **Modelo a partir da nuvem…** (separador **Massa e Estudos**): a janela diz «Destas, N curvas», e na
   planta a parede curva aparece a azul, em arco.
3. Clique em **OK**: a parede curva fica feita com as outras.
4. Clique nela: no painel **Propriedades** está o **Raio**.
5. Uma fachada curva vista só de dentro fica com a espessura de «parede vista de um lado», para fora.
## 0.214 — Vários pisos de uma vez a partir da nuvem

1. Ligue a nuvem de pontos de um edifício com dois pisos (separador **Início ▸ Ligar uma nuvem de pontos…**).
2. Clique em **Modelo a partir da nuvem…** (separador **Massa e Estudos**): a caixa **Todos os pisos de uma vez (2:
   chão a 0,00 / 3,05 m)** vem marcada, e a janela diz as paredes «Em 2 pisos».
3. Clique em **OK**: no painel **Pavimentos** aparece o pavimento novo à cota do chão de cima, e cada piso tem as suas
   paredes, portas, janelas e laje.
4. Ctrl+Z tira tudo de uma vez (também o pavimento novo).
5. Para fazer só um piso, desmarque a caixa e escreva a cota do chão e a altura desse piso.
## 0.213 — Os vãos lidos na nuvem de pontos

1. Ligue uma nuvem de pontos de uma sala com portas e janelas (separador **Início ▸ Ligar uma nuvem de pontos…**).
2. Clique em **Modelo a partir da nuvem…** (separador **Massa e Estudos**): além das paredes, a janela diz «Nos vãos:
   N portas e M janelas».
3. Clique em **OK**: as paredes ficam feitas com as portas e as janelas nos sítios dos vãos da nuvem. A barra de
   baixo diz quantas.
4. Selecione uma janela: no painel **Propriedades**, o tipo tem a largura, a altura e o peitoril medidos na nuvem.
5. Ctrl+Z tira tudo de uma vez.
## 0.212 — A altura dos vãos lida dos textos do desenho

1. Num programa de CAD, numa planta com paredes em linhas duplas e portas e janelas em blocos, escreva ao lado de
   uma porta «0,90x2,20» e ao lado de uma janela «1,20x1,10 pt 0,95»; grave em DXF.
2. No ArqSynth BIM, ligue o DXF (separador **Início ▸ Ligar um desenho DXF…**) e clique em **Modelo a partir do
   desenho…** (separador **Massa e Estudos**): a janela diz «2 vãos com as medidas escritas ao lado».
3. Clique em **OK**. Selecione a porta: no painel **Propriedades**, o tipo é «Porta 90×220» (2,20 m de altura).
4. Selecione a janela: o tipo é «Janela 120×110 (peitoril 0,95)».
5. Um vão sem medidas escritas ao lado fica com as de sempre (porta com 2,10 m, janela com 1,20 m sobre 1,00 m).
## 0.211 — Pilares a partir do desenho

1. Num programa de CAD, desenhe numa camada PILARES uns pilares: retângulos fechados (polilinha fechada) de
   30 × 30 cm e um círculo de 30 cm de diâmetro; grave em DXF.
2. No ArqSynth BIM, abra a planta (F4) e ligue o DXF (separador **Início ▸ Ligar um desenho DXF…**).
3. Clique em **Modelo a partir do desenho…** (separador **Massa e Estudos**): na lista **Pilares (retângulos e
   círculos)** a camada PILARES já vem marcada. A janela diz quantos pilares encontrou, e na planta aparecem a azul.
4. Clique em **OK**: os pilares ficam feitos, com a altura das paredes da janela.
5. Clique num pilar: o painel **Propriedades** mostra o tipo («Pilar de concreto 30×30», «Pilar circular Ø30»).
6. Ctrl+Z tira tudo de uma vez.
## 0.210 — Paredes curvas a partir do desenho

1. Num programa de CAD, desenhe numa camada PAREDES uma parede curva com dois arcos à volta do mesmo centro (por
   exemplo, raios de 3,00 e 3,20 m) e uma parede reta com duas linhas; grave em DXF.
2. No ArqSynth BIM, abra a planta (F4) e ligue o DXF (separador **Início ▸ Ligar um desenho DXF…**).
3. Clique em **Modelo a partir do desenho…** (separador **Massa e Estudos**): a janela diz quantas paredes
   encontrou e quantas são curvas; na planta aparecem a azul, as curvas em arco.
4. Clique em **OK**: aparecem a parede reta e a curva, ligadas onde se tocam.
5. Clique na parede curva: no painel **Propriedades** está o **Raio** (3,10 m).
6. Ctrl+Z tira as duas de uma vez.
## 0.209 — Recortar a imagem de fundo

1. Importe uma imagem de fundo e abra a planta do seu pavimento (F4).
2. Separador **Visualizar ▸ Imagens de fundo…**: escolha a imagem e clique em **Recortar**. O diálogo fecha e a
   imagem fica com o contorno desenhado.
3. Clique em cima da imagem num canto da parte que quer manter; leve o rato: aparece o retângulo dessa parte.
4. Clique no canto oposto: só essa parte fica à vista.
5. Exporte em PDF (Ctrl+P): no papel também só aparece essa parte.
6. Volte a **Imagens de fundo…**, escolha a imagem e clique em **Inteira**: a imagem aparece toda outra vez.
7. Ctrl+Z desfaz cada passo.
## 0.208 — Uma imagem numa fachada

1. Desenhe uma parede comprida e importe a fotografia de uma fachada (separador **Início ▸ Importar imagem de
   fundo…**).
2. Separador **Visualizar ▸ Imagens de fundo…**: escolha a fotografia e clique em **Pôr numa fachada**. O diálogo
   fecha.
3. Rode a vista até ver a parede de frente (por exemplo, clique na face **FRENTE** do cubo de vistas).
4. Clique na face da parede onde fica o canto de baixo à esquerda da fotografia; leve o rato para a direita: aparece
   o contorno da fotografia de pé, com a largura na caixa **Medidas**.
5. Clique onde fica o canto de baixo à direita (ou escreva a largura, por exemplo `8,00`, e Enter): a fotografia
   fica de pé na parede.
6. Abra o **Alçado Sul** (ou o do lado onde a pôs): a fotografia está lá. Exporte em PDF (Ctrl+P): também vai.
7. Ctrl+Z volta a deitar a imagem como estava.
## 0.207 — A imagem de fundo nas folhas

1. Importe uma imagem de fundo (separador **Início ▸ Importar imagem de fundo…**) e desenhe umas paredes por cima.
2. Abra a planta do pavimento (F4) e carregue em Ctrl+P (**Exportar vista em PDF…**): no PDF, a imagem está por
   baixo das paredes, com a mesma transparência do ecrã, cortada ao tamanho do desenho.
3. Ponha a planta numa folha: na folha também aparece a imagem.
4. Separador **Visualizar ▸ Imagens de fundo…**: na coluna **Visível**, desmarque a imagem e volte a exportar: a
   imagem já não vai.
5. Exporte em DXF (**Exportar vista em DXF…**): na camada IMAGENS está o contorno da imagem e o nome do ficheiro.
## 0.206 — Offset de faces em L e Escala a partir do centro

1. Separador **Massa e Estudos**: com a ferramenta **Linha**, desenhe no chão uma face em L (seis cantos, fechada).
2. Escolha **Offset**, clique dentro do L e leve o rato para dentro: aparece o L mais pequeno. Escreva `0,25` e
   Enter: o L divide-se no L interior e numa moldura à volta.
3. Com **Push/Pull**, puxe o L interior: só ele sobe.
4. Ctrl+Z duas vezes. Escolha **Offset** outra vez e escreva uma distância grande (por exemplo `0,8` num braço com
   1,5 m): aparece a mensagem de que essa distância muda a forma da face.
5. Desenhe um retângulo de 3 × 2 m e selecione-o. Escolha **Escala** e toque em Ctrl (carregue e largue): a barra de
   cima marca **A partir do centro**.
6. Escreva `2` e Enter: o retângulo fica com 6 × 4 m e o mesmo centro.
7. Toque outra vez em Ctrl: a escala volta a pedir o ponto base.
## 0.205 — Rampas de acesso entre plataformas

1. Num terreno inclinado, faça duas plataformas afastadas uma da outra (separador **Terreno ▸ Plataforma**), a cotas
   diferentes: por exemplo, uma em baixo e outra uns metros acima.
2. Abra a planta (F4). No separador **Terreno**, clique em **Rampa de acesso**.
3. Na barra de cima, escolha a **Largura** (por exemplo 3,00 m).
4. Clique na borda da plataforma de baixo, no meio de onde a rampa sai.
5. Leve o rato até à borda da outra plataforma: a barra de baixo vai dizendo as cotas das pontas, o comprimento e
   a inclinação.
6. Clique: a rampa fica feita, com o texto «+cota / +cota · inclinação %» na planta e os seus taludes à volta.
7. Rode a vista (F8): a rampa sobe de uma plataforma à outra, em plano inclinado.
8. Ctrl+Z tira-a.
## 0.204 — Editar uma plataforma

1. Num terreno com uma plataforma (veja o teste da 0.203), abra a planta (F4).
2. Clique no terreno para o selecionar: na barra de cima aparece **Editar plataforma** (também está no separador
   **Terreno**). Clique nele: os quatro cantos da plataforma ficam com pegas (quadrados), e o meio de cada lado com
   um losango.
3. Clique num canto e depois noutro sítio, uns metros ao lado: a plataforma muda de forma, o terreno fica plano na
   parte nova e os taludes refazem-se. A barra de baixo diz o desaterro e o aterro.
4. Clique num losango e depois noutro sítio: a plataforma ganha um canto.
5. Clique num canto e carregue em Delete: o canto sai.
6. Ctrl+Z desfaz cada passo de uma vez.
7. Esc volta ao Selecionar.
## 0.203 — O pé dos taludes na planta

1. Abra um projeto com terreno inclinado (ou importe pontos: separador **Terreno ▸ Importar pontos de
   levantamento…**).
2. No separador **Terreno**, clique em **Plataforma** e desenhe uma plataforma a meia encosta, a uma cota entre a
   mais baixa e a mais alta do terreno debaixo dela.
3. Abra a planta do pavimento do terreno (F4): do lado onde o terreno é mais alto, a uma certa distância da
   plataforma, aparece a crista do desaterro. Os traços de talude vão dela para a plataforma, um comprido e um
   curto.
4. Do lado onde o terreno é mais baixo aparece o pé do aterro, com os traços a sair da borda da plataforma.
5. Rode a vista (F8): as linhas estão sobre o terreno, à altura certa.
6. Carregue em Ctrl+P (**Exportar vista em PDF…**): no PDF estão as mesmas linhas, em traço fino. No DXF ficam na
   camada TALUDES.
## 0.202 — O valor escrito nas curvas mestras

1. Abra um projeto com terreno com pelo menos 5 m de desnível (ou importe pontos: separador **Terreno ▸ Importar
   pontos de levantamento…**).
2. Na vista 3D, aproxime-se do terreno: sobre as curvas mais grossas (as mestras) aparece a sua cota, por exemplo
   «15».
3. Abra a planta do pavimento do terreno (F4). Se o terreno ficar acima do corte, suba a **Altura de corte** no
   painel **Propriedades** (nada selecionado).
4. Carregue em Ctrl+P (**Exportar vista em PDF…**) e grave: no PDF, as curvas mestras têm o número escrito ao longo
   delas, rodado, com um fundo branco que interrompe a curva.
5. Exporte também em DXF (**Exportar vista em DXF…**) e abra no AutoCAD: os números estão na camada CURVAS_MESTRAS.
## 0.201 — Cores de inclinação nas folhas

1. Abra um projeto com terreno (ou faça um: separador **Terreno ▸ Importar pontos de levantamento…**).
2. Abra a planta do pavimento do terreno (F4).
3. No separador **Terreno**, clique em **Inclinações do terreno**: o terreno fica às cores (verde a vermelho).
4. Clique num sítio vazio da planta (nada selecionado): no painel **Propriedades**, a caixa **Cores de inclinação do
   terreno** está marcada.
5. Carregue em Ctrl+P (**Exportar vista em PDF…**) e grave: no PDF, o terreno está às cores, por baixo das curvas de
   nível. No canto inferior esquerdo há a legenda «Inclinação do terreno», com as faixas que aparecem.
6. Ponha a planta numa folha (painel **Projeto**, botão direito na planta ▸ **Pôr na folha**): na folha também
   aparecem as cores e a legenda.
7. Abra a vista 3D: o terreno está sem cores (a vista 3D tem a sua opção). Volte à planta: as cores continuam.
8. Na planta, desmarque a caixa no painel **Propriedades**: as cores saem do ecrã e do papel.
## 0.200 — Forquilhas a 45° nos esgotos

1. Abra a planta (F4). Com a ferramenta **Tubo**, escolha em **Tipo** o **Tubo PVC Ø100** e, em **Sistema**, as
   **Águas negras**. Escreva `-0,30` em **Eixo a** e escolha uma **Inclinação** (por exemplo 1 %). Desenhe um coletor
   comprido, da esquerda para a direita (desce para a direita).
2. Com a ferramenta **Louça sanitária**, escolha **Sanita**, **Ângulo** 0°, e ponha-a a cerca de 70 cm acima do
   coletor (na planta), longe das paredes.
3. Com a sanita selecionada, no separador **Instalações**, clique em **Ligar à rede**: o ramal desce da sanita para o coletor, vira 45°
   perto dele e entra-lhe na diagonal, virado para a direita (para onde o coletor desce).
4. Clique na peça onde o ramal encontra o coletor: o painel **Propriedades** mostra «Forquilha 1».
5. Rode a vista (F8) e aproxime-se: a forquilha tem o braço a 45°.
## 0.199 — O ramal contorna obstáculos

1. Abra a planta (F4). Com a ferramenta **Tubo**, escolha em **Tipo** o **Tubo PVC Ø25** e, em **Sistema**, a **Água
   fria**. Escreva `0,40` em **Eixo a** e desenhe um tubo comprido na horizontal.
2. Com a ferramenta **Pilar**, ponha um pilar 30×30 a cerca de 70 cm acima do tubo (na planta).
3. Com a ferramenta **Louça sanitária**, escolha **Sanita** e **Ângulo** 0° (as costas viradas para baixo, na
   planta) e ponha-a a cerca de 80 cm acima do pilar, longe das paredes: o pilar fica entre a sanita e o tubo.
4. Com a sanita selecionada, no separador **Instalações**, clique em **Ligar à rede**: o ramal de água sobe do tubo, sai para o lado do
   pilar, passa-o, volta à linha e chega à sanita de frente. Nenhum troço atravessa o pilar.
5. Rode a vista (F8) e aproxime-se: nas quatro esquinas do desvio há curvas.
6. Para comparar, apague o ramal (Ctrl+Z), mova o pilar para longe da linha e volte a ligar: o ramal vai direito.
## 0.198 — Gás e eletricidade nos aparelhos

1. Abra a planta (F4). Com a ferramenta **Tubo**, escolha em **Tipo** o **Tubo de cobre Ø22 (gás)** e desenhe um tubo
   comprido junto de uma parede da cozinha.
2. Com a ferramenta **Eletrodoméstico**, escolha **Placa a gás** e ponha-a a cerca de 1 m do tubo.
3. Com a placa selecionada, no separador **Instalações**, clique em **Ligar à rede**: aparece um ramal amarelo de cobre Ø15 da placa até ao
   tubo de gás, ligado nas duas pontas (a barra de baixo diz quantos ramais fez).
4. Com a ferramenta **Eletrodoméstico**, escolha **Forno** e ponha-o noutro sítio.
5. Com o forno selecionado, no separador **Instalações**, clique em **Novo circuito com a seleção**: a barra de baixo diz «Circuito C1
   (Máquina): 1 pontos, 3500 W».
6. Carregue em Ctrl+T (Tabelas) e escolha **Circuitos: quadro de cargas**: tem o C1 com o forno e 3500 W.

## 0.197 — Condutas em S

1. Abra a planta (F4). Com a ferramenta **Equipamento AVAC**, ponha uma **Unidade de conduta (no teto falso)**
   (fica a 2,60 m).
2. Escolha a ferramenta **Conduta**, tipo 30×20, e em **Eixo a** escreva `3`.
3. Clique longe da unidade, no alinhamento da porta de retorno (o lado esquerdo dela), e depois junto dessa porta.
4. Rode a vista (F8): a conduta segue a 3,00 m, desce a 45° em S com duas curvas e entra na porta, ligada.
5. Para comparar, desenhe outra até outra unidade com **Eixo a** `4`: com mais desnível, desce na vertical.
