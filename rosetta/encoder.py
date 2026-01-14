"""
Rosetta LOL:D Encoder/Decoder

Zlib-based compact encoding for large-scale LOL:D constructs while maintaining
relational integrity for traversal. Provides lossless text preservation.
"""

import zlib
import struct
from typing import List, Tuple, Optional
from dataclasses import dataclass
from .symbol_map import encode_symbol, decode_symbol, ROSETTA_SYMBOL_MAP


@dataclass
class CompressedLoldStream:
    """A compressed LOL:D stream with metadata"""
    compressed_data: bytes        # The compressed byte stream
    original_size: int           # Size before compression
    compressed_size: int         # Size after compression
    version: int = 1            # Encoder version
    checksum: int = 0           # CRC32 checksum
    
    def compression_ratio(self) -> float:
        """Calculate compression ratio"""
        if self.original_size == 0:
            return 0.0
        return self.compressed_size / self.original_size
    
    def to_bytes(self) -> bytes:
        """Serialize the compressed stream to bytes"""
        # Header format: 4 bytes magic, 2 bytes version, 4 bytes original size,
        # 4 bytes compressed size, 4 bytes checksum
        magic = b'LOLD'
        header = struct.pack(
            '>4sHIII',  # Big-endian: magic(4), version(2), orig_size(4), comp_size(4), checksum(4)
            magic,
            self.version,
            self.original_size,
            self.compressed_size,
            self.checksum
        )
        return header + self.compressed_data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'CompressedLoldStream':
        """Deserialize a compressed stream from bytes"""
        if len(data) < 18:  # Minimum header size
            raise ValueError("Invalid compressed stream: too short")
        
        # Unpack header
        magic, version, original_size, compressed_size, checksum = struct.unpack(
            '>4sHIII',
            data[:18]
        )
        
        if magic != b'LOLD':
            raise ValueError(f"Invalid magic number: {magic}")
        
        compressed_data = data[18:]
        
        if len(compressed_data) != compressed_size:
            raise ValueError(
                f"Compressed data size mismatch: expected {compressed_size}, "
                f"got {len(compressed_data)}"
            )
        
        return cls(
            compressed_data=compressed_data,
            original_size=original_size,
            compressed_size=compressed_size,
            version=version,
            checksum=checksum
        )


class LoldEncoder:
    """
    Encoder for LOL:D symbolic-text constructs
    
    Supports:
    - Symbol encoding using the Rosetta symbol map
    - Plain text preservation (lossless)
    - Symbol chaining
    - Zlib compression
    """
    
    def __init__(self, compression_level: int = 6):
        """
        Initialize the encoder
        
        Args:
            compression_level: Zlib compression level (0-9, default 6)
        """
        self.compression_level = max(0, min(9, compression_level))
        self.buffer: List[int] = []
    
    def encode_symbol(self, symbol: str) -> None:
        """Encode a single LOL:D symbol to the buffer"""
        byte_val = encode_symbol(symbol)
        if byte_val is None:
            raise ValueError(f"Unknown symbol: {symbol}")
        self.buffer.append(byte_val)
    
    def encode_text(self, text: str) -> None:
        """
        Encode plain text (lossless preservation)
        
        Format: TEXT_START + length(4 bytes) + UTF-8 text + TEXT_END
        """
        text_bytes = text.encode('utf-8')
        text_len = len(text_bytes)
        
        # Add TEXT_START marker
        self.encode_symbol("TEXT_START")
        
        # Add length (4 bytes, big-endian)
        self.buffer.extend(struct.pack('>I', text_len))
        
        # Add UTF-8 encoded text
        self.buffer.extend(text_bytes)
        
        # Add TEXT_END marker
        self.encode_symbol("TEXT_END")
    
    def encode_chain(self, symbols: List[str]) -> None:
        """
        Encode a chain of symbols
        
        Format: CHAIN_START + symbols + CHAIN_END
        """
        self.encode_symbol("CHAIN_START")
        for symbol in symbols:
            self.encode_symbol(symbol)
        self.encode_symbol("CHAIN_END")
    
    def encode_construct(self, construct_string: str) -> None:
        """
        Encode a GGCCD construct string
        
        Parses the string and encodes symbols and text appropriately
        """
        # Add LOLD_START marker
        self.encode_symbol("LOLD_START")
        
        # Parse and encode the construct
        i = 0
        current_text = ""
        
        while i < len(construct_string):
            # Check for multi-character symbols
            found_symbol = False
            
            # Try two-character symbols first
            if i + 1 < len(construct_string):
                two_char = construct_string[i:i+2]
                if two_char in ROSETTA_SYMBOL_MAP:
                    # Flush any accumulated text
                    if current_text:
                        self.encode_text(current_text)
                        current_text = ""
                    self.encode_symbol(two_char)
                    i += 2
                    found_symbol = True
            
            # Try single-character symbols
            if not found_symbol:
                single_char = construct_string[i]
                if single_char in ROSETTA_SYMBOL_MAP:
                    # Flush any accumulated text
                    if current_text:
                        self.encode_text(current_text)
                        current_text = ""
                    self.encode_symbol(single_char)
                    i += 1
                    found_symbol = True
            
            # If not a symbol, accumulate as text
            if not found_symbol:
                current_text += construct_string[i]
                i += 1
        
        # Flush any remaining text
        if current_text:
            self.encode_text(current_text)
        
        # Add LOLD_END marker
        self.encode_symbol("LOLD_END")
    
    def compress(self) -> CompressedLoldStream:
        """
        Compress the encoded buffer
        
        Returns:
            CompressedLoldStream with compressed data and metadata
        """
        # Convert buffer to bytes
        original_bytes = bytes(self.buffer)
        original_size = len(original_bytes)
        
        # Compress with zlib
        compressed_data = zlib.compress(original_bytes, level=self.compression_level)
        compressed_size = len(compressed_data)
        
        # Calculate checksum
        checksum = zlib.crc32(original_bytes)
        
        return CompressedLoldStream(
            compressed_data=compressed_data,
            original_size=original_size,
            compressed_size=compressed_size,
            checksum=checksum
        )
    
    def reset(self) -> None:
        """Reset the encoder buffer"""
        self.buffer.clear()


