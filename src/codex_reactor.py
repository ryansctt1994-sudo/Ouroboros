"""Codex Reactor Framework - Production-Ready Governance and Trust Architecture.

This module implements the Codex Reactor framework, which provides:

1. **Key**: Authorship operators for authorship provenance and trust
2. **GlyphEngine**: Compression and diagnostic system for structured event representation
3. **Tablet (WORM Ledger)**: Append-only, auditable ledger system storing signed manifests
4. **RootNetwork**: Propagation of consequences and downstream effects simulation
5. **CodexReactor**: Orchestrating events through ignition, inscription, and consequence mapping

The framework integrates post-quantum cryptography (CRYSTALS-Dilithium-5) via the
SovereignSigner for cryptographic integrity of all written manifests.
"""

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum

# Import security module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from security.dilithium_signer import SovereignSigner, SignatureResult


# Constants
PHI = 1.618033988749895  # Golden ratio
ZOREL_CONSTANT = 717  # Project signature number


class EventType(Enum):
    """Types of events in the Codex Reactor."""
    IGNITION = "ignition"
    INSCRIPTION = "inscription"
    CONSEQUENCE = "consequence"
    AUDIT = "audit"


@dataclass
class Author:
    """Represents an author with cryptographic identity."""
    name: str
    key_id: str  # Derived from public key
    public_key: str
    
    def __hash__(self):
        return hash(self.key_id)


@dataclass
class Event:
    """Represents an event in the Codex Reactor system."""
    event_type: EventType
    author: Author
    payload: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    event_id: Optional[str] = None
    
    def __post_init__(self):
        if self.event_id is None:
            # Generate deterministic event ID
            content = f"{self.event_type.value}:{self.author.key_id}:{self.timestamp}"
            self.event_id = hashlib.sha256(content.encode()).hexdigest()[:16]


class Key:
    """Authorship operator for authorship provenance and trust.
    
    The Key manages cryptographic identity and provides the turn() mechanism
    for rotating authorship context while maintaining chain-of-trust.
    
    Attributes:
        author: The current author
        signer: The cryptographic signer
        turn_count: Number of turns (rotations) performed
    """
    
    def __init__(self, author_name: str, signer: Optional[SovereignSigner] = None):
        """Initialize a Key with author identity.
        
        Args:
            author_name: Name of the author
            signer: Optional SovereignSigner instance (creates new if not provided)
        """
        self.signer = signer if signer is not None else SovereignSigner()
        self.turn_count = 0
        
        # Create author from signer
        public_key = self.signer.export_public_key()
        key_id = hashlib.sha256(public_key.encode()).hexdigest()[:16]
        self.author = Author(
            name=author_name,
            key_id=key_id,
            public_key=public_key
        )
    
    def turn(self, new_author_name: Optional[str] = None) -> 'Key':
        """Perform a key turn - rotate to new cryptographic context.
        
        This creates a new Key with a new cryptographic identity while
        maintaining provenance through the turn chain.
        
        Args:
            new_author_name: Optional new author name (defaults to current + turn count)
            
        Returns:
            New Key instance with fresh cryptographic identity
        """
        self.turn_count += 1
        if new_author_name is None:
            new_author_name = f"{self.author.name}:turn{self.turn_count}"
        
        # Create new key with fresh signer
        new_key = Key(author_name=new_author_name, signer=SovereignSigner())
        new_key.turn_count = self.turn_count
        
        return new_key
    
    def sign_event(self, event: Event) -> SignatureResult:
        """Sign an event with this key.
        
        Args:
            event: Event to sign
            
        Returns:
            SignatureResult with signature and metadata
        """
        event_data = {
            "event_type": event.event_type.value,
            "event_id": event.event_id,
            "author": {
                "name": event.author.name,
                "key_id": event.author.key_id
            },
            "payload": event.payload,
            "timestamp": event.timestamp
        }
        return self.signer.sign(event_data)


