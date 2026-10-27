# -*- coding: utf-8 -*-
"""
Generador de reportes PDF (Sesiones 34 y 35 - ReportLab + SQLAlchemy).

El cuerpo del reporte se construye con Flowables (SimpleDocTemplate,
Paragraph, Spacer y Table) para que las tablas y los listados se adapten
automaticamente a varias paginas. El Canvas se usa solo para el marco
estatico de la pagina (pie y numeracion), tal como recomienda la Sesion 34.

Los datos se obtienen con SQLAlchemy ORM a traves de ReservaRepository y
MesaRepository; la interfaz PySide6 solo invoca generar_reporte_pdf().
"""

from collections import Counter
from datetime import datetime
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from repository import MesaRepository, ReservaRepository

ANCHO_UTIL = letter[0] - 108
MARGEN = 54

PRIMARIO_HEX = "#1B3A5C"
SECUNDARIO_HEX = "#2C5F8A"
DORADO_HEX = "#D4A843"
VERDE_HEX = "#4CAF50"
ROJO_HEX = "#F44336"
NARANJA_HEX = "#FF9800"
GRIS_TEXTO_HEX = "#6B7280"
GRIS_CLARO_HEX = "#F2F6FA"

PRIMARIO = colors.HexColor(PRIMARIO_HEX)
BORDE = colors.HexColor("#D9E2EC")
GRIS_CLARO = colors.HexColor(GRIS_CLARO_HEX)
GRIS_TEXTO = colors.HexColor(GRIS_TEXTO_HEX)

DIAS_SEMANA = [
    "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
]

COLOR_ESTADO = {
    "Cancelada": ROJO_HEX,
    "Confirmada": VERDE_HEX,
    "Pendiente": NARANJA_HEX,
    "Completada": SECUNDARIO_HEX,
}


def _texto(valor):
    """Escapa texto dinamico para que Paragraph no interprete etiquetas."""
    if valor is None:
        return ""
    return escape(str(valor))


def _crear_estilos():
    """Estilos tipograficos institucionales del reporte."""
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "TituloReporte", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=19, leading=23,
            textColor=PRIMARIO, spaceAfter=2,
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloReporte", parent=base["Normal"],
            fontName="Helvetica", fontSize=9, leading=12,
            textColor=GRIS_TEXTO, spaceAfter=2,
        ),
        "titulo_reporte": ParagraphStyle(
            "TituloSeccionReporte", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=13, leading=16,
            textColor=PRIMARIO, spaceBefore=6, spaceAfter=2,
        ),
        "seccion": ParagraphStyle(
            "SeccionReporte", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=11.5, leading=14,
            textColor=PRIMARIO, spaceBefore=10, spaceAfter=5,
        ),
        "subseccion": ParagraphStyle(
            "SubseccionReporte", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=10, leading=13,
            textColor=PRIMARIO, spaceBefore=2, spaceAfter=4,
        ),
        "cuerpo": ParagraphStyle(
            "CuerpoReporte", parent=base["Normal"],
            fontName="Helvetica", fontSize=8.5, leading=12,
            textColor=colors.HexColor("#1F2937"),
        ),
        "kpi": ParagraphStyle(
            "KpiReporte", parent=base["Normal"],
            fontName="Helvetica", fontSize=8, leading=10,
            alignment=1,
        ),
        "celda": ParagraphStyle(
            "CeldaReporte", parent=base["Normal"],
            fontName="Helvetica", fontSize=7.6, leading=9.5,
            textColor=colors.HexColor("#1F2937"),
        ),
        "celda_centro": ParagraphStyle(
            "CeldaCentroReporte", parent=base["Normal"],
            fontName="Helvetica", fontSize=7.6, leading=9.5,
            alignment=1, textColor=colors.HexColor("#1F2937"),
        ),
        "encabezado": ParagraphStyle(
            "EncabezadoReporte", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=7.6, leading=9.5,
            alignment=1, textColor=colors.white,
        ),
        "pie": ParagraphStyle(
            "PieReporte", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=7.2, leading=9,
            textColor=GRIS_TEXTO,
        ),
    }


