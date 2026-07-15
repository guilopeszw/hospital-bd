# DER — Diagrama e Justificativa das Cardinalidades

**Hospital Universitário Dra. Yuska Maritan Brito** — Etapa 1 Modelo conceitual/lógico, notação Crow's Foot (pé-de-galinha).

## 1. Diagrama Entidade-Relacionamento

![Diagrama Entidade-Relacionamento](./der_hospitalar_diagrama.png)

## 2. Especializações (herança)

O modelo usa *joined table inheritance*: cada subtipo é uma tabela cuja PK é também FK para o supertipo. Toda especialização é, portanto, 1:0..1 no nível físico — o supertipo existe sozinho, e o subtipo só existe se o supertipo existir.

### 2.1 PESSOA → PACIENTE (1 : 0..1)

Uma pessoa pode ser paciente; um paciente é sempre exatamente uma pessoa.

- Lado PESSOA (1,1) em relação ao paciente: `PACIENTE.id_pessoa` é PK e FK para PESSOA, logo todo paciente tem uma e apenas uma pessoa por trás.
- Lado PACIENTE (0,1): a especialização é parcial — existe pessoa que nunca foi paciente (um preceptor, por exemplo). Por isso o `|o` e não `| |`.
- Sobreposição: a especialização PACIENTE/PROFISSIONAL é sobreposta (*overlapping*) de propósito: nada impede um médico do hospital ser atendido como paciente lá dentro. O modelo permite as duas linhas para o mesmo `id_pessoa`.

### 2.2 PESSOA → PROFISSIONAL (1 : 0..1)

Mesma mecânica: `PROFISSIONAL.id_pessoa` é PK+FK. Nem toda pessoa é profissional (participação parcial), e todo profissional é exatamente uma pessoa.

### 2.3 PROFISSIONAL → PRECEPTOR e PROFISSIONAL → RESIDENTE (1 : 0..1, disjuntas)

Aqui a especialização é disjunta e parcial, e essa disjunção é o ponto delicado do enunciado: "um profissional pode atuar como preceptor num período e como residente em outro (histórico), mas num dado momento exerce apenas um papel".

Como isso é garantido sem trigger, só com integridade referencial declarativa:

1. `PROFISSIONAL` tem a coluna `papel_atual` (`'residente'` | `'preceptor'`) e a constraint `UNIQUE (id_pessoa, papel_atual)`, que serve de alvo de FK.
2. `PRECEPTOR` tem uma coluna `papel` com `CHECK (papel = 'preceptor')` e uma FK composta `(id_pessoa, papel)` → `PROFISSIONAL(id_pessoa, papel_atual)`.
3. `RESIDENTE` faz o simétrico, travando `papel = 'residente'`.

Consequência: um profissional com `papel_atual = 'residente'` não consegue ter linha em `PRECEPTOR` — a FK composta não acha o par `(id_pessoa, 'preceptor')` em `PROFISSIONAL`. A disjunção do DER vira uma restrição real no banco.

A troca de papel (o "histórico" do enunciado) é feita removendo a linha do papel antigo e inserindo a do novo, sempre atualizando `papel_atual` — o `ON UPDATE CASCADE` da FK composta, somado ao `CHECK`, impede que a troca aconteça pela metade.

## 3. Relacionamentos de Atendimento

### 3.1 PACIENTE (1) —recebe— (0..N) ATENDIMENTO

- Do lado do ATENDIMENTO: (1,1) — todo atendimento tem exatamente um paciente (`id_paciente NOT NULL` + FK). Não existe atendimento sem paciente.
- Do lado do PACIENTE: (0,N) — um paciente pode ter zero atendimentos (cadastrado, ainda não atendido) ou vários ao longo do tempo.
- `ON DELETE RESTRICT`: não se apaga paciente que tem histórico de atendimento.

### 3.2 RESIDENTE (1) —executa— (0..N) ATENDIMENTO

- Do lado do ATENDIMENTO: (1,1) — o enunciado diz que cada atendimento envolve um residente, que executa o cuidado sob supervisão. `id_residente NOT NULL`.
- Do lado do RESIDENTE: (0,N) — residente recém-admitido tem zero atendimentos. É exatamente por isso que a consulta de ranking usa `LEFT JOIN`: um `INNER JOIN` sumiria com o residente de total zero.

### 3.3 PRECEPTOR (1) —supervisiona— (0..N) ATENDIMENTO

- Do lado do ATENDIMENTO: (1,1) — um preceptor supervisiona aquele atendimento específico. `id_preceptor NOT NULL`.
- Do lado do PRECEPTOR: (0,N) — um preceptor supervisiona muitos atendimentos.

