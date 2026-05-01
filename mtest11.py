#!/usr/bin/env python3
"""Minimal test server for static module import."""
import http.server, socketserver, os, sys

PORT = 9791
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
                   'import lodash from "https://cdn.jsdelivr.net/npm/lodash@4.17.21/lodash.min.js"; ' \
                   'document.getElementById("status").textContent = "loaded:" + typeof lodash; ' \
                   'document.title = "PASS";' \
                   '</script></body></html>'
            self.wfile.write(html.encode())
        elif self.path == '/mtest2':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = '<!DOCTYPE html><html><head></head><body>' \
                   '<span id=status>loading</span>' \
                   '<script type=module>' \
                   'import dayjs from "https://cdn.jsdelivr.net/npm/dayjs@1.11.10/dayjs.min.js"; ' \
                   'document.getElementById("status").textContent = "loaded:" + typeof dayjs; ' \
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
