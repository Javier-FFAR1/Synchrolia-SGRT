# -*- coding: utf-8 -*-
"""
Modulo: Encabezado de Modulo
Barra superior reutilizable de cada panel: titulo a la izquierda y
fecha/hora actual en vivo a la derecha (refuerza el concepto SGRT
= gestion en tiempo real). Actualiza la hora cada segundo.
"""

import datetime

from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

PRIMARIO = "#1B3A5C"
DORADO = "#D4A843"
SECUNDARIO = "#2C5F8A"
GRIS_SUBTITULO = "#888888"
GRIS_MEDIO = "#555555"


class EncabezadoModulo(QWidget):
    """Encabezado con titulo, subtitulo y reloj en vivo."""

    def __init__(self, titulo, subtitulo="", parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Columna de titulo y subtitulo
        col_titulo = QVBoxLayout()
        col_titulo.setSpacing(2)

        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("titulo")
        col_titulo.addWidget(lbl_titulo)

        if subtitulo:
            lbl_sub = QLabel(subtitulo)
            lbl_sub.setObjectName("subtitulo")
            col_titulo.addWidget(lbl_sub)

        layout.addLayout(col_titulo)
        layout.addStretch()

        # Reloj en vivo a la derecha
        self.lbl_fecha = QLabel()
        self.lbl_fecha.setStyleSheet(
            f"color: {GRIS_MEDIO}; font-size: 12px; font-weight: 600; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        self.lbl_fecha.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.lbl_fecha)

        self.lbl_hora = QLabel()
        self.lbl_hora.setFont(QFont("Raleway", 22, QFont.Weight.Bold))
        self.lbl_hora.setStyleSheet(
            f"color: {PRIMARIO}; font-family: 'Raleway', 'Segoe UI', sans-serif; "
            "font-size: 22px; font-weight: 700;"
        )
        self.lbl_hora.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.lbl_hora)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._actualizar_reloj)
        self._timer.start(1000)
        self._actualizar_reloj()

    def _actualizar_reloj(self):
        ahora = datetime.datetime.now()
        self.lbl_fecha.setText(self._fecha_es(ahora))
        self.lbl_hora.setText(ahora.strftime("%I:%M %p"))

    @staticmethod
    def _fecha_es(ahora):
        """Retorna la fecha en espanol independiente de la locale del sistema."""
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                 "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        dia = dias[ahora.weekday()]
        mes = meses[ahora.month - 1]
        return f"{dia}, {ahora.day} de {mes} de {ahora.year}"
