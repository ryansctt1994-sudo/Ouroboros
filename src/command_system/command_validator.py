"""
Command Validator

Provides security validation, permission checking, and command sanitization.
"""

from typing import Dict, Any, List, Optional
from enum import Enum

from .nlp_parser import ParsedCommand, CommandIntent, Entity


class ValidationResult(Enum):
    """Validation result status."""
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class PermissionLevel(Enum):
    """Permission levels for command execution."""
    PUBLIC = 0
    USER = 1
    ADMIN = 2
    SYSTEM = 3


class CommandValidator:
    """
    Validates and sanitizes commands before execution.
    
    Provides security checks, permission validation, and resource limit enforcement.
    """
    
    def __init__(
        self,
        max_memory_allocation_mb: int = 1024,
        enable_dangerous_commands: bool = False,
        required_permission_level: PermissionLevel = PermissionLevel.USER
    ):
        """
        Initialize command validator.
        
        Args:
            max_memory_allocation_mb: Maximum allowed memory allocation
            enable_dangerous_commands: Whether to allow potentially dangerous commands
            required_permission_level: Minimum permission level required
        """
        self.max_memory_allocation_mb = max_memory_allocation_mb
        self.enable_dangerous_commands = enable_dangerous_commands
        self.required_permission_level = required_permission_level
        
        # Define permission requirements per intent
        self.intent_permissions = {
            CommandIntent.ALLOCATE_MEMORY: PermissionLevel.USER,
            CommandIntent.DEALLOCATE_MEMORY: PermissionLevel.USER,
            CommandIntent.OPTIMIZE_RESOURCES: PermissionLevel.ADMIN,
            CommandIntent.GET_STATUS: PermissionLevel.PUBLIC,
            CommandIntent.SET_PARAMETER: PermissionLevel.ADMIN,
            CommandIntent.EXECUTE_TASK: PermissionLevel.USER,
            CommandIntent.QUERY_DATA: PermissionLevel.USER,
            CommandIntent.UNKNOWN: PermissionLevel.PUBLIC
        }
        
        # Blacklisted keywords (security)
        self.blacklisted_keywords = [
            'exec', 'eval', 'system', 'shell', 'subprocess',
            '__import__', 'compile', 'globals', 'locals'
        ]
        
        # Validation history
        self.validation_history: List[Dict[str, Any]] = []
    
    def validate(
        self,
        command: ParsedCommand,
        current_permission: PermissionLevel = PermissionLevel.USER
    ) -> Dict[str, Any]:
        """
        Validate parsed command.
        
        Args:
            command: Parsed command to validate
            current_permission: Current user's permission level
            
        Returns:
            Validation result dictionary
        """
        result = {
            'status': ValidationResult.APPROVED,
            'command': command,
            'errors': [],
            'warnings': [],
            'sanitized_entities': []
        }
        
        # Check permission level
        required_perm = self.intent_permissions.get(
            command.intent,
            PermissionLevel.ADMIN
        )
        
        if current_permission.value < required_perm.value:
            result['status'] = ValidationResult.REJECTED
            result['errors'].append(
                f"Insufficient permissions. Required: {required_perm.name}, "
                f"Current: {current_permission.name}"
            )
            self._log_validation(result)
            return result
        
        # Check for blacklisted keywords
        blacklist_check = self._check_blacklist(command.raw_text)
        if not blacklist_check['safe']:
            result['status'] = ValidationResult.REJECTED
            result['errors'].extend(blacklist_check['violations'])
            self._log_validation(result)
            return result
        
        # Intent-specific validation
        if command.intent == CommandIntent.ALLOCATE_MEMORY:
            mem_validation = self._validate_memory_allocation(command)
            if not mem_validation['approved']:
                result['status'] = ValidationResult.REJECTED
                result['errors'].extend(mem_validation['errors'])
        
        elif command.intent == CommandIntent.SET_PARAMETER:
            param_validation = self._validate_parameter_set(command)
            if not param_validation['approved']:
                result['status'] = ValidationResult.REQUIRES_CONFIRMATION
                result['warnings'].extend(param_validation['warnings'])
        
        elif command.intent == CommandIntent.EXECUTE_TASK:
            task_validation = self._validate_task_execution(command)
            if not task_validation['approved']:
                result['status'] = ValidationResult.REJECTED
                result['errors'].extend(task_validation['errors'])
        
        # Sanitize entities
        result['sanitized_entities'] = self._sanitize_entities(command.entities)
        
        # Log validation
        self._log_validation(result)
        
        return result
    
    def _check_blacklist(self, text: str) -> Dict[str, Any]:
        """Check for blacklisted keywords."""
        violations = []
        text_lower = text.lower()
        
        for keyword in self.blacklisted_keywords:
            if keyword in text_lower:
                violations.append(f"Blacklisted keyword detected: {keyword}")
        
        return {
            'safe': len(violations) == 0,
            'violations': violations
        }
    
    def _validate_memory_allocation(self, command: ParsedCommand) -> Dict[str, Any]:
        """Validate memory allocation command."""
        errors = []
        
        # Get memory size entity
        mem_entity = command.get_entity('memory_size')
        
        if mem_entity is None:
            errors.append("Memory allocation amount not specified")
            return {'approved': False, 'errors': errors}
        
        # Check against limits
        if mem_entity.value > self.max_memory_allocation_mb:
            errors.append(
                f"Requested memory ({mem_entity.value:.1f} MB) exceeds "
                f"maximum allowed ({self.max_memory_allocation_mb} MB)"
            )
        
        if mem_entity.value <= 0:
            errors.append("Memory allocation must be positive")
        
        return {
            'approved': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_parameter_set(self, command: ParsedCommand) -> Dict[str, Any]:
        """Validate parameter set command."""
        warnings = []
        
        param_name = command.get_entity('parameter_name')
        param_value = command.get_entity('parameter_value')
        
        if param_name is None:
            return {'approved': False, 'warnings': ['Parameter name not specified']}
        
        # Check for critical parameters
        critical_params = ['max_memory', 'critical_threshold', 'system_limit']
        if param_name.value.lower() in critical_params:
            warnings.append(
                f"Modifying critical parameter: {param_name.value}. "
                "Confirmation required."
            )
        
        return {
            'approved': True,
            'warnings': warnings
        }
    
    def _validate_task_execution(self, command: ParsedCommand) -> Dict[str, Any]:
        """Validate task execution command."""
        errors = []
        
        # Check if dangerous commands are enabled
        if not self.enable_dangerous_commands:
            # List of potentially dangerous task keywords
            dangerous_keywords = ['delete', 'remove', 'drop', 'truncate', 'destroy']
            
            text_lower = command.raw_text.lower()
            for keyword in dangerous_keywords:
                if keyword in text_lower:
                    errors.append(
                        f"Potentially dangerous operation ({keyword}) blocked. "
                        "Enable dangerous commands if intended."
                    )
        
        return {
            'approved': len(errors) == 0,
            'errors': errors
        }
    
    def _sanitize_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Sanitize entities to prevent injection attacks.
        
        Args:
            entities: List of entities to sanitize
            
        Returns:
            List of sanitized entities
        """
        sanitized = []
        
        for entity in entities:
            # Create copy
            clean_entity = Entity(entity.type, entity.value, entity.confidence)
            
            # Sanitize string values
            if isinstance(entity.value, str):
                # Remove potentially dangerous characters
                clean_value = entity.value
                
                # Remove special shell characters
                dangerous_chars = ['$', '`', '|', ';', '&', '>', '<', '\n', '\r']
                for char in dangerous_chars:
                    clean_value = clean_value.replace(char, '')
                
                # Limit length
                max_length = 1000
                if len(clean_value) > max_length:
                    clean_value = clean_value[:max_length]
                
                clean_entity.value = clean_value
            
            sanitized.append(clean_entity)
        
        return sanitized
    
    def _log_validation(self, result: Dict[str, Any]) -> None:
        """Log validation result."""
        log_entry = {
            'status': result['status'].value,
            'intent': result['command'].intent.value if 'command' in result else 'unknown',
            'error_count': len(result['errors']),
            'warning_count': len(result['warnings'])
        }
        
        self.validation_history.append(log_entry)
        
        # Keep only recent history
        if len(self.validation_history) > 1000:
            self.validation_history = self.validation_history[-1000:]
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics."""
        if not self.validation_history:
            return {
                'total_validations': 0,
                'approved': 0,
                'rejected': 0,
                'requires_confirmation': 0
            }
        
        stats = {
            'total_validations': len(self.validation_history),
            'approved': sum(1 for v in self.validation_history if v['status'] == 'approved'),
            'rejected': sum(1 for v in self.validation_history if v['status'] == 'rejected'),
            'requires_confirmation': sum(1 for v in self.validation_history if v['status'] == 'requires_confirmation'),
            'total_errors': sum(v['error_count'] for v in self.validation_history),
            'total_warnings': sum(v['warning_count'] for v in self.validation_history)
        }
        
        return stats
