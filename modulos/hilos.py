# -*- coding: utf-8 -*-
"""
Modulo: Hilos (Programacion Concurrente - Unidad III)
Sesiones 22 al 26: QThread, ciclo de vida (started/finished), senales
personalizadas con parametros y cancelacion cooperativa (Stop Flag).

Patrones aplicados (tal como se evaluan en las guias de laboratorio):
  - Sesion 23: subclase de QThread que sobrescribe run() sin tocar widgets.
  - Sesion 24: senales nativas started/finished + guardas con isRunning().
  - Sesion 25: senal tipada a nivel de clase (Signal(int, str)) + .emit().
  - Sesion 26: bandera _interrupcion_solicitada + detener() + break.
            NUNCA se usa terminate() (cancelacion destructiva prohibida).
"""

from PySide6.QtCore import QThread, Signal

from modulos import almacen_datos


class HiloTarea(QThread):
    """Base reutilizable para tareas pesadas en segundo plano.

    Expone:
      - signal 'progreso'        -> (porcentaje 0-100, texto de estado).
      - signal 'tarea_finalizada'-> dict con el resultado de run().
      - 'detener()'              -> peticion cooperativa de parada (Stop Flag).
      - atributo 'cancelado'     -> True si la tarea se detuvo antes de terminar.
    """

    # Sesion 25: senal personalizada tipada declarada a nivel de clase,
    # fuera del constructor.
    progreso = Signal(int, str)
    tarea_finalizada = Signal(dict)

    def __init__(self):
        super().__init__()
        # Sesion 26: bandera de parada cooperativa (Stop Flag).
        self._interrupcion_solicitada = False
        self.cancelado = False

    def detener(self):
        """Solicita la parada; el hilo la confirma en un punto seguro."""
        self._interrupcion_solicitada = True

    def _parada_solicitada(self):
        return self._interrupcion_solicitada


class HiloLimpiarReservas(HiloTarea):
    """Elimina reservas en lotes con progreso y cancelacion cooperativa.

    El trabajo pesado (DELETE masivo en lotes) corre en run(); la cache en
    memoria (almacen_datos.lista_reservas) se actualiza SOLO en el hilo
    principal, cuando llega la senal 'tarea_finalizada'.
    """

    def __init__(self, ids):
        super().__init__()
        self.ids = list(ids)

    def run(self):
        """Sesion 23: punto de entrada del hilo secundario. Sin widgets."""
        total = len(self.ids)

        def _avance(hechas, _total):
            pct = int((hechas * 100) / total) if total else 100
            self.progreso.emit(pct, f"Eliminadas {hechas} de {total}.")

        try:
            resultado = almacen_datos.borrar_reservas_por_lotes(
                self.ids,
                pedir_parada=self._parada_solicitada,
                on_progreso=_avance,
            )
        except Exception as error:  # noqa: BLE001
            self.tarea_finalizada.emit({
                "eliminadas": 0,
                "mesas_afectadas": [],
                "cancelado": False,
                "error": str(error),
            })
            return

        self.cancelado = resultado.get("cancelado", False)
        # La cache se recarga en el hilo secundario pero NO se muta: la lista
        # fresca viaja por señal y se asigna en el hilo principal (thread-safe).
        nuevas_reservas = resultado.get("nuevas_reservas")
        if nuevas_reservas is None:
            nuevas_reservas = almacen_datos._cargar_reservas()
        self.tarea_finalizada.emit({
            "eliminadas": resultado.get("eliminadas", 0),
            "mesas_afectadas": resultado.get("mesas_afectadas", []),
            "cancelado": self.cancelado,
            "nuevas_reservas": nuevas_reservas,
            "total": total,
        })