"""
threads.py — Analizador de la vista Threads.

Por proceso lista sus threads (LWPs, visibles en /proc/<pid>/task/<tid>).
De cada thread saca estado, CPU% (delta de jiffies), nombre y context switches.
"""
import time

from base import AnalizadorBase
import procfs


class AnalizadorThreads(AnalizadorBase):
    clave = "threads"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Delta de CPU por thread: {(pid, tid): (jiffies, ts)}
        self._prev = {}

    def recolectar(self):
        ahora = time.time()
        procesos = {}
        nuevos_prev = {}

        for pid in self.pids_a_analizar():
            tids = procfs.listar_threads(pid)
            if not tids:
                continue

            threads_info = []
            for tid in tids:
                stat = procfs.leer_stat(pid, tid)
                if not stat:
                    continue

                try:
                    jiffies = int(stat[14]) + int(stat[15])
                except (IndexError, ValueError):
                    jiffies = 0
                nuevos_prev[(pid, tid)] = (jiffies, ahora)

                cpu_pct = 0.0
                if (pid, tid) in self._prev:
                    pj, pt = self._prev[(pid, tid)]
                    dt = ahora - pt
                    if dt > 0:
                        cpu_pct = 100.0 * ((jiffies - pj) / procfs.CLK_TCK) / dt

                # Context switches del thread (voluntary + nonvoluntary)
                st = procfs.leer_status(pid, tid)
                vol = st.get("voluntary_ctxt_switches", "0")
                nonvol = st.get("nonvoluntary_ctxt_switches", "0")

                threads_info.append({
                    "tid": tid,
                    "nombre": procfs.leer_comm(pid, tid),
                    "estado": stat[3] if len(stat) > 3 else "?",
                    "cpu": round(cpu_pct, 1),
                    "ctx_vol": vol,
                    "ctx_nonvol": nonvol,
                })

            if threads_info:
                threads_info.sort(key=lambda t: t["tid"])
                procesos[pid] = {
                    "pid": pid,
                    "comando": procfs.leer_cmdline(pid) or f"pid {pid}",
                    "num_threads": len(threads_info),
                    "threads": threads_info,
                }

        self._prev = nuevos_prev
        return procesos
