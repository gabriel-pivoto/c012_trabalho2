from __future__ import annotations

from dataclasses import dataclass
from queue import Empty, Queue
from random import Random
from threading import Lock, Thread
from time import sleep
from typing import Sequence

from models import Process, ScheduleResult


@dataclass(frozen=True, slots=True)
class PatientRequest:
    patient_id: str
    patient_name: str
    requested_units: int
    prep_delay_s: float
    critical_delay_s: float

    def __post_init__(self) -> None:
        if self.requested_units <= 0:
            raise ValueError("requested_units deve ser maior que zero")


@dataclass(frozen=True, slots=True)
class ChartEntry:
    doctor_id: str
    patient_id: str
    patient_name: str
    requested_units: int
    granted_units: int
    stock_before: int
    stock_after: int
    status: str


@dataclass(frozen=True, slots=True)
class AttendanceLog:
    doctor_id: str
    patient_id: str
    patient_name: str
    requested_units: int
    stock_before: int
    stock_after: int
    status: str


@dataclass(frozen=True, slots=True)
class SyncSimulationResult:
    mode_name: str
    doctor_count: int
    initial_stock: int
    final_stock: int
    total_requested: int
    total_granted: int
    attended_count: int
    not_attended_count: int
    chart_entries: tuple[ChartEntry, ...]
    logs: tuple[AttendanceLog, ...]
    consistency_ok: bool
    consistency_details: str


def build_patient_requests(
    source_schedule: ScheduleResult,
    seed: int | None = None,
) -> list[PatientRequest]:
    rng = Random(seed)
    requests: list[PatientRequest] = []

    for record in source_schedule.records:
        process = record.process
        max_units = max(1, min(6, process.burst_time))
        urgency_bonus = 1 if _is_high_urgency(process) else 0
        max_units = max(1, min(6, process.burst_time + urgency_bonus))
        requested_units = rng.randint(1, max_units)

        requests.append(
            PatientRequest(
                patient_id=process.id,
                patient_name=process.name,
                requested_units=requested_units,
                prep_delay_s=rng.uniform(0.0005, 0.0030),
                critical_delay_s=rng.uniform(0.0005, 0.0020),
            )
        )

    return requests


def _is_high_urgency(process: Process) -> bool:
    max_wait = process.max_wait_tolerated
    if max_wait is not None:
        return max_wait <= process.burst_time + 1
    return process.life_time <= process.burst_time + 1


def suggest_initial_stock(patient_requests: Sequence[PatientRequest]) -> int:
    if not patient_requests:
        return 0

    total_requested = sum(item.requested_units for item in patient_requests)
    return max(1, int(round(total_requested * 0.7)))


