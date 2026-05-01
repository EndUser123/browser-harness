import sys
sys.path.insert(0, '.')
from admin import ensure_daemon
from helpers import new_tab, wait_for_load, cdp
ensure_daemon()
new_tab('http://localhost:9795/index.html')
wait_for_load()
import time; time.sleep(6)
# Intercept mermaid.render by patching window
cdp("Runtime.evaluate", expression="window.__renderCalls=[];window.__origRender=mermaid.render.bind(mermaid);mermaid.render=async function(id,src){window.__renderCalls.push({id,src:src.slice(0,50)});const r=await window.__origRender(id,src);window.__renderResult={svgLen:r.svg.length,hasSvg:!!r.svg};return r;}", returnByValue=True)
time.sleep(1)
# Force re-render by triggering
cdp("Runtime.evaluate", expression="typeof renderMermaid", returnByValue=True)
print("renderMermaid type:", cdp("Runtime.evaluate", expression="typeof renderMermaid", returnByValue=True))
print("render calls:", cdp("Runtime.evaluate", expression="window.__renderCalls", returnByValue=True))
print("render result:", cdp("Runtime.evaluate", expression="window.__renderResult", returnByValue=True))
# Try calling renderMermaid directly
cdp("Runtime.evaluate", expression="renderMermaid()", returnByValue=True, awaitPromise=True)
print("after manual call:", cdp("Runtime.evaluate", expression="window.__renderResult", returnByValue=True))
