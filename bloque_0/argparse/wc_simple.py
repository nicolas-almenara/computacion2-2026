import sys
if len(sys.argv)<2:
    print("Error: Debe especificar un archivo")
    sys.exit()
nombre_archivo = sys.argv[1]
try:
    with open(sys.argv[1], "r") as f:
        contador = 0
        for lines in f:
            contador = contador + 1
        print(f"{contador} lineas")  
except:
    print(f"Error: No se puede leer '{nombre_archivo}'")
