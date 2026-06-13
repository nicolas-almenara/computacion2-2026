import threading

saldo = 1000
lock = threading.Lock()
def retirar(monto):
    global saldo
    with lock:
        if saldo >= monto:
            import time; time.sleep(0.001)  # simular procesamiento
            saldo -= monto
            print(f"Retiro de ${monto} exitoso. Saldo: ${saldo}")
        else:
            print(f"Saldo insuficiente para retirar ${monto}")
threads = []
for i in range(10):
    t = threading.Thread(target=retirar, args=(200,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()

