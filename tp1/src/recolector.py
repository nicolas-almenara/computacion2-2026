"""
recolector.py — Componente recolector central.

Corre en su propio proceso (igual que los analizadores). Su tarea es la
"fuente única de verdad" de qué procesos existen: lista los PIDs vivos
leyendo /proc y los publica en el snapshot bajo la clave "_pids".

Los analizadores consumen esa lista en vez de listar /proc cada uno por su
cuenta. Esto centraliza el "qué procesos hay" en un solo lugar: si mañana
se quiere filtrar procesos globalmente (por ejemplo, ignorar kernel threads
o procesos de otro usuario), se hace acá y todos los analizadores lo heredan.

Hereda de AnalizadorBase para reutilizar el mismo loop (recolectar → escribir
snapshot → dormir chequeando el Event de shutdown).
"""
from base import AnalizadorBase
import procfs


class Recolector(AnalizadorBase):
    clave = "_pids"

    def recolectar(self):
        # La lista maestra de PIDs vivos, ordenada para estabilidad visual.
        return sorted(procfs.listar_pids())
