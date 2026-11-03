import socket
c = socket.create_connection(('0.0.0.0', 8080))
c.settimeout(3)
mensaje = c.recv(4096)