def _calcular_kpis(reservas, total_mesas):
    """Calcula los indicadores del periodo a partir de las entidades ORM."""
    total = len(reservas)
    canceladas = sum(
        1 for r in reservas if r.estado.nombre_estado == "Cancelada"
    )
    activas = sum(
        1 for r in reservas
        if r.estado.nombre_estado in ("Pendiente", "Confirmada")
    )
    tasa = (canceladas / total * 100) if total else 0.0
    ocupacion = (activas / total_mesas * 100) if total_mesas else 0.0

    no_canceladas = [
        r for r in reservas if r.estado.nombre_estado != "Cancelada"
    ]
    conteo_mesas = Counter(r.mesa.numero_mesa for r in no_canceladas)
    conteo_horas = Counter(
        r.hora_inicio.strftime("%H:%M") for r in no_canceladas
    )

    return {
        "total": total,
        "tasa_cancelacion": round(tasa, 1),
        "mesa_top": conteo_mesas.most_common(1)[0][0] if conteo_mesas else "-",
        "horario_pico": conteo_horas.most_common(1)[0][0] if conteo_horas else "-",
        "ocupacion_promedio": round(ocupacion),
        "clientes_frecuentes": len({r.id_cliente for r in reservas}),
    }


def _reservas_por_dia(reservas):
    """Cuenta reservas no canceladas por dia de la semana."""
    conteo = {dia: 0 for dia in DIAS_SEMANA}
    for reserva in reservas:
        if reserva.estado.nombre_estado == "Cancelada":
            continue
        conteo[DIAS_SEMANA[reserva.fecha_reserva.weekday()]] += 1
    return conteo


def _top_mesas(reservas, limite=7):
    """Devuelve las mesas con mas reservas no canceladas."""
    no_canceladas = [
        r for r in reservas if r.estado.nombre_estado != "Cancelada"
    ]
    conteo = Counter(r.mesa.numero_mesa for r in no_canceladas)
    return conteo.most_common(limite)


def _estilo_tabla():
    return [
        ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARIO),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
    ]


def _tabla_kpis(kpis, estilos):
    """Tarjetas de indicadores en una grilla de 3 columnas por 2 filas."""
    datos = [
        ("Reservas del periodo", kpis["total"], PRIMARIO_HEX),
        ("Tasa de cancelación", f"{kpis['tasa_cancelacion']}%", ROJO_HEX),
        ("Mesa más solicitada", kpis["mesa_top"], VERDE_HEX),
        ("Horario pico", kpis["horario_pico"], NARANJA_HEX),
        ("Ocupación promedio", f"{kpis['ocupacion_promedio']}%", DORADO_HEX),
        ("Clientes únicos", kpis["clientes_frecuentes"], SECUNDARIO_HEX),
    ]

    celdas = []
    for inicio in range(0, len(datos), 3):
        fila = []
        for titulo, valor, color in datos[inicio:inicio + 3]:
            contenido = (
                f"<font size='16' color='{color}'><b>{_texto(valor)}</b></font>"
                f"<br/><font size='7' color='{GRIS_TEXTO_HEX}'>"
                f"{_texto(titulo)}</font>"
            )
            fila.append(Paragraph(contenido, estilos["kpi"]))
        celdas.append(fila)

    tabla = Table(
        celdas,
        colWidths=[ANCHO_UTIL / 3] * 3,
        rowHeights=[46, 46],
    )
    tabla.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, BORDE),
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tabla


def _tabla_dias(dias, estilos, ancho):
    datos = [[
        Paragraph("Día", estilos["encabezado"]),
        Paragraph("Reservas", estilos["encabezado"]),
    ]]
    for dia, total in dias.items():
        datos.append([
            Paragraph(_texto(dia), estilos["celda"]),
            Paragraph(str(total), estilos["celda_centro"]),
        ])
    tabla = Table(
        datos,
        colWidths=[ancho * 0.55, ancho * 0.45],
        repeatRows=1,
    )
    tabla.setStyle(TableStyle(_estilo_tabla()))
    return tabla


