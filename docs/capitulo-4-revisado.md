# 4. DESENVOLVIMENTO DA FERRAMENTA

Este capítulo descreve a construção da ferramenta cujas etapas foram apresentadas na seção 3.2. Inicialmente, apresenta-se a arquitetura da aplicação e as tecnologias empregadas. Em seguida, descrevem-se o modelo adotado para o catálogo de regras de negócio, o modelo de dados da aplicação e a implementação de cada etapa: a geração da base de conhecimento, a análise incremental por *pull request*, a integração com o GitHub e o portal de consulta.

## 4.1 Arquitetura

A aplicação adota o estilo de monólito modular com processamento assíncrono. Ela é composta por dois processos, um processo web e um processo de processamento em segundo plano (*worker*), mantidos no mesmo repositório, escritos na mesma linguagem e apoiados sobre um único banco de dados. Os dois processos compartilham os mesmos módulos de código, mas têm pontos de entrada distintos e responsabilidades separadas, apresentadas no Quadro 3.

**Quadro 3 — Processos da aplicação**

| Processo | Responsabilidade |
|---|---|
| Processo web (API) | Receber e validar as notificações enviadas pelo GitHub, registrar os eventos e as tarefas correspondentes, autenticar as pessoas que acessam o portal e disponibilizar os dados consultados por elas. |
| *Worker* | Reservar as tarefas pendentes, obter as versões do código, executar a análise estática, consultar o modelo de linguagem, publicar a documentação no PR e atualizar o catálogo após o *merge*. |

Fonte: Elaborado pelo autor (2026)

### 4.1.1 Componentes

A Figura 2 apresenta os componentes da solução e as relações entre eles. Além dos dois processos da aplicação, participam da arquitetura o banco de dados PostgreSQL, o portal executado no navegador e dois serviços externos: o GitHub, que hospeda os repositórios analisados, e o modelo de linguagem Gemini, responsável pela interpretação das mudanças.

**[Inserir Figura 2 — Arquitetura da ferramenta]**

Fonte: Elaborado pelo autor (2026)

O processo web e o *worker* não se comunicam diretamente. O banco de dados é o ponto de encontro entre eles: o processo web registra as tarefas a executar, e o *worker* as retira do banco, processa e grava os resultados. A própria fila de tarefas é mantida em uma tabela do banco, o que permite registrar um evento e a tarefa correspondente em uma mesma transação. Assim, uma tarefa recebida durante uma parada do *worker* permanece registrada e é processada quando ele volta a operar.

### 4.1.2 Fluxos de funcionamento

A aplicação opera em dois fluxos. O primeiro, de leitura, é iniciado por uma pessoa que consulta a documentação:

1. A pessoa abre o portal no navegador e se autentica com sua conta do GitHub.
2. O portal solicita à API o catálogo, o histórico ou o grafo de dependências de um repositório.
3. A API verifica se a pessoa tem acesso ao repositório, consulta o banco de dados e devolve os dados no formato JSON.

O segundo fluxo, automático, é iniciado pelo GitHub sempre que um PR é aberto, atualizado ou integrado:

1. O GitHub notifica a API por meio de um *webhook*. A API valida a notificação, registra o evento e cria uma tarefa, respondendo em seguida.
2. O *worker* reserva a tarefa, obtém as duas versões do código e executa a análise estática.
3. O *worker* envia ao modelo de linguagem as unidades alteradas e o contexto relacionado e recebe a proposta de atualização da documentação.
4. O *worker* grava a documentação proposta na *branch* do próprio PR, acompanhada de um comentário que resume as alterações.
5. O revisor examina o código e a documentação no GitHub e, ao aprovar, realiza o *merge* do PR.
6. O *merge* gera uma nova notificação, e o *worker* atualiza a cópia do catálogo mantida no banco, que passa a ser exibida pelo portal.

### 4.1.3 Organização em módulos

Internamente, o código da aplicação é dividido em módulos com responsabilidades delimitadas, apresentados no Quadro 4. O módulo de análise não depende do GitHub, do banco de dados nem do modelo de linguagem: recebe versões de código e a documentação existente e devolve resultados estruturados. O acesso aos serviços externos fica concentrado em adaptadores, coordenados pelo módulo de processamento.

**Quadro 4 — Módulos da aplicação**

