# ArqSynth BIM e a IA (MCP)

O ArqSynth BIM tem um servidor **MCP** (Model Context Protocol). Com ele, um assistente de IA, como o Claude Desktop
ou o Claude Code, consegue ler e mudar os seus modelos IFC. Faz o mesmo que o utilizador na janela:
- as paredes ligam-se nos cantos;
- os dados IFC preenchem-se sozinhos;
- cada mudança desfaz-se com Ctrl+Z.

## Ligar

O caminho mais simples:
1. Abra o ArqSynth BIM.
2. No separador **Gerenciar**, clique em **Ligar um assistente de IA…**.
3. Escolha uma das três formas:
   - **Claude Desktop:** clique em **Pôr no Claude Desktop**, depois feche e volte a abrir o Claude Desktop. O que
     já estava no ficheiro de configuração fica, e o ficheiro antigo é guardado ao lado, com o nome .bak.
   - **Claude Code:** clique em **Copiar** e cole a linha num terminal. Fica disponível em todas as pastas.
   - **Outro programa:** copie a configuração JSON e cole-a onde esse programa guarda os servidores MCP.

**Trabalhar no modelo aberto na janela:** no separador **Gerenciar**, ligue **Ligação à IA**.
- A IA trabalha no modelo aberto, à vista, e o rodapé diz o que ela fez.
- A janela só aceita pedidos deste computador, com uma chave feita ao acaso.
- Desligar o botão, ou fechar o programa, corta a ligação.

**Sem a janela:** o servidor trabalha num modelo seu, que a IA pode gravar e abrir. Para começar num ficheiro
escolhido, acrescente `--file caminho\do\modelo.ifc` à configuração.

## As ferramentas

| Ferramenta | O que faz |
|---|---|
| summary | Pisos, elementos por classe, tipos usados (types=true: as chaves dos tipos; missing=true: os dados IFC em falta, por classe) |
| query | Elementos numa tabela: filtros (classe, piso, tipo, nome), campos escolhidos, 40 linhas de cada vez; classe IfcWallType…: os tipos, com quantos elementos cada um tem |
| get | Um elemento (ou um tipo): classe, nome, tipo, piso, medidas, os seus dados IFC |
| create | Parede, paredes seguidas, laje, cobertura, porta, janela, pilar, viga, compartimento, piso |
| edit | Nome, tipo, altura, qualquer dado IFC (FireRating, IsExternal, Pset_X.Prop…); mover. Num tipo: o dado vale para todos os elementos dele |
| delete, undo | Apagar; desfazer |
| file | Novo, abrir, gravar (com a janela, só gravar) |
| show | Só com a janela: seleciona elementos e aproxima a vista deles |

## Gastar poucos tokens

O servidor responde em tabelas de texto curtas, não em JSON comprido. Chama cada elemento pelo seu número no
ficheiro («#54»), com poucas letras. Medido numa sessão típica no edifício médio do teste de desempenho, com 3 241
elementos (resumo, consulta, uma casa, uma porta, os seus dados, uma mudança e gravar), em tokens aproximados:

| Pedido | Resposta |
|---|---|
| lista das ferramentas (vai em cada pedido à IA) | ~700 |
| resumo do modelo | ~120 |
| 20 paredes de um piso, com comprimento e se são exteriores | ~130 |
| criar uma casa de quatro paredes | ~50 |
| um elemento com os seus dados IFC | ~70 |
| **a sessão toda (enviado + recebido)** | **~1 550** |

Conselhos:
- comece por pedir um resumo do modelo;
- para os dados IFC, peça o que falta («resumo com os dados em falta») e preencha-os nos tipos («dá EI 60 ao tipo
  de parede de 20 cm»): uma só chamada vale para todos os elementos desse tipo;
- peça tabelas só com os campos de que precisa («lista as paredes com o comprimento»);
- fale dos elementos pelo número (#54);
- peça páginas pequenas em modelos grandes.
