from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Sequence


@dataclass(frozen=True, slots=True)
class Process:
    id: str
    name: str
    arrival_time: int
    burst_time: int
    life_time: int
    severity_label: str | None = None
    max_wait_tolerated: int | None = None
    original_index: int = field(default=0, compare=False)

    def __post_init__(self) -> None:
        if self.arrival_time < 0:
            raise ValueError(f"arrival_time invalido para {self.id}: {self.arrival_time}")
        if self.burst_time <= 0:
            raise ValueError(f"burst_time invalido para {self.id}: {self.burst_time}")
        if self.life_time < 0:
            raise ValueError(f"life_time invalido para {self.id}: {self.life_time}")


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    process: Process
    start_time: int
    finish_time: int
    waiting_time: int
    turnaround_time: int
    response_time: int


@dataclass(frozen=True, slots=True)
class PatientResult:
    process: Process
    life_time_initial: int
    life_time_final: int
    survived: bool
    start_time: int | None = None
    finish_time: int | None = None
    waiting_time: int | None = None
    turnaround_time: int | None = None
    response_time: int | None = None
    death_time: int | None = None

    @property
    def status_final(self) -> str:
        return "RESISTIU" if self.survived else "NAO RESISTIU"

    @property
    def was_attended(self) -> bool:
        return self.start_time is not None


@dataclass(frozen=True, slots=True)
class GanttBlock:
    label: str
    start: int
    end: int
    is_idle: bool = False


@dataclass(frozen=True, slots=True)
class ScheduleResult:
    algorithm_name: str
    records: tuple[ExecutionRecord, ...]
    patient_results: tuple[PatientResult, ...]
    gantt_blocks: tuple[GanttBlock, ...]
    decision_log: tuple[str, ...]

    @property
    def execution_order(self) -> tuple[str, ...]:
        return tuple(record.process.id for record in self.records)

    @property
    def average_waiting_time(self) -> float:
        if not self.records:
            return 0.0
        return sum(record.waiting_time for record in self.records) / len(self.records)

    @property
    def average_turnaround_time(self) -> float:
        if not self.records:
            return 0.0
        return sum(record.turnaround_time for record in self.records) / len(self.records)

    @property
    def average_response_time(self) -> float:
        if not self.records:
            return 0.0
        return sum(record.response_time for record in self.records) / len(self.records)

    @property
    def survived_count(self) -> int:
        return sum(1 for result in self.patient_results if result.survived)

    @property
    def deceased_count(self) -> int:
        return len(self.patient_results) - self.survived_count

    @property
    def deceased_patient_ids(self) -> tuple[str, ...]:
        return tuple(result.process.id for result in self.patient_results if not result.survived)

    def record_by_process_id(self) -> dict[str, ExecutionRecord]:
        return {record.process.id: record for record in self.records}

    def patient_result_by_process_id(self) -> dict[str, PatientResult]:
        return {result.process.id: result for result in self.patient_results}


def normalize_processes(processes: Sequence[Process]) -> list[Process]:
    normalized: list[Process] = []
    seen_ids: set[str] = set()

    for index, process in enumerate(processes):
        if process.id in seen_ids:
            raise ValueError(f"IDs de processo duplicados nao sao permitidos: {process.id}")
        seen_ids.add(process.id)
        normalized.append(replace(process, original_index=index))

    return normalized
