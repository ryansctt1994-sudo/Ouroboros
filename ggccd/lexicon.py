"""
GGCCD Lexicon - Symbols, Glyphs, and True Text Definitions

This module defines the immutable lexicon of GGCCD symbols and glyphs
for encoding multi-dimensional states in lattice constructs.
"""

from typing import Dict, Optional, List, NamedTuple
from dataclasses import dataclass, field
from enum import Enum


class SymbolCategory(Enum):
    """Categories for organizing GGCCD symbols"""
    STATE = "state"              # Ternary state symbols (+1, 0, -1)
    GEOMETRIC = "geometric"      # Geometric constructs (Δ, Ø, Θ)
    OPERATIONAL = "operational"  # Operations (→, ≈, ⊕, ⊗)
    LATTICE = "lattice"         # Lattice-specific glyphs
    SEMANTIC = "semantic"        # Semantic markers
    COMPOSITE = "composite"      # Composite constructs


@dataclass(frozen=True)
class TrueText:
    """Immutable True Text explanation for a symbol or glyph"""
    primary: str                    # Primary meaning/definition
    dimensional_context: str        # Context in multi-dimensional space
    lattice_role: str              # Role in lattice constructs
    operational_semantics: str      # Operational meaning when used
    examples: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        return f"{self.primary}\n{self.dimensional_context}"


@dataclass(frozen=True)
class Symbol:
    """A GGCCD symbol with its immutable properties"""
    glyph: str                      # The actual symbol character(s)
    name: str                       # Human-readable name
    category: SymbolCategory        # Category classification
    true_text: TrueText            # Immutable explanation
    encoding_value: Optional[int] = None  # Numeric encoding for compression
    
    def __str__(self) -> str:
        return f"{self.glyph} ({self.name})"
    
    def __repr__(self) -> str:
        return f"Symbol({self.glyph}, {self.name}, {self.category.value})"


@dataclass(frozen=True)
class Glyph:
    """Extended glyph for advanced GGCCD lattice operations"""
    symbol: str                     # The glyph character
    name: str                       # Glyph name
    category: SymbolCategory        # Category
    true_text: TrueText            # Immutable explanation
    chainable: bool = False         # Can be chained with other glyphs
    precedence: int = 0            # Precedence in composite statements
    
    def __str__(self) -> str:
        return f"{self.symbol} ({self.name})"


# ============================================================================
# GGCCD CORE LEXICON
# ============================================================================

# State Symbols (Ternary)
SYMBOL_EXPANSION = Symbol(
    glyph="+1",
    name="Expansion",
    category=SymbolCategory.STATE,
    true_text=TrueText(
        primary="Positive expansion state in ternary processing",
        dimensional_context="Represents outward flow, being, truth assertion in toroidal manifold",
        lattice_role="Expansion node in lattice, positive geodesic direction",
        operational_semantics="When encountered, triggers expansion operations and positive state transitions",
        examples=["+1(validated_transaction)", "+1::expansion_phase"]
    ),
    encoding_value=1
)

SYMBOL_RECONCILIATION = Symbol(
    glyph="0",
    name="Reconciliation",
    category=SymbolCategory.STATE,
    true_text=TrueText(
        primary="Neutral reconciliation state, Elpis condition",
        dimensional_context="Represents throat condition, neutral bounce, parabolic transition (K≈0)",
        lattice_role="Reconciliation node, requires adjudication or timeout",
        operational_semantics="Triggers escalation protocol, creates adjudication ticket",
        examples=["0(uncertain_state)", "0::awaiting_reconciliation"]
    ),
    encoding_value=0
)

SYMBOL_COLLAPSE = Symbol(
    glyph="-1",
    name="Collapse",
    category=SymbolCategory.STATE,
    true_text=TrueText(
        primary="Negative collapse state in ternary processing",
        dimensional_context="Represents inward flow, non-being, negation, contraction in toroidal manifold",
        lattice_role="Collapse node in lattice, negative geodesic direction",
        operational_semantics="When encountered, triggers collapse operations and negative state transitions",
        examples=["-1(refuted_claim)", "-1::collapse_phase"]
    ),
    encoding_value=-1
)

# Geometric Glyphs
GLYPH_DELTA = Glyph(
    symbol="Δ",
    name="Delta",
    category=SymbolCategory.GEOMETRIC,
    true_text=TrueText(
        primary="Change operator, difference, delta transformation",
        dimensional_context="Represents differential in state space, change vector in lattice",
        lattice_role="Transformation marker between lattice nodes",
        operational_semantics="Calculates or marks state differences, enables delta-check operations",
        examples=["Δ(V_exp, V_obs)", "Δ::state_transition"]
    ),
    chainable=True,
    precedence=5
)

