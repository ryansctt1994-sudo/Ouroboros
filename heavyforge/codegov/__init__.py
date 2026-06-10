"""Kaskal Code Governance pure-function MVP.

This package turns a raw pull-request diff plus a local .kaskal.yml policy
configuration into a concise, receipt-backed governance decision.
"""

from .engine import analyze_diff
from .models import Decision, KaskalCodeReceipt, PolicyResult

__all__ = [
    "analyze_diff",
    "Decision",
    "KaskalCodeReceipt",
    "PolicyResult",
]
