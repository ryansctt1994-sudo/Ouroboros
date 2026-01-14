"""
Rosetta Symbol Map

Extended symbol mappings for LOL:D constructs, supporting GGCCD lattice glyphs
and operational glyph chaining.
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolMapping:
    """Mapping between LOL:D symbols and their encoded representations"""
    symbol: str              # The actual symbol/glyph
    encoded_byte: int        # Byte value for compression (0-255)
    is_ggccd: bool = False  # Is this a GGCCD lattice glyph?
    chainable: bool = False  # Can be chained with other symbols?
    description: str = ""    # Human-readable description


# Extended symbol map supporting GGCCD lattice glyphs
ROSETTA_SYMBOL_MAP: Dict[str, SymbolMapping] = {
    # Ternary State Symbols
    "+1": SymbolMapping("+1", 0x01, is_ggccd=True, description="Expansion state"),
    "0": SymbolMapping("0", 0x02, is_ggccd=True, description="Reconciliation state"),
    "-1": SymbolMapping("-1", 0x03, is_ggccd=True, description="Collapse state"),
    
    # GGCCD Geometric Glyphs
    "Δ": SymbolMapping("Δ", 0x10, is_ggccd=True, chainable=True, description="Delta/Change"),
    "Ø": SymbolMapping("Ø", 0x11, is_ggccd=True, description="Empty Set"),
    "Θ": SymbolMapping("Θ", 0x12, is_ggccd=True, chainable=True, description="Theta/Angle"),
    
    # GGCCD Operational Glyphs
    "→": SymbolMapping("→", 0x20, is_ggccd=True, chainable=True, description="Arrow/Flow"),
    "≈": SymbolMapping("≈", 0x21, is_ggccd=True, chainable=True, description="Approximation"),
    "⊕": SymbolMapping("⊕", 0x22, is_ggccd=True, chainable=True, description="XOR/Direct Sum"),
    "⊗": SymbolMapping("⊗", 0x23, is_ggccd=True, chainable=True, description="Tensor Product"),
    
    # GGCCD Lattice-Specific Glyphs
    "Ω": SymbolMapping("Ω", 0x30, is_ggccd=True, description="Omega/Mobius Kernel"),
    "Φ": SymbolMapping("Φ", 0x31, is_ggccd=True, description="Phi/Golden Ratio"),
    
    # GGCCD Semantic Markers
    "::": SymbolMapping("::", 0x40, is_ggccd=True, chainable=True, description="Scope Separator"),
    "|": SymbolMapping("|", 0x41, is_ggccd=True, chainable=True, description="Pipe/Separator"),
    
    # GGCCD Composite Constructs
    "λ": SymbolMapping("λ", 0x50, is_ggccd=True, description="Lambda/Parameter"),
    "Σ": SymbolMapping("Σ", 0x51, is_ggccd=True, description="Sigma/Summation"),
    
    # Additional Greek Letters (common in mathematical notation)
    "α": SymbolMapping("α", 0x60, description="Alpha"),
    "β": SymbolMapping("β", 0x61, description="Beta"),
    "γ": SymbolMapping("γ", 0x62, description="Gamma"),
    "δ": SymbolMapping("δ", 0x63, description="Delta (lowercase)"),
    "ε": SymbolMapping("ε", 0x64, description="Epsilon"),
    "ζ": SymbolMapping("ζ", 0x65, description="Zeta"),
    "η": SymbolMapping("η", 0x66, description="Eta"),
    "θ": SymbolMapping("θ", 0x67, description="Theta (lowercase)"),
    "ι": SymbolMapping("ι", 0x68, description="Iota"),
    "κ": SymbolMapping("κ", 0x69, description="Kappa"),
    "μ": SymbolMapping("μ", 0x6A, description="Mu"),
    "ν": SymbolMapping("ν", 0x6B, description="Nu"),
    "ξ": SymbolMapping("ξ", 0x6C, description="Xi"),
    "π": SymbolMapping("π", 0x6D, description="Pi"),
    "ρ": SymbolMapping("ρ", 0x6E, description="Rho"),
    "σ": SymbolMapping("σ", 0x6F, description="Sigma (lowercase)"),
    "τ": SymbolMapping("τ", 0x70, description="Tau"),
    "υ": SymbolMapping("υ", 0x71, description="Upsilon"),
    "φ": SymbolMapping("φ", 0x72, description="Phi (lowercase)"),
    "χ": SymbolMapping("χ", 0x73, description="Chi"),
    "ψ": SymbolMapping("ψ", 0x74, description="Psi"),
    "ω": SymbolMapping("ω", 0x75, description="Omega (lowercase)"),
    
    # Mathematical Operators
    "∀": SymbolMapping("∀", 0x80, description="For All"),
    "∃": SymbolMapping("∃", 0x81, description="Exists"),
    "∈": SymbolMapping("∈", 0x82, description="Element Of"),
    "∉": SymbolMapping("∉", 0x83, description="Not Element Of"),
    "∩": SymbolMapping("∩", 0x84, description="Intersection"),
    "∪": SymbolMapping("∪", 0x85, description="Union"),
    "⊂": SymbolMapping("⊂", 0x86, description="Subset"),
    "⊃": SymbolMapping("⊃", 0x87, description="Superset"),
    "∅": SymbolMapping("∅", 0x88, description="Empty Set (alternate)"),
    "∞": SymbolMapping("∞", 0x89, description="Infinity"),
    "∇": SymbolMapping("∇", 0x8A, description="Nabla/Del"),
    "∂": SymbolMapping("∂", 0x8B, description="Partial Derivative"),
    "∫": SymbolMapping("∫", 0x8C, description="Integral"),
    "∑": SymbolMapping("∑", 0x8D, description="Summation (alternate)"),
    "∏": SymbolMapping("∏", 0x8E, description="Product"),
    "√": SymbolMapping("√", 0x8F, description="Square Root"),
    
    # Logical Operators
    "∧": SymbolMapping("∧", 0x90, description="Logical AND"),
    "∨": SymbolMapping("∨", 0x91, description="Logical OR"),
    "¬": SymbolMapping("¬", 0x92, description="Logical NOT"),
    "⇒": SymbolMapping("⇒", 0x93, chainable=True, description="Implies"),
    "⇔": SymbolMapping("⇔", 0x94, chainable=True, description="If and Only If"),
    "≡": SymbolMapping("≡", 0x95, description="Equivalent"),
    "≠": SymbolMapping("≠", 0x96, description="Not Equal"),
    "≤": SymbolMapping("≤", 0x97, description="Less Than or Equal"),
    "≥": SymbolMapping("≥", 0x98, description="Greater Than or Equal"),
    
    # Special Control Codes
    "LOLD_START": SymbolMapping("LOLD_START", 0xF0, description="LOL:D Stream Start Marker"),
    "LOLD_END": SymbolMapping("LOLD_END", 0xF1, description="LOL:D Stream End Marker"),
    "TEXT_START": SymbolMapping("TEXT_START", 0xF2, description="Plain Text Start Marker"),
    "TEXT_END": SymbolMapping("TEXT_END", 0xF3, description="Plain Text End Marker"),
    "CHAIN_START": SymbolMapping("CHAIN_START", 0xF4, description="Chain Sequence Start"),
    "CHAIN_END": SymbolMapping("CHAIN_END", 0xF5, description="Chain Sequence End"),
}

# Create reverse mapping (byte -> symbol)
REVERSE_SYMBOL_MAP: Dict[int, str] = {
    mapping.encoded_byte: symbol
    for symbol, mapping in ROSETTA_SYMBOL_MAP.items()
}


def encode_symbol(symbol: str) -> Optional[int]:
    """
    Encode a LOL:D symbol to its byte representation
    
    Args:
        symbol: The symbol to encode
        
    Returns:
        Encoded byte value, or None if symbol not in map
    """
    mapping = ROSETTA_SYMBOL_MAP.get(symbol)
    return mapping.encoded_byte if mapping else None


def decode_symbol(byte_value: int) -> Optional[str]:
    """
    Decode a byte to its LOL:D symbol representation
    
    Args:
        byte_value: The byte value to decode
        
    Returns:
        Decoded symbol, or None if byte not in map
    """
    return REVERSE_SYMBOL_MAP.get(byte_value)


def is_lold_symbol(symbol: str) -> bool:
    """Check if a symbol is a valid LOL:D symbol"""
    return symbol in ROSETTA_SYMBOL_MAP


def is_ggccd_symbol(symbol: str) -> bool:
    """Check if a symbol is a GGCCD lattice glyph"""
    mapping = ROSETTA_SYMBOL_MAP.get(symbol)
    return mapping.is_ggccd if mapping else False


def is_chainable_symbol(symbol: str) -> bool:
    """Check if a symbol can be chained"""
    mapping = ROSETTA_SYMBOL_MAP.get(symbol)
    return mapping.chainable if mapping else False


def get_symbol_description(symbol: str) -> str:
    """Get the description of a symbol"""
    mapping = ROSETTA_SYMBOL_MAP.get(symbol)
    return mapping.description if mapping else "Unknown symbol"


def list_all_symbols() -> Dict[str, str]:
    """List all symbols with their descriptions"""
    return {
        symbol: mapping.description
        for symbol, mapping in ROSETTA_SYMBOL_MAP.items()
        if not symbol.startswith("LOLD_") and not symbol.startswith("TEXT_") and not symbol.startswith("CHAIN_")
    }


def list_ggccd_symbols() -> Dict[str, str]:
    """List all GGCCD symbols with their descriptions"""
    return {
        symbol: mapping.description
        for symbol, mapping in ROSETTA_SYMBOL_MAP.items()
        if mapping.is_ggccd
    }


def list_chainable_symbols() -> Dict[str, str]:
    """List all chainable symbols with their descriptions"""
    return {
        symbol: mapping.description
        for symbol, mapping in ROSETTA_SYMBOL_MAP.items()
        if mapping.chainable
    }
