#!/usr/bin/env python3
import http.server, socketserver, os

PORT = 9793
os.chdir('P:/packages/.github_repos/browser-harness')

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<!DOCTYPE html><html><body><span id=s>x</span><script type=module>window.addEventListener("error",e=>{document.getElementById("s").textContent="ERR:"+e.message;}); import * as m from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs"; document.getElementById("s").textContent="ok:"+typeof m.default;</script></body></html>')

socketserver.TCPServer.allow_reuse_address = True
httpd = http.server.HTTPServer(('', PORT), H)
print(f'Serving on {PORT}', flush=True)
httpd.serve_forever()
