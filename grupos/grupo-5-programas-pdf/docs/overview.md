# Descripción General — Gestión de Programas

El sistema controla el ciclo de vida de los programas académicos, desde su creación como borrador hasta su autorización final.

## Componentes
- **Backend**: Basado en FastAPI. Incluye un manejador de errores unificado que estandariza las respuestas de la API.
- **Módulo G5**: Implementa la lógica de negocio y el control de acceso basado en roles (Autor, Coordinador, etc.).
- **Servicio de PDF**: Genera el documento institucional en memoria usando `ReportLab` para versiones autorizadas.
- **Frontend**: Interfaz web para la gestión de contenidos.

La seguridad se integra con el middleware de G2 para validar la identidad y roles del usuario.
