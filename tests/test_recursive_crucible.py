"""
Test suite for Recursive Crucible Core

Tests the self-improving framework including:
- Weakness detection
- Stress testing
- Code strengthening
- Validation
- Recursive improvement cycles
"""

import pytest
import sys
import os

# Add parent directory to path for test execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_interface.recursive_crucible import (
    WeaknessDetector,
    StressTester,
    CodeStrengthener,
    ValidationOracle,
    RecursiveCrucible,
    WeaknessType,
    StrengtheningStrategy,
    Weakness,
    Fix
)


class TestWeaknessDetector:
    """Test WeaknessDetector class"""
    
    def test_initialization(self):
        """Test detector initialization"""
        detector = WeaknessDetector()
        assert detector.patterns is not None
        assert isinstance(detector.patterns, dict)
        assert len(detector.evolutionary_memory) == 0
    
    def test_detect_static_analysis(self):
        """Test static analysis detection"""
        detector = WeaknessDetector()
        
        code = """
def test_function():
    pass
"""
        weaknesses = detector.detect_static_analysis(code, "test.py")
        
        # Should detect missing docstring
        assert len(weaknesses) > 0
        assert any('docstring' in w.description.lower() for w in weaknesses)
    
    def test_detect_bare_except(self):
        """Test bare except detection"""
        detector = WeaknessDetector()
        
        code = """
def test_function():
    try:
        x = 1
    except:
        pass
"""
        weaknesses = detector.detect_static_analysis(code, "test.py")
        
        # Should detect bare except
        assert len(weaknesses) > 0
        assert any('bare except' in w.description.lower() for w in weaknesses)
    
    def test_detect_pattern_match(self):
        """Test pattern matching detection"""
        detector = WeaknessDetector()
        
        code = """
def unsafe():
    return eval("1 + 1")
"""
        weaknesses = detector.detect_pattern_match(code, "test.py")
        
        # Should detect unsafe operation
        assert len(weaknesses) > 0
    
    def test_detect_syntax_error(self):
        """Test syntax error detection"""
        detector = WeaknessDetector()
        
        code = "def broken("  # Invalid syntax
        weaknesses = detector.detect_static_analysis(code, "test.py")
        
        # Should detect syntax error
        assert len(weaknesses) > 0
        assert weaknesses[0].severity == 1.0


class TestStressTester:
    """Test StressTester class"""
    
    def test_initialization(self):
        """Test tester initialization"""
        tester = StressTester()
        assert tester.test_cases == []
    
    def test_inject_boundary_conditions(self):
        """Test boundary condition injection"""
        tester = StressTester()
        
        code = """
def process(data):
    return data * 2
"""
        weaknesses = tester.inject_boundary_conditions(code, "test.py")
        
        # Should find edge case issues
        assert isinstance(weaknesses, list)
    
    def test_overload_test(self):
        """Test overload testing"""
        tester = StressTester()
        
        code = """
def process_list(items):
    result = []
    for item in items:
        result.append(item * 2)
    return result
"""
        weaknesses = tester.overload_test(code, "test.py")
        
        # Should detect performance issue
        assert len(weaknesses) > 0


class TestCodeStrengthener:
    """Test CodeStrengthener class"""
    
    def test_initialization(self):
        """Test strengthener initialization"""
        strengthener = CodeStrengthener()
        assert strengthener.strategies is not None
    
    def test_strengthen_docstring(self):
        """Test strengthening missing docstring"""
        strengthener = CodeStrengthener()
        
        weakness = Weakness(
            type=WeaknessType.STATIC_ANALYSIS,
            location="test.py:1",
            description="Function 'test' missing docstring",
            severity=0.3
        )
        
        fix = strengthener.strengthen(weakness, "def test(): pass")
        
        assert fix is not None
        assert fix.strategy == StrengtheningStrategy.ADD_LOGGING
    
    def test_strengthen_bare_except(self):
        """Test strengthening bare except"""
        strengthener = CodeStrengthener()
        
        weakness = Weakness(
            type=WeaknessType.STATIC_ANALYSIS,
            location="test.py:3",
            description="Bare except clause detected",
            severity=0.6
        )
        
        fix = strengthener.strengthen(weakness, "try:\n    pass\nexcept:\n    pass")
        
        assert fix is not None
        assert fix.strategy == StrengtheningStrategy.ADD_ERROR_HANDLING


