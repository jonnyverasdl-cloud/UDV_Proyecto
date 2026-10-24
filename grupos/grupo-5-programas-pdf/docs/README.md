# Programas de curso UDV

Aplicación para gestionar programas de curso, sus versiones y el flujo de revisión hasta la generación del PDF institucional.

## Estructura del Proyecto

```text
grupo-5-programas-pdf/
├── backend/                ← Lógica de la API y servicios de PDF
├── frontend/               ← Interfaz web y recursos estáticos
├── grupos/
│   └── grupo-5-programas-pdf/
│       ├── g5_programas/   ← Código core del módulo (paquete Python)
│       └── requirements.txt ← dependencias propias del grupo
├── tests/                  ← Pruebas automatizadas de transiciones
├── docs/                   ← Guías, flujo y documentación
├── main.py                 ← Punto de entrada para Uvicorn
└── .env.example           ← Plantilla de configuración de entorno
```

## Arranque rápido
1. Configure `.env` con su `DATABASE_URL`.
2. Instale dependencias: `pip install -r grupos/grupo-5-programas-pdf/requirements.txt`.
3. Ejecute: `uvicorn main:app --reload --env-file .env`.

API Docs: `/api/v1/docs` | Interfaz: `/`
