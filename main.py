from http.client import HTTP_PORT
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import socket
import urllib.parse
from pathlib import Path
import mimetypes
import logging
from threading import Thread

BASE_DIR = Path()
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
BUFFER_SIZE = 1024
SOCKET_PORT = 5000
SOCKET_HOST = '127.0.0.1'


class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_html(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        pass


    def send_html(self, filename, status_code = 200):
        self.send_response(status_code)
        self.send_header('Content-Type', value='text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


    def send_static(self, filename, status_code = 200):
        self.send_response(status_code)
        mimetype, _ = mimetypes.guess_type(filename)
        if mimetype:
            self.send_header('Content-Type', value=mimetype)
        else:
            self.send_header('Content-Type', value='text/plain')

        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, ServerHandler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt as err:
        http_server.server_close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    run_http_server(HTTP_HOST, HTTP_PORT)