"""
Helpers para respuestas estandarizadas.
TODAS las respuestas del API deben usar el contrato:
    { "status_code": int, "message": str, "data": Any }
"""
from typing import Any, Optional


def standard_response(
    status_code: int,
    message: str,
    data: Optional[Any] = None,
) -> dict:
    """
    Construye una respuesta estandarizada.

    Args:
        status_code: Código HTTP semántico (200, 201, 400, 404, 409, 500...).
        message: Mensaje legible para el cliente. Prefijar con código de error si aplica
                  (ej: "LIMITE_CREDITO_EXCEDIDO: el cliente supera el límite").
        data: Payload. None para errores. Lista/dict para éxito.

    Returns:
        dict con la estructura estándar.
    """
    return {
        "status_code": status_code,
        "message": message,
        "data": data,
    }


# === Constantes de error semánticas (para reglas de negocio) ===
ERR_LIMITE_CREDITO_EXCEDIDO = "LIMITE_CREDITO_EXCEDIDO"
ERR_DEBE_CARGAR_TASA = "DEBE_CARGAR_TASA_DEL_DIA"
ERR_STOCK_INSUFICIENTE = "STOCK_INSUFICIENTE"
ERR_CLIENTE_NO_CONTR_ESPECIAL = "CLIENTE_NO_ES_CONTRIBUYENTE_ESPECIAL"
ERR_DOCUMENTO_CON_PAGOS = "DOCUMENTO_CON_PAGOS_APLICADOS"
ERR_DUPLICADO = "REGISTRO_DUPLICADO"
ERR_NO_ENCONTRADO = "REGISTRO_NO_ENCONTRADO"
ERR_CONCURRENCIA = "ERROR_CONCURRENCIA"
