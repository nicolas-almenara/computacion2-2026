import threading
import time
import random
class ConnectionPool():
    def __init__(self, size):
        self.size = size
        self.semaforo = threading.Semaphore(size)
        self.conexiones_disponibles = list(range(size))
        self.lock = threading.Lock()
        self.estadisticas = {"total_request": 0, "esperas": 0, "tiempo_total_espera": 0}
    def obtener(self, timeout=None):
        tiempo_inicial = time.time()
        if self.semaforo.acquire(timeout=timeout):
            tiempo_espera = time.time() - tiempo_inicial
            with self.lock:
                conn_id = self.conexiones_disponibles.pop(0)
                self.estadisticas["total_request"] += 1
                if tiempo_espera > 0.01:
                    self.estadisticas["esperas"] += 1
                    self.estadisticas["tiempo_total_espera"] += tiempo_espera
            return conn_id
        return None
    def liberar(self, conn_id):
        with self.lock:
            self.conexiones_disponibles.append(conn_id)
        self.semaforo.release()
    def mostrar_estadisticas(self):
        print(f"total request: {self.estadisticas["total_request"]}, esperas: {self.estadisticas["esperas"]}")
        if self.estadisticas["esperas"] > 0:
            print(f"tiempo proemedio de espera: {self.estadisticas['tiempo_total_espera'] / self.estadisticas['esperas']}")
pool = ConnectionPool(3)
def cliente(id):
    for i in range(3):
        conn = pool.obtener(timeout=5)
        if conn is not None:
            print(f"el cliente {id} obtuvo la conexion")
            time.sleep(random.uniform(0.5, 1.5))
            pool.liberar(conn)
            print(f"conexion liberada")
        else:
            print(f"timepo de espera excedido, hubo timeout")
        time.sleep(random.uniform(0.1, 0.3))
threads = [threading.Thread(target=cliente, args=(i,)) for i in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
pool.mostrar_estadisticas()



