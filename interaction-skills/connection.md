# Connection & Tab Visibility

The daemon connects to Chrome via CDP and attaches to a page. Common failure: it attaches to an invisible target (omnibox popup, detached tab) and all work happens where the user can't see it.

## Before doing anything

```python
# 1. Check if daemon is already running
from admin import daemon_alive
if daemon_alive():
    print("daemon already running")
else:
    print("need to start daemon")
    ensure_daemon()

# 2. List all tabs to understand what's open
tabs = list_tabs(include_chrome=True)
for t in tabs:
    print(t["targetId"][:12], t["url"][:60])
```

## Ensure the user can SEE the page

The daemon often attaches to `chrome://omnibox-popup.top-chrome/` (invisible 1px viewport). Always switch to a real tab AND activate it:

```python
# Switch to a real tab
tab = ensure_real_tab()

# CRITICAL: activate it so it's the focused tab in Chrome
cdp("Target.activateTarget", targetId=tab["targetId"])
```

`ensure_real_tab()` switches the CDP session but does NOT make the tab visible. `Target.activateTarget` brings it to front in Chrome's UI.

## Never use new_tab() for visible work

`new_tab()` creates a tab via CDP that may end up in a detached window or behind other tabs. Instead, navigate an existing visible tab:

```python
# BAD — tab may be invisible
tid = new_tab("https://example.com")

# GOOD — navigate the tab the user is already looking at
tab = ensure_real_tab()
cdp("Target.activateTarget", targetId=tab["targetId"])
goto("https://example.com")
```

## Multiple daemons

Check for stale sockets before starting:

```python
import os
# Clean up stale sockets if daemon process is dead
if os.path.exists("/tmp/bu-default.sock"):
    if not daemon_alive():
        os.unlink("/tmp/bu-default.sock")
        os.unlink("/tmp/bu-default.pid")
```

## Startup checklist

1. `daemon_alive()` — is one already running?
2. If not: clean stale sockets, then `ensure_daemon()`
3. `list_tabs()` — see what's open
4. `ensure_real_tab()` — attach to a real page
5. `cdp("Target.activateTarget", targetId=...)` — make it visible
6. `screenshot()` + verify — confirm user can see it
