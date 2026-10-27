# -*- coding: utf-8 -*-
"""
Modelos declarativos del sistema (Sesion 29 y 32 - SQLAlchemy 2.0).

Cada clase representa una tabla de la base de datos restaurante_reservas:
clase -> tabla, instancia -> fila, atributo -> columna. Se usan Mapped[T] y
mapped_column() para el tipado estatico y las restricciones fisicas.

Las relaciones uno a muchos se declaran con relationship() y back_populates
para la navegacion bidireccional; el historial de reservas usa cascada.
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Time,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Registro central de metadatos de todos los modelos."""


# Tabla intermedia N:M entre roles y permisos (RBAC).
permisos_rol = Table(
    "permisos_rol",
    Base.metadata,
    Column("id_rol", Integer, ForeignKey("roles.id_rol"), primary_key=True),
    Column("id_permiso", Integer, ForeignKey("permisos.id_permiso"), primary_key=True),
)


class RolModel(Base):
    __tablename__ = "roles"

    id_rol: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_rol: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)

    usuarios: Mapped[List["UsuarioModel"]] = relationship(
        "UsuarioModel", back_populates="rol"
    )
    permisos: Mapped[List["PermisoModel"]] = relationship(
        "PermisoModel", secondary=permisos_rol, back_populates="roles"
    )

    def __repr__(self):
        return f"<Rol(id={self.id_rol}, nombre='{self.nombre_rol}')>"


class PermisoModel(Base):
    __tablename__ = "permisos"

    id_permiso: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    codigo_permiso: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    descripcion: Mapped[str] = mapped_column(String(150), nullable=False)

    roles: Mapped[List["RolModel"]] = relationship(
        "RolModel", secondary=permisos_rol, back_populates="permisos"
    )

    def __repr__(self):
        return f"<Permiso(id={self.id_permiso}, codigo='{self.codigo_permiso}')>"


class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    nombre_completo: Mapped[str] = mapped_column(String(100), nullable=False)
    nombre_usuario: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    id_rol: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id_rol"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    rol: Mapped["RolModel"] = relationship("RolModel", back_populates="usuarios")
    reservas: Mapped[List["ReservaModel"]] = relationship(
        "ReservaModel", back_populates="usuario"
    )
    historial: Mapped[List["HistorialReservaModel"]] = relationship(
        "HistorialReservaModel", back_populates="usuario"
    )

    def __repr__(self):
        return f"<Usuario(id={self.id_usuario}, usuario='{self.nombre_usuario}')>"


class ClienteModel(Base):
    __tablename__ = "clientes"

    id_cliente: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    nombre_completo: Mapped[str] = mapped_column(String(100), nullable=False)
    telefono: Mapped[str] = mapped_column(String(20), nullable=False)
    correo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    reservas: Mapped[List["ReservaModel"]] = relationship(
        "ReservaModel", back_populates="cliente"
    )

    def __repr__(self):
        return f"<Cliente(id={self.id_cliente}, nombre='{self.nombre_completo}')>"


class UbicacionModel(Base):
    __tablename__ = "ubicaciones"

    id_ubicacion: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    nombre_ubicacion: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )

    mesas: Mapped[List["MesaModel"]] = relationship(
        "MesaModel", back_populates="ubicacion"
    )

    def __repr__(self):
        return f"<Ubicacion(id={self.id_ubicacion}, nombre='{self.nombre_ubicacion}')>"


class EstadoMesaModel(Base):
    __tablename__ = "estados_mesa"

    id_estado_mesa: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    nombre_estado: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    mesas: Mapped[List["MesaModel"]] = relationship(
        "MesaModel", back_populates="estado"
    )

    def __repr__(self):
        return f"<EstadoMesa(id={self.id_estado_mesa}, nombre='{self.nombre_estado}')>"


class EstadoReservaModel(Base):
    __tablename__ = "estados_reserva"

    id_estado_reserva: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    nombre_estado: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    reservas: Mapped[List["ReservaModel"]] = relationship(
        "ReservaModel", back_populates="estado"
    )

    def __repr__(self):
        return (
            f"<EstadoReserva(id={self.id_estado_reserva}, "
            f"nombre='{self.nombre_estado}')>"
        )


