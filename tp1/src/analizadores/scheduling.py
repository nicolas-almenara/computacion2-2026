"""
scheduling.py — Analizador de la vista Scheduling.

Por proceso: nice, priority, política de scheduling, RT priority,
CPU affinity, context switches (vol/nonvol), utime/stime, SID y PGID.
"""
from base import AnalizadorBase
import procfs


class AnalizadorScheduling(AnalizadorBase):
    clave = "scheduling"

    def recolectar(self):
        procesos = {}
        for pid in self.pids_a_analizar():
            stat = procfs.leer_stat(pid)
            status = procfs.leer_status(pid)
            if not stat or not status:
                continue

            # Campos de stat (indexados desde 1, como proc(5)):
            #  6=session(SID), 7=pgrp(PGID), 18=priority, 19=nice,
            #  40=rt_priority, 41=policy, 14=utime, 15=stime
            def campo(n, default="0"):
                try:
                    return stat[n]
                except IndexError:
                    return default

            try:
                policy_num = int(campo(41))
            except ValueError:
                policy_num = 0

            procesos[pid] = {
                "pid": pid,
                "comando": procfs.leer_cmdline(pid) or f"pid {pid}",
                "nice": campo(19),
                "priority": campo(18),
                "policy": procfs.SCHED_POLICIES.get(policy_num, str(policy_num)),
                "rt_priority": campo(40),
                "affinity": status.get("Cpus_allowed_list", "?"),
                "ctx_vol": status.get("voluntary_ctxt_switches", "0"),
                "ctx_nonvol": status.get("nonvoluntary_ctxt_switches", "0"),
                "utime": campo(14),
                "stime": campo(15),
                "sid": campo(6),
                "pgid": campo(7),
            }
        return procesos
