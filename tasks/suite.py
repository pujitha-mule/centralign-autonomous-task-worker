from __future__ import annotations
from dataclasses import dataclass


@dataclass
class TaskSpec:
    name: str
    instruction: str
    expected_evidence: str
    namespace: str = "demo-company"


TASKS: list[TaskSpec] = [
    TaskSpec(
        name="acme_latest_invoice",
        instruction=(
            "Find the latest invoice from Acme Corp in the invoices folder, "
            "extract the amount and due date, enter it into our internal tracker, "
            "and confirm it's done."
        ),
        expected_evidence="ACME-2024-03",
    ),
    TaskSpec(
        name="otherco_invoice",
        instruction=(
            "Process the latest OtherCo invoice: find it in the invoices folder, "
            "extract the amount and due date, enter it into our internal tracker, "
            "and confirm it's done."
        ),
        expected_evidence="OTHER-2024-02",
    ),
]