#!/usr/bin/env python3
"""Ignite Demo - Command-line demonstration of Codex Reactor.

This script demonstrates the Codex Reactor framework by:
1. Initializing a reactor with an author
2. Igniting events
3. Inscribing them to the WORM ledger
4. Simulating consequence propagation
5. Displaying diagnostics
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.codex_reactor import (
    CodexReactor,
    EventType,
    PHI,
    ZOREL_CONSTANT
)


def display_banner():
    """Display the demo banner."""
    print("=" * 70)
    print("  CODEX REACTOR - IGNITION DEMO")
    print("  Production-Ready Governance and Trust Architecture")
    print("=" * 70)
    print(f"  Φ (Golden Ratio): {PHI:.6f}")
    print(f"  Zorel Constant: {ZOREL_CONSTANT}")
    print("=" * 70)
    print()


def demo_basic_ignition(author_name: str, ledger_path: str):
    """Demonstrate basic ignition and inscription.
    
    Args:
        author_name: Name of the author
        ledger_path: Path to the ledger
    """
    print("🚀 BASIC IGNITION DEMO")
    print("-" * 70)
    
    # Initialize reactor
    reactor = CodexReactor(author_name=author_name, ledger_path=ledger_path)
    print(f"✓ Reactor initialized for author: {author_name}")
    print(f"  Key ID: {reactor.key.author.key_id}")
    print(f"  Algorithm: {reactor.key.signer.algorithm}")
    print()
    
    # Ignite an event
    print("⚡ Igniting event...")
    event = reactor.ignite(
        payload={
            "action": "initialize",
            "message": "First ignition in the Codex Reactor",
            "phi_reference": PHI
        },
        event_type=EventType.IGNITION
    )
    print(f"  Event ID: {event.event_id}")
    print(f"  Compressed: {reactor.glyph_engine.compress(event)}")
    print()
    
    # Inscribe to ledger
    print("📜 Inscribing to WORM ledger...")
    entry = reactor.inscribe(event)
    print(f"  Sequence: {entry.sequence}")
    print(f"  Entry Hash: {entry.entry_hash[:16]}...")
    print(f"  Previous Hash: {entry.previous_hash[:16]}...")
    print(f"  Signature: {entry.signature.signature[:32]}...")
    print()
    
    return reactor


def demo_multiple_events(reactor: CodexReactor):
    """Demonstrate multiple events and consequences.
    
    Args:
        reactor: Initialized CodexReactor
    """
    print("🌊 MULTIPLE EVENTS & CONSEQUENCE MAPPING")
    print("-" * 70)
    
    events = []
    
    # Create multiple events
    for i in range(3):
        event = reactor.ignite(
            payload={
                "step": i + 1,
                "description": f"Sequential event {i + 1}",
                "data": f"Payload data for event {i + 1}"
            },
            event_type=EventType.INSCRIPTION
        )
        entry = reactor.inscribe(event)
        events.append(event)
        print(f"  ✓ Event {i + 1}: {event.event_id} → {reactor.glyph_engine.compress(event)}")
    
    print()
    
    # Map consequences
    print("🔗 Mapping consequences...")
    # First event triggers second and third
    result = reactor.map_consequence(
        events[0].event_id,
        [events[1].event_id, events[2].event_id]
    )
    
    print(f"  Source: {events[0].event_id}")
    print(f"  Total Burden: {result['total_burden']:.4f}")
    print(f"  Affected Nodes: {result['affected_nodes']}")
    print(f"  Max Depth: {result['max_depth']}")
    print()


def demo_key_turn(reactor: CodexReactor):
    """Demonstrate key turn mechanism.
    
    Args:
        reactor: Initialized CodexReactor
    """
    print("🔄 KEY TURN DEMO")
    print("-" * 70)
    
    original_author = reactor.key.author.name
    original_key_id = reactor.key.author.key_id
    original_turn_count = reactor.key.turn_count
    
    print(f"  Original Author: {original_author}")
    print(f"  Original Key ID: {original_key_id}")
    print(f"  Turn Count: {original_turn_count}")
    print()
    
    # Perform key turn
    print("  Performing key turn...")
    new_key = reactor.key.turn()
    reactor.key = new_key
    
    print(f"  New Author: {reactor.key.author.name}")
    print(f"  New Key ID: {reactor.key.author.key_id}")
    print(f"  Turn Count: {reactor.key.turn_count}")
    print()
    
    # Create event with new key
    event = reactor.ignite(
        payload={
            "action": "post_turn_event",
            "message": "Event after key turn"
        },
        event_type=EventType.AUDIT
    )
    entry = reactor.inscribe(event)
    print(f"  ✓ Event inscribed with new key: {event.event_id}")
    print()


def display_diagnostics(reactor: CodexReactor):
    """Display comprehensive diagnostics.
    
    Args:
        reactor: Initialized CodexReactor
    """
    print("🔍 REACTOR DIAGNOSTICS")
    print("-" * 70)
    
    diagnostics = reactor.get_diagnostics()
    
    print("Author:")
    print(f"  Name: {diagnostics['author']['name']}")
    print(f"  Key ID: {diagnostics['author']['key_id']}")
    print(f"  Turn Count: {diagnostics['author']['turn_count']}")
    print()
    
    print("Signer:")
    print(f"  Algorithm: {diagnostics['signer']['algorithm']}")
    print()
    
    print("Ledger:")
    print(f"  Path: {diagnostics['ledger']['path']}")
    print(f"  Entries: {diagnostics['ledger']['entries']}")
    print(f"  Latest Hash: {diagnostics['ledger']['latest_hash'][:32]}...")
    print(f"  Chain Valid: {diagnostics['ledger']['chain_valid']}")
    if diagnostics['ledger']['chain_errors']:
        print(f"  Errors: {diagnostics['ledger']['chain_errors']}")
    print()
    
    print("Network:")
    print(f"  Total Nodes: {diagnostics['network']['total_nodes']}")
    print(f"  Total Edges: {diagnostics['network']['total_edges']}")
    print(f"  Propagation Events: {diagnostics['network']['propagation_events']}")
    if diagnostics['network']['propagation_events'] > 0:
        print(f"  Avg Burden: {diagnostics['network']['avg_burden']:.4f}")
    print()
    
    print("Reactor:")
    print(f"  Ignitions: {diagnostics['ignitions']}")
    print(f"  Zorel Constant: {diagnostics['zorel_constant']}")
    print(f"  Phi: {diagnostics['phi']:.6f}")
    print()


def main():
    """Main entry point for the demo."""
    parser = argparse.ArgumentParser(
        description="Codex Reactor Ignition Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic demo with default author
  python ignite_demo.py
  
  # Demo with custom author
  python ignite_demo.py --author alice
  
  # Demo with custom ledger path
  python ignite_demo.py --ledger /tmp/test_ledger.log
  
  # Full demo with all features
  python ignite_demo.py --author bob --full
        """
    )
    
    parser.add_argument(
        '--author',
        default='reactor_demo',
        help='Author name (default: reactor_demo)'
    )
    
    parser.add_argument(
        '--ledger',
        default='docs/ledger/worm.log',
        help='Path to ledger file (default: docs/ledger/worm.log)'
    )
    
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full demo with all features'
    )
    
    args = parser.parse_args()
    
    # Display banner
    display_banner()
    
    # Run basic demo
    reactor = demo_basic_ignition(args.author, args.ledger)
    
    if args.full:
        # Run additional demos
        demo_multiple_events(reactor)
        demo_key_turn(reactor)
    
    # Always display diagnostics
    display_diagnostics(reactor)
    
    print("=" * 70)
    print("  Demo complete! Check the ledger at:", args.ledger)
    print("=" * 70)


if __name__ == '__main__':
    main()
