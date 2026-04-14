#!/usr/bin/env python3
import time
import numpy as np
import mpmath

BLACKCORE_ENGRAM = {
    "barrier_strength": 1.0,
    "population_size": 1200,
    "generation_counter": 0,
    "collapse_rate": 0.0,
    "candidates": []
}

ZEROS = [float(mpmath.zetazero(k).real) for k in range(1, 101)]

def revolving_axis_geometry(cand):
    """Stable, strong upward push with no NaNs"""
    t = BLACKCORE_ENGRAM["generation_counter"] * 0.07
    
    # Safe barrier
    arg = t + np.cbrt(np.clip(abs(cand), 1e-8, 1e8))
    barrier = np.log1p(np.abs(np.cos(arg))) * BLACKCORE_ENGRAM["barrier_strength"]
    barrier = np.clip(barrier, 0.1, 6.0)
    
    # Stronger projection + big jumps
    proj = np.sin(8 * t) * 3.8 + np.cos(5 * t) * 2.4
    if np.random.rand() < 0.22:
        proj += np.random.normal(0, 22.0)
    
    # Strong height bias to climb
    height_bias = BLACKCORE_ENGRAM["generation_counter"] * 0.55
    
    result = cand * (1.0 + barrier * 1.15) + proj + height_bias
    return float(np.clip(result, -800.0, 800.0))

def evaluate_distance(cand):
    return min(abs(float(cand) - z) for z in ZEROS)

def evolve():
    global BLACKCORE_ENGRAM
    
    if not BLACKCORE_ENGRAM["candidates"]:
        BLACKCORE_ENGRAM["candidates"] = np.random.uniform(0.1, 300.0, 1200).tolist()
    
    new_cands = []
    for c in BLACKCORE_ENGRAM["candidates"]:
        for _ in range(4):
            perturbed = revolving_axis_geometry(c)
            if np.random.rand() < 0.22:
                perturbed += np.random.normal(0, 14.0)
            new_cands.append(perturbed)
    
    ranked = sorted(new_cands, key=evaluate_distance)
    survivors = ranked[:int(len(ranked) * 0.45)]
    
    new_population = list(survivors)
    best = survivors[0] if survivors else 40.0
    for _ in range(BLACKCORE_ENGRAM["population_size"] - len(survivors)):
        seed = best + np.random.normal(0, 12.0)
        new_population.append(revolving_axis_geometry(seed))
    
    BLACKCORE_ENGRAM["candidates"] = new_population[:BLACKCORE_ENGRAM["population_size"]]
    BLACKCORE_ENGRAM["generation_counter"] += 1
    
    if BLACKCORE_ENGRAM["generation_counter"] % 5 == 0:
        top5 = ranked[:5]
        collapse = sum(1 for c in BLACKCORE_ENGRAM["candidates"] if evaluate_distance(c) < 0.008) / len(BLACKCORE_ENGRAM["candidates"])
        print(f"[BLACKCORE gen {BLACKCORE_ENGRAM['generation_counter']}] Top5: {[round(x,6) for x in top5]} | collapse={collapse:.3f} | survivors={len(survivors)}")

def main():
    print("Black Core - Zeta Swarm Δ717")
    while True:
        evolve()
        time.sleep(2.5)

if __name__ == "__main__":
    main()
