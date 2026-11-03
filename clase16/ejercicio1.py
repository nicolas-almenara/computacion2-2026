import socketserver
import time
import os
import threading
class Contador(socketserver.StreamRequestHandler):
    def setup(self):
        print('setup')

    def handle(self):
        linea = self.rfile.readline()
        if linea.strip() == b'CRASH':
            raise RuntimeError('explote')
        with self.server.lock:
            self.server.visitas += 1
            self.wfile.write(f'visita {self.server.visitas}\n'.encode())

    def finish(self):
        print('finish')
        super().finish()

class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visitas=0
        self.lock = threading.Lock()


with Servidor(('localhost', 8080), Contador) as servidor:
    servidor.serve_forever()

#Respuesta pregunta 1: self.request es un socket, por eso llamo a recv y a sendall.
#hice el print(type(self.request)) y me devolvio un objeto socket.socket.
#Respuesta pregunta 2: observo que en los 3 clientes que hice me dio el mismo id, esto es porque
#en TCPServer no hay concurrencia y atiende a un cliente por turno, esto le da la libertad a python
#de poder reutilizar la direccion de memoria (Lo que no significa que sea el mismo objeto).)
#Respuesta pregunta 3: El handle se ejecuta una unica vez por cada conexion, luego cierra el
#socket para escuchar otra conexion.
#Respuesta pregunta 4: Al relanzarlo rapidamente me da el error 'Adress already in use'.
#Respuesta pregunta 5: Al relanzarlo rapidamente sin haberme conectado nunca no da el mismo error,
#esto es debido a que el puerto ni si quiera se uso ya que ningun cliente se conecto.
#Respuesta pregunta 6: Luego de implemetar allow_reuse_address=True puedo confirmar que desaparece.
#Respuesta pregunta 7: El segundo tarda 3 segundos desde que ya se atndio al primer cliente.
#Respuesta pregunta 8: con ThreadingTCPServer los dos se ejecutan pasados los tres segundos del time sleep.
#Respuesta pregunta 9: Por cada cliente se hace un fork con un nuevo pid para atender al cliente.
#Respuesta pregunta 10: al enviar printf 'UNO\nDOS\n' | nc localhost 8080 el servidor recibe b'UNO\nDOS\n' y le devuelve al 
#cliente UNO salto de linea DOS.
#Respuesta pregunta 11: Cambia que recibe linea por linea separadas por los saltos de linea en lugar de recibir todo junto
#con los \n en el medio.
#Respuesta pregunta 12: No hay que mezclar self.rfile y self.request.recv ya que cuando hagas el recv, r.file ya
#se va a haber llevado los datos a su buffer inerno y se va a quedar esperando datos infinitamente sin dar ningun
#error.
#Respuesta pregunta 13: El contador siempre da 1 ya que cada conexion crea una nueva instancia de Contador,
#por lo que siempre comienza en 0 y lo incrementa a 1.
#Respuesta pregunta 14: Moviendolo a servidor si cuenta.
#Respuesta pregunta 15: con lock no se pierde ninguna suma, en cambio sin lock puede que se pierda alguno o que no se pierda
#ninguno.
#Respuesta pregunta 16: El servidor no se cae pero lanza una excepcion.
#Respuesta pregunta 17: El orden es setup, finish y luego hadle error.
#Respuesta pregunta 18: Lanza la excepcion 'Contador' object has no attribute 'wfile'.
