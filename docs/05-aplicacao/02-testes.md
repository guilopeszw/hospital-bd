# Testes Automatizados

## Visão Geral

Suite de testes com `pytest`. Duas camadas:

- **`tests/unit/`** — SQL puro via `psycopg2` (schema/constraints/regras de negócio) e ORM via SQLAlchemy (Etapa 2: `crud_orm`, `consultas_avancadas`, `concorrencia`). 34 testes.
- **`tests/integration/`** — API Flask do webapp via test client, incluindo os endpoints que chamam procedures/views e disparam triggers da Etapa 2. 34 testes.

Total: **68 testes**, todos rodando contra o Postgres real (nenhum mock de banco).

**Localização:** [`../../tests/`](../../tests/)

---

## Estrutura

```
tests/
├── conftest.py                              # Fixtures globais
├── unit/
│   ├── test_core_entities.py                # 5 testes (entidades base, SQL puro)
│   ├── test_negocio.py                      # 11 testes (regras de negócio, SQL puro)
│   ├── test_etapa2_orm.py                   # 11 testes (crud_orm.py)
│   ├── test_etapa2_consultas_avancadas.py   # 4 testes (consultas_avancadas.py)
│   └── test_etapa2_concorrencia.py          # 3 testes (concorrencia.py, threads reais)
└── integration/
    └── test_webapp.py                       # 34 testes (API Flask, test client)
```

---

## conftest.py — Isolamento do Schema

`conftest.py` aplica `DROP SCHEMA public CASCADE` + recria todo o DDL via fixture `setup_database` (escopo: sessão). Nenhum dado residual de execuções anteriores interfere.

Fixtures disponíveis:

| Fixture | Escopo | Descrição |
|---------|--------|-----------|
| `setup_database` | session | Recria schema do zero (só DDL) |
| `db_connection` | session | Conexão única |
| `db_cursor` | function | Cursor com ROLLBACK automático — usado pelos testes de SQL puro |
| `seeded_db` | session | Carrega seeds + procedures + triggers + views **aditivamente** sobre o schema vazio (sem novo DROP). Usado pelos testes de ORM, consultas avançadas, concorrência e webapp — eles leem por uma conexão/engine separada da `db_cursor`, então precisam de dados de fato commitados. |

**Por que dois estilos de isolamento?** Os testes de SQL puro usam ROLLBACK por teste (rápido, sem sujeira). Os testes de ORM/webapp leem através de conexões diferentes (engine SQLAlchemy, cliente Flask) que não enxergam uma transação aberta em outra conexão — por isso usam dados commitados via `seeded_db`, com asserções desenhadas para tolerar mutações de outros testes na mesma sessão (contagem antes/depois em vez de número fixo, `issuperset` em vez de igualdade onde outro teste pode ter adicionado uma linha).

---

## Testes: Core Entities (5 testes)

| Teste | O que verifica |
|-------|---------------|
| `test_inserir_pessoa_valida` | Inserção de pessoa com dados válidos |
| `test_violacao_cpf_unico` | UNIQUE(cpf) barra CPF duplicado |
| `test_violacao_regex_cpf` | CHECK de formato rejeita CPF com letras |
| `test_violacao_grupo_sanguineo_paciente` | CHECK rejeita tipo sanguíneo inválido |
| `test_default_is_flamengo` | Default TRUE de is_flamengo |

## Testes: Regras de Negócio (11 testes)

| Teste | O que verifica |
|-------|---------------|
| `test_atendimento_fk_paciente_inexistente` | FK barra paciente que não existe |
| `test_escala_unique_constraint` | UNIQUE composto impede mesmo residente/unidade/dia/turno com 2 preceptores |
| `test_escala_mesmo_preceptor_residentes_diferentes_permitido` | Preceptor pode supervisionar 2 residentes no mesmo plantão |
| `test_delete_bloqueado_quando_ha_faturamento` | NOT EXISTS bloqueia DELETE com faturamento |
| `test_delete_direto_de_faturado_viola_fk` | FK ON DELETE RESTRICT também bloqueia |
| `test_delete_permitido_sem_faturamento` | DELETE permitido sem faturamento |
| `test_faturamento_unico_por_procedimento_realizado` | UNIQUE em FATURAMENTO impede dupla cobrança |
| `test_profissional_nao_pode_ter_dois_papeis` | FK composta impede PRECEPTOR com papel_atual='residente' |
| `test_trocar_papel_com_subtipo_ativo_e_bloqueado` | CHECK impede troca de papel sem limpar subtipo |
| `test_procedimento_nivel_risco_enum_invalido` | Enum rejeita valor fora do domínio |
| `test_unidade_capacidade_leitos_positiva` | CHECK rejeita capacidade ≤ 0 |

