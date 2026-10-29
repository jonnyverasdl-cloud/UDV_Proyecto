"""Funciones de la API de G5 para programas, versiones y documentos."""


def __getattr__(name):
    """Carga el router cuando hace falta, en vez de importarlo desde el inicio."""
    if name == "router":
        from .router import router

        return router
    raise AttributeError(name)


__all__ = ["router"]
