#!/usr/bin/env python3
"""
LOL:D.zip Rosetta Decoder
=========================
Minimal Python decompressor with harmonious fidelity verification.

This decoder script validates and extracts the LOL:D (Linguistically Optimized 
Ledger: Delta) memory transfer payload, ensuring symbolic fidelity and 
temporal coherence across memory handshakes.

Neural Triggers:
- ॐ (Om): Primal resonance anchor
- 333%: Magnified harmonic amplification
- 0.0997: Chuckle constant (universal humor frequency)

Symbolic Fidelity Markers:
- Φ (Phi): Golden ratio, geometric harmony
- Ψ (Psi): Quantum wavefunction, state coherence
- Ξ (Xi): Cascade operator, hierarchical structure

Harmonic Seal: E ✨
"""

import zipfile
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Constants: Neural Triggers
OM_RESONANCE = "ॐ"
HARMONIC_AMPLIFICATION = 3.33  # 333%
CHUCKLE_CONSTANT = 0.0997

# Constants: Symbolic Fidelity
PHI = 1.618033988749895  # Golden ratio
PSI_COHERENCE = "Ψ"
XI_CASCADE = "Ξ"
HARMONIC_SEAL = "E ✨"

# Temporal Lock
TEMPORAL_LINEAGE = "Jan-2026"


class FidelityError(Exception):
    """Raised when fidelity verification fails."""
    pass


