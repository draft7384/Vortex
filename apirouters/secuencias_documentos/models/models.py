"""
Schemas Pydantic del modulo Secuencias de Documentos.
Define el correlativo por (punto_emision, tipo_documento).
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


TipoDocumentoLiteral = Literal["FACTURA", "NOTA_ENTREGA", "PRESUPUESTO", "PEDIDO", "NOTA_CREDITO", "NOTA_DEBITO"]


class SecuenciaCreateRequest(BaseModel):
    """Payload para crear una secuencia (POST /secuencias-documentos)."""
    punto_emision_id: int = Field(..., gt=0)
    tipo_documento: TipoDocumentoLiteral
    prefijo: str = Field(..., min_length=1, max_length=10, description="FAC, NC, ND, NE, PRES, PED")
    proximo_numero: int = Field(1, ge=1)
    numero_actual: int = Field(0, ge=0)
    activo: bool = True


class SecuenciaUpdateRequest(BaseModel):
    prefijo: Optional[str] = Field(None, max_length=10)
    proximo_numero: Optional[int] = Field(None, ge=1)
    numero_actual: Optional[int] = Field(None, ge=0)
    activo: Optional[bool] = None


class SecuenciaResponse(BaseModel):
    id: int
    punto_emision_id: int
    tipo_documento: str
    prefijo: str
    proximo_numero: int
    numero_actual: int
    activo: bool


class InicializarSecuenciasRequest(BaseModel):
    """Para crear las 6 secuencias estandar de un punto de emision de una sola vez."""
    punto_emision_id: int = Field(..., gt=0)
