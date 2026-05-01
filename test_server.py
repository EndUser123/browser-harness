import http.server, socketserver, os, sys

PORT = 9796
os.chdir('P:/packages/.github_repos/browser-harness')

class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

socketserver.TCPServer.allow_reuse_address = True
httpd = http.server.HTTPServer(('', PORT), H)
print(f'Serving on {PORT}', flush=True)
httpd.serve_forever()
