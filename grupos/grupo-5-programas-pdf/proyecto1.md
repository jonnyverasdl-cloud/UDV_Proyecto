# MEMORIA PRINCIPAL — PROYECTO F1, GRUPO 5

## 1. Identificación del proyecto

**Nombre:** Grupo 5 — Programas de curso, versiones y PDF.

**Curso:** Programación Web.

**Universidad:** Universidad Da Vinci de Guatemala (UDV).

**Tipo:** Proyecto integrador de API REST y workflow docente.

**Repositorio de GitHub:** https://github.com/aldron01/grupo5-programas-curso.git

La finalidad es desarrollar un sistema web que permita gestionar programas académicos de cursos mediante formularios por secciones, borradores, versiones, revisión, aprobación, autorización y generación de PDF institucional.

La prioridad es cumplir todos los requisitos del proyecto académico, no solamente crear una página que se vea bien o que guarde información.

## 2. Objetivo general

Construir una aplicación web funcional que permita crear y administrar programas de curso, guardar avances, crear nuevas versiones, revisar cambios, controlar el flujo de autorización y generar documentos PDF institucionales.

El sistema debe mantener el historial de versiones y garantizar que solamente exista una versión autorizada y vigente por cada programa de curso.

## 3. Tecnologías del proyecto

- HTML para la estructura del frontend.
- CSS para los estilos.
- JavaScript para las interacciones y comunicación con el backend.
- Python para el servidor y la API REST.
- `programas.json` como almacenamiento actual de datos.
- Git y GitHub para controlar las versiones del código.
- PDF para la generación del documento institucional.

El almacenamiento actual en JSON es la implementación inicial. Si los requisitos académicos exigen una base de datos, se deberá incorporar sin perder las funcionalidades existentes.

## 4. Estructura actual del proyecto

```text
Proyecto/
├── backend/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── Demo.html
│   ├── estilos/
│   │   └── style.css
│   └── script.js
├── programas.json
├── Formulario.pdf
├── Flujo.md
└── .gitignore
```

Esta es la estructura que el usuario tiene actualmente según la terminal. Puede haber cambios posteriores.

No asumir que existen carpetas, archivos, funciones o módulos que no se hayan comprobado.

## 5. Estado actual del desarrollo

### Frontend

Existe una interfaz en `frontend/Demo.html`, los estilos en `frontend/estilos/style.css` y el JavaScript en `frontend/script.js`.

El proyecto utiliza una interfaz con menú lateral, secciones de formulario y
botones de acciones. El workflow actual usa Docente,
Coordinación académica y Decanatura; sus nombres se registran al realizar las
acciones. El selector de rol es una simulación, no un inicio de sesión.

### Backend

El archivo `backend/main.py` implementa un servidor Python usando
`SimpleHTTPRequestHandler` y `ThreadingHTTPServer`. La dependencia PDF se
instala desde `backend/requirements.txt`.

Instala las dependencias y ejecuta el servidor desde la raíz del proyecto:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python backend/main.py
```

La dirección local es:

`http://127.0.0.1:8000`

El servidor carga `frontend/Demo.html` al abrir la ruta principal `/`.

El backend implementa los endpoints de programas, versiones, secciones,
workflow, comparación de versiones y descarga PDF descritos en la sección 9.
La escritura JSON se realiza mediante archivo temporal. `PUT /api/programas`
ya no se admite para impedir reemplazar los datos sin seguir el flujo.

### Almacenamiento

El archivo `programas.json` contiene las colecciones `programas`, `versiones` e `historial`.

La estructura inicial contiene información del curso Programación Web, como código, asignatura, programa académico, facultad, departamento, ciclo, año, nivel, área de formación, pensum, modalidad, créditos, horas, sede, docente, versión actual y estado.

Antes de modificar los nombres de los campos o la estructura JSON, revisar los archivos existentes y mantener la compatibilidad con el frontend.

### GitHub

El repositorio del proyecto es:

`https://github.com/aldron01/grupo5-programas-curso.git`

Para registrar y subir cambios se utiliza Git. No confundir guardar archivos en VS Code con subirlos a GitHub.

