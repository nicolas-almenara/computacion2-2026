import socket
def recibir_lineas(sock):
    buffer = b''
    while True:
        pedazo = sock.recv(4096)
        if not pedazo:
            return
        buffer += pedazo
        while b'\n' in buffer:
            linea, buffer = buffer.split(b'\n', 1)
            yield linea
def atender(conn):
    for linea in recibir_lineas(conn):
        mayuscula = linea.upper()
        conn.sendall(mayuscula + b'\n')
def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', 8080))
        s.listen(5)
        print("escuhcando en 0.0.0.0, puerto 8080:")
        while True:
            conn, direccion = s.accept()
            print(f"conexion desde {direccion}")
            with conn as c:
                atender(c)
if __name__ == "__main__":
    main()





