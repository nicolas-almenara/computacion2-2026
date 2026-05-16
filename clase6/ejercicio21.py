import mmap
import struct
import os
ARCHIVO = "/tmp/numeros.bin"
NUM_ELEMENTOS = 10
TAMAÑO = NUM_ELEMENTOS * 4
with open("/tmp/numeros.bin", "wb") as f:
    f.write(b"\x00" * TAMAÑO)
with open("/tmp/numeros.bin", "r+b") as f:
    mm = mmap.mmap(f.fileno(), TAMAÑO)
    for i in range(NUM_ELEMENTOS):
        valor = (i+1)*100
        struct.pack_into("i", mm, i*4, valor)
        print(f"  Posición {i}: {valor}")
    for i in range(NUM_ELEMENTOS):
        valor = struct.unpack_from("i", mm, i*4)[0]
        print(f"  Posición {i}: {valor}")
    struct.pack_into("i", mm, 12, 9999)
    struct.unpack_from("i", mm, 12)[0]
    print(f"\nPosición 3 modificada a: {struct.unpack_from('i', mm, 3 * 4)[0]}")
    mm.close()
os.unlink(ARCHIVO)
