import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(('localhost', 8080))
    datos = b'x'* (1024*1024*10)
    cant_datos = len(datos)
    enviados = s.send(datos)
    print(f"los datos eran {cant_datos} y llegaron {enviados}")