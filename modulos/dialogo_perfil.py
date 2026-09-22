# -*- coding: utf-8 -*-
"""
Dialogos de gestion de usuarios:
- DialogoPerfil: permite al usuario logueado editar su nombre, cambiar su
  contrasena y eliminar su propia cuenta.
- DialogoRegistro: permite crear una cuenta nueva desde el login.
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator

# Patron de solo letras (incluye acentos y espacio) para nombres completos
PATRON_NOMBRE = r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' ]+$"

# Colores del tema oscuro (coherentes con la ventana de login)
FONDO_OSCURO = "#0D1B2A"
FONDO_CAMPO = "#1A2F45"
BORDE_CAMPO = "#3A5068"
TEXTO_CLARO = "#FFFFFF"
TEXTO_SUAVE = "#B0BEC5"
DORADO = "#D4A843"
PRIMARIO_OSCURO = "#1B3A5C"

# Hoja de estilos para los dialogos de cuenta (fondo oscuro -> texto blanco)
ESTILOS_DIALOGO = f"""
QDialog {{
    background-color: {FONDO_OSCURO};
    color: {TEXTO_CLARO};
}}
QLabel {{
    color: {TEXTO_SUAVE};
}}
QLabel#titulo_dialogo {{
    font-size: 16px;
    font-weight: 700;
    color: {DORADO};
}}
QLineEdit {{
    background-color: {FONDO_CAMPO};
    border: 1px solid {BORDE_CAMPO};
    border-radius: 6px;
    padding: 8px 12px;
    color: {TEXTO_CLARO};
    font-size: 13px;
    min-height: 18px;
}}
QLineEdit:focus {{
    border: 2px solid {DORADO};
}}
QComboBox {{
    background-color: {FONDO_CAMPO};
    border: 1px solid {BORDE_CAMPO};
    border-radius: 6px;
    padding: 8px 12px;
    color: {TEXTO_CLARO};
    font-size: 13px;
    min-height: 18px;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid {BORDE_CAMPO};
    background-color: {FONDO_CAMPO};
}}
QComboBox QAbstractItemView {{
    background-color: {FONDO_CAMPO};
    color: {TEXTO_CLARO};
    border: 1px solid {BORDE_CAMPO};
    border-radius: 6px;
    selection-background-color: {PRIMARIO_OSCURO};
    selection-color: {TEXTO_CLARO};
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    padding: 8px 12px;
    color: {TEXTO_CLARO};
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: {PRIMARIO_OSCURO};
    color: {TEXTO_CLARO};
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {DORADO};
    color: {FONDO_OSCURO};
}}
QPushButton {{
    background-color: {PRIMARIO_OSCURO};
    color: {TEXTO_CLARO};
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 13px;
    min-height: 20px;
}}
QPushButton:hover {{
    background-color: #2C5F8A;
}}
QPushButton#exito {{
    background-color: #4CAF50;
    color: {TEXTO_CLARO};
}}
QPushButton#exito:hover {{
    background-color: #388E3C;
}}
QPushButton#peligro {{
    background-color: #BC1515;
    color: {TEXTO_CLARO};
}}
QPushButton#peligro:hover {{
    background-color: #9C1212;
}}
QPushButton#acento {{
    background-color: {DORADO};
    color: {FONDO_OSCURO};
}}
QMessageBox {{
    background-color: {FONDO_OSCURO};
    color: {TEXTO_CLARO};
}}
QMessageBox QLabel {{
    color: {TEXTO_CLARO};
    font-size: 13px;
}}
"""


AVISO_QSS = "QMessageBox { background-color: %s; color: %s; } QLabel { color: %s; } QPushButton { background-color: #1B3A5C; color: #FFFFFF; border-radius: 6px; padding: 6px 14px; font-weight: 700; }" % (FONDO_OSCURO, TEXTO_CLARO, TEXTO_CLARO)


def aviso(padre, titulo, texto, icono=QMessageBox.Icon.Warning,
          botones=QMessageBox.StandardButton.Ok,
          predeterminado=None):
    """Muestra un QMessageBox legible sobre los dialogos de fondo oscuro."""
    msg = QMessageBox(padre)
    msg.setIcon(icono)
    msg.setWindowTitle(titulo)
    msg.setText('<span style="color:%s;">%s</span>' % (TEXTO_CLARO, texto))
    msg.setStandardButtons(botones)
    if predeterminado is not None:
        msg.setDefaultButton(predeterminado)
    msg.setStyleSheet(AVISO_QSS)
    return msg.exec()


def info(padre, titulo, texto):
    return aviso(padre, titulo, texto, icono=QMessageBox.Icon.Information)


def _validador_nombre():
    return QRegularExpressionValidator(QRegularExpression(PATRON_NOMBRE))


def _validar_nombre(nombre):
    import re
    return bool(re.match(PATRON_NOMBRE, nombre.strip()))


class DialogoPerfil(QDialog):
    """Permite al usuario ver y editar su propio perfil."""

    # Emite (respuesta, nombre_actualizado_hex) donde respuesta indica si
    # se borro la cuenta (guardamos como nro para simplificar la senal).
    cuenta_eliminada = None

    def __init__(self, nombre_usuario, almacen, parent=None):
        super().__init__(parent)
        self.nombre_usuario = nombre_usuario
        self.almacen = almacen
        self.setWindowTitle("Mi Perfil")
        self.setMinimumWidth(420)
        self.setStyleSheet(ESTILOS_DIALOGO)
        self.se_elimino = False
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        datos = self.almacen.obtener(self.nombre_usuario)

        lbl_titulo = QLabel("Mi Perfil")
        lbl_titulo.setObjectName("titulo_dialogo")
        layout.addWidget(lbl_titulo)

        form = QFormLayout()
        form.setSpacing(10)

        # Usuario (no editable)
        self.lbl_usuario = QLabel(datos["usuario"] if datos else self.nombre_usuario)
        form.addRow("Usuario:", self.lbl_usuario)

        # Rol (no editable)
        self.lbl_rol = QLabel(datos["rol"] if datos else "-")
        form.addRow("Rol:", self.lbl_rol)

        # Nombre (editable)
        self.txt_nombre = QLineEdit(datos["nombre"] if datos else "")
        self.txt_nombre.setMaxLength(60)
        self.txt_nombre.setValidator(_validador_nombre())
        form.addRow("Nombre completo:", self.txt_nombre)

        layout.addLayout(form)

        # --- Cambiar contrasena ---
        btn_cambiar = QPushButton("Cambiar Contrasena")
        btn_cambiar.clicked.connect(self._cambiar_contrasena)
        layout.addWidget(btn_cambiar)

        # --- Botones de accion ---
        layout_accion = QHBoxLayout()
        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setObjectName("exito")
        btn_guardar.clicked.connect(self._guardar)
        layout_accion.addWidget(btn_guardar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        layout_accion.addWidget(btn_cancelar)
        layout.addLayout(layout_accion)

        # --- Eliminar cuenta ---
        btn_eliminar = QPushButton("Eliminar mi cuenta")
        btn_eliminar.setObjectName("peligro")
        btn_eliminar.clicked.connect(self._eliminar_cuenta)
        layout.addWidget(btn_eliminar)

    def _guardar(self):
        """Guarda el nuevo nombre completo del usuario."""
        nuevo_nombre = self.txt_nombre.text().strip()
        if not nuevo_nombre:
            aviso(self, "Campo requerido", "El nombre no puede estar vacio.")
            return
        if not _validar_nombre(nuevo_nombre):
            aviso(self, "Nombre invalido",
                  "El nombre solo puede contener letras y espacios.")
            return
        self.almacen.editar_nombre(self.nombre_usuario, nuevo_nombre)
        info(self, "Perfil actualizado",
             f"Su nombre fue actualizado a '{nuevo_nombre}'.")
        self.accept()

    def _cambiar_contrasena(self):
        """Muestra campos para cambiar la contrasena."""
        dlg = DialogoCambiarContrasena(self.nombre_usuario, self.almacen, self)
        dlg.exec()

    def _eliminar_cuenta(self):
        """Elimina la cuenta del usuario logueado tras confirmar."""
        respuesta = aviso(
            self,
            "Eliminar cuenta",
            "Esto eliminara permanentemente su cuenta de usuario. "
            "Esta accion no se puede deshacer.\n\nDesea continuar?",
            icono=QMessageBox.Icon.Warning,
            botones=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            predeterminado=QMessageBox.StandardButton.No
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            self.almacen.eliminar(self.nombre_usuario)
            self.se_elimino = True
            info(self, "Cuenta eliminada",
                 "Su cuenta fue eliminada. Sera redirigido al inicio de sesion.")
            self.accept()


class DialogoCambiarContrasena(QDialog):
    """Dialogo para cambiar la contrasena del usuario logueado."""

    def __init__(self, nombre_usuario, almacen, parent=None):
        super().__init__(parent)
        self.nombre_usuario = nombre_usuario
        self.almacen = almacen
        self.setWindowTitle("Cambiar Contrasena")
        self.setMinimumWidth(400)
        self.setStyleSheet(ESTILOS_DIALOGO)
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        self.txt_actual = QLineEdit()
        self.txt_actual.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Contrasena actual:", self.txt_actual)

        self.txt_nueva = QLineEdit()
        self.txt_nueva.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Nueva contrasena:", self.txt_nueva)

        self.txt_confirmar = QLineEdit()
        self.txt_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Confirmar nueva:", self.txt_confirmar)

        layout.addLayout(form)

        layout_accion = QHBoxLayout()
        btn_aceptar = QPushButton("Cambiar")
        btn_aceptar.setObjectName("exito")
        btn_aceptar.clicked.connect(self._cambiar)
        layout_accion.addWidget(btn_aceptar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        layout_accion.addWidget(btn_cancelar)
        layout.addLayout(layout_accion)

    def _cambiar(self):
        actual = self.txt_actual.text()
        nueva = self.txt_nueva.text()
        confirmar = self.txt_confirmar.text()
        if nueva != confirmar:
            aviso(self, "Error", "Las contrasenas no coinciden.")
            return
        ok, error = self.almacen.cambiar_contrasena(self.nombre_usuario, actual, nueva)
        if not ok:
            aviso(self, "Error", error)
            return
        info(self, "Contrasena cambiada", "Su contrasena fue actualizada.")
        self.accept()


class DialogoRegistro(QDialog):
    """Dialogo para registrar una cuenta nueva desde el login."""

    def __init__(self, almacen, parent=None):
        super().__init__(parent)
        self.almacen = almacen
        self.setWindowTitle("Registrarse - Synchrolia")
        self.setMinimumWidth(420)
        self.setStyleSheet(ESTILOS_DIALOGO)
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl_titulo = QLabel("Crear una cuenta")
        lbl_titulo.setObjectName("titulo_dialogo")
        layout.addWidget(lbl_titulo)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre completo")
        self.txt_nombre.setMaxLength(60)
        self.txt_nombre.setValidator(_validador_nombre())
        form.addRow("Nombre completo:", self.txt_nombre)

        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Nombre de usuario")
        self.txt_usuario.setMaxLength(30)
        form.addRow("Usuario:", self.txt_usuario)

        self.txt_contrasena = QLineEdit()
        self.txt_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Contrasena:", self.txt_contrasena)

        self.txt_confirmar = QLineEdit()
        self.txt_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Confirmar contrasena:", self.txt_confirmar)

        layout.addLayout(form)

        layout_accion = QHBoxLayout()
        btn_registrar = QPushButton("Registrarse")
        btn_registrar.setObjectName("exito")
        btn_registrar.clicked.connect(self._registrar)
        layout_accion.addWidget(btn_registrar)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        layout_accion.addWidget(btn_cancelar)
        layout.addLayout(layout_accion)

    def _registrar(self):
        nombre = self.txt_nombre.text().strip()
        usuario = self.txt_usuario.text().strip()
        contrasena = self.txt_contrasena.text()
        confirmar = self.txt_confirmar.text()

        if not nombre or not usuario or not contrasena:
            aviso(self, "Campos requeridos", "Debe completar todos los campos.")
            return
        if not _validar_nombre(nombre):
            aviso(self, "Nombre invalido",
                  "El nombre solo puede contener letras y espacios.")
            return
        if contrasena != confirmar:
            aviso(self, "Error", "Las contrasenas no coinciden.")
            return

        # El registro publico siempre crea cuentas de Recepcionista.
        # Los roles de Administrador solo los asigna un administrador
        # desde el modulo de Configuracion.
        rol = "Recepcionista"
        ok, error = self.almacen.registrar(nombre, usuario, rol, contrasena)
        if not ok:
            aviso(self, "No se pudo registrar", error)
            return

        info(self, "Registro exitoso",
             f"Cuenta creada para '{usuario}'. Ya puede iniciar sesion.")
        self.accept()
