# 1. INTRODUÇÃO

A crescente complexidade dos sistemas de *software* contemporâneos transformou o desenvolvimento tecnológico em um esforço massivamente colaborativo e intrincado. Diferentemente de décadas passadas, o *software* moderno não é construído por indivíduos isolados, mas por equipes cada vez maiores e, frequentemente, distribuídas geograficamente (Pressman; Maxim, 2021). Essa escala traz consigo um desafio inerente: a dependência crítica do conhecimento técnico acumulado durante o ciclo de vida do desenvolvimento. Decisões arquiteturais, regras de negócio complexas e padrões de codificação específicos muitas vezes residem exclusivamente na mente dos desenvolvedores seniores, configurando um conhecimento tácito e não documentado.

Neste cenário, a alta rotatividade de profissionais, característica marcante do setor de Tecnologia da Informação, torna-se um risco operacional (Sommerville, 2019). Quando um desenvolvedor experiente deixa a organização, ele leva consigo não apenas suas habilidades, mas o domínio do contexto histórico e estrutural do projeto: por que determinada arquitetura foi escolhida em detrimento de alternativas, quais requisitos de negócio motivaram decisões que hoje parecem arbitrárias, quais são as partes frágeis do sistema que exigem atenção redobrada. A dificuldade de preservar esse conhecimento arquitetural e essas decisões técnicas gera consequências significativas para as organizações. Esse fenômeno remete à perda da memória organizacional, um risco alertado por Davenport e Prusak (1998), que ocorre de forma progressiva quando colaboradores deixam a empresa sem que seu conhecimento tácito tenha sido devidamente capturado, estruturado e preservado. As consequências práticas dessa amnésia corporativa são profundas e multidimensionais: o tempo necessário para o treinamento e a integração (*onboarding*) de novos desenvolvedores aumenta consideravelmente. A manutenção do *software* torna-se mais lenta, propensa a erros e financeiramente custosa, uma vez que novos programadores precisam decifrar o sistema por tentativa e erro, e funcionalidades são reimplementadas por desconhecimento (Martin, 2009). Essa perda contínua de domínio técnico compromete a sustentabilidade e a evolução do *software* a longo prazo, configurando um problema organizacional e financeiro, além de técnico.

Uma resposta recorrente a esse risco é externalizar o conhecimento em documentação, convertendo-o de tácito em explícito (Nonaka; Takeuchi, 1995). No desenvolvimento de *software*, contudo, essa externalização não é suficiente por si só. O código evolui continuamente, e a documentação que não acompanha essa evolução deixa de corresponder ao comportamento implementado, fenômeno conhecido como documentação desatualizada (*documentation drift*). Estudos com profissionais e com projetos da área apontam a desatualização como um problema recorrente da documentação de *software* (Forward; Lethbridge, 2002; Aghajani et al., 2019). Uma documentação desatualizada não apenas deixa de transmitir o conhecimento, mas passa a transmiti-lo de forma incorreta, levando a equipe a decisões baseadas em regras que já não valem. Assim, preservar o conhecimento sobre as regras de negócio de um sistema exige não somente registrá-lo, mas mantê-lo correto ao longo do tempo.

Um momento natural para essa manutenção é a revisão de código. Em equipes que utilizam plataformas como o GitHub, as alterações passam por um *pull request* (PR), no qual a mudança é apresentada, discutida e aprovada antes de ser integrada ao sistema. É nesse ponto que este trabalho propõe intervir: a cada PR, a análise estática do código identifica as unidades alteradas e as dependências envolvidas, e modelos de Inteligência Artificial auxiliam na interpretação da mudança e na redação, em linguagem natural, das regras de negócio afetadas. As atualizações propostas são submetidas à revisão humana antes de compor a documentação, e um portal torna esse conhecimento consultável, preservando o histórico de cada regra e o PR que a modificou.

