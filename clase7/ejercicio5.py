#Corré el mismo programa con set_start_method('fork') y set_start_method('spawn').
#Medí el tiempo de creación de 100 procesos en cada caso
import multiprocessing
import time
def contenido(nro_proceso):
    print(f"proceso numero {nro_proceso}")
if __name__ == "__main__":
    multiprocessing.set_start_method("fork")
    #multiprocessing.set_start_method("spawn")
    procesos=[]
    tiempo_inicial = time.time()
    for i in range(100):
        p = multiprocessing.Process(target=contenido, args=(i,))
        p.start()
        procesos.append(p)
    tiempo_final = time.time()
    for p in procesos:
        p.join()
    print(f"tiempo que tardo:{tiempo_final-tiempo_inicial}")