Os três FKs coexistem em `ATENDIMENTO`. É o que caracteriza um relacionamento ternário resolvido como entidade: paciente + residente + preceptor + data/hora + duração.

## 4. ATENDIMENTO × PROCEDIMENTO (N:M) via PROCEDIMENTO_REALIZADO

O enunciado: "durante um atendimento, um ou mais procedimentos podem ser realizados", e cada execução guarda quantidade, tempo real e observações. Isso é um N:M com atributos próprios, resolvido pela tabela associativa `PROCEDIMENTO_REALIZADO` com PK composta `(id_atendimento, id_procedimento)`.

- ATENDIMENTO (1) — (0..N) PROCEDIMENTO_REALIZADO: conceitualmente o esperado é 1..N (todo atendimento registra pelo menos um procedimento) e os dados de seed respeitam isso. Fisicamente o diagrama marca (0,N), porque um mínimo obrigatório de 1 filho não é expressável por FK — exigiria trigger ou constraint deferida (Etapa 2). O DER reflete o que o schema realmente garante, não o que gostaríamos que garantisse.
- PROCEDIMENTO (1) — (0..N) PROCEDIMENTO_REALIZADO: um procedimento do catálogo (ex.: "Drenagem de abscesso") pode nunca ter sido executado — daí o zero. E o mesmo procedimento pode ser executado em muitos atendimentos diferentes.
- PROCEDIMENTO_REALIZADO → (1,1) ATENDIMENTO e (1,1) PROCEDIMENTO — as duas colunas da PK composta são `NOT NULL` por definição.
- `ON DELETE CASCADE` no lado do atendimento (apagou o atendimento, some o registro de execução) e `ON DELETE RESTRICT` no lado do procedimento (não se apaga do catálogo um procedimento que já foi executado).

## 5. PROCEDIMENTO_REALIZADO (1) —é faturado por— (0..1) FATURAMENTO

O enunciado exige que só se possa remover um procedimento realizado se não houver faturamento associado. "Faturamento associado" é uma entidade, não um booleano — então há uma tabela `FATURAMENTO` com valor e data de emissão.

- (0,1) do lado do FATURAMENTO: um procedimento realizado é faturado no máximo uma vez, garantido por `UNIQUE (id_atendimento, id_procedimento)` em `FATURAMENTO`; pode também nunca ter sido faturado (zero).
- (1,1) do lado do PROCEDIMENTO_REALIZADO: todo faturamento aponta para exatamente um procedimento realizado (FK composta, `NOT NULL`).
- `ON DELETE RESTRICT` é o coração da regra: o banco recusa apagar um `PROCEDIMENTO_REALIZADO` que tenha faturamento. A aplicação também filtra com `NOT EXISTS` para dar uma mensagem amigável, mas mesmo que a aplicação erre, o schema não deixa passar.

## 6. ESCALA — o plantão recorrente

`ESCALA` materializa o relacionamento ternário UNIDADE × RESIDENTE × PRECEPTOR, qualificado por `dia_semana` e `turno`.

- UNIDADE (1) — (0..N) ESCALA: toda escala acontece em exatamente uma unidade (`id_unidade NOT NULL`); uma unidade pode ter zero ou muitas escalas.
- RESIDENTE (1) — (0..N) ESCALA: toda escala tem exatamente um residente; um residente pode estar em vários plantões (dias/turnos/unidades diferentes).
- PRECEPTOR (1) — (0..N) ESCALA: toda escala tem exatamente um preceptor responsável; um preceptor pode aparecer em muitas escalas.

### 6.1 A restrição de unicidade e por que o preceptor fica de fora dela

```sql
UNIQUE (id_unidade, dia_semana, turno, id_residente)
```

O enunciado pede duas coisas que parecem opostas:

1. "o mesmo residente não pode ser escalado no mesmo local/dia/turno com dois preceptores diferentes" → a chave única não inclui `id_preceptor`. Se incluísse, `(unidade, dia, turno, residente, preceptor_A)` e `(unidade, dia, turno, residente, preceptor_B)` seriam duas linhas válidas — o que é exatamente o que se quer proibir. Deixando o preceptor fora da `UNIQUE`, a segunda inserção colide na primeira. Um residente tem um único preceptor supervisor por unidade/dia/turno.
2. "um mesmo preceptor pode supervisionar vários residentes no mesmo turno" → como `id_preceptor` não faz parte da chave, nada impede duas linhas com o mesmo preceptor e residentes distintos. Permitido, como pedido.

