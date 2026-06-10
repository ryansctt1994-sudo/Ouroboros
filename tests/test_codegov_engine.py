from heavyforge.codegov.config import KaskalConfig
from heavyforge.codegov.engine import analyze_diff, compute_code_receipt_hash
from heavyforge.codegov.models import Decision, ReviewMode


PASS_DIFF = """diff --git a/tests/test_app.py b/tests/test_app.py
--- a/tests/test_app.py
+++ b/tests/test_app.py
@@ -0,0 +1 @@
+def test_app(): assert True
"""


WARN_DIFF = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -0,0 +1 @@
+value = 1
"""


FAIL_DIFF = """diff --git a/.env b/.env
--- a/.env
+++ b/.env
@@ -0,0 +1 @@
+TOKEN=abcdefghijklmnopqrstuvwxyz
"""


def test_analyze_diff_returns_receipt_with_stable_hash():
    receipt = analyze_diff(PASS_DIFF, project="demo", commit_sha="abc123", pr_number=1)

    assert receipt.project == "demo"
    assert receipt.commit_sha == "abc123"
    assert receipt.pr_number == 1
    assert receipt.receipt_hash == compute_code_receipt_hash(receipt)
    assert receipt.changed_lines == 1


def test_analyze_diff_warns_on_source_without_tests():
    receipt = analyze_diff(WARN_DIFF)

    assert receipt.decision == Decision.WARN
    assert receipt.check_conclusion.value == "neutral"


def test_enforce_mode_maps_fail_to_blocking_check():
    receipt = analyze_diff(FAIL_DIFF, config=KaskalConfig(mode=ReviewMode.ENFORCE))

    assert receipt.decision == Decision.FAIL
    assert receipt.check_conclusion.value == "failure"
