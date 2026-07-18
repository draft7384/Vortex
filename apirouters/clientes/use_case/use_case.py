"""
Lógica de negocio del módulo Clientes.
Cada método ejecuta el SQL correspondiente desde statement.py,
realiza validaciones y maneja la transacción (commit/rollback).
"""
import re
from typing import Optional, List
from io import BytesIO

import pandas as pd
from openpyxl import load_workbook
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.responses import standard_response
from apirouters.clientes.models.models import (
    ClienteCreateRequest,
    ClienteUpdateRequest,
    ClienteImportItem,
)
from apirouters.clientes.statement import statement as st


# Regex para validar RIF venezolano: V/E/J/G + '-' + 8 a 10 dígitos + opcional '-' + 1 dígito
RIF_VENEZOLANO_REGEX = re.compile(r"^[VEJGvejg]-\d{7,10}(-\d)?$")


class ClientesUseCase:
    """Encapsula la lógica de negocio del módulo Clientes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================
    # CREATE
    # =========================================================
    async def create_cliente(self, data: ClienteCreateRequest) -> dict:
        """
        Crea un cliente.
        Validaciones:
            - RIF formato venezolano.
            - Código y RIF únicos.
        """
        # Validación de RIF
        if not RIF_VENEZOLANO_REGEX.match(data.rif):
            return standard_response(
                400,
                "RIF_INVALIDO: el RIF debe tener formato venezolano (ej. J-12345678-9 o V-12345678)",
                None,
            )

        # Validar contribuyente especial
        if data.es_contribuyente_especial and not data.numero_contribuyente_especial:
            return standard_response(
                400,
                "CONTRIBUYENTE_ESPECIAL_REQUIERE_NUMERO: si es_contribuyente_especial=TRUE debe proveer numero_contribuyente_especial",
                None,
            )

        try:
            # Verificar RIF duplicado
            existing = await self.db.execute(
                text(st.SELECT_CLIENTE_BY_RIF), {"rif": data.rif}
            )
            if existing.mappings().first():
                return standard_response(
                    409, "REGISTRO_DUPLICADO: ya existe un cliente con ese RIF", None
                )

            # Insertar
            result = await self.db.execute(
                text(st.INSERT_CLIENTE), data.model_dump()
            )
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(201, "Cliente creado exitosamente", dict(row))

        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error al crear cliente: {str(e)}", None)

    # =========================================================
    # READ - Listado paginado
    # =========================================================
    async def get_clientes(self, limit: int = 50, offset: int = 0, search: Optional[str] = None, activo: Optional[bool] = None, sort_by: str = "nombre_razon_social", sort_order: str = "asc") -> dict:
        try:
            # Validar columnas permitidas para ordenar para evitar SQL Injection
            allowed_sort_cols = {
                "codigo": "codigo",
                "rif": "rif",
                "nombre": "nombre_razon_social",
                "nombre_razon_social": "nombre_razon_social",
                "condicion": "condicion_pago",
                "credito": "limite_credito"
            }
            column = allowed_sort_cols.get(sort_by, "nombre_razon_social")
            order = "ASC" if sort_order.lower() == "asc" else "DESC"

            # Construcción dinámica de la cláusula WHERE
            where_clauses = ["activo = :activo_val"] if activo is None else ["activo = :activo_val"]
            params = {"limit": limit, "offset": offset, "activo_val": activo if activo is not None else True}

            if search:
                where_clauses.append("(LOWER(nombre_razon_social) LIKE LOWER(:search) OR LOWER(rif) LIKE LOWER(:search) OR LOWER(codigo) LIKE LOWER(:search))")
                params["search"] = f"%{search.strip()}%"

            where_sql = " AND ".join(where_clauses)

            # Query para obtener items con orden dinámico
            query_items = f"""
                SELECT id, codigo, rif, nombre_razon_social, condicion_pago, limite_credito,
                       es_contribuyente_especial, activo
                FROM clientes
                WHERE {where_sql}
                ORDER BY {column} {order}
                LIMIT :limit OFFSET :offset;
            """

            # Query para obtener total
            query_count = f"SELECT COUNT(*) FROM clientes WHERE {where_sql}"

            result = await self.db.execute(text(query_items), params)
            rows = [dict(r) for r in result.mappings().all()]

            total_result = await self.db.execute(text(query_count), params)
            total = total_result.scalar() or 0

            return standard_response(
                200,
                f"Listado de clientes (total={total})",
                {"items": rows, "total": total, "limit": limit, "offset": offset},
            )
        except Exception as e:
            return standard_response(500, f"Error al listar clientes: {str(e)}", None)

    # =========================================================
    # READ - Por ID
    # =========================================================
    async def get_cliente_by_id(self, cliente_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.SELECT_CLIENTE_BY_ID), {"cliente_id": cliente_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Cliente no encontrado", None)
            return standard_response(200, "Cliente encontrado", dict(row))
        except Exception as e:
            return standard_response(500, f"Error al obtener cliente: {str(e)}", None)

    # =========================================================
    # READ - Búsqueda por keyword
    # =========================================================
    async def search_clientes(self, keyword: str) -> dict:
        try:
            if not keyword or len(keyword.strip()) < 2:
                return standard_response(
                    400, "KEYWORD_REQUERIDO: minimo 2 caracteres para buscar", None
                )
            result = await self.db.execute(
                text(st.SEARCH_CLIENTES_BY_KEYWORD), {"keyword": f"%{keyword.strip()}%"}
            )
            rows = [dict(r) for r in result.mappings().all()]
            return standard_response(
                200, f"{len(rows)} resultados para '{keyword}'", rows
            )
        except Exception as e:
            return standard_response(500, f"Error en busqueda: {str(e)}", None)

    # =========================================================
    # UPDATE
    # =========================================================
    async def update_cliente(
        self, cliente_id: int, data: ClienteUpdateRequest
    ) -> dict:
        try:
            # Verificar que existe
            existing = await self.db.execute(
                text(st.SELECT_CLIENTE_BY_ID), {"cliente_id": cliente_id}
            )
            if not existing.mappings().first():
                return standard_response(404, "Cliente no encontrado", None)

            # COALESCE espera TODOS los params nombrados; enviamos los no seteados como None
            payload = data.model_dump()
            payload["cliente_id"] = cliente_id

            result = await self.db.execute(text(st.UPDATE_CLIENTE), payload)
            row = result.mappings().first()
            await self.db.commit()
            return standard_response(200, "Cliente actualizado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error al actualizar cliente: {str(e)}", None)

    # =========================================================
    # DELETE (soft)
    # =========================================================
    async def delete_cliente(self, cliente_id: int) -> dict:
        try:
            result = await self.db.execute(
                text(st.DELETE_CLIENTE), {"cliente_id": cliente_id}
            )
            row = result.mappings().first()
            if not row:
                return standard_response(404, "Cliente no encontrado", None)
            await self.db.commit()
            return standard_response(200, "Cliente desactivado", dict(row))
        except Exception as e:
            await self.db.rollback()
            return standard_response(500, f"Error al eliminar cliente: {str(e)}", None)

    # =========================================================
    # QUERY AUXILIAR: saldo pendiente del cliente
    # =========================================================
    async def get_saldo_pendiente(self, cliente_id: int) -> dict:
        """Usado por otros módulos (facturas) para validar límite de crédito."""
        try:
            result = await self.db.execute(
                text(st.SELECT_SUM_SALDO_PENDIENTE_CLIENTE),
                {"cliente_id": cliente_id},
            )
            total = result.scalar() or 0
            return standard_response(200, "Saldo pendiente", {"total_pendiente": float(total)})
        except Exception as e:
            return standard_response(500, f"Error: {str(e)}", None)

    # =========================================================
    # IMPORTACION MASIVA DESDE EXCEL
    # =========================================================
    async def import_clientes_from_excel(self, file_bytes: bytes) -> dict:
        """
        Importa clientes masivamente desde un archivo Excel.
        Valida cada fila y crea los clientes válidos.
        Retorna resumen de éxitos y errores.
        """
        errores: List[dict] = []
        registros_exitosos = 0
        
        try:
            # Leer Excel desde bytes
            df = pd.read_excel(BytesIO(file_bytes), sheet_name=0, header=0)
            
            # Columnas requeridas
            columnas_requeridas = ['codigo', 'rif', 'nombre_razon_social']
            for col in columnas_requeridas:
                if col not in df.columns:
                    return standard_response(400, f"COLUMNA_FALTANTE: la columna '{col}' es requerida en el Excel", None)
            
            total_registros = len(df)
            
            for idx, row in df.iterrows():
                fila_numero = idx + 2  # +2 porque Excel empieza en 1 y hay header
                
                try:
                    # Limpiar datos
                    codigo = str(row.get('codigo', '')).strip()
                    rif = str(row.get('rif', '')).strip()
                    nombre_razon_social = str(row.get('nombre_razon_social', '')).strip()
                    
                    # Validaciones básicas
                    if not codigo:
                        errores.append({"fila": fila_numero, "error": "Código vacío", "datos": dict(row)})
                        continue
                    
                    if not rif:
                        errores.append({"fila": fila_numero, "error": "RIF vacío", "datos": dict(row)})
                        continue
                    
                    # Validar formato RIF
                    if not RIF_VENEZOLANO_REGEX.match(rif):
                        errores.append({"fila": fila_numero, "error": f"RIF inválido: {rif}", "datos": dict(row)})
                        continue
                    
                    if not nombre_razon_social:
                        errores.append({"fila": fila_numero, "error": "Nombre/Razón social vacío", "datos": dict(row)})
                        continue
                    
                    # Verificar duplicados en BD
                    existing = await self.db.execute(text(st.SELECT_CLIENTE_BY_RIF), {"rif": rif})
                    if existing.mappings().first():
                        errores.append({"fila": fila_numero, "error": f"RIF duplicado: {rif}", "datos": dict(row)})
                        continue
                    
                    # Verificar código duplicado
                    existing_codigo = await self.db.execute(
                        text("SELECT id FROM clientes WHERE codigo = :codigo"),
                        {"codigo": codigo}
                    )
                    if existing_codigo.mappings().first():
                        errores.append({"fila": fila_numero, "error": f"Código duplicado: {codigo}", "datos": dict(row)})
                        continue
                    
                    # Preparar datos opcionales
                    direccion = str(row.get('direccion', '')) or None
                    telefono = str(row.get('telefono', '')) or None
                    email_val = str(row.get('email', '')) or None
                    condicion_pago = str(row.get('condicion_pago', 'CONTADO')).upper()
                    if condicion_pago not in ['CONTADO', 'CREDITO', 'ANTICIPO']:
                        condicion_pago = 'CONTADO'
                    
                    limite_credito = float(row.get('limite_credito', 0) or 0)
                    regimen_iva = str(row.get('regimen_iva', 'ORDINARIO')).upper()
                    if regimen_iva not in ['ORDINARIO', 'ESPECIAL']:
                        regimen_iva = 'ORDINARIO'
                    
                    es_contribuyente = bool(row.get('es_contribuyente_especial', False))
                    numero_contribuyente = str(row.get('numero_contribuyente_especial', '')) or None
                    moneda_id = int(row.get('moneda_id', 1) or 1)
                    
                    # Si es contribuyente especial pero no tiene número, omitir
                    if es_contribuyente and not numero_contribuyente:
                        errores.append({"fila": fila_numero, "error": "Contribuyente especial sin número", "datos": dict(row)})
                        continue
                    
                    # Insertar cliente
                    data = {
                        "codigo": codigo,
                        "rif": rif,
                        "nombre_razon_social": nombre_razon_social,
                        "direccion": direccion,
                        "telefono": telefono,
                        "email": email_val,
                        "condicion_pago": condicion_pago,
                        "limite_credito": limite_credito,
                        "regimen_iva": regimen_iva,
                        "es_contribuyente_especial": es_contribuyente,
                        "numero_contribuyente_especial": numero_contribuyente,
                        "moneda_id": moneda_id,
                    }
                    
                    result = await self.db.execute(text(st.INSERT_CLIENTE), data)
                    await self.db.commit()
                    registros_exitosos += 1
                    
                except Exception as e:
                    errores.append({"fila": fila_numero, "error": str(e), "datos": dict(row)})
                    await self.db.rollback()
            
            return standard_response(
                200,
                f"Importación completada: {registros_exitosos}/{total_registros} exitosos",
                {
                    "total_registros": total_registros,
                    "registros_exitosos": registros_exitosos,
                    "registros_fallidos": len(errores),
                    "errores": errores[:50]  # Limitar a primeros 50 errores
                }
            )
            
        except Exception as e:
            return standard_response(500, f"Error al procesar Excel: {str(e)}", None)
