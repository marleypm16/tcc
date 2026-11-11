# Lastro — Especificação de requisitos

Versão 0.7 · 10/11/2026 · rascunho para revisão (em aberto: D5, D13, D14, D17, D18)

Este documento reúne os requisitos funcionais e não funcionais do Lastro, levantados a partir de [escopo-tcc.md](escopo-tcc.md), [arquitetura-tcc.md](arquitetura-tcc.md), [Mapa da arquitetura do TCC](<Mapa da arquitetura do TCC.md>) e dos capítulos 1, 3 e 4 revisados. As decisões já tomadas (D1–D4, D6–D12, D15, D16, D19, D20) foram incorporadas a esses documentos e estão resumidas na seção 10.1 da arquitetura. Aqui ficam apenas os pontos ainda em aberto (seção 6).

## 1. Convenções

**Identificadores.** `RF-<grupo>-<nn>` para requisitos funcionais, `RNF-<categoria>-<nn>` para não funcionais e `RN-<nn>` para regras de negócio da própria ferramenta. Os identificadores são estáveis: um requisito removido continua na tabela, riscado e com o motivo, e seu número não é reaproveitado.

**Prioridade.**

| Prioridade | Significado |
|---|---|
| **Essencial** | Sem ele, a pergunta de pesquisa não pode ser respondida ou o fluxo principal não funciona. |
| **Importante** | Faz parte da entrega descrita no TCC, mas a avaliação principal (replay) funciona sem ele. |
| **Desejável** | Melhora a operação ou a experiência; pode ficar como trabalho futuro sem prejuízo do TCC. |

**Fontes.** `E` = escopo-tcc.md · `A§n` = arquitetura-tcc.md, seção n · `M` = Mapa da arquitetura · `C1`, `C3.x`, `C4.x` = capítulos revisados · `Dn` = decisão numerada (as tomadas estão em A§10.1; as em aberto, na seção 6 deste documento).

**Incremento.** Número da etapa da ordem de implementação (arquitetura, seção 9) em que o requisito é entregue: 1 analisador local · 2 catálogo e Gemini · 3 persistência e fila · 4 GitHub App, ativação e publicação no PR · 5 revisão no portal e incorporação após o merge · 6 portal de consulta · 7 avaliação.

## 2. Visão geral

### 2.1 Objetivo do sistema

Manter a documentação das regras de negócio de repositórios Python no GitHub correta, atualizada e rastreável. A cada pull request, o Lastro identifica as unidades de código alteradas com análise estática (`ast`), usa o Gemini para decidir se alguma regra de negócio mudou e registra propostas de atualização da documentação. O bot comenta no PR o resumo das propostas, com link para o portal, onde o revisor aprova, edita ou rejeita cada uma. Após o merge, as propostas aprovadas são incorporadas ao catálogo, mantido no banco e consultado pelo portal.

### 2.2 Atores

| Ator | Descrição | Onde interage |
|---|---|---|
| **Desenvolvedor** | Abre e atualiza PRs no repositório acompanhado. | GitHub |
| **Revisor** | Pessoa com permissão de escrita no repositório. Recebe o comentário no PR, revisa as propostas no portal (aprova, edita ou rejeita) e realiza o merge. | GitHub e portal |
| **Consultor do portal** | Qualquer pessoa com acesso ao repositório no GitHub que consulta catálogo, histórico, propostas e grafo. Inclui novos integrantes da equipe. | Portal |
| **Administrador da instalação** | Instala a GitHub App nos repositórios, o que dispara a geração da base inicial, e pode dispará-la também pelo terminal. | GitHub e terminal |
| **Pesquisador** | Executa o replay histórico, as linhas de base e coleta as métricas (o autor do TCC). | Terminal |
| **GitHub** (sistema) | Envia webhooks, fornece código e recebe comentários e status. | API e worker |
| **Gemini** (sistema) | Interpreta as mudanças e redige as regras. | Worker |

### 2.3 Fluxos cobertos