## 6. Requisitos funcionales obligatorios

El sistema debe incluir:

1. Formularios organizados por secciones.
2. Creación y edición de programas de curso.
3. Guardado de borradores.
4. Guardado parcial de las secciones.
5. Creación y clonación de versiones.
6. Filas dinámicas que permitan agregar, eliminar y ordenar elementos cuando corresponda.
7. Validaciones de los datos requeridos.
8. Comparación de cambios entre versiones.
9. Historial de acciones y modificaciones.
10. Workflow de envío, revisión, devolución, aprobación y autorización.
11. Control de roles y permisos según las responsabilidades de cada usuario.
12. Una sola versión autorizada y vigente por programa.
13. Generación y descarga de PDF institucional.
14. Comunicación real entre frontend y backend.
15. Persistencia de los datos, para que no desaparezcan al recargar la página.

No marcar una funcionalidad como completada si solamente muestra un mensaje visual, pero no realiza la operación correspondiente.

## 7. Secciones del programa de curso

El formulario debe contemplar las siguientes secciones:

### Información general
Código, asignatura, programa académico, departamento, facultad, ciclo, año, nivel, área de formación, pensum, modalidad, créditos, horas semanales, sede y docente.

### Prerrequisitos
Asignatura, código y orden de los prerrequisitos.

### Descripción
Descripción general del curso.

### Competencias
Competencia general y competencias específicas.

### Perfil de egreso
Código y contribución de la asignatura al perfil de egreso.

### Contenidos
Organización de los contenidos del curso, incluyendo filas dinámicas si el formulario lo requiere.

### Bibliografía
Referencias bibliográficas del curso.

### Evaluación
Actividades, criterios, distribución de puntos y otros campos que establezca el formulario institucional.

### Autorización
Información relacionada con responsables, revisión, aprobación y autorización del programa.

Estas secciones deben verificarse contra `Formulario.pdf`. Si el documento contiene campos adicionales, deben incluirse según los requisitos originales.

## 8. Workflow del sistema

El flujo implementado es:

**Borrador → En revisión → Devuelto o Aprobado → Vigente**

Comportamiento:

- **Docente:** crea y edita el programa, guarda borradores y lo envía a revisión.
- **Coordinación académica:** revisa el contenido, puede devolverlo o aprobarlo y crea nuevas versiones a partir de la vigente.
- **Decanatura:** autoriza las versiones aprobadas.

Reglas importantes:

- No enviar a revisión si faltan datos obligatorios.
- La devolución debe registrar una observación.
- No permitir autorizar una versión que no haya sido aprobada.
- Una versión autorizada debe conservarse como registro histórico.
- Las modificaciones posteriores deben realizarse en una nueva versión.
- Al autorizar una nueva versión, la anterior pasa a `reemplazado` sin borrar su historial.
- No permitir transiciones de estado que incumplan el workflow.

El backend valida el rol declarado para cada acción. El selector de rol es una
simulación académica, no autenticación: cualquier cliente puede falsificar el
rol enviado en una solicitud. No debe desplegarse como sistema seguro sin
autenticación real y asociación de permisos a la identidad autenticada.

## 9. Endpoints REST disponibles

El backend implementa los siguientes endpoints:

### Programas

- `GET /course-programs`: listar programas.
- `POST /course-programs`: crear un programa.
- `GET /course-programs/{id}`: consultar un programa y sus versiones.

### Versiones

- `POST /course-programs/{id}/versions`: crear una versión o clonar un borrador.
- `GET /program-versions/{id}`: consultar una versión.
- `PUT /program-versions/{id}`: guardar una versión completa.
- `PUT /program-versions/{id}/sections/{section}`: guardar una sección específica.
- `GET /program-versions/{id}/changes`: comparar con la versión anterior.

### Workflow

- `POST /program-versions/{id}/submit`: enviar a revisión.
- `POST /program-versions/{id}/return`: devolver con observaciones.
- `POST /program-versions/{id}/approve`: aprobar contenido.
- `POST /program-versions/{id}/authorize`: autorizar y declarar vigente.

