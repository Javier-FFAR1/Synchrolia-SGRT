# -*- coding: utf-8 -*-
"""
Modulo: Dashboard
Panel principal con estadisticas resumen y accesos rapidos.
Muestra: reservas del dia, mesas disponibles, ocupacion actual.
"""

from PySide6.QtCore import Qt, QRectF, QEvent
from PySide6.QtGui import QFont, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGraphicsDropShadowEffect,
    QScrollArea
)

from modulos.encabezado_modulo import EncabezadoModulo
from modulos.delegados import BadgeEstadoDelegate
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
VERDE = "#2E7D32"
ROJO = "#BC1515"
NARANJA = "#FF9800"
GRIS_TEXTO = "#6B7280"


class TarjetaEstadistica(QFrame):
    """Widget reutilizable para mostrar una metrica clave."""
    def __init__(self, titulo, valor, color, detalle="", parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.setFixedHeight(132)

        # Sombra suave para dar profundidad
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(16)
        sombra.setOffset(0, 3)
        sombra.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(3)

        # Barra de color en la parte superior
        barra = QFrame()
        barra.setFixedHeight(4)
        barra.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        layout.addWidget(barra)
        layout.addStretch(1)

        # Valor numerico grande
        self.label_valor = QLabel(valor)
        fuente_valor = QFont("Segoe UI")
        fuente_valor.setPixelSize(38)
        fuente_valor.setWeight(QFont.Weight.Bold)
        self.label_valor.setFont(fuente_valor)
        self.label_valor.setStyleSheet(
            f"color: {color}; font-family: 'Segoe UI', sans-serif; "
            "font-size: 38px; font-weight: 700; background: transparent;"
        )
        layout.addWidget(self.label_valor)

        # Titulo descriptivo
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet(
            f"color: {GRIS_TEXTO}; font-size: 12px; font-weight: 600; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout.addWidget(lbl_titulo)

        # Contexto breve debajo del titulo
        self.label_detalle = QLabel(detalle)
        self.label_detalle.setStyleSheet(
            f"color: {GRIS_TEXTO}; font-size: 11px; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout.addWidget(self.label_detalle)

        layout.addStretch(1)

    def set_datos(self, valor, detalle=""):
        self.label_valor.setText(str(valor))
        self.label_detalle.setText(detalle)


class DonutOcupacion(QWidget):
    """Dona de ocupacion con el porcentaje de mesas en uso."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(164, 164)
        self._segmentos = []
        self._porcentaje = 0.0

    def set_datos(self, libres, reservadas, ocupadas, mantenimiento):
        total = libres + reservadas + ocupadas + mantenimiento
        en_uso = reservadas + ocupadas
        self._porcentaje = en_uso / total * 100 if total else 0.0
        self._segmentos = (
            [
                (QColor(VERDE), libres),
                (QColor(NARANJA), reservadas),
                (QColor(ROJO), ocupadas),
                (QColor("#8899AA"), mantenimiento),
            ]
            if total
            else []
        )
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        grosor = 16.0
        margen = grosor / 2 + 4
        rect = QRectF(
            margen, margen,
            self.width() - 2 * margen,
            self.height() - 2 * margen,
        )
        painter.setPen(QPen(
            QColor("#E5E7EB"), grosor,
            Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap,
        ))
        painter.drawEllipse(rect)

        total = sum(cantidad for _, cantidad in self._segmentos)
        if total > 0:
            inicio = 90 * 16
            for color, cantidad in self._segmentos:
                if cantidad <= 0:
                    continue
                extension = -int(round(cantidad / total * 360 * 16))
                painter.setPen(QPen(
                    color, grosor,
                    Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap,
                ))
                painter.drawArc(rect, inicio, extension)
                inicio += extension

        fuente = QFont("Segoe UI")
        fuente.setPixelSize(30)
        fuente.setWeight(QFont.Weight.Bold)
        painter.setFont(fuente)
        painter.setPen(QColor(PRIMARIO))
        painter.drawText(
            QRectF(0, self.height() / 2 - 28, self.width(), 36),
            Qt.AlignmentFlag.AlignCenter,
            f"{self._porcentaje:.0f}%",
        )

        fuente.setPixelSize(10)
        fuente.setWeight(QFont.Weight.Medium)
        painter.setFont(fuente)
        painter.setPen(QColor(GRIS_TEXTO))
        painter.drawText(
            QRectF(0, self.height() / 2 + 6, self.width(), 20),
            Qt.AlignmentFlag.AlignCenter,
            "de ocupación",
        )
        painter.end()


class TarjetaOcupacion(QFrame):
    """Tarjeta lateral con dona, leyenda y detalle de ocupacion."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tarjeta")
        self.setFixedWidth(320)
        self.setFixedHeight(384)

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(16)
        sombra.setOffset(0, 3)
        sombra.setColor(QColor(0, 0, 0, 40))
        self.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        lbl_titulo = QLabel("Ocupación del Local")
        lbl_titulo.setStyleSheet(
            "color: #1B3A5C; font-size: 15px; font-weight: 700; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout.addWidget(lbl_titulo)

        self.lbl_subtitulo = QLabel("Distribución de las mesas")
        self.lbl_subtitulo.setStyleSheet(
            f"color: {GRIS_TEXTO}; font-size: 11px; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout.addWidget(self.lbl_subtitulo)

        layout.addStretch(1)

        self.donut = DonutOcupacion()
        layout.addWidget(
            self.donut, 0, Qt.AlignmentFlag.AlignHCenter
        )

        layout.addSpacing(6)

        leyenda = QGridLayout()
        leyenda.setHorizontalSpacing(8)
        leyenda.setVerticalSpacing(6)
        leyenda.setColumnStretch(1, 1)
        self.valores = {}
        self.valores["libres"] = self._agregar_fila(
            leyenda, 0, "Libres", VERDE
        )
        self.valores["reservadas"] = self._agregar_fila(
            leyenda, 1, "Reservadas", NARANJA
        )
        self.valores["ocupadas"] = self._agregar_fila(
            leyenda, 2, "Ocupadas", ROJO
        )
        self.valores["mantenimiento"] = self._agregar_fila(
            leyenda, 3, "Mantenimiento", "#8899AA"
        )
        layout.addLayout(leyenda)

        layout.addStretch(1)

        lbl_nota = QLabel("La ocupación incluye reservadas y ocupadas.")
        lbl_nota.setWordWrap(True)
        lbl_nota.setStyleSheet(
            f"color: {GRIS_TEXTO}; font-size: 10px; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout.addWidget(lbl_nota)

    def _agregar_fila(self, layout, fila, texto, color):
        punto = QFrame()
        punto.setFixedSize(9, 9)
        punto.setStyleSheet(
            f"background-color: {color}; border-radius: 4px;"
        )
        layout.addWidget(punto, fila, 0, Qt.AlignmentFlag.AlignVCenter)

        etiqueta = QLabel(texto)
        etiqueta.setStyleSheet(
            f"color: #4B5563; font-size: 11px; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout.addWidget(etiqueta, fila, 1)

        valor = QLabel("0")
        valor.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        valor.setStyleSheet(
            f"color: {PRIMARIO}; font-size: 13px; font-weight: 700; "
            "font-family: 'Segoe UI', sans-serif;"
        )
        layout.addWidget(valor, fila, 2)
        return valor

    def set_datos(self, libres, reservadas, ocupadas, mantenimiento):
        self.donut.set_datos(libres, reservadas, ocupadas, mantenimiento)
        self.valores["libres"].setText(str(libres))
        self.valores["reservadas"].setText(str(reservadas))
        self.valores["ocupadas"].setText(str(ocupadas))
        self.valores["mantenimiento"].setText(str(mantenimiento))

        total = libres + reservadas + ocupadas + mantenimiento
        texto_mesas = "mesa" if total == 1 else "mesas"
        self.lbl_subtitulo.setText(f"Distribución de {total} {texto_mesas}")


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

        fila_inferior = QHBoxLayout()
        fila_inferior.setSpacing(16)

        columna_reservas = QVBoxLayout()
        columna_reservas.setSpacing(8)

        lbl_reservas = QLabel("Reservas de Hoy")
        lbl_reservas.setObjectName("titulo")
        lbl_reservas.setStyleSheet(
            f"color: {PRIMARIO}; font-size: 16px; font-weight: 700;"
        )
        columna_reservas.addWidget(lbl_reservas)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Cliente", "Mesa", "Hora", "Personas", "Estado", "Gestionó"
        ])
        header = self.tabla.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for columna in (1, 2, 3, 4):
            header.setSectionResizeMode(
                columna, QHeaderView.ResizeMode.ResizeToContents
            )
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tabla.setItemDelegateForColumn(4, BadgeEstadoDelegate(self.tabla))
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(36)
        self.tabla.setMaximumHeight(430)

        self.lbl_tabla_vacia = QLabel(
            "No hay reservas para hoy.", self.tabla.viewport()
        )
        self.lbl_tabla_vacia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_tabla_vacia.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self.lbl_tabla_vacia.setStyleSheet(
            f"color: {GRIS_TEXTO}; font-size: 12px; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif; "
            "background: transparent;"
        )
        self.lbl_tabla_vacia.hide()
        self.tabla.viewport().installEventFilter(self)

        columna_reservas.addWidget(self.tabla)

        nota_tabla = QLabel("Se excluyen las reservas canceladas.")
        nota_tabla.setStyleSheet(
            f"color: {GRIS_TEXTO}; font-size: 10px; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        columna_reservas.addWidget(nota_tabla)
        columna_reservas.addStretch(1)

        fila_inferior.addLayout(columna_reservas, 1)

        self.tarjeta_ocupacion = TarjetaOcupacion()
        fila_inferior.addWidget(self.tarjeta_ocupacion)

        layout.addLayout(fila_inferior)
        layout.addStretch(1)

        # Los datos se llenan desde el almacen central
        self._actualizar_contenido()

    def eventFilter(self, obj, event):
        if obj is self.tabla.viewport() and event.type() == QEvent.Type.Resize:
            self.lbl_tabla_vacia.setGeometry(obj.rect())
            self.lbl_tabla_vacia.raise_()
        return super().eventFilter(obj, event)

    def _ajustar_alto_tabla(self):
        alto_encabezado = self.tabla.horizontalHeader().sizeHint().height()
        alto_filas = (
            self.tabla.rowCount()
            * self.tabla.verticalHeader().defaultSectionSize()
        )
        alto = max(92, min(alto_encabezado + alto_filas + 4, 430))
        self.tabla.setFixedHeight(alto)
        self.lbl_tabla_vacia.setVisible(self.tabla.rowCount() == 0)
        self.lbl_tabla_vacia.setGeometry(self.tabla.viewport().rect())
        self.lbl_tabla_vacia.raise_()

    def _actualizar_contenido(self):
        """Calcula las estadisticas y la tabla de hoy desde el almacen central."""
        reservas_hoy = sorted(
            reservas_de_hoy(),
            key=lambda r: (r.get("hora_inicio", ""), r.get("mesa", "")),
        )
        conteo = conteo_mesas_por_estado()
        total_mesas = sum(conteo.values())
        total_hoy = sum(
            1 for r in lista_reservas
            if r.get("fecha") == fecha_hoy()
        )
        pendientes = sum(
            1 for r in lista_reservas
            if r.get("fecha") == fecha_hoy() and r.get("estado") == "Pendiente"
        )

        activas = len(reservas_hoy)
        texto_activas = "activa" if activas == 1 else "activas"
        self.tarjeta_reservas_hoy.set_datos(
            activas,
            f"{activas} {texto_activas} de {total_hoy} hoy",
        )
        self.tarjeta_mesas_libres.set_datos(
            conteo["Libre"],
            f"{conteo['Libre']} de {total_mesas} mesas",
        )
        self.tarjeta_mesas_ocupadas.set_datos(
            conteo["Ocupada"],
            f"{conteo['Ocupada']} de {total_mesas} mesas",
        )
        self.tarjeta_por_confirmar.set_datos(
            pendientes,
            f"{pendientes} pendiente{'s' if pendientes != 1 else ''}",
        )

        self.tarjeta_ocupacion.set_datos(
            conteo["Libre"], conteo["Reservada"], conteo["Ocupada"],
            conteo["Mantenimiento"]
        )

        # Tabla de reservas de hoy, en orden cronologico
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
                item.setToolTip(str(valor))

                if col == 4:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                self.tabla.setItem(fila, col, item)

        self._ajustar_alto_tabla()
