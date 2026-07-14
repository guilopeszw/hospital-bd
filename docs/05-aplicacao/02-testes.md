# Testes Automatizados

## Visão Geral

Suite de testes com `pytest` e `psycopg2`. Cobre validação de schema, constraints e regras de negócio. Cada sessão de teste isola o schema completamente.

**Localização:** [`../../tests/`](../../tests/)

---

## Estrutura

```
tests/
├── conftest.py                          # Fixtures globais
└── unit/
    ├── test_core_entities.py            # 5 testes (entidades base)
    └── test_negocio.py                  # 11 testes (regras de negócio)
```

---

## conftest.py — Isolamento do Schema

`conftest.py` aplica `DROP SCHEMA public CASCADE` + recria todo o DDL via fixture `setup_database` (escopo: sessão). Nenhum dado residual de execuções anteriores interfere.

Fixtures disponíveis:

| Fixture | Escopo | Descrição |
|---------|--------|-----------|
| `setup_database` | session | Recria schema do zero |
| `db_connection` | session | Conexão única |
| `db_cursor` | function | Cursor com ROLLBACK automático |

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

## Como Rodar

```bash
# Com DATABASE_URL default
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" pytest

# Com cobertura
DATABASE_URL="..." pytest -v --tb=short

# Apenas testes de negócio
DATABASE_URL="..." pytest tests/unit/test_negocio.py -v
```
