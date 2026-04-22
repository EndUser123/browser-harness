import json
import os
import socket
import tempfile
import time
import urllib.request
from pathlib import Path

from _compat import client_connect, daemon_alive as _daemon_alive, paths, _tmpdir, remove_transport


def _load_env():
    p = Path(__file__).parent / ".env"
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env()

NAME = os.environ.get("BU_NAME", "default")
BU_API = "https://api.browser-use.com/api/v3"
MAX_INSTANCES = 8
BASE_PORT = 9222
PROFILE_BASE = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "browser-harness"


def _log_tail(name):
    _, _, log_path = paths(name or NAME)
    try:
        return Path(log_path).read_text().strip().splitlines()[-1]
    except (FileNotFoundError, IndexError):
        return None


def daemon_alive(name=None):
    return _daemon_alive(name or NAME)


def ensure_daemon(wait=60.0, name=None, env=None):
    """Idempotent. `env` is merged into the child process env.

    If no Chrome with CDP is found and BU_CDP_WS isn't set, launches a
    dedicated Chrome instance via launch_browser().
    """
    if daemon_alive(name):
        return
    import subprocess

    # If no explicit CDP target, try to find or launch a browser
    effective_name = name or NAME
    has_cdp_target = bool(env and env.get("BU_CDP_WS")) or bool(os.environ.get("BU_CDP_WS"))
    if not has_cdp_target:
        # Check if an existing Chrome already has CDP (devtools active)
        from daemon import get_ws_url
        try:
            get_ws_url()
        except RuntimeError:
            # No existing CDP — launch our own Chrome instance
            browser = launch_browser(effective_name)
            env = {**(env or {}), "BU_CDP_WS": browser["ws_url"]}

    e = {**os.environ, **({"BU_NAME": name} if name else {}), **(env or {})}
    popen_kwargs: dict = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = 0x00000200 | 0x08000000  # CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    else:
        popen_kwargs["start_new_session"] = True
    p = subprocess.Popen(
        ["uv", "run", "daemon.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=e,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **popen_kwargs,
    )
    deadline = time.time() + wait
    while time.time() < deadline:
        if daemon_alive(name):
            return
        if p.poll() is not None:
            break
        time.sleep(0.2)
    msg = _log_tail(name)
    _, _, log_path = paths(name or NAME)
    raise RuntimeError(msg or f"daemon {name or NAME} didn't come up -- check {log_path}")


def stop_remote_daemon(name="remote"):
    """Stop a remote daemon and its backing Browser Use cloud browser.

    Triggers the daemon's clean shutdown, which PATCHes
    /browsers/{id} {"action":"stop"} so billing ends and any profile
    state in the session is persisted."""
    # restart_daemon is misnamed — it only stops the daemon (sends
    # shutdown, SIGTERMs if needed, unlinks socket+pid). It never
    # restarts anything on its own; a follow-up `browser-harness`
    # call would auto-spawn a fresh one via ensure_daemon(). That
    # "run-it-again-to-restart" workflow is why it was named that way.
    restart_daemon(name)


def restart_daemon(name=None):
    """Best-effort daemon shutdown + socket/pid cleanup.

    Name is historical: callers typically follow this with another
    `browser-harness` invocation, which auto-spawns a fresh daemon via
    ensure_daemon(). The function itself only stops."""
    import signal

    _, pid_path, _ = paths(name or NAME)
    try:
        s = client_connect(name or NAME)
        s.sendall(b'{"meta":"shutdown"}\n')
        s.recv(1024)
        s.close()
    except Exception:
        pass
    try:
        pid = int(open(pid_path).read())
    except (FileNotFoundError, ValueError):
        pid = None
    if pid:
        for _ in range(75):
            try:
                os.kill(pid, 0)
                time.sleep(0.2)
            except (ProcessLookupError, OSError):
                break
        else:
            try:
                os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, OSError):
                pass
    # Gracefully close our launched Chrome instance (if any)
    close_browser(name)
    remove_transport(name or NAME)


