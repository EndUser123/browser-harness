#!/usr/bin/env python3
"""Minimal test server for mermaid ESM module loading."""
import http.server, socketserver, os, sys

PORT = 9790
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
                   'import lodash from "https://cdn.jsdelivr.net/npm/lodash@4.17.21/dist/lodash.min.js"; ' \
                   'document.getElementById("status").textContent = "loaded:" + typeof lodash + " keys:" + Object.keys(lodash).slice(0,5).join(","); ' \
                   'document.title = "PASS";' \
                   '</script></body></html>'
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()

socketserver.TCPServer.allow_reuse_address = True
httpd = http.server.HTTPServer(('', PORT), H)
print(f'Serving on {PORT}', flush=True)
httpd.serve_forever()
