"""
Example Usage: GGCCD Framework

This script demonstrates how to use the GGCCD (Global Geometric Construct 
Compression Dictionary) framework for encoding multi-dimensional states using 
symbols, glyphs, and lattice constructs.
"""

from ggccd import (
    Symbol, Glyph, TrueText,
    CompositeStatement, LatticeConstruct, LatticeNode,
    DeploymentProtocol, ConstructType,
    encode_construct, decode_construct, extend_lattice,
    create_ternary_lattice, apply_operation_chain,
    get_symbol, list_all_symbols
)


def example_1_basic_symbols():
    """Example 1: Working with basic GGCCD symbols"""
    print("=" * 70)
    print("Example 1: Basic GGCCD Symbols")
    print("=" * 70)
    
    # Get a symbol from the lexicon
    delta = get_symbol("Δ")
    print(f"\nSymbol: {delta}")
    print(f"Category: {delta.category.value}")
    print(f"True Text (Primary): {delta.true_text.primary}")
    print(f"Operational Semantics: {delta.true_text.operational_semantics}")
    
    # List all available symbols
    print("\n\nAll GGCCD Symbols:")
    all_symbols = list_all_symbols()
    for glyph, name in sorted(all_symbols.items()):
        print(f"  {glyph:4s} -> {name}")


def example_2_composite_statements():
    """Example 2: Creating composite statements"""
    print("\n\n" + "=" * 70)
    print("Example 2: Composite Statements")
    print("=" * 70)
    
    # Create a simple composite statement
    statement1 = CompositeStatement(
        symbols=["Δ", "→", "+1"],
        construct_type=ConstructType.CHAIN,
        context="state_validation"
    )
    print(f"\nStatement 1: {statement1}")
    print(f"Chainability valid: {statement1.validate_chainability()}")
    
    # Create a more complex statement with context
    statement2 = CompositeStatement(
        symbols=["+1", "→", "0", "→", "-1"],
        construct_type=ConstructType.CHAIN,
        context="ternary_cycle_transition"
    )
    print(f"\nStatement 2: {statement2}")
    
    # Encode the statement
    encoded = encode_construct(statement2)
    print(f"Encoded: {encoded}")


def example_3_lattice_constructs():
    """Example 3: Creating lattice constructs"""
    print("\n\n" + "=" * 70)
    print("Example 3: Lattice Constructs")
    print("=" * 70)
    
    # Create a simple lattice
    lattice = LatticeConstruct(dimensions=3, name="test_lattice")
    
    # Add nodes at different positions
    node1 = LatticeNode(symbol="+1", position=(0.0, 0.0, 0.0), state_value=1)
    node2 = LatticeNode(symbol="0", position=(1.0, 0.0, 0.0), state_value=0)
    node3 = LatticeNode(symbol="-1", position=(0.0, 1.0, 0.0), state_value=-1)
    
    lattice.add_node(node1)
    lattice.add_node(node2)
    lattice.add_node(node3)
    
    # Connect nodes
    lattice.connect_nodes(node1.node_id, node2.node_id)
    lattice.connect_nodes(node2.node_id, node3.node_id)
    
    print(f"\nLattice: {lattice.name}")
    print(f"Dimensions: {lattice.dimensions}")
    print(f"Number of nodes: {len(lattice.nodes)}")
    
    for node in lattice.nodes:
        print(f"\n  Node: {node.symbol} at {node.position}")
        print(f"    Connections: {len(node.connections)}")
        print(f"    State value: {node.state_value}")
    
    # Encode lattice to JSON
    encoded = encode_construct(lattice)
    print(f"\nEncoded lattice (JSON): {encoded[:100]}...")


