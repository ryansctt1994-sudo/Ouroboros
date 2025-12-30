Visualization utilities for the project

This directory contains tools to generate torus meshes and simple visualizations.

Continuous Integration
----------------------
A GitHub Actions workflow (/.github/workflows/visualize.yml) runs on demand or when visualization files change. The workflow will:
- install project requirements (or fallback dependencies)
- run linters (ruff and black)
- set MPLBACKEND=Agg for headless plotting
- run visualization/torus_geodesics.py to produce artifacts
- upload the contents of visualization/output/ as workflow artifacts

Artifacts
---------
After the workflow runs, generated artifacts can be downloaded from the workflow run page under "Artifacts" (the artifact is named "visualization-artifacts"). The artifacts include:
- torus.obj (if exported)
- torus.stl (if exported)
- torus.png (if saved)

Usage
-----
Run the script locally to generate files:

python visualization/torus_geodesics.py --export-obj --export-stl --save-png

Options:
- --output-dir / -o : target directory (default: visualization/output)
- --export-obj : save OBJ
- --export-stl : save STL
- --save-png : save PNG render
- --nu, --nv : mesh resolution parameters

Notes
-----
The visualization/output/ directory is ignored by git (see .gitignore) to avoid committing generated binaries.
