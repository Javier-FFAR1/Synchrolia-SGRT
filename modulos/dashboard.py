# -*- coding: utf-8 -*-
"""
Modulo: Dashboard
Panel principal con estadisticas resumen y accesos rapidos.
Muestra: reservas del dia, mesas disponibles, ocupacion actual.
"""

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QFont, QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGraphicsDropShadowEffect,
    QScrollArea
)

from modulos.encabezado_modulo import EncabezadoModulo
from modulos.almacen_datos import (
    lista_reservas, mesas_con_estado, reservas_de_hoy,
    conteo_mesas_por_estado
)

import datetime


def fecha_hoy():
    return datetime.date.today().strftime("%d/%m/%Y")

PRIMARIO = "#1B3A5C"
SECUNDARIO = "#2C5F8A"
DORADO = "#D4A843"
VERDE = "#4CAF50"
ROJO = "#BC1515"
NARANJA = "#FF9800"


class TarjetaEstadistica(QFrame):
    """Widget reutilizable para mostrar una metrica clave."""
    def __init__(self, titulo, valor, color, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.setMinimumHeight(96)

        # Sombra suave para dar profundidad
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(16)
        sombra.setOffset(0, 3)
        sombra.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Barra de color en la parte superior
        barra = QFrame()
        barra.setFixedHeight(4)
        barra.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        layout.addWidget(barra)

        # Valor numerico grande
        self.label_valor = QLabel(valor)
        self.label_valor.setFont(QFont("Raleway", 32, QFont.Weight.Bold))
        self.label_valor.setStyleSheet(f"color: {color};")
        layout.addWidget(self.label_valor)

        # Titulo descriptivo
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(lbl_titulo)

        layout.addStretch()


class BarraSegmentos(QWidget):
    """Barra horizontal segmentada (libre / en uso / mantenimiento)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(14)
        self._segmentos = []

    def set_segmentos(self, segmentos):
        self._segmentos = segmentos
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ancho = self.width()
        alto = self.height()
        radio = alto / 2.0
        rect_completo = QRectF(0, 0, ancho, alto)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#26344A"))
        p.drawRoundedRect(rect_completo, radio, radio)
        p.save()
        p.setClipRect(rect_completo)
        x = 0.0
        for color, fraccion in self._segmentos:
            if fraccion <= 0:
                continue
            w = ancho * fraccion
            p.setBrush(color)
            p.drawRect(QRectF(x, 0, w, alto))
            x += w
        p.restore()
        p.end()


class BarraOcupacion(QFrame):
    """Resumen visual de la ocupacion del local: barra segmentada + detalle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.setMinimumHeight(58)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(4)

        fila_titulo = QHBoxLayout()
        lbl_titulo = QLabel("Ocupacion del Local")
        lbl_titulo.setStyleSheet(
            "color: #1B3A5C; font-size: 12px; font-weight: 700;"
        )
        fila_titulo.addWidget(lbl_titulo)
        fila_titulo.addStretch()
        layout.addLayout(fila_titulo)

        self.barra = BarraSegmentos()
        layout.addWidget(self.barra)

        self.label_detalle = QLabel("")
        self.label_detalle.setStyleSheet(
            "color: #555555; font-size: 11px;"
        )
        layout.addWidget(self.label_detalle)

    def set_datos(self, libres, en_uso, mantenimiento):
        total = libres + en_uso + mantenimiento
        if total <= 0:
            self.barra.set_segmentos([])
            self.label_detalle.setText("Sin datos")
            return

        def frac(n):
            return n / total

        self.barra.set_segmentos([
            (QColor(VERDE), frac(libres)),
            (QColor(ROJO), frac(en_uso)),
            (QColor("#8899AA"), frac(mantenimiento)),
        ])
        porc_uso = en_uso / total * 100
        self.label_detalle.setText(
            f"{porc_uso:.0f}% de las mesas en uso  -  "
            f"{libres} libres  -  {en_uso} en uso  -  "
            f"{mantenimiento} en mantenimiento"
        )


class PanelDashboard(QWidget):
    """Panel de inicio con vista general del restaurante."""
    def __init__(self, nombre_usuario="Usuario"):
        super().__init__()
        self.nombre_usuario = nombre_usuario
        self._construir_interfaz()

    def _construir_interfaz(self):
        # Contenedor con scroll: evita que el contenido quede recortado
        area_scroll = QScrollArea(self)
        area_scroll.setWidgetResizable(True)
        area_scroll.setFrameShape(QFrame.Shape.NoFrame)
        area_scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
        )

        contenido = QWidget()
        contenido.setStyleSheet("background: transparent;")
        area_scroll.setWidget(contenido)

        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)
        layout_raiz.addWidget(area_scroll)

        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # Encabezado del panel con reloj en vivo
        encabezado = EncabezadoModulo(
            f"Bienvenido, {self.nombre_usuario}",
            "Vista general del restaurante"
        )
        layout.addWidget(encabezado)

        layout.addSpacing(8)

        # Tarjetas de estadisticas (se recalculan en _actualizar_contenido)
        grid_stats = QGridLayout()
        grid_stats.setSpacing(12)

        self.tarjeta_reservas_hoy = TarjetaEstadistica("Reservas Hoy", "0", PRIMARIO)
        self.tarjeta_mesas_libres = TarjetaEstadistica("Mesas Libres", "0", VERDE)
        self.tarjeta_mesas_ocupadas = TarjetaEstadistica("Mesas Ocupadas", "0", ROJO)
        self.tarjeta_por_confirmar = TarjetaEstadistica("Por Confirmar", "0", NARANJA)

        grid_stats.addWidget(self.tarjeta_reservas_hoy, 0, 0)
        grid_stats.addWidget(self.tarjeta_mesas_libres, 0, 1)
        grid_stats.addWidget(self.tarjeta_mesas_ocupadas, 0, 2)
        grid_stats.addWidget(self.tarjeta_por_confirmar, 0, 3)

        layout.addLayout(grid_stats)

        # Barra de ocupacion con porcentaje en vivo
        self.barra_ocupacion = BarraOcupacion()
        layout.addWidget(self.barra_ocupacion)

        # Tabla de reservas del dia
        lbl_reservas = QLabel("Reservas de Hoy")
        lbl_reservas.setObjectName("titulo")
        lbl_reservas.setStyleSheet(f"color: {PRIMARIO}; font-size: 16px; font-weight: 700; margin-top: 8px;")
        layout.addWidget(lbl_reservas)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Cliente", "Mesa", "Hora", "Personas", "Estado", "Gestiono"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setMinimumHeight(200)

        layout.addWidget(self.tabla)
        layout.addStretch()

        # Los datos se llenan desde el almacen central
        self._actualizar_contenido()

    def _actualizar_contenido(self):
        """Calcula las estadisticas y la tabla de hoy desde el almacen central."""
        reservas_hoy = reservas_de_hoy()
        conteo = conteo_mesas_por_estado()
        pendientes = sum(
            1 for r in lista_reservas
            if r.get("fecha") == fecha_hoy() and r.get("estado") == "Pendiente"
        )

        self.tarjeta_reservas_hoy.label_valor.setText(str(len(reservas_hoy)))
        self.tarjeta_mesas_libres.label_valor.setText(str(conteo["Libre"]))
        self.tarjeta_mesas_ocupadas.label_valor.setText(str(conteo["Ocupada"]))
        self.tarjeta_por_confirmar.label_valor.setText(str(pendientes))

        # Ocupacion del local (las reservadas del dia tambien cuentan como en uso)
        self.barra_ocupacion.set_datos(
            conteo["Libre"], conteo["Ocupada"] + conteo["Reservada"],
            conteo["Mantenimiento"]
        )

        # Tabla de reservas de hoy
        self.tabla.setRowCount(len(reservas_hoy))
        for fila, r in enumerate(reservas_hoy):
            datos = (
                r.get("cliente", ""), r.get("mesa", ""),
                r.get("hora_inicio", ""), r.get("personas", ""),
                r.get("estado", ""), r.get("gestiono", ""),
            )
            for col, valor in enumerate(datos):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Colorear columna de estado como badge
                if col == 4:
                    colores_estado = {
                        "Confirmada": VERDE,
                        "Pendiente": NARANJA,
                        "Cancelada": ROJO,
                    }
                    color = colores_estado.get(valor, "#888888")
                    item.setForeground(Qt.GlobalColor.white if color != NARANJA else Qt.GlobalColor.black)
                    item.setBackground(QColor(color))
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.tabla.setItem(fila, col, item)