def _tabla_top(top, estilos, ancho):
    datos = [[
        Paragraph("#", estilos["encabezado"]),
        Paragraph("Mesa", estilos["encabezado"]),
        Paragraph("Reservas", estilos["encabezado"]),
    ]]
    if top:
        for posicion, (mesa, total) in enumerate(top, start=1):
            datos.append([
                Paragraph(str(posicion), estilos["celda_centro"]),
                Paragraph(_texto(mesa), estilos["celda_centro"]),
                Paragraph(str(total), estilos["celda_centro"]),
            ])
    else:
        datos.append([
            Paragraph("-", estilos["celda_centro"]),
            Paragraph("Sin datos", estilos["celda_centro"]),
            Paragraph("0", estilos["celda_centro"]),
        ])
    tabla = Table(
        datos,
        colWidths=[ancho * 0.14, ancho * 0.52, ancho * 0.34],
        repeatRows=1,
    )
    tabla.setStyle(TableStyle(_estilo_tabla()))
    return tabla


def _bloque(titulo, tabla, ancho, estilos):
    """Agrupa un titulo y su tabla para colocarlos lado a lado."""
    contenedor = Table(
        [[Paragraph(_texto(titulo), estilos["subseccion"])], [tabla]],
        colWidths=[ancho],
    )
    contenedor.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return contenedor


