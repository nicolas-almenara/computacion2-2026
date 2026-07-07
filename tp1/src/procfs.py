"""
procfs.py — Helpers para leer y parsear el filesystem /proc.

Todo el acceso a /proc pasa por acá. Ningún analizador lee /proc
directamente: usan estas funciones. Esto centraliza el parseo y el
manejo de errores (procesos que mueren entre que los listamos y los leemos).
"""
import os
import re

# Clock ticks por segundo (para convertir jiffies a segundos).
# Normalmente 100 en Linux. os.sysconf lo devuelve de forma portable.
try:
    CLK_TCK = os.sysconf("SC_CLK_TCK")
except (ValueError, OSError):
    CLK_TCK = 100

# Tamaño de página en bytes (para convertir páginas a bytes en algunas métricas).
try:
    PAGE_SIZE = os.sysconf("SC_PAGE_SIZE")
except (ValueError, OSError):
    PAGE_SIZE = 4096

PROC = "/proc"

# ---------------------------------------------------------------------------
# Nombres de señales indexados por número de bit (para decodificar máscaras).
# El bit 0 (valor 1) corresponde a la señal 1 (SIGHUP), etc.
# ---------------------------------------------------------------------------
SIGNAL_NAMES = {
    1: "SIGHUP", 2: "SIGINT", 3: "SIGQUIT", 4: "SIGILL", 5: "SIGTRAP",
    6: "SIGABRT", 7: "SIGBUS", 8: "SIGFPE", 9: "SIGKILL", 10: "SIGUSR1",
    11: "SIGSEGV", 12: "SIGUSR2", 13: "SIGPIPE", 14: "SIGALRM", 15: "SIGTERM",
    16: "SIGSTKFLT", 17: "SIGCHLD", 18: "SIGCONT", 19: "SIGSTOP", 20: "SIGTSTP",
    21: "SIGTTIN", 22: "SIGTTOU", 23: "SIGURG", 24: "SIGXCPU", 25: "SIGXFSZ",
    26: "SIGVTALRM", 27: "SIGPROF", 28: "SIGWINCH", 29: "SIGIO", 30: "SIGPWR",
    31: "SIGSYS",
}

# Mapa de política de scheduling (campo 41 de /proc/<pid>/stat).
SCHED_POLICIES = {
    0: "OTHER", 1: "FIFO", 2: "RR", 3: "BATCH", 5: "IDLE", 6: "DEADLINE",
}


def listar_pids():
    """Devuelve la lista de PIDs actuales (carpetas numéricas en /proc)."""
    pids = []
    try:
        for nombre in os.listdir(PROC):
            if nombre.isdigit():
                pids.append(int(nombre))
    except OSError:
        pass
    return pids


def _leer(path):
    """Lee un archivo de /proc devolviendo str, o None si desaparece/no hay permiso."""
    try:
        with open(path, "r") as f:
            return f.read()
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
        return None


def leer_status(pid, tid=None):
    """
    Parsea /proc/<pid>/status (o /proc/<pid>/task/<tid>/status) a un dict.
    Cada línea es "Clave:\tvalor". Devuelve {} si el proceso ya no existe.
    """
    base = f"{PROC}/{pid}"
    if tid is not None:
        base = f"{base}/task/{tid}"
    contenido = _leer(f"{base}/status")
    if contenido is None:
        return {}
    datos = {}
    for linea in contenido.splitlines():
        if ":" in linea:
            clave, _, valor = linea.partition(":")
            datos[clave.strip()] = valor.strip()
    return datos


def leer_stat(pid, tid=None):
    """
    Parsea /proc/<pid>/stat (o el de un thread) a una lista de campos.

    Ojo: el campo 2 (comm) puede tener espacios y paréntesis, así que
    lo aislamos por los paréntesis antes de hacer split del resto.
    Devuelve lista indexable desde 1 (índice 0 es None de relleno) para
    que los números de campo coincidan con los de la man page proc(5).
    """
    base = f"{PROC}/{pid}"
    if tid is not None:
        base = f"{base}/task/{tid}"
    contenido = _leer(f"{base}/stat")
    if contenido is None:
        return None

    # comm está entre paréntesis; puede contener espacios
    abre = contenido.find("(")
    cierra = contenido.rfind(")")
    if abre == -1 or cierra == -1:
        return None

    pid_str = contenido[:abre].strip()
    comm = contenido[abre + 1:cierra]
    resto = contenido[cierra + 1:].split()

    # campo 1 = pid, campo 2 = comm, del 3 en adelante = resto
    campos = [None, pid_str, comm] + resto
    return campos


def leer_cmdline(pid):
    """Comando completo desde /proc/<pid>/cmdline (args separados por NUL)."""
    contenido = _leer(f"{PROC}/{pid}/cmdline")
    if not contenido:
        return ""
    # Los argumentos están separados por bytes NUL
    partes = contenido.split("\x00")
    return " ".join(p for p in partes if p).strip()


def leer_comm(pid, tid=None):
    """Nombre corto del proceso/thread desde comm."""
    base = f"{PROC}/{pid}"
    if tid is not None:
        base = f"{base}/task/{tid}"
    contenido = _leer(f"{base}/comm")
    return contenido.strip() if contenido else ""


