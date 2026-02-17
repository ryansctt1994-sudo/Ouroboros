"""
Manuscript Validator Module

Validates AIOSPANDORA manuscript structures and ensures compliance
with the defined schema and semantic rules.
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
        
    def add_info(self, message: str) -> None:
        """Add an info message."""
        self.info.append(message)
        
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    def get_summary(self) -> str:
        """Get a summary of validation results."""
        summary = []
        if self.errors:
            summary.append(f"Errors: {len(self.errors)}")
        if self.warnings:
            summary.append(f"Warnings: {len(self.warnings)}")
        if self.info:
            summary.append(f"Info: {len(self.info)}")
        return ", ".join(summary) if summary else "Valid"


class ManuscriptValidator:
    """
    Validator for AIOSPANDORA manuscript structures.
    
    Ensures manuscripts conform to schema requirements and semantic rules
    for consciousness computation and ECS integration.
    """
    
    REQUIRED_FIELDS = ['id', 'type', 'version']
    VALID_TYPES = ['entity', 'component', 'system', 'world']
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the manuscript validator.
        
        Args:
            strict_mode: If True, treat warnings as errors
        """
        self.strict_mode = strict_mode
        
    def validate(self, manuscript: Dict[str, Any]) -> ValidationResult:
        """
        Validate a manuscript structure.
        
        Args:
            manuscript: Dictionary containing manuscript data
            
        Returns:
            ValidationResult object with validation details
        """
        result = ValidationResult()
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in manuscript:
                result.add_error(f"Missing required field: {field}")
        
        # Validate type
        if 'type' in manuscript:
            if manuscript['type'] not in self.VALID_TYPES:
                result.add_error(
                    f"Invalid type: {manuscript['type']}. "
                    f"Must be one of {self.VALID_TYPES}"
                )
        
        # Validate version format
        if 'version' in manuscript:
            if not self._validate_version(manuscript['version']):
                result.add_warning(
                    f"Version format should be semantic (e.g., '1.0.0'): "
                    f"{manuscript['version']}"
                )
        
        # Type-specific validation
        if 'type' in manuscript:
            if manuscript['type'] == 'entity':
                self._validate_entity(manuscript, result)
            elif manuscript['type'] == 'component':
                self._validate_component(manuscript, result)
            elif manuscript['type'] == 'system':
                self._validate_system(manuscript, result)
            elif manuscript['type'] == 'world':
                self._validate_world(manuscript, result)
        
        # If strict mode, convert warnings to errors
        if self.strict_mode and result.warnings:
            for warning in result.warnings:
                result.add_error(f"[STRICT] {warning}")
            result.warnings.clear()
        
        return result
    
    def _validate_version(self, version: Any) -> bool:
        """Validate semantic version format."""
        if not isinstance(version, str):
            return False
        parts = version.split('.')
        return len(parts) == 3 and all(part.isdigit() for part in parts)
    
    def _validate_entity(self, manuscript: Dict[str, Any], result: ValidationResult) -> None:
        """Validate entity-specific fields."""
        if 'components' not in manuscript:
            result.add_warning("Entity should have 'components' field")
        elif not isinstance(manuscript['components'], list):
            result.add_error("Entity 'components' must be a list")
    
    def _validate_component(self, manuscript: Dict[str, Any], result: ValidationResult) -> None:
        """Validate component-specific fields."""
        if 'data' not in manuscript:
            result.add_warning("Component should have 'data' field")
        elif not isinstance(manuscript['data'], dict):
            result.add_error("Component 'data' must be a dictionary")
    
    def _validate_system(self, manuscript: Dict[str, Any], result: ValidationResult) -> None:
        """Validate system-specific fields."""
        if 'priority' in manuscript:
            if not isinstance(manuscript['priority'], (int, float)):
                result.add_error("System 'priority' must be numeric")
        else:
            result.add_info("System has no priority defined (default will be used)")
    
    def _validate_world(self, manuscript: Dict[str, Any], result: ValidationResult) -> None:
        """Validate world-specific fields."""
        if 'entities' not in manuscript:
            result.add_warning("World should have 'entities' field")
        
        if 'systems' not in manuscript:
            result.add_warning("World should have 'systems' field")
    
    def validate_from_json(self, json_string: str) -> Tuple[ValidationResult, Optional[Dict[str, Any]]]:
        """
        Validate manuscript from JSON string.
        
        Args:
            json_string: JSON-formatted manuscript
            
        Returns:
            Tuple of (ValidationResult, parsed manuscript dict or None if invalid JSON)
        """
        result = ValidationResult()
        
        try:
            manuscript = json.loads(json_string)
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON: {str(e)}")
            return result, None
        
        # Validate the parsed manuscript
        validation_result = self.validate(manuscript)
        
        # Merge results
        result.errors.extend(validation_result.errors)
        result.warnings.extend(validation_result.warnings)
        result.info.extend(validation_result.info)
        
        return result, manuscript if result.is_valid() else None
