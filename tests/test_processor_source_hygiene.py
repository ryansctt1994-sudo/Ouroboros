import re
from pathlib import Path


CONFLICT_LINE_PATTERNS = (
    re.compile(r"^<<<<<<< .+$", re.MULTILINE),
    re.compile(r"^=======$", re.MULTILINE),
    re.compile(r"^>>>>>>> .+$", re.MULTILINE),
)


def test_ouroboros_processor_has_no_merge_conflict_markers() -> None:
    source = Path('ouroboros_processor.py').read_text(encoding='utf-8')
    matches = [pattern.pattern for pattern in CONFLICT_LINE_PATTERNS if pattern.search(source)]
    assert not matches, f'Merge conflict markers found in ouroboros_processor.py: {matches}'


def test_ouroboros_processor_core_geometry_block_is_singleton() -> None:
    source = Path('ouroboros_processor.py').read_text(encoding='utf-8')
    assert source.count('TAU = 2.0 * math.pi') == 1
    assert source.count('class TorusParams') == 1
    assert source.count('def _py_scalar(') == 1
