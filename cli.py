from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from gantt import render_gantt
from metrics import build_average_rows, build_comparison_analysis, build_result_rows
from models import Process, ScheduleResult
from sample_data import get_default_processes, load_processes_from_json
from schedulers import schedule_priority, schedule_sjf
from thread_sync import (
    build_patient_requests,
    render_synchronization_report,
    run_thread_synchronization_demo,
    suggest_initial_stock,
)


Column = tuple[str, Callable[[Any], str], str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulacao didatica de escalonamento de CPU com SJF e Priority Scheduling."
    )
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument(
        "--json",
        type=Path,
        help="Carrega processos a partir de um arquivo JSON.",
    )
    source_group.add_argument(
        "--interactive",
        action="store_true",
        help="Permite cadastrar processos manualmente pela CLI.",
    )

    parser.add_argument(
        "--sync-doctors",
        type=int,
        default=3,
        help="Quantidade de medicos (threads) na parte 2.",
    )
    parser.add_argument(
        "--sync-stock",
        type=int,
        default=None,
        help="Estoque inicial para a parte 2. Se omitido, e calculado automaticamente.",
    )
    parser.add_argument(
        "--sync-queue-source",
        choices=("sjf", "ps"),
        default="sjf",
        help="Algoritmo da parte 1 usado como fila de pacientes para a parte 2.",
    )
    parser.add_argument(
        "--sync-seed",
        type=int,
        default=None,
        help="Seed opcional para reproduzir as requisicoes de recursos da parte 2.",
    )
    return parser


