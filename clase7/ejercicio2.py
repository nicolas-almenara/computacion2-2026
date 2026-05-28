import multiprocessing
import random
import os
import time
def esperar(i, tiempo_total):
    tiempo = random.uniform(0.5, 2)
    time.sleep(tiempo)
    print(F"proceso {i} espero {tiempo}")
    with tiempo_total.get_lock():
        tiempo_total.value+=tiempo
procesos = []
if __name__ == "__main__":
    v = multiprocessing.Value("d", 0)
    for i in range(1, 6):
        p = multiprocessing.Process(target=esperar, args=(i, v,))
        p.start()
        procesos.append(p)
    for p in procesos:
        p.join()
    print(f"tiempo total: {v.value}s")
    

