import socketserver
import time
import os
import threading
from multiprocessing import Value
class Contador(socketserver.StreamRequestHandler):
    def setup(self):
        super().setup()
        print('setup')

    def handle(self):
        linea = self.rfile.readline()
        if linea.strip() == b'CRASH':
            raise RuntimeError('explote')
        with self.server.visitas.get_lock():
            self.server.visitas.value += 1
            self.wfile.write(f'visita {self.server.visitas}\n'.encode())

    def finish(self):
        print('finish')
        super().finish()

class Servidor(socketserver.ThreadingTCPServer):
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visitas=Value('i', 0)

with Servidor(('localhost', 8080), Contador) as servidor:
    servidor.serve_forever()


#Respuesta pregunta 1: ThreadingMixIn define 3 metodos. El que se encarga de la concurrencia
#es process_request.
#Respuesta pregunta 2: Se diferencian en que BaseServer hace el trabajo ahi mismo y bloquea, en cambio
#ThreadingMixIn le asigna el trabajo a un hilo y sigue con la ejecucion del programa principal, es decir
#aceptando clientes.
#Respuesta pregunta 3: A los hijos los cosecha en collect_children(), no hay zombies como en la clase 14
#ya que en cada vuelta del bucle principal se llama a collect_children() que dentro de su codigo tiene 
#waitpid lo que hace que no hayan zombies.
#Respuesta pregunta 4: ThreadingTCPServer tiene 0 lineas de codigo propias. Es la combinacion entre las
#ThreadingMixIn y TCPServer.
#Respuesta pregunta 5: Los dos MRO se diferencian en que en bien primero esta como parametro la clase
#ThreadingMixIn la cual implementa el manejo de hilos, y luego TCPServer, en cambio en mal, primera esta la clase base
#TCPServer, por lo cual como ThreadingMixIn esta segunda, el manejo de los clientes ya esta implmenetado desde
#TCPServer ya que incluso en el MRO esta primera BaseServer.
#Respuesta pregunta 6: En el MRO bien se encarga ThreadingMixIn de process_request, en cambio en 
#mal se encarga BaseServer de process_request.
#Respuesta pregunta 7: El servidor que atiende en paralelo es Bien, ya que implementa threading.
#Respuesta pregunta 8: Mal no lanza ningun error, simplemente no es concurrente. Lo que lo hace 
#peligroso es que no es concurrente pero no tira nungun error es decir es silencioso.
#Respuesta pregunta 9: Cambiando a ForkingTCPServer devuelve siempre visita 1, ya que cada proceso tiene su propio
#espacio en memoria por ende no comparten la varible que cuenta las visitas, siemre la incrementan de 0 a 1.
#Respuesta pregunta 10: Cuando hay una nueva conexion, se hace fork, es decir una copia del proceso padre, lo que el
#proceso hijo haga sobre la copia, el padre no lo puede ver, y cuando el hijo termine, esa variable morira con el.
#Respuesta pregunta 11: Lo que haria falta para implementarlo seria un valor compartido por los procesos. Para esto
#se puede utilizar Multiprocessing.value.
#Respuesta pregunta 12: hay que crearlo en el init, ya que el objeto servidor se crea una unica vez, y de esta manera
#los hijos reciben. La razon es porque cuando se haga fork es Value ya debe existir para que lo hijos lo hereden.
#Respuesta pregunta 13: ...
#Respuesta pregunta 14: Con daemon_thread = False cuando se cierra el servidor, el hilo que atiende el cliente sigue vivo
#'colgado', en cambio con daemos_threads = True corta al instante sin esperar a los hilos.