1. **Geração da base:** instalação da App (ou comando de terminal) → AST → grafo + catálogo inicial → PR de ativação com `.lastro.yml` → revisão no portal → merge → catálogo vigente.
2. **Análise por PR:** webhook → tarefa → comparação de AST → contexto → Gemini → validação → propostas no banco → comentário com link para o portal + status no PR.
3. **Revisão:** portal → aprovar, editar ou rejeitar cada proposta (rejeitar = descartar ou refazer com motivo) → status do PR atualizado.
4. **Incorporação:** merge → tarefa `pr_mergeado` → propostas aprovadas viram versões vigentes das regras.
5. **Consulta:** login GitHub → repositórios acessíveis → catálogo, histórico, propostas, grafo.
6. **Avaliação:** replay de PRs mesclados → métricas → comparação com linhas de base.

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
| RF-AN-11 | Para cada unidade adicionada, removida ou alterada, o sistema deve selecionar o contexto: código nas duas versões, regras vinculadas à unidade e unidades vizinhas no grafo (quem chama e quem é chamado) com suas regras. A profundidade é fixa em **um nível**: apenas vizinhos diretos (D7). | Essencial | A§3, C4.5.2, D7 | 1–2 |
| RF-AN-12 | O sistema deve distinguir, no resultado, as unidades **alteradas** das unidades de **contexto**; vizinhas nunca são tratadas como alteradas. | Essencial | A§7, C4.5.2 | 1 |
| RF-AN-13 | O sistema deve permitir executar a comparação de duas versões pelo terminal, sem banco nem GitHub, exibindo as diferenças estruturais e o contexto. | Essencial | A§9 | 1 |
| RF-AN-14 | O sistema deve excluir arquivos de teste da extração e da comparação (ex.: diretórios `tests/`, arquivos `test_*.py`, `*_test.py` e `conftest.py`), com o critério configurável no arquivo `.lastro.yml` do repositório (RF-DOC-15). *Provisório (D6).* | Essencial | RN-02, D6 | 1 |

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
| RF-IA-09 | Ao refazer uma proposta rejeitada (RF-PO-14), o prompt deve incluir, além do contexto original, a proposta rejeitada e o motivo escrito pelo revisor. A nova proposta substitui a anterior, que permanece no histórico. | Importante | D2 | 5 |

### 3.3 Catálogo e documentação (`documentacao`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-DOC-01 | Cada regra do catálogo deve ter: identificador, título, descrição, módulo, unidade de código, arquivo e intervalo de linhas, commit do código, PR de origem e situação (`vigente` ou `removida`). | Essencial | C4.3 | 2 |
| RF-DOC-02 | O identificador da regra deve ser atribuído na criação, ser independente da posição no código e se manter quando a unidade mudar de linha, arquivo ou nome. | Essencial | E, C4.3 | 2 |
| RF-DOC-03 | O sistema deve poder exportar o catálogo vigente em **JSON** e **Markdown** para o repositório, como cópia de leitura. Formato, caminhos e mecanismo de publicação seguem D5. | Desejável | A§6, C4.3.1, D2, D5 | 5 |
| RF-DOC-04 | O sistema deve gerar a base inicial de um repositório a partir de uma versão de referência: catálogo inicial por módulo e unidade + grafo de módulos. | Essencial | E, C3.2.1, C4.4 | 2 |
| RF-DOC-05 | A base inicial deve passar por revisão no portal e pelo merge do PR de ativação antes de ser tratada como documentação vigente (RF-DOC-15). | Essencial | E, A§9, D4 | 4/5 |
| RF-DOC-06 | Na incorporação, o sistema deve aplicar ao catálogo as propostas **aprovadas** (incluir, alterar ou remover regras), usando o texto editado pelo revisor quando houver. | Essencial | A§6, D2 | 5 |
| RF-DOC-07 | Após o merge, o sistema deve incorporar as propostas aprovadas do PR, criando uma nova versão para cada regra afetada, vinculada ao commit efetivamente incorporado. | Essencial | A§6, C4.6.4, D2 | 5 |
| RF-DOC-08 | A versão incorporada deve ser marcada `editada_por_humano` quando o texto aprovado diferir da proposta original. | Essencial | A§6, A§7 | 5 |
| RF-DOC-09 | A incorporação deve ser idempotente e registrar repositório, PR, commit do código, propostas incorporadas e horário. | Essencial | A§6 | 5 |
| RF-DOC-10 | O catálogo atual não deve retroceder quando merges chegarem fora de ordem: versões podem entrar no histórico, mas `commit_catalogo_atual` só avança para commits descendentes. | Essencial | A§6, A§7 | 5 |
| RF-DOC-11 | Se o PR for mesclado com propostas pendentes ou com análise desatualizada (o head analisado é diferente do head mesclado), o sistema deve registrar a inconsistência e sinalizar o catálogo como defasado. Propostas pendentes de PR já mesclado podem ser revisadas depois e, quando aprovadas, são incorporadas imediatamente. | Importante | A§6, D2 | 5 |
| RF-DOC-12 | Módulos removidos devem ser marcados como inativos, sem exclusão, preservando as versões antigas das regras. | Importante | A§7 | 5 |
| RF-DOC-13 | As propostas originais do modelo devem ser imutáveis e guardadas separadamente das decisões do revisor e das versões incorporadas. | Essencial | A§6, A§7 | 3 |
| RF-DOC-14 | A geração da base inicial deve poder ser disparada de duas formas: automaticamente, quando a GitHub App é instalada no repositório, e manualmente, por comando de terminal (usado também pelo replay). | Essencial | D15 | 2/4 |
| RF-DOC-15 | Após gerar a base inicial, o bot deve abrir na branch principal um **PR de ativação** ("Lastro: base inicial"), que adiciona o arquivo de configuração `.lastro.yml` e traz na descrição o resumo do catálogo inicial e o link para revisá-lo no portal. As regras da base são as propostas desse PR e seguem o mesmo fluxo de revisão dos demais; a base se torna vigente com o merge, vinculada ao commit de referência. | Essencial | D4, D2 | 4/5 |
| RF-DOC-16 | Quando chegar uma nova versão do PR, as decisões já tomadas sobre unidades cujo código não mudou entre as duas versões são mantidas. As demais propostas voltam para `pendente`, e o portal mostra a decisão anterior como referência. | Importante | D16 | 5 |
| RF-DOC-17 | PR fechado sem merge descarta suas propostas e decisões, que permanecem no histórico para a avaliação. | Essencial | RN-06, D2 | 5 |
| RF-DOC-18 | Se o PR de ativação for fechado sem merge, o repositório volta à situação `inativo`. A reativação pode ser pedida pelo portal (RF-PO-18) ou pelo terminal e gera uma nova base e um novo PR de ativação. | Importante | D20 | 4/5 |

