from __future__ import annotations

import unittest

from cli import _prompt_processes


class TestInteractiveCli(unittest.TestCase):
    def test_prompt_processes_collects_manual_entries(self) -> None:
        answers = iter(
            [
                "Alice",
                "",
                "5",
                "8",
                "Bob",
                "2",
                "1",
                "3",
                "",
            ]
        )
        messages: list[str] = []

        def fake_input(prompt: str) -> str:
            return next(answers)

        processes = _prompt_processes(input_func=fake_input, output_func=messages.append)

        self.assertEqual(len(processes), 2)
        self.assertEqual(processes[0].id, "P1")
        self.assertEqual(processes[0].name, "Alice")
        self.assertEqual(processes[0].arrival_time, 0)
        self.assertEqual(processes[0].burst_time, 5)
        self.assertEqual(processes[0].life_time, 8)
        self.assertEqual(processes[1].id, "P2")
        self.assertEqual(processes[1].name, "Bob")
        self.assertEqual(processes[1].arrival_time, 2)
        self.assertEqual(processes[1].burst_time, 1)
        self.assertEqual(processes[1].life_time, 3)
        self.assertIn("2 processo(s) cadastrado(s).", messages)


if __name__ == "__main__":
    unittest.main()
