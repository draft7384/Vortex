"""
Schemas Pydantic del modulo Aplicaciones CxC.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================
# REQUEST
# ============================================================

class AplicacionCxcCreateRequest(BaseModel):
    """Aplicacion manual entre dos movimientos (no usada en POST /pagos)."""
    movimiento_pago_id: int = Field(..., gt=0)
    movimiento_deuda_id: int = Field(..., gt=0)
    monto_aplicado: float = Field(..., gt=0)
    observaciones: Optional[str] = Field(None, max_length=500)


class AplicacionCxcReverseRequest(BaseModel):
    """Body para reversar una aplicacion (POST /aplicaciones-cxc/{id}/reversar)."""
    motivo: str = Field(..., min_length=5, max_length=500)


# ============================================================
# RESPONSE
# ============================================================

class AplicacionCxcResponse(BaseModel):
    id: int
    movimiento_pago_id: int
    movimiento_deuda_id: int
    monto_aplicado_original: float
    monto_aplicado_local: float
    fecha_aplicacion: datetime
    aplicado_por: int
    reversada: bool = False
    reversada_por: Optional[int] = None
    reversada_en: Optional[datetime] = None
    motivo_reverso: Optional[str] = None
