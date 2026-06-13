from multiprocessing import Array, Value, Process
import time
def incrementar(contador, n_veces, id):
    for i in range(n_veces):
        with contador.get_lock():
            contador.value += 1
    print(f"el worker {id} termino sus {n_veces} incrementos")
def llenar_array(arr, valor_inicial, id):
    inicio = (len(arr) // 4) * id
    fin = (len(arr) // 4) + inicio
    for i in range(inicio, fin):
        arr[i] = valor_inicial+i
if __name__ == "__main__":
    contador = Value("i", 0)
    procs = [Process(target=incrementar, args=(contador, 10000, i)) for i in range(4)]
    for proc in procs:
        proc.start()
    for proc in procs:
        proc.join()
    print(f"\nContador final: {contador.value}")
    assert contador.value == 40000, "¡Race condition! Falta el lock"
    arr = Array("i", 100)
    procs = [Process(target=llenar_array, args=(arr, 1000, i))
             for i in range(4)]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    print(f"Array completo (primeros 10): {list(arr)[:10]}")
    print(f"Array completo (últimos 10): {list(arr)[-10:]}")
