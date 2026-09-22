# -*- coding: utf-8 -*-
"""
Modulo: Fuentes
Centraliza la carga de las tipografias corporativas de la aplicacion:
- Principal: Raleway (variable font, cubre pesos Regulares, Semibold,
  Bold, etc. desde un unico archivo). Se usa para titulos, marca y
  numeros destacados.
- Secundaria: Merriweather (serif). Se usa para el cuerpo de texto e
  informacion detallada.
Expone helpers para crear QFont de cada familia.
"""

from PySide6.QtGui import QFontDatabase
from rutas import (
    FUENTE_RALEWAY, FAMILIA_RALEWAY,
    FUENTE_MERRIWEATHER, FAMILIA_MERRIWEATHER,
)


_raleway_cargada = False
_merriweather_cargada = False
_id_raleway = None
_id_merriweather = None


def cargar_fuente_raleway():
    """Carga la tipografia principal Raleway en la aplicacion.

    Devuelve True si cargo correctamente (o ya estaba cargada).
    Se debe llamar una vez al iniciar la app, antes de crear ventanas.
    """
    global _raleway_cargada, _id_raleway
    if _raleway_cargada:
        return True
    _id_raleway = QFontDatabase.addApplicationFont(FUENTE_RALEWAY)
    if _id_raleway == -1:
        return False
    _raleway_cargada = True
    return True


def cargar_fuente_merriweather():
    """Carga la tipografia secundaria Merriweather en la aplicacion.

    Devuelve True si cargo correctamente (o ya estaba cargada).
    """
    global _merriweather_cargada, _id_merriweather
    if _merriweather_cargada:
        return True
    _id_merriweather = QFontDatabase.addApplicationFont(FUENTE_MERRIWEATHER)
    if _id_merriweather == -1:
        return False
    _merriweather_cargada = True
    return True


def cargar_fuentes():
    """Carga las dos tipografias corporativas (Raleway + Merriweather)."""
    return cargar_fuente_raleway() and cargar_fuente_merriweather()


def qfont_raleway(tamano=13, peso=400):
    """Crea un QFont de la familia principal Raleway (si cargo).

    peso es un valor numerico (400 normal, 700 bold, etc.) compatible
    con la fuente variable Raleway.
    """
    from PySide6.QtGui import QFont
    if not _raleway_cargada:
        cargar_fuente_raleway()
    if not _raleway_cargada:
        return QFont("Segoe UI", tamano)
    fuente = QFont(FAMILIA_RALEWAY, tamano)
    try:
        fuente.setWeight(QFont.Weight(peso))
    except (TypeError, ValueError):
        fuente.setWeight(QFont.Weight.Normal)
    return fuente


def qfont_merriweather(tamano=13, peso=400):
    """Crea un QFont de la familia secundaria Merriweather (si cargo).

    peso es un valor numerico compatible con la fuente variable.
    Si no cargo, usa un fallback serif legible.
    """
    from PySide6.QtGui import QFont
    if not _merriweather_cargada:
        cargar_fuente_merriweather()
    if not _merriweather_cargada:
        return QFont("Georgia", tamano)
    fuente = QFont(FAMILIA_MERRIWEATHER, tamano)
    try:
        fuente.setWeight(QFont.Weight(peso))
    except (TypeError, ValueError):
        fuente.setWeight(QFont.Weight.Normal)
    return fuente
