import signal
import time
class Timeout(Exception):
    pass
def handler(sig, frame):
    raise Timeout("Timeout: se a pasado del tiempo limite")
def con_timeout(segundos):
    def decorador(func):
        def wrapper(*args, **kwargs):
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(segundos)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorador
@con_timeout(3)
def operacion_lenta():
    import time
    print("Iniciando operación...")
    time.sleep(5)
    return "Completado"

@con_timeout(3)
def operacion_rapida():
    import time
    print("Iniciando operación...")
    time.sleep(1)
    return "Completado"

print("=== Operación rápida ===")
try:
    resultado = operacion_rapida()
    print(f"Resultado: {resultado}")
except Timeout as e:
    print(f"Timeout: {e}")

print("\n=== Operación lenta ===")
try:
    resultado = operacion_lenta()
    print(f"Resultado: {resultado}")
except Timeout as e:
    print(f"Timeout: {e}")

