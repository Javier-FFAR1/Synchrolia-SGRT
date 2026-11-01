# -*- coding: utf-8 -*-
"""
Modulo: Notificaciones
Envio de correos de confirmacion y recordatorio mediante SMTP.

Las credenciales se leen de .env y nunca se guardan en la base de datos ni
en el repositorio. El registro de envios evita duplicados entre reinicios.
"""

import datetime
import html
import os
import smtplib
import ssl
import threading
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

from conexion import get_conexion
from modulos.almacen_configuracion import almacen_config


_NOMBRE_REMITENTE = "Synchrolia SGRT"
_TIMEOUT_SMTP = 20
_BANNER_EMAIL = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "Recursos",
    "Synchrolia_banner_email_600x120@2x.jpg",
)
_TABLA_ASEGURADA = False
_LOCK = threading.Lock()
_EN_VUELO = set()

_ESTADOS_RECORDATORIO = ("Confirmada",)

_SQL_TABLA_NOTIFICACIONES = """
CREATE TABLE IF NOT EXISTS notificaciones_enviadas (
    id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_reserva INT NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    correo VARCHAR(100) NOT NULL,
    enviado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_notificacion_reserva (id_reserva, tipo),
    CONSTRAINT fk_notificacion_reserva
        FOREIGN KEY (id_reserva) REFERENCES reservas(id_reserva)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def _valor_env(clave, defecto=""):
    return str(os.environ.get(clave, defecto) or "").strip()


def configuracion_smtp():
    """Devuelve la configuracion SMTP cargada desde el entorno."""
    try:
        puerto = int(_valor_env("SYNCHROLIA_SMTP_PORT", "587"))
    except ValueError:
        puerto = 587
    usuario = _valor_env("SYNCHROLIA_SMTP_USER")
    return {
        "host": _valor_env("SYNCHROLIA_SMTP_HOST", "smtp.gmail.com"),
        "puerto": puerto,
        "usuario": usuario,
        "password": _valor_env("SYNCHROLIA_SMTP_PASSWORD"),
        "remitente": _valor_env("SYNCHROLIA_SMTP_FROM") or usuario,
    }


def estado_configuracion():
    """Indica si SMTP esta listo y devuelve un mensaje para la interfaz."""
    cfg = configuracion_smtp()
    if not cfg["host"] or not cfg["usuario"] or not cfg["password"]:
        return False, (
            "SMTP no configurado. Complete SYNCHROLIA_SMTP_USER y "
            "SYNCHROLIA_SMTP_PASSWORD en .env."
        )
    return True, f"SMTP configurado: {cfg['usuario']}"


def _parametro_activo(clave, defecto=False):
    try:
        parametros = almacen_config.obtener_parametros()
    except Exception:
        return defecto
    return bool(parametros.get(clave, defecto))


def _cuerpo_html(cuerpo, cid=None):
    contenido = "<br>".join(
        html.escape(linea) for linea in str(cuerpo).splitlines()
    )
    if cid:
        cabecera = (
            f'<img src="cid:{cid}" alt="Synchrolia SGRT" width="600" height="120" '
            'style="display:block;width:100%;max-width:600px;height:auto;border:0;'
            'background:#1B3A5C;color:#FFFFFF;font-size:22px;font-weight:bold;">'
        )
    else:
        cabecera = (
            '<div style="background:#1B3A5C;color:#FFFFFF;padding:24px 32px;'
            'font-size:22px;font-weight:bold;">Synchrolia SGRT</div>'
        )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#F5F7FA;font-family:Arial,Helvetica,sans-serif;color:#1F2937;">
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#F5F7FA;">
<tr>
<td align="center" style="padding:24px 12px;">
<table role="presentation" width="600" cellspacing="0" cellpadding="0" style="width:100%;max-width:600px;background:#FFFFFF;border-radius:12px;overflow:hidden;">
<tr><td>{cabecera}</td></tr>
<tr><td style="padding:28px 32px;font-size:15px;line-height:1.6;color:#1F2937;">{contenido}</td></tr>
<tr><td style="background:#1B3A5C;color:#FFFFFF;padding:16px 32px;font-size:12px;line-height:1.5;">Synchrolia SGRT<br>Este mensaje fue enviado automáticamente.</td></tr>
</table>
</td>
</tr>
</table>
</body>
</html>"""