| Módulo | Responsabilidade |
|---|---|
| API | Recebimento dos *webhooks*, autenticação das pessoas no portal e *endpoints* de consulta. |
| Processamento | Reserva das tarefas, controle das etapas, novas tentativas e recuperação de falhas. |
| Análise | Extração da AST, comparação de versões, dependências e seleção de contexto. |
| IA | Preparação das solicitações, comunicação com o Gemini e validação das respostas. |
| Documentação | Geração dos arquivos do catálogo, importação após o *merge* e histórico das versões. |
| GitHub | Validação dos eventos, autenticação, obtenção das versões e publicação de *commits* e comentários. |
| Persistência | Modelos de dados, acesso ao banco e migrações, compartilhados pelos dois processos. |
| Portal | Interface de consulta do catálogo, do histórico e do grafo. |

Fonte: Elaborado pelo autor (2026)

## 4.2 Tecnologias utilizadas

O Quadro 5 apresenta as tecnologias empregadas na construção da ferramenta e o papel de cada uma.

**Quadro 5 — Tecnologias utilizadas**

| Parte da solução | Tecnologia | Papel na ferramenta |
|---|---|---|
| Linguagem | Python | Implementação da API, do *worker* e do módulo de análise. A versão é fixada no ambiente para permitir a reprodução dos experimentos. |
| API | FastAPI | Recebimento dos *webhooks* e atendimento às consultas do portal. |
| Análise estática | Módulo `ast` da biblioteca padrão do Python | Conversão do código-fonte em AST, extração da estrutura e comparação entre versões. |
| Banco de dados | PostgreSQL | Armazenamento dos eventos, das tarefas, das análises, das propostas e da cópia do catálogo. |
| Acesso ao banco | SQLAlchemy | Mapeamento dos dados e migrações, compartilhados pela API e pelo *worker*. |
| Integração com o GitHub | GitHub App, *webhooks* e API REST do GitHub | Notificação dos eventos de PR, obtenção do código, publicação da documentação e dos comentários e autenticação das pessoas no portal. |
| Modelo de linguagem | Gemini 3.6 Flash, por meio da Gemini API | Interpretação das mudanças e redação das regras de negócio em linguagem natural. |
| Portal | React, com Vite | Construção da interface de consulta executada no navegador. |
| Visualização do grafo | Cytoscape.js | Exibição do grafo de dependências e destaque dos módulos envolvidos em uma mudança. |
| Hospedagem | Render | Execução do processo web e do *worker*. |

Fonte: Elaborado pelo autor (2026)

Os repositórios analisados são escritos em Python 3. A versão da linguagem usada para executar a ferramenta é independente da versão do projeto analisado, pois o código é lido como texto, sem a instalação de suas dependências e sem execução. O módulo `ast` da versão instalada aceita o código da versão atual e de versões anteriores do Python 3, desde que a sintaxe utilizada continue suportada pelo interpretador (Python Software Foundation, 2026).

## 4.3 Modelo do catálogo e modelo de dados

O catálogo é o conjunto das regras de negócio documentadas de um sistema. Cada regra está vinculada a uma unidade de código, isto é, a uma função ou a um método, e é descrita pelos atributos apresentados no Quadro 6.

**Quadro 6 — Atributos de uma regra de negócio no catálogo**

| Atributo | Descrição |
|---|---|
| Identificador | Código único e estável da regra, atribuído na sua criação e mantido nas alterações posteriores. |
| Título | Nome curto da regra. |
| Descrição | Enunciado da regra em linguagem natural. |
| Módulo | Módulo do sistema ao qual a regra pertence. |
| Unidade de código | Nome qualificado da função ou do método que implementa a regra (por exemplo, `vendas.pedido.calcular_desconto`). |
| Localização | Arquivo e intervalo de linhas da unidade de código. |
| Versão do código | *Commit* analisado quando a regra foi registrada ou alterada pela última vez. |
| PR de origem | PR responsável pela última alteração da regra. |
| Situação | Indica se a regra está vigente ou foi removida. |

Fonte: Elaborado pelo autor (2026)

O identificador não é derivado da posição da regra no código. Desse modo, uma regra mantém sua identidade quando a unidade que a implementa muda de linha, de arquivo ou de nome; nesses casos, atualiza-se apenas o vínculo com a unidade. Essa estabilidade permite reunir, sob o mesmo identificador, todas as versões de uma regra ao longo da evolução do sistema.

