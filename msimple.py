#!/usr/bin/env python3
"""Minimal HTTP server for mermaid ESM testing."""
import http.server, socketserver, threading, sys

PORT = 9781

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == '/mtest':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = """<!DOCTYPE html><html><head></head><body>
<span id=status>loading</span>
<script type=module>
document.getElementById('status').textContent = 'module running';
let mm;
import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs')
  .then(m => { mm = m.default; document.getElementById('status').textContent = 'imported type:' + typeof mm; return mm.initialize({startOnLoad:false}); })
  .then(() => { document.getElementById('status').textContent += ' | initialized'; return mm.render('tid','graph TD\\n    A-->B'); })
  .then(r => { document.getElementById('status').textContent += ' | svg len:' + r.svg.length; document.title = 'PASS'; })
  .catch(e => { document.getElementById('status').textContent = 'ERR:' + e.message; document.title = 'FAIL'; });
</script></body></html>"""
            self.wfile.write(html.encode())
        else:
            super().do_GET()

socketserver.TCPServer.allow_reuse_address = True
httpd = http.server.HTTPServer(('', PORT), H)
print(f"Serving on {PORT}")
sys.stdout.flush()
httpd.serve_forever()