def example_4_ternary_lattice():
    """Example 4: Creating a ternary state lattice"""
    print("\n\n" + "=" * 70)
    print("Example 4: Ternary State Lattice")
    print("=" * 70)
    
    # Create a ternary lattice with expansion, reconciliation, and collapse nodes
    expansion_positions = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0)]
    reconciliation_positions = [(0.5, 0.5, 0.0)]
    collapse_positions = [(-1.0, 0.0, 0.0), (0.0, -1.0, 0.0)]
    
    lattice = create_ternary_lattice(
        expansion_positions=expansion_positions,
        reconciliation_positions=reconciliation_positions,
        collapse_positions=collapse_positions,
        dimensions=3,
        name="ouroboros_ternary_lattice"
    )
    
    print(f"\nTernary Lattice: {lattice.name}")
    print(f"Total nodes: {len(lattice.nodes)}")
    
    # Get nodes by symbol
    expansion_nodes = lattice.get_nodes_by_symbol("+1")
    reconciliation_nodes = lattice.get_nodes_by_symbol("0")
    collapse_nodes = lattice.get_nodes_by_symbol("-1")
    
    print(f"\nExpansion nodes (+1): {len(expansion_nodes)}")
    print(f"Reconciliation nodes (0): {len(reconciliation_nodes)}")
    print(f"Collapse nodes (-1): {len(collapse_nodes)}")


def example_5_operation_chaining():
    """Example 5: Chaining operations"""
    print("\n\n" + "=" * 70)
    print("Example 5: Operation Chaining")
    print("=" * 70)
    
    # Create a base statement
    base = CompositeStatement(
        symbols=["Δ"],
        construct_type=ConstructType.SIMPLE,
        context="delta_operation"
    )
    print(f"\nBase statement: {base}")
    
    # Apply a chain of chainable operations
    operations = ["→", "≈", "Θ"]
    chained = apply_operation_chain(base, operations)
    
    print(f"Chained statement: {chained}")
    print(f"Construct type: {chained.construct_type.value}")


def example_6_deployment_protocol():
    """Example 6: Deployment protocols"""
    print("\n\n" + "=" * 70)
    print("Example 6: Deployment Protocol")
    print("=" * 70)
    
    # Create a lattice
    lattice = create_ternary_lattice(
        expansion_positions=[(1.0, 0.0, 0.0)],
        reconciliation_positions=[(0.0, 0.0, 0.0)],
        collapse_positions=[(-1.0, 0.0, 0.0)],
        dimensions=3,
        name="protocol_test"
    )
    
    # Create deployment protocol
    execution_order = [node.node_id for node in lattice.nodes]
    
    protocol = DeploymentProtocol(
        construct=lattice,
        execution_order=execution_order,
        validation_rules=["validate_ternary_states", "check_connectivity"],
        deployment_context={"mode": "production", "timeout": 717}
    )
    
    # Validate protocol
    is_valid, errors = protocol.validate()
    print(f"\nProtocol valid: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    else:
        print("No errors detected")
    
    # Execute first step
    first_step = protocol.execute_step(0)
    print(f"\nFirst execution step: {first_step}")


def example_7_lattice_extension():
    """Example 7: Extending lattices"""
    print("\n\n" + "=" * 70)
    print("Example 7: Lattice Extension")
    print("=" * 70)
    
    # Create base lattice
    base = create_ternary_lattice(
        expansion_positions=[(1.0, 0.0, 0.0)],
        reconciliation_positions=[(0.0, 0.0, 0.0)],
        collapse_positions=[(-1.0, 0.0, 0.0)],
        dimensions=3,
        name="base_lattice"
    )
    print(f"\nBase lattice nodes: {len(base.nodes)}")
    
    # Create extension lattice
    extension = create_ternary_lattice(
        expansion_positions=[(0.0, 1.0, 0.0)],
        reconciliation_positions=[(0.0, 0.5, 0.0)],
        collapse_positions=[(0.0, -1.0, 0.0)],
        dimensions=3,
        name="extension_lattice"
    )
    print(f"Extension lattice nodes: {len(extension.nodes)}")
    
    # Extend the base lattice
    extended = extend_lattice(base, extension, merge_strategy="append")
    print(f"\nExtended lattice nodes: {len(extended.nodes)}")
    print(f"Extended lattice name: {extended.name}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("GGCCD Framework Examples")
    print("=" * 70)
    
    example_1_basic_symbols()
    example_2_composite_statements()
    example_3_lattice_constructs()
    example_4_ternary_lattice()
    example_5_operation_chaining()
    example_6_deployment_protocol()
    example_7_lattice_extension()
    
    print("\n\n" + "=" * 70)
    print("All examples completed successfully!")
    print("=" * 70 + "\n")
