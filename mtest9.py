#!/usr/bin/env python3
"""Minimal test server for mermaid ESM module loading."""
import http.server, socketserver, os, sys

PORT = 9789
os.chdir('P:/packages/.github_repos/browser-harness')

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == '/mtest':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = '<!DOCTYPE html><html><head></head><body>' \
                   '<span id=status>loading</span>' \
                   '<script type=module>' \
                   'document.getElementById("status").textContent = "module started"; ' \
                   'const m = await import("https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"); ' \
                   'document.getElementById("status").textContent = "imported:" + typeof m.default; ' \
                   '</script></body></html>'
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

socketserver.TCPServer.allow_reuse_address = True
httpd = http.server.HTTPServer(('', PORT), H)
print(f'Serving on {PORT}', flush=True)
httpd.serve_forever()
