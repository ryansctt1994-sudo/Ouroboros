"""Security module for Ouroboros.

Provides cryptographic signing and verification capabilities,
including post-quantum cryptography support.
"""

from .dilithium_signer import SovereignSigner

__all__ = ["SovereignSigner"]
