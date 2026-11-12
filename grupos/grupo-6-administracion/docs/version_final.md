# Versión final y regresión (G6-39 y G6-40)

## Antes de cada entrega: regresión (G6-40)

Dos pasos. Si alguno falla, no se entrega.

**1. Pruebas automáticas**, en la carpeta del G6:

```bash
python -m pytest                       # todo el G6 sin MySQL
python -m pytest tests/integracion     # contra un MySQL de pruebas (G6_MYSQL_URL)
```

**2. Casos críticos contra la API levantada** (local, la base compartida o
la demostración). Solo consulta: no crea ni cambia datos.

```bash
python -m g6_admin.regresion --url http://127.0.0.1:8000
```

Pide la contraseña de los usuarios de prueba (o la lee de
`G6_REGRESION_CLAVE`) y nunca la muestra. Revisa, con el login real del G2:

| Escenario | Qué comprueba |
|---|---|
| G6-34 | `/api/v1/health` responde y la base dice `ok` |
| G6-01, G6-02 | Sin sesión: 401. Un docente consulta los 6 catálogos, pero no puede agregar (403) |
| G6-04 a G6-13 | El docente ve sus notificaciones |
| G6-26 a G6-29 | El panel responde, sus estados suman el total, las vencidas ya vencieron, las próximas están en el plazo y el cumplimiento cuadra. El docente no lo ve (403) |
| G6-30 a G6-33 | La auditoría filtra por usuario, fecha, entidad y acción, y el docente no la ve (403) |

Termina con `24 de 24 casos pasaron` y código 0, o marca con ✗ lo que falló y
sale con código 1.

## Versión o etiqueta final reproducible (G6-39)

La versión que se presenta tiene que poder reconstruirse igual en cualquier
momento. Para eso:

1. **Todo fijo.** Cada `requirements.txt` usa versiones exactas (`==`), como
   pide el README §5. El G6 no usa rangos.
2. **Regresión completa** sobre `main` (sección de arriba).
3. **Etiqueta en GitHub.** La pone el PM sobre el commit de `main` que pasó la
   regresión, por ejemplo `v1.0.0`, en Releases → Draft a new release. Una
   etiqueta no se mueve: si hay que corregir algo, se crea `v1.0.1`.
4. **Desplegar esa etiqueta.** En Railway, el despliegue del commit
   etiquetado, con `APP_VERSION=1.0.0`.
5. **Comprobar.** `GET /api/v1/health` muestra la versión y el commit:

   ```json
   {"status": "ok", "version": "1.0.0", "commit": "3dc943c", "environment": "demostracion", ...}
   ```

   `commit` lo pone Railway solo (`RAILWAY_GIT_COMMIT_SHA`); en otro servidor
   se define `APP_COMMIT`. Tiene que ser el mismo commit de la etiqueta.

**Reconstruir la versión** en otra computadora:

```bash
git clone --branch v1.0.0 https://github.com/jonnyverasdl-cloud/UDV_Proyecto.git
```

y seguir `instalacion.md` desde el paso 1.

Los cambios del G6 entre versiones están en `CHANGELOG.md` de esta carpeta.
