import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js, page_info
ensure_daemon()
new_tab('http://localhost:9795/index.html')
wait_for_load()
import time; time.sleep(6)
err = js("(function(){var e=document.getElementById('diagramError');return e?e.textContent:'no err';})()")
print("error:", err)
svg_count = js("(function(){var s=document.getElementById('diagramStage');return s?s.querySelectorAll('svg').length:0;})()")
print("svg count:", svg_count)
m = js("(function(){return typeof mermaid;})()")
print("mermaid type:", m)
mm = js("(function(){return typeof mermaidModule;})()")
print("mermaidModule type:", mm)
