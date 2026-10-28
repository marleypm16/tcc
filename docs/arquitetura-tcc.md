# TCC — Proposta de arquitetura e implementação

Este documento registra a proposta técnica discutida para implementar o produto definido em [escopo-tcc.md](escopo-tcc.md). O escopo define **o que vamos construir**; este documento descreve **como podemos construir**.

As tecnologias abaixo são recomendações iniciais. O provedor e o modelo de IA serão escolhidos após um piloto que considere qualidade, consumo e limites de uso. As condições de acesso às APIs devem ser conferidas novamente antes dos experimentos.

## 1. Direção da arquitetura

Vamos utilizar **Python no backend e no analisador de código**, organizando a aplicação como um **monólito modular**: um único projeto dividido em módulos de análise, documentação, GitHub e IA.

O servidor web recebe os eventos do GitHub e atende o portal. Um processo separado, chamado **worker**, executa as análises demoradas a partir de uma fila. Os dois processos compartilham o mesmo núcleo de análise.

O fluxo geral será:

1. O GitHub informa que um PR foi aberto ou atualizado.
2. O backend registra o evento e agenda a análise.
3. O worker obtém as versões do código e executa a análise estática.
4. A LLM recebe o contexto relevante e propõe atualizações na documentação.
5. A aplicação salva as propostas e publica um comentário no PR.
6. Uma pessoa revisa as sugestões pelo portal.
7. Após a incorporação do código e a publicação das atualizações aprovadas, o catálogo passa a refletir a nova versão.

## 2. Tecnologias propostas

| Parte | Tecnologia | Responsabilidade |
|---|---|---|
| Backend | FastAPI | Receber webhooks, disponibilizar as operações da aplicação e atender o portal. |
| Análise estática | Biblioteca padrão `ast` | Extrair a estrutura do código Python e apoiar a comparação entre versões. |
| Acesso às versões | Git e API do GitHub | Obter arquivos, commits e informações dos PRs. |
| Integração com IA | Adaptador para o provedor escolhido | Preparar as requisições e validar as respostas da LLM. |
| Banco de dados | PostgreSQL + SQLAlchemy | Persistir análises, propostas, revisões e histórico. |
| Fila de processamento | RQ + Redis | Agendar análises, executá-las em segundo plano e permitir novas tentativas. |
| Portal | Jinja2 + JavaScript | Exibir catálogo, propostas e histórico. |
| Visualização do grafo | Cytoscape.js | Apresentar dependências e destacar módulos envolvidos nas mudanças. |

