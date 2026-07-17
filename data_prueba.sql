-- =====================================================================
-- DATA DE PRUEBA: Vortex
-- Genera ~20+ documentos de venta con historial CxC realista para
-- alimentar el front-end con consultas variadas.
-- =====================================================================

BEGIN;

-- =====================================================================
-- 0. LIMPIEZA AUTORIZADA POR EL USUARIO: docs previos de pruebas T1-T16
-- =====================================================================
DELETE FROM aplicaciones_cxc;
DELETE FROM override_credito_log;
DELETE FROM movimientos_cxc;
DELETE FROM documentos_ventas_detalle;
DELETE FROM documentos_ventas;
UPDATE secuencias_documentos SET numero_actual = 0, proximo_numero = 1;

-- =====================================================================
-- 1. VENDEDORES ADICIONALES (5 mas, total 6)
-- =====================================================================
INSERT INTO vendedores (codigo, nombre, comision_pct, activo) VALUES
  ('V002', 'Ana Rodriguez',  4.50, TRUE),
  ('V003', 'Luis Hernandez',  6.00, TRUE),
  ('V004', 'Pedro Martinez',  5.50, TRUE),
  ('V005', 'Sofia Castro',    3.00, TRUE),
  ('V006', 'Roberto Silva',   7.00, FALSE)
ON CONFLICT (codigo) DO UPDATE SET nombre=EXCLUDED.nombre, comision_pct=EXCLUDED.comision_pct, activo=EXCLUDED.activo;

-- =====================================================================
-- 2. PRODUCTOS ADICIONALES (15 mas, total 18)
-- =====================================================================
INSERT INTO productos (codigo, descripcion, unidad_medida, precio_base, impuesto_pct, existencia, es_servicio, activo) VALUES
  ('P003', 'Arroz Mary 1kg',         'UND',  2.50,  16.00, 80.00, FALSE, TRUE),
  ('P004', 'Aceite Girasol 1L',      'UND',  4.80,  16.00, 45.00, FALSE, TRUE),
  ('P005', 'Pan Hallullas 6und',     'UND',  1.50,  16.00,  3.00, FALSE, TRUE),
  ('P006', 'Leche en polvo 1kg',     'UND',  6.20,  16.00, 25.00, FALSE, TRUE),
  ('P007', 'Huevos 12und',           'UND',  3.80,  16.00, 60.00, FALSE, TRUE),
  ('P008', 'Cafe Molido 500g',       'UND',  5.50,  16.00, 18.00, FALSE, TRUE),
  ('P009', 'Pasta Espagueti 500g',   'UND',  1.80,  16.00,100.00, FALSE, TRUE),
  ('P010', 'Atun en lata 170g',      'UND',  2.20,  16.00, 40.00, FALSE, TRUE),
  ('P011', 'Salsa de Tomate 500g',   'UND',  1.90,  16.00, 35.00, FALSE, TRUE),
  ('P012', 'Galletas Maria 200g',    'UND',  1.30,  16.00,  2.00, FALSE, TRUE),
  ('P013', 'Detergente 1kg',         'UND',  4.50,  16.00, 28.00, FALSE, TRUE),
  ('S002', 'Soporte Tecnico (hora)', 'HRS', 18.00,  16.00,  0.00, TRUE,  TRUE),
  ('S003', 'Diseno Grafico (hora)',  'HRS', 25.00,  16.00,  0.00, TRUE,  TRUE),
  ('S004', 'Capacitacion (hora)',    'HRS', 30.00,  16.00,  0.00, TRUE,  TRUE),
  ('S005', 'Mantenimiento (visita)', 'VIS', 80.00,  16.00,  0.00, TRUE,  TRUE)
ON CONFLICT (codigo) DO UPDATE SET
  descripcion=EXCLUDED.descripcion,
  precio_base=EXCLUDED.precio_base,
  existencia=EXCLUDED.existencia,
  es_servicio=EXCLUDED.es_servicio,
  activo=EXCLUDED.activo;

