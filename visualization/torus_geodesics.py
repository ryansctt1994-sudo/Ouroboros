#!/usr/bin/env python3
"""Generate a torus mesh and optional visualizations/exports.

This script creates a triangular mesh approximating a torus, optionally
exports it as OBJ and/or STL, and can save a PNG rendering to
visualization/output/.

Dependencies:
- numpy
- matplotlib
- trimesh

The CI workflow sets MPLBACKEND=Agg so this script can run headless.
"""

from __future__ import annotations
import argparse
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import trimesh


def make_torus(R: float = 1.0, r: float = 0.3, nu: int = 120, nv: int = 60):
    """Create vertices and triangular faces for a torus.

    Parameters:
        R: Major radius.
        r: Minor radius.
        nu: Number of samples around the major circumference.
        nv: Number of samples around the minor circumference.

    Returns:
        vertices: (N,3) float array
        faces: (M,3) int array
        grid coords x,y,z (for plotting)
    """
    u = np.linspace(0.0, 2.0 * np.pi, nu, endpoint=False)
    v = np.linspace(0.0, 2.0 * np.pi, nv, endpoint=False)
    uu, vv = np.meshgrid(u, v, indexing="ij")

    x = (R + r * np.cos(vv)) * np.cos(uu)
    y = (R + r * np.cos(vv)) * np.sin(uu)
    z = r * np.sin(vv)

    vertices = np.column_stack((x.ravel(), y.ravel(), z.ravel()))

    faces = []
    for i in range(nu):
        for j in range(nv):
            i2 = (i + 1) % nu
            j2 = (j + 1) % nv
            v00 = i * nv + j
            v10 = i2 * nv + j
            v01 = i * nv + j2
            v11 = i2 * nv + j2
            faces.append([v00, v10, v11])
            faces.append([v00, v11, v01])

    faces = np.asarray(faces, dtype=np.int64)
    return vertices, faces, x, y, z


def save_mesh(vertices: np.ndarray, faces: np.ndarray, out_path: Path):
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    # trimesh will infer file type from extension
    mesh.export(str(out_path))


def save_png(x, y, z, out_path: Path, dpi: int = 200):
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")
    # Use a surface plot with modest alpha so mesh structure is visible
    ax.plot_surface(x, y, z, rstride=2, cstride=2, cmap="viridis", linewidth=0, antialiased=True, alpha=0.9)
    ax.set_axis_off()
    # Equal aspect ratio
    try:
        max_range = np.array([x.max() - x.min(), y.max() - y.min(), z.max() - z.min()]).max() / 2.0
        mid_x = (x.max() + x.min()) * 0.5
        mid_y = (y.max() + y.min()) * 0.5
        mid_z = (z.max() + z.min()) * 0.5
        ax.set_xlim(mid_x - max_range, mid_x + max_range)
        ax.set_ylim(mid_y - max_range, mid_y + max_range)
        ax.set_zlim(mid_z - max_range, mid_z + max_range)
    except Exception:
        pass
    fig.tight_layout()
    fig.savefig(str(out_path), dpi=dpi)
    plt.close(fig)


def parse_args():
    p = argparse.ArgumentParser(description="Create a torus mesh and optional exports")
    p.add_argument("--output-dir", "-o", default="visualization/output", help="Directory to place exports and images")
    p.add_argument("--export-obj", action="store_true", help="Export mesh as OBJ (outdir/torus.obj)")
    p.add_argument("--export-stl", action="store_true", help="Export mesh as STL (outdir/torus.stl)")
    p.add_argument("--save-png", action="store_true", help="Save a PNG render (outdir/torus.png)")
    p.add_argument("--nu", type=int, default=180, help="Samples around major circumference")
    p.add_argument("--nv", type=int, default=90, help="Samples around minor circumference")
    p.add_argument("--R", type=float, default=1.0, help="Major radius")
    p.add_argument("--r", type=float, default=0.35, help="Minor radius")
    return p.parse_args()


def main():
    args = parse_args()
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"Generating torus mesh (R={args.R}, r={args.r}, nu={args.nu}, nv={args.nv})")
    vertices, faces, x, y, z = make_torus(R=args.R, r=args.r, nu=args.nu, nv=args.nv)

    if args.export_obj:
        obj_path = outdir / "torus.obj"
        print(f"Exporting OBJ to {obj_path}")
        save_mesh(vertices, faces, obj_path)

    if args.export_stl:
        stl_path = outdir / "torus.stl"
        print(f"Exporting STL to {stl_path}")
        save_mesh(vertices, faces, stl_path)

    if args.save_png:
        png_path = outdir / "torus.png"
        print(f"Saving PNG render to {png_path}")
        save_png(x, y, z, png_path)

    if not (args.export_obj or args.export_stl or args.save_png):
        print("No outputs requested. Use --export-obj, --export-stl and/or --save-png to produce files.")


if __name__ == "__main__":
    main()
