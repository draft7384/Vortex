"""
Schemas Pydantic del modulo Usuarios.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import datetime


# ============== REQUEST ==============

class UsuarioCreateRequest(BaseModel):
    """Payload para crear un usuario (POST /usuarios)."""
    username: str = Field(..., min_length=3, max_length=50)
    nombre_completo: str = Field(..., min_length=1, max_length=150)
    email: Optional[EmailStr] = None
    password: str = Field(..., min_length=6, max_length=128, description="Minimo 6 caracteres")
    rol: Literal["ADMIN", "VENDEDOR", "CAJERO", "CONTADOR"] = "VENDEDOR"


class UsuarioUpdateRequest(BaseModel):
    """Payload para actualizar un usuario (PUT /usuarios/{id})."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    nombre_completo: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    rol: Optional[Literal["ADMIN", "VENDEDOR", "CAJERO", "CONTADOR"]] = None
    activo: Optional[bool] = None


# ============== RESPONSE ==============

class UsuarioResponse(BaseModel):
    """Usuario completo (sin password_hash) devuelto por GET/PUT."""
    id: int
    username: str
    nombre_completo: str
    email: Optional[str] = None
    rol: str
    activo: bool
    creado_en: Optional[datetime] = None
    ultimo_acceso: Optional[datetime] = None


class UsuarioListItem(BaseModel):
    """Item resumido para listados."""
    id: int
    username: str
    nombre_completo: str
    email: Optional[str] = None
    rol: str
    activo: bool
