```mermaid
%%{init: { 'theme': 'base', 'themeVariables': { 'primaryColor': '#f4f4f6', 'primaryTextColor': '#1e293b', 'primaryBorderColor': '#64748b', 'lineColor': '#dc2626', 'secondaryColor': '#e2e8f0', 'tertiaryColor': '#ffffff'}, 'graph': { 'rankdir': 'TB', 'nodesep': 60, 'edgesep': 40, 'ranksep': 80 }}}%%
erDiagram
    %% --- Entidades Core ---
    PESSOA {
        uuid id_pessoa PK
        varchar nome
        varchar cpf UK
        date data_nascimento
        boolean is_flamengo
        varchar telefone
    }

    PACIENTE {
        uuid id_pessoa PK, FK
        varchar num_convenio
        text alergias
        varchar grupo_sanguineo
    }

    PROFISSIONAL {
        uuid id_pessoa PK, FK
        varchar crm UK
        date data_admissao
        varchar especialidade
        papel_profissional_enum papel_atual
    }

    PRECEPTOR {
        uuid id_pessoa PK, FK
        papel_profissional_enum papel
        varchar titulacao
    }

    RESIDENTE {
        uuid id_pessoa PK, FK
        papel_profissional_enum papel
        ano_residencia_enum ano_residencia
    }

    %% --- Entidades de Negócio ---
    ATENDIMENTO {
        uuid id_atendimento PK
        timestamp data_hora
        integer duracao_minutos
        uuid id_paciente FK
        uuid id_residente FK
        uuid id_preceptor FK
        uuid id_unidade FK
    }

    PROCEDIMENTO {
        uuid id_procedimento PK
        varchar codigo UK
        varchar nome
        integer tempo_medio_minutos
        nivel_risco_enum nivel_risco
        numeric media_tempo_procedimento
    }

    PROCEDIMENTO_REALIZADO {
        uuid id_atendimento PK, FK
        uuid id_procedimento PK, FK
        integer quantidade
        integer tempo_real_minutos
        timestamp data_hora_inicio
        text observacao
    }

    INTERNACAO {
        uuid id_internacao PK
        uuid id_paciente FK
        uuid id_unidade FK
        timestamp data_hora_entrada
        timestamp data_hora_saida
        text motivo
    }

    AUDITORIA_ATENDIMENTO {
        uuid id_auditoria PK
        uuid id_atendimento
        varchar operacao
        jsonb dados_antigos
        jsonb dados_novos
        timestamp alterado_em
    }

    FATURAMENTO {
        uuid id_faturamento PK
        uuid id_atendimento FK
        uuid id_procedimento FK
        numeric valor
        date data_emissao
    }

    ESCALA {
        uuid id_escala PK
        dia_semana_enum dia_semana
        turno_enum turno
        uuid id_unidade FK
        uuid id_residente FK
        uuid id_preceptor FK
    }

    UNIDADE {
        uuid id_unidade PK
        varchar nome
        varchar tipo
        integer capacidade_leitos
    }

    %% --- Relacionamentos e Cardinalidades ---
    %% Especialização Core (1:0..1 — joined table inheritance)
    %% PROFISSIONAL -> PRECEPTOR/RESIDENTE é disjunta: a coluna `papel`, travada
    %% por CHECK, + FK composta (id_pessoa, papel) -> PROFISSIONAL(id_pessoa,
    %% papel_atual) impedem a mesma pessoa de ocupar os dois papéis ao mesmo tempo.
    PESSOA ||--o| PACIENTE : "pode ser"
    PESSOA ||--o| PROFISSIONAL : "pode ser"
    PROFISSIONAL ||--o| PRECEPTOR : "atua como"
    PROFISSIONAL ||--o| RESIDENTE : "atua como"

    %% Relacionamentos de Atendimento
    PACIENTE ||--o{ ATENDIMENTO : "recebe"
    RESIDENTE ||--o{ ATENDIMENTO : "executa"
    PRECEPTOR ||--o{ ATENDIMENTO : "supervisiona"
    UNIDADE ||--o{ ATENDIMENTO : "ocorre em"

    %% Atendimento N:M Procedimento via tabela associativa
    %% (0,N) e não (1,N): um mínimo de 1 filho não é expressável por FK — exigiria trigger.
    ATENDIMENTO ||--o{ PROCEDIMENTO_REALIZADO : "possui"
    PROCEDIMENTO ||--o{ PROCEDIMENTO_REALIZADO : "e_realizado_em"

    %% Faturamento: no máximo um por procedimento realizado (UNIQUE na FK composta).
    %% A FK usa ON DELETE RESTRICT: o banco recusa apagar procedimento já faturado.
    PROCEDIMENTO_REALIZADO ||--o| FATURAMENTO : "e_faturado_por"

    %% Escalas e Unidades
    %% UNIQUE(id_unidade, dia_semana, turno, id_residente): um residente só pode ter
    %% um preceptor supervisor por unidade/dia/turno. id_preceptor fica fora da chave
    %% de propósito — assim um mesmo preceptor pode supervisionar vários residentes.
    RESIDENTE ||--o{ ESCALA : "cumpre"
    PRECEPTOR ||--o{ ESCALA : "supervisiona"
    UNIDADE ||--o{ ESCALA : "sedia"

    %% --- Etapa 2 ---
    %% INTERNACAO: paciente internado numa unidade; saída NULL = ainda internado.
    PACIENTE ||--o{ INTERNACAO : "é internado em"
    UNIDADE ||--o{ INTERNACAO : "abriga"

    %% AUDITORIA_ATENDIMENTO é preenchida pelo trigger trg_audita_atendimento.
    %% NÃO tem FK para ATENDIMENTO de propósito: o log de auditoria sobrevive
    %% mesmo que o atendimento original seja apagado (por isso a relação é
    %% tracejada/lógica, não uma FK real).
    ATENDIMENTO ||..o{ AUDITORIA_ATENDIMENTO : "auditado por"
```

---

## Notas da Etapa 2

O diagrama acima já reflete as adições da Etapa 2:

- **`ATENDIMENTO.id_unidade`** — a unidade onde o atendimento ocorreu (a Etapa 1 não amarrava atendimento a unidade). Alimenta `vw_estatisticas_atendimentos_mensal`.
- **`PROCEDIMENTO_REALIZADO.data_hora_inicio`** — horário real de início do procedimento; base do cálculo de `sp_calcular_tempo_medio_espera`.
- **`PROCEDIMENTO.media_tempo_procedimento`** — mantida automaticamente pelo trigger `trg_atualiza_media_procedimentos`.
- **`INTERNACAO`** — entidade nova; `data_hora_saida IS NULL` marca paciente ainda internado. Base de `vw_pacientes_internados`.
- **`AUDITORIA_ATENDIMENTO`** — log escrito pelo trigger `trg_audita_atendimento` (INSERT/UPDATE/DELETE em `ATENDIMENTO`), sem FK de propósito.

Detalhamento em [`../04-banco/04-procedures.md`](../04-banco/04-procedures.md), [`05-views.md`](../04-banco/05-views.md) e [`06-triggers.md`](../04-banco/06-triggers.md).
