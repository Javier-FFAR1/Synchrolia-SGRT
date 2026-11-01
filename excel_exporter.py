# -*- coding: utf-8 -*-
"""
Exportador de reservas a Excel (Sesion 36 - openpyxl + SQLAlchemy).

Genera un libro .xlsx con dos hojas:
- Resumen: indicadores, reservas por dia, top de mesas y conteo por estado.
- Reservas: detalle editable, con formato por estado y filtros automaticos.

Sigue el flujo de la Sesion 36: los datos se extraen con el repositorio ORM,
se escriben con openpyxl y se aplican estilos corporativos (Font, PatternFill,
Alignment, Border y Side). La interfaz PySide6 solo invoca
exportar_reservas_excel().
"""

from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from report_metrics import (
    calcular_kpis,
    reservas_por_dia,
    resumen_estados,
    top_mesas,
)
from repository import MesaRepository, ReservaRepository

PRIMARIO = "1B3A5C"
SECUNDARIO = "2C5F8A"
DORADO = "D4A843"
FONDO_CLARO = "F2F6FA"
BORDE = "D9E2EC"
TEXTO = "1F2937"
GRIS = "6B7280"
BLANCO = "FFFFFF"

FUENTE = "Calibri"
BORDE_FINO = Side(style="thin", color=BORDE)
MARCO = Border(
    left=BORDE_FINO,
    right=BORDE_FINO,
    top=BORDE_FINO,
    bottom=BORDE_FINO,
)
CENTRO = Alignment(horizontal="center", vertical="center", wrap_text=True)
IZQUIERDA = Alignment(horizontal="left", vertical="center", wrap_text=True)

COLOR_ESTADO = {
    "Confirmada": ("E8F5E9", "2E7D32"),
    "Pendiente": ("FFF3E0", "E65100"),
    "Cancelada": ("FFEBEE", "C62828"),
    "Completada": ("E3F2FD", "1565C0"),
}

ENCABEZADOS_DETALLE = [
    "ID",
    "Fecha",
    "Hora inicio",
    "Hora fin",
    "Cliente",
    "Teléfono",
    "Correo",
    "Mesa",
    "Ubicación",
    "Capacidad",
    "Personas",
    "Estado",
    "Atendió",
    "Observaciones",
]


def _relleno(color):
    return PatternFill(start_color=color, end_color=color, fill_type="solid")


def _fuente(tamano=10, negrita=False, color=TEXTO, cursiva=False):
    return Font(
        name=FUENTE,
        size=tamano,
        bold=negrita,
        italic=cursiva,
        color=color,
    )


def _texto_seguro(valor):
    """Evita que un texto se interprete como formula en Excel."""
    texto = "" if valor is None else str(valor)
    if texto.startswith(("=", "+", "-", "@")):
        return "'" + texto
    return texto


def _celda(
    ws,
    fila,
    columna,
    valor,
    negrita=False,
    color=TEXTO,
    fondo=None,
    alineacion=CENTRO,
    formato=None,
    tamano=10,
    cursiva=False,
):
    celda = ws.cell(row=fila, column=columna, value=valor)
    celda.font = _fuente(
        tamano=tamano,
        negrita=negrita,
        color=color,
        cursiva=cursiva,
    )
    celda.alignment = alineacion
    celda.border = MARCO
    if fondo:
        celda.fill = _relleno(fondo)
    if formato:
        celda.number_format = formato
    return celda


def _subtitulo(periodo):
    generado = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"Período: {periodo} | Generado: {generado}"


