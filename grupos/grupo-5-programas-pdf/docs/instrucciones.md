# Instrucciones para QA — G5 Programas y PDF

## Propósito

Esta guía explica el módulo G5, resume los cambios de esta rama y propone
comprobaciones para revisar su comportamiento. G5 administra programas de
curso, versiones, revisión y autorización; es un router para la aplicación
compartida, no un servidor independiente.

Antes de aprobar la integración, comparar el resultado con
[`CONTRATO.md` de G5](https://github.com/jonnyverasdl-cloud/UDV_Proyecto/blob/main/grupos/grupo-5-programas-pdf/CONTRATO.md)
y el [`CONTRATO_COMUN.md`](https://github.com/jonnyverasdl-cloud/UDV_Proyecto/blob/main/CONTRATO_COMUN.md).

## Qué cambió en esta rama

- **Autenticación:** `g5_programas/auth.py` obtiene el usuario mediante
  `g2_api.routers.auth.obtener_usuario_actual` y convierte su ID, nombre y
  roles al `Actor` interno que usan las rutas.
- **G2 no disponible:** si el paquete `g2_api` no se puede importar, el módulo
  define un proveedor alternativo que responde 503. Verificar que este sea el
  comportamiento esperado al ejecutar G5 fuera de la aplicación compartida.
- **Dependencias:** `requirements.txt` fija las versiones oficiales de
  FastAPI, Uvicorn, SQLAlchemy, PyMySQL y cryptography. No usar rangos de
  versiones para estas librerías.
- **Documentación:** arquitectura, flujo y criterios de revisión se mantienen
  en el README y esta guía.

El selector de rol del frontend solo sirve para mostrar opciones de la interfaz;
no representa autenticación real ni concede permisos en el backend.

## Flujo que debe validar QA

Las transiciones normales son:

```text
draft -> submitted -> under_review -> approved -> authorized
             ^             |
             |             v
             +---------- returned
```

| Acción | Estado inicial | Resultado | Rol esperado |
|---|---|---|---|
| Enviar (`submit`) | `draft` o `returned` | `submitted` | docente/autor |
| Tomar revisión (`review`) | `submitted` | `under_review` | revisor |
| Devolver (`return`) | `under_review` | `returned` | revisor |
| Aprobar (`approve`) | `under_review` | `approved` | revisor |
| Autorizar (`authorize`) | `approved` | `authorized` | autoridad |

Comprobar también que solo `draft` y `returned` se puedan editar, que una
devolución requiera observación y que no existan dos versiones autorizadas
para el mismo programa y período. La versión autorizada debe permanecer
inmutable; una nueva versión se crea como borrador clonado.

## Lista de comprobación

### Instalación y arranque

- [ ] Instalar desde cero con el `requirements.txt` de la raíz del proyecto
      compartido y confirmar que las dependencias se resuelvan sin rangos
      incompatibles.
- [ ] Confirmar que `main.py` incluya el router de G5 y que sus rutas aparezcan
      en `/api/v1/openapi.json`.
- [ ] Verificar que `DATABASE_URL` apunte a una base de prueba compatible con
      el esquema de G1; G5 no debe crear ni alterar tablas.
- [ ] Probar una petición autenticada con el token Bearer de G2. Confirmar que
      el usuario y sus roles llegan desde `obtener_usuario_actual`, no desde
      el selector del navegador.

### Permisos, validación y errores

- [ ] Sin autenticación: 401. Usuario autenticado sin el rol requerido: 403.
- [ ] ID inexistente: 404. Transición fuera de orden o conflicto de versión:
      409.
- [ ] Entrada inválida y devolución sin observación: 422 con detalles por
      campo y el formato común `{"error":{"code","message","details"}}`.
- [ ] Probar cada transición permitida y denegada con roles correctos e
      incorrectos.
- [ ] Confirmar que la UI no sea la única barrera de autorización: probar las
      rutas directamente contra la API.

### Persistencia, auditoría y PDF

- [ ] Guardar una sección y comprobar que las demás secciones se conserven.
- [ ] Confirmar que las filas dinámicas mantienen su orden tras guardar y
      volver a cargar.
- [ ] Enviar incompleto o con ponderaciones distintas de 100: la API debe
      rechazarlo sin cambiar el estado.
- [ ] Confirmar que las transiciones guarden actor, estado anterior, estado
      nuevo, fecha y comentario cuando corresponda.
- [ ] Generar PDF solo para una versión `authorized` o `superseded`; comprobar
      respuesta `application/pdf`, contenido y registro de huella.
- [ ] Verificar que autorizar una versión nueva deje la anterior como
      `superseded` y mantenga el historial consultable.

### Pruebas automatizadas

Desde la raíz del proyecto:

```bash
pytest -q
```

Las pruebas unitarias actuales cubren reglas de estados, editabilidad,
unicidad de versión autorizada y permisos. Un resultado exitoso no sustituye
las pruebas de integración con G2, MySQL, OpenAPI ni la descarga real del PDF.