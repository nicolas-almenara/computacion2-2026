import time
from functools import wraps
def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            intento = 0
            while intento < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    intento += 1
                    if intento == max_attempts:
                        print(f"Intento {intento}/{max_attempts} falló: {e}")
                        raise
                    print(f"Intento {intento}/{max_attempts} falló: {e}. Esperando {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator
import random
@retry(max_attempts=3, delay=1)
def conectar_servidor():
    if random.random() < 0.7:
        raise ConnectionError("Servidor no disponible")
    return "Conectado exitosamente"
try:
    resultado = conectar_servidor()
    print(resultado)
except ConnectionError:
    print("Falló después de 3 intentos")