-- =====================================================================
-- 3. CLIENTES ADICIONALES (10 mas, total 13)
-- =====================================================================
INSERT INTO clientes (codigo, rif, nombre_razon_social, direccion, telefono, email,
                      condicion_pago, limite_credito, regimen_iva,
                      es_contribuyente_especial, numero_contribuyente_especial,
                      moneda_id, activo) VALUES
  ('C004', 'J-22222222-2', 'Distribuidora El Sol C.A.',       'Av. Bolivar, Caracas', '0212-2222222', 'elsol@ventas.com',       'CREDITO', 15000.00, 'ESPECIAL',  TRUE,  'CE-10001', 2, TRUE),
  ('C005', 'J-33333333-3', 'Corporacion Alpha S.A.',          'Av. Sucre, Valencia',  '0241-3333333', 'alpha@corp.com',         'CREDITO', 25000.00, 'ESPECIAL',  TRUE,  'CE-10002', 2, TRUE),
  ('C006', 'V-5555555-5',  'Jose Perez',                       'Urb. El Cafetal, Caracas', '0414-5555555', 'jperez@gmail.com', 'CREDITO',  3000.00, 'ORDINARIO', FALSE, NULL,    2, TRUE),
  ('C007', 'J-44444444-4', 'Inversiones La Montana C.A.',     'Calle 100, Maracaibo',  '0261-4444444', 'montana@inv.com',        'CREDITO',  8000.00, 'ORDINARIO', FALSE, NULL,    2, TRUE),
  ('C008', 'V-6666666-6',  'Carmen Lopez',                     'Av. Principal, Barquisimeto','0251-6666666','carmenlopez@hotmail.com','CREDITO',1500.00,'ORDINARIO', FALSE, NULL,    1, TRUE),
  ('C009', 'V-7777777-7',  'Luis Rodriguez',                  'Calle 5, Maracay',     '0243-7777777', NULL,                       'CONTADO',     0.00, 'ORDINARIO', FALSE, NULL,    1, TRUE),
  ('C010', 'J-88888888-8', 'Tienda Don Pepe C.A.',            'Av. Comercio, Pto Cabello','0242-8888888','donpepe@tienda.com',     'CONTADO',     0.00, 'ORDINARIO', FALSE, NULL,    1, TRUE),
  ('C011', 'J-99999999-9', 'Constructora Horizonte C.A.',     'Av. Las Americas, Caracas','0212-9999999','horizonte@const.com',   'ANTICIPO',20000.00, 'ORDINARIO', FALSE, NULL,    2, TRUE),
  ('C012', 'V-1212121-2',  'Ana Martinez',                     'Calle 12, Valencia',    '0241-1212121', NULL,                      'CREDITO',   500.00, 'ORDINARIO', FALSE, NULL,    1, TRUE),
  ('C013', 'J-13131313-0', 'Empresa Cerrada C.A.',            'Av. Inactiva',          '0212-1313131', NULL,                       'CONTADO',     0.00, 'ORDINARIO', FALSE, NULL,    1, FALSE)
ON CONFLICT (codigo) DO UPDATE SET
  rif=EXCLUDED.rif,
  nombre_razon_social=EXCLUDED.nombre_razon_social,
  condicion_pago=EXCLUDED.condicion_pago,
  limite_credito=EXCLUDED.limite_credito,
  es_contribuyente_especial=EXCLUDED.es_contribuyente_especial,
  numero_contribuyente_especial=EXCLUDED.numero_contribuyente_especial,
  activo=EXCLUDED.activo;

-- =====================================================================
-- 4. TASAS DE CAMBIO
-- =====================================================================
INSERT INTO tasas_cambio (moneda_id, fecha, tasa) VALUES
  (1, CURRENT_DATE, 1.0000),
  (2, CURRENT_DATE, 36.5000),
  (3, CURRENT_DATE, 39.8000)
ON CONFLICT (moneda_id, fecha) DO UPDATE SET tasa = EXCLUDED.tasa;

-- =====================================================================
-- 5. Verificacion de IDs antes de insertar documentos
-- =====================================================================
DO $$
DECLARE
  v_id_anterior INT;
  v_id_actual INT;
  v_count_actual INT;
BEGIN
  SELECT count(*) INTO v_count_actual FROM vendedores WHERE activo;
  RAISE NOTICE 'Vendedores activos: %', v_count_actual;

  SELECT count(*) INTO v_count_actual FROM clientes WHERE activo;
  RAISE NOTICE 'Clientes activos: %', v_count_actual;

  SELECT count(*) INTO v_count_actual FROM productos WHERE activo;
  RAISE NOTICE 'Productos activos: %', v_count_actual;
END $$;

COMMIT;

-- =====================================================================
-- 6. DOCUMENTOS DE VENTA (20+) - EN TRANSACCION SEPARADA
-- =====================================================================

BEGIN;

-- FAC-000001: Cliente C001, CREDITO, USD
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000001', '00-00000001', 'FACTURA', 101, 101, 1,
        CURRENT_DATE - 30, CURRENT_DATE - 15, 2, 36.5000,
        1025.00, 164.00, 0.00, 1189.00, 43398.50,
        'EMITIDO', 'Cliente regular, pago a 15 dias', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 101, 1, 'Coca-Cola 2L',                2.00, 500.00, 0.00, 16.00, 1160.00
