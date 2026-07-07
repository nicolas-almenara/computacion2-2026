"""
resumen.py — Analizador de la vista Resumen.

Extrae por proceso: PID, PPID, usuario, estado, CPU%, RSS, nro de threads
y comando. El CPU% se calcula como delta de jiffies (utime+stime) entre
dos lecturas consecutivas, dividido por el tiempo real transcurrido.
"""
import time

from base import AnalizadorBase
import procfs


class AnalizadorResumen(AnalizadorBase):
    clave = "resumen"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Guardamos el estado anterior para calcular deltas de CPU:
        # {pid: (jiffies_totales, timestamp)}
        self._prev = {}

    def recolectar(self):
        ahora = time.time()
        procesos = {}
        nuevos_prev = {}

        for pid in self.pids_a_analizar():
            stat = procfs.leer_stat(pid)
            status = procfs.leer_status(pid)
            if not stat or not status:
                continue

            # utime (campo 14) + stime (campo 15) en jiffies
            try:
                utime = int(stat[14])
                stime = int(stat[15])
            except (IndexError, ValueError):
                continue
            jiffies = utime + stime
            nuevos_prev[pid] = (jiffies, ahora)

            # CPU%: comparar contra la lectura anterior de este mismo PID
            cpu_pct = 0.0
            if pid in self._prev:
                prev_jiffies, prev_ts = self._prev[pid]
                dt = ahora - prev_ts
                if dt > 0:
                    delta_jiffies = jiffies - prev_jiffies
                    cpu_pct = 100.0 * (delta_jiffies / procfs.CLK_TCK) / dt

            # Uid/Gid en status vienen como "real efectivo saved fs"; tomamos el real.
            uid = status.get("Uid", "0").split()[0] if status.get("Uid") else "0"
            gid = status.get("Gid", "0").split()[0] if status.get("Gid") else "0"

            procesos[pid] = {
                "pid": pid,
                "ppid": status.get("PPid", "?"),
                "usuario": procfs.nombre_usuario(uid),
                "uid": uid,
                "gid": gid,
                "estado": stat[3] if len(stat) > 3 else "?",
                "cpu": round(cpu_pct, 1),
                "rss_kb": _vm_kb(status.get("VmRSS")),
                "threads": status.get("Threads", "?"),
                "comando": procfs.leer_cmdline(pid) or f"[{stat[2]}]",
            }

        self._prev = nuevos_prev
        return procesos


def _vm_kb(valor):
    """Extrae el número de un campo tipo 'VmRSS: 1234 kB'."""
    if not valor:
        return 0
    try:
        return int(valor.split()[0])
    except (ValueError, IndexError):
        return 0