class MesaModel(Base):
    __tablename__ = "mesas"

    id_mesa: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    numero_mesa: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    capacidad: Mapped[int] = mapped_column(Integer, nullable=False)
    id_ubicacion: Mapped[int] = mapped_column(
        Integer, ForeignKey("ubicaciones.id_ubicacion"), nullable=False
    )
    id_estado_mesa: Mapped[int] = mapped_column(
        Integer, ForeignKey("estados_mesa.id_estado_mesa"), nullable=False
    )

    ubicacion: Mapped["UbicacionModel"] = relationship(
        "UbicacionModel", back_populates="mesas"
    )
    estado: Mapped["EstadoMesaModel"] = relationship(
        "EstadoMesaModel", back_populates="mesas"
    )
    reservas: Mapped[List["ReservaModel"]] = relationship(
        "ReservaModel", back_populates="mesa"
    )

    def __repr__(self):
        return f"<Mesa(id={self.id_mesa}, numero='{self.numero_mesa}')>"


class ReservaModel(Base):
    __tablename__ = "reservas"

    id_reserva: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    id_cliente: Mapped[int] = mapped_column(
        Integer, ForeignKey("clientes.id_cliente"), nullable=False
    )
    id_mesa: Mapped[int] = mapped_column(
        Integer, ForeignKey("mesas.id_mesa"), nullable=False
    )
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario"), nullable=False
    )
    id_estado_reserva: Mapped[int] = mapped_column(
        Integer, ForeignKey("estados_reserva.id_estado_reserva"), nullable=False
    )
    fecha_reserva: Mapped[date] = mapped_column(Date, nullable=False)
    hora_inicio: Mapped[time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[time] = mapped_column(Time, nullable=False)
    numero_personas: Mapped[int] = mapped_column(Integer, nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    cliente: Mapped["ClienteModel"] = relationship(
        "ClienteModel", back_populates="reservas"
    )
    mesa: Mapped["MesaModel"] = relationship("MesaModel", back_populates="reservas")
    usuario: Mapped["UsuarioModel"] = relationship(
        "UsuarioModel", back_populates="reservas"
    )
    estado: Mapped["EstadoReservaModel"] = relationship(
        "EstadoReservaModel", back_populates="reservas"
    )
    historial: Mapped[List["HistorialReservaModel"]] = relationship(
        "HistorialReservaModel",
        back_populates="reserva",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"<Reserva(id={self.id_reserva}, fecha={self.fecha_reserva}, "
            f"mesa_id={self.id_mesa})>"
        )


class HorarioAtencionModel(Base):
    __tablename__ = "horarios_atencion"

    id_horario: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    dia_semana: Mapped[str] = mapped_column(
        Enum(
            "Lunes",
            "Martes",
            "Miercoles",
            "Jueves",
            "Viernes",
            "Sabado",
            "Domingo",
            name="dia_semana_enum",
        ),
        nullable=False,
        unique=True,
    )
    hora_apertura: Mapped[time] = mapped_column(Time, nullable=False)
    hora_cierre: Mapped[time] = mapped_column(Time, nullable=False)
    cerrado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Horario(dia='{self.dia_semana}')>"


class DiaFestivoModel(Base):
    __tablename__ = "dias_festivos"

    id_dia_festivo: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    fecha: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    accion: Mapped[str] = mapped_column(
        Enum("Cerrado", "Horario Especial", name="accion_festivo_enum"),
        nullable=False,
        default="Cerrado",
    )

    def __repr__(self):
        return f"<DiaFestivo(fecha={self.fecha}, accion='{self.accion}')>"


class ConfiguracionGeneralModel(Base):
    __tablename__ = "configuracion_general"

    id_config: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    clave: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    valor: Mapped[str] = mapped_column(String(100), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    def __repr__(self):
        return f"<Configuracion(clave='{self.clave}', valor='{self.valor}')>"


class HistorialReservaModel(Base):
    __tablename__ = "historial_reservas"

    id_historial: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    id_reserva: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reservas.id_reserva", ondelete="CASCADE"),
        nullable=False,
    )
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario"), nullable=False
    )
    accion: Mapped[str] = mapped_column(String(20), nullable=False)
    fecha_accion: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    detalle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    reserva: Mapped["ReservaModel"] = relationship(
        "ReservaModel", back_populates="historial"
    )
    usuario: Mapped["UsuarioModel"] = relationship(
        "UsuarioModel", back_populates="historial"
    )

    def __repr__(self):
        return (
            f"<Historial(id={self.id_historial}, reserva={self.id_reserva}, "
            f"accion='{self.accion}')>"
        )
