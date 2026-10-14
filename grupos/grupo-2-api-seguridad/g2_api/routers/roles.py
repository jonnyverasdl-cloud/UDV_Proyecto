from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from g2_api.middleware.auth_middleware import obtener_usuario_actual, requerir_rol

router = APIRouter(prefix="/api/v1/roles", tags=["Roles"])
#lista de los roles, esperando el db
roles = [
    {"id": 1, "rol": "administrador", "nombre": "Administrador",
     "descripcion": "acceso completo", "activo": True},
    {"id": 2, "rol": "coordinador ", "nombre": "Coordinador",
     "descripcion": "Crear tareas", "activo": True},
    {"id": 3, "rol": "docente", "nombre": "Docente",
     "descripcion": "Completar tareas", "activo": True},
    {"id": 4, "rol": "revisor", "nombre": "Revisor",
     "descripcion": "Revisar tareas", "activo": True},
    {"id": 5, "rol": "autoridadacadémica", "nombre": "Autoridad Académica",
     "descripcion": "Autorizar programa", "activo": True},
    {"id": 6, "rol": "auditor", "nombre": "Auditor",
     "descripcion": "Consultar historial", "activo": True}
]

class RolCreate(BaseModel):
    rol: str
    nombre: str
    descripcion: Optional[str] = None
#esto lista los roles
@router.get("/")
def lista_roles(usuario_actual: dict = Depends(obtener_usuario_actual)):
    return roles
#este método crea los roles
@router.post("/", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(requerir_rol(["administrador"]))])
def crea_rol(datos: RolCreate):
    if any(r["rol"] == datos.rol for r in roles):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Este rol ya existe") #si el rol ya existe, no lo crea

    nuevo = {
        "id": max((r["id"] for r in roles), default=0) + 1,  #aquí es donde se crea un id automáticamente para cada rol nuevo
        "rol": datos.rol,
        "nombre": datos.nombre,
        "descripcion": datos.descripcion,
        "activo": True,
    }
    
    roles.append(nuevo) #y se guarda el nuevo rol en memoria por ahora
    return nuevo 