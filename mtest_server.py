import http.server, threading, socketserver, time, os

PORT = 9776
os.chdir('P:/packages/.github_repos/browser-harness')

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == '/mtest':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            source = "graph TD\n    A-->B"
            html = f"""<!DOCTYPE html><html><head></head><body>
<span id=status>loading</span>
<script type=module>
try {{
  const m = await import('https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs');
  window.__mermaid = m.default;
  document.getElementById('status').textContent = 'mermaid type: ' + typeof m.default;
  const keys = Object.keys(m.default);
  document.getElementById('status').textContent += ' | keys: ' + keys.join(',');
  document.title = 'PASS';
}} catch(e) {{
  document.getElementById('status').textContent = 'ERROR: ' + e.message;
  document.title = 'FAIL';
}}
</script></body></html>"""
            self.wfile.write(html.encode())
        else:
            super().do_GET()

socketserver.TCPServer.allow_reuse_address = True
httpd = http.server.HTTPServer(('', PORT), H)
httpd.serve_forever()
