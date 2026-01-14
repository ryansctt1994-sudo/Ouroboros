"""
GGCCD (Global Geometric Construct Compression Dictionary) Framework

A holistic lexicon system for encoding multi-dimensional states using symbols,
glyphs, and immutable "True Text" explanations organized into lattice constructs.
"""

from .lexicon import (
    Symbol,
    Glyph,
    TrueText,
    GGCCD_LEXICON,
    get_symbol,
    get_glyph,
    validate_symbol,
    list_all_symbols,
)

from .framework import (
    CompositeStatement,
    LatticeConstruct,
    LatticeNode,
    DeploymentProtocol,
    ConstructType,
    encode_construct,
    decode_construct,
    extend_lattice,
    create_ternary_lattice,
    apply_operation_chain,
)

__version__ = "1.0.0"

__all__ = [
    # Lexicon exports
    "Symbol",
    "Glyph",
    "TrueText",
    "GGCCD_LEXICON",
    "get_symbol",
    "get_glyph",
    "validate_symbol",
    "list_all_symbols",
    # Framework exports
    "CompositeStatement",
    "LatticeConstruct",
    "LatticeNode",
    "DeploymentProtocol",
    "ConstructType",
    "encode_construct",
    "decode_construct",
    "extend_lattice",
    "create_ternary_lattice",
    "apply_operation_chain",
]
