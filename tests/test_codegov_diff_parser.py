from heavyforge.codegov.diff_parser import parse_unified_diff


SAMPLE_DIFF = """diff --git a/src/app.py b/src/app.py
index 111..222 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1,2 +1,3 @@
-old = 1
+new = 2
+print(new)
 unchanged
"""


def test_parse_unified_diff_counts_files_and_lines():
    summary = parse_unified_diff(SAMPLE_DIFF)

    assert [changed.path for changed in summary.changed_files] == ["src/app.py"]
    assert summary.additions == 2
    assert summary.deletions == 1
    assert summary.changed_lines == 3
    assert "new = 2" in summary.added_lines
