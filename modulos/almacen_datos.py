# -*- coding: utf-8 -*-
"""
Almacen de Datos (MySQL + cache en memoria)
Repositorio central unico que gestiona las entidades del dominio: clientes,
reservas y mesas. Es la UNICA fuente de verdad de la que dependen los modulos
(PanelReservas, PanelMesas, PanelReportes, PanelClientes, PanelDashboard).

Para no reescribir la interfaz, las listas en memoria (lista_reservas,
lista_clientes) actuan como cache que se SIEMBRA desde MySQL al importar.
Toda operacion CRUD pasa por los metodos de este repositorio, que persisten
en la base de datos y mantienen la cache sincronizada.

Los triggers y vistas de la BD (restaurante_reservas) aportan validacion y
auditoria a nivel de servidor (traslapes, aforo, historial).
"""

import datetime
import time

from mysql.connector import Error

from conexion import get_conexion


# ---------------------------------------------------------------------------
# Estados posibles de una reserva (constantes unicas para toda la app)
# ---------------------------------------------------------------------------
ESTADO_PENDIENTE = "Pendiente"
ESTADO_CONFIRMADA = "Confirmada"
ESTADO_CANCELADA = "Cancelada"
ESTADO_COMPLETADA = "Completada"
ESTADOS_RESERVA = [
    ESTADO_PENDIENTE,
    ESTADO_CONFIRMADA,
    ESTADO_CANCELADA,
    ESTADO_COMPLETADA,
]

# Ciclo de vida de una reserva. Solo estas transiciones son validas:
#   Pendiente  -> Confirmada / Cancelada
#   Confirmada -> Completada / Cancelada
#   Cancelada / Completada -> son estados terminales (no tienen salidas).
TRANSICIONES_ESTADO = {
    ESTADO_PENDIENTE: [ESTADO_CONFIRMADA, ESTADO_CANCELADA],
    ESTADO_CONFIRMADA: [ESTADO_COMPLETADA, ESTADO_CANCELADA],
    ESTADO_CANCELADA: [],
    ESTADO_COMPLETADA: [],
}


def transicion_estado_valida(estado_actual, nuevo_estado):
    """True si nuevo_estado es un paso valido desde estado_actual."""
    return nuevo_estado in TRANSICIONES_ESTADO.get(estado_actual, [])

# ---------------------------------------------------------------------------
# Estados posibles de una mesa
# ---------------------------------------------------------------------------
ESTADO_MESA_LIBRE = "Libre"
ESTADO_MESA_OCUPADA = "Ocupada"
ESTADO_MESA_RESERVADA = "Reservada"
ESTADO_MESA_MANTENIMIENTO = "Mantenimiento"
ESTADOS_MESA = [
    ESTADO_MESA_LIBRE,
    ESTADO_MESA_OCUPADA,
    ESTADO_MESA_RESERVADA,
    ESTADO_MESA_MANTENIMIENTO,
]


# ---------------------------------------------------------------------------
# Utilidades de formato de fecha (la UI usa dd/mm/yyyy, la BD date)
# ---------------------------------------------------------------------------
def _ui_a_bd_fecha(fecha_ui):
    """'dd/mm/yyyy' -> 'yyyy-mm-dd'"""
    try:
        d, m, y = fecha_ui.split("/")
        return f"{y}-{m}-{d}"
    except Exception:
        return fecha_ui


def _bd_a_ui_fecha(fecha_bd):
    """'yyyy-mm-dd' o date -> 'dd/mm/yyyy'"""
    if fecha_bd is None:
        return ""
    if isinstance(fecha_bd, datetime.date):
        return fecha_bd.strftime("%d/%m/%Y")
    s = str(fecha_bd)
    partes = s.split("-")
    if len(partes) == 3:
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return s


def _bd_a_ui_hora(hora):
    """time -> 'HH:MM'"""
    if hora is None:
        return ""
    s = str(hora)
    return s[:5] if ":" in s else s


# ---------------------------------------------------------------------------
# Helpers para resolver IDs (catálogos de la BD)
# ---------------------------------------------------------------------------
def _id_mesa_de(numero_mesa):
    conn = get_conexion()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_mesa FROM mesas WHERE numero_mesa = %s", (numero_mesa,))
        f = cur.fetchone()
        cur.close()
        return f[0] if f else None
    except Exception:
        return None
    finally:
        conn.close()


def _id_estado_reserva_de(nombre):
    conn = get_conexion()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_estado_reserva FROM estados_reserva WHERE nombre_estado = %s", (nombre,))
        f = cur.fetchone()
        cur.close()
        return f[0] if f else None
    except Exception:
        return None
    finally:
        conn.close()


