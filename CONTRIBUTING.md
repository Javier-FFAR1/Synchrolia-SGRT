# Guia de contribucion - Synchrolia SGRT

Gracias por colaborar en el proyecto. Para mantener el repositorio ordenado,
sigue estas convenciones.

## Requisitos previos

- Git con tu nombre y correo configurados:
  ```
  git config --global user.name "Tu Nombre"
  git config --global user.email "tu-correo@ejemplo.com"
  ```
- Python 3.10+ y las dependencias instaladas (`pip install -r requirements.txt`).

## Flujo de trabajo

1. Actualiza `main` antes de empezar:
   ```
   git checkout main
   git pull origin main
   ```
2. Crea una rama para tu tarea (nunca trabajes directo en `main`):
   ```
   git checkout -b feat/limpiar-reservas-lote
   ```
3. Realiza commits pequenos y frecuentes (ver convencion abajo).
4. Sube tu rama:
   ```
   git push -u origin feat/limpiar-reservas-lote
   ```
5. Abre un **Pull Request** hacia `main`, pide revision a un companero y
   espera la aprobacion antes de mergear.

## Nombres de ramas

Usa un prefijo segun el tipo de cambio:

- `feat/`  nueva funcionalidad (ej. `feat/reportes-pdf`)
- `fix/`   correccion de errores (ej. `fix/validar-telefono`)
- `docs/`  documentacion
- `refactor/`  mejora de codigo sin cambiar comportamiento
- `chore/` tareas de mantenimiento (config, dependencias)

## Mensajes de commit (Conventional Commits)

Formato: `tipo: descripcion corta en imperativo`

- `feat: agregar limpieza de reservas en lote con hilo`
- `fix: corregir validacion de telefono`
- `docs: actualizar instrucciones del README`
- `style: ajustar espaciado del dashboard`
- `refactor: extraer consultas a almacen_datos`
- `chore: agregar requirements.txt`

Reglas:

- Un commit = un cambio logico. Evita commits gigantes.
- Descripcion en minuscula, sin punto final.
- Si el commit cierra un issue: `fix: ... (closes #12)`.

## Pull Requests

- Titulo claro y descripcion de que cambia y por que.
- Cambios pequenos y enfocados (facilita la revision).
- No mergear con conflictos sin resolver.
- Pide una revision a otro integrante antes de mergear.

## Reglas importantes

- **Nunca subas el archivo `.env`** ni credenciales. Ya esta en `.gitignore`.
- No subas `__pycache__/`, entornos virtuales ni la carpeta `Reportes/`.
- Manten el estilo del codigo existente (sin cambios masivos no relacionados).
- Actualiza tu rama con `main` periodicamente para evitar conflictos:
  ```
  git checkout main && git pull
  git checkout feat/tu-rama && git merge main
  ```

## Antes de pedir revision

- La aplicacion debe ejecutar sin errores (`python app.py`).
- Si aplica, verifica los archivos no rastreados con `git status`.
