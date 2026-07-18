"""
Schemas Pydantic del modulo Productos.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductoCreateRequest(BaseModel):
    """Payload para crear un producto (POST /productos)."""
    codigo: str = Field(..., min_length=1, max_length=30)
    descripcion: str = Field(..., min_length=1, max_length=255)
    unidad_medida: str = Field("UND", max_length=10)
    precio_base: float = Field(..., ge=0)
    impuesto_pct: float = Field(16.00, ge=0, le=100, description="Porcentaje de IVA (0-100)")
    existencia: float = Field(0.00, ge=0, description="Cantidad en stock")
    es_servicio: bool = Field(False, description="Si TRUE no descuenta existencia al facturar")

    # Campos de Shopify (preparacion para sync futura)
    shopify_id: Optional[int] = None
    shopify_handle: Optional[str] = Field(None, max_length=255)
    shopify_status: Optional[str] = Field("active", max_length=50)
    shopify_product_type: Optional[str] = Field(None, max_length=255)
    shopify_tags: Optional[str] = None
    shopify_image_url: Optional[str] = None

    activo: bool = True


class ProductoUpdateRequest(BaseModel):
    codigo: Optional[str] = Field(None, max_length=30)
    descripcion: Optional[str] = Field(None, max_length=255)
    unidad_medida: Optional[str] = Field(None, max_length=10)
    precio_base: Optional[float] = Field(None, ge=0)
    impuesto_pct: Optional[float] = Field(None, ge=0, le=100)
    existencia: Optional[float] = Field(None, ge=0)
    es_servicio: Optional[bool] = None
    shopify_id: Optional[int] = None
    shopify_handle: Optional[str] = Field(None, max_length=255)
    shopify_status: Optional[str] = Field(None, max_length=50)
    shopify_product_type: Optional[str] = Field(None, max_length=255)
    shopify_tags: Optional[str] = None
    shopify_image_url: Optional[str] = None
    activo: Optional[bool] = None


class ProductoResponse(BaseModel):
    id: int
    codigo: str
    descripcion: str
    unidad_medida: str
    precio_base: float
    impuesto_pct: float
    existencia: float
    es_servicio: bool
    activo: bool
    shopify_id: Optional[int] = None
    shopify_handle: Optional[str] = None
    shopify_status: Optional[str] = None
    shopify_product_type: Optional[str] = None
    shopify_tags: Optional[str] = None
    shopify_image_url: Optional[str] = None
    actualizado_en: Optional[datetime] = None


class ProductoListItem(BaseModel):
    id: int
    codigo: str
    descripcion: str
    precio_base: float
    impuesto_pct: float
    existencia: float
    es_servicio: bool
    activo: bool


class ProductoImportItem(BaseModel):
    """Schema para importacion masiva desde Excel."""
    codigo: str
    descripcion: str
    unidad_medida: Optional[str] = "UND"
    precio_base: float
    impuesto_pct: Optional[float] = 16.0
    existencia: Optional[float] = 0.0
    es_servicio: Optional[bool] = False


class ProductoImportResponse(BaseModel):
    """Respuesta de importacion masiva."""
    total_registros: int
    exitosos: int
    fallidos: int
    errores: List[dict]
