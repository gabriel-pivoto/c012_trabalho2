from __future__ import annotations

import unittest

from models import Process
from schedulers import schedule_priority, schedule_sjf


class TestSchedulingMetrics(unittest.TestCase):
    def test_waiting_turnaround_and_response_times_are_computed_correctly(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=5, priority=1),
            Process(id="P2", name="B", arrival_time=1, burst_time=2, priority=9),
            Process(id="P3", name="C", arrival_time=2, burst_time=1, priority=3),
        ]

        result = schedule_sjf(processes)
        records = result.record_by_process_id()

        self.assertEqual(records["P1"].waiting_time, 0)
        self.assertEqual(records["P1"].turnaround_time, 5)
        self.assertEqual(records["P1"].response_time, 0)

        self.assertEqual(records["P3"].waiting_time, 3)
        self.assertEqual(records["P3"].turnaround_time, 4)
        self.assertEqual(records["P3"].response_time, 3)

        self.assertEqual(records["P2"].waiting_time, 5)
        self.assertEqual(records["P2"].turnaround_time, 7)
        self.assertEqual(records["P2"].response_time, 5)

    def test_cpu_idle_is_represented_and_time_advances_to_next_arrival(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=3, burst_time=2, priority=1),
            Process(id="P2", name="B", arrival_time=5, burst_time=1, priority=2),
        ]

        result = schedule_priority(processes)
        records = result.record_by_process_id()

        self.assertEqual(result.gantt_blocks[0].label, "IDLE")
        self.assertEqual(result.gantt_blocks[0].start, 0)
        self.assertEqual(result.gantt_blocks[0].end, 3)
        self.assertEqual(records["P1"].start_time, 3)
        self.assertEqual(records["P1"].waiting_time, 0)
        self.assertEqual(records["P2"].start_time, 5)
        self.assertEqual(records["P2"].waiting_time, 0)


if __name__ == "__main__":
    unittest.main()
