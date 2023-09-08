"""add salt

Revision ID: 6488deec84c6
Revises: 56a753312600
Create Date: 2023-09-07 22:58:17.635572

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6488deec84c6'
down_revision = '56a753312600'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('auth', sa.Column('salt', sa.LargeBinary(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('auth', 'salt')
    # ### end Alembic commands ###
