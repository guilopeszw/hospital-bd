# Webapp — API Flask + Painel Web

Front-end web opcional (o enunciado permite CLI, web ou desktop). Uma API REST em
Flask sobre o mesmo Postgres da CLI, e um painel estático em HTML/CSS/JS puro
(sem build step, sem framework).

**Localização:** [`../../webapp/`](../../webapp/)

| Camada | Entrada | Stack |
|---|---|---|
| API | [`webapp/api/app.py`](../../webapp/api/app.py) | Flask + flask-cors + psycopg2 (SQL parametrizado) + SQLAlchemy (só na rota ORM) |
| Front | [`webapp/frontend/index.html`](../../webapp/frontend/index.html) | HTML/CSS/JS puro, ES modules nativos |

---

## Como se conectam

O front é um arquivo estático (`index.html`) aberto direto no navegador — não tem
servidor próprio. Todo dado vem de `fetch()` para a API Flask em
`http://localhost:5055/api/...` (constante `API_BASE` em
[`js/core/api.js`](../../webapp/frontend/js/core/api.js)). Por isso a API precisa
de CORS liberado (`flask-cors`): a origem do front (`file://` ou outra porta) é
diferente da origem da API.

Fluxo de uma tela típica (ex: clicar em "Pacientes" na sidebar):

1. `js/core/nav.js` troca a view visível e chama `carregarView("pacientes")`.
2. `js/core/viewLoader.js` despacha pro loader certo, com cache de sessão (não
   recarrega a mesma view duas vezes, exceto "visão geral").
3. `js/views/pacientes.js` faz `apiGet("/pacientes")`.
4. Flask roteia pro blueprint `webapp/api/routes/pacientes.py`, que chama
   `db.query(...)` (SQL parametrizado direto, sem ORM) e devolve JSON.
5. O JS monta a tabela via `format.js#tabela()` e injeta no DOM — todo campo
   passa por `esc()` antes (ver seção de segurança).

---

## Como rodar

```bash
# 1. Banco no ar + schema/seeds (ver 06-infraestrutura/01-docker.md)

# 2. API (dependências já vêm do requirements.txt da raiz do repo)
cd webapp/api
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" python app.py
# sobe em http://localhost:5055  (env PORT sobrescreve)

# 3. Front: abrir webapp/frontend/index.html no navegador
```

> **Porta 5055, não 5000.** No macOS o AirPlay Receiver (Control Center) ocupa a
> `5000` e responde `403` a tudo — o front nunca alcançaria a API. Por isso a API
> roda em `5055`, e o `API_BASE` do front aponta pra ela.

---

## Backend — `webapp/api/`

```
webapp/api/
  app.py              # entry point: cria o Flask app, CORS, registra os blueprints
  db.py               # get_connection, query(), execute(), api_error() — usados por todos os blueprints
  routes/
    dashboard.py      # GET /api/dashboard/summary
    pacientes.py       # /api/pacientes*
    profissionais.py   # /api/profissionais
    atendimentos.py     # /api/atendimentos* (inclui procedimentos realizados)
    faturamento.py      # POST /api/faturamentos
    unidades.py          # /api/unidades, /api/procedimentos
    escalas.py            # /api/escalas*
    analytics.py           # /api/analytics/* — SQL puro + stored procedures
    analytics_orm.py        # /api/orm/* — chama src/etapa2/consultas_avancadas.py
    views.py                 # /api/views/* — views da Etapa 2
    health.py                 # GET /api/health
```

Cada blueprint é um arquivo Flask `Blueprint` independente com as rotas de um
domínio; `app.py` só importa e registra (`app.register_blueprint(...)`). `db.py`
concentra a conexão e os dois helpers (`query` para SELECT, `execute` para
INSERT/UPDATE/DELETE — só `execute()` comita) usados pelo resto do backend.

**Detalhe de import:** `webapp/api` não é um pacote Python instalado, e
`tests/integration/test_webapp.py` carrega `app.py` direto por caminho de
arquivo (`importlib`), não por `import webapp.api.app`. Por isso `app.py` insere
o próprio diretório em `sys.path` antes de importar `db`/`routes` — sem isso,
esses imports locais quebrariam dependendo de como o módulo é carregado.
`routes/analytics_orm.py` faz o mesmo truque, mas subindo até a raiz do repo,
porque ele importa `src.etapa2.consultas_avancadas` — o único blueprint que sai
do mundo "SQL cru" e chama a camada ORM da Etapa 2.

### Endpoints

