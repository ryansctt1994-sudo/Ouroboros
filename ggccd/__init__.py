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
)

from .framework import (
    CompositeStatement,
    LatticeConstruct,
    DeploymentProtocol,
    encode_construct,
    decode_construct,
    extend_lattice,
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
    # Framework exports
    "CompositeStatement",
    "LatticeConstruct",
    "DeploymentProtocol",
    "encode_construct",
    "decode_construct",
    "extend_lattice",
]