def _tabla_detalle(reservas, estilos):
    encabezados = [
        "Fecha", "Hora", "Cliente", "Mesa", "Pers.", "Estado", "Atendió"
    ]
    datos = [[
        Paragraph(titulo, estilos["encabezado"]) for titulo in encabezados
    ]]

    if reservas:
        for reserva in reservas:
            estado = reserva.estado.nombre_estado
            color_estado = COLOR_ESTADO.get(estado, "#1F2937")
            datos.append([
                Paragraph(
                    reserva.fecha_reserva.strftime("%d/%m/%Y"),
                    estilos["celda_centro"],
                ),
                Paragraph(
                    f"{reserva.hora_inicio.strftime('%H:%M')} - "
                    f"{reserva.hora_fin.strftime('%H:%M')}",
                    estilos["celda_centro"],
                ),
                Paragraph(
                    _texto(reserva.cliente.nombre_completo), estilos["celda"]
                ),
                Paragraph(
                    _texto(reserva.mesa.numero_mesa), estilos["celda_centro"]
                ),
                Paragraph(str(reserva.numero_personas), estilos["celda_centro"]),
                Paragraph(
                    f"<font color='{color_estado}'>{_texto(estado)}</font>",
                    estilos["celda_centro"],
                ),
                Paragraph(
                    _texto(reserva.usuario.nombre_completo), estilos["celda"]
                ),
            ])
    else:
        datos.append([
            Paragraph(
                "No hay reservas registradas para el periodo seleccionado.",
                estilos["celda_centro"],
            )
        ] + [""] * (len(encabezados) - 1))

    proporciones = [0.123, 0.155, 0.262, 0.083, 0.067, 0.131, 0.179]
    tabla = Table(
        datos,
        colWidths=[ANCHO_UTIL * proporcion for proporcion in proporciones],
        repeatRows=1,
    )
    reglas = [
        ("GRID", (0, 0), (-1, -1), 0.5, BORDE),
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARIO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    if not reservas:
        reglas.extend([
            ("SPAN", (0, 1), (-1, 1)),
            ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ])
    tabla.setStyle(TableStyle(reglas))
    return tabla


def _construir_story(reservas, periodo, kpis, estilos):
    story = []

    story.append(Paragraph("Synchrolia SGRT", estilos["titulo"]))
    story.append(Paragraph(
        "Sistema de Gestión de Reservas para Restaurante",
        estilos["subtitulo"],
    ))
    story.append(Paragraph("Reporte de Reservas", estilos["titulo_reporte"]))
    story.append(HRFlowable(
        width="100%", thickness=1.2, color=PRIMARIO,
        spaceBefore=4, spaceAfter=8,
    ))
    story.append(Paragraph(
        f"Periodo: <b>{_texto(periodo)}</b> | "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilos["cuerpo"],
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Indicadores del periodo", estilos["seccion"]))
    story.append(_tabla_kpis(kpis, estilos))
    story.append(Spacer(1, 12))

    ancho_dias = ANCHO_UTIL * 0.46
    ancho_top = ANCHO_UTIL * 0.54
    bloque_dias = _bloque(
        "Reservas por día",
        _tabla_dias(_reservas_por_dia(reservas), estilos, ancho_dias),
        ancho_dias,
        estilos,
    )
    bloque_top = _bloque(
        "Top mesas más solicitadas",
        _tabla_top(_top_mesas(reservas), estilos, ancho_top),
        ancho_top,
        estilos,
    )
    resumen = Table(
        [[bloque_dias, bloque_top]],
        colWidths=[ancho_dias, ancho_top],
    )
    resumen.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(resumen)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Detalle de reservas", estilos["seccion"]))
    story.append(Paragraph(
        f"Total de registros: <b>{len(reservas)}</b>",
        estilos["cuerpo"],
    ))
    story.append(Spacer(1, 6))
    story.append(_tabla_detalle(reservas, estilos))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Generado automáticamente por Synchrolia SGRT - "
        "Datos obtenidos con SQLAlchemy ORM.",
        estilos["pie"],
    ))
    return story


def _plantilla_pagina(canvas, doc):
    """Marco estático: cabecera en páginas siguientes y pie con numeración."""
    canvas.saveState()

    if doc.page > 1:
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(PRIMARIO)
        canvas.drawString(MARGEN, letter[1] - 36,
                          "Synchrolia SGRT - Reporte de Reservas")
        canvas.setStrokeColor(BORDE)
        canvas.setLineWidth(0.6)
        canvas.line(MARGEN, letter[1] - 42, letter[0] - MARGEN, letter[1] - 42)

    canvas.setStrokeColor(BORDE)
    canvas.setLineWidth(0.6)
    canvas.line(MARGEN, 42, letter[0] - MARGEN, 42)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRIS_TEXTO)
    canvas.drawString(MARGEN, 30, "Synchrolia SGRT - Gestión de reservas")
    canvas.drawRightString(
        letter[0] - MARGEN, 30, f"Página {doc.page}"
    )
    canvas.restoreState()


def generar_reporte_pdf(ruta, periodo="Todos", reservas=None):
    """Genera el PDF del periodo y devuelve la ruta del archivo creado.

    reservas es opcional y se usa en pruebas para inyectar datos sin BD.
    """
    if reservas is None:
        reservas = ReservaRepository.obtener_detalladas(periodo)

    total_mesas = MesaRepository.contar_todas()
    estilos = _crear_estilos()
    kpis = _calcular_kpis(reservas, total_mesas)
    story = _construir_story(reservas, periodo, kpis, estilos)

    doc = SimpleDocTemplate(
        ruta,
        pagesize=letter,
        rightMargin=MARGEN,
        leftMargin=MARGEN,
        topMargin=MARGEN,
        bottomMargin=MARGEN,
        title="Reporte de Reservas - Synchrolia SGRT",
        author="Synchrolia SGRT",
        subject=f"Reporte de reservas - {periodo}",
    )
    doc.build(
        story,
        onFirstPage=_plantilla_pagina,
        onLaterPages=_plantilla_pagina,
    )
    return ruta


if __name__ == "__main__":
    generar_reporte_pdf("reporte_flowables_prueba.pdf")
    print("Reporte Flowables generado exitosamente.")
