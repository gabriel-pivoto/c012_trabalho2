from __future__ import annotations

from dataclasses import dataclass, replace
from collections.abc import Callable, Sequence

from models import (
    ExecutionRecord,
    GanttBlock,
    PatientResult,
    Process,
    ScheduleResult,
    normalize_processes,
)


@dataclass(slots=True)
class _PatientState:
    # Estado mutavel usado durante a simulacao. O Process continua imutavel,
    # mas o tempo de vida atual precisa ser reduzido enquanto o paciente espera.
    process: Process
    current_life_time: int


CandidateKey = Callable[[_PatientState], tuple[int, ...]]


def schedule_sjf(processes: Sequence[Process]) -> ScheduleResult:
    # SJF: escolhe sempre o menor burst entre os processos ja prontos.
    return _schedule_non_preemptive(
        processes=processes,
        algorithm_name="SJF (nao-preemptivo)",
        candidate_key=lambda state: (
            state.process.burst_time,
            state.process.arrival_time,
            state.current_life_time,
            state.process.original_index,
        ),
        selection_reason=(
            "menor burst_time; desempates por menor arrival_time, menor tempo de vida atual e ordem original"
        ),
    )

# regra aplicada agora e a de menor tempo de vida.
def schedule_priority(processes: Sequence[Process]) -> ScheduleResult:
    # "Priority": menor tempo de vida significa maior urgencia.
    return _schedule_non_preemptive(
        processes=processes,
        algorithm_name="PS (menor tempo de vida)",
        candidate_key=lambda state: (
            state.current_life_time,
            state.process.arrival_time,
            state.process.burst_time,
            state.process.original_index,
        ),
        selection_reason=(
            "menor tempo de vida atual"
        ),
    )


def _schedule_non_preemptive(
    processes: Sequence[Process],
    algorithm_name: str,
    candidate_key: CandidateKey,
    selection_reason: str,
) -> ScheduleResult:
    # Normaliza a entrada para garantir IDs unicos e preservar a ordem original
    # como ultimo criterio de desempate.
    normalized_processes = normalize_processes(processes)

    # Cada item restante carrega o processo original e o tempo de vida que vai
    # diminuindo enquanto ele espera na fila.
    remaining = [
        _PatientState(process=process, current_life_time=process.life_time)
        for process in normalized_processes
    ]
    current_time = 0
    records: list[ExecutionRecord] = []
    gantt_blocks: list[GanttBlock] = []
    decision_log: list[str] = []
    patient_results = {
        process.id: PatientResult(
            process=process,
            life_time_initial=process.life_time,
            life_time_final=process.life_time,
            survived=process.life_time > 0,
        )
        for process in normalized_processes
    }

    while remaining:
        # Remove imediatamente quem ja chegou "morto" no instante atual.
        _mark_dead_on_arrival(remaining, current_time, patient_results, decision_log)

        # "Ready" representa os processos que ja chegaram e podem disputar CPU agora.
        ready = [state for state in remaining if state.process.arrival_time <= current_time]

        if not ready:
            # Se ninguem esta pronto, a CPU avanca para a proxima chegada.
            future_arrivals = [
                state for state in remaining if state.process.arrival_time > current_time
            ]
            if not future_arrivals:
                break

            next_state = min(
                future_arrivals,
                key=lambda state: (state.process.arrival_time, state.process.original_index),
            )
            if current_time < next_state.process.arrival_time:
                # Sem processos prontos, a CPU fica ociosa ate a proxima chegada.
                decision_log.append(
                    f"t={current_time}: CPU ociosa ate t={next_state.process.arrival_time} aguardando a chegada de {next_state.process.id}."
                )
                gantt_blocks.append(
                    GanttBlock(
                        label="IDLE",
                        start=current_time,
                        end=next_state.process.arrival_time,
                        is_idle=True,
                    )
                )
                current_time = next_state.process.arrival_time

            _mark_dead_on_arrival(remaining, current_time, patient_results, decision_log)
            ready = [state for state in remaining if state.process.arrival_time <= current_time]
            if not ready:
                continue

        # O algoritmo e nao-preemptivo: depois de escolhido, o processo roda ate o fim.
        chosen = min(ready, key=candidate_key)
        start_time = current_time
        finish_time = start_time + chosen.process.burst_time
        waiting_time = start_time - chosen.process.arrival_time
        turnaround_time = finish_time - chosen.process.arrival_time
        response_time = start_time - chosen.process.arrival_time

        # Registra a decisao do escalonador com os candidatos disponiveis.
        ready_labels = ", ".join(
            state.process.id
            for state in sorted(ready, key=lambda item: item.process.original_index)
        )
        decision_log.append(
            f"t={current_time}: prontos=[{ready_labels}] -> {chosen.process.id} "
            f"(arrival={chosen.process.arrival_time}, burst={chosen.process.burst_time}, vida_atual={chosen.current_life_time}; {selection_reason})."
        )

        records.append(
            ExecutionRecord(
                process=chosen.process,
                start_time=start_time,
                finish_time=finish_time,
                waiting_time=waiting_time,
                turnaround_time=turnaround_time,
                response_time=response_time,
            )
        )

        # Atualiza o resultado final do paciente atendido sem alterar o Process original.
        patient_results[chosen.process.id] = replace(
            patient_results[chosen.process.id],
            life_time_final=chosen.current_life_time,
            survived=True,
            start_time=start_time,
            finish_time=finish_time,
            waiting_time=waiting_time,
            turnaround_time=turnaround_time,
            response_time=response_time,
        )
        gantt_blocks.append(GanttBlock(label=chosen.process.id, start=start_time, end=finish_time))

        remaining.remove(chosen)

        # Enquanto o escolhido esta em consulta, os demais que ja chegaram continuam
        # esperando e perdem tempo de vida.
        _apply_waiting_life_loss(remaining, start_time, finish_time, patient_results, decision_log)
        current_time = finish_time

    return ScheduleResult(
        algorithm_name=algorithm_name,
        records=tuple(records),
        patient_results=tuple(
            patient_results[process.id]
            for process in sorted(normalized_processes, key=lambda process: process.original_index)
        ),
        gantt_blocks=tuple(gantt_blocks),
        decision_log=tuple(decision_log),
    )


