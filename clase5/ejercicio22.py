import signal
import time
import os
class Aplicacion:
    def __init__(self):
        self.ejecutando = True
        self.recursos = []
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
    def shutdown(self, sig, frame):
        nombre_señal = signal.Signals(sig).name
        print(f"\nrecibi la señal {nombre_señal}, cerrando")
        self.ejecutando = False
    def adquirir_recurso(self, nombre):
        print(f"adquieriendo recurso: {nombre}")
        self.recursos.append(nombre)
    def liberar_recursos(self):
        for recurso in reversed(self.recursos):
            print(f"liberando recurso: {recurso}")
            time.sleep(0.3)
        self.recursos.clear()
    def run(self):
        print(f"pid: {os.getpid()}")
        self.adquirir_recurso("base_de_datos")
        self.adquirir_recurso("archivo_log")
        self.adquirir_recurso("conexion_red")
        while self.ejecutando:
            print("currently working...")
            time.sleep(1)
        self.liberar_recursos()
        print("aplicacion terminada correctamente")
if __name__ == "__main__":
    app = Aplicacion()
    app.run()    