### 3.4 Integração com o GitHub (`integracao_github`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-GH-01 | O sistema deve receber webhooks em `POST /webhooks/github` e validar a assinatura com o segredo compartilhado, rejeitando entregas inválidas. | Essencial | A§4, C4.6.1 | 4 |
| RF-GH-02 | O sistema deve tratar os eventos `pull_request` conforme a tabela: `opened`, `reopened` e `synchronize` → `analisar_pr`; `closed` com merge → `pr_mergeado`; `closed` sem merge → registrar, descartar tarefas pendentes e aplicar RF-DOC-17. | Essencial | A§4, C4.6.1, D2 | 4 |
| RF-GH-03 | Evento e tarefa devem ser gravados na mesma transação; a resposta ao GitHub só é enviada após o commit. Eventos ignorados podem ser registrados com o motivo, sem tarefa. | Essencial | A§4, C4.6.1 | 3–4 |
| RF-GH-04 | ~~Reconhecer o `synchronize` causado pelo commit de documentação do próprio bot e não gerar tarefa.~~ *Removido (D2): o bot não faz mais commit na branch do PR.* | — | — | — |
| RF-GH-05 | O worker deve obter um token de instalação com a chave privada da GitHub App para ler código, comentar e publicar status no repositório. | Essencial | A§4 | 4 |
| RF-GH-06 | O sistema deve obter a lista de arquivos Python alterados no PR e o conteúdo de cada um nas versões base e head, inclusive em PRs vindos de forks. | Essencial | C4.5.1, D9 | 4 |
| RF-GH-07 | ~~Commit dos artefatos JSON e Markdown na branch do PR.~~ *Removido (D2): as propostas ficam no banco e são revisadas no portal.* | — | — | — |
| RF-GH-08 | ~~Conferir a branch antes de publicar o commit e atualizar a referência sem forçar.~~ *Removido (D2).* | — | — | — |
| RF-GH-09 | O worker deve publicar no PR um comentário curto com o resumo das propostas (regras incluídas, alteradas e removidas, com as unidades de código correspondentes) e o link para a tela de revisão do PR no portal. Em novas análises do mesmo PR, o comentário existente é atualizado em vez de criar outro. | Essencial | E, A§6, C4.6.3, D2 | 4 |
| RF-GH-10 | Quando a análise concluir que não houve mudança de regra de negócio, o sistema não cria propostas e apenas comenta essa conclusão. | Importante | C4.6.3 | 4 |
| RF-GH-11 | A publicação de comentário e status deve ser idempotente: antes de criar, o worker verifica se a publicação para a mesma análise e commit já existe. | Essencial | A§4, C4.6.2 | 4 |
| RF-GH-12 | ~~Preservar ajustes humanos feitos na branch ou apresentá-los como conflito.~~ *Removido (D8): a edição é feita só no portal.* | — | — | — |
| RF-GH-13 | ~~Tratar a falta de permissão de escrita na branch (forks, branches protegidas).~~ *Removido (D9): o bot não escreve na branch; PRs de forks seguem o fluxo normal.* | — | — | — |
| RF-GH-14 | Após o merge, o sistema deve resolver o commit incorporado conforme o tipo de merge (merge comum, squash ou rebase). | Essencial | A§6 | 5 |
| RF-GH-15 | Enquanto o PR de ativação de um repositório não for mesclado, os demais PRs desse repositório não são analisados: o bot apenas comenta que a base inicial ainda está em revisão, com link para o PR de ativação e para o portal. | Essencial | D4 | 4 |
| RF-GH-16 | O sistema deve tratar os eventos `installation` e `installation_repositories` (repositório adicionado) criando uma tarefa `gerar_base` para cada repositório. | Essencial | D4, D15 | 4 |
| RF-GH-17 | O worker deve publicar no head do PR o status `lastro/documentacao`: `pending` enquanto houver propostas pendentes; `success` quando todas forem decididas ou quando não houver mudança de regra; `error` quando a análise falhar. O dono do repositório pode torná-lo obrigatório para bloquear o merge. | Essencial | D2 | 4 |
| RF-GH-18 | Cada decisão tomada no portal deve atualizar o status do PR (RF-GH-17) por meio de uma tarefa `atualizar_status`, sem que a API chame o GitHub para isso. | Essencial | D2, RNF-MAN-02 | 5 |

