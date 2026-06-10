from __future__ import annotations

from typing import Protocol


class ProviderProtocol(Protocol):
    async def complete_worker(
        self,
        agent_name: str,
        role_prompt: str,
        user_prompt: str,
    ) -> str:
        ...

    async def repair_worker_output(
        self,
        agent_name: str,
        bad_output: str,
        validation_error: str,
    ) -> str:
        ...

    async def complete_judge(
        self,
        judge_prompt: str,
        worker_outputs_json: str,
    ) -> str:
        ...

    async def repair_judge_output(
        self,
        bad_output: str,
        validation_error: str,
    ) -> str:
        ...
