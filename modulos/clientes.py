# -*- coding: utf-8 -*-
"""
Modulo: Clientes
CRUD completo de clientes del restaurante.
Permite registrar, buscar, modificar y consultar historial de reservas.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFormLayout, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QGroupBox,
    QAbstractItemView, QDialog
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QFont, QIntValidator, QRegularExpressionValidator

from modulos import almacen_datos
from modulos.almacen_datos import lista_clientes, lista_reservas

PRIMARIO = "#1B3A5C"


class PanelClientes(QWidget):
    """Panel de gestion de clientes."""
    def __init__(self):
        super().__init__()
        # Fuente unica: la misma lista que usa el almacen central.
        self.lista_clientes = lista_clientes
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Encabezado
        lbl_titulo = QLabel("Gestion de Clientes")
        lbl_titulo.setObjectName("titulo")
        layout.addWidget(lbl_titulo)

        layout_principal = QHBoxLayout()
        layout_principal.setSpacing(16)

        # ============================================================
        # Formulario de registro/edicion
        # ============================================================
        grupo_form = QGroupBox("Datos del Cliente")
        grupo_form.setMinimumWidth(380)
        grupo_form.setMaximumWidth(420)

        form = QFormLayout(grupo_form)
        form.setSpacing(10)
        form.setContentsMargins(16, 24, 16, 16)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre completo")
        nombre_pattern = QRegularExpression(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' ]+$")
        self.txt_nombre.setValidator(QRegularExpressionValidator(nombre_pattern))
        self.txt_nombre.setMaxLength(100)
        form.addRow("Nombre:", self.txt_nombre)

        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Telefono de contacto")
        self.txt_telefono.setValidator(QIntValidator(0, 99999999))
        self.txt_telefono.setMaxLength(8)
        form.addRow("Telefono:", self.txt_telefono)

        self.txt_correo = QLineEdit()
        self.txt_correo.setPlaceholderText("Correo electronico (opcional)")
        pattern = QRegularExpression(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )
        self.txt_correo.setValidator(QRegularExpressionValidator(pattern))
        form.addRow("Correo:", self.txt_correo)

        layout_botones = QHBoxLayout()

        btn_guardar = QPushButton("Guardar Cliente")
        btn_guardar.setObjectName("acento")
        btn_guardar.setMinimumHeight(38)
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.clicked.connect(self._guardar_cliente)
        layout_botones.addWidget(btn_guardar)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setObjectName("secundario")
        btn_limpiar.setMinimumHeight(38)
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar.clicked.connect(self._limpiar)
        layout_botones.addWidget(btn_limpiar)

        form.addRow(layout_botones)

        layout_principal.addWidget(grupo_form)

        # ============================================================
        # Tabla de clientes registrados
        # ============================================================
        layout_derecha = QVBoxLayout()

        lbl_lista = QLabel("Clientes Registrados")
        lbl_lista.setStyleSheet(f"color: {PRIMARIO}; font-size: 16px; font-weight: 700;")
        layout_derecha.addWidget(lbl_lista)

        # Campo de busqueda
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre o telefono...")
        self.txt_buscar.setMinimumHeight(36)
        self.txt_buscar.textChanged.connect(self._filtrar_clientes)
        layout_derecha.addWidget(self.txt_buscar)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Nombre", "Telefono", "Correo", "Registro"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)

        layout_derecha.addWidget(self.tabla)
        self._refrescar_tabla()

        # Botones de gestion
        layout_acciones = QHBoxLayout()

        btn_editar = QPushButton("Editar Seleccionado")
        btn_editar.setMinimumHeight(36)
        btn_editar.clicked.connect(self._editar_cliente)
        layout_acciones.addWidget(btn_editar)

        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setObjectName("peligro")
        btn_eliminar.setMinimumHeight(36)
        btn_eliminar.clicked.connect(self._eliminar_cliente)
        layout_acciones.addWidget(btn_eliminar)

        btn_historial = QPushButton("Ver Historial")
        btn_historial.setMinimumHeight(36)
        btn_historial.clicked.connect(self._ver_historial)
        layout_acciones.addWidget(btn_historial)

        layout_derecha.addLayout(layout_acciones)

        layout_principal.addLayout(layout_derecha)

        layout.addLayout(layout_principal)
        layout.addStretch()

    def _refrescar_tabla(self):
        """Vuelca la lista de clientes (fuente unica) a la tabla."""
        self.tabla.setRowCount(len(self.lista_clientes))
        for fila, c in enumerate(self.lista_clientes):
            datos = (
                str(c.get("id", "")),
                c.get("nombre", ""),
                c.get("telefono", ""),
                c.get("correo", ""),
                c.get("registro", ""),
            )
            for col, valor in enumerate(datos):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(fila, col, item)

    def _guardar_cliente(self):
        nombre = self.txt_nombre.text().strip()
        telefono = self.txt_telefono.text().strip()
        correo = self.txt_correo.text().strip()

        if not nombre or not telefono:
            QMessageBox.warning(self, "Campos requeridos", "Nombre y telefono son obligatorios.")
            return

        if len(telefono) < 8:
            QMessageBox.warning(
                self,
                "Telefono invalido",
                "El telefono debe tener al menos 8 digitos."
            )
            self.txt_telefono.setFocus()
            return

        # Validar correo si el usuario lo ingreso (campo opcional)
        if correo:
            patron = QRegularExpression(
                r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
            )
            if not patron.match(correo).hasMatch():
                QMessageBox.warning(
                    self,
                    "Correo invalido",
                    "El correo electronico no tiene un formato valido."
                )
                self.txt_correo.setFocus()
                return

        if self._telefono_en_uso(telefono):
            QMessageBox.warning(
                self,
                "Telefono duplicado",
                f"Ya existe un cliente registrado con el telefono {telefono}."
            )
            self.txt_telefono.setFocus()
            return

        from datetime import date
        # Insertar el cliente en la base de datos y actualizar la cache
        ok, nid, error = almacen_datos.crear_cliente(nombre, telefono, correo)
        if not ok:
            QMessageBox.critical(self, "Error", error or "No se pudo guardar el cliente.")
            return
        self._refrescar_tabla()

        QMessageBox.information(
            self,
            "Cliente Guardado",
            f"Cliente '{nombre}' registrado exitosamente."
        )
        self._limpiar()

    def _telefono_en_uso(self, telefono, id_excluir=None):
        for c in self.lista_clientes:
            if c.get("telefono") == telefono and c.get("id") != id_excluir:
                return True
        return False

    def _limpiar(self):
        self.txt_nombre.clear()
        self.txt_telefono.clear()
        self.txt_correo.clear()

    def _filtrar_clientes(self, texto):
        """Filtra la tabla segun el texto ingresado en el campo de busqueda."""
        texto_lower = texto.lower()
        for fila in range(self.tabla.rowCount()):
            visible = False
            for col in range(self.tabla.columnCount()):
                item = self.tabla.item(fila, col)
                if item and texto_lower in item.text().lower():
                    visible = True
                    break
            self.tabla.setRowHidden(fila, not visible)

    def _editar_cliente(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.information(self, "Seleccion", "Seleccione un cliente para editar.")
            return
        id_cliente = int(self.tabla.item(fila, 0).text())
        nombre = self.tabla.item(fila, 1).text()
        self.txt_nombre.setText(self.tabla.item(fila, 1).text())
        self.txt_telefono.setText(self.tabla.item(fila, 2).text())
        self.txt_correo.setText(self.tabla.item(fila, 3).text())

        respuesta = QMessageBox.question(
            self,
            "Editar Cliente",
            f"Actualizar los datos del cliente '{nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            nuevo_nombre = self.txt_nombre.text().strip()
            nuevo_telefono = self.txt_telefono.text().strip()
            nuevo_correo = self.txt_correo.text().strip()
            if not nuevo_nombre or not nuevo_telefono:
                QMessageBox.warning(self, "Campos requeridos", "Nombre y telefono son obligatorios.")
                return
            if len(nuevo_telefono) < 8:
                QMessageBox.warning(
                    self,
                    "Telefono invalido",
                    "El telefono debe tener al menos 8 digitos."
                )
                self.txt_telefono.setFocus()
                return
            if nuevo_correo:
                patron = QRegularExpression(
                    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
                )
                if not patron.match(nuevo_correo).hasMatch():
                    QMessageBox.warning(
                        self,
                        "Correo invalido",
                        "El correo electronico no tiene un formato valido."
                    )
                    self.txt_correo.setFocus()
                    return
            if self._telefono_en_uso(nuevo_telefono, id_excluir=id_cliente):
                QMessageBox.warning(
                    self,
                    "Telefono duplicado",
                    f"Ya existe otro cliente registrado con el telefono {nuevo_telefono}."
                )
                self.txt_telefono.setFocus()
                return
            if not almacen_datos.actualizar_cliente(id_cliente, nuevo_nombre, nuevo_telefono, nuevo_correo):
                QMessageBox.critical(self, "Error", "No se pudo actualizar el cliente.")
                return
            self._refrescar_tabla()
            QMessageBox.information(
                self,
                "Cliente Actualizado",
                f"Cliente '{nuevo_nombre}' actualizado correctamente."
            )
            self._limpiar()
        else:
            self._limpiar()

    def _eliminar_cliente(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.information(self, "Seleccion", "Seleccione un cliente para eliminar.")
            return
        nombre = self.tabla.item(fila, 1).text()
        respuesta = QMessageBox.question(
            self,
            "Confirmar Eliminacion",
            f"Desea eliminar al cliente '{nombre}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            id_cliente = int(self.tabla.item(fila, 0).text())
            # Bloquear si el cliente tiene reservas activas (evita datos huerfanos)
            from modulos.almacen_datos import lista_reservas, ESTADO_CANCELADA
            activas = [
                r for r in lista_reservas
                if r.get("id_cliente") == id_cliente
                and r.get("estado") != ESTADO_CANCELADA
            ]
            if activas:
                QMessageBox.warning(
                    self,
                    "Cliente con reservas",
                    f"El cliente '{nombre}' tiene {len(activas)} reserva(s) activa(s).\n\n"
                    "No se puede eliminar mientras tenga reservas vigentes."
                )
                return
            if not almacen_datos.eliminar_cliente(id_cliente):
                QMessageBox.warning(
                    self,
                    "No se puede eliminar",
                    f"No se pudo eliminar al cliente '{nombre}'.\n"
                    "Verifique que no tenga reservas vinculadas."
                )
                return
            self._refrescar_tabla()
            QMessageBox.information(self, "Eliminado", f"Cliente '{nombre}' eliminado.")
            self._limpiar()

    def _ver_historial(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.information(self, "Seleccion", "Seleccione un cliente para ver su historial.")
            return
        id_cliente = int(self.tabla.item(fila, 0).text())
        nombre = self.tabla.item(fila, 1).text()

        reservas_cliente = sorted(
            [r for r in lista_reservas if r.get("id_cliente") == id_cliente],
            key=lambda r: (r.get("fecha", ""), r.get("hora_inicio", "")),
            reverse=True,
        )

        dialogo = QDialog(self)
        dialogo.setWindowTitle(f"Historial de Reservas - {nombre}")
        dialogo.resize(760, 430)

        layout_dialogo = QVBoxLayout(dialogo)
        layout_dialogo.setContentsMargins(16, 16, 16, 16)
        layout_dialogo.setSpacing(10)

        lbl_info = QLabel(
            f"Cliente: {nombre}   |   Total de reservas: {len(reservas_cliente)}"
        )
        lbl_info.setStyleSheet(f"color: {PRIMARIO}; font-weight: 700; font-size: 14px;")
        layout_dialogo.addWidget(lbl_info)

        tabla_historial = QTableWidget()
        tabla_historial.setColumnCount(8)
        tabla_historial.setHorizontalHeaderLabels([
            "ID", "Mesa", "Fecha", "Inicio", "Fin", "Personas", "Estado", "Observaciones"
        ])
        tabla_historial.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        tabla_historial.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla_historial.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla_historial.verticalHeader().setVisible(False)
        tabla_historial.setAlternatingRowColors(True)

        tabla_historial.setRowCount(len(reservas_cliente))
        for fil, r in enumerate(reservas_cliente):
            valores = [
                str(r.get("id", "")),
                r.get("mesa", ""),
                r.get("fecha", ""),
                r.get("hora_inicio", ""),
                r.get("hora_fin", ""),
                str(r.get("personas", "")),
                r.get("estado", ""),
                r.get("observaciones", "") or "-",
            ]
            for col, valor in enumerate(valores):
                item = QTableWidgetItem(valor)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                tabla_historial.setItem(fil, col, item)

        layout_dialogo.addWidget(tabla_historial)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("secundario")
        btn_cerrar.setMinimumHeight(36)
        btn_cerrar.setMinimumWidth(120)
        btn_cerrar.clicked.connect(dialogo.accept)
        layout_dialogo.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

        dialogo.exec()
