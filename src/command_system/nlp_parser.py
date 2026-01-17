"""
NLP Command Parser

Provides natural language processing capabilities for command parsing
using pattern matching, intent recognition, and entity extraction.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class CommandIntent(Enum):
    """Recognized command intents."""
    ALLOCATE_MEMORY = "allocate_memory"
    DEALLOCATE_MEMORY = "deallocate_memory"
    OPTIMIZE_RESOURCES = "optimize_resources"
    GET_STATUS = "get_status"
    SET_PARAMETER = "set_parameter"
    EXECUTE_TASK = "execute_task"
    QUERY_DATA = "query_data"
    UNKNOWN = "unknown"


class Entity:
    """Extracted entity from command."""
    
    def __init__(self, entity_type: str, value: Any, confidence: float = 1.0):
        self.type = entity_type
        self.value = value
        self.confidence = confidence
    
    def __repr__(self):
        return f"Entity({self.type}={self.value}, conf={self.confidence:.2f})"


class ParsedCommand:
    """Parsed command structure."""
    
    def __init__(
        self,
        raw_text: str,
        intent: CommandIntent,
        entities: List[Entity],
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.raw_text = raw_text
        self.intent = intent
        self.entities = entities
        self.confidence = confidence
        self.metadata = metadata or {}
    
    def get_entity(self, entity_type: str) -> Optional[Entity]:
        """Get first entity of given type."""
        for entity in self.entities:
            if entity.type == entity_type:
                return entity
        return None
    
    def get_all_entities(self, entity_type: str) -> List[Entity]:
        """Get all entities of given type."""
        return [e for e in self.entities if e.type == entity_type]
    
    def __repr__(self):
        return f"ParsedCommand(intent={self.intent.value}, entities={len(self.entities)}, conf={self.confidence:.2f})"


class NLPCommandParser:
    """
    Natural Language Processing parser for command interpretation.
    
    Uses pattern matching and rule-based intent recognition with
    entity extraction capabilities.
    """
    
    def __init__(self):
        """Initialize NLP parser with intent patterns."""
        # Intent patterns (regex patterns mapped to intents)
        self.intent_patterns = {
            CommandIntent.ALLOCATE_MEMORY: [
                r'allocate\s+(\d+)\s*(mb|gb|bytes?)',
                r'request\s+(\d+)\s*(mb|gb|bytes?)',
                r'reserve\s+(\d+)\s*(mb|gb|bytes?)',
                r'need\s+(\d+)\s*(mb|gb|bytes?)'
            ],
            CommandIntent.DEALLOCATE_MEMORY: [
                r'(deallocate|free|release)\s+(\d+)\s*(mb|gb|bytes?)',
                r'(deallocate|free|release)\s+memory',
            ],
            CommandIntent.OPTIMIZE_RESOURCES: [
                r'optimize\s+(resources?|memory|performance)',
                r'improve\s+(performance|efficiency)',
                r'reduce\s+(usage|consumption)',
                r'cleanup|clean\s+up'
            ],
            CommandIntent.GET_STATUS: [
                r'(status|state|info|information)',
                r'(show|get|display)\s+(status|state|info)',
                r'how\s+(much|many)',
                r'what\s+is\s+the\s+(status|state)'
            ],
            CommandIntent.SET_PARAMETER: [
                r'set\s+(\w+)\s+to\s+(.+)',
                r'configure\s+(\w+)\s+(.+)',
                r'update\s+(\w+)\s+(.+)'
            ],
            CommandIntent.EXECUTE_TASK: [
                r'(run|execute|start)\s+(.+)',
                r'perform\s+(.+)',
                r'do\s+(.+)'
            ],
            CommandIntent.QUERY_DATA: [
                r'(query|search|find)\s+(.+)',
                r'what\s+(.+)',
                r'which\s+(.+)',
                r'list\s+(.+)'
            ]
        }
        
        # Compile patterns
        self.compiled_patterns = {}
        for intent, patterns in self.intent_patterns.items():
            self.compiled_patterns[intent] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Entity extractors
        self.entity_extractors = {
            'memory_size': self._extract_memory_size,
            'number': self._extract_numbers,
            'parameter': self._extract_parameters,
            'keyword': self._extract_keywords
        }
    
    def parse(self, command_text: str) -> ParsedCommand:
        """
        Parse natural language command.
        
        Args:
            command_text: Raw command text
            
        Returns:
            ParsedCommand object
        """
        # Normalize text
        normalized = command_text.strip()
        
        # Detect intent
        intent, intent_confidence = self._detect_intent(normalized)
        
        # Extract entities based on intent
        entities = self._extract_entities(normalized, intent)
        
        # Calculate overall confidence
        confidence = intent_confidence
        
        # Create metadata
        metadata = {
            'original_length': len(command_text),
            'normalized_length': len(normalized),
            'word_count': len(normalized.split())
        }
        
        return ParsedCommand(
            raw_text=command_text,
            intent=intent,
            entities=entities,
            confidence=confidence,
            metadata=metadata
        )
    
    def _detect_intent(self, text: str) -> Tuple[CommandIntent, float]:
        """
        Detect command intent from text.
        
        Args:
            text: Normalized command text
            
        Returns:
            Tuple of (intent, confidence)
        """
        best_intent = CommandIntent.UNKNOWN
        best_confidence = 0.0
        
        for intent, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                match = pattern.search(text)
                if match:
                    # Calculate confidence based on match quality
                    match_length = len(match.group(0))
                    text_length = len(text)
                    confidence = min(1.0, match_length / text_length * 1.5)
                    
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent
        
        # Minimum confidence threshold
        if best_confidence < 0.3:
            best_intent = CommandIntent.UNKNOWN
            best_confidence = 0.0
        
        return best_intent, best_confidence
    
    def _extract_entities(self, text: str, intent: CommandIntent) -> List[Entity]:
        """Extract entities from text based on intent."""
        entities = []
        
        # Memory size entities (for memory-related intents)
        if intent in [CommandIntent.ALLOCATE_MEMORY, CommandIntent.DEALLOCATE_MEMORY]:
            memory_entities = self._extract_memory_size(text)
            entities.extend(memory_entities)
        
        # Number entities
        number_entities = self._extract_numbers(text)
        entities.extend(number_entities)
        
        # Parameter entities (for SET_PARAMETER intent)
        if intent == CommandIntent.SET_PARAMETER:
            param_entities = self._extract_parameters(text)
            entities.extend(param_entities)
        
        # Keyword entities
        keyword_entities = self._extract_keywords(text)
        entities.extend(keyword_entities)
        
        return entities
    
    def _extract_memory_size(self, text: str) -> List[Entity]:
        """Extract memory size specifications."""
        entities = []
        
        # Pattern: number + unit
        pattern = r'(\d+(?:\.\d+)?)\s*(mb|gb|kb|bytes?|b)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            value_str, unit = match.groups()
            value = float(value_str)
            
            # Normalize to MB
            unit_lower = unit.lower()
            if unit_lower in ['gb', 'g']:
                value_mb = value * 1024
            elif unit_lower in ['kb', 'k']:
                value_mb = value / 1024
            elif unit_lower in ['bytes', 'byte', 'b']:
                value_mb = value / (1024 * 1024)
            else:  # mb, m
                value_mb = value
            
            entities.append(Entity('memory_size', value_mb, confidence=0.95))
        
        return entities
    
    def _extract_numbers(self, text: str) -> List[Entity]:
        """Extract numeric values."""
        entities = []
        
        # Pattern: standalone numbers
        pattern = r'\b(\d+(?:\.\d+)?)\b'
        matches = re.finditer(pattern, text)
        
        for match in matches:
            value = float(match.group(1))
            entities.append(Entity('number', value, confidence=0.8))
        
        return entities
    
    def _extract_parameters(self, text: str) -> List[Entity]:
        """Extract parameter key-value pairs."""
        entities = []
        
        # Pattern: set X to Y / configure X Y
        pattern = r'(?:set|configure|update)\s+(\w+)\s+(?:to\s+)?(.+?)(?:\s+|$)'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            param_name = match.group(1)
            param_value = match.group(2).strip()
            
            entities.append(Entity('parameter_name', param_name, confidence=0.9))
            entities.append(Entity('parameter_value', param_value, confidence=0.85))
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[Entity]:
        """Extract important keywords."""
        # Define important keywords
        keywords = {
            'memory', 'cpu', 'disk', 'network', 'performance',
            'optimize', 'allocate', 'deallocate', 'status',
            'threshold', 'limit', 'usage', 'available'
        }
        
        entities = []
        words = text.lower().split()
        
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word in keywords:
                entities.append(Entity('keyword', clean_word, confidence=0.7))
        
        return entities
    
    def add_intent_pattern(self, intent: CommandIntent, pattern: str) -> None:
        """
        Add new intent pattern.
        
        Args:
            intent: Command intent
            pattern: Regex pattern
        """
        if intent not in self.compiled_patterns:
            self.compiled_patterns[intent] = []
        
        compiled = re.compile(pattern, re.IGNORECASE)
        self.compiled_patterns[intent].append(compiled)
    
    def get_supported_intents(self) -> List[str]:
        """Get list of supported intent names."""
        return [intent.value for intent in CommandIntent]