O [FastAPI permite renderizar páginas com Jinja2](https://fastapi.tiangolo.com/advanced/templates/), então podemos começar com uma interface enxuta servida pelo próprio backend. O grafo utiliza [Cytoscape.js](https://js.cytoscape.org/), uma biblioteca JavaScript para visualização e análise de redes.

O [SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/quickstart.html) fará o acesso aos dados. O [RQ](https://python-rq.org/docs/) permite enfileirar funções Python para execução em um worker, utilizando Redis como infraestrutura da fila.

## 3. Núcleo de análise com `ast`

A biblioteca `ast` transforma o código Python em uma árvore de sintaxe abstrata. Podemos percorrer essa árvore para identificar funções, classes, condições, chamadas, retornos e importações. A entrada é o texto do código; não precisamos executar o projeto analisado para extrair sua estrutura. [Documentação do `ast`](https://docs.python.org/3/library/ast.html).

O processamento será dividido em cinco etapas:

1. **Extração:** identificar módulos, funções, métodos, classes e referências presentes no código.
2. **Comparação:** localizar inclusões, remoções e alterações estruturais entre as versões envolvidas na mudança.
3. **Seleção de contexto:** reunir código anterior e novo, regras já documentadas e dependências relevantes.
4. **Interpretação pela LLM:** avaliar se existe mudança de negócio e propor a atualização correspondente.
5. **Validação:** conferir o formato da resposta e se as referências apresentadas existem no código analisado.

### Exemplo

Código anterior:

```python
if valor_compra >= 100:
    desconto = 0.10
```

Código alterado:

```python
if valor_compra >= 150:
    desconto = 0.10
```

A comparação estrutural identifica a troca de `100` por `150` na condição. A LLM recebe os dois trechos e a regra existente, podendo propor:

> O desconto de 10% passa a ser concedido para compras a partir de R$ 150.

A análise também precisa considerar alterações fora das funções, como constantes e importações. Uma função pode manter o mesmo texto e mudar de comportamento porque uma constante utilizada por ela foi alterada.

### Limites da análise estática

O `ast` não determina sozinho o significado de negócio de uma alteração nem resolve todas as dependências de Python. A proposta inicial é construir um grafo de importações e chamadas que conseguimos resolver estaticamente, registrando relações desconhecidas como limitação.

Uma dependência indica possível impacto e necessidade de análise. Sua existência não comprova uma mudança de regra de negócio. Da mesma forma, uma alteração estrutural exige interpretação: pode representar uma mudança de negócio ou uma refatoração sem mudança de comportamento.

## 4. Integração com o GitHub

### GitHub App

A integração será feita por uma **GitHub App**, que representa a identidade do aplicativo dentro do GitHub. A equipe instala o app nos repositórios que deseja acompanhar e concede as permissões necessárias.

A integração possui duas peças:

- **Webhook:** o GitHub avisa nossa aplicação de que um evento aconteceu.
- **API do GitHub:** nossa aplicação busca informações e publica os resultados.

O GitHub documenta o fluxo de receber um evento de PR e responder com um comentário. Embora o tutorial utilize JavaScript, o mesmo fluxo pode ser implementado em Python. [Tutorial oficial](https://docs.github.com/en/apps/creating-github-apps/writing-code-for-a-github-app/building-a-github-app-that-responds-to-webhook-events).

### Eventos acompanhados

O evento principal será `pull_request`, com tratamento das seguintes ações:

| Ação | Significado para a aplicação |
|---|---|
| `opened` | Iniciar a análise de um novo PR. |
| `synchronize` | Analisar a nova versão após atualização dos commits do PR. |
| `reopened` | Retomar o acompanhamento e verificar a necessidade de nova análise. |
| `closed` | Verificar se houve merge ou encerramento sem incorporação do código. |

Um PR fechado sem merge não deve atualizar o catálogo vigente. A lista de eventos e seus payloads está na [documentação de webhooks do GitHub](https://docs.github.com/en/webhooks/webhook-events-and-payloads).

### Recebimento e processamento

1. O GitHub envia uma requisição para um endpoint como `POST /webhooks/github`.
2. O backend valida a assinatura com o segredo do webhook, identifica o evento e registra o recebimento.
3. A aplicação agenda a análise e responde ao GitHub.
4. O worker obtém as versões do código, executa o pipeline e persiste o resultado.
5. A aplicação publica ou atualiza o comentário do bot no PR, com o resumo e um link para revisão no portal.

O backend precisa responder rapidamente: o GitHub espera uma resposta em até dez segundos. Por isso, a análise e as chamadas à LLM ficam na fila, fora do processamento da requisição. O identificador da entrega também deve ser registrado para evitar processamento duplicado de um mesmo evento. [Boas práticas para webhooks](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks).

As análises e aprovações devem estar vinculadas à versão exata do código. Se novos commits alterarem o PR, uma proposta aprovada anteriormente precisa ser revalidada antes da consolidação.

### Autenticação e permissões

A aplicação utiliza sua chave privada para autenticar como GitHub App e solicitar um **token de instalação**, válido por uma hora. Esse token permite atuar nos repositórios autorizados pela instalação. [Autenticação da instalação](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation).

As permissões previstas são:

- **Contents — leitura:** obter o conteúdo do código.
- **Pull requests — leitura e escrita:** consultar PRs e publicar comentários.
- **Contents — escrita:** publicar os arquivos de documentação por meio de uma branch e de um PR de documentação.

Os comentários gerais de PR são atendidos pelos endpoints de comentários de issues, pois o GitHub compartilha essas operações entre issues e PRs. [API de comentários](https://docs.github.com/en/rest/issues/comments).

A autenticação do bot é distinta do acesso de uma pessoa ao portal. O mecanismo de login e a autorização dos revisores serão detalhados na implementação da revisão humana.

### Desenvolvimento local e hospedagem

Durante o desenvolvimento, podemos encaminhar os eventos do GitHub para o backend local usando uma ferramenta como o Smee, utilizada no tutorial oficial. Para operação contínua, o backend precisará de um endereço público HTTPS. [Tutorial com encaminhamento local](https://docs.github.com/en/apps/creating-github-apps/writing-code-for-a-github-app/building-a-github-app-that-responds-to-webhook-events).

A hospedagem do backend, do banco e da fila ainda será definida. A gratuidade de uma API de IA não implica hospedagem gratuita desses componentes.

## 5. Uso de LLM e alternativas de acesso

A primeira versão utilizará um modelo existente por API. Não precisamos treinar um modelo próprio para começar.

É necessário distinguir o acesso a um chatbot da disponibilidade de uma API gratuita. A API do DeepSeek é cobrada por tokens, portanto não devemos planejar o projeto contando com sua gratuidade permanente. [Preços oficiais do DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/).

| Opção | Situação para começar | Papel proposto |
|---|---|---|
| Gemini API | Possui nível gratuito para determinados modelos, sujeito a cotas. | Primeira opção para um piloto. |
| GroqCloud | Possui plano gratuito, com restrições de requisições e tokens. | Alternativa para avaliar no piloto. |
| DeepSeek API | API cobrada por tokens. | Alternativa caso exista orçamento posteriormente. |

As condições estão nas páginas oficiais de [preços do Gemini](https://ai.google.dev/gemini-api/docs/pricing), [limites do Gemini](https://ai.google.dev/gemini-api/docs/rate-limits) e [limites da Groq](https://console.groq.com/docs/rate-limits). As cotas efetivamente disponíveis precisam ser verificadas na conta utilizada pelo projeto.

No nível gratuito do Gemini, o conteúdo pode ser utilizado para melhorar os produtos. Essa condição precisa ser considerada se o estudo de caso envolver código privado. [Condições apresentadas na página de preços](https://ai.google.dev/gemini-api/docs/pricing).

### Adaptador de IA

O núcleo de análise terá uma interface própria para solicitar a interpretação de uma mudança. O código específico de cada provedor ficará em um adaptador, permitindo substituir a integração sem reescrever o analisador.

A resposta esperada será estruturada, contendo informações como:

- Existência ou ausência de mudança de regra de negócio.
- Regras afetadas e referências ao código que sustentam a proposta.
- Tipo de atualização: inclusão, alteração ou remoção.
- Texto proposto para a documentação.

A validação do formato e das referências não comprova a corretude semântica da resposta. Essa parte continua sujeita à revisão humana e à avaliação do TCC.

### Controle de consumo e escolha do modelo

Para controlar o consumo, enviaremos as unidades alteradas e o contexto relevante, incluindo dependências e regras existentes quando necessário. Não enviaremos o repositório inteiro a cada PR.

Antes de escolher o modelo, faremos um piloto com alguns PRs rotulados para medir qualidade, consumo e disponibilidade. Uma API gratuita pode permitir o desenvolvimento, mas suas cotas precisam ser confrontadas com o volume previsto para o replay histórico.

As execuções registrarão provedor, modelo, versão do prompt, parâmetros, tokens e tempo. Nos experimentos, a configuração será mantida consistente entre as comparações; mudanças de modelo ou de prompt precisarão ser registradas.

## 6. Armazenamento e versionamento da documentação

Como o escopo prevê documentação versionada junto ao repositório, a proposta separa os dados de operação dos artefatos publicados:

| Local | Conteúdo |
|---|---|
| PostgreSQL | Eventos recebidos, execuções de análise, propostas, revisões humanas, métricas e índice das versões publicadas. |
| Repositório analisado | Catálogo aprovado em JSON e Markdown, vinculado à versão de código documentada. |

O JSON representa os dados estruturados do catálogo; o Markdown apresenta o conteúdo para leitura. Ambos devem ser gerados a partir da mesma versão aprovada, evitando manutenção independente.

A publicação será realizada por um **PR de documentação**, contendo as atualizações aprovadas e correspondentes ao código incorporado. O portal indexará as versões publicadas e apresentará propostas pendentes separadamente.

Enquanto o PR de documentação estiver pendente, o portal deverá indicar a versão de código efetivamente documentada e a atualização ainda não publicada. Isso evita apresentar um catálogo antigo como sincronizado com o código atual.

PRs que contenham somente os arquivos gerados do catálogo serão reconhecidos para evitar um ciclo de análises e novas publicações.

## 7. Organização do código e reaproveitamento

O projeto terá módulos com responsabilidades explícitas:

| Módulo | Responsabilidade |
|---|---|
| Análise | Extração de AST, comparação de versões, dependências e seleção de contexto. |
| IA | Preparação das solicitações, adaptadores de provedores e validação das respostas. |
| Documentação | Catálogo, propostas, revisões, histórico e geração de artefatos. |
| GitHub | Webhooks, autenticação, consulta de PRs e publicação de comentários e documentação. |
| Portal | Consulta de regras, revisão de propostas e visualização do histórico e do grafo. |
| Avaliação | Replay de PRs, execução das linhas de base e coleta de métricas. |

O núcleo de análise deve receber versões de código e documentação existente sem depender do recebimento de um webhook. Assim, será possível chamá-lo pelo terminal, pelo worker da integração com o GitHub e pelo experimento de replay.

Esse reaproveitamento permite avaliar o mesmo processamento utilizado pela aplicação. O replay poderá executar as análises e registrar os resultados sem publicar comentários nos repositórios estudados.

## 8. Ordem de implementação

1. **Analisador local:** receber duas versões de código pelo terminal, extrair as estruturas e identificar alterações e dependências.
2. **Catálogo e IA:** gerar uma base inicial, integrar um provedor e produzir propostas estruturadas de atualização. Executar o piloto para escolher o modelo.
3. **Persistência e processamento:** salvar análises e propostas, configurar o banco e executar as análises pela fila.
4. **GitHub App:** receber eventos, obter o código das versões analisadas e publicar o comentário do bot no PR.
5. **Portal e revisão:** implementar catálogo pesquisável, revisão das propostas, histórico e grafo.
6. **Publicação da documentação:** gerar JSON e Markdown, abrir o PR de documentação e acompanhar a publicação das versões aprovadas.
7. **Avaliação:** executar o replay histórico e as linhas de base, coletando os resultados definidos no escopo.

O registro das métricas e das configurações deve começar nas primeiras execuções; a etapa final organiza o experimento completo.

## 9. Pontos a detalhar antes da implementação correspondente

- Modelo e provedor de IA, com base no piloto e nas cotas disponíveis.
- Versão do Python utilizada pelo analisador e versões de sintaxe suportadas nos repositórios de avaliação.
- Critérios para selecionar contexto e resolver dependências estaticamente.
- Formato do catálogo e identificação estável das regras entre versões.
- Login no portal e autorização para revisar propostas de um repositório.
- Reconciliação das propostas quando o PR recebe commits ou a branch de referência avança.
- Hospedagem do backend, do banco, da fila e do worker.

O primeiro incremento será o **analisador local que compara duas versões e produz uma proposta de atualização**, estabelecendo o núcleo reutilizado pela integração com o GitHub e pelos experimentos do TCC.