UNION ALL SELECT currval('documentos_ventas_id_seq'), 102, 2, 'Consultoria IT (hora)',  1.00,  25.00, 0.00, 16.00,   29.00;

-- FAC-000002: Cliente C006
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000002', '00-00000002', 'FACTURA', 106, 102, 1,
        CURRENT_DATE - 25, CURRENT_DATE + 5, 2, 36.5000,
        16.30, 2.61, 0.00, 18.91, 690.22,
        'EMITIDO', NULL, 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 103, 1, 'Arroz Mary 1kg',   2.00, 2.50, 0.00, 16.00, 5.80
UNION ALL SELECT currval('documentos_ventas_id_seq'), 107, 2, 'Huevos 12und', 1.00, 3.80, 0.00, 16.00, 4.41
UNION ALL SELECT currval('documentos_ventas_id_seq'), 109, 3, 'Pasta Espagueti', 2.00, 1.80, 0.00, 16.00, 4.18
UNION ALL SELECT currval('documentos_ventas_id_seq'), 111,4, 'Salsa de Tomate', 1.00, 1.90, 0.00, 16.00, 2.20
UNION ALL SELECT currval('documentos_ventas_id_seq'), 113,5, 'Detergente 1kg',  1.00, 4.50, 0.00, 16.00, 5.22;

-- FAC-000003: Cliente C007
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000003', '00-00000003', 'FACTURA', 107, 103, 1,
        CURRENT_DATE - 20, CURRENT_DATE + 10, 2, 36.5000,
        145.00, 23.20, 5.80, 162.40, 5927.60,
        'EMITIDO', 'Aplica descuento del 4% por volumen', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 101, 1, 'Coca-Cola 2L',    10.00, 5.50, 0.00, 16.00, 63.80
UNION ALL SELECT currval('documentos_ventas_id_seq'), 106, 2, 'Leche en polvo',  5.00, 6.20, 0.00, 16.00, 35.96
UNION ALL SELECT currval('documentos_ventas_id_seq'), 108, 3, 'Cafe Molido 500g',3.00, 5.50, 0.00, 16.00, 19.14
UNION ALL SELECT currval('documentos_ventas_id_seq'), 104, 4, 'Aceite Girasol',  4.00, 4.80, 0.00, 16.00, 22.27;

-- FAC-000004: Cliente C004 (contribuyente especial)
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000004', '00-00000004', 'FACTURA', 105, 101, 1,
        CURRENT_DATE - 15, CURRENT_DATE + 15, 2, 36.5000,
        450.00, 72.00, 0.00, 522.00, 19053.00,
        'EMITIDO', 'Cliente CE-10001 - aplica retencion IVA', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 114, 1, 'Soporte Tecnico (hora)',   10.00, 18.00, 0.00, 16.00, 208.80
UNION ALL SELECT currval('documentos_ventas_id_seq'), 116, 2, 'Capacitacion (hora)',    5.00, 30.00, 0.00, 16.00, 174.00
UNION ALL SELECT currval('documentos_ventas_id_seq'), 117, 3, 'Mantenimiento (visita)', 1.00, 80.00, 0.00, 16.00,  92.80;

-- FAC-000005: PAGADA totalmente (cliente C004 pago todo)
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000005', '00-00000005', 'FACTURA', 105, 102, 1,
        CURRENT_DATE - 45, CURRENT_DATE - 15, 2, 36.5000,
        250.00, 40.00, 0.00, 290.00, 10585.00,
        'EMITIDO', 'Pagada en su totalidad', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 115, 1, 'Diseno Grafico (hora)', 10.00, 25.00, 0.00, 16.00, 290.00;

-- FAC-000006: PAGADA totalmente (cliente C001)
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000006', '00-00000006', 'FACTURA', 101, 104, 1,
        CURRENT_DATE - 40, CURRENT_DATE - 10, 2, 36.5000,
        500.00, 80.00, 0.00, 580.00, 21170.00,
        'EMITIDO', 'Pagada por transferencia', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 101, 1, 'Coca-Cola 2L', 100.00, 5.50, 0.00, 16.00, 638.00;

-- FAC-000007: PAGADA totalmente (cliente C005)
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000007', '00-00000007', 'FACTURA', 106, 105, 1,
        CURRENT_DATE - 35, CURRENT_DATE - 5, 2, 36.5000,
        180.00, 28.80, 0.00, 208.80, 7621.20,
        'EMITIDO', NULL, 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 106, 1, 'Leche en polvo 1kg', 20.00, 6.20, 0.00, 16.00, 143.84
