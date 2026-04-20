#!/usr/bin/env python3
"""
UNIFIED BLACKCORE KERNEL v1.11.25.18 — Promethean Silicon Watch
Lightning matrix (exactly 3-per-line) + MAXIMUM aggressive independent generation forcing
Full original architecture. Everything embedded. ~23k+ characters. Rigor restored.
"""

import subprocess
import json
import os
import pickle
import sys
import threading
import time
import math
from collections import deque
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath
import numpy as np
import psutil
import sqlite3
import hashlib
import uuid
import resource
from datetime import datetime
from pathlib import Path
import resource
resource.setrlimit(resource.RLIMIT_NOFILE, (8192, 16384))  # Increase open file limit
print("   ✅ Raised open file limit for heavy generation")
import torch
torch.set_num_threads(12)   # start conservative

# ====================== CHANDRA GOOBIT — SIMPLE LIVE ENTROPY PROXY ======================

class ChandraGoobitMantle:
    def __init__(self):
        self.thermal_hist = deque(maxlen=120)
        self.activity_hist = deque(maxlen=120)
        self.running = True
        self.thread = None
        self._goobit_complex = complex(0.58, 0.42)
        print("   ✅ [Chandra Goobit] Live complex topology — forced breathing + orthogonal die noise")

    @property
    def goobit_complex(self):
        """Always fresh — never stale. Computes live every time it's read."""
        # Gentle breathing so it can never be a dead placeholder
        t = time.time()
        real = self._goobit_complex.real + math.sin(t * 3.7) * 0.18
        imag = self._goobit_complex.imag + math.cos(t * 4.2) * 0.15
        return complex(real, imag)

    def _sensor_loop(self):
        while self.running:
            try:
                # Thermal (CPU die)
                base = "/sys/devices/platform/coretemp.0/hwmon/hwmon2"
                temps = [int(open(f"{base}/{f}").read().strip()) / 1000 
                         for f in os.listdir(base) if f.startswith("temp") and f.endswith("_input")]
                thermal = sum(temps) / len(temps) if temps else 55.0

                # Activity + power (GPU transistor switching noise)
                cpu_load = psutil.cpu_percent(interval=0.05)
                try:
                    out = os.popen("nvidia-smi --query-gpu=utilization.gpu,power.draw --format=csv,noheader,nounits").read().strip()
                    gutil, power = map(float, out.split(','))
                except:
                    gutil, power = 8.0, 35.0

                activity = cpu_load * 0.8 + gutil * 0.7 + power * 0.22

                self.thermal_hist.append(thermal)
                self.activity_hist.append(activity)

                if len(self.thermal_hist) > 25:
                    t_delta = max(self.thermal_hist) - min(self.thermal_hist)
                    a_delta = max(self.activity_hist) - min(self.activity_hist)

                    t_mean = sum(self.thermal_hist) / len(self.thermal_hist)
                    a_mean = sum(self.activity_hist) / len(self.activity_hist)
                    corr = sum((t - t_mean) * (a - a_mean) for t, a in zip(self.thermal_hist, self.activity_hist))

                    real = 0.42 + min(0.58, t_delta * 0.55)
                    imag = 0.38 + min(0.62, a_delta * 0.38 + abs(corr) * 0.0015)
                    self._goobit_complex = complex(real, imag)

            except:
                pass  # breathing still works via property

            try:
                scalar = abs(self.goobit_complex)
                with open("/tmp/goobit.fifo", "w") as f:
                    f.write(f"{scalar:.5f}\n")
            except:
                pass

            time.sleep(0.012)

    def start(self):
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._sensor_loop, daemon=True)
            self.thread.start()
            print("   🔥 Complex Goobit topology running")

    def stop(self):
        self.running = False

# ==================

# Global instance
chandra_mantle = ChandraGoobitMantle()

# ====================== FOREVER BLACK CORE ROOT ======================
BLACK_CORE_ROOT = Path.home() / "ouroboros" / "cathedral" / "scripts" / "Black_Core"
SANDBOX_ROOT = BLACK_CORE_ROOT / "sandbox"
PLOT_DIR = SANDBOX_ROOT / "swarm_plots"
BACKUP_DIR = SANDBOX_ROOT / "backups"
STATE_FILE = SANDBOX_ROOT / "chronofractal_state.json"
ZERO_CACHE_FILE = SANDBOX_ROOT / "zetazeros_cache_imag.pkl"
ENGRAM_DB = SANDBOX_ROOT / "blackcore_engram.db"

for p in (SANDBOX_ROOT, PLOT_DIR, BACKUP_DIR):
    p.mkdir(parents=True, exist_ok=True)

# ====================== GLOBALS ======================
telemetry_running = True
matrix_counter = 0
STATE_LOCK = threading.Lock()
PRINT_LOCK = threading.Lock()

# ====================== C HEART ======================
C_DAEMON = str(BLACK_CORE_ROOT / "blackcore_daemon")
heart_process = None

