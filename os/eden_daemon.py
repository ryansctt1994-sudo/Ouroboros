#!/usr/bin/env python3
"""
EDEN Daemon - Background System Service
========================================

Runs the EDEN ECS world as a background service, exposing control
via Unix domain socket with JSON-RPC protocol. Includes AI assistant,
sandboxed code execution, and patch management.

Author: AIOSPANDORA Development Team
License: MIT
Version: 1.1.0
"""

import argparse
import json
import logging
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add python-bridge to path
SCRIPT_DIR = Path(__file__).parent.absolute()
PYTHON_BRIDGE_DIR = SCRIPT_DIR.parent / "python-bridge"
if PYTHON_BRIDGE_DIR.exists():
    sys.path.insert(0, str(PYTHON_BRIDGE_DIR))

# Import IPC protocol
from eden_ipc import SOCKET_PATH, PID_FILE, make_response, make_error, parse_message

# Import new services
from eden_ai import EdenAI
from eden_sandbox import EdenSandbox
from eden_patch import EdenPatch

# Try to import EDEN ECS modules
try:
    from eden_ecs.core import World, EntityType
    from eden_ecs.components import Consciousness7D
    from eden_ecs.systems import ConsciousnessSystem
    try:
        from eden_ecs.mycelial_sync import MycelialSyncSystem
        from eden_ecs.mycelial_components import HyphalNodeComponent
        MYCELIAL_AVAILABLE = True
    except ImportError:
        MYCELIAL_AVAILABLE = False
    EDEN_ECS_AVAILABLE = True
except ImportError:
    EDEN_ECS_AVAILABLE = False
    MYCELIAL_AVAILABLE = False


# Setup logging
def setup_logging() -> logging.Logger:
    """Setup logging to stdout and file."""
    logger = logging.getLogger("eden_daemon")
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if sys.platform == 'darwin':
        log_dir = Path.home() / "Library" / "Logs"
        log_file = log_dir / "eden.log"
    else:
        log_dir = Path.home() / ".local" / "share" / "eden"
        log_file = log_dir / "eden.log"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


logger = setup_logging()


class MockWorld:
    """Mock world for when EDEN ECS is not available."""
    
    def __init__(self):
        self.entities = {}
        self.tick_count = 0
        self.running = False
        logger.warning("Using mock world (EDEN ECS not available)")
    
    def tick(self, dt: float = 0.016):
        """Mock tick."""
        self.tick_count += 1
        time.sleep(dt)  # Simulate work
    
    def create_entity(self, entity_type, name):
        """Mock entity creation."""
        import uuid
        entity_id = str(uuid.uuid4())
        self.entities[entity_id] = {
            'id': entity_id,
            'name': name,
            'consciousness': [0.5] * 7,
            'phase': 0.0,
            'gamma': 0.5,
            'coherence': 0.8,
            'synced': False
        }
        return type('Entity', (), {'entity_id': entity_id})()


