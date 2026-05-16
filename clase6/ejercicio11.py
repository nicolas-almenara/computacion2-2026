import mmap
with open("/tmp/mmap_test.txt", "wb") as f:
    f.write(b"Linea 1: Hola mundo\n")
    f.write(b"Linea 2: Computacion II\n")
    f.write(b"Linea 3: mmap es genial\n")
with open("/tmp/mmap_test.txt","r+b") as f:
    mm=mmap.mmap(f.fileno(), 0)
    print("contenido del archivo")
    print(mm[:].decode())
    mm.seek(0)
    while True:
        linea = mm.readline()
        if not linea:
            break
        print(f"{linea.decode().strip()}")
    pos = mm[:].find(b"mmap")
    print(f"posicion de mmap en el archivo: {pos}")
    mm.seek(pos)
    mm.write(b"MMAP")
    print("despues de modificar")
    print(mm[:].decode())
    mm.close()


