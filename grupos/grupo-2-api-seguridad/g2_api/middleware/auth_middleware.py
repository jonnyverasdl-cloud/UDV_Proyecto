
from fastapi import  Depends, HTTPException, status
from g2_api.models import Usuario
from g2_api.routers.auth import obtener_usuario_actual


def requerir_rol(roles_permitidos: list[str]): #recibe un parámetro tipo lista de los roles permitidos
    def verificacion(usuario_actual: Usuario = Depends(obtener_usuario_actual)): #Obtiene la varaible de la función de arriba
        roles_usuario = [i.codigo for i in usuario_actual.roles] 
       
        if not any(j in roles_permitidos for j in roles_usuario): #Compara si el usuario actual tiene permiso para ingresar
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos necesarios para realizar esta acción"
            )
        
        return usuario_actual

    return verificacion
