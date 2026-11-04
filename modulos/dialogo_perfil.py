# -*- coding: utf-8 -*-
"""
Dialogos de gestion de usuarios:
- DialogoPerfil: permite al usuario logueado editar su nombre, cambiar su
  contrasena y eliminar su propia cuenta.
- DialogoRegistro: permite crear una cuenta nueva desde el login.
"""

from PySide6.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QRegularExpression
from PySide6.QtGui import QRegularExpressionValidator

# Patron de solo letras (incluye acentos y espacio) para nombres completos
PATRON_NOMBRE = r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü' ]+$"

# Colores del tema oscuro (coherentes con la ventana de login)
FONDO_OSCURO = "#0D1B2A"
TEXTO_CLARO = "#FFFFFF"
DORADO = "#D4A843"
PRIMARIO_OSCURO = "#1B3A5C"


ESTILOS_PERFIL = f"""
QDialog#perfil_dialogo, QDialog#password_dialogo {{
    background-color: #F4F7FA;
}}
QLabel {{
    background-color: transparent;
}}
QFrame#perfil_encabezado {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 #1B3A5C, stop:1 #13293F);
    border-radius: 12px;
}}
QLabel#perfil_avatar {{
    background-color: {DORADO};
    color: {FONDO_OSCURO};
    border-radius: 28px;
    font-family: 'Raleway', 'Segoe UI', sans-serif;
    font-size: 22px;
    font-weight: 700;
}}
QLabel#perfil_nombre {{
    color: #FFFFFF;
    font-family: 'Raleway', 'Segoe UI', sans-serif;
    font-size: 20px;
    font-weight: 700;
}}
QLabel#perfil_meta {{
    color: #D7E0E9;
    font-size: 12px;
}}
QLabel#perfil_rol {{
    color: #F6E3B9;
    background-color: rgba(212, 168, 67, 0.16);
    border: 1px solid rgba(212, 168, 67, 0.55);
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}}
QFrame#perfil_tarjeta {{
    background-color: #FFFFFF;
    border: 1px solid #E0E5EB;
    border-radius: 12px;
}}
QFrame#perfil_peligro {{
    background-color: #FFF8F8;
    border: 1px solid #EED2D2;
    border-radius: 12px;
}}
QLabel#perfil_seccion {{
    color: {PRIMARIO_OSCURO};
    font-family: 'Raleway', 'Segoe UI', sans-serif;
    font-size: 14px;
    font-weight: 700;
}}
QLabel#perfil_descripcion {{
    color: #6B7280;
    font-size: 12px;
}}
QLabel#perfil_valor {{
    color: {PRIMARIO_OSCURO};
    font-weight: 600;
}}
QLabel#perfil_peligro_titulo {{
    color: #A61B1B;
    font-family: 'Raleway', 'Segoe UI', sans-serif;
    font-size: 14px;
    font-weight: 700;
}}
QLabel#perfil_peligro_descripcion {{
    color: #8A4C4C;
    font-size: 12px;
}}
QLabel#perfil_titulo {{
    color: {PRIMARIO_OSCURO};
    font-family: 'Raleway', 'Segoe UI', sans-serif;
    font-size: 20px;
    font-weight: 700;
}}
"""


