# 📋 API REST y Workflow Docente — Proyecto Integrador

> Curso de Programación Web · Ingeniería en Sistemas · Universidad Da Vinci
> PM del proyecto: Jonathan Veras

> Este documento manda sobre todo lo demás del repositorio. Si algo aquí
> contradice lo dicho en el chat, gana este documento. Los cambios a estas
> reglas los hace el PM, con fecha y motivo, en el historial al final.

## 0. Fuentes de verdad (quién gana si dos documentos se contradicen)

| Nivel | Documento | Qué define | Quién lo cambia |
|---|---|---|---|
| 1 | `README.md` (este) | Proceso, reglas del repo, decisiones técnicas | PM |
| 2 | `CONTRATO_COMUN.md` | Convenciones de API que comparten los 6 grupos | PM |
| 3 | `grupos/*/CONTRATO.md` | Endpoints, reglas y checklist de PR de cada módulo | PM, a pedido del grupo |
| 4 | `grupos/*/*.docx` | Requerimiento detallado (versión 1, 2026-09-23) | Congelado |

- Gana el documento con el número de nivel más bajo. Si el .docx y el CONTRATO.md de un grupo
  se contradicen, gana el CONTRATO.md.
- Lo que el .docx exige y el CONTRATO.md no menciona **sigue siendo
  obligatorio**: el contrato resume, no recorta.
- El .docx no se edita. Todo cambio posterior queda en el historial del
  CONTRATO.md correspondiente.
- El OpenAPI **no** es fuente de verdad: se deriva de los contratos y debe
  coincidir con ellos.
- Los .docx oficiales son los que están dentro de `grupos/`. Cualquier otra
  copia (correo, chat, carpeta personal) puede estar desactualizada.

## 1. Qué construimos

Un sistema de workflow docente: coordinadores crean y asignan tareas, los
docentes las reciben en su inbox, entregan evidencias, los revisores aprueban
o devuelven, y los programas de curso se gestionan con versiones y PDF
institucional. **Una sola aplicación, un solo backend en Python** — cada grupo
construye un módulo y todos se integran por contratos de endpoints.

## 2. Los 6 grupos y sus módulos

| Grupo | Módulo | Carpeta | Paquete Python |
|---|---|---|---|
| 1 | Base de datos (modelo, migraciones, semillas, vistas) | `grupos/grupo-1-base-de-datos/` | `g1_bd` |
| 2 | API base y seguridad (auth, roles, archivos, OpenAPI) | `grupos/grupo-2-api-seguridad/` | `g2_api` |
| 3 | Workflow y tareas (tipos, publicación, transiciones) | `grupos/grupo-3-workflow-tareas/` | `g3_workflow` |
| 4 | Inbox y entregas (experiencia del docente y revisor) | `grupos/grupo-4-inbox-entregas/` | `g4_inbox` |
| 5 | Programas de curso, versiones y PDF | `grupos/grupo-5-programas-pdf/` | `g5_programas` |
| 6 | Administración, notificaciones, pruebas y despliegue | `grupos/grupo-6-administracion/` | `g6_admin` |

Cada carpeta de grupo contiene su **CONTRATO.md** (resumen operativo,
contrato de endpoints y checklist de PR) y su **documento de requerimientos
completo** (.docx). El contrato es lo que se evalúa en cada PR, junto con el
`CONTRATO_COMUN.md`.

## 3. Mapa de dependencias (quién necesita a quién)

```
G1 Base de datos  ──→  G2 API y seguridad  ──→  G3 Workflow ──→ G4 Inbox
        │                      │                                  │
        └──────────────────────┴──→  G5 Programas y PDF  ←────────┘
G6 Administración/Calidad consume los servicios de TODOS
```

(G4 ↔ G5: una entrega puede referenciar `program_version_id`.)

Regla práctica: si tu módulo necesita algo de otro grupo que aún no existe,
**no lo inventes** — trabaja contra el contrato de ese grupo (su tabla de
endpoints) usando datos de ejemplo, y avísale al PM para coordinar fechas.

## 4. Cómo está organizado el repo

- **`main`** — rama protegida. Nadie hace push directo (el servidor lo
  rechaza). Todo entra por Pull Request.
- **Una rama por grupo** (`grupo-1` … `grupo-6`) — ahí trabaja cada equipo.
  Si un grupo quiere ramas por funcionalidad, las crea como sub-ramas
  (`grupo-3/publicacion`) y las integra a `grupo-3`, nunca a `main`.
- **Una carpeta por grupo** — cada grupo toca SOLO su carpeta. Tocar la
  carpeta de otro grupo invalida el PR completo.
- **La raíz es del PM.** `README.md`, `CONTRATO_COMUN.md`, `requirements.txt`,
  `.gitignore`, `.env.example` y el punto de entrada de la aplicación los
  mantiene el PM. Si tu grupo necesita un cambio en la raíz, lo pide al PM.

