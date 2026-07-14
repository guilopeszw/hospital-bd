import os
import sys
import re
import shutil
from contextlib import redirect_stdout
from io import StringIO
from datetime import datetime

from src.etapa1.atendimento_crud import (
    inserir_atendimento,
    listar_atendimentos_paciente,
    listar_procedimentos_atendimento,
    atualizar_paciente,
    remover_procedimento_realizado,
    tempo_medio_por_residente,
    ranking_residentes,
    preceptores_mais_atendimentos_mes,
    plantoes_por_unidade_mes,
    pacientes_sem_procedimento_risco_alto,
)

_RE_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)


def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _width():
    return min(shutil.get_terminal_size().columns, 100)


def _sep(char="─"):
    return char * (_width() - 2)


# ponytail: box-drawing table, no rich/tabulate dep
def _print_table(rows, columns):
    if not rows:
        _warn("Nenhum resultado encontrado.")
        return

    ncols = len(columns)
    col_widths = []
    for i, (_, _, weight) in enumerate(columns):
        raw = _width() - 4 - ncols - 1
        w = max(int(raw * weight / 100), len(columns[i][0]) + 2)
        col_widths.append(w)

    def _row(vals):
        return " │ ".join(v.ljust(w) for v, w in zip(vals, col_widths))

    sep = "─" * (sum(col_widths) + ncols + 2)
    hdr = _row([c[0] for c in columns])
    print(f"  ┌{sep}┐")
    print(f"  │ {hdr} │")
    print(f"  ├{sep}┤")
    for row in rows:
        vals = []
        for (_, key, _), w in zip(columns, col_widths):
            v = str(row.get(key, ""))
            if len(v) > w - 2:
                v = v[: w - 5] + "..."
            vals.append(v)
        print(f"  │ {_row(vals)} │")
    print(f"  └{sep}┘")


def _ok(msg):
    print(f"  ✓ {msg}")


def _warn(msg):
    print(f"  ⚠ {msg}")


def _call(fn, *a, **kw):
    buf = StringIO()
    with redirect_stdout(buf):
        r = fn(*a, **kw)
    return r, buf.getvalue()


def _input(prompt, required=True, validator=None, err="Valor inválido."):
    while True:
        val = input(f"  {prompt}: ").strip()
        if required and not val:
            _warn("Campo obrigatório.")
            continue
        if not required and not val:
            return None
        if validator and not validator(val):
            _warn(err)
            continue
        return val


def _pause():
    input("  Pressione Enter para continuar... ")


def _is_uuid(s):
    return bool(_RE_UUID.match(s))


def _is_int(s):
    return s.isdigit() or (s.startswith("-") and s[1:].isdigit())


# ── Menu screens ──────────────────────────────────────────────

def _screen_ranking():
    _clear()
    print("  Ranking de Residentes por Atendimentos\n")
    rows, _ = _call(ranking_residentes)
    _print_table(rows, [
        ("Residente", "residente", 60),
        ("Total", "total_atendimentos", 40),
    ])
    _pause()


def _screen_tempo_medio():
    _clear()
    print("  Tempo Médio de Atendimento por Residente\n")
    rows, _ = _call(tempo_medio_por_residente)
    _print_table(rows, [
        ("Residente", "residente", 45),
        ("Tempo Médio (min)", "tempo_medio_minutos", 25),
        ("Atendimentos", "total_atendimentos", 30),
    ])
    _pause()


def _screen_plantoes():
    _clear()
    print("  Plantões por Unidade no Mês Corrente\n")
    rows, _ = _call(plantoes_por_unidade_mes)
    _print_table(rows, [
        ("Unidade", "unidade", 35),
        ("Residente", "residente", 35),
        ("Total", "total_plantoes_no_mes", 30),
    ])
    _pause()


def _screen_pacientes_sem_risco():
    _clear()
    print("  Pacientes sem Procedimento de Alto Risco\n")
    rows, _ = _call(pacientes_sem_procedimento_risco_alto)
    _print_table(rows, [
        ("Paciente", "paciente", 55),
        ("Convênio", "num_convenio", 45),
    ])
    _pause()


def _screen_atendimentos_paciente():
    _clear()
    print("  Listar Atendimentos de um Paciente\n")
    pid = _input("ID do paciente (UUID)", validator=_is_uuid, err="UUID inválido")
    _clear()
    print(f"  Atendimentos do Paciente {pid}\n")
    rows, _ = _call(listar_atendimentos_paciente, pid)
    _print_table(rows, [
        ("Data/Hora", "data_hora", 25),
        ("Duração", "duracao_minutos", 10),
        ("Paciente", "paciente", 20),
        ("Residente", "residente", 20),
        ("Preceptor", "preceptor", 25),
    ])
    _pause()


def _screen_procedimentos():
    _clear()
    print("  Listar Procedimentos de um Atendimento\n")
    aid = _input("ID do atendimento (UUID)", validator=_is_uuid, err="UUID inválido")
    _clear()
    print(f"  Procedimentos do Atendimento {aid}\n")
    rows, _ = _call(listar_procedimentos_atendimento, aid)
    _print_table(rows, [
        ("Procedimento", "procedimento", 25),
        ("Risco", "nivel_risco", 8),
        ("Qtd", "quantidade", 7),
        ("Tempo", "tempo_real_minutos", 10),
        ("Obs", "observacao", 25),
        ("Faturado", "faturado", 10),
        ("Valor", "valor_faturado", 15),
    ])
    _pause()


