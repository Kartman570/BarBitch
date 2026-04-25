"""add_item_name_snapshot_to_orders

Revision ID: 1b8a75e50aa9
Revises: e5f6a7b8c9d0
Create Date: 2026-04-25 09:29:47.333513

"""
from typing import Sequence, Union

from alembic import op
import sqlmodel
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b8a75e50aa9'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add item_name with a temporary server default so existing rows get an empty string
    op.add_column('orders', sa.Column('item_name', sa.String(), nullable=False, server_default=''))

    # Backfill item_name from items table for existing orders
    op.execute("""
        UPDATE orders
        SET item_name = items.name
        FROM items
        WHERE orders.item_id = items.id
    """)

    # Remove the server default now that all rows are populated
    op.alter_column('orders', 'item_name', server_default=None)

    # Make item_id nullable and update the FK to cascade SET NULL on item deletion
    op.alter_column('orders', 'item_id', existing_type=sa.INTEGER(), nullable=True)
    op.drop_constraint('orders_item_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key('orders_item_id_fkey', 'orders', 'items', ['item_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('orders_item_id_fkey', 'orders', type_='foreignkey')
    op.create_foreign_key('orders_item_id_fkey', 'orders', 'items', ['item_id'], ['id'])
    op.alter_column('orders', 'item_id', existing_type=sa.INTEGER(), nullable=False)
    op.drop_column('orders', 'item_name')
