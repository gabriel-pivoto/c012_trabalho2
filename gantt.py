from __future__ import annotations

from models import GanttBlock


def render_gantt(blocks: tuple[GanttBlock, ...] | list[GanttBlock]) -> str:
    if not blocks:
        return "(nenhum bloco no Gantt)"

    normalized_blocks = list(blocks)
    bar_parts: list[str] = []
    boundaries: list[tuple[int, str]] = [(0, str(normalized_blocks[0].start))]
    cursor = 0

    for block in normalized_blocks:
        segment = f"| {block.label} "
        bar_parts.append(segment)
        cursor += len(segment)
        boundaries.append((cursor, str(block.end)))

    bar = "".join(bar_parts) + "|"
    timeline_width = max(len(bar) + 1, max(position + len(text) for position, text in boundaries) + 1)
    timeline = [" "] * timeline_width

    for position, text in boundaries:
        for offset, char in enumerate(text):
            index = position + offset
            if index >= len(timeline):
                timeline.extend(" " * (index - len(timeline) + 1))
            timeline[index] = char

    return f"{bar}\n{''.join(timeline).rstrip()}"
