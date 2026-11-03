#!/usr/bin/env python3
"""Servidor eco con selectors: portable y con escritura no bloqueante.

Esta es la forma correcta de hacerlo en Python: selectors elige epoll en
Linux, kqueue en BSD/macOS, y select donde no haya nada mejor.

El bucle del final es un event loop: despacha a un callback sin saber qué
hace cada socket. Es, en esencia, lo que hace asyncio por dentro.

Uso:
    python3 servidor_selectors.py [puerto]
"""
import selectors
import socket
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

sel = selectors.DefaultSelector()
pendiente = {}          # socket -> bytes que faltan enviar


def aceptar(servidor):
    """El socket que escucha está listo: hay una conexión esperando."""
    conn, direccion = servidor.accept()
    conn.setblocking(False)
    # El tercer argumento es dato libre: guardamos quién atiende este socket.
    sel.register(conn, selectors.EVENT_READ, atender)
    print(f'+ cliente {direccion}')


def cerrar(conn):
    """Siempre unregister ANTES de close: un fd cerrado y aún registrado
    deja al selector en estado indefinido."""
    sel.unregister(conn)
    pendiente.pop(conn, None)
    conn.close()


def atender(conn):
    """Hay datos para leer (o el cliente cerró)."""
    try:
        datos = conn.recv(4096)
    except ConnectionResetError:
        cerrar(conn)
        print('- cliente (reset)')
        return

    if not datos:
        cerrar(conn)
        print('- cliente (cerró)')
        return

    # EJERCICIO 7: trabajo pesado DENTRO del handler. Como hay un solo hilo
    # atendiendo a todos los clientes, esto bloquea el event loop entero
    # mientras dura, sin importar que el envío después sea no bloqueante.
    import hashlib
    import time
    t0 = time.perf_counter()
    h = datos
    for _ in range(3_000_000):        # ~2 segundos de CPU
        h = hashlib.sha256(h).digest()
    print(f'  (proceso pesado: {time.perf_counter() - t0:.2f}s)')
    respuesta = h.hex().encode()

    pendiente[conn] = pendiente.get(conn, b'') + respuesta
    # Ahora me interesa saber cuándo puedo escribir sin bloquear.
    sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, atender_rw)


def atender_rw(conn, escribible=False):
    """Handler que sirve para lectura y escritura."""
    if escribible:
        escribir(conn)
    else:
        atender(conn)


def escribir(conn):
    """Se puede escribir sin bloquear: mandar lo que entre."""
    buf = pendiente.get(conn, b'')
    if buf:
        try:
            # send(), NO sendall(): sendall insiste hasta terminar y eso
            # bloquearía a los demás clientes. Mandamos lo que entre ahora
            # y volvemos cuando el selector avise que se puede seguir.
            n = conn.send(buf)
        except (BrokenPipeError, ConnectionResetError):
            cerrar(conn)
            return
        pendiente[conn] = buf[n:]

    if not pendiente.get(conn):
        # Ya no queda nada pendiente: dejar de vigilar escritura.
        # Si lo dejáramos registrado, el bucle giraría sin parar, porque
        # un socket casi siempre está listo para escribir.
        sel.modify(conn, selectors.EVENT_READ, atender)


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', PUERTO))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ, aceptar)

    print(f'Escuchando en 0.0.0.0:{PUERTO}')
    print(f'Implementación elegida: {type(sel).__name__}')

    try:
        while True:
            # El event loop: despacha al handler registrado con cada socket.
            for clave, mascara in sel.select():
                callback = clave.data
                if callback is atender_rw:
                    callback(clave.fileobj, bool(mascara & selectors.EVENT_WRITE))
                else:
                    callback(clave.fileobj)
    except KeyboardInterrupt:
        print('\nServidor detenido')
    finally:
        sel.close()


if __name__ == '__main__':
    main()

#1)Utiliza send y no sendall ya que hay un unico hilo atendiendo, lo que significa que
#un cliente lento puede hacer esperar a todos lo demas.

