#!/usr/bin/env python3
"""Servidor eco con selectors(): un solo hilo, muchos clientes.

Compará con los cuatro servidores de la clase 14: acá no hay threads,
procesos, locks ni zombies. Un proceso, un hilo, N clientes.

Uso:
    python3 servidor_select.py [puerto]

Probalo con varios clientes a la vez:
    nc localhost 8080        (en varias terminales)
"""
import selectors
import socket
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def main():
    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', PUERTO))
    servidor.listen(128)
    servidor.setblocking(False)
    print(f'Escuchando en 0.0.0.0:{PUERTO} (un solo hilo)')

    # El socket que escucha se vigila igual que los demás: "listo para
    # leer" significa que hay una conexión esperando en accept().
    sel = selectors.DefaultSelector()
    sel.register(servidor, selectors.EVENT_READ)

    try:
        while True:
            # Bloquea acá hasta que ALGUNO esté listo. Sin busy-waiting:
            # el proceso duerme y no consume CPU mientras espera.
            eventos = sel.select()

            for key, mask in eventos:
                sock = key.fileobj
                if sock is servidor:
                    conn, direccion = servidor.accept()
                    conn.setblocking(False)
                    sel.register(conn, selectors.EVENT_READ, direccion)
                    print(f'+ cliente {direccion}  (total: {len(sel.get_map()) - 1})')
                else:
                    datos = sock.recv(4096)
                    if datos:
                        sock.sendall(datos)
                    else:
                        # recv() vacío = cerró. unregister() antes de close()
                        # es obligatorio: si no, el selector queda con un fd
                        # muerto y el comportamiento es indefinido.
                        d = key.data
                        sel.unregister(sock)
                        sock.close()
                        print(f'- cliente {d}  (total: {len(sel.get_map()) - 1})')
    except KeyboardInterrupt:
        print('\nServidor detenido')
    finally:
        sel.close()


if __name__ == '__main__':
    main()

#EJERCICIO 2:
#1)El proceso tiene un solo hilo.

#2)El tercer cliente si responde, no hay que esperar a los demas ya que select devuelve una
#lista de los sockets que tienen datos para leer o que quieren conectarse. El kernel se encarga
#de detectar esto, por lo que el proceso esta dormido esperando esto.

#3)El servidor detecta - cliente ('127.0.0.1', 38142)  (total: 2), la linea que lo detecta
#es el else luego del if datos.

#4)El servidor se cierra y lanza esta ecxepcion: ValueError: file descriptor cannot be a negative integer (-1).

#EJERCICIO 4:
#1)Desaparecen la lista `vigilados` y el diccionario `direcciones`. El selector (sel) guarda
#internamente los sockets registrados (ya no hace falta una lista propia: se usa sel.register()
#y sel.unregister() en vez de append()/remove()), y el tercer argumento de register() (data)
#guarda la direccion junto con el socket, reemplazando al diccionario.

#2)DefaultSelector eligio EpollSelector (probado con: print(type(selectors.DefaultSelector()).__name__)).

#3)Con pocos clientes no cambia nada el comportamiento (misma logica de la Parte C del benchmark:
#con pocas conexiones, la implementacion no se nota). El limite de fds SIGUE estando: SelectSelector
#usa select() por dentro, asi que el mismo fd alto (1102) que rompia a select() rompe igual a
#SelectSelector, con el mismo error: ValueError: filedescriptor out of range in select().

#4)Al sacar sel.unregister(conn) antes del close(), el servidor no crashea apenas se desconecta el
#primer cliente. El sintoma aparece despues: cuando se conecta un cliente NUEVO, el sistema operativo
#reutiliza el mismo numero de fd que tenia el socket cerrado, y al intentar sel.register() con ese fd
#el selector explota con KeyError: "<socket...> (FD 5) is already registered", porque todavia lo
#tenia registrado (apuntando al socket viejo) y nunca lo liberamos.