### 4.3.1 Armazenamento e versionamento

A versão oficial do catálogo é mantida no próprio repositório analisado, junto ao código, em dois formatos gerados a partir da mesma estrutura de dados. O formato JSON é destinado ao processamento pela ferramenta, e o formato Markdown, à leitura por pessoas, inclusive na própria interface do GitHub. Como os arquivos do catálogo são versionados pelo Git, cada alteração de uma regra fica registrada no histórico do repositório, ao lado da alteração de código que a motivou.

O banco de dados mantém uma cópia do catálogo incorporado à *branch* de referência, utilizada pelo portal. Para cada regra, o banco armazena todas as suas versões, com o texto anterior e o novo, o PR e o *commit* correspondentes e a data da incorporação. O banco também registra os dados operacionais da ferramenta: os eventos recebidos, as tarefas, as análises realizadas e as propostas originais geradas pelo modelo, preservadas separadamente das edições feitas pelos revisores.

### 4.3.2 Modelo de dados

O banco de dados é organizado em onze entidades, apresentadas no Quadro 7, e em três tabelas associativas, que representam as relações de muitos para muitos entre usuários e repositórios, entre módulos e entre propostas e trechos de código.

**Quadro 7 — Entidades do modelo de dados**

| Entidade | Conteúdo |
|---|---|
| Usuário | Pessoa autenticada no portal, identificada pela sua conta do GitHub. |
| Repositório | Repositório acompanhado, com a instalação da GitHub App a que pertence e a versão do catálogo sincronizada. |
| Módulo | Módulo Python do repositório na versão vigente do catálogo. |
| *Pull request* | PR do repositório, com seu estado e as versões de código envolvidas. |
| Evento | Notificação recebida do GitHub, identificada pelo seu identificador de entrega. |
| Tarefa | Operação a ser executada pelo *worker*, originada de um evento. |
| Análise | Execução da análise incremental sobre uma versão do PR, com a configuração do modelo de linguagem, o consumo registrado e a publicação realizada no PR. |
| Trecho de código | Cópia de uma unidade de código no momento da análise, nas versões base e nova, indicando se a unidade foi alterada ou apenas enviada como contexto. |
| Proposta | Atualização de regra sugerida pelo modelo de linguagem, preservada sem alterações. |
| Regra | Identidade estável de uma regra de negócio no catálogo. |
| Versão da regra | Conteúdo da regra incorporado por um *merge*, com os atributos do Quadro 6. |

Fonte: Elaborado pelo autor (2026)

A Figura 3 apresenta as relações entre as entidades e suas cardinalidades.

**[Inserir Figura 3 — Modelo de dados]**

Fonte: Elaborado pelo autor (2026)

Um repositório reúne vários PRs, módulos e regras. Cada usuário pode acessar vários repositórios, e cada repositório pode ser acessado por vários usuários. Um PR recebe vários eventos, e cada evento gera no máximo uma tarefa, pois os eventos ignorados, como os provocados pelos *commits* da própria ferramenta, não geram processamento. Um PR pode ser analisado várias vezes, uma para cada nova versão do código, e cada análise contém zero ou mais propostas; não há propostas quando o modelo conclui que o PR não alterou regras de negócio.

Cada análise registra os trechos de código examinados, isto é, as unidades alteradas e as unidades de contexto, exatamente como foram enviadas ao modelo. Cada proposta cita um ou mais desses trechos, e um mesmo trecho pode sustentar mais de uma proposta, relação registrada em uma tabela associativa. Esse registro permite apresentar, no histórico de uma regra, o código anterior e o novo que motivaram a alteração e reproduzir cada interpretação na avaliação sem consultar novamente o GitHub.

Uma regra possui uma ou mais versões, e cada versão é incorporada por um PR e pertence a um módulo. A versão fica vinculada à proposta que lhe deu origem, o que permite comparar o texto sugerido pelo modelo com o texto incorporado após a revisão; versões criadas diretamente pelos revisores não têm proposta associada. Essa separação permite à avaliação medir a saída automática antes da intervenção humana. As dependências de importação e de chamada entre módulos são registradas em uma tabela associativa, que liga cada módulo de origem ao módulo de destino.

## 4.4 Geração da base de conhecimento

