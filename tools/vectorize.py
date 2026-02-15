#!/usr/bin/env python3
"""
Ouroboros Code Vectorization Tool
==================================

Scans the entire Ouroboros codebase and produces a machine-readable manifest
(vectors.json) of every function, class, method, and system. This turns the
repository into a searchable, composable knowledge base.

Usage:
    python tools/vectorize.py [--output vectors.json] [--root .]

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import ast
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Any


# Directories to skip during repository walk
SKIP_DIRS = {
    '__pycache__', '.git', 'node_modules', 'target', 'venv', '.venv',
    '.pytest_cache', 'htmlcov', '.eggs', 'dist', 'build', 'env', 'ENV',
    '.idea', '.vscode', 'checkpoints', 'logs', 'runs'
}

# File extensions to process
PYTHON_EXTENSIONS = {'.py'}
RUST_EXTENSIONS = {'.rs'}


@dataclass
class VectorMetadata:
    """Metadata envelope for a code unit (function, class, method, etc.)"""
    vector_id: str
    type: str  # "function", "method", "class", "struct", "enum", "impl", etc.
    name: str
    parent: Optional[str] = None
    module: str = ""
    file_path: str = ""
    language: str = ""
    line_start: int = 0
    line_end: int = 0
    signature: str = ""
    docstring: str = ""
    domain: str = ""
    purity: str = ""
    dependencies: List[str] = field(default_factory=list)
    internal_refs: List[str] = field(default_factory=list)
    constants: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""
    decorators: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    visibility: str = "private"
    base_classes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class PythonParser:
    """Parser for Python source files using AST"""
    
    def __init__(self, file_path: str, repo_root: Path):
        self.file_path = file_path
        self.repo_root = repo_root
        self.relative_path = Path(file_path).relative_to(repo_root)
        self.module = self._compute_module_name()
        self.vectors: List[VectorMetadata] = []
        
    def _compute_module_name(self) -> str:
        """Convert file path to Python module notation"""
        parts = list(self.relative_path.parts)
        if parts[-1] == '__init__.py':
            parts = parts[:-1]
        elif parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]
        return '.'.join(parts) if parts else ''
    
    def parse(self) -> List[VectorMetadata]:
        """Parse Python file and extract all code units"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            tree = ast.parse(source, filename=self.file_path)
            
            # Extract module-level docstring
            module_docstring = ast.get_docstring(tree)
            if module_docstring:
                vector_id = f"ouroboros.{self.module}"
                self.vectors.append(VectorMetadata(
                    vector_id=vector_id,
                    type="module",
                    name=self.module,
                    module=self.module,
                    file_path=str(self.relative_path),
                    language="python",
                    line_start=1,
                    line_end=1,
                    docstring=module_docstring,
                    hash=self._compute_hash(module_docstring)
                ))
            
            # Walk the AST
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    self._process_class(node)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Only process top-level functions (methods are processed within classes)
                    if not self._is_method(node, tree):
                        self._process_function(node)
            
            return self.vectors
            
        except Exception as e:
            print(f"Warning: Failed to parse {self.file_path}: {e}", file=sys.stderr)
            return []
    
    def _is_method(self, node: ast.FunctionDef, tree: ast.Module) -> bool:
        """Check if a function is a method (inside a class)"""
        for parent in ast.walk(tree):
            if isinstance(parent, ast.ClassDef):
                if node in parent.body:
                    return True
        return False
    
    def _process_class(self, node: ast.ClassDef) -> None:
        """Extract class metadata"""
        vector_id = f"ouroboros.{self.module}.{node.name}"
        
        # Extract base classes
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(self._get_attribute_name(base))
        
        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        docstring = ast.get_docstring(node) or ""
        
        class_vector = VectorMetadata(
            vector_id=vector_id,
            type="class",
            name=node.name,
            module=self.module,
            file_path=str(self.relative_path),
            language="python",
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=f"class {node.name}({', '.join(base_classes)})" if base_classes else f"class {node.name}",
            docstring=docstring,
            base_classes=base_classes,
            decorators=decorators,
            hash=self._compute_hash(f"{node.name}{docstring}")
        )
        self.vectors.append(class_vector)
        
        # Process methods within the class
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._process_function(item, parent_class=node.name)
    
    def _process_function(self, node: ast.FunctionDef, parent_class: Optional[str] = None) -> None:
        """Extract function or method metadata"""
        if parent_class:
            vector_id = f"ouroboros.{self.module}.{parent_class}.{node.name}"
            func_type = "method"
        else:
            vector_id = f"ouroboros.{self.module}.{node.name}"
            func_type = "function"
        
        # Extract function signature
        args = self._get_function_args(node)
        return_annotation = ""
        if node.returns:
            return_annotation = f" -> {self._get_annotation_name(node.returns)}"
        
        is_async = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
        signature = f"{is_async}def {node.name}({', '.join(args)}){return_annotation}"
        
        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # Analyze function purity (basic heuristic)
        purity = self._analyze_purity(node)
        
        # Extract dependencies (imported names used in function)
        dependencies = self._extract_dependencies(node)
        
        docstring = ast.get_docstring(node) or ""
        
        func_vector = VectorMetadata(
            vector_id=vector_id,
            type=func_type,
            name=node.name,
            parent=parent_class,
            module=self.module,
            file_path=str(self.relative_path),
            language="python",
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=signature,
            docstring=docstring,
            decorators=decorators,
            purity=purity,
            dependencies=dependencies,
            hash=self._compute_hash(f"{signature}{docstring}")
        )
        self.vectors.append(func_vector)
    
    def _get_function_args(self, node: ast.FunctionDef) -> List[str]:
        """Extract function argument list with annotations"""
        args = []
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {self._get_annotation_name(arg.annotation)}"
            args.append(arg_str)
        return args
    
    def _get_annotation_name(self, node: ast.expr) -> str:
        """Get the name of a type annotation"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_name(node)
        elif isinstance(node, ast.Subscript):
            value = self._get_annotation_name(node.value)
            slice_val = self._get_annotation_name(node.slice)
            return f"{value}[{slice_val}]"
        elif isinstance(node, ast.Tuple):
            elements = [self._get_annotation_name(e) for e in node.elts]
            return f"({', '.join(elements)})"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        else:
            return "Any"
    
    def _get_attribute_name(self, node: ast.Attribute) -> str:
        """Get full attribute name (e.g., 'module.Class')"""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts))
    
    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get decorator name"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_attribute_name(node)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return self._get_attribute_name(node.func)
        return "decorator"
    
    def _analyze_purity(self, node: ast.FunctionDef) -> str:
        """Analyze function purity (basic heuristic)"""
        # Check for common patterns of side effects
        for child in ast.walk(node):
            # Global/nonlocal variables suggest impurity
            if isinstance(child, (ast.Global, ast.Nonlocal)):
                return "impure"
            # Print/file operations suggest impurity
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    if child.func.id in {'print', 'open', 'input'}:
                        return "impure"
        
        # If no obvious side effects, assume pure (may be conservative)
        return "pure"
    
    def _extract_dependencies(self, node: ast.FunctionDef) -> List[str]:
        """Extract names used in function (basic dependency analysis)"""
        deps = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                # Skip function parameters
                if child.id not in [arg.arg for arg in node.args.args]:
                    deps.add(child.id)
        return sorted(list(deps))
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


class RustParser:
    """Parser for Rust source files using regex patterns"""
    
    # Regex patterns for Rust code extraction
    FN_PATTERN = re.compile(
        r'(?:(?P<vis>pub(?:\([^)]+\))?)\s+)?'  # visibility
        r'(?:(?P<async>async)\s+)?'  # async
        r'(?:(?P<unsafe>unsafe)\s+)?'  # unsafe
        r'(?:(?P<extern>extern\s+"[^"]+"\s+)?)'  # extern
        r'fn\s+(?P<name>\w+)\s*'  # function name
        r'(?:<[^>]+>)?'  # optional generics
        r'\((?P<args>[^)]*)\)'  # arguments
        r'(?:\s*->\s*(?P<ret>[^{;]+))?'  # return type
    )
    
    STRUCT_PATTERN = re.compile(
        r'(?:(?P<vis>pub(?:\([^)]+\))?)\s+)?'
        r'struct\s+(?P<name>\w+)\s*'
        r'(?:<[^>]+>)?'  # optional generics
    )
    
    ENUM_PATTERN = re.compile(
        r'(?:(?P<vis>pub(?:\([^)]+\))?)\s+)?'
        r'enum\s+(?P<name>\w+)\s*'
        r'(?:<[^>]+>)?'  # optional generics
    )
    
    IMPL_PATTERN = re.compile(
        r'impl\s+(?:<[^>]+>\s+)?(?P<name>\w+)'
    )
    
    ATTR_PATTERN = re.compile(r'#\[([^\]]+)\]')
    
    DOC_COMMENT_PATTERN = re.compile(r'^\s*///\s*(.*)$', re.MULTILINE)
    MODULE_DOC_PATTERN = re.compile(r'^\s*//!\s*(.*)$', re.MULTILINE)
    
    def __init__(self, file_path: str, repo_root: Path):
        self.file_path = file_path
        self.repo_root = repo_root
        self.relative_path = Path(file_path).relative_to(repo_root)
        self.module = self._compute_module_name()
        self.vectors: List[VectorMetadata] = []
        
    def _compute_module_name(self) -> str:
        """Convert file path to Rust module notation"""
        parts = list(self.relative_path.parts)
        if parts[-1] == 'mod.rs' or parts[-1] == 'lib.rs':
            parts = parts[:-1]
        elif parts[-1].endswith('.rs'):
            parts[-1] = parts[-1][:-3]
        return '::'.join(parts) if parts else ''
    
    def parse(self) -> List[VectorMetadata]:
        """Parse Rust file and extract all code units"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            lines = source.split('\n')
            
            # Extract module-level doc comments
            module_docs = self.MODULE_DOC_PATTERN.findall(source)
            if module_docs:
                vector_id = f"ouroboros::{self.module}"
                self.vectors.append(VectorMetadata(
                    vector_id=vector_id,
                    type="module",
                    name=self.module,
                    module=self.module,
                    file_path=str(self.relative_path),
                    language="rust",
                    line_start=1,
                    line_end=1,
                    docstring=' '.join(module_docs),
                    hash=self._compute_hash(' '.join(module_docs))
                ))
            
            # Extract functions
            self._extract_functions(source, lines)
            
            # Extract structs
            self._extract_structs(source, lines)
            
            # Extract enums
            self._extract_enums(source, lines)
            
            # Extract impl blocks
            self._extract_impls(source, lines)
            
            return self.vectors
            
        except Exception as e:
            print(f"Warning: Failed to parse {self.file_path}: {e}", file=sys.stderr)
            return []
    
    def _extract_functions(self, source: str, lines: List[str]) -> None:
        """Extract function declarations"""
        for match in self.FN_PATTERN.finditer(source):
            name = match.group('name')
            vis = match.group('vis') or 'private'
            async_kw = 'async ' if match.group('async') else ''
            unsafe_kw = 'unsafe ' if match.group('unsafe') else ''
            extern_kw = match.group('extern') or ''
            args = match.group('args') or ''
            ret = match.group('ret') or ''
            
            # Determine visibility
            visibility = 'public' if vis and 'pub' in vis else 'private'
            
            # Build signature
            ret_part = f" -> {ret.strip()}" if ret else ''
            signature = f"{extern_kw}{async_kw}{unsafe_kw}fn {name}({args}){ret_part}"
            
            # Find line number (1-indexed)
            line_num = source[:match.start()].count('\n') + 1
            
            # Extract preceding doc comments and attributes
            # lines is 0-indexed, so lines[line_num-1] would be the declaration line itself
            # We pass line_num-2 to start from lines[line_num-2], the line before the declaration
            docstring, attributes = self._extract_doc_and_attrs(lines, line_num - 2)
            
            # Check if FFI export
            is_ffi = any('#[no_mangle]' in attr for attr in attributes)
            func_type = "ffi_function" if is_ffi else "function"
            
            vector_id = f"ouroboros::{self.module}::{name}"
            
            self.vectors.append(VectorMetadata(
                vector_id=vector_id,
                type=func_type,
                name=name,
                module=self.module,
                file_path=str(self.relative_path),
                language="rust",
                line_start=line_num,
                line_end=line_num,  # Can't easily determine end without full parsing
                signature=signature,
                docstring=docstring,
                visibility=visibility,
                attributes=attributes,
                hash=self._compute_hash(f"{signature}{docstring}")
            ))
    
    def _extract_structs(self, source: str, lines: List[str]) -> None:
        """Extract struct declarations"""
        for match in self.STRUCT_PATTERN.finditer(source):
            name = match.group('name')
            vis = match.group('vis') or 'private'
            visibility = 'public' if vis and 'pub' in vis else 'private'
            
            line_num = source[:match.start()].count('\n') + 1
            docstring, attributes = self._extract_doc_and_attrs(lines, line_num - 2)
            
            vector_id = f"ouroboros::{self.module}::{name}"
            
            self.vectors.append(VectorMetadata(
                vector_id=vector_id,
                type="struct",
                name=name,
                module=self.module,
                file_path=str(self.relative_path),
                language="rust",
                line_start=line_num,
                line_end=line_num,
                signature=f"struct {name}",
                docstring=docstring,
                visibility=visibility,
                attributes=attributes,
                hash=self._compute_hash(f"{name}{docstring}")
            ))
    
    def _extract_enums(self, source: str, lines: List[str]) -> None:
        """Extract enum declarations"""
        for match in self.ENUM_PATTERN.finditer(source):
            name = match.group('name')
            vis = match.group('vis') or 'private'
            visibility = 'public' if vis and 'pub' in vis else 'private'
            
            line_num = source[:match.start()].count('\n') + 1
            docstring, attributes = self._extract_doc_and_attrs(lines, line_num - 2)
            
            vector_id = f"ouroboros::{self.module}::{name}"
            
            self.vectors.append(VectorMetadata(
                vector_id=vector_id,
                type="enum",
                name=name,
                module=self.module,
                file_path=str(self.relative_path),
                language="rust",
                line_start=line_num,
                line_end=line_num,
                signature=f"enum {name}",
                docstring=docstring,
                visibility=visibility,
                attributes=attributes,
                hash=self._compute_hash(f"{name}{docstring}")
            ))
    
    def _extract_impls(self, source: str, lines: List[str]) -> None:
        """Extract impl blocks"""
        for match in self.IMPL_PATTERN.finditer(source):
            name = match.group('name')
            line_num = source[:match.start()].count('\n') + 1
            docstring, attributes = self._extract_doc_and_attrs(lines, line_num - 2)
            
            vector_id = f"ouroboros::{self.module}::impl_{name}"
            
            self.vectors.append(VectorMetadata(
                vector_id=vector_id,
                type="impl",
                name=f"impl {name}",
                module=self.module,
                file_path=str(self.relative_path),
                language="rust",
                line_start=line_num,
                line_end=line_num,
                signature=f"impl {name}",
                docstring=docstring,
                attributes=attributes,
                hash=self._compute_hash(f"impl {name}{docstring}")
            ))
    
    def _extract_doc_and_attrs(self, lines: List[str], before_line: int) -> tuple:
        """Extract doc comments and attributes before a declaration"""
        doc_lines = []
        attributes = []
        
        # Look backwards from the line before the declaration
        idx = before_line
        while idx >= 0:
            line = lines[idx].strip()
            
            # Check for doc comment
            if line.startswith('///'):
                doc_lines.insert(0, line[3:].strip())
                idx -= 1
            # Check for attribute
            elif line.startswith('#['):
                attributes.insert(0, line)
                idx -= 1
            # Empty line or regular comment
            elif not line or line.startswith('//'):
                idx -= 1
            else:
                # Hit non-doc/non-attr line
                break
        
        docstring = ' '.join(doc_lines)
        return docstring, attributes
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


