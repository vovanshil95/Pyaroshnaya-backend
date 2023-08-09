"""init db

Revision ID: e5f3744a4f79
Revises: 
Create Date: 2023-08-09 11:43:38.604893

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f3744a4f79'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('phone', sa.String(), nullable=False),
    sa.Column('company', sa.String(), nullable=False),
    sa.Column('role', sa.String(), nullable=False),
    sa.Column('balance', sa.Float(), nullable=False),
    sa.Column('till_date', sa.TIMESTAMP(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('phone')
    )
    op.create_table('auth',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('password', sa.LargeBinary(), nullable=False),
    sa.Column('sms_code', sa.String(), nullable=True),
    sa.Column('token', sa.String(), nullable=True),
    sa.Column('token_exp_time', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('refresh_token',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('user_agent', sa.String(), nullable=False),
    sa.Column('exp', sa.TIMESTAMP(), nullable=False),
    sa.Column('last_use', sa.TIMESTAMP(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('sms_send',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('ip', sa.String(), nullable=False),
    sa.Column('user_agent', sa.String(), nullable=False),
    sa.Column('time_send', sa.TIMESTAMP(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('ip')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('sms_send')
    op.drop_table('refresh_token')
    op.drop_table('auth')
    op.drop_table('users')
    # ### end Alembic commands ###
