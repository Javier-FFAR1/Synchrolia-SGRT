# -*- coding: utf-8 -*-
"""
Modulo de Conexion a MySQL (Sesion 16 - Patron de Clase de Conexion)
Capa unica que centraliza el ciclo de vida de las conexiones a la base
de datos MySQL del restaurante.

Sigue el patron de la sesion 16 (conexion.py -> clase ConexionBD) para
evitar duplicar la configuracion de red/credenciales en cada modulo.
"""

import os

import mysql.connector
from mysql.connector import Error


def _cargar_env(archivo=".env"):
    """Carga variables CLAVE=VALOR de un archivo .env local (sin dotenv).

    Complementa pero no reemplaza a las variables de entorno del sistema:
    las variables ya definidas en el entorno tienen prioridad. Ignora lineas
    vacias y comentarios (que empiecen con '#').
    """
    if not os.path.exists(archivo):
        return
    with open(archivo, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            clave = clave.strip()
            valor = valor.strip().strip('"').strip("'")
            if clave and clave not in os.environ:
                os.environ[clave] = valor


_cargar_env()


# Valores por defecto; se sobreescriben con variables de entorno.
# La contrasena se lee siempre de la variable de entorno SYNCHROLIA_DB_PASSWORD
# para no exponer credenciales en el repositorio.
_CONFIG = {
    "host": os.environ.get("SYNCHROLIA_DB_HOST", "localhost"),
    "port": int(os.environ.get("SYNCHROLIA_DB_PORT", 3306)),
    "user": os.environ.get("SYNCHROLIA_DB_USER", "root"),
    "password": os.environ.get("SYNCHROLIA_DB_PASSWORD", ""),
    "database": os.environ.get("SYNCHROLIA_DB_NAME", "restaurante_reservas"),
}


class ConexionBD:
    """Clase encargada de gestionar el ciclo de vida de las conexiones a MySQL."""

    def __init__(self):
        self.host = _CONFIG["host"]
        self.port = _CONFIG["port"]
        self.user = _CONFIG["user"]
        self.password = _CONFIG["password"]
        self.database = _CONFIG["database"]
        self.conexion = None

    def conectar(self):
        """Establece y retorna una nueva conexion a la base de datos."""
        try:
            self.conexion = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
            )
            if self.conexion.is_connected():
                return self.conexion
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            return None

    def desconectar(self):
        """Cierra la conexion activa si se encuentra abierta."""
        if self.conexion and self.conexion.is_connected():
            self.conexion.close()
            self.conexion = None


def get_conexion():
    """
    Devuelve una conexion MySQL nueva (abierta) o None si falla.
    Util para que los repositorios/almacenes creen conexiones puntuales
    por operacion sin compartir estado global.
    """
    db = ConexionBD()
    return db.conectar()


# Instancia global reutilizable (un solo punto de acceso)
conexion_bd = ConexionBD()