def _preparar_titulo(ws, titulo, subtitulo, ultima_columna):
    for columna in range(1, ultima_columna + 1):
        celda_titulo = ws.cell(row=1, column=columna)
        celda_titulo.fill = _relleno(PRIMARIO)
        celda_titulo.border = Border(
            bottom=Side(style="medium", color=DORADO)
        )
        celda_subtitulo = ws.cell(row=2, column=columna)
        celda_subtitulo.fill = _relleno(FONDO_CLARO)

    ws.merge_cells(
        start_row=1, start_column=1, end_row=1, end_column=ultima_columna
    )
    ws.merge_cells(
        start_row=2, start_column=1, end_row=2, end_column=ultima_columna
    )

    celda_titulo = ws.cell(row=1, column=1, value=titulo)
    celda_titulo.font = _fuente(tamano=15, negrita=True, color=BLANCO)
    celda_titulo.alignment = Alignment(
        horizontal="left", vertical="center"
    )

    celda_subtitulo = ws.cell(row=2, column=1, value=subtitulo)
    celda_subtitulo.font = _fuente(tamano=10, color=GRIS, cursiva=True)
    celda_subtitulo.alignment = Alignment(
        horizontal="left", vertical="center"
    )

    ws.row_dimensions[1].height = 28
    ws.row_dimensions[2].height = 20


def _titulo_seccion(ws, fila, columna_inicio, columna_fin, titulo):
    for columna in range(columna_inicio, columna_fin + 1):
        celda = ws.cell(row=fila, column=columna)
        celda.fill = _relleno(FONDO_CLARO)
        celda.border = Border(
            bottom=Side(style="medium", color=DORADO)
        )

    if columna_fin > columna_inicio:
        ws.merge_cells(
            start_row=fila,
            start_column=columna_inicio,
            end_row=fila,
            end_column=columna_fin,
        )

    celda = ws.cell(row=fila, column=columna_inicio, value=titulo)
    celda.font = _fuente(tamano=11, negrita=True, color=PRIMARIO)
    celda.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[fila].height = 20


def _encabezados(ws, fila, columna_inicio, titulos):
    for offset, titulo in enumerate(titulos):
        _celda(
            ws,
            fila,
            columna_inicio + offset,
            titulo,
            negrita=True,
            color=BLANCO,
            fondo=PRIMARIO,
        )
    ws.row_dimensions[fila].height = 22


def _nota_pie(ws, fila, ultima_columna):
    ws.merge_cells(
        start_row=fila, start_column=1, end_row=fila, end_column=ultima_columna
    )
    celda = ws.cell(
        row=fila,
        column=1,
        value=(
            "Generado automáticamente por Synchrolia SGRT - "
            "Datos obtenidos con SQLAlchemy ORM."
        ),
    )
    celda.font = _fuente(tamano=9, color=GRIS, cursiva=True)
    celda.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[fila].height = 18


def _configurar_impresion(ws, titulo_filas=None):
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    if titulo_filas:
        ws.print_title_rows = titulo_filas


def _autoajustar_anchos(ws, fila_inicio, fila_fin, ancho_max=45):
    """Ajusta cada columna al contenido, con un maximo para no desbordar."""
    for columna in range(1, ws.max_column + 1):
        maximo = 0
        for fila in range(fila_inicio, fila_fin + 1):
            valor = ws.cell(row=fila, column=columna).value
            if valor is not None:
                maximo = max(maximo, len(str(valor)))
        letra = get_column_letter(columna)
        ws.column_dimensions[letra].width = min(max(maximo + 4, 12), ancho_max)


def _altura_detalle(reserva):
    largo = max(
        len(reserva.cliente.nombre_completo),
        len(reserva.observaciones or ""),
    )
    if largo > 70:
        return 42
    if largo > 35:
        return 30
    return 20


