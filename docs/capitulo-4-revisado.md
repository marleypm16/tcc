# 4. DESENVOLVIMENTO DA FERRAMENTA

Este capítulo descreve a construção da ferramenta cujas etapas foram apresentadas na seção 3.2. Inicialmente, apresenta-se a arquitetura da aplicação e as tecnologias empregadas. Em seguida, descrevem-se o modelo adotado para o catálogo de regras de negócio, o modelo de dados da aplicação e a implementação de cada etapa: a geração da base de conhecimento, a análise incremental por *pull request*, a integração com o GitHub e a revisão das propostas, e o portal.

## 4.1 Arquitetura

A aplicação adota o estilo de monólito modular com processamento assíncrono. Ela é composta por dois processos, um processo web e um processo de processamento em segundo plano (*worker*), mantidos no mesmo repositório, escritos na mesma linguagem e apoiados sobre um único banco de dados. Os dois processos compartilham os mesmos módulos de código, mas têm pontos de entrada distintos e responsabilidades separadas, apresentadas no Quadro 3.

**Quadro 3 — Processos da aplicação**

| Processo | Responsabilidade |
|---|---|
| Processo web (API) | Receber e validar as notificações enviadas pelo GitHub, registrar os eventos e as tarefas correspondentes, autenticar as pessoas que acessam o portal, disponibilizar os dados consultados por elas e registrar as decisões de revisão. |
| *Worker* | Reservar as tarefas pendentes, gerar a base inicial, obter as versões do código, executar a análise estática, consultar o modelo de linguagem, publicar o resultado no PR e incorporar ao catálogo as propostas aprovadas após o *merge*. |

Fonte: Elaborado pelo autor (2026)

### 4.1.1 Componentes

A Figura 2 apresenta os componentes da solução e as relações entre eles. Além dos dois processos da aplicação, participam da arquitetura o banco de dados PostgreSQL, o portal executado no navegador e dois serviços externos: o GitHub, que hospeda os repositórios analisados, e o modelo de linguagem Gemini, responsável pela interpretação das mudanças.

**[Inserir Figura 2 — Arquitetura da ferramenta]**

Fonte: Elaborado pelo autor (2026)

O processo web e o *worker* não se comunicam diretamente. O banco de dados é o ponto de encontro entre eles: o processo web registra as tarefas a executar, e o *worker* as retira do banco, processa e grava os resultados. A própria fila de tarefas é mantida em uma tabela do banco, o que permite registrar um evento e a tarefa correspondente em uma mesma transação. Assim, uma tarefa recebida durante uma parada do *worker* permanece registrada e é processada quando ele volta a operar. O banco também mantém a versão oficial do catálogo de regras de negócio.

### 4.1.2 Fluxos de funcionamento

A aplicação opera em dois fluxos, precedidos pela geração da base inicial, que ocorre quando a GitHub App é instalada em um repositório (seção 4.4). O primeiro fluxo é iniciado por uma pessoa que consulta a documentação ou revisa as propostas da ferramenta:

1. A pessoa abre o portal no navegador e se autentica com sua conta do GitHub.
2. O portal solicita à API o catálogo, o histórico, o grafo de dependências ou as propostas de um PR.
3. A API verifica se a pessoa tem acesso ao repositório, consulta o banco de dados e devolve os dados no formato JSON.
4. Na revisão, a pessoa com permissão de escrita no repositório aprova, edita ou rejeita cada proposta. A API registra a decisão e uma tarefa de atualização do PR em uma mesma transação.

O segundo fluxo, automático, é iniciado pelo GitHub sempre que um PR é aberto, atualizado ou integrado:

1. O GitHub notifica a API por meio de um *webhook*. A API valida a notificação, registra o evento e cria uma tarefa, respondendo em seguida.
2. O *worker* reserva a tarefa, obtém as duas versões do código e executa a análise estática.
3. O *worker* envia ao modelo de linguagem as unidades alteradas e o contexto relacionado, valida a resposta e grava as propostas de atualização no banco.
4. O *worker* publica no PR um comentário que resume as propostas e aponta para a tela de revisão no portal, além de um status que indica se a revisão da documentação está pendente.
5. O revisor examina o código no GitHub e as propostas no portal e, ao concluir, realiza o *merge* do PR.
6. O *merge* gera uma nova notificação, e o *worker* incorpora ao catálogo as propostas aprovadas, que passam a ser exibidas pelo portal.

### 4.1.3 Organização em módulos

Internamente, o código da aplicação é dividido em módulos com responsabilidades delimitadas, apresentados no Quadro 4. O módulo de análise não depende do GitHub, do banco de dados nem do modelo de linguagem: recebe versões de código e a documentação existente e devolve resultados estruturados. O acesso aos serviços externos fica concentrado em adaptadores, coordenados pelo módulo de processamento.

