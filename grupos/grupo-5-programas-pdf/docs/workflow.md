# Flujo del Sistema

Este documento describe el proceso de gestión de los programas de curso, desde su creación hasta la emisión del documento oficial.

## Componentes del Flujo
- **Frontend**: Interfaz donde el usuario gestiona el contenido del programa.
- **Backend (`app.py`)**: Actúa como el núcleo que integra los routers de los diferentes grupos, sirve la interfaz web y estandariza los errores de la API.
- **Módulo G5**: Implementa las reglas de negocio, la autenticación delegada a G2 y la persistencia en MySQL.
- **Servicio de PDF**: Genera el documento institucional en formato PDF utilizando la librería `ReportLab`.

## Ciclo de Vida de una Versión

El sistema controla el estado de cada versión para asegurar que solo los documentos revisados sean oficiales:

`draft` $\rightarrow$ `submitted` $\rightarrow$ `under_review` $\rightarrow$ `approved` $\rightarrow$ `authorized`

### Reglas de Transición
- **Edición**: Solo es posible editar versiones en estado `draft` (borrador) o `returned` (devuelta para correcciones).
- **Revisión**: Una versión `submitted` pasa a `under_review` cuando un revisor comienza la evaluación.
- **Devolución**: Si hay observaciones, la versión regresa al estado `returned`.
- **Autorización**: Es el estado final. La base de datos protege estas versiones para que sean inmutables y garantiza que solo haya una versión vigente por período.

## Generación y Descarga de PDF

El PDF es la representación oficial del programa y sigue estas condiciones:

1. **Restricción**: Solo se generan PDFs para versiones en estado `authorized` o `superseded` (reemplazadas).
2. **Proceso**: 
   - El sistema recupera los datos y las secciones del programa.
   - Se construye el documento en memoria para evitar archivos temporales en el servidor.
   - Se calcula y guarda un **digest** (hash) del archivo para auditoría.
3. **Descarga**: El archivo se entrega directamente al usuario mediante el endpoint `/api/v1/program-versions/{id}/pdf`.