def _fila_detalle(ws, fila, reserva, alterna):
    estado = reserva.estado.nombre_estado
    fondo_estado, color_estado = COLOR_ESTADO.get(estado, (None, TEXTO))
    fondo = FONDO_CLARO if alterna else None

    valores = [
        reserva.id_reserva,
        reserva.fecha_reserva,
        reserva.hora_inicio,
        reserva.hora_fin,
        _texto_seguro(reserva.cliente.nombre_completo),
        _texto_seguro(reserva.cliente.telefono),
        _texto_seguro(reserva.cliente.correo),
        _texto_seguro(reserva.mesa.numero_mesa),
        _texto_seguro(reserva.mesa.ubicacion.nombre_ubicacion),
        reserva.mesa.capacidad,
        reserva.numero_personas,
        estado,
        _texto_seguro(reserva.usuario.nombre_completo),
        _texto_seguro(reserva.observaciones),
    ]

    for columna, valor in enumerate(valores, start=1):
        alineacion = IZQUIERDA if columna in (5, 6, 7, 9, 13, 14) else CENTRO
        _celda(
            ws,
            fila,
            columna,
            valor,
            fondo=fondo,
            alineacion=alineacion,
        )

    ws.cell(row=fila, column=2).number_format = "DD/MM/YYYY"
    ws.cell(row=fila, column=3).number_format = "HH:MM"
    ws.cell(row=fila, column=4).number_format = "HH:MM"

    if fondo_estado:
        celda_estado = ws.cell(row=fila, column=12)
        celda_estado.fill = _relleno(fondo_estado)
        celda_estado.font = _fuente(negrita=True, color=color_estado)

    ws.row_dimensions[fila].height = _altura_detalle(reserva)


def _hoja_detalle(wb, reservas, periodo):
    ws = wb.create_sheet("Reservas")
    ws.sheet_view.showGridLines = False

    total_columnas = len(ENCABEZADOS_DETALLE)
    _preparar_titulo(
        ws,
        "Synchrolia SGRT - Detalle de Reservas",
        _subtitulo(periodo),
        total_columnas,
    )

    fila_encabezado = 4
    _encabezados(ws, fila_encabezado, 1, ENCABEZADOS_DETALLE)

    fila = fila_encabezado + 1
    if reservas:
        for indice, reserva in enumerate(reservas):
            _fila_detalle(ws, fila, reserva, indice % 2 == 1)
            fila += 1
    else:
        ws.merge_cells(
            start_row=fila,
            start_column=1,
            end_row=fila,
            end_column=total_columnas,
        )
        celda = ws.cell(
            row=fila,
            column=1,
            value=(
                "No hay reservas registradas para el período seleccionado."
            ),
        )
        celda.font = _fuente(tamano=10, color=GRIS, cursiva=True)
        celda.alignment = CENTRO
        for columna in range(1, total_columnas + 1):
            ws.cell(row=fila, column=columna).border = MARCO
        ws.row_dimensions[fila].height = 22
        fila += 1

    ultima_fila_datos = fila - 1
    ws.freeze_panes = f"A{fila_encabezado + 1}"

    if reservas:
        ws.auto_filter.ref = (
            f"A{fila_encabezado}:"
            f"{get_column_letter(total_columnas)}{ultima_fila_datos}"
        )

    _autoajustar_anchos(
        ws,
        fila_encabezado,
        ultima_fila_datos if reservas else fila_encabezado,
    )

    fila_nota = fila + 1
    _nota_pie(ws, fila_nota, total_columnas)
    _configurar_impresion(
        ws,
        titulo_filas=f"{fila_encabezado}:{fila_encabezado}",
    )
    ws.print_area = (
        f"A1:{get_column_letter(total_columnas)}{fila_nota}"
    )
    return ws


