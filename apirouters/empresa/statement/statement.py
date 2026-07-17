"""
SQL del modulo Empresa (singleton).
Solo hay una fila con id=1. Se inserta/actualiza con UPSERT.
"""

UPSERT_EMPRESA = """
INSERT INTO empresa_config (
    id, rif, nombre_razon_social, nombre_comercial, direccion_fiscal,
    telefono, email, sitio_web, logo_url, serial_imprenta,
    rango_factura_desde, rango_factura_hasta,
    rango_nc_desde, rango_nc_hasta,
    rango_nd_desde, rango_nd_hasta,
    actualizado_en
) VALUES (
    1, :rif, :nombre_razon_social, :nombre_comercial, :direccion_fiscal,
    :telefono, :email, :sitio_web, :logo_url, :serial_imprenta,
    :rango_factura_desde, :rango_factura_hasta,
    :rango_nc_desde, :rango_nc_hasta,
    :rango_nd_desde, :rango_nd_hasta,
    CURRENT_TIMESTAMP
)
ON CONFLICT (id) DO UPDATE SET
    rif = EXCLUDED.rif,
    nombre_razon_social = EXCLUDED.nombre_razon_social,
    nombre_comercial = EXCLUDED.nombre_comercial,
    direccion_fiscal = EXCLUDED.direccion_fiscal,
    telefono = EXCLUDED.telefono,
    email = EXCLUDED.email,
    sitio_web = EXCLUDED.sitio_web,
    logo_url = EXCLUDED.logo_url,
    serial_imprenta = EXCLUDED.serial_imprenta,
    rango_factura_desde = EXCLUDED.rango_factura_desde,
    rango_factura_hasta = EXCLUDED.rango_factura_hasta,
    rango_nc_desde = EXCLUDED.rango_nc_desde,
    rango_nc_hasta = EXCLUDED.rango_nc_hasta,
    rango_nd_desde = EXCLUDED.rango_nd_desde,
    rango_nd_hasta = EXCLUDED.rango_nd_hasta,
    actualizado_en = CURRENT_TIMESTAMP
RETURNING id, rif, nombre_razon_social, nombre_comercial, direccion_fiscal,
          telefono, email, sitio_web, logo_url, serial_imprenta,
          rango_factura_desde, rango_factura_hasta,
          rango_nc_desde, rango_nc_hasta,
          rango_nd_desde, rango_nd_hasta,
          actualizado_en;
"""

SELECT_EMPRESA = """
SELECT id, rif, nombre_razon_social, nombre_comercial, direccion_fiscal,
       telefono, email, sitio_web, logo_url, serial_imprenta,
       rango_factura_desde, rango_factura_hasta,
       rango_nc_desde, rango_nc_hasta,
       rango_nd_desde, rango_nd_hasta,
       actualizado_en
FROM empresa_config
WHERE id = 1;
"""
