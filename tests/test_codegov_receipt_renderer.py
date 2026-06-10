from heavyforge.codegov.engine import analyze_diff
from heavyforge.codegov.receipt_renderer import render_markdown_receipt


SAMPLE_DIFF = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -0,0 +1 @@
+value = 1
"""


def test_render_markdown_receipt_is_concise_and_contains_core_fields():
    receipt = analyze_diff(SAMPLE_DIFF, project="demo", commit_sha="abc123", pr_number=7)
    markdown = render_markdown_receipt(receipt)

    assert "## Kaskal Verified Receipt" in markdown
    assert "Decision:" in markdown
    assert "Receipt Hash:" in markdown
    assert "Policy Results" in markdown
    assert "cathedral" not in markdown.lower()
    assert "myth" not in markdown.lower()
