# TCC — Definição do QUE vamos construir e avaliar (antes do COMO)

## Contexto

O documento atual (`docs/TCC_Marley_01-07-2026.docx.pdf`) descreve uma ferramenta de **extração pontual**: lê a AST do repositório, gera grafo de dependências, usa LLM para sumarizar regras de negócio e exibe tudo num catálogo + grafo. A validação prevista é "acurácia estrutural" e "qualidade da sumarização" (avaliação heurística).

A nova pergunta de pesquisa muda o foco:

> **Em que medida uma ferramenta que analisa cada pull request com análise estática de código e IA consegue manter a documentação de um sistema correta e atualizada?**

Diferenças que isso impõe ao trabalho:

| Aspecto | Documento atual | Pergunta nova |
|---|---|---|
| Momento da análise | Uma vez, no repositório inteiro | **Incremental, a cada PR** |
| Objeto central | Gerar documentação | **Manter** documentação (detectar quando ela fica errada e corrigir) |
| Pergunta chave da ferramenta | "O que este módulo faz?" | "**Este PR alterou alguma regra de negócio? Qual? O que precisa mudar na doc?**" |
| Avaliação | Heurística da qualidade do texto | **Corretude** e **atualização** medidas ao longo de uma sequência de PRs |
| "em que medida" | — | Exige **métricas quantitativas** + comparação com linhas de base |

Ou seja: o núcleo do TCC deixa de ser "sumarizar código" e passa a ser **detectar e propagar mudança de lógica de negócio para a documentação**. Grafo, catálogo e contexto para agentes viram consequências desse núcleo.

---

## Caminhos possíveis

### Caminho A — "Guardião de documentação" no PR (núcleo mínimo)
A cada PR: identifica as unidades de código alteradas → decide se houve **mudança de regra de negócio** (vs. refatoração, formatação, testes, infra) → aponta quais trechos da documentação ficaram desatualizados → propõe o texto novo como comentário/sugestão no PR (humano aprova).
- Pró: responde diretamente à pergunta; escopo controlado; fácil de avaliar.
- Contra: sem interface própria rica; a "documentação" precisa já existir (ou ser gerada uma vez).

### Caminho B — Documentação viva com portal (A + interface)
Gera uma **linha de base** da documentação do sistema (catálogo de regras de negócio por módulo + grafo de dependências) e, a cada PR, atualiza incrementalmente. A interface mostra o estado atual **e o histórico**: "regra X mudou no PR #123", diff da regra antes/depois, módulos impactados no grafo.
- Pró: aproveita quase tudo do documento atual (AST, grafo, catálogo, sumarização); a interface vira evidência visual da manutenção.
- Contra: mais trabalho de front-end, que não ajuda diretamente a responder a pergunta.

### Caminho C — Base de conhecimento para agentes de IA
A documentação mantida é exposta em formato consumível por agentes (ex.: arquivos de contexto no repositório ou um servidor MCP), e avalia-se se agentes respondem/atuam melhor com ela.
- Pró: tema atual, conecta com "passagem de conhecimento" (Nonaka/SECI — internalização por agentes).
- Contra: introduz **uma segunda pergunta de pesquisa** (eficácia para agentes) que exige outra avaliação; dilui o foco.

### Recomendação
**Núcleo = A, apresentado via uma versão enxuta de B; C como funcionalidade secundária/trabalho futuro.**
- A é o que responde à pergunta.
- B enxuto (catálogo + histórico de mudanças por PR + grafo já planejado) mantém coerência com o texto já escrito e com o objetivo específico 3.
- C entra como "exportação" da mesma base (barato de fazer) e, no máximo, um experimento qualitativo pequeno — sem virar critério de sucesso do TCC.

---

## Decisões fechadas (QUE)

