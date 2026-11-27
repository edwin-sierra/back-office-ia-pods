# ADR 0004 — Autenticación sin RBAC en `/auth/*`

- **Estado**: Aceptado
- **Fecha**: 2026-11-27

## Contexto

La autenticación de usuarios se incorpora antes que RBAC. El ADR 0003 define JWT y la autorización
RBAC general, pero los endpoints de autenticación deben poder operar sin roles ni permisos.

## Decisión

Los endpoints `/auth/*` autentican, pero no declaran ni evalúan permisos RBAC y no responden 403
por autorización. `POST /auth/login` es público; `POST /auth/refresh` requiere un refresh token
válido; los demás endpoints de autenticación requieren un access token válido según corresponda.
En particular, `GET /auth/me` requiere el access token de un usuario activo. Esta decisión
complementa el ADR 0003 y no cambia sus duraciones ni sus reglas de emisión y validación de JWT.

## Consecuencias

- Login puede usarse antes de crear roles o permisos.
- Refresh y los endpoints protegidos de autenticación siguen exigiendo el tipo de token apropiado;
  la excepción a RBAC no los hace públicos.
- Los endpoints fuera de `/auth/*` continúan sujetos a las reglas generales de autorización.
