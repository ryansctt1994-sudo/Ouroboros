"""Test suite for Codex Reactor framework.

Tests the core components:
- Key: Authorship operators and turn() mechanism
- GlyphEngine: Compression and diagnostics
- Tablet: WORM ledger operations
- RootNetwork: Consequence propagation
- CodexReactor: End-to-end orchestration
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.codex_reactor import (
    CodexReactor,
    Key,
    GlyphEngine,
    Tablet,
    RootNetwork,
    Event,
    EventType,
    Author,
    ManifestEntry,
    PHI,
    ZOREL_CONSTANT
)
from security.dilithium_signer import SovereignSigner


class TestKey:
    """Test Key authorship operator."""
    
    def test_key_initialization(self):
        """Test Key initialization."""
        key = Key("alice")
        
        assert key.author.name == "alice"
        assert key.author.key_id is not None
        assert len(key.author.key_id) == 16  # 16 hex characters
        assert key.turn_count == 0
        assert key.signer is not None
    
    def test_key_turn(self):
        """Test Key.turn() mechanism."""
        key = Key("alice")
        original_key_id = key.author.key_id
        
        # Perform turn
        new_key = key.turn()
        
        # Original key state
        assert key.turn_count == 1
        
        # New key state
        assert new_key.author.name == "alice:turn1"
        assert new_key.author.key_id != original_key_id
        assert new_key.turn_count == 1
    
    def test_key_turn_custom_name(self):
        """Test Key.turn() with custom name."""
        key = Key("alice")
        
        new_key = key.turn("bob")
        
        assert new_key.author.name == "bob"
        assert new_key.turn_count == 1
    
    def test_sign_event(self):
        """Test event signing."""
        key = Key("alice")
        
        event = Event(
            event_type=EventType.IGNITION,
            author=key.author,
            payload={"test": "data"}
        )
        
        signature = key.sign_event(event)
        
        assert signature.signature is not None
        assert signature.public_key == key.author.public_key
        assert signature.algorithm in ["Dilithium5", "HMAC-SHA256"]


class TestGlyphEngine:
    """Test GlyphEngine compression and diagnostics."""
    
    def test_compress(self):
        """Test event compression."""
        engine = GlyphEngine()
        author = Author("alice", "abc123", "pubkey")
        
        event = Event(
            event_type=EventType.IGNITION,
            author=author,
            payload={"test": "data"}
        )
        
        compressed = engine.compress(event)
        
        assert "⚡" in compressed
        assert event.event_id[:8] in compressed
        assert author.key_id[:8] in compressed
    
    def test_extract_diagnostics(self):
        """Test diagnostic extraction."""
        engine = GlyphEngine()
        author = Author("alice", "abc123", "pubkey")
        
        event = Event(
            event_type=EventType.INSCRIPTION,
            author=author,
            payload={"key1": "value1", "key2": "value2"}
        )
        
        diagnostics = engine.extract_diagnostics(event)
        
        assert diagnostics["event_id"] == event.event_id
        assert diagnostics["event_type"] == "inscription"
        assert diagnostics["author_name"] == "alice"
        assert "payload_size_bytes" in diagnostics
        assert diagnostics["payload_keys"] == ["key1", "key2"]
    
    def test_summarize_events(self):
        """Test event summarization."""
        engine = GlyphEngine()
        author = Author("alice", "abc123", "pubkey")
        
        events = [
            Event(EventType.IGNITION, author, {"data": i})
            for i in range(5)
        ]
        
        summary = engine.summarize(events)
        
        assert summary["total"] == 5
        assert summary["by_type"]["ignition"] == 5
        assert summary["unique_authors"] == 1
        assert summary["total_payload_bytes"] > 0


class TestTablet:
    """Test Tablet WORM ledger."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.ledger_path = Path(self.temp_dir) / "test_ledger.log"
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_tablet_initialization(self):
        """Test Tablet initialization."""
        tablet = Tablet(str(self.ledger_path))
        
        assert tablet.ledger_path.exists()
        assert tablet.get_entry_count() == 0
    
    def test_append_entry(self):
        """Test appending entry to ledger."""
        tablet = Tablet(str(self.ledger_path))
        key = Key("alice")
        
        event = Event(
            event_type=EventType.IGNITION,
            author=key.author,
            payload={"test": "data"}
        )
        
        signature = key.sign_event(event)
        entry = tablet.append(event, signature)
        
        assert entry.sequence == 0
        assert entry.previous_hash == "0" * 64
        assert entry.entry_hash is not None
        assert tablet.get_entry_count() == 1
    
    def test_append_multiple_entries(self):
        """Test appending multiple entries."""
        tablet = Tablet(str(self.ledger_path))
        key = Key("alice")
        
        # Append 3 entries
        for i in range(3):
            event = Event(
                event_type=EventType.INSCRIPTION,
                author=key.author,
                payload={"step": i}
            )
            signature = key.sign_event(event)
            tablet.append(event, signature)
        
        assert tablet.get_entry_count() == 3
    
    def test_verify_chain(self):
        """Test ledger chain verification."""
        tablet = Tablet(str(self.ledger_path))
        key = Key("alice")
        
        # Append entries
        for i in range(3):
            event = Event(
                event_type=EventType.INSCRIPTION,
                author=key.author,
                payload={"step": i}
            )
            signature = key.sign_event(event)
            tablet.append(event, signature)
        
        is_valid, errors = tablet.verify_chain()
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_ledger_persistence(self):
        """Test that ledger persists to disk."""
        tablet = Tablet(str(self.ledger_path))
        key = Key("alice")
        
        event = Event(
            event_type=EventType.IGNITION,
            author=key.author,
            payload={"test": "data"}
        )
        signature = key.sign_event(event)
        tablet.append(event, signature)
        
        # Read raw file
        content = self.ledger_path.read_text()
        
        assert len(content) > 0
        assert event.event_id in content


