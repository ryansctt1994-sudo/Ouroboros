#!/usr/bin/env python3
"""
Cathedral-OS Toroidal Coherence Conductor
Central orchestrator: telemetry → E8E8 → router → DNA + model selection.
"""
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, "/home/joe/ouroboros")
from toroidal_minimal import E8E8CoherenceEngine, CoherenceEngineParams

TELEMETRY_FILE = "/tmp/live_telemetry.json"
DNA_OUTPUT = "/tmp/dna_proposal.json"
STATE_FILE = "/tmp/conductor_state.json"

# Router state
class RouterState:
    def __init__(self):
        self.previous_model = None
        self.stability_counter = 0   # hysteresis: count of cycles in same regime
        self.last_dna = None

    def load(self):
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
                self.previous_model = data.get("previous_model")
                self.stability_counter = data.get("stability_counter", 0)
                self.last_dna = data.get("last_dna")
        except:
            pass

    def save(self):
        with open(STATE_FILE, 'w') as f:
            json.dump({
                "previous_model": self.previous_model,
                "stability_counter": self.stability_counter,
                "last_dna": self.last_dna
            }, f)

def get_telemetry():
    try:
        with open(TELEMETRY_FILE) as f:
            t = json.load(f)
        return {
            "hebbian_delta": t.get("hebbian_delta", 2.0),
            "volatility": t.get("volatility", 0.0),
            "cpu_percent": t.get("cpu_percent", 30.0),
            "temperature": t.get("temperature", 30.0),
            "kernel_delta": t.get("kernel_delta", 0.0)
        }
    except:
        return {"hebbian_delta": 2.0, "volatility": 0.0, "cpu_percent": 30.0, "temperature": 30.0, "kernel_delta": 0.0}

def run_toroidal(tele):
    params = CoherenceEngineParams(T=1000)  # faster loop
    engine = E8E8CoherenceEngine(
        params,
        hebbian_delta=tele["hebbian_delta"],
        volatility=tele["volatility"],
        cpu_percent=tele["cpu_percent"]
    )
    result = engine.run()
    return {
        "Gamma": result["final_coherence"]["Gamma"],
        "L": result["final_L"],
        "dna": result["proposed_hebbian_controller"]
    }

def decide_model(tele, coherence, state):
    """
    Weighted decision: Hebbian Delta primary axis, with safety valves.
    Hysteresis: require 2 consecutive cycles to switch.
    """
    H = tele["hebbian_delta"]
    V = tele["volatility"]
    CPU = tele["cpu_percent"]
    Gamma = coherence["Gamma"]
    L = coherence["L"]

    # Base score
    light_score = 0
    heavy_score = 0

    # Primary: Hebbian Delta (4.0 threshold)
    if H < 4.0:
        light_score += 2
    elif H > 6.5:
        heavy_score += 2
    else:
        light_score += 1
        heavy_score += 1

    # Safety valves
    if V > 22.0:
        light_score += 3   # high chaos → fast model
    if CPU > 45.0:
        light_score += 3   # thermal protection
    if Gamma < 0.95:
        heavy_score += 2   # low coherence → need deeper reasoning
    if L < 5.0:
        heavy_score += 1

    # Decide
    chosen = "light" if light_score > heavy_score else "heavy" if heavy_score > light_score else state.previous_model
    # Hysteresis: require two consecutive same decisions before switching
    if chosen == state.previous_model:
        state.stability_counter += 1
    else:
        state.stability_counter = 0
        state.previous_model = chosen

    if state.stability_counter < 2:
        chosen = state.previous_model or "light"

    return chosen

def model_params(chosen):
    if chosen == "light":
        return {
            "model_name": "qwen-0.5b-onnx",
            "path": "/home/joe/ouroboros/cathedral/models/qwen-0.5b-onnx",
            "max_tokens": 512,
            "temperature": 0.8
        }
    else:
        return {
            "model_name": "qwen-coder-7b-onnx",
            "path": "/home/joe/ouroboros/cathedral/models/qwen-coder-7b-onnx",
            "max_tokens": 2048,
            "temperature": 0.6
        }

def main_loop():
    state = RouterState()
    state.load()
    while True:
        tele = get_telemetry()
        coherence = run_toroidal(tele)
        chosen = decide_model(tele, coherence, state)
        params = model_params(chosen)
        state.last_dna = coherence["dna"]
        state.save()

        # Output to console and DNA file
        print(f"[{time.strftime('%H:%M:%S')}] H={tele['hebbian_delta']:.2f} V={tele['volatility']:.1f} CPU={tele['cpu_percent']:.0f}")
        print(f"  Gamma={coherence['Gamma']:.4f} L={coherence['L']:.4f}")
        print(f"  Router: {params['model_name']} (max_tokens={params['max_tokens']})")
        print(f"  DNA: base_decay={coherence['dna']['base_decay']:.3f} press_div={coherence['dna']['pressure_div']:.2f} damp_mul={coherence['dna']['dampening_mul']:.3f}")
        print("-" * 50)

        # Write DNA for kernel_controller
        with open(DNA_OUTPUT, 'w') as f:
            json.dump(coherence["dna"], f, indent=2)

        time.sleep(30)   # loop every 30 seconds

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nConductor stopped.")
        sys.exit(0)
