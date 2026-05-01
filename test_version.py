import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js, page_info, cdp
ensure_daemon()
new_tab('http://localhost:9795/index.html')
wait_for_load()
import time; time.sleep(2)
# Try dynamic import
result = cdp("Runtime.evaluate", {
    "expression": "import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs').then(m => ({type: typeof m, keys: Object.keys(m).join(','), defaultType: typeof m.default}))",
    "awaitPromise": True
})
print("dynamic import:", result)