**Quadro 4 — Módulos da aplicação**

| Módulo | Responsabilidade |
|---|---|
| API | Recebimento dos *webhooks*, autenticação das pessoas no portal e *endpoints* de consulta e de revisão. |
| Processamento | Reserva das tarefas, controle das etapas, novas tentativas e recuperação de falhas. |
| Análise | Extração da AST, comparação de versões, dependências e seleção de contexto. |
| IA | Preparação das solicitações, comunicação com o Gemini e validação das respostas. |
| Documentação | Propostas, decisões de revisão, incorporação após o *merge* e histórico das versões. |
| GitHub | Validação dos eventos, autenticação, obtenção das versões, abertura do PR de ativação e publicação de comentários e status. |
| Persistência | Modelos de dados, acesso ao banco e migrações, compartilhados pelos dois processos. |
| Portal | Interface de consulta do catálogo, do histórico e do grafo e de revisão das propostas. |

Fonte: Elaborado pelo autor (2026)

## 4.2 Tecnologias utilizadas

O Quadro 5 apresenta as tecnologias empregadas na construção da ferramenta e o papel de cada uma.

**Quadro 5 — Tecnologias utilizadas**

| Parte da solução | Tecnologia | Papel na ferramenta |
|---|---|---|
| Linguagem | Python | Implementação da API, do *worker* e do módulo de análise. A versão é fixada no ambiente para permitir a reprodução dos experimentos. |
| API | FastAPI | Recebimento dos *webhooks* e atendimento às consultas e às decisões registradas no portal. |
| Análise estática | Módulo `ast` da biblioteca padrão do Python | Conversão do código-fonte em AST, extração da estrutura e comparação entre versões. |
| Banco de dados | PostgreSQL | Armazenamento da versão oficial do catálogo e de seu histórico, das propostas, das decisões de revisão, dos eventos, das tarefas e das análises. |
| Acesso ao banco | SQLAlchemy | Mapeamento dos dados e migrações, compartilhados pela API e pelo *worker*. |
| Integração com o GitHub | GitHub App, *webhooks* e API REST do GitHub | Notificação dos eventos de instalação e de PR, obtenção do código, abertura do PR de ativação, publicação de comentários e status e autenticação das pessoas no portal. |
| Modelo de linguagem | Gemini 3.6 Flash, por meio da Gemini API | Interpretação das mudanças e redação das regras de negócio em linguagem natural. |
| Portal | React, com Vite | Construção da interface de consulta e de revisão executada no navegador. |
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

A versão oficial do catálogo é mantida no banco de dados da ferramenta. Para cada regra, o banco armazena todas as suas versões, com o texto anterior e o novo, o PR e o *commit* correspondentes, a decisão de revisão que a originou e a data da incorporação. Uma nova versão só é criada quando uma proposta aprovada é incorporada pelo *merge* do PR correspondente, de modo que o histórico de cada regra acompanha o histórico de integração do código.

O banco também registra os dados operacionais da ferramenta: os eventos recebidos, as tarefas e suas etapas, as análises realizadas, as propostas originais geradas pelo modelo e as decisões dos revisores. As propostas originais são preservadas sem alterações, separadas das decisões e das versões incorporadas, o que permite comparar o texto sugerido pelo modelo com o texto aceito. No repositório analisado, a ferramenta mantém apenas um arquivo de configuração, adicionado na ativação (seção 4.4.4).

### 4.3.2 Modelo de dados

O banco de dados é organizado em catorze entidades, apresentadas no Quadro 7, e em três tabelas associativas, que representam as relações de muitos para muitos entre usuários e repositórios, entre módulos e entre propostas e trechos de código.

**Quadro 7 — Entidades do modelo de dados**

| Entidade | Conteúdo |
|---|---|
| Usuário | Pessoa autenticada no portal, identificada pela sua conta do GitHub. |
| Sessão | Sessão de uma pessoa no portal, com prazo de validade e o *token* de acesso ao GitHub armazenado de forma cifrada. |
| Repositório | Repositório acompanhado, com a instalação da GitHub App a que pertence, a situação da ativação e a versão atual do catálogo. |
| Módulo | Módulo Python do repositório na versão vigente do catálogo. |
| *Pull request* | PR do repositório, com seu estado e as versões de código envolvidas. |
| Evento | Notificação recebida do GitHub, identificada pelo seu identificador de entrega. |
| Tarefa | Operação a ser executada pelo *worker*, originada de um evento ou de uma decisão de revisão. |
| Etapa da tarefa | Registro de cada etapa executada em uma tarefa, com início, fim, resultado e erro. |
| Análise | Execução da análise incremental sobre uma versão do PR, com a configuração do modelo de linguagem, o consumo registrado e as publicações realizadas no PR. |
| Trecho de código | Cópia de uma unidade de código no momento da análise, nas versões base e nova, indicando se a unidade foi alterada ou apenas enviada como contexto. |
| Proposta | Atualização de regra sugerida pelo modelo de linguagem, preservada sem alterações. |
| Decisão | Aprovação, edição ou rejeição de uma proposta por um revisor, com o autor, a data e o texto final ou o motivo. |
| Regra | Identidade estável de uma regra de negócio no catálogo. |
| Versão da regra | Conteúdo da regra incorporado por um *merge*, com os atributos do Quadro 6. |

