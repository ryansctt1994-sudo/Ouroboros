#!/usr/bin/env python3
"""
Manuscript Validation System
=============================

Validates documentation (manuscripts) against live code.
Ensures documentation accuracy, cross-reference integrity,
and integration with OUROBOROS_MANUSCRIPT_DATA.md.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple


@dataclass
class ValidationMarker:
    """Marker indicating validation status of a documentation section."""
    section: str
    status: str  # "validated", "outdated", "missing_reference", "error"
    timestamp: float
    details: str
    references: List[str]


@dataclass
class ManuscriptValidationReport:
    """Complete validation report for manuscript vs code."""
    timestamp: float
    manuscript: str
    total_sections: int
    validated_sections: int
    warnings: List[str]
    errors: List[str]
    markers: List[ValidationMarker]
    cross_references_valid: bool
    integration_status: str  # "synced", "needs_update", "broken"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "manuscript": self.manuscript,
            "total_sections": self.total_sections,
            "validated_sections": self.validated_sections,
            "warnings": self.warnings,
            "errors": self.errors,
            "markers": [asdict(m) for m in self.markers],
            "cross_references_valid": self.cross_references_valid,
            "integration_status": self.integration_status
        }


class ManuscriptValidator:
    """
    Validates documentation against live code and vector manifest.
    
    Features:
    - Documentation vs code validation
    - Cross-reference verification
    - Self-updating manuscripts with validation markers
    - Integration with OUROBOROS_MANUSCRIPT_DATA.md
    """
    
    def __init__(self, vectors_file: str = "vectors.json", repo_root: str = "."):
        """
        Initialize manuscript validator.
        
        Args:
            vectors_file: Path to vectors.json manifest
            repo_root: Repository root directory
        """
        self.vectors_file = Path(vectors_file)
        self.repo_root = Path(repo_root)
        self.vectors: Dict[str, Any] = {}
        self.manuscripts: Dict[str, Path] = {}
        
        # Load vectors
        self._load_vectors()
        
        # Discover manuscripts
        self._discover_manuscripts()
    
    def _load_vectors(self) -> None:
        """Load vector manifest."""
        if not self.vectors_file.exists():
            raise FileNotFoundError(f"Vector manifest not found: {self.vectors_file}")
        
        with open(self.vectors_file, 'r') as f:
            data = json.load(f)
            self.vectors = {v["vector_id"]: v for v in data.get("vectors", [])}
        
        print(f"✓ Loaded {len(self.vectors)} vectors")
    
    def _discover_manuscripts(self) -> None:
        """Discover all manuscript files in repository."""
        manuscript_patterns = [
            "*MANUSCRIPT*.md",
            "*_DATA.md",
            "docs/*.md"
        ]
        
        for pattern in manuscript_patterns:
            for path in self.repo_root.glob(pattern):
                if path.is_file():
                    self.manuscripts[path.name] = path
        
        print(f"✓ Discovered {len(self.manuscripts)} manuscripts")
    
    def _extract_code_references(self, content: str) -> List[str]:
        """Extract code references from markdown content."""
        references = []
        
        # Find code blocks with language identifiers
        code_blocks = re.findall(r'```(\w+)\n(.*?)```', content, re.DOTALL)
        for lang, code in code_blocks:
            if lang in ["python", "py", "rust", "rs"]:
                # Extract function/class names
                if lang in ["python", "py"]:
                    # Python patterns
                    refs = re.findall(r'(?:def|class)\s+(\w+)', code)
                    references.extend(refs)
                elif lang in ["rust", "rs"]:
                    # Rust patterns
                    refs = re.findall(r'(?:fn|struct|enum|impl)\s+(\w+)', code)
                    references.extend(refs)
        
        # Find inline code references
        inline_refs = re.findall(r'`(\w+\.\w+(?:\.\w+)*)`', content)
        references.extend(inline_refs)
        
        # Find file path references
        file_refs = re.findall(r'`([a-zA-Z0-9_/]+\.(?:py|rs|md))`', content)
        references.extend(file_refs)
        
        return list(set(references))  # Deduplicate
    
    def _verify_code_reference(self, reference: str) -> Tuple[bool, str]:
        """
        Verify if a code reference exists in the vector manifest or filesystem.
        
        Args:
            reference: Code reference (e.g., function name, module path)
            
        Returns:
            Tuple of (exists, details)
        """
        # Check if it's a vector ID
        if reference in self.vectors:
            return True, f"Found in vectors: {reference}"
        
        # Check if it's a partial match (e.g., function name)
        for vector_id, vector_data in self.vectors.items():
            if vector_data.get("name") == reference:
                return True, f"Found vector: {vector_id}"
        
        # Check if it's a file path
        file_path = self.repo_root / reference
        if file_path.exists():
            return True, f"File exists: {reference}"
        
        return False, f"Not found: {reference}"
    
    def _parse_manuscript_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse manuscript into logical sections."""
        sections = []
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            # Detect section headers
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections.append({
                        "title": current_section,
                        "content": '\n'.join(current_content),
                        "level": current_section.count('#')
                    })
                
                # Start new section
                current_section = line
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections.append({
                "title": current_section,
                "content": '\n'.join(current_content),
                "level": current_section.count('#')
            })
        
        return sections
    
    def validate_manuscript(self, manuscript_path: Path) -> ManuscriptValidationReport:
        """
        Validate a manuscript against code and cross-references.
        
        Args:
            manuscript_path: Path to manuscript file
            
        Returns:
            ManuscriptValidationReport
        """
        print(f"\nValidating manuscript: {manuscript_path.name}")
        
        # Read manuscript
        with open(manuscript_path, 'r') as f:
            content = f.read()
        
        # Parse sections
        sections = self._parse_manuscript_sections(content)
        
        # Extract all code references
        all_references = self._extract_code_references(content)
        
        # Validation state
        warnings = []
        errors = []
        markers = []
        validated_count = 0
        
        # Validate each section
        for section in sections:
            section_title = section["title"].strip('#').strip()
            section_refs = self._extract_code_references(section["content"])
            
            # Validate references in this section
            invalid_refs = []
            valid_refs = []
            
            for ref in section_refs:
                exists, details = self._verify_code_reference(ref)
                if exists:
                    valid_refs.append(ref)
                else:
                    invalid_refs.append(ref)
            
            # Create validation marker
            if invalid_refs:
                marker = ValidationMarker(
                    section=section_title,
                    status="missing_reference",
                    timestamp=time.time(),
                    details=f"Invalid references: {', '.join(invalid_refs[:3])}",
                    references=section_refs
                )
                warnings.append(f"Section '{section_title}' has invalid references: {invalid_refs[:3]}")
            elif section_refs:
                marker = ValidationMarker(
                    section=section_title,
                    status="validated",
                    timestamp=time.time(),
                    details=f"All {len(valid_refs)} references validated",
                    references=section_refs
                )
                validated_count += 1
            else:
                marker = ValidationMarker(
                    section=section_title,
                    status="validated",
                    timestamp=time.time(),
                    details="No code references (documentation-only section)",
                    references=[]
                )
                validated_count += 1
            
            markers.append(marker)
        
        # Verify cross-references to other manuscripts
        cross_ref_pattern = r'\[([^\]]+)\]\(([^\)]+\.md)\)'
        cross_refs = re.findall(cross_ref_pattern, content)
        cross_refs_valid = True
        
        for ref_text, ref_file in cross_refs:
            ref_path = self.repo_root / ref_file
            if not ref_path.exists():
                # Try relative to manuscript
                ref_path = manuscript_path.parent / ref_file
                if not ref_path.exists():
                    errors.append(f"Broken cross-reference: {ref_file}")
                    cross_refs_valid = False
        
        # Check integration with OUROBOROS_MANUSCRIPT_DATA.md
        manuscript_data_path = self.repo_root / "OUROBOROS_MANUSCRIPT_DATA.md"
        integration_status = "synced"
        
        if manuscript_data_path.exists():
            with open(manuscript_data_path, 'r') as f:
                master_content = f.read()
            
            # Check if this manuscript is referenced
            if manuscript_path.name not in master_content:
                warnings.append(f"{manuscript_path.name} not referenced in OUROBOROS_MANUSCRIPT_DATA.md")
                integration_status = "needs_update"
        else:
            warnings.append("OUROBOROS_MANUSCRIPT_DATA.md not found")
            integration_status = "broken"
        
        # Determine overall integration status
        if errors:
            integration_status = "broken"
        elif warnings and integration_status == "synced":
            integration_status = "needs_update"
        
        # Create report
        report = ManuscriptValidationReport(
            timestamp=time.time(),
            manuscript=manuscript_path.name,
            total_sections=len(sections),
            validated_sections=validated_count,
            warnings=warnings,
            errors=errors,
            markers=markers,
            cross_references_valid=cross_refs_valid,
            integration_status=integration_status
        )
        
        return report
    
    def validate_all_manuscripts(self) -> Dict[str, ManuscriptValidationReport]:
        """Validate all discovered manuscripts."""
        reports = {}
        
        for name, path in self.manuscripts.items():
            try:
                report = self.validate_manuscript(path)
                reports[name] = report
            except Exception as e:
                print(f"✗ Error validating {name}: {e}")
        
        return reports
    
    def print_report(self, report: ManuscriptValidationReport) -> None:
        """Print validation report to console."""
        print("\n" + "=" * 70)
        print(f"MANUSCRIPT VALIDATION: {report.manuscript}")
        print("=" * 70)
        print(f"Status: {report.integration_status.upper()}")
        print(f"Sections: {report.validated_sections}/{report.total_sections} validated")
        print(f"Cross-references: {'✓ Valid' if report.cross_references_valid else '✗ Broken'}")
        print(f"Warnings: {len(report.warnings)}")
        print(f"Errors: {len(report.errors)}")
        print("-" * 70)
        
        if report.errors:
            print("\nERRORS:")
            for error in report.errors:
                print(f"  ✗ {error}")
        
        if report.warnings:
            print("\nWARNINGS:")
            for warning in report.warnings[:10]:
                print(f"  ⚠ {warning}")
            if len(report.warnings) > 10:
                print(f"  ... and {len(report.warnings) - 10} more warnings")
        
        if not report.errors and not report.warnings:
            print("\n✓ Manuscript fully validated!")
        
        print("=" * 70)
    
    def print_summary(self, reports: Dict[str, ManuscriptValidationReport]) -> None:
        """Print summary of all manuscript validations."""
        print("\n" + "=" * 70)
        print("MANUSCRIPT VALIDATION SUMMARY")
        print("=" * 70)
        
        total_manuscripts = len(reports)
        synced = sum(1 for r in reports.values() if r.integration_status == "synced")
        needs_update = sum(1 for r in reports.values() if r.integration_status == "needs_update")
        broken = sum(1 for r in reports.values() if r.integration_status == "broken")
        
        print(f"Total Manuscripts: {total_manuscripts}")
        print(f"  ✓ Synced: {synced}")
        print(f"  ⚠ Needs Update: {needs_update}")
        print(f"  ✗ Broken: {broken}")
        print()
        
        for name, report in sorted(reports.items()):
            status_symbol = {
                "synced": "✓",
                "needs_update": "⚠",
                "broken": "✗"
            }[report.integration_status]
            
            print(f"{status_symbol} {name:40} {report.validated_sections}/{report.total_sections} sections")
        
        print("=" * 70)


