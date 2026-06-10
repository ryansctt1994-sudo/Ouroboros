from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum


class Scenario(str, Enum):
    VALID = "VALID"
    MALFORMED_JSON = "MALFORMED_JSON"
    SCHEMA_INVALID = "SCHEMA_INVALID"
    TIMEOUT = "TIMEOUT"
    API_ERROR = "API_ERROR"
    EMPTY = "EMPTY"


@dataclass
class StubProvider:
    worker_scenarios: dict[str, Scenario] = field(default_factory=dict)
    repair_succeeds: bool = True
    judge_scenario: Scenario = Scenario.VALID
    judge_repair_succeeds: bool = True
    repair_calls: int = 0
    judge_repair_calls: int = 0

    async def complete_worker(
        self,
        agent_name: str,
        role_prompt: str,
        user_prompt: str,
    ) -> str:
        scenario = self.worker_scenarios.get(agent_name, Scenario.VALID)

        if scenario == Scenario.VALID:
            return json.dumps({
                "agent_name": agent_name,
                "answer": f"{agent_name} valid answer",
                "assumptions": [],
                "evidence": [],
                "objections": [],
                "confidence": 0.8,
                "failed": False,
            })

        if scenario == Scenario.MALFORMED_JSON:
            return "{not valid json"

        if scenario == Scenario.SCHEMA_INVALID:
            return json.dumps({
                "agent_name": agent_name,
                "answer": 123,
                "confidence": 2.4,
            })

        if scenario == Scenario.TIMEOUT:
            await asyncio.sleep(999)
            return ""

        if scenario == Scenario.API_ERROR:
            raise RuntimeError("simulated provider outage")

        if scenario == Scenario.EMPTY:
            return ""

        raise AssertionError(f"Unhandled worker scenario: {scenario}")

    async def repair_worker_output(
        self,
        agent_name: str,
        bad_output: str,
        validation_error: str,
    ) -> str:
        self.repair_calls += 1

        if not self.repair_succeeds:
            return "{still invalid json"

        return json.dumps({
            "agent_name": agent_name,
            "answer": "repaired answer",
            "assumptions": [],
            "evidence": [],
            "objections": [],
            "confidence": 0.5,
            "failed": False,
        })

    async def complete_judge(
        self,
        judge_prompt: str,
        worker_outputs_json: str,
    ) -> str:
        if self.judge_scenario == Scenario.VALID:
            return json.dumps({
                "consensus": ["valid consensus"],
                "unresolved_disputes": [],
                "missing_evidence": [],
                "strongest_answer": "valid synthesis",
                "judge_confidence": 0.9,
                "evidence_notes": ["structured evidence note"],
                "judge_warnings": [],
            })

        if self.judge_scenario == Scenario.MALFORMED_JSON:
            return "{not valid json"

        if self.judge_scenario == Scenario.SCHEMA_INVALID:
            return json.dumps({
                "strongest_answer": 123,
                "judge_confidence": 3.0,
            })

        if self.judge_scenario == Scenario.TIMEOUT:
            await asyncio.sleep(999)
            return ""

        if self.judge_scenario == Scenario.API_ERROR:
            raise RuntimeError("simulated judge outage")

        if self.judge_scenario == Scenario.EMPTY:
            return ""

        raise AssertionError(f"Unhandled judge scenario: {self.judge_scenario}")

    async def repair_judge_output(
        self,
        bad_output: str,
        validation_error: str,
    ) -> str:
        self.judge_repair_calls += 1

        if not self.judge_repair_succeeds:
            return "{still invalid json"

        return json.dumps({
            "consensus": [],
            "unresolved_disputes": ["judge output required repair"],
            "missing_evidence": [],
            "strongest_answer": "repaired synthesis",
            "judge_confidence": 0.5,
            "evidence_notes": [],
            "judge_warnings": ["schema repaired"],
        })