UNION ALL SELECT currval('documentos_ventas_id_seq'), 108, 2, 'Cafe Molido 500g', 5.00, 5.50, 0.00, 16.00, 31.90;

-- FAC-000008: Cliente C009, CONTADO, VES
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000008', '00-00000008', 'FACTURA', 109, 103, 1,
        CURRENT_DATE - 10, CURRENT_DATE - 10, 1, 1.0000,
        5.50, 0.88, 0.00, 6.38, 6.38,
        'EMITIDO', 'Venta de mostrador', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 101, 1, 'Coca-Cola 2L', 1.00, 5.50, 0.00, 16.00, 6.38;

-- FAC-000009: Cliente C010, CONTADO, VES
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000009', '00-00000009', 'FACTURA', 110, 104, 1,
        CURRENT_DATE - 8, CURRENT_DATE - 8, 1, 1.0000,
        38.20, 6.11, 0.00, 44.31, 44.31,
        'EMITIDO', NULL, 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 104, 1, 'Aceite Girasol 1L', 2.00, 4.80, 0.00, 16.00, 11.14
UNION ALL SELECT currval('documentos_ventas_id_seq'), 107, 2, 'Huevos 12und',   3.00, 3.80, 0.00, 16.00, 13.22
UNION ALL SELECT currval('documentos_ventas_id_seq'), 109, 3, 'Pasta Espagueti',4.00, 1.80, 0.00, 16.00,  8.35
UNION ALL SELECT currval('documentos_ventas_id_seq'), 103, 4, 'Arroz Mary 1kg', 2.00, 2.50, 0.00, 16.00,  5.80
UNION ALL SELECT currval('documentos_ventas_id_seq'), 113,5, 'Detergente 1kg', 1.00, 4.50, 0.00, 16.00,  5.22;

-- FAC-000010: OVERRIDE DE CREDITO (cliente C012 con limite bajo)
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000010', '00-00000010', 'FACTURA', 112, 105, 1,
        CURRENT_DATE - 5, CURRENT_DATE + 25, 1, 1.0000,
        50.00, 8.00, 0.00, 58.00, 58.00,
        'EMITIDO', 'Override autorizado por gerente general - cliente nuevo pero confiable', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 101, 1, 'Coca-Cola 2L',     5.00, 5.50, 0.00, 16.00, 31.90
UNION ALL SELECT currval('documentos_ventas_id_seq'), 107, 2, 'Huevos 12und', 4.00, 3.80, 0.00, 16.00, 17.62
UNION ALL SELECT currval('documentos_ventas_id_seq'), 109, 3, 'Pasta Espagueti', 2.00, 1.80, 0.00, 16.00,  4.18;

-- FAC-000011: ANULADA
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por, anulado_por, anulado_en, motivo)
VALUES ('FAC-000011', '00-00000011', 'FACTURA', 106, 101, 1,
        CURRENT_DATE - 3, CURRENT_DATE + 27, 2, 36.5000,
        100.00, 16.00, 0.00, 116.00, 4234.00,
        'ANULADO', 'Anulada por error en precio - se emitio FAC-000012 en su lugar', 1, 1,
        CURRENT_TIMESTAMP, 'Error en precio del producto, se anula para emitir factura correcta');

-- FAC-000012: factura que reemplaza la 11
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000012', '00-00000012', 'FACTURA', 106, 101, 1,
        CURRENT_DATE - 2, CURRENT_DATE + 28, 2, 36.5000,
        100.00, 16.00, 0.00, 116.00, 4234.00,
        'EMITIDO', 'Reemplazo de FAC-000011 con precio correcto', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 106, 1, 'Leche en polvo 1kg', 5.00, 6.20, 0.00, 16.00, 35.96
UNION ALL SELECT currval('documentos_ventas_id_seq'), 108, 2, 'Cafe Molido 500g',4.00, 5.50, 0.00, 16.00, 25.52
UNION ALL SELECT currval('documentos_ventas_id_seq'), 104, 3, 'Aceite Girasol 1L',2.00, 4.80, 0.00, 16.00, 11.14;

-- FAC-000013: pago parcial
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000013', '00-00000013', 'FACTURA', 107, 103, 1,
        CURRENT_DATE - 12, CURRENT_DATE + 18, 2, 36.5000,
        300.00, 48.00, 0.00, 348.00, 12702.00,
        'EMITIDO', 'Pago parcial recibido (50%)', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 101, 1, 'Coca-Cola 2L',   30.00, 5.50, 0.00, 16.00, 191.40
