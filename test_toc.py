from run import ensure_daemon, new_tab, wait_for_load, screenshot, wait, js

ensure_daemon()
new_tab("file:///P:/packages/cc-skills-sdlc/skills/go/index.html")
wait_for_load()
wait(2000)

# Check initial state
initial = js("(function() { var toc = document.getElementById('toc'); var btn = document.getElementById('tocToggle'); if(!toc||!btn) return 'elements missing'; return {tocClass: toc.className, bodyClass: document.body.className, btnBound: btn.dataset.bound, btnAria: btn.getAttribute('aria-expanded'), tocAria: toc.getAttribute('aria-hidden')}; })()")
bprint("Initial state: " + str(initial))

# Click toggle button via JS
click_result = js("(function() { var btn = document.getElementById('tocToggle'); if(!btn) return 'no btn'; btn.click(); return 'clicked'; })()")
bprint("Click result: " + click_result)
wait(1000)

# Check state after click
after = js("(function() { var toc = document.getElementById('toc'); var btn = document.getElementById('tocToggle'); if(!toc||!btn) return 'elements missing'; return {tocClass: toc.className, bodyClass: document.body.className, btnAria: btn.getAttribute('aria-expanded'), tocAria: toc.getAttribute('aria-hidden')}; })()")
bprint("After click: " + str(after))

screenshot('after_toc_click.png')
bprint("Screenshot saved")
