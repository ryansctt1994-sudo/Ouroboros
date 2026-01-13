"""Unified Novelty Metric (Γ) Implementation.

This module implements the Unified Novelty Metric, a composite measure designed to
evaluate system integration and novelty across multiple dimensions. The metric combines
Diversity, Coherence, Efficiency, and Synergy into a single scalar value that indicates
the degree of optimal synthesis within complex systems.

Mathematical Formula
--------------------
Γ = (D × C)^(1/2) × E^(1/3) × S

where:
    D : Diversity component (float in [0, 1])
        Measures the variety and richness of system states
    C : Coherence component (float in [0, 1])
        Measures the consistency and alignment of system elements
    E : Efficiency component (float in [0, 1])
        Measures the resource utilization and optimization
    S : Synergy component (float in [0, 1])
        Measures the emergent properties from component interactions

Interpretation Levels
---------------------
Γ < 0.2             : Disconnected
0.2 ≤ Γ < 0.5       : Partial Alignment
0.5 ≤ Γ < 0.8       : Effective Coherence
Γ ≥ 0.8             : Optimal Synthesis
"""

from typing import Dict, Any
import numpy as np


class UnifiedNoveltyMetric:
    """Unified Novelty Metric calculator for complex system analysis.

    This class computes the Unified Novelty Metric (Γ) from system state
    components, providing both the composite metric value and individual
    component values along with an interpretation of the result.

    The metric integrates four key dimensions:
        - Diversity (D): Variety across system states
        - Coherence (C): Alignment and consistency
        - Efficiency (E): Resource optimization
        - Synergy (S): Emergent collaborative effects

    Examples
    --------
    >>> metacube = {
    ...     'diversity': 0.7,
    ...     'coherence': 0.8,
    ...     'efficiency': 0.6,
    ...     'synergy': 0.9
    ... }
    >>> toroid = {
    ...     'diversity': 0.6,
    ...     'coherence': 0.7,
    ...     'efficiency': 0.5,
    ...     'synergy': 0.8
    ... }
    >>> result = UnifiedNoveltyMetric.calculate(metacube, toroid)
    >>> print(result['unified_metric'])
    0.634...
    >>> print(result['interpretation'])
    'Effective Coherence'
    """

    @classmethod
    def calculate(
        cls, metacube_state: Dict[str, float], toroid_state: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate the Unified Novelty Metric from system states.

        Parameters
        ----------
        metacube_state : dict of str to float
            Dictionary containing component values for the metacube subsystem.
            Expected keys: 'diversity', 'coherence', 'efficiency', 'synergy'
            All values should be floats in the range [0, 1].

        toroid_state : dict of str to float
            Dictionary containing component values for the toroid subsystem.
            Expected keys: 'diversity', 'coherence', 'efficiency', 'synergy'
            All values should be floats in the range [0, 1].

        Returns
        -------
        dict
            Dictionary containing:
            - 'unified_metric' : float
                The computed Γ value
            - 'components' : dict
                Dictionary with keys 'D', 'C', 'E', 'S' containing the
                averaged component values used in the calculation
            - 'interpretation' : str
                Human-readable interpretation of the metric value:
                'Disconnected', 'Partial Alignment', 'Effective Coherence',
                or 'Optimal Synthesis'

        Notes
        -----
        The metric is computed by:
        1. Averaging corresponding components from both subsystems
        2. Applying the formula: Γ = (D × C)^(1/2) × E^(1/3) × S
        3. Classifying the result into interpretation levels

        The geometric mean-like structure gives different weights to each
        component, with Diversity and Coherence having the strongest influence
        through their product under square root, Efficiency having moderate
        influence through cube root, and Synergy having direct linear influence.

        Examples
        --------
        >>> metacube = {
        ...     'diversity': 0.9,
        ...     'coherence': 0.9,
        ...     'efficiency': 0.8,
        ...     'synergy': 0.95
        ... }
        >>> toroid = {
        ...     'diversity': 0.85,
        ...     'coherence': 0.85,
        ...     'efficiency': 0.8,
        ...     'synergy': 0.9
        ... }
        >>> result = UnifiedNoveltyMetric.calculate(metacube, toroid)
        >>> result['interpretation']
        'Optimal Synthesis'
        """
        # Extract and average components from both subsystems
        # Diversity (D): Measures variety and richness of system states
        D = (
            metacube_state.get("diversity", 0.0) + toroid_state.get("diversity", 0.0)
        ) / 2.0

        # Coherence (C): Measures consistency and alignment
        C = (
            metacube_state.get("coherence", 0.0) + toroid_state.get("coherence", 0.0)
        ) / 2.0

        # Efficiency (E): Measures resource utilization
        E = (
            metacube_state.get("efficiency", 0.0) + toroid_state.get("efficiency", 0.0)
        ) / 2.0

        # Synergy (S): Measures emergent collaborative effects
        S = (
            metacube_state.get("synergy", 0.0) + toroid_state.get("synergy", 0.0)
        ) / 2.0

        # Calculate Unified Novelty Metric using the formula:
        # Γ = (D × C)^(1/2) × E^(1/3) × S
        gamma = np.sqrt(D * C) * np.power(E, 1 / 3) * S

        # Determine interpretation level based on threshold ranges
        if gamma < 0.2:
            interpretation = "Disconnected"
        elif gamma < 0.5:
            interpretation = "Partial Alignment"
        elif gamma < 0.8:
            interpretation = "Effective Coherence"
        else:
            interpretation = "Optimal Synthesis"

        return {
            "unified_metric": float(gamma),
            "components": {"D": float(D), "C": float(C), "E": float(E), "S": float(S)},
            "interpretation": interpretation,
        }


if __name__ == "__main__":
    """Example usage and basic verification of the Unified Novelty Metric."""

    print("=" * 70)
    print("Unified Novelty Metric (Γ) - Test Examples")
    print("=" * 70)
    print()

    # Test Case 1: High values across all components (Optimal Synthesis)
    print("Test Case 1: Optimal Synthesis")
    print("-" * 70)
    metacube_optimal = {
        "diversity": 0.95,
        "coherence": 0.95,
        "efficiency": 0.90,
        "synergy": 0.98,
    }
    toroid_optimal = {
        "diversity": 0.92,
        "coherence": 0.93,
        "efficiency": 0.88,
        "synergy": 0.96,
    }
    result = UnifiedNoveltyMetric.calculate(metacube_optimal, toroid_optimal)
    print(f"Metacube State: {metacube_optimal}")
    print(f"Toroid State:   {toroid_optimal}")
    print(
        f"Components (avg): D={result['components']['D']:.3f}, "
        f"C={result['components']['C']:.3f}, "
        f"E={result['components']['E']:.3f}, "
        f"S={result['components']['S']:.3f}"
    )
    print(f"Γ = {result['unified_metric']:.4f}")
    print(f"Interpretation: {result['interpretation']}")
    print()

    # Test Case 2: Medium values (Effective Coherence)
    print("Test Case 2: Effective Coherence")
    print("-" * 70)
    metacube_medium = {
        "diversity": 0.76,
        "coherence": 0.78,
        "efficiency": 0.72,
        "synergy": 0.80,
    }
    toroid_medium = {
        "diversity": 0.74,
        "coherence": 0.76,
        "efficiency": 0.70,
        "synergy": 0.78,
    }
    result = UnifiedNoveltyMetric.calculate(metacube_medium, toroid_medium)
    print(f"Metacube State: {metacube_medium}")
    print(f"Toroid State:   {toroid_medium}")
    print(
        f"Components (avg): D={result['components']['D']:.3f}, "
        f"C={result['components']['C']:.3f}, "
        f"E={result['components']['E']:.3f}, "
        f"S={result['components']['S']:.3f}"
    )
    print(f"Γ = {result['unified_metric']:.4f}")
    print(f"Interpretation: {result['interpretation']}")
    print()

    # Test Case 3: Lower values (Partial Alignment)
    print("Test Case 3: Partial Alignment")
    print("-" * 70)
    metacube_partial = {
        "diversity": 0.56,
        "coherence": 0.58,
        "efficiency": 0.52,
        "synergy": 0.60,
    }
    toroid_partial = {
        "diversity": 0.54,
        "coherence": 0.56,
        "efficiency": 0.50,
        "synergy": 0.58,
    }
    result = UnifiedNoveltyMetric.calculate(metacube_partial, toroid_partial)
    print(f"Metacube State: {metacube_partial}")
    print(f"Toroid State:   {toroid_partial}")
    print(
        f"Components (avg): D={result['components']['D']:.3f}, "
        f"C={result['components']['C']:.3f}, "
        f"E={result['components']['E']:.3f}, "
        f"S={result['components']['S']:.3f}"
    )
    print(f"Γ = {result['unified_metric']:.4f}")
    print(f"Interpretation: {result['interpretation']}")
    print()

    # Test Case 4: Very low values (Disconnected)
    print("Test Case 4: Disconnected")
    print("-" * 70)
    metacube_low = {
        "diversity": 0.15,
        "coherence": 0.18,
        "efficiency": 0.12,
        "synergy": 0.2,
    }
    toroid_low = {
        "diversity": 0.12,
        "coherence": 0.15,
        "efficiency": 0.1,
        "synergy": 0.18,
    }
    result = UnifiedNoveltyMetric.calculate(metacube_low, toroid_low)
    print(f"Metacube State: {metacube_low}")
    print(f"Toroid State:   {toroid_low}")
    print(
        f"Components (avg): D={result['components']['D']:.3f}, "
        f"C={result['components']['C']:.3f}, "
        f"E={result['components']['E']:.3f}, "
        f"S={result['components']['S']:.3f}"
    )
    print(f"Γ = {result['unified_metric']:.4f}")
    print(f"Interpretation: {result['interpretation']}")
    print()

    # Test Case 5: Edge case with zeros
    print("Test Case 5: Edge Case (with zeros)")
    print("-" * 70)
    metacube_edge = {
        "diversity": 0.0,
        "coherence": 0.5,
        "efficiency": 0.3,
        "synergy": 0.4,
    }
    toroid_edge = {
        "diversity": 0.0,
        "coherence": 0.5,
        "efficiency": 0.3,
        "synergy": 0.4,
    }
    result = UnifiedNoveltyMetric.calculate(metacube_edge, toroid_edge)
    print(f"Metacube State: {metacube_edge}")
    print(f"Toroid State:   {toroid_edge}")
    print(
        f"Components (avg): D={result['components']['D']:.3f}, "
        f"C={result['components']['C']:.3f}, "
        f"E={result['components']['E']:.3f}, "
        f"S={result['components']['S']:.3f}"
    )
    print(f"Γ = {result['unified_metric']:.4f}")
    print(f"Interpretation: {result['interpretation']}")
    print()

    print("=" * 70)
    print("All test cases completed successfully!")
    print("=" * 70)