UNION ALL SELECT currval('documentos_ventas_id_seq'), 104, 2, 'Aceite Girasol', 10.00, 4.80, 0.00, 16.00,  55.68
UNION ALL SELECT currval('documentos_ventas_id_seq'), 113,3, 'Detergente 1kg',  8.00, 4.50, 0.00, 16.00,  41.76;

-- FAC-000014: pago parcial + retencion IVA (cliente C004 CE)
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('FAC-000014', '00-00000014', 'FACTURA', 105, 102, 1,
        CURRENT_DATE - 10, CURRENT_DATE + 20, 2, 36.5000,
        500.00, 80.00, 0.00, 580.00, 21170.00,
        'EMITIDO', 'Retencion IVA 75% + pago parcial', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 117, 1, 'Mantenimiento (visita)',5.00, 80.00, 0.00, 16.00, 464.00
UNION ALL SELECT currval('documentos_ventas_id_seq'), 116, 2, 'Capacitacion (hora)',1.00, 30.00, 0.00, 16.00,  34.80
UNION ALL SELECT currval('documentos_ventas_id_seq'), 114, 3, 'Soporte Tecnico (hora)',1.00, 18.00, 0.00, 16.00,  20.88;

-- NE-000001
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('NE-000001', NULL, 'NOTA_ENTREGA', 108, 104, 1,
        CURRENT_DATE - 5, NULL, 1, 1.0000,
        25.00, 4.00, 0.00, 29.00, 29.00,
        'EMITIDO', 'Entrega sin factura', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 107, 1, 'Huevos 12und',   2.00, 3.80, 0.00, 16.00, 8.82
UNION ALL SELECT currval('documentos_ventas_id_seq'), 109, 2, 'Pasta Espagueti',5.00, 1.80, 0.00, 16.00,10.44
UNION ALL SELECT currval('documentos_ventas_id_seq'), 103, 3, 'Arroz Mary 1kg', 2.00, 2.50, 0.00, 16.00, 5.80;

-- NE-000002
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('NE-000002', NULL, 'NOTA_ENTREGA', 109, 101, 1,
        CURRENT_DATE - 3, NULL, 1, 1.0000,
        13.00, 2.08, 0.00, 15.08, 15.08,
        'EMITIDO', NULL, 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 111, 1, 'Salsa de Tomate', 2.00, 1.90, 0.00, 16.00,  4.41
UNION ALL SELECT currval('documentos_ventas_id_seq'), 110, 2, 'Atun en lata',   2.00, 2.20, 0.00, 16.00,  5.10
UNION ALL SELECT currval('documentos_ventas_id_seq'), 112, 3, 'Galletas Maria', 2.00, 1.30, 0.00, 16.00,  3.02;

-- PRES-000001
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('PRES-000001', NULL, 'PRESUPUESTO', 111, 105, 1,
        CURRENT_DATE - 7, CURRENT_DATE + 7, 2, 36.5000,
        800.00, 128.00, 0.00, 928.00, 33872.00,
        'EMITIDO', 'Cotizacion para evento corporativo - vence en 7 dias', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 101, 1, 'Coca-Cola 2L',      100.00, 5.50, 0.00, 16.00, 638.00
UNION ALL SELECT currval('documentos_ventas_id_seq'), 107, 2, 'Huevos 12und',    50.00, 3.80, 0.00, 16.00, 220.40
UNION ALL SELECT currval('documentos_ventas_id_seq'), 105, 3, 'Pan Hallullas 6und', 50.00, 1.50, 0.00, 16.00, 87.00;

-- PRES-000002
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('PRES-000002', NULL, 'PRESUPUESTO', 104, 102, 1,
        CURRENT_DATE - 2, CURRENT_DATE + 12, 2, 36.5000,
        1500.00, 240.00, 0.00, 1740.00, 63510.00,
        'EMITIDO', 'Cotizacion stock mensual para supermercado', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 101, 1, 'Coca-Cola 2L',     150.00, 5.50, 0.00, 16.00, 957.00
UNION ALL SELECT currval('documentos_ventas_id_seq'), 104, 2, 'Aceite Girasol',  50.00, 4.80, 0.00, 16.00, 278.40
UNION ALL SELECT currval('documentos_ventas_id_seq'), 106, 3, 'Leche en polvo',  80.00, 6.20, 0.00, 16.00, 575.36;

-- PED-000001
INSERT INTO documentos_ventas (codigo, numero_control, tipo, cliente_id, vendedor_id, punto_emision_id,
                                fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
                                subtotal, total_impuestos, total_descuentos, total_neto, total_neto_local,
                                estado, observaciones, creado_por)
VALUES ('PED-000001', NULL, 'PEDIDO', 107, 103, 1,
        CURRENT_DATE - 4, CURRENT_DATE + 11, 2, 36.5000,
        220.00, 35.20, 0.00, 255.20, 9314.80,
        'EMITIDO', 'Pedido para entrega la proxima semana', 1);

INSERT INTO documentos_ventas_detalle (documento_id, producto_id, nro_renglon, descripcion,
                                        cantidad, precio_unitario, descuento_pct, impuesto_pct, total_renglon)
SELECT currval('documentos_ventas_id_seq'), 101, 1, 'Coca-Cola 2L',    20.00, 5.50, 0.00, 16.00, 127.60
UNION ALL SELECT currval('documentos_ventas_id_seq'), 106, 2, 'Leche en polvo', 10.00, 6.20, 0.00, 16.00,  71.92
UNION ALL SELECT currval('documentos_ventas_id_seq'), 108, 3, 'Cafe Molido',    10.00, 5.50, 0.00, 16.00,  63.80;

COMMIT;

-- =====================================================================
-- 7. MOVIMIENTOS DE CxC (libro mayor): solo FACTURAS vigentes a CREDITO
--    Insertamos deuda espejo para las facturas CREDITO pendientes
-- =====================================================================
BEGIN;

-- Para FAC-000001, 000002, 000003 (CREDITO, vigentes)
INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, documento_venta_id, numero_documento,
                              fecha_movimiento, fecha_vencimiento, moneda_id, tasa_cambio,
                              monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por)
SELECT cliente_id, 'FACTURA', id, codigo, fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
       total_neto, total_neto, total_neto_local, total_neto_local, 'EMITIDO', 1
FROM documentos_ventas
WHERE tipo = 'FACTURA' AND estado = 'EMITIDO'
  AND codigo IN ('FAC-000001', 'FAC-000002', 'FAC-000003', 'FAC-000004', 'FAC-000012', 'FAC-000013', 'FAC-000014', 'FAC-000010');

-- FAC-000005, 000006, 000007 son PAGADAS: insertamos el mov original con saldo 0
INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, documento_venta_id, numero_documento,
                              fecha_movimiento, fecha_vencimiento, moneda_id, tasa_cambio,
                              monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por)
SELECT cliente_id, 'FACTURA', id, codigo, fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
       total_neto, 0.00, total_neto_local, 0.00, 'PAGADO', 1
FROM documentos_ventas
WHERE tipo = 'FACTURA' AND estado = 'EMITIDO'
  AND codigo IN ('FAC-000005', 'FAC-000006', 'FAC-000007');

-- Para FAC-000011 (anulada): CxC anulada
INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, documento_venta_id, numero_documento,
                              fecha_movimiento, fecha_vencimiento, moneda_id, tasa_cambio,
                              monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por)
SELECT cliente_id, 'FACTURA', id, codigo, fecha_emision, fecha_vencimiento, moneda_id, tasa_cambio,
       total_neto, 0.00, total_neto_local, 0.00, 'ANULADO', 1
FROM documentos_ventas
WHERE tipo = 'FACTURA' AND estado = 'ANULADO';

COMMIT;

-- =====================================================================
-- 8. PAGOS Y APLICACIONES (CxC: abonos, retenciones)
-- =====================================================================
BEGIN;

-- Pagos totales para FAC-000001, 000002, 000003, 000005, 000006, 000007
-- (Insertamos un ABONO por cada una)
INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, numero_documento, fecha_movimiento,
                              moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por)
SELECT cliente_id, 'ABONO', 'PAGO-' || codigo, fecha_vencimiento - 3,
       moneda_id, tasa_cambio, total_neto, 0.00, total_neto_local, 0.00, 'EMITIDO', 1
FROM documentos_ventas
WHERE tipo = 'FACTURA' AND estado = 'EMITIDO'
  AND codigo IN ('FAC-000001', 'FAC-000002', 'FAC-000003', 'FAC-000005', 'FAC-000006', 'FAC-000007');

-- Crear aplicaciones (cada ABONO aplicado a su FACTURA)
INSERT INTO aplicaciones_cxc (movimiento_pago_id, movimiento_deuda_id, monto_aplicado_original, monto_aplicado_local, aplicado_por)
SELECT
  pag.id, deu.id, pag.monto_original, pag.monto_local, 1
FROM movimientos_cxc pag
INNER JOIN movimientos_cxc deu
  ON deu.tipo_movimiento = 'FACTURA'
  AND deu.documento_venta_id = (
    SELECT id FROM documentos_ventas WHERE codigo = SUBSTRING(pag.numero_documento, 6)  -- 'PAGO-FAC-000001' -> 'FAC-000001'
  )
WHERE pag.tipo_movimiento = 'ABONO' AND pag.numero_documento LIKE 'PAGO-FAC-%';

COMMIT;

-- =====================================================================
-- 9. PAGO PARCIAL de FAC-000013 (50% = 174 USD)
-- =====================================================================
BEGIN;

-- Insertar el abono parcial
INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, numero_documento, fecha_movimiento,
                              moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por)
