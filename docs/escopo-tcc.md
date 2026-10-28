# TCC — Escopo definido da aplicação

## O que vamos construir

Vamos construir uma **aplicação de documentação viva de regras de negócio para repositórios Python no GitHub**, combinando os caminhos A e B: análise e sugestões nos pull requests (PRs), com um portal para consultar o catálogo de regras, o histórico de alterações e o grafo de dependências do sistema.

A ferramenta gera uma documentação inicial a partir do código e acompanha sua evolução a cada PR. A análise estática identifica a estrutura e as dependências do código; a IA auxilia na interpretação das mudanças e na redação das regras em linguagem natural. As atualizações propostas passam por revisão humana.

## Propósito do aplicativo

O propósito do aplicativo é **reduzir a distância entre o comportamento implementado no código e o conhecimento documentado sobre as regras de negócio**, ajudando a equipe a manter esse conhecimento correto, atualizado e rastreável durante a evolução do sistema.

O público principal são desenvolvedores e revisores de código que precisam compreender o sistema, avaliar mudanças e compartilhar conhecimento. O aplicativo deve permitir que essas pessoas encontrem uma regra, entendam seu vínculo com o código e consultem quando e por que ela mudou.

Na prática, a aplicação deve ajudar a:

- Identificar, durante a revisão de um PR, quais regras de negócio foram alteradas e quais registros precisam de atualização.
- Consultar as regras atuais sem depender exclusivamente da leitura do código ou da memória de outros integrantes da equipe.
- Rastrear a evolução de uma regra até o PR e a alteração de código que a originaram.
- Apoiar a entrada de novos integrantes e a passagem de conhecimento sobre o sistema.

Esses benefícios orientam o produto. A avaliação principal do TCC será a capacidade de detectar mudanças e propor documentação correta e atualizada; ganhos de produtividade ou de integração de novos integrantes não serão tratados como resultados comprovados sem avaliação específica.

## Contexto e pergunta de pesquisa

A proposta inicial descrevia uma ferramenta de **extração pontual**: leitura da AST do repositório, geração de grafo de dependências, sumarização de regras de negócio com LLM e consulta por catálogo e grafo. O escopo definido amplia essa proposta para acompanhar a evolução do sistema.

A pergunta de pesquisa que orienta o trabalho é:

> **Em que medida uma ferramenta que analisa cada pull request com análise estática de código e IA consegue manter a documentação de um sistema correta e atualizada?**

Diferenças que isso impõe ao trabalho:

| Aspecto | Proposta inicial | Escopo definido |
|---|---|---|
| Momento da análise | Uma vez, no repositório inteiro | **Incremental, a cada PR** |
| Objeto central | Gerar documentação | **Manter** documentação (detectar quando ela fica errada e corrigir) |
| Pergunta chave da ferramenta | "O que este módulo faz?" | "**Este PR alterou alguma regra de negócio? Qual? O que precisa mudar na doc?**" |
| Avaliação | Heurística da qualidade do texto | **Corretude** e **atualização** medidas ao longo de uma sequência de PRs |
| "em que medida" | — | Exige **métricas quantitativas** + comparação com linhas de base |

O núcleo do TCC é **detectar e propagar mudanças de lógica de negócio para a documentação**. O catálogo, o histórico e o grafo permitem consultar e verificar o resultado dessa manutenção.

---

## Proposta consolidada: caminhos A + B

### Análise e feedback nos PRs — caminho A

A cada PR, a aplicação identifica as unidades de código alteradas, avalia se houve **mudança de regra de negócio**, localiza as entradas do catálogo afetadas e propõe inclusões, alterações ou remoções na documentação. Um comentário no PR apresenta o resumo, as referências ao código e as sugestões de texto para revisão humana.

### Portal de documentação viva — caminho B

