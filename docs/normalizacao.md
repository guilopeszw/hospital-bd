# Esquema de Normalização e Modelo Lógico

Este documento formaliza a modelagem das entidades Core (Pessoa, Paciente, Profissional, Preceptor, Residente) mapeadas através da estratégia de **herança por tabela de associação (joined table inheritance)**, provando matematicamente a sua aderência até a 3FN.

---

## 1. Modelo Relacional — Core

Chaves Primárias estão **sublinhadas** e Chaves Estrangeiras são indicadas por asterisco (`*`).

* **PESSOA** (__id_pessoa__, nome, cpf, data_nascimento, is_flamengo, telefone)
* **PACIENTE** (__id_pessoa__\*, num_convenio, alergias, grupo_sanguineo)
  * `id_pessoa` referencia PESSOA(id_pessoa)
* **PROFISSIONAL** (__id_pessoa__\*, crm, data_admissao, especialidade, papel_atual)
  * `id_pessoa` referencia PESSOA(id_pessoa)
  * `UNIQUE(id_pessoa, papel_atual)` — chave candidata usada como alvo das FKs compostas de PRECEPTOR e RESIDENTE
* **PRECEPTOR** (__id_pessoa__\*, papel\*, titulacao)
  * `(id_pessoa, papel)` referencia PROFISSIONAL(id_pessoa, papel_atual); `CHECK (papel = 'preceptor')`
* **RESIDENTE** (__id_pessoa__\*, papel\*, ano_residencia)
  * `(id_pessoa, papel)` referencia PROFISSIONAL(id_pessoa, papel_atual); `CHECK (papel = 'residente')`

> A coluna `papel` em PRECEPTOR/RESIDENTE não é redundância de dados: é o mecanismo declarativo que torna a especialização **disjunta** (um profissional exerce um único papel por vez, como exige o enunciado). Ela é constante por tabela — travada pelo CHECK — e não introduz dependência funcional nova, já que $\{id\_pessoa\} \rightarrow \{papel\}$ é trivialmente satisfeita pela chave. Ver detalhamento em `docs/der/cardinalidades.md`, seção 2.3.

---

## 2. Prova Formal de Normalização

Definimos $R$ como a relação e $X \rightarrow Y$ como uma Dependência Funcional (DF), onde o determinante $X$ mapeia univocamente o dependente $Y$.

### A. 1FN
**Definição:** Uma relação $R$ está na 1FN se, e somente se, todos os domínios de seus atributos contêm apenas valores atômicos (indivisíveis) e não existem grupos repetitivos ou atributos multivalorados.

* **Prova:** No esquema implementado, atributos textuais como `nome` e `telefone` guardam cadeias atômicas de caracteres de contato direto (não há vetores ou múltiplos telefones na mesma célula). Atributos clínicos como `alergias` utilizam o tipo `TEXT` de forma declarativa e não-estruturada. Portanto, nenhuma tupla viola a atomicidade de domínio.

### B. 2FN
**Definição:** Uma relação $R$ está na 2FN se estiver na 1FN e todo atributo não-chave depender funcionalmente de forma **plena** da chave primária (não existem dependências parciais sobre chaves compostas).

* **Prova:** Seja $K$ a Chave Primária de qualquer uma das tabelas core. Nota-se que em todas as cinco tabelas, $|K| = 1$, ou seja, a chave primária é **simples** (composta por um único atributo: `id_pessoa`). 
* Por definição matemática, se a chave primária não é composta, é impossível a existência de uma dependência funcional parcial de um atributo não-chave em relação a uma parte da chave. Logo, as relações satisfazem a 2FN por vacuidade de subconjuntos de chaves.
* Exemplificando as Dependências Plenas:
  * $\{id\_pessoa\} \rightarrow \{nome, cpf, data\_nascimento\}$
  * $\{id\_pessoa\} \rightarrow \{crm, especialidade\}$

### C. 3FN
**Definição:** Uma relação $R$ está na 3FN se estiver na 2FN e nenhuma dependência funcional $X \rightarrow Y$ entre atributos não-chave for transitiva (atributos não-chave devem depender exclusivamente da chave primária, e não de outros atributos não-chave).

* **Prova:** Analisando os determinantes das relações:
  1. Em `PESSOA`, embora o `cpf` seja uma chave candidata (cpf -> id_pessoa), ela possui restrição `UNIQUE`, caracterizando-se como superchave. Não há relações do tipo $A \rightarrow B \rightarrow C$ onde $B$ não seja uma superchave. O atributo `is_flamengo` depende estritamente do indivíduo (id_pessoa).
  2. Em `PACIENTE`, as condições médicas (`alergias`, `grupo_sanguineo`) dependem unicamente da biologia do paciente ligado à superchave `id_pessoa`. O número do convênio não determina as alergias do indivíduo.
  3. Em `PROFISSIONAL`, o `crm` atua como chave candidata (`UNIQUE`). O campo de controle de histórico `papel_atual` mapeia o estado da superchave naquele momento temporal.
* Como não existem dependências transitivas induzidas por atributos não-determinantes, o modelo core encontra-se estritamente na 3FN.

---