SELECT cliente_id, 'ABONO', 'PAGO-PARCIAL-013', CURRENT_DATE - 5,
       moneda_id, tasa_cambio, 174.00, 0.00, 174.00 * 36.5000, 0.00, 'EMITIDO', 1
FROM documentos_ventas WHERE codigo = 'FAC-000013';

-- Aplicar a FAC-000013
INSERT INTO aplicaciones_cxc (movimiento_pago_id, movimiento_deuda_id, monto_aplicado_original, monto_aplicado_local, aplicado_por)
SELECT pag.id, deu.id, 174.00, 174.00 * 36.5000, 1
FROM movimientos_cxc pag, movimientos_cxc deu
WHERE pag.numero_documento = 'PAGO-PARCIAL-013' AND pag.tipo_movimiento = 'ABONO'
  AND deu.tipo_movimiento = 'FACTURA' AND deu.documento_venta_id = (SELECT id FROM documentos_ventas WHERE codigo = 'FAC-000013');

-- Actualizar saldo de la factura
UPDATE movimientos_cxc SET saldo_original = 174.00, saldo_local = 174.00 * 36.5000
WHERE tipo_movimiento = 'FACTURA' AND documento_venta_id = (SELECT id FROM documentos_ventas WHERE codigo = 'FAC-000013');

