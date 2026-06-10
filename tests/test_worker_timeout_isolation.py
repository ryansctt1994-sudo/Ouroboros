import pytest

from heavyforge.enums import AuthorityLevel, FailureType
from heavyforge.kernel import heavy_run
from heavyforge.testing.stub_provider import Scenario, StubProvider


@pytest.mark.asyncio
async def test_timeout_does_not_cancel_swarm():
    provider = StubProvider(
        worker_scenarios={"builder": Scenario.TIMEOUT},
    )

    receipt = await heavy_run(
        provider=provider,
        user_prompt="Test prompt.",
        run_id="hf_test_timeout",
        worker_timeout=0.01,
        judge_timeout=0.2,
    )

    assert receipt.authority_level == AuthorityLevel.DRAFT
    assert len(receipt.agents) == 5

    builder = next(worker for worker in receipt.agents if worker.agent_name == "builder")
    direct_solver = next(worker for worker in receipt.agents if worker.agent_name == "direct_solver")

    assert builder.failed is True
    assert builder.failure_type == FailureType.TIMEOUT
    assert direct_solver.failed is False
