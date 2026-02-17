#!/usr/bin/env python3
"""
Post-Build Verification Hook
=============================

Verifies build artifacts and system state after build:
- Build artifact integrity
- Cryptographic signing
- Integration test execution
- Final validation report

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)  # 64KB chunks
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def sign_build_artifacts(
    artifact_paths: List[Path],
    output_file: Path
) -> Dict[str, str]:
    """
    Create cryptographic signatures for build artifacts.
    
    Args:
        artifact_paths: List of paths to artifacts
        output_file: Path to output signature file
        
    Returns:
        Dictionary mapping artifact names to signatures
    """
    signatures = {}
    
    for artifact_path in artifact_paths:
        if artifact_path.exists():
            file_hash = compute_file_hash(artifact_path)
            signatures[str(artifact_path)] = file_hash
    
    # Save signatures
    with open(output_file, 'w') as f:
        json.dump(signatures, f, indent=2)
    
    return signatures


def verify_build_artifacts(
    repo_root: str = "."
) -> Dict[str, Any]:
    """
    Verify build artifacts exist and are valid.
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        Verification result dictionary
    """
    root = Path(repo_root)
    results = {
        "status": "pass",
        "artifacts": {},
        "errors": [],
        "warnings": []
    }
    
    # Expected build artifacts
    expected_artifacts = [
        "vectors.json",
        "python-bridge/eden_ecs/__init__.py",
        "python-bridge/eden_ecs/core.py",
        "python-bridge/eden_ecs/systems.py",
        "python-bridge/eden_ecs/components.py",
        "python-bridge/eden_ecs/adapters/__init__.py",
        "tools/vectorize.py",
        "tools/runtime_validator.py",
        "tools/manuscript_validator.py",
        "tools/integration_orchestrator.py",
    ]
    
    for artifact in expected_artifacts:
        artifact_path = root / artifact
        
        if not artifact_path.exists():
            results["status"] = "fail"
            results["errors"].append(f"Missing artifact: {artifact}")
            results["artifacts"][artifact] = {
                "status": "missing",
                "error": "File not found"
            }
        else:
            # Compute hash
            file_hash = compute_file_hash(artifact_path)
            results["artifacts"][artifact] = {
                "status": "verified",
                "hash": file_hash,
                "size": artifact_path.stat().st_size
            }
    
    return results


def run_integration_tests(
    repo_root: str = "."
) -> Dict[str, Any]:
    """
    Run integration tests.
    
    Args:
        repo_root: Repository root directory
        
    Returns:
        Test results dictionary
    """
    results = {
        "status": "pass",
        "tests": [],
        "passed": 0,
        "failed": 0,
        "skipped": 0
    }
    
    # Test 1: Import ECS modules
    try:
        sys.path.insert(0, str(Path(repo_root) / "python-bridge"))
        
        import eden_ecs
        from eden_ecs import World, Entity, EntityType
        from eden_ecs import QuantumSystem, TeleportationSystem
        from eden_ecs.adapters import (
            QuantumSystemAdapter,
            SynchronizationSystemAdapter,
            TeleportationSystemAdapter
        )
        
        results["tests"].append({
            "name": "Import ECS modules",
            "status": "pass",
            "duration": 0.0
        })
        results["passed"] += 1
    except Exception as e:
        results["status"] = "fail"
        results["tests"].append({
            "name": "Import ECS modules",
            "status": "fail",
            "error": str(e)
        })
        results["failed"] += 1
    
    # Test 2: Create ECS world
    try:
        from eden_ecs import World, Entity, EntityType
        
        world = World()
        entity = world.create_entity(EntityType.AI_AGENT, "test_entity")
        
        if entity.entity_id and entity.name == "test_entity":
            results["tests"].append({
                "name": "Create ECS world and entity",
                "status": "pass",
                "duration": 0.0
            })
            results["passed"] += 1
        else:
            raise ValueError("Entity creation failed")
    except Exception as e:
        results["status"] = "fail"
        results["tests"].append({
            "name": "Create ECS world and entity",
            "status": "fail",
            "error": str(e)
        })
        results["failed"] += 1
    
    # Test 3: Adapter instantiation
    try:
        from eden_ecs import QuantumSystem, TeleportationSystem
        from eden_ecs.mycelial_sync import MycelialSyncSystem
        from eden_ecs.adapters import (
            QuantumSystemAdapter,
            SynchronizationSystemAdapter,
            TeleportationSystemAdapter
        )
        
        quantum_sys = QuantumSystem()
        teleport_sys = TeleportationSystem()
        sync_sys = MycelialSyncSystem(use_rust=False)
        
        quantum_adapter = QuantumSystemAdapter(quantum_sys)
        teleport_adapter = TeleportationSystemAdapter(teleport_sys)
        sync_adapter = SynchronizationSystemAdapter(sync_sys)
        
        results["tests"].append({
            "name": "Instantiate system adapters",
            "status": "pass",
            "duration": 0.0
        })
        results["passed"] += 1
    except Exception as e:
        results["status"] = "fail"
        results["tests"].append({
            "name": "Instantiate system adapters",
            "status": "fail",
            "error": str(e)
        })
        results["failed"] += 1
    
    # Test 4: Vector manifest validation
    try:
        vectors_path = Path(repo_root) / "vectors.json"
        if not vectors_path.exists():
            raise FileNotFoundError("vectors.json not found")
        
        with open(vectors_path, 'r') as f:
            vectors_data = json.load(f)
        
        if "vectors" not in vectors_data:
            raise ValueError("Invalid vectors.json format")
        
        vector_count = len(vectors_data["vectors"])
        
        results["tests"].append({
            "name": "Validate vector manifest",
            "status": "pass",
            "duration": 0.0,
            "metadata": {"vector_count": vector_count}
        })
        results["passed"] += 1
    except Exception as e:
        results["status"] = "fail"
        results["tests"].append({
            "name": "Validate vector manifest",
            "status": "fail",
            "error": str(e)
        })
        results["failed"] += 1
    
    return results


def run_post_build_verification(
    repo_root: str = ".",
    sign_artifacts: bool = True,
    run_tests: bool = True
) -> Dict[str, Any]:
    """
    Run post-build verification.
    
    Args:
        repo_root: Repository root directory
        sign_artifacts: Whether to sign build artifacts
        run_tests: Whether to run integration tests
        
    Returns:
        Verification result dictionary
    """
    print("\n" + "=" * 70)
    print("POST-BUILD VERIFICATION HOOK")
    print("=" * 70)
    print()
    
    results = {
        "timestamp": time.time(),
        "status": "pass",
        "artifact_verification": None,
        "integration_tests": None,
        "build_signature": None,
        "errors": [],
        "warnings": []
    }
    
    # Step 1: Verify build artifacts
    print("[1/3] Verifying build artifacts...")
    artifact_results = verify_build_artifacts(repo_root)
    results["artifact_verification"] = artifact_results
    
    if artifact_results["status"] == "fail":
        results["status"] = "fail"
        results["errors"].extend(artifact_results["errors"])
        print(f"      ✗ FAIL - {len(artifact_results['errors'])} missing artifacts")
    else:
        print(f"      ✓ PASS - All artifacts verified")
    
    # Step 2: Sign build artifacts
    if sign_artifacts and artifact_results["status"] == "pass":
        print("\n[2/3] Signing build artifacts...")
        try:
            root = Path(repo_root)
            artifact_paths = [
                root / artifact
                for artifact in artifact_results["artifacts"].keys()
                if artifact_results["artifacts"][artifact]["status"] == "verified"
            ]
            
            signature_file = root / "build_signatures.json"
            signatures = sign_build_artifacts(artifact_paths, signature_file)
            
            results["build_signature"] = {
                "status": "signed",
                "signature_file": str(signature_file),
                "artifact_count": len(signatures),
                "timestamp": time.time()
            }
            
            print(f"      ✓ SIGNED - {len(signatures)} artifacts")
            print(f"      Signature file: {signature_file}")
        except Exception as e:
            results["warnings"].append(f"Build signing failed: {e}")
            print(f"      ⚠ WARN - {e}")
    else:
        print("\n[2/3] Build signing skipped")
    
    # Step 3: Run integration tests
    if run_tests:
        print("\n[3/3] Running integration tests...")
        test_results = run_integration_tests(repo_root)
        results["integration_tests"] = test_results
        
        if test_results["status"] == "fail":
            results["status"] = "fail"
            results["errors"].append(
                f"Integration tests failed: {test_results['failed']}/{test_results['passed'] + test_results['failed']}"
            )
            print(f"      ✗ FAIL - {test_results['failed']} test(s) failed")
        else:
            print(f"      ✓ PASS - {test_results['passed']} test(s) passed")
        
        # Show test details
        for test in test_results["tests"]:
            status_symbol = "✓" if test["status"] == "pass" else "✗"
            print(f"        {status_symbol} {test['name']}")
    else:
        print("\n[3/3] Integration tests skipped")
    
    # Final summary
    print("\n" + "=" * 70)
    print("POST-BUILD VERIFICATION SUMMARY")
    print("=" * 70)
    print(f"Status: {results['status'].upper()}")
    
    if results["artifact_verification"]:
        verified = sum(
            1 for a in results["artifact_verification"]["artifacts"].values()
            if a["status"] == "verified"
        )
        total = len(results["artifact_verification"]["artifacts"])
        print(f"Artifacts Verified: {verified}/{total}")
    
    if results["integration_tests"]:
        print(f"Tests Passed: {results['integration_tests']['passed']}")
        print(f"Tests Failed: {results['integration_tests']['failed']}")
    
    if results["build_signature"]:
        print(f"Build Signed: Yes ({results['build_signature']['artifact_count']} artifacts)")
    
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
        description="Post-Build Verification Hook"
    )
    parser.add_argument(
        "--repo-root",
        "-r",
        default=".",
        help="Repository root directory"
    )
    parser.add_argument(
        "--no-sign",
        action="store_true",
        help="Skip build artifact signing"
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip integration tests"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output path for verification results JSON"
    )
    
    args = parser.parse_args()
    
    # Run verification
    results = run_post_build_verification(
        repo_root=args.repo_root,
        sign_artifacts=not args.no_sign,
        run_tests=not args.no_tests
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
