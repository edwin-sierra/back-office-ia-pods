# ADR 0003 — Autenticación con JWT propio y API keys

- **Estado**: Aceptado
- **Fecha**: 2026-11-25

## Contexto
Hay dos tipos de clientes: personas (admin, operador, viewer) y robots o runners que reportan sus ejecuciones. Además, se necesita RBAC con roles y permisos administrables.

## Decisión
- **Usuarios**: login con email y password (hash Argon2id). La API emite un access token JWT (15 min) y un refresh token (7 días), firmados con `APP_JWT_SECRET_KEY`.
- **Robots/runners**: API keys en el header `X-API-Key`. Se muestran una sola vez y se guardan como hash + prefijo. Pueden estar acotadas a un robot y tener scopes.
- **Autorización**: RBAC en base de datos (`roles`, `permissions`, `role_permissions`, `user_roles`). Cada endpoint declara su permiso con `require_permission("recurso:accion")`.

## Consecuencias
- No hay dependencia de un IdP externo en v1.
- La rotación del secreto JWT invalida todas las sesiones; hay que planificarla.
- Para migrar a OIDC más adelante, alcanza con reemplazar el emisor y validador de tokens y mapear claims a roles: el modelo RBAC se mantiene.
