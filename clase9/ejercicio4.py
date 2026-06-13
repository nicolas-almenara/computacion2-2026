import threading
import time
class ContadorHilo(threading.Thread):
    def __init__(self, nombre, limite):
        super().__init__(name=nombre)
        self.limite = limite
        self.resultado = ""
    def run(self):
        numeros = []
        for i in range(1, self.limite+1):
            numeros.append(str(i))
            time.sleep(0.1)
        self.resultado = ", ".join(numeros)
threads = []
for i, limite in enumerate([5, 8, 3], 1):
    t = ContadorHilo(f"Contador-{i}", limite)
    threads.append(t)
    t.start()
for t in threads:
    t.join()
for h in threads:
    print(f"[{h.name}] resultado: {h.resultado}")

            