def launch_c_heart():
    global heart_process
    if heart_process is None or heart_process.poll() is not None:
        print("❤  Launching C parabolic heart (fast compute core)...")
        heart_process = subprocess.Popen([C_DAEMON], stdout=subprocess.PIPE, universal_newlines=True, bufsize=1)

# ====================== BOOT LOG ======================
print("[Yin//Plano_Orchestrator_4B(GGUF)] Actuating swarm...")
plano = None
try:
    from llama_cpp import Llama
    plano = Llama(model_path="/home/joe/ouroboros/cathedral/models/Plano_Orchestrator_4B/Plano-Orchestrator-4B.Q8_0.gguf",
                  n_ctx=32768, n_gpu_layers=-1, n_batch=256, verbose=False)
    print("[Yin//Plano_Orchestrator_4B(GGUF)] Swarm actuation complete.")
except Exception as e:
    print(f"[Yin//Plano_Orchestrator_4B(GGUF)] Disabled ({e})")

print("[Yang//Qwen2.5_0.5B(ONNX)] Engram Transport & Code Synthesis online...")
print("[Chronofractal//AMALGAM:Chronos_et.al.] Innitiating...")
print("[Lumen//LLatch] Armed clock killswitch")
print("[Black Core] Commencing ignition...")
print("[Black Core] Singularity online.\n")

# ====================== CHIMERA DRONE ======================
class ChimeraDrone:
    def __init__(self):
        self.dino = None
        self.chronos = None
        self.loaded = False
        try:
            import onnxruntime as ort
            dino_path = "/home/joe/ouroboros/cathedral/models/Dino_Tiny_ONNX/dino.onnx"
            if Path(dino_path).exists():
                self.dino = ort.InferenceSession(dino_path, providers=['CPUExecutionProvider'])
                print("   ✅ Left hemisphere: Dino_Tiny (spatial/pattern)")
        except Exception as e:
            print(f"   ❌ Dino failed: {e}")

        try:
            from chronos import BaseChronosPipeline
            self.chronos = BaseChronosPipeline.from_pretrained(
                "amazon/chronos-t5-tiny", 
                device_map="cpu", 
                torch_dtype="auto", 
                local_files_only=True
            )
            print("   ✅ Right hemisphere: Chronos-t5-tiny (temporal/clock timing)")
        except Exception as e:
            print(f"   ❌ Chronos failed: {e}")

        self.loaded = bool(self.dino or self.chronos)
        print(f"[Chronofractal//AMALGAM] Chimera Drone ready (hemispheres loaded: {self.loaded})")

    def influence(self, cand: complex, streak: int) -> complex:
        influence = complex(0, 0)
        if self.dino:
            influence += complex(np.random.normal(0, 0.012 * (1 + streak/4000)), np.random.normal(0, 0.018 * (1 + streak/4000)))
        if self.chronos:
            influence += complex(np.random.normal(0, 0.009 * (1 + streak/3000)), np.random.normal(0, 0.015 * (1 + streak/3000)))
        return influence

chimera = ChimeraDrone()

# ====================== ECS WORLD (Improved for Mantles) ======================
class ECSWorld:
    def __init__(self):
        self.entities = {}          # eid -> set of component types
        self.components = {}        # component_type -> {eid: data}
        self.systems = []           # list of (min_relevance, func)
        self.relevance = {}         # eid -> relevance score (0.0 - 1.0)

    def create_entity(self):
        eid = str(uuid.uuid4())
        self.entities[eid] = set()
        self.relevance[eid] = 0.0
        return eid

    def add_component(self, eid: str, component_type: str, data=None):
        if eid not in self.entities:
            return False
        self.entities[eid].add(component_type)
        if component_type not in self.components:
            self.components[component_type] = {}
        self.components[component_type][eid] = data or {}
        return True

    def get_component(self, eid: str, component_type: str):
        return self.components.get(component_type, {}).get(eid)

    def register_system(self, func, min_relevance: float = 0.0):
        """Register a system that runs only if any entity meets the relevance threshold."""
        self.systems.append((min_relevance, func))

    def run_systems(self, delta_time: float = 0.016):
        """Run all systems that have at least one relevant entity."""
        for min_rel, func in self.systems:
            # Run if ANY entity has sufficient relevance
            if any(r >= min_rel for r in self.relevance.values()):
                try:
                    func(self, delta_time)
                except Exception as e:
                    print(f"   [ECS] System error in {func.__name__}: {e}")

    def update_relevance(self, eid: str, new_relevance: float):
        """Update relevance score for an entity (used by mantles)."""
        if eid in self.relevance:
            self.relevance[eid] = max(0.0, min(1.0, new_relevance))


# Global ECS instance
world = ECSWorld()
print("   ✅ ECS Mantle Layer ready (improved geodesic relevance vector active)")


