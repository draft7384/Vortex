"""
SQL crudo del modulo Usuarios.
"""

# ============================================================
# CREATE
# ============================================================
INSERT_USUARIO = """
INSERT INTO usuarios (username, nombre_completo, email, password_hash, rol)
VALUES (:username, :nombre_completo, :email, :password_hash, :rol)
RETURNING id, username, nombre_completo, email, rol, activo, creado_en, ultimo_acceso;
"""


# ============================================================
# READ
# ============================================================
SELECT_USUARIO_BY_ID = """
SELECT id, username, nombre_completo, email, rol, activo, creado_en, ultimo_acceso
FROM usuarios
WHERE id = :usuario_id;
"""

SELECT_USUARIO_BY_USERNAME = """
SELECT id, username, nombre_completo, email, password_hash, rol, activo, creado_en, ultimo_acceso
FROM usuarios
WHERE username = :username;
"""

SELECT_USUARIO_BY_EMAIL = """
SELECT id, username, nombre_completo, email, password_hash, rol, activo
FROM usuarios
WHERE email = :email;
"""

SELECT_USUARIOS_PAGINATED = """
SELECT id, username, nombre_completo, email, rol, activo, creado_en, ultimo_acceso
FROM usuarios
WHERE activo = TRUE
ORDER BY username ASC
LIMIT :limit OFFSET :offset;
"""

SELECT_USUARIOS_COUNT = """
SELECT COUNT(*) AS total FROM usuarios WHERE activo = TRUE;
"""

SEARCH_USUARIOS_BY_KEYWORD = """
SELECT id, username, nombre_completo, email, rol, activo
FROM usuarios
WHERE activo = TRUE
  AND (
    LOWER(username) LIKE LOWER(:keyword)
    OR LOWER(nombre_completo) LIKE LOWER(:keyword)
    OR LOWER(email) LIKE LOWER(:keyword)
  )
ORDER BY username ASC
LIMIT 50;
"""


# ============================================================
# UPDATE
# ============================================================
UPDATE_USUARIO = """
UPDATE usuarios SET
    username         = COALESCE(:username, username),
    nombre_completo  = COALESCE(:nombre_completo, nombre_completo),
    email            = COALESCE(:email, email),
    password_hash    = COALESCE(:password_hash, password_hash),
    rol              = COALESCE(:rol, rol),
    activo           = COALESCE(:activo, activo)
WHERE id = :usuario_id
RETURNING id, username, nombre_completo, email, rol, activo, creado_en, ultimo_acceso;
"""

UPDATE_ULTIMO_ACCESO = """
UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = :usuario_id;
"""


# ============================================================
# DELETE (soft)
# ============================================================
DELETE_USUARIO = """
UPDATE usuarios SET activo = FALSE WHERE id = :usuario_id
RETURNING id, username;
"""
