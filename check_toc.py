from run import ensure_daemon, new_tab, wait_for_load, wait, cdp, screenshot

ensure_daemon()
new_tab("about:blank")
wait(500)
cdp("Page.navigate", url="file:///P:/packages/cc-skills-sdlc/skills/go/index.html")
wait(3000)

result = cdp("Runtime.evaluate", expression="""
(function() {
  var toc = document.getElementById("toc");
  var btn = document.getElementById("tocToggle");
  var stages = document.querySelectorAll(".stage-header");
  var mermaidDone = document.querySelectorAll(".mermaid svg").length;
  return {
    tocExists: !!toc,
    tocClass: toc ? toc.className : null,
    tocAriaHidden: toc ? toc.getAttribute("aria-hidden") : null,
    btnExists: !!btn,
    btnBound: btn ? btn.dataset.bound : null,
    btnAriaExpanded: btn ? btn.getAttribute("aria-expanded") : null,
    stageCount: stages.length,
    bodyClass: document.body.className,
    mermaidSvgs: mermaidDone
  };
})()
""", returnByValue=True)

print("DOM state:", result)
screenshot("dom_check.png")
print("Screenshot saved")
