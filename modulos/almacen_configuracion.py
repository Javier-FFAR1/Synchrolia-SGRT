# -*- coding: utf-8 -*-
"""
Almacen de Configuracion (MySQL)
Repositorio central que gestiona los parametros del sistema: horarios de
atencion, parametros generales y dias festivos.

Persiste en las tablas de MySQL: horarios_atencion, configuracion_general y
dias_festivos (restaurante_reservas). Mantiene la misma API publica que la
version en memoria para que el panel de configuracion no cambie.
"""

import datetime

from mysql.connector import Error
from sqlalchemy.exc import SQLAlchemyError

from conexion import get_conexion
from repository import FestivoRepository


DIAS_SEMANA = [
    "Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"
]

# Mapeo de claves UI <-> claves BD (configuracion_general)
_PARAM_UI_A_BD = {
    "duracion": "duracion_estandar_reserva_min",
    "tolerancia": "tiempo_tolerancia_min",
    "max_personas": "max_personas_por_reserva",
    "email_notif": "notif_email_confirmacion",
    "recordatorio": "notif_recordatorio",
}
_PARAM_BD_A_UI = {v: k for k, v in _PARAM_UI_A_BD.items()}

# Valores por defecto usados si la BD no tiene alguna clave
_PARAMETROS_DEFECTO = {
    "duracion": "90",
    "tolerancia": "15",
    "max_personas": "20",
    "email_notif": True,
    "recordatorio": False,
}

# Claves de configuracion_general para limites de anticipacion de reservas
# La columna valor es VARCHAR(100), por eso cada zona guarda un valor compacto
# "max_dias|requiere_deposito(0/1)|porcentaje_deposito" en su propia clave.
DIAS_ESTANDAR_ANTICIPACION_KEY = "dias_estandar_anticipacion"
PREFIJO_LIMITE_ZONA = "limite_anticipacion_zona_"
DIAS_ESTANDAR_ANTICIPACION_DEFECTO = 30

# Limites por defecto de una zona cuando aun no tiene configuracion guardada.
# El sistema es generico: toda zona nueva inicia con el mismo default.
ZONA_ANTICIPACION_DEFECTO = {
    "max_dias": 30,
    "requiere_deposito": False,
    "porcentaje_deposito": 30,
}


def _fecha_a_ui(fecha_bd):
    """date -> 'dd/mm/yyyy'"""
    if isinstance(fecha_bd, datetime.date):
        return fecha_bd.strftime("%d/%m/%Y")
    s = str(fecha_bd)
    partes = s.split("-")
    return f"{partes[2]}/{partes[1]}/{partes[0]}" if len(partes) == 3 else s


def _hora_a_ui(hora):
    s = str(hora)
    return s[:5] if ":" in s else s


