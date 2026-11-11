# Lastro

Aplicação do TCC de Marley: **documentação viva de regras de negócio para repositórios Python no GitHub**.

## O que é e para que serve

A cada pull request, o Lastro analisa o código alterado com análise estática (`ast`), usa IA (Gemini) para decidir se alguma **regra de negócio** mudou e grava as propostas de atualização da documentação no banco. O bot comenta no PR um resumo com link para o portal e publica o status `lastro/documentacao`; **ele não faz commit na branch do PR**. No portal React, quem tem permissão de escrita no repositório aprova, edita ou rejeita cada proposta. **Aprovação mais merge é a aceitação**: depois do merge, o worker incorpora as propostas aprovadas ao catálogo. O **banco é a fonte oficial** da documentação, e o portal também permite consultar o catálogo de regras, o histórico por PR e o grafo de módulos. A base inicial é gerada quando a GitHub App é instalada e chega ao repositório por um PR de ativação, que adiciona o `.lastro.yml`.

O objetivo é reduzir a distância entre o comportamento do código e o conhecimento documentado sobre ele, mantendo esse conhecimento correto, atualizado e rastreável. A pergunta de pesquisa é: *em que medida uma ferramenta que analisa cada PR com análise estática e IA consegue manter a documentação correta e atualizada?* A avaliação usa replay histórico de PRs.

Fontes de verdade (leia antes de decisões de arquitetura):
- `docs/escopo-tcc.md`: escopo e propósito.
- `docs/arquitetura-tcc.md`: arquitetura, fluxos, fila, **modelo de dados (seção 7)**, ordem de implementação (seção 9) e pontos em aberto (seção 10.3).
- `docs/requisitos.md`: requisitos com identificadores (RF/RNF/RN) e pontos em aberto (seção 6). As decisões D1–D20 já tomadas estão em `docs/arquitetura-tcc.md` §10.1.
- `docs/capitulo-*-revisado.md`: texto do TCC. Não altere esses arquivos sem aprovação explícita.

## Stack

| Parte | Tecnologia |
|---|---|
| Linguagem do servidor | Python 3.15 (fixado em `backend/.python-version`), gerenciado com **uv** |
| API (processo 1) | FastAPI + Uvicorn |
| Worker (processo 2) | Python, consulta a fila no PostgreSQL |
| Análise estática | `ast` da biblioteca padrão |
| IA | Gemini 3.6 Flash (`gemini-3.6-flash`) via SDK `google-genai` |
| Banco | PostgreSQL 18 + SQLAlchemy 2 + Alembic. A fila é a tabela `tarefas` (`FOR UPDATE SKIP LOCKED`), sem broker |
| GitHub | GitHub App: webhooks, token de instalação, login OAuth do portal |
| Portal | React + TypeScript + Vite, **pnpm**; grafo com Cytoscape.js |
| Qualidade | Ruff (lint + formatação), mypy strict, pytest + pytest-cov; Biome + tsc no frontend |
| Hospedagem | Render (API e worker); PostgreSQL em oferta gratuita a definir |

Não troque nenhuma dessas escolhas (por exemplo, colocar RabbitMQ/Celery, outro LLM ou outro ORM) sem perguntar.

## Estrutura do repositório