A aplicação gera o catálogo inicial de regras de negócio e o grafo de dependências, disponibiliza essa base para revisão e mantém o catálogo incrementalmente. O portal permite pesquisar regras, consultar sua origem no código e acompanhar seu histórico: qual regra mudou, o texto antes e depois e o PR responsável. O grafo destaca os módulos envolvidos na mudança e suas dependências.

**As duas partes integram a entrega:** a análise nos PRs mantém a documentação; o portal torna esse conhecimento consultável e sua evolução verificável. A interface terá foco em catálogo, histórico, revisão das propostas e grafo.

---

## Decisões fechadas (QUE)

1. **Escopo:** caminho A (análise e feedback no PR) + caminho B enxuto (portal com catálogo, revisão das propostas, histórico por PR e grafo). O caminho C (contexto para agentes) fica como **trabalho futuro, fora da entrega e dos critérios de sucesso**.
2. **Documentação mantida:** **catálogo de regras de negócio gerado e mantido pela ferramenta**, versionado junto ao repositório. Documentos humanos existentes ficam fora do escopo e serão tratados como limitação e possibilidade de trabalho futuro.
3. **Linguagem alvo dos repositórios analisados:** **Python**. Plataforma: GitHub (PRs). A stack da aplicação será definida no desenho técnico.
4. **Avaliação:** **replay de PRs open-source** como experimento principal (quantitativo). O **uso em sistema real de uma equipe** será um estudo de caso complementar (qualitativo), condicionado à disponibilidade de uma equipe e de PRs suficientes.
5. **Definição operacional de "mudança de lógica de negócio":** alteração em condição, cálculo, validação, fluxo de estados, regra de autorização ou contrato de entrada/saída que modifique um comportamento de domínio. **Não conta, isoladamente:** renomeação, formatação, refatoração sem mudança de comportamento, testes, dependências ou configuração. PRs mistos serão avaliados quanto às alterações que afetam o comportamento de negócio.
6. **Revisão humana:** as sugestões poderão ser aceitas, ajustadas ou rejeitadas. A documentação vigente só incorporará atualizações aprovadas e correspondentes ao código integrado à branch de referência; propostas pendentes ficarão identificadas separadamente.
7. **Limites:** não fazem parte da entrega o suporte a outras linguagens ou plataformas, a edição automática do código analisado, a atualização de documentos humanos existentes nem a integração com agentes de IA.

## Entregáveis da ferramenta (o que ela FAZ, não como)

1. **Geração da base:** dado um repositório Python, produzir o catálogo inicial de regras de negócio por módulo e unidade de código (função ou método) + grafo de dependências, disponibilizando a base para revisão.
2. **Análise por PR:** listar unidades alteradas, classificar se houve mudança de regra de negócio, identificar entradas do catálogo afetadas e propor inclusões, alterações ou remoções. Dependências indicam possíveis impactos a analisar, não comprovam por si só uma mudança de regra.
3. **Feedback e revisão:** publicar comentário no PR resumindo "regras alteradas / documentação afetada / sugestão", com referências ao código e possibilidade de aceitar, ajustar ou rejeitar as propostas.
4. **Portal:** catálogo pesquisável por texto e módulo, acesso à origem das regras no código, revisão das propostas, linha do tempo por PR (antes/depois) e grafo destacando os módulos envolvidos.
5. **Rastreabilidade:** manter identificação estável das regras, versão de código analisada, situação das propostas e histórico das atualizações aprovadas.

## Fluxo de uso e atualização

1. A equipe seleciona um repositório e uma versão de referência. A ferramenta gera o catálogo inicial e o grafo para revisão.
2. Um PR é aberto ou atualizado. A ferramenta analisa as mudanças e apresenta as sugestões de documentação no PR e no portal.
3. Uma pessoa da equipe revisa as propostas, aceitando, ajustando ou rejeitando cada atualização.
4. Quando o código é incorporado à branch de referência, as atualizações aprovadas correspondentes passam a compor o catálogo vigente. Um PR fechado sem merge não altera essa documentação.
5. A equipe consulta as regras atuais no portal e pode recuperar versões anteriores, os PRs associados e as dependências envolvidas.

