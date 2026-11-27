"""Registro de modelos para Alembic.

Importar aquí los módulos `models` de cada bounded context para que
`Base.metadata` los conozca al autogenerar migraciones, p.ej.:

    from app.modules.robots import models as robots_models  # noqa: F401
"""

from app.db.base import Base
from app.modules.iam import models as iam_models  # noqa: F401

__all__ = ["Base"]
