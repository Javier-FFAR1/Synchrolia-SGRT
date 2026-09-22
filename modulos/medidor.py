# -*- coding: utf-8 -*-
"""
Modulo: Medidor Circular
Widget reutilizable tipo "donut" para visualizar porcentajes (KPIs):
un anillo que se llena segun el valor y el porcentaje en el centro.
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class BarraProgreso(QWidget):
    """Barra de progreso horizontal estilizada para porcentajes."""

    def __init__(self, color, altura=16, parent=None):
        super().__init__(parent)
        self._valor = 0.0
        self._color = QColor(color)
        self.setFixedHeight(altura)

    def set_valor(self, valor):
        """Actualiza el porcentaje (0-100) y repinta la barra."""
        self._valor = max(0.0, min(100.0, float(valor)))
        self.update()

    def valor(self):
        return self._valor

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        radio = h / 2.0
        track = QRectF(0, 0, w, h)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#E3E9F0"))
        p.drawRoundedRect(track, radio, radio)

        ancho_fill = w * self._valor / 100.0
        if ancho_fill > 0:
            p.save()
            p.setClipRect(track)
            p.setBrush(self._color)
            p.drawRect(QRectF(0, 0, ancho_fill, h))
            p.restore()
        p.end()


class MedidorCircular(QWidget):
    """Medidor de porcentaje tipo donut con el valor en el centro."""

    def __init__(self, color, ancho_anillo=14, tamano=130,
                 color_texto="#1B3A5C", parent=None):
        super().__init__(parent)
        self._valor = 0.0
        self._color = QColor(color)
        self._anillo = ancho_anillo
        self._color_texto = QColor(color_texto)
        self.setFixedSize(tamano, tamano)

    def set_valor(self, valor):
        """Actualiza el porcentaje (0-100) y repinta el anillo."""
        self._valor = max(0.0, min(100.0, float(valor)))
        self.update()

    def valor(self):
        return self._valor

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        tamano = self.width()
        margen = 6
        rect = QRectF(margen, margen, tamano - 2 * margen, tamano - 2 * margen)

        # Anillo de fondo (oscuro)
        p.setPen(
            QPen(
                QColor("#26344A"), self._anillo,
                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
            )
        )
        p.drawArc(rect, 0, 360 * 16)

        # Anillo de progreso (arranca arriba y gira en sentido horario)
        if self._valor > 0:
            p.setPen(
                QPen(
                    self._color, self._anillo,
                    Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
                )
            )
            span = int(-self._valor * 360 * 16 / 100)
            p.drawArc(rect, 90 * 16, span)

        # Valor porcentual en el centro
        fuente = QFont("Raleway", 24, QFont.Weight.Bold)
        if not fuente.exactMatch():
            fuente = QFont("Segoe UI", 24, QFont.Weight.Bold)
        p.setFont(fuente)
        p.setPen(self._color_texto)
        p.drawText(
            self.rect(), Qt.AlignmentFlag.AlignCenter,
            f"{int(round(self._valor))}%"
        )
        p.end()