from __future__ import annotations

from typing import Iterable

from models import Process, ScheduleResult


def build_result_rows(result: ScheduleResult) -> list[dict[str, int | str | None]]:
    rows: list[dict[str, int | str | None]] = []
    for patient_result in result.patient_results:
        rows.append(
            {
                "id": patient_result.process.id,
                "name": patient_result.process.name,
                "arrival_time": patient_result.process.arrival_time,
                "burst_time": patient_result.process.burst_time,
                "life_time_initial": patient_result.life_time_initial,
                "life_time_final": patient_result.life_time_final,
                "start_time": patient_result.start_time,
                "finish_time": patient_result.finish_time,
                "waiting_time": patient_result.waiting_time,
                "turnaround_time": patient_result.turnaround_time,
                "response_time": patient_result.response_time,
                "status_final": patient_result.status_final,
                "death_time": patient_result.death_time,
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
    life_label = "algoritmo por menor tempo de vida"

    if sjf_result.survived_count > ps_result.survived_count:
        lines.append(
            f"O SJF preservou mais pacientes vivos ({sjf_result.survived_count} contra {ps_result.survived_count})."
        )
        survival_winner = "SJF"
    elif ps_result.survived_count > sjf_result.survived_count:
        lines.append(
            f"O {life_label} preservou mais pacientes vivos ({ps_result.survived_count} contra {sjf_result.survived_count})."
        )
        survival_winner = life_label
    else:
        lines.append(
            f"Os dois algoritmos preservaram a mesma quantidade de pacientes vivos ({sjf_result.survived_count})."
        )
        survival_winner = "empate"

    if sjf_result.deceased_count < ps_result.deceased_count:
        lines.append(
            f"O SJF teve menos mortes ({sjf_result.deceased_count} contra {ps_result.deceased_count})."
        )
    elif ps_result.deceased_count < sjf_result.deceased_count:
        lines.append(
            f"O {life_label} teve menos mortes ({ps_result.deceased_count} contra {sjf_result.deceased_count})."
        )
    else:
        lines.append(
            f"Os dois algoritmos tiveram o mesmo numero de mortes ({sjf_result.deceased_count})."
        )

    sjf_avg = sjf_result.average_waiting_time
    ps_avg = ps_result.average_waiting_time
    if sjf_avg < ps_avg:
        lines.append(
            f"O menor tempo medio de espera entre os pacientes atendidos foi do SJF ({sjf_avg:.2f}), contra {ps_avg:.2f} no {life_label}."
        )
        waiting_winner = "SJF"
    elif ps_avg < sjf_avg:
        lines.append(
            f"O menor tempo medio de espera entre os pacientes atendidos foi do {life_label} ({ps_avg:.2f}), contra {sjf_avg:.2f} no SJF."
        )
        waiting_winner = life_label
    else:
        lines.append(
            f"Os dois algoritmos empataram no tempo medio de espera entre os pacientes atendidos ({sjf_avg:.2f})."
        )
        waiting_winner = "empate"

    sjf_by_id = sjf_result.patient_result_by_process_id()
    ps_by_id = ps_result.patient_result_by_process_id()
    died_only_in_sjf = [
        _describe_process(process)
        for process in processes_list
        if not sjf_by_id[process.id].survived and ps_by_id[process.id].survived
    ]
    died_only_in_life = [
        _describe_process(process)
        for process in processes_list
        if sjf_by_id[process.id].survived and not ps_by_id[process.id].survived
    ]

    if died_only_in_sjf:
        lines.append(
            "Pacientes que morreram no SJF mas resistiram no algoritmo por menor tempo de vida: "
            + "; ".join(died_only_in_sjf)
            + "."
        )
    if died_only_in_life:
        lines.append(
            "Pacientes que morreram no algoritmo por menor tempo de vida mas resistiram no SJF: "
            + "; ".join(died_only_in_life)
            + "."
        )
    if not died_only_in_sjf and not died_only_in_life:
        lines.append("Os mesmos pacientes resistiram nos dois algoritmos.")

    if survival_winner != "empate" and waiting_winner != "empate" and survival_winner != waiting_winner:
        lines.append(
            "Isto mostra que menor espera media nem sempre significa mais sobreviventes."
        )

    return lines


def _describe_process(process: Process) -> str:
    return (
        f"{process.id} ({process.name}, burst={process.burst_time}, vida_inicial={process.life_time})"
    )