def main():
    """Main entry point for manuscript validation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Manuscript Validation System"
    )
    parser.add_argument(
        "--vectors",
        "-v",
        default="vectors.json",
        help="Path to vectors manifest"
    )
    parser.add_argument(
        "--manuscript",
        "-m",
        help="Specific manuscript to validate (default: all)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output path for validation report JSON"
    )
    parser.add_argument(
        "--repo-root",
        "-r",
        default=".",
        help="Repository root directory"
    )
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = ManuscriptValidator(args.vectors, args.repo_root)
    
    # Validate
    if args.manuscript:
        # Validate specific manuscript
        manuscript_path = Path(args.manuscript)
        if not manuscript_path.exists():
            print(f"Error: Manuscript not found: {manuscript_path}")
            sys.exit(1)
        
        report = validator.validate_manuscript(manuscript_path)
        validator.print_report(report)
        
        reports = {manuscript_path.name: report}
    else:
        # Validate all manuscripts
        reports = validator.validate_all_manuscripts()
        
        # Print individual reports
        for report in reports.values():
            validator.print_report(report)
        
        # Print summary
        validator.print_summary(reports)
    
    # Save reports if requested
    if args.output:
        output_data = {
            name: report.to_dict()
            for name, report in reports.items()
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\n✓ Validation reports saved to: {args.output}")
    
    # Exit with appropriate code
    has_errors = any(r.errors for r in reports.values())
    has_broken = any(r.integration_status == "broken" for r in reports.values())
    
    if has_errors or has_broken:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
