# -*- coding: utf-8 -*-
"""
Widget reutilizable: Buscador de clientes con autocomplete.
Permite escribir un nombre y muestra coincidencias en tiempo real.
Se puede usar en Reservas, Reportes, o cualquier modulo que necesite
seleccionar un cliente.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QFrame, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

PRIMARIO = "#1B3A5C"
SECUNDARIO = "#2C5F8A"
DORADO = "#D4A843"
NEUTRO_CLARO = "#F5F5F5"
BLANCO = "#FFFFFF"


class BuscadorCliente(QWidget):
    """
    Campo de busqueda de cliente con lista desplegable filtrada.
    
    Uso:
        buscador = BuscadorCliente()
        buscador.agregar_cliente(1, "Juan Perez", "88887777")
        buscador.agregar_cliente(2, "Maria Lopez", "77778888")
        
        # Obtener el cliente seleccionado
        id_cliente = buscador.obtener_id()
        nombre = buscador.obtener_nombre()
        
        # Conectar senal cuando se selecciona un cliente
        buscador.cliente_seleccionado.connect(mi_funcion)
    """
    
    # Senal que emite (id_cliente, nombre, telefono) cuando se selecciona un cliente
    cliente_seleccionado = Signal(int, str, str)
    
    # Senal que emite cuando se limpia la seleccion
    seleccion_limpiada = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)

        # La politica horizontal Ignored permite que el widget se comprima al
        # ancho disponible (en formularios estrechos) sin desbordar la ventana.
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        # Almacenamiento de clientes: [{id, nombre, telefono}, ...]
        self.clientes = []
        
        # Estado actual
        self._id_seleccionado = None
        self._nombre_seleccionado = ""
        self._telefono_seleccionado = ""
        self._mostrando_lista = False
        
        self._construir_interfaz()
    
    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Campo de texto principal
        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText("Escriba el nombre del cliente...")
        self.txt_busqueda.setMinimumHeight(36)
        self.txt_busqueda.setStyleSheet(f"""
            QLineEdit {{
                background-color: {NEUTRO_CLARO};
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #333;
            }}
            QLineEdit:focus {{
                border: 2px solid {SECUNDARIO};
                background-color: {BLANCO};
            }}
        """)
        
        # Conectar el evento de escritura para filtrar
        self.txt_busqueda.textChanged.connect(self._filtrar_clientes)
        self.txt_busqueda.textEdited.connect(self._on_texto_editado)
        
        layout.addWidget(self.txt_busqueda)
        
        # Lista desplegable de resultados
        self.lista_resultados = QListWidget()
        self.lista_resultados.setMaximumHeight(180)
        self.lista_resultados.setStyleSheet(f"""
            QListWidget {{
                background-color: {BLANCO};
                border: 1px solid #D0D0D0;
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                padding: 4px 0;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid #F0F0F0;
            }}
            QListWidget::item:hover {{
                background-color: #E8F0FE;
            }}
            QListWidget::item:selected {{
                background-color: {SECUNDARIO};
                color: white;
            }}
        """)
        self.lista_resultados.setVisible(False)
        self.lista_resultados.itemClicked.connect(self._seleccionar_cliente)
        
        layout.addWidget(self.lista_resultados)
        
        # Label que muestra el cliente seleccionado (cuando la lista esta oculta)
        self.lbl_seleccionado = QLabel()
        self.lbl_seleccionado.setWordWrap(True)
        self.lbl_seleccionado.setStyleSheet(f"""
            QLabel {{
                background-color: #E8F5E9;
                border: 1px solid #A5D6A7;
                border-radius: 6px;
                padding: 6px 12px;
                color: #2E7D32;
                font-weight: 600;
                font-size: 12px;
            }}
        """)
        self.lbl_seleccionado.setVisible(False)
        
        # Boton para limpiar seleccion
        layout_seleccion = QHBoxLayout()
        layout_seleccion.setContentsMargins(0, 4, 0, 0)
        layout_seleccion.addWidget(self.lbl_seleccionado)
        
        self.btn_limpiar = QLabel("[X] Cambiar")
        self.btn_limpiar.setStyleSheet(f"""
            QLabel {{
                color: {PRIMARIO};
                font-size: 11px;
                font-weight: 600;
                padding: 4px 8px;
                text-decoration: underline;
            }}
            QLabel:hover {{
                color: {DORADO};
            }}
        """)
        self.btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_limpiar.mousePressEvent = lambda e: self.limpiar_seleccion()
        layout_seleccion.addWidget(self.btn_limpiar)
        layout_seleccion.addStretch()
        
        self.widget_seleccion = QWidget()
        self.widget_seleccion.setLayout(layout_seleccion)
        self.widget_seleccion.setVisible(False)
        
        layout.addWidget(self.widget_seleccion)
    
    def agregar_cliente(self, id_cliente, nombre, telefono=""):
        """Agrega un cliente a la lista de busqueda."""
        self.clientes.append({
            "id": id_cliente,
            "nombre": nombre,
            "telefono": telefono,
        })
    
    def cargar_clientes(self, lista_clientes):
        """
        Carga una lista completa de clientes.
        lista_clientes: lista de tuplas [(id, nombre, telefono), ...]
        """
        self.clientes = []
        for id_c, nombre, telefono in lista_clientes:
            self.clientes.append({
                "id": id_c,
                "nombre": nombre,
                "telefono": telefono,
            })
    
    def _filtrar_clientes(self, texto):
        """Filtra la lista de clientes segun el texto escrito."""
        texto_lower = texto.lower().strip()
        
        if not texto_lower:
            self.lista_resultados.setVisible(False)
            self._mostrando_lista = False
            return
        
        # Buscar coincidencias en nombre o telefono
        coincidencias = [
            c for c in self.clientes
            if texto_lower in c["nombre"].lower()
            or texto_lower in c["telefono"]
        ]
        
        if not coincidencias:
            # Mostrar mensaje de "no encontrado"
            self.lista_resultados.clear()
            item = QListWidgetItem("No se encontraron clientes")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            item.setForeground(Qt.GlobalColor.gray)
            self.lista_resultados.addItem(item)
            self.lista_resultados.setVisible(True)
            self._mostrando_lista = True
            return
        
        # Llenar la lista con las coincidencias
        self.lista_resultados.clear()
        for cliente in coincidencias:
            texto_item = f"{cliente['nombre']}  -  {cliente['telefono']}"
            item = QListWidgetItem(texto_item)
            # Guardar el ID del cliente en el item para recuperarlo despues
            item.setData(Qt.ItemDataRole.UserRole, cliente["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, cliente["nombre"])
            item.setData(Qt.ItemDataRole.UserRole + 2, cliente["telefono"])
            self.lista_resultados.addItem(item)
        
        self.lista_resultados.setVisible(True)
        self._mostrando_lista = True
    
    def _on_texto_editado(self, texto):
        """Cuando el usuario edita el texto, limpiar la seleccion previa."""
        if self._id_seleccionado is not None:
            self._id_seleccionado = None
            self._nombre_seleccionado = ""
            self._telefono_seleccionado = ""
            self.lbl_seleccionado.setVisible(False)
            self.widget_seleccion.setVisible(False)
            self.txt_busqueda.setVisible(True)
            self.seleccion_limpiada.emit()
    
    def _seleccionar_cliente(self, item):
        """Maneja el click en un item de la lista de resultados."""
        # Verificar que no sea el mensaje "no encontrado"
        selectable = item.flags() & Qt.ItemFlag.ItemIsSelectable
        if not selectable:
            return
        
        # Obtener datos del item
        self._id_seleccionado = item.data(Qt.ItemDataRole.UserRole)
        self._nombre_seleccionado = item.data(Qt.ItemDataRole.UserRole + 1)
        self._telefono_seleccionado = item.data(Qt.ItemDataRole.UserRole + 2)
        
        # Actualizar la interfaz
        self.txt_busqueda.setVisible(False)
        self.lista_resultados.setVisible(False)
        self._mostrando_lista = False
        
        texto_seleccion = f"{self._nombre_seleccionado}  |  Tel: {self._telefono_seleccionado}"
        self.lbl_seleccionado.setText(texto_seleccion)
        self.lbl_seleccionado.setVisible(True)
        self.widget_seleccion.setVisible(True)
        
        # Emitir senal
        self.cliente_seleccionado.emit(
            self._id_seleccionado,
            self._nombre_seleccionado,
            self._telefono_seleccionado
        )
    
    def limpiar_seleccion(self):
        """Limpia la seleccion actual y muestra el campo de busqueda."""
        self._id_seleccionado = None
        self._nombre_seleccionado = ""
        self._telefono_seleccionado = ""
        
        self.txt_busqueda.clear()
        self.txt_busqueda.setVisible(True)
        self.lista_resultados.setVisible(False)
        self.lbl_seleccionado.setVisible(False)
        self.widget_seleccion.setVisible(False)
        self._mostrando_lista = False
        
        self.txt_busqueda.setFocus()
        self.seleccion_limpiada.emit()
    
    def obtener_id(self):
        """Retorna el ID del cliente seleccionado, o None si no hay seleccion."""
        return self._id_seleccionado
    
    def obtener_nombre(self):
        """Retorna el nombre del cliente seleccionado, o cadena vacia."""
        return self._nombre_seleccionado
    
    def obtener_telefono(self):
        """Retorna el telefono del cliente seleccionado, o cadena vacia."""
        return self._telefono_seleccionado
    
    def tiene_seleccion(self):
        """Retorna True si hay un cliente seleccionado."""
        return self._id_seleccionado is not None
    
    def keyPressEvent(self, event):
        """
        Maneja teclas especiales:
        - Escape: cierra la lista
        - Enter/Return: selecciona el primer item de la lista
        - Flechas arriba/abajo: navega la lista
        """
        if event.key() == Qt.Key.Key_Escape:
            if self._mostrando_lista:
                self.lista_resultados.setVisible(False)
                self._mostrando_lista = False
        
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._mostrando_lista and self.lista_resultados.count() > 0:
                primer_item = self.lista_resultados.item(0)
                if primer_item and (primer_item.flags() & Qt.ItemFlag.ItemIsSelectable):
                    self._seleccionar_cliente(primer_item)
        
        super().keyPressEvent(event)


class BuscadorMesa(QWidget):
    """
    Campo de busqueda de mesa con lista desplegable filtrada (misma UX que
    BuscadorCliente): se escribe y solo se muestran las mesas coincidentes.

    Conserva la interfaz minima del QComboBox (count/itemText/setCurrentIndex/
    currentText) para no romper la logica del formulario de reservas.
    """

    currentIndexChanged = Signal(int)

    def __init__(self, textos, parent=None):
        super().__init__(parent)

        # Igual que BuscadorCliente: comprimirse al ancho disponible.
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)

        self._items = list(textos)
        self._indice = -1
        self._mostrando_lista = False
        self._actualizando = False
        self._construir_interfaz()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Campo de texto principal
        self.txt_busqueda = QLineEdit()
        self.txt_busqueda.setPlaceholderText("Codigo o cantidad de personas")
        self.txt_busqueda.setMinimumHeight(36)
        self.txt_busqueda.setStyleSheet(f"""
            QLineEdit {{
                background-color: {NEUTRO_CLARO};
                border: 1px solid #D0D0D0;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 13px;
                color: #333;
            }}
            QLineEdit:focus {{
                border: 2px solid {SECUNDARIO};
                background-color: {BLANCO};
            }}
        """)
        self.txt_busqueda.textChanged.connect(self._filtrar)
        self.txt_busqueda.setFocus()
        layout.addWidget(self.txt_busqueda)

        # Lista desplegable de resultados
        self.lista_resultados = QListWidget()
        self.lista_resultados.setMaximumHeight(150)
        self.lista_resultados.setStyleSheet(f"""
            QListWidget {{
                background-color: {BLANCO};
                border: 1px solid #D0D0D0;
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                padding: 4px 0;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid #F0F0F0;
            }}
            QListWidget::item:hover {{
                background-color: #E8F0FE;
            }}
            QListWidget::item:selected {{
                background-color: {SECUNDARIO};
                color: white;
            }}
        """)
        self.lista_resultados.setVisible(False)
        self.lista_resultados.itemClicked.connect(self._seleccionar_mesa)
        layout.addWidget(self.lista_resultados)

        # Label que muestra la mesa seleccionada (cuando la lista esta oculta)
        self.lbl_seleccionado = QLabel()
        self.lbl_seleccionado.setWordWrap(True)
        self.lbl_seleccionado.setStyleSheet(f"""
            QLabel {{
                background-color: #E8F5E9;
                border: 1px solid #A5D6A7;
                border-radius: 6px;
                padding: 6px 12px;
                color: #2E7D32;
                font-weight: 600;
                font-size: 12px;
            }}
        """)
        self.lbl_seleccionado.setVisible(False)

        self.btn_limpiar = QLabel("[X] Cambiar")
        self.btn_limpiar.setStyleSheet(f"""
            QLabel {{
                color: {PRIMARIO};
                font-size: 11px;
                font-weight: 600;
                padding: 4px 8px;
                text-decoration: underline;
            }}
            QLabel:hover {{
                color: {DORADO};
            }}
        """)
        self.btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_limpiar.mousePressEvent = lambda e: self.limpiar()

        layout_seleccion = QHBoxLayout()
        layout_seleccion.setContentsMargins(0, 4, 0, 0)
        layout_seleccion.addWidget(self.lbl_seleccionado)
        layout_seleccion.addWidget(self.btn_limpiar)
        layout_seleccion.addStretch()

        self.widget_seleccion = QWidget()
        self.widget_seleccion.setLayout(layout_seleccion)
        self.widget_seleccion.setVisible(False)
        layout.addWidget(self.widget_seleccion)

    # ---------------------------------------------------------------
    # API compatible con QComboBox (para la logica del formulario)
    # ---------------------------------------------------------------
    def count(self):
        return len(self._items)

    def itemText(self, i):
        if 0 <= i < len(self._items):
            return self._items[i]
        return ""

    def currentText(self):
        if 0 <= self._indice < len(self._items):
            return self._items[self._indice]
        return ""

    def setCurrentIndex(self, i):
        if 0 <= i < len(self._items):
            self._indice = i
            self._pintar_seleccion()
            self.currentIndexChanged.emit(i)

    def setCurrentText(self, texto):
        for i, t in enumerate(self._items):
            if t == texto:
                self.setCurrentIndex(i)
                return
        self.limpiar()

    def tiene_seleccion(self):
        return self._indice >= 0

    # ---------------------------------------------------------------
    # Internos
    # ---------------------------------------------------------------
    def _pintar_seleccion(self):
        self._actualizando = True
        self.txt_busqueda.setText(self.currentText())
        self.txt_busqueda.setVisible(True)
        self.lista_resultados.setVisible(False)
        self._mostrando_lista = False
        self.lbl_seleccionado.setText(self.currentText())
        self.lbl_seleccionado.setVisible(True)
        self.widget_seleccion.setVisible(True)
        self._actualizando = False

    def _filtrar(self, texto):
        if self._actualizando:
            return
        texto_lower = texto.lower().strip()

        # Al editar se pierde la seleccion previa
        if self._indice >= 0:
            self._indice = -1
            self.lbl_seleccionado.setVisible(False)
            self.widget_seleccion.setVisible(False)

        if not texto_lower:
            self.lista_resultados.setVisible(False)
            self._mostrando_lista = False
            return

        coincidencias = [
            t for t in self._items
            if texto_lower in t.lower()
        ]

        self.lista_resultados.clear()
        if not coincidencias:
            item = QListWidgetItem("No se encontraron mesas")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            item.setForeground(Qt.GlobalColor.gray)
            self.lista_resultados.addItem(item)
        else:
            for t in coincidencias:
                item = QListWidgetItem(t)
                item.setData(Qt.ItemDataRole.UserRole, t)
                self.lista_resultados.addItem(item)

        self.lista_resultados.setVisible(True)
        self._mostrando_lista = True

    def _seleccionar_mesa(self, item):
        if not (item.flags() & Qt.ItemFlag.ItemIsSelectable):
            return
        texto = item.data(Qt.ItemDataRole.UserRole)
        for i, t in enumerate(self._items):
            if t == texto:
                self.setCurrentIndex(i)
                break

    def limpiar(self):
        self._indice = -1
        self.txt_busqueda.clear()
        self.txt_busqueda.setVisible(True)
        self.lista_resultados.setVisible(False)
        self.lbl_seleccionado.setVisible(False)
        self.widget_seleccion.setVisible(False)
        self._mostrando_lista = False
        self.txt_busqueda.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self._mostrando_lista:
                self.lista_resultados.setVisible(False)
                self._mostrando_lista = False

        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._mostrando_lista and self.lista_resultados.count() > 0:
                primer_item = self.lista_resultados.item(0)
                if primer_item and (primer_item.flags() & Qt.ItemFlag.ItemIsSelectable):
                    self._seleccionar_mesa(primer_item)

        super().keyPressEvent(event)
