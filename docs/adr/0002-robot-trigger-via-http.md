# ADR 0002 — Disparo de robots vía llamado HTTP

- **Estado**: Aceptado
- **Fecha**: 2026-11-25

## Contexto
La API tiene que poder "ejecutar" un robot. Opciones evaluadas: (a) solo registrar la ejecución y que un runner la tome; (b) encolar en un worker propio (Celery o ARQ); (c) llamar a un endpoint HTTP que dispara el robot.

## Decisión
Cada robot del catálogo define un `trigger_url`. Al ejecutar, la API:
1. Crea la `Execution` en `PENDING`.
2. Hace un `POST` (o el método configurado) al `trigger_url` con `execution_id`, `params` y `callback_url`.
3. Marca `TRIGGERED` si recibe una respuesta 2xx, o `TRIGGER_FAILED` ante un error o un timeout.
4. El robot reporta su avance y su resultado final con `PATCH /api/v1/executions/{id}`, autenticado con API key.

El disparo es síncrono dentro del request, con timeout corto, y responde `202 Accepted`.

## Consecuencias
- No se agrega infraestructura extra (sin broker ni workers).
- La API depende de la disponibilidad del endpoint del robot en el momento del disparo; un fallo queda registrado como `TRIGGER_FAILED`.
- Riesgo de SSRF: se mitiga con una allowlist de hosts (`APP_TRIGGER_ALLOWED_HOSTS`) y sin redirects.
- Si en el futuro hacen falta reintentos diferidos o un alto volumen, se puede introducir una cola sin cambiar el contrato público.
