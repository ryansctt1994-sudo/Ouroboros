"""
Test suite for the vectorization tool.

This test suite validates the code vectorization functionality,
ensuring accurate extraction of metadata from Python and Rust files.

Test coverage includes:
- Python AST parsing for functions, classes, methods
- Rust regex-based parsing for functions, structs, enums
- Metadata extraction (signatures, docstrings, attributes)
- FFI function detection
- JSON output format validation
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
import sys

# Add tools directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'tools')))

from vectorize import (
    PythonParser,
    RustParser,
    CodebaseVectorizer,
    VectorMetadata
)


class TestPythonParser:
    """Test Python AST parsing functionality"""
    
    def test_parse_simple_function(self, tmp_path):
        """Test parsing a simple function"""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def hello_world():
    \"\"\"Say hello to the world\"\"\"
    print("Hello, World!")
""")
        
        parser = PythonParser(str(test_file), tmp_path)
        vectors = parser.parse()
        
        # Should have 1 function
        func_vectors = [v for v in vectors if v.type == "function"]
        assert len(func_vectors) == 1
        
        func = func_vectors[0]
        assert func.name == "hello_world"
        assert func.signature == "def hello_world()"
        assert "Say hello" in func.docstring
    
    def test_parse_class_with_methods(self, tmp_path):
        """Test parsing a class with methods"""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
class Calculator:
    \"\"\"Simple calculator class\"\"\"
    
    def add(self, a: int, b: int) -> int:
        \"\"\"Add two numbers\"\"\"
        return a + b
    
    def subtract(self, a: int, b: int) -> int:
        return a - b
""")
        
        parser = PythonParser(str(test_file), tmp_path)
        vectors = parser.parse()
        
        # Should have 1 class and 2 methods
        class_vectors = [v for v in vectors if v.type == "class"]
        method_vectors = [v for v in vectors if v.type == "method"]
        
        assert len(class_vectors) == 1
        assert len(method_vectors) == 2
        
        calc_class = class_vectors[0]
        assert calc_class.name == "Calculator"
        assert "calculator" in calc_class.docstring.lower()
        
        # Check method details
        add_method = [m for m in method_vectors if m.name == "add"][0]
        assert add_method.parent == "Calculator"
        assert "a: int" in add_method.signature
        assert "-> int" in add_method.signature
    
    def test_parse_module_docstring(self, tmp_path):
        """Test parsing module-level docstring"""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
\"\"\"
This is a test module.
It has a docstring.
\"\"\"

def foo():
    pass
""")
        
        parser = PythonParser(str(test_file), tmp_path)
        vectors = parser.parse()
        
        # Should have 1 module and 1 function
        module_vectors = [v for v in vectors if v.type == "module"]
        assert len(module_vectors) == 1
        
        module = module_vectors[0]
        assert "test module" in module.docstring
    
    def test_parse_decorators(self, tmp_path):
        """Test parsing function decorators"""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
@property
def getter(self):
    return self.value

@staticmethod
def static_method():
    pass
""")
        
        parser = PythonParser(str(test_file), tmp_path)
        vectors = parser.parse()
        
        getter = [v for v in vectors if v.name == "getter"][0]
        static = [v for v in vectors if v.name == "static_method"][0]
        
        assert "property" in getter.decorators
        assert "staticmethod" in static.decorators


class TestRustParser:
    """Test Rust regex-based parsing functionality"""
    
    def test_parse_simple_function(self, tmp_path):
        """Test parsing a simple Rust function"""
        test_file = tmp_path / "test.rs"
        test_file.write_text("""
