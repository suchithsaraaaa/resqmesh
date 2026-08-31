"""
ResQMesh AI: Standalone Windows Server Executable Entrypoint.
Initializes SQLite database, starts mDNS Zeroconf peer discovery, and launches FastAPI.
"""

import sys
import os
import argparse
import socket
import uvicorn

# Handle PyInstaller path resolution for both onedir and onefile
if getattr(sys, "frozen", False):
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.abspath(os.path.join(base_dir, "..")))

# Ensure any "from backend.app..." import resolves seamlessly in PyInstaller
import types
if "backend" not in sys.modules:
    backend_module = types.ModuleType("backend")
    backend_module.__path__ = [base_dir]
    sys.modules["backend"] = backend_module

try:
    from app.main import app
    import app as app_pkg
    sys.modules["backend.app"] = app_pkg
except ImportError:
    from backend.app.main import app


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently occupied."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    """Find first available TCP port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(p):
            return p
    return start_port


def main():
    parser = argparse.ArgumentParser(description="ResQMesh AI Node Core Engine")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Network host interface to bind")
    parser.add_argument("--port", type=int, default=None, help="TCP port to bind (default: 8000 or next available)")
    args = parser.parse_args()

    default_port = int(os.environ.get("RESQMESH_PORT", 8000))
    target_port = args.port if args.port is not None else find_available_port(default_port)

    print("=" * 70)
    print("   [+] ResQMesh AI: Standalone Emergency Response Node Server")
    print("=" * 70)
    print(f"   [*] Active Port: {target_port} (Bound to {args.host})")
    print(f"   [*] Local Health: http://127.0.0.1:{target_port}/health")
    print(f"   [*] Interactive Docs: http://127.0.0.1:{target_port}/docs\n")

    uvicorn.run(app, host=args.host, port=target_port, log_level="info")


if __name__ == "__main__":
    main()
