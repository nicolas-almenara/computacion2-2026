"""
sistema.py — Analizador de la vista Sistema global.

Agrega stats de todo el sistema: CPU global (delta de jiffies de /proc/stat),
memoria de /proc/meminfo, load average, uptime, conteo de procesos por estado,
threads totales, zombies, y top 3 por CPU y por RSS.
"""
import time

from base import AnalizadorBase
import procfs


class AnalizadorSistema(AnalizadorBase):
    clave = "sistema"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prev_cpu = None          # lista de jiffies de la lectura anterior
        self._prev_proc = {}           # {pid: jiffies} para top por CPU
        self._prev_ts = None

    def recolectar(self):
        ahora = time.time()

        # --- CPU global: delta entre lecturas de la línea 'cpu' de /proc/stat ---
        g = procfs.leer_stat_global()
        cpu_pcts = self._delta_cpu_global(g["cpu"])

        # --- Memoria ---
        mem = procfs.leer_meminfo()
        mem_total = mem.get("MemTotal", 0)
        mem_free = mem.get("MemFree", 0)
        mem_avail = mem.get("MemAvailable", 0)
        buffers = mem.get("Buffers", 0)
        cached = mem.get("Cached", 0)
        swap_total = mem.get("SwapTotal", 0)
        swap_free = mem.get("SwapFree", 0)

        # --- Recorrer procesos: conteo por estado, threads, zombies, top ---
        por_estado = {}
        total_threads = 0
        zombies = 0
        proc_cpu = []   # (pid, comando, cpu%)
        proc_rss = []   # (pid, comando, rss_kb)
        nuevos_proc = {}

        for pid in self.pids_a_analizar():
            stat = procfs.leer_stat(pid)
            status = procfs.leer_status(pid)
            if not stat or not status:
                continue

            estado = stat[3] if len(stat) > 3 else "?"
            por_estado[estado] = por_estado.get(estado, 0) + 1
            if estado == "Z":
                zombies += 1

            try:
                total_threads += int(status.get("Threads", "0"))
            except ValueError:
                pass

            comando = procfs.leer_cmdline(pid) or f"[{stat[2]}]"

            # CPU% por proceso (para el top)
            try:
                jiffies = int(stat[14]) + int(stat[15])
            except (IndexError, ValueError):
                jiffies = 0
            nuevos_proc[pid] = jiffies
            if pid in self._prev_proc and self._prev_ts:
                dt = ahora - self._prev_ts
                if dt > 0:
                    cpu = 100.0 * ((jiffies - self._prev_proc[pid]) / procfs.CLK_TCK) / dt
                    proc_cpu.append((pid, comando, round(cpu, 1)))

            rss = _kb(status.get("VmRSS"))
            proc_rss.append((pid, comando, rss))

        self._prev_proc = nuevos_proc
        self._prev_ts = ahora

        # Top 3
        proc_cpu.sort(key=lambda t: t[2], reverse=True)
        proc_rss.sort(key=lambda t: t[2], reverse=True)

        return {
            "cpu": cpu_pcts,   # dict con user/system/idle/iowait %
            "mem_total": mem_total,
            "mem_free": mem_free,
            "mem_avail": mem_avail,
            "mem_usada": mem_total - mem_avail if mem_total else 0,
            "buffers": buffers,
            "cached": cached,
            "swap_total": swap_total,
            "swap_usada": swap_total - swap_free,
            "load": procfs.leer_loadavg(),
            "uptime": procfs.leer_uptime(),
            "btime": g["btime"],
            "num_procesos": sum(por_estado.values()),
            "por_estado": por_estado,
            "total_threads": total_threads,
            "zombies": zombies,
            "top_cpu": proc_cpu[:3],
            "top_rss": proc_rss[:3],
        }

    def _delta_cpu_global(self, actual):
        """
        Calcula % de CPU global comparando dos lecturas de la línea 'cpu'.
        Los índices de la línea cpu son:
        0=user 1=nice 2=system 3=idle 4=iowait 5=irq 6=softirq 7=steal ...
        """
        vacio = {"user": 0.0, "system": 0.0, "idle": 0.0, "iowait": 0.0}
        if not actual:
            return vacio
        if self._prev_cpu is None:
            self._prev_cpu = actual
            return vacio

        deltas = [a - p for a, p in zip(actual, self._prev_cpu)]
        self._prev_cpu = actual
        total = sum(deltas)
        if total <= 0:
            return vacio

        def pct(i):
            return round(100.0 * deltas[i] / total, 1) if i < len(deltas) else 0.0

        return {
            "user": pct(0) + pct(1),   # user + nice
            "system": pct(2),
            "idle": pct(3),
            "iowait": pct(4),
        }


def _kb(valor):
    if not valor:
        return 0
    try:
        return int(valor.split()[0])
    except (ValueError, IndexError):
        return 0
