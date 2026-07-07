"""
base.py — Clase base de los analizadores.

Cada analizador corre en su propio proceso (multiprocessing.Process).
La clase base implementa el loop común: recolectar datos, escribirlos al
snapshot compartido con timestamp, dormir el intervalo, repetir.

El intervalo vive en un multiprocessing.Value compartido para que el
display pueda ajustarlo en caliente con las teclas + / -.
"""
import os
import time
import signal
import multiprocessing


class AnalizadorBase(multiprocessing.Process):
    # Cada subclase define su clave (bajo qué entrada del snapshot escribe).
    clave = "base"

    def __init__(self, snapshot, intervalo_valor, detener_event,
                 contador_lecturas=None, lock_contador=None):
        """
        snapshot          : Manager.dict global compartido
        intervalo_valor   : multiprocessing.Value('d') con el intervalo en segundos
        detener_event     : multiprocessing.Event para shutdown coordinado
        contador_lecturas : multiprocessing.Value('i') compartido — cuenta cuántas
                            veces TODOS los analizadores leyeron /proc (estadística global)
        lock_contador     : multiprocessing.Lock que protege ese contador. Como los 7
                            analizadores (procesos distintos) incrementan el mismo valor,
                            sin lock habría una race condition (el clásico contador += 1
                            de la clase 9: leer-sumar-escribir no es atómico).
        """
        super().__init__()
        self.snapshot = snapshot
        self.intervalo = intervalo_valor
        self.detener = detener_event
        self.contador_lecturas = contador_lecturas
        self.lock_contador = lock_contador
        # Los analizadores no son daemon: queremos joinearlos limpiamente.
        self.daemon = False

    def recolectar(self):
        """
        Cada subclase implementa esto. Debe devolver el objeto (normalmente
        un dict) que se guarda en snapshot[self.clave]["datos"].
        """
        raise NotImplementedError

    def pids_a_analizar(self):
        """
        Devuelve la lista de PIDs que publica el recolector central (clave
        "_pids" del snapshot). Si el recolector todavía no escribió nada
        (arranque), cae en leer /proc directamente para no perder el primer
        ciclo. Así los analizadores consumen la lista maestra en vez de
        listar /proc cada uno por su lado.
        """
        entrada = self.snapshot.get("_pids")
        if entrada and entrada.get("datos"):
            return entrada["datos"]
        # Fallback: el recolector aún no publicó (evita carrera en el arranque).
        import procfs
        return procfs.listar_pids()

    def _contar_lectura(self):
        """
        Incrementa el contador global de lecturas de /proc, de forma segura.

        Varios analizadores (procesos distintos) llaman a esto sobre el MISMO
        Value compartido. La operación `contador.value += 1` NO es atómica:
        internamente hace leer -> sumar -> escribir, y dos procesos pueden
        pisarse (race condition, clase 9). El `with self.lock_contador:`
        garantiza que solo un proceso por vez ejecute el incremento, evitando
        que se pierdan cuentas. Es el uso de libro de un Lock.
        """
        if self.contador_lecturas is None or self.lock_contador is None:
            return
        with self.lock_contador:
            self.contador_lecturas.value += 1

    def run(self):
        # Los hijos ignoran SIGINT: el shutdown lo coordina el padre vía Event.
        # Así Ctrl+C no mata a cada analizador por su cuenta dejando basura.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

        while not self.detener.is_set():
            inicio = time.time()
            try:
                datos = self.recolectar()
                # Contabilizar esta lectura de /proc en el contador global
                # compartido (protegido por lock). Ver _contar_lectura().
                self._contar_lectura()
                # Escritura atómica de la entrada completa: reasignamos la clave
                # entera del Manager.dict (dict-de-dict) en un solo paso.
                self.snapshot[self.clave] = {
                    "datos": datos,
                    "ts": time.time(),
                    "pid_analizador": os.getpid(),
                }
            except Exception as e:
                # Un analizador nunca debe tumbar el sistema: registramos el error
                # en el propio snapshot y seguimos.
                self.snapshot[self.clave] = {
                    "datos": {},
                    "ts": time.time(),
                    "error": repr(e),
                    "pid_analizador": os.getpid(),
                }

            # Dormir el intervalo, pero chequeando el Event para poder salir
            # rápido en un shutdown. Leemos el intervalo fresco cada vuelta.
            objetivo = max(0.1, self.intervalo.value)
            transcurrido = time.time() - inicio
            restante = objetivo - transcurrido
            while restante > 0 and not self.detener.is_set():
                paso = min(0.2, restante)
                time.sleep(paso)
                restante -= paso