class GlyphEngine:
    """Compression and diagnostic system for structured event representation.
    
    The GlyphEngine provides:
    - Event compression using symbolic glyphs
    - Diagnostic information extraction
    - Human-readable event summaries
    """
    
    # Symbolic glyphs for event types
    GLYPHS = {
        EventType.IGNITION: "⚡",
        EventType.INSCRIPTION: "📜",
        EventType.CONSEQUENCE: "🌊",
        EventType.AUDIT: "🔍"
    }
    
    def compress(self, event: Event) -> str:
        """Compress event to symbolic representation.
        
        Args:
            event: Event to compress
            
        Returns:
            Compressed symbolic string
        """
        glyph = self.GLYPHS.get(event.event_type, "?")
        return f"{glyph}[{event.event_id}]@{event.author.key_id[:8]}"
    
    def extract_diagnostics(self, event: Event) -> Dict[str, Any]:
        """Extract diagnostic information from event.
        
        Args:
            event: Event to analyze
            
        Returns:
            Dictionary of diagnostic information
        """
        payload_size = len(json.dumps(event.payload))
        
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "author_key_id": event.author.key_id,
            "author_name": event.author.name,
            "timestamp": event.timestamp,
            "payload_size_bytes": payload_size,
            "compressed_form": self.compress(event),
            "payload_keys": list(event.payload.keys())
        }
    
    def summarize(self, events: List[Event]) -> Dict[str, Any]:
        """Create summary of multiple events.
        
        Args:
            events: List of events to summarize
            
        Returns:
            Summary statistics
        """
        if not events:
            return {"total": 0}
        
        by_type = {}
        by_author = {}
        total_payload_size = 0
        
        for event in events:
            # Count by type
            event_type = event.event_type.value
            by_type[event_type] = by_type.get(event_type, 0) + 1
            
            # Count by author
            author_id = event.author.key_id
            by_author[author_id] = by_author.get(author_id, 0) + 1
            
            # Accumulate payload size
            total_payload_size += len(json.dumps(event.payload))
        
        return {
            "total": len(events),
            "by_type": by_type,
            "by_author": by_author,
            "total_payload_bytes": total_payload_size,
            "unique_authors": len(by_author)
        }


