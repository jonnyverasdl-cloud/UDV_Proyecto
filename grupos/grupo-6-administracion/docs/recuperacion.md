# Archivos persistentes y recuperación (G6-37 y G6-38)

Qué hay que respaldar, cómo volver a levantar el sistema si se pierde la base
o el servidor, y cómo comprobar que los archivos subidos sobreviven a un
reinicio. El procedimiento se probó completo el 28-oct-2026 (ver "Cómo se
probó" al final).

## Qué se respalda

| Qué | Dónde vive | Cómo se respalda |
|---|---|---|
| La base `db_udv` (datos, vistas, triggers y procedimientos del G1) | MySQL (Railway o local) | `mysqldump`, abajo |
| Archivos que suben los docentes | La carpeta del router de archivos del G2 | Copiar la carpeta |
| Configuración | Variables de entorno de Railway o `.env` | Anotarlas en un lugar seguro, **nunca** en el repositorio |
| El código | GitHub | La etiqueta de la versión (ver `version_final.md`) |

## 1. Respaldar la base

Con el usuario administrador de MySQL (el mismo con el que el G1 crea la base;
en Railway es el de las variables del servicio MySQL):

```bash
mysqldump -h HOST -P PUERTO -u USUARIO -p --single-transaction --routines --triggers --events --set-gtid-purged=OFF --databases db_udv > respaldo_db_udv_AAAA-MM-DD.sql
```

- `-p` sin nada pide la contraseña y no la deja en el historial.
- `--routines --triggers` son obligatorios: sin ellos se pierden los triggers
  del G1 que protegen la auditoría y crean los eventos de notificación.
- `--single-transaction` respalda sin detener el sistema.
- El archivo tiene datos personales (correos y nombres): se guarda fuera del
  repositorio, con acceso solo para el equipo.

## 2. Respaldar los archivos

La carpeta de archivos se copia tal cual, por ejemplo con
`tar -czf archivos_AAAA-MM-DD.tar.gz -C <carpeta> .`. Para saber cuál es la
carpeta, ver "Dónde guarda los archivos el G2" abajo.

## 3. Recuperar

1. **Base nueva y vacía.** En un MySQL 8 nuevo, sin crear `db_udv` (el
   respaldo la crea):

   ```bash
   mysql -h HOST -P PUERTO -u USUARIO -p < respaldo_db_udv_AAAA-MM-DD.sql
   ```

   Hay que usar el usuario administrador. Con un usuario sin privilegio
   `SUPER`, MySQL rechaza crear los triggers (`ERROR 1419 ... binary logging
   is enabled`) y la base quedaría sin sus protecciones.
2. **Archivos.** Descomprimir el respaldo en la carpeta de archivos.
3. **Configuración.** Apuntar `DATABASE_URL` a la base recuperada y volver a
   poner `SECRET_KEY` (si cambia, las sesiones abiertas se cierran y cada
   persona vuelve a entrar; no se pierde nada más).
4. **Levantar** la app (`uvicorn main:app` o volver a desplegar en Railway).

## 4. Comprobar que quedó bien

1. `GET /api/v1/health` responde `"status": "ok"` y `"database": "ok"`.
2. `GET /health/db` (de la raíz) dice 50 tablas.
3. La regresión pasa completa:

   ```bash
   cd grupos/grupo-6-administracion
   python -m g6_admin.regresion --url https://<direccion>
   ```

4. Si se respaldaron archivos: `python -m g6_admin.persistencia comprobar`
   (ver abajo) o descargar uno conocido.

## Archivos que sobreviven a un reinicio (G6-37)

En Docker y en Railway, todo lo que se escribe dentro del contenedor se borra
cuando el contenedor se vuelve a crear (cada despliegue en Railway, o
`docker compose up --build`). Solo sobrevive lo que está en un **volumen**.

**Cómo comprobarlo**, en el servidor donde corre la app (en Railway, con
`railway ssh`; con Docker, `docker compose exec api ...`):

```bash
python -m g6_admin.persistencia marcar      # deja una marca en la carpeta de archivos
# reiniciar o volver a desplegar el servicio
python -m g6_admin.persistencia comprobar   # ✓ si la marca sigue ahí; ✗ y código 1 si se perdió
```

La carpeta es la de `UPLOAD_DIR`, o `uploads` si no está definida. Se puede
revisar otra con `--dir`.

### Dónde guarda los archivos el G2 (hallazgo)

- `g2_api/config.py` lee `UPLOAD_DIR` (por defecto `almacen_archivos`), pero
  `g2_api/routers/files.py` no la usa: guarda siempre en `uploads/`, relativo
  a la carpeta desde donde se arranca la app (`/app/uploads` en el contenedor).
- El `docker-compose.yml` de la raíz solo tiene volumen para MySQL, y Railway
  no tiene volumen para la app. Hoy, cualquier archivo subido se perdería en
  el siguiente despliegue.
- El router de archivos todavía no está montado en `main.py` (pendiente G2-21),
  así que por ahora no hay archivos que perder.

**Pedidos** (no son archivos del G6):

| A quién | Qué |
|---|---|
| G2 | Que `files.py` guarde en `config.UPLOAD_DIR` en lugar de `uploads` fijo |
| PM | Un volumen para la app: en Railway, montado en `/data` con `UPLOAD_DIR=/data/archivos`; en `docker-compose.yml`, un volumen `archivos:/data/archivos` |

Mientras tanto, `python -m g6_admin.ambiente` marca como problema una
demostración sin `UPLOAD_DIR` absoluto.

## Cómo se probó

28-oct-2026, con MySQL 8.0 en Docker y la base del G1 de `main` (`3dc943c`):

| Paso | Resultado |
|---|---|
| `mysqldump` de `db_udv` con datos de prueba | 256 KB en menos de 1 s |
| Restaurar en un MySQL nuevo con un usuario sin `SUPER` | Falla con `ERROR 1419` (por eso el paso 3 pide el administrador) |
| Restaurar en el MySQL nuevo con el administrador | Termina en 2 s |
| Comparar original y restaurada | Iguales: 50 tablas, 7 vistas, 60 triggers, 4 rutinas, 156 registros de auditoría, 15 asignaciones, 8 usuarios |
| `UPDATE auditoria` en la restaurada | Rechazado por el trigger del G1: la protección se recuperó |
| API apuntando a la restaurada + `python -m g6_admin.regresion` | 24 de 24 casos pasan |
