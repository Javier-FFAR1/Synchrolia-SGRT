# -*- coding: utf-8 -*-
"""
Almacen de Usuarios (MySQL)
Capa central que gestiona los usuarios del sistema: registro, autenticacion,
edicion de perfil y eliminacion de cuenta.

Persiste en la tabla `usuarios` de MySQL (restaurante_reservas). Mantiene la
misma API publica que la version en memoria para que los paneles no cambien.
Las contrasenas se guardan como "salt$sha256(salt+contrasena)" (hex). Se
mantiene compatibilidad con los hashes SHA-256 planos creados por el script
SQL inicial: se verifican igual y se migran a salt en el primer login.
"""

import hashlib
import re
import secrets

from mysql.connector import Error

from conexion import get_conexion


def _generar_salt():
    """Genera un salt aleatorio de 16 bytes (32 caracteres hex)."""
    return secrets.token_hex(16)


def _hash_contrasena(contrasena, salt=None):
    """Genera 'salt$digest' con SHA-256(salt + contrasena). Si salt es None,
    genera uno nuevo aleatorio."""
    salt = salt or _generar_salt()
    digest = hashlib.sha256((salt + contrasena).encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def _verificar_contrasena(contrasena, hash_guardado):
    """Verifica una contrasena contra el hash almacenado.

    Acepta el formato actual "salt$digest" y el formato antiguo de SHA-256
    plano (64 hex) usado por el script SQL inicial.
    """
    if not hash_guardado:
        return False
    if "$" in hash_guardado:
        salt, digest = hash_guardado.split("$", 1)
        return hashlib.sha256(
            (salt + contrasena).encode("utf-8")
        ).hexdigest() == digest
    # Formato antiguo: SHA-256 plano
    return hashlib.sha256(contrasena.encode("utf-8")).hexdigest() == hash_guardado


LONGITUD_MIN_CONTRASENA = 6
LONGITUD_MAX_USUARIO = 50


def _usuario_archivado(nombre_usuario, id_usuario):
    """Genera un nombre unico para una cuenta desactivada."""
    sufijo = f"_eliminado_{id_usuario}"
    base = nombre_usuario[:LONGITUD_MAX_USUARIO - len(sufijo)]
    return f"{base}{sufijo}"


def _id_rol_de(nombre_rol):
    """Devuelve el id_rol asociado al nombre de rol, o None si no existe."""
    conn = get_conexion()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT id_rol FROM roles WHERE nombre_rol = %s", (nombre_rol,))
        fila = cur.fetchone()
        cur.close()
        return fila[0] if fila else None
    except Error:
        return None
    finally:
        conn.close()


def _nombre_rol_de(id_rol):
    """Devuelve el nombre de rol asociado a un id_rol, o None."""
    conn = get_conexion()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute("SELECT nombre_rol FROM roles WHERE id_rol = %s", (id_rol,))
        fila = cur.fetchone()
        cur.close()
        return fila[0] if fila else None
    except Error:
        return None
    finally:
        conn.close()


class AlmacenUsuarios:
    """Repositorio de usuarios persistido en MySQL."""

    def __init__(self):
        self.usuario_actual = None
        self._asegurar_usuarios_base()

    def _asegurar_usuarios_base(self):
        """
        Garantiza que existan las cuentas base (admin / recepcion1) si la BD
        fue creada sin los INSERT de usuarios. No sobreescribe si ya existen.
        """
        if not self.existe("admin"):
            self._insertar_usuario(
                "Admin General", "admin", "Administrador", "admin123"
            )
        if not self.existe("recepcion1"):
            self._insertar_usuario(
                "Recepcionista Uno", "recepcion1", "Recepcionista", "recepcion123"
            )

    def _insertar_usuario(self, nombre, usuario, rol, contrasena):
        conn = get_conexion()
        if conn is None:
            return False
        try:
            id_rol = _id_rol_de(rol)
            if id_rol is None:
                return False
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO usuarios
                   (nombre_completo, nombre_usuario, contrasena_hash, id_rol, activo)
                   VALUES (%s, %s, %s, %s, TRUE)""",
                (nombre, usuario, _hash_contrasena(contrasena), id_rol),
            )
            conn.commit()
            cur.close()
            return True
        except Error:
            return False
        finally:
            conn.close()

    # ---------- Consultas ----------

    def obtener(self, nombre_usuario):
        """Devuelve los datos de un usuario (sin hash) o None."""
        conn = get_conexion()
        if conn is None:
            return None
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT u.nombre_completo, u.nombre_usuario, r.nombre_rol, u.activo
                   FROM usuarios u
                   JOIN roles r ON u.id_rol = r.id_rol
                   WHERE u.nombre_usuario = %s""",
                (nombre_usuario,),
            )
            fila = cur.fetchone()
            cur.close()
            if fila is None:
                return None
            return {"nombre": fila[0], "usuario": fila[1], "rol": fila[2]}
        except Error:
            return None
        finally:
            conn.close()

    def todos(self):
        """Devuelve la lista de todos los usuarios activos (sin hash)."""
        conn = get_conexion()
        if conn is None:
            return []
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT u.nombre_completo, u.nombre_usuario, r.nombre_rol
                   FROM usuarios u
                   JOIN roles r ON u.id_rol = r.id_rol
                   WHERE u.activo = TRUE
                   ORDER BY u.nombre_usuario"""
            )
            filas = cur.fetchall()
            cur.close()
            return [
                {"nombre": f[0], "usuario": f[1], "rol": f[2]} for f in filas
            ]
        except Error:
            return []
        finally:
            conn.close()

    def existe(self, nombre_usuario):
        conn = get_conexion()
        if conn is None:
            return False
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM usuarios WHERE nombre_usuario = %s",
                (nombre_usuario,),
            )
            n = cur.fetchone()[0]
            cur.close()
            return n > 0
        except Error:
            return False
        finally:
            conn.close()

    # ---------- Autenticacion ----------

    def permisos_de(self, nombre_usuario):
        """
        Devuelve el conjunto de codigos de permiso del usuario (RBAC).
        Usa la vista vista_permisos_usuario de la BD. Si falla la conexion,
        devuelve un conjunto vacio (la UI decide como degradar).
        """
        conn = get_conexion()
        if conn is None:
            return set()
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT codigo_permiso
                   FROM vista_permisos_usuario
                   WHERE nombre_usuario = %s""",
                (nombre_usuario,),
            )
            permisos = {fila[0] for fila in cur.fetchall()}
            cur.close()
            return permisos
        except Error:
            return set()
        finally:
            conn.close()

    def verificar_login(self, usuario, contrasena):
        """
        Valida credenciales. Devuelve dict con nombre y rol si son correctas,
        o None si falla. Solo permite usuarios activos.
        """
        conn = get_conexion()
        if conn is None:
            return None
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT u.nombre_completo, u.nombre_usuario, r.nombre_rol, u.activo
                   FROM usuarios u
                   JOIN roles r ON u.id_rol = r.id_rol
                   WHERE u.nombre_usuario = %s""",
                (usuario.strip(),),
            )
            fila = cur.fetchone()
            cur.close()
            if fila is None:
                return None
            # Comparar hash contra el hash almacenado
            cur = conn.cursor()
            cur.execute(
                "SELECT contrasena_hash FROM usuarios WHERE nombre_usuario = %s",
                (usuario.strip(),),
            )
            hash_guardado = cur.fetchone()[0]
            cur.close()
            if not _verificar_contrasena(contrasena, hash_guardado):
                return None
            if not fila[3]:
                return None
            # Migrar el hash plano (script SQL) al formato con salt
            if "$" not in (hash_guardado or ""):
                cur = conn.cursor()
                cur.execute(
                    "UPDATE usuarios SET contrasena_hash = %s WHERE nombre_usuario = %s",
                    (_hash_contrasena(contrasena), usuario.strip()),
                )
                conn.commit()
                cur.close()
            self.usuario_actual = usuario.strip()
            return {"nombre": fila[0], "rol": fila[2]}
        except Error:
            return None
        finally:
            conn.close()

    # ---------- Gestion de cuentas ----------

    def registrar(self, nombre, usuario, rol, contrasena):
        """
        Registra un nuevo usuario.
        Devuelve (True, None) si se creo, o (False, mensaje_error) si falla.
        """
        nombre = nombre.strip()
        usuario = usuario.strip()
        if not nombre or not usuario or not contrasena:
            return False, "Debe completar todos los campos."
        if len(nombre) > 100:
            return False, "El nombre completo no puede superar 100 caracteres."
        if len(usuario) > LONGITUD_MAX_USUARIO:
            return False, (
                f"El nombre de usuario no puede superar "
                f"{LONGITUD_MAX_USUARIO} caracteres."
            )
        if self.existe(usuario):
            return False, f"El usuario '{usuario}' ya existe."
        if not re.match(r"^[A-Za-z0-9_.-]+$", usuario):
            return False, (
                "El nombre de usuario solo puede contener letras, números, "
                "puntos, guiones y guiones bajos (sin espacios)."
            )
        if len(contrasena) < LONGITUD_MIN_CONTRASENA:
            return False, (
                f"La contraseña debe tener al menos "
                f"{LONGITUD_MIN_CONTRASENA} caracteres."
            )
        if self._insertar_usuario(nombre, usuario, rol, contrasena):
            return True, None
        return False, "No fue posible registrar el usuario en la base de datos."

    def editar_nombre(self, nombre_usuario, nuevo_nombre):
        """Actualiza el nombre completo de un usuario. Devuelve bool."""
        nuevo_nombre = nuevo_nombre.strip()
        if not nuevo_nombre or len(nuevo_nombre) > 100:
            return False
        conn = get_conexion()
        if conn is None:
            return False
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE usuarios SET nombre_completo = %s WHERE nombre_usuario = %s",
                (nuevo_nombre.strip(), nombre_usuario),
            )
            conn.commit()
            ok = cur.rowcount > 0
            cur.close()
            return ok
        except Error:
            return False
        finally:
            conn.close()

    def cambiar_contrasena(self, nombre_usuario, contrasena_actual, nueva_contrasena):
        """
        Cambia la contrasena verificando la actual.
        Devuelve (True, None) o (False, mensaje_error).
        """
        conn = get_conexion()
        if conn is None:
            return False, "No hay conexión a la base de datos."
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT contrasena_hash FROM usuarios WHERE nombre_usuario = %s",
                (nombre_usuario,),
            )
            fila = cur.fetchone()
            cur.close()
            if fila is None:
                return False, "Usuario no encontrado."
            if not _verificar_contrasena(contrasena_actual, fila[0]):
                return False, "La contraseña actual es incorrecta."
            if not nueva_contrasena:
                return False, "La nueva contraseña no puede estar vacía."
            if len(nueva_contrasena) < LONGITUD_MIN_CONTRASENA:
                return False, (
                    f"La contraseña debe tener al menos "
                    f"{LONGITUD_MIN_CONTRASENA} caracteres."
                )
            cur = conn.cursor()
            cur.execute(
                "UPDATE usuarios SET contrasena_hash = %s WHERE nombre_usuario = %s",
                (_hash_contrasena(nueva_contrasena), nombre_usuario),
            )
            conn.commit()
            cur.close()
            return True, None
        except Error as e:
            return False, f"Error al cambiar la contraseña: {e}"
        finally:
            conn.close()

    def es_ultimo_admin(self, nombre_usuario):
        """Indica si el usuario es el unico administrador activo del sistema."""
        conn = get_conexion()
        if conn is None:
            return False
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT r.nombre_rol, u.activo
                   FROM usuarios u
                   JOIN roles r ON u.id_rol = r.id_rol
                   WHERE u.nombre_usuario = %s""",
                (nombre_usuario,),
            )
            fila = cur.fetchone()
            if not fila or fila[0] != "Administrador" or not fila[1]:
                cur.close()
                return False
            cur.execute(
                """SELECT COUNT(*)
                   FROM usuarios u
                   JOIN roles r ON u.id_rol = r.id_rol
                   WHERE r.nombre_rol = 'Administrador'
                     AND u.activo = TRUE"""
            )
            total = cur.fetchone()[0]
            cur.close()
            return total <= 1
        except Error:
            return False
        finally:
            conn.close()

    def eliminar(self, nombre_usuario):
        """
        Elimina la cuenta de un usuario. Devuelve bool.

        Con MySQL, si el usuario tiene reservas o auditoria vinculada, la FK
        impide el borrado fisico; en ese caso se desactiva (activo = FALSE) y
        se renombra la cuenta para liberar el nombre de usuario. Si no tiene
        vinculos, se borra.
        """
        if self.es_ultimo_admin(nombre_usuario):
            return False
        conn = get_conexion()
        if conn is None:
            return False
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id_usuario FROM usuarios WHERE nombre_usuario = %s",
                (nombre_usuario,),
            )
            fila = cur.fetchone()
            if fila is None:
                cur.close()
                return False
            id_usuario = fila[0]

            # ¿Tiene reservas o historial vinculado?
            cur.execute(
                "SELECT COUNT(*) FROM reservas WHERE id_usuario = %s",
                (id_usuario,),
            )
            reservas = cur.fetchone()[0]
            if reservas == 0:
                cur.execute(
                    "SELECT COUNT(*) FROM historial_reservas WHERE id_usuario = %s",
                    (id_usuario,),
                )
                reservas = cur.fetchone()[0]

            if reservas > 0:
                # Desactivar (logico) y liberar el nombre de usuario
                cur.execute(
                    """UPDATE usuarios
                       SET activo = FALSE, nombre_usuario = %s
                       WHERE id_usuario = %s""",
                    (_usuario_archivado(nombre_usuario, id_usuario), id_usuario),
                )
            else:
                cur.execute(
                    "DELETE FROM usuarios WHERE id_usuario = %s", (id_usuario,)
                )
            conn.commit()
            cur.close()

            if self.usuario_actual == nombre_usuario:
                self.usuario_actual = None
            return True
        except Error:
            return False
        finally:
            conn.close()


# Punto de acceso global compartido por toda la aplicacion
almacen = AlmacenUsuarios()
