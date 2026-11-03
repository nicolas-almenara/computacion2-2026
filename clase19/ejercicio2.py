#1. Mirá la primera sección. ¿De qué clase hereda `BaseHTTPRequestHandler`? ¿Qué le aporta eso?
#BaseHTTPRequestHandler hereda de StreamRequestHandler que a su vez hereda de BaseRequestHandler
#De aca tiene toda la implementacion de tcp resuelta, incluyendo el rfile, wfile el cual 
#permite leer con readline() o read(n) y escribir, client_address y manejo de la conexion 
# (setup(), handle() y finish()).BaseHttpRequestHandler solo agrega la parte de Http por encima
#parsea la linea de pedido y los headers, y llama a do_post(), do_get() segun el metodo.

#2. ¿Qué mixin usa `ThreadingHTTPServer`? ¿Es el mismo de la clase 16?
#ThreadingHTTPServer usa el mixin ThreadingMixIn y HTTPserver.

#3. ¿Por qué hay que leer exactamente Content-Length bytes y no recv(4096)?
#Porque TCP es un flujo de bytes y no respeta limites de mensajes: recv(4096) devuelve
#lo que haya llegado, que puede ser MENOS que el cuerpo (llega partido) o MAS
#(con keep-alive se mezcla el principio del pedido siguiente en la misma conexion).
#Content-Length es framing por longitud (clase 13): dice exactamente cuantos bytes mide
#el cuerpo, y rfile.read(n) lee exactamente esos n bytes, dejando el resto para el
#pedido siguiente. Para el cuerpo no se usa un delimitador porque puede contener cualquier byte.

#4. La respuesta dice HTTP/1.0 aunque pedimos 1.1. ¿Qué cambia si protocol_version = 'HTTP/1.1'?
#protocol_version = 'HTTP/1.1' define la version con la que responde el servidor, por defecto
#'HTTP/1.0'. 1.1 activa keep-alive, la conexion no se cierra despues de cada respuesta, y el cliente
#puede mandar varios pedidos por el mismo socket. En 1.1 pasa a ser obligatorio content-lenght, mientras
#que en 1.0 se marca cerrando la conexion.

#5. Agregale un `do_DELETE`. ¿Qué código de estado conviene devolver?
#Conviene devolver el codigo de estado '204 no content' (familia 2xx exito), indica que el
#borrado salio bien y que no hay nada para devolver.

#6. ¿Qué pasa si mandás un método que no implementaste, como `PATCH`? ¿Qué código devuelve el framework solo?
#Devuelve un codigo de estado '501 unsupported method' (familia 500 error del servidor).

#7En FastAPI un endpoint son ~3 lineas (decorador, funcion y return), en crudo.py son ~10.
#FastAPI nos ahorra: convertir a JSON, armar lo headers, el codigo de estado, leer el cuerpo,
#elegir la funcion segun la ruta, validar los datos y generar documentacion en /docs.