Fonte: Elaborado pelo autor (2026)

A Figura 3 apresenta as relações entre as entidades e suas cardinalidades.

**[Inserir Figura 3 — Modelo de dados]**

Fonte: Elaborado pelo autor (2026)

Um repositório reúne vários PRs, módulos e regras. Cada usuário pode acessar vários repositórios, e cada repositório pode ser acessado por vários usuários. Um PR recebe vários eventos, e cada evento gera no máximo uma tarefa, pois alguns eventos, como o fechamento de um PR sem *merge*, são apenas registrados. As tarefas originadas no portal, como a atualização do status do PR após uma decisão, não têm evento associado. Cada tarefa registra as etapas executadas. Um PR pode ser analisado várias vezes, uma para cada nova versão do código, e cada análise contém zero ou mais propostas; não há propostas quando o modelo conclui que o PR não alterou regras de negócio.

Cada análise registra os trechos de código examinados, isto é, as unidades alteradas e as unidades de contexto, exatamente como foram enviadas ao modelo. Cada proposta cita um ou mais desses trechos, e um mesmo trecho pode sustentar mais de uma proposta, relação registrada em uma tabela associativa. Esse registro permite apresentar, no histórico de uma regra, o código anterior e o novo que motivaram a alteração e reproduzir cada interpretação na avaliação sem consultar novamente o GitHub.

Cada proposta recebe zero ou mais decisões, e a mais recente define sua situação. Quando o revisor solicita uma nova interpretação, a proposta gerada substitui a anterior e mantém a referência a ela. Uma regra possui uma ou mais versões, e cada versão é incorporada por um PR e pertence a um módulo. A versão fica vinculada à proposta e à decisão que lhe deram origem, o que permite comparar o texto sugerido pelo modelo com o texto incorporado após a revisão; regras incluídas manualmente pelo revisor não têm proposta associada. Essa separação permite à avaliação medir a saída automática antes da intervenção humana. As dependências de importação e de chamada entre módulos são registradas em uma tabela associativa, que liga cada módulo de origem ao módulo de destino.

## 4.4 Geração da base de conhecimento

A geração da base é executada uma única vez por repositório, sobre uma versão de referência do código. Ela é iniciada automaticamente quando a GitHub App é instalada no repositório, tomando como referência a versão atual da *branch* principal, e também pode ser iniciada por comando de terminal. É composta por quatro passos: a extração da estrutura, a construção do grafo de dependências, a geração do catálogo inicial e a revisão e ativação da base.

### 4.4.1 Extração da estrutura

Cada arquivo Python do repositório é convertido em AST por meio da função `ast.parse`. Em seguida, a árvore é percorrida, e a ferramenta registra, para cada arquivo, o módulo correspondente, as classes, as funções e os métodos definidos, as constantes declaradas no nível do módulo, as importações e as chamadas de funções e métodos realizadas no corpo de cada unidade. Cada unidade de código é identificada pelo seu nome qualificado, formado pelo caminho do módulo, pela classe, quando houver, e pelo nome da função ou do método.

Os arquivos de teste, identificados por critérios de nome e de diretório definidos na configuração do repositório, não são analisados, pois alterações restritas a testes não constituem mudança de regra de negócio (seção 3.2.2). Quando um arquivo não pode ser convertido em AST, por utilizar uma sintaxe não suportada pela versão do interpretador, o arquivo é registrado como não analisado. Essa ocorrência é tratada como análise incompleta, e não como ausência de regras de negócio.

### 4.4.2 Construção do grafo de dependências

A partir da estrutura extraída, a ferramenta constrói um grafo direcionado de dependências em dois níveis. No nível das unidades de código, os nós são as funções e os métodos, e as arestas são as chamadas de uma unidade por outra; esse grafo é calculado a cada análise e utilizado na seleção do contexto (seção 4.5.2), sem ser armazenado. No nível de módulo, os nós são os módulos do repositório, e as arestas representam a importação de um módulo por outro ou a existência de chamadas de unidades de um módulo para unidades de outro; esse é o grafo armazenado no banco e exibido no portal. As importações são resolvidas para os módulos do próprio repositório; importações de bibliotecas externas não geram arestas. As chamadas são resolvidas estaticamente sempre que o nome chamado puder ser associado a uma unidade conhecida. As chamadas que não podem ser resolvidas sem executar o código, como as que dependem do tipo de um objeto definido em tempo de execução, são registradas como não resolvidas.

