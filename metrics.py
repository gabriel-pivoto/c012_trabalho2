from __future__ import annotations

from collections.abc import Callable
from statistics import median
from typing import Iterable

from models import ExecutionRecord, Process, ScheduleResult


def build_result_rows(result: ScheduleResult) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for record in result.records:
        rows.append(
            {
                "id": record.process.id,
                "name": record.process.name,
                "arrival_time": record.process.arrival_time,
                "burst_time": record.process.burst_time,
                "priority": record.process.priority,
                "start_time": record.start_time,
                "finish_time": record.finish_time,
                "waiting_time": record.waiting_time,
                "turnaround_time": record.turnaround_time,
                "response_time": record.response_time,
            }
        )
    return rows


def build_average_rows(result: ScheduleResult) -> list[tuple[str, float]]:
    return [
        ("Tempo medio de espera", result.average_waiting_time),
        ("Tempo medio de turnaround", result.average_turnaround_time),
        ("Tempo medio de resposta", result.average_response_time),
    ]


def build_comparison_analysis(
    processes: Iterable[Process],
    sjf_result: ScheduleResult,
    ps_result: ScheduleResult,
) -> list[str]:
    processes_list = list(processes)
    if not processes_list:
        return ["Nenhum processo foi informado para comparacao."]

    lines: list[str] = []
    sjf_avg = sjf_result.average_waiting_time
    ps_avg = ps_result.average_waiting_time

    if sjf_avg < ps_avg:
        lines.append(
            f"O menor tempo medio de espera foi do SJF ({sjf_avg:.2f}), contra {ps_avg:.2f} no PS."
        )
        average_winner = sjf_result
        average_winner_name = "SJF"
        average_loser = ps_result
        average_loser_name = "PS"
    elif ps_avg < sjf_avg:
        lines.append(
            f"O menor tempo medio de espera foi do PS ({ps_avg:.2f}), contra {sjf_avg:.2f} no SJF."
        )
        average_winner = ps_result
        average_winner_name = "PS"
        average_loser = sjf_result
        average_loser_name = "SJF"
    else:
        lines.append(
            f"Os dois algoritmos empataram no tempo medio de espera ({sjf_avg:.2f})."
        )
        average_winner = sjf_result
        average_winner_name = sjf_result.algorithm_name
        average_loser = ps_result
        average_loser_name = ps_result.algorithm_name

    long_processes = _select_top_by_metric(processes_list, key=lambda process: process.burst_time)
    long_descriptions: list[str] = []
    for process in long_processes:
        sjf_record = sjf_result.record_by_process_id()[process.id]
        ps_record = ps_result.record_by_process_id()[process.id]
        if sjf_record.waiting_time > ps_record.waiting_time:
            long_descriptions.append(
                f"{process.id} ({process.name}, burst={process.burst_time}) sofreu mais no SJF: espera {sjf_record.waiting_time} contra {ps_record.waiting_time} no PS"
            )
        elif ps_record.waiting_time > sjf_record.waiting_time:
            long_descriptions.append(
                f"{process.id} ({process.name}, burst={process.burst_time}) sofreu mais no PS: espera {ps_record.waiting_time} contra {sjf_record.waiting_time} no SJF"
            )
        else:
            long_descriptions.append(
                f"{process.id} ({process.name}, burst={process.burst_time}) teve a mesma espera nos dois algoritmos ({sjf_record.waiting_time})"
            )

    if long_descriptions:
        lines.append("Entre os processos mais longos: " + "; ".join(long_descriptions) + ".")

    high_priority_processes = _select_high_priority_processes(processes_list)
    benefited: list[str] = []
    not_benefited: list[str] = []

    for process in high_priority_processes:
        sjf_record = sjf_result.record_by_process_id()[process.id]
        ps_record = ps_result.record_by_process_id()[process.id]
        if ps_record.waiting_time < sjf_record.waiting_time:
            benefited.append(
                f"{process.id} ({process.name}) caiu de {sjf_record.waiting_time} para {ps_record.waiting_time} de espera"
            )
        elif ps_record.waiting_time > sjf_record.waiting_time:
            not_benefited.append(
                f"{process.id} ({process.name}) esperou {ps_record.waiting_time} no PS e {sjf_record.waiting_time} no SJF"
            )

    if benefited:
        lines.append(
            "Processos de alta prioridade beneficiados no PS: " + "; ".join(benefited) + "."
        )
    else:
        lines.append(
            "Nenhum dos processos classificados como alta prioridade teve melhora de espera no PS em relacao ao SJF."
        )

    if not_benefited:
        lines.append(
            "Ainda assim, alta prioridade nao garante beneficio automatico: "
            + "; ".join(not_benefited)
            + "."
        )

    worse_under_average_winner: list[str] = []
    winner_records = average_winner.record_by_process_id()
    loser_records = average_loser.record_by_process_id()

    for process in processes_list:
        if winner_records[process.id].waiting_time > loser_records[process.id].waiting_time:
            worse_under_average_winner.append(
                f"{process.id} ({process.name})"
            )

    if worse_under_average_winner:
        lines.append(
            f"Isto ilustra que menor media nao significa melhor para todos: embora {average_winner_name} reduza a media global, "
            f"{', '.join(worse_under_average_winner)} teria(m) espera menor no {average_loser_name}."
        )

    return lines


def _select_top_by_metric(processes: list[Process], key: Callable[[Process], int]) -> list[Process]:
    count = max(1, len(processes) // 3)
    return sorted(
        processes,
        key=lambda process: (key(process), process.priority, -process.arrival_time),
        reverse=True,
    )[:count]


def _select_high_priority_processes(processes: list[Process]) -> list[Process]:
    if not processes:
        return []

    threshold = median(process.priority for process in processes)
    return [
        process
        for process in processes
        if process.priority >= threshold
    ]