def run_thread_synchronization_demo(
    patient_requests: Sequence[PatientRequest],
    doctor_count: int,
    initial_stock: int,
    use_lock: bool,
    seed: int | None = None,
) -> SyncSimulationResult:
    if doctor_count <= 0:
        raise ValueError("doctor_count deve ser maior que zero")
    if initial_stock < 0:
        raise ValueError("initial_stock nao pode ser negativo")

    waiting_queue: Queue[PatientRequest] = Queue()
    for request in patient_requests:
        waiting_queue.put(request)

    shared = _SharedResources(initial_stock=initial_stock)
    mode_name = "Com sincronizacao (Lock)" if use_lock else "Sem sincronizacao"

    threads = [
        Thread(
            target=_doctor_worker,
            args=(f"D{index + 1}", waiting_queue, shared, use_lock),
            name=f"doctor-{index + 1}",
            daemon=False,
        )
        for index in range(doctor_count)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    total_requested = sum(item.requested_units for item in patient_requests)
    total_granted = sum(entry.granted_units for entry in shared.chart_entries)
    attended_count = sum(1 for entry in shared.chart_entries if entry.status == "ATENDIDO")
    not_attended_count = len(shared.chart_entries) - attended_count
    final_stock = shared.stock

    consistency_ok, consistency_details = _check_consistency(
        request_count=len(patient_requests),
        initial_stock=initial_stock,
        final_stock=final_stock,
        total_requested=total_requested,
        total_granted=total_granted,
        chart_entries=shared.chart_entries,
        attended_count=attended_count,
        not_attended_count=not_attended_count,
    )

    return SyncSimulationResult(
        mode_name=mode_name,
        doctor_count=doctor_count,
        initial_stock=initial_stock,
        final_stock=final_stock,
        total_requested=total_requested,
        total_granted=total_granted,
        attended_count=attended_count,
        not_attended_count=not_attended_count,
        chart_entries=tuple(shared.chart_entries),
        logs=tuple(shared.logs),
        consistency_ok=consistency_ok,
        consistency_details=consistency_details,
    )


def render_synchronization_report(
    source_algorithm_name: str,
    patient_requests: Sequence[PatientRequest],
    unsafe_result: SyncSimulationResult,
    safe_result: SyncSimulationResult,
) -> str:
    lines = [
        "Parte 2 - Sincronizacao de Threads",
        "----------------------------------",
        f"Fila de pacientes da parte 1: {source_algorithm_name}",
    ]

    if patient_requests:
        lines.append(
            "Ordem planejada da fila: "
            + " -> ".join(request.patient_id for request in patient_requests)
        )
        lines.append(
            "Requisicoes por paciente: "
            + ", ".join(
                f"{request.patient_id}={request.requested_units}" for request in patient_requests
            )
        )
    else:
        lines.append("Nenhum paciente disponivel para a parte 2.")

    lines.extend(
        [
            "",
            _render_mode_result(unsafe_result),
            "",
            _render_mode_result(safe_result),
        ]
    )

    return "\n".join(lines)


class _SharedResources:
    def __init__(self, initial_stock: int) -> None:
        self.stock = initial_stock
        self.stock_lock = Lock()
        self.log_lock = Lock()
        self.chart_entries: list[ChartEntry] = []
        self.logs: list[AttendanceLog] = []


def _doctor_worker(
    doctor_id: str,
    waiting_queue: Queue[PatientRequest],
    shared: _SharedResources,
    use_lock: bool,
) -> None:
    while True:
        try:
            request = waiting_queue.get_nowait()
        except Empty:
            return

        sleep(request.prep_delay_s)

        if use_lock:
            with shared.stock_lock:
                log = _attend_patient(
                    doctor_id=doctor_id,
                    request=request,
                    shared=shared,
                    inject_race_delay=False,
                )
        else:
            log = _attend_patient(
                doctor_id=doctor_id,
                request=request,
                shared=shared,
                inject_race_delay=True,
            )

        with shared.log_lock:
            shared.logs.append(log)

        waiting_queue.task_done()


def _attend_patient(
    doctor_id: str,
    request: PatientRequest,
    shared: _SharedResources,
    inject_race_delay: bool,
) -> AttendanceLog:
    stock_before = shared.stock

    if inject_race_delay:
        sleep(request.critical_delay_s)

    if stock_before >= request.requested_units:
        granted_units = request.requested_units

        if inject_race_delay:
            sleep(request.critical_delay_s)

        shared.stock = stock_before - granted_units
        status = "ATENDIDO"
    else:
        granted_units = 0
        status = "SEM_RECURSO"

    stock_after = shared.stock

    shared.chart_entries.append(
        ChartEntry(
            doctor_id=doctor_id,
            patient_id=request.patient_id,
            patient_name=request.patient_name,
            requested_units=request.requested_units,
            granted_units=granted_units,
            stock_before=stock_before,
            stock_after=stock_after,
            status=status,
        )
    )

    return AttendanceLog(
        doctor_id=doctor_id,
        patient_id=request.patient_id,
        patient_name=request.patient_name,
        requested_units=request.requested_units,
        stock_before=stock_before,
        stock_after=stock_after,
        status=status,
    )


def _check_consistency(
    request_count: int,
    initial_stock: int,
    final_stock: int,
    total_requested: int,
    total_granted: int,
    chart_entries: Sequence[ChartEntry],
    attended_count: int,
    not_attended_count: int,
) -> tuple[bool, str]:
    expected_final_stock = initial_stock - total_granted
    problems: list[str] = []

    if final_stock != expected_final_stock:
        problems.append(
            f"estoque_final={final_stock} mas esperado={expected_final_stock}"
        )
    if len(chart_entries) != request_count:
        problems.append(
            f"prontuario={len(chart_entries)} mas fila_original={request_count}"
        )
    if attended_count + not_attended_count != len(chart_entries):
        problems.append("contagem de atendidos nao fecha com o prontuario")
    if total_granted > total_requested:
        problems.append(
            f"total_concedido={total_granted} maior que total_solicitado={total_requested}"
        )
    if final_stock < 0:
        problems.append(f"estoque_final negativo ({final_stock})")

    if problems:
        return False, "INCONSISTENTE: " + "; ".join(problems)

    return (
        True,
        f"OK: estoque_final={final_stock}, esperado={expected_final_stock}, prontuario={len(chart_entries)}",
    )


def _render_mode_result(result: SyncSimulationResult) -> str:
    lines = [
        result.mode_name,
        "Logs de atendimento:",
    ]

    if result.logs:
        for log in result.logs:
            lines.append(
                "- "
                + f"medico={log.doctor_id} "
                + f"paciente={log.patient_id} "
                + f"solicitou={log.requested_units} "
                + f"estoque={log.stock_before}->{log.stock_after} "
                + f"status={log.status}"
            )
    else:
        lines.append("- (nenhum atendimento registrado)")

    lines.extend(
        [
            "Resumo final:",
            f"- estoque inicial: {result.initial_stock}",
            f"- total solicitado: {result.total_requested}",
            f"- total concedido: {result.total_granted}",
            f"- estoque final: {result.final_stock}",
            f"- entradas no prontuario: {len(result.chart_entries)}",
            f"- atendidos: {result.attended_count}",
            f"- sem recurso: {result.not_attended_count}",
            "- consistencia: "
            + ("OK" if result.consistency_ok else "INCONSISTENTE")
            + f" ({result.consistency_details})",
        ]
    )

    return "\n".join(lines)