class AlmacenConfiguracion:
    """Repositorio de configuracion persistido en MySQL."""

    # ---------------- Horarios ----------------

    def obtener_horarios(self):
        """Devuelve el horario de atencion por dia (orden Lunes..Domingo)."""
        conn = get_conexion()
        if conn is None:
            return [{"dia": d, "apertura": "12:00", "cierre": "22:00", "cerrado": False} for d in DIAS_SEMANA]
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT dia_semana, hora_apertura, hora_cierre, cerrado
                   FROM horarios_atencion"""
            )
            mapa = {}
            for dia, ap, ci, cerrado in cur.fetchall():
                mapa[dia] = {
                    "dia": dia,
                    "apertura": _hora_a_ui(ap),
                    "cierre": _hora_a_ui(ci),
                    "cerrado": bool(cerrado),
                }
            cur.close()
            return [mapa[d] for d in DIAS_SEMANA if d in mapa]
        except Error:
            return []
        finally:
            conn.close()

    def guardar_horarios(self, horarios):
        """
        Recibe una lista de dicts {dia, apertura, cierre, cerrado} y guarda.
        Devuelve el numero de dias configurados.
        """
        conn = get_conexion()
        if conn is None:
            return 0
        try:
            cur = conn.cursor()
            for h in horarios:
                cur.execute(
                    """UPDATE horarios_atencion
                       SET hora_apertura = %s, hora_cierre = %s, cerrado = %s
                       WHERE dia_semana = %s""",
                    (h["apertura"] + ":00", h["cierre"] + ":00",
                     bool(h["cerrado"]), h["dia"]),
                )
            conn.commit()
            cur.close()
            return len(horarios)
        except Error:
            return 0
        finally:
            conn.close()

    # ---------------- Parametros ----------------

    def obtener_parametros(self):
        """Devuelve los parametros del sistema desde configuracion_general."""
        conn = get_conexion()
        if conn is None:
            return dict(_PARAMETROS_DEFECTO)
        try:
            cur = conn.cursor()
            cur.execute("SELECT clave, valor FROM configuracion_general")
            mapa = dict(cur.fetchall())
            cur.close()

            params = dict(_PARAMETROS_DEFECTO)
            for clave_bd, clave_ui in _PARAM_BD_A_UI.items():
                if clave_bd in mapa:
                    valor = mapa[clave_bd]
                    if clave_ui in ("email_notif", "recordatorio"):
                        params[clave_ui] = str(valor) not in ("0", "False", "", "None")
                    else:
                        params[clave_ui] = str(valor)
            return params
        except Error:
            return dict(_PARAMETROS_DEFECTO)
        finally:
            conn.close()

    def guardar_parametros(self, duracion, tolerancia, max_personas,
                           email_notif, recordatorio):
        """Guarda los parametros generales. Devuelve el dict guardado."""
        valores = {
            "duracion": str(duracion),
            "tolerancia": str(tolerancia),
            "max_personas": str(max_personas),
            "email_notif": 1 if email_notif else 0,
            "recordatorio": 1 if recordatorio else 0,
        }
        conn = get_conexion()
        if conn is None:
            return valores
        try:
            cur = conn.cursor()
            for clave_ui, valor in valores.items():
                cur.execute(
                    """UPDATE configuracion_general SET valor = %s
                       WHERE clave = %s""",
                    (str(valor), _PARAM_UI_A_BD[clave_ui]),
                )
            conn.commit()
            cur.close()
        except Error:
            pass
        finally:
            conn.close()
        return dict(valores)

    # ---------------- Anticipacion de reservas ----------------

    def _leer_key(self, clave):
        """Lee una clave suelta de configuracion_general."""
        conn = get_conexion()
        if conn is None:
            return None
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT valor FROM configuracion_general WHERE clave = %s",
                (clave,),
            )
            fila = cur.fetchone()
            cur.close()
            return fila[0] if fila else None
        except Error:
            return None
        finally:
            conn.close()

    def _escribir_key(self, clave, valor):
        """Inserta o actualiza una clave suelta de configuracion_general."""
        conn = get_conexion()
        if conn is None:
            return False
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM configuracion_general WHERE clave = %s",
                (clave,),
            )
            existe = cur.fetchone()[0] > 0
            if existe:
                cur.execute(
                    "UPDATE configuracion_general SET valor = %s WHERE clave = %s",
                    (str(valor), clave),
                )
            else:
                cur.execute(
                    "INSERT INTO configuracion_general (clave, valor) VALUES (%s, %s)",
                    (clave, str(valor)),
                )
            conn.commit()
            cur.close()
            return True
        except Error:
            return False
        finally:
            conn.close()

    def _eliminar_key(self, clave):
        """Elimina una clave suelta de configuracion_general."""
        conn = get_conexion()
        if conn is None:
            return False
        try:
            cur = conn.cursor()
            cur.execute(
                "DELETE FROM configuracion_general WHERE clave = %s", (clave,)
            )
            conn.commit()
            cur.close()
            return True
        except Error:
            return False
        finally:
            conn.close()

    def obtener_dias_estandar(self):
        """Dias max. de anticipacion para reservas sin requisitos."""
        valor = self._leer_key(DIAS_ESTANDAR_ANTICIPACION_KEY)
        try:
            return int(valor)
        except (TypeError, ValueError):
            return DIAS_ESTANDAR_ANTICIPACION_DEFECTO

    def guardar_dias_estandar(self, dias):
        return self._escribir_key(DIAS_ESTANDAR_ANTICIPACION_KEY, int(dias))

    def obtener_limites_anticipacion(self):
        """Limites por zona {zona: {max_dias, requiere_deposito, porcentaje_deposito}}.

        Solo incluye zonas con configuracion guardada; las zonas nuevas usan el
        default uniforme (ZONA_ANTICIPACION_DEFECTO) sin necesidad de registrarse.
        """
        limites = {}
        conn = get_conexion()
        if conn is None:
            return limites
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT clave, valor FROM configuracion_general WHERE clave LIKE %s",
                (PREFIJO_LIMITE_ZONA + "%",),
            )
            for clave, valor in cur.fetchall():
                zona = clave[len(PREFIJO_LIMITE_ZONA):]
                cfg = dict(ZONA_ANTICIPACION_DEFECTO)
                partes = str(valor).split("|")
                if len(partes) >= 1:
                    try:
                        cfg["max_dias"] = int(partes[0])
                    except ValueError:
                        pass
                if len(partes) >= 2:
                    cfg["requiere_deposito"] = partes[1] in ("1", "True", "true")
                if len(partes) >= 3:
                    try:
                        cfg["porcentaje_deposito"] = int(partes[2])
                    except ValueError:
                        pass
                limites[zona] = cfg
            cur.close()
        except Error:
            pass
        finally:
            conn.close()
        return limites

    def guardar_limites_anticipacion(self, limites):
        ok_total = True
        for zona, cfg in limites.items():
            valor = "|".join([
                str(cfg.get("max_dias", 30)),
                "1" if cfg.get("requiere_deposito") else "0",
                str(cfg.get("porcentaje_deposito", 30)),
            ])
            ok = self._escribir_key(PREFIJO_LIMITE_ZONA + zona, valor)
            ok_total = ok_total and ok
        return ok_total

    def renombrar_zona_limites(self, anterior, nuevo):
        """Mueve la configuracion de limites de una zona al renombrar el area."""
        if not anterior or not nuevo or anterior == nuevo:
            return
        valor = self._leer_key(PREFIJO_LIMITE_ZONA + anterior)
        if valor is not None:
            self._escribir_key(PREFIJO_LIMITE_ZONA + nuevo, valor)
            self._eliminar_key(PREFIJO_LIMITE_ZONA + anterior)

    def eliminar_zona_limites(self, zona):
        """Elimina la configuracion de limites de una zona al borrar el area."""
        if zona:
            self._eliminar_key(PREFIJO_LIMITE_ZONA + zona)

    # ---------------- Festivos ----------------

    def obtener_festivos(self):
        """Devuelve los festivos desde dias_festivos usando el repositorio ORM."""
        try:
            festivos = FestivoRepository.obtener_todos()
        except SQLAlchemyError:
            return []
        return [
            {
                "fecha": _fecha_a_ui(festivo.fecha),
                "descripcion": festivo.descripcion or "",
                "accion": festivo.accion,
            }
            for festivo in festivos
        ]

    def agregar_festivo(self, fecha, descripcion, accion):
        """Agrega un festivo. Devuelve (True, None) o (False, error)."""
        fecha = fecha.strip()
        if not fecha:
            return False, "La fecha no puede estar vacia."
        if not self._fecha_valida(fecha):
            return False, "La fecha debe tener el formato DD/MM/AAAA y ser una fecha real."
        dia, mes, anio = (int(p) for p in fecha.split("/"))
        fecha_bd = datetime.date(anio, mes, dia)
        if fecha_bd < datetime.date.today():
            return False, (
                "No se puede registrar un festivo en el pasado.\n"
                "Use la fecha de hoy o una fecha futura."
            )
        try:
            if FestivoRepository.existe(fecha_bd):
                return False, f"Ya existe un festivo el {fecha}."
            if FestivoRepository.crear(
                fecha_bd, descripcion.strip() or "Festivo", accion
            ):
                return True, None
            return False, "No se pudo guardar el festivo en la base de datos."
        except SQLAlchemyError as e:
            return False, f"Error al agregar el festivo: {e}"

    @staticmethod
    def _fecha_valida(fecha):
        """Valida que la fecha sea real con formato DD/MM/AAAA."""
        partes = fecha.split("/")
        if len(partes) != 3:
            return False
        try:
            dia, mes, anio = int(partes[0]), int(partes[1]), int(partes[2])
            datetime.date(anio, mes, dia)
            return True
        except ValueError:
            return False

    def eliminar_festivo(self, fecha):
        """Elimina un festivo por su fecha usando el repositorio ORM."""
        if not self._fecha_valida(fecha):
            return False
        dia, mes, anio = (int(p) for p in fecha.split("/"))
        try:
            return FestivoRepository.eliminar(datetime.date(anio, mes, dia))
        except SQLAlchemyError:
            return False


# Punto de acceso global compartido por toda la aplicacion
almacen_config = AlmacenConfiguracion()
