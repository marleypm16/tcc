---
name: verificar
description: Roda todas as checagens de qualidade do Códice (formatação, lint com pureza de analise/, mypy strict, Biome, tsc e pytest com cobertura) e resume o que falhou. Use antes de commit/PR, ao terminar uma tarefa, ou quando o usuário disser "verifica", "roda os testes", "está tudo passando?".
---

# /verificar

Executa as checagens na ordem abaixo, a partir da raiz do repositório. **Não pare na primeira falha**: rode todas e só então resuma.

## Passos

1. Garanta que o banco de testes está de pé: `docker compose ps db`. Se não estiver, rode `make db`. Se o Docker não estiver disponível, rode só `make testes-unit` no passo 5 e avise que a integração foi pulada.
2. `cd backend && uv run ruff format --check .`
3. `cd backend && uv run ruff check .`. Erros `TID251` significam que `src/codice/analise/` importou framework ou I/O. Explique qual importação violou a pureza do núcleo estático e mova o I/O para o módulo adequado.
4. `cd backend && uv run mypy`
5. `cd backend && uv run pytest --cov --cov-report=term-missing`
6. `cd frontend && pnpm check` e `cd frontend && pnpm tipos`

Se o usuário passar `--fix` como argumento, rode antes `make formatar` e depois os passos acima.

## Saída

Uma tabela curta:

| Checagem | Resultado |
|---|---|
| ruff format | ok / N arquivos |
| ruff check | ok / N erros |
| mypy | ok / N erros |
| pytest | X passed, Y failed · cobertura Z% |
| biome | ok / N erros |
| tsc | ok / N erros |

Em seguida, liste cada falha com `arquivo:linha` e a causa em uma linha. Para testes que falharam, mostre a asserção. Não corrija nada sem o usuário pedir, exceto com `--fix`, que só aplica correções automáticas de formatação/lint.

Mostre a cobertura de `analise/` e dos módulos de regras de negócio que ficarem abaixo de 80%; rotas e scripts de entrada podem ter cobertura menor.