GLYPH_EMPTY = Glyph(
    symbol="Ø",
    name="Empty Set",
    category=SymbolCategory.GEOMETRIC,
    true_text=TrueText(
        primary="Null state, empty construct, void reference",
        dimensional_context="Represents absence, null geodesic, zero-point in manifold",
        lattice_role="Empty node or null reference in lattice",
        operational_semantics="Returns null, triggers empty-state handling",
        examples=["Ø(missing_data)", "Ø::null_construct"]
    ),
    chainable=False,
    precedence=0
)

GLYPH_THETA = Glyph(
    symbol="Θ",
    name="Theta",
    category=SymbolCategory.GEOMETRIC,
    true_text=TrueText(
        primary="Angular parameter, rotation, cyclic phase",
        dimensional_context="Represents toroidal angle θ in parametric equations",
        lattice_role="Phase marker in cyclic lattice constructs",
        operational_semantics="Parametrizes angular position on torus, enables rotational operations",
        examples=["Θ(π/2)", "Θ::cyclic_phase"]
    ),
    chainable=True,
    precedence=3
)

# Operational Glyphs
GLYPH_ARROW = Glyph(
    symbol="→",
    name="Arrow/Implication",
    category=SymbolCategory.OPERATIONAL,
    true_text=TrueText(
        primary="Directional flow, implication, state transition",
        dimensional_context="Represents directed geodesic flow in manifold",
        lattice_role="Directed edge in lattice graph",
        operational_semantics="Indicates state transition, flow direction, or logical implication",
        examples=["state_A → state_B", "+1 → 0 :: transition"]
    ),
    chainable=True,
    precedence=2
)

GLYPH_APPROX = Glyph(
    symbol="≈",
    name="Approximation",
    category=SymbolCategory.OPERATIONAL,
    true_text=TrueText(
        primary="Approximate equality, fuzzy match",
        dimensional_context="Represents epsilon-neighborhood equivalence in state space",
        lattice_role="Soft constraint in lattice relationships",
        operational_semantics="Enables fuzzy matching, approximate validation with tolerance",
        examples=["V_obs ≈ V_exp", "Θ ≈ π :: near_throat"]
    ),
    chainable=True,
    precedence=4
)

GLYPH_XORPLUS = Glyph(
    symbol="⊕",
    name="XOR/Direct Sum",
    category=SymbolCategory.OPERATIONAL,
    true_text=TrueText(
        primary="Exclusive OR, direct sum, symmetric difference",
        dimensional_context="Represents binary XOR or vector space direct sum",
        lattice_role="Combines disjoint lattice components",
        operational_semantics="Performs XOR operation or merges non-overlapping constructs",
        examples=["state_A ⊕ state_B", "lattice_1 ⊕ lattice_2"]
    ),
    chainable=True,
    precedence=6
)

GLYPH_OTIMES = Glyph(
    symbol="⊗",
    name="Tensor Product",
    category=SymbolCategory.OPERATIONAL,
    true_text=TrueText(
        primary="Tensor product, cross product, outer product",
        dimensional_context="Represents tensor product of vector spaces or constructs",
        lattice_role="Creates composite lattice from component lattices",
        operational_semantics="Generates tensor product, enables multi-dimensional composition",
        examples=["V_1 ⊗ V_2", "lattice_A ⊗ lattice_B"]
    ),
    chainable=True,
    precedence=7
)

# Lattice-Specific Glyphs
GLYPH_OMEGA = Glyph(
    symbol="Ω",
    name="Omega/Omega-Hat",
    category=SymbolCategory.LATTICE,
    true_text=TrueText(
        primary="Möbius kernel operator, sacred constant (717)",
        dimensional_context="Represents Ω̂ operator for number-theoretic transformations",
        lattice_role="Kernel operator applied to lattice nodes",
        operational_semantics="Applies Möbius kernel, uses sacred constant Ω=717 for thresholds",
        examples=["Ω̂(n, discretization)", "Ω::threshold_717"]
    ),
    chainable=False,
    precedence=8
)

GLYPH_PHI = Glyph(
    symbol="Φ",
    name="Phi/Golden Ratio",
    category=SymbolCategory.LATTICE,
    true_text=TrueText(
        primary="Golden ratio (1.618...), geometric proportion constant",
        dimensional_context="Represents φ angle or golden ratio scaling in E8 lattice",
        lattice_role="Scaling factor and proportion constant in lattice geometry",
        operational_semantics="Applies golden ratio scaling, φ=1.618033988749895",
        examples=["Φ::scaling_factor", "E_semantic = K · Φ"]
    ),
    chainable=False,
    precedence=8
)

