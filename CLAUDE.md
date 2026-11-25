# Códice

Aplicação do TCC de Marley Pinheiro Martins: **documentação viva de regras de negócio para repositórios Python no GitHub**.

## O que é e para que serve

A cada pull request, o Códice analisa o código alterado com análise estática (`ast`), usa IA (Gemini) para decidir se alguma **regra de negócio** mudou e gera propostas de atualização da documentação. O worker publica um **comentário no próprio PR** com o resumo das alterações sugeridas e o **link direto para o portal**. No portal React (autenticado via GitHub), o revisor aceita, ajusta ou rejeita cada proposta; quando o PR é **mergeado**, as propostas aprovadas passam a compor o catálogo oficial no PostgreSQL (exportável em JSON e Markdown), preservando as propostas originais da IA separadas das edições humanas para a avaliação do TCC. O portal também permite consultar o catálogo vigente, o histórico de evolução por PR e o grafo de dependências entre módulos.

O objetivo é reduzir a distância entre o comportamento do código e o conhecimento documentado sobre ele, mantendo esse conhecimento correto, atualizado e rastreável. A pergunta de pesquisa é: *em que medida uma ferramenta que analisa cada PR com análise estática e IA consegue manter a documentação correta e atualizada?* A avaliação usa replay histórico de PRs.

Fontes de verdade (leia antes de decisões de arquitetura):
- `docs/escopo-tcc.md`: escopo e propósito.
- `docs/arquitetura-tcc.md`: arquitetura, fluxos, fila, **modelo de dados (seção 7)**, ordem de implementação (seção 9) e pontos em aberto (seção 10.3).
- `docs/capitulo-*-revisado.md`: texto do TCC. Não altere esses arquivos sem aprovação explícita.

## Stack

| Parte | Tecnologia |
|---|---|
| Linguagem do servidor | Python 3.15 (fixado em `backend/.python-version`), gerenciado com **uv** |
| API (processo 1) | FastAPI + Uvicorn |
| Worker (processo 2) | Python, consulta a fila no PostgreSQL |
| Análise estática | `ast` da biblioteca padrão |
| IA | Gemini 3.6 Flash (`gemini-3.6-flash`) via SDK `google-genai` |
| Banco | PostgreSQL 18 + SQLAlchemy 2 + Alembic. Catálogo oficial + fila na tabela `tarefas` (`FOR UPDATE SKIP LOCKED`), sem broker |
| GitHub | GitHub App: webhooks, leitura de código, comentários no PR e login OAuth do portal |
| Portal | React 19 + TypeScript 7 + Vite 8, **pnpm**; grafo com Cytoscape.js |
| Qualidade | Ruff (lint + formatação), mypy strict, pytest + pytest-cov; Biome + tsc no frontend |
| Hospedagem | Render (API e worker); PostgreSQL em oferta gratuita a definir |

Não troque nenhuma dessas escolhas (por exemplo, colocar RabbitMQ/Celery, outro LLM ou outro ORM) sem perguntar.

## Estrutura do repositório

```
backend/
  src/codice/
    analise/             # núcleo ast puro (sem I/O): extração, diff, dependências e contexto
    ia/                  # prompt, cliente Gemini e validação estruturada das propostas
    github/              # webhooks, auth do app/OAuth, leitura de código e comentários no PR
    catalogo/            # catálogo vigente, revisão/aprovação de propostas, histórico, grafo e export JSON/MD
    processamento/       # fila de tarefas, tentativas, recuperação e orquestração do pipeline
    avaliacao/           # replay histórico, linhas de base e métricas do TCC
    db/                  # Base SQLAlchemy, sessão e modelos ORM de todas as tabelas
    api/                 # FastAPI: app e rotas (saúde, webhooks, auth, catálogo e revisão)
    worker.py            # ponto de entrada do processo worker (`codice-worker`)
    cli.py               # ponto de entrada do terminal (`codice`)
    config.py            # pydantic-settings, lê o .env da raiz
  migrations/            # Alembic (uma sequência única, compartilhada por API e worker)
  tests/unit/            # rápidos, sem banco/rede
  tests/integration/     # PostgreSQL real (marcador `integration`)
frontend/                # portal React (consulta e revisão de propostas)
docs/                    # documentos do TCC
docker-compose.yml       # PostgreSQL local (bancos `codice` e `codice_testes`)
```

