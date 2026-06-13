import threading
import random
import time
lock = threading.Lock()
class CuentaSegura():
    def __init__(self, saldo_inicial):
        self.saldo = saldo_inicial
    def depositar(self, cantidad):
        with lock:
            saldo_actual = self.saldo
            time.sleep(0.001)
            self.saldo = saldo_actual+cantidad
    def retirar(self, cantidad):
        with lock:
            saldo_actual = self.saldo
            time.sleep(0.001)
            if saldo_actual>=cantidad:
                self.saldo = saldo_actual - cantidad
                return True
            else:
                return False
cuenta = CuentaSegura(1000)
def operaciones_aleatorias():
    for i in range(100):
        if random.choice([True, False]):
            cuenta.depositar(10)
        else:
            cuenta.retirar(10)
threads = [threading.Thread(target=operaciones_aleatorias) for _ in range(10)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print(f"Saldo esperado: 1000 (si no hay errores)")
print(f"Saldo obtenido: {cuenta.saldo}")