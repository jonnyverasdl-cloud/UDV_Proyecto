
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from g2_api.database import get_db
from typing import Optional
import bcrypt
from g2_api.middleware.auth_middleware import requerir_rol
from g2_api.models import Rol, Usuario, UsuarioRol
from g2_api.routers.auth import obtener_usuario_actual
from g2_api.database import fijar_actor
from g2_api.utils.paginacion import params_paginacion, Paginacion, paginar

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

class UsuarioCreate(BaseModel):
    nombres: str
    apellidos: str
    correo: str
    password: str
    rol: str
    activo:bool = True

class UsuarioUpdate(BaseModel):
    nombres: Optional[str] = None
    apellidos: Optional[str] = None
    correo: Optional[str] = None
    password: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None
    
    
def diccionario(u: Usuario) -> dict:
    return {
        "id": u.id,
        "correo": u.correo,
        "nombres": u.nombres,
        "apellidos": u.apellidos,
        "activo": u.activo,
        "roles": [i.codigo for i in u.roles]
    }


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")

def _buscar_usuario(db: Session, usuario_id: int) -> Usuario:
    u = db.get(Usuario, usuario_id)
    if u is None or u.eliminado_en is not None:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="El usuario no se encontró o no existe"
        )
    return u
    
    
def _buscar_rol(db: Session, codigo: str) -> Rol:
    rol = db.query(Rol).filter(Rol.codigo == codigo, Rol.activo.is_(True)).first()
    if rol is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El rol indicado no existe"
        )
    return rol


def _correo_repetido():
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="El correo ya está registrado"
    )
    

@router.get("", dependencies=[Depends(requerir_rol(["admin"]))]) #Endpoint para buscar usuarios 
def listar_usuarios(paginacion: Paginacion =Depends(params_paginacion), db: Session = Depends(get_db)):
    
    consultas = (
        db.query(Usuario)
        .options(selectinload(Usuario.roles))
        .filter(Usuario.eliminado_en.is_(None))
        .order_by(Usuario.id)
    )
    
    return paginar(consultas, paginacion.page, paginacion.per_page, diccionario)


@router.get("/{usuario_id}", dependencies=[Depends(requerir_rol(["admin"]))])
def obtiene_usuario(usuario_id: int, db: Session = Depends(get_db)):
    return diccionario(_buscar_usuario(db, usuario_id))


@router.post("", status_code=status.HTTP_201_CREATED, dependencies=[Depends(requerir_rol(["admin"]))]) #Crea usuarios 
def crear_usuario(datos: UsuarioCreate, db: Session = Depends(get_db), actual: Usuario = Depends(obtener_usuario_actual)): #recibe parámetro tipo class
    if db.query(Usuario).filter(Usuario.correo == datos.correo).first():
        raise _correo_repetido()
    
    
    rol = _buscar_rol(db, datos.rol)
    
    nuevo = Usuario(
        correo=datos.correo,
        nombres=datos.nombres,
        apellidos=datos.apellidos,
        hash_contrasena=_hash(datos.password),
        activo=datos.activo
    )
    
    fijar_actor(db, actual.id)
    
    try:
        db.add(nuevo)
        db.flush()
        db.add(UsuarioRol(usuario_id=nuevo.id, rol_id=rol.id, asignado_por=actual.id))
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if "correo" in str(e.orig).lower():
            raise _correo_repetido()
        raise   
    
    db.refresh(nuevo)
    return diccionario(nuevo)
        

@router.patch("/{usuario_id}", dependencies=[Depends(requerir_rol(["admin"]))]) 
def actualizar_o_desactivar_usuario(usuario_id: int, datos: UsuarioUpdate, db: Session = Depends(get_db), 
                                    actual: Usuario = Depends(obtener_usuario_actual)):
    
    fijar_actor(db, actual.id)
    u = _buscar_usuario(db, usuario_id)
    
    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    
    if "correo" in cambios and cambios["correo"] != u.correo:
        if db.query(Usuario).filter(Usuario.correo == cambios["correo"]).first():
            raise _correo_repetido()
    
    if "password" in cambios:
        u.hash_contrasena = _hash(cambios.pop("password"))
        
    if "rol" in cambios:
        rol = _buscar_rol(db, cambios.pop("rol"))
        db.query(UsuarioRol).filter(UsuarioRol.usuario_id == u.id).delete()
        db.add(UsuarioRol(usuario_id=u.id, rol_id=rol.id, asignado_por=actual.id))
        
    for campo, valor in cambios.items():
        setattr(u, campo, valor)
        
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise _correo_repetido()
    
    db.refresh(u)
    return diccionario(u)
        
        