### PDF

- `GET /program-versions/{id}/pdf`: generar o descargar el PDF institucional.

La ruta heredada `GET /api/programas` permanece disponible para lectura.
`PUT /api/programas` fue retirada para evitar reemplazar todo el archivo sin
respetar el flujo; para guardar se deben usar los endpoints de secciones.

## 10. Fases originales del proyecto

### Fase 1: propuesta y estructura

- Definir el objetivo.
- Identificar las secciones del programa de curso.
- Seleccionar tecnologías.
- Preparar la estructura de carpetas.
- Crear el repositorio.
- Elaborar el README inicial.
- Preparar un primer diseño de la interfaz.

Entregable: estructura inicial del proyecto y prototipo sencillo de la pantalla principal.

### Fase 2: prototipo visual básico

- Crear la página HTML principal.
- Diseñar el menú lateral.
- Organizar las secciones.
- Agregar los campos básicos del formulario.
- Incorporar botones de navegación, guardar y cancelar.
- Probar con datos de ejemplo.

Entregable: página HTML funcional para realizar pruebas.

### Trabajo pendiente

La comparación y descarga PDF están conectadas a la API; los campos del
formulario se guardan por sección. La creación de programas desde la interfaz
y la autenticación real todavía requieren superficies específicas. Los roles
del selector son solo una simulación hasta que se incorpore autenticación.

## 11. Flujo de datos

Cuando el usuario consulta un programa, el frontend solicita los datos al backend.

Cuando el usuario guarda cambios, el frontend envía la información a la API.

El backend valida la solicitud, actualiza el almacenamiento y devuelve una respuesta.

La interfaz debe mostrar un mensaje de éxito o error según el resultado real del servidor.

El sistema no debe fingir que guardó los cambios cuando la solicitud falla o cuando todavía no existe conexión con la API.

## 12. Reglas de trabajo para la IA de VS Code

- Leer los archivos actuales antes de proponer cambios.
- Trabajar sobre el proyecto existente, no empezar uno nuevo.
- Conservar las funciones que ya funcionan.
- Evitar reemplazar todos los archivos si solo se necesita modificar una parte.
- Explicar los cambios en español sencillo, casual y natural.
- Usar comentarios cortos y útiles en el código.
- Entregar archivos completos cuando el usuario solicite expresamente reemplazarlos.
- No inventar funciones implementadas ni afirmar que se hicieron pruebas que no se ejecutaron.
- Explicar cómo probar cada funcionalidad.
- Mantener los nombres de campos y rutas consistentes.
- Comprobar errores, validaciones y persistencia.
- Priorizar los requisitos académicos y el funcionamiento real sobre las mejoras visuales innecesarias.

## 13. Próximo paso recomendado

El siguiente paso es incorporar autenticación real para reemplazar el selector
de rol simulado y comparar el formulario implementado con la versión válida del
documento institucional.

**Objetivo final:** tener una aplicación funcional que cumpla los requisitos del Grupo 5 y permita administrar programas de curso con formularios por secciones, versiones, workflow docente, autorización de una única versión vigente y generación de PDF institucional.

## 14. Estado verificado del proyecto y roles (2026-10-12)

- Los roles de prueba son `docente`, `coordinador-academico` y `decanatura`.
- El backend valida el rol declarado, las transiciones y los campos requeridos,
  registra las observaciones y mantiene una sola versión vigente.
- El selector de rol sigue siendo una simulación: no hay autenticación y un
  cliente puede falsificar el rol enviado. Se requiere autenticación real antes
  de desplegar el sistema como una aplicación segura.
- El frontend consume la API, permite elegir un programa, guardar secciones,
  revisar el workflow y descargar un PDF.
- El formulario incluye Información general, Prerrequisitos, Descripción,
  Competencias, Perfil de egreso, Metodología, Contenidos, Bibliografía y
  Evaluación.
- La verificación del flujo se debe realizar ejecutando el servidor y probando
  las acciones de cada rol.
- La copia de trabajo de `Formulario.pdf` está eliminada/vacía; por ello falta
  contrastar el formulario con el documento institucional original.