/// Calculate the sum of two numbers
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}
""")
        
        parser = RustParser(str(test_file), tmp_path)
        vectors = parser.parse()
        
        func_vectors = [v for v in vectors if v.type == "function"]
        assert len(func_vectors) == 1
        
        func = func_vectors[0]
        assert func.name == "add"
        assert func.visibility == "public"
        assert "fn add" in func.signature
        assert "Calculate the sum" in func.docstring
    
    def test_parse_ffi_function(self, tmp_path):
        """Test parsing FFI function with #[no_mangle]"""
        test_file = tmp_path / "test.rs"
        test_file.write_text("""
/// Create a new engine
#[no_mangle]
pub extern "C" fn engine_new() -> *mut Engine {
    Box::into_raw(Box::new(Engine::new()))
}
""")
        
        parser = RustParser(str(test_file), tmp_path)
        vectors = parser.parse()
        
        func_vectors = [v for v in vectors if "function" in v.type]
        assert len(func_vectors) == 1
        
        func = func_vectors[0]
        assert func.name == "engine_new"
        assert func.type == "ffi_function"
        assert "#[no_mangle]" in func.attributes
        assert "extern" in func.signature
    
    def test_parse_struct(self, tmp_path):
        """Test parsing a struct"""
        test_file = tmp_path / "test.rs"
        test_file.write_text("""
/// A point in 2D space
pub struct Point {
    x: f64,
    y: f64,
}
""")
        
        parser = RustParser(str(test_file), tmp_path)
        vectors = parser.parse()
        
        struct_vectors = [v for v in vectors if v.type == "struct"]
        assert len(struct_vectors) == 1
        
        struct = struct_vectors[0]
        assert struct.name == "Point"
        assert struct.visibility == "public"
        assert "2D space" in struct.docstring
    
    def test_parse_enum(self, tmp_path):
        """Test parsing an enum"""
        test_file = tmp_path / "test.rs"
        test_file.write_text("""
/// Color enumeration
pub enum Color {
    Red,
    Green,
    Blue,
}
""")
        
        parser = RustParser(str(test_file), tmp_path)
        vectors = parser.parse()
        
        enum_vectors = [v for v in vectors if v.type == "enum"]
        assert len(enum_vectors) == 1
        
        enum = enum_vectors[0]
        assert enum.name == "Color"
        assert "enumeration" in enum.docstring


class TestCodebaseVectorizer:
    """Test full codebase vectorization"""
    
    def test_vectorize_directory(self, tmp_path):
        """Test vectorizing a directory with mixed files"""
        # Create test files
        py_file = tmp_path / "module.py"
        py_file.write_text("""
def foo():
    pass

class Bar:
    def baz(self):
        pass
""")
        
        rs_file = tmp_path / "lib.rs"
        rs_file.write_text("""
pub fn rust_func() -> i32 {
    42
}
""")
        
        vectorizer = CodebaseVectorizer(tmp_path)
        vectors = vectorizer.scan()
        
        # Should have vectors from both files
        py_vectors = [v for v in vectors if v.language == "python"]
        rs_vectors = [v for v in vectors if v.language == "rust"]
        
        assert len(py_vectors) > 0
        assert len(rs_vectors) > 0
    
    def test_save_to_json(self, tmp_path):
        """Test saving vectors to JSON file"""
        py_file = tmp_path / "test.py"
        py_file.write_text("def test(): pass")
        
        vectorizer = CodebaseVectorizer(tmp_path)
        vectors = vectorizer.scan()
        
        output_file = tmp_path / "output.json"
        vectorizer.save_to_json(output_file)
        
        # Verify JSON file was created and is valid
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "vectors" in data
        assert data["metadata"]["total_vectors"] == len(vectors)
        assert "python" in data["metadata"]["languages"]
    
    def test_skip_directories(self, tmp_path):
        """Test that excluded directories are skipped"""
        # Create excluded directories
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / ".git").mkdir()
        (tmp_path / "venv").mkdir()
        
        # Create files in excluded directories
        (tmp_path / "__pycache__" / "test.py").write_text("def foo(): pass")
        (tmp_path / ".git" / "test.py").write_text("def bar(): pass")
        (tmp_path / "venv" / "test.py").write_text("def baz(): pass")
        
        # Create file in root
        (tmp_path / "valid.py").write_text("def valid(): pass")
        
        vectorizer = CodebaseVectorizer(tmp_path)
        vectors = vectorizer.scan()
        
        # Should only have vectors from valid.py
        assert len(vectors) == 1
        assert vectors[0].name == "valid"


class TestVectorMetadata:
    """Test VectorMetadata dataclass"""
    
    def test_to_dict(self):
        """Test converting metadata to dictionary"""
        meta = VectorMetadata(
            vector_id="test.module.func",
            type="function",
            name="func",
            module="test.module",
            language="python",
            signature="def func()",
        )
        
        data = meta.to_dict()
        
        assert data["vector_id"] == "test.module.func"
        assert data["type"] == "function"
        assert data["name"] == "func"
        assert isinstance(data, dict)


# Integration test
def test_vectorize_real_file():
    """Test vectorizing a real file from the repository"""
    repo_root = Path(__file__).parent.parent
    test_file = repo_root / "python-bridge" / "eden_ecs" / "components.py"
    
    if test_file.exists():
        parser = PythonParser(str(test_file), repo_root)
        vectors = parser.parse()
        
        # Should have multiple vectors
        assert len(vectors) > 10
        
        # Should have Consciousness7D class
        class_vectors = [v for v in vectors if v.type == "class"]
        assert any(v.name == "Consciousness7D" for v in class_vectors)
        
        # Should have methods
        method_vectors = [v for v in vectors if v.type == "method"]
        assert len(method_vectors) > 0