### 4.4.3 Geração do catálogo inicial

Para gerar o catálogo inicial, a ferramenta envia ao modelo de linguagem, unidade por unidade, o código da unidade, as constantes que ela utiliza e as unidades que ela chama diretamente. O modelo indica se a unidade implementa alguma regra de negócio, segundo a definição operacional da seção 3.2.2, e, em caso positivo, redige o título e a descrição de cada regra. Unidades sem regras de negócio, como funções utilitárias, não geram entradas no catálogo.

A ferramenta completa os atributos do Quadro 6 a partir da estrutura extraída e registra cada regra identificada como uma proposta de inclusão. O identificador definitivo é atribuído à regra quando ela é incorporada ao catálogo.

### 4.4.4 Revisão e ativação da base

Concluída a geração, a ferramenta abre um PR na *branch* principal do repositório, chamado PR de ativação. Esse PR adiciona o arquivo de configuração da ferramenta, `.lastro.yml`, e traz, na descrição, o resumo do catálogo inicial e o *link* para revisá-lo no portal. As regras da base são tratadas como propostas desse PR e revisadas da mesma forma que as de qualquer outro PR (seção 4.6.4).

O *merge* do PR de ativação torna a base vigente. Enquanto ele não ocorre, os demais PRs do repositório não são analisados, e a ferramenta apenas comenta neles que a base ainda está em revisão. Se o PR de ativação for fechado sem *merge*, o repositório permanece inativo; a reativação pode ser solicitada no portal, por quem tem permissão de escrita no repositório, ou por comando de terminal, e gera uma nova base e um novo PR de ativação.

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
- as unidades vizinhas no grafo de dependências, limitadas às ligadas diretamente à unidade alterada, isto é, as que a chamam e as que são chamadas por ela, acompanhadas das regras a elas vinculadas.

As unidades vizinhas indicam onde a mudança pode ter impacto, mas a ferramenta não as trata como alteradas: elas apenas compõem o contexto enviado ao modelo. As unidades alteradas e as de contexto são registradas no banco como trechos de código da análise, conforme a seção 4.3.2.

### 4.5.3 Interpretação pelo modelo de linguagem

A comunicação com o Gemini é feita por um adaptador, que concentra a montagem das solicitações, o tratamento de erros e a leitura das respostas. A instrução enviada ao modelo (*prompt*) é composta por três partes:

1. **Instruções:** o papel atribuído ao modelo e a definição operacional de mudança de regra de negócio, incluindo as alterações que não devem ser consideradas, como renomeação e refatoração sem mudança de comportamento;
2. **Contexto:** o resultado da comparação e o contexto selecionado no passo anterior;
3. **Formato de saída:** a estrutura em JSON que a resposta deve seguir.

A resposta do modelo informa, para o PR analisado, se houve mudança de regra de negócio e, para cada mudança, a regra afetada, o tipo de atualização (inclusão, alteração ou remoção), o texto proposto, a justificativa e as referências às unidades de código que sustentam a proposta.

Quando o revisor rejeita uma proposta e solicita uma nova interpretação (seção 4.6.4), a solicitação ao modelo inclui, além do contexto original, a proposta rejeitada e o motivo informado pelo revisor.

### 4.5.4 Validação da resposta

Antes de registrar as propostas, a ferramenta verifica se a resposta segue o formato esperado, se os identificadores de regras citados existem no catálogo e se as unidades de código referenciadas existem na versão analisada. Respostas que não passam nessa verificação são solicitadas novamente, até um limite de tentativas. Essa validação garante a consistência estrutural da resposta, mas não comprova a corretude do texto proposto, que continua sujeita à revisão humana.

Cada execução registra no banco o modelo utilizado, a versão do *prompt*, a quantidade de *tokens* consumidos e o tempo de processamento, dados utilizados na dimensão de custo da avaliação.

## 4.6 Integração com o GitHub e revisão

### 4.6.1 Recebimento dos eventos

A integração com o GitHub é realizada por meio de uma GitHub App instalada nos repositórios acompanhados. A aplicação tem permissão de leitura e escrita sobre o conteúdo do repositório, usando a escrita apenas para criar o PR de ativação; de leitura e escrita sobre os PRs, para consultá-los, abrir o PR de ativação e publicar comentários; e de escrita sobre os status de *commit*, para indicar a situação da revisão. Para atuar em um repositório, o *worker* obtém um *token* de instalação, autenticando-se com a chave privada da aplicação (GitHub, 2026a).

