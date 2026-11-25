"""Primitivas de seguridad (hash de passwords, JWT, API keys).

Placeholder: la implementación llega con los changes de OpenSpec `add-iam-auth` y
`add-service-api-keys`. Reglas que debe respetar:

- Passwords: hash con argon2 (pwdlib). Nunca guardar ni loguear texto plano.
- JWT: access token corto + refresh token; firmado con `Settings.jwt_secret_key`.
- API keys: se muestran una sola vez al crearlas; en DB se guarda solo el hash + prefijo.
"""
