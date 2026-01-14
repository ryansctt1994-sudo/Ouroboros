"""
GGCCD Framework - Composite Statements and Deployment Protocols

This module provides the framework for creating composite statements,
lattice constructs, and deployment protocols for GGCCD symbolic encoding.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from .lexicon import (
    Symbol, Glyph, GGCCD_LEXICON, validate_symbol,
    SymbolCategory, get_symbol
)


class ConstructType(Enum):
    """Types of GGCCD constructs"""
    SIMPLE = "simple"              # Single symbol statement
    COMPOSITE = "composite"        # Multiple symbols combined
    LATTICE = "lattice"           # Full lattice structure
    CHAIN = "chain"               # Chained operational sequence
    NESTED = "nested"             # Nested hierarchical construct


@dataclass
class CompositeStatement:
    """A composite statement built from GGCCD symbols and glyphs"""
    symbols: List[str]                    # Ordered list of symbol glyphs
    construct_type: ConstructType         # Type of construct
    context: str = ""                     # Contextual information
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate symbols on initialization"""
        for symbol in self.symbols:
            if not validate_symbol(symbol):
                raise ValueError(f"Invalid symbol in statement: {symbol}")
    
    def to_string(self) -> str:
        """Convert composite statement to string representation"""
        if self.context:
            return " ".join(self.symbols) + f" :: {self.context}"
        return " ".join(self.symbols)
    
    def validate_chainability(self) -> bool:
        """Validate that chained symbols are actually chainable"""
        if self.construct_type != ConstructType.CHAIN:
            return True
        
        for symbol_str in self.symbols:
            sym = get_symbol(symbol_str)
            if isinstance(sym, Glyph) and not sym.chainable:
                return False
        return True
    
    def __str__(self) -> str:
        return self.to_string()


@dataclass
class LatticeNode:
    """A node in a GGCCD lattice construct"""
    symbol: str                           # The symbol at this node
    position: Tuple[float, ...]          # Position in multi-dimensional space
    connections: List[str] = field(default_factory=list)  # Connected node IDs
    state_value: Optional[Any] = None    # Actual state value at this node
    node_id: str = ""                    # Unique identifier
    
    def __post_init__(self):
        if not validate_symbol(self.symbol):
            raise ValueError(f"Invalid symbol for lattice node: {self.symbol}")
        if not self.node_id:
            self.node_id = f"node_{hash(self.position)}_{self.symbol}"


@dataclass
class LatticeConstruct:
    """A complete GGCCD lattice construct with nodes and relationships"""
    nodes: List[LatticeNode] = field(default_factory=list)
    dimensions: int = 3                  # Dimensionality of the lattice
    name: str = ""                       # Name/identifier for the lattice
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: LatticeNode) -> None:
        """Add a node to the lattice"""
        if len(node.position) != self.dimensions:
            raise ValueError(
                f"Node position dimensions {len(node.position)} "
                f"don't match lattice dimensions {self.dimensions}"
            )
        self.nodes.append(node)
    
    def connect_nodes(self, node1_id: str, node2_id: str) -> None:
        """Create a bidirectional connection between two nodes"""
        node1 = self.get_node(node1_id)
        node2 = self.get_node(node2_id)
        
        if node1 and node2:
            if node2_id not in node1.connections:
                node1.connections.append(node2_id)
            if node1_id not in node2.connections:
                node2.connections.append(node1_id)
    
    def get_node(self, node_id: str) -> Optional[LatticeNode]:
        """Retrieve a node by its ID"""
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None
    
    def get_nodes_by_symbol(self, symbol: str) -> List[LatticeNode]:
        """Get all nodes with a specific symbol"""
        return [node for node in self.nodes if node.symbol == symbol]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert lattice to dictionary representation"""
        return {
            "name": self.name,
            "dimensions": self.dimensions,
            "nodes": [
                {
                    "node_id": node.node_id,
                    "symbol": node.symbol,
                    "position": list(node.position),
                    "connections": node.connections,
                    "state_value": node.state_value,
                }
                for node in self.nodes
            ],
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LatticeConstruct':
        """Create lattice from dictionary representation"""
        lattice = cls(
            dimensions=data["dimensions"],
            name=data.get("name", ""),
            metadata=data.get("metadata", {}),
        )
        
        for node_data in data["nodes"]:
            node = LatticeNode(
                symbol=node_data["symbol"],
                position=tuple(node_data["position"]),
                connections=node_data.get("connections", []),
                state_value=node_data.get("state_value"),
                node_id=node_data["node_id"],
            )
            lattice.add_node(node)
        
        return lattice


@dataclass
class DeploymentProtocol:
    """Protocol for deploying and executing GGCCD constructs"""
    construct: CompositeStatement | LatticeConstruct
    execution_order: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    deployment_context: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the deployment protocol"""
        errors = []
        
        # Validate construct type
        if isinstance(self.construct, CompositeStatement):
            if not self.construct.validate_chainability():
                errors.append("Composite statement contains non-chainable symbols in chain")
        
        # Validate execution order
        if isinstance(self.construct, LatticeConstruct):
            for step in self.execution_order:
                if not self.construct.get_node(step):
                    errors.append(f"Execution step references non-existent node: {step}")
        
        return (len(errors) == 0, errors)
    
    def execute_step(self, step_index: int) -> Optional[str]:
        """Execute a single step in the deployment protocol"""
        if step_index >= len(self.execution_order):
            return None
        return self.execution_order[step_index]