A geração da base é executada uma única vez, sobre uma versão de referência do repositório, e é composta por três passos: a extração da estrutura, a construção do grafo de dependências e a geração do catálogo inicial.

### 4.4.1 Extração da estrutura

Cada arquivo Python do repositório é convertido em AST por meio da função `ast.parse`. Em seguida, a árvore é percorrida, e a ferramenta registra, para cada arquivo, o módulo correspondente, as classes, as funções e os métodos definidos, as constantes declaradas no nível do módulo, as importações e as chamadas de funções e métodos realizadas no corpo de cada unidade. Cada unidade de código é identificada pelo seu nome qualificado, formado pelo caminho do módulo, pela classe, quando houver, e pelo nome da função ou do método.

Quando um arquivo não pode ser convertido em AST, por utilizar uma sintaxe não suportada pela versão do interpretador, o arquivo é registrado como não analisado. Essa ocorrência é tratada como análise incompleta, e não como ausência de regras de negócio.

### 4.4.2 Construção do grafo de dependências

A partir da estrutura extraída, a ferramenta constrói um grafo direcionado de dependências em dois níveis. No nível das unidades de código, os nós são as funções e os métodos, e as arestas são as chamadas de uma unidade por outra; esse grafo é calculado a cada análise e utilizado na seleção do contexto (seção 4.5.2), sem ser armazenado. No nível de módulo, os nós são os módulos do repositório, e as arestas representam a importação de um módulo por outro ou a existência de chamadas de unidades de um módulo para unidades de outro; esse é o grafo armazenado no banco e exibido no portal. As importações são resolvidas para os módulos do próprio repositório; importações de bibliotecas externas não geram arestas. As chamadas são resolvidas estaticamente sempre que o nome chamado puder ser associado a uma unidade conhecida. As chamadas que não podem ser resolvidas sem executar o código, como as que dependem do tipo de um objeto definido em tempo de execução, são registradas como não resolvidas.

### 4.4.3 Geração do catálogo inicial

Para gerar o catálogo inicial, a ferramenta envia ao modelo de linguagem, unidade por unidade, o código da unidade, as constantes que ela utiliza e as unidades que ela chama diretamente. O modelo indica se a unidade implementa alguma regra de negócio, segundo a definição operacional da seção 3.2.2, e, em caso positivo, redige o título e a descrição de cada regra. Unidades sem regras de negócio, como funções utilitárias, não geram entradas no catálogo.

A ferramenta atribui um identificador a cada regra, completa os atributos do Quadro 6 a partir da estrutura extraída e gera os arquivos JSON e Markdown do catálogo.

## 4.5 Análise incremental por *pull request*

A análise incremental é executada a cada tarefa de análise de PR e compara duas versões do código: a versão da *branch* de destino a partir da qual o PR foi criado, chamada de versão base, e a versão mais recente da *branch* do PR. O processo é composto por quatro passos: a comparação das versões, a seleção do contexto, a interpretação pelo modelo de linguagem e a validação da resposta.

### 4.5.1 Comparação das versões

A ferramenta obtém, pela API do GitHub, a lista dos arquivos Python modificados no PR e o conteúdo de cada um nas duas versões. Os dois conteúdos são convertidos em AST e as unidades de código são pareadas pelo nome qualificado. Desse pareamento resultam três situações: unidades adicionadas, presentes apenas na nova versão; unidades removidas, presentes apenas na versão base; e unidades potencialmente alteradas, presentes nas duas.

Para as unidades presentes nas duas versões, a ferramenta compara as árvores sem considerar as informações de posição, como linha e coluna. Assim, alterações apenas de formatação, de espaçamento ou de comentários não são tratadas como mudança na unidade. Também são comparadas as constantes do nível do módulo: quando uma constante é alterada, as unidades que a utilizam são marcadas como afetadas, ainda que seu próprio código não tenha mudado.

O resultado da comparação é estrutural. Ele indica onde o código mudou, mas não indica se a mudança altera uma regra de negócio. Uma alteração estrutural pode corresponder a uma refatoração sem mudança de comportamento, e essa distinção é atribuída ao passo de interpretação.

### 4.5.2 Seleção do contexto

Para cada unidade adicionada, removida ou alterada, a ferramenta reúne o contexto necessário à interpretação:

- o código da unidade na versão base e na nova versão;
- as regras do catálogo vinculadas à unidade;
- as unidades vizinhas no grafo de dependências, isto é, as que chamam e as que são chamadas pela unidade alterada, acompanhadas das regras a elas vinculadas.

