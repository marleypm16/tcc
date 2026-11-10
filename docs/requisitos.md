# Lastro — Especificação de requisitos

Versão 0.1 · 10/11/2026 · rascunho para revisão

Este documento reúne os requisitos funcionais e não funcionais do Lastro, levantados a partir de [escopo-tcc.md](escopo-tcc.md), [arquitetura-tcc.md](arquitetura-tcc.md), [Mapa da arquitetura do TCC](<Mapa da arquitetura do TCC.md>) e dos capítulos 1, 3 e 4 revisados. Ele não cria decisões novas: quando as fontes divergem ou deixam algo em aberto, o ponto aparece na seção 6 para decisão.

## 1. Convenções

**Identificadores.** `RF-<grupo>-<nn>` para requisitos funcionais, `RNF-<categoria>-<nn>` para não funcionais e `RN-<nn>` para regras de negócio da própria ferramenta. Os identificadores são estáveis: um requisito removido não tem seu número reaproveitado.

**Prioridade.**

| Prioridade | Significado |
|---|---|
| **Essencial** | Sem ele, a pergunta de pesquisa não pode ser respondida ou o fluxo principal não funciona. |
| **Importante** | Faz parte da entrega descrita no TCC, mas a avaliação principal (replay) funciona sem ele. |
| **Desejável** | Melhora a operação ou a experiência; pode ficar como trabalho futuro sem prejuízo do TCC. |

**Fontes.** `E` = escopo-tcc.md · `A§n` = arquitetura-tcc.md, seção n · `M` = Mapa da arquitetura · `C1`, `C3.x`, `C4.x` = capítulos revisados.

**Incremento.** Número da etapa da ordem de implementação (arquitetura, seção 9) em que o requisito é entregue: 1 analisador local · 2 catálogo e Gemini · 3 persistência e fila · 4 GitHub App e documentação no PR · 5 sincronização após merge · 6 portal · 7 avaliação.

## 2. Visão geral

### 2.1 Objetivo do sistema

Manter a documentação das regras de negócio de repositórios Python no GitHub correta, atualizada e rastreável. A cada pull request, o Lastro identifica as unidades de código alteradas com análise estática (`ast`), usa o Gemini para decidir se alguma regra de negócio mudou, propõe a atualização da documentação na branch do próprio PR e, após o merge, sincroniza a documentação incorporada com o banco consultado pelo portal.

### 2.2 Atores

| Ator | Descrição | Onde interage |
|---|---|---|
| **Desenvolvedor** | Abre e atualiza PRs no repositório acompanhado. | GitHub |
| **Revisor** | Revisa código e documentação no PR, edita os arquivos do catálogo se discordar e realiza o merge. | GitHub |
| **Consultor do portal** | Qualquer pessoa com acesso ao repositório no GitHub que consulta catálogo, histórico e grafo. Inclui novos integrantes da equipe. | Portal |
| **Administrador da instalação** | Instala a GitHub App nos repositórios e dispara a geração da base inicial. | GitHub e terminal |
| **Pesquisador** | Executa o replay histórico, as linhas de base e coleta as métricas (o autor do TCC). | Terminal |
| **GitHub** (sistema) | Envia webhooks, fornece código e recebe commits e comentários. | API e worker |
| **Gemini** (sistema) | Interpreta as mudanças e redige as regras. | Worker |

### 2.3 Fluxos cobertos

1. **Geração da base:** repositório + versão de referência → AST → grafo + catálogo inicial → revisão → catálogo vigente.
2. **Análise por PR:** webhook → tarefa → comparação de AST → contexto → Gemini → validação → commit de JSON/Markdown + comentário no PR.
3. **Incorporação:** merge → tarefa `pr_mergeado` → leitura do catálogo no commit incorporado → cópia no banco.
4. **Consulta:** login GitHub → repositórios acessíveis → catálogo, histórico, grafo.
5. **Avaliação:** replay de PRs mesclados → métricas → comparação com linhas de base.

## 3. Requisitos funcionais

