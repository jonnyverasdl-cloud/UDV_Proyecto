from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from g2_api.database import get_db

from g2_api.models import Rol, Usuario
from g2_api.routers.auth import obtener_usuario_actual
from g2_api.middleware.auth_middleware import requerir_rol



router = APIRouter(prefix="/api/v1/roles", tags=["Roles"])

class RolCreate(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    

def _diccionario(r: Rol) -> dict: 
    return {"id": r.id, "codigo": r.codigo, "nombre":r.nombre,
            "descripcion": r.descripcion, "activo": r.activo}
    
def _rol_es_repetido():
    return HTTPException(status.HTTP_409_CONFLICT, detail="Este rol ya existe")
    
#esto lista los roles
@router.get("")
def lista_roles(usuario_actual: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    
    return [_diccionario(i) for i in db.query(Rol).order_by(Rol.id).all()]


#este método crea los roles
@router.post("", status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(requerir_rol(["admin"]))])
def crea_rol(datos: RolCreate, db: Session = Depends(get_db)):
    
    if db.query(Rol).filter(Rol.codigo == datos.codigo).first():
        raise _rol_es_repetido()
    nuevo = Rol(codigo=datos.codigo, nombre=datos.nombre, descripcion=datos.descripcion)
    
    try:
        db.add(nuevo)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _rol_es_repetido()
    
    db.refresh(nuevo)
    return _diccionario(nuevo)