import asyncio
import threading
import time

# ---------- 4.1 Cuando no hacen falta ----------
contador = 0


async def sumar():
    global contador
    contador += 1


async def prueba_corrutinas():
    global contador
    contador = 0
    await asyncio.gather(*(sumar() for _ in range(1000)))
    print(f'corrutinas:           contador = {contador}  (esperado 1000)')


def sumar_thread():
    global contador
    contador += 1


def sumar_thread_con_pausa():
    global contador
    leido = contador
    time.sleep(0)                 # el GIL puede pasar a otro thread aca
    contador = leido + 1


def prueba_threads(funcion, etiqueta):
    global contador
    contador = 0
    hilos = [threading.Thread(target=funcion) for _ in range(1000)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    print(f'{etiqueta:<21} contador = {contador}  (esperado 1000)')


# ---------- 4.2 Cuando si ----------
cuentas = {'a': 1000}


async def transferir(origen, monto):
    saldo = cuentas[origen]
    await asyncio.sleep(0)        # punto de suspension en el medio
    cuentas[origen] = saldo - monto


async def prueba_sin_lock():
    cuentas['a'] = 1000
    await asyncio.gather(*(transferir('a', 1) for _ in range(100)))
    print(f'sin lock:             saldo = {cuentas["a"]}  (esperado 900)')


lock = asyncio.Lock()


async def transferir_seguro(origen, monto):
    async with lock:              # async with, no with
        saldo = cuentas[origen]
        await asyncio.sleep(0)
        cuentas[origen] = saldo - monto


async def prueba_con_lock():
    cuentas['a'] = 1000
    await asyncio.gather(*(transferir_seguro('a', 1) for _ in range(100)))
    print(f'con lock:             saldo = {cuentas["a"]}  (esperado 900)')


async def main():
    print('--- 4.1 ---')
    await prueba_corrutinas()
    prueba_threads(sumar_thread, 'threads:')
    prueba_threads(sumar_thread_con_pausa, 'threads con pausa:')
    print('\n--- 4.2 ---')
    await prueba_sin_lock()
    await prueba_con_lock()


asyncio.run(main())

#Corrutinas: queda en 1000. Entre dos await nadie interrumpe, y sumar() no tiene ninguno.
#Threads: en mi prueba también dio 1000, y es una sorpresa. Python 3.12 casi nunca cambia de thread en medio de un contador += 1 simple, así que la race condition que viste en la clase 11 no se reproduce con ese código, ni con 100 millones de sumas. Se reproduce si hay una pausa entre leer y escribir: con time.sleep(0) en el medio, 100 threads x 100 sumas dieron 175 en vez de 10000. Si te da 1000, anotalo tal cual y aclará que en 3.12 es difícil de provocar.
#Por qué no hace falta Lock con corrutinas: el cambio de contexto solo ocurre en un await.
#100 transferencias: saldo 999, no 900. Todas leyeron 1000 antes de que alguna escribiera.
#Por qué hay race condition con un solo hilo: el await asyncio.sleep(0) es un punto de suspensión entre leer y escribir. Otra tarea corre ahí y la primera después escribe un valor viejo.
#Con asyncio.Lock: da 900. Se usa async with porque esperar el lock puede requerir suspenderse, y with común no puede hacer un await.
#La regla: hace falta un lock cuando la sección crítica contiene un await.