def _mark_dead_on_arrival(
    remaining: list[_PatientState],
    current_time: int,
    patient_results: dict[str, PatientResult],
    decision_log: list[str],
) -> None:
    # Filtra apenas quem ja chegou ao sistema e esta com vida esgotada.
    arriving_dead = [
        state
        for state in remaining
        if state.process.arrival_time <= current_time and state.current_life_time <= 0
    ]

    for state in sorted(
        arriving_dead,
        key=lambda item: (item.process.arrival_time, item.process.original_index),
    ):
        _register_death(
            state=state,
            death_time=state.process.arrival_time,
            patient_results=patient_results,
            decision_log=decision_log,
        )
        remaining.remove(state)


def _apply_waiting_life_loss(
    remaining: list[_PatientState],
    start_time: int,
    finish_time: int,
    patient_results: dict[str, PatientResult],
    decision_log: list[str],
) -> None:
    # Guarda mortes para aplicar depois do loop, evitando alterar a lista
    # remaining enquanto ela esta sendo percorrida.
    death_events: list[tuple[int, _PatientState]] = []

    for state in remaining:
        # O paciente so perde vida a partir do instante em que realmente chegou.
        overlap_start = max(start_time, state.process.arrival_time)
        if overlap_start >= finish_time:
            continue

        waited_time = finish_time - overlap_start
        if state.current_life_time <= waited_time:
            # Se a vida acaba antes do fim do atendimento atual, registramos o
            # instante exato da morte.
            death_events.append((overlap_start + state.current_life_time, state))
            continue

        state.current_life_time -= waited_time

    for death_time, state in sorted(
        death_events,
        key=lambda item: (item[0], item[1].process.original_index),
    ):
        state.current_life_time = 0
        _register_death(
            state=state,
            death_time=death_time,
            patient_results=patient_results,
            decision_log=decision_log,
        )
        remaining.remove(state)


def _register_death(
    state: _PatientState,
    death_time: int,
    patient_results: dict[str, PatientResult],
    decision_log: list[str],
) -> None:
    # Evita registrar a mesma morte duas vezes caso a funcao seja chamada novamente.
    existing_result = patient_results[state.process.id]
    if existing_result.death_time is not None:
        return

    patient_results[state.process.id] = replace(
        existing_result,
        life_time_final=0,
        survived=False,
        death_time=death_time,
    )
    decision_log.append(
        f"t={death_time}: {state.process.id} nao resistiu aguardando na fila e saiu da simulacao."
    )
