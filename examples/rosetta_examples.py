"""
Example Usage: Rosetta Translator

This script demonstrates how to use the Rosetta Translator for compressing
and decompressing LOL:D (Language of Lattice: Dimensional) symbolic-text constructs.
"""

from rosetta import (
    RosettaTranslator,
    compress_lold, decompress_lold,
    validate_roundtrip,
    save_lold_zip, load_lold_zip,
    ROSETTA_SYMBOL_MAP,
    list_all_symbols, list_ggccd_symbols, list_chainable_symbols
)


def example_1_basic_compression():
    """Example 1: Basic compression and decompression"""
    print("=" * 70)
    print("Example 1: Basic Compression/Decompression")
    print("=" * 70)
    
    # Create a LOL:D construct
    lold_construct = "Δ(V_exp, V_obs) → +1 :: validated_state"
    
    print(f"\nOriginal LOL:D construct:")
    print(f"  '{lold_construct}'")
    print(f"  Length: {len(lold_construct)} characters")
    
    # Compress
    translator = RosettaTranslator(compression_level=6)
    compressed = translator.compress(lold_construct)
    
    print(f"\nCompressed stream:")
    print(f"  Original size: {compressed.original_size} bytes")
    print(f"  Compressed size: {compressed.compressed_size} bytes")
    print(f"  Compression ratio: {compressed.compression_ratio():.2%}")
    print(f"  Checksum: {compressed.checksum}")
    
    # Decompress
    decompressed = translator.decompress(compressed)
    
    print(f"\nDecompressed LOL:D construct:")
    print(f"  '{decompressed}'")
    print(f"  Match: {lold_construct == decompressed}")


def example_2_ternary_states():
    """Example 2: Compressing ternary state transitions"""
    print("\n\n" + "=" * 70)
    print("Example 2: Ternary State Transitions")
    print("=" * 70)
    
    # LOL:D construct with ternary state transitions
    lold_construct = "+1 → 0 → -1 :: ternary_cycle | expansion to collapse"
    
    print(f"\nLOL:D construct: '{lold_construct}'")
    
    # Compress with high compression
    compressed = compress_lold(lold_construct, compression_level=9)
    
    print(f"Compressed: {compressed.compressed_size} bytes")
    print(f"Compression ratio: {compressed.compression_ratio():.2%}")
    
    # Decompress
    decompressed = decompress_lold(compressed)
    print(f"Decompressed: '{decompressed}'")
    print(f"Lossless: {lold_construct == decompressed}")


def example_3_complex_lattice():
    """Example 3: Complex lattice construct with chaining"""
    print("\n\n" + "=" * 70)
    print("Example 3: Complex Lattice Construct")
    print("=" * 70)
    
    # Complex LOL:D construct with multiple symbols and operators
    lold_construct = (
        "Δ → Θ(π/2) ≈ Φ :: golden_angle | "
        "+1 ⊗ -1 → 0 :: tensor_reconciliation | "
        "Ω(n=5) ⊕ Σ :: mobius_summation"
    )
    
    print(f"\nComplex LOL:D construct:")
    print(f"  '{lold_construct}'")
    print(f"  Length: {len(lold_construct)} characters")
    
    # Compress
    compressed = compress_lold(lold_construct, compression_level=6)
    
    print(f"\nCompression results:")
    print(f"  Original: {compressed.original_size} bytes")
    print(f"  Compressed: {compressed.compressed_size} bytes")
    print(f"  Ratio: {compressed.compression_ratio():.2%}")
    print(f"  Savings: {compressed.original_size - compressed.compressed_size} bytes")
    
    # Validate roundtrip
    success, message, ratio = validate_roundtrip(lold_construct)
    print(f"\nRoundtrip validation: {message}")


def example_4_file_operations():
    """Example 4: Save and load from file"""
    print("\n\n" + "=" * 70)
    print("Example 4: File Operations (.lold.zip)")
    print("=" * 70)
    
    # Create a LOL:D construct
    lold_construct = (
        "State transition lattice: "
        "+1 → 0 :: escalation | "
        "0 → -1 :: collapse | "
        "-1 → +1 :: reversal (forbidden without 0)"
    )
    
    print(f"\nLOL:D construct to save:")
    print(f"  '{lold_construct}'")
    
    # Save to file
    filename = "/tmp/test_lattice.lold.zip"
    compressed = save_lold_zip(lold_construct, filename, compression_level=6)
    
    print(f"\nSaved to: {filename}")
    print(f"  Compressed size: {compressed.compressed_size} bytes")
    print(f"  Compression ratio: {compressed.compression_ratio():.2%}")
    
    # Load from file
    loaded = load_lold_zip(filename)
    
    print(f"\nLoaded from file:")
    print(f"  '{loaded}'")
    print(f"  Match: {lold_construct == loaded}")