ESTILOS_REGISTRO = ESTILOS_PERFIL + f"""
QDialog#registro_dialogo {{
    background-color: #F4F7FA;
}}
QFrame#registro_encabezado {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                      stop:0 #1B3A5C, stop:1 #13293F);
    border-radius: 12px;
}}
QLabel#registro_icono {{
    background-color: {DORADO};
    color: {FONDO_OSCURO};
    border-radius: 28px;
    font-family: 'Raleway', 'Segoe UI', sans-serif;
    font-size: 24px;
    font-weight: 700;
}}
QLabel#registro_titulo {{
    color: #FFFFFF;
    font-family: 'Raleway', 'Segoe UI', sans-serif;
    font-size: 20px;
    font-weight: 700;
}}
QLabel#registro_subtitulo {{
    color: #D7E0E9;
    font-size: 12px;
}}
QLabel#registro_rol {{
    color: #F6E3B9;
    background-color: rgba(212, 168, 67, 0.16);
    border: 1px solid rgba(212, 168, 67, 0.55);
    border-radius: 10px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}}
QFrame#registro_tarjeta {{
    background-color: #FFFFFF;
    border: 1px solid #E0E5EB;
    border-radius: 12px;
}}
QLabel#registro_seccion {{
    color: {PRIMARIO_OSCURO};
    font-family: 'Raleway', 'Segoe UI', sans-serif;
    font-size: 14px;
    font-weight: 700;
}}
QLabel#registro_descripcion {{
    color: #6B7280;
    font-size: 12px;
}}
QLabel#registro_etiqueta {{
    color: #4B5563;
    font-size: 12px;
    font-weight: 600;
}}
QDialog#registro_dialogo QLineEdit {{
    background-color: #FFFFFF;
    border: 1px solid #D7DEE6;
    border-radius: 8px;
    padding: 9px 12px;
    color: #1F2937;
    font-size: 13px;
    min-height: 20px;
}}
QDialog#registro_dialogo QLineEdit:focus {{
    border: 2px solid {DORADO};
    background-color: #FFFFFF;
}}
QDialog#registro_dialogo QLineEdit[echoMode="2"] {{
    font-family: 'Raleway', 'Segoe UI', sans-serif;
}}
QDialog#registro_dialogo QPushButton {{
    border-radius: 8px;
    padding: 9px 20px;
    font-family: 'Raleway', 'Segoe UI', sans-serif;
    font-size: 13px;
    min-height: 20px;
}}
QDialog#registro_dialogo QPushButton#secundario {{
    background-color: #FFFFFF;
    color: #1B3A5C;
    border: 1px solid #C8D3DE;
    font-weight: 600;
}}
QDialog#registro_dialogo QPushButton#secundario:hover {{
    background-color: #EEF4F9;
    border-color: #2C5F8A;
}}
QDialog#registro_dialogo QPushButton#secundario:pressed {{
    background-color: #DFEAF3;
}}
QDialog#registro_dialogo QPushButton#secundario:disabled {{
    background-color: #F7F8FA;
    color: #A0A7B0;
    border-color: #E2E6EA;
}}
QDialog#registro_dialogo QPushButton#acento {{
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                      stop:0 #E0B65C, stop:1 #D4A843);
    color: #0D1B2A;
    border: none;
    font-weight: 700;
}}
QDialog#registro_dialogo QPushButton#acento:hover {{
    background-color: #C49A3C;
}}
QDialog#registro_dialogo QPushButton#acento:pressed {{
    background-color: #B8892E;
}}
QDialog#registro_dialogo QPushButton#acento:disabled {{
    background-color: #E6E0D2;
    color: #9C9587;
}}
"""


AVISO_QSS = "QMessageBox { background-color: %s; color: %s; } QLabel { color: %s; } QPushButton { background-color: #1B3A5C; color: #FFFFFF; border-radius: 6px; padding: 6px 14px; font-weight: 700; }" % (FONDO_OSCURO, TEXTO_CLARO, TEXTO_CLARO)
AVISO_QSS_CLARO = "QMessageBox { background-color: #FFFFFF; } QMessageBox QLabel { color: #333333; font-size: 13px; } QPushButton { background-color: #1B3A5C; color: #FFFFFF; border-radius: 6px; padding: 6px 14px; font-weight: 700; }"


