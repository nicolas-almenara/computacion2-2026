import socket

def pedir_con_reintentos(sock, mensaje, destino, intentos=5, timeout=0.5):
    """Manda y reintenta si no llega respuesta.
    PISTA: settimeout() + capturar TimeoutError en un bucle."""
    # TODO
    for i in range(intentos):
        sock.settimeout(timeout)
        sock.sendto(mensaje, destino)
        try:
            respuesta, origen = sock.recvfrom(65535)
            return respuesta
        except TimeoutError as t:
            print(f"Timeout error: {t}")
            continue
    return ("fracaso, no se pudo recibir datos.")

def main():
    mensaje = b'Hola mundo'
    destino = ('localhost', 8080)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    resultado = pedir_con_reintentos(s ,mensaje, destino)
    print (resultado)

if __name__ == "__main__":
    main()


