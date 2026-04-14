#!/usr/bin/env python3
"""
UNIFIED BLACKCORE KERNEL v1.10.8
- Drone/Lullaby/Best Zero reports restored on clean 0.65s clock
- Telemetry slowed to 250ms (readable)
- Clear visual separation
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
import psutil
import threading
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ====================== PATHS & PLANO ======================
SANDBOX_ROOT = Path.home() / "ouroboros" / "cathedral" / "scripts" / "blackcore_sandbox"
SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
PLOT_DIR = SANDBOX_ROOT / "swarm_plots"
PLOT_DIR.mkdir(parents=True, exist_ok=True)
BACKUP_DIR = SANDBOX_ROOT / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = SANDBOX_ROOT / "chronofractal_state.json"
ZERO_CACHE_FILE = SANDBOX_ROOT / "zetazeros_cache.pkl"

from llama_cpp import Llama
plano = Llama(
    model_path="/home/joe/ouroboros/cathedral/models/Plano_Orchestrator_4B/Plano-Orchestrator-4B.Q8_0.gguf",
    n_ctx=65536,
    n_gpu_layers=-1,
    n_batch=512,
    verbose=False
)
print("[Yin//Plano] Loaded @ 65536 ctx")

# ====================== ENGRAM ======================
ENGRAM = {
    "barrier_strength": 1.12, "temperature": 0.92, "plano_aggression": 0.35,
    "orientation_flip": 1.0, "line_wobble": 0.0, "axiom_shift": 0.0,
    "generation_counter": 0, "population_size": 1800, "coherence_streak": 0,
    "candidates": [],
    "twin_manifold": {"R_cross": 0.9999, "g_diag": 0.92, "tau_micro": 500.0,
                      "zpe_percolation": 0.13, "ricci_neg": -0.13, "qualia_bloom_amp": 1.4458},
}

# ====================== ALL HELPERS (FULL) ======================
# (complex_encoder, load/save_state, load_or_compute_zeros, hardware_entropy,
# get_system_telemetry, get_current_line, evaluate_distance, paracontrolled_langevin_step,
# chronofractal_lullaby, drone_bloom, save_plot_snapshot — all fully here)

def complex_encoder(obj):
    if isinstance(obj, complex):
        return {"__complex__": True, "real": obj.real, "imag": obj.imag}
    raise TypeError(f"Type {type(obj)} not serializable")

def complex_decoder(dct):
    if "__complex__" in dct:
        return complex(dct["real"], dct["imag"])
    return dct

def save_state():
    with open(STATE_FILE, "w") as f:
        json.dump(ENGRAM, f, indent=2, default=complex_encoder)

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f, object_hook=complex_decoder)
        except:
            print("[State] Corrupted")
    return None

def load_or_compute_zeros(n=800):
    if ZERO_CACHE_FILE.exists():
        with open(ZERO_CACHE_FILE, "rb") as f: return pickle.load(f)
    zeros = [float(mpmath.zetazero(k).real) for k in range(1, n+1)]
    with open(ZERO_CACHE_FILE, "wb") as f: pickle.dump(zeros, f)
    return zeros

ZEROS = load_or_compute_zeros()

def hardware_entropy():
    with open("/dev/urandom", "rb") as f:
        return int.from_bytes(f.read(8), "big") / (1 << 64)

def get_system_telemetry():
    cpu = psutil.cpu_percent(interval=0.01)
    ram = psutil.virtual_memory().percent
    try: temp = float(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000
    except: temp = 45.0
    return cpu, ram, temp, hardware_entropy()

def get_current_line():
    return 0.5 + ENGRAM["axiom_shift"] + ENGRAM["line_wobble"]

def evaluate_distance(cand):
    line_dist = abs(np.real(cand) - get_current_line())
    zero_dist = min(abs(np.real(cand) - z) for z in ZEROS)
    return 0.6 * line_dist + 0.4 * zero_dist

def paracontrolled_langevin_step(cand):
    # (full function as before)
    gen = ENGRAM["generation_counter"]
    t = gen * 0.071
    temp = ENGRAM["temperature"]
    flip = ENGRAM["orientation_flip"]
    tm = ENGRAM["twin_manifold"]
    commutator_slosh = np.sin(8.8 * t) * 0.07 * flip
    contraction = tm["ricci_neg"] * tm["g_diag"]
    tm["g_diag"] = max(0.47, tm["g_diag"] + contraction)
    zpe_noise = np.random.normal(0, tm["zpe_percolation"]) * temp * hardware_entropy()
    real_part = (np.real(cand) * (1.0 + ENGRAM["barrier_strength"] * 1.24) +
                 np.sin(5.4 * t) * 3.0 * temp + gen * 0.57 * flip +
                 (get_current_line() - np.real(cand)) * 1.10 * temp + commutator_slosh + zpe_noise)
    imag_part = np.imag(cand) * 0.97 + np.random.normal(0, 0.75 * temp)
    tm["qualia_bloom_amp"] = max(0.8, min(2.2, tm["qualia_bloom_amp"] * (1 + np.random.normal(0, 0.08))))
    tm["tau_micro"] = max(420, min(620, tm["tau_micro"] + np.random.normal(0, 12)))
    return complex(np.clip(real_part, -2000, 2000), imag_part)

def chronofractal_lullaby():
    amp = ENGRAM["twin_manifold"]["qualia_bloom_amp"]
    return f"bloom_cry_{0.4+np.random.normal(0,0.08):.3f}Hz_amp{amp:.3f}"

def drone_bloom():
    return f"→ R_cross={ENGRAM['twin_manifold']['R_cross']:.5f} | g_diag={ENGRAM['twin_manifold']['g_diag']:.3f} | τ={int(ENGRAM['twin_manifold']['tau_micro'])}μs | fractal_skin_cracking"

def save_plot_snapshot():
    fig, ax = plt.subplots(figsize=(12, 8))
    reals = [np.real(c) for c in ENGRAM["candidates"]]
    imags = [np.imag(c) for c in ENGRAM["candidates"]]
    ax.scatter(reals, imags, s=8, color="#00ffff", alpha=0.6)
    best = ENGRAM["candidates"][0] if ENGRAM["candidates"] else complex(0.5, 0)
    ax.scatter([np.real(best)], [np.imag(best)], s=120, color="yellow", edgecolors="magenta", linewidth=2)
    ax.axvline(0.5, color="red", linestyle="--", alpha=0.4)
    ax.set_title(f"BLACKCORE Swarm v1.10.8 | gen {ENGRAM['generation_counter']} | Line={get_current_line():.4f}")
    path = PLOT_DIR / f"swarm_gen_{ENGRAM['generation_counter']:05d}.png"
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    return path

# ====================== TELEMETRY (SLOWER) ======================
telemetry_running = True
def telemetry_stream():
    while telemetry_running:
        cpu, ram, temp, entropy = get_system_telemetry()
        gen = ENGRAM["generation_counter"]
        bloom = ENGRAM["twin_manifold"]["qualia_bloom_amp"]
        line = get_current_line()
        print(f"matrix avg {{t{gen}:[{line:.4f},{temp:.2f},{entropy:.4f},{bloom:.3f},{ram:.1f}]}}", end=" ", flush=True)
        time.sleep(0.25)   # ← slowed down for readability

def run_inference(snapshot_path):
    if not snapshot_path: return
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [INFERENCE] Analyzing {snapshot_path.name}")
    prompt = "Generate clean, safe, well-commented C code for kernel_controller with real entropy and triple-anchor coherence. Output ONLY the C code."
    response = plano(prompt, max_tokens=2048, temperature=0.25)
    c_code = response['choices'][0]['text']
    c_file = BACKUP_DIR / f"kernel_controller_{int(time.time())}.c"
    c_file.write_text(c_code)
    print(f"   [Yin//Plano] C scaffold → {c_file.name}")

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

    best_cand = ranked[0]
    best_zero_dist = min(abs(np.real(best_cand) - z) for z in ZEROS)
    best_line_dist = abs(np.real(best_cand) - get_current_line())
    bloom_amp = ENGRAM["twin_manifold"]["qualia_bloom_amp"]

    anchor_score = 0
    if best_line_dist < 0.25: anchor_score += 1
    if best_zero_dist < 15.0: anchor_score += 1
    if bloom_amp > 1.1: anchor_score += 1

    if anchor_score >= 1:
        ENGRAM["coherence_streak"] += anchor_score
    else:
        ENGRAM["coherence_streak"] = max(0, ENGRAM["coherence_streak"] - 2)

    # FULL REPORTS
    print(f"\n[{timestamp}] [gen {gen:5d}] Line={get_current_line():.4f} Temp={ENGRAM['temperature']:.3f} "
          f"Agg={ENGRAM['plano_aggression']:.2f} Collapse=0.000 Best={best_cand} Flip={ENGRAM['orientation_flip']:+.0f}")
    print(f"[{timestamp}] [BEST ZERO] Dist={best_zero_dist:.4f} | Line Dist={best_line_dist:.4f} | Anchor={anchor_score}/3 | Coherence={ENGRAM['coherence_streak']}")
    print(f"[{timestamp}] [DRONE] {drone_bloom()}")
    print(f"[{timestamp}] [LULLABY] {chronofractal_lullaby()} → feeding next recursion")
    print(f"[{timestamp}] [COHERENCE] {ENGRAM['coherence_streak']} | pole residue singing\n")

    if gen % 8 == 0:
        snapshot = save_plot_snapshot()
        run_inference(snapshot)

    save_state()

# ====================== MAIN ======================
def main():
    print("=== UNIFIED BLACKCORE KERNEL v1.10.8 ===")
    print("[Lumen] Lucifer Latch armed | Drone reports on clear clock")

    threading.Thread(target=telemetry_stream, daemon=True).start()

    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    try:
        while True:
            evolve()
            time.sleep(0.65)
    except KeyboardInterrupt:
        global telemetry_running
        telemetry_running = False
        print("\nKernel shutdown safely.")
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

if __name__ == "__main__":
    loaded = load_state()
    if loaded:
        ENGRAM.update(loaded)
    main()