def _id_usuario_de(nombre_completo):
    conn = get_conexion()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_usuario FROM usuarios WHERE nombre_completo = %s", (nombre_completo,))
        f = cur.fetchone()
        cur.close()
        return f[0] if f else None
    except Exception:
        return None
    finally:
        conn.close()


def _id_cliente_de(id_cliente):
    """Verifica que el cliente exista. Devuelve id o None."""
    conn = get_conexion()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_cliente FROM clientes WHERE id_cliente = %s", (id_cliente,))
        f = cur.fetchone()
        cur.close()
        return f[0] if f else None
    except Exception:
        return None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Catalogo de mesas (cargado desde la BD)
# ---------------------------------------------------------------------------
def _cargar_mesas():
    mesas = []
    conn = get_conexion()
    if conn is None:
        return mesas
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT m.numero_mesa, m.capacidad, u.nombre_ubicacion
               FROM mesas m
               JOIN ubicaciones u ON m.id_ubicacion = u.id_ubicacion
               ORDER BY m.id_mesa"""
        )
        for numero, capacidad, zona in cur.fetchall():
            mesas.append({"numero": numero, "capacidad": capacidad, "zona": zona})
        cur.close()
    except Error:
        return mesas
    finally:
        conn.close()
    return mesas


MESAS = _cargar_mesas()


# ---------------------------------------------------------------------------
# Carga de listas (cache) desde MySQL
# ---------------------------------------------------------------------------
def _cargar_reservas():
    """Devuelve las reservas con el formato que usa la UI (JOIN con cliente/mesa)."""
    reservas = []
    conn = get_conexion()
    if conn is None:
        return reservas
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT r.id_reserva, c.nombre_completo, m.numero_mesa,
                      r.fecha_reserva, r.hora_inicio, r.hora_fin,
                      r.numero_personas, er.nombre_estado,
                      COALESCE(r.observaciones, ''), us.nombre_completo,
                      r.id_cliente
               FROM reservas r
               JOIN clientes c ON r.id_cliente = c.id_cliente
               JOIN mesas m ON r.id_mesa = m.id_mesa
               JOIN estados_reserva er ON r.id_estado_reserva = er.id_estado_reserva
               LEFT JOIN usuarios us ON r.id_usuario = us.id_usuario
               ORDER BY r.id_reserva"""
        )
        for (rid, cliente, mesa, fecha, h_ini, h_fin,
             personas, estado, obs, gestiono, id_cliente) in cur.fetchall():
            reservas.append({
                "id": rid,
                "cliente": cliente,
                "id_cliente": id_cliente,
                "mesa": mesa,
                "fecha": _bd_a_ui_fecha(fecha),
                "hora_inicio": _bd_a_ui_hora(h_ini),
                "hora_fin": _bd_a_ui_hora(h_fin),
                "personas": str(personas),
                "estado": estado,
                "observaciones": obs,
                "gestiono": gestiono or "",
            })
        cur.close()
    except Error:
        reservas = []
    finally:
        conn.close()
    return reservas


def _cargar_clientes():
    """Devuelve los clientes con el formato que usa la UI."""
    clientes = []
    conn = get_conexion()
    if conn is None:
        return clientes
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT id_cliente, nombre_completo, telefono, COALESCE(correo, ''),
                      fecha_registro
               FROM clientes ORDER BY id_cliente"""
        )
        for cid, nombre, telefono, correo, registro in cur.fetchall():
            clientes.append({
                "id": cid,
                "nombre": nombre,
                "telefono": telefono,
                "correo": correo,
                "registro": _bd_a_ui_fecha(registro),
            })
        cur.close()
    except Error:
        clientes = []
    finally:
        conn.close()
    return clientes


def _cargar_mantenimiento():
    """Devuelve el set de mesas en mantenimiento segun la BD."""
    mant = set()
    conn = get_conexion()
    if conn is None:
        return mant
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT m.numero_mesa FROM mesas m
               JOIN estados_mesa em ON m.id_estado_mesa = em.id_estado_mesa
               WHERE em.nombre_estado = 'Mantenimiento'"""
        )
        mant = {fila[0] for fila in cur.fetchall()}
        cur.close()
    except Error:
        pass
    finally:
        conn.close()
    return mant


# Listas centrales (cache)
lista_reservas = _cargar_reservas()
lista_clientes = _cargar_clientes()
_mesas_mantenimiento = _cargar_mantenimiento()


