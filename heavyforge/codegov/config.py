from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from .models import ReviewMode


class ThresholdConfig(BaseModel):
    full_review_max_changed_lines: int = 800
    warn_max_changed_lines: int = 2500


class PolicyConfig(BaseModel):
    secrets_exposure: bool = True
    dangerous_file_mutation: bool = True
    dependency_risk: bool = True
    test_impact: bool = True
    large_diff_risk: bool = True


class CommentConfig(BaseModel):
    verbosity: str = "concise"


class ReceiptConfig(BaseModel):
    include_hash: bool = True
    include_policy_results: bool = True


class KaskalConfig(BaseModel):
    mode: ReviewMode = ReviewMode.OBSERVE
    thresholds: ThresholdConfig = Field(default_factory=ThresholdConfig)
    policies: PolicyConfig = Field(default_factory=PolicyConfig)
    comment: CommentConfig = Field(default_factory=CommentConfig)
    receipt: ReceiptConfig = Field(default_factory=ReceiptConfig)


def load_config_data(data: dict[str, Any] | None) -> KaskalConfig:
    return KaskalConfig.model_validate(data or {})


def load_config_file(path: Path | str | None) -> KaskalConfig:
    if path is None:
        return KaskalConfig()

    config_path = Path(path)
    if not config_path.exists():
        return KaskalConfig()

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ValueError(".kaskal.yml must contain a mapping at the top level.")
    return load_config_data(raw)
