#Libreria para anotar los endpoints
from fastapi import APIRouter, HTTPException, status
router = APIRouter(prefix="/api/v1/auth", tags=["Autenticacion"])

import bcrypt

#Herramienta para leer json temporalmente
import json
import os

#Buscara la ruta del archivo usuarios_prueba.json en la carpeta g2_api/datos_prueba
#Temporal: cuando el Grupo 1 entregue la base de datos, se cambia por la conexion real
ruta_actual = os.path.dirname(__file__)
ruta_json = os.path.join(ruta_actual, "..", "datos_prueba", "usuarios_prueba.json")

with open(ruta_json, "r", encoding="utf-8") as archivo:
    datos = json.load(archivo)

usuarios = datos["usuarios"]

#Definir qué datos recibe el login, si correo o contraseña no son str lo rechaza
from pydantic import BaseModel

class LoginRequest(BaseModel):
    correo: str
    password: str

#El endpoint POST /api/v1/auth/login
@router.post("/login")
def login(datos_login: LoginRequest): #Recibimos los datos de LoginRequest
    usuario_encontrado = None
    for usuario in usuarios: # buscamos el usuario en la lista de usuarios
        if usuario["correo"] == datos_login.correo:
            usuario_encontrado = usuario
            break

    if usuario_encontrado is None: #si no encuentra el usuario responde 401
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")

    #comparacion de contraseña con el hash guardado
    contraseña_correcta = bcrypt.checkpw(
        datos_login.password.encode(),
        usuario_encontrado["hash_contrasena"].encode()
    )

    if not contraseña_correcta:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")

    return {
        "mensaje": "Login exitoso",
        "id": usuario_encontrado["id"],
        "correo": usuario_encontrado["correo"],
        "roles": usuario_encontrado["roles"]
    }
