import socket
s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
s.bind(('::', 8080)); s.listen(5)
while True:
    conn, addr = s.accept()
    print(f"conexion de {addr}")
    conn.close()

#1)El sistema al mandar un paquete verifica si el destino se encuantra dentro de la misma red
#o en otra, en el caso de que sea dentro de la misma red, el sistema envia un ARP(Address resolution protocol)
#request para obtener la mac del destino. Arma la trama Ethernet con es mac destino y la envia
#directamente por la Lan sin tener que pasar por el router/gateway. En caso de que sea otra red
#busca la ruta hacia esa red en la tabla de ruteo que generalmente es hacia el gateway, hace ARP
#request para obtener la mac del gateway. Finalmente arma la trama Ethernet con la mac del gateway
#pero con la ip de destino real, luego el router se encarga de reenviar el paquete hacia la red correcta.

#2)docker usa el rango desde 172.17.0.1 hasta 172.17.255.255 es decir que la mascara de subred es /16.
#Se ven entre si sin configurar nada ya que docket define la red 172.17.0.0 /16 lo que significa que 
#como todos los contenedores estan en la misma red, se pueden comunicar sin necesidad de un gateway,
#por lo tanto no necesitan ninguna configuracion.

#3).getsockname() al tratarse de ipv6 imprime una tupla de 4 valores, lo cuales son ip, puerto,
#flowinfo: que es un campo especifico de ipv6, que combina la etiqueta de flujo y la clase de 
#trafico que son partes de la cabecera ipv6, por lo general es 0. scope_id: le dice al sistema
#por cual interfaz de red usar la direccion ipv6 local, ya que esta misma ip puede repetirse en
#varias interfaces y no sabria cual usar.

#4)La ultima linea da el error ValueError: too many values to unpack, ya que solo estamos
#recibiendo dos elementos, para que funcione se debe guardar el getsockname() en una variable
#y luego pedir por posicion de esa variable.

#5)Ese bug no aparece con ipv4, ya que getsockname() en ipv4 solo tiene dos elementos que son
#ip y puerto, en ipv6 como ya aclare agrega flowinfo y scope_id.

#6)Devuelve las dos familias, primero la ipv6 y luego la ipv4.

#7)Porque tener una ruta ipv6 no garantiza que llegue a destino, la primera ipv6 no se funcionaba
#y si me quedaba con esa no me iba a poder conectar, hay que recorrer en ordern las ips hasta que una
#funcione, para esto se recomienda socket.create_connection() que hace esto internamente.

#8)socket.create_connection() es un bucle que recorre socket.getaddrinfo(), crea un socket
#para todas las direcciones y prueba connect(), si falla, cierra el sokcet y prueba con la 
#siguiente hasta que una conecte. Te devuelve el socket ya conectado o lanza la excepcion.

#9)En el caso de ::1 el servidor ve ::1, y en el caso de 127.0.0.1 el servidor ve ::ffff:127.0.0.1

#10)La del cliente ipv4 tiene el pregijo ::ffff, sirve para que un mismo socket dual stack, sepa que
#la direccion es ipv4.

#11)Al poner IPV6_V6ONLY en 1, el cliente ipv4 nunca se conecta.

#12)Conviene ponerlo aunque el default del sistema sirva, porque este default varia segun
#el sistema operativo, por ejemplo en linux suele ser 0 y en windows 1. Esto significa que
#el programa tendira un determinado funcionamiento segun en el so que se ejecute.