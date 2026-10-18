# g4_inbox — versión final integrada (inbox + detalle/entrega/revisión)



## Cómo correrlo

Debe quedar en `grupos/grupo-4-inbox-entregas/` dentro del repo (para que
`grupos/udv-styles/udv.css` se encuentre con la ruta relativa).

```
cd grupos/grupo-4-inbox-entregas
pip install -r requirements.txt
uvicorn g4_inbox.main:app --reload --app-dir .
```

Abrir `http://127.0.0.1:8000/static/inbox.html` y navegar desde ahí —
ya no hace falta abrir nada más por separado.

## Ya probado

- Los 4 archivos estáticos nuevos cargan con 200.
- El clic en una tarjeta navega correctamente a `detalle.html`.
- El ciclo completo (iniciar → guardar borrador → vincular archivo →
  entregar → tomar para revisar → aprobar/devolver) funciona de punta a
  punta contra el backend real.
- Las 53 pruebas automáticas de `inbox.py` (de Isai) siguen pasando.



## Actualización 16 de octubre — APIRouter + error común de G2

- `routes.py` es ahora el `APIRouter` real que la raíz del proyecto monta
  (`app.include_router(g4_router)`) — ya no tenemos nuestra propia
  `FastAPI()` para producción.
- `main.py` quedó como una app liviana, solo para correr y probar G4 por
  su cuenta: `uvicorn g4_inbox.main:app --reload --app-dir .`
- Ya usamos `register_error_handlers` de G2 — probado con el import
  cruzado real (`from g2_api.middleware.error_handler import
  register_error_handlers`), montando G2 y G4 lado a lado como estarán
  en el repo. Los 404/422/409 ya salen con el formato común, sin que
  tuviéramos que tocar ningún `HTTPException` existente.
- Si G4 corre completamente sola (sin G2 al lado), el import falla en
  silencio y sigue funcionando con los errores normales de FastAPI — no
  se rompe para quien solo quiere probar G4.
- El mount de `udv-styles` ya NO se activa por defecto (como pidió el
  brief) — solo se prende con `G4_STANDALONE_DEV=1`, para seguir viendo
  el CSS institucional mientras prueban G4 solos.
- Docs ahora en `/api/v1/docs` (antes `/docs`), para coincidir con la
  convención del resto del proyecto.

## Brief del 14 de octubre — estado final

| # | Punto | Estado |
|---|---|---|
| 1 | Versiones exactas | ✅ Resuelto |
| 2 | Base de datos real (MySQL) | ✅ Resuelto — SQLAlchemy + DATABASE_URL, probado contra MySQL real |
| 3 | Transiciones duplicadas con G3 | Confirmado en reunión del 16/10: seguimos emulando hasta que G3 publique su motor |
| 4 | Pruebas automatizadas | ✅ Resuelto — 66 pruebas pasando |
| 5 | Formato de error común de G2 | ✅ Resuelto — `register_error_handlers`, probado con import real |
| 6 | APIRouter en vez de FastAPI propia | ✅ Resuelto |
| 7 | No montar udv-styles | ✅ Resuelto — solo opcional en modo desarrollo |



