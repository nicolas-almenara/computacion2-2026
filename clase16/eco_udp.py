#!/usr/bin/env python3
"""Servidor eco UDP con socketserver, y la asimetría de self.request.

En TCP, self.request ES el socket. En UDP es una TUPLA (datos, socket).
Esa diferencia es la fuente número uno de confusión con este módulo, y
DatagramRequestHandler existe para esconderla.

Uso:
    python3 eco_udp.py [puerto]           # con BaseRequestHandler
    python3 eco_udp.py --files [puerto]   # con DatagramRequestHandler
"""
import socketserver
import sys


class EchoUDPCrudo(socketserver.BaseRequestHandler):
    """Con BaseRequestHandler hay que desempaquetar la tupla a mano."""

    def handle(self):
        datos, sock = self.request          # <- tupla, NO un socket
        print(type(self.request))
        print(f'{self.client_address}: {datos!r}')
        # En UDP no hay conexión: hay que decir explícitamente a quién
        # responder, porque el socket no "recuerda" al cliente.
        sock.sendto(datos.upper(), self.client_address)


class EchoUDPFiles(socketserver.DatagramRequestHandler):
    """DatagramRequestHandler ofrece rfile/wfile también para UDP."""

    def handle(self):
        datos = self.rfile.read()
        print(f'{self.client_address}: {datos!r}')
        self.wfile.write(datos.upper())     # se manda al cerrar el handler


if __name__ == '__main__':
    usar_files = '--files' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    puerto = int(args[0]) if args else 8080

    Handler = EchoUDPFiles if usar_files else EchoUDPCrudo

    class Servidor(socketserver.UDPServer):
        allow_reuse_address = True

    with Servidor(('0.0.0.0', puerto), Handler) as srv:
        print(f'UDP en 0.0.0.0:{puerto} — handler: {Handler.__name__}')
        # UDPServer hereda de TCPServer, no de BaseServer. Es reutilización
        # de código, no una relación conceptual.
        print(f'UDPServer.__bases__ = {socketserver.UDPServer.__bases__}')
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')

#Ejercicio 3
#Respuesta pregunta 1: self.request es de tipo tuple, que incluye datos y socket.
#Respuesta pregunta 2: Hay que pasar self.client_address al sendto ya que es un servidor UDP
#, los cuales no estan orientados a conexion, entonces se debe especificar la direccion del cliente.
#Al contrario que en TCP, donde se hace un handshake de 3 vias, por lo que cuando hago un sendall ya 
#sabe a donde va dirigido ese datagrama.
#Respuesta pregunta 3: En BaseRequestHandler su utiliza self.request y hay que desempaquetar la tupla a mano, en cambio en DatagramRequestHandler
#se utiliza rfile y wfile. Con wfile no es necesario especificar la direccion ya que el handler la guarda internamente.
#Respuesta pregunta 4: Si existe ThreadingUDPServer, es util ya que nos permite solucionar el problema de que se
#atiende un cliente por vez, asignandole un hilo a cada datagrama. Sin esto, si el handle esta ocupado, se podria llenar el buffer y perder informacion.
