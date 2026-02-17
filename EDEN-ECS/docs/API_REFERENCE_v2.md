# EDEN-ECS v2.0.0 API Reference

Complete API documentation for all v2.0.0 systems and components.

See MIGRATION_GUIDE.md for upgrade instructions.
See PERFORMANCE_REPORT.md for benchmarks.

## Quick Reference

**Core Classes:**
- `World` - Main ECS orchestrator with hybrid timestep
- `TimestepManager` - Time management (FIXED/VARIABLE/HYBRID modes)
- `Entity`, `Component`, `System` - Core ECS primitives

**Enhanced Components (v2.0):**
- `Loyalty` - 4 decay modes, modifiers, trend analysis
- `QuantumCircuit` - 1000+ gates, 5 noise channels, QASM export
- `MemoryLattice` - Tag-based allocation, 6 alignments, defrag

**Performance:** 2-3x faster than v1.0 across all systems.