### 3.1 Análise estática (`analise`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-AN-01 | O sistema deve converter cada arquivo Python em AST com o `ast` da versão instalada, sem executar o código nem instalar suas dependências. | Essencial | A§3, C4.2 | 1 |
| RF-AN-02 | O sistema deve extrair, por arquivo: módulo, classes, funções, métodos, constantes de nível de módulo, importações e chamadas feitas no corpo de cada unidade. | Essencial | A§3, C4.4.1 | 1 |
| RF-AN-03 | O sistema deve identificar cada unidade de código (função ou método) pelo nome qualificado: caminho do módulo + classe (quando houver) + nome. | Essencial | C4.4.1 | 1 |
| RF-AN-04 | O sistema deve registrar como **não analisado** o arquivo que não puder ser convertido em AST e marcar a análise como **incompleta**, sem tratar o arquivo como ausência de regras ou de mudança. | Essencial | A§3, C4.4.1 | 1 |
| RF-AN-05 | O sistema deve comparar duas versões de um conjunto de arquivos e classificar cada unidade como adicionada, removida ou alterada, pareando as unidades pelo nome qualificado. | Essencial | A§3, C4.5.1 | 1 |
| RF-AN-06 | A comparação deve ignorar posição (linha/coluna), formatação, espaçamento e comentários, considerando alterada apenas a unidade cuja árvore mudou. | Essencial | C4.5.1 | 1 |
| RF-AN-07 | O sistema deve detectar alterações em constantes de nível de módulo e marcar como `afetada_por_constante` as unidades que as utilizam, mesmo sem mudança no próprio código. | Essencial | A§3, C4.5.1 | 1 |
| RF-AN-08 | O sistema deve construir o grafo de dependências entre unidades (chamadas), calculado em memória a cada análise e não persistido. | Essencial | A§7, C4.4.2 | 1 |
| RF-AN-09 | O sistema deve construir o grafo de dependências entre módulos, com arestas de `importacao` e de `chamada`, considerando apenas módulos do próprio repositório. | Essencial | A§7, C4.4.2 | 1 |
| RF-AN-10 | O sistema deve resolver estaticamente as chamadas associáveis a uma unidade conhecida e registrar as demais como **não resolvidas**. | Importante | A§3, C4.4.2 | 1 |
| RF-AN-11 | Para cada unidade adicionada, removida ou alterada, o sistema deve selecionar o contexto: código nas duas versões, regras vinculadas à unidade e unidades vizinhas no grafo (quem chama e quem é chamado) com suas regras. | Essencial | A§3, C4.5.2 | 1–2 |
| RF-AN-12 | O sistema deve distinguir, no resultado, as unidades **alteradas** das unidades de **contexto**; vizinhas nunca são tratadas como alteradas. | Essencial | A§7, C4.5.2 | 1 |
| RF-AN-13 | O sistema deve permitir executar a comparação de duas versões pelo terminal, sem banco nem GitHub, exibindo as diferenças estruturais e o contexto. | Essencial | A§9 | 1 |

### 3.2 Interpretação por IA (`interpretacao`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-IA-01 | O sistema deve montar o prompt em três partes: instruções (papel e definição operacional de mudança de regra, RN-01 e RN-02), contexto (comparação + contexto selecionado) e formato de saída em JSON. | Essencial | C4.5.3 | 2 |
| RF-IA-02 | O sistema deve enviar ao modelo apenas as unidades alteradas e o contexto selecionado, nunca o repositório inteiro nem o diff bruto (exceto na linha de base RF-AV-04). | Essencial | C3.2.2, A§5 | 2 |
| RF-IA-03 | A resposta deve informar se houve mudança de regra de negócio e, para cada mudança: regra afetada (quando existir), tipo (`inclusao`, `alteracao`, `remocao`), título, descrição proposta, unidade, justificativa e referências às unidades que a sustentam. | Essencial | A§5, A§7, C4.5.3 | 2 |
| RF-IA-04 | O sistema deve validar a resposta: formato JSON esperado, identificadores de regra existentes no catálogo e unidades referenciadas existentes na análise. | Essencial | A§5, C4.5.4 | 2 |
| RF-IA-05 | Respostas que falharem na validação devem ser solicitadas novamente, até um limite configurável; esgotado o limite, a análise é registrada como falha. | Essencial | C4.5.4 | 2 |
| RF-IA-06 | Para gerar o catálogo inicial, o sistema deve enviar ao modelo, unidade por unidade, o código, as constantes usadas e as unidades chamadas diretamente; o modelo indica se a unidade implementa regras e redige título e descrição de cada uma. | Essencial | C4.4.3 | 2 |
| RF-IA-07 | O acesso ao Gemini deve ficar atrás de uma porta (`InterpretadorMudancas`), com o SDK isolado em um adaptador, para que o pipeline possa ser testado com fakes. | Essencial | A§5, CLAUDE.md | 2 |
| RF-IA-08 | Cada chamada deve registrar modelo, versão do prompt, parâmetros, tokens de entrada e de saída e duração. | Essencial | A§5, C4.5.4 | 2 |

