---
name: nova-migracao
description: Cria ou altera modelos ORM do Lastro e gera a migração Alembic correspondente, conferindo o resultado com o modelo de dados de docs/arquitetura-tcc.md (seção 7). Use quando o usuário pedir uma tabela nova, uma coluna, um índice, uma constraint, "cria a migração de X" ou "muda o esquema".
---

# /nova-migracao

Argumento: descrição da mudança (ex.: `/nova-migracao criar tabelas eventos e tarefas`).

## Passos

1. **Conferir a especificação.** Leia `docs/arquitetura-tcc.md`, seção 7 (entidades, campos, restrições, cardinalidades) e, para `tarefas`, a seção 4. Se a mudança pedida não estiver no documento ou o contradisser, **pare e pergunte** antes de seguir. Anote o que o documento deixa em aberto (seção 10.3: tipos, índices) e proponha uma escolha.
2. **Modelos ORM** em `backend/src/lastro/persistencia/modelos/<grupo>.py`, nos grupos da seção 7: `acesso.py`, `codigo_catalogo.py`, `operacao.py`.
   - SQLAlchemy 2: `Mapped[...]` + `mapped_column(...)`, herdando de `lastro.persistencia.base.Base`.
   - `__tablename__` e colunas com os nomes exatos do documento (português, snake_case).
   - Datas `DateTime(timezone=True)`; `server_default=func.now()` onde o doc usa `DEFAULT now()`.
   - Estados (`status`, `tipo`, `situacao`...) como `Text` + `CheckConstraint` com os valores do doc. Não use ENUM nativo do Postgres, que complica as migrações.
   - Unicidades compostas e índices parciais (ex.: `tarefas_pendentes_idx ... WHERE status = 'pendente'`) em `__table_args__`.
   - Chaves estrangeiras com o `ondelete` pensado. Na dúvida, sem cascade, e diga isso ao usuário.
   - Importe o novo modelo em `persistencia/modelos/__init__.py`.
3. **Gerar:** `make db` (se o banco não estiver de pé) e `make migracao m="<descrição curta>"`.
4. **Revisar o arquivo gerado** em `backend/migrations/versions/`. O autogenerate do Alembic **não detecta** bem:
   - índices parciais/funcionais e `CheckConstraint`s: confira se estão lá;
   - extensões (`gen_random_uuid()` é nativo no PG 13+, não precisa de `pgcrypto`);
   - renomeações (aparecem como drop + add, o que perde dados). Reescreva com `op.alter_column`/`op.rename_table`.
   - O `downgrade()` precisa desfazer exatamente o `upgrade()`.
5. **Testar ida e volta:** `cd backend && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head`.
6. Confirme que `uv run alembic check` não acusa diferenças entre modelos e banco.
7. `uv run ruff check . && uv run mypy`.

## Saída

Uma tabela **Documento × Implementado** com cada tabela/coluna/restrição alterada, marcando divergências. Indique também as decisões que você tomou nos pontos que o documento deixa em aberto, para o usuário validar e, se quiser, levar ao Cap. 4.
