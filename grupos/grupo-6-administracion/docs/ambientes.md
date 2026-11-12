# Ambientes: desarrollo y demostración (G6-35)

Todo se configura con variables de entorno, nunca en el código. Cada ambiente
tiene **su propia base**: lo que se prueba en desarrollo no toca la de la
demostración.

| Variable | desarrollo (tu computadora) | demostracion (Railway) |
|---|---|---|
| `APP_ENV` | `desarrollo` | `demostracion` |
| `DATABASE_URL` | MySQL local (`127.0.0.1`) o SQLite | El MySQL de Railway, con un usuario que no sea `root` |
| `SECRET_KEY` | Cualquiera | Aleatoria, de 32 caracteres o más, distinta a la de desarrollo |
| `CORS_ORIGINS` | `http://localhost:5500` | La dirección pública, nunca `*` |
| `APP_VERSION` | Opcional | La etiqueta que se presenta (ver `version_final.md`) |
| `UPLOAD_DIR` | Opcional | Ruta absoluta dentro de un volumen, por ejemplo `/data/archivos` (ver `recuperacion.md`) |
| `APP_COMMIT` | Opcional | Railway ya da `RAILWAY_GIT_COMMIT_SHA`; en otro servidor, el commit desplegado |

`GET /api/v1/health` muestra `environment`, `version` y `commit`, así se sabe
en qué ambiente está cada servidor y qué código corre, sin ver secretos.

## Revisar un ambiente

```bash
cd grupos/grupo-6-administracion
python -m g6_admin.ambiente
```

Lee el `.env` de la raíz (o las variables del servidor) y revisa:

- `APP_ENV` es `desarrollo` o `demostracion`.
- Existe `DATABASE_URL` y dice el nombre de la base.
- En demostración: la base es MySQL, no es la local, no usa `root` y su
  contraseña no es la del ejemplo.
- En demostración: `SECRET_KEY` es larga y no es un valor de ejemplo, y
  `CORS_ORIGINS` no es `*`.
- En demostración: `UPLOAD_DIR` es una ruta absoluta, para que los archivos
  vivan en un volumen y no se pierdan al reiniciar (G6-37).

Las contraseñas salen como `***`. Termina con código 1 si algo falla, así que
se puede usar antes de desplegar. Las reglas están probadas en
`tests/test_ambiente.py`.

## En Railway

En **Variables** del servicio de la app se definen `APP_ENV=demostracion`,
`SECRET_KEY` y `DATABASE_URL` como indica `.env.example` de la raíz. Después
del despliegue, `/api/v1/health` debe decir `"environment": "demostracion"` y
`"database": "ok"`.
