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
    }

    PROCEDIMENTO {
        uuid id_procedimento PK
        varchar codigo UK
        varchar nome
        integer tempo_medio_minutos
        nivel_risco_enum nivel_risco
    }

    PROCEDIMENTO_REALIZADO {
        uuid id_atendimento PK, FK
        uuid id_procedimento PK, FK
        integer quantidade
        integer tempo_real_minutos
        text observacao
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
```