| Método | Rota | Retorna |
|---|---|---|
| GET | `/api/health` | status do banco (indicador da sidebar) |
| GET | `/api/dashboard/summary` | contadores do painel — inclui `pacientes_internados` e `residentes_sem_supervisor`, lidos das views da Etapa 2 |
| GET/POST | `/api/pacientes` | lista / cadastra paciente |
| PUT | `/api/pacientes/<id_paciente>` | atualiza convênio/alergias/grupo sanguíneo |
| GET | `/api/pacientes/<id_paciente>/atendimentos` | atendimentos de um paciente |
| GET/POST | `/api/profissionais` | lista / cadastra residente ou preceptor (`tipo` no body) |
| GET/POST | `/api/atendimentos` | lista / registra atendimento — `POST` com `procedimentos` no body delega para `sp_registrar_atendimento_completo` |
| GET/POST | `/api/atendimentos/<id_atendimento>/procedimentos` | lista / registra procedimento realizado — `POST` dispara `trg_atualiza_media_procedimentos` |
| DELETE | `/api/atendimentos/<id_atendimento>/procedimentos/<id_procedimento>` | remove procedimento realizado, bloqueado (`409`) se já faturado |
| POST | `/api/faturamentos` | fatura um procedimento realizado |
| GET/POST | `/api/unidades` | lista / cadastra unidade |
| GET | `/api/procedimentos` | catálogo de procedimentos |
| GET/POST | `/api/escalas` | lista / cadastra escala — `POST` dispara `trg_check_sobreposicao_escala` (barra o mesmo residente em duas unidades no mesmo dia/turno, `409`) |
| POST | `/api/escalas/reajustar` | move escalas de um residente entre slots via `sp_reajustar_escala` |
| GET | `/api/views/pacientes-internados` | `vw_pacientes_internados` |
| GET | `/api/views/residentes-sem-supervisor` | `vw_residentes_sem_supervisor` |
| GET | `/api/views/estatisticas-mensais` | `vw_estatisticas_atendimentos_mensal` |
| GET | `/api/analytics/ranking-residentes` | ranking de residentes |
| GET | `/api/analytics/preceptores-mais-atendimentos` | preceptores +5 no mês |
| GET | `/api/analytics/plantoes-mes` | plantões por unidade/residente |
| GET | `/api/analytics/pacientes-sem-risco-alto` | pacientes sem procedimento ALTO |
| GET | `/api/analytics/tempo-medio-residente` | tempo médio por residente |
| GET | `/api/analytics/tempo-medio-espera` | chama `sp_calcular_tempo_medio_espera()` |
| GET | `/api/orm/preceptores-supervisionaram-flamenguistas` | via ORM — preceptores de residentes que atenderam pacientes `is_flamengo` |
| GET | `/api/orm/ultimo-atendimento-por-paciente` | via ORM — último atendimento de cada paciente + procedimentos |
| GET | `/api/orm/percentual-alto-risco-por-residente` | via ORM — % de procedimentos ALTO por residente |

Persistência verificada ponta a ponta (curl manual + `tests/integration/test_webapp.py`,
68 testes): `POST/PUT/DELETE` gravam no Postgres e sobrevivem a restart da API.

### Etapa 2 no backend do webapp

- **Procedures**: `sp_registrar_atendimento_completo` (via `POST /atendimentos` com
  `procedimentos`), `sp_reajustar_escala` (`POST /escalas/reajustar`),
  `sp_calcular_tempo_medio_espera` (`GET /analytics/tempo-medio-espera`).
- **Triggers**: `trg_atualiza_media_procedimentos` dispara em
  `POST /atendimentos/<id>/procedimentos`. `trg_check_sobreposicao_escala`
  dispara em `POST /escalas` e devolve `409` com a mensagem do `RAISE EXCEPTION`.
- **Views**: as 3 views (`vw_pacientes_internados`, `vw_residentes_sem_supervisor`,
  `vw_estatisticas_atendimentos_mensal`) têm rota própria em `/api/views/*`, e as
  duas primeiras alimentam o dashboard.
- **ORM**: `routes/analytics_orm.py` é a única ponte entre o webapp e
  `src/etapa2/`, expondo as 3 consultas avançadas via ORM (item 5 do enunciado).
  O resto do backend (CRUD, procedures, triggers, views) continua em SQL puro via
  `psycopg2` — não foi migrado pro ORM, porque a reimplementação via ORM (item 4)
  já é demonstrada e testada separadamente em `src/etapa2/crud_orm.py` (ver
  [`03-orm.md`](03-orm.md)). O cenário de concorrência
  (`src/etapa2/concorrencia.py`, ver [`06-concorrencia.md`](06-concorrencia.md))
  também não tem rota HTTP — é uma demo de lock pessimista com log de terminal,
  não um recurso de produto.

