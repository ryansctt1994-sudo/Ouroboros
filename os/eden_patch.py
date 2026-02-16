#!/usr/bin/env python3
"""
EDEN Patch Manager
==================

Apply unified diffs to the repository and manage service restarts.

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

logger = logging.getLogger("eden_patch")


class EdenPatch:
    """
    Patch manager for applying unified diffs.
    
    Uses the `patch` command to apply diffs, with support for
    dry-run mode and automatic service restart.
    """
    
    def __init__(self, repo_root: str = None):
        """
        Initialize the patch manager.
        
        Args:
            repo_root: Root directory of the repository (default: current directory)
        """
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.patch_available = self._check_patch()
        
        if not self.patch_available:
            logger.warning(
                "patch command not found. Patch application will be unavailable.\n"
                "To install on Ubuntu/Debian: sudo apt-get install patch\n"
                "To install on Fedora/RHEL: sudo dnf install patch"
            )
        else:
            logger.info("patch command available")
    
    def _check_patch(self) -> bool:
        """
        Check if patch command is available.
        
        Returns:
            True if patch is available, False otherwise
        """
        return shutil.which("patch") is not None
    
    def apply(self, diff: str, dry_run: bool = False) -> Tuple[bool, str]:
        """
        Apply a unified diff to the repository.
        
        Args:
            diff: Unified diff content
            dry_run: If True, test without applying (default: False)
        
        Returns:
            Tuple of (success, message)
            - success: True if patch applied successfully, False otherwise
            - message: Status message or error description
        """
        if not self.patch_available:
            return False, "patch command not available"
        
        if not diff.strip():
            return False, "Empty diff provided"
        
        # Write diff to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
            diff_file = f.name
            f.write(diff)
        
        try:
            # Build patch command
            cmd = ["patch"]
            
            if dry_run:
                cmd.append("--dry-run")
            
            # Options:
            # -p1: Strip first path component (standard for git diffs)
            # -i: Input file
            # -f: Force (don't ask questions)
            # --verbose: Verbose output
            cmd.extend(["-p1", "-i", diff_file, "-f", "--verbose"])
            
            # Run patch command in repository root
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                if dry_run:
                    message = f"Dry-run successful. Patch can be applied.\n{output}"
                else:
                    message = f"Patch applied successfully.\n{output}"
                return True, message
            else:
                message = f"Patch failed (exit code {result.returncode}).\n{output}"
                return False, message
        
        except Exception as e:
            return False, f"Failed to apply patch: {e}"
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(diff_file)
            except:
                pass
    
    def restart_service(self) -> Tuple[bool, str]:
        """
        Restart the EDEN systemd user service.
        
        Returns:
            Tuple of (success, message)
        """
        # Check if systemctl is available
        if not shutil.which("systemctl"):
            return False, "systemctl not available (not running on systemd)"
        
        try:
            # Try to restart user service
            result = subprocess.run(
                ["systemctl", "--user", "restart", "eden.service"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "EDEN service restarted successfully"
            else:
                # Service might not be installed/enabled
                return False, f"Failed to restart service: {result.stderr}"
        
        except subprocess.TimeoutExpired:
            return False, "Service restart timed out"
        except Exception as e:
            return False, f"Failed to restart service: {e}"
    
    def get_status(self) -> dict:
        """
        Get patch manager status.
        
        Returns:
            Status dictionary
        """
        return {
            "patch_available": self.patch_available,
            "repo_root": str(self.repo_root)
        }
