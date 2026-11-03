import socketserver

class MiHandler(socketserver.BaseRequestHandler):
    def handle(self):
        datos = self.request.recv(4096) #reques es un socket. Por eso se pude usar recv, sendall, etc.
        self.request.sendall(datos.upper())
        print(f"Datos recibidos del cliente {datos}")

if __name__ == "__main__":
    with socketserver.TCPServer(("localhost", 9999), MiHandler) as server:
        server.serve_forever() #esto hace un loop de recibir conexiones hasta que lo mate con ctrl-c o
                               #o llame a server.shutdown() desde otro hilo.                                 