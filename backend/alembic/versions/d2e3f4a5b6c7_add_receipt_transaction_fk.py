"""add receipts.transaction_id foreign key

The initial schema declared this constraint with use_alter=True, which
op.create_table() silently skips, so databases built from migrations never got
it. Databases built with metadata.create_all() (the .deb releases up to v0.1.10)
do have it, so only create it where it's missing.

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4g5h6
Create Date: 2026-11-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, None] = 'c1d2e3f4g5h6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

FK_NAME = 'fk_receipt_transaction_id'


def upgrade() -> None:
    existing = {fk['name'] for fk in sa.inspect(op.get_bind()).get_foreign_keys('receipts')}
    if FK_NAME in existing:
        return

    # Without the constraint, receipts could be left pointing at deleted
    # transactions. Unlink those so the constraint can be added.
    op.execute(
        "UPDATE receipts SET transaction_id = NULL "
        "WHERE transaction_id IS NOT NULL "
        "AND transaction_id NOT IN (SELECT id FROM transactions)"
    )
    op.create_foreign_key(FK_NAME, 'receipts', 'transactions', ['transaction_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(FK_NAME, 'receipts', type_='foreignkey')
