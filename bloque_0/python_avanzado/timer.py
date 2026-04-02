import time
class Timer:
    def __init__(self, nombre=None):
        self.nombre = nombre
        self._start = None
        self.elapsed = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self._start
        if self.nombre:
            print(f"[Timer] {self.nombre}: {self.elapsed:.3f}s")
with Timer("Procesamiento de datos"):
    datos = [x**2 for x in range(1000000)]
with Timer() as t:
    time.sleep(0.5)
print(f"El bloque tardó {t.elapsed:.3f} segundos")
with Timer() as t:
    time.sleep(0.2)
    print(f"Después del paso 1: {t.elapsed:.3f}s")
    time.sleep(0.3)
    print(f"Después del paso 2: {t.elapsed:.3f}s")
from contextlib import contextmanager
@contextmanager
def timer(nombre=None):
    start = time.perf_counter()
    t = type("TimerContext", (), {})()
    t.elapsed = 0.0
    try:
        yield t
    finally:
        t.elapsed = time.perf_counter() - start
        if nombre:
            print(f"[Timer] {nombre}: {t.elapsed:.3f}s")
with timer("Procesamiento de datos"):
    datos = [x**2 for x in range(1000000)]

with timer() as t:
    time.sleep(0.5)
print(f"El bloque tardó {t.elapsed:.3f} segundos")

with timer() as t:
    time.sleep(0.2)
    print(f"Después del paso 1: {t.elapsed:.3f}s")
    time.sleep(0.3)
    print(f"Después del paso 2: {t.elapsed:.3f}s")