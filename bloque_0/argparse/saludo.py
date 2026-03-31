import sys
if len(sys.argv) < 2:
    print ("Uso: saludo.py <nombre>")
else:
    nombre = " ".join(sys.argv[1:])
    print (f"Hola, {nombre}!")

    




