"""
Schemas Pydantic del modulo Auth.
"""
from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Payload para login (POST /auth/login)."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Respuesta de login exitoso."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # segundos
    usuario: dict
