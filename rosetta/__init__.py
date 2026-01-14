"""
Rosetta Translator Prototype

Complete reversible compression/decompression utility for LOL:D symbolic-text constructs.
Provides lossless text preservation through direct encoding into the compressed stream.
"""

from .translator import (
    RosettaTranslator,
    compress_lold,
    decompress_lold,
    validate_roundtrip,
    save_lold_zip,
    load_lold_zip,
)

from .symbol_map import (
    ROSETTA_SYMBOL_MAP,
    encode_symbol,
    decode_symbol,
    is_lold_symbol,
    list_all_symbols,
    list_ggccd_symbols,
    list_chainable_symbols,
)

from .encoder import (
    LoldEncoder,
    LoldDecoder,
    CompressedLoldStream,
)

__version__ = "1.0.0"

__all__ = [
    # Translator exports
    "RosettaTranslator",
    "compress_lold",
    "decompress_lold",
    "validate_roundtrip",
    "save_lold_zip",
    "load_lold_zip",
    # Symbol map exports
    "ROSETTA_SYMBOL_MAP",
    "encode_symbol",
    "decode_symbol",
    "is_lold_symbol",
    "list_all_symbols",
    "list_ggccd_symbols",
    "list_chainable_symbols",
    # Encoder exports
    "LoldEncoder",
    "LoldDecoder",
    "CompressedLoldStream",
]
