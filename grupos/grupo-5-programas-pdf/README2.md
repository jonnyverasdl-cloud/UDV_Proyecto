# Grupo 5 · Programas de curso y PDF

El módulo publica `g5_programas.router` con rutas bajo `/api/v1`, y usa el
esquema MySQL 8 que instala el Grupo 1. No crea ni modifica tablas.

## Arranque

Desde la raíz del proyecto:

```sh
pip install -r requirements.txt
uvicorn main:app --reload --env-file .env
```

Configura `DATABASE_URL` en `.env` con las credenciales locales de Railway.
`DATABASE_URL` debe apuntar a una base creada con las migraciones y semillas
del Grupo 1. El módulo consume `programa_curso`, `programa_version`, las tablas
relacionales de secciones, `v_programa_versiones` y
`sp_autorizar_version`.

El módulo no interpreta roles enviados en el JSON. El middleware de
autenticación de G2 debe establecer el principal autenticado en
`request.state.user`, con `id` y `roles`; las operaciones protegidas rechazan
la solicitud si ese contexto no existe o no contiene el rol requerido. Cada
escritura establece `@actor_id` en la conexión para los triggers de G1.

## Pruebas

```sh
pytest -q
```

Las pruebas de dominio cubren las transiciones válidas e inválidas, la
inmutabilidad de versiones enviadas/autorizadas y el conflicto por más de una
versión autorizada. La base refuerza la inmutabilidad y unicidad mediante los
triggers y la restricción única de G1.

Los PDF solo se generan desde estados `authorized` o `superseded` (una
versión que ya fue autorizada y luego reemplazada). El documento incluye la
fecha y el registro de autorización que lo originó.
