def _orthogonalise(G, spec_norm, eps):
    # Early return if spec_norm is less than eps
    if spec_norm < eps:
        return G  # Return unchanged
    # Rest of your function logic...
    

def reset_momentum(buf):
    # Use buf.fill(0.0) instead of buf[:] = 0.0
    buf.fill(0.0)
