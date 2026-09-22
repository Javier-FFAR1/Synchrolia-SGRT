# -*- coding: utf-8 -*-
"""
Synchrolia SGRT
Modulo de estilos: paleta de colores y hoja de estilos (QSS) global.
El punto de entrada oficial de la app es app.py; este modulo aporta
COLORES y cargar_estilos() para aplicar el tema visual a la aplicacion.
"""

from PySide6.QtWidgets import QApplication


# Paleta de colores Synchrolia - usada globalmente en QSS
COLORES = {
    "primario": "#1B3A5C",
    "secundario": "#2C5F8A",
    "acento": "#D4A843",
    "neutro_claro": "#F5F5F5",
    "neutro_oscuro": "#0D1B2A",
    "blanco": "#FFFFFF",
    "texto": "#333333",
    "texto_claro": "#888888",
    "borde": "#E0E0E0",
    # Estados de mesas
    "libre": "#4CAF50",
    "ocupada": "#BC1515",
    "reservada": "#FF9800",
    "mantenimiento": "#9E9E9E",
}


def cargar_estilos(app: QApplication):
    """Carga la hoja de estilos QSS global de la aplicacion."""
    estilos = f"""
    /* ============================================================
       SYNCHROLIA SGRT - Tema Visual Global
       ============================================================ */

    /* Fuente base de toda la aplicacion */
    /* Tipografia secundaria (Merriweather) para el cuerpo de texto;
       los titulos y la marca usan la principal (Raleway) mas abajo. */
    QWidget {{
        font-family: 'Merriweather', 'Segoe UI', serif;
        font-size: 13px;
        color: #333333;
    }}

    /* --- Botones generales (por defecto azul oscuro) --- */
    QPushButton {{
        background-color: #1B3A5C;
        color: white;
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
    QPushButton:pressed {{
        background-color: #0D1B2A;
    }}
    QPushButton:disabled {{
        background-color: #E0E0E0;
        color: #999999;
    }}

    /* Boton de acento (dorado - acciones principales) */
    QPushButton#acento {{
        background-color: #D4A843;
        color: #0D1B2A;
        font-weight: 700;
        border: none;
    }}
    QPushButton#acento:hover {{
        background-color: #C49A3C;
    }}
    QPushButton#acento:pressed {{
        background-color: #B8892E;
    }}

    /* Boton de peligro (rojo - eliminar/cancelar) */
    QPushButton#peligro {{
        background-color: #BC1515;
        color: white;
        font-weight: 700;
        border: none;
    }}
    QPushButton#peligro:hover {{
        background-color: #9C1212;
    }}
    QPushButton#peligro:pressed {{
        background-color: #8E1010;
    }}

    /* Boton de exito (verde - confirmar/guardar) */
    QPushButton#exito {{
        background-color: #4CAF50;
        color: white;
        font-weight: 700;
        border: none;
    }}
    QPushButton#exito:hover {{
        background-color: #388E3C;
    }}
    QPushButton#exito:pressed {{
        background-color: #2E7D32;
    }}

    /* Boton secundario (gris - acciones secundarias) */
    QPushButton#secundario {{
        background-color: #F0F0F0;
        color: #333333;
        border: 1px solid #CCCCCC;
        font-weight: 600;
    }}
    QPushButton#secundario:hover {{
        background-color: #E0E0E0;
    }}
    QPushButton#secundario:pressed {{
        background-color: #D0D0D0;
    }}

    /* --- Campos de texto --- */
    QLineEdit, QTextEdit, QSpinBox, QTimeEdit, QDateEdit {{
        background-color: #F5F5F5;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
        color: #333333;
        min-height: 18px;
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border: 2px solid #2C5F8A;
        background-color: white;
    }}

    /* Campos de contrasena: se usa una fuente sans-serif para que los
       puntos del echo (Password) se vean del tamano normal; la fuente
       serif (Merriweather) los dibuja demasiado grandes. */
    QLineEdit[echoMode="2"] {{
        font-family: 'Raleway', 'Segoe UI', sans-serif;
    }}

    /* --- Combobox --- */
    QComboBox {{
        background-color: #F5F5F5;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
        min-height: 18px;
    }}
    QComboBox:focus {{
        border: 2px solid #2C5F8A;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left: 1px solid #E0E0E0;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
        background-color: #F5F5F5;
    }}

    /* --- Tablas --- */
    QTableWidget {{
        background-color: white;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        gridline-color: #E0E0E0;
        selection-background-color: #2C5F8A;
        selection-color: white;
    }}
    QTableWidget::item {{
        padding: 6px 8px;
    }}
    QTableWidget::item:selected {{
        background-color: #2C5F8A;
    }}

    /* Encabezados de tabla */
    QHeaderView::section {{
        background-color: #1B3A5C;
        color: white;
        padding: 8px;
        border: none;
        font-weight: 600;
        font-size: 12px;
    }}

    /* --- Scrollbars --- */
    QScrollBar:vertical {{
        background-color: #F5F5F5;
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background-color: #2C5F8A;
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: #1B3A5C;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* --- Labels de titulo (tipografia principal Raleway) --- */
    QLabel#titulo {{
        font-family: 'Raleway', 'Segoe UI', sans-serif;
        font-size: 22px;
        font-weight: 700;
        color: #1B3A5C;
    }}
    QLabel#subtitulo {{
        font-family: 'Raleway', 'Segoe UI', sans-serif;
        font-size: 14px;
        font-weight: 500;
        color: #888888;
    }}
    QLabel#marca {{
        font-family: 'Raleway', 'Segoe UI', sans-serif;
        font-size: 16px;
        font-weight: 700;
        color: #D4A843;
    }}

    /* --- Tarjetas (estadisticas) --- */
    QFrame#tarjeta {{
        background-color: white;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 16px;
    }}
    QFrame#tarjeta_acento {{
        background-color: #1B3A5C;
        border-radius: 10px;
        padding: 16px;
    }}

    /* --- Sidebar --- */
    QFrame#sidebar {{
        background-color: #1B3A5C;
        border: none;
    }}

    /* --- GroupBox --- */
    QGroupBox {{
        font-weight: 600;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 20px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: #1B3A5C;
    }}
    """
    app.setStyleSheet(estilos)
