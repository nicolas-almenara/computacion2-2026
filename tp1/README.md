# Monitor de Procesos y Threads

**Trabajo Práctico Nº 1 — Computación II — Universidad de Mendoza — 2026**
**Alumno: Nicolás Almenara**

Monitor del sistema en tiempo real, estilo `htop`, con énfasis en mostrar la
**anatomía interna** de cada proceso y sus threads. Toda la información se
extrae leyendo `/proc` directamente (sin `psutil` ni equivalentes).

---

## Descripción general

El monitor es un **sistema multiproceso**. El proceso principal corre una
interfaz de texto (TUI, con `curses`) y siete procesos analizadores corren en
paralelo, cada uno extrayendo una dimensión distinta de cada proceso del
sistema (resumen, memoria, file descriptors, threads, señales, scheduling y
stats globales). Cada analizador tiene su propio ritmo de refresco y escribe
sus resultados en un **snapshot global compartido** (`Manager.dict`). La TUI
lee ese snapshot y renderiza la vista activa.

### Cómo se usa

```bash
docker compose up --build
```

Ese comando construye la imagen y levanta todo el sistema (proceso principal +
recolector + 7 analizadores). Ahora bien, como el monitor es una **TUI
interactiva**, `docker compose up` no siempre conecta bien el teclado (está
pensado para servicios de fondo). Para interactuar con las teclas, correrlo con
`run`, que conecta la terminal completa:

```bash
docker compose run --rm monitor
```

Una vez dentro, se navega con el teclado (ver ayuda con `h`):

| Tecla | Acción |
|-------|--------|
| `1`–`7` o `r/m/f/t/s/p/g` | Cambiar de vista |
| `↑` `↓` | Navegar la lista de procesos |
| `Enter` | Fijar (pin) el proceso seleccionado |
| `/` | Filtrar por comando |
| `u` | Filtrar por usuario |
| `c` | Cambiar orden (CPU% / RSS / PID) |
| `+` / `-` | Ajustar el intervalo de refresco de la vista activa |
| `q` | Salir limpiamente |
| `h` / `?` | Ayuda |

Por defecto el contenedor solo ve **sus propios procesos**. Para monitorear
todo el host, descomentar `pid: "host"` en `docker-compose.yml`.

---

## Diagrama de arquitectura

```
                    ┌──────────────────────────────────────┐
                    │           SNAPSHOT GLOBAL            │
                    │        (Manager.dict compartido)     │
                    │  "resumen"    : {datos, ts, pid}     │
                    │  "memoria"    : {datos, ts, pid}     │
                    │  "fds"        : {datos, ts, pid}     │
                    │  "threads"    : {datos, ts, pid}     │
                    │  "senales"    : {datos, ts, pid}     │
                    │  "scheduling" : {datos, ts, pid}     │
                    │  "sistema"    : {datos, ts, pid}     │
                    │  "_pids"      : {lista maestra}      │
                    └───────▲──────────────────────▲───────┘
             escriben (7)   │                      │  lee
        ┌──────────┬────────┼───────┬─────  ...    │
        │          │        │       │              │
   ┌────▼───┐ ┌────▼───┐ ┌──▼────┐ ┌▼──────┐  ┌────▼──────┐
   │Resumen │ │Memoria │ │ FDs   │ │Threads│  │  Display  │
   │  2s    │ │  3s    │ │  5s   │ │  2s   │  │   (TUI)   │
   └────────┘ └────────┘ └───────┘ └───────┘  │  proceso  │
   ┌────────┐ ┌──────────┐ ┌────────┐         │ principal │
   │Señales │ │Scheduling│ │Sistema │         └─────▲─────┘
   │  10s   │ │   10s    │ │  2s    │               │ señales
   └────────┘ └──────────┘ └────────┘         ┌─────┴──────┐
                                              │ self-pipe  │
   7 analizadores en paralelo,               │ (handlers) │
   cada uno proceso independiente            └────────────┘

   Intervalos ajustables en caliente vía multiprocessing.Value (uno por vista)
   Shutdown coordinado vía multiprocessing.Event
   Contador de lecturas de /proc vía multiprocessing.Value + Lock
```

