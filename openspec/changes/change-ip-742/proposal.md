## Why
IP-742 incorpora autenticación de usuarios para que las llamadas al back office puedan asociarse a una identidad y protegerse antes de incorporar RBAC. Hoy el módulo IAM solo contiene un marcador y la API no ofrece login, renovación de tokens ni consulta del usuario autenticado.

## What Changes
- Añadir usuarios persistidos y un comando de bootstrap para crear el primer usuario activo.
- Añadir login con JWT, renovación mediante refresh token, consulta del usuario actual y la dependencia reutilizable CurrentUserDep.
- Rechazar credenciales y tokens no válidos, cuerpos de solicitud inválidos y usuarios inactivos sin exponer datos de autenticación.

## Capabilities
### New Capabilities
- `iam-auth`: usuarios, bootstrap inicial y autenticación con access y refresh tokens.

### Modified Capabilities
- Ninguna.

## Impact
El cambio afecta el módulo IAM, la persistencia de usuarios y su migración Alembic, la configuración JWT y los endpoints versionados `/api/v1/auth`. No agrega ni usa permisos RBAC: según la aclaración de IP-742, los endpoints `/auth/*` solo autentican, login es público y ninguno devuelve 403 por permisos. RBAC, roles, permisos y ABM de usuarios quedan fuera de alcance. Se asume que el bootstrap crea un usuario inicial activo, sin asignarle un rol aún inexistente; que el perfil expone id, email, nombre completo, estado y timestamps, pero nunca el hash de contraseña; y que un intento de bootstrap con un email ya registrado falla sin modificar ese usuario. Se aplican las duraciones del ADR vigente: access token de 15 minutos y refresh token de 7 días.
