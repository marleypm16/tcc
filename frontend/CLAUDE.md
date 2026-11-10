# Portal do Lastro (frontend)

Portal React **somente de consulta**: catálogo de regras, histórico por PR e grafo de módulos, com login pelo GitHub. Não há edição de documentação aqui; revisão e aprovação acontecem no GitHub (ver `docs/arquitetura-tcc.md`, seções 7 e 10.2).

Stack: React 19 + TypeScript 7 + Vite, **pnpm**, Biome (lint + formatação), tsc. Grafo com Cytoscape.js. Não adicione bibliotecas (roteador, cliente de dados, UI kit, CSS-in-JS) sem perguntar.

## Regra principal: componente desenha, hook pensa

Todo componente é **apenas visual**: recebe dados e callbacks prontos e devolve JSX. Toda lógica fica em hooks.

| Fica no **componente** (`componentes/*.tsx`)                             | Fica no **hook** (`hooks/use*.ts`)                                                      |
| ------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| JSX, classes CSS, textos                                                 | `useState`, `useEffect`, `useReducer`, `useRef`, `useMemo`, `useCallback`, `useContext` |
| Chamar **um** hook da própria funcionalidade e repassar o resultado      | Chamadas à API (via `api.ts`) e estados de carregamento/erro                            |
| Escolher entre estados já calculados (`if (estado.tipo === 'erro') ...`) | Filtros, ordenação, paginação, derivação de dados                                       |
| `useId` (acessibilidade)                                                 | Integração com Cytoscape, `localStorage`, URL, timers                                   |
| Composição de outros componentes                                         | Handlers com regra (`aoSelecionarRegra`, `aoMudarFiltro`)                               |

Isso é **verificado pelo Biome**: em `src/**/componentes/**` e `src/app/**`, importar hooks de estado/efeito do `react` ou importar `api` é erro. Não silencie com `// biome-ignore`; mova o código para um hook.

Padrão de uso:

```tsx
// hooks/useCatalogoRegras.ts
export function useCatalogoRegras(repositorioId: number): EstadoCatalogo { ... }

// componentes/CatalogoRegras.tsx
export function CatalogoRegras({ repositorioId }: CatalogoRegrasProps) {
  const catalogo = useCatalogoRegras(repositorioId)
  return <ListaRegras estado={catalogo} />
}
```

- Prefira **um hook por componente de tela** (`useCatalogoRegras` para `CatalogoRegras`), que compõe hooks menores se precisar.
- Componentes de apresentação puros (`ListaRegras`, `CartaoRegra`) não chamam hook nenhum: só props.
- Hooks devolvem um objeto com nome de domínio, nunca uma tupla longa. Arquivos de hook são `.ts` (sem JSX).
- Estados assíncronos usam união discriminada, nunca vários booleanos:

  ```ts
  type Carregavel<T> =
    | { tipo: 'carregando' }
    | { tipo: 'erro'; mensagem: string }
    | { tipo: 'pronto'; dados: T }
  ```

## Estrutura

```
src/
  main.tsx                       # monta a aplicação
  app/                           # App, rotas, provedores (só composição)
  funcionalidades/
    <nome>/                      # catalogo, historico, grafo, acesso
      componentes/               # PascalCase.tsx, só visual
      hooks/                     # useAlgo.ts, toda a lógica
      api.ts                     # funções tipadas que chamam /api/...
      tipos.ts                   # tipos do domínio dessa funcionalidade
  compartilhado/
    api/cliente.ts               # ÚNICO lugar com fetch (erros, JSON, credenciais)
    componentes/                 # visuais reutilizáveis (Carregando, MensagemErro)
    hooks/                       # hooks genéricos (useCarregavel, useDebounce)
```

- As funcionalidades espelham os módulos do backend (`catalogo`, `acesso`...). Uma funcionalidade pode importar de `compartilhado/`, mas não de outra funcionalidade; se precisar, mova para `compartilhado/`.
- Sem barrel files (`index.ts` reexportando tudo). Importe do arquivo.
- Só exportações nomeadas (`export function X`); `export default` é erro, exceto em `*.config.ts`.

## Acesso à API

- `fetch` é proibido pelo Biome fora de `src/compartilhado/api/cliente.ts`.
- Toda URL começa com `/api/...` (proxy do Vite em dev; mesma origem em produção). Nunca `http://localhost:8000`.
- `api.ts` de cada funcionalidade expõe funções tipadas (`listarRegras(repositorioId)`). A resposta chega como `unknown` e é **validada/estreitada** antes de virar tipo de domínio; nada de `as Regra`.
- Os tipos mantêm os nomes de campo do JSON da API, que segue `docs/arquitetura-tcc.md` seção 7 (português, snake_case: `versao_sincronizada`). Não converta para camelCase.
- Segredos nunca chegam ao frontend. Não use `import.meta.env` para tokens.

## TypeScript estrito

`tsconfig.app.json` liga `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitReturns`, `noImplicitOverride` e `noPropertyAccessFromIndexSignature`. Consequências práticas:

- Proibido: `any` (use `unknown` e estreite), `!` non-null assertion, `as` para "calar" o compilador, `@ts-ignore`/`@ts-expect-error`. `as const` é permitido.
- `lista[0]` é `T | undefined`: trate o `undefined`.
- Props opcionais: não passe `prop={undefined}`; omita a prop ou tipe como `prop?: T | undefined` se precisar.
- Props sempre com tipo nomeado `<Componente>Props`; nada de `React.FC`.
- `switch` sobre uniões discriminadas termina com verificação de exaustividade (`const _nunca: never = valor`).
- Use `import type` para tipos (o Biome corrige com `pnpm check:fix`).

## Biome

Configuração em `biome.json`: preset `recommended`, domínio React completo, e várias regras elevadas a erro (dependências exaustivas de hooks, sem `console`, sem `key` por índice, chaves obrigatórias em `if`, sem default export, nomes de arquivo camelCase/PascalCase). O `pnpm check` roda com `--error-on-warnings`: aviso também reprova.

- Nunca desligue regra com `biome-ignore` sem perguntar. Se uma regra atrapalha de verdade, proponha a mudança no `biome.json`.
- `useExhaustiveDependencies` reclamou? A dependência faltando é quase sempre um bug; corrija em vez de suprimir.

## Convenções

- Português nos identificadores de domínio, textos da interface e nomes de arquivo (`CatalogoRegras.tsx`, `useHistoricoPr.ts`). Prefixo `use` e termos técnicos ficam em inglês.
- Handlers recebidos por prop: `aoAlgo` (`aoSelecionar`); funções internas do hook: verbo (`selecionar`).
- Toda tela trata os três estados: carregando, erro e vazio. A defasagem da sincronização (merge feito, tarefa pendente/erro) deve ficar visível (arquitetura, seção "Portal de consulta e histórico").
- Acessibilidade: elementos semânticos (`button`, `nav`, `table`), `alt` em imagens, rótulo em campos. O domínio React do Biome cobre parte disso.
- CSS simples por enquanto (`index.css` + arquivos por componente). Cores como variáveis CSS em `:root`.

## Comandos

```bash
make portal        # pnpm dev em :5173 (proxy /api → :8000)
pnpm check         # Biome (lint + formatação), aviso reprova
pnpm check:fix     # aplica correções automáticas
pnpm tipos         # tsc -b
```

Antes de considerar uma tarefa de frontend pronta: `pnpm check` e `pnpm tipos` sem erros (ou `make verificar` na raiz).