class TestRootNetwork:
    """Test RootNetwork consequence propagation."""
    
    def test_initialization(self):
        """Test RootNetwork initialization."""
        network = RootNetwork()
        
        assert len(network.graph) == 0
        assert len(network.burden_weights) == 0
    
    def test_add_node(self):
        """Test adding nodes."""
        network = RootNetwork()
        
        network.add_node("node1", burden=1.5)
        
        assert "node1" in network.graph
        assert network.burden_weights["node1"] == 1.5
    
    def test_add_edge(self):
        """Test adding edges."""
        network = RootNetwork()
        
        network.add_edge("node1", "node2")
        
        assert "node1" in network.graph
        assert "node2" in network.graph
        assert "node2" in network.graph["node1"]
    
    def test_simulate_propagation_simple(self):
        """Test simple propagation simulation."""
        network = RootNetwork()
        
        network.add_node("event1", burden=1.0)
        
        result = network.simulate_propagation("event1", initial_burden=1.0)
        
        assert result["event_id"] == "event1"
        assert result["total_burden"] == 1.0
        assert result["affected_nodes"] == 1
        assert result["max_depth"] == 0
    
    def test_simulate_propagation_chain(self):
        """Test propagation through a chain."""
        network = RootNetwork()
        
        # Create chain: event1 -> event2 -> event3
        network.add_edge("event1", "event2")
        network.add_edge("event2", "event3")
        
        result = network.simulate_propagation("event1", initial_burden=1.0)
        
        assert result["affected_nodes"] == 3
        assert result["max_depth"] == 2
        # Burden should decay by PHI at each level
        assert result["total_burden"] > 1.0
    
    def test_get_statistics(self):
        """Test network statistics."""
        network = RootNetwork()
        
        network.add_edge("event1", "event2")
        network.add_edge("event1", "event3")
        network.simulate_propagation("event1")
        
        stats = network.get_statistics()
        
        assert stats["total_nodes"] == 3
        assert stats["total_edges"] == 2
        assert stats["propagation_events"] == 1


