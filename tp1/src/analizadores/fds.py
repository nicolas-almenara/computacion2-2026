"""
fds.py — Analizador de la vista File Descriptors.

Por proceso lista los FDs abiertos con su destino y tipo inferido.
Guarda también un conteo por tipo para el resumen de la lista.
"""
from base import AnalizadorBase
import procfs


class AnalizadorFDs(AnalizadorBase):
    clave = "fds"

    def recolectar(self):
        procesos = {}
        for pid in self.pids_a_analizar():
            fds = procfs.listar_fds(pid)
            if not fds:
                # Puede ser un proceso sin permiso de lectura o ya muerto.
                # Igual lo registramos vacío para que la vista lo muestre.
                continue

            # Conteo por tipo (file, socket, pipe, tty, ...)
            conteo = {}
            for _, _, tipo in fds:
                conteo[tipo] = conteo.get(tipo, 0) + 1

            procesos[pid] = {
                "pid": pid,
                "comando": procfs.leer_cmdline(pid) or f"pid {pid}",
                "total": len(fds),
                "conteo": conteo,
                # Guardamos la lista completa (fd, destino, tipo) para el detalle.
                "lista": [{"fd": fd, "destino": dst, "tipo": tipo}
                          for fd, dst, tipo in fds],
            }
        return procesos
