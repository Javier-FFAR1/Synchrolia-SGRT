# -*- coding: utf-8 -*-
"""
Modulo: Configuracion
Parametros generales del sistema: horarios de atencion, duracion estandar
de reservas, dias festivos y gestion de usuarios del sistema.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFormLayout, QLineEdit, QTimeEdit, QComboBox,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QCheckBox, QAbstractItemView,
    QTabWidget, QInputDialog, QDialog, QSpinBox
)
from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QFont, QIntValidator, QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression

from modulos.almacen_usuarios import almacen as almacen_usuarios
from modulos.almacen_configuracion import almacen_config
from modulos import almacen_datos
from modulos import notificaciones

PRIMARIO = "#1B3A5C"
DIAS_VISIBLES = {"Miercoles": "Miércoles", "Sabado": "Sábado"}
DIAS_CLAVES = {visible: clave for clave, visible in DIAS_VISIBLES.items()}
ZONAS_VISIBLES = {
    "Salon Principal": "Salón Principal",
    "Area VIP": "Área VIP",
}


class PanelConfiguracion(QWidget):
    """Panel de configuracion general del sistema."""
    def __init__(self):
        super().__init__()
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Encabezado
        lbl_titulo = QLabel("Configuración del Sistema")
        lbl_titulo.setObjectName("titulo")
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel("Horarios, parámetros, áreas, festivos y usuarios")
        lbl_sub.setObjectName("subtitulo")
        layout.addWidget(lbl_sub)

        # Pestañas de configuracion
        tabs = QTabWidget()

        # ============================================================
        # TAB 1: Horarios de Atencion
        # ============================================================
        tab_horarios = QWidget()
        layout_horarios = QVBoxLayout(tab_horarios)
        layout_horarios.setContentsMargins(16, 16, 16, 16)

        lbl_horarios = QLabel("Horarios de Atención por Día")
        lbl_horarios.setStyleSheet(
            f"color: {PRIMARIO}; font-size: 15px; font-weight: 700; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout_horarios.addWidget(lbl_horarios)

        self.tabla_horarios = QTableWidget()
        self.tabla_horarios.setColumnCount(4)
        self.tabla_horarios.setHorizontalHeaderLabels([
            "Día", "Apertura", "Cierre", "Cerrado"
        ])
        self.tabla_horarios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_horarios.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.tabla_horarios.verticalHeader().setVisible(False)
        self.tabla_horarios.verticalHeader().setDefaultSectionSize(36)
        self.tabla_horarios.setAlternatingRowColors(True)

        dias_semana = [
            (h["dia"], h["apertura"], h["cierre"], bool(h["cerrado"]))
            for h in almacen_config.obtener_horarios()
        ]

        self.tabla_horarios.setRowCount(len(dias_semana))
        for fila, (dia, apertura, cierre, cerrado) in enumerate(dias_semana):
            item_dia = QTableWidgetItem(DIAS_VISIBLES.get(dia, dia))
            item_dia.setData(Qt.ItemDataRole.UserRole, dia)
            item_dia.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_horarios.setItem(fila, 0, item_dia)

            item_ap = QTableWidgetItem(apertura)
            item_ap.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_horarios.setItem(fila, 1, item_ap)

            item_ci = QTableWidgetItem(cierre)
            item_ci.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_horarios.setItem(fila, 2, item_ci)

            item_cerrado = QTableWidgetItem("Sí" if cerrado else "No")
            item_cerrado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_horarios.setItem(fila, 3, item_cerrado)

        layout_horarios.addWidget(self.tabla_horarios, 1)

        btn_guardar_horarios = QPushButton("Guardar Horarios")
        btn_guardar_horarios.setObjectName("acento")
        btn_guardar_horarios.setMinimumHeight(36)
        btn_guardar_horarios.setMinimumWidth(180)
        btn_guardar_horarios.clicked.connect(self._guardar_horarios)
        layout_horarios.addWidget(
            btn_guardar_horarios, 0, Qt.AlignmentFlag.AlignRight
        )

        tabs.addTab(tab_horarios, "Horarios de Atención")

        # ============================================================
        # TAB 2: Parametros del Sistema
        # ============================================================
        tab_parametros = QWidget()
        layout_param = QVBoxLayout(tab_parametros)
        layout_param.setContentsMargins(16, 16, 16, 16)

        grupo_general = QGroupBox("Parámetros Generales")
        form_param = QFormLayout(grupo_general)
        form_param.setSpacing(12)
        form_param.setContentsMargins(16, 24, 16, 16)

        params = almacen_config.obtener_parametros()

        self.txt_duracion = QLineEdit(params["duracion"])
        self.txt_duracion.setPlaceholderText("Duración en minutos")
        self.txt_duracion.setMaximumWidth(120)
        self.txt_duracion.setValidator(QIntValidator(1, 999))
        form_param.addRow("Duración estándar de reserva (min):", self.txt_duracion)

        self.txt_tolerancia = QLineEdit(params["tolerancia"])
        self.txt_tolerancia.setPlaceholderText("Minutos de tolerancia")
        self.txt_tolerancia.setMaximumWidth(120)
        self.txt_tolerancia.setValidator(QIntValidator(0, 999))
        form_param.addRow("Tolerancia (min):", self.txt_tolerancia)

        self.txt_limite_confirmacion = QLineEdit(params["limite_confirmacion"])
        self.txt_limite_confirmacion.setPlaceholderText("Minutos antes del inicio")
        self.txt_limite_confirmacion.setMaximumWidth(120)
        self.txt_limite_confirmacion.setValidator(QIntValidator(1, 999))
        form_param.addRow(
            "Cancelar reserva pendiente si faltan (min):",
            self.txt_limite_confirmacion,
        )

        self.txt_max_personas = QLineEdit(params["max_personas"])
        self.txt_max_personas.setPlaceholderText("Máximo por reserva")
        self.txt_max_personas.setMaximumWidth(120)
        self.txt_max_personas.setValidator(QIntValidator(1, 999))
        form_param.addRow("Máximo de personas por reserva:", self.txt_max_personas)

        layout_param.addWidget(grupo_general)

        grupo_notif = QGroupBox("Notificaciones")
        layout_notif = QVBoxLayout(grupo_notif)
        layout_notif.setContentsMargins(16, 24, 16, 16)

        self.chk_email = QCheckBox("Enviar confirmación por correo electrónico")
        self.chk_email.setChecked(bool(params["email_notif"]))
        layout_notif.addWidget(self.chk_email)

        self.chk_recordatorio = QCheckBox(
            "Enviar recordatorio 1 hora antes (solo reservas confirmadas)"
        )
        self.chk_recordatorio.setChecked(bool(params["recordatorio"]))
        layout_notif.addWidget(self.chk_recordatorio)

        self.lbl_smtp = QLabel()
        self.lbl_smtp.setWordWrap(True)
        layout_notif.addWidget(self.lbl_smtp)

        self._actualizar_estado_smtp()

        layout_param.addWidget(grupo_notif)

        btn_guardar_param = QPushButton("Guardar Parámetros")
        btn_guardar_param.setObjectName("acento")
        btn_guardar_param.setMinimumHeight(36)
        btn_guardar_param.setMinimumWidth(180)
        btn_guardar_param.clicked.connect(self._guardar_parametros)
        layout_param.addWidget(
            btn_guardar_param, 0, Qt.AlignmentFlag.AlignRight
        )

        layout_param.addStretch()

        tabs.addTab(tab_parametros, "Parámetros del Sistema")

        # ============================================================
        # TAB 3: Anticipacion de Reservas
        # ============================================================
        tab_anticipacion = QWidget()
        layout_ant = QVBoxLayout(tab_anticipacion)
        layout_ant.setContentsMargins(16, 16, 16, 16)
        layout_ant.setSpacing(12)

        grupo_estandar = QGroupBox("Límite Estándar de Anticipación")
        form_estandar = QFormLayout(grupo_estandar)
        form_estandar.setSpacing(12)
        form_estandar.setContentsMargins(16, 24, 16, 16)

        self.spin_dias_estandar = QSpinBox()
        self.spin_dias_estandar.setRange(1, 360)
        self.spin_dias_estandar.setFixedWidth(110)
        self.spin_dias_estandar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spin_dias_estandar.setValue(almacen_config.obtener_dias_estandar())
        form_estandar.addRow("Días máx. sin requisitos:", self.spin_dias_estandar)

        lbl_note_estandar = QLabel(
            "Las reservas dentro de este límite no exigen condiciones especiales. "
            "Las zonas con mayor anticipación pueden requerir un depósito."
        )
        lbl_note_estandar.setWordWrap(True)
        lbl_note_estandar.setStyleSheet("color: #888888; font-size: 11px;")
        form_estandar.addRow("", lbl_note_estandar)

        layout_ant.addWidget(grupo_estandar)

        grupo_zonas = QGroupBox("Límites por Zona del Restaurante")
        layout_zonas = QVBoxLayout(grupo_zonas)
        layout_zonas.setContentsMargins(16, 24, 16, 16)

        self.tabla_limites = QTableWidget()
        self.tabla_limites.setColumnCount(4)
        self.tabla_limites.setHorizontalHeaderLabels([
            "Zona", "Máx. anticipación (días)", "Requiere depósito", "Depósito (%)"
        ])
        self.tabla_limites.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_limites.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tabla_limites.verticalHeader().setVisible(False)
        self.tabla_limites.verticalHeader().setDefaultSectionSize(58)
        self.tabla_limites.setAlternatingRowColors(True)
        layout_zonas.addWidget(self.tabla_limites, 1)

        self._cargar_zonas_anticipacion()

        btn_guardar_ant = QPushButton("Guardar Anticipación")
        btn_guardar_ant.setObjectName("acento")
        btn_guardar_ant.setMinimumHeight(36)
        btn_guardar_ant.setMinimumWidth(190)
        btn_guardar_ant.clicked.connect(self._guardar_anticipacion)
        layout_zonas.addWidget(
            btn_guardar_ant, 0, Qt.AlignmentFlag.AlignRight
        )

        layout_ant.addWidget(grupo_zonas, 1)

        tabs.addTab(tab_anticipacion, "Anticipación de Reservas")

        # ============================================================
        # TAB 4: Mesas y Areas
        # ============================================================
        tab_mesas = QWidget()
        layout_mesas = QVBoxLayout(tab_mesas)
        layout_mesas.setContentsMargins(16, 16, 16, 16)
        layout_mesas.setSpacing(12)

        filas_crud = QHBoxLayout()
        filas_crud.setSpacing(12)

        # --- Areas del local ---
        grupo_areas = QGroupBox("Áreas del Local")
        layout_area = QVBoxLayout(grupo_areas)
        layout_area.setContentsMargins(16, 24, 16, 16)

        self.tabla_areas = QTableWidget()
        self.tabla_areas.setColumnCount(1)
        self.tabla_areas.setHorizontalHeaderLabels(["Área"])
        self.tabla_areas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_areas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_areas.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tabla_areas.verticalHeader().setVisible(False)
        self.tabla_areas.verticalHeader().setDefaultSectionSize(36)
        self.tabla_areas.setAlternatingRowColors(True)
        layout_area.addWidget(self.tabla_areas, 1)

        fila_btn_area = QHBoxLayout()
        fila_btn_area.setSpacing(6)
        btn_area_nueva = QPushButton("Nueva Área")
        btn_area_nueva.setMinimumHeight(34)
        btn_area_nueva.clicked.connect(self._nueva_area)
        btn_area_renombrar = QPushButton("Renombrar")
        btn_area_renombrar.setObjectName("secundario")
        btn_area_renombrar.setMinimumHeight(34)
        btn_area_renombrar.clicked.connect(self._renombrar_area)
        btn_area_eliminar = QPushButton("Eliminar")
        btn_area_eliminar.setObjectName("peligro_borde")
        btn_area_eliminar.setMinimumHeight(34)
        btn_area_eliminar.clicked.connect(self._eliminar_area)
        fila_btn_area.addWidget(btn_area_nueva)
        fila_btn_area.addWidget(btn_area_renombrar)
        fila_btn_area.addWidget(btn_area_eliminar)
        layout_area.addLayout(fila_btn_area)

        filas_crud.addWidget(grupo_areas, 1)

        # --- Mesas ---
        grupo_mesas = QGroupBox("Mesas")
        layout_mesa_g = QVBoxLayout(grupo_mesas)
        layout_mesa_g.setContentsMargins(16, 24, 16, 16)

        self.tabla_mesas = QTableWidget()
        self.tabla_mesas.setColumnCount(3)
        self.tabla_mesas.setHorizontalHeaderLabels(["Número", "Capacidad", "Área"])
        self.tabla_mesas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_mesas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_mesas.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tabla_mesas.verticalHeader().setVisible(False)
        self.tabla_mesas.verticalHeader().setDefaultSectionSize(36)
        self.tabla_mesas.setAlternatingRowColors(True)
        layout_mesa_g.addWidget(self.tabla_mesas, 1)

        fila_btn_mesa = QHBoxLayout()
        fila_btn_mesa.setSpacing(6)
        btn_mesa_nueva = QPushButton("Nueva Mesa")
        btn_mesa_nueva.setMinimumHeight(34)
        btn_mesa_nueva.clicked.connect(self._nueva_mesa)
        btn_mesa_editar = QPushButton("Editar")
        btn_mesa_editar.setObjectName("secundario")
        btn_mesa_editar.setMinimumHeight(34)
        btn_mesa_editar.clicked.connect(self._editar_mesa)
        btn_mesa_eliminar = QPushButton("Eliminar")
        btn_mesa_eliminar.setObjectName("peligro_borde")
        btn_mesa_eliminar.setMinimumHeight(34)
        btn_mesa_eliminar.clicked.connect(self._eliminar_mesa)
        fila_btn_mesa.addWidget(btn_mesa_nueva)
        fila_btn_mesa.addWidget(btn_mesa_editar)
        fila_btn_mesa.addWidget(btn_mesa_eliminar)
        layout_mesa_g.addLayout(fila_btn_mesa)

        filas_crud.addWidget(grupo_mesas, 1)

        layout_mesas.addLayout(filas_crud, 1)

        lbl_note_mesas = QLabel(
            "El sistema se adapta al local: cada restaurante define sus propias "
            "áreas (salón, terraza, VIP, etc.) y la cantidad y capacidad de sus mesas. "
            "Los cambios se reflejan al instante en el mapa, las reservas y los reportes."
        )
        lbl_note_mesas.setWordWrap(True)
        lbl_note_mesas.setStyleSheet("color: #888888; font-size: 11px;")
        layout_mesas.addWidget(lbl_note_mesas)

        self._areas = []
        self._mesas = []
        self._cargar_areas()
        self._cargar_mesas()

        tabs.addTab(tab_mesas, "Mesas y Áreas")

        # ============================================================
        # TAB 5: Dias Festivos
        # ============================================================
        tab_festivos = QWidget()
        layout_festivos = QVBoxLayout(tab_festivos)
        layout_festivos.setContentsMargins(16, 16, 16, 16)

        lbl_festivos = QLabel("Días Festivos / No Laborables")
        lbl_festivos.setStyleSheet(
            f"color: {PRIMARIO}; font-size: 15px; font-weight: 700; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout_festivos.addWidget(lbl_festivos)

        self.tabla_festivos = QTableWidget()
        self.tabla_festivos.setColumnCount(3)
        self.tabla_festivos.setHorizontalHeaderLabels(["Fecha", "Descripción", "Acción"])
        self.tabla_festivos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_festivos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_festivos.verticalHeader().setVisible(False)
        self.tabla_festivos.verticalHeader().setDefaultSectionSize(36)
        self.tabla_festivos.setAlternatingRowColors(True)

        festivos = [
            (f["fecha"], f["descripcion"], f["accion"])
            for f in almacen_config.obtener_festivos()
        ]

        self.tabla_festivos.setRowCount(len(festivos))
        for fila, (fecha, desc, accion) in enumerate(festivos):
            for col, valor in enumerate([fecha, desc, accion]):
                item = QTableWidgetItem(valor)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_festivos.setItem(fila, col, item)

        layout_festivos.addWidget(self.tabla_festivos, 1)

        layout_accion_festivo = QHBoxLayout()
        layout_accion_festivo.setSpacing(8)

        btn_agregar_festivo = QPushButton("Agregar Festivo")
        btn_agregar_festivo.setObjectName("acento")
        btn_agregar_festivo.setMinimumHeight(36)
        btn_agregar_festivo.setMinimumWidth(160)
        btn_agregar_festivo.clicked.connect(self._agregar_festivo)
        layout_accion_festivo.addWidget(btn_agregar_festivo)

        layout_accion_festivo.addStretch()

        btn_eliminar_festivo = QPushButton("Eliminar Seleccionado")
        btn_eliminar_festivo.setObjectName("peligro_borde")
        btn_eliminar_festivo.setMinimumHeight(36)
        btn_eliminar_festivo.clicked.connect(self._eliminar_festivo)
        layout_accion_festivo.addWidget(btn_eliminar_festivo)

        layout_festivos.addLayout(layout_accion_festivo)

        tabs.addTab(tab_festivos, "Días Festivos")

        # ============================================================
        # TAB 6: Gestion de Usuarios
        # ============================================================
        tab_usuarios = QWidget()
        layout_usuarios = QVBoxLayout(tab_usuarios)
        layout_usuarios.setContentsMargins(16, 16, 16, 16)

        lbl_usuarios = QLabel("Usuarios del Sistema")
        lbl_usuarios.setStyleSheet(
            f"color: {PRIMARIO}; font-size: 15px; font-weight: 700; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout_usuarios.addWidget(lbl_usuarios)

        self.tabla_usuarios = QTableWidget()
        self.tabla_usuarios.setColumnCount(4)
        self.tabla_usuarios.setHorizontalHeaderLabels([
            "ID", "Nombre", "Usuario", "Rol"
        ])
        self.tabla_usuarios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_usuarios.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_usuarios.verticalHeader().setVisible(False)
        self.tabla_usuarios.verticalHeader().setDefaultSectionSize(36)
        self.tabla_usuarios.setAlternatingRowColors(True)
        self._cargar_usuarios()

        layout_usuarios.addWidget(self.tabla_usuarios, 1)

        layout_accion_usuario = QHBoxLayout()
        layout_accion_usuario.setSpacing(8)

        btn_agregar_usuario = QPushButton("Agregar Usuario")
        btn_agregar_usuario.setObjectName("acento")
        btn_agregar_usuario.setMinimumHeight(36)
        btn_agregar_usuario.setMinimumWidth(160)
        btn_agregar_usuario.clicked.connect(self._agregar_usuario)
        layout_accion_usuario.addWidget(btn_agregar_usuario)

        layout_accion_usuario.addStretch()

        btn_editar_usuario = QPushButton("Editar")
        btn_editar_usuario.setObjectName("secundario")
        btn_editar_usuario.setMinimumHeight(36)
        btn_editar_usuario.clicked.connect(self._editar_usuario)
        layout_accion_usuario.addWidget(btn_editar_usuario)

        btn_eliminar_usuario = QPushButton("Eliminar")
        btn_eliminar_usuario.setObjectName("peligro_borde")
        btn_eliminar_usuario.setMinimumHeight(36)
        btn_eliminar_usuario.clicked.connect(self._eliminar_usuario)
        layout_accion_usuario.addWidget(btn_eliminar_usuario)

        layout_usuarios.addLayout(layout_accion_usuario)

        tabs.addTab(tab_usuarios, "Gestión de Usuarios")
        self.tab_usuarios_indice = tabs.indexOf(tab_usuarios)

        layout.addWidget(tabs, 1)

        # Recargar la lista de usuarios cada vez que se active su pestana
        tabs.currentChanged.connect(self._recargar_usuarios_pestana)

    def _recargar_usuarios_pestana(self, indice):
        if self.tab_usuarios_indice == indice:
            self._cargar_usuarios()

    def _cargar_usuarios(self):
        """Llena la tabla de usuarios desde el almacen central."""
        usuarios = almacen_usuarios.todos()
        self.tabla_usuarios.setRowCount(0)
        self.tabla_usuarios.setRowCount(len(usuarios))
        for fila, u in enumerate(usuarios):
            for col, valor in enumerate([str(fila + 1), u["nombre"], u["usuario"], u["rol"]]):
                item = QTableWidgetItem(valor)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_usuarios.setItem(fila, col, item)

    # ------------------------------------------------------------------
    # Mesas y Areas: carga de tablas
    # ------------------------------------------------------------------
    def _cargar_zonas_anticipacion(self):
        """(Re)construye las filas de zonas de la tabla de limites de anticipacion."""
        self._spin_dias_por_fila = {}
        self._check_deposito_por_fila = {}
        self._spin_pct_por_fila = {}

        zonas = sorted({m["zona"] for m in almacen_datos.MESAS})
        limites = almacen_config.obtener_limites_anticipacion()
        self.tabla_limites.setRowCount(len(zonas))
        for fila, zona in enumerate(zonas):
            cfg = limites.get(zona) or {}

            item_zona = QTableWidgetItem(ZONAS_VISIBLES.get(zona, zona))
            item_zona.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_zona.setData(Qt.ItemDataRole.UserRole, zona)
            self.tabla_limites.setItem(fila, 0, item_zona)

            spin_dias = QSpinBox()
            spin_dias.setRange(1, 360)
            spin_dias.setFixedWidth(92)
            spin_dias.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                spin_dias.setValue(int(cfg.get("max_dias") or 30))
            except (TypeError, ValueError):
                spin_dias.setValue(30)
            self.tabla_limites.setCellWidget(fila, 1, self._widget_centrado(spin_dias))
            self._spin_dias_por_fila[fila] = spin_dias

            check_dep = QCheckBox()
            check_dep.setChecked(bool(cfg.get("requiere_deposito")))
            contenedor = QWidget()
            fila_check = QHBoxLayout(contenedor)
            fila_check.setContentsMargins(0, 0, 0, 0)
            fila_check.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fila_check.addWidget(check_dep)
            self.tabla_limites.setCellWidget(fila, 2, contenedor)
            self._check_deposito_por_fila[fila] = check_dep

            spin_pct = QSpinBox()
            spin_pct.setRange(1, 100)
            spin_pct.setFixedWidth(86)
            spin_pct.setAlignment(Qt.AlignmentFlag.AlignCenter)
            try:
                spin_pct.setValue(int(cfg.get("porcentaje_deposito") or 30))
            except (TypeError, ValueError):
                spin_pct.setValue(30)
            spin_pct.setEnabled(check_dep.isChecked())
            check_dep.toggled.connect(spin_pct.setEnabled)
            self.tabla_limites.setCellWidget(fila, 3, self._widget_centrado(spin_pct))
            self._spin_pct_por_fila[fila] = spin_pct

    @staticmethod
    def _widget_centrado(widget):
        """Envuelve un widget para centrarlo dentro de la celda de la tabla
        (setCellWidget ancla arriba y un QSpinBox mas alto que la fila
        desborda hacia abajo)."""
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(widget)
        return contenedor

    def _cargar_areas(self):
        areas = almacen_datos.obtener_ubicaciones()
        self._areas = areas
        self.tabla_areas.setRowCount(len(areas))
        for fila, a in enumerate(areas):
            item = QTableWidgetItem(ZONAS_VISIBLES.get(a["nombre"], a["nombre"]))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setData(Qt.ItemDataRole.UserRole, a["id"])
            self.tabla_areas.setItem(fila, 0, item)

    def _cargar_mesas(self):
        mesas = almacen_datos.obtener_mesas()
        self._mesas = mesas
        self.tabla_mesas.setRowCount(len(mesas))
        for fila, m in enumerate(mesas):
            for col, valor in enumerate([
                m["numero"],
                str(m["capacidad"]),
                ZONAS_VISIBLES.get(m["zona"], m["zona"]),
            ]):
                item = QTableWidgetItem(valor)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, m["id"])
                self.tabla_mesas.setItem(fila, col, item)

    def _area_seleccionada(self):
        fila = self.tabla_areas.currentRow()
        if fila < 0 or fila >= len(self._areas):
            QMessageBox.information(
                self, "Área", "Seleccione un área de la lista."
            )
            return None
        return self._areas[fila]

    def _mesa_seleccionada(self):
        fila = self.tabla_mesas.currentRow()
        if fila < 0 or fila >= len(self._mesas):
            QMessageBox.information(
                self, "Mesa", "Seleccione una mesa de la lista."
            )
            return None
        return self._mesas[fila]

    def _refrescar_tras_cambios(self):
        """Recarga las caches de mesas y las tablas de la pestana de configuracion."""
        almacen_datos.recargar_catalogos()
        self._cargar_areas()
        self._cargar_mesas()
        self._cargar_zonas_anticipacion()

    # ------------------------------------------------------------------
    # Mesas y Areas: acciones CRUD
    # ------------------------------------------------------------------
    def _nombre_area_valido(self, nombre):
        """Valida el nombre de un area: obligatorio y maximo 50 caracteres."""
        nombre = (nombre or "").strip()
        if not nombre:
            QMessageBox.warning(
                self, "Nombre requerido", "Debe ingresar el nombre del área."
            )
            return False, nombre
        if len(nombre) > 50:
            QMessageBox.warning(
                self, "Nombre muy largo",
                "El nombre del área no puede superar los 50 caracteres."
            )
            return False, nombre
        return True, nombre

    def _nueva_area(self):
        nombre, ok = QInputDialog.getText(self, "Nueva Área", "Nombre del área:")
        if not ok:
            return
        valido, nombre = self._nombre_area_valido(nombre)
        if not valido:
            return
        nuevo_id, error = almacen_datos.crear_ubicacion(nombre)
        if error:
            QMessageBox.warning(self, "No se pudo crear", error)
            return
        self._refrescar_tras_cambios()

    def _renombrar_area(self):
        area = self._area_seleccionada()
        if not area:
            return
        nombre, ok = QInputDialog.getText(
            self,
            "Renombrar Área",
            "Nuevo nombre:",
            text=ZONAS_VISIBLES.get(area["nombre"], area["nombre"]),
        )
        if not ok:
            return
        valido, nombre = self._nombre_area_valido(nombre)
        if not valido:
            return
        ok, error = almacen_datos.renombrar_ubicacion(area["id"], nombre)
        if error:
            QMessageBox.warning(self, "No se pudo renombrar", error)
            return
        almacen_config.renombrar_zona_limites(area["nombre"], nombre)
        self._refrescar_tras_cambios()

    def _eliminar_area(self):
        area = self._area_seleccionada()
        if not area:
            return
        respuesta = QMessageBox.question(
            self,
            "Eliminar Área",
            f"¿Eliminar el área '{ZONAS_VISIBLES.get(area['nombre'], area['nombre'])}'?\n\n"
            "Solo es posible si no tiene mesas asociadas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen_datos.eliminar_ubicacion(area["id"])
        if error:
            QMessageBox.warning(self, "No se pudo eliminar", error)
            return
        almacen_config.eliminar_zona_limites(area["nombre"])
        self._refrescar_tras_cambios()

    def _nueva_mesa(self):
        areas = almacen_datos.obtener_ubicaciones()
        if not areas:
            QMessageBox.warning(
                self, "Sin áreas", "Cree primero un área para el local."
            )
            return
        dialogo = _DialogoMesa(areas, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        datos = dialogo.obtener_datos()
        ok, error = almacen_datos.crear_mesa(
            datos["numero"], datos["capacidad"], datos["id_ubicacion"]
        )
        if error:
            QMessageBox.warning(self, "No se pudo crear", error)
            return
        self._refrescar_tras_cambios()

    def _editar_mesa(self):
        mesa = self._mesa_seleccionada()
        if not mesa:
            return
        areas = almacen_datos.obtener_ubicaciones()
        dialogo = _DialogoMesa(areas, self, datos=mesa)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        datos = dialogo.obtener_datos()
        ok, error = almacen_datos.actualizar_mesa(
            mesa["id"], datos["numero"], datos["capacidad"], datos["id_ubicacion"]
        )
        if error:
            QMessageBox.warning(self, "No se pudo editar", error)
            return
        self._refrescar_tras_cambios()

    def _eliminar_mesa(self):
        mesa = self._mesa_seleccionada()
        if not mesa:
            return
        respuesta = QMessageBox.question(
            self,
            "Eliminar Mesa",
            f"Eliminar la mesa '{mesa['numero']}'?\n\n"
            "Solo es posible si no tiene reservas asociadas.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return
        ok, error = almacen_datos.eliminar_mesa(mesa["id"])
        if error:
            QMessageBox.warning(self, "No se pudo eliminar", error)
            return
        self._refrescar_tras_cambios()

    def _actualizar_estado_smtp(self):
        configurado, detalle = notificaciones.estado_configuracion()
        color = "#2E7D32" if configurado else "#B26A00"
        self.lbl_smtp.setText(detalle)
        self.lbl_smtp.setStyleSheet(f"color: {color}; font-size: 12px;")

    def _guardar_parametros(self):
        """Valida y guarda los parametros generales del sistema."""
        duracion = self.txt_duracion.text().strip()
        tolerancia = self.txt_tolerancia.text().strip()
        limite_confirmacion = self.txt_limite_confirmacion.text().strip()
        max_personas = self.txt_max_personas.text().strip()

        # Los validadores QIntValidator ya restringen la entrada a numeros,
        # aqui solo se verifica que no esten vacios.
        if not duracion or not tolerancia or not max_personas \
                or not limite_confirmacion:
            QMessageBox.warning(
                self,
                "Campos requeridos",
                "Debe ingresar un valor en todos los parámetros numéricos."
            )
            return

        almacen_config.guardar_parametros(
            duracion,
            tolerancia,
            limite_confirmacion,
            max_personas,
            self.chk_email.isChecked(),
            self.chk_recordatorio.isChecked(),
        )
        almacen_datos.recargar_parametros_reservas()

        QMessageBox.information(
            self,
            "Parámetros Guardados",
            "Los parámetros del sistema se guardaron correctamente.\n\n"
            f"Duración estándar: {duracion} min\n"
            f"Tolerancia: {tolerancia} min\n"
            f"Límite de confirmación: {limite_confirmacion} min\n"
            f"Máximo de personas: {max_personas}"
        )

    def _guardar_anticipacion(self):
        """Guarda el limite estandar y los limites por zona de anticipacion."""
        estandar = self.spin_dias_estandar.value()
        limites = {}
        for fila in range(self.tabla_limites.rowCount()):
            item_zona = self.tabla_limites.item(fila, 0)
            zona = item_zona.data(Qt.ItemDataRole.UserRole) or item_zona.text()
            limites[zona] = {
                "max_dias": self._spin_dias_por_fila[fila].value(),
                "requiere_deposito": bool(
                    self._check_deposito_por_fila[fila].isChecked()
                ),
                "porcentaje_deposito": self._spin_pct_por_fila[fila].value(),
            }

        almacen_config.guardar_dias_estandar(estandar)
        almacen_config.guardar_limites_anticipacion(limites)

        detalle = "\n".join(
            f"{ZONAS_VISIBLES.get(z, z)}: {c['max_dias']} días"
            f"{' + depósito ' + str(c['porcentaje_deposito']) + '%' if c['requiere_deposito'] else ''}"
            for z, c in limites.items()
        )
        QMessageBox.information(
            self,
            "Anticipación Guardada",
            "Los límites de anticipación se guardaron correctamente.\n\n"
            f"Días estándar: {estandar}\n\n{detalle}"
        )

    @staticmethod
    def _dia_clave(texto):
        texto = (texto or "").strip()
        return DIAS_CLAVES.get(texto, texto)

    @staticmethod
    def _hora_valida(hora):
        """Valida que la hora tenga formato HH:MM dentro de un rango valido."""
        try:
            h, m = hora.split(":")
            return int(h) <= 23 and int(m) <= 59
        except (ValueError, AttributeError):
            return False

    def _guardar_horarios(self):
        """Guarda los horarios de atencion en el almacen central."""
        filas = self.tabla_horarios.rowCount()
        if filas == 0:
            QMessageBox.information(self, "Horarios", "No hay horarios para guardar.")
            return
        horarios = []
        for fila in range(filas):
            item_dia = self.tabla_horarios.item(fila, 0)
            dia = self._dia_clave(item_dia.text())
            apertura = self.tabla_horarios.item(fila, 1).text().strip()
            cierre = self.tabla_horarios.item(fila, 2).text().strip()
            cerrado = self.tabla_horarios.item(fila, 3).text() in ("Sí", "Si")
            if not cerrado:
                if not self._hora_valida(apertura) or not self._hora_valida(cierre):
                    QMessageBox.warning(
                        self,
                        "Hora inválida",
                        f"El horario del {DIAS_VISIBLES.get(dia, dia)} es inválido.\n\n"
                        "Las horas deben tener el formato HH:MM "
                        "(por ejemplo 09:00) dentro de un rango válido."
                    )
                    return
                if cierre <= apertura:
                    QMessageBox.warning(
                        self,
                        "Horario inválido",
                        f"En {DIAS_VISIBLES.get(dia, dia)} la hora de cierre debe ser "
                        "posterior a la de apertura."
                    )
                    return
            horarios.append({
                "dia": dia,
                "apertura": apertura,
                "cierre": cierre,
                "cerrado": cerrado,
            })
        guardados = almacen_config.guardar_horarios(horarios)
        QMessageBox.information(
            self,
            "Horarios Guardados",
            "Los horarios de atención se guardaron correctamente "
            f"({guardados} días configurados)."
        )

    def _agregar_festivo(self):
        """Agrega un nuevo dia festivo a la tabla."""
        fecha, ok = QInputDialog.getText(self, "Agregar Festivo", "Fecha (DD/MM/AAAA):")
        if not ok or not fecha.strip():
            return
        descripcion, ok2 = QInputDialog.getText(
            self, "Agregar Festivo", "Descripción:"
        )
        if not ok2 or not descripcion.strip():
            descripcion = "Festivo"
        accion, ok3 = QInputDialog.getItem(
            self, "Agregar Festivo", "Acción:",
            ["Cerrado", "Horario Especial"], 0, False
        )
        if not ok3:
            return
        fila = self.tabla_festivos.rowCount()
        self.tabla_festivos.insertRow(fila)
        for col, valor in enumerate([fecha.strip(), descripcion.strip(), accion]):
            item = QTableWidgetItem(valor)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_festivos.setItem(fila, col, item)
        valido, error = almacen_config.agregar_festivo(
            fecha.strip(), descripcion.strip(), accion
        )
        if not valido:
            QMessageBox.warning(self, "No se pudo agregar", error)
            self.tabla_festivos.removeRow(fila)
            return
        QMessageBox.information(
            self, "Festivo Agregado",
            f"Festivo '{descripcion}' ({fecha}) agregado correctamente."
        )

    def _eliminar_festivo(self):
        """Elimina el festivo seleccionado de la tabla."""
        fila = self.tabla_festivos.currentRow()
        if fila == -1:
            QMessageBox.information(
                self, "Selección", "Seleccione un festivo para eliminar."
            )
            return
        fecha = self.tabla_festivos.item(fila, 0).text()
        respuesta = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Desea eliminar el festivo del {fecha}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            self.tabla_festivos.removeRow(fila)
            almacen_config.eliminar_festivo(fecha)
            QMessageBox.information(
                self, "Eliminado", f"Festivo del {fecha} eliminado."
            )

    def _agregar_usuario(self):
        """Registra un nuevo usuario en el almacen central."""
        nombre, ok = QInputDialog.getText(self, "Agregar Usuario", "Nombre completo:")
        if not ok or not nombre.strip():
            return
        usuario, ok2 = QInputDialog.getText(self, "Agregar Usuario", "Nombre de usuario:")
        if not ok2 or not usuario.strip():
            return
        if len(nombre.strip()) > 100:
            QMessageBox.warning(self, "Nombre muy largo",
                                "El nombre completo no puede superar 100 caracteres.")
            return
        if len(usuario.strip()) > 50:
            QMessageBox.warning(self, "Usuario muy largo",
                                "El nombre de usuario no puede superar 50 caracteres.")
            return
        rol, ok3 = QInputDialog.getItem(
            self, "Agregar Usuario", "Rol:",
            ["Administrador", "Recepcionista"], 0, False
        )
        if not ok3:
            return
        contrasena, ok4 = QInputDialog.getText(
            self, "Agregar Usuario", "Contraseña:",
            QLineEdit.EchoMode.Password
        )
        if not ok4 or not contrasena:
            QMessageBox.warning(
                self, "Campo requerido", "Debe ingresar una contraseña."
            )
            return
        contrasena2, ok5 = QInputDialog.getText(
            self, "Agregar Usuario", "Confirmar contraseña:",
            QLineEdit.EchoMode.Password
        )
        if not ok5:
            return
        if contrasena != contrasena2:
            QMessageBox.warning(
                self, "Contraseña no coincide",
                "Las contraseñas ingresadas no coinciden."
            )
            return
        valido, error = almacen_usuarios.registrar(
            nombre, usuario, rol, contrasena
        )
        if not valido:
            QMessageBox.warning(self, "No se pudo agregar", error)
            return
        self._cargar_usuarios()
        QMessageBox.information(
            self, "Usuario Agregado",
            f"Usuario '{usuario}' con rol '{rol}' agregado correctamente."
        )

    def _editar_usuario(self):
        """Edita el nombre del usuario seleccionado via el almacen central."""
        fila = self.tabla_usuarios.currentRow()
        if fila == -1:
            QMessageBox.information(
                self, "Selección", "Seleccione un usuario para editar."
            )
            return
        login = self.tabla_usuarios.item(fila, 2).text()
        nombre_actual = self.tabla_usuarios.item(fila, 1).text()
        nuevo_nombre, ok = QInputDialog.getText(
            self, "Editar Usuario", "Nombre completo:", text=nombre_actual
        )
        if not ok or not nuevo_nombre.strip():
            return
        if len(nuevo_nombre.strip()) > 100:
            QMessageBox.warning(self, "Nombre muy largo",
                                "El nombre completo no puede superar 100 caracteres.")
            return
        if not almacen_usuarios.editar_nombre(login, nuevo_nombre):
            QMessageBox.warning(self, "Error", "No se pudo actualizar el usuario.")
            return
        self._cargar_usuarios()
        QMessageBox.information(
            self, "Usuario Actualizado",
            f"Nombre del usuario '{login}' actualizado a '{nuevo_nombre.strip()}'."
        )

    def _eliminar_usuario(self):
        """Elimina el usuario seleccionado via el almacen central."""
        fila = self.tabla_usuarios.currentRow()
        if fila == -1:
            QMessageBox.information(
                self, "Selección", "Seleccione un usuario para eliminar."
            )
            return
        usuario = self.tabla_usuarios.item(fila, 2).text()
        if usuario == "admin":
            QMessageBox.warning(
                self, "Acción no permitida",
                "El usuario administrador principal no puede eliminarse."
            )
            return
        if usuario == getattr(almacen_usuarios, "usuario_actual", None):
            QMessageBox.warning(
                self, "Acción no permitida",
                "No puede eliminar al usuario con el que inició sesión.\n"
                "Para eliminarlo, ingrese con otra cuenta."
            )
            return
        respuesta = QMessageBox.question(
            self,
            "Confirmar Eliminación",
            f"¿Desea eliminar al usuario '{usuario}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            almacen_usuarios.eliminar(usuario)
            self._cargar_usuarios()
            QMessageBox.information(
                self, "Eliminado", f"Usuario '{usuario}' eliminado."
            )


class _DialogoMesa(QDialog):
    """Dialogo para crear/editar una mesa (numero, capacidad y area)."""

    def __init__(self, areas, parent=None, datos=None):
        super().__init__(parent)
        self.setWindowTitle("Editar Mesa" if datos else "Nueva Mesa")
        self.setMinimumWidth(340)

        form = QFormLayout(self)
        form.setSpacing(12)
        form.setContentsMargins(20, 20, 20, 20)

        self.txt_numero = QLineEdit(datos["numero"] if datos else "")
        self.txt_numero.setPlaceholderText("Ej: M9")
        self.txt_numero.setMaxLength(10)
        # Formato: de 1 a 3 letras + hasta 3 digitos (sin espacios ni simbolos).
        # El validador en vivo bloquea caracteres no permitidos al teclear.
        self.txt_numero.setValidator(QRegularExpressionValidator(
            QRegularExpression(r"^[A-Za-z]{0,3}[0-9]{0,3}$")
        ))
        form.addRow("Número de mesa:", self.txt_numero)

        self.spin_capacidad = QSpinBox()
        self.spin_capacidad.setRange(1, 999)
        self.spin_capacidad.setValue(int(datos["capacidad"]) if datos else 4)
        form.addRow("Capacidad:", self.spin_capacidad)

        self.cmb_area = QComboBox()
        for a in areas:
            self.cmb_area.addItem(
                ZONAS_VISIBLES.get(a["nombre"], a["nombre"]), a["id"]
            )
        if datos and datos.get("id_ubicacion") is not None:
            idx = self.cmb_area.findData(datos["id_ubicacion"])
            if idx >= 0:
                self.cmb_area.setCurrentIndex(idx)
        form.addRow("Área:", self.cmb_area)

        botones = QHBoxLayout()
        botones.setContentsMargins(0, 8, 0, 0)
        botones.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secundario")
        btn_cancelar.setMinimumHeight(36)
        btn_cancelar.setMinimumWidth(130)
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar")
        btn_guardar.setObjectName("acento")
        btn_guardar.setMinimumHeight(36)
        btn_guardar.setMinimumWidth(130)
        btn_guardar.clicked.connect(self._validar)

        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)
        form.addRow(botones)

    def _validar(self):
        numero = self.txt_numero.text().strip().upper()
        if not numero:
            QMessageBox.warning(
                self, "Campo requerido", "Ingrese el número de la mesa."
            )
            self.txt_numero.setFocus()
            return
        patron = QRegularExpression(r"^[A-Z]{1,3}[0-9]{1,3}$")
        if not patron.match(numero).hasMatch():
            QMessageBox.warning(
                self, "Número inválido",
                "El número de mesa debe contener de 1 a 3 letras seguidas de "
                "hasta 3 dígitos (sin espacios ni símbolos).\n\n"
                'Ejemplos válidos: M1, M12, CV3, VIP4.'
            )
            self.txt_numero.setFocus()
            return
        if self.cmb_area.currentIndex() < 0:
            QMessageBox.warning(
                self, "Área requerida", "Seleccione un área para la mesa."
            )
            return
        self.txt_numero.setText(numero)
        self.accept()

    def obtener_datos(self):
        return {
            "numero": self.txt_numero.text().strip().upper(),
            "capacidad": self.spin_capacidad.value(),
            "id_ubicacion": self.cmb_area.currentData(),
        }
