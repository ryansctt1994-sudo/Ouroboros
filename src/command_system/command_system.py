"""
Multi-Layered Command System

Integrates NLP parsing, validation, and execution with advanced features.
"""

from typing import Dict, Any, Optional, List
import time

from .nlp_parser import NLPCommandParser, ParsedCommand, CommandIntent
from .command_validator import CommandValidator, ValidationResult, PermissionLevel
from .command_executor import CommandExecutor, ExecutionPriority


class MultiLayeredCommandSystem:
    """
    Comprehensive command system with NLP, validation, and execution.
    
    Provides a complete pipeline from natural language input to execution
    with security, priority handling, and analytics.
    """
    
    def __init__(
        self,
        max_memory_allocation_mb: int = 1024,
        max_concurrent_executions: int = 5,
        enable_async: bool = True,
        default_permission: PermissionLevel = PermissionLevel.USER
    ):
        """
        Initialize multi-layered command system.
        
        Args:
            max_memory_allocation_mb: Maximum allowed memory allocation
            max_concurrent_executions: Maximum concurrent command executions
            enable_async: Enable asynchronous execution
            default_permission: Default permission level for commands
        """
        # Initialize layers
        self.parser = NLPCommandParser()
        self.validator = CommandValidator(
            max_memory_allocation_mb=max_memory_allocation_mb
        )
        self.executor = CommandExecutor(
            max_concurrent=max_concurrent_executions,
            enable_async=enable_async
        )
        
        # Default settings
        self.default_permission = default_permission
        
        # Command history
        self.command_history: List[Dict[str, Any]] = []
        
        # Analytics
        self.total_commands = 0
        self.successful_commands = 0
        self.failed_commands = 0
    
    def process(
        self,
        command_text: str,
        permission: Optional[PermissionLevel] = None,
        priority: ExecutionPriority = ExecutionPriority.MEDIUM,
        execute_async: bool = True
    ) -> Dict[str, Any]:
        """
        Process natural language command through full pipeline.
        
        Args:
            command_text: Natural language command
            permission: User permission level (default: system default)
            priority: Execution priority
            execute_async: Execute asynchronously
            
        Returns:
            Processing result with execution details
        """
        start_time = time.time()
        
        # Use default permission if not specified
        if permission is None:
            permission = self.default_permission
        
        result = {
            'command_text': command_text,
            'timestamp': start_time,
            'parse_result': None,
            'validation_result': None,
            'execution_result': None,
            'success': False
        }
        
        try:
            # Layer 1: Parse with NLP
            parsed = self.parser.parse(command_text)
            result['parse_result'] = {
                'intent': parsed.intent.value,
                'confidence': parsed.confidence,
                'entities': [
                    {'type': e.type, 'value': e.value, 'confidence': e.confidence}
                    for e in parsed.entities
                ]
            }
            
            # Layer 2: Validate
            validation = self.validator.validate(parsed, permission)
            result['validation_result'] = {
                'status': validation['status'].value,
                'errors': validation['errors'],
                'warnings': validation['warnings']
            }
            
            # Check if approved
            if validation['status'] == ValidationResult.REJECTED:
                result['success'] = False
                result['message'] = 'Command rejected: ' + ', '.join(validation['errors'])
                self.failed_commands += 1
                self._log_command(result)
                return result
            
            if validation['status'] == ValidationResult.REQUIRES_CONFIRMATION:
                result['success'] = False
                result['message'] = 'Command requires confirmation: ' + ', '.join(validation['warnings'])
                result['requires_confirmation'] = True
                self._log_command(result)
                return result
            
            # Layer 3: Execute
            if execute_async:
                execution_id = self.executor.submit(parsed, priority)
                result['execution_result'] = {
                    'execution_id': execution_id,
                    'async': True,
                    'status': 'submitted'
                }
                result['success'] = True
                result['message'] = f'Command submitted for execution: {execution_id}'
            else:
                exec_result = self.executor.execute_sync(parsed)
                result['execution_result'] = exec_result
                result['success'] = exec_result.get('success', False)
                result['message'] = exec_result.get('message', 'Command executed')
            
            if result['success']:
                self.successful_commands += 1
            else:
                self.failed_commands += 1
        
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            result['message'] = f'Error processing command: {str(e)}'
            self.failed_commands += 1
        
        finally:
            result['processing_time_ms'] = (time.time() - start_time) * 1000
            self.total_commands += 1
            self._log_command(result)
        
        return result
    
    def process_batch(
        self,
        commands: List[str],
        permission: Optional[PermissionLevel] = None,
        priority: ExecutionPriority = ExecutionPriority.MEDIUM
    ) -> List[Dict[str, Any]]:
        """
        Process multiple commands in batch.
        
        Args:
            commands: List of command texts
            permission: Permission level for all commands
            priority: Priority for all commands
            
        Returns:
            List of processing results
        """
        results = []
        
        for cmd in commands:
            result = self.process(cmd, permission, priority, execute_async=True)
            results.append(result)
        
        return results
    
    def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of asynchronous execution.
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Execution status or None if not found
        """
        return self.executor.get_status(execution_id)
    
    def _log_command(self, result: Dict[str, Any]):
        """Log command processing result."""
        log_entry = {
            'timestamp': result['timestamp'],
            'command_text': result['command_text'][:100],  # Truncate for storage
            'success': result['success'],
            'intent': result['parse_result']['intent'] if result.get('parse_result') else 'unknown',
            'validation_status': result['validation_result']['status'] if result.get('validation_result') else 'unknown'
        }
        
        self.command_history.append(log_entry)
        
        # Keep history bounded
        if len(self.command_history) > 10000:
            self.command_history = self.command_history[-10000:]
    
    def get_analytics(self) -> Dict[str, Any]:
        """
        Get command system analytics.
        
        Returns:
            Analytics data
        """
        # Intent distribution
        intent_counts = {}
        for entry in self.command_history:
            intent = entry.get('intent', 'unknown')
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Success rate
        success_rate = (
            self.successful_commands / self.total_commands
            if self.total_commands > 0 else 0.0
        )
        
        return {
            'total_commands': self.total_commands,
            'successful_commands': self.successful_commands,
            'failed_commands': self.failed_commands,
            'success_rate': success_rate,
            'intent_distribution': intent_counts,
            'validation_stats': self.validator.get_validation_stats(),
            'executor_stats': self.executor.get_stats(),
            'recent_commands_count': len(self.command_history)
        }
    
    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent command history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent command entries
        """
        return self.command_history[-limit:]
    
    def start_executor(self):
        """Start asynchronous executor."""
        self.executor.start()
    
    def stop_executor(self):
        """Stop asynchronous executor."""
        self.executor.stop()
    
    def get_supported_intents(self) -> List[str]:
        """Get list of supported command intents."""
        return self.parser.get_supported_intents()
    
    def add_custom_handler(self, intent: CommandIntent, handler):
        """
        Add custom command handler.
        
        Args:
            intent: Command intent to handle
            handler: Handler function
        """
        self.executor.register_handler(intent, handler)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get complete system state.
        
        Returns:
            System state dictionary
        """
        return {
            'total_commands': self.total_commands,
            'successful_commands': self.successful_commands,
            'failed_commands': self.failed_commands,
            'parser_intents': len(self.parser.get_supported_intents()),
            'executor_running': self.executor.running,
            'default_permission': self.default_permission.name,
            'analytics': self.get_analytics()
        }
