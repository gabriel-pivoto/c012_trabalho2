from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models import Process


DEFAULT_PROCESSES_RAW: list[dict[str, Any]] = [
    {
        "id": "P1",
        "name": "Paciente Ana",
        "arrival_time": 0,
        "burst_time": 3,
        "life_time": 2,
        "severity_label": "grave",
        "max_wait_tolerated": 2,
    },
    {
        "id": "P2",
        "name": "Paciente Bruno",
        "arrival_time": 0,
        "burst_time": 3,
        "life_time": 5,
        "severity_label": "grave",
        "max_wait_tolerated": 4,
    },
    {
        "id": "P3",
        "name": "Paciente Carla",
        "arrival_time": 0,
        "burst_time": 1,
        "life_time": 9,
        "severity_label": "leve",
        "max_wait_tolerated": 10,
    },
    {
        "id": "P4",
        "name": "Paciente Daniel",
        "arrival_time": 1,
        "burst_time": 1,
        "life_time": 8,
        "severity_label": "moderado",
        "max_wait_tolerated": 9,
    },
    {
        "id": "P5",
        "name": "Paciente Elisa",
        "arrival_time": 10,
        "burst_time": 1,
        "life_time": 4,
        "severity_label": "moderado",
        "max_wait_tolerated": 4,
    },
]


def get_default_processes() -> list[Process]:
    return _build_processes(DEFAULT_PROCESSES_RAW)


def load_processes_from_json(path: str | Path) -> list[Process]:
    file_path = Path(path)
    content = json.loads(file_path.read_text(encoding="utf-8"))

    if not isinstance(content, list):
        raise ValueError("O arquivo JSON deve conter uma lista de processos.")

    return _build_processes(content)


def _build_processes(items: list[dict[str, Any]]) -> list[Process]:
    processes: list[Process] = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError("Cada item do dataset deve ser um objeto JSON.")

        processes.append(
            Process(
                id=str(item["id"]),
                name=str(item["name"]),
                arrival_time=int(item["arrival_time"]),
                burst_time=int(item["burst_time"]),
                life_time=_extract_life_time(item),
                severity_label=_optional_string(item.get("severity_label")),
                max_wait_tolerated=_optional_int(item.get("max_wait_tolerated")),
                original_index=index,
            )
        )

    return processes


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _extract_life_time(item: dict[str, Any]) -> int:
    if "life_time" in item:
        return int(item["life_time"])
    if "tempo_de_vida" in item:
        return int(item["tempo_de_vida"])
    if "priority" in item:
        return int(item["priority"])
    raise KeyError("Cada processo precisa informar life_time ou tempo_de_vida.")
