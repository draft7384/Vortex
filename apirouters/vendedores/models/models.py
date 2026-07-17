"""
Schemas Pydantic del modulo Vendedores.
"""
from pydantic import BaseModel, Field
from typing import Optional


class VendedorCreateRequest(BaseModel):
    """Payload para crear un vendedor (POST /vendedores)."""
    codigo: str = Field(..., min_length=1, max_length=20)
    usuario_id: Optional[int] = Field(None, gt=0, description="Vinculacion opcional con un usuario del sistema")
    nombre: str = Field(..., min_length=1, max_length=100)
    comision_pct: float = Field(0.00, ge=0, le=100, description="Porcentaje de comision (0-100)")
    activo: bool = True


class VendedorUpdateRequest(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    usuario_id: Optional[int] = Field(None, gt=0)
    nombre: Optional[str] = Field(None, max_length=100)
    comision_pct: Optional[float] = Field(None, ge=0, le=100)
    activo: Optional[bool] = None


class VendedorResponse(BaseModel):
    id: int
    codigo: str
    usuario_id: Optional[int] = None
    nombre: str
    comision_pct: float
    activo: bool


class VendedorListItem(BaseModel):
    id: int
    codigo: str
    nombre: str
    comision_pct: float
    activo: bool
