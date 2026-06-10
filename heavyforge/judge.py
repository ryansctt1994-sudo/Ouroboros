from __future__ import annotations

import asyncio

from pydantic import ValidationError

from .contracts import JudgeDecision, WorkerOutput
from .provider_protocol import ProviderProtocol


JUDGE_PROMPT = """
You are the hostile verifier.

Rules:
1. Consensus is not proof.
2. Repaired worker outputs are admissible but tainted.
3. Failed worker outputs must be preserved as evidence.
4. Unsupported claims must be downgraded.
5. You may not assign authority_level.
6. Return only the required JudgeDecision JSON schema.
""".strip()


async def call_judge(
    provider: ProviderProtocol,
    worker_results: list[WorkerOutput],
    timeout: float = 30.0,
    allow_schema_repair: bool = True,
) -> tuple[JudgeDecision | None, bool, str | None]:
    """Call the Judge and return (decision, repaired, error_msg).

    If the Judge fails, the Kernel must still build an emergency DRAFT receipt.
    """

    worker_outputs_json = "[" + ",".join(w.model_dump_json() for w in worker_results) + "]"

    try:
        async with asyncio.timeout(timeout):
            raw = await provider.complete_judge(
                judge_prompt=JUDGE_PROMPT,
                worker_outputs_json=worker_outputs_json,
            )
    except Exception as exc:
        return None, False, str(exc)

    try:
        return JudgeDecision.model_validate_json(raw), False, None
    except ValidationError as first_error:
        if not allow_schema_repair:
            return None, False, str(first_error)

        try:
            repaired_raw = await provider.repair_judge_output(
                bad_output=raw,
                validation_error=str(first_error),
            )
            repaired = JudgeDecision.model_validate_json(repaired_raw)
            return repaired, True, None
        except Exception as repair_error:
            return None, False, (
                f"Initial validation: {first_error}; repair failed: {repair_error}"
            )
