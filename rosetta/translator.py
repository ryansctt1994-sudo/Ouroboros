"""
Rosetta Translator - High-Level API

Complete reversible compression/decompression utility for LOL:D symbolic-text constructs.
"""

from typing import Tuple
from .encoder import LoldEncoder, LoldDecoder, CompressedLoldStream
from .symbol_map import is_lold_symbol


class RosettaTranslator:
    """
    High-level interface for LOL:D compression/decompression
    
    Usage:
        translator = RosettaTranslator()
        compressed = translator.compress("Δ(V_exp, V_obs) → +1 :: validated")
        original = translator.decompress(compressed)
    """
    
    def __init__(self, compression_level: int = 6):
        """
        Initialize the translator
        
        Args:
            compression_level: Zlib compression level (0-9, default 6)
        """
        self.compression_level = compression_level
    
    def compress(self, lold_construct: str) -> CompressedLoldStream:
        """
        Compress a LOL:D construct string
        
        Args:
            lold_construct: LOL:D construct string to compress
            
        Returns:
            CompressedLoldStream with compressed data
        """
        encoder = LoldEncoder(compression_level=self.compression_level)
        encoder.encode_construct(lold_construct)
        return encoder.compress()
    
    def decompress(self, stream: CompressedLoldStream) -> str:
        """
        Decompress a LOL:D compressed stream
        
        Args:
            stream: CompressedLoldStream to decompress
            
        Returns:
            Decompressed LOL:D construct string
        """
        decoder = LoldDecoder()
        decoder.decompress(stream)
        return decoder.decode_construct()
    
    def compress_to_file(self, lold_construct: str, filename: str) -> None:
        """
        Compress a LOL:D construct and save to file
        
        Args:
            lold_construct: LOL:D construct string to compress
            filename: Output filename (typically .lold.zip)
        """
        stream = self.compress(lold_construct)
        with open(filename, 'wb') as f:
            f.write(stream.to_bytes())
    
    def decompress_from_file(self, filename: str) -> str:
        """
        Decompress a LOL:D construct from file
        
        Args:
            filename: Input filename (.lold.zip)
            
        Returns:
            Decompressed LOL:D construct string
        """
        with open(filename, 'rb') as f:
            data = f.read()
        stream = CompressedLoldStream.from_bytes(data)
        return self.decompress(stream)


def compress_lold(lold_construct: str, compression_level: int = 6) -> CompressedLoldStream:
    """
    Convenience function to compress a LOL:D construct
    
    Args:
        lold_construct: LOL:D construct string to compress
        compression_level: Zlib compression level (0-9, default 6)
        
    Returns:
        CompressedLoldStream with compressed data
    """
    translator = RosettaTranslator(compression_level=compression_level)
    return translator.compress(lold_construct)


def decompress_lold(stream: CompressedLoldStream) -> str:
    """
    Convenience function to decompress a LOL:D stream
    
    Args:
        stream: CompressedLoldStream to decompress
        
    Returns:
        Decompressed LOL:D construct string
    """
    translator = RosettaTranslator()
    return translator.decompress(stream)


def validate_roundtrip(lold_construct: str, compression_level: int = 6) -> Tuple[bool, str, float]:
    """
    Validate that compression/decompression is lossless
    
    Args:
        lold_construct: LOL:D construct string to test
        compression_level: Zlib compression level (0-9, default 6)
        
    Returns:
        Tuple of (success, message, compression_ratio)
    """
    try:
        translator = RosettaTranslator(compression_level=compression_level)
        
        # Compress
        compressed = translator.compress(lold_construct)
        
        # Decompress
        decompressed = translator.decompress(compressed)
        
        # Compare
        if lold_construct == decompressed:
            return (
                True,
                f"Roundtrip successful. Compression ratio: {compressed.compression_ratio():.2%}",
                compressed.compression_ratio()
            )
        else:
            return (
                False,
                f"Roundtrip failed. Original != Decompressed",
                compressed.compression_ratio()
            )
    
    except Exception as e:
        return (False, f"Error during roundtrip: {str(e)}", 0.0)


def save_lold_zip(lold_construct: str, filename: str, compression_level: int = 6) -> CompressedLoldStream:
    """
    Compress and save LOL:D construct to .lold.zip file
    
    Args:
        lold_construct: LOL:D construct string to compress
        filename: Output filename (will append .lold.zip if not present)
        compression_level: Zlib compression level (0-9, default 6)
        
    Returns:
        CompressedLoldStream that was saved
    """
    # Ensure filename has proper extension
    if not filename.endswith('.lold.zip'):
        if not filename.endswith('.lold'):
            filename += '.lold'
        filename += '.zip'
    
    translator = RosettaTranslator(compression_level=compression_level)
    translator.compress_to_file(lold_construct, filename)
    
    # Return the stream for metadata
    return translator.compress(lold_construct)


def load_lold_zip(filename: str) -> str:
    """
    Load and decompress LOL:D construct from .lold.zip file
    
    Args:
        filename: Input filename (.lold.zip)
        
    Returns:
        Decompressed LOL:D construct string
    """
    translator = RosettaTranslator()
    return translator.decompress_from_file(filename)
