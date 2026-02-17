#!/usr/bin/env python3
"""
Runtime-Aware Vector Validator
===============================

Validates ECS runtime state against static vectorization data.
Detects drift, performs cryptographic verification, and enables
self-healing vector synchronization.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import hashlib
import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple


@dataclass
class DriftEvent:
    """Represents a detected drift between runtime and static vectors."""
    timestamp: float
    vector_id: str
    drift_type: str  # "missing", "modified", "added", "signature_changed"
    expected_hash: str
    actual_hash: str
    details: Dict[str, Any]
    severity: str  # "low", "medium", "high", "critical"


@dataclass
class ValidationReport:
    """Complete validation report for runtime vs static vectors."""
    timestamp: float
    total_vectors: int
    validated_vectors: int
    drift_events: List[DriftEvent]
    drift_count: int
    status: str  # "synced", "drift_detected", "critical_drift"
    cryptographic_signature: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "total_vectors": self.total_vectors,
            "validated_vectors": self.validated_vectors,
            "drift_events": [asdict(d) for d in self.drift_events],
            "drift_count": self.drift_count,
            "status": self.status,
            "cryptographic_signature": self.cryptographic_signature
        }


class RuntimeVectorValidator:
    """
    Validates ECS runtime state against static vector manifest.
    
    Features:
    - Real-time state validation
    - Drift detection with cryptographic verification
    - Self-healing recommendations
    - Live monitoring interface
    """
    
    def __init__(self, vectors_file: str = "vectors.json"):
        """
        Initialize validator with static vector manifest.
        
        Args:
            vectors_file: Path to vectors.json manifest
        """
        self.vectors_file = Path(vectors_file)
        self.static_vectors: Dict[str, Any] = {}
        self.drift_events: List[DriftEvent] = []
        self.validation_count = 0
        
        # Load static vectors
        self._load_static_vectors()
    
    def _load_static_vectors(self) -> None:
        """Load static vector manifest from disk."""
        if not self.vectors_file.exists():
            raise FileNotFoundError(f"Vector manifest not found: {self.vectors_file}")
        
        with open(self.vectors_file, 'r') as f:
            data = json.load(f)
            
        # Index by vector_id for fast lookup
        self.static_vectors = {v["vector_id"]: v for v in data.get("vectors", [])}
        
        print(f"✓ Loaded {len(self.static_vectors)} static vectors from {self.vectors_file}")
    
    def _compute_signature(self, data: Dict[str, Any]) -> str:
        """Compute cryptographic signature for validation data."""
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def _compute_vector_hash(self, vector_data: Dict[str, Any]) -> str:
        """Compute hash for a vector (excluding the hash field itself)."""
        # Create copy without hash field
        data = {k: v for k, v in vector_data.items() if k != "hash"}
        return self._compute_signature(data)
    
    def validate_vector(self, runtime_vector: Dict[str, Any]) -> Optional[DriftEvent]:
        """
        Validate a single runtime vector against static manifest.
        
        Args:
            runtime_vector: Runtime vector data with vector_id
            
        Returns:
            DriftEvent if drift detected, None if validated
        """
        vector_id = runtime_vector.get("vector_id")
        if not vector_id:
            return DriftEvent(
                timestamp=time.time(),
                vector_id="unknown",
                drift_type="missing",
                expected_hash="",
                actual_hash="",
                details={"error": "No vector_id in runtime vector"},
                severity="high"
            )
        
        # Check if vector exists in static manifest
        static_vector = self.static_vectors.get(vector_id)
        if not static_vector:
            return DriftEvent(
                timestamp=time.time(),
                vector_id=vector_id,
                drift_type="added",
                expected_hash="",
                actual_hash=self._compute_vector_hash(runtime_vector),
                details={"message": "Vector not found in static manifest"},
                severity="medium"
            )
        
        # Compute hashes
        expected_hash = static_vector.get("hash", "")
        actual_hash = self._compute_vector_hash(runtime_vector)
        
        # Check for drift
        if expected_hash != actual_hash:
            # Detect specific drift types
            drift_details = self._analyze_drift(static_vector, runtime_vector)
            
            return DriftEvent(
                timestamp=time.time(),
                vector_id=vector_id,
                drift_type=drift_details["type"],
                expected_hash=expected_hash,
                actual_hash=actual_hash,
                details=drift_details,
                severity=drift_details.get("severity", "medium")
            )
        
        return None
    
    def _analyze_drift(self, static: Dict[str, Any], runtime: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze specific differences between static and runtime vectors."""
        details = {"type": "modified", "severity": "medium", "changes": []}
        
        # Check signature changes
        if static.get("signature") != runtime.get("signature"):
            details["changes"].append("signature_changed")
            details["type"] = "signature_changed"
            details["severity"] = "high"
            details["old_signature"] = static.get("signature")
            details["new_signature"] = runtime.get("signature")
        
        # Check docstring changes
        if static.get("docstring") != runtime.get("docstring"):
            details["changes"].append("docstring_changed")
        
        # Check line numbers (code moved)
        if static.get("line_start") != runtime.get("line_start"):
            details["changes"].append("location_changed")
        
        # Check dependencies
        static_deps = set(static.get("dependencies", []))
        runtime_deps = set(runtime.get("dependencies", []))
        if static_deps != runtime_deps:
            details["changes"].append("dependencies_changed")
            details["added_deps"] = list(runtime_deps - static_deps)
            details["removed_deps"] = list(static_deps - runtime_deps)
        
        return details
    
    def validate_runtime_state(self, runtime_vectors: List[Dict[str, Any]]) -> ValidationReport:
        """
        Validate complete runtime state against static vectors.
        
        Args:
            runtime_vectors: List of runtime vector data
            
        Returns:
            ValidationReport with complete drift analysis
        """
        self.validation_count += 1
        drift_events = []
        validated_count = 0
        
        # Validate each runtime vector
        for runtime_vector in runtime_vectors:
            drift = self.validate_vector(runtime_vector)
            if drift:
                drift_events.append(drift)
            else:
                validated_count += 1
        
        # Check for missing vectors (in static but not in runtime)
        runtime_ids = {v.get("vector_id") for v in runtime_vectors}
        static_ids = set(self.static_vectors.keys())
        missing_ids = static_ids - runtime_ids
        
        for vector_id in missing_ids:
            drift_events.append(DriftEvent(
                timestamp=time.time(),
                vector_id=vector_id,
                drift_type="missing",
                expected_hash=self.static_vectors[vector_id].get("hash", ""),
                actual_hash="",
                details={"message": "Vector exists in static but not in runtime"},
                severity="critical"
            ))
        
        # Determine overall status
        critical_count = sum(1 for d in drift_events if d.severity == "critical")
        high_count = sum(1 for d in drift_events if d.severity == "high")
        
        if critical_count > 0:
            status = "critical_drift"
        elif len(drift_events) > 0:
            status = "drift_detected"
        else:
            status = "synced"
        
        # Create report
        report = ValidationReport(
            timestamp=time.time(),
            total_vectors=len(self.static_vectors),
            validated_vectors=validated_count,
            drift_events=drift_events,
            drift_count=len(drift_events),
            status=status,
            cryptographic_signature=self._compute_signature({
                "validation_count": self.validation_count,
                "timestamp": time.time(),
                "drift_count": len(drift_events)
            })
        )
        
        # Store drift events
        self.drift_events.extend(drift_events)
        
        return report
    
    def get_self_healing_recommendations(self, report: ValidationReport) -> List[Dict[str, Any]]:
        """
        Generate self-healing recommendations based on drift events.
        
        Args:
            report: Validation report
            
        Returns:
            List of recommended actions
        """
        recommendations = []
        
        for drift in report.drift_events:
            if drift.drift_type == "missing":
                recommendations.append({
                    "vector_id": drift.vector_id,
                    "action": "restore",
                    "priority": "high" if drift.severity == "critical" else "medium",
                    "description": f"Restore missing vector: {drift.vector_id}",
                    "steps": [
                        "Check if code was deleted",
                        "Verify git history",
                        "Restore from backup or regenerate"
                    ]
                })
            
            elif drift.drift_type == "signature_changed":
                recommendations.append({
                    "vector_id": drift.vector_id,
                    "action": "re-vectorize",
                    "priority": "high",
                    "description": f"Re-vectorize changed function: {drift.vector_id}",
                    "steps": [
                        "Run vectorization tool on modified file",
                        "Update vectors.json manifest",
                        "Verify new signature"
                    ]
                })
            
            elif drift.drift_type == "added":
                recommendations.append({
                    "vector_id": drift.vector_id,
                    "action": "add_to_manifest",
                    "priority": "low",
                    "description": f"Add new vector to manifest: {drift.vector_id}",
                    "steps": [
                        "Run vectorization tool",
                        "Update vectors.json",
                        "Validate new vector"
                    ]
                })
        
        return recommendations
    
    def print_report(self, report: ValidationReport) -> None:
        """Print validation report to console."""
        print("\n" + "=" * 70)
        print("RUNTIME VECTOR VALIDATION REPORT")
        print("=" * 70)
        print(f"Status: {report.status.upper()}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}")
        print(f"Total Vectors: {report.total_vectors}")
        print(f"Validated: {report.validated_vectors}")
        print(f"Drift Events: {report.drift_count}")
        print(f"Signature: {report.cryptographic_signature[:16]}...")
        print("-" * 70)
        
        if report.drift_count == 0:
            print("✓ All vectors validated successfully!")
            print("✓ No drift detected - system is synchronized")
        else:
            print(f"⚠ {report.drift_count} drift event(s) detected:")
            print()
            
            # Group by severity
            by_severity = {}
            for drift in report.drift_events:
                by_severity.setdefault(drift.severity, []).append(drift)
            
            for severity in ["critical", "high", "medium", "low"]:
                events = by_severity.get(severity, [])
                if events:
                    print(f"  {severity.upper()} ({len(events)} events):")
                    for drift in events[:5]:  # Show first 5
                        print(f"    • {drift.vector_id}")
                        print(f"      Type: {drift.drift_type}")
                        if drift.details.get("changes"):
                            print(f"      Changes: {', '.join(drift.details['changes'])}")
                    if len(events) > 5:
                        print(f"    ... and {len(events) - 5} more")
                    print()
        
        print("=" * 70)


