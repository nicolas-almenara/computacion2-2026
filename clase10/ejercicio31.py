import threading
import time
import random
NUM_WORKERS = 4
datos = [0] * NUM_WORKERS
resultados_fase1 = [0] * NUM_WORKERS
resultados_fase2 = [0] * NUM_WORKERS
def imprimir_estado():
    print(f"resultados fase 1: {resultados_fase1}")
    print(f"resultados fase 2: {resultados_fase2}")
barrera = threading.Barrier(NUM_WORKERS, action=imprimir_estado)
def worker(id):
    print(f"el worker id: {id} esta en fase 1 procesando")
    time.sleep(random.uniform(0.5, 1.5))
    resultados_fase1[id] = datos[id] * 2
    print(f"el worker id: {id} completo la fase 1")
    barrera.wait()
    print(f"el worker id: {id} esta en fase 2 combinando")
    time.sleep(random.uniform(0.3, 0.8))
    vecino = (id + 1) % NUM_WORKERS
    resultados_fase2[id] = resultados_fase1[id] + resultados_fase1[vecino]
    print(f"el worker id: {id} completo la fase 2")
    barrera.wait()
    print(f"el procesamiento del woeker: {id} esta completo")
datos = [i * 10 for i in range(NUM_WORKERS)]
print(f"datos: {datos}")
threads = []
for i in range(NUM_WORKERS):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()
print(f"resultados fase 2: {resultados_fase2}")
