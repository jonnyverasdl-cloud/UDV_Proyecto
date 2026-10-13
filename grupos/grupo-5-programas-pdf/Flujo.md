# Flujo del sistema

## Inicio

Al abrir la aplicación desde el servidor (`http://127.0.0.1:8000/`), el sistema
carga el programa principal (ID 1) desde la API:

- Rol seleccionado: `Docente`.

El selector de rol permite probar las acciones de Docente, Coordinación
académica y Decanatura. Los permisos del flujo se validan también en el backend;
el selector sigue siendo una simulación y no sustituye la autenticación de
usuarios.

## Flujo del programa

```text
BORRADOR
  |
  | Docente completa su nombre y selecciona "Enviar a revisión"
  v
EN REVISIÓN
  |
  | Coordinación académica registra su nombre
  |
  +-- Devolver al docente --> DEVUELTO
  |                              |
  |                              | Docente edita, guarda y vuelve a enviar
  |                              +--------------------------> EN REVISIÓN
  |
  +-- Aprobar ----------------> APROBADO
                                  |
                                  | Decanatura registra su nombre
                                  |
                                  +-- Autorizar -----------> VIGENTE
                                  |                           |
                                  |                           | Coordinación académica
                                  |                           | crea una versión
                                  |                           v
                                  |                        BORRADOR
                                  |                        (versión siguiente)

Al autorizar una versión nueva, la que estaba vigente pasa a `REEMPLAZADO` y
se conserva como historial.
```

## Acciones y permisos

| Rol | Estado | Acciones disponibles |
| --- | --- | --- |
| Docente | `BORRADOR` o `DEVUELTO` | Editar el programa, guardar borrador y enviarlo a revisión. |
| Coordinador académico | `EN REVISIÓN` | Registrar su nombre, devolver el programa o aprobarlo. |
| Decanatura | `APROBADO` | Registrar su nombre y autorizar la versión. |
| Coordinador académico | `VIGENTE` | Crear la siguiente versión en estado `BORRADOR`. |

Los campos de las secciones del programa solo se pueden editar como Docente
cuando el estado es `BORRADOR` o `DEVUELTO`.

El nombre de Docencia se puede editar en esos mismos casos. Los nombres de
Coordinación académica y Decanatura se registran al devolver/aprobar y
autorizar, respectivamente, y quedan asociados a la versión.

Para enviar a revisión, el programa debe tener nombre de docente y los campos
obligatorios de información general. Para aprobar o devolver, Coordinación
académica debe indicar su nombre; la devolución también exige una observación.
Para autorizar, Decanatura debe indicar su nombre.

## Guardado y versiones

- «Guardar borrador» persiste las secciones en la API y en `programas.json`.
- «Cancelar cambios» vuelve a cargar los últimos datos guardados del servidor.
- Crear una versión copia la última versión vigente y la inicia en
  `BORRADOR`.
- El estado, el número de versión y las acciones quedan persistidos en el
  historial.

## Vista previa e impresión

- «Vista previa PDF» genera una vista institucional con el contenido actual de
  todas las secciones del programa, mostrando sus campos como texto.
- La vista incluye asignatura, facultad, versión, fecha, estado, los nombres de
  Docencia, Decanatura y Coordinación académica, además de espacios de firma.
- La leyenda indica «Documento autorizado» solo cuando el estado es `VIGENTE`;
  en los demás estados indica que no tiene autorización vigente.
- «Descargar PDF» obtiene el documento generado por el endpoint del backend.
- «Volver al editor» cierra la vista previa y vuelve a mostrar el formulario.

## Iniciar el servidor

Desde la raíz del proyecto, crea un entorno e instala la dependencia del PDF:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python backend/main.py
```

Abre `http://127.0.0.1:8000/`. Si el servidor ya estaba activo antes de una
actualización, reinícialo para que cargue el backend nuevo.
