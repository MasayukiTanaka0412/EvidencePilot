from __future__ import annotations

import logging
from pathlib import Path

from azure_devops_client import AzureDevOpsClient, AzureDevOpsError
from capture import MonitorError, MonitorInfo, ScreenCapture
from config_loader import AppConfig
from models import TestCaseData
from utils import ensure_directory, sanitize_name


class EvidencePilotCLI:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.azdo = AzureDevOpsClient(config.azdo_org_url, config.azdo_project, config.azdo_pat)
        self.capture = ScreenCapture()

    def run(self) -> None:
        monitor = self._choose_monitor()
        if not monitor:
            return

        while True:
            selection = self._input_suite_case()
            if selection is None:
                print("Goodbye.")
                return
            suite_id, case_id = selection

            try:
                case_data = self.azdo.get_test_case(suite_id, case_id)
            except AzureDevOpsError as exc:
                logging.exception("Failed to fetch test case")
                print(f"Error: {exc}")
                continue

            self._show_case(case_data)
            if not self._confirm_case():
                continue

            action = self._execute_case(case_data, monitor)
            if action == "quit":
                print("Goodbye.")
                return

    def _choose_monitor(self) -> MonitorInfo | None:
        try:
            monitors = self.capture.list_monitors()
        except MonitorError as exc:
            logging.exception("Monitor detection failed")
            print(f"Error: {exc}")
            return None

        print("Connected monitors:")
        for monitor in monitors:
            primary = " (Primary)" if monitor.is_primary else ""
            print(
                f"  [{monitor.index}] {monitor.width}x{monitor.height} "
                f"at ({monitor.x}, {monitor.y}){primary}"
            )

        while True:
            value = input("Choose monitor number for screenshot capture (or Q to quit): ").strip()
            if value.upper() == "Q":
                return None
            if value.isdigit():
                chosen = int(value)
                for monitor in monitors:
                    if monitor.index == chosen:
                        return monitor
            print("Invalid selection. Please enter a valid monitor number.")

    def _input_suite_case(self) -> tuple[int, int] | None:
        while True:
            suite_raw = input("Enter Suite ID (or Q to quit): ").strip()
            if suite_raw.upper() == "Q":
                return None

            case_raw = input("Enter Case ID (or Q to quit): ").strip()
            if case_raw.upper() == "Q":
                return None

            if suite_raw.isdigit() and case_raw.isdigit():
                return int(suite_raw), int(case_raw)

            print("Suite ID and Case ID must be numeric.")

    def _show_case(self, case_data: TestCaseData) -> None:
        print("\n=== Test Case Information ===")
        print(f"Suite ID: {case_data.suite_id}")
        print(f"Suite Name: {case_data.suite_name}")
        print(f"Case ID: {case_data.case_id}")
        print(f"Case Name: {case_data.case_name}")
        print("Steps:")
        if not case_data.steps:
            print("  (No steps found)")
        for step in case_data.steps:
            print(f"  {step.number}. Action: {step.action}")
            print(f"     Expected: {step.expected_result}")

    def _confirm_case(self) -> bool:
        while True:
            value = input("Is this the correct test case? (Y/N): ").strip().upper()
            if value == "Y":
                return True
            if value == "N":
                return False
            print("Please enter Y or N.")

    def _execute_case(self, case_data: TestCaseData, monitor: MonitorInfo) -> str:
        if not case_data.steps:
            print("No steps available for this test case.")
            return "back"

        per_step_sequence: dict[int, int] = {}
        index = 0

        while 0 <= index < len(case_data.steps):
            step = case_data.steps[index]
            print("\n----------------------------------------")
            print(f"Step {step.number}/{len(case_data.steps)}")
            print(f"Action: {step.action}")
            print(f"Expected: {step.expected_result}")
            print("[E] Capture screenshot")
            print("[N] Next step")
            print("[S] Back to suite/case selection")
            print("[Q] Quit")
            cmd = input("Choose command: ").strip().upper()

            if cmd == "E":
                per_step_sequence[step.number] = per_step_sequence.get(step.number, 0) + 1
                self._capture_step(case_data, step.number, step.action, per_step_sequence[step.number], monitor)
                continue
            if cmd == "N":
                if index == len(case_data.steps) - 1:
                    print("Case completed.")
                    return "back"
                index += 1
                continue
            if cmd == "S":
                return "back"
            if cmd == "Q":
                return "quit"

            print("Invalid command. Please use E, N, S, or Q.")

        return "back"

    def _capture_step(
        self,
        case_data: TestCaseData,
        step_number: int,
        step_action: str,
        sequence: int,
        monitor: MonitorInfo,
    ) -> None:
        suite_folder = f"{case_data.suite_id}_{sanitize_name(case_data.suite_name, 60)}"
        case_folder = f"{case_data.case_id}_{sanitize_name(case_data.case_name, 60)}"
        step_label = sanitize_name(step_action, self.config.step_name_max_length)

        base_dir = Path(self.config.capture_root) / suite_folder / case_folder
        ensure_directory(base_dir)

        filename = f"{step_number:02d}_{step_label}_{sequence:02d}.png"
        output_path = base_dir / filename

        try:
            self.capture.capture_monitor(monitor, output_path)
            print(f"Screenshot saved: {output_path.as_posix()}")
        except Exception as exc:  # noqa: BLE001
            logging.exception("Screenshot save failed")
            print(f"Failed to save screenshot: {exc}")
