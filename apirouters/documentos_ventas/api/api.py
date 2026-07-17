"""
Capa HTTP del modulo Documentos de Venta. Todos los endpoints requieren JWT.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apirouters.auth.use_case.use_case import CurrentUser, get_current_user
from apirouters.documentos_ventas.models.models import (
    DocumentoVentaAnularRequest,
    DocumentoVentaCreateRequest,
    EstadoDocumentoLiteral,
    TipoDocumentoLiteral,
)
from apirouters.documentos_ventas.use_case.use_case import DocumentosVentasUseCase
from conex.conn import get_db


class DocumentosVentasAPI:
    router = APIRouter(prefix="/documentos-ventas", tags=["Documentos de Venta"])

    @staticmethod
    @router.post("/", status_code=201, summary="Crear un documento de venta (factura, NE, presupuesto, pedido)")
    async def create_documento(
        data: DocumentoVentaCreateRequest,
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(get_current_user),
    ):
        return await DocumentosVentasUseCase(db).create_documento(data, current_user)

    @staticmethod
    @router.get("/", summary="Listar documentos con filtros y paginacion")
    async def get_documentos(
        cliente_id: Optional[int] = Query(None, gt=0),
        tipo: Optional[TipoDocumentoLiteral] = Query(None),
        estado: Optional[EstadoDocumentoLiteral] = Query(None),
        fecha_desde: Optional[date] = Query(None),
        fecha_hasta: Optional[date] = Query(None),
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await DocumentosVentasUseCase(db).get_documentos(
            cliente_id, tipo, estado, fecha_desde, fecha_hasta, limit, offset
        )

    @staticmethod
    @router.post("/{documento_id}/anular", summary="Anular un documento (regla de anulacion segura)")
    async def anular_documento(
        documento_id: int,
        data: DocumentoVentaAnularRequest,
        db: AsyncSession = Depends(get_db),
        current_user: CurrentUser = Depends(get_current_user),
    ):
        return await DocumentosVentasUseCase(db).anular_documento(documento_id, data, current_user)

    @staticmethod
    @router.get("/{documento_id}", summary="Obtener un documento con su detalle")
    async def get_documento_by_id(
        documento_id: int,
        db: AsyncSession = Depends(get_db),
        _: CurrentUser = Depends(get_current_user),
    ):
        return await DocumentosVentasUseCase(db).get_documento_by_id(documento_id)
