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

## Por que pessimista e não otimista

Optou-se por lock pessimista (`FOR UPDATE`) em vez de otimista (coluna de
versão) porque a disputa aqui é sobre um recurso pontual e de vida curta —
a checagem+insert de uma escala leva milissegundos, então o custo de
segurar um lock de linha por esse tempo é baixo, e evita o retrabalho de um
lock otimista (que exigiria a segunda transação recomeçar do zero após
descobrir o conflito só na hora do commit).