### 3.3 Catálogo e documentação (`documentacao`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-DOC-01 | Cada regra do catálogo deve ter: identificador, título, descrição, módulo, unidade de código, arquivo e intervalo de linhas, commit do código, PR de origem e situação (`vigente` ou `removida`). | Essencial | C4.3 | 2 |
| RF-DOC-02 | O identificador da regra deve ser atribuído na criação, ser independente da posição no código e se manter quando a unidade mudar de linha, arquivo ou nome. | Essencial | E, C4.3 | 2 |
| RF-DOC-03 | O sistema deve gerar, a partir da mesma estrutura de dados, o catálogo em **JSON** (para a ferramenta) e em **Markdown** (para leitura humana, inclusive no GitHub). | Essencial | A§6, C4.3.1 | 2 |
| RF-DOC-04 | O sistema deve gerar a base inicial de um repositório a partir de uma versão de referência: catálogo inicial por módulo e unidade + grafo de módulos. | Essencial | E, C3.2.1, C4.4 | 2 |
| RF-DOC-05 | A base inicial deve passar por revisão antes de ser tratada como documentação vigente. | Essencial | E, A§9 | 2/4 |
| RF-DOC-06 | O sistema deve aplicar as propostas validadas ao catálogo existente (incluir, alterar ou remover regras), gerando o novo JSON e Markdown. | Essencial | A§6 | 2 |
| RF-DOC-07 | Após o merge, o sistema deve ler os artefatos de documentação do commit efetivamente incorporado e atualizar a cópia no banco, criando uma nova versão para cada regra modificada. | Essencial | A§6, C4.6.4 | 5 |
| RF-DOC-08 | A importação deve trazer a versão final do repositório, incluindo edições humanas, e marcar `editada_por_humano` quando o conteúdo diferir da proposta original. | Essencial | A§6, A§7 | 5 |
| RF-DOC-09 | A importação deve ser idempotente e registrar repositório, PR, commit do código, versão da documentação e horário da sincronização. | Essencial | A§6 | 5 |
| RF-DOC-10 | O catálogo atual não deve retroceder quando merges chegarem fora de ordem: versões podem entrar no histórico, mas `commit_catalogo_atual` só avança para commits descendentes. | Essencial | A§6, A§7 | 5 |
| RF-DOC-11 | Se o PR for mergeado com documentação ausente, inválida ou referente a uma análise desatualizada, o sistema deve registrar a inconsistência e não apresentar a versão como sincronizada. | Importante | A§6 | 5 |
| RF-DOC-12 | Módulos removidos devem ser marcados como inativos, sem exclusão, preservando as versões antigas das regras. | Importante | A§7 | 5 |
| RF-DOC-13 | As propostas originais do modelo devem ser imutáveis e guardadas separadamente das versões incorporadas. | Essencial | A§6, A§7 | 3 |

### 3.4 Integração com o GitHub (`integracao_github`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-GH-01 | O sistema deve receber webhooks em `POST /webhooks/github` e validar a assinatura com o segredo compartilhado, rejeitando entregas inválidas. | Essencial | A§4, C4.6.1 | 4 |
| RF-GH-02 | O sistema deve tratar os eventos `pull_request` conforme a tabela: `opened` e `reopened` → `analisar_pr`; `synchronize` → `analisar_pr` (exceto commit do bot, RF-GH-04); `closed` com merge → `pr_mergeado`; `closed` sem merge → registrar e descartar pendentes. | Essencial | A§4, C4.6.1 | 4 |
| RF-GH-03 | Evento e tarefa devem ser gravados na mesma transação; a resposta ao GitHub só é enviada após o commit. Eventos ignorados podem ser registrados com o motivo, sem tarefa. | Essencial | A§4, C4.6.1 | 3–4 |
| RF-GH-04 | O sistema deve reconhecer o `synchronize` causado apenas pelo commit de documentação do próprio bot (identidade do app, commit e arquivos alterados) e não gerar tarefa. Commits humanos sempre geram análise. | Essencial | A§4, C4.6.3 | 4 |
| RF-GH-05 | O worker deve obter um token de instalação com a chave privada da GitHub App para ler código e publicar no repositório. | Essencial | A§4 | 4 |
| RF-GH-06 | O sistema deve obter a lista de arquivos Python alterados no PR e o conteúdo de cada um nas versões base e head. | Essencial | C4.5.1 | 4 |
| RF-GH-07 | O worker deve fazer commit dos artefatos JSON e Markdown na branch do PR, alterando **apenas** os caminhos de documentação mantidos pela ferramenta. | Essencial | A§6, C4.6.3 | 4 |
| RF-GH-08 | Antes de publicar, o worker deve conferir que o PR continua aberto e que a branch ainda está na versão analisada; o commit tem como pai essa versão e a referência é atualizada sem forçar (`force: false`). Se a branch avançou, a publicação é cancelada. | Essencial | A§6, C4.6.3 | 4 |
| RF-GH-09 | O worker deve publicar no PR um comentário curto com o resumo das regras incluídas, alteradas e removidas, as unidades de código correspondentes e os arquivos de documentação alterados. | Essencial | E, A§6, C4.6.3 | 4 |
| RF-GH-10 | Quando a análise concluir que não houve mudança de regra de negócio, o sistema não faz commit e apenas comenta essa conclusão. | Importante | C4.6.3 | 4 |
| RF-GH-11 | A publicação deve ser idempotente: antes de criar commit ou comentário, o worker verifica se a publicação para a mesma análise e commit já existe. | Essencial | A§4, C4.6.2 | 4 |
| RF-GH-12 | Ajustes humanos à documentação na branch não podem ser sobrescritos silenciosamente por uma nova análise: devem ser preservados ou apresentados como conflito. | Importante | A§6 | 4 |
| RF-GH-13 | Sem permissão de escrita na branch (ex.: forks, branches protegidas), o sistema deve registrar a falta de permissão e informá-la no PR, sem apresentar a documentação como publicada. | Importante | A§4 | 4 |
| RF-GH-14 | Após o merge, o sistema deve resolver o commit incorporado conforme o tipo de merge (merge comum, squash ou rebase). | Essencial | A§6 | 5 |