As unidades vizinhas indicam onde a mudança pode ter impacto, mas a ferramenta não as trata como alteradas: elas apenas compõem o contexto enviado ao modelo. As unidades alteradas e as de contexto são registradas no banco como trechos de código da análise, conforme a seção 4.3.2.

### 4.5.3 Interpretação pelo modelo de linguagem

A comunicação com o Gemini é feita por um adaptador, que concentra a montagem das solicitações, o tratamento de erros e a leitura das respostas. A instrução enviada ao modelo (*prompt*) é composta por três partes:

1. **Instruções:** o papel atribuído ao modelo e a definição operacional de mudança de regra de negócio, incluindo as alterações que não devem ser consideradas, como renomeação e refatoração sem mudança de comportamento;
2. **Contexto:** o resultado da comparação e o contexto selecionado no passo anterior;
3. **Formato de saída:** a estrutura em JSON que a resposta deve seguir.

A resposta do modelo informa, para o PR analisado, se houve mudança de regra de negócio e, para cada mudança, a regra afetada, o tipo de atualização (inclusão, alteração ou remoção), o texto proposto e as referências às unidades de código que sustentam a proposta.

### 4.5.4 Validação da resposta

Antes de gerar a documentação, a ferramenta verifica se a resposta segue o formato esperado, se os identificadores de regras citados existem no catálogo e se as unidades de código referenciadas existem na versão analisada. Respostas que não passam nessa verificação são solicitadas novamente, até um limite de tentativas. Essa validação garante a consistência estrutural da resposta, mas não comprova a corretude do texto proposto, que continua sujeita à revisão humana.

Cada execução registra no banco o modelo utilizado, a versão do *prompt*, a quantidade de *tokens* consumidos e o tempo de processamento, dados utilizados na dimensão de custo da avaliação.

## 4.6 Integração com o GitHub e revisão

### 4.6.1 Recebimento dos eventos

A integração com o GitHub é realizada por meio de uma GitHub App instalada nos repositórios acompanhados. A aplicação tem permissão de leitura e escrita sobre o conteúdo do repositório, para obter o código e gravar os arquivos do catálogo, e sobre os PRs, para consultá-los e publicar comentários. Para atuar em um repositório, o *worker* obtém um *token* de instalação, autenticando-se com a chave privada da aplicação (GitHub, 2026).

O GitHub notifica a API a cada evento de PR por meio de um *webhook*. Ao receber uma notificação, a API verifica sua assinatura, calculada pelo GitHub com uma chave secreta compartilhada, o que garante que a notificação foi de fato enviada por ele. O Quadro 8 apresenta os eventos acompanhados e o tratamento dado a cada um.

**Quadro 8 — Eventos de *pull request* acompanhados**

| Evento | Tratamento |
|---|---|
| PR aberto (`opened`) ou reaberto (`reopened`) | Cria uma tarefa de análise do PR. |
| PR atualizado (`synchronize`) | Cria uma tarefa de análise do PR, exceto quando a atualização corresponde a um *commit* de documentação feito pela própria ferramenta. |
| PR fechado com *merge* (`closed`, com `merged` verdadeiro) | Cria uma tarefa de atualização do catálogo. |
| PR fechado sem *merge* (`closed`, com `merged` falso) | Registra o encerramento e descarta as análises pendentes, sem alterar o catálogo. |

Fonte: Elaborado pelo autor (2026)

O registro do evento e a criação da tarefa ocorrem em uma única transação do banco de dados, e a API só responde ao GitHub depois de confirmada essa transação. O processamento pesado, como a análise estática e as chamadas ao modelo de linguagem, não é executado durante o recebimento, de modo que a resposta é devolvida em poucos milissegundos. Cada notificação do GitHub traz um identificador de entrega único; como esse identificador é registrado no evento com restrição de unicidade, e cada evento gera no máximo uma tarefa, uma notificação recebida mais de uma vez não gera uma segunda tarefa.

### 4.6.2 Fila de tarefas

A fila de tarefas é a tabela `tarefas` do banco de dados. Cada tarefa registra seu tipo (análise do PR ou atualização do catálogo após o *merge*), o evento que a originou, o PR, os *commits* envolvidos, o estado, o número de tentativas, os horários de início e de conclusão e, quando houver, o erro ocorrido. O repositório e o identificador de entrega são obtidos pelo evento de origem. Os estados possíveis são pendente, processando, concluída, erro e descartada.