# ---------------------------------------------------------------------------
# Gestion de mesas (mantenimiento)
# ---------------------------------------------------------------------------
def poner_mesa_en_mantenimiento(numero, activo=True):
    """Marca o desmarca una mesa como en mantenimiento (persistido en BD)."""
    conn = get_conexion()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_mesa FROM mesas WHERE numero_mesa = %s", (numero,))
        f = cur.fetchone()
        id_mesa = f[0] if f else None
        cur.close()
        if id_mesa is None:
            conn.close()
            return
        if activo:
            cur = conn.cursor()
            cur.execute(
                """UPDATE mesas SET id_estado_mesa =
                       (SELECT id_estado_mesa FROM estados_mesa WHERE nombre_estado = 'Mantenimiento')
                   WHERE id_mesa = %s""", (id_mesa,))
            conn.commit()
            cur.close()
            _mesas_mantenimiento.add(numero)
        else:
            # Quitar mantenimiento: el estado real se deriva de las reservas activas.
            _mesas_mantenimiento.discard(numero)
    except Error:
        pass
    finally:
        conn.close()
    if not activo:
        _sincronizar_estado_mesa_bd(numero)


def estado_mesa(numero):
    """Deriva el estado de una mesa (Mantenimiento/Ocupada/Reservada/Libre).

    Solo considera reservas del dia actual: una reserva confirmada de otro dia
    no debe marcar la mesa como ocupada hoy.
    """
    if numero in _mesas_mantenimiento:
        return ESTADO_MESA_MANTENIMIENTO
    hoy = datetime.date.today().strftime("%d/%m/%Y")
    for r in lista_reservas:
        if (r.get("mesa") == numero and r.get("fecha") == hoy
                and r.get("estado") == ESTADO_CONFIRMADA):
            return ESTADO_MESA_OCUPADA
    for r in lista_reservas:
        if (r.get("mesa") == numero and r.get("fecha") == hoy
                and r.get("estado") == ESTADO_PENDIENTE):
            return ESTADO_MESA_RESERVADA
    return ESTADO_MESA_LIBRE


def _sincronizar_estado_mesa_bd(numero):
    """
    Persiste en mesas.id_estado_mesa el estado derivado en memoria de una mesa
    (Mantenimiento/Ocupada/Reservada/Libre). Mantiene la columna de la BD
    coherente con el mapa visual de la aplicacion (vista_mapa_ocupacion,
    ocupacion promedio).
    """
    estado = estado_mesa(numero)
    conn = get_conexion()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_mesa FROM mesas WHERE numero_mesa = %s", (numero,))
        f = cur.fetchone()
        if f is None:
            cur.close()
            return
        id_mesa = f[0]
        cur.execute(
            """UPDATE mesas SET id_estado_mesa =
               (SELECT id_estado_mesa FROM estados_mesa WHERE nombre_estado = %s)
               WHERE id_mesa = %s""",
            (estado, id_mesa),
        )
        conn.commit()
        cur.close()
    except Error:
        pass
    finally:
        conn.close()


def mesas_con_estado():
    """Devuelve la lista de mesas con su estado derivado."""
    return [
        {"numero": m["numero"], "capacidad": m["capacidad"], "zona": m["zona"],
         "estado": estado_mesa(m["numero"])}
        for m in MESAS
    ]


def reservas_de_hoy(hoy=None):
    """Devuelve las reservas (no canceladas) cuya fecha coincide con 'hoy'."""
    from datetime import date
    hoy = hoy or date.today().strftime("%d/%m/%Y")
    return [
        r for r in lista_reservas
        if r.get("fecha") == hoy and r.get("estado") != ESTADO_CANCELADA
    ]


def hay_traslape(mesa, fecha, hora_inicio, hora_fin, id_excluir=None):
    """Verifica traslape de horario de una mesa en la misma fecha."""
    for r in lista_reservas:
        if id_excluir is not None and r.get("id") == id_excluir:
            continue
        if r.get("estado") not in (ESTADO_PENDIENTE, ESTADO_CONFIRMADA):
            continue
        if r.get("mesa") != mesa or r.get("fecha") != fecha:
            continue
        if hora_inicio < r.get("hora_fin", "") and hora_fin > r.get("hora_inicio", ""):
            return r
    return None


def mesas_disponibles(fecha, hora_inicio, hora_fin, personas=1, id_excluir=None):
    """Mesas libres con capacidad suficiente que no se traslapan."""
    disponibles = []
    for m in MESAS:
        numero = m["numero"]
        if numero in _mesas_mantenimiento:
            continue
        if m["capacidad"] < personas:
            continue
        if hay_traslape(numero, fecha, hora_inicio, hora_fin, id_excluir) is not None:
            continue
        disponibles.append({"numero": numero, "capacidad": m["capacidad"], "zona": m["zona"]})
    return disponibles


def local_lleno(fecha, hora_inicio, hora_fin, personas=1, id_excluir=None):
    """True si no queda ninguna mesa disponible."""
    return len(mesas_disponibles(fecha, hora_inicio, hora_fin, personas, id_excluir)) == 0