### 3.5 Processamento e fila (`processamento`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-PR-01 | A fila deve ser a tabela `tarefas`, com tipos `analisar_pr` e `pr_mergeado` e estados `pendente`, `processando`, `concluida`, `erro` e `descartada`. | Essencial | A§4, A§7 | 3 |
| RF-PR-02 | O worker deve consultar periodicamente a fila, com intervalo configurável quando vazia, e reservar uma tarefa por vez com `FOR UPDATE SKIP LOCKED` em transação curta, confirmada antes da análise. | Essencial | A§4 | 3 |
| RF-PR-03 | Uma entrega repetida (mesmo `X-GitHub-Delivery`) deve ser reconhecida e não gerar outra tarefa. | Essencial | A§4 | 3 |
| RF-PR-04 | A reserva deve ter prazo (`reserva_ate`) e token (`reserva_token`); o worker a renova enquanto ativo, e conclusão e renovação conferem o token para que uma execução antiga não conclua tarefa retomada. | Essencial | A§4 | 3 |
| RF-PR-05 | Na inicialização e periodicamente, o worker deve recuperar reservas expiradas, devolvendo a tarefa a `pendente` ou marcando `erro` se o limite de tentativas foi atingido. | Essencial | A§4, C4.6.2 | 3 |
| RF-PR-06 | Falhas temporárias do Gemini ou do GitHub devem reagendar a tarefa (`disponivel_em`) com intervalo entre tentativas e limite configurável; esgotado o limite, a tarefa vai para `erro` preservando o histórico. | Essencial | A§4, C4.6.2 | 3 |
| RF-PR-07 | Uma tarefa retomada deve reaproveitar etapas já persistidas (ex.: análise salva, publicação pendente) em vez de refazê-las. | Importante | A§4 | 3–4 |
| RF-PR-08 | A análise deve ser deduplicada por PR, `base_sha`, `head_sha`, modelo e versão do prompt. | Essencial | A§4, A§7 | 3 |
| RF-PR-09 | Ao fechar um PR sem merge ou ao chegar nova versão, tarefas pendentes que perderam a finalidade devem ser marcadas `descartada`. | Importante | A§4, C4.6.1 | 3–4 |
| RF-PR-10 | O sistema deve registrar as etapas e tentativas de cada tarefa (recebimento, análise, chamadas ao Gemini, publicação, erros, sincronização). | Importante | A§4 | 3 |
| RF-PR-11 | Deve existir um procedimento operacional para reprocessar tarefas em `erro` após correção. | Desejável | A§4 | 3 |

### 3.6 Acesso e autenticação (`acesso`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-AC-01 | O portal deve exigir login com a conta do GitHub, pelo fluxo de autorização de usuário da GitHub App, sem armazenar senhas. | Essencial | A§7, C4.7 | 6 |
| RF-AC-02 | Após o login, o sistema deve consultar os repositórios da instalação acessíveis à pessoa e registrar essa relação (`usuario_repositorio`). | Essencial | A§7 | 6 |
| RF-AC-03 | Todas as consultas do portal devem ser restritas aos repositórios acessíveis à pessoa autenticada. | Essencial | A§7, C4.7 | 6 |
| RF-AC-04 | A permissão deve ser verificada novamente no GitHub quando `verificado_em` expirar. | Importante | A§7 | 6 |
| RF-AC-05 | A pessoa deve poder encerrar a sessão (`POST /auth/logout`). | Importante | C4.7 | 6 |

