import select, socket
relleno = [socket.socket() for _ in range(1100)]
alto = relleno[-1]
print("fd:", alto.fileno())
poller = select.poll()
poller.register(alto, select.POLLIN)
print(poller.poll(0))

#7)Da el siguiente error filedescriptor out of range in select().

#8)El limite de select es el numero del descriptor, el cual no puede ser mayor a 1102.

#9)poll no falla con un numero de file descriptor alto, esto es porque poll utiliza un 
#arreglo de sockets, en cambio select utliza un mapa de bits de tamaño fijo, por esto
#por lo que no tiene el limite de 1024 que tiene select.

#10)En desarrollo normalmente abris pocos archivos/sockets en cambio en produccion se 
#abren muchas conexiones durante mucho tiempo, pudiendo sobrepasar el limite de 1024 fd.