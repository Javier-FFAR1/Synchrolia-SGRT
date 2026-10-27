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
from PySide6.QtGui import QFont

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
        lbl_titulo = QLabel("Reportes y Estadisticas")
        lbl_titulo.setObjectName("titulo")
        layout.addWidget(lbl_titulo)

        # Filtros
        layout_filtros = QHBoxLayout()
        layout_filtros.setSpacing(12)

        lbl_filtro = QLabel("Periodo:")
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
        btn_exportar.setObjectName("acento")
        btn_exportar.setMinimumHeight(36)
        btn_exportar.clicked.connect(self._exportar_pdf)
        layout_filtros.addWidget(btn_exportar)

        btn_excel = QPushButton("Exportar Excel")
        btn_excel.setObjectName("exito")
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
            ("Reservas Semana", "reservas_semana", SECUNDARIO),
            ("Tasa Cancelacion", "tasa_cancelacion", ROJO),
            ("Mesa Top", "mesa_top", VERDE),
            ("Horario Pico", "horario_pico", NARANJA),
            ("Ocupacion Promedio", "ocupacion_promedio", DORADO),
            ("Clientes Frecuentes", "clientes_frecuentes", PRIMARIO),
        ]

        for i, (titulo, clave, color) in enumerate(kpis):
            fila = i // 3
            columna = i % 3

            tarjeta = QFrame()
            tarjeta.setObjectName("tarjeta")
            tarjeta.setMinimumHeight(100)

            layout_tarjeta = QVBoxLayout(tarjeta)
            layout_tarjeta.setContentsMargins(12, 10, 12, 10)
            layout_tarjeta.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            barra = QFrame()
            barra.setFixedHeight(3)
            barra.setStyleSheet(f"background-color: {color}; border-radius: 1px;")
            layout_tarjeta.addWidget(barra)

            if clave in KPI_PORCENTAJE:
                # KPI porcentual: numero grande + barra de progreso
                tarjeta.setMinimumHeight(170)
                lbl_valor = QLabel("-")
                lbl_valor.setFont(QFont("Raleway", 26, QFont.Weight.Bold))
                if not lbl_valor.font().exactMatch():
                    lbl_valor.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
                lbl_valor.setStyleSheet(f"color: {color};")
                lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout_tarjeta.addWidget(lbl_valor)
                self.labels_kpi[clave] = lbl_valor

                barra = BarraProgreso(color, altura=12)
                layout_tarjeta.addWidget(barra)
                self.medidores_kpi[clave] = barra
            else:
                lbl_valor = QLabel("-")
                lbl_valor.setFont(QFont("Raleway", 28, QFont.Weight.Bold))
                if not lbl_valor.font().exactMatch():
                    lbl_valor.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
                lbl_valor.setStyleSheet(f"color: {color};")
                layout_tarjeta.addWidget(lbl_valor)
                self.labels_kpi[clave] = lbl_valor

            lbl_kpi = QLabel(titulo)
            lbl_kpi.setStyleSheet("color: #888888; font-size: 11px;")
            lbl_kpi.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_tarjeta.addWidget(lbl_kpi)
            self.labels_titulo[clave] = lbl_kpi

            grid_kpi.addWidget(tarjeta, fila, columna)

        layout.addLayout(grid_kpi)

        # Tabla: Reservas por dia de la semana
        layout_tablas = QHBoxLayout()
        layout_tablas.setSpacing(16)

        # Izquierda: Reservas por dia
        layout_izq = QVBoxLayout()

        lbl_res_dia = QLabel("Reservas por Dia")
        lbl_res_dia.setStyleSheet(f"color: {PRIMARIO}; font-size: 14px; font-weight: 700;")
        layout_izq.addWidget(lbl_res_dia)

        self.tabla_dias = QTableWidget()
        self.tabla_dias.setColumnCount(2)
        self.tabla_dias.setHorizontalHeaderLabels(["Dia", "Reservas"])
        self.tabla_dias.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_dias.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_dias.verticalHeader().setVisible(False)
        self.tabla_dias.setRowCount(7)

        layout_izq.addWidget(self.tabla_dias)

        layout_tablas.addLayout(layout_izq)

        # Derecha: Top mesas
        layout_der = QVBoxLayout()

        lbl_top = QLabel("Top Mesas Mas Solicitadas")
        lbl_top.setStyleSheet(f"color: {PRIMARIO}; font-size: 14px; font-weight: 700;")
        layout_der.addWidget(lbl_top)

        self.tabla_top = QTableWidget()
        self.tabla_top.setColumnCount(3)
        self.tabla_top.setHorizontalHeaderLabels(["Posicion", "Mesa", "Reservas"])
        self.tabla_top.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_top.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_top.verticalHeader().setVisible(False)
        self.tabla_top.setRowCount(0)

        layout_der.addWidget(self.tabla_top)

        layout_tablas.addLayout(layout_der)

        layout.addLayout(layout_tablas)
        layout.addStretch()

    def _actualizar_reporte(self):
        """Recalcula KPIs, reservas por dia y top mesas desde el almacen."""
        periodo = self.cmb_periodo.currentText()
        kpis = reportes_kpis(periodo)

        # El KPI de reservas adapta su titulo al periodo filtrado
        titulos_reservas = {
            "Hoy": "Reservas Hoy",
            "Esta Semana": "Reservas Esta Semana",
            "Este Mes": "Reservas Este Mes",
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
        self.tabla_dias.setRowCount(0)
        self.tabla_dias.setRowCount(len(orden))
        for fila, dia in enumerate(orden):
            item_dia = QTableWidgetItem(dia)
            item_dia.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_dias.setItem(fila, 0, item_dia)

            item_total = QTableWidgetItem(str(dias[dia]))
            item_total.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_total.setFont(QFont("Raleway", 12, QFont.Weight.Bold))
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
                item_pos.setForeground(Qt.GlobalColor.yellow)
                item_pos.setFont(QFont("Raleway", 12, QFont.Weight.Bold))

            self.tabla_top.setItem(fila, 0, item_pos)
            self.tabla_top.setItem(fila, 1, item_mesa)
            self.tabla_top.setItem(fila, 2, item_total)

    def _generar_reporte(self):
        """Recalcula el reporte segun el periodo seleccionado."""
        self._actualizar_reporte()
        QMessageBox.information(
            self,
            "Reporte Generado",
            f"Reporte del periodo '{self.cmb_periodo.currentText()}' actualizado "
            "con la informacion actual."
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
                "La libreria 'reportlab' no esta instalada. "
                "Instalela con: pip install reportlab"
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
                "La libreria 'openpyxl' no esta instalada. "
                "Instalela con: pip install openpyxl"
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