class TestValidationOracle:
    """Test ValidationOracle class"""
    
    def test_initialization(self):
        """Test oracle initialization"""
        oracle = ValidationOracle(min_score_threshold=0.7)
        assert oracle.min_score_threshold == 0.7
        assert len(oracle.validation_history) == 0
    
    def test_validate_fix(self):
        """Test fix validation"""
        oracle = ValidationOracle()
        
        weakness = Weakness(
            type=WeaknessType.STATIC_ANALYSIS,
            location="test.py:1",
            description="Missing error handling",
            severity=0.5
        )
        
        fix = Fix(
            weakness=weakness,
            strategy=StrengtheningStrategy.ADD_ERROR_HANDLING,
            code_change="Add try-except"
        )
        
        original_code = "x = risky_operation()"
        fixed_code = "try:\n    x = risky_operation()\nexcept Exception as e:\n    pass"
        
        result = oracle.validate_fix(fix, original_code, fixed_code)
        
        assert result is not None
        assert isinstance(result.passed, bool)
        assert 0.0 <= result.score <= 1.0
    
    def test_get_average_score(self):
        """Test average score calculation"""
        oracle = ValidationOracle()
        
        weakness = Weakness(
            type=WeaknessType.STATIC_ANALYSIS,
            location="test.py:1",
            description="Test",
            severity=0.5
        )
        
        fix = Fix(
            weakness=weakness,
            strategy=StrengtheningStrategy.ADD_VALIDATION,
            code_change="Add validation"
        )
        
        # Add some validation results
        oracle.validate_fix(fix, "old", "if x: new")
        oracle.validate_fix(fix, "old", "if y: new")
        
        avg = oracle.get_average_score()
        assert 0.0 <= avg <= 1.0


class TestRecursiveCrucible:
    """Test RecursiveCrucible main class"""
    
    def test_initialization(self):
        """Test crucible initialization"""
        crucible = RecursiveCrucible(max_iterations=5, validation_threshold=0.8)
        assert crucible.max_iterations == 5
        assert crucible.validation_threshold == 0.8
        assert crucible.current_iteration == 0
        assert len(crucible.iteration_history) == 0
    
    def test_analyze(self):
        """Test code analysis"""
        crucible = RecursiveCrucible()
        
        code = """
def test():
    pass
"""
        weaknesses = crucible.analyze(code, "test.py")
        
        assert isinstance(weaknesses, list)
        assert len(weaknesses) > 0
    
    def test_test_method(self):
        """Test stress testing method"""
        crucible = RecursiveCrucible()
        
        code = """
def process(data):
    return data
"""
        weaknesses = crucible.test(code, "test.py")
        
        assert isinstance(weaknesses, list)
    
    def test_strengthen(self):
        """Test code strengthening"""
        crucible = RecursiveCrucible()
        
        weakness = Weakness(
            type=WeaknessType.STATIC_ANALYSIS,
            location="test.py:1",
            description="Missing docstring",
            severity=0.3
        )
        
        fixes = crucible.strengthen([weakness], "def test(): pass")
        
        assert isinstance(fixes, list)
    
    def test_run_iteration(self):
        """Test single iteration"""
        crucible = RecursiveCrucible()
        
        code = """
def test_function():
    x = 1
    return x
"""
        result = crucible.run_iteration(code, "test.py")
        
        assert result is not None
        assert result.iteration == 0
        assert isinstance(result.weaknesses_found, list)
        assert isinstance(result.fixes_applied, list)
        assert isinstance(result.validation_results, list)
        assert result.duration >= 0.0
    
    def test_run_recursive(self):
        """Test recursive improvement cycles"""
        crucible = RecursiveCrucible(max_iterations=2)
        
        code = """
def simple():
    pass
"""
        results = crucible.run_recursive(code, "test.py")
        
        assert isinstance(results, list)
        assert len(results) <= 2
        assert all(r.iteration == i for i, r in enumerate(results))
    
    def test_get_summary(self):
        """Test summary generation"""
        crucible = RecursiveCrucible(max_iterations=1)
        
        code = """
def test():
    pass
"""
        crucible.run_recursive(code, "test.py")
        
        summary = crucible.get_summary()
        
        assert isinstance(summary, dict)
        assert 'total_iterations' in summary
        assert 'total_weaknesses' in summary
        assert 'total_fixes' in summary
        assert 'successful_fixes' in summary
        assert 'average_validation_score' in summary
        assert 'iterations' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