O GitHub notifica a API a cada evento de instalação da aplicação e de PR por meio de um *webhook*. Ao receber uma notificação, a API verifica sua assinatura, calculada pelo GitHub com uma chave secreta compartilhada, o que garante que a notificação foi de fato enviada por ele. O Quadro 8 apresenta os eventos acompanhados e o tratamento dado a cada um.

**Quadro 8 — Eventos acompanhados**

| Evento | Tratamento |
|---|---|
| Instalação da GitHub App em um repositório (`installation` ou `installation_repositories`) | Cria uma tarefa de geração da base inicial. |
| PR aberto (`opened`) ou reaberto (`reopened`) | Cria uma tarefa de análise do PR. |
| PR atualizado (`synchronize`) | Cria uma tarefa de análise da nova versão do PR. |
| PR fechado com *merge* (`closed`, com `merged` verdadeiro) | Cria uma tarefa de incorporação ao catálogo. |
| PR fechado sem *merge* (`closed`, com `merged` falso) | Registra o encerramento e descarta as tarefas pendentes e as decisões tomadas, sem alterar o catálogo. |

Fonte: Elaborado pelo autor (2026)

O registro do evento e a criação da tarefa ocorrem em uma única transação do banco de dados, e a API só responde ao GitHub depois de confirmada essa transação. O processamento pesado, como a análise estática e as chamadas ao modelo de linguagem, não é executado durante o recebimento, de modo que a resposta é devolvida em poucos milissegundos. Cada notificação do GitHub traz um identificador de entrega único; como esse identificador é registrado no evento com restrição de unicidade, e cada evento gera no máximo uma tarefa, uma notificação recebida mais de uma vez não gera uma segunda tarefa.

### 4.6.2 Fila de tarefas

A fila de tarefas é a tabela `tarefas` do banco de dados. Cada tarefa registra seu tipo, o evento que a originou, quando houver, o PR, os *commits* envolvidos, o estado, o número de tentativas, os horários de início e de conclusão e, quando houver, o erro ocorrido. Os tipos de tarefa são a geração da base inicial, a análise do PR, a nova interpretação de uma proposta rejeitada, a atualização do status do PR e a incorporação ao catálogo após o *merge*. Os estados possíveis são pendente, processando, concluída, erro e descartada. As etapas executadas em cada tarefa, como a análise, as chamadas ao modelo e as publicações no PR, são registradas em uma tabela própria, o que permite acompanhar o processamento sem consultar os registros do servidor.

O *worker* consulta periodicamente a tabela e reserva a próxima tarefa pendente por meio de um único comando de atualização, que utiliza a cláusula `FOR UPDATE SKIP LOCKED` do PostgreSQL. Essa cláusula faz a consulta ignorar as linhas já bloqueadas por outra transação, de modo que uma mesma tarefa não pode ser reservada duas vezes (PostgreSQL Global Development Group, 2026). A reserva é confirmada imediatamente, antes do início da análise.

A tabela também permite a recuperação de falhas, conforme o Quadro 9.

**Quadro 9 — Tratamento de falhas no processamento das tarefas**

| Situação | Tratamento |
|---|---|
| Notificação recebida mais de uma vez | O identificador de entrega já registrado no evento impede a criação de outra tarefa. |
| *Worker* interrompido durante o processamento | A reserva tem prazo, renovado enquanto o *worker* está ativo; ao expirar, a tarefa volta a ficar pendente e é retomada. |
| Falha temporária no GitHub ou no Gemini | A tarefa é reagendada com intervalos crescentes, até um limite de tentativas; esgotado o limite, recebe o estado de erro. |
| PR atualizado ou fechado durante a análise | Antes de publicar, o *worker* confere o estado atual do PR e não publica o resultado obsoleto. |

Fonte: Elaborado pelo autor (2026)

Como as etapas que envolvem serviços externos podem ser repetidas após uma falha, elas são construídas de forma idempotente. Antes de publicar um comentário ou um status, o *worker* verifica se a publicação correspondente à mesma análise e à mesma versão do código já foi realizada.

### 4.6.3 Publicação do resultado no *pull request*

Concluída a análise, o *worker* grava as propostas validadas no banco e publica no PR um comentário curto, que resume as regras incluídas, alteradas ou removidas, aponta as unidades de código correspondentes e traz o *link* para a tela de revisão do PR no portal. Em novas análises do mesmo PR, o comentário existente é atualizado, em vez de ser publicado outro. Quando a análise conclui que o PR não alterou regras de negócio, nenhuma proposta é criada, e o comentário apenas registra essa conclusão.

