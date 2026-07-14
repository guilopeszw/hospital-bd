# CLI — Interface de Linha de Comando

## Visão Geral

CLI implementada em Python puro com `argparse` (stdlib). Todas as operações CRUD e consultas analíticas da Etapa 1 são acessíveis via terminal.

**Arquivo:** [`../../src/etapa1/atendimento_crud.py`](../../src/etapa1/atendimento_crud.py)

---

## Uso Básico

```bash
python -m src.etapa1.atendimento_crud <comando> [argumentos]
```

Ou, com a variável de ambiente `DATABASE_URL`:

```bash
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" \
  python -m src.etapa1.atendimento_crud <comando> [argumentos]
```

Para ajuda:

```bash
python -m src.etapa1.atendimento_crud --help
python -m src.etapa1.atendimento_crud <comando> --help
```

---

## Subcomandos

### ranking-residentes
Ranking de residentes por número de atendimentos realizados.

```bash
python -m src.etapa1.atendimento_crud ranking-residentes
```

### tempo-medio-residente
Tempo médio de duração dos atendimentos por residente.

```bash
python -m src.etapa1.atendimento_crud tempo-medio-residente
```

### plantoes-mes
Quantidade de plantões escalados por unidade/residente no mês corrente.

```bash
python -m src.etapa1.atendimento_crud plantoes-mes
```

### pacientes-sem-risco-alto
Pacientes que nunca realizaram procedimento de risco ALTO.

```bash
python -m src.etapa1.atendimento_crud pacientes-sem-risco-alto
```

### atendimentos-paciente
Lista todos os atendimentos de um paciente.

```bash
python -m src.etapa1.atendimento_crud atendimentos-paciente <id_paciente>
```

### procedimentos-atendimento
Lista procedimentos realizados em um atendimento.

```bash
python -m src.etapa1.atendimento_crud procedimentos-atendimento <id_atendimento>
```

### preceptores-mes
Preceptores com mais de 5 atendimentos em um mês.

```bash
python -m src.etapa1.atendimento_crud preceptores-mes <ano> <mes>
```

### remover-procedimento
Remove procedimento realizado (bloqueado se houver faturamento).

```bash
python -m src.etapa1.atendimento_crud remover-procedimento <id_atendimento> <id_procedimento>
```

### atualizar-paciente
Atualiza convênio e/ou alergias de um paciente.

```bash
python -m src.etapa1.atendimento_crud atualizar-paciente <id_paciente> --convenio NOVO-CONV
python -m src.etapa1.atendimento_crud atualizar-paciente <id_paciente> --alergias "Nova alergia"
```

### inserir-atendimento
Insere novo atendimento com validação de existência do paciente, residente e preceptor.

```bash
python -m src.etapa1.atendimento_crud inserir-atendimento "2025-07-01 10:00" 30 <id_paciente> <id_residente> <id_preceptor>
```

---

## Conexão com o Banco

A CLI lê a variável de ambiente `DATABASE_URL`. Valor default:

```
dbname=hospital_db user=postgres password=password host=localhost port=5433
```

Para sobrescrever:

```bash
export DATABASE_URL="dbname=hospital_db user=postgres password=minha_senha host=meu_host port=5433"
```
