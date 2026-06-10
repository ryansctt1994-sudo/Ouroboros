from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from .authority import calculate_authority_level
from .contracts import JudgeDecision, JudgeReceipt, WorkerOutput
from .judge import call_judge
from .provider_protocol import ProviderProtocol
from .worker import call_worker


DEFAULT_AGENTS: tuple[tuple[str, str], ...] = (
    ("direct_solver", "Solve directly. Be precise."),
    ("skeptic", "Find flaws, hidden assumptions, and weak claims."),
    ("researcher", "Identify what must be verified with sources."),
    ("builder", "Convert the answer into an executable plan."),
    ("alternative", "Develop a competing hypothesis."),
)


def build_receipt(
    run_id: str,
    user_prompt: str,
    worker_results: list[WorkerOutput],
    judge_decision: JudgeDecision | None,
    judge_failed: bool,
    judge_repaired: bool,
    judge_error_msg: str | None,
    replay_verified: bool = False,
) -> JudgeReceipt:
    authority_level = calculate_authority_level(
        worker_results=worker_results,
        judge_decision=judge_decision,
        judge_failed=judge_failed,
        judge_repaired=judge_repaired,
        replay_verified=replay_verified,
    )

    failed_agents = [worker.agent_name for worker in worker_results if worker.failed]
    repaired_agents = [worker.agent_name for worker in worker_results if worker.repaired]

    if judge_decision is None:
        consensus: list[str] = []
        unresolved_disputes = ["Judge failed; no adjudicated consensus available."]
        missing_evidence = ["Judge decision unavailable."]
        strongest_answer = "No authoritative synthesis produced."
    else:
        consensus = judge_decision.consensus
        unresolved_disputes = list(judge_decision.unresolved_disputes)
        missing_evidence = judge_decision.missing_evidence
        strongest_answer = judge_decision.strongest_answer

    unresolved_disputes.extend(
        [
            f"Failed agents: {failed_agents}" if failed_agents else "No failed agents.",
            f"Repaired agents: {repaired_agents}" if repaired_agents else "No repaired agents.",
        ]
    )

    return JudgeReceipt(
        run_id=run_id,
        user_prompt=user_prompt,
        consensus=consensus,
        unresolved_disputes=unresolved_disputes,
        missing_evidence=missing_evidence,
        strongest_answer=strongest_answer,
        authority_level=authority_level,
        timestamp=datetime.now(UTC).isoformat(),
        agents=worker_results,
        judge_failed=judge_failed,
        judge_repaired=judge_repaired,
        judge_error_msg=judge_error_msg,
    )


async def run_workers(
    provider: ProviderProtocol,
    user_prompt: str,
    agents: tuple[tuple[str, str], ...] = DEFAULT_AGENTS,
    worker_timeout: float = 20.0,
) -> list[WorkerOutput]:
    tasks: list[asyncio.Task[WorkerOutput]] = []

    async with asyncio.TaskGroup() as task_group:
        for name, role_prompt in agents:
            tasks.append(
                task_group.create_task(
                    call_worker(
                        provider=provider,
                        agent_name=name,
                        role_prompt=role_prompt,
                        user_prompt=user_prompt,
                        timeout=worker_timeout,
                    ),
                    name=f"worker:{name}",
                )
            )

    return [task.result() for task in tasks]


async def heavy_run(
    provider: ProviderProtocol,
    user_prompt: str,
    run_id: str | None = None,
    agents: tuple[tuple[str, str], ...] = DEFAULT_AGENTS,
    worker_timeout: float = 20.0,
    judge_timeout: float = 30.0,
) -> JudgeReceipt:
    actual_run_id = run_id or f"hf_{uuid4().hex}"

    worker_results = await run_workers(
        provider=provider,
        user_prompt=user_prompt,
        agents=agents,
        worker_timeout=worker_timeout,
    )

    judge_decision, judge_repaired, judge_error_msg = await call_judge(
        provider=provider,
        worker_results=worker_results,
        timeout=judge_timeout,
    )

    return build_receipt(
        run_id=actual_run_id,
        user_prompt=user_prompt,
        worker_results=worker_results,
        judge_decision=judge_decision,
        judge_failed=judge_decision is None,
        judge_repaired=judge_repaired,
        judge_error_msg=judge_error_msg,
        replay_verified=False,
    )
