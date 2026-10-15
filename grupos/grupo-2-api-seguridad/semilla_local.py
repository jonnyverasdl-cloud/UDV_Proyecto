# SOLO PARA DEMO LOCAL. NO SE SUBE AL REPO.
# Arma dev.db (SQLite) con las tablas de models.py y un usuario admin para probar el login
# mientras no tengamos MySQL con Docker.
# Correr desde grupos/grupo-2-api-seguridad:  .venv\Scripts\python.exe semilla_local.py

from g2_api import config
from g2_api.database import Base, SessionLocal, engine
from g2_api import models
from g2_api.seguridad import hashear_contrasena

if not config.DATABASE_URL.startswith("sqlite"):
    raise SystemExit("Este script solo corre con SQLite. Revisa DATABASE_URL en tu .env")

# Borra y vuelve a crear las tablas en dev.db (solo tu archivo local).
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

with SessionLocal() as db:
    db.add(models.Rol(id=1, codigo="admin", nombre="Administrador"))
    db.add(
        models.Usuario(
            id=1,
            correo="admin@demo.udv.edu.gt",
            nombres="Ana",
            apellidos="Administradora",
            hash_contrasena=hashear_contrasena("Demo2026!"),
        )
    )
    db.flush()
    db.add(models.UsuarioRol(usuario_id=1, rol_id=1))
    db.commit()

print("Listo: admin@demo.udv.edu.gt / Demo2026!")