@dataclass
class ManifestEntry:
    """An entry in the WORM ledger."""
    sequence: int
    event: Event
    signature: SignatureResult
    previous_hash: str
    entry_hash: str = ""
    
    def __post_init__(self):
        if not self.entry_hash:
            self.entry_hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute hash of this entry."""
        content = {
            "sequence": self.sequence,
            "event_id": self.event.event_id,
            "timestamp": self.event.timestamp,
            "signature": self.signature.signature,
            "previous_hash": self.previous_hash
        }
        canonical = json.dumps(content, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "sequence": self.sequence,
            "event": {
                "event_type": self.event.event_type.value,
                "event_id": self.event.event_id,
                "author": {
                    "name": self.event.author.name,
                    "key_id": self.event.author.key_id,
                    "public_key": self.event.author.public_key
                },
                "payload": self.event.payload,
                "timestamp": self.event.timestamp
            },
            "signature": self.signature.to_dict(),
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash
        }


class Tablet:
    """WORM (Write-Once, Read-Many) Ledger for append-only audit trail.
    
    The Tablet provides:
    - Append-only storage of signed manifests
    - Chain-of-trust verification via hash chaining
    - Immutable audit trail
    
    Attributes:
        ledger_path: Path to the ledger file
        entries: List of manifest entries in memory
    """
    
    def __init__(self, ledger_path: str = "docs/ledger/worm.log"):
        """Initialize the Tablet.
        
        Args:
            ledger_path: Path to the ledger file
        """
        self.ledger_path = Path(ledger_path)
        self.entries: List[ManifestEntry] = []
        self._ensure_ledger_exists()
        self._load_entries()
    
    def _ensure_ledger_exists(self):
        """Ensure ledger file and directory exist."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.ledger_path.exists():
            self.ledger_path.write_text("")
    
    def _load_entries(self):
        """Load existing entries from ledger file."""
        if self.ledger_path.stat().st_size == 0:
            return
        
        content = self.ledger_path.read_text()
        for line in content.strip().split('\n'):
            if line:
                entry_dict = json.loads(line)
                # Reconstruct entry (simplified - full reconstruction would be more complex)
                self.entries.append(entry_dict)
    
    def append(self, event: Event, signature: SignatureResult) -> ManifestEntry:
        """Append a new signed event to the ledger.
        
        Args:
            event: Event to append
            signature: Signature for the event
            
        Returns:
            The created ManifestEntry
        """
        sequence = len(self.entries)
        previous_hash = self.entries[-1]["entry_hash"] if self.entries else "0" * 64
        
        entry = ManifestEntry(
            sequence=sequence,
            event=event,
            signature=signature,
            previous_hash=previous_hash
        )
        
        # Write to ledger file
        entry_line = json.dumps(entry.to_dict(), separators=(',', ':')) + '\n'
        with open(self.ledger_path, 'a') as f:
            f.write(entry_line)
        
        # Add to in-memory entries
        self.entries.append(entry.to_dict())
        
        return entry
    
    def verify_chain(self) -> Tuple[bool, List[str]]:
        """Verify the integrity of the ledger chain.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.entries:
            return True, []
        
        # Verify first entry
        if self.entries[0]["previous_hash"] != "0" * 64:
            errors.append("First entry has invalid previous_hash")
        
        # Verify chain
        for i in range(1, len(self.entries)):
            expected_prev = self.entries[i-1]["entry_hash"]
            actual_prev = self.entries[i]["previous_hash"]
            
            if expected_prev != actual_prev:
                errors.append(f"Entry {i}: hash chain broken")
        
        return len(errors) == 0, errors
    
    def get_entry_count(self) -> int:
        """Get the number of entries in the ledger."""
        return len(self.entries)
    
    def get_latest_hash(self) -> str:
        """Get the hash of the latest entry."""
        if not self.entries:
            return "0" * 64
        return self.entries[-1]["entry_hash"]


class RootNetwork:
    """Propagation of consequences and downstream effects simulation.
    
    The RootNetwork simulates how events propagate through a dependency graph,
    tracking burden (computational/resource cost) and downstream effects.
    
    Attributes:
        graph: Adjacency list representing the dependency graph
        burden_weights: Weights for burden calculation
    """
    
    def __init__(self):
        """Initialize the RootNetwork."""
        self.graph: Dict[str, Set[str]] = {}  # node_id -> set of dependent node_ids
        self.burden_weights: Dict[str, float] = {}
        self.propagation_history: List[Dict[str, Any]] = []
    
    def add_node(self, node_id: str, burden: float = 1.0):
        """Add a node to the network.
        
        Args:
            node_id: Unique identifier for the node
            burden: Initial burden weight (default 1.0)
        """
        if node_id not in self.graph:
            self.graph[node_id] = set()
            self.burden_weights[node_id] = burden
    
    def add_edge(self, from_node: str, to_node: str):
        """Add a dependency edge.
        
        Args:
            from_node: Source node
            to_node: Dependent node
        """
        self.add_node(from_node)
        self.add_node(to_node)
        self.graph[from_node].add(to_node)
    
    def simulate_propagation(self, event_id: str, initial_burden: float = 1.0) -> Dict[str, Any]:
        """Simulate propagation of an event through the network.
        
        Args:
            event_id: ID of the initiating event
            initial_burden: Initial burden value
            
        Returns:
            Dictionary with propagation results
        """
        # Simple breadth-first propagation
        visited = set()
        queue = [(event_id, initial_burden, 0)]  # (node_id, burden, depth)
        total_burden = 0.0
        affected_nodes = []
        max_depth = 0
        
        while queue:
            node_id, burden, depth = queue.pop(0)
            
            if node_id in visited:
                continue
            
            visited.add(node_id)
            max_depth = max(max_depth, depth)
            
            # Calculate burden for this node
            node_burden = burden * self.burden_weights.get(node_id, 1.0)
            total_burden += node_burden
            
            affected_nodes.append({
                "node_id": node_id,
                "burden": node_burden,
                "depth": depth
            })
            
            # Propagate to dependents
            if node_id in self.graph:
                for dependent in self.graph[node_id]:
                    # Burden decays by PHI at each level
                    decayed_burden = burden / PHI
                    queue.append((dependent, decayed_burden, depth + 1))
        
        result = {
            "event_id": event_id,
            "total_burden": total_burden,
            "affected_nodes": len(affected_nodes),
            "max_depth": max_depth,
            "nodes": affected_nodes
        }
        
        self.propagation_history.append(result)
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the network.
        
        Returns:
            Dictionary with network statistics
        """
        total_nodes = len(self.graph)
        total_edges = sum(len(deps) for deps in self.graph.values())
        
        return {
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "propagation_events": len(self.propagation_history),
            "avg_burden": sum(p["total_burden"] for p in self.propagation_history) / len(self.propagation_history) if self.propagation_history else 0
        }


