#1. ¿En qué thread corre el endpoint `async`? ¿Y el `def` común?
#El endpoint async corre en el main thread, estos se ejecutan en el event loop que corre dentro
#del hilo principal. En cambio el def comun corre en 'any io worker thread', es decir FastAPI
#lo manda a un poolthread para que no interfiera con el loop principal.
#2. Pedí `/quien-soy` dos veces y compará el `id_del_loop`. ¿Hay uno o varios event loops?
#Hay un unico event loop en el cual cada tarea va cediendo el hilo cuando tenga un await.
#3. ¿Por qué el endpoint sincrónico dice que no hay loop corriendo?
#El endpoint sincrono dice que no hay loop corriendo porque este no corre en un evento loop
#sino que FastAPI lo pone en un threadingpool.
#4. ¿Quién crea el event loop: FastAPI o uvicorn? ¿Qué es ASGI?
#uvicorn crea el event loop, es el servidor que crea y ejecuta el event loop y le envia
#los pedidos a FastAPI.
#ASGI(asynchronous server gateway interface): es el estandar que define como se comunica
#un servidor web con una aplicacion asincrona de python.
#5. Levantá con `uvicorn api:app --workers 3` y pedí `/quien-soy` varias veces. ¿Cambia el `pid`?
#Al levantarlo con uvicorn api:app --workers 3, los /quien-soy tienen distintos pid. Lo que 
#hace --workers 3 es crear 3 procesos distintos y por eso tenian id de loop diferentes. Algunos
#se repiten porque se reutiliza el mismo socket (los que ejecuta el mismo worker).
#6. Con varios workers, ¿qué pasa con el diccionario `tareas`? Probá: creá una tarea y pedila varias veces hasta que dé 404. Explicá por qué.
#Con varios workets algunos pedidos dan 200 Ok Y otros dan 404 not found, esto es porque el 
#worker(proceso) que creo la tarea la tiene guardada en su memoria y cuando la pidas dara
#200, en cambio los otros workers tienen su propia version de la lista de tareas(desactualizada)
#por lo tanto da como codigo de estado 404 not found.
#7. ¿Qué implica eso para el TP2? ¿Dónde debería vivir el estado en un sistema real?
#Implica que un diccionario en memoria solo sirve con un unico proceso: con varios workers cada
#uno tendria un estado distinto y los resultados serian inconsistentes (404 aleatorios, limites que
#no se cumplen). En el TP2 hay que usar un solo proceso, o compartir el estado entre procesos
#con mecanismos de IPC (multiprocessing).
#En un sistema real el estado debe vivir fuera de los procesos de la aplicacion, en un servicio
#compartido como una base de datos o Redis, y los workers no deben guardar estado propio.
#Asi da igual que worker atienda cada pedido, y el estado sobrevive a los reinicios.