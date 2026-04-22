from __future__ import annotations

from collections.abc import Callable, Sequence

from models import ExecutionRecord, GanttBlock, Process, ScheduleResult, normalize_processes


CandidateKey = Callable[[Process], tuple[int, ...]]


def schedule_sjf(processes: Sequence[Process]) -> ScheduleResult:
    return _schedule_non_preemptive(
        processes=processes,
        algorithm_name="SJF (nao-preemptivo)",
        candidate_key=lambda process: (
            process.burst_time,
            process.arrival_time,
            -process.priority,
            process.original_index,
        ),
        selection_reason=(
            "menor burst_time; desempates por menor arrival_time, maior priority e ordem original"
        ),
    )


def schedule_priority(processes: Sequence[Process]) -> ScheduleResult:
    return _schedule_non_preemptive(
        processes=processes,
        algorithm_name="PS (nao-preemptivo)",
        candidate_key=lambda process: (
            # Convencao explicita deste trabalho: numero maior = prioridade maior.
            -process.priority,
            process.arrival_time,
            process.burst_time,
            process.original_index,
        ),
        selection_reason=(
            "maior priority; nesta simulacao, numero maior significa prioridade maior"
        ),
    )


def _schedule_non_preemptive(
    processes: Sequence[Process],
    algorithm_name: str,
    candidate_key: CandidateKey,
    selection_reason: str,
) -> ScheduleResult:
    pending = normalize_processes(processes)
    remaining = pending.copy()
    current_time = 0
    records: list[ExecutionRecord] = []
    gantt_blocks: list[GanttBlock] = []
    decision_log: list[str] = []

    while remaining:
        ready = [process for process in remaining if process.arrival_time <= current_time]

        if not ready:
            next_process = min(remaining, key=lambda process: (process.arrival_time, process.original_index))
            if current_time < next_process.arrival_time:
                # Sem processos prontos, a CPU fica ociosa ate a proxima chegada.
                decision_log.append(
                    f"t={current_time}: CPU ociosa ate t={next_process.arrival_time} aguardando a chegada de {next_process.id}."
                )
                gantt_blocks.append(
                    GanttBlock(
                        label="IDLE",
                        start=current_time,
                        end=next_process.arrival_time,
                        is_idle=True,
                    )
                )
                current_time = next_process.arrival_time
            ready = [process for process in remaining if process.arrival_time <= current_time]

        # O algoritmo e nao-preemptivo: o processo escolhido usa a CPU ate terminar.
        chosen = min(ready, key=candidate_key)
        start_time = current_time
        finish_time = start_time + chosen.burst_time
        waiting_time = start_time - chosen.arrival_time
        turnaround_time = finish_time - chosen.arrival_time
        response_time = start_time - chosen.arrival_time

        ready_labels = ", ".join(process.id for process in sorted(ready, key=lambda item: item.original_index))
        decision_log.append(
            f"t={current_time}: prontos=[{ready_labels}] -> {chosen.id} "
            f"(arrival={chosen.arrival_time}, burst={chosen.burst_time}, priority={chosen.priority}; {selection_reason})."
        )

        records.append(
            ExecutionRecord(
                process=chosen,
                start_time=start_time,
                finish_time=finish_time,
                waiting_time=waiting_time,
                turnaround_time=turnaround_time,
                response_time=response_time,
            )
        )
        gantt_blocks.append(GanttBlock(label=chosen.id, start=start_time, end=finish_time))

        remaining.remove(chosen)
        current_time = finish_time

    return ScheduleResult(
        algorithm_name=algorithm_name,
        records=tuple(records),
        gantt_blocks=tuple(gantt_blocks),
        decision_log=tuple(decision_log),
    )
