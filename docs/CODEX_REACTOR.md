# Codex Reactor Framework

**Production-Ready Architecture for Governance and Trust**

## Overview

The Codex Reactor is a comprehensive framework for event governance, auditing, and trust management. It integrates post-quantum cryptography (PQC) with immutable ledger technology to provide a robust "trust spine" for the ZOREL-IRON architecture.

## Architecture Components

### 1. Key - Authorship Operators

The `Key` class provides cryptographic identity and authorship provenance:

```python
from src.codex_reactor import Key

# Initialize with author name
key = Key("alice")

# Access author information
print(key.author.name)      # "alice"
print(key.author.key_id)    # Unique key identifier
print(key.author.public_key) # PQC public key

# Perform key rotation (turn)
new_key = key.turn()  # Creates fresh cryptographic context
```

**Key Features:**
- Post-quantum cryptographic identity via CRYSTALS-Dilithium-5
- Deterministic key IDs derived from public keys
- `turn()` mechanism for key rotation with provenance preservation
- Integration with `SovereignSigner` for all signing operations

**Invariants:**
- Each Key has unique cryptographic identity
- `turn()` maintains chain-of-trust through turn counter
- All signed operations include author attribution

### 2. GlyphEngine - Compression & Diagnostics

The `GlyphEngine` provides symbolic compression and diagnostic extraction for events:

```python
from src.codex_reactor import GlyphEngine, Event, EventType

engine = GlyphEngine()

# Compress event to symbolic form
compressed = engine.compress(event)  # Returns: "⚡[event_id]@key_id"

# Extract diagnostics
diagnostics = engine.extract_diagnostics(event)

# Summarize multiple events
summary = engine.summarize(events)
```

**Symbolic Glyphs:**
- ⚡ : IGNITION events
- 📜 : INSCRIPTION events
- 🌊 : CONSEQUENCE events
- 🔍 : AUDIT events

**Diagnostic Information:**
- Event metadata (ID, type, author)
- Payload size and structure
- Compressed symbolic representation
- Temporal markers

### 3. Tablet - WORM Ledger

The `Tablet` implements a Write-Once, Read-Many (WORM) ledger for immutable audit trails:

```python
from src.codex_reactor import Tablet

# Initialize ledger
tablet = Tablet("docs/ledger/worm.log")

# Append signed event
entry = tablet.append(event, signature)

# Verify chain integrity
is_valid, errors = tablet.verify_chain()

# Query ledger
count = tablet.get_entry_count()
latest_hash = tablet.get_latest_hash()
```

**Properties:**
- Append-only: No modifications or deletions
- Hash-chained: Each entry links to previous via cryptographic hash
- Signed: All entries include PQC signatures
- Persistent: Stored on disk with JSON-lines format

**Chain Structure:**
```
Entry[0]: previous_hash = "0000...0000" (genesis)
Entry[1]: previous_hash = Entry[0].entry_hash
Entry[2]: previous_hash = Entry[1].entry_hash
...
```

### 4. RootNetwork - Consequence Propagation

The `RootNetwork` simulates propagation of consequences through dependency graphs:

```python
from src.codex_reactor import RootNetwork

network = RootNetwork()

# Build dependency graph
network.add_edge("event1", "event2")  # event2 depends on event1
network.add_edge("event1", "event3")  # event3 depends on event1

# Simulate propagation
result = network.simulate_propagation("event1", initial_burden=1.0)

# Analyze results
print(result["total_burden"])      # Accumulated burden
print(result["affected_nodes"])    # Number of affected events
print(result["max_depth"])        # Max propagation depth
```

**Burden Model:**
- Initial burden assigned to source event
- Burden decays by Φ (golden ratio) at each propagation level
- Each node has configurable burden weight
- Total burden = sum of weighted burdens across all affected nodes

**Invariants:**
- Burden decreases monotonically with depth
- Propagation terminates (no cycles in current implementation)
- Statistics track all propagation events

### 5. CodexReactor - Orchestration

The `CodexReactor` coordinates all components into a unified workflow:

