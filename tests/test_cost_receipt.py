"""Tests for v0.1.3 Cost Receipt feature."""

import pytest
from pydantic import ValidationError


class TestCostReceipt:
    def test_all_fields(self):
        from ampro import CostReceipt
        receipt = CostReceipt(
            agent_id="agent://worker.example.com",
            task_id="t-42",
            cost_usd=0.05,
            currency="USD",
            breakdown={"llm": 0.04, "tools": 0.01},
            token_usage={"input": 1000, "output": 500},
            duration_seconds=2.5,
            signature="sig_abc123",
            issued_at="2026-04-09T12:00:00Z",
        )
        assert receipt.agent_id == "agent://worker.example.com"
        assert receipt.task_id == "t-42"
        assert receipt.cost_usd == 0.05
        assert receipt.currency == "USD"
        assert receipt.breakdown == {"llm": 0.04, "tools": 0.01}
        assert receipt.token_usage == {"input": 1000, "output": 500}
        assert receipt.duration_seconds == 2.5
        assert receipt.signature == "sig_abc123"
        assert receipt.issued_at == "2026-04-09T12:00:00Z"

    def test_optional_fields_default_none(self):
        from ampro import CostReceipt
        receipt = CostReceipt(
            agent_id="agent://a.com",
            task_id="t-1",
            cost_usd=0.01,
            issued_at="2026-04-09T00:00:00Z",
        )
        assert receipt.breakdown is None
        assert receipt.token_usage is None
        assert receipt.duration_seconds is None
        assert receipt.signature is None

    def test_currency_defaults_to_usd(self):
        from ampro import CostReceipt
        receipt = CostReceipt(
            agent_id="agent://a.com",
            task_id="t-1",
            cost_usd=1.00,
            issued_at="2026-04-09T00:00:00Z",
        )
        assert receipt.currency == "USD"

    def test_missing_required_raises(self):
        from ampro import CostReceipt
        with pytest.raises(ValidationError):
            CostReceipt()


class TestCostReceiptChain:
    def test_starts_empty_with_zero_total(self):
        from ampro import CostReceiptChain
        chain = CostReceiptChain()
        assert chain.receipts == []
        assert chain.total_cost_usd == 0.0

    def test_add_receipt_appends_and_updates_total(self):
        from ampro import CostReceiptChain, CostReceipt
        chain = CostReceiptChain()
        receipt = CostReceipt(
            agent_id="agent://a.com",
            task_id="t-1",
            cost_usd=0.10,
            issued_at="2026-04-09T00:00:00Z",
        )
        chain.add_receipt(receipt)
        assert len(chain.receipts) == 1
        assert chain.total_cost_usd == pytest.approx(0.10)

    def test_multiple_receipts_maintain_order(self):
        from ampro import CostReceiptChain, CostReceipt
        chain = CostReceiptChain()

        r1 = CostReceipt(
            agent_id="agent://first.com",
            task_id="t-1",
            cost_usd=0.05,
            issued_at="2026-04-09T00:00:00Z",
        )
        r2 = CostReceipt(
            agent_id="agent://second.com",
            task_id="t-1",
            cost_usd=0.15,
            issued_at="2026-04-09T00:01:00Z",
        )
        r3 = CostReceipt(
            agent_id="agent://third.com",
            task_id="t-1",
            cost_usd=0.30,
            issued_at="2026-04-09T00:02:00Z",
        )

        chain.add_receipt(r1)
        chain.add_receipt(r2)
        chain.add_receipt(r3)

        assert len(chain.receipts) == 3
        assert chain.receipts[0].agent_id == "agent://first.com"
        assert chain.receipts[1].agent_id == "agent://second.com"
        assert chain.receipts[2].agent_id == "agent://third.com"
        assert chain.total_cost_usd == pytest.approx(0.50)


class TestTaskCompleteBodyCostReceipt:
    def test_accepts_cost_receipt_dict(self):
        from ampro import TaskCompleteBody
        body = TaskCompleteBody(
            task_id="t-99",
            result="done",
            cost_receipt={
                "agent_id": "agent://worker.com",
                "task_id": "t-99",
                "cost_usd": 0.25,
                "issued_at": "2026-04-09T00:00:00Z",
            },
        )
        assert body.cost_receipt is not None
        assert body.cost_receipt["cost_usd"] == 0.25

    def test_cost_receipt_defaults_to_none(self):
        from ampro import TaskCompleteBody
        body = TaskCompleteBody(
            task_id="t-100",
            result="done",
        )
        assert body.cost_receipt is None
