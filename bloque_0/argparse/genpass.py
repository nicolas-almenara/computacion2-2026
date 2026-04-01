import argparse
import random
import string
parser = argparse.ArgumentParser(description="Generador de contraseñas")
parser.add_argument(
    "-n", "--length",
    type=int,
    default=12,
    help="Largo de la contraseña"
)
parser.add_argument(
    "--no-symbols",
    action="store_true",
    help="Excluir símbolos"
)
parser.add_argument(
    "--no-numbers",
    action="store_true",
    help="Excluir números"
)
parser.add_argument(
    "--count",
    type=int,
    default=1,
    help="Cantidad de contraseñas a generar"
)
args = parser.parse_args()
caracteres = string.ascii_letters  # a-zA-Z
if not args.no_numbers:
    caracteres += string.digits  # 0-9
if not args.no_symbols:
    caracteres += string.punctuation  # !@#$...
for _ in range(args.count):
    password = "".join(random.choice(caracteres) for _ in range(args.length))
    print(password)