def _crear_mensaje(destinatario, asunto, cuerpo):
    cfg = configuracion_smtp()
    dominio = cfg["remitente"].rsplit("@", 1)[-1].strip()
    mensaje = MIMEMultipart("related", type="multipart/alternative")
    mensaje["Subject"] = asunto
    mensaje["From"] = formataddr((_NOMBRE_REMITENTE, cfg["remitente"]))
    mensaje["Reply-To"] = formataddr((_NOMBRE_REMITENTE, cfg["remitente"]))
    mensaje["To"] = destinatario
    mensaje["Date"] = formatdate(localtime=True)
    mensaje["Message-ID"] = make_msgid(domain=dominio) if dominio else make_msgid()
    mensaje["Auto-Submitted"] = "auto-generated"
    mensaje["X-Auto-Response-Suppress"] = "All"
    mensaje["Content-Language"] = "es"

    cid = None
    imagen = None
    if os.path.isfile(_BANNER_EMAIL):
        cid = "banner-synchrolia"
        try:
            with open(_BANNER_EMAIL, "rb") as archivo:
                imagen = MIMEImage(archivo.read(), _subtype="jpeg")
            imagen.set_param("name", "banner_synchrolia.jpg")
            imagen.add_header("Content-ID", f"<{cid}>")
            imagen.add_header(
                "Content-Disposition", "inline",
                filename="banner_synchrolia.jpg",
            )
            imagen.add_header("X-Attachment-Id", cid)
        except OSError:
            cid = None
            imagen = None

    alternativo = MIMEMultipart("alternative")
    alternativo.attach(MIMEText(cuerpo, "plain", "utf-8"))
    alternativo.attach(MIMEText(_cuerpo_html(cuerpo, cid), "html", "utf-8"))
    mensaje.attach(alternativo)
    if imagen is not None:
        mensaje.attach(imagen)
    return mensaje


def _enviar(destinatario, asunto, cuerpo):
    cfg = configuracion_smtp()
    if not cfg["host"] or not cfg["usuario"] or not cfg["password"]:
        return False, "SMTP no configurado."

    password = cfg["password"]
    if cfg["host"].lower() == "smtp.gmail.com":
        password = "".join(password.split())
        if len(password) != 16:
            return False, (
                "La contraseña SMTP de Gmail debe ser una contraseña de "
                "aplicación de 16 caracteres. No use la contraseña normal "
                "de la cuenta."
            )

    mensaje = _crear_mensaje(destinatario, asunto, cuerpo)
    contexto = ssl.create_default_context()
    try:
        if cfg["puerto"] == 465:
            with smtplib.SMTP_SSL(
                cfg["host"], cfg["puerto"],
                timeout=_TIMEOUT_SMTP, context=contexto,
            ) as smtp:
                smtp.login(cfg["usuario"], password)
                smtp.send_message(mensaje)
        else:
            with smtplib.SMTP(
                cfg["host"], cfg["puerto"], timeout=_TIMEOUT_SMTP,
            ) as smtp:
                smtp.ehlo()
                smtp.starttls(context=contexto)
                smtp.ehlo()
                smtp.login(cfg["usuario"], password)
                smtp.send_message(mensaje)
        return True, None
    except smtplib.SMTPAuthenticationError:
        return False, (
            "Gmail rechazó el usuario o la contraseña. Verifique que sea una "
            "contraseña de aplicación de 16 caracteres y que la verificación "
            "en dos pasos esté activa."
        )
    except smtplib.SMTPServerDisconnected:
        return False, (
            "Gmail cerró la conexión. Verifique la contraseña de aplicación, "
            "la conexión a Internet y que el puerto sea 587 o 465."
        )
    except Exception as error:
        return False, str(error)