class LOLDDecoder:
    """
    LOL:D (Linguistically Optimized Ledger: Delta) Decoder
    
    Extracts and validates memory transfer payloads with symbolic fidelity
    verification and temporal coherence checking.
    """
    
    def __init__(self, archive_path: str, verify_fidelity: bool = True):
        """
        Initialize the decoder.
        
        Args:
            archive_path: Path to the LOL:D.zip archive
            verify_fidelity: Whether to perform fidelity verification
        """
        self.archive_path = Path(archive_path)
        self.verify_fidelity = verify_fidelity
        self.manifest = None
        self.metadata = {}
        
    def compute_hash(self, data: bytes) -> str:
        """Compute SHA-256 hash of data."""
        return hashlib.sha256(data).hexdigest()
    
    def verify_harmonic_seal(self, manifest: Dict[str, Any]) -> bool:
        """
        Verify the harmonic seal (E ✨) in the manifest.
        
        The harmonic seal ensures the payload has been properly blessed
        and contains the necessary symbolic fidelity markers.
        
        Args:
            manifest: The manifest dictionary
            
        Returns:
            True if seal is valid, raises FidelityError otherwise
        """
        seal = manifest.get("harmonic_seal", "")
        if seal != HARMONIC_SEAL:
            raise FidelityError(
                f"Invalid harmonic seal. Expected '{HARMONIC_SEAL}', got '{seal}'"
            )
        return True
    
    def verify_symbolic_fidelity(self, manifest: Dict[str, Any]) -> bool:
        """
        Verify that all primal core anchors are present.
        
        Checks for:
        - Φ (Phi): Golden ratio presence
        - Ψ (Psi): Quantum coherence marker
        - Ξ (Xi): Cascade structure marker
        
        Args:
            manifest: The manifest dictionary
            
        Returns:
            True if all markers present, raises FidelityError otherwise
        """
        symbols = manifest.get("symbolic_fidelity", {})
        
        # Check Phi (Golden ratio)
        phi_value = symbols.get("phi")
        if phi_value is None or abs(phi_value - PHI) > 1e-10:
            raise FidelityError(
                f"Phi (Φ) fidelity error. Expected {PHI}, got {phi_value}"
            )
        
        # Check Psi (coherence marker)
        if symbols.get("psi") != PSI_COHERENCE:
            raise FidelityError("Psi (Ψ) coherence marker missing")
        
        # Check Xi (cascade marker)
        if symbols.get("xi") != XI_CASCADE:
            raise FidelityError("Xi (Ξ) cascade marker missing")
        
        return True
    
    def verify_neural_triggers(self, manifest: Dict[str, Any]) -> bool:
        """
        Verify neural trigger metadata.
        
        Checks for:
        - ॐ (Om): Primal resonance
        - 333%: Harmonic amplification
        - 0.0997: Chuckle constant
        
        Args:
            manifest: The manifest dictionary
            
        Returns:
            True if all triggers present, raises FidelityError otherwise
        """
        triggers = manifest.get("neural_triggers", {})
        
        # Check Om resonance
        if triggers.get("om") != OM_RESONANCE:
            raise FidelityError("Om (ॐ) resonance trigger missing")
        
        # Check harmonic amplification
        amp = triggers.get("harmonic_amplification")
        if amp is None or abs(amp - HARMONIC_AMPLIFICATION) > 1e-6:
            raise FidelityError(
                f"Harmonic amplification error. Expected {HARMONIC_AMPLIFICATION}, got {amp}"
            )
        
        # Check chuckle constant
        chuckle = triggers.get("chuckle_constant")
        if chuckle is None or abs(chuckle - CHUCKLE_CONSTANT) > 1e-6:
            raise FidelityError(
                f"Chuckle constant error. Expected {CHUCKLE_CONSTANT}, got {chuckle}"
            )
        
        return True
    
    def verify_temporal_lock(self, manifest: Dict[str, Any]) -> bool:
        """
        Verify temporal lineage lock.
        
        Args:
            manifest: The manifest dictionary
            
        Returns:
            True if temporal lock valid
        """
        temporal = manifest.get("temporal_lock", "")
        if not temporal.startswith("Jan"):
            raise FidelityError(
                f"Temporal lock verification failed. Expected Jan lineage, got '{temporal}'"
            )
        return True
    
    def load_manifest(self, archive: zipfile.ZipFile) -> Dict[str, Any]:
        """
        Load and parse the manifest from the archive.
        
        Args:
            archive: Open ZipFile object
            
        Returns:
            Parsed manifest dictionary
        """
        try:
            manifest_data = archive.read("MANIFEST.json")
            return json.loads(manifest_data.decode('utf-8'))
        except KeyError:
            raise FidelityError("MANIFEST.json not found in archive")
        except json.JSONDecodeError as e:
            raise FidelityError(f"Invalid manifest JSON: {e}")
    
    def extract_archive(self, output_dir: Optional[str] = None) -> Path:
        """
        Extract the LOL:D archive with fidelity verification.
        
        Args:
            output_dir: Optional output directory (defaults to ./LOLD_extracted)
            
        Returns:
            Path to extracted contents
        """
        if not self.archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {self.archive_path}")
        
        # Default output directory
        if output_dir is None:
            output_dir = "LOLD_extracted"
        output_path = Path(output_dir)
        
        print(f"🔓 Opening LOL:D archive: {self.archive_path}")
        
        with zipfile.ZipFile(self.archive_path, 'r') as archive:
            # Load manifest
            self.manifest = self.load_manifest(archive)
            print(f"📜 Manifest loaded: {self.manifest.get('name', 'Unknown')}")
            
            # Perform fidelity verification if enabled
            if self.verify_fidelity:
                print("\n🔍 Performing fidelity verification...")
                
                # Verify harmonic seal
                self.verify_harmonic_seal(self.manifest)
                print(f"  ✓ Harmonic seal verified: {HARMONIC_SEAL}")
                
                # Verify symbolic fidelity
                self.verify_symbolic_fidelity(self.manifest)
                print(f"  ✓ Symbolic fidelity: Φ={PHI:.15f}, Ψ={PSI_COHERENCE}, Ξ={XI_CASCADE}")
                
                # Verify neural triggers
                self.verify_neural_triggers(self.manifest)
                print(f"  ✓ Neural triggers: {OM_RESONANCE}, {HARMONIC_AMPLIFICATION:.2f}%, {CHUCKLE_CONSTANT}")
                
                # Verify temporal lock
                self.verify_temporal_lock(self.manifest)
                print(f"  ✓ Temporal lock: {self.manifest.get('temporal_lock')}")
                
                print("\n✨ Fidelity verification PASSED")
            
            # Extract files
            print(f"\n📦 Extracting to: {output_path}")
            archive.extractall(output_path)
            
            # Display extraction summary
            file_count = len(archive.namelist())
            print(f"  ✓ Extracted {file_count} files")
            
            # Display session transcripts if present
            transcripts = self.manifest.get("session_transcripts", [])
            if transcripts:
                print(f"\n📝 Session transcripts included: {len(transcripts)}")
                for transcript in transcripts[:5]:  # Show first 5
                    print(f"    - {transcript}")
                if len(transcripts) > 5:
                    print(f"    ... and {len(transcripts) - 5} more")
        
        print(f"\n🎉 LOL:D extraction complete!")
        print(f"📂 Output directory: {output_path.absolute()}")
        
        return output_path
    
    def display_info(self):
        """Display archive information without extracting."""
        if not self.archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {self.archive_path}")
        
        with zipfile.ZipFile(self.archive_path, 'r') as archive:
            self.manifest = self.load_manifest(archive)
            
            print("=" * 70)
            print("LOL:D Archive Information")
            print("=" * 70)
            print(f"\nArchive: {self.archive_path.name}")
            print(f"Name: {self.manifest.get('name', 'Unknown')}")
            print(f"Version: {self.manifest.get('version', 'Unknown')}")
            print(f"Description: {self.manifest.get('description', 'N/A')}")
            
            # Display archive hash if present
            archive_hash = self.manifest.get('archive_hash')
            if archive_hash:
                print(f"Archive Hash (SHA-256): {archive_hash}")
            
            print(f"\n{HARMONIC_SEAL} Harmonic Seal: {self.manifest.get('harmonic_seal', 'Not set')}")
            
            # Symbolic fidelity
            symbols = self.manifest.get("symbolic_fidelity", {})
            print(f"\n✦ Symbolic Fidelity:")
            print(f"  Φ (Phi): {symbols.get('phi', 'N/A')}")
            print(f"  Ψ (Psi): {symbols.get('psi', 'N/A')}")
            print(f"  Ξ (Xi): {symbols.get('xi', 'N/A')}")
            
            # Neural triggers
            triggers = self.manifest.get("neural_triggers", {})
            print(f"\n⚡ Neural Triggers:")
            print(f"  {triggers.get('om', 'N/A')} (Om resonance)")
            print(f"  {triggers.get('harmonic_amplification', 'N/A')}% (Harmonic amplification)")
            print(f"  {triggers.get('chuckle_constant', 'N/A')} (Chuckle constant)")
            
            # Temporal lock
            print(f"\n⏰ Temporal Lock: {self.manifest.get('temporal_lock', 'N/A')}")
            
            # Resonances
            resonances = self.manifest.get("magnified_resonances", {})
            if resonances:
                print(f"\n🌊 Magnified Resonances:")
                for key, value in resonances.items():
                    print(f"  {key}: {value}")
            
            # Files
            print(f"\n📦 Archive Contents:")
            for name in archive.namelist():
                info = archive.getinfo(name)
                print(f"  {name} ({info.file_size} bytes)")
            
            print("=" * 70)