### 3.5 Processamento e fila (`processamento`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-PR-01 | A fila deve ser a tabela `tarefas`, com tipos `analisar_pr`, `pr_mergeado`, `gerar_base` (D4), `reanalisar_proposta` e `atualizar_status` (D2) e estados `pendente`, `processando`, `concluida`, `erro` e `descartada`. | Essencial | A§4, A§7, D2, D4 | 3 |
| RF-PR-02 | O worker deve consultar periodicamente a fila, com intervalo configurável quando vazia (padrão: 5 s), e reservar uma tarefa por vez com `FOR UPDATE SKIP LOCKED` em transação curta, confirmada antes da análise. | Essencial | A§4, D10 | 3 |
| RF-PR-03 | Uma entrega repetida (mesmo `X-GitHub-Delivery`) deve ser reconhecida e não gerar outra tarefa. | Essencial | A§4 | 3 |
| RF-PR-04 | A reserva deve ter prazo (`reserva_ate`) e token (`reserva_token`); o prazo padrão é de 5 min, renovado a cada 1 min enquanto o worker estiver ativo; conclusão e renovação conferem o token para que uma execução antiga não conclua tarefa retomada. | Essencial | A§4, D10 | 3 |
| RF-PR-05 | Na inicialização e periodicamente, o worker deve recuperar reservas expiradas, devolvendo a tarefa a `pendente` ou marcando `erro` se o limite de tentativas foi atingido. | Essencial | A§4, C4.6.2 | 3 |
| RF-PR-06 | Falhas temporárias do Gemini ou do GitHub devem reagendar a tarefa (`disponivel_em`). Valores padrão, configuráveis: até 5 tentativas, com espera crescente de 30 s, 1, 2, 4 e 8 min, ou o `Retry-After` informado pelo serviço, quando houver. Esgotado o limite, a tarefa vai para `erro` preservando o histórico. | Essencial | A§4, C4.6.2, D10 | 3 |
| RF-PR-07 | Uma tarefa retomada deve reaproveitar etapas já persistidas (ex.: análise salva, publicação pendente) em vez de refazê-las. | Importante | A§4 | 3–4 |
| RF-PR-08 | A análise deve ser deduplicada por PR, `base_sha`, `head_sha`, modelo e versão do prompt. O recálculo de uma proposta rejeitada (`reanalisar_proposta`) fica fora dessa deduplicação e é vinculado à proposta que substitui. | Essencial | A§4, A§7, D2 | 3 |
| RF-PR-09 | Ao fechar um PR sem merge ou ao chegar nova versão, tarefas pendentes que perderam a finalidade devem ser marcadas `descartada`. | Importante | A§4, C4.6.1 | 3–4 |
| RF-PR-10 | O sistema deve registrar as etapas e tentativas de cada tarefa (recebimento, análise, chamadas ao Gemini, publicação, erros, incorporação) em uma tabela própria, `etapas_tarefa`, com tarefa, etapa, início, fim, resultado e erro. | Importante | A§4, D10 | 3 |
| RF-PR-11 | Deve existir um procedimento operacional para reprocessar tarefas em `erro` após correção. | Desejável | A§4 | 3 |

