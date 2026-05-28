import multiprocessing
def productor(q):
    for i in range(10):
        q.put(i)
    q.put(None)
def consumidor(q):
    while True:
        item = q.get()
        if item is None:
            break
        print(f"Consumió: {item}")
if __name__ == "__main__":
    q = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=productor, args=(q,))
    p2 = multiprocessing.Process(target=consumidor, args=(q,))
    p1.start()
    p2.start()
    p1.join()
    p2.join()

