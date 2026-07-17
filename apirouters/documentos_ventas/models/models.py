"""
Schemas Pydantic (entrada y salida) del modulo Documentos de Venta.
NO usamos ORM: estos modelos validan payloads y dan forma a las respuestas.
"""
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


# ============== LITERALES DE TIPO ==============

# Tipos soportados. NC/ND se implementan en Fase 5.
TipoDocumentoLiteral = Literal["FACTURA", "NOTA_ENTREGA", "PRESUPUESTO", "PEDIDO", "NOTA_CREDITO", "NOTA_DEBITO"]
EstadoDocumentoLiteral = Literal["BORRADOR", "EMITIDO", "ANULADO", "PAGADO"]
CondicionPagoLiteral = Literal["CONTADO", "CREDITO", "ANTICIPO"]


# ============== REQUEST (entrada) ==============

class DocumentoVentaDetalleItem(BaseModel):
    """Renglon del documento de venta (anidado en CreateRequest)."""
    producto_id: Optional[int] = Field(None, gt=0,
                                       description="Opcional: si es None, es un renglon de 'ajuste' (ej: NC sin producto)")
    descripcion: Optional[str] = Field(None, max_length=255,
                                       description="Si no se envia, se usa la descripcion del producto")
    cantidad: float = Field(..., gt=0, description="Cantidad del producto (debe ser > 0)")
    precio_unitario: float = Field(..., ge=0, description="Precio unitario (>= 0)")
    descuento_pct: float = Field(0.00, ge=0, le=100, description="Porcentaje de descuento (0-100)")
    impuesto_pct: float = Field(16.00, ge=0, le=100, description="Porcentaje de IVA (0-100)")


class DocumentoVentaCreateRequest(BaseModel):
    """Payload para crear un documento de venta (POST /documentos-ventas)."""
    tipo: TipoDocumentoLiteral = Field(...,
        description="FACTURA | NOTA_ENTREGA | PRESUPUESTO | PEDIDO | NOTA_CREDITO | NOTA_DEBITO")
    cliente_id: int = Field(..., gt=0)
    vendedor_id: Optional[int] = Field(None, gt=0)
    punto_emision_id: int = Field(..., gt=0)
    moneda_id: int = Field(..., gt=0)
    condicion_pago: Optional[CondicionPagoLiteral] = Field(None,
        description="Solo aplica a FACTURA (CONTADO/CREDITO/ANTICIPO)")
    numero_control: Optional[str] = Field(None, max_length=30,
        description="Obligatorio para FACTURA, NOTA_CREDITO y NOTA_DEBITO")
    documento_referencia_id: Optional[int] = Field(None, gt=0,
        description="Obligatorio para NOTA_CREDITO y NOTA_DEBITO: id de la FACTURA que ajustan")
    motivo: Optional[str] = Field(None, max_length=500,
        description="Obligatorio para NC/ND (min 5 chars). Texto libre auditado.")
    fecha_emision: Optional[date] = Field(None, description="Default: hoy")
    fecha_vencimiento: Optional[date] = Field(None,
        description="Requerido si FACTURA+condicion_pago=CREDITO")
    observaciones: Optional[str] = None
    detalles: List[DocumentoVentaDetalleItem] = Field(..., min_length=1, description="Al menos 1 renglon")
    forzar_credito: bool = Field(False, description="Override de limite de credito (requiere motivo_override). Solo FACTURA.")
    motivo_override: Optional[str] = Field(None, min_length=5, max_length=500,
        description="Motivo auditable del override de credito")

    @model_validator(mode="after")
    def _validaciones_cruzadas(self):
        # 1. NC/ND: requieren documento_referencia_id + motivo (min 5)
        if self.tipo in ("NOTA_CREDITO", "NOTA_DEBITO"):
            if not self.documento_referencia_id:
                raise ValueError("DOCUMENTO_REFERENCIA_REQUERIDO: NC/ND requieren documento_referencia_id")
            if not self.motivo or len(self.motivo.strip()) < 5:
                raise ValueError("MOTIVO_REQUERIDO_PARA_NC_ND: NC/ND requieren motivo (min 5 chars)")

        # 2. FACTURA / NC / ND requieren numero_control (tambien lo exige chk_numero_control en DB)
        if self.tipo in ("FACTURA", "NOTA_CREDITO", "NOTA_DEBITO") and not self.numero_control:
            raise ValueError("NUMERO_CONTROL_REQUERIDO: FACTURA, NOTA_CREDITO y NOTA_DEBITO deben incluir numero_control")

        # 3. condicion_pago solo aplica a FACTURA
        if self.condicion_pago and self.tipo != "FACTURA":
            raise ValueError("CONDICION_PAGO_SOLO_FACTURA: condicion_pago solo aplica a FACTURA")

        # 4. fecha_vencimiento solo aplica a FACTURA
        if self.fecha_vencimiento and self.tipo != "FACTURA":
            raise ValueError("FECHA_VENCIMIENTO_SOLO_FACTURA: fecha_vencimiento solo aplica a FACTURA")

        # 5. FACTURA con CREDITO requiere fecha_vencimiento
        if self.tipo == "FACTURA" and self.condicion_pago == "CREDITO" and not self.fecha_vencimiento:
            raise ValueError("FECHA_VENCIMIENTO_REQUERIDA_PARA_CREDITO: FACTURA con condicion_pago=CREDITO requiere fecha_vencimiento")

        # 6. forzar_credito requiere motivo_override (solo FACTURA)
        if self.forzar_credito and (not self.motivo_override or len(self.motivo_override.strip()) < 5):
            raise ValueError("MOTIVO_REQUERIDO_PARA_OVERRIDE: forzar_credito=true requiere motivo_override (min 5 chars)")

        # 7. forzar_credito solo aplica a FACTURA
        if self.forzar_credito and self.tipo != "FACTURA":
            raise ValueError("FORZAR_CREDITO_SOLO_FACTURA: forzar_credito solo aplica a FACTURA")

        return self


