"""
memoria.py — Analizador de la vista Memoria.

Por proceso extrae los campos Vm* de status, los page faults de stat,
y los segmentos agrupados de maps (text/data/heap/stack/shared).
"""
from base import AnalizadorBase
import procfs


class AnalizadorMemoria(AnalizadorBase):
    clave = "memoria"

    def recolectar(self):
        procesos = {}
        for pid in self.pids_a_analizar():
            status = procfs.leer_status(pid)
            stat = procfs.leer_stat(pid)
            if not status or not stat:
                continue

            # Page faults: campos 10-13 de stat.
            # minflt=10, cminflt=11, majflt=12, cmajflt=13
            try:
                minflt = int(stat[10])
                majflt = int(stat[12])
            except (IndexError, ValueError):
                minflt = majflt = 0

            procesos[pid] = {
                "pid": pid,
                "comando": procfs.leer_cmdline(pid) or f"[{stat[2]}]",
                "vm_size": _kb(status.get("VmSize")),
                "vm_rss": _kb(status.get("VmRSS")),
                "vm_data": _kb(status.get("VmData")),
                "vm_stk": _kb(status.get("VmStk")),
                "vm_exe": _kb(status.get("VmExe")),
                "vm_lib": _kb(status.get("VmLib")),
                "vm_hwm": _kb(status.get("VmHWM")),
                "vm_swap": _kb(status.get("VmSwap")),
                "minflt": minflt,
                "majflt": majflt,
                "segmentos": procfs.leer_maps_agrupado(pid),
            }
        return procesos


def _kb(valor):
    """Extrae número de un campo 'VmXXX: N kB'."""
    if not valor:
        return 0
    try:
        return int(valor.split()[0])
    except (ValueError, IndexError):
        return 0
