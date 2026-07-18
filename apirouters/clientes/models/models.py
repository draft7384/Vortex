"""
Schemas Pydantic (entrada y salida) del módulo Clientes.
NO usamos ORM: estos modelos validan payloads y dan forma a las respuestas.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime


# ============== REQUEST (entrada) ==============

class ClienteCreateRequest(BaseModel):
    """Payload para crear un cliente (POST /clientes)."""
    codigo: str = Field(..., min_length=1, max_length=20)
    rif: str = Field(..., min_length=4, max_length=20, description="Formato venezolano: J-123456789, V-12345678, E-..., G-...")
    nombre_razon_social: str = Field(..., min_length=1, max_length=255)
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    condicion_pago: str = Field("CONTADO", description="CONTADO | CREDITO | ANTICIPO")
    limite_credito: float = Field(0.00, ge=0)
    regimen_iva: str = Field("ORDINARIO", description="ORDINARIO | ESPECIAL | AGENTE")
    es_contribuyente_especial: bool = False
    numero_contribuyente_especial: Optional[str] = Field(None, max_length=30)
    moneda_id: Optional[int] = None


class ClienteUpdateRequest(BaseModel):
    """Payload para actualizar un cliente (PUT /clientes/{id})."""
    codigo: Optional[str] = Field(None, max_length=20)
    rif: Optional[str] = Field(None, max_length=20)
    nombre_razon_social: Optional[str] = Field(None, max_length=255)
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    condicion_pago: Optional[str] = None
    limite_credito: Optional[float] = Field(None, ge=0)
    regimen_iva: Optional[str] = None
    es_contribuyente_especial: Optional[bool] = None
    numero_contribuyente_especial: Optional[str] = None
    moneda_id: Optional[int] = None
    activo: Optional[bool] = None


class ClienteImportItem(BaseModel):
    """Item individual para importación masiva desde Excel."""
    codigo: str = Field(..., min_length=1, max_length=20)
    rif: str = Field(..., min_length=4, max_length=20)
    nombre_razon_social: str = Field(..., min_length=1, max_length=255)
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    condicion_pago: str = Field("CONTADO", description="CONTADO | CREDITO | ANTICIPO")
    limite_credito: float = Field(0.00, ge=0)
    regimen_iva: str = Field("ORDINARIO", description="ORDINARIO | ESPECIAL")
    es_contribuyente_especial: bool = False
    numero_contribuyente_especial: Optional[str] = None
    moneda_id: Optional[int] = None


class ClienteImportResponse(BaseModel):
    """Respuesta de importación masiva."""
    total_registros: int
    registros_exitosos: int
    registros_fallidos: int
    errores: List[dict] = []


# ============== RESPONSE (salida) ==============

class ClienteResponse(BaseModel):
    """Cliente completo devuelto por GET/PUT."""
    id: int
    codigo: str
    rif: str
    nombre_razon_social: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    condicion_pago: str
    limite_credito: float
    regimen_iva: str
    es_contribuyente_especial: bool
    numero_contribuyente_especial: Optional[str] = None
    moneda_id: Optional[int] = None
    activo: bool
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None


class ClienteListItem(BaseModel):
    """Item resumido para listados y búsqueda."""
    id: int
    codigo: str
    rif: str
    nombre_razon_social: str
    condicion_pago: str
    limite_credito: float
    es_contribuyente_especial: bool
    activo: bool