### 3.7 Portal de consulta (`catalogo` + frontend)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-PO-01 | O portal deve listar os repositórios acessíveis com a versão do catálogo sincronizada de cada um. | Essencial | C4.7 | 6 |
| RF-PO-02 | A tela de **catálogo** deve listar as regras vigentes, com pesquisa por texto e filtro por módulo. | Essencial | E, C4.7 | 6 |
| RF-PO-03 | Ao selecionar uma regra, o portal deve exibir descrição, unidade de código e link para o trecho no GitHub, na versão do código em que a regra foi registrada. | Essencial | E, C4.7 | 6 |
| RF-PO-04 | A tela de **histórico** deve apresentar a linha do tempo de cada regra, com texto anterior e novo, código que motivou a mudança nas duas versões, data e PR (com link). | Essencial | E, C4.7 | 6 |
| RF-PO-05 | A partir de um PR, o portal deve listar todas as regras que ele modificou. | Essencial | E, C4.7 | 6 |
| RF-PO-06 | A tela de **grafo** deve exibir os módulos e suas dependências (importação e chamada) com Cytoscape.js. | Essencial | E, C4.7 | 6 |
| RF-PO-07 | Ao selecionar um PR, o grafo deve destacar os módulos com unidades alteradas e seus vizinhos. | Importante | E, C4.7 | 6 |
| RF-PO-08 | O portal deve indicar a versão do catálogo exibida e a data da última sincronização. | Essencial | A§6, C4.7 | 6 |
| RF-PO-09 | Se um PR já foi mergeado mas sua tarefa `pr_mergeado` estiver pendente ou com erro, o portal deve sinalizar a defasagem. | Importante | A§6, C4.7 | 6 |
| RF-PO-10 | O portal é somente de consulta: não permite criar, editar, aprovar nem rejeitar regras ou propostas. | Essencial | A§1, M, C4.7 | 6 |
| RF-PO-11 | A API deve expor os endpoints do Quadro 10 do Cap. 4: `/auth/github`, `/auth/github/callback`, `/auth/logout`, `/api/repositorios`, `/api/repositorios/{repo}/regras`, `.../regras/{id}`, `.../regras/{id}/historico`, `.../prs/{numero}`, `.../grafo`. | Essencial | C4.7 | 6 |

### 3.8 Avaliação (`avaliacao`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-AV-01 | O sistema deve executar o replay histórico: gerar a base em um commit inicial e reprocessar os PRs mesclados na ordem de integração, com o mesmo pipeline de análise e interpretação e **publicação no GitHub desabilitada**. | Essencial | E, A§8, C3.3.1 | 7 |
| RF-AV-02 | As análises do replay devem ser registradas sem tarefa associada (`tarefa_id` nulo), com os mesmos dados de custo e configuração das execuções reais. | Essencial | A§7 | 7 |
| RF-AV-03 | O sistema deve executar a linha de base **catálogo congelado**: manter a base inicial sem manutenção e medir quanto ela fica desatualizada. | Essencial | E | 7 |
| RF-AV-04 | O sistema deve executar a linha de base **só IA no diff bruto**, sem análise estática, com o mesmo modelo e configuração. | Essencial | E | 7 |
| RF-AV-05 | O sistema pode executar a linha de base **regenerar do zero a cada PR**, para comparação de qualidade e custo. | Desejável | E | 7 |
| RF-AV-06 | O sistema deve importar o gabarito rotulado manualmente (alterou regra? qual? atualização esperada?) por PR. | Essencial | E, C3.3.2 | 7 |
| RF-AV-07 | O sistema deve calcular **detecção** (precisão, recall e F1 por PR) contra o gabarito. | Essencial | E, C3.3.3 | 7 |
| RF-AV-08 | O sistema deve apoiar a avaliação manual de **corretude** (correta, parcial, incorreta) das propostas originais, sem contar correções humanas como acerto automático. | Essencial | E, C3.3.2 | 7 |
| RF-AV-09 | O sistema deve medir **atualização**: percentual de regras documentadas desatualizadas ao longo e ao final da sequência, registrando regras esperadas ausentes. | Essencial | E, C3.3.3 | 7 |
| RF-AV-10 | O sistema deve reportar **custo**: tempo e tokens por PR. | Essencial | E, C3.3.3 | 7 |
| RF-AV-11 | O sistema deve calcular a concordância entre avaliadores (kappa de Cohen) quando houver segundo avaliador. | Desejável | E, C3.3.2 | 7 |
| RF-AV-12 | O sistema deve permitir conferir manualmente a acurácia estrutural do grafo em uma amostra de módulos (exportação da amostra para conferência). | Desejável | C3.3.3 | 7 |
| RF-AV-13 | O replay deve poder reproduzir cada interpretação a partir dos trechos gravados (`trechos_codigo`), sem consultar o GitHub. | Importante | A§7 | 7 |

## 4. Regras de negócio da ferramenta

