---
name: nova-funcionalidade
description: Cria ou amplia uma funcionalidade no backend do Códice seguindo a arquitetura modular plana em Python (serviços/funções diretas, analise/ puro sem I/O, rotas FastAPI ou etapa de worker, e testes unitários/integração). Use quando o usuário pedir uma nova funcionalidade de backend, "implementa reservar tarefa", "cria endpoint de revisão", etc. Argumentos: <modulo> <nome> [descrição].
---

# /nova-funcionalidade

Argumentos esperados: `<modulo> <nome_em_snake_case> [descrição livre]`. Exemplo: `/nova-funcionalidade processamento reservar_tarefa reserva a próxima tarefa pendente`.

Se faltar o módulo ou o nome, ou se não estiver claro qual módulo é o dono do comportamento, **pergunte** antes de criar arquivos. Os módulos válidos em `backend/src/codice/` são: `analise`, `ia`, `github`, `catalogo`, `processamento`, `avaliacao`, `api` e `db`.

## Antes de escrever

1. Leia o `CLAUDE.md` e a parte de `docs/arquitetura-tcc.md` que descreve esse comportamento. Use os mesmos nomes de entidades, estados e campos do documento.
2. Leia o que já existe em `backend/src/codice/<modulo>/` para reaproveitar funções, tipos e modelos ORM existentes.
3. Apresente ao usuário um plano curto (arquivos, assinaturas principais e testes) e espere confirmação se algo não estiver definido na arquitetura.

## Diretrizes por tipo de módulo

1. **Núcleo estático (`backend/src/codice/analise/`):**
   - Python puro (`stdlib` + `dataclasses`). Sem imports de FastAPI, SQLAlchemy, Pydantic, `httpx`, `google-genai`, `codice.db` ou `codice.config` (o Ruff bloqueia via `TID251`).
   - Recebe código-fonte como texto/estruturas e devolve resultados tipados.
2. **Módulos de serviço (`catalogo/`, `processamento/`, `ia/`, `github/`, `avaliacao/`):**
   - Funções ou classes simples diretamente em `<modulo>/<nome>.py`.
   - Use modelos SQLAlchemy 2 (`codice.db.modelos`) e `Session` diretamente quando houver persistência; se precisar de tabela/coluna nova, use `/nova-migracao`.
   - Receba clientes externos (Gemini em `ia/`, GitHub em `github/`) por parâmetro para permitir fakes/mocks simples em testes unitários e desligar publicação no replay.
3. **API (`backend/src/codice/api/`):**
   - Rotas FastAPI e schemas Pydantic de entrada/saída em `api/rotas/<recurso>.py`, registrados em `api/app.py`.
4. **Testes:**
   - **Unitários** em `backend/tests/unit/<modulo>/test_<nome>.py` (Arrange-Act-Assert, nomes `test_<comportamento_esperado>`), cobrindo caminho feliz e casos de erro.
   - **Integração** em `backend/tests/integration/<modulo>/test_<nome>.py` marcados com `@pytest.mark.integration` sempre que houver consulta ou transação no PostgreSQL.

## Ao terminar

Rode `cd backend && uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest tests/unit` e corrija até passar. Liste os arquivos criados e qualquer decisão que não estava na arquitetura.
