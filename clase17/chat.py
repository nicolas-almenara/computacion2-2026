#!/usr/bin/env python3
"""Chat multiusuario con selectors: lo que un servidor eco no muestra.

Acá aparece algo que el eco no tiene: para retransmitir un mensaje hay que
escribir en sockets DISTINTOS del que lo recibió. Con threads eso exigiría
un lock sobre la lista de clientes; en un event loop de un solo hilo, no.

Uso:
    python3 chat.py [puerto]

Y desde varias terminales:
    nc localhost 8080
"""
import selectors
import socket
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

sel = selectors.DefaultSelector()
clientes = {}           # socket -> apodo
salida = {}             # socket -> bytes pendientes de enviar
entrada = {}            # socket -> bytes recibidos sin procesar (framing)


def difundir(mensaje: bytes, excepto=None):
    """Encola un mensaje para todos los clientes menos uno.

    No escribe directo: encola. Escribir acá podría bloquear si el buffer
    de algún cliente lento está lleno, y eso congelaría a todos los demás.
    """
    for conn in clientes:
        if conn is excepto:
            continue
        salida[conn] = salida.get(conn, b'') + mensaje
        sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, manejar)


def aceptar(servidor, _mascara):
    conn, direccion = servidor.accept()
    conn.setblocking(False)
    apodo = f'{direccion[0]}:{direccion[1]}'
    clientes[conn] = apodo
    sel.register(conn, selectors.EVENT_READ, manejar)
    print(f'+ {apodo}  ({len(clientes)} conectados)')
    salida[conn] = b'Bienvenido al chat. Escribi y presiona Enter.\n'
    sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, manejar)
    difundir(f'* se conecto {apodo}\n'.encode(), excepto=conn)


def desconectar(conn):
    apodo = clientes.pop(conn, '?')
    salida.pop(conn, None)
    entrada.pop(conn, None)
    sel.unregister(conn)            # SIEMPRE antes de close()
    conn.close()
    print(f'- {apodo}  ({len(clientes)} conectados)')
    difundir(f'* se fue {apodo}\n'.encode())


def encolar(conn, texto: str):
    """Agrega una linea a la salida de un cliente y activa EVENT_WRITE."""
    salida[conn] = salida.get(conn, b'') + texto.encode()
    sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, manejar)


def procesar_linea(conn, texto: str):
    apodo = clientes.get(conn, '?')

    if texto.startswith('/nick '):
        nuevo = texto[len('/nick '):].strip()
        if nuevo:
            viejo = clientes.get(conn, '?')
            clientes[conn] = nuevo
            difundir(f'* {viejo} ahora se llama {nuevo}\n'.encode())
        return

    if texto == '/lista':
        nombres = ', '.join(clientes.values())
        encolar(conn, f'* conectados: {nombres}\n')
        return

    if texto:
        print(f'  <{apodo}> {texto}')
        difundir(f'<{apodo}> {texto}\n'.encode(), excepto=conn)


def manejar(conn, mascara):
    """Un solo handler para lectura y escritura."""
    if mascara & selectors.EVENT_READ:
        try:
            datos = conn.recv(4096)
        except ConnectionResetError:
            desconectar(conn)
            return
        if not datos:
            desconectar(conn)
            return
        # Framing: recv() puede traer una linea partida, varias juntas, o
        # ninguna completa todavia. Acumulamos en un buffer por cliente y
        # solo procesamos lo que ya tiene un '\n' completo.
        entrada[conn] = entrada.get(conn, b'') + datos
        while b'\n' in entrada[conn]:
            linea, entrada[conn] = entrada[conn].split(b'\n', 1)
            texto = linea.decode('utf-8', errors='replace').rstrip('\r')
            procesar_linea(conn, texto)

    if mascara & selectors.EVENT_WRITE:
        buf = salida.get(conn, b'')
        if buf:
            try:
                # send() y no sendall(): mandamos lo que entre y volvemos
                # cuando el selector avise. sendall() bloquearía a todos.
                n = conn.send(buf)
            except (BrokenPipeError, ConnectionResetError):
                desconectar(conn)
                return
            salida[conn] = buf[n:]
        if not salida.get(conn) and conn in clientes:
            # Nada pendiente: dejar de vigilar escritura, o el bucle giraría.
            sel.modify(conn, selectors.EVENT_READ, manejar)


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', PUERTO))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ, aceptar)

    print(f'Chat escuchando en 0.0.0.0:{PUERTO} ({type(sel).__name__})')
    print('Conectate con: nc localhost', PUERTO)

    try:
        while True:
            for clave, mascara in sel.select():
                clave.data(clave.fileobj, mascara)
    except KeyboardInterrupt:
        print('\nChat detenido')
    finally:
        sel.close()


if __name__ == '__main__':
    main()

#EJERCICIO 6:
#1)No necesita lock porque hay un solo hilo: un handler (manejar, aceptar, etc.) corre completo,
#de principio a fin, antes de que el event loop atienda el siguiente evento. Nunca hay dos
#handlers ejecutandose "al mismo tiempo" tocando clientes o salida, que es justamente lo que un
#lock evita en un modelo con threads (que dos hilos modifiquen la misma lista a la vez).

#2)Encolar en vez de escribir directo evita que un send()/sendall() bloqueante en UN cliente lento
#(con el buffer lleno) congele la difusion para TODOS los demas. Al encolar en salida[conn] y
#activar EVENT_WRITE, cada cliente recibe su copia cuando el selector avisa que puede escribir,
#sin frenar el loop ni a los otros clientes mientras tanto.

#5)No, no es cierto: TCP es un flujo de bytes sin limites de mensaje, recv() no garantiza traer
#una linea completa (ni una sola). Se rompe, por ejemplo, si un cliente pega/manda varias lineas
#juntas de una (recv() trae mas de una linea en un solo datos), o si el mensaje llega partido en
#varios recv() (ej: escribiendo caracter por caracter, o una linea muy larga que no entra en un
#solo paquete). Es el mismo problema de framing de la clase 13: recv() devuelve bytes crudos, la
#aplicacion tiene que armar los "mensajes" (lineas) ella misma, no viene resuelto por el socket.

#6)Arreglado con un buffer por cliente (entrada[conn]): se van acumulando los bytes que llegan y
#solo se procesa como linea completa lo que ya tiene un '\n', dejando el resto guardado para la
#proxima vuelta. Asi una linea partida en varios recv() se arma bien, y varias lineas juntas en un
#solo recv() se procesan una por una.