### Estructura del código dentro de cada carpeta

Los nombres de carpeta llevan guiones y **no se pueden importar en Python**.
Por eso el código de cada grupo vive en un paquete con nombre válido:

```
grupos/grupo-2-api-seguridad/
├── CONTRATO.md
├── 02_Requerimientos_API_y_Seguridad.docx
├── README.md            ← cómo correr y probar el módulo
├── requirements.txt     ← dependencias propias del grupo
├── g2_api/              ← el código (paquete Python)
└── tests/
```

El punto de entrada de la raíz registra las carpetas de grupo para que
cualquier módulo pueda hacer `from g2_api import ...`. Nadie importa por
ruta de archivo ni copia código de otro grupo.

### Dependencias

- Cada grupo declara sus librerías en **su** `requirements.txt`.
- El `requirements.txt` de la raíz solo incluye los seis archivos de grupo.
  Toda la aplicación se instala con `pip install -r requirements.txt` desde
  la raíz.
- Si dos grupos piden versiones distintas de la misma librería, decide el PM.

## 5. Decisiones técnicas

| Tema | Estado | Quién decide | Plazo |
|---|---|---|---|
| Lenguaje del backend | ✅ **Python** | PM | Definido |
| Framework web (FastAPI / Flask / Django) | ⏳ Pendiente | PM, con propuesta del G2 | Semana 1, antes de escribir código |
| ORM y herramienta de migraciones | ⏳ Pendiente | G1 + G2 proponen, PM aprueba | Semana 1 |
| Motor de base de datos | ⏳ Pendiente | G1 + G2 proponen, PM aprueba | Semana 1 |
| Identificadores (enteros o UUID) | ⏳ Pendiente | G1 + G2 | Semana 1 |
| Zona horaria institucional | ⏳ Pendiente | PM | Semana 1 |
| Tecnología del frontend (pantallas de G3, G4, G5 y G6) | ⏳ Pendiente | PM | Semana 1 |
| Transporte de eventos para notificaciones | ⏳ Pendiente | G3 + G6 proponen (con G1 si requiere tabla), PM aprueba | Semana 1 |

Cuando una decisión se toma, se marca ✅ aquí y se anota en el historial.
Hasta entonces, nadie escribe código que dependa de ella.

## 6. El flujo de trabajo diario

1. `git pull origin grupo-X` — SIEMPRE antes de empezar.
2. Commits pequeños y frecuentes con mensajes claros:
   `git commit -m "inbox: filtro por estado y vencimiento"`.
3. `git push origin grupo-X` — tu trabajo queda respaldado y visible.
4. Para integrar, **solo el coordinador del grupo** abre el Pull Request.

**Sobre los puntos:** GitHub registra CADA commit con nombre y fecha — el
historial individual es visible para siempre. Que el coordinador maneje el PR
no significa que se lleve el crédito de nadie.

## 7. Reglas duras (no se negocian)

1. **Nunca push directo a `main`.**
2. **Solo el coordinador de cada grupo abre PRs.**
3. **Cada grupo toca solo su carpeta y su rama.**
4. **Backend en Python, un solo lenguaje.** Somos una aplicación, no seis
   apps pegadas con cinta. La libertad de cada grupo está en CÓMO implementa
   su módulo — mientras sus endpoints reciban y devuelvan exactamente lo que
   dice su CONTRATO.md y respeten el CONTRATO_COMUN.md.
5. **Nada de credenciales en el código.** Un commit con una contraseña
   adentro se rechaza y esa contraseña se considera quemada.
6. **Sin pruebas no hay PR.** Cada PR trae pruebas automáticas de lo que
   agrega, y pasan.

## 8. Seguridad (aviso amistoso ⚠️)

El servidor sanitiza y registra todas las entradas. Los intentos de inyección
SQL, XSS y similares no rompen nada y **quedan registrados con usuario y
hora**. Si te interesa la seguridad ofensiva, excelente — hablemos y te
enseño en un entorno hecho para eso.

## 9. Ayuda

¿Nunca has usado Git o GitHub? Sin pena — escríbeme y lo vemos juntos en 15
minutos. Glosario mínimo: **commit** = foto de tu avance con tu nombre ·
**push** = subir tus commits · **PR** = pedir que tu código entre a `main`
tras revisión · **merge** = la integración aprobada.

---

## Historial de cambios a este documento

| Fecha | Cambio | Motivo |
|---|---|---|
| 2026-09-26 | Versión inicial | Arranque del proyecto |
| 2026-09-28 | Jerarquía de fuentes de verdad (§0); `CONTRATO_COMUN.md`; raíz del PM, paquetes Python y `requirements.txt` por grupo (§4); tabla de decisiones técnicas (§5); sub-ramas por funcionalidad; regla dura 6 (pruebas) | README, CONTRATO.md, .docx y OpenAPI se declaraban fuente de verdad sin orden; la estructura por carpetas no permitía importar código entre grupos |