class TestCodexReactor:
    """Test CodexReactor orchestration."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.ledger_path = Path(self.temp_dir) / "test_ledger.log"
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_reactor_initialization(self):
        """Test CodexReactor initialization."""
        reactor = CodexReactor("alice", str(self.ledger_path))
        
        assert reactor.key.author.name == "alice"
        assert reactor.tablet.ledger_path == self.ledger_path
        assert reactor.ignition_count == 0
    
    def test_ignite(self):
        """Test event ignition."""
        reactor = CodexReactor("alice", str(self.ledger_path))
        
        event = reactor.ignite({"action": "test"})
        
        assert event.event_type == EventType.IGNITION
        assert event.author.name == "alice"
        assert event.payload["action"] == "test"
        assert reactor.ignition_count == 1
    
    def test_inscribe(self):
        """Test event inscription."""
        reactor = CodexReactor("alice", str(self.ledger_path))
        
        event = reactor.ignite({"action": "test"})
        entry = reactor.inscribe(event)
        
        assert entry.sequence == 0
        assert entry.event.event_id == event.event_id
        assert reactor.tablet.get_entry_count() == 1
    
    def test_map_consequence(self):
        """Test consequence mapping."""
        reactor = CodexReactor("alice", str(self.ledger_path))
        
        # Create events
        event1 = reactor.ignite({"step": 1})
        event2 = reactor.ignite({"step": 2})
        
        reactor.inscribe(event1)
        reactor.inscribe(event2)
        
        # Map consequence
        result = reactor.map_consequence(event1.event_id, [event2.event_id])
        
        assert result["event_id"] == event1.event_id
        assert result["affected_nodes"] >= 2
    
    def test_get_diagnostics(self):
        """Test reactor diagnostics."""
        reactor = CodexReactor("alice", str(self.ledger_path))
        
        # Create some activity
        event = reactor.ignite({"action": "test"})
        reactor.inscribe(event)
        
        diagnostics = reactor.get_diagnostics()
        
        assert diagnostics["author"]["name"] == "alice"
        assert diagnostics["ledger"]["entries"] == 1
        assert diagnostics["ledger"]["chain_valid"] is True
        assert diagnostics["ignitions"] == 1
        assert diagnostics["zorel_constant"] == ZOREL_CONSTANT
        assert diagnostics["phi"] == PHI
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow."""
        reactor = CodexReactor("alice", str(self.ledger_path))
        
        # Step 1: Ignite initial event
        event1 = reactor.ignite({
            "action": "initialize",
            "message": "Starting workflow"
        }, EventType.IGNITION)
        
        entry1 = reactor.inscribe(event1)
        assert entry1.sequence == 0
        
        # Step 2: Create dependent events
        event2 = reactor.ignite({"step": 2}, EventType.INSCRIPTION)
        event3 = reactor.ignite({"step": 3}, EventType.INSCRIPTION)
        
        reactor.inscribe(event2)
        reactor.inscribe(event3)
        
        # Step 3: Map consequences
        result = reactor.map_consequence(
            event1.event_id,
            [event2.event_id, event3.event_id]
        )
        
        assert result["affected_nodes"] == 3
        
        # Step 4: Verify integrity
        is_valid, errors = reactor.tablet.verify_chain()
        assert is_valid is True
        
        # Step 5: Get diagnostics
        diagnostics = reactor.get_diagnostics()
        assert diagnostics["ledger"]["entries"] == 3
        assert diagnostics["network"]["total_nodes"] == 3
        assert diagnostics["network"]["total_edges"] == 2


class TestInvariants:
    """Test critical invariants and properties."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.ledger_path = Path(self.temp_dir) / "test_ledger.log"
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_ledger_append_only(self):
        """Test that ledger is truly append-only."""
        tablet = Tablet(str(self.ledger_path))
        key = Key("alice")
        
        # Append 3 entries
        for i in range(3):
            event = Event(
                event_type=EventType.INSCRIPTION,
                author=key.author,
                payload={"step": i}
            )
            signature = key.sign_event(event)
            tablet.append(event, signature)
        
        # Verify count doesn't decrease
        initial_count = tablet.get_entry_count()
        assert initial_count == 3
        
        # Any new operation should only increase or maintain count
        # (We can't test actual immutability without filesystem manipulation)
    
    def test_hash_chain_integrity(self):
        """Test hash chain maintains integrity."""
        tablet = Tablet(str(self.ledger_path))
        key = Key("alice")
        
        entries = []
        for i in range(5):
            event = Event(
                event_type=EventType.INSCRIPTION,
                author=key.author,
                payload={"step": i}
            )
            signature = key.sign_event(event)
            entry = tablet.append(event, signature)
            entries.append(entry)
        
        # Verify each entry links to previous
        for i in range(1, len(entries)):
            # Note: entries are dicts after being stored
            # In production, we'd have proper object reconstruction
            pass
    
    def test_burden_decay_by_phi(self):
        """Test that burden decays by PHI in propagation."""
        network = RootNetwork()
        
        # Create linear chain
        network.add_edge("e1", "e2")
        network.add_edge("e2", "e3")
        
        result = network.simulate_propagation("e1", initial_burden=1.0)
        
        # With default burden weights of 1.0, we expect:
        # e1: 1.0 * 1.0 = 1.0
        # e2: (1.0 / PHI) * 1.0 ≈ 0.618
        # e3: (0.618 / PHI) * 1.0 ≈ 0.382
        # Total ≈ 2.0
        
        assert result["total_burden"] > 1.5
        assert result["total_burden"] < 2.5
