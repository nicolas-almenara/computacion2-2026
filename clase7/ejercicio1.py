#ejemplo a adaptar a multiprocessing
# import os
#print(f"Antes del fork, soy el proceso {os.getpid()}")
#pid = os.fork()
#if pid == 0:
    # Este código lo ejecuta el HIJO
    #print(f"Soy el hijo, mi PID es {os.getpid()}, mi padre es {os.getppid()}")
#else:
    # Este código lo ejecuta el PADRE
    #print(f"Soy el padre (PID {os.getpid()}), creé al hijo con PID {pid}")
#print(f"Este mensaje lo imprimen AMBOS procesos (PID {os.getpid()})")
import multiprocessing
import os
def informacion():
    print(f"Soy el hijo, mi PID es {os.getpid()}, mi padre es {os.getppid()}")
if __name__ == "__main__":
    p = multiprocessing.Process(target=informacion, args=())
    p.start()
    p.join()
    print(f"Soy el padre (PID {os.getpid()}), creé al hijo con PID {p.pid}")

