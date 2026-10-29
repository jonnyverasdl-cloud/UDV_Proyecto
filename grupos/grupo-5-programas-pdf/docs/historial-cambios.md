# Historial de cambios del proyecto

Este documento resume la evolución anterior del proyecto según el historial de
Git. Cubre los cambios registrados desde el 7 hasta el 27 de octubre de 2026;
no incluye la actualización de documentación realizada el 28 de octubre.

## 7 de octubre — Primera versión

- Se creó el prototipo inicial con una página web para el programa de curso,
  estilos y lógica JavaScript.
- Se agregó un backend inicial en `backend/main.py` y el archivo
  `programas.json` para trabajar con los datos del programa.
- Se incorporaron el formulario PDF de referencia y el primer documento de
  flujo.
- Se añadieron reglas de Git para excluir archivos generados y del sistema,
  como `.DS_Store`.

## 8 al 13 de octubre — Evolución del prototipo

- Se ajustaron la interfaz, el formulario y sus estilos.
- Se amplió la lógica del frontend para gestionar el flujo del programa y los
  datos guardados en `programas.json`.
- Se modificaron las instrucciones del flujo y la documentación del proyecto.
- Se retiró el PDF de formulario que se había agregado como referencia.

## 21 de octubre — Separación de responsabilidades

- Se reorganizó el backend en módulos de aplicación, configuración,
  almacenamiento, validación e historial.
- Se trasladó la generación de PDF a `backend/pdf_service.py`.
- Se renombró `frontend/Demo.html` como `frontend/Programa.html`.
- Se actualizaron el documento de flujo y la descripción del proyecto.

## 23 de octubre — Módulo G5 y API

- Se estableció el paquete `g5_programas` con router FastAPI, autenticación,
  acceso a base de datos, reglas de dominio, errores y repositorio.
- Se implementaron operaciones de programas y versiones, validación de
  estados y permisos, y generación de PDF.
- Se renovaron las pantallas, estilos y lógica JavaScript del frontend para
  trabajar con la API.
- Se incorporaron pruebas para el flujo de estados y los permisos.
- Se añadieron variables de entorno de ejemplo y se empezó a documentar la
  arquitectura en `docs/`.

## 24 de octubre — Documentación y dependencias

- Se revisaron `docs/README.md`, `docs/overview.md` y `docs/workflow.md` para
  describir la organización del proyecto y su proceso de trabajo.
- Se ajustó la ubicación de `requirements.txt` durante la organización del
  módulo, y posteriormente se centralizaron las dependencias en la raíz.
- Se añadió una representación de la estructura de archivos al README de
  documentación.

## 27 de octubre — Reorganización del repositorio

- Se movió `g5_programas` desde el subdirectorio del grupo a la raíz del
  repositorio.
- Se integró la generación de PDF en el paquete G5.
- Se eliminó el backend anterior y el punto de entrada local (`main.py`), de
  modo que el módulo quedó orientado a integrarse en una aplicación FastAPI
  compartida.
- Se actualizaron las pruebas y la documentación para reflejar la ubicación
  nueva de los archivos.

## Estado resultante al 27 de octubre

El proyecto quedó organizado como un módulo FastAPI integrable, acompañado
por una interfaz web y pruebas de las reglas principales. La API utiliza el
esquema de base de datos compartido y depende de una aplicación host para
registrar el router, proporcionar la sesión autenticada y ejecutar el servicio.