def run_cli(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    processes = _load_processes_from_cli(args)
    report = build_report(
        processes,
        sync_queue_source=args.sync_queue_source,
        sync_doctors=args.sync_doctors,
        sync_stock=args.sync_stock,
        sync_seed=args.sync_seed,
    )
    print(report)
    return 0


def build_report(
    processes: Sequence[Process],
    sync_queue_source: str = "sjf",
    sync_doctors: int = 3,
    sync_stock: int | None = None,
    sync_seed: int | None = None,
) -> str:
    sjf_result = schedule_sjf(processes)
    ps_result = schedule_priority(processes)

    selected_source = sync_queue_source.strip().lower()
    if selected_source == "sjf":
        queue_source_result = sjf_result
    elif selected_source == "ps":
        queue_source_result = ps_result
    else:
        raise ValueError("sync_queue_source invalido. Use 'sjf' ou 'ps'.")

    patient_requests = build_patient_requests(queue_source_result, seed=sync_seed)
    initial_stock = sync_stock if sync_stock is not None else suggest_initial_stock(patient_requests)
    unsafe_result = run_thread_synchronization_demo(
        patient_requests,
        doctor_count=sync_doctors,
        initial_stock=initial_stock,
        use_lock=False,
    )
    safe_result = run_thread_synchronization_demo(
        patient_requests,
        doctor_count=sync_doctors,
        initial_stock=initial_stock,
        use_lock=True,
    )

    lines: list[str] = [
        "SIMULACAO EDUCACIONAL DE ESCALONAMENTO DE CPU",
        "Analogia hospitalar opcional: nomes podem representar pacientes, mas a logica e de processos.",
        "",
        _section_title("Entrada original"),
        _render_input_table(processes),
        "",
        _render_schedule_section(sjf_result),
        "",
        _render_schedule_section(ps_result),
        "",
        _section_title("Comparacao final"),
    ]
    lines.extend(f"- {line}" for line in build_comparison_analysis(processes, sjf_result, ps_result))
    lines.extend(
        [
            "",
            render_synchronization_report(
                source_algorithm_name=queue_source_result.algorithm_name,
                patient_requests=patient_requests,
                unsafe_result=unsafe_result,
                safe_result=safe_result,
            ),
        ]
    )
    return "\n".join(lines)


def _render_schedule_section(result: ScheduleResult) -> str:
    average_rows = build_average_rows(result)
    average_text = "\n".join(f"- {label}: {value:.2f}" for label, value in average_rows)

    lines = [
        _section_title(result.algorithm_name),
        f"Ordem de execucao: {' -> '.join(result.execution_order)}",
        "Decisoes do escalonador:",
    ]
    lines.extend(f"- {decision}" for decision in result.decision_log)
    lines.extend(
        [
            "",
            "Grafico de Gantt:",
            render_gantt(result.gantt_blocks),
            "",
            "Tabela final:",
            _render_result_table(result),
            "",
            "Medias:",
            average_text,
        ]
    )
    return "\n".join(lines)


def _render_input_table(processes: Sequence[Process]) -> str:
    include_severity = any(process.severity_label is not None for process in processes)
    include_max_wait = any(process.max_wait_tolerated is not None for process in processes)

    columns: list[Column] = [
        ("ID", lambda process: process.id, "<"),
        ("Nome", lambda process: process.name, "<"),
        ("Chegada", lambda process: str(process.arrival_time), ">"),
        ("Burst", lambda process: str(process.burst_time), ">"),
        ("Prio", lambda process: str(process.priority), ">"),
    ]

    if include_severity:
        columns.append(("Categoria", lambda process: process.severity_label or "-", "<"))
    if include_max_wait:
        columns.append(
            ("Espera max.", lambda process: _format_optional_int(process.max_wait_tolerated), ">")
        )

    return _render_table(processes, columns)


def _render_result_table(result: ScheduleResult) -> str:
    rows = build_result_rows(result)
    columns: list[Column] = [
        ("ID", lambda row: str(row["id"]), "<"),
        ("Nome", lambda row: str(row["name"]), "<"),
        ("Chegada", lambda row: str(row["arrival_time"]), ">"),
        ("Burst", lambda row: str(row["burst_time"]), ">"),
        ("Prio", lambda row: str(row["priority"]), ">"),
        ("Inicio", lambda row: str(row["start_time"]), ">"),
        ("Fim", lambda row: str(row["finish_time"]), ">"),
        ("Espera", lambda row: str(row["waiting_time"]), ">"),
        ("Turnaround", lambda row: str(row["turnaround_time"]), ">"),
        ("Resposta", lambda row: str(row["response_time"]), ">"),
    ]
    return _render_table(rows, columns)


def _render_table(rows: Sequence[Any], columns: Sequence[Column]) -> str:
    prepared_rows = [[getter(row) for _, getter, _ in columns] for row in rows]
    widths: list[int] = []

    for index, (header, _, _) in enumerate(columns):
        column_width = len(header)
        for row in prepared_rows:
            column_width = max(column_width, len(row[index]))
        widths.append(column_width)

    def format_row(values: Sequence[str]) -> str:
        parts: list[str] = []
        for value, width, (_, _, alignment) in zip(values, widths, columns):
            parts.append(value.rjust(width) if alignment == ">" else value.ljust(width))
        return " | ".join(parts)

    header = format_row([title for title, _, _ in columns])
    separator = "-+-".join("-" * width for width in widths)
    body = "\n".join(format_row(row) for row in prepared_rows)
    return f"{header}\n{separator}\n{body}"


def _section_title(title: str) -> str:
    underline = "-" * len(title)
    return f"{title}\n{underline}"


def _format_optional_int(value: int | None) -> str:
    return "-" if value is None else str(value)


def _load_processes_from_cli(args: argparse.Namespace) -> list[Process]:
    if args.json:
        return load_processes_from_json(args.json)
    if args.interactive:
        return _prompt_processes()
    return get_default_processes()


def _prompt_processes(
    input_func: Callable[[str], str] = input,
    output_func: Callable[[str], None] = print,
) -> list[Process]:
    output_func("Modo interativo de cadastro")
    output_func("Informe os processos manualmente. Para encerrar, deixe o nome em branco.")
    output_func("Se nao informar chegada, o valor padrao sera 0.")
    output_func("Convencao: numero maior = prioridade maior.")

    processes: list[Process] = []
    next_index = 1

    while True:
        name = input_func(f"\nNome da pessoa/processo P{next_index}: ").strip()
        if not name:
            if processes:
                break
            output_func("Pelo menos um processo precisa ser informado.")
            continue

        arrival_time = _prompt_int(
            "Tempo de chegada [0]: ",
            input_func=input_func,
            output_func=output_func,
            default=0,
            min_value=0,
        )
        burst_time = _prompt_int(
            "Tempo gasto (burst time): ",
            input_func=input_func,
            output_func=output_func,
            min_value=1,
        )
        priority = _prompt_int(
            "Prioridade (numero maior = prioridade maior): ",
            input_func=input_func,
            output_func=output_func,
        )

        processes.append(
            Process(
                id=f"P{next_index}",
                name=name,
                arrival_time=arrival_time,
                burst_time=burst_time,
                priority=priority,
                original_index=next_index - 1,
            )
        )
        next_index += 1

    output_func("")
    output_func(f"{len(processes)} processo(s) cadastrado(s).")
    return processes


def _prompt_int(
    prompt: str,
    input_func: Callable[[str], str],
    output_func: Callable[[str], None],
    default: int | None = None,
    min_value: int | None = None,
) -> int:
    while True:
        raw_value = input_func(prompt).strip()
        if not raw_value and default is not None:
            return default

        try:
            value = int(raw_value)
        except ValueError:
            output_func("Digite um numero inteiro valido.")
            continue

        if min_value is not None and value < min_value:
            output_func(f"O valor deve ser maior ou igual a {min_value}.")
            continue

        return value
