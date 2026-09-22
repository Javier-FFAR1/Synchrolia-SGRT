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
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

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


class MesaWidget(QFrame):
    """
    Widget visual que representa una mesa en el mapa.
    Muestra numero, capacidad y estado con color codificado.
    """
    def __init__(self, numero, capacidad, estado, zona, parent=None):
        super().__init__(parent)
        self.numero = numero
        self.capacidad = capacidad
        self.estado = estado
        self.zona = zona

        self.colores_estado = {
            "Libre": VERDE,
            "Ocupada": ROJO,
            "Reservada": NARANJA,
            "Mantenimiento": GRIS,
        }

        self.setFixedSize(110, 110)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._aplicar_estilo(estado)

        # Sombra suave bajo cada mesa
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(12)
        sombra.setOffset(0, 2)
        sombra.setColor(QColor(0, 0, 0, 60))
        self.setGraphicsEffect(sombra)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Numero de mesa
        lbl_numero = QLabel(numero)
        lbl_numero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_numero.setFont(QFont("Raleway", 18, QFont.Weight.Bold))
        lbl_numero.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(lbl_numero)

        # Capacidad
        lbl_cap = QLabel(f"{capacidad} personas")
        lbl_cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_cap.setStyleSheet("color: rgba(255,255,255,0.85); font-size: 10px; background: transparent;")
        layout.addWidget(lbl_cap)

        # Estado
        self.lbl_estado = QLabel(estado)
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet("color: white; font-size: 10px; font-weight: 600; background: transparent;")
        layout.addWidget(self.lbl_estado)

    def _aplicar_estilo(self, estado):
        color = self.colores_estado.get(estado, GRIS)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 12px;
                border: 2px solid transparent;
            }}
            QFrame:hover {{
                border: 2px solid white;
            }}
        """)

    def set_estado(self, estado):
        """Actualiza el color y el texto del estado de la mesa."""
        self.estado = estado
        self._aplicar_estilo(estado)
        self.lbl_estado.setText(estado)


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
        lbl_titulo = QLabel("Mapa Visual de Ocupacion")
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
            lbl.setStyleSheet("font-size: 12px; color: #555555;")
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

        # Limpiar el contenido previo del scroll
        from PySide6.QtWidgets import QWidget
        contenido_scroll = self._scroll.widget()
        layout_anterior = contenido_scroll.layout()
        if layout_anterior is not None:
            while layout_anterior.count():
                item = layout_anterior.takeAt(0)
                w = item.widget()
                if w is not None:
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
            grupo = QGroupBox(nombre_zona)
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
                    font-size: 14px;
                    font-weight: 700;
                }}
            """)

            grid = QGridLayout(grupo)
            grid.setSpacing(12)

            for i, m in enumerate(mesas):
                fila = i // 4
                columna = i % 4
                widget_mesa = MesaWidget(m["numero"], m["capacidad"], m["estado"], nombre_zona)
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
            f"Accion para la mesa {numero}:", opciones, 0, False
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
