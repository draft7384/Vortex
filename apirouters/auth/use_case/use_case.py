"""
Logica de negocio del modulo Auth.
Maneja login, generacion/verificacion de JWT, y la dependency de proteccion
para el resto del API.
"""
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.responses import standard_response
from apirouters.auth.models.models import LoginRequest
from apirouters.auth.statement import statement as st


# ============================================================
# Esquema de seguridad Bearer (extrae el token del header)
# ============================================================
security = HTTPBearer(auto_error=False)


# ============================================================
# Modelo interno del usuario autenticado
# ============================================================
class CurrentUser(BaseModel):
    id: int
    username: str
    rol: str


# ============================================================
# Helpers de JWT
# ============================================================
def _create_access_token(user_id: int, username: str, rol: str) -> tuple[str, int]:
    """
    Genera un JWT firmado.
    Retorna (token, expiracion_en_segundos).
    """
    expires_minutes = settings.JWT_EXPIRATION_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)

    payload = {
        "sub": str(user_id),
        "username": username,
        "rol": rol,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_minutes * 60


def _decode_access_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza HTTPException si es invalido/expirado."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"TOKEN_INVALIDO: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================
# Dependency: extraer el usuario actual desde el header Authorization
# Uso en cualquier endpoint protegido:
#   async def mi_endpoint(usuario_actual: CurrentUser = Depends(get_current_user)):
# ============================================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_REQUERIDO: debes enviar el header 'Authorization: Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _decode_access_token(credentials.credentials)
    return CurrentUser(
        id=int(payload["sub"]),
        username=payload["username"],
        rol=payload["rol"],
    )


# ============================================================
# Dependency opcional para endpoints con/sin auth
# ============================================================
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[CurrentUser]:
    if not credentials or not credentials.credentials:
        return None
    try:
        payload = _decode_access_token(credentials.credentials)
        return CurrentUser(
            id=int(payload["sub"]),
            username=payload["username"],
            rol=payload["rol"],
        )
    except HTTPException:
        return None


# ============================================================
# Use Case
# ============================================================
class AuthUseCase:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def login(self, data: LoginRequest) -> dict:
        """
        Autentica un usuario. Retorna {status_code, message, data: {access_token, ...}}.
        """
        try:
            result = await self.db.execute(
                text(st.SELECT_USUARIO_AUTENTICAR), {"username": data.username}
            )
            user = result.mappings().first()

            if not user:
                return standard_response(401, "CREDENCIALES_INVALIDAS: usuario o password incorrecto", None)

            # Verificar password con bcrypt
            password_matches = bcrypt.checkpw(
                data.password.encode("utf-8"),
                user["password_hash"].encode("utf-8"),
            )
            if not password_matches:
                return standard_response(401, "CREDENCIALES_INVALIDAS: usuario o password incorrecto", None)

            # Generar token
            token, expires_in = _create_access_token(
                user_id=user["id"],
                username=user["username"],
                rol=user["rol"],
            )

            # Actualizar ultimo acceso (no falla el login si esto falla)
            try:
                await self.db.execute(
                    text(st.UPDATE_ULTIMO_ACCESO), {"usuario_id": user["id"]}
                )
                await self.db.commit()
            except Exception:
                await self.db.rollback()

            user_data = {
                "id": user["id"],
                "username": user["username"],
                "nombre_completo": user["nombre_completo"],
                "email": user["email"],
                "rol": user["rol"],
            }

            return standard_response(
                200,
                "Login exitoso",
                {
                    "access_token": token,
                    "token_type": "bearer",
                    "expires_in": expires_in,
                    "usuario": user_data,
                },
            )

        except Exception as e:
            return standard_response(500, f"Error en login: {str(e)}", None)
