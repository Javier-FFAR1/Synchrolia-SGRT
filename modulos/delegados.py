# -*- coding: utf-8 -*-
"""Delegados visuales reutilizables para tablas."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QStyle, QStyledItemDelegate

ESTADOS_RESERVA = {
    "Pendiente": ("#FFF4E5", "#8A5200", "#F59E0B"),
    "Confirmada": ("#EAF6EB", "#256B2A", "#2E7D32"),
    "Cancelada": ("#FDECEC", "#A61B1B", "#BC1515"),
    "Completada": ("#EAF1F8", "#1B3A5C", "#2C5F8A"),
}
ESTADO_NEUTRO = ("#F1F3F5", "#555F6B", "#8899AA")


class BadgeEstadoDelegate(QStyledItemDelegate):
    """Dibuja el estado de una reserva como una pastilla suave con punto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fuente = QFont("Segoe UI")
        self._fuente.setPixelSize(12)
        self._fuente.setWeight(QFont.Weight.DemiBold)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor("#E8F0F7"))

        texto = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        fondo, color_texto, color_punto = ESTADOS_RESERVA.get(
            texto, ESTADO_NEUTRO
        )

        painter.setFont(self._fuente)
        metricas = painter.fontMetrics()
        ancho_texto = metricas.horizontalAdvance(texto)
        ancho = min(max(94, ancho_texto + 38), max(94, option.rect.width() - 12))
        alto = 24
        x = option.rect.x() + (option.rect.width() - ancho) / 2
        y = option.rect.y() + (option.rect.height() - alto) / 2
        pastilla = QRectF(x, y, ancho, alto)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(fondo))
        painter.drawRoundedRect(pastilla, 12, 12)

        painter.setBrush(QColor(color_punto))
        painter.drawEllipse(QRectF(x + 11, y + 9, 6, 6))

        painter.setPen(QPen(QColor(color_texto)))
        painter.drawText(
            QRectF(x + 23, y, ancho - 29, alto),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            texto,
        )
        painter.restore()
