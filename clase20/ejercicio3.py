#1. Copiá los cuatro tiempos. ¿Por qué `gather` tarda lo que la más lenta y no la suma?
#gather tarda lo mismo que la tarea mas lenta ya que lanza las corrutinas al mismo tiempo
#en un unico hilo, esperandolas hasta que terminen todas.
#2. ¿Por qué el semáforo da un tiempo intermedio?
#El semaforo da un tiempo intermedio ya que acota cuantas corren a la vez para no agotar
#descriptores ni saturar la red.
#3. Con el timeout de 0.8s, ¿cuántas se cancelaron? ¿Qué les pasó a esas tareas?
#Con el timeout de 0.8s se cancelo 1 tarea, al vencer el tiempo asyncio.timeout cancela
#esas tareas, le inyecta CancelledError en su await que se convierte en un TimeoutError.
#4. Medí 10 descargas secuenciales contra 10 concurrentes. ¿Cuánto mejora?
#secuencial   10 descargas en  4.63s
#concurrente  10 descargas en  0.59s
#5. ¿Por qué el `AsyncClient` se crea **una vez** y no uno por descarga? (Pista: keep-alive, clase 19.)
#Porque el cliente mantiene un pool de conexiones y las reutiliza (keep-alive, clase 19). Con uno
#por descarga se abre una conexion TCP (y TLS) nueva cada vez, y se pierde ese ahorro.
#6. Cambiá `httpx` por `requests` dentro de la corrutina. ¿Qué pasa con los tiempos? Explicá con lo de la clase 19.
#Empeoran: gather deja de ayudar y tarda como el secuencial. requests es bloqueante, no tiene
#await y congela el unico hilo del loop, asi que las descargas van una detras de otra
#(el caso async def con codigo bloqueante, /async-mal de la clase 19).
#7. Agregá un `Semaphore(3)` y volvé a medir. ¿Cuál es el nuevo tiempo?
#El nuevo tiempo con el semaforo fue de 1.28s.
#8. ¿Qué problema evita acotar la concurrencia? Nombrá dos.
#Acotar la concurrencia evita los problemas de quedarse sin descriptores de archivos, saturar
#la red, o que el servidor nos bloquee en el otro lado por mandar demasiados pedidos juntos.
#9. Probá con 200 URLs sin semáforo. ¿Qué error aparece? (Pista: `ulimit -n`.)
#Aparece el error httpx.ConnectTimeout, esto es porque se intentan abrir demasiadas conexiones
#a la vez, por lo que algunas se pasan del timeout. Si bajamos el unilimit -n a un numero
#menor, se agotarian la cantidad de descriptores y falla con ConnectError.
#10. Agregá una URL inválida a la lista. Con `gather` normal, ¿qué pasa con las demás?
#Cuando hay una URL invalida tira la excepcion Name or service not known.Lo que pasa es que
#las demas tareas si se ejecutan pero en segundo plano, perdiendose sus valores.
#11. Probá asyncio.gather(..., return_exceptions=True). ¿Qué cambia?
#gather ya no corta con la excepcion: devuelve una lista completa con un elemento por descarga,
#con el resultado de las que salieron bien y el objeto excepcion en el lugar de la que fallo.
