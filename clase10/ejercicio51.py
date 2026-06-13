import threading
import time
import random
class ReadWriteLock():
    def __init__(self):
        self.readers = 0
        self.writers = 0
        self.lock = threading.Lock()
        self.can_read = threading.Condition(self.lock)
        self.can_write = threading.Condition(self.lock)
    def acquire_read(self):
        with self.lock:
            while self.writers > 0:
                self.can_read.wait()
            self.readers += 1
    def release_read(self):
        with self.lock:
            self.readers -= 1
            if self.readers == 0:
                self.can_write.notify()
    def acquire_write(self):
        with self.lock:
            while self.writers > 0 or self.readers > 0:
                self.can_write.wait()
            self.writers += 1
    def release_write(self):
        with self.lock:
            self.writers -= 1
            self.can_read.notify_all()
            self.can_write.notify()
class ReadLock():
    def __init__(self, rwlock): self.rwlock = rwlock
    def __enter__(self): self.rwlock.acquire_read()  
    def __exit__(self, *args): self.rwlock.release_read()
class WriteLock():
    def __init__(self, rwlock): self.rwlock = rwlock
    def __enter__(self): self.rwlock.acquire_write()  
    def __exit__(self, *args): self.rwlock.release_write()
rwlock = ReadWriteLock()
datos = {"valor": 0, "lecturas": 0, "escrituras": 0}
def lector(id):
    for i in range(5):
        with ReadLock(rwlock):
            valor = datos["valor"]
            datos["lecturas"] += 1
            print(f"valor leido: {valor}")
            time.sleep(random.uniform(0.1, 0.2))
        time.sleep(random.uniform(0.2, 0.4))
def escritor(id):
    for i in range(3):
        with WriteLock(rwlock):
            datos["valor"] = id*100 + i
            datos["escrituras"] += 1
            print(f"valor escrito: {datos['valor']}")
            time.sleep(random.uniform(0.1, 0.2))
        time.sleep(random.uniform(0.2, 0.4))
threads = []
for i in range(5):
    t = threading.Thread(target=lector, args=(i,))
    threads.append(t)
for i in range(5, 7):
    t = threading.Thread(target=escritor, args=(i,))
    threads.append(t)
random.shuffle(threads)
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"\nEstadísticas finales:")
print(f"  Valor final: {datos['valor']}")
print(f"  Total lecturas: {datos['lecturas']}")
print(f"  Total escrituras: {datos['escrituras']}")