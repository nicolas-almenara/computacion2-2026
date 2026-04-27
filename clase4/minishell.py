import os

def cmd_cd(args):
    if not args:
        destino = os.environ.get("HOME", "/")
    else:
        destino = args[0]
    try:
        os.chdir(destino)
    except OSError as e:
        print(f"cd: {e}")
def parsear_linea(linea):
    partes = linea.split()
    comando = linea[0]
    args = []
    archivo_salida = None
    archivo_entrada = None
    i = 1
    while i < len(partes):
        if partes[i] == ">":
            archivo_salida = partes[i+1]
            i += 2
        elif partes[i] == "<":
            archivo_entrada = partes[i+1]
            i += 2
        else:
            args.append(partes[i])
            i += 1
    return comando, args, archivo_salida, archivo_entrada
def ejecutar(comando, args, archivo_salida=None, archivo_entrada=None):
    pid = os.fork()
    if pid == 0:
        if archivo_salida:
            fd = os.open(archivo_salida, os.O_CREAT | os.O_WRONLY | os. O_TRUNC, 0o644)
            os.dup2(fd, 1)
            os.close(fd)
        if archivo_entrada:
            fd = os.open(archivo_entrada, os.O_RDONLY)
            os.dup2(fd, 0)
        try:
            os.execvp(comando, [comando] + args)
        except OSError as e:
            print(f"minish: {comando}: {e}")
            os._exit(127)
        else:
            _, status = os.wait()
            codigo = os.WEXITSTATUS(status)
            if codigo != 0:
                print(f"[codigo: {codigo}]")
def main():
    internos = {"cd": cmd_cd}
    while True:
        cwd = os.getcwd()
        try:
            linea = input(f"minish:{cwd}$ ")
        except EOFError:
            print("\nChau!")
            break
        if not linea.strip():
            continue
        if linea.strip() == "exit":
            break
        comando, args, salida, entrada = parsear_linea(linea)
        if comando in internos:
            internos[comando](args)
        else:
            ejecutar(comando, args, salida, entrada)



if __name__ == "__main__":
    main()