O *worker* consulta periodicamente a tabela e reserva a próxima tarefa pendente por meio de um único comando de atualização, que utiliza a cláusula `FOR UPDATE SKIP LOCKED` do PostgreSQL. Essa cláusula faz a consulta ignorar as linhas já bloqueadas por outra transação, de modo que uma mesma tarefa não pode ser reservada duas vezes (PostgreSQL Global Development Group, 2026). A reserva é confirmada imediatamente, antes do início da análise.

A tabela também permite a recuperação de falhas, conforme o Quadro 9.

**Quadro 9 — Tratamento de falhas no processamento das tarefas**

| Situação | Tratamento |
|---|---|
| Notificação recebida mais de uma vez | O identificador de entrega já registrado no evento impede a criação de outra tarefa. |
| *Worker* interrompido durante o processamento | A reserva tem prazo; ao expirar, a tarefa volta a ficar pendente e é retomada. |
| Falha temporária no GitHub ou no Gemini | A tarefa é reagendada, até um limite de tentativas; esgotado o limite, recebe o estado de erro. |
| PR atualizado ou fechado durante a análise | Antes de publicar, o *worker* confere o estado atual do PR e descarta o resultado obsoleto. |

Fonte: Elaborado pelo autor (2026)

Como as etapas que envolvem serviços externos podem ser repetidas após uma falha, elas são construídas de forma idempotente. Antes de criar um *commit* ou um comentário, o *worker* verifica se a publicação correspondente à mesma versão do código já foi realizada.

### 4.6.3 Publicação da documentação no *pull request*

Concluída a análise, o *worker* gera os arquivos JSON e Markdown do catálogo atualizado e os grava, por meio de um *commit*, na *branch* do próprio PR. O *commit* altera somente os arquivos do catálogo. Antes de gravá-lo, o *worker* confere se o PR continua aberto e se a *branch* ainda corresponde à versão analisada; se ela tiver avançado, a publicação é cancelada, pois o novo *commit* já terá gerado outra tarefa de análise.

Junto ao *commit*, o *worker* publica no PR um comentário curto, que resume as regras incluídas, alteradas ou removidas e aponta as unidades de código correspondentes. Quando a análise conclui que o PR não alterou regras de negócio, nenhum *commit* é feito, e o comentário apenas registra essa conclusão.

O *commit* de documentação gera, no GitHub, um novo evento de atualização do PR. Para evitar um ciclo de análises, a API identifica os eventos cujo último *commit* foi criado pela própria aplicação e alterou somente os arquivos do catálogo, e não cria tarefa para eles. *Commits* feitos por desenvolvedores continuam gerando nova análise.

### 4.6.4 Revisão e incorporação ao catálogo

A revisão ocorre na própria interface do GitHub. Na aba de arquivos alterados do PR, o revisor visualiza lado a lado as mudanças no código e as mudanças propostas na documentação. Se concordar com a proposta, aprova o PR; se discordar, pode editar diretamente os arquivos do catálogo na *branch* ou solicitar ajustes. O *merge* do PR representa a aceitação da versão final, incorporando à *branch* de referência o código e a documentação ao mesmo tempo.

O *merge* gera a tarefa de atualização do catálogo. O *worker* identifica o *commit* efetivamente incorporado à *branch* de referência, lê os arquivos do catálogo nessa versão e atualiza a cópia mantida no banco, registrando uma nova versão para cada regra modificada. Como o conteúdo é lido do repositório após o *merge*, o banco recebe a documentação final, incluindo as edições feitas pelo revisor. Um PR fechado sem *merge* não altera o catálogo.

## 4.7 Portal de consulta

O portal é uma aplicação React executada no navegador, que obtém os dados por meio da API. Ele é destinado exclusivamente à consulta e é composto por três telas, acessíveis após a autenticação.

O acesso ao portal exige login com a conta do GitHub, realizado pelo fluxo de autorização de usuário da própria GitHub App, de modo que a ferramenta não armazena senhas (GitHub, 2026). Após o login, a API consulta os repositórios da instalação aos quais a pessoa tem acesso no GitHub e restringe as consultas a esses repositórios. A autenticação vale apenas para o portal: a revisão e a edição da documentação continuam a ser feitas no GitHub.

