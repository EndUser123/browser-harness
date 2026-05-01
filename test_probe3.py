import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js, page_info
ensure_daemon()
new_tab('file:///P:/packages/cc-skills-meta/skills/skill-to-page/index.html')
wait_for_load()
import time; time.sleep(8)
mm = js("(function(){return typeof mermaidModule;})()")
print("mermaidModule type:", mm)
m = js("(function(){return typeof mermaid;})()")
print("mermaid type:", m)
result = js("(function(){if(typeof mermaid!=='undefined'){return 'mermaid is defined: '+typeof mermaid;}return 'mermaid undefined at 8s';})()")
print(result)
err = js("(function(){var e=document.getElementById('diagramError');return e?e.textContent:'no err';})()")
print("error:", err)
