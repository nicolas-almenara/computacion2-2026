#1. ¿Por qué `writer.write()` no lleva `await` y `writer.drain()` sí?
#writer.write() no lleva await porque solo lleva los bytes a un buffer interno de writer,
#en cambio writer.drain() lo que hace es si el buffer biene muy atras, esperarlo por lo
#tanto se bloquearia el loop, por eso se utiliza await.
#2. Sacá el `await writer.drain()` del servidor. ¿Sigue funcionando con `nc`?
#Si, al sacar await writer.drain() del servidor siguie funcionando.
#3. Entonces, ¿para qué sirve? Escribí un cliente que mande 100 MB sin leer nunca la respuesta, y observá la memoria del servidor con y sin `drain()`.
#writer.drain() lo que hace es esperar al buffer si esta muy lleno, por lo que bloquearia
#el loop, por eso se usa await. Lo que ocurre con el cliente de 100MB con drain es que
#el buffer de escritura se queda clavado en 64KB y la memoria del servidor queda en 20MB.
#Sin drain tanto el buffer de escritura como la memoria del servidor siguien subiendo.
#4. ¿Cuál devuelve qué? Anotá los cuatro resultados. (una lectura sobre b'hola\nmundo\n')
#read(100)        -> b'hola\nmundo\n'  (lo que haya llegado, hasta 100 bytes)
#readline()       -> b'hola\n'         (hasta el \n inclusive)
#readexactly(4)   -> b'hola'           (exactamente 4 bytes)
#readuntil(b'\n') -> b'hola\n'         (hasta el separador inclusive)
#5. ¿Cuáles corresponden a los dos framings de la clase 13?
#Por delimitador: reader.readline() y reader.readuntil(/n).
#por longitud: reader.readexactly(100)
#y el que no corresponderia a ninguno seria reader.read(100)
#6. ¿Qué pasa con `readexactly(100)` si el cliente manda menos y cierra? ¿Qué excepción?
#Lanza asyncio.IncompleteReadError ya que readexactly promete leer exactamente 100 bytes
#por lo que si le llegan menos, se queda esperando por mas.
#7. ¿Qué devuelve `read()` cuando el cliente cerró? ¿Te suena de la clase 13?
#Cuando el cliente cerro, read() envia b'', es decir bytes vacios.