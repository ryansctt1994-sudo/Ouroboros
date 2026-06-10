from __future__ import annotations

from pathlib import Path
from typing import Any

from heavyforge.enums import AuthorityLevel
from heavyforge.receipts import canonical_json_bytes, sha256_hex

from .config import KaskalConfig, load_config_file
from .diff_parser import parse_unified_diff
from .models import KaskalCodeReceipt, ReplayStatus
from .policy import decide, map_check_conclusion, run_policies
from .receipt_renderer import render_markdown_receipt


def analyze_diff(
    diff_text: str,
    config: KaskalConfig | None = None,
    *,
    project: str = "unknown",
    commit_sha: str | None = None,
    pr_number: int | None = None,
    ledger_sequence: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> KaskalCodeReceipt:
    config = config or KaskalConfig()
    summary = parse_unified_diff(diff_text)
    policy_results = run_policies(summary, config)
    decision = decide(policy_results)
    check_conclusion = map_check_conclusion(decision, config.mode)
    changed_files = [changed.path for changed in summary.changed_files]

    receipt = KaskalCodeReceipt(
        project=project,
        commit_sha=commit_sha,
        pr_number=pr_number,
        mode=config.mode,
        decision=decision,
        check_conclusion=check_conclusion,
        authority_level=AuthorityLevel.EVIDENCE_SUPPORTED,
        replay_status=ReplayStatus.NOT_REPLAY_VERIFIED,
        receipt_hash="",
        ledger_sequence=ledger_sequence,
        changed_files=changed_files,
        changed_lines=summary.changed_lines,
        policy_results=policy_results,
        summary=_summary_for_decision(decision.value),
        metadata=metadata or {},
    )
    receipt.receipt_hash = compute_code_receipt_hash(receipt)
    return receipt


def analyze_diff_file(
    diff_path: Path | str,
    config_path: Path | str | None = None,
    **kwargs: Any,
) -> KaskalCodeReceipt:
    diff_text = Path(diff_path).read_text(encoding="utf-8")
    config = load_config_file(config_path)
    return analyze_diff(diff_text, config=config, **kwargs)


def render_receipt_for_diff(
    diff_text: str,
    config: KaskalConfig | None = None,
    **kwargs: Any,
) -> tuple[KaskalCodeReceipt, str]:
    receipt = analyze_diff(diff_text, config=config, **kwargs)
    return receipt, render_markdown_receipt(receipt)


def compute_code_receipt_hash(receipt: KaskalCodeReceipt) -> str:
    payload = receipt.model_dump(mode="json")
    payload["receipt_hash"] = ""
    return sha256_hex(canonical_json_bytes(payload))


def _summary_for_decision(decision: str) -> str:
    if decision == "PASS":
        return "This pull request passed the enabled Kaskal governance policies."
    if decision == "WARN":
        return "This pull request produced non-blocking governance warnings. Human review is recommended before merge."
    return "This pull request triggered a blocking governance failure or requires human override before merge."