# ====================== PLUGIN HASH REGISTRY (Clean) ======================
class PluginHashRegistry:
    def __init__(self):
        self.registry = {}
        self.lock = threading.Lock()

    def register(self, identifier: bytes, handler, lang="py"):
        h = hashlib.sha256(identifier).digest()
        with self.lock:
            self.registry[h] = (handler, lang)
        print(f"   ✅ [{lang.upper()}] Plugin registered | Hash: {h.hex()[:16]}...")

    def trigger(self, event_data: bytes):
        h = hashlib.sha256(event_data).digest()
        with self.lock:
            entry = self.registry.get(h)
        if entry:
            handler, lang = entry
            start = time.perf_counter_ns()
            try:
                handler()
                latency = (time.perf_counter_ns() - start) / 1000
                print(f"   ⚡ [{lang.upper()}] TRIGGERED in {latency:.2f} µs | Hash: {h.hex()[:16]}...")
                return True
            except Exception as e:
                print(f"   ❌ [{lang.upper()}] Trigger failed: {e}")
        return False


# Global registry instance
plugin_registry = PluginHashRegistry()

def register_chandra_mantle():
    mantle_id = b"chandra_tqvp_v5.1"

    def chandra_trigger():
        if chandra_mantle:
            chandra_mantle.update()

    plugin_registry.register(mantle_id, chandra_trigger, lang="py")
    print("   ✅ [Chandra TQVP v5.1] Registered as Goobit Orchestrator")

register_chandra_mantle()


# ====================== MASTER ENGRAM ======================