class CodebaseVectorizer:
    """Main vectorizer that scans the entire codebase"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.vectors: List[VectorMetadata] = []
        
    def scan(self) -> List[VectorMetadata]:
        """Scan the entire repository and extract all code vectors"""
        print(f"Scanning repository at: {self.repo_root}")
        
        for root, dirs, files in os.walk(self.repo_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            
            root_path = Path(root)
            
            for file in files:
                file_path = root_path / file
                suffix = file_path.suffix
                
                # Process Python files
                if suffix in PYTHON_EXTENSIONS:
                    parser = PythonParser(str(file_path), self.repo_root)
                    vectors = parser.parse()
                    self.vectors.extend(vectors)
                    if vectors:
                        print(f"  Parsed {len(vectors)} vectors from {file_path.relative_to(self.repo_root)}")
                
                # Process Rust files
                elif suffix in RUST_EXTENSIONS:
                    parser = RustParser(str(file_path), self.repo_root)
                    vectors = parser.parse()
                    self.vectors.extend(vectors)
                    if vectors:
                        print(f"  Parsed {len(vectors)} vectors from {file_path.relative_to(self.repo_root)}")
        
        print(f"\nTotal vectors extracted: {len(self.vectors)}")
        return self.vectors
    
    def save_to_json(self, output_path: Path) -> None:
        """Save vectors to JSON file"""
        data = {
            "metadata": {
                "version": "1.0.0",
                "repository": "AIOSPANDORA/Ouroboros",
                "total_vectors": len(self.vectors),
                "languages": list(set(v.language for v in self.vectors)),
                "types": list(set(v.type for v in self.vectors))
            },
            "vectors": [v.to_dict() for v in self.vectors]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nVectors saved to: {output_path}")
        print(f"  Total vectors: {len(self.vectors)}")
        print(f"  Languages: {', '.join(data['metadata']['languages'])}")
        print(f"  Types: {', '.join(data['metadata']['types'])}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Vectorize Ouroboros codebase into machine-readable manifest'
    )
    parser.add_argument(
        '--output', '-o',
        default='vectors.json',
        help='Output JSON file path (default: vectors.json)'
    )
    parser.add_argument(
        '--root', '-r',
        default='.',
        help='Repository root directory (default: current directory)'
    )
    
    args = parser.parse_args()
    
    repo_root = Path(args.root).resolve()
    output_path = Path(args.output).resolve()
    
    if not repo_root.exists():
        print(f"Error: Repository root does not exist: {repo_root}", file=sys.stderr)
        sys.exit(1)
    
    # Create vectorizer and scan
    vectorizer = CodebaseVectorizer(repo_root)
    vectorizer.scan()
    
    # Save to JSON
    vectorizer.save_to_json(output_path)
    
    print("\n✓ Vectorization complete!")


if __name__ == '__main__':
    main()