# Semantic Markers
GLYPH_DOUBLE_COLON = Glyph(
    symbol="::",
    name="Scope Separator",
    category=SymbolCategory.SEMANTIC,
    true_text=TrueText(
        primary="Scope separator, namespace delimiter",
        dimensional_context="Separates semantic context from symbol application",
        lattice_role="Delimits hierarchical structure in lattice paths",
        operational_semantics="Separates symbol from context, enables namespaced references",
        examples=["state::context", "+1::expansion_phase"]
    ),
    chainable=True,
    precedence=1
)

GLYPH_PIPE = Glyph(
    symbol="|",
    name="Separator/Or",
    category=SymbolCategory.SEMANTIC,
    true_text=TrueText(
        primary="Separator for hash chains, logical OR",
        dimensional_context="Separates components in canonical hash payloads",
        lattice_role="Separates sequential lattice elements",
        operational_semantics="Hash separator: prev_hash | payload, or logical OR",
        examples=["SHA256(prev_hash | canonical_payload)", "option_A | option_B"]
    ),
    chainable=True,
    precedence=1
)

# Composite Constructs
GLYPH_LAMBDA = Glyph(
    symbol="λ",
    name="Lambda/Tuning Parameter",
    category=SymbolCategory.COMPOSITE,
    true_text=TrueText(
        primary="Tuning parameter, lambda function, eigenvalue",
        dimensional_context="Represents λ parameter in delta-check: d + λ(1 - H_norm)",
        lattice_role="Tuning constant for lattice validation thresholds",
        operational_semantics="Weight parameter for composite calculations",
        examples=["λ=0.3 :: delta_check_weight", "λ_func :: transformation"]
    ),
    chainable=False,
    precedence=3
)

GLYPH_SIGMA = Glyph(
    symbol="Σ",
    name="Sigma/Summation",
    category=SymbolCategory.COMPOSITE,
    true_text=TrueText(
        primary="Summation operator, state space symbol",
        dimensional_context="Represents ternary state space Σ = {+1, 0, -1}",
        lattice_role="Aggregation operator across lattice nodes",
        operational_semantics="Performs summation or denotes complete state space",
        examples=["Σ := {+1, 0, -1}", "Σ(values) :: sum_aggregate"]
    ),
    chainable=False,
    precedence=5
)


# ============================================================================
# GGCCD LEXICON REGISTRY
# ============================================================================

GGCCD_LEXICON: Dict[str, Symbol | Glyph] = {
    # State symbols
    "+1": SYMBOL_EXPANSION,
    "0": SYMBOL_RECONCILIATION,
    "-1": SYMBOL_COLLAPSE,
    
    # Geometric glyphs
    "Δ": GLYPH_DELTA,
    "Ø": GLYPH_EMPTY,
    "Θ": GLYPH_THETA,
    
    # Operational glyphs
    "→": GLYPH_ARROW,
    "≈": GLYPH_APPROX,
    "⊕": GLYPH_XORPLUS,
    "⊗": GLYPH_OTIMES,
    
    # Lattice-specific glyphs
    "Ω": GLYPH_OMEGA,
    "Φ": GLYPH_PHI,
    
    # Semantic markers
    "::": GLYPH_DOUBLE_COLON,
    "|": GLYPH_PIPE,
    
    # Composite constructs
    "λ": GLYPH_LAMBDA,
    "Σ": GLYPH_SIGMA,
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_symbol(glyph: str) -> Optional[Symbol | Glyph]:
    """Retrieve a symbol or glyph from the lexicon by its character(s)"""
    return GGCCD_LEXICON.get(glyph)


def get_glyph(name: str) -> Optional[Symbol | Glyph]:
    """Retrieve a symbol or glyph from the lexicon by its name"""
    for item in GGCCD_LEXICON.values():
        if item.name.lower() == name.lower():
            return item
    return None


def validate_symbol(glyph: str) -> bool:
    """Check if a glyph is valid in the GGCCD lexicon"""
    return glyph in GGCCD_LEXICON


def get_symbols_by_category(category: SymbolCategory) -> List[Symbol | Glyph]:
    """Get all symbols/glyphs of a specific category"""
    return [item for item in GGCCD_LEXICON.values() if item.category == category]


def list_all_symbols() -> Dict[str, str]:
    """List all symbols with their names for reference"""
    return {glyph: item.name for glyph, item in GGCCD_LEXICON.items()}