### Componentes

| Componente | Archivo | Responsabilidad |
|------------|---------|-----------------|
| Recolector | `src/recolector.py` | Lista central de PIDs vivos (clave `_pids`) |
| 7 Analizadores | `src/analizadores/*.py` | Cada uno extrae una dimensión de `/proc` |
| Clase base | `src/base.py` | Loop común: recolectar → escribir snapshot → dormir |
| Agregador | *(el propio `Manager.dict`)* | Mantiene el snapshot global en memoria compartida |
| Display (TUI) | `src/display.py` | Renderiza la vista activa, maneja teclado y señales |
| Manejo de señales | `src/senales.py` | Self-pipe: convierte señales en eventos legibles |
| Helpers `/proc` | `src/procfs.py` | Todo el parseo de `/proc` centralizado |
| Orquestador | `src/main.py` | Arma todo y coordina el ciclo de vida |

---

## Decisiones de diseño

### ¿Por qué multiproceso y no threads?

El TP lo pide, pero además tiene sentido: los analizadores son
mayormente **I/O-bound** (leen cientos de archivos de `/proc`), pero el parseo
y los cálculos de deltas son CPU. Con procesos separados cada analizador corre
en su propio intérprete sin pelear por el GIL (clase 10). Además, si un
analizador falla parseando un `/proc` raro, no tumba a los demás: está aislado
en su propio proceso.

### ¿Por qué `Manager.dict` y no `Value`/`Array` para el snapshot?

El snapshot es una estructura **compleja y anidada** (dict de dicts, con listas
de threads, listas de FDs, etc.) cuyo tamaño cambia todo el tiempo (procesos
que nacen y mueren). `Value`/`Array` solo sirven para tipos primitivos de C de
tamaño fijo (clase 9), así que no alcanzan. `Manager.dict` permite compartir
objetos Python arbitrarios entre procesos: es más lento (va por IPC contra el
proceso del Manager), pero acá la conveniencia gana, porque los intervalos de
refresco son de segundos, no de microsegundos. La velocidad no es crítica.

En cambio, **para los intervalos sí uso `Value`** (`multiprocessing.Value('d')`,
uno por vista): son un solo `double`, se leen/escriben muchísimo (cada vuelta
del loop de cada analizador), y ahí sí importa que sea memoria compartida
directa vía `mmap` (clase 7) y no IPC. Es exactamente el criterio de la tabla
de la clase 9: *datos simples y frecuentes → `Value`; datos complejos → `Manager`*.

### ¿Cómo manejo las race conditions?

Dos frentes:

1. **Escritura al snapshot**: cada analizador escribe **su propia clave** del
   `Manager.dict` (`snapshot["resumen"] = ...`), nunca la de otro. No hay dos
   procesos escribiendo la misma clave, así que no hay carrera entre
   analizadores. Además, reasigno la entrada **completa** de una sola vez
   (el dict `{datos, ts, pid}` entero), en lugar de mutar sub-campos por
   separado — así el display nunca ve una entrada a medio actualizar.

2. **Intervalos (`Value`)**: el display escribe y los analizadores leen. Como
   es un solo `double` y la semántica es "último que escribe gana" (no un
   read-modify-write acumulativo), un lock sería innecesario acá. El caso
   peligroso de la clase 9 (`contador.value += 1` desde varios procesos) no
   aplica porque nadie **acumula** sobre el intervalo: se **setea**.

3. **Contador de lecturas de /proc (`Value` + `Lock`)**: acá sí uso una
   primitiva de sincronización. Hay un contador global (`multiprocessing.Value`)
   que lleva cuántas veces todos los analizadores leyeron `/proc`, y se muestra
   en la vista Sistema. Como los 8 procesos (recolector + 7 analizadores)
   incrementan el **mismo** valor, esto es exactamente el caso peligroso de la
   clase 9: `contador.value += 1` **no es atómico** (hace leer → sumar →
   escribir), y sin protección dos procesos se pisarían y se perderían cuentas.
   Por eso el incremento va dentro de un `with lock_contador:` (`base.py`,
   método `_contar_lectura`), que garantiza que solo un proceso por vez ejecute
   el read-modify-write. Es el uso de libro de un `Lock`.

