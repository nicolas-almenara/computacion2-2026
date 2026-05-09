import signal
import time
import os
class Servidor:
    def __init__(self):
        self.ejecutando = True
        self.configuracion = {"max_conexiones": 0, "timeouts": 0}
        self.estadisticas = {"request": 0, "errores": 0, "inicio": time.time()}
    def registrar_manejadores(self):
        signal.signal(signal.SIGTERM, self.apagado_limpio)
        signal.signal(signal.SIGINT, self.apagado_limpio)
        signal.signal(signal.SIGHUP, self.recarga_configuracion)
        signal.signal(signal.SIGUSR1, self.mostrar_estadisticas)
        signal.signal(signal.SIGUSR2, self.mostrar_logs)

    def apagado_limpio(self, sig, frame):
        nombre = signal.Signals(sig).name
        print(f"{nombre} detectado, iniciando apagado limpio")
        self.ejecutando = False
    def recarga_configuracion(self, sig, frame):
        print(f"SIGHUP detectado, recargando configuracion")
        self.configuracion["max_conexiones"] += 5
        self.configuracion["timeouts"] += 5
        print(f"nueva configuracion: {self.configuracion}")
    def mostrar_estadisticas(self, sig, frame):
        print(f"SIGUSR1 detectado, estadisticas: {self.estadisticas}")
    def mostrar_logs(self, sig, frame):
        print("SIGUSR2 detectado, rotando logs")
        print(f"[SIGUSR2] Logs rotados a server.log.{int(time.time())}")
    def run(self):
        print(f"servido iniciado (PID: {os.getpid})")
        print("Comandos disponibles:")
        print(f"  kill -HUP {os.getpid()}   -> Recargar config")
        print(f"  kill -USR1 {os.getpid()}  -> Ver stats")
        print(f"  kill -USR2 {os.getpid()}  -> Rotar logs")
        print(f"  kill {os.getpid()}        -> Shutdown")
        while self.ejecutando:
            self.registrar_manejadores()
        print("Realizando cleanup...")
        time.sleep(0.5)
        print(f"Servidor terminado. Requests procesadas: {self.stats['requests']}")
if __name__ == "__main__":
    servidor = Servidor()
    servidor.run()
