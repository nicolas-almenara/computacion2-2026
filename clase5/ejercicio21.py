import signal
import time
contadorctrlc = 0
def handler_sigint(sig, frame):
    global contadorctrlc
    contadorctrlc += 1
    print(f"\n¡ctrl+c detectado! (vez {contadorctrlc})")
    if contadorctrlc >=3:
        print(f"ok,ok me voy")
        raise SystemExit(0)
    else:
        print(f"quedan {3-contadorctrlc} para salir")
signal.signal(signal.SIGINT, handler_sigint)
print("presiona ctrl+c tres veces para salir")
while True:
    print(".", end="", flush=True)
    time.sleep(0.5)

