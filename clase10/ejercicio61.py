import threading
import time
def version_corregida():
    lock_a = threading.Lock()
    lock_b = threading.Lock()
    def thread_ordenado(nombre):
        with lock_a:
            print(f"{nombre} tiene lock a")
            with lock_b:
                print(f"{nombre} tiene a y b")
                time.sleep(0.1)
    t1 = threading.Thread(target=thread_ordenado, args=("Thread 1",))
    t2 = threading.Thread(target=thread_ordenado, args=("Thread 2",))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("terminado sin deadlock(interbloqueo)")
version_corregida()