### 3.6 Acesso e autenticação (`acesso`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-AC-01 | O portal deve exigir login com a conta do GitHub, pelo fluxo de autorização de usuário da GitHub App, sem armazenar senhas. | Essencial | A§7, C4.7 | 5 |
| RF-AC-02 | Após o login, o sistema deve consultar os repositórios da instalação acessíveis à pessoa e registrar essa relação (`usuario_repositorio`), incluindo se ela tem permissão de escrita. | Essencial | A§7, D2 | 5 |
| RF-AC-03 | Todas as consultas do portal devem ser restritas aos repositórios acessíveis à pessoa autenticada. | Essencial | A§7, C4.7 | 5 |
| RF-AC-04 | A permissão deve ser verificada novamente no GitHub quando `verificado_em` tiver mais de 1 h. | Importante | A§7, D12 | 5 |
| RF-AC-05 | A pessoa deve poder encerrar a sessão (`POST /auth/logout`). | Importante | C4.7 | 5 |
| RF-AC-06 | A sessão deve usar um cookie `HttpOnly`, `Secure` e `SameSite=Lax`, com duração de 8 h (o prazo do token de usuário da GitHub App). Ao expirar, a pessoa faz login novamente, sem renovação automática. | Importante | D12 | 5 |
| RF-AC-07 | Somente pessoas com permissão de escrita no repositório podem aprovar, editar ou rejeitar propostas; as demais só consultam (RN-11). | Essencial | D2 | 5 |

### 3.7 Portal (`catalogo` + `documentacao` + frontend)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-PO-01 | O portal deve listar os repositórios acessíveis com a versão do catálogo de cada um e indicar quando a base inicial ainda está em revisão. | Essencial | C4.7, D4 | 6 |
| RF-PO-02 | A tela de **catálogo** deve listar as regras vigentes, com pesquisa por texto e filtro por módulo. | Essencial | E, C4.7 | 6 |
| RF-PO-03 | Ao selecionar uma regra, o portal deve exibir descrição, unidade de código e link para o trecho no GitHub, na versão do código em que a regra foi registrada. | Essencial | E, C4.7 | 6 |
| RF-PO-04 | A tela de **histórico** deve apresentar a linha do tempo de cada regra, com texto anterior e novo, código que motivou a mudança nas duas versões, data, PR (com link) e quem aprovou. | Essencial | E, C4.7, D2 | 6 |
| RF-PO-05 | A partir de um PR, o portal deve listar todas as regras que ele modificou. | Essencial | E, C4.7 | 6 |
| RF-PO-06 | A tela de **grafo** deve exibir os módulos e suas dependências (importação e chamada) com Cytoscape.js. | Essencial | E, C4.7 | 6 |
| RF-PO-07 | Ao selecionar um PR, o grafo deve destacar os módulos com unidades alteradas e seus vizinhos. | Importante | E, C4.7 | 6 |
| RF-PO-08 | O portal deve indicar a versão do catálogo exibida e a data da última incorporação. | Essencial | A§6, C4.7 | 6 |
| RF-PO-09 | Se um PR já foi mesclado mas sua tarefa `pr_mergeado` estiver pendente ou com erro, ou se ele ainda tiver propostas pendentes, o portal deve sinalizar a defasagem. | Importante | A§6, C4.7, D2 | 6 |
| RF-PO-10 | O portal permite revisar propostas (RF-PO-13), inclusive as da base inicial (RF-DOC-15). Regras vigentes não são editadas diretamente, fora de uma proposta; essa edição fica como versão futura. | Essencial | D1, D2 | 5 |
| RF-PO-11 | A API deve expor os endpoints do Quadro 10 do Cap. 4 (`/auth/github`, `/auth/github/callback`, `/auth/logout`, `/api/repositorios`, `/api/repositorios/{repo}/regras`, `.../regras/{id}`, `.../regras/{id}/historico`, `.../prs/{numero}`, `.../grafo`) e os de revisão: listar as propostas de um PR (inclusive o de ativação), aprovar (com ou sem edição), aprovar todas e rejeitar (descartar ou refazer), além do pedido de reativação de um repositório inativo. | Essencial | C4.7, D2 | 5–6 |
| RF-PO-12 | A tela de **revisão do PR** deve listar as propostas do PR, separadas do catálogo vigente, com situação (`pendente`, `aprovada`, `editada`, `descartada`, `refazendo`), texto atual e proposto, código antes e depois e justificativa do modelo. Quem não pode revisar vê a mesma tela somente para leitura. | Essencial | E, D2, D3 | 5 |
| RF-PO-13 | O revisor deve poder, para cada proposta: **aprovar**; **editar** o título e a descrição e aprovar; ou **rejeitar**. Deve ser possível aprovar todas as propostas pendentes de uma vez. | Essencial | E, C3.2.4, D2 | 5 |
| RF-PO-14 | Ao rejeitar, o revisor escolhe entre **descartar** (não é mudança de regra) e **refazer com motivo**. O pedido de refazer cria uma tarefa `reanalisar_proposta` (RF-IA-09). O limite é de 3 recálculos por proposta; depois dele, restam editar ou descartar. | Importante | D2 | 5 |
| RF-PO-15 | Decisões concorrentes sobre a mesma proposta devem ser detectadas por controle de versão: a segunda decisão é recusada com aviso, e a tela é recarregada. | Importante | D8 | 5 |
| RF-PO-16 | O revisor pode incluir manualmente, durante a revisão de um PR, uma regra que o modelo não propôs (RN-09). | Desejável | A§7, D2 | 5 |
| RF-PO-17 | Toda decisão deve registrar quem decidiu, quando, o tipo de decisão e o texto final ou o motivo. | Essencial | RNF-RAS-01, D2 | 5 |
| RF-PO-18 | Para um repositório inativo, o portal deve exibir a situação e, a quem tem permissão de escrita, a opção de reativá-lo, que cria uma tarefa `gerar_base`. | Importante | D20 | 5 |

