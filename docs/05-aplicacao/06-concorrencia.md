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

## Solução: lock pessimista

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

### Log esperado (exemplo)

```
[10:02:01.001] [thread-A] tentando travar a linha do residente ...
[10:02:01.002] [thread-A] lock adquirido — checando conflito de escala…
[10:02:01.052] [thread-B] tentando travar a linha do residente ...   <- fica bloqueada aqui
[10:02:01.502] [thread-A] OK — escala ... criada. Commitando (lock será liberado agora).
[10:02:01.503] [thread-B] lock adquirido — checando conflito de escala…
[10:02:01.503] [thread-B] CONFLITO — residente já escalado nesse dia/turno/unidade. Abortando.

--- resultado final ---
thread-A: ('sucesso', '...')
thread-B: ('rejeitada', 'Residente ... já está escalado em segunda/noite nessa unidade.')

OK — o lock pessimista impediu a dupla escala do mesmo residente no mesmo slot.
```

A demo termina com um `assert` conferindo que houve exatamente 1 sucesso e
1 rejeição — nunca as duas escalas indo pra frente, nunca as duas caindo
num erro de banco não tratado.

## Por que pessimista e não otimista

Optou-se por lock pessimista (`FOR UPDATE`) em vez de otimista (coluna de
versão) porque a disputa aqui é sobre um recurso pontual e de vida curta —
a checagem+insert de uma escala leva milissegundos, então o custo de
segurar um lock de linha por esse tempo é baixo, e evita o retrabalho de um
lock otimista (que exigiria a segunda transação recomeçar do zero após
descobrir o conflito só na hora do commit).