def _asegurar_tabla(conn):
    global _TABLA_ASEGURADA
    if _TABLA_ASEGURADA:
        return True
    try:
        cur = conn.cursor()
        cur.execute(_SQL_TABLA_NOTIFICACIONES)
        conn.commit()
        cur.close()
        _TABLA_ASEGURADA = True
        return True
    except Exception:
        return False


def _ya_enviada(id_reserva, tipo):
    conn = get_conexion()
    if conn is None:
        return False
    try:
        if not _asegurar_tabla(conn):
            return False
        cur = conn.cursor()
        cur.execute(
            """SELECT 1 FROM notificaciones_enviadas
               WHERE id_reserva = %s AND tipo = %s""",
            (id_reserva, tipo),
        )
        enviada = cur.fetchone() is not None
        cur.close()
        return enviada
    except Exception:
        return False
    finally:
        conn.close()


def _marcar_enviada(id_reserva, tipo, correo):
    conn = get_conexion()
    if conn is None:
        return False
    try:
        if not _asegurar_tabla(conn):
            return False
        cur = conn.cursor()
        cur.execute(
            """INSERT IGNORE INTO notificaciones_enviadas
               (id_reserva, tipo, correo) VALUES (%s, %s, %s)""",
            (id_reserva, tipo, correo),
        )
        conn.commit()
        cur.close()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def _reclamar(id_reserva, tipo):
    clave = (int(id_reserva), tipo)
    with _LOCK:
        if clave in _EN_VUELO:
            return False
        _EN_VUELO.add(clave)
        return True


def _liberar(id_reserva, tipo):
    clave = (int(id_reserva), tipo)
    with _LOCK:
        _EN_VUELO.discard(clave)


def _inicio_reserva(reserva):
    try:
        return datetime.datetime.strptime(
            f"{reserva['fecha']} {reserva['hora_inicio']}",
            "%d/%m/%Y %H:%M",
        )
    except (KeyError, TypeError, ValueError):
        return None


def _asunto_confirmacion(reserva):
    if str(reserva.get("estado") or "") == "Confirmada":
        return f"Reserva confirmada #{reserva.get('id')} - Synchrolia SGRT"
    return f"Reserva registrada #{reserva.get('id')} - Synchrolia SGRT"


def _cuerpo_confirmacion(reserva):
    estado = str(reserva.get("estado") or "")
    if estado == "Confirmada":
        introduccion = "Su reserva ha sido confirmada."
    else:
        introduccion = "Hemos registrado su reserva correctamente."

    lineas = [
        f"Estimado(a) {reserva.get('cliente', 'cliente')}:",
        "",
        "Gracias por elegir Synchrolia SGRT.",
        introduccion,
        "",
        f"Reserva: #{reserva.get('id')}",
        f"Fecha: {reserva.get('fecha', '')}",
        f"Hora: {reserva.get('hora_inicio', '')} - {reserva.get('hora_fin', '')}",
        f"Mesa: {reserva.get('mesa', '')}",
        f"Personas: {reserva.get('personas', '')}",
        f"Estado: {estado}",
    ]
    observaciones = str(reserva.get("observaciones") or "").strip()
    if observaciones:
        lineas.append(f"Observaciones: {observaciones}")
    lineas.extend([
        "",
        "Si necesita modificar o cancelar su reserva, comuníquese con nosotros.",
        "",
        "Le esperamos.",
        "",
        "Synchrolia SGRT",
    ])
    return "\n".join(lineas)


def _cuerpo_recordatorio(reserva):
    lineas = [
        f"Estimado(a) {reserva.get('cliente', 'cliente')}:",
        "",
        "Le recordamos que su reserva en Synchrolia SGRT está programada "
        "para dentro de una hora.",
        "",
        f"Reserva: #{reserva.get('id')}",
        f"Fecha: {reserva.get('fecha', '')}",
        f"Hora: {reserva.get('hora_inicio', '')} - {reserva.get('hora_fin', '')}",
        f"Mesa: {reserva.get('mesa', '')}",
        f"Personas: {reserva.get('personas', '')}",
        "",
        "Le esperamos. Si no puede asistir, le agradecemos avisarnos con "
        "anticipación.",
        "",
        "Synchrolia SGRT",
    ]
    return "\n".join(lineas)