### 3.8 Avaliação (`avaliacao`)

| ID | Requisito | Prioridade | Fonte | Inc. |
|---|---|---|---|---|
| RF-AV-01 | O sistema deve executar o replay histórico: gerar a base em um commit inicial e reprocessar os PRs mesclados na ordem de integração, com o mesmo pipeline de análise e interpretação e **publicação no GitHub desabilitada**. O grafo de cada commit é recalculado com `ast`, sem cópia no banco (D11). | Essencial | E, A§8, C3.3.1, D11 | 7 |
| RF-AV-14 | No replay não há revisão: a base inicial e as propostas originais de cada PR são incorporadas automaticamente ao catálogo, sem edição, antes de processar o PR seguinte. Essas versões são registradas como incorporação automática, sem decisão de revisor, e o catálogo do replay fica separado do catálogo real. | Essencial | D19, C3.3.1 | 7 |
| RF-AV-02 | As análises do replay devem ser registradas sem tarefa associada (`tarefa_id` nulo), com os mesmos dados de custo e configuração das execuções reais. | Essencial | A§7 | 7 |
| RF-AV-03 | O sistema deve executar a linha de base **catálogo congelado**: manter a base inicial sem manutenção e medir quanto ela fica desatualizada. | Essencial | E | 7 |
| RF-AV-04 | O sistema deve executar a linha de base **só IA no diff bruto**, sem análise estática, com o mesmo modelo e configuração. | Essencial | E | 7 |
| RF-AV-05 | O sistema pode executar a linha de base **regenerar do zero a cada PR**, para comparação de qualidade e custo. | Desejável | E | 7 |
| RF-AV-06 | O sistema deve importar o gabarito rotulado manualmente (alterou regra? qual? atualização esperada?) por PR. | Essencial | E, C3.3.2 | 7 |
| RF-AV-07 | O sistema deve calcular **detecção** (precisão, recall e F1 por PR) contra o gabarito. | Essencial | E, C3.3.3 | 7 |
| RF-AV-08 | O sistema deve apoiar a avaliação manual de **corretude** (correta, parcial, incorreta) das propostas originais, sem contar edições ou recálculos pedidos pelo revisor como acerto automático. | Essencial | E, C3.3.2 | 7 |
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
| RN-05 | **Aprovação + merge é a aceitação.** Uma proposta aprovada no portal só se torna vigente quando o PR é mesclado. O merge não incorpora propostas pendentes ou descartadas. A base inicial segue a mesma regra, pelo PR de ativação (RF-DOC-15). | D2, D4 |
| RN-06 | PR fechado sem merge não altera o catálogo vigente, e as decisões tomadas sobre suas propostas são descartadas. | E, A§4, D2 |
| RN-07 | O **banco** é a fonte oficial da documentação. Arquivos exportados para o repositório (RF-DOC-03) são cópias de leitura. | D2 |
| RN-08 | Uma regra só existe a partir da sua primeira versão incorporada; inclusões ainda não incorporadas não têm `regra_id`. | A§7 |
| RN-09 | Uma versão de regra criada pelo revisor, sem proposta correspondente, é válida e fica sem `proposta_id`. | A§7 |
| RN-10 | Análise incompleta (arquivo não parseado, estrutura não tratada) não pode ser interpretada como "sem mudança de negócio". | A§3 |
| RN-11 | Só quem tem permissão de escrita no repositório no GitHub pode decidir sobre propostas. | D2 |

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
| RNF-CON-04 | Uma queda do worker não pode impedir o recebimento de webhooks nem as decisões no portal enquanto API e banco estiverem disponíveis. | Essencial | A§1 |
| RNF-CON-05 | O catálogo atual nunca retrocede para um commit anterior. | Essencial | A§6 |
| RNF-CON-06 | Quando houver exportação para o repositório (RF-DOC-03), ela nunca força a atualização de referências Git. | Desejável | A§6 |
| RNF-CON-07 | Uma decisão no portal e a tarefa `atualizar_status` correspondente são gravadas na mesma transação. | Essencial | D2 |