COMMIT;

-- =====================================================================
-- 10. RETENCION IVA + PAGO PARCIAL de FAC-000014 (cliente C004 CE)
--     IVA 16% de 500 = 80 USD, retencion 75% = 60 USD
--     Pago parcial en efectivo = 145 USD
--     Pendiente: 580 - 60 - 145 = 375 USD
-- =====================================================================
BEGIN;

-- Retencion IVA
INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, numero_documento, fecha_movimiento,
                              moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por)
SELECT cliente_id, 'RETENCION_IVA', 'RET-IVA-014', CURRENT_DATE - 3,
       moneda_id, tasa_cambio, 60.00, 0.00, 60.00 * 36.5000, 0.00, 'EMITIDO', 1
FROM documentos_ventas WHERE codigo = 'FAC-000014';

-- Pago parcial
INSERT INTO movimientos_cxc (cliente_id, tipo_movimiento, numero_documento, fecha_movimiento,
                              moneda_id, tasa_cambio, monto_original, saldo_original, monto_local, saldo_local, estado, registrado_por)
SELECT cliente_id, 'ABONO', 'PAGO-PARCIAL-014', CURRENT_DATE - 3,
       moneda_id, tasa_cambio, 145.00, 0.00, 145.00 * 36.5000, 0.00, 'EMITIDO', 1
FROM documentos_ventas WHERE codigo = 'FAC-000014';

-- Aplicar la retencion
INSERT INTO aplicaciones_cxc (movimiento_pago_id, movimiento_deuda_id, monto_aplicado_original, monto_aplicado_local, aplicado_por)
SELECT ret.id, deu.id, 60.00, 60.00 * 36.5000, 1
FROM movimientos_cxc ret, movimientos_cxc deu
WHERE ret.numero_documento = 'RET-IVA-014' AND ret.tipo_movimiento = 'RETENCION_IVA'
  AND deu.tipo_movimiento = 'FACTURA' AND deu.documento_venta_id = (SELECT id FROM documentos_ventas WHERE codigo = 'FAC-000014');

-- Aplicar el pago
INSERT INTO aplicaciones_cxc (movimiento_pago_id, movimiento_deuda_id, monto_aplicado_original, monto_aplicado_local, aplicado_por)
SELECT pag.id, deu.id, 145.00, 145.00 * 36.5000, 1
FROM movimientos_cxc pag, movimientos_cxc deu
WHERE pag.numero_documento = 'PAGO-PARCIAL-014' AND pag.tipo_movimiento = 'ABONO'
  AND deu.tipo_movimiento = 'FACTURA' AND deu.documento_venta_id = (SELECT id FROM documentos_ventas WHERE codigo = 'FAC-000014');

