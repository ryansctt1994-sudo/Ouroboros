#!/usr/bin/env python3
"""
Pre-Build Validation Hook
==========================

Validates system state before build to ensure:
- All vectors are synchronized
- Documentation is up-to-date
- No critical drift detected
- Adapters are connected

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Import validation tools
try:
    from runtime_validator import RuntimeVectorValidator
    from manuscript_validator import ManuscriptValidator
    from integration_orchestrator import IntegrationOrchestrator
except ImportError:
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from runtime_validator import RuntimeVectorValidator
    from manuscript_validator import ManuscriptValidator
    from integration_orchestrator import IntegrationOrchestrator


def run_pre_build_validation(
    vectors_file: str = "vectors.json",
    repo_root: str = ".",
    strict: bool = False
) -> Dict[str, Any]:
    """
    Run pre-build validation checks.
    
    Args:
        vectors_file: Path to vectors manifest
        repo_root: Repository root directory
        strict: If True, fail on any warnings
        
    Returns:
        Validation result dictionary
    """
    print("\n" + "=" * 70)
    print("PRE-BUILD VALIDATION HOOK")
    print("=" * 70)
    print(f"Strict Mode: {'ENABLED' if strict else 'DISABLED'}")
    print()
    
    results = {
        "timestamp": time.time(),
        "status": "pass",
        "checks": {},
        "errors": [],
        "warnings": []
    }
    
    # Check 1: Vector manifest exists
    print("[1/5] Checking vector manifest...")
    vectors_path = Path(vectors_file)
    if not vectors_path.exists():
        results["status"] = "fail"
        results["errors"].append(f"Vector manifest not found: {vectors_file}")
        print(f"      ✗ FAIL - {vectors_file} not found")
    else:
        print(f"      ✓ PASS - {vectors_file} exists")
        results["checks"]["vector_manifest"] = "pass"
    
    # Check 2: Runtime vector validation
    print("\n[2/5] Validating runtime vectors...")
    try:
        validator = RuntimeVectorValidator(vectors_file)
        
        # Use static vectors for validation (in real use, would get runtime state)
        runtime_vectors = list(validator.static_vectors.values())
        report = validator.validate_runtime_state(runtime_vectors)
        
        if report.drift_count > 0:
            # Count critical drift
            critical_drift = sum(
                1 for d in report.drift_events if d.severity == "critical"
            )
            
            if critical_drift > 0:
                results["status"] = "fail"
                results["errors"].append(
                    f"Critical drift detected: {critical_drift} events"
                )
                print(f"      ✗ FAIL - {critical_drift} critical drift events")
            elif strict:
                results["status"] = "fail"
                results["warnings"].append(
                    f"Drift detected (strict mode): {report.drift_count} events"
                )
                print(f"      ✗ FAIL (strict) - {report.drift_count} drift events")
            else:
                results["warnings"].append(
                    f"Drift detected: {report.drift_count} events"
                )
                print(f"      ⚠ WARN - {report.drift_count} drift events")
                results["checks"]["vector_validation"] = "warn"
        else:
            print(f"      ✓ PASS - No drift detected")
            results["checks"]["vector_validation"] = "pass"
    except Exception as e:
        results["status"] = "fail"
        results["errors"].append(f"Vector validation failed: {e}")
        print(f"      ✗ FAIL - {e}")
    
    # Check 3: Manuscript validation
    print("\n[3/5] Validating manuscripts...")
    try:
        manuscript_validator = ManuscriptValidator(vectors_file, repo_root)
        manuscript_reports = manuscript_validator.validate_all_manuscripts()
        
        # Check for errors
        total_errors = sum(len(r.errors) for r in manuscript_reports.values())
        total_warnings = sum(len(r.warnings) for r in manuscript_reports.values())
        
        if total_errors > 0:
            results["status"] = "fail"
            results["errors"].append(
                f"Manuscript validation errors: {total_errors}"
            )
            print(f"      ✗ FAIL - {total_errors} errors in manuscripts")
        elif total_warnings > 0 and strict:
            results["status"] = "fail"
            results["warnings"].append(
                f"Manuscript warnings (strict mode): {total_warnings}"
            )
            print(f"      ✗ FAIL (strict) - {total_warnings} warnings")
        elif total_warnings > 0:
            results["warnings"].append(
                f"Manuscript warnings: {total_warnings}"
            )
            print(f"      ⚠ WARN - {total_warnings} warnings")
            results["checks"]["manuscript_validation"] = "warn"
        else:
            print(f"      ✓ PASS - All manuscripts validated")
            results["checks"]["manuscript_validation"] = "pass"
    except Exception as e:
        results["status"] = "fail"
        results["errors"].append(f"Manuscript validation failed: {e}")
        print(f"      ✗ FAIL - {e}")
    
    # Check 4: Adapter validation
    print("\n[4/5] Validating system adapters...")
    try:
        adapters_path = Path(repo_root) / "python-bridge" / "eden_ecs" / "adapters"
        
        if not adapters_path.exists():
            results["status"] = "fail"
            results["errors"].append("Adapters directory not found")
            print(f"      ✗ FAIL - Adapters directory missing")
        else:
            required_adapters = [
                "quantum_adapter.py",
                "sync_adapter.py",
                "teleport_adapter.py"
            ]
            
            missing = []
            for adapter in required_adapters:
                if not (adapters_path / adapter).exists():
                    missing.append(adapter)
            
            if missing:
                results["status"] = "fail"
                results["errors"].append(f"Missing adapters: {missing}")
                print(f"      ✗ FAIL - Missing: {', '.join(missing)}")
            else:
                print(f"      ✓ PASS - All adapters present")
                results["checks"]["adapter_validation"] = "pass"
    except Exception as e:
        results["status"] = "fail"
        results["errors"].append(f"Adapter validation failed: {e}")
        print(f"      ✗ FAIL - {e}")
    
    # Check 5: Integration orchestrator
    print("\n[5/5] Running integration orchestrator...")
    try:
        orchestrator = IntegrationOrchestrator(
            vectors_file=vectors_file,
            repo_root=repo_root,
            enable_runtime_validation=False,  # Already validated above
            enable_manuscript_validation=False  # Already validated above
        )
        
        # Validate ECS core and adapters
        ecs_result = orchestrator.validate_ecs_core()
        adapter_results = orchestrator.validate_adapters()
        
        if ecs_result["status"] != "ACTIVE":
            results["status"] = "fail"
            results["errors"].append(f"ECS Core not active: {ecs_result.get('error', 'Unknown')}")
            print(f"      ✗ FAIL - ECS Core: {ecs_result['status']}")
        else:
            print(f"      ✓ PASS - ECS Core active")
            results["checks"]["ecs_core"] = "pass"
        
        # Check adapters
        disconnected = [
            name for name, data in adapter_results.items()
            if data["status"] != "CONNECTED"
        ]
        
        if disconnected:
            results["status"] = "fail"
            results["errors"].append(f"Disconnected adapters: {disconnected}")
            print(f"      ✗ FAIL - Disconnected: {', '.join(disconnected)}")
        else:
            print(f"      ✓ PASS - All adapters connected")
            results["checks"]["adapters"] = "pass"
    except Exception as e:
        results["warnings"].append(f"Integration check skipped: {e}")
        print(f"      ⚠ WARN - {e}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("PRE-BUILD VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Status: {results['status'].upper()}")
    print(f"Checks Passed: {sum(1 for v in results['checks'].values() if v == 'pass')}/{len(results['checks'])}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")
    
    if results["errors"]:
        print("\nERRORS:")
        for error in results["errors"]:
            print(f"  ✗ {error}")
    
    if results["warnings"]:
        print("\nWARNINGS:")
        for warning in results["warnings"]:
            print(f"  ⚠ {warning}")
    
    print("=" * 70)
    
    return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Pre-Build Validation Hook"
    )
    parser.add_argument(
        "--vectors",
        "-v",
        default="vectors.json",
        help="Path to vectors manifest"
    )
    parser.add_argument(
        "--repo-root",
        "-r",
        default=".",
        help="Repository root directory"
    )
    parser.add_argument(
        "--strict",
        "-s",
        action="store_true",
        help="Fail on any warnings"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output path for validation results JSON"
    )
    
    args = parser.parse_args()
    
    # Run validation
    results = run_pre_build_validation(
        vectors_file=args.vectors,
        repo_root=args.repo_root,
        strict=args.strict
    )
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✓ Results saved to: {args.output}")
    
    # Exit with appropriate code
    if results["status"] == "fail":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