def main():
    """Main entry point for runtime validation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Runtime-Aware Vector Validator for ECS"
    )
    parser.add_argument(
        "--vectors",
        "-v",
        default="vectors.json",
        help="Path to static vectors manifest"
    )
    parser.add_argument(
        "--runtime-vectors",
        "-r",
        help="Path to runtime vectors JSON (for testing)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output path for validation report JSON"
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = RuntimeVectorValidator(args.vectors)
    
    # For testing, allow loading runtime vectors from file
    if args.runtime_vectors:
        with open(args.runtime_vectors, 'r') as f:
            runtime_data = json.load(f)
            runtime_vectors = runtime_data.get("vectors", [])
    else:
        # In production, would get runtime vectors from live ECS state
        print("Note: No runtime vectors provided, using static vectors for validation")
        runtime_vectors = list(validator.static_vectors.values())
    
    # Validate
    report = validator.validate_runtime_state(runtime_vectors)
    
    # Print report
    validator.print_report(report)
    
    # Show recommendations if drift detected
    if report.drift_count > 0:
        print("\nSELF-HEALING RECOMMENDATIONS:")
        print("-" * 70)
        recommendations = validator.get_self_healing_recommendations(report)
        for i, rec in enumerate(recommendations[:10], 1):
            print(f"\n{i}. [{rec['priority'].upper()}] {rec['description']}")
            print(f"   Action: {rec['action']}")
            print(f"   Steps:")
            for step in rec['steps']:
                print(f"     - {step}")
        if len(recommendations) > 10:
            print(f"\n... and {len(recommendations) - 10} more recommendations")
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n✓ Validation report saved to: {args.output}")
    
    # Exit with appropriate code
    if report.status == "critical_drift":
        sys.exit(2)
    elif report.status == "drift_detected":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
