from __future__ import annotations

from .models import ChangedFile, DiffSummary


def parse_unified_diff(diff_text: str) -> DiffSummary:
    """Parse enough unified diff structure for deterministic governance checks.

    This parser intentionally avoids applying patches. It extracts changed file
    paths, additions, deletions, total changed lines, and added-line payloads.
    """

    files: dict[str, ChangedFile] = {}
    current_path: str | None = None
    added_lines: list[str] = []
    additions = 0
    deletions = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                current_path = _normalize_git_path(parts[3])
                files.setdefault(current_path, ChangedFile(path=current_path))
            continue

        if line.startswith("+++ "):
            candidate = line[4:].strip()
            if candidate != "/dev/null":
                current_path = _normalize_git_path(candidate)
                files.setdefault(current_path, ChangedFile(path=current_path))
            continue

        if current_path is None:
            continue

        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            payload = line[1:]
            additions += 1
            files[current_path].additions += 1
            added_lines.append(payload)
        elif line.startswith("-"):
            deletions += 1
            files[current_path].deletions += 1

    return DiffSummary(
        changed_files=list(files.values()),
        additions=additions,
        deletions=deletions,
        changed_lines=additions + deletions,
        added_lines=added_lines,
    )


def _normalize_git_path(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path
