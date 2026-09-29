# CONTRATO_COMUN.md — Reglas de integración para los 6 grupos

> **Nivel 2 de la jerarquía de fuentes de verdad** (ver README §0). Solo lo
> modifica el PM, con fecha y motivo en el historial. Este texto reemplaza a la
> tabla "Contrato común de integración" que aparece repetida en los seis .docx;
> si alguna copia del .docx difiere, gana este archivo.

Cualquier cambio a estas reglas se discute con el PM, se registra aquí y se
comunica a todos los grupos **antes** de modificar código.

## 1. Convenciones de la API

| Elemento | Convención |
|---|---|
| Base API | `/api/v1`. **Todas** las rutas de los CONTRATO.md llevan este prefijo aunque la tabla no lo repita: `/me` significa `/api/v1/me`. |
| Formato | JSON UTF-8; `multipart/form-data` solamente para archivos. |
| Autenticación | Token o sesión segura (la define el G2). `GET /api/v1/me` retorna usuario, roles y permisos. |
| Identificadores | Enteros o UUID, **un solo tipo para todo el sistema** (lo acuerdan G1 y G2, ver README §5). El mismo recurso conserva el mismo identificador en todos los módulos. |
| Fechas | ISO 8601. Zona horaria institucional: ver README §5. |
| Errores | `{"error": {"code": "VALIDATION_ERROR", "message": "...", "details": {}}}` — en 422, `details` trae el detalle **por campo**. |
| Códigos HTTP | 200, 201 y 204 éxito · 400 solicitud mal formada · 401 no autenticado · 403 sin permiso · 404 inexistente · 409 conflicto de estado · 422 validación. |
| Paginación | Respuesta con `page`, `per_page`, `total`, `data`. El máximo de `per_page` lo documenta el G2 en el OpenAPI. |
| Auditoría | Toda transición registra actor, fecha, estado anterior, estado nuevo y comentario. |
| OpenAPI | Se deriva de los CONTRATO.md y debe coincidir con lo que la API responde. No es una fuente de verdad propia: si difiere del contrato, el OpenAPI está mal. |

El formato de error, la paginación y el middleware los implementa el **G2**
como servicio compartido. Los demás grupos los importan; no los reimplementan.

## 2. Estados

**Tarea / asignación:** `draft`, `assigned`, `in_progress`, `submitted`,
`under_review`, `returned`, `approved`, `closed`, `cancelled`.
Las transiciones válidas son las de `grupos/grupo-3-workflow-tareas/CONTRATO.md`.

**Programa de curso (versión):** `draft`, `submitted`, `under_review`,
`returned`, `approved`, `authorized`, `superseded`.
Las transiciones válidas son las de `grupos/grupo-5-programas-pdf/CONTRATO.md`.

Los nombres de estado son exactamente estos, en inglés y en minúsculas, en la
base, en la API y en el código.

## 3. Eventos

Nombres oficiales de los eventos que alimentan las notificaciones: los define
la tabla de `grupos/grupo-6-administracion/CONTRATO.md` §3. El emisor de cada
evento es el módulo dueño de la acción; el mecanismo de transporte está
pendiente (README §5).

## 4. Repositorio

Ramas, PR y carpetas según el README §4 y §6. El .docx dice "ramas por
funcionalidad": eso se permite solo como sub-rama dentro del grupo
(`grupo-3/publicacion`) que se integra a `grupo-3`, nunca directo a `main`.
Las migraciones de base de datos se versionan (G1).

## 5. Definición de terminado (aplica a todos)

El trabajo está terminado cuando funciona desde la interfaz hasta la base de
datos, respeta este contrato común, valida permisos y errores, **tiene
pruebas**, **aparece en OpenAPI** cuando corresponde y puede instalarse
siguiendo el README. No se considera terminado un endpoint aislado, una
pantalla con datos fijos o una tabla sin integración.

Cada CONTRATO.md traduce esta definición a su checklist de PR.

---

## Historial de cambios

| Fecha | Cambio | Motivo |
|---|---|---|
| 2026-09-28 | Versión inicial, extraída del "Contrato común" de los .docx | La regla estaba solo dentro de binarios y no en ningún .md |
