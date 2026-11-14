import uuid # <----- Nombre interno aleatorio del archivo
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import puremagic # <----- Dependencia Para verificar el tipo de archivo
from g2_api.middleware.auth_middleware import obtener_usuario_actual
from g2_api.models import Usuario
from pathlib import Path
from fastapi.responses import FileResponse
import hashlib

from sqlalchemy.orm import Session

from g2_api import config
from g2_api.database import get_db
from g2_api.models import Archivo

# Crear un router para manejar las rutas relacionadas con archivos
router = APIRouter(
    prefix="/api/v1/files",
    tags=["Files"]
)


MAX_SIZE = 5 * 1024 * 1024  # 5 MB

# Definir los tipos de archivos permitidos y sus extensiones correspondientes
MIMETYPES_PERMITIDOS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png"
}

# Definir la ruta para verificar el archivo subido
@router.post("")
async def verificar_archivo(file: UploadFile = File(...),
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):
    contenido = await file.read()

    if len(contenido) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="El archivo supera el límite de 5 MB"
        )
    # leer los primeros 2048 bytes del archivo para determinar su tipo real
    try:
        tipo_real = puremagic.from_string(contenido[:2048], mime=True)
    except puremagic.PureError:
        # si el archivo esta corrupto o no se puede determinar su tipo, se lanza una excepción HTTP
        raise HTTPException(
            status_code=400,
            detail="No se pudo leer el tipo de archivo. Solo se aceptan PDF, JPG o PNG sin dañar."
        )

    # Verificar si el tipo de archivo real está en la lista de tipos permitidos
    if tipo_real not in MIMETYPES_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no permitido ({tipo_real}). Solo se aceptan PDF, JPG o PNG."
        )

    # Generar un identificador único para el archivo y un nombre interno basado en el tipo de archivo
    file_id = str(uuid.uuid4())

    # Guardar el archivo f
    nombre_interno = (
        file_id +
        MIMETYPES_PERMITIDOS[tipo_real]
    )
    # la carpeta sale del .env (UPLOAD_DIR) para usar el volumen de Railway
    UPLOAD_DIR = Path(config.UPLOAD_DIR)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    ruta_archivo = UPLOAD_DIR / nombre_interno

    with open(ruta_archivo, "wb") as archivo:
        archivo.write(contenido)
        
    hash_sha256 = hashlib.sha256(contenido).hexdigest()

    nuevo_archivo = Archivo(
        nombre_original=file.filename,
        nombre_interno=nombre_interno,
        tipo_mime=tipo_real,
        tamano_bytes=len(contenido),
        hash_sha256=hash_sha256,
        ubicacion=str(ruta_archivo),
        autor_id=usuario_actual.id
    )

    db.add(nuevo_archivo)
    db.commit()
    db.refresh(nuevo_archivo)
    
    # devolver el identificador único y el nombre interno del archivo
    return {
        "file_id": nuevo_archivo.id,
        "nombre_interno": nombre_interno
    }
    



@router.get("/{id}")
async def descargar_archivo(
    id: int,
    usuario_actual: Usuario = Depends(obtener_usuario_actual),
    db: Session = Depends(get_db)
):

    # un archivo eliminado se trata como si no existiera
    registro = db.query(Archivo).filter(
        Archivo.id == id,
        Archivo.eliminado_en.is_(None)
    ).first()

    if registro is None:
        raise HTTPException(
            status_code=404,
            detail="Archivo no encontrado"
        )

    # descarga el dueño, el admin o un rol que no sea docente con files.download
    # (revisor, coordinacion, autoridad, auditoria), segun la matriz del Grupo 1
    puede_descargar = any(
        rol.codigo == "admin"
        or (rol.codigo != "teacher" and any(p.codigo == "files.download" for p in rol.permisos))
        for rol in usuario_actual.roles
    )

    if registro.autor_id != usuario_actual.id and not puede_descargar:
        raise HTTPException(
        status_code=403,
        detail="No tienes permiso para acceder a este archivo"
    )

    ruta = Path(registro.ubicacion)

    if not ruta.exists():
        raise HTTPException(
            status_code=404,
            detail="Archivo no encontrado en almacenamiento"
        )

    return FileResponse(
        path=str(ruta),
        filename=registro.nombre_original
    )