A tela de **catálogo** lista as regras de negócio vigentes e permite pesquisá-las por texto e filtrá-las por módulo. Ao selecionar uma regra, o usuário visualiza sua descrição, a unidade de código que a implementa e um *link* para o trecho correspondente no GitHub, na versão do código em que a regra foi registrada.

A tela de **histórico** apresenta a linha do tempo de cada regra, com o texto anterior e o novo de cada alteração, o trecho de código que a motivou, nas duas versões, a data e o PR responsável, também acessível por *link*. A partir de um PR, é possível consultar todas as regras que ele modificou.

A tela de **grafo** exibe o grafo de dependências entre os módulos do sistema, com as relações de importação e de chamada como arestas, renderizado com a biblioteca Cytoscape.js. Ao selecionar um PR, o grafo destaca os módulos que contêm unidades alteradas e os módulos vizinhos.

O portal indica ainda a versão do catálogo exibida e a data de sua última atualização. Se um PR já tiver sido integrado, mas a tarefa de atualização correspondente ainda estiver pendente ou tiver falhado, o portal sinaliza essa defasagem. O Quadro 10 apresenta os *endpoints* da API utilizados pelo portal.

**Quadro 10 — *Endpoints* da API utilizados pelo portal**

| *Endpoint* | Retorno |
|---|---|
| `GET /auth/github` | Início do login, com redirecionamento para a autorização no GitHub. |
| `GET /auth/github/callback` | Conclusão do login e criação da sessão no portal. |
| `POST /auth/logout` | Encerramento da sessão. |
| `GET /api/repositorios` | Repositórios acessíveis à pessoa autenticada e versão do catálogo sincronizada de cada um. |
| `GET /api/repositorios/{repo}/regras` | Regras vigentes, com pesquisa por texto e filtro por módulo. |
| `GET /api/repositorios/{repo}/regras/{id}` | Dados completos de uma regra. |
| `GET /api/repositorios/{repo}/regras/{id}/historico` | Versões de uma regra, com o texto anterior e o novo e o PR de cada alteração. |
| `GET /api/repositorios/{repo}/prs/{numero}` | Regras alteradas por um PR. |
| `GET /api/repositorios/{repo}/grafo` | Módulos e dependências do grafo, com destaque opcional para os módulos alterados por um PR. |

Fonte: Elaborado pelo autor (2026)

---

## Referências a acrescentar

GITHUB. **Authenticating as a GitHub App installation**. 2026. Disponível em: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation. Acesso em: 4 nov. 2026.

GITHUB. **Authenticating with a GitHub App on behalf of a user**. 2026. Disponível em: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-with-a-github-app-on-behalf-of-a-user. Acesso em: 4 nov. 2026.

POSTGRESQL GLOBAL DEVELOPMENT GROUP. **SELECT: the locking clause**. 2026. Disponível em: https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE. Acesso em: 4 nov. 2026.

PYTHON SOFTWARE FOUNDATION. **ast — Abstract Syntax Trees**. 2026. Disponível em: https://docs.python.org/3/library/ast.html. Acesso em: 4 nov. 2026.

---

## Notas para o autor (não colar no TCC)

