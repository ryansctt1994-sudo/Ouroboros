from heavyforge.codegov.config import KaskalConfig, ThresholdConfig
from heavyforge.codegov.diff_parser import parse_unified_diff
from heavyforge.codegov.models import Decision, PolicyStatus, ReviewMode
from heavyforge.codegov.policy import decide, map_check_conclusion, run_policies


def diff_for(path: str, added: str = "value = 1") -> str:
    return f"""diff --git a/{path} b/{path}
--- a/{path}
+++ b/{path}
@@ -0,0 +1 @@
+{added}
"""


def result_by_name(results, name):
    return next(result for result in results if result.name == name)


def test_secret_like_addition_fails():
    summary = parse_unified_diff(diff_for("src/app.py", "API_KEY='abcdefghijklmnopqrstuvwxyz'"))
    results = run_policies(summary, KaskalConfig())

    assert result_by_name(results, "secrets_exposure").status == PolicyStatus.FAIL
    assert decide(results) == Decision.FAIL


def test_dependency_file_warns():
    summary = parse_unified_diff(diff_for("package.json", '{"dependencies": {"x": "1.0.0"}}'))
    results = run_policies(summary, KaskalConfig())

    assert result_by_name(results, "dependency_risk").status == PolicyStatus.WARN
    assert decide(results) == Decision.WARN


def test_source_without_tests_warns():
    summary = parse_unified_diff(diff_for("src/app.py", "value = 1"))
    results = run_policies(summary, KaskalConfig())

    assert result_by_name(results, "test_impact").status == PolicyStatus.WARN


def test_large_diff_thresholds_fail_when_exceeded():
    diff = "diff --git a/src/app.py b/src/app.py\n--- a/src/app.py\n+++ b/src/app.py\n@@ -0,0 +1,3 @@\n" + "\n".join(
        f"+line_{idx}" for idx in range(4)
    )
    config = KaskalConfig(thresholds=ThresholdConfig(full_review_max_changed_lines=1, warn_max_changed_lines=3))
    results = run_policies(parse_unified_diff(diff), config)

    assert result_by_name(results, "large_diff_risk").status == PolicyStatus.FAIL


def test_check_conclusion_mapping_observe_does_not_block_failures():
    assert map_check_conclusion(Decision.FAIL, ReviewMode.OBSERVE).value == "neutral"
    assert map_check_conclusion(Decision.FAIL, ReviewMode.ENFORCE).value == "failure"