Além do comentário, o *worker* publica na versão analisada um status de *commit*, exibido pelo GitHub junto às verificações do PR. O status fica pendente enquanto houver propostas não revisadas e passa a indicar sucesso quando todas forem decididas ou quando não houver mudança de regra; em caso de falha na análise, indica erro. O responsável pelo repositório pode tornar esse status obrigatório, de modo que o *merge* só seja liberado após a revisão da documentação (GitHub, 2026c).

Antes de publicar, o *worker* confere se o PR continua aberto e se a versão analisada ainda é a mais recente; caso contrário, o resultado é registrado, mas não publicado, pois o novo *commit* já terá gerado outra tarefa de análise. A ferramenta não grava arquivos na *branch* do PR, o que permite tratar da mesma forma os PRs originados de *forks* do repositório.

### 4.6.4 Revisão no portal e incorporação ao catálogo

A revisão das propostas ocorre no portal (seção 4.7), acessado pelo *link* publicado no PR. Para cada proposta, o revisor visualiza o texto atual da regra, o texto proposto, a justificativa do modelo e o código da unidade nas duas versões, e pode aprová-la, editá-la antes de aprovar ou rejeitá-la. Ao rejeitar, o revisor indica se a proposta deve ser descartada, por não corresponder a uma mudança de regra de negócio, ou refeita; nesse caso, informa o motivo, e uma nova interpretação é solicitada ao modelo, até um limite de três vezes por proposta. Somente pessoas com permissão de escrita no repositório no GitHub podem registrar decisões. Cada decisão é registrada com seu autor, sua data e o texto final ou o motivo, e atualiza o status publicado no PR.

A aprovação no portal não altera o catálogo vigente: uma proposta aprovada só é incorporada quando o PR é integrado à *branch* principal. O *merge* representa, assim, a aceitação conjunta do código e da documentação aprovada. Se o PR receber novos *commits* durante a revisão, a ferramenta realiza nova análise e mantém as decisões tomadas sobre as unidades cujo código não mudou; as demais propostas voltam a aguardar revisão, acompanhadas da decisão anterior como referência.

O *merge* gera a tarefa de incorporação ao catálogo. O *worker* identifica o *commit* efetivamente incorporado à *branch* principal, considerando as formas de *merge* oferecidas pelo GitHub, e registra uma nova versão para cada regra afetada por uma proposta aprovada, com o texto editado pelo revisor, quando houver. *Merges* processados fora de ordem acrescentam versões ao histórico, mas não fazem o catálogo atual retroceder. Propostas ainda pendentes no momento do *merge* continuam disponíveis para revisão e, quando aprovadas, são incorporadas imediatamente; enquanto isso, o portal sinaliza que o catálogo está defasado em relação ao código. Um PR fechado sem *merge* não altera o catálogo, e as decisões tomadas sobre suas propostas são descartadas.

## 4.7 Portal

O portal é uma aplicação React executada no navegador, que obtém os dados por meio da API. É composto por quatro telas, acessíveis após a autenticação: catálogo, histórico, grafo e revisão.

O acesso ao portal exige login com a conta do GitHub, realizado pelo fluxo de autorização de usuário da própria GitHub App, de modo que a ferramenta não armazena senhas (GitHub, 2026b). Após o login, a API consulta os repositórios da instalação aos quais a pessoa tem acesso no GitHub e restringe as consultas a esses repositórios; essa permissão é verificada novamente a cada hora. A sessão é mantida por um *cookie* protegido, válido por oito horas, e o *token* de acesso ao GitHub permanece cifrado no servidor, sem ser enviado ao navegador. Somente as pessoas com permissão de escrita no repositório podem registrar decisões na tela de revisão; as demais a acessam apenas para leitura.

A tela de **catálogo** lista as regras de negócio vigentes e permite pesquisá-las por texto e filtrá-las por módulo. Ao selecionar uma regra, o usuário visualiza sua descrição, a unidade de código que a implementa e um *link* para o trecho correspondente no GitHub, na versão do código em que a regra foi registrada.

A tela de **histórico** apresenta a linha do tempo de cada regra, com o texto anterior e o novo de cada alteração, o trecho de código que a motivou, nas duas versões, a data, o revisor que aprovou a alteração e o PR responsável, também acessível por *link*. A partir de um PR, é possível consultar todas as regras que ele modificou.

A tela de **grafo** exibe o grafo de dependências entre os módulos do sistema, com as relações de importação e de chamada como arestas, renderizado com a biblioteca Cytoscape.js. Ao selecionar um PR, o grafo destaca os módulos que contêm unidades alteradas e os módulos vizinhos.

