import pytest

from heavyforge.enums import AuthorityLevel
from heavyforge.judge import call_judge
from heavyforge.kernel import heavy_run
from heavyforge.testing.stub_provider import StubProvider


@pytest.mark.asyncio
async def test_judge_decision_has_no_authority_level_field():
    provider = StubProvider()
    decision, repaired, error_msg = await call_judge(
        provider=provider,
        worker_results=[],
        timeout=0.2,
    )

    assert error_msg is None
    assert repaired is False
    assert decision is not None
    assert not hasattr(decision, "authority_level")


@pytest.mark.asyncio
async def test_kernel_not_judge_assigns_authority():
    provider = StubProvider()
    receipt = await heavy_run(
        provider=provider,
        user_prompt="Test prompt.",
        run_id="hf_test_authority_boundary",
        worker_timeout=0.2,
        judge_timeout=0.2,
    )

    assert receipt.authority_level == AuthorityLevel.EVIDENCE_SUPPORTED
