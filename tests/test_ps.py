from __future__ import annotations

import unittest

from models import Process
from schedulers import schedule_priority


class TestPriorityScheduling(unittest.TestCase):
    def test_ps_orders_by_lower_life_time(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=7, life_time=8),
            Process(id="P2", name="B", arrival_time=0, burst_time=2, life_time=2),
            Process(id="P3", name="C", arrival_time=1, burst_time=1, life_time=3),
            Process(id="P4", name="D", arrival_time=2, burst_time=4, life_time=5),
        ]

        result = schedule_priority(processes)

        self.assertEqual(result.execution_order, ("P2", "P3", "P4", "P1"))

    def test_ps_uses_secondary_tie_breakers(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=4, life_time=8),
            Process(id="P2", name="B", arrival_time=0, burst_time=2, life_time=8),
            Process(id="P3", name="C", arrival_time=1, burst_time=1, life_time=8),
        ]

        result = schedule_priority(processes)

        self.assertEqual(result.execution_order, ("P2", "P1", "P3"))

    def test_ps_preserves_original_order_after_secondary_tie_breakers(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=3, life_time=4),
            Process(id="P2", name="B", arrival_time=0, burst_time=3, life_time=4),
        ]

        result = schedule_priority(processes)

        self.assertEqual(result.execution_order, ("P1", "P2"))


if __name__ == "__main__":
    unittest.main()
