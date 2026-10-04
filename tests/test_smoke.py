import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_imports():
    from agent import run_agent, LLM  # noqa
    from agent.tools import default_tools  # noqa


def test_files_tool_sandbox():
    from agent.tools.files import FilesListTool
    obs = FilesListTool().run(path="invoices", pattern="acme")
    assert obs.ok
    assert any("acme_invoice_2024_03" in f for f in obs.output["files"])


def test_extraction_is_generic():
    from agent.llm import LLM
    llm = LLM()
    text = (
        "INVOICE  ZZZ-2099-42\n"
        "Vendor: Zeta Zeta Ltd\n"
        "Amount: 42.50\n"
        "Due Date: 2099-12-31\n"
    )
    fields = llm._extract_fields(text)
    assert fields["invoice_id"] == "ZZZ-2099-42"
    assert fields["company"] == "Zeta Zeta Ltd"
    assert fields["amount"] == "42.50"
    assert fields["due_date"] == "2099-12-31"