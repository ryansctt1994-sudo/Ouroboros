"""Post-Quantum Cryptographic Signing with CRYSTALS-Dilithium-5.

This module implements the SovereignSigner class which provides
post-quantum signature generation and verification using the
CRYSTALS-Dilithium-5 algorithm via liboqs.

The implementation includes a fallback mode using SHA-256 HMAC
for environments where liboqs is not available.
"""

import hashlib
import hmac
import json
import os
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, UTC


# Try to import liboqs for post-quantum cryptography
try:
    import oqs
    HAS_LIBOQS = True
except ImportError:
    HAS_LIBOQS = False


@dataclass
class SignatureResult:
    """Result of a signing operation."""
    signature: str  # Hex-encoded signature
    public_key: str  # Hex-encoded public key
    algorithm: str  # Algorithm used (e.g., "Dilithium5", "HMAC-SHA256")
    timestamp: str  # ISO 8601 timestamp
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary representation."""
        return {
            "signature": self.signature,
            "public_key": self.public_key,
            "algorithm": self.algorithm,
            "timestamp": self.timestamp,
        }


class SovereignSigner:
    """Post-quantum cryptographic signer using CRYSTALS-Dilithium-5.
    
    This class provides signing and verification capabilities for manifests
    and other critical data structures. It uses CRYSTALS-Dilithium-5 when
    liboqs is available, falling back to HMAC-SHA256 otherwise.
    
    Attributes:
        algorithm: The signature algorithm in use
        public_key: The public key (hex-encoded)
        
    Example:
        >>> signer = SovereignSigner()
        >>> data = {"manifest": "test", "author": "alice"}
        >>> result = signer.sign(data)
        >>> is_valid = signer.verify(data, result.signature, result.public_key)
    """
    
    def __init__(self, private_key: Optional[bytes] = None):
        """Initialize the signer.
        
        Args:
            private_key: Optional private key bytes. If not provided,
                        a new key pair will be generated.
        """
        if HAS_LIBOQS:
            self.algorithm = "Dilithium5"
            self._init_dilithium(private_key)
        else:
            self.algorithm = "HMAC-SHA256"
            self._init_hmac_fallback(private_key)
    
    def _init_dilithium(self, private_key: Optional[bytes] = None):
        """Initialize Dilithium-5 signer."""
        self._signer = oqs.Signature("Dilithium5")
        
        if private_key is not None:
            # For liboqs, we cannot directly restore from private key alone
            # This is a limitation of the current implementation
            # In production, you would store both private and public keys
            # For now, we generate new keys and warn
            import warnings
            warnings.warn(
                "liboqs does not support restoring from private key alone. "
                "Generating new keypair. Store both public and private keys for restoration.",
                RuntimeWarning
            )
        
        # Generate new key pair
        self._public_key = self._signer.generate_keypair()
        self._private_key = self._signer.export_secret_key()
        self.public_key = self._public_key.hex()
    
    def _init_hmac_fallback(self, private_key: Optional[bytes] = None):
        """Initialize HMAC-SHA256 fallback signer."""
        if private_key is not None:
            self._private_key = private_key
        else:
            # Generate random key
            self._private_key = os.urandom(32)
        
        # For HMAC, public key is derived from private key
        self._public_key = hashlib.sha256(self._private_key).digest()
        self.public_key = self._public_key.hex()
    
    def _canonical_json(self, data: Any) -> str:
        """Create canonical JSON representation of data.
        
        Args:
            data: Data to canonicalize
            
        Returns:
            Canonical JSON string (sorted keys, no whitespace)
        """
        return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    
    def sign(self, data: Any) -> SignatureResult:
        """Sign data with the private key.
        
        Args:
            data: Data to sign (will be converted to canonical JSON)
            
        Returns:
            SignatureResult containing signature and metadata
        """
        # Convert data to canonical bytes
        canonical = self._canonical_json(data)
        message_bytes = canonical.encode('utf-8')
        
        # Generate signature
        if HAS_LIBOQS:
            signature_bytes = self._signer.sign(message_bytes)
        else:
            # HMAC fallback
            signature_bytes = hmac.new(
                self._private_key,
                message_bytes,
                hashlib.sha256
            ).digest()
        
        return SignatureResult(
            signature=signature_bytes.hex(),
            public_key=self.public_key,
            algorithm=self.algorithm,
            timestamp=datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        )
    
    def verify(self, data: Any, signature: str, public_key: str) -> bool:
        """Verify a signature against data.
        
        Args:
            data: Data that was signed
            signature: Hex-encoded signature
            public_key: Hex-encoded public key
            
        Returns:
            True if signature is valid, False otherwise
        """
        # Convert data to canonical bytes
        canonical = self._canonical_json(data)
        message_bytes = canonical.encode('utf-8')
        
        # Decode signature and public key
        signature_bytes = bytes.fromhex(signature)
        public_key_bytes = bytes.fromhex(public_key)
        
        try:
            if HAS_LIBOQS:
                # Use liboqs verification
                verifier = oqs.Signature("Dilithium5")
                return verifier.verify(message_bytes, signature_bytes, public_key_bytes)
            else:
                # HMAC fallback verification
                # For HMAC, we need the private key which we derive from public key hash
                # This is a simplified fallback - in production, use proper key management
                expected_sig = hmac.new(
                    self._private_key,
                    message_bytes,
                    hashlib.sha256
                ).digest()
                return hmac.compare_digest(signature_bytes, expected_sig)
        except Exception:
            return False
    
    def export_public_key(self) -> str:
        """Export the public key as hex string.
        
        Returns:
            Hex-encoded public key
        """
        return self.public_key
    
    def export_private_key(self) -> str:
        """Export the private key as hex string.
        
        WARNING: Keep private keys secure!
        
        Returns:
            Hex-encoded private key
        """
        return self._private_key.hex()
    
    @staticmethod
    def from_private_key(private_key_hex: str) -> 'SovereignSigner':
        """Create a signer from a hex-encoded private key.
        
        Args:
            private_key_hex: Hex-encoded private key
            
        Returns:
            New SovereignSigner instance
        """
        private_key_bytes = bytes.fromhex(private_key_hex)
        return SovereignSigner(private_key=private_key_bytes)
