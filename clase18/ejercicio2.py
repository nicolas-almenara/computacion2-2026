import time
from collections import deque

def dormir(segundos):
    yield time.monotonic() + segundos

def tarea(nombre, pasos):
    for i in range(1, pasos+1):
        print(f"[{nombre}], paso {i} de {pasos}")
        yield

def tarea_egoista(nombre):
    print(f'  [{nombre}] me pongo a calcular')
    import time
    time.sleep(3)              # no cede el control
    print(f'  [{nombre}] listo')
    yield

def tarea_lenta(nombre, veces, espera):
    for i in range(veces):
        print(f" [{nombre}] {i}")
        yield from dormir(espera)

def scheduler(tareas):
    pendientes = deque((0, t) for t in tareas)
    while pendientes:
        despertar, t = pendientes.popleft()
        ahora = time.monotonic()
        if ahora<despertar:
            pendientes.append((despertar, t))
            continue
        try:
            cuando = next(t)
            pendientes.append((cuando or 0, t))
        except StopIteration:
            pass
inicio=time.monotonic()
scheduler([tarea_lenta('A', 2, 0.15), tarea_lenta('B', 2, 0.15), tarea_lenta('C', 2, 0.15)])
fin=time.monotonic()
print(f"tiempo {fin-inicio}")
#1. Corrélo con tres tareas de distinta cantidad de pasos. ¿En qué orden salen?
#Salen en el orden en el que le evias las tareas, va completando cada paso 1 por 1
#hasta que van terminando.

#2. ¿Cuántas veces llamó a `next()` en total? Agregá un contador.
#Llamo a next() en total 12 veces. es decir pasos mas 1 por cada tarea, esto es porque
#el ultimo no encuentra ningun yield y lanza StopIteration.

#3. ¿Qué pasa si una tarea no tiene ningún `yield`? Probalo.
#Si una tarea no tiene ningun yield, se hace un unico next() el cual no encuntra
#ningun yield y lanza StopIteration.

#4. Metela entre las otras y corré el scheduler. ¿Qué les pasa a las demás durante esos 3 segundos?
#Las demas tareas durante esos segundos quedan bloqueadas esperando esos 3 segundos ya que
#corre sobre un unico hilo y la tarea egoista no devuelve el control al scheduler.

#5. Con threads (clase 10), ¿habría pasado lo mismo? Explicá la diferencia entre concurrencia cooperativa y preventiva.
#Con threads no hubiera pasado lo mismo ya que el kernel del sistema operativo hubiera
#dado tiempo de cpu a las otras tareas mientra ocurria el time.sleep(3) en paralelo. Eso es 
#concurrencia preventiva: el kernel del sistema operativo decide cuando interrumpir un hilo
#y darle lugar a otro, sin 'pedir permiso'. Concurrencia cooperativa: cada tarea decide voluntariamente
#cuando ceder y si una no coopera, bloquea a todas las demas.

#8. ¿Por qué `dormir()` no puede simplemente llamar a `time.sleep()`?
#No puede simplemente llamar a time.sleep() ya que en ese bloquearia a las demas tareas
#esperando ese tiempo muerto sin progresar en las demas.

#9. Corré tres tareas que esperen 0.15s cada una, varias veces. ¿El total es la suma de las esperas o menos? ¿Por qué?
#El total es menos de la suma de las esperas ya que justamente mientras una tarea espera
#inicia la espera de otra tarea, entonces termina mucho antes de la suma de las esperas.

#10. En `tarea_lenta`, ¿qué hace `yield from dormir(espera)`? ¿Por qué no alcanza con llamar `dormir(espera)` a secas?
#Lo que hace yield form es delegar al generador dormir como si lo hiciera ella misma,
#Si hicieras dormir(espera) solo crearias el objeto de la funcion generadora, no lo correria.

#11. Probá cambiarlo por `dormir(espera)` sin el `yield from`. ¿Qué pasa y por qué no falla ruidosamente?
#Lo que pasa no tiene ningun yield y deja de ser generadora, al llamarla se ejecuta todo el 
#for de una sola vez y devuelve None. No falla porque es sintacticamente correcto, el error recien
#aparece cuando el scheduler tira un next(None) y tira TypeError.