def _browser_use(path, method, body=None):
    key = os.environ.get("BROWSER_USE_API_KEY")
    if not key:
        raise RuntimeError("BROWSER_USE_API_KEY missing -- see .env.example")
    req = urllib.request.Request(
        f"{BU_API}{path}",
        method=method,
        data=(json.dumps(body).encode() if body is not None else None),
        headers={"X-Browser-Use-API-Key": key, "Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=60).read() or b"{}")


def _cdp_ws_from_url(cdp_url):
    return json.loads(urllib.request.urlopen(f"{cdp_url}/json/version", timeout=15).read())["webSocketDebuggerUrl"]


def _has_local_gui():
    """True when this machine plausibly has a browser we can open. False on headless servers."""
    import platform
    system = platform.system()
    if system in ("Darwin", "Windows"):
        return True
    if system == "Linux":
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return False


def _chrome_exe() -> str:
    """Find the Chrome executable on this system."""
    import platform, shutil
    system = platform.system()
    if system == "Windows":
        for p in [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]:
            if os.path.isfile(p):
                return p
    elif system == "Darwin":
        p = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.isfile(p):
            return p
    else:
        p = shutil.which("google-chrome") or shutil.which("chromium-browser") or shutil.which("chrome")
        if p:
            return p
    raise RuntimeError("Chrome not found — install Google Chrome or set BU_CDP_WS manually")


def _port_alive(port: int) -> bool:
    s = socket.socket()
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except (ConnectionRefusedError, socket.timeout, OSError):
        return False


def _fix_exit_type(profile_dir: Path):
    """Set exit_type=Normal in a Chrome profile so no 'restore pages' bubble appears."""
    try:
        prefs_path = profile_dir / "Default" / "Preferences"
        if prefs_path.exists():
            p = json.loads(prefs_path.read_text())
            p.setdefault("profile", {})["exited_cleanly"] = True
            p["profile"]["exit_type"] = "Normal"
            prefs_path.write_text(json.dumps(p))
    except Exception:
        pass


def launch_browser(name: str = None) -> dict:
    """Launch a dedicated Chrome instance for the harness.

    Creates a fresh profile under %LOCALAPPDATA%/browser-harness/<name>/,
    picks a free port from BASE_PORT..BASE_PORT+MAX_INSTANCES-1,
    starts Chrome, and returns {port, profile_dir, ws_url}.

    Raises RuntimeError if all slots are taken.
    """
    import subprocess
    name = name or NAME
    profile_dir = PROFILE_BASE / name
    profile_dir.mkdir(parents=True, exist_ok=True)

    # Fix stale crash state so no "restore pages" bubble appears
    _fix_exit_type(profile_dir)

    # Find a free port slot
    port = None
    for p in range(BASE_PORT, BASE_PORT + MAX_INSTANCES):
        if not _port_alive(p):
            port = p
            break
    if port is None:
        raise RuntimeError(
            f"All {MAX_INSTANCES} browser harness slots ({BASE_PORT}-{BASE_PORT + MAX_INSTANCES - 1}) are in use"
        )

    chrome = _chrome_exe()
    args = [
        chrome,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-timer-throttling",
        "about:blank",
    ]
    popen_kwargs: dict = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = 0x00000200 | 0x08000000  # CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    else:
        popen_kwargs["start_new_session"] = True
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **popen_kwargs)

    # Wait for Chrome to be ready
    deadline = time.time() + 30
    ws_url = None
    while time.time() < deadline:
        if _port_alive(port):
            try:
                import urllib.request as _ur
                info = json.loads(_ur.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=3).read())
                ws_url = info["webSocketDebuggerUrl"]
                break
            except Exception:
                pass
        time.sleep(0.5)
    if not ws_url:
        raise RuntimeError(f"Chrome started on port {port} but /json/version never responded")

    # Persist Chrome PID so we can close it gracefully later
    _, pid_path, _ = paths(name)
    chrome_pid_path = pid_path.replace(".pid", ".chrome-pid")
    open(chrome_pid_path, "w").write(str(proc.pid))

    return {"port": port, "profile_dir": str(profile_dir), "ws_url": ws_url}


