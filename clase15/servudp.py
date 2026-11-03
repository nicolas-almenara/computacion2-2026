import socketserver
import threading

class MiHandler(socketserver.BaseRequestHandler):
    def handle(self):
        pass

class threadingserver(socketserver.ThreadingTCPServer):
    pass

if __name__ == "__main__":
    Host, Port = 'localhost', 0
    server = ThreadingTCPServer((Host, Port), MiHandler)
    with server:
        ip, port = server.server_address
        server.thread = threading.Thread(target=server.serve_forever)