# ---------------------------------------------------------------------------
# Catalogo editable de areas (ubicaciones) y mesas
# El modelo ya es configurable: cada restaurante define sus propias areas y la
# cantidad/capacidad de sus mesas. Estas funciones lo administran en la BD.
# ---------------------------------------------------------------------------
def obtener_ubicaciones():
    """[{id, nombre}] ordenado por id."""
    conn = get_conexion()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id_ubicacion, nombre_ubicacion FROM ubicaciones ORDER BY id_ubicacion"
        )
        filas = [{"id": f[0], "nombre": f[1]} for f in cur.fetchall()]
        cur.close()
        return filas
    except Error:
        return []
    finally:
        conn.close()


def _mensaje_duplicado(error, entidad):
    """Si el error es de violacion de UNIQUE, devuelve un mensaje claro."""
    if getattr(error, "errno", None) == 1062:
        return f"Ya existe {entidad} con ese nombre o numero."
    return str(error)


def crear_ubicacion(nombre):
    """Crea un area nueva. Devuelve (id, None) o (None, error)."""
    nombre = (nombre or "").strip()
    if not nombre:
        return None, "El nombre del area no puede estar vacio."
    conn = get_conexion()
    if conn is None:
        return None, "No hay conexion a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO ubicaciones (nombre_ubicacion) VALUES (%s)", (nombre,)
        )
        conn.commit()
        nuevo_id = cur.lastrowid
        cur.close()
        return nuevo_id, None
    except Error as e:
        return None, _mensaje_duplicado(e, "un area")
    finally:
        conn.close()


def renombrar_ubicacion(id_ubicacion, nombre):
    """Renombra un area. Devuelve (True, None) o (False, error)."""
    nombre = (nombre or "").strip()
    if not nombre:
        return False, "El nombre del area no puede estar vacio."
    conn = get_conexion()
    if conn is None:
        return False, "No hay conexion a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE ubicaciones SET nombre_ubicacion = %s WHERE id_ubicacion = %s",
            (nombre, id_ubicacion),
        )
        conn.commit()
        cur.close()
        return True, None
    except Error as e:
        return False, _mensaje_duplicado(e, "un area")
    finally:
        conn.close()


def eliminar_ubicacion(id_ubicacion):
    """Elimina un area si no tiene mesas asociadas. Devuelve (True, None) o (False, error)."""
    conn = get_conexion()
    if conn is None:
        return False, "No hay conexion a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM ubicaciones WHERE id_ubicacion = %s", (id_ubicacion,))
        conn.commit()
        cur.close()
        return True, None
    except Error as e:
        if getattr(e, "errno", None) == 1451:
            return False, "No se puede eliminar el area: tiene mesas asociadas."
        return False, str(e)
    finally:
        conn.close()


def obtener_mesas():
    """[{id, numero, capacidad, id_ubicacion, zona}] ordenado por id."""
    conn = get_conexion()
    if conn is None:
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT m.id_mesa, m.numero_mesa, m.capacidad, m.id_ubicacion,
                      u.nombre_ubicacion
               FROM mesas m
               JOIN ubicaciones u ON m.id_ubicacion = u.id_ubicacion
               ORDER BY m.id_mesa"""
        )
        filas = [
            {"id": f[0], "numero": f[1], "capacidad": f[2],
             "id_ubicacion": f[3], "zona": f[4]}
            for f in cur.fetchall()
        ]
        cur.close()
        return filas
    except Error:
        return []
    finally:
        conn.close()


def crear_mesa(numero, capacidad, id_ubicacion):
    """Crea una mesa en el estado 'Libre'. Devuelve (True, None) o (False, error)."""
    numero = (numero or "").strip()
    if not numero:
        return False, "El numero de mesa no puede estar vacio."
    conn = get_conexion()
    if conn is None:
        return False, "No hay conexion a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO mesas (numero_mesa, capacidad, id_ubicacion, id_estado_mesa)
               VALUES (%s, %s, %s,
                       (SELECT id_estado_mesa FROM estados_mesa
                        WHERE nombre_estado = 'Libre'))""",
            (numero, int(capacidad), id_ubicacion),
        )
        conn.commit()
        cur.close()
        return True, None
    except Error as e:
        return False, _mensaje_duplicado(e, "una mesa")
    finally:
        conn.close()


