#!/usr/bin/env python3
"""
EDEN Patch Manager Tests
=========================

Unit tests for the patch manager.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from eden_patch import EdenPatch


class TestEdenPatch(unittest.TestCase):
    """Test EdenPatch class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.patch_mgr = EdenPatch(repo_root=self.test_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_init(self):
        """Test patch manager initialization."""
        self.assertIsNotNone(self.patch_mgr)
        self.assertEqual(str(self.patch_mgr.repo_root), self.test_dir)
        self.assertIsInstance(self.patch_mgr.patch_available, bool)
    
    def test_apply_empty_diff(self):
        """Test applying empty diff."""
        success, message = self.patch_mgr.apply("")
        
        self.assertFalse(success)
        self.assertIn("Empty diff", message)
    
    def test_apply_simple_diff_dry_run(self):
        """Test applying a simple diff in dry-run mode."""
        # Create a test file
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("Hello\nWorld\n")
        
        # Create a unified diff (git format with a/ and b/ prefixes)
        diff = """--- a/test.txt
+++ b/test.txt
@@ -1,2 +1,2 @@
-Hello
+Hi
 World
"""
        
        if self.patch_mgr.patch_available:
            success, message = self.patch_mgr.apply(diff, dry_run=True)
            
            # Dry-run should succeed
            self.assertTrue(success)
            self.assertIn("Dry-run successful", message)
            
            # Original file should be unchanged
            content = test_file.read_text()
            self.assertIn("Hello", content)
            self.assertNotIn("Hi", content)
    
    def test_apply_simple_diff_real(self):
        """Test applying a simple diff for real."""
        # Create a test file
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("Hello\nWorld\n")
        
        # Create a unified diff (git format with a/ and b/ prefixes)
        diff = """--- a/test.txt
+++ b/test.txt
@@ -1,2 +1,2 @@
-Hello
+Hi
 World
"""
        
        if self.patch_mgr.patch_available:
            success, message = self.patch_mgr.apply(diff, dry_run=False)
            
            # Should succeed
            self.assertTrue(success)
            self.assertIn("applied successfully", message)
            
            # File should be modified
            content = test_file.read_text()
            self.assertIn("Hi", content)
            self.assertNotIn("Hello", content)
    
    def test_apply_invalid_diff(self):
        """Test applying invalid diff."""
        diff = "This is not a valid diff"
        
        if self.patch_mgr.patch_available:
            success, message = self.patch_mgr.apply(diff)
            
            self.assertFalse(success)
            # patch command should fail
    
    def test_apply_diff_file_not_found(self):
        """Test applying diff for non-existent file."""
        diff = """--- nonexistent.txt
+++ nonexistent.txt
@@ -1,1 +1,1 @@
-Old
+New
"""
        
        if self.patch_mgr.patch_available:
            success, message = self.patch_mgr.apply(diff)
            
            # Should fail because file doesn't exist
            self.assertFalse(success)
    
    def test_apply_multifile_diff(self):
        """Test applying diff with multiple files."""
        # Create test files
        file1 = Path(self.test_dir) / "file1.txt"
        file2 = Path(self.test_dir) / "file2.txt"
        file1.write_text("Content 1\n")
        file2.write_text("Content 2\n")
        
        # Create multi-file diff (git format with a/ and b/ prefixes)
        diff = """--- a/file1.txt
+++ b/file1.txt
@@ -1,1 +1,1 @@
-Content 1
+Modified 1
--- a/file2.txt
+++ b/file2.txt
@@ -1,1 +1,1 @@
-Content 2
+Modified 2
"""
        
        if self.patch_mgr.patch_available:
            success, message = self.patch_mgr.apply(diff)
            
            # Should succeed
            self.assertTrue(success)
            
            # Both files should be modified
            self.assertIn("Modified 1", file1.read_text())
            self.assertIn("Modified 2", file2.read_text())
    
    def test_restart_service(self):
        """Test service restart (may fail if not on systemd)."""
        success, message = self.patch_mgr.restart_service()
        
        # We don't assert success/failure since this depends on the system
        # Just check that we get a boolean and a message
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)
        self.assertGreater(len(message), 0)
    
    def test_get_status(self):
        """Test get_status method."""
        status = self.patch_mgr.get_status()
        
        self.assertIn("patch_available", status)
        self.assertIn("repo_root", status)
        self.assertEqual(status["repo_root"], self.test_dir)


if __name__ == "__main__":
    unittest.main()
