from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class TestStep:
    number: int
    action: str
    expected_result: str


@dataclass
class TestCaseData:
    suite_id: int
    suite_name: str
    case_id: int
    case_name: str
    steps: List[TestStep]