## Regras da arquitetura (monólito modular plano em Python)

1. **`analise/` é Python puro (sem I/O):** recebe texto de código e devolve estruturas (`dataclasses` / stdlib). Não importa FastAPI, SQLAlchemy, pydantic, httpx, SDK do Gemini, `codice.db` nem `codice.config`. O Ruff garante isso (`TID251` em `pyproject.toml`). Assim o worker, a CLI e o replay reutilizam exatamente o mesmo núcleo.
2. **Sem cerimônia excessiva nos demais módulos:** `catalogo/`, `processamento/`, `api/`, `ia/`, `github/` e `avaliacao/` são módulos planos em Python que usam modelos SQLAlchemy 2 (`codice.db.modelos`) e schemas Pydantic diretamente onde fizer sentido, sem duplicar cada tabela em dataclasses nem criar interfaces `Protocol` para tudo.
3. **Dependências externas injetáveis:** chamadas ao Gemini (`ia/`) e ao GitHub (`github/`) ficam encapsuladas em seus módulos e são passadas por parâmetro ao pipeline, facilitando testes unitários e a execução do replay histórico (sem publicação no GitHub).
4. **Modelos ORM centralizados** em `codice/db/modelos/` (`acesso.py`, `codigo_catalogo.py`, `operacao.py`), compartilhados por API e worker com uma única sequência de migrações Alembic.
5. **API e worker não se chamam diretamente:** comunicam-se pelo PostgreSQL (tabela `tarefas`). Evento e tarefa são gravados na mesma transação.

## Convenções

- **Português** para identificadores de domínio, nomes de tabelas/colunas, mensagens e docstrings (`Tarefa`, `reservar_tarefa`, `versoes_regra`). Termos técnicos consagrados podem ficar em inglês (`api`, `worker`, `cli`, `db`).
- Nomes de tabelas, colunas e estados seguem exatamente `docs/arquitetura-tcc.md` seção 7 (ex.: status de tarefa `pendente | processando | concluida | erro | descartada`; status de proposta `pendente | aprovada | ajustada | rejeitada | obsoleta`).
- Imports absolutos (`from codice.analise ...`); imports relativos são proibidos pelo Ruff.
- Datas sempre com fuso (`datetime.now(UTC)`); o banco usa `timestamptz`.
- Segredos só via `.env` / variáveis de ambiente; nunca no código ou em commits.
- Toda regra nova vem com teste unitário; código que consulta ou altera o banco vem com teste de integração (`@pytest.mark.integration`).
- Frontend: siga `frontend/CLAUDE.md`. Resumo: componentes só visuais e lógica em hooks (o Biome bloqueia), TypeScript estrito sem `any`/`!`, `fetch` só em `src/compartilhado/api/cliente.ts`, chamadas sempre por `/api/...`.

## Comandos

Tudo pela raiz com `make` (`make ajuda` lista os alvos):

```bash
make instalar          # uv sync + pnpm install
make db                # sobe o PostgreSQL no Docker (dev e testes)
make migrar            # alembic upgrade head
make api               # FastAPI em :8000 com reload
make worker            # worker
make portal            # Vite em :5173 (proxy /api → :8000)
make formatar          # ruff format + ruff --fix + biome --write
make verificar         # lint + tipos + testes (rodar antes de commit)
make testes-unit       # pytest sem banco, com cobertura
make migracao m="..."  # alembic revision --autogenerate
```

Dentro de `backend/`, rode qualquer ferramenta Python com `uv run` (`uv run pytest tests/unit/x.py -k nome`). Para adicionar dependência: `uv add pacote` (ou `uv add --dev`); no frontend, `pnpm add`. Não edite `uv.lock` nem `pnpm-lock.yaml` à mão.

## Fluxo de trabalho

- Antes de considerar uma tarefa pronta, rode `make verificar` (ou a skill `/verificar`) e corrija o que falhar.
- Novas funcionalidades no backend: skill `/nova-funcionalidade`. Mudanças no esquema: skill `/nova-migracao`.
- Se uma implementação divergir do que está em `docs/arquitetura-tcc.md`, **pare e pergunte** antes de seguir. Use `/sincronizar-docs` para listar as divergências.
- Siga a ordem de implementação da seção 9 da arquitetura (o primeiro incremento é o analisador local).
- Commits e PRs só quando o usuário pedir. Trabalhe em branch, nunca direto na `master`.