def _screen_preceptores_mes():
    _clear()
    print("  Preceptores com +5 Atendimentos no Mês\n")
    ano = _input("Ano (ex: 2025)", validator=lambda x: x.isdigit() and 2000 <= int(x) <= 2100, err="Ano inválido (2000-2100)")
    mes = _input("Mês (1-12)", validator=lambda x: x.isdigit() and 1 <= int(x) <= 12, err="Mês inválido")
    _clear()
    print(f"  Preceptores com +5 Atendimentos — {mes}/{ano}\n")
    rows, _ = _call(preceptores_mais_atendimentos_mes, int(ano), int(mes))
    _print_table(rows, [
        ("Preceptor", "preceptor", 60),
        ("Total Atend.", "total_atendimentos", 40),
    ])
    _pause()


def _screen_remover():
    _clear()
    print("  Remover Procedimento Realizado\n")
    aid = _input("ID do atendimento (UUID)", validator=_is_uuid, err="UUID inválido")
    pid = _input("ID do procedimento (UUID)", validator=_is_uuid, err="UUID inválido")
    conf = _input('Confirma? digite "sim"', required=True)
    if conf.lower() == "sim":
        _, out = _call(remover_procedimento_realizado, aid, pid)
        if out.strip():
            print(out)
        else:
            _ok("Operação concluída.")
    else:
        _warn("Cancelado.")
    _pause()


def _screen_atualizar():
    _clear()
    print("  Atualizar Dados de Paciente\n")
    pid = _input("ID do paciente (UUID)", validator=_is_uuid, err="UUID inválido")
    convenio = _input("Novo convênio", required=False)
    alergias = _input("Novas alergias", required=False)
    if not convenio and not alergias:
        _warn("Nada a atualizar.")
    else:
        _, out = _call(atualizar_paciente, pid, novo_convenio=convenio, novas_alergias=alergias)
        if out.strip():
            print(out)
        else:
            _ok("Paciente atualizado.")
    _pause()


def _screen_inserir():
    _clear()
    print("  Inserir Novo Atendimento\n")
    dh = _input("Data e hora (YYYY-MM-DD HH:MM)", validator=lambda x: len(x) >= 16, err="Formato: YYYY-MM-DD HH:MM")
    dur = _input("Duração (minutos)", validator=_is_int, err="Número inteiro")
    pac = _input("ID do paciente (UUID)", validator=_is_uuid, err="UUID inválido")
    res = _input("ID do residente (UUID)", validator=_is_uuid, err="UUID inválido")
    pre = _input("ID do preceptor (UUID)", validator=_is_uuid, err="UUID inválido")
    _clear()
    _, out = _call(inserir_atendimento, dh, int(dur), pac, res, pre)
    if out.strip():
        print(out)
    else:
        _ok("Atendimento criado.")
    _pause()


# ── Menu ──────────────────────────────────────────────────────

def _menu():
    items = [
        ("1", "Ranking de Residentes", _screen_ranking),
        ("2", "Tempo Médio por Residente", _screen_tempo_medio),
        ("3", "Plantões por Unidade (mês corrente)", _screen_plantoes),
        ("4", "Pacientes sem Procedimento de Alto Risco", _screen_pacientes_sem_risco),
        ("5", "Listar Atendimentos de um Paciente", _screen_atendimentos_paciente),
        ("6", "Listar Procedimentos de um Atendimento", _screen_procedimentos),
        ("7", "Preceptores com +5 Atendimentos no Mês", _screen_preceptores_mes),
        ("8", "Remover Procedimento Realizado", _screen_remover),
        ("9", "Atualizar Dados de Paciente", _screen_atualizar),
        ("10", "Inserir Novo Atendimento", _screen_inserir),
        ("0", "Sair", None),
    ]

    while True:
        _clear()
        w = _width()
        print()
        print(f"  ╔{'═' * (w - 4)}╗")
        print(f"  ║{' HOSPITAL UNIVERSITÁRIO — Dra. Yuska Maritan Brito ':.^{w - 4}}║")
        print(f"  ║{' SISTEMA DE GESTÃO HOSPITALAR — Etapa 1 ':.^{w - 4}}║")
        print(f"  ╠{'═' * (w - 4)}╣")
        for key, label, _ in items:
            side = " " if key == "0" else " "
            print(f"  ║  {key}. {label.ljust(w - 9)}{side}║")
        print(f"  ╚{'═' * (w - 4)}╝")
        print()

        choice = input("  Opção: ").strip()
        matched = False
        for key, _, handler in items:
            if choice == key:
                matched = True
                if handler:
                    try:
                        handler()
                    except (EOFError, KeyboardInterrupt):
                        print()
                        _ok("Até logo!")
                        return
                    except Exception as e:
                        _warn(f"Erro inesperado: {e}")
                        _pause()
                else:
                    _ok("Até logo!")
                    return
                break
        if not matched:
            _warn("Opção inválida.")
            _pause()


def main():
    try:
        _menu()
    except (EOFError, KeyboardInterrupt):
        print()
        _ok("Até logo!")
        sys.exit(0)


if __name__ == "__main__":
    main()
