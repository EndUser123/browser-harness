import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js, page_info
ensure_daemon()
new_tab('http://example.com')
wait_for_load()
import time; time.sleep(1)
result = js("(function(){var ok=false;var msg='init';try{var r=new XMLHttpRequest();r.open('GET','https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs',false);r.send();ok=(r.status===200);msg='xhr status: '+r.status+' len: '+r.responseText.length;}catch(e){msg='xhr error: '+e.message;}return ok+' | '+msg;})()")
print("CDN accessibility:", result)
