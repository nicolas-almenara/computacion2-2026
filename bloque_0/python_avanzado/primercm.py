from contextlib import contextmanager
import os
@contextmanager
def archivo_temporal(nombre):
    archivo = open(nombre, "w+")
    try:
        yield archivo
    finally:
        archivo.close()
        if os.path.exists(nombre):
            os.remove(nombre)

with archivo_temporal("test.txt") as f:
    f.write("Datos de prueba\n")
    f.write("Más datos\n")
    f.seek(0)
    print(f.read())
import os
assert not os.path.exists("test.txt")
