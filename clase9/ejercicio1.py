import threading
import time
def tarea(nombre):
    for i in range(1, 5):
        print(f"nombre del thread: {nombre}, numero {i}")
        time.sleep(0.2)
threads = []
for i in range(3):
    t = threading.Thread(target=tarea, args=((f"nombre{i}"),))
    threads.append(t)
    t.start()
for t in threads:
    t.join()
print("listos")