| ID | Regra | Fonte |
|---|---|---|
| RN-01 | **Mudança de regra de negócio** é alteração em condição, cálculo, validação, fluxo de estados, regra de autorização ou contrato de entrada/saída que modifique um comportamento de domínio. | E, C3.2.2 |
| RN-02 | **Não contam, isoladamente:** renomeação, formatação, refatoração sem mudança de comportamento e alterações restritas a testes, dependências ou configuração. Em PRs mistos, só as alterações de comportamento de negócio são consideradas. | E, C3.2.2 |
| RN-03 | Dependência indica possível impacto, mas não comprova mudança de regra. Mudança estrutural não comprova mudança de comportamento. | E, A§3 |
| RN-04 | O texto gerado pelo modelo é uma **proposta**, nunca documentação vigente. | C3.2.2 |
| RN-05 | **O merge é a aceitação.** A documentação vigente só incorpora o que estiver no commit integrado à branch de referência. Aprovação de revisão sem merge não altera o catálogo. | A§6, M |
| RN-06 | PR fechado sem merge não altera o catálogo vigente. | E, A§4 |
| RN-07 | O repositório analisado é a **fonte oficial** da documentação; o banco guarda uma cópia para consulta e os dados de operação. | A§6 |
| RN-08 | Uma regra só existe a partir da sua primeira versão incorporada; inclusões ainda não incorporadas não têm `regra_id`. | A§7 |
| RN-09 | Uma versão de regra criada pelo revisor, sem proposta correspondente, é válida e fica sem `proposta_id`. | A§7 |
| RN-10 | Análise incompleta (arquivo não parseado, estrutura não tratada) não pode ser interpretada como "sem mudança de negócio". | A§3 |

## 5. Requisitos não funcionais

### 5.1 Desempenho e capacidade

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-DES-01 | O recebimento de um webhook deve responder em até **10 segundos**, sem executar AST nem chamar a IA na requisição. | Essencial | A§4 |
| RNF-DES-02 | O sistema deve operar com **um worker processando uma tarefa por vez**; a fila deve permitir mais workers sem mudança de esquema (`SKIP LOCKED`). | Essencial | A§1, A§4 |
| RNF-DES-03 | Chamadas ao Gemini e ao GitHub devem ter tempo limite configurável. | Essencial | A§5 |
| RNF-DES-04 | O custo por PR (tempo e tokens) deve ser medido e compatível com a cota do Gemini disponível para o replay (meta: 2–3 repositórios × 50–100 PRs). | Importante | E, A§5 |

### 5.2 Confiabilidade e consistência

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-CON-01 | Nenhuma entrega aceita pelo GitHub pode ser perdida: evento e tarefa são confirmados na mesma transação antes da resposta. | Essencial | A§4 |
| RNF-CON-02 | Toda etapa que toca serviço externo deve ser **idempotente** e tolerar repetição (banco e GitHub não compartilham transação). | Essencial | A§4 |
| RNF-CON-03 | Uma tarefa nunca pode ser reservada por dois workers ao mesmo tempo nem concluída por uma execução expirada. | Essencial | A§4 |
| RNF-CON-04 | Uma queda do worker não pode impedir o recebimento de webhooks enquanto API e banco estiverem disponíveis. | Essencial | A§1 |
| RNF-CON-05 | O catálogo atual nunca retrocede para um commit anterior. | Essencial | A§6 |
| RNF-CON-06 | A publicação nunca força a atualização de referências Git. | Essencial | A§6 |

### 5.3 Segurança e privacidade

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-SEG-01 | Webhooks sem assinatura válida devem ser rejeitados. | Essencial | A§4 |
| RNF-SEG-02 | Segredos (chave privada da App, segredo do webhook, credenciais OAuth, chave do Gemini, URL do banco) ficam apenas em variáveis de ambiente do servidor; nunca no código, em commits ou no frontend. | Essencial | A§4, CLAUDE.md |
| RNF-SEG-03 | A GitHub App deve pedir somente as permissões necessárias: Contents (leitura e escrita) e Pull requests (leitura e escrita). | Essencial | A§4 |
| RNF-SEG-04 | O sistema não armazena senhas de usuários. | Essencial | A§7 |
| RNF-SEG-05 | Nenhuma resposta da API pode expor dados de repositório ao qual a pessoa não tem acesso. | Essencial | A§7 |
| RNF-SEG-06 | O código dos repositórios analisados nunca é executado; é lido apenas como texto. | Essencial | A§3 |
| RNF-SEG-07 | O uso com repositórios privados deve considerar que trechos de código são copiados para o banco e que, no nível gratuito, o Gemini pode usar o conteúdo enviado; isso deve constar nas limitações. | Importante | A§5, A§7 |

### 5.4 Rastreabilidade e reprodutibilidade

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-RAS-01 | Toda versão de regra deve ser rastreável até o PR, o commit de código, a proposta original (quando houver) e os trechos de código que a sustentaram. | Essencial | E, A§7 |
| RNF-RAS-02 | Cada análise deve registrar `base_sha`, `head_sha`, modelo, versão do prompt, parâmetros, tokens e duração, para que o experimento possa ser reproduzido. | Essencial | A§5 |
| RNF-RAS-03 | Versão do Python e das dependências devem ser fixadas (`.python-version`, `uv.lock`, `pnpm-lock.yaml`). | Essencial | A§3 |
| RNF-RAS-04 | Modelo e configuração devem ser mantidos constantes nas comparações; qualquer mudança é registrada. | Essencial | A§5 |
| RNF-RAS-05 | Todas as datas são armazenadas com fuso (`timestamptz`, `datetime.now(UTC)`). | Essencial | CLAUDE.md |

