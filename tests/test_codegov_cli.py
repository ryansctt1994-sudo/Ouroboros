from heavyforge.codegov.cli import main


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


def test_codegov_cli_writes_receipt_and_comment_for_warn(tmp_path):
    diff_path = tmp_path / "sample.diff"
    receipt_path = tmp_path / "receipt.json"
    comment_path = tmp_path / "receipt.md"
    diff_path.write_text(WARN_DIFF, encoding="utf-8")

    code = main([
        "--diff",
        str(diff_path),
        "--out",
        str(receipt_path),
        "--comment",
        str(comment_path),
        "--project",
        "demo",
        "--commit-sha",
        "abc123",
        "--pr-number",
        "5",
    ])

    assert code == 1
    assert receipt_path.exists()
    assert comment_path.exists()
    assert "Kaskal Verified Receipt" in comment_path.read_text(encoding="utf-8")
    assert '"decision": "WARN"' in receipt_path.read_text(encoding="utf-8")


def test_codegov_cli_returns_zero_for_pass(tmp_path):
    diff_path = tmp_path / "pass.diff"
    diff_path.write_text(PASS_DIFF, encoding="utf-8")

    assert main(["--diff", str(diff_path)]) == 0


def test_codegov_cli_returns_two_for_fail(tmp_path):
    diff_path = tmp_path / "fail.diff"
    config_path = tmp_path / ".kaskal.yml"
    diff_path.write_text(FAIL_DIFF, encoding="utf-8")
    config_path.write_text("mode: enforce\n", encoding="utf-8")

    assert main(["--diff", str(diff_path), "--config", str(config_path)]) == 2


def test_codegov_cli_returns_three_for_missing_diff():
    assert main(["--diff", "/definitely/missing.diff"]) == 3