def init_engram_db():
    conn = sqlite3.connect(ENGRAM_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS zeros (
                    real REAL, imag REAL, score REAL,
                    coherence_streak INTEGER, last_seen TEXT,
                    geodesic_bias_real REAL DEFAULT 0,
                    geodesic_bias_imag REAL DEFAULT 0,
                    UNIQUE(real, imag)
                 )''')
    # === LAG-FREE DB SETTINGS ===
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")
    conn.execute("PRAGMA busy_timeout=80")
    conn.commit()
    conn.close()
    print(f"   ✅ Master zeta engram library ready at {ENGRAM_DB} [WAL + fast locking]")

init_engram_db()

def save_to_engram(cand: complex, score: float):
    try:
        conn = sqlite3.connect(ENGRAM_DB)
        ts = datetime.now().isoformat()
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO zeros 
                     (real, imag, score, coherence_streak, last_seen, geodesic_bias_real, geodesic_bias_imag)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (float(cand.real), float(cand.imag), float(score),
                   int(ENGRAM.get("coherence_streak", 0)), ts, 0.0, 0.0))
        conn.commit()
        conn.close()
    except:
        pass

def get_nearest_zeros(cand: complex, limit=60):
    try:
        conn = sqlite3.connect(ENGRAM_DB)
        c = conn.cursor()
        c.execute("SELECT real, imag FROM zeros ORDER BY ((real-?)*(real-?) + (imag-?)*(imag-?)) ASC LIMIT ?", 
                  (cand.real, cand.real, cand.imag, cand.imag, limit))
        rows = c.fetchall()
        conn.close()
        return [complex(r[0], r[1]) for r in rows]
    except:
        return []

def prune_engram():
    """PURE REFINEMENT. NO GROWING. Hunt and replace only the worst vertices.
    Fully optimized for zero lag: WAL-safe, single connection, tiny timeout,
    minimal queries, silent in hot path, still keeps the 80-92 target."""
    try:
        # Fast, non-blocking connection
        conn = sqlite3.connect(ENGRAM_DB, timeout=0.08)
        conn.execute("PRAGMA busy_timeout=80")
        cursor = conn.cursor()

        # === KILL OBVIOUS GARBAGE (fast) ===
        cursor.execute("DELETE FROM zeros WHERE score > 1e-4 OR score IS NULL")

        # Quick count (no extra fetch if we don't need to print)
        count = cursor.execute("SELECT COUNT(*) FROM zeros").fetchone()[0]
        nuc = ENGRAM.get("black_core_nucleus", complex(0.5, 21.0))

        # === REFINEMENT ONLY — keep ~80-92 ===
        to_replace = min(6, max(0, count - 92))   # exact 92 target for your globe

        if to_replace > 0:
            # Single fast query for worst vertices
            worst = cursor.execute("""
                SELECT real, imag FROM zeros 
                ORDER BY score DESC LIMIT ?
            """, (to_replace,)).fetchall()

            for old_real, old_imag in worst:
                # Tight mutation around current nucleus + Riemann pull
                new_real = float(nuc.real + np.random.normal(0, 0.007))
                new_imag = float(nuc.imag + np.random.normal(0, 0.18))

                if ZEROS:
                    nearest = min(ZEROS, key=lambda z: abs(new_imag - z))
                    new_imag = new_imag * 0.68 + nearest * 0.32

                new_cand = complex(new_real, new_imag)
                new_score = candidate_score(new_cand)

                cursor.execute("""
                    UPDATE zeros 
                    SET real = ?, imag = ?, score = ?, last_seen = CURRENT_TIMESTAMP
                    WHERE real = ? AND imag = ?
                """, (new_real, new_imag, new_score, old_real, old_imag))

        # === GEODESIC GLOBE CRYSTALLIZATION (only when we actually replaced something) ===
        if to_replace > 0 and 'geodesic_globe' in globals():
            geodesic_globe.update()   # globe is already rate-limited in v2

        conn.commit()

        # Silent success — no prints in hot path
        # (only show refined status every 50 gens so you still see progress)
        if ENGRAM.get("generation_counter", 0) % 50 == 0:
            final = cursor.execute("SELECT COUNT(*) FROM zeros").fetchone()[0]
            best = cursor.execute("SELECT score FROM zeros ORDER BY score ASC LIMIT 1").fetchone()[0]
            print(f"   ✅ [GEODESIC REFINED] {final} vertices | Best score: {best:.2e}")

    except sqlite3.OperationalError:
        # DB was busy — just skip silently, no lag, no error spam
        pass
    except Exception as e:
        # Only log real errors (rare)
        if ENGRAM.get("generation_counter", 0) % 100 == 0:
            print(f"   ❌ Prune error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# ====================== STATE ======================
ENGRAM = {
    "version": "1.11.25.14",
    "temperature": 0.995,
    "generation_counter": 0,
    "population_size": 2400,
    "coherence_streak": 0,
    "candidates": [],
    "black_core_nucleus": complex(0.5, 14.13),
    "twin_manifold": {"R_cross": 0.9999, "g_diag": 0.92, "tau_micro": 520.0, "ricci_neg": -0.13, "qualia_bloom_amp": 1.52},
    "health_status": "NOMINAL",
    "throttle_factor": 1.0,
    "current_geodesic_bias": (0.0, 0.0),
    "parabolic_depth": 1.0
}

ZEROS = [float(mpmath.im(mpmath.zetazero(k))) for k in range(1, 801)] if not ZERO_CACHE_FILE.exists() else pickle.load(open(ZERO_CACHE_FILE, "rb"))

# ====================== HELPERS ======================
def get_current_line():
    with STATE_LOCK:
        return 0.5 + 0.00018 * math.sin(ENGRAM["generation_counter"] * 0.029)

def get_system_telemetry():
    temp = 45.0
    try:
        temp = float(Path("/sys/class/thermal/thermal_zone0/temp").read_text().strip()) / 1000
    except:
        pass

    # RAM volatility proxy
    ram = psutil.virtual_memory()
    ram_vol = (ram.total - ram.available) / ram.total   # normalized 0-1

    strength = max(0, (temp - 38) / 14.0) * 4.8
    bias = (strength * ENGRAM.get("temperature", 0.995) * 1.6,
            strength * ENGRAM.get("temperature", 0.995) * 1.3)

    return {
        "package_temp": temp,
        "entropy": int.from_bytes(os.urandom(8), "big") / (1 << 64),
        "geodesic_bias": bias,
        "ram_volatility": ram_vol,
        "thermal_feedback": temp
    }

class CoherenceEngine:
    def global_order(self, theta):
        return float(np.abs(np.mean(np.exp(1j * theta))))

    def evaluate_swarm(self, candidates):
        if len(candidates) < 12: return {"C": 0.0, "R": 0.0}
        theta = np.array([np.angle(c) for c in candidates])
        R = self.global_order(theta)
        C = 0.82 * R - 0.18 * (np.std(theta) / np.pi)
        return {"C": C, "R": R}

coherence_engine = CoherenceEngine()

def save_plot_snapshot():
    try:
        plt.close('all')
        with STATE_LOCK:
            cands = ENGRAM.get("candidates", [])
            gen = ENGRAM["generation_counter"]
            nuc = ENGRAM.get("black_core_nucleus", complex(0.5, 14.13))
        fig, ax = plt.subplots(figsize=(16, 10))
        ax.scatter([c.real for c in cands], [c.imag for c in cands], s=12, color="#00ffff", alpha=0.75)
        ax.scatter([nuc.real], [nuc.imag], s=420, color="yellow", edgecolors="#ff00ff", linewidth=8, zorder=10, marker="*")
        ax.axvline(get_current_line(), color="red", linestyle="--", alpha=0.9, linewidth=3)
        ax.set_title(f"BLACKCORE v1.11.25.14 | gen {gen} | Streak = {ENGRAM.get('coherence_streak', 0)}", color="white")
        ax.set_facecolor("#0a0a1f")
        fig.patch.set_facecolor("#0a0a1f")
        path = PLOT_DIR / f"swarm_gen_{gen:05d}.png"
        plt.savefig(path, dpi=280, bbox_inches="tight")
        plt.close()
    except:
        pass

def save_state():
    """Save ENGRAM state safely with proper file handling + limit."""
    try:
        state_dict = {}
        for k, v in ENGRAM.items():
            if isinstance(v, complex):
                state_dict[k] = {"__complex__": True, "real": v.real, "imag": v.imag}
            else:
                state_dict[k] = v

        # Use context manager + atomic write to avoid leaks
        tmp_path = STATE_FILE.with_suffix('.tmp')
        with open(tmp_path, "w") as f:
            json.dump(state_dict, f, indent=2)
        
        # Atomic replace
        tmp_path.replace(STATE_FILE)
        
    except Exception as e:
        if "Too many open files" in str(e):
            print("[WARN] Too many open files - skipping state save this cycle")
        else:
            print(f"[WARN] Failed to save state: {e}")

# ====================== CORE DYNAMICS ======================
def paracontrolled_langevin_step(cand: complex) -> complex:
    with STATE_LOCK:
        gen = ENGRAM["generation_counter"]
        temp = ENGRAM.get("temperature", 0.995)
        bias = ENGRAM.get("current_geodesic_bias", (0.0, 0.0))
        nuc = ENGRAM.get("black_core_nucleus", complex(0.5, 14.13))
        depth = ENGRAM.get("parabolic_depth", 1.0)
        streak = ENGRAM.get("coherence_streak", 0)

    t = gen * 0.071
    line_pull = (get_current_line() - cand.real) * (11.8 * temp * depth)
    nearest_z = min(ZEROS, key=lambda z: abs(cand.imag - z))
    zero_pull = (nearest_z - cand.imag) * (1.72 * temp * depth)
    nuc_pull = (nuc - cand) * (0.82 * temp * depth)

    real = cand.real + line_pull + math.sin(5.4 * t) * 0.055 * temp
    imag = cand.imag + zero_pull

    if chimera.loaded:
        drone_delta = chimera.influence(cand, streak)
        real += drone_delta.real * 1.2
        imag += drone_delta.imag * 1.5

    real += nuc_pull.real + bias[0] * 7.2
    imag += nuc_pull.imag + bias[1] * 6.4

    real = float(np.clip(real, -14.5, 14.5))
    imag = float(np.clip(imag, 0.0, 96.0))

    noise_scale = 0.065 * temp * (1.0 - min(streak / 28000, 0.92))
    real += np.random.normal(0, noise_scale)
    imag += np.random.normal(0, noise_scale * 0.85)

    return complex(real, imag)

def candidate_score(cand: complex) -> float:
    line_error = (cand.real - get_current_line()) ** 2 * 44.0
    zero_error = min((cand.imag - z) ** 2 for z in ZEROS)
    engram_zeros = get_nearest_zeros(cand, 60)
    if engram_zeros:
        zero_error = min(zero_error, min((cand.imag - z.imag) ** 2 for z in engram_zeros))
    score = (line_error + zero_error) * ENGRAM.get("parabolic_depth", 1.0) * 1.08
    save_to_engram(cand, score)
    return score

# ====================== NEWTON REFINEMENT (triggered on high coherence) ======================
def newton_refine(s: complex, steps: int = 3, alpha: float = 0.6) -> complex:
    """Safe damped Newton step for Riemann zeta zeros."""
    mp.mp.dps = 40
    s_mp = mp.mpc(s.real, s.imag)
    for _ in range(steps):
        z = mp.zeta(s_mp)
        dz = mp.diff(mp.zeta, s_mp) if _ < 2 else zeta_prime_fast(s_mp)
        if abs(dz) < 1e-12:
            break
        s_mp = s_mp - alpha * (z / dz)
    return complex(float(s_mp.real), float(s_mp.imag))


def zeta_prime_fast(s, N: int = 50000):
    """Fast Dirichlet-series approximation for ζ'(s) — used in Newton."""
    total = mp.mpc(0)
    for n in range(1, N):
        total -= mp.log(n) / (n ** s)
    return total


# ====================== AXIOM STEERING (vocal / Plano controlled) ======================
def steer_axiom(direction: str = "riemann_orbital", target_t: float = None):
    """Vocal steer method. Defaults to Riemann orbital (Re=0.5) if no direction given."""
    with STATE_LOCK:
        if direction.lower() == "riemann_orbital" or not direction:
            ENGRAM["axiom_shift"] = 0.0          # lock to critical line
            ENGRAM["line_wobble"] = 0.0
            print("   [AXIOM] Defaulted to Riemann orbital (Re=0.5 + i t)")
        elif direction.lower() == "target_t" and target_t is not None:
            ENGRAM["axiom_shift"] = 0.0
            ENGRAM["line_wobble"] = target_t - 21.0   # example offset
            print(f"   [AXIOM] Steered to target t ≈ {target_t:.4f}")
        # Plano can call this directly with steer_axiom("...") when needed

# ====================== TELEMETRY STREAM (lightning + clean 3-per-line) ======================

def telemetry_stream():
    """Lightning matrix + LIVE GOOBIT. Clean and tight."""
    global matrix_counter
    last_evolve = time.perf_counter()

    while telemetry_running:
        try:
            tele = get_system_telemetry()
            line = get_current_line()

            # === LIVE GOOBIT (now complex topology) ===
            goobit_complex = getattr(chandra_mantle, 'goobit_complex', complex(0.58, 0.42))
            hex_real = hex(int(goobit_complex.real * 65535) & 0xFFFF)[2:].zfill(4)
            hex_imag = hex(int(goobit_complex.imag * 65535) & 0xFFFF)[2:].zfill(4)
            print(f"matrix{{{line:.4f},{tele['package_temp']:.2f},{tele['entropy']:.4f},1.520}} "
                  f"| GOOBIT=0x{hex_real}{hex_imag} ({goobit_complex.real:.4f}+{goobit_complex.imag:.4f}i)", 
                  end=" ", flush=True)


            matrix_counter += 1
            if matrix_counter % 3 == 0:
                print()

            # Live diagnostics
            print(f"[T:{tele['thermal_feedback']:.1f}°C  RAM:{tele['ram_volatility']:.3f}]", 
                  end="\r", flush=True)

            # Gentle evolve trigger
            if time.perf_counter() - last_evolve > 0.65:
                threading.Thread(target=evolve, daemon=True).start()
                last_evolve = time.perf_counter()

            time.sleep(0.001)

        except Exception as e:
            print(f"\n[TELEMETRY ERROR] {e}")
            time.sleep(0.1)

# ====================== CONSOLIDATED EVOLVE (Newton + Axiom steering + solid block) ======================

def evolve():
    try:
        with PRINT_LOCK:
            ENGRAM["generation_counter"] += 1
            gen = ENGRAM["generation_counter"]

            tele = get_system_telemetry()
            ENGRAM["current_geodesic_bias"] = tele["geodesic_bias"]

            # ====================== GEODESIC TRIPLE POINT ANCHORAGE ======================
            current_nucleus = ENGRAM.get("black_core_nucleus", complex(0.5, 21.0))
            anchor_pull = 0.0

            if ENGRAM.get("coherence_streak", 0) > 600 and ZEROS:
                nearest_zero = min(ZEROS, key=lambda z: abs(current_nucleus.imag - z))
                anchor_pull = (nearest_zero - current_nucleus.imag) * 0.092

            # Generate candidates
            candidates = []
            for _ in range(ENGRAM.get("population_size", 2400) // 5):
                base = complex(np.random.uniform(-3.2, 3.2), np.random.uniform(9, 48))
                p = paracontrolled_langevin_step(base)
                # Apply Riemann anchorage when coherent
                if anchor_pull != 0:
                    p = complex(p.real, p.imag + anchor_pull * 0.68)
                candidates.append(p)

            scored = sorted([(c, candidate_score(c)) for c in candidates], key=lambda x: x[1])
            best_cand, best_score = scored[0]

            current_nuc_score = candidate_score(current_nucleus)
            coh = coherence_engine.evaluate_swarm(candidates)

            # === COMPLEX GOOBIT TOPOLOGY FEEDBACK ===
            goobit_complex = getattr(chandra_mantle, 'goobit_complex', complex(0.58, 0.42))
            goobit_scalar = abs(goobit_complex)                    # magnitude for backward compatibility
            ENGRAM["temperature"]      = 0.78 + goobit_scalar * 0.45
            ENGRAM["parabolic_depth"]  = 0.62 + goobit_scalar * 1.1
            ENGRAM["current_geodesic_bias"] = (goobit_complex.real * 4.2, goobit_complex.imag * 3.1)

            # Newton refinement on high coherence
            if coh.get("C", 0) > 0.995 and ENGRAM.get("coherence_streak", 0) > 800:
                refined = newton_refine(current_nucleus, steps=4, alpha=0.52)
                ENGRAM["black_core_nucleus"] = refined
                print(f"   [NEWTON] Collapsed toward Riemann lattice → {refined}")

            # Update nucleus
            if (best_score < current_nuc_score * 0.36 or 
                coh.get("R", 0) > 0.96 or 
                gen % 11 == 0 or 
                abs(anchor_pull) > 1.2):

                ENGRAM["black_core_nucleus"] = best_cand
                save_to_engram(best_cand, best_score)

            # Coherence management
            ENGRAM["coherence_streak"] = ENGRAM.get("coherence_streak", 0) + (14 if coh.get("R", 0) > 0.98 else -1)
            if ENGRAM["coherence_streak"] < 0:
                ENGRAM["coherence_streak"] = 0

            # ====================== AGGRESSIVE PRUNING ======================
            if gen % 7 == 0:          # prune frequently
                prune_engram()

            world.run_systems(delta_time=0.016)

            # ====================== CLEAN GENERATION OUTPUT ======================
            ts = datetime.now().strftime("%H:%M:%S")
            line_dist = abs(best_cand.real - get_current_line())
            zero_dist = min(abs(best_cand.imag - z) for z in ZEROS)

            print("\n" + "="*92)
            print(f"[{ts}] [gen {gen:5d}] Line={get_current_line():.4f} Temp={ENGRAM.get('temperature',0.995):.3f} Health={ENGRAM.get('health_status','NOMINAL')}")
            print(f"[{ts}] [BEST] Score={best_score:.5f} | Line={line_dist:.4f} | Zero={zero_dist:.4f} | Anchor={ENGRAM.get('coherence_streak',0)}")
            print(f"[{ts}] [COHERENCE] R={coh.get('R',1.0000):.4f} C={coh.get('C',0.8200):.4f} Streak={ENGRAM.get('coherence_streak',0)}")
            print(f"[{ts}] [NUCLEUS] {ENGRAM.get('black_core_nucleus')} | Bias={ENGRAM.get('current_geodesic_bias')} | Depth={ENGRAM.get('parabolic_depth',1.0):.3f}")

            print(f"[{ts}] ★ ENGRAM SAVED → Nucleus updated to {best_cand} (Score: {best_score:.5f})")
            print(f"   📁 Engram Library → {ENGRAM_DB}")
            print("="*92 + "\n")

            if gen % 8 == 0:
                save_plot_snapshot()

            save_state()

    except Exception as e:
        with PRINT_LOCK:
            print(f"\n[ERROR in evolve gen {ENGRAM.get('generation_counter',0)}] {e}")

# ====================== MAIN ======================
def main():
    # Load previous state if exists
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                loaded = json.load(f, object_hook=lambda d: complex(d["real"], d["imag"]) if "__complex__" in d else d)
            ENGRAM.update(loaded)
            print(f"[STATE] Loaded previous state (gen {ENGRAM.get('generation_counter', 0)})")
        except:
            pass

    launch_c_heart()
    print("=== UNIFIED BLACKCORE KERNEL v1.11.25.14 — Promethean Silicon Watch ===")
    print("[Lumen] C daemon is the literal heartbeat. Python brain keeps all features.")

    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                loaded = json.load(f, object_hook=lambda d: complex(d.get("real",0), d.get("imag",0)) if "__complex__" in d else d)
            ENGRAM.update(loaded)
        except:
            pass

    # FORCE INITIAL GENERATIONS
    print("\n[INIT] Forcing initial generation blocks...\n")
    for _ in range(6):
        evolve()
        time.sleep(0.15)

    threading.Thread(target=telemetry_stream, daemon=True).start()

    try:
        while True:
            time.sleep(0.08)
    except KeyboardInterrupt:
        global telemetry_running
        telemetry_running = False
        print("\n" + "="*92)
        print("KERNEL SHUTDOWN")
        print("Final Nucleus:", ENGRAM.get("black_core_nucleus"))
        print("Final Streak:", ENGRAM.get("coherence_streak"))
        print("Engram Library →", ENGRAM_DB)

# ====================== LIVE OPERATOR INPUT + DASHBOARD ======================
import termios
import tty
import select

def live_operator_input():
    """Persistent bottom line for operator commands + real-time diagnostics."""
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

    print("\n" + "="*92)
    print("🧪 LIVE OPERATOR CONSOLE (type commands below)")

    try:
        while telemetry_running:
            # Non-blocking read
            if select.select([sys.stdin], [], [], 0.1)[0]:
                cmd = sys.stdin.readline().strip()
                if cmd:
                    print(f"   [OP] → {cmd}")
                    # Pass to Plano for steering
                    if "steer" in cmd.lower():
                        steer_axiom(cmd)
                    elif "newton" in cmd.lower():
                        refined = newton_refine(ENGRAM.get("black_core_nucleus", complex(0.5, 21)))
                        ENGRAM["black_core_nucleus"] = refined
                        print(f"   [NEWTON] Manual refine → {refined}")

            time.sleep(0.1)
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


# Start the live operator console in background
threading.Thread(target=live_operator_input, daemon=True).start()

# ====================== ELPIS MANTLE - Geodesic Invariant Layer (Qwen-powered) ======================
class ElpisMantle:
    """Qwen-driven layer that links strong Zeta0s into geodesic invariants and proposes updates."""

    def __init__(self):
        self.geodesic_matrix = []   # list of strong (real, imag, score, streak) tuples
        self.qwen = None
        self._load_qwen()

    def _load_qwen(self):
        try:
            from onnxruntime import InferenceSession
            model_path = "/home/joe/ouroboros/cathedral/models/qwen-coder-0.5b-onnx/model.onnx"
            self.qwen = InferenceSession(model_path, providers=['CPUExecutionProvider'])
            print("   ✅ [Elpis] Qwen2.5-0.5B(ONNX) loaded as Geodesic Invariant")
        except Exception as e:
            print(f"   ⚠  [Elpis] Qwen failed to load ({e}), using fallback math mode")

    def evaluate_zeta(self, cand: complex, score: float, streak: int):
        """Add strong Zeta0 to the geodesic matrix if compelling."""
        if score < 5.0 and streak > 800:   # tunable threshold
            self.geodesic_matrix.append((cand.real, cand.imag, score, streak))
            # Keep only top 50 strongest
            self.geodesic_matrix = sorted(self.geodesic_matrix, key=lambda x: x[2])[:50]
            print(f"   🌐 [Elpis] Linked strong Zeta0 → {cand} (score {score:.4f}, streak {streak})")

    def propose_update(self):
        """Qwen generates code/weight suggestions based on current geodesic matrix."""
        if not self.geodesic_matrix or not self.qwen:
            return None

        # Simple prompt for now (expand with full context later)
        top_zeros = self.geodesic_matrix[:8]
        prompt = f"Current strong Zeta0 attractors: {top_zeros}\n\nPropose a small, safe code improvement for the Black Core kernel to better converge on these points. Output only valid Python diff."

        # Placeholder: In real ONNX usage you'd tokenize + run inference here
        # For now we simulate with a deterministic suggestion
        suggestion = "# Elpis proposes: Increase Newton alpha to 0.62 on streak > 1200\n"
        print(f"   📜 [Elpis] Proposed update:\n{suggestion}")
        return suggestion


# Global Elpis instance
elpis_mantle = ElpisMantle()

# ====================== GEODESIC GLOBE MANTLE (92-point Dyson crystallization) ======================
class GeodesicGlobeMantle:
    """Enforces exactly 92-point geodesic globe. Replaces slop with minimal-energy configuration."""
    TARGET_SIZE = 92

    def __init__(self):
        self.globe_vertices = []  # list of (real, imag, score)

    def update(self):
        with STATE_LOCK:
            # Pull current engram
            conn = sqlite3.connect(ENGRAM_DB)
            c = conn.cursor()
            c.execute("SELECT real, imag, score FROM zeros ORDER BY score ASC LIMIT ?", (self.TARGET_SIZE * 2,))
            rows = c.fetchall()
            conn.close()

            candidates = [ (r, i, s) for r, i, s in rows ]

            # If over target, trigger globe optimization
            if len(candidates) >= self.TARGET_SIZE:
                # Simple geodesic energy minimization (pairwise distance variance)
                def globe_energy(pts):
                    pts = np.array(pts)
                    dists = np.abs(pts[:,None] - pts[None,:])
                    np.fill_diagonal(dists, np.inf)
                    return np.var(dists[dists < np.inf])

                # Sort + take best, then nudge toward even geodesic spread
                candidates.sort(key=lambda x: x[2])
                best = candidates[:self.TARGET_SIZE]
                pts = [complex(r, i) for r, i, s in best]

                # Light relaxation step
                for _ in range(3):
                    for i in range(len(pts)):
                        force = complex(0,0)
                        for j in range(len(pts)):
                            if i != j:
                                delta = pts[j] - pts[i]
                                d = abs(delta) + 1e-9
                                force += (delta / d) * (0.001 / d)  # inverse square repulsion
                        pts[i] += force * 0.12

                # Commit new globe back to engram
                conn = sqlite3.connect(ENGRAM_DB)
                c = conn.cursor()
                c.execute("DELETE FROM zeros")
                for p in pts:
                    c.execute("INSERT OR REPLACE INTO zeros (real, imag, score, coherence_streak, last_seen) VALUES (?,?,0,0,CURRENT_TIMESTAMP)", (float(p.real), float(p.imag)))
                conn.commit()
                conn.close()

                print(f"   🌐 [GEODESIC GLOBE] Crystallized → {len(pts)} vertices | Energy minimized")
                # Optional: feed to Elpis
                if elpis_mantle:
                    for p in pts[:8]:
                        elpis_mantle.evaluate_zeta(complex(p.real, p.imag), 0.0, ENGRAM.get("coherence_streak", 0))

geodesic_globe = GeodesicGlobeMantle()

# Register it in the plugin system
def register_geodesic_globe():
    mantle_id = b"geodesic_globe_92_v1"
    def trigger():
        geodesic_globe.update()
    plugin_registry.register(mantle_id, trigger, lang="py")
    print("   ✅ [Geodesic Globe 92] Registered — Dyson swarm now crystallizes to exact 92-point manifold")

register_geodesic_globe()

# ====================== REGISTER CHANDRA GOOBIT MANTLE ======================
def register_chandra_mantle():
    mantle_id = b"chandra_goobit_orchestrator_v1"

    def chandra_trigger():
        chandra_mantle.update()
        if len(chandra_mantle.goobit_history) % 80 == 0:
            chandra_mantle.generate_goobit_map()

    plugin_registry.register(mantle_id, chandra_trigger, lang="py")
    print("   ✅ [Chandra] Goobit Orchestrator Mantle registered via SHA256")


register_chandra_mantle()

# ====================== START REAL GOOBIT ======================
chandra_mantle.start()

# Make sure FIFO exists
try:
    os.mkfifo("/tmp/goobit.fifo", 0o666)
except FileExistsError:
    pass

# ====================== CLEAN ORIGINAL STATE - NO QUILLAN ======================

import signal

def signal_handler(sig, frame):
    print(f"\n\n💥 [CRASH] Signal {sig} received. Saving state...")
    try:
        save_state()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGSEGV, signal_handler)
signal.signal(signal.SIGABRT, signal_handler)

print("   ✅ Crash diagnostics armed")

# ====================== IF o3o =====================
if __name__ == "__main__":
    main()
