"""
Schemas Pydantic del modulo Empresa (singleton).
Solo hay una fila (id=1) con los datos fiscales del emisor.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class EmpresaConfigRequest(BaseModel):
    """Payload para inicializar/actualizar la config de la empresa (POST/PUT /empresa-config)."""
    rif: str = Field(..., min_length=4, max_length=20)
    nombre_razon_social: str = Field(..., min_length=1, max_length=255)
    nombre_comercial: Optional[str] = Field(None, max_length=255)
    direccion_fiscal: str = Field(..., min_length=1)
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    sitio_web: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None
    serial_imprenta: Optional[str] = Field(None, max_length=50)
    rango_factura_desde: Optional[int] = Field(None, ge=0)
    rango_factura_hasta: Optional[int] = Field(None, ge=0)
    rango_nc_desde: Optional[int] = Field(None, ge=0)
    rango_nc_hasta: Optional[int] = Field(None, ge=0)
    rango_nd_desde: Optional[int] = Field(None, ge=0)
    rango_nd_hasta: Optional[int] = Field(None, ge=0)


class EmpresaConfigResponse(BaseModel):
    id: int
    rif: str
    nombre_razon_social: str
    nombre_comercial: Optional[str] = None
    direccion_fiscal: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    sitio_web: Optional[str] = None
    logo_url: Optional[str] = None
    serial_imprenta: Optional[str] = None
    rango_factura_desde: Optional[int] = None
    rango_factura_hasta: Optional[int] = None
    rango_nc_desde: Optional[int] = None
    rango_nc_hasta: Optional[int] = None
    rango_nd_desde: Optional[int] = None
    rango_nd_hasta: Optional[int] = None
    actualizado_en: Optional[str] = None
