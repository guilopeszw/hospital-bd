# DDL — Definição do Esquema do Banco

## Visão Geral

12 arquivos DDL numerados por ordem de dependência. Criam todo o schema do hospital: enums, tabelas base, hierarquia de pessoas, tabelas de negócio e faturamento.

**Localização:** [`../../sql/ddl/`](../../sql/ddl/)

---

## Ordem de Criação

| # | Arquivo | Tabela(s) | Depende de |
|---|---------|-----------|------------|
| 01 | `01_enums.sql` | Enums | — |
| 02 | `02_pessoa.sql` | `PESSOA` | — |
| 03 | `03_paciente.sql` | `PACIENTE` | `PESSOA` |
| 04 | `04_profissional.sql` | `PROFISSIONAL` | `PESSOA` |
| 05 | `05_preceptor.sql` | `PRECEPTOR` | `PROFISSIONAL` |
| 06 | `06_residente.sql` | `RESIDENTE` | `PROFISSIONAL` |
| 07 | `07_procedimento.sql` | `PROCEDIMENTO` | — |
| 08 | `08_atendimento.sql` | `ATENDIMENTO` | `PACIENTE`, `RESIDENTE`, `PRECEPTOR` |
| 09 | `09_procedimento_realizado.sql` | `PROCEDIMENTO_REALIZADO` | `ATENDIMENTO`, `PROCEDIMENTO` |
| 10 | `10_unidade.sql` | `UNIDADE` | — |
| 11 | `11_escala.sql` | `ESCALA` | `UNIDADE`, `RESIDENTE`, `PRECEPTOR` |
| 12 | `12_faturamento.sql` | `FATURAMENTO` | `PROCEDIMENTO_REALIZADO` |

---

## Enums (01_enums.sql)

| Enum | Valores | Uso |
|------|---------|-----|
| `papel_profissional_enum` | `'residente'`, `'preceptor'` | `PROFISSIONAL.papel_atual` |
| `ano_residencia_enum` | `'R1'`, `'R2'`, `'R3'` | `RESIDENTE.ano_residencia` |
| `dia_semana_enum` | `'segunda'`..`'domingo'` | `ESCALA.dia_semana` |
| `turno_enum` | `'manha'`, `'tarde'`, `'noite'` | `ESCALA.turno` |
| `nivel_risco_enum` | `'BAIXO'`, `'MEDIO'`, `'ALTO'` | `PROCEDIMENTO.nivel_risco` |

---

## Hierarquia PESSOA (Joined Table Inheritance)

```
PESSOA (tabela base)
  ├── PACIENTE (FK → PESSOA)
  └── PROFISSIONAL (FK → PESSOA)
        ├── PRECEPTOR (FK → PROFISSIONAL)
        └── RESIDENTE (FK → PROFISSIONAL)
```

Cada subclasse herda a PK da tabela pai. Um profissional não pode estar em `PRECEPTOR` e `RESIDENTE` simultaneamente — a constraint é mantida por `CHECK` em `PROFISSIONAL.papel_atual` + FK cruzada.

---

## Constraints Relevantes

- **CPF único + regex:** `UNIQUE(cpf)` + `CHECK (cpf ~ '^\d{11}$')`
- **Grupo sanguíneo:** `CHECK (grupo_sanguineo IN ('A+','A-','B+','B-','AB+','AB-','O+','O-'))`
- **Capacidade de leitos positiva:** `CHECK (capacidade_leitos > 0)`
- **UNIQUE composto em ESCALA:** `UNIQUE(id_unidade, dia_semana, turno, id_residente)` — garante um preceptor por residente/plantão
- **PK composta em PROCEDIMENTO_REALIZADO:** `PRIMARY KEY (id_atendimento, id_procedimento)`

---

## Extensões

- `uuid-ossp` — geração de UUIDs via `uuid_generate_v4()`
- Todas as PKs usam `UUID` com `DEFAULT uuid_generate_v4()`
