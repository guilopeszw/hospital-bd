# DML — Dados de Teste (Seeds)

## Visão Geral

7 arquivos DML com dados de teste para todas as tabelas. Atendem aos requisitos mínimos da especificação.

**Localização:** [`../../sql/dml/`](../../sql/dml/)

---

## Arquivos e Conteúdo

| # | Arquivo | Tabelas | Qtde Registros | Requisito |
|---|---------|---------|----------------|-----------|
| 01 | `01_seed_pacientes.sql` | `PESSOA`, `PACIENTE` | 5 pacientes | Mínimo 5 |
| 02 | `02_seed_preceptores.sql` | `PESSOA`, `PROFISSIONAL`, `PRECEPTOR` | 5 preceptores | Mínimo 5 |
| 03 | `03_seed_residentes.sql` | `PESSOA`, `PROFISSIONAL`, `RESIDENTE` | 5 residentes | Mínimo 5 |
| 04 | `04_seed_atendimentos.sql` | `PROCEDIMENTO`, `ATENDIMENTO`, `PROCEDIMENTO_REALIZADO` | 10 procedimentos, 10 atendimentos, 10+ procedimentos realizados | Mínimo 10 atendimentos |
| 05 | `05_seed_unidades.sql` | `UNIDADE` | 3 unidades | Mínimo 3 |
| 06 | `06_seed_escalas.sql` | `ESCALA` | 8 escalas | — |
| 07 | `07_seed_faturamento.sql` | `FATURAMENTO` | 3 registros | Teste de remoção bloqueada |

---

## Dados de Exemplo

### Pacientes
| Nome | Convênio | Grupo Sanguíneo |
|------|----------|-----------------|
| Arthur Antunes Coimbra (Zico) | UNIMED-999 | A+ |
| Gabigol da Silva | SUS-456 | O- |
| Arrascaeta Giorgian | AMIL-101 | AB+ |
| Pedro Guilherme | CASSI-202 | O+ |

### Preceptores
| Nome | Titulação |
|------|-----------|
| Dr. Jorge Jesus | Doutor |
| Dra. Tia Leila | Mestre |
| Dr. Marcos Braz | Especialista |

### Unidades
| Nome | Tipo | Leitos |
|------|------|--------|
| Enfermaria Central | Enfermaria | 40 |
| UTI Adulto | UTI | 12 |
| Pronto-Socorro | Pronto-Socorro | 20 |

---

## Dependência Entre Seeds

A ordem de inserção respeita as FKs:

1. Pessoas base (pacientes, preceptores, residentes)
2. Profissionais e subclasses
3. Procedimentos (independentes)
4. Atendimentos (dependentes de paciente, residente, preceptor)
5. Procedimentos realizados (dependentes de atendimento e procedimento)
6. Unidades (independentes)
7. Escalas e faturamento (dependentes de tudo anterior)
