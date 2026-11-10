---
name: novo-caso-de-uso
description: Cria um caso de uso no backend do Lastro seguindo a Clean/Hexagonal: entidades de domínio, porta (Protocol), caso de uso, adapter, teste unitário com fake e ligação no entrypoint. Use quando o usuário pedir uma nova funcionalidade de backend, "cria o caso de uso X", "implementa reservar tarefa", etc. Argumentos: <modulo> <nome_do_caso_de_uso> [descrição].
---

# /novo-caso-de-uso

Argumentos esperados: `<modulo> <nome_em_snake_case> [descrição livre]`. Exemplo: `/novo-caso-de-uso processamento reservar_tarefa reserva a próxima tarefa pendente`.

Se faltar o módulo ou o nome, ou se não estiver claro qual módulo é o dono do comportamento, **pergunte** antes de criar arquivos. Os módulos válidos são as pastas em `backend/src/lastro/` (exceto `shared`, `persistencia` e `entrypoints`).

## Antes de escrever

1. Leia o CLAUDE.md (regras da arquitetura) e a parte de `docs/arquitetura-tcc.md` que descreve esse comportamento. Use os mesmos nomes de entidades, estados e campos do documento.
2. Leia o que já existe em `<modulo>/domain/`, `<modulo>/application/portas.py` e `<modulo>/application/casos_de_uso/`, para reaproveitar entidades e portas em vez de duplicar.
3. Apresente ao usuário um plano curto (entidades, porta(s), assinatura de `executar`, adapter) e espere confirmação se algo não estiver definido na arquitetura.

## Arquivos (dentro de `backend/src/lastro/<modulo>/`)

1. **`domain/<conceito>.py`**: entidades e objetos de valor como `@dataclass(frozen=True, slots=True)` (ou não frozen se a entidade muda de estado por métodos). As regras de negócio ficam em métodos da entidade. Erros de domínio herdam de uma exceção do módulo em `domain/erros.py`. Sem imports de framework.
2. **`application/portas.py`**: acrescente a porta como `class NomeDoPapel(Protocol)` com métodos tipados que recebem e devolvem tipos de domínio.
3. **`application/casos_de_uso/<nome>.py`**:
   ```python
   @dataclass(frozen=True, slots=True)
   class EntradaNome: ...

   @dataclass(frozen=True, slots=True)
   class SaidaNome: ...

   class Nome:
       def __init__(self, porta_a: PortaA, porta_b: PortaB) -> None: ...
       def executar(self, entrada: EntradaNome) -> SaidaNome: ...
   ```
   O nome da classe é o caso de uso em PascalCase (`ReservarTarefa`). Lógica de orquestração aqui; regra de negócio no domínio.
4. **`adapters/<tecnologia>_<papel>.py`** (ex.: `sqlalchemy_repositorio_tarefas.py`, `gemini_interpretador.py`): implementa a porta. Converte modelos ORM/DTOs externos ↔ entidades. Se precisar de tabela nova, **não** crie o modelo aqui: use `/nova-migracao`.
   - O módulo `analise` não tem adapters.
5. **Teste unitário** em `backend/tests/unit/<modulo>/test_<nome>.py`: fake em memória da porta (classe simples no próprio teste ou em `tests/unit/<modulo>/fakes.py`), cobrindo caminho feliz e cada regra/erro. Padrão Arrange-Act-Assert, nomes `test_<comportamento_esperado>`.
6. **Teste de integração** em `backend/tests/integration/<modulo>/` se o adapter usar o banco, marcado com `@pytest.mark.integration`.
7. **Ligação**: instancie o caso de uso com o adapter no entrypoint que o usa (`entrypoints/api`, `worker` ou `cli`). Nunca dentro do próprio módulo.

## Ao terminar

Rode `cd backend && uv run ruff check . && uv run mypy && uv run pytest tests/unit/<modulo>` e corrija até passar. Liste os arquivos criados e qualquer decisão que não estava na arquitetura.
