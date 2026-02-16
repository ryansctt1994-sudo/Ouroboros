# Ouroboros Code Vectorization Tool

## Overview

The vectorization tool scans the entire Ouroboros codebase and produces a machine-readable manifest (`vectors.json`) of every function, class, method, and system. This turns the repository into a searchable, composable knowledge base — a "mycelial substrate" where each code unit is a discoverable "fruit body" that a local AI can query and compose from.

## Features

### Python Parsing (AST-based)
- **Functions**: Extracts function definitions (both regular and async)
- **Classes**: Captures class definitions with base classes
- **Methods**: Identifies methods within classes
- **Decorators**: Records all decorators applied to functions and classes
- **Type Annotations**: Preserves function signatures with type hints
- **Docstrings**: Extracts module, class, function, and method docstrings

### Rust Parsing (Regex-based)
- **Functions**: Identifies `pub fn`, `fn`, `async fn`, `unsafe fn`
- **Structs**: Extracts struct declarations
- **Enums**: Captures enum definitions
- **Impl Blocks**: Records implementation blocks
- **FFI Exports**: Detects `#[no_mangle] pub extern "C" fn` exports
- **Doc Comments**: Preserves `///` and `//!` documentation
- **Attributes**: Captures all `#[...]` attributes

### Metadata Extraction

Each code unit is wrapped in a metadata envelope containing:

```json
{
  "vector_id": "ouroboros.module.Class.method",
  "type": "method|function|class|struct|enum|impl|ffi_function",
  "name": "method_name",
  "parent": "Class",
  "module": "module.path",
  "file_path": "relative/path/to/file.py",
  "language": "python|rust",
  "line_start": 45,
  "line_end": 58,
  "signature": "def method(self, arg: Type) -> ReturnType",
  "docstring": "Method documentation...",
  "decorators": ["@decorator1", "@decorator2"],
  "attributes": ["#[attribute]"],
  "visibility": "public|private",
  "base_classes": ["BaseClass"],
  "dependencies": ["imported_symbol"],
  "hash": "abcdef123456"
}
```

## Usage

### Basic Usage

```bash
# Vectorize the entire repository
python tools/vectorize.py

# Specify custom output file
python tools/vectorize.py --output my_vectors.json

# Vectorize a specific directory
python tools/vectorize.py --root /path/to/directory
```

### Command-Line Options

```
usage: vectorize.py [-h] [--output OUTPUT] [--root ROOT]

Vectorize Ouroboros codebase into machine-readable manifest

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output JSON file path (default: vectors.json)
  --root ROOT, -r ROOT  Repository root directory (default: current directory)
```

## Output Format

The tool generates a JSON file with the following structure:

```json
{
  "metadata": {
    "version": "1.0.0",
    "repository": "AIOSPANDORA/Ouroboros",
    "total_vectors": 2082,
    "languages": ["python", "rust"],
    "types": ["function", "method", "class", "struct", "enum", "impl", "ffi_function"]
  },
  "vectors": [
    { /* vector 1 */ },
    { /* vector 2 */ },
    ...
  ]
}
```

## Excluded Directories

The tool automatically skips the following directories:
- `__pycache__`
- `.git`
- `node_modules`
- `target/` (Rust build directory)
- `venv/`, `.venv/`
- `.pytest_cache`
- `htmlcov`
- `.eggs`
- `dist`, `build`
- `env`, `ENV`
- `.idea`, `.vscode`
- `checkpoints`, `logs`, `runs`

## Examples

### Query Vectors by Type

```python
import json

with open('vectors.json', 'r') as f:
    data = json.load(f)

# Find all FFI functions
ffi_functions = [v for v in data['vectors'] if v['type'] == 'ffi_function']

# Find all classes
classes = [v for v in data['vectors'] if v['type'] == 'class']

# Find methods in a specific class
consciousness_methods = [
    v for v in data['vectors'] 
    if v['type'] == 'method' and v['parent'] == 'Consciousness7D'
]
```

### Search by Module

```python
# Find all vectors in the ECS module
ecs_vectors = [
    v for v in data['vectors'] 
    if 'eden_ecs' in v['module']
]
```

### Find Functions by Name Pattern

```python
import re

# Find all functions containing 'sync' in the name
sync_functions = [
    v for v in data['vectors']
    if v['type'] == 'function' and re.search('sync', v['name'], re.I)
]
```

## Testing

Run the test suite:

```bash
python -m pytest tests/test_vectorize.py -v
```

The test suite includes:
- 13 comprehensive test cases
- Python AST parsing validation
- Rust regex parsing validation
- Metadata extraction verification
- JSON output format validation

## Statistics

Current vectorization results:
- **Total vectors**: 2,082
- **Methods**: 1,272
- **Functions**: 318
- **Classes**: 309
- **Modules**: 136
- **Structs**: 21
- **Impl blocks**: 13
- **FFI functions**: 10
- **Enums**: 3

## Security

The vectorization tool is designed with security in mind:
- ✓ Uses Python's AST module (no code execution)
- ✓ Uses regex for Rust parsing (no code execution)
- ✓ All dependencies from Python standard library
- ✓ No network operations
- ✓ No shell command execution
- ✓ Safe path handling with pathlib
- ✓ Explicit UTF-8 encoding for file operations

## Integration with AI Systems

The `vectors.json` file can be used by AI systems to:
1. **Navigate the codebase** by querying specific functions or modules
2. **Understand relationships** between components through dependencies
3. **Generate documentation** using extracted docstrings
4. **Analyze code patterns** across the entire repository
5. **Build knowledge graphs** of code structure
6. **Enable semantic search** across all code units

## Contributing

When adding new parsing capabilities:
1. Update the appropriate parser class (`PythonParser` or `RustParser`)
2. Add corresponding test cases in `tests/test_vectorize.py`
3. Update this README with the new features
4. Regenerate `vectors.json` to include the new metadata

## License

MIT License - See LICENSE file for details

## Author

AIOSPANDORA Development Team
