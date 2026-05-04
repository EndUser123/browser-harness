import sys, json, os, time
sys.path.insert(0, r'P:/packages/.github_repos/browser-harness')
from helpers import *
from admin import *

INDEX_PATH = 'file:///P:/packages/cc-skills-meta/skills/doc-compiler/index.html'
SNAP_DIR = r'P:/packages/cc-skills-meta/skills/doc-compiler/_snapshots'
os.makedirs(SNAP_DIR, exist_ok=True)

print('Starting daemon check...')
restart_daemon()
ensure_daemon()
print('Daemon ready')

print('Opening tab...')
new_tab(INDEX_PATH)
print('Tab opened')

print('Waiting for load...')
wait_for_load()
print('Loaded')

time.sleep(2)
print('Taking screenshot...')
screenshot(os.path.join(SNAP_DIR, 'debug.png'))
print('Screenshot taken')

toc_found = js("document.getElementById('tocToggle') !== null")
print('toc_found:', toc_found)

result = {'toc_found': toc_found}
print('__RESULTS__:' + json.dumps(result))