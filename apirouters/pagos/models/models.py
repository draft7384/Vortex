"""
Schemas Pydantic (entrada y salida) del modulo Pagos / CxC.
"""
from typing import List, Literal, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator


# Type aliases
TipoPagoLiteral = Literal["ABONO", "RETENCION_IVA", "RETENCION_ISLR", "ANTICIPO", "NOTA_CREDITO", "NOTA_DEBITO"]
TipoAplicacionModoLiteral = Literal["AUTO", "MANUAL"]


# ============================================================
# REQUEST
# ============================================================

class AplicacionPagoItem(BaseModel):
    """Sub-schema: linea de cruce contra una deuda."""
    movimiento_deuda_id: int = Field(..., gt=0)
    monto_aplicado: float = Field(..., gt=0)


class PagoCreateRequest(BaseModel):
    """Payload para crear un pago/abono (POST /pagos)."""
    cliente_id: int = Field(..., gt=0)
    fecha_pago: Optional[date] = Field(None, description="Default: hoy")
    moneda_id: int = Field(..., gt=0)
    numero_documento: str = Field(..., min_length=1, max_length=30,
                                  description="Referencia externa: REF-BANC-123, RET-IVA-2024-001, etc.")
    tipo: TipoPagoLiteral
    monto_pago: float = Field(..., gt=0)
    observaciones: Optional[str] = Field(None, max_length=500)
    modo_aplicacion: TipoAplicacionModoLiteral = Field("AUTO",
        description="AUTO: backend aplica FIFO contra deudas mas viejas. MANUAL: usa data.aplicaciones")
    aplicaciones: Optional[List[AplicacionPagoItem]] = Field(None,
        description="Requerido si modo_aplicacion=MANUAL. Ignorado si AUTO")

    @model_validator(mode="after")
    def _validar_modo_y_aplicaciones(self):
        if self.modo_aplicacion == "MANUAL":
            if not self.aplicaciones:
                raise ValueError("APLICACIONES_REQUERIDAS: modo MANUAL requiere 'aplicaciones' no vacias")
            if self.tipo == "ANTICIPO":
                raise ValueError("ANTICIPO_NO_TIENE_APLICACIONES_INMEDIATAS: un anticipo queda como saldo a favor del cliente, sin aplicaciones")
        return self


# ============================================================
# RESPONSE
# ============================================================

class AplicacionCxcItem(BaseModel):
    id: int
    movimiento_pago_id: int
    movimiento_deuda_id: int
    monto_aplicado_original: float
    monto_aplicado_local: float
    fecha_aplicacion: datetime
    aplicado_por: int
    reversada: bool = False
    reversada_por: Optional[int] = None
    reversada_en: Optional[datetime] = None
    motivo_reverso: Optional[str] = None


class MovimientoCxcConAplicaciones(BaseModel):
    id: int
    cliente_id: int
    tipo_movimiento: str
    documento_venta_id: Optional[int] = None
    numero_documento: Optional[str] = None
    fecha_movimiento: date
    fecha_vencimiento: Optional[date] = None
    moneda_id: int
    tasa_cambio: float
    monto_original: float
    saldo_original: float
    monto_local: float
    saldo_local: float
    estado: str
    aplicaciones: List[AplicacionCxcItem] = []
