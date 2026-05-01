import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js
ensure_daemon()
new_tab('http://localhost:9795/index.html')
wait_for_load()
import time; time.sleep(6)
result = js("(function(){return import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs').then(function(m){return 'ok: '+typeof m.default;}).catch(function(e){return 'err: '+e.message;});})()")
print(result)
