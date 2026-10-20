
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from g2_api.routers.auth import usuarios
from g2_api.seguridad import verificar_token

control_bearer = HTTPBearer(auto_error= False)

def no_esta_autenticado(detalle: str):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, #Definición de funcion para el error de unauthorized
        detail=detalle,
        headers={"WWW-Authenticate": "Bearer"},
    )
    
def obtener_usuario_actual(credenciales: HTTPAuthorizationCredentials | None = Depends(control_bearer),):
    if credenciales is None:
        raise no_esta_autenticado("El token de autentication es el que falta")
    payload = verificar_token(credenciales.credentials)
    if payload is None:
        raise no_esta_autenticado("El Token es invalido o está expirado")
    
    try:
        id_usuario = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise no_esta_autenticado("El token es inválido")
    
    for u in usuarios:
        if u.get("id") == id_usuario:
            return u
    
    raise no_esta_autenticado("El usuario no está autenticado o no se encontró ")
    
def requerir_rol(roles_permitidos: list[str]): #recibe un parámetro tipo lista de los roles permitidos
    def verificacion(usuario_actual: dict = Depends(obtener_usuario_actual)): #Obtiene la varaible de la función de arriba
        if not usuario_actual.get("activo", True):  #verifica si el usuario está activo
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="El usuario se encuentra inactivo"
            )
        
        roles_usuario = usuario_actual.get("roles", [])  # en el JSON es una lista
        if not any(r in roles_permitidos for r in roles_usuario): #Compara si el usuario actual tiene permiso para ingresar
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos necesarios para realizar esta acción"
            )
        
        return usuario_actual

    return verificacion
