import threading
import time
def task():
    while True:
        print("Trabajando...")
        time.sleep(1)
t2 = threading.Thread(target=task, daemon=True)
t2.start()
time.sleep(3)
print("murio el thread main, termina automaticamente")