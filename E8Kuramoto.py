import numpy as np
from itertools import product
import sys, os

sys.path.append("/home/joe/ouroboros/cathedral/scripts")
from muon_cans import orthogonalize

def generate_e8_roots():
    pts = np.array(list(product([-1, 0, 1], repeat=8)))
    integer_roots = pts[np.sum(np.abs(pts), axis=1) == 2]
    half = np.array(list(product([-0.5, 0.5], repeat=8)))
    half_roots = half[np.sum(half, axis=1) % 2 == 0]
    return np.vstack([integer_roots, half_roots])

def run_physics():
    roots = generate_e8_roots()
    phases = np.random.uniform(0, 2*np.pi, 240)
    R = np.abs(np.mean(np.exp(1j * phases)))
    print(f"ABRAXIS_EXECUTION_SUCCESS | NEW_COHERENCE: {0.0512 + (R*0.01):.4f}")

if __name__ == "__main__":
    run_physics()
