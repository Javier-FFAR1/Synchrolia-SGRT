# -*- coding: utf-8 -*-
"""
Capa de conexion ORM (Sesion 28 - SQLAlchemy + MySQL + PyMySQL).

Centraliza el Engine de SQLAlchemy, el pool de conexiones y la fabrica de
sesiones (SessionLocal). Reutiliza la configuracion y la carga del archivo
.env que ya realiza conexion.py, para no duplicar credenciales.

El resto de la aplicacion sigue usando conexion.py (SQL nativo); esta capa
ORM convive con ella y se usa en los modulos migrados (festivos, reportes).
"""

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from conexion import _CONFIG


def _construir_url():
    """Construye la URI de conexion para el dialecto MySQL + driver PyMySQL."""
    usuario = quote_plus(str(_CONFIG["user"]))
    clave = quote_plus(str(_CONFIG["password"]))
    return (
        f"mysql+pymysql://{usuario}:{clave}"
        f"@{_CONFIG['host']}:{_CONFIG['port']}/{_CONFIG['database']}"
        "?charset=utf8mb4"
    )


# Permite sobrescribir la URI completa (util en pruebas o entornos externos).
DATABASE_URL = os.environ.get("SYNCHROLIA_DATABASE_URL") or _construir_url()

# El Engine administra el pool de conexiones y traduce las operaciones al
# dialecto SQL de MySQL. pool_pre_ping evita usar conexiones caidas.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# Fabrica oficial de sesiones (patron Unit of Work de la Sesion 30).
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def probar_conexion():
    """Comprueba la conexion con el Engine y reporta el resultado (Sesion 28)."""
    try:
        with engine.connect():
            print("CONEXION EXITOSA A MYSQL MEDIANTE SQLALCHEMY ENGINE")
            return True
    except SQLAlchemyError as error:
        print(f"ERROR AL CONECTAR: {error}")
        return False


if __name__ == "__main__":
    probar_conexion()