### 6.2 dia_semana é categoria, não data

`ESCALA` guarda um plantão recorrente semanal (`'segunda'`, `'terca'`, …), não um evento datado. Por isso a consulta analítica "plantões escalados no mês corrente" usa `generate_series` sobre os dias do mês e conta quantas vezes cada dia da semana cai no calendário — uma escala de segunda-feira vale 4 ou 5 plantões, dependendo do mês.

## 7. Tabela-resumo das cardinalidades

| Relacionamento | Lado esquerdo | Lado direito | Como o banco garante |
|---|---|---|---|
| PESSOA → PACIENTE | (1,1) | (0,1) | PK = FK em PACIENTE |
| PESSOA → PROFISSIONAL | (1,1) | (0,1) | PK = FK em PROFISSIONAL |
| PROFISSIONAL → PRECEPTOR | (1,1) | (0,1) | PK = FK composta + CHECK (disjunta) |
| PROFISSIONAL → RESIDENTE | (1,1) | (0,1) | PK = FK composta + CHECK (disjunta) |
| PACIENTE → ATENDIMENTO | (1,1) | (0,N) | FK NOT NULL, ON DELETE RESTRICT |
| RESIDENTE → ATENDIMENTO | (1,1) | (0,N) | FK NOT NULL, ON DELETE RESTRICT |
| PRECEPTOR → ATENDIMENTO | (1,1) | (0,N) | FK NOT NULL, ON DELETE RESTRICT |
| ATENDIMENTO → PROCEDIMENTO_REALIZADO | (1,1) | (0,N) | PK composta, ON DELETE CASCADE |
| PROCEDIMENTO → PROCEDIMENTO_REALIZADO | (1,1) | (0,N) | PK composta, ON DELETE RESTRICT |
| PROCEDIMENTO_REALIZADO → FATURAMENTO | (1,1) | (0,1) | FK composta + UNIQUE, ON DELETE RESTRICT |
| UNIDADE → ESCALA | (1,1) | (0,N) | FK NOT NULL, ON DELETE RESTRICT |
| RESIDENTE → ESCALA | (1,1) | (0,N) | FK NOT NULL + UNIQUE(unidade,dia,turno,residente) |
| PRECEPTOR → ESCALA | (1,1) | (0,N) | FK NOT NULL (fora da UNIQUE, de propósito) |

## 8. Evidências de Normalização

Justificativa de Normalização (1FN, 2FN e 3FN) — O modelo de dados proposto atende rigorosamente às três primeiras Formas Normais:

- **1ª Forma Normal (1FN)**: Garantida pela atomicidade dos atributos. Não existem atributos multivalorados ou compostos nas tabelas. Por exemplo, o telefone é um campo único na tabela PESSOA, e as associações M:N (como ATENDIMENTO e PROCEDIMENTO) foram corretamente resolvidas por meio da tabela associativa PROCEDIMENTO_REALIZADO. Todas as tabelas possuem uma Chave Primária (PK) bem definida.
- **2ª Forma Normal (2FN)**: O modelo está em 1FN e todos os atributos não-chave dependem totalmente das chaves primárias. O melhor exemplo é a tabela PROCEDIMENTO_REALIZADO, cuja PK é composta (id_atendimento, id_procedimento). Os atributos quantidade, tempo_real_minutos e observacao dependem da execução específica daquele procedimento naquele atendimento (dependência total da chave composta), e não apenas do atendimento ou apenas do procedimento.
- **3ª Forma Normal (3FN)**: O modelo está em 2FN e não possui dependências transitivas (atributos não-chave dependendo de outros atributos não-chave). As informações específicas de PACIENTE (grupo sanguíneo, alergias) e de PROFISSIONAL (CRM, especialidade) foram isoladas de PESSOA usando herança, garantindo que a entidade base armazene apenas dados puramente pessoais (CPF, data de nascimento).

## 9. Modelo Relacional

- `PESSOA (id_pessoa, nome, cpf, data_nascimento, is_flamengo, telefone)`
- `PACIENTE (id_pessoa (FK), num_convenio, alergias, grupo_sanguineo)`
- `PROFISSIONAL (id_pessoa (FK), crm, data_admissao, especialidade, papel_atual)`
- `PRECEPTOR (id_pessoa (FK), papel (FK), titulacao)`
- `RESIDENTE (id_pessoa (FK), papel (FK), ano_residencia)`
- `UNIDADE (id_unidade, nome, tipo, capacidade_leitos)`
- `ATENDIMENTO (id_atendimento, data_hora, duracao_minutos, id_paciente (FK), id_residente (FK), id_preceptor (FK))`
- `PROCEDIMENTO (id_procedimento, codigo, nome, tempo_medio_minutos, nivel_risco)`
- `PROCEDIMENTO_REALIZADO (id_atendimento (FK), id_procedimento (FK), quantidade, tempo_real_minutos, observacao)`
- `FATURAMENTO (id_faturamento, id_atendimento (FK), id_procedimento (FK), valor, data_emissao)`
- `ESCALA (id_escala, id_unidade (FK), dia_semana, turno, id_residente (FK), id_preceptor (FK))`