def aviso(padre, titulo, texto, icono=QMessageBox.Icon.Warning,
          botones=QMessageBox.StandardButton.Ok,
          predeterminado=None, claro=False):
    """Muestra un QMessageBox legible sobre el tema del dialogo."""
    msg = QMessageBox(padre)
    msg.setIcon(icono)
    msg.setWindowTitle(titulo)
    if claro:
        msg.setText(texto)
    else:
        msg.setText('<span style="color:%s;">%s</span>' % (TEXTO_CLARO, texto))
    msg.setStandardButtons(botones)
    if predeterminado is not None:
        msg.setDefaultButton(predeterminado)
    msg.setStyleSheet(AVISO_QSS_CLARO if claro else AVISO_QSS)
    return msg.exec()


def info(padre, titulo, texto, claro=False):
    return aviso(
        padre, titulo, texto,
        icono=QMessageBox.Icon.Information,
        claro=claro
    )


def _validador_nombre():
    return QRegularExpressionValidator(QRegularExpression(PATRON_NOMBRE))


def _validar_nombre(nombre):
    import re
    return bool(re.match(PATRON_NOMBRE, nombre.strip()))


class DialogoPerfil(QDialog):
    """Permite al usuario ver y editar su propio perfil."""

    cuenta_eliminada = None

    def __init__(self, nombre_usuario, almacen, parent=None):
        super().__init__(parent)
        self.nombre_usuario = nombre_usuario
        self.almacen = almacen
        self.setWindowTitle("Mi Perfil")
        self.setObjectName("perfil_dialogo")
        self.setMinimumWidth(560)
        self.resize(600, 670)
        self.setStyleSheet(ESTILOS_PERFIL)
        self.se_elimino = False
        self._datos = self.almacen.obtener(self.nombre_usuario) or {}
        self._construir_interfaz()

    @staticmethod
    def _iniciales(nombre):
        partes = [parte for parte in nombre.split() if parte]
        if not partes:
            return "?"
        return "".join(parte[0] for parte in partes[:2]).upper()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 18)
        layout.setSpacing(14)

        nombre = self._datos.get("nombre") or self.nombre_usuario
        usuario = self._datos.get("usuario") or self.nombre_usuario
        rol = self._datos.get("rol") or "Sin rol"

        encabezado = QFrame()
        encabezado.setObjectName("perfil_encabezado")
        layout_encabezado = QHBoxLayout(encabezado)
        layout_encabezado.setContentsMargins(20, 18, 20, 18)
        layout_encabezado.setSpacing(16)

        lbl_avatar = QLabel(self._iniciales(nombre))
        lbl_avatar.setObjectName("perfil_avatar")
        lbl_avatar.setFixedSize(56, 56)
        lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_encabezado.addWidget(
            lbl_avatar, 0, Qt.AlignmentFlag.AlignVCenter
        )

        layout_texto = QVBoxLayout()
        layout_texto.setSpacing(4)

        lbl_nombre = QLabel(nombre)
        lbl_nombre.setObjectName("perfil_nombre")
        lbl_nombre.setWordWrap(True)
        layout_texto.addWidget(lbl_nombre)

        layout_meta = QHBoxLayout()
        layout_meta.setSpacing(8)
        lbl_usuario = QLabel(f"@{usuario}")
        lbl_usuario.setObjectName("perfil_meta")
        lbl_rol = QLabel(rol)
        lbl_rol.setObjectName("perfil_rol")
        layout_meta.addWidget(lbl_usuario)
        layout_meta.addWidget(lbl_rol)
        layout_meta.addStretch()
        layout_texto.addLayout(layout_meta)

        layout_encabezado.addLayout(layout_texto, 1)
        layout.addWidget(encabezado)

        lbl_intro = QLabel(
            "Gestiona tu información personal y la seguridad de tu cuenta."
        )
        lbl_intro.setObjectName("perfil_descripcion")
        layout.addWidget(lbl_intro)

        tarjeta_info = QFrame()
        tarjeta_info.setObjectName("perfil_tarjeta")
        layout_info = QVBoxLayout(tarjeta_info)
        layout_info.setContentsMargins(20, 18, 20, 18)
        layout_info.setSpacing(12)

        lbl_info = QLabel("Información personal")
        lbl_info.setObjectName("perfil_seccion")
        layout_info.addWidget(lbl_info)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        lbl_usuario_valor = QLabel(usuario)
        lbl_usuario_valor.setObjectName("perfil_valor")
        form.addRow("Usuario:", lbl_usuario_valor)

        lbl_rol_valor = QLabel(rol)
        lbl_rol_valor.setObjectName("perfil_valor")
        form.addRow("Rol:", lbl_rol_valor)

        self.txt_nombre = QLineEdit(nombre)
        self.txt_nombre.setMaxLength(60)
        self.txt_nombre.setValidator(_validador_nombre())
        self.txt_nombre.setPlaceholderText("Nombre completo")
        form.addRow("Nombre completo:", self.txt_nombre)
        layout_info.addLayout(form)
        layout.addWidget(tarjeta_info)

        tarjeta_seguridad = QFrame()
        tarjeta_seguridad.setObjectName("perfil_tarjeta")
        layout_seguridad = QHBoxLayout(tarjeta_seguridad)
        layout_seguridad.setContentsMargins(20, 18, 20, 18)
        layout_seguridad.setSpacing(16)

        layout_seguridad_texto = QVBoxLayout()
        layout_seguridad_texto.setSpacing(4)
        lbl_seguridad = QLabel("Seguridad")
        lbl_seguridad.setObjectName("perfil_seccion")
        lbl_seguridad_desc = QLabel(
            "Actualiza tu contraseña para mantener tu cuenta protegida."
        )
        lbl_seguridad_desc.setObjectName("perfil_descripcion")
        lbl_seguridad_desc.setWordWrap(True)
        layout_seguridad_texto.addWidget(lbl_seguridad)
        layout_seguridad_texto.addWidget(lbl_seguridad_desc)

        btn_cambiar = QPushButton("Cambiar Contraseña")
        btn_cambiar.setObjectName("secundario")
        btn_cambiar.setMinimumHeight(36)
        btn_cambiar.setMinimumWidth(170)
        btn_cambiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cambiar.clicked.connect(self._cambiar_contrasena)

        layout_seguridad.addLayout(layout_seguridad_texto, 1)
        layout_seguridad.addWidget(
            btn_cambiar, 0, Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(tarjeta_seguridad)

        tarjeta_peligro = QFrame()
        tarjeta_peligro.setObjectName("perfil_peligro")
        layout_peligro = QHBoxLayout(tarjeta_peligro)
        layout_peligro.setContentsMargins(20, 18, 20, 18)
        layout_peligro.setSpacing(16)

        layout_peligro_texto = QVBoxLayout()
        layout_peligro_texto.setSpacing(4)
        lbl_peligro = QLabel("Eliminar cuenta")
        lbl_peligro.setObjectName("perfil_peligro_titulo")
        lbl_peligro_desc = QLabel(
            "Esta acción elimina tu acceso de forma permanente y no se puede deshacer."
        )
        lbl_peligro_desc.setObjectName("perfil_peligro_descripcion")
        lbl_peligro_desc.setWordWrap(True)
        layout_peligro_texto.addWidget(lbl_peligro)
        layout_peligro_texto.addWidget(lbl_peligro_desc)

        btn_eliminar = QPushButton("Eliminar mi cuenta")
        btn_eliminar.setObjectName("peligro_borde")
        btn_eliminar.setMinimumHeight(36)
        btn_eliminar.setMinimumWidth(150)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar.clicked.connect(self._eliminar_cuenta)

        layout_peligro.addLayout(layout_peligro_texto, 1)
        layout_peligro.addWidget(
            btn_eliminar, 0, Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(tarjeta_peligro)

        layout_accion = QHBoxLayout()
        layout_accion.setSpacing(8)
        layout_accion.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secundario")
        btn_cancelar.setMinimumHeight(38)
        btn_cancelar.setMinimumWidth(100)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        layout_accion.addWidget(btn_cancelar)

        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setObjectName("acento")
        btn_guardar.setMinimumHeight(38)
        btn_guardar.setMinimumWidth(150)
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.clicked.connect(self._guardar)
        layout_accion.addWidget(btn_guardar)
        layout.addLayout(layout_accion)

    def _guardar(self):
        """Guarda el nuevo nombre completo del usuario."""
        nuevo_nombre = self.txt_nombre.text().strip()
        if not nuevo_nombre:
            aviso(
                self, "Campo requerido",
                "El nombre no puede estar vacío.", claro=True
            )
            return
        if not _validar_nombre(nuevo_nombre):
            aviso(
                self, "Nombre inválido",
                "El nombre solo puede contener letras y espacios.",
                claro=True
            )
            return
        if nuevo_nombre == (self._datos.get("nombre") or ""):
            self.accept()
            return
        if not self.almacen.editar_nombre(self.nombre_usuario, nuevo_nombre):
            aviso(
                self, "No se pudo actualizar",
                "No fue posible guardar los cambios del perfil.",
                claro=True
            )
            return
        info(
            self, "Perfil actualizado",
            f"Su nombre fue actualizado a '{nuevo_nombre}'.",
            claro=True
        )
        self.accept()

    def _cambiar_contrasena(self):
        """Muestra campos para cambiar la contrasena."""
        dlg = DialogoCambiarContrasena(self.nombre_usuario, self.almacen, self)
        dlg.exec()

    def _eliminar_cuenta(self):
        """Elimina la cuenta del usuario logueado tras confirmar."""
        if self._datos.get("rol") == "Administrador":
            aviso(
                self,
                "Acción no permitida",
                "Las cuentas de administrador no pueden eliminarse desde el "
                "perfil, para evitar que el sistema quede sin acceso "
                "administrativo.",
                icono=QMessageBox.Icon.Warning,
                claro=True
            )
            return
        respuesta = aviso(
            self,
            "Eliminar cuenta",
            "Esto eliminará permanentemente su cuenta de usuario. "
            "Esta acción no se puede deshacer.\n\n¿Desea continuar?",
            icono=QMessageBox.Icon.Warning,
            botones=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            predeterminado=QMessageBox.StandardButton.No,
            claro=True
        )
        if respuesta == QMessageBox.StandardButton.Yes:
            if not self.almacen.eliminar(self.nombre_usuario):
                aviso(
                    self, "No se pudo eliminar",
                    "No fue posible eliminar la cuenta en este momento.",
                    claro=True
                )
                return
            self.se_elimino = True
            info(
                self, "Cuenta eliminada",
                "Su cuenta fue eliminada. Será redirigido al inicio de sesión.",
                claro=True
            )
            self.accept()


class DialogoCambiarContrasena(QDialog):
    """Dialogo para cambiar la contrasena del usuario logueado."""

    def __init__(self, nombre_usuario, almacen, parent=None):
        super().__init__(parent)
        self.nombre_usuario = nombre_usuario
        self.almacen = almacen
        self.setWindowTitle("Cambiar Contraseña")
        self.setObjectName("password_dialogo")
        self.setMinimumWidth(460)
        self.resize(480, 430)
        self.setStyleSheet(ESTILOS_PERFIL)
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 18)
        layout.setSpacing(14)

        lbl_titulo = QLabel("Cambiar contraseña")
        lbl_titulo.setObjectName("perfil_titulo")
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel(
            "Ingresa tu contraseña actual y define una nueva."
        )
        lbl_sub.setObjectName("perfil_descripcion")
        layout.addWidget(lbl_sub)

        tarjeta = QFrame()
        tarjeta.setObjectName("perfil_tarjeta")
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(20, 18, 20, 18)
        layout_tarjeta.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(12)

        self.txt_actual = QLineEdit()
        self.txt_actual.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_actual.setPlaceholderText("Contraseña actual")
        form.addRow("Contraseña actual:", self.txt_actual)

        self.txt_nueva = QLineEdit()
        self.txt_nueva.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_nueva.setPlaceholderText("Nueva contraseña")
        form.addRow("Nueva contraseña:", self.txt_nueva)

        self.txt_confirmar = QLineEdit()
        self.txt_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirmar.setPlaceholderText("Repite la nueva contraseña")
        form.addRow("Confirmar nueva:", self.txt_confirmar)

        layout_tarjeta.addLayout(form)
        layout.addWidget(tarjeta)

        layout_accion = QHBoxLayout()
        layout_accion.setSpacing(8)
        layout_accion.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secundario")
        btn_cancelar.setMinimumHeight(38)
        btn_cancelar.setMinimumWidth(100)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        layout_accion.addWidget(btn_cancelar)

        btn_aceptar = QPushButton("Cambiar Contraseña")
        btn_aceptar.setObjectName("acento")
        btn_aceptar.setMinimumHeight(38)
        btn_aceptar.setMinimumWidth(160)
        btn_aceptar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_aceptar.clicked.connect(self._cambiar)
        layout_accion.addWidget(btn_aceptar)
        layout.addLayout(layout_accion)

    def _cambiar(self):
        actual = self.txt_actual.text()
        nueva = self.txt_nueva.text()
        confirmar = self.txt_confirmar.text()
        if not actual or not nueva or not confirmar:
            aviso(
                self, "Campos requeridos",
                "Debe completar todos los campos.", claro=True
            )
            return
        if nueva != confirmar:
            aviso(
                self, "Error", "Las contraseñas no coinciden.", claro=True
            )
            return
        ok, error = self.almacen.cambiar_contrasena(
            self.nombre_usuario, actual, nueva
        )
        if not ok:
            aviso(self, "Error", error, claro=True)
            return
        info(
            self, "Contraseña cambiada",
            "Su contraseña fue actualizada.", claro=True
        )
        self.accept()


class DialogoRegistro(QDialog):
    """Dialogo para registrar una cuenta nueva desde el login."""

    def __init__(self, almacen, parent=None):
        super().__init__(parent)
        self.almacen = almacen
        self.setWindowTitle("Registrarse - Synchrolia")
        self.setObjectName("registro_dialogo")
        self.setMinimumWidth(560)
        self.resize(600, 660)
        self.setStyleSheet(ESTILOS_REGISTRO)
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(14)

        encabezado = QFrame()
        encabezado.setObjectName("registro_encabezado")
        layout_encabezado = QHBoxLayout(encabezado)
        layout_encabezado.setContentsMargins(20, 18, 20, 18)
        layout_encabezado.setSpacing(14)

        lbl_icono = QLabel("S")
        lbl_icono.setObjectName("registro_icono")
        lbl_icono.setFixedSize(56, 56)
        lbl_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_encabezado.addWidget(
            lbl_icono, 0, Qt.AlignmentFlag.AlignVCenter
        )

        layout_texto = QVBoxLayout()
        layout_texto.setSpacing(3)

        lbl_titulo = QLabel("Crea tu cuenta")
        lbl_titulo.setObjectName("registro_titulo")
        layout_texto.addWidget(lbl_titulo)

        lbl_subtitulo = QLabel(
            "Accede al sistema de reservas de Synchrolia."
        )
        lbl_subtitulo.setObjectName("registro_subtitulo")
        lbl_subtitulo.setWordWrap(True)
        layout_texto.addWidget(lbl_subtitulo)

        layout_encabezado.addLayout(layout_texto, 1)

        lbl_rol = QLabel("Recepción")
        lbl_rol.setObjectName("registro_rol")
        layout_encabezado.addWidget(
            lbl_rol, 0, Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(encabezado)

        lbl_intro = QLabel(
            "Completa tus datos para crear tu cuenta. "
            "Todos los campos son obligatorios."
        )
        lbl_intro.setObjectName("registro_descripcion")
        lbl_intro.setWordWrap(True)
        layout.addWidget(lbl_intro)

        tarjeta = QFrame()
        tarjeta.setObjectName("registro_tarjeta")
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(20, 18, 20, 18)
        layout_tarjeta.setSpacing(14)

        lbl_seccion = QLabel("Datos de la cuenta")
        lbl_seccion.setObjectName("registro_seccion")
        layout_tarjeta.addWidget(lbl_seccion)

        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej. María López")
        self.txt_nombre.setMaxLength(60)
        self.txt_nombre.setValidator(_validador_nombre())
        self._agregar_campo(
            layout_tarjeta, "Nombre completo", self.txt_nombre
        )

        self.txt_usuario = QLineEdit()
        self.txt_usuario.setPlaceholderText("Ej. recepcion01")
        self.txt_usuario.setMaxLength(30)
        self._agregar_campo(
            layout_tarjeta, "Nombre de usuario", self.txt_usuario
        )

        self.txt_contrasena = QLineEdit()
        self.txt_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_contrasena.setPlaceholderText("Crea una contraseña")
        self._agregar_campo(
            layout_tarjeta, "Contraseña", self.txt_contrasena
        )

        self.txt_confirmar = QLineEdit()
        self.txt_confirmar.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirmar.setPlaceholderText("Repite tu contraseña")
        self.txt_confirmar.returnPressed.connect(self._registrar)
        self._agregar_campo(
            layout_tarjeta, "Confirmar contraseña", self.txt_confirmar
        )

        lbl_nota = QLabel(
            "Las cuentas creadas desde aquí se registran con el rol "
            "Recepcionista."
        )
        lbl_nota.setObjectName("registro_descripcion")
        lbl_nota.setWordWrap(True)
        layout_tarjeta.addWidget(lbl_nota)

        layout.addWidget(tarjeta)
        layout.addStretch()

        layout_accion = QHBoxLayout()
        layout_accion.setSpacing(8)
        layout_accion.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setObjectName("secundario")
        btn_cancelar.setMinimumWidth(110)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.clicked.connect(self.reject)
        layout_accion.addWidget(btn_cancelar)

        btn_registrar = QPushButton("Crear cuenta")
        btn_registrar.setObjectName("acento")
        btn_registrar.setMinimumWidth(150)
        btn_registrar.setDefault(True)
        btn_registrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_registrar.clicked.connect(self._registrar)
        layout_accion.addWidget(btn_registrar)
        layout.addLayout(layout_accion)

    def _agregar_campo(self, layout, etiqueta, campo):
        contenedor = QVBoxLayout()
        contenedor.setSpacing(4)

        lbl = QLabel(etiqueta)
        lbl.setObjectName("registro_etiqueta")
        contenedor.addWidget(lbl)
        contenedor.addWidget(campo)
        layout.addLayout(contenedor)

    def _registrar(self):
        nombre = self.txt_nombre.text().strip()
        usuario = self.txt_usuario.text().strip()
        contrasena = self.txt_contrasena.text()
        confirmar = self.txt_confirmar.text()

        if not nombre or not usuario or not contrasena or not confirmar:
            aviso(
                self, "Campos requeridos",
                "Debe completar todos los campos.", claro=True
            )
            return
        if not _validar_nombre(nombre):
            aviso(
                self, "Nombre inválido",
                "El nombre solo puede contener letras y espacios.",
                claro=True
            )
            return
        if contrasena != confirmar:
            aviso(
                self, "Error", "Las contraseñas no coinciden.", claro=True
            )
            return

        # El registro publico siempre crea cuentas de Recepcionista.
        # Los roles de Administrador solo los asigna un administrador
        # desde el modulo de Configuracion.
        rol = "Recepcionista"
        ok, error = self.almacen.registrar(nombre, usuario, rol, contrasena)
        if not ok:
            aviso(
                self, "No se pudo registrar", error, claro=True
            )
            return

        info(
            self, "Registro exitoso",
            f"Cuenta creada para '{usuario}'. Ya puede iniciar sesión.",
            claro=True
        )
        self.accept()
