#!/usr/bin/env python3
import os
import sys
import time
def main():
    if len(sys.argv) < 2:
        print(f"Uso: {sys.argv[0]} comando1 [comando2 ...]")
        sys.exit(1)
    comandos = sys.argv[1:]
    procesos = {}  # pid -> comando
    inicio = time.time()
    for cmd in comandos:
        pid = os.fork()

        if pid == 0:
            # 👶 Proceso hijo
            args = cmd.split()
            os.execvp(args[0], args)
        else:
            # 👨 Proceso padre
            procesos[pid] = cmd
            print(f"[{pid}] Iniciado: {cmd}")
    exitosos = 0
    fallidos = 0
    while procesos:
        pid, status = os.wait()

        cmd = procesos.pop(pid)

        codigo = os.WEXITSTATUS(status)

        print(f"[{pid}] Terminado: {cmd} (código: {codigo})")

        if codigo == 0:
            exitosos += 1
        else:
            fallidos += 1
    fin = time.time()
    print("\nResumen:")
    print(f"- Comandos ejecutados: {len(comandos)}")
    print(f"- Exitosos: {exitosos}")
    print(f"- Fallidos: {fallidos}")
    print(f"- Tiempo total: {fin - inicio:.2f}s")
if __name__ == "__main__":
    main()