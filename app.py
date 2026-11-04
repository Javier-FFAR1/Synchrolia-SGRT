
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from rutas import LOGO_PATH
from estilos import cargar_estilos
from modulos.fuentes import cargar_fuente_raleway, cargar_fuente_merriweather
from modulos.ventana_login import VentanaLogin
from modulos.ventana_principal import VentanaPrincipal
from modulos.almacen_datos import MESAS, _sincronizar_estado_mesa_bd


def _refrescar_estados_mesas_en_bd():
    """Actualiza mesas.id_estado_mesa acorde a las reservas del dia actual.

    Se ejecuta al abrir la aplicacion para que el estado guardado en la BD
    nunca quede desactualizado (cambio de dia, reservas hechas fuera de la app).
    """
    for m in MESAS:
        _sincronizar_estado_mesa_bd(m["numero"])


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Synchrolia SGRT")
    app.setOrganizationName("UNAN-Leon")

    # Forzar estilo Fusion para que QSS funcione correctamente en Windows
    app.setStyle("Fusion")

    # Icono de la aplicacion
    app.setWindowIcon(QIcon(LOGO_PATH))

    # Aplicar estilos globales
    cargar_estilos(app)

    # Cargar las tipografias corporativas Raleway (principal) y
    # Merriweather (secundaria)
    cargar_fuente_raleway()
    cargar_fuente_merriweather()

    # ventana_login y ventana_principal se comunican por senales (Signal)
    # para desacoplar los modulos entre si.
    login = VentanaLogin()

    # Sincronizar el estado de las mesas en la BD con el dia actual
    _refrescar_estados_mesas_en_bd()

    ventana_main = None

    def abrir_ventana_principal(login_usuario, nombre, rol):
        nonlocal ventana_main
        ventana_main = VentanaPrincipal(login_usuario, nombre, rol)
        ventana_main.cerrar_sesion.connect(lambda: reabrir_login(ventana_main))
        ventana_main.show()

    def reabrir_login(ventana_actual):
        nonlocal ventana_main
        ventana_actual.close()
        ventana_main = None
        login.show()
        login.txt_usuario.clear()
        login.txt_contrasena.clear()
        login.txt_usuario.setFocus()

    login.login_exitoso.connect(abrir_ventana_principal)

    login.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
