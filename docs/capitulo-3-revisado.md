# 3. PROCEDIMENTOS METODOLÓGICOS

## 3.1 Caracterização da pesquisa

Esta pesquisa classifica-se, quanto à sua natureza, como aplicada, pois visa gerar conhecimentos para aplicação prática dirigidos à solução de um problema específico (Gil, 2017): a perda do conhecimento sobre as regras de negócio de sistemas de *software*, que ocorre quando esse conhecimento permanece restrito ao código-fonte e à memória dos desenvolvedores ou quando a documentação existente deixa de corresponder ao comportamento implementado à medida que o sistema evolui.

Quanto aos objetivos, a pesquisa é exploratória e descritiva (Gil, 2017). É exploratória porque investiga a viabilidade de combinar análise estática de código e modelos de linguagem de grande porte na manutenção contínua da documentação de regras de negócio. É descritiva porque descreve e mensura o comportamento da ferramenta desenvolvida ao longo da evolução de sistemas reais.

Quanto à abordagem, adota um formato qualiquantitativo. A dimensão quantitativa constitui a avaliação principal e reúne métricas de detecção, corretude, atualização e custo, obtidas em um experimento sobre o histórico de *pull requests* de repositórios de código aberto. A dimensão qualitativa é complementar e compreende o julgamento humano da corretude das atualizações propostas e, quando viável, a percepção de uma equipe de desenvolvimento que utilize a ferramenta em seu próprio sistema.

O procedimento metodológico organiza-se, assim, em duas frentes: o desenvolvimento da ferramenta, descrito na seção 3.2, e a sua avaliação, descrita na seção 3.3.

## 3.2 Etapas de desenvolvimento da ferramenta

A ferramenta atua sobre repositórios escritos na linguagem Python e hospedados na plataforma GitHub, e opera em dois momentos distintos. O primeiro é a geração da base de conhecimento, executada uma única vez a partir de uma versão de referência do repositório. O segundo é um ciclo incremental, repetido a cada *pull request* (PR), no qual a ferramenta identifica mudanças nas regras de negócio, propõe a atualização da documentação e submete essa proposta à revisão humana. A Figura 1 apresenta o fluxo geral desse processo.

**[Inserir Figura 1 — Fluxo de geração e manutenção da documentação]**

Fonte: Elaborado pelo autor (2026)

### 3.2.1 Geração da base de conhecimento

A primeira etapa produz a documentação inicial do sistema. A ferramenta recebe um repositório e uma versão de referência e converte cada arquivo de código-fonte em uma Árvore de Sintaxe Abstrata (AST). A partir da travessia hierárquica dos nós dessa árvore, identifica módulos, classes, funções e métodos, bem como as relações de importação e de chamada entre eles, compondo um inventário estrutural do sistema e o seu grafo de dependências.

Com base nesse inventário, a ferramenta gera o catálogo inicial de regras de negócio, organizado por módulo e por unidade de código (função ou método). Cada regra recebe uma identificação estável, e a versão do código analisada é registrada, de modo que toda entrada do catálogo possa ser rastreada até a sua origem. Essa base é disponibilizada para revisão antes de passar a compor a documentação vigente.

### 3.2.2 Análise incremental por *pull request*

A segunda etapa é executada sempre que um PR é aberto ou atualizado. A ferramenta compara a versão anterior e a nova versão do código e identifica as unidades alteradas. O grafo de dependências é utilizado para apontar os módulos possivelmente impactados pela mudança; as dependências, entretanto, indicam apenas onde investigar e não comprovam, por si só, que uma regra de negócio foi alterada.

Para que essa decisão seja consistente, adota-se uma definição operacional de mudança de regra de negócio: alteração em condição, cálculo, validação, fluxo de estados, regra de autorização ou contrato de entrada e saída que modifique um comportamento do domínio. Não constituem, isoladamente, mudança de regra de negócio a renomeação de elementos, a formatação, a refatoração sem mudança de comportamento e as alterações restritas a testes, dependências ou configuração. Em PRs que combinam diferentes tipos de alteração, consideram-se apenas aquelas que afetam o comportamento de negócio.

Nessa etapa, a ferramenta integra-se a modelos de linguagem de grande porte (LLMs — *Large Language Models*). Em vez de enviar o código inteiro ou o diff bruto, o que excede limites de contexto e introduz ruído, a ferramenta envia as unidades alteradas, isoladas na análise da AST, junto com as entradas do catálogo relacionadas e instruções de contexto (*prompts*). Cabe ao modelo classificar se houve mudança de regra de negócio, localizar as entradas do catálogo afetadas e propor a inclusão, a alteração ou a remoção de regras. O texto produzido pelo modelo constitui uma proposta, e não a documentação definitiva.

### 3.2.3 *Feedback* no *pull request* e revisão humana

A terceira etapa leva as propostas ao local em que a revisão de código já acontece. A ferramenta publica no PR um comentário que resume as regras alteradas, a documentação afetada e o texto sugerido, com referências às linhas de código correspondentes. Uma pessoa da equipe revisa cada sugestão e pode aceitá-la, ajustá-la ou rejeitá-la.

A documentação vigente incorpora somente as atualizações aprovadas e correspondentes ao código integrado à *branch* de referência. Um PR fechado sem *merge* não altera o catálogo, e as propostas ainda não revisadas permanecem identificadas separadamente. O catálogo é versionado junto ao repositório, o que preserva o histórico de cada regra ao lado do código que a implementa.

