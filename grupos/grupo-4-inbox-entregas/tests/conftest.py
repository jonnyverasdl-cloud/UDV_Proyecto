"""Se ejecuta antes que cualquier prueba.

En la app integrada G4 lee de MySQL por defecto. Las pruebas, en cambio,
corren con los datos de ejemplo en memoria (no necesitan base de datos), así
que aquí se apaga MySQL ANTES de que se importe g4_inbox.routes.

Para probar contra una base real hay un módulo aparte: test_mysql.py.
"""
import os

os.environ["G4_USAR_MYSQL"] = "0"
