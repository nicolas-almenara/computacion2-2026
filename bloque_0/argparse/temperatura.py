import argparse
parser = argparse.ArgumentParser(description= "convierte entre grados celsius y fahrenheit")
parser.add_argument("valor", type=float, help="temperatura a convertir")
parser.add_argument("-t","--to", choices = ["celsius", "fahrenheit"], required=True, help = "unidad de destino")
args = parser.parse_args()
if args.to == "fahrenheit":
    resultado = args.valor * 9/5 + 32
    print(f"{args.valor}°C = {resultado}°F")
else:
    resultado = (args.valor - 32) * 5/9
    print(f"{args.valor}°F = {resultado:.2f}°C")