## 10. Execução do Projeto

Passo a passo para subir o banco, popular os dados, rodar os testes automatizados e usar a CLI de CRUD/consultas — reflete exatamente o que está em `README.md`, `docker/docker-compose.yml` e `tests/conftest.py`.

### 10.1 Pré-requisitos

- Docker + Docker Compose
- Python 3.12+ e o cliente `psql` do PostgreSQL

### 10.2 Subir o banco

```bash
cd docker
docker compose up -d
```

O PostgreSQL (imagem `postgres:16-alpine`) fica disponível em `localhost:5433` (user=`postgres`, password=`password`, db=`hospital_db`).

### 10.3 Popular o banco (DDL + seeds)

```bash
for f in sql/ddl/*.sql sql/dml/*.sql; do
  psql "postgresql://postgres:password@localhost:5433/hospital_db" -f "$f"
done
```

Os arquivos são numerados e devem rodar nessa ordem — o `for` acima já respeita a ordem numérica: `01_enums` → `02_pessoa` → ... → `11_escala` → `12_faturamento` (DDL), seguido de `01_seed_pacientes` → ... → `07_seed_faturamento` (DML).

### 10.4 Rodar os testes automatizados

```bash
pip install -r requirements.txt
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" pytest
```

A fixture de sessão em `tests/conftest.py` recria o schema do zero a cada execução (`DROP SCHEMA public CASCADE` + reaplicação de todo o DDL 01–12), então não é necessário ter rodado o passo 10.3 antes. São 11 testes automatizados: 5 em `test_core_entities.py` (CPF único, regex de CPF, grupo sanguíneo, default de `is_flamengo`) e 6 em `test_negocio.py` (FK de Atendimento, UNIQUE de Escala, mesmo preceptor com residentes diferentes, bloqueio de remoção de procedimento faturado, enum de `nivel_risco`, CHECK de `capacidade_leitos`).

### 10.5 Usar a CLI

Comandos prontos para copiar e colar, já com os UUIDs reais dos seeds (`sql/dml/`) no lugar dos placeholders — úteis para rodar ao vivo durante a apresentação:

```bash
# Consultas analíticas (sem parâmetros)
python -m src.etapa1.atendimento_crud ranking-residentes
python -m src.etapa1.atendimento_crud tempo-medio-residente
python -m src.etapa1.atendimento_crud plantoes-mes
python -m src.etapa1.atendimento_crud pacientes-sem-risco-alto

# Preceptores com mais de 5 atendimentos em um mês (ano, mes)
python -m src.etapa1.atendimento_crud preceptores-mes 2025 6

# Atendimentos de um paciente (Arthur Antunes Coimbra)
python -m src.etapa1.atendimento_crud atendimentos-paciente a1111111-1111-1111-1111-111111111111

# Procedimentos realizados em um atendimento
python -m src.etapa1.atendimento_crud procedimentos-atendimento e1111111-1111-1111-1111-111111111111

# Remover um procedimento realizado (bloqueado se já houver faturamento)
python -m src.etapa1.atendimento_crud remover-procedimento \
    e1111111-1111-1111-1111-111111111111 d1111111-1111-1111-1111-111111111111

# Atualizar convênio do paciente
python -m src.etapa1.atendimento_crud atualizar-paciente \
    a1111111-1111-1111-1111-111111111111 --convenio NOVO-CONV

# Inserir um novo atendimento (data, duração, paciente, residente, preceptor)
python -m src.etapa1.atendimento_crud inserir-atendimento \
    "2025-07-01 10:00:00" 30 \
    a1111111-1111-1111-1111-111111111111 \
    c1111111-1111-1111-1111-111111111111 \
    b1111111-1111-1111-1111-111111111111
```

Cada subcomando corresponde a uma operação de CRUD ou a uma das quatro consultas analíticas, implementadas em SQL puro via psycopg2 em `src/etapa1/atendimento_crud.py`, com o SQL equivalente documentado em `sql/queries/`.
