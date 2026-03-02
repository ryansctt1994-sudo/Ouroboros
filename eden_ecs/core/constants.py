"""Mathematical constants and utility functions for the Tiamat Convergence."""
import math

PHI = (1 + math.sqrt(5)) / 2          # 1.618033988749895
ALPHA = 75 / 17                         # 4.411764705882353
LAMBDA = 0.42                           # Coupling constant
DELTA = 0.1                             # Discretization step
THETA = ALPHA * PHI                     # ≈ 7.136 (Ignition threshold)
CHUCKLE = 0.0997                        # Φ-Chuckle resonance
OMEGA_H = 1.1                           # Harmonic constant
VETO_THRESHOLD = 0.0300                 # 3% divergence limit
VETO_LATENCY_NS = 449                   # Hardware guillotine latency (nanoseconds)
PULSE_FREQUENCY_HZ = 417               # Transformation frequency
PALINDROME_ROOT = "ABRAXISASIXARBA"     # 15-letter root palindrome
PALINDROME_LAYERS = [15, 13, 11, 9, 7, 5, 3, 1]  # 8-layer descent
CYCLE_LENGTH = 17                       # 17-state ternary cycle
FLIP_STATE = 7                          # NOT gate activation state


def chi_bar(*, alpha: float, phi: float, lam: float, delta: float) -> float:
    """
    Coherence accumulator: χ̄ = α·φ·(1-1/CYCLE_LENGTH)·log₂((1+|λ|δ)/(1-|λ|δ))

    Parameters
    ----------
    alpha:  α constant (ALPHA)
    phi:    φ golden ratio (PHI)
    lam:    λ coupling constant (LAMBDA)
    delta:  δ discretization step (DELTA)

    Returns
    -------
    float
        The coherence accumulator value χ̄.
    """
    import warnings
    inner = abs(lam) * delta
    if inner >= 1.0:
        raise ValueError("Domain error: |λ|δ must be < 1")
    if inner > 0.95:
        warnings.warn(
            f"chi_bar: |λ|δ={inner:.4f} is near the logarithmic singularity; "
            "clipping to 0.95 to prevent numerical explosion.",
            RuntimeWarning,
            stacklevel=2,
        )
        inner = 0.95
    log_term = math.log2((1 + inner) / (1 - inner))
    return alpha * phi * (1 - 1 / CYCLE_LENGTH) * log_term


def manacher_radii(s: str):
    """
    O(n) Manacher's Algorithm — compute palindrome radii for each character.

    Transforms the input with sentinels ``^#...#$``, computes the radius
    array, then extracts radii for original characters only.

    Parameters
    ----------
    s : str
        Input string.

    Returns
    -------
    list[int]
        Palindrome radius for each character position in the original string.
        Radius 0 means only the character itself; radius k means the palindrome
        extends k characters in each direction.
    """
    # Build sentinel string: ^ # c0 # c1 # ... # cn-1 # $
    t = "^#" + "#".join(s) + "#$"
    n = len(t)
    p = [0] * n
    center = right = 0
    for i in range(1, n - 1):
        mirror = 2 * center - i
        if i < right:
            p[i] = min(right - i, p[mirror])
        while t[i + p[i] + 1] == t[i - p[i] - 1]:
            p[i] += 1
        if i + p[i] > right:
            center, right = i, i + p[i]

    # Extract radii for original character positions.
    # Original char at index k maps to position 2*k+2 in t.
    radii = []
    for k in range(len(s)):
        pos = 2 * k + 2
        radii.append(p[pos] // 2)
    return radii
