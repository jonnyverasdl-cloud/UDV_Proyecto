# CONTRATO.md — Grupo 6 · Administración, notificaciones, pruebas y despliegue

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

## 2. Alcance del módulo

Lo transversal: administración de usuarios/roles (usando servicios
del G2), catálogos académicos, notificaciones internas con marcas de lectura,
panel de indicadores, consulta de auditoría, pruebas de integración y
extremo a extremo, ambientes y despliegue, datos de demostración, y la
documentación de instalación con el guion de la presentación final.

Paquete Python: `g6_admin` (README §2).

## 3. Contrato de endpoints y eventos 🔒

Todas las rutas llevan el prefijo `/api/v1` (CONTRATO_COMUN.md §1).

| Método | Ruta | Uso |
|---|---|---|
| GET/POST | /academic-units | Administrar unidades académicas |
| GET/POST | /campuses | Administrar sedes |
| GET/POST | /courses | Administrar cursos |
| GET/POST | /periods | Administrar períodos |
| GET/POST | /modalities | Administrar modalidades |
| GET/POST | /areas | Administrar áreas |
| GET | /notifications | Listar notificaciones del usuario |
| PATCH | /notifications/{id}/read | Marcar lectura |
| GET | /dashboard | Indicadores agregados |
| GET | /audit | Consulta filtrada de auditoría |
| GET | /health | Estado técnico del servicio |

Eventos que disparan notificación. Estos nombres son los oficiales para todo
el sistema (CONTRATO_COMUN.md §3):

| Evento | Emisor | Destinatario | Mensaje esperado |
|---|---|---|---|
| task.published | G3 | Docente | Nueva tarea asignada y fecha límite |
| assignment.due_soon | G6 (tarea programada) | Docente | Tarea próxima a vencer |
| assignment.submitted | G3 | Revisor | Entrega disponible para revisión |
| assignment.returned | G3 | Docente | Entrega devuelta con observación |
| assignment.approved | G3 | Docente y coordinador | Entrega aprobada |
| program.authorized | G5 | Docente y coordinación | Nueva versión de programa autorizada |
| task.cancelled | G3 | Destinatarios | Tarea cancelada |

El mecanismo de transporte de eventos está pendiente (README §5): lo
proponen G3 y G6 en la semana 1.

## 4. Reglas duras del módulo

- La administración USA los servicios del G2 — no reimplementa auth ni
  usuarios.
- Solo administradores modifican catálogos protegidos.
- Cada evento genera una notificación, sin duplicados. Marcar como leída
  solo afecta al destinatario.
- El panel coincide con consultas verificables de la base.
- La auditoría se filtra por usuario, fecha, entidad y acción.
- No modifica tablas ajenas sin coordinación con el G1.
- Las pruebas de integración corren contra la máquina de estados del G3 y
  el contrato de cada grupo, no contra copias locales.
- El despliegue y los datos demo son de este grupo: nadie más toca ambientes.
  Los datos demo se cargan **encima** de las semillas del G1, sin
  modificarlas, y sin contraseñas reales.
- Todo lo de este grupo vive en su carpeta: pruebas de extremo a extremo,
  configuración de despliegue y documentación de instalación. El README de
  la raíz es del PM, que enlaza la guía de instalación de este grupo; si el
  despliegue necesita un archivo en la raíz, se pide al PM.

## 5. Definición de HECHO (checklist de cada PR)

- [ ] Corre desde cero con `pip install -r requirements.txt` (raíz) en una
      máquina que no es la de ustedes.
- [ ] Respeta el CONTRATO_COMUN.md (prefijo, formato de error, códigos).
- [ ] Pruebas propias (catálogos, notificaciones, permisos) y pasan.
- [ ] Las pruebas de integración y extremo a extremo pasan contra los
      módulos reales: crear tarea → inbox → entregar → devolver → reenviar →
      autorizar programa → descargar PDF.
- [ ] Sus endpoints aparecen en el OpenAPI y coinciden con este contrato.
- [ ] Una instalación limpia funciona siguiendo la guía de instalación, sin
      ajustes manuales ocultos.
- [ ] Ningún archivo fuera de la carpeta del grupo fue tocado.
- [ ] Sin credenciales ni datos personales reales en el código.
- [ ] El README del grupo dice cómo correr y probar el módulo.

## 6. Historial de cambios

| Fecha | Qué cambió | Quién lo pidió | Aprobado por |
|---|---|---|---|
| 2026-09-26 | Versión inicial | — | PM |
| 2026-09-28 | Jerarquía de fuentes; prefijo `/api/v1`; catálogos en filas separadas y **nuevos** `/modalities` y `/areas` (el .docx los pide en el alcance y no tenían ruta); columnas emisor y mensaje en eventos; datos demo vs. semillas del G1; README principal → guía en la carpeta del grupo; reglas del .docx que faltaban; checklist con pruebas y OpenAPI | PM | PM |
