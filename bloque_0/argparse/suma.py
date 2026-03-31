import sys
suma = 0
for i in sys.argv[1:]:
    suma = float(i)+suma
print(f"suma: {suma}")