def example_5_symbol_mapping():
    """Example 5: Exploring symbol mappings"""
    print("\n\n" + "=" * 70)
    print("Example 5: Symbol Mappings")
    print("=" * 70)
    
    # List all symbols
    print("\nAll LOL:D Symbols:")
    all_symbols = list_all_symbols()
    for symbol, desc in list(all_symbols.items())[:10]:  # Show first 10
        print(f"  {symbol:4s} -> {desc}")
    print(f"  ... and {len(all_symbols) - 10} more")
    
    # List GGCCD symbols
    print("\n\nGGCCD Lattice Symbols:")
    ggccd_symbols = list_ggccd_symbols()
    for symbol, desc in ggccd_symbols.items():
        print(f"  {symbol:4s} -> {desc}")
    
    # List chainable symbols
    print("\n\nChainable Symbols (for operations):")
    chainable = list_chainable_symbols()
    for symbol, desc in chainable.items():
        print(f"  {symbol:4s} -> {desc}")


def example_6_compression_levels():
    """Example 6: Comparing compression levels"""
    print("\n\n" + "=" * 70)
    print("Example 6: Compression Level Comparison")
    print("=" * 70)
    
    # Create a larger LOL:D construct for better compression
    lold_construct = (
        "Multi-dimensional lattice construct: " * 5 +
        "Δ → Θ → Φ :: geodesic_flow | " * 10 +
        "+1 ⊗ -1 → 0 :: ternary_reconciliation | " * 10
    )
    
    print(f"\nOriginal size: {len(lold_construct)} characters")
    print("\nCompression level comparison:")
    
    for level in [0, 3, 6, 9]:
        compressed = compress_lold(lold_construct, compression_level=level)
        print(f"  Level {level}: {compressed.compressed_size:5d} bytes "
              f"({compressed.compression_ratio():.2%})")


def example_7_mixed_content():
    """Example 7: Mixed symbolic and text content"""
    print("\n\n" + "=" * 70)
    print("Example 7: Mixed Symbolic and Text Content")
    print("=" * 70)
    
    # LOL:D construct with both symbols and explanatory text
    lold_construct = (
        "This is a ternary state transition: +1 → 0 → -1 which represents "
        "the complete cycle from expansion through reconciliation to collapse. "
        "The delta operator Δ measures the difference between expected and observed "
        "states, with approximate equality ≈ used for fuzzy matching within tolerance."
    )
    
    print(f"\nMixed content LOL:D construct:")
    print(f"  Length: {len(lold_construct)} characters")
    
    # Compress
    compressed = compress_lold(lold_construct, compression_level=6)
    
    print(f"\nCompression results:")
    print(f"  Compressed: {compressed.compressed_size} bytes")
    print(f"  Ratio: {compressed.compression_ratio():.2%}")
    
    # Validate roundtrip (critical for mixed content)
    success, message, ratio = validate_roundtrip(lold_construct)
    print(f"\nRoundtrip validation: {message}")
    
    if success:
        print("\n✓ Lossless preservation confirmed for mixed content!")


def example_8_serialization():
    """Example 8: Serializing compressed streams"""
    print("\n\n" + "=" * 70)
    print("Example 8: Compressed Stream Serialization")
    print("=" * 70)
    
    # Create and compress a LOL:D construct
    lold_construct = "Ω(717) :: sacred_constant | Φ(1.618) :: golden_ratio"
    
    print(f"\nLOL:D construct: '{lold_construct}'")
    
    # Compress
    compressed = compress_lold(lold_construct)
    
    # Serialize to bytes
    serialized = compressed.to_bytes()
    print(f"\nSerialized to {len(serialized)} bytes")
    print(f"  Header: LOLD magic + metadata (18 bytes)")
    print(f"  Data: {len(serialized) - 18} bytes")
    
    # Deserialize
    from rosetta.encoder import CompressedLoldStream
    deserialized = CompressedLoldStream.from_bytes(serialized)
    
    print(f"\nDeserialized stream:")
    print(f"  Version: {deserialized.version}")
    print(f"  Original size: {deserialized.original_size}")
    print(f"  Compressed size: {deserialized.compressed_size}")
    print(f"  Checksum: {deserialized.checksum}")
    
    # Decompress and verify
    decompressed = decompress_lold(deserialized)
    print(f"\n✓ Serialization roundtrip: {lold_construct == decompressed}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("Rosetta Translator Examples")
    print("=" * 70)
    
    example_1_basic_compression()
    example_2_ternary_states()
    example_3_complex_lattice()
    example_4_file_operations()
    example_5_symbol_mapping()
    example_6_compression_levels()
    example_7_mixed_content()
    example_8_serialization()
    
    print("\n\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70 + "\n")
