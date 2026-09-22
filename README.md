# Synchrolia SGRT

Sistema de Gestion de Reservas para Restaurante (SGRT) desarrollado en Python con PySide6 (Qt) y MySQL. Proyecto integrador II - UNAN-Leon.

## Caracteristicas

- Gestion de reservas con flujo de estados: Pendiente -> Confirmada -> Completada (Cancelada y Completada son estados terminales).
- Busqueda de clientes y mesas con autocomplete.
- Mapa visual de mesas con estado en tiempo real (Libre / Ocupada / Reservada / Mantenimiento).
- Configuracion: horarios de atencion, limites de anticipacion por zona, depositos, festivos, usuarios y roles.
- Reportes PDF (KPIs, reservas por periodo, mesas mas solicitadas).
- Autenticacion de usuario con contrasena hasheada y roles (Administrador, Recepcionista).
- Dashboard con indicadores del dia.

## Estructura del proyecto

```
Synchrolia/
├── app.py                     # Punto de entrada de la aplicacion
├── conexion.py                # Capa de conexion a MySQL (clase ConexionBD)
├── estilos.py                 # QSS (tema visual) global
├── rutas.py                   # Rutas centralizadas a recursos y fuentes
├── Recursos/                  # Imagenes (logo, banners) y tipografias
├── Base de Datos/             # Esquema y datos semilla (restaurante_reservas.sql)
└── modulos/
    ├── almacen_datos.py       # Repositorio central: CRUD + cache en memoria
    ├── almacen_configuracion.py
    ├── almacen_usuarios.py
    ├── buscador_cliente.py    # Widget autocomplete (clientes y mesas)
    ├── clientes.py
    ├── configuracion.py
    ├── dashboard.py
    ├── dialogo_perfil.py
    ├── encabezado_modulo.py
    ├── fuentes.py
    ├── medidor.py
    ├── mesas.py
    ├── reportes.py
    ├── reservas.py
    ├── ventana_login.py
    └── ventana_principal.py
```

## Requisitos

- Python 3.10+
- MySQL 8.x
- PySide6, mysql-connector-python

Instalar dependencias:

```
pip install PySide6 mysql-connector-python
```

## Base de datos

1. Crear la base de datos e importar el esquema:

```sql
CREATE DATABASE restaurante_reservas;
```

Ejecutar `Base de Datos/restaurante_reservas.sql` sobre esa base.

2. Configurar las credenciales mediante variables de entorno (no se envian
   contrasenas por codigo):

```
SYNCHROLIA_DB_HOST=localhost
SYNCHROLIA_DB_PORT=3306
SYNCHROLIA_DB_USER=root
SYNCHROLIA_DB_PASSWORD=tu_contrasena
SYNCHROLIA_DB_NAME=restaurante_reservas
```

## Ejecucion

```
python app.py
```

## Notas

- Las capturas de pantalla, videos de demostracion y reportes generados no se
  incluyen en el repositorio (ver `.gitignore`).