- **Numeração:** as Figuras 2 e 3 e os Quadros 3 a 10 continuam a numeração do Cap. 3 (Figura 1 e Quadro 2). Se o Cap. 2 ganhar quadros novos, renumere.
- **Duas citações "(GitHub, 2026)":** 4.6.1 e 4.7 citam documentos diferentes do GitHub no mesmo ano. Na ABNT, diferencie como (GitHub, 2026a) e (GitHub, 2026b) nas citações e nas referências.
- **Figura 3:** desenhar a partir do diagrama abaixo, que é o mesmo da seção 7 de `arquitetura-tcc.md`. As cardinalidades detalhadas, com a coluna que implementa cada relação, estão na tabela daquela seção.

  ```mermaid
  erDiagram
      USUARIO ||--o{ USUARIO_REPOSITORIO : "tem acesso"
      REPOSITORIO ||--o{ USUARIO_REPOSITORIO : "é acessado por"
      REPOSITORIO ||--o{ PULL_REQUEST : "recebe"
      REPOSITORIO ||--o{ EVENTO : "origina"
      PULL_REQUEST |o--o{ EVENTO : "é notificado por"
      EVENTO ||--o| TAREFA : "gera"
      PULL_REQUEST ||--o{ TAREFA : "é processado por"
      PULL_REQUEST ||--o{ ANALISE : "é analisado em"
      TAREFA |o--o| ANALISE : "produz"
      ANALISE ||--o{ TRECHO_CODIGO : "registra"
      ANALISE ||--o{ PROPOSTA : "contém"
      PROPOSTA ||--|{ PROPOSTA_TRECHO : "é sustentada por"
      TRECHO_CODIGO ||--o{ PROPOSTA_TRECHO : "sustenta"
      REGRA |o--o{ PROPOSTA : "é alvo de"
      REPOSITORIO ||--o{ REGRA : "documenta"
      REGRA ||--|{ VERSAO_REGRA : "possui"
      REGRA |o--o| VERSAO_REGRA : "aponta a versão atual"
      PULL_REQUEST ||--o{ VERSAO_REGRA : "incorpora"
      PROPOSTA |o--o| VERSAO_REGRA : "origina"
      MODULO ||--o{ VERSAO_REGRA : "contém a regra"
      REPOSITORIO ||--o{ MODULO : "contém"
      MODULO ||--o{ MODULO_DEPENDENCIA : "depende de (origem)"
      MODULO ||--o{ MODULO_DEPENDENCIA : "é dependência de (destino)"
  ```

- **Código de terceiros no banco:** os trechos de código analisados são copiados para o banco. Se o estudo usar repositório privado, mencione isso nas limitações, junto com a condição de uso de dados do nível gratuito do Gemini.
- **Grafo no nível de módulo:** decisão tomada para esta etapa (4.4.2 e 4.7). Se o desenvolvimento exigir armazenar ou exibir funções e métodos, acrescente a entidade de unidades de código ao Quadro 7 e à Figura 3 e volte a descrever o grafo do portal com unidades.
- **Figura 2:** desenhar a partir do diagrama abaixo.

  ```mermaid
  flowchart LR
      U["Portal React<br/>(navegador)"]
      GH["GitHub"]
      LLM["Gemini"]
      subgraph APP["Aplicação Python"]
          API["Processo web<br/>API FastAPI"]
          W["Worker<br/>+ módulo de análise (ast)"]
      end
      DB[("PostgreSQL<br/>tarefas · análises · catálogo")]

      U <-->|"consulta"| API
      GH -->|"1. webhook"| API
      API -->|"2. grava tarefa"| DB
      DB -->|"3. reserva tarefa"| W
      W <-->|"4. interpreta mudança"| LLM
      W -->|"5. commit da doc no PR"| GH
      W -->|"6. após merge, atualiza catálogo"| DB
      API <-->|"lê catálogo"| DB
  ```

- **Decisões que este texto propõe, mas que ainda não estavam fechadas** (confirme ou ajuste):
  - Identificador estável independente da posição, com vínculo pelo nome qualificado (4.3).
  - Contexto enviado ao modelo: unidade nas duas versões, regras vinculadas e vizinhas de um nível no grafo (4.5.2).
  - Comparação de AST sem posições, para ignorar formatação (4.5.1).
  - Geração do catálogo inicial unidade por unidade (4.4.3). Ainda não define se testes ficam fora da varredura.
  - *Endpoints* do Quadro 10 e as três telas do portal (4.7). Os caminhos de login (`/auth/github`, `/auth/github/callback`, `/auth/logout`) são propostos aqui e ainda não constam em `arquitetura-tcc.md`.
  - Sem *commit* quando o PR não altera regras, apenas comentário (4.6.3).
- **Escrito conforme a arquitetura revisada, com conflitos pendentes em relação ao Cap. 3:** a revisão acontece no PR, e não no portal; a proposta é um *commit* na *branch*, e não só um comentário; e ainda falta definir como a base inicial é revisada. A seção 4.4 termina na geração dos arquivos de propósito, sem dizer como a base é revisada.
- **Hospedagem (Render) no Quadro 5:** o plano do *worker* e o provedor do banco ainda estão em aberto. Se preferir, tire a linha até isso ser decidido.
- **Gemini 3.6 Flash:** confirme o nome e a versão do modelo na época da entrega.
- **Referências:** são documentações online; confira a data de acesso ao incluí-las.