```
backend/
  src/lastro/
    <modulo>/            # um bounded context por pasta
      domain/            # entidades, objetos de valor, regras puras
      application/       # casos de uso + portas (Protocol)
      adapters/          # implementações das portas (SQLAlchemy, GitHub, Gemini)
    analise/             # núcleo ast: só domain/ e application/ (puro, sem I/O)
    interpretacao/       # IA: prompt, adaptador Gemini, validação da resposta
    documentacao/        # propostas, decisões de revisão, base inicial, incorporação pós-merge
    processamento/       # fila de tarefas, etapas, tentativas; orquestra o pipeline
    integracao_github/   # webhooks, autenticação do app, PR de ativação, comentários e status
    catalogo/            # consultas do portal (regras, histórico, grafo, propostas)
    acesso/              # login GitHub e repositórios acessíveis por usuário
    avaliacao/           # replay histórico, linhas de base, métricas
    shared/domain/       # kernel comum puro (tipos/erros usados por vários módulos)
    persistencia/        # Base SQLAlchemy, sessão e modelos ORM de TODAS as tabelas
    entrypoints/         # composition root: api/, worker/, cli/
    config.py            # pydantic-settings, lê o .env da raiz
  migrations/            # Alembic (uma sequência única, compartilhada por API e worker)
  tests/unit/            # sem I/O, portas trocadas por fakes
  tests/integration/     # PostgreSQL real (marcador `integration`)
frontend/                # portal React (consulta e revisão das propostas)
docs/                    # documentos do TCC
docker-compose.yml       # PostgreSQL local (bancos `lastro` e `lastro_testes`)
```

## Regras da arquitetura (Clean + Hexagonal)

1. **Direção das dependências:** `entrypoints → adapters → application → domain`. Nunca ao contrário.
2. **`domain/` e `application/` são Python puro**: stdlib e `dataclasses`. Não importam FastAPI, SQLAlchemy, pydantic, httpx, SDK do Gemini, `lastro.persistencia` nem `lastro.config`. O Ruff bloqueia isso (`TID251`, ver `banned-api` no `pyproject.toml`). Não silencie essa regra com `# noqa`; mova o código para a camada certa.
3. **Portas** são `typing.Protocol` em `application/portas.py`, nomeadas pelo papel no domínio (`InterpretadorMudancas`, `RepositorioTarefas`, `PublicadorPR`), não pela tecnologia.
4. **Casos de uso** ficam em `application/casos_de_uso/<nome>.py`, um por arquivo, como classe com dependências (portas) no `__init__` e um método `executar(...)`. Entradas e saídas são dataclasses, nunca modelos ORM ou pydantic.
5. **Entre módulos:** um módulo pode usar `domain/` e `application/` de outro, mas **nunca** os `adapters/` de outro. Quem conecta tudo é `entrypoints/`.
6. **Modelos ORM** ficam em `persistencia/modelos/` (o esquema é um só, conforme a seção 7 da arquitetura). Os adapters de repositório de cada módulo convertem ORM ↔ entidade de domínio. Entidades de domínio não são modelos ORM.
7. **`analise/` não tem I/O:** recebe texto de código e devolve estruturas. Assim o worker, o terminal e o replay usam o mesmo núcleo.
8. API e worker **não se chamam**: se comunicam pelo PostgreSQL (tabela `tarefas`). Evento e tarefa são gravados na mesma transação.

## Convenções

- **Português** para identificadores de domínio, nomes de tabelas/colunas, mensagens e docstrings (`Tarefa`, `reservar_tarefa`, `versoes_regra`). Termos técnicos consagrados podem ficar em inglês (`domain`, `adapters`, `Protocol`, `Repository`).
- Nomes de tabelas, colunas e estados seguem exatamente `docs/arquitetura-tcc.md` seção 7 (ex.: status `pendente | processando | concluida | erro | descartada`).
- Imports absolutos (`from lastro.analise.domain ...`); imports relativos são proibidos pelo Ruff.
- Datas sempre com fuso (`datetime.now(UTC)`); o banco usa `timestamptz`.
- Segredos só via `.env` / variáveis de ambiente; nunca no código ou em commits.
- Toda regra de domínio e caso de uso novo vem com teste unitário usando fakes das portas. Adapters de banco têm teste de integração.
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
- Novos casos de uso: skill `/novo-caso-de-uso`. Mudanças no esquema: skill `/nova-migracao`.
- Se uma implementação divergir do que está em `docs/arquitetura-tcc.md`, **pare e pergunte** antes de seguir. Use `/sincronizar-docs` para listar as divergências.
- Siga a ordem de implementação da seção 9 da arquitetura (o primeiro incremento é o analisador local).
- Commits e PRs só quando o usuário pedir. Trabalhe em branch, nunca direto na `master`.
