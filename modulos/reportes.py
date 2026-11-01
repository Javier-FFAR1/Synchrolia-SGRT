# -*- coding: utf-8 -*-
"""
Modulo: Reportes
Estadisticas e indicadores clave del restaurante.
Todos los valores se calculan a partir del almacen central de datos (reservas),
por lo que reflejan la informacion real ingresada y se regeneran al pulsar
"Generar Reporte". Incluye exportacion a PDF y Excel.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QPushButton, QAbstractItemView,
    QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from modulos.almacen_datos import (
    reportes_kpis, reportes_dias, reportes_top_mesas
)
from modulos.medidor import BarraProgreso

# Claves cuyos KPI se muestran como porcentaje (numero + barra de progreso)
KPI_PORCENTAJE = ("tasa_cancelacion", "ocupacion_promedio")

PRIMARIO = "#1B3A5C"
SECUNDARIO = "#2C5F8A"
DORADO = "#D4A843"
VERDE = "#4CAF50"
ROJO = "#F44336"
NARANJA = "#FF9800"


class PanelReportes(QWidget):
    """Panel de reportes y estadisticas (datos reales del almacen)."""
    def __init__(self):
        super().__init__()
        self._construir_interfaz()
        self._actualizar_reporte()

    def _construir_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Encabezado
        lbl_titulo = QLabel("Reportes y Estadísticas")
        lbl_titulo.setObjectName("titulo")
        layout.addWidget(lbl_titulo)

        lbl_sub = QLabel("Indicadores de reservas y ocupación del restaurante")
        lbl_sub.setObjectName("subtitulo")
        layout.addWidget(lbl_sub)

        # Filtros
        layout_filtros = QHBoxLayout()
        layout_filtros.setSpacing(12)

        lbl_filtro = QLabel("Período:")
        lbl_filtro.setStyleSheet("font-weight: 600;")
        layout_filtros.addWidget(lbl_filtro)

        self.cmb_periodo = QComboBox()
        self.cmb_periodo.addItems(["Hoy", "Esta Semana", "Este Mes", "Todos"])
        self.cmb_periodo.setCurrentText("Todos")
        self.cmb_periodo.setMinimumWidth(160)
        self.cmb_periodo.currentTextChanged.connect(self._actualizar_reporte)
        layout_filtros.addWidget(self.cmb_periodo)

        btn_generar = QPushButton("Generar Reporte")
        btn_generar.setMinimumHeight(36)
        btn_generar.clicked.connect(self._generar_reporte)
        layout_filtros.addWidget(btn_generar)

        btn_exportar = QPushButton("Exportar PDF")
        btn_exportar.setObjectName("secundario")
        btn_exportar.setMinimumHeight(36)
        btn_exportar.clicked.connect(self._exportar_pdf)
        layout_filtros.addWidget(btn_exportar)

        btn_excel = QPushButton("Exportar Excel")
        btn_excel.setObjectName("secundario")
        btn_excel.setMinimumHeight(36)
        btn_excel.clicked.connect(self._exportar_excel)
        layout_filtros.addWidget(btn_excel)

        layout_filtros.addStretch()
        layout.addLayout(layout_filtros)

        # Tarjetas de KPIs
        grid_kpi = QGridLayout()
        grid_kpi.setSpacing(12)

        self.labels_kpi = {}
        self.medidores_kpi = {}
        self.labels_titulo = {}
        kpis = [
            ("Reservas de la Semana", "reservas_semana", SECUNDARIO),
            ("Tasa de Cancelación", "tasa_cancelacion", ROJO),
            ("Mesa Más Solicitada", "mesa_top", VERDE),
            ("Horario Pico", "horario_pico", NARANJA),
            ("Ocupación Promedio", "ocupacion_promedio", DORADO),
            ("Clientes Únicos", "clientes_frecuentes", PRIMARIO),
        ]

        for i, (titulo, clave, color) in enumerate(kpis):
            fila = i // 3
            columna = i % 3

            tarjeta = QFrame()
            tarjeta.setObjectName("tarjeta")
            tarjeta.setFixedHeight(136)

            layout_tarjeta = QVBoxLayout(tarjeta)
            layout_tarjeta.setContentsMargins(14, 10, 14, 10)
            layout_tarjeta.setSpacing(6)
            layout_tarjeta.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            barra = QFrame()
            barra.setFixedHeight(3)
            barra.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            layout_tarjeta.addWidget(barra)

            lbl_valor = QLabel("-")
            lbl_valor.setStyleSheet(
                f"color: {color}; font-family: 'Segoe UI', sans-serif; "
                "font-size: 32px; font-weight: 700; background: transparent;"
            )
            lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_tarjeta.addWidget(lbl_valor)
            self.labels_kpi[clave] = lbl_valor

            if clave in KPI_PORCENTAJE:
                barra_progreso = BarraProgreso(color, altura=10)
                layout_tarjeta.addWidget(barra_progreso)
                self.medidores_kpi[clave] = barra_progreso

            lbl_kpi = QLabel(titulo)
            lbl_kpi.setStyleSheet(
                "color: #6B7280; font-size: 11px; font-weight: 600; "
                "font-family: 'Segoe UI', sans-serif;"
            )
            lbl_kpi.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_tarjeta.addWidget(lbl_kpi)
            self.labels_titulo[clave] = lbl_kpi

            grid_kpi.addWidget(tarjeta, fila, columna)
            grid_kpi.setColumnStretch(columna, 1)

        layout.addLayout(grid_kpi)

        # Tabla: Reservas por dia de la semana
        layout_tablas = QHBoxLayout()
        layout_tablas.setSpacing(16)

        # Izquierda: Reservas por dia
        layout_izq = QVBoxLayout()

        lbl_res_dia = QLabel("Reservas por Día")
        lbl_res_dia.setStyleSheet(
            f"color: {PRIMARIO}; font-size: 15px; font-weight: 700; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout_izq.addWidget(lbl_res_dia)

        self.tabla_dias = QTableWidget()
        self.tabla_dias.setColumnCount(2)
        self.tabla_dias.setHorizontalHeaderLabels(["Día", "Reservas"])
        self.tabla_dias.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for columna in range(self.tabla_dias.columnCount()):
            item = self.tabla_dias.horizontalHeaderItem(columna)
            if item is not None:
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
        self.tabla_dias.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_dias.verticalHeader().setVisible(False)
        self.tabla_dias.verticalHeader().setDefaultSectionSize(36)
        self.tabla_dias.setAlternatingRowColors(True)
        self.tabla_dias.setRowCount(7)

        layout_izq.addWidget(self.tabla_dias, 1)
        layout_tablas.addLayout(layout_izq, 1)

        # Derecha: Top mesas
        layout_der = QVBoxLayout()

        lbl_top = QLabel("Top Mesas Más Solicitadas")
        lbl_top.setStyleSheet(
            f"color: {PRIMARIO}; font-size: 15px; font-weight: 700; "
            "font-family: 'Raleway', 'Segoe UI', sans-serif;"
        )
        layout_der.addWidget(lbl_top)

        self.tabla_top = QTableWidget()
        self.tabla_top.setColumnCount(3)
        self.tabla_top.setHorizontalHeaderLabels(["Posición", "Mesa", "Reservas"])
        header_top = self.tabla_top.horizontalHeader()
        header_top.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_top.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_top.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        for columna in range(self.tabla_top.columnCount()):
            item = self.tabla_top.horizontalHeaderItem(columna)
            if item is not None:
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
        self.tabla_top.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_top.verticalHeader().setVisible(False)
        self.tabla_top.verticalHeader().setDefaultSectionSize(36)
        self.tabla_top.setAlternatingRowColors(True)
        self.tabla_top.setRowCount(0)

        layout_der.addWidget(self.tabla_top, 1)
        layout_tablas.addLayout(layout_der, 1)

        layout.addLayout(layout_tablas, 1)

    def _actualizar_reporte(self):
        """Recalcula KPIs, reservas por dia y top mesas desde el almacen."""
        periodo = self.cmb_periodo.currentText()
        kpis = reportes_kpis(periodo)

        # El KPI de reservas adapta su titulo al periodo filtrado
        titulos_reservas = {
            "Hoy": "Reservas de Hoy",
            "Esta Semana": "Reservas de la Semana",
            "Este Mes": "Reservas del Mes",
            "Todos": "Reservas Totales",
        }
        self.labels_titulo["reservas_semana"].setText(
            titulos_reservas.get(periodo, "Reservas")
        )

        # Formatear valores con su unidad
        self.labels_kpi["reservas_semana"].setText(str(kpis["reservas_semana"]))
        self.labels_kpi["tasa_cancelacion"].setText(f"{kpis['tasa_cancelacion']}%")
        self.medidores_kpi["tasa_cancelacion"].set_valor(kpis["tasa_cancelacion"])
        self.labels_kpi["mesa_top"].setText(str(kpis["mesa_top"]))
        self.labels_kpi["horario_pico"].setText(str(kpis["horario_pico"]))
        self.labels_kpi["ocupacion_promedio"].setText(f"{kpis['ocupacion_promedio']}%")
        self.medidores_kpi["ocupacion_promedio"].set_valor(kpis["ocupacion_promedio"])
        self.labels_kpi["clientes_frecuentes"].setText(str(kpis["clientes_frecuentes"]))

        # Reservas por dia
        dias = reportes_dias(periodo)
        orden = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
        etiquetas_dias = {"Miercoles": "Miércoles", "Sabado": "Sábado"}
        fuente_numero = QFont("Segoe UI")
        fuente_numero.setPixelSize(13)
        fuente_numero.setWeight(QFont.Weight.Bold)

        self.tabla_dias.setRowCount(0)
        self.tabla_dias.setRowCount(len(orden))
        for fila, dia in enumerate(orden):
            item_dia = QTableWidgetItem(etiquetas_dias.get(dia, dia))
            item_dia.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_dias.setItem(fila, 0, item_dia)

            item_total = QTableWidgetItem(str(dias[dia]))
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_total.setFont(fuente_numero)
            self.tabla_dias.setItem(fila, 1, item_total)

        # Top mesas
        top = reportes_top_mesas(7, periodo)
        self.tabla_top.setRowCount(0)
        self.tabla_top.setRowCount(len(top))
        for fila, (mesa, total) in enumerate(top):
            item_pos = QTableWidgetItem(str(fila + 1))
            item_pos.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_mesa = QTableWidgetItem(mesa)
            item_mesa.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_total = QTableWidgetItem(str(total))
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            if fila == 0:
                for item in (item_pos, item_mesa, item_total):
                    item.setForeground(QColor("#8A6D1F"))
                    item.setFont(fuente_numero)

            self.tabla_top.setItem(fila, 0, item_pos)
            self.tabla_top.setItem(fila, 1, item_mesa)
            self.tabla_top.setItem(fila, 2, item_total)

    def _generar_reporte(self):
        """Recalcula el reporte segun el periodo seleccionado."""
        self._actualizar_reporte()
        QMessageBox.information(
            self,
            "Reporte Generado",
            f"Reporte del período '{self.cmb_periodo.currentText()}' actualizado "
            "con la información actual."
        )

    def _exportar_pdf(self):
        """Genera un PDF detallado con Flowables a partir de los datos ORM."""
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar Reporte PDF", "reporte_synchrolia.pdf", "PDF (*.pdf)"
        )
        if not ruta:
            return

        try:
            from report_generator import generar_reporte_pdf
            generar_reporte_pdf(ruta, self.cmb_periodo.currentText())
        except ImportError:
            QMessageBox.information(
                self, "Exportar PDF",
                "La librería 'reportlab' no está instalada. "
                "Instálela con: pip install reportlab"
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self, "Error al exportar PDF",
                f"No se pudo generar el reporte:\n{error}"
            )
            return

        QMessageBox.information(
            self, "PDF Exportado",
            f"Reporte guardado en:\n{ruta}"
        )

    def _exportar_excel(self):
        """Genera un libro Excel con resumen y detalle desde los datos ORM."""
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar Reporte Excel", "reporte_synchrolia.xlsx",
            "Excel (*.xlsx)"
        )
        if not ruta:
            return

        try:
            from excel_exporter import exportar_reservas_excel
            exportar_reservas_excel(ruta, self.cmb_periodo.currentText())
        except ImportError:
            QMessageBox.information(
                self, "Exportar Excel",
                "La librería 'openpyxl' no está instalada. "
                "Instálela con: pip install openpyxl"
            )
            return
        except Exception as error:
            QMessageBox.critical(
                self, "Error al exportar Excel",
                f"No se pudo generar el reporte:\n{error}"
            )
            return

        QMessageBox.information(
            self, "Excel Exportado",
            f"Reporte guardado en:\n{ruta}"
        )