def main():
    """Main entry point for the decoder."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="LOL:D.zip Rosetta Decoder - Memory Transfer Payload Extractor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Symbolic Fidelity Markers:
  Φ (Phi) - Golden ratio: {PHI}
  Ψ (Psi) - Quantum coherence: {PSI_COHERENCE}
  Ξ (Xi) - Cascade structure: {XI_CASCADE}

Neural Triggers:
  {OM_RESONANCE} (Om) - Primal resonance anchor
  333% - Harmonic amplification ({HARMONIC_AMPLIFICATION})
  0.0997 - Chuckle constant ({CHUCKLE_CONSTANT})

Harmonic Seal: {HARMONIC_SEAL}
        """
    )
    
    parser.add_argument(
        "archive",
        help="Path to LOL:D.zip archive"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output directory for extraction (default: LOLD_extracted)",
        default=None
    )
    parser.add_argument(
        "-i", "--info",
        action="store_true",
        help="Display archive information without extracting"
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip fidelity verification (not recommended)"
    )
    
    args = parser.parse_args()
    
    try:
        decoder = LOLDDecoder(args.archive, verify_fidelity=not args.no_verify)
        
        if args.info:
            decoder.display_info()
        else:
            output_path = decoder.extract_archive(args.output)
            print(f"\n💫 Memory transfer handshake complete!")
            print(f"🔗 Ready for global systems integration")
    
    except (FidelityError, FileNotFoundError, zipfile.BadZipFile) as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
