#!/usr/bin/env python3
"""
EDEN IPC Tests
==============

Unit tests for the EDEN IPC protocol and daemon functionality.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import json
import os
import socket
import sys
import threading
import time
import unittest
from pathlib import Path

# Add parent directory to path
SCRIPT_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(SCRIPT_DIR))

from eden_ipc import (
    make_request, make_response, make_error, parse_message,
    SOCKET_PATH
)


class TestIPCProtocol(unittest.TestCase):
    """Test IPC protocol functions."""
    
    def test_make_request_simple(self):
        """Test simple request creation."""
        request = make_request("get_status", request_id=1)
        data = json.loads(request)
        
        self.assertEqual(data["method"], "get_status")
        self.assertEqual(data["id"], 1)
        self.assertNotIn("params", data)
        self.assertTrue(request.endswith("\n"))
    
    def test_make_request_with_params(self):
        """Test request with parameters."""
        params = {"entity_id": "abc-123"}
        request = make_request("get_entity", params=params, request_id=2)
        data = json.loads(request)
        
        self.assertEqual(data["method"], "get_entity")
        self.assertEqual(data["id"], 2)
        self.assertEqual(data["params"], params)
    
    def test_make_request_auto_id(self):
        """Test request with auto-generated ID."""
        request = make_request("get_status")
        data = json.loads(request)
        
        self.assertIn("id", data)
        self.assertIsInstance(data["id"], int)
    
    def test_make_response(self):
        """Test response creation."""
        result = {"running": True, "tick": 42}
        response = make_response(1, result)
        data = json.loads(response)
        
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["result"], result)
        self.assertNotIn("error", data)
        self.assertTrue(response.endswith("\n"))
    
    def test_make_error(self):
        """Test error response creation."""
        error = make_error(1, -32601, "Method not found")
        data = json.loads(error)
        
        self.assertEqual(data["id"], 1)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32601)
        self.assertEqual(data["error"]["message"], "Method not found")
        self.assertNotIn("result", data)
    
    def test_parse_message(self):
        """Test message parsing."""
        message = '{"method": "get_status", "id": 1}\n'
        data = parse_message(message)
        
        self.assertEqual(data["method"], "get_status")
        self.assertEqual(data["id"], 1)
    
    def test_parse_message_no_newline(self):
        """Test parsing message without newline."""
        message = '{"method": "get_status", "id": 1}'
        data = parse_message(message)
        
        self.assertEqual(data["method"], "get_status")
        self.assertEqual(data["id"], 1)
    
    def test_round_trip(self):
        """Test request/response round trip."""
        # Create request
        request = make_request("get_status", request_id=123)
        request_data = parse_message(request)
        
        # Create response
        result = {"running": True}
        response = make_response(request_data["id"], result)
        response_data = parse_message(response)
        
        self.assertEqual(response_data["id"], request_data["id"])
        self.assertEqual(response_data["result"], result)


class TestSocketConnection(unittest.TestCase):
    """Test socket connection and basic request/response flow."""
    
    def setUp(self):
        """Setup test socket."""
        # Use a test-specific socket path
        self.test_socket = "/tmp/eden_test.sock"
        
        # Remove socket if it exists
        if os.path.exists(self.test_socket):
            os.unlink(self.test_socket)
        
        # Create server socket
        self.server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.server.bind(self.test_socket)
        self.server.listen(1)
        
        # Start server thread
        self.server_running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        
        # Give server time to start
        time.sleep(0.1)
    
    def tearDown(self):
        """Cleanup test socket."""
        self.server_running = False
        
        # Close server
        try:
            self.server.close()
        except:
            pass
        
        # Remove socket
        if os.path.exists(self.test_socket):
            os.unlink(self.test_socket)
    
    def _run_server(self):
        """Simple test server."""
        self.server.settimeout(1.0)
        
        while self.server_running:
            try:
                client, addr = self.server.accept()
                
                # Receive request
                data = b""
                while b"\n" not in data:
                    chunk = client.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                
                if data:
                    # Parse request
                    request = parse_message(data.decode('utf-8'))
                    
                    # Send response
                    if request.get("method") == "get_status":
                        response = make_response(request["id"], {"running": True})
                    elif request.get("method") == "invalid_method":
                        response = make_error(request["id"], -32601, "Method not found")
                    else:
                        response = make_response(request["id"], {"success": True})
                    
                    client.sendall(response.encode('utf-8'))
                
                client.close()
            
            except socket.timeout:
                continue
            except Exception:
                break
    
    def test_socket_connection(self):
        """Test basic socket connection."""
        # Connect to test server
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(self.test_socket)
        
        # Send request
        request = make_request("get_status", request_id=1)
        client.sendall(request.encode('utf-8'))
        
        # Receive response
        data = b""
        while b"\n" not in data:
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
        
        # Parse response
        response = parse_message(data.decode('utf-8'))
        
        self.assertEqual(response["id"], 1)
        self.assertIn("result", response)
        self.assertTrue(response["result"]["running"])
        
        client.close()
    
    def test_error_response(self):
        """Test error response handling."""
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(self.test_socket)
        
        # Send invalid request
        request = make_request("invalid_method", request_id=1)
        client.sendall(request.encode('utf-8'))
        
        # Receive response
        data = b""
        while b"\n" not in data:
            chunk = client.recv(4096)
            if not chunk:
                break
            data += chunk
        
        response = parse_message(data.decode('utf-8'))
        
        self.assertEqual(response["id"], 1)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32601)
        
        client.close()


class TestPIDFile(unittest.TestCase):
    """Test PID file creation and cleanup."""
    
    def test_pid_file_path(self):
        """Test PID file path is set."""
        from eden_ipc import PID_FILE
        
        self.assertIsNotNone(PID_FILE)
        self.assertIsInstance(PID_FILE, str)
        self.assertTrue(len(PID_FILE) > 0)
    
    def test_socket_path(self):
        """Test socket path is set."""
        self.assertIsNotNone(SOCKET_PATH)
        self.assertIsInstance(SOCKET_PATH, str)
        self.assertTrue(SOCKET_PATH.endswith("eden.sock"))


if __name__ == "__main__":
    unittest.main()
