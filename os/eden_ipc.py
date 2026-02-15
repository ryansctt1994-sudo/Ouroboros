#!/usr/bin/env python3
"""
EDEN IPC Protocol Definition
=============================

JSON-RPC-like protocol for Unix domain socket communication
between the EDEN daemon and CLI clients.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.0.0
"""

import json
import os
import tempfile
from typing import Any, Dict, Optional


# Socket path (platform-appropriate)
SOCKET_PATH = os.path.join(tempfile.gettempdir(), "eden.sock")

# PID file path
if os.name == 'posix':
    if os.path.exists(os.path.expanduser("~/Library")):
        # macOS
        PID_FILE = os.path.expanduser("~/Library/Application Support/eden/eden.pid")
    else:
        # Linux
        PID_FILE = os.path.expanduser("~/.local/share/eden/eden.pid")
else:
    # Fallback for other platforms
    PID_FILE = os.path.join(tempfile.gettempdir(), "eden.pid")


def make_request(method: str, params: Optional[Dict[str, Any]] = None, 
                 request_id: Optional[int] = None) -> str:
    """
    Create a JSON-RPC request.
    
    Args:
        method: Method name (e.g., "get_status", "start", "stop")
        params: Optional parameters dictionary
        request_id: Optional request ID (auto-generated if not provided)
    
    Returns:
        JSON string with newline terminator
    
    Example:
        >>> make_request("get_status", id=1)
        '{"method": "get_status", "id": 1}\\n'
    """
    if request_id is None:
        import random
        request_id = random.randint(1, 1000000)
    
    request = {
        "method": method,
        "id": request_id
    }
    
    if params is not None:
        request["params"] = params
    
    return json.dumps(request) + "\n"


def make_response(request_id: int, result: Any) -> str:
    """
    Create a JSON-RPC success response.
    
    Args:
        request_id: Request ID from the original request
        result: Result data
    
    Returns:
        JSON string with newline terminator
    
    Example:
        >>> make_response(1, {"running": True})
        '{"id": 1, "result": {"running": true}}\\n'
    """
    response = {
        "id": request_id,
        "result": result
    }
    return json.dumps(response) + "\n"


def make_error(request_id: int, code: int, message: str) -> str:
    """
    Create a JSON-RPC error response.
    
    Args:
        request_id: Request ID from the original request
        code: Error code (negative integer)
        message: Error message
    
    Returns:
        JSON string with newline terminator
    
    Example:
        >>> make_error(1, -1, "Method not found")
        '{"id": 1, "error": {"code": -1, "message": "Method not found"}}\\n'
    """
    response = {
        "id": request_id,
        "error": {
            "code": code,
            "message": message
        }
    }
    return json.dumps(response) + "\n"


def parse_message(data: str) -> Dict[str, Any]:
    """
    Parse a JSON message (request or response).
    
    Args:
        data: JSON string (may include newline)
    
    Returns:
        Parsed message dictionary
    
    Raises:
        json.JSONDecodeError: If data is not valid JSON
    
    Example:
        >>> parse_message('{"method": "get_status", "id": 1}\\n')
        {'method': 'get_status', 'id': 1}
    """
    return json.loads(data.strip())
