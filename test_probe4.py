import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js, page_info, cdp
ensure_daemon()
new_tab('http://localhost:9795/index.html')
wait_for_load()
import time; time.sleep(3)
# Get all module scripts
scripts = cdp("Runtime.evaluate", expression="JSON.stringify(Array.from(document.querySelectorAll('script[type=module]')).map(s=>({src:s.src,text:s.textContent.slice(0,50)})))", returnByValue=True)
print("module scripts:", scripts)
# Check if there's an error listener
errs = cdp("Runtime.evaluate", expression="window.__moduleErrors", returnByValue=True)
print("module errors:", errs)
# Try to attach to the module's context
# Check if the import was successful via CDP evaluation
cdp_result = cdp("Runtime.evaluate", expression="typeof mermaidModule", returnByValue=True)
print("mermaidModule type:", cdp_result)
PY