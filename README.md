# Códice

> **Documentação viva de regras de negócio para repositórios Python no GitHub.**

![Python 3.15](https://img.shields.io/badge/Python-3.15-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.162+-009688?logo=fastapi&logoColor=white)
![React 19](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript 7](https://img.shields.io/badge/TypeScript-7-3178C6?logo=typescript&logoColor=white)
![PostgreSQL 18](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)
![Licença MIT](https://img.shields.io/badge/Licen%C3%A7a-MIT-green)
![Status: Em desenvolvimento](https://img.shields.io/badge/Status-Em%20desenvolvimento-yellow)

O **Códice** é uma ferramenta desenvolvida como Trabalho de Conclusão de Curso (TCC) para combater a **documentação desatualizada (*documentation drift*)** e a perda de conhecimento técnico em equipes de desenvolvimento. A cada *pull request* (PR), a plataforma analisa o código Python alterado usando análise estática (`ast`), interpreta com Inteligência Artificial (**Gemini 3.6 Flash**) se alguma **regra de negócio** foi modificada e publica um comentário no próprio PR com o resumo da mudança proposta e o **link direto para revisão e aprovação no portal**.

> **Pergunta de pesquisa:**
> *Em que medida uma ferramenta que analisa cada pull request com análise estática de código e IA consegue manter a documentação de um sistema correta e atualizada?*

---

## Sumário

- [Como funciona](#como-funciona)
- [Arquitetura](#arquitetura)
- [Stack tecnológica](#stack-tecnológica)
- [Status do projeto e roadmap](#status-do-projeto-e-roadmap)
- [Metodologia de avaliação (TCC)](#metodologia-de-avaliação-tcc)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como executar localmente](#como-executar-localmente)
- [Documentação de referência](#documentação-de-referência)
- [Contexto acadêmico](#contexto-acadêmico)
- [Licença](#licença)

---

## Como funciona

### O que conta como mudança de regra de negócio

Para manter a classificação consistente tanto na ferramenta quanto no experimento de avaliação, o Códice adota uma definição operacional explícita:

- **Conta como mudança de regra de negócio:** alteração em condição, cálculo, validação, fluxo de estados, regra de autorização ou contrato de entrada/saída que modifique um comportamento de domínio.
- **Não conta, isoladamente:** renomeação de identificadores, formatação, refatoração sem mudança de comportamento, nem alterações restritas a testes, dependências ou configuração.

### Fluxo de ponta a ponta

1. **Geração da base inicial:** a partir de uma versão de referência de um repositório Python, o Códice percorre a AST dos módulos, extrai o grafo de dependências e gera propostas para o catálogo inicial de regras de negócio, revisadas no portal.
2. **Evento de PR (`opened`, `synchronize`, `reopened`):** o GitHub App envia um webhook para a API FastAPI, que valida a assinatura, deduplica pela entrega (`X-GitHub-Delivery`) e grava evento e tarefa (`analisar_pr`) na mesma transação no PostgreSQL.
3. **Análise estática + interpretação com IA:** o worker reserva a tarefa com `FOR UPDATE SKIP LOCKED`, lê as versões base e nova do código via API do GitHub (permissão somente leitura em `Contents`), identifica com `ast` as unidades alteradas e o contexto de dependências e consulta o **Gemini 3.6 Flash** para propor inclusões, alterações ou remoções no catálogo.
4. **Feedback no PR (resumo + link):** o worker salva a análise, os trechos de código e as propostas no PostgreSQL e publica (ou atualiza) um **comentário no PR** contendo o resumo das regras afetadas, referências ao código e o **link direto para a tela de revisão no portal**. O bot não faz commits automáticos na branch do PR — eliminando loops de eventos e problemas de permissão em *forks*.
5. **Revisão e aprovação no portal:** autenticado via OAuth do GitHub, o revisor abre o portal (pelo link no PR ou pela lista de pendências), compara o código anterior e novo com o texto sugerido e decide **aprovar**, **ajustar** ou **rejeitar** cada proposta. As propostas originais da IA ficam preservadas separadamente dos ajustes humanos para a avaliação do TCC.
6. **Incorporação condicionada ao merge:** quando o PR é integrado à branch de referência (`closed` com `merged: true`), a tarefa `pr_mergeado` incorpora as propostas aprovadas/ajustadas ao catálogo vigente no PostgreSQL e atualiza o grafo de módulos. Se um PR for mergeado antes da revisão, o portal sinaliza a pendência até a aprovação; se for fechado sem merge, o catálogo vigente permanece inalterado.
7. **Consulta e exportação:** a equipe consulta o catálogo pesquisável, o histórico de cada regra por PR (antes/depois + código vinculado) e o grafo de dependências no portal, podendo exportar o catálogo em **JSON** e **Markdown**.

### Exemplo ilustrativo

```python
# Código anterior
if valor_compra >= 100:
    desconto = 0.10

# Código alterado no PR
if valor_compra >= 150:
    desconto = 0.10
```

O analisador `ast` detecta a alteração na condição da função e envia o trecho alterado, o contexto relevante e a regra atual ao Gemini. O Códice comenta no PR o resumo da mudança sugerida (*"O desconto de 10% passa a ser concedido para compras a partir de R$ 150."*) com o link para aprovação no portal. Após aprovação e merge do PR, a nova versão da regra entra no catálogo vigente preservando o histórico anterior e o vínculo com o PR.

---

## Arquitetura

O Códice é um **monólito modular plano com processamento assíncrono**: dois processos Python permanentes (API FastAPI e Worker) no mesmo repositório, compartilhando os mesmos módulos de código e um único banco **PostgreSQL 18**, sem broker de mensageria externo.

```mermaid
flowchart LR
    PORTAL["Portal React (Consulta e Revisão)"]
    GH["GitHub (App + Webhooks)"]
    IA["Gemini 3.6 Flash API"]
    subgraph APP["Códice — Monólito Modular Python"]
        API["Processo 1: API FastAPI"]
        WORKER["Processo 2: Worker + Analisador AST"]
    end
    DB[("PostgreSQL 18\nEventos · Fila tarefas · Análises · Propostas · Catálogo")]

    PORTAL <-->|HTTP / JSON (Consulta e Aprovação)| API
    GH -->|Webhook PR / Merge| API
    API -->|Transação única: evento + tarefa| DB
    DB -->|FOR UPDATE SKIP LOCKED| WORKER
    WORKER <-->|Contexto mínimo + Propostas| IA
    WORKER -->|Comentário no PR: resumo + link p/ portal| GH
    WORKER -->|Propostas e incorporação pós-merge| DB
    DB -->|Catálogo, propostas, histórico e grafo| API
```

### Decisões arquiteturais principais

- **Backend Python pragmático (monólito modular plano):** em vez de camadas rígidas repetidas por módulo, o pacote `backend/src/codice/` é organizado em pastas diretas por responsabilidade (`analise`, `ia`, `github`, `catalogo`, `processamento`, `avaliacao`, `db`, `api`), usando SQLAlchemy 2 e Pydantic diretamente onde fazem sentido.
- **Núcleo estático `analise/` 100% puro (sem I/O):** garantido estaticamente pelo Ruff (`TID251` em `backend/pyproject.toml`). Recebe código-fonte como texto e devolve estruturas Python puras, permitindo o mesmo motor no worker, na CLI local e no replay histórico sem mocks de banco ou rede.
- **Fila transacional no PostgreSQL:** a tabela `tarefas` usa `FOR UPDATE SKIP LOCKED` para reserva atômica, `reserva_ate` / `reserva_token` para recuperação após quedas, e unicidade em `eventos.delivery_id` para deduplicar entregas repetidas do GitHub na mesma transação.
- **Catálogo oficial no PostgreSQL (11 entidades + 3 tabelas associativas):** organizado em *Acesso* (`usuarios`, `usuario_repositorio`), *Código e Catálogo* (`repositorios`, `modulos`, `modulo_dependencia`, `regras`, `versoes_regra`) e *Operação e Revisão* (`pull_requests`, `eventos`, `tarefas`, `analises`, `trechos_codigo`, `propostas`, `proposta_trecho`), mantendo as propostas originais da IA separadas das revisões humanas.
- **Permissões mínimas no GitHub App:** apenas `Contents: read` e `Pull requests: write`, sem precisar escrever em branches do repositório analisado.
- **Frontend com separação estrita visual/lógica (*"componente desenha, hook pensa"*):** aplicada automaticamente pelo Biome e TypeScript estrito, com `fetch` centralizado em `src/compartilhado/api/cliente.ts` e chamadas sempre via `/api/...`.

---

## Stack tecnológica

| Camada | Tecnologia | Papel |
|---|---|---|
| **Linguagem (Backend)** | Python 3.15 (`uv`) | API, worker, CLI e analisador estático com versão fixada para reprodutibilidade |
| **API HTTP (Processo 1)** | FastAPI + Uvicorn | Webhooks do GitHub, OAuth, consultas do portal e endpoints de revisão/aprovação |
| **Worker (Processo 2)** | Python (`codice-worker`) | Consumo da fila no PostgreSQL, análise, chamadas ao Gemini, comentários no PR e pós-merge |
| **Análise estática** | `ast` (stdlib Python) | Extração de módulos/funções/classes, diff estrutural, grafo de dependências e seleção de contexto |
| **IA (LLM)** | Gemini 3.6 Flash (`google-genai`) | Classificação de mudança de regra de negócio e geração de propostas estruturadas |
| **Banco e fila** | PostgreSQL 18 + SQLAlchemy 2 + Alembic | Catálogo oficial, histórico, revisão humana e fila transacional (`tarefas`) |
| **Integração GitHub** | GitHub App + REST API (`httpx`, `PyJWT`) | Webhooks, leitura de código (`Contents: read`), comentários em PR e login OAuth |
| **Portal (Frontend)** | React 19 + TypeScript 7 + Vite 8 (`pnpm`) | Catálogo pesquisável, tela de revisão de propostas, histórico por PR e grafo |
| **Grafo de módulos** | Cytoscape.js *(previsto na etapa do portal)* | Visualização interativa de dependências e módulos impactados |
| **Qualidade e testes** | Ruff, mypy strict, pytest + pytest-cov, Biome, `tsc` | Lint, formatação, pureza de `analise/`, tipagem estrita e cobertura de testes |
| **Hospedagem prevista** | Render + PostgreSQL gerenciado | Serviço web (API + build estático React) e background worker |

---

## Status do projeto e roadmap

O projeto está na fase inicial de implementação, com a arquitetura, o modelo de dados, o ambiente de desenvolvimento e a esteira de qualidade configurados.

### Concluído

- [x] Definição do escopo, pergunta de pesquisa e protocolo experimental do TCC ([docs/escopo-tcc.md](docs/escopo-tcc.md))
- [x] Definição da arquitetura, fluxos, fila transacional e modelo de dados ([docs/arquitetura-tcc.md](docs/arquitetura-tcc.md))
- [x] Ambiente de desenvolvimento completo: monólito modular em `backend/src/codice/`, Docker Compose (PostgreSQL 18 com bancos `codice` e `codice_testes`), Alembic, healthcheck `GET /saude`, CLI/worker iniciais, portal React inicial e esteira de qualidade (`make verificar`)

### Roadmap de implementação ([arquitetura, seção 9](docs/arquitetura-tcc.md#9-ordem-de-implementação))

| Etapa | Escopo | Status |
|---|---|---|
| **1. Analisador local** | Extração de AST, comparação entre versões, dependências estáticas e seleção de contexto via CLI (`codice analisar`) | Em aberto (próximo passo) |
| **2. Catálogo inicial e Gemini** | Geração da base inicial, integração com Gemini 3.6 Flash, propostas estruturadas e piloto de calibração | Planejado |
| **3. Persistência e fila** | Modelos ORM (`db/modelos/`), migrações Alembic, transação única de evento + tarefa e reserva/recuperação no worker | Planejado |
| **4. GitHub App e feedback no PR** | Webhooks (`opened`, `synchronize`, `reopened`, `closed`), leitura de código e publicação/atualização do comentário resumo + link no PR | Planejado |
| **5. Revisão e efetivação pós-merge** | Aceitar/ajustar/rejeitar propostas preservando a saída original da IA, incorporação pós-merge sem regressão e exportação JSON/Markdown | Planejado |
| **6. Portal React** | Login OAuth GitHub, tela de revisão de propostas por PR, catálogo pesquisável, histórico antes/depois e grafo com Cytoscape.js | Planejado |
| **7. Avaliação experimental** | Replay histórico de PRs open-source, linhas de base e consolidação das métricas do TCC | Planejado |

---

## Metodologia de avaliação (TCC)

Para responder à pergunta de pesquisa de forma quantitativa e reproduzível, o experimento principal realiza **replay histórico de PRs reais** em **2 a 3 repositórios Python open-source** (meta de **50 a 100 PRs por repositório**), reprocessando os PRs na ordem em que foram mesclados e comparando os resultados contra um gabarito manual (com medição de concordância pelo coeficiente **kappa de Cohen**, sempre que houver segundo avaliador).

| Dimensão | O que mede | Métricas |
|---|---|---|
| **Detecção** | Capacidade de perceber quando uma regra de negócio mudou | Precisão, *recall* e F1 por PR |
| **Corretude** | Qualidade semântica das atualizações propostas (antes de qualquer edição humana) | % correta, parcialmente correta e incorreta |
| **Atualização (*drift*)** | Se a documentação continua refletindo o código ao longo da sequência de PRs | % de regras desatualizadas e regras esperadas ausentes |
| **Custo** | Viabilidade operacional de rodar a cada PR | Tempo de processamento e consumo de tokens por PR |

**Linhas de base para comparação:**
1. **Catálogo inicial sem manutenção:** base inicial congelada para medir o acúmulo de *drift* ao longo dos PRs.
2. **Apenas IA sobre o diff bruto (sem análise estática):** isola a contribuição da extração de AST, dependências e seleção de contexto.

Complementarmente, prevê-se um estudo de caso qualitativo com uma equipe de desenvolvimento, condicionado à disponibilidade de projeto Python com volume adequado de PRs.

---

## Estrutura do repositório

```text
.
├── backend/
│   ├── src/codice/
│   │   ├── analise/           # Núcleo AST puro (sem I/O): extração, diff, dependências e contexto
│   │   ├── ia/                # Prompts, cliente Gemini (google-genai) e validação estruturada
│   │   ├── github/            # Webhooks, OAuth/App, leitura de código e comentários em PRs
│   │   ├── catalogo/          # Catálogo vigente, revisão de propostas, histórico, grafo e export JSON/MD
│   │   ├── processamento/     # Fila transacional (tarefas) e orquestração do pipeline do worker
│   │   ├── avaliacao/         # Replay histórico de PRs, linhas de base e métricas do TCC
│   │   ├── db/                # Base SQLAlchemy, sessão e modelos ORM (modelos/)
│   │   ├── api/               # Aplicação FastAPI e rotas HTTP (app.py)
│   │   ├── worker.py          # Entrada do processo worker (`codice-worker`)
│   │   ├── cli.py             # Entrada do terminal (`codice`)
│   │   └── config.py          # Configurações via pydantic-settings (.env da raiz)
│   ├── migrations/            # Migrações Alembic compartilhadas por API e worker
│   ├── tests/
│   │   ├── unit/              # Testes rápidos sem banco ou rede
│   │   └── integration/       # Testes com PostgreSQL real (marcador `integration`)
│   ├── .python-version        # Python 3.15
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── app/               # Composição da aplicação (App.tsx)
│   │   └── main.tsx           # Ponto de entrada React
│   ├── CLAUDE.md              # Convenções e regras do frontend
│   ├── biome.json             # Lint e formatação estritos (Biome)
│   ├── package.json           # Portal (`codice-portal`)
│   ├── tsconfig.app.json      # TypeScript estrito
│   └── vite.config.ts         # Proxy /api → http://localhost:8000
├── docker/
│   └── postgres-init.sql      # Criação automática do banco `codice_testes`
├── docs/                      # Escopo, arquitetura e capítulos do TCC
├── .env.example               # Modelo de variáveis de ambiente
├── CLAUDE.md                  # Guia técnico e convenções do repositório
├── LICENSE                    # Licença MIT
├── Makefile                   # Atalhos de setup, execução, qualidade e migrações
└── docker-compose.yml         # PostgreSQL 18 local (`codice` e `codice_testes`)
```

---

## Como executar localmente

### Pré-requisitos

- **Python 3.15** e **[uv](https://docs.astral.sh/uv/)**
- **Node.js** e **[pnpm](https://pnpm.io/)**
- **Docker** e **Docker Compose** (para o PostgreSQL 18 local)
- **Make** *(opcional no Windows: se não tiver `make` instalado via Git Bash/WSL/Chocolatey, execute diretamente os comandos equivalentes indicados no [Makefile](Makefile))*

### 1. Clonar e configurar variáveis de ambiente

```bash
git clone https://github.com/marleypm16/tcc.git
cd tcc
cp .env.example .env
```

> No PowerShell (Windows), use `Copy-Item .env.example .env`.

| Variável | Padrão no `.env.example` | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://codice:codice@localhost:5432/codice` | URL do banco PostgreSQL de desenvolvimento |
| `DATABASE_URL_TESTES` | `postgresql+psycopg://codice:codice@localhost:5432/codice_testes` | URL do banco PostgreSQL de testes de integração |
| `PORTAL_URL` | `http://localhost:5173` | URL base do portal usada para gerar links de revisão nos comentários do PR |
| `GITHUB_APP_ID` | *(vazio)* | ID do GitHub App *(necessário a partir da etapa 4)* |
| `GITHUB_PRIVATE_KEY_PATH` | *(vazio)* | Caminho para a chave privada `.pem` do GitHub App *(etapa 4)* |
| `GITHUB_WEBHOOK_SECRET` | *(vazio)* | Segredo para validar a assinatura dos webhooks do GitHub *(etapa 4)* |
| `GITHUB_CLIENT_ID` | *(vazio)* | Client ID OAuth do GitHub App para login no portal *(etapa 6)* |
| `GITHUB_CLIENT_SECRET` | *(vazio)* | Client Secret OAuth do GitHub App *(etapa 6)* |
| `GEMINI_API_KEY` | *(vazio)* | Chave da Gemini API *(necessária a partir da etapa 2)* |
| `GEMINI_MODELO` | `gemini-3.6-flash` | Identificador do modelo Gemini usado na interpretação |
| `WORKER_INTERVALO_CONSULTA_S` | `5` | Intervalo (em segundos) de consulta da fila pelo worker |

### 2. Instalar dependências e subir o banco

```bash
make instalar   # cd backend && uv sync  |  cd frontend && pnpm install
make db         # docker compose up -d --wait db
make migrar     # cd backend && uv run alembic upgrade head
```

### 3. Executar os processos

Abra terminais separados conforme necessário:

```bash
make api        # API FastAPI com reload em http://localhost:8000 (healthcheck: GET /saude)
make worker     # Worker Python (`uv run codice-worker`)
make portal     # Portal React (Vite) em http://localhost:5173 (proxy /api → :8000)
```

Para testar a CLI do analisador local (em construção na etapa 1):

```bash
cd backend
uv run codice --help
uv run codice analisar arquivo_base.py arquivo_novo.py
```

### Comandos do `Makefile`

| Comando | O que faz |
|---|---|
| `make ajuda` | Lista todos os comandos disponíveis |
| `make instalar` | Instala dependências do backend (`uv sync`) e do frontend (`pnpm install`) |
| `make db` | Sobe o PostgreSQL 18 no Docker (cria `codice` e `codice_testes`) |
| `make db-parar` | Para o container do PostgreSQL |
| `make api` | Inicia a API FastAPI em `http://localhost:8000` com hot reload |
| `make worker` | Inicia o processo worker (`codice-worker`) |
| `make portal` | Inicia o portal React (Vite) em `http://localhost:5173` |
| `make formatar` | Formata e aplica correções automáticas (Ruff + Biome) |
| `make lint` | Verifica formatação, lint e pureza de `analise/` sem alterar arquivos |
| `make tipos` | Checagem de tipos (`mypy` strict + `tsc -b`) |
| `make testes` | Executa todos os testes com cobertura (requer `make db`) |
| `make testes-unit` | Executa apenas testes unitários (sem necessidade de banco) |
| `make testes-integracao` | Executa apenas testes marcados com `integration` (requer `make db`) |
| `make verificar` | Roda `lint`, `tipos` e `testes` — deve passar antes de commits/PRs |
| `make migracao m="descricao"` | Gera nova migração Alembic via `--autogenerate` |
| `make migrar` | Aplica as migrações pendentes (`alembic upgrade head`) |

---

## Documentação de referência

| Documento | Conteúdo |
|---|---|
| [docs/escopo-tcc.md](docs/escopo-tcc.md) | Escopo, propósito, pergunta de pesquisa, definição operacional e desenho da avaliação |
| [docs/arquitetura-tcc.md](docs/arquitetura-tcc.md) | Especificação técnica atualizada: arquitetura, fluxos, fila no PostgreSQL, modelo de dados e roadmap |
| [CLAUDE.md](CLAUDE.md) | Convenções do projeto, estrutura modular do backend e fluxo de desenvolvimento |
| [frontend/CLAUDE.md](frontend/CLAUDE.md) | Regras de engenharia do portal React (*"componente desenha, hook pensa"*, Biome e TypeScript estrito) |
| [docs/resumo-revisado.md](docs/resumo-revisado.md) | Resumo acadêmico revisado do TCC |
| [docs/capitulo-1-revisado.md](docs/capitulo-1-revisado.md) | Capítulo 1 — Introdução, justificativa, objetivo geral e objetivos específicos |
| [docs/capitulo-3-revisado.md](docs/capitulo-3-revisado.md) | Capítulo 3 — Procedimentos metodológicos e protocolo experimental |
| [docs/capitulo-4-revisado.md](docs/capitulo-4-revisado.md) | Capítulo 4 — Desenvolvimento da ferramenta *(texto em evolução; sincronização pendente com a revisão no portal)* |
| [docs/Mapa da arquitetura do TCC.md](docs/Mapa%20da%20arquitetura%20do%20TCC.md) | Histórico de decisões arquiteturais anteriores *(referência histórica)* |

---

## Contexto acadêmico

Este repositório reúne a implementação e os artefatos técnicos do Relatório Técnico de Conclusão de Curso:

- **Título:** *Gestão do Conhecimento em Sistemas de Software: Uma Ferramenta Baseada em Análise Estática de Código*
- **Plataforma:** Códice
- **Autor:** Marley Pinheiro Martins
- **Orientadora:** Katarina Leal Chaves Lacerda (DADM/UFRPE)
- **Curso:** Bacharelado em Sistemas de Informação (BSI)
- **Instituição:** Universidade Federal Rural de Pernambuco (UFRPE) — Recife, 2026

---

## Licença

Este projeto está licenciado sob a **Licença MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
