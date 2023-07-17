"""init db

Revision ID: 4da99a993e0f
Revises: 
Create Date: 2023-07-17 22:42:41.574055

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4da99a993e0f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('sms_send',
    sa.Column('ip', sa.String(), nullable=False),
    sa.Column('time_send', sa.TIMESTAMP(), nullable=False),
    sa.PrimaryKeyConstraint('ip')
    )
    op.create_table('unverified_user',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('phone', sa.String(), nullable=False),
    sa.Column('company', sa.String(), nullable=False),
    sa.Column('last_sms_code', sa.String(), nullable=False),
    sa.Column('last_sms_time', sa.TIMESTAMP(), nullable=False),
    sa.Column('ip', sa.String(), nullable=False),
    sa.Column('user_agent', sa.String(), nullable=False),
    sa.Column('password', sa.LargeBinary(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('phone', sa.String(), nullable=False),
    sa.Column('company', sa.String(), nullable=False),
    sa.Column('role', sa.String(), nullable=False),
    sa.Column('balance', sa.Float(), nullable=False),
    sa.Column('till_date', sa.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('phone')
    )
    op.create_table('auth',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('password', sa.LargeBinary(), nullable=False),
    sa.Column('sms_code', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('refresh_token',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('user_agent', sa.String(), nullable=False),
    sa.Column('exp', sa.TIMESTAMP(), nullable=False),
    sa.Column('valid', sa.BOOLEAN(), nullable=False),
    sa.Column('last_use', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('refresh_token')
    op.drop_table('auth')
    op.drop_table('users')
    op.drop_table('unverified_user')
    op.drop_table('sms_send')
    # ### end Alembic commands ###