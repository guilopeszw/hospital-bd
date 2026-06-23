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
        varchar titulacao
    }

    RESIDENTE {
        uuid id_pessoa PK, FK
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
        integer tempo_medio_execucao
    }

    ATENDIMENTO_PROCEDIMENTO {
        uuid id_atendimento PK, FK
        uuid id_procedimento PK, FK
        integer quantidade
        varchar resultado
    }

    ESCALA_PLANTAO {
        uuid id_escala PK
        date data_escala
        turno_enum turno
        uuid id_unidade FK
        uuid id_profissional FK
    }

    UNIDADE_HOSPITALAR {
        uuid id_unidade PK
        varchar nome
        varchar setor
    }

    INTERNACAO {
        uuid id_internacao PK
        timestamp data_entrada
        timestamp data_saida
        varchar leito
        text motivo
        uuid id_atendimento FK
    }

    %% --- Relacionamentos e Cardinalidades ---
    %% Especialização Core (1:0..1 devido ao Joined Table)
    PESSOA ||--o| PACIENTE : "pode ser"
    PESSOA ||--o| PROFISSIONAL : "pode ser"
    PROFISSIONAL ||--o| PRECEPTOR : "pode ser"
    PROFISSIONAL ||--o| RESIDENTE : "pode ser"

    %% Relacionamentos de Atendimento
    PACIENTE ||--o{ ATENDIMENTO : "recebe"
    RESIDENTE ||--o{ ATENDIMENTO : "executa"
    PRECEPTOR ||--o{ ATENDIMENTO : "supervisiona"

    %% Atendimento N:M Procedimento via Tabela Associativa
    ATENDIMENTO ||--|{ ATENDIMENTO_PROCEDIMENTO : "possui"
    PROCEDIMENTO ||--|{ ATENDIMENTO_PROCEDIMENTO : "e_realizado_em"

    %% Escalas e Unidades
    PROFISSIONAL ||--o{ ESCALA_PLANTAO : "cumpre"
    UNIDADE_HOSPITALAR ||--o{ ESCALA_PLANTAO : "sedia"

    %% Internações (Geradas a partir de um Atendimento)
    ATENDIMENTO ||--o| INTERNACAO : "pode_gerar"
    