**Bug real encontrado e corrigido nesse processo:** as duas rotas que chamam
procedures com efeito colateral (`sp_registrar_atendimento_completo`,
`sp_reajustar_escala`) inicialmente usavam o helper `query()` — que só faz `SELECT`
e nunca comita. O `INSERT`/`UPDATE` feito *dentro* da function rodava, mas era
descartado ao fechar a conexão sem commit; a API respondia `201`/`200` com um
resultado que não existia no banco. Corrigido trocando para o helper `execute()`
(que comita) nessas duas rotas — confirmado com uma query direta no Postgres
depois da chamada HTTP, não só pelo código de status.

---

## Frontend — `webapp/frontend/`

```
webapp/frontend/
  index.html
  css/
    base.css          # :root (paleta/fontes), reset, .muted/.empty
    layout.css         # .app, .sidebar, .nav, .main, .topbar, .vitals
    components.css       # stat-card, panel, table, badge, input, btn
    modal.css              # .modal, .toast
    responsive.css           # media query única (<= 880px)
  js/
    main.js           # entry point — único <script type="module"> do HTML
    core/
      api.js          # API_BASE, apiGet, apiPost
      format.js        # fmtData, fmtMoeda, esc (escape XSS), idChip, badges, tabela()
      constants.js       # TITULOS (nav), DIA_LEGIVEL, TURNO_LEGIVEL
      toast.js              # showToast()
      health.js              # relógio da topbar + checarSaude() (polling /api/health)
      nav.js                  # troca de view + delega o carregamento pro viewLoader
      viewLoader.js             # registro view → função de carga (cache de sessão)
    views/              # 1 arquivo por seção da sidebar
      visaoGeral.js, pacientes.js, profissionais.js,
      atendimentos.js, escalas.js, indicadores.js
    modals/              # 1 arquivo por modal + fechamento genérico
      pacienteModal.js, atendimentoModal.js, escalaModal.js, closeModals.js
```

ES modules nativos (`<script type="module" src="js/main.js">`), sem bundler —
o projeto é pequeno o bastante pra não justificar um passo de build. `main.js`
importa e inicializa cada módulo (`iniciarNav()`, `iniciarModalPaciente()`, etc);
os módulos de `views/` e `modals/` não se auto-executam, só exportam funções.

**Views mapeadas pra endpoints:**

| View (sidebar) | Módulo JS | Endpoints |
|---|---|---|
| Visão geral | `views/visaoGeral.js` | `/dashboard/summary`, `/atendimentos?limite=6` |
| Pacientes | `views/pacientes.js` | `/pacientes` (GET/busca), modal usa `POST /pacientes` |
| Equipe médica | `views/profissionais.js` | `/profissionais` |
| Atendimentos | `views/atendimentos.js` | `/atendimentos`, modal usa `/pacientes`, `/profissionais`, `/unidades`, `POST /atendimentos` |
| Escalas | `views/escalas.js` | `/escalas`, modal usa `/unidades`, `/profissionais`, `POST /escalas` |
| Indicadores | `views/indicadores.js` | `/analytics/*`, `/views/*`, `/orm/*` (7 painéis SQL/procedure/view + 3 painéis ORM) |

---

## Segurança — XSS

O painel monta as tabelas com `innerHTML` interpolando dados da API. Como o
backend grava `nome`/`alergias`/`convênio` sem sanitizar, um paciente cadastrado
com `nome = <img src=x onerror=...>` teria o script **armazenado** e executado ao
renderizar a lista (XSS armazenado, atingindo qualquer usuário).

Correção: helper `esc()` ([`js/core/format.js`](../../webapp/frontend/js/core/format.js),
escapa `& < > " '`) aplicado em **todo** campo derivado da API antes de ir para o
DOM. Escape na saída — camada correta — em vez de sanitizar no servidor (não
corrompe `O'Brien & Souza`; as queries já são parametrizadas, sem risco de SQLi).

---

## Notas de implementação

- **CORS** liberado (`flask-cors`) porque o front é servido como arquivo e chama a
  API em `localhost:5055`.
- **SQL parametrizado** (`%s` via psycopg2) em todas as rotas que não são a
  rota ORM — sem concatenação.
- **Feedback de UI**: `scale(0.96)` no `:active` dos botões, transições
  específicas (nunca `transition: all`), `prefers-reduced-motion` respeitado.
- **Schema:** a API acompanha o schema unificado (Etapa 1 + Etapa 2). O
  `POST /atendimentos` exige `id_unidade` (coluna `NOT NULL`), e o formulário do
  painel tem um select de unidade populado por `GET /api/unidades`.
- **Dependências**: `webapp/api` não tem `requirements.txt` próprio — usa o
  [`requirements.txt`](../../requirements.txt) da raiz do repo (já cobre Flask,
  flask-cors, psycopg2 e sqlalchemy).
