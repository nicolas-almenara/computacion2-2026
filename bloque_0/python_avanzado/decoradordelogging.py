from functools import wraps
from datetime import datetime
def log_llamada(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        args_str = ", ".join(repr(arg) for arg in args)
        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
        todos_los_args = ", ".join(x for x in [args_str, kwargs_str] if x)
        print(f"[{timestamp}] Llamando a {func.__name__}({todos_los_args})")
        resultado = func(*args, **kwargs)
        print(f"[{timestamp}] {func.__name__} retornó {repr(resultado)}")
        return resultado
    return wrapper
@log_llamada
def sumar(a, b):
    return a + b
@log_llamada
def saludar(nombre, entusiasta=False):
    sufijo = "!" if entusiasta else "."
    return f"Hola, {nombre}{sufijo}"
resultado = sumar(3, 5)
saludar("Ana", entusiasta=True)
