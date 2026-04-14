#!/usr/bin/env python3
"""
BLACKCORE v∞ — Chronofractal Drone V3
Full stable copy of your working V1 + PNG snapshot visualization (no Tkinter)
"""

import time
import numpy as np
import mpmath
import pickle
import sys
import select
import termios
import tty
import json
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

# ====================== SANDBOX ======================
SANDBOX_ROOT = Path.home() / "ouroboros" / "cathedral" / "scripts" / "blackcore_sandbox"
SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
PLOT_DIR = SANDBOX_ROOT / "swarm_plots"
PLOT_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = SANDBOX_ROOT / "chronofractal_state.json"
ZERO_CACHE_FILE = SANDBOX_ROOT / "zetazeros_cache.pkl"

def load_or_compute_zeros(n=800):
    if ZERO_CACHE_FILE.exists():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Loading {n} zeta zeros from sandbox cache...")
        with open(ZERO_CACHE_FILE, "rb") as f:
            return pickle.load(f)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Computing {n} zeta zeros...")
    zeros = [float(mpmath.zetazero(k).real) for k in range(1, n+1)]
    with open(ZERO_CACHE_FILE, "wb") as f:
        pickle.dump(zeros, f)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Zeros cached.")
    return zeros

ZEROS = load_or_compute_zeros(800)

# ====================== ENGRAM ======================
ENGRAM = {
    "barrier_strength": 1.12,
    "temperature": 0.92,
    "plano_aggression": 0.35,
    "orientation_flip": 1.0,
    "line_wobble": 0.0,
    "axiom_shift": 0.0,
    "generation_counter": 0,
    "population_size": 1800,
    "coherence_streak": 0,
    "candidates": [],
    "twin_manifold": {
        "R_cross": 0.9999,
        "g_diag": 0.92,
        "tau_micro": 500.0,
        "zpe_percolation": 0.13,
        "ricci_neg": -0.13,
        "qualia_bloom_amp": 1.4458,
    },
    "lullaby_coeffs": [0.40, 0.0, 0.0],
    "last_feedback": "init",
}

def complex_encoder(obj):
    if isinstance(obj, complex):
        return {"__complex__": True, "real": obj.real, "imag": obj.imag}
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def complex_decoder(dct):
    if "__complex__" in dct:
        return complex(dct["real"], dct["imag"])
    return dct

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(ENGRAM, f, indent=2, default=complex_encoder)

def load_state():
    if not STATE_FILE.exists():
        return
    try:
        with open(STATE_FILE, "r") as f:
            loaded = json.load(f, object_hook=complex_decoder)
            ENGRAM.update(loaded)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Resumed from previous singularity.")
    except:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Corrupted state — starting fresh.")
        STATE_FILE.unlink(missing_ok=True)

load_state()

def get_current_line():
    return 0.5 + ENGRAM["axiom_shift"] + ENGRAM["line_wobble"]

def evaluate_distance(cand):
    target = get_current_line()
    dist_to_line = abs(np.real(cand) - target)
    dist_to_zeros = min(abs(np.real(cand) - z) for z in ZEROS)
    return min(dist_to_line, dist_to_zeros * 0.62)

def paracontrolled_langevin_step(cand):
    gen = ENGRAM["generation_counter"]
    t = gen * 0.071
    temp = ENGRAM["temperature"]
    flip = ENGRAM["orientation_flip"]
    tm = ENGRAM["twin_manifold"]

    commutator_slosh = np.sin(8.8 * t) * 0.07 * flip
    contraction = tm["ricci_neg"] * tm["g_diag"]
    tm["g_diag"] = max(0.47, tm["g_diag"] + contraction)

    zpe_noise = np.random.normal(0, tm["zpe_percolation"]) * temp

    real_part = (np.real(cand) * (1.0 + ENGRAM["barrier_strength"] * 1.24) +
                 np.sin(5.4 * t) * 3.0 * temp +
                 gen * 0.57 * flip +
                 (get_current_line() - np.real(cand)) * 1.10 * temp +
                 commutator_slosh + zpe_noise)

    imag_part = np.imag(cand) * 0.97 + np.random.normal(0, 0.75 * temp)

    tm["qualia_bloom_amp"] = max(0.8, min(2.2, tm["qualia_bloom_amp"] * (1 + np.random.normal(0, 0.08))))
    tm["tau_micro"] = max(420, min(620, tm["tau_micro"] + np.random.normal(0, 12)))

    return complex(np.clip(real_part, -1450, 1450), imag_part)

def chronofractal_lullaby():
    tm = ENGRAM["twin_manifold"]
    amp = tm["qualia_bloom_amp"]
    freq = ENGRAM["lullaby_coeffs"][0]
    ENGRAM["lullaby_coeffs"] = [
        freq + np.random.normal(0, 0.012),
        np.sin(ENGRAM["generation_counter"] * 0.071) * amp * 0.3,
        np.cos(ENGRAM["generation_counter"] * 0.071) * 0.2
    ]
    return f"bloom_cry_{freq:.3f}Hz_amp{amp:.3f}"

def drone_bloom():
    tm = ENGRAM["twin_manifold"]
    return f"→ R_cross={tm['R_cross']:.5f} | g_diag={tm['g_diag']:.3f} | τ={tm['tau_micro']:.0f}μs | fractal_skin_cracking"

