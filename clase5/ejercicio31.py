import os
import signal
import time
pid = os.fork()
if pid == 0:
    contador = 0
    def handlerSIGUSR1(sig, frame):
        global contador
        print("se recibio la señal SIGUSR1")
        contador += 1
    def handlerSIGUSR2(sig, frame):
        global contador
        print("se recibio la señal SIGUSR2")
        print(contador)
    signal.signal(signal.SIGUSR1, handlerSIGUSR1)
    signal.signal(signal.SIGUSR2, handlerSIGUSR2)
    print(f"hijo PID={os.getpid()}, esperando señales...")
    while True:
        signal.pause()
else:
    time.sleep(0.5)
    print("Padre enviando 3 SIGUSR1")
    for _ in range(3):
        os.kill(pid, signal.SIGUSR1)
        time.sleep(0.3)
    os.kill(pid, signal.SIGUSR2)
    time.sleep(0.3)
    for _ in range(2):
        os.kill(pid, signal.SIGUSR1)
        time.sleep(0.3)
    os.kill(pid, signal.SIGUSR2)
    time.sleep(0.3)
    os.kill(pid, signal.SIGTERM)
    os.wait()
