"""
senales.py — Manejo de señales del proceso principal (self-pipe pattern).

El monitor debe responder a SIGINT/SIGTERM (shutdown), SIGHUP (reload),
SIGUSR1 (dump), SIGUSR2 (toggle verbose) y SIGWINCH (repintar).

Los handlers de señal deben ser async-signal-safe: NO pueden hacer print,
tomar locks, ni tocar estructuras complejas. Por eso usamos el patrón
self-pipe: el handler solo escribe UN byte identificador al pipe. El loop
principal del display lee ese pipe con select() y procesa la señal de forma
segura, fuera del contexto del handler.
"""
import os
import signal
import fcntl

# Byte identificador que se escribe al pipe por cada señal.
# El loop principal lee estos bytes y sabe qué señal llegó.
CODIGOS = {
    signal.SIGINT:  b"I",
    signal.SIGTERM: b"T",
    signal.SIGHUP:  b"H",
    signal.SIGUSR1: b"1",
    signal.SIGUSR2: b"2",
    signal.SIGWINCH: b"W",
}

# Extremos del self-pipe (se inicializan en instalar()).
_read_fd = -1
_write_fd = -1


def instalar():
    """
    Crea el self-pipe y registra los handlers. Devuelve el fd de lectura
    para que el loop principal lo incluya en su select().
    """
    global _read_fd, _write_fd
    _read_fd, _write_fd = os.pipe()

    # El extremo de escritura debe ser no bloqueante: si el pipe se llena,
    # el handler descarta el byte en vez de colgarse (async-signal-safe).
    flags = fcntl.fcntl(_write_fd, fcntl.F_GETFL)
    fcntl.fcntl(_write_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    for sig in CODIGOS:
        try:
            signal.signal(sig, _handler)
        except (ValueError, OSError):
            # Algunas señales pueden no existir en ciertas plataformas.
            pass

    return _read_fd


def _handler(signum, frame):
    """
    Handler async-signal-safe: SOLO escribe un byte al pipe.
    Nada de prints, locks o lógica. El procesamiento real ocurre en el loop.
    """
    try:
        os.write(_write_fd, CODIGOS.get(signum, b"?"))
    except BlockingIOError:
        pass  # Pipe lleno: la señal ya está encolada de sobra, no pasa nada.


def leer_senales():
    """
    Lee del self-pipe todos los bytes disponibles y devuelve la lista de
    señales pendientes como strings ('SIGINT', 'SIGHUP', ...).
    El loop principal llama esto cuando select() marca el fd como legible.
    """
    resultado = []
    try:
        datos = os.read(_read_fd, 1024)
    except (BlockingIOError, OSError):
        return resultado

    inverso = {v: k for k, v in CODIGOS.items()}
    for byte in datos:
        b = bytes([byte])
        sig = inverso.get(b)
        if sig is not None:
            resultado.append(signal.Signals(sig).name)
    return resultado


def fd_lectura():
    """Devuelve el fd de lectura del self-pipe (para el select del loop)."""
    return _read_fd
