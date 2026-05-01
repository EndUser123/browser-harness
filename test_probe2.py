import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js, page_info
ensure_daemon()
new_tab('file:///P:/packages/cc-skills-meta/skills/skill-to-page/index.html')
wait_for_load()
import time; time.sleep(5)
err = js("(function(){var e=document.getElementById('diagramError');return e?e.textContent:'no err div';})()")
print("error div:", err)
svg_count = js("(function(){var s=document.getElementById('diagramStage');return s?s.querySelectorAll('svg').length:0;})()")
print("svg count in stage:", svg_count)
mermaid_val = js("(function(){return typeof mermaid;})()")
print("mermaid type:", mermaid_val)