#2)Si se registra EVENT_WRITE permanente, el CPU se dispara (probado: subio a ~70% con un solo
#cliente conectado sin mandar nada). Un socket casi siempre tiene lugar libre en su buffer de
#envio, entonces select() lo reporta "listo para escribir" en cada vuelta del loop aunque no haya
#nada pendiente, y el bucle gira sin parar. Por eso hay que registrar EVENT_WRITE solo mientras
#pendiente[conn] tenga datos, y sacarlo apenas se vacia.

#3)Con sendall(), como hay un solo hilo, ese sendall() bloqueado en el cliente lento congela TODO
#el event loop: los otros 999 clientes quedan sin atender hasta que el lento libere buffer. Con el
#esquema de pendiente + EVENT_WRITE, send() nunca bloquea: manda lo que entra y lo que no entro
#queda guardado en pendiente[conn], asi que los demas 999 siguen siendo atendidos normalmente.

#4)La memoria crece en el diccionario pendiente: como el cliente lento nunca lee, send() cada vez
#manda menos (o nada) y pendiente[conn] sigue acumulando datos sin limite. Para protegerse habria
#que poner un tamaño maximo a pendiente[conn] y, si se supera, cortar la conexion (cerrar ese
#cliente) en vez de seguir acumulando indefinidamente.

#EJERCICIO 7:
#1)No, mientras procesa al primer cliente el segundo NO responde. Probado con dos clientes reales:
#A manda datos, B manda 0.3s despues. A recibe respuesta a los 1.92s. B, que ya habia mandado sus
#datos, tiene que esperar a que el handler de A termine ANTES de que el event loop siquiera lea lo
#que B mando: B recibe su respuesta recien a los 3.56s (practicamente 1.92s + 1.92s, uno atras del
#otro). El unico hilo esta 100% ocupado en el for de A, sin poder atender ningun otro socket.

#2)Arme un servidor equivalente con un thread por cliente (mismo hashlib.sha256 en loop) y compare.
#El resultado NO fue "B responde enseguida": los DOS clientes tardaron casi lo mismo (~3.86s y
#~3.88s), en vez de que A tarde 2s y B otros 2s en paralelo. La razon es el GIL de CPython: como el
#hash se calcula sobre un bloque muy chico (32 bytes), Python no libera el GIL entre llamadas a
#hashlib, entonces aunque A y B corran en threads distintos, el trabajo CPU-bound se sigue
#serializando igual -solo que entrelazado (el scheduler les va dando turnos cortos a cada uno),
#no en un bloque estricto como en el event loop. Con threads, el trabajo total se reparte pero
#ninguno de los dos "vuela" independiente del otro.

#3)La regla: en un modelo de un solo hilo (event loop), CUALQUIER trabajo que tarde -CPU-bound o
#una llamada bloqueante escondida- congela a TODOS los clientes por igual, porque no hay forma de
#que el sistema operativo reparta el tiempo entre ellos: es un solo hilo ejecutando una sola cosa
#a la vez. Con threads el sistema operativo SI puede repartir tiempo entre conexiones, pero para
#codigo Python puro esa mejora esta limitada por el GIL cuando el trabajo es CPU-bound: los threads
#ayudan sobre todo cuando el trabajo es I/O-bound (esperar red, disco, DB), no cuando es CPU pura.

#4)Sin abandonar el event loop, el trabajo pesado hay que sacarlo del hilo principal y mandarlo a
#un pool de threads o, mejor para CPU-bound (por el GIL), a un pool de PROCESOS aparte -cada
#proceso tiene su propio interprete y su propio GIL, asi que ahi si hay paralelismo real-. El loop
#le pasa el trabajo al pool, sigue atendiendo a los demas clientes mientras tanto, y cuando el pool
#termina, el resultado vuelve al loop para mandarselo al cliente. Es exactamente el mecanismo de
#run_in_executor() de asyncio, y reaparece en el TP2 con FastAPI: los endpoints CPU-bound no deben
#bloquear el event loop de uvicorn, hay que correrlos en un executor (ThreadPoolExecutor o
#ProcessPoolExecutor) en vez de hacerlos directamente en la funcion async.