# -*- coding: utf-8 -*-
"""
Synchrolia SGRT
Modulo de estilos: paleta de colores y hoja de estilos (QSS) global.
El punto de entrada oficial de la app es app.py; este modulo aporta
COLORES y cargar_estilos() para aplicar el tema visual a la aplicacion.
"""

from PySide6.QtWidgets import QApplication

from rutas import ruta_recurso


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
    chevron_down = ruta_recurso("chevron_down.png").replace("\\", "/")
    chevron_up = ruta_recurso("chevron_up.png").replace("\\", "/")
    estilos = f"""
    /* ============================================================
       SYNCHROLIA SGRT - Tema Visual Global
       ============================================================ */

    /* Fuente base de toda la aplicacion */
    /* Segoe UI para lectura y cifras; Raleway para titulos y marca. */
    QWidget {{
        font-family: 'Segoe UI', 'Raleway', sans-serif;
        font-size: 13px;
        color: #333333;
    }}

    /* --- Botones generales (por defecto azul oscuro) --- */
    QPushButton {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #24476B, stop:1 #1B3A5C);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-family: 'Raleway', 'Segoe UI', sans-serif;
        font-weight: 700;
        font-size: 13px;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #2C5F8A, stop:1 #244F79);
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
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #E0B65C, stop:1 #D4A843);
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
    QPushButton#acento:disabled {{
        background-color: #E6E0D2;
        color: #9C9587;
    }}

    /* Boton de peligro (rojo - eliminar/cancelar) */
    QPushButton#peligro {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #D02828, stop:1 #BC1515);
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
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #5CC15F, stop:1 #4CAF50);
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

    /* Boton de exito suave (acciones de avance de estado) */
    QPushButton#exito_suave {{
        background-color: #F1F9F1;
        color: #2E6B32;
        border: 1px solid #A9D4AC;
        font-weight: 600;
    }}
    QPushButton#exito_suave:hover {{
        background-color: #E1F2E2;
        border-color: #6DAF71;
    }}
    QPushButton#exito_suave:pressed {{
        background-color: #D2EAD4;
    }}
    QPushButton#exito_suave:disabled {{
        background-color: #F5F7F5;
        color: #A5AFA6;
        border-color: #E1E6E1;
    }}

    /* Boton secundario (contorno - acciones secundarias) */
    QPushButton#secundario {{
        background-color: #FFFFFF;
        color: #1B3A5C;
        border: 1px solid #C8D3DE;
        font-weight: 600;
    }}
    QPushButton#secundario:hover {{
        background-color: #EEF4F9;
        border-color: #2C5F8A;
    }}
    QPushButton#secundario:pressed {{
        background-color: #DFEAF3;
    }}
    QPushButton#secundario:disabled {{
        background-color: #F7F8FA;
        color: #A0A7B0;
        border-color: #E2E6EA;
    }}

    /* Boton de peligro con contorno (acciones destructivas discretas) */
    QPushButton#peligro_borde {{
        background-color: #FFFFFF;
        color: #A61B1B;
        border: 1px solid #E3B4B4;
        font-weight: 600;
    }}
    QPushButton#peligro_borde:hover {{
        background-color: #FDF1F1;
        border-color: #BC1515;
    }}
    QPushButton#peligro_borde:pressed {{
        background-color: #F9E1E1;
    }}
    QPushButton#peligro_borde:disabled {{
        background-color: #F8F7F7;
        color: #B9A5A5;
        border-color: #E9DDDD;
    }}

    QPushButton#perfil_sidebar {{
        background-color: transparent;
        color: #FFFFFF;
        border: 1px solid rgba(212, 168, 67, 0.70);
        font-weight: 600;
    }}
    QPushButton#perfil_sidebar:hover {{
        background-color: rgba(212, 168, 67, 0.14);
        border-color: #D4A843;
    }}
    QPushButton#cerrar_sidebar {{
        background-color: transparent;
        color: #F0B7B4;
        border: 1px solid rgba(240, 183, 180, 0.55);
        font-weight: 600;
    }}
    QPushButton#cerrar_sidebar:hover {{
        background-color: rgba(188, 21, 21, 0.18);
        border-color: #E6A3A0;
        color: #FFFFFF;
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
    QLineEdit:focus, QTextEdit:focus, QSpinBox:focus,
    QTimeEdit:focus, QDateEdit:focus {{
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
        width: 28px;
        border-left: 1px solid #E0E0E0;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
        background-color: #F5F5F5;
    }}
    QComboBox::down-arrow {{
        image: url("{chevron_down}");
        width: 12px;
        height: 7px;
    }}
    QComboBox QAbstractItemView {{
        background-color: #FFFFFF;
        border: 1px solid #D7DEE6;
        padding: 4px;
        selection-background-color: #E8F0F7;
        selection-color: #1B3A5C;
        outline: 0;
    }}

    /* --- Flechas de los SpinBox --- */
    QSpinBox {{
        padding-right: 26px;
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        subcontrol-origin: border;
        width: 20px;
        background-color: #F5F7FA;
        border-left: 1px solid #D7DEE6;
    }}
    QSpinBox::up-button {{
        subcontrol-position: top right;
        border-top-right-radius: 6px;
    }}
    QSpinBox::down-button {{
        subcontrol-position: bottom right;
        border-bottom-right-radius: 6px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: #E8EEF5;
    }}
    QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{
        background-color: #DCE6F0;
    }}
    QSpinBox::up-arrow {{
        image: url("{chevron_up}");
        width: 9px;
        height: 6px;
    }}
    QSpinBox::down-arrow {{
        image: url("{chevron_down}");
        width: 9px;
        height: 6px;
    }}

    /* --- Tablas --- */
    QTableWidget {{
        background-color: white;
        alternate-background-color: #F8FAFC;
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        gridline-color: #EAEDF1;
        selection-background-color: #E8F0F7;
        selection-color: #1B3A5C;
        font-family: 'Segoe UI', sans-serif;
        font-size: 13px;
    }}
    QTableWidget::item {{
        padding: 8px 10px;
    }}
    QTableWidget::item:selected {{
        background-color: #E8F0F7;
        color: #1B3A5C;
    }}

    /* Encabezados de tabla */
    QHeaderView::section {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #24476B, stop:1 #1B3A5C);
        color: white;
        padding: 9px 8px;
        border: none;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
        font-size: 12px;
    }}
    QTableCornerButton::section {{
        background-color: #1B3A5C;
        border: none;
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
        color: #6B7280;
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
        border-radius: 12px;
        padding: 16px;
    }}
    QFrame#tarjeta_acento {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                          stop:0 #24476B, stop:1 #13293F);
        border-radius: 12px;
        padding: 16px;
    }}

    /* --- Sidebar --- */
    QFrame#sidebar {{
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #1B3A5C, stop:1 #13293F);
        border: none;
    }}

    /* --- GroupBox --- */
    QGroupBox {{
        font-family: 'Raleway', 'Segoe UI', sans-serif;
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
        font-size: 14px;
        background-color: #FFFFFF;
    }}

    /* --- Pestanas --- */
    QTabWidget::pane {{
        border: 1px solid #E0E0E0;
        border-radius: 6px;
        background: #FFFFFF;
        top: -1px;
    }}
    QTabBar::tab {{
        background: #EEF2F6;
        color: #5C6773;
        padding: 10px 18px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
        font-size: 13px;
    }}
    QTabBar::tab:hover {{
        background: #E3EAF1;
        color: #1B3A5C;
    }}
    QTabBar::tab:selected {{
        background: #FFFFFF;
        color: #1B3A5C;
        border-bottom: 2px solid #D4A843;
    }}
    """
    app.setStyleSheet(estilos)
