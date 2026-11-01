# -*- coding: utf-8 -*-
"""
Modulo: Mesas (Mapa Visual de Ocupacion)
Muestra el estado actual de todas las mesas del restaurante organizadas por zona.
Colores: Verde=Libre, Rojo=Ocupada, Naranja=Reservada, Gris=Mantenimiento.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QGridLayout, QGroupBox,
    QScrollArea, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QPen

from modulos.almacen_datos import (
    mesas_con_estado, poner_mesa_en_mantenimiento
)

PRIMARIO = "#1B3A5C"
SECUNDARIO = "#2C5F8A"
DORADO = "#D4A843"
VERDE = "#4CAF50"
ROJO = "#BC1515"
NARANJA = "#FF9800"
GRIS = "#9E9E9E"
NEUTRO_CLARO = "#F5F5F5"

NOMBRES_ZONA = {
    "Salon Principal": "Salón Principal",
    "Area VIP": "Área VIP",
}


class MesaWidget(QWidget):
    """
    Widget visual que representa una mesa vista desde arriba.
    Dibuja la mesa y sus sillas segun la capacidad, con el color del estado.
    """
    def __init__(self, numero, capacidad, estado, zona, parent=None):
        super().__init__(parent)
        self.numero = numero
        self.capacidad = capacidad
        self.estado = estado
        self.zona = zona
        self._hover = False
        self._seleccionada = False

        self.colores_estado = {
            "Libre": VERDE,
            "Ocupada": ROJO,
            "Reservada": NARANJA,
            "Mantenimiento": GRIS,
        }

        self.setFixedSize(148, 148)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._actualizar_tooltip()

        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(14)
        sombra.setOffset(0, 3)
        sombra.setColor(QColor(0, 0, 0, 45))
        self.setGraphicsEffect(sombra)

    @property
    def _centro(self):
        return QPointF(self.width() / 2, 62)

    def _color_estado(self):
        return QColor(self.colores_estado.get(self.estado, GRIS))

    def _color_texto(self):
        if self.estado == "Reservada":
            return QColor("#3D2600")
        return QColor("#FFFFFF")

    def _actualizar_tooltip(self):
        texto_personas = "persona" if self.capacidad == 1 else "personas"
        self.setToolTip(
            f"Mesa {self.numero}\n"
            f"Zona: {NOMBRES_ZONA.get(self.zona, self.zona)}\n"
            f"Capacidad: {self.capacidad} {texto_personas}\n"
            f"Estado: {self.estado}\n\n"
            "Clic para seleccionar"
        )

    def set_estado(self, estado):
        """Actualiza el estado y repinta la mesa."""
        self.estado = estado
        self._actualizar_tooltip()
        self.update()

    def set_seleccionada(self, seleccionada):
        self._seleccionada = seleccionada
        self.update()

    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._dibujar_sillas(painter)
        self._dibujar_mesa(painter)
        self._dibujar_textos(painter)

        if self._seleccionada:
            painter.setPen(QPen(QColor(DORADO), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(
                QRectF(4, 4, self.width() - 8, self.height() - 8),
                14, 14
            )
        painter.end()

    def _dibujar_sillas(self, painter):
        painter.setPen(QPen(QColor("#AEB7C2"), 1))
        painter.setBrush(QColor("#E8ECF1"))

        if self.capacidad <= 4:
            radio_mesa = 34
            distancia = radio_mesa + 9
            for indice in range(max(self.capacidad, 1)):
                angulo = indice * 360 / max(self.capacidad, 1)
                painter.save()
                painter.translate(self._centro)
                painter.rotate(angulo)
                painter.drawRoundedRect(
                    QRectF(-7.5, -distancia - 4.5, 15, 9), 3.5, 3.5
                )
                painter.restore()
            return

        ancho, alto = self._dimensiones_mesa()
        lados = max(self.capacidad - 2, 0)
        arriba = (lados + 1) // 2
        abajo = lados // 2
        self._fila_sillas(
            painter, arriba, self._centro.y() - alto / 2 - 10, ancho
        )
        self._fila_sillas(
            painter, abajo, self._centro.y() + alto / 2 + 10, ancho
        )

        for lado in (-1, 1):
            x = self._centro.x() + lado * (ancho / 2 + 10)
            painter.drawRoundedRect(
                QRectF(x - 4.5, self._centro.y() - 9, 9, 18), 3.5, 3.5
            )

    def _fila_sillas(self, painter, cantidad, y, ancho):
        if cantidad <= 0:
            return
        paso = min(22.0, (ancho - 18) / max(cantidad - 1, 1))
        inicio = self._centro.x() - (cantidad - 1) * paso / 2
        for indice in range(cantidad):
            x = inicio + indice * paso
            painter.drawRoundedRect(
                QRectF(x - 7.5, y - 4.5, 15, 9), 3.5, 3.5
            )

    def _dimensiones_mesa(self):
        if self.capacidad <= 6:
            return 90, 56
        if self.capacidad <= 8:
            return 96, 58
        return min(110, 98 + (self.capacidad - 9) * 3), 60

    def _dibujar_mesa(self, painter):
        color = self._color_estado()
        borde = QColor("#FFFFFF") if self._hover else color.darker(135)
        painter.setPen(QPen(borde, 2.5 if self._hover else 2))
        painter.setBrush(color)

        if self.capacidad <= 4:
            painter.drawEllipse(self._centro, 34, 34)
            return

        ancho, alto = self._dimensiones_mesa()
        painter.drawRoundedRect(
            QRectF(
                self._centro.x() - ancho / 2,
                self._centro.y() - alto / 2,
                ancho,
                alto,
            ),
            11, 11
        )

    def _dibujar_textos(self, painter):
        color_texto = self._color_texto()
        fuente = QFont("Segoe UI")
        fuente.setPixelSize(21 if len(self.numero) <= 2 else 17)
        fuente.setWeight(QFont.Weight.Bold)
        painter.setFont(fuente)
        painter.setPen(color_texto)
        painter.drawText(
            QRectF(0, self._centro.y() - 23, self.width(), 30),
            Qt.AlignmentFlag.AlignCenter,
            self.numero,
        )

        fuente.setPixelSize(12)
        fuente.setWeight(QFont.Weight.DemiBold)
        painter.setFont(fuente)
        painter.setPen(color_texto)
        painter.drawText(
            QRectF(0, self._centro.y() + 8, self.width(), 18),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.capacidad} pers.",
        )

        color_estado = self._color_estado()
        if self.estado == "Reservada":
            color_estado = QColor("#9A5B00")
        fuente_estado = QFont("Raleway")
        fuente_estado.setPixelSize(13)
        fuente_estado.setWeight(QFont.Weight.DemiBold)
        painter.setFont(fuente_estado)
        painter.setPen(color_estado)
        painter.drawText(
            QRectF(0, 122, self.width(), 18),
            Qt.AlignmentFlag.AlignCenter,
            self.estado,
        )


class PanelMesas(QWidget):
    """Panel del mapa visual de ocupacion del restaurante."""

    estado_mesas_cambiado = Signal()

    def __init__(self):
        super().__init__()
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Encabezado
        lbl_titulo = QLabel("Mapa Visual de Ocupación")
        lbl_titulo.setObjectName("titulo")
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel("Estado en tiempo real de las mesas del restaurante")
        lbl_sub.setObjectName("subtitulo")
        layout.addWidget(lbl_sub)

        # Leyenda de colores
        layout_leyenda = QHBoxLayout()
        layout_leyenda.setSpacing(20)

        leyenda = [
            ("Libre", VERDE),
            ("Ocupada", ROJO),
            ("Reservada", NARANJA),
            ("Mantenimiento", GRIS),
        ]

        for texto, color in leyenda:
            layout_item = QHBoxLayout()
            layout_item.setSpacing(6)

            circulo = QFrame()
            circulo.setFixedSize(14, 14)
            circulo.setStyleSheet(f"""
                background-color: {color};
                border-radius: 7px;
                border: 1px solid #CCCCCC;
            """)
            layout_item.addWidget(circulo)

            lbl = QLabel(texto)
            lbl.setStyleSheet(
                "font-family: 'Raleway', 'Segoe UI', sans-serif; "
                "font-size: 12px; color: #555555;"
            )
            layout_item.addWidget(lbl)

            layout_leyenda.addLayout(layout_item)

        layout_leyenda.addStretch()
        layout.addLayout(layout_leyenda)

        # Zonas del restaurante
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        contenido_scroll = QWidget()
        layout_scroll = QVBoxLayout(contenido_scroll)
        layout_scroll.setContentsMargins(0, 8, 0, 8)
        layout_scroll.setSpacing(16)

        self._scroll.setWidget(contenido_scroll)

        # Mapa de mesas construido desde el almacen central (estado derivado
        # de las reservas). self.widgets_mesas guarda la referencia de cada
        # mesa para actualizar el color sin reconstruir la interfaz.
        self.widgets_mesas = {}
        self._construir_mapa()
        self._firma_mapa = self._calcular_firma()

        layout.addWidget(self._scroll)

        # Botones de accion inferiores
        layout_acciones = QHBoxLayout()

        btn_actualizar = QPushButton("Actualizar Mapa")
        btn_actualizar.setMinimumHeight(38)
        btn_actualizar.clicked.connect(self._actualizar_mapa)
        layout_acciones.addWidget(btn_actualizar)

        btn_cambiar_estado = QPushButton("Cambiar Estado Mesa")
        btn_cambiar_estado.setMinimumHeight(38)
        btn_cambiar_estado.clicked.connect(self._cambiar_estado)
        layout_acciones.addWidget(btn_cambiar_estado)

        layout_acciones.addStretch()
        layout.addLayout(layout_acciones)

    def _construir_mapa(self):
        """(Re)construye el mapa con las mesas y su estado derivado."""
        # Agrupar mesas por zona preservando orden del catalogo
        self.widgets_mesas.clear()
        self._mesa_seleccionada = None

        # Limpiar el contenido previo del scroll
        from PySide6.QtWidgets import QWidget
        contenido_scroll = self._scroll.widget()
        layout_anterior = contenido_scroll.layout()
        if layout_anterior is not None:
            while layout_anterior.count():
                item = layout_anterior.takeAt(0)
                w = item.widget()
                if w is not None:
                    w.hide()
                    w.setParent(None)
                    w.deleteLater()
                elif item.layout() is not None:
                    pass

        layout_scroll = contenido_scroll.layout()
        if layout_scroll is None:
            layout_scroll = QVBoxLayout(contenido_scroll)

        zonas = {}
        for m in mesas_con_estado():
            zonas.setdefault(m["zona"], []).append(m)

        for nombre_zona, mesas in zonas.items():
            nombre_visible = NOMBRES_ZONA.get(nombre_zona, nombre_zona)
            grupo = QGroupBox(nombre_visible)
            grupo.setStyleSheet(f"""
                QGroupBox {{
                    background-color: white;
                    border: 1px solid #E0E0E0;
                    border-radius: 10px;
                    margin-top: 12px;
                    padding: 16px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 16px;
                    padding: 0 8px;
                    color: {PRIMARIO};
                    font-family: 'Raleway', 'Segoe UI', sans-serif;
                    font-size: 14px;
                    font-weight: 700;
                }}
            """)

            grid = QGridLayout(grupo)
            grid.setSpacing(14)

            for i, m in enumerate(mesas):
                fila = i // 4
                columna = i % 4
                widget_mesa = MesaWidget(
                    m["numero"], m["capacidad"], m["estado"], nombre_zona
                )
                widget_mesa.mousePressEvent = lambda e, num=m["numero"]: self._seleccionar_mesa(num)
                grid.addWidget(widget_mesa, fila, columna)
                self.widgets_mesas[m["numero"]] = widget_mesa

            layout_scroll.addWidget(grupo)

    def _calcular_firma(self):
        """Firma (zona, numero, capacidad) de las mesas ya dibujadas en el mapa."""
        return tuple(sorted(
            (w.zona, w.numero, w.capacidad) for w in self.widgets_mesas.values()
        ))

    def _seleccionar_mesa(self, numero):
        self._mesa_seleccionada = numero
        for numero_mesa, widget in self.widgets_mesas.items():
            widget.set_seleccionada(numero_mesa == numero)

    def _refrescar_mapa(self):
        """Recalcula el mapa desde las reservas.

        Si se agregaron o eliminaron areas/mesas, o se edito su capacidad o
        area, reconstruye toda la interfaz; en caso contrario solo actualiza
        el color/estado de cada mesa ya dibujada.
        """
        props = mesas_con_estado()
        firma = tuple(sorted(
            (m["zona"], m["numero"], m["capacidad"]) for m in props
        ))
        if firma != self._firma_mapa:
            self._construir_mapa()
            self._firma_mapa = self._calcular_firma()
            return
        for m in props:
            widget = self.widgets_mesas.get(m["numero"])
            if widget is not None:
                widget.set_estado(m["estado"])

    def _actualizar_mapa(self):
        """Actualiza el mapa y notifica al usuario (boton manual)."""
        self._refrescar_mapa()
        QMessageBox.information(
            self,
            "Mapa Actualizado",
            "El mapa se actualizo segun el estado actual de las reservas."
        )

    def _cambiar_estado(self):
        """Permite marcar/desmarcar la mesa seleccionada como mantenimiento."""
        numero = getattr(self, "_mesa_seleccionada", None)
        if numero is None:
            QMessageBox.information(
                self, "Sin seleccion",
                "Haga clic sobre una mesa para seleccionarla."
            )
            return
        opciones = ["Mantenimiento", "Disponible (Quitar mantenimiento)"]
        from PySide6.QtWidgets import QInputDialog
        opcion, ok = QInputDialog.getItem(
            self, "Cambiar Estado Mesa",
            f"Acción para la mesa {numero}:", opciones, 0, False
        )
        if not ok:
            return
        if opcion.startswith("Mantenimiento"):
            # Guarda: no poner en mantenimiento una mesa ocupada/reservada
            from modulos.almacen_datos import estado_mesa, ESTADO_MESA_OCUPADA, ESTADO_MESA_RESERVADA
            st = estado_mesa(numero)
            if st in (ESTADO_MESA_OCUPADA, ESTADO_MESA_RESERVADA):
                QMessageBox.warning(
                    self, "Mesa en uso",
                    f"La mesa {numero} tiene una reserva activa ({st}).\n\n"
                    "No se puede poner en mantenimiento mientras este en uso."
                )
                return
            respuesta = QMessageBox.question(
                self, "Poner en mantenimiento",
                f"Desea poner la mesa {numero} en mantenimiento?\n\n"
                "Mientras este en mantenimiento no podra asignarse a reservas.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if respuesta != QMessageBox.StandardButton.Yes:
                return
            poner_mesa_en_mantenimiento(numero, True)
        else:
            poner_mesa_en_mantenimiento(numero, False)
        self._actualizar_mapa()
        self.estado_mesas_cambiado.emit()
        QMessageBox.information(
            self, "Estado actualizado",
            f"Mesa {numero}: {opcion}."
        )