---

## Testes: ORM — crud_orm.py (11 testes)

Cobre as operações da Etapa 1 reimplementadas via ORM: `ranking_residentes`, `tempo_medio_por_residente`, `preceptores_mais_atendimentos_mes`, `pacientes_sem_procedimento_risco_alto`, `listar_procedimentos_atendimento`, `inserir_atendimento` (feliz + FK inexistente), `listar_atendimentos_paciente`, `atualizar_paciente`, `remover_procedimento_realizado` (bloqueado/permitido).

## Testes: Consultas Avançadas — consultas_avancadas.py (4 testes)

Cobre os 3 itens do enunciado (preceptores que supervisionaram flamenguistas, último atendimento por paciente, % de risco alto por residente) mais uma checagem de que o "último atendimento" bate com a data mais recente real do seed.

## Testes: Concorrência — concorrencia.py (3 testes)

Testa `escalar_residente_com_lock` isoladamente (cria escala; rejeita slot já ocupado) e a `demo()` real com duas threads disputando o mesmo residente/dia/turno/unidade — verifica que o lock pessimista serializa (exatamente 1 sucesso, 1 rejeição, nunca os dois nem erro cru de banco). Usa slots (`domingo`) que não existem no seed, pra não colidir com a UNIQUE real.

## Testes: Webapp — test_webapp.py (34 testes)

Sobe a API Flask via test client (sem processo separado) contra o Postgres real. Cobre `/api/health`, `/api/dashboard/summary`, CRUD de pacientes (listar, buscar, criar, atualizar, CPF duplicado, campo obrigatório faltando), CRUD de atendimentos (criar, unidade inexistente), CRUD de profissionais e unidades, listagens de apoio, e os 6 endpoints de `/api/analytics/*`.

**Etapa 2 via HTTP** — a segunda metade do arquivo prova que views/procedures/triggers funcionam de ponta a ponta pela API, não só pela CLI/ORM:
- `/api/views/*` batem com o resultado das 3 views direto no banco.
- `sp_registrar_atendimento_completo` (via `POST /atendimentos` com `procedimentos`): confirma no Postgres, com uma query separada, que o atendimento *e* o procedimento foram persistidos — não só que a API respondeu 201. Foi esse teste que pegou o bug do `query()`/`execute()` (ver `04-webapp.md`).
- `sp_reajustar_escala` (`POST /escalas/reajustar`): confirma no banco que o slot da escala mudou de verdade.
- `trg_atualiza_media_procedimentos`: registra um procedimento e confere que `media_tempo_procedimento` mudou de valor no Postgres.
- `trg_check_sobreposicao_escala`: cria duas escalas conflitantes via `POST /escalas` e espera `409` com a mensagem do `RAISE EXCEPTION`.
- Testes que criam dado novo (residente, escala, unidade) limpam depois de si — outros módulos desta suite assumem contagens exatas do seed (5 residentes etc.) e quebrariam se o dado ficasse para trás.

---

## Como Rodar

```bash
# Toda a suite (unit + integration)
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" pytest

# Com verbose
DATABASE_URL="..." pytest -v --tb=short

# Só SQL puro (rápido, sem seeds/Etapa 2)
DATABASE_URL="..." pytest tests/unit/test_negocio.py tests/unit/test_core_entities.py -v

# Só Etapa 2 (ORM + consultas avançadas + concorrência)
DATABASE_URL="..." pytest tests/unit/test_etapa2_*.py -v

# Só webapp
DATABASE_URL="..." pytest tests/integration/ -v
```
