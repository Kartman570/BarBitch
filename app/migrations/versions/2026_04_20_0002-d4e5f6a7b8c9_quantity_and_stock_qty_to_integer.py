"""quantity and stock_qty to integer

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-20 00:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('orders', 'quantity',
                    existing_type=sa.Float(),
                    type_=sa.Integer(),
                    existing_nullable=False,
                    postgresql_using='quantity::integer')
    op.alter_column('items', 'stock_qty',
                    existing_type=sa.Float(),
                    type_=sa.Integer(),
                    existing_nullable=True,
                    postgresql_using='stock_qty::integer')


def downgrade() -> None:
    op.alter_column('items', 'stock_qty',
                    existing_type=sa.Integer(),
                    type_=sa.Float(),
                    existing_nullable=True)
    op.alter_column('orders', 'quantity',
                    existing_type=sa.Integer(),
                    type_=sa.Float(),
                    existing_nullable=False)
