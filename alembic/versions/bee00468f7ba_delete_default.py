"""delete default

Revision ID: bee00468f7ba
Revises: 4a627258aa88
Create Date: 2023-09-28 12:49:30.620586

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bee00468f7ba'
down_revision = '4a627258aa88'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('product', 'expanding', server_default=None)
    op.alter_column('product', 'is_promo', server_default=None)
    op.alter_column('product', 'expandable', server_default=None)

def downgrade() -> None:
    op.alter_column('product', 'expanding', server_default='0')
    op.alter_column('product', 'is_promo', server_default='0')
    op.alter_column('product', 'expandable', server_default='1')