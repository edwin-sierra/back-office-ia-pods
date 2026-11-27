"""Comando para crear el usuario administrador inicial sin exponer su contraseña."""

import argparse
import asyncio
import getpass
import sys

from app.db.session import get_sessionmaker
from app.modules.iam.service import UserAlreadyExistsError, bootstrap_user


async def _create_user(email: str, full_name: str, password: str) -> bool:
    async with get_sessionmaker()() as session:
        try:
            await bootstrap_user(session, email, full_name, password)
        except UserAlreadyExistsError:
            return False
    return True


def main() -> None:
    """Solicita los datos de bootstrap y crea el primer usuario."""
    parser = argparse.ArgumentParser(description="Crear el usuario inicial de IAM")
    parser.add_argument("--email", required=True)
    parser.add_argument("--full-name", required=True)
    arguments = parser.parse_args()
    password = getpass.getpass("Contraseña: ")

    if not asyncio.run(_create_user(arguments.email, arguments.full_name, password)):
        print("Conflicto: ya existe un usuario con ese email.", file=sys.stderr)
        raise SystemExit(1)

    print("Usuario inicial creado.")


if __name__ == "__main__":
    main()
