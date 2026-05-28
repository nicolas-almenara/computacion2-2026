import multiprocessing
def hijo(conn):
    for i in range(5):
        print(f"mensaje recibido por el hijo: {conn.recv()}")
        conn.send(f"mensaje hijo nro{i}")
    conn.close()
if __name__ == "__main__":
    padre_conn, hijo_conn = multiprocessing.Pipe()
    p = multiprocessing.Process(target=hijo, args=(hijo_conn,))
    p.start()
    for i in range(5):
        padre_conn.send(f"mensaje padre nro{i}")
        print(f"mensaje recibido por el padre: {padre_conn.recv()}")
    p.join()
    