def close_browser(name: str = None):
    """Gracefully close a Chrome instance launched by launch_browser().

    Sends Browser.close via CDP first, then waits. Falls back to SIGTERM.
    Also fixes the profile's exit_type so no 'restore pages' bubble appears.
    """
    import signal
    name = name or NAME

    # Read persisted Chrome PID
    _, pid_path, _ = paths(name)
    chrome_pid_path = pid_path.replace(".pid", ".chrome-pid")
    try:
        chrome_pid = int(open(chrome_pid_path).read().strip())
    except (FileNotFoundError, ValueError):
        chrome_pid = None

    # Try graceful CDP Browser.close first
    if chrome_pid:
        try:
            port = None
            for p in range(BASE_PORT, BASE_PORT + MAX_INSTANCES):
                if _port_alive(p):
                    try:
                        url = f"http://127.0.0.1:{p}/json/version"
                        info = json.loads(urllib.request.urlopen(url, timeout=2).read())
                        port = p
                        break
                    except Exception:
                        pass
            if port:
                # Send Browser.close via HTTP (lighter than opening a WS)
                try:
                    urllib.request.urlopen(
                        urllib.request.Request(
                            f"http://127.0.0.1:{port}/json/protocol",
                            data=json.dumps({"id": 1, "method": "Browser.close"}).encode(),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        ),
                        timeout=5,
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # Wait for Chrome to exit gracefully
        for _ in range(20):
            try:
                os.kill(chrome_pid, 0)
                time.sleep(0.5)
            except (ProcessLookupError, OSError):
                break
        else:
            # Still running — SIGTERM as fallback
            try:
                os.kill(chrome_pid, signal.SIGTERM)
            except (ProcessLookupError, OSError):
                pass

    # Fix profile exit_type so no "restore pages" bubble appears
    _fix_exit_type(PROFILE_BASE / name)

    # Clean up PID file
    try:
        os.unlink(chrome_pid_path)
    except FileNotFoundError:
        pass


def _show_live_url(url):
    """Print liveUrl and auto-open it locally if there's a GUI."""
    import sys, webbrowser
    if not url: return
    print(url)
    if not _has_local_gui():
        print("(no local GUI — share the liveUrl with the user)", file=sys.stderr)
        return
    try:
        webbrowser.open(url, new=2)
        print("(opened liveUrl in your default browser)", file=sys.stderr)
    except Exception as e:
        print(f"(couldn't auto-open: {e} — share the liveUrl with the user)", file=sys.stderr)


def list_cloud_profiles():
    """List cloud profiles under the current API key.

    Returns [{id, name, userId, cookieDomains, lastUsedAt}, ...]. `cookieDomains`
    is the array of domain strings the cloud profile has cookies for — use
    `len(cookieDomains)` as a cheap 'how much is logged in' summary. Per-cookie
    detail on a *local* profile before sync: `profile-use inspect --profile <name>`.

    Paginates through all pages — the API caps `pageSize` at 100."""
    out, page = [], 1
    while True:
        listing = _browser_use(f"/profiles?pageSize=100&pageNumber={page}", "GET")
        items = listing.get("items") if isinstance(listing, dict) else listing
        if not items:
            break
        for p in items:
            detail = _browser_use(f"/profiles/{p['id']}", "GET")
            out.append({
                "id": detail["id"],
                "name": detail.get("name"),
                "userId": detail.get("userId"),
                "cookieDomains": detail.get("cookieDomains") or [],
                "lastUsedAt": detail.get("lastUsedAt"),
            })
        if isinstance(listing, dict) and len(out) >= listing.get("totalItems", len(out)):
            break
        page += 1
    return out


def _resolve_profile_name(profile_name):
    """Find a single cloud profile by exact name; raise if 0 or >1 match."""
    matches = [p for p in list_cloud_profiles() if p.get("name") == profile_name]
    if not matches:
        raise RuntimeError(f"no cloud profile named {profile_name!r} -- call list_cloud_profiles() or sync_local_profile() first")
    if len(matches) > 1:
        raise RuntimeError(f"{len(matches)} cloud profiles named {profile_name!r} -- pass profileId=<uuid> instead")
    return matches[0]["id"]


def start_remote_daemon(name="remote", profileName=None, **create_kwargs):
    """Provision a Browser Use cloud browser and start a daemon attached to it.

    kwargs forwarded to `POST /browsers` (camelCase):
      profileId        — cloud profile UUID; start already-logged-in. Default: none (clean browser).
      profileName      — cloud profile name; resolved client-side to profileId via list_cloud_profiles().
      proxyCountryCode — ISO2 country code (default "us"); pass None to disable the BU proxy.
      timeout          — minutes, 1..240.
      customProxy      — {host, port, username, password, ignoreCertErrors}.
      browserScreenWidth / browserScreenHeight, allowResizing, enableRecording.

    Returns the full browser dict including `liveUrl`. Prints the liveUrl and
    auto-opens it locally when a GUI is detected, so the user can watch along."""
    if daemon_alive(name):
        raise RuntimeError(f"daemon {name!r} already alive -- restart_daemon({name!r}) first")
    if profileName:
        if "profileId" in create_kwargs:
            raise RuntimeError("pass profileName OR profileId, not both")
        create_kwargs["profileId"] = _resolve_profile_name(profileName)
    browser = _browser_use("/browsers", "POST", create_kwargs)
    ensure_daemon(
        name=name,
        env={"BU_CDP_WS": _cdp_ws_from_url(browser["cdpUrl"]), "BU_BROWSER_ID": browser["id"]},
    )
    _show_live_url(browser.get("liveUrl"))
    return browser


def list_local_profiles():
    """Detected local browser profiles on this machine. Shells out to `profile-use list --json`.
    Returns [{BrowserName, BrowserPath, ProfileName, ProfilePath, DisplayName}, ...].
    Requires `profile-use` (see interaction-skills/profile-sync.md for install)."""
    import json, shutil, subprocess
    if not shutil.which("profile-use"):
        raise RuntimeError("profile-use not installed -- curl -fsSL https://browser-use.com/profile.sh | sh")
    return json.loads(subprocess.check_output(["profile-use", "list", "--json"], text=True))


def sync_local_profile(profile_name, browser=None, cloud_profile_id=None,
                        include_domains=None, exclude_domains=None):
    """Sync a local profile's cookies to a cloud profile. Returns the cloud UUID.

    Shells out to `profile-use sync` (v1.0.4+). Requires BROWSER_USE_API_KEY and the
    target local Chrome profile to be closed (profile-use needs an exclusive lock on
    the Cookies DB).

    Args:
      profile_name:       local Chrome profile name (as shown by `list_local_profiles`).
      browser:            disambiguate when multiple browsers have profiles of the
                          same name (e.g. "Google Chrome"). Default: any match.
      cloud_profile_id:   push cookies into this existing cloud profile instead of
                          creating a new one. Idempotent — call again to refresh
                          the same profile. Default: create new.
      include_domains:    only sync cookies for these domains (and subdomains).
                          Leading dot is optional. Example: ["google.com", "stripe.com"].
      exclude_domains:    drop cookies for these domains (and subdomains). Applied
                          before `include_domains` so exclude wins on overlap."""
    import os, re, shutil, subprocess, sys
    if not shutil.which("profile-use"):
        raise RuntimeError("profile-use not installed -- curl -fsSL https://browser-use.com/profile.sh | sh")
    if not os.environ.get("BROWSER_USE_API_KEY"):
        raise RuntimeError("BROWSER_USE_API_KEY missing")
    cmd = ["profile-use", "sync", "--profile", profile_name]
    if browser:
        cmd += ["--browser", browser]
    if cloud_profile_id:
        cmd += ["--cloud-profile-id", cloud_profile_id]
    for d in include_domains or []:
        cmd += ["--domain", d]
    for d in exclude_domains or []:
        cmd += ["--exclude-domain", d]
    r = subprocess.run(cmd, text=True, capture_output=True)
    sys.stdout.write(r.stdout)
    sys.stderr.write(r.stderr)
    if r.returncode != 0:
        raise RuntimeError(f"profile-use sync failed (exit {r.returncode})")
    # With --cloud-profile-id the tool prints "♻️ Using existing cloud profile"
    # instead of "Profile created: <uuid>", so we already know the UUID.
    if cloud_profile_id:
        return cloud_profile_id
    m = re.search(r"Profile created:\s+([0-9a-f-]{36})", r.stdout)
    if not m:
        raise RuntimeError(f"profile-use did not report a profile UUID (exit {r.returncode})")
    return m.group(1)