class DocumentoVentaAnularRequest(BaseModel):
    """Payload para anular un documento (POST /documentos-ventas/{id}/anular)."""
    motivo: str = Field(..., min_length=5, max_length=500, description="Motivo auditable de la anulacion")
    forzar_anulacion: bool = Field(False, description="Override para anular aunque tenga pagos aplicados")


# ============== RESPONSE (salida) ==============

class DocumentoVentaDetalleResponse(BaseModel):
    """Renglon devuelto en GET /documentos-ventas/{id}."""
    id: int
    documento_id: int
    producto_id: Optional[int] = None
    nro_renglon: int
    descripcion: str
    cantidad: float
    precio_unitario: float
    descuento_pct: float
    impuesto_pct: float
    total_renglon: float


class DocumentoVentaResponse(BaseModel):
    """Documento completo devuelto por GET / POST."""
    id: int
    codigo: str
    numero_control: Optional[str] = None
    tipo: str
    cliente_id: int
    vendedor_id: Optional[int] = None
    punto_emision_id: int
    documento_referencia_id: Optional[int] = None
    motivo: Optional[str] = None
    fecha_emision: date
    fecha_vencimiento: Optional[date] = None
    moneda_id: int
    tasa_cambio: float
    subtotal: float
    total_impuestos: float
    total_descuentos: float
    total_neto: float
    total_neto_local: float
    estado: str
    observaciones: Optional[str] = None
    creado_por: int
    creado_en: Optional[datetime] = None
    actualizado_en: Optional[datetime] = None
    anulado_por: Optional[int] = None
    anulado_en: Optional[datetime] = None
    detalles: List[DocumentoVentaDetalleResponse] = []


class DocumentoVentaListItem(BaseModel):
    """Item resumido para listados y busqueda."""
    id: int
    codigo: str
    numero_control: Optional[str] = None
    tipo: str
    fecha_emision: date
    fecha_vencimiento: Optional[date] = None
    cliente_id: int
    cliente_nombre: Optional[str] = None
    total_neto: float
    total_neto_local: float
    estado: str
