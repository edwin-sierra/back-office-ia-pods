# ADR 0001 — Registrar decisiones de arquitectura

- **Estado**: Aceptado
- **Fecha**: 2026-11-25

## Contexto
El proyecto se desarrolla con Claude Code y OpenSpec. Las specs describen el *qué*; hace falta un lugar para registrar el *por qué* de las decisiones transversales.

## Decisión
Usamos ADRs breves en `docs/adr/NNNN-titulo.md` (formato: Contexto, Decisión, Consecuencias). Las decisiones propias de una feature viven en el `design.md` de su change de OpenSpec; las transversales o duraderas, en un ADR.

## Consecuencias
- Las decisiones quedan trazables y versionadas junto al código.
- Un ADR no se edita una vez aceptado: si la decisión cambia, se crea uno nuevo que lo reemplaza.
