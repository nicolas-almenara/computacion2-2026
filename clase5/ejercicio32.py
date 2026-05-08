import signal
import os
import time
hijos_activos = []
resultados = {}
def handler(sig, frame):
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
            hijos_activos.remove(pid)
            codigo = os.WEXITSTATUS(status) if os.WEXITSTATUS(status) else -1
            resultados[pid] = codigo
            print(f"Hijo {pid} termino con codigo {codigo}")
        except ChildProcessError:
            break
signal.signal(signal.SIGCHLD, handler)
print("creando 5 hijos")
for i in range(5):
    pid = os.fork()
    if pid == 0:
        duracion = (i+1) * 0.5
        time.sleep(duracion)
        os._exit(i)
    else:
        hijos_activos.append(pid)
        print(f"hijo creado {pid}, durara {(i+1) * 0.5}s")
print("padre trabajando mientras los hijos se ejecutan...")
for tick in range(10):
    print(f"[PADRE] Tick {tick}, hijos activos: {len(hijos_activos)}")
    time.sleep(0.5)
    if not hijos_activos:
        break

print(f"\n[PADRE] Todos terminaron. Resultados: {resultados}")