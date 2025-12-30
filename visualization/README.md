# Visualization

This folder contains the enhanced torus visualization script (torus_geodesics.py) that renders the Ouroboros toroidal manifold, geodesics, and curvature.

Usage
1. Install dependencies: pip install -r requirements.txt
2. Run the script: python visualization/torus_geodesics.py
3. To save high-resolution PNGs, uncomment the plt.savefig line near the bottom of the script.

Generating OBJ/STL
- The script does not include mesh export by default. To export, extend the script to sample the (theta,phi) grid and write to an OBJ file using a small writer function or use trimesh/meshio.

License
See repository LICENSE (CC BY 4.0).

---
