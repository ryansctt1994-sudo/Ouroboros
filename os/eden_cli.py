#!/usr/bin/env python3
"""
EDEN CLI - Command-Line Client
===============================

Standalone CLI for controlling the EDEN daemon via Unix domain socket.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import argparse
import json
import os
import socket
import sys
from pathlib import Path

# Add current directory to path for importing eden_ipc
SCRIPT_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from eden_ipc import SOCKET_PATH, make_request, parse_message


def connect_to_daemon() -> socket.socket:
    """
    Connect to the EDEN daemon socket.
    
    Returns:
        Connected socket
    
    Raises:
        ConnectionError: If daemon is not running
    """
    if not os.path.exists(SOCKET_PATH):
        raise ConnectionError(
            "EDEN daemon is not running. Start it with:\n"
            f"  python {SCRIPT_DIR}/eden_daemon.py"
        )
    
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.connect(SOCKET_PATH)
        return sock
    except (ConnectionRefusedError, FileNotFoundError):
        raise ConnectionError(
            "EDEN daemon is not running. Start it with:\n"
            f"  python {SCRIPT_DIR}/eden_daemon.py"
        )


def send_request(method: str, params: dict = None) -> dict:
    """
    Send a request to the daemon and get response.
    
    Args:
        method: Method name
        params: Optional parameters
    
    Returns:
        Response result
    
    Raises:
        ConnectionError: If daemon is not running
        RuntimeError: If daemon returns an error
    """
    sock = connect_to_daemon()
    
    try:
        # Send request
        request = make_request(method, params)
        sock.sendall(request.encode('utf-8'))
        
        # Receive response
        data = b""
        while b"\n" not in data:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        
        # Parse response
        response = parse_message(data.decode('utf-8'))
        
        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"Error {error['code']}: {error['message']}")
        
        return response.get("result", {})
    
    finally:
        sock.close()


def cmd_status(args):
    """Show daemon status."""
    try:
        result = send_request("get_status")
        print("EDEN Daemon Status")
        print("=" * 40)
        print(f"Running:    {result['running']}")
        print(f"Tick:       {result['tick']}")
        print(f"Agents:     {result['agents']}")
        print(f"Consensus:  {result['consensus']}")
        print(f"Gamma:      {result['gamma']:.4f}")
        return 0
    except ConnectionError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_start(args):
    """Start the tick loop."""
    try:
        result = send_request("start")
        if result.get("success"):
            print("Tick loop started")
            return 0
        else:
            print("Failed to start tick loop", file=sys.stderr)
            return 1
    except ConnectionError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_stop(args):
    """Stop the tick loop."""
    try:
        result = send_request("stop")
        if result.get("success"):
            print("Tick loop stopped")
            return 0
        else:
            print("Failed to stop tick loop", file=sys.stderr)
            return 1
    except ConnectionError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_step(args):
    """Run one tick."""
    try:
        result = send_request("step")
        if result.get("success"):
            print("Single tick executed")
            return 0
        else:
            print("Failed to execute tick", file=sys.stderr)
            return 1
    except ConnectionError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_entities(args):
    """List all entities."""
    try:
        result = send_request("get_entities")
        print("EDEN Entities")
        print("=" * 80)
        print(f"{'ID':<36}  {'Name':<15}  {'Phase':<8}  {'Gamma':<8}  {'Coherence':<10}  {'Synced'}")
        print("-" * 80)
        for entity in result:
            entity_id = entity['id'][:8] + "..."
            name = entity.get('name', 'Unknown')[:15]
            phase = entity.get('phase', 0.0)
            gamma = entity.get('gamma', 0.0)
            coherence = entity.get('coherence', 0.0)
            synced = "✓" if entity.get('synced', False) else "✗"
            print(f"{entity_id:<36}  {name:<15}  {phase:<8.4f}  {gamma:<8.4f}  {coherence:<10.4f}  {synced}")
        print(f"\nTotal: {len(result)} entities")
        return 0
    except ConnectionError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_entity(args):
    """Show entity details."""
    try:
        result = send_request("get_entity", {"entity_id": args.entity_id})
        print(f"Entity: {result.get('name', 'Unknown')}")
        print("=" * 60)
        print(f"ID:   {result['id']}")
        print(f"Type: {result.get('type', 'Unknown')}")
        
        if 'consciousness' in result:
            print("\n7D Consciousness:")
            c = result['consciousness']
            print(f"  Awareness:    {c['awareness']:.4f}")
            print(f"  Intention:    {c['intention']:.4f}")
            print(f"  Emotion:      {c['emotion']:.4f}")
            print(f"  Cognition:    {c['cognition']:.4f}")
            print(f"  Memory:       {c['memory']:.4f}")
            print(f"  Creativity:   {c['creativity']:.4f}")
            print(f"  Integration:  {c['integration']:.4f}")
            print(f"  Coherence:    {c['coherence']:.4f}")
        
        if 'hyphal' in result:
            print("\nHyphal Network:")
            h = result['hyphal']
            print(f"  Phase:        {h['phase']:.4f}")
            print(f"  Gamma:        {h['gamma']:.4f}")
            print(f"  Synchronized: {h['synchronized']}")
            print(f"  Neighbors:    {len(h.get('neighbors', []))}")
        
        return 0
    except ConnectionError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_graph(args):
    """Show graph topology."""
    try:
        result = send_request("get_graph")
        nodes = result.get('nodes', [])
        edges = result.get('edges', [])
        
        print("Network Graph Topology")
        print("=" * 60)
        print(f"Nodes: {len(nodes)}")
        print(f"Edges: {len(edges)}")
        
        if nodes:
            print("\nNodes:")
            for node in nodes[:10]:  # Show first 10
                node_id = node['id'][:8] + "..."
                name = node.get('name', 'Unknown')
                phase = node.get('phase', 0.0)
                gamma = node.get('gamma', 0.0)
                print(f"  {node_id:<15} {name:<15} phase={phase:.4f} gamma={gamma:.4f}")
            
            if len(nodes) > 10:
                print(f"  ... and {len(nodes) - 10} more")
        
        if edges:
            print(f"\nEdges: {len(edges)} connections")
        
        return 0
    except ConnectionError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_metrics(args):
    """Show network metrics."""
    try:
        result = send_request("get_metrics")
        print("Network Metrics")
        print("=" * 40)
        print(f"Mean Gamma:       {result.get('mean_gamma', 0.0):.4f}")
        print(f"Mean Coherence:   {result.get('mean_coherence', 0.0):.4f}")
        print(f"Consensus:        {result.get('consensus', False)}")
        print(f"Total Entities:   {result.get('total_entities', 0)}")
        print(f"Synchronized:     {result.get('synchronized_entities', 0)}")
        return 0
    except ConnectionError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_shutdown(args):
    """Shut down the daemon."""
    try:
        result = send_request("shutdown")
        if result.get("success"):
            print("Daemon shutting down...")
            return 0
        else:
            print("Failed to shutdown daemon", file=sys.stderr)
            return 1
    except ConnectionError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_help(args):
    """Show help message."""
    print("""EDEN CLI - Control the EDEN daemon

