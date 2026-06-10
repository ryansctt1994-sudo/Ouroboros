from __future__ import annotations

import asyncio

from pydantic import ValidationError

from .contracts import WorkerOutput
from .enums import FailureType
from .provider_protocol import ProviderProtocol


async def call_worker(
    provider: ProviderProtocol,
    agent_name: str,
    role_prompt: str,
    user_prompt: str,
    timeout: float = 20.0,
    allow_schema_repair: bool = True,
) -> WorkerOutput:
    """Call one worker and always return a WorkerOutput.

    The TaskGroup supervisor must not receive unhandled provider/schema/timeout
    exceptions from workers. Every failure is converted into a failed witness.
    """

    try:
        async with asyncio.timeout(timeout):
            raw = await provider.complete_worker(
                agent_name=agent_name,
                role_prompt=role_prompt,
                user_prompt=user_prompt,
            )
    except TimeoutError:
        return WorkerOutput(
            agent_name=agent_name,
            failed=True,
            failure_type=FailureType.TIMEOUT,
            error_msg=f"Worker exceeded timeout={timeout}s",
        )
    except Exception as exc:
        return WorkerOutput(
            agent_name=agent_name,
            failed=True,
            failure_type=FailureType.API_ERROR,
            error_msg=str(exc),
        )

    if not raw or not raw.strip():
        return WorkerOutput(
            agent_name=agent_name,
            failed=True,
            failure_type=FailureType.EMPTY_RESPONSE,
            error_msg="Provider returned empty response.",
        )

    try:
        parsed = WorkerOutput.model_validate_json(raw)
        parsed.raw_output = raw
        return parsed
    except ValidationError as first_error:
        if not allow_schema_repair:
            return WorkerOutput(
                agent_name=agent_name,
                failed=True,
                failure_type=FailureType.SCHEMA_INVALID,
                error_msg=str(first_error),
                raw_output=raw,
            )

        try:
            repaired_raw = await provider.repair_worker_output(
                agent_name=agent_name,
                bad_output=raw,
                validation_error=str(first_error),
            )
            repaired = WorkerOutput.model_validate_json(repaired_raw)
            repaired.repaired = True
            repaired.raw_output = raw
            return repaired
        except Exception as repair_error:
            return WorkerOutput(
                agent_name=agent_name,
                failed=True,
                failure_type=FailureType.SCHEMA_REPAIR_FAILED,
                error_msg=(
                    f"Initial validation: {first_error}; "
                    f"repair failed: {repair_error}"
                ),
                raw_output=raw,
            )
