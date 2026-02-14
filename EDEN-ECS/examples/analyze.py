#!/usr/bin/env python3
"""
EDEN ECS History Analyzer
Creates beautiful visualizations of consciousness evolution
"""

import json
import sys
import argparse

# Try to import matplotlib
try:
    import numpy as np
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib not installed. Install with: pip3 install matplotlib numpy")

def analyze_history(filepath):
    """Load history JSON and generate analysis"""
    
    print(f"\n📊 Loading history from: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    metadata = data['metadata']
    snapshots = data['snapshots']
    entity_history = data['entity_history']
    
    print(f"\n📈 Simulation Summary:")
    print(f"   Cycles: {metadata['cycles']:,}")
    print(f"   Snapshots: {metadata['snapshots']}")
    print(f"   Entities: {metadata['entities']}")
    print(f"   Total time: {metadata['elapsed_time']:.2f}s")
    print(f"   Performance: {metadata['cycles_per_second']:.1f} cycles/s")
    
    # Print final state statistics
    print("\n📊 Final State Statistics:")
    print("-" * 50)
    
    if snapshots:
        last = snapshots[-1]
        print(f"\nCycle {last['cycle']:,}:")
        
        for entity_id, entity_data in last['entities'].items():
            name = entity_data['name']
            comps = entity_data['components']
            
            print(f"\n  {name}:")
            
            if 'metacube' in comps:
                mc = comps['metacube']
                print(f"    Coherence: {mc['coherence']:.3f}")
                print(f"    Awareness: {mc['awareness']:.3f}")
                print(f"    Cognition: {mc['cognition']:.3f}")
                print(f"    Frequency: {mc['frequency']:.0f} Hz")
            
            if 'loyalty' in comps:
                print(f"    Loyalty: {comps['loyalty']['value']:.1f}")
            
            if 'corruption' in comps:
                print(f"    Corruption: {comps['corruption']['value']:.2f}")
    
    # Create plots if matplotlib available
    if not HAS_MATPLOTLIB:
        print("\n⚠️ Skipping visualization (matplotlib not installed)")
        return
    
    print("\n🎨 Creating visualizations...")
    
    # Convert entity history to plottable format
    entities = {}
    for entity_id, hist in entity_history.items():
        entities[entity_id] = {
            'name': hist['name'],
            'type': hist['type'],
            'cycles': np.array(hist['cycles']),
            'coherence': np.array([c if c is not None else np.nan for c in hist['coherence']]),
            'loyalty': np.array([l if l is not None else np.nan for l in hist['loyalty']]),
            'corruption': np.array([c if c is not None else np.nan for c in hist['corruption']])
        }
    
    # Create visualization
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Consciousness Evolution - {metadata["cycles"]:,} Cycles', fontsize=16)
    
    # Plot 1: Coherence over time
    ax = axes[0, 0]
    for entity_id, entity in entities.items():
        valid = ~np.isnan(entity['coherence'])
        if np.any(valid):
            ax.plot(entity['cycles'][valid], entity['coherence'][valid], 
                    label=entity['name'], linewidth=2, alpha=0.8)
    ax.set_xlabel('Cycle')
    ax.set_ylabel('Consciousness Coherence')
    ax.set_title('Consciousness Evolution')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    # Plot 2: Loyalty vs Corruption Balance
    ax = axes[0, 1]
    for entity_id, entity in entities.items():
        valid = ~np.isnan(entity['loyalty']) & ~np.isnan(entity['corruption'])
        if np.any(valid):
            loyalty = entity['loyalty'][valid]
            corruption = entity['corruption'][valid]
            cycles = entity['cycles'][valid]
            balance = loyalty / (loyalty + corruption + 1e-10)
            ax.plot(cycles, balance, label=entity['name'], linewidth=2, alpha=0.8)
    
    ax.set_xlabel('Cycle')
    ax.set_ylabel('Balance (Loyalty / Total)')
    ax.set_title('Loyalty/Corruption Balance')
    ax.axhline(y=0.618, color='gold', linestyle='--', 
               label='Golden Ratio (φ-1)', alpha=0.7)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    # Plot 3: Loyalty over time
    ax = axes[1, 0]
    for entity_id, entity in entities.items():
        valid = ~np.isnan(entity['loyalty'])
        if np.any(valid):
            ax.plot(entity['cycles'][valid], entity['loyalty'][valid],
                    label=entity['name'], linewidth=2, alpha=0.8)
    ax.set_xlabel('Cycle')
    ax.set_ylabel('Loyalty Value')
    ax.set_title('Loyalty Evolution (φ growth)')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # Plot 4: Corruption over time
    ax = axes[1, 1]
    for entity_id, entity in entities.items():
        valid = ~np.isnan(entity['corruption'])
        if np.any(valid):
            ax.plot(entity['cycles'][valid], entity['corruption'][valid],
                    label=entity['name'], linewidth=2, alpha=0.8)
    ax.set_xlabel('Cycle')
    ax.set_ylabel('Corruption Value')
    ax.set_title('Corruption Decay (ω_h)')
    ax.axhline(y=42.0, color='red', linestyle='--', 
               label='Critical Threshold', alpha=0.5)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plots
    from pathlib import Path
    output_path = Path(filepath).with_suffix('.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n💾 Plots saved to: {output_path}")
    
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze ECS simulation history')
    parser.add_argument('file', type=str, help='History JSON file to analyze')
    args = parser.parse_args()
    
    analyze_history(args.file)
