"""
Schemas Pydantic del modulo Parametros del Sistema.
Los valores se manejan como JSON generico (cualquier estructura).
"""
from pydantic import BaseModel, Field
from typing import Any, Optional


class ParametroCreateRequest(BaseModel):
    """Payload para crear un parametro (POST /parametros-sistema)."""
    clave: str = Field(..., min_length=1, max_length=100)
    valor: Any = Field(..., description="Valor JSON generico (numero, string, lista, dict, bool)")
    descripcion: Optional[str] = None


class ParametroUpdateRequest(BaseModel):
    """Payload para actualizar un parametro (PUT /parametros-sistema/{clave})."""
    valor: Any = Field(..., description="Nuevo valor JSON")
    descripcion: Optional[str] = None


class ParametroResponse(BaseModel):
    clave: str
    valor: Any
    descripcion: Optional[str] = None
    actualizado_en: Optional[str] = None
