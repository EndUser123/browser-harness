import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js, page_info, cdp
ensure_daemon()
new_tab('http://localhost:9795/index.html')
wait_for_load()
import time; time.sleep(3)
# Get console messages
msgs = cdp("Runtime.evaluate", expression="window.__consoleMsgs", returnByValue=True)
print("console msgs:", msgs)
# Check if initMermaid exists
initm = cdp("Runtime.evaluate", expression="typeof initMermaid", returnByValue=True)
print("initMermaid type:", initm)
# Check error div
err = cdp("Runtime.evaluate", expression="document.getElementById('diagramError')?document.getElementById('diagramError').textContent:'no div'", returnByValue=True)
print("error div:", err)
