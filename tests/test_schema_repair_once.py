import pytest

from heavyforge.enums import FailureType
from heavyforge.testing.stub_provider import Scenario, StubProvider
from heavyforge.worker import call_worker


@pytest.mark.asyncio
async def test_schema_repair_attempted_once():
    provider = StubProvider(
        worker_scenarios={"skeptic": Scenario.SCHEMA_INVALID},
        repair_succeeds=True,
    )

    result = await call_worker(
        provider=provider,
        agent_name="skeptic",
        role_prompt="Find flaws.",
        user_prompt="Test prompt.",
        timeout=0.2,
    )

    assert result.failed is False
    assert result.repaired is True
    assert provider.repair_calls == 1
    assert result.raw_output is not None


@pytest.mark.asyncio
async def test_schema_repair_failure_fails_closed():
    provider = StubProvider(
        worker_scenarios={"skeptic": Scenario.SCHEMA_INVALID},
        repair_succeeds=False,
    )

    result = await call_worker(
        provider=provider,
        agent_name="skeptic",
        role_prompt="Find flaws.",
        user_prompt="Test prompt.",
        timeout=0.2,
    )

    assert result.failed is True
    assert result.failure_type == FailureType.SCHEMA_REPAIR_FAILED
    assert provider.repair_calls == 1
    assert result.raw_output is not None
