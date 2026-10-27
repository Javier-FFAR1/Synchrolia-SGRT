# -*- coding: utf-8 -*-
"""
Metricas compartidas por los reportes PDF y Excel (Sesiones 35 y 36).

Centraliza el calculo de indicadores para que el PDF y el libro de Excel
muestren exactamente los mismos valores. No depende de ReportLab ni de
openpyxl: recibe entidades ORM ya cargadas por el repositorio.
"""

from collections import Counter

DIAS_SEMANA = [
    "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
]

ESTADO_CANCELADA = "Cancelada"
ESTADOS_ACTIVOS = ("Pendiente", "Confirmada")
ORDEN_ESTADOS = ("Confirmada", "Pendiente", "Cancelada", "Completada")


def calcular_kpis(reservas, total_mesas):
    """Calcula los indicadores del periodo a partir de las entidades ORM."""
    total = len(reservas)
    canceladas = sum(
        1 for reserva in reservas
        if reserva.estado.nombre_estado == ESTADO_CANCELADA
    )
    activas = sum(
        1 for reserva in reservas
        if reserva.estado.nombre_estado in ESTADOS_ACTIVOS
    )
    tasa = (canceladas / total * 100) if total else 0.0
    ocupacion = (activas / total_mesas * 100) if total_mesas else 0.0

    no_canceladas = [
        reserva for reserva in reservas
        if reserva.estado.nombre_estado != ESTADO_CANCELADA
    ]
    conteo_mesas = Counter(
        reserva.mesa.numero_mesa for reserva in no_canceladas
    )
    conteo_horas = Counter(
        reserva.hora_inicio.strftime("%H:%M") for reserva in no_canceladas
    )

    return {
        "total": total,
        "tasa_cancelacion": round(tasa, 1),
        "mesa_top": conteo_mesas.most_common(1)[0][0] if conteo_mesas else "-",
        "horario_pico": conteo_horas.most_common(1)[0][0] if conteo_horas else "-",
        "ocupacion_promedio": round(ocupacion),
        "clientes_frecuentes": len({reserva.id_cliente for reserva in reservas}),
    }


def reservas_por_dia(reservas):
    """Cuenta reservas no canceladas por dia de la semana."""
    conteo = {dia: 0 for dia in DIAS_SEMANA}
    for reserva in reservas:
        if reserva.estado.nombre_estado == ESTADO_CANCELADA:
            continue
        conteo[DIAS_SEMANA[reserva.fecha_reserva.weekday()]] += 1
    return conteo


def top_mesas(reservas, limite=7):
    """Devuelve las mesas con mas reservas no canceladas."""
    no_canceladas = [
        reserva for reserva in reservas
        if reserva.estado.nombre_estado != ESTADO_CANCELADA
    ]
    conteo = Counter(
        reserva.mesa.numero_mesa for reserva in no_canceladas
    )
    return conteo.most_common(limite)


def resumen_estados(reservas):
    """Cuenta las reservas por estado en un orden estable."""
    conteo = Counter(
        reserva.estado.nombre_estado for reserva in reservas
    )
    extras = sorted(set(conteo) - set(ORDEN_ESTADOS))
    return {
        estado: conteo.get(estado, 0)
        for estado in ORDEN_ESTADOS + tuple(extras)
    }
