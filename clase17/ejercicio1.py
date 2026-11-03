#!/usr/bin/env python3
"""Servidor con polling activo. Funciona, pero mal."""
import socket

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind(('localhost', 8080)); srv.listen(5)
srv.setblocking(False)

conexiones = []
while True:
    try:
        conn, _ = srv.accept()
        conn.setblocking(False)
        conexiones.append(conn)
    except BlockingIOError:
        pass
    for c in list(conexiones):
        try:
            datos = c.recv(4096)
            if datos: c.sendall(datos)
            else: conexiones.remove(c); c.close()
        except BlockingIOError:
            pass

#1)El servidor si funciona con nc localhost 8080.

#2)Con htop -p pid, me muestra que el servidor utiliza el 100% del cpu.

#3)Consume el 100% ya que esta constantemente tratando de recibiir datos del cliente
#y cuando se lanza la excepcion BlockingIOError, no hace nada, simplemente vuelve a intentarlo
#infinitamente.

#4)En servidor_select.py utiliza el 0% del procesador, esto se debe a que se utiliza select,
#al cual se le pasa una lista de sockets a revisar y hasta que no haya algo para leer en alguno,
#que bien puede ser una nueva conexion o contenido para leer, no se activa. Aqui el proceso no esta
#constantemente revisando sino que el kernel avisa.

#5)En un servidor de la clase 13 (secuencial), cuando el primer cliente no mandaba nada, el
#servidor se queda esperando hasta que ese cliente termine, por lo tanto deja en espera a todas
#las demas conexiones, en cambio con select, el kernel activa el proceso cuando algun socket tiene
#algo para leer, ya sean nuevas conexiones o datos.