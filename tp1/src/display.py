"""
display.py — Interfaz de texto (TUI) con curses.

Corre en el proceso principal. Lee el snapshot compartido (que los
analizadores mantienen actualizado) y lo renderiza según la vista activa.
Maneja el teclado para navegación, filtros, cambio de vista e intervalos,
y procesa las señales que llegan por el self-pipe.

Nota: curses maneja su propio input, pero para poder atender el self-pipe
de señales usamos timeout no bloqueante en getch() y chequeamos el pipe
en cada vuelta del loop.
"""
import curses
import time
import json
import select

import senales as sig_mod


# Definición de las 7 vistas: clave interna, título, teclas que la activan.
VISTAS = [
    ("resumen",    "Resumen",     ["1", "r"]),
    ("memoria",    "Memoria",     ["2", "m"]),
    ("fds",        "File Descriptors", ["3", "f"]),
    ("threads",    "Threads",     ["4", "t"]),
    ("senales",    "Señales",     ["5", "s"]),
    ("scheduling", "Scheduling",  ["6", "p"]),
    ("sistema",    "Sistema",     ["7", "g"]),
]

# Mapa tecla -> índice de vista (se arma una vez).
_TECLA_A_VISTA = {}
for _i, (_clave, _titulo, _teclas) in enumerate(VISTAS):
    for _t in _teclas:
        _TECLA_A_VISTA[_t] = _i

# Intervalo mínimo permitido por vista (segundos), según la tabla del enunciado.
# El usuario no puede bajar de acá con la tecla '+'. Evita, por ejemplo, refrescar
# las señales (casi estáticas) más rápido de lo razonable.
MIN_INTERVALO = {
    "resumen": 0.5,
    "memoria": 1.0,
    "fds": 2.0,
    "threads": 0.5,
    "senales": 5.0,
    "scheduling": 5.0,
    "sistema": 1.0,
}


