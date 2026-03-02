"""
dsl_primitives.py – ARC-AGI-2 DSL primitive library.

All operations accept and return 2-D integer arrays.  When CuPy is
available the arrays may live on GPU; all internal operations use the
*array namespace* (``xp``) so they work transparently with both
NumPy and CuPy.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Backend selection: prefer CuPy when available, fall back to NumPy.
# ---------------------------------------------------------------------------
try:
    import cupy as xp  # type: ignore[import]

    _BACKEND = "cupy"
except ImportError:
    import numpy as xp  # type: ignore[assignment]

    _BACKEND = "numpy"

import numpy as _np  # always available for type-annotation helpers

Grid = Any  # xp.ndarray (2-D, dtype int)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _as_grid(arr: Any) -> Grid:
    """Coerce *arr* to a 2-D integer array on the active backend."""
    return xp.asarray(arr, dtype=xp.int32)


def _to_numpy(arr: Any) -> _np.ndarray:
    """Return a NumPy copy regardless of backend."""
    if _BACKEND == "cupy":
        return xp.asnumpy(arr)
    return _np.asarray(arr)


# ---------------------------------------------------------------------------
# Primitive: identity
# ---------------------------------------------------------------------------

def identity(grid: Grid) -> Grid:
    """Return a copy of *grid* unchanged (useful as a no-op program)."""
    return _as_grid(grid).copy()


# ---------------------------------------------------------------------------
# Primitive: rotate_grid
# ---------------------------------------------------------------------------

def rotate_grid(grid: Grid, k: int = 1) -> Grid:
    """Rotate *grid* by ``k * 90`` degrees counter-clockwise.

    Parameters
    ----------
    grid:
        2-D integer array.
    k:
        Number of 90-degree CCW rotations (0–3).
    """
    g = _as_grid(grid)
    k = int(k) % 4
    return xp.rot90(g, k=k)


# ---------------------------------------------------------------------------
# Primitive: flip_grid
# ---------------------------------------------------------------------------

def flip_grid(grid: Grid, axis: int = 0) -> Grid:
    """Flip *grid* along the given axis.

    Parameters
    ----------
    axis:
        0 = vertical flip (up/down), 1 = horizontal flip (left/right).
    """
    g = _as_grid(grid)
    return xp.flip(g, axis=axis)


# ---------------------------------------------------------------------------
# Primitive: apply_symmetry
# ---------------------------------------------------------------------------

def apply_symmetry(grid: Grid, kind: str = "horizontal") -> Grid:
    """Apply a reflective symmetry to *grid*.

    Parameters
    ----------
    kind:
        ``"horizontal"``  – mirror left half onto right half.
        ``"vertical"``    – mirror top half onto bottom half.
        ``"diagonal"``    – transpose (main diagonal reflection).
        ``"antidiagonal"``– anti-diagonal reflection.
    """
    g = _as_grid(grid)
    if kind == "horizontal":
        half = g[:, : g.shape[1] // 2]
        return xp.concatenate([half, xp.flip(half, axis=1)], axis=1)[
            :, : g.shape[1]
        ]
    if kind == "vertical":
        half = g[: g.shape[0] // 2, :]
        return xp.concatenate([half, xp.flip(half, axis=0)], axis=0)[
            : g.shape[0], :
        ]
    if kind == "diagonal":
        return xp.swapaxes(g, 0, 1)
    if kind == "antidiagonal":
        return xp.flip(xp.swapaxes(g, 0, 1), axis=(0, 1))
    raise ValueError(f"Unknown symmetry kind: {kind!r}")


# ---------------------------------------------------------------------------
# Primitive: recolor
# ---------------------------------------------------------------------------

def recolor(grid: Grid, color_map: Dict[int, int]) -> Grid:
    """Replace pixel values according to *color_map*.

    Parameters
    ----------
    color_map:
        Mapping ``{old_color: new_color, ...}``.  Colors absent from the
        map are left unchanged.
    """
    g = _as_grid(grid).copy()
    for src, dst in color_map.items():
        g = xp.where(g == int(src), int(dst), g)
    return g


# ---------------------------------------------------------------------------
# Primitive: fill_region
# ---------------------------------------------------------------------------

def fill_region(
    grid: Grid,
    row: int,
    col: int,
    fill_color: int,
    target_color: Optional[int] = None,
) -> Grid:
    """Flood-fill starting at *(row, col)* with *fill_color*.

    Parameters
    ----------
    target_color:
        Color to replace.  Defaults to the color at *(row, col)*.
    """
    g = _to_numpy(_as_grid(grid)).copy()
    h, w = g.shape
    if row < 0 or row >= h or col < 0 or col >= w:
        return _as_grid(g)
    if target_color is None:
        target_color = int(g[row, col])
    if target_color == fill_color:
        return _as_grid(g)
    stack: List[Tuple[int, int]] = [(row, col)]
    while stack:
        r, c = stack.pop()
        if r < 0 or r >= h or c < 0 or c >= w:
            continue
        if g[r, c] != target_color:
            continue
        g[r, c] = fill_color
        stack.extend([(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)])
    return _as_grid(g)


# ---------------------------------------------------------------------------
# Primitive: extract_objects
# ---------------------------------------------------------------------------

def extract_objects(
    grid: Grid,
    background: int = 0,
) -> List[Dict[str, Any]]:
    """Extract connected non-background objects from *grid*.

    Returns a list of object descriptors, each containing:

    ``"color"``
        Dominant colour of the object (most-frequent non-background pixel).
    ``"bbox"``
        ``(row_min, col_min, row_max, col_max)`` bounding box.
    ``"mask"``
        Boolean NumPy array (same shape as *grid*) marking the object cells.
    ``"pixels"``
        List of ``(row, col)`` tuples belonging to the object.
    """
    g = _to_numpy(_as_grid(grid))
    h, w = g.shape
    visited = _np.zeros((h, w), dtype=bool)
    objects: List[Dict[str, Any]] = []

    for start_r in range(h):
        for start_c in range(w):
            if visited[start_r, start_c]:
                continue
            cell_val = int(g[start_r, start_c])
            if cell_val == background:
                visited[start_r, start_c] = True
                continue
            # DFS to find connected component
            pixels: List[Tuple[int, int]] = []
            stack: List[Tuple[int, int]] = [(start_r, start_c)]
            while stack:
                r, c = stack.pop()
                if r < 0 or r >= h or c < 0 or c >= w:
                    continue
                if visited[r, c]:
                    continue
                if g[r, c] == background:
                    continue
                visited[r, c] = True
                pixels.append((r, c))
                stack.extend(
                    [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
                )
            if not pixels:
                continue
            rows = [p[0] for p in pixels]
            cols = [p[1] for p in pixels]
            mask = _np.zeros((h, w), dtype=bool)
            for pr, pc in pixels:
                mask[pr, pc] = True
            # dominant colour (most-frequent value in object cells)
            vals = g[mask]
            counts: Dict[int, int] = {}
            for v in vals:
                counts[int(v)] = counts.get(int(v), 0) + 1
            dominant = max(counts, key=lambda k: counts[k])
            objects.append(
                {
                    "color": dominant,
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                    "mask": mask,
                    "pixels": pixels,
                }
            )
    return objects