class CodexReactor:
    """Orchestrator for events through ignition, inscription, and consequence mapping.
    
    The CodexReactor coordinates all components:
    - Key: For authorship and signing
    - GlyphEngine: For event compression and diagnostics
    - Tablet: For immutable storage
    - RootNetwork: For consequence simulation
    
    This is the main entry point for the Codex Reactor framework.
    """
    
    def __init__(self, 
                 author_name: str,
                 ledger_path: str = "docs/ledger/worm.log",
                 signer: Optional[SovereignSigner] = None):
        """Initialize the CodexReactor.
        
        Args:
            author_name: Name of the primary author
            ledger_path: Path to the WORM ledger
            signer: Optional SovereignSigner instance
        """
        self.key = Key(author_name, signer)
        self.glyph_engine = GlyphEngine()
        self.tablet = Tablet(ledger_path)
        self.root_network = RootNetwork()
        self.ignition_count = 0
    
    def ignite(self, payload: Dict[str, Any], 
               event_type: EventType = EventType.IGNITION) -> Event:
        """Ignite a new event in the reactor.
        
        Args:
            payload: Event payload data
            event_type: Type of event (default: IGNITION)
            
        Returns:
            The created Event
        """
        self.ignition_count += 1
        
        event = Event(
            event_type=event_type,
            author=self.key.author,
            payload=payload
        )
        
        return event
    
    def inscribe(self, event: Event) -> ManifestEntry:
        """Inscribe an event to the WORM ledger.
        
        Args:
            event: Event to inscribe
            
        Returns:
            The created ManifestEntry
        """
        # Sign the event
        signature = self.key.sign_event(event)
        
        # Append to ledger
        entry = self.tablet.append(event, signature)
        
        # Add to root network
        self.root_network.add_node(event.event_id, burden=1.0)
        
        return entry
    
    def map_consequence(self, event_id: str, 
                       downstream_ids: List[str]) -> Dict[str, Any]:
        """Map consequences of an event to downstream effects.
        
        Args:
            event_id: ID of the source event
            downstream_ids: List of dependent event IDs
            
        Returns:
            Propagation simulation results
        """
        # Add edges in root network
        for downstream_id in downstream_ids:
            self.root_network.add_edge(event_id, downstream_id)
        
        # Simulate propagation
        return self.root_network.simulate_propagation(event_id)
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive diagnostics for the reactor.
        
        Returns:
            Dictionary with diagnostic information
        """
        chain_valid, chain_errors = self.tablet.verify_chain()
        
        return {
            "author": {
                "name": self.key.author.name,
                "key_id": self.key.author.key_id,
                "turn_count": self.key.turn_count
            },
            "signer": {
                "algorithm": self.key.signer.algorithm
            },
            "ledger": {
                "path": str(self.tablet.ledger_path),
                "entries": self.tablet.get_entry_count(),
                "latest_hash": self.tablet.get_latest_hash(),
                "chain_valid": chain_valid,
                "chain_errors": chain_errors
            },
            "network": self.root_network.get_statistics(),
            "ignitions": self.ignition_count,
            "zorel_constant": ZOREL_CONSTANT,
            "phi": PHI
        }