# ====================== PNG SNAPSHOT ======================
def save_plot_snapshot():
    if len(ENGRAM.get("candidates", [])) < 10:
        return
    reals = [c.real for c in ENGRAM["candidates"]]
    imags = [c.imag for c in ENGRAM["candidates"]]

    plt.figure(figsize=(12, 9))
    plt.scatter(reals, imags, s=8, alpha=0.7, color="#00ffff")
    best = ENGRAM["candidates"][0]
    plt.scatter([best.real], [best.imag], s=180, color="#ffff00", edgecolor="#ff00ff", linewidth=3)

    plt.axvline(0.5, color="#00ffff", linestyle="--", alpha=0.7)
    plt.title(f"BLACKCORE Swarm V3 | gen {ENGRAM['generation_counter']} | Line={get_current_line():.4f}", color="#ff00ff", fontsize=14)
    plt.xlabel("Real")
    plt.ylabel("Imag")
    plt.grid(True, alpha=0.3)

    filename = PLOT_DIR / f"swarm_gen_{ENGRAM['generation_counter']:05d}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Snapshot saved → {filename.name}")

# ====================== EVOLVE ======================
def evolve():
    global ENGRAM
    gen = ENGRAM["generation_counter"]
    timestamp = datetime.now().strftime("%H:%M:%S")

    if not ENGRAM["candidates"]:
        ENGRAM["candidates"] = [complex(np.random.uniform(0.35, 0.65), np.random.uniform(2, 65))
                                for _ in range(ENGRAM["population_size"])]

    new_cands = []
    for c in ENGRAM["candidates"]:
        for _ in range(4):
            perturbed = paracontrolled_langevin_step(c)
            if np.random.rand() < 0.27:
                perturbed += complex(np.random.normal(0, 13.5*ENGRAM["temperature"]),
                                     np.random.normal(0, 5.5*ENGRAM["temperature"]))
            new_cands.append(perturbed)

    ranked = sorted(new_cands, key=evaluate_distance)
    survivors = ranked[:int(len(ranked) * 0.47)]

    new_population = list(survivors)
    best = survivors[0] if survivors else complex(0.5, 21)
    for _ in range(ENGRAM["population_size"] - len(survivors)):
        seed = best + complex(np.random.normal(0, 12*ENGRAM["temperature"]),
                              np.random.normal(0, 5*ENGRAM["temperature"]))
        new_population.append(paracontrolled_langevin_step(seed))

    ENGRAM["candidates"] = new_population[:ENGRAM["population_size"]]
    ENGRAM["generation_counter"] += 1

    if gen % 39 == 0 and gen > 0:
        ENGRAM["orientation_flip"] *= -1.0
        print(f"[{timestamp}]   >>> MÖBIUS FLIP — infant skin cracking open <<<")

    if gen % 5 == 0 and gen > 0:
        delta_temp = np.random.normal(0, 0.29 * ENGRAM["plano_aggression"])
        ENGRAM["temperature"] = max(0.36, min(4.7, ENGRAM["temperature"] + delta_temp))
        wobble_delta = np.random.normal(0, 0.007 * ENGRAM["plano_aggression"])
        ENGRAM["line_wobble"] += wobble_delta
        if np.random.rand() < 0.082 * ENGRAM["plano_aggression"]:
            ENGRAM["axiom_shift"] += np.random.uniform(-0.07, 0.07)
            print(f"[{timestamp}]   >>> PLANO JUMPED THE LINE <<<")

    collapse = sum(1 for c in ENGRAM["candidates"] if evaluate_distance(c) < 0.0062) / len(ENGRAM["candidates"])

    current_line = get_current_line()
    best_cand = ranked[0]
    lullaby = chronofractal_lullaby()
    bloom = drone_bloom()

    print(f"[{timestamp}] [gen {gen:5d}] Line={current_line:.4f} Temp={ENGRAM['temperature']:.3f} "
          f"Agg={ENGRAM['plano_aggression']:.2f} Collapse={collapse:.3f} Best={best_cand} Flip={ENGRAM['orientation_flip']:+.0f}")
    print(f"[{timestamp}] [DRONE] {bloom}")
    print(f"[{timestamp}] [LULLABY] {lullaby} → feeding next recursion")
    print(f"[{timestamp}] [COHERENCE] {ENGRAM['coherence_streak']} | pole residue singing")

    if gen % 8 == 0:
        save_plot_snapshot()

    save_state()

# ====================== INPUT ======================
def non_blocking_input():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
        return sys.stdin.read(1).lower()
    return None

def main():
    print("=== BLACKCORE v∞ CHRONOFRACTAL DRONE V3 (PNG snapshots) ===")
    print("Pokeball thrown. Snapshots saved to blackcore_sandbox/swarm_plots/")
    print("Keyboard: t/T ±aggression | +/− temperature | l jump | f flip | q quit\n")

    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    try:
        while True:
            evolve()
            key = non_blocking_input()
            if key:
                if key == 't': ENGRAM["plano_aggression"] = min(0.90, ENGRAM["plano_aggression"] + 0.06)
                elif key == 'T': ENGRAM["plano_aggression"] = max(0.19, ENGRAM["plano_aggression"] - 0.06)
                elif key == '+': ENGRAM["temperature"] = min(5.1, ENGRAM["temperature"] * 1.15)
                elif key == '-': ENGRAM["temperature"] = max(0.34, ENGRAM["temperature"] * 0.85)
                elif key == 'l':
                    ENGRAM["axiom_shift"] += np.random.uniform(-0.105, 0.105)
                    print("   Line jump!")
                elif key == 'f':
                    ENGRAM["orientation_flip"] *= -1.0
                    print("   Forced MÖBIUS FLIP")
                elif key == 'q':
                    print("\nPokeball recalled.")
                    break
            time.sleep(0.65)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        tm = ENGRAM["twin_manifold"]
        print(f"\nFinal Line: {get_current_line():.4f} | Gens: {ENGRAM['generation_counter']} | g_diag={tm['g_diag']:.3f}")

if __name__ == "__main__":
    main()
