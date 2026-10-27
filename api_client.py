# -*- coding: utf-8 -*-
"""
Cliente REST configurable (Sesion 37 - Arquitectura cliente-servidor).

Implementa el lado cliente del estilo arquitectonico REST: recursos,
metodos HTTP y representaciones JSON. La URL base se toma de la variable
SYNCHROLIA_API_URL (o del archivo .env); si no se define, se usa
http://127.0.0.1:8000/api.

No depende de un servidor concreto: cualquier backend que respete los
endpoints documentados en README.md puede conectarse.

Uso:
    from api_client import ReservasApi

    api = ReservasApi()
    print(api.listar(periodo="Hoy"))
"""

import os
from pathlib import Path

import requests


class ApiError(Exception):
    """Error de la API con el codigo HTTP y la respuesta del servidor."""

    def __init__(self, mensaje, codigo=None, datos=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.datos = datos


class ApiNoDisponibleError(ApiError):
    """El servidor no responde, la URL es invalida o hubo un timeout."""


def _leer_env(ruta=None):
    """Carga variables CLAVE=VALOR desde .env sin depender de dotenv."""
    ruta = Path(ruta) if ruta else Path(__file__).resolve().with_name(".env")
    if not ruta.exists():
        return
    with ruta.open("r", encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            clave = clave.strip()
            valor = valor.strip().strip('"').strip("'")
            if clave and clave not in os.environ:
                os.environ[clave] = valor


def _url_base_por_defecto():
    _leer_env()
    return os.environ.get(
        "SYNCHROLIA_API_URL", "http://127.0.0.1:8000/api"
    ).rstrip("/")


class ApiClient:
    """Cliente HTTP/JSON generico para consumir una API REST."""

    def __init__(self, base_url=None, timeout=8):
        self.base_url = (base_url or _url_base_por_defecto()).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Synchrolia-SGRT/1.0",
        })

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cerrar()

    def cerrar(self):
        """Libera la Session y sus conexiones HTTP."""
        self.session.close()

    def _url(self, recurso):
        return f"{self.base_url}/{recurso.lstrip('/')}"

    def _solicitar(self, metodo, recurso, **kwargs):
        url = self._url(recurso)
        kwargs.setdefault("timeout", self.timeout)

        try:
            respuesta = self.session.request(metodo, url, **kwargs)
        except requests.RequestException as error:
            raise ApiNoDisponibleError(
                f"No se pudo conectar con la API en {url}: {error}"
            ) from error

        if not respuesta.ok:
            datos = None
            try:
                datos = respuesta.json()
            except ValueError:
                datos = respuesta.text

            detalle = ""
            if isinstance(datos, dict):
                detalle = (
                    datos.get("detail")
                    or datos.get("mensaje")
                    or datos.get("error")
                    or ""
                )
            elif isinstance(datos, str):
                detalle = datos

            raise ApiError(
                f"Error HTTP {respuesta.status_code} en {metodo} {url}"
                + (f": {detalle}" if detalle else ""),
                codigo=respuesta.status_code,
                datos=datos,
            )

        if respuesta.status_code == 204 or not respuesta.content:
            return None

        try:
            return respuesta.json()
        except ValueError:
            return respuesta.text

    def get(self, recurso, params=None):
        """Solicita un recurso con GET y devuelve su representacion JSON."""
        return self._solicitar("GET", recurso, params=params)

    def post(self, recurso, datos=None):
        """Crea un recurso con POST y devuelve la respuesta JSON."""
        return self._solicitar("POST", recurso, json=datos)

    def put(self, recurso, datos=None):
        """Reemplaza un recurso completo con PUT."""
        return self._solicitar("PUT", recurso, json=datos)

    def patch(self, recurso, datos=None):
        """Actualiza parcialmente un recurso con PATCH."""
        return self._solicitar("PATCH", recurso, json=datos)

    def delete(self, recurso):
        """Elimina un recurso con DELETE."""
        return self._solicitar("DELETE", recurso)


class ReservasApi:
    """Endpoints REST del recurso reservas."""

    def __init__(self, cliente=None):
        self.cliente = cliente or ApiClient()

    def listar(self, periodo=None, **filtros):
        """GET /reservas?periodo=...&otro_filtro=..."""
        params = dict(filtros)
        if periodo:
            params["periodo"] = periodo
        return self.cliente.get("reservas", params=params or None)

    def obtener(self, id_reserva):
        """GET /reservas/{id}"""
        return self.cliente.get(f"reservas/{id_reserva}")

    def crear(self, datos):
        """POST /reservas"""
        return self.cliente.post("reservas", datos)

    def actualizar(self, id_reserva, datos):
        """PUT /reservas/{id}"""
        return self.cliente.put(f"reservas/{id_reserva}", datos)

    def actualizar_parcial(self, id_reserva, datos):
        """PATCH /reservas/{id}"""
        return self.cliente.patch(f"reservas/{id_reserva}", datos)

    def eliminar(self, id_reserva):
        """DELETE /reservas/{id}"""
        return self.cliente.delete(f"reservas/{id_reserva}")

    def cerrar(self):
        """Cierra la Session HTTP del cliente asociado."""
        self.cliente.cerrar()
