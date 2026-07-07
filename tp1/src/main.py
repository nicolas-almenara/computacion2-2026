#!/usr/bin/env python3
"""
main.py — Entry point del monitor de procesos y threads.

Responsabilidades:
  1. Cargar la config inicial (intervalos por vista).
  2. Crear las estructuras de memoria compartida (Manager.dict para el
     snapshot, Value por vista para los intervalos, Event para el shutdown).
  3. Arrancar los 7 analizadores, cada uno en su propio proceso.
  4. Instalar el manejo de señales (self-pipe).
  5. Lanzar la TUI (curses) en el proceso principal.
  6. Al salir, coordinar el shutdown limpio de todos los analizadores.

La arquitectura es multiproceso: el proceso principal corre la TUI y
7 procesos analizadores corren en paralelo, cada uno con su propio ritmo,
escribiendo al snapshot compartido.
"""
import os
import sys
import json
import curses
import multiprocessing

# Permitir imports planos (procfs, base, ...) sin paquete.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import senales as sig_mod
from display import Display, VISTAS
from recolector import Recolector

from analizadores.resumen import AnalizadorResumen
from analizadores.memoria import AnalizadorMemoria
from analizadores.fds import AnalizadorFDs
from analizadores.threads import AnalizadorThreads
from analizadores.senales import AnalizadorSenales
from analizadores.scheduling import AnalizadorScheduling
from analizadores.sistema import AnalizadorSistema


# Mapa clave-de-vista -> (clase del analizador, intervalo por defecto).
ANALIZADORES = {
    "resumen":    (AnalizadorResumen,    2.0),
    "memoria":    (AnalizadorMemoria,    3.0),
    "fds":        (AnalizadorFDs,        5.0),
    "threads":    (AnalizadorThreads,    2.0),
    "senales":    (AnalizadorSenales,    10.0),
    "scheduling": (AnalizadorScheduling, 10.0),
    "sistema":    (AnalizadorSistema,    2.0),
}


def cargar_config():
    """Lee config.json si existe. Devuelve dict de intervalos por vista."""
    intervalos = {clave: default for clave, (_, default) in ANALIZADORES.items()}
    try:
        with open("config.json") as f:
            cfg = json.load(f)
        for clave, val in cfg.get("intervalos", {}).items():
            if clave in intervalos:
                intervalos[clave] = float(val)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        pass
    return intervalos


def main():
    # En Linux el default es 'fork', que nos sirve: los hijos heredan el
    # snapshot y los Values sin tener que picklearlos explícitamente.
    manager = multiprocessing.Manager()

    # Snapshot global: dict-de-dict. Cada analizador escribe bajo su clave.
    snapshot = manager.dict()

    # Estado de control compartido (verbose toggle, etc.)
    control = manager.dict()
    control["verbose"] = False

    # Un Value por vista para el intervalo (ajustable en caliente con +/-).
    config = cargar_config()
    intervalos = {
        clave: multiprocessing.Value("d", config[clave])
        for clave in ANALIZADORES
    }

    # Event para coordinar el shutdown de todos los analizadores a la vez.
    detener = multiprocessing.Event()

    # Contador global de lecturas de /proc + su Lock. Los 7 analizadores
    # (procesos distintos) incrementan el mismo Value; el Lock evita la race
    # condition del contador += 1 (clase 9). Se muestra en la vista Sistema.
    contador_lecturas = multiprocessing.Value("i", 0)
    lock_contador = multiprocessing.Lock()

    # Instalar el self-pipe de señales ANTES de arrancar la TUI.
    sig_mod.instalar()

    procesos = []

    # Arrancar el recolector PRIMERO: publica la lista maestra de PIDs que
    # los analizadores van a consumir. Refresca rápido (1s) porque es la
    # fuente de "qué procesos hay" para todos los demás.
    intervalo_recolector = multiprocessing.Value("d", 1.0)
    recolector = Recolector(snapshot, intervalo_recolector, detener,
                            contador_lecturas, lock_contador)
    recolector.start()
    procesos.append(recolector)

    # Arrancar los 7 analizadores.
    for clave, (clase, _) in ANALIZADORES.items():
        p = clase(snapshot, intervalos[clave], detener,
                  contador_lecturas, lock_contador)
        p.start()
        procesos.append(p)

    # Lanzar la TUI. curses.wrapper garantiza restaurar la terminal aunque
    # haya una excepción (deja la consola usable pase lo que pase).
    display = Display(snapshot, intervalos, detener, control, contador_lecturas)
    try:
        curses.wrapper(display.correr)
    finally:
        # Shutdown limpio: señalizar a los analizadores y esperarlos.
        detener.set()
        for p in procesos:
            p.join(timeout=3)
        # Si alguno no cerró a tiempo, terminarlo por las malas.
        for p in procesos:
            if p.is_alive():
                p.terminate()
                p.join(timeout=1)
        manager.shutdown()

    print("Monitor finalizado.")


if __name__ == "__main__":
    main()