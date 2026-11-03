#1. Identificá en la respuesta las tres partes: línea de estado, headers, cuerpo. ¿Qué las separa?
#La linea de estado se separa de los headers por un \r\n  y los headers del cuerpo se separan
#por un \r\n\r\n,

#2. ¿Qué código de estado devolvió? ¿Qué familia es?
#Devolvio el codigo de estado 200 OK, es la familia 2xx que es la de exito. El servidor entendio
#el pedido y devolvio el recurso.

#3. Sacá el header `Host:` y repetí. ¿Qué pasa? ¿Por qué HTTP/1.1 lo exige?
#Devuelve 400 bad request (familia 4xx, error del cliente): el pedido esta mal formado
#HTTP/1.1 exige host porque una misma ip puede alojar varios sitios.

#4. Cambiá `GET /` por `GET /noexiste`. ¿Qué código devuelve ahora?
#Ahora devuelve el codigo 404 not found (familia 4xx, error del cliente). Este error nos indica
#que el recurso al que solicito acceder el cliente no existe.

#5. Probá el mismo pedido usando `\n` en vez de `\r\n`. ¿Funciona contra `example.com`? ¿Y contra el servidor de `crudo.py`?
#Si, funciona con los dos, ambos devuelven 200ok. Ambos son tolerantes a \n.

#6. ¿Por qué es mala idea depender de que un servidor tolere `\n`?
#Es mala idea ya que \r\n es un estandar de http, en cambio \n es solo una capacidad que
#alguno servidores toleran, pero no estan obligados, por lo que podria responder 400 bad request
#o quedarse esperando indefinidamente.

#7. ¿Cuáles de estos son **seguros** (no modifican nada): GET, POST, PUT, DELETE, HEAD?
#Los seguros son get (pide un recurso) y head (pide un recurso pero solo los headers).
#Post crea un recurso, put modifica un recurso y delete elimina un recurso.

#8. ¿Cuáles son **idempotentes**? Explicá por qué `POST` no lo es.
#Un metodo es idempotente si hacerlo 1 vez o n veces el servidor sigue en el mismo estado.
#Son idempotentes GET, HEAD, PUT, DELETE.
#GET Y HEAD no modifican nada, asi que repetirlos no cambia nada.
#PUT con los mismos datos, la primera vez la reemplaza, las siguientes lo deja igual.
#DELETE la primera vez lo borra, la siguiente ya no hay nada que borrar.
#POST no es idempotente ya que cada que se ejecuta crea un nuevo recurso.

#9. Tu cliente manda un `POST` y le vence el timeout sin respuesta. ¿Es seguro reintentar? ¿Y si fuera un `PUT`?
#En el caso de un post no es seguro reintentar ya que puede duplicarse el dato si ya funciono
#la primera vez (no idempotente y no seguro), en cambio con un put si es seguro reintentarlo
#ya que si funciono la primera vez, en la segunda no va a pasar nada, y en el caso de que no haya
#funcionado lo reintentamos (idempotente y no seguro).