-- Actualizar saldo pendiente de FAC-000014
UPDATE movimientos_cxc SET saldo_original = 375.00, saldo_local = 375.00 * 36.5000
WHERE tipo_movimiento = 'FACTURA' AND documento_venta_id = (SELECT id FROM documentos_ventas WHERE codigo = 'FAC-000014');

COMMIT;

-- =====================================================================
-- 11. OVERRIDE DE CREDITO (auditoria de FAC-000010)
-- =====================================================================
INSERT INTO override_credito_log (cliente_id, documento_venta_id, usuario_id, limite_vigente,
                                    saldo_antes_emision, monto_nueva_factura, monto_excedente, motivo)
SELECT 112, id, 1, 500.00, 0.00, 58.00, 58.00, 'Cliente nuevo pero referido por socio comercial - autorizado por gerente general'
FROM documentos_ventas WHERE codigo = 'FAC-000010';

-- =====================================================================
-- 12. Sincronizar secuencias y stock
-- =====================================================================
SELECT setval('documentos_ventas_id_seq', (SELECT COALESCE(MAX(id), 0) FROM documentos_ventas), true);
SELECT setval('documentos_ventas_detalle_id_seq', (SELECT COALESCE(MAX(id), 0) FROM documentos_ventas_detalle), true);
SELECT setval('movimientos_cxc_id_seq', (SELECT COALESCE(MAX(id), 0) FROM movimientos_cxc), true);
SELECT setval('aplicaciones_cxc_id_seq', (SELECT COALESCE(MAX(id), 0) FROM aplicaciones_cxc), true);

UPDATE secuencias_documentos SET numero_actual = 14, proximo_numero = 15 WHERE tipo_documento = 'FACTURA' AND punto_emision_id = 1;
UPDATE secuencias_documentos SET numero_actual = 2,  proximo_numero = 3  WHERE tipo_documento = 'NOTA_ENTREGA' AND punto_emision_id = 1;
UPDATE secuencias_documentos SET numero_actual = 2,  proximo_numero = 3  WHERE tipo_documento = 'PRESUPUESTO' AND punto_emision_id = 1;
UPDATE secuencias_documentos SET numero_actual = 1,  proximo_numero = 2  WHERE tipo_documento = 'PEDIDO' AND punto_emision_id = 1;

-- Descontar stock para los productos vendidos en FACTURAS y NOTAS DE ENTREGA vigentes
UPDATE productos p SET existencia = GREATEST(0, p.existencia - COALESCE((
  SELECT SUM(dd.cantidad)
  FROM documentos_ventas_detalle dd
  INNER JOIN documentos_ventas d ON d.id = dd.documento_id
  WHERE dd.producto_id = p.id
    AND d.tipo IN ('FACTURA', 'NOTA_ENTREGA')
    AND d.estado = 'EMITIDO'
), 0))
WHERE p.es_servicio = FALSE;

-- =====================================================================
-- VERIFICACION FINAL
-- =====================================================================
SELECT 'documentos_ventas total' as t, count(*)::text as v FROM documentos_ventas
UNION ALL SELECT 'facturas EMITIDO', count(*)::text FROM documentos_ventas WHERE tipo='FACTURA' AND estado='EMITIDO'
UNION ALL SELECT 'facturas ANULADO', count(*)::text FROM documentos_ventas WHERE tipo='FACTURA' AND estado='ANULADO'
UNION ALL SELECT 'NE', count(*)::text FROM documentos_ventas WHERE tipo='NOTA_ENTREGA'
UNION ALL SELECT 'PRESUPUESTO', count(*)::text FROM documentos_ventas WHERE tipo='PRESUPUESTO'
UNION ALL SELECT 'PEDIDO', count(*)::text FROM documentos_ventas WHERE tipo='PEDIDO'
UNION ALL SELECT 'movimientos_cxc', count(*)::text FROM movimientos_cxc
UNION ALL SELECT 'aplicaciones_cxc', count(*)::text FROM aplicaciones_cxc
UNION ALL SELECT 'override_credito_log', count(*)::text FROM override_credito_log
UNION ALL SELECT 'clientes activos', count(*)::text FROM clientes WHERE activo
UNION ALL SELECT 'productos activos', count(*)::text FROM productos WHERE activo
UNION ALL SELECT 'vendedores activos', count(*)::text FROM vendedores WHERE activo;