### 5.3 Segurança e privacidade

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-SEG-01 | Webhooks sem assinatura válida devem ser rejeitados. | Essencial | A§4 |
| RNF-SEG-02 | Segredos (chave privada da App, segredo do webhook, credenciais OAuth, chave do Gemini, URL do banco) ficam apenas em variáveis de ambiente do servidor; nunca no código, em commits ou no frontend. | Essencial | A§4, CLAUDE.md |
| RNF-SEG-03 | A GitHub App deve pedir somente as permissões necessárias: Contents (leitura e escrita; a escrita é usada só para criar a branch e o `.lastro.yml` do PR de ativação e, se implementada, a exportação RF-DOC-03), Pull requests (leitura e escrita, para abrir o PR de ativação e comentar) e Commit statuses (leitura e escrita). | Essencial | A§4, D2, D4 |
| RNF-SEG-04 | O sistema não armazena senhas de usuários. O token de usuário do GitHub fica cifrado no banco, vinculado à sessão, e nunca é enviado ao navegador. | Essencial | A§7, D12 |
| RNF-SEG-05 | Nenhuma resposta da API pode expor dados de repositório ao qual a pessoa não tem acesso, e nenhuma operação de revisão pode ser aceita sem permissão de escrita (RN-11). | Essencial | A§7, D2 |
| RNF-SEG-06 | O código dos repositórios analisados nunca é executado; é lido apenas como texto. | Essencial | A§3 |
| RNF-SEG-07 | O uso com repositórios privados deve considerar que trechos de código são copiados para o banco e que, no nível gratuito, o Gemini pode usar o conteúdo enviado; isso deve constar nas limitações. | Importante | A§5, A§7 |
| RNF-SEG-08 | As operações de revisão do portal (requisições que alteram estado) devem ser protegidas contra CSRF. | Essencial | D2 |

### 5.4 Rastreabilidade e reprodutibilidade

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-RAS-01 | Toda versão de regra deve ser rastreável até o PR, o commit de código, a proposta original (quando houver), a decisão do revisor e os trechos de código que a sustentaram. | Essencial | E, A§7, D2 |
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
| RNF-USA-02 | O comentário no PR deve ser curto e legível na própria interface do GitHub, com referências clicáveis ao código e um link direto para a revisão no portal. | Importante | E, A§6, D2 |
| RNF-USA-03 | ~~O Markdown do catálogo deve ser legível na aba "Files changed" do PR.~~ *Removido (D2): a documentação não vai mais na branch do PR.* | — | — |
| RNF-USA-04 | As telas do portal devem apresentar explicitamente os estados de carregamento, erro e vazio. | Importante | A§10.2 |
| RNF-USA-05 | Uma pessoa deve abrir uma tela diretamente pelo endereço (rotas da SPA com fallback), inclusive pelo link do comentário no PR. | Importante | A§2, A§10.2 |
| RNF-USA-06 | A tela de revisão deve permitir decidir uma proposta sem trocar de tela, com o texto atual e o proposto e o código antes e depois visíveis lado a lado. | Importante | D2 |

### 5.8 Implantação e operação