Dessa forma, o presente trabalho justifica-se pela necessidade de mitigar a volatilidade do conhecimento em equipes de engenharia de *software*, substituindo a dependência da memória individual pela manutenção contínua da documentação das regras de negócio, apoiada por automação e validada por revisão humana. A relevância científica deste estudo reside na interseção entre a Engenharia de Software e a Gestão do Conhecimento e na avaliação quantitativa, por meio do reprocessamento de PRs reais e da comparação com linhas de base, da capacidade da análise estática combinada à Inteligência Artificial de manter essa documentação correta e atualizada. Do ponto de vista prático, a ferramenta busca tornar o conhecimento sobre as regras de negócio acessível à equipe, rastreável até a alteração de código que o originou e menos dependente de indivíduos específicos.

Portanto, o objetivo geral desta pesquisa é desenvolver e avaliar uma ferramenta que, por meio de análise estática de código e Inteligência Artificial, gere e mantenha atualizada, a cada *pull request*, a documentação das regras de negócio de sistemas de *software*, apoiando a retenção do conhecimento técnico nas equipes de desenvolvimento. Para alcançar este propósito, definem-se os seguintes objetivos específicos:

1. Gerar o catálogo inicial de regras de negócio e o grafo de dependências de um sistema a partir da leitura da Árvore de Sintaxe Abstrata (AST);
2. Detectar, a cada *pull request*, alterações em regras de negócio e propor as atualizações correspondentes na documentação, com o apoio de modelos de Inteligência Artificial;
3. Submeter as propostas à revisão humana no próprio *pull request*, incorporando ao catálogo apenas as atualizações aprovadas e integradas ao sistema;
4. Disponibilizar um portal com catálogo pesquisável, histórico das regras por *pull request* e grafo de dependências, facilitando a recuperação do conhecimento pelos desenvolvedores;
5. Avaliar a detecção de mudanças, a corretude das atualizações propostas e a atualização da documentação mantida, por meio do reprocessamento de *pull requests* reais e da comparação com linhas de base.

---

## Referências a acrescentar

AGHAJANI, E. et al. Software documentation issues unveiled. In: INTERNATIONAL CONFERENCE ON SOFTWARE ENGINEERING, 41., 2019, Montreal. **Proceedings** [...]. Piscataway: IEEE, 2019. p. 1199–1210.

FORWARD, A.; LETHBRIDGE, T. C. The relevance of software documentation, tools and technologies: a survey. In: ACM SYMPOSIUM ON DOCUMENT ENGINEERING, 2002, McLean. **Proceedings** [...]. New York: ACM, 2002. p. 26–33.

---

## Notas para o autor (não colar no TCC)

- **1º parágrafo:** sem alterações.
- **2º parágrafo:** só ajustes de redação.
  - "do projeto, porque determinada arquitetura" → "do projeto: por que determinada arquitetura"
  - "gera consequências profundas" → "gera consequências significativas", para não repetir "profundas" na frase seguinte
  - "multidimensionais, tempo necessário" → "multidimensionais: o tempo necessário"
- **3º a 5º parágrafos:** novos. Tratam da documentação desatualizada, da proposta de intervir no PR e da pergunta de pesquisa.
- **6º parágrafo (justificativa):** reescrito. Saem "processos automatizados de extração e registro", "documentação autônoma" e "capital intelectual".
- **Objetivo geral e objetivos específicos:** reescritos. Os cinco objetivos correspondem às seções 3.2.1, 3.2.2, 3.2.3, 3.2.4 e 3.3 do novo Capítulo 3.
- **Título e estrutura do trabalho:** por decisão sua, o título fica como está e não há parágrafo de estrutura do trabalho.
- **Citações novas:** Forward e Lethbridge (2002) e Aghajani et al. (2019) precisam ser conferidas por você. Elas também devem aparecer no Referencial Teórico, numa seção sobre documentação desatualizada.
- **Resumo:** continua desatualizado. Ainda fala em "sumarização" e em "reduz a curva de aprendizado".