def _hoja_resumen(wb, reservas, periodo, total_mesas):
    ws = wb.active
    ws.title = "Resumen"
    ws.sheet_view.showGridLines = False

    total_columnas = 9
    _preparar_titulo(
        ws,
        "Synchrolia SGRT - Resumen del Período",
        _subtitulo(periodo),
        total_columnas,
    )

    kpis = calcular_kpis(reservas, total_mesas)
    dias = reservas_por_dia(reservas)
    top = top_mesas(reservas)
    estados = resumen_estados(reservas)

    _titulo_seccion(ws, 4, 1, 2, "Indicadores del período")
    _titulo_seccion(ws, 4, 4, 5, "Reservas por día")
    _titulo_seccion(ws, 4, 7, 9, "Top mesas más solicitadas")

    _encabezados(ws, 5, 1, ["Indicador", "Valor"])
    _encabezados(ws, 5, 4, ["Día", "Reservas"])
    _encabezados(ws, 5, 7, ["#", "Mesa", "Reservas"])

    filas_kpi = [
        ("Reservas del período", kpis["total"], PRIMARIO),
        ("Tasa de cancelación", f"{kpis['tasa_cancelacion']}%", "C62828"),
        ("Mesa más solicitada", kpis["mesa_top"], "2E7D32"),
        ("Horario pico", kpis["horario_pico"], "E65100"),
        ("Ocupación promedio", f"{kpis['ocupacion_promedio']}%", "B8892E"),
        ("Clientes únicos", kpis["clientes_frecuentes"], SECUNDARIO),
    ]
    for fila, (etiqueta, valor, color) in enumerate(filas_kpi, start=6):
        _celda(
            ws,
            fila,
            1,
            etiqueta,
            alineacion=IZQUIERDA,
            fondo=FONDO_CLARO,
        )
        _celda(ws, fila, 2, valor, negrita=True, color=color, fondo=BLANCO)
        ws.row_dimensions[fila].height = 18

    for fila, (dia, total) in enumerate(dias.items(), start=6):
        fondo = FONDO_CLARO if fila % 2 == 0 else None
        _celda(ws, fila, 4, dia, alineacion=IZQUIERDA, fondo=fondo)
        _celda(ws, fila, 5, total, fondo=fondo)
        ws.row_dimensions[fila].height = 18

    if top:
        for fila, (mesa, total) in enumerate(top, start=6):
            fondo = FONDO_CLARO if fila % 2 == 0 else None
            _celda(ws, fila, 7, fila - 5, fondo=fondo)
            _celda(ws, fila, 8, mesa, alineacion=IZQUIERDA, fondo=fondo)
            _celda(ws, fila, 9, total, fondo=fondo)
    else:
        ws.merge_cells(
            start_row=6, start_column=7, end_row=6, end_column=9
        )
        _celda(
            ws,
            6,
            7,
            "Sin datos",
            color=GRIS,
            cursiva=True,
        )

    _titulo_seccion(ws, 13, 1, 2, "Reservas por estado")
    _encabezados(ws, 14, 1, ["Estado", "Cantidad"])

    for fila, (estado, total) in enumerate(estados.items(), start=15):
        fondo_estado, color_estado = COLOR_ESTADO.get(
            estado, (FONDO_CLARO, TEXTO)
        )
        _celda(
            ws,
            fila,
            1,
            estado,
            negrita=True,
            color=color_estado,
            fondo=fondo_estado,
            alineacion=IZQUIERDA,
        )
        _celda(ws, fila, 2, total)
        ws.row_dimensions[fila].height = 18

    fila_nota = 15 + len(estados) + 1
    _nota_pie(ws, fila_nota, total_columnas)

    anchos = {
        "A": 26,
        "B": 16,
        "C": 3,
        "D": 16,
        "E": 12,
        "F": 3,
        "G": 7,
        "H": 16,
        "I": 12,
    }
    for letra, ancho in anchos.items():
        ws.column_dimensions[letra].width = ancho

    _configurar_impresion(ws)
    ws.print_area = f"A1:I{fila_nota}"
    ws.freeze_panes = "A4"
    return ws


def exportar_reservas_excel(
    ruta="reporte_reservas.xlsx",
    periodo="Todos",
    reservas=None,
):
    """Genera el libro Excel del periodo y devuelve la ruta creada.

    reservas es opcional y se usa en pruebas para inyectar datos sin BD.
    """
    if reservas is None:
        reservas = ReservaRepository.obtener_detalladas(periodo)

    total_mesas = MesaRepository.contar_todas()

    wb = Workbook()
    wb.properties.creator = "Synchrolia SGRT"
    wb.properties.title = "Reporte de Reservas"
    wb.properties.subject = f"Período: {periodo}"

    _hoja_resumen(wb, reservas, periodo, total_mesas)
    _hoja_detalle(wb, reservas, periodo)
    wb.active = 0
    wb.save(ruta)

    print(f"Archivo Excel generado exitosamente: {ruta}")
    return ruta


if __name__ == "__main__":
    exportar_reservas_excel("reporte_reservas_prueba.xlsx")