```python
from src.codex_reactor import CodexReactor, EventType

# Initialize reactor
reactor = CodexReactor(
    author_name="alice",
    ledger_path="docs/ledger/worm.log"
)

# IGNITE: Create new event
event = reactor.ignite(
    payload={"action": "initialize", "data": 42},
    event_type=EventType.IGNITION
)

# INSCRIBE: Write to ledger with signature
entry = reactor.inscribe(event)

# MAP CONSEQUENCE: Simulate downstream effects
result = reactor.map_consequence(
    event_id=event.event_id,
    downstream_ids=["dependent_event_1", "dependent_event_2"]
)

# DIAGNOSTICS: Get comprehensive status
diagnostics = reactor.get_diagnostics()
```

**Workflow Stages:**
1. **Ignition**: Create event with author and payload
2. **Inscription**: Sign and append to WORM ledger
3. **Consequence Mapping**: Simulate propagation effects
4. **Audit**: Verify chain integrity and gather diagnostics

## Security Integration

### Post-Quantum Cryptography

All signatures use **CRYSTALS-Dilithium-5** via the `SovereignSigner`:

```python
from security.dilithium_signer import SovereignSigner

signer = SovereignSigner()  # Auto-generates Dilithium-5 keys

# Sign data
result = signer.sign({"manifest": "data"})
print(result.algorithm)  # "Dilithium5" or "HMAC-SHA256" (fallback)

# Verify signature
is_valid = signer.verify(data, result.signature, result.public_key)
```

**Fallback Mode:**
- If `liboqs` is not available, falls back to HMAC-SHA256
- Maintains API compatibility
- Suitable for development/testing environments

**Key Management:**
- Private keys kept secure within signer instance
- Public keys embedded in manifest entries
- Key rotation via `Key.turn()` mechanism

### Canonical JSON

All signed data uses canonical JSON representation:
- Sorted keys: `sort_keys=True`
- No whitespace: `separators=(',', ':')`
- Deterministic serialization across platforms

## Repository Artifact Mapping

| Component | File Path | Description |
|-----------|-----------|-------------|
| **SovereignSigner** | `security/dilithium_signer.py` | PQC signing implementation |
| **CodexReactor** | `src/codex_reactor.py` | Main framework components |
| **Ignite Demo** | `scripts/ignite_demo.py` | CLI demonstration tool |
| **Tests** | `tests/test_codex_reactor.py` | Comprehensive test suite |
| **WORM Ledger** | `docs/ledger/worm.log` | Append-only ledger file |
| **Documentation** | `docs/CODEX_REACTOR.md` | This document |

## Constants and References

### Mathematical Constants

```python
PHI = 1.618033988749895  # Golden ratio (Φ)
ZOREL_CONSTANT = 717      # Project signature number
```

**Usage:**
- Φ: Burden decay factor in RootNetwork propagation
- 717: Zorel signature (3 × 239, where 239 is prime)

### Event Types

```python
class EventType(Enum):
    IGNITION = "ignition"       # System initialization events
    INSCRIPTION = "inscription" # Data recording events
    CONSEQUENCE = "consequence" # Propagation effects
    AUDIT = "audit"            # Verification events
```

## Usage Examples

### Basic Ignition and Inscription

```python
from src.codex_reactor import CodexReactor, EventType

# Create reactor
reactor = CodexReactor("alice")

# Ignite event
event = reactor.ignite({
    "action": "create_resource",
    "resource_id": "res_001",
    "timestamp": "2026-02-17T18:00:00Z"
})

# Inscribe to ledger
entry = reactor.inscribe(event)

print(f"Inscribed to sequence {entry.sequence}")
print(f"Entry hash: {entry.entry_hash}")
```

### Key Turn with Provenance

```python
# Initial key
key1 = reactor.key
print(f"Key 1: {key1.author.key_id}, turn_count={key1.turn_count}")

# Perform turn
key2 = key1.turn("alice_v2")
reactor.key = key2

# Create event with new key
event = reactor.ignite({"action": "post_rotation"})
entry = reactor.inscribe(event)

print(f"Key 2: {key2.author.key_id}, turn_count={key2.turn_count}")
```

