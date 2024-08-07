"""Add size limit to study

Revision ID: 151f1467fe64
Revises: 1fe8bdf14c04
Create Date: 2024-08-05 15:29:48.433328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '151f1467fe64'
down_revision = '1fe8bdf14c04'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('study', sa.Column('size_limit', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('study', 'size_limit')
    # ### end Alembic commands ###
