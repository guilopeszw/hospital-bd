# Concorrência e transações (Etapa 2 — item 6)

**Localização:** [`../../src/etapa2/concorrencia.py`](../../src/etapa2/concorrencia.py)

## Cenário

Duas transações tentam, ao mesmo tempo, escalar o **mesmo residente** para
o **mesmo dia/turno/unidade** — só o preceptor muda entre as duas
tentativas.

Sem controle de concorrência, cada transação faria de forma independente:
"checa se já existe conflito → se não existe, insere". Como o `SELECT` de
checagem de uma pode rodar antes do `INSERT` da outra, as duas conseguem
ler "sem conflito" e seguir para o `INSERT`. O
`UNIQUE(id_unidade, dia_semana, turno, id_residente)` do banco ainda evita
a inconsistência final nos dados, mas quem perde a corrida recebe um
`IntegrityError` cru do driver, sem chance de tratar isso como uma regra de
negócio (ex.: devolver uma mensagem amigável, tentar outro horário, etc.).

## Solução 1 — lock pessimista

`escalar_residente_com_lock()` usa `SELECT ... FOR UPDATE` na linha de
`RESIDENTE` antes de checar conflito e inserir. A primeira transação a
chegar trava a linha e só libera no commit/rollback; a segunda fica
bloqueada esperando — e quando acorda, já enxerga a escala recém-criada
pela primeira, então é rejeitada com uma exceção de negócio
(`ConflitoEscalaError`), não um erro de banco.

```python
with Session.begin() as s:
    residente = s.execute(
        select(Residente).where(Residente.id_pessoa == id_residente).with_for_update()
    ).scalar_one_or_none()
    # ... checagem de conflito + insert, protegidos pelo lock ...
```

## Correção aplicada em `models.py`

Na primeira tentativa de rodar a demo apareceu um `FlushError: NULL identity
key` ao inserir a `Escala`. Causa: `Escala.id_escala` e
`Atendimento.id_atendimento` são UUID gerados no banco
(`DEFAULT uuid_generate_v4()` no DDL), mas o `models.py` não declarava esse
default do lado Python — então o SQLAlchemy não sabia recuperar o valor
gerado depois do `INSERT`. Corrigido adicionando
`default=lambda: str(uuid.uuid4())` nas duas colunas, gerando o UUID no
Python em vez de depender do retorno do banco.

## Demo

```bash
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" \
  python -m src.etapa2.concorrencia
```

Dispara duas threads quase simultâneas (`thread-A`, `thread-B`) chamando
`escalar_residente_com_lock` com o mesmo residente/dia/turno/unidade e
preceptores diferentes. Um `atraso_simulado` de meio segundo entre travar a
linha e commitar deixa o race window visível nos logs — sem ele a disputa
seria rápida demais para observar no terminal.

### Log real (rodado em 01/08/2026)

```
[14:41:17.665] [thread-A] tentando travar a linha do residente c1111111-1111-1111-1111-111111111111…
[14:41:17.669] [thread-A] lock adquirido — checando conflito de escala…
[14:41:17.716] [thread-B] tentando travar a linha do residente c1111111-1111-1111-1111-111111111111…
[14:41:18.179] [thread-A] OK — escala 5363ad82-d95f-488f-b5ed-7565722d33b9 criada. Commitando (lock será liberado agora).
[14:41:18.183] [thread-B] lock adquirido — checando conflito de escala…
[14:41:18.694] [thread-B] CONFLITO — residente já escalado nesse dia/turno/unidade. Abortando.

--- resultado final ---
thread-A: ('sucesso', '5363ad82-d95f-488f-b5ed-7565722d33b9')
thread-B: ('rejeitada', 'Residente c1111111-1111-1111-1111-111111111111 já está escalado em segunda/noite nessa unidade.')

OK — o lock pessimista impediu a dupla escala do mesmo residente no mesmo slot.
```

