#1. Mirá la salida del servidor. ¿Cuántos threads reporta con tres clientes conectados?
#Con tres clientes conectados reporta un unico thread.
#2. Compará con server_threads.py de la clase 14: contá los threads ahí con ls /proc/$(pgrep -f server_threads)/task | wc -l
#Con server_threads.py y 3 clientes hay 4 threads (3 de conexiones mas el principal), porque ahi
#cada conexion se atendia con un thread. En eco_async.py hay 1 solo thread: cada conexion es
#una Task, y todas las Tasks las ejecuta el mismo thread.
#3. ¿Qué es una conexión en cada caso: un thread o un objeto?
#En el caso de server_threads cada conexion es un thread distinto, en cambio en el caso de
#eco async cada conexion es una task dentro de un mismo thread.
#4. Conectá dos clientes y escribí en ambos. ¿El segundo espera a que el primero reciba su respuesta?
#Luego de conectar dos clientes se puede observar que el segundo no espera a que el primero
#reciba su respuesta, si no que en el momento de la demora con await asyncio.sleep(demora)
#cede el uso del hilo mientras espera, por lo que el loop aprovecha ese tiempo para atender
#al otro.
#5. ¿Por qué el `await asyncio.sleep(3)` no congela a los demás?
#No congela a los demas asyncio.sleep es una corrutina que no bloquea al hilo, cuando hace
#el await la task le avisa al loop que lo despierte en 3 segundos y se suspende y cede el
#control. Mientras el loop esta libre aprovecha a ejecutar otras task.
#6. Cambiá ese `await asyncio.sleep(demora)` por `time.sleep(demora)` y repetí. ¿Qué cambia? Explicá.
#Lo que cambia es que con await asyncio.sleep(demora) se demora 2s y 2s a la vez por task
#en cambio con time.sleep(2) demora 4 es segundos, es decir que en este caso si espera a
#responderle al primer task antes de atender a la segunda.
#7. Con clientes conectados, mandale `SIGTERM` al servidor: `kill -TERM $(pgrep -f eco_async)`. ¿Qué imprime?
#El servidor imprime cerrando: no se aceptan conexiones nuevas. Es decir deja que terminen
#las task que todavia estan vivas pero no acepta nuevas.
#8. Mirá `loop.add_signal_handler()` en el código. ¿En qué se diferencia de `signal.signal()` de la clase 6?
#Con signal.signal() el handler interrumpe al programa en cualquier momento.Con loop.add_signal_handler()
#el loop recibe la señal y ejecuta el callback cerrar.set entre tareas en un momento seguro.
#9. ¿Por qué esa diferencia importa? Relacionalo con async-signal-safety.
#Un handler de signal.signal() puede interrumpir al programa en cualquier punto, incluso en medio
#de una operacion a medias, y por eso solo puede hacer cosas async-signal-safe (muy pocas). Los
#objetos de asyncio (Event, la cola del loop) no lo son: si el handler los tocara en medio de que
#el loop los modifica, podrian quedar corruptos. Con loop.add_signal_handler el unico codigo que
#corre al llegar la señal es escribir un byte en un pipe (seguro), y el callback (cerrar.set) lo
#ejecuta el loop entre tareas, en un momento seguro, donde se puede usar asyncio con normalidad.