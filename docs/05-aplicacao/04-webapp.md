# Webapp — API Flask + Painel Web

Front-end web opcional (o enunciado permite CLI, web ou desktop). Uma API REST em
Flask sobre o mesmo Postgres da CLI, e um painel estático em HTML/CSS/JS puro.

**Localização:** [`../../webapp/`](../../webapp/)

| Camada | Arquivo | Stack |
|---|---|---|
| API | [`webapp/api/app.py`](../../webapp/api/app.py) | Flask + flask-cors + psycopg2 (SQL parametrizado) |
| Front | [`webapp/frontend/index.html`](../../webapp/frontend/index.html) + `css/` + `js/` | HTML/CSS/JS puro, sem framework |

---

## Como rodar

```bash
# 1. Banco no ar + schema/seeds (ver 06-infraestrutura/01-docker.md)

# 2. API
cd webapp/api
pip install -r requirements.txt
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" python app.py
# sobe em http://localhost:5055  (env PORT sobrescreve)

# 3. Front: abrir webapp/frontend/index.html no navegador
```

> **Porta 5055, não 5000.** No macOS o AirPlay Receiver (Control Center) ocupa a
> `5000` e responde `403` a tudo — o front nunca alcançaria a API. Por isso a API
> roda em `5055`, e o `API_BASE` do front aponta pra ela.

---

## Endpoints

| Método | Rota | Retorna |
|---|---|---|
| GET | `/api/health` | status do banco (usado pelo indicador da sidebar) |
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

Persistência verificada ponta a ponta (curl manual + `tests/integration/test_webapp.py`,
68 testes): `POST/PUT/DELETE` gravam no Postgres e sobrevivem a restart da API.

### Etapa 2 no backend do webapp

Até a rodada anterior de testes, o webapp era um CRUD raso sobre as tabelas base —
nenhuma rota chamava procedure, lia view ou tinha como disparar os triggers que
dependem de INSERT em ESCALA/PROCEDIMENTO_REALIZADO. Fechado agora:

- **Procedures**: `sp_registrar_atendimento_completo` (via `POST /atendimentos` com
  `procedimentos`), `sp_reajustar_escala` (`POST /escalas/reajustar`),
  `sp_calcular_tempo_medio_espera` (`GET /analytics/tempo-medio-espera`).
- **Triggers**: `trg_atualiza_media_procedimentos` dispara em
  `POST /atendimentos/<id>/procedimentos` (dado real: uma chamada de teste mudou a
  média de um procedimento de `null` para um valor calculado). `trg_check_sobreposicao_escala`
  dispara em `POST /escalas` e devolve `409` com a mensagem do `RAISE EXCEPTION`.
- **Views**: as 3 views (`vw_pacientes_internados`, `vw_residentes_sem_supervisor`,
  `vw_estatisticas_atendimentos_mensal`) têm rota própria em `/api/views/*`, e as
  duas primeiras alimentam o dashboard.

**Bug real encontrado e corrigido nesse processo:** as duas rotas que chamam
procedures com efeito colateral (`sp_registrar_atendimento_completo`,
`sp_reajustar_escala`) inicialmente usavam o helper `query()` — que só faz `SELECT`
e nunca comita. O `INSERT`/`UPDATE` feito *dentro* da function rodava, mas era
descartado ao fechar a conexão sem commit; a API respondia `201`/`200` com um
resultado que não existia no banco. Corrigido trocando para o helper `execute()`
(que comita) nessas duas rotas — confirmado com uma query direta no Postgres
depois da chamada HTTP, não só pelo código de status.

---

## Segurança — XSS

O painel montava as tabelas com `innerHTML` interpolando dados da API. Como o
backend grava `nome`/`alergias`/`convênio` sem sanitizar, um paciente cadastrado
com `nome = <img src=x onerror=...>` teria o script **armazenado** e executado ao
renderizar a lista (XSS armazenado, atingindo qualquer usuário).

Correção: helper `esc()` (escapa `& < > " '`) aplicado em **todo** campo derivado
da API antes de ir para o DOM. Escape na saída — camada correta — em vez de
sanitizar no servidor (não corrompe `O'Brien & Souza`; as queries já são
parametrizadas, sem risco de SQLi).

---

## Notas de implementação

- **CORS** liberado (`flask-cors`) porque o front é servido como arquivo e chama a
  API em `localhost:5055`.
- **SQL parametrizado** (`%s` via psycopg2) em todas as rotas — sem concatenação.
- **Feedback de UI**: `scale(0.96)` no `:active` dos botões, transições
  específicas (nunca `transition: all`), `prefers-reduced-motion` respeitado.
- **Schema:** a API acompanha o schema unificado (Etapa 1 + Etapa 2). O
  `POST /atendimentos` exige `id_unidade` (coluna `NOT NULL`), e o formulário do
  painel tem um select de unidade populado por `GET /api/unidades`.
