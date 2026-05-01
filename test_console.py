import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, cdp
ensure_daemon()
new_tab('http://localhost:9795/index.html')
wait_for_load()
import time; time.sleep(2)
# Enable console logging
cdp("Log.enable")
cdp("Runtime.enable")
# Evaluate to trigger any console messages
result = cdp("Runtime.evaluate", expression="1+1", returnByValue=True)
print("eval works:", result)
# Try to get module information
mod_info = cdp("Runtime.evaluate", expression="Object.keys(window).filter(k=>k.includes('ermaid')).join(',')", returnByValue=True)
print("window mermaid keys:", mod_info)
# Check if there's a module error via the console API
events = cdp("Runtime.executeCommand", commandId=1, parameters={"bindObject": ""})
print("events:", events)
