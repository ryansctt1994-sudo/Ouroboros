#!/usr/bin/env python3
"""
EDEN AI Service Tests
=====================

Unit tests for the AI service with mocked llama-cpp-python.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from eden_ai import EdenAI


class TestEdenAI(unittest.TestCase):
    """Test EdenAI class."""
    
    def test_init_without_llama(self):
        """Test initialization when llama-cpp-python is not available."""
        with patch.dict('sys.modules', {'llama_cpp': None}):
            ai = EdenAI()
            self.assertFalse(ai._llama_available)
            self.assertFalse(ai.model_loaded)
            self.assertFalse(ai.is_available())
    
    def test_init_with_llama_no_model(self):
        """Test initialization when llama is available but no model."""
        mock_llama = MagicMock()
        
        with patch.dict('sys.modules', {'llama_cpp': mock_llama}):
            ai = EdenAI(model_path="/nonexistent/model.gguf")
            self.assertTrue(ai._llama_available)
            self.assertFalse(ai.model_loaded)
            self.assertFalse(ai.is_available())
    
    def test_load_vectors_success(self):
        """Test loading vectors.json."""
        # Create temporary vectors file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            vectors_data = {
                "metadata": {"version": "1.0.0"},
                "vectors": [
                    {"name": "test_func", "docstring": "Test function", "module": "test"}
                ]
            }
            json.dump(vectors_data, f)
            vectors_file = f.name
        
        try:
            ai = EdenAI()
            result = ai.load_vectors(vectors_file)
            
            self.assertTrue(result)
            self.assertIsNotNone(ai.vectors_data)
            self.assertEqual(len(ai.vectors_data['vectors']), 1)
        
        finally:
            os.unlink(vectors_file)
    
    def test_load_vectors_not_found(self):
        """Test loading non-existent vectors.json."""
        ai = EdenAI()
        result = ai.load_vectors("/nonexistent/vectors.json")
        
        self.assertFalse(result)
        self.assertIsNone(ai.vectors_data)
    
    def test_search_vectors_no_data(self):
        """Test searching vectors when no data is loaded."""
        ai = EdenAI()
        results = ai.search_vectors("test query")
        
        self.assertEqual(len(results), 0)
    
    def test_search_vectors_keyword_match(self):
        """Test vector search with keyword matching."""
        ai = EdenAI()
        ai.vectors_data = {
            "vectors": [
                {
                    "name": "calculate_sum",
                    "docstring": "Calculate the sum of two numbers",
                    "module": "math_utils"
                },
                {
                    "name": "calculate_product",
                    "docstring": "Calculate the product of two numbers",
                    "module": "math_utils"
                },
                {
                    "name": "format_string",
                    "docstring": "Format a string",
                    "module": "string_utils"
                }
            ]
        }
        
        # Search for "calculate"
        results = ai.search_vectors("calculate")
        self.assertEqual(len(results), 2)
        self.assertIn("calculate", results[0]['name'].lower())
        
        # Search for "sum"
        results = ai.search_vectors("sum")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "calculate_sum")
        
        # Search for "string"
        results = ai.search_vectors("string")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "format_string")
    
    def test_search_vectors_limit(self):
        """Test vector search respects limit."""
        ai = EdenAI()
        ai.vectors_data = {
            "vectors": [
                {"name": f"test_{i}", "docstring": "test function", "module": "test"}
                for i in range(10)
            ]
        }
        
        results = ai.search_vectors("test", limit=3)
        self.assertEqual(len(results), 3)
    
    def test_build_context(self):
        """Test building context from vectors."""
        ai = EdenAI()
        ai.vectors_data = {
            "vectors": [
                {
                    "name": "test_function",
                    "file_path": "test.py",
                    "docstring": "A test function",
                    "signature": "def test_function()"
                }
            ]
        }
        
        context = ai._build_context("test function")
        
        self.assertIn("test_function", context)
        self.assertIn("test.py", context)
        self.assertIn("A test function", context)
    
    def test_generate_without_llama(self):
        """Test generate raises error when llama not available."""
        ai = EdenAI()
        ai._llama_available = False
        
        with self.assertRaises(RuntimeError) as ctx:
            ai.generate([{"role": "user", "content": "Hello"}])
        
        self.assertIn("llama-cpp-python", str(ctx.exception))
    
    def test_generate_without_model(self):
        """Test generate raises error when model not loaded."""
        mock_llama = MagicMock()
        
        with patch.dict('sys.modules', {'llama_cpp': mock_llama}):
            ai = EdenAI()
            ai._llama_available = True
            ai.model_loaded = False
            
            with self.assertRaises(RuntimeError) as ctx:
                ai.generate([{"role": "user", "content": "Hello"}])
            
            self.assertIn("No AI model", str(ctx.exception))
    
    def test_generate_with_mocked_model(self):
        """Test generate with mocked llama model."""
        # Create mock Llama class
        mock_llama_class = MagicMock()
        mock_model = MagicMock()
        mock_model.return_value = {
            'choices': [{'text': 'Hello! I am EDEN.'}]
        }
        mock_llama_class.return_value = mock_model
        
        # Create temporary model file
        with tempfile.NamedTemporaryFile(suffix='.gguf', delete=False) as f:
            model_file = f.name
        
        try:
            # Mock llama_cpp module
            mock_module = MagicMock()
            mock_module.Llama = mock_llama_class
            
            with patch.dict('sys.modules', {'llama_cpp': mock_module}):
                ai = EdenAI(model_path=model_file)
                
                messages = [{"role": "user", "content": "Hello"}]
                response = ai.generate(messages)
                
                self.assertIsInstance(response, str)
                self.assertIn("EDEN", response)
        
        finally:
            os.unlink(model_file)
    
    def test_get_status(self):
        """Test get_status method."""
        ai = EdenAI()
        status = ai.get_status()
        
        self.assertIn("llama_available", status)
        self.assertIn("model_loaded", status)
        self.assertIn("model_path", status)
        self.assertIn("vectors_loaded", status)
        self.assertIn("vector_count", status)
        
        self.assertFalse(status["vectors_loaded"])
        self.assertEqual(status["vector_count"], 0)


if __name__ == "__main__":
    unittest.main()
