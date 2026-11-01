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
    QAbstractItemView, QDialog, QSizePolicy
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
        self._id_cliente_editando = None
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Encabezado
        lbl_titulo = QLabel("Gestión de Clientes")
        lbl_titulo.setObjectName("titulo")
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel("Registra clientes y consulta su historial de reservas")
        lbl_sub.setObjectName("subtitulo")
        layout.addWidget(lbl_sub)

        layout_principal = QHBoxLayout()
        layout_principal.setSpacing(16)

        # ============================================================
        # Formulario de registro/edicion
        # ============================================================
        grupo_form = QGroupBox("Datos del Cliente")
        grupo_form.setMinimumWidth(360)
        grupo_form.setMaximumWidth(400)
        grupo_form.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )

        form = QFormLayout(grupo_form)
        form.setSpacing(12)
        form.setContentsMargins(16, 24, 16, 16)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre completo")
        nombre_pattern = QRegularExpression(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' ]+$")
        self.txt_nombre.setValidator(QRegularExpressionValidator(nombre_pattern))
        self.txt_nombre.setMaxLength(100)
        form.addRow("Nombre:", self.txt_nombre)

        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Teléfono de contacto")
        self.txt_telefono.setValidator(QIntValidator(0, 99999999))
        self.txt_telefono.setMaxLength(8)
        form.addRow("Teléfono:", self.txt_telefono)

        self.txt_correo = QLineEdit()
        self.txt_correo.setPlaceholderText("Correo electrónico (opcional)")
        pattern = QRegularExpression(
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )
        self.txt_correo.setValidator(QRegularExpressionValidator(pattern))
        form.addRow("Correo:", self.txt_correo)

        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(8)

        self.btn_guardar = QPushButton("Guardar Cliente")
        self.btn_guardar.setObjectName("acento")
        self.btn_guardar.setMinimumHeight(38)
        self.btn_guardar.setMinimumWidth(150)
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.clicked.connect(self._guardar_cliente)
        layout_botones.addWidget(self.btn_guardar)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setObjectName("secundario")
        btn_limpiar.setMinimumHeight(38)
        btn_limpiar.setMinimumWidth(90)
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar.clicked.connect(self._limpiar)
        layout_botones.addWidget(btn_limpiar)

        layout_botones.addStretch()
        form.addRow(layout_botones)

        layout_principal.addWidget(
            grupo_form, 0, Qt.AlignmentFlag.AlignTop
        )

        # ============================================================
        # Tabla de clientes registrados
        # ============================================================
        layout_derecha = QVBoxLayout()

        lbl_lista = QLabel("Clientes Registrados")
        lbl_lista.setStyleSheet(
            f"color: {PRIMARIO}; font-size: 15px; font-weight: 700; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout_derecha.addWidget(lbl_lista)

        # Campo de busqueda
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre o teléfono...")
        self.txt_buscar.setMinimumHeight(36)
        self.txt_buscar.textChanged.connect(self._filtrar_clientes)
        layout_derecha.addWidget(self.txt_buscar)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Nombre", "Teléfono", "Correo", "Registro"
        ])
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(3, 200)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        for columna in range(self.tabla.columnCount()):
            item = self.tabla.horizontalHeaderItem(columna)
            if item is not None:
                alineacion = (
                    Qt.AlignmentFlag.AlignLeft
                    if columna in (1, 2, 3)
                    else Qt.AlignmentFlag.AlignCenter
                )
                item.setTextAlignment(
                    alineacion | Qt.AlignmentFlag.AlignVCenter
                )
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(38)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.itemSelectionChanged.connect(self._actualizar_acciones)

        layout_derecha.addWidget(self.tabla, 1)

        # Botones de gestion
        layout_acciones = QHBoxLayout()
        layout_acciones.setSpacing(8)

        self.btn_editar = QPushButton("Editar Seleccionado")
        self.btn_editar.setObjectName("secundario")
        self.btn_editar.setMinimumHeight(36)
        self.btn_editar.clicked.connect(self._editar_cliente)
        layout_acciones.addWidget(self.btn_editar)

        self.btn_historial = QPushButton("Ver Historial")
        self.btn_historial.setObjectName("secundario")
        self.btn_historial.setMinimumHeight(36)
        self.btn_historial.clicked.connect(self._ver_historial)
        layout_acciones.addWidget(self.btn_historial)

        layout_acciones.addStretch()

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setObjectName("peligro_borde")
        self.btn_eliminar.setMinimumHeight(36)
        self.btn_eliminar.clicked.connect(self._eliminar_cliente)
        layout_acciones.addWidget(self.btn_eliminar)

        layout_derecha.addLayout(layout_acciones)

        layout_principal.addLayout(layout_derecha, 1)

        layout.addLayout(layout_principal, 1)
        self._refrescar_tabla()

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
                item.setToolTip(str(valor))

                if col in (1, 2, 3):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                    )
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, c.get("id"))

                self.tabla.setItem(fila, col, item)

        self._actualizar_acciones()

    def _actualizar_acciones(self):
        hay_seleccion = self.tabla.currentRow() >= 0
        self.btn_editar.setEnabled(hay_seleccion)
        self.btn_eliminar.setEnabled(hay_seleccion)
        self.btn_historial.setEnabled(hay_seleccion)

    def _guardar_cliente(self):
        nombre = self.txt_nombre.text().strip()
        telefono = self.txt_telefono.text().strip()
        correo = self.txt_correo.text().strip()

        if not nombre or not telefono:
            QMessageBox.warning(self, "Campos requeridos", "Nombre y teléfono son obligatorios.")
            return

        if len(telefono) < 8:
            QMessageBox.warning(
                self,
                "Teléfono inválido",
                "El teléfono debe tener al menos 8 dígitos."
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
                    "Correo inválido",
                    "El correo electrónico no tiene un formato válido."
                )
                self.txt_correo.setFocus()
                return

        if self._telefono_en_uso(telefono, id_excluir=self._id_cliente_editando):
            if self._id_cliente_editando is None:
                mensaje = f"Ya existe un cliente registrado con el teléfono {telefono}."
            else:
                mensaje = f"Ya existe otro cliente registrado con el teléfono {telefono}."
            QMessageBox.warning(self, "Teléfono duplicado", mensaje)
            self.txt_telefono.setFocus()
            return

        if self._id_cliente_editando is not None:
            if not almacen_datos.actualizar_cliente(
                self._id_cliente_editando, nombre, telefono, correo
            ):
                QMessageBox.critical(self, "Error", "No se pudo actualizar el cliente.")
                return
            self._refrescar_tabla()
            QMessageBox.information(
                self,
                "Cliente Actualizado",
                f"Cliente '{nombre}' actualizado correctamente."
            )
            self._limpiar()
            return

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
        self._id_cliente_editando = None
        self.btn_guardar.setText("Guardar Cliente")
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
            QMessageBox.information(self, "Selección", "Seleccione un cliente para editar.")
            return
        id_cliente = int(self.tabla.item(fila, 0).text())
        self._id_cliente_editando = id_cliente
        self.txt_nombre.setText(self.tabla.item(fila, 1).text())
        self.txt_telefono.setText(self.tabla.item(fila, 2).text())
        self.txt_correo.setText(self.tabla.item(fila, 3).text())
        self.btn_guardar.setText("Actualizar Cliente")
        self.txt_nombre.setFocus()
        self.txt_nombre.selectAll()

    def _eliminar_cliente(self):
        fila = self.tabla.currentRow()
        if fila == -1:
            QMessageBox.information(self, "Selección", "Seleccione un cliente para eliminar.")
            return
        nombre = self.tabla.item(fila, 1).text()
        respuesta = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Desea eliminar al cliente '{nombre}'?",
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
            QMessageBox.information(
                self,
                "Selección",
                "Seleccione un cliente para ver su historial.",
            )
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
