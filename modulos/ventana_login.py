# -*- coding: utf-8 -*-
"""
Modulo: Ventana de Login
Punto de entrada visual del sistema. Valida credenciales contra la base de datos
y redirige a la ventana principal segun el rol del usuario.
"""

import sys
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap, QIcon

from rutas import LOGO_PATH
from modulos.almacen_usuarios import almacen
from modulos.dialogo_perfil import DialogoRegistro

# Colores locales para referencia dentro del modulo
PRIMARIO = "#1B3A5C"
DORADO = "#D4A843"
NEUTRO_OSCURO = "#0D1B2A"

# Seguridad: limite de intentos fallidos de inicio de sesion
MAX_INTENTOS = 3
BLOQUEO_SEGUNDOS = 30


class VentanaLogin(QWidget):
    """
    Ventana de autenticacion.
    Emite senal 'login_exitoso' con el nombre y rol del usuario cuando las
    credenciales son correctas.
    """
    login_exitoso = Signal(str, str, str)  # (login_usuario, nombre, rol)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Synchrolia SGRT - Iniciar Sesion")
        self.setFixedSize(560, 800)
        self.setWindowIcon(QIcon(LOGO_PATH))
        self.setStyleSheet(f"""
            background-color: {NEUTRO_OSCURO};
            QMessageBox {{
                background-color: {NEUTRO_OSCURO};
            }}
            QMessageBox QLabel {{
                color: #FFFFFF;
                font-size: 13px;
            }}
        """)
        self._construir_interfaz()

        self._intentos_fallidos = 0
        self._bloqueado_hasta = 0.0
        self._timer_bloqueo = QTimer(self)
        self._timer_bloqueo.setInterval(1000)
        self._timer_bloqueo.timeout.connect(self._actualizar_bloqueo)

    def _construir_interfaz(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 30)
        layout_principal.setSpacing(0)

        layout_interior = QVBoxLayout()
        layout_interior.setContentsMargins(40, 24, 40, 0)
        layout_interior.setSpacing(0)

        # Logo (icono) centrado
        lbl_logo = QLabel()
        pixmap_logo = QPixmap(LOGO_PATH)
        lbl_logo.setPixmap(
            pixmap_logo.scaled(
                190, 190,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_logo.setFixedHeight(200)
        layout_interior.addWidget(lbl_logo)

        # Nombre de la marca en mayusculas bajo el logo
        lbl_nombre = QLabel("SYNCHROLIA")
        lbl_nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_nombre.setFont(QFont("Raleway", 22, QFont.Weight.Bold))
        lbl_nombre.setStyleSheet(f"color: {DORADO}; letter-spacing: 6px; margin-bottom: 4px;")
        layout_interior.addWidget(lbl_nombre)

        # Separador visual
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet(f"background-color: {DORADO}; max-height: 2px; margin: 0 80px;")
        layout_interior.addWidget(separador)

        layout_interior.addSpacing(20)

        # Titulo del formulario
        lbl_titulo = QLabel("Iniciar Sesion")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setFont(QFont("Raleway", 18, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: white;")
        layout_interior.addWidget(lbl_titulo)

        layout_interior.addSpacing(24)

        # Campo: Usuario
        lbl_usuario = QLabel("Usuario")
        lbl_usuario.setStyleSheet("color: #B0BEC5; font-size: 12px;")
        layout_interior.addWidget(lbl_usuario)

        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Ingrese su usuario")
        self.txt_usuario.setMinimumHeight(40)
        self.txt_usuario.setStyleSheet(f"""
            QLineEdit {{
                background-color: #1A2F45;
                border: 1px solid #3A5068;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {DORADO};
            }}
        """)
        layout_interior.addWidget(self.txt_usuario)

        layout_interior.addSpacing(12)

        # Campo: Contrasena
        lbl_contrasena = QLabel("Contrasena")
        lbl_contrasena.setStyleSheet("color: #B0BEC5; font-size: 12px;")
        layout_interior.addWidget(lbl_contrasena)

        self.txt_contrasena = QLineEdit()
        self.txt_contrasena.setPlaceholderText("Ingrese su contrasena")
        self.txt_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_contrasena.setMinimumHeight(40)
        self.txt_contrasena.setStyleSheet(f"""
            QLineEdit {{
                background-color: #1A2F45;
                border: 1px solid #3A5068;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
                /* Se usa una fuente sans-serif para que los puntos de la
                   contrasena se vean del tamano normal (Merriweather los dibuja demasiado grandes). */
                font-family: 'Raleway', 'Segoe UI', sans-serif;
            }}
            QLineEdit:focus {{
                border: 2px solid {DORADO};
            }}
        """)
        layout_interior.addWidget(self.txt_contrasena)

        layout_interior.addSpacing(24)

        # Boton de ingreso
        self.btn_ingresar = QPushButton("Ingresar")
        self.btn_ingresar.setMinimumHeight(44)
        self.btn_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ingresar.setStyleSheet(f"""
            QPushButton {{
                background-color: {DORADO};
                color: {NEUTRO_OSCURO};
                border: none;
                border-radius: 8px;
                font-size: 15px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: #C49A3C;
            }}
            QPushButton:pressed {{
                background-color: #B8892E;
            }}
        """)
        self.btn_ingresar.clicked.connect(self._validar_login)
        layout_interior.addWidget(self.btn_ingresar)

        layout_interior.addSpacing(12)

        # Enlace para registrarse
        self.btn_registrar = QPushButton("Registrarse")
        self.btn_registrar.setMinimumHeight(36)
        self.btn_registrar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_registrar.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {DORADO};
                border: 1px solid {DORADO};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(212, 168, 67, 0.15);
            }}
        """)
        self.btn_registrar.clicked.connect(self._abrir_registro)
        layout_interior.addWidget(self.btn_registrar)

        layout_interior.addStretch()

        # Pie de pagina
        lbl_pie = QLabel("UNAN-Leon | Proyecto Integrador II | 2026")
        lbl_pie.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_pie.setStyleSheet("color: #607D8B; font-size: 10px;")
        layout_interior.addWidget(lbl_pie)

        # Agregar el bloque interior al layout principal
        layout_principal.addLayout(layout_interior)

        # Atajos: Enter para iniciar sesion
        self.txt_contrasena.returnPressed.connect(self._validar_login)
        self.txt_usuario.returnPressed.connect(self._validar_login)

    def _validar_login(self):
        """
        Valida las credenciales ingresadas contra el almacen de usuarios.
        Bloquea temporalmente el acceso tras varios intentos fallidos.
        """
        if self._esta_bloqueado():
            restante = int(self._bloqueado_hasta - time.time())
            QMessageBox.warning(
                self,
                "Cuenta bloqueada temporalmente",
                f"<span style='color:#FFFFFF;'>Demasiados intentos fallidos. "
                f"Espere {restante} segundo(s) para volver a intentar.</span>"
            )
            return

        usuario = self.txt_usuario.text().strip()
        contrasena = self.txt_contrasena.text().strip()

        if not usuario or not contrasena:
            QMessageBox.warning(
                self,
                "Campos vacios",
                "<span style='color:#FFFFFF;'>Debe ingresar usuario y contrasena.</span>"
            )
            return

        datos = almacen.verificar_login(usuario, contrasena)
        if datos is not None:
            self._intentos_fallidos = 0
            self.login_exitoso.emit(usuario, datos["nombre"], datos["rol"])
            self.close()
        else:
            self._intentos_fallidos += 1
            restantes = MAX_INTENTOS - self._intentos_fallidos
            QMessageBox.critical(
                self,
                "Error de autenticacion",
                f"<span style='color:#FFFFFF;'>Usuario o contrasena incorrectos. "
                f"Le queda(n) {max(restantes, 0)} intento(s).</span>"
            )
            self.txt_contrasena.clear()
            self.txt_contrasena.setFocus()
            if self._intentos_fallidos >= MAX_INTENTOS:
                self._intentos_fallidos = 0
                self._aplicar_bloqueo()

    def _esta_bloqueado(self):
        """True si el formulario esta en periodo de bloqueo temporal."""
        return time.time() < self._bloqueado_hasta

    def _aplicar_bloqueo(self):
        """Deshabilita el boton Ingresar durante BLOQUEO_SEGUNDOS segundos."""
        self._bloqueado_hasta = time.time() + BLOQUEO_SEGUNDOS
        self.btn_ingresar.setEnabled(False)
        self.btn_ingresar.setText(f"Bloqueado ({BLOQUEO_SEGUNDOS} s)")
        self._timer_bloqueo.start()
        QMessageBox.warning(
            self,
            "Cuenta bloqueada temporalmente",
            f"<span style='color:#FFFFFF;'>Supero el limite de intentos. "
            f"Espere {BLOQUEO_SEGUNDOS} segundos para volver a intentarlo.</span>"
        )

    def _actualizar_bloqueo(self):
        """Cuenta regresiva en el boton; al terminar lo vuelve a habilitar."""
        restante = int(self._bloqueado_hasta - time.time())
        if restante > 0:
            self.btn_ingresar.setText(f"Bloqueado ({restante} s)")
        else:
            self._timer_bloqueo.stop()
            self._bloqueado_hasta = 0.0
            self._intentos_fallidos = 0
            self.btn_ingresar.setText("Ingresar")
            self.btn_ingresar.setEnabled(True)

    def _abrir_registro(self):
        """Abre el dialogo de registro de una nueva cuenta."""
        dlg = DialogoRegistro(almacen, self)
        dlg.exec()
