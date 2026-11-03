import socket 
import time

def conectar_con_reintentos(host, puerto, intentos=5):
    for intento in range(1, intentos+1):
        try:
            s = socket.create_connection((host, puerto))
            return s
        except ConnectionRefusedError as e:
            print(f"error de conexion: {e}")
            time.sleep(0.1*intento)
            continue
        
        