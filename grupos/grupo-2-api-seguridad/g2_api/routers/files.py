import uuid # <----- Nombre interno aleatorio del archivo
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
import puremagic # <----- Dependencia Para verificar el tipo de archivo
from g2_api.middleware.auth_middleware import obtener_usuario_actual
from g2_api.models import Usuario
from pathlib import Path
from fastapi.responses import FileResponse

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
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
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
            detail={"error": "Archivo invlálido", "mensaje": "No se pudo determinar el tipo de archivo. Asegúrese de que el archivo no esté corrupto y sea un archivo válido."}
        )

    # Verificar si el tipo de archivo real está en la lista de tipos permitidos
    if tipo_real not in MIMETYPES_PERMITIDOS:
        raise HTTPException(
            status_code=400,
            detail={"error": "formato no permitido",
                    "mensaje": f"El archivo tiene un formato real de tipo '{tipo_real}'. Solo se permiten los siguientes formatos: {', '.join(MIMETYPES_PERMITIDOS.keys())}."
                    }
        )

    # Generar un identificador único para el archivo y un nombre interno basado en el tipo de archivo
    file_id = str(uuid.uuid4())

    nombre_interno = (
        file_id +
        MIMETYPES_PERMITIDOS[tipo_real]
    )
    UPLOAD_DIR = Path("uploads")
    UPLOAD_DIR.mkdir(exist_ok=True)

    ruta_archivo = UPLOAD_DIR / nombre_interno

    with open(ruta_archivo, "wb") as archivo:
        archivo.write(contenido)
    # devolver el identificador único y el nombre interno del archivo
    return {
        "file_id": file_id,
        "nombre_interno": nombre_interno,
        "usuario": usuario_actual.correo
    }
    


@router.get("/{id}")
async def descargar_archivo(
    file_id: str,
    usuario_actual: Usuario = Depends(obtener_usuario_actual)
):

    carpeta = Path("uploads")
    
    if not carpeta.exists():
        raise HTTPException(
        status_code=404,
        detail="No existen archivos almacenados"
    )

    for archivo in carpeta.iterdir():
        if archivo.name.startswith(file_id):
            return FileResponse(
                path=archivo,
                filename=archivo.name
            )

    raise HTTPException(
        status_code=404,
        detail="Archivo no encontrado"
    )
# El archivo es validado y almacenado localmente
# usando un nombre interno generado de forma aleatoria.
