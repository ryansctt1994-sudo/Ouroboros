from pathlib import Path


def test_ouroboros_processor_has_no_merge_conflict_markers() -> None:
    source = Path("ouroboros_processor.py").read_text(encoding="utf-8")
    assert "<<<<<<<" not in source
    assert "=======" not in source
    assert ">>>>>>>" not in source


def test_ouroboros_processor_core_geometry_block_is_singleton() -> None:
    source = Path("ouroboros_processor.py").read_text(encoding="utf-8")
    assert source.count("TAU = 2.0 * math.pi") == 1
    assert source.count("class TorusParams") == 1
    assert source.count("def _py_scalar(") == 1
