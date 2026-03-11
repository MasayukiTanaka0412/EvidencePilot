from __future__ import annotations

import base64
import logging
from typing import Any, Dict, List
import xml.etree.ElementTree as ET

import requests

from models import TestCaseData, TestStep
from utils import html_to_text


class AzureDevOpsError(Exception):
    pass


class AzureDevOpsClient:
    def __init__(self, org_url: str, project: str, pat: str, timeout: int = 30) -> None:
        self.org_url = org_url.rstrip("/")
        self.project = project
        self.timeout = timeout
        token = base64.b64encode(f":{pat}".encode("utf-8")).decode("utf-8")
        self.headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    def _get(self, url: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        try:
            response = requests.get(url, headers=self.headers, params=None, timeout=self.timeout)
        except requests.RequestException as exc:
            raise AzureDevOpsError(f"Connection to Azure DevOps failed: {exc}") from exc

        if response.status_code >= 400:
            message = response.text.strip()[:300]
            raise AzureDevOpsError(f"Azure DevOps request failed ({response.status_code}): {message}")

        return response.json()

    def _find_suite_plan(self, suite_id: int) -> tuple[int, str]:
        plans_url = f"{self.org_url}/{self.project}/_apis/test/plans"
        plans = self._get(plans_url, params={"api-version": "7.1"}).get("value", [])

        for plan in plans:
            plan_id = int(plan["id"])
            suite_url = f"{self.org_url}/{self.project}/_apis/test/Plans/{plan_id}/suites/{suite_id}"
            try:
                suite = self._get(suite_url, params={"api-version": "7.1"})
                return plan_id, suite.get("name", f"Suite {suite_id}")
            except AzureDevOpsError:
                continue

        raise AzureDevOpsError(f"Suite not found: {suite_id}")

    def _suite_contains_case(self, plan_id: int, suite_id: int, case_id: int) -> bool:
        url = f"{self.org_url}/{self.project}/_apis/test/Plans/{plan_id}/suites/{suite_id}/testcases"
        payload = self._get(url, params={"api-version": "7.1"})
        for item in payload.get("value", []):
            point = item.get("testCase") or {}
            if str(point.get("id")) == str(case_id):
                return True
        return False

    def _fetch_case_work_item(self, case_id: int) -> Dict[str, Any]:
        url = f"{self.org_url}/{self.project}/_apis/wit/workitems/{case_id}"
        params = {
            "api-version": "7.1",
            "fields": "System.Title,Microsoft.VSTS.TCM.Steps",
        }
        return self._get(url, params=params)

    def _parse_steps(self, xml_text: str) -> List[TestStep]:
        if not xml_text:
            return []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logging.exception("Failed to parse step XML")
            raise AzureDevOpsError(f"Failed to parse test steps: {exc}") from exc

        steps: List[TestStep] = []
        for index, node in enumerate(root.findall("step"), start=1):
            parameterized = node.find("parameterizedString")
            expected_node = node.find("expected")

            action = html_to_text(parameterized.text if parameterized is not None else "")
            expected = html_to_text(expected_node.text if expected_node is not None else "")
            steps.append(TestStep(number=index, action=action or "(No action)", expected_result=expected or "(No expected result)"))

        return steps

    def get_test_case(self, suite_id: int, case_id: int) -> TestCaseData:
        plan_id, suite_name = self._find_suite_plan(suite_id)

        if not self._suite_contains_case(plan_id, suite_id, case_id):
            raise AzureDevOpsError(f"Case {case_id} was not found in suite {suite_id}")

        work_item = self._fetch_case_work_item(case_id)
        fields = work_item.get("fields", {})
        case_name = fields.get("System.Title", f"Case {case_id}")
        steps_xml = fields.get("Microsoft.VSTS.TCM.Steps", "")

        return TestCaseData(
            suite_id=suite_id,
            suite_name=suite_name,
            case_id=case_id,
            case_name=case_name,
            steps=self._parse_steps(steps_xml),
        )
