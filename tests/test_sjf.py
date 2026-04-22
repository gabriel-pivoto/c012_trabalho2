from __future__ import annotations

import unittest

from models import Process
from schedulers import schedule_sjf


class TestSJF(unittest.TestCase):
    def test_sjf_orders_by_shortest_burst_among_ready_processes(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=7, life_time=20),
            Process(id="P2", name="B", arrival_time=0, burst_time=2, life_time=15),
            Process(id="P3", name="C", arrival_time=1, burst_time=1, life_time=18),
            Process(id="P4", name="D", arrival_time=2, burst_time=4, life_time=16),
        ]

        result = schedule_sjf(processes)

        self.assertEqual(result.execution_order, ("P2", "P3", "P4", "P1"))

    def test_sjf_uses_secondary_tie_breakers(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=3, life_time=2),
            Process(id="P2", name="B", arrival_time=0, burst_time=3, life_time=5),
            Process(id="P3", name="C", arrival_time=1, burst_time=3, life_time=9),
        ]

        result = schedule_sjf(processes)

        self.assertEqual(result.execution_order, ("P1", "P2", "P3"))

    def test_sjf_preserves_original_order_after_other_tie_breakers(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=3, life_time=4),
            Process(id="P2", name="B", arrival_time=0, burst_time=3, life_time=4),
        ]

        result = schedule_sjf(processes)

        self.assertEqual(result.execution_order, ("P1", "P2"))


if __name__ == "__main__":
    unittest.main()
