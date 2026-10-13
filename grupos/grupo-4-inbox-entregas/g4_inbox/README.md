# g4_inbox — versión integrada (inbox real + backend)


## Cómo correrlo DENTRO del repositorio completo (como va a vivir de verdad)

Debe quedar en: `grupos/grupo-4-inbox-entregas/g4_inbox/` — y
`grupos/udv-styles/udv.css` debe existir (ya existe en el repo real).

```
cd grupos/grupo-4-inbox-entregas
pip install -r requirements.txt
uvicorn g4_inbox.main:app --reload --app-dir .
```

Abrir:
- http://127.0.0.1:8000/docs → probar los 13 endpoints
- http://127.0.0.1:8000/static/inbox.html → la pantalla real del inbox, ya conectada

## Qué falta 

- Las pantallas de detalle, entrega y revisión (demo-grupo4-simple.html)
  todavía no están conectadas al backend real — esa es la otra tarea
  pendiente.
- Las tarjetas del inbox todavía no navegan a ninguna pantalla al hacer
  clic — falta ese enlace una vez exista la pantalla de detalle real.
- Probado con `X-User: 1` (ve 8 tareas) y `X-User: 2` (ve 2 tareas,
  prueba de privacidad) — ya verificado que funciona.
