from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import urllib.parse
from pathlib import Path
import mimetypes
import logging
import json
from threading import Thread
from datetime import datetime

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
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', value='/message')
        self.end_headers()


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


def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        time = str(datetime.now())
        parse_dict = {time: {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}}
        try:
            with open('storage/data.json', 'r', encoding='utf-8') as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            existing_data = {}
        except json.JSONDecodeError:
            existing_data = {}

        existing_data.update(parse_dict)

        with open('storage/data.json', 'w', encoding='utf-8') as file:
            json.dump(existing_data, file, ensure_ascii=False, indent=4)

    except ValueError as err:
        logging.error(f"ValueError: {err}")
    except OSError as err:
        logging.error(f"OSError: {err}")
    except Exception as err:
        logging.error(f"Unexpected error: {err}")


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, ServerHandler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt as err:
        http_server.server_close()


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            save_data_from_form(msg)
    except KeyboardInterrupt as err:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s %(message)s')

    server_http = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server_http.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()