# ============================================================================
# ENCODING AND DECODING FUNCTIONS
# ============================================================================

def encode_construct(construct: CompositeStatement | LatticeConstruct) -> str:
    """
    Encode a GGCCD construct to a string representation
    
    For CompositeStatement: Returns the string representation
    For LatticeConstruct: Returns JSON representation
    """
    if isinstance(construct, CompositeStatement):
        return construct.to_string()
    elif isinstance(construct, LatticeConstruct):
        return json.dumps(construct.to_dict(), separators=(',', ':'), sort_keys=True)
    else:
        raise TypeError(f"Unsupported construct type: {type(construct)}")


def decode_construct(encoded: str, construct_type: ConstructType) -> CompositeStatement | LatticeConstruct:
    """
    Decode a GGCCD construct from string representation
    
    Args:
        encoded: String representation of the construct
        construct_type: Type of construct to decode
        
    Returns:
        Decoded construct object
    """
    if construct_type == ConstructType.LATTICE:
        data = json.loads(encoded)
        return LatticeConstruct.from_dict(data)
    else:
        # Parse composite statement
        parts = encoded.split(" :: ")
        symbols = parts[0].split()
        context = parts[1] if len(parts) > 1 else ""
        
        return CompositeStatement(
            symbols=symbols,
            construct_type=construct_type,
            context=context,
        )


def extend_lattice(
    base_lattice: LatticeConstruct,
    extension: LatticeConstruct,
    merge_strategy: str = "append"
) -> LatticeConstruct:
    """
    Extend a lattice construct with additional nodes
    
    Args:
        base_lattice: The base lattice to extend
        extension: The extension lattice to add
        merge_strategy: How to merge ("append", "merge", "overlay")
        
    Returns:
        Extended lattice construct
    """
    if base_lattice.dimensions != extension.dimensions:
        raise ValueError(
            f"Cannot extend lattice: dimension mismatch "
            f"({base_lattice.dimensions} vs {extension.dimensions})"
        )
    
    extended = LatticeConstruct(
        dimensions=base_lattice.dimensions,
        name=f"{base_lattice.name}_extended",
        metadata={**base_lattice.metadata, "extended": True},
    )
    
    # Add all nodes from base lattice
    for node in base_lattice.nodes:
        extended.add_node(node)
    
    if merge_strategy == "append":
        # Simply append all extension nodes
        for node in extension.nodes:
            extended.add_node(node)
    
    elif merge_strategy == "merge":
        # Merge nodes at same positions
        for ext_node in extension.nodes:
            existing = None
            for base_node in extended.nodes:
                if base_node.position == ext_node.position:
                    existing = base_node
                    break
            
            if existing:
                # Merge connections
                for conn in ext_node.connections:
                    if conn not in existing.connections:
                        existing.connections.append(conn)
            else:
                extended.add_node(ext_node)
    
    elif merge_strategy == "overlay":
        # Overlay replaces conflicting nodes
        for ext_node in extension.nodes:
            # Remove any existing node at this position
            extended.nodes = [
                n for n in extended.nodes if n.position != ext_node.position
            ]
            extended.add_node(ext_node)
    
    else:
        raise ValueError(f"Unknown merge strategy: {merge_strategy}")
    
    return extended


def create_ternary_lattice(
    expansion_positions: List[Tuple[float, ...]],
    reconciliation_positions: List[Tuple[float, ...]],
    collapse_positions: List[Tuple[float, ...]],
    dimensions: int = 3,
    name: str = "ternary_lattice"
) -> LatticeConstruct:
    """
    Create a lattice construct with ternary state nodes
    
    Args:
        expansion_positions: Positions for +1 (expansion) nodes
        reconciliation_positions: Positions for 0 (reconciliation) nodes
        collapse_positions: Positions for -1 (collapse) nodes
        dimensions: Dimensionality of the lattice
        name: Name for the lattice
        
    Returns:
        LatticeConstruct with ternary state nodes
    """
    lattice = LatticeConstruct(dimensions=dimensions, name=name)
    
    # Add expansion nodes
    for pos in expansion_positions:
        node = LatticeNode(symbol="+1", position=pos, state_value=1)
        lattice.add_node(node)
    
    # Add reconciliation nodes
    for pos in reconciliation_positions:
        node = LatticeNode(symbol="0", position=pos, state_value=0)
        lattice.add_node(node)
    
    # Add collapse nodes
    for pos in collapse_positions:
        node = LatticeNode(symbol="-1", position=pos, state_value=-1)
        lattice.add_node(node)
    
    return lattice


def apply_operation_chain(
    base_statement: CompositeStatement,
    operations: List[str]
) -> CompositeStatement:
    """
    Apply a chain of operations to a base statement
    
    Args:
        base_statement: Starting composite statement
        operations: List of operation symbols to apply
        
    Returns:
        New composite statement with operations applied
    """
    # Validate all operations are chainable
    for op in operations:
        sym = get_symbol(op)
        if not (isinstance(sym, Glyph) and sym.chainable):
            raise ValueError(f"Operation {op} is not chainable")
    
    new_symbols = base_statement.symbols + operations
    return CompositeStatement(
        symbols=new_symbols,
        construct_type=ConstructType.CHAIN,
        context=base_statement.context,
        metadata={**base_statement.metadata, "chained": True},
    )
