import argparse
import sys
from pathlib import Path
parser = argparse.ArgumentParser(description="Mini grep en Python")
parser.add_argument("patron", help="Patrón a buscar")
parser.add_argument("archivos", nargs="*", help="Archivos donde buscar")
parser.add_argument(
    "-i", "--ignore-case",
    action="store_true",
    help="Ignora mayúsculas y minúsculas"
)
parser.add_argument(
    "-n", "--line-number",
    action="store_true",
    help="Mostrar número de línea"
)
parser.add_argument(
    "-c", "--count",
    action="store_true",
    help="Solo mostrar conteo de coincidencias"
)
parser.add_argument(
    "-v", "--invert",
    action="store_true",
    help="Mostrar líneas que NO coinciden"
)
args = parser.parse_args()
def coincide(linea, patron, ignore_case=False):
    if ignore_case:
        linea = linea.lower()
        patron = patron.lower()
    return patron in linea
def procesar_lineas(lineas, patron, mostrar_numero=False, invertir=False):
    resultados = []
    cantidad = 0
    for numero, linea in enumerate(lineas, start=1):
        linea = linea.rstrip("\n")
        hay_coincidencia = coincide(linea, patron, args.ignore_case)
        if invertir:
            hay_coincidencia = not hay_coincidencia
        if hay_coincidencia:
            cantidad += 1
            if mostrar_numero:
                resultados.append(f"{numero}:{linea}")
            else:
                resultados.append(linea)
    return resultados, cantidad
def procesar_archivo(nombre_archivo, patron, multiples_archivos=False):
    ruta = Path(nombre_archivo)
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            lineas = archivo.readlines()
    except FileNotFoundError:
        print(f"Error: no existe el archivo {nombre_archivo}", file=sys.stderr)
        return 0
    except OSError:
        print(f"Error: no se pudo leer el archivo {nombre_archivo}", file=sys.stderr)
        return 0
    mostrar_numero = args.line_number or multiples_archivos
    resultados, cantidad = procesar_lineas(
        lineas,
        patron,
        mostrar_numero=mostrar_numero,
        invertir=args.invert
    )
    if args.count:
        print(f"{nombre_archivo}: {cantidad} coincidencias")
    else:
        for resultado in resultados:
            print(f"{nombre_archivo}:{resultado}")
    return cantidad
def procesar_stdin(patron):
    lineas = sys.stdin.readlines()
    resultados, cantidad = procesar_lineas(
        lineas,
        patron,
        mostrar_numero=args.line_number,
        invertir=args.invert
    )
    if args.count:
        print(cantidad)
    else:
        for resultado in resultados:
            print(resultado)
    return cantidad
if args.archivos:
    total = 0
    multiples_archivos = len(args.archivos) > 1
    for archivo in args.archivos:
        total += procesar_archivo(archivo, args.patron, multiples_archivos)
    if args.count and multiples_archivos:
        print(f"Total: {total} coincidencias")
else:
    if not sys.stdin.isatty():
        procesar_stdin(args.patron)
    else:
        print("Error: debés indicar archivos o pasar datos por stdin", file=sys.stderr)
        sys.exit(1)

