from __future__ import annotations

from .models import KaskalCodeReceipt, PolicyStatus


def render_markdown_receipt(receipt: KaskalCodeReceipt) -> str:
    """Render a concise, boardroom-safe PR comment."""

    lines = [
        "## Kaskal Verified Receipt",
        "",
        f"Decision: **{receipt.decision.value}**  ",
        f"Mode: `{receipt.mode.value}`  ",
        f"Check Conclusion: `{receipt.check_conclusion.value}`  ",
        f"Authority Level: `{receipt.authority_level.value}`  ",
        f"Replay Status: `{receipt.replay_status.value}`  ",
        f"Receipt Hash: `sha256:{receipt.receipt_hash}`  ",
    ]
    if receipt.ledger_sequence is not None:
        lines.append(f"Ledger Sequence: `{receipt.ledger_sequence}`  ")
    if receipt.commit_sha:
        lines.append(f"Commit SHA: `{receipt.commit_sha}`  ")
    if receipt.pr_number is not None:
        lines.append(f"PR: `#{receipt.pr_number}`  ")
    lines.extend(
        [
            f"Changed Lines: `{receipt.changed_lines}`  ",
            "",
            "### Policy Results",
        ]
    )

    for result in receipt.policy_results:
        label = _display_name(result.name)
        status = result.status.value
        reason = result.reason
        lines.append(f"- **{label}: {status}** — {reason}")
        if result.status != PolicyStatus.PASS and result.evidence:
            evidence = ", ".join(f"`{item}`" for item in result.evidence[:3])
            lines.append(f"  - Evidence: {evidence}")

    lines.extend(
        [
            "",
            "### Summary",
            receipt.summary,
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _display_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.split("_"))