### Consequence Propagation

```python
# Create event chain
e1 = reactor.ignite({"step": 1})
e2 = reactor.ignite({"step": 2})
e3 = reactor.ignite({"step": 3})

reactor.inscribe(e1)
reactor.inscribe(e2)
reactor.inscribe(e3)

# Map dependencies: e1 triggers e2 and e3
result = reactor.map_consequence(e1.event_id, [e2.event_id, e3.event_id])

print(f"Propagation affected {result['affected_nodes']} nodes")
print(f"Total burden: {result['total_burden']:.4f}")
```

### Full Audit Trail

```python
# Get comprehensive diagnostics
diagnostics = reactor.get_diagnostics()

# Check ledger integrity
print(f"Ledger entries: {diagnostics['ledger']['entries']}")
print(f"Chain valid: {diagnostics['ledger']['chain_valid']}")

# Network statistics
print(f"Network nodes: {diagnostics['network']['total_nodes']}")
print(f"Network edges: {diagnostics['network']['total_edges']}")

# Author information
print(f"Author: {diagnostics['author']['name']}")
print(f"Key turns: {diagnostics['author']['turn_count']}")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/test_codex_reactor.py -v

# Run specific test class
python -m pytest tests/test_codex_reactor.py::TestCodexReactor -v

# Run with coverage
python -m pytest tests/test_codex_reactor.py --cov=src.codex_reactor
```

## Demo Script

Try the interactive demo:

```bash
# Basic demo
python scripts/ignite_demo.py

# Full demo with all features
python scripts/ignite_demo.py --author alice --full

# Custom ledger path
python scripts/ignite_demo.py --ledger /tmp/test_ledger.log
```

## Design Principles

### 1. Immutability
- WORM ledger ensures no tampering with historical records
- Hash chains provide cryptographic proof of sequence
- Append-only operations prevent deletion

### 2. Provenance
- All events signed by author with PQC keys
- Key.turn() maintains rotation history
- Event IDs deterministically derived from content

### 3. Auditability
- Complete event history in ledger
- Verifiable signature chain
- Diagnostic tools for investigation

### 4. Transparency
- Human-readable event summaries via GlyphEngine
- Comprehensive diagnostics API
- Clear error reporting

### 5. Resilience
- Fallback signing mode when PQC unavailable
- Graceful degradation
- No single point of failure

## Future Enhancements

### Phase 1 (Current)
- ✅ CRYSTALS-Dilithium-5 integration
- ✅ WORM ledger implementation
- ✅ Basic consequence simulation
- ✅ Key rotation mechanism

### Phase 2 (Planned)
- [ ] Hardware HSM integration for key storage
- [ ] Parallel propagation simulation
- [ ] Distributed ledger replication
- [ ] Advanced burden models (non-linear decay)

### Phase 3 (Future)
- [ ] Zero-knowledge proofs for privacy
- [ ] Cross-reactor synchronization
- [ ] Machine learning for burden prediction
- [ ] Real-time audit dashboards

## Integration with ZOREL-IRON

The Codex Reactor serves as the **trust spine** for the ZOREL-IRON architecture:

1. **Governance Layer**: All governance decisions inscribed to ledger
2. **Trust Anchors**: PQC signatures ensure authenticity
3. **Audit Trail**: Complete history for compliance
4. **Consequence Analysis**: Impact assessment via RootNetwork

## References

- [NIST PQC Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography)
- [CRYSTALS-Dilithium Specification](https://pq-crystals.org/dilithium/)
- [Open Quantum Safe (liboqs)](https://openquantumsafe.org/)
- [WORM Storage Principles](https://en.wikipedia.org/wiki/Write_once_read_many)

## License

See repository LICENSE file.

## Contact

For questions or contributions, see the main repository README.

---

**Generated**: 2026-02-17  
**Version**: 1.0.0  
**Status**: Production-Ready