### 5.5 Compatibilidade

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-COM-01 | O sistema analisa repositórios **Python 3** hospedados no **GitHub**. Outras linguagens e plataformas estão fora do escopo. | Essencial | E |
| RNF-COM-02 | O analisador usa o `ast` da versão instalada (Python 3.15) e aceita código de versões anteriores do Python 3 enquanto a sintaxe for suportada; os casos aceitos são documentados em testes. | Essencial | A§3 |
| RNF-COM-03 | O portal deve funcionar nas versões atuais dos navegadores Chrome, Firefox e Edge. | Desejável | — (proposto) |

### 5.6 Manutenibilidade e arquitetura

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-MAN-01 | A aplicação é um **monólito modular** com dois processos (API e worker) no mesmo repositório, compartilhando código e um único PostgreSQL. | Essencial | A§1, M |
| RNF-MAN-02 | API e worker não se chamam; comunicam-se apenas pelo banco. | Essencial | A§1, M |
| RNF-MAN-03 | Camadas Clean/Hexagonal: `entrypoints → adapters → application → domain`; `domain/` e `application/` são Python puro, verificado pelo Ruff (`TID251`). | Essencial | CLAUDE.md |
| RNF-MAN-04 | O núcleo `analise` não tem I/O e é reutilizado pelo worker, pelo terminal e pelo replay. | Essencial | A§3, A§8 |
| RNF-MAN-05 | Serviços externos (Gemini, GitHub, banco) ficam atrás de portas (`Protocol`), permitindo trocá-los por fakes nos testes. | Essencial | A§5, CLAUDE.md |
| RNF-MAN-06 | Esquema único com uma sequência de migrações Alembic compartilhada por API e worker. | Essencial | A§2 |
| RNF-MAN-07 | `make verificar` (Ruff, mypy strict, pytest, Biome, tsc) deve passar antes de cada entrega. | Essencial | CLAUDE.md |
| RNF-MAN-08 | Todo caso de uso e regra de domínio tem teste unitário com fakes; adapters de banco têm teste de integração com PostgreSQL real. | Essencial | CLAUDE.md |
| RNF-MAN-09 | Frontend: componentes apenas visuais, lógica em hooks, TypeScript estrito, `fetch` centralizado no cliente da API. | Essencial | frontend/CLAUDE.md |

### 5.7 Usabilidade

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-USA-01 | Identificadores, mensagens, comentários no PR e textos do portal em português. | Importante | CLAUDE.md |
| RNF-USA-02 | O comentário no PR deve ser curto e legível na própria interface do GitHub, com referências clicáveis ao código. | Importante | E, A§6 |
| RNF-USA-03 | O Markdown do catálogo deve ser legível diretamente na aba "Files changed" do PR. | Essencial | A§6, C4.3.1 |
| RNF-USA-04 | As telas do portal devem apresentar explicitamente os estados de carregamento, erro e vazio. | Importante | A§10.2 |
| RNF-USA-05 | Uma pessoa deve abrir uma tela diretamente pelo endereço (rotas da SPA com fallback). | Importante | A§2, A§10.2 |

### 5.8 Implantação e operação

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-OPE-01 | API e worker são hospedados na Render; o PostgreSQL usa uma oferta gratuita (provedor a definir). | Essencial | A§4 |
| RNF-OPE-02 | A API deve ter endereço público HTTPS para receber webhooks. | Essencial | A§4 |
| RNF-OPE-03 | O build estático do portal é servido pela própria API. | Importante | A§1, A§4 |
| RNF-OPE-04 | O ambiente local deve subir com `make db`, `make migrar`, `make api`, `make worker` e `make portal`, com encaminhamento de webhooks para a API local. | Essencial | A§4, CLAUDE.md |
| RNF-OPE-05 | Deve haver backup do banco e procedimento de reinício dos processos. | Importante | A§1, A§4 |
| RNF-OPE-06 | Entregas de webhook com falha devem poder ser conferidas e reenviadas manualmente (o GitHub não reenvia sozinho). | Importante | A§4 |
| RNF-OPE-07 | O histórico de etapas e tentativas no banco deve permitir diagnosticar uma tarefa sem acesso aos logs do servidor. | Importante | A§4 |

## 6. Pontos para decisão

Itens em que as fontes divergem ou que a arquitetura (seção 10.3) mantém em aberto e que afetam requisitos. Cada um indica os requisitos impactados.

