#!/usr/bin/env python3
"""Servidor de comandos con estado compartido entre handlers.

Muestra el problema que aparece apenas el servidor deja de ser un eco:
como cada conexión crea un handler NUEVO, el estado común vive en el
servidor, y con ThreadingTCPServer eso significa acceso concurrente.
De ahí el Lock: es la clase 11 otra vez, escondida detrás del mixin.

Comandos: TIME, ECHO <texto>, QUIEN, CONTADOR, AYUDA, QUIT

Uso:
    python3 comandos.py [puerto]
    nc localhost 8080
"""
import socketserver
import sys
import threading
import time


class Handler(socketserver.StreamRequestHandler):
    timeout = 30

    def setup(self):
        """Se llama ANTES de handle(). Acá se abren rfile/wfile."""
        super().setup()               # imprescindible: crea rfile/wfile
        with self.server.lock:
            self.server.conexiones += 1
            self.server.activos.add(self.client_address)
            self.server.clientes[self.client_address] = self.wfile

    def finish(self):
        """Se llama DESPUÉS de handle(), incluso si hubo excepción."""
        with self.server.lock:
            self.server.activos.discard(self.client_address)
            self.server.clientes.pop(self.client_address, None)
        super().finish()

    def responder(self, texto):
        self.wfile.write((texto + '\n').encode())

    def handle(self):
        self.responder('Servidor de comandos. Escribí AYUDA.')
        try:
            for linea in self.rfile:                    # framing por líneas
                partes = linea.decode('utf-8', 'replace').strip().split(maxsplit=1)
                if not partes:
                    continue
                cmd, resto = partes[0].upper(), (partes[1] if len(partes) > 1 else '')

                if cmd == 'TIME':
                    self.responder(time.strftime('%Y-%m-%d %H:%M:%S'))
                elif cmd == 'ECHO':
                    self.responder(resto)
                elif cmd == 'QUIEN':
                    with self.server.lock:              # lectura también protegida
                        activos = sorted(f'{h}:{p}' for h, p in self.server.activos)
                    self.responder(f'{len(activos)} conectados: ' + ', '.join(activos))
                elif cmd == 'CONTADOR':
                    with self.server.lock:
                        n = self.server.conexiones
                    self.responder(f'Conexiones totales desde el arranque: {n}')
                elif cmd == 'AYUDA':
                    self.responder('TIME | ECHO <texto> | QUIEN | CONTADOR | QUIT')
                elif cmd == 'QUIT':
                    self.responder('Chau')
                    return                              # cierra la conexión
                elif cmd == 'NICK':
                    with self.server.lock:
                        self.server.nicks[self.client_address] = resto
                    self.responder(f'Ahora sos {resto}')
                elif cmd == 'BROADCAST':
                    with self.server.lock:
                        destinatarios = list(self.server.clientes.items())
                    for direccion, wfile in destinatarios:
                        try:
                            wfile.write(f'[{self.client_address}] {resto}\n'.encode())
                        except OSError:
                            pass
                else:
                    self.responder(f'Comando desconocido: {cmd}')
        except TimeoutError:
            self.responder('Desconectado por inactividad')

    def handle_error(self, *args):
        """Si handle() explota, el servidor NO se cae."""
        print(f'Error atendiendo a {self.client_address}')


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # El estado compartido vive acá, no en el handler: cada conexión
        # crea un handler nuevo y su estado moriría con ella.
        self.conexiones = 0
        self.activos = set()
        # Con ThreadingMixIn los handlers corren en threads distintos sobre
        # este mismo objeto. Sin lock, hay race condition (clase 11).
        self.lock = threading.Lock()
        self.nicks = {}
        self.clientes = {}


if __name__ == '__main__':
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    with Servidor(('0.0.0.0', puerto), Handler) as srv:
        print(f'Escuchando en 0.0.0.0:{puerto}')
        print('Probá: nc localhost', puerto)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')

#Respuesta pregunta 1: Ese dato vive en __init__, ya que de esta manera esto se crea apenas se instancia
#la clase, lo cual es necesario porque es utilizado en handle.
#Respuesta pregunta 3: Si un cliente se desconecta justo cuando se le esta escribiendo, wfile.write lanza una
#excepcion (OSError, tipicamente BrokenPipeError). Por eso el write va en un try/except OSError: pass adentro
#del for, para que ese cliente caido no corte el broadcast para el resto.
#Respuesta pregunta 5: Con ForkingTCPServer el BROADCAST no funcionaria, porque cada conexion corre en un
#proceso con memoria separada: self.server.clientes no seria visible entre procesos. Y no alcanza con
#cambiar el diccionario por un arreglo compartido (multiprocessing.Array/Value), porque esos solo comparten
#tipos primitivos, no sockets/wfiles (son file descriptors del sistema operativo). Haria falta repensar la
#arquitectura, no solo el contenedor.

#Ejercicio 5: El limite
#Respuesta pregunta 1 y 2: Con ThreadingTCPServer, cada conexion activa dispara un thread nuevo. Con 200
#conexiones abiertas (sin cerrarlas), ls /proc/<pid>/task | wc -l deberia dar un numero cercano a 200
#(mas algunos threads internos del runtime).
#Respuesta pregunta 3: El RSS (ps -o rss=) sube notablemente respecto del servidor recien arrancado, porque
#cada thread reserva su propia pila de memoria ademas del handler que atiende.
#Respuesta pregunta 4: Al subir a 1000 conexiones el costo escala linealmente: mas memoria, mas overhead del
#sistema operativo cambiando de contexto entre threads, y se vuelve mas lento aceptar conexiones nuevas.
#Respuesta pregunta 5: No, socketserver no resuelve el problema C10K. Un thread por cliente tiene un costo de
#memoria y de scheduling que crece linealmente con la cantidad de conexiones, asi que no escala a los miles
#de clientes simultaneos que plantea el C10K. Por eso la clase 17 introduce I/O multiplexing (select/epoll),
#que atiende muchas conexiones con un solo hilo.