## 3. Modelo Relacional — Tabelas de Negócio

* **UNIDADE** (__id_unidade__, nome, tipo, capacidade_leitos)
* **PROCEDIMENTO** (__id_procedimento__, codigo, nome, tempo_medio_minutos, nivel_risco)
* **ATENDIMENTO** (__id_atendimento__, data_hora, duracao_minutos, id_paciente\*, id_residente\*, id_preceptor\*)
  * `id_paciente` referencia PACIENTE(id_pessoa); `id_residente` referencia RESIDENTE(id_pessoa); `id_preceptor` referencia PRECEPTOR(id_pessoa)
* **PROCEDIMENTO_REALIZADO** (__id_atendimento__\*, __id_procedimento__\*, quantidade, tempo_real_minutos, observacao)
  * PK composta; `id_atendimento` referencia ATENDIMENTO(id_atendimento); `id_procedimento` referencia PROCEDIMENTO(id_procedimento)
* **FATURAMENTO** (__id_faturamento__, id_atendimento\*, id_procedimento\*, valor, data_emissao)
  * `(id_atendimento, id_procedimento)` referencia PROCEDIMENTO_REALIZADO(id_atendimento, id_procedimento), com `UNIQUE` — no máximo um faturamento por procedimento realizado
* **ESCALA** (__id_escala__, id_unidade\*, dia_semana, turno, id_residente\*, id_preceptor\*)
  * `UNIQUE(id_unidade, dia_semana, turno, id_residente)`

## 4. Prova de Normalização — Tabelas de Negócio

### 4.1 UNIDADE, PROCEDIMENTO, ATENDIMENTO, ESCALA, FATURAMENTO (1FN/2FN/3FN)

Todas essas cinco tabelas têm **chave primária simples** (um único atributo UUID). Pelo mesmo argumento da seção 2.B, a 2FN é satisfeita por vacuidade (não há como existir dependência parcial sobre uma chave de tamanho 1). Os atributos não-chave de cada uma dependem apenas do identificador da própria entidade (ex.: `capacidade_leitos` depende só de `id_unidade`; `tempo_medio_minutos` e `nivel_risco` dependem só de `id_procedimento`; `valor` e `data_emissao` dependem só de `id_faturamento`), sem dependência transitiva entre atributos não-chave — logo, 3FN.

Sobre `FATURAMENTO`: o par `(id_atendimento, id_procedimento)` é **chave candidata** (tem `UNIQUE`), e portanto superchave — a FD $\{id\_atendimento, id\_procedimento\} \rightarrow \{valor, data\_emissao\}$ não é transitiva por atributo não-chave, e a 3FN se mantém. Modelar o faturamento como entidade própria, em vez de uma flag booleana `faturado` dentro de `PROCEDIMENTO_REALIZADO`, também elimina a dependência de um atributo (`valor`) que não teria onde morar sem gerar redundância.

Único ponto que merece nota: em `ESCALA`, o atributo `dia_semana` é categórico (segunda-domingo), não uma data concreta — isso é modelagem proposital (plantão recorrente semanal, não um evento pontual), e não fere nenhuma forma normal: `dia_semana`, `turno`, `id_unidade`, `id_residente` e `id_preceptor` dependem todos apenas de `id_escala`.

### 4.2 PROCEDIMENTO_REALIZADO (a única prova de 2FN não-trivial do documento)

Esta é a única tabela com **chave primária composta** (`id_atendimento`, `id_procedimento`), então é o único caso em que a 2FN precisa ser provada de verdade (não por vacuidade).

* **1FN:** `quantidade`, `tempo_real_minutos` e `observacao` são todos atômicos (inteiros e texto livre) — sem grupos repetitivos.
* **2FN:** Seja $K = \{id\_atendimento, id\_procedimento\}$ a chave composta. Testamos dependência parcial para cada atributo não-chave:
  * `quantidade`, `tempo_real_minutos`, `observacao` — nenhum depende apenas de `id_atendimento` (o mesmo atendimento pode ter vários procedimentos, cada um com tempo/quantidade diferentes) nem apenas de `id_procedimento` (o mesmo procedimento executado em atendimentos diferentes pode ter tempos reais diferentes — ex.: uma sutura simples pode levar 18min num atendimento e 22min em outro, como nos dados de seed). Logo, esses atributos dependem da combinação inteira $\{id\_atendimento, id\_procedimento\} \rightarrow \{quantidade, tempo\_real\_minutos, observacao\}$, sem dependência parcial — 2FN satisfeita.
* **3FN:** Não há dependência transitiva entre os atributos não-chave (`observacao` não determina `quantidade`, por exemplo) — todos dependem exclusivamente da chave composta completa. Logo, `PROCEDIMENTO_REALIZADO` está na 3FN.

> Nota de projeto: a situação de faturamento **não** é um atributo desta tabela. Uma flag `faturado` guardaria só metade do fato (falta valor e data de emissão) e viraria redundância no dia em que o faturamento ganhasse atributos próprios. O fato "este procedimento realizado foi faturado por R$ X em tal data" mora na relação `FATURAMENTO`, cuja existência (ou não) responde à pergunta que o enunciado faz na hora de remover um procedimento.