class LoldDecoder:
    """
    Decoder for LOL:D symbolic-text constructs
    
    Supports:
    - Symbol decoding using the Rosetta symbol map
    - Plain text restoration (lossless)
    - Symbol chain parsing
    - Zlib decompression
    """
    
    def __init__(self):
        """Initialize the decoder"""
        self.buffer: List[int] = []
        self.position: int = 0
    
    def decompress(self, stream: CompressedLoldStream) -> None:
        """
        Decompress a LOL:D stream
        
        Args:
            stream: CompressedLoldStream to decompress
        """
        # Decompress the data
        decompressed_bytes = zlib.decompress(stream.compressed_data)
        
        # Verify size
        if len(decompressed_bytes) != stream.original_size:
            raise ValueError(
                f"Decompressed size mismatch: expected {stream.original_size}, "
                f"got {len(decompressed_bytes)}"
            )
        
        # Verify checksum
        checksum = zlib.crc32(decompressed_bytes)
        if checksum != stream.checksum:
            raise ValueError(
                f"Checksum mismatch: expected {stream.checksum}, got {checksum}"
            )
        
        # Load into buffer
        self.buffer = list(decompressed_bytes)
        self.position = 0
    
    def read_byte(self) -> Optional[int]:
        """Read the next byte from the buffer"""
        if self.position >= len(self.buffer):
            return None
        byte = self.buffer[self.position]
        self.position += 1
        return byte
    
    def read_bytes(self, count: int) -> Optional[bytes]:
        """Read multiple bytes from the buffer"""
        if self.position + count > len(self.buffer):
            return None
        data = bytes(self.buffer[self.position:self.position + count])
        self.position += count
        return data
    
    def decode_symbol(self) -> Optional[str]:
        """Decode the next symbol from the buffer"""
        byte_val = self.read_byte()
        if byte_val is None:
            return None
        return decode_symbol(byte_val)
    
    def decode_text(self) -> Optional[str]:
        """
        Decode plain text segment
        
        Expected format: TEXT_START already read, now: length(4) + UTF-8 text + TEXT_END
        """
        # Read length (4 bytes, big-endian)
        len_bytes = self.read_bytes(4)
        if len_bytes is None:
            raise ValueError("Unexpected end of stream while reading text length")
        
        text_len = struct.unpack('>I', len_bytes)[0]
        
        # Read UTF-8 text
        text_bytes = self.read_bytes(text_len)
        if text_bytes is None:
            raise ValueError("Unexpected end of stream while reading text")
        
        text = text_bytes.decode('utf-8')
        
        # Read TEXT_END marker
        end_marker = self.decode_symbol()
        if end_marker != "TEXT_END":
            raise ValueError(f"Expected TEXT_END, got {end_marker}")
        
        return text
    
    def decode_chain(self) -> List[str]:
        """
        Decode a symbol chain
        
        Expected format: CHAIN_START already read, now: symbols + CHAIN_END
        """
        symbols = []
        while True:
            symbol = self.decode_symbol()
            if symbol is None:
                raise ValueError("Unexpected end of stream in chain")
            if symbol == "CHAIN_END":
                break
            symbols.append(symbol)
        return symbols
    
    def decode_construct(self) -> str:
        """
        Decode a complete GGCCD construct
        
        Returns:
            Reconstructed construct string
        """
        result_parts = []
        
        # Expect LOLD_START marker
        start_marker = self.decode_symbol()
        if start_marker != "LOLD_START":
            raise ValueError(f"Expected LOLD_START, got {start_marker}")
        
        # Decode until LOLD_END
        while True:
            symbol = self.decode_symbol()
            
            if symbol is None:
                raise ValueError("Unexpected end of stream")
            
            if symbol == "LOLD_END":
                break
            
            elif symbol == "TEXT_START":
                text = self.decode_text()
                result_parts.append(text)
            
            elif symbol == "CHAIN_START":
                chain = self.decode_chain()
                result_parts.append(" ".join(chain))
            
            else:
                # Regular symbol
                result_parts.append(symbol)
        
        return "".join(result_parts)
    
    def reset(self) -> None:
        """Reset the decoder"""
        self.buffer.clear()
        self.position = 0
