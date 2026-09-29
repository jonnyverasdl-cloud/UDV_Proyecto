# CONTRATO.md — Grupo 1 · Base de datos

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

Modelo relacional completo del sistema: DER, diccionario de datos,
migraciones, claves e índices, datos semilla (roles, estados, tipos de tarea,
usuarios, cursos y un programa de ejemplo), vistas para inbox/panel/historial/
versión vigente, y estrategia de eliminación lógica y respaldo.

Paquete Python: `g1_bd` (README §2).

## 3. Contrato de entrega (lo que los demás grupos consumen) 🔒

Este grupo no expone endpoints: entrega **el esquema**. Su contrato es:

- Migraciones reproducibles (`01_schema.sql` o migraciones equivalentes con
  la herramienta aprobada en README §5): cualquier grupo levanta la base desde
  cero con un solo comando documentado.
- Nombres de tablas y columnas EXACTOS al diccionario de datos — un rename
  sin aviso rompe a los grupos 2, 3, 4, 5 y 6.
- El diccionario de datos incluye, por tabla, **el recurso de la API que la
  expone** (ej.: `tarea_destinatario` ↔ `/assignments`, `tipo_tarea` ↔
  `/task-types`), porque la base usa nombres en español y la API en inglés.
- Datos semilla (`02_seed.sql` o equivalente) suficientes para que los demás
  desarrollen sin inventar datos. Son la **base** del sistema; el escenario de
  demostración del G6 se carga encima, sin modificar estas tablas.
- Las vistas de inbox, panel, historial y versión vigente documentadas con
  sus columnas.
- Tipo de identificador (entero o UUID) acordado con el G2 antes de congelar
  el esquema (README §5).

## 4. Reglas duras del módulo

- Correo de usuario único; una asignación única por tarea y destinatario.
- Toda transición referencia asignación, actor y estados válidos.
- Solo UNA versión autorizada y vigente por curso/sede/período (y el contexto
  acordado), garantizado por restricción en la base.
- Una versión autorizada no se actualiza: los cambios crean otra versión.
- El orden de módulos, unidades, bibliografía y evaluaciones se persiste.
- El total de evaluaciones se valida en negocio y, cuando sea viable, también
  en la base.
- Archivo conserva nombre original, nombre interno, MIME, tamaño, hash, autor
  y ubicación.
- Fechas de creación y actualización se generan de forma consistente.
- Eliminación lógica: el historial nunca se pierde con un DELETE.
- Nombres de estado exactamente como en CONTRATO_COMUN.md §2.

## 5. Definición de HECHO (checklist de cada PR)

- [ ] Corre desde cero con `pip install -r requirements.txt` (raíz) en una
      máquina que no es la de ustedes.
- [ ] Las migraciones corren desde cero y los seeds cargan sin errores.
- [ ] Hay pruebas o consultas de verificación de las restricciones (FK,
      únicos, versión vigente) y pasan.
- [ ] Las consultas principales usan índices, justificados en el README.
- [ ] Diccionario de datos y DER actualizados con los cambios del PR.
- [ ] Respaldo y restauración documentados.
- [ ] Ningún archivo fuera de la carpeta del grupo fue tocado.
- [ ] Sin credenciales ni datos personales reales en el código.
- [ ] El README del grupo dice cómo crear, migrar, respaldar y restaurar.

## 6. Historial de cambios

| Fecha | Qué cambió | Quién lo pidió | Aprobado por |
|---|---|---|---|
| 2026-09-26 | Versión inicial | — | PM |
| 2026-09-28 | Jerarquía de fuentes; reglas del .docx que faltaban (inmutabilidad, orden, metadatos de archivo, fechas, total de evaluaciones); mapeo tabla↔recurso API; semillas vs. demo del G6; checklist con pruebas, índices y respaldo | PM | PM |
