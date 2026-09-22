# -*- coding: utf-8 -*-
"""
Modulo: Ventana Principal
Contenedor principal del sistema. Administra la navegacion entre modulos
mediante un sidebar lateral y un area central de contenido.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFrame, QLabel, QPushButton, QStackedWidget, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap

from rutas import LOGO_PATH
from modulos.dashboard import PanelDashboard
from modulos.reservas import PanelReservas
from modulos.mesas import PanelMesas
from modulos.clientes import PanelClientes
from modulos.reportes import PanelReportes
from modulos.configuracion import PanelConfiguracion

PRIMARIO = "#1B3A5C"
SECUNDARIO = "#2C5F8A"
DORADO = "#D4A843"
NEUTRO_CLARO = "#F5F5F5"
NEUTRO_OSCURO = "#0D1B2A"


class BotonSidebar(QPushButton):
    """
    Boton personalizado para el sidebar.
    Muestra el nombre del modulo con estilos resaltados.
    """
    def __init__(self, texto, parent=None):
        super().__init__(texto, parent)
        self.setCheckable(True)
        self.setMinimumHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #B0BEC5;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {SECUNDARIO};
                color: white;
            }}
            QPushButton:checked {{
                background-color: {DORADO};
                color: {NEUTRO_OSCURO};
                font-weight: 700;
            }}
        """)


