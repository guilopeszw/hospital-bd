# Esquema de Normalização e Modelo Lógico

Este documento formaliza a modelagem das entidades Core (Pessoa, Paciente, Profissional, Preceptor, Residente) mapeadas através da estratégia de **herança por tabela de associação (joined table inheritance)**, provando matematicamente a sua aderência até a 3FN.

---

## 1. Modelo Relacional

Chaves Primárias estão **sublinhadas** e Chaves Estrangeiras são indicadas por asterisco (`*`).

* **PESSOA** (__id_pessoa__, nome, cpf, data_nascimento, is_flamengo, telefone)
* **PACIENTE** (__id_pessoa__\*, num_convenio, alergias, grupo_sanguineo)
  * `id_pessoa` referencia PESSOA(id_pessoa)
* **PROFISSIONAL** (__id_pessoa__\*, crm, data_admissao, especialidade, papel_atual)
  * `id_pessoa` referencia PESSOA(id_pessoa)
* **PRECEPTOR** (__id_pessoa__\*, titulacao)
  * `id_pessoa` referencia PROFISSIONAL(id_pessoa)
* **RESIDENTE** (__id_pessoa__\*, ano_residencia)
  * `id_pessoa` referencia PROFISSIONAL(id_pessoa)

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