class Display:
    def __init__(self, snapshot, intervalos, detener_event, control,
                 contador_lecturas=None):
        """
        snapshot          : Manager.dict global
        intervalos        : dict {clave_vista: multiprocessing.Value} para ajustar en caliente
        detener_event     : Event para señalizar shutdown a los analizadores
        control           : Manager.dict con estado compartido (verbose, etc.)
        contador_lecturas : multiprocessing.Value('i') con el total de lecturas de /proc
                            (lo escriben los analizadores; el display solo lo lee y muestra)
        """
        self.snapshot = snapshot
        self.intervalos = intervalos
        self.detener = detener_event
        self.control = control
        self.contador_lecturas = contador_lecturas

        self.vista_idx = 0          # vista activa (índice en VISTAS)
        self.seleccion = 0          # índice del proceso seleccionado en la lista
        self.scroll = 0             # offset de scroll de la lista
        self.pin_pid = None         # PID fijado (no cambia con el orden)
        self.filtro_cmd = ""        # filtro por comando
        self.filtro_usuario = ""    # filtro por usuario
        self.orden = "cpu"          # cpu / rss / pid
        self.mensaje = ""           # línea de estado temporal (feedback de señales)
        self.mensaje_hasta = 0
        self.mostrar_ayuda = False

    # -----------------------------------------------------------------
    # Punto de entrada: curses.wrapper llama a esto con la pantalla lista.
    # -----------------------------------------------------------------
    def correr(self, stdscr):
        curses.curs_set(0)              # ocultar cursor
        stdscr.nodelay(True)            # getch no bloquea
        stdscr.timeout(100)             # refresco cada 100ms como máximo
        self._init_colores()

        fd_senales = sig_mod.fd_lectura()

        while not self.detener.is_set():
            # 1) Atender señales pendientes del self-pipe (no bloqueante)
            r, _, _ = select.select([fd_senales], [], [], 0)
            if r:
                for nombre in sig_mod.leer_senales():
                    self._procesar_senal(nombre)
                    if self.detener.is_set():
                        break

            if self.detener.is_set():
                break

            # 2) Dibujar la pantalla
            try:
                self._dibujar(stdscr)
            except curses.error:
                # Terminal muy chica o redimensión en curso: ignorar este frame.
                pass

            # 3) Leer teclado
            try:
                ch = stdscr.getch()
            except curses.error:
                ch = -1
            if ch != -1:
                self._procesar_tecla(ch, stdscr)

    # -----------------------------------------------------------------
    # Colores
    # -----------------------------------------------------------------
    def _init_colores(self):
        if not curses.has_colors():
            return
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)     # cabeceras
        curses.init_pair(2, curses.COLOR_GREEN, -1)    # ok / running
        curses.init_pair(3, curses.COLOR_YELLOW, -1)   # advertencia
        curses.init_pair(4, curses.COLOR_RED, -1)      # zombie / alto
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_CYAN)  # selección
        curses.init_pair(6, curses.COLOR_MAGENTA, -1)  # pin

    # -----------------------------------------------------------------
    # Procesamiento de señales (llega desde el self-pipe, contexto seguro)
    # -----------------------------------------------------------------
    def _procesar_senal(self, nombre):
        if nombre in ("SIGINT", "SIGTERM"):
            # Shutdown limpio: señalizamos a todos los analizadores.
            self.detener.set()
        elif nombre == "SIGHUP":
            self._recargar_config()
            self._flash("Config recargada (SIGHUP)")
        elif nombre == "SIGUSR1":
            self._dump_snapshot()
        elif nombre == "SIGUSR2":
            actual = self.control.get("verbose", False)
            self.control["verbose"] = not actual
            self._flash(f"Verbose {'ON' if not actual else 'OFF'} (SIGUSR2)")
        elif nombre == "SIGWINCH":
            # Terminal redimensionada. NO usar endwin() acá (cierra curses y
            # rompe el loop). Basta con avisarle a curses que recalcule sus
            # dimensiones; el próximo _dibujar() ya lee getmaxyx() fresco y
            # repinta todo desde cero.
            try:
                curses.update_lines_cols()
            except (curses.error, AttributeError):
                pass
            self._flash("Pantalla redimensionada")

    def _recargar_config(self):
        """Relee config.json y aplica intervalos por defecto."""
        try:
            with open("config.json") as f:
                cfg = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return
        for clave, val in cfg.get("intervalos", {}).items():
            if clave in self.intervalos:
                try:
                    self.intervalos[clave].value = float(val)
                except (ValueError, TypeError):
                    pass
        self.filtro_cmd = cfg.get("filtro_cmd", self.filtro_cmd)
        self.filtro_usuario = cfg.get("filtro_usuario", self.filtro_usuario)

    def _dump_snapshot(self):
        """Vuelca el snapshot completo a dump_<timestamp>.json."""
        ts = time.strftime("%Y%m%d_%H%M%S")
        nombre = f"dump_{ts}.json"
        try:
            # snapshot es un Manager.dict; lo convertimos a dict normal.
            data = {k: dict(v) if hasattr(v, "keys") else v
                    for k, v in dict(self.snapshot).items()}
            with open(nombre, "w") as f:
                json.dump(data, f, indent=2, default=str)
            self._flash(f"Dump guardado: {nombre}")
        except Exception as e:
            self._flash(f"Error en dump: {e}")

    def _flash(self, texto, segundos=3):
        """Muestra un mensaje temporal en la barra de estado."""
        self.mensaje = texto
        self.mensaje_hasta = time.time() + segundos

    # -----------------------------------------------------------------
    # Teclado
    # -----------------------------------------------------------------
    def _procesar_tecla(self, ch, stdscr):
        try:
            tecla = chr(ch)
        except ValueError:
            tecla = ""

        if self.mostrar_ayuda:
            # Cualquier tecla cierra la ayuda.
            self.mostrar_ayuda = False
            return

        if tecla in ("q", "Q"):
            self.detener.set()
            return
        if tecla in ("h", "?"):
            self.mostrar_ayuda = True
            return
        if tecla in _TECLA_A_VISTA:
            self.vista_idx = _TECLA_A_VISTA[tecla]
            self.seleccion = 0
            self.scroll = 0
            return
        if ch == curses.KEY_UP:
            self.seleccion = max(0, self.seleccion - 1)
            return
        if ch == curses.KEY_DOWN:
            self.seleccion += 1
            return
        if ch in (curses.KEY_ENTER, 10, 13):
            # Pin del proceso seleccionado
            pids = self._pids_ordenados()
            if 0 <= self.seleccion < len(pids):
                nuevo = pids[self.seleccion]
                self.pin_pid = None if self.pin_pid == nuevo else nuevo
            return
        if tecla == "c":
            # Toggle de ordenamiento
            orden = {"cpu": "rss", "rss": "pid", "pid": "cpu"}
            self.orden = orden[self.orden]
            return
        if tecla in ("+", "="):
            self._ajustar_intervalo(-0.5)
            return
        if tecla in ("-", "_"):
            self._ajustar_intervalo(+0.5)
            return
        if tecla == "/":
            self.filtro_cmd = self._prompt(stdscr, "Filtrar comando: ")
            return
        if tecla == "u":
            self.filtro_usuario = self._prompt(stdscr, "Filtrar usuario: ")
            return

    def _ajustar_intervalo(self, delta):
        """Ajusta el intervalo de la vista activa, respetando su mínimo propio."""
        clave = VISTAS[self.vista_idx][0]
        if clave in self.intervalos:
            val = self.intervalos[clave]
            minimo = MIN_INTERVALO.get(clave, 0.5)
            nuevo = max(minimo, val.value + delta)
            val.value = nuevo
            if nuevo == minimo and delta < 0:
                self._flash(f"Intervalo {clave}: {nuevo:.1f}s (mínimo)")
            else:
                self._flash(f"Intervalo {clave}: {nuevo:.1f}s")

    def _prompt(self, stdscr, etiqueta):
        """Pide una línea de texto al usuario (bloqueante, con echo)."""
        curses.curs_set(1)
        stdscr.nodelay(False)
        curses.echo()
        h, w = stdscr.getmaxyx()
        stdscr.move(h - 1, 0)
        stdscr.clrtoeol()
        stdscr.addstr(h - 1, 0, etiqueta)
        try:
            texto = stdscr.getstr(h - 1, len(etiqueta), 60).decode("utf-8", "ignore")
        except curses.error:
            texto = ""
        curses.noecho()
        curses.curs_set(0)
        stdscr.nodelay(True)
        return texto.strip()

    # -----------------------------------------------------------------
    # Selección y orden de la lista de procesos
    # -----------------------------------------------------------------
    def _entrada_resumen(self):
        """Devuelve el dict de datos del analizador de resumen (o {})."""
        entrada = self.snapshot.get("resumen")
        if not entrada:
            return {}
        return entrada.get("datos", {})

    def _pids_ordenados(self):
        """
        Lista de PIDs filtrados y ordenados según los criterios activos.
        Se basa en la vista Resumen para tener CPU/RSS/usuario de cada proceso.
        """
        datos = self._entrada_resumen()
        procesos = list(datos.values())

        # Filtros
        if self.filtro_cmd:
            f = self.filtro_cmd.lower()
            procesos = [p for p in procesos if f in p.get("comando", "").lower()]
        if self.filtro_usuario:
            f = self.filtro_usuario.lower()
            procesos = [p for p in procesos if f in p.get("usuario", "").lower()]

        # Orden
        if self.orden == "cpu":
            procesos.sort(key=lambda p: p.get("cpu", 0), reverse=True)
        elif self.orden == "rss":
            procesos.sort(key=lambda p: p.get("rss_kb", 0), reverse=True)
        else:
            procesos.sort(key=lambda p: p.get("pid", 0))

        return [p["pid"] for p in procesos]

    # -----------------------------------------------------------------
    # Dibujo
    # -----------------------------------------------------------------
    def _dibujar(self, stdscr):
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        if h < 6 or w < 40:
            stdscr.addstr(0, 0, "Terminal muy chica")
            stdscr.refresh()
            return

        self._dibujar_barra_vistas(stdscr, w)
        # Zona superior: lista de procesos (mitad de la pantalla)
        alto_lista = max(3, (h - 4) // 2)
        self._dibujar_lista(stdscr, 1, alto_lista, w)
        # Zona inferior: panel de detalle según vista activa
        inicio_detalle = 1 + alto_lista + 1
        self._dibujar_detalle(stdscr, inicio_detalle, h - inicio_detalle - 1, w)
        self._dibujar_barra_estado(stdscr, h, w)

        if self.mostrar_ayuda:
            self._dibujar_ayuda(stdscr, h, w)

        stdscr.refresh()

    def _dibujar_barra_vistas(self, stdscr, w):
        x = 0
        stdscr.addstr(0, 0, " " * (w - 1), curses.color_pair(1))
        for i, (clave, titulo, teclas) in enumerate(VISTAS):
            etiqueta = f" {i+1}:{titulo} "
            attr = curses.color_pair(5) if i == self.vista_idx else curses.color_pair(1)
            if x + len(etiqueta) < w:
                stdscr.addstr(0, x, etiqueta, attr | curses.A_BOLD)
                x += len(etiqueta)

    def _dibujar_lista(self, stdscr, y0, alto, w):
        pids = self._pids_ordenados()
        datos = self._entrada_resumen()

        # Ajustar selección y scroll a los límites actuales
        if pids:
            self.seleccion = min(self.seleccion, len(pids) - 1)
        else:
            self.seleccion = 0
        if self.seleccion < self.scroll:
            self.scroll = self.seleccion
        elif self.seleccion >= self.scroll + (alto - 1):
            self.scroll = self.seleccion - (alto - 2)
        self.scroll = max(0, self.scroll)

        # Cabecera de columnas
        cab = f"{'PID':>7} {'USUARIO':<10} {'ST':<2} {'CPU%':>6} {'RSS(MB)':>9} {'THR':>4} COMANDO"
        stdscr.addstr(y0, 0, cab[:w - 1], curses.color_pair(1) | curses.A_BOLD)

        visibles = pids[self.scroll:self.scroll + (alto - 1)]
        for i, pid in enumerate(visibles):
            idx_real = self.scroll + i
            p = datos.get(pid, {})
            estado = p.get("estado", "?")
            rss_mb = p.get("rss_kb", 0) / 1024
            marca = "*" if pid == self.pin_pid else " "
            linea = (f"{marca}{pid:>6} {p.get('usuario','?')[:10]:<10} "
                     f"{estado:<2} {p.get('cpu',0):>6.1f} {rss_mb:>9.1f} "
                     f"{str(p.get('threads','?')):>4} {p.get('comando','')}")

            attr = curses.A_NORMAL
            if estado == "Z":
                attr = curses.color_pair(4)
            elif estado == "R":
                attr = curses.color_pair(2)
            if idx_real == self.seleccion:
                attr = curses.color_pair(5) | curses.A_BOLD
            if pid == self.pin_pid and idx_real != self.seleccion:
                attr = curses.color_pair(6)

            try:
                stdscr.addstr(y0 + 1 + i, 0, linea[:w - 1], attr)
            except curses.error:
                pass

    def _pid_activo(self):
        """PID cuyo detalle se muestra: el pineado, o el seleccionado."""
        if self.pin_pid is not None:
            return self.pin_pid
        pids = self._pids_ordenados()
        if 0 <= self.seleccion < len(pids):
            return pids[self.seleccion]
        return None

    def _dibujar_detalle(self, stdscr, y0, alto, w):
        if alto < 2:
            return
        clave = VISTAS[self.vista_idx][0]
        entrada = self.snapshot.get(clave, {})
        ts = entrada.get("ts")
        edad = f"{time.time() - ts:.1f}s" if ts else "s/d"
        titulo = f"── {VISTAS[self.vista_idx][1]} (act. hace {edad}) "
        stdscr.addstr(y0, 0, (titulo + "─" * w)[:w - 1], curses.color_pair(1))

        if "error" in entrada:
            stdscr.addstr(y0 + 1, 0, f"Error en analizador: {entrada['error']}"[:w-1],
                          curses.color_pair(4))
            return

        # La vista Sistema es global (no depende de un proceso seleccionado).
        if clave == "sistema":
            self._detalle_sistema(stdscr, y0 + 1, alto - 1, w, entrada.get("datos", {}))
            return

        pid = self._pid_activo()
        if pid is None:
            stdscr.addstr(y0 + 1, 0, "Sin proceso seleccionado")
            return

        datos = entrada.get("datos", {})
        info = datos.get(pid)
        if info is None:
            stdscr.addstr(y0 + 1, 0, f"PID {pid}: sin datos en esta vista (aún)")
            return

        # Dispatch a la función de detalle según la vista
        render = {
            "resumen": self._detalle_resumen,
            "memoria": self._detalle_memoria,
            "fds": self._detalle_fds,
            "threads": self._detalle_threads,
            "senales": self._detalle_senales,
            "scheduling": self._detalle_scheduling,
        }.get(clave)
        if render:
            render(stdscr, y0 + 1, alto - 1, w, info)

    # -------- Renders de detalle por vista --------
    def _linea(self, stdscr, y, w, texto, attr=curses.A_NORMAL):
        try:
            stdscr.addstr(y, 0, texto[:w - 1], attr)
        except curses.error:
            pass

    def _detalle_resumen(self, stdscr, y, alto, w, info):
        self._linea(stdscr, y, w, f"PID {info['pid']}   PPID {info['ppid']}   "
                    f"Usuario {info['usuario']} (uid {info['uid']} / gid {info.get('gid','?')})")
        self._linea(stdscr, y+1, w, f"Estado {info['estado']}   CPU {info['cpu']}%   "
                    f"RSS {info['rss_kb']/1024:.1f} MB   Threads {info['threads']}")
        self._linea(stdscr, y+2, w, f"Comando: {info['comando']}")

    def _detalle_memoria(self, stdscr, y, alto, w, info):
        self._linea(stdscr, y, w,
                    f"VmSize {info['vm_size']//1024} MB   VmRSS {info['vm_rss']//1024} MB   "
                    f"VmHWM {info['vm_hwm']//1024} MB   Swap {info['vm_swap']} kB")
        self._linea(stdscr, y+1, w,
                    f"Data {info['vm_data']} kB   Stack {info['vm_stk']} kB   "
                    f"Exe {info['vm_exe']} kB   Lib {info['vm_lib']} kB")
        self._linea(stdscr, y+2, w,
                    f"Page faults — minor: {info['minflt']}   major: {info['majflt']}")
        seg = info["segmentos"]
        self._linea(stdscr, y+3, w,
                    f"Segmentos (KB) — text:{seg['text']} data:{seg['data']} "
                    f"heap:{seg['heap']} stack:{seg['stack']} shared:{seg['shared']}",
                    curses.color_pair(3))

    def _detalle_fds(self, stdscr, y, alto, w, info):
        verbose = self.control.get("verbose", False)
        conteo = "  ".join(f"{t}:{n}" for t, n in info["conteo"].items())
        self._linea(stdscr, y, w, f"Total FDs: {info['total']}   [{conteo}]",
                    curses.color_pair(1))
        # En modo verbose mostramos más FDs.
        limite = (alto - 1) if verbose else min(alto - 1, 8)
        for i, fd in enumerate(info["lista"][:limite]):
            self._linea(stdscr, y + 1 + i, w,
                        f"  fd {fd['fd']:>3} [{fd['tipo']}] -> {fd['destino']}")
        restantes = len(info["lista"]) - limite
        if restantes > 0:
            self._linea(stdscr, y + 1 + limite, w,
                        f"  ... {restantes} más (SIGUSR2 para verbose)",
                        curses.color_pair(3))

    def _detalle_threads(self, stdscr, y, alto, w, info):
        self._linea(stdscr, y, w, f"Threads (LWPs): {info['num_threads']}",
                    curses.color_pair(1))
        cab = f"  {'TID':>7} {'ST':<2} {'CPU%':>6} {'ctx.vol':>9} {'ctx.nvol':>9} NOMBRE"
        self._linea(stdscr, y+1, w, cab, curses.A_BOLD)
        for i, t in enumerate(info["threads"][:alto - 2]):
            self._linea(stdscr, y + 2 + i, w,
                        f"  {t['tid']:>7} {t['estado']:<2} {t['cpu']:>6.1f} "
                        f"{t['ctx_vol']:>9} {t['ctx_nonvol']:>9} {t['nombre']}")

    def _detalle_senales(self, stdscr, y, alto, w, info):
        def fmt(lst):
            return ", ".join(lst) if lst else "(ninguna)"
        self._linea(stdscr, y, w, f"Bloqueadas:   {fmt(info['bloqueadas'])}")
        self._linea(stdscr, y+1, w, f"Ignoradas:    {fmt(info['ignoradas'])}")
        self._linea(stdscr, y+2, w, f"Con handler:  {fmt(info['con_handler'])}",
                    curses.color_pair(2))
        self._linea(stdscr, y+3, w, f"Pendientes:   {fmt(info['pendientes'])}",
                    curses.color_pair(3))
        self._linea(stdscr, y+4, w, f"Pend. grupo:  {fmt(info['pendientes_grupo'])}")

    def _detalle_scheduling(self, stdscr, y, alto, w, info):
        self._linea(stdscr, y, w,
                    f"Nice {info['nice']}   Priority {info['priority']}   "
                    f"Policy {info['policy']}   RT-prio {info['rt_priority']}")
        self._linea(stdscr, y+1, w,
                    f"Affinity CPUs: {info['affinity']}")
        self._linea(stdscr, y+2, w,
                    f"Ctx switches — vol: {info['ctx_vol']}   nonvol: {info['ctx_nonvol']}")
        self._linea(stdscr, y+3, w,
                    f"utime {info['utime']}   stime {info['stime']}   "
                    f"SID {info['sid']}   PGID {info['pgid']}")

    def _detalle_sistema(self, stdscr, y, alto, w, d):
        if not d:
            self._linea(stdscr, y, w, "Recolectando datos del sistema...")
            return
        cpu = d.get("cpu", {})
        self._linea(stdscr, y, w,
                    f"CPU — user {cpu.get('user',0)}%  sys {cpu.get('system',0)}%  "
                    f"idle {cpu.get('idle',0)}%  iowait {cpu.get('iowait',0)}%",
                    curses.color_pair(2))
        load = d.get("load", (0, 0, 0))
        self._linea(stdscr, y+1, w,
                    f"Load avg: {load[0]:.2f} {load[1]:.2f} {load[2]:.2f}   "
                    f"Uptime: {d.get('uptime',0)/3600:.1f} h")
        self._linea(stdscr, y+2, w,
                    f"Mem — usada {d.get('mem_usada',0)//1024} MB / "
                    f"{d.get('mem_total',0)//1024} MB   "
                    f"buffers {d.get('buffers',0)//1024} MB   "
                    f"cached {d.get('cached',0)//1024} MB")
        self._linea(stdscr, y+3, w,
                    f"Swap usada {d.get('swap_usada',0)//1024} MB / "
                    f"{d.get('swap_total',0)//1024} MB")
        estados = "  ".join(f"{k}:{v}" for k, v in d.get("por_estado", {}).items())
        self._linea(stdscr, y+4, w,
                    f"Procesos: {d.get('num_procesos',0)}   Threads: {d.get('total_threads',0)}   "
                    f"Zombies: {d.get('zombies',0)}   [{estados}]",
                    curses.color_pair(4) if d.get("zombies", 0) else curses.A_NORMAL)
        # Top 3 CPU y RSS
        top_cpu = d.get("top_cpu", [])
        top_rss = d.get("top_rss", [])
        self._linea(stdscr, y+5, w, "Top CPU:", curses.color_pair(1))
        for i, (pid, cmd, val) in enumerate(top_cpu):
            self._linea(stdscr, y+6+i, w, f"  {val:>6.1f}%  pid {pid}  {cmd}")
        base = y + 6 + len(top_cpu)
        self._linea(stdscr, base, w, "Top RSS:", curses.color_pair(1))
        for i, (pid, cmd, val) in enumerate(top_rss):
            self._linea(stdscr, base+1+i, w, f"  {val/1024:>6.1f}MB  pid {pid}  {cmd}")
        # Contador global de lecturas de /proc (compartido entre analizadores,
        # protegido por Lock). Demuestra el uso de una primitiva de sincronización.
        if self.contador_lecturas is not None:
            fila = base + 1 + len(top_rss)
            self._linea(stdscr, fila, w,
                        f"Lecturas de /proc (total, todos los analizadores): "
                        f"{self.contador_lecturas.value}",
                        curses.color_pair(3))

    def _dibujar_barra_estado(self, stdscr, h, w):
        clave = VISTAS[self.vista_idx][0]
        intervalo = self.intervalos[clave].value if clave in self.intervalos else 0
        verbose = "V" if self.control.get("verbose", False) else " "
        pin = f"pin:{self.pin_pid}" if self.pin_pid else "pin:-"
        filtro = ""
        if self.filtro_cmd:
            filtro += f" /{self.filtro_cmd}"
        if self.filtro_usuario:
            filtro += f" u:{self.filtro_usuario}"

        # Mensaje temporal (feedback de señales) tiene prioridad.
        if self.mensaje and time.time() < self.mensaje_hasta:
            izquierda = self.mensaje
        else:
            izquierda = (f"[{verbose}] orden:{self.orden}  {pin}  "
                         f"int:{intervalo:.1f}s{filtro}")
        derecha = "h:ayuda  q:salir"
        linea = izquierda.ljust(w - len(derecha) - 1) + derecha
        try:
            stdscr.addstr(h - 1, 0, linea[:w - 1], curses.color_pair(1))
        except curses.error:
            pass

    def _dibujar_ayuda(self, stdscr, h, w):
        lineas = [
            "  AYUDA — Monitor de Procesos",
            "",
            "  1-7 / r m f t s p g   Cambiar de vista",
            "  ↑ ↓                   Navegar procesos",
            "  Enter                 Fijar (pin) proceso",
            "  /                     Filtrar por comando",
            "  u                     Filtrar por usuario",
            "  c                     Cambiar orden (cpu/rss/pid)",
            "  + / -                 Ajustar intervalo de la vista",
            "  q                     Salir",
            "",
            "  Señales: SIGUSR1=dump  SIGUSR2=verbose  SIGHUP=reload",
            "",
            "  (cualquier tecla para cerrar)",
        ]
        alto = len(lineas) + 2
        ancho = max(len(l) for l in lineas) + 4
        y0 = max(0, (h - alto) // 2)
        x0 = max(0, (w - ancho) // 2)
        for i in range(alto):
            try:
                stdscr.addstr(y0 + i, x0, " " * ancho, curses.color_pair(5))
            except curses.error:
                pass
        for i, l in enumerate(lineas):
            try:
                stdscr.addstr(y0 + 1 + i, x0, l.ljust(ancho), curses.color_pair(5))
            except curses.error:
                pass