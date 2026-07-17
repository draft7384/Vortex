"""
Schemas Pydantic del modulo Tasas de Cambio.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class TasaCambioCreateRequest(BaseModel):
    """Payload para registrar una tasa (POST /tasas-cambio)."""
    moneda_id: int = Field(..., gt=0)
    fecha: date = Field(default_factory=date.today)
    tasa: float = Field(..., gt=0, description="Cuanta moneda local vale 1 unidad de la moneda")


class TasaCambioUpdateRequest(BaseModel):
    """Payload para actualizar una tasa (PUT /tasas-cambio/{id})."""
    tasa: Optional[float] = Field(None, gt=0)


class TasaCambioResponse(BaseModel):
    id: int
    moneda_id: int
    fecha: date
    tasa: float