Por exemplo: se um PR alterar o valor mínimo para conceder um desconto, a ferramenta deverá identificar a mudança na condição, localizar a regra documentada e sugerir o novo texto. Após revisão e incorporação do código, o portal exibirá a regra atual, preservando o valor anterior e o vínculo com o PR.

---

## Como a pergunta será respondida (desenho da avaliação — o "o que medir")

**Experimento principal — replay histórico:** selecionar repositórios Python open-source; gerar a documentação base num commit inicial; reprocessar os PRs reais já mesclados na ordem em que foram integrados. A meta inicial é de 2–3 repositórios e cerca de 50–100 PRs por repositório, sujeita à disponibilidade de projetos adequados e ao esforço de rotulação.

**Gabarito:** rotular manualmente cada PR (alterou regra de negócio? qual? que atualização era esperada?) — idealmente com um segundo avaliador para medir concordância (kappa). O protocolo distinguirá as propostas originais da ferramenta das correções humanas, para que a intervenção do revisor não seja contabilizada como acerto automático.

**Métricas:**

| Dimensão | O que mede | Métrica |
|---|---|---|
| Detecção | A ferramenta percebe quando a regra de negócio mudou? | Precisão, recall, F1 por PR |
| Corretude | A atualização proposta está certa? | % correta / parcial / incorreta (avaliação manual) |
| Atualização | Ao longo da sequência e ao final, a doc ainda reflete o código? | % de regras documentadas desatualizadas (drift), com registro também de regras esperadas ausentes |
| Custo | É viável rodar a cada PR? | Tempo e custo (tokens) por PR |

**Linhas de base (para "em que medida"):**

- **Catálogo inicial sem manutenção:** manter congelada a mesma base inicial e medir quanto ela fica desatualizada ao longo dos PRs.
- **Só IA no diff bruto (sem análise estática):** comparação para avaliar a contribuição da estrutura e das dependências extraídas do código.
- (Opcional) Regenerar tudo do zero a cada PR — comparação de qualidade e custo, sem presumir superioridade.

**Estudo de caso complementar (sistema real):** buscar uma equipe com projeto Python e volume suficiente de PRs no período; registrar aceitação, ajustes e rejeição das sugestões; aplicar questionário/entrevista curta sobre utilidade, corretude percebida e apoio à passagem de conhecimento. Sua realização depende da disponibilidade dessa equipe; o replay histórico permanece como avaliação principal.

---

## Entregáveis do TCC

1. Aplicação integrada ao GitHub para geração inicial e manutenção incremental do catálogo, com revisão humana das propostas.
2. Portal com catálogo pesquisável, histórico das regras por PR e grafo de dependências.
3. Experimento reproduzível de replay de PRs, com protocolo de rotulação, métricas e comparação com as linhas de base.
4. Relato dos resultados, limitações e, caso viável, do estudo de caso com uma equipe.

## Impacto no documento acadêmico

- Título e objetivo geral: incluir "a cada pull request" e "manter atualizada".
- Objetivos específicos: abranger geração inicial, detecção de mudança de regra de negócio no PR, atualização incremental com revisão humana, consulta pelo portal e avaliação de corretude/atualização.
- Referencial teórico: acrescentar documentação desatualizada (*documentation drift / outdated documentation*), *docs-as-code*, integração contínua e revisão de código, LLMs para sumarização de código, trabalhos relacionados (ferramentas de análise em PR e geradores de documentação com IA).
- Metodologia: substituir a validação heurística pelo experimento de replay acima.

## Próximo passo

Com o escopo definido como **análise nos PRs + portal de documentação viva**, detalhar a arquitetura, os parsers e a comparação de ASTs para Python, os prompts, o armazenamento e versionamento do catálogo, a integração com o GitHub e a stack da interface.
