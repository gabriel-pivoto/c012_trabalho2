from __future__ import annotations

import unittest

from models import Process
from schedulers import schedule_priority, schedule_sjf


class TestSchedulingMetrics(unittest.TestCase):
    def test_process_uses_life_time_field_instead_of_priority(self) -> None:
        process = Process(id="P1", name="A", arrival_time=0, burst_time=2, life_time=4)

        self.assertEqual(process.life_time, 4)
        self.assertFalse(hasattr(process, "priority"))

    def test_waiting_turnaround_and_response_times_are_computed_correctly(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=5, life_time=20),
            Process(id="P2", name="B", arrival_time=1, burst_time=2, life_time=20),
            Process(id="P3", name="C", arrival_time=2, burst_time=1, life_time=20),
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
            Process(id="P1", name="A", arrival_time=3, burst_time=2, life_time=4),
            Process(id="P2", name="B", arrival_time=5, burst_time=1, life_time=3),
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

    def test_waiting_patients_lose_life_time_after_each_execution_completed(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=2, life_time=10),
            Process(id="P2", name="B", arrival_time=0, burst_time=4, life_time=6),
            Process(id="P3", name="C", arrival_time=1, burst_time=1, life_time=9),
        ]

        result = schedule_sjf(processes)
        patient_results = result.patient_result_by_process_id()

        self.assertEqual(patient_results["P1"].life_time_final, 10)
        self.assertEqual(patient_results["P2"].life_time_final, 3)
        self.assertEqual(patient_results["P3"].life_time_final, 8)

    def test_patients_not_arrived_do_not_lose_life_before_arrival(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=2, life_time=10),
            Process(id="P2", name="B", arrival_time=1, burst_time=1, life_time=5),
        ]

        result = schedule_sjf(processes)
        patient_results = result.patient_result_by_process_id()

        self.assertEqual(patient_results["P2"].life_time_final, 4)

    def test_patient_in_execution_does_not_lose_life_time(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=3, life_time=2),
            Process(id="P2", name="B", arrival_time=0, burst_time=1, life_time=10),
        ]

        result = schedule_priority(processes)
        patient_results = result.patient_result_by_process_id()

        self.assertEqual(patient_results["P1"].life_time_final, 2)

    def test_patient_that_reaches_zero_life_while_waiting_dies_and_is_not_executed(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=2, life_time=5),
            Process(id="P2", name="B", arrival_time=0, burst_time=4, life_time=1),
        ]

        result = schedule_sjf(processes)
        patient_results = result.patient_result_by_process_id()

        self.assertEqual(result.execution_order, ("P1",))
        self.assertFalse(patient_results["P2"].survived)
        self.assertEqual(patient_results["P2"].death_time, 1)
        self.assertIsNone(patient_results["P2"].start_time)

    def test_survival_counts_and_cross_algorithm_difference(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=3, life_time=2),
            Process(id="P2", name="B", arrival_time=0, burst_time=3, life_time=5),
            Process(id="P3", name="C", arrival_time=0, burst_time=1, life_time=9),
            Process(id="P4", name="D", arrival_time=1, burst_time=1, life_time=8),
            Process(id="P5", name="E", arrival_time=10, burst_time=1, life_time=4),
        ]

        sjf_result = schedule_sjf(processes)
        ps_result = schedule_priority(processes)

        self.assertEqual(sjf_result.survived_count, 4)
        self.assertEqual(sjf_result.deceased_count, 1)
        self.assertEqual(ps_result.survived_count, 5)
        self.assertEqual(ps_result.deceased_count, 0)
        self.assertFalse(sjf_result.patient_result_by_process_id()["P1"].survived)
        self.assertTrue(ps_result.patient_result_by_process_id()["P1"].survived)


if __name__ == "__main__":
    unittest.main()
