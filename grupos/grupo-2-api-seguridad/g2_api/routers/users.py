
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import bcrypt
from g2_api.routers.auth import usuarios
from g2_api.middleware.auth_middleware import requerir_rol

router = APIRouter(prefix="/api/v1/users", tags=["Users and Roles"])

class UsuarioCreate(BaseModel):
    id: int
    usuario: str
    correo: str
    password: str
    rol: str
    activo: bool = True

class UsuarioUpdate(BaseModel):
    usuario: Optional[str] = None
    correo: Optional[str] = None
    password: Optional[str] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None

@router.get("/", dependencies=[Depends(requerir_rol(["administrador"]))]) #Endpoint para buscar usuarios 
def listar_usuarios():
    lista_limpia = []
    for u in usuarios: 
        copia = u.copy() #Copia elementos u
        copia.pop("password", None) #elimina la password
        copia.pop("hash_contrasena", None) #tampoco se devuelve el hash
        lista_limpia.append(copia) #en la variable lista limpia, guarda el usuario sin la contraseña
    return lista_limpia

@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(requerir_rol(["administrador"]))]) #Crea usuarios 
def crear_usuario(datos: UsuarioCreate): #recibe parámetro tipo class
    for u in usuarios:
        if u.get("correo") == datos.correo or u.get("id") == datos.id: #Compara el correo y el id del usuario
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El ID o correo ya se encuentra registrado" #si los datos son iguales no acepta la creación  del usuario
            )
    #si no existe el usuario guarda la contraseña usando el método hash y los demás datos
    password_hash = bcrypt.hashpw(datos.password.encode(), bcrypt.gensalt()).decode('utf-8') 
    
    
    nuevo_usuario = {
        "id": datos.id,
        "usuario": datos.usuario, 
        "correo": datos.correo,
        "hash_contrasena": password_hash,  # mismo campo que lee el login
        "roles": [datos.rol],  # lista, igual que el JSON de prueba
        "activo": datos.activo
    }
    
    usuarios.append(nuevo_usuario)
    
    respuesta = nuevo_usuario.copy()
    respuesta.pop("hash_contrasena", None) #Regresa los datos del usuario que se está creando sin la contraseña
    return respuesta

@router.patch("/{usuario_id}", dependencies=[Depends(requerir_rol(["administrador"]))]) 
def actualizar_o_desactivar_usuario(usuario_id: int, datos: UsuarioUpdate):
    usuario_encontrado = None
    for u in usuarios:
        if u.get("id") == usuario_id: #compara ids
            usuario_encontrado = u
            break
            
    if not usuario_encontrado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, #si el usuario no está, lanza un error
            detail="Usuario no encontrado"
        )
        
    cambios = datos.model_dump(exclude_unset=True) #convierte datos que es un basemodel en un diccionario
    
    #si se actualizó la contraseña, se cambia el input por un hash
    if "password" in cambios:
        cambios["hash_contrasena"] = bcrypt.hashpw(cambios.pop("password").encode(), bcrypt.gensalt()).decode('utf-8')
    if "rol" in cambios:
        cambios["roles"] = [cambios.pop("rol")]
        
    usuario_encontrado.update(cambios) #actualiza los datos
    #retorna los datos a excepción de la password
    respuesta = usuario_encontrado.copy()
    respuesta.pop("hash_contrasena", None)
    return respuesta
