# g4_inbox — versión final integrada (inbox + detalle/entrega/revisión)


## Cómo correrlo

Debe quedar en `grupos/grupo-4-inbox-entregas/` dentro del repo (para que
`grupos/udv-styles/udv.css` se encuentre con la ruta relativa).

```
cd grupos/grupo-4-inbox-entregas
pip install -r requirements.txt
uvicorn g4_inbox.main:app --reload --app-dir .
```

Abrir `http://127.0.0.1:8000/static/inbox.html` 

## Ya probado

- Los 4 archivos estáticos cargan con 200.
- El clic en una tarjeta navega correctamente a `detalle.html`.
- El ciclo completo (iniciar → guardar borrador → vincular archivo →
  entregar → tomar para revisar → aprobar/devolver) funciona de punta a
  punta contra el backend real.
- Las 53 pruebas automáticas de `inbox.py` siguen pasando.
