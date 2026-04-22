from __future__ import annotations

from models import GanttBlock


def render_gantt(blocks: tuple[GanttBlock, ...] | list[GanttBlock]) -> str:
    if not blocks:
        return "(nenhum bloco no Gantt)"

    normalized_blocks = list(blocks)
    unit_width = 3
    bar_parts: list[str] = []
    boundaries: list[tuple[int, str]] = []
    cursor = 0

    for block in normalized_blocks:
        duration = max(1, block.end - block.start)
        fill_char = "." if block.is_idle else "#"
        inner_width = max(duration * unit_width, len(block.label) + 2)
        segment = "[" + block.label.center(inner_width, fill_char) + "]"
        bar_parts.append(segment)
        boundaries.append((cursor, str(block.start)))
        cursor += len(segment)

    boundaries.append((cursor, str(normalized_blocks[-1].end)))
    bar = "".join(bar_parts)
    timeline_width = max(len(bar) + 1, max(position + len(text) for position, text in boundaries) + 1)
    timeline = [" "] * timeline_width

    for position, text in boundaries:
        for offset, char in enumerate(text):
            index = position + offset
            if index >= len(timeline):
                timeline.extend(" " * (index - len(timeline) + 1))
            timeline[index] = char

    return f"{bar}\n{''.join(timeline).rstrip()}\nLegenda: '#' em execucao, '.' em ociosidade"
