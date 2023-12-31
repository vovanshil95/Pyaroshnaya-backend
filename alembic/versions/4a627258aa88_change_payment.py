"""change payment

Revision ID: 4a627258aa88
Revises: bd326a23dcfb
Create Date: 2023-09-27 21:02:49.996064

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a627258aa88'
down_revision = 'bd326a23dcfb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('payment_category',
    sa.Column('payment_id', sa.UUID(), nullable=False),
    sa.Column('category_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['question_category.id'], ondelete='cascade'),
    sa.ForeignKeyConstraint(['payment_id'], ['payment.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('payment_id', 'category_id')
    )
    op.create_table('purchase_category',
    sa.Column('purchase_id', sa.UUID(), nullable=False),
    sa.Column('category_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['question_category.id'], ondelete='cascade'),
    sa.ForeignKeyConstraint(['purchase_id'], ['purchase.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('purchase_id', 'category_id')
    )
    op.add_column('payment', sa.Column('product_to_expend_id', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'payment', 'product', ['product_to_expend_id'], ['id'], ondelete='cascade')
    op.add_column('product', sa.Column('categories_size', sa.Integer(), nullable=True))
    op.add_column('product', sa.Column('expandable', sa.BOOLEAN(), nullable=False, server_default='1'))
    op.add_column('product', sa.Column('is_promo', sa.BOOLEAN(), nullable=False, server_default='0'))
    op.add_column('product', sa.Column('expanding', sa.BOOLEAN(), nullable=False, server_default='0'))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('product', 'expanding')
    op.drop_column('product', 'is_promo')
    op.drop_column('product', 'expandable')
    op.drop_column('product', 'categories_size')
    op.drop_constraint(None, 'payment', type_='foreignkey')
    op.drop_column('payment', 'product_to_expend_id')
    op.drop_table('purchase_category')
    op.drop_table('payment_category')
    # ### end Alembic commands ###
