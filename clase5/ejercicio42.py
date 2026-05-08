import signal
import time
class TimerPeriodico:
    def __init__(self, intervalo, callback):
        self.intervalo = intervalo
        self.callback = callback
        self.activo = False
    def handler(self, sig, frame):
        if self.activo == True:
            self.callback()
    def iniciar(self):
        self.activo = True
        signal.signal(signal.SIGALRM, self.handler)
        signal.setitimer(signal.ITIMER_REAL, self.intervalo, self.intervalo)
        print(f"timer iniciado (cada {self.intervalo}s)")
    def detener(self):
        self.activo = False
        signal.setitimer(signal.ITIMER_REAL, 0)
        print("timer detenido")
stats = {"operaciones": 0}
def mostrar_stats():
    print(f"operaciones basicas hasta ahora: {stats["operaciones"]}")
timer = TimerPeriodico(2.0, mostrar_stats)
timer.iniciar()
print("Simulando trabajo...")
print("Ctrl+C para terminar")
try:
    for i in range(20):
        stats["operaciones"] +=1
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    timer.detener()
    print(f"\ntotal de operaciones: {stats["operaciones"]}")