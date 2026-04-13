import typer
from typing import List
from sqlmodel import Session, select

from core.database import create_db_and_tables, engine
from models.models import User, Item

cli = typer.Typer(help="init db, seed data")


@cli.command("init-db")
def init_db() -> None:
    create_db_and_tables()
    typer.echo("DB initialized")


@cli.command("create-user")
def create_user(
    name: str = typer.Option("Admin", "--name"),
    update: bool = typer.Option(False, "--update"),
) -> None:
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.name == name)).first()
        if existing:
            if update:
                existing.name = name
                session.add(existing)
                session.commit()
                typer.echo(f"User updated: {name}")
            else:
                typer.echo(f"User already exists, skip: {name}")
            return

        user = User(name=name)
        session.add(user)
        session.commit()
        session.refresh(user)
        typer.echo(f"User created: id={user.id}, name={user.name}")


def _default_items() -> List[dict]:
    return [
        {
            "name": "Beer",
            "price": 5.0,
            "uom": "liter",
            "is_active": True,
            "discount": 0.0,
            "available": 100.0,
        },
        {
            "name": "Nuts",
            "price": 4.0,
            "uom": "cup",
            "is_active": True,
            "discount": 0.0,
            "available": 200.0,
        },
        {
            "name": "Burger",
            "price": 10.0,
            "uom": "item",
            "is_active": True,
            "discount": 0.0,
            "available": 20.0,
        },
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
                # upsert/update
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
    create_user(name=user_name, update=False)
    seed_items(if_empty=items_if_empty)
    typer.echo("All done.")


if __name__ == "__main__":
    cli()
