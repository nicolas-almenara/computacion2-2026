from multiprocessing import Process, Value
def incrementar(contador, n, nombre):
    print(f"[{nombre}] Iniciando {n} incrementos...")
    for _ in range(n):
        contador.value += 1
    print(f"[{nombre}] Terminado")
contador = Value("i", 0)
N = 100000
Procesos = []
for i in range(4):
    p = Process(target=incrementar, args=(contador, N, f"P{i}"))
    p.start()
    Procesos.append(p)
for p in Procesos:
    p.join()
esperado = 4 * N
print(f"\nEsperado: {esperado}")
print(f"Obtenido: {contador.value}")
print(f"Diferencia: {esperado - contador.value} incrementos perdidos")