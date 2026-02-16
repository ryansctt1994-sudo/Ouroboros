#!/usr/bin/env python3
"""
EDEN Sandbox Tests
==================

Unit tests for the sandbox execution service.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from eden_sandbox import EdenSandbox


class TestEdenSandbox(unittest.TestCase):
    """Test EdenSandbox class."""
    
    def setUp(self):
        """Set up test sandbox."""
        self.sandbox = EdenSandbox()
    
    def test_init(self):
        """Test sandbox initialization."""
        self.assertIsNotNone(self.sandbox)
        self.assertIsInstance(self.sandbox.bwrap_available, bool)
    
    def test_execute_python_success(self):
        """Test executing successful Python code."""
        code = "print('Hello, World!')"
        output, success, error = self.sandbox.execute(code, language="python", timeout=5)
        
        self.assertTrue(success)
        self.assertIn("Hello, World!", output)
        self.assertEqual(error, "")
    
    def test_execute_python_error(self):
        """Test executing Python code with error."""
        code = "raise ValueError('Test error')"
        output, success, error = self.sandbox.execute(code, language="python", timeout=5)
        
        self.assertFalse(success)
        self.assertIn("ValueError", output)
        self.assertIn("Test error", output)
    
    def test_execute_python_syntax_error(self):
        """Test executing Python code with syntax error."""
        code = "print('unclosed string"
        output, success, error = self.sandbox.execute(code, language="python", timeout=5)
        
        self.assertFalse(success)
        self.assertIn("SyntaxError", output)
    
    def test_execute_shell_success(self):
        """Test executing successful shell code."""
        code = "echo 'Hello from shell'"
        output, success, error = self.sandbox.execute(code, language="shell", timeout=5)
        
        self.assertTrue(success)
        self.assertIn("Hello from shell", output)
        self.assertEqual(error, "")
    
    def test_execute_shell_error(self):
        """Test executing shell code with error."""
        code = "exit 1"
        output, success, error = self.sandbox.execute(code, language="shell", timeout=5)
        
        self.assertFalse(success)
        self.assertIn("Exit code 1", error)
    
    def test_execute_timeout(self):
        """Test execution timeout."""
        # Code that sleeps for 10 seconds
        code = "import time; time.sleep(10)"
        output, success, error = self.sandbox.execute(code, language="python", timeout=1)
        
        self.assertFalse(success)
        self.assertIn("timed out", error.lower())
    
    def test_execute_unsupported_language(self):
        """Test executing code in unsupported language."""
        code = "console.log('test')"
        output, success, error = self.sandbox.execute(code, language="javascript", timeout=5)
        
        self.assertFalse(success)
        self.assertIn("Unsupported language", error)
    
    def test_execute_empty_code(self):
        """Test executing empty code."""
        code = ""
        output, success, error = self.sandbox.execute(code, language="python", timeout=5)
        
        # Empty code should succeed (no output)
        self.assertTrue(success)
    
    def test_execute_multiline_python(self):
        """Test executing multiline Python code."""
        code = """
x = 10
y = 20
print(f"Sum: {x + y}")
"""
        output, success, error = self.sandbox.execute(code, language="python", timeout=5)
        
        self.assertTrue(success)
        self.assertIn("Sum: 30", output)
    
    def test_execute_multiline_shell(self):
        """Test executing multiline shell code."""
        code = """
echo "Line 1"
echo "Line 2"
echo "Line 3"
"""
        output, success, error = self.sandbox.execute(code, language="shell", timeout=5)
        
        self.assertTrue(success)
        self.assertIn("Line 1", output)
        self.assertIn("Line 2", output)
        self.assertIn("Line 3", output)
    
    def test_get_status(self):
        """Test get_status method."""
        status = self.sandbox.get_status()
        
        self.assertIn("bwrap_available", status)
        self.assertIn("mode", status)
        self.assertIsInstance(status["bwrap_available"], bool)
        
        expected_mode = "secure" if status["bwrap_available"] else "unsafe_fallback"
        self.assertEqual(status["mode"], expected_mode)


if __name__ == "__main__":
    unittest.main()