En resumen: el **estado principal** (snapshot e intervalos) está libre de races
por diseño, y donde sí aparece una race genuina (un contador acumulativo
compartido) la resuelvo con un `Lock`, que es la herramienta correcta para
proteger un read-modify-write entre procesos.

### ¿Por qué los intervalos por defecto que elegí?

Balanceo costo de lectura vs. utilidad. Las vistas que cambian rápido y son las
más miradas (Resumen, Threads, Sistema) van a **2s**. Memoria cambia más lento
→ **3s**. FDs es más caro (un `readlink` por descriptor) y cambia poco → **5s**.
Señales y Scheduling son casi estáticos (rara vez cambian las máscaras o la
política) → **10s**. Todos ajustables en caliente con `+`/`-`, pero cada vista
tiene un **mínimo propio** (Resumen/Threads 0.5s, Memoria/Sistema 1s, FDs 2s,
Señales/Scheduling 5s): no tiene sentido refrescar las señales, que casi nunca
cambian, tan rápido como el CPU. El mínimo está en `MIN_INTERVALO` en
`display.py`, siguiendo la tabla del enunciado.

### El rol del recolector

El recolector (`recolector.py`) corre en su propio proceso y es la **fuente
única de verdad** de qué procesos existen: lista los PIDs de `/proc` y los
publica en el snapshot bajo `_pids`. Los 7 analizadores consumen esa lista
(`self.pids_a_analizar()` en la clase base) en vez de listar `/proc` cada uno
por su cuenta. Esto centraliza el "qué procesos hay": si mañana quisiéramos
filtrar kernel threads o procesos de otro usuario, se hace en un solo lugar y
todos lo heredan. En el arranque, si el recolector todavía no publicó, los
analizadores caen en leer `/proc` directo para no perder el primer ciclo
(evita una carrera de arranque).

### Self-pipe para señales

Los handlers de señal deben ser **async-signal-safe** (clase 6): no pueden
hacer `print`, tomar locks ni tocar estructuras complejas. Por eso el handler
solo escribe **un byte** al pipe. El loop principal de la TUI lee ese pipe con
`select()` y procesa la señal fuera del contexto del handler, donde ya es seguro
hacer cualquier cosa (generar el dump, recargar config, etc.). El extremo de
escritura es no bloqueante: si el pipe se llenara, el handler descarta el byte
en vez de colgarse.

### Shutdown coordinado

Un solo `multiprocessing.Event` (`detener`). Los analizadores lo chequean en
cada vuelta del loop (y mientras duermen, en pasos de 0.2s, para salir rápido).
El display lo setea al recibir SIGINT/SIGTERM o al presionar `q`. `main.py`
hace `join()` con timeout y, si algún proceso quedó colgado, lo `terminate()`.
Los analizadores **ignoran SIGINT/SIGTERM** ellos mismos: el shutdown lo maneja
solo el padre, para que Ctrl+C no mate cada hijo por su cuenta dejando el
Manager en un estado raro.

---

## Conceptos del curso aplicados

- **Clase 3 (Procesos: anatomía)**: la vista Memoria agrupa los segmentos de
  `/proc/<pid>/maps` en text/data/heap/stack/shared, exactamente el layout de
  memoria virtual que vimos (text = `r-x`, data = `rw-`, más `[heap]` y
  `[stack]`).

- **Clase 4 (fork, exec, wait — zombies)**: la vista Sistema cuenta los
  procesos en estado `Z`. Como vimos, un zombie es un proceso terminado cuyo
  padre todavía no llamó a `wait()`; lo detecto por el campo `State` de
  `/proc/<pid>/stat`.

- **Clase 5 (Pipes, file descriptors)**: la vista FDs lista los descriptores
  abiertos de cada proceso (`/proc/<pid>/fd`), infiriendo su tipo (tty, socket,
  pipe, file) del destino del symlink — los mismos fds 0/1/2 y demás que vimos.

