"""Platform-abstracted IPC for daemon communication.

POSIX: AF_UNIX socket at /tmp/bu-<NAME>.sock (unchanged).
Windows: AF_INET TCP on 127.0.0.1, ephemeral port persisted to %TEMP%\bu-<NAME>.port.
"""
import asyncio
import os
import socket
import tempfile

_IS_WIN = os.name == "nt"


def _tmpdir() -> str:
    return tempfile.gettempdir()


def paths(name: str):
    """Return (transport_addr, pid_path, log_path).

    POSIX: transport_addr is a filesystem path string.
    Windows: transport_addr is the port-file path (client reads port from it).
    """
    base = _tmpdir()
    if _IS_WIN:
        return f"{base}\\bu-{name}.port", f"{base}\\bu-{name}.pid", f"{base}\\bu-{name}.log"
    return f"/tmp/bu-{name}.sock", f"/tmp/bu-{name}.pid", f"/tmp/bu-{name}.log"


def client_connect(name: str) -> socket.socket:
    """Connect to the daemon. Returns a connected socket."""
    addr, _, _ = paths(name)
    if _IS_WIN:
        with open(addr) as f:
            port = int(f.read().strip())
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect(("127.0.0.1", port))
        return s
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(addr)
    return s


def daemon_alive(name: str) -> bool:
    try:
        s = client_connect(name)
        s.close()
        return True
    except (FileNotFoundError, ConnectionRefusedError, socket.timeout, OSError):
        return False


async def start_server(handler, name: str):
    """Start the IPC server. Returns the asyncio server object."""
    if _IS_WIN:
        addr, _, _ = paths(name)
        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        with open(addr, "w") as f:
            f.write(str(port))
        return server
    addr, _, _ = paths(name)
    if os.path.exists(addr):
        os.unlink(addr)
    server = await asyncio.start_unix_server(handler, path=addr)
    os.chmod(addr, 0o600)
    return server


def remove_transport(name: str):
    addr, pid_path, _ = paths(name)
    for f in (addr, pid_path):
        try:
            os.unlink(f)
        except FileNotFoundError:
            pass
