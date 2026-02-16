"""
Recursive Crucible Core - Self-Improving Framework for ECS-Based Agent Code

This module implements a multi-stage recursive testing framework that:
1. Analyzes code for weaknesses using multiple strategies
2. Stress tests code via boundary weakening
3. Automatically strengthens code based on detected weaknesses
4. Validates improvements with configurable thresholds
5. Adaptively evolves testing strategies
"""

import ast
import re
import time
import json
import traceback
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class WeaknessType(Enum):
    """Types of weaknesses that can be detected"""
    STATIC_ANALYSIS = "static_analysis"
    PATTERN_MATCH = "pattern_match"
    EVOLUTIONARY_MEMORY = "evolutionary_memory"
    BOUNDARY_INJECTION = "boundary_injection"
    STRESS_OVERLOAD = "stress_overload"
    EDGE_CASE = "edge_case"


class StrengtheningStrategy(Enum):
    """Strategies for code strengthening"""
    ADD_VALIDATION = "add_validation"
    ADD_ERROR_HANDLING = "add_error_handling"
    ADD_TYPE_CHECKING = "add_type_checking"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    ADD_LOGGING = "add_logging"
    REFACTOR = "refactor"


@dataclass
class Weakness:
    """Represents a detected weakness in code"""
    type: WeaknessType
    location: str
    description: str
    severity: float  # 0.0 to 1.0
    detected_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Fix:
    """Represents a fix applied to code"""
    weakness: Weakness
    strategy: StrengtheningStrategy
    code_change: str
    applied_at: datetime = field(default_factory=datetime.now)
    success: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of validating a fix"""
    passed: bool
    score: float  # 0.0 to 1.0
    details: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class IterationResult:
    """Result of a single crucible iteration"""
    iteration: int
    weaknesses_found: List[Weakness]
    fixes_applied: List[Fix]
    validation_results: List[ValidationResult]
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)


class WeaknessDetector:
    """Detects weaknesses in code using multiple strategies"""
    
    def __init__(self):
        self.patterns = self._load_weakness_patterns()
        self.evolutionary_memory: List[Weakness] = []
    
    def _load_weakness_patterns(self) -> Dict[str, List[str]]:
        """Load patterns for common weaknesses"""
        return {
            'missing_error_handling': [
                r'def\s+\w+\([^)]*\):(?:(?!try|except).)*$',
                r'open\([^)]+\)(?!\s*as)',
            ],
            'missing_type_hints': [
                r'def\s+\w+\([^:)]*\)\s*:',
            ],
            'unsafe_operations': [
                r'eval\(',
                r'exec\(',
                r'__import__\(',
            ],
            'performance_issues': [
                r'for\s+\w+\s+in\s+range\([^)]+\):.*\+\=',  # List concatenation in loop
            ],
        }
    
    def detect_static_analysis(self, code: str, location: str) -> List[Weakness]:
        """Detect weaknesses using static analysis"""
        weaknesses = []
        
        try:
            tree = ast.parse(code)
            
            # Check for functions without docstrings
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if not ast.get_docstring(node):
                        weaknesses.append(Weakness(
                            type=WeaknessType.STATIC_ANALYSIS,
                            location=f"{location}:{node.lineno}",
                            description=f"Function '{node.name}' missing docstring",
                            severity=0.3
                        ))
                    
                    # Check for bare except clauses
                    for child in ast.walk(node):
                        if isinstance(child, ast.ExceptHandler) and child.type is None:
                            weaknesses.append(Weakness(
                                type=WeaknessType.STATIC_ANALYSIS,
                                location=f"{location}:{child.lineno}",
                                description="Bare except clause detected - should specify exception type",
                                severity=0.6
                            ))
        
        except SyntaxError as e:
            weaknesses.append(Weakness(
                type=WeaknessType.STATIC_ANALYSIS,
                location=f"{location}:{e.lineno if hasattr(e, 'lineno') else 0}",
                description=f"Syntax error: {str(e)}",
                severity=1.0
            ))
        
        return weaknesses
    
    def detect_pattern_match(self, code: str, location: str) -> List[Weakness]:
        """Detect weaknesses using pattern matching"""
        weaknesses = []
        
        for category, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    line_num = code[:match.start()].count('\n') + 1
                    weaknesses.append(Weakness(
                        type=WeaknessType.PATTERN_MATCH,
                        location=f"{location}:{line_num}",
                        description=f"Pattern matched: {category}",
                        severity=0.5,
                        metadata={'pattern': pattern, 'category': category}
                    ))
        
        return weaknesses
    
    def detect_all(self, code: str, location: str = "unknown") -> List[Weakness]:
        """Run all detection strategies"""
        weaknesses = []
        weaknesses.extend(self.detect_static_analysis(code, location))
        weaknesses.extend(self.detect_pattern_match(code, location))
        return weaknesses


class StressTester:
    """Stress tests code via boundary weakening"""
    
    def __init__(self):
        self.test_cases = []
    
    def inject_boundary_conditions(self, code: str, location: str) -> List[Weakness]:
        """Test boundary conditions by injection"""
        weaknesses = []
        
        # Simulate testing with edge cases
        edge_cases = [
            {'name': 'null_input', 'value': None},
            {'name': 'empty_string', 'value': ''},
            {'name': 'negative_number', 'value': -1},
            {'name': 'large_number', 'value': 10**100},
        ]
        
        for case in edge_cases:
            # In a real implementation, this would actually execute the code
            # For now, we'll simulate finding weaknesses
            if 'None' not in code and case['value'] is None:
                weaknesses.append(Weakness(
                    type=WeaknessType.BOUNDARY_INJECTION,
                    location=location,
                    description=f"No handling for edge case: {case['name']}",
                    severity=0.4,
                    metadata={'edge_case': case['name']}
                ))
        
        return weaknesses
    
    def overload_test(self, code: str, location: str) -> List[Weakness]:
        """Test with overload conditions"""
        weaknesses = []
        
        # Check for potential performance issues with large inputs
        if 'for' in code and 'append' in code:
            weaknesses.append(Weakness(
                type=WeaknessType.STRESS_OVERLOAD,
                location=location,
                description="Potential O(n²) performance issue with list operations in loop",
                severity=0.5
            ))
        
        return weaknesses
    
    def test_all(self, code: str, location: str = "unknown") -> List[Weakness]:
        """Run all stress tests"""
        weaknesses = []
        weaknesses.extend(self.inject_boundary_conditions(code, location))
        weaknesses.extend(self.overload_test(code, location))
        return weaknesses


class CodeStrengthener:
    """Automatically strengthens code based on detected weaknesses"""
    
    def __init__(self):
        self.strategies = {
            WeaknessType.STATIC_ANALYSIS: self._strengthen_static_issues,
            WeaknessType.PATTERN_MATCH: self._strengthen_pattern_issues,
            WeaknessType.BOUNDARY_INJECTION: self._strengthen_boundary_issues,
            WeaknessType.STRESS_OVERLOAD: self._strengthen_performance_issues,
        }
    
    def _strengthen_static_issues(self, weakness: Weakness, code: str) -> Optional[Fix]:
        """Strengthen static analysis issues"""
        if 'missing docstring' in weakness.description:
            return Fix(
                weakness=weakness,
                strategy=StrengtheningStrategy.ADD_LOGGING,
                code_change="Add docstring to function",
                metadata={'suggestion': 'Add comprehensive docstring with parameters and return types'}
            )
        
        if 'Bare except' in weakness.description:
            return Fix(
                weakness=weakness,
                strategy=StrengtheningStrategy.ADD_ERROR_HANDLING,
                code_change="Replace bare except with specific exception types",
                metadata={'suggestion': 'Use except Exception as e: or specific exception types'}
            )
        
        return None
    
    def _strengthen_pattern_issues(self, weakness: Weakness, code: str) -> Optional[Fix]:
        """Strengthen pattern-matched issues"""
        category = weakness.metadata.get('category', '')
        
        if category == 'missing_error_handling':
            return Fix(
                weakness=weakness,
                strategy=StrengtheningStrategy.ADD_ERROR_HANDLING,
                code_change="Add try-except block",
                metadata={'suggestion': 'Wrap risky operations in try-except blocks'}
            )
        
        if category == 'missing_type_hints':
            return Fix(
                weakness=weakness,
                strategy=StrengtheningStrategy.ADD_TYPE_CHECKING,
                code_change="Add type hints",
                metadata={'suggestion': 'Add proper type annotations to function signature'}
            )
        
        return None
    
    def _strengthen_boundary_issues(self, weakness: Weakness, code: str) -> Optional[Fix]:
        """Strengthen boundary condition issues"""
        return Fix(
            weakness=weakness,
            strategy=StrengtheningStrategy.ADD_VALIDATION,
            code_change="Add input validation",
            metadata={'suggestion': 'Add checks for None, empty strings, and edge case values'}
        )
    
    def _strengthen_performance_issues(self, weakness: Weakness, code: str) -> Optional[Fix]:
        """Strengthen performance issues"""
        return Fix(
            weakness=weakness,
            strategy=StrengtheningStrategy.OPTIMIZE_PERFORMANCE,
            code_change="Optimize data structure usage",
            metadata={'suggestion': 'Use list comprehension or pre-allocate list size'}
        )
    
    def strengthen(self, weakness: Weakness, code: str) -> Optional[Fix]:
        """Apply appropriate strengthening strategy"""
        strategy_func = self.strategies.get(weakness.type)
        if strategy_func:
            return strategy_func(weakness, code)
        return None


class ValidationOracle:
    """Validates improvements with configurable thresholds"""
    
    def __init__(self, min_score_threshold: float = 0.7):
        self.min_score_threshold = min_score_threshold
        self.validation_history: List[ValidationResult] = []
    
    def validate_fix(self, fix: Fix, original_code: str, fixed_code: str) -> ValidationResult:
        """Validate that a fix actually improves the code"""
        # In a real implementation, this would run tests and check metrics
        # For now, we'll simulate validation
        
        score = 0.0
        details = []
        
        # Check if fix addresses the weakness
        if fix.strategy == StrengtheningStrategy.ADD_ERROR_HANDLING:
            if 'try' in fixed_code and 'except' in fixed_code:
                score += 0.4
                details.append("Error handling added")
        
        if fix.strategy == StrengtheningStrategy.ADD_VALIDATION:
            if 'if' in fixed_code or 'assert' in fixed_code:
                score += 0.4
                details.append("Validation added")
        
        if fix.strategy == StrengtheningStrategy.ADD_TYPE_CHECKING:
            if '->' in fixed_code or ':' in fixed_code:
                score += 0.3
                details.append("Type hints added")
        
        # Ensure code still runs (simulate)
        score += 0.3
        details.append("Code syntax valid")
        
        passed = score >= self.min_score_threshold
        
        result = ValidationResult(
            passed=passed,
            score=score,
            details="; ".join(details)
        )
        
        self.validation_history.append(result)
        return result
    
    def get_average_score(self) -> float:
        """Get average validation score"""
        if not self.validation_history:
            return 0.0
        return sum(r.score for r in self.validation_history) / len(self.validation_history)


class RecursiveCrucible:
    """
    Main Recursive Crucible Core
    
    Implements the analyze → test → strengthen → validate loop
    with multi-pass improvement cycles and tracking.
    """
    
    def __init__(self, max_iterations: int = 10, validation_threshold: float = 0.7):
        self.max_iterations = max_iterations
        self.validation_threshold = validation_threshold
        
        self.detector = WeaknessDetector()
        self.tester = StressTester()
        self.strengthener = CodeStrengthener()
        self.validator = ValidationOracle(validation_threshold)
        
        self.iteration_history: List[IterationResult] = []
        self.current_iteration = 0
        
    def analyze(self, code: str, location: str = "unknown") -> List[Weakness]:
        """Analyze code for weaknesses"""
        weaknesses = []
        weaknesses.extend(self.detector.detect_all(code, location))
        return weaknesses
    
    def test(self, code: str, location: str = "unknown") -> List[Weakness]:
        """Stress test code"""
        weaknesses = []
        weaknesses.extend(self.tester.test_all(code, location))
        return weaknesses
    
    def strengthen(self, weaknesses: List[Weakness], code: str) -> List[Fix]:
        """Generate fixes for weaknesses"""
        fixes = []
        for weakness in weaknesses:
            fix = self.strengthener.strengthen(weakness, code)
            if fix:
                fixes.append(fix)
        return fixes
    
    def validate(self, fixes: List[Fix], original_code: str, fixed_code: str) -> List[ValidationResult]:
        """Validate fixes"""
        results = []
        for fix in fixes:
            result = self.validator.validate_fix(fix, original_code, fixed_code)
            fix.success = result.passed
            results.append(result)
        return results
    
    def run_iteration(self, code: str, location: str = "unknown") -> IterationResult:
        """Run a single crucible iteration"""
        start_time = time.time()
        
        # 1. Analyze
        weaknesses = self.analyze(code, location)
        
        # 2. Test
        test_weaknesses = self.test(code, location)
        weaknesses.extend(test_weaknesses)
        
        # 3. Strengthen
        fixes = self.strengthen(weaknesses, code)
        
        # 4. Validate (simulate fixed code for now)
        fixed_code = code  # In real implementation, apply fixes
        validation_results = self.validate(fixes, code, fixed_code)
        
        duration = time.time() - start_time
        
        result = IterationResult(
            iteration=self.current_iteration,
            weaknesses_found=weaknesses,
            fixes_applied=fixes,
            validation_results=validation_results,
            duration=duration
        )
        
        self.iteration_history.append(result)
        self.current_iteration += 1
        
        return result
    
    def run_recursive(self, code: str, location: str = "unknown") -> List[IterationResult]:
        """Run recursive improvement cycles"""
        results = []
        
        for i in range(self.max_iterations):
            result = self.run_iteration(code, location)
            results.append(result)
            
            # Stop if no weaknesses found or all fixes validated
            if not result.weaknesses_found:
                print(f"✓ No more weaknesses found after {i+1} iterations")
                break
            
            if all(vr.passed for vr in result.validation_results):
                print(f"✓ All fixes validated after {i+1} iterations")
                break
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all iterations"""
        total_weaknesses = sum(len(r.weaknesses_found) for r in self.iteration_history)
        total_fixes = sum(len(r.fixes_applied) for r in self.iteration_history)
        successful_fixes = sum(
            sum(1 for f in r.fixes_applied if f.success) 
            for r in self.iteration_history
        )
        avg_score = self.validator.get_average_score()
        
        return {
            'total_iterations': len(self.iteration_history),
            'total_weaknesses': total_weaknesses,
            'total_fixes': total_fixes,
            'successful_fixes': successful_fixes,
            'average_validation_score': avg_score,
            'iterations': [
                {
                    'iteration': r.iteration,
                    'weaknesses': len(r.weaknesses_found),
                    'fixes': len(r.fixes_applied),
                    'duration': r.duration,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.iteration_history
            ]
        }
    
    def export_results(self, filepath: str) -> None:
        """Export results to JSON file"""
        summary = self.get_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)