Por exemplo, se um PR alterar o valor mínimo exigido para a concessão de um desconto, a ferramenta deverá identificar a mudança na condição, localizar a regra documentada e sugerir o novo texto. Após a revisão e a incorporação do código, o catálogo passa a exibir a regra atual, preservando o valor anterior e o vínculo com o PR que a modificou.

### 3.2.4 Portal de consulta

A quarta etapa compreende a construção da interface de usuário (*front-end*) que torna o conhecimento mantido acessível à equipe. O portal oferece um catálogo de regras de negócio pesquisável por texto e por módulo, com acesso à origem de cada regra no código. Oferece também a revisão das propostas pendentes e uma linha do tempo por PR, que apresenta o texto da regra antes e depois de cada alteração e o PR responsável.

Complementarmente, o portal exibe o grafo de dependências do sistema, com nós e arestas, destacando os módulos envolvidos em cada mudança e as suas dependências. Dessa forma, o desenvolvedor pode consultar não apenas a regra vigente, mas também quando, por que e em que parte do sistema ela mudou.

## 3.3 Avaliação da ferramenta

A avaliação busca verificar em que medida a ferramenta mantém a documentação de um sistema correta e atualizada ao longo de sua evolução. Para isso, adota-se como experimento principal o *replay* histórico de PRs, complementado, por um estudo de caso com uma equipe de desenvolvimento.

### 3.3.1 Experimento de *replay* histórico

São selecionados repositórios Python de código aberto (*open-source*) com histórico de PRs adequado à análise. Para cada repositório, a ferramenta gera a base de conhecimento em um *commit* inicial e, em seguida, reprocessa os PRs reais já mesclados, na mesma ordem em que foram integrados. A meta inicial é de dois a três repositórios e de cinquenta a cem PRs por repositório, sujeita à disponibilidade de projetos adequados e ao esforço de rotulação descrito a seguir.

### 3.3.2 Construção do gabarito

Cada PR do experimento é rotulado manualmente quanto a três questões: se alterou alguma regra de negócio, segundo a definição operacional da seção 3.2.2; qual regra foi alterada; e que atualização da documentação era esperada. Sempre que possível, a rotulação é realizada por um segundo avaliador, e a concordância entre os avaliadores é medida pelo coeficiente kappa (Cohen, 1960).

O protocolo distingue as propostas originais da ferramenta das correções feitas na revisão humana. Assim, uma sugestão que só se torna correta após o ajuste do revisor não é contabilizada como acerto automático.

### 3.3.3 Métricas

As métricas adotadas cobrem quatro dimensões, apresentadas no Quadro 2.

**Quadro 2 — Métricas de avaliação da ferramenta**

| Dimensão | O que mede | Métrica |
|---|---|---|
| Detecção | Se a ferramenta percebe quando uma regra de negócio mudou | Precisão, *recall* e F1 por PR |
| Corretude | Se a atualização proposta está certa | Percentual de propostas corretas, parcialmente corretas e incorretas (avaliação manual) |
| Atualização | Se, ao longo da sequência de PRs e ao final dela, a documentação ainda reflete o código | Percentual de regras documentadas desatualizadas e registro das regras esperadas ausentes |
| Custo | Se é viável executar a análise a cada PR | Tempo de processamento e consumo de *tokens* por PR |

Fonte: Elaborado pelo autor (2026)

Na dimensão de detecção, a precisão corresponde à proporção dos PRs sinalizados pela ferramenta que de fato alteraram regras de negócio; o *recall* corresponde à proporção dos PRs que alteraram regras de negócio e foram sinalizados; e o F1 é a média harmônica entre ambos.

Como verificação complementar, a acurácia estrutural do grafo de dependências é conferida manualmente em uma amostra de módulos, verificando se as relações extraídas da AST refletem a estrutura real do código.

---

## Referências a acrescentar

COHEN, J. A coefficient of agreement for nominal scales. **Educational and Psychological Measurement**, v. 20, n. 1, p. 37–46, 1960.

GIL, A. C. **Como elaborar projetos de pesquisa**. 6. ed. São Paulo: Atlas, 2017.

WAZLAWICK, R. S. **Metodologia de pesquisa para ciência da computação**. 2. ed. Rio de Janeiro: Elsevier, 2014.

---

## Notas para o autor (não colar no TCC)

- **Figura 1:** desenhar o fluxo abaixo no Word, no draw.io ou em outra ferramenta.

  ```mermaid
  flowchart LR
      A[Repositório + versão de referência] --> B[Geração da base: AST, grafo e catálogo inicial]
      B --> C[Revisão da base]
      C --> D[(Catálogo vigente)]
      E[PR aberto ou atualizado] --> F[Análise incremental: unidades alteradas + LLM]
      F --> G[Comentário no PR com propostas]
      G --> H{Revisão humana}
      H -->|aceita / ajusta| I[Proposta aprovada]
      H -->|rejeita| J[Descartada]
      I --> K{PR mesclado?}
      K -->|sim| D
      K -->|não| L[Catálogo inalterado]
      D --> M[Portal: catálogo, histórico por PR e grafo]
  ```

- **Pergunta de pesquisa:** a seção 3.3 remete a ela ("em que medida..."), mas ela deve ser apresentada na Introdução, que será revisada depois.
- **Remissões a capítulos futuros:** o texto remete ao Capítulo 4 (desenvolvimento). A delimitação do escopo (só Python e GitHub, sem documentos humanos, sem edição do código, agentes de IA como trabalho futuro) fica para o capítulo de limitações e trabalhos futuros.
- **Design Science Research:** não foi adotado no texto. Se a orientadora preferir, ele entra na seção 3.1, no parágrafo de procedimentos técnicos.
- **Referências:** confira as edições de Gil e Wazlawick nos exemplares que você usar.
