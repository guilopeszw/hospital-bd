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
| GET | `/api/dashboard/summary` | contadores do painel |
| GET/POST | `/api/pacientes` | lista / cadastra paciente |
| GET | `/api/pacientes/<id>/atendimentos` | atendimentos de um paciente |
| GET | `/api/profissionais` | residentes + preceptores |
| GET/POST | `/api/atendimentos` | lista / registra atendimento |
| GET | `/api/unidades`, `/api/procedimentos`, `/api/escalas` | listagens de apoio |
| GET | `/api/analytics/ranking-residentes` | ranking de residentes |
| GET | `/api/analytics/preceptores-mais-atendimentos` | preceptores +5 no mês |
| GET | `/api/analytics/plantoes-mes` | plantões por unidade/residente |
| GET | `/api/analytics/pacientes-sem-risco-alto` | pacientes sem procedimento ALTO |
| GET | `/api/analytics/tempo-medio-residente` | tempo médio por residente |

Persistência verificada ponta a ponta: `POST /pacientes` e `POST /atendimentos`
gravam no Postgres e sobrevivem a restart da API.

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
- **Schema:** a API acompanha o schema da branch `main` (Etapa 1). Se `main` for
  reconciliada com `main-parte2`, o `POST /atendimentos` precisará passar a
  informar `id_unidade` (coluna `NOT NULL` na Etapa 2).
