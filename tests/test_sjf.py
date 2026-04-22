from __future__ import annotations

import unittest

from models import Process
from schedulers import schedule_sjf


class TestSJF(unittest.TestCase):
    def test_sjf_orders_by_shortest_burst_among_ready_processes(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=7, priority=4),
            Process(id="P2", name="B", arrival_time=0, burst_time=2, priority=1),
            Process(id="P3", name="C", arrival_time=1, burst_time=1, priority=8),
            Process(id="P4", name="D", arrival_time=2, burst_time=4, priority=5),
        ]

        result = schedule_sjf(processes)

        self.assertEqual(result.execution_order, ("P2", "P3", "P4", "P1"))

    def test_sjf_uses_secondary_tie_breakers(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=3, priority=2),
            Process(id="P2", name="B", arrival_time=0, burst_time=3, priority=5),
            Process(id="P3", name="C", arrival_time=1, burst_time=3, priority=9),
        ]

        result = schedule_sjf(processes)

        self.assertEqual(result.execution_order, ("P2", "P1", "P3"))

    def test_sjf_preserves_original_order_after_other_tie_breakers(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=3, priority=4),
            Process(id="P2", name="B", arrival_time=0, burst_time=3, priority=4),
        ]

        result = schedule_sjf(processes)

        self.assertEqual(result.execution_order, ("P1", "P2"))


if __name__ == "__main__":
    unittest.main()
