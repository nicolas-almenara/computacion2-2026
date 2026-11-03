import struct
import socket

def recibir_exacto(sock, n):
    """Lee EXACTAMENTE n bytes, o None si cerraron antes.
    PISTA: recv(n) puede devolver menos de n. Hay que insistir."""
    buffer = b''
    while len(buffer) < n:
        pedazo = sock.recv(n-len(buffer))
        if not pedazo:
            return 
        buffer += pedazo
    return buffer

def enviar_mensaje(sock, payload: bytes):
    cabecera = struct.pack('!I', len(payload))
    sock.sendall(cabecera + payload)
    

def recibir_mensaje(sock):
        cabecera = recibir_exacto(sock, 4)
        tamaño_tupla = struct.unpack('!I', cabecera)
        tamaño = tamaño_tupla[0]
        return recibir_exacto(sock, tamaño)

def main():
     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', 8080))
        print("eschuchando en 0.0.0.0 en el puerto 8080")
        s.listen(5)
        conn, direccion = s.accept()
        mensaje = recibir_mensaje(conn)
        print(f"mensaje recibido: {mensaje}")
        payload = b'hola desde el servidor'
        enviar_mensaje(conn,payload)
if __name__ == "__main__":
     main()