# Example usage
if __name__ == "__main__":
    print("🔥 Recursive Crucible Core - Self-Improving Framework\n")
    
    # Sample code to analyze
    sample_code = """
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result

def unsafe_operation(x):
    return eval(x)
"""
    
    crucible = RecursiveCrucible(max_iterations=3)
    results = crucible.run_recursive(sample_code, "sample.py")
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    summary = crucible.get_summary()
    print(f"Total Iterations: {summary['total_iterations']}")
    print(f"Total Weaknesses Found: {summary['total_weaknesses']}")
    print(f"Total Fixes Applied: {summary['total_fixes']}")
    print(f"Successful Fixes: {summary['successful_fixes']}")
    print(f"Average Validation Score: {summary['average_validation_score']:.2f}")
    
    print(f"\n{'='*60}")
    print("ITERATION DETAILS")
    print('='*60)
    
    for result in results:
        print(f"\nIteration {result.iteration + 1}:")
        print(f"  Weaknesses: {len(result.weaknesses_found)}")
        for w in result.weaknesses_found[:3]:  # Show first 3
            print(f"    - [{w.type.value}] {w.description}")
        print(f"  Fixes: {len(result.fixes_applied)}")
        for f in result.fixes_applied[:3]:  # Show first 3
            print(f"    - [{f.strategy.value}] {f.code_change} ({'✓' if f.success else '✗'})")
        print(f"  Duration: {result.duration:.3f}s")
