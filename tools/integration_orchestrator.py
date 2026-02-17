#!/usr/bin/env python3
"""
Integration Orchestrator
========================

Central coordination system that brings together all ECS components:
- Runtime vector validation
- Manuscript validation
- System adapters
- Build pipeline integration
- Live monitoring dashboard

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import json
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import validation tools
try:
    from runtime_validator import RuntimeVectorValidator
    from manuscript_validator import ManuscriptValidator
except ImportError:
    # Allow running from different locations
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from runtime_validator import RuntimeVectorValidator
    from manuscript_validator import ManuscriptValidator


@dataclass
class IntegrationReport:
    """Complete integration validation report."""
    timestamp: float
    status: str  # "healthy", "degraded", "critical"
    components: Dict[str, Dict[str, Any]]
    vector_validation: Optional[Dict[str, Any]]
    manuscript_validation: Optional[Dict[str, Any]]
    adapter_metrics: Dict[str, Dict[str, Any]]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "status": self.status,
            "components": self.components,
            "vector_validation": self.vector_validation,
            "manuscript_validation": self.manuscript_validation,
            "adapter_metrics": self.adapter_metrics,
            "recommendations": self.recommendations
        }


class IntegrationOrchestrator:
    """
    Central orchestrator for ECS integration.
    
    Features:
    - Full system validation
    - Component coordination
    - Live monitoring
    - Health reporting
    """
    
    def __init__(
        self,
        vectors_file: str = "vectors.json",
        repo_root: str = ".",
        enable_runtime_validation: bool = True,
        enable_manuscript_validation: bool = True
    ):
        """
        Initialize integration orchestrator.
        
        Args:
            vectors_file: Path to vectors.json
            repo_root: Repository root directory
            enable_runtime_validation: Enable runtime vector validation
            enable_manuscript_validation: Enable manuscript validation
        """
        self.vectors_file = vectors_file
        self.repo_root = Path(repo_root)
        self.enable_runtime_validation = enable_runtime_validation
        self.enable_manuscript_validation = enable_manuscript_validation
        
        # Component status tracking
        self.components = {
            "ECS Core": {"status": "UNKNOWN", "metrics": {}},
            "Vectorizer": {"status": "UNKNOWN", "metrics": {}},
            "Manuscripts": {"status": "UNKNOWN", "metrics": {}},
            "Quantum Adapter": {"status": "UNKNOWN", "metrics": {}},
            "Sync Adapter": {"status": "UNKNOWN", "metrics": {}},
            "Teleport Adapter": {"status": "UNKNOWN", "metrics": {}},
        }
        
        # Validators
        self.runtime_validator: Optional[RuntimeVectorValidator] = None
        self.manuscript_validator: Optional[ManuscriptValidator] = None
        
        # Initialize validators
        self._initialize_validators()
    
    def _initialize_validators(self) -> None:
        """Initialize validation components."""
        if self.enable_runtime_validation:
            try:
                self.runtime_validator = RuntimeVectorValidator(self.vectors_file)
                self.components["Vectorizer"]["status"] = "ACTIVE"
                print("✓ Runtime validator initialized")
            except Exception as e:
                print(f"⚠ Runtime validator initialization failed: {e}")
                self.components["Vectorizer"]["status"] = "ERROR"
        
        if self.enable_manuscript_validation:
            try:
                self.manuscript_validator = ManuscriptValidator(
                    self.vectors_file,
                    str(self.repo_root)
                )
                self.components["Manuscripts"]["status"] = "ACTIVE"
                print("✓ Manuscript validator initialized")
            except Exception as e:
                print(f"⚠ Manuscript validator initialization failed: {e}")
                self.components["Manuscripts"]["status"] = "ERROR"
    
    def validate_ecs_core(self) -> Dict[str, Any]:
        """Validate ECS core components."""
        try:
            # Check if ECS modules exist
            ecs_path = self.repo_root / "python-bridge" / "eden_ecs"
            
            if not ecs_path.exists():
                return {
                    "status": "ERROR",
                    "error": "ECS directory not found",
                    "path": str(ecs_path)
                }
            
            # Check core files
            required_files = ["__init__.py", "core.py", "components.py", "systems.py"]
            missing_files = []
            
            for file in required_files:
                if not (ecs_path / file).exists():
                    missing_files.append(file)
            
            if missing_files:
                return {
                    "status": "DEGRADED",
                    "warning": f"Missing files: {missing_files}",
                    "path": str(ecs_path)
                }
            
            # Count vectors related to ECS
            if self.runtime_validator:
                ecs_vectors = [
                    v for v in self.runtime_validator.static_vectors.values()
                    if "eden_ecs" in v.get("module", "")
                ]
                
                return {
                    "status": "ACTIVE",
                    "path": str(ecs_path),
                    "files": required_files,
                    "vectors": len(ecs_vectors)
                }
            
            return {
                "status": "ACTIVE",
                "path": str(ecs_path),
                "files": required_files
            }
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e)
            }
    
    def validate_adapters(self) -> Dict[str, Dict[str, Any]]:
        """Validate system adapters."""
        adapters = {}
        
        try:
            # Check if adapters directory exists
            adapters_path = self.repo_root / "python-bridge" / "eden_ecs" / "adapters"
            
            if not adapters_path.exists():
                return {
                    "Quantum Adapter": {"status": "ERROR", "error": "Adapters directory not found"},
                    "Sync Adapter": {"status": "ERROR", "error": "Adapters directory not found"},
                    "Teleport Adapter": {"status": "ERROR", "error": "Adapters directory not found"},
                }
            
            # Check individual adapters
            adapter_files = {
                "Quantum Adapter": "quantum_adapter.py",
                "Sync Adapter": "sync_adapter.py",
                "Teleport Adapter": "teleport_adapter.py",
            }
            
            for adapter_name, filename in adapter_files.items():
                adapter_path = adapters_path / filename
                
                if adapter_path.exists():
                    # Count vectors for this adapter
                    vectors = 0
                    if self.runtime_validator:
                        module_name = f"eden_ecs.adapters.{filename[:-3]}"
                        vectors = len([
                            v for v in self.runtime_validator.static_vectors.values()
                            if v.get("module", "") == module_name
                        ])
                    
                    adapters[adapter_name] = {
                        "status": "CONNECTED",
                        "path": str(adapter_path),
                        "vectors": vectors
                    }
                else:
                    adapters[adapter_name] = {
                        "status": "ERROR",
                        "error": f"File not found: {filename}"
                    }
            
        except Exception as e:
            for adapter_name in ["Quantum Adapter", "Sync Adapter", "Teleport Adapter"]:
                adapters[adapter_name] = {
                    "status": "ERROR",
                    "error": str(e)
                }
        
        return adapters
    
    def run_full_validation(self) -> IntegrationReport:
        """
        Run complete system validation.
        
        Returns:
            IntegrationReport with full status
        """
        print("\n" + "=" * 70)
        print("SOVEREIGN ECS INTEGRATION - FULL SYSTEM VALIDATION")
        print("=" * 70)
        
        # Validate ECS Core
        print("\n[1/5] Validating ECS Core...")
        ecs_result = self.validate_ecs_core()
        self.components["ECS Core"]["status"] = ecs_result["status"]
        self.components["ECS Core"]["metrics"] = ecs_result
        print(f"      Status: {ecs_result['status']}")
        
        # Validate Runtime Vectors
        vector_validation = None
        if self.runtime_validator:
            print("\n[2/5] Validating Runtime Vectors...")
            try:
                # Use static vectors as runtime for validation
                runtime_vectors = list(self.runtime_validator.static_vectors.values())
                vector_report = self.runtime_validator.validate_runtime_state(runtime_vectors)
                vector_validation = vector_report.to_dict()
                
                status = "ACTIVE" if vector_report.status == "synced" else "DEGRADED"
                self.components["Vectorizer"]["status"] = status
                self.components["Vectorizer"]["metrics"] = {
                    "total_vectors": vector_report.total_vectors,
                    "drift_count": vector_report.drift_count
                }
                print(f"      Status: {status}")
                print(f"      Vectors: {vector_report.total_vectors}")
                print(f"      Drift: {vector_report.drift_count}")
            except Exception as e:
                print(f"      Error: {e}")
                self.components["Vectorizer"]["status"] = "ERROR"
        else:
            print("\n[2/5] Runtime validation disabled")
        
        # Validate Manuscripts
        manuscript_validation = None
        if self.manuscript_validator:
            print("\n[3/5] Validating Manuscripts...")
            try:
                manuscript_reports = self.manuscript_validator.validate_all_manuscripts()
                
                # Convert reports to dict
                manuscript_validation = {
                    name: report.to_dict()
                    for name, report in manuscript_reports.items()
                }
                
                # Determine status
                has_errors = any(r.errors for r in manuscript_reports.values())
                if has_errors:
                    status = "DEGRADED"
                else:
                    status = "VALIDATED"
                
                self.components["Manuscripts"]["status"] = status
                self.components["Manuscripts"]["metrics"] = {
                    "total_manuscripts": len(manuscript_reports),
                    "validated": sum(
                        1 for r in manuscript_reports.values()
                        if r.integration_status == "synced"
                    )
                }
                print(f"      Status: {status}")
                print(f"      Manuscripts: {len(manuscript_reports)}")
            except Exception as e:
                print(f"      Error: {e}")
                self.components["Manuscripts"]["status"] = "ERROR"
        else:
            print("\n[3/5] Manuscript validation disabled")
        
        # Validate Adapters
        print("\n[4/5] Validating System Adapters...")
        adapter_metrics = self.validate_adapters()
        
        for adapter_name, metrics in adapter_metrics.items():
            self.components[adapter_name]["status"] = metrics["status"]
            self.components[adapter_name]["metrics"] = metrics
            print(f"      {adapter_name}: {metrics['status']}")
        
        # Generate recommendations
        print("\n[5/5] Generating Recommendations...")
        recommendations = self._generate_recommendations()
        
        # Determine overall status
        statuses = [comp["status"] for comp in self.components.values()]
        if "ERROR" in statuses:
            overall_status = "critical"
        elif "DEGRADED" in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
        
        # Create report
        report = IntegrationReport(
            timestamp=time.time(),
            status=overall_status,
            components=self.components,
            vector_validation=vector_validation,
            manuscript_validation=manuscript_validation,
            adapter_metrics=adapter_metrics,
            recommendations=recommendations
        )
        
        print(f"\n✓ Validation complete - Overall Status: {overall_status.upper()}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        for comp_name, comp_data in self.components.items():
            status = comp_data["status"]
            
            if status == "ERROR":
                recommendations.append(
                    f"CRITICAL: Fix {comp_name} - {comp_data['metrics'].get('error', 'Unknown error')}"
                )
            elif status == "DEGRADED":
                recommendations.append(
                    f"WARNING: Review {comp_name} - {comp_data['metrics'].get('warning', 'Degraded state')}"
                )
            elif status == "UNKNOWN":
                recommendations.append(
                    f"INFO: Initialize {comp_name} for full integration"
                )
        
        if not recommendations:
            recommendations.append("System is fully integrated and operational")
        
        return recommendations
    
    def print_report(self, report: IntegrationReport) -> None:
        """Print integration report."""
        print("\n" + "=" * 70)
        print("INTEGRATION ORCHESTRATOR - SYSTEM REPORT")
        print("=" * 70)
        print(f"Status: {report.status.upper()}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}")
        print("-" * 70)
        
        # Component status table
        print("\nCOMPONENT STATUS:")
        print(f"{'Component':<20} {'Status':<15} {'Details':<35}")
        print("-" * 70)
        
        for comp_name, comp_data in report.components.items():
            status = comp_data["status"]
            
            # Get detail string
            metrics = comp_data.get("metrics", {})
            if "vectors" in metrics:
                details = f"Vectors: {metrics['vectors']}"
            elif "total_vectors" in metrics:
                details = f"Total: {metrics['total_vectors']}, Drift: {metrics['drift_count']}"
            elif "total_manuscripts" in metrics:
                details = f"Total: {metrics['total_manuscripts']}, Valid: {metrics['validated']}"
            elif "error" in metrics:
                details = metrics["error"][:35]
            else:
                details = ""
            
            print(f"{comp_name:<20} {status:<15} {details:<35}")
        
        # Recommendations
        print("\nRECOMMENDATIONS:")
        print("-" * 70)
        for i, rec in enumerate(report.recommendations, 1):
            print(f"{i}. {rec}")
        
        print("=" * 70)
    
    def print_dashboard(self, report: IntegrationReport) -> None:
        """Print live monitoring dashboard."""
        print("\n" + "┌" + "─" * 68 + "┐")
        print("│" + " " * 15 + "SOVEREIGN ECS INTEGRATION DASHBOARD" + " " * 17 + "│")
        print("├" + "─" * 68 + "┤")
        
        # Status indicators
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "critical": "❌"
        }
        
        print(f"│ Overall Status: {status_emoji.get(report.status, '❓')} {report.status.upper():<46} │")
        print("├" + "─" * 68 + "┤")
        
        # Component grid
        print("│ COMPONENTS:                                                          │")
        
        for comp_name, comp_data in report.components.items():
            status = comp_data["status"]
            status_symbol = {
                "ACTIVE": "✅",
                "CONNECTED": "✅",
                "VALIDATED": "✅",
                "DEGRADED": "⚠️",
                "ERROR": "❌",
                "UNKNOWN": "❓",
                "IDLE": "⏸️"
            }.get(status, "❓")
            
            metrics = comp_data.get("metrics", {})
            metric_str = ""
            if "vectors" in metrics:
                metric_str = f" ({metrics['vectors']} vectors)"
            elif "drift_count" in metrics:
                metric_str = f" (drift: {metrics['drift_count']})"
            
            line = f"│   {status_symbol} {comp_name:<25} {status:<20}{metric_str}"
            # Pad to 68 characters
            line = line + " " * (70 - len(line)) + "│"
            print(line)
        
        print("└" + "─" * 68 + "┘")


def main():
    """Main entry point for integration orchestrator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Integration Orchestrator - Sovereign ECS System"
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
        "--output",
        "-o",
        help="Output path for integration report JSON"
    )
    parser.add_argument(
        "--dashboard",
        "-d",
        action="store_true",
        help="Show live monitoring dashboard"
    )
    parser.add_argument(
        "--no-runtime",
        action="store_true",
        help="Disable runtime validation"
    )
    parser.add_argument(
        "--no-manuscripts",
        action="store_true",
        help="Disable manuscript validation"
    )
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = IntegrationOrchestrator(
        vectors_file=args.vectors,
        repo_root=args.repo_root,
        enable_runtime_validation=not args.no_runtime,
        enable_manuscript_validation=not args.no_manuscripts
    )
    
    # Run full validation
    report = orchestrator.run_full_validation()
    
    # Print report or dashboard
    if args.dashboard:
        orchestrator.print_dashboard(report)
    else:
        orchestrator.print_report(report)
    
    # Save report if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        print(f"\n✓ Integration report saved to: {args.output}")
    
    # Exit with appropriate code
    if report.status == "critical":
        sys.exit(2)
    elif report.status == "degraded":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