- **Clase 6 (Señales, self-pipe)**: el manejo de señales del monitor usa
  literalmente el patrón self-pipe de la clase, y la vista Señales decodifica
  las máscaras `SigBlk`/`SigIgn`/`SigCgt`/`SigPnd` a nombres legibles.

- **Clase 7 (mmap y memoria compartida)**: los `Value` de los intervalos son
  `mmap` anónimo por debajo, como vimos. El snapshot compartido es la versión
  de alto nivel (`Manager`) del mismo problema.

- **Clase 8-9 (Multiprocessing)**: toda la arquitectura son `Process` +
  `Manager` + `Value` + `Event` + `Lock`. La elección `Value` vs `Manager`
  sigue la tabla comparativa de la clase 9, y el `Lock` protege el contador
  de lecturas de `/proc` (un `contador.value += 1` compartido entre procesos,
  el caso de race condition de la clase 9).

- **Clase 10 (Threading, GIL)**: la vista Threads lee los LWPs de
  `/proc/<pid>/task/<tid>`, que es donde el kernel expone los threads de un
  proceso. Que use multiproceso (y no threads) para los analizadores es
  justamente por el GIL en tareas con cómputo.

---

## Limitaciones conocidas

- **Permisos**: sin privilegios, no se pueden leer los FDs ni algunos campos de
  procesos de otros usuarios (`/proc/<pid>/fd` da `PermissionError`). El monitor
  lo maneja silenciosamente (los omite), pero por eso la vista FDs puede mostrar
  menos procesos que las otras. Correr como root (o con `pid: host` + privilegios)
  muestra todo.
- **CPU% en la primera lectura**: como se calcula por delta de jiffies entre dos
  lecturas, el primer refresh de cada proceso muestra 0.0%. Se estabiliza en el
  segundo ciclo.
- **Procesos efímeros**: un proceso que nace y muere entre que el recolector lo
  lista y el analizador lo lee simplemente se omite (los helpers de `procfs`
  devuelven vacío ante `FileNotFoundError`). No se rastrean procesos con vida
  más corta que el intervalo.
- **`SIGWINCH`**: el repintado al redimensionar es básico (fuerza un refresh);
  en redimensiones muy agresivas puede haber un frame feo antes de reacomodarse.
- **Precisión de CPU% global**: usa la línea agregada `cpu` de `/proc/stat`, no
  el desglose por core.

---

## Cómo correr y testear

### Correr

```bash
docker compose up --build
```

Para interactuar con la TUI (que el teclado responda), correr con `run`:

```bash
docker compose run --rm monitor
```

O directamente (en Linux, fuera de Docker):

```bash
python3 src/main.py
```

### Probar las señales (con el monitor corriendo)

En otra terminal, averiguar el PID del proceso `python3 src/main.py` y:

```bash
kill -USR1 <pid>    # genera dump_<timestamp>.json con el snapshot actual
kill -USR2 <pid>    # toggle modo verbose (más FDs visibles en la vista FDs)
kill -HUP  <pid>    # recarga config.json (intervalos por defecto)
kill -TERM <pid>    # shutdown limpio
```

---

## Estructura del repositorio

```
.
├── README.md                 ← este informe
├── Dockerfile
├── docker-compose.yml
├── requirements.txt          ← solo stdlib (sin dependencias externas)
├── config.json               ← intervalos por defecto
└── src/
    ├── main.py               ← entry point / orquestador
    ├── base.py               ← clase base de los analizadores
    ├── procfs.py             ← helpers de parseo de /proc
    ├── recolector.py         ← lista maestra de PIDs
    ├── senales.py            ← self-pipe y handlers
    ├── display.py            ← TUI con curses
    └── analizadores/
        ├── resumen.py
        ├── memoria.py
        ├── fds.py
        ├── threads.py
        ├── senales.py
        ├── scheduling.py
        └── sistema.py
```

---

*Trabajo Práctico Nº 1 — Computación II — 2026*