def listar_fds(pid):
    """
    Lista los file descriptors abiertos de un proceso.
    Devuelve lista de tuplas (fd_num, destino, tipo).
    """
    ruta = f"{PROC}/{pid}/fd"
    resultado = []
    try:
        fds = os.listdir(ruta)
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
        return resultado
    for fd in fds:
        destino = "?"
        try:
            destino = os.readlink(f"{ruta}/{fd}")
        except OSError:
            pass
        resultado.append((fd, destino, _tipo_fd(destino)))
    # Ordenar numéricamente por descriptor
    resultado.sort(key=lambda t: int(t[0]) if t[0].isdigit() else 0)
    return resultado


def _tipo_fd(destino):
    """Infiere el tipo de un FD a partir del destino del symlink."""
    if destino.startswith("socket:"):
        return "socket"
    if destino.startswith("pipe:"):
        return "pipe"
    if destino.startswith("anon_inode:"):
        return "anon"
    if "/dev/pts/" in destino or destino.startswith("/dev/tty"):
        return "tty"
    if destino.startswith("/dev/null"):
        return "null"
    if destino.startswith("/"):
        return "file"
    return "otro"


def listar_threads(pid):
    """Devuelve la lista de TIDs (threads / LWPs) de un proceso."""
    try:
        return [int(t) for t in os.listdir(f"{PROC}/{pid}/task") if t.isdigit()]
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
        return []


def leer_maps_agrupado(pid):
    """
    Lee /proc/<pid>/maps y agrupa el tamaño total por categoría:
    text (r-x), data (rw-), heap, stack, shared, otros. Devuelve dict {cat: kb}.
    """
    contenido = _leer(f"{PROC}/{pid}/maps")
    grupos = {"text": 0, "data": 0, "heap": 0, "stack": 0, "shared": 0, "otros": 0}
    if not contenido:
        return grupos
    for linea in contenido.splitlines():
        partes = linea.split()
        if len(partes) < 5:
            continue
        rango = partes[0]
        perms = partes[1]
        nombre = partes[-1] if len(partes) >= 6 else ""
        try:
            ini, fin = rango.split("-")
            tam_kb = (int(fin, 16) - int(ini, 16)) // 1024
        except ValueError:
            continue

        if nombre == "[heap]":
            grupos["heap"] += tam_kb
        elif nombre == "[stack]":
            grupos["stack"] += tam_kb
        elif len(perms) >= 4 and perms[3] == "s":
            grupos["shared"] += tam_kb
        elif "x" in perms:
            grupos["text"] += tam_kb
        elif "w" in perms:
            grupos["data"] += tam_kb
        else:
            grupos["otros"] += tam_kb
    return grupos


def decodificar_mascara_senales(hex_str):
    """
    Convierte una máscara hexadecimal de /proc/<pid>/status (SigBlk, SigCgt...)
    a una lista ordenada de nombres de señal.
    Cada bit i (0-indexado) representa la señal i+1.
    """
    if not hex_str:
        return []
    try:
        valor = int(hex_str, 16)
    except ValueError:
        return []
    nombres = []
    for bit in range(64):
        if valor & (1 << bit):
            num = bit + 1
            nombres.append(SIGNAL_NAMES.get(num, f"SIG{num}"))
    return nombres


# ---------------------------------------------------------------------------
# Stats globales del sistema
# ---------------------------------------------------------------------------
def leer_stat_global():
    """
    Lee /proc/stat. Devuelve dict con la línea 'cpu' (lista de jiffies) y btime.
    """
    contenido = _leer(f"{PROC}/stat")
    resultado = {"cpu": None, "btime": None}
    if not contenido:
        return resultado
    for linea in contenido.splitlines():
        if linea.startswith("cpu "):
            resultado["cpu"] = [int(x) for x in linea.split()[1:]]
        elif linea.startswith("btime "):
            resultado["btime"] = int(linea.split()[1])
    return resultado


def leer_meminfo():
    """Lee /proc/meminfo devolviendo dict {clave: kb}."""
    contenido = _leer(f"{PROC}/meminfo")
    datos = {}
    if not contenido:
        return datos
    for linea in contenido.splitlines():
        m = re.match(r"(\w+):\s+(\d+)", linea)
        if m:
            datos[m.group(1)] = int(m.group(2))
    return datos


def leer_loadavg():
    """Lee /proc/loadavg devolviendo (1min, 5min, 15min)."""
    contenido = _leer(f"{PROC}/loadavg")
    if not contenido:
        return (0.0, 0.0, 0.0)
    partes = contenido.split()
    try:
        return (float(partes[0]), float(partes[1]), float(partes[2]))
    except (ValueError, IndexError):
        return (0.0, 0.0, 0.0)


def leer_uptime():
    """Lee /proc/uptime devolviendo segundos de uptime (float)."""
    contenido = _leer(f"{PROC}/uptime")
    if not contenido:
        return 0.0
    try:
        return float(contenido.split()[0])
    except (ValueError, IndexError):
        return 0.0


def nombre_usuario(uid):
    """Resuelve un UID a nombre de usuario leyendo /etc/passwd (sin pwd para ser explícitos)."""
    try:
        import pwd
        return pwd.getpwuid(int(uid)).pw_name
    except (KeyError, ValueError, OSError):
        return str(uid)
