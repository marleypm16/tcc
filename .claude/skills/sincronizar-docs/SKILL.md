---
name: sincronizar-docs
description: Compara o código do Lastro (ou um diff/branch) com docs/arquitetura-tcc.md e os capítulos revisados do TCC e lista as divergências e o que precisa ser atualizado no texto. Não edita o texto do TCC sem aprovação. Use quando o usuário perguntar "o código ainda bate com a arquitetura?", "o que mudar no Cap. 4?", ao fim de uma etapa da implementação ou antes de atualizar o documento do TCC.
---

# /sincronizar-docs

Argumento opcional: o que comparar. Sem argumento, use o diff da branch atual contra `master` (`git diff master...HEAD`) mais o que não foi commitado. Pode ser também um módulo (`/sincronizar-docs processamento`) ou `tudo`.

## Fontes

- `docs/arquitetura-tcc.md`: referência técnica (tecnologias, fluxos, fila, modelo de dados na seção 7, organização na seção 8, ordem na seção 9, pendências na seção 10.3).
- `docs/capitulo-4-revisado.md`: texto do TCC sobre a construção (4.1 Arquitetura ... 4.7 Portal).
- `docs/capitulo-3-revisado.md`: só método e protocolo de avaliação. Mudanças no replay/métricas podem afetá-lo.
- `docs/escopo-tcc.md`: escopo.

## O que procurar

1. **Contradições**: o código faz algo diferente do documento (nome de tabela/coluna/estado, fluxo de evento, regra de reserva, permissões do GitHub App, formato da resposta da IA, tecnologia).
2. **Decisões novas**: o código resolveu algo listado como em aberto na seção 10.3. É candidato a sair de "em aberto" e entrar no Cap. 4.
3. **Lacunas**: o documento descreve algo que o código da etapa atual já deveria ter e não tem.
4. **Termos**: nomes diferentes para a mesma coisa entre código e texto.

## Saída

Uma tabela com: **Onde no código** (`arquivo:linha`) · **Onde no documento** (arquivo + seção) · **Tipo** (contradição / decisão nova / lacuna / termo) · **Sugestão**.

Depois, uma recomendação por item: ajustar o código ou ajustar o texto.

## Regras

- **Não edite** `docs/capitulo-*` nem `docs/arquitetura-tcc.md` nesta skill. O usuário valida cada ponto antes de qualquer mudança no texto. Só proponha.
- No Cap. 4, respeite a estrutura aprovada: sem justificar escolhas comparando com alternativas, sem seção de replay e sem exemplo de ponta a ponta. Problema e pergunta de pesquisa ficam na Introdução; limitações têm capítulo próprio.
- Seja específico: cite a frase do documento que diverge.
