from __future__ import annotations

import unittest

from gantt import render_gantt
from models import GanttBlock


class TestGanttRendering(unittest.TestCase):
    def test_gantt_uses_loading_bar_style_and_marks_idle(self) -> None:
        blocks = [
            GanttBlock(label="P1", start=0, end=2),
            GanttBlock(label="IDLE", start=2, end=4, is_idle=True),
            GanttBlock(label="P2", start=4, end=5),
        ]

        rendered = render_gantt(blocks)

        self.assertIn("[##P1##]", rendered)
        self.assertIn("[.IDLE.]", rendered)
        self.assertIn("[#P2#]", rendered)
        self.assertIn("0", rendered)
        self.assertIn("2", rendered)
        self.assertIn("4", rendered)
        self.assertIn("5", rendered)
        self.assertIn("Legenda: '#' em execucao, '.' em ociosidade", rendered)


if __name__ == "__main__":
    unittest.main()