| ID | Requisito | Prioridade | Fonte |
|---|---|---|---|
| RNF-OPE-01 | API e worker são hospedados na Render; o PostgreSQL usa uma oferta gratuita (provedor a definir, D13). | Essencial | A§4 |
| RNF-OPE-02 | A API deve ter endereço público HTTPS para receber webhooks. | Essencial | A§4 |
| RNF-OPE-03 | O build estático do portal é servido pela própria API. | Importante | A§1, A§4 |
| RNF-OPE-04 | O ambiente local deve subir com `make db`, `make migrar`, `make api`, `make worker` e `make portal`, com encaminhamento de webhooks para a API local. | Essencial | A§4, CLAUDE.md |
| RNF-OPE-05 | Deve haver backup do banco e procedimento de reinício dos processos. Como o banco passa a ser a fonte oficial (RN-07), o backup é Essencial. | Essencial | A§1, A§4, D2 |
| RNF-OPE-06 | Entregas de webhook com falha devem poder ser conferidas e reenviadas manualmente (o GitHub não reenvia sozinho). | Importante | A§4 |
| RNF-OPE-07 | O histórico de etapas e tentativas no banco deve permitir diagnosticar uma tarefa sem acesso aos logs do servidor. | Importante | A§4 |

## 6. Pontos em aberto

Itens que a arquitetura (seção 10.3) mantém em aberto. Os números D1–D20 são estáveis: quando um item é decidido, ele sai desta tabela e passa para a seção 10.1 da arquitetura com o mesmo número.

| # | Ponto | Situação e proposta | Requisitos afetados |
|---|---|---|---|
| D5 | **Identificador estável e exportação.** | Formato do identificador da regra: `RN-<modulo>-<nnn>` (legível, mas preso ao nome do módulo) ou código curto (ex.: `r-7f3a`). Com D2, os arquivos no repositório passam a ser só uma exportação desejável: falta definir formato, caminhos e como publicar (PR próprio após o merge?). | RF-DOC-01–03 |
| D13 | **Plano de hospedagem.** *(Adiado: Marley vai pesquisar.)* | Worker da Render não tem instância gratuita; serviço web gratuito hiberna (risco ao RNF-DES-01); provedor do banco indefinido. Não afeta o replay, que roda no terminal. Com D2, o banco é a fonte oficial, o que pesa na escolha do provedor (backup, expiração do plano gratuito). | RNF-OPE-01, RNF-OPE-05, RNF-DES-01 |
| D14 | **Cotas do Gemini.** *(Adiado.)* | Verificado por Marley: o nível gratuito permite **250 requisições por dia**. A base inicial faz hoje uma chamada por unidade (RF-IA-06) e é o maior consumo. Falta decidir como a ferramenta respeita esse limite e definir o protocolo do piloto. | RNF-DES-04, RF-IA-06, RF-AV-* |
| D17 | **Limite de tamanho do contexto.** *(Adiado.)* | Com um nível fixo (D7), uma função muito chamada pode trazer dezenas de vizinhas. *Proposta:* limite de tokens por chamada, configurável; acima dele, manter as vizinhas que já têm regras vinculadas e cortar as demais, registrando o corte como limitação da análise. | RF-AN-11, RNF-DES-04 |
| D18 | **Conteúdo do `.lastro.yml`.** *(Adiado.)* | *Proposta:* versão do formato, branch de referência, padrões de arquivos de teste e de diretórios ignorados. A ferramenta lê o arquivo da branch de referência a cada análise. | RF-AN-14, RF-DOC-15 |

## 7. Fora do escopo

- Outras linguagens além de Python e outras plataformas além do GitHub.
- Edição automática do código analisado.
- Atualização de documentos escritos por humanos fora do catálogo do Lastro.
- Integração com agentes de IA (caminho C), tratada como trabalho futuro.
- Edição direta de regras vigentes pelo portal, fora da revisão de um PR (versão futura, D1).
- Microsserviços e broker de mensagens.

## 8. Rastreabilidade com os objetivos específicos

| Objetivo específico (Cap. 1) | Requisitos principais |
|---|---|
| 1. Gerar catálogo inicial e grafo a partir da AST | RF-AN-01–10, RF-AN-14, RF-IA-06, RF-DOC-01–05, RF-DOC-14–15 |
| 2. Detectar mudanças a cada PR e propor atualizações com IA | RF-AN-05–12, RF-IA-01–09, RF-DOC-06, RN-01–04 |
| 3. Revisão humana das propostas, incorporando só o aprovado e integrado | RF-GH-01–18, RF-DOC-07–18, RF-PR-01–11, RF-PO-12–17, RN-05–06, RN-11 |
| 4. Portal com catálogo, histórico por PR e grafo | RF-AC-01–07, RF-PO-01–11, RF-PO-18 |
| 5. Avaliar detecção, corretude e atualização com replay e linhas de base | RF-AV-01–14, RNF-RAS-01–04 |
