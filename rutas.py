# -*- coding: utf-8 -*-
"""
Utilidades para acceder a los recursos graficos de la aplicacion
(logo y banner) usando rutas relativas y robustas.
"""

import os

# Directorio raiz del proyecto Synchrolia
RAIZ = os.path.dirname(os.path.abspath(__file__))
RECURSOS = os.path.join(RAIZ, "Recursos")

LOGO_PATH = os.path.join(RECURSOS, "logo_marca.png")
BANNER_LOGIN = os.path.join(RECURSOS, "banner_login.jpg")
BANNER_DASHBOARD = os.path.join(RECURSOS, "banner_dashboard.jpg")

# Fuente corporativa Raleway (variable: cubre regular, semi/bold, etc.)
FUENTE_RALEWAY = os.path.join(RECURSOS, "fuentes", "Raleway[wght].ttf")
FAMILIA_RALEWAY = "Raleway"

# Tipografia secundaria Merriweather (serif): cuerpo de texto
FUENTE_MERRIWEATHER = os.path.join(RECURSOS, "fuentes", "Merriweather-Variable.ttf")
FAMILIA_MERRIWEATHER = "Merriweather"


def ruta_recurso(nombre_archivo):
    """Devuelve la ruta absoluta a un archivo dentro de Recursos/."""
    return os.path.join(RECURSOS, nombre_archivo)
