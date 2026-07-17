"""
Schemas Pydantic del modulo Monedas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class MonedaCreateRequest(BaseModel):
    """Payload para crear una moneda (POST /monedas)."""
    codigo_iso: str = Field(..., min_length=3, max_length=3, description="Codigo ISO 4217: VES, USD, EUR, COP, etc.")
    nombre: str = Field(..., min_length=1, max_length=50)
    simbolo: str = Field(..., min_length=1, max_length=10)
    decimales: int = Field(2, ge=0, le=6)
    es_moneda_local: bool = Field(False, description="Solo UNA moneda puede tener TRUE (constraint DB lo bloquea)")
    activo: bool = True


class MonedaUpdateRequest(BaseModel):
    """Payload para actualizar una moneda (PUT /monedas/{id})."""
    codigo_iso: Optional[str] = Field(None, min_length=3, max_length=3)
    nombre: Optional[str] = Field(None, min_length=1, max_length=50)
    simbolo: Optional[str] = Field(None, min_length=1, max_length=10)
    decimales: Optional[int] = Field(None, ge=0, le=6)
    es_moneda_local: Optional[bool] = None
    activo: Optional[bool] = None


class MonedaResponse(BaseModel):
    id: int
    codigo_iso: str
    nombre: str
    simbolo: str
    decimales: int
    es_moneda_local: bool
    activo: bool
