# Normalização

Este documento justifica a normalização das tabelas base do Sistema Hospitalar (Pessoa, Paciente, Profissional, Preceptor, Residente) até a 3FN.

## 1. Estratégia de herança: Joined Table Inheritance
Para mapear a especialização do enunciado, adotamos uma tabela base (`PESSOA`) e tabelas filhas que compartilham a mesma chave primária (`id_pessoa`) como Chave Estrangeira.

## 2. Análise por tabela

### PESSOA
- **Atributos:** `id_pessoa` (PK - UUID), `nome`, `cpf`, `data_nascimento`, `is_flamengo`, `telefone`
- **1FN:** Todos os atributos são atômicos (telefone é armazenado como string única de contato; nomes são atômicos).
- **2FN:** Não há dependências parciais, pois a PK é simples (`id_pessoa`). Todos os atributos dependem totalmente do UUID da pessoa.
- **3FN:** Não há dependências transitivas. Atributos como `is_flamengo` ou `cpf` dependem exclusivamente do ID da pessoa, e não de outros campos não-chave.
- **Constraints:** `cpf` possui constraint `UNIQUE`. `is_flamengo` possui `NOT NULL DEFAULT TRUE`.

### PACIENTE
- **Atributos:** `id_pessoa` (PK/FK), `num_convenio`, `alergias`, `grupo_sanguineo`
- **3FN:** Atende aos critérios pois depende diretamente de `id_pessoa`. `num_convenio` é um identificador único do plano, mas não determina os dados clínicos (alergias/sangue), eliminando dependências transitivas.

### PROFISSIONAL
- **Atributos:** `id_pessoa` (PK/FK), `crm`, `data_admissao`, `especialidade`, `papel_atual` (ENUM)
- **3FN:** O `crm` é único (`UNIQUE`). O campo `papel_atual` determina se no momento corrente ele atua como preceptor ou residente, mantendo a consistência exigida pelo histórico.

### PRECEPTOR / RESIDENTE
- **Preceptor:** `id_pessoa` (PK/FK), `titulacao`
- **Residente:** `id_pessoa` (PK/FK), `ano_residencia` (ENUM: R1, R2, R3)
- **3FN:** Ambas as tabelas estendem `PROFISSIONAL` de forma limpa. Não há atributos redundantes ou que dependam de campos fora da PK.