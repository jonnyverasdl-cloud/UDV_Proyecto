# CONTRATO.md — Grupo 2 · API base y seguridad

> **Nivel 3 de la jerarquía de fuentes de verdad** (README §0). Por encima:
> README y CONTRATO_COMUN.md. Por debajo: el .docx de esta carpeta. Si el
> .docx y este contrato se contradicen, gana este contrato; lo que el .docx
> exige y aquí no aparece sigue siendo obligatorio. Este contrato es lo que
> se revisa en cada PR. Cambios: se piden al PM por escrito y quedan en el
> historial.

## 1. El equipo

| Rol | Nombre | Usuario GitHub |
|---|---|---|
| Coordinador (abre los PRs) | | |
| Dev | | |
| Dev | | |
| Dev | | |
| Dev | | |

## 2. Alcance del módulo

Estructura del backend, conexión a base de datos, autenticación y
sesiones, control de acceso por roles, middleware (auth, validación, errores),
utilidades compartidas (paginación, filtros, fechas, respuestas), carga/
descarga segura de archivos, y especificación OpenAPI con colección de pruebas.

Paquete Python: `g2_api` (README §2).

## 3. Contrato de endpoints 🔒

Todas las rutas llevan el prefijo `/api/v1` (CONTRATO_COMUN.md §1).

| Método | Ruta | Resultado |
|---|---|---|
| POST | /auth/login | Autentica y entrega sesión o token |
| POST | /auth/logout | Invalida la sesión o token |
| GET | /me | Usuario, roles y permisos |
| GET/POST | /users | Lista o crea usuarios autorizados |
| GET/PATCH | /users/{id} | Consulta o actualiza usuario |
| GET/POST | /roles | Consulta o administra roles |
| POST | /files | Carga validada; retorna file_id |
| GET | /files/{id} | Descarga autorizada |
| GET | /openapi | Documentación del contrato |

**Servicio compartido.** Este grupo es dueño de, y publica para los grupos 3,
4, 5 y 6 (que los importan desde `g2_api`, no los reimplementan):

- Middleware de autenticación, autorización, validación y errores.
- El formato de error y la tabla de códigos HTTP del CONTRATO_COMUN.md.
- La utilidad de paginación (`page`, `per_page`, `total`, `data`) y el
  máximo de `per_page`, documentado en el OpenAPI.
- El servicio de archivos (`/files`).
- El OpenAPI integrado: cada grupo documenta sus rutas; el G2 las reúne.

El middleware y el OpenAPI base se publican **antes** de que los grupos 3, 4,
5 y 6 integren.

## 4. Reglas duras del módulo

- Contraseñas con hash robusto; jamás texto plano.
- Autorización EN el servidor, nunca solo botones ocultos.
- Consultas parametrizadas u ORM; nunca concatenar entrada del usuario.
- Archivos: lista permitida de tipos, límite de tamaño, nombres internos no
  predecibles, fuera de rutas ejecutables, descarga solo con autorización.
- Errores sin trazas, SQL, secretos ni rutas internas.
- Variables sensibles fuera del repositorio (en `.env`, con `.env.example`
  documentado).
- CORS, CSRF o estrategia equivalente según la autenticación escogida.
- Limitación o control de intentos de login.
- Registro de accesos y acciones sensibles.

## 5. Definición de HECHO (checklist de cada PR)

- [ ] Corre desde cero con `pip install -r requirements.txt` (raíz) en una
      máquina que no es la de ustedes.
- [ ] Respeta el CONTRATO_COMUN.md (prefijo, formato de error, códigos).
- [ ] Pruebas de acceso autorizado y denegado, y pasan: credenciales
      inválidas → 401; sin permiso → 403; inexistente → 404; conflicto → 409;
      validación → 422 con detalle por campo.
- [ ] Ninguna respuesta expone contraseñas ni secretos; un archivo no
      permitido es rechazado.
- [ ] El OpenAPI refleja EXACTAMENTE lo que la API responde.
- [ ] Ningún archivo fuera de la carpeta del grupo fue tocado.
- [ ] Sin credenciales ni datos personales reales en el código.
- [ ] El README del grupo dice cómo correr y probar el módulo, e incluye la
      guía de variables de entorno y seguridad.

## 6. Historial de cambios

| Fecha | Qué cambió | Quién lo pidió | Aprobado por |
|---|---|---|---|
| 2026-09-26 | Versión inicial | — | PM |
| 2026-09-28 | Jerarquía de fuentes; prefijo `/api/v1`; G2 dueño del formato de error, paginación y OpenAPI integrado; reglas del .docx que faltaban (variables sensibles, CORS/CSRF, límite de login, registro de accesos); checklist con pruebas y códigos HTTP | PM | PM |