A tela de **revisão** reúne as propostas de um PR, separadas do catálogo vigente, com a situação de cada uma: pendente, aprovada, descartada ou em nova interpretação. Para cada proposta, apresenta lado a lado o texto atual e o proposto e o código da unidade nas duas versões, além das ações de decisão descritas na seção 4.6.4. É também nessa tela que o catálogo inicial é revisado, por meio das propostas do PR de ativação, com a opção de aprovar todas de uma vez. Quando duas pessoas decidem a mesma proposta ao mesmo tempo, apenas a primeira decisão é aceita, e a tela da segunda é atualizada.

O portal indica ainda a versão do catálogo exibida e a data de sua última atualização. Se um PR já tiver sido integrado, mas a tarefa de incorporação correspondente ainda estiver pendente ou tiver falhado, ou se ainda houver propostas pendentes, o portal sinaliza essa defasagem. O Quadro 10 apresenta os *endpoints* da API utilizados pelo portal.

**Quadro 10 — *Endpoints* da API utilizados pelo portal**

| *Endpoint* | Retorno |
|---|---|
| `GET /auth/github` | Início do login, com redirecionamento para a autorização no GitHub. |
| `GET /auth/github/callback` | Conclusão do login e criação da sessão no portal. |
| `POST /auth/logout` | Encerramento da sessão. |
| `GET /api/repositorios` | Repositórios acessíveis à pessoa autenticada, com a situação da ativação e a versão atual do catálogo de cada um. |
| `GET /api/repositorios/{repo}/regras` | Regras vigentes, com pesquisa por texto e filtro por módulo. |
| `GET /api/repositorios/{repo}/regras/{id}` | Dados completos de uma regra. |
| `GET /api/repositorios/{repo}/regras/{id}/historico` | Versões de uma regra, com o texto anterior e o novo, o PR e o revisor de cada alteração. |
| `GET /api/repositorios/{repo}/prs/{numero}` | Regras alteradas por um PR. |
| `GET /api/repositorios/{repo}/prs/{numero}/propostas` | Propostas de um PR, com a situação e as decisões de cada uma. |
| `POST /api/repositorios/{repo}/propostas/{id}/aprovar` | Aprovação de uma proposta, com o texto editado, quando houver. |
| `POST /api/repositorios/{repo}/prs/{numero}/propostas/aprovar` | Aprovação de todas as propostas pendentes de um PR. |
| `POST /api/repositorios/{repo}/propostas/{id}/rejeitar` | Rejeição de uma proposta, com a indicação de descarte ou de nova interpretação e o motivo. |
| `POST /api/repositorios/{repo}/ativacao` | Solicitação de reativação de um repositório inativo, com a geração de uma nova base. |
| `GET /api/repositorios/{repo}/grafo` | Módulos e dependências do grafo, com destaque opcional para os módulos alterados por um PR. |

Fonte: Elaborado pelo autor (2026)

---

## Referências a acrescentar

GITHUB. **Authenticating as a GitHub App installation**. 2026a. Disponível em: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation. Acesso em: 4 nov. 2026.

GITHUB. **Authenticating with a GitHub App on behalf of a user**. 2026b. Disponível em: https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-with-a-github-app-on-behalf-of-a-user. Acesso em: 4 nov. 2026.

GITHUB. **About protected branches**. 2026c. Disponível em: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches. Acesso em: 10 nov. 2026.

POSTGRESQL GLOBAL DEVELOPMENT GROUP. **SELECT: the locking clause**. 2026. Disponível em: https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE. Acesso em: 4 nov. 2026.

PYTHON SOFTWARE FOUNDATION. **ast — Abstract Syntax Trees**. 2026. Disponível em: https://docs.python.org/3/library/ast.html. Acesso em: 4 nov. 2026.

---

## Notas para o autor (não colar no TCC)

