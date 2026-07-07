"""
senales.py — Analizador de la vista Señales.

Lee las máscaras hexadecimales de /proc/<pid>/status (SigBlk, SigIgn,
SigCgt, SigPnd, ShdPnd) y las decodifica a listas de nombres legibles.
"""
from base import AnalizadorBase
import procfs


class AnalizadorSenales(AnalizadorBase):
    clave = "senales"

    def recolectar(self):
        procesos = {}
        for pid in self.pids_a_analizar():
            status = procfs.leer_status(pid)
            if not status:
                continue

            procesos[pid] = {
                "pid": pid,
                "comando": procfs.leer_cmdline(pid) or f"pid {pid}",
                # Cada máscara se decodifica a lista de nombres de señal.
                "bloqueadas": procfs.decodificar_mascara_senales(status.get("SigBlk", "0")),
                "ignoradas": procfs.decodificar_mascara_senales(status.get("SigIgn", "0")),
                "con_handler": procfs.decodificar_mascara_senales(status.get("SigCgt", "0")),
                "pendientes": procfs.decodificar_mascara_senales(status.get("SigPnd", "0")),
                "pendientes_grupo": procfs.decodificar_mascara_senales(status.get("ShdPnd", "0")),
            }
        return procesos
