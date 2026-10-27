# -*- coding: utf-8 -*-
"""
Patron Repository (Sesiones 30, 31 y 33 - SQLAlchemy ORM).

Encapsula las consultas y transacciones de la base de datos. La interfaz
grafica (PySide6) no conoce Session, select() ni SQL: solo invoca metodos
del repositorio, que devuelven entidades u objetos simples.

Cada metodo abre su propia Session con un context manager y garantiza
commit/rollback, evitando fugas de conexiones del pool.
"""

from datetime import date
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from database import SessionLocal
from models import DiaFestivoModel


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
