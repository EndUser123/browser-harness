import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, js, page_info
ensure_daemon()
new_tab('file:///P:/packages/cc-skills-meta/skills/skill-to-page/index.html')
wait_for_load()
import time; time.sleep(3)
result = js("(function(){var el=document.createElement('div');el.id='testProbe';el.textContent='loaded';document.body.appendChild(el);return el.id;})()")
print("DOM probe:", result)
result2 = js("(function(){var pre=document.getElementById('mermaidSource');if(!pre)return'no pre';return'pre found: '+pre.textContent.slice(0,80);})()")
print(result2)
result3 = js("(function(){var stage=document.getElementById('diagramStage');if(!stage)return'no stage';var svg=stage.querySelector('svg');return'svg: '+(svg?'found':'none');})()")
print("stage svg:", result3)