def _enviar_reserva(reserva, tipo, asunto, cuerpo):
    if not reserva or not reserva.get("id"):
        return False, "Reserva inválida."
    correo = str(reserva.get("correo") or "").strip()
    if not correo:
        return False, "El cliente no tiene correo registrado."
    if _ya_enviada(reserva["id"], tipo):
        return False, "La notificación ya fue enviada."
    if not _reclamar(reserva["id"], tipo):
        return False, "La notificación se está enviando."

    try:
        ok, error = _enviar(correo, asunto, cuerpo)
        if ok:
            _marcar_enviada(reserva["id"], tipo, correo)
        return ok, error
    finally:
        _liberar(reserva["id"], tipo)


def enviar_confirmacion(reserva):
    """Envia la confirmacion de una reserva si la opcion esta activa."""
    if not _parametro_activo("email_notif", True):
        return False, "Las confirmaciones por correo están desactivadas."
    return _enviar_reserva(
        reserva,
        "confirmacion",
        _asunto_confirmacion(reserva),
        _cuerpo_confirmacion(reserva),
    )


def enviar_confirmacion_estado(reserva):
    """Envia el aviso cuando una reserva pasa a Confirmada."""
    if not _parametro_activo("email_notif", True):
        return False, "Las confirmaciones por correo est\u00e1n desactivadas."
    return _enviar_reserva(
        reserva,
        "confirmada",
        _asunto_confirmacion(reserva),
        _cuerpo_confirmacion(reserva),
    )


def enviar_recordatorio(reserva):
    """Envia el recordatorio de una reserva si la opcion esta activa."""
    if not _parametro_activo("recordatorio", False):
        return False, "Los recordatorios por correo están desactivados."
    return _enviar_reserva(
        reserva,
        "recordatorio",
        f"Recordatorio de reserva #{reserva.get('id')} - Synchrolia",
        _cuerpo_recordatorio(reserva),
    )


def enviar_confirmacion_async(reserva):
    hilo = threading.Thread(
        target=enviar_confirmacion, args=(reserva,), daemon=True,
    )
    hilo.start()
    return hilo


def enviar_confirmacion_estado_async(reserva):
    hilo = threading.Thread(
        target=enviar_confirmacion_estado, args=(reserva,), daemon=True,
    )
    hilo.start()
    return hilo


def enviar_recordatorio_async(reserva):
    hilo = threading.Thread(
        target=enviar_recordatorio, args=(reserva,), daemon=True,
    )
    hilo.start()
    return hilo


def procesar_recordatorios(reservas, ahora=None):
    """Envia recordatorios para reservas que inician dentro de una hora."""
    if not _parametro_activo("recordatorio", False):
        return 0
    ahora = ahora or datetime.datetime.now()
    enviados = 0
    for reserva in reservas or []:
        if reserva.get("estado") not in _ESTADOS_RECORDATORIO:
            continue
        if not str(reserva.get("correo") or "").strip():
            continue
        inicio = _inicio_reserva(reserva)
        if inicio is None:
            continue
        diferencia = inicio - ahora
        if datetime.timedelta(0) <= diferencia <= datetime.timedelta(hours=1):
            if _ya_enviada(reserva["id"], "recordatorio"):
                continue
            enviar_recordatorio_async(reserva)
            enviados += 1
    return enviados


def enviar_prueba(destinatario=None):
    """Envia un correo de prueba al usuario SMTP configurado."""
    cfg = configuracion_smtp()
    destino = str(destinatario or cfg["usuario"] or "").strip()
    if not destino:
        return False, "Defina SYNCHROLIA_SMTP_USER en .env."
    cuerpo = (
        "Este es un correo de prueba de Synchrolia SGRT.\n\n"
        "Si lo recibió, la configuración SMTP funciona correctamente."
    )
    return _enviar(destino, "Prueba de notificaciones - Synchrolia", cuerpo)