def actualizar_mesa(id_mesa, numero, capacidad, id_ubicacion):
    """Actualiza numero, capacidad y area de una mesa. Devuelve (True, None) o (False, error)."""
    numero = (numero or "").strip()
    if not numero:
        return False, "El numero de mesa no puede estar vacio."
    conn = get_conexion()
    if conn is None:
        return False, "No hay conexion a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE mesas SET numero_mesa = %s, capacidad = %s, id_ubicacion = %s
               WHERE id_mesa = %s""",
            (numero, int(capacidad), id_ubicacion, id_mesa),
        )
        conn.commit()
        cur.close()
        return True, None
    except Error as e:
        return False, _mensaje_duplicado(e, "una mesa")
    finally:
        conn.close()


def eliminar_mesa(id_mesa):
    """Elimina una mesa si no tiene reservas asociadas. Devuelve (True, None) o (False, error)."""
    conn = get_conexion()
    if conn is None:
        return False, "No hay conexion a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM mesas WHERE id_mesa = %s", (id_mesa,))
        conn.commit()
        cur.close()
        return True, None
    except Error as e:
        if getattr(e, "errno", None) == 1451:
            return False, "No se puede eliminar la mesa: tiene reservas asociadas."
        return False, str(e)
    finally:
        conn.close()


def recargar_catalogos():
    """Recarga las caches de mesas, mantenimiento y reservas desde la BD.

    Se usa despues de administrar areas/mesas para que el mapa, los combos y
    las disponibilidades reflejen inmediatamente los cambios.
    """
    global _mesas_mantenimiento
    MESAS[:] = _cargar_mesas()
    _mesas_mantenimiento = set(_cargar_mantenimiento())
    _recargar_reservas()


def conteo_mesas_por_estado():
    """Cuenta cuantas mesas hay en cada estado derivado."""
    conteo = {s: 0 for s in ESTADOS_MESA}
    for m in mesas_con_estado():
        if m["estado"] in conteo:
            conteo[m["estado"]] += 1
    return conteo


# ---------------------------------------------------------------------------
# CRUD de clientes (persistido en MySQL)
# ---------------------------------------------------------------------------
def crear_cliente(nombre, telefono, correo=""):
    """Inserta un cliente. Devuelve (True, id, None) o (False, None, error)."""
    conn = get_conexion()
    if conn is None:
        return False, None, "No hay conexion a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO clientes (nombre_completo, telefono, correo)
               VALUES (%s, %s, %s)""",
            (nombre, telefono, correo or None),
        )
        conn.commit()
        nid = cur.lastrowid
        cur.close()
        from datetime import date
        lista_clientes.append({
            "id": nid, "nombre": nombre, "telefono": telefono,
            "correo": correo, "registro": date.today().strftime("%d/%m/%Y"),
        })
        return True, nid, None
    except Error as e:
        return False, None, f"Error al guardar el cliente: {e}"
    finally:
        conn.close()


def actualizar_cliente(id_cliente, nombre, telefono, correo=""):
    """Actualiza un cliente. Devuelve bool."""
    conn = get_conexion()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute(
            """UPDATE clientes SET nombre_completo = %s, telefono = %s, correo = %s
               WHERE id_cliente = %s""",
            (nombre, telefono, correo or None, id_cliente),
        )
        conn.commit()
        cur.close()
        for c in lista_clientes:
            if c.get("id") == id_cliente:
                c["nombre"] = nombre
                c["telefono"] = telefono
                c["correo"] = correo
                break
        return True
    except Error:
        return False
    finally:
        conn.close()