Usage:
  eden status              Show daemon status
  eden start               Start the tick loop
  eden stop                Stop the tick loop
  eden step                Run one tick
  eden entities            List all entities
  eden entity <id>         Show entity details (7D values, phase, gamma)
  eden graph               Show graph topology (nodes + edges)
  eden metrics             Show network metrics
  eden shutdown            Shut down the daemon
  eden help                Show this help

Examples:
  eden status              # Check if daemon is running
  eden start               # Start continuous simulation
  eden entities            # List all AI agents
  eden entity abc-123      # Show details for specific entity
  eden metrics             # Show network-level metrics
""")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="EDEN CLI - Control the EDEN daemon",
        add_help=False
    )
    parser.add_argument("command", nargs='?', default="help",
                       help="Command to execute")
    parser.add_argument("args", nargs='*', help="Command arguments")
    
    args = parser.parse_args()
    
    # Map commands to functions
    commands = {
        "status": cmd_status,
        "start": cmd_start,
        "stop": cmd_stop,
        "step": cmd_step,
        "entities": cmd_entities,
        "entity": cmd_entity,
        "graph": cmd_graph,
        "metrics": cmd_metrics,
        "shutdown": cmd_shutdown,
        "help": cmd_help,
    }
    
    # Special handling for entity command (needs entity_id argument)
    if args.command == "entity":
        if not args.args:
            print("Error: entity command requires entity ID", file=sys.stderr)
            print("Usage: eden entity <entity_id>", file=sys.stderr)
            return 1
        args.entity_id = args.args[0]
    
    # Execute command
    cmd_func = commands.get(args.command)
    if cmd_func:
        return cmd_func(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        print("Run 'eden help' for usage information", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
