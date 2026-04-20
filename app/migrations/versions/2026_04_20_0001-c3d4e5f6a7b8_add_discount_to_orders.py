"""add discount to orders

Revision ID: c3d4e5f6a7b8
Revises: b0898e61453c
Create Date: 2026-04-20 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b0898e61453c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('orders', sa.Column('discount', sa.Float(), nullable=False, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('orders', 'discount')
