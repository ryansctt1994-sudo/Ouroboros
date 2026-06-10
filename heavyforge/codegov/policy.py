from __future__ import annotations

import re
from pathlib import PurePosixPath

from .config import KaskalConfig
from .models import Decision, DiffSummary, PolicyResult, PolicyStatus, ReviewMode, CheckConclusion


SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
)

DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "pom.xml",
    "build.gradle",
    "gradle.lockfile",
}

DANGEROUS_PATH_PARTS = {
    ".github/workflows",
    "scripts/deploy",
    "deploy",
    "deployment",
    "infra",
    "terraform",
    "auth",
    "security",
    "permissions",
    "iam",
}

SOURCE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cs", ".cpp", ".c", ".h"}
TEST_HINTS = {"test", "tests", "spec", "__tests__"}


def run_policies(summary: DiffSummary, config: KaskalConfig) -> list[PolicyResult]:
    results: list[PolicyResult] = []
    if config.policies.large_diff_risk:
        results.append(check_large_diff(summary, config))
    if config.policies.secrets_exposure:
        results.append(check_secrets_exposure(summary))
    if config.policies.dangerous_file_mutation:
        results.append(check_dangerous_file_mutation(summary))
    if config.policies.dependency_risk:
        results.append(check_dependency_risk(summary))
    if config.policies.test_impact:
        results.append(check_test_impact(summary))
    return results


def check_large_diff(summary: DiffSummary, config: KaskalConfig) -> PolicyResult:
    changed = summary.changed_lines
    full_max = config.thresholds.full_review_max_changed_lines
    warn_max = config.thresholds.warn_max_changed_lines
    if changed <= full_max:
        return PolicyResult(name="large_diff_risk", status=PolicyStatus.PASS, reason="Diff is within full-review threshold.")
    if changed <= warn_max:
        return PolicyResult(
            name="large_diff_risk",
            status=PolicyStatus.WARN,
            reason="Diff exceeds full-review threshold; chunked or human review recommended.",
            evidence=[f"changed_lines={changed}", f"full_review_max_changed_lines={full_max}"],
        )
    return PolicyResult(
        name="large_diff_risk",
        status=PolicyStatus.FAIL,
        reason="Diff exceeds maximum automated-review threshold; human override required.",
        evidence=[f"changed_lines={changed}", f"warn_max_changed_lines={warn_max}"],
    )


def check_secrets_exposure(summary: DiffSummary) -> PolicyResult:
    evidence: list[str] = []
    for line in summary.added_lines:
        for pattern in SECRET_PATTERNS:
            if pattern.search(line):
                evidence.append(_redact_line(line))
                break
    if evidence:
        return PolicyResult(
            name="secrets_exposure",
            status=PolicyStatus.FAIL,
            reason="Secret-like content appears in added lines.",
            evidence=evidence[:5],
        )
    return PolicyResult(name="secrets_exposure", status=PolicyStatus.PASS, reason="No secret-like additions detected.")


def check_dangerous_file_mutation(summary: DiffSummary) -> PolicyResult:
    paths = [changed.path for changed in summary.changed_files]
    flagged = [path for path in paths if _is_dangerous_path(path)]
    if flagged:
        return PolicyResult(
            name="dangerous_file_mutation",
            status=PolicyStatus.WARN,
            reason="Security-sensitive or deployment-sensitive files changed.",
            evidence=flagged[:10],
        )
    return PolicyResult(name="dangerous_file_mutation", status=PolicyStatus.PASS, reason="No sensitive path mutations detected.")


def check_dependency_risk(summary: DiffSummary) -> PolicyResult:
    flagged = [changed.path for changed in summary.changed_files if PurePosixPath(changed.path).name in DEPENDENCY_FILES]
    if flagged:
        return PolicyResult(
            name="dependency_risk",
            status=PolicyStatus.WARN,
            reason="Dependency manifest or lockfile changed.",
            evidence=flagged[:10],
        )
    return PolicyResult(name="dependency_risk", status=PolicyStatus.PASS, reason="No dependency manifest or lockfile changes detected.")


def check_test_impact(summary: DiffSummary) -> PolicyResult:
    paths = [changed.path for changed in summary.changed_files]
    source_changed = any(_is_source_path(path) for path in paths)
    test_changed = any(_is_test_path(path) for path in paths)
    if source_changed and not test_changed:
        return PolicyResult(
            name="test_impact",
            status=PolicyStatus.WARN,
            reason="Source files changed without matching test-file changes.",
            evidence=[path for path in paths if _is_source_path(path)][:10],
        )
    return PolicyResult(name="test_impact", status=PolicyStatus.PASS, reason="Test impact policy satisfied.")


def decide(policy_results: list[PolicyResult]) -> Decision:
    if any(result.status == PolicyStatus.FAIL for result in policy_results):
        return Decision.FAIL
    if any(result.status == PolicyStatus.WARN for result in policy_results):
        return Decision.WARN
    return Decision.PASS


def map_check_conclusion(decision: Decision, mode: ReviewMode) -> CheckConclusion:
    if mode == ReviewMode.OBSERVE:
        if decision == Decision.PASS:
            return CheckConclusion.SUCCESS
        return CheckConclusion.NEUTRAL
    if mode == ReviewMode.WARN:
        if decision == Decision.PASS:
            return CheckConclusion.SUCCESS
        if decision == Decision.WARN:
            return CheckConclusion.NEUTRAL
        return CheckConclusion.FAILURE
    if decision == Decision.PASS:
        return CheckConclusion.SUCCESS
    if decision == Decision.WARN:
        return CheckConclusion.ACTION_REQUIRED
    return CheckConclusion.FAILURE


def _is_dangerous_path(path: str) -> bool:
    lowered = path.lower()
    return any(part in lowered for part in DANGEROUS_PATH_PARTS)


def _is_source_path(path: str) -> bool:
    pure = PurePosixPath(path)
    return pure.suffix in SOURCE_EXTENSIONS and not _is_test_path(path)


def _is_test_path(path: str) -> bool:
    lowered_parts = [part.lower() for part in PurePosixPath(path).parts]
    lowered_name = PurePosixPath(path).name.lower()
    return any(hint in lowered_parts for hint in TEST_HINTS) or "test" in lowered_name or "spec" in lowered_name


def _redact_line(line: str) -> str:
    trimmed = line.strip()
    if len(trimmed) <= 24:
        return "[redacted secret-like line]"
    return f"{trimmed[:12]}...[redacted]...{trimmed[-6:]}"
