import argparse
from pathlib import Path
parser = argparse.ArgumentParser(description="Lista de archivos de un directorio")
parser.add_argument("directorio", nargs="?", default=".", help="Directorio a listar (por defecto: actual)")
parser.add_argument("-a" "--all", action="store_true", help="Incluye archivos ocultos")
parser.add_argument("--extension", help="Filtra por extensión, por ejemplo: .py")
args = parser.parse_args
ruta = Path(args.directorio)
if not ruta.exists():
    print("Error: el directorio no existe")
    exit(1)
if not ruta.is_dir():
    print("Error: la ruta indicada no es un directorio")
    exit(1)
elementos = sorted(ruta.iterdir(), key=lambda x: x.name)
for elemento in elementos:
    nombre = elemento.name
    if not args.all and nombre.startswith("."):
        continue
    if args.extension and elemento.is_file() and elemento.suffix != args.extension:
        continue
    if args.extension and elemento.is_dir():
        continue
    if elemento.is_dir():
        print(nombre + "/")
    else:
        print(nombre)