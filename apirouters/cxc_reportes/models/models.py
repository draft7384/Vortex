"""
Schemas Pydantic del modulo Reportes CxC.
"""
from typing import List, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


# ============================================================
# ITEMS COMPARTIDOS
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


class MovimientoCxcListItem(BaseModel):
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


# ============================================================
# ESTADO DE CUENTA
# ============================================================

class EstadoCuentaResponse(BaseModel):
    cliente_id: int
    cliente_nombre: str
    saldo_total_pendiente: float
    saldo_total_pendiente_local: float
    movimientos: List[MovimientoCxcListItem] = []


# ============================================================
# ANTIGUEDAD DE SALDOS
# ============================================================

class AntiguedadSaldosBucket(BaseModel):
    rango: str
    desde_dias: int
    hasta_dias: Optional[int] = None  # None = "y mas" (ultimo bucket)
    cantidad_documentos: int
    monto_total: float
    monto_total_local: float


class AntiguedadSaldosResponse(BaseModel):
    fecha_corte: date
    rangos_usados: List[int]
    total_pendiente: float
    total_pendiente_local: float
    buckets: List[AntiguedadSaldosBucket] = []
