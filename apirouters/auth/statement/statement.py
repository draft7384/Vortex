"""
SQL del modulo Auth.
Reutiliza los queries del modulo usuarios para login/refresh.
"""

SELECT_USUARIO_AUTENTICAR = """
SELECT id, username, nombre_completo, email, password_hash, rol, activo
FROM usuarios
WHERE username = :username AND activo = TRUE;
"""

UPDATE_ULTIMO_ACCESO = """
UPDATE usuarios SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id = :usuario_id;
"""
