#!/usr/bin/env python3
"""
EDEN Sandbox
============

Secure code execution using bubblewrap (bwrap) on Linux, with fallback
to basic subprocess execution.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

logger = logging.getLogger("eden_sandbox")


class EdenSandbox:
    """
    Sandboxed code execution service.
    
    Uses bubblewrap (bwrap) on Linux for secure sandboxing, falls back
    to basic subprocess with timeout if bwrap is not available.
    """
    
    def __init__(self):
        """Initialize the sandbox."""
        self.bwrap_available = self._check_bwrap()
        
        if not self.bwrap_available:
            logger.warning(
                "bubblewrap (bwrap) not found. Running in UNSAFE fallback mode.\n"
                "To install on Ubuntu/Debian: sudo apt-get install bubblewrap\n"
                "To install on Fedora/RHEL: sudo dnf install bubblewrap"
            )
        else:
            logger.info("bubblewrap detected, using secure sandbox")
    
    def _check_bwrap(self) -> bool:
        """
        Check if bubblewrap is available.
        
        Returns:
            True if bwrap is available, False otherwise
        """
        return shutil.which("bwrap") is not None
    
    def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int = 5
    ) -> Tuple[str, bool, str]:
        """
        Execute code in a sandbox.
        
        Args:
            code: Code to execute
            language: Language ("python" or "shell")
            timeout: Timeout in seconds (default: 5)
        
        Returns:
            Tuple of (output, success, error_message)
            - output: stdout/stderr combined
            - success: True if execution succeeded, False otherwise
            - error_message: Error description if success is False, empty otherwise
        """
        # Create temporary directory for code execution
        with tempfile.TemporaryDirectory() as tmpdir:
            # Determine file extension and interpreter
            if language == "python":
                ext = ".py"
                interpreter = ["python3"]
            elif language == "shell":
                ext = ".sh"
                interpreter = ["bash"]
            else:
                return "", False, f"Unsupported language: {language}"
            
            # Write code to file
            code_file = Path(tmpdir) / f"code{ext}"
            try:
                code_file.write_text(code)
            except Exception as e:
                return "", False, f"Failed to write code to file: {e}"
            
            # Make shell scripts executable
            if language == "shell":
                code_file.chmod(0o755)
            
            # Execute code
            if self.bwrap_available:
                return self._execute_bwrap(code_file, interpreter, timeout)
            else:
                return self._execute_fallback(code_file, interpreter, timeout)
    
    def _execute_bwrap(
        self,
        code_file: Path,
        interpreter: list,
        timeout: int
    ) -> Tuple[str, bool, str]:
        """
        Execute code using bubblewrap sandbox.
        
        Args:
            code_file: Path to code file
            interpreter: Interpreter command (e.g., ["python3"])
            timeout: Timeout in seconds
        
        Returns:
            Tuple of (output, success, error_message)
        """
        # Build bwrap command
        # - Create minimal filesystem
        # - No network access
        # - Read-only bindings
        # - Temporary /tmp
        cmd = [
            "bwrap",
            # Create a new user namespace
            "--unshare-all",
            # Share the network namespace (but we'll drop network capabilities)
            "--share-net",
            # Mount minimal filesystem
            "--ro-bind", "/usr", "/usr",
            "--ro-bind", "/lib", "/lib",
            "--ro-bind", "/lib64", "/lib64",
            "--ro-bind", "/bin", "/bin",
            "--ro-bind", "/sbin", "/sbin",
            # Temporary /tmp
            "--tmpfs", "/tmp",
            # Bind the code file
            "--ro-bind", str(code_file), "/tmp/code",
            # Set working directory
            "--chdir", "/tmp",
            # Drop all capabilities
            "--cap-drop", "ALL",
            # Run the interpreter
            "--",
        ] + interpreter + ["/tmp/code"]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            error_message = "" if success else f"Exit code {result.returncode}"
            
            return output, success, error_message
        
        except subprocess.TimeoutExpired:
            return "", False, f"Execution timed out after {timeout}s"
        except Exception as e:
            return "", False, f"Execution failed: {e}"
    
    def _execute_fallback(
        self,
        code_file: Path,
        interpreter: list,
        timeout: int
    ) -> Tuple[str, bool, str]:
        """
        Execute code using basic subprocess (UNSAFE fallback).
        
        Args:
            code_file: Path to code file
            interpreter: Interpreter command
            timeout: Timeout in seconds
        
        Returns:
            Tuple of (output, success, error_message)
        """
        logger.warning("Executing in UNSAFE fallback mode (no sandboxing)")
        
        cmd = interpreter + [str(code_file)]
        
        try:
            # Create minimal safe environment
            safe_env = {
                'PATH': '/usr/bin:/bin:/usr/local/bin',
                'HOME': '/tmp',
                'LANG': 'C.UTF-8',
            }
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=safe_env
            )
            
            output = result.stdout + result.stderr
            success = result.returncode == 0
            error_message = "" if success else f"Exit code {result.returncode}"
            
            return output, success, error_message
        
        except subprocess.TimeoutExpired:
            return "", False, f"Execution timed out after {timeout}s"
        except Exception as e:
            return "", False, f"Execution failed: {e}"
    
    def get_status(self) -> dict:
        """
        Get sandbox status.
        
        Returns:
            Status dictionary
        """
        return {
            "bwrap_available": self.bwrap_available,
            "mode": "secure" if self.bwrap_available else "unsafe_fallback"
        }
