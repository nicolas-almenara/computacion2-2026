import threading
import math
import time
def cpu_intensive(N):
    return sum(math.sqrt(i) for i in range (N))
N = 5_000_000
inico_secuencial = time.time()
for _ in range(4):
    cpu_intensive(N)
final_secuencial = time.time()
total_secuencial = final_secuencial - inico_secuencial
print(f"tiempo total secuencial: {total_secuencial :.2f}")
inicio_paralelo = time.time()
threads = []
for i in range(4):
    t = threading.Thread(target=cpu_intensive, args=(N,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()
final_paralelo = time.time()
total_paralelo = final_paralelo - inicio_paralelo
print(f"tiempo total paralelo: {total_paralelo :.2f}")
print(f"mejora con paralelismo: {total_secuencial/total_paralelo :.2f}")