1. **Escopo:** Caminho A (análise no PR) + B enxuto (catálogo, histórico de mudanças por PR, grafo). C (contexto para agentes) = exportação simples da mesma base / trabalho futuro, **fora dos critérios de sucesso**.
2. **"A documentação"** = **catálogo de regras de negócio gerado e mantido pela ferramenta**, versionado junto ao repositório. Docs humanas existentes ficam fora do escopo (citar como limitação/trabalho futuro).
3. **Linguagem alvo:** **Python**. Plataforma: GitHub (PRs).
4. **Avaliação:** **replay de PRs open-source** como experimento principal (quantitativo) + **uso em sistema real de uma equipe** como estudo de caso (qualitativo).
5. **Definição operacional de "mudança de lógica de negócio"** (proposta, a validar com a orientadora): alteração em condição, cálculo, validação, fluxo de estados, regra de autorização ou contrato de entrada/saída de uma unidade de domínio. **Não conta:** renomeação, formatação, refatoração sem mudança de comportamento, testes, dependências, configuração.

## Entregáveis da ferramenta (o que ela FAZ, não como)
1. **Geração da base:** dado um repositório Python, produzir o catálogo inicial de regras de negócio por módulo/função + grafo de dependências.
2. **Análise por PR:** para cada PR, listar unidades alteradas, classificar se houve mudança de regra de negócio, identificar entradas do catálogo afetadas (inclusive por dependência), e propor a atualização.
3. **Feedback no PR:** comentário resumindo "regras alteradas / doc afetada / sugestão", com aprovação humana.
4. **Interface:** catálogo pesquisável, linha do tempo de mudanças de regras por PR (antes/depois), grafo destacando módulos impactados.
5. **(Secundário)** Exportar o catálogo num formato consumível por agentes de IA.

---

## Como a pergunta será respondida (desenho da avaliação — o "o que medir")

**Experimento principal — replay histórico:** escolher 2–3 repositórios open-source; gerar a documentação base num commit inicial; reprocessar em ordem cronológica N PRs reais já mesclados (ex.: 50–100 por repositório).

**Gabarito:** rotular manualmente cada PR (alterou regra de negócio? qual?) — idealmente com um segundo avaliador para medir concordância (kappa).

**Métricas:**
| Dimensão | O que mede | Métrica |
|---|---|---|
| Detecção | A ferramenta percebe quando a regra de negócio mudou? | Precisão, recall, F1 por PR |
| Corretude | A atualização proposta está certa? | % correta / parcial / incorreta (avaliação manual) |
| Atualização | Ao fim da sequência, a doc ainda reflete o código? | % de regras documentadas desatualizadas (drift) |
| Custo | É viável rodar a cada PR? | Tempo e custo (tokens) por PR |

**Linhas de base (para "em que medida"):**
- Sem ferramenta: a documentação original do projeto fica desatualizada quanto?
- **Só IA no diff bruto (sem análise estática)** — ablação que mostra o ganho da AST; a pergunta cita explicitamente "análise estática **e** IA", então isso é central.
- (Opcional) Regenerar tudo do zero a cada PR — teto de qualidade vs. custo.

**Estudo de caso (sistema real):** instalar a ferramenta num projeto de uma equipe durante um período; registrar aceitação/rejeição das sugestões feitas nos PRs; aplicar questionário/entrevista curta com os desenvolvedores sobre utilidade, corretude percebida e impacto na passagem de conhecimento.
- Pendente: confirmar qual equipe/sistema, se ele é em Python e se há volume de PRs suficiente no período.

---

## Impacto no documento do TCC (quando formos escrever)
- Título e objetivo geral: incluir "a cada pull request" e "manter atualizada".
- Objetivos específicos: adicionar (i) detecção de mudança de regra de negócio no PR, (ii) atualização incremental da documentação, (iii) avaliação de corretude/atualização.
- Referencial teórico: acrescentar documentação desatualizada (*documentation drift / outdated documentation*), *docs-as-code*, integração contínua e revisão de código, LLMs para sumarização de código, trabalhos relacionados (ferramentas de análise em PR e geradores de documentação com IA).
- Metodologia: substituir a validação heurística pelo experimento de replay acima.

## Próximo passo (depois de aprovado o QUE)
Só então discutir o COMO: linguagem/parsers, diff de AST, prompts, armazenamento da documentação, integração com GitHub, stack da interface.
