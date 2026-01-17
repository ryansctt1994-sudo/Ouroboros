"""
Test suite for dummy_tenant.py and genesis_mandate.json validation.

This test validates the Genesis Pipeline's foundational components:
- Schema validation for genesis mandates
- Witness report generation
- Log file creation and content validation
"""

import pytest
import json
import subprocess
import sys
import os
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestDummyTenant:
    """Test suite for the dummy_tenant.py script."""

    @pytest.fixture
    def valid_mandate_path(self):
        """Return path to valid genesis_mandate.json."""
        return Path(__file__).parent.parent / "genesis_mandate.json"

    @pytest.fixture
    def temp_mandate_path(self, tmp_path):
        """Create a temporary mandate file for testing."""
        return tmp_path / "test_mandate.json"

    def run_tenant(self, mandate_path):
        """Helper to run dummy_tenant.py and return output."""
        script_path = Path(__file__).parent.parent / "dummy_tenant.py"
        result = subprocess.run(
            [sys.executable, str(script_path), str(mandate_path)],
            capture_output=True,
            text=True,
        )
        return result

    def test_valid_mandate_success(self, valid_mandate_path):
        """Test that a valid mandate produces a successful witness report."""
        result = self.run_tenant(valid_mandate_path)
        assert result.returncode == 0
        
        report = json.loads(result.stdout)
        assert report["witness_report_version"] == "0.1"
        assert report["mandate_id"] == "GENESIS-001"
        assert report["tenant_class"] == "Witness-0.1"
        assert report["status"] == "OK"
        assert report["violations"] == []
        assert len(report["artifacts"]) == 1
        assert report["artifacts"][0]["type"] == "log"
        assert "genesis.log" in report["artifacts"][0]["path"]
        assert "elapsed_ms" in report["metrics"]
        assert report["metrics"]["declared_max_seconds"] == 30
        assert report["metrics"]["declared_max_tokens"] == 1000

    def test_no_arguments_failure(self):
        """Test that running without arguments produces proper error."""
        script_path = Path(__file__).parent.parent / "dummy_tenant.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        
        report = json.loads(result.stdout)
        assert report["status"] == "FAIL"
        assert "USAGE" in report["violations"][0]

    def test_nonexistent_file_failure(self):
        """Test that a nonexistent file produces proper error."""
        result = self.run_tenant(Path("nonexistent_file.json"))
        assert result.returncode == 2
        
        report = json.loads(result.stdout)
        assert report["status"] == "FAIL"
        assert "MANDATE_READ_ERROR" in report["violations"][0]

    def test_missing_required_field(self, temp_mandate_path):
        """Test that missing required fields are detected."""
        invalid_mandate = {
            "mandate_id": "TEST-001",
            # Missing tenant_class and signature fields
            "scope_boundary": ["/test"],
            "axiom_set": ["TEST"],
            "compute_budget": {"max_tokens": 100, "max_seconds": 10},
            "resource_permissions": {"read": ["/test"], "write": ["/tmp"]},
            "issued_at_utc": 1705420800,
        }
        temp_mandate_path.write_text(json.dumps(invalid_mandate))
        
        result = self.run_tenant(temp_mandate_path)
        assert result.returncode == 3
        
        report = json.loads(result.stdout)
        assert report["status"] == "FAIL"
        assert "MANDATE_SCHEMA_MISSING_FIELD" in report["violations"][0]

    def test_invalid_field_type(self, temp_mandate_path):
        """Test that invalid field types are detected."""
        invalid_mandate = {
            "mandate_id": 123,  # Should be string
            "tenant_class": "Test",
            "scope_boundary": ["/test"],
            "axiom_set": ["TEST"],
            "compute_budget": {"max_tokens": 100, "max_seconds": 10},
            "resource_permissions": {"read": ["/test"], "write": ["/tmp"]},
            "issued_at_utc": 1705420800,
            "signature": "SIG_HERE",
        }
        temp_mandate_path.write_text(json.dumps(invalid_mandate))
        
        result = self.run_tenant(temp_mandate_path)
        assert result.returncode == 3
        
        report = json.loads(result.stdout)
        assert report["status"] == "FAIL"
        assert "MANDATE_SCHEMA_TYPE_MISMATCH" in report["violations"][0]

    def test_invalid_compute_budget(self, temp_mandate_path):
        """Test that invalid compute_budget is detected."""
        invalid_mandate = {
            "mandate_id": "TEST-001",
            "tenant_class": "Test",
            "scope_boundary": ["/test"],
            "axiom_set": ["TEST"],
            "compute_budget": {"max_tokens": 100},  # Missing max_seconds
            "resource_permissions": {"read": ["/test"], "write": ["/tmp"]},
            "issued_at_utc": 1705420800,
            "signature": "SIG_HERE",
        }
        temp_mandate_path.write_text(json.dumps(invalid_mandate))
        
        result = self.run_tenant(temp_mandate_path)
        assert result.returncode == 3
        
        report = json.loads(result.stdout)
        assert report["status"] == "FAIL"
        assert "compute_budget missing max_tokens/max_seconds" in report["violations"][0]

    def test_invalid_resource_permissions(self, temp_mandate_path):
        """Test that invalid resource_permissions is detected."""
        invalid_mandate = {
            "mandate_id": "TEST-001",
            "tenant_class": "Test",
            "scope_boundary": ["/test"],
            "axiom_set": ["TEST"],
            "compute_budget": {"max_tokens": 100, "max_seconds": 10},
            "resource_permissions": {"read": ["/test"]},  # Missing write
            "issued_at_utc": 1705420800,
            "signature": "SIG_HERE",
        }
        temp_mandate_path.write_text(json.dumps(invalid_mandate))
        
        result = self.run_tenant(temp_mandate_path)
        assert result.returncode == 3
        
        report = json.loads(result.stdout)
        assert report["status"] == "FAIL"
        assert "resource_permissions missing read/write" in report["violations"][0]

    def test_invalid_scope_path(self, temp_mandate_path):
        """Test that non-absolute paths in scope_boundary are rejected."""
        invalid_mandate = {
            "mandate_id": "TEST-001",
            "tenant_class": "Test",
            "scope_boundary": ["relative/path"],  # Not absolute
            "axiom_set": ["TEST"],
            "compute_budget": {"max_tokens": 100, "max_seconds": 10},
            "resource_permissions": {"read": ["/test"], "write": ["/tmp"]},
            "issued_at_utc": 1705420800,
            "signature": "SIG_HERE",
        }
        temp_mandate_path.write_text(json.dumps(invalid_mandate))
        
        result = self.run_tenant(temp_mandate_path)
        assert result.returncode == 4
        
        report = json.loads(result.stdout)
        assert report["status"] == "FAIL"
        assert "SCOPE_INVALID_PATH" in report["violations"][0]

    def test_log_file_created(self, valid_mandate_path):
        """Test that the log file is created with correct content."""
        # Clean up existing log if present
        log_path = Path(__file__).parent.parent / "logs" / "genesis.log"
        if log_path.exists():
            log_path.unlink()
        
        result = self.run_tenant(valid_mandate_path)
        assert result.returncode == 0
        
        # Verify log file exists
        assert log_path.exists()
        
        # Verify log content
        log_content = log_path.read_text()
        assert "DummyTenant ok for GENESIS-001" in log_content
        assert log_content.startswith("[")