class EdenDaemon:
    """
    EDEN daemon service.
    
    Manages the ECS world, tick loop, socket server, AI assistant,
    sandbox, and patch manager.
    """
    
    def __init__(self):
        self.world = None
        self.running = False
        self.tick_thread: Optional[threading.Thread] = None
        self.tick_interval = 1.0 / 60.0  # 60 Hz
        self.lock = threading.RLock()
        self.shutdown_flag = False
        self.socket_server: Optional[socket.socket] = None
        
        # Initialize AI, sandbox, and patch services
        self._init_services()
        
        # Initialize world
        self._init_world()
    
    def _init_services(self):
        """Initialize AI, sandbox, and patch manager services."""
        # Initialize AI service
        try:
            logger.info("Initializing AI service...")
            self.ai = EdenAI()
            
            # Try to load vectors.json if it exists
            vectors_path = SCRIPT_DIR.parent / "vectors.json"
            if vectors_path.exists():
                self.ai.load_vectors(str(vectors_path))
            
            if self.ai.is_available():
                logger.info("AI service initialized and model loaded")
            else:
                logger.warning("AI service initialized but no model loaded")
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            self.ai = None
        
        # Initialize sandbox
        try:
            logger.info("Initializing sandbox...")
            self.sandbox = EdenSandbox()
            logger.info("Sandbox initialized")
        except Exception as e:
            logger.error(f"Failed to initialize sandbox: {e}")
            self.sandbox = None
        
        # Initialize patch manager
        try:
            logger.info("Initializing patch manager...")
            repo_root = SCRIPT_DIR.parent
            self.patch_mgr = EdenPatch(str(repo_root))
            logger.info("Patch manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize patch manager: {e}")
            self.patch_mgr = None
        self.chat_history = []
    
    def _init_world(self):
        """Initialize the ECS world."""
        if EDEN_ECS_AVAILABLE:
            logger.info("Initializing EDEN ECS world")
            self.world = World("EDEN-Daemon")
            
            # Add systems
            self.world.add_system(ConsciousnessSystem(priority=20))
            
            if MYCELIAL_AVAILABLE:
                logger.info("Adding MycelialSyncSystem")
                self.world.add_system(MycelialSyncSystem(priority=45))
            else:
                logger.warning("MycelialSyncSystem not available")
            
            # Create 8 default AI agent entities
            import random
            for i in range(8):
                entity = self.world.create_entity(
                    EntityType.AI_AGENT,
                    name=f"Agent-{i}"
                )
                
                # Add consciousness with varied initial states
                consciousness = Consciousness7D(
                    awareness=random.uniform(0.4, 0.6),
                    intention=random.uniform(0.4, 0.6),
                    emotion=random.uniform(0.4, 0.6),
                    cognition=random.uniform(0.4, 0.6),
                    memory=random.uniform(0.4, 0.6),
                    creativity=random.uniform(0.4, 0.6),
                    integration=random.uniform(0.4, 0.6)
                )
                entity.add_component(consciousness)
            
            logger.info(f"Created {len(self.world.entities)} entities")
        else:
            logger.warning("EDEN ECS not available, using mock world")
            self.world = MockWorld()
            # Create mock entities
            for i in range(8):
                self.world.create_entity("ai_agent", f"Agent-{i}")
    
    def start_tick_loop(self):
        """Start the tick loop in a separate thread."""
        with self.lock:
            if self.running:
                logger.warning("Tick loop already running")
                return False
            
            self.running = True
            self.tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
            self.tick_thread.start()
            logger.info("Tick loop started")
            return True
    
    def stop_tick_loop(self):
        """Stop the tick loop."""
        with self.lock:
            if not self.running:
                logger.warning("Tick loop not running")
                return False
            
            self.running = False
            if self.tick_thread:
                self.tick_thread.join(timeout=2.0)
            logger.info("Tick loop stopped")
            return True
    
    def _tick_loop(self):
        """Main tick loop (runs in separate thread)."""
        logger.info("Tick loop thread started")
        while self.running:
            start_time = time.time()
            
            with self.lock:
                self.world.tick(self.tick_interval)
            
            elapsed = time.time() - start_time
            sleep_time = max(0, self.tick_interval - elapsed)
            time.sleep(sleep_time)
        
        logger.info("Tick loop thread stopped")
    
    def step(self):
        """Run a single tick (works even when not running)."""
        with self.lock:
            self.world.tick(self.tick_interval)
            return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get daemon status."""
        with self.lock:
            # Calculate consensus
            consensus = False
            if EDEN_ECS_AVAILABLE:
                consensus = any(e.has_tag("forge_consensus") for e in self.world.entities.values())
            
            # Calculate mean gamma
            mean_gamma = 0.5
            if EDEN_ECS_AVAILABLE and MYCELIAL_AVAILABLE:
                hyphal_entities = [e for e in self.world.entities.values() 
                                  if e.has_component(HyphalNodeComponent)]
                if hyphal_entities:
                    gammas = [e.get_component(HyphalNodeComponent).last_gamma 
                             for e in hyphal_entities]
                    mean_gamma = sum(gammas) / len(gammas) if gammas else 0.5
            
            return {
                "running": self.running,
                "tick": self.world.tick_count,
                "agents": len(self.world.entities),
                "consensus": consensus,
                "gamma": mean_gamma
            }
    
    def get_entities(self) -> List[Dict[str, Any]]:
        """Get list of entities with their status."""
        with self.lock:
            entities = []
            
            if EDEN_ECS_AVAILABLE:
                for entity in self.world.entities.values():
                    entity_data = {
                        "id": entity.entity_id,
                        "name": entity.name,
                        "phase": 0.0,
                        "gamma": 0.5,
                        "coherence": 0.8,
                        "synced": False
                    }
                    
                    # Get hyphal node data if available
                    if MYCELIAL_AVAILABLE and entity.has_component(HyphalNodeComponent):
                        hyphal = entity.get_component(HyphalNodeComponent)
                        entity_data["phase"] = hyphal.phase
                        entity_data["gamma"] = hyphal.last_gamma
                        entity_data["synced"] = hyphal.synchronized
                    
                    # Get consciousness coherence if available
                    if entity.has_component(Consciousness7D):
                        consciousness = entity.get_component(Consciousness7D)
                        entity_data["coherence"] = consciousness.coherence()
                    
                    entities.append(entity_data)
            else:
                # Mock entities
                for entity_id, entity_data in self.world.entities.items():
                    entities.append(entity_data)
            
            return entities
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed entity information."""
        with self.lock:
            if EDEN_ECS_AVAILABLE:
                entity = self.world.get_entity(entity_id)
                if not entity:
                    return None
                
                result = {
                    "id": entity.entity_id,
                    "name": entity.name,
                    # entity_type is an EntityType enum, so get its value
                    "type": entity.entity_type.value if hasattr(entity.entity_type, 'value') else str(entity.entity_type)
                }
                
                # Add consciousness 7D values
                if entity.has_component(Consciousness7D):
                    consciousness = entity.get_component(Consciousness7D)
                    result["consciousness"] = {
                        "awareness": consciousness.awareness,
                        "intention": consciousness.intention,
                        "emotion": consciousness.emotion,
                        "cognition": consciousness.cognition,
                        "memory": consciousness.memory,
                        "creativity": consciousness.creativity,
                        "integration": consciousness.integration,
                        "coherence": consciousness.coherence()
                    }
                
                # Add hyphal node data
                if MYCELIAL_AVAILABLE and entity.has_component(HyphalNodeComponent):
                    hyphal = entity.get_component(HyphalNodeComponent)
                    result["hyphal"] = {
                        "phase": hyphal.phase,
                        "gamma": hyphal.last_gamma,
                        "synchronized": hyphal.synchronized,
                        "neighbors": hyphal.neighbor_ids
                    }
                
                return result
            else:
                # Mock entity
                return self.world.entities.get(entity_id)
    
    def get_graph(self) -> Dict[str, Any]:
        """Get network graph topology."""
        with self.lock:
            nodes = []
            edges = []
            
            if EDEN_ECS_AVAILABLE and MYCELIAL_AVAILABLE:
                for entity in self.world.entities.values():
                    if entity.has_component(HyphalNodeComponent):
                        hyphal = entity.get_component(HyphalNodeComponent)
                        nodes.append({
                            "id": entity.entity_id,
                            "name": entity.name,
                            "phase": hyphal.phase,
                            "gamma": hyphal.last_gamma
                        })
                        
                        # Add edges
                        for neighbor_id in hyphal.neighbor_ids:
                            edges.append({
                                "source": entity.entity_id,
                                "target": neighbor_id
                            })
            else:
                # Mock graph
                for entity_id, entity_data in self.world.entities.items():
                    nodes.append({
                        "id": entity_id,
                        "name": entity_data.get('name', entity_id)
                    })
            
            return {"nodes": nodes, "edges": edges}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get network metrics."""
        with self.lock:
            if EDEN_ECS_AVAILABLE and MYCELIAL_AVAILABLE:
                hyphal_entities = [e for e in self.world.entities.values() 
                                  if e.has_component(HyphalNodeComponent)]
                
                if hyphal_entities:
                    gammas = [e.get_component(HyphalNodeComponent).last_gamma 
                             for e in hyphal_entities]
                    mean_gamma = sum(gammas) / len(gammas)
                    
                    coherences = []
                    for e in hyphal_entities:
                        if e.has_component(Consciousness7D):
                            coherences.append(e.get_component(Consciousness7D).coherence())
                    mean_coherence = sum(coherences) / len(coherences) if coherences else 0.0
                    
                    consensus = any(e.has_tag("forge_consensus") for e in self.world.entities.values())
                    
                    return {
                        "mean_gamma": mean_gamma,
                        "mean_coherence": mean_coherence,
                        "consensus": consensus,
                        "total_entities": len(self.world.entities),
                        "synchronized_entities": len([e for e in hyphal_entities 
                                                     if e.get_component(HyphalNodeComponent).synchronized])
                    }
            
            return {
                "mean_gamma": 0.5,
                "mean_coherence": 0.8,
                "consensus": False,
                "total_entities": len(self.world.entities),
                "synchronized_entities": 0
            }
    
    def handle_request(self, request: Dict[str, Any]) -> str:
        """Handle a JSON-RPC request."""
        method = request.get("method")
        request_id = request.get("id", 0)
        params = request.get("params", {})
        
        try:
            if method == "get_status":
                result = self.get_status()
            elif method == "get_entities":
                result = self.get_entities()
            elif method == "get_entity":
                entity_id = params.get("entity_id")
                if not entity_id:
                    return make_error(request_id, -32602, "Missing entity_id parameter")
                result = self.get_entity(entity_id)
                if result is None:
                    return make_error(request_id, -32000, f"Entity not found: {entity_id}")
            elif method == "get_graph":
                result = self.get_graph()
            elif method == "get_metrics":
                result = self.get_metrics()
            elif method == "start":
                success = self.start_tick_loop()
                result = {"success": success}
            elif method == "stop":
                success = self.stop_tick_loop()
                result = {"success": success}
            elif method == "step":
                success = self.step()
                result = {"success": success}
            elif method == "chat":
                # AI chat method
                message = params.get("message")
                if not message:
                    return make_error(request_id, -32602, "Missing message parameter")
                result = self.handle_chat(message)
            elif method == "execute_code":
                # Sandbox execution method
                code = params.get("code")
                language = params.get("language", "python")
                if not code:
                    return make_error(request_id, -32602, "Missing code parameter")
                result = self.handle_execute_code(code, language)
            elif method == "apply_patch":
                # Patch application method
                diff = params.get("diff")
                dry_run = params.get("dry_run", False)
                if not diff:
                    return make_error(request_id, -32602, "Missing diff parameter")
                result = self.handle_apply_patch(diff, dry_run)
            elif method == "shutdown":
                logger.info("Shutdown requested")
                self.shutdown_flag = True
                result = {"success": True}
            else:
                return make_error(request_id, -32601, f"Method not found: {method}")
            
            return make_response(request_id, result)
        
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return make_error(request_id, -32603, str(e))
    
    def handle_chat(self, message: str) -> Dict[str, Any]:
        """Handle AI chat with conversation memory and tool detection."""
        if self.ai is None:
            return {"response": "AI service not initialized", "error": "AI service unavailable"}

        if not self.ai.is_available():
            return {"response": "No AI model loaded.", "error": "Model not loaded"}

        try:
            # Detect tool commands in natural language
            tool_result = self._detect_and_run_tool(message)
            if tool_result:
                return tool_result

            # Add user message to history
            self.chat_history.append({"role": "user", "content": message})

            # Keep last 20 messages for context window
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]

            # Generate with full conversation history
            response_text = self.ai.generate(self.chat_history)

            # Add assistant response to history
            self.chat_history.append({"role": "assistant", "content": response_text})

            return {"response": response_text}

        except Exception as e:
            logger.error(f"Error generating AI response: {e}", exc_info=True)
            return {"response": f"Error: {str(e)}", "error": str(e)}

    def _detect_and_run_tool(self, message):
        """Detect if user wants a git/file operation and run it."""
        import subprocess
        msg = message.lower().strip()

        # Git status
        if any(p in msg for p in ["git status", "what changed", "any changes", "uncommitted"]):
            r = subprocess.run(["git", "status", "--short"], capture_output=True, text=True, cwd=os.getcwd())
            out = r.stdout.strip() or "Working tree clean."
            return {"response": "```\n" + out + "\n```"}

        # Git log
        if any(p in msg for p in ["git log", "recent commits", "last commits", "commit history"]):
            r = subprocess.run(["git", "log", "--oneline", "-10"], capture_output=True, text=True, cwd=os.getcwd())
            return {"response": "Last 10 commits:\n```\n" + r.stdout.strip() + "\n```"}

        # Git diff
        if any(p in msg for p in ["git diff", "show diff", "what did i change", "show changes"]):
            r = subprocess.run(["git", "diff", "--stat"], capture_output=True, text=True, cwd=os.getcwd())
            out = r.stdout.strip() or "No unstaged changes."
            return {"response": "```\n" + out + "\n```"}

        # Git commit + push
        if any(p in msg for p in ["commit and push", "commit & push", "push changes", "commit everything"]):
            subprocess.run(["git", "add", "-A"], capture_output=True, cwd=os.getcwd())
            commit_msg = "chore: auto-commit via EDEN chat"
            if "message:" in msg:
                commit_msg = msg.split("message:", 1)[1].strip()
            elif "msg:" in msg:
                commit_msg = msg.split("msg:", 1)[1].strip()
            r = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True, cwd=os.getcwd())
            if r.returncode != 0:
                return {"response": "Nothing to commit or error:\n```\n" + r.stderr.strip() + "\n```"}
            p = subprocess.run(["git", "push"], capture_output=True, text=True, cwd=os.getcwd())
            if p.returncode != 0:
                return {"response": "Committed but push failed:\n```\n" + p.stderr.strip() + "\n```"}
            return {"response": "Done:\n```\n" + r.stdout.strip() + "\n```"}

        # Show file
        for prefix in ["show me ", "show file ", "read file ", "open file "]:
            if prefix in msg:
                fname = msg.split(prefix, 1)[1].strip().strip("'").strip('"')
                # Try direct path and os/ path
                for try_path in [fname, "os/" + fname]:
                    if os.path.isfile(try_path):
                        with open(try_path, "r") as f:
                            txt = f.read()
                        if len(txt) > 3000:
                            txt = txt[:3000] + "\n... (truncated)"
                        return {"response": "**" + try_path + "**:\n```\n" + txt + "\n```"}
                return {"response": "File not found: " + fname}

        # List files
        if any(p in msg for p in ["list files", "what files", "show directory", "show folder"]):
            target = "."
            for prefix in ["in ", "of ", "inside "]:
                if prefix in msg:
                    target = msg.split(prefix, 1)[1].strip().strip("/")
                    break
            if os.path.isdir(target):
                files = sorted(os.listdir(target))
                listing = "\n".join(files[:50])
                return {"response": "**" + target + "/**:\n```\n" + listing + "\n```"}

        return None

    def handle_execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Handle code execution request.
        
        Args:
            code: Code to execute
            language: Language (python or shell)
        
        Returns:
            Response dictionary with output, success, and error keys
        """
        if self.sandbox is None:
            return {
                "output": "",
                "success": False,
                "error": "Sandbox not initialized"
            }
        
        try:
            output, success, error = self.sandbox.execute(code, language)
            
            return {
                "output": output,
                "success": success,
                "error": error
            }
        
        except Exception as e:
            logger.error(f"Error executing code: {e}", exc_info=True)
            return {
                "output": "",
                "success": False,
                "error": str(e)
            }
    
    def handle_apply_patch(self, diff: str, dry_run: bool = False) -> Dict[str, Any]:
        """
        Handle patch application request.
        
        Args:
            diff: Unified diff content
            dry_run: Whether to do a dry run
        
        Returns:
            Response dictionary with success and message keys
        """
        if self.patch_mgr is None:
            return {
                "success": False,
                "message": "Patch manager not initialized"
            }
        
        try:
            success, message = self.patch_mgr.apply(diff, dry_run)
            
            return {
                "success": success,
                "message": message
            }
        
        except Exception as e:
            logger.error(f"Error applying patch: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e)
            }
    
    def handle_client(self, client_socket: socket.socket, address):
        """Handle a client connection."""
        logger.info(f"Client connected: {address}")
        
        try:
            # Receive data
            data = b""
            while b"\n" not in data:
                chunk = client_socket.recv(4096)
                if not chunk:
                    break
                data += chunk
            
            if data:
                # Parse request
                request = parse_message(data.decode('utf-8'))
                logger.debug(f"Request: {request}")
                
                # Handle request
                response = self.handle_request(request)
                
                # Send response
                client_socket.sendall(response.encode('utf-8'))
        
        except Exception as e:
            logger.error(f"Error handling client: {e}", exc_info=True)
        
        finally:
            client_socket.close()
            logger.info(f"Client disconnected: {address}")
    
    def run(self):
        """Run the daemon (main loop)."""
        # Create PID file
        self._write_pid_file()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Create socket
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
        
        self.socket_server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket_server.bind(SOCKET_PATH)
        self.socket_server.listen(5)
        logger.info(f"Listening on {SOCKET_PATH}")
        
        # Accept connections
        while not self.shutdown_flag:
            try:
                self.socket_server.settimeout(1.0)
                try:
                    client_socket, address = self.socket_server.accept()
                except socket.timeout:
                    continue
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
        
        # Cleanup
        self._cleanup()
    
    def _write_pid_file(self):
        """Write PID file."""
        pid_dir = Path(PID_FILE).parent
        pid_dir.mkdir(parents=True, exist_ok=True)
        
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info(f"PID file written: {PID_FILE}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}")
        self.shutdown_flag = True
    
    def _cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up...")
        
        # Stop tick loop
        if self.running:
            self.stop_tick_loop()
        
        # Close socket
        if self.socket_server:
            self.socket_server.close()
        
        # Remove socket file
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
            logger.info(f"Removed socket: {SOCKET_PATH}")
        
        # Remove PID file
        if os.path.exists(PID_FILE):
            os.unlink(PID_FILE)
            logger.info(f"Removed PID file: {PID_FILE}")
        
        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="EDEN Daemon")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    logger.info("EDEN Daemon starting...")
    logger.info(f"Socket path: {SOCKET_PATH}")
    logger.info(f"PID file: {PID_FILE}")
    logger.info(f"EDEN ECS available: {EDEN_ECS_AVAILABLE}")
    logger.info(f"Mycelial Sync available: {MYCELIAL_AVAILABLE}")
    
    daemon = EdenDaemon()
    daemon.run()


if __name__ == "__main__":
    main()