class VentanaPrincipal(QMainWindow):
    """
    Ventana principal del sistema Synchrolia.
    Recibe el nombre y rol del usuario logueado para adaptar permisos.
    """
    cerrar_sesion = Signal()

    def __init__(self, login_usuario, nombre_usuario, rol):
        super().__init__()
        self.login_usuario = login_usuario
        self.nombre_usuario = nombre_usuario
        self.rol = rol
        self.setWindowTitle(f"Synchrolia SGRT - {rol}: {nombre_usuario}")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        self._construir_interfaz()

    def _construir_interfaz(self):
        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_raiz = QHBoxLayout(widget_central)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        # ============================================================
        # SIDEBAR IZQUIERDO
        # ============================================================
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {PRIMARIO};
                border-right: none;
            }}
        """)

        layout_sidebar = QVBoxLayout(sidebar)
        layout_sidebar.setContentsMargins(12, 16, 12, 16)
        layout_sidebar.setSpacing(4)

        # Logo de la marca en el sidebar
        lbl_marca = QLabel()
        pixmap_marca = QPixmap(LOGO_PATH)
        lbl_marca.setPixmap(
            pixmap_marca.scaled(
                170, 170,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        lbl_marca.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_marca.setFixedHeight(180)
        layout_sidebar.addWidget(lbl_marca)

        # Nombre de la marca en mayusculas bajo el logo
        lbl_nombre = QLabel("SYNCHROLIA")
        lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_nombre.setFont(QFont("Raleway", 16, QFont.Weight.Bold))
        lbl_nombre.setStyleSheet(f"color: {DORADO}; letter-spacing: 4px; margin-bottom: 6px;")
        layout_sidebar.addWidget(lbl_nombre)

        layout_sidebar.addSpacing(8)

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("background-color: #3A5068; max-height: 1px; margin: 8px 0;")
        layout_sidebar.addWidget(separador)

        # Botones de navegacion (solo los modulos permitidos segun permisos RBAC)
        # Dashboard y Clientes siempre visibles: el Dashboard es el resumen general
        # y Clientes es necesario para registrar clientes de las reservas.
        permisos_requeridos = {
            "Reservas": {"GESTIONAR_RESERVAS"},
            "Mesas": {"VER_MAPA_MESAS"},
            "Reportes": {"VER_REPORTES"},
            "Configuracion": {"GESTIONAR_CONFIGURACION", "GESTIONAR_USUARIOS"},
        }

        from modulos.almacen_usuarios import almacen
        permisos = almacen.permisos_de(self.login_usuario)

        modulos = [
            "Dashboard",
            "Reservas",
            "Mesas",
            "Clientes",
            "Reportes",
            "Configuracion",
        ]
        modulos = [
            m for m in modulos
            if m not in permisos_requeridos
            or not permisos_requeridos[m].isdisjoint(permisos)
        ]

        self.botones_nav = []
        for indice, texto in enumerate(modulos):
            btn = BotonSidebar("  " + texto)
            btn.clicked.connect(lambda checked, i=indice: self._navegar(i))
            layout_sidebar.addWidget(btn)
            self.botones_nav.append(btn)

        layout_sidebar.addStretch()

        # Informacion del usuario logueado
        separador2 = QFrame()
        separador2.setFrameShape(QFrame.Shape.HLine)
        separador2.setStyleSheet("background-color: #3A5068; max-height: 1px; margin: 8px 0;")
        layout_sidebar.addWidget(separador2)

        # Avatar circular con iniciales + nombre y rol
        layout_usuario = QHBoxLayout()
        layout_usuario.setSpacing(10)

        iniciales = " ".join([p[0] for p in self.nombre_usuario.split() if p])[:2].upper() or "?"
        avatar = QLabel(iniciales)
        avatar.setFixedSize(40, 40)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFont(QFont("Raleway", 14, QFont.Weight.Bold))
        avatar.setStyleSheet(f"""
            background-color: {DORADO};
                color: {NEUTRO_OSCURO};
                border-radius: 20px;
                font-weight: 700;
        """)
        layout_usuario.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)

        layout_datos_usuario = QVBoxLayout()
        layout_datos_usuario.setSpacing(2)

        lbl_usuario = QLabel(self.nombre_usuario)
        lbl_usuario.setStyleSheet("color: white; font-size: 12px; font-weight: 600;")
        layout_datos_usuario.addWidget(lbl_usuario)

        lbl_rol = QLabel(self.rol)
        lbl_rol.setStyleSheet("color: #D4A843; font-size: 10px;")
        layout_datos_usuario.addWidget(lbl_rol)

        layout_usuario.addLayout(layout_datos_usuario)
        layout_usuario.addStretch()

        layout_sidebar.addLayout(layout_usuario)
        layout_sidebar.addSpacing(8)

        btn_perfil = QPushButton("  Mi Perfil")
        btn_perfil.setObjectName("acento")
        btn_perfil.setMinimumHeight(36)
        btn_perfil.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_perfil.clicked.connect(self._abrir_perfil)
        layout_sidebar.addWidget(btn_perfil)

        btn_cerrar = QPushButton("  Cerrar Sesion")
        btn_cerrar.setObjectName("peligro")
        btn_cerrar.setMinimumHeight(36)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.clicked.connect(self._cerrar_sesion)
        layout_sidebar.addWidget(btn_cerrar)

        layout_raiz.addWidget(sidebar)

        # ============================================================
        # AREA DE CONTENIDO CENTRAL
        # ============================================================
        self.stack_contenido = QStackedWidget()
        # IMPORTANTE: NO poner setStyleSheet aqui. Un stylesheet local en un
        # contenedor hace que Qt resuelva los estilos de los widgets hijos contra
        # ESE stylesheet, rompiendo la herencia de los selectores por objectName
        # (QPushButton#exito, #acento, etc.) definidos en el QSS global de la app.
        # Eso hacia que los botones perdieran su fondo/color. El fondo gris claro
        # lo aportan los propios paneles/configuracion del QSS global.

        # Crear los paneles de cada modulo, respetando el mismo orden de
        # navegacion (indice de boton == indice del stack).
        self.panel_dashboard = None
        self.panel_reservas = None
        self.panel_mesas = None
        self.panel_clientes = None
        self.panel_reportes = None
        self.panel_configuracion = None

        for texto in modulos:
            if texto == "Dashboard":
                # El dashboard se envuelve en un area desplazable para que el
                # banner a ancho completo (alto proporcional) no recorte la tabla.
                self.panel_dashboard = PanelDashboard(self.nombre_usuario)
                scroll_dashboard = QScrollArea()
                scroll_dashboard.setWidgetResizable(True)
                scroll_dashboard.setFrameShape(QFrame.Shape.NoFrame)
                scroll_dashboard.setWidget(self.panel_dashboard)
                self.stack_contenido.addWidget(scroll_dashboard)
            elif texto == "Reservas":
                self.panel_reservas = PanelReservas(self.nombre_usuario)
                self.stack_contenido.addWidget(self.panel_reservas)
            elif texto == "Mesas":
                self.panel_mesas = PanelMesas()
                self.stack_contenido.addWidget(self.panel_mesas)
            elif texto == "Clientes":
                self.panel_clientes = PanelClientes()
                self.stack_contenido.addWidget(self.panel_clientes)
            elif texto == "Reportes":
                self.panel_reportes = PanelReportes()
                self.stack_contenido.addWidget(self.panel_reportes)
            elif texto == "Configuracion":
                self.panel_configuracion = PanelConfiguracion()
                self.stack_contenido.addWidget(self.panel_configuracion)

        # Actualizacion automatica en vivo: al cambiar reservas, se refleja
        # en el mapa de mesas, reportes y dashboard (según modulos visibles).
        if self.panel_reservas is not None:
            if self.panel_mesas is not None:
                self.panel_reservas.reservas_cambiadas.connect(
                    self.panel_mesas._refrescar_mapa
                )
            if self.panel_reportes is not None:
                self.panel_reservas.reservas_cambiadas.connect(
                    self.panel_reportes._actualizar_reporte
                )
            if self.panel_dashboard is not None:
                self.panel_reservas.reservas_cambiadas.connect(
                    self.panel_dashboard._actualizar_contenido
                )

        # Al cambiar una mesa (mantenimiento), tambien se reflejan
        # el dashboard (barra de ocupacion) y los reportes.
        if self.panel_mesas is not None:
            if self.panel_dashboard is not None:
                self.panel_mesas.estado_mesas_cambiado.connect(
                    self.panel_dashboard._actualizar_contenido
                )
            if self.panel_reportes is not None:
                self.panel_mesas.estado_mesas_cambiado.connect(
                    self.panel_reportes._actualizar_reporte
                )

        layout_raiz.addWidget(self.stack_contenido)

        # Seleccionar Dashboard por defecto
        self._navegar(0)

    def _navegar(self, indice):
        """Cambia el panel visible en el area central y actualiza el boton activo."""
        self.stack_contenido.setCurrentIndex(indice)

        for i, btn in enumerate(self.botones_nav):
            btn.setChecked(i == indice)

        # Al entrar al mapa de mesas, reconstruirlo si cambiaron areas/mesas
        # (p. ej. luego de administrarlas en Configuracion).
        if self.stack_contenido.currentWidget() is getattr(self, "panel_mesas", None):
            self.panel_mesas._refrescar_mapa()

    def _abrir_perfil(self):
        """Abre el dialogo de perfil y gestiona la eliminacion de cuenta."""
        from modulos.dialogo_perfil import DialogoPerfil
        from modulos.almacen_usuarios import almacen
        dlg = DialogoPerfil(self.login_usuario, almacen, self)
        dlg.exec()

        # Refrescar nombre en la interfaz si se edito el perfil
        datos = almacen.obtener(self.login_usuario)
        if datos and datos["nombre"] != self.nombre_usuario:
            self.nombre_usuario = datos["nombre"]
            self.setWindowTitle(f"Synchrolia SGRT - {self.rol}: {self.nombre_usuario}")

        # Si el usuario elimino su cuenta, cerrar sesion hacia el login
        if getattr(dlg, "se_elimino", False):
            self.cerrar_sesion.emit()
            self.close()

    def _cerrar_sesion(self):
        from PySide6.QtWidgets import QMessageBox
        respuesta = QMessageBox.question(
            self,
            "Cerrar Sesion",
            "Desea cerrar la sesion actual?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            self.cerrar_sesion.emit()
            self.close()
