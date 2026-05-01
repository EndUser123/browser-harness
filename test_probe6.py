import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, cdp
ensure_daemon()
new_tab('http://localhost:9795/index.html')
wait_for_load()
import time; time.sleep(2)
# Enable console domain
cdp("Console.enable")
# Get console messages
msgs = cdp("Runtime.evaluate", expression="console.__msgs", returnByValue=True)
print("console msgs via evaluate:", msgs)
# Check Console domain events
events = cdp("Runtime.getTypedArrays", {})
print("typed arrays:", events)