| # | Ponto | Situação nas fontes | Requisitos afetados |
|---|---|---|---|
| D1 | **Revisão das propostas pelo portal.** | O escopo e o Cap. 3 (3.2.4) citam "revisão das propostas pendentes" no portal; a arquitetura, o Mapa e o Cap. 4 definem portal só de consulta, com revisão no GitHub. Este documento seguiu a arquitetura (RF-PO-10). O Cap. 3 precisa ser alinhado. | RF-PO-10 |
| D2 | **Aceitar/ajustar/rejeitar cada proposta.** | Escopo e Cap. 3 falam em decisão por proposta; na arquitetura, a decisão é sobre o PR inteiro (merge) e o ajuste é editar o arquivo. Rejeitar uma proposta = apagar a regra do arquivo antes do merge? | RN-05, RF-DOC-08 |
| D3 | **Propostas pendentes visíveis.** | O escopo diz que propostas pendentes ficam "identificadas separadamente". Elas devem aparecer no portal (somente leitura) ou só no PR? | RF-PO-* |
| D4 | **Como a base inicial é revisada e incorporada.** | Arquitetura (§9) exige revisão no GitHub; o mecanismo não está definido (PR de bootstrap aberto pelo bot? comando no terminal?). | RF-DOC-04, RF-DOC-05 |
| D5 | **Formato e caminhos do catálogo e regra do identificador estável.** | Em aberto (A§10.3). Ex.: `docs/lastro/catalogo.json` + um Markdown por módulo; identificador `RN-<modulo>-<nnn>` ou UUID curto. | RF-DOC-01–03 |
| D6 | **Testes na varredura da base.** | Cap. 4 não define se arquivos de teste ficam fora da extração. Pela RN-02, a proposta é excluí-los. | RF-AN-01, RF-DOC-04 |
| D7 | **Profundidade do contexto.** | Cap. 4 propõe vizinhos de um nível; A§10.3 mantém em aberto. Há limite de tamanho do contexto por chamada? | RF-AN-11 |
| D8 | **Conflito com ajustes humanos.** | Quando o revisor edita a doc e depois o dev faz novo commit, a nova análise preserva a edição ou abre conflito? Como o conflito é apresentado? | RF-GH-12 |
| D9 | **PRs de forks.** | Sem escrita na branch, só comentar? Ou comentar com o conteúdo proposto para o revisor copiar? | RF-GH-13 |
| D10 | **Prazos e limites da fila.** | Intervalo de consulta, duração da reserva, nº de tentativas, intervalo entre tentativas. Etapas em colunas ou tabela própria. | RF-PR-02–06, RF-PR-10 |
| D11 | **Grafo histórico no replay.** | O banco guarda só o commit atual; o replay recalcula o grafo com `ast` por commit ou o banco guarda cópia? | RF-AV-01 |
| D12 | **Sessão do portal.** | Duração, armazenamento do token do usuário, intervalo de reverificação (`verificado_em`). | RF-AC-01–04 |
| D13 | **Plano de hospedagem.** | Worker da Render não tem instância gratuita; serviço web gratuito hiberna (risco ao RNF-DES-01); provedor do banco indefinido. | RNF-OPE-01, RNF-DES-01 |
| D14 | **Cotas do Gemini.** | Cota do nível gratuito vs. volume do replay ainda não verificada. | RNF-DES-04, RF-AV-* |
| D15 | **Gatilho da geração da base.** | Quem dispara: comando de terminal, evento `installation` da GitHub App, ou ambos? Não há evento previsto na tabela de webhooks. | RF-DOC-04, RF-GH-02 |

## 7. Fora do escopo

- Outras linguagens além de Python e outras plataformas além do GitHub.
- Edição automática do código analisado.
- Atualização de documentos escritos por humanos fora do catálogo do Lastro.
- Integração com agentes de IA (caminho C), tratada como trabalho futuro.
- Edição, aprovação ou rejeição de documentação pelo portal.
- Microsserviços e broker de mensagens.

## 8. Rastreabilidade com os objetivos específicos

| Objetivo específico (Cap. 1) | Requisitos principais |
|---|---|
| 1. Gerar catálogo inicial e grafo a partir da AST | RF-AN-01–10, RF-IA-06, RF-DOC-01–05 |
| 2. Detectar mudanças a cada PR e propor atualizações com IA | RF-AN-05–12, RF-IA-01–08, RF-DOC-06, RN-01–04 |
| 3. Revisão humana no PR, incorporando só o aprovado e integrado | RF-GH-01–14, RF-DOC-07–13, RF-PR-01–11, RN-05–06 |
| 4. Portal com catálogo, histórico por PR e grafo | RF-AC-01–05, RF-PO-01–11 |
| 5. Avaliar detecção, corretude e atualização com replay e linhas de base | RF-AV-01–13, RNF-RAS-01–04 |
