#!/usr/bin/env python3
"""Compara select, poll y epoll con cantidades crecientes de conexiones.

Mide el costo de UNA llamada al multiplexor con N descriptores vigilados,
de los cuales solo unos pocos tienen datos. Es el escenario real de un
servidor: miles de conexiones abiertas, un puñado activas en cada momento.

Los números explican por qué existe epoll.

Uso:
    python3 comparar.py                # 100, 500, 1000, 2000, 5000
    python3 comparar.py 200 4000       # cantidades a medida
"""
import select
import socket
import sys
import time

REPETICIONES = 200          # llamadas al multiplexor por medición
ACTIVOS = 3              # cuántos sockets tienen datos listos


def crear_pares(n):
    """Crea n pares de sockets conectados. Devuelve (lectores, escritores)."""
    lectores, escritores = [], []
    for _ in range(n):
        a, b = socket.socketpair()
        lectores.append(a)
        escritores.append(b)
    return lectores, escritores


def medir_select(lectores):
    try:
        t0 = time.perf_counter()
        for _ in range(REPETICIONES):
            select.select(lectores, [], [], 0)
        return (time.perf_counter() - t0) / REPETICIONES * 1e6
    except (ValueError, OSError) as e:
        # FD_SETSIZE: el límite es el NÚMERO del fd, no la cantidad
        return f'falla ({type(e).__name__})'


def medir_poll(lectores):
    p = select.poll()
    for s in lectores:
        p.register(s, select.POLLIN)
    t0 = time.perf_counter()
    for _ in range(REPETICIONES):
        p.poll(0)
    return (time.perf_counter() - t0) / REPETICIONES * 1e6


def medir_epoll(lectores):
    if not hasattr(select, 'epoll'):
        return 'no disponible'
    ep = select.epoll()
    for s in lectores:
        ep.register(s.fileno(), select.EPOLLIN)
    t0 = time.perf_counter()
    for _ in range(REPETICIONES):
        ep.poll(0)
    resultado = (time.perf_counter() - t0) / REPETICIONES * 1e6
    ep.close()
    return resultado


def fmt(v):
    return f'{v:>9.1f}' if isinstance(v, float) else f'{v:>9}'


def main():
    cantidades = [int(a) for a in sys.argv[1:]] or [100, 500, 1000, 2000, 5000]

    print(f'Costo de una llamada al multiplexor, en microsegundos.')
    print(f'{ACTIVOS} sockets con datos listos, el resto ociosos. '
          f'Promedio de {REPETICIONES} llamadas.\n')
    print(f"{'conexiones':>11} {'select':>10} {'poll':>10} {'epoll':>10}")
    print('-' * 45)

    for n in cantidades:
        lectores, escritores = crear_pares(n)
        try:
            # Solo unos pocos tienen datos: es el caso real de un servidor
            for w in escritores[:ACTIVOS]:
                w.send(b'x')

            fila = (medir_select(lectores), medir_poll(lectores),
                    medir_epoll(lectores))
            print(f'{n:>11} {fmt(fila[0])} {fmt(fila[1])} {fmt(fila[2])}')
        finally:
            for s in lectores + escritores:
                s.close()

    print('\nQué mirar:')
    print('  - select y poll crecen con el TOTAL de conexiones: son O(n).')
    print('  - epoll se mantiene plano: solo devuelve los listos, O(listos).')
    print('  - select falla cuando algún fd supera 1023 (FD_SETSIZE), aunque')
    print('    la cantidad vigilada sea chica.')
    print('\nEse salto de O(n) a O(listos) es lo que resolvió el problema C10K.')


if __name__ == '__main__':
    main()

#2)El factor de poll entre 100 y 5000 conexiones es de 401, esto significa que es 401 veces
#mas lento con 5000 conexiones que con 100.

#3)Epoll se mantiene casi constante con cualquier cantidad de conexiones, sin importar cuantas
#conexiones vigiles, ya que el kernel ya tiene el conjunto registrado y solo te devuelve los que
#tienen actividad.(complejidad algoritmica de 0(listos)). De lo contrario con Poll el tiempo aumenta
#proporcionalmente con la cantidad de conexiones,porque el kernel recorre la lista completa cada vez
#tegnan actividad o no.

#4)select falla a partir de las 1000 conexiones. Lo que coincide perfectamente con el ejercicio
#2.3 ya que ya tendria acumuladas 1600 descriptores de archivos.

#5)Es realista ya que en un servidor web la mayoria de las conexiones estan abiertas pero inactivas.
#clientes con keep alive esperando la proxima request, conexiones lentas, usuarios que no interactuan
#en ese instante.

#6)Poll es 0(n) ya que la cantidad de trabajo es proporcional a la cantidad de sockets ya que
#el kernel revisa toda la lista de sockets, tengan o no actividad. Epoll es 0(listos) ya que 
#el tiempo se mantiene constante independientemente de la cantidad de sockets. El kernel ya tiene
#el conjunto registrado y te devuelve los que tienen actividad.

#7)Con 2500 activos la ventaja de Epoll se achica, esto se debe a que Epoll es 0(listos) es
#decir que si crece la cantidad dea activos, tambien crece la cantidad de trabajo que debe
#hacer.

#8)Con 10 conexiones epoll no vale la pena, con 50 y 100 si ya que el tiempo es mucho mas grande
#para poll y select.

#9)No tiene sentido complicarse con multiplexing cuando la cantidad de conexiones es chica,
#para pocas conexiones el costo de select, poll y epoll son parecidas. Para estos casos se
#justifica mas el threading, el multiplexing recien se justifica con miles de conexiones.

#10)Apache con un thread por cliente paga memoria y context switching por cada conexion
#activa o no, en cambio nginx con un event loop sobre epoll, paga solo por las conexiones
#con actividad real. Por eso con muchas conexiones nginx utiliza menos recursos que un modelo
#thread per connection como el de apache.