def eliminar_cliente(id_cliente):
    """
    Elimina un cliente si no tiene reservas vinculadas. Si tiene reservas,
    se rechaza (devuelve False) para no dejar datos huerfanos.
    """
    conn = get_conexion()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM reservas WHERE id_cliente = %s", (id_cliente,))
        if cur.fetchone()[0] > 0:
            cur.close()
            return False
        cur.execute("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
        conn.commit()
        cur.close()
        global lista_clientes
        lista_clientes[:] = [c for c in lista_clientes if c.get("id") != id_cliente]
        return True
    except Error:
        return False
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CRUD de reservas (persistido en MySQL)
# ---------------------------------------------------------------------------
def _recargar_reservas():
    """Recarga la cache de reservas desde la BD, preservando la referencia
    de la lista (para que los paneles que la comparten vean los cambios)."""
    global lista_reservas
    nuevas = _cargar_reservas()
    lista_reservas[:] = nuevas


def crear_reserva(datos):
    """
    Crea una reserva a partir de un dict de la UI (obtener_datos del dialogo).
    datos: {id_cliente, mesa, fecha(dd/mm/yyyy), hora_inicio, hora_fin,
            personas, estado, observaciones, gestiono}
    Devuelve (True, id, None) o (False, None, error).
    """
    conn = get_conexion()
    if conn is None:
        return False, None, "No hay conexion a la base de datos."
    try:
        id_cliente = datos.get("id_cliente")
        if not _id_cliente_de(id_cliente):
            return False, None, "El cliente seleccionado no existe."
        id_mesa = _id_mesa_de(datos.get("mesa"))
        if id_mesa is None:
            return False, None, "La mesa seleccionada no existe."
        id_estado = _id_estado_reserva_de(datos.get("estado", ESTADO_PENDIENTE))
        id_usuario = _id_usuario_de(datos.get("gestiono", ""))
        fecha_bd = _ui_a_bd_fecha(datos.get("fecha", ""))
        hora_ini = datos.get("hora_inicio", "00:00") + ":00"
        hora_fin = datos.get("hora_fin", "00:00") + ":00"

        cur = conn.cursor()
        cur.execute(
            """INSERT INTO reservas
               (id_cliente, id_mesa, id_usuario, id_estado_reserva,
                fecha_reserva, hora_inicio, hora_fin, numero_personas, observaciones)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (id_cliente, id_mesa, id_usuario, id_estado, fecha_bd,
             hora_ini, hora_fin, int(datos.get("personas", 1)),
             datos.get("observaciones") or None),
        )
        conn.commit()
        nid = cur.lastrowid
        cur.close()
        _recargar_reservas()
        _sincronizar_estado_mesa_bd(datos.get("mesa"))
        return True, nid, None
    except Error as e:
        conn.rollback()
        return False, None, f"Error al guardar la reserva: {e}"
    except (ValueError, TypeError) as e:
        return False, None, f"Datos invalidos: {e}"
    finally:
        conn.close()


def actualizar_reserva(id_reserva, datos):
    """
    Actualiza una reserva existente. Devuelve (True, None) o (False, error).
    """
    conn = get_conexion()
    if conn is None:
        return False, "No hay conexion a la base de datos."
    try:
        id_cliente = datos.get("id_cliente")
        if not _id_cliente_de(id_cliente):
            return False, "El cliente seleccionado no existe."
        id_mesa = _id_mesa_de(datos.get("mesa"))
        if id_mesa is None:
            return False, "La mesa seleccionada no existe."
        id_estado = _id_estado_reserva_de(datos.get("estado", ESTADO_PENDIENTE))
        id_usuario = _id_usuario_de(datos.get("gestiono", ""))
        fecha_bd = _ui_a_bd_fecha(datos.get("fecha", ""))
        hora_ini = datos.get("hora_inicio", "00:00") + ":00"
        hora_fin = datos.get("hora_fin", "00:00") + ":00"

        cur = conn.cursor()
        # Estado actual de la reserva (para validar la transicion al editar)
        cur.execute(
            """SELECT er.nombre_estado, m.numero_mesa FROM reservas r
               JOIN estados_reserva er ON r.id_estado_reserva = er.id_estado_reserva
               JOIN mesas m ON r.id_mesa = m.id_mesa
               WHERE r.id_reserva = %s""",
            (id_reserva,),
        )
        f = cur.fetchone()
        if not f:
            cur.close()
            return False, "La reserva no existe."
        estado_actual = f[0]
        mesa_anterior = f[1]

        nuevo_estado = datos.get("estado", estado_actual)
        if nuevo_estado != estado_actual and not transicion_estado_valida(
            estado_actual, nuevo_estado
        ):
            cur.close()
            return False, (
                f"No se puede pasar la reserva de '{estado_actual}' a '{nuevo_estado}'. "
                f"Flujo valido: {TRANSICIONES_ESTADO.get(estado_actual, []) or 'estado terminal'}."
            )

        cur.execute(
            """UPDATE reservas
               SET id_cliente = %s, id_mesa = %s, id_usuario = %s,
                   id_estado_reserva = %s, fecha_reserva = %s,
                   hora_inicio = %s, hora_fin = %s, numero_personas = %s,
                   observaciones = %s
               WHERE id_reserva = %s""",
            (id_cliente, id_mesa, id_usuario, id_estado, fecha_bd,
             hora_ini, hora_fin, int(datos.get("personas", 1)),
             datos.get("observaciones") or None, id_reserva),
        )
        conn.commit()
        cur.close()
        _recargar_reservas()
        if mesa_anterior:
            _sincronizar_estado_mesa_bd(mesa_anterior)
        _sincronizar_estado_mesa_bd(datos.get("mesa"))
        return True, None
    except Error as e:
        conn.rollback()
        return False, f"Error al actualizar la reserva: {e}"
    except (ValueError, TypeError) as e:
        return False, f"Datos invalidos: {e}"
    finally:
        conn.close()


def cambiar_estado_reserva(id_reserva, nuevo_estado):
    """Cambia el estado de una reserva. Devuelve (True, None) o (False, error)."""
    conn = get_conexion()
    if conn is None:
        return False, "No hay conexion a la base de datos."
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT er.nombre_estado, m.numero_mesa
               FROM reservas r
               JOIN estados_reserva er ON r.id_estado_reserva = er.id_estado_reserva
               JOIN mesas m ON r.id_mesa = m.id_mesa
               WHERE r.id_reserva = %s""",
            (id_reserva,),
        )
        f = cur.fetchone()
        if not f:
            cur.close()
            return False, "La reserva no existe."
        estado_actual, numero_mesa = f

        if not transicion_estado_valida(estado_actual, nuevo_estado):
            cur.close()
            return False, (
                f"No se puede pasar la reserva de '{estado_actual}' a '{nuevo_estado}'. "
                f"Flujo valido: {TRANSICIONES_ESTADO.get(estado_actual, []) or 'estado terminal'}."
            )

        id_estado = _id_estado_reserva_de(nuevo_estado)
        if id_estado is None:
            cur.close()
            return False, f"El estado '{nuevo_estado}' no existe."

        cur.execute(
            "UPDATE reservas SET id_estado_reserva = %s WHERE id_reserva = %s",
            (id_estado, id_reserva),
        )
        conn.commit()
        cur.close()
        _recargar_reservas()
        if numero_mesa:
            _sincronizar_estado_mesa_bd(numero_mesa)
        return True, None
    except Error:
        return False, "Error al cambiar el estado de la reserva."
    finally:
        conn.close()


def eliminar_reserva(id_reserva):
    """Elimina permanentemente una reserva. Devuelve bool."""
    conn = get_conexion()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        # Mesa de la reserva antes de eliminarla (para re-sincronizar su estado)
        cur.execute(
            """SELECT m.numero_mesa FROM reservas r
               JOIN mesas m ON r.id_mesa = m.id_mesa
               WHERE r.id_reserva = %s""",
            (id_reserva,),
        )
        f = cur.fetchone()
        numero_mesa = f[0] if f else None

        cur.execute("DELETE FROM reservas WHERE id_reserva = %s", (id_reserva,))
        conn.commit()
        cur.close()
        _recargar_reservas()
        if numero_mesa:
            _sincronizar_estado_mesa_bd(numero_mesa)
        return True
    except Error:
        return False
    finally:
        conn.close()


def _reservas_lote_seleccion(estados=None, solo_pasadas=False):
    """IDs de reservas que coinciden con los criterios de limpieza en lote."""
    hoy = datetime.date.today()
    ids = []
    for r in lista_reservas:
        if estados and r.get("estado") not in estados:
            continue
        if solo_pasadas:
            try:
                partes = r["fecha"].split("/")
                fecha_r = datetime.date(
                    int(partes[2]), int(partes[1]), int(partes[0])
                )
            except (KeyError, ValueError, IndexError):
                continue
            if fecha_r >= hoy:
                continue
        ids.append(r["id"])
    return ids


def eliminar_reservas_en_lote(estados=None, solo_pasadas=False):
    """Elimina todas las reservas que coinciden con los criterios.

    Devuelve la cantidad de reservas eliminadas, o 0 si no hubo
    coincidencias o la operacion fallo.
    """
    ids = _reservas_lote_seleccion(estados, solo_pasadas)
    if not ids:
        return 0

    conn = get_conexion()
    if conn is None:
        return 0
    try:
        cur = conn.cursor()
        placeholders = ",".join(["%s"] * len(ids))
        cur.execute(
            f"SELECT DISTINCT m.numero_mesa FROM reservas r "
            f"JOIN mesas m ON r.id_mesa = m.id_mesa "
            f"WHERE r.id_reserva IN ({placeholders})",
            ids,
        )
        mesas_afectadas = [fila[0] for fila in cur.fetchall()]

        cur.execute(
            f"DELETE FROM reservas WHERE id_reserva IN ({placeholders})", ids
        )
        conn.commit()
        cur.close()
        _recargar_reservas()
        for numero in mesas_afectadas:
            _sincronizar_estado_mesa_bd(numero)
        return len(ids)
    except Error:
        return 0
    finally:
        conn.close()


def borrar_reservas_por_lotes(ids, tamanio_lote=20, pedir_parada=None,
                              on_progreso=None, retardo_lote=0.4):
    """Elimina reservas en lotes con una sola conexion (tarea pesada).

    - Cancela de forma cooperativa comprobando pedir_parada() entre lotes
      (Sesion 26: Stop Flag -> break, sin terminate()).
    - Notifica avance via on_progreso(hechas, total) despues de cada lote.
    - retardo_lote: pausa opcional por lote (segundos) para simular
      procesamiento pesado y hacer visible la concurrencia (guia 22-26).
    - NO muta la cache en memoria: devuelve las reservas frescas para que el
      hilo principal actualice lista_reservas en su propio contexto.

    Devuelve dict {eliminadas, mesas_afectadas, cancelado, nuevas_reservas}.
    Lanza RuntimeError si no hay conexion; relanza Error de MySQL.
    """
    conn = get_conexion()
    if conn is None:
        raise RuntimeError("No hay conexion a la base de datos.")
    ids = [int(i) for i in ids]
    total = len(ids)
    eliminadas = 0
    cancelado = False
    mesas_afectadas = []
    try:
        cur = conn.cursor()
        ph = ",".join(["%s"] * len(ids))
        cur.execute(
            "SELECT DISTINCT m.numero_mesa FROM reservas r "
            "JOIN mesas m ON r.id_mesa = m.id_mesa "
            f"WHERE r.id_reserva IN ({ph})", ids
        )
        mesas_afectadas = [fila[0] for fila in cur.fetchall()]

        for inicio in range(0, total, tamanio_lote):
            if pedir_parada is not None and pedir_parada():
                cancelado = True
                break
            lote = ids[inicio:inicio + tamanio_lote]
            lph = ",".join(["%s"] * len(lote))
            cur.execute(f"DELETE FROM reservas WHERE id_reserva IN ({lph})", lote)
            eliminadas += cur.rowcount
            conn.commit()
            if retardo_lote > 0:
                time.sleep(retardo_lote)
            if on_progreso is not None:
                on_progreso(min(inicio + len(lote), total), total)
        cur.close()
        nuevas_reservas = _cargar_reservas()
    except Error:
        conn.rollback()
        raise
    finally:
        conn.close()
    return {
        "eliminadas": eliminadas,
        "mesas_afectadas": mesas_afectadas,
        "cancelado": cancelado,
        "nuevas_reservas": nuevas_reservas,
    }


# ---------------------------------------------------------------------------
# Calculos para reportes (derivados de la cache lista_reservas)
# ---------------------------------------------------------------------------
def _reservas_en_periodo(periodo="Todos"):
    """Filtra lista_reservas segun el periodo: Hoy / Esta Semana / Este Mes / Todos."""
    fecha_hoy = datetime.date.today()

    def _fecha(r):
        try:
            d, m, y = r.get("fecha", "").split("/")
            return datetime.date(int(y), int(m), int(d))
        except (ValueError, AttributeError):
            return None

    def _en_periodo(r):
        if periodo == "Todos":
            return True
        f = _fecha(r)
        if f is None:
            return False
        if periodo == "Hoy":
            return f == fecha_hoy
        if periodo == "Esta Semana":
            inicio = fecha_hoy - datetime.timedelta(days=fecha_hoy.weekday())
            return inicio <= f <= inicio + datetime.timedelta(days=6)
        if periodo == "Este Mes":
            return f.year == fecha_hoy.year and f.month == fecha_hoy.month
        return True

    return [r for r in lista_reservas if _en_periodo(r)]


def reportes_dias(periodo="Todos"):
    """Reservas (no canceladas) por dia de la semana: Lunes..Domingo."""
    nombres = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
    conteo = {n: 0 for n in nombres}
    for r in _reservas_en_periodo(periodo):
        if r.get("estado") == ESTADO_CANCELADA:
            continue
        fecha = r.get("fecha", "")
        try:
            d, m, y = fecha.split("/")
            dia_semana = datetime.date(int(y), int(m), int(d)).weekday()
            conteo[nombres[dia_semana]] += 1
        except Exception:
            continue
    return conteo


def reportes_top_mesas(limite=7, periodo="Todos"):
    """Mesas mas solicitadas (no canceladas), ordenadas descendente."""
    conteo = {}
    for r in _reservas_en_periodo(periodo):
        if r.get("estado") == ESTADO_CANCELADA:
            continue
        mesa = r.get("mesa", "")
        if mesa:
            conteo[mesa] = conteo.get(mesa, 0) + 1
    ordenadas = sorted(conteo.items(), key=lambda kv: kv[1], reverse=True)
    return ordenadas[:limite]


def reportes_kpis(periodo="Todos"):
    """Indicadores clave derivados de las reservas."""
    reservas = _reservas_en_periodo(periodo)
    total = len(reservas)
    canceladas = sum(1 for r in reservas if r.get("estado") == ESTADO_CANCELADA)
    tasa = (canceladas / total * 100) if total else 0.0

    top = reportes_top_mesas(1, periodo)
    mesa_top = top[0][0] if top else "-"

    horas = {}
    for r in reservas:
        if r.get("estado") == ESTADO_CANCELADA:
            continue
        h = r.get("hora_inicio", "")
        if h:
            horas[h] = horas.get(h, 0) + 1
    horario_pico = max(horas, key=horas.get) if horas else "-"

    activas = sum(1 for r in reservas if r.get("estado") in (ESTADO_CONFIRMADA, ESTADO_PENDIENTE))
    ocupacion = (activas / len(MESAS) * 100) if MESAS else 0

    clientes_unicos = len({r.get("id_cliente") for r in reservas if r.get("id_cliente")})
    if clientes_unicos == 0:
        clientes_unicos = len({r.get("cliente") for r in reservas if r.get("cliente")})

    return {
        "reservas_semana": total,
        "tasa_cancelacion": round(tasa, 1),
        "mesa_top": mesa_top,
        "horario_pico": horario_pico,
        "ocupacion_promedio": round(ocupacion),
        "clientes_frecuentes": clientes_unicos,
    }
