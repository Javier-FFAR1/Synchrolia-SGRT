# -*- coding: utf-8 -*-
"""
Patron Repository (Sesiones 30, 31 y 33 - SQLAlchemy ORM).

Encapsula las consultas y transacciones de la base de datos. La interfaz
grafica (PySide6) no conoce Session, select() ni SQL: solo invoca metodos
del repositorio, que devuelven entidades u objetos simples.

Cada metodo abre su propia Session con un context manager y garantiza
commit/rollback, evitando fugas de conexiones del pool.
"""

from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from database import SessionLocal
from models import DiaFestivoModel, MesaModel, ReservaModel


class FestivoRepository:
    """Repositorio ORM de dias festivos (tabla dias_festivos)."""

    @staticmethod
    def obtener_todos() -> List[DiaFestivoModel]:
        """Devuelve todos los festivos ordenados por fecha (Read)."""
        with SessionLocal() as session:
            stmt = select(DiaFestivoModel).order_by(DiaFestivoModel.fecha)
            return list(session.scalars(stmt).all())

    @staticmethod
    def buscar_por_fecha(fecha: date) -> Optional[DiaFestivoModel]:
        """Devuelve el festivo de una fecha o None si no existe."""
        with SessionLocal() as session:
            stmt = select(DiaFestivoModel).where(DiaFestivoModel.fecha == fecha)
            return session.scalars(stmt).first()

    @staticmethod
    def existe(fecha: date) -> bool:
        """Indica si ya hay un festivo registrado en esa fecha."""
        return FestivoRepository.buscar_por_fecha(fecha) is not None

    @staticmethod
    def crear(fecha: date, descripcion: str, accion: str) -> bool:
        """Crea un festivo dentro de una transaccion (Create)."""
        with SessionLocal() as session:
            try:
                session.add(
                    DiaFestivoModel(
                        fecha=fecha,
                        descripcion=descripcion,
                        accion=accion,
                    )
                )
                session.commit()
                return True
            except SQLAlchemyError as error:
                session.rollback()
                print(f"Error transaccional al crear festivo: {error}")
                return False

    @staticmethod
    def actualizar(fecha: date, descripcion: str, accion: str) -> bool:
        """Actualiza un festivo existente (Update con dirty tracking)."""
        with SessionLocal() as session:
            try:
                stmt = select(DiaFestivoModel).where(DiaFestivoModel.fecha == fecha)
                festivo = session.scalars(stmt).first()
                if festivo is None:
                    return False
                festivo.descripcion = descripcion
                festivo.accion = accion
                session.commit()
                return True
            except SQLAlchemyError as error:
                session.rollback()
                print(f"Error transaccional al actualizar festivo: {error}")
                return False

    @staticmethod
    def eliminar(fecha: date) -> bool:
        """Elimina el festivo de una fecha (Delete)."""
        with SessionLocal() as session:
            try:
                stmt = select(DiaFestivoModel).where(DiaFestivoModel.fecha == fecha)
                festivo = session.scalars(stmt).first()
                if festivo is None:
                    return False
                session.delete(festivo)
                session.commit()
                return True
            except SQLAlchemyError as error:
                session.rollback()
                print(f"Error transaccional al eliminar festivo: {error}")
                return False


class ReservaRepository:
    """Repositorio ORM de reservas con relaciones precargadas."""

    @staticmethod
    def _aplicar_periodo(stmt, periodo: str):
        """Aplica el filtro de fecha del panel de reportes."""
        hoy = date.today()
        if periodo == "Hoy":
            return stmt.where(ReservaModel.fecha_reserva == hoy)
        if periodo == "Esta Semana":
            inicio = hoy - timedelta(days=hoy.weekday())
            fin = inicio + timedelta(days=6)
            return stmt.where(ReservaModel.fecha_reserva.between(inicio, fin))
        if periodo == "Este Mes":
            inicio = hoy.replace(day=1)
            if hoy.month == 12:
                fin = date(hoy.year + 1, 1, 1) - timedelta(days=1)
            else:
                fin = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
            return stmt.where(ReservaModel.fecha_reserva.between(inicio, fin))
        return stmt

    @staticmethod
    def obtener_detalladas(periodo: str = "Todos") -> List[ReservaModel]:
        """Devuelve las reservas del periodo con cliente, mesa, estado y usuario.

        Usa selectinload para evitar el problema N+1 (Sesion 33): las
        relaciones se cargan en pocas consultas y quedan disponibles aunque
        la Session se cierre antes de renderizar el PDF.
        """
        with SessionLocal() as session:
            stmt = (
                select(ReservaModel)
                .options(
                    selectinload(ReservaModel.cliente),
                    selectinload(ReservaModel.mesa).selectinload(
                        MesaModel.ubicacion
                    ),
                    selectinload(ReservaModel.estado),
                    selectinload(ReservaModel.usuario),
                )
                .order_by(
                    ReservaModel.fecha_reserva.desc(),
                    ReservaModel.hora_inicio.asc(),
                )
            )
            stmt = ReservaRepository._aplicar_periodo(stmt, periodo)
            return list(session.scalars(stmt).all())


class MesaRepository:
    """Repositorio ORM de mesas."""

    @staticmethod
    def contar_todas() -> int:
        """Devuelve el total de mesas registradas en el restaurante."""
        with SessionLocal() as session:
            return session.scalar(select(func.count()).select_from(MesaModel)) or 0