Repara no timing: `thread-B` chega a tentar travar a linha às `17.716`, mas só
consegue o lock às `18.183` — ou seja, ficou bloqueada ~467ms esperando a
`thread-A` liberar (ela só libera depois do `atraso_simulado` de 0.5s +
commit). Isso confirma que o `FOR UPDATE` está de fato serializando as
duas tentativas, e não é coincidência que só uma tenha passado.

A demo termina com um `assert` conferindo que houve exatamente 1 sucesso e
1 rejeição — nunca as duas escalas indo pra frente, nunca as duas caindo
num erro de banco não tratado.

## Solução 2 — controle otimista

`escalar_residente_otimista()` faz o oposto: **não segura lock nenhum**. As
duas transações seguem em paralelo, fazem a checagem best-effort e tentam o
`INSERT`. A `UNIQUE(id_unidade, dia_semana, turno, id_residente)` é o
detector de conflito — quem perde a corrida recebe o `IntegrityError` no
flush, que é capturado e traduzido para o mesmo `ConflitoEscalaError` de
negócio (sem vazar erro cru do driver).

```python
try:
    with Session.begin() as s:
        # checagem best-effort (sem lock) + insert
        s.add(nova)
        s.flush()   # a UNIQUE é validada aqui; se a outra ganhou, estoura
except IntegrityError:
    raise ConflitoEscalaError(...)   # perdeu a corrida, rejeita limpo
```

O conflito é detectado **depois**, no momento da escrita — mais
concorrência (ninguém espera), ao custo de retrabalho de quem perde.

### Log real (controle otimista)

```
===== DEMO: controle otimista (sem lock, UNIQUE detecta) =====
[11:50:20.281] [thread-A] sem lock — checando conflito (best-effort) e tentando inserir…
[11:50:20.334] [thread-B] sem lock — checando conflito (best-effort) e tentando inserir…
[11:50:20.796] [thread-A] OK — escala d4b7366b-…-8cf14c9cb70f criada. Commitando.
[11:50:20.843] [thread-B] CONFLITO detectado na escrita (UNIQUE) — perdeu a corrida. Rejeitando.

--- resultado final ---
thread-A: ('sucesso', 'd4b7366b-…')
thread-B: ('rejeitada', 'Residente c1111111-… já está escalado em terca/noite nessa unidade.')
```

Repara na diferença de comportamento em relação ao pessimista: aqui as duas
threads entram na seção crítica **quase juntas** (`20.281` e `20.334`) —
ninguém fica bloqueado. A `thread-B` só descobre o conflito na hora do
`INSERT` (`20.843`), quando a UNIQUE dispara. No log pessimista, ao
contrário, a `thread-B` ficou ~467ms **parada** esperando o lock antes de
sequer checar.

## Pessimista vs. otimista — quando usar cada um

| | Pessimista (`FOR UPDATE`) | Otimista (UNIQUE detecta) |
|---|---|---|
| Lock | trava a linha do residente até o commit | nenhum |
| Segunda transação | **espera** o lock liberar | roda em paralelo, falha na escrita |
| Detecta o conflito | antes (na checagem, já sob lock) | depois (no `INSERT`) |
| Custo | contenção: threads serializam e esperam | retrabalho: quem perde refaz/rejeita |
| Melhor quando | conflito é **provável** (muita disputa no mesmo slot) | conflito é **raro** (disputa é exceção) |

Ambas as estratégias entregam a mesma garantia — nunca duas escalas do mesmo
residente no mesmo slot, e nunca um erro cru de banco escapando — e a
`UNIQUE` do schema é a rede de segurança final nos dois casos. Para o volume
deste sistema (escala hospitalar, poucos conflitos reais), o **otimista**
tende a ser mais eficiente; o **pessimista** compensa se o mesmo slot passar
a ser muito disputado.

Rodar as duas demos em sequência:

```bash
DATABASE_URL="dbname=hospital_db user=postgres password=password host=localhost port=5433" \
  python -m src.etapa2.concorrencia
```