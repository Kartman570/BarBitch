import typer
from typing import List
from sqlmodel import Session, select

from core.database import create_db_and_tables, engine
from models.models import User, Item, Role
from services.auth_service import hash_password, encode_permissions, DEFAULT_ROLES

cli = typer.Typer(help="init db, seed data")


@cli.command("init-db")
def init_db() -> None:
    create_db_and_tables()
    typer.echo("DB initialized")


@cli.command("seed-roles")
def seed_roles() -> None:
    """Create the four default roles if they don't exist."""
    with Session(engine) as session:
        for data in DEFAULT_ROLES:
            existing = session.exec(select(Role).where(Role.name == data["name"])).first()
            if existing:
                typer.echo(f"Role already exists, skip: {data['name']}")
                continue
            role = Role(
                name=data["name"],
                description=data["description"],
                permissions=encode_permissions(data["permissions"]),
            )
            session.add(role)
            typer.echo(f"Role created: {data['name']}")
        session.commit()


@cli.command("create-user")
def create_user(
    name: str = typer.Option("Admin", "--name"),
    username: str = typer.Option("admin", "--username"),
    password: str = typer.Option("admin", "--password"),
    role: str = typer.Option("admin", "--role"),
    update: bool = typer.Option(False, "--update"),
) -> None:
    with Session(engine) as session:
        role_obj = session.exec(select(Role).where(Role.name == role)).first()
        if role_obj is None:
            typer.echo(f"Role '{role}' not found. Run seed-roles first.")
            raise typer.Exit(1)

        existing = session.exec(select(User).where(User.username == username)).first()
        if existing:
            if update:
                existing.name = name
                existing.username = username
                existing.password_hash = hash_password(password)
                existing.role_id = role_obj.id
                session.add(existing)
                session.commit()
                typer.echo(f"User updated: {username}")
            else:
                typer.echo(f"User already exists, skip: {username}")
            return

        user = User(
            name=name,
            username=username,
            password_hash=hash_password(password),
            role_id=role_obj.id,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        typer.echo(f"User created: id={user.id}, username={user.username}, role={role}")


def _default_items() -> List[dict]:
    return [
        {"name": "Beer", "price": 5.0, "is_available": True},
        {"name": "Nuts", "price": 4.0, "is_available": True},
        {"name": "Burger", "price": 10.0, "is_available": True},
    ]


@cli.command("seed-items")
def seed_items(
    if_empty: bool = typer.Option(True, "--if-empty/--force"),
) -> None:
    with Session(engine) as session:
        if if_empty:
            any_row = session.exec(select(Item).limit(1)).first()
            if any_row:
                typer.echo("Items table is not empty, skip seeding (use --force to upsert).")
                return

        upserted, created = 0, 0
        for data in _default_items():
            existing = session.exec(select(Item).where(Item.name == data["name"])).first()
            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
                session.add(existing)
                upserted += 1
            else:
                session.add(Item(**data))
                created += 1

        session.commit()
        typer.echo(f"Seed complete. Created: {created}, Upserted: {upserted}")


@cli.command("seed-all")
def seed_all(
    user_name: str = typer.Option("Admin", "--user-name"),
    items_if_empty: bool = typer.Option(True, "--items-if-empty/--items-force"),
) -> None:
    init_db()
    seed_roles()
    create_user(name=user_name, username="admin", password="admin", role="admin", update=False)
    seed_items(if_empty=items_if_empty)
    typer.echo("All done.")


if __name__ == "__main__":
    cli()
