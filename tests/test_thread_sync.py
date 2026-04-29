from __future__ import annotations

import unittest

from models import Process
from schedulers import schedule_sjf
from thread_sync import (
    PatientRequest,
    build_patient_requests,
    render_synchronization_report,
    run_thread_synchronization_demo,
)


class TestThreadSynchronization(unittest.TestCase):
    def test_build_patient_requests_is_reproducible_with_seed(self) -> None:
        processes = [
            Process(id="P1", name="A", arrival_time=0, burst_time=5, life_time=2),
            Process(id="P2", name="B", arrival_time=1, burst_time=2, life_time=6),
            Process(id="P3", name="C", arrival_time=2, burst_time=3, life_time=3),
        ]
        source = schedule_sjf(processes)

        first = build_patient_requests(source, seed=42)
        second = build_patient_requests(source, seed=42)

        self.assertEqual(first, second)

    def test_lock_mode_keeps_consistency(self) -> None:
        requests = [
            PatientRequest("P1", "A", requested_units=2, prep_delay_s=0.0, critical_delay_s=0.0),
            PatientRequest("P2", "B", requested_units=2, prep_delay_s=0.0, critical_delay_s=0.0),
            PatientRequest("P3", "C", requested_units=2, prep_delay_s=0.0, critical_delay_s=0.0),
        ]

        result = run_thread_synchronization_demo(
            patient_requests=requests,
            doctor_count=3,
            initial_stock=4,
            use_lock=True,
        )

        self.assertTrue(result.consistency_ok)
        self.assertEqual(result.total_requested, 6)
        self.assertEqual(result.total_granted, 4)
        self.assertEqual(result.final_stock, 0)
        self.assertEqual(result.attended_count, 2)
        self.assertEqual(result.not_attended_count, 1)
        self.assertEqual(len(result.chart_entries), 3)
        self.assertEqual(len(result.logs), 3)

    def test_render_report_contains_required_summary_fields(self) -> None:
        requests = [
            PatientRequest("P1", "A", requested_units=1, prep_delay_s=0.0, critical_delay_s=0.0),
            PatientRequest("P2", "B", requested_units=1, prep_delay_s=0.0, critical_delay_s=0.0),
        ]

        unsafe_result = run_thread_synchronization_demo(
            patient_requests=requests,
            doctor_count=2,
            initial_stock=1,
            use_lock=False,
        )
        safe_result = run_thread_synchronization_demo(
            patient_requests=requests,
            doctor_count=2,
            initial_stock=1,
            use_lock=True,
        )

        report = render_synchronization_report(
            source_algorithm_name="SJF (nao-preemptivo)",
            patient_requests=requests,
            unsafe_result=unsafe_result,
            safe_result=safe_result,
        )

        self.assertIn("Parte 2 - Sincronizacao de Threads", report)
        self.assertIn("Logs de atendimento:", report)
        self.assertIn("estoque inicial", report)
        self.assertIn("total solicitado", report)
        self.assertIn("total concedido", report)
        self.assertIn("entradas no prontuario", report)
        self.assertIn("consistencia", report)


if __name__ == "__main__":
    unittest.main()
