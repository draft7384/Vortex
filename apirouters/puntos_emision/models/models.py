"""
Schemas Pydantic del modulo Puntos de Emision.
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class PuntoEmisionCreateRequest(BaseModel):
    """Payload para crear un punto de emision (POST /puntos-emision)."""
    codigo: str = Field(..., min_length=1, max_length=20, description="Codigo unico: S001, S001-C1, S002-C1, etc.")
    nombre: str = Field(..., min_length=1, max_length=100)
    tipo: Literal["SUCURSAL", "CAJA", "DEPOSITO"] = "SUCURSAL"
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=50)
    activo: bool = True


class PuntoEmisionUpdateRequest(BaseModel):
    codigo: Optional[str] = Field(None, max_length=20)
    nombre: Optional[str] = Field(None, max_length=100)
    tipo: Optional[Literal["SUCURSAL", "CAJA", "DEPOSITO"]] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=50)
    activo: Optional[bool] = None


class PuntoEmisionResponse(BaseModel):
    id: int
    codigo: str
    nombre: str
    tipo: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    activo: bool
    creado_en: Optional[str] = None
