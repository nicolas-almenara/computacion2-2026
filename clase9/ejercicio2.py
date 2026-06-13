import threading
import time
URLS = [f"http://servidor.com/archivo_{i}.zip" for i in range(5)]
DEMORA = 1
def simular_descarga(url, demora):
    print(f"descargando archivo: {url}, demora: {demora}")
    time.sleep(demora)
tiempo_inicial_secuencial = time.time()
for i in range(5):
    simular_descarga(URLS[i], DEMORA)
tiempo_final_secuencial = time.time()
tiempo_secuencial = tiempo_final_secuencial - tiempo_inicial_secuencial
threads = []
tiempo_inicial_paralelo = time.time()
for i in range(len(URLS)):
    t = threading.Thread(target=simular_descarga, args=(URLS[i], DEMORA))
    threads.append(t)
    t.start()
for t in threads:
    t.join()
tiempo_final_paralelo = time.time()
tiempo_paralelo = tiempo_final_paralelo - tiempo_inicial_paralelo
print(f"el tiempo total en secuencial es {tiempo_secuencial:.2f}, el tiempo total en paralelo es {tiempo_paralelo:.2f}")
print(f"mejora con paralelismo: {tiempo_secuencial/tiempo_paralelo :.2f}x")