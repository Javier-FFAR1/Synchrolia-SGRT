# Synchrolia SGRT

Sistema de Gestion de Reservas para Restaurante (SGRT) desarrollado en Python con PySide6 (Qt), SQLAlchemy ORM y MySQL. Proyecto integrador II - UNAN-Leon.

## Caracteristicas

- Gestion de reservas con flujo de estados: Pendiente -> Confirmada -> Completada (Cancelada y Completada son estados terminales).
- Busqueda de clientes y mesas con autocomplete.
- Mapa visual de mesas con estado en tiempo real (Libre / Ocupada / Reservada / Mantenimiento).
- Configuracion: horarios de atencion, limites de anticipacion por zona, depositos, festivos, usuarios y roles.
- Reportes PDF (KPIs, reservas por periodo, mesas mas solicitadas).
- Exportacion a Excel con hoja resumen y detalle editable de reservas.
- Cliente REST/JSON configurable, listo para integrar la app con un servidor externo.
- Autenticacion de usuario con contrasena hasheada y roles (Administrador, Recepcionista).
- Dashboard con indicadores del dia.

## Estructura del proyecto

```
Synchrolia/
├── app.py                     # Punto de entrada de la aplicacion
├── conexion.py                # Conexion nativa a MySQL (clase ConexionBD)
├── database.py                # Engine y SessionLocal de SQLAlchemy
├── models.py                  # Modelos ORM (tablas y relaciones)
├── repository.py              # Repositorio ORM de festivos y reservas
├── report_metrics.py          # KPIs compartidos por PDF y Excel
├── report_generator.py        # Reporte PDF con Flowables (ReportLab)
├── excel_exporter.py          # Exportacion Excel con openpyxl
├── api_client.py              # Cliente REST/JSON configurable (requests)
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
- Git

## Instalacion para el equipo

1. Clonar el repositorio:

```
git clone https://github.com/Javier-FFAR1/Synchrolia-SGRT.git
cd Synchrolia-SGRT
```

2. Crear y activar un entorno virtual:

```
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS
```

3. Instalar dependencias:

```
pip install -r requirements.txt
```

## Base de datos

1. Crear la base de datos e importar el esquema:

```sql
CREATE DATABASE restaurante_reservas;
```

Ejecutar `Base de Datos/restaurante_reservas.sql` sobre esa base.

2. Crear un archivo `.env` en la raiz del proyecto con los datos de acceso a MySQL:

```
SYNCHROLIA_DB_HOST=localhost
SYNCHROLIA_DB_PORT=3306
SYNCHROLIA_DB_USER=root
SYNCHROLIA_DB_PASSWORD=tu_contrasena
SYNCHROLIA_DB_NAME=restaurante_reservas
```

Para enviar confirmaciones y recordatorios por correo, agregue tambien la
configuracion SMTP de Gmail. Use una contrasena de aplicacion, no la
contrasena normal de la cuenta:

```
SYNCHROLIA_SMTP_HOST=smtp.gmail.com
SYNCHROLIA_SMTP_PORT=587
SYNCHROLIA_SMTP_USER=tu_correo@gmail.com
SYNCHROLIA_SMTP_PASSWORD=tu_contrasena_de_aplicacion
SYNCHROLIA_SMTP_FROM=tu_correo@gmail.com
```

> Despues de editar `.env`, reinicie la aplicacion. Los recordatorios se
> envian mientras Synchrolia este abierta.

> El archivo `.env` esta en `.gitignore`: nunca subas tus credenciales al repositorio.

## Ejecucion

```
python app.py
```

## Cliente API REST (opcional)

`api_client.py` implementa el lado cliente de una API REST/JSON y no
depende de un servidor concreto. La URL base se configura en `.env`:

```
SYNCHROLIA_API_URL=http://127.0.0.1:8000/api
```

Si no se define, se usa `http://127.0.0.1:8000/api`. Ejemplo de uso:

```python
from api_client import ReservasApi

api = ReservasApi()
api.listar(periodo="Hoy")
api.obtener(1)
api.crear({"id_cliente": 1, "id_mesa": 3, "fecha_reserva": "2026-10-26"})
api.actualizar(1, {"estado": "Confirmada"})
api.actualizar_parcial(1, {"numero_personas": 4})
api.eliminar(1)
api.cerrar()
```

Endpoints esperados del servidor:

- `GET /reservas?periodo=...`
- `GET /reservas/{id}`
- `POST /reservas`
- `PUT /reservas/{id}`
- `PATCH /reservas/{id}`
- `DELETE /reservas/{id}`

Los errores HTTP se reportan con `ApiError` (codigo y datos) y los fallos
de conexion o timeout con `ApiNoDisponibleError`.