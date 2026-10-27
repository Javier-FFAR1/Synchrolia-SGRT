# Synchrolia SGRT

Sistema de Gestion de Reservas para Restaurante (SGRT) desarrollado en Python con PySide6 (Qt), SQLAlchemy ORM y MySQL. Proyecto integrador II - UNAN-Leon.

## Caracteristicas

- Gestion de reservas con flujo de estados: Pendiente -> Confirmada -> Completada (Cancelada y Completada son estados terminales).
- Busqueda de clientes y mesas con autocomplete.
- Mapa visual de mesas con estado en tiempo real (Libre / Ocupada / Reservada / Mantenimiento).
- Configuracion: horarios de atencion, limites de anticipacion por zona, depositos, festivos, usuarios y roles.
- Reportes PDF (KPIs, reservas por periodo, mesas mas solicitadas).
- Exportacion a Excel con hoja resumen y detalle editable de reservas.
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

> El archivo `.env` esta en `.gitignore`: nunca subas tus credenciales al repositorio.

## Ejecucion

```
python app.py
```