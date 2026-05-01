import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js, page_info
ensure_daemon()
new_tab('file:///P:/packages/cc-skills-meta/skills/skill-to-page/index.html')
wait_for_load()
import time; time.sleep(5)
result = js("(function(){var items=[];window.addEventListener('error',function(e){items.push('ERR:'+e.message);});return 'errors: '+items.length+' | '+items.join(' | ');})()")
print(result)
result2 = js("(function(){return 'mermaidNS: '+(typeof mermaidModule)+' | mermaid: '+(typeof mermaid);})()")
print(result2)
status = js("(function(){var s=document.getElementById('status');return s?s.textContent:'no status el';})()")
print("status element:", status)
PY