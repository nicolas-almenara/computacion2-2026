from multiprocessing import Process, Manager
import time
import random
def worker(shared_dict, shared_list, id):
    tiempo = random.uniform(0.2, 1.0)
    time.sleep(tiempo)
    shared_dict[f"worker_{id}"] = {"status": "done", "resultado": id**2, "duracion": tiempo}
    shared_list.append(f"Worker {id} completó en {tiempo:.2f}s")
if __name__ == "__main__":
    with Manager() as manager:
        d = manager.dict()
        l = manager.list()
        procs = [Process(target=worker, args=(d, l, i)) for i in range(5)]
        for p in procs:
            p.start()
        for p in procs:
            p.join()
        print("Diccionario compartido:")
        for k, v in d.items():
            print(f"{k}: {v}")
        print("\nLista compartida (orden de finalización):")
        for item in l:
            print(f"  {item}")