- **Revisão de 10/11/2026:** o capítulo segue `docs/requisitos.md` v0.5 (decisões D1+D2, D4, D6, D7, D10, D12, D16). A revisão saiu do GitHub e foi para o portal, e o banco passou a ser a fonte oficial do catálogo. `arquitetura-tcc.md`, o Mapa, os Caps. 1 e 3 e o resumo foram alinhados no mesmo dia.
- **Numeração:** as Figuras 2 e 3 e os Quadros 3 a 10 continuam a numeração do Cap. 3 (Figura 1 e Quadro 2). Se o Cap. 2 ganhar quadros novos, renumere.
- **Citações do GitHub:** já diferenciadas como 2026a (instalação, 4.6.1), 2026b (login de usuário, 4.7) e 2026c (branches protegidas, 4.6.3). Confira a data de acesso de 2026c.
- **Figura 3:** desenhar a partir do diagrama abaixo, que é o mesmo da seção 7 de `arquitetura-tcc.md`. As cardinalidades detalhadas, com a coluna que implementa cada relação, estão na tabela daquela seção.

  ```mermaid
  erDiagram
      USUARIO ||--o{ USUARIO_REPOSITORIO : "tem acesso"
      REPOSITORIO ||--o{ USUARIO_REPOSITORIO : "é acessado por"
      USUARIO ||--o{ SESSAO : "abre"
      REPOSITORIO ||--o{ PULL_REQUEST : "recebe"
      REPOSITORIO |o--o| PULL_REQUEST : "é ativado por"
      REPOSITORIO ||--o{ EVENTO : "origina"
      PULL_REQUEST |o--o{ EVENTO : "é notificado por"
      EVENTO |o--o| TAREFA : "gera"
      REPOSITORIO ||--o{ TAREFA : "tem"
      PULL_REQUEST |o--o{ TAREFA : "é processado por"
      PROPOSTA |o--o{ TAREFA : "é refeita por"
      TAREFA ||--o{ ETAPA_TAREFA : "registra"
      PULL_REQUEST |o--o{ ANALISE : "é analisado em"
      TAREFA |o--o| ANALISE : "produz"
      ANALISE ||--o{ TRECHO_CODIGO : "registra"
      ANALISE ||--o{ PROPOSTA : "contém"
      PROPOSTA |o--o| PROPOSTA : "substitui"
      PROPOSTA ||--|{ PROPOSTA_TRECHO : "é sustentada por"
      TRECHO_CODIGO ||--o{ PROPOSTA_TRECHO : "sustenta"
      PROPOSTA ||--o{ DECISAO : "recebe"
      USUARIO ||--o{ DECISAO : "registra"
      REGRA |o--o{ PROPOSTA : "é alvo de"
      REPOSITORIO ||--o{ REGRA : "documenta"
      REGRA ||--|{ VERSAO_REGRA : "possui"
      REGRA |o--o| VERSAO_REGRA : "aponta a versão atual"
      PULL_REQUEST ||--o{ VERSAO_REGRA : "incorpora"
      PROPOSTA |o--o| VERSAO_REGRA : "origina"
      DECISAO |o--o| VERSAO_REGRA : "aprova"
      MODULO ||--o{ VERSAO_REGRA : "contém a regra"
      REPOSITORIO ||--o{ MODULO : "contém"
      MODULO ||--o{ MODULO_DEPENDENCIA : "depende de (origem)"
      MODULO ||--o{ MODULO_DEPENDENCIA : "é dependência de (destino)"
  ```

- **Tarefa sem evento:** a relação Evento → Tarefa passou a ser opcional (`|o--o|`), porque as tarefas criadas por decisões no portal e pelo terminal não têm evento.
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
      DB[("PostgreSQL<br/>catálogo oficial · propostas · tarefas")]

      U <-->|"consulta e revisão"| API
      GH -->|"1. webhook"| API
      API -->|"2. grava tarefa / decisão"| DB
      DB -->|"3. reserva tarefa"| W
      W <-->|"4. interpreta mudança"| LLM
      W -->|"5. comentário e status no PR"| GH
      W -->|"6. após merge, incorpora aprovadas"| DB
      API <-->|"lê catálogo e propostas"| DB
  ```

- **Decisões que este texto adota e que ainda não estão na arquitetura** (confirme ou ajuste):
  - Identificador estável independente da posição, atribuído na incorporação (4.3 e 4.4.3). O formato do identificador continua em aberto (D5).
  - Contexto de um nível no grafo, fixo (4.5.2).
  - Arquivos de teste fora da análise, com o critério no `.lastro.yml` (4.4.1). Decisão provisória (D6).
  - PR de ativação com `.lastro.yml` para a base inicial (4.4.4).
  - Status de *commit* `lastro/documentacao` e limite de três novas interpretações por proposta (4.6.3 e 4.6.4).
  - Sessão de 8 h e reverificação de permissão a cada 1 h (4.7).
  - *Endpoints* de revisão do Quadro 10. Os caminhos são propostos aqui.
- **O que saiu do texto:** o *commit* da documentação na *branch* do PR, os arquivos JSON e Markdown no repositório, o filtro de `synchronize` do bot e a edição dos arquivos na aba "Files changed". A exportação do catálogo para o repositório ficou como desejável nos requisitos (RF-DOC-03) e não aparece no capítulo.
- **Hospedagem (Render) no Quadro 5:** o plano do *worker* e o provedor do banco ainda estão em aberto (D13). Se preferir, tire a linha até isso ser decidido.
- **Gemini 3.6 Flash:** confirme o nome e a versão do modelo na época da entrega.
- **Referências:** são documentações online; confira a data de acesso ao incluí-las.
