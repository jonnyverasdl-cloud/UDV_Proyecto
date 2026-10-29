"""Comprueba que la carpeta de archivos sobrevive a un reinicio (escenario G6-37).

Antes de reiniciar o volver a desplegar se deja una marca en la carpeta donde
se guardan los archivos subidos; después del reinicio se comprueba que sigue
ahí. Si desapareció, los archivos de los docentes también se perderían.

    python -m g6_admin.persistencia marcar
    (reiniciar o volver a desplegar el servicio)
    python -m g6_admin.persistencia comprobar

La carpeta es la de UPLOAD_DIR o, si no está definida, `uploads`, que es donde
guarda hoy el router de archivos del G2 (ver docs/recuperacion.md). Se puede
indicar otra con --dir. Termina con código 1 si la marca no está.
"""

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

NOMBRE_MARCA = ".g6-persistencia.json"
CARPETA_PREDETERMINADA = "uploads"


def carpeta_de_archivos(variables: dict[str, str] | None = None) -> Path:
    variables = os.environ if variables is None else variables
    return Path(variables.get("UPLOAD_DIR") or CARPETA_PREDETERMINADA)


def marcar(carpeta: Path) -> dict[str, str]:
    carpeta.mkdir(parents=True, exist_ok=True)
    marca = {"id": secrets.token_hex(8),
             "creada_en": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (carpeta / NOMBRE_MARCA).write_text(json.dumps(marca), encoding="utf-8")
    return marca


def comprobar(carpeta: Path) -> dict[str, str] | None:
    """La marca guardada, o None si ya no está (o no se puede leer)."""
    try:
        marca = json.loads((carpeta / NOMBRE_MARCA).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return marca if isinstance(marca, dict) and "id" in marca else None


def main(argumentos: list[str] | None = None) -> int:
    lector = argparse.ArgumentParser(prog="python -m g6_admin.persistencia",
                                     description=__doc__.splitlines()[0])
    lector.add_argument("accion", choices=("marcar", "comprobar"))
    lector.add_argument("--dir", type=Path, help="Carpeta a revisar (por defecto UPLOAD_DIR)")
    opciones = lector.parse_args(argumentos)
    carpeta = opciones.dir or carpeta_de_archivos()

    if opciones.accion == "marcar":
        marca = marcar(carpeta)
        print(f"Marca {marca['id']} guardada en {carpeta.resolve()}.")
        print("Ahora reinicia o vuelve a desplegar y corre: "
              "python -m g6_admin.persistencia comprobar")
        return 0

    marca = comprobar(carpeta)
    if marca is None:
        print(f"  ✗ No está la marca en {carpeta.resolve()}: la carpeta no sobrevivió "
              "al reinicio (o no se marcó antes).")
        return 1
    print(f"  ✓ La marca {marca['id']} del {marca.get('creada_en', '?')} sigue en "
          f"{carpeta.resolve()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
